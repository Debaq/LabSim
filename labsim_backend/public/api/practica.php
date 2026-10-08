<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Práctica deliberada desde la app (ver src/Practica.php).
 *
 * GET  -> {items: [...]}: los pacientes de práctica de los cursos del
 *         alumno, con sus intentos y el que tenga abierto.
 * POST {action: "iniciar", id: <practice_cases.id>} -> {appointment}: la
 *         cita del intento (la abierta, o una nueva). La app la atiende
 *         con el mismo camino de cualquier cita.
 */

$user = Auth::requireUser();

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    Response::json(['items' => Practica::paraAlumno((int) $user['id'])]);
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
