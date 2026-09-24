<?php

declare(strict_types=1);

require_once __DIR__ . '/Db.php';

/**
 * La biblioteca de fichas clínicas: carpetas, archivado y borrado en tanda.
 *
 * Todo esto vivía dentro de admin/patients.php como un único `delete_case`
 * de una ficha por vez, y con doscientos casos eso no es mantenimiento: es
 * borrar de a uno o dejar la lista crecer para siempre. Acá adentro no hay
 * $_POST, ni echo, ni redirect -- recibe ids y devuelve cuántas filas tocó,
 * así que se puede probar y lo usan igual la página y cualquier otra cosa
 * que en el futuro necesite mover o archivar fichas.
 *
 * Dos operaciones y una diferencia que importa:
 * - ARCHIVAR es reversible y no pierde nada: la ficha sale de la vista y del
 *   selector de "agendar caso nuevo", pero sus citas, atenciones e historial
 *   quedan intactos, y si tenía citas vivas se siguen atendiendo.
 * - ELIMINAR arrastra las citas y las atenciones registradas, y no se puede
 *   deshacer. Por eso el borrado masivo informa ANTES cuántas de cada cosa
 *   se va a llevar (ver impactoDeBorrado): "eliminar 40 fichas" y "eliminar
 *   40 fichas, 112 citas y 380 atenciones de alumnos" no son la misma frase.
 */
final class CaseLibrary
{
    /** Carpetas con cuántas fichas vivas (no archivadas) tiene cada una. */
    public static function folders(): array
    {
        Db::migrateCaseLibraryIfNeeded();
        return Db::get()->query(
            'SELECT f.id, f.name,
                    (SELECT COUNT(*) FROM cases c WHERE c.folder_id = f.id AND c.archived_at IS NULL) AS n_fichas
             FROM case_folders f
             ORDER BY f.name COLLATE NOCASE'
        )->fetchAll();
    }

    /**
     * Crea una carpeta y devuelve su id, o null si el nombre ya estaba
     * (índice único sin distinguir mayúsculas: dos "Semestre 1" no son dos
     * carpetas, son la misma escrita dos veces).
     */
    public static function createFolder(string $name, ?int $userId): ?int
    {
        Db::migrateCaseLibraryIfNeeded();
        $name = trim($name);
        if ($name === '') {
            return null;
        }
        $pdo = Db::get();
        $stmt = $pdo->prepare('SELECT id FROM case_folders WHERE name = ? COLLATE NOCASE');
        $stmt->execute([$name]);
        if ($stmt->fetchColumn() !== false) {
            return null;
        }
        $pdo->prepare('INSERT INTO case_folders (name, created_by) VALUES (?, ?)')->execute([$name, $userId]);
        return (int) $pdo->lastInsertId();
    }

    public static function renameFolder(int $folderId, string $name): bool
    {
        Db::migrateCaseLibraryIfNeeded();
        $name = trim($name);
        if ($name === '') {
            return false;
        }
        $pdo = Db::get();
        $stmt = $pdo->prepare('SELECT id FROM case_folders WHERE name = ? COLLATE NOCASE AND id != ?');
        $stmt->execute([$name, $folderId]);
        if ($stmt->fetchColumn() !== false) {
            return false;
        }
        $pdo->prepare('UPDATE case_folders SET name = ? WHERE id = ?')->execute([$name, $folderId]);
        return true;
    }

    /**
     * Borra la carpeta y deja sueltas sus fichas. NUNCA borra fichas: una
     * carpeta es dónde está guardado algo, no el algo -- que "eliminar
     * carpeta" se llevara doscientos casos armados sería la peor sorpresa
     * posible de esta pantalla.
     *
     * @return int fichas que quedaron sueltas
     */
    public static function deleteFolder(int $folderId): int
    {
        Db::migrateCaseLibraryIfNeeded();
        $pdo = Db::get();
        $stmt = $pdo->prepare('UPDATE cases SET folder_id = NULL WHERE folder_id = ?');
        $stmt->execute([$folderId]);
        $sueltas = $stmt->rowCount();
        $pdo->prepare('DELETE FROM case_folders WHERE id = ?')->execute([$folderId]);
        return $sueltas;
    }

    /** Mueve fichas a una carpeta ($folderId null = sacarlas de toda carpeta). */
    public static function moveToFolder(array $caseIds, ?int $folderId): int
    {
        return self::updateCases($caseIds, 'folder_id = ?', [$folderId]);
    }

    /** Archiva fichas (idempotente: no le pisa la fecha a una ya archivada). */
    public static function archive(array $caseIds): int
    {
        return self::updateCases($caseIds, 'archived_at = CURRENT_TIMESTAMP', [], 'archived_at IS NULL');
    }

    public static function unarchive(array $caseIds): int
    {
        return self::updateCases($caseIds, 'archived_at = NULL', [], 'archived_at IS NOT NULL');
    }

    /**
     * Qué se lleva puesto un borrado, para poder decírselo a quien lo pide
     * ANTES de hacerlo.
     *
     * @return array{fichas:int, citas:int, atenciones:int}
     */
    public static function impactoDeBorrado(array $caseIds): array
    {
        $caseIds = self::limpiarIds($caseIds);
        if ($caseIds === []) {
            return ['fichas' => 0, 'citas' => 0, 'atenciones' => 0];
        }
        $pdo = Db::get();
        [$in, $params] = self::inClause($caseIds);
        $citas = (int) self::scalar($pdo, "SELECT COUNT(*) FROM appointments WHERE case_id IN ({$in})", $params);
        $atenciones = (int) self::scalar(
            $pdo,
            "SELECT COUNT(*) FROM attendances att
              JOIN appointments ap ON ap.id = att.appointment_id
              WHERE ap.case_id IN ({$in})",
            $params
        );
        $fichas = (int) self::scalar($pdo, "SELECT COUNT(*) FROM cases WHERE id IN ({$in})", $params);
        return ['fichas' => $fichas, 'citas' => $citas, 'atenciones' => $atenciones];
    }

    /**
     * Elimina fichas con todo lo que cuelga de ellas, en UNA transacción: o
     * se van enteras o no se va ninguna. Antes el borrado de a una abría y
     * cerraba una transacción por ficha, y una tanda interrumpida a la mitad
     * dejaba casos sin citas y citas sin atenciones.
     *
     * @return array{fichas:int, citas:int, atenciones:int} lo que se borró
     */
    public static function deleteCases(array $caseIds): array
    {
        $caseIds = self::limpiarIds($caseIds);
        if ($caseIds === []) {
            return ['fichas' => 0, 'citas' => 0, 'atenciones' => 0];
        }
        $impacto = self::impactoDeBorrado($caseIds);
        $pdo = Db::get();
        [$in, $params] = self::inClause($caseIds);

        $propia = !$pdo->inTransaction();
        if ($propia) {
            $pdo->beginTransaction();
        }
        try {
            $pdo->prepare(
                "DELETE FROM attendances WHERE appointment_id IN
                    (SELECT id FROM appointments WHERE case_id IN ({$in}))"
            )->execute($params);
            $pdo->prepare("DELETE FROM appointments WHERE case_id IN ({$in})")->execute($params);
            $pdo->prepare("DELETE FROM cases WHERE id IN ({$in})")->execute($params);
            if ($propia) {
                $pdo->commit();
            }
        } catch (Throwable $e) {
            if ($propia && $pdo->inTransaction()) {
                $pdo->rollBack();
            }
            throw $e;
        }
        return $impacto;
    }

    // -----------------------------------------------------------------
    // Interno
    // -----------------------------------------------------------------

    /** Ids no vacíos, sin repetidos y reindexados (lo que llega de un form de checkboxes). */
    public static function limpiarIds(array $caseIds): array
    {
        $out = [];
        foreach ($caseIds as $id) {
            $id = trim((string) $id);
            if ($id !== '') {
                $out[$id] = true;
            }
        }
        return array_keys($out);
    }

    /** ('?,?,?', [ids]) para un IN dinámico. */
    private static function inClause(array $caseIds): array
    {
        return [implode(',', array_fill(0, count($caseIds), '?')), array_values($caseIds)];
    }

    private static function scalar(PDO $pdo, string $sql, array $params)
    {
        $stmt = $pdo->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetchColumn();
    }

    /**
     * UPDATE sobre un conjunto de fichas. `$extraWhere` acota además de los
     * ids (ej. "solo las que no estaban archivadas"), y es lo que hace que
     * el contador devuelto sea lo que REALMENTE cambió y no cuántas venían
     * tildadas.
     */
    private static function updateCases(array $caseIds, string $set, array $setParams, string $extraWhere = ''): int
    {
        Db::migrateCaseLibraryIfNeeded();
        $caseIds = self::limpiarIds($caseIds);
        if ($caseIds === []) {
            return 0;
        }
        [$in, $idParams] = self::inClause($caseIds);
        $where = "id IN ({$in})" . ($extraWhere !== '' ? " AND {$extraWhere}" : '');
        $stmt = Db::get()->prepare("UPDATE cases SET {$set} WHERE {$where}");
        $stmt->execute(array_merge($setParams, $idParams));
        return $stmt->rowCount();
    }
}
