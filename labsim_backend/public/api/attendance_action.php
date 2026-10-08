<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/LlmConfig.php';
require_once __DIR__ . '/../../src/LlmChat.php';
require_once __DIR__ . '/../../src/OirsEvaluator.php';

/**
 * Progreso de un alumno sobre una cita compartida (antes entry[8][username]
 * en schedule.json). Cada alumno tiene su propia fila en attendances para
 * la misma cita -- atenderla uno no le quita la cita a los demás.
 */

$user = Auth::requireUser();
$body = json_decode(file_get_contents('php://input'), true) ?? [];
$appointmentId = (int) ($body['id'] ?? 0);
$action = $body['action'] ?? '';

if ($appointmentId <= 0) {
    Response::error('Falta id de la cita', 400);
}

$pdo = Db::get();

switch ($action) {
    case 'atendiendo':
        $stmt = $pdo->prepare(
            "INSERT INTO attendances (appointment_id, student_id, estado, hora_real)
             VALUES (?, ?, 'atendiendo', time('now'))
             ON CONFLICT(appointment_id, student_id) DO UPDATE SET
                estado = 'atendiendo', updated_at = CURRENT_TIMESTAMP"
        );
        $stmt->execute([$appointmentId, $user['id']]);
        break;

    case 'atendido':
        $nota = trim((string) ($body['nota'] ?? ''));
        if ($nota === '') {
            Response::error('Falta la nota de atención', 400);
        }
        $stmt = $pdo->prepare(
            "INSERT INTO attendances (appointment_id, student_id, estado, nota, hora_real)
             VALUES (?, ?, 'atendido', ?, time('now'))
             ON CONFLICT(appointment_id, student_id) DO UPDATE SET
                estado = 'atendido', nota = excluded.nota, updated_at = CURRENT_TIMESTAMP"
        );
        $stmt->execute([$appointmentId, $user['id'], $nota]);

        $stmt = $pdo->prepare('SELECT case_id, patient_id FROM appointments WHERE id = ?');
        $stmt->execute([$appointmentId]);
        $appt = $stmt->fetch();
        $stmt->closeCursor();   // ver Db::get: una lectura abierta hace fallar la escritura que sigue
        if ($appt) {
            // La evaluación OIRS llama al LLM (hasta 30 s). Antes corría
            // antes de responder: la app cortaba a los 10 s, creía que no
            // se había cerrado y el alumno quedaba en un bucle de "sin
            // conexión" con la atención ya cerrada. Ahora corre después de
            // mandar la respuesta (Response::json hace exit y recién ahí
            // se ejecutan las funciones de cierre).
            $studentId = (int) $user['id'];
            $caseId = $appt['case_id'] !== null ? (string) $appt['case_id'] : null;
            $patientId = $appt['patient_id'] !== null ? (int) $appt['patient_id'] : null;
            ignore_user_abort(true);
            register_shutdown_function(static function () use ($appointmentId, $studentId, $caseId, $patientId): void {
                if (function_exists('fastcgi_finish_request')) {
                    fastcgi_finish_request();
                } elseif (function_exists('litespeed_finish_request')) {
                    litespeed_finish_request();
                }
                OirsEvaluator::evaluate($appointmentId, $studentId, $caseId, $patientId);
            });
        }
        break;

    case 'no_show':
        $nota = (string) ($body['nota'] ?? '');
        $stmt = $pdo->prepare(
            "INSERT INTO attendances (appointment_id, student_id, estado, nota)
             VALUES (?, ?, 'no_show', ?)
             ON CONFLICT(appointment_id, student_id) DO UPDATE SET
                estado = 'no_show', nota = excluded.nota, updated_at = CURRENT_TIMESTAMP"
        );
        $stmt->execute([$appointmentId, $user['id'], $nota]);
        break;

    default:
        Response::error('Acción no soportada', 400);
}

$stmt = $pdo->prepare('SELECT * FROM attendances WHERE appointment_id = ? AND student_id = ?');
$stmt->execute([$appointmentId, $user['id']]);
$attendance = $stmt->fetch();
// Cerrada antes de responder: la evaluación OIRS escribe después, en la
// función de cierre, y con esta lectura abierta fallaba ("database is locked").
$stmt->closeCursor();
Response::json(['attendance' => $attendance]);
