<?php

/**
 * Perfil auditivo del caso: el sitio de la lesión, y las proyecciones que
 * salen de él hacia cada examen.
 *
 * El audiograma (Aerea/Osea) YA dice cuánta pérdida hay y cuánta es
 * conductiva, frecuencia por frecuencia. Lo único que no puede decir es
 * dónde está la lesión dentro del componente sensorioneural -- cóclea
 * (células ciliadas externas) o retrococlear -- y con qué patrón
 * electrofisiológico. Eso, y solo eso, es lo que agrega el perfil:
 * `cce_pct` y `retro`.
 *
 * Por eso acá NO se guardan `perdida[hz]` ni `gap[hz]`: serían una segunda
 * fuente de verdad frente a Aerea/Osea y se desincronizarían el primer día
 * que alguien edite el audiograma. Se derivan en decompose().
 *
 * Todo en esta clase es función pura sobre arrays: no toca PDO, ni $_POST,
 * ni cases.data directamente (salvo normalize(), que solo lee). Así se
 * puede testear sin base de datos ni servidor -- ver labsim_backend/tests.
 *
 * Ver ROADMAP.md en la raíz del repo para el plan completo.
 */
// Las frecuencias, los defaults del patrón retro y las bandas de la OEA son
// las de CaseBuilder: el perfil proyecta sobre ellas, no define otras.
require_once __DIR__ . '/CaseBuilder.php';

final class CaseProfile
{
    /** Versión del shape de `cases.data['Perfil']`. */
    public const VERSION = 1;

    /**
     * Qué proporción del componente SENSORIONEURAL es coclear (CCE).
     * 100 = coclear puro (la OEA muere con la pérdida, hay reclutamiento);
     * 0 = retrococlear puro (la cóclea está viva: OEA presentes con umbral
     * elevado, que es la neuropatía auditiva).
     *
     * Default 100 y no 50: la inmensa mayoría de las hipoacusias
     * sensorioneurales son cocleares, y es el valor con el que un caso
     * viejo (sin perfil) se comporta igual que antes.
     */
    public const DEFAULT_CCE_PCT = 100.0;

    /**
     * Módulos que pueden proyectarse desde el perfil. `false` = el docente
     * escribe ese examen a mano, que es como funciona todo hoy y como
     * quedan TODOS los casos ya guardados (ver normalize()).
     *
     * Es el mismo mecanismo que ya existe en el formulario para
     * Rinne/Weber (`acumetria_auto`) y SDT/SRT (`sdt_auto`/`srt_auto`): no
     * se inventa nada, se generaliza.
     *
     * - abr:     tipo de patología y umbral por estímulo (aéreo y óseo).
     * - eoas:    tipo y desviación por frecuencia de la OEA.
     * - reflex:  umbrales del reflejo acústico, ipsi y contra.
     * - recruit: supraliminares -- reclutamiento (Fowler, SISI) y
     *            deterioro tonal (Carhart/Stat/Rosemberg). Van juntas
     *            porque miden el mismo eje desde los dos lados: el
     *            reclutamiento es el signo de la lesión de CCE y el
     *            deterioro tonal el del nervio.
     */
    public const AUTO_MODULES = ['abr', 'eoas', 'reflex', 'recruit'];

    /** Frecuencias sobre las que se promedia para clasificar el oído (Hz). */
    public const CORE_FREQS = [500, 1000, 2000, 4000];

    /**
     * Pesos por estímulo del ABR: qué zona coclear representa cada uno.
     * Las claves son EXACTAMENTE las de STIM_MAP en src/abr/ABR_generator.py
     * (click / ls_chirp / ce_chirp / tone_burst_<freq>), así el cliente
     * indexa el resultado sin traducir nada.
     *
     * El burst es frecuencia-específico por definición. El click no: su
     * respuesta la domina la base coclear (2-4 kHz), y por eso un click
     * normal no descarta una pérdida en graves -- que es justamente el
     * error que el alumno tiene que aprender a no cometer. El chirp
     * compensa el retardo de la onda viajera y sincroniza también el ápex,
     * así que pesa más parejo hacia los graves que el click.
     */
    public const STIM_WEIGHTS = [
        'tone_burst_500Hz'  => [500 => 1.0],
        'tone_burst_1000Hz' => [1000 => 1.0],
        'tone_burst_2000Hz' => [2000 => 1.0],
        'tone_burst_4000Hz' => [4000 => 1.0],
        'click'             => [2000 => 0.35, 3000 => 0.30, 4000 => 0.35],
        'ce_chirp'          => [500 => 0.15, 1000 => 0.20, 2000 => 0.25, 4000 => 0.40],
        'ls_chirp'          => [500 => 0.15, 1000 => 0.20, 2000 => 0.25, 4000 => 0.40],
    ];

    /**
     * Corrección conductual -> electrofisiológico, en dB: cuánto MÁS alto
     * lee el umbral del ABR (dB nHL) que el umbral tonal real (dB HL).
     *
     * Son los factores de corrección de la práctica clínica (Stapells y
     * cía.): para estimar el audiograma a partir del ABR hay que RESTAR
     * estos valores del umbral nHL obtenido. Acá se usan al revés, porque
     * vamos del caso (que se define en dB HL, el audiograma) a lo que el
     * equipo va a mostrar.
     *
     * Que un oído de 0 dB HL dé 20 dB nHL en burst de 500 y 10 en click no
     * es un error: es el hallazgo. La conversión nHL->eHL es contenido de
     * la asignatura, no plomería.
     */
    public const STIM_NHL_CORRECTION = [
        'tone_burst_500Hz'  => 20.0,
        'tone_burst_1000Hz' => 15.0,
        'tone_burst_2000Hz' => 10.0,
        'tone_burst_4000Hz' => 5.0,
        'click'             => 10.0,
        // El chirp sincroniza mejor toda la partición coclear: misma
        // respuesta con menos nivel, umbral algo más bajo que el click.
        'ce_chirp'          => 5.0,
        'ls_chirp'          => 5.0,
    ];

    /** Paso del umbral ABR (los equipos van de 5 en 5 dB). */
    public const ABR_STEP_DB = 5;
    public const ABR_MAX_DB = 120;

    /**
     * Umbrales de clasificación del oído (dB, promedio en CORE_FREQS).
     * GAP_CONDUCTIVO: gap desde el cual la pérdida se llama de transmisión.
     * SN_NORMAL: pérdida ósea hasta la cual el oído sigue siendo normal
     * (mismo criterio que CaseBuilder::NORMAL_MAX_UMBRAL).
     * CCE_COCLEAR: proporción de CCE desde la cual el cuadro se lee coclear.
     */
    public const GAP_CONDUCTIVO_DB = 15.0;
    public const SN_NORMAL_DB = 25.0;
    public const CCE_COCLEAR_PCT = 60.0;

    /**
     * Ley de atenuación de la OEA. Espejo de oae_attenuation_db() en
     * src/oae/generators/base.py -- si cambia allá, cambia acá.
     * Coclear: 1.2 dB de atenuación por dB de pérdida CCE sobre 15 dB HL.
     * Conductivo: 2.0 dB/dB sobre 8 dB, porque atenúa la ida Y la vuelta.
     */
    public const OAE_CCE_SLOPE = 1.2;
    public const OAE_CCE_KNEE_DB = 15.0;
    public const OAE_GAP_SLOPE = 2.0;
    public const OAE_GAP_KNEE_DB = 8.0;
    public const OAE_MAX_ATTEN_DB = 45.0;

    /**
     * Cuadros clínicos para sortear un caso coherente de una sola vez.
     *
     * Reemplazan al par de "Autocompletar" independientes de ABR y EOA, que
     * sorteaban cada uno por su lado y ya podían contradecirse entre sí (uno
     * podía dejar el ABR coclear y el otro la OEA neural en el mismo oído).
     * Acá se sortea EL OÍDO -- forma del audiograma, gap, sitio de la
     * lesión -- y de ahí sale todo lo demás por proyección.
     *
     * `sn_shape`/`gap_shape` son formas relativas en dB por frecuencia; la
     * escala se sortea dentro de `*_scale`, así dos casos del mismo cuadro
     * no salen calcados (mismo criterio que EOAS_AUTOFILL_GRADES, y la razón
     * de no fijar un valor "correcto" en lo que el alumno debe aprender a
     * leer).
     *
     * `lateralidad`: 'bilateral' carga los dos oídos, 'unilateral' sortea
     * cuál y deja el otro sano -- que es lo que hace falta para que el IT5,
     * el Weber y el Fowler tengan con qué comparar.
     */
    public const SCENARIOS = [
        'normal' => [
            'label' => 'Normal',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 5, 3000 => 5, 4000 => 5, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'bilateral',
        ],
        'coclear_agudos' => [
            'label' => 'Coclear en agudos (descendente)',
            'sn_shape' => [125 => 0, 250 => 0, 500 => 5, 1000 => 10, 2000 => 25, 3000 => 35, 4000 => 45, 6000 => 50, 8000 => 55],
            'sn_scale' => [0.6, 1.5], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'bilateral',
        ],
        'muesca_4k' => [
            'label' => 'Muesca en 4 kHz (trauma acústico)',
            'sn_shape' => [125 => 0, 250 => 0, 500 => 0, 1000 => 5, 2000 => 10, 3000 => 30, 4000 => 45, 6000 => 35, 8000 => 20],
            'sn_scale' => [0.7, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'bilateral',
        ],
        'coclear_plana' => [
            'label' => 'Coclear plana',
            'sn_shape' => [125 => 40, 250 => 40, 500 => 45, 1000 => 45, 2000 => 45, 3000 => 45, 4000 => 50, 6000 => 50, 8000 => 50],
            'sn_scale' => [0.6, 1.5], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'bilateral',
        ],
        'conductiva' => [
            'label' => 'Conductiva (otitis media / otoesclerosis)',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 10, 3000 => 10, 4000 => 10, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.2],
            'gap_shape' => [125 => 40, 250 => 40, 500 => 38, 1000 => 32, 2000 => 28, 3000 => 26, 4000 => 25, 6000 => 25, 8000 => 25],
            'gap_scale' => [0.5, 1.2],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
        ],
        'mixta' => [
            'label' => 'Mixta',
            'sn_shape' => [125 => 25, 250 => 25, 500 => 30, 1000 => 30, 2000 => 35, 3000 => 40, 4000 => 45, 6000 => 45, 8000 => 45],
            'sn_scale' => [0.7, 1.3],
            'gap_shape' => [125 => 30, 250 => 30, 500 => 28, 1000 => 25, 2000 => 22, 3000 => 20, 4000 => 20, 6000 => 20, 8000 => 20],
            'gap_scale' => [0.6, 1.1],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'unilateral',
        ],
        'retrococlear' => [
            'label' => 'Retrococlear (schwannoma vestibular)',
            'sn_shape' => [125 => 10, 250 => 10, 500 => 15, 1000 => 20, 2000 => 30, 3000 => 40, 4000 => 45, 6000 => 50, 8000 => 55],
            'sn_scale' => [0.5, 1.2], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [10, 35], 'retro' => 'schwannoma', 'lateralidad' => 'unilateral',
        ],
        'neuropatia' => [
            'label' => 'Neuropatía auditiva / desincronía (ANSD)',
            'sn_shape' => [125 => 45, 250 => 45, 500 => 50, 1000 => 50, 2000 => 50, 3000 => 50, 4000 => 55, 6000 => 55, 8000 => 55],
            'sn_scale' => [0.6, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [0, 10], 'retro' => 'ansd', 'lateralidad' => 'bilateral',
        ],
    ];

    /**
     * Perfil normalizado a partir de un `cases.data` cualquiera.
     *
     * Un caso guardado antes de que el perfil existiera no trae la clave:
     * se infiere `cce_pct` de la patología que ya tiene cargada (ver
     * inferCcePct) y TODOS los `auto` quedan apagados. Es el criterio de
     * no-regresión: abrir un caso viejo y volver a guardarlo tiene que
     * producir el mismo JSON que antes.
     *
     * @param array<string,mixed> $data cases.data
     * @return array{version:int, OD:array, OI:array, auto:array<string,bool>}
     */
    public static function normalize(array $data): array
    {
        $perfil = is_array($data['Perfil'] ?? null) ? $data['Perfil'] : [];
        $tienePerfil = isset($perfil['version']);

        $out = ['version' => self::VERSION];
        foreach (['OD', 'OI'] as $lado) {
            $ladoPerfil = is_array($perfil[$lado] ?? null) ? $perfil[$lado] : [];
            $abrLado = is_array(($data['ABR'] ?? [])[$lado] ?? null) ? $data['ABR'][$lado] : [];
            $eoasLado = is_array(($data['EOAS'] ?? [])[$lado] ?? null) ? $data['EOAS'][$lado] : [];

            $cce = $ladoPerfil['cce_pct'] ?? null;
            $retro = is_array($ladoPerfil['retro'] ?? null) ? $ladoPerfil['retro'] : null;

            $out[$lado] = [
                'cce_pct' => $cce !== null
                    ? self::clamp((float) $cce, 0.0, 100.0)
                    : self::inferCcePct($abrLado, $eoasLado),
                // Mientras el bloque retrococlear siga viviendo en el tab
                // ABR (hasta la fase 3 del roadmap), la fuente es
                // ABR[lado]['neural'] -- son los mismos inputs del
                // formulario, no dos verdades distintas.
                'retro' => self::normalizeRetro($retro ?? (is_array($abrLado['neural'] ?? null) ? $abrLado['neural'] : [])),
            ];
        }

        $auto = is_array($perfil['auto'] ?? null) ? $perfil['auto'] : [];
        $out['auto'] = [];
        foreach (self::AUTO_MODULES as $modulo) {
            // Sin perfil guardado, todo en manual: un caso viejo no puede
            // cambiar de comportamiento por abrirlo.
            $out['auto'][$modulo] = $tienePerfil && !empty($auto[$modulo]);
        }

        return $out;
    }

    /**
     * Patrón retrococlear completo a partir de lo que venga, rellenando
     * con los defaults que comparte con el generador
     * (NEURAL_PARAM_DEFAULTS en src/abr/ABR_generator.py).
     *
     * @param array<string,mixed> $retro
     * @return array<string,mixed>
     */
    public static function normalizeRetro(array $retro): array
    {
        $out = [];
        foreach (CaseBuilder::ABR_NEURAL_DEFAULTS as $clave => $default) {
            $valor = $retro[$clave] ?? $default;
            $out[$clave] = is_string($default) ? (string) $valor : (float) $valor;
        }
        return $out;
    }

    /**
     * `cce_pct` de un caso viejo, a partir de la patología ya cargada.
     *
     * La EOA es la que manda: es el examen que separa cóclea de nervio.
     * Un oído marcado 'neural' en EOA tiene OEA conservadas -> cóclea
     * viva -> el componente sensorioneural es retrococlear. Todo lo demás
     * (coclear, transmisión, normal) se comporta como coclear puro, que es
     * lo que hacía el generador antes de que esto existiera.
     *
     * @param array<string,mixed> $abrEar  cases.data['ABR'][lado]
     * @param array<string,mixed> $eoasEar cases.data['EOAS'][lado]
     */
    public static function inferCcePct(array $abrEar, array $eoasEar): float
    {
        if (($eoasEar['type'] ?? null) === 'neural') {
            return 0.0;
        }
        if (($abrEar['type'] ?? null) === 'neural' && !isset($eoasEar['type'])) {
            // ABR neural sin EOA configurada: el caso solo dice
            // "retrococlear", no hay dato que lo contradiga.
            return 0.0;
        }
        return self::DEFAULT_CCE_PCT;
    }

    /**
     * Descompone el audiograma de un oído en los componentes que las
     * proyecciones necesitan. Devuelve arrays indexados por Hz.
     *
     * @param array<int,array{0:int|float,1:int|float}> $airPairs  cases.data['Aerea']
     * @param array<int,array{0:int|float,1:int|float}> $bonePairs cases.data['Osea']
     * @param int $side 0 = OD, 1 = OI (mismo orden que los pares)
     * @return array{air:array<int,float>, bone:array<int,float>, gap:array<int,float>,
     *               sn:array<int,float>, cce:array<int,float>, retro_sn:array<int,float>}
     */
    public static function decompose(array $airPairs, array $bonePairs, int $side, float $ccePct): array
    {
        $ccePct = self::clamp($ccePct, 0.0, 100.0);
        $out = ['air' => [], 'bone' => [], 'gap' => [], 'sn' => [], 'cce' => [], 'retro_sn' => []];

        foreach (CaseBuilder::FREQUENCIES as $i => $hz) {
            $air = (float) ($airPairs[$i][$side] ?? 0);
            // Sin ósea cargada, el oído se lee sensorioneural puro (gap 0),
            // que es lo conservador: inventar un gap cambiaría el examen.
            $bone = (float) ($bonePairs[$i][$side] ?? $air);
            // Una ósea PEOR que la aérea no existe: es ruido de carga del
            // formulario (o un caso viejo con la ósea sin tocar). El gap se
            // trunca en 0 y la ósea se toma como el aéreo.
            $bone = min($bone, $air);

            $sn = $bone;
            $cce = $sn * $ccePct / 100.0;

            $out['air'][$hz] = $air;
            $out['bone'][$hz] = $bone;
            $out['gap'][$hz] = $air - $bone;
            $out['sn'][$hz] = $sn;
            $out['cce'][$hz] = $cce;
            $out['retro_sn'][$hz] = $sn - $cce;
        }

        return $out;
    }

    /**
     * Umbral del ABR por estímulo, en dB nHL.
     *
     * Es la proyección que resuelve el problema que originó todo esto: sin
     * ella, `cases.data['ABR'][lado]['umbral']` es un escalar y una
     * hipoacusia descendente responde igual a un burst de 500 Hz que a uno
     * de 4 kHz (el estímulo solo movía latencias vía get_baseline_values).
     *
     * En vía ósea se usa el umbral óseo, con lo cual el gap conductivo del
     * ABR sale del audiograma solo: no hace falta ningún campo nuevo.
     *
     * @param array $decomp Salida de decompose()
     * @param string $pathway 'air_conduction' | 'bone_conduction'
     * @return array<string,int> clave de STIM_MAP -> dB nHL
     */
    public static function abrThresholds(array $decomp, string $pathway = 'air_conduction'): array
    {
        $curva = $pathway === 'bone_conduction' ? $decomp['bone'] : $decomp['air'];
        $out = [];
        foreach (self::STIM_WEIGHTS as $stim => $pesos) {
            $suma = 0.0;
            $peso = 0.0;
            foreach ($pesos as $hz => $w) {
                $nivel = self::levelAt($curva, (float) $hz);
                if ($nivel === null) {
                    continue;
                }
                $suma += $nivel * $w;
                $peso += $w;
            }
            $hl = $peso > 0 ? $suma / $peso : 0.0;
            $nhl = $hl + self::STIM_NHL_CORRECTION[$stim];
            $out[$stim] = (int) self::clamp(
                round($nhl / self::ABR_STEP_DB) * self::ABR_STEP_DB,
                0.0,
                (float) self::ABR_MAX_DB
            );
        }
        return $out;
    }

    /**
     * Nivel de una curva (array Hz => dB) en una frecuencia cualquiera,
     * interpolando en log-frecuencia si esa frecuencia no está medida.
     *
     * Hace falta porque las frecuencias de la OEA (EOAS_FREQS incluye
     * 1500 Hz) no son las del audiograma (FREQUENCIES no lo tiene). Fuera
     * de rango se extiende con el extremo más cercano, que es lo que hace
     * el ojo clínico al leer un audiograma.
     *
     * @param array<int,float> $curva
     */
    public static function levelAt(array $curva, float $hz): ?float
    {
        if ($curva === []) {
            return null;
        }
        if (isset($curva[(int) $hz])) {
            return (float) $curva[(int) $hz];
        }
        $freqs = array_keys($curva);
        sort($freqs);
        if ($hz <= $freqs[0]) {
            return (float) $curva[$freqs[0]];
        }
        $ultimo = $freqs[count($freqs) - 1];
        if ($hz >= $ultimo) {
            return (float) $curva[$ultimo];
        }
        for ($i = 0; $i < count($freqs) - 1; $i++) {
            [$lo, $hi] = [$freqs[$i], $freqs[$i + 1]];
            if ($hz > $lo && $hz < $hi) {
                $t = (log($hz, 2) - log($lo, 2)) / (log($hi, 2) - log($lo, 2));
                return (float) $curva[$lo] + $t * ((float) $curva[$hi] - (float) $curva[$lo]);
            }
        }
        return (float) $curva[$ultimo];
    }

    /**
     * Tipo de patología del oído (las mismas 4 claves que usan hoy los
     * selectores de ABR/EOA), derivado del audiograma + `cce_pct`.
     *
     * El orden importa: primero el gap (una conductiva pura se lee como
     * transmisión aunque la ósea esté impecable), después el umbral, y
     * recién ahí se pregunta dónde está la lesión sensorioneural.
     *
     * @param array $decomp Salida de decompose()
     * @param array<string,mixed> $retro Patrón retrococlear (ver normalizeRetro)
     */
    public static function derivedType(array $decomp, float $ccePct, array $retro = []): string
    {
        // Máximo y no promedio: una hipoacusia descendente con 500 y 1000
        // conservados promedia dentro de lo normal y se clasificaba como
        // oído sano, que es exactamente el caso que el perfil existe para
        // representar. Un oído es normal solo si NINGUNA frecuencia se sale.
        $gap = self::coreMax($decomp['gap']);
        $sn = self::coreMax($decomp['sn']);

        if ($gap >= self::GAP_CONDUCTIVO_DB) {
            return 'transmission';
        }
        if ($sn <= self::SN_NORMAL_DB && !self::retroActivo($retro)) {
            return 'normal';
        }
        if (self::retroActivo($retro) && $ccePct < self::CCE_COCLEAR_PCT) {
            return 'neural';
        }
        if ($ccePct >= self::CCE_COCLEAR_PCT) {
            return 'coclear';
        }
        return 'neural';
    }

    /**
     * ¿El patrón retrococlear cargado dice algo, o son los defaults?
     *
     * Los defaults de ABR_NEURAL_DEFAULTS no son "sin hallazgo" (i_iii y
     * iii_v arrancan en 0.2 ms, que es variabilidad normal): lo que marca
     * un cuadro retrococlear es superar eso, bloquear ondas, o cargar
     * desincronía.
     *
     * @param array<string,mixed> $retro
     */
    public static function retroActivo(array $retro): bool
    {
        if ($retro === []) {
            return false;
        }
        $r = self::normalizeRetro($retro);
        if ($r['bloqueo'] !== 'ninguno' || $r['desincronia'] !== 'ninguna'
            || $r['microfonica'] !== 'normal') {
            return true;
        }
        $base = CaseBuilder::ABR_NEURAL_DEFAULTS;
        foreach (['i_iii_ms', 'iii_v_ms', 'global_delay_ms'] as $clave) {
            if ((float) $r[$clave] > (float) $base[$clave] + 1e-9) {
                return true;
            }
        }
        return (float) $r['v_i_factor'] < (float) $base['v_i_factor'] - 1e-9;
    }

    /**
     * Desviación de la OEA por frecuencia (dB por DEBAJO de lo esperado,
     * mismo criterio "más número, peor oído" que el tab EOA).
     *
     * Solo el componente CCE y el gap atenúan la emisión. `retro_sn` NO
     * entra: la cóclea está viva. Con eso la neuropatía sale sola del
     * modelo -- OEA presentes con umbral elevado, ABR desarmado -- en vez
     * de tener que cargarla a mano en dos tabs y esperar que no se
     * contradigan.
     *
     * @param array $decomp Salida de decompose()
     * @return array<string,float> Hz (string, como en el form) -> dB
     */
    public static function oaeDeviations(array $decomp): array
    {
        $out = [];
        foreach (CaseBuilder::EOAS_FREQS as $hz) {
            $cce = self::levelAt($decomp['cce'], (float) $hz) ?? 0.0;
            $gap = self::levelAt($decomp['gap'], (float) $hz) ?? 0.0;
            $atten = max(0.0, $cce - self::OAE_CCE_KNEE_DB) * self::OAE_CCE_SLOPE
                   + max(0.0, $gap - self::OAE_GAP_KNEE_DB) * self::OAE_GAP_SLOPE;
            $out[(string) $hz] = round(min($atten, self::OAE_MAX_ATTEN_DB), 1);
        }
        return $out;
    }

    /**
     * Reclutamiento derivado de `cce_pct`: patrón de Fowler, SISI y el
     * flag de reclutamiento, coherentes entre sí.
     *
     * El reclutamiento es el hallazgo de la lesión de CCE (la cóclea
     * dañada pierde su compresión y la sonoridad crece de golpe). Un oído
     * retrococlear con la misma pérdida no lo tiene -- ese contraste es
     * exactamente lo que Fowler y el SISI existen para mostrar.
     *
     * Devuelve el valor representativo, sin azar: el sorteo del caso
     * (fase 6 del roadmap) le agrega el jitter, no esta función, que tiene
     * que ser determinística para poder testearse.
     *
     * @return array{pattern:string, sisi_pct:int, recruit:bool}
     */
    public static function recruitment(float $ccePct, array $decomp): array
    {
        // Sin pérdida sensorioneural no hay reclutamiento que mostrar, por
        // más "coclear" que diga el perfil: no hay CCE dañadas.
        // Máximo, por lo mismo que derivedType: el reclutamiento de una
        // descendente se busca en la frecuencia dañada, no en el promedio.
        if (self::coreMax($decomp['sn']) <= self::SN_NORMAL_DB) {
            return ['pattern' => 'none', 'sisi_pct' => 0, 'recruit' => false];
        }
        if ($ccePct >= 80.0) {
            return ['pattern' => 'complete', 'sisi_pct' => 90, 'recruit' => true];
        }
        if ($ccePct >= 50.0) {
            return ['pattern' => 'partial', 'sisi_pct' => 50, 'recruit' => true];
        }
        return ['pattern' => 'none', 'sisi_pct' => 10, 'recruit' => false];
    }

    // ---------------------------------------------------------------
    // Reflejo acustico
    // ---------------------------------------------------------------

    /**
     * Frecuencias de cada modo, en el orden de las filas de
     * cases.data['Reflex'] (ver reflex_stimulus() en Z.py, que indexa
     * ['500','1000','2000','4000','NBN']). 'NBN' es ruido de banda
     * estrecha: no tiene una frecuencia, se juzga sobre el promedio.
     */
    public const REFLEX_FREQS_IPSI = [500, 1000, 2000, 4000];
    public const REFLEX_FREQS_CONTRA = [500, 1000, 2000, 4000, 'NBN'];

    /** Valor con el que el caso marca "reflejo ausente" (fuera de escala). */
    public const REFLEX_ABSENT_DB = 130;

    /**
     * Umbral del reflejo en un oído sano: ~85 dB HL, o sea 85 dB de nivel
     * de sensación. Ese SL enorme es lo que hace al reflejo útil: en una
     * hipoacusia coclear NO sube en proporción a la pérdida, y el SL se
     * achica -- es el reclutamiento de Metz.
     */
    public const REFLEX_NORMAL_DB = 85.0;

    /** SL mínimo del reflejo en un oído coclear (reclutamiento de Metz). */
    public const REFLEX_METZ_SL_DB = 25.0;

    /**
     * Cuánto sube el umbral del reflejo por dB de pérdida RETROCOCLEAR.
     * A diferencia de la coclear, acá sube dB a dB (o peor): el reflejo se
     * pierde temprano, que es el hallazgo que lo separa de una coclear con
     * el mismo audiograma.
     */
    public const REFLEX_RETRO_SLOPE = 1.0;

    /**
     * Penalización fija (dB) cuando el ABR muestra patrón retrococlear.
     * Un schwannoma chico con audiograma normal igual eleva o abole el
     * reflejo: la lesión está en la vía del arco reflejo, no en el umbral.
     */
    public const REFLEX_RETRO_PENALTY_DB = 15.0;

    /** Salida máxima del canal de reflejo: por encima, "ausente". */
    public const REFLEX_MAX_DB = 110.0;

    /**
     * Gap aéreo-óseo en el oído SONDA desde el cual el reflejo no se puede
     * registrar. No es que no ocurra: el oído medio rígido no deja ver el
     * cambio de admitancia.
     */
    public const REFLEX_PROBE_GAP_DB = 10.0;

    /**
     * Timpanogramas del oído SONDA que abolen el reflejo registrable.
     * B (plano, ocupación) y As (rígido, otoesclerosis) no dejan ver el
     * cambio de admitancia; Cs es la versión rígida y retraída.
     */
    public const REFLEX_PROBE_TYMP_ABSENT = ['B', 'As', 'Cs'];

    /**
     * Umbral del reflejo acústico (dB HL) para una frecuencia, o
     * REFLEX_ABSENT_DB si no se registra.
     *
     * Son DOS oídos: la sonda mide en uno y el estímulo entra por otro
     * (el mismo en ipsi, el contrario en contra). El oído medio de la
     * SONDA decide si el reflejo se puede ver; la cóclea y el nervio del
     * oído ESTIMULADO deciden a qué nivel aparece. Confundir los dos es
     * exactamente el error que el patrón de reflejos existe para enseñar.
     *
     * @param array $decompProbe  decompose() del oído donde va la sonda
     * @param array $decompStim   decompose() del oído estimulado
     * @param string $tympProbe   tipo de timpanograma del oído sonda (Z_OD/Z_OI)
     * @param array<string,mixed> $retroStim patrón retrococlear del oído estimulado
     * @param int|string $hz      frecuencia, o 'NBN' para el ruido de banda
     */
    public static function reflexThreshold(
        array $decompProbe,
        array $decompStim,
        string $tympProbe,
        float $ccePctStim,
        array $retroStim,
        $hz
    ): int {
        // 1. ¿Se puede registrar? Lo decide el oído medio de la sonda.
        if (in_array($tympProbe, self::REFLEX_PROBE_TYMP_ABSENT, true)) {
            return self::REFLEX_ABSENT_DB;
        }
        $gapProbe = $hz === 'NBN'
            ? self::coreAverage($decompProbe['gap'])
            : (self::levelAt($decompProbe['gap'], (float) $hz) ?? 0.0);
        if ($gapProbe >= self::REFLEX_PROBE_GAP_DB) {
            return self::REFLEX_ABSENT_DB;
        }

        // 2. Un bloqueo o una desincronía del lado estimulado no dejan
        // llegar la señal al núcleo: no hay reflejo a ningún nivel.
        $retro = self::normalizeRetro($retroStim);
        if ($retro['bloqueo'] !== 'ninguno' || $retro['desincronia'] === 'alta') {
            return self::REFLEX_ABSENT_DB;
        }

        // 3. ¿A qué nivel aparece? Lo decide el oído estimulado.
        if ($hz === 'NBN') {
            $sn = self::coreAverage($decompStim['sn']);
            $gapStim = self::coreAverage($decompStim['gap']);
        } else {
            $sn = self::levelAt($decompStim['sn'], (float) $hz) ?? 0.0;
            $gapStim = self::levelAt($decompStim['gap'], (float) $hz) ?? 0.0;
        }
        $cce = $sn * self::clamp($ccePctStim, 0.0, 100.0) / 100.0;
        $retroSn = $sn - $cce;

        // Coclear: el umbral NO sigue a la pérdida hasta que el SL se
        // achica al mínimo (Metz). Retrococlear: sube dB a dB desde el
        // primer decibel. Manda el mecanismo que más lo eleva.
        $porCoclear = max(self::REFLEX_NORMAL_DB, $cce + self::REFLEX_METZ_SL_DB);
        $porRetro = self::REFLEX_NORMAL_DB + $retroSn * self::REFLEX_RETRO_SLOPE
            + (self::retroActivo($retroStim) ? self::REFLEX_RETRO_PENALTY_DB : 0.0);
        // El gap del oído estimulado es atenuación pura: se suma entero.
        $umbral = max($porCoclear, $porRetro) + $gapStim;

        if ($umbral > self::REFLEX_MAX_DB) {
            return self::REFLEX_ABSENT_DB;
        }
        return (int) (round($umbral / 5) * 5);
    }

    // ---------------------------------------------------------------
    // Deterioro tonal (Carhart / Stat / Rosemberg)
    // ---------------------------------------------------------------

    /**
     * dB que hay que subir sobre el umbral para sostener el tono un minuto.
     *
     * Es el signo retrococlear clásico: una cóclea dañada mantiene el tono
     * (deterioro de 0-10 dB), un nervio enfermo lo pierde y hay que subir
     * 25-30 dB o más. Por eso depende del componente retro, no del umbral.
     *
     * @param array $decomp Salida de decompose()
     * @param array<string,mixed> $retro Patrón retrococlear
     */
    public static function toneDecay(array $decomp, float $ccePct, array $retro, $hz): int
    {
        // El patrón retro manda aunque el audiograma esté limpio: un
        // schwannoma chico da deterioro tonal con umbrales normales, y ese
        // es justamente el caso en que la prueba vale la pena.
        if (self::retroActivo($retro)) {
            return 30;
        }
        $sn = self::levelAt($decomp['sn'], (float) $hz) ?? 0.0;
        if ($sn <= 0.0) {
            return 0;
        }
        $retroSn = $sn * (1.0 - self::clamp($ccePct, 0.0, 100.0) / 100.0);
        if ($retroSn >= 30.0) {
            return 30;
        }
        if ($retroSn >= 15.0) {
            return 20;
        }
        // Coclear puro: adaptación mínima, dentro de lo normal.
        return $sn > self::SN_NORMAL_DB ? 5 : 0;
    }

    // ---------------------------------------------------------------
    // Proyeccion completa
    // ---------------------------------------------------------------

    /**
     * Índices de CaseBuilder::FREQUENCIES del protocolo de cada prueba de
     * deterioro tonal. Mismos que ResponseAudiometry.DECAY_TESTS en
     * src/audiometria/response.py.
     */
    public const DECAY_FREQ_IDX = [
        'carhart' => [2, 3, 4, 6],      // 500, 1000, 2000, 4000
        'stat' => [2, 3, 4],            // 500, 1000, 2000
        'rosemberg' => [2, 3, 4, 6],
    ];

    /**
     * Todo lo que el perfil proyecta, de una sola pasada.
     *
     * Devuelve los cuatro módulos completos SIN mirar `auto`: quién aplica
     * qué lo decide el llamador. Así la misma función sirve para guardar
     * (case_create.php aplica solo lo derivado) y para la vista previa en
     * vivo (case_project.php devuelve todo y el navegador pinta lo que
     * corresponde) -- una sola implementación de cada ley, que es el punto
     * entero de este refactor.
     *
     * @param array $airPairs   cases.data['Aerea']
     * @param array $bonePairs  cases.data['Osea']
     * @param array $perfil     normalize()
     * @param array<string,string> $tympPorLado ['OD' => 'A', 'OI' => 'B']
     */
    public static function project(array $airPairs, array $bonePairs, array $perfil, array $tympPorLado): array
    {
        $decomp = [];
        foreach (['OD' => 0, 'OI' => 1] as $lado => $sideIdx) {
            $decomp[$lado] = self::decompose(
                $airPairs, $bonePairs, $sideIdx, (float) ($perfil[$lado]['cce_pct'] ?? self::DEFAULT_CCE_PCT)
            );
        }

        $abr = [];
        $eoas = [];
        $reflex = ['ipsi' => [], 'contra' => []];
        $recPorLado = [];
        foreach (['od' => 'OD', 'oi' => 'OI'] as $ladoForm => $lado) {
            $ccePct = (float) ($perfil[$lado]['cce_pct'] ?? self::DEFAULT_CCE_PCT);
            $retro = self::normalizeRetro($perfil[$lado]['retro'] ?? []);
            $otro = $lado === 'OD' ? 'OI' : 'OD';

            $porEstimulo = self::abrThresholds($decomp[$lado], 'air_conduction');
            $abr[$lado] = [
                // El tipo decide la física de la curva (corrimiento paralelo
                // de la conductiva, pendiente L-I de la coclear, interpicos
                // del retro): derivar el umbral y dejar el tipo a mano deja
                // curvas que no se corresponden con ningún oído.
                'type' => self::derivedType($decomp[$lado], $ccePct, $retro),
                'umbral' => $porEstimulo['click'],
                'umbral_por_estimulo' => $porEstimulo,
                'umbral_por_estimulo_oseo' => self::abrThresholds($decomp[$lado], 'bone_conduction'),
            ];

            // El `umbral` de la OEA va en 0 a propósito: el cliente suma su
            // ley por patología (type + umbral, ver oae_attenuation_db en
            // src/oae/generators/base.py) A LO QUE VENGA en `desviaciones`.
            // Con el umbral cargado, la misma pérdida se descontaría dos
            // veces. Derivado hay una sola curva, que es el punto.
            $eoas[$lado] = [
                'type' => self::derivedType($decomp[$lado], $ccePct, $retro),
                'umbral' => 0,
                'desviaciones' => self::oaeDeviations($decomp[$lado]),
            ];

            $tymp = (string) ($tympPorLado[$lado] ?? 'A');
            $ipsi = [];
            foreach (self::REFLEX_FREQS_IPSI as $hz) {
                $ipsi[] = self::reflexThreshold($decomp[$lado], $decomp[$lado], $tymp, $ccePct, $retro, $hz);
            }
            // Contra: la sonda va en ESTE oído y el estímulo entra por el
            // contrario (ver reflex_stimulus() en Z.py, que indexa las filas
            // por el oído de la sonda).
            $contra = [];
            foreach (self::REFLEX_FREQS_CONTRA as $hz) {
                $contra[] = self::reflexThreshold(
                    $decomp[$lado], $decomp[$otro], $tymp,
                    (float) ($perfil[$otro]['cce_pct'] ?? self::DEFAULT_CCE_PCT),
                    self::normalizeRetro($perfil[$otro]['retro'] ?? []), $hz
                );
            }
            $reflex['ipsi'][$ladoForm] = $ipsi;
            $reflex['contra'][$ladoForm] = $contra;

            $recPorLado[$lado] = self::recruitment($ccePct, $decomp[$lado]);
        }

        // Fowler compara dos oídos: el patrón es el del oído EN ESTUDIO (el
        // peor en esa frecuencia), que es de quien se juzga el crecimiento
        // de sonoridad. Las frecuencias que califican salen solas de los
        // umbrales, igual que en el formulario.
        $fowler = [];
        foreach (CaseBuilder::fowlerQualifyingFreqs($airPairs, $bonePairs) as $freqIdx) {
            $estudio = ($airPairs[$freqIdx][0] ?? 0) >= ($airPairs[$freqIdx][1] ?? 0) ? 'OD' : 'OI';
            $fowler[(string) $freqIdx] = $recPorLado[$estudio]['pattern'];
        }

        $decay = [];
        foreach (self::DECAY_FREQ_IDX as $modo => $indices) {
            $decay[$modo] = ['od' => [], 'oi' => []];
            foreach (['od' => 'OD', 'oi' => 'OI'] as $ladoForm => $lado) {
                foreach ($indices as $freqIdx) {
                    $decay[$modo][$ladoForm][] = self::toneDecay(
                        $decomp[$lado],
                        (float) ($perfil[$lado]['cce_pct'] ?? self::DEFAULT_CCE_PCT),
                        self::normalizeRetro($perfil[$lado]['retro'] ?? []),
                        CaseBuilder::FREQUENCIES[$freqIdx]
                    );
                }
            }
        }

        return [
            'decomp' => $decomp,
            'abr' => $abr,
            'eoas' => $eoas,
            'reflex' => $reflex,
            'recruit' => [
                'sisi' => [$recPorLado['OD']['sisi_pct'], $recPorLado['OI']['sisi_pct']],
                'recruit' => [$recPorLado['OD']['recruit'], $recPorLado['OI']['recruit']],
                'fowler' => $fowler,
                'decay' => $decay,
            ],
        ];
    }

    // ---------------------------------------------------------------
    // Avisos de incoherencia entre modulos
    // ---------------------------------------------------------------

    /**
     * Diferencia (dB) desde la cual un examen cargado a mano se considera
     * en desacuerdo con lo que predice el perfil. Generosos a propósito:
     * el objetivo es cazar el caso imposible (OEA normales con un gap de
     * 40 dB), no discutir 10 dB con el docente.
     */
    public const WARN_OAE_DB = 15.0;
    public const WARN_ABR_DB = 25.0;

    /**
     * Contradicciones entre lo que el docente cargó a mano y lo que el
     * perfil predice.
     *
     * Solo mira los módulos que NO están derivados: uno derivado no puede
     * contradecirse a sí mismo. Y devuelve avisos, no errores: un caso
     * puede ser incoherente a propósito (Stenger, simulación, falsa onda V)
     * y eso tiene que seguir siendo posible. Ver ROADMAP.md.
     *
     * @param array<string,array> $decompPorLado ['OD' => decompose(), 'OI' => ...]
     * @param array<string,mixed> $perfil        normalize()
     * @param array<string,array> $abr           ['OD' => lado ya armado, ...]
     * @param array<string,array> $eoas          idem
     * @param array{ipsi:array,contra:array} $reflex  filas por modo, ['od'=>[], 'oi'=>[]]
     * @param array<string,string> $tympPorLado  ['OD' => 'A', 'OI' => 'B']
     * @return list<string>
     */
    public static function warnings(
        array $decompPorLado,
        array $perfil,
        array $abr,
        array $eoas,
        array $reflex,
        array $tympPorLado
    ): array {
        $avisos = [];
        $auto = $perfil['auto'] ?? [];

        foreach (['OD', 'OI'] as $lado) {
            $decomp = $decompPorLado[$lado] ?? null;
            if ($decomp === null) {
                continue;
            }
            $ccePct = (float) ($perfil[$lado]['cce_pct'] ?? self::DEFAULT_CCE_PCT);
            $retro = self::normalizeRetro($perfil[$lado]['retro'] ?? []);

            // --- ABR: el umbral cargado contra el que predice el audiograma.
            if (empty($auto['abr']) && isset($abr[$lado]['umbral'])) {
                $esperado = self::abrThresholds($decomp)['click'];
                $cargado = (float) $abr[$lado]['umbral'];
                if (abs($cargado - $esperado) > self::WARN_ABR_DB) {
                    $avisos[] = sprintf(
                        'ABR %s: umbral cargado %s dB, pero el audiograma predice ~%d dB nHL con click. %s',
                        $lado, (string) $cargado, $esperado,
                        $cargado < $esperado
                            ? 'Un ABR mucho mejor que el audiograma es el patrón de la simulación (o de un audiograma mal cargado).'
                            : 'Un ABR mucho peor que el audiograma solo se explica por una desincronía.'
                    );
                }
            }

            // --- OEA: la emisión cargada contra la que sobrevive al daño.
            if (empty($auto['eoas']) && isset($eoas[$lado])) {
                $esperadas = self::oaeDeviations($decomp);
                $cargadas = self::loadedOaeAttenuation($eoas[$lado]);
                foreach ([2000, 4000] as $hz) {
                    $dif = ($esperadas[(string) $hz] ?? 0.0) - ($cargadas[(string) $hz] ?? 0.0);
                    if ($dif > self::WARN_OAE_DB) {
                        $avisos[] = sprintf(
                            'OEA %s en %d Hz: cargada como presente (%d dB de atenuación), pero con esta pérdida y este gap se esperan ~%d dB. Una OEA conservada con la cóclea dañada solo pasa si la lesión es retrococlear (bajá cce_pct).',
                            $lado, $hz, (int) round($cargadas[(string) $hz] ?? 0.0),
                            (int) round($esperadas[(string) $hz] ?? 0.0)
                        );
                        break;
                    }
                }
            }

            // --- Reflejos: presencia, que es el hallazgo que se lee primero.
            if (empty($auto['reflex'])) {
                $otro = $lado === 'OD' ? 'OI' : 'OD';
                $ladoForm = strtolower($lado);
                foreach (['ipsi' => self::REFLEX_FREQS_IPSI,
                          'contra' => self::REFLEX_FREQS_CONTRA] as $modo => $freqs) {
                    $filas = $reflex[$modo][$ladoForm] ?? [];
                    foreach ($freqs as $i => $hz) {
                        if (!isset($filas[$i])) {
                            continue;
                        }
                        $estimulado = $modo === 'ipsi' ? $lado : $otro;
                        $esperado = self::reflexThreshold(
                            $decomp,
                            $decompPorLado[$estimulado] ?? $decomp,
                            (string) ($tympPorLado[$lado] ?? 'A'),
                            (float) ($perfil[$estimulado]['cce_pct'] ?? self::DEFAULT_CCE_PCT),
                            self::normalizeRetro($perfil[$estimulado]['retro'] ?? []),
                            $hz
                        );
                        $cargadoPresente = (float) $filas[$i] < self::REFLEX_ABSENT_DB;
                        if ($esperado === self::REFLEX_ABSENT_DB && $cargadoPresente) {
                            $avisos[] = sprintf(
                                'Reflejo %s %s en %s: cargado como presente, pero con este oído medio y esta pérdida no debería registrarse.',
                                $modo, $lado, is_int($hz) ? $hz . ' Hz' : (string) $hz
                            );
                            break 2;
                        }
                    }
                }
            }
            unset($ccePct, $retro);
        }

        return $avisos;
    }

    /**
     * Atenuación de la OEA que implica un lado ya cargado a mano, por
     * frecuencia. Réplica de oae_attenuation_db() en
     * src/oae/generators/base.py: la ley por patología (type + umbral) MÁS
     * el perfil por frecuencia, que es como los suma el cliente.
     *
     * @param array<string,mixed> $eoasLado
     * @return array<string,float>
     */
    public static function loadedOaeAttenuation(array $eoasLado): array
    {
        $tipo = (string) ($eoasLado['type'] ?? 'normal');
        $umbral = (float) ($eoasLado['umbral'] ?? 0);
        if ($tipo === 'coclear') {
            $patologia = min(max(0.0, $umbral - self::OAE_CCE_KNEE_DB) * self::OAE_CCE_SLOPE,
                             self::OAE_MAX_ATTEN_DB);
        } elseif ($tipo === 'transmission') {
            $patologia = min(max(0.0, $umbral - self::OAE_GAP_KNEE_DB) * self::OAE_GAP_SLOPE,
                             self::OAE_MAX_ATTEN_DB);
        } else {
            // 'neural' deja la cóclea intacta: la OEA no se atenúa.
            $patologia = 0.0;
        }
        $patologia += (float) ($eoasLado['atten_db'] ?? 0);

        $desv = is_array($eoasLado['desviaciones'] ?? null) ? $eoasLado['desviaciones'] : [];
        $out = [];
        foreach (CaseBuilder::EOAS_FREQS as $hz) {
            $out[(string) $hz] = $patologia + (float) ($desv[(string) $hz] ?? 0);
        }
        return $out;
    }

    /**
     * Promedio de una curva (Hz => dB) en CORE_FREQS.
     *
     * @param array<int,float> $curva
     */
    public static function coreAverage(array $curva): float
    {
        $suma = 0.0;
        $n = 0;
        foreach (self::CORE_FREQS as $hz) {
            $nivel = self::levelAt($curva, (float) $hz);
            if ($nivel === null) {
                continue;
            }
            $suma += $nivel;
            $n++;
        }
        return $n > 0 ? $suma / $n : 0.0;
    }

    /**
     * Máximo de una curva (Hz => dB) en CORE_FREQS.
     *
     * @param array<int,float> $curva
     */
    public static function coreMax(array $curva): float
    {
        $max = 0.0;
        foreach (self::CORE_FREQS as $hz) {
            $nivel = self::levelAt($curva, (float) $hz);
            if ($nivel !== null) {
                $max = max($max, $nivel);
            }
        }
        return $max;
    }

    private static function clamp(float $valor, float $min, float $max): float
    {
        return max($min, min($max, $valor));
    }
}
