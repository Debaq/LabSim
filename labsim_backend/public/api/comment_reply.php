<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Feedback al feedback desde la app: el alumno responde un comentario que
 * su docente dejó sobre una atención propia (ver ComentarioRespuestas y
 * core/mis_pacientes.py).
 *
 * POST {comment_id, texto} -> {ok, respuestas: [hilo completo del comentario]}
 *
 * Solo en comentarios de atenciones del propio alumno (deAlumno): un
 * comment_id ajeno responde 404, igual que uno que no existe.
 */

$user = Auth::requireUser();
$pdo = Db::get();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    Response::error('Método no soportado', 405);
}
if (!ComentarioRespuestas::listo($pdo)) {
    Response::error('Las respuestas a comentarios todavía no están habilitadas en el servidor.', 503);
}

$body = json_decode(file_get_contents('php://input'), true) ?? [];
$commentId = (int) ($body['comment_id'] ?? 0);
$texto = (string) ($body['texto'] ?? '');

if (!ComentarioRespuestas::deAlumno($pdo, $commentId, (int) $user['id'])) {
    Response::error('Comentario no encontrado', 404);
}
if (ComentarioRespuestas::limpiar($texto) === null) {
    Response::error('La respuesta está vacía', 400);
}

ComentarioRespuestas::responder($pdo, $commentId, (int) $user['id'], 'alumno', $texto);

Response::json([
    'ok' => true,
    'respuestas' => ComentarioRespuestas::porComentario($pdo, [$commentId])[$commentId] ?? [],
]);
