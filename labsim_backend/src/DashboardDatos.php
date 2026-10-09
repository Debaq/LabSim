<?php

declare(strict_types=1);

require_once __DIR__ . '/Courses.php';
require_once __DIR__ . '/Metrics.php';

/**
 * Lo que lee admin/dashboard.php. La vista general sale de las atenciones
 * (decenas de filas), no de action_logs: antes cargaba el registro entero
 * (más de 100 mil filas) en cada visita, y el dashboard es la página donde
 * aterriza el docente al entrar desde Moodle.
 */
final class DashboardDatos
{
    /**
     * Alumnos que puede ver: null = todos (admin completo sin foco de curso);
     * lista (puede venir vacía) = solo esos. Docente: el roster de sus cursos;
     * con un curso elegido en el header, además solo el de ese curso.
     */
    public static function alumnosVisibles(array $me, ?int $contextCourseId): ?array
    {
        $isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
        $permitidos = $isFullAdmin ? null : Courses::rosterUserIds(Courses::teacherCourseIds((int) $me['id']));
        if ($contextCourseId !== null) {
            $delCurso = Courses::rosterUserIds([$contextCourseId]);
            $permitidos = $permitidos === null ? $delCurso : array_values(array_intersect($permitidos, $delCurso));
        }
        return $permitidos;
    }

    /**
     * Atenciones de alumnos reales (sin docentes ni el estudiante demo), la
     * más reciente primero, con la cita, el alumno y el curso.
     */
    public static function atenciones(?array $permitidos, bool $conPractica = false, ?int $appointmentId = null): array
    {
        if ($permitidos === []) {
            return [];
        }
        $where = ["u.role = 'student'", 'u.is_demo = 0'];
        $args = [];
        if (!$conPractica) {
            $where[] = Practica::sinPractica('a');
        }
        if ($permitidos !== null) {
            $where[] = 'att.student_id IN (' . implode(',', array_fill(0, count($permitidos), '?')) . ')';
            $args = array_merge($args, array_map('intval', $permitidos));
        }
        if ($appointmentId !== null) {
            $where[] = 'a.id = ?';
            $args[] = $appointmentId;
        }
        $stmt = Db::get()->prepare(
            'SELECT att.id AS attendance_id, att.student_id, att.estado, att.hora_real, att.updated_at, att.nota,
                    a.id AS appointment_id, a.fecha, a.hora, a.nombre, a.apellido, a.procedimiento, a.case_id, a.course_id,
                    ' . (Practica::listo() ? 'a.practice_id' : 'NULL AS practice_id') . ',
                    u.display_name, c.name AS course_name
               FROM attendances att
               JOIN appointments a ON a.id = att.appointment_id
               JOIN users u ON u.id = att.student_id
               LEFT JOIN courses c ON c.id = a.course_id
              WHERE ' . implode(' AND ', $where) . '
              ORDER BY att.updated_at DESC'
        );
        $stmt->execute($args);
        return $stmt->fetchAll();
    }

    /** Preguntas del alumno al paciente: [appointment_id][student_id] => n. */
    public static function preguntas(array $appointmentIds): array
    {
        $ids = array_values(array_unique(array_map('intval', $appointmentIds)));
        if (!$ids) {
            return [];
        }
        $stmt = Db::get()->prepare(
            "SELECT appointment_id, student_id, COUNT(*) AS n FROM llm_chat_logs
              WHERE role = 'user' AND appointment_id IN (" . implode(',', array_fill(0, count($ids), '?')) . ')
              GROUP BY appointment_id, student_id'
        );
        $stmt->execute($ids);
        $out = [];
        foreach ($stmt->fetchAll() as $r) {
            $out[(int) $r['appointment_id']][(int) $r['student_id']] = (int) $r['n'];
        }
        return $out;
    }

    /** Informes por atención: [attendance_id] => [['id', 'tipo', 'updated_at'], ...]. */
    public static function informes(array $attendanceIds): array
    {
        $ids = array_values(array_unique(array_map('intval', $attendanceIds)));
        if (!$ids) {
            return [];
        }
        $stmt = Db::get()->prepare(
            'SELECT id, attendance_id, tipo, updated_at FROM reports
              WHERE attendance_id IN (' . implode(',', array_fill(0, count($ids), '?')) . ') ORDER BY tipo'
        );
        $stmt->execute($ids);
        $out = [];
        foreach ($stmt->fetchAll() as $r) {
            $out[(int) $r['attendance_id']][] = $r;
        }
        return $out;
    }

    /**
     * Las acciones registradas de UNA cita, por alumno, decodificadas. El
     * número de cita va dentro del JSON (no hay columna), así que el LIKE
     * descarta en la base lo que no es de esta cita y acá solo se confirma.
     *
     * @return array<int,array<int,array>> [student_id] => filas de Metrics::decodeLog
     */
    public static function logsDeCita(int $appointmentId, array $studentIds): array
    {
        $ids = array_values(array_unique(array_map('intval', $studentIds)));
        if (!$ids) {
            return [];
        }
        $stmt = Db::get()->prepare(
            'SELECT id, user_id, client_ts, action, payload FROM action_logs
              WHERE user_id IN (' . implode(',', array_fill(0, count($ids), '?')) . ')
                AND (payload LIKE ? OR payload LIKE ? OR payload LIKE ?)
              ORDER BY id'
        );
        $stmt->execute(array_merge($ids, [
            '%"appointment_id":"' . $appointmentId . '"%',
            '%"appointment_id":' . $appointmentId . ',%',
            '%"appointment_id":' . $appointmentId . '}%',
        ]));
        $out = [];
        while (($r = $stmt->fetch()) !== false) {
            $l = Metrics::decodeLog($r);
            if ((int) ($l['appointment_id'] ?? 0) === $appointmentId) {
                $out[(int) $l['user_id']][] = $l;
            }
        }
        return $out;
    }
}
