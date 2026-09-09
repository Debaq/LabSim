<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/HistoriaClinica.php';

/**
 * Línea de tiempo del paciente: atenciones previas del caso + atenciones del
 * alumno, en un solo orden cronológico.
 */

$HISTORIA = "{{-20}} Nace de 38 semanas, 3.240 g. Screening: refiere OD.\n"
          . "{{-5}} Control con pediatra, se deriva a evaluación auditiva.";

// --- resolución de fechas
t_eq(HistoriaClinica::resolverFechas('{{-20}} algo', '10-09-26'), '21-08-2026 algo',
    '{{-20}} son 20 días antes de la cita');
t_eq(HistoriaClinica::resolverFechas('{{0}} hoy', '10-09-26'), '10-09-2026 hoy',
    '{{0}} es el día de la cita');
t_eq(HistoriaClinica::resolverFechas('{{+7}} control', '10-09-26'), '17-09-2026 control',
    'Un offset positivo cae después de la cita');
t_eq(HistoriaClinica::resolverFechas('{{-5}} algo', null), '{{-5}} algo',
    'Sin fecha de cita se deja la llave: mejor eso que inventar una fecha');
t_eq(HistoriaClinica::resolverFechas('{{-5}} algo', 'no-es-fecha'), '{{-5}} algo',
    'Y con una fecha ilegible, igual');

// --- la evolución del alumno va DESPUÉS de las atenciones previas
$linea = HistoriaClinica::lineaTiempo($HISTORIA, '10-09-26', [
    ['fecha' => '10-09-26', 'hora_real' => '09:12:00', 'nota' => 'Se realiza audiometría.'],
]);
t_eq(count($linea), 3, 'Dos atenciones previas más la del alumno');
t_eq($linea[0]['fecha'], '21-08-2026', 'Primero la más antigua del caso');
t_eq($linea[1]['fecha'], '05-09-2026', 'Después la otra previa');
t_true($linea[2]['propia'], 'Y al final la del alumno, que es la más reciente');
t_eq($linea[2]['fecha'], '10-09-2026',
    'Todas las fechas se muestran igual: la agenda guarda dd-MM-yy y la historia dd-MM-yyyy');
t_true(!$linea[0]['propia'] && !$linea[1]['propia'], 'Las del caso no se marcan como propias');
t_eq($linea[0]['texto'], 'Nace de 38 semanas, 3.240 g. Screening: refiere OD.',
    'La fecha se separa del texto para poder mostrarla igual que las del alumno');

// --- el orden por string estaba mal a fin de año
$linea = HistoriaClinica::lineaTiempo('', '05-01-26', [
    ['fecha' => '10-12-25', 'hora_real' => '10:00:00', 'nota' => 'Primera ronda.'],
    ['fecha' => '05-01-26', 'hora_real' => '09:00:00', 'nota' => 'Segunda ronda.'],
]);
t_eq($linea[0]['texto'], 'Primera ronda.',
    'Diciembre va antes que enero -- ordenado como string quedaba al revés');
t_eq($linea[1]['texto'], 'Segunda ronda.', 'Y la segunda ronda después');

// --- dos atenciones el mismo día se ordenan por hora
$linea = HistoriaClinica::lineaTiempo('', '10-09-26', [
    ['fecha' => '10-09-26', 'hora_real' => '15:30:00', 'nota' => 'Tarde.'],
    ['fecha' => '10-09-26', 'hora_real' => '09:00:00', 'nota' => 'Mañana.'],
]);
t_eq($linea[0]['texto'], 'Mañana.', 'Mismo día: manda la hora real');
t_eq($linea[1]['texto'], 'Tarde.', 'Y la de la tarde va después');

// --- casos borde
t_eq(HistoriaClinica::lineaTiempo('', '10-09-26', []), [], 'Sin nada, línea de tiempo vacía');
$linea = HistoriaClinica::lineaTiempo("\n\n{{-3}} Una sola.\n\n", '10-09-26', []);
t_eq(count($linea), 1, 'Las líneas en blanco no generan entradas');

$linea = HistoriaClinica::lineaTiempo("Sin fecha al principio.\n{{-3}} Con fecha.", '10-09-26', []);
t_eq($linea[0]['texto'], 'Sin fecha al principio.',
    'Una línea sin fecha legible va al principio y conserva el orden del docente');

$linea = HistoriaClinica::lineaTiempo($HISTORIA, '10-09-26', [
    ['fecha' => '', 'hora_real' => '', 'nota' => 'Atención sin fecha.'],
]);
t_true($linea[2]['propia'],
    'Una atención del alumno sin fecha legible es la de ahora: va al final, no al principio');
