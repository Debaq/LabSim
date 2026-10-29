<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Práctica libre desde la app (ver src/Practica.php): los pacientes del
 * libro en carpetas, los mismos para todos.
 *
 * GET  -> {carpetas: [{id, nombre, orden, items: [...]}], items: [...]}:
 *         al alumno, con sus intentos y el que tenga abierto; al docente,
 *         con los intentos de todos los alumnos. `items` es la misma lista
 *         sin carpetas, para las apps de antes de las carpetas.
 * POST {action: "iniciar", id: <practice_items.id>} -> {appointment}: la
 *         cita del intento (la abierta, o una nueva). La app la atiende
 *         con el mismo camino de cualquier cita.
 */

$user = Auth::requireUser();

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    $carpetas = Practica::lista((int) $user['id'], $user['role'] === 'admin');
    $items = [];
    foreach ($carpetas as $c) {
        foreach ($c['items'] as $it) {
            $items[] = $it;
        }
    }
    Response::json(['carpetas' => $carpetas, 'items' => $items]);
}

$body = json_decode(file_get_contents('php://input'), true) ?? [];
$action = (string) ($body['action'] ?? '');
$itemId = (int) ($body['id'] ?? 0);

if ($action !== 'iniciar') {
    Response::error('Acción no soportada', 400);
}
if ($itemId <= 0) {
    Response::error('Falta id del paciente de práctica', 400);
}

try {
    $appointment = Practica::iniciar((int) $user['id'], $itemId);
} catch (RuntimeException $e) {
    Response::error($e->getMessage(), 409);
}
Response::json(['appointment' => $appointment]);
