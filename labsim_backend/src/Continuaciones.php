<?php

declare(strict_types=1);

/**
 * Continuación de una atención incompleta (agenda relativa, parte 3; ver
 * docs/decisiones.md "Agenda relativa al ingreso del alumno").
 *
 * Al cerrar una atención el alumno puede marcar "Queda incompleta: citar
 * para terminar". El cierre (attendance_action.php, 'atendido' con
 * `continuar`) crea entonces una cita nueva SOLO para ese alumno:
 * mismo caso y paciente, hora fija (sin duración: se atiende en horario
 * libre), fecha y hora del cierre, y `continua_de` apuntando a la original.
 * El plazo (el próximo día de práctico del alumno) no se guarda: lo deriva
 * la app de su agenda, así se ubica solo cuando el docente agenda el día
 * siguiente.
 *
 * Idempotente: la cola de la app puede mandar el mismo cierre dos veces.
 */
final class Continuaciones
{
    public static function disponible(): bool
    {
        return Db::tieneColumna('appointments', 'continua_de');
    }

    /** Id de la continuación (nueva o la que ya existía), o null si no se pudo. */
    public static function crear(PDO $pdo, int $appointmentId, int $studentId): ?int
    {
        if (!self::disponible()) {
            return null;
        }
        $stmt = $pdo->prepare('SELECT id FROM appointments WHERE continua_de = ? AND assigned_student_id = ?');
        $stmt->execute([$appointmentId, $studentId]);
        $ya = $stmt->fetchColumn();
        $stmt->closeCursor();
        if ($ya !== false) {
            return (int) $ya;
        }
        $stmt = $pdo->prepare('SELECT * FROM appointments WHERE id = ?');
        $stmt->execute([$appointmentId]);
        $orig = $stmt->fetch();
        $stmt->closeCursor();
        if ($orig === false || ($orig['practice_id'] ?? null) !== null || ($orig['practice_item_id'] ?? null) !== null) {
            return null;   // los intentos de práctica libre no se continúan: se repiten
        }
        $ahora = Clock::now();
        $pdo->prepare(
            'INSERT INTO appointments (fecha, hora, rut, nombre, apellido, fecha_nac, procedimiento, case_id,
                                       nota_admin, course_id, assigned_student_id, patient_id, continua_de)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
        )->execute([
            $ahora->format('d-m-y'), $ahora->format('H:i'),
            $orig['rut'], $orig['nombre'], $orig['apellido'], $orig['fecha_nac'], $orig['procedimiento'],
            $orig['case_id'], 'Continuación de la cita ' . $appointmentId,
            $orig['course_id'], $studentId, $orig['patient_id'], $appointmentId,
        ]);
        return (int) $pdo->lastInsertId();
    }

    /**
     * El alumno fue a buscar al paciente recién despedido y reabrió la
     * atención: la continuación que había pedido ese cierre se borra si
     * nadie la atendió (al volver a cerrar decide de nuevo).
     */
    public static function anularSinAtender(PDO $pdo, int $appointmentId, int $studentId): void
    {
        if (!self::disponible()) {
            return;
        }
        $pdo->prepare(
            'DELETE FROM appointments WHERE continua_de = ? AND assigned_student_id = ?
                AND NOT EXISTS (SELECT 1 FROM attendances att WHERE att.appointment_id = appointments.id)'
        )->execute([$appointmentId, $studentId]);
    }
}
