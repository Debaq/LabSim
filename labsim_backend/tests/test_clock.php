<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Clock.php';
require_once __DIR__ . '/../src/CaseBuilder.php';
require_once __DIR__ . '/../src/LlmUsage.php';

/**
 * El reloj de la aplicación.
 *
 * Lo que estos tests protegen es una sola propiedad, y es la que hacía falta:
 * el resultado NO puede depender de la zona que traiga el php.ini del
 * servidor. Antes dependía, y no había forma de saberlo desde afuera.
 */

// ------------------------------------------------- la zona está declarada

t_true(in_array(Clock::ZONA, DateTimeZone::listIdentifiers(), true),
       'La zona de la aplicación es un identificador válido de zona horaria');
t_eq(Clock::ZONA_ALMACENAMIENTO, 'UTC',
     'Se guarda en UTC: es lo que entrega CURRENT_TIMESTAMP de SQLite');
t_eq(LlmUsage::ZONA_INFORME, Clock::ZONA,
     'La zona del informe de IA es la misma de la aplicación, declarada una sola vez');

// Chile está entre UTC-3 (verano) y UTC-4 (invierno).
$offset = Clock::offsetMinutes();
t_true($offset === -180 || $offset === -240,
       "El desfase es el de Chile, con o sin horario de verano (dio $offset)");

// ----------------------------------------------- pin(): el php.ini no manda

$original = date_default_timezone_get();

// pin() devuelve la que había, que es el único momento en que se puede ver
// qué zona trae el servidor.
date_default_timezone_set('Europe/Madrid');
t_eq(Clock::pin(), 'Europe/Madrid', 'pin() informa la zona que traía el servidor');
t_eq(date_default_timezone_get(), Clock::ZONA, 'pin() deja puesta la de la aplicación');

// Y lo que de verdad importa: el MISMO código da el MISMO resultado sea cual
// sea la zona del hosting. Se prueba con tres servidores imaginarios muy
// separados entre sí -- si alguno se saliera, la fecha de nacimiento de un
// recién nacido cambiaría de día según dónde esté alojado el backend.
$resultados = [];
foreach (['Europe/Madrid', 'Asia/Tokyo', 'UTC', 'Pacific/Kiritimati'] as $hosting) {
    date_default_timezone_set($hosting);
    Clock::pin();
    $resultados[$hosting] = [
        'hoy' => date('d-m-Y'),
        'rn' => CaseBuilder::fechaNacFromHoras(10),
        'local' => Clock::now()->format('Y-m-d H'),
    ];
}
$primero = reset($resultados);
foreach ($resultados as $hosting => $r) {
    t_eq($r, $primero, "El resultado no cambia con el hosting en $hosting");
}

// Y la fecha del recién nacido sale de la zona de la aplicación, no de otra.
Clock::pin();
t_eq(CaseBuilder::fechaNacFromHoras(10),
     Clock::now()->modify('-10 hours')->format('d-m-Y'),
     'La fecha del recién nacido se cuenta en la zona de la aplicación');

// ------------------------------------------------- fromUtc(): lo guardado

// Una marca de la base (UTC) leída en la zona de la aplicación. Se elige una
// hora que cruza el día: a las 02:00 UTC en Chile todavía es el día anterior,
// y confundir eso es exactamente lo que hacía que una atención apareciera
// con fecha de mañana.
$leida = Clock::fromUtc('2026-06-15 02:00:00');
t_eq($leida->format('Y-m-d H:i'), '2026-06-14 22:00',
     'Una marca UTC de la madrugada se lee como la noche anterior en Chile');
t_eq($leida->getTimezone()->getName(), Clock::ZONA,
     'Y viene con la zona de la aplicación puesta');

// ------------------------------------------------------------ info()

$info = Clock::info('Asia/Tokyo');
t_eq($info['php_ini'], 'Asia/Tokyo', 'info() informa la zona del servidor que se le pasa');
t_true($info['php_ini_coincide'] === false, 'Y dice que no coincide con la de la aplicación');
t_eq($info['zona'], Clock::ZONA, 'info() informa la zona de la aplicación');
t_eq($info['almacenamiento'], 'UTC', 'info() informa cómo se guarda');
t_true(abs($info['epoch'] - time()) < 5, 'El epoch de info() es ahora');
// El epoch es lo único absoluto: es con lo que el cliente calcula su
// desfase sin tener que discutir zonas con el servidor.
t_eq(gmdate('Y-m-d H:i:s', $info['epoch']), $info['utc'],
     'El epoch y la hora UTC informada son el mismo instante');

t_eq(Clock::info(Clock::ZONA)['php_ini_coincide'], true,
     'Un servidor ya configurado en la zona de la aplicación se informa como coincidente');

date_default_timezone_set($original);
