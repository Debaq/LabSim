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
        'adult_male'       => ['I' => [1.47, 0.320], 'III' => [3.75, 0.370], 'V' => [5.68, 0.400]],
        'adult_female'     => ['I' => [1.46, 0.440], 'III' => [3.65, 0.470], 'V' => [5.54, 0.540]],
        'child'            => ['I' => [1.48, 0.239], 'III' => [3.50, 0.282], 'V' => [5.50, 0.410]],
        'toddler'          => ['I' => [1.52, 0.231], 'III' => [3.67, 0.270], 'V' => [5.80, 0.388]],
        'neonate'          => ['I' => [1.79, 0.171], 'III' => [4.56, 0.205], 'V' => [7.00, 0.299]],
        'elderly_male'     => ['I' => [1.83, 0.288], 'III' => [3.98, 0.333], 'V' => [5.85, 0.360]],
        'elderly_female'   => ['I' => [1.84, 0.396], 'III' => [3.84, 0.423], 'V' => [5.84, 0.486]],
    ];

    /**
     * Interpicos normativos del click por población (ms). Copia de
     * populations[*].air_conduction.click.interpeak en
     * resources/abr/normative_data.json.
     */
    public const CLICK_INTERPICOS = [
        'adult_male'       => ['I-III' => 2.28, 'III-V' => 1.93, 'I-V' => 4.21],
        'adult_female'     => ['I-III' => 2.19, 'III-V' => 1.89, 'I-V' => 4.08],
        'child'            => ['I-III' => 2.02, 'III-V' => 2.00, 'I-V' => 4.02],
        'toddler'          => ['I-III' => 2.15, 'III-V' => 2.13, 'I-V' => 4.28],
        'neonate'          => ['I-III' => 2.77, 'III-V' => 2.44, 'I-V' => 5.21],
        'elderly_male'     => ['I-III' => 2.15, 'III-V' => 1.87, 'I-V' => 4.02],
        'elderly_female'   => ['I-III' => 2.00, 'III-V' => 2.00, 'I-V' => 4.00],
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
    public const LAT_SHIFT_FACTOR = ['I' => 1.15, 'III' => 1.05, 'V' => 1.0];

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
     * SN10: el valle lento que sigue a la V (de acá sale la amplitud de V
     * medida pico-a-valle) y VII: el bump tardío chico que a veces ni
     * aparece. Las dos son geometría derivada de V, no ondas con su propio
     * crecimiento por SL -- por eso no están en AMP_GROWTH. Espejo de
     * SN10_SIGMA_MS/SN10_AMP_RATIO y del bloque VII en build_target_curve().
     */
    public const SN10_SIGMA_MS = 0.55;
    public const SN10_AMP_RATIO = 0.45;
    public const SN10_LAT_OFFSET = 0.9;
    public const VII_SIGMA = 0.40;
    public const VII_AMP_RATIO = 0.18;
    public const VII_LAT_OFFSET = 2.5;

    /**
     * Efecto de la tasa de estimulación (clics/s), anclado en RATE_REF (la
     * tasa a la que se miden los valores normativos: ahí no cambia nada).
     * Por encima la latencia crece lineal y la amplitud cae exponencial;
     * la I es la más sensible y la V la que mejor aguanta. Espejo de
     * RATE_REF/RATE_LAT_SLOPE/RATE_AMP_DECAY.
     */
    public const RATE_REF = 21.1;
    public const RATE_LAT_SLOPE = ['I' => 0.0025, 'III' => 0.0045, 'V' => 0.0060];
    public const RATE_AMP_DECAY = ['I' => 0.0060, 'III' => 0.0045, 'V' => 0.0035];

    /**
     * Un oído neural aguanta peor las tasas altas (fatiga de conducción):
     * multiplica el corrimiento de latencia y la caída de amplitud de
     * arriba. Espejo de NEURAL_RATE_FACTORS -- misma clave que
     * neural.sensibilidad_tasa.
     */
    public const RATE_NEURAL_FACTORES = [
        'normal' => [1.0, 1.0],
        'moderada' => [1.25, 1.6],
        'severa' => [1.5, 2.2],
    ];

    /**
     * Tasa "de estrés": la que en la clínica se sube a propósito para
     * desenmascarar fatiga de conducción (el hallazgo neural que a tasa
     * normal puede no verse). No se usa para dibujar nada en la ficha --
     * `ondasClick()` es sensible a la tasa (ver `$tasa` más abajo), pero
     * la pila del PDF solo se arma a RATE_REF. Queda acá como valor de
     * referencia para ejercitar esa sensibilidad en los tests.
     */
    public const TASA_ESTRES = 90.0;

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
     * Espejo exacto de ABRGenerator.latency_intensity_shift: 0.12 ms/10 dB
     * por encima de 70 dB, 0.28 entre 70 y 50, y 0.50 de 50 para abajo
     * (Hood F26, contrastado con Delgado F22).
     */
    public static function corrimientoLatencia(float $intensidad): float
    {
        if ($intensidad >= 70) {
            return (80 - $intensidad) / 10 * 0.12;
        }
        if ($intensidad >= 50) {
            return 0.12 + (70 - $intensidad) / 10 * 0.28;
        }
        return 0.12 + 2 * 0.28 + (50 - $intensidad) / 10 * 0.50;
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
        // Espejo de ABR_generator.select_population. El tramo de 1 a 3 años
        // tiene bloque propio (la vía todavía madura) y el sexo separa de
        // los 18 en adelante, adulto mayor incluido.
        if ($edad < 1) {
            return 'neonate';
        }
        if ($edad < 3) {
            return 'toddler';
        }
        if ($edad < 18) {
            return 'child';
        }
        if ($edad >= 60) {
            return $genero === 0 ? 'elderly_male' : 'elderly_female';
        }
        return $genero === 0 ? 'adult_male' : 'adult_female';
    }

    /**
     * Latencia y amplitud de cada onda del click a una intensidad dada.
     *
     * Incluye, además de I/III/V, SN10 y VII -- geometría derivada de la V
     * final (después de tasa, tipo y patrón neural), así que siempre van
     * pegadas a ella. `trazo()` las suma igual que a cualquier otra: no son
     * ondas que haya que tratar aparte.
     *
     * @param array<string,mixed> $neural patrón retrococlear ya normalizado
     * @param array<string,array{lat:float,amp:float}> $desviaciones del caso
     * @param float $tasa clics/s del estímulo. RATE_REF (21.1) es donde
     *        están medidos los valores normativos -- ahí no cambia nada.
     * @return array<string,array{lat:float,amp:float,sigma:float}>
     */
    public static function ondasClick(
        float $intensidad,
        float $umbral,
        string $tipo,
        array $neural,
        array $desviaciones = [],
        string $poblacion = 'adult_female',
        float $tasa = self::RATE_REF
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

        // Tasa alta = fatiga de conducción: en un oído neural pega mucho
        // más fuerte (RATE_NEURAL_FACTORES), en cualquier otro pega el
        // corrimiento base nomás.
        $dTasa = $tasa - self::RATE_REF;
        $tasaLatGain = 1.0;
        $tasaAmpGain = 1.0;
        if ($esNeural && abs($dTasa) > 0.001) {
            $sensibilidadTasa = (string) ($neural['sensibilidad_tasa'] ?? 'severa');
            [$tasaLatGain, $tasaAmpGain] = self::RATE_NEURAL_FACTORES[$sensibilidadTasa]
                ?? self::RATE_NEURAL_FACTORES['severa'];
        }

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

            if (abs($dTasa) > 0.001) {
                $lat += self::RATE_LAT_SLOPE[$onda] * $dTasa * $tasaLatGain;
                $decaimiento = exp(-self::RATE_AMP_DECAY[$onda] * $tasaAmpGain * $dTasa);
                // Techo bajo (tasas lentas no suben mucho la amplitud) y
                // piso: ni a tasas muy altas la respuesta desaparece del
                // todo en un oído normal.
                $amp *= max(0.15, min(1.20, $decaimiento));
            }

            $out[$onda] = ['lat' => $lat, 'amp' => max(0.0, $amp), 'sigma' => $sigma];
        }

        // SN10 y VII: geometría derivada de la V YA final (con tasa, tipo y
        // patrón neural aplicados) -- por eso van después del loop y no dentro.
        $v = $out['V'];
        $out['SN10'] = [
            'lat' => $v['lat'] + self::SN10_LAT_OFFSET + $v['sigma'] * 2,
            'amp' => -$v['amp'] * self::SN10_AMP_RATIO,
            'sigma' => self::SN10_SIGMA_MS * ($v['sigma'] / self::SIGMA['V']),
        ];
        $out['VII'] = [
            'lat' => $v['lat'] + self::VII_LAT_OFFSET,
            'amp' => $v['amp'] * self::VII_AMP_RATIO,
            'sigma' => self::VII_SIGMA,
        ];

        return $out;
    }

    /**
     * Amplitud (µV) del ruido residual de fondo (EEG+EMG ya promediados):
     * lo que le queda a un registro bien hecho después de promediar.
     * Espejo aproximado de NOISE_FLOOR_UV -- el generador real llega ahí
     * simulando barrido por barrido; acá alcanza con una textura del
     * mismo orden, no la simulación de la promediación entera (el PDF
     * muestra el resultado final, no el proceso).
     */
    public const RUIDO_AMPLITUD_UV = 0.05;

    /**
     * Ruido de fondo determinístico (misma semilla = mismo ruido, para que
     * el PDF sea reproducible al re-generarse) pero que se vea orgánico: no
     * es blanco puro -- es una suma de pocas sinusoides con más peso en las
     * graves, aproximando el EEG (pink) + EMG del generador real sin FFT.
     * Ruido blanco puro en 240 muestras se ve como estática, no como un
     * registro.
     *
     * @return array<int,float> $muestras+1 valores, mismo largo que trazo()
     */
    private static function ruidoDeFondo(int $semilla, int $muestras): array
    {
        // LCG de 32 bits (Numerical Recipes): 2^32 * 1664525 no se pasa de
        // los 64 bits con signo de un int de PHP -- un finalizador tipo
        // Murmur (XOR + multiplicar por una constante de 32 bits) SÍ se
        // pasa, el producto cae en punto flotante y el & que sigue tira
        // "not representable as an int". Determinístico igual, sin
        // depender de mt_srand (que es un estado GLOBAL de PHP y pisaría
        // cualquier otro random() del proceso).
        $estado = $semilla % 4294967296;
        if ($estado < 0) {
            $estado += 4294967296;
        }
        $siguiente = static function () use (&$estado): float {
            $estado = ($estado * 1664525 + 1013904223) % 4294967296;
            return $estado / 4294967296;
        };

        $componentes = [
            ['ciclos' => 0.6, 'peso' => 1.00],
            ['ciclos' => 1.3, 'peso' => 0.80],
            ['ciclos' => 2.4, 'peso' => 0.55],
            ['ciclos' => 4.5, 'peso' => 0.35],
            ['ciclos' => 8.0, 'peso' => 0.20],
        ];
        $fases = [];
        $pesoTotal = 0.0;
        foreach ($componentes as $c) {
            $fases[] = $siguiente() * 2 * M_PI;
            $pesoTotal += $c['peso'];
        }

        $ruido = [];
        for ($n = 0; $n <= $muestras; $n++) {
            $v = 0.0;
            foreach ($componentes as $i => $c) {
                $v += $c['peso'] * sin(2 * M_PI * $c['ciclos'] * $n / $muestras + $fases[$i]);
            }
            $ruido[] = $v / $pesoTotal;
        }
        return $ruido;
    }

    /**
     * Trazo del click: suma de gaussianas centradas en cada onda, muestreada
     * de 0 a $hasta ms. Es la misma construcción del generador ("ondas =
     * suma de gaussianas centradas en cada latencia, no Bézier").
     *
     * Con `$ruidoSemilla` se le suma una textura de fondo determinística
     * (RUIDO_AMPLITUD_UV): sin ruido, dos pasadas al mismo nivel salían
     * pixel a pixel iguales, que no es como se ve un registro real -- y una
     * curva "sin respuesta" perfectamente plana tampoco. Semillas
     * distintas para las dos réplicas del mismo nivel (ver
     * CaseSheetPdf::nivelesAbr()): son dos pasadas, no la misma dibujada
     * dos veces.
     *
     * @param array<string,array{lat:float,amp:float,sigma:float}> $ondas
     * @return array<int,array{0:float,1:float}> pares [ms, µV]
     */
    public static function trazo(
        array $ondas,
        float $hasta = 12.0,
        int $muestras = 240,
        ?int $ruidoSemilla = null
    ): array {
        $ruido = $ruidoSemilla === null ? null : self::ruidoDeFondo($ruidoSemilla, $muestras);

        $pts = [];
        for ($n = 0; $n <= $muestras; $n++) {
            $t = $hasta * $n / $muestras;
            $v = 0.0;
            foreach ($ondas as $onda) {
                $d = $t - $onda['lat'];
                $v += $onda['amp'] * exp(-($d * $d) / (2 * $onda['sigma'] * $onda['sigma']));
            }
            if ($ruido !== null) {
                $v += $ruido[$n] * self::RUIDO_AMPLITUD_UV;
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
        // Un umbral por encima del tope de la escala significa que no hubo
        // respuesta en todo el barrido: la serie es el nivel máximo, plano.
        // Dibujar un trazo rotulado "115 dB" mostraría un nivel que el
        // equipo no puede dar.
        if ($umbral >= $maximo) {
            return [$maximo];
        }

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
    /**
     * El ABR separa más poblaciones que el VEMP: tiene bloque de 1 a 3 años
     * y parte el adulto mayor por sexo. La tabla del VEMP no, así que acá se
     * traduce en vez de caer al fallback de adulto -- un chico de 2 años y
     * un hombre de 70 se dibujaban con la p13 de una mujer adulta.
     */
    private const VEMP_POP_ALIAS = [
        'toddler' => 'child',
        'elderly_male' => 'elderly',
        'elderly_female' => 'elderly',
    ];

    private static function poblacionVemp(string $poblacion): string
    {
        return self::VEMP_POP_ALIAS[$poblacion] ?? $poblacion;
    }

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

    /**
     * Fracción de la amplitud normativa por debajo de la cual se considera
     * que NO hay respuesta: el trazo no se marca y la tabla dice "no se
     * observa" en vez de un número. Rotular un pico sobre una línea plana
     * enseña a marcar lo que no está.
     */
    public const VEMP_MIN_FRACCION = 0.15;

    /**
     * ¿Hay respuesta a esa intensidad? Se compara contra la amplitud que
     * daría el mismo subtipo con la respuesta saturada, así el criterio vale
     * igual para el cervical (cientos de µV) que para el ocular (unidades).
     *
     * @param array<string,array{lat:float,amp:float}> $picos
     */
    public static function hayRespuestaVemp(string $subtipo, array $picos, string $poblacion = 'adult_female'): bool
    {
        $base = self::VEMP_BASE[self::poblacionVemp($poblacion)] ?? self::VEMP_BASE['adult_female'];
        $definicion = $base[$subtipo] ?? $base['CVEMP'];
        $plena = 0.0;
        foreach ($definicion as [, $amp]) {
            $plena += abs((float) $amp);
        }
        $medida = 0.0;
        foreach ($picos as $pico) {
            $medida += abs((float) $pico['amp']);
        }
        return $plena > 0 && $medida / $plena >= self::VEMP_MIN_FRACCION;
    }

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
        $base = self::VEMP_BASE[self::poblacionVemp($poblacion)] ?? self::VEMP_BASE['adult_female'];
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
