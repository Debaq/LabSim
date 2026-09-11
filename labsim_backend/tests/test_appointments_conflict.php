<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Appointments.php';

/**
 * Choque de horario por audiencia (Appointments::audienciasSePisan). Solo la
 * parte pura -- buscarChoque() necesita base y acá no hay pdo_sqlite.
 */

$grupos = [
    10 => [1, 2, 3],   // grupo A del curso 1
    11 => [4, 5],      // grupo B del curso 1
    20 => [6, 7],      // grupo del curso 2
];
$cursos = [
    1 => [1, 2, 3, 4, 5],
    2 => [6, 7],
];

$grupoA = ['course_id' => 1, 'assigned_group_id' => 10, 'assigned_student_id' => null];
$grupoB = ['course_id' => 1, 'assigned_group_id' => 11, 'assigned_student_id' => null];
$otroCurso = ['course_id' => 2, 'assigned_group_id' => 20, 'assigned_student_id' => null];
$alumno1 = ['course_id' => 1, 'assigned_group_id' => null, 'assigned_student_id' => 1];
$alumno4 = ['course_id' => 1, 'assigned_group_id' => null, 'assigned_student_id' => 4];
$todoElCurso = ['course_id' => 1, 'assigned_group_id' => null, 'assigned_student_id' => null];
$legado = ['course_id' => null, 'assigned_group_id' => null, 'assigned_student_id' => null];

t_true(
    Appointments::audienciasSePisan($grupoA, $grupoA, $grupos, $cursos),
    'el mismo grupo a la misma hora choca'
);
t_true(
    !Appointments::audienciasSePisan($grupoA, $grupoB, $grupos, $cursos),
    'dos grupos distintos del mismo curso pueden atender a la misma hora'
);
t_true(
    !Appointments::audienciasSePisan($grupoA, $otroCurso, $grupos, $cursos),
    'cursos distintos no se pisan'
);
t_true(
    Appointments::audienciasSePisan($alumno1, $grupoA, $grupos, $cursos),
    'un alumno choca con una cita de su propio grupo'
);
t_true(
    !Appointments::audienciasSePisan($alumno4, $grupoA, $grupos, $cursos),
    'un alumno de otro grupo no choca'
);
t_true(
    Appointments::audienciasSePisan($todoElCurso, $grupoB, $grupos, $cursos),
    'una cita legado "todo el curso" choca con cualquier grupo de ese curso'
);
t_true(
    !Appointments::audienciasSePisan($legado, $grupoA, $grupos, $cursos),
    'una fila legado sin curso no bloquea el horario de un curso'
);
t_true(
    Appointments::audienciasSePisan($legado, $legado, $grupos, $cursos),
    'dos filas legado sin curso sí chocan entre sí'
);
t_eq(
    Appointments::audiencia($grupoA, $grupos, $cursos),
    [1, 2, 3],
    'la audiencia de una cita de grupo son sus miembros'
);
