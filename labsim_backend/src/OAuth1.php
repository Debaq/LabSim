<?php

/**
 * Firma/verificación OAuth 1.0a de 2 patas (sin token, solo consumer key +
 * shared secret) -- lo mínimo que necesita validar un launch LTI 1.1.
 */
final class OAuth1
{
    public static function verifyRequest(array $params, string $method, string $url, string $consumerSecret): bool
    {
        $signature = $params['oauth_signature'] ?? '';
        if ($signature === '') {
            return false;
        }
        unset($params['oauth_signature']);
        $expected = self::sign($params, $method, $url, $consumerSecret);
        return hash_equals($expected, $signature);
    }

    public static function sign(array $params, string $method, string $url, string $consumerSecret, string $tokenSecret = ''): string
    {
        $pairs = [];
        foreach ($params as $key => $value) {
            $pairs[] = self::encode((string) $key) . '=' . self::encode((string) $value);
        }
        sort($pairs);
        $paramString = implode('&', $pairs);

        $baseString = strtoupper($method) . '&' . self::encode($url) . '&' . self::encode($paramString);
        $signingKey = self::encode($consumerSecret) . '&' . self::encode($tokenSecret);

        return base64_encode(hash_hmac('sha1', $baseString, $signingKey, true));
    }

    /** rawurlencode ya sigue RFC 3986 salvo '~', que OAuth exige sin codificar. */
    private static function encode(string $s): string
    {
        return str_replace('%7E', '~', rawurlencode($s));
    }
}
