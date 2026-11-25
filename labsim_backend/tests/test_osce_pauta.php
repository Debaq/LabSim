<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/OscePauta.php';

/**
 * Estación de pauta docente del OSCE: interelectrodo, puntaje por ítem,
 * ítems críticos y pautas precargadas desde el Protocolo Técnico ORL 2019.
 */

// -- Interelectrodo -----------------------------------------------------
$c = OscePauta::impedancias(['3,2', '1.5', '4', '2.8'], 5.0, 2.0);
t_true($c['completo'], 'Cuatro valores: completo');
t_eq([$c['max'], $c['min'], $c['inter']], [4.0, 1.5, 2.5], 'Interelectrodo = mayor − menor (4 − 1,5 = 2,5)');
t_eq($c['ok_abs'], true, 'Todos bajo 5 kΩ');
t_eq($c['ok_inter'], false, '2,5 kΩ de diferencia no cumple < 2');
t_eq(count($c['pares']), 6, 'Cuatro electrodos: 6 pares');
t_eq($c['pares'][0], [0, 1, 1.7], 'Par blanco–negro: 3,2 − 1,5 = 1,7');

$c = OscePauta::impedancias([4.9, 5.0, 3], 5.0, 2.0);
t_eq([$c['fuera'], $c['ok_abs']], [[1], false], 'Justo en el límite (5,0) no cumple "bajo 5"');

$c = OscePauta::impedancias(['2', '', '3'], 5.0, 2.0);
t_eq([$c['completo'], $c['ok_abs'], $c['ok_inter'], $c['inter']], [false, null, null, 1.0],
     'Con un cable sin anotar no se juzga, pero ya muestra la diferencia');

$c = OscePauta::impedancias(['8', '11.5', '9'], 12.0, null);
t_eq([$c['ok_abs'], $c['ok_inter']], [true, null], 'AABR: bajo 12 kΩ y sin límite de interelectrodo');

t_eq(OscePauta::kohm('abc'), null, 'Texto no es kΩ');
t_eq(OscePauta::kohm(' 2,35 '), 2.35, 'Coma decimal');
t_eq(OscePauta::kohm('-1'), null, 'Negativo no vale');

// -- Puntaje por ítem -----------------------------------------------------
$tick = ['tipo' => 'tick', 'puntaje' => 2, 'critico' => 0];
t_eq(OscePauta::evaluarItem($tick, 'cumple')['puntaje'], 2.0, 'Cumple = completo');
t_eq(OscePauta::evaluarItem($tick, 'parcial')['puntaje'], 1.0, 'Parcial = la mitad');
t_eq(OscePauta::evaluarItem($tick, 'no_cumple')['puntaje'], 0.0, 'No cumple = 0');
t_eq(OscePauta::evaluarItem($tick, '')['marcado'], false, 'Sin marcar');
t_eq(OscePauta::evaluarItem($tick, 'no_cumple')['critico_fallado'], false, 'No crítico: no reprueba');
$critico = ['tipo' => 'tick', 'puntaje' => 1, 'critico' => 1];
t_eq(OscePauta::evaluarItem($critico, 'no_cumple')['critico_fallado'], true, 'Crítico en no cumple reprueba');
t_eq(OscePauta::evaluarItem($critico, 'parcial')['critico_fallado'], false, 'Crítico en parcial no reprueba');

$si = ['tipo' => 'si_no', 'puntaje' => 2, 'critico' => 1];
t_eq(OscePauta::evaluarItem($si, 'cumple')['puntaje'], 2.0, 'Dicotómico: sí = completo');
$r = OscePauta::evaluarItem($si, 'no_cumple');
t_eq([$r['puntaje'], $r['critico_fallado']], [0.0, true], 'Dicotómico crítico en no: 0 y reprueba');
t_eq(OscePauta::evaluarItem($si, 'parcial')['marcado'], false, 'Dicotómico no tiene parcial');
t_eq(array_column(OscePauta::opciones($si), 'rotulo'), ['Sí', 'No'], 'Dicotómico se ve como Sí / No');
$esc = ['tipo' => 'escala', 'puntaje' => 3, 'critico' => 0, 'cfg' => ['niveles' => [3 => 'a', 2 => 'b', 1 => 'c', 0 => 'd']]];
t_eq(array_map(static fn ($v) => OscePauta::evaluarItem($esc, $v)['puntaje'], ['n3', 'n2', 'n1', 'n0']), [3.0, 2.0, 1.0, 0.0],
     'Escala: cada nivel vale su tercio');
t_eq(OscePauta::opciones($esc)[1], ['v' => 'n2', 'rotulo' => 'Mayormente logrado', 'frac' => 2 / 3, 'desc' => 'b'], 'Escala con su descriptor');
t_eq(OscePauta::rotuloValor($esc, 'n0'), 'No logrado', 'Rótulo de lo marcado');
$e = OscePauta::limpiarItem(['texto' => 'Global', 'tipo' => 'escala', 'puntaje' => '3', 'niveles' => "3: Todo\n2: Casi\n1: Poco\n0: Nada"]);
t_eq(json_decode($e['config'], true)['niveles'], ['3' => 'Todo', '2' => 'Casi', '1' => 'Poco', '0' => 'Nada'], 'Editor: descriptores sin el número');
$err = null;
try { OscePauta::limpiarItem(['texto' => 'x', 'tipo' => 'escala', 'niveles' => "a\nb"]); } catch (InvalidArgumentException $ex) { $err = $ex->getMessage(); }
t_true($err !== null && strpos($err, '4 descriptores') !== false, 'Escala sin los 4 descriptores no se guarda');

$imp = ['tipo' => 'impedancias', 'puntaje' => 2, 'critico' => 1,
        'cfg' => ['electrodos' => ['B', 'N', 'R', 'A'], 'max_kohm' => 5, 'inter_kohm' => 2]];
t_eq(OscePauta::evaluarItem($imp, [3, 3.5, 4, 2.5])['puntaje'], 2.0, 'Impedancias bien: completo');
t_eq(OscePauta::evaluarItem($imp, [3, 1, 4.5, 2.5])['puntaje'], 1.0, 'Bajo 5 pero 3,5 de diferencia: la mitad');
$r = OscePauta::evaluarItem($imp, [8, 1, 9, 2]);
t_eq([$r['puntaje'], $r['critico_fallado']], [0.0, true], 'Ninguna: 0 y, si es crítico, reprueba');
$r = OscePauta::evaluarItem($imp, [3, 3]);
t_eq([$r['puntaje'], $r['marcado']], [0.0, false], 'Faltan cables: sin puntaje y sin marcar');
t_eq(OscePauta::evaluarItem($imp, [3, 3.5, 4, 2.5, 99])['puntaje'], 2.0, 'Valores de más se ignoran');

// -- Pautas del protocolo -----------------------------------------------
$peatc = OscePauta::pautaBase('peatc');
$impItem = array_values(array_filter($peatc, static fn ($i) => $i['tipo'] === 'impedancias'))[0];
t_eq([$impItem['config']['max_kohm'], $impItem['config']['inter_kohm']], [5.0, 2.0], 'PEATC: < 5 kΩ e interelectrodo < 2');
t_eq(count($impItem['config']['electrodos']), 4, 'PEATC: blanco, negro, rojo y azul');
t_true(strpos($impItem['config']['electrodos'][0], 'Blanco') === 0 && strpos($impItem['config']['electrodos'][0], 'Vértex') !== false,
       'PEATC: blanco en vértex');
$textos = implode("\n", array_column($peatc, 'texto'));
t_true(strpos($textos, 'una sola dirección') !== false, 'PEATC: gel abrasivo en una sola dirección');
t_true(strpos($textos, 'decúbito dorsal') !== false, 'PEATC: decúbito dorsal');
t_true(strpos($textos, 'rojo en OD, azul en OI') !== false, 'PEATC: fono rojo OD, azul OI');
t_true(count(array_filter($peatc, static fn ($i) => $i['critico'])) >= 2, 'PEATC: lavado de manos y montaje son críticos');
t_eq(array_count_values(array_column($peatc, 'tipo')), ['si_no' => 10, 'escala' => 2, 'tick' => 1, 'impedancias' => 1],
     'PEATC: pasos dicotómicos, comunicación y desempeño global en escala');
t_eq(array_sum(array_column($peatc, 'puntaje')), 19.0, 'PEATC: 19 puntos');

$ov = OscePauta::montaje('ovemp');
t_eq([$ov['max_kohm'], $ov['inter_kohm']], [3.0, 1.0], 'oVEMP: < 3 kΩ e interelectrodo < 1');
t_eq(OscePauta::montaje('cvemp')['electrodos'][1], ['Activo', 'Unión esternoclavicular'], 'cVEMP: activo como lo escribe el protocolo');
t_eq(OscePauta::montaje('aabr')['max_kohm'], 12.0, 'AABR (GSI): bajo 12 kΩ');
t_eq(OscePauta::montaje('estado_estable')['max_kohm'], 3.0, 'Estado estable: idealmente bajo 3 kΩ');
t_true(strpos(OscePauta::montaje('ecochg')['fuente'], 'No está en el Protocolo') === 0, 'ECochG avisa que no viene del protocolo');
t_eq(OscePauta::montaje('general'), OscePauta::montaje('peatc'), 'Examen sin montaje propio: el del PEATC');
foreach (array_keys(Osce::EXAMENES) as $ex) {
    t_true(count(OscePauta::pautaBase($ex)) >= 10, "Hay pauta precargada para {$ex}");
}

// -- Editor ---------------------------------------------------------------
$it = OscePauta::limpiarItem(['texto' => 'Impedancias', 'tipo' => 'impedancias', 'puntaje' => '2',
                              'electrodos' => "Blanco · Vértex\n\nNegro · Ceja\nRojo", 'max_kohm' => '5', 'inter_kohm' => '']);
$cfg = json_decode($it['config'], true);
t_eq([count($cfg['electrodos']), $cfg['max_kohm'], $cfg['inter_kohm']], [3, 5.0, null], 'Un electrodo por línea; interelectrodo vacío = sin límite');
$falla = false;
try {
    OscePauta::limpiarItem(['texto' => 'x', 'tipo' => 'impedancias', 'electrodos' => 'solo uno', 'max_kohm' => '5']);
} catch (InvalidArgumentException $e) {
    $falla = true;
}
t_true($falla, 'Impedancias con un solo electrodo se rechaza');
