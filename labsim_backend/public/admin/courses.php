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
        } elseif ($action === 'set_modules') {
            $codes = array_map('strval', (array) ($_POST['modules'] ?? []));
            Courses::setEnabledModules($courseId, $codes);
            $success = 'Módulos actualizados.';
            AdminAudit::log($me, 'course_set_modules', ['course_id' => $courseId, 'modules' => Courses::enabledModules($courseId)]);
        } elseif ($action === 'set_abr_normative') {
            // El click SIEMPRE sale del perfil del paciente (caso, via
            // 'desviaciones' en case_create.php) -- acá NUNCA se edita click.
            // Lo que se configura por curso es cuánto se desvía cada
            // estímulo (chirp/ls-chirp/burst) respecto a ESE click, como
            // ratio (lat_ratio/amp_ratio) por onda I/III/V -- ver
            // ABR_generator.py::get_baseline_values. Reemplaza el
            // override completo cada guardado (no hace merge con el
            // anterior), así un campo que se deja vacío a propósito vuelve
            // a heredar el default de la app.
            $override = [];
            foreach ((array) ($_POST['abr_ratio'] ?? []) as $stimKey => $waves) {
                foreach ((array) $waves as $wave => $fields) {
                    $waveOverride = [];
                    foreach (['lat_ratio', 'amp_ratio'] as $field) {
                        $val = trim((string) ($fields[$field] ?? ''));
                        if ($val !== '' && is_numeric($val)) {
                            $waveOverride[$field] = (float) $val;
                        }
                    }
                    if ($waveOverride) {
                        $override[(string) $stimKey][(string) $wave] = $waveOverride;
                    }
                }
            }
            if ($override) {
                AppConfig::set('normative_data.abr', $override, $courseId);
                $success = 'Configuración de desviación ABR actualizada.';
            } else {
                AppConfig::clearCourseOverride('normative_data.abr', $courseId);
                $success = 'Sin valores marcados -- el curso vuelve a usar el default de la app.';
            }
            AdminAudit::log($me, 'course_set_abr_normative', ['course_id' => $courseId, 'override' => $override]);
        } elseif ($action === 'reset_abr_normative') {
            AppConfig::clearCourseOverride('normative_data.abr', $courseId);
            $success = 'Configuración normativa ABR restablecida al default de la app.';
            AdminAudit::log($me, 'course_reset_abr_normative', ['course_id' => $courseId]);
        } elseif ($action === 'set_vemp_normative') {
            // VEMP usa baselines ABSOLUTOS por pico (a diferencia de ABR
            // donde el click lo define el paciente y el resto son ratios).
            // Esto es porque VEMP depende del equipo/estímulo y no del
            // paciente -- la patología del paciente se aplica aparte vía
            // 'desviaciones' en case_create.php (mismo concepto que ABR).
            // Shape: {subtipo: {pico: {lat: float, amp: float}}}
            $override = [];
            foreach ((array) ($_POST['vemp_baseline'] ?? []) as $subtipo => $picos) {
                foreach ((array) $picos as $pico => $fields) {
                    $picoOverride = [];
                    foreach (['lat', 'amp'] as $field) {
                        $val = trim((string) ($fields[$field] ?? ''));
                        if ($val !== '' && is_numeric($val)) {
                            $picoOverride[$field] = (float) $val;
                        }
                    }
                    if ($picoOverride) {
                        $override[(string) $subtipo][(string) $pico] = $picoOverride;
                    }
                }
            }
            if ($override) {
                AppConfig::set('normative_data.vemp', $override, $courseId);
                $success = 'Configuración normativa VEMP actualizada.';
            } else {
                AppConfig::clearCourseOverride('normative_data.vemp', $courseId);
                $success = 'Sin valores marcados -- el curso vuelve a usar el default de la app.';
            }
            AdminAudit::log($me, 'course_set_vemp_normative', ['course_id' => $courseId, 'override' => $override]);
        } elseif ($action === 'reset_vemp_normative') {
            AppConfig::clearCourseOverride('normative_data.vemp', $courseId);
            $success = 'Configuración normativa VEMP restablecida al default de la app.';
            AdminAudit::log($me, 'course_reset_vemp_normative', ['course_id' => $courseId]);
        } elseif ($action === 'generate_demo_code') {
            $result = Courses::generateDemoAccessCode($courseId);
            $seconds = Auth::secondsUntil($result['expires_at']);
            $success = "Código para entrar como {$result['username']}: {$result['code']} (vence en " . intdiv($seconds, 60) . " min).";
            AdminAudit::log($me, 'course_generate_demo_code', ['course_id' => $courseId, 'username' => $result['username']]);
        } elseif ($action === 'clean_demo') {
            Courses::cleanDemoData($courseId);
            $success = 'Datos de prueba del demo eliminados (la cuenta y su contraseña siguen igual).';
            AdminAudit::log($me, 'course_clean_demo', ['course_id' => $courseId]);
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
                <div class="form-actions-sticky">
                    <button type="submit" class="btn btn--secondary">Guardar</button>
                </div>
            </form>
            <form method="post" class="inline" style="margin-top:0.6rem;">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="toggle_active">
                <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                <button type="submit" class="btn btn--secondary"><?= $course['active'] ? 'Archivar curso' : 'Activar curso' ?></button>
            </form>
        </details>
        <?php endif; ?>
    </div>

    <?php
        $courseMembers = Courses::students((int) $course['id']);
        $students = array_values(array_filter($courseMembers, static fn($s) => !$s['is_demo']));
        $demoStudent = null;
        foreach ($courseMembers as $s) {
            if ($s['is_demo']) {
                $demoStudent = $s;
                break;
            }
        }
        $enrollable = Courses::enrollableStudents((int) $course['id']);
        $groups = Courses::groupsForCourse((int) $course['id']);
        $groupMap = Courses::studentGroupMap((int) $course['id']);
        $origins = [];
        foreach ($enrollable as $u) {
            $o = trim((string) ($u['origin'] ?? ''));
            if ($o !== '') {
                $origins[$o] = ($origins[$o] ?? 0) + 1;
            }
        }
        ksort($origins);
    ?>

    <div class="card">
        <strong>Alumnos</strong>
        <p class="help help--mt">
            Un solo listado: matriculados y candidatos (alumnos activos que todavía no están en este curso). Busca y marca los que quieras matricular. El grupo de cada uno se asigna abajo, en "Grupos" (arrastrar y soltar).
        </p>
        <input type="text" id="roster_search" placeholder="Buscar por nombre o usuario..." class="input" style="margin:0.6rem 0;" oninput="rosterFilter()">
        <?php if ($origins): ?>
        <div style="margin-bottom:0.5rem;">
            <span class="help help--xs">Filtrar candidatos por curso de Moodle:</span>
            <?php foreach ($origins as $label => $count): ?>
            <button type="button" class="btn btn--secondary btn--xs" style="margin:0 0.3rem 0.3rem 0;" onclick="rosterSelectOrigin(<?= htmlspecialchars(json_encode($label), ENT_QUOTES) ?>)">Todos de "<?= htmlspecialchars($label) ?>" (<?= $count ?>)</button>
            <?php endforeach; ?>
        </div>
        <?php endif; ?>

        <form method="post" id="roster_form">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="bulk_enroll_selected">
            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
            <div class="scrollbox scrollbox--tall pane">
            <div class="table-wrap">
            <table id="roster_table" style="margin:0;">
                <tr>
                    <th><input type="checkbox" id="roster_select_all" onclick="rosterToggleAll(this)" title="Seleccionar todos los candidatos visibles"></th>
                    <th>Usuario</th><th>Nombre</th><th>Origen</th><th>Grupos</th><th></th>
                </tr>
                <?php foreach ($students as $s): ?>
                <tr class="roster_row" data-origin="" data-search="<?= htmlspecialchars(mb_strtolower($s['username'] . ' ' . $s['display_name'])) ?>">
                    <td></td>
                    <td><?= htmlspecialchars($s['username']) ?></td>
                    <td><a href="student.php?id=<?= $s['id'] ?>"><?= htmlspecialchars($s['display_name']) ?></a></td>
                    <td class="help help--xs">—</td>
                    <td>
                        <?php $g0 = $groupMap[$s['id']][0] ?? null; ?>
                        <?php if ($g0): ?>
                        <span class="tag tag--muted"><?= htmlspecialchars($g0['name']) ?></span>
                        <?php else: ?>
                        <span class="help help--xs">sin grupo</span>
                        <?php endif; ?>
                    </td>
                    <td>
                        <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Quitar a ' . $s['username'] . ' del curso? También lo saca de cualquier grupo del curso.'), ENT_QUOTES) ?>);">
                        <?= csrf_field() ?>
                            <input type="hidden" name="form_action" value="remove_student">
                            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                            <input type="hidden" name="user_id" value="<?= $s['id'] ?>">
                            <button type="submit" class="btn btn--danger btn--xs">Quitar</button>
                        </form>
                    </td>
                </tr>
                <?php endforeach; ?>
                <?php foreach ($enrollable as $u): ?>
                <tr class="roster_row" data-origin="<?= htmlspecialchars((string) ($u['origin'] ?? '')) ?>" data-search="<?= htmlspecialchars(mb_strtolower($u['username'] . ' ' . $u['display_name'] . ' ' . ($u['origin'] ?? ''))) ?>">
                    <td><input type="checkbox" name="user_ids[]" value="<?= $u['id'] ?>" class="roster_check" onchange="rosterUpdateCount()"></td>
                    <td><?= htmlspecialchars($u['username']) ?></td>
                    <td><?= htmlspecialchars($u['display_name']) ?></td>
                    <td class="help help--xs"><?= htmlspecialchars($u['origin'] ?: '—') ?></td>
                    <td class="help help--xs">sin matricular</td>
                    <td></td>
                </tr>
                <?php endforeach; ?>
                <?php if (!$students && !$enrollable): ?>
                <tr><td colspan="6" class="muted">Sin alumnos matriculados ni candidatos disponibles.</td></tr>
                <?php endif; ?>
            </table>
            </div>
            </div>
            <button type="submit" class="btn btn--secondary" style="margin-top:0.5rem;">Matricular seleccionados (<span id="roster_count">0</span>)</button>
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
                        var cb = row.querySelector('.roster_check');
                        if (cb) cb.checked = true;
                    }
                });
                rosterUpdateCount();
            };
            window.rosterToggleAll = function (cb) {
                rows().forEach(function (row) {
                    if (row.style.display !== 'none') {
                        var rowCb = row.querySelector('.roster_check');
                        if (rowCb) rowCb.checked = cb.checked;
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

        <details class="section-sep section-sep--lg">
            <summary>Agregar alumno nuevo o sin Moodle (manual)</summary>
            <form method="post" class="row" style="margin-top:0.6rem; flex-wrap:wrap;">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="add_student">
                <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                <label style="flex:1; margin:0; min-width:220px;">Agregar alumno (nombre o username)
                    <input type="text" name="username" list="students_datalist" required>
                </label>
                <label style="flex:1; margin:0; min-width:220px;">Nombre completo (solo si es alumno nuevo)
                    <input type="text" name="display_name" placeholder="Se usa si el username no existe todavía">
                </label>
                <button type="submit" class="btn btn--secondary btn--sm">Agregar</button>
            </form>
            <p class="help help--mt-md">Si el username no existe todavía, se crea una cuenta nueva automáticamente con contraseña temporal (se muestra al agregar).</p>

            <details class="section-sep section-sep--lg">
                <summary>Agregar varios alumnos a la vez (por texto)</summary>
                <form method="post" style="margin-top:0.6rem;">
                <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="bulk_add_students">
                    <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                    <label>Uno por línea: <code>username</code>, o <code>username, nombre completo</code>, o <code>username, nombre completo, password</code>
                        <textarea name="bulk_students" rows="6" class="textarea" placeholder="jperez&#10;mgonzalez, María González&#10;asilva, Ana Silva, MiClave123"></textarea>
                    </label>
                    <p class="help">Los que ya existen se matriculan tal cual. Los que no existen se crean con esa contraseña, o con una generada automáticamente si no se indica.</p>
                    <button type="submit" class="btn btn--secondary">Procesar lista</button>
                </form>
                <?php if ($bulkResults): ?>
                <div class="table-wrap">
                <table style="margin-top:0.8rem;">
                    <tr><th>Username</th><th>Resultado</th><th>Contraseña</th></tr>
                    <?php foreach ($bulkResults as $r): ?>
                    <tr>
                        <td><?= htmlspecialchars($r['username']) ?></td>
                        <td style="color:<?= $r['status'] === 'error' ? 'var(--color-danger)' : 'var(--color-text)' ?>;"><?= htmlspecialchars($r['message']) ?></td>
                        <td><?= !empty($r['password']) ? '<code>' . htmlspecialchars($r['password']) . '</code>' : '' ?></td>
                    </tr>
                    <?php endforeach; ?>
                </table>
                </div>
                <?php endif; ?>
            </details>
        </details>
    </div>

    <?php if ($isFullAdmin): ?>
    <div class="card">
        <strong>Docentes (<?= count($teachers = Courses::teachers((int) $course['id'])) ?>)</strong>
        <div class="table-wrap">
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
                        <button type="submit" class="btn btn--danger btn--xs">Quitar</button>
                    </form>
                </td>
            </tr>
            <?php endforeach; ?>
            <?php if (!$teachers): ?>
            <tr><td colspan="3" class="muted">Sin docentes asignados todavía.</td></tr>
            <?php endif; ?>
        </table>
        </div>
        <form method="post" class="row" style="margin-top:0.6rem;">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="add_teacher">
            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
            <label style="flex:1; margin:0;">Agregar docente (nombre o username)
                <input type="text" name="username" list="teachers_datalist" required>
            </label>
            <button type="submit" class="btn btn--secondary btn--sm">Agregar</button>
        </form>
    </div>
    <?php endif; ?>

    <div class="card">
        <strong>Grupos</strong>
        <p class="muted">Para citar a un subgrupo (p. ej. 5 alumnos a la misma hora) sin asignarlos uno por uno en la agenda. Un alumno pertenece a un solo grupo a la vez -- arrastralo a otra columna para moverlo, o a "Sin grupo" para sacarlo.</p>

        <?php
            $groupedIds = [];
            foreach ($groupMap as $uid => $gs) {
                if ($gs) {
                    $groupedIds[$uid] = (int) $gs[0]['id'];
                }
            }
            $unassigned = array_values(array_filter($students, fn($s) => !isset($groupedIds[$s['id']])));
        ?>
        <div id="group_board" style="display:flex; gap:0.8rem; overflow-x:auto; padding-bottom:0.4rem; margin-top:0.6rem;">
            <div class="pane group_column" data-group-id="" style="min-width:200px; flex:1 1 200px;">
                <strong>Sin grupo (<span class="group_count"><?= count($unassigned) ?></span>)</strong>
                <div class="group_dropzone" style="min-height:3rem; margin-top:0.5rem;">
                    <?php foreach ($unassigned as $s): ?>
                    <div class="group_card" draggable="true" data-user-id="<?= $s['id'] ?>"><?= htmlspecialchars($s['display_name']) ?></div>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php foreach ($groups as $g): ?>
            <div class="pane group_column" data-group-id="<?= $g['id'] ?>" style="min-width:200px; flex:1 1 200px;">
                <div class="row row--between" style="margin:0; align-items:center;">
                    <strong><?= htmlspecialchars($g['name']) ?> (<span class="group_count"><?= (int) $g['member_count'] ?></span>)</strong>
                    <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Eliminar el grupo ' . $g['name'] . '? Sus miembros quedan sin grupo.'), ENT_QUOTES) ?>);">
                    <?= csrf_field() ?>
                        <input type="hidden" name="form_action" value="delete_group">
                        <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                        <input type="hidden" name="group_id" value="<?= $g['id'] ?>">
                        <button type="submit" class="btn btn--danger btn--xs" title="Eliminar grupo">&times;</button>
                    </form>
                </div>
                <div class="group_dropzone" style="min-height:3rem; margin-top:0.5rem;">
                    <?php foreach ($students as $s): ?>
                    <?php if (($groupedIds[$s['id']] ?? null) !== (int) $g['id']) continue; ?>
                    <div class="group_card" draggable="true" data-user-id="<?= $s['id'] ?>"><?= htmlspecialchars($s['display_name']) ?></div>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endforeach; ?>
            <?php if (!$groups): ?>
            <p class="muted">Sin grupos creados todavía -- creá uno abajo.</p>
            <?php endif; ?>
        </div>
        <p id="group_board_error" class="error" hidden style="margin-top:0.6rem;"></p>

        <form method="post" class="row" style="margin-top:0.8rem;">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="create_group">
            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
            <label style="flex:1; margin:0;">Nuevo grupo (nombre)
                <input type="text" name="name" required>
            </label>
            <button type="submit" class="btn btn--secondary btn--sm">Crear grupo</button>
        </form>

        <script>
        (function () {
            var board = document.getElementById('group_board');
            if (!board) return;
            var csrfToken = <?= json_encode(Auth::csrfToken()) ?>;
            var courseId = <?= (int) $course['id'] ?>;
            var errorBox = document.getElementById('group_board_error');
            var dragged = null;

            function updateCounts() {
                board.querySelectorAll('.group_column').forEach(function (col) {
                    var count = col.querySelectorAll('.group_card').length;
                    var label = col.querySelector('.group_count');
                    if (label) label.textContent = count;
                });
            }

            board.querySelectorAll('.group_card').forEach(function (card) {
                card.addEventListener('dragstart', function () { dragged = card; });
            });

            board.querySelectorAll('.group_dropzone').forEach(function (zone) {
                zone.addEventListener('dragover', function (e) {
                    e.preventDefault();
                    zone.classList.add('group_dropzone--over');
                });
                zone.addEventListener('dragleave', function () {
                    zone.classList.remove('group_dropzone--over');
                });
                zone.addEventListener('drop', function (e) {
                    e.preventDefault();
                    zone.classList.remove('group_dropzone--over');
                    if (!dragged) return;

                    var fromZone = dragged.parentElement;
                    if (fromZone === zone) return;

                    var userId = dragged.dataset.userId;
                    var groupId = zone.closest('.group_column').dataset.groupId;

                    zone.appendChild(dragged);
                    updateCounts();
                    errorBox.hidden = true;

                    var body = new URLSearchParams();
                    body.set('csrf_token', csrfToken);
                    body.set('course_id', courseId);
                    body.set('user_id', userId);
                    body.set('group_id', groupId);

                    fetch('group_move.php', { method: 'POST', body: body })
                        .then(function (r) { return r.json(); })
                        .then(function (data) {
                            if (!data.ok) {
                                throw new Error(data.error || 'No se pudo mover al alumno.');
                            }
                        })
                        .catch(function (err) {
                            fromZone.appendChild(dragged);
                            updateCounts();
                            errorBox.textContent = err.message;
                            errorBox.hidden = false;
                        });
                });
            });
        })();
        </script>
    </div>

    <div class="card">
        <strong>Módulos habilitados</strong>
        <p class="help help--mt">
            Qué ve un alumno de este curso en la app de escritorio. Sin marcar nada, el curso queda sin módulos habilitados.
        </p>
        <?php $enabledModules = Courses::enabledModules((int) $course['id']); ?>
        <form method="post">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="set_modules">
            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
            <?php foreach (Courses::modulesGroupedByBox() as $boxLabel => $boxModules): ?>
            <div class="section-sep">
                <strong><?= htmlspecialchars($boxLabel) ?></strong>
                <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(230px, 1fr)); gap:0.4rem 1rem; margin-top:0.4rem;">
                    <?php foreach ($boxModules as $code => $label): ?>
                    <label style="font-weight:normal; display:flex; align-items:center; gap:0.3rem; margin:0;">
                        <input type="checkbox" name="modules[]" value="<?= htmlspecialchars($code) ?>" <?= in_array($code, $enabledModules, true) ? 'checked' : '' ?>>
                        <?= htmlspecialchars($label) ?>
                    </label>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endforeach; ?>
            <button type="submit" class="btn btn--secondary" style="margin-top:0.6rem;">Guardar módulos</button>
        </form>
    </div>

    <?php if (in_array('ABR', $enabledModules, true)): ?>
    <div class="card">
        <strong>Desviación de estímulos ABR (potenciales evocados)</strong>
        <p class="help help--mt">
            El click de cada paciente lo define el caso (case_create.php, campo "desviaciones") -- acá NO se edita click. Esto configura cuánto se desvían chirp/ls-chirp/burst respecto al click de ESE paciente, como factor multiplicador (ratio) por onda -- ej. amp_ratio 1.4 en onda V de "Chirp" = la V del chirp sale 40% más grande que la V (ya ajustada) del click de ese caso. Los campos muestran el valor por defecto de la app; tocalos para sobreescribir, dejalos como están para no cambiar nada.
        </p>
        <?php
            // Ver ABR_generator.py::get_baseline_values -- valores por
            // defecto (adult_female, vía aérea) de resources/abr/normative_data.json.
            // Mantener sincronizado a mano si ese JSON cambia (repos separados).
            $abrStimDefaults = [
                'ce_chirp'         => ['label' => 'Chirp',       'I' => ['lat_ratio' => 0.8951, 'amp_ratio' => 2.1429], 'III' => ['lat_ratio' => 0.9783, 'amp_ratio' => 1.4054], 'V' => ['lat_ratio' => 0.9872, 'amp_ratio' => 1.2167]],
                'ls_chirp'         => ['label' => 'Ls-chirp',    'I' => ['lat_ratio' => 0.9074, 'amp_ratio' => 1.8095], 'III' => ['lat_ratio' => 0.9918, 'amp_ratio' => 1.1892], 'V' => ['lat_ratio' => 0.9963, 'amp_ratio' => 1.0333]],
                'tone_burst_500Hz'  => ['label' => 'Burst 500Hz', 'I' => ['lat_ratio' => 1.4506, 'amp_ratio' => 1.0476], 'III' => ['lat_ratio' => 1.4538, 'amp_ratio' => 0.7297], 'V' => ['lat_ratio' => 1.4625, 'amp_ratio' => 0.6333]],
                'tone_burst_1000Hz' => ['label' => 'Burst 1kHz',  'I' => ['lat_ratio' => 1.2037, 'amp_ratio' => 1.2857], 'III' => ['lat_ratio' => 1.2636, 'amp_ratio' => 0.8649], 'V' => ['lat_ratio' => 1.2431, 'amp_ratio' => 0.7167]],
                'tone_burst_2000Hz' => ['label' => 'Burst 2kHz',  'I' => ['lat_ratio' => 1.0494, 'amp_ratio' => 1.4286], 'III' => ['lat_ratio' => 1.1005, 'amp_ratio' => 0.9459], 'V' => ['lat_ratio' => 1.0969, 'amp_ratio' => 0.7833]],
                'tone_burst_4000Hz' => ['label' => 'Burst 4kHz',  'I' => ['lat_ratio' => 0.9568, 'amp_ratio' => 1.5238], 'III' => ['lat_ratio' => 1.0326, 'amp_ratio' => 1.0000], 'V' => ['lat_ratio' => 1.0329, 'amp_ratio' => 0.8333]],
            ];
            $abrOverride = AppConfig::getEffective('normative_data.abr', (int) $course['id']) ?? [];
        ?>
        <form method="post">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="set_abr_normative">
            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
            <?php foreach ($abrStimDefaults as $stimKey => $stimDefaults): ?>
            <details style="margin-top:0.5rem;">
                <summary><strong><?= htmlspecialchars($stimDefaults['label']) ?></strong></summary>
                <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:0.6rem 1rem; margin-top:0.4rem;">
                    <?php foreach (['I' => 'Onda I', 'III' => 'Onda III', 'V' => 'Onda V'] as $wave => $waveLabel): ?>
                    <?php
                        $defaults = $stimDefaults[$wave];
                        $current = $abrOverride[$stimKey][$wave] ?? [];
                    ?>
                    <div>
                        <strong style="font-weight:600;"><?= $waveLabel ?></strong>
                        <label style="font-weight:normal; display:block; margin-top:0.2rem;">
                            Ratio latencia
                            <input type="number" step="0.0001" name="abr_ratio[<?= $stimKey ?>][<?= $wave ?>][lat_ratio]"
                                   value="<?= htmlspecialchars((string) ($current['lat_ratio'] ?? $defaults['lat_ratio'])) ?>">
                        </label>
                        <label style="font-weight:normal; display:block; margin-top:0.2rem;">
                            Ratio amplitud
                            <input type="number" step="0.0001" name="abr_ratio[<?= $stimKey ?>][<?= $wave ?>][amp_ratio]"
                                   value="<?= htmlspecialchars((string) ($current['amp_ratio'] ?? $defaults['amp_ratio'])) ?>">
                        </label>
                    </div>
                    <?php endforeach; ?>
                </div>
            </details>
            <?php endforeach; ?>
            <div class="form-actions-sticky">
                <button type="submit" class="btn btn--secondary">Guardar configuración</button>
            </div>
        </form>
        <?php if ($abrOverride): ?>
        <form method="post" style="margin-top:0.5rem;"
              onsubmit="return confirm('¿Restablecer al valor por defecto de la app? Se pierde la configuración actual del curso.');">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="reset_abr_normative">
            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
            <button type="submit" class="btn btn--danger btn--sm">Volver a default</button>
        </form>
        <?php else: ?>
        <p class="help help--mt">Sin configuración propia -- usando el valor por defecto de la app.</p>
        <?php endif; ?>
    </div>
    <?php endif; ?>

    <?php if (in_array('VEMP', $enabledModules, true)): ?>
    <div class="card">
        <strong>Normativa VEMP (potenciales evocados vestibulares miogénicos)</strong>
        <p class="help help--mt">
            VEMP ajusta el baseline por pico/subtipo (a diferencia de ABR, donde el click lo define el paciente y el resto son ratios -- acá el baseline es del equipo). Acá se sobreescriben los absolutos de latencia/amplitud por pico, por subtipo (CVEMP cervical sobre SCM, OVEMP ocular sobre oblicuo inferior, MVEMP masetero). El paciente en sí desvía aparte vía "desviaciones" en case_create.php. Los campos muestran el default de la app; tocarlos sobreescribe, dejarlos como están hereda el default.
        </p>
        <?php
            // Defaults sincronizados a mano con
            // resources/vemp/normative_data.json (adult_female / 500Hz).
            $vempDefaults = [
                'CVEMP' => [
                    'label' => 'CVEMP (cervical / SCM)',
                    'picos' => [
                        'p13' => ['lat' => 12.8, 'amp' => 135.0],
                        'n23' => ['lat' => 22.5, 'amp' => 185.0],
                    ],
                ],
                'OVEMP' => [
                    'label' => 'OVEMP (ocular / oblicuo inferior)',
                    'picos' => [
                        'n10' => ['lat' => 9.8, 'amp' => 8.5],
                        'p16' => ['lat' => 15.8, 'amp' => 11.5],
                    ],
                ],
                'MVEMP' => [
                    'label' => 'MVEMP (masetero -- experimental)',
                    'picos' => [
                        'p13' => ['lat' => 12.8, 'amp' => 45.0],
                        'n23' => ['lat' => 22.5, 'amp' => 60.0],
                    ],
                ],
            ];
            $vempOverride = AppConfig::getEffective('normative_data.vemp', (int) $course['id']) ?? [];
        ?>
        <form method="post">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="set_vemp_normative">
            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
            <?php foreach ($vempDefaults as $subtipo => $subDefaults): ?>
            <details style="margin-top:0.5rem;">
                <summary><strong><?= htmlspecialchars($subDefaults['label']) ?></strong></summary>
                <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(180px, 1fr)); gap:0.6rem 1rem; margin-top:0.4rem;">
                    <?php foreach ($subDefaults['picos'] as $pico => $defaults): ?>
                    <?php $current = $vempOverride[$subtipo][$pico] ?? []; ?>
                    <div>
                        <strong style="font-weight:600;"><?= strtoupper($pico) ?></strong>
                        <label style="font-weight:normal; display:block; margin-top:0.2rem;">
                            Latencia (ms)
                            <input type="number" step="0.01" name="vemp_baseline[<?= $subtipo ?>][<?= $pico ?>][lat]"
                                   value="<?= htmlspecialchars((string) ($current['lat'] ?? $defaults['lat'])) ?>">
                        </label>
                        <label style="font-weight:normal; display:block; margin-top:0.2rem;">
                            Amplitud (µV)
                            <input type="number" step="0.01" name="vemp_baseline[<?= $subtipo ?>][<?= $pico ?>][amp]"
                                   value="<?= htmlspecialchars((string) ($current['amp'] ?? $defaults['amp'])) ?>">
                        </label>
                    </div>
                    <?php endforeach; ?>
                </div>
            </details>
            <?php endforeach; ?>
            <div class="form-actions-sticky">
                <button type="submit" class="btn btn--secondary">Guardar configuración</button>
            </div>
        </form>
        <?php if ($vempOverride): ?>
        <form method="post" style="margin-top:0.5rem;"
              onsubmit="return confirm('¿Restablecer al valor por defecto de la app? Se pierde la configuración actual del curso.');">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="reset_vemp_normative">
            <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
            <button type="submit" class="btn btn--danger btn--sm">Volver a default</button>
        </form>
        <?php else: ?>
        <p class="help help--mt">Sin configuración propia -- usando el valor por defecto de la app.</p>
        <?php endif; ?>
    </div>
    <?php endif; ?>

    <div class="card">
        <details>
        <summary><strong>Área de pruebas</strong></summary>
        <p class="help help--mt">
            Un alumno más del curso para probar la app de punta a punta (agendarle pacientes, atender, etc.) sin tocar datos de alumnos reales. Invisible para los alumnos -- solo docente/admin lo ven acá. Entra con código de 6 dígitos, igual que un alumno LTI -- sin usuario ni contraseña que gestionar.
        </p>
        <div class="row" style="margin-top:0.5rem;">
            <form method="post">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="generate_demo_code">
                <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                <button type="submit" class="btn btn--secondary">Generar código de acceso</button>
            </form>
            <?php if ($demoStudent !== null): ?>
            <form method="post" onsubmit="return confirm('¿Borrar todas las citas/atenciones/chats de prueba del demo? La cuenta queda igual.');">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="clean_demo">
                <input type="hidden" name="course_id" value="<?= $course['id'] ?>">
                <button type="submit" class="btn btn--danger">Limpiar datos de prueba</button>
            </form>
            <?php endif; ?>
        </div>
        </details>
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
        echo '<p class="muted">Todavía no estás asignado como docente de ningún curso.</p>';
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
<div class="card" style="border: 2px solid var(--color-info-border);">
    <strong>Vincular curso de Moodle</strong>
    <p class="muted">Entraste desde un curso de Moodle que todavía no está vinculado a ningún curso de LabSim. Vincúlalo una sola vez y cada alumno que entre desde ahí se matriculará solo -- sin que tengas que agregarlos a mano ni conocer sus nombres.</p>
    <?php if (!$courses): ?>
    <p class="muted">No tienes ningún curso de LabSim todavía -- créalo primero (o pide que te asignen como docente de uno) y vuelve a entrar desde Moodle.</p>
    <?php else: ?>
    <form method="post" class="row">
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
        <label class="field-label">Nombre
            <input class="input" type="text" name="name" required>
        </label>
        <div class="form-actions-sticky">
            <button class="btn" type="submit">Crear</button>
        </div>
    </form>
</div>
<?php endif; ?>

<div class="card">
    <strong>Cursos</strong>
    <div class="table-wrap">
    <table>
        <tr><th>Nombre</th><th>Estado</th><th>Docentes</th><th>Alumnos</th></tr>
        <?php foreach ($courses as $c): ?>
        <tr>
            <td><a href="courses.php?id=<?= $c['id'] ?>"><?= htmlspecialchars($c['name']) ?></a></td>
            <td><?= $c['active'] ? 'activo' : 'archivado' ?></td>
            <td><?= count(Courses::teachers((int) $c['id'])) ?></td>
            <td><?= count(array_filter(Courses::students((int) $c['id']), static fn($s) => !$s['is_demo'])) ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$courses): ?>
        <tr><td colspan="4" class="muted">Ningún curso creado todavía.</td></tr>
        <?php endif; ?>
    </table>
    </div>
</div>
<?php
admin_footer();
