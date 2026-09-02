<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

$body = json_decode(file_get_contents('php://input'), true) ?? [];
$code = trim((string) ($body['code'] ?? ''));
$ip = (string) ($_SERVER['REMOTE_ADDR'] ?? 'unknown');

if (!preg_match('/^\d{6}$/', $code)) {
    Response::error('Código inválido', 400);
}

// Sin esto, el código de 6 dígitos (1M combos, TTL 300s) era fuerza-bruteable
// con requests automatizados dentro de esa ventana.
if (Auth::pairExchangeBlocked($ip)) {
    Response::error('Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo.', 429);
}

$result = Auth::exchangePairingCode($code);
Auth::recordPairExchangeAttempt($ip, $result !== null);
if ($result === null) {
    Response::error('Código inválido, ya usado o expirado', 404);
}

Response::json($result);
