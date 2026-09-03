<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Cursos: separa alumnos/docentes/casos de cursos distintos que antes iban
 * todos al mismo fondo común (ver comentario en sql/schema.sql sobre
 * `courses`). El admin completo ve/crea cualquier curso; un docente entra
 * directo al detalle del/los suyo(s) -- nunca ve la lista global ni cursos
 * ajenos (mismo criterio de scoping que agenda.php/dashboard.php/student.php).
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$myCourseIds = $isFullAdmin ? null : Courses::teacherCourseIds((int) $me['id']);

$error = null;
$success = null;
$bulkResults = [];

/** Corta la request si $courseId no es un curso que $me pueda administrar. */
function require_course_access(int $courseId, bool $isFullAdmin, ?array $myCourseIds): void
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
    $action = (string) ($_POST['form_action'] ?? '');
    $courseId = (int) ($_POST['course_id'] ?? 0);

    if ($action === 'create_course') {
        if (!$isFullAdmin) {
            http_response_code(403);
            exit('Requiere permisos de administrador completo.');
        }
        $name = trim((string) ($_POST['name'] ?? ''));
        if ($name === '') {
            $error = 'Falta el nombre del curso.';
        } else {
            $courseId = Courses::create($name);
            AdminAudit::log($me, 'course_create', ['course_id' => $courseId, 'name' => $name]);
            header('Location: courses.php?id=' . $courseId);
            exit;
        }
    } elseif ($courseId > 0) {
        require_course_access($courseId, $isFullAdmin, $myCourseIds);

        if ($action === 'rename_course' && $isFullAdmin) {
            $name = trim((string) ($_POST['name'] ?? ''));
            if ($name !== '') {
                Courses::rename($courseId, $name);
                $success = 'Curso actualizado.';
                AdminAudit::log($me, 'course_rename', ['course_id' => $courseId, 'name' => $name]);
            }
        } elseif ($action === 'toggle_active' && $isFullAdmin) {
            $course = Courses::find($courseId);
            if ($course) {
                Courses::setActive($courseId, !$course['active']);
                $success = $course['active'] ? 'Curso archivado.' : 'Curso activado.';
                AdminAudit::log($me, $course['active'] ? 'course_archive' : 'course_activate', ['course_id' => $courseId]);
            }
        } elseif ($action === 'add_teacher' && $isFullAdmin) {
            $username = trim((string) ($_POST['username'] ?? ''));
            $err = Courses::addMemberByUsername($courseId, $username, 'teacher');
            if ($err) {
                $error = $err;
            } else {
                $success = 'Docente agregado.';
                AdminAudit::log($me, 'course_add_teacher', ['course_id' => $courseId, 'username' => $username]);
            }
        } elseif ($action === 'remove_teacher' && $isFullAdmin) {
            $teacherId = (int) ($_POST['user_id'] ?? 0);
            Courses::removeTeacher($courseId, $teacherId);
            $success = 'Docente quitado del curso.';
            AdminAudit::log($me, 'course_remove_teacher', ['course_id' => $courseId, 'user_id' => $teacherId]);
        } elseif ($action === 'add_student') {
            $username = trim((string) ($_POST['username'] ?? ''));
            $displayName = trim((string) ($_POST['display_name'] ?? ''));
            $result = Courses::addOrCreateStudentByUsername($courseId, $username, $displayName);
            if ($result['status'] === 'error') {
                $error = $result['message'];
            } else {
                $success = $result['status'] === 'created'
                    ? "Alumno '{$username}' creado y matriculado. Contraseña temporal: {$result['password']}"
                    : 'Alumno agregado al curso.';
                AdminAudit::log($me, 'course_add_student', ['course_id' => $courseId, 'username' => $username, 'status' => $result['status']]);
            }
        } elseif ($action === 'bulk_add_students') {
            $raw = (string) ($_POST['bulk_students'] ?? '');
            $bulkResults = Courses::bulkAddStudents($courseId, $raw);
            $created = count(array_filter($bulkResults, fn($r) => $r['status'] === 'created'));
            $enrolled = count(array_filter($bulkResults, fn($r) => $r['status'] === 'enrolled'));
            $errors = count(array_filter($bulkResults, fn($r) => $r['status'] === 'error'));
            $success = "{$created} cuenta(s) creada(s), {$enrolled} matriculado(s), {$errors} error(es).";
            AdminAudit::log($me, 'course_bulk_add_students', ['course_id' => $courseId, 'created' => $created, 'enrolled' => $enrolled, 'errors' => $errors]);
        } elseif ($action === 'remove_student') {
            $studentId = (int) ($_POST['user_id'] ?? 0);
            Courses::removeStudent($courseId, $studentId);
            $success = 'Alumno quitado del curso.';
            AdminAudit::log($me, 'course_remove_student', ['course_id' => $courseId, 'user_id' => $studentId]);
        } elseif ($action === 'create_group') {
            $name = trim((string) ($_POST['name'] ?? ''));
            if ($name === '') {
                $error = 'Falta el nombre del grupo.';
            } else {
                Courses::createGroup($courseId, $name);
                $success = 'Grupo creado.';
                AdminAudit::log($me, 'group_create', ['course_id' => $courseId, 'name' => $name]);
            }
        } elseif ($action === 'delete_group') {
            $groupId = (int) ($_POST['group_id'] ?? 0);
            Courses::deleteGroup($groupId);
            $success = 'Grupo eliminado.';
            AdminAudit::log($me, 'group_delete', ['course_id' => $courseId, 'group_id' => $groupId]);
        } elseif ($action === 'add_group_member') {
            $groupId = (int) ($_POST['group_id'] ?? 0);
            $username = trim((string) ($_POST['username'] ?? ''));
            $err = Courses::addGroupMemberByUsername($groupId, $courseId, $username);
            if ($err) {
                $error = $err;
            } else {
                $success = 'Miembro agregado al grupo.';
                AdminAudit::log($me, 'group_add_member', ['course_id' => $courseId, 'group_id' => $groupId, 'username' => $username]);
            }
        } elseif ($action === 'bulk_enroll_selected') {
            $userIds = array_map('intval', (array) ($_POST['user_ids'] ?? []));
            $n = Courses::enrollExistingUsers($courseId, $userIds);
            $success = "{$n} alumno(s) matriculado(s).";
            AdminAudit::log($me, 'course_bulk_enroll', ['course_id' => $courseId, 'count' => $n]);
        } elseif ($action === 'link_lti_context') {
            $platformId = (int) ($_POST['lti_platform_id'] ?? 0);
            $ltiContextId = trim((string) ($_POST['lti_context_id'] ?? ''));
            if ($platformId <= 0 || $ltiContextId === '') {
                $error = 'Datos de vínculo inválidos.';
            } else {
                Lti::linkContextToCourse($platformId, $ltiContextId, $courseId);
                $success = 'Curso de Moodle vinculado -- los alumnos que entren por ahí se matricularán solos.';
                AdminAudit::log($me, 'course_link_lti_context', ['course_id' => $courseId, 'lti_platform_id' => $platformId, 'context_id' => $ltiContextId]);
            }
        } elseif ($action === 'remove_group_member') {
            $groupId = (int) ($_POST['group_id'] ?? 0);
            $userId = (int) ($_POST['user_id'] ?? 0);
            Courses::removeGroupMember($groupId, $userId);
            $success = 'Miembro quitado del grupo.';
            AdminAudit::log($me, 'group_remove_member', ['course_id' => $courseId, 'group_id' => $groupId, 'user_id' => $userId]);
        }
    }
}

$detailId = isset($_GET['id']) && $_GET['id'] !== '' ? (int) $_GET['id'] : null;

// Docente sin id en la URL: si tiene un solo curso, entra directo a su
// detalle -- salvo que venga a vincular un contexto LTI (ver bloque
// "link_lti_context" más abajo), que necesita la vista de lista para
// mostrar el selector de curso.
$pendingLinkPlatform = (int) ($_GET['link_platform'] ?? 0);
$pendingLinkContext = (string) ($_GET['link_context'] ?? '');
$hasPendingLink = $pendingLinkPlatform > 0 && $pendingLinkContext !== '';

if ($detailId === null && !$isFullAdmin && $myCourseIds && count($myCourseIds) === 1 && !$hasPendingLink) {
    $detailId = $myCourseIds[0];
}

if ($detailId !== null) {
    require_course_access($detailId, $isFullAdmin, $myCourseIds);
    $course = Courses::find($detailId);
    if (!$course) {
        admin_header('Curso', $me);
        echo '<p class="error">Curso no encontrado.</p>';
        admin_footer();
        exit;
    }

    $studentOptions = $pdo->query(
        "SELECT username, display_name FROM users WHERE role = 'student' AND active = 1 ORDER BY display_name"
    )->fetchAll();
    $teacherOptions = $isFullAdmin
        ? $pdo->query(
            "SELECT username, display_name FROM users WHERE role = 'admin' AND active = 1 ORDER BY display_name"
        )->fetchAll()
        : [];

    admin_header('Curso: ' . $course['name'], $me);
    ?>
    <datalist id="students_datalist">
        <?php foreach ($studentOptions as $u): ?>
        <option value="<?= htmlspecialchars($u['username']) ?>"><?= htmlspecialchars($u['display_name']) ?></option>
        <?php endforeach; ?>
    </datalist>
    <?php if ($isFullAdmin): ?>
    <datalist id="teachers_datalist">
        <?php foreach ($teacherOptions as $u): ?>
        <option value="<?= htmlspecialchars($u['username']) ?>"><?= htmlspecialchars($u['display_name']) ?></option>
        <?php endforeach; ?>
    </datalist>
    <?php endif; ?>
    <?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
    <?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

    <?php if ($isFullAdmin): ?>
    <p><a href="courses.php">&larr; Todos los cursos</a></p>
    <?php endif; ?>

    <div class="card">
        <strong><?= htmlspecialchars($course['name']) ?></strong>
        &nbsp;·&nbsp; <?= $course['active'] ? 'activo' : 'archivado' ?>
        <?php if ($isFullAdmin): ?>
        <details style="margin-top:0.6rem;">
            <summary>Editar</summary>
            <form method="post" style="margin-top:0.4rem;">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="rename_course">
                <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                <label>Nombre
                    <input type="text" name="name" value="<?= htmlspecialchars($course['name']) ?>" required>
                </label>
                <button type="submit" class="secondary">Guardar</button>
            </form>
            <form method="post" class="inline" style="margin-top:0.6rem;">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="toggle_active">
                <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                <button type="submit" class="secondary"><?= $course['active'] ? 'Archivar curso' : 'Activar curso' ?></button>
            </form>
        </details>
        <?php endif; ?>
    </div>

    <?php if ($isFullAdmin): ?>
    <div class="card">
        <strong>Docentes (<?= count($teachers = Courses::teachers((int) $course['id'])) ?>)</strong>
        <table>
            <tr><th>Usuario</th><th>Nombre</th><th></th></tr>
            <?php foreach ($teachers as $t): ?>
            <tr>
                <td><?= htmlspecialchars($t['username']) ?></td>
                <td><?= htmlspecialchars($t['display_name']) ?></td>
                <td>
                    <form method="post" class="inline">
                    <?= csrf_field() ?>
                        <input type="hidden" name="form_action" value="remove_teacher">
                        <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                        <input type="hidden" name="user_id" value="<?= $t['id'] ?>">
                        <button type="submit" class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Quitar</button>
                    </form>
                </td>
            </tr>
            <?php endforeach; ?>
            <?php if (!$teachers): ?>
            <tr><td colspan="3" style="color:#888;">Sin docentes asignados todavía.</td></tr>
            <?php endif; ?>
        </table>
        <form method="post" style="display:flex; gap:0.6rem; align-items:flex-end; margin-top:0.6rem;">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="add_teacher">
            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
            <label style="flex:1; margin:0;">Agregar docente (nombre o username)
                <input type="text" name="username" list="teachers_datalist" required>
            </label>
            <button type="submit" class="secondary" style="margin-top:0;">Agregar</button>
        </form>
    </div>
    <?php endif; ?>

    <div class="card">
        <strong>Alumnos matriculados (<?= count($students = Courses::students((int) $course['id'])) ?>)</strong>
        <table>
            <tr><th>Usuario</th><th>Nombre</th><th></th></tr>
            <?php foreach ($students as $s): ?>
            <tr>
                <td><?= htmlspecialchars($s['username']) ?></td>
                <td><a href="student.php?id=<?= $s['id'] ?>"><?= htmlspecialchars($s['display_name']) ?></a></td>
                <td>
                    <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Quitar a ' . $s['username'] . ' del curso? También lo saca de cualquier grupo del curso.'), ENT_QUOTES) ?>);">
                    <?= csrf_field() ?>
                        <input type="hidden" name="form_action" value="remove_student">
                        <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                        <input type="hidden" name="user_id" value="<?= $s['id'] ?>">
                        <button type="submit" class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Quitar</button>
                    </form>
                </td>
            </tr>
            <?php endforeach; ?>
            <?php if (!$students): ?>
            <tr><td colspan="3" style="color:#888;">Sin alumnos matriculados todavía.</td></tr>
            <?php endif; ?>
        </table>

        <?php $enrollable = Courses::enrollableStudents((int) $course['id']); ?>
        <div style="margin-top:0.8rem; border-top:1px solid #e5e5e5; padding-top:0.6rem;">
            <strong>Matricular alumnos existentes</strong>
            <?php if (!$enrollable): ?>
            <p style="color:#888; font-size:0.85rem;">Todos los alumnos activos ya están en este curso.</p>
            <?php else: ?>
            <?php
                $origins = [];
                foreach ($enrollable as $u) {
                    $o = trim((string) ($u['origin'] ?? ''));
                    if ($o !== '') {
                        $origins[$o] = ($origins[$o] ?? 0) + 1;
                    }
                }
                ksort($origins);
            ?>
            <p style="font-size:0.8rem; color:#555;">Busca por nombre o usuario, marca a los que quieras, o usa "seleccionar todos". Si Moodle informó de qué curso vienen, aparecen agrupados abajo -- un clic selecciona a todo ese grupo.</p>
            <input type="text" id="roster_search" placeholder="Buscar por nombre o usuario..." style="width:100%; margin-bottom:0.5rem;" oninput="rosterFilter()">
            <?php if ($origins): ?>
            <div style="margin-bottom:0.5rem;">
                <?php foreach ($origins as $label => $count): ?>
                <button type="button" class="secondary" style="margin:0 0.3rem 0.3rem 0; padding:0.15rem 0.5rem; font-size:0.75rem;" onclick="rosterSelectOrigin(<?= htmlspecialchars(json_encode($label), ENT_QUOTES) ?>)">Todos de "<?= htmlspecialchars($label) ?>" (<?= $count ?>)</button>
                <?php endforeach; ?>
            </div>
            <?php endif; ?>
            <form method="post" id="roster_form">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="bulk_enroll_selected">
                <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                <div style="max-height:320px; overflow-y:auto; border:1px solid #e5e5e5;">
                <table id="roster_table" style="margin:0;">
                    <tr>
                        <th><input type="checkbox" id="roster_select_all" onclick="rosterToggleAll(this)" title="Seleccionar todos los visibles"></th>
                        <th>Usuario</th><th>Nombre</th><th>Origen (Moodle)</th>
                    </tr>
                    <?php foreach ($enrollable as $u): ?>
                    <tr class="roster_row" data-origin="<?= htmlspecialchars((string) ($u['origin'] ?? '')) ?>" data-search="<?= htmlspecialchars(mb_strtolower($u['username'] . ' ' . $u['display_name'] . ' ' . ($u['origin'] ?? ''))) ?>">
                        <td><input type="checkbox" name="user_ids[]" value="<?= $u['id'] ?>" class="roster_check" onchange="rosterUpdateCount()"></td>
                        <td><?= htmlspecialchars($u['username']) ?></td>
                        <td><?= htmlspecialchars($u['display_name']) ?></td>
                        <td style="color:#888; font-size:0.8rem;"><?= htmlspecialchars($u['origin'] ?: '—') ?></td>
                    </tr>
                    <?php endforeach; ?>
                </table>
                </div>
                <button type="submit" class="secondary" style="margin-top:0.5rem;">Matricular seleccionados (<span id="roster_count">0</span>)</button>
            </form>
            <script>
            (function () {
                function rows() { return document.querySelectorAll('#roster_table .roster_row'); }
                window.rosterFilter = function () {
                    var q = document.getElementById('roster_search').value.toLowerCase();
                    rows().forEach(function (row) {
                        row.style.display = row.dataset.search.indexOf(q) === -1 ? 'none' : '';
                    });
                };
                window.rosterSelectOrigin = function (label) {
                    rows().forEach(function (row) {
                        if (row.dataset.origin === label) {
                            row.style.display = '';
                            row.querySelector('.roster_check').checked = true;
                        }
                    });
                    rosterUpdateCount();
                };
                window.rosterToggleAll = function (cb) {
                    rows().forEach(function (row) {
                        if (row.style.display !== 'none') {
                            row.querySelector('.roster_check').checked = cb.checked;
                        }
                    });
                    rosterUpdateCount();
                };
                window.rosterUpdateCount = function () {
                    document.getElementById('roster_count').textContent =
                        document.querySelectorAll('#roster_table .roster_check:checked').length;
                };
            })();
            </script>
            <?php endif; ?>
        </div>

        <details style="margin-top:0.8rem; border-top:1px solid #e5e5e5; padding-top:0.6rem;">
            <summary>Agregar alumno nuevo o sin Moodle (manual)</summary>
            <form method="post" style="display:flex; gap:0.6rem; align-items:flex-end; margin-top:0.6rem; flex-wrap:wrap;">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="add_student">
                <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                <label style="flex:1; margin:0; min-width:220px;">Agregar alumno (nombre o username)
                    <input type="text" name="username" list="students_datalist" required>
                </label>
                <label style="flex:1; margin:0; min-width:220px;">Nombre completo (solo si es alumno nuevo)
                    <input type="text" name="display_name" placeholder="Se usa si el username no existe todavía">
                </label>
                <button type="submit" class="secondary" style="margin-top:0;">Agregar</button>
            </form>
            <p style="font-size:0.8rem; color:#888; margin-top:0.4rem;">Si el username no existe todavía, se crea una cuenta nueva automáticamente con contraseña temporal (se muestra al agregar).</p>

            <details style="margin-top:0.8rem; border-top:1px solid #e5e5e5; padding-top:0.6rem;">
                <summary>Agregar varios alumnos a la vez (por texto)</summary>
                <form method="post" style="margin-top:0.6rem;">
                <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="bulk_add_students">
                    <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                    <label>Uno por línea: <code>username</code>, o <code>username, nombre completo</code>, o <code>username, nombre completo, password</code>
                        <textarea name="bulk_students" rows="6" style="width:100%; font-family:monospace;" placeholder="jperez&#10;mgonzalez, María González&#10;asilva, Ana Silva, MiClave123"></textarea>
                    </label>
                    <p style="font-size:0.8rem; color:#888;">Los que ya existen se matriculan tal cual. Los que no existen se crean con esa contraseña, o con una generada automáticamente si no se indica.</p>
                    <button type="submit" class="secondary">Procesar lista</button>
                </form>
                <?php if ($bulkResults): ?>
                <table style="margin-top:0.8rem;">
                    <tr><th>Username</th><th>Resultado</th><th>Contraseña</th></tr>
                    <?php foreach ($bulkResults as $r): ?>
                    <tr>
                        <td><?= htmlspecialchars($r['username']) ?></td>
                        <td style="color:<?= $r['status'] === 'error' ? '#b00' : '#333' ?>;"><?= htmlspecialchars($r['message']) ?></td>
                        <td><?= !empty($r['password']) ? '<code>' . htmlspecialchars($r['password']) . '</code>' : '' ?></td>
                    </tr>
                    <?php endforeach; ?>
                </table>
                <?php endif; ?>
            </details>
        </details>
    </div>

    <div class="card">
        <strong>Grupos</strong>
        <p style="font-size:0.85rem; color:#555;">Para citar a un subgrupo (p. ej. 5 alumnos a la misma hora) sin asignarlos uno por uno en la agenda.</p>
        <?php foreach (Courses::groupsForCourse((int) $course['id']) as $g): ?>
        <div style="border-top:1px solid #e5e5e5; padding-top:0.8rem; margin-top:0.8rem;">
            <strong><?= htmlspecialchars($g['name']) ?></strong> (<?= (int) $g['member_count'] ?> miembros)
            <form method="post" class="inline" style="margin-left:0.6rem;" onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Eliminar el grupo ' . $g['name'] . '?'), ENT_QUOTES) ?>);">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="delete_group">
                <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                <input type="hidden" name="group_id" value="<?= $g['id'] ?>">
                <button type="submit" class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Eliminar grupo</button>
            </form>
            <table>
                <tr><th>Usuario</th><th>Nombre</th><th></th></tr>
                <?php foreach (Courses::membersOfGroup((int) $g['id']) as $m): ?>
                <tr>
                    <td><?= htmlspecialchars($m['username']) ?></td>
                    <td><?= htmlspecialchars($m['display_name']) ?></td>
                    <td>
                        <form method="post" class="inline">
                        <?= csrf_field() ?>
                            <input type="hidden" name="form_action" value="remove_group_member">
                            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                            <input type="hidden" name="group_id" value="<?= $g['id'] ?>">
                            <input type="hidden" name="user_id" value="<?= $m['id'] ?>">
                            <button type="submit" class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Quitar</button>
                        </form>
                    </td>
                </tr>
                <?php endforeach; ?>
            </table>
            <form method="post" style="display:flex; gap:0.6rem; align-items:flex-end;">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="add_group_member">
                <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                <input type="hidden" name="group_id" value="<?= $g['id'] ?>">
                <label style="flex:1; margin:0;">Agregar al grupo (nombre o username, debe estar matriculado en el curso)
                    <input type="text" name="username" list="students_datalist" required>
                </label>
                <button type="submit" class="secondary" style="margin-top:0;">Agregar</button>
            </form>
        </div>
        <?php endforeach; ?>
        <form method="post" style="display:flex; gap:0.6rem; align-items:flex-end; margin-top:0.8rem; border-top:1px solid #e5e5e5; padding-top:0.8rem;">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="create_group">
            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
            <label style="flex:1; margin:0;">Nuevo grupo (nombre)
                <input type="text" name="name" required>
            </label>
            <button type="submit" class="secondary" style="margin-top:0;">Crear grupo</button>
        </form>
    </div>
    <?php
    admin_footer();
    exit;
}

// Sin id: admin completo ve la lista global; docente sin cursos ve un aviso
// (con 1 curso ya se redirigió arriba, con 2+ se lista solo lo suyo).
if (!$isFullAdmin) {
    admin_header('Cursos', $me);
    if (!$myCourseIds) {
        echo '<p style="color:#888;">Todavía no estás asignado como docente de ningún curso.</p>';
        admin_footer();
        exit;
    }
    $placeholders = implode(',', array_fill(0, count($myCourseIds), '?'));
    $stmt = $pdo->prepare("SELECT * FROM courses WHERE id IN ({$placeholders}) ORDER BY name");
    $stmt->execute($myCourseIds);
    $courses = $stmt->fetchAll();
} else {
    admin_header('Cursos', $me);
    $courses = $pdo->query('SELECT * FROM courses ORDER BY active DESC, name')->fetchAll();
}
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<?php if ($hasPendingLink): ?>
<div class="card" style="border: 2px solid #4a7dbd;">
    <strong>Vincular curso de Moodle</strong>
    <p style="font-size:0.85rem; color:#555;">Entraste desde un curso de Moodle que todavía no está vinculado a ningún curso de LabSim. Vincúlalo una sola vez y cada alumno que entre desde ahí se matriculará solo -- sin que tengas que agregarlos a mano ni conocer sus nombres.</p>
    <?php if (!$courses): ?>
    <p style="color:#888;">No tienes ningún curso de LabSim todavía -- créalo primero (o pide que te asignen como docente de uno) y vuelve a entrar desde Moodle.</p>
    <?php else: ?>
    <form method="post" style="display:flex; gap:0.6rem; align-items:flex-end;">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="link_lti_context">
        <input type="hidden" name="lti_platform_id" value="<?= $pendingLinkPlatform ?>">
        <input type="hidden" name="lti_context_id" value="<?= htmlspecialchars($pendingLinkContext) ?>">
        <label style="flex:1; margin:0;">Curso de LabSim
            <select name="course_id" required>
                <option value="">-- elegir --</option>
                <?php foreach ($courses as $c): ?>
                <option value="<?= $c['id'] ?>"><?= htmlspecialchars($c['name']) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <button type="submit">Vincular</button>
    </form>
    <?php endif; ?>
</div>
<?php endif; ?>

<?php if ($isFullAdmin): ?>
<div class="card">
    <strong>Crear curso</strong>
    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="create_course">
        <label>Nombre
            <input type="text" name="name" required>
        </label>
        <button type="submit">Crear</button>
    </form>
</div>
<?php endif; ?>

<div class="card">
    <strong>Cursos</strong>
    <table>
        <tr><th>Nombre</th><th>Estado</th><th>Docentes</th><th>Alumnos</th><th></th></tr>
        <?php foreach ($courses as $c): ?>
        <tr>
            <td><a href="courses.php?id=<?= $c['id'] ?>"><?= htmlspecialchars($c['name']) ?></a></td>
            <td><?= $c['active'] ? 'activo' : 'archivado' ?></td>
            <td><?= count(Courses::teachers((int) $c['id'])) ?></td>
            <td><?= count(Courses::students((int) $c['id'])) ?></td>
            <td><a href="courses.php?id=<?= $c['id'] ?>">Ver</a></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$courses): ?>
        <tr><td colspan="5" style="color:#888;">Ningún curso creado todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>
<?php
admin_footer();
