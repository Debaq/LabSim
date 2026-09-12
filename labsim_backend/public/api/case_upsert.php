<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

$user = Auth::requireAdmin();

$body = json_decode(file_get_contents('php://input'), true) ?? [];
$id = trim((string) ($body['id'] ?? ''));
$data = $body['data'] ?? null;

if ($id === '' || !is_array($data)) {
    Response::error('Falta id o data del caso', 400);
}

$pdo = Db::get();
// Autoría de la ficha (la muestra admin/patients.php): created_by/created_at
// solo en el INSERT -- un caso que ya existía conserva a su creador, la app
// solo mueve la última edición.
$stmt = $pdo->prepare(
    "INSERT INTO cases (id, data, updated_at, created_at, created_by, updated_by)
         VALUES (?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, ?, ?)
     ON CONFLICT(id) DO UPDATE SET data = excluded.data, updated_at = CURRENT_TIMESTAMP,
         updated_by = excluded.updated_by"
);
$stmt->execute([$id, json_encode($data, JSON_UNESCAPED_UNICODE), (int) $user['id'], (int) $user['id']]);

Response::json(['ok' => true, 'id' => $id]);
