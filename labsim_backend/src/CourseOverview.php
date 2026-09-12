<?php

require_once __DIR__ . '/HistoriaClinica.php';

/**
 * Lo que la pestaña Resumen de un curso necesita saber: si el curso está
 * listo para que entre un alumno, qué viene en la agenda y quién todavía no
 * hizo nada.
 *
 * Es lo que faltaba en la página vieja: mostraba con qué se configura el
 * curso, nunca en qué estado está. Un curso al que le falta habilitar
 * módulos, o que no tiene ninguna cita agendada, se veía exactamente igual
 * que uno andando -- el docente se enteraba cuando el alumno abría la app y
 * no tenía nada.
 *
 * Solo lee. Lo que escribe vive en CourseAdmin.
 */
final class CourseOverview
{
    /**
     * true si la cita cae dentro de los próximos $dias días (hoy incluido).
     * Las citas guardan la fecha como texto "dd-MM-yy" (así la compara el
     * cliente, ver el comentario de appointments.fecha en schema.sql), así
     * que la ventana se resuelve en PHP y no en SQL. Fecha vacía = paciente
     * sin agendar todavía: no entra.
     */
    public static function dentroDeVentana(?string $fecha, DateTimeImmutable $hoy, int $dias): bool
    {
        $dt = HistoriaClinica::parseFechaAgenda($fecha);
        if ($dt === null) {
            return false;
        }
        $desde = $hoy->setTime(0, 0);
        return $dt >= $desde && $dt <= $desde->modify('+' . $dias . ' days');
    }

    /**
     * Citas del curso en los próximos $dias días, ordenadas por fecha y
     * hora, con el nombre de a quién están asignadas y cuántos alumnos ya
     * las atendieron.
     */
    public static function proximasCitas(int $courseId, int $dias = 7, ?DateTimeImmutable $hoy = null): array
    {
        $hoy = $hoy ?: new DateTimeImmutable('today');
        $stmt = Db::get()->prepare(
            "SELECT a.id, a.fecha, a.hora, a.nombre, a.apellido, a.procedimiento, a.case_id,
                    a.assigned_student_id, a.assigned_group_id,
                    u.display_name AS alumno, g.name AS grupo,
                    (SELECT COUNT(*) FROM attendances att WHERE att.appointment_id = a.id) AS atenciones
             FROM appointments a
             LEFT JOIN users u ON u.id = a.assigned_student_id
             LEFT JOIN student_groups g ON g.id = a.assigned_group_id
             WHERE a.course_id = ?"
        );
        $stmt->execute([$courseId]);

        $citas = [];
        foreach ($stmt->fetchAll() as $row) {
            if (!self::dentroDeVentana($row['fecha'], $hoy, $dias)) {
                continue;
            }
            $dt = HistoriaClinica::parseFechaAgenda($row['fecha']);
            $row['_orden'] = $dt->format('Y-m-d') . ' ' . str_pad((string) $row['hora'], 5, '0', STR_PAD_LEFT);
            $citas[] = $row;
        }
        usort($citas, static fn(array $a, array $b): int => strcmp($a['_orden'], $b['_orden']));
        return $citas;
    }

    /** Cuántas citas tiene el curso en total y cuántas de hoy en adelante. */
    public static function conteoCitas(int $courseId, ?DateTimeImmutable $hoy = null): array
    {
        $hoy = $hoy ?: new DateTimeImmutable('today');
        $stmt = Db::get()->prepare('SELECT fecha FROM appointments WHERE course_id = ?');
        $stmt->execute([$courseId]);
        $total = 0;
        $futuras = 0;
        foreach ($stmt->fetchAll() as $row) {
            $total++;
            $dt = HistoriaClinica::parseFechaAgenda($row['fecha']);
            if ($dt !== null && $dt >= $hoy->setTime(0, 0)) {
                $futuras++;
            }
        }
        return ['total' => $total, 'futuras' => $futuras];
    }

    /** Alumnos matriculados que nunca registraron una atención en el curso. */
    public static function alumnosSinActividad(int $courseId): array
    {
        $progreso = Courses::rosterProgress($courseId);
        $sin = [];
        foreach (Courses::students($courseId) as $s) {
            if ((int) $s['is_demo'] === 1) {
                continue;
            }
            $p = $progreso[(int) $s['id']] ?? null;
            if ($p === null || $p['ultima'] === null) {
                $sin[] = $s;
            }
        }
        return $sin;
    }

    /**
     * Checklist de "curso listo". Cada ítem: si está cumplido, qué dice, a
     * qué pestaña lleva y si es imprescindible u opcional -- un curso sin
     * grupos ni Moodle funciona perfectamente, uno sin módulos no.
     */
    public static function checklist(int $courseId): array
    {
        $alumnos = array_values(array_filter(
            Courses::students($courseId),
            static fn(array $s): bool => (int) $s['is_demo'] !== 1
        ));
        $docentes = Courses::teachers($courseId);
        $grupos = Courses::groupsForCourse($courseId);
        $modulos = Courses::enabledModules($courseId);
        $citas = self::conteoCitas($courseId);
        $vinculos = Lti::contextsForCourse($courseId);

        return [
            [
                'ok' => count($docentes) > 0,
                'label' => 'Docente a cargo',
                'detalle' => count($docentes) > 0
                    ? count($docentes) . ' docente(s)'
                    : 'Nadie puede ver este curso salvo el administrador.',
                'tab' => 'personas',
                'opcional' => false,
            ],
            [
                'ok' => count($alumnos) > 0,
                'label' => 'Alumnos matriculados',
                'detalle' => count($alumnos) > 0 ? count($alumnos) . ' alumno(s)' : 'Todavía no hay a quién atender.',
                'tab' => 'personas',
                'opcional' => false,
            ],
            [
                'ok' => count($modulos) > 0,
                'label' => 'Módulos habilitados',
                'detalle' => count($modulos) > 0
                    ? count($modulos) . ' módulo(s)'
                    : 'Sin módulos, el alumno entra a la app y no tiene ningún equipo.',
                'tab' => 'modulos',
                'opcional' => false,
            ],
            [
                'ok' => $citas['futuras'] > 0,
                'label' => 'Citas por delante',
                'detalle' => $citas['futuras'] > 0
                    ? $citas['futuras'] . ' de hoy en adelante (' . $citas['total'] . ' en total)'
                    : ($citas['total'] > 0 ? 'Las ' . $citas['total'] . ' citas del curso ya pasaron.' : 'La agenda del curso está vacía.'),
                'tab' => 'agenda',
                'opcional' => false,
            ],
            [
                'ok' => count($grupos) > 0,
                'label' => 'Grupos armados',
                'detalle' => count($grupos) > 0
                    ? count($grupos) . ' grupo(s)'
                    : 'Sin grupos hay que citar alumno por alumno.',
                'tab' => 'personas',
                'opcional' => true,
            ],
            [
                'ok' => count($vinculos) > 0,
                'label' => 'Curso de Moodle vinculado',
                'detalle' => count($vinculos) > 0
                    ? count($vinculos) . ' contexto(s) vinculado(s) -- los alumnos se matriculan solos'
                    : 'Sin vínculo hay que matricular a mano.',
                'tab' => 'vinculos',
                'opcional' => true,
            ],
        ];
    }
}
