<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/AdminAudit.php';

/**
 * Mueve un alumno a un grupo (o a "sin grupo") desde el tablero de
 * arrastrar-y-soltar de courses.php -- fetch(), no <form>, por eso
 * devuelve JSON en vez de redirigir. Ver Courses::moveStudentToGroup()
 * para la regla de "un alumno, un solo grupo por curso".
 */

header('Content-Type: application/json; charset=utf-8');

$me = Auth::requireAdminSession();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$myCourseIds = $isFullAdmin ? null : Courses::teacherCourseIds((int) $me['id']);

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Método no permitido.']);
    exit;
}

try {
    Auth::requireCsrf();
} catch (Throwable $e) {
    http_response_code(403);
    echo json_encode(['ok' => false, 'error' => 'Sesión expirada, recarga la página.']);
    exit;
}

$courseId = (int) ($_POST['course_id'] ?? 0);
$userId = (int) ($_POST['user_id'] ?? 0);
$groupIdRaw = trim((string) ($_POST['group_id'] ?? ''));
$groupId = $groupIdRaw === '' ? null : (int) $groupIdRaw;

if ($courseId <= 0 || $userId <= 0) {
    http_response_code(422);
    echo json_encode(['ok' => false, 'error' => 'Datos inválidos.']);
    exit;
}

if (!$isFullAdmin && (!$myCourseIds || !in_array($courseId, $myCourseIds, true))) {
    http_response_code(403);
    echo json_encode(['ok' => false, 'error' => 'No tienes acceso a este curso.']);
    exit;
}

$err = Courses::moveStudentToGroup($courseId, $userId, $groupId);
if ($err) {
    http_response_code(422);
    echo json_encode(['ok' => false, 'error' => $err]);
    exit;
}

AdminAudit::log($me, 'group_move_member', ['course_id' => $courseId, 'user_id' => $userId, 'group_id' => $groupId]);
echo json_encode(['ok' => true]);
