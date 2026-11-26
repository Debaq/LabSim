<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/OsceApp.php';
require_once __DIR__ . '/../../src/OscePreguntas.php';

/**
 * API de la app LabSim en modo "Estación OSCE" (paso 4 de
 * docs/osce_plan.md). El PC se identifica con el código corto de la
 * estación, que solo se entrega a un docente con su usuario y contraseña
 * ("estaciones"); el alumno con su número. Solo deja entrar a quien le toca
 * esa estación en el turno en curso (Osce::motivoNoToca, la misma regla que
 * las tablets). Entrar es en dos pasos: con el número se muestra el nombre
 * y al confirmarlo ("confirmar") parte su tiempo. Nunca devuelve lo esperado.
 *
 * Cuerpo JSON (POST):
 *   {"accion": "estaciones", "usuario": ..., "clave": ...}   (docente: OSCE y estaciones de la app)
 *   {"accion": "estacion",  "estacion": "K7F-3QM"}
 *   {"accion": "entrar",    "estacion": ..., "codigo": "7"}       -> nombre de la tarjeta
 *   {"accion": "confirmar", "estacion": ..., "codigo": "7"}       -> casos y su tiempo
 *   {"accion": "entregar",  "estacion": ..., "codigo": ..., "entrega": {...}}
 *   {"accion": "corregir",  "estacion": ..., "codigo": ...}   (conclusión: IA)
 */

header('Cache-Control: no-store');

$body = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($body)) {
    $body = $_POST;
}
if (($body['accion'] ?? '') === 'estaciones') {
    // El docente deja el PC como estación: con su clave (como al entrar a la
    // app) se le listan los OSCE de sus cursos y sus estaciones de la app.
    $usuario = trim((string) ($body['usuario'] ?? ''));
    $ip = (string) ($_SERVER['REMOTE_ADDR'] ?? 'unknown');
    if ($usuario === '' || (string) ($body['clave'] ?? '') === '') {
        Response::error('Falta usuario o contraseña.', 400);
    }
    if (Auth::loginBlocked($usuario, $ip)) {
        Response::error('Demasiados intentos fallidos. Espera unos minutos.', 429);
    }
    $docente = OsceApp::docentePorClave($usuario, (string) $body['clave']);
    Auth::recordLoginAttempt($usuario, $ip, $docente !== null);
    if ($docente === null) {
        Response::error('Usuario o contraseña incorrectos (docente o admin).', 401);
    }
    Response::json(['ok' => true, 'osces' => OsceApp::estacionesDelDocente($docente)]);
}

$est = OsceApp::estacionPorCodigo((string) ($body['estacion'] ?? ''));
$o = $est !== null ? Osce::obtener((int) $est['osce_id']) : null;
if ($est === null || $o === null || !OsceApp::esApp((string) $est['tipo'])) {
    Response::error('Estación no encontrada. Revisa el código de la estación.', 404);
}
$cfg = OsceApp::config($est);
$accion = (string) ($body['accion'] ?? '');

if ($accion === 'estacion') {
    Response::json([
        'ok' => true,
        'titulo' => $est['titulo'],
        'tipo' => $est['tipo'],
        'osce' => $o['nombre'],
        'reloj' => $o['reloj_token'],
        'modulo' => OsceApp::modulos($est)[0],
        'modulos' => OsceApp::modulos($est),
        'lista' => OsceApp::tareas($est) !== [],
    ]);
}

$p = Osce::participantePorCodigo((int) $o['id'], (string) ($body['codigo'] ?? ''));
if ($p === null) {
    Response::error('Número no encontrado. Revisa tu tarjeta.', 404);
}
if ($accion === 'corregir') {
    // La app la llama después de entregar, sin esperar: la IA corrige la
    // conclusión en el servidor aunque la app ya pasó al alumno siguiente.
    ignore_user_abort(true);
    @set_time_limit(300);
    if (!in_array((int) $p['id'], OsceApp::pendientesIa((int) $est['id']), true)) {
        Response::json(['ok' => true, 'corregida' => false]);
    }
    try {
        OsceApp::corregirIa((int) $est['id'], (int) $p['id']);
    } catch (Throwable $e) {
        error_log('[osce_app corregir] ' . $e->getMessage());
        Response::json(['ok' => true, 'corregida' => false]);
    }
    Response::json(['ok' => true, 'corregida' => true]);
}

// Entrar exige la ventana del reloj. Entregar no: si se cortó la red, la app
// reintenta después y lo hecho no se puede perder (una sola entrega por
// alumno y estación, y nunca con los resultados ya publicados).
if ($accion === 'entregar') {
    if (!in_array($o['estado'], ['en_curso', 'cerrado'], true)) {
        Response::error('El OSCE no está recibiendo entregas.', 409);
    }
} else {
    $motivo = OscePreguntas::motivoNoPuede($o, $est, $p);
    if ($motivo !== null) {
        Response::error($motivo, 409);
    }
}

if ($accion === 'entrar') {
    // Primer paso: el alumno ve su nombre y confirma que es él. Aún no corre su tiempo.
    if ($p['user_id'] === null) {
        Response::error('Tu tarjeta aún no tiene tu nombre: escanea el QR de tu gafete o avisa al docente.', 409);
    }
    Response::json([
        'ok' => true,
        'codigo' => $p['codigo'],
        'numero' => (int) $p['numero'],
        'nombre' => (string) $p['display_name'],
        'partio' => Osce::ventanaReal($o, (int) $p['id'], (int) $est['id']) !== null,
    ]);
}

if ($accion === 'confirmar') {
    if ($p['user_id'] === null) {
        Response::error('Tu tarjeta aún no tiene tu nombre: avisa al docente.', 409);
    }
    try {
        $tareas = OsceApp::tareasParaAlumno($est, (int) $p['numero']);
    } catch (InvalidArgumentException $e) {
        Response::error($e->getMessage(), 409);
    }
    if (!$tareas) {
        Response::error('La estación no tiene paciente configurado. Avisa al docente.', 409);
    }
    // Su tiempo parte ahora (o sigue el que ya tenía si vuelve a entrar).
    $ventana = Osce::iniciarReloj($o, (int) $p['id'], (int) $est['id']);
    // Arriba, la primera tarea suelta (como una estación de un solo caso).
    $t0 = $tareas[0];
    Response::json([
        'ok' => true,
        'codigo' => $p['codigo'],
        'numero' => (int) $p['numero'],
        'tipo' => $est['tipo'],
        'modulo' => $t0['modulo'],
        'prueba' => $t0['prueba'],
        'curvas' => $t0['curvas'],
        'caso' => $t0['caso'],
        'tareas' => $tareas,
        'ventana' => $ventana,
    ]);
}

if ($accion === 'entregar') {
    $entrega = $body['entrega'] ?? null;
    if (!is_array($entrega)) {
        Response::error('Entrega vacía.', 400);
    }
    try {
        $r = OsceApp::entregar((int) $est['id'], (int) $p['id'], $entrega);
    } catch (InvalidArgumentException $e) {
        Response::error($e->getMessage(), 409);
    }
    // Al alumno no se le dice el puntaje: lo verá publicado.
    Response::json(['ok' => true]);
}

Response::error('Acción desconocida.', 400);
