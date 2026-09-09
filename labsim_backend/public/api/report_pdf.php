<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/ReportFile.php';
require_once __DIR__ . '/../../src/ReportPdfBuilder.php';

/**
 * Sirve el PDF de un informe (?id=). Bearer auth -- dueño del informe
 * (mismo student_id de la atención) o docente/admin (permission 777, puede
 * ver el de cualquier alumno). Si el archivo no está en disco (ej. falló
 * la generación al subir, ver report_upload.php) lo reconstruye al vuelo
 * desde reports.data + las imágenes que sí se hayan guardado.
 */

$user = Auth::requireUser();

$reportId = (int) ($_GET['id'] ?? 0);
if ($reportId <= 0) {
    Response::error('Falta id.', 400);
}

$pdo = Db::get();
$stmt = $pdo->prepare(
    'SELECT r.id, r.tipo, r.data, a.student_id, ap.rut, ap.nombre, ap.apellido, ap.fecha_nac
     FROM reports r
     JOIN attendances a ON a.id = r.attendance_id
     JOIN appointments ap ON ap.id = a.appointment_id
     WHERE r.id = ?'
);
$stmt->execute([$reportId]);
$report = $stmt->fetch();

if (!$report) {
    Response::error('Informe no encontrado.', 404);
}
if ((int) $report['student_id'] !== (int) $user['id'] && (int) $user['permission'] !== 777) {
    Response::error('No autorizado.', 403);
}

$pdfPath = ReportFile::pdfPath($reportId);
if (!is_file($pdfPath)) {
    $stmt = $pdo->prepare('SELECT display_name FROM users WHERE id = ?');
    $stmt->execute([$report['student_id']]);
    $evaluatorName = (string) ($stmt->fetchColumn() ?: 'N/D');

    $data = json_decode((string) $report['data'], true) ?: [];
    $patient = [
        'rut' => $report['rut'],
        'nombre' => $report['nombre'],
        'apellido' => $report['apellido'],
        'fecha_nac' => $report['fecha_nac'],
    ];
    try {
        $pdfBytes = ReportPdfBuilder::build($reportId, (string) $report['tipo'], $data, $patient, $evaluatorName, date('d-m-Y'));
        file_put_contents($pdfPath, $pdfBytes);
    } catch (Throwable $e) {
        Response::error('No se pudo generar el PDF: ' . $e->getMessage(), 500);
    }
}

header('Content-Type: application/pdf');
header('Content-Disposition: inline; filename="informe_' . $reportId . '.pdf"');
header('Cache-Control: private, max-age=300');
readfile($pdfPath);
