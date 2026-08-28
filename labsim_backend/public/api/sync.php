<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Sync incremental por polling. El cliente manda la última marca de tiempo
 * que ya tiene (`since`) y recibe solo lo que cambió desde entonces.
 * Con 14 clientes y polling cada ~15s esto es liviano para hosting compartido;
 * evita mantener conexiones abiertas (websockets/long-poll) que ese tipo de
 * hosting no siempre soporta bien.
 *
 * appointments y cases son compartidos (cola común, todos ven todo).
 * attendances es el progreso propio de cada uno: el admin ve el de todos
 * (lo necesita para el historial por paciente), el alumno solo el suyo.
 */

$user = Auth::requireUser();
$since = $_GET['since'] ?? '1970-01-01 00:00:00';
$pdo = Db::get();

$stmt = $pdo->prepare('SELECT * FROM appointments WHERE updated_at > ?');
$stmt->execute([$since]);
$appointments = Db::castAppointments($stmt->fetchAll());

$stmt = $pdo->prepare('SELECT id, data, updated_at FROM cases WHERE updated_at > ?');
$stmt->execute([$since]);
$cases = $stmt->fetchAll();
foreach ($cases as &$c) {
    $c['data'] = json_decode($c['data'], true);
}
unset($c);

$attendanceSql = 'SELECT * FROM attendances WHERE updated_at > ?';
$attendanceParams = [$since];
if ($user['role'] !== 'admin') {
    $attendanceSql .= ' AND student_id = ?';
    $attendanceParams[] = $user['id'];
}
$stmt = $pdo->prepare($attendanceSql);
$stmt->execute($attendanceParams);
$attendances = $stmt->fetchAll();

$stmt = $pdo->prepare('SELECT k, v, updated_at FROM app_config WHERE updated_at > ?');
$stmt->execute([$since]);
$config = $stmt->fetchAll();
foreach ($config as &$c) {
    $c['v'] = json_decode($c['v'], true);
}
unset($c);

Response::json([
    'server_time' => (new DateTime())->format('Y-m-d H:i:s'),
    'appointments' => $appointments,
    'cases' => $cases,
    'attendances' => $attendances,
    'config' => $config,
]);
