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
            $err = Courses::addMemberByUsername($courseId, $username, 'student');
            if ($err) {
                $error = $err;
            } else {
                $success = 'Alumno agregado al curso.';
                AdminAudit::log($me, 'course_add_student', ['course_id' => $courseId, 'username' => $username]);
            }
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

// Docente sin id en la URL: si tiene un solo curso, entra directo a su detalle.
if ($detailId === null && !$isFullAdmin && $myCourseIds && count($myCourseIds) === 1) {
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
        <form method="post" style="display:flex; gap:0.6rem; align-items:flex-end; margin-top:0.6rem;">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="add_student">
            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
            <label style="flex:1; margin:0;">Agregar alumno (nombre o username)
                <input type="text" name="username" list="students_datalist" required>
            </label>
            <button type="submit" class="secondary" style="margin-top:0;">Agregar</button>
        </form>
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
