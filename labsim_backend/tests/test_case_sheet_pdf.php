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

// Marca y numeración: el pie va en TODAS las páginas, con el año en que se
// imprime el PDF (la marca dice cuándo se generó este papel).
t_eq(substr_count($pdfDemo, 'Desarrollado con LabSim'), 6,
    'La marca del pie está en las seis páginas');
t_true(strpos($pdfDemo, 'LabSim ' . date('Y') . ' para la simulaci') !== false,
    'El pie lleva el año en que se imprime');

// El logo es un JPEG incrustado: si el archivo se pierde, la ficha sale
// igual (PdfImage devuelve null) pero esto avisa.
t_true(substr_count($pdfDemo, '/Subtype /Image') >= 1, 'El logo se incrusta en la portada');

// Identidad del archivo: el visor mostraba el nombre del script que sirve el
// PDF, y la descarga un "ficha_9.pdf" que no decía de quién era.
t_true(strpos($pdfDemo, '/Title (CASO-TEST_A_Perez_11111111-1)') !== false,
    'El documento se titula con el caso, el paciente y su RUT');
t_eq(CaseSheetPdf::identificador('9', ['nombre' => 'Ana María', 'apellido' => 'Pérez González', 'rut' => '11.111.111-1']),
    '9_AM_Perez_Gonzalez_11111111-1',
    'Iniciales de los nombres, apellidos completos y el RUT sin puntos');
t_eq(CaseSheetPdf::identificador('7'), '7', 'Sin paciente queda solo el número de caso');
t_eq(CaseSheetPdf::identificador('12', ['nombre' => 'Juan', 'apellido' => 'Muñoz', 'rut' => '9.876.543-K']),
    '12_J_Munoz_9876543-K',
    'Sin tildes ni eñes: el nombre tiene que sobrevivir a cualquier sistema de archivos');
t_true(strpos($pdfDemo, 'curva tipo As') !== false, 'El timpanograma dice el tipo del oído');

// La hoja es el único apoyo del docente mientras el alumno atiende: tiene
// que traer lo que el caso decidió Y lo que dejó sin decidir.
t_true(strpos($pdfDemo, 'sin decidir') !== false,
    'La portada avisa de las fichas que el caso no terminó de decidir');
t_true(strpos($pdfDemo, '500 Hz') !== false && strpos($pdfDemo, 'Zumbido') !== false,
    'El acúfeno trae los datos con los que se cuadra la acufenometría, no solo la frase del paciente');
// Lo que el audiograma dibuja no se repite en números: el LDL tiene su
// propia línea en el gráfico y una tabla al lado obliga a leer dos veces lo
// mismo y a dudar de cuál manda.
t_true(strpos($pdfDemo, 'LDL (dB HL)') === false,
    'El LDL no se repite en tabla: ya está dibujado en el audiograma');

t_true(strpos($pdfDemo, 'Interpico I-V') !== false,
    'El ABR informa los interpicos a 80 dB');
t_true(strpos($pdfDemo, 'FSP objetivo') !== false && strpos($pdfDemo, 'Alcanza el objetivo') !== false,
    'El ABR dice qué FSP logra y si llega al objetivo');
// La hoja de OEA trae los números, no solo las curvas: emisión, ruido y la
// relación entre los dos, que es lo que decide el PASS/REFER.
t_true(strpos($pdfDemo, 'OD emis.') !== false && strpos($pdfDemo, 'OD S/R') !== false,
    'La OEA informa emisión, ruido y relación señal/ruido por banda');
foreach (['TEOAE 1k', 'DP 8k', 'SFOAE 500'] as $banda) {
    t_true(strpos($pdfDemo, $banda) !== false, "La tabla de OEA incluye la banda '{$banda}'");
}
// Los paréntesis delimitan las cadenas en un content stream, así que MiniPdf
// los escapa: en los bytes del PDF "(-)" aparece como "\(-\)".
t_true(strpos($pdfDemo, '\\(-\\)') !== false, 'Un reflejo fuera de escala se imprime (-), no 130 dB');

// Un caso vacío (recién creado, sin nada cargado) tiene que salir igual: el
// PDF no puede ser lo que se rompa cuando alguien imprime una ficha a medias.
$pdfVacio = CaseSheetPdf::build('VACIO', []);
t_true(strpos($pdfVacio, '%PDF-1.4') === 0, 'Una ficha vacía igual genera un PDF');
t_true(strpos($pdfVacio, 'Sin cita asociada') !== false, 'Sin paciente, la ficha lo dice en vez de fallar');

// --- Un umbral que no existe no se dibuja ni se promedia ---------------
//
// 130 es "no se midió" o "no hubo respuesta", no un umbral de 130 dB. El eje
// del audiograma llega a 120: sin este corte se dibujaba recortado contra el
// borde, la línea lo unía con sus vecinos y entraba al promedio.

t_eq(CaseCharts::SIN_UMBRAL_DB, 130, 'El valor que marca "sin umbral" es el 130 con el que guarda el caso');

// Un hueco FUERA del promedio (6k y 8k) no cambia los promedios, así que no
// hay nada que avisar.
$huecoAgudos = ficha_caso_demo();
foreach ([7, 8] as $i) {
    $huecoAgudos['Aerea'][$i][1] = 130;
}
$pdfAgudos = CaseSheetPdf::build('HUECOS', $huecoAgudos);
t_true(strpos($pdfAgudos, '%PDF-1.4') === 0, 'Un caso con frecuencias sin umbral igual genera la ficha');
t_true(strpos($pdfAgudos, 'frecuencias sin umbral') === false,
    'Un hueco fuera del promedio no dispara el aviso: los promedios no cambian');

// Uno DENTRO del promedio sí: ahí el número sale de tres frecuencias y no de
// cuatro, y eso hay que decirlo.
$huecoEnPromedio = ficha_caso_demo();
$huecoEnPromedio['Aerea'][6][1] = 130;
$pdfHueco = CaseSheetPdf::build('HUECOS', $huecoEnPromedio);
t_true(strpos($pdfHueco, 'frecuencias sin umbral') !== false,
    'Sin umbral en 4k, la ficha avisa que el promedio va con las que responden');

// El promedio ignora las frecuencias sin umbral en vez de meter 130 en la
// cuenta, que daría un promedio que nadie puede informar.
$promedio = new ReflectionMethod('CaseSheetPdf', 'promedio');
$promedio->setAccessible(true);
t_close($promedio->invoke(null, [0, 0, 20, 30, 40, 0, 50, 0, 0], [2, 3, 4, 6]), 35.0, 0.01,
    'Sin huecos, el promedio es el de las cuatro frecuencias');
t_close($promedio->invoke(null, [0, 0, 20, 30, 40, 0, 130, 0, 0], [2, 3, 4, 6]), 30.0, 0.01,
    'Con 4k sin umbral, promedia las otras tres y no mete el 130');
t_eq($promedio->invoke(null, array_fill(0, 9, 130), [2, 3, 4, 6]), null,
    'Sin ninguna frecuencia con umbral no hay promedio que informar');

// --- Las curvas que se sintetizan --------------------------------------

// Timpanograma: la curva sale del TIPO, y cada tipo tiene que dar la forma
// que lo define -- si esto se desalinea con tympanogram.js, el docente ve
// una curva en el editor y otra en el PDF; si se desalinea con Z_225, ve
// una curva distinta a la que le sale al alumno en el equipo.
foreach (CaseBuilder::Z_OPTIONS as $tipo) {
    $pts = CaseCharts::tympanogramPoints($tipo);
    t_true($pts[0][0] <= -400.0, "Timpanograma {$tipo}: el barrido arranca en el borde de la ventana");
    t_true(end($pts)[0] >= 190.0, "Timpanograma {$tipo}: el barrido llega al otro borde");
    $previa = -INF;
    foreach ($pts as [$daPa, $ml]) {
        t_true($daPa > $previa, "Timpanograma {$tipo}: el barrido va en presión creciente");
        $previa = $daPa;
    }
    if ($tipo === 'B') {
        // B no tiene pico: su hallazgo es no tenerlo, y se comprueba abajo.
        continue;
    }
    $v = CaseCharts::valoresTimpanograma($tipo);
    $picos = array_column($pts, 1);
    $presiones = array_column($pts, 0);
    $presionPico = $presiones[array_search(max($picos), $picos, true)];
    t_close($presionPico, (float) $v['pico_dapa'], 10.0, "Timpanograma {$tipo}: el pico cae donde corresponde");
    t_true($v['pico_dapa'] >= $v['p_min'] && $v['pico_dapa'] <= $v['p_max'],
        "Timpanograma {$tipo}: la presión dibujada cae dentro del rango que sortea la app");
    t_true($v['estatica'] >= $v['c_min'] && $v['estatica'] <= $v['c_max'],
        "Timpanograma {$tipo}: la compliance dibujada cae dentro del rango que sortea la app");
}
t_true(max(array_column(CaseCharts::tympanogramPoints('Ad'), 1))
     > max(array_column(CaseCharts::tympanogramPoints('A'), 1)),
    'Ad es más alta que A (oído medio hipermóvil)');
t_true(max(array_column(CaseCharts::tympanogramPoints('As'), 1))
     < max(array_column(CaseCharts::tympanogramPoints('A'), 1)),
    'As es más chata que A (rigidez)');
$curvaB = array_column(CaseCharts::tympanogramPoints('B'), 1);
t_true(max($curvaB) - min($curvaB) < 0.1, 'B es plana: no tiene pico que buscar');

// La forma es el coseno alzado de la app: llega y sale del ápice con
// pendiente cero, y también empalma con la línea base sin quiebre. Lo que
// cae de verdad es la mitad del flanco. Antes la ficha dibujaba un ápice en
// punta, que no es lo que ve el alumno.
$curvaA = CaseCharts::curvaTimpanograma(0.95, -40.0);
$iPico = 0;
foreach ($curvaA as $i => $pt) {
    if ($pt[1] > $curvaA[$iPico][1]) { $iPico = $i; }
}
$caida = static fn (array $c, int $i): float => abs($c[$i][1] - $c[$i + 1][1]);
$mitadFlanco = (int) round($iPico / 2);
t_true($caida($curvaA, $iPico) < $caida($curvaA, $mitadFlanco),
    'El ápice llega con pendiente cero: el coseno alzado no hace punta');
t_true($caida($curvaA, 0) < $caida($curvaA, $mitadFlanco),
    'Y el pie de la curva empalma con la línea base sin quiebre');

// La gradiente se calcula como en el equipo (Z.move): altura a +-50 daPa
// del pico sobre la altura del pico, entre 0 y 1. Con el semiancho fijo de
// la app da 0.85 para cualquier curva con pico -- es un número que NO
// discrimina tipos, y la ficha tiene que mostrar eso y no otra cosa.
foreach (CaseBuilder::Z_OPTIONS as $tipo) {
    $v = CaseCharts::valoresTimpanograma($tipo);
    t_true($v['gradiente'] >= 0.0 && $v['gradiente'] <= 1.0,
        "Timpanograma {$tipo}: la gradiente queda entre 0 y 1");
    if (!$v['plana']) {
        t_close($v['gradiente'], 0.85, 0.02,
            "Timpanograma {$tipo}: la gradiente es la que calcula el equipo");
    }
}
t_eq(CaseCharts::gradienteTimpanograma(0.0, 0.0), 0.0, 'Sin compliance no hay gradiente que calcular');

// La escala sube cuando la curva no cabe, como el botón cc del equipo.
t_eq(CaseCharts::escalaTimpanograma(0.95), 1.0, 'Una curva chica se lee en el tope de 1 mL');
t_eq(CaseCharts::escalaTimpanograma(1.6), 2.0, 'Una A alta necesita el tope de 2 mL');
t_eq(CaseCharts::escalaTimpanograma(CaseCharts::valoresTimpanograma('Ad')['estatica']), 5.0,
    'Un Ad no cabe en 2 mL: la ficha sube la escala en vez de recortar la curva');
t_eq(CaseCharts::escalaTimpanograma(99.0), 8.0, 'Por encima de todo, queda el tope más alto');

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
