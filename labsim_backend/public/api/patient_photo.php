<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/PatientPhoto.php';

/**
 * Sirve el avatar/foto de un paciente para la app de escritorio (auth por
 * Bearer token, no sesión de admin -- ver admin/patient_photo.php, que es
 * el equivalente para el panel web). Cualquier usuario logueado (alumno o
 * docente) puede pedir la foto de cualquier caso: no es información
 * sensible propia de un alumno, es del paciente simulado.
 */

Auth::requireUser();

$caseId = trim((string) ($_GET['case_id'] ?? ''));
$type = (string) ($_GET['type'] ?? 'avatar');

if ($caseId === '' || !in_array($type, ['avatar', 'original'], true)) {
    Response::error('Falta case_id o type inválido.', 400);
}

try {
    $path = $type === 'avatar' ? PatientPhoto::avatarPath($caseId) : PatientPhoto::originalPath($caseId);
} catch (InvalidArgumentException $e) {
    Response::error('case_id inválido.', 400);
}

if (!is_file($path)) {
    Response::error('Sin foto.', 404);
}

header('Content-Type: ' . ($type === 'avatar' ? 'image/png' : 'image/jpeg'));
header('Cache-Control: private, max-age=300');
readfile($path);
