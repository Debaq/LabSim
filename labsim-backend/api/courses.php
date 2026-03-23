<?php
/**
 * LabSim Backend - Cursos
 *
 * GET    /courses                    → Listar cursos
 * POST   /courses                    → Crear curso (admin o docente)
 * GET    /courses/:id                → Detalle + miembros
 * PUT    /courses/:id                → Actualizar
 * POST   /courses/:id/members        → Inscribir estudiante
 * DELETE /courses/:id/members/:uid   → Quitar estudiante
 * POST   /courses/:id/import         → Bulk import CSV
 * DELETE /courses/:id                → Eliminar curso
 * PUT    /courses/:id/archive        → Archivar/desarchivar curso
 * POST   /courses/:id/duplicate      → Duplicar curso
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;
$action = $routeSegments[1] ?? null;
$subId = $routeSegments[2] ?? null;

switch (true) {

    // ─── LISTAR CURSOS ───────────────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth();

        $where = ['c.is_active = 1'];
        $params = [];

        if ($auth['role'] === 'estudiante') {
            // Estudiante ve solo sus cursos
            $where[] = "EXISTS (SELECT 1 FROM course_members cm WHERE cm.course_id = c.id AND cm.user_id = :uid)";
            $params[':uid'] = $auth['sub'];
        } elseif ($auth['role'] !== 'admin') {
            // Docente/instructor ve cursos donde es miembro o creador
            $where[] = "(c.created_by = :uid OR EXISTS (SELECT 1 FROM course_members cm WHERE cm.course_id = c.id AND cm.user_id = :uid2))";
            $params[':uid'] = $auth['sub'];
            $params[':uid2'] = $auth['sub'];
        }

        $institutionId = query_param('institution_id');
        if ($institutionId) {
            $where[] = 'c.institution_id = :iid';
            $params[':iid'] = $institutionId;
        }

        $sql = "SELECT c.*, u.full_name as creator_name, u.username as creator_username,
                       (SELECT COUNT(*) FROM course_members cm WHERE cm.course_id = c.id AND cm.role = 'estudiante') as student_count
                FROM courses c
                LEFT JOIN users u ON c.created_by = u.id
                WHERE " . implode(' AND ', $where) . "
                ORDER BY c.created_at DESC";

        $rows = Database::fetchAll($sql, $params);
        json_response(['data' => $rows]);
        break;

    // ─── CREAR CURSO ─────────────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth(['admin', 'docente']);
        $body = get_json_body();

        $errors = validate_required($body, ['name']);
        validate_or_fail($errors);

        // Determinar institución
        $institutionId = $body['institutionId'] ?? null;
        if (!$institutionId) {
            // Usar la institución del usuario
            $user = Database::fetchOne('SELECT institution_id FROM users WHERE id = :id', [':id' => $auth['sub']]);
            $institutionId = $user['institution_id'] ?? null;
        }
        if (!$institutionId) {
            error_response('No se pudo determinar la institución', 400);
        }

        $courseId = Database::uuid();
        Database::execute(
            "INSERT INTO courses (id, institution_id, name, code, description, created_by, period)
             VALUES (:id, :iid, :name, :code, :desc, :creator, :period)",
            [
                ':id' => $courseId,
                ':iid' => $institutionId,
                ':name' => $body['name'],
                ':code' => $body['code'] ?? null,
                ':desc' => $body['description'] ?? null,
                ':creator' => $auth['sub'],
                ':period' => $body['period'] ?? null,
            ]
        );

        // Auto-agregar creador como docente del curso
        Database::execute(
            "INSERT INTO course_members (course_id, user_id, role) VALUES (:cid, :uid, 'docente')",
            [':cid' => $courseId, ':uid' => $auth['sub']]
        );

        $course = Database::fetchOne('SELECT * FROM courses WHERE id = :id', [':id' => $courseId]);
        created_response(['course' => $course]);
        break;

    // ─── DETALLE CURSO + MIEMBROS ────────────────────
    case $method === 'GET' && $id !== null && $action === null:
        $auth = require_auth();

        $course = Database::fetchOne(
            "SELECT c.*, u.full_name as creator_name
             FROM courses c LEFT JOIN users u ON c.created_by = u.id
             WHERE c.id = :id",
            [':id' => $id]
        );
        if (!$course) error_response('Curso no encontrado', 404);

        $members = Database::fetchAll(
            "SELECT cm.role, cm.enrolled_at, u.id, u.username, u.full_name, u.email, u.student_id_number
             FROM course_members cm
             JOIN users u ON cm.user_id = u.id
             WHERE cm.course_id = :cid
             ORDER BY cm.role, u.full_name",
            [':cid' => $id]
        );

        json_response(['course' => $course, 'members' => $members]);
        break;

    // ─── ACTUALIZAR CURSO ────────────────────────────
    case $method === 'PUT' && $id !== null && $action === null:
        $auth = require_auth(['admin', 'docente']);
        $body = get_json_body();

        $course = Database::fetchOne('SELECT id, created_by FROM courses WHERE id = :id', [':id' => $id]);
        if (!$course) error_response('Curso no encontrado', 404);

        if ($auth['role'] !== 'admin' && $auth['sub'] !== $course['created_by']) {
            error_response('Solo el creador o un admin puede editar este curso', 403);
        }

        $fields = [];
        $params = [':id' => $id];
        foreach (['name', 'code', 'description', 'period'] as $f) {
            $camel = $f;
            if (isset($body[$camel])) {
                $fields[] = "$f = :$f";
                $params[":$f"] = $body[$camel];
            }
        }
        if (isset($body['isActive'])) {
            $fields[] = 'is_active = :active';
            $params[':active'] = (int)$body['isActive'];
        }

        if (empty($fields)) error_response('No hay campos para actualizar', 400);

        Database::execute("UPDATE courses SET " . implode(', ', $fields) . " WHERE id = :id", $params);
        $updated = Database::fetchOne('SELECT * FROM courses WHERE id = :id', [':id' => $id]);
        json_response(['course' => $updated]);
        break;

    // ─── INSCRIBIR ESTUDIANTE ────────────────────────
    case $method === 'POST' && $id !== null && $action === 'members' && $subId === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $body = get_json_body();

        $errors = validate_required($body, ['userId']);
        validate_or_fail($errors);

        $course = Database::fetchOne('SELECT id FROM courses WHERE id = :id', [':id' => $id]);
        if (!$course) error_response('Curso no encontrado', 404);

        $user = Database::fetchOne('SELECT id, is_active FROM users WHERE id = :id', [':id' => $body['userId']]);
        if (!$user || !$user['is_active']) error_response('Usuario no encontrado o inactivo', 404);

        // Verificar si ya es miembro
        $existing = Database::fetchOne(
            'SELECT course_id FROM course_members WHERE course_id = :cid AND user_id = :uid',
            [':cid' => $id, ':uid' => $body['userId']]
        );
        if ($existing) error_response('El usuario ya está inscrito en este curso', 409);

        Database::execute(
            "INSERT INTO course_members (course_id, user_id, role) VALUES (:cid, :uid, :role)",
            [':cid' => $id, ':uid' => $body['userId'], ':role' => $body['role'] ?? 'estudiante']
        );

        json_response(['message' => 'Estudiante inscrito']);
        break;

    // ─── QUITAR ESTUDIANTE ───────────────────────────
    case $method === 'DELETE' && $id !== null && $action === 'members' && $subId !== null:
        $auth = require_auth(['admin', 'docente']);

        Database::execute(
            'DELETE FROM course_members WHERE course_id = :cid AND user_id = :uid',
            [':cid' => $id, ':uid' => $subId]
        );
        json_response(['message' => 'Miembro eliminado del curso']);
        break;

    // ─── BULK IMPORT CSV ─────────────────────────────
    case $method === 'POST' && $id !== null && $action === 'import':
        $auth = require_auth(['admin', 'docente']);
        $body = get_json_body();

        $course = Database::fetchOne(
            'SELECT c.id, c.institution_id FROM courses c WHERE c.id = :id',
            [':id' => $id]
        );
        if (!$course) error_response('Curso no encontrado', 404);

        $rows = $body['students'] ?? [];
        if (empty($rows)) error_response('No se recibieron estudiantes', 400);

        $created = 0;
        $found = 0;
        $enrolled = 0;
        $errors = [];

        foreach ($rows as $i => $row) {
            $fullName = trim($row['fullName'] ?? $row['nombre'] ?? '');
            $studentId = trim($row['studentId'] ?? $row['identificador'] ?? $row['run'] ?? '');
            $email = trim($row['email'] ?? $row['correo'] ?? '');

            if (!$fullName && !$studentId) {
                $errors[] = "Fila " . ($i + 1) . ": sin nombre ni identificador";
                continue;
            }

            // Buscar si ya existe en la institución
            $existingUser = null;
            if ($studentId) {
                $existingUser = Database::fetchOne(
                    "SELECT id FROM users WHERE student_id_number = :sid AND institution_id = :iid AND is_active = 1",
                    [':sid' => $studentId, ':iid' => $course['institution_id']]
                );
            }
            if (!$existingUser && $email) {
                $existingUser = Database::fetchOne(
                    "SELECT id FROM users WHERE email = :email AND institution_id = :iid AND is_active = 1",
                    [':email' => $email, ':iid' => $course['institution_id']]
                );
            }

            if ($existingUser) {
                $userId = $existingUser['id'];
                $found++;
            } else {
                // Crear usuario nuevo
                $userId = Database::uuid();
                // Generar username desde nombre o studentId
                $username = $studentId ?: strtolower(str_replace(' ', '.', $fullName));
                $username = preg_replace('/[^a-zA-Z0-9._-]/', '', $username);

                // Verificar unicidad de username
                $suffix = '';
                $baseUsername = $username;
                while (Database::fetchOne('SELECT id FROM users WHERE username = :u', [':u' => $username . $suffix])) {
                    $suffix = $suffix === '' ? '1' : (string)((int)$suffix + 1);
                }
                $username = $baseUsername . $suffix;

                // Contraseña temporal = identificador
                $tempPassword = $studentId ?: 'labsim2026';
                $passwordHash = password_hash($tempPassword, PASSWORD_BCRYPT);

                Database::execute(
                    "INSERT INTO users (id, username, email, password_hash, role, full_name, institution_id, student_id_number, must_change_password)
                     VALUES (:id, :user, :email, :pass, 'estudiante', :name, :iid, :sid, 1)",
                    [
                        ':id' => $userId,
                        ':user' => $username,
                        ':email' => $email ?: null,
                        ':pass' => $passwordHash,
                        ':name' => $fullName,
                        ':iid' => $course['institution_id'],
                        ':sid' => $studentId ?: null,
                    ]
                );
                $created++;
            }

            // Inscribir en el curso si no está ya
            $alreadyEnrolled = Database::fetchOne(
                'SELECT course_id FROM course_members WHERE course_id = :cid AND user_id = :uid',
                [':cid' => $id, ':uid' => $userId]
            );
            if (!$alreadyEnrolled) {
                Database::execute(
                    "INSERT INTO course_members (course_id, user_id, role) VALUES (:cid, :uid, 'estudiante')",
                    [':cid' => $id, ':uid' => $userId]
                );
                $enrolled++;
            }
        }

        json_response([
            'summary' => [
                'created' => $created,
                'found' => $found,
                'enrolled' => $enrolled,
                'errors' => $errors,
                'total' => count($rows),
            ],
        ]);
        break;

    // ─── ELIMINAR CURSO ─────────────────────────────
    case $method === 'DELETE' && $id !== null && $action === null:
        $auth = require_auth(['admin', 'docente']);

        $course = Database::fetchOne('SELECT id, created_by FROM courses WHERE id = :id', [':id' => $id]);
        if (!$course) error_response('Curso no encontrado', 404);

        if ($auth['role'] !== 'admin' && $auth['sub'] !== $course['created_by']) {
            error_response('Solo el creador o un admin puede eliminar este curso', 403);
        }

        // Verificar que no tenga sesiones activas
        $activeSessions = Database::fetchOne(
            "SELECT COUNT(*) as count FROM practice_sessions
             WHERE course_id = :cid AND status IN ('approved','active')",
            [':cid' => $id]
        );
        if (($activeSessions['count'] ?? 0) > 0) {
            error_response('No se puede eliminar: el curso tiene sesiones activas', 409);
        }

        Database::execute('DELETE FROM course_members WHERE course_id = :cid', [':cid' => $id]);
        Database::execute('DELETE FROM courses WHERE id = :id', [':id' => $id]);

        json_response(['message' => 'Curso eliminado']);
        break;

    // ─── ARCHIVAR/DESARCHIVAR CURSO ─────────────────
    case $method === 'PUT' && $id !== null && $action === 'archive':
        $auth = require_auth(['admin', 'docente']);

        $course = Database::fetchOne('SELECT id, is_active FROM courses WHERE id = :id', [':id' => $id]);
        if (!$course) error_response('Curso no encontrado', 404);

        $newState = $course['is_active'] ? 0 : 1;
        Database::execute(
            "UPDATE courses SET is_active = :active WHERE id = :id",
            [':id' => $id, ':active' => $newState]
        );

        json_response([
            'message' => $newState ? 'Curso desarchivado' : 'Curso archivado',
            'is_active' => $newState,
        ]);
        break;

    // ─── DUPLICAR CURSO ─────────────────────────────
    case $method === 'POST' && $id !== null && $action === 'duplicate':
        $auth = require_auth(['admin', 'docente']);

        $course = Database::fetchOne('SELECT * FROM courses WHERE id = :id', [':id' => $id]);
        if (!$course) error_response('Curso no encontrado', 404);

        $newId = Database::uuid();
        Database::execute(
            "INSERT INTO courses (id, institution_id, name, code, description, created_by, period)
             VALUES (:id, :iid, :name, :code, :desc, :creator, :period)",
            [
                ':id' => $newId,
                ':iid' => $course['institution_id'],
                ':name' => 'Copia de ' . $course['name'],
                ':code' => $course['code'] ? $course['code'] . '-copia' : null,
                ':desc' => $course['description'],
                ':creator' => $auth['sub'],
                ':period' => $course['period'],
            ]
        );

        // Auto-agregar creador como docente
        Database::execute(
            "INSERT INTO course_members (course_id, user_id, role) VALUES (:cid, :uid, 'docente')",
            [':cid' => $newId, ':uid' => $auth['sub']]
        );

        $new = Database::fetchOne('SELECT * FROM courses WHERE id = :id', [':id' => $newId]);
        created_response(['course' => $new]);
        break;

    default:
        error_response("Ruta no encontrada: courses/$id" . ($action ? "/$action" : ''), 404);
}
