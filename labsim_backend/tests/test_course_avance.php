<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CourseAvance.php';

/** Avance del curso: metas de los objetivos, conteos y quién necesita atención. */

t_eq(CourseAvance::cumple('tecnica_promedio', 85, 85.0), true, 'Mínimo: igual a la meta cumple');
t_eq(CourseAvance::cumple('tecnica_promedio', 84, 85.0), false, 'Mínimo: debajo no cumple');
t_eq(CourseAvance::cumple('duracion', 20, 25.0), true, 'Máximo: debajo cumple');
t_eq(CourseAvance::cumple('duracion', 30, 25.0), false, 'Máximo: arriba no cumple');
t_eq(CourseAvance::cumple('tecnica_promedio', null, 85.0), null, 'Sin datos no cuenta ni a favor ni en contra');
t_eq(CourseAvance::cumple('', 3, 1.0), null, 'Sin indicador no se mide');
t_eq(CourseAvance::cumple('no_existe', 3, 1.0), null, 'Indicador desconocido no se mide');

t_eq(CourseAvance::metaTexto('tecnica_promedio', 85.0), '≥ 85 %', 'Meta mínima con unidad');
t_eq(CourseAvance::metaTexto('duracion', 22.5), '≤ 22,5 min', 'Meta máxima con decimal');
t_eq(CourseAvance::metaTexto('informes_ABR', 2.0), '≥ 2', 'Meta sin unidad');
t_true(isset(CourseAvance::indicadores()['informes_ABR']), 'Un indicador de informes por examen');

t_eq(CourseAvance::validarMedicion('', 'x'), ['', null, null], 'Sin indicador la meta se ignora');
t_eq(CourseAvance::validarMedicion('atenciones', '3'), ['atenciones', 3.0, null], 'Meta entera');
t_eq(CourseAvance::validarMedicion('duracion', '12,5'), ['duracion', 12.5, null], 'Meta con coma decimal');
t_true(CourseAvance::validarMedicion('atenciones', '')[2] !== null, 'Con indicador la meta es obligatoria');
t_true(CourseAvance::validarMedicion('atenciones', '-1')[2] !== null, 'Meta negativa no');
t_true(CourseAvance::validarMedicion('inventado', '1')[2] !== null, 'Indicador inexistente no');

$al = static function (array $v): array {
    return $v + ['nombre' => 'X', 'atenciones' => 0, 'ultima' => null, 'tecnica_promedio' => null, 'tendencia' => null, 'tecnicas' => []];
};
$alumnos = [
    1 => $al(['nombre' => 'Ana', 'atenciones' => 5, 'ultima' => '2026-10-08', 'tecnica_promedio' => 90]),
    2 => $al(['nombre' => 'Beto', 'atenciones' => 3, 'ultima' => '2026-09-01', 'tecnica_promedio' => 50, 'tendencia' => -15]),
    3 => $al(['nombre' => 'Cata']),
];
$obj = CourseAvance::resumenObjetivos([
    ['indicador' => 'tecnica_promedio', 'meta' => 85.0, 'texto' => 't'],
    ['indicador' => '', 'meta' => null, 'texto' => 'libre'],
], $alumnos);
t_eq([$obj[0]['cumplen'], $obj[0]['no_cumplen'], $obj[0]['sin_datos']], [1, 1, 1], 'Cumplen, no cumplen y sin datos');
t_eq([$obj[1]['cumplen'], $obj[1]['no_cumplen'], $obj[1]['sin_datos']], [0, 0, 0], 'Sin indicador no cuenta a nadie');

$nec = CourseAvance::necesitanAtencion($alumnos, '2026-10-09');
t_eq(array_keys($nec), [2, 3], 'Ana va bien; Beto y Cata necesitan atención');
t_eq(count($nec[2]['motivos']), 3, 'Beto: sin actividad reciente, técnica baja y bajando');
t_eq($nec[3]['motivos'], ['sin atenciones cerradas'], 'Cata: sin atenciones');

$r = static fn(string $t, bool $c): array => ['texto' => $t, 'cumple' => $c];
$tec = static fn(bool $mejor): array => ['aereos' => ['reglas' => [$r('Se parte por el oído mejor.', $mejor)]]];
$curso = [
    1 => $al(['tecnicas' => [$tec(false), $tec(false), $tec(true)]]),   // falla en la mayoría
    2 => $al(['tecnicas' => [$tec(false), $tec(true), $tec(true)]]),    // falló una vez: no cuenta
    3 => $al([]),                                                         // sin audiometrías
];
$pasos = CourseAvance::pasosDelCurso($curso);
t_eq([$pasos[0]['alumnos'], $pasos[0]['evaluados']], [1, 2], 'Cuenta alumnos que fallan en la mayoría, sobre los evaluados');
