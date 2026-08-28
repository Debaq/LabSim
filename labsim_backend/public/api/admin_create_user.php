<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Users.php';

Auth::requireAdmin();

$body = json_decode(file_get_contents('php://input'), true) ?? [];
$role = (string) ($body['role'] ?? 'student');
$username = trim((string) ($body['username'] ?? ''));
$displayName = trim((string) ($body['display_name'] ?? '')) ?: $username;
$password = (string) ($body['password'] ?? '');
$permission = (int) ($body['permission'] ?? ($role === 'admin' ? 777 : 444));
$modules = is_array($body['modules'] ?? null) ? $body['modules'] : ['A', 'Z'];

if (!in_array($role, ['admin', 'student'], true)) {
    Response::error("role debe ser 'admin' o 'student'", 400);
}
if ($username === '' || strlen($password) < 8) {
    Response::error('Falta username o password (mínimo 8 caracteres)', 400);
}

$userId = Users::createOrUpdateLocal($role, $username, $displayName, $password, $permission, $modules);

Response::json(['ok' => true, 'user_id' => $userId]);
