<?php

declare(strict_types=1);

/**
 * Feriados legales de Chile para marcarlos en el calendario de agenda.php --
 * agendar una cita en feriado es un error del docente que hoy no avisa nada.
 *
 * Fuente: https://feriados-cl.netlify.app/api/holidays/<año> (responde 400
 * para años pasados). Mismas tres capas que el cliente de escritorio
 * (src/core/feriados.py), y ninguna puede voltear la página:
 *
 *   1. data/feriados_<año>.json -- si existe se usa y NO se pide nada por red
 *      (la lista de un año ya bajado no cambia).
 *   2. la API, con timeout corto.
 *   3. resources/feriados_backup.json -- copia versionada en el repo, para un
 *      hosting sin salida a internet.
 *
 * Formato normalizado: ['MM-DD' => 'descripción'] por año.
 */
class Feriados
{
    private const URL = 'https://feriados-cl.netlify.app/api/holidays/%d';
    private const TIMEOUT = 4;

    /** @var array<int, array<string, string>> memo por request */
    private static array $memo = [];

    /**
     * Feriados del año. [] si no se pudo conseguir por ningún lado -- el
     * calendario se dibuja igual, solo que sin marcas.
     *
     * @return array<string, string>
     */
    public static function delAnio(int $year): array
    {
        if (isset(self::$memo[$year])) {
            return self::$memo[$year];
        }

        $mapa = self::leerJson(self::cachePath($year));
        if ($mapa === null) {
            $mapa = self::fetch($year);
            if ($mapa !== []) {
                self::guardarCache($year, $mapa);
            }
        }
        if ($mapa === null || $mapa === []) {
            $mapa = self::backup($year);
        }

        self::$memo[$year] = $mapa;
        return $mapa;
    }

    /**
     * Feriados de varios años en un solo arreglo ['YYYY-MM-DD' => descripción],
     * que es la forma en que los usa el calendario (y el JS del modal).
     *
     * @param int[] $years
     * @return array<string, string>
     */
    public static function porFecha(array $years): array
    {
        $porFecha = [];
        foreach (array_unique($years) as $year) {
            foreach (self::delAnio((int) $year) as $mmdd => $descripcion) {
                $porFecha[sprintf('%04d-%s', $year, $mmdd)] = $descripcion;
            }
        }
        return $porFecha;
    }

    private static function cachePath(int $year): string
    {
        return __DIR__ . '/../data/feriados_' . $year . '.json';
    }

    /** @return array<string, string>|null */
    private static function leerJson(string $path): ?array
    {
        if (!is_file($path)) {
            return null;
        }
        $raw = @file_get_contents($path);
        if ($raw === false) {
            return null;
        }
        $data = json_decode($raw, true);
        return self::esMapa($data) ? $data : null;
    }

    private static function esMapa($data): bool
    {
        if (!is_array($data)) {
            return false;
        }
        foreach ($data as $k => $v) {
            if (!is_string($k) || !is_string($v)) {
                return false;
            }
        }
        return true;
    }

    /**
     * Un intento contra la API. [] ante cualquier falla (sin red, 400 de un
     * año pasado, JSON raro) -- nunca lanza.
     *
     * @return array<string, string>
     */
    private static function fetch(int $year): array
    {
        if (!function_exists('curl_init')) {
            return [];
        }
        $ch = curl_init(sprintf(self::URL, $year));
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_TIMEOUT => self::TIMEOUT,
            CURLOPT_CONNECTTIMEOUT => self::TIMEOUT,
        ]);
        $body = curl_exec($ch);
        $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($body === false || $status < 200 || $status >= 300) {
            return [];
        }
        return self::parse(json_decode((string) $body, true));
    }

    /**
     * {"feriados": {"enero": [{"mes": 1, "dia": 1, "descripcion": ...}]}}
     * -> ['01-01' => 'Año Nuevo'].
     *
     * @return array<string, string>
     */
    public static function parse($data): array
    {
        $feriados = is_array($data) ? ($data['feriados'] ?? null) : null;
        if (!is_array($feriados)) {
            return [];
        }

        $mapa = [];
        foreach ($feriados as $dias) {
            if (!is_array($dias)) {
                continue;
            }
            foreach ($dias as $dia) {
                if (!is_array($dia) || !isset($dia['mes'], $dia['dia'])) {
                    continue;
                }
                $mes = (int) $dia['mes'];
                $num = (int) $dia['dia'];
                if ($mes < 1 || $mes > 12 || $num < 1 || $num > 31) {
                    continue;
                }
                $descripcion = isset($dia['descripcion']) ? trim((string) $dia['descripcion']) : '';
                $mapa[sprintf('%02d-%02d', $mes, $num)] = $descripcion !== '' ? $descripcion : 'Feriado';
            }
        }
        return $mapa;
    }

    /** @param array<string, string> $mapa */
    private static function guardarCache(int $year, array $mapa): void
    {
        $path = self::cachePath($year);
        $dir = dirname($path);
        if (!is_dir($dir) && !@mkdir($dir, 0775, true) && !is_dir($dir)) {
            return;
        }
        // tmp + rename: un json a medio escribir sería justo el que se lee en
        // el próximo request.
        $tmp = $path . '.tmp';
        $json = json_encode($mapa, JSON_UNESCAPED_UNICODE | JSON_PRETTY_PRINT);
        if ($json === false || @file_put_contents($tmp, $json) === false) {
            return;
        }
        @rename($tmp, $path);
    }

    /** @return array<string, string> */
    private static function backup(int $year): array
    {
        $data = json_decode((string) @file_get_contents(__DIR__ . '/../resources/feriados_backup.json'), true);
        if (!is_array($data) || !isset($data[(string) $year])) {
            return [];
        }
        $mapa = $data[(string) $year];
        return self::esMapa($mapa) ? $mapa : [];
    }
}
