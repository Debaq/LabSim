<?php

declare(strict_types=1);

require_once __DIR__ . '/CaseCompleteness.php';

/**
 * Práctica libre: pacientes que el alumno abre cuando quiera (en su casa,
 * por ejemplo) y cuantas veces quiera. Desde el 2026-10-28 son los pacientes
 * del libro, en carpetas (una por capítulo) con el orden que se les dé, y la
 * misma para todos: ver practice_folders y practice_items en sql/schema.sql
 * y docs/roadmap_practica_libro.md. La lista por curso de antes
 * (practice_cases) quedó solo como historia de los intentos viejos.
 *
 * Cada intento es una cita propia en appointments (practice_item_id = el
 * paciente de la carpeta, asignada al alumno, con la fecha y hora en que la
 * abrió). Así la atención, los informes, el chat, la técnica de audiometría
 * y la OIRS funcionan igual que en un práctico, sin un camino aparte. El
 * costo es que toda vista de agenda o estadística de PRÁCTICOS tiene que
 * dejar fuera estas citas: para eso están sinPractica() y marca().
 *
 * Intentos ilimitados y separados; al cerrar, la ficha de estudio del caso
 * se libera o no según la casilla de cada paciente; en las estadísticas va
 * aparte de los prácticos.
 */
final class Practica
{
    /**
     * ¿La base ya tiene practice_cases y appointments.practice_id? Si no, lo
     * crea al vuelo. Nunca lanza: entre el despliegue y "Aplicar schema" lo
     * llaman sync.php y la agenda, y una migración que revienta en un
     * endpoint así tumba la app entera (incidente de informes, 2026-10-08).
     * Si no se pudo, las consultas siguen como antes de la práctica.
     */
    public static function listo(): bool
    {
        static $listo = null;
        if ($listo !== null) {
            return $listo;
        }
        $marca = __DIR__ . '/../data/.migracion_practica_fallo';
        $reciente = is_file($marca) && (time() - (int) @filemtime($marca)) < 3600;
        try {
            $cols = array_column(Db::get()->query('PRAGMA table_info(appointments)')->fetchAll(), 'name');
            $listo = in_array('practice_id', $cols, true);
            if (!$listo && !$reciente) {
                Db::migratePracticeIfNeeded();
                $cols = array_column(Db::get()->query('PRAGMA table_info(appointments)')->fetchAll(), 'name');
                $listo = in_array('practice_id', $cols, true);
            }
        } catch (Throwable $e) {
            error_log('[Practica::listo] ' . $e->getMessage());
            @file_put_contents($marca, date('c') . ' ' . $e->getMessage() . "\n");
            $listo = false;
        }
        if ($listo && is_file($marca)) {
            @unlink($marca);
        }
        return $listo;
    }

    /**
     * ¿La base ya tiene las carpetas (practice_items y
     * appointments.practice_item_id)? No las crea: eso lo hace "Aplicar
     * schema" o la página de la práctica libre (Db::migratePracticeFoldersIfNeeded).
     * Sin ellas, la práctica libre sale vacía.
     */
    public static function carpetasListas(): bool
    {
        static $listas = null;
        if ($listas !== null) {
            return $listas;
        }
        try {
            $pdo = Db::get();
            $tabla = $pdo->query("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'practice_items'")->fetchColumn();
            $cols = array_column($pdo->query('PRAGMA table_info(appointments)')->fetchAll(), 'name');
            $listas = $tabla !== false && in_array('practice_item_id', $cols, true);
        } catch (Throwable $e) {
            error_log('[Practica::carpetasListas] ' . $e->getMessage());
            $listas = false;
        }
        return $listas;
    }

    /**
     * ¿Existe practice_folders.solo_admin? Lo agrega "Aplicar schema"
     * (Db::migratePracticeFoldersIfNeeded); antes de eso no hay carpetas
     * solo para el admin y no se filtra nada (la consulta con la columna
     * fallaría y dejaría sin práctica a todos).
     */
    public static function soloAdminListo(): bool
    {
        static $listo = null;
        if ($listo === null) {
            try {
                $cols = array_column(Db::get()->query('PRAGMA table_info(practice_folders)')->fetchAll(), 'name');
                $listo = in_array('solo_admin', $cols, true);
            } catch (Throwable $e) {
                $listo = false;
            }
        }
        return $listo;
    }

    /**
     * ¿Existe practice_folders.grupo (el libro que agrupa sus capítulos)? Lo
     * agrega "Aplicar schema"; antes, las carpetas van sueltas.
     */
    public static function grupoListo(): bool
    {
        static $listo = null;
        if ($listo === null) {
            try {
                $cols = array_column(Db::get()->query('PRAGMA table_info(practice_folders)')->fetchAll(), 'name');
                $listo = in_array('grupo', $cols, true);
            } catch (Throwable $e) {
                $listo = false;
            }
        }
        return $listo;
    }

    /** Lo que se agrega al JOIN de practice_folders para quien no es admin. */
    private static function filtroSoloAdmin(bool $verSoloAdmin): string
    {
        return !$verSoloAdmin && self::soloAdminListo() ? ' AND f.solo_admin = 0' : '';
    }

    /** Condición SQL "es cita de práctico" (no intento de práctica). */
    public static function sinPractica(string $alias = ''): string
    {
        if (!self::listo()) {
            return '1=1';
        }
        $a = $alias !== '' ? $alias . '.' : '';
        return self::carpetasListas()
            ? "({$a}practice_id IS NULL AND {$a}practice_item_id IS NULL)"
            : "{$a}practice_id IS NULL";
    }

    /** Condición SQL "es intento de práctica". */
    public static function soloPractica(string $alias = ''): string
    {
        if (!self::listo()) {
            return '0=1';
        }
        $a = $alias !== '' ? $alias . '.' : '';
        return self::carpetasListas()
            ? "({$a}practice_id IS NOT NULL OR {$a}practice_item_id IS NOT NULL)"
            : "{$a}practice_id IS NOT NULL";
    }

    /**
     * Expresión SQL que no es NULL justo en los intentos de práctica, de la
     * lista vieja o de las carpetas: para leerla como `... AS practice_id`
     * donde solo importa si es intento o no.
     */
    public static function marca(string $alias = ''): string
    {
        if (!self::listo()) {
            return 'NULL';
        }
        $a = $alias !== '' ? $alias . '.' : '';
        return self::carpetasListas() ? "COALESCE({$a}practice_id, {$a}practice_item_id)" : "{$a}practice_id";
    }

    // -- Carpetas: lo que arma el admin en el panel (admin/practica.php) -----

    /**
     * Las carpetas activas en orden, cada una con sus pacientes activos en
     * orden, con cuántos alumnos los practicaron y cuántos intentos cerrados
     * suman. Para el panel.
     */
    public static function carpetas(): array
    {
        if (!self::carpetasListas()) {
            return [];
        }
        $pdo = Db::get();
        $grupo = self::grupoListo() ? 'grupo' : 'NULL AS grupo';
        $carpetas = $pdo->query(
            "SELECT id, nombre, orden, {$grupo} FROM practice_folders WHERE active = 1 ORDER BY orden, id"
        )->fetchAll();
        $stmt = $pdo->query(
            "SELECT pi.id, pi.folder_id, pi.case_id, pi.procedimiento, pi.show_study_sheet, pi.orden,
                    c.archived_at, p.nombre, p.apellido,
                    (SELECT COUNT(*) FROM attendances att JOIN appointments a ON a.id = att.appointment_id
                      WHERE a.practice_item_id = pi.id AND att.estado = 'atendido') AS intentos,
                    (SELECT COUNT(DISTINCT att.student_id) FROM attendances att JOIN appointments a ON a.id = att.appointment_id
                      WHERE a.practice_item_id = pi.id AND att.estado = 'atendido') AS alumnos
               FROM practice_items pi
               JOIN cases c ON c.id = pi.case_id
               LEFT JOIN patients p ON p.id = c.patient_id
              WHERE pi.active = 1
              ORDER BY pi.orden, pi.id"
        );
        $porCarpeta = [];
        foreach ($stmt->fetchAll() as $it) {
            $porCarpeta[(int) $it['folder_id']][] = $it;
        }
        foreach ($carpetas as &$c) {
            $c['id'] = (int) $c['id'];
            $c['grupo'] = $c['grupo'] !== null && $c['grupo'] !== '' ? (string) $c['grupo'] : null;
            $c['items'] = $porCarpeta[$c['id']] ?? [];
        }
        unset($c);
        return $carpetas;
    }

    public static function crearCarpeta(string $nombre, int $userId, string $grupo = ''): ?string
    {
        $nombre = trim($nombre);
        $grupo = trim($grupo);
        if ($nombre === '') {
            return 'Falta el nombre de la carpeta.';
        }
        if (!self::carpetasListas()) {
            return 'La base todavía no tiene las carpetas: aplica el schema en Base de datos.';
        }
        $conGrupo = $grupo !== '' && self::grupoListo();
        Db::reintentar(static function () use ($nombre, $userId, $grupo, $conGrupo): void {
            $pdo = Db::get();
            $orden = (int) $pdo->query('SELECT COALESCE(MAX(orden), 0) + 1 FROM practice_folders WHERE active = 1')->fetchColumn();
            if ($conGrupo) {
                $pdo->prepare('INSERT INTO practice_folders (nombre, orden, created_by, grupo) VALUES (?, ?, ?, ?)')
                    ->execute([$nombre, $orden, $userId, $grupo]);
            } else {
                $pdo->prepare('INSERT INTO practice_folders (nombre, orden, created_by) VALUES (?, ?, ?)')
                    ->execute([$nombre, $orden, $userId]);
            }
        });
        return null;
    }

    /**
     * El libro (o la carpeta que la contiene) de una carpeta; vacío = suelta.
     * Ver practice_folders.grupo.
     */
    public static function cambiarGrupo(int $folderId, string $grupo): ?string
    {
        if (!self::grupoListo()) {
            return 'La base todavía no tiene la columna del libro: aplica el schema en Base de datos.';
        }
        $grupo = trim($grupo);
        Db::reintentar(static function () use ($folderId, $grupo): void {
            Db::get()->prepare('UPDATE practice_folders SET grupo = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
                ->execute([$grupo === '' ? null : $grupo, $folderId]);
        });
        return null;
    }

    /** Los libros que ya existen, para proponerlos al crear o mover una carpeta. */
    public static function grupos(): array
    {
        if (!self::grupoListo()) {
            return [];
        }
        $filas = Db::get()->query(
            "SELECT DISTINCT grupo FROM practice_folders WHERE active = 1 AND grupo IS NOT NULL AND grupo <> '' ORDER BY grupo"
        )->fetchAll();
        return array_map('strval', array_column($filas, 'grupo'));
    }

    /**
     * Las carpetas agrupadas por libro, en el orden de la primera carpeta de
     * cada uno; las sueltas, cada una en su propio bloque sin libro. Lo que
     * ve el panel y lo mismo que arma la app (Agenda._armar_carpetas).
     *
     * @return list<array{grupo:?string, carpetas:list<array>}>
     */
    public static function agrupar(array $carpetas): array
    {
        $bloques = [];
        $indice = [];
        foreach ($carpetas as $c) {
            $g = $c['grupo'] ?? null;
            if ($g === null) {
                $bloques[] = ['grupo' => null, 'carpetas' => [$c]];
                continue;
            }
            if (!isset($indice[$g])) {
                $indice[$g] = count($bloques);
                $bloques[] = ['grupo' => $g, 'carpetas' => []];
            }
            $bloques[$indice[$g]]['carpetas'][] = $c;
        }
        return $bloques;
    }

    public static function renombrarCarpeta(int $folderId, string $nombre): ?string
    {
        $nombre = trim($nombre);
        if ($nombre === '') {
            return 'Falta el nombre de la carpeta.';
        }
        Db::reintentar(static function () use ($folderId, $nombre): void {
            Db::get()->prepare('UPDATE practice_folders SET nombre = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
                ->execute([$nombre, $folderId]);
        });
        return null;
    }

    /** Solo una carpeta vacía: sacar primero sus pacientes es lo que se ve venir. */
    public static function borrarCarpeta(int $folderId): ?string
    {
        $stmt = Db::get()->prepare('SELECT COUNT(*) FROM practice_items WHERE folder_id = ? AND active = 1');
        $stmt->execute([$folderId]);
        $n = (int) $stmt->fetchColumn();
        $stmt->closeCursor();
        if ($n > 0) {
            return 'La carpeta todavía tiene pacientes: sácalos primero.';
        }
        Db::reintentar(static function () use ($folderId): void {
            Db::get()->prepare('UPDATE practice_folders SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
                ->execute([$folderId]);
        });
        return null;
    }

    /** Sube (-1) o baja (+1) una carpeta un lugar. */
    public static function moverCarpeta(int $folderId, int $sentido): void
    {
        self::mover('practice_folders', $folderId, $sentido, 'active = 1');
    }

    /** Sube (-1) o baja (+1) un paciente un lugar dentro de su carpeta. */
    public static function moverPaciente(int $itemId, int $sentido): void
    {
        $stmt = Db::get()->prepare('SELECT folder_id FROM practice_items WHERE id = ?');
        $stmt->execute([$itemId]);
        $folderId = $stmt->fetchColumn();
        $stmt->closeCursor();
        if ($folderId !== false) {
            self::mover('practice_items', $itemId, $sentido, 'active = 1 AND folder_id = ' . (int) $folderId);
        }
    }

    /**
     * Cambia de lugar con el vecino intercambiando sus números, sin
     * renumerar el resto: el número de un paciente es el de su caso en el
     * libro (caso 1.4), y los huecos (los que LabSim no simula) se respetan.
     * Solo si dos tienen el mismo número se renumera 1..n antes, porque si
     * no el intercambio no movería nada.
     */
    private static function mover(string $tabla, int $id, int $sentido, string $donde): void
    {
        Db::reintentar(static function () use ($tabla, $id, $sentido, $donde): void {
            $pdo = Db::get();
            $filas = $pdo->query("SELECT id, orden FROM {$tabla} WHERE {$donde} ORDER BY orden, id")->fetchAll();
            $ordenes = array_map('intval', array_column($filas, 'orden', 'id'));
            if (count(array_unique($ordenes)) < count($ordenes)) {
                $ordenes = array_combine(array_keys($ordenes), range(1, count($ordenes)));
            }
            $ids = array_keys($ordenes);
            $i = array_search($id, $ids, true);
            $j = $i === false ? false : $i + ($sentido < 0 ? -1 : 1);
            if ($j !== false && isset($ids[$j])) {
                [$ordenes[$ids[$i]], $ordenes[$ids[$j]]] = [$ordenes[$ids[$j]], $ordenes[$ids[$i]]];
            }
            $pdo->beginTransaction();
            try {
                $upd = $pdo->prepare("UPDATE {$tabla} SET orden = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?");
                foreach ($ordenes as $cada => $orden) {
                    $upd->execute([$orden, $cada]);
                }
                $pdo->commit();
            } catch (Throwable $e) {
                $pdo->rollBack();
                throw $e;
            }
        });
    }

    /** Fichas que se pueden sumar a una carpeta: no archivadas y que no estén ya en ella. */
    public static function casosParaAgregar(int $folderId): array
    {
        if (!self::carpetasListas()) {
            return [];
        }
        $stmt = Db::get()->prepare(
            "SELECT c.id, p.nombre, p.apellido
               FROM cases c
               LEFT JOIN patients p ON p.id = c.patient_id
              WHERE c.archived_at IS NULL
                AND c.id NOT IN (SELECT case_id FROM practice_items WHERE folder_id = ? AND active = 1)
              ORDER BY p.apellido, p.nombre, c.id"
        );
        $stmt->execute([$folderId]);
        return $stmt->fetchAll();
    }

    /** Suma un paciente al final de una carpeta. Devuelve el error para el admin, o null. */
    public static function agregarPaciente(int $folderId, string $caseId, string $procedimiento, bool $mostrarFicha, int $userId): ?string
    {
        if (!self::carpetasListas()) {
            return 'La base todavía no tiene las carpetas: aplica el schema en Base de datos.';
        }
        $pdo = Db::get();
        $stmt = $pdo->prepare('SELECT data, archived_at FROM cases WHERE id = ?');
        $stmt->execute([$caseId]);
        $filas = $stmt->fetchAll();
        if (!$filas) {
            return 'No existe esa ficha.';
        }
        if ($filas[0]['archived_at'] !== null) {
            return 'Esa ficha está archivada.';
        }
        // Mismo criterio que agendar: un caso al que le falta lo que no se
        // puede calcular deja al alumno con un paciente que no cierra.
        $data = json_decode((string) $filas[0]['data'], true);
        $faltantes = CaseCompleteness::pendingTexts(is_array($data) ? $data : []);
        if ($faltantes !== []) {
            return 'El caso ' . $caseId . ' está incompleto y no se puede dejar para práctica: ' . implode(' | ', $faltantes);
        }
        $procedimiento = trim($procedimiento) !== '' ? trim($procedimiento) : 'Audiometría';
        // Si ya estuvo y se sacó, vuelve la misma fila (al final): sus
        // intentos viejos siguen colgando de ella.
        Db::reintentar(static function () use ($pdo, $folderId, $caseId, $procedimiento, $mostrarFicha, $userId): void {
            $stmt = $pdo->prepare('SELECT COALESCE(MAX(orden), 0) + 1 FROM practice_items WHERE folder_id = ? AND active = 1');
            $stmt->execute([$folderId]);
            $orden = (int) $stmt->fetchColumn();
            $stmt->closeCursor();
            $pdo->prepare(
                'INSERT INTO practice_items (folder_id, case_id, procedimiento, show_study_sheet, orden, created_by)
                 VALUES (?, ?, ?, ?, ?, ?)
                 ON CONFLICT(folder_id, case_id) DO UPDATE SET
                    active = 1, procedimiento = excluded.procedimiento, orden = excluded.orden,
                    show_study_sheet = excluded.show_study_sheet, updated_at = CURRENT_TIMESTAMP'
            )->execute([$folderId, $caseId, $procedimiento, $mostrarFicha ? 1 : 0, $orden, $userId]);
        });
        return null;
    }

    public static function quitarPaciente(int $itemId): void
    {
        Db::reintentar(static function () use ($itemId): void {
            Db::get()->prepare('UPDATE practice_items SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
                ->execute([$itemId]);
        });
    }

    public static function setMostrarFicha(int $itemId, bool $mostrar): void
    {
        Db::reintentar(static function () use ($itemId, $mostrar): void {
            Db::get()->prepare('UPDATE practice_items SET show_study_sheet = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
                ->execute([$mostrar ? 1 : 0, $itemId]);
        });
    }

    // -- Lo que ve la app ------------------------------------------------------

    /**
     * Las carpetas con pacientes, en orden, para la app. El alumno ve sus
     * propios intentos (cerrados, el último y el que tenga abierto); el
     * docente (`$docente`), los de todos los alumnos, sin abierto: él la abre
     * en modo prueba. Las carpetas sin pacientes no salen.
     *
     * @return array<int, array{id:int, nombre:string, orden:int, items:array}>
     */
    /**
     * `$verSoloAdmin`: también las carpetas solo_admin (demo interna, p. ej.
     * los pacientes nasales: docs/roadmap_nasal.md). Solo permission 777;
     * un docente (555) tampoco las ve.
     */
    public static function lista(int $userId, bool $docente, bool $verSoloAdmin = false): array
    {
        $soloAdmin = self::filtroSoloAdmin($verSoloAdmin);
        if (!self::carpetasListas()) {
            return [];
        }
        $grupo = self::grupoListo() ? 'f.grupo' : 'NULL';
        $pdo = Db::get();
        $deQuien = $docente ? '' : ' AND att.student_id = :me';
        $stmt = $pdo->prepare(
            "SELECT pi.id, pi.folder_id, pi.case_id, pi.procedimiento, pi.show_study_sheet, pi.orden,
                    f.nombre AS carpeta, {$grupo} AS grupo,
                    p.nombre, p.apellido, p.rut, p.fecha_nac,
                    (SELECT COUNT(*) FROM attendances att JOIN appointments a ON a.id = att.appointment_id
                      WHERE a.practice_item_id = pi.id AND att.estado = 'atendido'{$deQuien}) AS intentos,
                    (SELECT COUNT(DISTINCT att.student_id) FROM attendances att JOIN appointments a ON a.id = att.appointment_id
                      WHERE a.practice_item_id = pi.id AND att.estado = 'atendido'{$deQuien}) AS alumnos,
                    (SELECT MAX(att.updated_at) FROM attendances att JOIN appointments a ON a.id = att.appointment_id
                      WHERE a.practice_item_id = pi.id AND att.estado = 'atendido'{$deQuien}) AS ultimo,
                    (SELECT a.id FROM attendances att JOIN appointments a ON a.id = att.appointment_id
                      WHERE a.practice_item_id = pi.id AND att.estado = 'atendido'{$deQuien}
                      ORDER BY att.updated_at DESC, a.id DESC LIMIT 1) AS ultimo_cerrado
               FROM practice_items pi
               JOIN practice_folders f ON f.id = pi.folder_id AND f.active = 1{$soloAdmin}
               JOIN cases c ON c.id = pi.case_id AND c.archived_at IS NULL
               LEFT JOIN patients p ON p.id = c.patient_id
              WHERE pi.active = 1
              ORDER BY f.orden, f.id, pi.orden, pi.id"
        );
        if (!$docente) {
            $stmt->bindValue(':me', $userId, PDO::PARAM_INT);
        }
        $stmt->execute();
        $filas = $stmt->fetchAll();
        $carpetas = [];
        foreach ($filas as $it) {
            $fid = (int) $it['folder_id'];
            if (!isset($carpetas[$fid])) {
                $carpetas[$fid] = ['id' => $fid, 'nombre' => (string) $it['carpeta'],
                                   'grupo' => $it['grupo'] !== null && $it['grupo'] !== '' ? (string) $it['grupo'] : null,
                                   'orden' => count($carpetas) + 1, 'items' => []];
            }
            $it['grupo'] = $carpetas[$fid]['grupo'];
            $it['id'] = (int) $it['id'];
            $it['folder_id'] = $fid;
            // El número del caso en su capítulo (caso 1.4 -> 4), aunque falten
            // los que LabSim no simula: así calza con el libro.
            $it['orden'] = (int) $it['orden'];
            $it['intentos'] = (int) $it['intentos'];
            $it['alumnos'] = (int) $it['alumnos'];
            $it['show_study_sheet'] = (bool) $it['show_study_sheet'];
            $it['ultimo_cerrado'] = !$docente && $it['ultimo_cerrado'] !== null ? (int) $it['ultimo_cerrado'] : null;
            $it['abierto'] = $docente ? null : self::intentoAbierto($it['id'], $userId);
            $carpetas[$fid]['items'][] = $it;
        }
        return array_values($carpetas);
    }

    /**
     * Avance del alumno en el libro: por carpeta, cuántos casos tiene y en
     * cuántos cerró al menos un intento. Lo mismo que cuenta la app arriba de
     * las carpetas (Agenda._mostrar_avance), para el portal del alumno. Un
     * paciente en dos carpetas son dos casos: en cada una se practica otro
     * examen.
     *
     * @return array{casos:int, hechos:int, carpetas:list<array{nombre:string, casos:int, hechos:int}>}
     */
    public static function avance(int $userId): array
    {
        $vacio = ['casos' => 0, 'hechos' => 0, 'carpetas' => []];
        if (!self::carpetasListas()) {
            return $vacio;
        }
        $stmt = Db::get()->prepare(
            "SELECT f.nombre, COUNT(*) AS casos,
                    SUM(EXISTS (SELECT 1 FROM attendances att JOIN appointments a ON a.id = att.appointment_id
                                 WHERE a.practice_item_id = pi.id AND att.estado = 'atendido'
                                   AND att.student_id = :me)) AS hechos
               FROM practice_items pi
               JOIN practice_folders f ON f.id = pi.folder_id AND f.active = 1
               JOIN cases c ON c.id = pi.case_id AND c.archived_at IS NULL
              WHERE pi.active = 1
              GROUP BY f.id
              ORDER BY f.orden, f.id"
        );
        $stmt->bindValue(':me', $userId, PDO::PARAM_INT);
        $stmt->execute();
        $avance = $vacio;
        foreach ($stmt->fetchAll() as $f) {
            $carpeta = ['nombre' => (string) $f['nombre'], 'casos' => (int) $f['casos'], 'hechos' => (int) $f['hechos']];
            $avance['carpetas'][] = $carpeta;
            $avance['casos'] += $carpeta['casos'];
            $avance['hechos'] += $carpeta['hechos'];
        }
        return $avance;
    }

    /**
     * Cita del intento que el alumno dejó a medias en este paciente, o null.
     * Cuenta también la cita creada sin atención todavía (la app se cayó
     * entre "Practicar" y marcar "atendiendo"): sin esto quedaría huérfana y
     * cada clic dejaría otra.
     */
    private static function intentoAbierto(int $itemId, int $userId): ?int
    {
        $stmt = Db::get()->prepare(
            "SELECT a.id FROM appointments a
               LEFT JOIN attendances att ON att.appointment_id = a.id AND att.student_id = ?
              WHERE a.practice_item_id = ? AND a.assigned_student_id = ?
                AND (att.id IS NULL OR att.estado = 'atendiendo')
              ORDER BY a.id DESC LIMIT 1"
        );
        $stmt->execute([$userId, $itemId, $userId]);
        $filas = $stmt->fetchAll();
        return $filas ? (int) $filas[0]['id'] : null;
    }

    /**
     * Abre un intento: devuelve la cita (la que quedó abierta, o una nueva).
     * La práctica libre es de todos: no pide curso. La cita lleva el primer
     * curso activo del alumno, si tiene, para que su docente la vea.
     * Lanza RuntimeException con un texto para el alumno si no corresponde.
     */
    public static function iniciar(int $userId, int $itemId, bool $verSoloAdmin = false): array
    {
        if (!self::carpetasListas()) {
            throw new RuntimeException('La práctica libre todavía no está disponible en el servidor.');
        }
        $pdo = Db::get();
        $soloAdmin = self::filtroSoloAdmin($verSoloAdmin);
        $stmt = $pdo->prepare(
            "SELECT pi.id, pi.case_id, pi.procedimiento, c.patient_id, c.data
               FROM practice_items pi
               JOIN practice_folders f ON f.id = pi.folder_id AND f.active = 1{$soloAdmin}
               JOIN cases c ON c.id = pi.case_id AND c.archived_at IS NULL
              WHERE pi.id = ? AND pi.active = 1"
        );
        $stmt->execute([$itemId]);
        $filas = $stmt->fetchAll();
        if (!$filas) {
            throw new RuntimeException('Este paciente ya no está en la práctica libre.');
        }
        $item = $filas[0];

        $abierto = self::intentoAbierto($itemId, $userId);
        if ($abierto === null) {
            $stmt = $pdo->prepare(
                'SELECT cs.course_id FROM course_students cs JOIN courses co ON co.id = cs.course_id AND co.active = 1
                  WHERE cs.user_id = ? ORDER BY cs.course_id LIMIT 1'
            );
            $stmt->execute([$userId]);
            $curso = $stmt->fetchColumn();
            $stmt->closeCursor();
            $identidad = self::identidad($item);
            $abierto = (int) Db::reintentar(static function () use ($pdo, $item, $identidad, $userId, $curso): int {
                // fecha 'dd-MM-yy' y hora 'HH:mm', como toda cita: es cuándo
                // lo abrió, y así se ordena con lo demás en su historial.
                $pdo->prepare(
                    'INSERT INTO appointments (fecha, hora, rut, nombre, apellido, fecha_nac, procedimiento, case_id,
                                               course_id, assigned_student_id, patient_id, practice_item_id)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
                )->execute([
                    date('d-m-y'), date('H:i'),
                    $identidad['rut'], $identidad['nombre'], $identidad['apellido'], $identidad['fecha_nac'],
                    (string) $item['procedimiento'], (string) $item['case_id'],
                    $curso !== false ? (int) $curso : null, $userId,
                    $item['patient_id'] !== null ? (int) $item['patient_id'] : null,
                    (int) $item['id'],
                ]);
                return (int) $pdo->lastInsertId();
            });
        }

        $stmt = $pdo->prepare('SELECT * FROM appointments WHERE id = ?');
        $stmt->execute([$abierto]);
        return Db::castAppointment($stmt->fetchAll()[0]);
    }

    /** Identidad del paciente del caso; si no tiene, la del snapshot de la ficha. */
    private static function identidad(array $item): array
    {
        if ($item['patient_id'] !== null) {
            $stmt = Db::get()->prepare('SELECT rut, nombre, apellido, fecha_nac FROM patients WHERE id = ?');
            $stmt->execute([(int) $item['patient_id']]);
            $filas = $stmt->fetchAll();
            if ($filas) {
                return array_map('strval', $filas[0]);
            }
        }
        $data = json_decode((string) $item['data'], true);
        $snap = is_array($data) && is_array($data['paciente_snapshot'] ?? null) ? $data['paciente_snapshot'] : [];
        return [
            'rut' => (string) ($snap['rut'] ?? ''),
            'nombre' => (string) ($snap['nombre'] ?? ''),
            'apellido' => (string) ($snap['apellido'] ?? ''),
            'fecha_nac' => (string) ($snap['fecha_nac'] ?? ''),
        ];
    }

    /**
     * PDF de la ficha de estudio del caso para el alumno: el mismo que el
     * docente baja con ?modo=estudio en admin/case_sheet_pdf.php (sin perfil
     * auditivo ni mandos del generador). Quien llama ya revisó el permiso
     * con fichaDeEstudioPermitida().
     *
     * @return array{0: string, 1: string} bytes del PDF y nombre de archivo
     */
    public static function pdfFichaDeEstudio(string $caseId, int $userId): array
    {
        require_once __DIR__ . '/CaseSheetPdf.php';
        require_once __DIR__ . '/EstudioRedactor.php';
        $stmt = Db::get()->prepare('SELECT data, patient_id FROM cases WHERE id = ?');
        $stmt->execute([$caseId]);
        $filas = $stmt->fetchAll();
        if (!$filas) {
            throw new RuntimeException('Caso no encontrado.');
        }
        $data = json_decode((string) $filas[0]['data'], true);
        if (!is_array($data)) {
            throw new RuntimeException('La ficha de este caso no se puede leer.');
        }
        // Redactada con IA la primera vez y cacheada en el caso (ver
        // EstudioRedactor): las siguientes, de cualquier alumno, la reusan.
        $data = EstudioRedactor::ensureFresh($caseId, $data, $userId);
        $patient = self::identidad(['patient_id' => $filas[0]['patient_id'], 'data' => json_encode($data)]);
        if ($patient['rut'] === '') {
            $patient['rut'] = 'N/D';
        }
        $bytes = CaseSheetPdf::build($caseId, $data, $patient, '', date('d-m-Y'), true);
        $nombre = 'ficha_estudio_' . CaseSheetPdf::identificador($caseId, $patient) . '.pdf';
        return [$bytes, $nombre];
    }

    /**
     * ¿El alumno puede bajar la ficha de estudio de esta cita? Solo si es un
     * intento suyo de práctica, ya cerrado, y el paciente tiene marcada la
     * casilla (en su carpeta, o en la lista vieja por curso). Devuelve el
     * case_id, o null.
     */
    public static function fichaDeEstudioPermitida(int $appointmentId, int $userId): ?string
    {
        if (!self::listo()) {
            return null;
        }
        $carpetas = self::carpetasListas();
        $sql = "SELECT a.case_id
                  FROM appointments a
                  LEFT JOIN practice_cases pc ON pc.id = a.practice_id"
             . ($carpetas ? ' LEFT JOIN practice_items pi ON pi.id = a.practice_item_id' : '') . "
                  JOIN attendances att ON att.appointment_id = a.id AND att.student_id = ?
                 WHERE a.id = ? AND a.assigned_student_id = ? AND att.estado = 'atendido'
                   AND " . ($carpetas ? 'COALESCE(pc.show_study_sheet, pi.show_study_sheet)' : 'pc.show_study_sheet') . ' = 1';
        $stmt = Db::get()->prepare($sql);
        $stmt->execute([$userId, $appointmentId, $userId]);
        $filas = $stmt->fetchAll();
        return $filas && $filas[0]['case_id'] !== null ? (string) $filas[0]['case_id'] : null;
    }
}
