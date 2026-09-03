<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/LlmConfig.php';
require_once __DIR__ . '/../../src/LlmChat.php';
require_once __DIR__ . '/../../src/OirsEvaluator.php';

/**
 * AJAX de case_create.php: "Simular término de sesión" en la tarjeta de
 * prueba del chat -- corre el evaluador OIRS (ver OirsEvaluator.php) sobre
 * la conversación de prueba que ya tiene el JS del navegador (nunca se
 * guardó en llm_chat_logs), para ver qué veredicto y aviso generaría al
 * cerrar una atención real, mientras se ajusta el prompt del paciente o del
 * evaluador. No escribe nada en inbox_messages.
 */

$me = Auth::requireAdminSession();

$raw = file_get_contents('php://input');
$body = json_decode($raw, true);
if (!is_array($body)) {
    Response::error('JSON inválido.', 400);
}

$sentCsrf = (string) ($body['csrf_token'] ?? '');
if (!hash_equals((string) ($_SESSION['csrf_token'] ?? ''), $sentCsrf)) {
    Response::error('Token CSRF inválido -- recarga la página.', 403);
}

$history = (array) ($body['history'] ?? []);
$disposicion = (int) ($body['disposicion'] ?? 0);

try {
    $verdict = OirsEvaluator::previewVerdict($history, $disposicion);
    Response::json($verdict);
} catch (Throwable $e) {
    Response::error($e->getMessage(), 502);
}
