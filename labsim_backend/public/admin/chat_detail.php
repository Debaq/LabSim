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
    admin_header('Conversación', $me);
    echo '<p class="error">Alumno o cita no encontrados.</p>';
    admin_footer();
    exit;
}

// Comentario del docente sobre un turno puntual (retroalimentación) -- queda
// amarrado al id exacto de llm_chat_logs, así se pinta a la misma altura del
// turno al que responde. PRG (POST -> redirect -> GET) para que un refresh
// no reenvíe el comentario.
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $chatLogId = (int) ($_POST['chat_log_id'] ?? 0);
    $comment = trim((string) ($_POST['comment'] ?? ''));
    if ($comment !== '') {
        // El chat_log_id debe pertenecer a ESTA cita/alumno (ya scopeados
        // arriba) -- si no, nadie comenta editando el POST en otra atención.
        $stmt = $pdo->prepare('SELECT 1 FROM llm_chat_logs WHERE id = ? AND appointment_id = ? AND student_id = ?');
        $stmt->execute([$chatLogId, $appointmentId, $studentId]);
        if ($stmt->fetch()) {
            $pdo->prepare('INSERT INTO chat_comments (chat_log_id, teacher_id, comment) VALUES (?, ?, ?)')
                ->execute([$chatLogId, $me['id'], $comment]);
        }
    }
    header('Location: chat_detail.php?appointment_id=' . $appointmentId . '&student_id=' . $studentId);
    exit;
}

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

admin_header('Conversación: ' . $student['display_name'], $me);
?>
<style>
    .chat-hero {
        background: linear-gradient(135deg, #1a2744, #24345c);
        color: #fff; border-radius: 10px; padding: 1.1rem 1.5rem; margin-bottom: 1.2rem;
        display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 0.6rem;
    }
    .chat-hero a { color: #cdd8f0; text-decoration: none; font-size: 0.85rem; }
    .chat-hero a:hover { color: #fff; text-decoration: underline; }
    .chat-hero h2 { margin: 0.2rem 0 0; font-size: 1.2rem; }
    .chat-hero .meta { font-size: 0.82rem; color: #aeb9d6; margin-top: 0.15rem; }
    .chat-hero .badge {
        background: rgba(255,255,255,0.12); border-radius: 999px; padding: 0.3rem 0.8rem;
        font-size: 0.8rem; white-space: nowrap;
    }

    .chat-panel { background: #fbfbfc; border-radius: 10px; padding: 0.5rem 1.5rem 1.5rem; }
    .chat-legend { font-size: 0.82rem; color: #7a7f8c; margin: 0 0 1rem; }

    .chat-grid { display: flex; flex-direction: column; gap: 1.1rem; width: 88%; max-width: 62rem; margin: 0 auto; }
    .chat-row { display: flex; align-items: flex-start; gap: 1rem; }

    .bubble-col { flex: 0 0 52%; display: flex; align-items: flex-end; gap: 0.5rem; }
    .bubble-col.align-user { justify-content: flex-end; }
    .bubble-col.align-assistant { justify-content: flex-start; }
    .bubble-col.align-user .avatar { order: 2; }

    .avatar {
        flex: 0 0 auto; width: 26px; height: 26px; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        font-size: 0.65rem; font-weight: 700; color: #fff;
    }
    .avatar.a-user { background: #3b5bdb; }
    .avatar.a-assistant { background: #6b7280; }
    .avatar.a-teacher { background: #c98a12; }

    .chat-turn {
        max-width: calc(100% - 2.2rem); padding: 0.5rem 0.8rem; border-radius: 14px;
        font-size: 0.88rem; line-height: 1.4; white-space: pre-wrap;
        box-shadow: 0 1px 1px rgba(0,0,0,0.04);
    }
    .chat-turn .chat-meta { display: block; font-size: 0.68rem; margin-bottom: 0.15rem; opacity: 0.75; }
    .chat-turn.user { background: #3b5bdb; color: #fff; border-bottom-right-radius: 4px; }
    .chat-turn.user .chat-meta { color: #dbe3ff; }
    .chat-turn.assistant { background: #fff; border: 1px solid #e5e5ea; border-bottom-left-radius: 4px; }
    .chat-turn.assistant .chat-meta { color: #9096a2; }

    .comment-col { flex: 1 1 auto; display: flex; flex-direction: column; gap: 0.4rem; padding-top: 0.1rem; min-width: 0; }
    .comment-bubble {
        display: flex; gap: 0.5rem; align-items: flex-start;
        background: #fff9ea; border: 1px solid #f3dfa0; border-radius: 10px; padding: 0.4rem 0.65rem;
    }
    .comment-bubble .comment-body { font-size: 0.82rem; line-height: 1.35; white-space: pre-wrap; }
    .comment-bubble .chat-meta { display: block; font-size: 0.66rem; color: #a3822f; margin-bottom: 0.1rem; }

    .comment-form { display: flex; gap: 0.4rem; align-items: center; }
    .comment-form input[type="text"] {
        width: auto; flex: 1 1 auto; padding: 0.35rem 0.6rem; margin: 0;
        font-size: 0.8rem; border: 1px solid #e2e2e8; border-radius: 999px; background: #fff;
    }
    .comment-form input[type="text"]:focus { outline: none; border-color: #c98a12; }
    .comment-form button {
        margin: 0; padding: 0; width: 1.7rem; height: 1.7rem; border-radius: 50%;
        background: #c98a12; color: #fff; font-size: 1rem; line-height: 1; flex: 0 0 auto;
    }
    .comment-form button:hover { background: #b57a0a; }

    .chat-empty { text-align: center; color: #9096a2; padding: 2rem 0; }
</style>
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
