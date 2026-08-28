<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

$body = json_decode(file_get_contents('php://input'), true) ?? [];
$username = trim((string) ($body['username'] ?? ''));
$password = (string) ($body['password'] ?? '');

if ($username === '' || $password === '') {
    Response::error('Falta usuario o contraseña', 400);
}

$result = Auth::loginAdmin($username, $password);
if ($result === null) {
    Response::error('Usuario o contraseña incorrectos', 401);
}

Response::json($result);
