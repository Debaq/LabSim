<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/ReportFile.php';
require_once __DIR__ . '/../src/ReportPdfBuilder.php';

/**
 * Los cuatro potenciales corticales del módulo ABR (PEALM, CAEP, P300,
 * MMN) tienen que figurar en TODOS los lugares donde figura
 * ELECTROCOCLEO: si falta uno, el informe se rechaza (endpoint o CHECK de
 * la tabla) o sale sin rótulo.
 */

$nuevos = ['PEALM', 'CAEP', 'P300', 'MMN', 'ASSR'];
$leer = function (string $ruta): string {
    return (string) file_get_contents(__DIR__ . '/../' . $ruta);
};

// REPORT_TIPOS está inline en el endpoint (hace requireUser al incluirlo).
$upload = $leer('public/api/report_upload.php');
t_true(preg_match('/const REPORT_TIPOS = \[([^\]]*)\]/', $upload, $m) === 1, 'report_upload define REPORT_TIPOS');
foreach ($nuevos as $t) {
    t_true(strpos($m[1], "'{$t}'") !== false, "REPORT_TIPOS acepta {$t}");
    t_true(isset(ReportFile::LABELS[$t]), "ReportFile::LABELS rotula {$t}");
    t_true(isset(ReportFile::SHORT_LABELS[$t]), "ReportFile::SHORT_LABELS rotula {$t}");
}
t_eq(ReportFile::LABELS['PEALM'], 'Potencial de latencia media (PEALM)', 'Rótulo del PEALM');
t_eq(ReportFile::LABELS['MMN'], 'Negatividad de disparidad (MMN)', 'Rótulo de la MMN');

foreach (['sql/schema.sql', 'src/Db.php'] as $archivo) {
    $txt = $leer($archivo);
    t_true(preg_match("/CHECK \(tipo IN \(([^)]*)\)\)/", $txt, $c) === 1, "{$archivo} trae el CHECK de reports.tipo");
    foreach ($nuevos as $t) {
        t_true(strpos($c[1], "'{$t}'") !== false, "El CHECK de {$archivo} acepta {$t}");
    }
}
// La migración mira el ÚLTIMO tipo agregado (hoy los nasales, ver
// test_report_tipos_nasales.php): un CHECK que lo trae trae los corticales.
t_true(strpos($leer('src/Db.php'), "strpos(\$sql, \"'RINOMETRIA'\")") !== false,
       'La migración detecta un CHECK sin los tipos corticales');
t_true(strpos($leer('public/api/my_patient_reports.php'), "'ASSR'") !== false,
       'my_patient_reports lista los tipos corticales');

// PDF mínimo del PEALM.
$paciente = ['nombre' => 'Ana', 'apellido' => 'Pérez', 'rut' => '11.111.111-1', 'fecha_nac' => '2000-01-01'];
$data = [
    'curvas' => [
        'R1.C3' => ['canal' => 'C3', 'Cortical' => ['lat' => ['Na' => 18.5, 'Pa' => 31.0], 'amp' => ['Na-Pa' => 0.8]]],
        'R1.C4' => ['canal' => 'C4', 'Cortical' => ['lat' => ['Na' => 19.0, 'Pa' => 32.5], 'amp' => ['Na-Pa' => 0.6]]],
        'L1.C3' => ['canal' => 'C3', 'Cortical' => ['lat' => ['Pa' => 150.0], 'amp' => []]],
    ],
    'efectos' => ['electrodo' => 0.25, 'hemisferio' => 'derecho', 'oido' => null, 'oido_menor' => null],
];
$pdf = ReportPdfBuilder::build(999, 'PEALM', $data, $paciente, 'Alumno X', '11-09-2026');
t_true(strpos($pdf, '%PDF-1.4') === 0, 'El informe PEALM sale como PDF');
t_true(substr(trim($pdf), -5) === '%%EOF', 'El PDF del PEALM cierra con %%EOF');
t_true(strpos($pdf, '25% menor en hemisferio derecho') !== false, 'El PDF dice el efecto electrodo');
t_true(strpos($pdf, 'Efecto oído') === false, 'El efecto null se omite');

$p300 = ReportPdfBuilder::build(999, 'P300', [
    'curvas' => [], 'conteo' => ['OD' => ['dice' => 18, 'reales' => 20]],
], $paciente, 'Alumno X', '11-09-2026');
t_true(strpos($p300, 'dice 18 de 20 raros presentados') !== false, 'El conteo de la P300 va al PDF');
$boton = ReportPdfBuilder::build(999, 'P300', [
    'curvas' => [
        'R1.Pz' => ['canal' => 'Pz', 'tarea' => 'boton', 'Cortical' => ['lat' => ['P3' => 330.0], 'amp' => ['P3' => 9.5]]],
        'L1.Pz' => ['canal' => 'Pz', 'tarea' => 'contar', 'Cortical' => ['lat' => ['P3' => 335.0], 'amp' => []]],
    ],
    'conteo' => ['OD' => ['tarea' => 'boton', 'aciertos' => 47, 'falsas' => 2, 'reales' => 50]],
], $paciente, 'Alumno X', '11-09-2026');
t_true(strpos($boton, '47 aciertos de 50 raros, 2 falsas alarmas') !== false, 'El botón de la P300 va al PDF');
t_true(strpos($boton, 'Apretar bot') !== false && strpos($boton, 'Contar los raros') !== false,
       'Cada oído dice la tarea con que se registró');
$mmn = ReportPdfBuilder::build(999, 'MMN', ['curvas' => [
    'R1.Fz' => ['canal' => 'Fz', 'tarea' => 'pasiva', 'Cortical' => ['lat' => ['MMN' => 180.0], 'amp' => []]],
]], $paciente, 'Alumno X', '11-09-2026');
t_true(strpos($mmn, 'video sin sonido') !== false, 'La MMN dice la tarea pasiva');
foreach (['CAEP', 'MMN'] as $t) {
    t_true(strpos(ReportPdfBuilder::build(999, $t, ['curvas' => []], $paciente, 'A', '11-09-2026'), '%PDF-1.4') === 0,
           "{$t} vacío igual genera PDF");
}

// ASSR: las cuatro vistas son imágenes del informe y el endpoint las acepta.
foreach (['assr_rastro', 'assr_fft', 'assr_polar', 'assr_audio'] as $suf) {
    t_true(strpos($upload, "'{$suf}'") !== false, "report_upload acepta la imagen {$suf}");
}
$assr = ReportPdfBuilder::build(999, 'ASSR', [
    'assr' => [
        'n' => 600, 'rechazadas' => 22,
        'correccion' => ['500' => 15.0, '1000' => 12.0, '2000' => 10.0, '4000' => 10.0],
        'canales' => [
            'OD:500' => ['nivel' => 30, 'umbral_hl' => 30, 'umbral_ehl' => 15,
                         'stats' => ['n' => 300, 'amp_nv' => 58.2, 'noise_nv' => 14.1, 'f_ratio' => 17.3, 'p' => 0.0002, 'estado' => 'respuesta']],
            'OD:4000' => ['nivel' => 90, 'umbral_hl' => null, 'umbral_ehl' => null,
                          'stats' => ['n' => 500, 'amp_nv' => 9.0, 'noise_nv' => 11.0, 'f_ratio' => 0.7, 'p' => 0.52, 'estado' => 'sin respuesta']],
        ],
    ],
    'hallazgos' => 'ASSR conservado en graves.', 'conclusion' => 'Descenso en agudos OD.',
], $paciente, 'Alumno X', '11-09-2026');
t_true(strpos($assr, '%PDF-1.4') === 0 && substr(trim($assr), -5) === '%%EOF', 'El informe ASSR sale como PDF');
t_true(strpos($assr, 'Potenciales de estado estable') !== false, 'El PDF del ASSR lleva su título');
t_true(strpos($assr, '600 ') !== false && strpos($assr, 'rechazadas por artefacto') !== false, 'El PDF del ASSR dice cuántas épocas');
t_true(strpos($assr, 'Portadoras OD') !== false, 'El PDF del ASSR trae la tabla del oído derecho');
t_true(strpos($assr, 'Portadoras OI') === false, 'Sin canales del OI no hay tabla del OI');
t_true(strpos($assr, 'sin resp.') !== false, 'La portadora sin respuesta se informa como tal');
t_true(strpos($assr, 'eHL aplicada: 500 Hz 15 dB') !== false, 'El PDF dice la corrección a eHL');
t_true(strpos(ReportPdfBuilder::build(999, 'ASSR', [], $paciente, 'A', '11-09-2026'), '%PDF-1.4') === 0,
       'ASSR vacío igual genera PDF');
