<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Sala.php';

/**
 * Quiénes están en el box de un caso (ver Sala.php), para que la app pueda
 * armar el selector de "a quién le hablo" ANTES del primer mensaje.
 *
 * Sin esto el alumno tendría que mandar una pregunta al aire para recién
 * enterarse de que además del paciente hay una madre y un padre esperando
 * -- justamente lo que tiene que ver al entrar.
 *
 * Devuelve solo lo visible (quién es, si está presente, si habla). Los
 * rasgos -- cuánto interrumpe, cuánta conciencia tiene de su problema -- se
 * quedan en el servidor: son la respuesta del ejercicio.
 */

Auth::requireUser();

$caseId = trim((string) ($_GET['case_id'] ?? ''));
if ($caseId === '') {
    Response::error('Falta case_id.', 400);
}

$stmt = Db::get()->prepare('SELECT data FROM cases WHERE id = ?');
$stmt->execute([$caseId]);
$row = $stmt->fetch();
if (!$row) {
    Response::error('El caso no existe.', 404);
}
$caseData = json_decode((string) $row['data'], true) ?: [];

// nombre/edad del paciente no viven en el caso sino en la cita (mismo
// criterio que llm_chat.php), así que los manda el cliente.
$sala = Sala::desde(
    $caseData,
    trim((string) ($_GET['nombre'] ?? '')),
    (int) ($_GET['edad'] ?? 0)
);

Response::json([
    'sala' => Sala::paraCliente($sala),
    'aforo' => $sala['aforo'],
]);
