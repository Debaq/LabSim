<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * El reloj del servidor, para que el cliente pueda compararse con él.
 *
 * Existe por una pregunta que no se podía contestar desde afuera: en qué
 * zona horaria corre el PHP del hosting. El repo no la fija --sale del
 * php.ini-- así que el mismo código daba fechas distintas en el servidor y
 * en desarrollo, y no había forma de verlo sin entrar al servidor.
 *
 * Ahora `bootstrap.php` fija la zona de la aplicación (ver Clock), o sea que
 * el php.ini ya no cambia el comportamiento. Este endpoint informa las dos
 * cosas de todos modos: la zona que manda y la que traía el servidor, para
 * poder confirmar que el pin está puesto y para saber en qué está el
 * hosting.
 *
 * Lo que el cliente hace con esto es COMPARARSE, no ajustarse: las horas de
 * una cita son del curso y no del que las mira (ver el comentario de
 * Clock). Si el reloj del computador está corrido, se avisa; no se
 * reinterpretan las fechas.
 *
 * Pide sesión: es información del servidor y no tiene por qué ser pública.
 */

Auth::requireUserWithSession();

$info = Clock::info($GLOBALS['ZONA_PHP_INI'] ?? null);

// Lo que la base entiende por "ahora", para confirmar que guarda en UTC y
// no en la zona del servidor. Es la otra mitad del problema: si esto no
// coincide con `utc`, las marcas guardadas no son UTC y todas las
// conversiones de la aplicación están corridas.
try {
    $info['base_ahora'] = (string) Db::get()->query('SELECT CURRENT_TIMESTAMP')->fetchColumn();
    $desfase = strtotime($info['base_ahora'] . ' UTC') - $info['epoch'];
    $info['base_desfase_seg'] = $desfase;
    // Un par de segundos es latencia, no un problema de zona.
    $info['base_en_utc'] = abs($desfase) < 120;
} catch (Throwable $e) {
    $info['base_ahora'] = null;
    $info['base_desfase_seg'] = null;
    $info['base_en_utc'] = null;
}

Response::json($info);
