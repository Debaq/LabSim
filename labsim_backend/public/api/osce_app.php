<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/OsceApp.php';
require_once __DIR__ . '/../../src/OscePreguntas.php';

/**
 * API de la app LabSim en modo "Estación OSCE" (paso 4 de
 * docs/osce_plan.md). Sin sesión: el PC se identifica con el código corto de
 * la estación y el alumno con el suyo; solo deja trabajar en la ventana de
 * tiempo del alumno en esa estación para entrar (OscePreguntas::motivoNoPuede,
 * la misma regla que la tablet de preguntas). Nunca devuelve lo esperado.
 *
 * Cuerpo JSON (POST):
 *   {"accion": "estacion", "estacion": "K7F-3QM"}
 *   {"accion": "entrar",   "estacion": ..., "codigo": "T24-TFJ"}
 *   {"accion": "entregar", "estacion": ..., "codigo": ..., "entrega": {...}}
 */

header('Cache-Control: no-store');

$body = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($body)) {
    $body = $_POST;
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
        'lista' => !empty($cfg['case_id']),
    ]);
}

$p = Osce::participantePorCodigo((int) $o['id'], (string) ($body['codigo'] ?? ''));
if ($p === null) {
    Response::error('Código no encontrado. Revisa tu tarjeta.', 404);
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

$estaciones = Osce::estaciones((int) $o['id']);
$indice = (int) array_search((int) $est['id'], array_map('intval', array_column($estaciones, 'id')), true);
$reloj = Osce::cfgReloj($o, count($estaciones), count(Osce::participantes((int) $o['id'])));

if ($accion === 'entrar') {
    $caso = OsceApp::caso((string) ($cfg['case_id'] ?? ''));
    if ($caso === null) {
        Response::error('La estación no tiene paciente configurado. Avisa al docente.', 409);
    }
    Response::json([
        'ok' => true,
        'codigo' => $p['codigo'],
        'tipo' => $est['tipo'],
        'prueba' => $cfg['prueba'] ?? 'ABR',
        'curvas' => $est['tipo'] === 'marcaje' ? ($cfg['curvas'] ?? []) : [],
        'ventana' => Osce::ventana($reloj, $p, $indice),
        'caso' => $caso,
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
