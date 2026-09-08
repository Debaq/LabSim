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
        $gap = self::coreAverage($decomp['gap']);
        $sn = self::coreAverage($decomp['sn']);

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
        if (self::coreAverage($decomp['sn']) <= self::SN_NORMAL_DB) {
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

    private static function clamp(float $valor, float $min, float $max): float
    {
        return max($min, min($max, $valor));
    }
}
