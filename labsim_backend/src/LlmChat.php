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
     * `$campoTokens` es el rótulo del campo que hay que subir en
     * Admin -> IA Paciente si el presupuesto no alcanza. Hay más de uno y
     * subir el que no es no arregla nada, así que el error lo nombra.
     */
    public static function reply(string $systemPrompt, array $history, string $userMessage,
                                 ?int $maxTokens = null,
                                 string $campoTokens = 'Máximo de tokens por respuesta'): string
    {
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

        $payload = json_encode([
            'model' => $cfg['model'],
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
            CURLOPT_TIMEOUT => 30,
        ]);
        $response = curl_exec($ch);
        $curlError = curl_error($ch);
        $status = curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($response === false) {
            throw new RuntimeException('No se pudo conectar con el LLM: ' . $curlError);
        }

        $decoded = json_decode($response, true);

        if ($status < 200 || $status >= 300) {
            $apiMsg = is_array($decoded) ? ($decoded['error']['message'] ?? null) : null;
            throw new RuntimeException("El LLM respondió con error HTTP {$status}: " . ($apiMsg ?? $response));
        }

        return self::extractContent(
            is_array($decoded) ? $decoded : [], (string) $response,
            (string) $cfg['model'], (int) ($maxTokens ?? $cfg['max_tokens']), $campoTokens
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
