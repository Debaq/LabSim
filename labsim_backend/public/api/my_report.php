<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Los informes que el alumno logueado ya guardó en ESTA cita, para que el
 * módulo los recupere al retomar la atención.
 *
 * Desde que los informes se guardan solos mientras se atiende (ver
 * core/report_autosave.py en el cliente), cerrar la app con la atención
 * abierta ya no pierde las curvas: quedan en el servidor. Esto las
 * devuelve para que el módulo vuelva a mostrarlas.
 *
 * GET appointment_id=<la cita>&tipos=ABR,ELECTROCOCLEO (opcional; sin
 * tipos, todos). Solo lo propio: el alumno sale del token.
 */

$user = Auth::requireUser();

$appointmentId = (int) ($_GET['appointment_id'] ?? 0);
if ($appointmentId <= 0) {
    Response::error('Falta appointment_id.', 400);
}

$tipos = array_values(array_filter(array_map('trim', explode(',', (string) ($_GET['tipos'] ?? '')))));

$sql = 'SELECT r.id, r.tipo, r.data, r.updated_at, a.estado
        FROM reports r
        JOIN attendances a ON a.id = r.attendance_id
        WHERE a.appointment_id = ? AND a.student_id = ?';
$params = [$appointmentId, $user['id']];
if ($tipos) {
    $sql .= ' AND r.tipo IN (' . implode(',', array_fill(0, count($tipos), '?')) . ')';
    $params = array_merge($params, $tipos);
}
$sql .= ' ORDER BY r.updated_at DESC, r.id DESC';

$stmt = Db::get()->prepare($sql);
$stmt->execute($params);
$reports = [];
foreach ($stmt->fetchAll() as $row) {
    $row['data'] = json_decode((string) $row['data'], true);
    $reports[] = $row;
}

Response::json(['reports' => $reports]);
