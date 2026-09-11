<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/CaseSheetPdf.php';

/**
 * PDF de la ficha completa de un caso (?id=), para el docente.
 *
 * No es el informe del alumno (public/admin/report_pdf.php): esto es la hoja
 * de respuestas del caso -- perfil, audiograma, impedanciometría, acumetría,
 * logoaudiometría, supraliminares, ABR, OEA y VEMP-- con los mismos gráficos
 * del editor. Se arma en cada pedido y no se cachea en disco: el caso se
 * edita, y un PDF guardado quedaría mintiendo desde la primera edición.
 *
 * Visibilidad: la misma de patients.php -- un docente no puede bajar la
 * ficha de un caso agendado en un curso ajeno.
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();

$caseId = trim((string) ($_GET['id'] ?? ''));
if ($caseId === '') {
    http_response_code(400);
    exit('Falta id.');
}

$stmt = $pdo->prepare(
    'SELECT c.id, c.data,
            a.course_id, a.rut, a.nombre, a.apellido, a.fecha_nac
     FROM cases c
     LEFT JOIN appointments a ON a.id = (
         SELECT id FROM appointments WHERE case_id = c.id ORDER BY id DESC LIMIT 1
     )
     WHERE c.id = ?'
);
$stmt->execute([$caseId]);
$caso = $stmt->fetch();

if (!$caso) {
    http_response_code(404);
    exit('Caso no encontrado.');
}

if ((int) $me['permission'] !== Auth::PERMISSION_ADMIN && $caso['course_id'] !== null) {
    $misCursos = Courses::teacherCourseIds((int) $me['id']);
    if (!in_array((int) $caso['course_id'], array_map('intval', $misCursos), true)) {
        http_response_code(403);
        exit('Este caso pertenece a un curso que no dictas.');
    }
}

$data = json_decode((string) ($caso['data'] ?? ''), true);
if (!is_array($data)) {
    http_response_code(500);
    exit('La ficha de este caso no se puede leer.');
}

// Sin cita viva, el nombre sale del snapshot que guarda Cases:: al borrarla
// -- si no, la ficha de un caso desagendado saldría sin paciente.
$snapshot = is_array($data['paciente_snapshot'] ?? null) ? $data['paciente_snapshot'] : [];
$patient = [
    'nombre' => (string) ($caso['nombre'] ?? $snapshot['nombre'] ?? ''),
    'apellido' => (string) ($caso['apellido'] ?? $snapshot['apellido'] ?? ''),
    'rut' => (string) ($caso['rut'] ?? $snapshot['rut'] ?? 'N/D'),
    'fecha_nac' => (string) ($caso['fecha_nac'] ?? $snapshot['fecha_nac'] ?? ''),
];

try {
    $pdfBytes = CaseSheetPdf::build(
        (string) $caso['id'],
        $data,
        $patient,
        (string) ($me['display_name'] ?? ''),
        date('d-m-Y')
    );
} catch (Throwable $e) {
    http_response_code(500);
    exit('No se pudo generar el PDF: ' . htmlspecialchars($e->getMessage()));
}

$nombreArchivo = 'ficha_' . preg_replace('/[^A-Za-z0-9_-]/', '_', (string) $caso['id']) . '.pdf';
header('Content-Type: application/pdf');
header('Content-Disposition: inline; filename="' . $nombreArchivo . '"');
header('Content-Length: ' . strlen($pdfBytes));
header('Cache-Control: private, no-store');
echo $pdfBytes;
