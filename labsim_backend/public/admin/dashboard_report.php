<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Metrics.php';

// Informe de comportamiento (no el dump crudo que ya da logs_download.php):
// sesiones, duración, delta promedio y pausas por semana -- lo que un
// docente necesita para evaluar avance, no la lista de eventos.

$me = Auth::requireAdminSession();
$pdo = Db::get();

$studentId = (int) ($_GET['student_id'] ?? 0);
// Sin filtro de role: mismo motivo que student.php -- un cambio de rol
// posterior no debería tapar el registro histórico.
$stmt = $pdo->prepare('SELECT username, display_name FROM users WHERE id = ?');
$stmt->execute([$studentId]);
$student = $stmt->fetch();

if (!$student) {
    http_response_code(404);
    exit('Alumno no encontrado.');
}

$stmt = $pdo->prepare('SELECT user_id, client_ts, action, payload FROM action_logs WHERE user_id = ? ORDER BY id');
$stmt->execute([$studentId]);
$logs = Metrics::decodeLogs($stmt->fetchAll());
$sessions = Metrics::buildSessions($logs);
$total = Metrics::summarizeSessions($sessions);
$weekly = Metrics::sessionsByWeek($sessions);

$filename = 'informe_' . preg_replace('/[^a-zA-Z0-9_.-]/', '_', $student['username']) . '_' . date('Ymd_His') . '.csv';

header('Content-Type: text/csv; charset=utf-8');
header('Content-Disposition: attachment; filename="' . $filename . '"');

$out = fopen('php://output', 'w');
fputcsv($out, ['alumno', $student['display_name']]);
fputcsv($out, ['sesiones_login_logout', Metrics::countLoginSessions($logs)]);
fputcsv($out, ['atenciones_pacientes_distintos', Metrics::countAttentions($logs)]);
fputcsv($out, ['bloques_actividad', $total['n_sessions']]);
fputcsv($out, ['duracion_total_s', $total['total_duration_s']]);
fputcsv($out, ['delta_promedio_s', $total['avg_delta_s'] ?? '']);
fputcsv($out, ['pausas_largas_ge30s', $total['long_pauses']]);
fputcsv($out, ['acciones_sin_pausa_0s', $total['no_pause_actions']]);
fputcsv($out, []);
fputcsv($out, ['semana', 'bloques', 'delta_promedio_s']);
foreach ($weekly as $week => $w) {
    fputcsv($out, [$week, $w['n_sessions'], $w['avg_delta_s'] ?? '']);
}
fclose($out);
