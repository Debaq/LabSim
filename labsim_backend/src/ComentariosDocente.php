<?php

declare(strict_types=1);

/**
 * Editar y eliminar lo que el docente escribió en una atención
 * (admin/chat_detail.php): el comentario sobre la evolución o el
 * procedimiento (attendance_comments), el de un turno del chat
 * (chat_comments) y su respuesta en el hilo del alumno
 * (attendance_comment_replies, autor 'docente').
 *
 * Cada docente toca solo lo suyo; el admin completo, todo. Lo que escribió
 * el alumno no se edita ni se borra desde aquí. Eliminar un comentario de
 * la atención se lleva su hilo entero (las respuestas cuelgan de él).
 * Ver docs/decisiones.md (2026-11-12).
 */
final class ComentariosDocente
{
    public const TIPOS = ['atencion', 'chat', 'respuesta'];

    /**
     * La fila (id, author_id) si `id` es de ese tipo y pertenece a la
     * atención appointmentId/studentId; null si no. Es el candado: sin
     * esto, editando el POST se tocaría el comentario de otra atención.
     */
    public static function buscar(PDO $pdo, string $tipo, int $id, int $appointmentId, int $studentId): ?array
    {
        switch ($tipo) {
            case 'atencion':
                $sql = 'SELECT ac.id, ac.teacher_id AS author_id
                        FROM attendance_comments ac JOIN attendances att ON att.id = ac.attendance_id
                        WHERE ac.id = ? AND att.appointment_id = ? AND att.student_id = ?';
                break;
            case 'chat':
                $sql = 'SELECT c.id, c.teacher_id AS author_id
                        FROM chat_comments c JOIN llm_chat_logs l ON l.id = c.chat_log_id
                        WHERE c.id = ? AND l.appointment_id = ? AND l.student_id = ?';
                break;
            case 'respuesta':
                if (!ComentarioRespuestas::listo($pdo)) {
                    return null;
                }
                $sql = "SELECT r.id, r.author_id
                        FROM attendance_comment_replies r
                        JOIN attendance_comments ac ON ac.id = r.comment_id
                        JOIN attendances att ON att.id = ac.attendance_id
                        WHERE r.id = ? AND r.autor = 'docente' AND att.appointment_id = ? AND att.student_id = ?";
                break;
            default:
                return null;
        }
        $stmt = $pdo->prepare($sql);
        $stmt->execute([$id, $appointmentId, $studentId]);
        $fila = $stmt->fetch();
        return $fila ?: null;
    }

    /** Lo escribió él, o es admin completo. */
    public static function puedeTocar(int $authorId, int $meId, bool $isFullAdmin): bool
    {
        return $isFullAdmin || $authorId === $meId;
    }

    /** Cambia el texto. Vacío no se guarda: para eso está eliminar. */
    public static function editar(PDO $pdo, string $tipo, int $id, string $texto): bool
    {
        $texto = ComentarioRespuestas::limpiar($texto);
        if ($texto === null) {
            return false;
        }
        $sql = [
            'atencion' => 'UPDATE attendance_comments SET comment = ? WHERE id = ?',
            'chat' => 'UPDATE chat_comments SET comment = ? WHERE id = ?',
            'respuesta' => 'UPDATE attendance_comment_replies SET texto = ? WHERE id = ?',
        ][$tipo] ?? null;
        if ($sql === null) {
            return false;
        }
        $pdo->prepare($sql)->execute([$texto, $id]);
        return true;
    }

    public static function borrar(PDO $pdo, string $tipo, int $id): void
    {
        if ($tipo === 'atencion') {
            $propia = !$pdo->inTransaction();
            if ($propia) {
                $pdo->beginTransaction();
            }
            try {
                // El hilo cuelga del comentario (PRAGMA foreign_keys=ON).
                if (ComentarioRespuestas::listo($pdo)) {
                    $pdo->prepare('DELETE FROM attendance_comment_replies WHERE comment_id = ?')->execute([$id]);
                }
                $pdo->prepare('DELETE FROM attendance_comments WHERE id = ?')->execute([$id]);
                if ($propia) {
                    $pdo->commit();
                }
            } catch (Throwable $e) {
                if ($propia) {
                    $pdo->rollBack();
                }
                throw $e;
            }
        } elseif ($tipo === 'chat') {
            $pdo->prepare('DELETE FROM chat_comments WHERE id = ?')->execute([$id]);
        } elseif ($tipo === 'respuesta') {
            $pdo->prepare("DELETE FROM attendance_comment_replies WHERE id = ? AND autor = 'docente'")->execute([$id]);
        }
    }
}
