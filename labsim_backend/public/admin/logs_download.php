<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

// Descarga el registro COMPLETO de action_logs de un alumno (no solo las
// últimas 30 que muestra student.php), en CSV, para analizar en detalle
// qué le está llegando al backend y si sobra volumen.

$me = Auth::requireAdminSession();
$pdo = Db::get();

$studentId = (int) ($_GET['id'] ?? 0);
$stmt = $pdo->prepare("SELECT username FROM users WHERE id = ? AND role = 'student'");
$stmt->execute([$studentId]);
$student = $stmt->fetch();

if (!$student) {
    http_response_code(404);
    exit('Alumno no encontrado.');
}

$stmt = $pdo->prepare(
    'SELECT id, client_ts, received_at, action, payload FROM action_logs WHERE user_id = ? ORDER BY id'
);
$stmt->execute([$studentId]);

$filename = 'logs_' . preg_replace('/[^a-zA-Z0-9_.-]/', '_', $student['username']) . '_' . date('Ymd_His') . '.csv';

header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="' . $filename . '"');

$out = fopen('php://output', 'w');
fputcsv($out, ['id', 'client_ts', 'received_at', 'action', 'payload']);
while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
    fputcsv($out, [$row['id'], $row['client_ts'], $row['received_at'], $row['action'], $row['payload']]);
}
fclose($out);
