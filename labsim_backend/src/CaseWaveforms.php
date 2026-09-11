<?php

declare(strict_types=1);

require_once __DIR__ . '/CaseBuilder.php';

/**
 * Trazos esquemáticos de ABR y VEMP a partir de los parámetros del caso.
 *
 * **No es el generador.** El que dibuja lo que el alumno ve vive en Python
 * (src/abr/ABR_generator.py, src/vemp/), tiene ruido, promediación,
 * artefactos y FSP, y es la única fuente de verdad de la señal. Esto es una
 * reconstrucción: las mismas latencias normativas, la misma función
 * latencia-intensidad y las mismas reglas del patrón retrococlear, sin
 * ruido y sin promediar, para que el docente vea en la ficha la FORMA que
 * va a tener el examen -- dónde caen las ondas, cuál se pierde primero y a
 * qué intensidad desaparece la V.
 *
 * Cada constante dice de dónde sale. Las latencias y amplitudes base son las
 * de resources/abr/normative_data.json (un test las compara contra ese JSON,
 * que no se despliega con el backend).
 */
final class CaseWaveforms
{
    // ---------------------------------------------------------------
    // ABR -- click, vía aérea
    // ---------------------------------------------------------------

    /**
     * Latencia (ms) y amplitud (µV) del click a nivel alto por población.
     * Copia de populations[*].air_conduction.click en
     * resources/abr/normative_data.json.
     */
    public const CLICK_BASE = [
        'adult_male'   => ['I' => [1.65, 0.30], 'III' => [3.85, 0.35], 'V' => [5.70, 0.50]],
        'adult_female' => ['I' => [1.62, 0.21], 'III' => [3.68, 0.37], 'V' => [5.47, 0.60]],
        'child'        => ['I' => [1.58, 0.28], 'III' => [3.78, 0.33], 'V' => [5.60, 0.48]],
        'neonate'      => ['I' => [2.10, 0.20], 'III' => [4.70, 0.24], 'V' => [6.80, 0.35]],
        'elderly'      => ['I' => [1.75, 0.27], 'III' => [4.00, 0.32], 'V' => [5.90, 0.45]],
    ];

    /**
     * Interpicos normativos del click por población (ms). Copia de
     * populations[*].air_conduction.click.interpeak en
     * resources/abr/normative_data.json.
     */
    public const CLICK_INTERPICOS = [
        'adult_male' => ['I-III' => 2.2, 'III-V' => 1.85, 'I-V' => 4.05],
        'adult_female' => ['I-III' => 2.2, 'III-V' => 1.8, 'I-V' => 4.0],
        'child' => ['I-III' => 2.2, 'III-V' => 1.82, 'I-V' => 4.02],
        'neonate' => ['I-III' => 2.6, 'III-V' => 2.1, 'I-V' => 4.7],
        'elderly' => ['I-III' => 2.25, 'III-V' => 1.9, 'I-V' => 4.15],
    ];

    /**
     * Rango de normalidad: media +- NORM_SD_LIMIT desviaciones. Mismos
     * números que NORM_LAT_SD / NORM_INTERPEAK_SD / NORM_SD_LIMIT en
     * ABR_generator.py, que es con los que el módulo juzga la tabla del
     * alumno -- si acá dijeran otra cosa, la ficha marcaría como alterado
     * lo que el equipo da por normal.
     */
    public const NORM_SD_LIMITE = 2.0;
    public const NORM_SD_LAT = ['I' => 0.20, 'III' => 0.22, 'V' => 0.25];
    public const NORM_SD_INTERPICO = ['I-III' => 0.22, 'III-V' => 0.22, 'I-V' => 0.25];

    /** Diferencia interaural de la onda V que se considera significativa (ms). */
    public const NORM_INTERAURAL_V_MS = 0.4;

    /**
     * Razón V/I mínima normal: en un oído normal la onda V es MAYOR que la
     * I, así que la razón pasa de 1. Por debajo, la V está
     * desproporcionadamente chica respecto de la I, que es el hallazgo
     * retrococlear clásico. Mismo valor que NORM_VI_RATIO_MIN en
     * ABR_generator.py, que se corrigió junto con este.
     */
    public const NORM_VI_RATIO_MIN = 1.0;

    /** Ancho (sigma, ms) de cada onda. WAVE_SIGMA en ABR_generator.py. */
    public const SIGMA = ['I' => 0.22, 'III' => 0.22, 'V' => 0.18];

    /**
     * Crecimiento de amplitud por nivel de sensación:
     * factor = 1 - exp(-(SL - sl_min) / tau). WAVE_AMP_GROWTH.
     * La I necesita mucho más nivel que la V, y por eso es la primera que se
     * pierde al bajar la intensidad.
     */
    public const AMP_GROWTH = [
        'I' => ['sl_min' => 20, 'tau' => 13],
        'III' => ['sl_min' => 5, 'tau' => 16],
        'V' => ['sl_min' => -4, 'tau' => 20],
    ];

    /** La coclear satura antes (reclutamiento). PATHOLOGY_TAU_FACTOR. */
    public const TAU_FACTOR_COCLEAR = 0.65;

    /** Cuánto del corrimiento L-I le toca a cada onda. LAT_SHIFT_FACTOR. */
    public const LAT_SHIFT_FACTOR = ['I' => 0.85, 'III' => 0.92, 'V' => 1.0];

    /** Reparto de las prolongaciones. NEURAL_LAT_SHARE / NEURAL_LAT_SHARE_IIIV. */
    public const SHARE_I_III = ['I' => 0.0, 'III' => 1.0, 'V' => 1.0];
    public const SHARE_III_V = ['I' => 0.0, 'III' => 0.0, 'V' => 1.0];
    /** Reparto de la caída de amplitud: la I intacta, la V con todo. NEURAL_AMP_SHARE. */
    public const SHARE_AMP = ['I' => 0.0, 'III' => 0.5, 'V' => 1.0];
    /** Lo que queda de una onda bloqueada. NEURAL_BLOCK_AMP_FACTOR. */
    public const BLOQUEO_AMP = 0.02;

    /** Empinada de la L-I coclear cerca del umbral. COCHLEAR_LI_*. */
    public const COCLEAR_SL_REF = 40.0;
    public const COCLEAR_SLOPE = 0.15;

    /** Amplificación de las desviaciones del caso cerca del umbral. DEV_LI_*. */
    public const DEV_GAIN = 0.35;
    public const DEV_MAX = 1.5;

    /** Amplitud (µV) por debajo de la cual la onda no se ve. */
    public const AMP_VISIBLE = 0.02;

    /**
     * Rangos de normalidad de latencias e interpicos a una intensidad.
     *
     * Espejo de ABRGenerator::normative_limits: la latencia absoluta se
     * corre con la MISMA función latencia-intensidad que dibuja la curva
     * (una V de 6.4 ms a 40 dB no es tardía; a 80 sí), y los interpicos no
     * dependen de la intensidad.
     *
     * @return array{lat:array<string,array{0:float,1:float}>,interpeak:array<string,array{0:float,1:float}>,interaural_v:float}
     */
    public static function limitesNormativos(string $poblacion = 'adult_female', float $intensidad = 80.0): array
    {
        $base = self::CLICK_BASE[$poblacion] ?? self::CLICK_BASE['adult_female'];
        $interpicos = self::CLICK_INTERPICOS[$poblacion] ?? self::CLICK_INTERPICOS['adult_female'];
        $corrimiento = self::corrimientoLatencia($intensidad);

        $lat = [];
        foreach (self::NORM_SD_LAT as $onda => $sd) {
            $centro = $base[$onda][0] + $corrimiento * self::LAT_SHIFT_FACTOR[$onda];
            $margen = $sd * self::NORM_SD_LIMITE;
            $lat[$onda] = [$centro - $margen, $centro + $margen];
        }

        $ip = [];
        foreach (self::NORM_SD_INTERPICO as $clave => $sd) {
            $margen = $sd * self::NORM_SD_LIMITE;
            $ip[$clave] = [$interpicos[$clave] - $margen, $interpicos[$clave] + $margen];
        }

        return [
            'lat' => $lat,
            'interpeak' => $ip,
            'interaural_v' => self::NORM_INTERAURAL_V_MS,
            'v_i_min' => self::NORM_VI_RATIO_MIN,
        ];
    }

    /**
     * Corrimiento (ms) de la función latencia-intensidad respecto de 80 dB.
     * Espejo exacto de ABRGenerator.latency_intensity_shift: ~0.12 ms/10 dB
     * por encima de 70 dB y ~0.3 ms/10 dB de ahí para abajo (Hood).
     */
    public static function corrimientoLatencia(float $intensidad): float
    {
        if ($intensidad >= 70) {
            return (80 - $intensidad) / 10 * 0.12;
        }
        return (80 - 70) / 10 * 0.12 + (70 - $intensidad) / 10 * 0.3;
    }

    /**
     * Población normativa del paciente. Espejo de select_population() en
     * ABR_generator.py, huecos incluidos: un lactante se aproxima con
     * 'child' y un adolescente también, porque a esa edad las latencias ya
     * son de adulto.
     */
    public static function poblacion(?int $edad, int $genero): string
    {
        if ($edad === null) {
            return 'adult_female';
        }
        if ($edad < 1) {
            return 'neonate';
        }
        if ($edad < 18) {
            return 'child';
        }
        if ($edad >= 60) {
            return 'elderly';
        }
        return $genero === 0 ? 'adult_male' : 'adult_female';
    }

    /**
     * Latencia y amplitud de cada onda del click a una intensidad dada.
     *
     * @param array<string,mixed> $neural patrón retrococlear ya normalizado
     * @param array<string,array{lat:float,amp:float}> $desviaciones del caso
     * @return array<string,array{lat:float,amp:float,sigma:float}>
     */
    public static function ondasClick(
        float $intensidad,
        float $umbral,
        string $tipo,
        array $neural,
        array $desviaciones = [],
        string $poblacion = 'adult_female'
    ): array {
        $base = self::CLICK_BASE[$poblacion] ?? self::CLICK_BASE['adult_female'];
        $sl = $intensidad - $umbral;

        // Intensidad efectiva: un oído con umbral elevado ve la misma
        // función L-I corrida a la derecha. Se mide desde el umbral normal
        // del click (10 dB nHL, la corrección nHL de un oído de 0 dB HL).
        $corrimiento = self::corrimientoLatencia(80 - max(0.0, 60.0 - $sl));
        if ($tipo === 'coclear' && $sl < self::COCLEAR_SL_REF) {
            // Cerca del umbral la coclear se alarga desproporcionado y al
            // subir el nivel converge a la normal: por eso su curva L-I es
            // EMPINADA en vez de corrida.
            $corrimiento += (self::COCLEAR_SL_REF - $sl) / 10 * self::COCLEAR_SLOPE;
        }
        $gananciaDesv = 1 + min(self::DEV_MAX, self::DEV_GAIN * $corrimiento);

        // El patrón retrococlear SOLO se aplica en un oído neural, igual
        // que en el generador (`if is_neural`): con los defaults cargados
        // --v_i_factor 0.45, i_iii 0.2-- un oído normal saldría con la V
        // caída a la mitad y las ondas corridas, que no es un oído normal.
        $esNeural = $tipo === 'neural';
        $bloqueo = $esNeural ? (string) ($neural['bloqueo'] ?? 'ninguno') : 'ninguno';
        $desincronia = $esNeural ? (string) ($neural['desincronia'] ?? 'ninguna') : 'ninguna';
        $caidaVI = $esNeural ? 1.0 - (float) ($neural['v_i_factor'] ?? 0.45) : 0.0;

        $out = [];
        foreach (['I', 'III', 'V'] as $onda) {
            [$lat0, $amp0] = $base[$onda];

            $lat = $lat0 + $corrimiento * self::LAT_SHIFT_FACTOR[$onda];
            if ($esNeural) {
                $lat += (float) ($neural['global_delay_ms'] ?? 0)
                    + (float) ($neural['i_iii_ms'] ?? 0) * self::SHARE_I_III[$onda]
                    + (float) ($neural['iii_v_ms'] ?? 0) * self::SHARE_III_V[$onda];
            }
            $lat += (float) ($desviaciones['onda_' . $onda]['lat'] ?? 0) * $gananciaDesv;

            $g = self::AMP_GROWTH[$onda];
            $tau = $g['tau'] * ($tipo === 'coclear' ? self::TAU_FACTOR_COCLEAR : 1.0);
            $crecimiento = 1 - exp(-max(0.0, $sl - $g['sl_min']) / $tau);
            $amp = $amp0 * max(0.0, $crecimiento);
            $amp *= max(0.0, 1 - $caidaVI * self::SHARE_AMP[$onda]);
            $amp += (float) ($desviaciones['onda_' . $onda]['amp'] ?? 0);

            if ($bloqueo === 'total' || ($bloqueo === 'post_i' && $onda !== 'I')) {
                $amp *= self::BLOQUEO_AMP;
            }

            // La desincronía no borra la onda: la ensancha y la achata, que
            // es exactamente lo que hace imposible marcarle un pico.
            $sigma = self::SIGMA[$onda];
            if ($desincronia === 'leve') {
                $sigma *= 1.35;
                $amp *= 0.8;
            } elseif ($desincronia === 'alta') {
                $sigma *= 1.9;
                $amp *= 0.5;
            }
            // A poco nivel de sensación la onda además se ensancha sola.
            $sigma *= 1 + max(0.0, 40 - $sl) / 120;

            $out[$onda] = ['lat' => $lat, 'amp' => max(0.0, $amp), 'sigma' => $sigma];
        }
        return $out;
    }

    /**
     * Trazo del click: suma de gaussianas centradas en cada onda, muestreada
     * de 0 a $hasta ms. Es la misma construcción del generador ("ondas =
     * suma de gaussianas centradas en cada latencia, no Bézier").
     *
     * @param array<string,array{lat:float,amp:float,sigma:float}> $ondas
     * @return array<int,array{0:float,1:float}> pares [ms, µV]
     */
    public static function trazo(array $ondas, float $hasta = 12.0, int $muestras = 240): array
    {
        $pts = [];
        for ($n = 0; $n <= $muestras; $n++) {
            $t = $hasta * $n / $muestras;
            $v = 0.0;
            foreach ($ondas as $onda) {
                $d = $t - $onda['lat'];
                $v += $onda['amp'] * exp(-($d * $d) / (2 * $onda['sigma'] * $onda['sigma']));
            }
            $pts[] = [$t, $v];
        }
        return $pts;
    }

    /**
     * Intensidades de la serie: del máximo al umbral, de 20 en 20 y con el
     * umbral siempre incluido -- así se ve la onda V persistiendo cuando ya
     * no queda nada más, que es como se busca un umbral electrofisiológico.
     *
     * @return array<int,float>
     */
    public static function serieIntensidades(float $umbral, float $maximo = 80.0, float $paso = 20.0): array
    {
        $niveles = [];
        for ($i = $maximo; $i > $umbral + 1; $i -= $paso) {
            $niveles[] = $i;
        }
        $niveles[] = max(0.0, $umbral);
        return $niveles;
    }

    // ---------------------------------------------------------------
    // VEMP
    // ---------------------------------------------------------------

    /**
     * Latencia (ms) y amplitud (µV) de cada pico del VEMP por población, con
     * tone burst de 500 Hz por vía aérea. Copia de
     * populations[*].air_conduction.tone_burst.500Hz en
     * resources/vemp/normative_data.json.
     *
     * El signo sale del nombre del pico: p13 y p16 son positivos, n10 y n23
     * negativos. Por eso el cVEMP arranca hacia arriba y el oVEMP hacia
     * abajo, que es lo que los distingue de un vistazo.
     */
    public const VEMP_BASE = [
        'adult_male' => [
            'CVEMP' => ['p13' => [13.0, 120.0], 'n23' => [23.0, 170.0]],
            'OVEMP' => ['n10' => [10.0, 8.0], 'p16' => [16.0, 11.0]],
            'MVEMP' => ['p13' => [13.0, 40.0], 'n23' => [23.0, 55.0]],
        ],
        'adult_female' => [
            'CVEMP' => ['p13' => [12.8, 135.0], 'n23' => [22.5, 185.0]],
            'OVEMP' => ['n10' => [9.8, 8.5], 'p16' => [15.8, 11.5]],
            'MVEMP' => ['p13' => [12.8, 45.0], 'n23' => [22.5, 60.0]],
        ],
        'child' => [
            'CVEMP' => ['p13' => [11.5, 150.0], 'n23' => [21.0, 210.0]],
            'OVEMP' => ['n10' => [8.8, 10.0], 'p16' => [14.5, 13.0]],
            'MVEMP' => ['p13' => [11.5, 50.0], 'n23' => [21.0, 68.0]],
        ],
        'elderly' => [
            'CVEMP' => ['p13' => [14.5, 85.0], 'n23' => [24.5, 120.0]],
            'OVEMP' => ['n10' => [11.5, 5.5], 'p16' => [17.5, 8.0]],
            'MVEMP' => ['p13' => [14.5, 28.0], 'n23' => [24.5, 38.0]],
        ],
    ];

    /** Ancho de cada pico (ms). */
    public const VEMP_SIGMA = 3.2;

    /**
     * Trazo del VEMP a una intensidad: dos gaussianas de signo opuesto.
     *
     * La amplitud crece con el nivel de sensación sobre el umbral del
     * subtipo y se apaga en el umbral mismo, que es lo que el alumno tiene
     * que encontrar bajando de 5 en 5 dB.
     *
     * @param array<string,array{lat:float,amp:float}> $desviaciones
     * @return array<int,array{0:float,1:float}> pares [ms, µV]
     */
    public static function trazoVemp(
        string $subtipo,
        float $intensidad,
        float $umbral,
        array $desviaciones = [],
        float $hasta = 40.0,
        int $muestras = 200,
        string $poblacion = 'adult_female'
    ): array {
        $picos = self::picosVemp($subtipo, $intensidad, $umbral, $desviaciones, $poblacion);

        $pts = [];
        for ($n = 0; $n <= $muestras; $n++) {
            $t = $hasta * $n / $muestras;
            $v = 0.0;
            foreach ($picos as $pico) {
                $d = $t - $pico['lat'];
                $v += $pico['amp'] * exp(-($d * $d) / (2 * self::VEMP_SIGMA * self::VEMP_SIGMA));
            }
            $pts[] = [$t, $v];
        }
        return $pts;
    }

    /**
     * Latencia y amplitud (con signo) de cada pico del VEMP a una
     * intensidad. Separado del trazo para poder rotular los picos sobre la
     * curva: el nombre del pico es la mitad de lo que se lee en un VEMP.
     *
     * @param array<string,array{lat:float,amp:float}> $desviaciones
     * @return array<string,array{lat:float,amp:float}>
     */
    public static function picosVemp(
        string $subtipo,
        float $intensidad,
        float $umbral,
        array $desviaciones = [],
        string $poblacion = 'adult_female'
    ): array {
        $base = self::VEMP_BASE[$poblacion] ?? self::VEMP_BASE['adult_female'];
        $definicion = $base[$subtipo] ?? $base['CVEMP'];
        $sl = $intensidad - $umbral;
        // Por debajo del umbral no hay respuesta; encima crece y satura.
        $crecimiento = $sl < 0 ? 0.0 : 1 - exp(-$sl / 12);

        $out = [];
        foreach ($definicion as $nombre => [$lat0, $amp0]) {
            $signo = strncmp($nombre, 'n', 1) === 0 ? -1.0 : 1.0;
            $out[$nombre] = [
                'lat' => $lat0 + (float) ($desviaciones[$nombre]['lat'] ?? 0),
                'amp' => ($amp0 * $crecimiento + (float) ($desviaciones[$nombre]['amp'] ?? 0)) * $signo,
            ];
        }
        return $out;
    }
}
