<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

Auth::requireAdmin();

$body = json_decode(file_get_contents('php://input'), true) ?? [];
$id = (int) ($body['id'] ?? 0);
if ($id <= 0) {
    Response::error('Falta id de la cita', 400);
}

$pdo = Db::get();
$pdo->beginTransaction();
$pdo->prepare('DELETE FROM attendances WHERE appointment_id = ?')->execute([$id]);
$stmt = $pdo->prepare('DELETE FROM appointments WHERE id = ?');
$stmt->execute([$id]);
$deleted = $stmt->rowCount();
$pdo->commit();

if ($deleted === 0) {
    Response::error('Cita no encontrada', 404);
}

Response::json(['ok' => true]);
