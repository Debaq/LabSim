<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Osce.php';

/**
 * Estado del reloj de un OSCE, para el proyector (osce_vivo.php), la página
 * del QR del alumno (student/osce.php) y las estaciones.
 *
 * Sin sesión a propósito: el alumno llega desde el QR sin cuenta abierta y
 * las tablets de estación no tienen login. Se entra con un token largo
 * aleatorio, del OSCE (?r=) o del alumno (?t=). No devuelve nombres: solo
 * tiempos, títulos de estación y, con ?t=, el código y recorrido de ese
 * alumno.
 */

header('Cache-Control: no-store');

$t = (string) ($_GET['t'] ?? '');
$r = (string) ($_GET['r'] ?? '');

if ($t !== '') {
    $p = Osce::participantePorToken($t);
    $o = $p !== null ? Osce::obtener((int) $p['osce_id']) : null;
    if ($p === null || $o === null) {
        Response::error('Código no encontrado.', 404);
    }
    Response::json(Osce::estadoPublico($o, $p));
}

if ($r !== '' && preg_match('/^[0-9a-f]{24}$/', $r)) {
    $o = Osce::porRelojToken($r);
    if ($o !== null) {
        Response::json(Osce::estadoPublico($o));
    }
}

Response::error('OSCE no encontrado.', 404);
