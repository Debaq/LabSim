<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

// Snapshot completo para sembrar el cache local del admin al loguearse
// (después de esto, el admin usa sync.php como todos).

Auth::requireAdmin();
$pdo = Db::get();

$students = $pdo->query(
    "SELECT id, username, display_name, permission, modules, active FROM users WHERE role = 'student'"
)->fetchAll();

$cases = $pdo->query('SELECT id, data, updated_at FROM cases')->fetchAll();
foreach ($cases as &$c) {
    $c['data'] = json_decode($c['data'], true);
}
unset($c);

$appointments = Db::castAppointments($pdo->query('SELECT * FROM appointments')->fetchAll());
$attendances = $pdo->query('SELECT * FROM attendances')->fetchAll();

$config = $pdo->query('SELECT k, v FROM app_config')->fetchAll();
foreach ($config as &$c) {
    $c['v'] = json_decode($c['v'], true);
}
unset($c);

Response::json([
    'server_time' => (new DateTime())->format('Y-m-d H:i:s'),
    'students' => $students,
    'cases' => $cases,
    'appointments' => $appointments,
    'attendances' => $attendances,
    'config' => $config,
]);
