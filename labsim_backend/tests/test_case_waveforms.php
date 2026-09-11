<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseWaveforms.php';
require_once __DIR__ . '/../src/CaseOae.php';
require_once __DIR__ . '/../src/CaseMasking.php';

/**
 * Los trazos y las cuentas que el PDF reconstruye a partir del caso.
 *
 * Lo que se comprueba no es que el dibujo "se vea bien" --eso se mira-- sino
 * que la física siga siendo la del motor: que la onda I se pierda antes que
 * la V al bajar la intensidad, que un bloqueo proximal deje solo la I, que
 * una prolongación III-V corra la V y no la III, y que las constantes
 * copiadas de los JSON normativos no se hayan separado del original.
 */

$neutro = [
    'i_iii_ms' => 0.2, 'iii_v_ms' => 0.2, 'global_delay_ms' => 0.0,
    'bloqueo' => 'ninguno', 'v_i_factor' => 0.45,
    'microfonica' => 'normal', 'desincronia' => 'ninguna', 'sensibilidad_tasa' => 'severa',
];

// --- Función latencia-intensidad (espejo de ABR_generator) --------------

t_close(CaseWaveforms::corrimientoLatencia(80), 0.0, 0.001, 'A 80 dB la función L-I no corre nada: es la referencia');
t_close(CaseWaveforms::corrimientoLatencia(70), 0.12, 0.001, 'De 80 a 70 dB la V se corre 0.12 ms (tramo plano)');
t_close(CaseWaveforms::corrimientoLatencia(50), 0.72, 0.001, 'Bajo 70 dB la pendiente es 0.3 ms/10 dB (Hood)');
t_true(CaseWaveforms::corrimientoLatencia(30) > CaseWaveforms::corrimientoLatencia(60),
    'Cuanto más cerca del umbral, más tarde aparece la onda');

// --- La onda I se pierde primero ---------------------------------------

$alto = CaseWaveforms::ondasClick(80, 10, 'normal', $neutro);
$bajo = CaseWaveforms::ondasClick(30, 10, 'normal', $neutro);
t_true($alto['I']['amp'] > CaseWaveforms::AMP_VISIBLE, 'A 80 dB sobre un umbral de 10 se ve la onda I');
t_true($bajo['I']['amp'] < $bajo['V']['amp'],
    'Cerca del umbral la I ya no se ve y la V sí: es el orden en que se pierden');
t_true($bajo['V']['lat'] > $alto['V']['lat'], 'La V se corre a la derecha al bajar la intensidad');

// Sin nivel de sensación no hay respuesta: no se puede dibujar una onda
// por debajo del umbral del oído.
$enUmbral = CaseWaveforms::ondasClick(10, 10, 'normal', $neutro);
t_true($enUmbral['I']['amp'] < CaseWaveforms::AMP_VISIBLE, 'En el umbral mismo no queda onda I');

// --- El patrón retrococlear mueve lo que dice mover ---------------------

// El patrón retrococlear solo corre en un oído neural: con los defaults
// cargados, un oído normal no puede salir con las ondas movidas.
$neuralBase = CaseWaveforms::ondasClick(80, 10, 'neural', $neutro);
$conIIIV = CaseWaveforms::ondasClick(80, 10, 'neural', ['iii_v_ms' => 1.0] + $neutro);
t_close($conIIIV['III']['lat'], $neuralBase['III']['lat'], 0.001,
    'Una prolongación III-V no mueve la onda III');
t_close($conIIIV['V']['lat'] - $neuralBase['V']['lat'], 0.8, 0.001,
    'Y corre la V lo que diga el parámetro (1.0 contra el default 0.2)');

$conIIII = CaseWaveforms::ondasClick(80, 10, 'neural', ['i_iii_ms' => 1.0] + $neutro);
t_close($conIIII['I']['lat'], $neuralBase['I']['lat'], 0.001, 'Una prolongación I-III no mueve la onda I');
t_true($conIIII['III']['lat'] > $neuralBase['III']['lat'], 'Pero sí la III');

$global = CaseWaveforms::ondasClick(80, 10, 'neural', ['global_delay_ms' => 0.5] + $neutro);
t_close($global['I']['lat'] - $neuralBase['I']['lat'], 0.5, 0.001,
    'El retraso global corre TODO, onda I incluida: es lo que lo distingue');

// Y en un oído que NO es neural, esos mismos parámetros no hacen nada.
$normalConRetro = CaseWaveforms::ondasClick(80, 10, 'normal', ['iii_v_ms' => 1.0, 'v_i_factor' => 0.2] + $neutro);
t_close($normalConRetro['V']['lat'], $alto['V']['lat'], 0.001,
    'Un oído normal ignora el patrón retrococlear que quedó cargado');
t_close($normalConRetro['V']['amp'], $alto['V']['amp'], 0.001,
    'y conserva la amplitud de su onda V');

$proximal = CaseWaveforms::ondasClick(80, 10, 'neural', ['bloqueo' => 'post_i'] + $neutro);
t_true($proximal['I']['amp'] > CaseWaveforms::AMP_VISIBLE, 'El bloqueo proximal deja la onda I');
t_true($proximal['V']['amp'] < CaseWaveforms::AMP_VISIBLE, 'Y no deja nada después');

$total = CaseWaveforms::ondasClick(80, 10, 'neural', ['bloqueo' => 'total'] + $neutro);
foreach (['I', 'III', 'V'] as $onda) {
    t_true($total[$onda]['amp'] < CaseWaveforms::AMP_VISIBLE, "Bloqueo total: la onda {$onda} no se ve");
}

$desinc = CaseWaveforms::ondasClick(80, 10, 'neural', ['desincronia' => 'alta'] + $neutro);
t_true($desinc['V']['sigma'] > $alto['V']['sigma'], 'La desincronía ensancha la onda');
t_true($desinc['V']['amp'] < $alto['V']['amp'], 'y la achata: por eso no se le puede marcar el pico');

// --- El trazo ----------------------------------------------------------

$trazo = CaseWaveforms::trazo($alto);
t_eq(count($trazo), 241, 'El trazo se muestrea de 0 a 12 ms');
t_close($trazo[0][0], 0.0, 0.001, 'Arranca en 0 ms');
t_close($trazo[240][0], 12.0, 0.001, 'Y termina en 12 ms');
$maxT = 0.0;
$maxV = -INF;
foreach ($trazo as [$t, $v]) {
    if ($v > $maxV) { $maxV = $v; $maxT = $t; }
}
t_close($maxT, $alto['V']['lat'], 0.3, 'El pico más alto del trazo cae donde está la onda V');

$serie = CaseWaveforms::serieIntensidades(45);
t_true(in_array(45.0, $serie, true), 'La serie de intensidades siempre incluye el umbral');
t_true(max($serie) <= 80.0, 'Y arranca en 80 dB nHL');

// --- Población normativa (espejo de select_population) ------------------

t_eq(CaseWaveforms::poblacion(0, 0), 'neonate', 'Un recién nacido usa la normativa de neonato');
t_eq(CaseWaveforms::poblacion(7, 0), 'child', 'Un niño de 7 usa la de niño');
t_eq(CaseWaveforms::poblacion(15, 1), 'child', 'A los 15 las latencias ya son casi de adulto, pero usa child');
t_eq(CaseWaveforms::poblacion(30, 0), 'adult_male', 'Adulto hombre');
t_eq(CaseWaveforms::poblacion(30, 1), 'adult_female', 'Adulta mujer');
t_eq(CaseWaveforms::poblacion(70, 1), 'elderly', 'Sobre 60 usa la normativa de adulto mayor');
t_eq(CaseWaveforms::poblacion(null, 0), 'adult_female', 'Sin edad cae en el default histórico');

// El neonato tiene TODO más tarde que el adulto: es el error clásico de
// leer un ABR de recién nacido con la banda de adulto.
t_true(CaseWaveforms::CLICK_BASE['neonate']['V'][0] > CaseWaveforms::CLICK_BASE['adult_female']['V'][0],
    'La onda V del neonato aparece más tarde que la del adulto');

// --- Rangos de normalidad (espejo de normative_limits) ------------------

$lim = CaseWaveforms::limitesNormativos('adult_female', 80.0);
foreach (['I', 'III', 'V'] as $onda) {
    [$lo, $hi] = $lim['lat'][$onda];
    $centro = CaseWaveforms::CLICK_BASE['adult_female'][$onda][0];
    t_close(($lo + $hi) / 2, $centro, 0.001, "Onda {$onda}: el rango normal está centrado en la latencia poblacional");
    t_close($hi - $lo, 2 * CaseWaveforms::NORM_SD_LIMITE * CaseWaveforms::NORM_SD_LAT[$onda], 0.001,
        "Onda {$onda}: el rango normal es la media +- 2 DE");
}
t_close(($lim['interpeak']['I-V'][0] + $lim['interpeak']['I-V'][1]) / 2,
    CaseWaveforms::CLICK_INTERPICOS['adult_female']['I-V'], 0.001,
    'El interpico I-V se centra en el valor normativo de la población');

// A menos intensidad la latencia normal es MÁS tardía: leer un ABR de 40 dB
// con la banda de 80 marcaría como alterado un oído sano.
$lim40 = CaseWaveforms::limitesNormativos('adult_female', 40.0);
t_true($lim40['lat']['V'][1] > $lim['lat']['V'][1],
    'El techo de la onda V se corre con la intensidad, como la curva');
t_close($lim40['interpeak']['I-V'][1], $lim['interpeak']['I-V'][1], 0.001,
    'Los interpicos NO dependen de la intensidad');

// El neonato tiene su propia banda: con la de adulto, todo neonato sano
// queda fuera de norma.
$limNeo = CaseWaveforms::limitesNormativos('neonate', 80.0);
t_true($limNeo['lat']['V'][1] > $lim['lat']['V'][1],
    'La banda del neonato va más tarde que la del adulto');

// --- VEMP ---------------------------------------------------------------

$vempAlto = CaseWaveforms::trazoVemp('CVEMP', 100, 60);
$vempUmbral = CaseWaveforms::trazoVemp('CVEMP', 60, 60);
$vempBajo = CaseWaveforms::trazoVemp('CVEMP', 50, 60);

$pp = static function (array $pts): float {
    $min = INF; $max = -INF;
    foreach ($pts as [, $v]) { $min = min($min, $v); $max = max($max, $v); }
    return $max - $min;
};
t_true($pp($vempAlto) > $pp($vempUmbral), 'El VEMP crece con la intensidad sobre el umbral');
t_close($pp($vempBajo), 0.0, 0.001, 'Por debajo del umbral no hay respuesta');

// El cVEMP arranca positivo (p13) y el oVEMP negativo (n10): invertir eso
// es confundir los dos exámenes.
$cv = CaseWaveforms::trazoVemp('CVEMP', 100, 60);
$ov = CaseWaveforms::trazoVemp('OVEMP', 100, 60);
$en = static function (array $pts, float $ms): float {
    $mejor = $pts[0];
    foreach ($pts as $pt) {
        if (abs($pt[0] - $ms) < abs($mejor[0] - $ms)) { $mejor = $pt; }
    }
    return $mejor[1];
};
t_true($en($cv, 13.0) > 0, 'El cVEMP tiene un pico POSITIVO en 13 ms');
t_true($en($ov, 10.0) < 0, 'El oVEMP tiene un pico NEGATIVO en 10 ms');

// --- OEA: las cuatro pruebas -------------------------------------------

$sano = CaseOae::pruebas(['type' => 'normal', 'umbral' => 10, 'desviaciones' => []]);
$muerto = CaseOae::pruebas(['type' => 'coclear', 'umbral' => 60, 'desviaciones' => []]);

foreach (['teoae', 'dpoae', 'sfoae'] as $prueba) {
    t_true(isset($sano[$prueba]['bandas']) && $sano[$prueba]['bandas'] !== [],
        "La prueba {$prueba} trae sus bandas");
    $pasanSano = 0;
    $pasanMuerto = 0;
    foreach ($sano[$prueba]['bandas'] as $hz => $banda) {
        $pasanSano += $banda['pasa'] ? 1 : 0;
        $pasanMuerto += $muerto[$prueba]['bandas'][$hz]['pasa'] ? 1 : 0;
        t_true(isset($sano[$prueba]['area'][$hz]),
            "{$prueba} {$hz} Hz: tiene área normal para comparar");
    }
    t_true($pasanSano > 0, "Un oído sano pasa alguna banda en {$prueba}");
    t_eq($pasanMuerto, 0, "Una coclear de 60 dB no deja emisión en {$prueba}");
}

// Las tres pruebas usan bandas DISTINTAS: ese es el motivo de separarlas.
t_true(array_keys($sano['teoae']['bandas']) !== array_keys($sano['dpoae']['bandas']),
    'TEOAE y DP-grama no se miden en las mismas frecuencias');

// La atenuación se interpola en log de frecuencia entre las bandas del perfil.
$aten = [500 => 0.0, 1000 => 10.0, 2000 => 20.0];
t_close(CaseOae::atenuacionEn($aten, 1000), 10.0, 0.001, 'En una banda exacta devuelve su valor');
t_close(CaseOae::atenuacionEn($aten, 1414), 15.0, 0.2, 'A media octava, la mitad del salto');
t_close(CaseOae::atenuacionEn($aten, 250), 0.0, 0.001, 'Por debajo de la primera banda, la primera');
t_close(CaseOae::atenuacionEn($aten, 8000), 20.0, 0.001, 'Por encima de la última, la última');

// --- Enmascaramiento (espejo de response.py / DebugMkg.py) -------------

// Oído derecho con 60 dB de pérdida aérea y ósea normal (conductiva), OI sano.
$aereaOd = array_fill(0, 9, 60.0);
$oseaOd = array_fill(0, 9, 5.0);
$aereaOi = array_fill(0, 9, 5.0);
$oseaOi = array_fill(0, 9, 5.0);

$via = CaseMasking::via('aerea', 2, $aereaOd, $oseaOd, $aereaOi, $oseaOi);
t_true($via['cruza'], 'Una conductiva de 60 dB cruza al oído sano: hay que enmascarar');
// mín = UAE - AI - UONE + UANE = 60 - 40 - 5 + 5
t_close($via['min'], 20.0, 0.001, 'El mínimo sale de la fórmula de la app');
// máx = UOE + AI = 5 + 40
t_close($via['max'], 45.0, 0.001, 'Y el máximo también');
t_true(!$via['dilema'], 'Con la ósea sana hay meseta de sobra');

// Dilema: conductiva bilateral grande -- el mínimo trepa y el máximo no.
$aereaBil = array_fill(0, 9, 65.0);
$oseaBil = array_fill(0, 9, 5.0);
$dilema = CaseMasking::via('aerea', 2, $aereaBil, $oseaBil, $aereaBil, $oseaBil);
t_true($dilema['dilema'], 'Conductiva bilateral grande: no existe ruido que sirva (dilema)');

// La ósea siempre cruza: no hay atenuación interaural por vía ósea.
$osea = CaseMasking::via('osea', 2, $aereaOd, $oseaOd, $aereaOi, $oseaOi);
t_true($osea['cruza'], 'La vía ósea cruza siempre: por eso una ósea sin enmascarar no dice de qué oído es');

// Efecto oclusivo: solo en graves y solo si el oído ocluido no tiene gap.
t_close(CaseMasking::efectoOclusivo(2, $aereaOi, $oseaOi), 15.0, 0.001,
    'En 500 Hz un oído sano gana 15 dB al ocluirlo');
t_close(CaseMasking::efectoOclusivo(4, $aereaOi, $oseaOi), 0.0, 0.001,
    'En 2 kHz no hay efecto oclusivo');
t_close(CaseMasking::efectoOclusivo(2, $aereaOd, $oseaOd), 0.0, 0.001,
    'Un oído con gap ya se comporta como ocluido: no gana nada');
