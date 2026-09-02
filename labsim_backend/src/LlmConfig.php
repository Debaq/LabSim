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
                'active' => 0,
                'updated_at' => null,
            ];
        }
        $row['temperature'] = (float) $row['temperature'];
        $row['max_tokens'] = (int) $row['max_tokens'];
        $row['active'] = (int) $row['active'];
        return $row;
    }

    /** Plantilla efectiva: la guardada, o DEFAULT_PROMPT si el admin la dejó vacía. */
    public static function effectivePrompt(): string
    {
        $template = trim((string) self::get()['system_prompt_template']);
        return $template !== '' ? $template : self::DEFAULT_PROMPT;
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
            "INSERT INTO llm_config (id, provider, api_key, api_base_url, model, temperature, max_tokens, system_prompt_template, active, updated_at)
             VALUES (1, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
             ON CONFLICT(id) DO UPDATE SET
                provider = excluded.provider,
                api_key = excluded.api_key,
                api_base_url = excluded.api_base_url,
                model = excluded.model,
                temperature = excluded.temperature,
                max_tokens = excluded.max_tokens,
                system_prompt_template = excluded.system_prompt_template,
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
            !empty($data['active']) ? 1 : 0,
        ]);
    }
}
