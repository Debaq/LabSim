<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Courses.php';

/**
 * "Ver como alumno": deja al docente/admin entrar al mini-portal de alumno
 * (public/student/) para ver exactamente lo que ese alumno ve (mismo
 * criterio de scoping que student.php), sin necesitar su sesión real.
 * Auth::requireStudentSession() revisa admin_view_as_id + admin_user_id.
 */

$me = Auth::requireAdminSession();

if (isset($_GET['salir'])) {
    $backId = (int) ($_SESSION['admin_view_as_id'] ?? 0);
    unset($_SESSION['admin_view_as_id']);
    header('Location: student.php?id=' . $backId);
    exit;
}

$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$studentId = (int) ($_GET['id'] ?? 0);

$stmt = Db::get()->prepare("SELECT 1 FROM users WHERE id = ? AND role = 'student' AND active = 1");
$stmt->execute([$studentId]);
$exists = (bool) $stmt->fetchColumn();

if ($exists && !$isFullAdmin) {
    $roster = Courses::rosterUserIds(Courses::teacherCourseIds((int) $me['id']));
    if (!in_array($studentId, $roster, true)) {
        $exists = false;
    }
}

if (!$exists) {
    http_response_code(404);
    exit('Alumno no encontrado.');
}

$_SESSION['admin_view_as_id'] = $studentId;
header('Location: ../student/mis_pacientes.php');
