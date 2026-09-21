<?php

// Las derivaciones del perfil auditivo viven aparte (CaseProfile), pero
// caseDataToForm() las necesita para releer un caso guardado.
require_once __DIR__ . '/CaseProfile.php';
// La sala del caso (paciente + acompañantes) se guarda dentro de
// cases.data, así que buildCaseData()/caseDataToForm() la necesitan.
require_once __DIR__ . '/Sala.php';
// Qué fichas declaró revisadas el docente: también viaja en cases.data.
require_once __DIR__ . '/CaseReview.php';

final class CaseBuilder
{
    // Mismas 9 frecuencias que usa el audiómetro (Fowler en create_a.py
    // enumera esta misma lista) -- Aerea/Osea/LDL/Reflex se indexan por
    // posición en este array, no por el valor Hz.
    public const FREQUENCIES = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000];

    /**
     * Los dos oídos: clave del formulario => etiqueta, que es además la
     * clave con la que viajan en cases.data ('OD'/'OI'). El literal estaba
     * escrito 15 veces entre el editor y la vista previa del perfil.
     */
    public const LADOS = ['od' => 'OD', 'oi' => 'OI'];

    public const HIST_CHECKBOXES = [
        'hipoacusia_familiar', 'ototoxicos', 'trauma_acustico', 'otitis',
        'meningitis', 'tce', 'diabetes', 'hta',
    ];

    // Mismas etiquetas que case_create.php pinta junto a cada checkbox --
    // repetidas acá (en vez de que ese archivo las importe) porque acá las
    // usa LlmConfig::buildSystemPrompt() para armar el resumen en texto de
    // los antecedentes marcados, sin acoplarse al archivo del formulario.
    public const HIST_LABELS = [
        'hipoacusia_familiar' => 'Hipoacusia familiar', 'ototoxicos' => 'Ototóxicos',
        'trauma_acustico' => 'Trauma acústico', 'otitis' => 'Otitis', 'meningitis' => 'Meningitis',
        'tce' => 'TCE', 'diabetes' => 'Diabetes', 'hta' => 'HTA',
    ];

    // Ficha Otoscopia: N tomas en el tiempo por oído (misma cantidad para
    // OD y OI). 1 sola fase = "única" (no hay selector de modo aparte: el
    // número de fases mismo lo dice). Cada fase lleva un texto libre que
    // describe qué pasó desde la fase anterior (vacío en la fase 1 --
    // todavía no hay "anterior"). Qué fase le corresponde ver a cada
    // alumno según su propio avance con ese paciente: TODO, ver TODO.md.
    public const OTOSCOPIA_MAX_FASES = 20;

    public const Z_OPTIONS = ['A', 'As', 'Ad', 'C', 'Cs', 'B'];

    /**
     * Timpanograma de ALTA FRECUENCIA (sonda de 1000 Hz), el del lactante.
     *
     * No lleva letra de Jerger: el protocolo es binario, hay pico o no hay
     * (positivo / negativo). 'auto' lo deriva de la letra de 226 Hz ya
     * cargada --A/Ad casi siempre positivo, As borderline, B/C sin pico casi
     * siempre negativo--, que es lo que el simulador hacía siempre. Las
     * otras dos opciones son para cuando el caso NECESITA un resultado
     * concreto: un lactante con el oído medio ocupado que a 226 Hz se ve
     * normal y solo la sonda de 1000 Hz delata, no puede quedar librado al
     * sorteo.
     */
    public const Z1000_OPTIONS = ['auto', 'positivo', 'negativo'];
    public const Z1000_LABELS = [
        'auto' => 'Derivado de la curva de 226 Hz',
        'positivo' => 'Positivo (con pico)',
        'negativo' => 'Negativo (sin pico)',
    ];
    public const ETF_OPTIONS = ['Normal', 'Disfunción tubaria', 'Permeable', 'No permeable'];

    // Patología ABR por oído -- ver AbrMainWindow.py::test_test() (llama a
    // ABR_Curve, que mapea 'transmission' -> 'conductive' internamente).
    public const ABR_TYPE_OPTIONS = ['normal', 'coclear', 'transmission', 'neural'];

    // "Neural" no es un hallazgo ni un catálogo de diagnósticos: es un
    // conjunto de PATRONES electrofisiológicos que se combinan. El ABR no
    // separa un schwannoma de un meningioma del ángulo --eso lo dice la
    // RM-- pero sí separa un I-III largo de un III-V largo, un bloqueo
    // proximal de una desincronía, o un retraso global de uno selectivo.
    // Por eso el caso guarda PARÁMETROS, no una etiqueta diagnóstica: la
    // curva nunca depende del nombre. Las entidades clínicas viven como
    // presets (ABR_NEURAL_PRESETS) que precargan estos valores en el
    // formulario y quedan editables; el preset elegido NO se persiste.
    // Las claves y los defaults tienen que coincidir con
    // NEURAL_PARAM_DEFAULTS en src/abr/ABR_generator.py.
    /**
     * Infecciones congénitas (TORCH) que el JCIH 2019 lista como indicador
     * de riesgo. NO mueven el tamizaje --no son líquido en el conducto--
     * pero sí obligan a seguimiento: varias dan hipoacusia progresiva o de
     * aparición tardía, y el caso "pasó el tamizaje y a los seis meses no"
     * es el que hay que poder armar.
     */
    public const TORCH_OPTIONS = [
        '' => 'Ninguna',
        'cmv' => 'Citomegalovirus (CMV)',
        'toxoplasmosis' => 'Toxoplasmosis',
        'rubeola' => 'Rubéola',
        'sifilis' => 'Sífilis',
        'herpes' => 'Herpes simple',
        'zika' => 'Zika',
        'vih' => 'VIH',
    ];

    /** Muy bajo peso al nacer, en gramos (JCIH 2019). */
    public const PESO_MUY_BAJO_G = 1500;

    public const ABR_NEURAL_DEFAULTS = [
        'i_iii_ms' => 0.2,          // prolongación selectiva I-III
        'iii_v_ms' => 0.2,          // prolongación selectiva III-V
        'global_delay_ms' => 0.0,   // corre TODO, onda I incluida
        'bloqueo' => 'ninguno',
        'v_i_factor' => 0.45,       // amplitud de la V respecto de la I
        'microfonica' => 'normal',
        'desincronia' => 'ninguna',
        'sensibilidad_tasa' => 'severa',
    ];
    public const ABR_NEURAL_BLOQUEO_OPTIONS = ['ninguno', 'post_i', 'total'];
    public const ABR_NEURAL_BLOQUEO_LABELS = [
        'ninguno' => 'Sin bloqueo',
        'post_i' => 'Solo onda I (bloqueo proximal)',
        'total' => 'Ninguna onda',
    ];
    public const ABR_NEURAL_MICROFONICA_OPTIONS = ['normal', 'amplificada'];
    public const ABR_NEURAL_MICROFONICA_LABELS = [
        'normal' => 'Normal',
        'amplificada' => 'Amplificada (patrón de desincronía)',
    ];
    public const ABR_NEURAL_DESINCRONIA_OPTIONS = ['ninguna', 'leve', 'alta'];
    public const ABR_NEURAL_TASA_OPTIONS = ['normal', 'moderada', 'severa'];

    // Rangos aceptados de los parámetros numéricos (ms / factor).
    public const ABR_NEURAL_MAX_MS = 4.0;

    // Entidades clínicas como punto de partida. Varias comparten patrón a
    // propósito -- el PEATC no las distingue entre sí, las separa la
    // imagen o la clínica --, y eso es justamente lo que el alumno tiene
    // que entender. Los valores son plausibles, no dogma: se editan.
    public const ABR_NEURAL_PRESETS = [
        'schwannoma' => [
            'label' => 'Schwannoma vestibular',
            'nota' => 'I normal, I-V prolongado, V/I caída. Compará el IT5 con el otro oído.',
            'params' => ['i_iii_ms' => 0.45, 'iii_v_ms' => 0.35, 'global_delay_ms' => 0.0,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.40, 'microfonica' => 'normal',
                'desincronia' => 'leve', 'sensibilidad_tasa' => 'severa'],
        ],
        'nf2' => [
            'label' => 'Neurofibromatosis tipo 2 (bilateral)',
            'nota' => 'Mismo patrón que el schwannoma, pero hay que cargarlo en LOS DOS oídos: sin asimetría, el IT5 no ayuda.',
            'params' => ['i_iii_ms' => 0.45, 'iii_v_ms' => 0.35, 'global_delay_ms' => 0.0,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.40, 'microfonica' => 'normal',
                'desincronia' => 'leve', 'sensibilidad_tasa' => 'severa'],
        ],
        'angulo' => [
            'label' => 'Tumor del ángulo pontocerebeloso (meningioma, epidermoide)',
            'nota' => 'Indistinguible del schwannoma en el PEATC: la diferencia la hace la RM.',
            'params' => ['i_iii_ms' => 0.40, 'iii_v_ms' => 0.30, 'global_delay_ms' => 0.0,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.50, 'microfonica' => 'normal',
                'desincronia' => 'leve', 'sensibilidad_tasa' => 'moderada'],
        ],
        'microvascular' => [
            'label' => 'Compresión microvascular del VIII par',
            'nota' => 'Alteración leve, a veces solo visible con tasas altas.',
            'params' => ['i_iii_ms' => 0.25, 'iii_v_ms' => 0.15, 'global_delay_ms' => 0.0,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.70, 'microfonica' => 'normal',
                'desincronia' => 'ninguna', 'sensibilidad_tasa' => 'moderada'],
        ],
        'ansd' => [
            'label' => 'Neuropatía auditiva / desincronía (ANSD)',
            'nota' => 'Sin ondas + microfónico que invierte con la polaridad (buscalo con rarefacción y condensación, no con alternada). En la pestaña EOA este oído va "Neural": OEA presentes.',
            'params' => ['i_iii_ms' => 0.0, 'iii_v_ms' => 0.0, 'global_delay_ms' => 0.0,
                'bloqueo' => 'total', 'v_i_factor' => 0.45, 'microfonica' => 'amplificada',
                'desincronia' => 'alta', 'sensibilidad_tasa' => 'severa'],
        ],
        'esclerosis_multiple' => [
            'label' => 'Esclerosis múltiple / desmielinizante',
            'nota' => 'I-III normal y III-V largo (lesión intraaxial), con fatiga marcada a tasas altas.',
            'params' => ['i_iii_ms' => 0.05, 'iii_v_ms' => 0.60, 'global_delay_ms' => 0.0,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.45, 'microfonica' => 'normal',
                'desincronia' => 'alta', 'sensibilidad_tasa' => 'severa'],
        ],
        'infarto_pontino' => [
            'label' => 'Infarto pontino / AICA',
            'nota' => 'III-V muy prolongado o V ausente, según la altura de la lesión.',
            'params' => ['i_iii_ms' => 0.0, 'iii_v_ms' => 0.70, 'global_delay_ms' => 0.0,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.35, 'microfonica' => 'normal',
                'desincronia' => 'alta', 'sensibilidad_tasa' => 'moderada'],
        ],
        'glioma_tronco' => [
            'label' => 'Glioma de tronco / tumor de fosa posterior',
            'params' => ['i_iii_ms' => 0.10, 'iii_v_ms' => 0.65, 'global_delay_ms' => 0.0,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.35, 'microfonica' => 'normal',
                'desincronia' => 'alta', 'sensibilidad_tasa' => 'moderada'],
        ],
        'chiari_hic' => [
            'label' => 'Chiari / hipertensión intracraneal / hidrocefalia',
            'nota' => 'Compresión difusa: algo de todo, sin un interpico dominante.',
            'params' => ['i_iii_ms' => 0.15, 'iii_v_ms' => 0.45, 'global_delay_ms' => 0.10,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.55, 'microfonica' => 'normal',
                'desincronia' => 'leve', 'sensibilidad_tasa' => 'moderada'],
        ],
        'kernicterus' => [
            'label' => 'Hiperbilirrubinemia neonatal / kernícterus',
            'nota' => 'Interpicos prolongados y morfología pobre. La forma severa se comporta como ANSD: en ese caso usá ese preset.',
            'params' => ['i_iii_ms' => 0.40, 'iii_v_ms' => 0.50, 'global_delay_ms' => 0.0,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.35, 'microfonica' => 'normal',
                'desincronia' => 'alta', 'sensibilidad_tasa' => 'severa'],
        ],
        'leucodistrofia' => [
            'label' => 'Leucodistrofia (adrenoleucodistrofia, metacromática, Krabbe)',
            'nota' => 'Desmielinización difusa: todo prolongado y ondas rostrales que se van perdiendo.',
            'params' => ['i_iii_ms' => 0.50, 'iii_v_ms' => 0.60, 'global_delay_ms' => 0.20,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.35, 'microfonica' => 'normal',
                'desincronia' => 'alta', 'sensibilidad_tasa' => 'severa'],
        ],
        'hereditaria_central' => [
            'label' => 'Neuropatía hereditaria con compromiso central (CMT, Friedreich)',
            'params' => ['i_iii_ms' => 0.60, 'iii_v_ms' => 0.50, 'global_delay_ms' => 0.0,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.30, 'microfonica' => 'normal',
                'desincronia' => 'alta', 'sensibilidad_tasa' => 'severa'],
        ],
        'siderosis' => [
            'label' => 'Siderosis superficial del SNC',
            'params' => ['i_iii_ms' => 0.55, 'iii_v_ms' => 0.40, 'global_delay_ms' => 0.0,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.35, 'microfonica' => 'normal',
                'desincronia' => 'alta', 'sensibilidad_tasa' => 'severa'],
        ],
        'toxico_metabolico' => [
            'label' => 'Tóxico-metabólico (encefalopatía hepática, hipotiroidismo)',
            'params' => ['i_iii_ms' => 0.20, 'iii_v_ms' => 0.25, 'global_delay_ms' => 0.25,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.70, 'microfonica' => 'normal',
                'desincronia' => 'leve', 'sensibilidad_tasa' => 'moderada'],
        ],
        'hipotermia_farmacos' => [
            'label' => 'Hipotermia / depresores del SNC',
            'nota' => 'Conducción lenta pareja: corre TODO, onda I incluida, con interpicos normales. Es el único cuadro donde la onda I se mueve.',
            'params' => ['i_iii_ms' => 0.0, 'iii_v_ms' => 0.0, 'global_delay_ms' => 0.80,
                'bloqueo' => 'ninguno', 'v_i_factor' => 1.0, 'microfonica' => 'normal',
                'desincronia' => 'ninguna', 'sensibilidad_tasa' => 'normal'],
        ],
        'tec_tronco' => [
            'label' => 'TEC con lesión de tronco',
            'params' => ['i_iii_ms' => 0.20, 'iii_v_ms' => 0.60, 'global_delay_ms' => 0.10,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.35, 'microfonica' => 'normal',
                'desincronia' => 'alta', 'sensibilidad_tasa' => 'severa'],
        ],
        'bloqueo_proximal' => [
            'label' => 'Bloqueo proximal (coma, muerte encefálica)',
            'nota' => 'Cóclea viva: onda I presente y nada después. Es el patrón que se busca en el estudio de muerte encefálica.',
            'params' => ['i_iii_ms' => 0.0, 'iii_v_ms' => 0.0, 'global_delay_ms' => 0.0,
                'bloqueo' => 'post_i', 'v_i_factor' => 0.45, 'microfonica' => 'normal',
                'desincronia' => 'alta', 'sensibilidad_tasa' => 'severa'],
        ],
        'prematuro' => [
            'label' => 'Retraso madurativo del prematuro',
            'nota' => 'No es patología: es maduración. Antes de usar esto, fijate que la edad del paciente ya elige la población normativa de neonato, que corre la onda V casi 1 ms.',
            'params' => ['i_iii_ms' => 0.0, 'iii_v_ms' => 0.0, 'global_delay_ms' => 0.60,
                'bloqueo' => 'ninguno', 'v_i_factor' => 0.80, 'microfonica' => 'normal',
                'desincronia' => 'leve', 'sensibilidad_tasa' => 'moderada'],
        ],
    ];

    // Umbral máximo que puede tener un oído marcado "Normal". Sale de
    // pathology_modifiers.normal.threshold_range en
    // resources/abr/normative_data.json (y del equivalente de OEA): por
    // encima de eso el oído tiene una pérdida y hay que decir de qué tipo,
    // porque el generador usa la patología --no el umbral-- para decidir
    // la física de la curva (GAP conductivo, función latencia-intensidad
    // coclear, interpicos retrococleares). Ver normalCoherenceError().
    public const NORMAL_MAX_UMBRAL = 25;

    // Patología EOA (OEA) por oído -- mismas categorías que ABR pero la
    // OEA responde distinto: 'neural' (neuropatía/retrococlear) mantiene
    // la OEA normal porque la cóclea está intacta (a diferencia de ABR,
    // que ahí sí sale alterado). Ver oae_attenuation_db en
    // src/oae/generators/base.py.
    public const EOAS_TYPE_OPTIONS = ['normal', 'coclear', 'transmission', 'neural'];

    // Frecuencias del perfil OEA por oído. Es la unión de las bandas que
    // usa cada prueba en el cliente (TEOAE 1-4k, DP-grama 1-8k, SFOAE
    // 0.5-4k, SOAE 0.7-4.5k), así el docente configura UNA curva por oído
    // y las cuatro pruebas quedan coherentes entre sí (una muesca en 4k
    // aparece en todas, como en un paciente real). Ver
    // resources/oae/normative_data.json.
    public const EOAS_FREQS = [500, 1000, 1500, 2000, 3000, 4000, 6000, 8000];

    // Tope de atenuación por patología, en dB. Espejo de
    // MAX_PATHOLOGY_ATTEN_DB en src/oae/generators/base.py (cliente):
    // pasado ese punto la OEA ya está bajo el piso de ruido.
    public const EOAS_MAX_PATHOLOGY_ATTEN_DB = 45.0;

    // Perfiles del botón "Autocompletar" del tab EOA, por patología y GRADO.
    //
    // Antes esto era una tabla de desviaciones fijas por patología y el
    // botón NO tocaba el umbral: como el umbral default es 20 dB y la
    // atenuación coclear arranca sobre 15 dB HL, un caso marcado "coclear"
    // sin tocar el umbral a mano daba exactamente la misma pantalla que un
    // normal. De ahí que todos los casos salieran normales y que no
    // hubiera cocleares de distinto nivel.
    //
    // Ahora cada grado define el rango de umbral (dB HL) que se sortea y
    // cuánto pesa la forma de caída por frecuencia (`shape`, dB por unidad
    // de escala). Es un punto de partida al azar dentro de un rango
    // clínicamente razonable -- el docente edita cualquier campo después
    // (mismo criterio que el autocompletar de ABR, y la memoria de no
    // fijar defaults "correctos" en lo que el alumno debe aprender a leer).
    //
    // `shape` de coclear cae en agudos (las CCE basales son las primeras en
    // morir); la de transmisión atenúa parejo con algo más en graves (el
    // oído medio devuelve peor los graves); neural deja la cóclea intacta.
    public const EOAS_AUTOFILL_SHAPES = [
        'normal'       => [500 => 0, 1000 => 0, 1500 => 0, 2000 => 0, 3000 => 0, 4000 => 0, 6000 => 0, 8000 => 0],
        'coclear'      => [500 => 0.4, 1000 => 0.7, 1500 => 1.0, 2000 => 1.4, 3000 => 2.0, 4000 => 2.6, 6000 => 3.2, 8000 => 3.8],
        'transmission' => [500 => 2.4, 1000 => 2.0, 1500 => 1.7, 2000 => 1.6, 3000 => 1.4, 4000 => 1.3, 6000 => 1.3, 8000 => 1.3],
        'neural'       => [500 => 0, 1000 => 0, 1500 => 0, 2000 => 0, 3000 => 0, 4000 => 0, 6000 => 0, 8000 => 0],
    ];

    // Grados por patología: [clave, etiqueta, rango de umbral dB HL, rango
    // de escala de la forma, rango de ruido del paciente, rango de sello].
    // El primer grado de cada patología es el que se usa si el select viene
    // vacío; "random" (en el formulario) sortea entre todos.
    public const EOAS_AUTOFILL_GRADES = [
        'normal' => [
            ['key' => 'normal', 'label' => 'Normal (OEA presente)',
             'umbral' => [0, 15], 'scale' => [0, 0.6], 'ruido' => [0, 2], 'sello' => [85, 97]],
        ],
        'coclear' => [
            // Con 1.2 dB/dB sobre 15 dB HL: 22 dB HL -> 8 dB de atenuación
            // (OEA presente pero chica), 32 -> 20 dB (REFER en agudos),
            // 50+ -> 42 dB y tope (ausente en todas las bandas).
            ['key' => 'leve', 'label' => 'Coclear leve (OEA reducida, aún presente)',
             'umbral' => [20, 27], 'scale' => [0.6, 1.4], 'ruido' => [0, 3], 'sello' => [80, 95]],
            ['key' => 'moderada', 'label' => 'Coclear moderada (REFER en agudos)',
             'umbral' => [30, 40], 'scale' => [1.4, 2.4], 'ruido' => [0, 4], 'sello' => [75, 92]],
            ['key' => 'severa', 'label' => 'Coclear severa (OEA ausente)',
             'umbral' => [45, 70], 'scale' => [2.4, 3.4], 'ruido' => [0, 4], 'sello' => [70, 92]],
        ],
        'transmission' => [
            ['key' => 'leve', 'label' => 'Transmisión leve (OEA presente y atenuada)',
             'umbral' => [10, 18], 'scale' => [0.8, 1.6], 'ruido' => [1, 5], 'sello' => [70, 88]],
            ['key' => 'moderada', 'label' => 'Transmisión moderada (OEA ausente)',
             'umbral' => [25, 45], 'scale' => [1.6, 2.6], 'ruido' => [1, 6], 'sello' => [60, 85]],
        ],
        'neural' => [
            // La cóclea está sana: la OEA queda normal por más alto que
            // esté el umbral. Es el contraste con el ABR del mismo caso.
            ['key' => 'neural', 'label' => 'Neuropatía (OEA conservada, ABR alterado)',
             'umbral' => [25, 70], 'scale' => [0, 0.6], 'ruido' => [0, 3], 'sello' => [80, 95]],
        ],
    ];

    // Jitter (dB) que se suma a cada frecuencia del perfil autocompletado,
    // para que dos casos del mismo grado no queden calcados.
    public const EOAS_AUTOFILL_JITTER_DB = 1.2;

    // SOAE (emisiones espontáneas): solo ~40-50% de los oídos normales
    // las tienen, así que en 'auto' el cliente las sortea (determinístico
    // por caso: el mismo paciente da siempre lo mismo). 'presentes' y
    // 'ausentes' fijan el hallazgo para poder mostrarlo en clase o evaluar
    // sobre algo que no cambie de oído en oído. Ver true_peaks() en
    // src/oae/generators/soae.py.
    public const EOAS_SOAE_MODES = ['auto', 'presentes', 'ausentes'];
    public const EOAS_SOAE_MODE_LABELS = [
        'auto' => 'Auto (sorteo por prevalencia)',
        'presentes' => 'Presentes (forzar)',
        'ausentes' => 'Ausentes (forzar)',
    ];
    // Picos SOAE que el docente puede fijar a mano por oído. Tres alcanza:
    // un oído real rara vez muestra más de 2-3 picos claros.
    public const EOAS_SOAE_MAX_PEAKS = 3;
    public const EOAS_SOAE_FREQ_MIN = 500;
    public const EOAS_SOAE_FREQ_MAX = 7000;
    // Nivel por defecto de un pico fijado a mano: en 1-2 kHz deja ~10 dB
    // sobre el piso, o sea visible sin ser irreal (los SOAE reales rondan
    // los 0 dB SPL y rara vez pasan de 20).
    public const EOAS_SOAE_DEFAULT_PEAK_DB = 6.0;

    // Defaults del perfil OEA por oído (paciente "limpio": sin atenuación
    // extra, sin ruido agregado, sello de sonda bueno).
    public const EOAS_DEFAULTS = [
        'umbral' => 20,
        'atten_db' => 0.0,
        'ruido_db' => 0.0,
        'sello_pct' => 85,
        'variabilidad_db' => 2.5,
        'soae_mode' => 'auto',
    ];

    // Patología VEMP por oído -- categorías vestibulares. 'sacular' afecta
    // CVEMP (P13/N23 sobre SCM), 'utricular' afecta OVEMP (N10/P16 sobre
    // oblicuo inferior), 'neural' afecta ambos (neuropatía vestibular).
    // Ver VEMP_generator_v1.py::calculate_wave_parameters.
    public const VEMP_TYPE_OPTIONS = ['normal', 'sacular', 'utricular', 'neural'];
    public const VEMP_SUBTIPOS = ['CVEMP', 'OVEMP', 'MVEMP'];

    // Picos por subtipo (orden de aparición en curva/tabla/PDF).
    public const VEMP_PEAKS = [
        'CVEMP' => ['p13', 'n23'],
        'OVEMP' => ['n10', 'p16'],
        'MVEMP' => ['p13', 'n23'],
    ];

    /**
     * Cómo se nombra cada VEMP en la ficha y en los avisos del editor.
     *
     * Los tres se arman siempre. No hay un selector de "cuál es el de este
     * caso" porque el que elige es el ALUMNO, en el equipo: configurar uno
     * solo dejaba los otros dos normales pasara lo que pasara, y bastaba
     * cambiar el combo para que la patología desapareciera.
     */
    public const VEMP_SUBTIPO_LABELS = [
        'CVEMP' => 'cVEMP -- cervical',
        'OVEMP' => 'oVEMP -- ocular',
        'MVEMP' => 'mVEMP -- masetero',
    ];

    /** Umbral (dB) por defecto de cada VEMP en un oído sano. */
    public const VEMP_DEFAULTS = [
        'CVEMP' => ['umbral' => 60, 'average_objetivo' => 200],
        'OVEMP' => ['umbral' => 65, 'average_objetivo' => 300],
        'MVEMP' => ['umbral' => 70, 'average_objetivo' => 300],
    ];
    public const VEMP_REPRO_VAR_DEFAULT = 0.2;

    /**
     * Normativa del VEMP: latencias y amplitudes medianas por población y
     * subtipo, y los modificadores por patología.
     *
     * Es el MISMO archivo que carga VEMPGeneratorV1 en la app de escritorio
     * (resources/vemp/normative_data.json). Acá se lee para dibujar la vista
     * previa de la ficha: sin estos números la previa sería una curva
     * inventada que no se parece a la que el alumno va a ver en el equipo.
     *
     * Mismo mecanismo (y misma copia por deployable) que nameBank().
     */
    public static function vempNormative(): array
    {
        $path = __DIR__ . '/../resources/vemp/normative_data.json';
        $norm = is_file($path) ? json_decode((string) file_get_contents($path), true) : null;
        if (!is_array($norm)) {
            return ['populations' => [], 'pathology_modifiers' => []];
        }
        return [
            'populations' => $norm['populations'] ?? [],
            'pathology_modifiers' => $norm['pathology_modifiers'] ?? [],
        ];
    }

    // Acumetría (diapasones 500 y 1000 Hz) -- se guarda dentro de
    // audiometría, no es tab aparte. Rinne es por oído (CA vs CO en ese
    // oído); Weber es un único resultado por frecuencia (a qué lado
    // lateraliza, o ninguno). Auto-calculado desde los umbrales tonales ya
    // cargados (índices 2=500Hz, 3=1000Hz en FREQUENCIES/Aerea/Osea),
    // modificable a mano por checkbox "auto" (mismo patrón que sdt_auto/
    // srt_auto con Fletcher).
    public const ACUMETRIA_FREQS = ['500' => 2, '1000' => 3]; // Hz => índice en FREQUENCIES

    public const RINNE_OPTIONS = ['positivo', 'negativo', 'falso_negativo'];
    public const RINNE_LABELS = [
        'positivo' => 'Positivo (CA > CO)',
        'negativo' => 'Negativo (CO > CA)',
        'falso_negativo' => 'Falso negativo (hipoacusia sensorioneural profunda, cruce óseo contralateral)',
    ];
    // Gap aérea-ósea (dB) desde el cual el Rinne auto-calculado da negativo.
    public const RINNE_GAP_THRESHOLD = 15;

    public const WEBER_OPTIONS = ['centrado', 'od', 'oi'];
    public const WEBER_LABELS = [
        'centrado' => 'Sin lateralización (centrado)',
        'od' => 'Lateraliza a OD',
        'oi' => 'Lateraliza a OI',
    ];
    // Asimetría de vía ósea (dB) entre oídos desde la cual el Weber
    // auto-calculado lateraliza (al oído con mejor -- menor dB -- umbral óseo).
    public const WEBER_ASYMMETRY_THRESHOLD = 10;

    /** Rinne auto: negativo si el gap aérea-ósea de ese oído en esa frecuencia es >= RINNE_GAP_THRESHOLD. "falso_negativo" nunca se auto-calcula, es solo elegible a mano. */
    /**
     * Picos SOAE cargados en el formulario -> shape de cases.data.
     *
     * Una fila sin Hz se ignora (el docente carga 1 pico y no tres), y el
     * nivel en blanco toma EOAS_SOAE_DEFAULT_PEAK_DB.
     */
    public static function soaePeaksFromForm($rows): array
    {
        $picos = [];
        if (!is_array($rows)) {
            return $picos;
        }
        for ($i = 0; $i < self::EOAS_SOAE_MAX_PEAKS; $i++) {
            $row = is_array($rows[$i] ?? null) ? $rows[$i] : [];
            $hz = (float) ($row['hz'] ?? 0);
            if ($hz <= 0) {
                continue;
            }
            $db = $row['db'] ?? '';
            $picos[] = [
                'hz' => $hz,
                'db' => ($db === '' || $db === null) ? self::EOAS_SOAE_DEFAULT_PEAK_DB : (float) $db,
            ];
        }
        return $picos;
    }

    /**
     * Valida los picos SOAE de un oído. Devuelve el mensaje de error o null.
     *
     * La separación mínima no es capricho: dos SOAE muy juntos se suprimen
     * entre sí y no coexisten en un oído real (~0.4 bark, ~6%). Ver
     * min_peak_spacing_ratio en resources/oae/normative_data.json.
     */
    public static function soaePeaksError(array $eoasLado): ?string
    {
        $picos = $eoasLado['soae_peaks'] ?? [];
        if (($eoasLado['soae_mode'] ?? 'auto') === 'ausentes' && $picos !== []) {
            return 'SOAE en modo "ausentes" no puede tener picos cargados: borrá las frecuencias o cambiá el modo.';
        }
        // Ordenados por frecuencia: el docente puede cargarlos en cualquier
        // orden en el formulario.
        usort($picos, static fn($a, $b) => $a['hz'] <=> $b['hz']);
        $hzPrevio = null;
        foreach ($picos as $pico) {
            if ($pico['hz'] < self::EOAS_SOAE_FREQ_MIN || $pico['hz'] > self::EOAS_SOAE_FREQ_MAX) {
                return sprintf('Frecuencia SOAE fuera de rango (%d-%d Hz).',
                    self::EOAS_SOAE_FREQ_MIN, self::EOAS_SOAE_FREQ_MAX);
            }
            if ($pico['db'] < -15 || $pico['db'] > 30) {
                return 'Nivel SOAE fuera de rango (-15 a 30 dB SPL).';
            }
            if ($hzPrevio !== null && (max($pico['hz'], $hzPrevio) / min($pico['hz'], $hzPrevio)) < 1.06) {
                return 'Dos picos SOAE del mismo oído deben estar separados al menos 6% en frecuencia (se suprimen entre sí).';
            }
            $hzPrevio = $pico['hz'];
        }
        return null;
    }

    // Tolerancia por módulo para la coherencia con patología "Normal": un
    // oído sano igual tiene ruido test-retest, y "Autocompletar" con tipo
    // Normal lo sortea a propósito (±0.05 ms de latencia, ±8% de amplitud
    // en ABR -- ver buildValues() en case_create.php). Estos números son el
    // techo de ese ruido: por encima ya no es variabilidad, es un hallazgo.
    // 'lat'/'amp' aplican a desviaciones anidadas por onda; 'plano' a las
    // desviaciones por frecuencia de la OEA (dB). null = no se chequea.
    public const NORMAL_DEVIATION_TOLERANCE = [
        'ABR' => ['lat' => 0.10, 'amp' => 0.06, 'plano' => null],
        'EOA' => ['lat' => null, 'amp' => null, 'plano' => 3.0],
        // VEMP: solo latencia. Las amplitudes normativas van de 8 uV (OVEMP
        // n10) a 170 uV (CVEMP n23) -- una tolerancia absoluta única no
        // significa nada, y el validador no tiene el normativo del subtipo
        // a mano para hacerla relativa.
        'VEMP' => ['lat' => 0.5, 'amp' => null, 'plano' => null],
    ];

    /**
     * Parámetros del patrón retrococlear fuera de rango, o null si están
     * bien. Los enums se validan contra las mismas listas que el generador
     * (NEURAL_PARAM_DEFAULTS en ABR_generator.py); los ms tienen tope
     * porque una prolongación de 10 ms no es un caso clínico, es un error
     * de tipeo que deja la onda fuera de la ventana de registro.
     *
     * @param array<string,mixed> $neural
     */
    public static function neuralParamsError(array $neural, string $lado): ?string
    {
        foreach (['i_iii_ms' => 'I-III', 'iii_v_ms' => 'III-V',
                  'global_delay_ms' => 'Retraso global'] as $clave => $nombre) {
            $valor = (float) ($neural[$clave] ?? 0);
            if ($valor < 0 || $valor > self::ABR_NEURAL_MAX_MS) {
                return sprintf('ABR %s: %s = %s ms fuera de rango (0 a %s).',
                    $lado, $nombre, (string) $valor, (string) self::ABR_NEURAL_MAX_MS);
            }
        }
        $vi = (float) ($neural['v_i_factor'] ?? 1);
        if ($vi <= 0 || $vi > 1) {
            return sprintf('ABR %s: razón V/I = %s fuera de rango (más de 0, hasta 1).', $lado, (string) $vi);
        }
        $enums = [
            'bloqueo' => self::ABR_NEURAL_BLOQUEO_OPTIONS,
            'microfonica' => self::ABR_NEURAL_MICROFONICA_OPTIONS,
            'desincronia' => self::ABR_NEURAL_DESINCRONIA_OPTIONS,
            'sensibilidad_tasa' => self::ABR_NEURAL_TASA_OPTIONS,
        ];
        foreach ($enums as $clave => $opciones) {
            if (!in_array($neural[$clave] ?? '', $opciones, true)) {
                return sprintf('ABR %s: valor inválido en "%s".', $lado, $clave);
            }
        }
        // Ausencia de respuesta SIN microfónico amplificado es un cuadro
        // válido (respuesta ausente de verdad), pero al revés no: un
        // microfónico de desincronía con las ondas presentes no existe --
        // el CM se ve porque NO hay respuesta neural que lo tape.
        if (($neural['microfonica'] ?? '') === 'amplificada'
            && ($neural['bloqueo'] ?? '') === 'ninguno') {
            return sprintf('ABR %s: el microfónico amplificado es el hallazgo de una desincronía, que va sin ondas -- poné el bloqueo en "Ninguna onda" o dejá el microfónico normal.', $lado);
        }
        return null;
    }

    /**
     * Un oído marcado "Normal" pero con umbral o desviaciones alteradas.
     *
     * El selector de patología no es decorativo: el generador decide con él
     * la FÍSICA de la curva, no con el umbral. Un ABR "normal" con umbral 60
     * sale con la función latencia-intensidad de un oído sano, sin
     * reclutamiento y con las desviaciones sumadas parejas -- o sea un
     * corrimiento paralelo, que es el hallazgo de una conductiva sin que
     * haya GAP. El resultado es un oído que no se corresponde con ninguna
     * patología real y que el alumno no puede clasificar. Ver
     * calculate_wave_parameters() en src/abr/ABR_generator.py.
     *
     * @param array<string,mixed> $cfg  El lado ya armado (abrBuild/eoasBuild/vempBuild).
     * @param string $modulo            Clave de NORMAL_DEVIATION_TOLERANCE ("ABR"/"EOA"/"VEMP").
     * @param string $lado              "OD"/"OI".
     * @param bool $checkUmbral         VEMP no lo chequea: su umbral normal
     *                                  ronda los 60-90 dB nHL, no los 25.
     */
    /**
     * Coherencia del VEMP de un oído, subtipo por subtipo.
     *
     * La patología es del oído pero las desviaciones son de cada VEMP, así
     * que el chequeo de "patología Normal con ondas alteradas" hay que
     * hacerlo tres veces y decir en cuál de los tres está el problema: un
     * "VEMP OD" a secas mandaba al docente a buscar entre seis campos.
     *
     * Sin chequeo de umbral (el del VEMP ronda 60-90 dB y no es comparable
     * con el de los otros módulos) -- ver normalCoherenceError.
     */
    public static function vempCoherenceError(array $cfg, string $lado): ?string
    {
        if (($cfg['type'] ?? 'normal') !== 'normal') {
            return null;
        }
        foreach (self::VEMP_SUBTIPOS as $subtipo) {
            $sub = is_array($cfg['subtipos'][$subtipo] ?? null) ? $cfg['subtipos'][$subtipo] : [];
            // El subtipo va en el LADO y no en el módulo: el módulo es la
            // clave de NORMAL_DEVIATION_TOLERANCE, y decorarlo la rompe.
            $error = self::normalCoherenceError(
                ['type' => 'normal', 'desviaciones' => $sub['desviaciones'] ?? []],
                'VEMP',
                $lado . ' (' . self::VEMP_SUBTIPO_LABELS[$subtipo] . ')',
                false
            );
            if ($error !== null) {
                return $error;
            }
        }
        return null;
    }

    public static function normalCoherenceError(array $cfg, string $modulo, string $lado, bool $checkUmbral = true): ?string
    {
        if (($cfg['type'] ?? 'normal') !== 'normal') {
            return null;
        }
        if ($checkUmbral && (float) ($cfg['umbral'] ?? 0) > self::NORMAL_MAX_UMBRAL) {
            return sprintf(
                '%s %s: umbral %s dB con patología "Normal". Sobre %d dB hay que elegir el tipo de pérdida (coclear/transmisión/neural) -- es lo que el generador usa para la física de la curva, no el umbral.',
                $modulo, $lado, (string) $cfg['umbral'], self::NORMAL_MAX_UMBRAL
            );
        }
        $tol = self::NORMAL_DEVIATION_TOLERANCE[$modulo];
        $campo = self::deviationOverTolerance($cfg['desviaciones'] ?? [], $tol);
        if ($campo !== null) {
            return sprintf(
                '%s %s: %s está fuera de lo que se explica por variabilidad normal, con patología "Normal". Elegí la patología que corresponde o dejá ese valor en 0.',
                $modulo, $lado, $campo
            );
        }
        // OEA: la atenuación manual es otra forma de alterar el oído, y no
        // tiene ruido test-retest que la explique -- se compara contra 0.
        if (abs((float) ($cfg['atten_db'] ?? 0)) > 1e-9) {
            return sprintf(
                '%s %s: atenuación %s dB con patología "Normal". Elegí la patología o dejá la atenuación en 0.',
                $modulo, $lado, (string) $cfg['atten_db']
            );
        }
        return null;
    }

    /**
     * Primera desviación que pasa la tolerancia, descrita para el mensaje
     * de error, o null si todas entran. Acepta las dos formas que usan los
     * módulos: anidada por onda (['onda_V' => ['lat' => .., 'amp' => ..]])
     * y plana por frecuencia (['2000' => 3.5]).
     *
     * @param array<string,mixed> $desviaciones
     * @param array{lat: ?float, amp: ?float, plano: ?float} $tol
     */
    private static function deviationOverTolerance(array $desviaciones, array $tol, string $prefijo = ''): ?string
    {
        foreach ($desviaciones as $clave => $valor) {
            $nombre = $prefijo === '' ? (string) $clave : "$prefijo $clave";
            if (is_array($valor)) {
                $hallazgo = self::deviationOverTolerance($valor, $tol, $nombre);
                if ($hallazgo !== null) {
                    return $hallazgo;
                }
                continue;
            }
            $limite = $tol[$clave] ?? $tol['plano'];
            if ($limite === null) {
                continue;
            }
            if (abs((float) $valor) > $limite) {
                return sprintf('%s = %s', $nombre, (string) $valor);
            }
        }
        return null;
    }

    public static function rinneAuto(int $air, int $bone): string
    {
        return ($air - $bone) >= self::RINNE_GAP_THRESHOLD ? 'negativo' : 'positivo';
    }

    /** Weber auto: lateraliza al oído con mejor (menor) umbral óseo si la asimetría ósea entre oídos es >= WEBER_ASYMMETRY_THRESHOLD; si no, centrado. */
    public static function weberAuto(int $boneOd, int $boneOi): string
    {
        if (abs($boneOd - $boneOi) < self::WEBER_ASYMMETRY_THRESHOLD) {
            return 'centrado';
        }
        return $boneOd < $boneOi ? 'od' : 'oi';
    }

    // Requisitos clínicos de aplicabilidad de Fowler/I.W.A. (ABLB): oído de
    // referencia dentro de rango normal, oído en estudio sensorioneural
    // (gap aéreo-óseo bajo) y fuera de rango normal, diferencia interaural
    // acotada, y frecuencia evaluada dentro del rango donde el criterio de
    // "al menos una frecuencia conservada" tiene sentido clínico.
    public const FOWLER_NORMAL_HL = 20;      // dB HL: umbral <= esto = "rango normal"
    public const FOWLER_SNHL_GAP_MAX = 10;   // dB: gap aéreo-óseo máximo para considerar sensorioneural puro
    public const FOWLER_DIFF_MIN = 20;       // dB: diferencia interaural mínima exigida
    public const FOWLER_DIFF_MAX = 40;       // dB: diferencia interaural máxima exigida
    public const FOWLER_FREQ_MIN_HZ = 250;
    public const FOWLER_FREQ_MAX_HZ = 4000;

    // Tipo de ruido percibido (acufenometría) -- "la forma" del acufeno,
    // junto a la frecuencia de matching (se reusa CaseBuilder::FREQUENCIES).
    public const TINNITUS_RUIDO_OPTIONS = ['Silbido', 'Zumbido', 'Siseo', 'Pitido', 'Campanilleo'];

    // Lateralidad del tinnitus -- independiente de permanente/ocasional (un
    // acufeno unilateral puede ser permanente igual que uno bilateral).
    // "unilateral" pide oído; "bilateral" admite predominio (asimetría).
    public const TINNITUS_LATERALIDAD_OPTIONS = ['craneal', 'unilateral', 'bilateral'];
    public const TINNITUS_PREDOMINIO_OPTIONS = ['igual', 'od', 'oi'];

    /**
     * Si el paciente tiene acúfeno. Lo normal es que NO tenga: la casilla de
     * la ficha arranca apagada.
     *
     * Los casos guardados antes de que existiera la casilla no traen
     * 'presente' y todos tienen un bloque de tinnitus, porque la ficha
     * obligaba a elegir una lateralidad. Para esos vale la forma del dato:
     * si quedó exactamente en el default que nadie tocó (craneal, silbido,
     * la primera frecuencia, ni pulsátil ni permanente) el acúfeno no era
     * del caso; cualquier otra combinación la eligió el docente y se
     * respeta.
     */
    public static function tinnitusPresente(array $t): bool
    {
        if ($t === []) {
            return false;
        }
        if (array_key_exists('presente', $t)) {
            return !empty($t['presente']);
        }
        return !(
            ($t['lateralidad'] ?? 'craneal') === 'craneal'
            && ($t['ruido'] ?? self::TINNITUS_RUIDO_OPTIONS[0]) === self::TINNITUS_RUIDO_OPTIONS[0]
            && (int) ($t['frecuencia'] ?? self::FREQUENCIES[0]) === self::FREQUENCIES[0]
            && empty($t['pulsatil'])
            && empty($t['permanente'])
        );
    }

    /** Índices de CaseBuilder::FREQUENCIES dentro del rango válido para Fowler/I.W.A. (250-4000 Hz). */
    public static function fowlerFreqOptions(): array
    {
        $out = [];
        foreach (self::FREQUENCIES as $i => $hz) {
            if ($hz >= self::FOWLER_FREQ_MIN_HZ && $hz <= self::FOWLER_FREQ_MAX_HZ) {
                $out[] = $i;
            }
        }
        return $out;
    }

    /**
     * Valida los requisitos clínicos de aplicabilidad del Fowler/I.W.A. (ABLB):
     *  1) hipoacusia sensorioneural en el oído en estudio (gap aéreo-óseo bajo),
     *     con el oído de referencia dentro de rango normal en esa frecuencia
     *     (cubre unilateral-normal-contralateral y bilateral-asimétrico, ya que
     *     la frecuencia evaluada queda automáticamente como "la conservada");
     *  2) diferencia interaural de 20 a 40 dB en la frecuencia evaluada;
     *  3) oído de referencia normal / oído en estudio fuera de rango normal.
     * $airPairs / $bonePairs: arrays [[od,oi], ...] indexados como FREQUENCIES
     * (mismo shape que Aerea/Osea en cases.data). Devuelve null si es válido,
     * o el mensaje de error si no.
     */
    public static function fowlerValidationError(int $freq, array $airPairs, array $bonePairs): ?string
    {
        $hz = self::FREQUENCIES[$freq] ?? null;
        if ($hz === null || $hz < self::FOWLER_FREQ_MIN_HZ || $hz > self::FOWLER_FREQ_MAX_HZ) {
            return 'La frecuencia de Fowler debe estar entre ' . self::FOWLER_FREQ_MIN_HZ . ' y ' . self::FOWLER_FREQ_MAX_HZ . ' Hz.';
        }

        $air = $airPairs[$freq] ?? [130, 130];
        $refSide = $air[0] <= $air[1] ? 0 : 1;
        $studySide = 1 - $refSide;
        $refTh = (int) $air[$refSide];
        $studyTh = (int) $air[$studySide];
        $diff = $studyTh - $refTh;

        if ($refTh > self::FOWLER_NORMAL_HL) {
            return "El oído de referencia (mejor umbral) debe estar dentro del rango normal (≤ " . self::FOWLER_NORMAL_HL . ' dB HL) en la frecuencia de Fowler.';
        }
        if ($studyTh <= self::FOWLER_NORMAL_HL) {
            return 'El oído en estudio debe tener un umbral fuera del rango normal (> ' . self::FOWLER_NORMAL_HL . ' dB HL) en la frecuencia de Fowler.';
        }
        if ($diff < self::FOWLER_DIFF_MIN || $diff > self::FOWLER_DIFF_MAX) {
            return 'La diferencia entre oídos en la frecuencia de Fowler debe estar entre ' . self::FOWLER_DIFF_MIN . ' y ' . self::FOWLER_DIFF_MAX . " dB (actual: {$diff} dB).";
        }

        $bone = $bonePairs[$freq] ?? [130, 130];
        $gap = $studyTh - (int) $bone[$studySide];
        if ($gap > self::FOWLER_SNHL_GAP_MAX) {
            return "El oído en estudio debe ser sensorioneural (gap aéreo-óseo ≤ " . self::FOWLER_SNHL_GAP_MAX . " dB); gap actual: {$gap} dB.";
        }

        return null;
    }

    /**
     * Todas las frecuencias (250-4000 Hz) donde los umbrales ya cargados
     * (Aerea/Osea) cumplen los requisitos de Fowler/I.W.A. (ver
     * fowlerValidationError) -- el caso puede calificar en más de una a la
     * vez, y el alumno debe poder encontrar cualquiera de ellas, así que el
     * form pide un patrón de reclutamiento por cada una, no solo una.
     */
    public static function fowlerQualifyingFreqs(array $airPairs, array $bonePairs): array
    {
        $out = [];
        foreach (self::fowlerFreqOptions() as $freq) {
            if (self::fowlerValidationError($freq, $airPairs, $bonePairs) === null) {
                $out[] = $freq;
            }
        }
        return $out;
    }

    // Patrón de reclutamiento -> cortes que le pasan al motor (Fowler.py):
    // ver docstring de Fowler.evaluate() para el porqué de estos valores --
    // en corto, "cuts" son quiebres en dB sobre el umbral del oído en
    // estudio que delimitan las zonas del algoritmo; un corte >= la salida
    // máxima práctica del audiómetro (200) equivale a "nunca se alcanza esa
    // zona". Debe coincidir exactamente con FOWLER_PATTERNS en Fowler.py.
    public const FOWLER_PATTERNS = [
        'none' => [200, 200, 200],       // sin reclutamiento: crecimiento paralelo, nunca iguala
        'partial' => [15, 200, 200],     // reclutamiento parcial: se acerca pero no cierra del todo
        'complete' => [15, 30, 200],     // reclutamiento completo: iguala sonoridad, no sobrepasa
        'over' => [15, 30, 50],          // sobre-reclutamiento: en niveles altos el oído afectado suena más fuerte
    ];

    public const FOWLER_PATTERN_LABELS = [
        'none' => 'Sin reclutamiento',
        'partial' => 'Reclutamiento parcial',
        'complete' => 'Reclutamiento completo',
        'over' => 'Sobre-reclutamiento',
    ];

    public static function fowlerCutsForPattern(string $pattern): array
    {
        return self::FOWLER_PATTERNS[$pattern] ?? self::FOWLER_PATTERNS['none'];
    }

    // Tipo de curva del reflejo acústico, por oído -- morfología del trazo
    // (no la intensidad umbral, que ya se captura en reflex_ipsi/contra).
    // 'normal' ES el patrón "ON" (meseta sostenida); no existe un tipo "on"
    // aparte, quedaba duplicado con este.
    public const REFLEX_CURVE_TYPES = ['normal', 'invertido', 'off', 'on-off'];

    public const REFLEX_CURVE_LABELS = [
        'normal' => 'ON',
        'invertido' => 'Invertido',
        'off' => 'OFF',
        'on-off' => 'ON-OFF',
    ];

    /** Lista en texto de los antecedentes marcados (para el prompt del LLM) -- "ninguno relevante" si no hay ninguno. */
    public static function antecedentesSummary(array $antecedentes): string
    {
        $labels = [];
        foreach (self::HIST_CHECKBOXES as $key) {
            if (!empty($antecedentes[$key])) {
                $labels[] = self::HIST_LABELS[$key];
            }
        }
        return $labels ? implode(', ', $labels) : 'ninguno relevante';
    }

    /**
     * Describe en lenguaje natural (nada de Hz/dB) lo que el "paciente"
     * percibe según los datos de Tinnitus del caso -- para completar
     * {{tinnitus_desc}} en LlmConfig::DEFAULT_PROMPT. $t viene con el mismo
     * shape que cases.data.Tinnitus (o el array crudo del form de la ficha).
     */
    public static function describeTinnitus(array $t): string
    {
        if (!self::tinnitusPresente($t)) {
            return 'No escuchas ruidos ni pitidos en los oídos.';
        }

        $lateralidad = (string) ($t['lateralidad'] ?? 'craneal');
        $ruido = mb_strtolower((string) ($t['ruido'] ?? self::TINNITUS_RUIDO_OPTIONS[0]));
        $permanente = !empty($t['permanente']);
        $pulsatil = !empty($t['pulsatil']);

        $lugar = 'en la cabeza, sin poder decir bien de qué lado';
        if ($lateralidad === 'unilateral') {
            $lugar = 'solo en el oído ' . (($t['oido'] ?? 'od') === 'oi' ? 'izquierdo' : 'derecho');
        } elseif ($lateralidad === 'bilateral') {
            $predominio = (string) ($t['predominio'] ?? 'igual');
            $lugar = $predominio === 'igual'
                ? 'en ambos oídos por igual'
                : ('en ambos oídos, más fuerte del lado ' . ($predominio === 'od' ? 'derecho' : 'izquierdo'));
        }

        $tiempo = $permanente ? 'lo escuchas casi todo el tiempo' : 'te pasa solo de a ratos, no siempre';
        $pulso = $pulsatil ? ' y a veces sientes que va al compás de tu pulso' : '';

        return "Escuchas un {$ruido} {$lugar}; {$tiempo}{$pulso}.";
    }

    public static function nextCaseId(PDO $pdo): string
    {
        $max = (int) $pdo->query('SELECT MAX(CAST(id AS INTEGER)) FROM cases')->fetchColumn();
        return (string) ($max + 1);
    }

    /**
     * Volumen del canal auditivo (Vea) en cm3 -- mismo rango clínico
     * (Katz, Handbook of Clinical Audiology) que CreatePatient.ear_volume
     * en src/lib/helpers.py. gender: 0 = hombre, 1 = mujer.
     */
    public static function earVolume(int $age, int $gender): float
    {
        if ($age <= 5) {
            [$low, $high] = [0.30, 0.90];
        } elseif ($age <= 12) {
            [$low, $high] = [0.40, 1.00];
        } elseif ($age <= 17) {
            [$low, $high] = [0.60, 1.30];
        } else {
            [$low, $high] = $gender === 0 ? [0.9, 2.0] : [0.8, 1.8];
        }
        $value = $low + (mt_rand() / mt_getrandmax()) * ($high - $low);
        return round($value, 2);
    }

    /**
     * RUT falso a partir de la edad -- misma regresión lineal fija que
     * CreatePatient.rut_from_age en src/lib/helpers.py (no inventar otra:
     * tiene que dar edades consistentes con get_age_from_rut del lado
     * cliente). Se agrega un día aleatorio del año para no chocar RUTs
     * entre pacientes con la misma edad.
     */
    public static function rutFromAge(int $age): int
    {
        $slope = 3.3363697569700348e-06;
        $intercept = 1932.2573852507373;
        $birthYear = (int) date('Y') - $age;
        $randomDay = random_int(0, 364);
        $birthDateFloat = $birthYear + ($randomDay / 365);
        return (int) (($birthDateFloat - $intercept) / $slope);
    }

    /**
     * Fallback server-side de la fecha de nacimiento a partir de la edad --
     * el cálculo real vive en JS (case/age-rut.js, recalcula al tipear la
     * edad); esto solo cubre el caso de que el campo llegue vacío (JS
     * deshabilitado). Año = año actual - edad, día/mes al azar dentro de
     * ese año.
     */
    public static function randomFechaNacForAge(int $age): string
    {
        $birthYear = (int) date('Y') - $age;
        $randomDay = random_int(0, 364);
        return date('d-m-Y', mktime(0, 0, 0, 1, 1 + $randomDay, $birthYear));
    }

    /** Mejor 2 de [500,1000,2000 Hz] (índices 2,3,4), promedio, floor a múltiplo de 5. Igual que create_a.py::_fletcher_avg. */
    public static function fletcherAvg(array $airPairs): array
    {
        $sublist = array_slice($airPairs, 2, 3);
        $result = [];
        foreach ([0, 1] as $side) {
            $values = array_map(static fn(array $pair) => $pair[$side], $sublist);
            sort($values);
            $best2 = array_slice($values, 0, 2);
            $avg = array_sum($best2) / count($best2);
            $result[] = (int) (floor($avg / 5) * 5);
        }
        return $result;
    }

    /**
     * Banco de nombres y apellidos, compartido con la app de escritorio
     * (resources/names.json).
     *
     * Devuelve el banco crudo y no un nombre ya elegido porque quien sortea
     * es el editor, en JS: el nombre se escribe junto con el resto del caso
     * al apretar "Generar caso", sin recargar la página. Sortearlo también
     * acá serían dos implementaciones de lo mismo, y la del servidor no la
     * llamaría nadie.
     *
     * @return array{nombres_hombres:list<string>, nombres_mujeres:list<string>, apellidos:list<string>}
     */
    public static function nameBank(): array
    {
        $path = __DIR__ . '/../resources/names.json';
        $bank = is_file($path) ? json_decode((string) file_get_contents($path), true) : null;
        if (!is_array($bank)) {
            $bank = [];
        }
        return [
            'nombres_hombres' => array_values($bank['nombres_hombres'] ?? []),
            'nombres_mujeres' => array_values($bank['nombres_mujeres'] ?? []),
            'apellidos' => array_values($bank['apellidos'] ?? []),
        ];
    }

    /**
     * Arma el JSON de cases.data con el mismo shape que create_a.py::_save_case
     * -- el cliente (Audiometer.py/Z.py/ListWords.py) espera exactamente
     * estas claves. $form ya viene validado desde case_create.php.
     */
    /**
     * Migración del FSP declarado a "barridos para el criterio".
     *
     * De FSP = 1 + A²N/σ² se despeja σ² = A²N/(FSP-1), y de ahí
     * N* = (3,1-1)·σ²/A² = 2,1·N/(FSP-1). La amplitud se cancela: la
     * conversión sale solo del FSP que el caso tenía declarado a 2000
     * promediaciones. Espejo de criterion_sweeps_from_fsp() en
     * src/abr/ABR_generator.py.
     */
    public static function fspToCriterionSweeps(float $fsp2000, float $barridos = 2000.0): int
    {
        $fsp = max($fsp2000, 1.01);
        return (int) round((3.1 - 1.0) * $barridos / ($fsp - 1.0));
    }

    public static function buildCaseData(array $form): array
    {
        $gender = (int) $form['gender'];
        $age = (int) $form['age'];

        return [
            'gender' => $gender,
            'id' => (int) $form['id'],
            'Aerea' => $form['aerea'],
            'Osea' => $form['osea'],
            'LDL' => $form['ldl'],
            'Aerea_mkg' => $form['aerea'],
            'Osea_mkg' => $form['osea'],
            'Z_OD' => $form['z_od'],
            'Z_OI' => $form['z_oi'],
            // Sonda de 1000 Hz, la del lactante (ver Z1000_OPTIONS). El
            // cliente la lee en z_generator.map_letter_for_probe.
            'Z1000_OD' => $form['z1000_od'] ?? 'auto',
            'Z1000_OI' => $form['z1000_oi'] ?? 'auto',
            'Rinne' => $form['rinne'],
            'Weber' => $form['weber'],
            'sector' => 'Camara_sono',
            'edad' => $age,
            // Horas de vida, solo en el primer año (ver CaseForm). Es lo que
            // separa un recién nacido de turno de un lactante de ocho meses:
            // los dos son 'edad' = 0 y no se parecen en nada.
            'edad_horas' => $form['edad_horas'] ?? null,
            // Circunstancias del parto y el percentil sorteado de cada oído
            // (ver NewbornScreening). Solo en recién nacidos.
            'nacimiento' => $form['nacimiento'] ?? [],
            'volume' => [self::earVolume($age, $gender), self::earVolume($age, $gender), 'N/D'],
            'UMD' => $form['umd'],
            'SDT' => $form['sdt'],
            'SRT' => $form['srt'],
            'Fowler' => $form['fowler'],
            'Stenger' => $form['stenger'],
            'SISI' => $form['sisi'],
            'box' => 'Box_1',
            'result' => 1,
            'state_login' => 1,
            'recruit' => $form['recruit'],
            'decay' => $form['decay'],
            'Carhart' => $form['carhart'],
            'Stat' => $form['stat'],
            'Rosemberg' => $form['rosemberg'],
            'Reflex' => $form['reflex'],
            'ETF' => [$form['etf_od'], $form['etf_oi']],
            'Anamnesis' => $form['anamnesis'],
            'PatientBehavior' => $form['comportamiento'] ?? '',
            'PatientDisposition' => (int) ($form['disposicion'] ?? 0),
            // Quiénes vienen con el paciente y cómo se comportan en la
            // entrevista (ver Sala.php). Un caso creado desde create_a.py
            // no lo trae: Sala::desde() le arma una sala de una persona y
            // el chat se comporta como el 1 a 1 de siempre.
            'Sala' => $form['sala'] ?? [],
            'Tinnitus' => $form['tinnitus'],
            'Otoscopia' => $form['otoscopia'],
            // Perfil auditivo: sitio de la lesión por oído (ver
            // src/CaseProfile.php). No lo lee ningún cliente todavía -- es
            // la fuente desde la que se proyectan los exámenes que tengan
            // `auto` encendido. Un caso creado desde create_a.py (la app de
            // escritorio) no lo trae, y CaseProfile::normalize() lo infiere.
            'Perfil' => $form['perfil'],
            'ABR' => $form['abr'],
            'EOAS' => $form['eoas'],
            'VEMP' => $form['vemp'],
            // Qué fichas del editor dio por revisadas el docente antes de
            // guardar, y quién (ver CaseReview). No lo lee ningún cliente:
            // es la trazabilidad de la revisión, y lo que evita que el
            // editor le vuelva a reclamar una decisión ya tomada.
            'Revision' => $form['revision'] ?? [],
            'tipo' => 'normal',
        ];
    }

    /**
     * Inverso de buildCaseData(): reconstruye el shape de $_POST que espera
     * case_create.php a partir de un `cases.data` ya guardado, para
     * precargar el formulario al editar un caso existente.
     */
    public static function caseDataToForm(array $data): array
    {
        $unzip = static function (array $pairs, int $count): array {
            $od = [];
            $oi = [];
            for ($n = 0; $n < $count; $n++) {
                $od[$n] = (string) ($pairs[$n][0] ?? 0);
                $oi[$n] = (string) ($pairs[$n][1] ?? 0);
            }
            return [$od, $oi];
        };

        $v = [];
        $v['gender'] = (string) ($data['gender'] ?? 0);
        $v['age'] = isset($data['edad']) ? (string) $data['edad'] : '';

        $freqCount = count(self::FREQUENCIES);
        [$aereaOd, $aereaOi] = $unzip($data['Aerea'] ?? [], $freqCount);
        [$oseaOd, $oseaOi] = $unzip($data['Osea'] ?? [], $freqCount);
        [$ldlOd, $ldlOi] = $unzip($data['LDL'] ?? [], $freqCount);
        $v['aerea'] = ['od' => $aereaOd, 'oi' => $aereaOi];
        $v['osea'] = ['od' => $oseaOd, 'oi' => $oseaOi];
        $v['ldl'] = ['od' => $ldlOd, 'oi' => $ldlOi];

        // "LDL no medido" se guarda como 130 en las 9 frecuencias (ver
        // case_create.php) -- si alguna difiere, asumimos que sí se midió.
        $v['ldl_habilitado'] = [];
        foreach (['od' => $ldlOd, 'oi' => $ldlOi] as $side => $vals) {
            foreach ($vals as $val) {
                if ((int) $val !== 130) {
                    $v['ldl_habilitado'][$side] = '1';
                    break;
                }
            }
        }

        $v['z_od'] = $data['Z_OD'] ?? 'A';
        $v['z_oi'] = $data['Z_OI'] ?? 'A';
        $v['z1000_od'] = $data['Z1000_OD'] ?? 'auto';
        $v['z1000_oi'] = $data['Z1000_OI'] ?? 'auto';

        // Igual que sdt_auto/srt_auto: se muestra el valor guardado tal cual
        // (acumetria_auto queda sin marcar) -- si quedara tildado el checkbox
        // "auto" el JS lo pisaría con el recálculo apenas cargara la página.
        $v['acumetria_auto'] = '';
        foreach (self::ACUMETRIA_FREQS as $hz => $freqIdx) {
            $v['rinne'][$hz]['od'] = $data['Rinne'][$hz]['od'] ?? 'positivo';
            $v['rinne'][$hz]['oi'] = $data['Rinne'][$hz]['oi'] ?? 'positivo';
            $v['weber'][$hz] = $data['Weber'][$hz] ?? 'centrado';
        }

        $umd = $data['UMD'] ?? [];
        $v['umd_int'] = ['od' => (string) ($umd[0]['int'] ?? 35), 'oi' => (string) ($umd[1]['int'] ?? 35)];
        $v['umd_pct'] = ['od' => (string) ($umd[0]['percentage'] ?? 100), 'oi' => (string) ($umd[1]['percentage'] ?? 100)];

        $sdt = $data['SDT'] ?? [0, 0];
        $srt = $data['SRT'] ?? [0, 0];
        $v['sdt'] = ['od' => (string) ($sdt[0] ?? 0), 'oi' => (string) ($sdt[1] ?? 0)];
        $v['srt'] = ['od' => (string) ($srt[0] ?? 0), 'oi' => (string) ($srt[1] ?? 0)];
        // Se muestra el valor guardado tal cual -- si quedaran tildados los
        // checkboxes "auto" el JS los pisaría con el recálculo de Fletcher
        // apenas cargara la página.
        $v['sdt_auto'] = [];
        $v['srt_auto'] = [];

        $fowler = $data['Fowler'] ?? [];
        // freq/cuts/auto: shape viejo (una sola frecuencia elegida al crear
        // el caso), ya no se usa -- se ignora silenciosamente si aparece en
        // un caso guardado con la versión anterior; el patrón por frecuencia
        // (abajo) es la única fuente de verdad ahora.
        $v['fowler_pattern'] = [];
        foreach ((array) ($fowler['patterns'] ?? []) as $freq => $pattern) {
            $v['fowler_pattern'][(string) $freq] = (string) $pattern;
        }
        if (!empty($fowler['diplacusia'])) { $v['diplacusia'] = '1'; }

        $stenger = $data['Stenger'] ?? [false, false];
        $v['stenger'] = [];
        if (!empty($stenger[0])) { $v['stenger']['od'] = '1'; }
        if (!empty($stenger[1])) { $v['stenger']['oi'] = '1'; }

        $sisi = $data['SISI'] ?? [0, 0];
        $v['sisi'] = ['od' => (string) ($sisi[0] ?? 0), 'oi' => (string) ($sisi[1] ?? 0)];

        $recruit = $data['recruit'] ?? [false, false];
        $v['recruit'] = [];
        if (!empty($recruit[0])) { $v['recruit']['od'] = '1'; }
        if (!empty($recruit[1])) { $v['recruit']['oi'] = '1'; }

        // Conteo fijo (no derivado de count($data[...])): un caso viejo sin
        // esta clave debe igual rellenar las N frecuencias del protocolo con
        // 0 (sin deterioro), no quedar con un array vacío.
        foreach (['carhart' => ['Carhart', 4], 'stat' => ['Stat', 3], 'rosemberg' => ['Rosemberg', 4]] as $formKey => [$dataKey, $count]) {
            [$od, $oi] = $unzip($data[$dataKey] ?? [], $count);
            $v[$formKey] = ['od' => $od, 'oi' => $oi];
        }

        $reflex = $data['Reflex'] ?? [];
        [$ipsiOd, $ipsiOi] = $unzip($reflex['ipsi'] ?? [], 4);
        [$contraOd, $contraOi] = $unzip($reflex['contra'] ?? [], 5);
        $v['reflex_ipsi'] = ['od' => $ipsiOd, 'oi' => $ipsiOi];
        $v['reflex_contra'] = ['od' => $contraOd, 'oi' => $contraOi];
        $reflexTipo = $reflex['tipo'] ?? [];
        $v['reflex_type'] = [
            'od' => (string) ($reflexTipo['od'] ?? 'normal'),
            'oi' => (string) ($reflexTipo['oi'] ?? 'normal'),
        ];

        $etf = $data['ETF'] ?? ['Normal', 'Normal'];
        $v['etf_od'] = $etf[0] ?? 'Normal';
        $v['etf_oi'] = $etf[1] ?? 'Normal';

        $anamnesis = $data['Anamnesis'] ?? [];
        $antecedentes = $anamnesis['antecedentes'] ?? [];
        $v['hist'] = [];
        foreach (self::HIST_CHECKBOXES as $h) {
            if (!empty($antecedentes[$h])) {
                $v['hist'][$h] = '1';
            }
        }
        // Estado del borrador de IA: se relee tal cual, así un caso ya
        // verificado no vuelve a pedir verificación al editarlo (y uno sin
        // verificar sigue bloqueado hasta que alguien lo lea).
        $ia = is_array($anamnesis['ia'] ?? null) ? $anamnesis['ia'] : [];
        $v['anamnesis_ia'] = [
            'generado' => !empty($ia['generado']) ? '1' : '',
            'verificado' => !empty($ia['verificado']) ? '1' : '',
            'generado_en' => (string) ($ia['generado_en'] ?? ''),
            'verificado_por' => (string) ($ia['verificado_por'] ?? ''),
            'verificado_en' => (string) ($ia['verificado_en'] ?? ''),
        ];
        $v['medicamentos'] = $anamnesis['medicamentos'] ?? '';
        $v['cirugias'] = $anamnesis['cirugias'] ?? '';
        $v['otros'] = $anamnesis['otros'] ?? '';
        $v['comportamiento'] = $data['PatientBehavior'] ?? '';
        $v['disposicion'] = (string) ($data['PatientDisposition'] ?? 0);

        // Sala: el editor repinta las filas de acompañantes desde acá. Se
        // pasa por Sala::desde() y no por el crudo para que un caso viejo
        // (sin sala) abra con la sala de una persona ya armada.
        $v += Sala::toForm(Sala::desde($data));

        $tinnitus = $data['Tinnitus'] ?? [];
        $v['tinnitus'] = [];
        if (self::tinnitusPresente((array) $tinnitus)) {
            $v['tinnitus']['presente'] = '1';
        }
        foreach (['pulsatil', 'permanente'] as $flag) {
            if (!empty($tinnitus[$flag])) {
                $v['tinnitus'][$flag] = '1';
            }
        }
        $v['tinnitus']['lateralidad'] = $tinnitus['lateralidad'] ?? 'craneal';
        $v['tinnitus']['oido'] = $tinnitus['oido'] ?? 'od';
        $v['tinnitus']['predominio'] = $tinnitus['predominio'] ?? 'igual';
        $v['tinnitus']['ruido'] = $tinnitus['ruido'] ?? self::TINNITUS_RUIDO_OPTIONS[0];
        $v['tinnitus']['frecuencia'] = (string) ($tinnitus['frecuencia'] ?? self::FREQUENCIES[0]);

        // 'modo' venía en versiones anteriores de esta ficha (antes de que
        // se sacara el selector) -- se ignora si aparece en un caso viejo,
        // el número de fases ya guardadas dice lo mismo sin necesitarlo.
        $otoscopia = $data['Otoscopia'] ?? [];
        $otoscopiaFases = $otoscopia['fases'] ?? [];
        if (!is_array($otoscopiaFases) || count($otoscopiaFases) === 0) {
            $otoscopiaFases = [['texto' => '']];
        }
        $v['otoscopia'] = [
            'fases' => array_map(
                static fn($f) => ['texto' => (string) (is_array($f) ? ($f['texto'] ?? '') : '')],
                array_values($otoscopiaFases)
            ),
        ];

        // Perfil auditivo: se relee normalizado, así un caso guardado antes
        // de que existiera entra al formulario con el `cce_pct` inferido de
        // su patología y todos los `auto` apagados, en vez de perderse al
        // guardar de nuevo. Ver CaseProfile::normalize().
        $perfil = CaseProfile::normalize($data);
        foreach (['OD' => 'od', 'OI' => 'oi'] as $ladoData => $ladoForm) {
            $v['perfil'][$ladoForm]['cce_pct'] = (string) $perfil[$ladoData]['cce_pct'];
        }
        $v['perfil']['auto'] = [];
        foreach ($perfil['auto'] as $moduloAuto => $activo) {
            if ($activo) {
                // Mismo shape que los otros checkboxes del form (presente =
                // marcado): un módulo en manual no aparece en $_POST.
                $v['perfil']['auto'][$moduloAuto] = '1';
            }
        }

        $horas = $data['edad_horas'] ?? null;
        if ($horas !== null && $horas !== '') {
            $horas = (int) $horas;
            // Se muestra en la unidad más legible: horas el primer par de
            // días, después días, y meses pasado el mes y medio.
            if ($horas >= 1080) {
                $v['edad_valor'] = (string) (int) round($horas / 720);
                $v['edad_unidad'] = 'meses';
            } elseif ($horas >= 48) {
                $v['edad_valor'] = (string) (int) round($horas / 24);
                $v['edad_unidad'] = 'dias';
            } else {
                $v['edad_valor'] = (string) $horas;
                $v['edad_unidad'] = 'horas';
            }
        }

        $nacimiento = is_array($data['nacimiento'] ?? null) ? $data['nacimiento'] : [];
        if ($nacimiento !== []) {
            $v['nacimiento'] = [
                'parto' => (string) ($nacimiento['parto'] ?? 'vaginal'),
                'semanas' => $nacimiento['semanas'] ?? '',
                'peso_g' => $nacimiento['peso_g'] ?? '',
                'torch' => (string) ($nacimiento['torch'] ?? ''),
                'torch_sintomatica' => !empty($nacimiento['torch_sintomatica']) ? '1' : '',
                'uci_dias' => $nacimiento['uci_dias'] ?? '',
                'ototoxicos' => !empty($nacimiento['ototoxicos']) ? '1' : '',
                'exanguinotransfusion' => !empty($nacimiento['exanguinotransfusion']) ? '1' : '',
                'peg' => !empty($nacimiento['peg']) ? '1' : '',
                'vernix_limpiado' => !empty($nacimiento['vernix_limpiado']) ? '1' : '',
                'liquido_persistente' => !empty($nacimiento['liquido_persistente']) ? '1' : '',
                // El percentil vuelve tal cual: si se resorteara al reabrir,
                // el mismo caso cambiaría de resultado entre dos clases.
                'percentil' => $nacimiento['percentil'] ?? [],
            ];
        }

        $abr = $data['ABR'] ?? [];
        // Set normativo con el que se construyó, para que el select vuelva
        // a marcarlo al reabrir el caso.
        $v['abr']['autor'] = (string) (($abr['autor']['set'] ?? null) ?: '__default__');
        foreach (['OD' => 'od', 'OI' => 'oi'] as $ladoData => $ladoForm) {
            $ladoAbr = is_array($abr[$ladoData] ?? null) ? $abr[$ladoData] : [];
            $desv = is_array($ladoAbr['desviaciones'] ?? null) ? $ladoAbr['desviaciones'] : [];
            $fsp = is_array($ladoAbr['fsp_puntos'] ?? null) ? $ladoAbr['fsp_puntos'] : [];
            $falsaV = is_array($ladoAbr['falsa_v'] ?? null) ? $ladoAbr['falsa_v'] : [];
            $ondaVal = static function (array $desv, string $onda, string $campo, $default) {
                return (string) ($desv[$onda][$campo] ?? $default);
            };
            $ladoAbrType = $ladoAbr['type'] ?? 'normal';
            $v['abr'][$ladoForm] = [
                'type' => in_array($ladoAbrType, self::ABR_TYPE_OPTIONS, true) ? $ladoAbrType : 'normal',
                'umbral' => (string) ($ladoAbr['umbral'] ?? 20),
                // repro_var y average_objetivo se guardaban (ver abrBuild en
                // case_create.php) pero no se releían: al editar un caso el
                // formulario los redibujaba con el default y el docente los
                // perdía al guardar de nuevo.
                'repro_var' => (string) ($ladoAbr['repro_var'] ?? 0.2),
                // Inquietud del paciente durante la captura: los casos
                // guardados antes de esto quedan en 0 (paciente quieto).
                'inquietud' => (string) ($ladoAbr['inquietud'] ?? 0),
                'pam' => (string) ($ladoAbr['pam'] ?? 0),
                'average_objetivo' => (string) ($ladoAbr['average_objetivo'] ?? 2000),
                // Falsa onda V (ver false_wave en ABR_generator.py): un caso
                // guardado antes de que existiera no trae la clave y queda
                // con amplitud 0, o sea desactivada.
                'falsa_v_amp' => (string) ($falsaV['amp'] ?? 0),
                'falsa_v_lat' => (string) ($falsaV['lat'] ?? 5.6),
                'falsa_v_int_min' => (string) ($falsaV['int_min'] ?? 0),
                'falsa_v_int_max' => (string) ($falsaV['int_max'] ?? 120),
                'falsa_v_mitad' => in_array($falsaV['mitad'] ?? 'auto', ['auto', 'a', 'b'], true)
                    ? (string) ($falsaV['mitad'] ?? 'auto') : 'auto',
                'lat_I' => $ondaVal($desv, 'onda_I', 'lat', 0),
                'amp_I' => $ondaVal($desv, 'onda_I', 'amp', 0),
                'lat_III' => $ondaVal($desv, 'onda_III', 'lat', 0),
                'amp_III' => $ondaVal($desv, 'onda_III', 'amp', 0),
                'lat_V' => $ondaVal($desv, 'onda_V', 'lat', 0),
                'amp_V' => $ondaVal($desv, 'onda_V', 'amp', 0),
                'fsp_800' => (string) ($fsp['800'] ?? 2.3),
                'fsp_2000' => (string) ($fsp['2000'] ?? 2.8),
                'fsp_obj' => (string) ($fsp['objetivo'] ?? 3.0),
                // Ruido del paciente. Un caso viejo trae el FSP declarado y
                // no estos campos: se convierte al vuelo con la misma
                // fórmula que usa el cliente (criterion_sweeps_from_fsp),
                // N* = (3,1 - 1) * 2000 / (FSP@2000 - 1). La amplitud se
                // cancela, así que la conversión no depende del caso.
                // Vacio = el propio umbral (es el default y lo habitual),
                // asi que null y "no esta la clave" son lo mismo.
                'nivel_referencia' => isset($ladoAbr['nivel_referencia'])
                    ? (string) $ladoAbr['nivel_referencia'] : '',
                'barridos_criterio' => (string) ($ladoAbr['barridos_criterio']
                    ?? self::fspToCriterionSweeps((float) ($fsp['2000'] ?? 2.8))),
                'respuesta_en_referencia' => (string) ($ladoAbr['respuesta_en_referencia'] ?? 'presente'),
            ];
            if (!empty($ladoAbr['repro']) || !isset($ladoAbr['repro'])) {
                // Default repro=true (caso nuevo sin ABR configurado aún, o
                // caso viejo de antes de esta clave -- ver DEFAULT_ABR_CASE
                // en AbrMainWindow.py): solo queda sin marcar si el docente
                // lo desmarcó explícitamente (repro === false guardado).
                $v['abr'][$ladoForm]['repro'] = '1';
            }
            // Patrón retrococlear: un caso guardado antes de que existiera
            // no trae la clave y cae en los defaults, que son el cuadro que
            // dibujaba el generador cuando "neural" era uno solo.
            $neural = is_array($ladoAbr['neural'] ?? null) ? $ladoAbr['neural'] : [];
            foreach (self::ABR_NEURAL_DEFAULTS as $clave => $default) {
                $v['abr'][$ladoForm]['neural'][$clave] = (string) ($neural[$clave] ?? $default);
            }
        }

        $eoas = $data['EOAS'] ?? [];
        foreach (['OD' => 'od', 'OI' => 'oi'] as $ladoData => $ladoForm) {
            $ladoEoas = is_array($eoas[$ladoData] ?? null) ? $eoas[$ladoData] : [];
            $ladoEoasType = $ladoEoas['type'] ?? 'normal';
            $desvEoas = is_array($ladoEoas['desviaciones'] ?? null) ? $ladoEoas['desviaciones'] : [];
            $v['eoas'][$ladoForm] = [
                'type' => in_array($ladoEoasType, self::EOAS_TYPE_OPTIONS, true) ? $ladoEoasType : 'normal',
                'umbral' => (string) ($ladoEoas['umbral'] ?? self::EOAS_DEFAULTS['umbral']),
                'atten_db' => (string) ($ladoEoas['atten_db'] ?? self::EOAS_DEFAULTS['atten_db']),
                'ruido_db' => (string) ($ladoEoas['ruido_db'] ?? self::EOAS_DEFAULTS['ruido_db']),
                'sello_pct' => (string) ($ladoEoas['sello_pct'] ?? self::EOAS_DEFAULTS['sello_pct']),
                'variabilidad_db' => (string) ($ladoEoas['variabilidad_db'] ?? self::EOAS_DEFAULTS['variabilidad_db']),
                'soae_mode' => in_array($ladoEoas['soae_mode'] ?? '', self::EOAS_SOAE_MODES, true)
                    ? $ladoEoas['soae_mode']
                    : self::EOAS_DEFAULTS['soae_mode'],
            ];
            // Picos SOAE fijados a mano (caso viejo: ninguno -> filas
            // vacías y el cliente decide por prevalencia).
            $picosSoae = is_array($ladoEoas['soae_peaks'] ?? null) ? array_values($ladoEoas['soae_peaks']) : [];
            for ($iSoae = 0; $iSoae < self::EOAS_SOAE_MAX_PEAKS; $iSoae++) {
                $picoSoae = is_array($picosSoae[$iSoae] ?? null) ? $picosSoae[$iSoae] : [];
                $v['eoas'][$ladoForm]['soae_peaks'][$iSoae] = [
                    'hz' => isset($picoSoae['hz']) ? (string) $picoSoae['hz'] : '',
                    'db' => isset($picoSoae['db']) ? (string) $picoSoae['db'] : '',
                ];
            }
            // Caso viejo (guardado antes del perfil por frecuencia): las
            // desviaciones no existen y quedan en 0 -- el cliente sigue
            // atenuando solo por type/umbral, igual que antes.
            foreach (self::EOAS_FREQS as $hzEoas) {
                $v['eoas'][$ladoForm]['desv'][(string) $hzEoas] = (string) ($desvEoas[(string) $hzEoas] ?? 0);
            }
        }

        // VEMP: los tres subtipos por oído (ver CaseForm::parseVemp).
        //
        // Un caso guardado ANTES de que fueran tres traía un solo subtipo
        // (`subtipo`) con sus valores en la raíz del oído. Se los queda el
        // subtipo que el caso decía, y los otros dos arrancan en default:
        // no había nada configurado en ellos, y suponer que el cVEMP del
        // caso viejo describe también al ocular sería inventar un hallazgo
        // que el docente nunca cargó.
        $vemp = $data['VEMP'] ?? [];
        foreach (['OD' => 'od', 'OI' => 'oi'] as $ladoData => $ladoForm) {
            $ladoVemp = is_array($vemp[$ladoData] ?? null) ? $vemp[$ladoData] : [];
            $ladoVempType = $ladoVemp['type'] ?? 'normal';
            $legado = $ladoVemp['subtipo'] ?? null;
            if (!in_array($legado, self::VEMP_SUBTIPOS, true)) {
                $legado = null;
            }
            $guardados = is_array($ladoVemp['subtipos'] ?? null) ? $ladoVemp['subtipos'] : [];

            $ladoFormArr = [
                'type' => in_array($ladoVempType, self::VEMP_TYPE_OPTIONS, true) ? $ladoVempType : 'normal',
            ];
            foreach (self::VEMP_SUBTIPOS as $subtipo) {
                $def = self::VEMP_DEFAULTS[$subtipo];
                if (is_array($guardados[$subtipo] ?? null)) {
                    $sub = $guardados[$subtipo];
                } elseif ($legado === $subtipo) {
                    $sub = $ladoVemp;   // caso viejo: sus valores estaban en la raíz
                } else {
                    $sub = [];
                }
                $desv = is_array($sub['desviaciones'] ?? null) ? $sub['desviaciones'] : [];
                $subForm = [
                    'umbral' => (string) ($sub['umbral'] ?? $def['umbral']),
                    'repro_var' => (string) ($sub['repro_var'] ?? self::VEMP_REPRO_VAR_DEFAULT),
                    'average_objetivo' => (string) ($sub['average_objetivo'] ?? $def['average_objetivo']),
                ];
                foreach (self::VEMP_PEAKS[$subtipo] as $pico) {
                    $subForm["lat_{$pico}"] = (string) ($desv[$pico]['lat'] ?? 0);
                    $subForm["amp_{$pico}"] = (string) ($desv[$pico]['amp'] ?? 0);
                }
                if (!empty($sub['repro']) || !isset($sub['repro'])) {
                    // Default repro=true (subtipo nunca configurado): solo
                    // queda sin marcar si el docente lo desmarcó él
                    // (repro === false guardado).
                    $subForm['repro'] = '1';
                }
                $ladoFormArr[$subtipo] = $subForm;
            }
            $v['vemp'][$ladoForm] = $ladoFormArr;
        }

        // Las tildes del Resumen, para que reeditar un caso ya revisado no
        // pida revisarlo de nuevo entero (ver CaseReview::toForm).
        $v['revisado'] = CaseReview::toForm($data);

        return $v;
    }
}
