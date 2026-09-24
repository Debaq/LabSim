<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/CourseParams.php';
require_once __DIR__ . '/../../src/CourseAdmin.php';
require_once __DIR__ . '/../../src/CourseOverview.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Página de curso: controlador. Resuelve permisos, manda el POST a
 * CourseAdmin, carga lo que necesita la pestaña pedida y la incluye desde
 * views/course/. La vista entera vivía acá y llegó a 937 líneas de scroll
 * único; cada pestaña es ahora su propio archivo y su propia carga.
 *
 * El admin completo ve/crea cualquier curso; un docente entra directo al
 * detalle del/los suyo(s) -- nunca ve la lista global ni cursos ajenos
 * (Courses::canAdminister(), la misma regla que usan agenda.php,
 * dashboard.php y student.php).
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$myCourseIds = $isFullAdmin ? null : Courses::teacherCourseIds((int) $me['id']);

$error = null;
$success = null;
$bulkResults = [];
$postTab = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $resultado = CourseAdmin::handle($me, $_POST);
    $error = $resultado['error'];
    $success = $resultado['success'];
    $bulkResults = $resultado['bulk'];
    $postTab = $resultado['tab'];
}

// Docente sin id en la URL: si tiene un solo curso, entra directo a su
// detalle -- salvo que venga a vincular un contexto LTI (ver el aviso de
// views/course/_lista.php), que necesita la lista para elegir curso.
$pendingLinkPlatform = (int) ($_GET['link_platform'] ?? 0);
$pendingLinkContext = (string) ($_GET['link_context'] ?? '');
$hasPendingLink = $pendingLinkPlatform > 0 && $pendingLinkContext !== '';

$detailId = isset($_GET['id']) && $_GET['id'] !== '' ? (int) $_GET['id'] : null;
// El selector de curso del header manda ?curso=N: acá dentro eso significa
// "mostrame ese curso", no solo cambiar el foco de las otras páginas.
if ($detailId === null && !$hasPendingLink && isset($_GET['curso']) && ctype_digit((string) $_GET['curso'])) {
    $detailId = (int) $_GET['curso'];
}
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
    // Entrar a un curso es elegirlo: agenda, fichas, dashboard y bandeja
    // quedan acotadas a él hasta que se cambie en el header.
    admin_set_course_context($courseId);

    $counts = Courses::counts($courseId);
    $courseTabs = [
        'resumen' => ['label' => 'Resumen'],
        'personas' => ['label' => 'Personas', 'count' => $counts['alumnos']],
        'modulos' => ['label' => 'Módulos', 'count' => $counts['modulos']],
        'agenda' => ['label' => 'Agenda'],
        'vinculos' => ['label' => 'Vínculos'],
        'pruebas' => ['label' => 'Pruebas'],
    ];
    // Después de un POST vuelve la pestaña de donde salió el formulario (la
    // sabe CourseAdmin por la acción), así el aviso se lee donde se trabajó.
    $activeTab = (string) ($postTab ?? $_GET['tab'] ?? 'resumen');
    if (!isset($courseTabs[$activeTab])) {
        $activeTab = 'resumen';
    }

    // Cada pestaña carga solo lo suyo: el tablero de personas es lo más caro
    // de la página y no tiene por qué armarse para mirar la agenda.
    switch ($activeTab) {
        case 'resumen':
            $checklist = CourseOverview::checklist($courseId);
            $proximas = CourseOverview::proximasCitas($courseId, 7);
            $conteoCitas = CourseOverview::conteoCitas($courseId);
            $sinActividad = CourseOverview::alumnosSinActividad($courseId);
            break;

        case 'personas':
            $courseMembers = Courses::students($courseId);
            $students = array_values(array_filter($courseMembers, static fn(array $s): bool => !$s['is_demo']));
            $enrollable = Courses::enrollableStudents($courseId);
            $groups = Courses::groupsForCourse($courseId);
            $groupMap = Courses::studentGroupMap($courseId);
            $progress = Courses::rosterProgress($courseId);
            $teachers = Courses::teachers($courseId);
            $teacherOptions = $isFullAdmin
                ? $pdo->query("SELECT username, display_name FROM users WHERE role = 'admin' AND active = 1 ORDER BY display_name")->fetchAll()
                : [];

            // Un alumno pertenece a un solo grupo por curso (ver
            // Courses::moveStudentToGroup): el map se aplana a "en qué
            // columna va".
            $groupedIds = [];
            foreach ($groupMap as $uid => $gs) {
                if ($gs) {
                    $groupedIds[(int) $uid] = (int) $gs[0]['id'];
                }
            }
            $sinGrupo = array_values(array_filter($students, static fn(array $s): bool => !isset($groupedIds[(int) $s['id']])));

            // Chips "todos los que vinieron del curso Moodle X" del panel de
            // candidatos (ver user_lti_contexts).
            $origins = [];
            foreach ($enrollable as $u) {
                $o = trim((string) ($u['origin'] ?? ''));
                if ($o !== '') {
                    $origins[$o] = ($origins[$o] ?? 0) + 1;
                }
            }
            ksort($origins);
            admin_add_js('course/board.js');
            break;

        case 'modulos':
            $enabledModules = Courses::enabledModules($courseId);
            break;

        case 'agenda':
            $ventanaDias = 30;
            $proximas = CourseOverview::proximasCitas($courseId, $ventanaDias);
            $conteoCitas = CourseOverview::conteoCitas($courseId);
            break;

        case 'vinculos':
            $vinculos = Lti::contextsForCourse($courseId);
            // Claves que matriculan a este curso por sí solas: la otra
            // mitad de la misma pregunta ("¿de dónde entran los alumnos de
            // este curso?"), y la única que hace la matrícula inmediata.
            $clavesLti = Lti::platformsForCourse($courseId);
            break;

        case 'pruebas':
            $demoStudent = null;
            foreach (Courses::students($courseId) as $s) {
                if ($s['is_demo']) {
                    $demoStudent = $s;
                    break;
                }
            }
            break;
    }

    admin_header($course['name'], $me);
    ?>
    <p class="help help--xs" style="margin-top:-0.6rem;">
        <?= $course['active'] ? 'Curso activo' : '<strong>Curso archivado</strong>' ?>
        &nbsp;·&nbsp; <?= (int) $counts['alumnos'] ?> alumno(s) &middot; <?= (int) $counts['docentes'] ?> docente(s) &middot; <?= (int) $counts['grupos'] ?> grupo(s)
        <?php if ($isFullAdmin): ?>&nbsp;·&nbsp; <a href="courses.php">Todos los cursos</a><?php endif; ?>
    </p>
    <?php include __DIR__ . '/../../views/course/_tabs.php'; ?>
    <?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
    <?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>
    <?php
    include __DIR__ . '/../../views/course/_' . $activeTab . '.php';
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
if ($error !== null) {
    echo '<p class="error">' . htmlspecialchars($error) . '</p>';
}
if ($success !== null) {
    echo '<p class="success">' . htmlspecialchars($success) . '</p>';
}
include __DIR__ . '/../../views/course/_lista.php';
admin_footer();
