<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/OtoscopiaPhoto.php';

/**
 * Sirve una imagen de otoscopia desde afuera de public/ -- mismo patrón que
 * patient_photo.php, así data/otoscopia_photos/ no queda expuesta directo
 * por URL.
 */

Auth::requireAdminSession();

$caseId = trim((string) ($_GET['case_id'] ?? ''));
$side = (string) ($_GET['side'] ?? '');
$faseIdx = (int) ($_GET['fase'] ?? -1);

if ($caseId === '' || !in_array($side, ['od', 'oi'], true) || $faseIdx < 0) {
    http_response_code(400);
    exit;
}

try {
    $path = OtoscopiaPhoto::path($caseId, $side, $faseIdx);
} catch (InvalidArgumentException $e) {
    http_response_code(400);
    exit;
}

if (!is_file($path)) {
    http_response_code(404);
    exit;
}

header('Content-Type: image/jpeg');
header('Cache-Control: private, max-age=60');
readfile($path);
