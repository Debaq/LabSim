<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Historial de informes (ABR/EOA/VEMP/electrococleo) del alumno logueado --
 * una fila por atención+tipo, más reciente primero. Mismo alcance que
 * my_attendances.php pero para `reports` en vez de `attendances`: el
 * cliente (o el futuro portal web) usa esto para listar "mis informes" y
 * arma la URL de descarga como /api/report_pdf.php?id=<id>.
 */

$user = Auth::requireUser();
$pdo = Db::get();

$stmt = $pdo->prepare(
    "SELECT r.id, r.tipo, r.created_at, r.updated_at,
            a.id AS attendance_id, a.estado,
            ap.id AS appointment_id, ap.fecha, ap.nombre, ap.apellido, ap.procedimiento
     FROM reports r
     JOIN attendances a ON a.id = r.attendance_id
     JOIN appointments ap ON ap.id = a.appointment_id
     WHERE a.student_id = ?
     ORDER BY r.updated_at DESC"
);
$stmt->execute([$user['id']]);

Response::json(['reports' => $stmt->fetchAll()]);
