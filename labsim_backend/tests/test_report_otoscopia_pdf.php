<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/ReportFile.php';
require_once __DIR__ . '/../src/ReportPdfBuilder.php';

/**
 * Informe de otoscopia por cuadrantes (el que sube el alumno desde el
 * módulo de otoscopia, tipo 'OTOSCOPIA'). Lo que se cuida acá es que
 * NINGÚN hallazgo marcado se pierda en el PDF: el docente evalúa contra
 * este documento, un cuadrante que no se dibuja es una respuesta del
 * alumno que desaparece.
 */

$paciente = ['nombre' => 'Ana', 'apellido' => 'Pérez', 'rut' => '11.111.111-1', 'fecha_nac' => '2000-01-01'];

$data = [
    'od' => [
        'cuadrantes' => [
            // Varios hallazgos en el mismo cuadrante: lo corriente (una
            // perforación con la placa alrededor), y lo que antes se
            // perdía porque el cliente guardaba solo el último marcado.
            'anterior_inferior' => ['tympanosclerosis', 'perforation'],
            'pars_flaccida' => ['retraction'],
        ],
        'cae' => ['cae_cerumen'],
        'observaciones' => 'Mucho cerumen, se ve solo parte de la membrana.',
    ],
    'oi' => [
        'cuadrantes' => [],
        'cae' => ['cae_normal'],
        'observaciones' => '',
    ],
];

$pdf = ReportPdfBuilder::build(999, 'OTOSCOPIA', $data, $paciente, 'Alumno X', '11-09-2026');

t_true(strpos($pdf, '%PDF-1.4') === 0, 'El informe de otoscopia sale como un PDF');
t_true(substr(trim($pdf), -5) === '%%EOF', 'El PDF de otoscopia cierra con %%EOF');
t_true(strpos($pdf, 'Informe Otoscopia') !== false, 'El PDF se titula como informe de otoscopia');

foreach ([
    'Anteroinferior: Timpanoesclerosis, Perforaci',
    'Pars fl',
    'CAE: Cerumen',
    'Mucho cerumen',
    'sin hallazgos marcados',
    'CAE: Normal',
] as $texto) {
    t_true(strpos($pdf, $texto) !== false, "El informe de otoscopia incluye '{$texto}'");
}

// Un oído sin nada marcado no puede quedar mudo: el docente tiene que
// poder distinguir "no vio nada" de "no informó".
$vacio = ReportPdfBuilder::build(999, 'OTOSCOPIA', ['od' => [], 'oi' => []], $paciente, 'Alumno X', '11-09-2026');
t_true(strpos($vacio, '%PDF-1.4') === 0, 'Un informe de otoscopia vacío igual genera PDF');
t_true(substr_count($vacio, 'sin hallazgos marcados') === 2, 'Los dos oídos sin marcas lo dicen');
t_true(substr_count($vacio, 'CAE: sin evaluar') === 2, 'Un CAE sin tildar dice "sin evaluar", no "normal"');

// Informes de la primera versión: un solo hallazgo por cuadrante, en un
// string y no en una lista. Si el PDF solo entendiera listas, un informe
// ya subido se imprimiría sin hallazgos (el docente evaluaría en blanco).
$legado = ReportPdfBuilder::build(999, 'OTOSCOPIA', [
    'od' => ['cuadrantes' => ['posterior_superior' => 'effusion'], 'cae' => [], 'observaciones' => ''],
    'oi' => [],
], $paciente, 'Alumno X', '11-09-2026');
t_true(strpos($legado, 'Posterosuperior: Efusi') !== false,
    'Un informe viejo (hallazgo en string) sigue imprimiendo su hallazgo');
