<?php
/**
 * LabSim Backend - Agenda de Atención
 *
 * GET    /agenda                     → Lista citas (visibilidad cruzada para docentes)
 * POST   /agenda                     → Crear cita (con detección de conflictos)
 * PUT    /agenda/:id                 → Actualizar cita
 * POST   /agenda/:id/reschedule      → Estudiante reagenda su cita
 * POST   /agenda/:id/status          → Cambiar estado
 * DELETE /agenda/:id                 → Cancelar cita
 * POST   /agenda/assign-group        → Asignar agenda a grupo o curso
 * GET    /agenda/conflicts           → Detectar conflictos de horario
 * GET    /agenda/student/:id         → Agenda global de un estudiante
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;
$action = $routeSegments[1] ?? null;

switch (true) {

    // ─── LISTAR CITAS (visibilidad cruzada) ──────────
    case $method === 'GET' && $id === null:
        $auth = require_auth();

        $where = ['a.is_active = 1'];
        $params = [];

        $from = query_param('from');
        if ($from) { $where[] = 'a.scheduled_date >= :from'; $params[':from'] = $from; }
        $to = query_param('to');
        if ($to) { $where[] = 'a.scheduled_date <= :to'; $params[':to'] = $to; }

        $status = query_param('status');
        if ($status) { $where[] = 'a.status = :status'; $params[':status'] = $status; }

        $procedureId = query_param('procedureId');
        if ($procedureId) { $where[] = 'a.procedure_id = :pid'; $params[':pid'] = $procedureId; }

        $courseId = query_param('courseId');
        if ($courseId) { $where[] = 'a.course_id = :cid_filter'; $params[':cid_filter'] = $courseId; }

        if ($auth['role'] === 'estudiante') {
            // Estudiante ve solo citas asignadas a él
            $where[] = "(a.assigned_to = :uid OR EXISTS (
                SELECT 1 FROM practice_sessions ps
                JOIN group_members gm ON gm.group_id = ps.group_id
                WHERE ps.id = a.session_id AND gm.user_id = :uid2
            ))";
            $params[':uid'] = $auth['sub'];
            $params[':uid2'] = $auth['sub'];
        } elseif ($auth['role'] !== 'admin') {
            // VISIBILIDAD CRUZADA: docente/instructor ve items de TODOS los estudiantes
            // que están en algún curso donde él es miembro
            $where[] = "(a.author_id = :myid OR a.assigned_to IN (
                SELECT cm.user_id FROM course_members cm
                WHERE cm.course_id IN (
                    SELECT cm2.course_id FROM course_members cm2 WHERE cm2.user_id = :myid2
                )
                AND cm.role = 'estudiante'
            ))";
            $params[':myid'] = $auth['sub'];
            $params[':myid2'] = $auth['sub'];
        }
        // admin ve todo

        $sql = "SELECT a.*,
                       a.course_id,
                       p.name as procedure_name, p.code as procedure_code, p.category as procedure_category,
                       u.username as author_username, u.full_name as author_name,
                       au.username as assigned_username, au.full_name as assigned_name,
                       co.name as course_name, co.code as course_code
                FROM agenda_items a
                LEFT JOIN procedures p ON a.procedure_id = p.id
                LEFT JOIN users u ON a.author_id = u.id
                LEFT JOIN users au ON a.assigned_to = au.id
                LEFT JOIN courses co ON a.course_id = co.id
                WHERE " . implode(' AND ', $where) . "
                ORDER BY a.scheduled_date, a.scheduled_time";

        $page = query_int('page', 1);
        $limit = query_int('limit', DEFAULT_PAGE_SIZE);
        json_response(Database::paginate($sql, $params, $page, $limit));
        break;

    // ─── DETECTAR CONFLICTOS ─────────────────────────
    case $method === 'GET' && $id === 'conflicts':
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $studentId = query_param('studentId');
        $date = query_param('date');
        $time = query_param('time');
        $duration = query_int('duration', 30);

        if (!$studentId || !$date || !$time) {
            error_response('Se requiere studentId, date y time', 400);
        }

        // Calcular hora de fin del nuevo item
        $startMinutes = intval(substr($time, 0, 2)) * 60 + intval(substr($time, 3, 2));
        $endMinutes = $startMinutes + $duration;

        $conflicts = Database::fetchAll(
            "SELECT a.*, u.full_name as author_name, co.name as course_name
             FROM agenda_items a
             LEFT JOIN users u ON a.author_id = u.id
             LEFT JOIN courses co ON a.course_id = co.id
             WHERE a.assigned_to = :sid
             AND a.scheduled_date = :date
             AND a.is_active = 1
             AND a.status NOT IN ('cancelled', 'rescheduled')
             ORDER BY a.scheduled_time",
            [':sid' => $studentId, ':date' => $date]
        );

        // Filtrar solapamientos en PHP (más preciso que SQL con tiempos)
        $overlapping = [];
        foreach ($conflicts as $c) {
            $cStart = intval(substr($c['scheduled_time'], 0, 2)) * 60 + intval(substr($c['scheduled_time'], 3, 2));
            $cEnd = $cStart + intval($c['duration_minutes']);

            if ($startMinutes < $cEnd && $endMinutes > $cStart) {
                $overlapping[] = $c;
            }
        }

        json_response(['conflicts' => $overlapping, 'hasConflicts' => count($overlapping) > 0]);
        break;

    // ─── AGENDA GLOBAL DE UN ESTUDIANTE ──────────────
    case $method === 'GET' && $id === 'student' && $action !== null:
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $studentId = $action;

        $where = ['a.is_active = 1', 'a.assigned_to = :sid'];
        $params = [':sid' => $studentId];

        $from = query_param('from');
        if ($from) { $where[] = 'a.scheduled_date >= :from'; $params[':from'] = $from; }
        $to = query_param('to');
        if ($to) { $where[] = 'a.scheduled_date <= :to'; $params[':to'] = $to; }

        $sql = "SELECT a.*,
                       p.name as procedure_name,
                       u.full_name as author_name, u.username as author_username,
                       co.name as course_name, co.code as course_code
                FROM agenda_items a
                LEFT JOIN procedures p ON a.procedure_id = p.id
                LEFT JOIN users u ON a.author_id = u.id
                LEFT JOIN courses co ON a.course_id = co.id
                WHERE " . implode(' AND ', $where) . "
                ORDER BY a.scheduled_date, a.scheduled_time";

        $rows = Database::fetchAll($sql, $params);
        json_response(['data' => $rows]);
        break;

    // ─── CREAR CITA (con conflictos) ─────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $body = get_json_body();

        $errors = validate_required($body, ['patientName', 'scheduledDate', 'scheduledTime']);
        $errors[] = validate_date($body['scheduledDate'] ?? null);
        $errors[] = validate_time($body['scheduledTime'] ?? null);
        validate_or_fail($errors);

        $duration = $body['durationMinutes'] ?? $body['duration_minutes'] ?? null;
        $procedureId = $body['procedureId'] ?? $body['procedure_id'] ?? null;

        if ($procedureId && !$duration) {
            $proc = Database::fetchOne('SELECT default_duration_minutes FROM procedures WHERE id = :id', [':id' => $procedureId]);
            if ($proc) $duration = $proc['default_duration_minutes'];
        }
        $duration = $duration ?? 30;

        $assignedTo = $body['assignedTo'] ?? $body['assigned_to'] ?? null;
        $courseId = $body['courseId'] ?? $body['course_id'] ?? null;

        // Detectar conflictos si hay estudiante asignado
        $conflicts = [];
        if ($assignedTo) {
            $date = $body['scheduledDate'] ?? $body['scheduled_date'];
            $time = $body['scheduledTime'] ?? $body['scheduled_time'];
            $startMin = intval(substr($time, 0, 2)) * 60 + intval(substr($time, 3, 2));
            $endMin = $startMin + $duration;

            $existing = Database::fetchAll(
                "SELECT a.id, a.patient_name, a.scheduled_time, a.duration_minutes, u.full_name as author_name
                 FROM agenda_items a LEFT JOIN users u ON a.author_id = u.id
                 WHERE a.assigned_to = :sid AND a.scheduled_date = :date
                 AND a.is_active = 1 AND a.status NOT IN ('cancelled', 'rescheduled')",
                [':sid' => $assignedTo, ':date' => $date]
            );
            foreach ($existing as $e) {
                $eStart = intval(substr($e['scheduled_time'], 0, 2)) * 60 + intval(substr($e['scheduled_time'], 3, 2));
                $eEnd = $eStart + intval($e['duration_minutes']);
                if ($startMin < $eEnd && $endMin > $eStart) {
                    $conflicts[] = $e;
                }
            }
        }

        $itemId = Database::uuid();
        Database::execute(
            "INSERT INTO agenda_items (id, author_id, patient_name, patient_age, patient_gender,
                patient_notes, procedure_id, scheduled_date, scheduled_time, duration_minutes,
                status, case_id, assigned_to, session_id, course_id)
             VALUES (:id, :uid, :patient, :age, :gender, :notes, :proc, :date, :time, :dur,
                'scheduled', :cid, :assigned, :sid, :courseid)",
            [
                ':id' => $itemId,
                ':uid' => $auth['sub'],
                ':patient' => $body['patientName'] ?? $body['patient_name'],
                ':age' => $body['patientAge'] ?? $body['patient_age'] ?? null,
                ':gender' => $body['patientGender'] ?? $body['patient_gender'] ?? null,
                ':notes' => $body['patientNotes'] ?? $body['patient_notes'] ?? null,
                ':proc' => $procedureId,
                ':date' => $body['scheduledDate'] ?? $body['scheduled_date'],
                ':time' => $body['scheduledTime'] ?? $body['scheduled_time'],
                ':dur' => $duration,
                ':cid' => $body['caseId'] ?? $body['case_id'] ?? null,
                ':assigned' => $assignedTo,
                ':sid' => $body['sessionId'] ?? $body['session_id'] ?? null,
                ':courseid' => $courseId,
            ]
        );

        $item = Database::fetchOne(
            "SELECT a.*, p.name as procedure_name, p.code as procedure_code
             FROM agenda_items a LEFT JOIN procedures p ON a.procedure_id = p.id
             WHERE a.id = :id",
            [':id' => $itemId]
        );

        $response = ['item' => $item];
        if (!empty($conflicts)) {
            $response['conflicts'] = $conflicts;
        }
        created_response($response);
        break;

    // ─── ASIGNAR A GRUPO O CURSO ─────────────────────
    case $method === 'POST' && $id === 'assign-group':
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $body = get_json_body();

        $errors = validate_required($body, ['patientName', 'scheduledDate', 'scheduledTime']);
        validate_or_fail($errors);

        // Obtener miembros: desde courseId o groupId
        $courseId = $body['courseId'] ?? $body['course_id'] ?? null;
        $groupId = $body['groupId'] ?? $body['group_id'] ?? null;

        if ($courseId) {
            $members = Database::fetchAll(
                "SELECT user_id FROM course_members WHERE course_id = :cid AND role = 'estudiante'",
                [':cid' => $courseId]
            );
        } elseif ($groupId) {
            $members = Database::fetchAll(
                "SELECT user_id FROM group_members WHERE group_id = :gid AND member_role = 'student'",
                [':gid' => $groupId]
            );
        } else {
            error_response('Se requiere courseId o groupId', 400);
        }

        $procedureId = $body['procedureId'] ?? $body['procedure_id'] ?? null;
        $duration = $body['durationMinutes'] ?? $body['duration_minutes'] ?? null;
        if ($procedureId && !$duration) {
            $proc = Database::fetchOne('SELECT default_duration_minutes FROM procedures WHERE id = :id', [':id' => $procedureId]);
            if ($proc) $duration = $proc['default_duration_minutes'];
        }
        $duration = $duration ?? 30;

        $date = $body['scheduledDate'] ?? $body['scheduled_date'];
        $time = $body['scheduledTime'] ?? $body['scheduled_time'];
        $startMin = intval(substr($time, 0, 2)) * 60 + intval(substr($time, 3, 2));
        $endMin = $startMin + $duration;

        $created = 0;
        $conflictStudents = [];

        foreach ($members as $member) {
            // Chequear conflictos por estudiante
            $existing = Database::fetchAll(
                "SELECT a.scheduled_time, a.duration_minutes FROM agenda_items a
                 WHERE a.assigned_to = :sid AND a.scheduled_date = :date
                 AND a.is_active = 1 AND a.status NOT IN ('cancelled', 'rescheduled')",
                [':sid' => $member['user_id'], ':date' => $date]
            );
            $hasConflict = false;
            foreach ($existing as $e) {
                $eStart = intval(substr($e['scheduled_time'], 0, 2)) * 60 + intval(substr($e['scheduled_time'], 3, 2));
                $eEnd = $eStart + intval($e['duration_minutes']);
                if ($startMin < $eEnd && $endMin > $eStart) {
                    $hasConflict = true;
                    $student = Database::fetchOne('SELECT full_name FROM users WHERE id = :id', [':id' => $member['user_id']]);
                    $conflictStudents[] = $student['full_name'] ?? $member['user_id'];
                    break;
                }
            }

            $itemId = Database::uuid();
            Database::execute(
                "INSERT INTO agenda_items (id, author_id, patient_name, patient_age, patient_gender,
                    patient_notes, procedure_id, scheduled_date, scheduled_time, duration_minutes,
                    status, case_id, assigned_to, session_id, course_id)
                 VALUES (:id, :uid, :patient, :age, :gender, :notes, :proc, :date, :time, :dur,
                    'scheduled', :cid, :assigned, :sid, :courseid)",
                [
                    ':id' => $itemId,
                    ':uid' => $auth['sub'],
                    ':patient' => $body['patientName'] ?? $body['patient_name'],
                    ':age' => $body['patientAge'] ?? $body['patient_age'] ?? null,
                    ':gender' => $body['patientGender'] ?? $body['patient_gender'] ?? null,
                    ':notes' => $body['patientNotes'] ?? $body['patient_notes'] ?? null,
                    ':proc' => $procedureId,
                    ':date' => $date,
                    ':time' => $time,
                    ':dur' => $duration,
                    ':cid' => $body['caseId'] ?? $body['case_id'] ?? null,
                    ':assigned' => $member['user_id'],
                    ':sid' => $body['sessionId'] ?? $body['session_id'] ?? null,
                    ':courseid' => $courseId,
                ]
            );
            $created++;
        }

        $response = ['message' => "Cita asignada a $created estudiantes", 'count' => $created];
        if (!empty($conflictStudents)) {
            $response['conflictStudents'] = $conflictStudents;
            $response['conflictCount'] = count($conflictStudents);
        }
        json_response($response);
        break;

    // ─── REAGENDAR (estudiante) ─────────────────────
    case $method === 'POST' && $id !== null && $action === 'reschedule':
        $auth = require_auth();
        $body = get_json_body();

        $item = Database::fetchOne('SELECT * FROM agenda_items WHERE id = :id AND is_active = 1', [':id' => $id]);
        if (!$item) error_response('Cita no encontrada', 404);

        if ($item['assigned_to'] !== $auth['sub']) {
            error_response('Solo puedes reagendar tus propias citas', 403);
        }

        if (!in_array($item['status'], ['scheduled', 'completed'])) {
            error_response('Solo se pueden reagendar citas programadas o completadas', 400);
        }

        $errors = validate_required($body, ['scheduledDate', 'scheduledTime']);
        $errors[] = validate_date($body['scheduledDate'] ?? null);
        $errors[] = validate_time($body['scheduledTime'] ?? null);
        validate_or_fail($errors);

        Database::execute(
            "UPDATE agenda_items SET status = 'rescheduled', rescheduled_date = :date, rescheduled_time = :time WHERE id = :id",
            [':id' => $id, ':date' => $body['scheduledDate'], ':time' => $body['scheduledTime']]
        );

        $newId = Database::uuid();
        Database::execute(
            "INSERT INTO agenda_items (id, author_id, patient_name, patient_age, patient_gender,
                patient_notes, procedure_id, scheduled_date, scheduled_time, duration_minutes,
                status, case_id, assigned_to, session_id, course_id, rescheduled_from)
             VALUES (:id, :uid, :patient, :age, :gender, :notes, :proc, :date, :time, :dur,
                'scheduled', :cid, :assigned, :sid, :courseid, :from)",
            [
                ':id' => $newId,
                ':uid' => $item['author_id'],
                ':patient' => $item['patient_name'],
                ':age' => $item['patient_age'],
                ':gender' => $item['patient_gender'],
                ':notes' => $item['patient_notes'],
                ':proc' => $item['procedure_id'],
                ':date' => $body['scheduledDate'],
                ':time' => $body['scheduledTime'],
                ':dur' => $item['duration_minutes'],
                ':cid' => $item['case_id'],
                ':assigned' => $auth['sub'],
                ':sid' => $item['session_id'],
                ':courseid' => $item['course_id'],
                ':from' => $id,
            ]
        );

        json_response([
            'message' => 'Cita reagendada',
            'originalId' => $id,
            'newItem' => Database::fetchOne('SELECT * FROM agenda_items WHERE id = :id', [':id' => $newId]),
        ]);
        break;

    // ─── CAMBIAR ESTADO ─────────────────────────────
    case $method === 'POST' && $id !== null && $action === 'status':
        $auth = require_auth();
        $body = get_json_body();

        $item = Database::fetchOne('SELECT id, assigned_to, status FROM agenda_items WHERE id = :id', [':id' => $id]);
        if (!$item) error_response('Cita no encontrada', 404);

        $newStatus = $body['status'] ?? null;
        $allowed = ['in_progress', 'completed', 'no_show'];
        if (!$newStatus || !in_array($newStatus, $allowed)) {
            error_response('Estado inválido. Permitidos: ' . implode(', ', $allowed), 400);
        }

        if ($auth['role'] === 'estudiante') {
            if ($item['assigned_to'] !== $auth['sub']) {
                error_response('Solo puedes actualizar tus propias citas', 403);
            }
            if ($newStatus === 'no_show') {
                error_response('Solo docentes pueden marcar inasistencia', 403);
            }
        }

        $params = [':id' => $id, ':status' => $newStatus];
        $extra = '';
        if ($newStatus === 'completed') {
            $extra = ", completion_notes = :notes";
            $params[':notes'] = $body['notes'] ?? $body['completionNotes'] ?? null;
        }

        Database::execute("UPDATE agenda_items SET status = :status $extra WHERE id = :id", $params);
        json_response(['message' => 'Estado actualizado', 'status' => $newStatus]);
        break;

    // ─── ACTUALIZAR CITA ────────────────────────────
    case $method === 'PUT' && $id !== null && $action === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $item = Database::fetchOne('SELECT id, author_id FROM agenda_items WHERE id = :id', [':id' => $id]);
        if (!$item) error_response('Cita no encontrada', 404);

        if ($auth['role'] !== 'admin' && $auth['sub'] !== $item['author_id']) {
            error_response('Permisos insuficientes', 403);
        }

        $body = get_json_body();
        $fields = [];
        $params = [':id' => $id];

        $mapping = [
            'patientName' => 'patient_name', 'patient_name' => 'patient_name',
            'patientAge' => 'patient_age', 'patient_age' => 'patient_age',
            'patientGender' => 'patient_gender', 'patient_gender' => 'patient_gender',
            'patientNotes' => 'patient_notes', 'patient_notes' => 'patient_notes',
            'procedureId' => 'procedure_id', 'procedure_id' => 'procedure_id',
            'scheduledDate' => 'scheduled_date', 'scheduled_date' => 'scheduled_date',
            'scheduledTime' => 'scheduled_time', 'scheduled_time' => 'scheduled_time',
            'durationMinutes' => 'duration_minutes', 'duration_minutes' => 'duration_minutes',
            'caseId' => 'case_id', 'case_id' => 'case_id',
            'assignedTo' => 'assigned_to', 'assigned_to' => 'assigned_to',
            'sessionId' => 'session_id', 'session_id' => 'session_id',
            'courseId' => 'course_id', 'course_id' => 'course_id',
        ];

        foreach ($body as $key => $value) {
            if (isset($mapping[$key])) {
                $dbKey = $mapping[$key];
                $fields[] = "$dbKey = :$dbKey";
                $params[":$dbKey"] = $value;
            }
        }

        if (empty($fields)) error_response('No hay campos para actualizar', 400);

        Database::execute("UPDATE agenda_items SET " . implode(', ', $fields) . " WHERE id = :id", $params);

        $updated = Database::fetchOne(
            "SELECT a.*, p.name as procedure_name FROM agenda_items a LEFT JOIN procedures p ON a.procedure_id = p.id WHERE a.id = :id",
            [':id' => $id]
        );
        json_response(['item' => $updated]);
        break;

    // ─── CANCELAR CITA ──────────────────────────────
    case $method === 'DELETE' && $id !== null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $item = Database::fetchOne('SELECT id, author_id FROM agenda_items WHERE id = :id', [':id' => $id]);
        if (!$item) error_response('Cita no encontrada', 404);

        if ($auth['role'] !== 'admin' && $auth['sub'] !== $item['author_id']) {
            error_response('Permisos insuficientes', 403);
        }

        Database::execute("UPDATE agenda_items SET status = 'cancelled', is_active = 0 WHERE id = :id", [':id' => $id]);
        json_response(['message' => 'Cita cancelada']);
        break;

    default:
        error_response("Ruta no encontrada: agenda/" . implode('/', $routeSegments), 404);
}
