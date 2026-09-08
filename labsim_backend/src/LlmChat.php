<?php

// No hay autoloader: la dependencia se declara donde se usa. Hasta ahora
// la cargaba cada llamador a mano, así que un endpoint nuevo moría con
// "Class 'LlmConfig' not found" recién al apretar el botón.
require_once __DIR__ . '/LlmConfig.php';

/**
 * El modelo se quedó sin presupuesto ANTES de escribir la respuesta.
 *
 * Tiene clase propia porque es la única falla del LLM que quien llama puede
 * arreglar solo: reintentar con más tokens. Las demás (sin api_key, red
 * caída, HTTP de error) no se arreglan reintentando, así que distinguirlas
 * por el texto del mensaje sería frágil justo donde importa.
 */
final class LlmBudgetException extends RuntimeException
{
}

final class LlmChat
{
    /**
     * Segundos de espera por defecto. Dimensionado para el chat con el
     * paciente, donde hay un alumno mirando la pantalla: si el modelo no
     * contestó en 30 segundos, la conversación ya se rompió igual.
     */
    public const TIMEOUT_DEFAULT_S = 30;

    /**
     * Consumo de la última llamada, tal como lo reporta la API en `usage`.
     *
     * Estático y no en el valor de retorno para no cambiarle la firma a los
     * tres llamadores que solo quieren el texto. Sirve para dejar de
     * adivinar de dónde sale la factura: en un modelo de razonamiento casi
     * todo el gasto son tokens de pensamiento que no se ven en la
     * respuesta, así que mirar el texto que volvió no dice nada.
     *
     * @var array<string,int>
     */
    private static array $lastUsage = [];

    /** Consumo de la última llamada: prompt, completion, razonamiento y total. */
    public static function lastUsage(): array
    {
        return self::$lastUsage;
    }

    /**
     * Normaliza las opciones de una tarea contra los defaults. Las claves
     * desconocidas se ignoran en silencio: es configuración de código, no
     * entrada de usuario.
     *
     * @param array<string,mixed> $opciones
     * @return array{model: ?string, max_tokens: ?int, timeout: ?int, campo_tokens: string}
     */
    public static function opcionesTarea(array $opciones): array
    {
        return [
            'model' => isset($opciones['model']) && trim((string) $opciones['model']) !== ''
                ? trim((string) $opciones['model']) : null,
            'max_tokens' => isset($opciones['max_tokens']) ? (int) $opciones['max_tokens'] : null,
            'timeout' => isset($opciones['timeout']) ? (int) $opciones['timeout'] : null,
            'campo_tokens' => (string) ($opciones['campo_tokens'] ?? 'Máximo de tokens por respuesta'),
        ];
    }

    /**
     * Llama al endpoint Chat Completions (formato OpenAI, el mismo que
     * habla DeepSeek) con el system prompt + historial + mensaje nuevo, y
     * devuelve el texto de respuesta. Lanza RuntimeException con un mensaje
     * legible para el admin ante cualquier falla (sin api_key, red, HTTP
     * de error, shape inesperado) -- quien llama decide cómo mostrarlo.
     *
     * `$maxTokens` pisa el límite configurado, que está dimensionado para
     * las respuestas cortas del chat del paciente. Una tarea más larga (o
     * un modelo de razonamiento, que gasta presupuesto ANTES de escribir la
     * respuesta) necesita más aire: sin esto devuelve `content` vacío con
     * todo el pensamiento adentro de `reasoning_content`.
     *
     * `$opciones` deja que cada tarea pise lo que la configuración fija
     * para el chat con el paciente (ver opcionesTarea): `model`,
     * `max_tokens`, `timeout` y `campo_tokens`. Van en un array y no como
     * parámetros sueltos porque ya eran cuatro y la llamada se volvía
     * ilegible; los llamadores que no pisan nada siguen escribiéndose con
     * tres argumentos.
     */
    public static function reply(string $systemPrompt, array $history, string $userMessage,
                                 array $opciones = []): string
    {
        $cfgTarea = self::opcionesTarea($opciones);
        $maxTokens = $cfgTarea['max_tokens'];
        $campoTokens = $cfgTarea['campo_tokens'];
        $timeoutSegundos = $cfgTarea['timeout'];
        $modeloTarea = $cfgTarea['model'];
        $cfg = LlmConfig::get();
        if ($cfg['api_key'] === '') {
            throw new RuntimeException('Falta configurar el api_key del LLM en Admin -> IA Paciente.');
        }
        if ($cfg['api_base_url'] === '') {
            throw new RuntimeException('Falta la base URL de la API en Admin -> IA Paciente.');
        }

        $messages = [['role' => 'system', 'content' => $systemPrompt]];
        foreach ($history as $h) {
            $messages[] = ['role' => $h['role'] === 'assistant' ? 'assistant' : 'user', 'content' => (string) $h['content']];
        }
        $messages[] = ['role' => 'user', 'content' => $userMessage];

        $modelo = $modeloTarea ?? (string) $cfg['model'];
        $payload = json_encode([
            'model' => $modelo,
            'messages' => $messages,
            'temperature' => $cfg['temperature'],
            'max_tokens' => $maxTokens ?? $cfg['max_tokens'],
        ], JSON_UNESCAPED_UNICODE);

        $url = rtrim($cfg['api_base_url'], '/') . '/chat/completions';
        $ch = curl_init($url);
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_POST => true,
            CURLOPT_POSTFIELDS => $payload,
            CURLOPT_HTTPHEADER => [
                'Content-Type: application/json',
                'Authorization: Bearer ' . $cfg['api_key'],
            ],
            CURLOPT_TIMEOUT => $timeoutSegundos ?? self::TIMEOUT_DEFAULT_S,
        ]);
        $response = curl_exec($ch);
        $curlError = curl_error($ch);
        // Se captura ANTES de cerrar: curl_close no invalida el handle en
        // PHP 8, pero depender de eso es pedir un bug silencioso el día que
        // cambie.
        $curlErrno = curl_errno($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($response === false) {
            // El timeout se distingue del resto de fallas de red porque se
            // arregla distinto: no es que el servidor no esté, es que el
            // modelo tarda más de lo que se le dio. Decir solo "operation
            // timed out" deja al admin sin saber qué tocar.
            if ($curlErrno === CURLE_OPERATION_TIMEDOUT) {
                throw new RuntimeException(sprintf(
                    'El modelo "%s" no alcanzó a responder en %d segundos. Los modelos de razonamiento tardan bastante más en tareas largas: probá con uno sin razonamiento (deepseek-chat, por ejemplo) en Admin -> IA Paciente.',
                    $modelo, $timeoutSegundos ?? self::TIMEOUT_DEFAULT_S
                ));
            }
            throw new RuntimeException('No se pudo conectar con el LLM: ' . $curlError);
        }

        $decoded = json_decode($response, true);

        if ($status < 200 || $status >= 300) {
            $apiMsg = is_array($decoded) ? ($decoded['error']['message'] ?? null) : null;
            throw new RuntimeException("El LLM respondió con error HTTP {$status}: " . ($apiMsg ?? $response));
        }

        // `usage` es opcional en el protocolo: si el proveedor no lo manda,
        // queda vacío y quien lo muestra decide qué decir.
        $usage = is_array($decoded['usage'] ?? null) ? $decoded['usage'] : [];
        self::$lastUsage = [
            'prompt' => (int) ($usage['prompt_tokens'] ?? 0),
            'completion' => (int) ($usage['completion_tokens'] ?? 0),
            // DeepSeek lo reporta anidado; otros proveedores lo omiten.
            'razonamiento' => (int) ($usage['completion_tokens_details']['reasoning_tokens'] ?? 0),
            'total' => (int) ($usage['total_tokens'] ?? 0),
        ];

        return self::extractContent(
            is_array($decoded) ? $decoded : [], (string) $response,
            $modelo, (int) ($maxTokens ?? $cfg['max_tokens']), $campoTokens
        );
    }

    /**
     * El texto de la respuesta, o una excepción que dice qué hacer.
     *
     * Aparte para poder testearlo: es la rama que más se rompe, y depende
     * del modelo configurado (los de razonamiento contestan distinto), no
     * de nuestro código.
     *
     * @param array<string,mixed> $decoded Body ya parseado
     * @param string $rawBody Body crudo, para el mensaje de último recurso
     */
    public static function extractContent(array $decoded, string $rawBody, string $model, int $maxTokens,
                                          string $campoTokens = 'Máximo de tokens por respuesta'): string
    {
        $content = $decoded['choices'][0]['message']['content'] ?? null;
        if (is_string($content) && $content !== '') {
            return $content;
        }

        // Caso propio de los modelos de razonamiento: se quedaron sin
        // presupuesto pensando y nunca llegaron a escribir. El body crudo lo
        // delata (reasoning_content lleno, content vacío, finish_reason
        // "length"), pero leerlo no le dice a nadie qué hacer -- el arreglo
        // es subir max_tokens, no reintentar.
        $razonamiento = (string) ($decoded['choices'][0]['message']['reasoning_content'] ?? '');
        $corte = (string) ($decoded['choices'][0]['finish_reason'] ?? '');
        if ($razonamiento !== '' || $corte === 'length') {
            throw new LlmBudgetException(sprintf(
                'El modelo "%s" se quedó sin tokens razonando y no alcanzó a escribir la respuesta (límite actual: %d). Subí "%s" en Admin -> IA Paciente, o elegí un modelo sin razonamiento para esta tarea.',
                $model, $maxTokens, $campoTokens
            ));
        }

        // Se incluye el body crudo (truncado) para diagnosticar sin depender
        // de error_log del servidor -- este mensaje solo lo ve el admin
        // (llm_chat_test.php / oirs_test.php) o queda en el error_log de
        // OirsEvaluator, nunca llega al alumno.
        throw new RuntimeException(
            'El LLM devolvió una respuesta vacía o con formato inesperado. Body crudo: '
            . substr($rawBody, 0, 1000)
        );
    }
}
