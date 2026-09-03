<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Mensajes que el docente/admin manda a mano a la bandeja de entrada del
 * alumno (tabla inbox_messages, tipo 'mensaje') -- para avisos de curso, o
 * simplemente para probar cómo se ve la bandeja sin tener que cerrar una
 * atención real y esperar al veredicto del LLM (ver OirsEvaluator.php).
 * Mismo scoping que courses.php: el admin completo ve/manda a cualquier
 * curso, un docente solo a los suyos.
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$myCourseIds = $isFullAdmin ? null : Courses::teacherCourseIds((int) $me['id']);

$courses = $isFullAdmin
    ? Courses::listActive()
    : array_filter(Courses::listActive(), fn (array $c) => in_array((int) $c['id'], $myCourseIds, true));

$error = null;
$success = null;

function require_course_access_inbox(int $courseId, bool $isFullAdmin, ?array $myCourseIds): void
{
    if ($isFullAdmin) {
        return;
    }
    if ($myCourseIds === null || !in_array($courseId, $myCourseIds, true)) {
        http_response_code(403);
        exit('No tienes acceso a este curso.');
    }
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $courseId = (int) ($_POST['course_id'] ?? 0);
    require_course_access_inbox($courseId, $isFullAdmin, $myCourseIds);

    $asunto = trim((string) ($_POST['asunto'] ?? ''));
    $cuerpo = trim((string) ($_POST['cuerpo'] ?? ''));
    $roster = Courses::students($courseId);
    $rosterIds = array_column($roster, 'id');

    $todos = !empty($_POST['todos']);
    $selectedIds = array_map('intval', (array) ($_POST['student_ids'] ?? []));
    // Nunca confiar en los ids tal cual vienen del form -- solo alumnos que
    // de verdad están matriculados en ESTE curso (mismo courseId ya validado
    // arriba), para que nadie mande un mensaje a un student_id ajeno editando el POST.
    $targetIds = $todos ? $rosterIds : array_values(array_intersect($rosterIds, $selectedIds));

    if ($asunto === '' || $cuerpo === '') {
        $error = 'Falta el asunto o el cuerpo del mensaje.';
    } elseif (!$targetIds) {
        $error = 'Selecciona al menos un alumno (o "Todo el curso").';
    } else {
        $remitente = 'Docente ' . $me['display_name'];
        $stmt = $pdo->prepare(
            'INSERT INTO inbox_messages (student_id, tipo, remitente, asunto, cuerpo, sender_admin_id)
             VALUES (?, ?, ?, ?, ?, ?)'
        );
        foreach ($targetIds as $studentId) {
            $stmt->execute([$studentId, 'mensaje', $remitente, $asunto, $cuerpo, $me['id']]);
        }
        $success = 'Mensaje enviado a ' . count($targetIds) . ' alumno(s).';
        AdminAudit::log($me, 'inbox_send', [
            'course_id' => $courseId, 'asunto' => $asunto, 'n_alumnos' => count($targetIds), 'todos' => $todos,
        ]);
    }
}

$selectedCourseId = (int) ($_POST['course_id'] ?? $_GET['course_id'] ?? 0);
if ($selectedCourseId <= 0 && $courses) {
    $selectedCourseId = (int) reset($courses)['id'];
}
if ($selectedCourseId > 0) {
    require_course_access_inbox($selectedCourseId, $isFullAdmin, $myCourseIds);
}
$roster = $selectedCourseId > 0 ? Courses::students($selectedCourseId) : [];

admin_header('Bandeja de entrada', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <strong>Enviar mensaje</strong>
    <p style="font-size:0.85rem; color:#555;">
        Llega a la misma bandeja de entrada donde el alumno ve los avisos automáticos sobre el trato a
        pacientes (ver <a href="llm.php">Admin → IA Paciente</a>) -- útil para avisos de curso, o para
        probar cómo se ve la bandeja sin esperar a que un alumno cierre una atención de verdad.
    </p>
    <?php if (!$courses): ?>
    <p class="legend">No tienes cursos todavía -- créalos o pide que te agreguen en <a href="courses.php">Cursos</a>.</p>
    <?php else: ?>
    <form method="get" style="margin-bottom:0.5rem;">
        <label>Curso
            <select name="course_id" onchange="this.form.submit()">
                <?php foreach ($courses as $c): ?>
                <option value="<?= (int) $c['id'] ?>" <?= (int) $c['id'] === $selectedCourseId ? 'selected' : '' ?>><?= htmlspecialchars($c['name']) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
    </form>

    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="course_id" value="<?= $selectedCourseId ?>">

        <label style="display:flex; align-items:center; gap:0.5rem; font-weight:600;">
            <input type="checkbox" name="todos" value="1" id="chk-todos" style="width:auto;">
            Todo el curso (<?= count($roster) ?> alumno<?= count($roster) === 1 ? '' : 's' ?>)
        </label>

        <div id="roster-box" style="max-height:14rem; overflow-y:auto; border:1px solid #e5e5e5; border-radius:6px; padding:0.5rem; margin-top:0.4rem;">
            <?php foreach ($roster as $r): ?>
            <label class="inline-check" style="display:block; font-weight:400;">
                <input type="checkbox" name="student_ids[]" value="<?= (int) $r['id'] ?>" class="chk-alumno">
                <?= htmlspecialchars($r['display_name']) ?> <span class="mono" style="font-size:0.75rem; color:#888;">(<?= htmlspecialchars($r['username']) ?>)</span>
            </label>
            <?php endforeach; ?>
            <?php if (!$roster): ?>
            <p class="legend">Este curso no tiene alumnos matriculados todavía.</p>
            <?php endif; ?>
        </div>

        <label>Asunto
            <input type="text" name="asunto" placeholder="Ej: Recordatorio de la próxima clase" required>
        </label>
        <label>Mensaje
            <textarea name="cuerpo" rows="6" style="width:100%; padding:0.45rem; margin-top:0.2rem; border:1px solid #ccc; border-radius:4px;" required></textarea>
        </label>

        <button type="submit">Enviar</button>
    </form>

    <script>
        (function () {
            var chkTodos = document.getElementById('chk-todos');
            var box = document.getElementById('roster-box');
            if (!chkTodos || !box) return;
            function sync() {
                box.querySelectorAll('.chk-alumno').forEach(function (el) {
                    el.disabled = chkTodos.checked;
                });
                box.style.opacity = chkTodos.checked ? '0.5' : '1';
            }
            chkTodos.addEventListener('change', sync);
            sync();
        })();
    </script>
    <?php endif; ?>
</div>
<?php
admin_footer();
