<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseSheetPdf.php';

/**
 * La ficha en PDF. No se puede "ver" un PDF desde un test, así que se
 * comprueba lo que sí se puede: que el documento sea válido, que TODO lo que
 * el docente cargó aparezca (una sección que se olvida de dibujar es el bug
 * caro acá), y que las curvas que se sintetizan --timpanograma y
 * logoaudiograma-- tengan la forma que dice el tipo elegido.
 */

/** Caso de prueba: mixta en OD, coclear con rollover en OI. */
function ficha_caso_demo(): array
{
    $pares = static function (array $od, array $oi): array {
        $out = [];
        foreach ($od as $i => $v) {
            $out[] = [$v, $oi[$i]];
        }
        return $out;
    };

    return [
        'gender' => 1,
        'edad' => 44,
        'Aerea' => $pares([50, 50, 45, 42, 38, 40, 42, 45, 45], [15, 15, 20, 25, 40, 50, 55, 60, 60]),
        'Osea' => $pares([10, 10, 12, 15, 25, 18, 15, 15, 15], [15, 15, 20, 25, 40, 50, 55, 60, 60]),
        'LDL' => $pares([110, 110, 105, 105, 100, 100, 100, 100, 100], array_fill(0, 9, 130)),
        'Z_OD' => 'As', 'Z_OI' => 'A',
        'volume' => [1.2, 1.1, 'N/D'],
        'ETF' => ['Normal', 'Disfunción tubaria'],
        'Rinne' => ['500' => ['od' => 'negativo', 'oi' => 'positivo'], '1000' => ['od' => 'negativo', 'oi' => 'positivo']],
        'Weber' => ['500' => 'od', '1000' => 'od'],
        'UMD' => [['int' => 70, 'percentage' => 96], ['int' => 65, 'percentage' => 80]],
        'SDT' => [38, 30], 'SRT' => [45, 38], 'SISI' => [20, 80],
        'recruit' => [false, true], 'Stenger' => [false, false],
        'Fowler' => ['patterns' => ['4' => 'complete'], 'diplacusia' => false],
        'Carhart' => [[5, 25], [5, 25], [0, 20], [0, 15]],
        'Stat' => [[0, 10], [0, 10], [0, 5]],
        'Rosemberg' => [[5, 30], [5, 30], [0, 25], [0, 20]],
        'Reflex' => [
            'ipsi' => [[130, 95], [130, 95], [130, 100], [130, 105]],
            'contra' => [[130, 95], [130, 95], [130, 100], [130, 105], [130, 95]],
            'tipo' => ['od' => 'normal', 'oi' => 'invertido'],
        ],
        'ABR' => [
            'OD' => ['type' => 'transmission', 'umbral' => 45],
            'OI' => ['type' => 'coclear', 'umbral' => 50, 'neural' => ['iii_v_ms' => 0.6, 'desincronia' => 'alta']],
        ],
        'EOAS' => [
            'OD' => ['type' => 'transmission', 'umbral' => 40, 'desviaciones' => ['500' => 25, '1000' => 22, '1500' => 20, '2000' => 18, '3000' => 16, '4000' => 15, '6000' => 15, '8000' => 15]],
            'OI' => ['type' => 'coclear', 'umbral' => 45, 'desviaciones' => ['500' => 5, '1000' => 8, '1500' => 14, '2000' => 20, '3000' => 30, '4000' => 38, '6000' => 42, '8000' => 45]],
        ],
        'VEMP' => [
            'OD' => ['type' => 'normal', 'subtipos' => ['CVEMP' => ['umbral' => 90], 'OVEMP' => ['umbral' => 88], 'MVEMP' => ['umbral' => 92]]],
            'OI' => ['type' => 'normal', 'subtipos' => ['CVEMP' => ['umbral' => 60], 'OVEMP' => ['umbral' => 65], 'MVEMP' => ['umbral' => 70]]],
        ],
        'Otoscopia' => ['fases' => [['texto' => 'Mancha de Schwartze en OD.']]],
        'Tinnitus' => ['presente' => true, 'lateralidad' => 'unilateral', 'oido' => 'od',
                       'ruido' => 'Zumbido', 'frecuencia' => 500, 'permanente' => true],
        'Anamnesis' => ['antecedentes' => ['hipoacusia_familiar' => 1], 'medicamentos' => 'Ninguno'],
        'PatientBehavior' => 'Colaboradora.',
        'PatientDisposition' => 80,
        'Perfil' => ['version' => 1, 'OD' => ['cce_pct' => 100.0], 'OI' => ['cce_pct' => 90.0],
                     'auto' => ['abr' => true, 'eoas' => true]],
    ];
}

$pdfDemo = CaseSheetPdf::build('CASO-TEST', ficha_caso_demo(), ['nombre' => 'Ana', 'apellido' => 'Pérez', 'rut' => '11.111.111-1'], 'Docente', '10-09-2026');

t_true(strpos($pdfDemo, '%PDF-1.4') === 0, 'La ficha sale como un PDF');
t_true(substr(trim($pdfDemo), -5) === '%%EOF', 'El PDF cierra con %%EOF');
// Paginación fija: un examen por página, para poder imprimir o archivar
// cualquiera de ellos suelto sin partirlo al medio.
t_eq(substr_count($pdfDemo, '/Type /Page '), 6,
    'La ficha son seis páginas: generales+anamnesis, tonal, impedanciometría, ABR, OEA y VEMP');
t_true(strlen($pdfDemo) > 20000, 'El PDF trae contenido, no una página en blanco');

// Ninguna sección puede faltar: el texto va en WinAnsi sin comprimir, así
// que los títulos se pueden buscar en los bytes del stream.
foreach ([
    'Ficha del caso', 'Perfil auditivo', 'Audiometr', 'Acumetr', 'Impedanciometr',
    'Logoaudiometr', 'supraliminares', 'ABR', 'OEA', 'VEMP', 'Otoscopia',
] as $seccion) {
    t_true(strpos($pdfDemo, $seccion) !== false, "La ficha incluye la sección '{$seccion}'");
}

// Y los datos del caso, no solo los rótulos.
t_true(strpos($pdfDemo, '#CASO-TEST') !== false, 'El PDF identifica el caso con su numeral');

// Marca y numeración: el pie va en TODAS las páginas, y el año es el de
// emisión (no el de hoy: una ficha impresa el año que viene no se firma sola
// con el año que viene).
t_eq(substr_count($pdfDemo, 'Desarrollado con LabSim'), 6,
    'La marca del pie está en las seis páginas');
t_true(strpos($pdfDemo, 'LabSim 2026 para la simulaci') !== false,
    'El pie lleva el año de emisión de la ficha');

// El logo es un JPEG incrustado: si el archivo se pierde, la ficha sale
// igual (PdfImage devuelve null) pero esto avisa.
t_true(substr_count($pdfDemo, '/Subtype /Image') >= 1, 'El logo se incrusta en la portada');
t_true(strpos($pdfDemo, 'curva tipo As') !== false, 'El timpanograma dice el tipo del oído');
// Los paréntesis delimitan las cadenas en un content stream, así que MiniPdf
// los escapa: en los bytes del PDF "(-)" aparece como "\(-\)".
t_true(strpos($pdfDemo, '\\(-\\)') !== false, 'Un reflejo fuera de escala se imprime (-), no 130 dB');

// Un caso vacío (recién creado, sin nada cargado) tiene que salir igual: el
// PDF no puede ser lo que se rompa cuando alguien imprime una ficha a medias.
$pdfVacio = CaseSheetPdf::build('VACIO', []);
t_true(strpos($pdfVacio, '%PDF-1.4') === 0, 'Una ficha vacía igual genera un PDF');
t_true(strpos($pdfVacio, 'Sin cita asociada') !== false, 'Sin paciente, la ficha lo dice en vez de fallar');

// --- Las curvas que se sintetizan --------------------------------------

// Timpanograma: la curva sale del TIPO, y cada tipo tiene que dar la forma
// que lo define -- si esto se desalinea con tympanogram.js, el docente ve
// una curva en el editor y otra en el PDF.
foreach (CaseBuilder::Z_OPTIONS as $tipo) {
    $pts = CaseCharts::tympanogramPoints($tipo);
    // Paso de 5 daPa: con 10 el muestreo recortaba la punta del ápice.
    t_eq(count($pts), 121, "Timpanograma {$tipo}: cubre -400..200 daPa de 5 en 5");
    if ($tipo === 'B') {
        // B no tiene pico: su hallazgo es no tenerlo, y se comprueba abajo.
        continue;
    }
    $picos = array_column($pts, 1);
    $presiones = array_column($pts, 0);
    $presionPico = $presiones[array_search(max($picos), $picos, true)];
    $esperada = in_array($tipo, ['C', 'Cs'], true) ? -150.0 : 0.0;
    t_close($presionPico, $esperada, 10.0, "Timpanograma {$tipo}: el pico cae donde corresponde");
}
t_true(max(array_column(CaseCharts::tympanogramPoints('Ad'), 1))
     > max(array_column(CaseCharts::tympanogramPoints('A'), 1)),
    'Ad es más alta que A (oído medio hipermóvil)');
t_true(max(array_column(CaseCharts::tympanogramPoints('As'), 1))
     < max(array_column(CaseCharts::tympanogramPoints('A'), 1)),
    'As es más chata que A (rigidez)');
$curvaB = array_column(CaseCharts::tympanogramPoints('B'), 1);
t_true(max($curvaB) - min($curvaB) < 0.1, 'B es plana: no tiene pico que buscar');

// El ápice va en punta, no redondeado: la pendiente justo al lado del pico
// tiene que ser MUCHO mayor que la de una gaussiana, que ahí llega plana.
$curvaA = CaseCharts::tympanogramPoints('A');
$iPico = 0;
foreach ($curvaA as $i => $pt) {
    if ($pt[1] > $curvaA[$iPico][1]) { $iPico = $i; }
}
$pendienteJuntoAlPico = abs($curvaA[$iPico][1] - $curvaA[$iPico + 1][1]);
$pendienteLejos = abs($curvaA[$iPico + 12][1] - $curvaA[$iPico + 13][1]);
t_true($pendienteJuntoAlPico > $pendienteLejos,
    'La curva cae más rápido junto al ápice que lejos: el pico es una punta, no una loma');

// Y la escala del eje es fija: los dos oídos y todas las fichas se leen igual.
t_eq(CaseCharts::ESCALA_TIMPANOGRAMA_ML, 2.0, 'El timpanograma se dibuja siempre de 0 a 2 mL');
foreach (CaseBuilder::Z_OPTIONS as $tipoZ) {
    t_true(max(array_column(CaseCharts::tympanogramPoints($tipoZ), 1)) <= CaseCharts::ESCALA_TIMPANOGRAMA_ML,
        "Timpanograma {$tipoZ}: su pico cabe en la escala fija");
}

// Logoaudiograma: con reclutamiento la curva CAE pasada la UMD (rollover),
// y sin él se queda en meseta. Es el hallazgo que el gráfico tiene que
// mostrar, no un detalle de dibujo.
$conRollover = CaseCharts::logogramPoints(['sdt' => 30, 'srt' => 38, 'umd_int' => 65, 'umd_pct' => 80, 'recruit' => true]);
$sinRollover = CaseCharts::logogramPoints(['sdt' => 30, 'srt' => 38, 'umd_int' => 65, 'umd_pct' => 80, 'recruit' => false]);
t_true(end($conRollover)[1] < 80, 'Con reclutamiento, la discriminación cae después de la máxima');
t_eq(end($sinRollover)[1], 80.0, 'Sin reclutamiento, la curva se queda en meseta');
foreach ([$conRollover, $sinRollover] as $curva) {
    $previa = -INF;
    foreach ($curva as [$db, $pct]) {
        t_true($db >= $previa, 'Los puntos del logoaudiograma van en dB creciente');
        $previa = $db;
    }
}
