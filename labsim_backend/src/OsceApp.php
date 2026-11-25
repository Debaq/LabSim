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
        // Pruebas que no están en el protocolo 2019: los límites son los del
        // simulador (src/abr/ecochg.py y cortical.py), los que se vieron en clases.
        'ecochg' => [
            ['Informa por OD y OI si se registran el PS y el PA, con la latencia del PA', 1],
            ['Informa la razón PS/PA de cada oído y la compara con el límite de su electrodo (conducto 0,50; tímpano 0,40; promontorio 0,35)', 2],
            ['Si la midió, informa la razón de áreas PS/PA (límite 1,94)', 1],
            ['Concluye por oído si el registro es compatible o no con hidrops endolinfático', 2],
        ],
        'latencia_media' => [
            ['Informa por oído y por electrodo (C3, Cz, C4) la presencia de Na y Pa con sus latencias (adulto: Na ~18 ms, Pa ~30 ms)', 1],
            ['Informa la amplitud Na-Pa de cada electrodo (normal 0,5 a 2 µV)', 1],
            ['Calcula e interpreta el efecto electrodo y el efecto oído (una diferencia de 50 % o más es significativa)', 2],
            ['Concluye si hay compromiso de la vía tálamo-cortical y de qué lado (hemisferio u oído)', 2],
        ],
        'latencia_tardia' => [
            ['Informa por oído si se registran P1, N1 y P2 en Cz, con sus latencias (adulto: P1 ~55, N1 ~100, P2 ~180 ms; en niños la P1 depende de la edad)', 2],
            ['Informa la amplitud N1-P2 (adulto 4 a 15 µV)', 1],
            ['Concluye si la respuesta cortical es normal para la edad y si sugiere detección cortical del sonido', 2],
        ],
        'p300' => [
            ['Informa la presencia de la P3 en Pz frente al frecuente, con su latencia (adulto ~300 ms, sube con la edad)', 2],
            ['Informa la amplitud de la P3 y si el paciente atendió la tarea (cuenta de raros)', 1],
            ['Concluye si el procesamiento cognitivo-auditivo (discriminación y atención) está conservado', 2],
        ],
        'mmn' => [
            ['Informa la presencia de la MMN en la onda de diferencia (Fz), con su latencia (150 a 250 ms)', 2],
            ['Informa la amplitud de la MMN (0,5 a 5 µV) y que el registro fue pasivo', 1],
            ['Concluye si la discriminación auditiva preatencional está conservada', 2],
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
        'latencia_media' => 'MLR', 'latencia_tardia' => 'CAEP', 'p300' => 'P300', 'mmn' => 'MMN', 'estado_estable' => 'ASSR',
        'cvemp' => 'CVEMP', 'ovemp' => 'OVEMP',
    ];

    /** Ondas a marcar: [en la intensidad mayor de cada oído, en las demás]; la primera de las demás define "hay respuesta". */
    public const ONDAS = [
        'peatc' => [['I', 'III', 'V'], ['V']],
        'ecochg' => [['PS', 'PA'], ['PA']],
        'latencia_media' => [['Na', 'Pa'], ['Na', 'Pa']],
        'latencia_tardia' => [['P1', 'N1', 'P2'], ['N1', 'P2']],
        'p300' => [['N1', 'P2', 'P3'], ['P3']],
        'mmn' => [['MMN'], ['MMN']],
        'cvemp' => [['p13', 'n23'], ['p13', 'n23']],
        'ovemp' => [['n10', 'p16'], ['n10', 'p16']],
    ];

    /** Canal del ABR donde se lee (y se marca) cada potencial multicanal. */
    public const CANAL_LECTURA = ['latencia_media' => 'Cz', 'latencia_tardia' => 'Cz', 'p300' => 'Pz', 'mmn' => 'Fz'];

    /** Tolerancia de latencia con que parte el marcaje (ms): la del pico que se busca. */
    public const TOL_MS = ['ecochg' => 0.2, 'latencia_media' => 3.0, 'latencia_tardia' => 15.0, 'p300' => 25.0, 'mmn' => 20.0];

    /** Parámetros que solo existen en el oddball (P300 y MMN). */
    private const SOLO_ODDBALL = ['tarea', 'oddball_rare', 'oddball_pct'];

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
            'tarea' => ['panel', 'Instrucción al paciente (oddball)'],
            'oddball_rare' => ['equipo', 'Oddball: estímulo infrecuente'],
            'oddball_pct' => ['equipo', 'Oddball: proporción de infrecuentes (%)'],
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
        // El Protocolo ORL 2019 no trae estas pruebas: parten con la
        // configuración de rutina de LabSim (protocols.STANDARD_SETUP, la de
        // la clase de latencia media y tardía) y el docente la ajusta.
        'ecochg' => ['test' => 'ECochG', 'stim' => 'Click', 'pol' => 'Alternada', 'rate' => '11.1',
                     'filter_passhigh' => '5', 'filter_down' => '3000', 'window_ms' => '10', 'gain' => '100000'],
        'latencia_media' => ['test' => 'MLR', 'stim' => 'Click', 'rate' => '7.1', 'filter_passhigh' => '10',
                             'filter_down' => '300', 'window_ms' => '100', 'gain' => '50000', 'artifact_reject_uv' => '50'],
        'latencia_tardia' => ['test' => 'CAEP', 'stim' => 'Burst 1 kHz', 'rate' => '1', 'filter_passhigh' => '1',
                              'filter_down' => '30', 'window_ms' => '500', 'gain' => '50000', 'artifact_reject_uv' => '100'],
        'p300' => ['test' => 'P300', 'stim' => 'Burst 1 kHz', 'rate' => '1', 'filter_passhigh' => '0.5', 'filter_down' => '30',
                   'window_ms' => '800', 'tarea' => 'contar', 'oddball_rare' => 'Burst 2 kHz', 'oddball_pct' => '20'],
        'mmn' => ['test' => 'MMN', 'stim' => 'Burst 1 kHz', 'rate' => '1.5', 'filter_passhigh' => '1', 'filter_down' => '30',
                  'window_ms' => '500', 'tarea' => 'pasiva', 'oddball_rare' => 'Burst 2 kHz', 'oddball_pct' => '20'],
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
        'polaridades' => ['Registra el mismo oído e intensidad en rarefacción y en condensación (microfónica coclear)', ''],
    ];

    /**
     * Estrategias extra según el caso: "registra alguna curva con <parámetro>
     * = <valor>". El docente activa las que el caso pide (y agrega las
     * suyas); por defecto son bonificación. [texto, parámetro, esperado].
     */
    public const EXTRAS_BASE = [
        'peatc' => [
            ['Usa tone burst para el umbral por frecuencia', 'stim', 'Burst 500 Hz | Burst 1 kHz | Burst 2 kHz | Burst 4 kHz | NB CE-Chirp LS 500 Hz | NB CE-Chirp LS 1 kHz | NB CE-Chirp LS 2 kHz | NB CE-Chirp LS 4 kHz'],
            ['Registra por vía ósea (cuadro conductivo)', 'transducer', 'bone_vibrator'],
            ['Enmascara el oído contralateral (asimetría)', 'mkg', '1–120'],
            ['Sube la tasa a 81,1 (sospecha de neuropatía)', 'rate', '81.1'],
            ['Pinza el tubo para descartar artefacto (microfónica coclear)', 'clamp', 'sí'],
        ],
        'cvemp' => [
            ['Registra por vía ósea (cuadro conductivo)', 'transducer', 'Vibrador óseo (mastoides)'],
            ['Prueba otra frecuencia del tone burst (sintonía)', 'freq', '750 Hz | 1000 Hz'],
        ],
        'ovemp' => [
            ['Registra por vía ósea (cuadro conductivo)', 'transducer', 'Vibrador óseo (mastoides)'],
            ['Prueba otra frecuencia del tone burst (sintonía)', 'freq', '500 Hz | 750 Hz'],
        ],
    ];

    /** Parámetros de curva que solo sirven para las estrategias extra. */
    public const PARAMETROS_EXTRA = [
        'ABR' => ['mkg' => 'Enmascaramiento (dB)', 'clamp' => 'Tubo pinzado (sí/no)'],
        'VEMP' => [],
    ];

    /** Por examen: clave => [activa, valor, puntos, bonificación]. */
    public const ESTRATEGIA_BASE = [
        'peatc' => [
            'inicio' => [true, '80', 1, false], 'baja' => [true, '20', 1, false], 'sube' => [true, '10', 1, false],
            'sube_max' => [true, '90–100', 1, false], 'replica_max' => [true, '', 1, false],
            'replica_umbral' => [true, '', 1, false], 'ambos' => [true, '', 1, false], 'umbral' => [true, '10', 2, false],
            'umbral_chirp' => [true, '10', 1, true], 'polaridades' => [false, '', 1, true],
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
        $out = self::PARAMETROS[self::modulo($examen)];
        if (!in_array($examen, ['p300', 'mmn'], true)) {
            $out = array_diff_key($out, array_flip(self::SOLO_ODDBALL));
        }
        return $out;
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

    /** Las reglas de estrategia con que parte la tarea (las guardadas o las del examen). */
    public static function estrategia(array $t): array
    {
        if (isset($t['estrategia']) && is_array($t['estrategia'])) {
            return $t['estrategia'];
        }
        $base = self::ESTRATEGIA_BASE[$t['examen'] ?? ''] ?? self::ESTRATEGIA_BASE['otro'];
        $out = [];
        foreach ($base as $clave => [$activa, $valor, $pts, $bonus]) {
            $out[$clave] = ['activa' => $activa, 'valor' => $valor, 'puntos' => $pts, 'bonus' => $bonus];
        }
        return $out;
    }

    /** Estrategias extra de la tarea (las guardadas o las del examen, apagadas). */
    public static function extras(array $t): array
    {
        if (isset($t['extras']) && is_array($t['extras'])) {
            return $t['extras'];
        }
        return array_map(static fn ($e) => ['activa' => false, 'texto' => $e[0], 'clave' => $e[1], 'esperado' => $e[2],
                                            'puntos' => 1, 'bonus' => true],
                         self::EXTRAS_BASE[$t['examen'] ?? ''] ?? []);
    }

    /** Parámetros que se pueden pedir en una estrategia extra: clave => rótulo. */
    public static function parametrosExtra(string $examen): array
    {
        $out = [];
        foreach (self::parametros($examen) as $clave => [, $rotulo]) {
            $out[$clave] = $rotulo;
        }
        return $out + self::PARAMETROS_EXTRA[self::modulo($examen)];
    }

    /**
     * Arma una tarea de una estación de la app con lo que mandó el
     * formulario: [config de la tarea, ítems con sus puntos sin escalar].
     * config_equipo: un ítem por parámetro con esperado. marcaje: uno por
     * onda y curva. conclusión: criterios de la IA. protocolo: parámetros
     * en cada curva + estrategia.
     */
    public static function armarTarea(string $tipo, string $examen, array $in): array
    {
        if (!isset(Osce::EXAMENES[$examen])) {
            throw new InvalidArgumentException('Examen desconocido.');
        }
        $cfg = ['examen' => $examen, 'prueba' => self::PRUEBA_DE_EXAMEN[$examen] ?? 'ABR', 'modulo' => self::modulo($examen)];
        $variantes = [];
        foreach ((array) ($in['variantes'] ?? []) as $v) {
            $caseId = trim((string) ($v['case_id'] ?? ''));
            if ($caseId === '') {
                continue;
            }
            $esperada = mb_substr(trim((string) ($v['conclusion_esperada'] ?? '')), 0, 4000);
            if ($tipo === 'conclusion' && $esperada === '') {
                throw new InvalidArgumentException('Cada paciente necesita su conclusión esperada: es la referencia con que corrige la IA.');
            }
            $variantes[] = ['case_id' => $caseId, 'conclusion_esperada' => $esperada];
        }
        if (!$variantes) {
            throw new InvalidArgumentException('Elige al menos un paciente para la tarea.');
        }
        $cfg['variantes'] = array_slice($variantes, 0, 6);
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
        if ($tipo === 'config_equipo') {
            [$items, $cfg['esperado']] = $params('param');
            if (!$items) {
                throw new InvalidArgumentException('Indica al menos un parámetro esperado.');
            }
        } elseif ($tipo === 'marcaje') {
            $curvas = self::leerCurvas((string) ($in['curvas'] ?? ''));
            if (!$curvas) {
                throw new InvalidArgumentException('Indica las curvas a registrar: una por línea, como "OD 80".');
            }
            $tolBase = self::TOL_MS[$examen] ?? 0.2;
            $tol = $num($in['tol_ms'] ?? $tolBase, $tolBase);
            if ($tol <= 0 || $tol > 50) {
                throw new InvalidArgumentException('Tolerancia: entre 0,05 y 50 ms.');
            }
            $cfg['curvas'] = $curvas;
            $cfg['tol_ms'] = $tol;
            [$ondasMax, $ondasResto] = self::ondas($examen);
            $canal = self::CANAL_LECTURA[$examen] ?? null;
            $maxPorLado = [];
            foreach ($curvas as [$lado, $int]) {
                $maxPorLado[$lado] = max($maxPorLado[$lado] ?? -100, $int);
            }
            foreach ($curvas as [$lado, $int]) {
                foreach ($int === $maxPorLado[$lado] ? $ondasMax : $ondasResto as $onda) {
                    $items[] = ['texto' => "{$lado} {$int} dB: onda {$onda}", 'puntaje' => 1.0, 'critico' => false,
                                'config' => ['regla' => 'marca', 'lado' => $lado, 'int' => $int, 'onda' => $onda, 'tol_ms' => $tol,
                                             'canal' => $canal]];
                }
            }
        } elseif ($tipo === 'conclusion') {
            $curvas = self::leerCurvas((string) ($in['curvas'] ?? ''));
            if (!$curvas) {
                throw new InvalidArgumentException('Indica las curvas a registrar: una por línea, como "OD 80".');
            }
            $criterios = self::leerCriterios((string) ($in['criterios'] ?? ''));
            if (!$criterios) {
                throw new InvalidArgumentException('Indica al menos un criterio: "texto | puntos" por línea.');
            }
            $cfg['curvas'] = $curvas;
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
            $extras = [];
            $validos = self::parametrosExtra($examen);
            foreach ((array) ($in['extras'] ?? []) as $e) {
                $texto = trim((string) ($e['texto'] ?? ''));
                $clave = (string) ($e['clave'] ?? '');
                $esperado = trim((string) ($e['esperado'] ?? ''));
                if ($texto === '' && $esperado === '') {
                    continue;   // fila vacía
                }
                if (!isset($validos[$clave]) || $esperado === '' || $texto === '') {
                    throw new InvalidArgumentException('Cada estrategia extra necesita texto, parámetro y valor.');
                }
                $extra = ['activa' => !empty($e['activa']), 'texto' => mb_substr($texto, 0, 200), 'clave' => $clave,
                          'esperado' => $esperado, 'puntos' => $num($e['puntos'] ?? 1, 1.0) ?: 1.0, 'bonus' => !empty($e['bonus'])];
                $extras[] = $extra;
                if ($extra['activa']) {
                    $items[] = ['texto' => $extra['texto'] . ($extra['bonus'] ? ' (bonificación)' : ''),
                                'puntaje' => $extra['puntos'], 'critico' => false,
                                'config' => ['regla' => 'alguna_curva', 'clave' => $clave, 'esperado' => $esperado,
                                             'bonus' => $extra['bonus']]];
                }
            }
            $cfg['extras'] = $extras;
            // Lo que el caso pide no puede descontar en "parámetros en cada
            // curva": si la estrategia del caso es la vía ósea, esas curvas
            // también valen con vibrador (y con rarefacción/condensación si
            // pide comparar polaridades).
            $tambien = [];
            foreach ($extras as $x) {
                if ($x['activa']) {
                    $tambien[$x['clave']][] = $x['esperado'];
                }
            }
            if (!empty($estrategia['polaridades']['activa'])) {
                $tambien['pol'][] = 'Rarefacción | Condensación';
            }
            foreach ($items as &$it) {
                $c = $it['config'];
                if ($c['regla'] === 'curvas_param' && !empty($tambien[$c['clave']])) {
                    $it['config']['tambien'] = implode(' | ', $tambien[$c['clave']]);
                }
            }
            unset($it);
            if (!$items) {
                throw new InvalidArgumentException('Activa al menos un criterio.');
            }
        }
        return [$cfg, $items];
    }

    // -- Tareas de la estación ------------------------------------------------

    /**
     * Las tareas de la estación, en orden. Cada una: titulo, examen, prueba,
     * modulo, peso (%), variantes [{case_id, conclusion_esperada}], lo propio
     * de su tipo (curvas, esperado, estrategia...) e items (sin escalar).
     * Una estación de antes (un solo caso) es una tarea de peso 100.
     */
    public static function tareas(array $est): array
    {
        $cfg = self::config($est);
        if (isset($cfg['tareas']) && is_array($cfg['tareas'])) {
            return array_map(static function ($t) {
                $t['peso'] = (float) ($t['peso'] ?? 100);
                return $t;
            }, array_values($cfg['tareas']));
        }
        if (empty($cfg['case_id'])) {
            return [];
        }
        $examen = (string) $est['examen'];
        $t = $cfg;
        unset($t['app_codigo'], $t['case_id'], $t['conclusion_esperada']);
        $t += ['examen' => $examen, 'prueba' => self::PRUEBA_DE_EXAMEN[$examen] ?? 'ABR', 'modulo' => self::modulo($examen)];
        $t['titulo'] = Osce::EXAMENES[$examen] ?? $examen;
        $t['peso'] = 100.0;
        $t['variantes'] = [['case_id' => (string) $cfg['case_id'], 'conclusion_esperada' => (string) ($cfg['conclusion_esperada'] ?? '')]];
        $t['items'] = array_map(static fn ($it) => ['texto' => $it['texto'], 'puntaje' => (float) $it['puntaje'],
                                                    'critico' => (int) $it['critico'] === 1, 'config' => $it['cfg']],
                                OscePauta::items((int) $est['id']));
        return [$t];
    }

    /**
     * Paciente de la tarea k para el alumno N.º numero. Las variantes son de
     * igual dificultad y se reparten por número, sin correrlas entre tareas:
     * el "paciente 1" de cada tarea le toca al mismo alumno, así un caso
     * integrado (PEATC y VEMP del mismo paciente, en dos tareas) es uno solo
     * si el docente pone los pacientes en el mismo orden. $k queda por si
     * algún día se quiere correr.
     */
    public static function variante(array $tarea, int $numero, int $k): ?array
    {
        $v = array_values($tarea['variantes'] ?? []);
        if (!$v) {
            return null;
        }
        return $v[(max(1, $numero) - 1) % count($v)];
    }

    /** Guarda (o agrega, con k = número de tareas) la tarea k y rehace los ítems. */
    public static function guardarTarea(array $est, int $k, array $in): void
    {
        $tareas = self::tareas($est);
        if ($k < 0 || $k > count($tareas)) {
            throw new InvalidArgumentException('Tarea no encontrada.');
        }
        if ($k === count($tareas) && $k >= 8) {
            throw new InvalidArgumentException('Hasta 8 tareas por estación.');
        }
        $examen = (string) ($in['examen'] ?? ($tareas[$k]['examen'] ?? $est['examen']));
        [$t, $items] = self::armarTarea((string) $est['tipo'], $examen, $in);
        $titulo = trim((string) ($in['titulo'] ?? ''));
        $t['titulo'] = mb_substr($titulo !== '' ? $titulo : (Osce::EXAMENES[$examen] ?? $examen), 0, 80);
        $peso = str_replace(',', '.', (string) ($in['peso'] ?? ''));
        $t['peso'] = is_numeric($peso) && (float) $peso > 0 ? min(100.0, (float) $peso) : (float) ($tareas[$k]['peso'] ?? 100);
        $t['items'] = $items;
        $tareas[$k] = $t;
        self::guardarTareas($est, $tareas);
    }

    public static function quitarTarea(array $est, int $k): void
    {
        $tareas = self::tareas($est);
        if (!isset($tareas[$k])) {
            throw new InvalidArgumentException('Tarea no encontrada.');
        }
        array_splice($tareas, $k, 1);
        self::guardarTareas($est, $tareas);
    }

    public static function moverTarea(array $est, int $k, int $dir): void
    {
        $tareas = self::tareas($est);
        $j = $k + $dir;
        if (!isset($tareas[$k], $tareas[$j])) {
            return;
        }
        [$tareas[$k], $tareas[$j]] = [$tareas[$j], $tareas[$k]];
        self::guardarTareas($est, $tareas);
    }

    /** Pesos de las tareas (%): k => peso. */
    public static function guardarPesos(array $est, array $pesos): void
    {
        $tareas = self::tareas($est);
        foreach ($tareas as $k => &$t) {
            $p = str_replace(',', '.', (string) ($pesos[$k] ?? ''));
            if (!is_numeric($p) || (float) $p <= 0 || (float) $p > 100) {
                throw new InvalidArgumentException('Cada peso va entre 1 y 100 %.');
            }
            $t['peso'] = (float) $p;
        }
        unset($t);
        self::guardarTareas($est, $tareas);
    }

    /** Suma de los pesos (debería ser 100). */
    public static function sumaPesos(array $tareas): float
    {
        return array_sum(array_map(static fn ($t) => (float) ($t['peso'] ?? 0), $tareas));
    }

    /**
     * Guarda las tareas y rehace los ítems de la estación: los de cada
     * tarea escalados para que su máximo (sin bonificaciones) sea su peso.
     * Así la estación suma 100 y cada tarea pesa lo que el docente dijo,
     * sin importar cuántos ítems tenga.
     */
    private static function guardarTareas(array $est, array $tareas): void
    {
        $cfg = self::config($est);
        $tareas = array_values($tareas);
        $cfg['tareas'] = $tareas;
        unset($cfg['case_id'], $cfg['conclusion_esperada'], $cfg['curvas'], $cfg['esperado'], $cfg['esperado_curvas'],
              $cfg['estrategia'], $cfg['extras'], $cfg['onda'], $cfg['tol_ms'], $cfg['prueba']);
        $varias = count($tareas) > 1;
        $items = [];
        foreach ($tareas as $k => $t) {
            $max = 0.0;
            foreach ($t['items'] ?? [] as $it) {
                if (empty($it['config']['bonus'])) {
                    $max += (float) $it['puntaje'];
                }
            }
            $escala = $max > 0 ? (float) $t['peso'] / $max : 1.0;
            foreach ($t['items'] ?? [] as $it) {
                $it['puntaje'] = round((float) $it['puntaje'] * $escala, 4);
                $it['config']['tarea'] = $k;
                if ($varias) {
                    $it['texto'] = $t['titulo'] . ' · ' . $it['texto'];
                }
                $items[] = $it;
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
            foreach ($items as $n => $it) {
                $ins->execute([$estId, $n + 1, $it['texto'], $it['puntaje'], !empty($it['critico']) ? 1 : 0,
                               json_encode($it['config'], JSON_UNESCAPED_UNICODE)]);
            }
            $pdo->commit();
        });
    }

    /**
     * Estación de un solo caso (como antes): la tarea 0 con el examen de la
     * estación. Acepta case_id y conclusion_esperada sueltos.
     */
    public static function guardarContenido(array $est, array $in): void
    {
        if (!isset($in['variantes'])) {
            $in['variantes'] = [['case_id' => $in['case_id'] ?? '', 'conclusion_esperada' => $in['conclusion_esperada'] ?? '']];
        }
        $in['examen'] = $in['examen'] ?? (self::tareas($est)[0]['examen'] ?? $est['examen']);
        self::guardarTarea($est, 0, $in);
    }

    /** Lo que la app entregó de la tarea k (o la entrega entera, si es de una sola). */
    public static function payloadDe(array $payload, ?int $k): array
    {
        if (!isset($payload['tareas']) || !is_array($payload['tareas'])) {
            return $payload;
        }
        $t = $payload['tareas'][$k ?? 0] ?? ($payload['tareas'][(string) ($k ?? 0)] ?? null);
        return is_array($t) ? $t : [];
    }

    /** Lo que recibe la app al entrar un alumno: cada tarea con su paciente. */
    public static function tareasParaAlumno(array $est, int $numero): array
    {
        $out = [];
        foreach (self::tareas($est) as $k => $t) {
            $v = self::variante($t, $numero, $k);
            $caso = $v !== null ? self::caso((string) $v['case_id']) : null;
            if ($caso === null) {
                throw new InvalidArgumentException('Una tarea de la estación no tiene paciente. Avisa al docente.');
            }
            $out[] = ['n' => $k, 'titulo' => $t['titulo'], 'peso' => (float) $t['peso'], 'tipo' => $est['tipo'],
                      'examen' => $t['examen'], 'modulo' => $t['modulo'] ?? self::modulo((string) $t['examen']),
                      'prueba' => $t['prueba'] ?? 'ABR',
                      'curvas' => in_array($est['tipo'], ['marcaje', 'conclusion'], true) ? ($t['curvas'] ?? []) : [],
                      'caso' => $caso];
        }
        return $out;
    }

    /** Módulos de la app que usa la estación (ABR, VEMP). */
    public static function modulos(array $est): array
    {
        $m = array_values(array_unique(array_map(static fn ($t) => (string) ($t['modulo'] ?? self::modulo((string) $t['examen'])), self::tareas($est))));
        return $m ?: [self::modulo((string) $est['examen'])];
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

    /** Curva con ese lado e intensidad (la primera registrada; en ese canal si es multicanal). */
    private static function curvaDe(array $payload, string $lado, int $int, ?string $canal = null): ?array
    {
        foreach (self::curvas($payload) as $c) {
            if ($canal !== null && isset($c['canal']) && $c['canal'] !== $canal) {
                continue;
            }
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
            $tambien = (string) ($r['tambien'] ?? '');
            foreach ($curvas as $c) {
                $v = $c[$r['clave']] ?? null;
                if (self::cumpleEsperado($v, (string) $r['esperado']) || ($tambien !== '' && self::cumpleEsperado($v, $tambien))) {
                    $bien++;
                } elseif (count($malos) < 3) {
                    $malos[] = self::mostrar($r['clave'], $c[$r['clave']] ?? '—');
                }
            }
            return self::resultado($bien / count($curvas), "{$bien} de " . count($curvas) . ' curvas'
                . ($malos ? ' (también ' . implode(', ', array_unique($malos)) . ')' : ''),
                self::mostrarEsperado($r['clave'], (string) $r['esperado'])
                    . ($tambien !== '' ? ' (o ' . self::mostrarEsperado($r['clave'], $tambien) . ', por el caso)' : ''), $pts);
        }

        if ($regla === 'marca') {
            $curva = self::curvaDe($payload, (string) $r['lado'], (int) $r['int'], isset($r['canal']) ? (string) $r['canal'] : null);
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

            case 'alguna_curva':
                $clave = (string) ($r['clave'] ?? '');
                $esp = self::mostrarEsperado($clave, (string) ($r['esperado'] ?? ''));
                foreach (self::curvas($payload) as $c) {
                    if (self::cumpleEsperado($c[$clave] ?? null, (string) ($r['esperado'] ?? ''))) {
                        return self::resultado(1.0, 'sí: ' . ($c['side'] ?? '') . ' ' . self::db(self::nivel($c)) . ' dB, '
                            . self::mostrar($clave, $c[$clave]), $esp, $pts);
                    }
                }
                return self::resultado(0.0, 'ninguna curva', $esp, $pts);

            case 'polaridades':
                $vistas = [];
                foreach (self::curvas($payload) as $c) {
                    $vistas[($c['side'] ?? '') . '|' . self::db(self::nivel($c))][(string) ($c['pol'] ?? '')] = true;
                }
                foreach ($vistas as $donde => $pols) {
                    if (isset($pols['Rarefacción'], $pols['Condensación'])) {
                        return self::resultado(1.0, 'sí: ' . str_replace('|', ' ', $donde) . ' dB', $esperado, $pts);
                    }
                }
                return self::resultado(0.0, 'no', $esperado, $pts);
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
            $e = self::evaluarItem($it, self::payloadDe($payload, isset($it['cfg']['tarea']) ? (int) $it['cfg']['tarea'] : null));
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
        $payload = self::registro($estacionId, $participanteId);
        if ($est === null || $payload === null) {
            throw new InvalidArgumentException('Entrega no encontrada.');
        }
        if (!LlmConfig::get()['active']) {
            throw new RuntimeException('La IA está desactivada (Admin → IA Paciente).');
        }
        $stmt = Db::get()->prepare('SELECT p.user_id, p.numero, o.course_id FROM osce_participante p JOIN osce o ON o.id = p.osce_id WHERE p.id = ?');
        $stmt->execute([$participanteId]);
        $quien = $stmt->fetch() ?: [];
        $stmt->closeCursor();
        $tareas = self::tareas($est);
        // Una llamada por tarea con criterios de IA: cada una con su paciente.
        $porTarea = [];
        foreach (OscePauta::items($estacionId) as $it) {
            if (($it['cfg']['regla'] ?? '') === 'ia') {
                $porTarea[(int) ($it['cfg']['tarea'] ?? 0)][] = $it;
            }
        }
        $entregaId = self::entregaId($estacionId, $participanteId);
        $generales = [];
        foreach ($porTarea as $k => $items) {
            $tarea = $tareas[$k] ?? [];
            $v = self::variante($tarea, (int) ($quien['numero'] ?? 1), $k) ?? [];
            $datos = self::payloadDe($payload, $k);
            $maximos = [];
            $lista = [];
            foreach ($items as $it) {
                $n = (int) $it['cfg']['n'];
                $maximos[$n] = (float) $it['puntaje'];
                $lista[] = "{$n}. {$it['texto']} (máximo " . self::db((float) $it['puntaje']) . ')';
            }
            $mensaje = "CRITERIOS:\n" . implode("\n", $lista)
                . "\n\nCONCLUSIÓN ESPERADA (docente):\n" . ($v['conclusion_esperada'] ?? '')
                . "\n\nDATOS REALES DEL CASO:\n" . self::datosReales($datos, self::caso((string) ($v['case_id'] ?? '')))
                . "\n\nLO QUE MARCÓ EL ESTUDIANTE:\n" . self::marcasTexto($datos)
                . "\n\nINFORME DEL ESTUDIANTE:\n" . self::informe($datos);
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
            $r = self::parsearIaConclusion($raw, $maximos);
            if ($r === null) {
                throw new RuntimeException('La IA no devolvió una corrección legible.');
            }
            Db::reintentar(static function () use ($items, $r, $entregaId): void {
                $pdo = Db::get();
                $pdo->beginTransaction();
                $upd = $pdo->prepare("UPDATE osce_resultado SET puntaje = ?, valor = ?, fuente = 'ia', updated_at = CURRENT_TIMESTAMP
                                       WHERE entrega_id = ? AND item_id = ? AND fuente <> 'docente'");
                foreach ($items as $it) {
                    $n = (int) $it['cfg']['n'];
                    if (!isset($r['criterios'][$n])) {
                        continue;
                    }
                    [$pts, $coment] = $r['criterios'][$n];
                    $eval = ['ia' => true, 'puntaje' => $pts, 'ok' => $pts >= (float) $it['puntaje'] - 1e-9,
                             'alumno' => $coment, 'esperado' => 'según la conclusión esperada'];
                    $upd->execute([$pts, json_encode($eval, JSON_UNESCAPED_UNICODE), $entregaId, (int) $it['id']]);
                }
                $pdo->commit();
            });
            if ($r['general'] !== '') {
                $generales[] = (count($porTarea) > 1 ? ($tarea['titulo'] ?? '') . ': ' : '') . $r['general'];
            }
        }
        if ($generales) {
            Db::reintentar(static function () use ($generales, $entregaId): void {
                Db::get()->prepare("UPDATE osce_entrega SET feedback = ? WHERE id = ? AND feedback = ''")
                    ->execute([implode("\n", $generales), $entregaId]);
            });
        }
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
