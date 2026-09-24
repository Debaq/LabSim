<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/UserPrefs.php';

/**
 * Preferencias personales de la app de escritorio (atajos de teclado,
 * mouse para zurdos) del usuario logueado. Ver UserPrefs.php.
 *
 * GET  -> {prefs}
 * POST {prefs} -> guarda y devuelve {prefs} tal como quedó (normalizado).
 */

$user = Auth::requireUser();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $body = json_decode(file_get_contents('php://input'), true);
    if (!is_array($body) || !isset($body['prefs'])) {
        Response::error('Faltan las preferencias.', 400);
    }
    Response::json(['prefs' => UserPrefs::guardar((int) $user['id'], $body['prefs'])]);
}

Response::json(['prefs' => UserPrefs::leer((int) $user['id'])]);
