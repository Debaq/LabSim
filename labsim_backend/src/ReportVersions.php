<?php

declare(strict_types=1);

require_once __DIR__ . '/ReportFile.php';

/**
 * Versiones de un informe que otra subida pisó (ver report_versions en
 * schema.sql y report_upload.php). Pasa cuando el alumno siguió en otro
 * equipo o retomó sin red y el módulo arrancó vacío: lo anterior no se
 * pierde, queda acá para que el docente lo mire o lo vuelva a poner.
 */
final class ReportVersions
{
    /** Cuántas versiones apartadas tiene cada informe: [report_id => n]. */
    public static function contar(array $reportIds): array
    {
        $reportIds = array_values(array_unique(array_map('intval', $reportIds)));
        if (!$reportIds) {
            return [];
        }
        $pdo = Db::get();
        if (!self::tablaExiste($pdo)) {
            return [];
        }
        $stmt = $pdo->prepare(
            'SELECT report_id, COUNT(*) AS n FROM report_versions
             WHERE report_id IN (' . implode(',', array_fill(0, count($reportIds), '?')) . ')
             GROUP BY report_id'
        );
        $stmt->execute($reportIds);
        $salida = [];
        foreach ($stmt->fetchAll() as $fila) {
            $salida[(int) $fila['report_id']] = (int) $fila['n'];
        }
        return $salida;
    }

    /** El informe con su alumno (para el control de acceso), o null. */
    public static function informe(int $reportId): ?array
    {
        $stmt = Db::get()->prepare(
            'SELECT r.id, r.tipo, r.data, r.version, r.updated_at, att.student_id,
                    att.appointment_id, att.estado
             FROM reports r JOIN attendances att ON att.id = r.attendance_id
             WHERE r.id = ?'
        );
        $stmt->execute([$reportId]);
        $fila = $stmt->fetch();
        return $fila ?: null;
    }

    /** Las versiones apartadas, la más nueva primero. */
    public static function listar(int $reportId): array
    {
        $pdo = Db::get();
        if (!self::tablaExiste($pdo)) {
            return [];
        }
        $stmt = $pdo->prepare(
            'SELECT id, version, data, guardado_at, reemplazado_at FROM report_versions
             WHERE report_id = ? ORDER BY id DESC'
        );
        $stmt->execute([$reportId]);
        return $stmt->fetchAll();
    }

    /**
     * Vuelve a poner una versión apartada como la actual. La actual no se
     * pierde: pasa a ser una versión apartada más. El PDF se rehace al
     * pedirlo; las imágenes son las de la última subida.
     */
    public static function restaurar(int $reportId, int $versionId): void
    {
        $pdo = Db::get();
        $pdo->beginTransaction();
        try {
            $stmt = $pdo->prepare('SELECT data FROM report_versions WHERE id = ? AND report_id = ?');
            $stmt->execute([$versionId, $reportId]);
            $data = $stmt->fetchColumn();
            if ($data === false) {
                throw new InvalidArgumentException('Esa versión no es de este informe.');
            }
            $stmt = $pdo->prepare('SELECT data, version, updated_at FROM reports WHERE id = ?');
            $stmt->execute([$reportId]);
            $actual = $stmt->fetch();
            if (!$actual) {
                throw new InvalidArgumentException('Informe no encontrado.');
            }
            $pdo->prepare(
                'INSERT INTO report_versions (report_id, version, data, guardado_at) VALUES (?, ?, ?, ?)'
            )->execute([$reportId, (int) $actual['version'], $actual['data'], $actual['updated_at']]);
            $pdo->prepare(
                'UPDATE reports SET data = ?, version = version + 1, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
            )->execute([$data, $reportId]);
            $pdo->commit();
        } catch (Throwable $e) {
            $pdo->rollBack();
            throw $e;
        }
        ReportFile::deletePdf($reportId);
    }

    /**
     * Una línea para reconocer la versión sin abrir el JSON: cuántas curvas
     * o resultados tiene y el comienzo de la conclusión.
     */
    public static function resumen(string $dataJson): string
    {
        $data = json_decode($dataJson, true);
        if (!is_array($data)) {
            return 'datos ilegibles';
        }
        $partes = [];
        foreach (['curvas' => 'curvas', 'resultados' => 'resultados', 'oidos' => 'oídos'] as $clave => $rotulo) {
            if (isset($data[$clave]) && is_array($data[$clave])) {
                $partes[] = count($data[$clave]) . ' ' . $rotulo;
            }
        }
        $conclusion = '';
        foreach (['conclusion', 'conclusión', 'texto'] as $clave) {
            if (isset($data[$clave]) && is_string($data[$clave]) && trim($data[$clave]) !== '') {
                $conclusion = trim($data[$clave]);
                break;
            }
        }
        if ($conclusion !== '') {
            $corto = mb_substr($conclusion, 0, 80);
            $partes[] = '"' . $corto . (mb_strlen($conclusion) > 80 ? '…' : '') . '"';
        }
        return $partes ? implode(' · ', $partes) : 'sin curvas ni conclusión';
    }

    private static function tablaExiste(PDO $pdo): bool
    {
        $stmt = $pdo->prepare("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'report_versions'");
        $stmt->execute();
        return (bool) $stmt->fetchColumn();
    }
}
