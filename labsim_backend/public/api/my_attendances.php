<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Metrics.php';

/**
 * Historial de pacientes atendidos por el alumno logueado (vista propia,
 * dentro de la app -- equivalente en alcance a la tabla "Atenciones" de
 * admin/student.php, pero scopeada al propio token en vez de a un
 * student_id arbitrario que solo un docente puede pedir).
 *
 * GET -> lista de atenciones cerradas ('atendido') propias, con stats de
 * comportamiento por atención (mismo criterio que Metrics::buildSessions,
 * agrupado por appointment_id).
 */

$user = Auth::requireUser();
$pdo = Db::get();

$stmt = $pdo->prepare(
    "SELECT att.nota, att.hora_real, att.updated_at,
            a.id AS appointment_id, a.fecha, a.hora, a.nombre, a.apellido, a.procedimiento, a.case_id
     FROM attendances att
     JOIN appointments a ON a.id = att.appointment_id
     WHERE att.student_id = ? AND att.estado = 'atendido'
     ORDER BY att.updated_at DESC"
);
$stmt->execute([$user['id']]);
$attendances = $stmt->fetchAll();

$stmt = $pdo->prepare('SELECT user_id, client_ts, action, payload FROM action_logs WHERE user_id = ? ORDER BY id');
$stmt->execute([$user['id']]);
$allLogs = Metrics::decodeLogs($stmt->fetchAll());
$sessions = Metrics::buildSessions($allLogs);

$sessionsByAppt = [];
foreach ($sessions as $s) {
    if ($s['appointment_id'] === null) {
        continue;
    }
    $sessionsByAppt[(int) $s['appointment_id']][] = $s;
}

$stmt = $pdo->prepare(
    'SELECT appointment_id, COUNT(*) AS n FROM llm_chat_logs WHERE student_id = ? GROUP BY appointment_id'
);
$stmt->execute([$user['id']]);
$chatCounts = [];
foreach ($stmt->fetchAll() as $row) {
    $chatCounts[(int) $row['appointment_id']] = (int) $row['n'];
}

$items = [];
foreach ($attendances as $a) {
    $apptId = (int) $a['appointment_id'];
    $group = $sessionsByAppt[$apptId] ?? [];
    $items[] = [
        'appointment_id' => $apptId,
        'fecha' => $a['fecha'],
        'hora' => $a['hora'],
        'nombre' => $a['nombre'],
        'apellido' => $a['apellido'],
        'procedimiento' => $a['procedimiento'],
        'case_id' => $a['case_id'],
        'nota' => $a['nota'],
        'hora_real' => $a['hora_real'],
        'updated_at' => $a['updated_at'],
        'n_chat_messages' => $chatCounts[$apptId] ?? 0,
        'stats' => Metrics::summarizeSessions($group),
    ];
}

Response::json(['items' => $items]);
