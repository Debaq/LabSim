<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/CaseBuilder.php';
require_once __DIR__ . '/../../src/LlmConfig.php';
require_once __DIR__ . '/../../src/LlmChat.php';

/**
 * Chat real de la app (Ficha del paciente -> "Conversar con paciente"): el
 * alumno manda case_id + historial + mensaje, y acá se arma el system
 * prompt con la Anamnesis/Tinnitus/gender ya guardados en cases.data (no se
 * confía en el cliente para eso -- son los datos clínicos del caso). nombre/
 * edad/procedimiento sí vienen del cliente porque no viven en cases.data
 * (son de la cita, ver CaseBuilder::caseDataToForm) y son solo texto de
 * ambientación, no dato clínico.
 *
 * Si viene appointment_id, el turno (mensaje del alumno + respuesta) queda
 * guardado en llm_chat_logs contra esa cita + el alumno logueado, para poder
 * revisar la conversación después. El "Atender (prueba)" del admin no manda
 * appointment_id a propósito -- esas pruebas no dejan rastro.
 */

$user = Auth::requireUser();

$body = json_decode(file_get_contents('php://input'), true);
if (!is_array($body)) {
    Response::error('JSON inválido.', 400);
}

$caseId = trim((string) ($body['case_id'] ?? ''));
$message = trim((string) ($body['message'] ?? ''));
if ($caseId === '' || $message === '') {
    Response::error('Falta case_id o message.', 400);
}

$appointmentId = isset($body['appointment_id']) ? (int) $body['appointment_id'] : 0;

if (!LlmConfig::get()['active']) {
    Response::error('El chat con el paciente no está habilitado (Admin -> IA Paciente).', 503);
}

$stmt = Db::get()->prepare('SELECT data FROM cases WHERE id = ?');
$stmt->execute([$caseId]);
$row = $stmt->fetch();
if (!$row) {
    Response::error('El caso no existe.', 404);
}
$caseData = json_decode((string) $row['data'], true) ?: [];

$systemPrompt = LlmConfig::buildSystemPrompt(
    [
        'nombre' => (string) ($body['nombre'] ?? ''),
        'edad' => (string) ($body['edad'] ?? ''),
        'genero' => (string) ($caseData['gender'] ?? '0'),
        'procedimiento' => (string) ($body['procedimiento'] ?? ''),
    ],
    [
        'antecedentes' => (array) ($caseData['Anamnesis']['antecedentes'] ?? []),
        'medicamentos' => (string) ($caseData['Anamnesis']['medicamentos'] ?? ''),
        'cirugias' => (string) ($caseData['Anamnesis']['cirugias'] ?? ''),
        'otros' => (string) ($caseData['Anamnesis']['otros'] ?? ''),
        'comportamiento' => (string) ($caseData['PatientBehavior'] ?? ''),
    ],
    (array) ($caseData['Tinnitus'] ?? [])
);

$history = [];
foreach ((array) ($body['history'] ?? []) as $h) {
    $content = trim((string) ($h['content'] ?? ''));
    if ($content !== '') {
        $history[] = ['role' => ($h['role'] ?? '') === 'assistant' ? 'assistant' : 'user', 'content' => $content];
    }
}

try {
    $reply = LlmChat::reply($systemPrompt, $history, $message);
} catch (Throwable $e) {
    Response::error($e->getMessage(), 502);
}

if ($appointmentId > 0) {
    $stmt = Db::get()->prepare('INSERT INTO llm_chat_logs (appointment_id, student_id, case_id, role, content) VALUES (?, ?, ?, ?, ?)');
    $stmt->execute([$appointmentId, $user['id'], $caseId, 'user', $message]);
    $stmt->execute([$appointmentId, $user['id'], $caseId, 'assistant', $reply]);
}

Response::json(['reply' => $reply]);
