<?php
/**
 * LabSim Backend - Feedback de pacientes (reclamos/felicitaciones)
 *
 * POST   /feedback                    → Generar feedback (sistema automático o docente)
 * GET    /feedback                    → Lista feedback (docente/instructor: sus estudiantes)
 * GET    /feedback/:id                → Detalle
 * POST   /feedback/:id/read           → Marcar como leído
 * GET    /feedback/summary             → Resumen por estudiante (docente)
 *
 * El feedback se genera automáticamente cuando:
 * - Estudiante se atrasa (complaint: late_start/overtime)
 * - Estudiante reagenda (complaint: rescheduled, probabilístico)
 * - Estudiante completa a tiempo o antes (compliment: fast_service)
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;
$action = $routeSegments[1] ?? null;

switch (true) {

    // ─── LISTAR FEEDBACK ────────────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $where = ['1=1'];
        $params = [];

        $type = query_param('type');
        if ($type) { $where[] = 'f.feedback_type = :type'; $params[':type'] = $type; }

        $studentId = query_param('studentId');
        if ($studentId) { $where[] = 'f.student_id = :sid'; $params[':sid'] = $studentId; }

        $unreadOnly = query_param('unread');
        if ($unreadOnly === 'true') {
            if ($auth['role'] === 'docente') {
                $where[] = 'f.is_read_by_docente = 0';
            } elseif ($auth['role'] === 'instructor') {
                $where[] = 'f.is_read_by_instructor = 0';
            }
        }

        // Docente/instructor solo ven feedback de sus estudiantes
        if ($auth['role'] !== 'admin') {
            $where[] = "EXISTS (
                SELECT 1 FROM group_members gm1
                JOIN group_members gm2 ON gm1.group_id = gm2.group_id
                WHERE gm1.user_id = :uid AND gm2.user_id = f.student_id
            )";
            $params[':uid'] = $auth['sub'];
        }

        $sql = "SELECT f.*,
                       u.username as student_username, u.full_name as student_name,
                       a.patient_name, a.scheduled_date, a.scheduled_time,
                       p.name as procedure_name
                FROM patient_feedback f
                JOIN users u ON f.student_id = u.id
                JOIN agenda_items a ON f.agenda_item_id = a.id
                LEFT JOIN procedures p ON a.procedure_id = p.id
                WHERE " . implode(' AND ', $where) . "
                ORDER BY f.created_at DESC";

        $page = query_int('page', 1);
        $limit = query_int('limit', DEFAULT_PAGE_SIZE);
        json_response(Database::paginate($sql, $params, $page, $limit));
        break;

    // ─── RESUMEN POR ESTUDIANTE ─────────────────────
    case $method === 'GET' && $id === 'summary':
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $where = ['1=1'];
        $params = [];

        if ($auth['role'] !== 'admin') {
            $where[] = "EXISTS (
                SELECT 1 FROM group_members gm1
                JOIN group_members gm2 ON gm1.group_id = gm2.group_id
                WHERE gm1.user_id = :uid AND gm2.user_id = f.student_id
            )";
            $params[':uid'] = $auth['sub'];
        }

        $summary = Database::fetchAll(
            "SELECT f.student_id, u.username, u.full_name,
                    SUM(CASE WHEN f.feedback_type = 'complaint' THEN 1 ELSE 0 END) as complaints,
                    SUM(CASE WHEN f.feedback_type = 'compliment' THEN 1 ELSE 0 END) as compliments,
                    COUNT(*) as total
             FROM patient_feedback f
             JOIN users u ON f.student_id = u.id
             WHERE " . implode(' AND ', $where) . "
             GROUP BY f.student_id
             ORDER BY complaints DESC, compliments DESC",
            $params
        );

        json_response(['summary' => $summary]);
        break;

    // ─── GENERAR FEEDBACK ───────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth();
        $body = get_json_body();

        $errors = validate_required($body, ['agendaItemId', 'studentId', 'feedbackType', 'reason', 'message']);
        $errors[] = validate_enum($body['feedbackType'] ?? null, ['complaint', 'compliment'], 'feedbackType');
        $errors[] = validate_enum(
            $body['reason'] ?? null,
            ['late_start', 'overtime', 'rescheduled', 'poor_attention', 'misdiagnosis',
             'fast_service', 'good_attention', 'accurate_diagnosis', 'patient_comfort', 'other'],
            'reason'
        );
        validate_or_fail($errors);

        $feedbackId = Database::uuid();
        $agendaItem = Database::fetchOne('SELECT patient_name FROM agenda_items WHERE id = :id', [':id' => $body['agendaItemId']]);

        Database::execute(
            "INSERT INTO patient_feedback (id, agenda_item_id, student_id, feedback_type, reason, message, patient_name, severity)
             VALUES (:id, :aid, :sid, :type, :reason, :msg, :patient, :sev)",
            [
                ':id' => $feedbackId,
                ':aid' => $body['agendaItemId'],
                ':sid' => $body['studentId'],
                ':type' => $body['feedbackType'],
                ':reason' => $body['reason'],
                ':msg' => $body['message'],
                ':patient' => $agendaItem['patient_name'] ?? null,
                ':sev' => $body['severity'] ?? 1,
            ]
        );

        created_response(['feedback' => Database::fetchOne('SELECT * FROM patient_feedback WHERE id = :id', [':id' => $feedbackId])]);
        break;

    // ─── MARCAR COMO LEÍDO ──────────────────────────
    case $method === 'POST' && $id !== null && $action === 'read':
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $field = ($auth['role'] === 'instructor') ? 'is_read_by_instructor' : 'is_read_by_docente';
        Database::execute("UPDATE patient_feedback SET $field = 1 WHERE id = :id", [':id' => $id]);

        json_response(['message' => 'Marcado como leído']);
        break;

    // ─── DETALLE ────────────────────────────────────
    case $method === 'GET' && $id !== null && $id !== 'summary':
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $fb = Database::fetchOne(
            "SELECT f.*, u.username as student_username, u.full_name as student_name,
                    a.patient_name, a.scheduled_date, a.scheduled_time, a.duration_minutes,
                    p.name as procedure_name
             FROM patient_feedback f
             JOIN users u ON f.student_id = u.id
             JOIN agenda_items a ON f.agenda_item_id = a.id
             LEFT JOIN procedures p ON a.procedure_id = p.id
             WHERE f.id = :id",
            [':id' => $id]
        );
        if (!$fb) error_response('Feedback no encontrado', 404);

        json_response(['feedback' => $fb]);
        break;

    default:
        error_response("Ruta no encontrada: feedback/" . implode('/', $routeSegments), 404);
}
