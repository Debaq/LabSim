<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Mensajes que el docente/admin manda a mano a la bandeja de entrada
 * (tabla inbox_messages, tipo 'mensaje') -- para avisos de curso, o
 * simplemente para probar cómo se ve la bandeja sin tener que cerrar una
 * atención real y esperar al veredicto del LLM (ver OirsEvaluator.php).
 * Mismo scoping que courses.php: el admin completo ve/manda a cualquier
 * curso, un docente solo a los suyos.
 *
 * Destinatario puede ser un alumno del curso (individual/grupo/todos) o
 * otro docente adscrito al MISMO curso (individual/todos) -- la columna
 * inbox_messages.student_id acepta cualquier user_id, así que el mismo
 * buzón sirve para ambos casos (lo lee cualquier rol vía requireUser()).
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

if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['accion'] ?? '') === 'marcar_leido') {
    Auth::requireCsrf();
    $id = (int) ($_POST['id'] ?? 0);
    // student_id = $me['id'] en el WHERE -- basta para que nadie marque
    // como leído un mensaje ajeno editando el id, sin necesitar más checks.
    $pdo->prepare('UPDATE inbox_messages SET leido = 1 WHERE id = ? AND student_id = ?')
        ->execute([$id, (int) $me['id']]);
    $backTo = (int) ($_POST['course_id'] ?? 0);
    $backPagina = max(1, (int) ($_POST['pagina'] ?? 1));
    $qs = array_filter(['course_id' => $backTo ?: null, 'pagina' => $backPagina > 1 ? $backPagina : null]);
    header('Location: inbox_send.php' . ($qs ? '?' . http_build_query($qs) : ''));
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $courseId = (int) ($_POST['course_id'] ?? 0);
    require_course_access_inbox($courseId, $isFullAdmin, $myCourseIds);

    $asunto = trim((string) ($_POST['asunto'] ?? ''));
    $cuerpo = trim((string) ($_POST['cuerpo'] ?? ''));
    $destinatario = (string) ($_POST['destinatario'] ?? 'alumno');
    $modo = (string) ($_POST['modo'] ?? 'individual');

    // Nunca confiar en los ids/grupo tal cual vienen del form -- solo
    // alumnos/docentes que de verdad pertenecen a ESTE curso (mismo courseId
    // ya validado arriba), para que nadie mande un mensaje a un user_id o
    // grupo ajeno editando el POST.
    if ($destinatario === 'docente') {
        $teachers = array_filter(Courses::teachers($courseId), fn (array $t) => (int) $t['id'] !== (int) $me['id']);
        $teacherIds = array_column($teachers, 'id');
        if (!empty($_POST['todos_docentes'])) {
            $targetIds = $teacherIds;
        } else {
            $selectedIds = array_map('intval', (array) ($_POST['teacher_ids'] ?? []));
            $targetIds = array_values(array_intersect($teacherIds, $selectedIds));
        }
    } else {
        $roster = Courses::students($courseId);
        $rosterIds = array_column($roster, 'id');
        if ($modo === 'todos') {
            $targetIds = $rosterIds;
        } elseif ($modo === 'grupo') {
            $grupoId = (int) ($_POST['grupo_id'] ?? 0);
            $stmt = $pdo->prepare('SELECT 1 FROM student_groups WHERE id = ? AND course_id = ?');
            $stmt->execute([$grupoId, $courseId]);
            $grupoIds = $stmt->fetch() ? array_column(Courses::membersOfGroup($grupoId), 'id') : [];
            $targetIds = array_values(array_intersect($rosterIds, $grupoIds));
        } else {
            $selectedIds = array_map('intval', (array) ($_POST['student_ids'] ?? []));
            $targetIds = array_values(array_intersect($rosterIds, $selectedIds));
        }
    }

    if ($asunto === '' || $cuerpo === '') {
        $error = 'Falta el asunto o el cuerpo del mensaje.';
    } elseif (!$targetIds) {
        $error = $destinatario === 'docente'
            ? 'Selecciona al menos un docente (o "Todos los docentes").'
            : 'Selecciona al menos un alumno (o "Todo el curso", o un grupo).';
    } else {
        $remitente = ($me['permission'] === Auth::PERMISSION_ADMIN ? 'Admin ' : 'Docente ') . $me['display_name'];
        $stmt = $pdo->prepare(
            'INSERT INTO inbox_messages (student_id, tipo, remitente, asunto, cuerpo, sender_admin_id)
             VALUES (?, ?, ?, ?, ?, ?)'
        );
        foreach ($targetIds as $userId) {
            $stmt->execute([$userId, 'mensaje', $remitente, $asunto, $cuerpo, $me['id']]);
        }
        $success = 'Mensaje enviado a ' . count($targetIds) . ' ' . ($destinatario === 'docente' ? 'docente(s)' : 'alumno(s)') . '.';
        AdminAudit::log($me, 'inbox_send', [
            'course_id' => $courseId, 'asunto' => $asunto, 'n_destinatarios' => count($targetIds),
            'destinatario' => $destinatario,
            'modo' => $destinatario === 'docente' ? (!empty($_POST['todos_docentes']) ? 'todos' : 'individual') : $modo,
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
$grupos = $selectedCourseId > 0 ? Courses::groupsForCourse($selectedCourseId) : [];
$teachers = $selectedCourseId > 0
    ? array_values(array_filter(Courses::teachers($selectedCourseId), fn (array $t) => (int) $t['id'] !== (int) $me['id']))
    : [];

// Lo que a MÍ me han mandado -- avisos automáticos de OirsEvaluator y
// mensajes de otros docentes/admin (esta misma página). El cliente de
// escritorio también los lee (ver core/inbox.py -> api/inbox.php), pero ese
// usa token propio (Auth::requireUser) y esta página usa sesión de admin,
// así que necesita su propia lectura.
//
// Paginado (POR_PAGINA + 1 para saber si hay página siguiente sin un
// segundo COUNT(*)) -- el contador de no leídos es una query aparte, sin
// límite, porque un mensaje sin leer viejo no debe desaparecer del badge
// solo por quedar fuera de la página actual.
const INBOX_POR_PAGINA = 50;
$pagina = max(1, (int) ($_GET['pagina'] ?? 1));
$offset = ($pagina - 1) * INBOX_POR_PAGINA;

$stmtNoLeidos = $pdo->prepare('SELECT COUNT(*) FROM inbox_messages WHERE student_id = ? AND leido = 0');
$stmtNoLeidos->execute([(int) $me['id']]);
$noLeidos = (int) $stmtNoLeidos->fetchColumn();

$stmtRecibidos = $pdo->prepare(
    "SELECT * FROM inbox_messages WHERE student_id = ? ORDER BY created_at DESC LIMIT " . (INBOX_POR_PAGINA + 1) . ' OFFSET ?'
);
$stmtRecibidos->execute([(int) $me['id'], $offset]);
$misMensajes = $stmtRecibidos->fetchAll();
$hayPaginaSiguiente = count($misMensajes) > INBOX_POR_PAGINA;
$misMensajes = array_slice($misMensajes, 0, INBOX_POR_PAGINA);

// Lo que YO he mandado (esta página, avisos manuales) -- cada envío a N
// destinatarios queda como N filas (mismo asunto/cuerpo/created_at, distinto
// student_id), así que se agrupan por lote para mostrar un solo renglón por
// envío con la lista de destinatarios y cuántos lo han leído.
$stmtEnviados = $pdo->prepare(
    "SELECT m.asunto, m.cuerpo, m.created_at, COUNT(*) AS n_destinatarios,
            SUM(m.leido) AS n_leidos, GROUP_CONCAT(u.display_name, ', ') AS destinatarios
     FROM inbox_messages m
     JOIN users u ON u.id = m.student_id
     WHERE m.sender_admin_id = ? AND m.tipo = 'mensaje'
     GROUP BY m.asunto, m.cuerpo, m.created_at
     ORDER BY m.created_at DESC
     LIMIT 50"
);
$stmtEnviados->execute([(int) $me['id']]);
$misEnvios = $stmtEnviados->fetchAll();

admin_header('Bandeja de entrada', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <strong>Mensajes recibidos<?= $noLeidos > 0 ? " ({$noLeidos} sin leer)" : '' ?></strong>
    <?php if (!$misMensajes): ?>
    <p class="legend">Sin mensajes todavía.</p>
    <?php else: ?>
    <div style="max-height:24rem; overflow-y:auto; margin-top:0.5rem;">
        <?php foreach ($misMensajes as $m): ?>
        <details style="border:1px solid #e5e5e5; border-radius:6px; padding:0.4rem 0.6rem; margin-bottom:0.4rem;" <?= !$m['leido'] ? 'open' : '' ?>>
            <summary style="cursor:pointer; <?= !$m['leido'] ? 'font-weight:700;' : '' ?>">
                <?= !$m['leido'] ? '● ' : '' ?><?= htmlspecialchars($m['asunto']) ?>
                <span class="legend" style="font-weight:400;">-- <?= htmlspecialchars($m['remitente'] ?: 'Sistema') ?>, <?= htmlspecialchars($m['created_at']) ?></span>
            </summary>
            <p style="white-space:pre-wrap; margin:0.5rem 0 0.3rem;"><?= htmlspecialchars($m['cuerpo']) ?></p>
            <?php if (!$m['leido']): ?>
            <form method="post" style="margin:0;">
                <?= csrf_field() ?>
                <input type="hidden" name="accion" value="marcar_leido">
                <input type="hidden" name="id" value="<?= (int) $m['id'] ?>">
                <input type="hidden" name="course_id" value="<?= $selectedCourseId ?>">
                <input type="hidden" name="pagina" value="<?= $pagina ?>">
                <button type="submit" style="font-size:0.8rem; padding:0.2rem 0.6rem;">Marcar leído</button>
            </form>
            <?php endif; ?>
        </details>
        <?php endforeach; ?>
    </div>
    <div style="display:flex; justify-content:space-between; margin-top:0.5rem;">
        <?php if ($pagina > 1): ?>
        <a href="?pagina=<?= $pagina - 1 ?><?= $selectedCourseId > 0 ? '&course_id=' . $selectedCourseId : '' ?>">« Más recientes</a>
        <?php else: ?><span></span><?php endif; ?>
        <?php if ($hayPaginaSiguiente): ?>
        <a href="?pagina=<?= $pagina + 1 ?><?= $selectedCourseId > 0 ? '&course_id=' . $selectedCourseId : '' ?>">Más antiguos »</a>
        <?php endif; ?>
    </div>
    <?php endif; ?>
</div>

<div class="card">
    <strong>Mensajes enviados</strong>
    <?php if (!$misEnvios): ?>
    <p class="legend">Todavía no has mandado mensajes.</p>
    <?php else: ?>
    <div style="max-height:24rem; overflow-y:auto; margin-top:0.5rem;">
        <?php foreach ($misEnvios as $e): ?>
        <details style="border:1px solid #e5e5e5; border-radius:6px; padding:0.4rem 0.6rem; margin-bottom:0.4rem;">
            <summary style="cursor:pointer;">
                <?= htmlspecialchars($e['asunto']) ?>
                <span class="legend" style="font-weight:400;">
                    -- <?= (int) $e['n_destinatarios'] ?> destinatario<?= (int) $e['n_destinatarios'] === 1 ? '' : 's' ?>
                    (<?= (int) $e['n_leidos'] ?> leído<?= (int) $e['n_leidos'] === 1 ? '' : 's' ?>), <?= htmlspecialchars($e['created_at']) ?>
                </span>
            </summary>
            <p style="white-space:pre-wrap; margin:0.5rem 0 0.3rem;"><?= htmlspecialchars($e['cuerpo']) ?></p>
            <p class="legend" style="margin:0;">Para: <?= htmlspecialchars($e['destinatarios']) ?></p>
        </details>
        <?php endforeach; ?>
    </div>
    <?php endif; ?>
</div>

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

        <div style="display:flex; gap:1.2rem; margin-bottom:0.4rem;">
            <label style="display:flex; align-items:center; gap:0.4rem; font-weight:600;">
                <input type="radio" name="destinatario" value="alumno" id="dest-alumno" style="width:auto;" checked>
                Alumnos
            </label>
            <label style="display:flex; align-items:center; gap:0.4rem; font-weight:600;">
                <input type="radio" name="destinatario" value="docente" id="dest-docente" style="width:auto;" <?= !$teachers ? 'disabled' : '' ?>>
                Otros docentes del curso
            </label>
        </div>

        <div id="bloque-alumnos">
        <div style="display:flex; flex-direction:column; gap:0.3rem;">
            <label style="display:flex; align-items:center; gap:0.5rem; font-weight:600;">
                <input type="radio" name="modo" value="individual" id="modo-individual" style="width:auto;" checked>
                Alumnos individuales
            </label>
            <label style="display:flex; align-items:center; gap:0.5rem; font-weight:600;">
                <input type="radio" name="modo" value="grupo" id="modo-grupo" style="width:auto;" <?= !$grupos ? 'disabled' : '' ?>>
                Grupo
                <select name="grupo_id" id="sel-grupo" <?= !$grupos ? 'disabled' : '' ?>>
                    <?php foreach ($grupos as $g): ?>
                    <option value="<?= (int) $g['id'] ?>"><?= htmlspecialchars($g['name']) ?> (<?= (int) $g['member_count'] ?>)</option>
                    <?php endforeach; ?>
                </select>
                <?php if (!$grupos): ?><span class="legend">Este curso no tiene grupos todavía.</span><?php endif; ?>
            </label>
            <label style="display:flex; align-items:center; gap:0.5rem; font-weight:600;">
                <input type="radio" name="modo" value="todos" id="modo-todos" style="width:auto;">
                Todo el curso (<?= count($roster) ?> alumno<?= count($roster) === 1 ? '' : 's' ?>)
            </label>
        </div>

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
        </div>

        <div id="bloque-docentes" style="display:none;">
            <label style="display:flex; align-items:center; gap:0.5rem; font-weight:600;">
                <input type="checkbox" name="todos_docentes" value="1" id="chk-todos-docentes" style="width:auto;">
                Todos los docentes del curso (<?= count($teachers) ?>)
            </label>
            <div id="teacher-box" style="max-height:14rem; overflow-y:auto; border:1px solid #e5e5e5; border-radius:6px; padding:0.5rem; margin-top:0.4rem;">
                <?php foreach ($teachers as $t): ?>
                <label class="inline-check" style="display:block; font-weight:400;">
                    <input type="checkbox" name="teacher_ids[]" value="<?= (int) $t['id'] ?>" class="chk-docente">
                    <?= htmlspecialchars($t['display_name']) ?> <span class="mono" style="font-size:0.75rem; color:#888;">(<?= htmlspecialchars($t['username']) ?>)</span>
                </label>
                <?php endforeach; ?>
                <?php if (!$teachers): ?>
                <p class="legend">No hay otros docentes en este curso todavía.</p>
                <?php endif; ?>
            </div>
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
            var radios = document.querySelectorAll('input[name="modo"]');
            var box = document.getElementById('roster-box');
            var selGrupo = document.getElementById('sel-grupo');
            if (radios.length && box) {
                function modoActivo() {
                    var checked = document.querySelector('input[name="modo"]:checked');
                    return checked ? checked.value : 'individual';
                }
                function syncAlumnos() {
                    var modo = modoActivo();
                    var esIndividual = modo === 'individual';
                    box.querySelectorAll('.chk-alumno').forEach(function (el) {
                        el.disabled = !esIndividual;
                    });
                    box.style.opacity = esIndividual ? '1' : '0.5';
                    if (selGrupo) selGrupo.disabled = modo !== 'grupo' || selGrupo.options.length === 0;
                }
                radios.forEach(function (r) { r.addEventListener('change', syncAlumnos); });
                if (selGrupo) selGrupo.addEventListener('focus', function () {
                    document.getElementById('modo-grupo').checked = true;
                    syncAlumnos();
                });
                syncAlumnos();
            }

            var destRadios = document.querySelectorAll('input[name="destinatario"]');
            var bloqueAlumnos = document.getElementById('bloque-alumnos');
            var bloqueDocentes = document.getElementById('bloque-docentes');
            var chkTodosDocentes = document.getElementById('chk-todos-docentes');
            var teacherBox = document.getElementById('teacher-box');
            if (destRadios.length && bloqueAlumnos && bloqueDocentes) {
                function syncDestinatario() {
                    var checked = document.querySelector('input[name="destinatario"]:checked');
                    var esDocente = checked && checked.value === 'docente';
                    bloqueAlumnos.style.display = esDocente ? 'none' : '';
                    bloqueDocentes.style.display = esDocente ? '' : 'none';
                }
                destRadios.forEach(function (r) { r.addEventListener('change', syncDestinatario); });
                syncDestinatario();
            }
            if (chkTodosDocentes && teacherBox) {
                function syncDocentes() {
                    teacherBox.querySelectorAll('.chk-docente').forEach(function (el) {
                        el.disabled = chkTodosDocentes.checked;
                    });
                    teacherBox.style.opacity = chkTodosDocentes.checked ? '0.5' : '1';
                }
                chkTodosDocentes.addEventListener('change', syncDocentes);
                syncDocentes();
            }
        })();
    </script>
    <?php endif; ?>
</div>
<?php
admin_footer();
