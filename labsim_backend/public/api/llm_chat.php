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
 * Dos modos, según el caso:
 *
 * - Paciente solo (la mayoría, y todos los casos anteriores a Sala.php):
 *   una llamada con el prompt del paciente de siempre y respuesta en texto
 *   plano. No cambió nada.
 * - Paciente acompañado: una llamada con el prompt de la sala, donde el
 *   modelo interpreta a todos y devuelve en JSON quién habló y qué dijo
 *   (ver LlmConfig::buildSalaPrompt). Un turno puede traer más de una
 *   intervención -- el paciente que minimiza y la esposa que lo desmiente
 *   son dos burbujas, con dos caras distintas.
 *
 * Quién contesta NO se decide acá: lo decide el modelo leyendo el mensaje.
 * "Mamita, ¿su hijo escucha bien?" lo contesta la madre porque la frase lo
 * dice, y eso ningún clasificador de palabras clave lo hace bien.
 *
 * Si viene appointment_id, el turno (mensaje del alumno + cada
 * intervención, con quién la dijo) queda guardado en llm_chat_logs contra
 * esa cita + el alumno logueado. El "Atender (prueba)" del admin no manda
 * appointment_id a propósito -- esas pruebas no dejan rastro.
 */

$user = Auth::requireUser();

$body = json_decode(file_get_contents('php://input'), true);
if (!is_array($body)) {
    Response::error('JSON inválido.', 400);
}

$caseId = trim((string) ($body['case_id'] ?? ''));
$message = trim((string) ($body['message'] ?? ''));
if ($caseId === '' || $message === '') {
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
$procedimiento = (string) ($body['procedimiento'] ?? '');
$sala = Sala::desde($caseData, $nombrePaciente, $edadPaciente);
$acompanado = Sala::tieneAcompanantes($sala);

$anamnesis = [
    'antecedentes' => (array) ($caseData['Anamnesis']['antecedentes'] ?? []),
    'medicamentos' => (string) ($caseData['Anamnesis']['medicamentos'] ?? ''),
    'cirugias' => (string) ($caseData['Anamnesis']['cirugias'] ?? ''),
    'otros' => (string) ($caseData['Anamnesis']['otros'] ?? ''),
];
$tinnitus = (array) ($caseData['Tinnitus'] ?? []);

if ($acompanado) {
    $systemPrompt = LlmConfig::buildSalaPrompt($sala, [
        'procedimiento' => $procedimiento,
        'anamnesis' => $anamnesis,
        'tinnitus' => $tinnitus,
    ]);
} else {
    $systemPrompt = LlmConfig::buildSystemPrompt(
        [
            'nombre' => $nombrePaciente,
            'edad' => (string) $edadPaciente,
            'genero' => (string) ($caseData['gender'] ?? '0'),
            'procedimiento' => $procedimiento,
        ],
        $anamnesis + [
            'comportamiento' => (string) ($caseData['PatientBehavior'] ?? ''),
            'disposicion' => (int) ($caseData['PatientDisposition'] ?? 0),
        ],
        $tinnitus
    );
}

// El historial va rotulado con quién dijo cada cosa: con más de una persona
// en la consulta, un "assistant" pelado no le dice al modelo si eso lo dijo
// el paciente o la madre, y las voces empiezan a mezclarse.
//
// Con acompañantes se le devuelve EN EL MISMO JSON que se le pide escribir.
// Antes se le devolvía como "Sofía García (Madre): buenas tardes", y el
// modelo copiaba ese formato: contestaba con el nombre pegado adelante del
// texto y sin el id, así que la frase quedaba sin dueño y se le atribuía a
// quien lleva la voz cantante. El historial es el ejemplo más fuerte que
// tiene: si ahí ve ids, escribe ids.
$history = [];
foreach ((array) ($body['history'] ?? []) as $h) {
    $content = trim((string) ($h['content'] ?? ''));
    if ($content === '') {
        continue;
    }
    $esAlumno = ($h['role'] ?? '') !== 'assistant';
    if ($esAlumno || !$acompanado) {
        $history[] = ['role' => $esAlumno ? 'user' : 'assistant', 'content' => $content];
        continue;
    }

    // El cliente manda speaker_id desde que existe la sala; los historiales
    // que solo traen la etiqueta ("Sofía García (Madre)") se resuelven igual.
    $persona = Sala::persona($sala, trim((string) ($h['speaker_id'] ?? '')))
        ?? Sala::resolver($sala, (string) ($h['speaker_label'] ?? ''))
        ?? Sala::informante($sala);
    [, $content] = Sala::separaRotulo($sala, $content);
    $history[] = [
        'role' => 'assistant',
        'content' => json_encode(
            ['turnos' => [['id' => $persona['id'] ?? '', 'texto' => $content]]],
            JSON_UNESCAPED_UNICODE
        ),
    ];
}

// Curso al que se le imputa el consumo (ver LlmUsage). Solo con cita real:
// el "Atender (prueba)" del admin no manda appointment_id, y esa llamada no
// pertenece a ningún curso. La columna es de una migración posterior, así
// que un backend sin aplicar todavía el schema queda sin curso, no roto.
$courseId = 0;
if ($appointmentId > 0) {
    try {
        $cStmt = Db::get()->prepare('SELECT course_id FROM appointments WHERE id = ?');
        $cStmt->execute([$appointmentId]);
        $cRow = $cStmt->fetch();
        $courseId = $cRow ? (int) ($cRow['course_id'] ?? 0) : 0;
    } catch (Throwable $e) {
        $courseId = 0;
    }
}

try {
    $raw = LlmChat::reply($systemPrompt, $history, $message, [
        // Se separan porque cuestan distinto: el prompt de la sala describe
        // a cada persona presente y pide JSON, así que arranca bastante más
        // caro que el del paciente solo.
        'tarea' => $acompanado ? 'sala' : 'chat_paciente',
        'course_id' => $courseId,
        'user_id' => (int) $user['id'],
    ]);
} catch (Throwable $e) {
    Response::error($e->getMessage(), 502);
}

$respuestas = $acompanado
    ? Sala::intervenciones($raw, $sala)
    : [['persona_id' => '', 'etiqueta' => '', 'texto' => $raw]];

if ($appointmentId > 0) {
    Db::migrateSalaIfNeeded();
    $logStmt = Db::get()->prepare(
        'INSERT INTO llm_chat_logs (appointment_id, student_id, case_id, role, content, speaker_id, speaker_label)
         VALUES (?, ?, ?, ?, ?, ?, ?)'
    );
    $logStmt->execute([$appointmentId, $user['id'], $caseId, 'user', $message, '', '']);
    foreach ($respuestas as $r) {
        $logStmt->execute([
            $appointmentId, $user['id'], $caseId, 'assistant', $r['texto'],
            $r['persona_id'], $r['etiqueta'],
        ]);
    }
}

Response::json([
    // `reply` es el texto del primero que habla: lo que espera un cliente
    // anterior a que el paciente pudiera venir acompañado.
    'reply' => $respuestas ? $respuestas[0]['texto'] : '',
    'respuestas' => $respuestas,
    'sala' => Sala::paraCliente($sala),
]);
