<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/PatientPhoto.php';
require_once __DIR__ . '/../../src/AdminAudit.php';

/**
 * Recibe la foto ya recortada en el navegador (fetch + FormData desde el
 * modal en case_create.php, no un <form> normal -- ese archivo ya tiene un
 * <form> gigante para toda la ficha y no se puede anidar otro adentro).
 * Devuelve JSON, no redirige.
 */

header('Content-Type: application/json');

$me = Auth::requireAdminSession();
$pdo = Db::get();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Método no permitido.']);
    exit;
}

try {
    Auth::requireCsrf();
} catch (Throwable $e) {
    http_response_code(403);
    echo json_encode(['ok' => false, 'error' => 'Sesión expirada, recarga la página.']);
    exit;
}

$caseId = trim((string) ($_POST['case_id'] ?? ''));
$cropX = (float) ($_POST['crop_x'] ?? 0);
$cropY = (float) ($_POST['crop_y'] ?? 0);
$cropSize = (float) ($_POST['crop_size'] ?? 0);

if ($caseId === '') {
    echo json_encode(['ok' => false, 'error' => 'Falta el caso.']);
    exit;
}

$stmt = $pdo->prepare('SELECT id FROM cases WHERE id = ?');
$stmt->execute([$caseId]);
if ($stmt->fetchColumn() === false) {
    echo json_encode(['ok' => false, 'error' => 'El caso no existe.']);
    exit;
}

$file = $_FILES['photo'] ?? null;
if (!$file || $file['error'] !== UPLOAD_ERR_OK) {
    echo json_encode(['ok' => false, 'error' => 'No se pudo recibir el archivo.']);
    exit;
}
// Límite generoso pero acotado -- una foto de celular actual ronda 3-8MB.
if ($file['size'] > 12 * 1024 * 1024) {
    echo json_encode(['ok' => false, 'error' => 'La imagen pesa más de 12MB.']);
    exit;
}
if ($cropSize <= 0) {
    echo json_encode(['ok' => false, 'error' => 'Falta el recorte.']);
    exit;
}

try {
    PatientPhoto::save($caseId, $file['tmp_name'], $cropX, $cropY, $cropSize);
    AdminAudit::log($me, 'patient_photo_upload', ['case_id' => $caseId]);
    echo json_encode(['ok' => true]);
} catch (Throwable $e) {
    echo json_encode(['ok' => false, 'error' => $e->getMessage()]);
}
