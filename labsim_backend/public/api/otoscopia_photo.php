<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/OtoscopiaPhoto.php';

/**
 * Sirve una imagen de otoscopia para la app de escritorio (auth por Bearer
 * token, no sesión de admin -- ver admin/otoscopia_photo.php, que es el
 * equivalente para el panel web). Cualquier usuario logueado (alumno o
 * docente) puede pedirla: no es información sensible propia de un alumno,
 * es del paciente simulado.
 */

Auth::requireUser();

$caseId = trim((string) ($_GET['case_id'] ?? ''));
$side = (string) ($_GET['side'] ?? '');
$faseIdx = (int) ($_GET['fase'] ?? 0);

if ($caseId === '' || !in_array($side, ['od', 'oi'], true) || $faseIdx < 0) {
    Response::error('Falta case_id, side inválido, o fase inválida.', 400);
}

try {
    $path = OtoscopiaPhoto::path($caseId, $side, $faseIdx);
} catch (InvalidArgumentException $e) {
    Response::error('case_id inválido.', 400);
}

if (!is_file($path)) {
    Response::error('Sin imagen.', 404);
}

header('Content-Type: image/jpeg');
header('Cache-Control: private, max-age=300');
readfile($path);
