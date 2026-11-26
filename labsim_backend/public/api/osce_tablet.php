<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/OscePreguntas.php';

/**
 * API de la tablet de una estación de preguntas del OSCE
 * (student/osce_estacion.php). Sin sesión: la tablet se identifica con el
 * token de la estación (?k=) y el alumno con su número. Solo deja trabajar
 * a quien le toca la estación en el turno en curso (Osce::motivoNoToca), con
 * su propio tiempo desde que confirma su nombre, y nunca devuelve la clave
 * ni la pauta.
 *
 * GET  k                                  estación + token del reloj
 * POST k, accion=entrar, codigo           nombre de la tarjeta (para confirmar)
 * POST k, accion=confirmar, codigo        parte su tiempo: preguntas (barajadas) y lo ya respondido
 * POST k, accion=guardar, codigo, respuestas (JSON), entregar
 * POST k, accion=corregir, codigo         corrige con IA lo de desarrollo (tras entregar)
 */

header('Cache-Control: no-store');

$k = (string) ($_GET['k'] ?? $_POST['k'] ?? '');
$est = OscePreguntas::estacionPorToken($k);
$o = $est !== null ? Osce::obtener((int) $est['osce_id']) : null;
if ($est === null || $o === null || $est['tipo'] !== 'preguntas') {
    Response::error('Estación no encontrada.', 404);
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    Response::json([
        'estacion' => $est['titulo'],
        'osce' => $o['nombre'],
        'reloj' => $o['reloj_token'],
    ]);
}

$accion = (string) ($_POST['accion'] ?? '');
$p = Osce::participantePorCodigo((int) $o['id'], (string) ($_POST['codigo'] ?? ''));
if ($p === null) {
    Response::error('Número no encontrado. Revisa tu tarjeta.', 404);
}

if ($accion === 'corregir') {
    // La tablet la llama sin esperar respuesta: que siga aunque se corte.
    ignore_user_abort(true);
    @set_time_limit(300);
    $hechas = 0;
    $fallas = 0;
    foreach (OscePreguntas::pendientesIa((int) $est['id'], (int) $p['id']) as $rid) {
        try {
            OscePreguntas::corregirIa($rid);
            $hechas++;
        } catch (Throwable $e) {
            $fallas++;
            error_log('[osce_tablet corregir] ' . $e->getMessage());
        }
    }
    Response::json(['ok' => true, 'corregidas' => $hechas, 'fallas' => $fallas]);
}

$motivo = OscePreguntas::motivoNoPuede($o, $est, $p);
if ($motivo !== null) {
    Response::error($motivo, 409);
}

if ($accion === 'entrar') {
    if ($p['user_id'] === null) {
        Response::error('Tu tarjeta aún no tiene tu nombre: escanea el QR de tu gafete o avisa al docente.', 409);
    }
    Response::json([
        'ok' => true,
        'codigo' => $p['codigo'],
        'numero' => (int) $p['numero'],
        'nombre' => (string) $p['display_name'],
    ]);
}

if ($accion === 'confirmar') {
    if ($p['user_id'] === null) {
        Response::error('Tu tarjeta aún no tiene tu nombre: avisa al docente.', 409);
    }
    Response::json([
        'ok' => true,
        'codigo' => $p['codigo'],
        'numero' => (int) $p['numero'],
        'ventana' => Osce::iniciarReloj($o, (int) $p['id'], (int) $est['id']),
        'preguntas' => OscePreguntas::paraAlumno($est, $p),
    ]);
}

if ($accion === 'guardar') {
    $respuestas = json_decode((string) ($_POST['respuestas'] ?? '{}'), true);
    $r = OscePreguntas::guardarRespuestas((int) $est['id'], (int) $p['id'], is_array($respuestas) ? $respuestas : [],
                                          !empty($_POST['entregar']));
    Response::json(['ok' => true] + $r);
}

Response::error('Acción desconocida.', 400);
