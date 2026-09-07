<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Courses.php';

$me = Auth::requireAdminSession();
$pdo = Db::get();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;

$appointmentId = (int) ($_GET['appointment_id'] ?? 0);
$studentId = (int) ($_GET['student_id'] ?? 0);

$stmt = $pdo->prepare('SELECT id, display_name FROM users WHERE id = ?');
$stmt->execute([$studentId]);
$student = $stmt->fetch();

// Mismo scoping que student.php: docente solo ve alumnos de su(s) curso(s).
if ($student && !$isFullAdmin) {
    $roster = Courses::rosterUserIds(Courses::teacherCourseIds((int) $me['id']));
    if (!in_array($studentId, $roster, true)) {
        $student = null;
    }
}

$stmt = $pdo->prepare(
    "SELECT a.id, a.fecha, a.hora, a.nombre, a.apellido, a.procedimiento
     FROM appointments a WHERE a.id = ?"
);
$stmt->execute([$appointmentId]);
$appointment = $stmt->fetch();

if (!$student || !$appointment) {
    admin_header('Atención', $me);
    echo '<p class="error">Alumno o cita no encontrados.</p>';
    admin_footer();
    exit;
}

$stmt = $pdo->prepare('SELECT id, nota FROM attendances WHERE appointment_id = ? AND student_id = ?');
$stmt->execute([$appointmentId, $studentId]);
$attendance = $stmt->fetch();

// Comentario del docente sobre un turno puntual (retroalimentación) -- queda
// amarrado al id exacto de llm_chat_logs, así se pinta a la misma altura del
// turno al que responde. PRG (POST -> redirect -> GET) para que un refresh
// no reenvíe el comentario.
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $section = (string) ($_POST['section'] ?? 'chat');
    $comment = trim((string) ($_POST['comment'] ?? ''));
    if ($comment !== '' && $section === 'chat') {
        $chatLogId = (int) ($_POST['chat_log_id'] ?? 0);
        // El chat_log_id debe pertenecer a ESTA cita/alumno (ya scopeados
        // arriba) -- si no, nadie comenta editando el POST en otra atención.
        $stmt = $pdo->prepare('SELECT 1 FROM llm_chat_logs WHERE id = ? AND appointment_id = ? AND student_id = ?');
        $stmt->execute([$chatLogId, $appointmentId, $studentId]);
        if ($stmt->fetch()) {
            $pdo->prepare('INSERT INTO chat_comments (chat_log_id, teacher_id, comment) VALUES (?, ?, ?)')
                ->execute([$chatLogId, $me['id'], $comment]);
        }
    } elseif ($comment !== '' && in_array($section, ['evolucion', 'procedimiento'], true) && $attendance) {
        // Acá el comentario va sobre la atención completa (no un turno
        // puntual) -- attendance_id ya viene scopeado por el SELECT de
        // arriba (appointment_id + student_id), no llega del POST.
        $pdo->prepare('INSERT INTO attendance_comments (attendance_id, section, teacher_id, comment) VALUES (?, ?, ?, ?)')
            ->execute([$attendance['id'], $section, $me['id'], $comment]);
    }
    header('Location: chat_detail.php?appointment_id=' . $appointmentId . '&student_id=' . $studentId);
    exit;
}

$attendanceComments = ['evolucion' => [], 'procedimiento' => []];
if ($attendance) {
    $stmt = $pdo->prepare(
        "SELECT ac.section, ac.comment, ac.created_at, u.display_name AS teacher_name
         FROM attendance_comments ac
         JOIN users u ON u.id = ac.teacher_id
         WHERE ac.attendance_id = ? ORDER BY ac.id"
    );
    $stmt->execute([$attendance['id']]);
    foreach ($stmt->fetchAll() as $c) {
        $attendanceComments[$c['section']][] = $c;
    }
}

// Informes de módulos de examen que el alumno subió en esta atención
// (EOA/ABR/VEMP...) -- el PDF se sirve en admin/report_pdf.php.
$reports = [];
if ($attendance) {
    $stmt = $pdo->prepare('SELECT id, tipo, updated_at FROM reports WHERE attendance_id = ? ORDER BY tipo');
    $stmt->execute([$attendance['id']]);
    $reports = $stmt->fetchAll();
}
$reportLabels = [
    'ABR' => 'PEATC (ABR)',
    'EOA' => 'Emisiones otoacústicas',
    'VEMP' => 'VEMP',
    'ELECTROCOCLEO' => 'Electrococleografía',
];

$stmt = $pdo->prepare(
    'SELECT id, role, content, created_at FROM llm_chat_logs
     WHERE appointment_id = ? AND student_id = ? ORDER BY id'
);
$stmt->execute([$appointmentId, $studentId]);
$log = $stmt->fetchAll();

$comments = [];
if ($log) {
    $logIds = array_column($log, 'id');
    $placeholders = implode(',', array_fill(0, count($logIds), '?'));
    $stmt = $pdo->prepare(
        "SELECT c.chat_log_id, c.comment, c.created_at, u.display_name AS teacher_name
         FROM chat_comments c
         JOIN users u ON u.id = c.teacher_id
         WHERE c.chat_log_id IN ($placeholders)
         ORDER BY c.id"
    );
    $stmt->execute($logIds);
    foreach ($stmt->fetchAll() as $c) {
        $comments[(int) $c['chat_log_id']][] = $c;
    }
}

function chat_initials(string $name): string
{
    $parts = preg_split('/\s+/', trim($name));
    $initials = '';
    foreach (array_slice($parts, 0, 2) as $p) {
        $initials .= mb_strtoupper(mb_substr($p, 0, 1));
    }
    return $initials ?: '?';
}

admin_add_css('chat.css');
admin_header('Atención: ' . $student['display_name'], $me);
?>
<div class="chat-hero">
    <div>
        <a href="student.php?id=<?= (int) $studentId ?>">&larr; <?= htmlspecialchars($student['display_name']) ?></a>
        <h2><?= htmlspecialchars(trim("{$appointment['nombre']} {$appointment['apellido']}")) ?: 'Paciente sin nombre' ?></h2>
        <div class="meta">
            Cita #<?= (int) $appointment['id'] ?> · <?= htmlspecialchars($appointment['fecha'] ?: '—') ?> <?= htmlspecialchars($appointment['hora'] ?: '') ?>
            · <?= htmlspecialchars($appointment['procedimiento']) ?>
        </div>
    </div>
    <span class="badge"><?= count($log) ?> mensajes</span>
</div>

<?php
function render_section_comments(string $section, string $label, string $text, array $comments): void
{
    ?>
    <div class="card section-panel">
        <h3><?= htmlspecialchars($label) ?></h3>
        <div class="section-text"><?= $text !== '' ? nl2br(htmlspecialchars($text)) : '<span style="color:var(--color-muted);">Sin registro todavía.</span>' ?></div>
        <div class="section-comments">
            <?php foreach ($comments as $c): ?>
            <div class="comment-bubble">
                <div class="avatar a-teacher" title="Docente"><?= htmlspecialchars(chat_initials($c['teacher_name'])) ?></div>
                <div class="comment-body">
                    <span class="chat-meta"><?= htmlspecialchars($c['teacher_name']) ?> · <?= htmlspecialchars($c['created_at']) ?></span>
                    <?= nl2br(htmlspecialchars($c['comment'])) ?>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
        <form method="post" class="comment-form">
            <?= csrf_field() ?>
            <input type="hidden" name="section" value="<?= htmlspecialchars($section) ?>">
            <input type="text" name="comment" placeholder="Comentar <?= $section === 'evolucion' ? 'la evolución' : 'el procedimiento' ?>...">
            <button type="submit" title="Agregar comentario">+</button>
        </form>
    </div>
    <?php
}

if ($attendance) {
    render_section_comments('evolucion', 'Evolución del alumno', (string) $attendance['nota'], $attendanceComments['evolucion']);
    render_section_comments('procedimiento', 'Procedimiento', (string) $appointment['procedimiento'], $attendanceComments['procedimiento']);
}
?>

<?php if ($reports): ?>
<div class="card section-panel">
    <h3>Informes del alumno</h3>
    <table>
        <tr><th>Examen</th><th>Actualizado</th><th></th></tr>
        <?php foreach ($reports as $r): ?>
        <tr>
            <td><?= htmlspecialchars($reportLabels[$r['tipo']] ?? $r['tipo']) ?></td>
            <td><?= htmlspecialchars($r['updated_at']) ?></td>
            <td><a href="report_pdf.php?id=<?= (int) $r['id'] ?>" target="_blank">Ver PDF</a></td>
        </tr>
        <?php endforeach; ?>
    </table>
</div>
<?php endif; ?>

<div class="card chat-panel">
    <p class="chat-legend">Globos amarillos = retroalimentación docente sobre ese turno puntual. Solo la ve el equipo docente, el alumno no la ve.</p>
    <div class="chat-grid">
        <?php foreach ($log as $turn):
            $role = $turn['role'] === 'assistant' ? 'assistant' : 'user';
            $turnComments = $comments[(int) $turn['id']] ?? [];
        ?>
        <div class="chat-row">
            <div class="bubble-col align-<?= $role ?>">
                <?php if ($role === 'assistant'): ?>
                <div class="avatar a-assistant" title="Paciente">P</div>
                <?php endif; ?>
                <div class="chat-turn <?= $role ?>">
                    <span class="chat-meta"><?= $role === 'assistant' ? 'Paciente' : 'Alumno' ?> · <?= htmlspecialchars($turn['created_at']) ?></span>
                    <?= htmlspecialchars($turn['content']) ?>
                </div>
                <?php if ($role === 'user'): ?>
                <div class="avatar a-user" title="Alumno"><?= htmlspecialchars(chat_initials($student['display_name'])) ?></div>
                <?php endif; ?>
            </div>
            <div class="comment-col">
                <?php foreach ($turnComments as $c): ?>
                <div class="comment-bubble">
                    <div class="avatar a-teacher" title="Docente"><?= htmlspecialchars(chat_initials($c['teacher_name'])) ?></div>
                    <div class="comment-body">
                        <span class="chat-meta"><?= htmlspecialchars($c['teacher_name']) ?> · <?= htmlspecialchars($c['created_at']) ?></span>
                        <?= htmlspecialchars($c['comment']) ?>
                    </div>
                </div>
                <?php endforeach; ?>
                <form method="post" class="comment-form">
                    <?= csrf_field() ?>
                    <input type="hidden" name="section" value="chat">
                    <input type="hidden" name="chat_log_id" value="<?= (int) $turn['id'] ?>">
                    <input type="text" name="comment" placeholder="Comentar este turno...">
                    <button type="submit" title="Agregar comentario">+</button>
                </form>
            </div>
        </div>
        <?php endforeach; ?>
        <?php if (!$log): ?>
        <p class="chat-empty">Sin conversación registrada para esta atención (o el alumno no chateó con el paciente).</p>
        <?php endif; ?>
    </div>
</div>
<?php
admin_footer();
