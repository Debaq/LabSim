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
     *            deterioro tonal el del nervio. Incluye el LDL, que es la
     *            expresión audiométrica del mismo fenómeno.
     * - logo:    logoaudiometría -- máxima discriminación y a qué nivel.
     */
    public const AUTO_MODULES = ['abr', 'eoas', 'reflex', 'recruit', 'logo'];

    /** Frecuencias sobre las que se promedia para clasificar el oído (Hz). */
    public const CORE_FREQS = [500, 1000, 2000, 4000];

    /**
     * Valor con el que el caso marca que en esa frecuencia NO HUBO
     * RESPUESTA: el paciente no oyó ni al máximo del audiómetro.
     *
     * No es un umbral de 130 dB HL -- ningún audiómetro llega ahí. Tomarlo
     * como número hacía dos daños: inflaba los promedios (una frecuencia
     * sin respuesta empujaba el promedio 60 dB) e inventaba gaps, porque
     * restarle la ósea a un 130 da una diferencia que nadie midió.
     *
     * Para todo lo que se deriva de la pérdida --OEA, ABR, reflejos,
     * clasificación-- se toma como el TOPE del audiómetro: ese oído es al
     * menos así de malo, y eso sí es un dato. Lo que no se puede es fingir
     * que el umbral vale 130.
     */
    public const SIN_RESPUESTA_DB = 130.0;

    /** Máximo que entrega el audiómetro (dB HL). */
    public const MAX_AUDIOMETRO_DB = 120.0;

    /**
     * Pesos por estímulo del ABR: qué zona coclear representa cada uno.
     * Las claves son EXACTAMENTE las de STIM_MAP en src/abr/ABR_generator.py
     * (click / ce_chirp / ce_chirp_ls / nb_ce_chirp_ls_<freq> /
     * tone_burst_<freq>), así el cliente indexa el resultado sin traducir
     * nada.
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
        // NB CE-Chirp LS: banda estrecha, o sea frecuencia específico como
        // el burst -- lo que cambia respecto al burst es la sincronía (sale
        // antes y más grande), no qué zona coclear mira.
        'nb_ce_chirp_ls_500Hz'  => [500 => 1.0],
        'nb_ce_chirp_ls_1000Hz' => [1000 => 1.0],
        'nb_ce_chirp_ls_2000Hz' => [2000 => 1.0],
        'nb_ce_chirp_ls_4000Hz' => [4000 => 1.0],
        'click'             => [2000 => 0.35, 3000 => 0.30, 4000 => 0.35],
        'ce_chirp'          => [500 => 0.15, 1000 => 0.20, 2000 => 0.25, 4000 => 0.40],
        'ce_chirp_ls'       => [500 => 0.15, 1000 => 0.20, 2000 => 0.25, 4000 => 0.40],
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
        'ce_chirp_ls'       => 5.0,
        // El NB CE-Chirp LS mira la misma banda que el burst, pero como
        // sincroniza el tramo coclear que le toca llega al umbral con
        // menos nivel: la corrección nHL->eHL es ~5 dB menor que la del
        // burst de esa frecuencia (en 4 kHz ya no queda margen).
        'nb_ce_chirp_ls_500Hz'  => 15.0,
        'nb_ce_chirp_ls_1000Hz' => 10.0,
        'nb_ce_chirp_ls_2000Hz' => 5.0,
        'nb_ce_chirp_ls_4000Hz' => 5.0,
    ];

    /**
     * Calibración de la vía ósea del lactante, en dB por frecuencia.
     *
     * Los valores de referencia del vibrador (la fuerza que equivale a 0 dB)
     * están definidos sobre un cráneo ADULTO, en la mastoides. El cráneo del
     * lactante tiene las suturas abiertas y los huesos sin fusionar, y eso lo
     * hace MÁS eficiente transmitiendo sonido por vía ósea, sobre todo en
     * graves: el mismo nivel de dial le llega más fuerte a la cóclea. Con
     * calibración de adulto, el umbral óseo de un bebé se lee más bajo que el
     * de un adulto con exactamente la misma audición.
     *
     * Ojo con la consecuencia clínica, que es el motivo de modelarlo: como el
     * gap aéreo-óseo se calcula restando, usar norma de adulto en un lactante
     * INFLA el componente conductivo aparente. Es un error clásico de lectura
     * en screening.
     *
     * Efecto decreciente con la frecuencia (en 4 kHz prácticamente no hay) y
     * que se va con la edad a medida que las suturas se cierran:
     * completo bajo los 6 meses, nada pasados los 24.
     */
    public const INFANT_BONE_CALIBRATION_DB = [
        500 => 15.0,
        1000 => 10.0,
        2000 => 5.0,
        3000 => 2.0,
        4000 => 0.0,
        6000 => 0.0,
        8000 => 0.0,
    ];
    public const INFANT_BONE_FULL_MONTHS = 6.0;
    public const INFANT_BONE_NONE_MONTHS = 24.0;

    /**
     * Cuánto de la calibración de lactante aplica a esa edad (0 a 1).
     * `null` = edad desconocida -> 0, no se inventa un lactante.
     */
    public static function infantBoneFactor($edadMeses): float
    {
        if ($edadMeses === null || $edadMeses === '') {
            return 0.0;
        }
        $m = max(0.0, (float) $edadMeses);
        if ($m <= self::INFANT_BONE_FULL_MONTHS) {
            return 1.0;
        }
        if ($m >= self::INFANT_BONE_NONE_MONTHS) {
            return 0.0;
        }
        return (self::INFANT_BONE_NONE_MONTHS - $m)
            / (self::INFANT_BONE_NONE_MONTHS - self::INFANT_BONE_FULL_MONTHS);
    }

    /**
     * Transitorio de las primeras horas de vida.
     *
     * Cuánta conductiva le toca a este bebé sale de NewbornScreening, que
     * invierte las tasas de pase publicadas por franja horaria: la
     * bibliografía no da decibeles, da porcentajes de pase, así que los dB
     * son consecuencia de la tabla y no al revés.
     *
     * Los tres exámenes no la sufren igual:
     * - EOA: la peor parte. El sonido atraviesa conducto y oído medio de ida
     *   Y de vuelta, así que va al doble (mismo criterio que la conductiva
     *   en oae_attenuation_db). Por eso refiere tanto en las primeras horas.
     * - ABR aéreo: la sufre una sola vez.
     * - ABR óseo: NO la sufre. El vibrador saltea conducto y oído medio, y
     *   ese contraste --aérea elevada, ósea normal-- es lo que dice que es
     *   transitorio y no una hipoacusia.
     */
    public const NEONATAL_OAE_FACTOR = 2.0;
    public const NEONATAL_ABR_FACTOR = 0.6;

    /**
     * Conductiva transitoria de ese oído, en dB HL. `$nacimiento` trae las
     * circunstancias (parto, edad gestacional, vérnix) y el percentil
     * sorteado del oído -- ver NewbornScreening.
     */
    public static function neonatalTransientDb($horas, array $nacimiento = [], string $lado = 'OD'): float
    {
        if ($horas === null || $horas === '') {
            return 0.0;
        }
        require_once __DIR__ . '/NewbornScreening.php';
        $u = $nacimiento['percentil'][$lado] ?? 0.5;
        return NewbornScreening::transientDb((float) $horas, $nacimiento, (float) $u);
    }

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
     * Máxima pérdida por transmisión, en dB: el gap aéreo-óseo no puede
     * pasar de acá por mucho que se agrave el cuadro del oído medio.
     *
     * El oído medio solo puede dejar de aportar lo que aporta: anulado por
     * completo --cadena interrumpida con tímpano indemne-- el sonido sigue
     * llegando a la cóclea por vía ósea a través del cráneo, y esa ruta le
     * pone piso a la curva aérea. De ahí el techo clásico de la conductiva
     * pura en 60 dB: más gap que eso no es un oído medio peor, es un
     * audiograma mal armado (o una ósea mal enmascarada).
     *
     * Cada cuadro declara además su propio `gap_max_db` en SCENARIOS, que es
     * más bajo: un tapón no atenúa como una disyunción de cadena. Este valor
     * es el tope de todos y el que se usa si un cuadro no declara el suyo.
     */
    public const GAP_MAX_DB = 60.0;

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
     * Frecuencias sobre las que se mide el grado de la hipoacusia: promedio
     * BIAP de 500, 1000, 2000 y 4000 Hz en vía aérea.
     *
     * NO es el promedio de Fletcher (mejores 2 de 500/1k/2k) que el equipo le
     * muestra al alumno --ver response.py-- y eso es a propósito: Fletcher
     * ignora 4 kHz, así que una hipoacusia descendente le da 7 dB y quedaría
     * "normal" por promedio. Con Fletcher, pedirle grado a un cuadro de
     * agudos obliga a multiplicar la forma por diez, los agudos saturan en
     * 120 y el cuadro pierde justamente la pendiente que enseña.
     *
     * Consecuencia a tener presente: el número que el alumno promedie en el
     * equipo va a dar más bajo que el grado con que se armó el caso, en los
     * cuadros descendentes. Es la diferencia real entre las dos escalas, no
     * un error del simulador.
     */
    public const GRADE_FREQS = [500, 1000, 2000, 4000];

    /**
     * Grados de hipoacusia por promedio tonal (BIAP, dB HL).
     *
     * La audición normal en Chile llega hasta 20 dB HL inclusive, así que el
     * grado leve arranca en 21 y no hay un grado "normal": un oído sin
     * hipoacusia se pide con el cuadro 'normal', que no tiene grados.
     *
     * `max_db` en un cuadro (ver SCENARIOS) recorta el techo del grado cuando
     * la fisiología lo exige.
     */
    public const GRADES = [
        'leve'     => ['label' => 'Leve (21-40 dB)',      'rango' => [21, 40]],
        'moderada' => ['label' => 'Moderada (41-70 dB)',  'rango' => [41, 70]],
        'severa'   => ['label' => 'Severa (71-90 dB)',    'rango' => [71, 90]],
        'profunda' => ['label' => 'Profunda (91-110 dB)', 'rango' => [91, 110]],
    ];

    /**
     * Umbral mediano por edad y sexo -- ISO 7029.
     *
     * La norma da la desviación mediana del umbral respecto de un adulto
     * joven otológicamente normal, como `a * (edad - 18)^2` con un
     * coeficiente por frecuencia distinto para hombres y mujeres (los agudos
     * se deterioran antes y más rápido en hombres). Debajo de los 18 la
     * desviación es 0.
     *
     * Está acá porque "normal" no es un audiograma plano en 0 para todo el
     * mundo: un niño de 10 que oye bien da 0 dB en todas las frecuencias, y
     * un hombre de 70 que también oye bien --normal PARA SU EDAD-- llega a
     * 30 dB en 4 kHz. Generar los dos iguales le enseñaba al alumno una
     * normalidad que no existe, y hacía imposible el ejercicio de decidir si
     * una presbiacusia es más de lo esperable para la edad.
     *
     * Se suma como piso a TODOS los cuadros, no solo al normal: un señor de
     * 70 con una otitis media tiene la otitis Y su presbiacusia.
     *
     * Coeficientes x10^-3, [hombre, mujer].
     */
    public const ISO7029_COEF = [
        125  => [3.00,  3.00],
        250  => [3.00,  3.00],
        500  => [3.55,  3.55],
        1000 => [3.50,  3.50],
        2000 => [5.35,  4.40],
        3000 => [8.60,  5.60],
        4000 => [11.30, 6.00],
        6000 => [11.90, 8.85],
        8000 => [13.50, 10.50],
    ];

    /** Edad desde la cual ISO 7029 empieza a contar la desviación. */
    public const ISO7029_EDAD_BASE = 18;

    /**
     * Umbral mediano esperable a esta edad, por frecuencia (dB HL).
     *
     * @param int $edad años
     * @param int $gender 0 hombre, 1 mujer (mismo código que el formulario)
     * @return array<int,float> Hz => dB
     */
    public static function ageNorm(int $edad, int $gender): array
    {
        $delta = max(0, $edad - self::ISO7029_EDAD_BASE);
        $cuadrado = $delta * $delta;
        $idx = $gender === 1 ? 1 : 0;

        $out = [];
        foreach (self::ISO7029_COEF as $hz => $coef) {
            $out[$hz] = round($coef[$idx] * 0.001 * $cuadrado, 1);
        }
        return $out;
    }

    /**
     * Categorías del catálogo, en el orden en que se muestran.
     *
     * Sensorial, neural y sensorioneural son tres categorías distintas y no
     * un paraguas con subgrupos: se separan por `cce_pct`, que es el eje que
     * el resto del perfil ya usa para proyectar. Sensorial es coclear puro
     * (100), neural es retrococlear puro (0) y sensorioneural es el caso con
     * los dos componentes, que es donde el alumno tiene que separarlos --la
     * OEA dice cuánto hay de coclear y el ABR cuánto de retro--.
     */
    public const CATEGORIAS = [
        'normal'         => 'Normal',
        'conductiva'     => 'Conductiva',
        'sensorial'      => 'Sensorial (coclear)',
        'neural'         => 'Neural (retrococlear)',
        'sensorioneural' => 'Sensorioneural (coclear + neural)',
        'mixta'          => 'Mixta (conductiva + sensorioneural)',
    ];

    /**
     * Cuadros clínicos para generar un caso coherente de una sola vez.
     *
     * `sn_shape`/`gap_shape` son formas relativas en dB por frecuencia; la
     * escala sale del grado pedido (ver GRADES y el generador en
     * case_create.php), que la ajusta para que el promedio BIAP caiga en el
     * rango. Sobre eso se suma el piso por edad de ageNorm(), así que dos
     * pacientes del mismo cuadro y grado no salen calcados ni ignoran los
     * años que tienen.
     *
     * `categoria` agrupa el catálogo en el selector (ver CATEGORIAS).
     *
     * `grados` es qué grados de GRADES puede producir el cuadro sin dejar de
     * ser ese cuadro, y la lista NO es genérica: es clínica. Una conductiva
     * pura no llega a severa porque la vía ósea le pone techo (ver
     * `max_db`); una muesca de 4 kHz no es una hipoacusia severa por
     * promedio, y forzarla a serlo la convertiría en una plana; un
     * descendente puro no sube el promedio más allá de moderada sin
     * aplanarse. El cuadro 'normal' no tiene grados: un oído sano no tiene
     * grado de hipoacusia.
     *
     * `max_db` es el techo físico del promedio, en los cuadros que lo tienen.
     *
     * `gap_max_db` es el techo del GAP por frecuencia, que es otra cosa: el
     * promedio lo puede subir la vía ósea (una mixta), el gap no --lo limita
     * cuánta transmisión puede perder ese oído medio y nada más (ver
     * GAP_MAX_DB)--. Hace falta porque el grado escala la forma entera: sin
     * techo, pedirle "moderada" a una otitis le ponía 68 dB de gap en 125 Hz
     * para que el promedio BIAP llegara, o 83 dB a una perforación. El
     * generador lo usa dos veces: recorta el grado alcanzable del cuadro
     * (techoDe) y recorta el gap frecuencia por frecuencia al escribirlo.
     * Todo cuadro con `gap_shape` lo declara.
     *
     * El cuadro se elige POR OÍDO: un paciente puede tener el OD sano y una
     * conductiva en el OI, o una coclear de un lado y un schwannoma del
     * otro. El oído sano se pide con 'normal', que no es un cero: es un oído
     * normal con la variabilidad y la edad que le corresponden.
     *
     * `vemp` es el eje vestibular del cuadro, y NO todos lo tienen: los que
     * no traen la clave se generan con un VEMP normal. Lleva `type` (la
     * patología del oído) y, o bien `umbral` con un rango por subtipo, o
     * bien `umbral_gap` para las conductivas -- ahí el VEMP aéreo se apaga
     * porque el oído medio no deja pasar el estímulo, así que el umbral
     * sube tanto como el gap en vez de un rango fijo.
     *
     * Que un cuadro no traiga `vemp` es una decisión, no un olvido. La
     * súbita y la ototóxica se dejan normales a propósito: el compromiso
     * vestibular en las dos es real pero variable caso a caso, y armarlo
     * como regla le enseñaría al alumno una asociación que no existe. El
     * docente lo pone a mano cuando el caso lo pide.
     *
     * `tinnitus` es la probabilidad de que el cuadro traiga acúfeno, con el
     * tipo de ruido y las frecuencias de matching entre las que sortear. Es
     * probabilidad y no un sí/no: dos casos del mismo cuadro tienen que
     * poder salir uno con acúfeno y otro sin. La LATERALIDAD no está acá --
     * sale de a cuántos oídos les tocó el cuadro al generar.
     *
     * `conciencia` es el rango del rasgo homónimo del paciente en la
     * entrevista (ver Sala::RASGOS_DEFAULT), y solo aparece en los cuadros
     * que lo corren del rango general: los de instalación lenta lo bajan
     * --el paciente contesta que oye bien-- y los de instalación brusca lo
     * suben. Sin la clave, el generador sortea en el rango general.
     *
     * `lateralidad` no decide nada por sí sola -- es la sugerencia que el
     * editor le hace al otro oído cuando se elige este cuadro: 'unilateral'
     * propone dejar el contrario normal (que es lo que hace falta para que
     * el IT5, el Weber y el Fowler tengan con qué comparar), 'bilateral'
     * propone repetirlo. Las dos se pisan eligiendo a mano.
     */
    public const SCENARIOS = [
        // --- Normal -----------------------------------------------------
        'normal' => [
            'label' => 'Normal para la edad',
            'categoria' => 'normal',
            'sn_shape' => [125 => 3, 250 => 3, 500 => 3, 1000 => 3, 2000 => 3, 3000 => 3, 4000 => 3, 6000 => 5, 8000 => 5],
            'sn_scale' => [0.0, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal', 'grados' => [],
            'tinnitus' => ['prob' => 0.05, 'ruido' => ['Zumbido', 'Siseo'],
                           'frecuencia' => [4000, 6000], 'permanente' => 0.3],
            'conciencia' => [60, 90],
        ],

        // --- Conductivas ------------------------------------------------
        // Todas con cce_pct 100: la cóclea está sana y el problema es de
        // transmisión. Lo que las distingue entre sí es la curva
        // timpanométrica, la forma del gap y cuánta transmisión puede perder
        // ese oído medio (`gap_max_db`): un tapón no atenúa como una cadena
        // interrumpida, y ninguno pasa de GAP_MAX_DB.
        'otitis_media' => [
            'label' => 'Otitis media con efusión',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 8, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.2],
            'gap_shape' => [125 => 40, 250 => 40, 500 => 38, 1000 => 32, 2000 => 28, 3000 => 26, 4000 => 25, 6000 => 25, 8000 => 25],
            'gap_scale' => [0.5, 1.2],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['B'], 'etf' => 'Disfunción tubaria',
            // La efusión sola llega a ~50 dB de gap en los graves, y con esta
            // forma (graves peor que agudos) el promedio BIAP no alcanza la
            // moderada sin pedirle al oído medio más atenuación de la que
            // puede dar. Una otitis que mide moderada ya tiene la cadena
            // comprometida: eso es 'mixta_otitis_cronica' o una disyunción.
            'grados' => ['leve'], 'max_db' => 45, 'gap_max_db' => 50,
            // El VEMP aéreo lo apaga el oído medio: el estímulo no llega. No
            // hay lesión vestibular (type normal), lo que sube es el umbral
            // -- y sube tanto como el gap, que ya está en el audiograma.
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.3, 'ruido' => ['Zumbido'],
                           'frecuencia' => [250, 500], 'permanente' => 0.3],
            'conciencia' => [70, 95],
        ],
        'otoesclerosis' => [
            'label' => 'Otoesclerosis',
            'categoria' => 'conductiva',
            // Muesca de Carhart: la ósea cae en 2 kHz por el artefacto
            // mecánico del estribo fijo, no por daño coclear.
            'sn_shape' => [125 => 5, 250 => 5, 500 => 8, 1000 => 10, 2000 => 18, 3000 => 12, 4000 => 8, 6000 => 8, 8000 => 8],
            'sn_scale' => [0.4, 1.2],
            'gap_shape' => [125 => 40, 250 => 40, 500 => 35, 1000 => 30, 2000 => 20, 3000 => 22, 4000 => 25, 6000 => 25, 8000 => 25],
            'gap_scale' => [0.5, 1.2],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['As'], 'etf' => 'Normal',
            // El estribo fijo del todo es el otro cuadro que llega a la
            // conductiva máxima: de ahí que sea una de las dos que alcanza la
            // moderada sin dejar de ser conductiva pura.
            'grados' => ['leve', 'moderada'], 'max_db' => 60, 'gap_max_db' => 60,
            // El VEMP aéreo lo apaga el oído medio: el estímulo no llega. No
            // hay lesión vestibular (type normal), lo que sube es el umbral
            // -- y sube tanto como el gap, que ya está en el audiograma.
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.55, 'ruido' => ['Zumbido', 'Campanilleo'],
                           'frecuencia' => [250, 500, 1000], 'permanente' => 0.5],
        ],
        'disyuncion_cadena' => [
            'label' => 'Disyunción de cadena osicular',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 8, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.2],
            // Gap PLANO y grande: la cadena desarticulada (típicamente la
            // articulación incudo-estapedial) deja de conducir en todas las
            // frecuencias por igual, no solo en los graves como la efusión o
            // la perforación. Esa planitud es el hallazgo que la separa del
            // resto de las conductivas, no solo su magnitud.
            'gap_shape' => [125 => 52, 250 => 55, 500 => 58, 1000 => 58, 2000 => 55, 3000 => 52, 4000 => 50, 6000 => 50, 8000 => 50],
            'gap_scale' => [0.6, 1.0],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            // Tímpano indemne y cadena suelta: el oído medio queda hipermóvil
            // (Ad), y con ese gap el reflejo no se registra (ver
            // reflexThreshold: REFLEX_PROBE_GAP_DB).
            'z' => ['Ad'], 'etf' => 'Normal',
            // Es LA conductiva máxima: con la cadena interrumpida el oído
            // medio no aporta nada y el gap se para en el techo de 60 dB.
            'grados' => ['leve', 'moderada'], 'max_db' => 60, 'gap_max_db' => 60,
            // El VEMP aéreo lo apaga el oído medio: el estímulo no llega. No
            // hay lesión vestibular (type normal), lo que sube es el umbral
            // -- y sube tanto como el gap, que ya está en el audiograma.
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.35, 'ruido' => ['Zumbido'],
                           'frecuencia' => [250, 500], 'permanente' => 0.3],
            // Instalación brusca (trauma, barotrauma, postquirúrgica): el
            // paciente sabe el día y la hora en que dejó de oír.
            'conciencia' => [85, 100],
        ],
        'fractura_cadena' => [
            'label' => 'Fractura de cadena osicular',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 8, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.2],
            // La misma planitud de la disyunción pero a media máquina: el
            // hueso fracturado (mango del martillo, crura del estribo) sigue
            // transmitiendo algo, así que el gap es parcial. La diferencia
            // con la disyunción completa es de magnitud y de timpanograma, y
            // separarlas es el ejercicio.
            'gap_shape' => [125 => 32, 250 => 34, 500 => 35, 1000 => 35, 2000 => 32, 3000 => 30, 4000 => 30, 6000 => 30, 8000 => 30],
            'gap_scale' => [0.5, 1.1],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            // Puede quedar normal o algo hipermóvil: la cadena está dañada,
            // no suelta.
            'z' => ['A', 'Ad'], 'etf' => 'Normal',
            // Transmisión parcial: no llega al gap de la disyunción, y por
            // promedio se queda en leve.
            'grados' => ['leve'], 'max_db' => 45, 'gap_max_db' => 40,
            // El VEMP aéreo lo apaga el oído medio: el estímulo no llega. No
            // hay lesión vestibular (type normal), lo que sube es el umbral
            // -- y sube tanto como el gap, que ya está en el audiograma.
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.35, 'ruido' => ['Zumbido', 'Campanilleo'],
                           'frecuencia' => [500, 1000], 'permanente' => 0.3],
            // Igual que la disyunción: pasó de un golpe.
            'conciencia' => [85, 100],
        ],
        'fractura_longitudinal' => [
            'label' => 'Fractura longitudinal de peñasco',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 8, 3000 => 10, 4000 => 10, 6000 => 12, 8000 => 12],
            'sn_scale' => [0.0, 1.2],
            // El trazo corre PARALELO al eje del peñasco y se mete por el oído
            // medio: hemotímpano, desgarro timpánico, a veces la cadena
            // luxada. El laberinto queda afuera, así que la cóclea está sana
            // y la pérdida es de transmisión -- y por eso suele recuperarse
            // cuando se reabsorbe la sangre.
            'gap_shape' => [125 => 45, 250 => 45, 500 => 42, 1000 => 38, 2000 => 35, 3000 => 32, 4000 => 30, 6000 => 30, 8000 => 30],
            'gap_scale' => [0.5, 1.1],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            // Hemotímpano: la caja ocupada por sangre da curva plana, igual
            // que una efusión. Lo que cambia es la historia, no la curva.
            'z' => ['B'], 'etf' => 'Normal',
            // Por promedio se queda en leve: el gap del hemotímpano no pasa
            // de ~50 dB en los graves y los agudos quedan mucho mejor. Si la
            // fractura además luxó la cadena, el cuadro a elegir es
            // 'disyuncion_cadena', que es lo que mide ese oído.
            'grados' => ['leve'], 'max_db' => 50, 'gap_max_db' => 50,
            // El VEMP aéreo lo apaga el oído medio: el estímulo no llega. No
            // hay lesión vestibular (type normal), lo que sube es el umbral
            // -- y sube tanto como el gap, que ya está en el audiograma.
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.4, 'ruido' => ['Zumbido'],
                           'frecuencia' => [250, 500], 'permanente' => 0.3],
            // Pasó de un golpe y con otorragia: el paciente sabe el momento.
            'conciencia' => [85, 100],
        ],
        'perforacion' => [
            'label' => 'Perforación timpánica',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 5, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.2],
            // Gap grande en graves y chico en agudos: perder superficie
            // vibrátil se nota sobre todo abajo.
            'gap_shape' => [125 => 40, 250 => 38, 500 => 32, 1000 => 25, 2000 => 18, 3000 => 15, 4000 => 12, 6000 => 12, 8000 => 12],
            'gap_scale' => [0.4, 1.1],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['B'], 'etf' => 'Normal',
            // Una perforación subtotal, con la cadena ya comprometida, llega
            // a 55 dB de gap en los graves; más que eso es otra cosa, no el
            // agujero. Con los agudos casi indemnes el promedio BIAP se
            // queda en leve: una perforación que mide moderada en promedio
            // está contando la cadena, no la membrana.
            'grados' => ['leve'], 'max_db' => 45, 'gap_max_db' => 55,
            // El VEMP aéreo lo apaga el oído medio: el estímulo no llega. No
            // hay lesión vestibular (type normal), lo que sube es el umbral
            // -- y sube tanto como el gap, que ya está en el audiograma.
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'conciencia' => [70, 95],
        ],
        'disfuncion_tubaria' => [
            'label' => 'Disfunción tubaria (presión negativa)',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 5, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.0],
            'gap_shape' => [125 => 25, 250 => 25, 500 => 22, 1000 => 18, 2000 => 15, 3000 => 12, 4000 => 12, 6000 => 12, 8000 => 12],
            'gap_scale' => [0.4, 1.1],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['C', 'Cs'], 'etf' => 'Disfunción tubaria',
            // Presión negativa sin líquido: el tímpano retraído pierde hasta
            // ~40 dB en los graves y no más -- de ahí para arriba ya hay
            // efusión, y entonces el cuadro es 'otitis_media'.
            'grados' => ['leve'], 'max_db' => 35, 'gap_max_db' => 40,
            // El VEMP aéreo lo apaga el oído medio: el estímulo no llega. No
            // hay lesión vestibular (type normal), lo que sube es el umbral
            // -- y sube tanto como el gap, que ya está en el audiograma.
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
        ],
        'tapon_cerumen' => [
            'label' => 'Tapón de cerumen',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 3, 250 => 3, 500 => 3, 1000 => 3, 2000 => 5, 3000 => 5, 4000 => 5, 6000 => 8, 8000 => 8],
            'sn_scale' => [0.0, 1.0],
            'gap_shape' => [125 => 30, 250 => 30, 500 => 28, 1000 => 25, 2000 => 25, 3000 => 25, 4000 => 25, 6000 => 28, 8000 => 30],
            'gap_scale' => [0.3, 1.0],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['As'], 'etf' => 'Normal',
            // Un tapón, aunque ocluya del todo, no pasa de ~40 dB: es el
            // cuadro leve por definición, y de ahí que sorprenda tanto al
            // paciente cuando se lo sacan.
            'grados' => ['leve'], 'max_db' => 40, 'gap_max_db' => 40,
            // El VEMP aéreo lo apaga el oído medio: el estímulo no llega. No
            // hay lesión vestibular (type normal), lo que sube es el umbral
            // -- y sube tanto como el gap, que ya está en el audiograma.
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'conciencia' => [70, 95],
        ],

        'cuerpo_extrano_cae' => [
            'label' => 'Cuerpo extraño en CAE',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 3, 250 => 3, 500 => 5, 1000 => 5, 2000 => 5, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.0],
            // Gap PLANO: un objeto que ocluye el conducto atenúa parejo, a
            // diferencia de la efusión o la perforación, que pierden sobre
            // todo los graves. El oído medio está sano y la curva es A: eso
            // es lo que separa este cuadro de una otitis.
            'gap_shape' => [125 => 28, 250 => 28, 500 => 28, 1000 => 28, 2000 => 28, 3000 => 28, 4000 => 28, 6000 => 30, 8000 => 30],
            'gap_scale' => [0.3, 1.1],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve'], 'max_db' => 35, 'gap_max_db' => 35,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            // Se instaló de golpe (o el paciente se lo metió): lo nota.
            'conciencia' => [85, 100],
        ],
        'otitis_externa' => [
            'label' => 'Otitis externa difusa',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 3, 250 => 3, 500 => 5, 1000 => 5, 2000 => 6, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.0],
            // El edema del conducto estrecha la luz sin tocar el oído medio:
            // gap chico y parejo con curva A. La otoscopia y el dolor a la
            // tracción del pabellón no salen del cuadro, se cargan aparte.
            'gap_shape' => [125 => 26, 250 => 26, 500 => 25, 1000 => 24, 2000 => 22, 3000 => 22, 4000 => 22, 6000 => 24, 8000 => 24],
            'gap_scale' => [0.4, 1.1],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve'], 'max_db' => 35, 'gap_max_db' => 32,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'conciencia' => [80, 100],
        ],
        'estenosis_atresia_cae' => [
            'label' => 'Estenosis / atresia congénita de CAE',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 8, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.2],
            // Gap grande y PLANO de toda la vida, y SIN muesca de Carhart:
            // el estribo se mueve, lo que falta es el conducto. Esa planitud
            // sin muesca es lo que lo separa de la otoesclerosis, que llega
            // al mismo gap por otro camino.
            'gap_shape' => [125 => 50, 250 => 52, 500 => 54, 1000 => 54, 2000 => 52, 3000 => 50, 4000 => 50, 6000 => 50, 8000 => 50],
            'gap_scale' => [0.6, 1.0],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            // El timpanograma de verdad es NO REGISTRABLE --no hay dónde
            // sellar la sonda--, y eso no existe en Z_OPTIONS. 'B' es lo
            // menos falso que se puede escribir hoy: plano, sin pico. Ver
            // TODO.md, "Timpanograma no registrable".
            'z' => ['B'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'], 'max_db' => 60, 'gap_max_db' => 60,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            // Nació así: no tiene con qué comparar, y ese es el punto.
            'conciencia' => [15, 45],
        ],
        'timpanoesclerosis' => [
            'label' => 'Timpanoesclerosis / miringoesclerosis',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 8, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.2],
            // Rigidez, no masa: el gap crece hacia los AGUDOS, al revés que
            // la efusión. Con la curva As, ese sentido de la pendiente es
            // todo el hallazgo.
            'gap_shape' => [125 => 18, 250 => 18, 500 => 20, 1000 => 22, 2000 => 25, 3000 => 26, 4000 => 26, 6000 => 26, 8000 => 26],
            'gap_scale' => [0.4, 1.1],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['As'], 'etf' => 'Normal',
            'grados' => ['leve'], 'max_db' => 35, 'gap_max_db' => 32,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'conciencia' => [40, 75],
        ],
        'otitis_media_aguda' => [
            'label' => 'Otitis media aguda',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 8, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.2],
            // Misma curva que la efusión: lo que separa la aguda de la
            // 'otitis_media' con efusión es la HISTORIA (horas-días, dolor,
            // fiebre), no el audiograma ni el timpanograma.
            'gap_shape' => [125 => 42, 250 => 42, 500 => 40, 1000 => 34, 2000 => 30, 3000 => 28, 4000 => 26, 6000 => 26, 8000 => 26],
            'gap_scale' => [0.5, 1.2],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['B'], 'etf' => 'Disfunción tubaria',
            'grados' => ['leve'], 'max_db' => 42, 'gap_max_db' => 48,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.3, 'ruido' => ['Zumbido'],
                           'frecuencia' => [250, 500], 'permanente' => 0.2],
            // Empezó anteanoche con dolor: el paciente sabe el día.
            'conciencia' => [90, 100],
        ],
        'colesteatoma' => [
            'label' => 'Colesteatoma (sin daño coclear)',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 8, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.2],
            // Erosión de la cadena: gap grande y bastante plano, más que el
            // de una efusión. Mientras la ósea siga sana el cuadro es este;
            // cuando el colesteatoma se lleva la cóclea, el cuadro que mide
            // ese oído es 'mixta_otitis_cronica' o 'colesteatoma_fistula'.
            'gap_shape' => [125 => 46, 250 => 46, 500 => 45, 1000 => 42, 2000 => 40, 3000 => 38, 4000 => 38, 6000 => 38, 8000 => 38],
            'gap_scale' => [0.6, 1.1],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['B'], 'etf' => 'Disfunción tubaria',
            'grados' => ['leve', 'moderada'], 'max_db' => 55, 'gap_max_db' => 55,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.3, 'ruido' => ['Zumbido'],
                           'frecuencia' => [250, 500], 'permanente' => 0.4],
            // Progresivo y con otorrea de años: se consulta tarde.
            'conciencia' => [55, 85],
        ],
        'fijacion_congenita_estribo' => [
            'label' => 'Fijación congénita del estribo / malformación de cadena',
            'categoria' => 'conductiva',
            // Sin muesca de Carhart: la fijación es de nacimiento y no
            // arrastra el artefacto mecánico de la otoesclerosis. Un gap
            // plano y grande con ósea limpia en 2 kHz es la diferencia.
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 8, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.2],
            'gap_shape' => [125 => 42, 250 => 44, 500 => 46, 1000 => 46, 2000 => 44, 3000 => 42, 4000 => 42, 6000 => 42, 8000 => 42],
            'gap_scale' => [0.6, 1.0],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['A', 'As'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'], 'max_db' => 55, 'gap_max_db' => 52,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'conciencia' => [20, 50],
        ],
        'barotrauma' => [
            'label' => 'Barotrauma de oído medio',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 8, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.2],
            // Graves dominantes, como toda caja que no se ventila. La curva
            // es C/Cs por la presión negativa, o B si hubo hemotímpano.
            'gap_shape' => [125 => 40, 250 => 40, 500 => 36, 1000 => 30, 2000 => 26, 3000 => 24, 4000 => 22, 6000 => 22, 8000 => 22],
            'gap_scale' => [0.5, 1.1],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['C', 'B'], 'etf' => 'Disfunción tubaria',
            'grados' => ['leve'], 'max_db' => 40, 'gap_max_db' => 48,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.3, 'ruido' => ['Zumbido'],
                           'frecuencia' => [250, 500], 'permanente' => 0.2],
            // Pasó en el descenso del avión o del buceo: fecha y hora.
            'conciencia' => [90, 100],
        ],
        'glomus_timpanico' => [
            'label' => 'Glomus timpánico (paraganglioma)',
            'categoria' => 'conductiva',
            'sn_shape' => [125 => 5, 250 => 5, 500 => 5, 1000 => 5, 2000 => 8, 3000 => 8, 4000 => 8, 6000 => 10, 8000 => 10],
            'sn_scale' => [0.0, 1.2],
            'gap_shape' => [125 => 34, 250 => 34, 500 => 32, 1000 => 30, 2000 => 28, 3000 => 26, 4000 => 26, 6000 => 26, 8000 => 26],
            'gap_scale' => [0.5, 1.1],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['B', 'As'], 'etf' => 'Normal',
            'grados' => ['leve'], 'max_db' => 40, 'gap_max_db' => 42,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            // El único cuadro del catálogo que enciende `pulsatil`: el
            // acúfeno va al compás del pulso porque la masa ES vascular. El
            // gap por sí solo no distingue esto de una otitis; el pulso sí.
            'tinnitus' => ['prob' => 0.9, 'ruido' => ['Zumbido'],
                           'frecuencia' => [125, 250], 'permanente' => 0.85,
                           'pulsatil' => 0.9],
            'conciencia' => [80, 100],
        ],

        // --- Sensoriales (cocleares puras) ------------------------------
        'presbiacusia' => [
            'label' => 'Presbiacusia (descendente en agudos)',
            'categoria' => 'sensorial',
            'sn_shape' => [125 => 0, 250 => 0, 500 => 5, 1000 => 10, 2000 => 25, 3000 => 35, 4000 => 45, 6000 => 50, 8000 => 55],
            'sn_scale' => [0.6, 1.5], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            // Descendente pura: los graves normales tiran el promedio abajo.
            // Para llevarla a severa habría que subir 500 y 1000, y entonces
            // ya no es descendente, es plana.
            'grados' => ['leve', 'moderada'],
            'tinnitus' => ['prob' => 0.55, 'ruido' => ['Pitido', 'Siseo'],
                           'frecuencia' => [4000, 6000, 8000], 'permanente' => 0.6],
            'conciencia' => [25, 55],
        ],
        'muesca_4k' => [
            'label' => 'Muesca en 4 kHz (trauma acústico)',
            'categoria' => 'sensorial',
            'sn_shape' => [125 => 0, 250 => 0, 500 => 0, 1000 => 5, 2000 => 10, 3000 => 30, 4000 => 45, 6000 => 35, 8000 => 20],
            'sn_scale' => [0.7, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            // La muesca es un hallazgo en 3-6 kHz con el resto conservado:
            // por promedio no pasa de leve, y ese es el punto del cuadro.
            'grados' => ['leve'],
            'tinnitus' => ['prob' => 0.75, 'ruido' => ['Pitido', 'Silbido'],
                           'frecuencia' => [3000, 4000, 6000], 'permanente' => 0.6],
            'conciencia' => [25, 55],
        ],
        'coclear_plana' => [
            'label' => 'Coclear plana',
            'categoria' => 'sensorial',
            'sn_shape' => [125 => 40, 250 => 40, 500 => 45, 1000 => 45, 2000 => 45, 3000 => 45, 4000 => 50, 6000 => 50, 8000 => 50],
            'sn_scale' => [0.6, 1.5], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada', 'severa', 'profunda'],
            'tinnitus' => ['prob' => 0.45, 'ruido' => ['Zumbido', 'Siseo'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.6],
            'conciencia' => [40, 70],
        ],
        'meniere' => [
            'label' => 'Ménière (ascendente, graves)',
            'categoria' => 'sensorial',
            // Al revés que la presbiacusia: el hidrops pega en los graves y
            // los agudos se conservan. Fluctuante en la clínica; el caso
            // guarda una foto del momento.
            'sn_shape' => [125 => 50, 250 => 50, 500 => 45, 1000 => 35, 2000 => 25, 3000 => 20, 4000 => 20, 6000 => 20, 8000 => 20],
            'sn_scale' => [0.6, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [95, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            // El hidrops se estaciona en el rango moderado: la curva
            // ascendente con agudos conservados no promedia más alto sin
            // dejar de ser ascendente.
            'grados' => ['leve', 'moderada'],
            // Hidrops saccular: el cVEMP se apaga y el oVEMP, que mide el
            // utrículo por el nervio superior, se conserva mejor.
            'vemp' => ['type' => 'sacular',
                       'umbral' => ['CVEMP' => [80, 95], 'OVEMP' => [60, 72], 'MVEMP' => [80, 95]]],
            'tinnitus' => ['prob' => 0.85, 'ruido' => ['Zumbido'],
                           'frecuencia' => [125, 250, 500], 'permanente' => 0.5],
            'conciencia' => [80, 100],
        ],
        'subita' => [
            'label' => 'Hipoacusia súbita',
            'categoria' => 'sensorial',
            'sn_shape' => [125 => 55, 250 => 55, 500 => 60, 1000 => 60, 2000 => 60, 3000 => 62, 4000 => 65, 6000 => 65, 8000 => 65],
            'sn_scale' => [0.6, 1.5], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['moderada', 'severa', 'profunda'],
            'tinnitus' => ['prob' => 0.7, 'ruido' => ['Pitido', 'Zumbido'],
                           'frecuencia' => [2000, 4000, 6000], 'permanente' => 0.8],
            'conciencia' => [85, 100],
        ],
        'fractura_transversal' => [
            'label' => 'Fractura transversal de peñasco',
            'categoria' => 'sensorial',
            // El trazo cruza PERPENDICULAR al eje y parte el laberinto (y a
            // menudo el CAI): cóclea destruida, anacusia o casi, vértigo
            // intenso con nistagmo. Es la otra cara de la longitudinal y por
            // eso no está entre las conductivas: acá el oído medio puede
            // estar impecable --tímpano normal, curva A-- y el oído no oye.
            'sn_shape' => [125 => 90, 250 => 90, 500 => 92, 1000 => 92, 2000 => 92, 3000 => 92, 4000 => 95, 6000 => 95, 8000 => 95],
            'sn_scale' => [0.8, 1.2], 'gap_shape' => [], 'gap_scale' => [0, 0],
            // La cóclea está muerta, no desincronizada: las OEA se van con
            // ella (cce 100) y el ABR no tiene de dónde salir.
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['severa', 'profunda'],
            // Arreflexia vestibular del lado: se lleva el laberinto completo,
            // así que los DOS VEMP se apagan. Se modela con 'neural' porque
            // es el único type del catálogo que pega en cVEMP y oVEMP a la
            // vez ('sacular' y 'utricular' tocan uno cada uno) -- la lesión
            // acá es laberíntica, no del nervio.
            'vemp' => ['type' => 'neural',
                       'umbral' => ['CVEMP' => [92, 95], 'OVEMP' => [92, 95], 'MVEMP' => [92, 95]]],
            'tinnitus' => ['prob' => 0.6, 'ruido' => ['Pitido', 'Zumbido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.8],
            // Instalación brusca y dramática: nadie duda de cuándo fue.
            'conciencia' => [90, 100],
        ],
        'ototoxica' => [
            'label' => 'Ototóxica (agudos, bilateral simétrica)',
            'categoria' => 'sensorial',
            // Empieza por la base coclear y baja: más abrupta que la
            // presbiacusia y sin la asimetría del trauma acústico.
            'sn_shape' => [125 => 0, 250 => 0, 500 => 0, 1000 => 5, 2000 => 20, 3000 => 45, 4000 => 60, 6000 => 70, 8000 => 75],
            'sn_scale' => [0.6, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            // Más abrupta todavía que la presbiacusia: con 500 y 1000 intactos
            // el promedio no llega a moderada, y subirlos la aplanaría --
            // justo la pendiente que hace sospechar el ototóxico.
            'grados' => ['leve'],
            'tinnitus' => ['prob' => 0.65, 'ruido' => ['Pitido', 'Siseo'],
                           'frecuencia' => [4000, 6000, 8000], 'permanente' => 0.7],
            'conciencia' => [30, 60],
        ],

        'nihl_cronica' => [
            'label' => 'Hipoacusia por ruido crónica (NIHL)',
            'categoria' => 'sensorial',
            // La muesca de 'muesca_4k' ensanchada y bilateral: años de
            // exposición comen 3-6 kHz y la recuperación en 8 kHz se
            // achica. Es una FOTO: la progresión no es un eje del caso.
            'sn_shape' => [125 => 0, 250 => 0, 500 => 5, 1000 => 8, 2000 => 20, 3000 => 38, 4000 => 48, 6000 => 45, 8000 => 30],
            'sn_scale' => [0.7, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            // Mismo techo que la muesca: con 500 y 1000 conservados el
            // promedio no pasa de leve sin aplanar la muesca.
            'grados' => ['leve'],
            'tinnitus' => ['prob' => 0.8, 'ruido' => ['Pitido', 'Siseo'],
                           'frecuencia' => [3000, 4000, 6000], 'permanente' => 0.7],
            // Se instaló en años y el paciente se adaptó: "yo escucho bien,
            // es la gente que habla bajo".
            'conciencia' => [20, 50],
        ],
        'trauma_acustico_agudo' => [
            'label' => 'Trauma acústico agudo (explosión)',
            'categoria' => 'sensorial',
            // Una sola exposición: muesca más profunda y estrecha que la
            // crónica, y de un solo lado (el oído que quedó expuesto). Si
            // además rompió el tímpano, el cuadro de ese oído es mixto.
            'sn_shape' => [125 => 0, 250 => 0, 500 => 5, 1000 => 10, 2000 => 25, 3000 => 50, 4000 => 62, 6000 => 50, 8000 => 35],
            'sn_scale' => [0.7, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve'],
            'tinnitus' => ['prob' => 0.85, 'ruido' => ['Pitido', 'Silbido'],
                           'frecuencia' => [3000, 4000, 6000], 'permanente' => 0.7],
            'conciencia' => [90, 100],
        ],
        'salicilatos' => [
            'label' => 'Ototoxicidad por salicilatos / quinina',
            'categoria' => 'sensorial',
            // Plana y bilateral, al revés que los aminoglucósidos, que
            // empiezan por la base coclear ('ototoxica'). El acúfeno es
            // desproporcionado para lo poco que baja el audiograma, y ese
            // desbalance es el hallazgo. La REVERSIBILIDAD no se modela: el
            // caso es una foto (ver TODO.md, "Eje temporal").
            'sn_shape' => [125 => 28, 250 => 28, 500 => 30, 1000 => 30, 2000 => 30, 3000 => 32, 4000 => 32, 6000 => 34, 8000 => 34],
            'sn_scale' => [0.6, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'], 'max_db' => 55,
            'tinnitus' => ['prob' => 0.9, 'ruido' => ['Pitido', 'Silbido'],
                           'frecuencia' => [4000, 6000], 'permanente' => 0.4],
            'conciencia' => [75, 95],
        ],
        'laberintitis' => [
            'label' => 'Laberintitis (viral / bacteriana)',
            'categoria' => 'sensorial',
            'sn_shape' => [125 => 70, 250 => 72, 500 => 75, 1000 => 75, 2000 => 78, 3000 => 78, 4000 => 80, 6000 => 80, 8000 => 80],
            'sn_scale' => [0.7, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['severa', 'profunda'],
            // El laberinto entero está inflamado, no solo la cóclea: los dos
            // VEMP se apagan. Acá SÍ es regla del cuadro (a diferencia de la
            // súbita, donde el compromiso vestibular es variable).
            'vemp' => ['type' => 'neural',
                       'umbral' => ['CVEMP' => [90, 95], 'OVEMP' => [90, 95], 'MVEMP' => [90, 95]]],
            'tinnitus' => ['prob' => 0.6, 'ruido' => ['Zumbido', 'Pitido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.6],
            'conciencia' => [90, 100],
        ],
        'osificacion_coclear' => [
            'label' => 'Osificación coclear post-meningitis',
            'categoria' => 'sensorial',
            // 'coclear_plana' en su extremo y bilateral: OEA ausentes, ABR
            // sin respuesta. Lo que lo hace un cuadro aparte es la ventana
            // quirúrgica, que no sale del audiograma.
            'sn_shape' => [125 => 90, 250 => 92, 500 => 95, 1000 => 95, 2000 => 95, 3000 => 95, 4000 => 98, 6000 => 98, 8000 => 98],
            'sn_scale' => [0.8, 1.2], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['profunda'],
            // La meningitis no respeta la división: se lleva el laberinto
            // completo, como la fractura transversal.
            'vemp' => ['type' => 'neural',
                       'umbral' => ['CVEMP' => [92, 95], 'OVEMP' => [92, 95], 'MVEMP' => [92, 95]]],
            'tinnitus' => ['prob' => 0.3, 'ruido' => ['Zumbido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.6],
            'conciencia' => [60, 90],
        ],
        'conmocion_laberintica' => [
            'label' => 'Conmoción laberíntica (TEC sin fractura)',
            'categoria' => 'sensorial',
            // Tímpano normal y curva A: el golpe no pasó por el oído medio,
            // sacudió el laberinto. Por eso NO está entre las conductivas
            // aunque el antecedente sea el mismo que el de la fractura
            // longitudinal.
            'sn_shape' => [125 => 0, 250 => 5, 500 => 10, 1000 => 15, 2000 => 35, 3000 => 45, 4000 => 50, 6000 => 50, 8000 => 50],
            'sn_scale' => [0.6, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'],
            // Sin `vemp` a propósito, mismo criterio que la súbita: el
            // compromiso vestibular del TEC es real pero variable caso a
            // caso, y como regla enseñaría una asociación que no existe.
            'tinnitus' => ['prob' => 0.5, 'ruido' => ['Pitido', 'Zumbido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.5],
            'conciencia' => [90, 100],
        ],
        'hidrops_retardado' => [
            'label' => 'Hidrops endolinfático retardado',
            'categoria' => 'sensorial',
            // La curva del Ménière en un oído que ya venía dañado años
            // antes. Igual que el Ménière, el caso guarda una foto: la
            // fluctuación semana a semana no es un eje del modelo.
            'sn_shape' => [125 => 52, 250 => 52, 500 => 48, 1000 => 38, 2000 => 28, 3000 => 22, 4000 => 22, 6000 => 22, 8000 => 22],
            'sn_scale' => [0.6, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [95, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'],
            'vemp' => ['type' => 'sacular',
                       'umbral' => ['CVEMP' => [80, 95], 'OVEMP' => [60, 72], 'MVEMP' => [80, 95]]],
            'tinnitus' => ['prob' => 0.7, 'ruido' => ['Zumbido'],
                           'frecuencia' => [125, 250, 500], 'permanente' => 0.5],
            'conciencia' => [70, 95],
        ],
        'autoinmune' => [
            'label' => 'Autoinmune del oído interno / otosífilis',
            'categoria' => 'sensorial',
            // Bilateral y rápidamente progresiva: semanas a meses, no años.
            // La ASIMETRÍA marcada que la caracteriza hoy solo se puede
            // pedir a mano (ver TODO.md, "Asimetría declarada por el cuadro").
            'sn_shape' => [125 => 40, 250 => 42, 500 => 45, 1000 => 48, 2000 => 55, 3000 => 58, 4000 => 60, 6000 => 62, 8000 => 62],
            'sn_scale' => [0.6, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada', 'severa'],
            'tinnitus' => ['prob' => 0.5, 'ruido' => ['Zumbido', 'Siseo'],
                           'frecuencia' => [1000, 2000, 4000], 'permanente' => 0.6],
            // Bajó rápido y el paciente lo vio bajar.
            'conciencia' => [80, 100],
        ],
        'parotiditis' => [
            'label' => 'Parotiditis / sarampión (profunda unilateral)',
            'categoria' => 'sensorial',
            'sn_shape' => [125 => 88, 250 => 90, 500 => 92, 1000 => 92, 2000 => 92, 3000 => 92, 4000 => 95, 6000 => 95, 8000 => 95],
            'sn_scale' => [0.8, 1.2], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['severa', 'profunda'],
            'tinnitus' => ['prob' => 0.2, 'ruido' => ['Zumbido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.5],
            // Pasó en la infancia y el otro oído tapó el hueco: se descubre
            // años después, en un examen escolar o laboral.
            'conciencia' => [15, 45],
        ],
        'metabolica' => [
            'label' => 'Diabetes / insuficiencia renal (descendente bilateral)',
            'categoria' => 'sensorial',
            // La forma de la presbiacusia, adelantada: lo que la hace un
            // hallazgo es que está PEOR que la mediana de su edad, y esa
            // comparación la hace ageNorm() cuando se elige el paciente.
            'sn_shape' => [125 => 0, 250 => 5, 500 => 10, 1000 => 15, 2000 => 30, 3000 => 42, 4000 => 50, 6000 => 55, 8000 => 58],
            'sn_scale' => [0.8, 1.6], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'],
            'tinnitus' => ['prob' => 0.45, 'ruido' => ['Siseo', 'Pitido'],
                           'frecuencia' => [4000, 6000], 'permanente' => 0.5],
            'conciencia' => [25, 55],
        ],

        // --- Genéticas y congénitas -------------------------------------
        // Van como sensoriales (salvo el kernícterus, que es neural) y lo
        // que las separa NO es el gen: es la forma, la lateralidad y la
        // edad de instalación. El gen y el síndrome viven en la anamnesis.
        'gjb2' => [
            'label' => 'No sindrómica GJB2 (conexina 26)',
            'categoria' => 'sensorial',
            // Plana, bilateral, simétrica y ESTABLE desde el nacimiento:
            // es el patrón de la sordera congénita más frecuente.
            'sn_shape' => [125 => 60, 250 => 62, 500 => 65, 1000 => 65, 2000 => 68, 3000 => 68, 4000 => 70, 6000 => 70, 8000 => 70],
            'sn_scale' => [0.6, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['moderada', 'severa', 'profunda'],
            'conciencia' => [10, 40],
        ],
        'usher' => [
            'label' => 'Usher (descendente + retinosis)',
            'categoria' => 'sensorial',
            // Curva de presbiacusia en alguien que no tiene edad para eso.
            // La retinosis pigmentaria es anamnesis, no audiograma.
            'sn_shape' => [125 => 5, 250 => 8, 500 => 15, 1000 => 25, 2000 => 45, 3000 => 55, 4000 => 60, 6000 => 65, 8000 => 65],
            'sn_scale' => [0.7, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'],
            'conciencia' => [30, 60],
        ],
        'waardenburg' => [
            'label' => 'Waardenburg (profunda congénita)',
            'categoria' => 'sensorial',
            'sn_shape' => [125 => 85, 250 => 88, 500 => 90, 1000 => 90, 2000 => 90, 3000 => 92, 4000 => 92, 6000 => 92, 8000 => 92],
            'sn_scale' => [0.8, 1.2], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['severa', 'profunda'],
            'conciencia' => [10, 40],
        ],
        'alport' => [
            'label' => 'Alport (descendente en agudos, adolescencia)',
            'categoria' => 'sensorial',
            // Misma pendiente de la ototóxica sin el antecedente del
            // fármaco: eso lo resuelve la anamnesis, no el audiograma.
            'sn_shape' => [125 => 0, 250 => 0, 500 => 5, 1000 => 10, 2000 => 25, 3000 => 45, 4000 => 55, 6000 => 62, 8000 => 65],
            'sn_scale' => [0.6, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve'],
            'tinnitus' => ['prob' => 0.4, 'ruido' => ['Pitido', 'Siseo'],
                           'frecuencia' => [4000, 6000], 'permanente' => 0.5],
            'conciencia' => [25, 55],
        ],
        'jervell_lange_nielsen' => [
            'label' => 'Jervell-Lange-Nielsen (profunda + QT largo)',
            'categoria' => 'sensorial',
            'sn_shape' => [125 => 90, 250 => 92, 500 => 95, 1000 => 95, 2000 => 95, 3000 => 95, 4000 => 98, 6000 => 98, 8000 => 98],
            'sn_scale' => [0.8, 1.2], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [100, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['profunda'],
            'conciencia' => [10, 40],
        ],
        'stickler' => [
            'label' => 'Stickler (descendente + artropatía y miopía)',
            'categoria' => 'sensorial',
            'sn_shape' => [125 => 10, 250 => 12, 500 => 18, 1000 => 25, 2000 => 38, 3000 => 45, 4000 => 50, 6000 => 52, 8000 => 52],
            'sn_scale' => [0.6, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'],
            'conciencia' => [25, 55],
        ],
        'cmv_congenito' => [
            'label' => 'CMV congénito (asimétrica progresiva)',
            'categoria' => 'sensorial',
            // Puede nacer con screening normal y caerse después: el caso
            // muestra UN momento de esa historia (ver TODO.md, "Eje temporal").
            'sn_shape' => [125 => 30, 250 => 32, 500 => 38, 1000 => 42, 2000 => 50, 3000 => 55, 4000 => 58, 6000 => 60, 8000 => 60],
            'sn_scale' => [0.5, 1.5], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada', 'severa'],
            'conciencia' => [10, 40],
        ],
        'rubeola_congenita' => [
            'label' => 'Rubéola / toxoplasmosis congénita',
            'categoria' => 'sensorial',
            'sn_shape' => [125 => 55, 250 => 58, 500 => 60, 1000 => 62, 2000 => 65, 3000 => 65, 4000 => 68, 6000 => 68, 8000 => 68],
            'sn_scale' => [0.6, 1.5], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['moderada', 'severa', 'profunda'],
            'conciencia' => [10, 40],
        ],

        // --- Neurales (retrococleares puras) ----------------------------
        // cce_pct bajo: la cóclea está viva, la OEA se conserva con el
        // umbral elevado y lo que se desarma es el ABR. Ese contraste ES el
        // hallazgo.
        'schwannoma' => [
            'label' => 'Schwannoma vestibular',
            'categoria' => 'neural',
            'sn_shape' => [125 => 10, 250 => 10, 500 => 15, 1000 => 20, 2000 => 30, 3000 => 40, 4000 => 45, 6000 => 50, 8000 => 55],
            'sn_scale' => [0.5, 1.2], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [10, 35], 'retro' => 'schwannoma', 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            // Con esta forma descendente el promedio no pasa de ~70 sin que
            // 4 kHz sature, y saturarla la aplanaría: dejaría de ser el
            // descendente asimétrico que hace sospechar el retro. Lo que
            // este cuadro enseña es la disociación (audiograma moderado con
            // ABR desarmado y OEA conservada), no la profundidad.
            'grados' => ['leve', 'moderada'],
            // El schwannoma nace del nervio VESTIBULAR: el VEMP se desarma
            // de los dos lados de la división, y ese hallazgo suele llegar
            // antes que el audiograma.
            'vemp' => ['type' => 'neural',
                       'umbral' => ['CVEMP' => [82, 95], 'OVEMP' => [80, 95], 'MVEMP' => [85, 95]]],
            'tinnitus' => ['prob' => 0.65, 'ruido' => ['Pitido', 'Zumbido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.7],
            'conciencia' => [70, 95],
        ],
        'neuropatia' => [
            'label' => 'Neuropatía auditiva / desincronía (ANSD)',
            'categoria' => 'neural',
            'sn_shape' => [125 => 45, 250 => 45, 500 => 50, 1000 => 50, 2000 => 50, 3000 => 50, 4000 => 55, 6000 => 55, 8000 => 55],
            'sn_scale' => [0.6, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [0, 10], 'retro' => 'ansd', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada', 'severa', 'profunda'],
            // VEMP CONSERVADO, y es a propósito: en la ANSD la lesión es de
            // la vía auditiva y el nervio vestibular queda indemne. Un ABR
            // desarmado con VEMP normal es lo que separa esto de un
            // compromiso del VIII completo.
            'vemp' => ['type' => 'normal',
                       'umbral' => ['CVEMP' => [55, 70], 'OVEMP' => [60, 75], 'MVEMP' => [65, 80]]],
        ],

        'kernicterus' => [
            'label' => 'Kernícterus (hiperbilirrubinemia neonatal)',
            'categoria' => 'neural',
            // NO es coclear, aunque el antecedente sea neonatal: las OEA se
            // conservan y lo que se desarma es el ABR. Ese contraste es todo
            // el cuadro, y es el mismo error que hay que evitar con la ANSD.
            'sn_shape' => [125 => 40, 250 => 42, 500 => 45, 1000 => 45, 2000 => 48, 3000 => 48, 4000 => 50, 6000 => 50, 8000 => 50],
            'sn_scale' => [0.6, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [0, 15], 'retro' => 'kernicterus', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada', 'severa', 'profunda'],
            // Vestibular conservado, igual que en la ANSD: la bilirrubina
            // pega en los núcleos auditivos del tronco, no en el nervio
            // vestibular.
            'vemp' => ['type' => 'normal',
                       'umbral' => ['CVEMP' => [55, 70], 'OVEMP' => [60, 75], 'MVEMP' => [65, 80]]],
            'conciencia' => [10, 40],
        ],
        'nf2' => [
            'label' => 'Neurofibromatosis tipo 2 (schwannomas bilaterales)',
            'categoria' => 'neural',
            // El patrón del schwannoma en LOS DOS oídos: sin un lado sano
            // que sirva de referencia, el IT5 no ayuda y hay que leer los
            // interpicos absolutos. Esa es la trampa del cuadro.
            'sn_shape' => [125 => 10, 250 => 10, 500 => 15, 1000 => 20, 2000 => 30, 3000 => 40, 4000 => 45, 6000 => 50, 8000 => 55],
            'sn_scale' => [0.5, 1.2], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [10, 35], 'retro' => 'nf2', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'],
            'vemp' => ['type' => 'neural',
                       'umbral' => ['CVEMP' => [82, 95], 'OVEMP' => [80, 95], 'MVEMP' => [85, 95]]],
            'tinnitus' => ['prob' => 0.6, 'ruido' => ['Pitido', 'Zumbido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.7],
            'conciencia' => [60, 90],
        ],
        'tumor_angulo' => [
            'label' => 'Meningioma / epidermoide del ángulo pontocerebeloso',
            'categoria' => 'neural',
            // Indistinguible del schwannoma en el ABR: la diferencia la hace
            // la imagen. Está en el catálogo justamente para que el alumno
            // no cierre el diagnóstico con el PEATC.
            'sn_shape' => [125 => 10, 250 => 10, 500 => 15, 1000 => 20, 2000 => 30, 3000 => 40, 4000 => 45, 6000 => 50, 8000 => 55],
            'sn_scale' => [0.5, 1.2], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [10, 35], 'retro' => 'angulo', 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'],
            'vemp' => ['type' => 'neural',
                       'umbral' => ['CVEMP' => [80, 95], 'OVEMP' => [80, 95], 'MVEMP' => [82, 95]]],
            'tinnitus' => ['prob' => 0.55, 'ruido' => ['Pitido', 'Zumbido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.6],
            'conciencia' => [60, 90],
        ],
        'compresion_microvascular' => [
            'label' => 'Compresión microvascular del VIII par',
            'categoria' => 'neural',
            // Alteración leve y a veces solo visible con tasas altas: el
            // audiograma casi no se mueve. cce por debajo de CCE_COCLEAR_PCT
            // a propósito -- si sube más, el cuadro que lo mide es
            // 'sensorioneural', que usa este mismo preset con los dos
            // componentes.
            'sn_shape' => [125 => 5, 250 => 5, 500 => 8, 1000 => 12, 2000 => 20, 3000 => 28, 4000 => 32, 6000 => 35, 8000 => 38],
            'sn_scale' => [0.5, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [25, 55], 'retro' => 'microvascular', 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve'],
            'vemp' => ['type' => 'neural',
                       'umbral' => ['CVEMP' => [65, 82], 'OVEMP' => [65, 82], 'MVEMP' => [70, 88]]],
            'tinnitus' => ['prob' => 0.6, 'ruido' => ['Pitido', 'Zumbido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.5],
            'conciencia' => [60, 90],
        ],
        'esclerosis_multiple' => [
            'label' => 'Esclerosis múltiple / desmielinizante',
            'categoria' => 'neural',
            // Audiograma normal o casi, con I-III limpio y III-V largo: la
            // lesión es intraaxial, después del núcleo coclear. Es el cuadro
            // que enseña que un audiograma normal no descarta nada.
            'sn_shape' => [125 => 5, 250 => 5, 500 => 8, 1000 => 8, 2000 => 10, 3000 => 12, 4000 => 15, 6000 => 18, 8000 => 20],
            'sn_scale' => [0.4, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [20, 55], 'retro' => 'esclerosis_multiple', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve'],
            'conciencia' => [60, 90],
        ],
        'infarto_pontino' => [
            'label' => 'Infarto pontino / AICA',
            'categoria' => 'neural',
            'sn_shape' => [125 => 8, 250 => 8, 500 => 10, 1000 => 12, 2000 => 15, 3000 => 18, 4000 => 20, 6000 => 22, 8000 => 25],
            'sn_scale' => [0.4, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [15, 45], 'retro' => 'infarto_pontino', 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve'],
            'conciencia' => [90, 100],
        ],
        'glioma_tronco' => [
            'label' => 'Glioma de tronco / tumor de fosa posterior',
            'categoria' => 'neural',
            'sn_shape' => [125 => 10, 250 => 12, 500 => 15, 1000 => 18, 2000 => 22, 3000 => 25, 4000 => 28, 6000 => 30, 8000 => 32],
            'sn_scale' => [0.5, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [10, 40], 'retro' => 'glioma_tronco', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'],
            'conciencia' => [55, 85],
        ],
        'siderosis' => [
            'label' => 'Siderosis superficial del SNC',
            'categoria' => 'neural',
            // Bilateral progresiva con ataxia: la hemosiderina se deposita
            // sobre el VIII en su trayecto cisternal, así que además del
            // ABR se cae el VEMP.
            'sn_shape' => [125 => 20, 250 => 22, 500 => 28, 1000 => 32, 2000 => 42, 3000 => 48, 4000 => 52, 6000 => 55, 8000 => 58],
            'sn_scale' => [0.5, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [10, 40], 'retro' => 'siderosis', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'],
            'vemp' => ['type' => 'neural',
                       'umbral' => ['CVEMP' => [82, 95], 'OVEMP' => [82, 95], 'MVEMP' => [85, 95]]],
            'tinnitus' => ['prob' => 0.5, 'ruido' => ['Zumbido', 'Siseo'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.6],
            'conciencia' => [40, 70],
        ],
        'chiari_hic' => [
            'label' => 'Chiari / hipertensión intracraneal',
            'categoria' => 'neural',
            // Compresión difusa: todo corrido y los interpicos largos, sin
            // un tramo que domine.
            'sn_shape' => [125 => 5, 250 => 5, 500 => 8, 1000 => 10, 2000 => 12, 3000 => 15, 4000 => 18, 6000 => 20, 8000 => 22],
            'sn_scale' => [0.4, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [20, 55], 'retro' => 'chiari_hic', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve'],
            'conciencia' => [55, 85],
        ],
        'leucodistrofia' => [
            'label' => 'Leucodistrofia (Krabbe, adrenoleucodistrofia)',
            'categoria' => 'neural',
            // Interpicos muy largos con audiograma conservado, en un niño:
            // la disociación es el hallazgo y el tamiz neonatal no la ve.
            'sn_shape' => [125 => 5, 250 => 5, 500 => 8, 1000 => 8, 2000 => 10, 3000 => 12, 4000 => 15, 6000 => 15, 8000 => 18],
            'sn_scale' => [0.4, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [0, 20], 'retro' => 'leucodistrofia', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve'],
            'conciencia' => [10, 40],
        ],
        'neuropatia_hereditaria' => [
            'label' => 'Neuropatía hereditaria (CMT, Friedreich)',
            'categoria' => 'neural',
            'sn_shape' => [125 => 10, 250 => 12, 500 => 15, 1000 => 18, 2000 => 25, 3000 => 30, 4000 => 35, 6000 => 38, 8000 => 40],
            'sn_scale' => [0.5, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [5, 35], 'retro' => 'hereditaria_central', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'],
            // Polineuropatía: el nervio vestibular es un nervio más.
            'vemp' => ['type' => 'neural',
                       'umbral' => ['CVEMP' => [78, 92], 'OVEMP' => [78, 92], 'MVEMP' => [80, 95]]],
            'conciencia' => [30, 60],
        ],
        'tec_tronco' => [
            'label' => 'TEC con lesión de tronco',
            'categoria' => 'neural',
            'sn_shape' => [125 => 15, 250 => 15, 500 => 20, 1000 => 22, 2000 => 28, 3000 => 32, 4000 => 35, 6000 => 38, 8000 => 40],
            'sn_scale' => [0.5, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [10, 45], 'retro' => 'tec_tronco', 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'],
            'tinnitus' => ['prob' => 0.5, 'ruido' => ['Zumbido', 'Pitido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.5],
            'conciencia' => [90, 100],
        ],
        'toxico_metabolico' => [
            'label' => 'Tóxico-metabólico (hepática, hipotiroidismo)',
            'categoria' => 'neural',
            // Todo lento y, a diferencia del resto de esta lista,
            // reversible al corregir la causa. La reversibilidad no se
            // modela: el caso es una foto.
            'sn_shape' => [125 => 5, 250 => 5, 500 => 8, 1000 => 10, 2000 => 12, 3000 => 15, 4000 => 18, 6000 => 20, 8000 => 20],
            'sn_scale' => [0.4, 1.3], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [20, 55], 'retro' => 'toxico_metabolico', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve'],
            'conciencia' => [40, 70],
        ],
        'hipotermia_farmacos' => [
            'label' => 'Hipotermia / depresores del SNC',
            'categoria' => 'neural',
            // Audiograma NORMAL y ABR corrido entero, onda I incluida, con
            // los interpicos intactos: es el único cuadro donde se mueve la
            // onda I, y por eso no tiene grado de hipoacusia.
            'sn_shape' => [125 => 3, 250 => 3, 500 => 3, 1000 => 3, 2000 => 5, 3000 => 5, 4000 => 5, 6000 => 8, 8000 => 8],
            'sn_scale' => [0.0, 1.2], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [20, 55], 'retro' => 'hipotermia_farmacos', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => [],
            'conciencia' => [40, 70],
        ],
        'prematuro' => [
            'label' => 'Retraso madurativo del prematuro',
            'categoria' => 'neural',
            // No es patología: es maduración. Sin hipoacusia y sin grado --
            // lo que corre son las latencias por edad, y la normativa de
            // neonato ya las corre por su cuenta.
            'sn_shape' => [125 => 3, 250 => 3, 500 => 3, 1000 => 3, 2000 => 5, 3000 => 5, 4000 => 5, 6000 => 8, 8000 => 8],
            'sn_scale' => [0.0, 1.2], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [20, 50], 'retro' => 'prematuro', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => [],
            'conciencia' => [10, 40],
        ],
        'bloqueo_proximal' => [
            'label' => 'Bloqueo proximal del VIII (coma)',
            'categoria' => 'neural',
            // Onda I presente y nada después: la cóclea está viva y la vía
            // se corta enseguida. El paciente no colabora con la
            // audiometría --el cuadro se define por el ABR, no por el
            // audiograma--, así que no lleva grado.
            'sn_shape' => [125 => 3, 250 => 3, 500 => 3, 1000 => 3, 2000 => 5, 3000 => 5, 4000 => 5, 6000 => 8, 8000 => 8],
            'sn_scale' => [0.0, 1.2], 'gap_shape' => [], 'gap_scale' => [0, 0],
            'cce_pct' => [0, 20], 'retro' => 'bloqueo_proximal', 'lateralidad' => 'bilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => [],
            // No hay entrevista posible: el rasgo queda en el piso.
            'conciencia' => [0, 20],
        ],

        // --- Sensorioneurales (los dos componentes a la vez) ------------
        'sensorioneural' => [
            'label' => 'Coclear con componente retrococlear',
            'categoria' => 'sensorioneural',
            'sn_shape' => [125 => 30, 250 => 30, 500 => 35, 1000 => 40, 2000 => 45, 3000 => 50, 4000 => 55, 6000 => 55, 8000 => 55],
            'sn_scale' => [0.6, 1.4], 'gap_shape' => [], 'gap_scale' => [0, 0],
            // El punto del cuadro: ni 100 ni 0. La OEA dice cuánto hay de
            // coclear y el ABR cuánto de retro, y separarlos es el ejercicio.
            'cce_pct' => [20, 80], 'retro' => 'microvascular', 'lateralidad' => 'unilateral',
            'z' => ['A'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada', 'severa'],
            // Microvascular: compromiso neural parcial, más leve que el del
            // schwannoma.
            'vemp' => ['type' => 'neural',
                       'umbral' => ['CVEMP' => [70, 85], 'OVEMP' => [70, 85], 'MVEMP' => [75, 90]]],
            'tinnitus' => ['prob' => 0.5, 'ruido' => ['Pitido', 'Zumbido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.6],
        ],

        // --- Mixtas (conductiva + sensorioneural) -----------------------
        'mixta_otitis_cronica' => [
            'label' => 'Otitis crónica con daño coclear',
            'categoria' => 'mixta',
            'sn_shape' => [125 => 25, 250 => 25, 500 => 30, 1000 => 30, 2000 => 35, 3000 => 40, 4000 => 45, 6000 => 45, 8000 => 45],
            'sn_scale' => [0.7, 1.3],
            'gap_shape' => [125 => 30, 250 => 30, 500 => 28, 1000 => 25, 2000 => 22, 3000 => 20, 4000 => 20, 6000 => 20, 8000 => 20],
            'gap_scale' => [0.6, 1.1],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['B'], 'etf' => 'Disfunción tubaria',
            // Acá el promedio SÍ puede llegar a profunda, porque lo sube la
            // ósea (el daño coclear) y no el gap. La cadena erosionada de una
            // otitis crónica sí llega a 55 dB de transmisión.
            'grados' => ['leve', 'moderada', 'severa', 'profunda'],
            'gap_max_db' => 55,
            // El VEMP aéreo lo apaga el oído medio: el estímulo no llega. No
            // hay lesión vestibular (type normal), lo que sube es el umbral
            // -- y sube tanto como el gap, que ya está en el audiograma.
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.45, 'ruido' => ['Zumbido', 'Siseo'],
                           'frecuencia' => [500, 1000, 2000], 'permanente' => 0.5],
        ],
        'mixta_otoesclerosis' => [
            'label' => 'Otoesclerosis avanzada (con daño coclear)',
            'categoria' => 'mixta',
            'sn_shape' => [125 => 30, 250 => 30, 500 => 35, 1000 => 38, 2000 => 45, 3000 => 42, 4000 => 40, 6000 => 45, 8000 => 45],
            'sn_scale' => [0.7, 1.3],
            'gap_shape' => [125 => 30, 250 => 30, 500 => 28, 1000 => 22, 2000 => 15, 3000 => 18, 4000 => 20, 6000 => 20, 8000 => 20],
            'gap_scale' => [0.5, 1.1],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['As'], 'etf' => 'Normal',
            // Igual que la otra mixta: el grado alto lo pone la ósea, no el
            // gap, que sigue topado por lo que el estribo fijo puede atenuar.
            'grados' => ['leve', 'moderada', 'severa', 'profunda'],
            'gap_max_db' => 55,
            // El VEMP aéreo lo apaga el oído medio: el estímulo no llega. No
            // hay lesión vestibular (type normal), lo que sube es el umbral
            // -- y sube tanto como el gap, que ya está en el audiograma.
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.55, 'ruido' => ['Zumbido', 'Campanilleo'],
                           'frecuencia' => [250, 500, 1000], 'permanente' => 0.5],
        ],
        'colesteatoma_fistula' => [
            'label' => 'Colesteatoma con fístula laberíntica',
            'categoria' => 'mixta',
            // El gap del colesteatoma más la caída coclear de la fístula: el
            // mismo oído tiene los dos componentes, y separarlos es el
            // ejercicio. El vértigo con presión (signo de la fístula) vive
            // en la anamnesis.
            'sn_shape' => [125 => 30, 250 => 32, 500 => 35, 1000 => 38, 2000 => 42, 3000 => 45, 4000 => 48, 6000 => 50, 8000 => 50],
            'sn_scale' => [0.6, 1.3],
            'gap_shape' => [125 => 46, 250 => 46, 500 => 45, 1000 => 42, 2000 => 40, 3000 => 38, 4000 => 38, 6000 => 38, 8000 => 38],
            'gap_scale' => [0.5, 1.0],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['B'], 'etf' => 'Disfunción tubaria',
            'grados' => ['leve', 'moderada', 'severa'], 'max_db' => 90, 'gap_max_db' => 55,
            // Hay lesión laberíntica, pero el VEMP AÉREO no llega a
            // mostrarla: lo apaga antes el oído medio. Por eso va atado al
            // gap y no a un rango -- las dos formas son excluyentes.
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.5, 'ruido' => ['Zumbido', 'Siseo'],
                           'frecuencia' => [500, 1000, 2000], 'permanente' => 0.5],
            'conciencia' => [70, 95],
        ],
        'oido_operado' => [
            'label' => 'Oído operado (timpanoplastia / mastoidectomía)',
            'categoria' => 'mixta',
            // Gap residual chico y ósea algo caída: el resultado habitual de
            // una cirugía que funcionó. La curva depende de qué quedó --Ad
            // si el injerto es laxo, B si hay cavidad--.
            'sn_shape' => [125 => 15, 250 => 15, 500 => 18, 1000 => 20, 2000 => 25, 3000 => 28, 4000 => 30, 6000 => 32, 8000 => 32],
            'sn_scale' => [0.5, 1.3],
            'gap_shape' => [125 => 26, 250 => 26, 500 => 24, 1000 => 22, 2000 => 20, 3000 => 18, 4000 => 18, 6000 => 18, 8000 => 18],
            'gap_scale' => [0.4, 1.1],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['Ad', 'B'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'], 'max_db' => 55, 'gap_max_db' => 35,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.4, 'ruido' => ['Zumbido'],
                           'frecuencia' => [500, 1000], 'permanente' => 0.4],
            'conciencia' => [60, 90],
        ],
        'paget' => [
            'label' => 'Enfermedad de Paget / otoespongiosis',
            'categoria' => 'mixta',
            // Mixta bilateral y progresiva: el hueso remodelado fija la
            // cadena y compromete la cápsula ótica a la vez.
            'sn_shape' => [125 => 25, 250 => 28, 500 => 32, 1000 => 35, 2000 => 40, 3000 => 45, 4000 => 48, 6000 => 50, 8000 => 52],
            'sn_scale' => [0.6, 1.3],
            'gap_shape' => [125 => 28, 250 => 28, 500 => 26, 1000 => 24, 2000 => 22, 3000 => 20, 4000 => 20, 6000 => 20, 8000 => 20],
            'gap_scale' => [0.5, 1.1],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'bilateral',
            'z' => ['As'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada', 'severa'], 'max_db' => 90, 'gap_max_db' => 45,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.5, 'ruido' => ['Zumbido', 'Campanilleo'],
                           'frecuencia' => [250, 500, 1000], 'permanente' => 0.5],
            'conciencia' => [30, 60],
        ],
        'carcinoma_cae' => [
            'label' => 'Carcinoma de CAE / tumor temporal',
            'categoria' => 'mixta',
            // Gap grande por la masa que ocupa el conducto MÁS compromiso
            // coclear por invasión: unilateral y progresivo. La parálisis
            // facial, que es el dato que apura la derivación, no sale del
            // audiograma.
            'sn_shape' => [125 => 35, 250 => 38, 500 => 42, 1000 => 45, 2000 => 50, 3000 => 55, 4000 => 58, 6000 => 60, 8000 => 60],
            'sn_scale' => [0.6, 1.3],
            'gap_shape' => [125 => 48, 250 => 48, 500 => 46, 1000 => 44, 2000 => 42, 3000 => 40, 4000 => 40, 6000 => 40, 8000 => 40],
            'gap_scale' => [0.5, 1.0],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['B'], 'etf' => 'Normal',
            'grados' => ['moderada', 'severa', 'profunda'], 'max_db' => 105, 'gap_max_db' => 56,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.4, 'ruido' => ['Zumbido'],
                           'frecuencia' => [500, 1000], 'permanente' => 0.5],
            'conciencia' => [80, 100],
        ],
        'trauma_craneal_completo' => [
            'label' => 'Trauma craneal con fractura y conmoción',
            'categoria' => 'mixta',
            // Los dos cuadros del TEC en el MISMO oído: el gap de la
            // fractura longitudinal (hemotímpano, cadena luxada) sobre la
            // caída en agudos de la conmoción laberíntica. Pedir cada uno
            // por separado en oídos distintos es otro caso, no este.
            'sn_shape' => [125 => 10, 250 => 15, 500 => 20, 1000 => 25, 2000 => 40, 3000 => 48, 4000 => 52, 6000 => 52, 8000 => 52],
            'sn_scale' => [0.6, 1.3],
            'gap_shape' => [125 => 45, 250 => 45, 500 => 42, 1000 => 38, 2000 => 35, 3000 => 32, 4000 => 30, 6000 => 30, 8000 => 30],
            'gap_scale' => [0.5, 1.1],
            'cce_pct' => [90, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['B'], 'etf' => 'Normal',
            'grados' => ['leve', 'moderada'], 'max_db' => 75, 'gap_max_db' => 50,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.5, 'ruido' => ['Zumbido', 'Pitido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.6],
            'conciencia' => [90, 100],
        ],
        'post_radioterapia' => [
            'label' => 'Post-radioterapia de cabeza y cuello',
            'categoria' => 'mixta',
            // Dos mecanismos con tiempos distintos: la otitis por disfunción
            // tubaria aparece durante el tratamiento y la caída coclear en
            // agudos se instala después, y sigue.
            'sn_shape' => [125 => 10, 250 => 12, 500 => 18, 1000 => 22, 2000 => 35, 3000 => 45, 4000 => 52, 6000 => 55, 8000 => 58],
            'sn_scale' => [0.6, 1.4],
            'gap_shape' => [125 => 32, 250 => 32, 500 => 30, 1000 => 26, 2000 => 22, 3000 => 20, 4000 => 20, 6000 => 20, 8000 => 20],
            'gap_scale' => [0.4, 1.1],
            'cce_pct' => [85, 100], 'retro' => null, 'lateralidad' => 'unilateral',
            'z' => ['B'], 'etf' => 'Disfunción tubaria',
            'grados' => ['leve', 'moderada'], 'max_db' => 75, 'gap_max_db' => 45,
            'vemp' => ['type' => 'normal', 'umbral_gap' => true],
            'tinnitus' => ['prob' => 0.45, 'ruido' => ['Siseo', 'Zumbido'],
                           'frecuencia' => [2000, 4000], 'permanente' => 0.5],
            'conciencia' => [55, 85],
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
        $out = [
            'air' => [], 'bone' => [], 'gap' => [], 'sn' => [], 'cce' => [], 'retro_sn' => [],
            // Frecuencias donde no hubo respuesta, por vía. Quien derive algo
            // de esa frecuencia tiene que saber que el número es un piso y no
            // una medición (ver SIN_RESPUESTA_DB).
            'sin_respuesta' => ['air' => [], 'bone' => []],
        ];

        foreach (CaseBuilder::FREQUENCIES as $i => $hz) {
            $air = (float) ($airPairs[$i][$side] ?? 0);
            // Sin ósea cargada, el oído se lee sensorioneural puro (gap 0),
            // que es lo conservador: inventar un gap cambiaría el examen.
            $bone = (float) ($bonePairs[$i][$side] ?? $air);

            // Sin respuesta: el umbral no es 130, es "al menos el tope del
            // audiómetro". Se recorta ahí y se deja anotado.
            if ($air >= self::SIN_RESPUESTA_DB) {
                $out['sin_respuesta']['air'][] = $hz;
                $air = self::MAX_AUDIOMETRO_DB;
            }
            if ($bone >= self::SIN_RESPUESTA_DB) {
                $out['sin_respuesta']['bone'][] = $hz;
                // Sin respuesta por vía ósea el gap no se puede medir: se
                // lee sensorioneural puro, que es lo conservador.
                $bone = $air;
            }

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
    public static function abrThresholds(array $decomp, string $pathway = 'air_conduction', $edadMeses = null): array
    {
        // Vía ósea en lactante: el cráneo sin suturar transmite mejor, así
        // que el mismo oído da un umbral más bajo en el dial (ver
        // INFANT_BONE_CALIBRATION_DB). Solo la ósea: la aérea entra por el
        // conducto y no le importa el cráneo.
        $calibracion = $pathway === 'bone_conduction'
            ? self::infantBoneFactor($edadMeses)
            : 0.0;
        $curva = $pathway === 'bone_conduction' ? $decomp['bone'] : $decomp['air'];
        $sinRespuesta = ($decomp['sin_respuesta'] ?? [])[$pathway === 'bone_conduction' ? 'bone' : 'air'] ?? [];
        $out = [];
        foreach (self::STIM_WEIGHTS as $stim => $pesos) {
            // Si NINGUNA de las frecuencias que pesan ese estímulo respondió
            // en el tonal, el ABR tampoco va a responder: es "sin respuesta"
            // y no un umbral saturado en el tope, que se leería como un
            // hallazgo medido.
            $conRespuesta = array_diff(array_keys($pesos), $sinRespuesta);
            if ($conRespuesta === []) {
                $out[$stim] = null;
                continue;
            }

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
            if ($calibracion > 0.0) {
                // La corrección pesa las mismas frecuencias que el estímulo:
                // un burst de 500 se lleva los 15 dB enteros y uno de 4 kHz
                // casi nada, que es como se comporta el cráneo.
                $ajuste = 0.0;
                $pesoAjuste = 0.0;
                foreach ($pesos as $hz => $w) {
                    $ajuste += (self::INFANT_BONE_CALIBRATION_DB[(int) $hz] ?? 0.0) * $w;
                    $pesoAjuste += $w;
                }
                if ($pesoAjuste > 0) {
                    $nhl -= ($ajuste / $pesoAjuste) * $calibracion;
                }
            }
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
    // Logoaudiometria
    // ---------------------------------------------------------------

    /**
     * Frecuencias que fijan el NIVEL del habla (las mismas de Fletcher,
     * que ya usan fletcherAvg/SRT).
     */
    public const SPEECH_FREQS = [500, 1000, 2000];

    /**
     * Peso de cada frecuencia en la DISCRIMINACIÓN, que no es lo mismo que
     * el nivel: las consonantes viven en 2-4 kHz. Con el promedio de
     * Fletcher a secas, una descendente con graves conservados daba 100% de
     * discriminación -- y una caída en agudos es justo la que se come las
     * consonantes y deja al paciente diciendo "oigo pero no entiendo".
     */
    public const SPEECH_WEIGHTS = [500 => 0.15, 1000 => 0.25, 2000 => 0.30, 4000 => 0.30];

    /**
     * Caída de la discriminación por dB de pérdida, según el sitio.
     *
     * La coclear pierde discriminación despacio y en proporción a la
     * pérdida: 40 dB deja ~85%, que sigue siendo funcional. La
     * retrococlear la pierde mucho más rápido y desproporcionadamente al
     * audiograma -- es la DISOCIACIÓN AUDIO-VERBAL, el signo retrococlear
     * más clásico que hay, y sin esto el caso no lo puede mostrar.
     */
    public const LOGO_CCE_SLOPE = 0.8;
    public const LOGO_CCE_KNEE_DB = 20.0;
    public const LOGO_RETRO_SLOPE = 1.8;
    public const LOGO_RETRO_KNEE_DB = 10.0;

    /** Cuánto por encima del umbral del habla se alcanza el máximo. */
    public const LOGO_SL_DB = 35.0;
    /** Salida máxima practicable del canal de habla. */
    public const LOGO_MAX_DB = 110.0;

    /**
     * Máxima discriminación del oído y a qué intensidad se alcanza.
     *
     * El gap NO baja el porcentaje: una conductiva no distorsiona, solo
     * atenúa. Lo que hace es correr la curva a la derecha, así que entra
     * en la intensidad y no en el máximo.
     *
     * El porcentaje se cuantiza a múltiplos de 4 porque es la grilla que
     * usa el motor del logoaudiograma (`por_logo` en
     * src/audiometria/logoaudiometry.py); un valor fuera de la grilla
     * revienta el índice al armar la curva.
     *
     * El reclutamiento (rollover: la curva CAE pasado el máximo) no se
     * decide acá -- sale del flag `recruit`, que ya deriva recruitment().
     *
     * @param array $decomp Salida de decompose()
     * @return array{pct:int, int:int}
     */
    public static function discrimination(array $decomp, float $ccePct, array $retro): array
    {
        $ccePct = self::clamp($ccePct, 0.0, 100.0);
        // Para el porcentaje manda la banda de las consonantes; para la
        // intensidad a la que se alcanza, el promedio de Fletcher.
        $snDiscrim = self::weightedAverage($decomp['sn'], self::SPEECH_WEIGHTS);
        $sn = self::speechAverage($decomp['sn']);
        $gap = self::speechAverage($decomp['gap']);
        $cce = $snDiscrim * $ccePct / 100.0;
        $retroSn = $snDiscrim - $cce;

        $porCoclear = max(0.0, $cce - self::LOGO_CCE_KNEE_DB) * self::LOGO_CCE_SLOPE;
        $porRetro = max(0.0, $retroSn - self::LOGO_RETRO_KNEE_DB) * self::LOGO_RETRO_SLOPE;
        // Un patrón retrococlear cargado castiga la discriminación aunque
        // el audiograma esté limpio: un schwannoma chico se delata así.
        if (self::retroActivo($retro)) {
            $porRetro += 20.0;
        }
        $pct = self::clamp(100.0 - $porCoclear - $porRetro, 0.0, 100.0);

        return [
            'pct' => (int) (round($pct / 4) * 4),
            'int' => (int) self::clamp(
                round(($sn + $gap + self::LOGO_SL_DB) / 5) * 5, 0.0, self::LOGO_MAX_DB
            ),
        ];
    }

    // ---------------------------------------------------------------
    // Campo dinamico (LDL)
    // ---------------------------------------------------------------

    /**
     * Nivel de disconfort en un oído sano (dB HL). Es casi constante: no
     * sube con la pérdida coclear, y ESE es el punto -- el umbral sube, el
     * LDL no, y el campo dinámico se estrecha solo. El reclutamiento no
     * hay que dibujarlo, cae de la física.
     */
    public const LDL_NORMAL_DB = 100.0;
    /** Campo dinámico mínimo que deja una cóclea dañada. */
    public const LDL_MIN_RANGE_DB = 10.0;
    /** Campo dinámico de un oído SIN reclutamiento (retrococlear). */
    public const LDL_FULL_RANGE_DB = 95.0;
    /** Tope del audiómetro para el LDL. 130 es el centinela de "no medido". */
    public const LDL_MAX_DB = 120.0;

    /**
     * Curva de LDL por frecuencia (dB HL).
     *
     * Coclear: el LDL se queda donde está y el campo dinámico se cierra.
     * Retrococlear: el LDL sube con el umbral, el campo dinámico se
     * conserva y no hay reclutamiento. Conductiva: todo corrido por el
     * gap, porque el oído medio atenúa también lo fuerte.
     *
     * @param array $decomp Salida de decompose()
     * @return array<int,int> índice de CaseBuilder::FREQUENCIES -> dB HL
     */
    public static function ldlCurve(array $decomp, float $ccePct): array
    {
        $fraccionRetro = 1.0 - self::clamp($ccePct, 0.0, 100.0) / 100.0;
        $rango = self::LDL_MIN_RANGE_DB
            + (self::LDL_FULL_RANGE_DB - self::LDL_MIN_RANGE_DB) * $fraccionRetro;

        $out = [];
        foreach (CaseBuilder::FREQUENCIES as $i => $hz) {
            $sn = $decomp['sn'][$hz] ?? 0.0;
            $gap = $decomp['gap'][$hz] ?? 0.0;
            $ldl = $gap + max(self::LDL_NORMAL_DB, $sn + $rango);
            $out[$i] = (int) self::clamp(round($ldl / 5) * 5, 0.0, self::LDL_MAX_DB);
        }
        return $out;
    }

    /**
     * Promedio ponderado de una curva (Hz => dB).
     *
     * @param array<int,float> $curva
     * @param array<int,float> $pesos Hz => peso
     */
    public static function weightedAverage(array $curva, array $pesos): float
    {
        $suma = 0.0;
        $peso = 0.0;
        foreach ($pesos as $hz => $w) {
            $nivel = self::levelAt($curva, (float) $hz);
            if ($nivel !== null) {
                $suma += $nivel * $w;
                $peso += $w;
            }
        }
        return $peso > 0 ? $suma / $peso : 0.0;
    }

    /**
     * Promedio de una curva (Hz => dB) en la zona del habla.
     *
     * @param array<int,float> $curva
     */
    public static function speechAverage(array $curva): float
    {
        $suma = 0.0;
        $n = 0;
        foreach (self::SPEECH_FREQS as $hz) {
            $nivel = self::levelAt($curva, (float) $hz);
            if ($nivel !== null) {
                $suma += $nivel;
                $n++;
            }
        }
        return $n > 0 ? $suma / $n : 0.0;
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

    /**
     * Morfología de la curva del reflejo (ver CaseBuilder::REFLEX_CURVE_TYPES).
     *
     * Solo se deriva el patrón OFF, que es el decay del reflejo: la
     * contracción no se sostiene y cae durante la estimulación. Es signo
     * retrococlear, del mismo eje que el deterioro tonal.
     *
     * 'invertido' y 'on-off' se dejan siempre al docente a propósito: el
     * primero es un artefacto de registro (sonda mal sellada, presión mal
     * compensada) y el segundo un hallazgo puntual; ninguno se deduce del
     * sitio de la lesión, y sortearlos solo agregaría ruido al caso.
     *
     * @param array<string,mixed> $retro
     */
    public static function reflexCurveType(array $decomp, float $ccePct, array $retro): string
    {
        if (self::retroActivo($retro)) {
            return 'off';
        }
        $retroSn = self::coreMax($decomp['sn']) * (1.0 - self::clamp($ccePct, 0.0, 100.0) / 100.0);
        return $retroSn >= 30.0 ? 'off' : 'normal';
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
    public static function project(array $airPairs, array $bonePairs, array $perfil, array $tympPorLado, $horasDeVida = null, $edadMeses = null, array $nacimiento = []): array
    {
        $decomp = [];
        foreach (['OD' => 0, 'OI' => 1] as $lado => $sideIdx) {
            $decomp[$lado] = self::decompose(
                $airPairs, $bonePairs, $sideIdx, (float) ($perfil[$lado]['cce_pct'] ?? self::DEFAULT_CCE_PCT)
            );
        }

        $abr = [];
        $eoas = [];
        $reflex = ['ipsi' => [], 'contra' => [], 'tipo' => []];
        $recPorLado = [];
        $logo = [];
        $ldl = [];
        foreach (CaseBuilder::LADOS as $ladoForm => $lado) {
            $ccePct = (float) ($perfil[$lado]['cce_pct'] ?? self::DEFAULT_CCE_PCT);
            $retro = self::normalizeRetro($perfil[$lado]['retro'] ?? []);
            $otro = $lado === 'OD' ? 'OI' : 'OD';

            // Transitorio de las primeras horas: no es patología del caso,
            // es la edad del paciente. Por oído, porque la cantidad de
            // líquido no es la misma en los dos (y por eso uno refiere y el
            // otro no, que es lo que se ve en el turno).
            $transitorio = self::neonatalTransientDb($horasDeVida, $nacimiento, $lado);

            $porEstimulo = self::abrThresholds($decomp[$lado], 'air_conduction');
            if ($transitorio > 0.0) {
                // Solo la vía aérea: el vibrador saltea conducto y oído
                // medio, y ese contraste es el hallazgo.
                $sumaAbr = $transitorio * self::NEONATAL_ABR_FACTOR;
                foreach ($porEstimulo as $stim => $db) {
                    if ($db === null) {
                        continue;
                    }
                    $porEstimulo[$stim] = (int) self::clamp(
                        round(($db + $sumaAbr) / self::ABR_STEP_DB) * self::ABR_STEP_DB,
                        0.0,
                        (float) self::ABR_MAX_DB
                    );
                }
            }
            $abr[$lado] = [
                // El tipo decide la física de la curva (corrimiento paralelo
                // de la conductiva, pendiente L-I de la coclear, interpicos
                // del retro): derivar el umbral y dejar el tipo a mano deja
                // curvas que no se corresponden con ningún oído.
                'type' => self::derivedType($decomp[$lado], $ccePct, $retro),
                // El caso guarda UN número y el cliente lo lee como tal: sin
                // respuesta se escribe el tope, que es como el propio módulo
                // expresa "no hubo respuesta en toda la escala". El detalle
                // --con su null-- viaja en umbral_por_estimulo.
                'umbral' => $porEstimulo['click'] ?? self::ABR_MAX_DB,
                'umbral_por_estimulo' => $porEstimulo,
                'umbral_por_estimulo_oseo' => self::abrThresholds($decomp[$lado], 'bone_conduction', $edadMeses),
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
            if ($transitorio > 0.0) {
                // atten_db es la atenuación pareja que el cliente suma tal
                // cual (ver oae_attenuation_db): acá entra al doble porque
                // el sonido cruza el conducto de ida y de vuelta.
                $eoas[$lado]['atten_db'] = round($transitorio * self::NEONATAL_OAE_FACTOR, 1);
            }

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
            $reflex['tipo'][$ladoForm] = self::reflexCurveType($decomp[$lado], $ccePct, $retro);

            $recPorLado[$lado] = self::recruitment($ccePct, $decomp[$lado]);
            $logo[$lado] = self::discrimination($decomp[$lado], $ccePct, $retro);
            $ldl[$ladoForm] = self::ldlCurve($decomp[$lado], $ccePct);
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
            foreach (CaseBuilder::LADOS as $ladoForm => $lado) {
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
                // El LDL va con el reclutamiento: es su expresión
                // audiométrica, el umbral sube y el disconfort no.
                'ldl' => $ldl,
            ],
            'logo' => $logo,
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
    /** Gap desde el cual un timpanograma A es una contradicción. */
    public const WARN_TYMP_GAP_DB = 20.0;
    /** Gap por debajo del cual un timpanograma B es una contradicción. */
    public const WARN_TYMP_NO_GAP_DB = 10.0;

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

            // --- Oído medio: el timpanograma nunca se deriva (qué curva
            // sale depende de la patología concreta, no del audiograma),
            // así que es el único lugar donde la contradicción solo se
            // puede avisar. Y es la que más se escapa: un gap de 40 dB con
            // timpanograma A no existe.
            $tymp = (string) ($tympPorLado[$lado] ?? 'A');
            $gapMax = self::coreMax($decomp['gap']);
            if ($tymp === 'A' && $gapMax >= self::WARN_TYMP_GAP_DB) {
                $avisos[] = sprintf(
                    'Timpanometría %s: curva A (oído medio normal) con un gap aéreo-óseo de %d dB. Un oído medio que funciona no produce gap -- elegí B (ocupación), As (rígido), Ad (hipercompliante) o C, o sacá el gap del audiograma.',
                    $lado, (int) round($gapMax)
                );
            }
            if ($tymp === 'B' && $gapMax < self::WARN_TYMP_NO_GAP_DB) {
                $avisos[] = sprintf(
                    'Timpanometría %s: curva B (oído medio ocupado o sin movilidad) con gap de %d dB. Una ocupación siempre deja gap: cargalo en la vía aérea o cambiá el timpanograma.',
                    $lado, (int) round($gapMax)
                );
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
