<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

// Snapshot completo para sembrar el cache local del admin al loguearse
// (después de esto, el admin usa sync.php como todos).

[, $platformId, $contextId] = Auth::requireAdminWithSession();
$courseId = $platformId !== null ? Lti::courseForLaunch($platformId, $contextId) : null;
$pdo = Db::get();

$students = $pdo->query(
    "SELECT id, username, display_name, permission, active FROM users WHERE role = 'student'"
)->fetchAll();

// Identidad del paciente junto al caso: la app de escritorio arma con esto
// las filas "sin agendar" de la agenda (casos sin cita, ver
// backend_state_to_shedule). NUNCA se seleccionan comentario_docente ni
// historia_clinica de patients -- eso no sale del panel admin.
$cases = $pdo->query(
    'SELECT c.id, c.data, c.updated_at,
            p.rut AS paciente_rut, p.nombre AS paciente_nombre,
            p.apellido AS paciente_apellido, p.fecha_nac AS paciente_fecha_nac
       FROM cases c
       LEFT JOIN patients p ON p.id = c.patient_id'
)->fetchAll();
foreach ($cases as &$c) {
    $c['data'] = json_decode($c['data'], true);
}
unset($c);

$appointments = Db::castAppointments($pdo->query('SELECT * FROM appointments')->fetchAll());
$attendances = $pdo->query('SELECT * FROM attendances')->fetchAll();

// Config efectiva (override del curso resuelto si existe, si no el default
// global) -- ver AppConfig::getEffective(). Un docente (permission 555) que
// entró por LTI a un curso ve la config de ESE curso, no el default a secas.
$config = [];
foreach (AppConfig::allKeys($courseId) as $k) {
    $config[] = ['k' => $k, 'v' => AppConfig::getEffective($k, $courseId)];
}

Response::json([
    'server_time' => (new DateTime())->format('Y-m-d H:i:s'),
    'students' => $students,
    'cases' => $cases,
    'appointments' => $appointments,
    'attendances' => $attendances,
    'config' => $config,
]);
