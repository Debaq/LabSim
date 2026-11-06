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

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    Response::error('Método no permitido.', 405);
}
// El cliente no deja enviar sin el consentimiento; acá se exige igual,
// para que ningún otro camino mande datos del equipo sin él.
if ((string) ($_POST['acepta'] ?? '') !== '1') {
    Response::error('Falta aceptar el envío de la información del equipo.', 400);
}

// Sin sesión se aceptan dos, sin usuario y con tope por equipo y global:
// - cierre inesperado (la app se cayó y al volver a abrir ofrece mandar el
//   registro, ver core/soporte.py): el registro vale más que saber quién era;
// - sin_sesion: el que se manda desde la ventana de ingreso cuando no se
//   puede entrar (2026-11-06: el servidor perdía paquetes y el equipo que
//   no conectaba era justo el que no podía reportar), o uno que quedó
//   guardado en el equipo y sale después (core/tickets_pendientes.py).
$cierreInesperado = (string) ($_POST['cierre_inesperado'] ?? '') === '1';
$sinSesion = (string) ($_POST['sin_sesion'] ?? '') === '1';
$equipoRaw = json_decode((string) ($_POST['equipo'] ?? ''), true);
$anonimo = ($cierreInesperado || $sinSesion) && trim((string) ($_SERVER['HTTP_AUTHORIZATION'] ?? '')) === '';
if ($anonimo) {
    $userId = null;
    $equipoId = (string) ((Equipos::normalizar($equipoRaw) ?? [])['id'] ?? '');
    if (Tickets::excedeLimiteAnonimo($equipoId)) {
        Response::error('Este equipo ya envió varios reportes en la última hora.', 429);
    }
} else {
    $user = Auth::requireUser();
    $userId = (int) $user['id'];
    if (Tickets::excedeLimite($userId)) {
        Response::error('Ya enviaste varios reportes en la última hora. Intenta más tarde.', 429);
    }
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

$descripcion = (string) ($_POST['descripcion'] ?? '');
if ($cierreInesperado) {
    $descripcion = trim('[Cierre inesperado] ' . $descripcion);
} elseif ($anonimo) {
    $descripcion = trim('[Sin sesión] ' . $descripcion);
}
$id = Tickets::crear(
    $userId,
    $descripcion,
    $equipoRaw,
    json_decode((string) ($_POST['detalle'] ?? ''), true),
    $logGz
);

Response::json(['id' => $id]);
