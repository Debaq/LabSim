<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * El cliente NUNCA hace streaming de logs (eso colgaba la app). En vez de
 * eso junta eventos localmente y sube lotes cada cierto tiempo. Este
 * endpoint solo recibe el lote y lo inserta en una sola transacción.
 */

$user = Auth::requireUser();
$body = json_decode(file_get_contents('php://input'), true) ?? [];
$entries = $body['entries'] ?? [];

if (!is_array($entries) || $entries === []) {
    Response::error('Lote vacío', 400);
}
if (count($entries) > 500) {
    Response::error('Lote demasiado grande (máx 500)', 400);
}

$pdo = Db::get();
$stmt = $pdo->prepare(
    'INSERT INTO action_logs (user_id, client_ts, action, payload) VALUES (?, ?, ?, ?)'
);

$pdo->beginTransaction();
foreach ($entries as $entry) {
    $stmt->execute([
        $user['id'],
        $entry['ts'] ?? date('Y-m-d H:i:s'),
        (string) ($entry['action'] ?? 'unknown'),
        isset($entry['payload']) ? json_encode($entry['payload'], JSON_UNESCAPED_UNICODE) : null,
    ]);
}
$pdo->commit();

Response::json(['inserted' => count($entries)]);
