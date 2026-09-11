<?php

declare(strict_types=1);

require_once __DIR__ . '/bootstrap.php';

/**
 * Renueva la sesión de portal (docente/admin o alumno) y dice cuánto le
 * queda. Lo llama js/session_guard.js: al tocar "Seguir conectado" en el
 * aviso de vencimiento, y cada tanto mientras la persona esté realmente
 * escribiendo -- así una ficha larga no se cae por inactividad, pero
 * irse del computador sí cierra la sesión.
 *
 * startSession() ya es quien renueva (escribe last_activity) y quien vacía
 * la sesión si se pasó del límite: acá solo se informa el resultado.
 */

header('Content-Type: application/json; charset=utf-8');

Auth::startSession();

if (!Auth::hasPortalSession()) {
    http_response_code(401);
    echo json_encode(['ok' => false, 'quedan' => 0]);
    exit;
}

// Sin CSRF a propósito: no cambia ningún dato y ya exige la cookie de
// sesión; pedir el token obligaría a filtrarlo a las dos plantillas de
// portal para algo que solo mueve el reloj de la propia sesión.
echo json_encode(['ok' => true, 'quedan' => Auth::sessionSecondsLeft()]);
