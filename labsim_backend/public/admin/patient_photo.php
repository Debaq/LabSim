<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/PatientPhoto.php';

/**
 * Sirve la foto de un paciente desde afuera de public/ -- mismo patrón que
 * backup_download.php/logs_download.php, así la carpeta data/patient_photos/
 * no queda expuesta directo por URL.
 */

Auth::requireAdminSession();

$caseId = trim((string) ($_GET['case_id'] ?? ''));
$type = (string) ($_GET['type'] ?? 'avatar');

if ($caseId === '' || !in_array($type, ['avatar', 'original'], true)) {
    http_response_code(400);
    exit;
}

try {
    $path = $type === 'avatar' ? PatientPhoto::avatarPath($caseId) : PatientPhoto::originalPath($caseId);
} catch (InvalidArgumentException $e) {
    http_response_code(400);
    exit;
}

if (!is_file($path)) {
    http_response_code(404);
    exit;
}

header('Content-Type: ' . ($type === 'avatar' ? 'image/png' : 'image/jpeg'));
header('Cache-Control: private, max-age=60');
readfile($path);
