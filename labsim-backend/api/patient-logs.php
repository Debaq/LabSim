<?php
/**
 * LabSim Backend - Logs de interacción paciente
 *
 * Memoria del paciente: registra qué pasó en cada atención
 * para que el paciente "recuerde" interacciones anteriores.
 *
 * GET    /patient-logs?case_id=X     → Listar logs de un paciente
 * POST   /patient-logs               → Crear log (al terminar atención)
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;

switch (true) {

    // ─── LISTAR LOGS DE UN PACIENTE ──────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth();

        $caseId = query_param('case_id');
        if (!$caseId) {
            error_response('Se requiere case_id', 400);
        }

        $rows = Database::fetchAll(
            "SELECT pl.*, u.full_name as student_full_name, u.username as student_username
             FROM patient_interaction_logs pl
             LEFT JOIN users u ON pl.student_id = u.id
             WHERE pl.case_id = :cid
             ORDER BY pl.created_at DESC",
            [':cid' => $caseId]
        );
        json_response(['data' => $rows]);
        break;

    // ─── CREAR LOG ───────────────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth();
        $body = get_json_body();

        $errors = validate_required($body, ['caseId', 'summary']);
        validate_or_fail($errors);

        $logId = Database::uuid();

        // Obtener nombre del estudiante
        $student = Database::fetchOne('SELECT full_name FROM users WHERE id = :id', [':id' => $auth['sub']]);

        Database::execute(
            "INSERT INTO patient_interaction_logs (id, case_id, agenda_item_id, student_id, student_name, summary, mood_at_end, tests_performed, duration_minutes)
             VALUES (:id, :cid, :aid, :sid, :sname, :summary, :mood, :tests, :dur)",
            [
                ':id' => $logId,
                ':cid' => $body['caseId'],
                ':aid' => $body['agendaItemId'] ?? null,
                ':sid' => $auth['sub'],
                ':sname' => $student['full_name'] ?? null,
                ':summary' => $body['summary'],
                ':mood' => $body['moodAtEnd'] ?? null,
                ':tests' => json_encode($body['testsPerformed'] ?? [], JSON_UNESCAPED_UNICODE),
                ':dur' => $body['durationMinutes'] ?? null,
            ]
        );

        $log = Database::fetchOne('SELECT * FROM patient_interaction_logs WHERE id = :id', [':id' => $logId]);
        created_response(['log' => $log]);
        break;

    default:
        error_response("Ruta no encontrada: patient-logs/$id", 404);
}
