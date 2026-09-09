<?php

/**
 * Verificador JWT RS256 mínimo, sin dependencias de composer (hosting
 * compartido: no siempre hay acceso a instalar paquetes). Solo cubre lo
 * que necesita un LTI 1.3 launch: decodificar, traer la JWK de Moodle por
 * 'kid' y verificar la firma + claims básicos.
 */
final class Jwt
{
    public static function decodeUnverified(string $jwt): array
    {
        [$h, $p] = explode('.', $jwt) + [null, null];
        if ($h === null || $p === null) {
            throw new RuntimeException('JWT malformado');
        }
        return [
            'header' => json_decode(self::b64urlDecode($h), true),
            'payload' => json_decode(self::b64urlDecode($p), true),
        ];
    }

    /**
     * Verifica firma RS256 contra el JWKS de la plataforma y valida
     * exp/iat. No valida iss/aud/nonce: eso lo hace Lti::validateLaunch.
     */
    public static function verify(string $jwt, string $jwksUrl, int $jwksCacheSeconds): array
    {
        $parts = explode('.', $jwt);
        if (count($parts) !== 3) {
            throw new RuntimeException('JWT malformado');
        }
        [$h64, $p64, $sig64] = $parts;

        $header = json_decode(self::b64urlDecode($h64), true);
        $payload = json_decode(self::b64urlDecode($p64), true);
        if (($header['alg'] ?? '') !== 'RS256') {
            throw new RuntimeException('Algoritmo no soportado: solo RS256');
        }

        $jwk = self::findJwk($jwksUrl, $header['kid'] ?? '', $jwksCacheSeconds);
        $pem = self::jwkToPem($jwk['n'], $jwk['e']);

        $signature = self::b64urlDecode($sig64);
        $signedData = "{$h64}.{$p64}";
        $ok = openssl_verify($signedData, $signature, $pem, OPENSSL_ALGO_SHA256);
        if ($ok !== 1) {
            throw new RuntimeException('Firma JWT inválida');
        }

        $now = time();
        if (isset($payload['exp']) && $now >= $payload['exp']) {
            throw new RuntimeException('JWT expirado');
        }

        return $payload;
    }

    private static function findJwk(string $jwksUrl, string $kid, int $cacheSeconds): array
    {
        $cacheFile = sys_get_temp_dir() . '/labsim_jwks_' . md5($jwksUrl) . '.json';
        $jwks = null;
        if (is_file($cacheFile) && (time() - filemtime($cacheFile)) < $cacheSeconds) {
            $jwks = json_decode(file_get_contents($cacheFile), true);
        }
        if ($jwks === null) {
            $raw = file_get_contents($jwksUrl);
            if ($raw === false) {
                throw new RuntimeException('No se pudo obtener JWKS de la plataforma');
            }
            $jwks = json_decode($raw, true);
            file_put_contents($cacheFile, $raw);
        }

        foreach ($jwks['keys'] ?? [] as $key) {
            if (($key['kid'] ?? null) === $kid) {
                return $key;
            }
        }
        throw new RuntimeException("No se encontró la llave '{$kid}' en el JWKS");
    }

    /** Arma un PEM de llave pública RSA a partir del JWK (n, e en base64url). */
    private static function jwkToPem(string $n64, string $e64): string
    {
        $n = self::b64urlDecode($n64);
        $e = self::b64urlDecode($e64);

        $modulus = self::derInteger($n);
        $exponent = self::derInteger($e);
        $rsaPublicKey = self::derSequence($modulus . $exponent);

        // Wrap en SubjectPublicKeyInfo (rsaEncryption OID).
        $algId = self::derSequence(
            self::derObjectId('1.2.840.113549.1.1.1') . self::derNull()
        );
        $bitString = "\x00" . $rsaPublicKey;
        $spki = self::derSequence(
            $algId . self::derBitString($bitString)
        );

        $b64 = chunk_split(base64_encode($spki), 64, "\n");
        return "-----BEGIN PUBLIC KEY-----\n{$b64}-----END PUBLIC KEY-----\n";
    }

    private static function derLength(int $len): string
    {
        if ($len < 128) {
            return chr($len);
        }
        $bytes = ltrim(pack('N', $len), "\x00");
        return chr(0x80 | strlen($bytes)) . $bytes;
    }

    private static function derInteger(string $bin): string
    {
        if (ord($bin[0]) > 0x7f) {
            $bin = "\x00" . $bin;
        }
        return "\x02" . self::derLength(strlen($bin)) . $bin;
    }

    private static function derSequence(string $bin): string
    {
        return "\x30" . self::derLength(strlen($bin)) . $bin;
    }

    private static function derBitString(string $bin): string
    {
        return "\x03" . self::derLength(strlen($bin)) . $bin;
    }

    private static function derNull(): string
    {
        return "\x05\x00";
    }

    private static function derObjectId(string $oid): string
    {
        $parts = explode('.', $oid);
        $first = (int) array_shift($parts);
        $second = (int) array_shift($parts);
        $bytes = chr($first * 40 + $second);
        foreach ($parts as $part) {
            $part = (int) $part;
            $chunk = chr($part & 0x7f);
            $part >>= 7;
            while ($part > 0) {
                $chunk = chr(0x80 | ($part & 0x7f)) . $chunk;
                $part >>= 7;
            }
            $bytes .= $chunk;
        }
        return "\x06" . self::derLength(strlen($bytes)) . $bytes;
    }

    private static function b64urlDecode(string $s): string
    {
        $s = strtr($s, '-_', '+/');
        $pad = strlen($s) % 4;
        if ($pad) {
            $s .= str_repeat('=', 4 - $pad);
        }
        return base64_decode($s);
    }
}
