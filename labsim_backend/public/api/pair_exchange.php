<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

$body = json_decode(file_get_contents('php://input'), true) ?? [];
$code = trim((string) ($body['code'] ?? ''));

if (!preg_match('/^\d{6}$/', $code)) {
    Response::error('Código inválido', 400);
}

$result = Auth::exchangePairingCode($code);
if ($result === null) {
    Response::error('Código inválido, ya usado o expirado', 404);
}

Response::json($result);
