<?php

declare(strict_types=1);

/**
 * Choque de horario entre citas.
 *
 * Un mismo paciente se atiende varias veces el mismo día -- el mismo grupo a
 * horas distintas, o dos grupos distintos en paralelo. Lo que no puede pasar
 * es que a un alumno le caigan DOS citas a la misma hora: ahí no sabe a cuál
 * ir. Por eso el choque se evalúa por AUDIENCIA (a quién le toca la cita), no
 * por fecha/hora global como antes, que bloqueaba agendas legítimas de cursos
 * o grupos que no se pisan entre sí.
 *
 * Audiencia de una cita:
 *   - assigned_student_id -> ese alumno
 *   - assigned_group_id   -> los miembros de ese grupo
 *   - solo course_id      -> todos los matriculados del curso (citas legado
 *                            "todo el curso"; en citas nuevas, solo si el
 *                            curso no tiene grupos)
 *   - sin course_id       -> cola global legado. No se le puede calcular una
 *                            audiencia, así que solo choca con otras citas sin
 *                            curso: no tiene sentido que una fila vieja sin
 *                            dueño bloquee el horario de un curso entero.
 */
class Appointments
{
    /**
     * ¿Se pisan las audiencias de dos citas? Función pura -- los mapas
     * (group_members / course_students ya resueltos) los arma el llamador,
     * así se puede testear sin base de datos.
     *
     * @param array $a            ['course_id'=>?int,'assigned_group_id'=>?int,'assigned_student_id'=>?int]
     * @param array $b            idem
     * @param array $groupMembers [group_id => [user_id, ...]]
     * @param array $courseStudents [course_id => [user_id, ...]]
     */
    public static function audienciasSePisan(array $a, array $b, array $groupMembers, array $courseStudents): bool
    {
        $cursoA = self::intOrNull($a['course_id'] ?? null);
        $cursoB = self::intOrNull($b['course_id'] ?? null);

        // Cola global legado: solo choca con otra cola global legado.
        if ($cursoA === null || $cursoB === null) {
            return $cursoA === null && $cursoB === null;
        }
        if ($cursoA !== $cursoB) {
            return false; // cursos distintos = alumnos distintos
        }

        $alumnosA = self::audiencia($a, $groupMembers, $courseStudents);
        $alumnosB = self::audiencia($b, $groupMembers, $courseStudents);

        return array_intersect($alumnosA, $alumnosB) !== [];
    }

    /** Alumnos a los que les toca una cita. @return int[] */
    public static function audiencia(array $cita, array $groupMembers, array $courseStudents): array
    {
        $studentId = self::intOrNull($cita['assigned_student_id'] ?? null);
        if ($studentId !== null) {
            return [$studentId];
        }
        $groupId = self::intOrNull($cita['assigned_group_id'] ?? null);
        if ($groupId !== null) {
            return array_map('intval', $groupMembers[$groupId] ?? []);
        }
        $courseId = self::intOrNull($cita['course_id'] ?? null);
        if ($courseId !== null) {
            return array_map('intval', $courseStudents[$courseId] ?? []);
        }
        return [];
    }

    /**
     * Primera cita que choca con la que se está por guardar, o null.
     * $cita = ['fecha','hora','course_id','assigned_group_id','assigned_student_id'].
     */
    public static function buscarChoque(PDO $pdo, array $cita, int $excluirId = 0): ?array
    {
        $fecha = (string) ($cita['fecha'] ?? '');
        $hora = (string) ($cita['hora'] ?? '');
        if ($fecha === '' || $hora === '') {
            return null; // sin agendar todavía: no ocupa horario
        }

        $stmt = $pdo->prepare(
            'SELECT id, nombre, apellido, case_id, course_id, assigned_group_id, assigned_student_id
             FROM appointments WHERE fecha = ? AND hora = ? AND id != ?'
        );
        $stmt->execute([$fecha, $hora, $excluirId]);
        $candidatas = $stmt->fetchAll();
        if (!$candidatas) {
            return null;
        }

        $groupMembers = self::groupMembers($pdo);
        $courseStudents = self::courseStudents($pdo);
        foreach ($candidatas as $otra) {
            if (self::audienciasSePisan($cita, $otra, $groupMembers, $courseStudents)) {
                return $otra;
            }
        }
        return null;
    }

    /** Texto del error listo para mostrar, con a quién le choca. */
    public static function textoChoque(PDO $pdo, array $choque): string
    {
        $paciente = trim(($choque['nombre'] ?? '') . ' ' . ($choque['apellido'] ?? ''));
        $quien = self::nombreAudiencia($pdo, $choque);
        return 'Ese horario ya está ocupado' . ($quien !== '' ? ' para ' . $quien : '')
            . ($paciente !== '' ? ' (paciente ' . $paciente . ')' : '')
            . '. Otro horario, otro grupo u otro alumno sí se puede.';
    }

    private static function nombreAudiencia(PDO $pdo, array $cita): string
    {
        $studentId = self::intOrNull($cita['assigned_student_id'] ?? null);
        if ($studentId !== null) {
            $stmt = $pdo->prepare('SELECT display_name FROM users WHERE id = ?');
            $stmt->execute([$studentId]);
            $nombre = $stmt->fetchColumn();
            return $nombre !== false ? 'el alumno ' . (string) $nombre : 'ese alumno';
        }
        $groupId = self::intOrNull($cita['assigned_group_id'] ?? null);
        if ($groupId !== null) {
            $stmt = $pdo->prepare('SELECT name FROM student_groups WHERE id = ?');
            $stmt->execute([$groupId]);
            $nombre = $stmt->fetchColumn();
            return $nombre !== false ? 'el grupo ' . (string) $nombre : 'ese grupo';
        }
        $courseId = self::intOrNull($cita['course_id'] ?? null);
        if ($courseId !== null) {
            $stmt = $pdo->prepare('SELECT name FROM courses WHERE id = ?');
            $stmt->execute([$courseId]);
            $nombre = $stmt->fetchColumn();
            return $nombre !== false ? 'todo el curso ' . (string) $nombre : 'ese curso';
        }
        return '';
    }

    /** @return array [group_id => [user_id, ...]] */
    private static function groupMembers(PDO $pdo): array
    {
        $map = [];
        foreach ($pdo->query('SELECT group_id, user_id FROM group_members') as $row) {
            $map[(int) $row['group_id']][] = (int) $row['user_id'];
        }
        return $map;
    }

    /** @return array [course_id => [user_id, ...]] */
    private static function courseStudents(PDO $pdo): array
    {
        $map = [];
        foreach ($pdo->query('SELECT course_id, user_id FROM course_students') as $row) {
            $map[(int) $row['course_id']][] = (int) $row['user_id'];
        }
        return $map;
    }

    private static function intOrNull($valor): ?int
    {
        return ($valor === null || $valor === '' || (int) $valor === 0) ? null : (int) $valor;
    }
}
