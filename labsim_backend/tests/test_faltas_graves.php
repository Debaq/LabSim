<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/FaltasGraves.php';

// La sonda en el oído NR: se nombra el oído y la prueba.
$f = FaltasGraves::describir('z_no_realizable', ['screen' => 'tymp', 'side' => 'OD', 'oido_nr' => 'OD', 'que' => 'sonda'], '2026-10-15 10:42:07.123');
t_eq($f['texto'], FaltasGraves::ACCIONES['z_no_realizable'], 'Falta grave: el texto sale de ACCIONES');
t_eq($f['detalle'], 'Sonda en OD, timpanograma', 'Falta grave: detalle de la sonda en el oído NR');
t_eq($f['hora'], '10:42', 'Falta grave: la hora va en HH:MM');

// Contra con la sonda en el sano: el auricular iba en el NR.
$f = FaltasGraves::describir('z_no_realizable', ['screen' => 'reflex', 'side' => 'OI', 'mode' => 'CONTRA', 'oido_nr' => 'OD', 'que' => 'auricular'], '2026-10-15 10:45:00');
t_eq($f['detalle'], 'Sonda en OI, reflejos contra (el auricular iba en OD)', 'Falta grave: contra estimulando por el oído NR');
