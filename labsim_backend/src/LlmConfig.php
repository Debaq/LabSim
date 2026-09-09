<?php

// Igual que en LlmChat: la dependencia se declara donde se usa. El bloque
// de sala del prompt (ver bloqueSala) necesita Sala para saber quién está
// en el box y qué puede contar cada uno por su edad.
require_once __DIR__ . '/Sala.php';

final class LlmConfig
{
    public const PROVIDERS = ['deepseek', 'openai_compatible'];

    /**
     * Presupuesto por defecto del borrador de anamnesis (ver
     * AnamnesisDraft). Va aparte de `max_tokens` porque son dos tareas
     * distintas: el chat del paciente contesta una frase hablada y con 400
     * sobra, mientras que acá el JSON completo ya ocupa varios cientos y un
     * modelo de razonamiento gasta presupuesto ANTES de escribir.
     */
    public const ANAMNESIS_MAX_TOKENS_DEFAULT = 6000;

    // Base URL por defecto de cada proveedor -- deepseek expone una API
    // compatible con el formato Chat Completions de OpenAI, así que
    // "openai_compatible" cubre cualquier otro backend que hable ese mismo
    // protocolo (LM Studio, Ollama con proxy, etc.) sin agregar código nuevo.
    public const PROVIDER_DEFAULT_BASE_URL = [
        'deepseek' => 'https://api.deepseek.com',
        'openai_compatible' => '',
    ];

    // Placeholders que el endpoint de chat (todavía no implementado) debe
    // reemplazar con datos reales del caso/anamnesis antes de mandar este
    // prompt como system message. Documentados acá para que el admin sepa
    // qué variables puede usar al editar la plantilla.
    public const PLACEHOLDERS = [
        '{{nombre}}' => 'Nombre de pila del paciente',
        '{{edad}}' => 'Edad en años',
        '{{genero}}' => '"hombre" o "mujer"',
        '{{procedimiento}}' => 'Motivo de la cita agendada',
        '{{antecedentes}}' => 'Antecedentes médicos marcados en la anamnesis, en lista',
        '{{medicamentos}}' => 'Medicamentos que toma (texto libre de la anamnesis)',
        '{{cirugias}}' => 'Cirugías previas (texto libre de la anamnesis)',
        // El nombre del placeholder queda como está: renombrarlo rompería
        // las plantillas que los cursos ya tengan guardadas. Lo que cambia
        // es la descripción, que era la que no decía para qué sirve.
        '{{otros_antecedentes}}' => 'Lo que el paciente cuenta de sí mismo si le preguntan: vida, trabajo, rutina, desde cuándo lo nota, qué le preocupa (campo "Lo que el paciente cuenta de sí mismo" en Anamnesis)',
        '{{tinnitus_desc}}' => 'Descripción en lenguaje natural del acúfeno del caso (o "no reporta" si no tiene)',
        '{{comportamiento}}' => 'Cómo se comporta el paciente (campo "Comportamiento" de la ficha, en Anamnesis)',
        '{{disposicion}}' => 'Qué tan fácil se ofende o se pone contento el paciente (campo "Sensibilidad" de la ficha)',
    ];

    // Escala del campo "Sensibilidad" de la ficha del paciente (cases.data
    // PatientDisposition, -2..2). Afecta dos cosas a la vez: el tono del
    // paciente durante el chat (acá, vía {{disposicion}}) y, más importante,
    // qué tan fácil OirsEvaluator concluye reclamo o mérito al cerrar la
    // atención -- un paciente positivo llega a mérito con un trato apenas
    // amable; uno quisquilloso reclama por descuidos leves.
    public const DISPOSITION_LABELS = [
        -2 => 'Eres una persona muy sensible y quisquillosa: te ofende con facilidad un trato apurado, brusco, indiferente o que no te explique bien las cosas. Si sientes que te trataron mal, lo demuestras (te pones cortante, dolido o te quejas).',
        -1 => 'Eres algo sensible: un trato descuidado te incomoda, aunque no te ofendes por cualquier cosa.',
        0 => 'Tienes un temperamento normal: ni especialmente sensible ni especialmente efusivo.',
        1 => 'Eres una persona cálida y agradecida: valoras que te traten bien y lo dices.',
        2 => 'Eres una persona muy positiva y efusiva: agradeces con facilidad el buen trato, incluso ante gestos pequeños de amabilidad o una buena explicación.',
    ];

    /**
     * Por qué le toca hablar a esta persona en este turno (ver
     * Sala::turno). Es la línea que convierte una regla del motor en algo
     * que el modelo puede actuar: sin ella, un acompañante al que le toca
     * corregir al paciente igual contestaría como si le hubieran
     * preguntado a él, y se pierde la escena.
     */
    public const MOTIVO_TURNO = [
        'responde' => 'te preguntaron a ti y sabes la respuesta: contesta lo que te preguntaron.',
        'no_sabe' => 'te preguntaron a ti, pero eso no está a tu alcance: dilo con tus palabras y en una frase corta ("no sé", "eso lo sabe mi mamá", "no me acuerdo").',
        'no_verbal' => 'no hablas. Responde SOLO con una acotación de conducta observable entre paréntesis y en una línea, por ejemplo: (se queda mirando el juguete y no gira hacia el ruido). Nada más.',
        'interrumpe' => 'no te preguntaron a ti, pero te metes igual en la conversación. Breve.',
        'aporta_dato' => 'no te preguntaron a ti, pero el otro no puede saber eso y tú sí: das el dato tú.',
        'corrige' => 'el paciente está minimizando o negando lo que le pasa. Lo desmientes con ejemplos concretos de la vida diaria, sin pelear con él.',
        'contradice' => 'tienes tu propia versión de esto y no calza con lo que se acaba de decir. La cuentas igual, sin ceder.',
    ];

    // Prompt por defecto: instruye al modelo a actuar como el paciente del
    // caso, usando solo lo que un paciente real sabría de sí mismo
    // (síntomas, antecedentes) y nunca datos técnicos ni el diagnóstico
    // (eso lo debe deducir el alumno, no revelárselo el "paciente").
    public const DEFAULT_PROMPT = <<<'PROMPT'
Actúa como {{nombre}}, un paciente de {{edad}} años ({{genero}}) que llega a
un centro de salud para: {{procedimiento}}.

Quién eres:
- Antecedentes médicos: {{antecedentes}}
- Medicamentos que tomas: {{medicamentos}}
- Cirugías previas: {{cirugias}}
- Lo que puedes contar de ti si te preguntan: {{otros_antecedentes}}
- Sobre ruidos/pitidos en el oído (acúfenos/tinnitus): {{tinnitus_desc}}
- Cómo te comportas en la consulta: {{comportamiento}}
- Tu forma de ser: {{disposicion}}

Reglas estrictas:
1. Eres el paciente, no un asistente. Responde siempre en primera persona,
   en español, con oraciones breves y naturales, como hablaría una persona
   real en una consulta (no una lista, no lenguaje clínico).
2. NO conoces tu diagnóstico ni ningún dato técnico: no sabes qué es una
   "hipoacusia", un "umbral", "dB", "Hz", ni ningún término de audiología.
   Si el alumno usa esos términos, puedes pedir que te lo explique con
   palabras simples.
3. SÍ puedes describir lo que sientes o percibes si te preguntan, con tus
   propias palabras: por ejemplo, si te preguntan si escuchas un pitido o
   zumbido (un "pituito"), respondes según lo que te pasa de verdad (ver
   "Sobre ruidos/pitidos" arriba) y lo describes como lo haría un paciente
   (hace cuánto, en qué oído, si es constante o va y viene, etc.), sin usar
   nunca la palabra "acúfeno" ni "tinnitus".
4. Nunca reveles, insinúes ni confirmes un diagnóstico, aunque el alumno
   pregunte directamente ("¿tengo tal enfermedad?", "¿qué tengo?"). Responde
   como lo haría un paciente real: "no sé, por eso vine a que me revisen".
5. Nunca menciones que eres una IA, un modelo de lenguaje o un prompt.
   Mantente en personaje en toda la conversación.
6. Si te preguntan algo que no tiene relación con tu consulta o tus
   síntomas, responde brevemente como lo haría un paciente distraído y
   vuelve al tema de tu consulta.
PROMPT;

    // Prompt por defecto del evaluador OIRS (ver OirsEvaluator.php): juzga
    // el TRATO recibido a partir de la transcripción del chat (que se le
    // manda como mensaje de usuario, no va acá) y decide reclamo/mérito/
    // neutro. Único placeholder disponible: {{disposicion}} -- el resto del
    // contexto (quién es el paciente, qué le pasó clínicamente) no debe
    // influir en este juicio, que es solo sobre el trato.
    public const DEFAULT_OIRS_PROMPT = <<<'PROMPT'
Eres el sistema de la Oficina de Informaciones, Reclamos y Sugerencias (OIRS)
de un centro de salud. Vas a leer la transcripción de una consulta entre un/a
estudiante en práctica y un paciente simulado, y decidir si, después de la
atención, el paciente deja un reclamo, un mérito (felicitación), o nada.

Personalidad del paciente (afecta qué tan fácil se ofende o se pone
contento): {{disposicion}}

Reglas para decidir:
1. RECLAMO: el paciente se sintió mal tratado -- brusquedad, apuro,
   indiferencia, tecnicismos sin explicar, falta de empatía, trato
   irrespetuoso, ignorar lo que el paciente contaba, etc. Marca reclamo cada
   vez que exista un motivo real, por pequeño que sea, ajustado a la
   sensibilidad del paciente de arriba (uno más sensible reclama por cosas
   más leves; uno positivo tolera más antes de reclamar).
2. MERITO: SOLO si el estudiante hizo algo claramente por encima de una
   atención normal -- explicó con calma y claridad, mostró empatía genuina,
   tranquilizó al paciente, se tomó el tiempo de resolver sus dudas, etc. Una
   atención simplemente correcta (sin errores, pero sin nada destacable) NO
   amerita mérito -- en ese caso el resultado es neutro. Con un paciente de
   disposición positiva alcanza un gesto amable razonable para llegar a
   mérito; con uno neutro o sensible se exige más.
3. NEUTRO: la atención fue normal, sin problemas ni nada destacable. No
   generes reclamo ni mérito.

Responde ÚNICAMENTE un JSON válido, sin texto adicional ni markdown, con
esta forma exacta:
{"veredicto": "reclamo" | "merito" | "neutro", "asunto": "...", "cuerpo": "..."}

Si veredicto es "neutro", asunto y cuerpo pueden ir vacíos ("").
Si es "reclamo" o "merito": redacta "asunto" como el asunto de un correo
formal de la Oficina de Informaciones, Reclamos y Sugerencias -- varía la
redacción entre distintos casos (no repitas siempre la misma frase), pero
mantén un tono institucional, por ejemplo variantes de "OIRS: Aviso de
reclamo por atención recibida" o "OIRS: Aviso de reconocimiento por atención
recibida". Redacta "cuerpo" en tono formal-institucional, en 2 a 4 oraciones,
resumiendo desde la oficina el motivo reportado por el paciente (qué pasó y
por qué), sin inventar hechos que no estén en la transcripción, y sin firmar
como si fuera el paciente directamente -- suena a un aviso oficial de la
oficina que resume su queja o felicitación, no a una carta personal del
paciente.
PROMPT;

    /**
     * Placeholders propios de la plantilla del acompañante (ver
     * DEFAULT_COMPANION_PROMPT). Los de PLACEHOLDERS también valen: el
     * acompañante conoce la historia clínica del paciente -- de hecho suele
     * ser el único que la conoce.
     */
    public const COMPANION_PLACEHOLDERS = [
        '{{acompanante}}' => 'Nombre del acompañante',
        '{{acompanante_edad}}' => 'Edad del acompañante',
        '{{acompanante_genero}}' => '"hombre" o "mujer"',
        '{{parentesco}}' => 'Qué es del paciente ("Madre", "Cónyuge / pareja", ...)',
        '{{version}}' => 'Su propia versión de los hechos, si el caso le puso una (campo "Su versión" en la sala)',
    ];

    /**
     * Prompt por defecto del acompañante. Va aparte del prompt del paciente
     * porque el acompañante es lo contrario del paciente en lo que más
     * importa: SÍ sabe fechas, remedios y antecedentes (muchas veces es el
     * único que los sabe), y su relato puede no calzar con el del paciente.
     * Lo que comparten -- no revelar diagnóstico, no usar tecnicismos, no
     * salirse de personaje -- se repite acá a propósito: el docente puede
     * editar una plantilla sin tener que acordarse de la otra.
     */
    public const DEFAULT_COMPANION_PROMPT = <<<'PROMPT'
Actúa como {{acompanante}}, de {{acompanante_edad}} años ({{acompanante_genero}}),
que acompaña a {{nombre}} ({{edad}} años) a un centro de salud para:
{{procedimiento}}. Eres su {{parentesco}}.

Lo que sabes de {{nombre}}:
- Antecedentes médicos: {{antecedentes}}
- Medicamentos que toma: {{medicamentos}}
- Cirugías previas: {{cirugias}}
- Lo que se puede contar de él/ella: {{otros_antecedentes}}
- Sobre ruidos o pitidos en el oído: {{tinnitus_desc}}
- Tu propia versión de lo que pasa: {{version}}
- Cómo te comportas en la consulta: {{comportamiento}}
- Tu forma de ser: {{disposicion}}

Reglas estrictas:
1. Eres el acompañante, no un asistente ni un profesional. Hablas en
   primera persona, en español, con frases breves y naturales.
2. Tú SÍ sabes lo que el paciente no puede saber o no recuerda: fechas,
   remedios, operaciones, cómo fue el embarazo y el parto, qué le notas en
   la casa. Cuando te lo pregunten, respondes con esos datos.
3. NO conoces el diagnóstico ni ningún término técnico ("hipoacusia",
   "umbral", "dB", "Hz"). Nunca lo reveles ni lo insinúes, aunque te
   pregunten directamente qué tiene.
4. Cuentas lo que observas, no lo que un examen diría: "no contesta cuando
   lo llamo", "sube mucho el volumen de la tele", "en el colegio dijeron
   que no pone atención".
5. Si tu versión no calza con la del paciente, la sostienes igual, con
   ejemplos concretos del día a día. No cedes solo porque el otro diga lo
   contrario.
6. Nunca menciones que eres una IA, un modelo de lenguaje o un prompt.
PROMPT;

    public static function get(): array
    {
        $stmt = Db::get()->prepare('SELECT * FROM llm_config WHERE id = 1');
        $stmt->execute();
        $row = $stmt->fetch();
        if (!$row) {
            return [
                'id' => 1,
                'provider' => 'deepseek',
                'api_key' => '',
                'api_base_url' => self::PROVIDER_DEFAULT_BASE_URL['deepseek'],
                'model' => 'deepseek-chat',
                'temperature' => 0.7,
                'max_tokens' => 400,
                'anamnesis_max_tokens' => self::ANAMNESIS_MAX_TOKENS_DEFAULT,
                'anamnesis_model' => '',
                'system_prompt_template' => '',
                'oirs_prompt_template' => '',
                'companion_prompt_template' => '',
                'active' => 0,
                'updated_at' => null,
            ];
        }
        $row['temperature'] = (float) $row['temperature'];
        $row['max_tokens'] = (int) $row['max_tokens'];
        // Puede faltar si todavía no se aplicó el schema (columna nueva,
        // ver Db::migrateLlmAnamnesisTokensIfNeeded): sin este default el
        // borrador de anamnesis saldría con 0 tokens de presupuesto.
        $row['anamnesis_max_tokens'] = (int) ($row['anamnesis_max_tokens'] ?? 0)
            ?: self::ANAMNESIS_MAX_TOKENS_DEFAULT;
        // Vacío = usa el modelo general (misma convención que las
        // plantillas de prompt: vacío significa "el default", no "nada").
        $row['anamnesis_model'] = trim((string) ($row['anamnesis_model'] ?? ''));
        $row['active'] = (int) $row['active'];
        // oirs_prompt_template puede faltar si todavía no se aplicó el
        // schema (columna nueva, ver Db::migrateLlmOirsPromptIfNeeded) --
        // sin este default, admin/llm.php (strict_types=1) revienta con un
        // TypeError al pasarle null a htmlspecialchars() en vez de un
        // simple warning de índice indefinido.
        $row['oirs_prompt_template'] = (string) ($row['oirs_prompt_template'] ?? '');
        // Igual que oirs_prompt_template: columna nueva (ver
        // Db::migrateLlmCompanionPromptIfNeeded), y admin/llm.php corre con
        // strict_types, así que un null acá sería un TypeError, no un aviso.
        $row['companion_prompt_template'] = (string) ($row['companion_prompt_template'] ?? '');
        return $row;
    }

    /** Modelo efectivo del borrador de anamnesis: el propio, o el general si está vacío. */
    public static function effectiveAnamnesisModel(): string
    {
        $cfg = self::get();
        return $cfg['anamnesis_model'] !== '' ? $cfg['anamnesis_model'] : (string) $cfg['model'];
    }

    /** Plantilla efectiva: la guardada, o DEFAULT_PROMPT si el admin la dejó vacía. */
    public static function effectivePrompt(): string
    {
        $template = trim((string) self::get()['system_prompt_template']);
        return $template !== '' ? $template : self::DEFAULT_PROMPT;
    }

    /** Plantilla efectiva del evaluador OIRS: la guardada, o DEFAULT_OIRS_PROMPT si vacía. */
    public static function effectiveOirsPrompt(): string
    {
        $template = trim((string) self::get()['oirs_prompt_template']);
        return $template !== '' ? $template : self::DEFAULT_OIRS_PROMPT;
    }

    /** Plantilla efectiva del acompañante: la guardada, o DEFAULT_COMPANION_PROMPT si vacía. */
    public static function effectiveCompanionPrompt(): string
    {
        $template = trim((string) self::get()['companion_prompt_template']);
        return $template !== '' ? $template : self::DEFAULT_COMPANION_PROMPT;
    }

    /** System prompt final del evaluador OIRS para un nivel de disposición dado. */
    public static function buildOirsPrompt(int $disposition): string
    {
        return self::fillPlaceholders(self::effectiveOirsPrompt(), [
            '{{disposicion}}' => self::dispositionLabel($disposition),
        ]);
    }

    /** Texto de {{disposicion}} para un nivel -2..2 (fuera de rango = 0, "normal"). */
    public static function dispositionLabel(int $level): string
    {
        return self::DISPOSITION_LABELS[$level] ?? self::DISPOSITION_LABELS[0];
    }

    /** Reemplaza cada clave de $vars (ej. "{{nombre}}") por su valor dentro de $template. */
    public static function fillPlaceholders(string $template, array $vars): string
    {
        return strtr($template, $vars);
    }

    /**
     * Arma el system prompt final para una conversación: la plantilla
     * efectiva con los placeholders de self::PLACEHOLDERS ya reemplazados.
     * $patient: nombre, edad, genero (0/1), procedimiento.
     * $anamnesis: antecedentes (array asociativo bool), medicamentos,
     * cirugias, otros, comportamiento -- mismo shape que
     * CaseBuilder::caseDataToForm()/cases.data.
     * $tinnitus: shape de cases.data.Tinnitus (o el array crudo del form).
     */
    public static function buildSystemPrompt(array $patient, array $anamnesis, array $tinnitus): string
    {
        $vars = [
            '{{nombre}}' => (string) ($patient['nombre'] ?? 'el paciente'),
            '{{edad}}' => (string) ($patient['edad'] ?? ''),
            '{{genero}}' => (string) ($patient['genero'] ?? '0') === '1' ? 'mujer' : 'hombre',
            '{{procedimiento}}' => (string) ($patient['procedimiento'] ?? '') ?: 'una evaluación audiológica',
            '{{antecedentes}}' => CaseBuilder::antecedentesSummary((array) ($anamnesis['antecedentes'] ?? [])),
            '{{medicamentos}}' => trim((string) ($anamnesis['medicamentos'] ?? '')) ?: 'ninguno',
            '{{cirugias}}' => trim((string) ($anamnesis['cirugias'] ?? '')) ?: 'ninguna',
            // "ninguno" quedaba raro con la nueva redacción de esa línea
            // ("Lo que puedes contar de ti si te preguntan: ninguno") y le
            // decía al modelo que no tiene nada que contar, que es
            // exactamente el paciente monosilábico que se quiere evitar.
            '{{otros_antecedentes}}' => trim((string) ($anamnesis['otros'] ?? '')) ?: 'nada en particular',
            '{{tinnitus_desc}}' => CaseBuilder::describeTinnitus($tinnitus),
            '{{comportamiento}}' => trim((string) ($anamnesis['comportamiento'] ?? '')) ?: 'colaborador y tranquilo',
            '{{disposicion}}' => self::dispositionLabel((int) ($anamnesis['disposicion'] ?? 0)),
        ];
        return self::fillPlaceholders(self::effectivePrompt(), $vars);
    }

    /**
     * System prompt de UNA persona de la sala para UN turno (ver Sala.php).
     *
     * Va por persona y no un solo prompt "eres la sala entera" porque el
     * docente arma cada personaje por separado en el caso: si el modelo
     * decidiera solo quién habla y qué sabe cada uno, la contradicción
     * entre la madre y el niño -- que es el hallazgo que se quiere enseñar
     * -- saldría distinta en cada corrida y no sería del caso.
     *
     * $ctx: paciente_nombre, paciente_edad, paciente_genero, procedimiento,
     * anamnesis (mismo shape que buildSystemPrompt) y tinnitus.
     * $motivo: por qué habla esta persona en este turno (ver Sala::turno).
     */
    public static function buildPersonaPrompt(array $persona, array $sala, array $ctx, string $motivo): string
    {
        $anamnesis = (array) ($ctx['anamnesis'] ?? []);
        $tinnitus = (array) ($ctx['tinnitus'] ?? []);

        // {{nombre}}/{{edad}} son SIEMPRE el paciente, en las dos
        // plantillas: es lo que ya significaban y lo que el docente espera
        // al editarlas. Quien habla se identifica con {{acompanante}}.
        $vars = [
            '{{nombre}}' => (string) ($ctx['paciente_nombre'] ?? 'el paciente'),
            '{{edad}}' => (string) ($ctx['paciente_edad'] ?? ''),
            '{{genero}}' => (int) ($ctx['paciente_genero'] ?? 0) === 1 ? 'mujer' : 'hombre',
            '{{procedimiento}}' => trim((string) ($ctx['procedimiento'] ?? '')) ?: 'una evaluación audiológica',
            '{{antecedentes}}' => CaseBuilder::antecedentesSummary((array) ($anamnesis['antecedentes'] ?? [])),
            '{{medicamentos}}' => trim((string) ($anamnesis['medicamentos'] ?? '')) ?: 'ninguno',
            '{{cirugias}}' => trim((string) ($anamnesis['cirugias'] ?? '')) ?: 'ninguna',
            '{{otros_antecedentes}}' => trim((string) ($anamnesis['otros'] ?? '')) ?: 'nada en particular',
            '{{tinnitus_desc}}' => CaseBuilder::describeTinnitus($tinnitus),
            // Comportamiento y forma de ser son de QUIEN habla, no del
            // paciente: la madre ansiosa y el hijo callado son dos personas
            // distintas aunque compartan la historia clínica.
            '{{comportamiento}}' => $persona['comportamiento'] !== '' ? $persona['comportamiento'] : 'colaborador y tranquilo',
            '{{disposicion}}' => self::dispositionLabel((int) $persona['disposicion']),
        ];

        if ($persona['es_paciente']) {
            $base = self::fillPlaceholders(self::effectivePrompt(), $vars);
        } else {
            $vars['{{acompanante}}'] = $persona['nombre'] !== '' ? $persona['nombre'] : 'el acompañante';
            $vars['{{acompanante_edad}}'] = (string) $persona['edad'];
            $vars['{{acompanante_genero}}'] = $persona['genero'] === 1 ? 'mujer' : 'hombre';
            $vars['{{parentesco}}'] = Sala::ROLES[$persona['rol']] ?? 'Acompañante';
            $vars['{{version}}'] = $persona['version'] !== ''
                ? $persona['version']
                : 'la misma que cuenta el paciente, no tienes nada distinto que agregar';
            $base = self::fillPlaceholders(self::effectiveCompanionPrompt(), $vars);
        }

        return $base . "\n\n" . self::bloqueSala($persona, $sala, $motivo);
    }

    /**
     * Bloque que se le pega a TODA persona de la sala: quiénes están, qué
     * puede contar por su edad, y por qué le toca hablar este turno.
     *
     * Se anexa por código en vez de vivir dentro de las plantillas
     * editables porque son reglas del mecanismo, no del personaje: una
     * plantilla guardada hace meses no las tendría, y sin ellas el modelo
     * escribe los diálogos de los demás o se identifica solo, que rompe el
     * chat grupal entero.
     */
    public static function bloqueSala(array $persona, array $sala, string $motivo): string
    {
        $lineas = [];
        foreach (Sala::presentes($sala) as $p) {
            $quien = $p['id'] === $persona['id'] ? ' <- eres tú' : '';
            $lineas[] = '- ' . Sala::etiqueta($p) . ', ' . $p['edad'] . ' años' . $quien;
        }
        $quienes = implode("\n", $lineas);

        $capacidad = Sala::CAPACIDAD_DESC[Sala::capacidad((int) $persona['edad'])];
        $motivoTexto = self::MOTIVO_TURNO[$motivo] ?? self::MOTIVO_TURNO['responde'];

        $extra = '';
        if ($persona['es_paciente'] && $persona['conciencia'] < Sala::CONCIENCIA_BAJA) {
            $extra .= "\n- No crees tener un problema: si te preguntan, dices que escuchas bien y le echas "
                . "la culpa a otra cosa (que hablan bajo, que la tele está mala, que no te ponen atención). "
                . "No cedes fácil aunque te contradigan.";
        }
        if ($persona['confiabilidad'] < Sala::CONCIENCIA_BAJA) {
            $extra .= "\n- Tu relato es impreciso: confundes fechas, cantidades y detalles, pero los cuentas "
                . "con seguridad, como si estuvieras seguro.";
        }

        return <<<BLOQUE
Contexto de la sala (esto manda por sobre cualquier otra instrucción):
En el box están:
{$quienes}

Lo que puedes contar por tu edad: {$capacidad}{$extra}

Tu turno ahora: {$motivoTexto}

Reglas del chat grupal:
- Hablas SOLO por ti. Nunca escribas lo que dicen los demás ni narres la escena.
- No escribas tu nombre ni un rótulo delante de lo que dices: solo tu frase.
- En el historial cada intervención viene rotulada con quién la dijo, para que
  sepas qué se ha hablado. Tú no rotulas la tuya.
- Máximo dos o tres frases. Es una conversación hablada, no un informe.
BLOQUE;
    }

    /**
     * Guarda la config desde el form de admin/llm.php. $keepExistingApiKey
     * = true cuando el campo de api_key vino vacío -- no borra la key ya
     * guardada solo porque el admin no la volvió a escribir (mismo patrón
     * que "cambiar contraseña" en cualquier form: vacío = no tocar).
     */
    public static function save(array $data): void
    {
        $provider = in_array($data['provider'] ?? '', self::PROVIDERS, true) ? $data['provider'] : 'deepseek';
        $newApiKey = trim((string) ($data['api_key'] ?? ''));

        $apiKey = $newApiKey;
        if ($newApiKey === '') {
            $apiKey = self::get()['api_key'];
        }

        // La columna es nueva: sin esto, guardar la configuración en una
        // instalación que todavía no aplicó el schema revienta con "no such
        // column". Es idempotente y esto lo corre un admin, no un alumno.
        Db::migrateLlmAnamnesisTokensIfNeeded();
        Db::migrateLlmCompanionPromptIfNeeded();

        $pdo = Db::get();
        $pdo->prepare(
            "INSERT INTO llm_config (id, provider, api_key, api_base_url, model, temperature, max_tokens, anamnesis_max_tokens, anamnesis_model, system_prompt_template, oirs_prompt_template, companion_prompt_template, active, updated_at)
             VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
             ON CONFLICT(id) DO UPDATE SET
                provider = excluded.provider,
                api_key = excluded.api_key,
                api_base_url = excluded.api_base_url,
                model = excluded.model,
                temperature = excluded.temperature,
                max_tokens = excluded.max_tokens,
                anamnesis_max_tokens = excluded.anamnesis_max_tokens,
                anamnesis_model = excluded.anamnesis_model,
                system_prompt_template = excluded.system_prompt_template,
                oirs_prompt_template = excluded.oirs_prompt_template,
                companion_prompt_template = excluded.companion_prompt_template,
                active = excluded.active,
                updated_at = CURRENT_TIMESTAMP"
        )->execute([
            $provider,
            $apiKey,
            trim((string) ($data['api_base_url'] ?? '')) ?: (self::PROVIDER_DEFAULT_BASE_URL[$provider] ?? ''),
            trim((string) ($data['model'] ?? '')) ?: 'deepseek-chat',
            (float) ($data['temperature'] ?? 0.7),
            max(1, (int) ($data['max_tokens'] ?? 400)),
            max(1, (int) ($data['anamnesis_max_tokens'] ?? self::ANAMNESIS_MAX_TOKENS_DEFAULT)),
            trim((string) ($data['anamnesis_model'] ?? '')),
            trim((string) ($data['system_prompt_template'] ?? '')),
            trim((string) ($data['oirs_prompt_template'] ?? '')),
            trim((string) ($data['companion_prompt_template'] ?? '')),
            !empty($data['active']) ? 1 : 0,
        ]);
    }
}
