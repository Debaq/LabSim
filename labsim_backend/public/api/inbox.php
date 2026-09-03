<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Bandeja de entrada del alumno logueado: mensajes de dos orígenes (ver
 * inbox_messages en sql/schema.sql) -- avisos automáticos que OirsEvaluator
 * dejó al cerrar una atención (attendance_action.php), y mensajes que un
 * docente mandó a mano (admin/inbox_send.php). Cada alumno solo ve los
 * suyos -- nunca los de otro (a diferencia de attendances, esto no es algo
 * que el docente necesite ver por fila; el resumen para el docente vive en
 * admin/student.php).
 *
 * GET  -> lista los mensajes del alumno (más nuevos primero).
 * POST {action:'mark_read', id} -> marca uno como leído.
 */

$user = Auth::requireUser();
$pdo = Db::get();

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $body = json_decode(file_get_contents('php://input'), true) ?? [];
    if (($body['action'] ?? '') !== 'mark_read') {
        Response::error('Acción no soportada', 400);
    }
    $id = (int) ($body['id'] ?? 0);
    $stmt = $pdo->prepare('UPDATE inbox_messages SET leido = 1 WHERE id = ? AND student_id = ?');
    $stmt->execute([$id, $user['id']]);
    Response::json(['ok' => true]);
}

$stmt = $pdo->prepare(
    "SELECT m.id, m.appointment_id, m.tipo, m.remitente, m.asunto, m.cuerpo, m.leido, m.created_at,
            a.fecha, a.hora, a.procedimiento
     FROM inbox_messages m
     LEFT JOIN appointments a ON a.id = m.appointment_id
     WHERE m.student_id = ?
     ORDER BY m.created_at DESC"
);
$stmt->execute([$user['id']]);
Response::json(['items' => $stmt->fetchAll()]);
