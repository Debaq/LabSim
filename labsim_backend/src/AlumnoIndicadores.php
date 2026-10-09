<?php

declare(strict_types=1);

/**
 * Indicadores de la ficha del alumno (admin/student.php) armados a partir de
 * lo que ya se mide: la técnica de la audiometría por atención
 * (AudiometriaTecnica::evaluar), las duraciones y los informes. Sin base:
 * recibe los resultados ya calculados, así se puede testear.
 */
final class AlumnoIndicadores
{
    private const SECCIONES = ['orden' => 'Orden', 'aereos' => 'Aéreos', 'oseos' => 'Óseos'];

    /**
     * Pasos de la técnica que el alumno no cumplió, sumados entre atenciones:
     * "Se parte por el oído mejor" falló en 3 de 4. Una regla cuenta una vez
     * por atención aunque se repita por oído (falló si falló en alguno).
     *
     * @param array<int,array> $tecnicas resultados de AudiometriaTecnica::evaluar
     * @return array<int,array{seccion:string, texto:string, fallos:int, evaluadas:int}>
     *         los que fallaron al menos una vez, el que más falla primero
     */
    public static function pasosDificiles(array $tecnicas): array
    {
        $fallados = array_values(array_filter(self::conteoPasos($tecnicas), static function (array $c): bool {
            return $c['fallos'] > 0;
        }));
        usort($fallados, static function (array $a, array $b): int {
            return [$b['fallos'] / $b['evaluadas'], $b['fallos']] <=> [$a['fallos'] / $a['evaluadas'], $a['fallos']];
        });
        return $fallados;
    }

    /**
     * Cada paso evaluado, cumplido o no, con sus fallos y evaluaciones,
     * indexado por "Sección|texto". Lo usan pasosDificiles() y el avance del
     * curso (que cuenta alumnos en vez de atenciones).
     *
     * @return array<string,array{seccion:string, texto:string, fallos:int, evaluadas:int}>
     */
    public static function conteoPasos(array $tecnicas): array
    {
        $cuenta = [];
        foreach ($tecnicas as $t) {
            foreach (self::SECCIONES as $clave => $seccion) {
                $listas = [$t[$clave]['reglas'] ?? []];
                foreach ($t[$clave]['oidos'] ?? [] as $reglas) {
                    $listas[] = $reglas;
                }
                $enEsta = [];
                foreach ($listas as $reglas) {
                    foreach ($reglas as $r) {
                        if (($r['cumple'] ?? null) === null) {
                            continue;
                        }
                        $k = $seccion . '|' . $r['texto'];
                        $enEsta[$k] = ($enEsta[$k] ?? true) && $r['cumple'];
                    }
                }
                foreach ($enEsta as $k => $cumplio) {
                    if (!isset($cuenta[$k])) {
                        [$s, $texto] = explode('|', $k, 2);
                        $cuenta[$k] = ['seccion' => $s, 'texto' => $texto, 'fallos' => 0, 'evaluadas' => 0];
                    }
                    $cuenta[$k]['evaluadas']++;
                    $cuenta[$k]['fallos'] += $cumplio ? 0 : 1;
                }
            }
        }
        return $cuenta;
    }

    /**
     * Cuánto cambió un porcentaje entre la primera y la segunda mitad de la
     * serie (en orden cronológico). null con menos de 2 puntos. Con un número
     * impar, el del medio no entra en ninguna mitad.
     *
     * @param array<int,int> $serie
     */
    public static function tendencia(array $serie): ?int
    {
        $serie = array_values($serie);
        $n = count($serie);
        if ($n < 2) {
            return null;
        }
        $mitad = intdiv($n, 2);
        $antes = array_slice($serie, 0, $mitad);
        $despues = array_slice($serie, $n - $mitad);
        return (int) round(array_sum($despues) / $mitad - array_sum($antes) / $mitad);
    }

    /** @param array<int,int|float> $valores */
    public static function promedio(array $valores): ?int
    {
        return $valores ? (int) round(array_sum($valores) / count($valores)) : null;
    }

    /** @param array<int,int|float> $valores */
    public static function mediana(array $valores): ?int
    {
        if (!$valores) {
            return null;
        }
        sort($valores);
        $n = count($valores);
        $m = intdiv($n, 2);
        return (int) round($n % 2 ? $valores[$m] : ($valores[$m - 1] + $valores[$m]) / 2);
    }

    /** Equipo de cada prefijo de action_logs (lo único que la app registra acción por acción). */
    public const EQUIPOS = ['audio_' => 'Audiómetro', 'z_' => 'Impedanciómetro'];

    /**
     * Cuánto usó cada equipo en una atención, en palabras: suma los
     * intervalos entre acciones seguidas del mismo equipo, sin contar los de
     * más de $pausaMax segundos (se fue a otra cosa: conversar, el otro
     * equipo, un informe). Sin acciones, el equipo no aparece.
     *
     * @param array<int,array{action:string, client_ts:string}> $logs en orden
     * @return array<string,array{segundos:int, acciones:int}> por nombre de equipo, en orden de uso
     */
    public static function usoEquipos(array $logs, int $pausaMax = 60): array
    {
        $out = [];
        $anterior = [];
        foreach ($logs as $l) {
            $equipo = null;
            foreach (self::EQUIPOS as $prefijo => $nombre) {
                if (strpos((string) $l['action'], $prefijo) === 0) {
                    $equipo = $nombre;
                    break;
                }
            }
            if ($equipo === null) {
                continue;
            }
            $t = strtotime((string) $l['client_ts']);
            if (!isset($out[$equipo])) {
                $out[$equipo] = ['segundos' => 0, 'acciones' => 0];
            }
            $out[$equipo]['acciones']++;
            if (isset($anterior[$equipo]) && $t !== false) {
                $dt = $t - $anterior[$equipo];
                if ($dt > 0 && $dt <= $pausaMax) {
                    $out[$equipo]['segundos'] += $dt;
                }
            }
            if ($t !== false) {
                $anterior[$equipo] = $t;
            }
        }
        return $out;
    }

    /** "hace 5 min", "hace 3 h", "hace 2 días": para "última atención". */
    public static function hace(int $segundos): string
    {
        if ($segundos < 60) {
            return 'recién';
        }
        if ($segundos < 3600) {
            return 'hace ' . intdiv($segundos, 60) . ' min';
        }
        if ($segundos < 86400) {
            return 'hace ' . intdiv($segundos, 3600) . ' h';
        }
        $dias = intdiv($segundos, 86400);
        return $dias === 1 ? 'ayer' : "hace {$dias} días";
    }

    /** "12 min", "1 h 05 min": para una duración típica no hacen falta segundos. */
    public static function minutos(?int $segundos): string
    {
        if ($segundos === null) {
            return '—';
        }
        $min = (int) round($segundos / 60);
        return $min < 60 ? "{$min} min" : sprintf('%d h %02d min', intdiv($min, 60), $min % 60);
    }
}
