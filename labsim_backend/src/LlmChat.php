<?php

final class LlmChat
{
    /**
     * Llama al endpoint Chat Completions (formato OpenAI, el mismo que
     * habla DeepSeek) con el system prompt + historial + mensaje nuevo, y
     * devuelve el texto de respuesta. Lanza RuntimeException con un mensaje
     * legible para el admin ante cualquier falla (sin api_key, red, HTTP
     * de error, shape inesperado) -- quien llama decide cómo mostrarlo.
     */
    public static function reply(string $systemPrompt, array $history, string $userMessage): string
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
            'max_tokens' => $cfg['max_tokens'],
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

        $content = $decoded['choices'][0]['message']['content'] ?? null;
        if (!is_string($content) || $content === '') {
            // Se incluye el body crudo (truncado) para diagnosticar sin
            // depender de error_log del servidor -- este mensaje solo lo ve
            // el admin (llm_chat_test.php / oirs_test.php) o queda en el
            // error_log de OirsEvaluator, nunca llega al alumno.
            throw new RuntimeException(
                'El LLM devolvió una respuesta vacía o con formato inesperado. Body crudo: '
                . substr($response, 0, 1000)
            );
        }

        return $content;
    }
}
