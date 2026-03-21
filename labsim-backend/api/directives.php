<?php
/**
 * LabSim Backend - Directrices de Karime
 *
 * Sistema jerárquico de configuración del comportamiento de Karime:
 *   global (admin, inamovible) > docente (por actividad) > instructor (ajustes + por sesión)
 *
 * GET    /directives                → Directrices que aplican al usuario actual
 * GET    /directives/all            → Todas las directrices (admin)
 * POST   /directives                → Crear directriz
 * PUT    /directives/:id            → Actualizar directriz
 * DELETE /directives/:id            → Desactivar directriz
 * POST   /directives/:id/approve    → Docente aprueba ajuste de instructor
 * GET    /directives/resolve        → Resolver directrices para una sesión (cascada completa)
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;
$action = $routeSegments[1] ?? null;

switch (true) {

    // ─── RESOLVER DIRECTRICES (cascada para una sesión) ─
    case $method === 'GET' && $id === 'resolve':
        $auth = require_auth();

        $sessionId = query_param('sessionId');

        // 1. Globales (admin, inamovibles)
        $globals = Database::fetchAll(
            "SELECT * FROM karime_directives WHERE scope = 'global' AND is_active = 1 ORDER BY created_at"
        );

        // 2. Docente (del docente que creó la sesión, o del grupo)
        $docenteDirectives = [];
        if ($sessionId) {
            $session = Database::fetchOne(
                "SELECT created_by FROM practice_sessions WHERE id = :sid",
                [':sid' => $sessionId]
            );
            if ($session) {
                $docenteDirectives = Database::fetchAll(
                    "SELECT * FROM karime_directives WHERE scope = 'docente' AND author_id = :uid AND is_active = 1 ORDER BY created_at",
                    [':uid' => $session['created_by']]
                );
            }
        }

        // 3. Instructor (ajustes aprobados + directrices de sesión)
        $instructorDirectives = [];
        if ($sessionId) {
            $instructorDirectives = Database::fetchAll(
                "SELECT * FROM karime_directives WHERE scope IN ('instructor','session')
                 AND (target_session_id = :sid OR target_session_id IS NULL)
                 AND is_active = 1
                 AND (scope = 'session' OR approved_by IS NOT NULL)
                 ORDER BY created_at",
                [':sid' => $sessionId]
            );
        }

        // Resolver cascada: global < docente < instructor
        // Los campos se sobreescriben en orden, excepto is_locked del global
        $resolved = [
            'studentTreatment' => 'formal',
            'tone' => 'profesional',
            'pressureLevel' => 2,
            'customMessages' => new \stdClass(),
            'rules' => [],
        ];

        $lockedFields = [];

        foreach ([$globals, $docenteDirectives, $instructorDirectives] as $layer) {
            foreach ($layer as $d) {
                if (!in_array('studentTreatment', $lockedFields) && $d['student_treatment']) {
                    $resolved['studentTreatment'] = $d['student_treatment'];
                }
                if (!in_array('tone', $lockedFields) && $d['tone']) {
                    $resolved['tone'] = $d['tone'];
                }
                if (!in_array('pressureLevel', $lockedFields) && $d['pressure_level']) {
                    $resolved['pressureLevel'] = (int)$d['pressure_level'];
                }

                $custom = json_decode($d['custom_messages_json'] ?? '{}', true);
                if ($custom) {
                    $resolved['customMessages'] = array_merge(
                        (array)$resolved['customMessages'], $custom
                    );
                }

                if ($d['rules_text']) {
                    $resolved['rules'][] = $d['rules_text'];
                }

                // Si la directriz global está bloqueada, marcar campos
                if ($d['scope'] === 'global' && $d['is_locked']) {
                    if ($d['student_treatment']) $lockedFields[] = 'studentTreatment';
                    if ($d['tone']) $lockedFields[] = 'tone';
                    if ($d['pressure_level']) $lockedFields[] = 'pressureLevel';
                }
            }
        }

        $resolved['rules'] = implode("\n", $resolved['rules']);
        $resolved['lockedFields'] = $lockedFields;

        json_response(['directives' => $resolved]);
        break;

    // ─── LISTAR MIS DIRECTRICES ─────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $where = ['d.is_active = 1'];
        $params = [];

        if ($auth['role'] === 'admin') {
            // Admin ve todo
        } elseif ($auth['role'] === 'docente') {
            $where[] = "(d.scope = 'global' OR d.author_id = :uid)";
            $params[':uid'] = $auth['sub'];
        } else {
            // Instructor ve globales + las del docente de su grupo + las suyas
            $where[] = "(d.scope = 'global' OR d.author_id = :uid OR (d.scope = 'docente' AND EXISTS (
                SELECT 1 FROM group_members gm1
                JOIN group_members gm2 ON gm1.group_id = gm2.group_id
                WHERE gm1.user_id = :uid2 AND gm2.user_id = d.author_id
            )))";
            $params[':uid'] = $auth['sub'];
            $params[':uid2'] = $auth['sub'];
        }

        $sql = "SELECT d.*, u.username as author_username, u.full_name as author_name,
                       a.username as approver_username
                FROM karime_directives d
                LEFT JOIN users u ON d.author_id = u.id
                LEFT JOIN users a ON d.approved_by = a.id
                WHERE " . implode(' AND ', $where) . "
                ORDER BY CASE d.scope
                    WHEN 'global' THEN 1
                    WHEN 'docente' THEN 2
                    WHEN 'instructor' THEN 3
                    WHEN 'session' THEN 4
                END, d.created_at";

        json_response(['directives' => Database::fetchAll($sql, $params)]);
        break;

    // ─── TODAS (admin) ──────────────────────────────
    case $method === 'GET' && $id === 'all':
        $auth = require_auth('admin');

        $directives = Database::fetchAll(
            "SELECT d.*, u.username as author_username, u.full_name as author_name
             FROM karime_directives d LEFT JOIN users u ON d.author_id = u.id
             WHERE d.is_active = 1 ORDER BY d.scope, d.created_at"
        );
        json_response(['directives' => $directives]);
        break;

    // ─── CREAR DIRECTRIZ ────────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $body = get_json_body();

        $errors = validate_required($body, ['title']);
        validate_or_fail($errors);

        // Validar scope según rol
        $scope = $body['scope'] ?? null;
        if ($auth['role'] === 'admin') {
            $scope = $scope ?? 'global';
            if (!in_array($scope, ['global'])) {
                error_response('Admin solo puede crear directrices globales', 400);
            }
        } elseif ($auth['role'] === 'docente') {
            $scope = $scope ?? 'docente';
            if (!in_array($scope, ['docente'])) {
                error_response('Docente solo puede crear directrices de tipo docente', 400);
            }
        } else {
            // Instructor
            $scope = $scope ?? 'session';
            if (!in_array($scope, ['instructor', 'session'])) {
                error_response('Instructor puede crear directrices tipo instructor o session', 400);
            }
        }

        $errors[] = validate_enum($body['tone'] ?? null, ['profesional', 'amigable', 'estricto', 'relajado'], 'tone');
        validate_or_fail($errors);

        // Instructor tipo 'instructor' necesita aprobación del docente
        $needsApproval = ($auth['role'] === 'instructor' && $scope === 'instructor');

        $directiveId = Database::uuid();
        Database::execute(
            "INSERT INTO karime_directives (id, scope, author_id, target_session_id, title,
                student_treatment, tone, pressure_level, custom_messages_json, rules_text,
                is_locked, approved_by)
             VALUES (:id, :scope, :uid, :sid, :title, :treat, :tone, :pressure, :custom, :rules,
                :locked, :approved)",
            [
                ':id' => $directiveId,
                ':scope' => $scope,
                ':uid' => $auth['sub'],
                ':sid' => $body['targetSessionId'] ?? $body['target_session_id'] ?? null,
                ':title' => $body['title'],
                ':treat' => $body['studentTreatment'] ?? $body['student_treatment'] ?? 'formal',
                ':tone' => $body['tone'] ?? 'profesional',
                ':pressure' => $body['pressureLevel'] ?? $body['pressure_level'] ?? 2,
                ':custom' => json_encode($body['customMessages'] ?? $body['custom_messages'] ?? new \stdClass()),
                ':rules' => $body['rulesText'] ?? $body['rules_text'] ?? null,
                ':locked' => ($scope === 'global') ? (int)($body['isLocked'] ?? 1) : 0,
                ':approved' => $needsApproval ? null : $auth['sub'],
            ]
        );

        $directive = Database::fetchOne('SELECT * FROM karime_directives WHERE id = :id', [':id' => $directiveId]);
        created_response([
            'directive' => $directive,
            'needsApproval' => $needsApproval,
        ]);
        break;

    // ─── ACTUALIZAR DIRECTRIZ ───────────────────────
    case $method === 'PUT' && $id !== null && $action === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $directive = Database::fetchOne('SELECT * FROM karime_directives WHERE id = :id', [':id' => $id]);
        if (!$directive) error_response('Directriz no encontrada', 404);

        // Solo el autor o admin pueden editar
        if ($auth['role'] !== 'admin' && $auth['sub'] !== $directive['author_id']) {
            error_response('Permisos insuficientes', 403);
        }

        $body = get_json_body();
        $fields = [];
        $params = [':id' => $id];

        $mapping = [
            'title' => 'title',
            'studentTreatment' => 'student_treatment', 'student_treatment' => 'student_treatment',
            'tone' => 'tone',
            'pressureLevel' => 'pressure_level', 'pressure_level' => 'pressure_level',
            'rulesText' => 'rules_text', 'rules_text' => 'rules_text',
            'isLocked' => 'is_locked', 'is_locked' => 'is_locked',
        ];

        foreach ($body as $key => $value) {
            if (isset($mapping[$key])) {
                $dbKey = $mapping[$key];
                $fields[] = "$dbKey = :$dbKey";
                $params[":$dbKey"] = $value;
            }
        }

        if (isset($body['customMessages']) || isset($body['custom_messages'])) {
            $fields[] = 'custom_messages_json = :custom';
            $params[':custom'] = json_encode($body['customMessages'] ?? $body['custom_messages']);
        }

        if (empty($fields)) error_response('No hay campos para actualizar', 400);

        $fields[] = "updated_at = datetime('now')";
        Database::execute("UPDATE karime_directives SET " . implode(', ', $fields) . " WHERE id = :id", $params);

        json_response(['directive' => Database::fetchOne('SELECT * FROM karime_directives WHERE id = :id', [':id' => $id])]);
        break;

    // ─── APROBAR (docente aprueba ajuste de instructor) ─
    case $method === 'POST' && $id !== null && $action === 'approve':
        $auth = require_auth(['admin', 'docente']);

        $directive = Database::fetchOne(
            "SELECT * FROM karime_directives WHERE id = :id AND scope = 'instructor' AND approved_by IS NULL",
            [':id' => $id]
        );
        if (!$directive) error_response('Directriz no encontrada o ya aprobada', 404);

        Database::execute(
            "UPDATE karime_directives SET approved_by = :uid, updated_at = datetime('now') WHERE id = :id",
            [':id' => $id, ':uid' => $auth['sub']]
        );

        json_response(['message' => 'Directriz aprobada']);
        break;

    // ─── DESACTIVAR ─────────────────────────────────
    case $method === 'DELETE' && $id !== null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $directive = Database::fetchOne('SELECT id, author_id, scope FROM karime_directives WHERE id = :id', [':id' => $id]);
        if (!$directive) error_response('Directriz no encontrada', 404);

        // Admin puede todo, otros solo sus propias
        if ($auth['role'] !== 'admin' && $auth['sub'] !== $directive['author_id']) {
            error_response('Permisos insuficientes', 403);
        }

        Database::execute("UPDATE karime_directives SET is_active = 0, updated_at = datetime('now') WHERE id = :id", [':id' => $id]);
        json_response(['message' => 'Directriz desactivada']);
        break;

    default:
        error_response("Ruta no encontrada: directives/" . implode('/', $routeSegments), 404);
}
