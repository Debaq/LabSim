<?php

declare(strict_types=1);

/**
 * Pruebas que correspondían (AudiometriaPertinencia, T05) y enmascaramiento
 * (AudiometriaTecnica, T04). Registros armados a mano: presentaciones como
 * las deja AudiometriaRegistro::leer().
 */

require_once dirname(__DIR__) . '/src/AudiometriaTecnica.php';

/** Caso con la misma audición en todas las frecuencias: [aérea OD, OI], [ósea OD, OI]. */
function ap_caso(array $aerea, array $osea, ?array $stenger = null): array
{
    $a = array_fill(0, 15, $aerea);
    $o = array_fill(0, 15, $osea);
    $c = ['Aerea_mkg' => $a, 'Osea_mkg' => $o, 'Aerea' => $a, 'Osea' => $o];
    if ($stenger !== null) {
        $c['Stenger'] = $stenger;
    }
    return $c;
}

/** Una presentación como las de AudiometriaRegistro. */
function ap_pres(string $prueba, int $oido, int $hz, int $db, ?bool $oyo, ?string $instr, ?array $ruido = null, string $via = 'aerea'): array
{
    static $t = 0.0;
    $t += 3.0;
    return ['t_on' => $t, 't_off' => $t + 1.5, 'duracion' => 1.5, 'canal' => 0, 'oido' => $oido, 'via' => $via,
        'freq' => $hz, 'int' => $db, 'ruido' => $ruido, 'instruccion' => $instr, 'prueba' => $prueba, 'oyo' => $oyo, 'ms' => true];
}

/** Búsqueda de umbral en $u con la técnica (cierra con 2 respuestas subiendo). */
function ap_umbral(string $prueba, int $oido, int $hz, int $u, string $instr, ?array $ruido = null, string $via = 'aerea'): array
{
    $out = [];
    foreach ([[10, true], [0, true], [-10, false], [-5, false], [0, true], [-10, false], [-5, false], [0, true]] as [$d, $oyo]) {
        $out[] = ap_pres($prueba, $oido, $hz, $u + $d, $oyo, $instr, $ruido, $via);
    }
    return $out;
}

/** Registro con umbrales aéreos de los dos oídos en 1 kHz más lo que se agregue. */
function ap_registro(array $caso, array $extra = [], array $pruebasExtra = []): array
{
    $pac = new AudiometriaPaciente($caso);
    $pres = array_merge(
        ap_umbral('aereos', 0, 1000, $pac->umbralSinRuido('aerea', 3, 0), 'colocar_fonos'),
        ap_umbral('aereos', 1, 1000, $pac->umbralSinRuido('aerea', 3, 1), 'colocar_fonos'),
        $extra
    );
    $pruebas = [[1.0, 'aereos']];
    foreach ($pruebasExtra as $p) {
        $pruebas[] = [99.0, $p];
    }
    return ['reconstruido' => false, 'con_ms' => true, 'presentaciones' => $pres, 'pruebas' => $pruebas, 'tinnitus' => []];
}

function ap_reglas(?array $s): array
{
    $out = [];
    foreach ($s['reglas'] ?? [] as $r) {
        $out[$r['texto']] = $r['cumple'];
    }
    return $out;
}

function ap_busca(array $reglas, string $fragmento)
{
    foreach ($reglas as $texto => $cumple) {
        if (strpos($texto, $fragmento) !== false) {
            return $cumple;
        }
    }
    return 'no está';
}

$apParams = AudiometriaTecnica::parametrosDefault();
$apEval = static function (array $caso, array $registro) use ($apParams): array {
    return AudiometriaTecnica::evaluar($registro, $caso, $apParams);
};

// --- Sensorioneural simétrica: Fowler sin oído de referencia ------------------
$sim = ap_caso([40, 40], [40, 40]);
$r = $apEval($sim, ap_registro($sim, [
    ap_pres('supra', 0, 1000, 60, null, 'dos_pitos'),
    ap_pres('supra', 1, 1000, 60, null, 'dos_pitos'),
    ap_pres('supra', 0, 2000, 60, null, 'cambie_de_volumen'),
]));
$rr = ap_reglas($r['pertinencia']);
t_eq(ap_busca($rr, 'El Fowler'), false, 'Pertinencia: Fowler en una simétrica no tiene oído de referencia');
t_eq(ap_busca($rr, 'logoaudiometría'), false, 'Pertinencia: toda audiometría lleva logo');
t_eq(ap_busca($rr, 'asimétrica'), 'no está', 'Pertinencia: simétrica no exige adaptación');
t_eq($r['pertinencia']['observaciones'], [], 'Pertinencia: SISI en una sensorioneural no es advertencia');
t_true(strpos($r['pertinencia']['reglas'][1]['detalle_docente'], 'OD 40, OI 40') !== false, 'Pertinencia: los números solo en el detalle docente');
t_true(strpos($r['pertinencia']['reglas'][1]['detalle'], '40') === false, 'Pertinencia: el detalle del alumno no lleva umbrales');

// --- Asimétrica sensorioneural: adaptación exigida, Fowler y Stenger válidos ------
$asim = ap_caso([10, 40], [10, 40]);
$sinAdapt = ap_reglas($apEval($asim, ap_registro($asim, [], ['logo']))['pertinencia']);
t_eq(ap_busca($sinAdapt, 'busca adaptación'), false, 'Pertinencia: asimétrica sin prueba de adaptación');
t_eq(ap_busca($sinAdapt, 'logoaudiometría'), true, 'Pertinencia: con logo cumple');
$r = $apEval($asim, ap_registro($asim, [
    ap_pres('supra', 1, 1000, 45, null, 'mano_levantada'),
    ap_pres('supra', 0, 1000, 20, null, 'dos_pitos'),
    ap_pres('supra', 1, 1000, 50, null, 'dos_pitos'),
    ap_pres('supra', 0, 1000, 20, null, 'colocar_fonos'),
    ap_pres('supra', 1, 1000, 30, null, 'colocar_fonos'),
], ['logo']));
$rr = ap_reglas($r['pertinencia']);
t_eq(ap_busca($rr, 'busca adaptación'), true, 'Pertinencia: Carhart cuenta como adaptación');
t_eq(ap_busca($rr, 'El Fowler'), true, 'Pertinencia: Fowler con oído normal y el otro 30 dB peor');
t_eq(ap_busca($rr, 'El Stenger'), true, 'Pertinencia: Stenger con 30 dB entre oídos');
t_eq(array_values(array_filter($r['pertinencia']['hechas'], static function ($h) { return $h === 'Stenger'; })), ['Stenger'], 'Pertinencia: el Stenger se reconoce por la instrucción de los aéreos');
t_eq(ap_busca($rr, 'Stenger.'), 'no está', 'Pertinencia: sin caso marcado no se exige Stenger');

// --- Conductiva: SISI no aporta, y la asimetría no pide adaptación ---------------
$cond = ap_caso([10, 40], [10, 5]);
$r = $apEval($cond, ap_registro($cond, [ap_pres('supra', 1, 1000, 60, null, 'cambie_de_volumen')], ['logo']));
t_eq(ap_busca(ap_reglas($r['pertinencia']), 'busca adaptación'), 'no está', 'Pertinencia: conductiva asimétrica no pide adaptación');
t_eq(count($r['pertinencia']['observaciones']), 1, 'Pertinencia: SISI en una conductiva es advertencia');
t_true(strpos($r['pertinencia']['observaciones'][0], 'SISI en OI 1 kHz') !== false, 'Pertinencia: la advertencia nombra oído y frecuencia');

// --- Stenger con oídos parejos ----------------------------------------------------
$r = $apEval($sim, ap_registro($sim, [
    ap_pres('supra', 0, 1000, 50, null, 'colocar_fonos'),
    ap_pres('supra', 1, 1000, 50, null, 'colocar_fonos'),
], ['logo']));
t_eq(ap_busca(ap_reglas($r['pertinencia']), 'El Stenger'), false, 'Pertinencia: Stenger con oídos parejos no dice nada');

// --- Caso marcado con pérdida no orgánica: el Stenger se exige --------------------
$fingido = ap_caso([10, 60], [10, 60], [false, true]);
$rr = ap_reglas($apEval($fingido, ap_registro($fingido, [], ['logo']))['pertinencia']);
t_eq(ap_busca($rr, 'se hace el Stenger'), false, 'Pertinencia: caso Stenger sin Stenger');
t_eq(ap_busca($rr, 'busca adaptación'), 'no está', 'Pertinencia: en la pérdida fingida no se exige adaptación');

// --- Reger: frecuencia conservada y otra 20 a 40 dB peor en el mismo oído ---------
$reger = ap_caso([10, 10], [10, 10]);
$reger['Aerea_mkg'][6] = [10, 40];
$reger['Osea_mkg'][6] = [10, 40];
$reger['Aerea'] = $reger['Aerea_mkg'];
$reger['Osea'] = $reger['Osea_mkg'];
$bien = ap_reglas($apEval($reger, ap_registro($reger, [
    ap_pres('supra', 1, 1000, 30, null, 'reger'),
    ap_pres('supra', 1, 4000, 60, null, 'reger'),
], ['logo']))['pertinencia']);
t_eq(ap_busca($bien, 'El Reger'), true, 'Pertinencia: Reger 1 kHz normal contra 4 kHz 30 dB peor');
$mal = ap_reglas($apEval($reger, ap_registro($reger, [
    ap_pres('supra', 1, 1000, 30, null, 'reger'),
    ap_pres('supra', 1, 2000, 30, null, 'reger'),
], ['logo']))['pertinencia']);
t_eq(ap_busca($mal, 'El Reger'), false, 'Pertinencia: Reger con dos frecuencias normales');

// --- Profunda bilateral: no se pide logo ---------------------------------------------
$prof = ap_caso([100, 100], [70, 70]);
t_eq(ap_busca(ap_reglas($apEval($prof, ap_registro($prof))['pertinencia']), 'logoaudiometría'), 'no está', 'Pertinencia: profunda bilateral no exige logo');

// --- Sin audiometría tonal no se exige nada ------------------------------------------
t_eq(AudiometriaPertinencia::evaluar(['presentaciones' => [], 'pruebas' => []], $sim, 20, false), null, 'Pertinencia: sin aéreos, nada');

// --- Asimetría: dos frecuencias seguidas ----------------------------------------------
$una = ap_caso([10, 10], [10, 10]);
$una['Aerea_mkg'][4] = [10, 40];
$una['Osea_mkg'][4] = [10, 40];
t_eq(AudiometriaPertinencia::asimetriaSensorioneural(new AudiometriaPaciente($una), 20), null, 'Pertinencia: una sola frecuencia no es asimetría');
$una['Aerea_mkg'][5] = [10, 40];
$una['Osea_mkg'][5] = [10, 40];
t_eq(AudiometriaPertinencia::asimetriaSensorioneural(new AudiometriaPaciente($una), 20), ['oido' => 1, 'freqs' => [2000, 3000]], 'Pertinencia: 2 y 3 kHz seguidas sí');

// --- Enmascaramiento ---------------------------------------------------------------------
// OD conductiva 50/0, OI normal 0/0: el aéreo de OD en 1 kHz cruza (40 + 0 < 50).
// Meseta con banda estrecha: mínimo 50-40-0+0 = 10, máximo 0+40 = 40.
$conductiva = ap_caso([50, 0], [0, 0]);
$base = static function (array $odAereo) use ($apParams, $conductiva): array {
    $reg = ['reconstruido' => false, 'con_ms' => true, 'pruebas' => [[1.0, 'aereos']], 'tinnitus' => [],
        'presentaciones' => array_merge($odAereo, ap_umbral('aereos', 1, 1000, 0, 'colocar_fonos'))];
    return AudiometriaTecnica::evaluar($reg, $conductiva, $apParams);
};
$ruido = static function (int $db): array {
    return ['int' => $db, 'stim' => 'Narrow Band Noise', 'oido' => 1];
};
$r = $base(ap_umbral('aereos', 0, 1000, 40, 'colocar_fonos'));
$m = ap_reglas($r['enmascaramiento']);
t_eq(ap_busca($m, 'cruza al otro oído'), false, 'Enmascaramiento: sombra sin ruido');
t_eq(ap_busca($m, 'meseta'), 'no está', 'Enmascaramiento: sin ruido no se evalúa la meseta');
$r = $base(ap_umbral('aereos', 0, 1000, 50, 'colocar_fonos', $ruido(30)));
$m = ap_reglas($r['enmascaramiento']);
t_eq(ap_busca($m, 'cruza al otro oído'), true, 'Enmascaramiento: con ruido en el otro oído');
t_eq(ap_busca($m, 'entre el mínimo'), true, 'Enmascaramiento: umbral real con ruido = meseta');
$r = $base(ap_umbral('aereos', 0, 1000, 40, 'colocar_fonos', $ruido(0)));
$m = ap_reglas($r['enmascaramiento']);
t_eq(ap_busca($m, 'entre el mínimo'), false, 'Enmascaramiento: ruido bajo el mínimo');
t_true(strpos($r['enmascaramiento']['reglas'][1]['detalle'], 'bajo el mínimo') !== false, 'Enmascaramiento: dice que quedó bajo');
t_eq($r['enmascaramiento']['reglas'][1]['detalle_docente'], 'OD 1 kHz: ruido 0 dB, meseta 10 a 40 dB', 'Enmascaramiento: números para el docente');
$r = $base(ap_umbral('aereos', 0, 1000, 60, 'colocar_fonos', $ruido(60)));
t_true(strpos(ap_reglas($r['enmascaramiento']) ? $r['enmascaramiento']['reglas'][1]['detalle'] : '', 'sobre el máximo') !== false, 'Enmascaramiento: ruido sobre el máximo');
// OI normal con ruido en OD: no cruzaba
$r = AudiometriaTecnica::evaluar(['reconstruido' => false, 'con_ms' => true, 'pruebas' => [[1.0, 'aereos']], 'tinnitus' => [],
    'presentaciones' => array_merge(ap_umbral('aereos', 0, 1000, 50, 'colocar_fonos', $ruido(30)),
        ap_umbral('aereos', 1, 1000, 0, 'colocar_fonos', ['int' => 30, 'stim' => 'Narrow Band Noise', 'oido' => 0]))],
    $conductiva, $apParams);
t_eq(count($r['enmascaramiento']['observaciones']), 1, 'Enmascaramiento: ruido donde no cruza es advertencia');
t_true(strpos($r['enmascaramiento']['observaciones'][0], 'OI 1 kHz') !== false, 'Enmascaramiento: la advertencia nombra oído y frecuencia');
// Simétrica: nada que enmascarar, no hay sección
t_eq($apEval($sim, ap_registro($sim))['enmascaramiento'], null, 'Enmascaramiento: simétrica sin ruido, sin sección');
// Las secciones nuevas suman al puntaje total
$r = $apEval($sim, ap_registro($sim));
t_eq($r['puntaje'], AudiometriaTecnica::sumar(array_values(array_filter([$r['orden'], $r['pertinencia'], $r['aereos'], $r['oseos'], $r['enmascaramiento'], $r['tinnitus']]))), 'Puntaje: suma todas las secciones');

// --- Puntería: sin verificar no se castiga dos veces ---------------------------------------
$sinVerificar = static function (int $oido, int $hz, int $u): array {
    $out = [];
    foreach ([[10, true], [0, true], [-10, false], [-5, false], [0, true]] as [$d, $oyo]) {
        $out[] = ap_pres('aereos', $oido, $hz, $u + $d, $oyo, 'colocar_fonos');
    }
    return $out;
};
$r = $apEval($sim, ['reconstruido' => false, 'con_ms' => true, 'pruebas' => [[1.0, 'aereos'], [9.0, 'logo']], 'tinnitus' => [],
    'presentaciones' => array_merge($sinVerificar(0, 1000, 40), $sinVerificar(0, 2000, 40), $sinVerificar(1, 1000, 40), $sinVerificar(1, 2000, 40))]);
$rr = ap_reglas($r['aereos']);
t_eq($rr['Los umbrales obtenidos corresponden a la audición del paciente.'], true, 'Puntería: en el nivel exacto aunque no verificó');
$oidosR = [];
foreach ($r['aereos']['oidos'] as $o => $lista) {
    foreach ($lista as $x) {
        if (strpos($x['texto'], '2 de 3') !== false) {
            $oidosR[$o] = $x['cumple'];
        }
    }
}
t_eq($oidosR, ['OD' => false, 'OI' => false], 'Puntería: la falta de verificación la cuenta solo su propia regla');
