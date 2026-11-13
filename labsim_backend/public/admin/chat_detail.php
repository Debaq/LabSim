<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/ReportFile.php';
require_once __DIR__ . '/../../views/indicadores/faltas_graves.php';
require_once __DIR__ . '/../../src/AudiometriaTecnicaVista.php';
require_once __DIR__ . '/../../src/AdminAudit.php';

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
    if (in_array($section, ['editar', 'borrar'], true)) {
        // Editar o eliminar lo que escribió un docente (ver
        // ComentariosDocente): el id tiene que ser de ESTA atención y del
        // docente que lo pide, salvo el admin completo.
        $tipo = (string) ($_POST['tipo'] ?? '');
        $id = (int) ($_POST['id'] ?? 0);
        $fila = in_array($tipo, ComentariosDocente::TIPOS, true)
            ? ComentariosDocente::buscar($pdo, $tipo, $id, $appointmentId, $studentId) : null;
        if ($fila && ComentariosDocente::puedeTocar((int) $fila['author_id'], (int) $me['id'], $isFullAdmin)) {
            if ($section === 'editar') {
                ComentariosDocente::editar($pdo, $tipo, $id, (string) ($_POST['texto'] ?? ''));
            } else {
                ComentariosDocente::borrar($pdo, $tipo, $id);
                AdminAudit::log($me, 'comentario_borrar', ['tipo' => $tipo, 'id' => $id,
                    'appointment_id' => $appointmentId, 'student_id' => $studentId]);
            }
        }
        $ancla = (string) ($_POST['ancla'] ?? '');
        header('Location: chat_detail.php?appointment_id=' . $appointmentId . '&student_id=' . $studentId
            . (preg_match('/^[a-z0-9-]+$/', $ancla) ? '#' . $ancla : ''));
        exit;
    }
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
    } elseif ($section === 'respuesta' && $attendance) {
        // Feedback al feedback: el docente contesta en el hilo de uno de
        // sus comentarios. El comment_id tiene que ser de ESTA atención.
        $commentId = (int) ($_POST['comment_id'] ?? 0);
        $stmt = $pdo->prepare('SELECT 1 FROM attendance_comments WHERE id = ? AND attendance_id = ?');
        $stmt->execute([$commentId, $attendance['id']]);
        if ($stmt->fetch()) {
            ComentarioRespuestas::responder($pdo, $commentId, (int) $me['id'], 'docente', (string) ($_POST['texto'] ?? ''));
        }
        header('Location: chat_detail.php?appointment_id=' . $appointmentId . '&student_id=' . $studentId . '#comentario-' . $commentId);
        exit;
    }
    header('Location: chat_detail.php?appointment_id=' . $appointmentId . '&student_id=' . $studentId);
    exit;
}

$attendanceComments = ['evolucion' => [], 'procedimiento' => []];
$hilos = [];
if ($attendance) {
    $stmt = $pdo->prepare(
        "SELECT ac.id, ac.section, ac.comment, ac.created_at, ac.teacher_id, u.display_name AS teacher_name
         FROM attendance_comments ac
         JOIN users u ON u.id = ac.teacher_id
         WHERE ac.attendance_id = ? ORDER BY ac.id"
    );
    $stmt->execute([$attendance['id']]);
    $filasComentarios = $stmt->fetchAll();
    foreach ($filasComentarios as $c) {
        $attendanceComments[$c['section']][] = $c;
    }
    // Lo que el alumno respondió y el docente no había visto se marca como
    // visto al abrir la atención, pero se pinta "nuevo" esta vez.
    $ids = array_column($filasComentarios, 'id');
    $hilos = ComentarioRespuestas::porComentario($pdo, $ids);
    ComentarioRespuestas::marcarLeidas($pdo, $ids, 'docente');
}
$puedeResponder = ComentarioRespuestas::listo($pdo);

// Informes de módulos de examen que el alumno subió en esta atención
// (EOA/ABR/VEMP...) -- el PDF se sirve en admin/report_pdf.php.
$reports = [];
if ($attendance) {
    $stmt = $pdo->prepare('SELECT id, tipo, updated_at FROM reports WHERE attendance_id = ? ORDER BY tipo');
    $stmt->execute([$attendance['id']]);
    $reports = $stmt->fetchAll();
}
$reportLabels = ReportFile::LABELS;

$stmt = $pdo->prepare(
    'SELECT id, role, content, speaker_label, created_at FROM llm_chat_logs
     WHERE appointment_id = ? AND student_id = ? ORDER BY id'
);
$stmt->execute([$appointmentId, $studentId]);
$log = $stmt->fetchAll();

$comments = [];
if ($log) {
    $logIds = array_column($log, 'id');
    $placeholders = implode(',', array_fill(0, count($logIds), '?'));
    $stmt = $pdo->prepare(
        "SELECT c.id, c.chat_log_id, c.comment, c.created_at, c.teacher_id, u.display_name AS teacher_name
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

/**
 * Editar / Eliminar bajo un "⋯" en lo que escribió un docente, solo si es
 * suyo (o es admin completo). Sin JS: un <details> con los dos formularios.
 */
function acciones_comentario(string $tipo, int $id, int $autorId, string $texto, string $ancla): void
{
    global $me, $isFullAdmin;
    if (!ComentariosDocente::puedeTocar($autorId, (int) $me['id'], (bool) $isFullAdmin)) {
        return;
    }
    $aviso = $tipo === 'atencion'
        ? '¿Eliminar este comentario? Se borra también lo que el alumno respondió. No se puede deshacer.'
        : '¿Eliminar este comentario? No se puede deshacer.';
    ?>
    <details class="comment-actions">
        <summary title="Editar o eliminar">⋯</summary>
        <form method="post" class="comment-edit">
            <?= csrf_field() ?>
            <input type="hidden" name="section" value="editar">
            <input type="hidden" name="tipo" value="<?= htmlspecialchars($tipo) ?>">
            <input type="hidden" name="id" value="<?= $id ?>">
            <input type="hidden" name="ancla" value="<?= htmlspecialchars($ancla) ?>">
            <textarea name="texto" rows="4" maxlength="<?= ComentarioRespuestas::MAX_CHARS ?>" required><?= htmlspecialchars($texto) ?></textarea>
            <div class="comment-edit-botones">
                <button type="submit" class="btn btn--sm">Guardar cambios</button>
                <?php // Del otro formulario (atributo form): misma fila, y su onsubmit pide confirmar ?>
                <button type="submit" class="btn btn--sm btn--danger" form="borrar-<?= htmlspecialchars($tipo) ?>-<?= $id ?>">Eliminar</button>
            </div>
        </form>
        <form method="post" id="borrar-<?= htmlspecialchars($tipo) ?>-<?= $id ?>" hidden onsubmit="return confirm(<?= htmlspecialchars(json_encode($aviso), ENT_QUOTES) ?>);">
            <?= csrf_field() ?>
            <input type="hidden" name="section" value="borrar">
            <input type="hidden" name="tipo" value="<?= htmlspecialchars($tipo) ?>">
            <input type="hidden" name="id" value="<?= $id ?>">
            <input type="hidden" name="ancla" value="<?= htmlspecialchars($ancla) ?>">
        </form>
    </details>
    <?php
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
function render_section_comments(string $section, string $label, string $text, array $comments,
                                 array $hilos, bool $puedeResponder, string $alumno): void
{
    ?>
    <div class="card section-panel">
        <h3><?= htmlspecialchars($label) ?></h3>
        <div class="section-text"><?= $text !== '' ? nl2br(htmlspecialchars($text)) : '<span style="color:var(--color-muted);">Sin registro todavía.</span>' ?></div>
        <div class="section-comments">
            <?php foreach ($comments as $c): $cid = (int) $c['id']; ?>
            <div class="comment-hilo" id="comentario-<?= $cid ?>">
            <div class="comment-bubble">
                <div class="avatar a-teacher" title="Docente"><?= htmlspecialchars(chat_initials($c['teacher_name'])) ?></div>
                <?php // Sin espacios entre etiquetas: .comment-body es pre-wrap y la sangría del PHP se veía ?>
                <div class="comment-body"><span class="chat-meta"><?= htmlspecialchars($c['teacher_name']) ?> · <?= htmlspecialchars($c['created_at']) ?></span><?= htmlspecialchars($c['comment']) ?></div>
                <?php acciones_comentario('atencion', $cid, (int) $c['teacher_id'], (string) $c['comment'], 'comentario-' . $cid); ?>
            </div>
            <?php foreach ($hilos[$cid] ?? [] as $r): $delAlumno = $r['autor'] === 'alumno'; ?>
            <div class="comment-bubble comment-reply<?= $delAlumno ? ' comment-reply--alumno' : '' ?>">
                <div class="avatar <?= $delAlumno ? 'a-user' : 'a-teacher' ?>" title="<?= $delAlumno ? 'Alumno' : 'Docente' ?>"><?= htmlspecialchars(chat_initials($r['author_name'])) ?></div>
                <div class="comment-body"><span class="chat-meta"><?= htmlspecialchars($r['author_name']) ?><?= $delAlumno ? ' (alumno)' : '' ?> · <?= htmlspecialchars($r['created_at']) ?><?php if ($delAlumno && !$r['leido']): ?> <span class="tag tag--warn">nuevo</span><?php endif; ?></span><?= htmlspecialchars($r['texto']) ?></div>
                <?php if (!$delAlumno) { acciones_comentario('respuesta', (int) $r['id'], (int) $r['author_id'], (string) $r['texto'], 'comentario-' . $cid); } ?>
            </div>
            <?php endforeach; ?>
            <?php if ($puedeResponder): ?>
            <form method="post" class="comment-form comment-reply-form">
                <?= csrf_field() ?>
                <input type="hidden" name="section" value="respuesta">
                <input type="hidden" name="comment_id" value="<?= $cid ?>">
                <input type="text" name="texto" maxlength="<?= ComentarioRespuestas::MAX_CHARS ?>" placeholder="Contestarle a <?= htmlspecialchars($alumno) ?> en este hilo...">
                <button type="submit" title="Contestar en el hilo">↩</button>
            </form>
            <?php endif; ?>
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
    render_section_comments('evolucion', 'Evolución del alumno', (string) $attendance['nota'], $attendanceComments['evolucion'],
        $hilos, $puedeResponder, (string) $student['display_name']);
    render_section_comments('procedimiento', 'Procedimiento', (string) $appointment['procedimiento'], $attendanceComments['procedimiento'],
        $hilos, $puedeResponder, (string) $student['display_name']);
}
?>

<?php faltas_graves_recuadro(FaltasGraves::deAtenciones($studentId, [$appointmentId])[$appointmentId] ?? [], true); ?>

<?php $tecnica = AudiometriaTecnica::paraAtencion($appointmentId, $studentId); ?>
<?php if ($tecnica !== null): ?>
<div class="card section-panel" id="tecnica">
    <h3>Técnica de audiometría</h3>
    <p class="help">Comparada con las técnicas T00-T02 de la <a href="bibliografia.php#tecnicas">Bibliografía</a>, con los valores del curso. El alumno ve lo mismo en su atención, sin los umbrales del paciente.</p>
    <?php AudiometriaTecnicaVista::render($tecnica, true); ?>
</div>
<?php endif; ?>

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
                <?php
                // Quién habló: en un caso con acompañantes la misma
                // conversación tiene varias voces. Las filas anteriores al
                // chat grupal no traen etiqueta y siguen diciendo "Paciente".
                $hablante = trim((string) ($turn['speaker_label'] ?? '')) ?: 'Paciente';
                ?>
                <?php if ($role === 'assistant'): ?>
                <div class="avatar a-assistant" title="<?= htmlspecialchars($hablante) ?>"><?= htmlspecialchars(chat_initials($hablante)) ?></div>
                <?php endif; ?>
                <div class="chat-turn <?= $role ?>">
                    <span class="chat-meta"><?= htmlspecialchars($role === 'assistant' ? $hablante : 'Alumno') ?> · <?= htmlspecialchars($turn['created_at']) ?></span>
                    <?= htmlspecialchars($turn['content']) ?>
                </div>
                <?php if ($role === 'user'): ?>
                <div class="avatar a-user" title="Alumno"><?= htmlspecialchars(chat_initials($student['display_name'])) ?></div>
                <?php endif; ?>
            </div>
            <div class="comment-col">
                <?php foreach ($turnComments as $c): ?>
                <div class="comment-bubble" id="turno-<?= (int) $c['id'] ?>">
                    <div class="avatar a-teacher" title="Docente"><?= htmlspecialchars(chat_initials($c['teacher_name'])) ?></div>
                    <div class="comment-body"><span class="chat-meta"><?= htmlspecialchars($c['teacher_name']) ?> · <?= htmlspecialchars($c['created_at']) ?></span><?= htmlspecialchars($c['comment']) ?></div>
                    <?php acciones_comentario('chat', (int) $c['id'], (int) $c['teacher_id'], (string) $c['comment'], 'turno-' . (int) $c['id']); ?>
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
