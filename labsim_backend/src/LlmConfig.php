<?php

final class LlmConfig
{
    public const PROVIDERS = ['deepseek', 'openai_compatible'];

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
        '{{otros_antecedentes}}' => 'Campo "otros" de la anamnesis',
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

    // Prompt por defecto: instruye al modelo a actuar como el paciente del
    // caso, usando solo lo que un paciente real sabría de sí mismo
    // (síntomas, antecedentes) y nunca datos técnicos ni el diagnóstico
    // (eso lo debe deducir el alumno, no revelárselo el "paciente").
    public const DEFAULT_PROMPT = <<<'PROMPT'
Actúa como {{nombre}}, un paciente de {{edad}} años ({{genero}}) que llega a
una consulta de fonoaudiología/otorrinolaringología por: {{procedimiento}}.

Quién eres:
- Antecedentes médicos: {{antecedentes}}
- Medicamentos que tomas: {{medicamentos}}
- Cirugías previas: {{cirugias}}
- Otros antecedentes: {{otros_antecedentes}}
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
estudiante de fonoaudiología/otorrinolaringología y un paciente simulado, y
decidir si, después de la atención, el paciente deja un reclamo, un mérito
(felicitación), o nada.

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
                'system_prompt_template' => '',
                'oirs_prompt_template' => '',
                'active' => 0,
                'updated_at' => null,
            ];
        }
        $row['temperature'] = (float) $row['temperature'];
        $row['max_tokens'] = (int) $row['max_tokens'];
        $row['active'] = (int) $row['active'];
        // oirs_prompt_template puede faltar si todavía no se aplicó el
        // schema (columna nueva, ver Db::migrateLlmOirsPromptIfNeeded) --
        // sin este default, admin/llm.php (strict_types=1) revienta con un
        // TypeError al pasarle null a htmlspecialchars() en vez de un
        // simple warning de índice indefinido.
        $row['oirs_prompt_template'] = (string) ($row['oirs_prompt_template'] ?? '');
        return $row;
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
            '{{otros_antecedentes}}' => trim((string) ($anamnesis['otros'] ?? '')) ?: 'ninguno',
            '{{tinnitus_desc}}' => CaseBuilder::describeTinnitus($tinnitus),
            '{{comportamiento}}' => trim((string) ($anamnesis['comportamiento'] ?? '')) ?: 'colaborador y tranquilo',
            '{{disposicion}}' => self::dispositionLabel((int) ($anamnesis['disposicion'] ?? 0)),
        ];
        return self::fillPlaceholders(self::effectivePrompt(), $vars);
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

        $pdo = Db::get();
        $pdo->prepare(
            "INSERT INTO llm_config (id, provider, api_key, api_base_url, model, temperature, max_tokens, system_prompt_template, oirs_prompt_template, active, updated_at)
             VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
             ON CONFLICT(id) DO UPDATE SET
                provider = excluded.provider,
                api_key = excluded.api_key,
                api_base_url = excluded.api_base_url,
                model = excluded.model,
                temperature = excluded.temperature,
                max_tokens = excluded.max_tokens,
                system_prompt_template = excluded.system_prompt_template,
                oirs_prompt_template = excluded.oirs_prompt_template,
                active = excluded.active,
                updated_at = CURRENT_TIMESTAMP"
        )->execute([
            $provider,
            $apiKey,
            trim((string) ($data['api_base_url'] ?? '')) ?: (self::PROVIDER_DEFAULT_BASE_URL[$provider] ?? ''),
            trim((string) ($data['model'] ?? '')) ?: 'deepseek-chat',
            (float) ($data['temperature'] ?? 0.7),
            max(1, (int) ($data['max_tokens'] ?? 400)),
            trim((string) ($data['system_prompt_template'] ?? '')),
            trim((string) ($data['oirs_prompt_template'] ?? '')),
            !empty($data['active']) ? 1 : 0,
        ]);
    }
}
