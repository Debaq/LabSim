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
        'content' => (!$esAlumno && $label !== '' && $acompanado) ? "{$label}: {$content}" : $content,
    ];
}

try {
    $raw = LlmChat::reply($systemPrompt, $history, $message);
} catch (Throwable $e) {
    Response::error($e->getMessage(), 502);
}

$respuestas = $acompanado
    ? intervencionesDesdeJson($raw, $sala)
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

/**
 * Lee el JSON con el que el modelo dice quién habló ({"turnos":[{"id","texto"}]}).
 *
 * Si el JSON no viene o los ids no son de esta consulta, NO se pierde el
 * turno: lo que haya escrito se muestra como intervención de quien lleva la
 * voz cantante. Una conversación que se corta porque el modelo se comió una
 * llave es peor que una atribuida al que más probablemente hablaba.
 *
 * @return list<array{persona_id: string, etiqueta: string, texto: string}>
 */
function intervencionesDesdeJson(string $raw, array $sala): array
{
    $clean = trim($raw);
    // El modelo a veces envuelve el JSON en ```json ... ``` pese a la
    // instrucción de no hacerlo -- se pela el fence si aparece (mismo
    // criterio que OirsEvaluator::parseVerdict).
    if (substr($clean, 0, 3) === '```') {
        $clean = trim((string) preg_replace('/^```[a-zA-Z]*\n?|```$/', '', $clean));
    }

    $data = json_decode($clean, true);
    $turnos = is_array($data) ? ($data['turnos'] ?? null) : null;

    $out = [];
    if (is_array($turnos)) {
        foreach ($turnos as $t) {
            $texto = trim((string) ($t['texto'] ?? ''));
            if ($texto === '') {
                continue;
            }
            // Id inventado o mal escrito: la frase igual sirve, se le
            // atribuye a quien lleva la voz cantante en vez de tirarla.
            $persona = Sala::persona($sala, trim((string) ($t['id'] ?? ''))) ?? Sala::informante($sala);
            if ($persona === null) {
                continue;
            }
            $out[] = [
                'persona_id' => $persona['id'],
                'etiqueta' => Sala::etiqueta($persona),
                'texto' => $texto,
            ];
        }
    }

    if ($out) {
        return $out;
    }

    $informante = Sala::informante($sala);
    return [[
        'persona_id' => $informante['id'] ?? '',
        'etiqueta' => $informante !== null ? Sala::etiqueta($informante) : '',
        'texto' => $clean !== '' ? $clean : $raw,
    ]];
}
