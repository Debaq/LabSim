<?php

declare(strict_types=1);

/**
 * Feedback al feedback: el hilo que cuelga de un comentario del docente
 * sobre una atención (attendance_comments, secciones evolución y
 * procedimiento). El alumno responde -- qué entendió, qué va a hacer
 * distinto, o por qué no está de acuerdo -- y el docente puede contestarle
 * en el mismo hilo. Ver docs/decisiones.md (2026-11-12).
 *
 * Quién puede escribir en qué hilo lo decide quien llama: el alumno solo en
 * comentarios de SUS atenciones (deAlumno), el docente desde chat_detail.php,
 * que ya viene scopeado a los alumnos de sus cursos.
 *
 * La tabla nace con "Aplicar schema.sql" (nunca se migra desde un endpoint):
 * mientras no exista, listo() es false y todo devuelve vacío -- los
 * comentarios del docente se siguen viendo, solo sin hilo.
 */
final class ComentarioRespuestas
{
    /** Largo máximo de una respuesta: un párrafo, no un informe. */
    public const MAX_CHARS = 2000;

    public static function listo(?PDO $pdo = null): bool
    {
        static $listo = null;
        if ($listo === true) {
            return true;
        }
        $pdo = $pdo ?? Db::get();
        $listo = (bool) $pdo->query(
            "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'attendance_comment_replies'"
        )->fetchColumn();
        return $listo;
    }

    /**
     * Texto listo para guardar, o null si no hay nada que guardar. Recorta
     * espacios y corta en MAX_CHARS (por caracteres, no bytes: es español).
     */
    public static function limpiar(string $texto): ?string
    {
        $texto = trim(str_replace("\r\n", "\n", $texto));
        if ($texto === '') {
            return null;
        }
        if (mb_strlen($texto) > self::MAX_CHARS) {
            $texto = rtrim(mb_substr($texto, 0, self::MAX_CHARS));
        }
        return $texto;
    }

    /**
     * Hilos de varios comentarios: [comment_id => [respuestas en orden]].
     * Cada respuesta trae id, author_id, autor ('alumno'|'docente'), author_name,
     * texto, leido y created_at.
     *
     * @param int[] $commentIds
     */
    public static function porComentario(PDO $pdo, array $commentIds): array
    {
        $commentIds = array_values(array_unique(array_map('intval', $commentIds)));
        if (!$commentIds || !self::listo($pdo)) {
            return [];
        }
        $ph = implode(',', array_fill(0, count($commentIds), '?'));
        $stmt = $pdo->prepare(
            "SELECT r.id, r.comment_id, r.author_id, r.autor, r.texto, r.leido, r.created_at, u.display_name AS author_name
             FROM attendance_comment_replies r JOIN users u ON u.id = r.author_id
             WHERE r.comment_id IN ({$ph}) ORDER BY r.id"
        );
        $stmt->execute($commentIds);
        $out = [];
        foreach ($stmt->fetchAll() as $r) {
            $out[(int) $r['comment_id']][] = [
                'id' => (int) $r['id'],
                'author_id' => (int) $r['author_id'],
                'autor' => (string) $r['autor'],
                'author_name' => (string) $r['author_name'],
                'texto' => (string) $r['texto'],
                'leido' => (bool) $r['leido'],
                'created_at' => (string) $r['created_at'],
            ];
        }
        return $out;
    }

    /**
     * El comentario `commentId` si es de una atención de `studentId`, o
     * null. Es el candado del lado del alumno: sin esto, editando el
     * comment_id se respondería en la atención de otro.
     */
    public static function deAlumno(PDO $pdo, int $commentId, int $studentId): ?array
    {
        $stmt = $pdo->prepare(
            'SELECT ac.id, ac.attendance_id, att.appointment_id
             FROM attendance_comments ac JOIN attendances att ON att.id = ac.attendance_id
             WHERE ac.id = ? AND att.student_id = ?'
        );
        $stmt->execute([$commentId, $studentId]);
        $fila = $stmt->fetch();
        return $fila ?: null;
    }

    /** Agrega una respuesta al hilo y devuelve su id (0 si no se guardó). */
    public static function responder(PDO $pdo, int $commentId, int $authorId, string $autor, string $texto): int
    {
        $texto = self::limpiar($texto);
        if ($texto === null || !in_array($autor, ['alumno', 'docente'], true) || !self::listo($pdo)) {
            return 0;
        }
        $pdo->prepare(
            'INSERT INTO attendance_comment_replies (comment_id, author_id, autor, texto) VALUES (?, ?, ?, ?)'
        )->execute([$commentId, $authorId, $autor, $texto]);
        return (int) $pdo->lastInsertId();
    }

    /**
     * Marca como vistas las respuestas que escribió el OTRO lado en estos
     * comentarios: el docente que abre la atención lee las del alumno.
     *
     * @param int[] $commentIds
     */
    public static function marcarLeidas(PDO $pdo, array $commentIds, string $lector): void
    {
        $commentIds = array_values(array_unique(array_map('intval', $commentIds)));
        if (!$commentIds || !self::listo($pdo)) {
            return;
        }
        $otro = $lector === 'docente' ? 'alumno' : 'docente';
        $ph = implode(',', array_fill(0, count($commentIds), '?'));
        $pdo->prepare(
            "UPDATE attendance_comment_replies SET leido = 1
             WHERE leido = 0 AND autor = ? AND comment_id IN ({$ph})"
        )->execute(array_merge([$otro], $commentIds));
    }

    /**
     * Respuestas del alumno que el docente todavía no vio, por cita:
     * [appointment_id => n]. Para avisar en la ficha del alumno.
     */
    public static function sinLeerDelAlumno(PDO $pdo, int $studentId): array
    {
        if (!self::listo($pdo)) {
            return [];
        }
        $stmt = $pdo->prepare(
            "SELECT att.appointment_id, COUNT(*) AS n
             FROM attendance_comment_replies r
             JOIN attendance_comments ac ON ac.id = r.comment_id
             JOIN attendances att ON att.id = ac.attendance_id
             WHERE att.student_id = ? AND r.autor = 'alumno' AND r.leido = 0
             GROUP BY att.appointment_id"
        );
        $stmt->execute([$studentId]);
        $out = [];
        foreach ($stmt->fetchAll() as $f) {
            $out[(int) $f['appointment_id']] = (int) $f['n'];
        }
        return $out;
    }

    /**
     * Borra los hilos de los comentarios de estas atenciones. Va ANTES de
     * borrar attendance_comments (PRAGMA foreign_keys=ON, ver Db::get()).
     *
     * @param int[] $attendanceIds
     */
    public static function borrarDeAtenciones(PDO $pdo, array $attendanceIds): void
    {
        $attendanceIds = array_values(array_unique(array_map('intval', $attendanceIds)));
        if (!$attendanceIds || !self::listo($pdo)) {
            return;
        }
        $ph = implode(',', array_fill(0, count($attendanceIds), '?'));
        $pdo->prepare(
            "DELETE FROM attendance_comment_replies WHERE comment_id IN
                (SELECT id FROM attendance_comments WHERE attendance_id IN ({$ph}))"
        )->execute($attendanceIds);
    }
}
