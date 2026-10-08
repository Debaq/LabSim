<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Ficha de estudio (PDF) de un intento de práctica propio ya cerrado
 * (?appointment_id=), desde el navegador del alumno. Igual que
 * api/practica_ficha.php, pero con sesión de portal (sso.php) en vez de
 * Bearer. Solo si el docente la dejó disponible en ese paciente.
 */

$me = Auth::requireStudentSession();
$appointmentId = (int) ($_GET['appointment_id'] ?? 0);

$caseId = $appointmentId > 0 ? Practica::fichaDeEstudioPermitida($appointmentId, (int) $me['id']) : null;
if ($caseId === null) {
    http_response_code(404);
    exit('La ficha de estudio de esta atención no está disponible.');
}

try {
    [$bytes, $nombre] = Practica::pdfFichaDeEstudio($caseId, (int) $me['id']);
} catch (Throwable $e) {
    error_log('[student/ficha_estudio] ' . $e->getMessage());
    http_response_code(500);
    exit('No se pudo generar la ficha de estudio.');
}

header('Content-Type: application/pdf');
header('Content-Disposition: inline; filename="' . $nombre . '"');
header('Content-Length: ' . strlen($bytes));
header('Cache-Control: private, no-store');
echo $bytes;
