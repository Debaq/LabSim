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
t_eq($rangoCompliance, [0.0, 2.5], 'El timpanograma va de 0 a 2.5 mL en los dos lados');

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
