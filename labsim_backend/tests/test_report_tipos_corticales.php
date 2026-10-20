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

$nuevos = ['PEALM', 'CAEP', 'P300', 'MMN'];
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
t_true(strpos($leer('src/Db.php'), "strpos(\$sql, \"'MMN'\")") !== false,
       'La migración detecta un CHECK sin los tipos corticales');
t_true(strpos($leer('public/api/my_patient_reports.php'), "'MMN'") !== false,
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
foreach (['CAEP', 'MMN'] as $t) {
    t_true(strpos(ReportPdfBuilder::build(999, $t, ['curvas' => []], $paciente, 'A', '11-09-2026'), '%PDF-1.4') === 0,
           "{$t} vacío igual genera PDF");
}
