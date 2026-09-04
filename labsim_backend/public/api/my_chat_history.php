<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Conversación con el paciente simulado (llm_chat_logs) de una atención
 * propia, más la retroalimentación que el docente haya dejado turno a
 * turno (chat_comments) -- misma información que ve el docente en
 * admin/chat_detail.php, pero solo lectura y scopeada al propio alumno vía
 * token (nunca puede pedir la conversación de otro).
 *
 * GET ?appointment_id=N
 */

$user = Auth::requireUser();
$pdo = Db::get();

$appointmentId = (int) ($_GET['appointment_id'] ?? 0);
if ($appointmentId <= 0) {
    Response::error('Falta appointment_id', 400);
}

$stmt = $pdo->prepare(
    'SELECT id, role, content, created_at FROM llm_chat_logs
     WHERE appointment_id = ? AND student_id = ? ORDER BY id'
);
$stmt->execute([$appointmentId, $user['id']]);
$log = $stmt->fetchAll();

$comments = [];
if ($log) {
    $logIds = array_column($log, 'id');
    $placeholders = implode(',', array_fill(0, count($logIds), '?'));
    $stmt = $pdo->prepare(
        "SELECT c.chat_log_id, c.comment, c.created_at, u.display_name AS teacher_name
         FROM chat_comments c
         JOIN users u ON u.id = c.teacher_id
         WHERE c.chat_log_id IN ($placeholders)
         ORDER BY c.id"
    );
    $stmt->execute($logIds);
    foreach ($stmt->fetchAll() as $c) {
        $comments[(int) $c['chat_log_id']][] = $c;
    }
}

$items = [];
foreach ($log as $turn) {
    $items[] = [
        'id' => (int) $turn['id'],
        'role' => $turn['role'],
        'content' => $turn['content'],
        'created_at' => $turn['created_at'],
        'comments' => $comments[(int) $turn['id']] ?? [],
    ];
}

Response::json(['items' => $items]);
