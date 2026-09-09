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
 * appointments y cases son compartidos por defecto (cola común, cita sin
 * curso = todos ven todo, ver comentario sobre `courses` en sql/schema.sql),
 * pero una cita puede quedar acotada a un curso/grupo/alumno puntual -- ahí
 * un alumno solo la ve si le corresponde (ver WHERE de abajo).
 * attendances es el progreso propio de cada uno: el admin ve el de todos
 * (lo necesita para el historial por paciente), el alumno solo el suyo.
 */

[$user, $platformId, $contextId] = Auth::requireUserWithSession();
$courseId = $platformId !== null ? Lti::findCourseForContext($platformId, $contextId) : null;
$since = $_GET['since'] ?? '1970-01-01 00:00:00';
$pdo = Db::get();

if ($user['role'] === 'admin') {
    // Docente/admin en el cliente de escritorio necesita ver todo, sin
    // filtro por curso (mismo criterio que ya usan dashboard.php/agenda.php
    // para el admin completo).
    $stmt = $pdo->prepare('SELECT * FROM appointments WHERE updated_at > ?');
    $stmt->execute([$since]);
} else {
    // PDO no permite mezclar placeholders posicionales y nombrados en la
    // misma query -- :since se repite en vez de usar "?" para $since.
    $stmt = $pdo->prepare(
        'SELECT * FROM appointments WHERE updated_at > :since AND (
            course_id IS NULL
            OR assigned_student_id = :me
            OR assigned_group_id IN (SELECT group_id FROM group_members WHERE user_id = :me)
            OR (assigned_student_id IS NULL AND assigned_group_id IS NULL
                AND course_id IN (SELECT course_id FROM course_students WHERE user_id = :me))
        )'
    );
    $stmt->bindValue(':since', $since);
    $stmt->bindValue(':me', $user['id']);
    $stmt->execute();
}
$appointments = Db::castAppointments($stmt->fetchAll());

// paciente_*: identidad del paciente dueño del caso (patients), que la app
// necesita para mostrar los casos SIN cita en la agenda del docente (ver
// backend_state_to_shedule). Nunca se manda comentario_docente ni
// historia_clinica -- esos no salen del panel admin.
$stmt = $pdo->prepare(
    'SELECT c.id, c.data, c.updated_at,
            p.rut AS paciente_rut, p.nombre AS paciente_nombre,
            p.apellido AS paciente_apellido, p.fecha_nac AS paciente_fecha_nac
       FROM cases c
       LEFT JOIN patients p ON p.id = c.patient_id
      WHERE c.updated_at > ?'
);
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

// Config efectiva (override del curso resuelto si existe, si no el default
// global) -- ver AppConfig::getEffective(). changedKeysSince() solo filtra
// qué keys re-mandar; el valor que se manda siempre es el efectivo, nunca
// la fila cruda (evita que el cliente reciba global y override de la misma
// key sin saber cuál gana).
$config = [];
foreach (AppConfig::changedKeysSince($since, $courseId) as $k) {
    $config[] = ['k' => $k, 'v' => AppConfig::getEffective($k, $courseId)];
}

Response::json([
    'server_time' => (new DateTime())->format('Y-m-d H:i:s'),
    'appointments' => $appointments,
    'cases' => $cases,
    'attendances' => $attendances,
    'config' => $config,
]);
