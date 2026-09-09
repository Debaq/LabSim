<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

Auth::requireAdmin();

$body = json_decode(file_get_contents('php://input'), true) ?? [];
$id = trim((string) ($body['id'] ?? ''));
$data = $body['data'] ?? null;

if ($id === '' || !is_array($data)) {
    Response::error('Falta id o data del caso', 400);
}

$pdo = Db::get();
$stmt = $pdo->prepare(
    "INSERT INTO cases (id, data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
     ON CONFLICT(id) DO UPDATE SET data = excluded.data, updated_at = CURRENT_TIMESTAMP"
);
$stmt->execute([$id, json_encode($data, JSON_UNESCAPED_UNICODE)]);

Response::json(['ok' => true, 'id' => $id]);
