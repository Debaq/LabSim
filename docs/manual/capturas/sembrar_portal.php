<?php

declare(strict_types=1);

/**
 * Siembra una base NUEVA con datos inventados para sacar las capturas del
 * portal web del estudiante (public/student/*) para el manual.
 *
 * NUNCA correr esto sobre la base de producción: aplica schema.sql en una
 * base vacía y la llena con una alumna, una docente y cinco atenciones
 * inventadas. Los pacientes salen de casos_demo.json (casos 33-42, también
 * inventados). Lo llama capturar_portal.sh, dentro de un contenedor
 * php:7.4-cli, sobre una COPIA de labsim_backend:
 *
 *   php sembrar_portal.php <raíz de la copia> <casos_demo.json>
 *
 * Qué queda sembrado (lo que necesita cada pantalla):
 *   - curso "Audiología Clínica I", docente Andrea Soto Vidal, alumna
 *     Valentina Rojas (entra por LTI 1.1 con la clave labsim-demo);
 *   - tres atenciones de práctico cerradas (Hernán, Tomás, Carolina) y dos
 *     intentos de práctica libre con Jorge (con ficha de estudio permitida);
 *   - registro del audiómetro de cada atención (action_logs), generado con
 *     un examinador simulado como el de tests/test_audiometria_tecnica.php,
 *     con errores distintos en cada una para que la técnica vaya subiendo;
 *   - conversación con el paciente, comentarios de la docente (por turno,
 *     del procedimiento y de la evolución), avisos de la OIRS simulada,
 *     informes (ABR y otoscopia) y objetivos del curso.
 *
 * PHP 7.4: nada de match, str_contains ni enums.
 */

if ($argc < 3) {
    fwrite(STDERR, "uso: php sembrar_portal.php <raíz backend> <casos_demo.json>\n");
    exit(1);
}
$raiz = rtrim($argv[1], '/');
$casosDemo = json_decode((string) file_get_contents($argv[2]), true);
if (!is_array($casosDemo)) {
    fwrite(STDERR, "No se pudo leer {$argv[2]}\n");
    exit(1);
}

require_once $raiz . '/src/Clock.php';
Clock::pin();
require_once $raiz . '/src/Db.php';
require_once $raiz . '/src/AudiometriaPaciente.php';

$dbPath = $raiz . '/data/labsim.sqlite';
if (is_file($dbPath) && filesize($dbPath) > 0) {
    fwrite(STDERR, "Ya existe {$dbPath}: esto siembra solo una base nueva.\n");
    exit(1);
}

$pdo = Db::get();
$pdo->exec((string) file_get_contents($raiz . '/sql/schema.sql'));

function ins(PDO $pdo, string $tabla, array $fila): int
{
    $cols = array_keys($fila);
    $pdo->prepare(
        "INSERT INTO {$tabla} (" . implode(', ', $cols) . ') VALUES (' . implode(', ', array_fill(0, count($cols), '?')) . ')'
    )->execute(array_values($fila));
    return (int) $pdo->lastInsertId();
}

// --- Curso, docente, alumna, clave LTI --------------------------------------
$curso = ins($pdo, 'courses', ['name' => 'Audiología Clínica I', 'created_at' => '2026-08-03 09:00:00']);
$docente = ins($pdo, 'users', [
    'role' => 'admin', 'username' => 'andrea.soto', 'display_name' => 'Andrea Soto Vidal',
    'password_hash' => password_hash('demo', PASSWORD_DEFAULT),
]);
ins($pdo, 'course_teachers', ['course_id' => $curso, 'user_id' => $docente]);
// LTI 1.1: la clave del curso matricula sola (default_course_id). La usa
// fake_lti_launch.php para mostrar la página "Ingreso correcto".
$plataforma = ins($pdo, 'lti_platforms', [
    'version' => '1.1', 'consumer_key' => 'labsim-demo', 'shared_secret' => 'secreto-demo',
    'default_course_id' => $curso,
]);
$alumna = ins($pdo, 'users', [
    'role' => 'student', 'username' => 'valentina.rojas@alumnos.ejemplo.cl', 'display_name' => 'Valentina Rojas',
    'lti_platform_id' => $plataforma, 'lti_sub' => 'moodle-1042',
]);
ins($pdo, 'course_students', ['course_id' => $curso, 'user_id' => $alumna]);
foreach (['A', 'Z', 'ABR', 'EOA', 'OTO'] as $m) {
    ins($pdo, 'course_modules', ['course_id' => $curso, 'module_code' => $m]);
}

// --- Pacientes y fichas (casos_demo.json) -----------------------------------
$pacientes = [];
foreach (['33', '34', '36', '37'] as $caseId) {
    $caso = $casosDemo[$caseId];
    $snap = $caso['paciente_snapshot'];
    $pid = ins($pdo, 'patients', [
        'rut' => (string) $snap['rut'], 'nombre' => (string) $snap['nombre'], 'apellido' => (string) $snap['apellido'],
        'fecha_nac' => (string) $snap['fecha_nac'], 'historia_clinica' => (string) ($caso['historia_clinica'] ?? ''),
    ]);
    ins($pdo, 'cases', [
        'id' => $caseId, 'data' => json_encode($caso, JSON_UNESCAPED_UNICODE), 'patient_id' => $pid,
        'created_by' => $docente, 'updated_by' => $docente, 'updated_at' => '2026-08-20 12:00:00',
    ]);
    $pacientes[$caseId] = ['id' => $pid, 'snap' => $snap, 'caso' => $caso];
}

// Lista de práctica libre: Jorge, con ficha de estudio para comparar.
$practica = ins($pdo, 'practice_cases', [
    'course_id' => $curso, 'case_id' => '37', 'procedimiento' => 'Audiometría',
    'show_study_sheet' => 1, 'created_by' => $docente,
]);

/**
 * Cita + atención cerrada. $inicio = cuando apretó Atender, $cierre =
 * cuando la cerró ('Y-m-d H:i:s').
 */
function atencion(PDO $pdo, array $p, array $o): array
{
    $ap = ins($pdo, 'appointments', [
        'fecha' => date('d-m-y', strtotime($o['inicio'])), 'hora' => $o['hora'],
        'rut' => $p['snap']['rut'], 'nombre' => $p['snap']['nombre'], 'apellido' => $p['snap']['apellido'],
        'fecha_nac' => $p['snap']['fecha_nac'], 'procedimiento' => $o['procedimiento'],
        'case_id' => (string) $p['caso']['id'], 'course_id' => $o['curso'], 'patient_id' => $p['id'],
        'assigned_student_id' => $o['practica'] ? $o['alumna'] : null,
        'practice_id' => $o['practica'],
    ]);
    $att = ins($pdo, 'attendances', [
        'appointment_id' => $ap, 'student_id' => $o['alumna'], 'estado' => 'atendido',
        'nota' => $o['nota'], 'hora_real' => date('H:i', strtotime($o['inicio'])), 'updated_at' => $o['cierre'],
    ]);
    return ['ap' => $ap, 'att' => $att];
}

// --- Examinador simulado del audiómetro --------------------------------------
/**
 * Escribe las filas de action_logs de una audiometría (registro v2: foto
 * del equipo, mano del paciente, milisegundos), igual que la app. Copia de
 * AtExaminador (tests/test_audiometria_tecnica.php) con la cita, el caso y
 * la hora de inicio como parámetros, y algunos errores típicos a elección.
 */
final class Examinador
{
    public $logs = [];
    private $t;
    private $ap;
    private $caseId;
    private $paciente;
    private $estado;

    public function __construct(int $ap, string $caseId, array $caso, string $inicio)
    {
        $this->ap = $ap;
        $this->caseId = $caseId;
        $this->t = (float) strtotime($inicio);
        $this->paciente = new AudiometriaPaciente($caso);
        $this->estado = [
            'prueba' => 'Umbrales', 'freq' => '1000 Hz', 'step' => 5, 'instruccion' => null,
            'canales' => [
                ['on' => false, 'invertido' => false, 'intensity' => '20 dB HL', 'stim' => 'Tono', 'output' => 'Derecha', 'trans' => 'Aerea', 'contin' => 'Continuo'],
                ['on' => false, 'invertido' => false, 'intensity' => '20 dB HL', 'stim' => 'Narrow Band Noise', 'output' => 'Izquierda', 'trans' => 'Aerea', 'contin' => 'Continuo'],
            ],
        ];
        $this->log('audio_caso_cargado', []);
    }

    public function fin(): float
    {
        return $this->t;
    }

    private function log(string $accion, array $payload, float $dt = 0.5): void
    {
        $this->t += $dt;
        $payload['appointment_id'] = $this->ap;
        $payload['case_id'] = $this->caseId;
        $payload['v'] = 2;
        $ms = (int) floor(round($this->t, 3) * 1000);
        $ts = date('Y-m-d H:i:s', intdiv($ms, 1000)) . sprintf('.%03d', $ms % 1000);
        $this->logs[] = ['client_ts' => $ts, 'action' => $accion, 'payload' => $payload];
    }

    public function instruccion(string $cmd): void
    {
        $this->estado['instruccion'] = $cmd;
        $this->log('audio_talkback_press', ['command' => $cmd], 4.0);
    }

    public function transductor(string $trans): void
    {
        $this->estado['canales'][0]['trans'] = $trans;
        $this->log('audio_trans_select', ['ch' => 0, 'trans' => $trans], 2.0);
    }

    public function oido(int $o): void
    {
        $this->estado['canales'][0]['output'] = $o === 0 ? 'Derecha' : 'Izquierda';
        $this->log('audio_output_select', ['ch' => 0, 'output' => $this->estado['canales'][0]['output']], 1.5);
    }

    public function frecuencia(int $hz): void
    {
        $this->estado['freq'] = "{$hz} Hz";
        $this->log('audio_freq_change', ['freq' => $hz], 1.2);
    }

    /** Un estímulo de $dur segundos a $db. Devuelve si levantó la mano. */
    public function tono(int $db, float $dur = 1.5): bool
    {
        if ($this->estado['canales'][0]['intensity'] !== "{$db} dB HL") {
            $this->estado['canales'][0]['intensity'] = "{$db} dB HL";
            $this->log('audio_intensity_change', ['ch' => 0, 'intensity' => $db, 'freq' => (int) $this->estado['freq']], 0.8);
        }
        $c = $this->estado['canales'][0];
        $base = ['ch' => 0, 'freq' => $this->estado['freq'], 'intensity' => $c['intensity'], 'stim' => $c['stim'], 'output' => $c['output'], 'trans' => $c['trans']];
        $f = array_search((int) $this->estado['freq'], AudiometriaPaciente::FRECUENCIAS, true);
        $o = $c['output'] === 'Derecha' ? 0 : 1;
        $via = $c['trans'] === 'Aerea' ? 'aerea' : 'osea';
        $oye = $db >= $this->paciente->umbralSinRuido($via, (int) $f, $o);
        $this->log('audio_stim_button', $base + ['play' => true, 'estado' => $this->estado], 0.6);
        $this->estado['canales'][0]['on'] = true;
        if ($oye) {
            $this->log('audio_respuesta', ['mano' => true], 0.3);
        }
        $this->log('audio_stim_button', $base + ['play' => false, 'estado' => $this->estado], $dur - ($oye ? 0.3 : 0));
        $this->estado['canales'][0]['on'] = false;
        if ($oye) {
            $this->log('audio_respuesta', ['mano' => false], 0.05);
        }
        $this->t += 1.2;
        return $oye;
    }

    /**
     * Una frecuencia: familiarización +10 hasta responder, después -10 tras
     * responder y +5 tras no responder, cierra con 2 respuestas subiendo.
     * Errores: 'sube10' (sube 10 en vez de 5), 'corto' (tonos de 0,5 s),
     * 'una' (cierra con una sola respuesta subiendo).
     */
    public function umbral(int $inicio, array $errores = []): int
    {
        $dur = in_array('corto', $errores, true) ? 0.5 : 1.5;
        $necesarias = in_array('una', $errores, true) ? 1 : 2;
        $db = $inicio;
        while (!$this->tono($db, $dur)) {
            $db += 10;
            if ($db > 120) {
                return $db;
            }
        }
        $asc = [];
        for ($guard = 0; $guard < 40; $guard++) {
            $db -= 10;
            $vieneDeAbajo = false;
            while (true) {
                if ($this->tono($db, $dur)) {
                    if ($vieneDeAbajo) {
                        $asc[$db] = ($asc[$db] ?? 0) + 1;
                        if ($asc[$db] >= $necesarias) {
                            return $db;
                        }
                    }
                    break;
                }
                $db += in_array('sube10', $errores, true) ? 10 : 5;
                $vieneDeAbajo = true;
            }
        }
        return $db;
    }

    /** Un oído completo, en el orden $orden; repite 1 kHz si $repetir. */
    public function oidoCompleto(int $o, array $orden, int $inicio = 40, bool $repetir = true, array $errores = []): void
    {
        $this->oido($o);
        $previo = null;
        foreach ($orden as $hz) {
            $this->frecuencia($hz);
            $previo = $this->umbral($previo === null ? $inicio : $previo + 10, $errores);
        }
        if ($repetir) {
            $this->frecuencia(1000);
            $this->umbral($previo + 10, $errores);
        }
    }

    public function guardar(PDO $pdo, int $userId): void
    {
        $st = $pdo->prepare('INSERT INTO action_logs (user_id, client_ts, action, payload, received_at) VALUES (?, ?, ?, ?, ?)');
        foreach ($this->logs as $l) {
            $st->execute([$userId, $l['client_ts'], $l['action'], json_encode($l['payload'], JSON_UNESCAPED_UNICODE), substr($l['client_ts'], 0, 19)]);
        }
    }
}

$aereos = [1000, 2000, 3000, 4000, 6000, 8000, 500, 250, 125];
$oseos = [1000, 2000, 3000, 4000, 500, 250];

/** Conversación: [[rol, texto, hablante]], un turno cada ~40 s desde $desde. */
function chat(PDO $pdo, int $ap, int $alumna, string $caseId, string $desde, array $turnos): array
{
    $ids = [];
    $t = strtotime($desde);
    foreach ($turnos as $i => $tu) {
        $t += $tu[0] === 'user' ? 35 : 6;
        $ids[$i] = ins($pdo, 'llm_chat_logs', [
            'appointment_id' => $ap, 'student_id' => $alumna, 'case_id' => $caseId, 'role' => $tu[0],
            'content' => $tu[1], 'speaker_label' => $tu[0] === 'assistant' ? ($tu[2] ?? '') : '',
            'created_at' => date('Y-m-d H:i:s', $t),
        ]);
    }
    return $ids;
}

// --- 1) Hernán Contreras Lagos: primer práctico (técnica floja) -------------
$a1 = atencion($pdo, $pacientes['36'], [
    'inicio' => '2026-09-08 09:34:00', 'cierre' => '2026-09-08 10:26:00', 'hora' => '09:30',
    'procedimiento' => 'Audiometría', 'curso' => $curso, 'alumna' => $alumna, 'practica' => null,
    'nota' => "Paciente de 74 años, carpintero jubilado, consulta acompañado de su esposa por dificultad para entender conversaciones en grupo y volumen alto de la televisión. Refiere tinnitus bilateral tipo siseo en silencio. Exposición a ruido laboral sin protección.\nAudiometría tonal: hipoacusia sensorioneural bilateral, simétrica, de predominio en frecuencias agudas.\nSe sugiere evaluación para adaptación de audífonos.",
]);
$ex = new Examinador($a1['ap'], '36', $pacientes['36']['caso'], '2026-09-08 09:52:00');
// Sin instrucción al paciente, parte en 50 dB, sube de a 10, sin repetir 1 kHz.
$ex->oidoCompleto(1, $aereos, 50, false, ['sube10']);
$ex->oidoCompleto(0, [1000, 2000, 4000, 3000, 6000, 8000, 500, 250, 125], 50, false, ['sube10', 'corto']);
$ex->guardar($pdo, $alumna);
chat($pdo, $a1['ap'], $alumna, '36', '2026-09-08 09:35:00', [
    ['user', 'Buenos días, don Hernán. Soy Valentina, voy a hacerle el examen de audición. ¿Qué lo trae por acá?'],
    ['assistant', 'Buenos días, señorita. Mire, yo escucho bien, es mi señora la que insistió. Dice que pongo la tele muy fuerte.', 'Hernán (Paciente)'],
    ['user', '¿Y usted nota alguna dificultad para entender cuando le hablan?'],
    ['assistant', 'Con los nietos sí, hablan para adentro. Y en los almuerzos de la familia, con tanta gente, a veces no pillo nada.', 'Hernán (Paciente)'],
    ['assistant', 'Y termina diciendo que sí a todo sin entender, Hernán. Yo lo veo.', 'Gladys Pérez (Cónyuge)'],
    ['user', '¿Escucha algún ruido o pito en los oídos?'],
    ['assistant', 'Un siseo, en los dos, cuando está todo callado. Hace un par de años ya.', 'Hernán (Paciente)'],
    ['user', '¿Trabajó en algún lugar con mucho ruido?'],
    ['assistant', 'Toda la vida en el taller, con la sierra y la lijadora. Nunca usé esas orejeras, no se usaban.', 'Hernán (Paciente)'],
    ['user', 'Bien. Ahora le voy a poner unos audífonos y va a escuchar unos pitos.'],
    ['assistant', 'Ya, dele no más.', 'Hernán (Paciente)'],
]);
ins($pdo, 'inbox_messages', [
    'student_id' => $alumna, 'tipo' => 'reclamo', 'remitente' => 'OIRS (simulada)', 'asunto' => 'Sugerencia de mejora sobre tu atención',
    'cuerpo' => 'La señora Gladys, que acompañaba al paciente, sintió que no la tomaste en cuenta: contó lo que pasa en la casa y la conversación siguió como si no hubiera hablado. Tampoco le explicaste al paciente qué tenía que hacer cuando escuchara los tonos.',
    'appointment_id' => $a1['ap'], 'patient_id' => $pacientes['36']['id'], 'created_at' => '2026-09-08 10:26:30',
]);
ins($pdo, 'attendance_comments', [
    'attendance_id' => $a1['att'], 'section' => 'procedimiento', 'teacher_id' => $docente, 'created_at' => '2026-09-10 18:12:00',
    'comment' => 'Antes de partir con los tonos hay que darle la instrucción al paciente (talkback). Revisa también el paso de la técnica: después de que no responde se sube de a 5 dB.',
]);

// --- 2) Tomás Fuentes Riquelme: segundo práctico ----------------------------
$a2 = atencion($pdo, $pacientes['33'], [
    'inicio' => '2026-09-22 10:02:00', 'cierre' => '2026-09-22 10:41:00', 'hora' => '10:00',
    'procedimiento' => 'Otoscopia y audiometría', 'curso' => $curso, 'alumna' => $alumna, 'practica' => null,
    'nota' => "Paciente de 23 años, técnico eléctrico, acude a evaluación auditiva preocupacional para ingreso a faena minera. Sin molestias auditivas. Antecedente de tinnitus transitorio tras un concierto hace dos años.\nOtoscopia: CAE y membrana timpánica de aspecto normal bilateral.\nAudiometría tonal: audición dentro de rangos normales bilateral.",
]);
$ex = new Examinador($a2['ap'], '33', $pacientes['33']['caso'], '2026-09-22 10:15:00');
$ex->instruccion('colocar_fonos');
$ex->oidoCompleto(0, $aereos, 40, false);
$ex->oidoCompleto(1, $aereos, 40, false, ['una']);
$ex->guardar($pdo, $alumna);
$chat2 = chat($pdo, $a2['ap'], $alumna, '33', '2026-09-22 10:03:00', [
    ['user', 'Hola, Tomás. Soy Valentina, estudiante de fonoaudiología. Hoy te voy a hacer la evaluación auditiva que te pidieron en la empresa. ¿Cómo estás?'],
    ['assistant', 'Bien, bien, un poco nervioso no más. ¿Cuánto se demora esto?', 'Tomás'],
    ['user', 'Unos treinta o cuarenta minutos. Primero te voy a hacer algunas preguntas y después te miro los oídos. ¿Has notado algún problema para escuchar?'],
    ['assistant', 'No, para nada. Converso bien con todos. Escucho música con audífonos en el bus, pero bajito, le juro.', 'Tomás'],
    ['user', '¿Alguna vez te ha quedado un pito o el oído tapado después de un ruido fuerte?'],
    ['assistant', 'Una vez, después de un concierto hace como dos años. Quedé con un pito toda la noche, pero al otro día estaba bien.', 'Tomás'],
    ['user', 'Perfecto. Ahora te voy a explicar el examen: vas a escuchar unos pitos, unos fuertes y otros muy suaves. Cada vez que escuches uno, aunque sea muy despacito, levanta la mano.'],
    ['assistant', 'Ya, ¿y si no estoy seguro?', 'Tomás'],
    ['user', 'Si tienes la duda, levántala igual. Vamos a partir por el oído derecho.'],
    ['assistant', 'Dale.', 'Tomás'],
]);
ins($pdo, 'chat_comments', [
    'chat_log_id' => $chat2[6], 'teacher_id' => $docente, 'created_at' => '2026-09-24 19:05:00',
    'comment' => 'Muy buena instrucción: clara, y le dices qué hacer si duda. Así se reducen los falsos negativos.',
]);
ins($pdo, 'inbox_messages', [
    'student_id' => $alumna, 'tipo' => 'merito', 'remitente' => 'OIRS (simulada)', 'asunto' => 'Felicitación por tu atención',
    'cuerpo' => 'Tomás quedó tranquilo: le explicaste cuánto iba a durar el examen y qué tenía que hacer en cada parte. Dice que se fue sin nervios.',
    'appointment_id' => $a2['ap'], 'patient_id' => $pacientes['33']['id'], 'created_at' => '2026-09-22 10:41:30',
]);
$r1 = ins($pdo, 'reports', [
    'attendance_id' => $a2['att'], 'tipo' => 'OTOSCOPIA', 'created_at' => '2026-09-22 10:20:00', 'updated_at' => '2026-09-22 10:20:00',
    'data' => json_encode([
        'od' => ['cuadrantes' => [], 'cae' => ['cae_normal'], 'observaciones' => 'Membrana timpánica íntegra, nacarada, con reflejo luminoso conservado.'],
        'oi' => ['cuadrantes' => [], 'cae' => ['cae_cerumen'], 'observaciones' => 'Cerumen escaso que no obstruye; membrana visible en su totalidad.'],
        'conclusion' => 'Otoscopia bilateral dentro de lo normal.',
    ], JSON_UNESCAPED_UNICODE),
]);

// --- 3) Jorge Pizarro Cortés: primer intento de práctica libre --------------
$a3 = atencion($pdo, $pacientes['37'], [
    'inicio' => '2026-09-29 20:10:00', 'cierre' => '2026-09-29 20:44:00', 'hora' => '20:10',
    'procedimiento' => 'Audiometría', 'curso' => $curso, 'alumna' => $alumna, 'practica' => $practica,
    'nota' => 'Práctica: operador de chancador con 22 años de exposición a ruido. Audiometría tonal con caída en agudos bilateral, peor en el oído izquierdo.',
]);
$ex = new Examinador($a3['ap'], '37', $pacientes['37']['caso'], '2026-09-29 20:16:00');
$ex->instruccion('colocar_fonos');
$ex->oidoCompleto(0, $aereos, 40, false);
$ex->oidoCompleto(1, $aereos, 40, true);
$ex->guardar($pdo, $alumna);
chat($pdo, $a3['ap'], $alumna, '37', '2026-09-29 20:11:00', [
    ['user', 'Buenas tardes, don Jorge. ¿Por qué viene hoy?'],
    ['assistant', 'Me mandaron de la mutual. Dicen que en la faena todos quedamos medios sordos, así que vengo a ver qué tan mal estoy.', 'Jorge'],
    ['user', '¿Tiene algún pito o zumbido?'],
    ['assistant', 'Sí, un pito agudo en los dos oídos, más en el izquierdo. Lo tengo todo el día y me cuesta dormir.', 'Jorge'],
]);

// --- 4) Carolina Muñoz Sepúlveda: tercer práctico, con informes -------------
$a4 = atencion($pdo, $pacientes['34'], [
    'inicio' => '2026-10-01 11:05:00', 'cierre' => '2026-10-01 11:58:00', 'hora' => '11:00',
    'procedimiento' => 'Otoscopia, audiometría y PEATC', 'curso' => $curso, 'alumna' => $alumna, 'practica' => null,
    'nota' => "Paciente de 34 años, secretaria, consulta por disminución progresiva de la audición del oído derecho desde su segundo embarazo (hace 3 años) y tinnitus grave en el mismo oído, de predominio nocturno. Refiere entender mejor en ambientes ruidosos. Antecedente de madre con hipoacusia operada.\nOtoscopia: normal bilateral.\nAudiometría tonal: hipoacusia de conducción moderada en OD, con descenso de la vía ósea en 2 kHz; OI dentro de rangos normales.\nPEATC: latencias absolutas prolongadas en OD, interlatencias conservadas.",
]);
$ex = new Examinador($a4['ap'], '34', $pacientes['34']['caso'], '2026-10-01 11:18:00');
$ex->instruccion('colocar_fonos');
$ex->oidoCompleto(1, $aereos);
$ex->oidoCompleto(0, $aereos);
$ex->instruccion('colocar_vibrador');
$ex->transductor('Oséa');
$ex->oidoCompleto(0, $oseos, 40, false);
$ex->guardar($pdo, $alumna);
$chat4 = chat($pdo, $a4['ap'], $alumna, '34', '2026-10-01 11:06:00', [
    ['user', 'Buenos días, Carolina. Me llamo Valentina y hoy le voy a hacer la evaluación auditiva. Cuénteme, ¿qué le pasa?'],
    ['assistant', 'Buenos días. Perdón, ¿me lo puede repetir? Es que por este lado escucho poco. Desde que nació mi segundo hijo siento que el oído derecho está cada vez peor.', 'Carolina'],
    ['user', '¿Hace cuánto nació?'],
    ['assistant', 'Va a cumplir tres años. Al principio pensé que era cerumen, pero me hicieron un lavado y nada.', 'Carolina'],
    ['user', '¿Hay situaciones en que le cueste más entender?'],
    ['assistant', 'Es raro: en la micro o en un cumpleaños, con ruido, entiendo mejor que en la casa en silencio.', 'Carolina'],
    ['user', '¿Alguien en su familia tiene problemas de audición?'],
    ['assistant', 'Mi mamá quedó sorda de joven y la operaron de un oído, pero no sé bien de qué. Me da miedo que me pase lo mismo.', 'Carolina'],
    ['user', 'Entiendo. Vamos a hacer los exámenes para saber bien qué está pasando. Primero le voy a mirar los oídos con una lucecita.'],
    ['assistant', 'Ya, gracias.', 'Carolina'],
]);
ins($pdo, 'chat_comments', [
    'chat_log_id' => $chat4[4], 'teacher_id' => $docente, 'created_at' => '2026-10-03 17:40:00',
    'comment' => 'Buena pregunta abierta: con ella apareció la paracusia de Willis. Faltó preguntar por el zumbido (desde cuándo, en qué oído, cómo es).',
]);
ins($pdo, 'attendance_comments', [
    'attendance_id' => $a4['att'], 'section' => 'procedimiento', 'teacher_id' => $docente, 'created_at' => '2026-10-03 17:44:00',
    'comment' => 'Bien que partiste por el oído mejor y repetiste 1 kHz. En la vía ósea del OD revisa si hacía falta enmascarar.',
]);
ins($pdo, 'attendance_comments', [
    'attendance_id' => $a4['att'], 'section' => 'evolucion', 'teacher_id' => $docente, 'created_at' => '2026-10-03 17:47:00',
    'comment' => 'Evolución ordenada y completa. Agrega el grado de la pérdida con el promedio tonal y una sugerencia de derivación.',
]);
$r2 = ins($pdo, 'reports', [
    'attendance_id' => $a4['att'], 'tipo' => 'OTOSCOPIA', 'created_at' => '2026-10-01 11:12:00', 'updated_at' => '2026-10-01 11:12:00',
    'data' => json_encode([
        'od' => ['cuadrantes' => [], 'cae' => ['cae_normal'], 'observaciones' => 'Membrana timpánica íntegra y translúcida.'],
        'oi' => ['cuadrantes' => [], 'cae' => ['cae_normal'], 'observaciones' => ''],
        'conclusion' => 'Otoscopia bilateral sin hallazgos.',
    ], JSON_UNESCAPED_UNICODE),
]);
$curva = static function (string $lado, int $int, array $lat): array {
    return [
        'side' => $lado, 'int' => $int, 'average' => 2000, 'stim' => 'Click', 'pol' => 'Rarefacción', 'rate' => 21.1,
        'filter_passhigh' => 100, 'filter_down' => 3000, 'transductor' => 'Inserto',
        'LatAmp' => ['I' => [$lat[0], 0.22], 'III' => [$lat[1], 0.24], 'V' => [$lat[2], 0.46]],
        'tecnica' => ['barridos_aceptados' => 2000, 'barridos_rechazados' => 37, 'impedancia_max_kohm' => 3.1],
    ];
};
$r3 = ins($pdo, 'reports', [
    'attendance_id' => $a4['att'], 'tipo' => 'ABR', 'created_at' => '2026-10-01 11:50:00', 'updated_at' => '2026-10-01 11:55:00',
    'data' => json_encode([
        'curvas' => [
            '1' => $curva('OI', 80, [1.58, 3.71, 5.62]),
            '2' => $curva('OD', 80, [2.31, 4.42, 6.35]),
            '3' => $curva('OD', 70, [2.68, 4.80, 6.71]),
        ],
        'umbral_informado' => ['OD' => 60, 'OI' => 20],
        'tecnica' => [
            'transductor' => 'Inserto', 'montaje' => 'Ipsilateral', 'ventana_ms' => 12,
            'electrodos' => ['vertex' => 'Cz', 'right' => 'A2', 'left' => 'A1', 'ground' => 'Fpz'],
            'impedancias_kohm' => ['vertex' => 2.4, 'right' => 3.1, 'left' => 2.8, 'ground' => 2.2],
            'impedancia_max_kohm' => 3.1, 'impedancia_desbalance_kohm' => 0.7, 'impedancia_en_norma' => true,
            'rechazo_artefacto_uv' => 25,
        ],
        'hallazgos' => 'OI: ondas I, III y V presentes, de latencias absolutas e interlatencias dentro de lo esperado. OD: ondas I, III y V presentes con latencias absolutas prolongadas e interlatencias I-III, III-V e I-V conservadas.',
        'conclusion' => 'Desplazamiento de latencias absolutas en OD con interlatencias normales, compatible con un componente de conducción. OI dentro de lo normal.',
    ], JSON_UNESCAPED_UNICODE),
]);

// --- 5) Jorge: segundo intento de práctica libre (técnica completa) ---------
$a5 = atencion($pdo, $pacientes['37'], [
    'inicio' => '2026-10-06 19:30:00', 'cierre' => '2026-10-06 20:02:00', 'hora' => '19:30',
    'procedimiento' => 'Audiometría', 'curso' => $curso, 'alumna' => $alumna, 'practica' => $practica,
    'nota' => 'Práctica, segundo intento: hipoacusia sensorioneural bilateral con escotoma en 4 kHz, mayor en OI, compatible con exposición a ruido.',
]);
$ex = new Examinador($a5['ap'], '37', $pacientes['37']['caso'], '2026-10-06 19:36:00');
$ex->instruccion('colocar_fonos');
$ex->oidoCompleto(0, $aereos);
$ex->oidoCompleto(1, $aereos);
$ex->guardar($pdo, $alumna);
chat($pdo, $a5['ap'], $alumna, '37', '2026-10-06 19:31:00', [
    ['user', 'Buenas tardes, don Jorge. Soy Valentina. ¿Qué lo trae hoy?'],
    ['assistant', 'Lo de siempre, señorita: el examen de la mutual. Dicen que en la faena todos quedamos así.', 'Jorge'],
    ['user', '¿Usa protección auditiva en el trabajo?'],
    ['assistant', 'Los tapones, cuando me acuerdo. Pican y no escucho la radio con ellos puestos.', 'Jorge'],
    ['user', '¿Y fuera del trabajo, se expone a ruidos fuertes?'],
    ['assistant', 'Los fines de semana salgo a cazar, con escopeta.', 'Jorge'],
]);

// --- Objetivos del curso (los ve la alumna arriba de su resumen) -------------
$objetivos = [
    ['Cerrar al menos 6 atenciones en los prácticos del semestre.', 'atenciones', 6],
    ['Llegar a 85 % de logro en la técnica de audiometría.', 'tecnica_promedio', 85],
    ['Entregar al menos 2 informes de exámenes.', 'informes', 2],
    ['Explicar cada examen al paciente antes de empezar y despedirse indicando los pasos a seguir.', '', null],
];
foreach ($objetivos as $i => $o) {
    ins($pdo, 'course_objectives', [
        'course_id' => $curso, 'texto' => $o[0], 'indicador' => $o[1], 'meta' => $o[2], 'orden' => $i, 'created_by' => $docente,
    ]);
}

echo json_encode([
    'curso' => $curso, 'alumna' => $alumna, 'docente' => $docente,
    'citas' => ['hernan' => $a1['ap'], 'tomas' => $a2['ap'], 'jorge1' => $a3['ap'], 'carolina' => $a4['ap'], 'jorge2' => $a5['ap']],
    'informes' => ['otoscopia_tomas' => $r1, 'otoscopia_carolina' => $r2, 'abr_carolina' => $r3],
]) . "\n";
