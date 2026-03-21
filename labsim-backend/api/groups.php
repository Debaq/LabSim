<?php
/**
 * LabSim Backend - CRUD Grupos
 *
 * GET    /groups                    → Lista grupos
 * GET    /groups/:id                → Detalle grupo + miembros
 * POST   /groups                    → Crear grupo (admin/docente)
 * PUT    /groups/:id                → Actualizar grupo
 * DELETE /groups/:id                → Desactivar grupo
 * POST   /groups/:id/members        → Agregar miembro
 * DELETE /groups/:id/members/:uid   → Quitar miembro
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;
$action = $routeSegments[1] ?? null;
$subId = $routeSegments[2] ?? null;

switch (true) {

    // ─── LISTAR GRUPOS ──────────────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth();

        $where = ['g.is_active = 1'];
        $params = [];

        // "mine=true" filtra grupos donde participo
        if (query_param('mine') === 'true') {
            $where[] = "EXISTS (SELECT 1 FROM group_members gm WHERE gm.group_id = g.id AND gm.user_id = :uid)";
            $params[':uid'] = $auth['sub'];
        }

        $search = query_param('search');
        if ($search) {
            $where[] = "(g.name LIKE :search OR g.description LIKE :search)";
            $params[':search'] = "%$search%";
        }

        $sql = "SELECT g.*, u.username as creator_username,
                       (SELECT COUNT(*) FROM group_members gm WHERE gm.group_id = g.id) as member_count
                FROM student_groups g
                LEFT JOIN users u ON g.created_by = u.id
                WHERE " . implode(' AND ', $where) . "
                ORDER BY g.created_at DESC";

        $page = query_int('page', 1);
        $limit = query_int('limit', DEFAULT_PAGE_SIZE);
        json_response(Database::paginate($sql, $params, $page, $limit));
        break;

    // ─── DETALLE GRUPO + MIEMBROS ───────────────────
    case $method === 'GET' && $id !== null && $action === null:
        $auth = require_auth();

        $group = Database::fetchOne(
            "SELECT g.*, u.username as creator_username
             FROM student_groups g
             LEFT JOIN users u ON g.created_by = u.id
             WHERE g.id = :id",
            [':id' => $id]
        );

        if (!$group) {
            error_response('Grupo no encontrado', 404);
        }

        // Miembros
        $members = Database::fetchAll(
            "SELECT gm.member_role, gm.joined_at, u.id, u.username, u.full_name, u.email, u.role
             FROM group_members gm
             JOIN users u ON gm.user_id = u.id
             WHERE gm.group_id = :gid
             ORDER BY gm.member_role, u.full_name",
            [':gid' => $id]
        );

        $group['members'] = $members;
        json_response(['group' => $group]);
        break;

    // ─── CREAR GRUPO ────────────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth(['admin', 'docente']);
        $body = get_json_body();

        $errors = validate_required($body, ['name']);
        validate_or_fail($errors);

        $groupId = Database::uuid();
        Database::execute(
            "INSERT INTO student_groups (id, name, description, institution, created_by)
             VALUES (:id, :name, :desc, :inst, :uid)",
            [
                ':id' => $groupId,
                ':name' => $body['name'],
                ':desc' => $body['description'] ?? null,
                ':inst' => $body['institution'] ?? null,
                ':uid' => $auth['sub'],
            ]
        );

        // Auto-agregar al creador como docente del grupo
        Database::execute(
            "INSERT INTO group_members (group_id, user_id, member_role) VALUES (:gid, :uid, 'docente')",
            [':gid' => $groupId, ':uid' => $auth['sub']]
        );

        $group = Database::fetchOne('SELECT * FROM student_groups WHERE id = :id', [':id' => $groupId]);
        created_response(['group' => $group]);
        break;

    // ─── ACTUALIZAR GRUPO ───────────────────────────
    case $method === 'PUT' && $id !== null && $action === null:
        $auth = require_auth(['admin', 'docente']);

        $group = Database::fetchOne('SELECT id, created_by FROM student_groups WHERE id = :id', [':id' => $id]);
        if (!$group) error_response('Grupo no encontrado', 404);

        if ($auth['role'] !== 'admin' && $auth['sub'] !== $group['created_by']) {
            error_response('Permisos insuficientes', 403);
        }

        $body = get_json_body();
        $fields = [];
        $params = [':id' => $id];

        foreach (['name', 'description', 'institution'] as $f) {
            if (isset($body[$f])) {
                $fields[] = "$f = :$f";
                $params[":$f"] = $body[$f];
            }
        }
        if (isset($body['isActive']) || isset($body['is_active'])) {
            $fields[] = 'is_active = :active';
            $params[':active'] = (int)($body['isActive'] ?? $body['is_active']);
        }

        if (empty($fields)) error_response('No hay campos para actualizar', 400);

        Database::execute("UPDATE student_groups SET " . implode(', ', $fields) . " WHERE id = :id", $params);
        json_response(['group' => Database::fetchOne('SELECT * FROM student_groups WHERE id = :id', [':id' => $id])]);
        break;

    // ─── DESACTIVAR GRUPO ───────────────────────────
    case $method === 'DELETE' && $id !== null && $action === null:
        $auth = require_auth(['admin', 'docente']);

        $group = Database::fetchOne('SELECT id, created_by FROM student_groups WHERE id = :id', [':id' => $id]);
        if (!$group) error_response('Grupo no encontrado', 404);

        if ($auth['role'] !== 'admin' && $auth['sub'] !== $group['created_by']) {
            error_response('Permisos insuficientes', 403);
        }

        Database::execute("UPDATE student_groups SET is_active = 0 WHERE id = :id", [':id' => $id]);
        json_response(['message' => 'Grupo desactivado']);
        break;

    // ─── AGREGAR MIEMBRO ────────────────────────────
    case $method === 'POST' && $id !== null && $action === 'members':
        $auth = require_auth(['admin', 'docente']);
        $body = get_json_body();

        $errors = validate_required($body, ['userId']);
        $errors[] = validate_enum($body['role'] ?? 'student', ['student', 'instructor', 'docente'], 'role');
        validate_or_fail($errors);

        $group = Database::fetchOne('SELECT id FROM student_groups WHERE id = :id AND is_active = 1', [':id' => $id]);
        if (!$group) error_response('Grupo no encontrado', 404);

        $user = Database::fetchOne('SELECT id FROM users WHERE id = :id AND is_active = 1', [':id' => $body['userId']]);
        if (!$user) error_response('Usuario no encontrado', 404);

        // Verificar que no sea ya miembro
        $existing = Database::fetchOne(
            'SELECT group_id FROM group_members WHERE group_id = :gid AND user_id = :uid',
            [':gid' => $id, ':uid' => $body['userId']]
        );
        if ($existing) error_response('El usuario ya es miembro del grupo', 409);

        Database::execute(
            "INSERT INTO group_members (group_id, user_id, member_role) VALUES (:gid, :uid, :role)",
            [':gid' => $id, ':uid' => $body['userId'], ':role' => $body['role'] ?? 'student']
        );

        json_response(['message' => 'Miembro agregado']);
        break;

    // ─── QUITAR MIEMBRO ─────────────────────────────
    case $method === 'DELETE' && $id !== null && $action === 'members' && $subId !== null:
        $auth = require_auth(['admin', 'docente']);

        $group = Database::fetchOne('SELECT id, created_by FROM student_groups WHERE id = :id', [':id' => $id]);
        if (!$group) error_response('Grupo no encontrado', 404);

        if ($auth['role'] !== 'admin' && $auth['sub'] !== $group['created_by']) {
            error_response('Permisos insuficientes', 403);
        }

        Database::execute(
            'DELETE FROM group_members WHERE group_id = :gid AND user_id = :uid',
            [':gid' => $id, ':uid' => $subId]
        );

        json_response(['message' => 'Miembro removido']);
        break;

    default:
        error_response("Ruta no encontrada: groups/" . implode('/', $routeSegments), 404);
}
