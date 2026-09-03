<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/OtoscopiaPhoto.php';
require_once __DIR__ . '/../../src/AdminAudit.php';

/**
 * Sube (o borra) una imagen de otoscopia para un oído/fase puntual --
 * mismo patrón que patient_photo_upload.php: fetch + FormData desde
 * case_create.php, que ya tiene un <form> gigante para toda la ficha y no
 * puede anidar otro adentro. Devuelve JSON, no redirige.
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
$side = (string) ($_POST['side'] ?? '');
$faseIdx = (int) ($_POST['fase_idx'] ?? -1);
$action = (string) ($_POST['action'] ?? 'upload');

if ($caseId === '') {
    echo json_encode(['ok' => false, 'error' => 'Falta el caso.']);
    exit;
}
if (!in_array($side, ['od', 'oi'], true)) {
    echo json_encode(['ok' => false, 'error' => 'Oído inválido.']);
    exit;
}
if ($faseIdx < 0) {
    echo json_encode(['ok' => false, 'error' => 'Fase inválida.']);
    exit;
}

// case_id real (ya guardado) o id temporal (ver $uploadTempId en
// case_create.php -- permite subir otoscopia ANTES de guardar el caso por
// primera vez; OtoscopiaPhoto::claim() la reasigna al case_id real al
// guardar). Los ids temporales siempre empiezan con "tmp".
$stmt = $pdo->prepare('SELECT id FROM cases WHERE id = ?');
$stmt->execute([$caseId]);
if ($stmt->fetchColumn() === false && !str_starts_with($caseId, 'tmp')) {
    echo json_encode(['ok' => false, 'error' => 'El caso no existe.']);
    exit;
}

if ($action === 'delete') {
    try {
        OtoscopiaPhoto::delete($caseId, $side, $faseIdx);
        AdminAudit::log($me, 'otoscopia_photo_delete', ['case_id' => $caseId, 'side' => $side, 'fase' => $faseIdx]);
        echo json_encode(['ok' => true]);
    } catch (Throwable $e) {
        echo json_encode(['ok' => false, 'error' => $e->getMessage()]);
    }
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

try {
    OtoscopiaPhoto::save($caseId, $side, $faseIdx, $file['tmp_name']);
    AdminAudit::log($me, 'otoscopia_photo_upload', ['case_id' => $caseId, 'side' => $side, 'fase' => $faseIdx]);
    echo json_encode(['ok' => true]);
} catch (Throwable $e) {
    echo json_encode(['ok' => false, 'error' => $e->getMessage()]);
}
