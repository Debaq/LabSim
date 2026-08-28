<?php

final class Auth
{
    /**
     * Genera un código de 6 dígitos que el alumno escribe en la app de
     * escritorio para vincular la sesión iniciada por LTI en el navegador.
     */
    public static function createPairingCode(int $userId): string
    {
        $pdo = Db::get();
        $cfg = Db::config();
        $ttl = $cfg['pairing_code_ttl_seconds'];

        do {
            $code = str_pad((string) random_int(0, 999999), 6, '0', STR_PAD_LEFT);
            $stmt = $pdo->prepare('SELECT 1 FROM pairing_codes WHERE code = ? AND used = 0 AND expires_at > CURRENT_TIMESTAMP');
            $stmt->execute([$code]);
        } while ($stmt->fetch());

        $stmt = $pdo->prepare(
            "INSERT INTO pairing_codes (code, user_id, expires_at) VALUES (?, ?, datetime(CURRENT_TIMESTAMP, '+' || ? || ' seconds'))"
        );
        $stmt->execute([$code, $userId, $ttl]);

        return $code;
    }

    /**
     * Código vigente para $userId: si $previousCode sigue sin usarse y no
     * venció, lo reusa (mismo código en pantalla, no confunde al alumno con
     * uno nuevo cada vez que recarga); si no, emite uno nuevo. Usado tanto
     * en el primer launch como al refrescar manualmente o al vencer.
     */
    public static function codeForLaunch(int $userId, ?string $previousCode): array
    {
        if ($previousCode !== null && self::pairingCodeStillValid($previousCode)) {
            return ['code' => $previousCode, 'expires_at' => self::pairingCodeExpiry($previousCode), 'renewed' => false];
        }
        $code = self::createPairingCode($userId);
        return ['code' => $code, 'expires_at' => self::pairingCodeExpiry($code), 'renewed' => true];
    }

    public static function pairingCodeStillValid(string $code): bool
    {
        $stmt = Db::get()->prepare('SELECT 1 FROM pairing_codes WHERE code = ? AND used = 0 AND expires_at > CURRENT_TIMESTAMP');
        $stmt->execute([$code]);
        return (bool) $stmt->fetch();
    }

    public static function pairingCodeExpiry(string $code): ?string
    {
        $stmt = Db::get()->prepare('SELECT expires_at FROM pairing_codes WHERE code = ?');
        $stmt->execute([$code]);
        $value = $stmt->fetchColumn();
        return $value === false ? null : $value;
    }

    /** Segundos hasta un datetime de SQLite (UTC, igual que CURRENT_TIMESTAMP) -- nunca negativo. */
    public static function secondsUntil(string $sqliteDatetime): int
    {
        return max(0, (int) strtotime($sqliteDatetime . ' UTC') - time());
    }

    /**
     * Cambia un código de emparejamiento válido por un token de sesión de la app.
     * Devuelve null si el código no existe, ya se usó o expiró.
     */
    public static function exchangePairingCode(string $code): ?array
    {
        $pdo = Db::get();

        $stmt = $pdo->prepare(
            'SELECT user_id FROM pairing_codes WHERE code = ? AND used = 0 AND expires_at > CURRENT_TIMESTAMP'
        );
        $stmt->execute([$code]);
        $row = $stmt->fetch();
        if (!$row) {
            return null;
        }

        $pdo->prepare('UPDATE pairing_codes SET used = 1 WHERE code = ?')->execute([$code]);

        return self::issueTokenFor((int) $row['user_id']);
    }

    /**
     * Login local usuario/contraseña. Los alumnos normalmente entran por
     * LTI (sin password_hash), pero una cuenta local puede tener cualquier
     * rol -- por ejemplo un alumno de prueba para probar el flujo de
     * atención sin depender de Moodle. Devuelve null si no existe el
     * usuario, no tiene contraseña local, o la contraseña no calza.
     */
    public static function loginAdmin(string $username, string $password): ?array
    {
        $stmt = Db::get()->prepare('SELECT * FROM users WHERE username = ? AND active = 1');
        $stmt->execute([$username]);
        $row = $stmt->fetch();
        if (!$row || !$row['password_hash'] || !password_verify($password, $row['password_hash'])) {
            return null;
        }
        return self::issueTokenFor((int) $row['id']);
    }

    /**
     * Verifica usuario/contraseña de un admin para el portal (navegador,
     * sesión PHP -- no emite un Bearer token, no lo necesita).
     */
    public static function verifyAdminPassword(string $username, string $password): ?array
    {
        $stmt = Db::get()->prepare("SELECT * FROM users WHERE username = ? AND role = 'admin' AND active = 1");
        $stmt->execute([$username]);
        $row = $stmt->fetch();
        if (!$row || !$row['password_hash'] || !password_verify($password, $row['password_hash'])) {
            return null;
        }
        return $row;
    }

    /** Corta con 403 si no hay una sesión de portal admin válida. */
    public static function requireAdminSession(): array
    {
        if (session_status() !== PHP_SESSION_ACTIVE) {
            session_start();
        }
        $userId = $_SESSION['admin_user_id'] ?? null;
        if (!$userId) {
            header('Location: login.php');
            exit;
        }
        $stmt = Db::get()->prepare("SELECT * FROM users WHERE id = ? AND role = 'admin' AND active = 1");
        $stmt->execute([$userId]);
        $user = $stmt->fetch();
        if (!$user) {
            unset($_SESSION['admin_user_id']);
            header('Location: login.php');
            exit;
        }
        return $user;
    }

    private static function issueTokenFor(int $userId): array
    {
        $token = bin2hex(random_bytes(32));
        Db::get()->prepare('INSERT INTO tokens (token, user_id) VALUES (?, ?)')->execute([$token, $userId]);
        return [
            'token' => $token,
            'user' => self::userProfile($userId),
        ];
    }

    /**
     * Valida el header Authorization: Bearer <token> y devuelve el usuario,
     * o corta la request con 401 si no es válido.
     */
    public static function requireUser(): array
    {
        $header = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
        if (!preg_match('/^Bearer\s+(\S+)$/', $header, $m)) {
            Response::error('Falta token de autorización', 401);
        }
        $token = $m[1];

        $pdo = Db::get();
        $stmt = $pdo->prepare(
            'SELECT u.* FROM tokens t JOIN users u ON u.id = t.user_id WHERE t.token = ? AND u.active = 1'
        );
        $stmt->execute([$token]);
        $user = $stmt->fetch();
        if (!$user) {
            Response::error('Token inválido o expirado', 401);
        }

        $pdo->prepare('UPDATE tokens SET last_seen_at = CURRENT_TIMESTAMP WHERE token = ?')->execute([$token]);

        return $user;
    }

    public static function requireAdmin(): array
    {
        $user = self::requireUser();
        if ($user['role'] !== 'admin') {
            Response::error('Requiere permisos de administrador', 403);
        }
        return $user;
    }

    private static function userProfile(int $userId): array
    {
        $stmt = Db::get()->prepare('SELECT id, role, username, display_name, permission, modules FROM users WHERE id = ?');
        $stmt->execute([$userId]);
        $user = $stmt->fetch();
        // PDO_SQLITE puede devolver columnas numéricas como string según
        // versión -- forzar int acá para que el JSON siempre mande un
        // número, no un string. La app compara `permission == 777` (int)
        // para decidir la vista de agenda admin vs alumno.
        $user['permission'] = (int) $user['permission'];
        $user['modules'] = json_decode($user['modules'] ?? '[]', true);
        return $user;
    }
}
