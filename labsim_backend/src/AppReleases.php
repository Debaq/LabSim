<?php

declare(strict_types=1);

/**
 * Lista de versiones de la app de escritorio, servida por el backend.
 *
 * La app pregunta en cada arranque (y el kiosko cada media hora) si hay una
 * versión nueva. Contra la API de GitHub eso no escala: sin autenticar deja
 * 60 consultas por hora POR IP, y todo el laboratorio sale por la misma. El
 * kiosko no abre sin confirmar que está al día (core/actualizacion_kiosko.py
 * del cliente), así que agotar el límite era dejar el laboratorio parado.
 *
 * El backend consulta a GitHub una vez cada TTL segundos (una sola IP, ~6
 * por hora) y entrega la misma lista a todos. Solo la información: los
 * paquetes se siguen bajando de GitHub, que para las descargas no tiene ese
 * límite, y guardarlos acá sería llenar el hosting con 100+ MB por versión.
 *
 * Si GitHub no responde se sirve la última lista guardada mientras tenga
 * menos de MAX_VIEJA segundos; más vieja no se sirve (null), porque el
 * cliente la tomaría por buena y creería estar al día. Ahí el cliente cae a
 * consultar GitHub él mismo.
 */
final class AppReleases
{
    private const URL = 'https://api.github.com/repos/Debaq/LabSim/releases?per_page=100';
    private const PREFIJO = 'pyinstaller-v';
    public const TTL = 600;
    public const MAX_VIEJA = 3600;
    private const TIMEOUT = 6;

    /**
     * ['consultado' => epoch, 'releases' => [...]] o null si no hay una
     * lista confiable.
     *
     * @return array{consultado: int, releases: array<int, array<string, mixed>>}|null
     */
    public static function lista(?callable $fetch = null, ?string $cachePath = null, ?int $ahora = null): ?array
    {
        $fetch = $fetch ?? [self::class, 'fetch'];
        $cachePath = $cachePath ?? __DIR__ . '/../data/app_releases.json';
        $ahora = $ahora ?? time();

        $cache = self::leerCache($cachePath);
        if ($cache !== null && $ahora - $cache['consultado'] < self::TTL) {
            return $cache;
        }

        // Con el cache vencido llegan muchos pedidos juntos (el laboratorio
        // entero prende a la misma hora): uno consulta a GitHub y los demás
        // esperan el lock y leen lo que dejó.
        $lock = @fopen($cachePath . '.lock', 'c');
        if ($lock !== false) {
            flock($lock, LOCK_EX);
        }
        try {
            $cache = self::leerCache($cachePath);
            if ($cache !== null && $ahora - $cache['consultado'] < self::TTL) {
                return $cache;
            }
            $releases = $fetch();
            if ($releases !== null) {
                $cache = ['consultado' => $ahora, 'releases' => self::normalizar($releases)];
                self::guardarCache($cachePath, $cache);
                return $cache;
            }
        } finally {
            if ($lock !== false) {
                flock($lock, LOCK_UN);
                fclose($lock);
            }
        }

        if ($cache !== null && $ahora - $cache['consultado'] < self::MAX_VIEJA) {
            return $cache;
        }
        return null;
    }

    /**
     * Solo las versiones de esta app (el repo comparte releases con el
     * rewrite Tauri) y solo los campos que usa core/updater.py.
     *
     * @return array<int, array<string, mixed>>
     */
    public static function normalizar(array $releases): array
    {
        $salida = [];
        foreach ($releases as $r) {
            if (!is_array($r)) {
                continue;
            }
            $tag = (string) ($r['tag_name'] ?? '');
            if (strpos($tag, self::PREFIJO) !== 0) {
                continue;
            }
            $assets = [];
            foreach ((array) ($r['assets'] ?? []) as $a) {
                if (is_array($a) && isset($a['name'], $a['browser_download_url'])) {
                    $assets[] = [
                        'name' => (string) $a['name'],
                        'browser_download_url' => (string) $a['browser_download_url'],
                    ];
                }
            }
            $salida[] = [
                'tag_name' => $tag,
                'created_at' => (string) ($r['created_at'] ?? ''),
                'body' => (string) ($r['body'] ?? ''),
                'assets' => $assets,
            ];
        }
        return $salida;
    }

    /**
     * Un intento contra la API. null ante cualquier falla (sin red, límite
     * agotado, respuesta rara) -- nunca lanza.
     *
     * @return array<int, mixed>|null
     */
    public static function fetch(): ?array
    {
        if (!function_exists('curl_init')) {
            return null;
        }
        $ch = curl_init(self::URL);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => self::TIMEOUT,
            CURLOPT_CONNECTTIMEOUT => self::TIMEOUT,
            // GitHub rechaza pedidos sin User-Agent
            CURLOPT_USERAGENT => 'LabSim-backend',
            CURLOPT_HTTPHEADER => ['Accept: application/vnd.github+json'],
        ]);
        $body = curl_exec($ch);
        $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($body === false || $status < 200 || $status >= 300) {
            return null;
        }
        $data = json_decode((string) $body, true);
        // con el límite agotado GitHub contesta un objeto con "message"
        return (is_array($data) && array_values($data) === $data) ? $data : null;
    }

    private static function leerCache(string $path): ?array
    {
        if (!is_file($path)) {
            return null;
        }
        $data = json_decode((string) @file_get_contents($path), true);
        if (!is_array($data) || !isset($data['consultado'], $data['releases'])
            || !is_int($data['consultado']) || !is_array($data['releases'])) {
            return null;
        }
        return $data;
    }

    private static function guardarCache(string $path, array $cache): void
    {
        $dir = dirname($path);
        if (!is_dir($dir) && !@mkdir($dir, 0775, true) && !is_dir($dir)) {
            return;
        }
        // tmp + rename: un json a medio escribir sería justo el que se lee
        // en el próximo pedido.
        $tmp = $path . '.tmp';
        $json = json_encode($cache, JSON_UNESCAPED_UNICODE);
        if ($json === false || @file_put_contents($tmp, $json) === false) {
            return;
        }
        @rename($tmp, $path);
    }
}
