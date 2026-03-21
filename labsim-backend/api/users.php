<?php
/**
 * LabSim Backend - CRUD Usuarios
 *
 * GET    /users              → Lista usuarios (admin)
 * POST   /users              → Crear usuario (admin)
 * GET    /users/:id          → Detalle usuario
 * PUT    /users/:id          → Actualizar usuario (admin)
 * DELETE /users/:id          → Desactivar usuario (admin)
 * POST   /users/:id/reset-password → Reset contraseña (admin)
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;
$action = $routeSegments[1] ?? null;

switch (true) {

    // ─── LISTAR USUARIOS ────────────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth('admin');

        $where = ['1=1'];
        $params = [];

        $role = query_param('role');
        if ($role) {
            $where[] = 'role = :role';
            $params[':role'] = $role;
        }

        $search = query_param('search');
        if ($search) {
            $where[] = "(username LIKE :search OR full_name LIKE :search OR email LIKE :search)";
            $params[':search'] = "%$search%";
        }

        $active = query_param('active');
        if ($active !== null) {
            $where[] = 'is_active = :active';
            $params[':active'] = (int)$active;
        }

        $sql = "SELECT id, username, email, role, full_name, institution, is_active, created_at, updated_at
                FROM users WHERE " . implode(' AND ', $where) . " ORDER BY created_at DESC";

        $page = query_int('page', 1);
        $limit = query_int('limit', DEFAULT_PAGE_SIZE);

        $result = Database::paginate($sql, $params, $page, $limit);
        json_response($result);
        break;

    // ─── CREAR USUARIO ──────────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth('admin');
        $body = get_json_body();

        $errors = validate_required($body, ['username', 'password', 'role']);
        $errors[] = validate_username($body['username'] ?? '');
        $errors[] = validate_password($body['password'] ?? '');
        $errors[] = validate_enum($body['role'] ?? null, ['admin', 'docente', 'instructor', 'estudiante'], 'role');
        $errors[] = validate_email($body['email'] ?? null);
        validate_or_fail($errors);

        // Verificar username único
        $existing = Database::fetchOne(
            'SELECT id FROM users WHERE username = :u',
            [':u' => $body['username']]
        );
        if ($existing) {
            error_response('El username ya está en uso', 409);
        }

        $userId = Database::uuid();
        $mustChange = isset($body['mustChangePassword']) ? (int)$body['mustChangePassword'] : 1;
        Database::execute(
            "INSERT INTO users (id, username, email, password_hash, role, full_name, institution, must_change_password)
             VALUES (:id, :username, :email, :hash, :role, :name, :inst, :mcp)",
            [
                ':id' => $userId,
                ':username' => $body['username'],
                ':email' => $body['email'] ?? null,
                ':hash' => password_hash($body['password'], PASSWORD_BCRYPT),
                ':role' => $body['role'],
                ':name' => $body['fullName'] ?? $body['full_name'] ?? null,
                ':inst' => $body['institution'] ?? null,
                ':mcp' => $mustChange,
            ]
        );

        $user = Database::fetchOne(
            'SELECT id, username, email, role, full_name, institution, is_active, created_at FROM users WHERE id = :id',
            [':id' => $userId]
        );

        created_response(['user' => $user]);
        break;

    // ─── DETALLE USUARIO ────────────────────────────
    case $method === 'GET' && $id !== null && $action === null:
        $auth = require_auth();

        // Admin ve todo, otros solo su propio perfil
        if ($auth['role'] !== 'admin' && $auth['sub'] !== $id) {
            error_response('Permisos insuficientes', 403);
        }

        $user = Database::fetchOne(
            'SELECT id, username, email, role, full_name, institution, is_active, created_at, updated_at
             FROM users WHERE id = :id',
            [':id' => $id]
        );

        if (!$user) {
            error_response('Usuario no encontrado', 404);
        }

        json_response(['user' => $user]);
        break;

    // ─── ACTUALIZAR USUARIO ─────────────────────────
    case $method === 'PUT' && $id !== null && $action === null:
        $auth = require_auth('admin');
        $body = get_json_body();

        $user = Database::fetchOne('SELECT id FROM users WHERE id = :id', [':id' => $id]);
        if (!$user) {
            error_response('Usuario no encontrado', 404);
        }

        $errors = [];
        if (isset($body['role'])) {
            $errors[] = validate_enum($body['role'], ['admin', 'docente', 'instructor', 'estudiante'], 'role');
        }
        if (isset($body['email'])) {
            $errors[] = validate_email($body['email']);
        }
        validate_or_fail($errors);

        // Campos actualizables
        $fields = [];
        $params = [':id' => $id];

        $updatable = ['email', 'role', 'full_name', 'institution', 'is_active'];
        // Aceptar camelCase también
        $mapping = ['fullName' => 'full_name', 'isActive' => 'is_active'];

        foreach ($body as $key => $value) {
            $dbKey = $mapping[$key] ?? $key;
            if (in_array($dbKey, $updatable, true)) {
                $fields[] = "$dbKey = :$dbKey";
                $params[":$dbKey"] = $value;
            }
        }

        if (empty($fields)) {
            error_response('No hay campos para actualizar', 400);
        }

        $fields[] = "updated_at = datetime('now')";
        $sql = "UPDATE users SET " . implode(', ', $fields) . " WHERE id = :id";
        Database::execute($sql, $params);

        $updated = Database::fetchOne(
            'SELECT id, username, email, role, full_name, institution, is_active, created_at, updated_at
             FROM users WHERE id = :id',
            [':id' => $id]
        );

        json_response(['user' => $updated]);
        break;

    // ─── DESACTIVAR USUARIO (soft delete) ───────────
    case $method === 'DELETE' && $id !== null && $action === null:
        $auth = require_auth('admin');

        // No permitir desactivarse a sí mismo
        if ($auth['sub'] === $id) {
            error_response('No puedes desactivar tu propia cuenta', 400);
        }

        $user = Database::fetchOne('SELECT id FROM users WHERE id = :id', [':id' => $id]);
        if (!$user) {
            error_response('Usuario no encontrado', 404);
        }

        Database::execute(
            "UPDATE users SET is_active = 0, updated_at = datetime('now') WHERE id = :id",
            [':id' => $id]
        );

        // Revocar todos sus refresh tokens
        Database::execute('DELETE FROM refresh_tokens WHERE user_id = :uid', [':uid' => $id]);

        json_response(['message' => 'Usuario desactivado']);
        break;

    // ─── RESET PASSWORD ─────────────────────────────
    case $method === 'POST' && $id !== null && $action === 'reset-password':
        $auth = require_auth('admin');
        $body = get_json_body();

        $errors = validate_required($body, ['password']);
        $errors[] = validate_password($body['password'] ?? '');
        validate_or_fail($errors);

        $user = Database::fetchOne('SELECT id FROM users WHERE id = :id', [':id' => $id]);
        if (!$user) {
            error_response('Usuario no encontrado', 404);
        }

        Database::execute(
            "UPDATE users SET password_hash = :hash, must_change_password = 1, updated_at = datetime('now') WHERE id = :id",
            [':id' => $id, ':hash' => password_hash($body['password'], PASSWORD_BCRYPT)]
        );

        // Revocar refresh tokens para forzar re-login
        Database::execute('DELETE FROM refresh_tokens WHERE user_id = :uid', [':uid' => $id]);

        json_response(['message' => 'Contraseña actualizada. El usuario deberá cambiarla al ingresar.']);
        break;

    default:
        error_response("Ruta no encontrada: users/$id" . ($action ? "/$action" : ''), 404);
}
