<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/CaseBuilder.php';
require_once __DIR__ . '/../../src/LlmConfig.php';
require_once __DIR__ . '/../../src/LlmChat.php';

/**
 * AJAX de case_create.php: deja al admin/docente conversar con el paciente
 * mientras arma la ficha, ANTES de guardarla -- por eso recibe los datos
 * crudos del formulario (no un case_id) y arma el prompt al vuelo con
 * LlmConfig::buildSystemPrompt(), igual que hará más adelante el chat real
 * de la app con los datos ya guardados en cases.data.
 */

$me = Auth::requireAdminSession(); // mismo nivel que case_create.php (admin completo o docente)

$raw = file_get_contents('php://input');
$body = json_decode($raw, true);
if (!is_array($body)) {
    Response::error('JSON inválido.', 400);
}

$sentCsrf = (string) ($body['csrf_token'] ?? '');
if (!hash_equals((string) ($_SESSION['csrf_token'] ?? ''), $sentCsrf)) {
    Response::error('Token CSRF inválido -- recarga la página.', 403);
}

$message = trim((string) ($body['message'] ?? ''));
if ($message === '') {
    Response::error('Falta el mensaje.', 400);
}

$antecedentes = [];
foreach (CaseBuilder::HIST_CHECKBOXES as $key) {
    $antecedentes[$key] = !empty($body['antecedentes'][$key]);
}

$systemPrompt = LlmConfig::buildSystemPrompt(
    [
        'nombre' => (string) ($body['nombre'] ?? ''),
        'edad' => (string) ($body['edad'] ?? ''),
        'genero' => (string) ($body['genero'] ?? '0'),
        'procedimiento' => (string) ($body['procedimiento'] ?? ''),
    ],
    [
        'antecedentes' => $antecedentes,
        'medicamentos' => (string) ($body['medicamentos'] ?? ''),
        'cirugias' => (string) ($body['cirugias'] ?? ''),
        'otros' => (string) ($body['otros'] ?? ''),
        'comportamiento' => (string) ($body['comportamiento'] ?? ''),
        'disposicion' => (int) ($body['disposicion'] ?? 0),
    ],
    (array) ($body['tinnitus'] ?? [])
);

$history = [];
foreach ((array) ($body['history'] ?? []) as $h) {
    $content = trim((string) ($h['content'] ?? ''));
    if ($content !== '') {
        $history[] = ['role' => ($h['role'] ?? '') === 'assistant' ? 'assistant' : 'user', 'content' => $content];
    }
}

try {
    $reply = LlmChat::reply($systemPrompt, $history, $message);
    Response::json(['reply' => $reply]);
} catch (Throwable $e) {
    Response::error($e->getMessage(), 502);
}
