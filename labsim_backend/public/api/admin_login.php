<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Equipos.php';

$body = json_decode(file_get_contents('php://input'), true) ?? [];
$username = trim((string) ($body['username'] ?? ''));
$password = (string) ($body['password'] ?? '');
$ip = (string) ($_SERVER['REMOTE_ADDR'] ?? 'unknown');

if ($username === '' || $password === '') {
    Response::error('Falta usuario o contraseña', 400);
}

// Mismo rate limit que admin/login.php (panel web) -- este endpoint es el
// login de la app de escritorio y usaba el mismo password sin límite.
if (Auth::loginBlocked($username, $ip)) {
    Response::error('Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo.', 429);
}

$result = Auth::loginAdmin($username, $password);
Auth::recordLoginAttempt($username, $ip, $result !== null);
if ($result === null) {
    Response::error('Usuario o contraseña incorrectos', 401);
}

// Versión de la app en cada equipo (ver admin/versiones.php).
Equipos::registrar($body['equipo'] ?? null, (int) $result['user']['id']);

Response::json($result);
