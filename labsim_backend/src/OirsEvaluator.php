<?php

final class OirsEvaluator
{
    /** Remitente que ve el alumno en la bandeja para este tipo de mensaje (ver inbox_messages.remitente). */
    private const REMITENTE = 'Oficina de Informaciones, Reclamos y Sugerencias (OIRS)';

    /**
     * Al cerrar una atención (attendance_action.php, action 'atendido'),
     * relee el chat completo del alumno con el paciente simulado y le pide
     * al LLM que juzgue el TRATO recibido (no el conocimiento clínico) como
     * lo haría la oficina de reclamos de un centro de salud real. Si
     * corresponde, deja un aviso en inbox_messages -- la bandeja del alumno
     * (ver inbox.php).
     *
     * Best-effort a propósito: sin chat que evaluar, LLM no configurado, o
     * cualquier falla de red/parseo, no pasa nada -- cerrar la atención
     * nunca debe fallar por culpa de este paso extra. El llamador no
     * necesita try/catch.
     */
    public static function evaluate(int $appointmentId, int $studentId, ?string $caseId, ?int $patientId): void
    {
        try {
            self::doEvaluate($appointmentId, $studentId, $caseId, $patientId);
        } catch (Throwable $e) {
            error_log('[OirsEvaluator] ' . $e->getMessage());
        }
    }

    private static function doEvaluate(int $appointmentId, int $studentId, ?string $caseId, ?int $patientId): void
    {
        if (!$caseId || !LlmConfig::get()['active']) {
            return;
        }

        // Ya evaluado (UNIQUE appointment_id+student_id) -- no se re-evalúa
        // si el alumno reabre y vuelve a cerrar la misma atención.
        $stmt = Db::get()->prepare('SELECT 1 FROM inbox_messages WHERE appointment_id = ? AND student_id = ?');
        $stmt->execute([$appointmentId, $studentId]);
        if ($stmt->fetch()) {
            return;
        }

        $stmt = Db::get()->prepare(
            "SELECT role, content FROM llm_chat_logs
             WHERE appointment_id = ? AND student_id = ? ORDER BY id"
        );
        $stmt->execute([$appointmentId, $studentId]);
        $log = $stmt->fetchAll();
        if (!$log) {
            return; // el alumno no conversó con el paciente -- nada que juzgar
        }

        $stmt = Db::get()->prepare('SELECT data FROM cases WHERE id = ?');
        $stmt->execute([$caseId]);
        $caseRow = $stmt->fetch();
        $caseData = $caseRow ? (json_decode((string) $caseRow['data'], true) ?: []) : [];
        $disposition = (int) ($caseData['PatientDisposition'] ?? 0);

        $transcript = self::transcriptFromLog($log);

        $systemPrompt = LlmConfig::buildOirsPrompt($disposition);

        try {
            $raw = LlmChat::reply($systemPrompt, [], $transcript);
        } catch (Throwable $e) {
            error_log('[OirsEvaluator] LLM call failed: ' . $e->getMessage());
            return;
        }

        $verdict = self::parseVerdict($raw);
        if ($verdict === null || $verdict['veredicto'] === 'neutro') {
            return;
        }
        if ($verdict['asunto'] === '' || $verdict['cuerpo'] === '') {
            return; // salida del LLM incompleta -- mejor no dejar un aviso vacío
        }

        $stmt = Db::get()->prepare(
            'INSERT INTO inbox_messages (appointment_id, student_id, patient_id, tipo, remitente, asunto, cuerpo)
             VALUES (?, ?, ?, ?, ?, ?, ?)'
        );
        $stmt->execute([
            $appointmentId,
            $studentId,
            $patientId,
            $verdict['veredicto'],
            self::REMITENTE,
            $verdict['asunto'],
            $verdict['cuerpo'],
        ]);
    }

    /**
     * Igual que evaluate(), pero para el chat de prueba de case_create.php
     * (Admin -> Anamnesis -> "Probar conversación"): $history es el array
     * {role, content}[] que ya tiene el JS del navegador (nunca pasó por
     * llm_chat_logs, esa conversación de prueba no se persiste), y a
     * diferencia de evaluate() esto SÍ lanza si algo falla -- quien prueba
     * el prompt quiere ver el error, no que quede en silencio como en
     * producción.
     */
    public static function previewVerdict(array $history, int $disposition): array
    {
        $log = [];
        foreach ($history as $h) {
            $content = trim((string) ($h['content'] ?? ''));
            if ($content !== '') {
                $log[] = ['role' => ($h['role'] ?? '') === 'assistant' ? 'assistant' : 'user', 'content' => $content];
            }
        }
        if (!$log) {
            throw new RuntimeException('No hay conversación que evaluar todavía -- escribe al menos un mensaje.');
        }

        $raw = LlmChat::reply(LlmConfig::buildOirsPrompt($disposition), [], self::transcriptFromLog($log));
        $verdict = self::parseVerdict($raw);
        if ($verdict === null) {
            throw new RuntimeException('El LLM no devolvió un JSON válido: ' . $raw);
        }
        return $verdict;
    }

    private static function transcriptFromLog(array $log): string
    {
        $transcript = '';
        foreach ($log as $turn) {
            $who = $turn['role'] === 'assistant' ? 'Paciente' : 'Alumno';
            $transcript .= "{$who}: {$turn['content']}\n";
        }
        return $transcript;
    }

    private static function parseVerdict(string $raw): ?array
    {
        $clean = trim($raw);
        // El modelo a veces envuelve el JSON en ```json ... ``` pese a la
        // instrucción de no hacerlo -- se pela el fence si aparece.
        if (substr($clean, 0, 3) === '```') {
            $clean = preg_replace('/^```[a-zA-Z]*\n?|```$/', '', $clean);
            $clean = trim((string) $clean);
        }

        $data = json_decode($clean, true);
        if (!is_array($data)) {
            return null;
        }

        $veredicto = (string) ($data['veredicto'] ?? '');
        if (!in_array($veredicto, ['reclamo', 'merito', 'neutro'], true)) {
            return null;
        }

        return [
            'veredicto' => $veredicto,
            'asunto' => trim((string) ($data['asunto'] ?? '')),
            'cuerpo' => trim((string) ($data['cuerpo'] ?? '')),
        ];
    }
}
