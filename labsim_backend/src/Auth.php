<?php

final class Auth
{
    // Distinción de nivel dentro de role='admin' (el CHECK de users.role
    // solo admite 'student'|'admin' -- un tercer rol real requeriría
    // migrar schema). El docente entra al portal igual que un admin
    // completo pero requireFullAdminSession() le corta el paso en las
    // páginas de gestión (Usuarios, LTI, Estado).
    public const PERMISSION_ADMIN = 777;
    public const PERMISSION_DOCENTE = 555;

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
     * Token de un solo uso para el handoff al portal admin/docente desde el
     * launch LTI -- launch.php corre dentro del iframe de Moodle (cookie de
     * tercero, muchos navegadores hoy la descartan) así que NO se puede
     * confiar en levantar la sesión de portal ahí mismo; en cambio se abre
     * una pestaña nueva a admin/sso.php?token=... que sí es un request de
     * primer partido y puede levantar la cookie de sesión sin problema.
     * Vida corta (60s) y de un solo uso -- no es para reusar, solo para el
     * primer request de esa pestaña.
     */
    public static function issuePortalSsoToken(int $userId): string
    {
        $token = bin2hex(random_bytes(32));
        Db::get()->prepare(
            "INSERT INTO portal_sso_tokens (token, user_id, expires_at) VALUES (?, ?, datetime(CURRENT_TIMESTAMP, '+60 seconds'))"
        )->execute([$token, $userId]);
        return $token;
    }

    /** Canjea un token de issuePortalSsoToken(): user_id si es válido (sin usar, sin vencer), o null. */
    public static function consumePortalSsoToken(string $token): ?int
    {
        $pdo = Db::get();
        $stmt = $pdo->prepare(
            'SELECT user_id FROM portal_sso_tokens WHERE token = ? AND used = 0 AND expires_at > CURRENT_TIMESTAMP'
        );
        $stmt->execute([$token]);
        $userId = $stmt->fetchColumn();
        if ($userId === false) {
            return null;
        }
        $pdo->prepare('UPDATE portal_sso_tokens SET used = 1 WHERE token = ?')->execute([$token]);
        return (int) $userId;
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

    private const LOGIN_MAX_ATTEMPTS = 5;
    private const LOGIN_WINDOW_SECONDS = 900; // 15 min

    /**
     * true si $username o $ip ya acumularon LOGIN_MAX_ATTEMPTS fallos en los
     * últimos LOGIN_WINDOW_SECONDS -- corta el intento de login.php ANTES de
     * tocar password_verify(), así un bloqueo no cuesta ni el hash.
     */
    public static function loginBlocked(string $username, string $ip): bool
    {
        $pdo = Db::get();
        $windowSql = "created_at > datetime('now', '-' || ? || ' seconds')";

        $stmt = $pdo->prepare("SELECT COUNT(*) FROM login_attempts WHERE ip = ? AND success = 0 AND {$windowSql}");
        $stmt->execute([$ip, self::LOGIN_WINDOW_SECONDS]);
        if ((int) $stmt->fetchColumn() >= self::LOGIN_MAX_ATTEMPTS) {
            return true;
        }

        $stmt = $pdo->prepare("SELECT COUNT(*) FROM login_attempts WHERE username = ? AND success = 0 AND {$windowSql}");
        $stmt->execute([$username, self::LOGIN_WINDOW_SECONDS]);
        return (int) $stmt->fetchColumn() >= self::LOGIN_MAX_ATTEMPTS;
    }

    /** Deja constancia de cada intento (éxito o fallo) -- lo que lee loginBlocked(). */
    public static function recordLoginAttempt(string $username, string $ip, bool $success): void
    {
        $pdo = Db::get();
        $pdo->prepare('INSERT INTO login_attempts (username, ip, success) VALUES (?, ?, ?)')
            ->execute([$username, $ip, $success ? 1 : 0]);
        // Purga oportunista de intentos viejos -- evita que la tabla crezca
        // sin límite sin necesitar un cron aparte para algo tan chico.
        $pdo->exec("DELETE FROM login_attempts WHERE created_at < datetime('now', '-1 day')");
    }

    private const PAIR_EXCHANGE_MAX_ATTEMPTS = 15;
    private const PAIR_EXCHANGE_WINDOW_SECONDS = 300; // igual al TTL del código

    /**
     * true si $ip ya acumuló PAIR_EXCHANGE_MAX_ATTEMPTS fallos en los
     * últimos PAIR_EXCHANGE_WINDOW_SECONDS -- corta pair_exchange.php antes
     * de tocar la tabla pairing_codes.
     */
    public static function pairExchangeBlocked(string $ip): bool
    {
        $stmt = Db::get()->prepare(
            "SELECT COUNT(*) FROM pair_exchange_attempts WHERE ip = ? AND success = 0 AND created_at > datetime('now', '-' || ? || ' seconds')"
        );
        $stmt->execute([$ip, self::PAIR_EXCHANGE_WINDOW_SECONDS]);
        return (int) $stmt->fetchColumn() >= self::PAIR_EXCHANGE_MAX_ATTEMPTS;
    }

    /** Deja constancia de cada intento (éxito o fallo) -- lo que lee pairExchangeBlocked(). */
    public static function recordPairExchangeAttempt(string $ip, bool $success): void
    {
        $pdo = Db::get();
        $pdo->prepare('INSERT INTO pair_exchange_attempts (ip, success) VALUES (?, ?)')
            ->execute([$ip, $success ? 1 : 0]);
        $pdo->exec("DELETE FROM pair_exchange_attempts WHERE created_at < datetime('now', '-1 day')");
    }

    /**
     * session_start() con flags de cookie explícitos (HttpOnly siempre,
     * Secure si la request llegó por HTTPS, SameSite=Lax) -- sin esto queda
     * a criterio del php.ini del hosting, que puede no traerlos.
     */
    public static function startSession(): void
    {
        if (session_status() === PHP_SESSION_ACTIVE) {
            return;
        }
        $https = !empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off';
        session_set_cookie_params([
            'lifetime' => 0,
            'path' => '/',
            'secure' => $https,
            'httponly' => true,
            'samesite' => 'Lax',
        ]);
        session_start();
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
        self::startSession();
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

    /** Como requireAdminSession(), pero corta con 403 si es una cuenta docente (permission != admin). */
    public static function requireFullAdminSession(): array
    {
        $user = self::requireAdminSession();
        if ((int) $user['permission'] !== self::PERMISSION_ADMIN) {
            http_response_code(403);
            exit('Requiere permisos de administrador completo.');
        }
        return $user;
    }

    /**
     * Token CSRF de la sesión de portal admin -- uno por sesión, no por
     * form. Se genera al primer pedido y se reusa mientras dure la sesión
     * (session_start() ya lo llamó requireAdminSession()/loginAdmin antes
     * de esto, así que no hace falta acá).
     */
    public static function csrfToken(): string
    {
        if (empty($_SESSION['csrf_token'])) {
            $_SESSION['csrf_token'] = bin2hex(random_bytes(32));
        }
        return $_SESSION['csrf_token'];
    }

    /** Corta con 403 si el POST no trae el csrf_token de la sesión actual. */
    public static function requireCsrf(): void
    {
        $sent = (string) ($_POST['csrf_token'] ?? '');
        $expected = (string) ($_SESSION['csrf_token'] ?? '');
        if ($expected === '' || !hash_equals($expected, $sent)) {
            http_response_code(403);
            exit('Token CSRF inválido o ausente. Recarga la página e inténtalo de nuevo.');
        }
    }

    private const TOKEN_INACTIVE_DAYS = 30;

    private static function issueTokenFor(int $userId): array
    {
        $pdo = Db::get();
        $token = bin2hex(random_bytes(32));
        $pdo->prepare('INSERT INTO tokens (token, user_id) VALUES (?, ?)')->execute([$token, $userId]);
        // Purga oportunista de tokens inactivos -- no se puede borrar "todos
        // menos el último" porque un mismo user entra desde varios
        // dispositivos a la vez; solo se descartan los que ya nadie usa.
        $pdo->exec(
            "DELETE FROM tokens WHERE last_seen_at < datetime('now', '-" . self::TOKEN_INACTIVE_DAYS . " days')"
        );
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
