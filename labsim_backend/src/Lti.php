<?php

require_once __DIR__ . '/Jwt.php';
require_once __DIR__ . '/OAuth1.php';

/**
 * Conector LTI para Moodle, en dos versiones a la vez (misma tabla
 * lti_platforms, columna `version` las distingue):
 * - 1.3: OIDC third-party initiated login (login.php -> auth.php -> launch.php).
 * - 1.1: OAuth1 2-legged, un solo POST directo a launch.php.
 * Ninguna implementa Deep Linking ni Names/Roles (no se necesitan acá).
 */
final class Lti
{
    public static function findPlatform(string $issuer, string $clientId): ?array
    {
        $stmt = Db::get()->prepare(
            "SELECT * FROM lti_platforms WHERE version = '1.3' AND issuer = ? AND client_id = ? AND active = 1"
        );
        $stmt->execute([$issuer, $clientId]);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    public static function findPlatformByConsumerKey(string $consumerKey): ?array
    {
        $stmt = Db::get()->prepare(
            "SELECT * FROM lti_platforms WHERE version = '1.1' AND consumer_key = ? AND active = 1"
        );
        $stmt->execute([$consumerKey]);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    public static function listPlatforms(): array
    {
        return Db::get()->query('SELECT * FROM lti_platforms ORDER BY id DESC')->fetchAll();
    }

    /** Registra (o edita, si se pasa $id) una plataforma LTI 1.3 -- datos que entrega Moodle al crear la "external tool". */
    public static function upsertPlatform13(
        ?int $id,
        string $issuer,
        string $clientId,
        string $deploymentId,
        string $authLoginUrl,
        string $authTokenUrl,
        string $jwksUrl
    ): int {
        $pdo = Db::get();
        if ($id !== null) {
            $pdo->prepare(
                "UPDATE lti_platforms SET version = '1.3', issuer = ?, client_id = ?, deployment_id = ?,
                        auth_login_url = ?, auth_token_url = ?, jwks_url = ?
                 WHERE id = ?"
            )->execute([$issuer, $clientId, $deploymentId, $authLoginUrl, $authTokenUrl, $jwksUrl, $id]);
            return $id;
        }
        $pdo->prepare(
            "INSERT INTO lti_platforms (version, issuer, client_id, deployment_id, auth_login_url, auth_token_url, jwks_url)
             VALUES ('1.3', ?, ?, ?, ?, ?, ?)"
        )->execute([$issuer, $clientId, $deploymentId, $authLoginUrl, $authTokenUrl, $jwksUrl]);
        return (int) $pdo->lastInsertId();
    }

    /** Registra (o edita, si se pasa $id) una plataforma LTI 1.1 -- consumer key + shared secret que se ponen en Moodle. */
    public static function upsertPlatform11(?int $id, string $consumerKey, string $sharedSecret): int
    {
        $pdo = Db::get();
        if ($id !== null) {
            $pdo->prepare("UPDATE lti_platforms SET version = '1.1', consumer_key = ?, shared_secret = ? WHERE id = ?")
                ->execute([$consumerKey, $sharedSecret, $id]);
            return $id;
        }
        $pdo->prepare("INSERT INTO lti_platforms (version, consumer_key, shared_secret) VALUES ('1.1', ?, ?)")
            ->execute([$consumerKey, $sharedSecret]);
        return (int) $pdo->lastInsertId();
    }

    /** Arma la URL de redirección al auth endpoint de Moodle (paso 1 del OIDC). */
    public static function buildAuthRedirect(array $platform, array $params, string $redirectUri): string
    {
        $state = self::randomUrlSafe();
        $nonce = self::randomUrlSafe();

        $stmt = Db::get()->prepare(
            "INSERT INTO lti_states (state, nonce, lti_platform_id, expires_at)
             VALUES (?, ?, ?, datetime(CURRENT_TIMESTAMP, '+10 minutes'))"
        );
        $stmt->execute([$state, $nonce, $platform['id']]);

        $query = http_build_query([
            'response_type' => 'id_token',
            'response_mode' => 'form_post',
            'scope' => 'openid',
            'client_id' => $platform['client_id'],
            'redirect_uri' => $redirectUri,
            'login_hint' => $params['login_hint'],
            'lti_message_hint' => $params['lti_message_hint'] ?? '',
            'state' => $state,
            'nonce' => $nonce,
            'prompt' => 'none',
        ]);

        return $platform['auth_login_url'] . '?' . $query;
    }

    /**
     * Valida el id_token del launch (paso 2 del OIDC) y devuelve los claims.
     * Lanza RuntimeException con un mensaje entendible si algo no calza.
     *
     * Si el navegador reenvía el mismo POST (F5, doble clic en el enlace de
     * vuelta) el state ya fue marcado con un user_id/issued_code por un
     * launch anterior -- se devuelve ['replay' => true, ...] para que
     * launch.php reuse/renueve el código en vez de volver a validar el JWT
     * (que además fallaría: el nonce del id_token ya no calzaría tras un
     * segundo intento con otro id_token, si Moodle llega a reenviar uno).
     */
    public static function validateLaunch(string $idToken, string $state): array
    {
        $stateRow = self::findLaunchByState($state);
        if (!$stateRow) {
            throw new RuntimeException('state inválido o expirado');
        }
        if ($stateRow['user_id'] !== null) {
            return [
                'replay' => true,
                'user_id' => (int) $stateRow['user_id'],
                'issued_code' => $stateRow['issued_code'],
                'state' => $state,
            ];
        }

        $stmt = Db::get()->prepare('SELECT * FROM lti_platforms WHERE id = ?');
        $stmt->execute([$stateRow['lti_platform_id']]);
        $platform = $stmt->fetch();
        if (!$platform) {
            throw new RuntimeException('plataforma no encontrada');
        }

        $cfg = Db::config();
        $payload = Jwt::verify($idToken, $platform['jwks_url'], $cfg['lti_jwks_cache_seconds']);

        if ($payload['iss'] !== $platform['issuer']) {
            throw new RuntimeException("iss no coincide (recibido: {$payload['iss']})");
        }
        $aud = is_array($payload['aud']) ? ($payload['aud'][0] ?? null) : $payload['aud'];
        if ($aud !== $platform['client_id']) {
            throw new RuntimeException("aud no coincide (recibido: {$aud})");
        }
        if (($payload['nonce'] ?? null) !== $stateRow['nonce']) {
            throw new RuntimeException('nonce no coincide');
        }
        $deploymentClaim = 'https://purl.imsglobal.org/spec/lti/claim/deployment_id';
        $deploymentReceived = $payload[$deploymentClaim] ?? null;
        if ($deploymentReceived !== $platform['deployment_id']) {
            throw new RuntimeException("deployment_id no coincide (recibido: {$deploymentReceived}, configurado: {$platform['deployment_id']})");
        }
        $messageType = 'https://purl.imsglobal.org/spec/lti/claim/message_type';
        if (($payload[$messageType] ?? null) !== 'LtiResourceLinkRequest') {
            throw new RuntimeException('message_type no soportado');
        }

        return ['platform' => $platform, 'claims' => $payload, 'state' => $state];
    }

    /**
     * Valida un launch LTI 1.1 (POST directo, firmado OAuth1) y devuelve la
     * plataforma junto con los parámetros. Lanza RuntimeException con un
     * mensaje entendible si algo no calza.
     *
     * Mismo replay que validateLaunch() de arriba pero para 1.1: si el
     * navegador reenvía el mismo POST, el (consumer_key, nonce) ya está
     * marcado con un user_id/issued_code -- se devuelve ['replay' => true,
     * ...] en vez de fallar con "nonce reutilizado" al intentar insertarlo
     * de nuevo.
     */
    public static function validateLaunch11(array $params): array
    {
        $consumerKey = $params['oauth_consumer_key'] ?? '';
        if ($consumerKey === '') {
            throw new RuntimeException('oauth_consumer_key faltante');
        }
        $platform = self::findPlatformByConsumerKey($consumerKey);
        if (!$platform) {
            throw new RuntimeException("consumer_key no registrado: {$consumerKey}");
        }

        $nonce = $params['oauth_nonce'] ?? '';
        if ($nonce === '') {
            throw new RuntimeException('oauth_nonce faltante');
        }

        $existing = self::findLaunchByNonce($consumerKey, $nonce);
        if ($existing !== null && $existing['user_id'] !== null) {
            return [
                'replay' => true,
                'user_id' => (int) $existing['user_id'],
                'issued_code' => $existing['issued_code'],
                'consumer_key' => $consumerKey,
                'nonce' => $nonce,
            ];
        }

        if (($params['oauth_signature_method'] ?? '') !== 'HMAC-SHA1') {
            throw new RuntimeException('oauth_signature_method no soportado (solo HMAC-SHA1)');
        }
        $timestamp = (int) ($params['oauth_timestamp'] ?? 0);
        if (abs(time() - $timestamp) > 300) {
            throw new RuntimeException('oauth_timestamp fuera de rango');
        }
        if ($existing === null) {
            self::claimNonce($consumerKey, $nonce);
        }

        $url = self::currentUrl();
        if (!OAuth1::verifyRequest($params, 'POST', $url, $platform['shared_secret'])) {
            throw new RuntimeException('firma OAuth1 inválida');
        }

        if (($params['lti_message_type'] ?? '') !== 'basic-lti-launch-request') {
            throw new RuntimeException('lti_message_type no soportado');
        }

        return ['platform' => $platform, 'params' => $params, 'consumer_key' => $consumerKey, 'nonce' => $nonce];
    }

    /** Crea o actualiza el alumno a partir de los claims de un launch 1.3. */
    public static function upsertStudent(array $platform, array $claims): int
    {
        $sub = $claims['sub'];
        $name = $claims['name'] ?? ($claims['given_name'] ?? 'Alumno');
        $email = $claims['email'] ?? null;
        return self::upsertStudentBySub($platform, (string) $sub, (string) $name, $email);
    }

    /** Crea o actualiza el alumno a partir de los parámetros de un launch 1.1. */
    public static function upsertStudentFromLti11(array $platform, array $params): int
    {
        $sub = $params['user_id'] ?? '';
        if ($sub === '') {
            throw new RuntimeException('user_id faltante en el launch');
        }
        $name = $params['lis_person_name_full'] ?? ($params['lis_person_name_given'] ?? 'Alumno');
        $email = $params['lis_person_contact_email_primary'] ?? null;
        return self::upsertStudentBySub($platform, $sub, $name, $email);
    }

    private static function upsertStudentBySub(array $platform, string $sub, string $name, ?string $email): int
    {
        $pdo = Db::get();
        // Username es lo que la app muestra como "quién atendió" en la
        // agenda del admin -- si Moodle no comparte el email (privacidad
        // del tool, default en muchas instalaciones), preferir el nombre
        // real por sobre el fallback opaco "{platform_id}:{sub}". Se
        // mantiene único agregando el sub entre paréntesis.
        $username = $email ?: "{$name} ({$platform['id']}:{$sub})";

        $stmt = $pdo->prepare('SELECT id FROM users WHERE lti_platform_id = ? AND lti_sub = ?');
        $stmt->execute([$platform['id'], $sub]);
        $row = $stmt->fetch();
        if ($row) {
            $pdo->prepare('UPDATE users SET display_name = ?, username = ? WHERE id = ?')
                ->execute([$name, $username, $row['id']]);
            return (int) $row['id'];
        }

        $stmt = $pdo->prepare(
            "INSERT INTO users (role, username, display_name, lti_platform_id, lti_sub, permission, modules)
             VALUES ('student', ?, ?, ?, ?, 444, '[\"A\", \"Z\"]')"
        );
        $stmt->execute([$username, $name, $platform['id'], $sub]);
        return (int) $pdo->lastInsertId();
    }

    /** ID del curso LabSim vinculado a este contexto de Moodle (ver linkContextToCourse), o null si no está vinculado. */
    public static function findCourseForContext(int $platformId, ?string $contextId): ?int
    {
        if ($contextId === null || $contextId === '') {
            return null;
        }
        $stmt = Db::get()->prepare('SELECT course_id FROM course_lti_contexts WHERE lti_platform_id = ? AND context_id = ?');
        $stmt->execute([$platformId, $contextId]);
        $courseId = $stmt->fetchColumn();
        return $courseId !== false ? (int) $courseId : null;
    }

    /** Vincula (o revincula) un contexto de Moodle a un curso LabSim -- ver comentario de course_lti_contexts en schema.sql. */
    public static function linkContextToCourse(int $platformId, string $contextId, int $courseId): void
    {
        Db::get()->prepare(
            'INSERT INTO course_lti_contexts (lti_platform_id, context_id, course_id) VALUES (?, ?, ?)
             ON CONFLICT (lti_platform_id, context_id) DO UPDATE SET course_id = excluded.course_id'
        )->execute([$platformId, $contextId, $courseId]);
    }

    /**
     * Si $contextId está vinculado a un curso (ver linkContextToCourse) y
     * $userId es alumno, lo matricula ahí mismo -- así cientos de alumnos
     * que entran por el mismo curso de Moodle no requieren que el docente
     * los agregue uno por uno ni sepa sus nombres.
     */
    public static function autoEnrollIfMapped(int $platformId, ?string $contextId, int $userId): void
    {
        $courseId = self::findCourseForContext($platformId, $contextId);
        if ($courseId === null) {
            return;
        }
        $stmt = Db::get()->prepare("SELECT 1 FROM users WHERE id = ? AND role = 'student'");
        $stmt->execute([$userId]);
        if (!$stmt->fetchColumn()) {
            return;
        }
        Db::get()->prepare('INSERT OR IGNORE INTO course_students (course_id, user_id) VALUES (?, ?)')
            ->execute([$courseId, $userId]);
    }

    /**
     * Deja constancia de que $userId entró por LTI desde este contexto de
     * Moodle (con su nombre humano si Moodle lo informó) -- ver
     * user_lti_contexts en schema.sql. No-op si Moodle no manda context_id.
     */
    public static function recordContextSighting(int $userId, int $platformId, ?string $contextId, ?string $label): void
    {
        if ($contextId === null || $contextId === '') {
            return;
        }
        Db::get()->prepare(
            'INSERT INTO user_lti_contexts (user_id, lti_platform_id, context_id, context_label, last_seen_at)
             VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
             ON CONFLICT (user_id, lti_platform_id, context_id) DO UPDATE SET
                context_label = excluded.context_label, last_seen_at = excluded.last_seen_at'
        )->execute([$userId, $platformId, $contextId, $label ?? '']);
    }

    /** Fila de nonce (consumer_key, nonce) ya vista antes, o null si es la primera vez. */
    public static function findLaunchByNonce(string $consumerKey, string $nonce): ?array
    {
        $stmt = Db::get()->prepare('SELECT * FROM lti_oauth_nonces WHERE consumer_key = ? AND nonce = ?');
        $stmt->execute([$consumerKey, $nonce]);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    /** Fila de state (LTI 1.3) todavía vigente, o null si no existe/venció. */
    public static function findLaunchByState(string $state): ?array
    {
        $stmt = Db::get()->prepare('SELECT * FROM lti_states WHERE state = ? AND expires_at > CURRENT_TIMESTAMP');
        $stmt->execute([$state]);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    /** Marca el nonce de un launch 1.1 con el código emitido, para reconocer un replay después. */
    public static function markNonceCode(string $consumerKey, string $nonce, int $userId, string $code): void
    {
        Db::get()->prepare('UPDATE lti_oauth_nonces SET user_id = ?, issued_code = ? WHERE consumer_key = ? AND nonce = ?')
            ->execute([$userId, $code, $consumerKey, $nonce]);
    }

    /** Marca el state de un launch 1.3 con el código emitido, y estira su vencimiento otros 10 min (el alumno sigue con la pestaña abierta refrescando/renovando el código). */
    public static function markStateCode(string $state, int $userId, string $code): void
    {
        Db::get()->prepare(
            "UPDATE lti_states SET user_id = ?, issued_code = ?, expires_at = datetime(CURRENT_TIMESTAMP, '+10 minutes') WHERE state = ?"
        )->execute([$userId, $code, $state]);
    }

    /** Registra un nonce nuevo (primera vez que se ve). */
    private static function claimNonce(string $consumerKey, string $nonce): void
    {
        $pdo = Db::get();
        try {
            $pdo->prepare('INSERT INTO lti_oauth_nonces (consumer_key, nonce) VALUES (?, ?)')
                ->execute([$consumerKey, $nonce]);
        } catch (PDOException $e) {
            // Carrera: dos requests con el mismo nonce llegaron casi a la
            // vez y ambas pasaron findLaunchByNonce() antes de que la otra
            // insertara. Extremadamente raro (mismo timestamp+nonce del
            // mismo launch) -- se ignora, la request que ganó la carrera ya
            // deja marcado el código en markNonceCode().
            if ($e->getCode() === '23000') {
                return;
            }
            throw new RuntimeException('error guardando nonce: ' . $e->getMessage());
        }
        // housekeeping barato: 1 de cada 20 llamadas limpia nonces viejos.
        if (random_int(1, 20) === 1) {
            $pdo->exec("DELETE FROM lti_oauth_nonces WHERE created_at < datetime(CURRENT_TIMESTAMP, '-1 day')");
        }
    }

    /** URL exacta de este script (sin query string) -- la que Moodle firmó como "Tool URL". */
    private static function currentUrl(): string
    {
        $scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
        return "{$scheme}://{$_SERVER['HTTP_HOST']}{$_SERVER['SCRIPT_NAME']}";
    }

    private static function randomUrlSafe(): string
    {
        return rtrim(strtr(base64_encode(random_bytes(32)), '+/', '-_'), '=');
    }
}
