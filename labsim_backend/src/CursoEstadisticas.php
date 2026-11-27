<?php

declare(strict_types=1);

require_once __DIR__ . '/AudiometriaTecnica.php';
require_once __DIR__ . '/AlumnoIndicadores.php';

/**
 * Estadísticas de la audiometría de un curso, a partir de las técnicas ya
 * evaluadas (AudiometriaTecnica::evaluar, con su 'resumen' de conductas):
 * cifras del curso, por mes, por paciente, por alumno, a quién mirar y
 * recomendaciones para los docentes. Sin base: recibe lo que arma
 * CourseAvance::porAlumno, así lo usan el panel (pestaña Avance) y el
 * informe PDF del curso con el mismo cálculo.
 *
 * Entrada: [uid => ['nombre' => string, 'tecnicas' => [resultado con
 * '_cita' => ['fecha' => 'Y-m-d', 'paciente' => string, 'case_id' => string]],
 * ...]], las técnicas de cada alumno en orden cronológico.
 */
final class CursoEstadisticas
{
    private const SECCIONES = AudiometriaTecnica::SECCIONES;

    /** Cortes de las recomendaciones (% del curso bajo el cual se recomienda). */
    public const CORTES = [
        'verificacion' => 70,
        'oseos' => 80,
        'adaptacion' => 50,
        'enmascaramiento' => 70,
        'orden' => 60,
        'tinnitus' => 60,
        'duracion_s' => 1.0,
    ];

    public static function calcular(array $alumnos): array
    {
        $todas = [];
        foreach ($alumnos as $uid => $al) {
            foreach ($al['tecnicas'] ?? [] as $t) {
                if (($t['puntaje']['pct'] ?? null) !== null) {
                    $todas[] = ['uid' => $uid, 't' => $t];
                }
            }
        }
        usort($todas, static function ($a, $b) {
            return ($a['t']['_cita']['fecha'] ?? '') <=> ($b['t']['_cita']['fecha'] ?? '');
        });
        $porAlumno = self::porAlumno($alumnos);
        $out = [
            'n' => count($todas),
            'kpis' => self::kpis(array_column($todas, 't')),
            'meses' => self::agrupar($todas, static function ($t) { return substr((string) ($t['_cita']['fecha'] ?? ''), 0, 7); }),
            'pacientes' => self::agrupar($todas, static function ($t) {
                return (string) ($t['_cita']['case_id'] ?? '') . '|' . (string) ($t['_cita']['paciente'] ?? '');
            }),
            'alumnos' => $porAlumno,
            'observaciones' => self::observacionesFrecuentes(array_column($todas, 't')),
        ];
        $out['mirar'] = self::paraMirar($porAlumno);
        $out['recomendaciones'] = self::recomendaciones($out);
        return $out;
    }

    /** Cifras del curso desde los resúmenes de cada atención. */
    public static function kpis(array $tecnicas): array
    {
        $s = self::sumarResumenes($tecnicas);
        return [
            'logro' => AlumnoIndicadores::promedio(array_map(static function ($t) { return $t['puntaje']['pct']; }, $tecnicas)),
            'a_5db' => self::pct($s['a_5db'], $s['medibles']),
            'verificacion' => self::pct($s['verificadas'], $s['frecuencias']),
            'duracion_mediana' => $s['duraciones'] ? self::mediana($s['duraciones']) : null,
            'bajo_1s' => self::pct($s['bajo_1s'], $s['estimulos']),
            'oseos' => [$s['oseos_hechos'], $s['oseos_pedidos']],
            'logo' => $s['logo'],
            'adaptacion' => $s['adaptacion'],
            'enmascaramiento' => $s['enmascaramiento'] ? (int) round(100 * array_sum($s['enmascaramiento']) / count($s['enmascaramiento'])) : null,
            'enmascaramiento_n' => count($s['enmascaramiento']),
            'supra' => $s['supra'],
            'secciones' => self::secciones($tecnicas),
        ];
    }

    /** Promedio de cada sección (% ponderado) sobre las atenciones donde se evaluó. */
    public static function secciones(array $tecnicas): array
    {
        $out = [];
        foreach (self::SECCIONES as $k) {
            $v = [];
            foreach ($tecnicas as $t) {
                if (($t[$k]['puntaje']['pct'] ?? null) !== null) {
                    $v[] = $t[$k]['puntaje']['pct'];
                }
            }
            $out[$k] = AlumnoIndicadores::promedio($v);
        }
        return $out;
    }

    private static function sumarResumenes(array $tecnicas): array
    {
        $s = ['frecuencias' => 0, 'verificadas' => 0, 'medibles' => 0, 'a_5db' => 0, 'estimulos' => 0, 'bajo_1s' => 0,
            'duraciones' => [], 'oseos_pedidos' => 0, 'oseos_hechos' => 0, 'logo' => [0, 0], 'adaptacion' => [0, 0],
            'enmascaramiento' => [], 'supra' => []];
        foreach ($tecnicas as $t) {
            $r = $t['resumen'] ?? null;
            if ($r === null) {
                continue;
            }
            foreach (['frecuencias', 'verificadas', 'medibles', 'a_5db', 'estimulos', 'bajo_1s'] as $k) {
                $s[$k] += (int) $r[$k];
            }
            if ($r['duracion_mediana'] !== null) {
                $s['duraciones'][] = (float) $r['duracion_mediana'];
            }
            if ($r['oseos_pedidos']) {
                $s['oseos_pedidos']++;
                $s['oseos_hechos'] += $r['oseos_hechos'] ? 1 : 0;
            }
            foreach (['logo', 'adaptacion'] as $k) {
                if ($r[$k] !== null) {
                    $s[$k][1]++;
                    $s[$k][0] += $r[$k] ? 1 : 0;
                }
            }
            foreach (['enmascaramiento_aerea', 'enmascaramiento_osea'] as $k) {
                if ($r[$k] !== null) {
                    $s['enmascaramiento'][] = (float) $r[$k];
                }
            }
            foreach ($r['supra'] as $p) {
                $s['supra'][$p] = ($s['supra'][$p] ?? 0) + 1;
            }
        }
        arsort($s['supra']);
        return $s;
    }

    /** Atenciones agrupadas por una clave (mes, paciente): n, logro y secciones. */
    private static function agrupar(array $todas, callable $clave): array
    {
        $grupos = [];
        foreach ($todas as $x) {
            $grupos[$clave($x['t'])][] = $x['t'];
        }
        $out = [];
        foreach ($grupos as $k => $ts) {
            $out[$k] = [
                'n' => count($ts),
                'fecha' => $ts[0]['_cita']['fecha'] ?? null,
                'paciente' => $ts[0]['_cita']['paciente'] ?? null,
                'logro' => AlumnoIndicadores::promedio(array_map(static function ($t) { return $t['puntaje']['pct']; }, $ts)),
                'secciones' => self::secciones($ts),
            ];
        }
        return $out;
    }

    /** Conductas de cada alumno, del logro más alto al más bajo. */
    public static function porAlumno(array $alumnos): array
    {
        $out = [];
        foreach ($alumnos as $uid => $al) {
            $ts = array_values(array_filter($al['tecnicas'] ?? [], static function ($t) {
                return ($t['puntaje']['pct'] ?? null) !== null;
            }));
            if (!$ts) {
                continue;
            }
            $serie = array_map(static function ($t) { return (int) $t['puntaje']['pct']; }, $ts);
            $k = self::kpis($ts);
            $out[$uid] = [
                'nombre' => (string) ($al['nombre'] ?? $uid),
                'n' => count($ts),
                'logro' => AlumnoIndicadores::promedio($serie),
                'tendencia' => AlumnoIndicadores::tendencia($serie),
                'serie' => $serie,
            ] + $k;
        }
        uasort($out, static function ($a, $b) { return $b['logro'] <=> $a['logro']; });
        return $out;
    }

    /** "Volvió a umbrales aéreos después de…": las advertencias de orden más repetidas. */
    private static function observacionesFrecuentes(array $tecnicas): array
    {
        $c = [];
        foreach ($tecnicas as $t) {
            foreach ($t['orden']['observaciones'] ?? [] as $o) {
                $c[$o] = ($c[$o] ?? 0) + 1;
            }
        }
        arsort($c);
        return array_slice($c, 0, 3, true);
    }

    /**
     * A quién mirar primero, con todos sus motivos en un renglón: los dos
     * logros más bajos si quedan 10 puntos bajo el curso, los que bajan 10 puntos o más, los que no toman
     * óseos y los que nunca enmascaran donde correspondía.
     *
     * @return array<int|string,array{nombre:string, motivos:array<int,string>}>
     */
    public static function paraMirar(array $porAlumno): array
    {
        $out = [];
        $add = static function ($uid, $al, string $m) use (&$out) {
            $out[$uid]['nombre'] = $al['nombre'];
            $out[$uid]['motivos'][] = $m;
        };
        // Los dos más bajos, solo si quedan 10 puntos o más bajo el promedio
        // del curso: si todos van bien, el último no está mal por serlo.
        $orden = $porAlumno;
        uasort($orden, static function ($a, $b) { return $a['logro'] <=> $b['logro']; });
        $media = AlumnoIndicadores::promedio(array_column($porAlumno, 'logro'));
        foreach (array_slice($orden, 0, 2, true) as $uid => $al) {
            if ($media !== null && $al['logro'] <= $media - 10) {
                $add($uid, $al, "logro bajo el del curso ({$al['logro']} % contra {$media} %)");
            }
        }
        foreach ($porAlumno as $uid => $al) {
            if ($al['tendencia'] !== null && $al['tendencia'] <= -10) {
                $add($uid, $al, sprintf('viene bajando (%+d puntos; últimas: %s)', $al['tendencia'], implode(', ', array_slice($al['serie'], -3))));
            }
            [$h, $p] = $al['oseos'];
            if ($p >= 3 && $h / $p < 0.5) {
                $add($uid, $al, "tomó óseos en {$h} de {$p} atenciones que los pedían");
            }
            if ($al['enmascaramiento_n'] >= 3 && $al['enmascaramiento'] === 0) {
                $add($uid, $al, 'no enmascaró nunca donde el tono cruzaba');
            }
        }
        return $out;
    }

    /**
     * Recomendaciones para los docentes: solo las que los datos piden (bajo
     * los CORTES), cada una con la cifra que la respalda, qué hacer y a
     * quiénes mirar en particular.
     *
     * @return array<int,array{titulo:string, evidencia:string, accion:string, alumnos:array<int,string>}>
     */
    public static function recomendaciones(array $e): array
    {
        $k = $e['kpis'];
        $al = $e['alumnos'];
        $quienes = static function (callable $f) use ($al): array {
            $n = [];
            foreach ($al as $a) {
                if ($f($a)) {
                    $n[] = $a['nombre'];
                }
            }
            return $n;
        };
        $out = [];

        if ($k['verificacion'] !== null && $k['verificacion'] < self::CORTES['verificacion']) {
            $out[] = [
                'titulo' => 'Verificar el umbral con 2 de 3',
                'evidencia' => sprintf('Solo el %d %% de las frecuencias se cierra con 2 de 3 respuestas subiendo, aunque el %d %% de los umbrales queda a ±5 dB del real: llegan al nivel, pero no lo confirman.',
                    $k['verificacion'], $k['a_5db']),
                'accion' => 'En el práctico, pedir que confirmen cada umbral con 2 de 3 subiendo antes de cambiar de frecuencia. Es el paso que más pesa en el indicador (×3).',
                'alumnos' => $quienes(static function ($a) { return $a['verificacion'] !== null && $a['verificacion'] < 30; }),
                'alumnos_motivo' => 'verifican menos del 30 %',
            ];
        }
        [$oh, $op] = $k['oseos'];
        if ($op > 0 && 100 * $oh / $op < self::CORTES['oseos']) {
            $out[] = [
                'titulo' => 'Tomar los umbrales óseos',
                'evidencia' => sprintf('Faltaron en %d de las %d atenciones con la vía aérea alterada.', $op - $oh, $op),
                'accion' => 'Recordar que los óseos se toman en todo oído con la vía aérea alterada y revisarlos antes de dar por cerrada la audiometría.',
                'alumnos' => $quienes(static function ($a) { return $a['oseos'][1] >= 3 && $a['oseos'][0] / $a['oseos'][1] < 0.5; }),
                'alumnos_motivo' => 'los tomaron en menos de la mitad',
            ];
        }
        if ($k['enmascaramiento'] !== null && $k['enmascaramiento'] < self::CORTES['enmascaramiento']) {
            $peor = self::peorPaciente($e['pacientes'], 'enmascaramiento');
            $out[] = [
                'titulo' => 'Enmascarar donde el tono cruza',
                'evidencia' => sprintf('Pusieron ruido en el %d %% de los umbrales que lo pedían.', $k['enmascaramiento'])
                    . ($peor ? sprintf(' El paciente más bajo fue %s (%s, %d %%).', $peor['paciente'], self::fechaCorta($peor['fecha']), $peor['secciones']['enmascaramiento']) : ''),
                'accion' => 'Repasar la regla de cruce (estímulo menos atenuación interaural contra la ósea del otro oído) y la meseta, idealmente sobre ese caso.',
                'alumnos' => $quienes(static function ($a) { return $a['enmascaramiento_n'] >= 3 && $a['enmascaramiento'] !== null && $a['enmascaramiento'] < 30; }),
                'alumnos_motivo' => 'enmascaran menos del 30 %',
            ];
        }
        [$as, $an] = $k['adaptacion'];
        if ($an >= 3 && 100 * $as / $an < self::CORTES['adaptacion']) {
            $top = array_slice($k['supra'], 0, 2, true);
            $out[] = [
                'titulo' => 'Buscar adaptación en la sensorioneural asimétrica',
                'evidencia' => sprintf('Hicieron Carhart, Rosemberg o STAT en %d de %d atenciones con asimetría.', $as, $an)
                    . ($top ? ' Las supraliminares que más usan son ' . implode(' y ', array_map(static function ($p, $n) { return "{$p} ({$n})"; }, array_keys($top), $top)) . '.' : ''),
                'accion' => 'En los casos asimétricos, pedir una prueba de adaptación antes de concluir coclear o retrococlear.',
                'alumnos' => $quienes(static function ($a) { return $a['adaptacion'][1] >= 3 && $a['adaptacion'][0] === 0; }),
                'alumnos_motivo' => 'no la hicieron nunca',
            ];
        }
        if ($k['duracion_mediana'] !== null && $k['duracion_mediana'] < self::CORTES['duracion_s']) {
            $out[] = [
                'titulo' => 'Sostener el estímulo 1 a 2 segundos',
                'evidencia' => sprintf('La duración mediana es %s s y el %d %% de los estímulos dura menos de 1 s.',
                    number_format($k['duracion_mediana'], 2, ',', ''), $k['bajo_1s']),
                'accion' => 'Mostrar en cabina cuánto dura un estímulo de 1 a 2 s. El paciente simulado levanta la mano al instante, así que nada los obliga a sostener el tono.',
                'alumnos' => $quienes(static function ($a) { return $a['duracion_mediana'] !== null && $a['duracion_mediana'] < 0.3; }),
                'alumnos_motivo' => 'mediana bajo 0,3 s',
            ];
        }
        $orden = $k['secciones']['orden'] ?? null;
        if ($orden !== null && $orden < self::CORTES['orden']) {
            $obs = array_keys($e['observaciones']);
            $out[] = [
                'titulo' => 'Orden de las pruebas',
                'evidencia' => sprintf('El orden se cumple en un %d %%.', $orden) . ($obs ? ' Lo más repetido: ' . lcfirst(rtrim($obs[0], '.')) . '.' : ''),
                'accion' => 'Recordar el orden aéreos → logoaudiometría → tinnitumetría → supraliminares → óseos, y terminar cada prueba antes de pasar a la siguiente.',
                'alumnos' => $quienes(static function ($a) { return ($a['secciones']['orden'] ?? 100) < 40; }),
                'alumnos_motivo' => 'orden bajo 40 %',
            ];
        }
        $tin = $k['secciones']['tinnitus'] ?? null;
        if ($tin !== null && $tin < self::CORTES['tinnitus']) {
            $out[] = [
                'titulo' => 'Tinnitumetría',
                'evidencia' => sprintf('La técnica de la tinnitumetría va en %d %%.', $tin),
                'accion' => 'Revisar los pasos que más fallan en la tabla de pasos (comparación en el oído contrario, intensidad de 1 en 1 dB, inhibición residual).',
                'alumnos' => [],
                'alumnos_motivo' => '',
            ];
        }
        if ($e['mirar']) {
            $out[] = [
                'titulo' => 'Seguimiento individual',
                'evidencia' => count($e['mirar']) . ' alumno(s) con logro bajo, en baja o con una conducta que casi no aparece.',
                'accion' => 'Revisar con cada uno sus últimas atenciones en su ficha, donde está el detalle paso a paso.',
                'alumnos' => array_values(array_column($e['mirar'], 'nombre')),
                'alumnos_motivo' => '',
            ];
        }
        return $out;
    }

    private static function peorPaciente(array $pacientes, string $seccion): ?array
    {
        $peor = null;
        foreach ($pacientes as $p) {
            $v = $p['secciones'][$seccion] ?? null;
            if ($v !== null && $p['n'] >= 3 && ($peor === null || $v < $peor['secciones'][$seccion])) {
                $peor = $p;
            }
        }
        return $peor;
    }

    public static function fechaCorta(?string $iso): string
    {
        if ($iso === null || strlen($iso) < 10) {
            return '';
        }
        return (int) substr($iso, 8, 2) . '-' . substr($iso, 5, 2);
    }

    private static function pct(int $a, int $b): ?int
    {
        return $b > 0 ? (int) round(100 * $a / $b) : null;
    }

    private static function mediana(array $v): float
    {
        sort($v);
        $n = count($v);
        return $n % 2 ? $v[intdiv($n, 2)] : ($v[$n / 2 - 1] + $v[$n / 2]) / 2;
    }
}
