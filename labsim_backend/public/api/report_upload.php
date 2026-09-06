<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/ReportFile.php';
require_once __DIR__ . '/../../src/ReportPdfBuilder.php';

/**
 * Sube (o rehace) el informe de un módulo "de examen" (ABR/EOA/VEMP/
 * electrococleo) para una atención propia -- ver tabla `reports` en
 * schema.sql. multipart/form-data:
 *   attendance_id (int), tipo (string), data (JSON string),
 *   image_0 / image_1 / image_lat_int (archivos JPEG, todos opcionales --
 *   el módulo manda los que tenga).
 *
 * Mientras attendances.estado siga 'atendiendo' esto es un upsert libre
 * (el alumno puede rehacer el informe cuantas veces quiera). Una vez
 * 'atendido' queda fijo -- rechaza con 409 en vez de sobreescribir.
 */

const REPORT_TIPOS = ['ABR', 'EOA', 'VEMP', 'ELECTROCOCLEO'];
const REPORT_IMAGE_SUFFIXES = ['0', '1', 'lat_int'];

$user = Auth::requireUser();

$attendanceId = (int) ($_POST['attendance_id'] ?? 0);
$tipo = (string) ($_POST['tipo'] ?? '');
$dataRaw = (string) ($_POST['data'] ?? '');

if ($attendanceId <= 0) {
    Response::error('Falta attendance_id.', 400);
}
if (!in_array($tipo, REPORT_TIPOS, true)) {
    Response::error('tipo inválido.', 400);
}
$data = json_decode($dataRaw, true);
if (!is_array($data)) {
    Response::error('Falta data (JSON) del informe.', 400);
}

$pdo = Db::get();

$stmt = $pdo->prepare(
    'SELECT a.id, a.student_id, a.estado, ap.rut, ap.nombre, ap.apellido, ap.fecha_nac
     FROM attendances a JOIN appointments ap ON ap.id = a.appointment_id
     WHERE a.id = ?'
);
$stmt->execute([$attendanceId]);
$attendance = $stmt->fetch();

if (!$attendance) {
    Response::error('Atención no encontrada.', 404);
}
if ((int) $attendance['student_id'] !== (int) $user['id']) {
    Response::error('Esta atención no es tuya.', 403);
}
if ($attendance['estado'] === 'atendido') {
    Response::error('La atención ya está cerrada, el informe quedó fijo.', 409);
}

// Validar imágenes subidas ANTES de tocar la base -- todo o nada.
$imageFiles = [];
foreach (REPORT_IMAGE_SUFFIXES as $suffix) {
    $field = "image_{$suffix}";
    if (!isset($_FILES[$field]) || $_FILES[$field]['error'] === UPLOAD_ERR_NO_FILE) {
        continue;
    }
    if ($_FILES[$field]['error'] !== UPLOAD_ERR_OK) {
        Response::error("Error al subir {$field} (código {$_FILES[$field]['error']}).", 400);
    }
    $tmpPath = $_FILES[$field]['tmp_name'];
    $info = @getimagesize($tmpPath);
    if ($info === false || $info[2] !== IMAGETYPE_JPEG) {
        Response::error("{$field} debe ser una imagen JPEG válida.", 400);
    }
    $imageFiles[$suffix] = $tmpPath;
}

$pdo->prepare(
    'INSERT INTO reports (attendance_id, tipo, data, updated_at)
     VALUES (?, ?, ?, CURRENT_TIMESTAMP)
     ON CONFLICT(attendance_id, tipo) DO UPDATE SET
        data = excluded.data, updated_at = CURRENT_TIMESTAMP'
)->execute([$attendanceId, $tipo, json_encode($data, JSON_UNESCAPED_UNICODE)]);

$stmt = $pdo->prepare('SELECT id FROM reports WHERE attendance_id = ? AND tipo = ?');
$stmt->execute([$attendanceId, $tipo]);
$reportId = (int) $stmt->fetchColumn();

// El PDF queda desactualizado apenas cambia data o alguna imagen -- se
// reconstruye al vuelo en report_pdf.php. Las imágenes NO se borran en
// bloque: cada suffix se sobreescribe solo si viene en este request (ver
// ReportFile::deletePdf()).
ReportFile::deletePdf($reportId);
foreach ($imageFiles as $suffix => $tmpPath) {
    ReportFile::saveImage($reportId, $suffix, $tmpPath);
}

$patient = [
    'rut' => $attendance['rut'],
    'nombre' => $attendance['nombre'],
    'apellido' => $attendance['apellido'],
    'fecha_nac' => $attendance['fecha_nac'],
];

try {
    $pdfBytes = ReportPdfBuilder::build(
        $reportId,
        $tipo,
        $data,
        $patient,
        (string) $user['display_name'],
        date('d-m-Y')
    );
    file_put_contents(ReportFile::pdfPath($reportId), $pdfBytes);
} catch (Throwable $e) {
    // El informe (fila + imágenes) ya quedó guardado -- el PDF se puede
    // regenerar después (ver report_pdf.php); no tumbamos la subida por esto.
    Response::json(['ok' => true, 'report_id' => $reportId, 'pdf_error' => $e->getMessage()]);
}

Response::json(['ok' => true, 'report_id' => $reportId]);
