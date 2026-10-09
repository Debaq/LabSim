<?php

declare(strict_types=1);

require_once __DIR__ . '/AudiometriaPaciente.php';
require_once __DIR__ . '/AudiometriaRegistro.php';
require_once __DIR__ . '/AppConfig.php';
require_once __DIR__ . '/CourseParams.php';

/**
 * Indicadores de técnica de la audiometría: compara lo que hizo el alumno
 * (AudiometriaRegistro) con las técnicas de la Bibliografía
 * (Bibliografia::TECNICAS): T00 orden de las pruebas, T01 umbrales aéreos,
 * T02 umbrales óseos.
 *
 * Cada regla dice qué pide la técnica ('texto'), si se cumplió ('cumple':
 * true, false o null cuando no se puede evaluar) y qué pasó ('detalle').
 * Las observaciones no descuentan: son cosas que el docente quiere ver (por
 * ejemplo, umbrales óseos en un oído sano, que no hacían falta).
 *
 * Por frecuencia hay dos fases: familiarización (subir de 10 en 10 hasta la
 * primera respuesta) y técnica (bajar 10 tras responder, subir 5 tras no
 * responder). "Subió 10" está bien en la primera y no en la segunda.
 *
 * Un "nivel" es una visita: estímulos seguidos a la misma intensidad. El
 * paso siguiente lo decide la respuesta al último estímulo de la visita. El
 * umbral es el nivel más bajo con 2 de 3 o 3 de 5 respuestas (mayoría y al
 * menos 2) contando los estímulos dados a ese nivel llegando desde abajo.
 */
final class AudiometriaTecnica
{
    public const PARAM_KEY = 'audiometria.tecnica';

    public const PRUEBAS = [
        'aereos' => 'Umbrales aéreos',
        'logo' => 'Logoaudiometría',
        'tinnitumetria' => 'Tinnitumetría',
        'supra' => 'Pruebas supraliminares',
        'oseos' => 'Umbrales óseos',
    ];

    public const ORDEN_FRECUENCIAS = [
        'aereos' => [1000, 2000, 3000, 4000, 6000, 8000, 500, 250, 125],
        'oseos' => [1000, 2000, 3000, 4000, 500, 250],
    ];

    /**
     * Tope del audiómetro por vía y frecuencia: [rango normal, rango
     * extendido] (intency_dict de resources/json/config_audiometer.json; el
     * test lo compara con el JSON). Al tope la familiarización no puede
     * subir 10, y llegar al tope sin respuesta es una frecuencia cerrada.
     */
    public const TOPES = [
        'aereos' => [125 => [100, 120], 250 => [100, 120], 500 => [100, 120], 1000 => [100, 120], 2000 => [100, 120],
            3000 => [100, 120], 4000 => [100, 120], 6000 => [100, 120], 8000 => [100, 120]],
        'oseos' => [125 => [40, 50], 250 => [45, 60], 500 => [50, 60], 1000 => [100, 100], 2000 => [100, 100],
            3000 => [100, 100], 4000 => [100, 100], 6000 => [100, 100], 8000 => [100, 100]],
    ];

    /** Frecuencias del promedio que decide el oído mejor (índices de AudiometriaPaciente::FRECUENCIAS). */
    private const PROMEDIO_IDX = [2, 3, 4, 6];
    /** Rango de la vía ósea (250 a 4000 Hz), para decidir si un oído es sano. */
    private const OSEA_IDX = [1, 2, 3, 4, 5, 6];
    /** Parte mínima de los estímulos dentro de la duración pedida. */
    private const DURACION_PCT = 0.8;

    private const OIDOS = ['OD', 'OI'];

    /** Parámetros del curso sobre los defaults (CourseParams 'audiometria.tecnica'). */
    public static function parametros(?int $courseId): array
    {
        $def = CourseParams::find(self::PARAM_KEY);
        $out = [];
        foreach ($def['defaults']['tecnica'] as $via => $campos) {
            $out[$via] = array_map('floatval', $campos);
        }
        $override = AppConfig::getEffective(self::PARAM_KEY, $courseId);
        foreach (($override['tecnica'] ?? []) as $via => $campos) {
            foreach ((array) $campos as $k => $v) {
                if (isset($out[$via][$k]) && is_numeric($v)) {
                    $out[$via][$k] = (float) $v;
                }
            }
        }
        return $out;
    }

    /** Los defaults sin base de datos (tests, o sin AppConfig a mano). */
    public static function parametrosDefault(): array
    {
        $def = CourseParams::find(self::PARAM_KEY);
        $out = [];
        foreach ($def['defaults']['tecnica'] as $via => $campos) {
            $out[$via] = array_map('floatval', $campos);
        }
        return $out;
    }

    /**
     * Sube cuando cambia cómo se evalúa (reglas, textos, umbrales): las
     * evaluaciones guardadas con otra versión se recalculan solas.
     */
    // 2: "Withe Noise" pasó a "White Noise" (2026-10-09); lo guardado
    // antes trae el rótulo viejo en el ruido de cada presentación.
    public const CACHE_VERSION = 2;

    /**
     * Indicadores de la atención $appointmentId del alumno $studentId, o null
     * si no usó el audiómetro con ese paciente. $logs: las filas de
     * action_logs del alumno si ya se tienen (payload como texto o array);
     * si no, se leen solo si hace falta (ver deAtenciones).
     */
    public static function paraAtencion(int $appointmentId, int $studentId, ?array $logs = null): ?array
    {
        return self::deAtenciones($studentId, [$appointmentId], $logs)[$appointmentId] ?? null;
    }

    /**
     * La técnica de varias atenciones de un alumno: [appointment_id => resultado
     * de evaluar() o null].
     *
     * Una atención cerrada no cambia, así que su evaluación se guarda en
     * audiometria_tecnica_cache y la próxima vez no se lee ni un registro: el
     * curso tenía ~70 mil filas del audiómetro y leerlas en cada visita de
     * Avance tardaba 11 s. La clave guarda todo lo que mueve el resultado
     * (CACHE_VERSION, los parámetros del curso, la ficha y la atención:
     * reabrirla y volver a cerrarla cambia su updated_at). Lo que falta se
     * calcula leyendo los registros del alumno UNA vez, repartidos por cita.
     * Sin la tabla (antes de aplicar schema.sql) se calcula igual, sin guardar.
     *
     * @param array<int,int> $appointmentIds
     * @return array<int,?array>
     */
    public static function deAtenciones(int $studentId, array $appointmentIds, ?array $logs = null): array
    {
        $ids = array_values(array_unique(array_map('intval', $appointmentIds)));
        if (!$ids) {
            return [];
        }
        $pdo = Db::get();
        $ph = implode(',', array_fill(0, count($ids), '?'));
        $stmt = $pdo->prepare(
            "SELECT a.id, a.course_id, c.data, c.updated_at AS caso_at, att.estado, att.updated_at AS att_at
               FROM appointments a
               LEFT JOIN cases c ON c.id = a.case_id
               LEFT JOIN attendances att ON att.appointment_id = a.id AND att.student_id = ?
              WHERE a.id IN ({$ph})"
        );
        $stmt->execute(array_merge([$studentId], $ids));
        $citas = [];
        $paramsCurso = [];
        foreach ($stmt->fetchAll() as $f) {
            $courseId = $f['course_id'] !== null ? (int) $f['course_id'] : null;
            $k = (string) $courseId;
            if (!isset($paramsCurso[$k])) {
                $paramsCurso[$k] = self::parametros($courseId);
            }
            $citas[(int) $f['id']] = [
                'caso' => $f['data'] ? json_decode((string) $f['data'], true) : null,
                'params' => $paramsCurso[$k],
                'cerrada' => $f['estado'] === 'atendido',
                'clave' => sha1(json_encode([self::CACHE_VERSION, $paramsCurso[$k], $f['caso_at'], $f['att_at']])),
            ];
        }

        $out = [];
        $guardadas = self::leerCache($studentId, array_keys($citas));
        $faltan = [];
        foreach ($citas as $ap => $c) {
            if (!is_array($c['caso'])) {
                $out[$ap] = null;
            } elseif ($c['cerrada'] && isset($guardadas[$ap]) && $guardadas[$ap]['clave'] === $c['clave']) {
                $out[$ap] = $guardadas[$ap]['resultado'];
            } else {
                $faltan[] = $ap;
            }
        }
        if (!$faltan) {
            return $out;
        }

        if ($logs === null) {
            // De a una fila y sin traer todo a memoria: solo se decodifica lo
            // de las citas que faltan (el número de cita se mira en el texto).
            $stmt = $pdo->prepare("SELECT client_ts, action, payload FROM action_logs WHERE user_id = ? AND action LIKE 'audio\\_%' ESCAPE '\\' ORDER BY id");
            $stmt->execute([$studentId]);
            $quiero = array_flip($faltan);
            $porCita = [];
            while (($l = $stmt->fetch()) !== false) {
                if (!preg_match('/"appointment_id":"?(\d+)/', (string) $l['payload'], $m) || !isset($quiero[(int) $m[1]])) {
                    continue;
                }
                $p = json_decode((string) $l['payload'], true);
                if (is_array($p)) {
                    $porCita[(int) $m[1]][] = ['client_ts' => $l['client_ts'], 'action' => $l['action'], 'payload' => $p];
                }
            }
            $stmt->closeCursor();   // antes de guardar (ver Db::get)
        } else {
            $porCita = self::logsPorCita($logs, $faltan);
        }
        foreach ($faltan as $ap) {
            $c = $citas[$ap];
            $res = isset($porCita[$ap])
                ? self::evaluar(AudiometriaRegistro::leer($porCita[$ap], $c['caso']), $c['caso'], $c['params'])
                : null;
            $out[$ap] = $res;
            if ($c['cerrada']) {
                self::guardarCache($ap, $studentId, $c['clave'], $res);
            }
        }
        return $out;
    }

    /**
     * Las filas del audiómetro repartidas por cita, con el payload
     * decodificado una sola vez (antes se decodificaba todo el historial del
     * alumno por cada atención).
     *
     * @param array<int,int> $soloCitas
     * @return array<int,array<int,array>>
     */
    public static function logsPorCita(array $logs, array $soloCitas): array
    {
        $quiero = array_flip(array_map('intval', $soloCitas));
        $out = [];
        foreach ($logs as $l) {
            if (strpos((string) $l['action'], 'audio_') !== 0) {
                continue;
            }
            $p = $l['payload'] ?? null;
            if (!is_array($p)) {
                $p = $p ? json_decode((string) $p, true) : null;
            }
            $ap = is_array($p) ? (int) ($p['appointment_id'] ?? 0) : 0;
            if ($ap > 0 && isset($quiero[$ap])) {
                $out[$ap][] = ['client_ts' => $l['client_ts'], 'action' => $l['action'], 'payload' => $p];
            }
        }
        return $out;
    }

    /** @return array<int,array{clave:string, resultado:?array}> */
    private static function leerCache(int $studentId, array $ids): array
    {
        if (!$ids) {
            return [];
        }
        try {
            $ph = implode(',', array_fill(0, count($ids), '?'));
            $stmt = Db::get()->prepare("SELECT appointment_id, clave, resultado FROM audiometria_tecnica_cache WHERE student_id = ? AND appointment_id IN ({$ph})");
            $stmt->execute(array_merge([$studentId], $ids));
            $out = [];
            foreach ($stmt->fetchAll() as $f) {
                $res = json_decode((string) $f['resultado'], true);
                $out[(int) $f['appointment_id']] = ['clave' => (string) $f['clave'], 'resultado' => is_array($res) ? $res : null];
            }
            return $out;
        } catch (PDOException $e) {
            return [];   // sin la tabla todavía: se calcula sin guardar
        }
    }

    /** Guardar es un extra: si la base está ocupada o falta la tabla, la página sigue igual. */
    private static function guardarCache(int $appointmentId, int $studentId, string $clave, ?array $resultado): void
    {
        try {
            Db::get()->prepare(
                'INSERT INTO audiometria_tecnica_cache (appointment_id, student_id, clave, resultado) VALUES (?, ?, ?, ?)
                 ON CONFLICT(appointment_id, student_id) DO UPDATE SET clave = excluded.clave, resultado = excluded.resultado, created_at = CURRENT_TIMESTAMP'
            )->execute([$appointmentId, $studentId, $clave, json_encode($resultado, JSON_UNESCAPED_UNICODE)]);
        } catch (PDOException $e) {
            error_log('[AudiometriaTecnica] no se pudo guardar la evaluación: ' . $e->getMessage());
        }
    }

    /** Las filas del audiómetro de una atención, con el payload decodificado. */
    public static function logsDeAtencion(array $logs, int $appointmentId): array
    {
        $out = [];
        foreach ($logs as $l) {
            if (strpos((string) $l['action'], 'audio_') !== 0) {
                continue;
            }
            $p = $l['payload'] ?? null;
            if (!is_array($p)) {
                $p = $p ? json_decode((string) $p, true) : null;
            }
            if (!is_array($p) || (int) ($p['appointment_id'] ?? 0) !== $appointmentId) {
                continue;
            }
            $out[] = ['client_ts' => $l['client_ts'], 'action' => $l['action'], 'payload' => $p];
        }
        return $out;
    }

    /** Null si en la atención no hubo nada que evaluar. */
    public static function evaluar(array $registro, array $caso, array $params): ?array
    {
        if ($registro['presentaciones'] === [] && $registro['pruebas'] === []) {
            return null;
        }
        $paciente = new AudiometriaPaciente($caso);
        $out = [
            'reconstruido' => $registro['reconstruido'],
            'con_ms' => $registro['con_ms'],
            'orden' => self::orden($registro['pruebas']),
            'aereos' => self::via('aereos', $registro, $paciente, $params['aereos']),
            'oseos' => self::via('oseos', $registro, $paciente, $params['oseos']),
        ];
        foreach (['orden', 'aereos', 'oseos'] as $k) {
            $out[$k]['puntaje'] = self::sumar([$out[$k]]);
            foreach ($out[$k]['oidos'] ?? [] as $oido => $reglas) {
                $out[$k]['puntaje_oidos'][$oido] = self::sumar([['reglas' => $reglas]]);
            }
        }
        $out['puntaje'] = self::sumar([$out['orden'], $out['aereos'], $out['oseos']]);
        return $out;
    }

    // ---- T00: orden ---------------------------------------------------------

    private static function orden(array $pruebas): array
    {
        $claves = array_keys(self::PRUEBAS);
        $primeras = [];
        $observaciones = [];
        $ultima = null;
        foreach ($pruebas as [$t, $prueba]) {
            if (!isset(self::PRUEBAS[$prueba])) {
                continue;
            }
            if (!isset($primeras[$prueba])) {
                $primeras[$prueba] = $t;
            } elseif ($ultima !== null && $ultima !== $prueba
                    && array_search($prueba, $claves, true) < array_search($ultima, $claves, true)) {
                $observaciones[self::PRUEBAS[$prueba] . '|' . self::PRUEBAS[$ultima]] = sprintf(
                    'Volvió a %s después de %s.', lcfirst(self::PRUEBAS[$prueba]), lcfirst(self::PRUEBAS[$ultima]));
            }
            $ultima = $prueba;
        }
        $hechas = array_keys($primeras);
        $esperado = array_values(array_intersect($claves, $hechas));
        $nombres = array_map(static function ($p) { return self::PRUEBAS[$p]; }, $hechas);
        $reglas = [];
        if (count($hechas) >= 2) {
            $reglas[] = [
                'texto' => 'Las pruebas van en orden: umbrales aéreos, logoaudiometría, tinnitumetría, supraliminares, umbrales óseos.',
                'cumple' => $hechas === $esperado,
                'detalle' => 'Se hizo: ' . implode(' → ', $nombres) . '.',
            ];
        }
        return ['reglas' => $reglas, 'observaciones' => array_values($observaciones), 'hechas' => $nombres];
    }

    // ---- T01 / T02: umbrales -------------------------------------------------

    private static function via(string $via, array $registro, AudiometriaPaciente $paciente, array $p): array
    {
        $pres = array_values(array_filter($registro['presentaciones'], static function ($x) use ($via) {
            return $x['prueba'] === $via && $x['oido'] !== null;
        }));
        $pta = [self::promedio($paciente, 0), self::promedio($paciente, 1)];
        $tol = (int) $p['tol_oido'];
        $mejor = abs($pta[0] - $pta[1]) <= $tol ? null : ($pta[0] < $pta[1] ? 0 : 1);
        $inicioEsperado = $mejor === null ? null : ($via === 'aereos' ? $mejor : 1 - $mejor);

        // Óseos: solo se exigen en los oídos con la vía aérea alterada.
        $requeridos = [0, 1];
        if ($via === 'oseos') {
            $requeridos = array_values(array_filter([0, 1], static function ($o) use ($paciente, $p) {
                return !self::oidoSano($paciente, $o, (int) $p['oido_sano']);
            }));
        }

        $res = ['hecha' => $pres !== [], 'reglas' => [], 'oidos' => [], 'umbrales' => [], 'observaciones' => []];
        if ($pres === []) {
            if ($via === 'aereos' || $requeridos !== []) {
                $res['reglas'][] = [
                    'texto' => $via === 'aereos' ? 'Se toman los umbrales aéreos.' : 'Se toman los umbrales óseos en los oídos con la vía aérea alterada.',
                    'cumple' => false,
                    'detalle' => 'No se tomaron.',
                ];
            }
            return $res;
        }

        $bloques = self::bloques($pres, $via, $p);
        $primero = $pres[0];

        // Repeticiones, por oído: la de 1 kHz al final y la del oído completo
        // cuando hace falta son de la técnica; las demás son advertencia.
        $retests = [];
        $sinNecesidad = [];
        foreach (array_values(array_unique(array_column($bloques, 'oido'))) as $o) {
            $indices = array_keys(array_filter($bloques, static function ($b) use ($o) { return $b['oido'] === $o; }));
            $clas = self::repeticiones(array_values(array_intersect_key($bloques, array_flip($indices))), $via, $p);
            $retests[$o] = $clas['retest'];
            foreach ($indices as $local => $global) {
                $bloques[$global]['innecesaria'] = in_array($local, $clas['innecesarias'], true);
                $bloques[$global]['previo_verificado'] = $clas['previos'][$local] ?? null;
                if ($bloques[$global]['innecesaria']) {
                    $sinNecesidad[] = $bloques[$global];
                }
            }
        }
        if ($sinNecesidad) {
            $segundos = 0.0;
            $cuales = [];
            foreach ($sinNecesidad as $b) {
                $ultimo = end($b['pres']);
                $segundos += max(0.0, (float) ($ultimo['t_off'] ?? $ultimo['t_on']) - (float) $b['pres'][0]['t_on']);
                $cuales[] = self::OIDOS[$b['oido']] . ' ' . self::hz($b['freq'])
                    . ($b['previo_verificado'] === null ? '' : ' (ya verificado en ' . $b['previo_verificado'] . ')');
            }
            $res['observaciones'][] = 'Repitió sin necesidad ' . self::lista($cuales) . '. Sin esas repeticiones habría ganado '
                . self::tiempo($segundos) . '.';
        }

        $instr = $via === 'aereos' ? AudiometriaRegistro::INSTR_AEREA : AudiometriaRegistro::INSTR_OSEA;
        $res['reglas'][] = [
            'texto' => 'Se da la instrucción al paciente antes del primer estímulo.',
            'cumple' => in_array($primero['instruccion'], $instr, true),
            'detalle' => $primero['instruccion'] === null
                ? 'El primer estímulo fue sin instrucción.'
                : 'Instrucción vigente en el primer estímulo: ' . str_replace('_', ' ', (string) $primero['instruccion']) . '.',
        ];

        $res['reglas'][] = [
            'texto' => $via === 'aereos' ? 'Se parte por el oído mejor.' : 'Se parte por el oído peor.',
            'cumple' => $inicioEsperado === null ? true : $primero['oido'] === $inicioEsperado,
            'detalle' => $inicioEsperado === null
                ? 'Los dos oídos están parejos: vale partir por cualquiera. Se partió por ' . self::OIDOS[$primero['oido']] . '.'
                : 'Se partió por ' . self::OIDOS[$primero['oido']] . '; el oído ' . ($via === 'aereos' ? 'mejor' : 'peor') . ' es ' . self::OIDOS[$inicioEsperado] . '.',
        ];

        // Volver al otro oído a repetir sin necesidad ya es advertencia: no
        // cuenta además como cambio de oído.
        $cambios = 0;
        $anterior = null;
        foreach ($bloques as $b) {
            if ($b['innecesaria']) {
                continue;
            }
            if ($anterior !== null && $b['oido'] !== $anterior) {
                $cambios++;
            }
            $anterior = $b['oido'];
        }
        $res['reglas'][] = [
            'texto' => 'Se termina un oído antes de pasar al otro.',
            'cumple' => $cambios <= 1,
            'detalle' => $cambios <= 1 ? 'Un oído a la vez.' : "Se cambió de oído {$cambios} veces.",
        ];

        if (!$registro['con_ms']) {
            $res['reglas'][] = [
                'texto' => sprintf('Cada estímulo dura entre %s y %s segundos.', self::num($p['dur_min']), self::num($p['dur_max'])),
                'cumple' => null,
                'detalle' => 'No se puede medir: este registro tiene la hora en segundos enteros.',
            ];
        } else {
            $cortos = $largos = $medidos = 0;
            foreach ($pres as $x) {
                if ($x['duracion'] === null) {
                    continue;
                }
                $medidos++;
                if ($x['duracion'] < $p['dur_min']) {
                    $cortos++;
                } elseif ($x['duracion'] > $p['dur_max']) {
                    $largos++;
                }
            }
            $bien = $medidos - $cortos - $largos;
            $res['reglas'][] = [
                'texto' => sprintf('Cada estímulo dura entre %s y %s segundos.', self::num($p['dur_min']), self::num($p['dur_max'])),
                'cumple' => $medidos === 0 ? null : $bien >= self::DURACION_PCT * $medidos,
                'detalle' => sprintf('%d de %d estímulos en ese rango; %d más cortos y %d más largos.', $bien, $medidos, $cortos, $largos),
            ];
        }

        $hechos = array_values(array_unique(array_column($bloques, 'oido')));
        foreach ($requeridos as $o) {
            if (!in_array($o, $hechos, true)) {
                $res['reglas'][] = [
                    'texto' => 'Se toman los umbrales de ' . self::OIDOS[$o] . '.',
                    'cumple' => false,
                    'detalle' => 'No se tomaron.',
                ];
            }
        }
        if ($via === 'oseos') {
            foreach ($hechos as $o) {
                if (!in_array($o, $requeridos, true)) {
                    $res['observaciones'][] = 'Se tomaron umbrales óseos en ' . self::OIDOS[$o] . ', que tiene la vía aérea normal: no eran necesarios.';
                }
            }
        }

        foreach ($hechos as $o) {
            $propios = array_values(array_filter($bloques, static function ($b) use ($o) { return $b['oido'] === $o; }));
            $res['oidos'][self::OIDOS[$o]] = self::oido($propios, $via, $p, $retests[$o]);
            $res['umbrales'][self::OIDOS[$o]] = self::umbrales($propios, $via, $o, $paciente);
        }

        $coinciden = $total = 0;
        foreach ($res['umbrales'] as $filas) {
            foreach ($filas as $f) {
                $total++;
                if ($f['estado'] === 'coincide') {
                    $coinciden++;
                }
            }
        }
        $res['reglas'][] = [
            'texto' => 'Los umbrales obtenidos corresponden a la audición del paciente.',
            'cumple' => $total === 0 ? null : $coinciden === $total,
            'detalle' => "{$coinciden} de {$total} umbrales.",
        ];
        return $res;
    }

    /** Reglas de un oído: inicio, pasos, cierre, orden y repetición de 1 kHz. */
    private static function oido(array $bloques, string $via, array $p, ?int $r): array
    {
        $reglas = [];
        $orden = self::ORDEN_FRECUENCIAS[$via];

        $b0 = $bloques[0];
        $reglas[] = [
            'texto' => sprintf('Se parte en 1 kHz a %d dB HL.', (int) $p['nivel_inicial']),
            'cumple' => $b0['freq'] === 1000 && $b0['inicio'] === (int) $p['nivel_inicial'],
            'detalle' => sprintf('Se partió en %s a %d dB HL.', self::hz($b0['freq']), $b0['inicio']),
        ];

        // Inicio de cada frecuencia nueva: 10 dB sobre el umbral de la anterior.
        $mal = [];
        $evaluadas = 0;
        $vistas = [$b0['freq'] => true];
        for ($i = 1, $n = count($bloques); $i < $n; $i++) {
            $b = $bloques[$i];
            $previo = $bloques[$i - 1]['umbral'];
            $repite = isset($vistas[$b['freq']]);
            $vistas[$b['freq']] = true;
            if ($repite || $previo === null) {
                continue;
            }
            $evaluadas++;
            $esperado = $previo + (int) $p['sobre_anterior'];
            if ($b['inicio'] !== $esperado) {
                $mal[] = sprintf('%s partió en %d dB (umbral anterior %d, correspondía %d)', self::hz($b['freq']), $b['inicio'], $previo, $esperado);
            }
        }
        $reglas[] = [
            'texto' => sprintf('Cada frecuencia nueva parte %d dB sobre el umbral de la anterior.', (int) $p['sobre_anterior']),
            'cumple' => $evaluadas === 0 ? null : $mal === [],
            'detalle' => $mal === [] ? ($evaluadas === 0 ? 'Ninguna frecuencia tenía el umbral anterior verificado.' : 'Así fue en las ' . $evaluadas . ' frecuencias.') : implode('; ', $mal) . '.',
        ];

        $desvios = [];
        foreach ($bloques as $b) {
            foreach ($b['desvios'] as $d) {
                $desvios[] = $d;
            }
        }
        $reglas[] = [
            'texto' => sprintf('Familiarización subiendo de %d en %d dB hasta la primera respuesta; después, bajar %d dB tras responder y subir %d dB tras no responder.',
                (int) $p['paso_familiarizacion'], (int) $p['paso_familiarizacion'], (int) $p['paso_bajada'], (int) $p['paso_subida']),
            'cumple' => $desvios === [],
            'detalle' => $desvios === [] ? 'Sin desvíos.' : implode(' ', array_slice($desvios, 0, 8)) . (count($desvios) > 8 ? ' (y ' . (count($desvios) - 8) . ' más)' : ''),
        ];

        $abiertos = [];
        foreach ($bloques as $b) {
            if (!$b['cerrado']) {
                $abiertos[] = self::hz($b['freq']);
            }
        }
        $reglas[] = [
            'texto' => 'Se verifica el umbral con 2 de 3 o 3 de 5 respuestas subiendo antes de cambiar de frecuencia.',
            'cumple' => $abiertos === [],
            'detalle' => $abiertos === [] ? 'Se verificó en todas las frecuencias.' : 'Cambió de frecuencia sin verificar 2 de 3 ni 3 de 5 en: ' . implode(', ', array_unique($abiertos)) . '.',
        ];

        // El orden mira la primera vez que tomó cada frecuencia: las
        // repeticiones son su propia regla (1 kHz) o advertencia.
        $secuencia = array_values(array_unique(array_column($bloques, 'freq')));
        $reglas[] = [
            'texto' => 'Orden de frecuencias: ' . implode(', ', array_map([self::class, 'hz'], $orden)) . '.',
            'cumple' => array_slice($secuencia, 0, count($orden)) === $orden,
            'detalle' => 'Se hizo: ' . implode(', ', array_map([self::class, 'hz'], $secuencia)) . '.',
        ];

        if ($r === null) {
            $reglas[] = [
                'texto' => sprintf('Se repite 1 kHz al final; si difiere más de %d dB de la primera vez, se repite todo el umbral.', (int) $p['dif_repeticion']),
                'cumple' => false,
                'detalle' => 'No se repitió 1 kHz.',
            ];
        } else {
            $u1 = $b0['umbral'];
            $u2 = $bloques[$r]['umbral'];
            if ($u1 === null || $u2 === null) {
                $cumple = null;
                $detalle = 'Se repitió 1 kHz, pero en alguna de las dos veces no verificó 2 de 3 ni 3 de 5: no hay umbrales para comparar.';
            } else {
                $dif = abs($u2 - $u1);
                $resto = array_column(array_slice($bloques, $r + 1), 'freq');
                $repetido = array_diff($orden, $resto) === [];
                if ($dif > $p['dif_repeticion']) {
                    $cumple = $repetido;
                    $detalle = sprintf('1 kHz dio %d y %d dB (diferencia %d): %s', $u1, $u2, $dif, $repetido ? 'se repitió el umbral.' : 'correspondía repetir todo el umbral y no se hizo.');
                } else {
                    $cumple = true;
                    $detalle = sprintf('1 kHz dio %d y %d dB (diferencia %d).', $u1, $u2, $dif);
                }
            }
            $reglas[] = [
                'texto' => sprintf('Se repite 1 kHz al final; si difiere más de %d dB de la primera vez, se repite todo el umbral.', (int) $p['dif_repeticion']),
                'cumple' => $cumple,
                'detalle' => $detalle,
            ];
        }
        return $reglas;
    }

    /**
     * Umbral obtenido en cada frecuencia contra el del paciente, en el orden
     * en que el alumno los tomó: la repetición de 1 kHz (o de cualquier
     * frecuencia) es su propia fila, marcada 'repeticion'.
     */
    private static function umbrales(array $bloques, string $via, int $oido, AudiometriaPaciente $paciente): array
    {
        $vistas = [];
        $filas = [];
        foreach ($bloques as $b) {
            $hz = $b['freq'];
            $repeticion = isset($vistas[$hz]);
            $vistas[$hz] = true;
            $idx = array_search($hz, AudiometriaPaciente::FRECUENCIAS, true);
            $real = $idx === false ? null : $paciente->umbralReal($via === 'aereos' ? 'aerea' : 'osea', $idx, $oido);
            $sombra = $idx === false ? null : $paciente->umbralSinRuido($via === 'aereos' ? 'aerea' : 'osea', $idx, $oido);
            $est = $b['umbral'];
            if ($real === null) {
                $estado = 'sin dato';
            } elseif ($est === null && $b['sin_respuesta']) {
                // corresponde si el paciente de verdad no oye hasta ahí
                $aparente = $b['con_ruido'] ? $real : (int) $sombra;
                $estado = $aparente > $b['maximo'] ? 'coincide' : 'difiere';
            } elseif ($est === null) {
                $estado = 'sin verificar';
            } elseif (abs($est - $real) <= 5) {
                $estado = 'coincide';
            } elseif (!$b['con_ruido'] && $sombra !== null && $sombra < $real - 5 && abs($est - $sombra) <= 5) {
                $estado = 'sombra';
            } else {
                $estado = 'difiere';
            }
            $filas[] = [
                'freq' => $hz,
                'repeticion' => $repeticion,
                'innecesaria' => $b['innecesaria'] ?? false,
                'estimado' => $est,
                'aprox' => $b['aprox'],
                'real' => $real,
                'sombra' => $sombra,
                'con_ruido' => $b['con_ruido'],
                'sin_respuesta' => $b['sin_respuesta'],
                'estado' => $estado,
            ];
        }
        return $filas;
    }

    /**
     * Bloques: estímulos seguidos al mismo oído y frecuencia. Cada uno con
     * sus visitas (niveles), el umbral, el nivel de inicio y los desvíos de
     * paso.
     */
    private static function bloques(array $pres, string $via, array $p): array
    {
        $bloques = [];
        foreach ($pres as $x) {
            $n = count($bloques);
            if ($n === 0 || $bloques[$n - 1]['oido'] !== $x['oido'] || $bloques[$n - 1]['freq'] !== $x['freq']) {
                $bloques[] = ['oido' => $x['oido'], 'freq' => $x['freq'], 'pres' => []];
                $n++;
            }
            $bloques[$n - 1]['pres'][] = $x;
        }
        foreach ($bloques as &$b) {
            $b = $b + self::analizar($b, $via, $p);
        }
        unset($b);
        return $bloques;
    }

    private static function analizar(array $bloque, string $via, array $p): array
    {
        $topes = self::TOPES[$via][$bloque['freq']] ?? [];
        $visitas = [];
        foreach ($bloque['pres'] as $x) {
            $n = count($visitas);
            if ($n === 0 || $visitas[$n - 1]['int'] !== $x['int']) {
                $visitas[] = ['int' => $x['int'], 'oyo' => null, 'ultimo' => null, 'respuestas' => [], 't' => $x['t_on']];
                $n++;
            }
            $v = &$visitas[$n - 1];
            $v['respuestas'][] = $x['oyo'];
            // el paso siguiente lo decide la respuesta al último estímulo
            $v['ultimo'] = $x['oyo'];
            if ($x['oyo'] === true || ($v['oyo'] === null && $x['oyo'] !== null)) {
                $v['oyo'] = $v['oyo'] === true ? true : $x['oyo'];
            }
            unset($v);
        }
        $conRuido = false;
        foreach ($bloque['pres'] as $x) {
            if ($x['ruido'] !== null) {
                $conRuido = true;
            }
        }

        $primera = null;
        foreach ($visitas as $i => $v) {
            if ($v['oyo'] === true) {
                $primera = $i;
                break;
            }
        }

        $desvios = [];
        $etiqueta = self::OIDOS[$bloque['oido']] . ' ' . self::hz($bloque['freq']);
        for ($i = 1, $n = count($visitas); $i < $n; $i++) {
            $a = $visitas[$i - 1];
            $b = $visitas[$i];
            if ($a['ultimo'] === null) {
                continue;
            }
            $delta = $b['int'] - $a['int'];
            if ($primera === null || $i - 1 < $primera) {
                $esperado = (int) $p['paso_familiarizacion'];
                $fase = 'en la familiarización';
            } else {
                $esperado = $a['ultimo'] ? -(int) $p['paso_bajada'] : (int) $p['paso_subida'];
                $fase = $a['ultimo'] ? 'tras responder' : 'tras no responder';
            }
            // al tope del equipo no se puede subir el paso completo
            $alTope = $esperado > 0 && $delta > 0 && $delta < $esperado && in_array($b['int'], $topes, true);
            if ($delta !== $esperado && !$alTope) {
                $desvios[] = sprintf('%s (%s): %s a %d dB pasó a %d dB (correspondía %+d).',
                    $etiqueta, date('H:i:s', (int) $b['t']), $fase, $a['int'], $b['int'], $esperado);
            }
        }

        // Criterio por estímulos en ascenso: 2 de 3 o 3 de 5 son respuestas
        // sobre estímulos dados a ese nivel llegando desde abajo.
        $asc = [];
        if ($primera !== null) {
            for ($i = $primera + 1, $n = count($visitas); $i < $n; $i++) {
                if ($visitas[$i]['int'] <= $visitas[$i - 1]['int']) {
                    continue;
                }
                $nivel = $visitas[$i]['int'];
                $asc[$nivel] = $asc[$nivel] ?? ['total' => 0, 'oyo' => 0];
                foreach ($visitas[$i]['respuestas'] as $r) {
                    if ($r === null) {
                        continue;
                    }
                    $asc[$nivel]['total']++;
                    if ($r) {
                        $asc[$nivel]['oyo']++;
                    }
                }
            }
        }
        ksort($asc);
        $umbral = null;
        foreach ($asc as $nivel => $c) {
            if ($c['oyo'] >= 2 && 2 * $c['oyo'] > $c['total']) {
                $umbral = (int) $nivel;
                break;
            }
        }
        $aprox = null;
        foreach ($visitas as $v) {
            if ($v['oyo'] === true && ($aprox === null || $v['int'] < $aprox)) {
                $aprox = $v['int'];
            }
        }
        // Sin ninguna respuesta hasta el tope del equipo: la búsqueda está
        // terminada, el oído no responde en esa frecuencia.
        $maximo = max(array_column($visitas, 'int'));
        $sinRespuesta = $primera === null && $topes !== [] && $maximo >= $topes[0];
        return [
            'inicio' => $visitas[0]['int'],
            'umbral' => $umbral,
            'aprox' => $aprox,
            'sin_respuesta' => $sinRespuesta,
            'maximo' => $maximo,
            'cerrado' => $umbral !== null || $sinRespuesta,
            'desvios' => $desvios,
            'con_ruido' => $conRuido,
        ];
    }

    /**
     * Repeticiones de un oído. 'retest' es la repetición de 1 kHz que pide la
     * técnica: el primer 1 kHz después de haber pasado por todas las demás
     * frecuencias. Si difiere más de lo permitido, lo que sigue es repetir
     * el oído completo y también es de la técnica. 'innecesarias' son los
     * bloques de una frecuencia que ya estaba verificada en ese oído.
     * 'previos': el umbral ya verificado de cada repetición innecesaria.
     */
    private static function repeticiones(array $bloques, string $via, array $p): array
    {
        $primeras = [];
        foreach ($bloques as $i => $b) {
            if (!isset($primeras[$b['freq']])) {
                $primeras[$b['freq']] = $i;
            }
        }
        $resto = array_diff_key($primeras, [1000 => true]);
        $ultimaNueva = $resto ? max($resto) : 0;
        $r = null;
        foreach ($bloques as $i => $b) {
            if ($i > $ultimaNueva && $i > 0 && $b['freq'] === 1000) {
                $r = $i;
                break;
            }
        }
        $repetirTodo = false;
        if ($r !== null && $bloques[0]['umbral'] !== null && $bloques[$r]['umbral'] !== null) {
            $repetirTodo = abs($bloques[$r]['umbral'] - $bloques[0]['umbral']) > $p['dif_repeticion'];
        }
        $verificadas = [];
        $innecesarias = [];
        $previos = [];
        foreach ($bloques as $i => $b) {
            $necesaria = $i === $r || ($repetirTodo && $i > $r);
            if (!$necesaria && isset($verificadas[$b['freq']])) {
                $innecesarias[] = $i;
                $previos[$i] = $verificadas[$b['freq']];
            }
            if ($b['cerrado']) {
                $verificadas[$b['freq']] = $b['umbral'] !== null ? $b['umbral'] . ' dB' : 'sin respuesta';
            }
        }
        return ['retest' => $r, 'innecesarias' => $innecesarias, 'previos' => $previos];
    }

    // ---- utilidades ----------------------------------------------------------

    /** "45 s", "1 min 20 s". */
    public static function tiempo(float $segundos): string
    {
        $s = (int) round($segundos);
        if ($s < 60) {
            return $s . ' s';
        }
        return intdiv($s, 60) . ' min' . ($s % 60 ? ' ' . ($s % 60) . ' s' : '');
    }

    /** "a", "a y b", "a, b y c". */
    private static function lista(array $items): string
    {
        if (count($items) <= 1) {
            return implode('', $items);
        }
        $ultimo = array_pop($items);
        return implode(', ', $items) . ' y ' . $ultimo;
    }

    /** Promedio aéreo 500-1000-2000-4000 del caso (decide oído mejor y peor). */
    private static function promedio(AudiometriaPaciente $paciente, int $oido): float
    {
        $suma = 0;
        foreach (self::PROMEDIO_IDX as $f) {
            $suma += $paciente->umbralReal('aerea', $f, $oido);
        }
        return $suma / count(self::PROMEDIO_IDX);
    }

    /** Oído sano: vía aérea dentro de lo normal de 250 a 4000 Hz. */
    private static function oidoSano(AudiometriaPaciente $paciente, int $oido, int $corte): bool
    {
        foreach (self::OSEA_IDX as $f) {
            if ($paciente->umbralReal('aerea', $f, $oido) > $corte) {
                return false;
            }
        }
        return true;
    }

    /**
     * Suma de reglas evaluables y cumplidas de varias secciones, con el
     * porcentaje de logro (null si no hubo nada evaluable). Cada regla pesa
     * lo mismo.
     */
    public static function sumar(array $secciones): array
    {
        $cumple = $total = 0;
        foreach ($secciones as $s) {
            $listas = [$s['reglas'] ?? []];
            foreach ($s['oidos'] ?? [] as $r) {
                $listas[] = $r;
            }
            foreach ($listas as $reglas) {
                foreach ($reglas as $r) {
                    if ($r['cumple'] === null) {
                        continue;
                    }
                    $total++;
                    if ($r['cumple']) {
                        $cumple++;
                    }
                }
            }
        }
        return ['cumple' => $cumple, 'total' => $total, 'pct' => $total > 0 ? (int) round(100 * $cumple / $total) : null];
    }

    public static function hz(int $hz): string
    {
        return $hz >= 1000 ? rtrim(rtrim(number_format($hz / 1000, 1, ',', ''), '0'), ',') . ' kHz' : $hz . ' Hz';
    }

    private static function num(float $x): string
    {
        return rtrim(rtrim(number_format($x, 1, ',', ''), '0'), ',');
    }
}
