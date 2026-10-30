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
foreach (['rm_curva', 'rm_resistencia', 'ra_curva', 'esp_fv', 'esp_vt', 'olf_umbral', 'prick_brazo', 'psg_noche', 'cpap_noche'] as $suf) {
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

// Olfatometría: puntajes por narina, categoría del alumno y P10.
$olf = ReportPdfBuilder::build(999, 'OLFATOMETRIA', [
    'paciente' => ['edad' => 35, 'sexo' => 'F'],
    'preparacion' => ['pregunto' => true, 'respuesta' => 'no fumó ni comió', 'espero' => false],
    'ensayos' => [],
    'puntajes' => [
        'ambas' => ['T' => 7.5, 'D' => 11, 'I' => 12, 'TDI' => 30.5],
        'D' => ['T' => 7.0, 'D' => 10, 'I' => 12, 'TDI' => 29.0],
        'I' => ['T' => null, 'D' => null, 'I' => null, 'TDI' => null],
    ],
    'p10' => 30.5, 'grupo_edad' => '31–40', 'categoria' => 'hiposmia',
    'hallazgos' => 'Hiposmia bilateral.', 'conclusion' => 'Control en 3 meses.',
], $paciente, 'Alumno X', '29-10-2026');
t_true(strpos($olf, '%PDF-1.4') === 0, 'El informe de olfatometría sale como PDF');
t_true(strpos($olf, 'Hiposmia') !== false && strpos($olf, '30,5') !== false, 'Trae la categoría y el P10 con coma');
t_true(strpos($olf, 'Narina derecha') !== false && strpos($olf, '29,0') !== false, 'Trae el TDI de la narina derecha');

// Prick: la hoja de registro, por orden de punción.
$prick = ReportPdfBuilder::build(999, 'PRICK', [
    'paciente' => ['edad' => 27, 'sexo' => 'M'], 'pregunto_farmacos' => true, 'farmacos' => 'ninguno.',
    'sitios' => [
        ['extracto' => 'dpte', 'nombre' => 'D. pteronyssinus', 'x' => 0, 'y' => 60, 'orden' => 2,
         'lectura' => ['mayor' => 8.0, 'perpendicular' => 6.0, 'min' => 17.0], 'resultado' => 'positivo'],
        ['extracto' => 'gato', 'nombre' => 'Gato (epitelio)', 'x' => 20, 'y' => 60, 'orden' => 3,
         'lectura' => ['mayor' => 3.5, 'perpendicular' => 3.0, 'min' => 17.0], 'resultado' => 'positivo'],
        ['extracto' => 'neg', 'nombre' => 'Control negativo', 'x' => 0, 'y' => 30, 'orden' => 1,
         'lectura' => ['mayor' => null, 'perpendicular' => null, 'min' => 17.0], 'resultado' => 'valido'],
    ],
    'lectura_min' => 17.0, 'hallazgos' => 'Sensibilización a ácaros.', 'conclusion' => 'Rinitis alérgica.',
], $paciente, 'Alumno X', '29-10-2026');
t_true(strpos($prick, '%PDF-1.4') === 0, 'El informe de prick sale como PDF');
t_true(strpos($prick, "8 \xD7 6 mm") !== false, 'Trae la pápula mayor × perpendicular');
t_true(strpos($prick, "3,5 \xD7 3 mm") !== false, 'La pápula conserva el medio milímetro de la regla');
t_true(strpos($prick, 'ninguno.') !== false && strpos($prick, 'ninguno..') === false, 'Fármacos con un solo punto final');
t_true(strpos($prick, "sin p\xE1pula") !== false && strpos($prick, "Sin reacci\xF3n \\(v\xE1lido\\)") !== false, 'Dice cuando no hay pápula');
t_true(strpos($prick, 'Positivo') !== false && strpos($prick, "minutos de la punci\xF3n") !== false, 'Trae el resultado y el minuto de lectura');

// Polisomnografía: título, regla, montaje con lo que falta, tabla y gravedad.
$datosPsg = [
    'estudio' => 'psg', 'montaje' => ['eeg', 'canula', 'spo2'], 'regla' => '4',
    'eventos' => [['t' => 1200, 'dur' => 20, 'tipo' => 'ao', 'auto' => true]], 'excluidos' => [],
    'indices' => ['IAH' => 32.4], 'avisos' => ['Falta el EMG mentoniano.'], 'gravedad' => 'moderada',
    'tabla' => ['cabeceras' => ['Parámetro', 'Valor'], 'filas' => [['IAH', '32,4 /h'], ['SpO2 mínima', '81 %']]],
    'hallazgos' => 'Apneas obstructivas en supino.', 'conclusion' => 'SAOS moderado.',
];
$psg = ReportPdfBuilder::build(999, 'POLISOMNOGRAFIA', $datosPsg, $paciente, 'Alumno X', '29-10-2026');
t_true(strpos($psg, '%PDF-1.4') === 0, 'El informe de polisomnografía sale como PDF');
t_true(strpos($psg, 'Polisomnograf') !== false && strpos($psg, 'noche completa') !== false, 'Trae el título de la polisomnografía');
t_true(strpos($psg, '32,4 /h') !== false && strpos($psg, 'SpO2 m') !== false, 'Trae la tabla que mandó la app');
t_true(strpos($psg, 'Gravedad por el') !== false && strpos($psg, 'moderada') !== false, 'Trae la gravedad que eligió el alumno');
t_true(strpos($psg, 'Aceptable') !== false, 'Dice la regla de hipopnea en palabras');
t_true(strpos($psg, 'EMG mentoniano') !== false && strpos($psg, 'faltan') !== false, 'Dice los sensores que faltan');
t_true(strpos($psg, 'Falta el EMG mentoniano') !== false, 'Trae los avisos');
$pg = ReportPdfBuilder::build(999, 'POLISOMNOGRAFIA', ['estudio' => 'pg', 'montaje' => ['canula', 'torax', 'abd', 'spo2', 'ron', 'pos'], 'regla' => '3', 'gravedad' => ''] + $datosPsg, $paciente, 'Alumno X', '29-10-2026');
t_true(strpos($pg, 'Poligraf') !== false && strpos($pg, 'domiciliaria') !== false, 'La poligrafía lleva su título');
t_true(strpos($pg, 'faltan') === false, 'Con el montaje completo de la poligrafía no falta nada');
t_true(strpos($pg, 'sin elegir') !== false, 'Sin gravedad elegida lo dice');

// Lo que WinAnsi no tiene no sale como "?": ≥ y los subíndices.
$sp = ReportPdfBuilder::build(999, 'POLISOMNOGRAFIA', [
    'estudio' => 'psg', 'montaje' => [], 'regla' => '3', 'eventos' => [], 'excluidos' => [],
    'tabla' => ['cabeceras' => ['Parámetro', 'Valor'], 'filas' => [['SpO₂ media / mínima', '94 %'], ['IDO ≥ 3 %', '20']]],
    'avisos' => [], 'gravedad' => '', 'hallazgos' => '', 'conclusion' => '',
], $paciente, 'Alumno X', '30-10-2026');
t_true(strpos($sp, 'SpO2 media') !== false && strpos($sp, 'IDO >= 3') !== false, 'Subíndices y desigualdades legibles en el PDF');


// CPAP: interfaz, presiones, duración, tabla de 11 columnas, presión indicada y grado.
$datosCpap = [
    'interfaz' => 'oronasal', 'talla' => 'L', 'cambios' => [[0, 4], [900, 6], [2400, 10]], 't_fin' => 22260, 'terminada' => true,
    'tabla' => ['cabeceras' => ['cmH₂O', 'Minutos', 'Sueño (min)', 'REM supino (min)', 'Apneas O/M/C', 'Hipopneas', 'RERA', 'IDR', 'SpO₂ mín.', 'Ronquido (min)', 'Fuga (L/min)'],
                'filas' => [['4', '15', '12', '0', '3/0/0', '4', '1', '40,0', '84', '9', '6'], ['10', '120', '100', '8', '0/0/0', '0', '0', '1,2', '93', '0', '9']]],
    'idr_basal' => 38.5, 'presion_indicada' => 10, 'grado' => 'optima',
    'hallazgos' => 'Los eventos cedieron a 10.', 'conclusion' => 'CPAP a 10.',
];
$cpap = ReportPdfBuilder::build(999, 'CPAP', $datosCpap, $paciente, 'Alumno X', '30-10-2026');
t_true(strpos($cpap, '%PDF-1.4') === 0, 'El informe de CPAP sale como PDF');
t_true(strpos($cpap, 'Titulaci') !== false && strpos($cpap, 'manual de CPAP') !== false, 'Trae el título de la titulación');
t_true(strpos($cpap, 'Mascarilla oronasal') !== false && strpos($cpap, 'talla L') !== false, 'Dice la interfaz y la talla');
t_true(strpos($cpap, '6 h 11 min') !== false && strpos($cpap, 'Se termin') !== false, 'Dice la duración y que se terminó');
t_true(strpos($cpap, 'Fuga \\(L/min\\)') !== false && strpos($cpap, '3/0/0') !== false, 'Trae la tabla de 11 columnas');
t_true(strpos($cpap, 'indicada: 10') !== false, 'Trae la presión indicada');
t_true(strpos($cpap, 'ptima') !== false, 'Trae el grado en palabras');
$cpap0 = ReportPdfBuilder::build(999, 'CPAP', ['interfaz' => 'nasal', 'talla' => 'M', 'presion_indicada' => null, 'grado' => ''] + $datosCpap, $paciente, 'Alumno X', '30-10-2026');
t_true(strpos($cpap0, 'sin indicar') !== false && strpos($cpap0, 'sin elegir') !== false, 'Sin presión ni grado lo dice');

// En producción el PDF se arma sin el resto de la app cargada: cada cuerpo
// tiene que traer lo que usa (cpapBody usaba CaseForm sin cargarlo).
foreach (['POLISOMNOGRAFIA', 'CPAP', 'OLFATOMETRIA', 'PRICK', 'ESPIROMETRIA'] as $t) {
    $codigo = 'require "' . __DIR__ . '/../src/ReportFile.php"; require "' . __DIR__ . '/../src/ReportPdfBuilder.php";'
        . ' echo substr(ReportPdfBuilder::build(999, "' . $t . '", ["estudio" => "psg", "cambios" => [[0, 4]],'
        . ' "interfaz" => "nasal", "talla" => "M", "regla" => "3"], ["nombre" => "A", "apellido" => "B"], "X", "30-10-2026"), 0, 8);';
    $salida = (string) shell_exec(escapeshellarg(PHP_BINARY) . ' -r ' . escapeshellarg($codigo) . ' 2>&1');
    t_true(strpos($salida, '%PDF-1.4') === 0, "El PDF de {$t} se arma solo con ReportFile y ReportPdfBuilder: " . substr($salida, 0, 120));
}

