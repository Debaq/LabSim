<?php

/**
 * Config compartida con override por curso (app_config, ver comentario de
 * esa tabla en sql/schema.sql). course_id NULL = default global; una fila
 * con course_id resuelto gana sobre esa por esa key para ese curso. Pensado
 * para tablas normativas de examenes (ABR primero, P300/electrococleografía
 * después) que un docente puede querer distintas a las que trae la app por
 * defecto, sin recompilar el cliente de escritorio.
 */
final class AppConfig
{
    /**
     * Valor efectivo para $key en $courseId: la fila de ese curso si existe,
     * si no la global. null si ninguna de las dos existe (la app sigue
     * usando su propio default local, ej. resources/abr/normative_data.json).
     */
    public static function getEffective(string $key, ?int $courseId): ?array
    {
        $pdo = Db::get();
        if ($courseId !== null) {
            $stmt = $pdo->prepare('SELECT v FROM app_config WHERE k = ? AND course_id = ?');
            $stmt->execute([$key, $courseId]);
            $row = $stmt->fetch();
            if ($row) {
                return json_decode($row['v'], true);
            }
        }
        $stmt = $pdo->prepare('SELECT v FROM app_config WHERE k = ? AND course_id IS NULL');
        $stmt->execute([$key]);
        $row = $stmt->fetch();
        return $row ? json_decode($row['v'], true) : null;
    }

    /**
     * Keys cuyo valor efectivo (global u override del curso resuelto) pudo
     * cambiar desde $since -- usado por sync.php para no reenviar config que
     * el cliente ya tiene. No distingue si cambió el lado global o el del
     * curso, solo que alguno de los dos candidatos se tocó: alcanza para
     * decidir qué volver a resolver con getEffective().
     */
    public static function changedKeysSince(string $since, ?int $courseId): array
    {
        $pdo = Db::get();
        if ($courseId !== null) {
            $stmt = $pdo->prepare(
                'SELECT DISTINCT k FROM app_config
                 WHERE updated_at > ? AND (course_id IS NULL OR course_id = ?)'
            );
            $stmt->execute([$since, $courseId]);
        } else {
            $stmt = $pdo->prepare('SELECT DISTINCT k FROM app_config WHERE updated_at > ? AND course_id IS NULL');
            $stmt->execute([$since]);
        }
        return array_column($stmt->fetchAll(), 'k');
    }

    /** Todas las keys con valor efectivo para $courseId (dump inicial completo). */
    public static function allKeys(?int $courseId): array
    {
        $pdo = Db::get();
        if ($courseId !== null) {
            $stmt = $pdo->prepare('SELECT DISTINCT k FROM app_config WHERE course_id IS NULL OR course_id = ?');
            $stmt->execute([$courseId]);
        } else {
            $stmt = $pdo->query('SELECT DISTINCT k FROM app_config WHERE course_id IS NULL');
        }
        return array_column($stmt->fetchAll(), 'k');
    }

    /**
     * Crea/reemplaza el override de $courseId para $key (o el default global
     * si $courseId es null). Upsert manual porque la unicidad vive en un
     * índice parcial (ver schema.sql), no en una PK compuesta que permita
     * "INSERT OR REPLACE" directo cuando course_id es NULL.
     */
    public static function set(string $key, $value, ?int $courseId): void
    {
        $pdo = Db::get();
        $json = json_encode($value, JSON_UNESCAPED_UNICODE);
        if ($courseId !== null) {
            $stmt = $pdo->prepare('SELECT id FROM app_config WHERE k = ? AND course_id = ?');
            $stmt->execute([$key, $courseId]);
        } else {
            $stmt = $pdo->prepare('SELECT id FROM app_config WHERE k = ? AND course_id IS NULL');
            $stmt->execute([$key]);
        }
        $existing = $stmt->fetch();
        if ($existing) {
            $pdo->prepare('UPDATE app_config SET v = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
                ->execute([$json, $existing['id']]);
            return;
        }
        $pdo->prepare('INSERT INTO app_config (k, course_id, v) VALUES (?, ?, ?)')
            ->execute([$key, $courseId, $json]);
    }

    /** Quita el override de $courseId para $key -- vuelve a heredar el global. */
    public static function clearCourseOverride(string $key, int $courseId): void
    {
        Db::get()->prepare('DELETE FROM app_config WHERE k = ? AND course_id = ?')->execute([$key, $courseId]);
    }
}
