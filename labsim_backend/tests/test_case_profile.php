<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseBuilder.php';
require_once __DIR__ . '/../src/CaseProfile.php';

/**
 * Audiograma de un oído a partir de un mapa Hz => dB, en el shape de pares
 * que usa cases.data (Aerea/Osea). Las frecuencias que no estén en el mapa
 * se rellenan con la más cercana ya definida, igual que carga un docente
 * que solo toca 500-4000.
 *
 * @param array<int,float> $porHz
 * @return array<int,array{0:float,1:float}>
 */
function audiograma(array $porHz): array
{
    $pares = [];
    $ultimo = 0.0;
    foreach (CaseBuilder::FREQUENCIES as $hz) {
        $ultimo = $porHz[$hz] ?? $ultimo;
        $pares[] = [$ultimo, $ultimo];
    }
    return $pares;
}

// ---------------------------------------------------------------------
// Umbral ABR por estímulo: el problema que originó el perfil.
// ---------------------------------------------------------------------

$normal = audiograma([125 => 0]);
$d = CaseProfile::decompose($normal, $normal, 0, 100.0);
$th = CaseProfile::abrThresholds($d);
t_eq($th['click'], 10, 'Oído de 0 dB HL: click a 10 dB nHL (la corrección nHL no es cero)');
t_eq($th['tone_burst_500Hz'], 20, 'Oído normal: burst de 500 Hz a 20 dB nHL');
t_eq($th['tone_burst_4000Hz'], 5, 'Oído normal: burst de 4 kHz a 5 dB nHL');
t_eq($th['ce_chirp'], 5, 'Oído normal: chirp por debajo del click (sincroniza mejor)');

// Descendente: lo que antes era imposible de representar -- un solo umbral
// escalar daba la misma respuesta a 500 Hz que a 4 kHz.
$descendente = audiograma([125 => 5, 250 => 5, 500 => 10, 1000 => 15, 2000 => 40, 3000 => 55, 4000 => 70, 6000 => 75, 8000 => 80]);
$d = CaseProfile::decompose($descendente, $descendente, 0, 100.0);
$th = CaseProfile::abrThresholds($d);
t_eq($th['tone_burst_500Hz'], 30, 'Descendente: burst de 500 Hz casi normal (10 dB HL + 20 de corrección)');
t_eq($th['tone_burst_1000Hz'], 30, 'Descendente: burst de 1 kHz todavía bajo');
t_eq($th['tone_burst_4000Hz'], 75, 'Descendente: burst de 4 kHz muy elevado');
t_true($th['tone_burst_4000Hz'] - $th['tone_burst_500Hz'] >= 40,
    'Descendente: 45 dB de diferencia entre 500 Hz y 4 kHz -- la evaluación frecuencia específica tiene algo que encontrar');
t_eq($th['click'], 65, 'Descendente: el click lo domina la base coclear (2-4 kHz), no el promedio del audiograma');
t_true($th['ce_chirp'] < $th['click'],
    'Descendente: el chirp pesa los graves conservados y da mejor umbral que el click');

// ---------------------------------------------------------------------
// Vía ósea: el gap conductivo del ABR sale del audiograma, sin campo nuevo.
// ---------------------------------------------------------------------

$aereaCond = audiograma([125 => 45]);
$oseaCond = audiograma([125 => 5]);
$d = CaseProfile::decompose($aereaCond, $oseaCond, 0, 100.0);
t_close($d['gap'][1000], 40.0, 0.01, 'Conductiva: gap de 40 dB en 1 kHz');
t_close($d['sn'][1000], 5.0, 0.01, 'Conductiva: componente sensorioneural mínimo');
$thAir = CaseProfile::abrThresholds($d, 'air_conduction');
$thBone = CaseProfile::abrThresholds($d, 'bone_conduction');
t_eq($thAir['click'], 55, 'Conductiva: click aéreo elevado por el gap');
// La ósea lleva su propia referencia de 0 dB nHL (ver boneNhlOffset): en un
// adulto son ~15 dB más que la aérea, y por eso este 30 es "óseo normal" y
// no un componente sensorioneural. Comparar los dos números de frente es
// justamente el error que hay que saber no cometer.
t_eq($thBone['click'], 30, 'Conductiva: click óseo normal para su propia referencia');
t_true(
    $thAir['click'] - $thBone['click'] >= 20,
    'Conductiva: el gap se ve igual comparando las dos vías, cada una contra su norma'
);
// Sin edad cargada se asume adulto; en un lactante el mismo oído daría la
// ósea mucho más baja, porque su cráneo compensa la referencia.
t_true(
    CaseProfile::abrThresholds($d, 'bone_conduction', 3.0)['click'] < $thBone['click'],
    'El mismo oído en un lactante da umbral óseo más bajo: es la referencia, no la audición'
);
t_eq(CaseProfile::derivedType($d, 100.0), 'transmission', 'Gap de 40 dB se clasifica como transmisión');

// Ósea peor que la aérea (ruido de carga del formulario) no inventa gap.
$d = CaseProfile::decompose(audiograma([125 => 20]), audiograma([125 => 40]), 0, 100.0);
t_close($d['gap'][1000], 0.0, 0.01, 'Ósea peor que la aérea: gap truncado en 0, no negativo');

// ---------------------------------------------------------------------
// OEA: solo el componente CCE y el gap atenúan la emisión.
// ---------------------------------------------------------------------

$plana40 = audiograma([125 => 40]);
$d = CaseProfile::decompose($plana40, $plana40, 0, 100.0);
$desv = CaseProfile::oaeDeviations($d);
t_close($desv['1000'], 30.0, 0.05, 'Coclear de 40 dB: 30 dB de atenuación de la OEA (1.2 dB/dB sobre 15)');
t_close($desv['4000'], 30.0, 0.05, 'Coclear plana: misma atenuación en agudos');

// Neuropatía: misma pérdida, cóclea viva -> OEA intactas. Es el contraste
// clínico con el ABR del mismo caso, y ahora sale del modelo solo.
$d = CaseProfile::decompose($plana40, $plana40, 0, 0.0);
$desv = CaseProfile::oaeDeviations($d);
t_close($desv['1000'], 0.0, 0.01, 'Neuropatía: OEA conservadas pese al umbral de 40 dB');
t_close($d['retro_sn'][1000], 40.0, 0.01, 'Neuropatía: toda la pérdida es retrococlear');
$ansd = ['bloqueo' => 'total', 'microfonica' => 'amplificada', 'desincronia' => 'alta'];
t_eq(CaseProfile::derivedType($d, 0.0, $ansd), 'neural', 'cce_pct 0 + patrón retro = neural');

// La conductiva también atenúa la OEA (ida y vuelta por el oído medio).
$d = CaseProfile::decompose($aereaCond, $oseaCond, 0, 100.0);
$desv = CaseProfile::oaeDeviations($d);
t_close($desv['1000'], 64.0 > CaseProfile::OAE_MAX_ATTEN_DB ? CaseProfile::OAE_MAX_ATTEN_DB : 64.0,
    0.05, 'Conductiva de 40 dB: OEA bajo el piso de ruido (tope de atenuación)');

// Descendente: la muesca en agudos tiene que verse en la OEA también.
$d = CaseProfile::decompose($descendente, $descendente, 0, 100.0);
$desv = CaseProfile::oaeDeviations($d);
t_close($desv['500'], 0.0, 0.01, 'Descendente: OEA presente en graves');
t_true($desv['4000'] > 40.0, 'Descendente: OEA ausente en agudos');

// Interpolación log-frecuencia: la OEA usa 1500 Hz y el audiograma no lo tiene.
$curva = [1000 => 20.0, 2000 => 40.0];
t_close(CaseProfile::levelAt($curva, 1500.0), 31.7, 0.2, '1500 Hz se interpola en log-frecuencia, no lineal en Hz');
t_close(CaseProfile::levelAt($curva, 500.0), 20.0, 0.01, 'Fuera de rango se extiende con el extremo más cercano');

// ---------------------------------------------------------------------
// Clasificación y reclutamiento.
// ---------------------------------------------------------------------

$d = CaseProfile::decompose($normal, $normal, 0, 100.0);
t_eq(CaseProfile::derivedType($d, 100.0), 'normal', 'Audiograma normal sin retro = normal');
t_eq(CaseProfile::recruitment(100.0, $d)['pattern'], 'none',
    'Sin pérdida sensorioneural no hay reclutamiento, por más coclear que diga el perfil');

$d = CaseProfile::decompose($plana40, $plana40, 0, 100.0);
t_eq(CaseProfile::derivedType($d, 100.0), 'coclear', 'Pérdida sin gap con CCE alto = coclear');
$rec = CaseProfile::recruitment(100.0, $d);
t_eq($rec['pattern'], 'complete', 'Coclear puro: reclutamiento completo');
t_true($rec['recruit'], 'Coclear puro: flag de reclutamiento encendido');
$rec = CaseProfile::recruitment(0.0, $d);
t_eq($rec['pattern'], 'none', 'Retrococlear: sin reclutamiento con la misma pérdida');
t_true($rec['sisi_pct'] < 20, 'Retrococlear: SISI bajo');

// retroActivo: los defaults NO son un hallazgo (i_iii/iii_v arrancan en 0.2).
t_true(!CaseProfile::retroActivo(CaseBuilder::ABR_NEURAL_DEFAULTS),
    'Los defaults del patrón retro no cuentan como hallazgo');
t_true(CaseProfile::retroActivo(CaseBuilder::ABR_NEURAL_PRESETS['schwannoma']['params']),
    'El preset de schwannoma sí es un patrón retro activo');
t_true(CaseProfile::retroActivo(['bloqueo' => 'post_i']),
    'Un bloqueo proximal es patrón retro aunque los interpicos estén en default');

// ---------------------------------------------------------------------
// No regresión: un caso guardado antes del perfil no cambia de conducta.
// ---------------------------------------------------------------------

$viejo = [
    'Aerea' => $plana40,
    'Osea' => $plana40,
    'ABR' => ['OD' => ['type' => 'coclear', 'umbral' => 40], 'OI' => ['type' => 'normal', 'umbral' => 20]],
    'EOAS' => ['OD' => ['type' => 'coclear', 'umbral' => 40], 'OI' => ['type' => 'normal', 'umbral' => 20]],
];
$p = CaseProfile::normalize($viejo);
t_eq($p['version'], CaseProfile::VERSION, 'normalize() estampa la versión del shape');
t_close($p['OD']['cce_pct'], 100.0, 0.01, 'Caso viejo coclear: cce_pct 100');
foreach (CaseProfile::AUTO_MODULES as $modulo) {
    t_true($p['auto'][$modulo] === false,
        "Caso viejo: el módulo '$modulo' arranca en manual (no puede cambiar de conducta al abrirlo)");
}

$viejoNeuro = $viejo;
$viejoNeuro['ABR']['OD'] = ['type' => 'neural', 'umbral' => 60, 'neural' => ['bloqueo' => 'total']];
$viejoNeuro['EOAS']['OD'] = ['type' => 'neural', 'umbral' => 60];
$p = CaseProfile::normalize($viejoNeuro);
t_close($p['OD']['cce_pct'], 0.0, 0.01, 'Caso viejo con EOA neural: cce_pct 0 (cóclea viva)');
t_eq($p['OD']['retro']['bloqueo'], 'total', 'El patrón retro se toma de ABR.neural mientras viva en ese tab');
t_eq($p['OD']['retro']['v_i_factor'], CaseBuilder::ABR_NEURAL_DEFAULTS['v_i_factor'],
    'Las claves que el caso viejo no traía caen en los defaults compartidos con el generador');

// Perfil ya guardado: se respeta tal cual, incluidos los auto encendidos.
$conPerfil = $viejo;
$conPerfil['Perfil'] = [
    'version' => 1,
    'OD' => ['cce_pct' => 35.0, 'retro' => ['iii_v_ms' => 0.7]],
    'OI' => ['cce_pct' => 100.0],
    'auto' => ['abr' => true, 'eoas' => false],
];
$p = CaseProfile::normalize($conPerfil);
t_close($p['OD']['cce_pct'], 35.0, 0.01, 'Perfil guardado: cce_pct se respeta');
t_true($p['auto']['abr'], 'Perfil guardado: auto encendido se respeta');
t_true(!$p['auto']['reflex'], 'Perfil guardado: un módulo ausente del mapa queda en manual');

// ---------------------------------------------------------------------
// Reflejo acústico: dos oídos, dos preguntas distintas.
// ---------------------------------------------------------------------

$dNormal = CaseProfile::decompose($normal, $normal, 0, 100.0);
$dCoclear40 = CaseProfile::decompose($plana40, $plana40, 0, 100.0);
$dRetro40 = CaseProfile::decompose($plana40, $plana40, 0, 0.0);
$dCond = CaseProfile::decompose($aereaCond, $oseaCond, 0, 100.0);
$sinRetro = CaseBuilder::ABR_NEURAL_DEFAULTS;

t_eq(CaseProfile::reflexThreshold($dNormal, $dNormal, 'A', 100.0, $sinRetro, 1000), 85,
    'Oído sano: reflejo a 85 dB HL');

// Metz: la coclear NO sube el umbral del reflejo en proporción a la pérdida.
t_eq(CaseProfile::reflexThreshold($dNormal, $dCoclear40, 'A', 100.0, $sinRetro, 1000), 85,
    'Coclear de 40 dB: el reflejo sigue en 85 -- el SL se achicó a 45 dB (Metz)');

// Misma pérdida, sitio distinto: el reflejo se cae.
t_eq(CaseProfile::reflexThreshold($dNormal, $dRetro40, 'A', 0.0, $sinRetro, 1000),
    CaseProfile::REFLEX_ABSENT_DB,
    'Retrococlear de 40 dB: reflejo ausente con el mismo audiograma que la coclear');

// El oído medio de la SONDA decide si se puede ver, aunque el estimulado esté sano.
t_eq(CaseProfile::reflexThreshold($dCond, $dNormal, 'A', 100.0, $sinRetro, 1000),
    CaseProfile::REFLEX_ABSENT_DB,
    'Gap en el oído sonda: no se registra el reflejo aunque el estimulado esté sano');
t_eq(CaseProfile::reflexThreshold($dNormal, $dNormal, 'B', 100.0, $sinRetro, 1000),
    CaseProfile::REFLEX_ABSENT_DB,
    'Timpanograma B en la sonda: reflejo no registrable');
t_eq(CaseProfile::reflexThreshold($dNormal, $dNormal, 'As', 100.0, $sinRetro, 1000),
    CaseProfile::REFLEX_ABSENT_DB,
    'Timpanograma As (rígido, otoesclerosis) en la sonda: reflejo no registrable');

// El gap del oído ESTIMULADO es atenuación pura y se suma entero.
$dGap15 = CaseProfile::decompose(audiograma([125 => 15]), audiograma([125 => 0]), 0, 100.0);
t_eq(CaseProfile::reflexThreshold($dNormal, $dGap15, 'A', 100.0, $sinRetro, 1000), 100,
    'Gap de 15 dB en el oído estimulado: el reflejo sube esos 15 dB');

// Schwannoma chico: audiograma casi normal y el reflejo ya se cae.
$schwannoma = CaseBuilder::ABR_NEURAL_PRESETS['schwannoma']['params'];
t_eq(CaseProfile::reflexThreshold($dNormal, $dNormal, 'A', 100.0, $schwannoma, 1000), 100,
    'Patrón retrococlear con audiograma normal: reflejo elevado');
$ansdParams = CaseBuilder::ABR_NEURAL_PRESETS['ansd']['params'];
t_eq(CaseProfile::reflexThreshold($dNormal, $dNormal, 'A', 0.0, $ansdParams, 1000),
    CaseProfile::REFLEX_ABSENT_DB,
    'ANSD: sin ondas no hay arco reflejo, ausente a cualquier nivel');

// Ruido de banda estrecha (fila NBN del contra): se juzga sobre el promedio.
t_eq(CaseProfile::reflexThreshold($dNormal, $dNormal, 'A', 100.0, $sinRetro, 'NBN'), 85,
    'Fila NBN: mismo criterio, sobre el promedio 500-4000');

// ---------------------------------------------------------------------
// Deterioro tonal.
// ---------------------------------------------------------------------

t_eq(CaseProfile::toneDecay($dNormal, 100.0, $sinRetro, 2000), 0,
    'Oído sano: sin deterioro tonal');
t_eq(CaseProfile::toneDecay($dCoclear40, 100.0, $sinRetro, 2000), 5,
    'Coclear: adaptación mínima, dentro de lo normal');
t_eq(CaseProfile::toneDecay($dRetro40, 0.0, $sinRetro, 2000), 30,
    'Retrococlear: hay que subir 30 dB para sostener el tono');
t_eq(CaseProfile::toneDecay($dNormal, 100.0, $schwannoma, 2000), 30,
    'Patrón retro con umbrales normales: deterioro igual -- es cuando la prueba vale la pena');

// ---------------------------------------------------------------------
// Avisos: contradicciones que hoy no las caza nadie.
// ---------------------------------------------------------------------

$perfilManual = [
    'version' => 1,
    'OD' => ['cce_pct' => 100.0, 'retro' => CaseBuilder::ABR_NEURAL_DEFAULTS],
    'OI' => ['cce_pct' => 100.0, 'retro' => CaseBuilder::ABR_NEURAL_DEFAULTS],
    'auto' => ['abr' => false, 'eoas' => false, 'reflex' => false, 'recruit' => false],
];
$eoasNormal = ['type' => 'normal', 'umbral' => 20, 'desviaciones' => []];
$abrNormal = ['type' => 'normal', 'umbral' => 20];
$reflexPresente = [
    'ipsi' => ['od' => [85, 85, 85, 85], 'oi' => [85, 85, 85, 85]],
    'contra' => ['od' => [85, 85, 85, 85, 85], 'oi' => [85, 85, 85, 85, 85]],
];
$tympNormal = ['OD' => 'A', 'OI' => 'A'];
$decompSanos = ['OD' => $dNormal, 'OI' => $dNormal];

t_eq(CaseProfile::warnings($decompSanos, $perfilManual,
        ['OD' => $abrNormal, 'OI' => $abrNormal],
        ['OD' => $eoasNormal, 'OI' => $eoasNormal],
        $reflexPresente, $tympNormal),
    [], 'Paciente sano y coherente: ningún aviso');

// OEA normales con una coclear de 40 dB: imposible, y hoy se guarda sin chistar.
$decompCoclear = ['OD' => $dCoclear40, 'OI' => $dNormal];
$avisos = CaseProfile::warnings($decompCoclear, $perfilManual,
    ['OD' => $abrNormal, 'OI' => $abrNormal],
    ['OD' => $eoasNormal, 'OI' => $eoasNormal],
    $reflexPresente, $tympNormal);
t_true(count($avisos) > 0, 'OEA presente con coclear de 40 dB: hay aviso');
t_true(strpos(implode(' ', $avisos), 'OEA OD') !== false, 'El aviso nombra el examen y el oído');

// La misma OEA con la lesión puesta en el nervio deja de ser contradictoria.
$perfilRetro = $perfilManual;
$perfilRetro['OD']['cce_pct'] = 0.0;
$decompRetro = ['OD' => $dRetro40, 'OI' => $dNormal];
$avisos = CaseProfile::warnings($decompRetro, $perfilRetro,
    ['OD' => $abrNormal, 'OI' => $abrNormal],
    ['OD' => $eoasNormal, 'OI' => $eoasNormal],
    $reflexPresente, $tympNormal);
t_true(!in_array(true, array_map(fn($a) => strpos($a, 'OEA') === 0, $avisos), true),
    'La misma OEA conservada con cce_pct 0 ya no contradice nada: es una neuropatía');

// Reflejos presentes con timpanograma B.
$avisos = CaseProfile::warnings($decompSanos, $perfilManual,
    ['OD' => $abrNormal, 'OI' => $abrNormal],
    ['OD' => $eoasNormal, 'OI' => $eoasNormal],
    $reflexPresente, ['OD' => 'B', 'OI' => 'A']);
t_true(count($avisos) > 0, 'Reflejos presentes con timpanograma B: hay aviso');

// ABR mucho mejor que el audiograma: el patrón de la simulación.
$decompProfunda = ['OD' => CaseProfile::decompose(audiograma([125 => 70]), audiograma([125 => 70]), 0, 100.0),
                   'OI' => $dNormal];
$avisos = CaseProfile::warnings($decompProfunda, $perfilManual,
    ['OD' => $abrNormal, 'OI' => $abrNormal],
    ['OD' => ['type' => 'coclear', 'umbral' => 70, 'desviaciones' => []], 'OI' => $eoasNormal],
    $reflexPresente, $tympNormal);
t_true(strpos(implode(' ', $avisos), 'ABR OD') !== false,
    'ABR de 20 dB con audiograma de 70: hay aviso');

// Un módulo derivado no puede contradecirse: no se lo revisa.
$perfilAuto = $perfilManual;
$perfilAuto['auto'] = ['abr' => true, 'eoas' => true, 'reflex' => true, 'recruit' => true];
t_eq(CaseProfile::warnings($decompCoclear, $perfilAuto,
        ['OD' => $abrNormal, 'OI' => $abrNormal],
        ['OD' => $eoasNormal, 'OI' => $eoasNormal],
        $reflexPresente, $tympNormal),
    [], 'Con todo derivado no se avisa nada: el perfil es la fuente');

// El timpanograma es la excepción: no se deriva de nada (qué curva sale
// depende de la patología concreta, no del audiograma), así que su
// contradicción con el gap se avisa siempre, con o sin módulos derivados.
$avisos = CaseProfile::warnings($decompSanos, $perfilAuto,
    ['OD' => $abrNormal, 'OI' => $abrNormal],
    ['OD' => $eoasNormal, 'OI' => $eoasNormal],
    $reflexPresente, ['OD' => 'B', 'OI' => 'A']);
t_true(strpos(implode(' ', $avisos), 'Timpanometría OD') !== false,
    'Curva B sin gap: se avisa aunque todo esté derivado');
$avisos = CaseProfile::warnings(['OD' => $dCond, 'OI' => $dNormal], $perfilAuto,
    ['OD' => $abrNormal, 'OI' => $abrNormal],
    ['OD' => $eoasNormal, 'OI' => $eoasNormal],
    $reflexPresente, $tympNormal);
t_true(strpos(implode(' ', $avisos), 'curva A') !== false,
    'Gap de 40 dB con timpanograma A: la contradicción que más se escapaba');
$avisos = CaseProfile::warnings(['OD' => $dCond, 'OI' => $dNormal], $perfilAuto,
    ['OD' => $abrNormal, 'OI' => $abrNormal],
    ['OD' => $eoasNormal, 'OI' => $eoasNormal],
    $reflexPresente, ['OD' => 'B', 'OI' => 'A']);
t_eq($avisos, [], 'Gap de 40 dB con curva B: coherente, sin aviso');

// La ley de atenuación cargada tiene que ser la misma que la del cliente.
$cargada = CaseProfile::loadedOaeAttenuation(['type' => 'coclear', 'umbral' => 40, 'desviaciones' => []]);
t_close($cargada['2000'], 30.0, 0.05, 'loadedOaeAttenuation replica oae_attenuation_db (1.2 dB/dB sobre 15)');
$cargada = CaseProfile::loadedOaeAttenuation(['type' => 'neural', 'umbral' => 70, 'desviaciones' => []]);
t_close($cargada['2000'], 0.0, 0.01, 'Neural no atenúa la OEA por más alto que esté el umbral');

// ---------------------------------------------------------------------
// Escenarios de sorteo: el JS los consume tal cual, así que el shape importa.
// ---------------------------------------------------------------------

foreach (CaseProfile::SCENARIOS as $clave => $esc) {
    foreach (['label', 'sn_shape', 'sn_scale', 'gap_shape', 'gap_scale', 'cce_pct', 'retro', 'lateralidad'] as $campo) {
        t_true(array_key_exists($campo, $esc), "Escenario '$clave': tiene la clave '$campo'");
    }
    t_true(in_array($esc['lateralidad'], ['bilateral', 'unilateral'], true),
        "Escenario '$clave': lateralidad válida");
    t_eq(array_keys($esc['sn_shape']), CaseBuilder::FREQUENCIES,
        "Escenario '$clave': la forma sensorioneural cubre las 9 frecuencias del audiograma");
    if ($esc['gap_shape'] !== []) {
        t_eq(array_keys($esc['gap_shape']), CaseBuilder::FREQUENCIES,
            "Escenario '$clave': la forma del gap cubre las 9 frecuencias");
    }
    if ($esc['retro'] !== null) {
        t_true(isset(CaseBuilder::ABR_NEURAL_PRESETS[$esc['retro']]),
            "Escenario '$clave': el preset retro '{$esc['retro']}' existe");
    }
}

// Cada escenario tiene que clasificar como lo que dice ser: si el sorteo
// produce un cuadro y el perfil lo lee como otro, el caso nace incoherente.
$esperado = [
    'normal' => 'normal',
    // Conductivas: la cóclea sana, el gap manda.
    'otitis_media' => 'transmission', 'efusion_neonatal' => 'transmission',
    'otoesclerosis' => 'transmission',
    'disyuncion_cadena' => 'transmission', 'fractura_cadena' => 'transmission',
    'fractura_longitudinal' => 'transmission', 'perforacion' => 'transmission', 'disfuncion_tubaria' => 'transmission',
    'tapon_cerumen' => 'transmission', 'cuerpo_extrano_cae' => 'transmission',
    'otitis_externa' => 'transmission', 'estenosis_atresia_cae' => 'transmission',
    'timpanoesclerosis' => 'transmission', 'otitis_media_aguda' => 'transmission',
    'colesteatoma' => 'transmission', 'fijacion_congenita_estribo' => 'transmission',
    'barotrauma' => 'transmission', 'glomus_timpanico' => 'transmission',
    // Sensoriales: coclear puro.
    'presbiacusia' => 'coclear', 'muesca_4k' => 'coclear', 'coclear_plana' => 'coclear',
    'meniere' => 'coclear', 'subita' => 'coclear',
    'fractura_transversal' => 'coclear', 'ototoxica' => 'coclear',
    'nihl_cronica' => 'coclear', 'trauma_acustico_agudo' => 'coclear',
    'salicilatos' => 'coclear', 'laberintitis' => 'coclear',
    'osificacion_coclear' => 'coclear', 'conmocion_laberintica' => 'coclear',
    'hidrops_retardado' => 'coclear', 'autoinmune' => 'coclear',
    'parotiditis' => 'coclear', 'metabolica' => 'coclear',
    // Genéticas y congénitas: la forma cambia, el sitio de la lesión no.
    'gjb2' => 'coclear', 'usher' => 'coclear', 'waardenburg' => 'coclear',
    'alport' => 'coclear', 'jervell_lange_nielsen' => 'coclear', 'stickler' => 'coclear',
    'pendred' => 'coclear',
    'cmv_congenito' => 'coclear', 'rubeola_congenita' => 'coclear',
    // Neurales: la cóclea viva y el ABR desarmado. Varios de estos traen el
    // audiograma casi normal y aun así NO clasifican normal: el patrón
    // retrococlear activo manda sobre el promedio tonal.
    'schwannoma' => 'neural', 'neuropatia' => 'neural',
    'asfixia_perinatal' => 'neural', 'kernicterus' => 'neural',
    'nf2' => 'neural', 'tumor_angulo' => 'neural', 'compresion_microvascular' => 'neural',
    'esclerosis_multiple' => 'neural', 'infarto_pontino' => 'neural',
    'glioma_tronco' => 'neural', 'siderosis' => 'neural', 'chiari_hic' => 'neural',
    'leucodistrofia' => 'neural', 'neuropatia_hereditaria' => 'neural',
    'tec_tronco' => 'neural', 'toxico_metabolico' => 'neural',
    'hipotermia_farmacos' => 'neural', 'prematuro' => 'neural',
    'bloqueo_proximal' => 'neural',
    // Los dos componentes a la vez: con cce en el medio pesa el retro, que es
    // lo que el generador de curvas tiene que dibujar.
    'sensorioneural' => 'neural',
    // Mixtas: el gap sigue mandando sobre el tipo que ve el generador.
    'mixta_otitis_cronica' => 'transmission', 'mixta_otoesclerosis' => 'transmission',
    'colesteatoma_fistula' => 'transmission', 'oido_operado' => 'transmission',
    'paget' => 'transmission', 'carcinoma_cae' => 'transmission',
    'trauma_craneal_completo' => 'transmission', 'post_radioterapia' => 'transmission',
];
t_eq(array_keys($esperado), array_keys(CaseProfile::SCENARIOS),
    'La tabla de clasificación esperada cubre todos los cuadros del catálogo');
foreach (CaseProfile::SCENARIOS as $clave => $esc) {
    // Escala media, sin jitter: el centro del cuadro.
    $escala = (($esc['sn_scale'][0] + $esc['sn_scale'][1]) / 2) ?: 1.0;
    $escalaGap = ($esc['gap_scale'][0] + $esc['gap_scale'][1]) / 2;
    $sn = [];
    $aire = [];
    foreach (CaseBuilder::FREQUENCIES as $hz) {
        $s = ($esc['sn_shape'][$hz] ?? 0) * $escala;
        $g = ($esc['gap_shape'][$hz] ?? 0) * $escalaGap;
        $sn[$hz] = $s;
        $aire[$hz] = $s + $g;
    }
    $cce = ($esc['cce_pct'][0] + $esc['cce_pct'][1]) / 2;
    $retro = $esc['retro'] !== null ? CaseBuilder::ABR_NEURAL_PRESETS[$esc['retro']]['params'] : [];
    $d = CaseProfile::decompose(audiograma($aire), audiograma($sn), 0, $cce);
    t_eq(CaseProfile::derivedType($d, $cce, $retro), $esperado[$clave],
        "Escenario '$clave': el perfil lo clasifica como '{$esperado[$clave]}'");
}

// La descendente NO es un oído normal aunque el promedio 500-4000 dé 22 dB:
// clasificar por promedio se comía el caso que motivó todo el perfil.
$suave = audiograma([125 => 0, 250 => 0, 500 => 5, 1000 => 10, 2000 => 25, 3000 => 35, 4000 => 45, 6000 => 50, 8000 => 55]);
$dDesc = CaseProfile::decompose($suave, $suave, 0, 100.0);
t_true(CaseProfile::coreAverage($dDesc['sn']) <= CaseProfile::SN_NORMAL_DB,
    'La descendente promedia dentro de lo normal en 500-4000');
t_eq(CaseProfile::derivedType($dDesc, 100.0), 'coclear',
    'Y aun así se clasifica coclear: manda la frecuencia dañada, no el promedio');
t_true(CaseProfile::recruitment(100.0, $dDesc)['recruit'],
    'Mismo criterio para el reclutamiento: se busca donde está el daño');

// ---------------------------------------------------------------------
// Sin respuesta (130): no es un umbral de 130 dB.
//
// El audiómetro llega a 120: un 130 significa que el paciente no oyó ni al
// máximo. Tomarlo como número inflaba los promedios 60 dB e inventaba gaps,
// porque restarle la ósea a un 130 da una diferencia que nadie midió.
// ---------------------------------------------------------------------

t_eq(CaseProfile::SIN_RESPUESTA_DB, 130.0, 'El valor de "sin respuesta" es el 130 que guarda el caso');
t_true(CaseProfile::MAX_AUDIOMETRO_DB < CaseProfile::SIN_RESPUESTA_DB,
    'Y está por encima de lo que el audiómetro puede entregar');

$sinResp = audiograma([125 => 30, 250 => 35, 500 => 40, 1000 => 50, 2000 => 70, 3000 => 90,
                       4000 => 130, 6000 => 130, 8000 => 130]);
$dSinResp = CaseProfile::decompose($sinResp, $sinResp, 0, 100.0);

t_eq($dSinResp['sin_respuesta']['air'], [4000, 6000, 8000],
    'decompose() deja anotadas las frecuencias sin respuesta');
t_eq($dSinResp['air'][4000], CaseProfile::MAX_AUDIOMETRO_DB,
    'El umbral se recorta al tope del audiómetro: ese oído es al menos así de malo');
t_eq($dSinResp['gap'][4000], 0.0,
    'Y no se inventa un gap restándole la ósea a un umbral que no existe');

// El promedio no se va a las nubes por una frecuencia sin respuesta.
t_true(CaseProfile::coreAverage($dSinResp['sn']) <= 75.0,
    'El promedio usa el tope del audiómetro, no el 130');

// El ABR de una frecuencia que no respondió en el tonal tampoco responde:
// es null y no un umbral saturado en el tope, que se leería como medido.
$thSinResp = CaseProfile::abrThresholds($dSinResp);
t_eq($thSinResp['tone_burst_4000Hz'], null,
    'Sin respuesta en 4 kHz, el burst de 4 kHz no tiene umbral que informar');
t_true($thSinResp['tone_burst_500Hz'] !== null,
    'Y las frecuencias que sí respondieron conservan el suyo');
t_true($thSinResp['click'] !== null,
    'El click se sostiene mientras alguna de sus frecuencias responda');

// Un oído sin respuesta en NINGUNA frecuencia: tampoco hay click.
$mudo = audiograma([125 => 130]);
$dMudo = CaseProfile::decompose($mudo, $mudo, 0, 100.0);
t_eq(CaseProfile::abrThresholds($dMudo)['click'], null,
    'Sin respuesta en todo el audiograma, el click tampoco tiene umbral');

// Lo que se GUARDA sí lleva número: el cliente lee un entero, y el tope es
// como el propio módulo expresa "no hubo respuesta en toda la escala".
$proyectadoMudo = CaseProfile::project(
    $mudo,
    $mudo,
    ['OD' => ['cce_pct' => 100.0, 'retro' => []], 'OI' => ['cce_pct' => 100.0, 'retro' => []]],
    ['OD' => 'A', 'OI' => 'A']
);
t_eq($proyectadoMudo['abr']['OD']['umbral'], CaseProfile::ABR_MAX_DB,
    'El umbral guardado del ABR es el tope, no null: el cliente lee un número');
t_eq($proyectadoMudo['abr']['OD']['umbral_por_estimulo']['click'], null,
    'Pero el detalle por estímulo conserva el null para poder decir "sin respuesta"');

// ---------------------------------------------------------------------
// project(): la misma pasada que corre al guardar y en la vista previa.
// ---------------------------------------------------------------------

$perfilCoclearOD = [
    'version' => 1,
    'OD' => ['cce_pct' => 100.0, 'retro' => CaseBuilder::ABR_NEURAL_DEFAULTS],
    'OI' => ['cce_pct' => 100.0, 'retro' => CaseBuilder::ABR_NEURAL_DEFAULTS],
    'auto' => ['abr' => true, 'eoas' => true, 'reflex' => true, 'recruit' => true],
];
// OD descendente, OI sano: pares [od, oi] armados a mano.
$paresAsim = [];
foreach (CaseBuilder::FREQUENCIES as $i => $hz) {
    $paresAsim[] = [$descendente[$i][0], 0];
}
$p = CaseProfile::project($paresAsim, $paresAsim, $perfilCoclearOD, ['OD' => 'A', 'OI' => 'A']);

foreach (['decomp', 'abr', 'eoas', 'reflex', 'recruit'] as $clave) {
    t_true(isset($p[$clave]), "project() devuelve '$clave'");
}
t_eq($p['abr']['OD']['type'], 'coclear', 'project(): OD descendente sale coclear');
t_eq($p['abr']['OI']['type'], 'normal', 'project(): OI sano sale normal');
t_eq($p['abr']['OD']['umbral_por_estimulo']['tone_burst_4000Hz'], 75,
    'project(): el umbral por estímulo es el mismo que abrThresholds');
t_eq($p['abr']['OD']['umbral'], $p['abr']['OD']['umbral_por_estimulo']['click'],
    'project(): el escalar queda alineado al click');
t_eq($p['eoas']['OD']['umbral'], 0,
    'project(): el umbral de EOA va en 0 -- la atenuación sale del perfil, no de la ley por patología');
t_eq(count($p['reflex']['ipsi']['od']), count(CaseProfile::REFLEX_FREQS_IPSI),
    'project(): 4 filas de reflejo ipsi');
t_eq(count($p['reflex']['contra']['od']), count(CaseProfile::REFLEX_FREQS_CONTRA),
    'project(): 5 filas de reflejo contra (incluye NBN)');
t_eq(count($p['recruit']['decay']['stat']['od']), 3, 'project(): el Stat tiene 3 frecuencias');
t_eq(count($p['recruit']['decay']['carhart']['od']), 4, 'project(): el Carhart tiene 4');
t_true($p['recruit']['sisi'][0] > $p['recruit']['sisi'][1],
    'project(): el SISI del oído dañado es más alto que el del sano');

// Fowler: con un oído sano y otro con 45 dB de diferencia, califica y el
// patrón es el del oído EN ESTUDIO (el peor).
t_true(count($p['recruit']['fowler']) > 0,
    'project(): un caso asimétrico califica para Fowler en alguna frecuencia');
foreach ($p['recruit']['fowler'] as $freqIdx => $patron) {
    t_true(array_key_exists($patron, CaseBuilder::FOWLER_PATTERNS),
        "project(): el patrón de Fowler en el índice $freqIdx es uno de los válidos");
}

// Un oído sin pérdida no puede tener reflejos ausentes ni deterioro tonal.
t_eq($p['reflex']['ipsi']['oi'], [85, 85, 85, 85], 'project(): el oído sano tiene reflejos normales');
t_eq($p['recruit']['decay']['carhart']['oi'], [0, 0, 0, 0], 'project(): el oído sano no tiene deterioro tonal');

// ---------------------------------------------------------------------
// Logoaudiometría: la disociación audio-verbal.
// ---------------------------------------------------------------------

$logoSano = CaseProfile::discrimination($dNormal, 100.0, $sinRetro);
t_eq($logoSano['pct'], 100, 'Oído sano: 100% de discriminación');

$logoCoclear = CaseProfile::discrimination($dCoclear40, 100.0, $sinRetro);
$logoRetro = CaseProfile::discrimination($dRetro40, 0.0, $sinRetro);
t_true($logoCoclear['pct'] >= 80,
    'Coclear de 40 dB: discriminación reducida pero funcional (~84%)');
t_true($logoRetro['pct'] < 60,
    'Retrococlear de 40 dB: discriminación muy por debajo de lo que predice el audiograma');
t_true($logoCoclear['pct'] - $logoRetro['pct'] >= 25,
    'Mismo audiograma, sitio distinto: eso es la disociación audio-verbal, y sin esto el caso no la podía mostrar');
t_eq($logoCoclear['pct'] % 4, 0,
    'El porcentaje cae en la grilla de por_logo (múltiplos de 4): fuera de ella el motor del logograma revienta');

// Schwannoma con audiograma limpio: la discriminación igual se cae.
$logoSchwannoma = CaseProfile::discrimination($dNormal, 100.0, $schwannoma);
t_true($logoSchwannoma['pct'] < 85,
    'Patrón retro con umbrales normales: discriminación caída igual');

// El gap no distorsiona, solo atenúa: no baja el máximo, lo corre a la derecha.
$logoCond = CaseProfile::discrimination($dCond, 100.0, $sinRetro);
t_eq($logoCond['pct'], 100, 'Conductiva: la discriminación máxima no cae, una conductiva no distorsiona');
t_true($logoCond['int'] > $logoSano['int'] + 25,
    'Conductiva: el máximo se alcanza mucho más fuerte');

// ---------------------------------------------------------------------
// LDL: el reclutamiento no se dibuja, cae de la física.
// ---------------------------------------------------------------------

$ldlSano = CaseProfile::ldlCurve($dNormal, 100.0);
$ldlCoclear = CaseProfile::ldlCurve($dCoclear40, 100.0);
$ldlRetro = CaseProfile::ldlCurve($dCoclear40, 0.0);
t_eq($ldlSano[3], (int) CaseProfile::LDL_NORMAL_DB, 'Oído sano: LDL en 100 dB');
t_eq($ldlCoclear[3], (int) CaseProfile::LDL_NORMAL_DB,
    'Coclear: el LDL NO sube con la pérdida -- el umbral sube y el campo dinámico se cierra solo');
t_true($ldlRetro[3] > $ldlCoclear[3],
    'Retrococlear: mismo umbral, LDL más alto, campo dinámico conservado (sin reclutamiento)');
t_true($ldlCoclear[3] <= CaseProfile::LDL_MAX_DB, 'El LDL no pasa el tope del audiómetro');
$ldlCond = CaseProfile::ldlCurve($dCond, 100.0);
t_true($ldlCond[3] > $ldlSano[3],
    'Conductiva: el oído medio atenúa también lo fuerte, el LDL sube con el gap');

// ---------------------------------------------------------------------
// Morfología de la curva del reflejo.
// ---------------------------------------------------------------------

t_eq(CaseProfile::reflexCurveType($dNormal, 100.0, $sinRetro), 'normal',
    'Oído sano: curva de reflejo normal (ON sostenido)');
t_eq(CaseProfile::reflexCurveType($dCoclear40, 100.0, $sinRetro), 'normal',
    'Coclear: sin decay del reflejo');
t_eq(CaseProfile::reflexCurveType($dRetro40, 0.0, $sinRetro), 'off',
    'Retrococlear: patrón OFF, el reflejo no se sostiene');
t_eq(CaseProfile::reflexCurveType($dNormal, 100.0, $schwannoma), 'off',
    'Patrón retro cargado: decay aunque el audiograma esté limpio');
foreach (['normal', 'off'] as $tipoRef) {
    t_true(in_array($tipoRef, CaseBuilder::REFLEX_CURVE_TYPES, true),
        "El tipo derivado '$tipoRef' es uno de los que acepta el formulario");
}

// project() los trae todos.
$p = CaseProfile::project($paresAsim, $paresAsim, $perfilCoclearOD, ['OD' => 'A', 'OI' => 'A']);
t_true(isset($p['logo']['OD']['pct'], $p['logo']['OD']['int']), 'project(): trae la logoaudiometría');
t_eq(count($p['recruit']['ldl']['od']), count(CaseBuilder::FREQUENCIES), 'project(): trae el LDL completo');
t_eq($p['reflex']['tipo']['oi'], 'normal', 'project(): trae la morfología del reflejo por oído');
t_true($p['logo']['OD']['pct'] < $p['logo']['OI']['pct'],
    'project(): el oído dañado discrimina menos que el sano');

// ---------------------------------------------------------------------
// Completitud: lo que el docente tiene que decidir porque no se calcula.
// ---------------------------------------------------------------------

require_once __DIR__ . '/../src/CaseCompleteness.php';

$abrCompleto = [
    'type' => 'coclear', 'umbral' => 40,
    'desviaciones' => ['onda_I' => ['lat' => 0.3, 'amp' => -0.1],
                       'onda_III' => ['lat' => 0.2, 'amp' => 0],
                       'onda_V' => ['lat' => 0.25, 'amp' => -0.05]],
];
$casoSano = [
    'Aerea' => $normal, 'Osea' => $normal,
    'Z_OD' => 'A', 'Z_OI' => 'A', 'ETF' => ['Normal', 'Normal'],
    'ABR' => ['OD' => ['type' => 'normal', 'desviaciones' => []], 'OI' => ['type' => 'normal', 'desviaciones' => []]],
    'VEMP' => ['OD' => ['type' => 'normal'], 'OI' => ['type' => 'normal']],
];
t_eq(CaseCompleteness::pending($casoSano), [], 'Caso normal completo: nada pendiente');

// Conductivo con el timpanograma sin tocar: el default más fácil de dejar.
$casoCond = $casoSano;
$casoCond['Aerea'] = $aereaCond;
$casoCond['Osea'] = $oseaCond;
$casoCond['ABR'] = ['OD' => $abrCompleto, 'OI' => $abrCompleto];
$faltan = CaseCompleteness::pendingTexts($casoCond);
t_true(count($faltan) >= 2, 'Gap de 40 dB con curva A: pendiente en los dos oídos');
t_true(strpos(implode(' ', $faltan), 'Timpanometría OD') !== false,
    'El pendiente nombra el examen y el oído');
t_eq(CaseCompleteness::pending($casoCond)[0]['tab'], 'timpanometria',
    'El pendiente dice en qué pestaña se arregla');

// Con la curva elegida, queda la ETF por decidir.
$casoCond['Z_OD'] = 'B';
$casoCond['Z_OI'] = 'B';
$faltan = CaseCompleteness::pendingTexts($casoCond);
t_true(strpos(implode(' ', $faltan), 'Función tubaria') !== false,
    'Timpanograma B con ETF "Normal": falta decidir la trompa');
$casoCond['ETF'] = ['No permeable', 'No permeable'];
t_eq(CaseCompleteness::pending($casoCond), [], 'Con la curva y la ETF decididas, el caso conductivo está completo');

// ABR con patología pero sin morfología: la curva sale como la de un sano.
$casoAbr = $casoSano;
$casoAbr['ABR'] = ['OD' => ['type' => 'coclear', 'umbral' => 40, 'desviaciones' => []],
                   'OI' => ['type' => 'normal', 'desviaciones' => []]];
$faltan = CaseCompleteness::pendingTexts($casoAbr);
t_true(strpos(implode(' ', $faltan), 'ABR OD') !== false,
    'ABR con patología y desviaciones en 0: falta correr el autocompletar');
$casoAbr['ABR']['OD'] = $abrCompleto;
t_eq(CaseCompleteness::pending($casoAbr), [], 'Con las ondas cargadas, el ABR deja de estar pendiente');

// VEMP: el perfil no tiene eje vestibular, así que alguien tiene que decidir.
$casoRetro = $casoSano;
$casoRetro['Perfil'] = [
    'version' => 1,
    'OD' => ['cce_pct' => 20.0, 'retro' => CaseBuilder::ABR_NEURAL_PRESETS['schwannoma']['params']],
    'OI' => ['cce_pct' => 100.0, 'retro' => CaseBuilder::ABR_NEURAL_DEFAULTS],
    'auto' => ['abr' => true, 'eoas' => true, 'reflex' => true, 'recruit' => true, 'logo' => true],
];
$casoRetro['ABR']['OD'] = ['type' => 'neural', 'desviaciones' => $abrCompleto['desviaciones']];
$faltan = CaseCompleteness::pendingTexts($casoRetro);
t_true(strpos(implode(' ', $faltan), 'VEMP OD') !== false,
    'Patrón retrococlear con VEMP normal sin tocar: falta decidir lo vestibular');
t_true(strpos(implode(' ', $faltan), 'VEMP OI') === false,
    'El oído sin patrón retro no pide nada en VEMP');

// Un caso viejo, sin las claves nuevas, no debe explotar ni inventar faltas.
t_eq(CaseCompleteness::pending([]), [], 'Un cases.data vacío no genera pendientes falsos');

// ---------------------------------------------------------------------
// Borrador de anamnesis por LLM: lo que vuelve del modelo es texto ajeno.
// ---------------------------------------------------------------------

require_once __DIR__ . '/../src/AnamnesisDraft.php';

$b = AnamnesisDraft::parse('{"antecedentes":["trauma_acustico","ototoxicos"],"medicamentos":"gentamicina IV hace 3 años","cirugias":"","otros":"trabajó 20 años en construcción","comportamiento":"colaborador","disposicion":1}');
t_true($b !== null, 'Un JSON bien formado se parsea');
t_true($b['antecedentes']['trauma_acustico'], 'Marca el antecedente que pidió el modelo');
t_true(!$b['antecedentes']['diabetes'], 'Deja en false los que no pidió');
t_eq(count($b['antecedentes']), count(CaseBuilder::HIST_CHECKBOXES),
    'Devuelve las 8 claves, no solo las marcadas');
t_eq($b['disposicion'], 1, 'La disposición pasa como entero');

// Lista cerrada: un antecedente inventado no entra a la ficha.
$b = AnamnesisDraft::parse('{"antecedentes":["trauma_acustico","tabaquismo","covid"],"disposicion":0}');
t_true(!array_key_exists('tabaquismo', $b['antecedentes']),
    'Un antecedente que el modelo inventó se descarta: la lista es cerrada');
t_true($b['antecedentes']['trauma_acustico'], 'Los válidos del mismo lote sí entran');

// Rangos y tamaños: el modelo no llena la ficha ni se sale de escala.
$b = AnamnesisDraft::parse('{"antecedentes":[],"medicamentos":"' . str_repeat('x', 900) . '","disposicion":99}');
t_eq(mb_strlen($b['medicamentos']), AnamnesisDraft::MAX_TEXTO, 'Los campos cortos se recortan a MAX_TEXTO');
t_eq($b['disposicion'], 2, 'La disposición se acota al rango del selector');
$b = AnamnesisDraft::parse('{"antecedentes":[],"disposicion":-99}');
t_eq($b['disposicion'], -2, 'Y por abajo también');

// El modelo a veces envuelve el JSON pese a la instrucción.
$b = AnamnesisDraft::parse("```json\n{\"antecedentes\":[\"otitis\"],\"disposicion\":0}\n```");
t_true($b !== null && $b['antecedentes']['otitis'], 'Se pela el fence de ``` como en OirsEvaluator');
t_eq(AnamnesisDraft::parse('lo siento, no puedo'), null, 'Una respuesta que no es JSON devuelve null');

// El prompt describe hallazgos, no números crudos ni nombres de examen.
$casoDesc = [
    'edad' => 34, 'gender' => 0,
    'Aerea' => $descendente, 'Osea' => $descendente,
    'Z_OD' => 'A', 'Z_OI' => 'A',
];
$desc = AnamnesisDraft::describeCase($casoDesc);
t_true(strpos($desc, '34 años') !== false, 'El prompt lleva la edad');
t_true(strpos($desc, 'agudas') !== false, 'Describe la forma de la pérdida, no la lista de umbrales');
t_true(strpos($desc, 'dB') === false, 'No le pasa dB al modelo: los umbrales los mide el alumno');

$casoCondDesc = $casoDesc;
$casoCondDesc['Aerea'] = $aereaCond;
$casoCondDesc['Osea'] = $oseaCond;
$casoCondDesc['Z_OD'] = 'B';
$desc = AnamnesisDraft::describeCase($casoCondDesc);
t_true(strpos($desc, 'oído medio') !== false, 'Una conductiva se describe como problema de oído medio');
t_true(strpos($desc, 'timpanograma tipo B') !== false, 'El timpanograma anormal entra al prompt');

// ---------------------------------------------------------------------
// Y la verificación es obligatoria.
// ---------------------------------------------------------------------

$casoIa = $casoSano;
$casoIa['Anamnesis'] = ['ia' => ['generado' => true, 'verificado' => false]];
$faltan = CaseCompleteness::pendingTexts($casoIa);
t_true(strpos(implode(' ', $faltan), 'Anamnesis') !== false,
    'Borrador de IA sin verificar: el caso no está listo');

$casoIa['Anamnesis']['ia']['verificado'] = true;
t_eq(CaseCompleteness::pending($casoIa), [], 'Verificado, deja de estar pendiente');

$casoManual = $casoSano;
$casoManual['Anamnesis'] = ['medicamentos' => 'ninguno'];
t_eq(CaseCompleteness::pending($casoManual), [],
    'Una anamnesis escrita a mano no pide verificación: el chequeo es solo para lo que escribió el modelo');

// El relato: el campo que faltaba. Sin él, un paciente sin antecedentes
// formales (una normoyente joven con acúfeno) dejaba la ficha vacía, y el
// modelo metía lo único que podía decir en "comportamiento".
// La historia clínica NO es el motivo de consulta: son las atenciones
// previas del paciente, fechadas con llaves {{-N}} que la app resuelve
// contra la fecha de la cita (ver resolver_fechas_historia_clinica en
// src/core/ficha.py). Es lo que el alumno lee en la ficha antes de atender.
$b = AnamnesisDraft::parse('{"historia_clinica":"{{-20}} Nace de 38 semanas, parto vaginal, 3.240 g. Screening auditivo: refiere OD.\n{{-5}} Control con pediatra, se deriva a evaluación auditiva.","antecedentes":[],"comportamiento":"tranquila","disposicion":0}');
t_true(strpos($b['historia_clinica'], '{{-20}}') !== false,
    'Las llaves de fecha llegan intactas: las resuelve el cliente, no nosotros');
t_true(substr_count($b['historia_clinica'], '{{-') === 2, 'Una atención por línea, cada una con su fecha');
t_eq(mb_strlen(AnamnesisDraft::parse('{"historia_clinica":"' . str_repeat('x', 3000) . '"}')['historia_clinica']),
    AnamnesisDraft::MAX_HISTORIA, 'La historia se recorta a su propio tope');
t_true(AnamnesisDraft::MAX_HISTORIA > AnamnesisDraft::MAX_RELATO,
    'Y es el tope más grande: son varias atenciones fechadas, no un párrafo');
t_eq(AnamnesisDraft::parse('{"antecedentes":[]}')['historia_clinica'], '',
    'Si el modelo no la manda, queda vacía -- no se inventa nada del lado nuestro');

// El prompt tiene que explicar las dos cosas que nadie puede adivinar: el
// significado del campo y la sintaxis de las fechas.
t_true(strpos(AnamnesisDraft::SYSTEM_PROMPT, 'ATENCIONES PREVIAS') !== false,
    'El prompt dice qué es la historia clínica, que no es el motivo de consulta');
t_true(strpos(AnamnesisDraft::SYSTEM_PROMPT, '{{-N}}') !== false,
    'Y la sintaxis de fecha relativa, que es propia de LabSim');
t_true(strpos(AnamnesisDraft::SYSTEM_PROMPT, 'screening auditivo') !== false,
    'Y qué poner en un recién nacido, que es donde la historia más importa');
t_true(strpos(AnamnesisDraft::SYSTEM_PROMPT, '"otros" TAMPOCO va vacío') !== false,
    'Y que "otros" tampoco va vacío: de ahí sale lo que el paciente cuenta en el chat');
t_true(strlen(AnamnesisDraft::SYSTEM_PROMPT) < 3400,
    'El prompt se mantiene acotado -- es lo único del input que controlamos -- pero sin recortar reglas que hacen falta');

// Un lactante no puede describirse como "de 0 años": es justo el caso donde
// la historia clínica (nacimiento, peso, screening) es lo que importa.
$desc = AnamnesisDraft::describeCase(['edad' => 0, 'gender' => 1,
    'Aerea' => $normal, 'Osea' => $normal, 'Z_OD' => 'A', 'Z_OI' => 'A']);
t_true(strpos($desc, 'lactante') !== false, 'Edad 0 se describe como lactante, no como "0 años"');
t_true(strpos($desc, '0 años') === false, 'Y no se le manda un absurdo al modelo');

// "otros" es narrativo como el relato, no un campo corto: de ahí sale todo
// lo que el paciente contesta en el chat, y con 400 caracteres hablaba en
// monosílabos.
$b = AnamnesisDraft::parse('{"otros":"' . str_repeat('x', 2000) . '"}');
t_eq(mb_strlen($b['otros']), AnamnesisDraft::MAX_RELATO,
    '"otros" usa el tope narrativo, no el de los campos cortos');
$b = AnamnesisDraft::parse('{"otros":"Trabaja en un taller mecánico desde los 18. Los fines de semana toca en una banda. Dice que lo nota más de noche, cuando se acuesta."}');
t_true(strpos($b['otros'], 'taller') !== false, 'Y se parsea tal cual lo escribió el modelo');

// En Chile quién realiza cada evaluación es materia sensible y el caso no la
// fija: las derivaciones se nombran por el ESTUDIO, no por la profesión.
foreach (['fonoaudiolog', 'otorrinolaring', 'tecnólogo médico', 'tecnologo medico'] as $profesion) {
    t_true(mb_stripos(AnamnesisDraft::SYSTEM_PROMPT, $profesion) === false,
        "El prompt del borrador no nombra la profesión ('$profesion')");
    t_true(mb_stripos(LlmConfig::DEFAULT_PROMPT, $profesion) === false,
        "El prompt del paciente tampoco ('$profesion')");
    t_true(mb_stripos(LlmConfig::DEFAULT_OIRS_PROMPT, $profesion) === false,
        "Ni el del evaluador OIRS ('$profesion')");
}
t_true(strpos(AnamnesisDraft::SYSTEM_PROMPT, 'evaluación auditiva') !== false,
    'Y dice explícitamente cómo escribir una derivación: por el estudio');

// ---------------------------------------------------------------------
// Grados de hipoacusia por cuadro (GRADES / SCENARIOS['grados']).
//
// El editor escala la forma del cuadro con UN factor hasta que el promedio
// BIAP caiga en el rango del grado pedido. Eso solo funciona mientras
// ninguna frecuencia DEL PROMEDIO sature: si 4 kHz llega al tope de la
// audiometría, subir la escala ya no sube el promedio y el cuadro se aplana
// --deja de ser el cuadro que se eligió--. Estos tests son el contrato entre
// las formas de SCENARIOS y las listas `grados`: tocar una `sn_shape` sin
// revisar la otra deja al docente un grado que el generador no puede dar.
// ---------------------------------------------------------------------

/**
 * Techo del promedio BIAP para un cuadro: los tres topes de techoDe() en el
 * JS del generador -- saturación de la audiometría, `max_db` y el techo de la
 * transmisión (`gap_max_db`), que es el que impide que subirle el grado a una
 * conductiva le ponga un gap que ningún oído medio puede dar.
 */
function techoBiap(array $esc): float
{
    $suma = 0.0;
    $peor = 0.0;
    foreach (CaseProfile::GRADE_FREQS as $hz) {
        $v = ($esc['sn_shape'][$hz] ?? 0) + ($esc['gap_shape'][$hz] ?? 0);
        $suma += $v;
        $peor = max($peor, (float) $v);
    }
    $base = $suma / count(CaseProfile::GRADE_FREQS);
    // 115 dB = MAX_DB en el JS del generador (case_create.php).
    $porSaturacion = $peor > 0 ? $base * (115.0 / $peor) : INF;
    // El gap se desborda en los graves, que NO entran en el promedio: el peor
    // se busca sobre las nueve frecuencias.
    $peorGap = $esc['gap_shape'] ? max($esc['gap_shape']) : 0;
    $porGap = $peorGap > 0
        ? $base * (techoGapDe($esc) / $peorGap)
        : INF;
    return min($porSaturacion, $porGap, (float) ($esc['max_db'] ?? INF));
}

/** Techo de la transmisión del cuadro (espejo de techoGap() en el JS). */
function techoGapDe(array $esc): float
{
    return min((float) ($esc['gap_max_db'] ?? CaseProfile::GAP_MAX_DB), CaseProfile::GAP_MAX_DB);
}

t_eq(CaseProfile::GRADE_FREQS, [500, 1000, 2000, 4000], 'GRADE_FREQS: promedio BIAP');
t_eq(CaseProfile::GRADES['leve']['rango'][0], 21,
     'La audición normal en Chile llega a 20 dB HL: el grado leve arranca en 21');

foreach (CaseProfile::SCENARIOS as $clave => $esc) {
    t_true(isset($esc['grados']) && is_array($esc['grados']),
           "Cuadro '{$clave}': declara `grados` (lista vacía si no tiene)");

    foreach ($esc['grados'] as $grado) {
        t_true(isset(CaseProfile::GRADES[$grado]),
               "Cuadro '{$clave}': el grado '{$grado}' existe en GRADES");
        // Alcanzable con margen: si el techo apenas roza el piso del rango,
        // todos los casos de ese grado salen calcados en el mínimo.
        $piso = CaseProfile::GRADES[$grado]['rango'][0];
        t_true(techoBiap($esc) >= $piso + 10,
               sprintf("Cuadro '%s': el grado '%s' (desde %d dB) es alcanzable -- techo %.0f dB",
                       $clave, $grado, $piso, techoBiap($esc)));
    }
}

// El oído sano no tiene grado de hipoacusia: es lo que hace que el select
// quede apagado en vez de ofrecer una lista vacía.
t_eq(CaseProfile::SCENARIOS['normal']['grados'], [],
     "El cuadro 'normal' no tiene grados");

// Techos que son decisiones clínicas, no accidentes de la forma: si alguien
// sube el gap de la conductiva, este test avisa antes que el aula.
foreach (array_keys(array_filter(CaseProfile::SCENARIOS,
         fn ($e) => $e['categoria'] === 'conductiva')) as $cond) {
    t_true(isset(CaseProfile::SCENARIOS[$cond]['max_db']),
           "Conductiva '{$cond}': declara techo (la vía ósea le pone límite al gap)");
    t_true(!in_array('severa', CaseProfile::SCENARIOS[$cond]['grados'], true)
           && !in_array('profunda', CaseProfile::SCENARIOS[$cond]['grados'], true),
           "Conductiva '{$cond}': no llega a severa ni profunda (más que eso ya es mixta)");
    t_eq(CaseProfile::SCENARIOS[$cond]['cce_pct'], [100, 100],
         "Conductiva '{$cond}': la cóclea está sana (cce 100 %)");
}
t_eq(CaseProfile::SCENARIOS['muesca_4k']['grados'], ['leve'],
     'Muesca de 4 kHz: por promedio no pasa de leve, y ese es el punto del cuadro');

// --- El techo de la transmisión -------------------------------------------
// La máxima pérdida que puede dar un oído medio: con la cadena interrumpida
// el sonido sigue entrando por vía ósea y la aérea no baja más. Sin este
// techo, el factor que alcanza el grado escalaba la forma entera y una otitis
// "moderada" salía con 68 dB de gap en 125 Hz (una perforación, con 83).
foreach (CaseProfile::SCENARIOS as $clave => $esc) {
    if ($esc['gap_shape'] === []) {
        t_true(!isset($esc['gap_max_db']),
               "Cuadro '{$clave}': sin gap no declara techo de transmisión");
        continue;
    }
    t_true(isset($esc['gap_max_db']),
           "Cuadro '{$clave}': declara `gap_max_db` (techo del gap por frecuencia)");
    t_true($esc['gap_max_db'] <= CaseProfile::GAP_MAX_DB,
           sprintf("Cuadro '%s': el techo del gap (%s dB) no pasa de GAP_MAX_DB (%d dB)",
                   $clave, $esc['gap_max_db'], CaseProfile::GAP_MAX_DB));
    // El techo tiene que ser alcanzable por la forma del cuadro: uno que no
    // lo roza nunca no lo está declarando, lo está decorando.
    $escalaGap = ($esc['gap_scale'][0] + $esc['gap_scale'][1]) / 2;
    t_true(max($esc['gap_shape']) * $escalaGap <= $esc['gap_max_db'],
           sprintf("Cuadro '%s': la forma base del gap (%.0f dB) no arranca ya sobre su techo (%s dB)",
                   $clave, max($esc['gap_shape']) * $escalaGap, $esc['gap_max_db']));

    // Y el grado más alto que declara no puede exigir más gap que el techo:
    // eso es exactamente lo que comprueba techoBiap() incluyendo $porGap.
    foreach ($esc['grados'] as $grado) {
        $piso = CaseProfile::GRADES[$grado]['rango'][0];
        $gapNecesario = max($esc['gap_shape']) * techoBiap($esc)
                      / max(1e-9, array_sum(array_map(
                            fn ($hz) => ($esc['sn_shape'][$hz] ?? 0) + ($esc['gap_shape'][$hz] ?? 0),
                            CaseProfile::GRADE_FREQS)) / count(CaseProfile::GRADE_FREQS));
        t_true($gapNecesario <= techoGapDe($esc) + 0.01,
               sprintf("Cuadro '%s', grado '%s' (desde %d dB): el gap que necesita (%.0f dB) cabe en el techo (%.0f dB)",
                       $clave, $grado, $piso, $gapNecesario, techoGapDe($esc)));
    }
}

// La disyunción de cadena es LA conductiva máxima: si alguien le sube el gap
// a otro cuadro por encima de ella, este test avisa.
foreach (CaseProfile::SCENARIOS as $clave => $esc) {
    if ($esc['gap_shape'] === [] || $esc['categoria'] !== 'conductiva') { continue; }
    t_true($esc['gap_max_db'] <= CaseProfile::SCENARIOS['disyuncion_cadena']['gap_max_db'],
           "Conductiva '{$clave}': no atenúa más que una cadena interrumpida");
}

// --- El eje vestibular de los cuadros -------------------------------------

// Todo cuadro con `vemp` tiene que declarar una patología del catálogo, y
// las dos formas de umbral (rango por subtipo / atado al gap) son
// excluyentes: mezclarlas dejaría dos fuentes para el mismo número.
foreach (CaseProfile::SCENARIOS as $escKey => $esc) {
    if (!isset($esc['vemp'])) {
        continue;
    }
    $vempCfg = $esc['vemp'];
    t_true(in_array($vempCfg['type'] ?? '', CaseBuilder::VEMP_TYPE_OPTIONS, true),
        "Cuadro {$escKey}: la patología VEMP está en el catálogo");
    t_true(!(isset($vempCfg['umbral']) && !empty($vempCfg['umbral_gap'])),
        "Cuadro {$escKey}: el umbral del VEMP sale del rango o del gap, no de los dos");
    foreach ((array) ($vempCfg['umbral'] ?? []) as $vempSub => $rango) {
        t_true(in_array($vempSub, CaseBuilder::VEMP_SUBTIPOS, true),
            "Cuadro {$escKey}: '{$vempSub}' es un subtipo de VEMP que existe");
        t_true(is_array($rango) && count($rango) === 2 && $rango[0] <= $rango[1],
            "Cuadro {$escKey}/{$vempSub}: el rango de umbral va de menor a mayor");
    }
}

// El schwannoma nace del nervio vestibular: no puede salir con VEMP normal.
t_eq(CaseProfile::SCENARIOS['schwannoma']['vemp']['type'], 'neural',
    'El schwannoma vestibular desarma el VEMP');
// Y la ANSD al revés: el VEMP conservado es el hallazgo que la separa de un
// compromiso del VIII completo.
t_eq(CaseProfile::SCENARIOS['neuropatia']['vemp']['type'], 'normal',
    'La ANSD deja el VEMP conservado a propósito');

// Un caso con patrón retro y el VEMP declarado normal a propósito ya no se
// reclama: es lo que arma el generador para la ANSD.
$ansd = [
    'Perfil' => [
        'version' => 1,
        'OD' => ['cce_pct' => 5.0, 'retro' => ['iii_v_ms' => 0.8] + CaseBuilder::ABR_NEURAL_DEFAULTS],
        'OI' => ['cce_pct' => 100.0, 'retro' => CaseBuilder::ABR_NEURAL_DEFAULTS],
        'auto' => [],
    ],
    'VEMP' => ['OD' => ['type' => 'normal', 'decidido' => true], 'OI' => ['type' => 'normal']],
];
$faltanAnsd = CaseCompleteness::pendingTexts($ansd);
t_true(strpos(implode(' ', $faltanAnsd), 'VEMP OD') === false,
    'Un VEMP normal marcado como decidido no se reclama (es el hallazgo de la ANSD)');

// --- Ejes de acúfeno y de conciencia --------------------------------------

foreach (CaseProfile::SCENARIOS as $escKey => $esc) {
    if (isset($esc['tinnitus'])) {
        $tinCfg = $esc['tinnitus'];
        t_true($tinCfg['prob'] > 0 && $tinCfg['prob'] <= 1,
            "Cuadro {$escKey}: la probabilidad de acúfeno es una probabilidad");
        t_true(!empty($tinCfg['ruido']), "Cuadro {$escKey}: hay al menos un tipo de ruido");
        foreach ($tinCfg['ruido'] as $tinRuido) {
            t_true(in_array($tinRuido, CaseBuilder::TINNITUS_RUIDO_OPTIONS, true),
                "Cuadro {$escKey}: '{$tinRuido}' está en el catálogo de ruidos");
        }
        foreach ($tinCfg['frecuencia'] as $tinHz) {
            t_true(in_array($tinHz, CaseBuilder::FREQUENCIES, true),
                "Cuadro {$escKey}: {$tinHz} Hz es una frecuencia del audiómetro");
        }
        t_true($tinCfg['permanente'] >= 0 && $tinCfg['permanente'] <= 1,
            "Cuadro {$escKey}: la probabilidad de permanente es una probabilidad");
        // Pulsátil es opcional y solo lo declara el cuadro que lo explica
        // (una masa vascular): sin la clave el generador lo deja apagado.
        if (isset($tinCfg['pulsatil'])) {
            t_true($tinCfg['pulsatil'] > 0 && $tinCfg['pulsatil'] <= 1,
                "Cuadro {$escKey}: la probabilidad de pulsátil es una probabilidad");
        }
    }
    if (isset($esc['conciencia'])) {
        $conc = $esc['conciencia'];
        t_true(count($conc) === 2 && $conc[0] <= $conc[1] && $conc[0] >= 0 && $conc[1] <= 100,
            "Cuadro {$escKey}: el rango de conciencia va de menor a mayor dentro de 0-100");
    }
}

// El acúfeno pulsátil no se sortea en cualquier cuadro: es el hallazgo de
// una masa vascular, y repartirlo le sacaría el valor que tiene.
$conPulsatil = array_keys(array_filter(CaseProfile::SCENARIOS,
    fn ($e) => isset($e['tinnitus']['pulsatil'])));
t_eq($conPulsatil, ['glomus_timpanico'],
    'Solo el glomus declara acúfeno pulsátil');

// Ningún cuadro puede prometer acúfeno siempre: dos casos del mismo cuadro
// tienen que poder salir uno con y otro sin, o el alumno memoriza la
// asociación en vez de preguntarla.
foreach (CaseProfile::SCENARIOS as $escKey => $esc) {
    t_true(!isset($esc['tinnitus']) || $esc['tinnitus']['prob'] < 1.0,
        "Cuadro {$escKey}: el acúfeno nunca es seguro");
}

// Los cuadros de instalación lenta bajan la conciencia y los bruscos la
// suben: es lo que hace que el paciente conteste "yo escucho bien".
t_true(CaseProfile::SCENARIOS['presbiacusia']['conciencia'][1]
     < CaseProfile::SCENARIOS['subita']['conciencia'][0],
    'La presbiacusia deja menos conciencia del problema que la súbita');

// --- Oído sano de un chico: cero clavado ----------------------------------

// A esta edad un oído normal oye en 0 dB HL en todas las frecuencias y no
// hay otra forma. La dispersión de 0 a 15 dB que trae la audiometría del
// adulto es envejecimiento temprano, ruido y otitis viejas: cosas que este
// paciente todavía no tuvo. El corte va donde arranca ISO 7029.
t_eq(CaseProfile::EDAD_AUDICION_PERFECTA, 18,
    'El cero clavado llega hasta donde arranca la norma por edad');
$normaChico = CaseProfile::ageNorm(CaseProfile::EDAD_AUDICION_PERFECTA - 1, 0);
t_close(array_sum(array_map('floatval', $normaChico)), 0.0, 0.001,
    'Bajo esa edad la norma por edad no suma nada en ninguna frecuencia');

// El generador vive en JS y esto no lo puede correr, pero sí puede exigir
// que use la MISMA constante y no una copia suya (mismo criterio que
// test_charts_vs_js): el día que alguien cambie la edad en un solo lado,
// falla acá y no en el aula.
$genJs = (string) @file_get_contents(dirname(__DIR__) . '/public/js/case/generator.js');
t_true(strpos($genJs, 'edadAudicionPerfecta') !== false,
    'El generador JS lee la edad desde CASE_CONST');
t_true(strpos($genJs, 'esCeroClavado') !== false,
    'Y tiene la regla del cero clavado');
$crear = (string) @file_get_contents(dirname(__DIR__) . '/public/admin/case_create.php');
t_true(strpos($crear, "'edadAudicionPerfecta' => CaseProfile::EDAD_AUDICION_PERFECTA") !== false,
    'case_create la expone en CASE_CONST');
