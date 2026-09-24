<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Sesiones de ABR/electrococleo del alumno logueado con el MISMO paciente
 * de una cita, para que el módulo ABR las liste y deje abrirlas. Solo para
 * mirarlas: una atención cerrada no se actualiza más (ver report_upload.php).
 *
 * GET appointment_id=<la cita en atención>. El paciente es el caso de esa
 * cita (appointments.case_id): sin caso no hay con qué agrupar y la lista
 * sale vacía. La propia cita se excluye -- esa es la sesión en curso, que
 * vive en el cliente hasta que se cierra la atención.
 *
 * Trae `data` completo (curvas con trazos): el cliente las redibuja tal
 * como se registraron.
 */

$user = Auth::requireUser();
$appointmentId = (int) ($_GET['appointment_id'] ?? 0);
if ($appointmentId <= 0) {
    Response::error('Falta appointment_id.', 400);
}

$pdo = Db::get();

$stmt = $pdo->prepare('SELECT case_id FROM appointments WHERE id = ?');
$stmt->execute([$appointmentId]);
$caseId = $stmt->fetchColumn();
if ($caseId === false || $caseId === null || $caseId === '') {
    Response::json(['reports' => []]);
}

$stmt = $pdo->prepare(
    "SELECT r.id, r.tipo, r.data, r.updated_at,
            a.estado,
            ap.id AS appointment_id, ap.fecha, ap.hora
     FROM reports r
     JOIN attendances a ON a.id = r.attendance_id
     JOIN appointments ap ON ap.id = a.appointment_id
     WHERE a.student_id = ? AND ap.case_id = ? AND ap.id <> ?
       AND r.tipo IN ('ABR', 'ELECTROCOCLEO')
     ORDER BY ap.fecha DESC, ap.hora DESC, r.id DESC"
);
$stmt->execute([$user['id'], $caseId, $appointmentId]);

$reports = [];
foreach ($stmt->fetchAll() as $row) {
    $row['data'] = json_decode((string) $row['data'], true);
    $reports[] = $row;
}

Response::json(['reports' => $reports]);
