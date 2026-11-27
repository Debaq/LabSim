<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Clock.php';
require_once __DIR__ . '/../src/AgendaAvance.php';

// Plazo del horario libre: el primer día de práctico posterior.
$practicos = ['30-11-26', '07-12-26', '01-12-26'];
t_eq(AgendaAvance::plazo('30-11-26', $practicos), '2026-12-01', 'AgendaAvance::plazo: el práctico siguiente');
t_eq(AgendaAvance::plazo('27-11-26', $practicos), '2026-11-30', 'AgendaAvance::plazo: desde un día sin práctico');
t_eq(AgendaAvance::plazo('07-12-26', $practicos), null, 'AgendaAvance::plazo: sin práctico agendado todavía');

// Cómo terminó un pendiente.
t_eq(AgendaAvance::estadoPendiente('2026-11-30', '2026-12-01', '2026-12-05'), 'a_tiempo', 'estadoPendiente: atendido antes del plazo');
t_eq(AgendaAvance::estadoPendiente('2026-12-01', '2026-12-01', '2026-12-05'), 'fuera_de_plazo', 'estadoPendiente: atendido el día del práctico siguiente = fuera');
t_eq(AgendaAvance::estadoPendiente(null, '2026-12-01', '2026-12-01'), 'vencido', 'estadoPendiente: sin atender al llegar el plazo');
t_eq(AgendaAvance::estadoPendiente(null, '2026-12-01', '2026-11-30'), 'abierto', 'estadoPendiente: todavía con plazo');
t_eq(AgendaAvance::estadoPendiente(null, null, '2026-12-30'), 'abierto', 'estadoPendiente: sin práctico siguiente no vence');

// Inicio local: hora_real UTC del día del cierre, en la hora de Chile.
$ini = AgendaAvance::inicioLocal('14:20:00', '2026-11-30 14:55:00');
t_eq($ini ? $ini->format('Y-m-d H:i') : null, '2026-11-30 11:20', 'inicioLocal: 14:20 UTC = 11:20 en Chile (verano, UTC-3)');
$ini = AgendaAvance::inicioLocal('23:50:00', '2026-12-01 00:20:00');
t_eq($ini ? $ini->format('Y-m-d H:i') : null, '2026-11-30 20:50', 'inicioLocal: atención que cruzó la medianoche UTC');
