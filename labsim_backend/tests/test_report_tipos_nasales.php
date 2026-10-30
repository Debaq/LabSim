<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/ReportFile.php';
require_once __DIR__ . '/../src/ReportPdfBuilder.php';

/**
 * Los informes de los equipos nasales (rinomanometría y rinometría, demo
 * interna: docs/roadmap_nasal.md) tienen que figurar en todos los lugares
 * donde figura el ASSR: si falta uno, el informe se rechaza (endpoint o
 * CHECK de la tabla) o sale sin rótulo. Y la migración tiene que detectar
 * un CHECK viejo, sin ellos.
 */

$nasales = ['RINOMANOMETRIA', 'RINOMETRIA', 'RINOSCOPIA', 'ESPIROMETRIA', 'OLFATOMETRIA', 'PRICK', 'POLISOMNOGRAFIA', 'CPAP'];
$leer = function (string $ruta): string {
    return (string) file_get_contents(__DIR__ . '/../' . $ruta);
};

$upload = $leer('public/api/report_upload.php');
t_true(preg_match('/const REPORT_TIPOS = \[([^\]]*)\]/', $upload, $m) === 1, 'report_upload define REPORT_TIPOS');
foreach ($nasales as $t) {
    t_true(strpos($m[1], "'{$t}'") !== false, "REPORT_TIPOS acepta {$t}");
    t_true(isset(ReportFile::LABELS[$t]), "ReportFile::LABELS rotula {$t}");
    t_true(isset(ReportFile::SHORT_LABELS[$t]), "ReportFile::SHORT_LABELS rotula {$t}");
}
foreach (['rm_curva', 'rm_resistencia', 'ra_curva', 'esp_fv', 'esp_vt'] as $suf) {
    t_true(strpos($upload, "'{$suf}'") !== false, "report_upload acepta la imagen {$suf}");
}
foreach (['sql/schema.sql', 'src/Db.php'] as $archivo) {
    $txt = $leer($archivo);
    t_true(preg_match("/CHECK \(tipo IN \(([^)]*)\)\)/", $txt, $c) === 1, "{$archivo} trae el CHECK de reports.tipo");
    foreach ($nasales as $t) {
        t_true(strpos($c[1], "'{$t}'") !== false, "El CHECK de {$archivo} acepta {$t}");
    }
}
t_true(strpos($leer('src/Db.php'), "strpos(\$sql, \"'CPAP'\")") !== false,
       'La migración detecta un CHECK sin los tipos nasales');

$paciente = ['nombre' => 'Ana', 'apellido' => 'Pérez', 'rut' => '11.111.111-1', 'fecha_nac' => '1986-01-01'];
$rm = ReportPdfBuilder::build(999, 'RINOMANOMETRIA', [
    'vasoconstrictor' => true,
    'tabla' => [
        'cabeceras' => ['Fosa', 'Pico insp. (Pa)', 'R 75', 'R 150', 'R 150 con VC', 'Cambio'],
        'filas' => [['FND', '450', '0,63', '0,82', '0,46', '-44 %'], ['FNI', '385', '0,27', '0,38', '0,29', '-23 %'],
                    ['Total', '', '0,19', '0,26', '0,18', '-31 %']],
    ],
    'avisos' => ['FNI (reposo): No alcanza 150 Pa en inspiración: leer a 75 Pa y decir a qué presión.'],
    'hallazgos' => 'Resistencia aumentada en FND.', 'conclusion' => 'Obstrucción mixta derecha.',
], $paciente, 'Alumno X', '29-10-2026');
t_true(strpos($rm, '%PDF-1.4') === 0 && substr(trim($rm), -5) === '%%EOF', 'El informe de rinomanometría sale como PDF');
t_true(strpos($rm, 'Rinomanometr') !== false, 'Lleva su título');
t_true(strpos($rm, 'vasoconstrictor') !== false, 'Dice que hubo prueba de vasoconstrictor');
t_true(strpos($rm, '0,82') !== false && strpos($rm, 'Total') !== false, 'Trae la tabla que mandó la app');
t_true(strpos($rm, 'No alcanza 150 Pa') !== false, 'Trae los avisos del equipo');
t_true(strpos($rm, 'Obstrucci') !== false, 'Trae la conclusión');
foreach ($nasales as $t) {
    t_true(strpos(ReportPdfBuilder::build(999, $t, [], $paciente, 'A', '29-10-2026'), '%PDF-1.4') === 0,
           "{$t} vacío igual genera PDF");
}

$rs = ReportPdfBuilder::build(999, 'RINOSCOPIA', [
    'D' => ['tabique' => 'desviado', 'cornete_inferior' => 'contacta', 'mucosa' => 'rosada', 'secrecion' => 'no',
            'perforacion' => false, 'observaciones' => 'Desviación en el tercio anterior.'],
    'I' => ['tabique' => 'centrado', 'cornete_inferior' => 'hipertrofico', 'mucosa' => 'palida'],
    'tecnica' => ['primera_fosa' => 'D', 'posiciones' => ['D' => [0, 30, 60], 'I' => [0]]],
    'conclusion' => 'Desviación septal derecha.',
], $paciente, 'Alumno X', '29-10-2026');
t_true(strpos($rs, '%PDF-1.4') === 0, 'El informe de rinoscopía sale como PDF');
t_true(strpos($rs, 'Desviado hacia esta fosa') !== false && strpos($rs, 'Contacta el tabique') !== false,
       'Trae lo que el alumno marcó en cada fosa');
t_true(strpos($rs, 'Primero la fosa derecha') !== false, 'Dice qué fosa miró primero');
t_true(strpos($rs, 'FNI: cabeza en 0') !== false, 'Dice en qué posiciones miró cada fosa');

// Espirometría: los datos del examen y la tabla del manual SER 2024.
$esp = ReportPdfBuilder::build(999, 'ESPIROMETRIA', [
    'paciente' => ['sexo' => 'M', 'edad' => 27, 'talla' => 176, 'peso' => 74, 'etnia' => 'caucasico'],
    'ecuacion' => 'GLI-2012, grupo caucásico',
    'broncodilatador' => ['clave' => 'salbutamol', 'nombre' => 'Salbutamol 400 µg con aerocámara',
                          'espera_min' => 15, 'minutos_primera' => 16],
    'verificacion' => ['ok' => true, 'descargas' => []],
    'ambiente' => ['temperatura' => 21.8, 'humedad' => 44, 'presion' => 1019],
    'calidad' => ['pre' => 'VEF1 A, CVF A', 'post' => 'VEF1 A, CVF B'],
    'bd_previo' => 'salbutamol hace más de 24 horas',
    'tabla' => [
        'cabeceras' => ['', 'Teór.', 'Pre', '% Teór.', 'LIN', 'z', 'Post', '% Teór.', 'z', 'Cambio (L)', 'Cambio (% teór.)'],
        'filas' => [['CVF (L)', '5,37', '4,86', '91', '4,34', '-0,81', '5,06', '94', '-0,50', '+0,19', '+3,6'],
                    ['VEF1 (L)', '4,47', '3,20', '72', '3,59', '-2,35', '3,78', '84', '-1,30', '+0,58', '+12,9']],
    ],
    'avisos' => ['Pre: 2 maniobras aceptables (se buscan 3).'],
    'conclusion' => 'Patrón obstructivo con respuesta significativa al broncodilatador.',
], $paciente, 'Alumno X', '29-10-2026');
t_true(strpos($esp, '%PDF-1.4') === 0, 'El informe de espirometría sale como PDF');
t_true(strpos($esp, 'GLI-2012') !== false, 'Dice qué valores teóricos usó');
t_true(strpos($esp, 'a los 16 minutos') !== false, 'Dice cuándo fue la primera maniobra post');
t_true(strpos($esp, 'VEF1 A, CVF B') !== false, 'Trae la calidad pre y post');
t_true(strpos($esp, '+12,9') !== false, 'Trae la tabla que mandó la app');
t_true(strpos($esp, 'verificado con la jeringa') !== false, 'Dice que el equipo se verificó');
