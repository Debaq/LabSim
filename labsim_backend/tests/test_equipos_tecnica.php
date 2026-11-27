<?php

declare(strict_types=1);

/**
 * Técnica de otoscopía, diapasones e impedanciometría (EquiposTecnica):
 * cada equipo se evalúa solo si se usó, cada prueba de la Z solo si se hizo
 * en algún oído, y las reglas siguen los capítulos H1, H2 y H7 del libro.
 */

require_once dirname(__DIR__) . '/src/EquiposTecnica.php';

/** Registro de una atención: [segundo, acción, payload]. */
function eq_logs(array $filas, string $dia = '2026-11-20'): array
{
    $out = [];
    foreach ($filas as [$s, $accion, $p]) {
        $out[] = ['client_ts' => $dia . ' 10:' . sprintf('%02d:%02d', intdiv($s, 60), $s % 60) . '.000', 'action' => $accion,
            'payload' => $p + ['appointment_id' => 5, 'case_id' => 1, 'con_paciente' => true]];
    }
    return $out;
}

function eq_reglas(?array $sec): array
{
    $out = [];
    foreach ($sec['reglas'] ?? [] as $r) {
        $out[$r['texto']] = $r['cumple'];
    }
    foreach ($sec['oidos'] ?? [] as $o => $rr) {
        foreach ($rr as $r) {
            $out[$o . ' · ' . $r['texto']] = $r['cumple'];
        }
    }
    return $out;
}

function eq_busca(array $reglas, string $frag)
{
    foreach ($reglas as $t => $c) {
        if (strpos($t, $frag) !== false) {
            return $c;
        }
    }
    return 'no está';
}

/** Caso adulto: oídos sanos, reflejos a 85 dB, Rinne positivo, Weber centrado. */
function eq_caso(array $extra = []): array
{
    $fila = array_fill(0, 15, [10, 10]);
    return $extra + [
        'edad' => 40, 'Aerea_mkg' => $fila, 'Osea_mkg' => $fila, 'Aerea' => $fila, 'Osea' => $fila,
        'Z_OD' => 'A', 'Z_OI' => 'A', 'ETF' => ['Normal', 'Normal'],
        'Reflex' => ['ipsi' => array_fill(0, 4, [85, 85]), 'contra' => array_fill(0, 5, [90, 90])],
        'Rinne' => ['500' => ['od' => 'positivo', 'oi' => 'positivo']], 'Weber' => ['500' => 'centrado'],
    ];
}

// ---- sin usar ningún equipo: nada ------------------------------------------------
$r = EquiposTecnica::evaluar([], eq_caso());
t_eq([$r['otoscopia'], $r['acumetria'], $r['impedanciometria']], [null, null, null], 'Equipos: sin usarlos no se evalúan (no descuenta no hacerlos)');

// ---- otoscopía -------------------------------------------------------------------------
$vista = static function (string $oido, bool $correcta, string $especulo = 'adulto', int $edad = 40): array {
    return ['oido' => $oido, 'especulo' => $especulo, 'traccion' => true, 'traccion_correcta' => $correcta,
        'traccion_calidad' => $correcta ? 'buena' : 'mala', 'edad' => $edad, 'hay_foto' => true];
};
$bien = eq_logs([
    [0, 'ot_instruccion', ['clave' => 'explicar_otoscopia']],
    [5, 'ot_otoscopio', $vista('od', true)],
    [20, 'ot_otoscopio', $vista('oi', true)],
]);
$r = EquiposTecnica::evaluar($bien, eq_caso(), ['informe_otoscopia' => ['od' => ['cae' => ['cae_normal']], 'oi' => []]]);
t_eq($r['otoscopia']['puntaje']['pct'], 100, 'Otoscopía: explicar, traccionar bien, espéculo de adulto, los dos oídos');
t_eq($r['acumetria'], null, 'Otoscopía sola: los diapasones no se evalúan');
$mal = eq_logs([
    [5, 'ot_otoscopio', $vista('oi', false, 'adulto', 4)],
    [6, 'ot_especulo_grande', ['oido' => 'oi', 'edad' => 4]],
]);
$rr = eq_reglas(EquiposTecnica::evaluar($mal, eq_caso(['edad' => 4]))['otoscopia']);
t_eq(eq_busca($rr, 'explica'), false, 'Otoscopía: sin explicar');
t_eq(eq_busca($rr, 'dos oídos'), false, 'Otoscopía: un solo oído');
t_eq(eq_busca($rr, 'OI · Se tracciona'), false, 'Otoscopía: sin tracción correcta');
t_eq(eq_busca($rr, 'OI · Se usa el espéculo'), false, 'Otoscopía: espéculo de adulto en un niño de 4 años');
// Empezar por el oído sano cuando se sabe cuál está alterado
$rr = eq_reglas(EquiposTecnica::evaluar($bien, eq_caso(['Z_OD' => 'NR']))['otoscopia']);
t_eq(eq_busca($rr, 'menos probablemente'), false, 'Otoscopía: empezó por el oído alterado (OD no realizable)');
$rr = eq_reglas(EquiposTecnica::evaluar($bien, eq_caso(['Z_OI' => 'NR']))['otoscopia']);
t_eq(eq_busca($rr, 'menos probablemente'), true, 'Otoscopía: empezó por el oído sano');
// Lo informado contra la imagen de la biblioteca
$rr = eq_reglas(EquiposTecnica::evaluar($bien, eq_caso(), [
    'informe_otoscopia' => ['od' => ['cuadrantes' => ['posterior_inferior' => ['perforation']]], 'oi' => ['cae' => ['cae_normal']]],
    'tipos_otoscopia' => ['od' => 'perforacion', 'oi' => 'cerumen']])['otoscopia']);
t_eq(eq_busca($rr, 'OD · El informe dice'), true, 'Otoscopía: informó la perforación de la imagen');
t_eq(eq_busca($rr, 'OI · El informe dice'), false, 'Otoscopía: no informó el cerumen de la imagen');

// ---- diapasones ----------------------------------------------------------------------
$apoyo = static function (string $zona, ?string $oido, string $hz = '500'): array {
    return ['hz' => $hz, 'zona' => $zona, 'oido' => $oido, 'vibrando' => true, 'oye' => true];
};
$preg = static function (string $clave, string $zona, ?string $oido): array {
    return ['clave' => $clave, 'zona' => $zona, 'oido' => $oido, 'retirado' => false];
};
$acu = eq_logs([
    [0, 'ot_otoscopio', $vista('od', true)],
    [10, 'ac_instruccion', ['clave' => 'explicar_diapasones', 'zona' => null]],
    [12, 'ac_golpe', ['hz' => '500']],
    [13, 'ac_apoyo', $apoyo('linea_media', 'frente')],
    [15, 'ac_pregunta', $preg('donde_mas_fuerte', 'linea_media', 'frente')],
    [20, 'ac_golpe', ['hz' => '500']],
    [21, 'ac_apoyo', $apoyo('pabellon', 'od')],
    [24, 'ac_apoyo', $apoyo('mastoides', 'od')],
    [26, 'ac_pregunta', $preg('donde_mas_fuerte', 'mastoides', 'od')],
    [30, 'ac_golpe', ['hz' => '500']],
    [31, 'ac_apoyo', $apoyo('pabellon', 'oi')],
    [34, 'ac_apoyo', $apoyo('mastoides', 'oi')],
    [36, 'ac_pregunta', $preg('donde_mas_fuerte', 'mastoides', 'oi')],
]);
$r = EquiposTecnica::evaluar($acu, eq_caso(), ['informe_otoscopia' => ['acumetria' => ['rinne' => ['500' => ['od' => 'positivo', 'oi' => 'positivo']], 'weber' => ['500' => 'centrado']]]]);
t_eq($r['acumetria']['puntaje']['pct'], 100, 'Diapasones: técnica del libro completa y lo anotado calza');
$rr = eq_reglas(EquiposTecnica::evaluar($acu, eq_caso(), ['informe_otoscopia' => ['acumetria' => ['weber' => ['500' => 'od']]]])['acumetria']);
t_eq(eq_busca($rr, 'Lo anotado'), false, 'Diapasones: anotó un Weber que el paciente no dijo');
// Rinne antes que Weber, un solo oído, golpes distintos para aire y hueso
$malAcu = eq_logs([
    [12, 'ac_golpe', ['hz' => '500']],
    [13, 'ac_apoyo', $apoyo('pabellon', 'od')],
    [20, 'ac_golpe', ['hz' => '500']],
    [21, 'ac_apoyo', $apoyo('mastoides', 'od')],
    [30, 'ac_golpe', ['hz' => '500']],
    [31, 'ac_apoyo', $apoyo('fuera_de_linea', 'od')],
]);
$sec = EquiposTecnica::evaluar($malAcu, eq_caso())['acumetria'];
$rr = eq_reglas($sec);
t_eq(eq_busca($rr, 'Weber va primero'), false, 'Diapasones: partió por el Rinne');
t_eq(eq_busca($rr, 'línea media (frente'), false, 'Diapasones: Weber a un lado de la línea media');
t_eq(eq_busca($rr, 'Rinne en los dos oídos'), false, 'Diapasones: aire y hueso con golpes distintos no es un Rinne');
t_true(in_array('Usó los diapasones sin otoscopía en esta atención: un tapón o una efusión cambian el resultado.', $sec['observaciones'], true), 'Diapasones: sin otoscopía es advertencia');
// Rinne por el oído al que fue el Weber
$lat = eq_caso(['Weber' => ['500' => 'oi']]);
$rr = eq_reglas(EquiposTecnica::evaluar($acu, $lat)['acumetria']);
t_eq(eq_busca($rr, 'parte por el oído al que fue el Weber'), false, 'Diapasones: Weber a OI y el Rinne partió por OD');

// ---- impedanciometría ------------------------------------------------------------------
$click = static function (string $screen, string $side, array $extra = []): array {
    return ['screen' => $screen, 'side' => $side] + $extra;
};
$refl = static function (string $side, string $mode, string $freq, int $db): array {
    return ['screen' => 'reflex', 'side' => $side, 'mode' => $mode, 'freq' => $freq, 'dB' => $db];
};
$z = [
    [0, 'ot_otoscopio', $vista('od', true)],
    [10, 'z_instruccion', ['clave' => 'explicar_examen']],
    [11, 'z_instruccion', ['clave' => 'sonidos_fuertes']],
];
$s = 20;
foreach (['OD', 'OI'] as $side) {
    $z[] = [$s++, 'z_stimulus_click', $click('tymp', $side)];
    foreach (['IPSI' => 85, 'CONTRA' => 90] as $mode => $umbral) {
        foreach (ImpedanciometriaTecnica::FRECUENCIAS as $f) {
            foreach ([80, 85, 90] as $db) {
                if ($db - 5 >= $umbral) {
                    break;
                }
                $z[] = [$s++, 'z_stimulus_click', $refl($side, $mode, $f, $db)];
            }
        }
    }
}
$r = EquiposTecnica::evaluar(eq_logs($z), eq_caso());
t_eq($r['impedanciometria']['puntaje']['pct'], 100, 'Z: timpanograma y reflejos completos, de 5 en 5 hasta el umbral');
t_true(in_array('No hizo reflejos estapediales.', $r['impedanciometria']['observaciones'], true) === false, 'Z: con reflejos no se advierte que faltan');
// Solo timpanometría: los reflejos no descuentan, se advierten
$soloT = eq_logs([[0, 'ot_otoscopio', $vista('od', true)], [10, 'z_instruccion', ['clave' => 'explicar_examen']],
    [20, 'z_stimulus_click', $click('tymp', 'OD')], [30, 'z_stimulus_click', $click('tymp', 'OI')]]);
$sec = EquiposTecnica::evaluar($soloT, eq_caso())['impedanciometria'];
t_eq($sec['puntaje']['pct'], 100, 'Z: solo timpanometría en los dos oídos cumple lo que se hizo');
t_true(in_array('No hizo reflejos estapediales.', $sec['observaciones'], true), 'Z: sin reflejos es advertencia');
// Timpanograma en un solo oído realizable
$uno = eq_logs([[20, 'z_stimulus_click', $click('tymp', 'OD')]]);
$rr = eq_reglas(EquiposTecnica::evaluar($uno, eq_caso())['impedanciometria']);
t_eq(eq_busca($rr, 'OI · Timpanograma'), false, 'Z: falta el timpanograma de OI');
$rr = eq_reglas(EquiposTecnica::evaluar($uno, eq_caso(['Z_OI' => 'NR']))['impedanciometria']);
t_eq(eq_busca($rr, 'OI · Timpanograma'), 'no está', 'Z: en el oído NR no se pide nada');
// Medición bloqueada por falta de sello no cuenta como timpanograma
$sinSello = eq_logs([[20, 'z_stimulus_click', $click('tymp', 'OD')], [20, 'z_sin_sello', ['screen' => 'tymp', 'side' => 'OD', 'que' => 'sin_sonda']],
    [30, 'z_stimulus_click', $click('tymp', 'OI')]]);
$rr = eq_reglas(EquiposTecnica::evaluar($sinSello, eq_caso())['impedanciometria']);
t_eq(eq_busca($rr, 'OD · Timpanograma'), false, 'Z: sin sello no hay timpanograma');
// Saltos de 10 dB y umbral no encontrado: dos errores distintos
$saltos = eq_logs([[20, 'z_stimulus_click', $click('tymp', 'OD')], [30, 'z_stimulus_click', $refl('OD', 'IPSI', '1000', 70)],
    [31, 'z_stimulus_click', $refl('OD', 'IPSI', '1000', 80)], [32, 'z_stimulus_click', $refl('OD', 'IPSI', '1000', 100)]]);
$b = ImpedanciometriaTecnica::busqueda(array_column(array_map(static function ($x) { return ['dB' => $x]; }, [70, 80, 100]), null), 85);
t_eq([$b['pasos'], $b['llego']], [false, false], 'Z: subir de 10 en 10 y pasar 15 dB sobre el umbral');
$b = ImpedanciometriaTecnica::busqueda([['dB' => 80], ['dB' => 85]], 85);
t_eq([$b['pasos'], $b['llego']], [true, true], 'Z: 80 → 85 con umbral 85');
$b = ImpedanciometriaTecnica::busqueda([['dB' => 80], ['dB' => 90], ['dB' => 95], ['dB' => 100]], null);
t_eq([$b['pasos'], $b['llego']], [false, true], 'Z: sin reflejo, llegó a 100 pero con un salto de 10');
// Instrucciones: antes del 31-10 la app no las tenía
$viejo = EquiposTecnica::evaluar(eq_logs([[20, 'z_stimulus_click', $click('tymp', 'OD')]], '2026-10-09'), eq_caso())['impedanciometria'];
t_eq(eq_busca(eq_reglas($viejo), 'explica el examen'), 'no está', 'Z: antes del 31-10 no se exigen las instrucciones');
t_eq($viejo['observaciones'] === [] || strpos(implode(' ', $viejo['observaciones']), 'otoscopía') === false, true, 'Z: antes del 06-11 no se pide otoscopía (no estaba en la app)');
// Función tubaria según la membrana
$etf = static function (string $prueba, string $side, array $extra = []): array {
    return ['prueba' => $prueba, 'side' => $side] + $extra;
};
$rr = eq_reglas(EquiposTecnica::evaluar(eq_logs([[20, 'z_etf_test', $etf('perforada', 'OD', ['pressure' => -200])]]),
    eq_caso(['ETF' => ['Permeable', 'Normal']]))['impedanciometria']);
t_eq(eq_busca($rr, 'trompa corresponde'), true, 'Z: membrana perforada, prueba de perforada');
$rr = eq_reglas(EquiposTecnica::evaluar(eq_logs([[20, 'z_etf_test', $etf('perforada', 'OD', ['pressure' => -200])]]), eq_caso())['impedanciometria']);
t_eq(eq_busca($rr, 'trompa corresponde'), false, 'Z: membrana íntegra, prueba de perforada');
$rr = eq_reglas(EquiposTecnica::evaluar(eq_logs([[20, 'z_etf_test', $etf('integra', 'OD', ['maniobra' => 'toynbee'])]]), eq_caso())['impedanciometria']);
t_eq(eq_busca($rr, 'basal'), false, 'Z: maniobra sin timpanograma basal');
// Deterioro donde no hay reflejo, a 2 kHz
$sinRefl = eq_caso(['Reflex' => ['ipsi' => array_fill(0, 4, [130, 130]), 'contra' => array_fill(0, 5, [130, 130])]]);
$rr = eq_reglas(EquiposTecnica::evaluar(eq_logs([[20, 'z_stimulus_click', ['screen' => 'decay', 'side' => 'OD', 'mode' => 'CONTRA', 'freq' => '2000', 'dB' => 100]]]), $sinRefl)['impedanciometria']);
t_eq(eq_busca($rr, 'donde hay reflejo'), false, 'Z: deterioro sin reflejo');
t_eq(eq_busca($rr, 'en 500 o 1000'), false, 'Z: deterioro en 2 kHz');

// ---- lo que muestra la foto (cargado por el docente en la ficha) --------------------
$h = CaseBuilder::otoscopiaHallazgos(['normal' => '1', 'cae' => ['cae_cerumen'], 'cuadrantes' => ['posterior_inferior' => ['perforation']]]);
t_eq([$h['cae'], $h['cuadrantes'], $h['definida']], [['cae_normal'], [], true], 'Ficha otoscopía: "Normal" deja conducto normal y sin hallazgos');
$h = CaseBuilder::otoscopiaHallazgos(['cuadrantes' => ['posterior_inferior' => ['perforation', 'inventado'], 'otro' => ['tube']], 'cae' => ['cae_otorrhea', 'x']]);
t_eq([$h['cuadrantes'], $h['cae']], [['posterior_inferior' => ['perforation']], ['cae_otorrhea']], 'Ficha otoscopía: solo claves conocidas');
t_eq(CaseBuilder::otoscopiaHallazgos(null)['definida'], false, 'Ficha otoscopía: vacío = sin describir');
$verdadCaso = eq_caso(['Otoscopia' => ['fases' => [['texto' => '']], 'hallazgos' => [
    'od' => ['cuadrantes' => ['posterior_inferior' => ['perforation']], 'cae' => ['cae_otorrhea'], 'texto' => 'Perforación posteroinferior con otorrea'],
    'oi' => ['normal' => true],
]]]);
$inf = ['od' => ['cuadrantes' => ['anterior_inferior' => ['perforation']], 'cae' => ['cae_normal'], 'observaciones' => 'perforación'],
    'oi' => ['cae' => ['cae_normal']]];
$sec = EquiposTecnica::evaluar($bien, $verdadCaso, ['informe_otoscopia' => $inf])['otoscopia'];
$od = array_values(array_filter($sec['oidos']['OD'], static function ($r) { return strpos($r['texto'], 'El informe dice') === 0; }))[0];
t_eq(round($od['logro'], 2), 0.5, 'Otoscopía: encontró la perforación y no la otorrea (1 de 2)');
t_true(strpos($od['detalle'], 'Encontró 1 de 2') === 0, 'Otoscopía: el alumno ve cuántos encontró, no cuáles');
t_true(strpos($od['detalle_docente'], 'Perforación (PI)') !== false && strpos($od['detalle_docente'], 'Docente: "Perforación') !== false, 'Otoscopía: el docente ve cuadrantes y textos');
$oi = array_values(array_filter($sec['oidos']['OI'], static function ($r) { return strpos($r['texto'], 'El informe dice') === 0; }))[0];
t_eq($oi['cumple'], true, 'Otoscopía: oído normal informado sin hallazgos');
$inf['oi'] = ['cuadrantes' => ['toda' => ['retraction']]];
$sec = EquiposTecnica::evaluar($bien, $verdadCaso, ['informe_otoscopia' => $inf])['otoscopia'];
$oi = array_values(array_filter($sec['oidos']['OI'], static function ($r) { return strpos($r['texto'], 'El informe dice') === 0; }))[0];
t_eq($oi['cumple'], false, 'Otoscopía: marcó un hallazgo en un oído normal');
$rr = eq_reglas($sec);
t_eq(eq_busca($rr, 'menos probablemente'), false, 'Otoscopía: con la ficha cargada, OD es el alterado y empezó por OD');
