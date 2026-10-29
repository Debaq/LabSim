<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Ficha de estudio (PDF) de un caso. Bearer auth: lo pide la app.
 *
 * ?appointment_id=: la de un intento de práctica ya cerrado, para el alumno
 * que lo hizo -- solo si el paciente tiene marcada esa opción (ver
 * Practica::fichaDeEstudioPermitida). La misma se baja desde el portal web
 * en student/ficha_estudio.php.
 * ?case_id=: la de cualquier caso, solo para el docente, siempre (como
 * admin/case_sheet_pdf.php?modo=estudio en el panel).
 */

$user = Auth::requireUser();
$appointmentId = (int) ($_GET['appointment_id'] ?? 0);
$caseIdPedido = trim((string) ($_GET['case_id'] ?? ''));

if ($caseIdPedido !== '') {
    if ($user['role'] !== 'admin') {
        Response::error('La ficha de estudio de un caso es solo para el docente.', 403);
    }
    $caseId = $caseIdPedido;
} else {
    if ($appointmentId <= 0) {
        Response::error('Falta appointment_id.', 400);
    }
    $caseId = Practica::fichaDeEstudioPermitida($appointmentId, (int) $user['id']);
    if ($caseId === null) {
        Response::error('La ficha de estudio de esta atención no está disponible.', 403);
    }
}

try {
    [$bytes, $nombre] = Practica::pdfFichaDeEstudio($caseId, (int) $user['id']);
} catch (Throwable $e) {
    error_log('[practica_ficha] ' . $e->getMessage());
    Response::error('No se pudo generar la ficha de estudio.', 500);
}

header('Content-Type: application/pdf');
header('Content-Disposition: inline; filename="' . $nombre . '"');
header('Content-Length: ' . strlen($bytes));
header('Cache-Control: private, no-store');
echo $bytes;
