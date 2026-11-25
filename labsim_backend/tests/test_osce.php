<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Osce.php';
require_once __DIR__ . '/../src/QrSvg.php';

/**
 * OSCE (docs/osce_plan.md): reparto en vueltas, recorrido de cada puesto,
 * reloj, nota con exigencia, códigos y QR. Todo cálculo puro, sin base.
 */

// -- Vueltas: 17 alumnos, 6 estaciones, 1 circuito = 6 + 6 + 5 -----------
$plan = Osce::planVueltas(17, 6, 1);
t_eq(count($plan), 17, 'Un lugar por alumno');
$porVuelta = array_count_values(array_column($plan, 'vuelta'));
t_eq($porVuelta, [0 => 6, 1 => 6, 2 => 5], '17 en 6 puestos: 6 + 6 + 5');
$puestosV0 = array_column(array_filter($plan, static fn ($a) => $a['vuelta'] === 0), 'puesto');
sort($puestosV0);
t_eq($puestosV0, [0, 1, 2, 3, 4, 5], 'En una vuelta llena cada puesto tiene un alumno');

// Vueltas parejas aunque sobre poco: 13 en 6 puestos = 5 + 4 + 4, no 6 + 6 + 1.
$p13 = array_count_values(array_column(Osce::planVueltas(13, 6, 1), 'vuelta'));
t_eq($p13, [0 => 5, 1 => 4, 2 => 4], 'Vueltas parejas: 5 + 4 + 4');

// Dos circuitos: 17 en 12 puestos = 2 vueltas (9 + 8), sin repetir puesto en un circuito.
$p2 = Osce::planVueltas(17, 6, 2);
t_eq(array_count_values(array_column($p2, 'vuelta')), [0 => 9, 1 => 8], 'Dos circuitos: 9 + 8');
$claves = array_map(static fn ($a) => $a['vuelta'] . '-' . $a['circuito'] . '-' . $a['puesto'], $p2);
t_eq(count(array_unique($claves)), 17, 'Nadie comparte puesto en la misma vuelta y circuito');
t_eq(Osce::planVueltas(0, 6, 1), [], 'Sin alumnos, sin plan');

// -- Recorrido: cada puesto pasa por todas las estaciones una vez ---------
for ($puesto = 0; $puesto < 6; $puesto++) {
    $vistas = [];
    for ($slot = 0; $slot < 6; $slot++) {
        $vistas[] = Osce::estacionEn($puesto, $slot, 6);
    }
    sort($vistas);
    t_eq($vistas, [0, 1, 2, 3, 4, 5], "El puesto {$puesto} pasa por las 6 estaciones");
}
// En un mismo tiempo, dos puestos nunca están en la misma estación.
for ($slot = 0; $slot < 6; $slot++) {
    $en = [];
    for ($puesto = 0; $puesto < 6; $puesto++) {
        $en[] = Osce::estacionEn($puesto, $slot, 6);
    }
    t_eq(count(array_unique($en)), 6, "Tiempo {$slot}: una estación por puesto");
}

// -- Reloj: 6 estaciones, 3 vueltas, 8 min + 2 min, 10 min entre vueltas --
$cfg = ['estaciones' => 6, 'vueltas' => 3, 'duracion_s' => 480, 'pausa_s' => 120, 'pausa_vueltas_s' => 600];
$r = Osce::estadoReloj($cfg, -30);
t_eq([$r['fase'], $r['restante_s']], ['antes', 30], 'Antes de partir');
$r = Osce::estadoReloj($cfg, 0);
t_eq([$r['fase'], $r['vuelta'], $r['slot'], $r['restante_s']], ['estacion', 0, 0, 480], 'Parte la primera estación');
$r = Osce::estadoReloj($cfg, 479);
t_eq([$r['fase'], $r['restante_s']], ['estacion', 1], 'Último segundo de la estación');
$r = Osce::estadoReloj($cfg, 480);
t_eq([$r['fase'], $r['slot'], $r['restante_s']], ['cambio', 0, 120], 'Cambio de 2 minutos');
$r = Osce::estadoReloj($cfg, 600);
t_eq([$r['fase'], $r['slot']], ['estacion', 1], 'Segunda estación a los 10 min');
// Fin de la sexta estación de la vuelta 1 (5×600 + 480 = 3480): la pausa de
// cambio y la de vuelta son un solo descanso de 2 + 10 min.
$r = Osce::estadoReloj($cfg, 3480);
t_eq([$r['fase'], $r['vuelta'], $r['restante_s']], ['entre_vueltas', 0, 720], 'Tras la vuelta 1: 12 min de descanso');
$r = Osce::estadoReloj($cfg, 4200);
t_eq([$r['fase'], $r['vuelta'], $r['slot']], ['estacion', 1, 0], 'Parte la vuelta 2 a los 70 min');
t_eq(Osce::inicioSlot($cfg, 1, 0), 4200, 'inicioSlot coincide con el reloj');
t_eq(Osce::duracionTotal($cfg), 2 * 4200 + 5 * 600 + 480, 'Duración total: 3 vueltas sin la última pausa');
$r = Osce::estadoReloj($cfg, Osce::duracionTotal($cfg));
t_eq($r['fase'], 'terminado', 'Al acabar la última estación, terminado');
$r = Osce::estadoReloj($cfg, Osce::duracionTotal($cfg) - 1);
t_eq([$r['fase'], $r['vuelta'], $r['slot']], ['estacion', 2, 5], 'El último segundo sigue en la última estación');

// Transcurrido descuenta pausas y se congela en pausa.
$o = ['inicio_epoch' => 1000, 'pausado_desde' => null, 'pausado_acum_s' => 50];
t_eq(Osce::transcurrido($o, 1300), 250, 'Transcurrido descuenta la pausa acumulada');
$o['pausado_desde'] = 1200;
t_eq(Osce::transcurrido($o, 5000), 150, 'En pausa, el reloj no avanza');
t_eq(Osce::transcurrido(['inicio_epoch' => null, 'pausado_desde' => null, 'pausado_acum_s' => 0], 5000), null, 'Sin iniciar: null');

// cfgReloj calcula las vueltas igual que planVueltas.
$c = Osce::cfgReloj(['circuitos' => 1, 'duracion_s' => 480, 'pausa_s' => 120, 'pausa_vueltas_s' => 600], 6, 17);
t_eq($c['vueltas'], 3, 'cfgReloj: 17 alumnos en 6 puestos = 3 vueltas');

// -- Nota chilena con exigencia ---------------------------------------
t_eq(Osce::nota(60, 100, 60, 4.0), 4.0, '60 % con exigencia 60 = 4,0');
t_eq(Osce::nota(100, 100, 60, 4.0), 7.0, 'Todo = 7,0');
t_eq(Osce::nota(0, 100, 60, 4.0), 1.0, 'Nada = 1,0');
t_eq(Osce::nota(30, 100, 60, 4.0), 2.5, '30 % = 2,5');
t_eq(Osce::nota(80, 100, 60, 4.0), 5.5, '80 % = 5,5');

// -- Códigos -----------------------------------------------------------
$cod = Osce::nuevoCodigo();
t_true(preg_match('/^[2-9A-HJKMNP-Z]{3}-[2-9A-HJKMNP-Z]{3}$/', $cod) === 1, 'Código sin 0/O/1/I/L: ' . $cod);
t_eq(Osce::normalizarCodigo(' k7f 3qm '), 'K7F-3QM', 'Código escrito a mano se normaliza');
t_eq(Osce::normalizarCodigo('k7f-3qm'), 'K7F-3QM', 'Con guion también');

// -- Configuración -----------------------------------------------------
$cfgForm = Osce::limpiarConfig(['nombre' => 'Práctica', 'inicio_programado' => '2026-12-04T09:00', 'duracion_min' => '8',
    'pausa_min' => '2', 'pausa_vueltas_min' => '10', 'circuitos' => '1', 'exigencia' => '60', 'nota_aprobacion' => '4,0']);
t_eq([$cfgForm['inicio_programado'], $cfgForm['duracion_s'], $cfgForm['pausa_s'], $cfgForm['nota_aprobacion']],
     ['2026-12-04 09:00', 480, 120, 4.0], 'El formulario se pasa a segundos y hora local');
$falla = false;
try {
    Osce::limpiarConfig(['nombre' => 'x', 'duracion_min' => '0']);
} catch (InvalidArgumentException $e) {
    $falla = true;
}
t_true($falla, 'Duración 0 se rechaza');

// -- QR ----------------------------------------------------------------
$m = QrSvg::matriz('https://ejemplo.cl/public/student/osce.php?t=0123456789abcdef01234567');
t_eq(count($m), 17 + 4 * 5, 'URL con token: QR versión 5 (37 módulos)');
t_true($m[0][0] && $m[6][6] && !$m[7][7], 'Patrón buscador arriba a la izquierda');
t_true(strpos(QrSvg::svg('hola'), '<svg') === 0, 'Sale SVG');

// -- Rotación en cadena (2026-11-25): entran de a 2 por estación, en orden --
$oc = ['rotacion' => 'cadena', 'por_turno' => 2, 'circuitos' => 1, 'duracion_s' => 480, 'pausa_s' => 120, 'pausa_vueltas_s' => 600];
$cc = Osce::cfgReloj($oc, 6, 17);
t_eq([$cc['grupos'], $cc['turnos'], $cc['vueltas']], [9, 14, 1], 'Cadena: 17 de a 2 = 9 grupos, 14 turnos, una vuelta');
t_eq(Osce::duracionTotal($cc), 13 * 600 + 480, 'Cadena: 14 turnos de 10 min menos la última pausa');
t_eq([Osce::grupo(1, 2), Osce::grupo(2, 2), Osce::grupo(3, 2), Osce::grupo(17, 2)], [0, 0, 1, 8], 'Grupo por número');
t_eq([Osce::carril(5, 2), Osce::carril(6, 2)], [0, 1], 'Carril dentro del grupo');
t_eq(Osce::ventana($cc, ['numero' => 5], 0), ['slot' => 2, 'inicio_s' => 1200, 'fin_s' => 1680], 'N.º 5 limpia en el turno 3');
t_eq(Osce::ventana($cc, ['numero' => 5], 5)['slot'], 7, 'N.º 5 termina en la estación 6 en el turno 8');
t_eq(Osce::ventana($cc, ['numero' => 17], 5)['slot'], 13, 'El 17 termina en el último turno');
t_eq([Osce::turnoPaciente(1, 9), Osce::turnoPaciente(4, 9)], [0, 3], 'Cada grupo es paciente el turno anterior al suyo');
t_eq(Osce::turnoPaciente(0, 9), 8, 'El primer grupo es paciente del último: se queda hasta el final');
t_eq(Osce::turnoPaciente(0, 1), null, 'Con un solo grupo no hay paciente');
$r = Osce::estadoReloj($cc, 7 * 600 + 100);
t_eq([$r['fase'], $r['vuelta'], $r['slot']], ['estacion', 0, 7], 'Reloj en cadena: turno 8');
t_eq(Osce::estadoReloj($cc, Osce::duracionTotal($cc))['fase'], 'terminado', 'Reloj en cadena: termina');
t_eq(Osce::limpiarConfig(['nombre' => 'x', 'rotacion' => 'cadena', 'por_turno' => '2'])['por_turno'], 2, 'De a cuántos se configura');
