<?php
/**
 * LabSim Backend - Entregas
 *
 * GET    /submissions              → Lista entregas
 * GET    /submissions/:id          → Detalle entrega
 * POST   /submissions              → Crear entrega (estudiante)
 * PUT    /submissions/:id          → Actualizar borrador
 * POST   /submissions/:id/submit   → Enviar entrega
 * POST   /submissions/:id/review   → Calificar (docente/instructor)
 * POST   /submissions/:id/return   → Devolver para corrección
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;
$action = $routeSegments[1] ?? null;

switch (true) {

    // ─── LISTAR ENTREGAS ────────────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth();

        $where = ['1=1'];
        $params = [];

        if ($auth['role'] === 'estudiante') {
            // Solo sus entregas
            $where[] = 's.student_id = :uid';
            $params[':uid'] = $auth['sub'];
        } elseif (query_param('mine') === 'true') {
            // Docente ve entregas de sus sesiones
            $where[] = "EXISTS (SELECT 1 FROM practice_sessions ps WHERE ps.id = s.session_id AND ps.created_by = :uid)";
            $params[':uid'] = $auth['sub'];
        }

        $sessionId = query_param('sessionId') ?? query_param('session_id');
        if ($sessionId) {
            $where[] = 's.session_id = :sid';
            $params[':sid'] = $sessionId;
        }

        $status = query_param('status');
        if ($status) {
            $where[] = 's.status = :status';
            $params[':status'] = $status;
        }

        $sql = "SELECT s.id, s.session_id, s.case_id, s.student_id, s.status, s.grade,
                       s.submitted_at, s.reviewed_at, s.created_at,
                       u.username as student_username, u.full_name as student_name,
                       c.title as case_title,
                       ps.title as session_title
                FROM submissions s
                JOIN users u ON s.student_id = u.id
                JOIN cases c ON s.case_id = c.id
                JOIN practice_sessions ps ON s.session_id = ps.id
                WHERE " . implode(' AND ', $where) . "
                ORDER BY s.created_at DESC";

        $page = query_int('page', 1);
        $limit = query_int('limit', DEFAULT_PAGE_SIZE);
        json_response(Database::paginate($sql, $params, $page, $limit));
        break;

    // ─── DETALLE ENTREGA ────────────────────────────
    case $method === 'GET' && $id !== null && $action === null:
        $auth = require_auth();

        $sub = Database::fetchOne(
            "SELECT s.*, u.username as student_username, u.full_name as student_name,
                    c.title as case_title, c.profile_json as case_profile,
                    ps.title as session_title,
                    r.username as reviewer_username
             FROM submissions s
             JOIN users u ON s.student_id = u.id
             JOIN cases c ON s.case_id = c.id
             JOIN practice_sessions ps ON s.session_id = ps.id
             LEFT JOIN users r ON s.reviewed_by = r.id
             WHERE s.id = :id",
            [':id' => $id]
        );

        if (!$sub) error_response('Entrega no encontrada', 404);

        // Estudiantes solo ven sus propias entregas
        if ($auth['role'] === 'estudiante' && $auth['sub'] !== $sub['student_id']) {
            error_response('No tienes permiso para ver esta entrega', 403);
        }

        // Decodificar JSONs
        $sub['submission'] = json_decode($sub['submission_json'], true);
        unset($sub['submission_json']);
        $sub['caseProfile'] = json_decode($sub['case_profile'], true);
        unset($sub['case_profile']);

        json_response(['submission' => $sub]);
        break;

    // ─── CREAR ENTREGA ──────────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth('estudiante');
        $body = get_json_body();

        $errors = validate_required($body, ['sessionId', 'caseId']);
        validate_or_fail($errors);

        $sessionId = $body['sessionId'];
        $caseId = $body['caseId'];

        // Verificar sesión activa y que el estudiante pertenece al grupo
        $session = Database::fetchOne(
            "SELECT ps.id, ps.max_submissions, ps.allow_late_submission, ps.due_date, ps.status
             FROM practice_sessions ps
             WHERE ps.id = :sid AND ps.status IN ('approved','active')",
            [':sid' => $sessionId]
        );
        if (!$session) error_response('Sesión no encontrada o no activa', 404);

        // Verificar due_date
        if ($session['due_date'] && !$session['allow_late_submission']) {
            if (date('Y-m-d H:i:s') > $session['due_date']) {
                error_response('La fecha límite de entrega ha pasado', 400);
            }
        }

        // Verificar que el caso pertenece a la sesión
        $sessionCase = Database::fetchOne(
            'SELECT session_id FROM practice_session_cases WHERE session_id = :sid AND case_id = :cid',
            [':sid' => $sessionId, ':cid' => $caseId]
        );
        if (!$sessionCase) error_response('El caso no pertenece a esta sesión', 400);

        // Verificar max_submissions
        $existing = Database::fetchOne(
            "SELECT COUNT(*) as count FROM submissions
             WHERE session_id = :sid AND case_id = :cid AND student_id = :uid AND status != 'draft'",
            [':sid' => $sessionId, ':cid' => $caseId, ':uid' => $auth['sub']]
        );
        if (($existing['count'] ?? 0) >= $session['max_submissions']) {
            error_response('Ya alcanzaste el máximo de entregas para este caso', 400);
        }

        $subId = Database::uuid();
        $submissionJson = json_encode($body['submissionJson'] ?? $body['submission'] ?? new stdClass(), JSON_UNESCAPED_UNICODE);

        Database::execute(
            "INSERT INTO submissions (id, session_id, case_id, student_id, submission_json, status)
             VALUES (:id, :sid, :cid, :uid, :json, 'draft')",
            [
                ':id' => $subId, ':sid' => $sessionId, ':cid' => $caseId,
                ':uid' => $auth['sub'], ':json' => $submissionJson,
            ]
        );

        created_response(['submission' => Database::fetchOne('SELECT * FROM submissions WHERE id = :id', [':id' => $subId])]);
        break;

    // ─── ACTUALIZAR BORRADOR ────────────────────────
    case $method === 'PUT' && $id !== null && $action === null:
        $auth = require_auth('estudiante');
        $body = get_json_body();

        $sub = Database::fetchOne('SELECT id, student_id, status FROM submissions WHERE id = :id', [':id' => $id]);
        if (!$sub) error_response('Entrega no encontrada', 404);
        if ($sub['student_id'] !== $auth['sub']) error_response('No es tu entrega', 403);
        if (!in_array($sub['status'], ['draft', 'returned'])) {
            error_response('Solo se pueden editar borradores o entregas devueltas', 400);
        }

        $submissionJson = json_encode($body['submissionJson'] ?? $body['submission'] ?? new stdClass(), JSON_UNESCAPED_UNICODE);
        Database::execute(
            "UPDATE submissions SET submission_json = :json WHERE id = :id",
            [':id' => $id, ':json' => $submissionJson]
        );

        json_response(['message' => 'Borrador actualizado']);
        break;

    // ─── ENVIAR ENTREGA ─────────────────────────────
    case $method === 'POST' && $action === 'submit':
        $auth = require_auth('estudiante');

        $sub = Database::fetchOne('SELECT id, student_id, status FROM submissions WHERE id = :id', [':id' => $id]);
        if (!$sub) error_response('Entrega no encontrada', 404);
        if ($sub['student_id'] !== $auth['sub']) error_response('No es tu entrega', 403);
        if (!in_array($sub['status'], ['draft', 'returned'])) {
            error_response('Solo se pueden enviar borradores o entregas devueltas', 400);
        }

        Database::execute(
            "UPDATE submissions SET status = 'submitted', submitted_at = datetime('now') WHERE id = :id",
            [':id' => $id]
        );

        json_response(['message' => 'Entrega enviada']);
        break;

    // ─── CALIFICAR ENTREGA ──────────────────────────
    case $method === 'POST' && $action === 'review':
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $body = get_json_body();

        $sub = Database::fetchOne('SELECT id, status FROM submissions WHERE id = :id', [':id' => $id]);
        if (!$sub) error_response('Entrega no encontrada', 404);
        if ($sub['status'] !== 'submitted') {
            error_response('Solo se pueden calificar entregas enviadas', 400);
        }

        Database::execute(
            "UPDATE submissions SET status = 'reviewed', grade = :grade, feedback = :feedback,
             reviewed_by = :uid, reviewed_at = datetime('now') WHERE id = :id",
            [
                ':id' => $id,
                ':grade' => $body['grade'] ?? null,
                ':feedback' => $body['feedback'] ?? null,
                ':uid' => $auth['sub'],
            ]
        );

        json_response(['message' => 'Entrega calificada']);
        break;

    // ─── DEVOLVER ENTREGA ───────────────────────────
    case $method === 'POST' && $action === 'return':
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $body = get_json_body();

        $sub = Database::fetchOne('SELECT id, status FROM submissions WHERE id = :id', [':id' => $id]);
        if (!$sub) error_response('Entrega no encontrada', 404);
        if ($sub['status'] !== 'submitted') {
            error_response('Solo se pueden devolver entregas enviadas', 400);
        }

        Database::execute(
            "UPDATE submissions SET status = 'returned', feedback = :feedback,
             reviewed_by = :uid, reviewed_at = datetime('now') WHERE id = :id",
            [
                ':id' => $id,
                ':feedback' => $body['feedback'] ?? 'Sin comentarios',
                ':uid' => $auth['sub'],
            ]
        );

        json_response(['message' => 'Entrega devuelta para corrección']);
        break;

    default:
        error_response("Ruta no encontrada: submissions/" . implode('/', $routeSegments), 404);
}
