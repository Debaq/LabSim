<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Tickets.php';

/**
 * Reporte de problema desde la app (Configuración → Reportar un problema).
 * multipart/form-data:
 *   descripcion (texto, opcional), equipo (JSON, el bloque del login),
 *   detalle (JSON, pares texto), acepta ('1': el usuario aceptó mandar
 *   esto), log (archivo gzip con el registro de la app, opcional).
 *
 * Responde {id}: el número de ticket que se le muestra al usuario.
 */

$user = Auth::requireUser();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    Response::error('Método no permitido.', 405);
}
// El cliente no deja enviar sin el consentimiento; acá se exige igual,
// para que ningún otro camino mande datos del equipo sin él.
if ((string) ($_POST['acepta'] ?? '') !== '1') {
    Response::error('Falta aceptar el envío de la información del equipo.', 400);
}
if (Tickets::excedeLimite((int) $user['id'])) {
    Response::error('Ya enviaste varios reportes en la última hora. Intenta más tarde.', 429);
}

$logGz = null;
if (isset($_FILES['log']) && $_FILES['log']['error'] !== UPLOAD_ERR_NO_FILE) {
    if ($_FILES['log']['error'] !== UPLOAD_ERR_OK) {
        Response::error("Error al subir el registro (código {$_FILES['log']['error']}).", 400);
    }
    if ((int) $_FILES['log']['size'] > Tickets::MAX_LOG_BYTES) {
        Response::error('El registro es demasiado grande.', 413);
    }
    $logGz = (string) file_get_contents($_FILES['log']['tmp_name']);
    if (!Tickets::esGzip($logGz)) {
        Response::error('El registro no viene comprimido (gzip).', 400);
    }
}

$id = Tickets::crear(
    (int) $user['id'],
    (string) ($_POST['descripcion'] ?? ''),
    json_decode((string) ($_POST['equipo'] ?? ''), true),
    json_decode((string) ($_POST['detalle'] ?? ''), true),
    $logGz
);

Response::json(['id' => $id]);
