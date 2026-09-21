<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseSheetPdf.php';
require_once __DIR__ . '/../src/EstudioRedactor.php';

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
t_eq(substr_count($pdfDemo, '/Type /Page '), 7,
    'La ficha son siete páginas: generales+anamnesis, tonal, impedanciometría, ABR, OEA, tamizaje y VEMP');
t_true(strlen($pdfDemo) > 20000, 'El PDF trae contenido, no una página en blanco');

// La ficha no tiene ninguna fuente de azar de verdad: regenerar el mismo
// caso tiene que dar el mismo PDF byte a byte, si no cada apertura se vería
// distinta.
t_eq(
    CaseSheetPdf::build('CASO-TEST', ficha_caso_demo(), ['nombre' => 'Ana', 'apellido' => 'Pérez', 'rut' => '11.111.111-1'], 'Docente', '10-09-2026'),
    $pdfDemo,
    'El mismo caso genera el mismo PDF byte a byte'
);

// Ninguna sección puede faltar: el texto va en WinAnsi sin comprimir, así
// que los títulos se pueden buscar en los bytes del stream.
foreach ([
    'Ficha del caso', 'Perfil auditivo', 'Audiometr', 'Acumetr', 'Impedanciometr',
    'Logoaudiometr', 'supraliminares', 'ABR', 'OEA', 'Tamizaje automatizado',
    'VEMP', 'Otoscopia',
] as $seccion) {
    t_true(strpos($pdfDemo, $seccion) !== false, "La ficha incluye la sección '{$seccion}'");
}

// Y los datos del caso, no solo los rótulos.
t_true(strpos($pdfDemo, '#CASO-TEST') !== false, 'El PDF identifica el caso con su numeral');

// Marca y numeración: el pie va en TODAS las páginas, con el año en que se
// imprime el PDF (la marca dice cuándo se generó este papel).
t_eq(substr_count($pdfDemo, 'Desarrollado con LabSim'), 7,
    'La marca del pie está en las siete páginas');
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
// La letra de Jerger no es una respuesta: se lee directo de la curva, así
// que va impresa sobre el gráfico (además de en la tabla) -- por eso "As"
// tiene que aparecer más de una vez.
t_true(substr_count($pdfDemo, 'As') >= 2, 'La letra de Jerger va sobre el timpanograma y en la tabla');
t_true(strpos($pdfDemo, 'Jerger') !== false, 'La tabla trae la fila con la letra de Jerger');

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

// UMD: no es un solo punto, es la subida de 5 en 5 dB hasta el máximo de
// CADA oído (ficha_caso_demo: OD 96% a 70dB desde SDT 38 sin rollover, OI
// 80% a 65dB con rollover desde SDT 30 -- por eso OI sigue un escalón más
// arriba, a 70). La tabla junta las dos ventanas en filas compartidas, pero
// un nivel que no es de la ventana PROPIA de un oído queda en "--": nada de
// seguir subiendo la intensidad en el oído que ya no tiene motivo clínico
// para seguir (sin rollover, no hay nada más que ver arriba del máximo).
// Las filas se numeran por POSICIÓN (UMD1/UMD2/...), no por dB: cada oído
// prueba su propia ventana y forzarlas a una fila por dB compartido dejaba
// celdas "--" que no aportaban nada (ver nivelesUmdEar() más abajo). OD
// tiene 3 niveles propios y OI 4 (por el escalón de rollover), así que la
// tabla llega hasta UMD4.
foreach (['UMD1', 'UMD2', 'UMD3', 'UMD4'] as $fila) {
    t_true(strpos($pdfDemo, $fila) !== false, "La tabla de UMD trae la fila '{$fila}'");
}
// OD (sin rollover) no se prueba a 55 dB -- ese nivel es de la ventana de
// OI, no de la suya -- así que ningún % calculado para OD en ese nivel
// tiene que aparecer en la ficha.
t_true(strpos($pdfDemo, '51 %') === false,
    'OD no se prueba a 55 dB (no es su ventana): no aparece el % que daría leer su curva ahí');
// Los % salen de la MISMA cúbica que dibuja la curva (CaseCharts::pctLogoEnDb,
// Fritsch-Carlson), no de una recta entre SDT y UMD -- por eso no son un
// tercio/dos tercios parejos entre SDT y UMD.
foreach (['74 %', '90 %', '96 %'] as $pctOd) {
    t_true(strpos($pdfDemo, $pctOd) !== false, "UMD de OD: aparece {$pctOd} en su propia ventana (60/65/70 dB)");
}
// OI tiene rollover: sobre su propio UMD (65 dB) el % cae, no se mantiene,
// y por eso su ventana sí sigue un escalón más arriba (70 dB) -- ahí es
// donde se ve la caída (la Fritsch-Carlson anula la tangente en el pico,
// así que la caída a solo 5 dB del máximo es suave, no un escalón brusco).
foreach (['64 %', '76 %', '80 %', '79 %'] as $pctOi) {
    t_true(strpos($pdfDemo, $pctOi) !== false, "UMD de OI (con rollover): aparece {$pctOi} en su propia ventana (55/60/65/70 dB)");
}

// El mkg de SDT/SRT/UMD (CaseMasking::logo()/boneSdt()): un solo valor --
// el mínimo efectivo, no el rango entero como en la tabla tonal -- y solo
// cuando hace falta enmascarar (a 60 dB, OD todavía no cruza).
t_eq(CaseMasking::boneSdt([10, 10, 12, 15, 25, 18, 15, 15, 15]), 10.0,
    'boneSdt: Fletcher (mejores 2 de 500/1k/2k) al piso de 5, óseo de OD');
t_eq(CaseMasking::boneSdt([15, 15, 20, 25, 40, 50, 55, 60, 60]), 20.0,
    'boneSdt: ídem para OI');
$mkgOdA60 = CaseMasking::logo(60.0, 10.0, 20.0, 30.0);
t_true(!$mkgOdA60['cruza'], 'A 60 dB, OD todavía no cruza (15 < 20 de umbral óseo del contrario)');
$mkgOdA65 = CaseMasking::logo(65.0, 10.0, 20.0, 30.0);
t_true($mkgOdA65['cruza'] && abs($mkgOdA65['min'] - 30.0) < 0.01, 'A 65 dB, OD cruza y el mkg mínimo efectivo es 30 dB');
// El "65 dB/30 dB 90 %" del PDF (confirmado a ojo renderizando a PNG con
// pdftoppm: color propio para el dB y el %, color del oído contrario para
// el mkg) no se puede confirmar con strpos sobre el texto crudo -- cada
// tramo de color es un Tj de MiniPdf separado, así que en los bytes del
// PDF quedan partidos por los operadores de color/posición de en medio,
// no como un string contiguo. La cuenta ya queda probada arriba.

$umdSoloUnNivel = ficha_caso_demo();
$umdSoloUnNivel['UMD'] = [['int' => 45, 'percentage' => 100], ['int' => 45, 'percentage' => 100]];
// Sin rollover en ninguno de los dos oídos: si no, el oído con rollover
// agrega su propio escalón de más arriba y el caso deja de aislar lo que
// se quiere probar acá.
$umdSoloUnNivel['recruit'] = [false, false];
$pdfUmdUnNivel = CaseSheetPdf::build('UMD45', $umdSoloUnNivel);
t_true(strpos($pdfUmdUnNivel, 'UMD1') !== false,
    'Si el máximo sale ya a 45 dB, la tabla de UMD trae un solo nivel');
t_true(strpos($pdfUmdUnNivel, 'UMD2') === false,
    'Si el máximo sale ya a 45 dB y no hay rollover, no hace falta seguir subiendo de a 5');

// Con rollover, la ventana de ESE oído sí sigue un escalón más arriba del
// máximo -- aunque el otro oído no tenga motivo para seguir.
$umdConRolloverA45 = ficha_caso_demo();
$umdConRolloverA45['UMD'] = [['int' => 45, 'percentage' => 100], ['int' => 45, 'percentage' => 90]];
$umdConRolloverA45['recruit'] = [false, true];
$pdfUmdRolloverA45 = CaseSheetPdf::build('UMD45R', $umdConRolloverA45);
t_true(strpos($pdfUmdRolloverA45, 'UMD2') !== false,
    'Con rollover, la ventana de ese oído sigue un escalón más arriba del máximo aunque sea a 45 dB');

// Lo mismo, directo sobre la función: nivelesUmdEar() es la ventana de UN
// oído, no la unión de los dos -- eso lo arma logoaudiometria() aparte.
$nivelesUmdEar = new ReflectionMethod('CaseSheetPdf', 'nivelesUmdEar');
$nivelesUmdEar->setAccessible(true);
t_eq($nivelesUmdEar->invoke(null, 70.0, false), [60.0, 65.0, 70.0],
    'nivelesUmdEar sin rollover no pasa del máximo propio');
t_eq($nivelesUmdEar->invoke(null, 65.0, true), [55.0, 60.0, 65.0, 70.0],
    'nivelesUmdEar con rollover agrega un escalón sobre el máximo propio');
t_eq($nivelesUmdEar->invoke(null, 45.0, false), [45.0],
    'nivelesUmdEar sin rollover y máximo a 45 dB no agrega nada');
t_eq($nivelesUmdEar->invoke(null, 45.0, true), [45.0, 50.0],
    'nivelesUmdEar con rollover sigue un escalón más arriba aunque el máximo ya sea 45 dB');

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

// Fowler sin frecuencias que califiquen: el criterio (diferencia interaural,
// oído bueno normal, sin gap) es la mecánica del test -- va en la ficha
// docente, no en la de estudio.
$sinFowler = ficha_caso_demo();
$sinFowler['Fowler'] = ['patterns' => [], 'diplacusia' => false];
$pdfSinFowlerDocente = CaseSheetPdf::build('SINFOWLER', $sinFowler, [], '', '', false);
$pdfSinFowlerEstudio = CaseSheetPdf::build('SINFOWLER', $sinFowler, [], '', '', true);
t_true(strpos($pdfSinFowlerDocente, 'diferencia interaural') !== false,
    'La ficha docente explica por qué Fowler no calificó ninguna frecuencia');
t_true(strpos($pdfSinFowlerEstudio, 'diferencia interaural') === false,
    'La ficha de estudio NO trae el criterio de calificación de Fowler');

// Y las unidades de los reflejos acústicos son SPL, no HL.
t_true(strpos($pdfDemo, 'Umbrales en dB SPL') !== false,
    'Los umbrales de reflejos acústicos se informan en dB SPL');

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

// --- ABR: cada nivel repetido, y un escalón bajo el umbral sin V --------
//
// La pila de trazos del click no es solo la serie hasta el umbral: cada
// nivel se repite dos veces (el equipo confirma que la V es reproducible)
// y se agrega un escalón más abajo que se queda sin V (así se decide que
// el umbral de arriba es el umbral, y no un nivel más de la serie). Bajar
// de 20 en 20 y, cerca del umbral, de 10 en 10 -- nunca de a 5 (nunca se
// hace un "x5" en la evaluación real): el escalón de confirmación es uno
// más de esos 10, no una fracción aparte.
$nivelesAbr = new ReflectionMethod('CaseSheetPdf', 'nivelesAbr');
$nivelesAbr->setAccessible(true);
t_eq(
    $nivelesAbr->invoke(null, 50.0, 80.0),
    [80.0, 80.0, 60.0, 60.0, 50.0, 50.0, 40.0, 40.0],
    'nivelesAbr duplica cada nivel de la serie y agrega el escalón de 10 dB bajo el umbral'
);
// Sin respuesta en todo el barrido no hay umbral real que confirmar, así
// que no hay escalón de más -- solo el nivel máximo, duplicado.
t_eq($nivelesAbr->invoke(null, 90.0, 80.0), [80.0, 80.0],
    'nivelesAbr sin umbral real (sin respuesta en el barrido) no agrega el escalón de confirmación');
// El escalón de confirmación no baja del piso de -10 dB aunque el umbral
// esté muy cerca de él.
t_true(in_array(-10.0, $nivelesAbr->invoke(null, -8.0, 80.0), true),
    'nivelesAbr no manda el escalón de confirmación bajo el piso de -10 dB');
// El ejemplo real que dio el usuario: umbral a 30 dB -> 80,60,40,30,20.
t_eq(
    array_values(array_unique($nivelesAbr->invoke(null, 30.0, 80.0))),
    [80.0, 60.0, 40.0, 30.0, 20.0],
    'Umbral a 30 dB: la serie es 80,60,40,30,20 (20 en 20 y, cerca del umbral, 10 en 10)'
);
// El umbral del ABR se guarda redondeado a 5 dB (CaseProfile::ABR_STEP_DB):
// la mitad de los casos el umbral YA es un "x5" (45, 35...), y ahí
// "umbral - 10" se queda en la misma familia (45 -> 35, sigue siendo x5).
// El escalón de confirmación tiene que ser el próximo múltiplo de 10 de
// la GRILLA, no un corrimiento relativo al umbral.
t_eq(
    array_values(array_unique($nivelesAbr->invoke(null, 45.0, 80.0))),
    [80.0, 60.0, 45.0, 40.0],
    'Umbral a 45 dB (un "x5" real): el escalón de confirmación es 40, no 35'
);

// Y la razón de que ese escalón sirva: 5 dB bajo el umbral, la onda V cae
// bajo el umbral de visibilidad (el mismo modelo que dibuja el trazo).
$ondasBajoUmbral = CaseWaveforms::ondasClick(45.0, 50.0, 'coclear', []);
t_true($ondasBajoUmbral['V']['amp'] < CaseWaveforms::AMP_VISIBLE,
    'A 5 dB bajo el umbral cargado, la onda V ya no es visible');

// --- ABR: SN10, VII, efecto de tasa y ruido de fondo -------------------
//
// SN10 (el valle que sigue a la V, contra el que se mide su amplitud
// pico-a-valle) y VII (el bump tardío chico): geometría derivada de la V
// final, no ondas con crecimiento propio. `ondasClick()` las agrega solas
// y `trazo()` las suma igual que a cualquier otra -- no hay que tratarlas
// aparte en el llamador.
$ondasRef = CaseWaveforms::ondasClick(80.0, 45.0, 'transmission', [], [], 'adult_female');
t_true($ondasRef['SN10']['amp'] < 0, 'El SN10 es un valle: amplitud negativa');
t_close($ondasRef['SN10']['amp'], -$ondasRef['V']['amp'] * CaseWaveforms::SN10_AMP_RATIO, 0.001,
    'El SN10 es proporcional a la amplitud de V (45 % en contra)');
t_true($ondasRef['SN10']['lat'] > $ondasRef['V']['lat'], 'El SN10 va DESPUÉS de la V, no antes');
t_true($ondasRef['VII']['lat'] > $ondasRef['SN10']['lat'], 'El VII va después del SN10 (más tardío todavía)');
t_true($ondasRef['VII']['amp'] > 0, 'El VII es un bump: amplitud positiva');

// Efecto de tasa: a RATE_REF (la tasa a la que están medidos los valores
// normativos) no cambia nada; a una tasa alta la latencia crece y la
// amplitud cae, MÁS en un oído neural con sensibilidad "severa" que en
// uno normal a la misma tasa (fatiga de conducción).
$ondasTasaRef = CaseWaveforms::ondasClick(80.0, 45.0, 'transmission', [], [], 'adult_female', CaseWaveforms::RATE_REF);
t_eq($ondasTasaRef['V']['lat'], $ondasRef['V']['lat'], 'A RATE_REF el efecto de tasa es cero (es el ancla)');
$ondasTasaAlta = CaseWaveforms::ondasClick(80.0, 45.0, 'transmission', [], [], 'adult_female', CaseWaveforms::TASA_ESTRES);
t_true($ondasTasaAlta['V']['lat'] > $ondasRef['V']['lat'], 'A tasa alta la V se corre a mayor latencia');
t_true($ondasTasaAlta['V']['amp'] < $ondasRef['V']['amp'], 'A tasa alta la V pierde amplitud');
$corrimientoNormal = $ondasTasaAlta['V']['lat'] - $ondasRef['V']['lat'];
$caidaNormal = $ondasTasaAlta['V']['amp'] / $ondasRef['V']['amp'];

$ondasNeuralRef = CaseWaveforms::ondasClick(80.0, 45.0, 'neural', ['sensibilidad_tasa' => 'severa'], [], 'adult_female');
$ondasNeuralAlta = CaseWaveforms::ondasClick(80.0, 45.0, 'neural', ['sensibilidad_tasa' => 'severa'], [], 'adult_female', CaseWaveforms::TASA_ESTRES);
$corrimientoNeural = $ondasNeuralAlta['V']['lat'] - $ondasNeuralRef['V']['lat'];
$caidaNeural = $ondasNeuralAlta['V']['amp'] / $ondasNeuralRef['V']['amp'];
t_true($corrimientoNeural > $corrimientoNormal,
    'La fatiga por tasa alta corre más la V en un oído neural "severa" que en uno normal');
t_true($caidaNeural < $caidaNormal,
    'Y le cae más la amplitud, por la misma razón');

// El ruido de fondo es determinístico por semilla (mismo PDF, mismo
// resultado si se regenera) pero distinto entre semillas (las dos
// réplicas de un mismo nivel no salen pixel a pixel iguales).
$trazoA = CaseWaveforms::trazo($ondasRef, 12.0, 240, 111);
$trazoA2 = CaseWaveforms::trazo($ondasRef, 12.0, 240, 111);
$trazoB = CaseWaveforms::trazo($ondasRef, 12.0, 240, 222);
t_eq($trazoA, $trazoA2, 'Misma semilla, mismo ruido: el trazo con ruido es reproducible');
t_true($trazoA[10][1] !== $trazoB[10][1], 'Semillas distintas dan ruido distinto (no son la misma pasada)');
$trazoSinRuido = CaseWaveforms::trazo($ondasRef, 12.0, 240);
t_true(abs($trazoA[10][1] - $trazoSinRuido[10][1]) > 0.0001,
    'Con semilla, el trazo se aparta del limpio (hay ruido sumado)');
t_true(abs($trazoA[10][1] - $trazoSinRuido[10][1]) < 0.5,
    'Pero el ruido no tapa la señal: la diferencia es chica, del orden de RUIDO_AMPLITUD_UV');

// --- EstudioRedactor: la anamnesis de la ficha de estudio como prosa ---
//
// fuente() solo puede ver lo mismo que ya es seguro para el alumno: nunca
// un umbral, un tipo de patología, ni la disposición del generador. Se
// prueba contra el mismo fixture de todo el archivo.
$fuenteDemo = EstudioRedactor::fuente(ficha_caso_demo());
foreach (['umbral', 'disposicion', 'tipo', 'conciencia', 'confiabilidad', 'interrumpe'] as $clavePeligrosa) {
    t_true(
        strpos(strtolower(json_encode($fuenteDemo)), $clavePeligrosa) === false,
        "fuente() no incluye '{$clavePeligrosa}': nunca debe llegarle al LLM"
    );
}
t_eq($fuenteDemo['antecedentes_marcados'], ['Hipoacusia familiar'],
    'fuente() trae los antecedentes ya marcados, en texto, no las claves crudas');
t_true(strpos($fuenteDemo['acufeno'], 'Zumbido') !== false,
    'fuente() reusa CaseSheetPdf::acufeno(), no reimplementa la frase');

// hash() es estable para los mismos datos y cambia si algo relevante
// cambió -- así es como ensureFresh() sabe cuándo la redacción guardada
// quedó vieja.
t_eq(EstudioRedactor::hash($fuenteDemo), EstudioRedactor::hash($fuenteDemo),
    'hash() es determinístico para los mismos datos');
$fuenteEditada = $fuenteDemo;
$fuenteEditada['medicamentos'] = 'Ibuprofeno';
t_true(EstudioRedactor::hash($fuenteDemo) !== EstudioRedactor::hash($fuenteEditada),
    'hash() cambia si el docente edita un hecho de la anamnesis');

// parse(): mismo pelado de ``` que AnamnesisDraft, y el tope de caracteres.
t_eq(EstudioRedactor::parse('{"texto": "Un párrafo."}'), 'Un párrafo.',
    'parse() lee el texto de un JSON limpio');
t_eq(EstudioRedactor::parse("```json\n{\"texto\": \"Un párrafo.\"}\n```"), 'Un párrafo.',
    'parse() pela el ``` si el modelo lo agregó pese a la instrucción');
t_eq(EstudioRedactor::parse('{"texto": ""}'), null, 'parse() de un texto vacío es null, no un string vacío');
t_eq(EstudioRedactor::parse('no es json'), null, 'parse() de algo que no es JSON es null, no un error');
t_eq(mb_strlen((string) EstudioRedactor::parse('{"texto": "' . str_repeat('a', 5000) . '"}')), EstudioRedactor::MAX_TEXTO,
    'parse() recorta a MAX_TEXTO, un modelo suelto no puede llenar la ficha');

// El render: con redacción guardada, la ficha de estudio la muestra como
// prosa y ESCONDE el detalle mecánico (Historia/campos, Quiénes vienen a
// la consulta); sin ella, cae al detalle mecánico de siempre. La ficha
// docente nunca usa la redacción -- sigue con el detalle completo, tenga
// o no una redacción guardada el caso.
$dataConRedaccion = ficha_caso_demo();
$dataConRedaccion['EstudioRedaccion']['clinica'] = [
    'texto' => "Paciente adulta que consulta por síntomas auditivos.\n\nRefiere antecedente de hipoacusia familiar.",
    'hash' => EstudioRedactor::hash($fuenteDemo),
    'generado_en' => '2026-09-15 10:00:00',
];
$patientDemo = ['nombre' => 'Ana', 'apellido' => 'Pérez', 'rut' => '11.111.111-1'];
$pdfConRedaccion = CaseSheetPdf::build('CASO-TEST', $dataConRedaccion, $patientDemo, 'Docente', '10-09-2026', true);
t_true(strpos($pdfConRedaccion, 'Paciente adulta que consulta') !== false,
    'Con redacción guardada, la ficha de estudio muestra la prosa');
t_true(strpos($pdfConRedaccion, 'Historia cl') !== false,
    'Con redacción guardada, el subtítulo pasa a "Historia clínica" (prosa, no campos)');
t_true(strpos($pdfConRedaccion, 'Ninguno marcado') === false,
    'Con redacción guardada, no aparece el detalle mecánico de antecedentes');

$pdfSinRedaccion = CaseSheetPdf::build('CASO-TEST', ficha_caso_demo(), $patientDemo, 'Docente', '10-09-2026', true);
t_true(strpos($pdfSinRedaccion, 'Paciente adulta que consulta') === false,
    'Sin redacción guardada, no aparece un texto que nadie generó');
t_true(strpos($pdfSinRedaccion, 'Zumbido') !== false,
    'Sin redacción guardada, la ficha de estudio cae al detalle mecánico de siempre');

$pdfDocenteConRedaccion = CaseSheetPdf::build('CASO-TEST', $dataConRedaccion, $patientDemo, 'Docente', '10-09-2026', false);
t_true(strpos($pdfDocenteConRedaccion, 'Paciente adulta que consulta') === false,
    'La ficha DOCENTE nunca usa la redacción de IA, aunque el caso ya tenga una guardada');

// ensureFresh(): si el hash no coincide (el caso cambió) pero el LLM no
// está configurado o falla, no rompe nada y se queda con el texto viejo
// -- nunca deja la ficha sin nada por un problema de red.
$dataDesactualizada = ficha_caso_demo();
$dataDesactualizada['EstudioRedaccion']['clinica'] = [
    'texto' => 'Texto viejo, de antes de la última edición del caso.',
    'hash' => 'un-hash-que-ya-no-coincide',
    'generado_en' => '2020-01-01 00:00:00',
];
$resultado = EstudioRedactor::ensureFresh('CASO-TEST', $dataDesactualizada, 1);
t_eq($resultado['EstudioRedaccion']['clinica']['texto'], 'Texto viejo, de antes de la última edición del caso.',
    'ensureFresh() no borra el texto viejo si no puede regenerar (sin LLM configurado en los tests)');

// --- Audiograma: la vía ósea normal se esconde en la ficha de estudio ---
//
// En un examen real no se prueba vía ósea en una frecuencia con audición
// normal (no hay nada que diferenciar). La ficha docente sigue mostrando
// el perfil completo del generador; la de estudio no.
$aereaOiConNormales = [10.0, 15.0, 20.0, 25.0, 40.0, 50.0, 55.0, 60.0, 60.0];
$freqs = CaseBuilder::FREQUENCIES;
t_eq(
    array_values(CaseCharts::freqsOseaVisibles($freqs, $aereaOiConNormales, false)),
    [250, 500, 1000, 2000, 3000, 4000],
    'Ficha docente: la vía ósea se muestra completa (FREQS_OSEA), sea normal o no el aéreo'
);
t_eq(
    array_values(CaseCharts::freqsOseaVisibles($freqs, $aereaOiConNormales, true)),
    [1000, 2000, 3000, 4000],
    'Ficha de estudio: se esconden 250 y 500 Hz, donde el aéreo (15 y 20) está en rango normal (<=20)'
);
// El límite es inclusive: exactamente 20 dB (el borde de lo normal) ya se
// esconde, no hace falta que sea peor.
t_true(
    !in_array(500, CaseCharts::freqsOseaVisibles($freqs, $aereaOiConNormales, true), true),
    'A exactamente 20 dB (el límite de lo normal) la vía ósea también se esconde'
);

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
// Las letras tienen que separarse por los NÚMEROS que informa la ficha, no
// sólo por el dibujo: As y Cs son las rígidas (compliance bajo lo normal) y
// no pueden sortear en el mismo rango que A y C, o la ficha imprime una
// compliance normal debajo del rótulo "rígida".
foreach (['As' => 'A', 'Cs' => 'C'] as $rigida => $normal) {
    $vR = CaseCharts::valoresTimpanograma($rigida);
    $vN = CaseCharts::valoresTimpanograma($normal);
    t_true($vR['c_max'] <= 0.3,
        "Timpanograma {$rigida}: la compliance informada es la de un oído rígido (<= 0,3 mL)");
    t_true($vR['c_max'] <= $vN['c_min'],
        "Timpanograma {$rigida}: su compliance no se solapa con la de {$normal}");
}
// Y el pico de las C tiene que quedar DENTRO de la ventana de barrido: en
// -400 daPa cae sobre el borde y no hay pico que leer.
foreach (['C', 'Cs'] as $tipo) {
    $v = CaseCharts::valoresTimpanograma($tipo);
    t_true($v['p_max'] < -100.0, "Timpanograma {$tipo}: el pico queda en presión negativa franca");
    t_true($v['p_min'] > -400.0, "Timpanograma {$tipo}: el pico no se va al borde de la ventana");
}

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

// La escala del eje es fija: los dos oídos y todas las fichas se leen igual.
t_eq(CaseCharts::ESCALA_TIMPANOGRAMA_ML, 2.0, 'El timpanograma se dibuja siempre de 0 a 2 mL');

// Dos gradientes, y las dos con la cuenta del equipo (Z.move): altura a +-50
// daPa del pico sobre la altura del pico, entre 0 y 1. Ojo con el sentido:
// 1 es una curva ANCHA y 0 una en punta, al revés de la gradiente clásica.
//  - 'gradiente' sale de la curva IMPRESA (ápice en punta).
//  - 'gradiente_equipo' sale de la curva de la app (coseno alzado). Es la
//    que va a leer el alumno en pantalla y la ficha tiene que anticiparla.
// Las dos tienen que DISTINGUIR las letras: mientras el ancho de la app fue
// fijo, la del equipo daba 0,85 en cualquier curva con pico y no informaba
// nada.
foreach (CaseBuilder::Z_OPTIONS as $tipo) {
    $v = CaseCharts::valoresTimpanograma($tipo);
    foreach (['gradiente', 'gradiente_equipo'] as $clave) {
        t_true($v[$clave] >= 0.0 && $v[$clave] <= 1.0,
            "Timpanograma {$tipo}: la {$clave} queda entre 0 y 1");
    }
}
$conPico = array_values(array_filter(CaseBuilder::Z_OPTIONS, static function (string $tipo): bool {
    return !CaseCharts::valoresTimpanograma($tipo)['plana'];
}));
foreach (['gradiente', 'gradiente_equipo'] as $clave) {
    $valores = [];
    foreach ($conPico as $tipo) {
        $valores[] = CaseCharts::valoresTimpanograma($tipo)[$clave];
    }
    t_true(count(array_unique($valores)) > 1,
        "La {$clave} no es el mismo número en todas las letras");
    // Cs es la redondeada --retracción con efusión incipiente-- y Ad la más
    // en punta: es el orden que tiene que salir de la cuenta, sin listarlo.
    t_true(CaseCharts::valoresTimpanograma('Cs')[$clave] > CaseCharts::valoresTimpanograma('A')[$clave],
        "Timpanograma Cs: la {$clave} delata una curva más redondeada que la A");
    t_true(CaseCharts::valoresTimpanograma('Ad')[$clave] < CaseCharts::valoresTimpanograma('A')[$clave],
        "Timpanograma Ad: la {$clave} delata una curva más en punta que la A");
}
t_eq(CaseCharts::gradienteTimpanograma(0.0, 0.0, 80.0), 0.0, 'Sin compliance no hay gradiente que calcular');
// Un TW de adulto normal (50 a 110 daPa) para las curvas con pico normal:
// con los 200 daPa fijos de antes ninguna caía en ese rango.
foreach (['A', 'As', 'Ad'] as $tipo) {
    $tw = CaseCharts::ANCHOS_APP_TIMPANOGRAMA[$tipo];
    t_true($tw >= 50.0 && $tw <= 110.0, "Timpanograma {$tipo}: el ancho es el de un adulto (TW 50-110 daPa)");
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

// --- Ficha de estudio: mismos exámenes, sin la respuesta del caso ------
//
// build(..., estudio: true) es el mismo documento para el alumno: entran
// los mismos gráficos y números que mide un examen real, pero no el perfil
// auditivo ni los mandos con los que el generador arma el caso -- eso es
// la solución, y es justo lo que el alumno tiene que deducir.
$pdfEstudio = CaseSheetPdf::build(
    'CASO-TEST',
    ficha_caso_demo(),
    ['nombre' => 'Ana', 'apellido' => 'Pérez', 'rut' => '11.111.111-1'],
    'Docente',
    '10-09-2026',
    true
);

t_true(strpos($pdfEstudio, '%PDF-1.4') === 0, 'La ficha de estudio sale como un PDF');
t_true(strpos($pdfEstudio, 'Ficha de estudio') !== false, 'La portada dice que es la ficha de estudio');

// Lo que sigue siendo un examen real: se queda.
foreach ([
    'Audiometr', 'Acumetr', 'Impedanciometr', 'Logoaudiometr', 'supraliminares',
    'ABR', 'OEA', 'VEMP', 'Otoscopia', 'Interpico I-V', 'OD emis.', 'OD S/R',
] as $seccion) {
    t_true(strpos($pdfEstudio, $seccion) !== false, "La ficha de estudio conserva '{$seccion}'");
}

// Lo que es la respuesta del caso o un mando del generador: no va. Los
// needles evitan tildes -- MiniPdf reescribe el texto a WinAnsi/cp1252 y esos
// bytes no coinciden con el literal UTF-8 de este archivo, así que una
// palabra acentuada nunca matchea y la comprobación de ausencia sería un
// falso positivo (ver 'Compliance est' más abajo, mismo motivo al revés).
foreach ([
    'Perfil auditivo' => 'el perfil auditivo (la solución del caso)',
    'retrococlear' => 'la tabla ni el aviso de patrón retrococlear',
    'Captura y FSP' => 'los mandos de captura y FSP del ABR',
    'Perfil del o' => 'el perfil de configuración de la OEA',
    'del perfil (dB)' => 'la caída del perfil de la OEA',
    'Disposici' => 'la disposición del paciente (mando del generador)',
    'sin decidir' => 'el aviso de fichas sin decidir (es para el docente)',
    'Gradiente en el equipo' => 'la gradiente recalculada del equipo',
    'Morfolog' => 'la morfología de los reflejos (es un hallazgo, no un dato de lectura)',
    'sortea el equipo' => 'la explicación de cómo el generador sortea compliance y presión',
    'Rollover' => 'el veredicto de rollover (ya se ve en los niveles de UMD que bajan)',
    'Lateraliza' => 'el veredicto de lateralización del Weber (la flecha ya lo dice)',
    'Funci' => 'la fila de función tubaria (veredicto cargado a mano)',
    'reconstruido' => 'la explicación de que el trazo del ABR es una reconstrucción sin ruido',
] as $ausente => $motivo) {
    t_true(strpos($pdfEstudio, $ausente) === false, "La ficha de estudio NO trae {$motivo}");
}

// El Weber sigue con su flecha (símbolo) en las dos versiones -- lo que se
// saca es solo el texto "Lateraliza a OD/OI" al lado.
t_true(strpos($pdfDemo, 'Lateraliza a OD') !== false, 'La ficha docente sí dice a dónde lateraliza el Weber');
t_true(strpos($pdfEstudio, 'Weber') !== false, 'La ficha de estudio sigue trayendo el bloque de Weber (solo sin el veredicto)');

// El rollover de OI queda igual visible -- en los propios niveles de UMD,
// que bajan pasado el máximo -- solo que sin el veredicto explícito.
t_true(strpos($pdfDemo, 'Rollover') !== false, 'La ficha docente sí trae el veredicto de rollover');
foreach (['64 %', '76 %', '80 %', '79 %'] as $pctOi) {
    t_true(strpos($pdfEstudio, $pctOi) !== false,
        "La ficha de estudio conserva {$pctOi} en la ventana de UMD de OI (ahí se ve la caída)");
}

// La letra de Jerger NO es una respuesta escondida -- se lee directo de la
// curva del timpanograma y de hecho se imprime encima de ella -- así que la
// ficha de estudio la trae igual que la del docente: en la tabla y sobre
// el gráfico (OD arriba a la izquierda en rojo, OI arriba a la derecha en
// azul, con margen).
t_true(strpos($pdfEstudio, 'Jerger') !== false, 'La ficha de estudio trae la fila con la letra de Jerger');
t_true(substr_count($pdfEstudio, 'As') >= 2,
    'La letra de Jerger va sobre el timpanograma y en la tabla también en la ficha de estudio');

// El rótulo "LDL:" del audiograma tampoco es una respuesta -- identifica la
// línea de guiones sobre el gráfico mismo, en la celda de 125 Hz que no
// tiene datos -- así que va en las dos versiones.
t_true(strpos($pdfDemo, 'LDL:') !== false, 'El audiograma trae el rótulo LDL: sobre el gráfico');
t_true(strpos($pdfEstudio, 'LDL:') !== false, 'La ficha de estudio también trae el rótulo LDL: sobre el gráfico');

// El enmascaramiento SÍ es la cuenta hecha (rango mín-máx de ruido útil por
// frecuencia): en la ficha de estudio el alumno lo decide en la cabina, no
// lo lee de una tabla. Y el aviso de que "el motor lo infiere" es mecánica
// del software, no algo que vaya en la ficha del alumno.
t_true(strpos($pdfDemo, 'Enmascaramiento') !== false, 'La ficha docente trae la tabla de enmascaramiento');
t_true(strpos($pdfDemo, 'infiere el motor') !== false,
    'La ficha docente trae el aviso de que el enmascaramiento lo infiere el motor');
t_true(strpos($pdfEstudio, 'Enmascaramiento') === false,
    'La ficha de estudio NO trae la tabla de enmascaramiento (es la cuenta ya hecha)');
t_true(strpos($pdfEstudio, 'infiere el motor') === false,
    'La ficha de estudio NO trae el aviso de mecánica del enmascaramiento');

// La compliance y la presión del timpanograma: en la ficha del docente son
// un RANGO (la app sortea el valor real dentro de él); en la de estudio, un
// único número -- el mismo centro que usa la curva -- como leería el
// alumno la pantalla de un equipo real.
t_true(strpos($pdfDemo, 'daPa') !== false, 'La ficha docente informa la presión del pico');
// "estática" lleva tilde: MiniPdf reescribe el texto a WinAnsi y el byte no
// coincide con el UTF-8 del literal PHP, así que se busca sin ella (mismo
// truco que ya usan las demás secciones, ver 'Audiometr'/'Impedanciometr').
t_true(strpos($pdfEstudio, 'Compliance est') !== false,
    'La ficha de estudio sigue trayendo la fila de compliance estática');
t_true(strpos($pdfEstudio, 'daPa') !== false, 'La ficha de estudio sigue trayendo la presión del pico');

$vOdDemo = CaseCharts::valoresTimpanograma((string) ficha_caso_demo()['Z_OD']);
t_true(
    strpos($pdfEstudio, number_format($vOdDemo['estatica'], 2) . ' mL') !== false,
    'La compliance de la ficha de estudio es el centro del rango (el mismo que dibuja la curva), no el rango'
);
t_true(
    strpos($pdfEstudio, number_format($vOdDemo['c_min'], 2) . ' a ' . number_format($vOdDemo['c_max'], 2) . ' mL') === false,
    'La ficha de estudio no trae el rango de compliance del generador'
);

// --- La hoja de tamizaje (AABR + TEOAE) -----------------------------------

// Va después de las OEA: es la otra mitad del mismo turno y se lee con los
// dos resultados a la vista. Y no es una prueba más del informe -- dice qué
// tiene que contestar el equipo en este paciente y POR QUÉ, que es lo que
// separa un rescreening de una derivación.
t_true(strpos($pdfDemo, 'Tamizaje automatizado') !== false,
    'La ficha trae la hoja de tamizaje');
t_true(strpos($pdfDemo, 'CE-Chirp') !== false,
    'Y dice con qué estímulo y a qué nivel tamiza el equipo');

// El caso demo es una mixta de 45 dB en OD: por encima del nivel de
// tamizaje, así que el equipo refiere. Si esto se cayera, la hoja estaría
// informando lo contrario de lo que el alumno va a ver en el módulo AABR.
t_true(strpos($pdfDemo, 'REFIERE') !== false,
    'Un oído con umbral sobre el nivel de tamizaje sale como REFIERE');

// Recién nacido: el transitorio de las primeras horas entra en la hoja, y
// con él la diferencia entre "rescreening" y "derivar".
$fichaBebe = ficha_caso_demo();
$fichaBebe['edad'] = 0;
$fichaBebe['edad_horas'] = 8;
$fichaBebe['nacimiento'] = ['percentil' => ['OD' => 0.9, 'OI' => 0.9],
    'semanas' => 30, 'peso_g' => 1150, 'pretermino' => true,
    'muy_bajo_peso' => true, 'torch' => 'cmv'];
$pdfBebe = CaseSheetPdf::build('CASO-RN', $fichaBebe,
    ['nombre' => 'Bebé', 'apellido' => 'Prueba', 'rut' => '1-9'], 'Docente', '21-09-2026');
t_true(strpos($pdfBebe, 'Screening neonatal esperado') !== false,
    'En un recién nacido la hoja trae el tamizaje esperado por franja horaria');
t_true(strpos($pdfBebe, 'prematuro de 30 semanas') !== false,
    'Y las circunstancias que lo mueven');
t_true(strpos($pdfBebe, 'Citomegalovirus') !== false,
    'Y los indicadores de riesgo, que no lo mueven pero obligan a seguimiento');
