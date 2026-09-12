<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/CourseParams.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Cursos: separa alumnos/docentes/casos de cursos distintos que antes iban
 * todos al mismo fondo común (ver comentario en sql/schema.sql sobre
 * `courses`). El admin completo ve/crea cualquier curso; un docente entra
 * directo al detalle del/los suyo(s) -- nunca ve la lista global ni cursos
 * ajenos (mismo criterio de scoping que agenda.php/dashboard.php/student.php,
 * hoy centralizado en Courses::canAdminister()).
 *
 * Las personas del curso se administran en UN solo lugar: el tablero de
 * grupos. Antes había además una tabla de alumnos arriba que listaba a los
 * mismos matriculados con otras columnas -- el mismo roster dos veces en la
 * misma página. Los candidatos a matricular viven en el panel de la derecha
 * y se matriculan arrastrándolos a una columna (o marcándolos, para tandas
 * grandes).
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$myCourseIds = $isFullAdmin ? null : Courses::teacherCourseIds((int) $me['id']);

$error = null;
$success = null;
$bulkResults = [];

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
        Courses::assertAdministers($courseId, $me);

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
        } elseif ($action === 'set_params' || $action === 'reset_params') {
            // Un solo par de acciones para TODOS los parámetros configurables
            // por curso (normativa ABR, normativa VEMP y lo que se sume): la
            // forma de cada key vive en CourseParams, no en un handler
            // escrito a mano por examen.
            $paramKey = (string) ($_POST['param_key'] ?? '');
            $def = CourseParams::find($paramKey);
            if ($def === null) {
                $error = 'Parámetro desconocido.';
            } elseif ($action === 'reset_params') {
                AppConfig::clearCourseOverride($paramKey, $courseId);
                $success = htmlspecialchars_decode($def['title']) . ': restablecido al default de la app.';
                AdminAudit::log($me, 'course_reset_params', ['course_id' => $courseId, 'param_key' => $paramKey]);
            } else {
                $override = CourseParams::parse($paramKey, (array) ($_POST['params'] ?? []));
                if ($override) {
                    AppConfig::set($paramKey, $override, $courseId);
                    $success = 'Configuración guardada -- el curso sobreescribe ' . count($override, COUNT_RECURSIVE) . ' valor(es).';
                } else {
                    // parse() omite lo que quedó igual al default: si no
                    // sobra nada, el curso no tiene por qué tener override.
                    AppConfig::clearCourseOverride($paramKey, $courseId);
                    $success = 'Todo quedó igual al default de la app -- el curso vuelve a heredarlo.';
                }
                AdminAudit::log($me, 'course_set_params', ['course_id' => $courseId, 'param_key' => $paramKey, 'override' => $override]);
            }
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
        } elseif ($action === 'rename_group' || $action === 'delete_group') {
            // El group_id viene del navegador: tener acceso al curso no
            // alcanza, hay que confirmar que el grupo sea de ESTE curso.
            $groupId = (int) ($_POST['group_id'] ?? 0);
            if (!Courses::groupBelongsTo($groupId, $courseId)) {
                $error = 'Ese grupo no pertenece a este curso.';
            } elseif ($action === 'delete_group') {
                Courses::deleteGroup($groupId);
                $success = 'Grupo eliminado.';
                AdminAudit::log($me, 'group_delete', ['course_id' => $courseId, 'group_id' => $groupId]);
            } else {
                $name = trim((string) ($_POST['name'] ?? ''));
                if ($name === '') {
                    $error = 'Falta el nombre del grupo.';
                } else {
                    Courses::renameGroup($groupId, $name);
                    $success = 'Grupo renombrado.';
                    AdminAudit::log($me, 'group_rename', ['course_id' => $courseId, 'group_id' => $groupId, 'name' => $name]);
                }
            }
        } elseif ($action === 'split_groups') {
            $n = (int) ($_POST['n_groups'] ?? 0);
            $prefix = trim((string) ($_POST['group_prefix'] ?? 'Grupo'));
            if ($n < 2 || $n > 40) {
                $error = 'Elige entre 2 y 40 grupos.';
            } else {
                $repartidos = Courses::splitUngroupedIntoGroups($courseId, $n, $prefix);
                $success = $repartidos > 0
                    ? "{$repartidos} alumno(s) repartido(s) en {$n} grupo(s) nuevo(s)."
                    : 'No había alumnos sin grupo -- no se creó nada.';
                AdminAudit::log($me, 'course_split_groups', ['course_id' => $courseId, 'n' => $n, 'repartidos' => $repartidos]);
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
    Courses::assertAdministers($detailId, $me);
    $course = Courses::find($detailId);
    if (!$course) {
        admin_header('Curso', $me);
        echo '<p class="error">Curso no encontrado.</p>';
        admin_footer();
        exit;
    }

    $courseId = (int) $course['id'];
    $courseMembers = Courses::students($courseId);
    $students = array_values(array_filter($courseMembers, static fn($s) => !$s['is_demo']));
    $demoStudent = null;
    foreach ($courseMembers as $s) {
        if ($s['is_demo']) {
            $demoStudent = $s;
            break;
        }
    }
    $enrollable = Courses::enrollableStudents($courseId);
    $groups = Courses::groupsForCourse($courseId);
    $groupMap = Courses::studentGroupMap($courseId);
    $progress = Courses::rosterProgress($courseId);

    // Un alumno pertenece a un solo grupo por curso (ver
    // Courses::moveStudentToGroup): aplanamos el map a "en qué columna va".
    $groupedIds = [];
    foreach ($groupMap as $uid => $gs) {
        if ($gs) {
            $groupedIds[(int) $uid] = (int) $gs[0]['id'];
        }
    }
    $sinGrupo = array_values(array_filter($students, static fn($s) => !isset($groupedIds[(int) $s['id']])));

    // Chips "todos los que vinieron del curso Moodle X" para el panel de
    // candidatos (ver user_lti_contexts).
    $origins = [];
    foreach ($enrollable as $u) {
        $o = trim((string) ($u['origin'] ?? ''));
        if ($o !== '') {
            $origins[$o] = ($origins[$o] ?? 0) + 1;
        }
    }
    ksort($origins);

    $enabledModules = Courses::enabledModules($courseId);
    $teacherOptions = $isFullAdmin
        ? $pdo->query("SELECT username, display_name FROM users WHERE role = 'admin' AND active = 1 ORDER BY display_name")->fetchAll()
        : [];

    /** Tarjeta de alumno del tablero: la misma para un matriculado y para un
     * candidato del panel -- lo que cambia es data-enroll y qué controles
     * quedan visibles, así arrastrar un candidato a una columna lo convierte
     * en miembro sin tener que rearmar la tarjeta desde JS. */
    $renderCard = static function (array $s, bool $isCandidate) use ($courseId, $progress): void {
        $uid = (int) $s['id'];
        $p = $progress[$uid] ?? ['asignadas' => 0, 'atendidas' => 0, 'ultima' => null];
        $search = mb_strtolower($s['username'] . ' ' . $s['display_name'] . ' ' . (string) ($s['origin'] ?? ''));
        ?>
        <div class="group_card" draggable="true"
             data-user-id="<?= $uid ?>"
             data-enroll="<?= $isCandidate ? '1' : '0' ?>"
             data-origin="<?= htmlspecialchars((string) ($s['origin'] ?? '')) ?>"
             data-search="<?= htmlspecialchars($search) ?>">
            <div class="group_card__head">
                <label class="group_card__pick card-enroll-only" <?= $isCandidate ? '' : 'hidden' ?>>
                    <input type="checkbox" form="enroll_form" name="user_ids[]" value="<?= $uid ?>" class="candidate_check">
                </label>
                <a href="student.php?id=<?= $uid ?>" class="group_card__name"><?= htmlspecialchars($s['display_name']) ?></a>
                <form method="post" class="inline card-member-only" <?= $isCandidate ? 'hidden' : '' ?>
                      onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Quitar a ' . $s['username'] . ' del curso? También lo saca de su grupo.'), ENT_QUOTES) ?>);">
                <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="remove_student">
                    <input type="hidden" name="course_id" value="<?= $courseId ?>">
                    <input type="hidden" name="user_id" value="<?= $uid ?>">
                    <button type="submit" class="btn btn--danger btn--xs" title="Quitar del curso">&times;</button>
                </form>
            </div>
            <div class="group_card__meta help help--xs">
                <?= htmlspecialchars($s['username']) ?>
                <span class="card-member-only" <?= $isCandidate ? 'hidden' : '' ?>>
                    &nbsp;·&nbsp; <?= $p['asignadas'] ?> cita<?= $p['asignadas'] === 1 ? '' : 's' ?>
                    &nbsp;·&nbsp; <?= $p['atendidas'] ?> cerrada<?= $p['atendidas'] === 1 ? '' : 's' ?>
                    <?php if ($p['ultima'] !== null): ?>
                    &nbsp;·&nbsp; últ. <?= htmlspecialchars(substr((string) $p['ultima'], 0, 10)) ?>
                    <?php endif; ?>
                </span>
                <span class="card-enroll-only" <?= $isCandidate ? '' : 'hidden' ?>>
                    <?= $s['origin'] ? '&nbsp;·&nbsp; ' . htmlspecialchars((string) $s['origin']) : '' ?>
                </span>
            </div>
        </div>
        <?php
    };

    admin_add_js('course/board.js');
    admin_header('Curso: ' . $course['name'], $me);
    ?>
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
        &nbsp;·&nbsp; <span class="help help--xs"><?= count($students) ?> alumno(s), <?= count($groups) ?> grupo(s)</span>
        <?php if ($isFullAdmin): ?>
        <details style="margin-top:0.6rem;">
            <summary>Editar</summary>
            <form method="post" style="margin-top:0.4rem;">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="rename_course">
                <input type="hidden" name="course_id" value="<?= $courseId ?>">
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
                <input type="hidden" name="course_id" value="<?= $courseId ?>">
                <button type="submit" class="btn btn--secondary"><?= $course['active'] ? 'Archivar curso' : 'Activar curso' ?></button>
            </form>
        </details>
        <?php endif; ?>
    </div>

    <div class="card">
        <div class="row row--between" style="margin:0; align-items:center;">
            <strong>Alumnos y grupos</strong>
            <span class="help help--xs"><?= count($students) ?> matriculado(s) &middot; <?= count($sinGrupo) ?> sin grupo &middot; <?= count($enrollable) ?> candidato(s)</span>
        </div>
        <p class="help help--mt">
            Cada tarjeta es un alumno; arrastrarla a otra columna lo mueve de grupo (pertenece a uno solo a la vez). Los candidatos del panel de la derecha --alumnos activos que todavía no están en este curso-- se matriculan al soltarlos en una columna, o marcándolos y usando el botón, para tandas grandes.
        </p>

        <div class="row" style="margin-top:0.6rem; flex-wrap:wrap; gap:0.6rem;">
            <input type="text" id="people_search" class="input grow" placeholder="Buscar por nombre, usuario u origen...">
            <form method="post" class="row" style="margin:0; gap:0.4rem;">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="create_group">
                <input type="hidden" name="course_id" value="<?= $courseId ?>">
                <input type="text" name="name" class="input input--auto" placeholder="Nuevo grupo" required>
                <button type="submit" class="btn btn--secondary btn--sm">Crear grupo</button>
            </form>
            <?php if ($sinGrupo): ?>
            <form method="post" class="row" style="margin:0; gap:0.4rem;"
                  onsubmit="return confirm('Crea los grupos nuevos y reparte entre ellos a los alumnos que hoy están sin grupo. ¿Seguir?');">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="split_groups">
                <input type="hidden" name="course_id" value="<?= $courseId ?>">
                <input type="number" name="n_groups" class="input input--narrow" min="2" max="40" value="4" required title="Cuántos grupos crear">
                <input type="text" name="group_prefix" class="input input--auto" value="Grupo" title="Prefijo del nombre">
                <button type="submit" class="btn btn--secondary btn--sm">Repartir <?= count($sinGrupo) ?> sin grupo</button>
            </form>
            <?php endif; ?>
        </div>

        <p id="board_error" class="error" hidden style="margin-top:0.6rem;"></p>

        <div class="course-people">
            <div id="course_board"
                 data-course-id="<?= $courseId ?>"
                 data-csrf="<?= htmlspecialchars(Auth::csrfToken()) ?>"
                 data-endpoint="group_move.php">
                <div class="pane group_column" data-group-id="">
                    <div class="row row--between" style="margin:0; align-items:center;">
                        <strong>Sin grupo (<span class="group_count"><?= count($sinGrupo) ?></span>)</strong>
                    </div>
                    <div class="group_dropzone">
                        <?php foreach ($sinGrupo as $s) {
                            $renderCard($s, false);
                        } ?>
                    </div>
                </div>
                <?php foreach ($groups as $g): ?>
                <div class="pane group_column" data-group-id="<?= (int) $g['id'] ?>">
                    <div class="row row--between" style="margin:0; align-items:center;">
                        <strong class="group_title"><?= htmlspecialchars($g['name']) ?> (<span class="group_count"><?= (int) $g['member_count'] ?></span>)</strong>
                        <form method="post" class="inline group_rename" hidden>
                        <?= csrf_field() ?>
                            <input type="hidden" name="form_action" value="rename_group">
                            <input type="hidden" name="course_id" value="<?= $courseId ?>">
                            <input type="hidden" name="group_id" value="<?= (int) $g['id'] ?>">
                            <input type="text" name="name" class="input input--auto" value="<?= htmlspecialchars($g['name']) ?>" required>
                        </form>
                        <span class="row" style="margin:0; gap:0.2rem;">
                            <button type="button" class="btn btn--ghost btn--xs" title="Renombrar grupo" data-rename-toggle>&#9998;</button>
                            <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Eliminar el grupo ' . $g['name'] . '? Sus miembros quedan sin grupo.'), ENT_QUOTES) ?>);">
                            <?= csrf_field() ?>
                                <input type="hidden" name="form_action" value="delete_group">
                                <input type="hidden" name="course_id" value="<?= $courseId ?>">
                                <input type="hidden" name="group_id" value="<?= (int) $g['id'] ?>">
                                <button type="submit" class="btn btn--danger btn--xs" title="Eliminar grupo">&times;</button>
                            </form>
                        </span>
                    </div>
                    <div class="group_dropzone">
                        <?php foreach ($students as $s): ?>
                        <?php if (($groupedIds[(int) $s['id']] ?? null) !== (int) $g['id']) continue; ?>
                        <?php $renderCard($s, false); ?>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>

            <div class="pane course-candidates">
                <strong>Matricular (<span id="candidate_total"><?= count($enrollable) ?></span>)</strong>
                <p class="help help--xs" style="margin-top:0.3rem;">Arrastra a una columna, o marca y matricula en bloque.</p>
                <?php if ($origins): ?>
                <div style="margin:0.4rem 0;">
                    <?php foreach ($origins as $label => $count): ?>
                    <button type="button" class="btn btn--secondary btn--xs" style="margin:0 0.3rem 0.3rem 0;"
                            data-origin-select="<?= htmlspecialchars($label) ?>">Todos de "<?= htmlspecialchars($label) ?>" (<?= $count ?>)</button>
                    <?php endforeach; ?>
                </div>
                <?php endif; ?>
                <!-- El form queda vacío y las tarjetas afuera: cada tarjeta trae
                     su propio form (quitar del curso) y un form dentro de otro es
                     HTML inválido. Los checkbox se asocian por atributo form=. -->
                <form method="post" id="enroll_form">
                <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="bulk_enroll_selected">
                    <input type="hidden" name="course_id" value="<?= $courseId ?>">
                </form>
                <div class="scrollbox" id="candidate_list">
                    <?php foreach ($enrollable as $u) {
                        $renderCard($u, true);
                    } ?>
                    <?php if (!$enrollable): ?>
                    <p class="help help--xs">No quedan alumnos activos fuera de este curso.</p>
                    <?php endif; ?>
                </div>
                <button type="submit" form="enroll_form" class="btn btn--secondary btn--sm" style="margin-top:0.5rem;">Matricular marcados (<span id="candidate_count">0</span>)</button>

                <details class="section-sep">
                    <summary>Alumno nuevo o sin Moodle</summary>
                    <form method="post" style="margin-top:0.5rem;">
                    <?= csrf_field() ?>
                        <input type="hidden" name="form_action" value="add_student">
                        <input type="hidden" name="course_id" value="<?= $courseId ?>">
                        <label>Usuario
                            <input type="text" name="username" required>
                        </label>
                        <label>Nombre completo (si es nuevo)
                            <input type="text" name="display_name" placeholder="Se usa si el usuario no existe todavía">
                        </label>
                        <button type="submit" class="btn btn--secondary btn--sm">Agregar</button>
                    </form>
                    <p class="help help--xs">Si el usuario no existe, se crea la cuenta con una contraseña temporal que se muestra al agregar.</p>
                </details>

                <details class="section-sep">
                    <summary>Pegar una lista</summary>
                    <form method="post" style="margin-top:0.5rem;">
                    <?= csrf_field() ?>
                        <input type="hidden" name="form_action" value="bulk_add_students">
                        <input type="hidden" name="course_id" value="<?= $courseId ?>">
                        <label>Uno por línea: <code>usuario</code>, <code>usuario, nombre</code> o <code>usuario, nombre, clave</code>
                            <textarea name="bulk_students" rows="6" class="textarea" placeholder="jperez&#10;mgonzalez, María González&#10;asilva, Ana Silva, MiClave123"></textarea>
                        </label>
                        <p class="help help--xs">Los que ya existen se matriculan; los que no, se crean con esa clave o con una generada.</p>
                        <button type="submit" class="btn btn--secondary btn--sm">Procesar lista</button>
                    </form>
                </details>
            </div>
        </div>

        <?php if ($bulkResults): ?>
        <div class="table-wrap">
        <table style="margin-top:0.8rem;">
            <tr><th>Usuario</th><th>Resultado</th><th>Contraseña</th></tr>
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
    </div>

    <?php if ($isFullAdmin): ?>
    <div class="card">
        <strong>Docentes (<?= count($teachers = Courses::teachers($courseId)) ?>)</strong>
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
                        <input type="hidden" name="course_id" value="<?= $courseId ?>">
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
            <input type="hidden" name="course_id" value="<?= $courseId ?>">
            <label style="flex:1; margin:0;">Agregar docente (nombre o username)
                <input type="text" name="username" list="teachers_datalist" required>
            </label>
            <button type="submit" class="btn btn--secondary btn--sm">Agregar</button>
        </form>
    </div>
    <?php endif; ?>

    <div class="card">
        <strong>Módulos habilitados</strong>
        <p class="help help--mt">
            Qué ve un alumno de este curso en la app de escritorio. Sin marcar nada, el curso queda sin módulos habilitados.
        </p>
        <form method="post">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="set_modules">
            <input type="hidden" name="course_id" value="<?= $courseId ?>">
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

    <?php
    // Un editor por parámetro configurable del curso, generado desde el
    // registro (CourseParams) -- solo los de módulos habilitados.
    foreach (CourseParams::forModules($enabledModules) as $paramKey => $def) {
        $override = AppConfig::courseOverride($paramKey, $courseId);
        include __DIR__ . '/../../views/course/_params.php';
    }
    ?>

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
                <input type="hidden" name="course_id" value="<?= $courseId ?>">
                <button type="submit" class="btn btn--secondary">Generar código de acceso</button>
            </form>
            <?php if ($demoStudent !== null): ?>
            <form method="post" onsubmit="return confirm('¿Borrar todas las citas/atenciones/chats de prueba del demo? La cuenta queda igual.');">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="clean_demo">
                <input type="hidden" name="course_id" value="<?= $courseId ?>">
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
admin_header('Cursos', $me);
if (!$isFullAdmin && !$myCourseIds) {
    echo '<p class="muted">Todavía no estás asignado como docente de ningún curso.</p>';
    admin_footer();
    exit;
}
$courses = Courses::listWithCounts($isFullAdmin ? null : $myCourseIds);
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
            <td><?= (int) $c['n_teachers'] ?></td>
            <td><?= (int) $c['n_students'] ?></td>
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
