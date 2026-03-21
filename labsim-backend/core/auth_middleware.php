<?php
/**
 * LabSim Backend - Middleware de autenticación JWT
 */

require_once __DIR__ . '/jwt.php';
require_once __DIR__ . '/response.php';
require_once __DIR__ . '/db.php';

/**
 * Verifica el JWT del header Authorization y retorna el payload
 * @param string|array|null $requiredRole Rol(es) requerido(s), null = cualquier autenticado
 * @return array JWT payload con datos del usuario
 */
function require_auth($requiredRole = null) {
    $header = $_SERVER['HTTP_AUTHORIZATION'] ?? '';

    if (!preg_match('/^Bearer\s+(.+)$/i', $header, $matches)) {
        error_response('Token de autenticación requerido', 401);
    }

    try {
        $payload = JWT::decode($matches[1]);
    } catch (Exception $e) {
        error_response('Token inválido: ' . $e->getMessage(), 401);
    }

    if (($payload['type'] ?? '') !== 'access') {
        error_response('Se requiere un access token', 401);
    }

    // Verificar que el usuario existe y está activo
    $user = Database::fetchOne(
        'SELECT id, role, is_active FROM users WHERE id = :id',
        [':id' => $payload['sub']]
    );

    if (!$user || !$user['is_active']) {
        error_response('Usuario no encontrado o desactivado', 401);
    }

    // Verificar rol
    if ($requiredRole !== null) {
        $roles = is_array($requiredRole) ? $requiredRole : [$requiredRole];
        if (!in_array($user['role'], $roles, true)) {
            error_response('Permisos insuficientes', 403);
        }
    }

    return $payload;
}

/**
 * Intenta autenticar si hay token, pero no falla si no hay
 * @return array|null payload o null
 */
function optional_auth(): ?array {
    $header = $_SERVER['HTTP_AUTHORIZATION'] ?? '';

    if (!preg_match('/^Bearer\s+(.+)$/i', $header, $matches)) {
        return null;
    }

    try {
        $payload = JWT::decode($matches[1]);
        if (($payload['type'] ?? '') !== 'access') {
            return null;
        }
        return $payload;
    } catch (Exception $e) {
        return null;
    }
}

/**
 * Verifica que el usuario autenticado es admin o el dueño del recurso
 */
function require_owner_or_admin(array $auth, string $resourceOwnerId): void {
    if ($auth['role'] !== 'admin' && $auth['sub'] !== $resourceOwnerId) {
        error_response('No tienes permiso para este recurso', 403);
    }
}

/**
 * Verifica rate limiting para login
 */
function check_login_rate_limit(string $ip): void {
    // Limpiar intentos viejos
    Database::execute(
        "DELETE FROM login_attempts WHERE attempted_at < datetime('now', :window)",
        [':window' => '-' . LOGIN_LOCKOUT_MINUTES . ' minutes']
    );

    $attempts = Database::fetchOne(
        "SELECT COUNT(*) as count FROM login_attempts WHERE ip_address = :ip AND attempted_at > datetime('now', :window)",
        [':ip' => $ip, ':window' => '-' . LOGIN_LOCKOUT_MINUTES . ' minutes']
    );

    if (($attempts['count'] ?? 0) >= LOGIN_MAX_ATTEMPTS) {
        error_response('Demasiados intentos de login. Intenta en ' . LOGIN_LOCKOUT_MINUTES . ' minutos', 429);
    }
}

/**
 * Registra un intento de login
 */
function record_login_attempt(string $ip, bool $success): void {
    if ($success) {
        // Limpiar intentos exitosos
        Database::execute(
            'DELETE FROM login_attempts WHERE ip_address = :ip',
            [':ip' => $ip]
        );
    } else {
        Database::execute(
            'INSERT INTO login_attempts (ip_address, attempted_at) VALUES (:ip, datetime(\'now\'))',
            [':ip' => $ip]
        );
    }
}
