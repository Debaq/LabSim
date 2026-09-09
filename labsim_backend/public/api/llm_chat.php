<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/CaseBuilder.php';
require_once __DIR__ . '/../../src/LlmConfig.php';
require_once __DIR__ . '/../../src/LlmChat.php';
require_once __DIR__ . '/../../src/Sala.php';

/**
 * Chat real de la app (Ficha del paciente -> "Conversar con paciente"): el
 * alumno manda case_id + historial + mensaje, y acá se arma el system
 * prompt con la Anamnesis/Tinnitus/gender ya guardados en cases.data (no se
 * confía en el cliente para eso -- son los datos clínicos del caso). nombre/
 * edad/procedimiento sí vienen del cliente porque no viven en cases.data
 * (son de la cita, ver CaseBuilder::caseDataToForm) y son solo texto de
 * ambientación, no dato clínico.
 *
 * Desde el chat grupal (ver Sala.php) un turno puede tener más de una
 * respuesta: el destinatario y, a veces, quien lo interrumpe. Por eso
 * devuelve `respuestas` (lista) además de `reply`, que se mantiene con el
 * texto del primero que habla para no romper a un cliente viejo.
 *
 * El estado de la sala (quién salió del box, a quién se contuvo y por
 * cuántos turnos) viaja en el cuerpo y vuelve en la respuesta: este
 * endpoint no tiene sesión -- cada turno manda el historial completo -- y
 * darle una tabla solo para eso sería inventarle estado a algo que no lo
 * tiene.
 *
 * Si viene appointment_id, el turno (mensaje del alumno + cada respuesta)
 * queda guardado en llm_chat_logs contra esa cita + el alumno logueado,
 * con quién habló y a quién le habló el alumno. El "Atender (prueba)" del
 * admin no manda appointment_id a propósito -- esas pruebas no dejan rastro.
 */

$user = Auth::requireUser();

$body = json_decode(file_get_contents('php://input'), true);
if (!is_array($body)) {
    Response::error('JSON inválido.', 400);
}

$caseId = trim((string) ($body['case_id'] ?? ''));
$message = trim((string) ($body['message'] ?? ''));
$salidaSolicitada = trim((string) ($body['salida_solicitada'] ?? ''));

// Pedir que alguien salga del box es un turno por sí solo: no lleva
// mensaje, pero sí queda en el log porque es una decisión evaluable.
if ($caseId === '' || ($message === '' && $salidaSolicitada === '')) {
    Response::error('Falta case_id o message.', 400);
}

$appointmentId = isset($body['appointment_id']) ? (int) $body['appointment_id'] : 0;

if (!LlmConfig::get()['active']) {
    Response::error('El chat con el paciente no está habilitado (Admin -> IA Paciente).', 503);
}

$stmt = Db::get()->prepare('SELECT data FROM cases WHERE id = ?');
$stmt->execute([$caseId]);
$row = $stmt->fetch();
if (!$row) {
    Response::error('El caso no existe.', 404);
}
$caseData = json_decode((string) $row['data'], true) ?: [];

$nombrePaciente = trim((string) ($body['nombre'] ?? ''));
$edadPaciente = (int) ($body['edad'] ?? 0);
$sala = Sala::desde($caseData, $nombrePaciente, $edadPaciente);

// Quiénes quedaron fuera del box. El cliente manda la lista completa en
// cada turno (no un delta) para que reabrir el chat no arrastre un estado
// a medias; acá se ignora a quien no se puede echar.
$avisos = [];
$fuera = array_map('strval', (array) ($body['fuera'] ?? []));
if ($salidaSolicitada !== '') {
    $fuera[] = $salidaSolicitada;
}
foreach ($sala['personas'] as $k => $p) {
    if (!in_array($p['id'], $fuera, true)) {
        continue;
    }
    if ($p['obligatorio']) {
        // Regla dura, no preferencia: al padre o la madre de un menor no se
        // les puede impedir estar presentes, y el paciente obviamente se
        // queda. Se avisa y se sigue con esa persona adentro.
        if ($p['id'] === $salidaSolicitada) {
            $avisos[] = $p['es_paciente']
                ? 'El paciente no puede salir del box.'
                : Sala::etiqueta($p) . ' no puede quedar fuera: un padre o una madre tiene derecho a acompañar a su hijo.';
        }
        continue;
    }
    $sala['personas'][$k]['presente'] = false;
}

$ctx = [
    'paciente_nombre' => $nombrePaciente !== '' ? $nombrePaciente : 'el paciente',
    'paciente_edad' => $edadPaciente > 0 ? $edadPaciente : (int) ($caseData['edad'] ?? 0),
    'paciente_genero' => (int) ($caseData['gender'] ?? 0),
    'procedimiento' => (string) ($body['procedimiento'] ?? ''),
    'anamnesis' => [
        'antecedentes' => (array) ($caseData['Anamnesis']['antecedentes'] ?? []),
        'medicamentos' => (string) ($caseData['Anamnesis']['medicamentos'] ?? ''),
        'cirugias' => (string) ($caseData['Anamnesis']['cirugias'] ?? ''),
        'otros' => (string) ($caseData['Anamnesis']['otros'] ?? ''),
    ],
    'tinnitus' => (array) ($caseData['Tinnitus'] ?? []),
];

$logStmt = null;
if ($appointmentId > 0) {
    Db::migrateSalaIfNeeded();
    $logStmt = Db::get()->prepare(
        'INSERT INTO llm_chat_logs (appointment_id, student_id, case_id, role, content, speaker_id, speaker_label, addressed_to)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
    );
}

// Sacar a alguien del box no llama al LLM: es una acción sobre la sala.
if ($message === '') {
    $quien = Sala::persona($sala, $salidaSolicitada);
    if ($logStmt !== null && $quien !== null) {
        $logStmt->execute([
            $appointmentId, $user['id'], $caseId, 'user',
            'Le pide salir del box a ' . Sala::etiqueta($quien),
            '', '', $salidaSolicitada,
        ]);
    }
    Response::json([
        'reply' => '',
        'respuestas' => [],
        'sala' => Sala::paraCliente($sala),
        'silenciados' => (array) ($body['silenciados'] ?? []),
        'avisos' => $avisos,
    ]);
}

$dirigidoA = trim((string) ($body['dirigido_a'] ?? ''));
$silenciados = [];
foreach ((array) ($body['silenciados'] ?? []) as $id => $turnos) {
    $silenciados[(string) $id] = (int) $turnos;
}

$turno = Sala::turno($sala, $dirigidoA, $message, $silenciados);
if (!$turno['hablan']) {
    Response::error('No queda nadie en el box a quien preguntarle.', 409);
}

// El historial va rotulado con quién dijo cada cosa: con más de una
// persona en la sala, un "assistant" pelado no le dice al modelo si eso lo
// dijo el paciente o la madre, y las respuestas empiezan a mezclarse.
$history = [];
foreach ((array) ($body['history'] ?? []) as $h) {
    $content = trim((string) ($h['content'] ?? ''));
    if ($content === '') {
        continue;
    }
    $esAlumno = ($h['role'] ?? '') !== 'assistant';
    $label = trim((string) ($h['speaker_label'] ?? ''));
    $history[] = [
        'role' => $esAlumno ? 'user' : 'assistant',
        'content' => (!$esAlumno && $label !== '') ? "{$label}: {$content}" : $content,
    ];
}

// A quién le habló el alumno, dicho en el propio mensaje: es la señal que
// hace que un acompañante sepa que la pregunta no era para él.
$destinatario = $turno['destinatario'];
$mensajeConDestino = $message;
if ($destinatario !== null && $dirigidoA !== '' && $dirigidoA !== 'sala') {
    $mensajeConDestino = '(le pregunta a ' . Sala::etiqueta($destinatario) . ') ' . $message;
}

$respuestas = [];
foreach ($turno['hablan'] as $quienHabla) {
    $persona = $quienHabla['persona'];
    $prompt = LlmConfig::buildPersonaPrompt($persona, $sala, $ctx, $quienHabla['motivo']);
    try {
        $texto = LlmChat::reply($prompt, $history, $mensajeConDestino);
    } catch (Throwable $e) {
        // Si ya contestó alguien, el turno no se pierde por culpa del que
        // venía a interrumpir: se devuelve lo que sí salió.
        if ($respuestas) {
            break;
        }
        Response::error($e->getMessage(), 502);
    }
    $etiqueta = Sala::etiqueta($persona);
    $respuestas[] = [
        'persona_id' => $persona['id'],
        'etiqueta' => $etiqueta,
        'motivo' => $quienHabla['motivo'],
        'texto' => $texto,
    ];
    // El que interrumpe tiene que ver lo que acaba de decir el otro: sin
    // esto, la madre "corrige" algo que en su historial nunca se dijo.
    $history[] = ['role' => 'assistant', 'content' => "{$etiqueta}: {$texto}"];
}

if ($logStmt !== null) {
    $logStmt->execute([
        $appointmentId, $user['id'], $caseId, 'user', $message, '', '',
        $destinatario !== null ? $destinatario['id'] : '',
    ]);
    foreach ($respuestas as $r) {
        $logStmt->execute([
            $appointmentId, $user['id'], $caseId, 'assistant', $r['texto'],
            $r['persona_id'], $r['etiqueta'], '',
        ]);
    }
}

Response::json([
    // `reply` es el texto del primero que habla: lo que espera un cliente
    // anterior al chat grupal, que solo sabe leer una respuesta.
    'reply' => $respuestas ? $respuestas[0]['texto'] : '',
    'respuestas' => $respuestas,
    'sala' => Sala::paraCliente($sala),
    'silenciados' => $turno['silenciados'],
    'tipo_pregunta' => $turno['tipo'],
    'avisos' => $avisos,
]);
