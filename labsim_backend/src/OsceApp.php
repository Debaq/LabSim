<?php

declare(strict_types=1);

require_once __DIR__ . '/Osce.php';
require_once __DIR__ . '/OscePauta.php';
require_once __DIR__ . '/LlmChat.php';
require_once __DIR__ . '/AnamnesisDraft.php';

/**
 * Estaciones del OSCE que se rinden en la app LabSim (pasos 4 y 5 de
 * docs/osce_plan.md): configuración del equipo, marcaje de curvas y
 * ejecución del protocolo, en el ABR (PEATC, ECochG, latencias, ASSR) o en
 * el VEMP (cVEMP, oVEMP).
 *
 * El PC de la estación entra a LabSim como "Estación OSCE" con el código
 * corto de la estación (app_codigo en osce_estacion.config); cada alumno
 * escribe el suyo y la app abre el equipo con el caso de la estación. Al
 * entregar, la app manda (osce_entrega del ABR o del VEMP, mismo formato):
 *
 *   panel/equipo  lo que quedó configurado al entregar
 *   curvas        cada curva EN EL ORDEN en que se registró: cómo se tomó
 *                 (oído, intensidad, estímulo, filtros...) y las ondas que el
 *                 alumno marcó
 *   verdad        por curva, lo que el equipo no muestra: si hay respuesta en
 *                 esa intensidad, la latencia de cada onda y el umbral
 *
 * Cada criterio es un osce_item de tipo 'auto' con su regla en config
 * ({"regla": ..., "bonus": true|false}). Las bonificaciones suman pero no
 * suben el máximo (la estación no pasa del 100 %).
 *
 * "Hay respuesta" en una curva, para juzgar la ESTRATEGIA, es que el alumno
 * marcó en ella la onda de respuesta del examen (V en el PEATC, p13 en el
 * cVEMP...): se evalúa si lo que hizo es coherente con lo que vio. La verdad
 * del generador se usa solo para saber si el umbral que encontró es el
 * real: un error de lectura no se castiga dos veces (decidido 2026-11-25).
 *
 * La entrega completa queda en una fila de osce_resultado sin ítem
 * (registro): con ella se vuelve a corregir si el docente ajusta la pauta,
 * sin pisar los puntajes que él puso a mano.
 */
final class OsceApp
{
    public const TIPOS = ['config_equipo', 'marcaje', 'protocolo', 'conclusion'];

    /**
     * Criterios de la estación de conclusión (los corrige la IA): el
     * formato de informe del Protocolo Técnico ORL 2019. "texto | puntos"
     * por línea en el editor.
     */
    public const CRITERIOS_CONCLUSION = [
        'peatc' => [
            ['Describe por OD y OI qué ondas se registran a la intensidad máxima, con su morfología y replicabilidad', 1],
            ['Informa por oído si las latencias absolutas (I, III, V) y los interpeaks (I-III, III-V, I-V) están dentro de lo esperado', 2],
            ['Informa el umbral de la onda V de cada oído', 1],
            ['Concluye el tipo de audición correcto en cada oído (normal, transmisión, sensorioneural, mixta o compromiso retrococlear)', 2],
            ['Estima el grado (dB HL aproximados) para el rango 2-4 kHz', 1],
            ['Sigue el formato del protocolo: por oído y con observaciones (estado del paciente, exámenes que se adjuntan)', 1],
        ],
        'cvemp' => [
            ['Informa por OD y OI la presencia del complejo P1-N1 a la intensidad máxima', 1],
            ['Informa las latencias de P1 y N1 de cada oído', 1],
            ['Informa la amplitud de cada oído y el porcentaje de asimetría con su significancia (35 % o más es significativo)', 2],
            ['Informa el umbral del potencial de cada oído', 1],
            ['Concluye correctamente sobre la función sacular (vía vestíbulo-cólica) de cada oído', 2],
        ],
        'ovemp' => [
            ['Informa por OD y OI la presencia del complejo N1-P1 (registro contralateral)', 1],
            ['Informa las latencias de N1 y P1 de cada oído', 1],
            ['Informa la amplitud de cada oído y el porcentaje de asimetría con su significancia (33 % o más es significativo)', 2],
            ['Concluye correctamente sobre la función utricular (vía vestíbulo-ocular) de cada oído', 2],
        ],
        'otro' => [
            ['Describe por OD y OI lo que se registró, con sus valores', 2],
            ['Interpreta los hallazgos contra lo esperado', 2],
            ['Concluye correctamente para cada oído', 2],
        ],
    ];

    public const PROMPT_CONCLUSION = <<<'TXT'
Eres el corrector de la estación de conclusión de una evaluación práctica
tipo OSCE de Tecnología Médica, mención Otorrinolaringología
(electrofisiología). El estudiante vio las curvas de un paciente, marcó las
ondas y escribió el informe (hallazgos y conclusión). Corriges ese informe.

Tienes:
- CRITERIOS numerados, cada uno con su puntaje máximo.
- CONCLUSIÓN ESPERADA que escribió el docente: es la referencia.
- DATOS REALES del caso, que el estudiante no veía: si en cada curva había
  respuesta, las latencias verdaderas y el umbral real de cada oído.
- LO QUE MARCÓ el estudiante en cada curva.
- El INFORME del estudiante.

Reglas:
- Asigna a cada criterio un puntaje de 0 a su máximo, en pasos de 0,5.
- Juzga el informe contra la conclusión esperada y los datos reales. Si el
  estudiante informa un valor que coincide con lo que él mismo marcó y su
  marca era razonable, no lo castigues por diferencias pequeñas con la
  latencia verdadera (±0,3 ms) ni con el umbral (±10 dB).
- Un error de interpretación (tipo de audición equivocado, oído cambiado,
  asimetría mal calculada o mal juzgada) descuenta en el criterio que
  corresponde, no en todos.
- Acepta sinónimos, abreviaturas clínicas y redacción informal. La ortografía
  no descuenta.
- Lo que el informe no dice no se da por dicho.
- Cada comentario va al estudiante, en español de Chile, una o dos frases
  concretas y respetuosas. No digas que eres una IA.

Responde SOLO con este JSON, sin texto alrededor ni bloques de código:
{"criterios": [{"n": 1, "puntaje": <número>, "comentario": "<texto>"}, ...],
 "comentario_general": "<dos o tres frases para el estudiante>"}
TXT;

    /** Equipo de la app que abre cada examen. */
    public const MODULO_DE_EXAMEN = ['cvemp' => 'VEMP', 'ovemp' => 'VEMP'];

    /** Prueba que abre (combo "Tipo de prueba" del ABR o subtipo del VEMP). */
    public const PRUEBA_DE_EXAMEN = [
        'peatc' => 'ABR', 'aabr' => 'ABR', 'general' => 'ABR', 'ecochg' => 'ECochG',
        'latencia_media' => 'MLR', 'latencia_tardia' => 'CAEP', 'estado_estable' => 'ASSR',
        'cvemp' => 'CVEMP', 'ovemp' => 'OVEMP',
    ];

    /** Ondas a marcar: [en la intensidad mayor de cada oído, en las demás]; la primera de las demás define "hay respuesta". */
    public const ONDAS = [
        'peatc' => [['I', 'III', 'V'], ['V']],
        'cvemp' => [['p13', 'n23'], ['p13', 'n23']],
        'ovemp' => [['n10', 'p16'], ['n10', 'p16']],
    ];

    /**
     * Parámetros que se pueden evaluar: clave => [fuente, rótulo].
     * panel = lo que se ve en el panel de control; equipo = Parámetros
     * avanzados del ABR (technical). En la estación de protocolo se miran
     * en cada curva registrada (la fuente da lo mismo).
     */
    public const PARAMETROS = [
        'ABR' => [
            'test' => ['panel', 'Tipo de prueba'],
            'stim' => ['panel', 'Estímulo'],
            'pol' => ['panel', 'Polaridad'],
            'int' => ['panel', 'Intensidad (dB nHL)'],
            'rate' => ['panel', 'Tasa de estimulación (est/s)'],
            'filter_passhigh' => ['panel', 'Filtro pasa alto (Hz)'],
            'filter_down' => ['panel', 'Filtro pasa bajo (Hz)'],
            'average' => ['panel', 'Promediaciones'],
            'side' => ['panel', 'Oído'],
            'window_ms' => ['equipo', 'Ventana de análisis (ms)'],
            'gain' => ['equipo', 'Ganancia'],
            'transducer' => ['equipo', 'Transductor'],
            'artifact_reject_uv' => ['equipo', 'Rechazo de artefacto (µV)'],
        ],
        'VEMP' => [
            'transducer' => ['panel', 'Transductor'],
            'freq' => ['panel', 'Frecuencia del tone burst'],
            'pol' => ['panel', 'Polaridad'],
            'int' => ['panel', 'Intensidad (dB SPL)'],
            'rate' => ['panel', 'Tasa de estimulación (est/s)'],
            'filter_passhigh' => ['panel', 'Filtro pasa alto (Hz)'],
            'filter_down' => ['panel', 'Filtro pasa bajo (Hz)'],
            'average' => ['panel', 'Promediaciones'],
            'side' => ['panel', 'Oído'],
            'maniobra' => ['panel', 'Maniobra (contracción)'],
            'emg_ok' => ['panel', 'EMG en la banda'],
        ],
    ];

    /**
     * Configuración del Protocolo Técnico ORL 2019. PEATC: la ventana dice
     * "10 s", es 10 ms; ganancia "10k" = ×10.000; acepta cualquier estímulo.
     * VEMP: el equipo de LabSim mide en dB SPL y el protocolo dice "100 dB
     * nHL", así que la intensidad la escribe el docente; ganancia y ventana
     * no son mandos del VEMP simulado.
     */
    public const ESPERADO_PEATC = [
        'stim' => 'Click | CE-Chirp | CE-Chirp LS | NB CE-Chirp LS 500 Hz | NB CE-Chirp LS 1 kHz | NB CE-Chirp LS 2 kHz | NB CE-Chirp LS 4 kHz | Burst 500 Hz | Burst 1 kHz | Burst 2 kHz | Burst 4 kHz',
        'pol' => 'Alternada',
        'int' => '80',
        'rate' => '21.1',
        'filter_passhigh' => '100',
        'filter_down' => '3000',
        'gain' => '10000',
        'window_ms' => '10',
        'transducer' => 'insert_earphone',
    ];
    public const ESPERADO = [
        'peatc' => self::ESPERADO_PEATC,
        'cvemp' => ['transducer' => 'Inserto (vía aérea)', 'freq' => '500 Hz', 'pol' => 'Rarefacción', 'rate' => '5.1',
                    'filter_passhigh' => '3', 'filter_down' => '1500', 'maniobra' => 'Rotación cefálica sostenida'],
        'ovemp' => ['transducer' => 'Inserto (vía aérea)', 'freq' => '1000 Hz | 500 Hz', 'pol' => 'Rarefacción', 'rate' => '5.1',
                    'filter_passhigh' => '1', 'filter_down' => '1000', 'maniobra' => 'Mirada superior ~30°'],
    ];
    /** En la estación de protocolo, lo que se pide a cada curva (difiere de la configuración final). */
    public const ESPERADO_CURVAS = [
        'peatc' => ['pol' => 'Alternada', 'rate' => '21.1 | 81.1', 'filter_passhigh' => '100', 'filter_down' => '3000',
                    'transducer' => 'insert_earphone', 'window_ms' => '10'],
        'cvemp' => ['transducer' => 'Inserto (vía aérea)', 'freq' => '500 Hz', 'pol' => 'Rarefacción', 'rate' => '5.1',
                    'filter_passhigh' => '3', 'filter_down' => '1500', 'emg_ok' => 'sí'],
        'ovemp' => ['transducer' => 'Inserto (vía aérea)', 'freq' => '1000 Hz | 500 Hz', 'pol' => 'Rarefacción', 'rate' => '5.1',
                    'filter_passhigh' => '1', 'filter_down' => '1000', 'emg_ok' => 'sí'],
    ];

    /** Estímulos chirp (bonificación por acercarse al umbral con ellos). */
    public const CHIRPS = 'CE-Chirp | CE-Chirp LS | NB CE-Chirp LS 500 Hz | NB CE-Chirp LS 1 kHz | NB CE-Chirp LS 2 kHz | NB CE-Chirp LS 4 kHz';

    /**
     * Reglas de estrategia: clave => [rótulo, qué se escribe en "valor"].
     * El texto del criterio sale del rótulo con el valor.
     */
    public const ESTRATEGIA = [
        'inicio' => ['Parte cada oído en {v} dB', 'nivel o rango'],
        'baja' => ['Con respuesta, baja de {v} en {v} dB', 'paso en dB'],
        'sube' => ['Sin respuesta, sube de {v} en {v} dB', 'paso en dB'],
        'sube_max' => ['Sin respuesta al partir, sube a {v} dB', 'rango'],
        'replica_max' => ['Replica la curva en la intensidad máxima', ''],
        'replica_umbral' => ['Replica la curva en el umbral', ''],
        'ambos' => ['Evalúa ambos oídos', ''],
        'umbral' => ['Umbral encontrado a ±{v} dB del real', 'tolerancia dB'],
        'umbral_chirp' => ['Se acerca al umbral con chirp y lo encuentra (±{v} dB)', 'tolerancia dB'],
        'alguna_tasa' => ['Registra alguna curva a tasa {v} (sospecha de neuropatía)', 'tasa'],
    ];

    /** Por examen: clave => [activa, valor, puntos, bonificación]. */
    public const ESTRATEGIA_BASE = [
        'peatc' => [
            'inicio' => [true, '80', 1, false], 'baja' => [true, '20', 1, false], 'sube' => [true, '10', 1, false],
            'sube_max' => [true, '90–100', 1, false], 'replica_max' => [true, '', 1, false],
            'replica_umbral' => [true, '', 1, false], 'ambos' => [true, '', 1, false], 'umbral' => [true, '10', 2, false],
            'umbral_chirp' => [true, '10', 1, true], 'alguna_tasa' => [false, '81.1', 1, false],
        ],
        'cvemp' => [
            'inicio' => [false, '', 1, false], 'baja' => [true, '10', 1, false], 'sube' => [true, '5', 1, false],
            'replica_max' => [true, '', 1, false], 'replica_umbral' => [false, '', 1, false],
            'ambos' => [true, '', 1, false], 'umbral' => [true, '10', 2, false],
        ],
        'ovemp' => [
            'inicio' => [false, '', 1, false], 'replica_max' => [true, '', 1, false], 'ambos' => [true, '', 1, false],
        ],
        'otro' => [
            'inicio' => [false, '', 1, false], 'baja' => [false, '', 1, false], 'sube' => [false, '', 1, false],
            'replica_max' => [true, '', 1, false], 'ambos' => [true, '', 1, false], 'umbral' => [false, '10', 2, false],
        ],
    ];

    /** Curvas que la app registra sola para la estación de marcaje. */
    public const CURVAS_BASE = "OD 80\nOD 60\nOD 40\nOD 20\nOI 80\nOI 60\nOI 40\nOI 20";

    public static function esApp(string $tipo): bool
    {
        return in_array($tipo, self::TIPOS, true);
    }

    public static function modulo(string $examen): string
    {
        return self::MODULO_DE_EXAMEN[$examen] ?? 'ABR';
    }

    public static function parametros(string $examen): array
    {
        return self::PARAMETROS[self::modulo($examen)];
    }

    /** [ondas en la intensidad mayor, ondas en las demás] del examen. */
    public static function ondas(string $examen): array
    {
        return self::ONDAS[$examen] ?? self::ONDAS['peatc'];
    }

    public static function config(array $est): array
    {
        return json_decode((string) ($est['config'] ?? '{}'), true) ?: [];
    }

    private static function guardarConfig(int $estacionId, array $cfg): void
    {
        Db::reintentar(static function () use ($estacionId, $cfg): void {
            Db::get()->prepare('UPDATE osce_estacion SET config = ? WHERE id = ?')
                ->execute([json_encode($cfg, JSON_UNESCAPED_UNICODE), $estacionId]);
        });
    }

    // -- Código de la estación -----------------------------------------------

    /** Código corto que se escribe en el PC de la estación (se crea la primera vez). */
    public static function codigoEstacion(int $estacionId): string
    {
        $est = Osce::estacion($estacionId);
        $cfg = self::config($est ?? []);
        if (!empty($cfg['app_codigo'])) {
            return (string) $cfg['app_codigo'];
        }
        do {
            $codigo = Osce::nuevoCodigo();
        } while (self::estacionPorCodigo($codigo) !== null);
        $cfg['app_codigo'] = $codigo;
        self::guardarConfig($estacionId, $cfg);
        return $codigo;
    }

    public static function estacionPorCodigo(string $codigo): ?array
    {
        Osce::migrar();
        $codigo = Osce::normalizarCodigo($codigo);
        if (!preg_match('/^[2-9A-HJKMNP-Z]{3}-[2-9A-HJKMNP-Z]{3}$/', $codigo)) {
            return null;
        }
        $stmt = Db::get()->prepare('SELECT * FROM osce_estacion WHERE config LIKE ?');
        $stmt->execute(['%"app_codigo":"' . $codigo . '"%']);
        $row = $stmt->fetch();
        $stmt->closeCursor();
        return $row ?: null;
    }

    // -- Contenido de la estación (editor) -----------------------------------

    /** Casos con datos para ese equipo (ABR o VEMP), para elegir el de la estación. */
    public static function casos(string $modulo): array
    {
        $stmt = Db::get()->query(
            "SELECT c.id, c.data, p.nombre, p.apellido FROM cases c LEFT JOIN patients p ON p.id = c.patient_id
              WHERE c.archived_at IS NULL ORDER BY p.apellido, p.nombre, c.id"
        );
        $out = [];
        foreach ($stmt->fetchAll() as $c) {
            $data = json_decode((string) $c['data'], true) ?: [];
            $sec = $data[$modulo] ?? [];
            if (empty($sec['OD']) && empty($sec['OI'])) {
                continue;
            }
            $tipoOd = (string) ($sec['OD']['type'] ?? '');
            $tipoOi = (string) ($sec['OI']['type'] ?? '');
            $nombre = trim(($c['nombre'] ?? '') . ' ' . ($c['apellido'] ?? ''));
            $out[] = ['id' => (string) $c['id'], 'rotulo' => ($nombre !== '' ? $nombre : 'Caso ' . $c['id'])
                . ' · OD ' . ($tipoOd ?: '—') . ' / OI ' . ($tipoOi ?: '—')];
        }
        return $out;
    }

    /** Texto de un criterio de estrategia con su valor. */
    public static function textoRegla(string $clave, string $valor): string
    {
        $rotulo = self::ESTRATEGIA[$clave][0] ?? $clave;
        return str_replace('{v}', $valor !== '' ? $valor : '…', $rotulo);
    }

    /** Las reglas de estrategia con que parte la estación (las guardadas o las del examen). */
    public static function estrategia(array $est): array
    {
        $cfg = self::config($est);
        if (isset($cfg['estrategia']) && is_array($cfg['estrategia'])) {
            return $cfg['estrategia'];
        }
        $base = self::ESTRATEGIA_BASE[$est['examen']] ?? self::ESTRATEGIA_BASE['otro'];
        $out = [];
        foreach ($base as $clave => [$activa, $valor, $pts, $bonus]) {
            $out[$clave] = ['activa' => $activa, 'valor' => $valor, 'puntos' => $pts, 'bonus' => $bonus];
        }
        return $out;
    }

    /**
     * Guarda el contenido de una estación de la app y rehace sus ítems.
     * config_equipo: un ítem por parámetro con esperado. marcaje: uno por
     * onda y curva. protocolo: parámetros en cada curva + estrategia.
     */
    public static function guardarContenido(array $est, array $in): void
    {
        $cfg = self::config($est);
        $caseId = trim((string) ($in['case_id'] ?? ''));
        if ($caseId === '') {
            throw new InvalidArgumentException('Elige el caso del paciente de la estación.');
        }
        $examen = (string) $est['examen'];
        $cfg['case_id'] = $caseId;
        $cfg['prueba'] = self::PRUEBA_DE_EXAMEN[$examen] ?? 'ABR';
        $items = [];
        $num = static fn ($v, float $def): float => is_numeric(str_replace(',', '.', (string) $v)) ? (float) str_replace(',', '.', (string) $v) : $def;
        $params = static function (string $regla) use ($in, $examen, $num): array {
            $out = [];
            $esperado = [];
            foreach (self::parametros($examen) as $clave => [$fuente, $rotulo]) {
                $valor = trim((string) ($in['esperado'][$clave] ?? ''));
                if ($valor === '' || ($regla === 'param' && $clave === 'emg_ok')) {
                    continue;
                }
                $esperado[$clave] = $valor;
                $out[] = ['texto' => $regla === 'curvas_param' ? "{$rotulo} en cada curva" : $rotulo,
                          'puntaje' => $num($in['puntos'][$clave] ?? 1, 1.0) ?: 1.0,
                          'critico' => !empty($in['critico'][$clave]),
                          'config' => ['regla' => $regla, 'fuente' => $fuente, 'clave' => $clave, 'esperado' => $valor]];
            }
            return [$out, $esperado];
        };
        if ($est['tipo'] === 'config_equipo') {
            [$items, $cfg['esperado']] = $params('param');
            if (!$items) {
                throw new InvalidArgumentException('Indica al menos un parámetro esperado.');
            }
        } elseif ($est['tipo'] === 'marcaje') {
            $curvas = self::leerCurvas((string) ($in['curvas'] ?? ''));
            if (!$curvas) {
                throw new InvalidArgumentException('Indica las curvas a registrar: una por línea, como "OD 80".');
            }
            $tol = $num($in['tol_ms'] ?? '0.2', 0.2);
            if ($tol <= 0 || $tol > 2) {
                throw new InvalidArgumentException('Tolerancia: entre 0,05 y 2 ms.');
            }
            $cfg['curvas'] = $curvas;
            $cfg['tol_ms'] = $tol;
            [$ondasMax, $ondasResto] = self::ondas($examen);
            $maxPorLado = [];
            foreach ($curvas as [$lado, $int]) {
                $maxPorLado[$lado] = max($maxPorLado[$lado] ?? -100, $int);
            }
            foreach ($curvas as [$lado, $int]) {
                foreach ($int === $maxPorLado[$lado] ? $ondasMax : $ondasResto as $onda) {
                    $items[] = ['texto' => "{$lado} {$int} dB: onda {$onda}", 'puntaje' => 1.0, 'critico' => false,
                                'config' => ['regla' => 'marca', 'lado' => $lado, 'int' => $int, 'onda' => $onda, 'tol_ms' => $tol]];
                }
            }
        } elseif ($est['tipo'] === 'conclusion') {
            $curvas = self::leerCurvas((string) ($in['curvas'] ?? ''));
            if (!$curvas) {
                throw new InvalidArgumentException('Indica las curvas a registrar: una por línea, como "OD 80".');
            }
            $esperada = trim((string) ($in['conclusion_esperada'] ?? ''));
            if ($esperada === '') {
                throw new InvalidArgumentException('Escribe la conclusión esperada: es la referencia con que corrige la IA.');
            }
            $criterios = self::leerCriterios((string) ($in['criterios'] ?? ''));
            if (!$criterios) {
                throw new InvalidArgumentException('Indica al menos un criterio: "texto | puntos" por línea.');
            }
            $cfg['curvas'] = $curvas;
            $cfg['conclusion_esperada'] = mb_substr($esperada, 0, 4000);
            foreach ($criterios as $k => [$texto, $pts]) {
                $items[] = ['texto' => $texto, 'puntaje' => $pts, 'critico' => false,
                            'config' => ['regla' => 'ia', 'n' => $k + 1]];
            }
        } else {
            $onda = trim((string) ($in['onda'] ?? ''));
            if ($onda === '') {
                throw new InvalidArgumentException('Indica la onda que define que hay respuesta (V en el PEATC).');
            }
            $cfg['onda'] = $onda;
            [$items, $cfg['esperado_curvas']] = $params('curvas_param');
            $estrategia = [];
            foreach (self::ESTRATEGIA as $clave => [$rotulo, $pide]) {
                $r = $in['estrategia'][$clave] ?? [];
                $activa = !empty($r['activa']);
                $valor = trim((string) ($r['valor'] ?? ''));
                $estrategia[$clave] = ['activa' => $activa, 'valor' => $valor,
                                       'puntos' => $num($r['puntos'] ?? 1, 1.0) ?: 1.0, 'bonus' => !empty($r['bonus'])];
                if (!$activa) {
                    continue;
                }
                if ($pide !== '' && $valor === '') {
                    throw new InvalidArgumentException('"' . self::textoRegla($clave, '…') . '" necesita su valor (' . $pide . ').');
                }
                $items[] = ['texto' => self::textoRegla($clave, $valor) . ($estrategia[$clave]['bonus'] ? ' (bonificación)' : ''),
                            'puntaje' => $estrategia[$clave]['puntos'], 'critico' => false,
                            'config' => ['regla' => $clave, 'valor' => $valor, 'onda' => $onda,
                                         'bonus' => $estrategia[$clave]['bonus']]];
            }
            $cfg['estrategia'] = $estrategia;
            if (!$items) {
                throw new InvalidArgumentException('Activa al menos un criterio.');
            }
        }
        $estId = (int) $est['id'];
        Db::reintentar(static function () use ($estId, $cfg, $items): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $pdo->prepare('UPDATE osce_estacion SET config = ? WHERE id = ?')
                ->execute([json_encode($cfg, JSON_UNESCAPED_UNICODE), $estId]);
            $pdo->prepare('DELETE FROM osce_item WHERE estacion_id = ?')->execute([$estId]);
            $ins = $pdo->prepare("INSERT INTO osce_item (estacion_id, orden, texto, puntaje, critico, tipo, config) VALUES (?, ?, ?, ?, ?, 'auto', ?)");
            foreach ($items as $k => $it) {
                $ins->execute([$estId, $k + 1, $it['texto'], $it['puntaje'], $it['critico'] ? 1 : 0,
                               json_encode($it['config'], JSON_UNESCAPED_UNICODE)]);
            }
            $pdo->commit();
        });
    }

    /** "texto | puntos" por línea → [[texto, puntos], ...] (sin puntos = 1). */
    public static function leerCriterios(string $texto): array
    {
        $out = [];
        foreach (preg_split('/\r?\n/', $texto) ?: [] as $linea) {
            $linea = trim($linea);
            if ($linea === '') {
                continue;
            }
            $pts = 1.0;
            if (preg_match('/^(.*)\|\s*([\d.,]+)\s*$/u', $linea, $m)) {
                $linea = trim($m[1]);
                $pts = (float) str_replace(',', '.', $m[2]);
            }
            if ($linea !== '' && $pts > 0 && $pts <= 100) {
                $out[] = [mb_substr($linea, 0, 400), $pts];
            }
        }
        return array_slice($out, 0, 20);
    }

    public static function criteriosTexto(array $criterios): string
    {
        return implode("\n", array_map(static fn ($c) => $c[0] . ' | ' . rtrim(rtrim(number_format((float) $c[1], 1, '.', ''), '0'), '.'), $criterios));
    }

    /** "OD 80" por línea → [["OD", 80], ...] (sin repetidas, en el orden dado). */
    public static function leerCurvas(string $texto): array
    {
        $out = [];
        foreach (preg_split('/[\r\n,;]+/', $texto) ?: [] as $linea) {
            if (!preg_match('/^\s*(OD|OI)\s*(-?\d{1,3})\s*$/i', $linea, $m)) {
                continue;
            }
            $par = [strtoupper($m[1]), (int) $m[2]];
            if ($par[1] < -10 || $par[1] > 130 || in_array($par, $out, true)) {
                continue;
            }
            $out[] = $par;
        }
        return array_slice($out, 0, 16);
    }

    public static function curvasTexto(array $curvas): string
    {
        return implode("\n", array_map(static fn ($c) => $c[0] . ' ' . $c[1], $curvas));
    }

    // -- Corrección (pura) -----------------------------------------------------

    /** ¿El valor cumple lo esperado? "a | b" = cualquiera, "x–y" o "x-y" = rango, si no igual. */
    public static function cumpleEsperado($valor, string $esperado): bool
    {
        if ($valor === null || $valor === '') {
            return false;
        }
        if (is_bool($valor)) {
            $valor = $valor ? 'sí' : 'no';
        }
        $v = trim((string) $valor);
        $num = static fn (string $s): ?float => is_numeric(str_replace(',', '.', trim($s))) ? (float) str_replace(',', '.', trim($s)) : null;
        if (strpos($esperado, '|') !== false) {
            foreach (explode('|', $esperado) as $opcion) {
                if (self::cumpleEsperado($v, trim($opcion))) {
                    return true;
                }
            }
            return false;
        }
        if (preg_match('/^\s*(-?[\d.,]+)\s*[–-]\s*(-?[\d.,]+)\s*$/u', $esperado, $m)) {
            $x = $num($v);
            $a = $num($m[1]);
            $b = $num($m[2]);
            return $x !== null && $a !== null && $b !== null && $x >= min($a, $b) - 1e-6 && $x <= max($a, $b) + 1e-6;
        }
        $x = $num($v);
        $e = $num($esperado);
        if ($x !== null && $e !== null) {
            return abs($x - $e) < 0.051;
        }
        return mb_strtolower($v) === mb_strtolower(trim($esperado));
    }

    /** Las curvas de la entrega, en orden (formato común de la app). */
    private static function curvas(array $payload): array
    {
        return array_values(array_filter($payload['curvas'] ?? [], 'is_array'));
    }

    /** Curva con ese lado e intensidad (la primera registrada). */
    private static function curvaDe(array $payload, string $lado, int $int): ?array
    {
        foreach (self::curvas($payload) as $c) {
            if (($c['side'] ?? '') === $lado && (int) round((float) ($c['int'] ?? -999)) === $int) {
                return $c;
            }
        }
        return null;
    }

    /** Las curvas de cada oído, en el orden en que se registraron. */
    private static function porOido(array $payload): array
    {
        $out = ['OD' => [], 'OI' => []];
        foreach (self::curvas($payload) as $c) {
            $lado = (string) ($c['side'] ?? '');
            if (isset($out[$lado])) {
                $out[$lado][] = $c;
            }
        }
        return $out;
    }

    private static function respondio(array $c, string $onda): bool
    {
        $v = $c['marcas'][$onda] ?? null;
        return is_numeric($v);
    }

    private static function nivel(array $c): float
    {
        return (float) ($c['int'] ?? 0);
    }

    /** Umbral que encontró el alumno en un oído: la curva de menor intensidad con respuesta. */
    private static function curvaUmbral(array $curvas, string $onda, ?string $estimulos = null): ?array
    {
        $mejor = null;
        foreach ($curvas as $c) {
            if (!self::respondio($c, $onda)) {
                continue;
            }
            if ($estimulos !== null && !self::cumpleEsperado($c['stim'] ?? '', $estimulos)) {
                continue;
            }
            if ($mejor === null || self::nivel($c) < self::nivel($mejor)) {
                $mejor = $c;
            }
        }
        return $mejor;
    }

    private static function db(float $x): string
    {
        return rtrim(rtrim(number_format($x, 1, ',', ''), '0'), ',');
    }

    /** Resultado de un criterio: fracción cumplida (0..1) o null si no aplica. */
    private static function resultado(?float $fraccion, string $alumno, string $esperado, float $pts): array
    {
        if ($fraccion === null) {
            return ['puntaje' => $pts, 'ok' => true, 'alumno' => $alumno ?: 'no aplica', 'esperado' => $esperado, 'fraccion' => null];
        }
        $fraccion = max(0.0, min(1.0, $fraccion));
        return ['puntaje' => round($pts * $fraccion, 2), 'ok' => $fraccion >= 0.999, 'alumno' => $alumno,
                'esperado' => $esperado, 'fraccion' => $fraccion];
    }

    /**
     * Evalúa un ítem automático contra la entrega.
     *
     * @return array{puntaje: float, ok: bool, alumno: string, esperado: string}
     */
    public static function evaluarItem(array $item, array $payload): array
    {
        $r = $item['cfg'] ?? (json_decode((string) ($item['config'] ?? '{}'), true) ?: []);
        $pts = (float) $item['puntaje'];
        $regla = (string) ($r['regla'] ?? '');

        if ($regla === 'param') {
            $fuente = $r['fuente'] === 'equipo'
                ? ($payload['equipo'] ?? ($payload['abr']['equipo'] ?? []))
                : ($payload['panel'] ?? []);
            $valor = $fuente[$r['clave']] ?? null;
            $ok = self::cumpleEsperado($valor, (string) $r['esperado']);
            return ['puntaje' => $ok ? $pts : 0.0, 'ok' => $ok,
                    'alumno' => $valor === null ? '—' : self::mostrar($r['clave'], $valor),
                    'esperado' => self::mostrarEsperado($r['clave'], (string) $r['esperado'])];
        }

        if ($regla === 'curvas_param') {
            $curvas = self::curvas($payload);
            if (!$curvas) {
                return self::resultado(0.0, 'sin curvas', self::mostrarEsperado($r['clave'], (string) $r['esperado']), $pts);
            }
            $bien = 0;
            $malos = [];
            foreach ($curvas as $c) {
                if (self::cumpleEsperado($c[$r['clave']] ?? null, (string) $r['esperado'])) {
                    $bien++;
                } elseif (count($malos) < 3) {
                    $malos[] = self::mostrar($r['clave'], $c[$r['clave']] ?? '—');
                }
            }
            return self::resultado($bien / count($curvas), "{$bien} de " . count($curvas) . ' curvas'
                . ($malos ? ' (también ' . implode(', ', array_unique($malos)) . ')' : ''),
                self::mostrarEsperado($r['clave'], (string) $r['esperado']), $pts);
        }

        if ($regla === 'marca') {
            $curva = self::curvaDe($payload, (string) $r['lado'], (int) $r['int']);
            if ($curva === null) {
                return ['puntaje' => 0.0, 'ok' => false, 'alumno' => 'sin curva', 'esperado' => '—'];
            }
            $verdad = $payload['verdad'][$curva['nombre'] ?? ''] ?? null;
            $onda = (string) $r['onda'];
            $lat = $verdad['waves'][$onda]['lat'] ?? null;
            $existe = $verdad !== null && !empty($verdad['visible']) && $lat !== null;
            $marca = $curva['marcas'][$onda] ?? null;
            $marca = is_numeric($marca) ? (float) $marca : null;
            $tol = (float) ($r['tol_ms'] ?? 0.2);
            $ok = $existe ? ($marca !== null && abs($marca - (float) $lat) <= $tol + 1e-9) : $marca === null;
            $fmt = static fn (?float $x): string => $x === null ? 'sin marca' : number_format($x, 2, ',', '') . ' ms';
            return ['puntaje' => $ok ? $pts : 0.0, 'ok' => $ok, 'alumno' => $fmt($marca),
                    'esperado' => $existe ? number_format((float) $lat, 2, ',', '') . ' ms ± ' . str_replace('.', ',', (string) $tol)
                                          : 'sin onda ' . $onda . ' (no marcar)'];
        }

        if ($regla === 'ia') {
            return ['puntaje' => null, 'ok' => false, 'pendiente' => true, 'ia' => true,
                    'alumno' => 'pendiente de corrección', 'esperado' => 'según la conclusión esperada'];
        }

        return self::evaluarEstrategia($regla, $r, $payload, $pts);
    }

    /** Criterios de estrategia (estación de protocolo). */
    private static function evaluarEstrategia(string $regla, array $r, array $payload, float $pts): array
    {
        $onda = (string) ($r['onda'] ?? 'V');
        $valor = (string) ($r['valor'] ?? '');
        $oidos = self::porOido($payload);
        $esperado = self::textoRegla($regla, $valor);
        $conCurvas = array_filter($oidos, static fn ($cs) => $cs !== []);

        switch ($regla) {
            case 'ambos':
                $n = count($conCurvas);
                return self::resultado($n / 2, $n === 2 ? 'OD y OI' : ($n === 1 ? 'solo ' . array_keys($conCurvas)[0] : 'ninguno'), 'OD y OI', $pts);

            case 'inicio':
                $bien = 0;
                $txt = [];
                foreach ($oidos as $lado => $cs) {
                    if (!$cs) {
                        continue;
                    }
                    $primero = self::nivel($cs[0]);
                    $txt[] = "{$lado} " . self::db($primero);
                    $bien += self::cumpleEsperado($primero, $valor) ? 1 : 0;
                }
                return self::resultado($bien / 2, implode(' · ', $txt) ?: 'sin curvas', $valor . ' dB en cada oído', $pts);

            case 'baja':
            case 'sube':
                $paso = (float) str_replace(',', '.', $valor);
                $fracciones = [];
                $malos = [];
                foreach ($oidos as $lado => $cs) {
                    $total = 0;
                    $bien = 0;
                    for ($i = 1; $i < count($cs); $i++) {
                        $antes = $cs[$i - 1];
                        $ahora = $cs[$i];
                        $resp = self::respondio($antes, $onda);
                        $delta = self::nivel($ahora) - self::nivel($antes);
                        if ($regla === 'baja' && $resp && $delta < 0) {
                            $total++;
                            $ok = abs(-$delta - $paso) < 0.01;
                        } elseif ($regla === 'sube' && !$resp && $delta > 0) {
                            $total++;
                            $ok = abs($delta - $paso) < 0.01;
                        } else {
                            continue;
                        }
                        $bien += $ok ? 1 : 0;
                        if (!$ok) {
                            $malos[] = "{$lado} " . self::db(self::nivel($antes)) . '→' . self::db(self::nivel($ahora));
                        }
                    }
                    $conRespuesta = array_filter($cs, static fn ($c) => self::respondio($c, $onda));
                    if ($total > 0) {
                        $fracciones[] = $bien / $total;
                    } elseif ($regla === 'baja' && $conRespuesta) {
                        // Vio respuesta y nunca bajó: no buscó el umbral.
                        $fracciones[] = 0.0;
                        $malos[] = "{$lado} no bajó";
                    }
                }
                if (!$fracciones) {
                    return self::resultado(null, 'no aplica', $esperado, $pts);
                }
                return self::resultado(array_sum($fracciones) / count($fracciones),
                    $malos ? 'fuera de paso: ' . implode(', ', array_slice($malos, 0, 4)) : 'siempre de ' . self::db($paso), $esperado, $pts);

            case 'sube_max':
                $aplica = 0;
                $bien = 0;
                $txt = [];
                foreach ($oidos as $lado => $cs) {
                    if (!$cs || self::respondio($cs[0], $onda)) {
                        continue;
                    }
                    $aplica++;
                    $sube = false;
                    foreach (array_slice($cs, 1) as $c) {
                        $sube = $sube || self::cumpleEsperado(self::nivel($c), $valor);
                    }
                    $bien += $sube ? 1 : 0;
                    $txt[] = $lado . ($sube ? ' subió' : ' no subió');
                }
                return self::resultado($aplica ? $bien / $aplica : null, implode(' · ', $txt), $esperado, $pts);

            case 'replica_max':
            case 'replica_umbral':
                $aplica = 0;
                $bien = 0;
                $txt = [];
                foreach ($oidos as $lado => $cs) {
                    if (!$cs) {
                        $aplica++;
                        $txt[] = "{$lado} sin curvas";
                        continue;
                    }
                    if ($regla === 'replica_max') {
                        $nivel = max(array_map([self::class, 'nivel'], $cs));
                    } else {
                        $u = self::curvaUmbral($cs, $onda);
                        if ($u === null) {
                            continue;   // sin respuesta en ese oído: no hay umbral que replicar
                        }
                        $nivel = self::nivel($u);
                    }
                    $aplica++;
                    $n = count(array_filter($cs, static fn ($c) => abs(self::nivel($c) - $nivel) < 0.01));
                    $bien += $n >= 2 ? 1 : 0;
                    $txt[] = "{$lado} " . self::db($nivel) . " dB: {$n} curva" . ($n === 1 ? '' : 's');
                }
                return self::resultado($aplica ? $bien / $aplica : null, implode(' · ', $txt), $esperado, $pts);

            case 'umbral':
            case 'umbral_chirp':
                $tol = (float) str_replace(',', '.', $valor ?: '10');
                $filtro = $regla === 'umbral_chirp' ? self::CHIRPS : null;
                $bien = 0;
                $txt = [];
                foreach ($oidos as $lado => $cs) {
                    if (!$cs) {
                        $txt[] = "{$lado} sin curvas";
                        continue;
                    }
                    $u = self::curvaUmbral($cs, $onda, $filtro);
                    if ($u === null) {
                        if ($filtro !== null) {
                            $txt[] = "{$lado} sin umbral con chirp";
                            continue;
                        }
                        // Dice que no hay respuesta: bien si de verdad no la hay en lo más alto que registró.
                        $mayor = $cs[0];
                        foreach ($cs as $c) {
                            if (self::nivel($c) > self::nivel($mayor)) {
                                $mayor = $c;
                            }
                        }
                        $v = $payload['verdad'][$mayor['nombre'] ?? ''] ?? null;
                        $ok = $v !== null && empty($v['visible']);
                        $bien += $ok ? 1 : 0;
                        $txt[] = "{$lado} sin respuesta hasta " . self::db(self::nivel($mayor)) . ($ok ? '' : ' (sí había)');
                        continue;
                    }
                    $real = $payload['verdad'][$u['nombre'] ?? '']['threshold'] ?? null;
                    $ok = $real !== null && abs(self::nivel($u) - (float) $real) <= $tol + 1e-9;
                    $bien += $ok ? 1 : 0;
                    $txt[] = "{$lado} " . self::db(self::nivel($u)) . ($real !== null ? ' (real ' . self::db((float) $real) . ')' : '');
                }
                return self::resultado($bien / 2, implode(' · ', $txt), $esperado, $pts);

            case 'alguna_tasa':
                foreach (self::curvas($payload) as $c) {
                    if (self::cumpleEsperado($c['rate'] ?? null, $valor)) {
                        return self::resultado(1.0, 'sí (' . ($c['side'] ?? '') . ' ' . self::db(self::nivel($c)) . ' dB)', $esperado, $pts);
                    }
                }
                return self::resultado(0.0, 'ninguna', $esperado, $pts);
        }
        return ['puntaje' => 0.0, 'ok' => false, 'alumno' => '—', 'esperado' => '—'];
    }

    private const ROTULOS_VALOR = [
        'insert_earphone' => 'Fono de inserción', 'TDH39_headphone' => 'Fono de copa (TDH-39)', 'bone_vibrator' => 'Vibrador óseo',
    ];

    private static function mostrar(string $clave, $valor): string
    {
        if ($clave === 'gain' && is_numeric($valor)) {
            return '×' . number_format((float) $valor, 0, ',', '.');
        }
        if (is_bool($valor)) {
            return $valor ? 'sí' : 'no';
        }
        if (is_numeric($valor)) {
            return rtrim(rtrim(number_format((float) $valor, 2, ',', ''), '0'), ',');
        }
        return self::ROTULOS_VALOR[(string) $valor] ?? (string) $valor;
    }

    private static function mostrarEsperado(string $clave, string $esperado): string
    {
        $partes = array_map('trim', explode('|', $esperado));
        if (count($partes) > 4) {
            return 'cualquiera de ' . count($partes) . ' opciones';
        }
        return implode(' o ', array_map(static fn ($p) => preg_match('/[–-]/u', $p) && !is_numeric($p) ? str_replace('-', '–', $p) : self::mostrar($clave, $p), $partes));
    }

    /**
     * Totales de una estación: las bonificaciones suman pero no entran en
     * el máximo, y el total no pasa del máximo.
     *
     * @param array<int, array{item: array, puntaje: float}> $filas
     */
    public static function totales(array $filas): array
    {
        $total = 0.0;
        $max = 0.0;
        $critico = false;
        foreach ($filas as $f) {
            $it = $f['item'];
            $bonus = !empty(($it['cfg'] ?? [])['bonus']);
            $total += (float) ($f['puntaje'] ?? 0);
            if (!$bonus) {
                $max += (float) $it['puntaje'];
            }
            $critico = $critico || ((int) $it['critico'] === 1 && $f['puntaje'] !== null && (float) $f['puntaje'] <= 0.0);
        }
        return ['puntaje' => round(min($total, $max), 2), 'puntaje_max' => round($max, 2), 'critico_fallado' => $critico];
    }

    // -- Entrega ---------------------------------------------------------------

    /**
     * Guarda la entrega de la app (registro completo) y la corrige.
     * Al volver a corregir (docente), lo que el docente puso a mano se respeta.
     */
    public static function entregar(int $estacionId, int $participanteId, array $payload): array
    {
        $json = json_encode($payload, JSON_UNESCAPED_UNICODE);
        if ($json === false || strlen($json) > 6000000) {
            throw new InvalidArgumentException('Entrega demasiado grande o ilegible.');
        }
        Db::reintentar(static function () use ($estacionId, $participanteId, $json): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $pdo->prepare(
                "INSERT INTO osce_entrega (participante_id, estacion_id) VALUES (?, ?)
                 ON CONFLICT (participante_id, estacion_id) DO NOTHING"
            )->execute([$participanteId, $estacionId]);
            $stmt = $pdo->prepare('SELECT id, estado FROM osce_entrega WHERE participante_id = ? AND estacion_id = ?');
            $stmt->execute([$participanteId, $estacionId]);
            $en = $stmt->fetch();
            $stmt->closeCursor();
            if ($en['estado'] === 'enviada') {
                $pdo->rollBack();
                throw new InvalidArgumentException('Ya entregaste esta estación.');
            }
            $pdo->prepare('DELETE FROM osce_resultado WHERE entrega_id = ? AND item_id IS NULL AND pregunta_id IS NULL')->execute([(int) $en['id']]);
            $pdo->prepare("INSERT INTO osce_resultado (entrega_id, valor, fuente) VALUES (?, ?, 'registro')")->execute([(int) $en['id'], $json]);
            $pdo->prepare("UPDATE osce_entrega SET estado = 'enviada', enviada_at = CURRENT_TIMESTAMP WHERE id = ?")->execute([(int) $en['id']]);
            $pdo->commit();
        });
        return self::corregir($estacionId, $participanteId);
    }

    /** La entrega guardada (registro) de un alumno, o null. */
    public static function registro(int $estacionId, int $participanteId): ?array
    {
        $stmt = Db::get()->prepare(
            "SELECT r.valor FROM osce_resultado r JOIN osce_entrega e ON e.id = r.entrega_id
              WHERE e.estacion_id = ? AND e.participante_id = ? AND r.fuente = 'registro'"
        );
        $stmt->execute([$estacionId, $participanteId]);
        $v = $stmt->fetchColumn();
        $stmt->closeCursor();
        return $v === false ? null : (json_decode((string) $v, true) ?: []);
    }

    private static function entregaId(int $estacionId, int $participanteId): int
    {
        $stmt = Db::get()->prepare('SELECT id FROM osce_entrega WHERE estacion_id = ? AND participante_id = ?');
        $stmt->execute([$estacionId, $participanteId]);
        $id = (int) $stmt->fetchColumn();
        $stmt->closeCursor();
        return $id;
    }

    /** Corrige (o vuelve a corregir) una entrega con los ítems actuales. */
    public static function corregir(int $estacionId, int $participanteId): array
    {
        $payload = self::registro($estacionId, $participanteId) ?? [];
        $items = OscePauta::items($estacionId);
        $pdo = Db::get();
        $entregaId = self::entregaId($estacionId, $participanteId);
        $stmt = $pdo->prepare("SELECT item_id, puntaje, comentario, fuente, valor FROM osce_resultado WHERE entrega_id = ? AND item_id IS NOT NULL");
        $stmt->execute([$entregaId]);
        $previos = [];
        foreach ($stmt->fetchAll() as $r) {
            $previos[(int) $r['item_id']] = $r;
        }
        $filas = [];
        $paraTotal = [];
        foreach ($items as $it) {
            $prev = $previos[(int) $it['id']] ?? null;
            if (($it['cfg']['regla'] ?? '') === 'ia' && $prev !== null && $prev['fuente'] !== 'auto') {
                // Lo que ya corrigió la IA (o el docente) no se vuelve a pedir.
                $pts = $prev['puntaje'] === null ? null : (float) $prev['puntaje'];
                $paraTotal[] = ['item' => $it, 'puntaje' => $pts];
                $filas[] = [(int) $it['id'], (string) $prev['valor'], $pts, (string) $prev['comentario'], (string) $prev['fuente']];
                continue;
            }
            $e = self::evaluarItem($it, $payload);
            $manual = $prev !== null && $prev['fuente'] === 'docente';
            $pts = $manual ? (float) $prev['puntaje'] : $e['puntaje'];
            $paraTotal[] = ['item' => $it, 'puntaje' => $pts];
            $filas[] = [(int) $it['id'], json_encode($e, JSON_UNESCAPED_UNICODE), $pts, $prev['comentario'] ?? '', $manual ? 'docente' : 'auto'];
        }
        $t = self::totales($paraTotal);
        Db::reintentar(static function () use ($pdo, $entregaId, $filas, $t): void {
            $pdo->beginTransaction();
            $pdo->prepare('DELETE FROM osce_resultado WHERE entrega_id = ? AND item_id IS NOT NULL')->execute([$entregaId]);
            $ins = $pdo->prepare('INSERT INTO osce_resultado (entrega_id, item_id, valor, puntaje, comentario, fuente) VALUES (?, ?, ?, ?, ?, ?)');
            foreach ($filas as $f) {
                $ins->execute(array_merge([$entregaId], $f));
            }
            $pdo->prepare('UPDATE osce_entrega SET puntaje = ?, puntaje_max = ?, critico_fallado = ? WHERE id = ?')
                ->execute([$t['puntaje'], $t['puntaje_max'], $t['critico_fallado'] ? 1 : 0, $entregaId]);
            $pdo->commit();
        });
        return $t;
    }

    /** Lo que ve el docente (y el alumno, publicado): ítem, valor del alumno, esperado, puntaje. */
    public static function detalle(int $estacionId, int $participanteId): array
    {
        $stmt = Db::get()->prepare(
            "SELECT r.* FROM osce_resultado r JOIN osce_entrega e ON e.id = r.entrega_id
              WHERE e.estacion_id = ? AND e.participante_id = ? AND r.item_id IS NOT NULL"
        );
        $stmt->execute([$estacionId, $participanteId]);
        $res = [];
        foreach ($stmt->fetchAll() as $r) {
            $res[(int) $r['item_id']] = $r;
        }
        $out = [];
        foreach (OscePauta::items($estacionId) as $it) {
            $r = $res[(int) $it['id']] ?? null;
            $out[] = ['item' => $it, 'resultado' => $r, 'eval' => $r ? (json_decode((string) $r['valor'], true) ?: []) : null];
        }
        return $out;
    }

    /**
     * Revisión del docente: puntaje y comentario por ítem y feedback
     * general. Un puntaje distinto del automático pasa a ser del docente.
     */
    public static function guardarRevision(int $estacionId, int $participanteId, array $porItem, string $feedback): void
    {
        $detalle = self::detalle($estacionId, $participanteId);
        $entregaId = self::entregaId($estacionId, $participanteId);
        if ($entregaId === 0) {
            throw new InvalidArgumentException('Entrega no encontrada.');
        }
        $paraTotal = [];
        $cambios = [];
        foreach ($detalle as $d) {
            $r = $d['resultado'];
            if ($r === null) {
                continue;
            }
            $pts = $r['puntaje'] === null ? null : (float) $r['puntaje'];
            $comentario = (string) $r['comentario'];
            $fuente = (string) $r['fuente'];
            $in = $porItem[(int) $d['item']['id']] ?? null;
            if ($in !== null) {
                $max = (float) $d['item']['puntaje'];
                $raw = trim(str_replace(',', '.', (string) ($in['puntaje'] ?? '')));
                $auto = $d['eval']['puntaje'] ?? null;
                if ($raw !== '' && is_numeric($raw)) {
                    $pts = max(0.0, min($max, (float) $raw));
                }
                if ($pts === null) {
                    $fuente = $fuente;   // sigue pendiente de la IA
                } elseif ($auto === null || abs($pts - (float) $auto) > 0.001) {
                    $fuente = 'docente';
                } else {
                    $fuente = ($d['eval']['ia'] ?? false) ? 'ia' : 'auto';
                }
                $comentario = mb_substr(trim((string) ($in['comentario'] ?? '')), 0, 2000);
                $cambios[] = [$pts, $comentario, $fuente, (int) $r['id']];
            }
            $paraTotal[] = ['item' => $d['item'], 'puntaje' => $pts];
        }
        $t = self::totales($paraTotal);
        Db::reintentar(static function () use ($cambios, $feedback, $entregaId, $t): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $upd = $pdo->prepare('UPDATE osce_resultado SET puntaje = ?, comentario = ?, fuente = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?');
            foreach ($cambios as $c) {
                $upd->execute($c);
            }
            $pdo->prepare('UPDATE osce_entrega SET feedback = ?, puntaje = ?, puntaje_max = ?, critico_fallado = ? WHERE id = ?')
                ->execute([mb_substr($feedback, 0, 4000), $t['puntaje'], $t['puntaje_max'], $t['critico_fallado'] ? 1 : 0, $entregaId]);
            $pdo->commit();
        });
    }

    // -- Conclusión: corrección con IA ------------------------------------------

    /** Participantes con criterios de IA sin corregir en la estación. */
    public static function pendientesIa(int $estacionId): array
    {
        $stmt = Db::get()->prepare(
            "SELECT DISTINCT e.participante_id FROM osce_resultado r
               JOIN osce_entrega e ON e.id = r.entrega_id
               JOIN osce_item i ON i.id = r.item_id
              WHERE e.estacion_id = ? AND r.puntaje IS NULL AND i.config LIKE '%\"regla\":\"ia\"%'"
        );
        $stmt->execute([$estacionId]);
        return array_map('intval', $stmt->fetchAll(PDO::FETCH_COLUMN));
    }

    /** Lo que el estudiante no veía, en texto para la IA. */
    public static function datosReales(array $payload, ?array $caso): string
    {
        $lineas = [];
        $tipos = [];
        // Solo el equipo de la estación: el cuadro del VEMP no dice nada de un PEATC.
        $sec = ($payload['modulo'] ?? 'ABR') === 'VEMP' ? 'VEMP' : 'ABR';
        foreach (['OD', 'OI'] as $lado) {
            $t = $caso[$sec][$lado]['type'] ?? null;
            if ($t) {
                $tipos[] = "{$sec} {$lado}: cuadro del caso = {$t}";
            }
        }
        if ($tipos) {
            $lineas[] = implode('; ', $tipos);
        }
        foreach (self::curvas($payload) as $c) {
            $v = $payload['verdad'][$c['nombre'] ?? ''] ?? null;
            $desc = ($c['side'] ?? '?') . ' ' . self::db(self::nivel($c)) . ' dB'
                . (isset($c['stim']) ? ' ' . $c['stim'] : '') . (isset($c['freq']) ? ' ' . $c['freq'] : '') . ': ';
            if ($v === null) {
                $lineas[] = $desc . 'sin datos';
                continue;
            }
            $ondas = [];
            foreach (($v['waves'] ?? []) as $w => $d) {
                if (isset($d['amp']) && abs((float) $d['amp']) < 0.02) {
                    continue;   // a esa intensidad la onda ya no se ve
                }
                $ondas[] = $w . ' ' . number_format((float) $d['lat'], 2, ',', '') . ' ms'
                    . (isset($d['amp']) ? ' (amp ' . number_format(abs((float) $d['amp']), 2, ',', '') . ')' : '');
            }
            $lineas[] = $desc . (!empty($v['visible']) ? 'HAY respuesta; ' . implode(', ', $ondas) : 'SIN respuesta')
                . (isset($v['threshold']) ? '; umbral real del oído ' . self::db((float) $v['threshold']) . ' dB' : '');
        }
        return implode("\n", $lineas);
    }

    private static function marcasTexto(array $payload): string
    {
        $out = [];
        foreach (self::curvas($payload) as $c) {
            $m = [];
            foreach (($c['marcas'] ?? []) as $w => $lat) {
                if (is_numeric($lat)) {
                    $m[] = $w . ' ' . number_format((float) $lat, 2, ',', '') . ' ms';
                }
            }
            $out[] = ($c['side'] ?? '?') . ' ' . self::db(self::nivel($c)) . ' dB: ' . ($m ? implode(', ', $m) : 'sin marcas');
        }
        return implode("\n", $out);
    }

    /** El informe que escribió el estudiante en el equipo. */
    public static function informe(array $payload): string
    {
        $sec = $payload['abr'] ?? ($payload['vemp'] ?? []);
        $txt = 'HALLAZGOS:' . "\n" . trim((string) ($sec['hallazgos'] ?? '')) . "\n\nCONCLUSIÓN:\n" . trim((string) ($sec['conclusion'] ?? ''));
        if (!empty($sec['umbral_informado'])) {
            $txt .= "\n\nUMBRALES INFORMADOS: " . json_encode($sec['umbral_informado'], JSON_UNESCAPED_UNICODE);
        }
        return $txt;
    }

    /** Lee la respuesta de la IA: n => [puntaje, comentario], y el comentario general. */
    public static function parsearIaConclusion(string $raw, array $maximos): ?array
    {
        $clean = trim($raw);
        if (substr($clean, 0, 3) === '```') {
            $clean = trim((string) preg_replace('/^```[a-zA-Z]*\n?|```$/', '', $clean));
        }
        if (!preg_match('/\{.*\}/s', $clean, $m)) {
            return null;
        }
        $d = json_decode($m[0], true);
        if (!is_array($d) || !is_array($d['criterios'] ?? null)) {
            return null;
        }
        $out = [];
        foreach ($d['criterios'] as $c) {
            $n = (int) ($c['n'] ?? 0);
            if (!isset($maximos[$n]) || !is_numeric($c['puntaje'] ?? null)) {
                continue;
            }
            $p = round(((float) $c['puntaje']) * 2) / 2;
            $out[$n] = [max(0.0, min($maximos[$n], $p)), trim((string) ($c['comentario'] ?? ''))];
        }
        if (!$out) {
            return null;
        }
        return ['criterios' => $out, 'general' => trim((string) ($d['comentario_general'] ?? ''))];
    }

    /**
     * Corrige con IA los criterios de la conclusión de un alumno. Lo que el
     * docente ya puso a mano se respeta. Lanza si la IA no está o no responde.
     */
    public static function corregirIa(int $estacionId, int $participanteId): array
    {
        $est = Osce::estacion($estacionId);
        $cfg = self::config($est ?? []);
        $payload = self::registro($estacionId, $participanteId);
        if ($est === null || $payload === null) {
            throw new InvalidArgumentException('Entrega no encontrada.');
        }
        if (!LlmConfig::get()['active']) {
            throw new RuntimeException('La IA está desactivada (Admin → IA Paciente).');
        }
        $items = array_values(array_filter(OscePauta::items($estacionId), static fn ($it) => ($it['cfg']['regla'] ?? '') === 'ia'));
        $maximos = [];
        $lista = [];
        foreach ($items as $it) {
            $n = (int) $it['cfg']['n'];
            $maximos[$n] = (float) $it['puntaje'];
            $lista[] = "{$n}. {$it['texto']} (máximo " . self::db((float) $it['puntaje']) . ')';
        }
        $caso = self::caso((string) ($cfg['case_id'] ?? ''));
        $mensaje = "CRITERIOS:\n" . implode("\n", $lista)
            . "\n\nCONCLUSIÓN ESPERADA (docente):\n" . ($cfg['conclusion_esperada'] ?? '')
            . "\n\nDATOS REALES DEL CASO:\n" . self::datosReales($payload, $caso)
            . "\n\nLO QUE MARCÓ EL ESTUDIANTE:\n" . self::marcasTexto($payload)
            . "\n\nINFORME DEL ESTUDIANTE:\n" . self::informe($payload);
        $stmt = Db::get()->prepare('SELECT p.user_id, o.course_id FROM osce_participante p JOIN osce o ON o.id = p.osce_id WHERE p.id = ?');
        $stmt->execute([$participanteId]);
        $quien = $stmt->fetch() ?: [];
        $stmt->closeCursor();
        $presupuesto = AnamnesisDraft::maxTokens();
        $opciones = ['model' => AnamnesisDraft::model(), 'max_tokens' => $presupuesto, 'timeout' => AnamnesisDraft::TIMEOUT_S,
                     'campo_tokens' => 'Máximo de tokens del borrador de anamnesis', 'tarea' => 'osce',
                     'course_id' => (int) ($quien['course_id'] ?? 0), 'user_id' => (int) ($quien['user_id'] ?? 0)];
        try {
            $raw = LlmChat::reply(self::PROMPT_CONCLUSION, [], $mensaje, $opciones);
        } catch (LlmBudgetException $e) {
            $reintento = AnamnesisDraft::retryBudget($presupuesto);
            if ($reintento <= $presupuesto) {
                throw $e;
            }
            $opciones['max_tokens'] = $reintento;
            $raw = LlmChat::reply(self::PROMPT_CONCLUSION, [], $mensaje, $opciones);
        }
        $v = self::parsearIaConclusion($raw, $maximos);
        if ($v === null) {
            throw new RuntimeException('La IA no devolvió una corrección legible.');
        }
        $entregaId = self::entregaId($estacionId, $participanteId);
        Db::reintentar(static function () use ($items, $v, $entregaId): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $upd = $pdo->prepare("UPDATE osce_resultado SET puntaje = ?, valor = ?, fuente = 'ia', updated_at = CURRENT_TIMESTAMP
                                   WHERE entrega_id = ? AND item_id = ? AND fuente <> 'docente'");
            foreach ($items as $it) {
                $n = (int) $it['cfg']['n'];
                if (!isset($v['criterios'][$n])) {
                    continue;
                }
                [$pts, $coment] = $v['criterios'][$n];
                $eval = ['ia' => true, 'puntaje' => $pts, 'ok' => $pts >= (float) $it['puntaje'] - 1e-9,
                         'alumno' => $coment, 'esperado' => 'según la conclusión esperada'];
                $upd->execute([$pts, json_encode($eval, JSON_UNESCAPED_UNICODE), $entregaId, (int) $it['id']]);
            }
            if ($v['general'] !== '') {
                $pdo->prepare("UPDATE osce_entrega SET feedback = ? WHERE id = ? AND feedback = ''")->execute([$v['general'], $entregaId]);
            }
            $pdo->commit();
        });
        return self::corregir($estacionId, $participanteId);
    }

    // -- Lo que recibe la app al entrar ------------------------------------------

    /** Caso tal como lo usa la app (cases.data, con su id). */
    public static function caso(string $caseId): ?array
    {
        $stmt = Db::get()->prepare('SELECT id, data FROM cases WHERE id = ?');
        $stmt->execute([$caseId]);
        $row = $stmt->fetch();
        $stmt->closeCursor();
        if (!$row) {
            return null;
        }
        $data = json_decode((string) $row['data'], true) ?: [];
        $data['id'] = $data['id'] ?? $row['id'];
        return $data;
    }
}
