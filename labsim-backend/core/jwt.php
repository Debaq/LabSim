<?php
/**
 * LabSim Backend - JWT puro (sin librería externa)
 * Implementa HS256 (HMAC-SHA256)
 */

require_once __DIR__ . '/config.php';

class JWT {
    /**
     * Genera un JWT
     */
    public static function encode(array $payload, string $secret = JWT_SECRET): string {
        $header = self::base64url_encode(json_encode([
            'typ' => 'JWT',
            'alg' => JWT_ALGORITHM,
        ]));

        $payload = self::base64url_encode(json_encode($payload));
        $signature = self::base64url_encode(
            hash_hmac('sha256', "$header.$payload", $secret, true)
        );

        return "$header.$payload.$signature";
    }

    /**
     * Decodifica y verifica un JWT
     * @return array payload decodificado
     * @throws Exception si el token es inválido o expirado
     */
    public static function decode(string $token, string $secret = JWT_SECRET): array {
        $parts = explode('.', $token);
        if (count($parts) !== 3) {
            throw new Exception('Token malformado');
        }

        [$headerB64, $payloadB64, $signatureB64] = $parts;

        // Verificar firma
        $expectedSignature = self::base64url_encode(
            hash_hmac('sha256', "$headerB64.$payloadB64", $secret, true)
        );

        if (!hash_equals($expectedSignature, $signatureB64)) {
            throw new Exception('Firma inválida');
        }

        // Decodificar header
        $header = json_decode(self::base64url_decode($headerB64), true);
        if (!$header || ($header['alg'] ?? '') !== JWT_ALGORITHM) {
            throw new Exception('Algoritmo no soportado');
        }

        // Decodificar payload
        $payload = json_decode(self::base64url_decode($payloadB64), true);
        if (!$payload) {
            throw new Exception('Payload inválido');
        }

        // Verificar expiración
        if (isset($payload['exp']) && $payload['exp'] < time()) {
            throw new Exception('Token expirado');
        }

        // Verificar nbf (not before)
        if (isset($payload['nbf']) && $payload['nbf'] > time()) {
            throw new Exception('Token aún no válido');
        }

        return $payload;
    }

    /**
     * Genera un access token
     */
    public static function createAccessToken(string $userId, string $username, string $role, bool $isDemo = false): string {
        $payload = [
            'sub' => $userId,
            'username' => $username,
            'role' => $role,
            'type' => 'access',
            'iat' => time(),
            'exp' => time() + JWT_ACCESS_TTL,
            'iss' => JWT_ISSUER,
        ];
        if ($isDemo) {
            $payload['demo'] = true;
        }
        return self::encode($payload);
    }

    /**
     * Genera un refresh token
     */
    public static function createRefreshToken(string $userId): string {
        return self::encode([
            'sub' => $userId,
            'type' => 'refresh',
            'iat' => time(),
            'exp' => time() + JWT_REFRESH_TTL,
            'iss' => JWT_ISSUER,
        ]);
    }

    private static function base64url_encode(string $data): string {
        return rtrim(strtr(base64_encode($data), '+/', '-_'), '=');
    }

    private static function base64url_decode(string $data): string {
        return base64_decode(strtr($data, '-_', '+/') . str_repeat('=', 3 - (3 + strlen($data)) % 4));
    }
}
