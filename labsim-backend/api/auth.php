<?php
/**
 * LabSim Backend - Auth endpoints
 *
 * POST /auth/login            → Login con username/password
 * POST /auth/refresh          → Refresh access token
 * POST /auth/logout           → Invalidar refresh token
 * POST /auth/change-password  → Cambiar contraseña propia
 * GET  /auth/me               → Datos del usuario autenticado
 */

require_once __DIR__ . '/../core/jwt.php';
require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$action = $routeSegments[0] ?? '';

switch ("$method:$action") {

    // ─── LOGIN ───────────────────────────────────────
    case 'POST:login':
        $body = get_json_body();
        $errors = validate_required($body, ['username', 'password']);
        validate_or_fail($errors);

        $ip = $_SERVER['REMOTE_ADDR'] ?? '0.0.0.0';
        check_login_rate_limit($ip);

        $user = Database::fetchOne(
            'SELECT id, username, password_hash, role, full_name, email, institution, is_active, must_change_password
             FROM users WHERE username = :username',
            [':username' => $body['username']]
        );

        if (!$user || !password_verify($body['password'], $user['password_hash'])) {
            record_login_attempt($ip, false);
            error_response('Credenciales inválidas', 401);
        }

        if (!$user['is_active']) {
            error_response('Cuenta desactivada. Contacta al administrador', 403);
        }

        record_login_attempt($ip, true);

        $accessToken = JWT::createAccessToken($user['id'], $user['username'], $user['role']);
        $refreshToken = JWT::createRefreshToken($user['id']);

        // Guardar hash del refresh token
        $tokenId = Database::uuid();
        Database::execute(
            "INSERT INTO refresh_tokens (id, user_id, token_hash, expires_at)
             VALUES (:id, :uid, :hash, datetime('now', '+30 days'))",
            [
                ':id' => $tokenId,
                ':uid' => $user['id'],
                ':hash' => hash('sha256', $refreshToken),
            ]
        );

        json_response([
            'accessToken' => $accessToken,
            'refreshToken' => $refreshToken,
            'user' => [
                'id' => $user['id'],
                'username' => $user['username'],
                'role' => $user['role'],
                'fullName' => $user['full_name'],
                'email' => $user['email'],
                'institution' => $user['institution'],
                'mustChangePassword' => (bool)$user['must_change_password'],
            ],
        ]);
        break;

    // ─── REFRESH ─────────────────────────────────────
    case 'POST:refresh':
        $body = get_json_body();
        if (empty($body['refreshToken'])) {
            error_response('refreshToken requerido', 400);
        }

        try {
            $payload = JWT::decode($body['refreshToken']);
        } catch (Exception $e) {
            error_response('Refresh token inválido: ' . $e->getMessage(), 401);
        }

        if (($payload['type'] ?? '') !== 'refresh') {
            error_response('Se requiere un refresh token', 401);
        }

        // Verificar que el token existe en BD
        $tokenHash = hash('sha256', $body['refreshToken']);
        $stored = Database::fetchOne(
            "SELECT id FROM refresh_tokens WHERE token_hash = :hash AND user_id = :uid AND expires_at > datetime('now')",
            [':hash' => $tokenHash, ':uid' => $payload['sub']]
        );

        if (!$stored) {
            error_response('Refresh token revocado o expirado', 401);
        }

        // Obtener datos actuales del usuario
        $user = Database::fetchOne(
            'SELECT id, username, role, is_active FROM users WHERE id = :id',
            [':id' => $payload['sub']]
        );

        if (!$user || !$user['is_active']) {
            error_response('Usuario no encontrado o desactivado', 401);
        }

        $accessToken = JWT::createAccessToken($user['id'], $user['username'], $user['role']);

        json_response([
            'accessToken' => $accessToken,
        ]);
        break;

    // ─── LOGOUT ──────────────────────────────────────
    case 'POST:logout':
        $body = get_json_body();

        if (!empty($body['refreshToken'])) {
            $tokenHash = hash('sha256', $body['refreshToken']);
            Database::execute(
                'DELETE FROM refresh_tokens WHERE token_hash = :hash',
                [':hash' => $tokenHash]
            );
        }

        // Si hay access token, intentar revocar todos los refresh del usuario
        $auth = optional_auth();
        if ($auth && empty($body['refreshToken'])) {
            Database::execute(
                'DELETE FROM refresh_tokens WHERE user_id = :uid',
                [':uid' => $auth['sub']]
            );
        }

        json_response(['message' => 'Sesión cerrada']);
        break;

    // ─── CAMBIAR CONTRASEÑA (cualquier usuario autenticado) ─
    case 'POST:change-password':
        $auth = require_auth();
        $body = get_json_body();

        $errors = validate_required($body, ['currentPassword', 'newPassword']);
        $errors[] = validate_password($body['newPassword'] ?? '');
        validate_or_fail($errors);

        $user = Database::fetchOne(
            'SELECT id, password_hash FROM users WHERE id = :id',
            [':id' => $auth['sub']]
        );

        if (!$user || !password_verify($body['currentPassword'], $user['password_hash'])) {
            error_response('Contraseña actual incorrecta', 401);
        }

        Database::execute(
            "UPDATE users SET password_hash = :hash, must_change_password = 0, updated_at = datetime('now') WHERE id = :id",
            [':id' => $auth['sub'], ':hash' => password_hash($body['newPassword'], PASSWORD_BCRYPT)]
        );

        // Revocar todos los refresh tokens para forzar re-login en otros dispositivos
        Database::execute('DELETE FROM refresh_tokens WHERE user_id = :uid', [':uid' => $auth['sub']]);

        json_response(['message' => 'Contraseña actualizada']);
        break;

    // ─── ME ──────────────────────────────────────────
    case 'GET:me':
        $auth = require_auth();

        $user = Database::fetchOne(
            'SELECT id, username, email, role, full_name, institution, created_at
             FROM users WHERE id = :id',
            [':id' => $auth['sub']]
        );

        if (!$user) {
            error_response('Usuario no encontrado', 404);
        }

        json_response(['user' => $user]);
        break;

    default:
        error_response("Ruta no encontrada: auth/$action", 404);
}
