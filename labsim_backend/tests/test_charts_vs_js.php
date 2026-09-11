<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseCharts.php';

/**
 * El PDF y el editor dibujan lo mismo en dos lenguajes.
 *
 * `CaseCharts` (PHP, para el PDF) y `public/js/case/*.js` (para el editor)
 * tienen que usar las MISMAS escalas, las mismas campanas del timpanograma y
 * las mismas reglas de enmascaramiento. Unificarlos de verdad implicaría
 * reescribir el dibujo del editor --que hoy funciona-- para que lea las
 * constantes desde PHP, y no vale el riesgo; lo que sí se puede es que
 * ninguna de las dos copias se mueva sin la otra.
 *
 * Por eso este test LEE el JavaScript y compara los números con los del PHP.
 * Es feo y es a propósito: el día que alguien cambie una convención clínica
 * en un solo lado, falla acá y no en el aula.
 */

function js_fuente(string $archivo): string
{
    $ruta = dirname(__DIR__) . '/public/js/case/' . $archivo;
    $codigo = @file_get_contents($ruta);
    t_true(is_string($codigo) && $codigo !== '', "Se puede leer public/js/case/{$archivo}");
    return (string) $codigo;
}

/**
 * Números de los grupos capturados por $patron, en orden. Sirve tanto para
 * un literal de array ("[35, 40, 40]", un solo grupo) como para un par de
 * límites ("Math.max(0, Math.min(2.5, c))", dos grupos).
 */
function js_numeros(string $codigo, string $patron, string $que): array
{
    if (preg_match($patron, $codigo, $m) !== 1) {
        t_true(false, "Se encuentra {$que} en el JS");
        return [];
    }
    preg_match_all('/-?\d+(?:\.\d+)?/', implode(' ', array_slice($m, 1)), $nums);
    return array_map('floatval', $nums[0]);
}

// --- Enmascaramiento (audiogram.js) -------------------------------------

$audiogramJs = js_fuente('audiogram.js');

t_eq(
    js_numeros($audiogramJs, '/AIR_ATTENUATION_BY_FREQ\s*=\s*\[([^\]]*)\]/', 'la tabla de atenuación interaural'),
    array_map('floatval', CaseCharts::ATENUACION_AEREA_POR_FREQ),
    'La atenuación interaural por frecuencia es la misma en el PDF y en el editor'
);

$boneGap = js_numeros($audiogramJs, '/BONE_MASKING_GAP\s*=\s*(\d+)/', 'el gap que enmascara la ósea');
t_eq($boneGap[0] ?? null, (float) CaseCharts::GAP_ENMASCARA_OSEA,
    'El gap desde el que la ósea se enmascara es el mismo en los dos lados');

// La escala del audiograma: -10..120 dB sobre 130 de recorrido. Si el editor
// cambia el rango y el PDF no, el mismo umbral cae en otra altura.
$escala = js_numeros($audiogramJs, '/db = Math\.max\((-?\d+), Math\.min\((\d+), db\)\)/', 'el recorte de dB del audiograma');
t_eq($escala, [-10.0, 120.0], 'El audiograma del editor va de -10 a 120 dB HL, igual que el del PDF');

// --- Trazos de las líneas (audiogram.js) --------------------------------
//
// La ósea va unida con puntos y el LDL con guiones más largos: si los dos
// patrones se parecen, el alumno lee una curva por otra.

function js_trazo(string $codigo, string $constante): array
{
    if (preg_match('/' . $constante . "\s*=\s*'([\d.,]+)'/", $codigo, $m) !== 1) {
        t_true(false, "Se encuentra {$constante} en audiogram.js");
        return [];
    }
    return array_map('floatval', explode(',', $m[1]));
}

t_eq(js_trazo($audiogramJs, 'BONE_DASH'), array_map('floatval', CaseCharts::TRAZO_OSEA),
    'La ósea se une con el mismo punteado en el editor y en el PDF');
t_eq(js_trazo($audiogramJs, 'LDL_DASH'), array_map('floatval', CaseCharts::TRAZO_LDL),
    'El LDL usa el mismo trazo en el editor y en el PDF');
t_true(CaseCharts::TRAZO_OSEA[0] < CaseCharts::TRAZO_LDL[0],
    'El punteado de la ósea es más corto que el del LDL: son dos líneas distintas, no la misma');
t_eq(js_numeros($audiogramJs, '/BONE_FREQS\s*=\s*\[([^\]]*)\]/', 'las frecuencias con vía ósea'),
    array_map('floatval', CaseCharts::FREQS_OSEA),
    'La vía ósea y el LDL se dibujan en las mismas frecuencias en el editor y en el PDF');
t_true(
    preg_match('/drawLine\(oseaOd,.*BONE_DASH, true\);/', $audiogramJs) === 1
    && preg_match('/drawLine\(oseaOi,.*BONE_DASH, true\);/', $audiogramJs) === 1,
    'El editor une los puntos de la vía ósea de los dos oídos'
);

// --- Límite de normalidad -----------------------------------------------
//
// 20 dB HL: la audición normal en Chile llega hasta ahí inclusive, y por eso
// el grado leve arranca en 21. El número vive en CaseProfile::GRADES; acá se
// comprueba que la línea gruesa del audiograma siga apuntando al mismo lugar.

require_once __DIR__ . '/../src/CaseProfile.php';

t_eq(CaseCharts::LIMITE_NORMALIDAD_DB, CaseProfile::GRADES['leve']['rango'][0] - 1,
    'La línea gruesa del audiograma marca donde termina la audición normal (GRADES)');

$audiometriaPhp = (string) @file_get_contents(dirname(__DIR__) . '/views/case/_audiometria.php');
t_true($audiometriaPhp !== '', 'Se puede leer la ficha de audiometría del editor');
t_true(
    strpos($audiometriaPhp, "GRADES['leve']['rango'][0] - 1") !== false,
    'El editor saca el límite de normalidad de GRADES, no de un 20 escrito a mano'
);

// --- Campanas del timpanograma (tympanogram.js) -------------------------

$tympJs = js_fuente('tympanogram.js');
foreach (CaseCharts::FORMAS_TIMPANOGRAMA as $tipo => $forma) {
    $enJs = js_numeros($tympJs, '/\b' . preg_quote($tipo, '/') . ':\s*\[([^\]]*)\]/', "la campana del tipo {$tipo}");
    t_eq($enJs, array_map('floatval', $forma),
        "Timpanograma {$tipo}: la campana del editor y la del PDF son la misma");
}

$rangoPresion = js_numeros($tympJs, '/p = Math\.max\((-?\d+), Math\.min\((\d+), p\)\)/', 'el rango de presión');
t_eq($rangoPresion, [-400.0, 200.0], 'El timpanograma va de -400 a 200 daPa en los dos lados');

$rangoCompliance = js_numeros($tympJs, '/c = Math\.max\((\d+), Math\.min\((\d+(?:\.\d+)?), c\)\)/', 'el rango de compliance');
t_eq($rangoCompliance, [0.0, (float) CaseCharts::ESCALA_TIMPANOGRAMA_ML],
    'El timpanograma usa la misma escala fija de mL en el editor y en el PDF');

// El ápice va en punta en los dos lados: si uno vuelve a la gaussiana, la
// curva del editor deja de ser la del PDF.
t_true(preg_match('/Math\.exp\(-Math\.abs\(p - peakPos\) \/ width\)/', $tympJs) === 1,
    'El editor dibuja el timpanograma con el ápice en punta (exponencial de |distancia|)');

// --- Rollover del logoaudiograma (logogram.js) --------------------------

$logoJs = js_fuente('logogram.js');
t_true(
    preg_match('/umdPct\s*-\s*\(120\s*-\s*umdInt\)\s*\/\s*5\s*\*\s*5/', $logoJs) === 1,
    'El editor calcula el rollover como umdPct - (120 - umdInt)/5*5'
);
// Y el PHP tiene que dar exactamente ese número para el mismo caso.
$puntos = CaseCharts::logogramPoints(['sdt' => 30, 'srt' => 38, 'umd_int' => 60, 'umd_pct' => 90, 'recruit' => true]);
t_eq(end($puntos)[1], 90.0 - (120 - 60) / 5 * 5,
    'El PDF aplica la misma caída por reclutamiento que el editor');
