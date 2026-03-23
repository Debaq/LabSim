<?php
/**
 * LabSim Backend - Sesiones Prácticas
 *
 * GET    /sessions                         → Lista sesiones
 * GET    /sessions/:id                     → Detalle (+ casos + guías)
 * POST   /sessions                         → Crear sesión
 * PUT    /sessions/:id                     → Actualizar sesión
 * DELETE /sessions/:id                     → Cancelar sesión
 * POST   /sessions/:id/approve             → Aprobar sesión (docente)
 * POST   /sessions/:id/reject              → Rechazar sesión
 * POST   /sessions/:id/activate            → Activar sesión
 * POST   /sessions/:id/complete            → Completar sesión
 * POST   /sessions/:id/cases               → Agregar caso a sesión
 * DELETE /sessions/:id/cases/:caseId       → Quitar caso de sesión
 * GET    /sessions/:id/guides              → Lista guías
 * POST   /sessions/:id/guides              → Subir guía
 * DELETE /sessions/:id/guides/:guideId     → Eliminar guía
 * GET    /sessions/:id/guides/:guideId/download → Descargar guía
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';
require_once __DIR__ . '/../core/upload.php';

$id = $routeSegments[0] ?? null;
$action = $routeSegments[1] ?? null;
$subId = $routeSegments[2] ?? null;
$subAction = $routeSegments[3] ?? null;

switch (true) {

    // ─── LISTAR SESIONES ────────────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth();

        $where = ['1=1'];
        $params = [];

        $status = query_param('status');
        if ($status) {
            $where[] = 'ps.status = :status';
            $params[':status'] = $status;
        }

        $groupId = query_param('groupId');
        if ($groupId) {
            $where[] = 'ps.group_id = :gid';
            $params[':gid'] = $groupId;
        }

        $from = query_param('from');
        if ($from) {
            $where[] = 'ps.scheduled_date >= :from';
            $params[':from'] = $from;
        }
        $to = query_param('to');
        if ($to) {
            $where[] = 'ps.scheduled_date <= :to';
            $params[':to'] = $to;
        }

        // Estudiantes solo ven sesiones de sus grupos que estén activas/completadas
        if ($auth['role'] === 'estudiante') {
            $where[] = "ps.status IN ('approved','active','completed')";
            $where[] = "EXISTS (SELECT 1 FROM group_members gm WHERE gm.group_id = ps.group_id AND gm.user_id = :uid)";
            $params[':uid'] = $auth['sub'];
        } elseif (query_param('mine') === 'true') {
            $where[] = 'ps.created_by = :uid';
            $params[':uid'] = $auth['sub'];
        }

        $sql = "SELECT ps.*, u.username as creator_username, u.full_name as creator_name,
                       g.name as group_name,
                       (SELECT COUNT(*) FROM practice_session_cases psc WHERE psc.session_id = ps.id) as case_count,
                       (SELECT COUNT(*) FROM submissions s WHERE s.session_id = ps.id AND s.status = 'submitted') as pending_submissions
                FROM practice_sessions ps
                LEFT JOIN users u ON ps.created_by = u.id
                LEFT JOIN student_groups g ON ps.group_id = g.id
                WHERE " . implode(' AND ', $where) . "
                ORDER BY ps.scheduled_date DESC, ps.scheduled_time DESC";

        $page = query_int('page', 1);
        $limit = query_int('limit', DEFAULT_PAGE_SIZE);
        json_response(Database::paginate($sql, $params, $page, $limit));
        break;

    // ─── DETALLE SESIÓN ─────────────────────────────
    case $method === 'GET' && $id !== null && $action === null:
        $auth = require_auth();

        $session = Database::fetchOne(
            "SELECT ps.*, u.username as creator_username, u.full_name as creator_name,
                    g.name as group_name
             FROM practice_sessions ps
             LEFT JOIN users u ON ps.created_by = u.id
             LEFT JOIN student_groups g ON ps.group_id = g.id
             WHERE ps.id = :id",
            [':id' => $id]
        );
        if (!$session) error_response('Sesión no encontrada', 404);

        // Casos asignados
        $session['cases'] = Database::fetchAll(
            "SELECT psc.order_index, psc.is_required, c.id, c.title, c.description, c.difficulty, c.tags
             FROM practice_session_cases psc
             JOIN cases c ON psc.case_id = c.id
             WHERE psc.session_id = :sid
             ORDER BY psc.order_index",
            [':sid' => $id]
        );

        // Guías
        $session['guides'] = Database::fetchAll(
            "SELECT sg.id, sg.title, sg.description, sg.file_size, sg.mime_type, sg.guide_type,
                    sg.external_url, sg.created_at, u.username as uploader
             FROM session_guides sg
             LEFT JOIN users u ON sg.uploaded_by = u.id
             WHERE sg.session_id = :sid
             ORDER BY sg.created_at",
            [':sid' => $id]
        );

        // Entregas (si es docente/instructor/admin)
        if (in_array($auth['role'], ['admin', 'docente', 'instructor'])) {
            $session['submissions'] = Database::fetchAll(
                "SELECT s.id, s.case_id, s.student_id, s.status, s.grade, s.submitted_at,
                        u.username as student_username, u.full_name as student_name
                 FROM submissions s
                 JOIN users u ON s.student_id = u.id
                 WHERE s.session_id = :sid
                 ORDER BY s.submitted_at DESC",
                [':sid' => $id]
            );
        }

        json_response(['session' => $session]);
        break;

    // ─── CREAR SESIÓN ───────────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $body = get_json_body();

        $errors = validate_required($body, ['title']);
        $date = $body['scheduledDate'] ?? $body['scheduled_date'] ?? null;
        $time = $body['scheduledTime'] ?? $body['scheduled_time'] ?? null;
        if ($date) $errors[] = validate_date($date);
        if ($time) $errors[] = validate_time($time);
        validate_or_fail($errors);

        $status = 'active';
        $approvedBy = $auth['sub'];

        $sessionId = Database::uuid();
        Database::execute(
            "INSERT INTO practice_sessions (id, title, description, created_by, approved_by, status,
                scheduled_date, scheduled_time, duration_minutes, location, group_id,
                instructions, max_submissions, allow_late_submission, due_date,
                session_type, course_id, centro_enabled, end_date)
             VALUES (:id, :title, :desc, :uid, :approved, :status,
                :date, :time, :dur, :loc, :gid,
                :instr, :max, :late, :due,
                :stype, :cid, :centro, :edate)",
            [
                ':id' => $sessionId,
                ':title' => $body['title'],
                ':desc' => $body['description'] ?? null,
                ':uid' => $auth['sub'],
                ':approved' => $approvedBy,
                ':status' => $status,
                ':date' => $body['scheduledDate'] ?? $body['scheduled_date'] ?? null,
                ':time' => $body['scheduledTime'] ?? $body['scheduled_time'] ?? null,
                ':dur' => $body['durationMinutes'] ?? $body['duration_minutes'] ?? 90,
                ':loc' => $body['location'] ?? null,
                ':gid' => $body['groupId'] ?? $body['group_id'] ?? null,
                ':instr' => $body['instructions'] ?? null,
                ':max' => $body['maxSubmissions'] ?? $body['max_submissions'] ?? 1,
                ':late' => (int)($body['allowLateSubmission'] ?? $body['allow_late_submission'] ?? 0),
                ':due' => $body['dueDate'] ?? $body['due_date'] ?? null,
                ':stype' => $body['sessionType'] ?? $body['session_type'] ?? 'conjunto',
                ':cid' => $body['courseId'] ?? $body['course_id'] ?? null,
                ':centro' => (int)($body['centroEnabled'] ?? $body['centro_enabled'] ?? 0),
                ':edate' => $body['endDate'] ?? $body['end_date'] ?? null,
            ]
        );

        $session = Database::fetchOne('SELECT * FROM practice_sessions WHERE id = :id', [':id' => $sessionId]);
        created_response(['session' => $session]);
        break;

    // ─── ACTUALIZAR SESIÓN ──────────────────────────
    case $method === 'PUT' && $id !== null && $action === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $session = Database::fetchOne('SELECT id, created_by, status FROM practice_sessions WHERE id = :id', [':id' => $id]);
        if (!$session) error_response('Sesión no encontrada', 404);

        if ($auth['role'] !== 'admin' && $auth['sub'] !== $session['created_by']) {
            error_response('Permisos insuficientes', 403);
        }

        $body = get_json_body();
        $fields = [];
        $params = [':id' => $id];

        $mapping = [
            'title' => 'title', 'description' => 'description', 'location' => 'location',
            'instructions' => 'instructions', 'dueDate' => 'due_date', 'due_date' => 'due_date',
            'scheduledDate' => 'scheduled_date', 'scheduled_date' => 'scheduled_date',
            'endDate' => 'end_date', 'end_date' => 'end_date',
            'scheduledTime' => 'scheduled_time', 'scheduled_time' => 'scheduled_time',
            'durationMinutes' => 'duration_minutes', 'duration_minutes' => 'duration_minutes',
            'groupId' => 'group_id', 'group_id' => 'group_id',
            'maxSubmissions' => 'max_submissions', 'max_submissions' => 'max_submissions',
            'allowLateSubmission' => 'allow_late_submission', 'allow_late_submission' => 'allow_late_submission',
            'sessionType' => 'session_type', 'session_type' => 'session_type',
            'courseId' => 'course_id', 'course_id' => 'course_id',
            'centroEnabled' => 'centro_enabled', 'centro_enabled' => 'centro_enabled',
        ];

        foreach ($body as $key => $value) {
            if (isset($mapping[$key])) {
                $dbKey = $mapping[$key];
                $fields[] = "$dbKey = :$dbKey";
                $params[":$dbKey"] = $value;
            }
        }

        if (empty($fields)) error_response('No hay campos para actualizar', 400);

        $fields[] = "updated_at = datetime('now')";
        Database::execute("UPDATE practice_sessions SET " . implode(', ', $fields) . " WHERE id = :id", $params);

        json_response(['session' => Database::fetchOne('SELECT * FROM practice_sessions WHERE id = :id', [':id' => $id])]);
        break;

    // ─── ELIMINAR SESIÓN ────────────────────────────
    case $method === 'DELETE' && $id !== null && $action === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $session = Database::fetchOne('SELECT id, created_by FROM practice_sessions WHERE id = :id', [':id' => $id]);
        if (!$session) error_response('Sesión no encontrada', 404);

        if ($auth['role'] !== 'admin' && $auth['sub'] !== $session['created_by']) {
            error_response('Solo el creador o un admin puede eliminar esta sesión', 403);
        }

        // Eliminar agenda_items vinculados
        Database::execute('DELETE FROM agenda_items WHERE session_id = :sid', [':sid' => $id]);
        // Eliminar casos vinculados
        Database::execute('DELETE FROM practice_session_cases WHERE session_id = :sid', [':sid' => $id]);
        // Eliminar guías
        Database::execute('DELETE FROM session_guides WHERE session_id = :sid', [':sid' => $id]);
        // Eliminar la sesión
        Database::execute('DELETE FROM practice_sessions WHERE id = :id', [':id' => $id]);

        json_response(['message' => 'Sesión eliminada']);
        break;

    // ─── COMPLETAR SESIÓN ───────────────────────────
    case $method === 'POST' && $action === 'complete':
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $session = Database::fetchOne('SELECT id, status, created_by FROM practice_sessions WHERE id = :id', [':id' => $id]);
        if (!$session) error_response('Sesión no encontrada', 404);
        if (!in_array($session['status'], ['active', 'approved'])) {
            error_response('Solo se pueden completar sesiones activas', 400);
        }

        Database::execute(
            "UPDATE practice_sessions SET status = 'completed', updated_at = datetime('now') WHERE id = :id",
            [':id' => $id]
        );
        json_response(['message' => 'Sesión completada']);
        break;

    // ─── AGREGAR CASO A SESIÓN ──────────────────────
    case $method === 'POST' && $action === 'cases':
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $body = get_json_body();

        $errors = validate_required($body, ['caseId']);
        validate_or_fail($errors);

        $session = Database::fetchOne('SELECT id, created_by FROM practice_sessions WHERE id = :id', [':id' => $id]);
        if (!$session) error_response('Sesión no encontrada', 404);

        $caso = Database::fetchOne('SELECT id FROM cases WHERE id = :id', [':id' => $body['caseId']]);
        if (!$caso) error_response('Caso no encontrado', 404);

        $existing = Database::fetchOne(
            'SELECT session_id FROM practice_session_cases WHERE session_id = :sid AND case_id = :cid',
            [':sid' => $id, ':cid' => $body['caseId']]
        );
        if ($existing) error_response('El caso ya está en esta sesión', 409);

        Database::execute(
            "INSERT INTO practice_session_cases (session_id, case_id, order_index, is_required)
             VALUES (:sid, :cid, :ord, :req)",
            [
                ':sid' => $id,
                ':cid' => $body['caseId'],
                ':ord' => $body['orderIndex'] ?? $body['order_index'] ?? 0,
                ':req' => (int)($body['isRequired'] ?? $body['is_required'] ?? 1),
            ]
        );
        json_response(['message' => 'Caso agregado a la sesión']);
        break;

    // ─── QUITAR CASO DE SESIÓN ──────────────────────
    case $method === 'DELETE' && $action === 'cases' && $subId !== null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        Database::execute(
            'DELETE FROM practice_session_cases WHERE session_id = :sid AND case_id = :cid',
            [':sid' => $id, ':cid' => $subId]
        );
        json_response(['message' => 'Caso removido de la sesión']);
        break;

    // ─── LISTAR GUÍAS ───────────────────────────────
    case $method === 'GET' && $action === 'guides' && $subId === null:
        $auth = require_auth();

        $guides = Database::fetchAll(
            "SELECT sg.id, sg.title, sg.description, sg.file_size, sg.mime_type, sg.guide_type,
                    sg.external_url, sg.created_at, u.username as uploader
             FROM session_guides sg
             LEFT JOIN users u ON sg.uploaded_by = u.id
             WHERE sg.session_id = :sid
             ORDER BY sg.created_at",
            [':sid' => $id]
        );
        json_response(['guides' => $guides]);
        break;

    // ─── SUBIR GUÍA ─────────────────────────────────
    case $method === 'POST' && $action === 'guides' && $subId === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $session = Database::fetchOne('SELECT id FROM practice_sessions WHERE id = :id', [':id' => $id]);
        if (!$session) error_response('Sesión no encontrada', 404);

        $title = $_POST['title'] ?? 'Sin título';
        $description = $_POST['description'] ?? null;
        $guideType = $_POST['guideType'] ?? $_POST['guide_type'] ?? 'document';

        // Si es un link externo
        $externalUrl = $_POST['externalUrl'] ?? $_POST['external_url'] ?? null;
        if ($externalUrl) {
            $guideId = Database::uuid();
            Database::execute(
                "INSERT INTO session_guides (id, session_id, uploaded_by, title, description, file_path, guide_type, external_url)
                 VALUES (:id, :sid, :uid, :title, :desc, '', :type, :url)",
                [
                    ':id' => $guideId, ':sid' => $id, ':uid' => $auth['sub'],
                    ':title' => $title, ':desc' => $description, ':type' => 'link', ':url' => $externalUrl,
                ]
            );
            created_response(['guide' => Database::fetchOne('SELECT * FROM session_guides WHERE id = :id', [':id' => $guideId])]);
            break;
        }

        $upload = handle_upload('file', 'guides', ALLOWED_GUIDE_TYPES);

        $guideId = Database::uuid();
        Database::execute(
            "INSERT INTO session_guides (id, session_id, uploaded_by, title, description, file_path, file_size, mime_type, guide_type)
             VALUES (:id, :sid, :uid, :title, :desc, :path, :size, :mime, :type)",
            [
                ':id' => $guideId, ':sid' => $id, ':uid' => $auth['sub'],
                ':title' => $title, ':desc' => $description,
                ':path' => $upload['path'], ':size' => $upload['size'], ':mime' => $upload['mime'],
                ':type' => $guideType,
            ]
        );

        created_response(['guide' => Database::fetchOne('SELECT * FROM session_guides WHERE id = :id', [':id' => $guideId])]);
        break;

    // ─── DESCARGAR GUÍA ─────────────────────────────
    case $method === 'GET' && $action === 'guides' && $subId !== null && $subAction === 'download':
        $auth = require_auth();

        $guide = Database::fetchOne(
            'SELECT file_path, title FROM session_guides WHERE id = :id AND session_id = :sid',
            [':id' => $subId, ':sid' => $id]
        );
        if (!$guide) error_response('Guía no encontrada', 404);
        if (!$guide['file_path']) error_response('Esta guía es un enlace externo', 400);

        send_file_download($guide['file_path'], $guide['title']);
        break;

    // ─── ELIMINAR GUÍA ──────────────────────────────
    case $method === 'DELETE' && $action === 'guides' && $subId !== null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $guide = Database::fetchOne(
            'SELECT id, file_path FROM session_guides WHERE id = :id AND session_id = :sid',
            [':id' => $subId, ':sid' => $id]
        );
        if (!$guide) error_response('Guía no encontrada', 404);

        if ($guide['file_path']) {
            delete_upload($guide['file_path']);
        }
        Database::execute('DELETE FROM session_guides WHERE id = :id', [':id' => $subId]);

        json_response(['message' => 'Guía eliminada']);
        break;

    default:
        error_response("Ruta no encontrada: sessions/" . implode('/', $routeSegments), 404);
}
