<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/ReportFile.php';
require_once __DIR__ . '/../../src/ReportPdfBuilder.php';

/**
 * PDF de un informe (?id=) para el docente desde el navegador: mismo PDF
 * que api/report_pdf.php, pero autenticado por sesión de admin en vez de
 * Bearer (el navegador del docente no tiene token de app).
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();

$reportId = (int) ($_GET['id'] ?? 0);
if ($reportId <= 0) {
    http_response_code(400);
    exit('Falta id.');
}

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
    http_response_code(404);
    exit('Informe no encontrado.');
}

$pdfPath = ReportFile::pdfPath($reportId);
if (!is_file($pdfPath)) {
    $stmt = $pdo->prepare('SELECT display_name FROM users WHERE id = ?');
    $stmt->execute([(int) $report['student_id']]);
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
        http_response_code(500);
        exit('No se pudo generar el PDF: ' . htmlspecialchars($e->getMessage()));
    }
}

header('Content-Type: application/pdf');
header('Content-Disposition: inline; filename="informe_' . $reportId . '.pdf"');
header('Cache-Control: private, max-age=300');
readfile($pdfPath);
