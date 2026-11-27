<?php

declare(strict_types=1);

/**
 * Estadísticas del curso (CursoEstadisticas): cifras desde el 'resumen' de
 * cada atención, agrupación por mes y paciente, a quién mirar y qué
 * recomendaciones salen según los cortes.
 */

require_once dirname(__DIR__) . '/src/CursoEstadisticas.php';
require_once dirname(__DIR__) . '/src/CourseAvance.php';

/** Una atención evaluada, con lo mínimo que usa CursoEstadisticas. */
function ce_tec(string $fecha, string $paciente, int $pct, array $resumen = [], array $secciones = []): array
{
    $t = [
        'puntaje' => ['pct' => $pct, 'cumple' => 0, 'total' => 0],
        '_cita' => ['fecha' => $fecha, 'paciente' => $paciente, 'case_id' => $paciente === 'Eva' ? '31' : '32'],
        'orden' => ['puntaje' => ['pct' => $secciones['orden'] ?? 100], 'observaciones' => ['Volvió a umbrales aéreos después de pruebas supraliminares.']],
        'resumen' => $resumen + [
            'frecuencias' => 10, 'verificadas' => 9, 'medibles' => 10, 'a_5db' => 10,
            'estimulos' => 50, 'bajo_1s' => 5, 'duracion_mediana' => 1.4,
            'oseos_pedidos' => true, 'oseos_hechos' => true, 'logo' => true, 'adaptacion' => null, 'stenger' => null,
            'enmascaramiento_aerea' => null, 'enmascaramiento_osea' => null, 'supra' => ['LDL'],
        ],
    ];
    foreach ($secciones as $k => $v) {
        if ($k !== 'orden') {
            $t[$k] = ['puntaje' => ['pct' => $v]];
        }
    }
    return $t;
}

// Curso que lo hace bien: ninguna recomendación salvo nada
$bien = [
    1 => ['nombre' => 'Ana', 'tecnicas' => [ce_tec('2026-10-01', 'Eva', 90), ce_tec('2026-11-01', 'Raquel', 92)]],
    2 => ['nombre' => 'Beto', 'tecnicas' => [ce_tec('2026-10-01', 'Eva', 88), ce_tec('2026-11-01', 'Raquel', 90)]],
];
$e = CursoEstadisticas::calcular($bien);
t_eq($e['n'], 4, 'Estadísticas: cuenta las atenciones');
t_eq($e['kpis']['verificacion'], 90, 'Estadísticas: verificación = verificadas / frecuencias');
t_eq($e['kpis']['a_5db'], 100, 'Estadísticas: puntería');
t_eq($e['kpis']['oseos'], [4, 4], 'Estadísticas: óseos hechos / pedidos');
t_eq($e['kpis']['logo'], [4, 4], 'Estadísticas: logo');
t_eq(array_keys($e['meses']), ['2026-10', '2026-11'], 'Estadísticas: por mes, en orden');
t_eq($e['meses']['2026-10']['logro'], 89, 'Estadísticas: logro medio del mes');
t_eq(array_keys($e['pacientes']), ['31|Eva', '32|Raquel'], 'Estadísticas: por paciente');
t_eq(array_column($e['recomendaciones'], 'titulo'), [], 'Recomendaciones: un curso que cumple no recibe ninguna');

// Curso que no verifica, no toma óseos ni sostiene el tono
$mal = [
    1 => ['nombre' => 'Ana', 'tecnicas' => [
        ce_tec('2026-10-01', 'Eva', 40, ['verificadas' => 1, 'oseos_hechos' => false, 'duracion_mediana' => 0.25, 'bajo_1s' => 48]),
        ce_tec('2026-11-01', 'Raquel', 30, ['verificadas' => 2, 'oseos_hechos' => false, 'duracion_mediana' => 0.2, 'bajo_1s' => 49]),
        ce_tec('2026-11-08', 'Raquel', 20, ['verificadas' => 2, 'oseos_hechos' => false, 'duracion_mediana' => 0.2, 'bajo_1s' => 49]),
    ]],
    2 => ['nombre' => 'Beto', 'tecnicas' => [
        ce_tec('2026-10-01', 'Eva', 80, ['adaptacion' => false, 'enmascaramiento_aerea' => 0.0]),
        ce_tec('2026-11-01', 'Raquel', 82, ['adaptacion' => false, 'enmascaramiento_aerea' => 0.0]),
        ce_tec('2026-11-08', 'Raquel', 84, ['adaptacion' => false, 'enmascaramiento_aerea' => 0.0]),
    ]],
];
$e = CursoEstadisticas::calcular($mal);
$titulos = array_column($e['recomendaciones'], 'titulo');
t_true(in_array('Verificar el umbral con 2 de 3', $titulos, true), 'Recomendaciones: verificación bajo el corte');
t_true(in_array('Tomar los umbrales óseos', $titulos, true), 'Recomendaciones: óseos que faltan');
t_true(in_array('Buscar adaptación en la sensorioneural asimétrica', $titulos, true), 'Recomendaciones: adaptación');
t_true(in_array('Enmascarar donde el tono cruza', $titulos, true), 'Recomendaciones: enmascaramiento');
$rec = array_values(array_filter($e['recomendaciones'], static function ($r) { return $r['titulo'] === 'Verificar el umbral con 2 de 3'; }))[0];
t_eq($rec['alumnos'], ['Ana'], 'Recomendaciones: nombra a quien verifica menos del 30 %');
t_true(strpos($rec['evidencia'], '%') !== false, 'Recomendaciones: con la cifra que la respalda');
t_eq($e['alumnos'][1]['oseos'], [0, 3], 'Por alumno: óseos 0 de 3');
t_eq(array_keys($e['alumnos']), [2, 1], 'Por alumno: del logro más alto al más bajo');
t_eq($e['alumnos'][1]['tendencia'], -20, 'Por alumno: tendencia');
t_true(isset($e['mirar'][1]) && in_array('tomó óseos en 0 de 3 atenciones que los pedían', $e['mirar'][1]['motivos'], true), 'Para mirar: óseos');
t_true(isset($e['mirar'][2]) && in_array('no enmascaró nunca donde el tono cruzaba', $e['mirar'][2]['motivos'], true), 'Para mirar: nunca enmascara');
t_eq(CursoEstadisticas::fechaCorta('2026-09-04'), '4-09', 'Fecha corta');
t_eq(CourseAvance::fechaCita('25-09-26'), '2026-09-25', 'Fecha de la agenda a Y-m-d');
t_eq(CourseAvance::fechaCita(''), null, 'Cita sin fecha');
