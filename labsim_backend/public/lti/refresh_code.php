<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

// Llamado por el JS de launch.php (botón "Generar código nuevo" y al vencer
// el contador). No hay forma de reenviar un launch LTI firmado desde JS del
// navegador -- $refreshKey identifica el mismo (state) o (consumer_key,
// nonce) que ya validó el launch original, así que solo hace falta mirar
// esa fila para saber a qué alumno emitirle el código, igual que un replay.
$body = json_decode(file_get_contents('php://input'), true) ?? [];
$key = (string) ($body['key'] ?? '');

[$kind, $rest] = array_pad(explode(':', $key, 2), 2, '');

$row = null;
$mark = null;
if ($kind === 'state') {
    $row = Lti::findLaunchByState($rest);
    $mark = static fn (string $code, int $userId) => Lti::markStateCode($rest, $userId, $code);
} elseif ($kind === 'nonce') {
    [$consumerKey, $nonce] = array_pad(explode('|', $rest, 2), 2, '');
    $row = Lti::findLaunchByNonce($consumerKey, $nonce);
    $mark = static fn (string $code, int $userId) => Lti::markNonceCode($consumerKey, $nonce, $userId, $code);
}

if ($row === null || $row['user_id'] === null) {
    Response::error('Sesión vencida, vuelve a abrir la actividad desde la plataforma.', 410);
}

$userId = (int) $row['user_id'];
$issued = Auth::codeForLaunch($userId, $row['issued_code']);
if ($issued['renewed']) {
    $mark($issued['code'], $userId);
}

Response::json([
    'code' => $issued['code'],
    'expires_in' => Auth::secondsUntil($issued['expires_at']),
]);
