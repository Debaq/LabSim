<?php
/**
 * LabSim Backend - Modalidad Centro (Boxes, Incidentes, Reuniones)
 *
 * ═══ BOXES ═══
 * GET    /center/boxes                    → Boxes de una sesión
 * POST   /center/boxes                    → Configurar boxes
 * PUT    /center/boxes/:id                → Asignar estudiante a box
 *
 * ═══ INCIDENTES ═══
 * GET    /center/incidents/templates       → Biblioteca de incidentes
 * GET    /center/incidents                 → Incidentes activos de la sesión
 * POST   /center/incidents                 → Inyectar incidente (docente/instructor)
 * POST   /center/incidents/:id/resolve     → Resolver incidente
 * POST   /center/incidents/:id/discuss     → Marcar para reunión
 *
 * ═══ REUNIONES CLÍNICAS ═══
 * GET    /center/meetings                  → Reuniones de la sesión
 * POST   /center/meetings                  → Convocar reunión
 * POST   /center/meetings/:id/start        → Iniciar reunión
 * POST   /center/meetings/:id/end          → Finalizar reunión
 * PUT    /center/meetings/:id              → Actualizar actas/decisiones
 *
 * ═══ CHAT ═══
 * GET    /center/chat                      → Mensajes del chat
 * POST   /center/chat                      → Enviar mensaje
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$section = $routeSegments[0] ?? null;
$id = $routeSegments[1] ?? null;
$action = $routeSegments[2] ?? null;

$auth = require_auth();

switch ("$section") {

// ═══════════════════════════════════════════════════
// BOXES
// ═══════════════════════════════════════════════════
case 'boxes':
    switch (true) {

        // Lista boxes de una sesión
        case $method === 'GET' && $id === null:
            $sessionId = query_param('sessionId');
            if (!$sessionId) error_response('sessionId requerido', 400);

            $boxes = Database::fetchAll(
                "SELECT b.*, u.username as student_username, u.full_name as student_name
                 FROM boxes b
                 LEFT JOIN users u ON b.student_id = u.id
                 WHERE b.session_id = :sid
                 ORDER BY b.box_number",
                [':sid' => $sessionId]
            );

            // Agenda de cada box
            foreach ($boxes as &$box) {
                $box['agenda'] = Database::fetchAll(
                    "SELECT a.*, p.name as procedure_name
                     FROM agenda_items a
                     LEFT JOIN procedures p ON a.procedure_id = p.id
                     WHERE a.assigned_to = :uid AND a.session_id = :sid AND a.is_active = 1
                     ORDER BY a.scheduled_time",
                    [':uid' => $box['student_id'] ?? '', ':sid' => $sessionId]
                );
                // Incidentes que afectan este box
                $box['incidents'] = Database::fetchAll(
                    "SELECT * FROM center_incidents
                     WHERE session_id = :sid AND (affected_box = :bn OR affected_box IS NULL) AND status = 'active'
                     ORDER BY created_at",
                    [':sid' => $sessionId, ':bn' => $box['box_number']]
                );
            }

            json_response(['boxes' => $boxes]);
            break;

        // Crear/configurar boxes para una sesión
        case $method === 'POST' && $id === null:
            require_auth(['admin', 'docente', 'instructor']);
            $body = get_json_body();
            $errors = validate_required($body, ['sessionId', 'boxCount']);
            validate_or_fail($errors);

            $sessionId = $body['sessionId'];
            $count = (int)$body['boxCount'];
            $created = [];

            for ($i = 1; $i <= $count; $i++) {
                $existing = Database::fetchOne(
                    "SELECT id FROM boxes WHERE session_id = :sid AND box_number = :bn",
                    [':sid' => $sessionId, ':bn' => $i]
                );
                if (!$existing) {
                    $boxId = Database::uuid();
                    Database::execute(
                        "INSERT INTO boxes (id, session_id, box_number, name) VALUES (:id, :sid, :bn, :name)",
                        [':id' => $boxId, ':sid' => $sessionId, ':bn' => $i, ':name' => "Box $i"]
                    );
                    $created[] = $boxId;
                }
            }

            json_response(['message' => count($created) . ' boxes creados', 'count' => count($created)]);
            break;

        // Asignar estudiante a box
        case $method === 'PUT' && $id !== null:
            require_auth(['admin', 'docente', 'instructor']);
            $body = get_json_body();

            Database::execute(
                "UPDATE boxes SET student_id = :uid, name = COALESCE(:name, name), equipment_list = COALESCE(:equip, equipment_list) WHERE id = :id",
                [
                    ':id' => $id,
                    ':uid' => $body['studentId'] ?? $body['student_id'] ?? null,
                    ':name' => $body['name'] ?? null,
                    ':equip' => $body['equipmentList'] ?? $body['equipment_list'] ?? null,
                ]
            );
            json_response(['box' => Database::fetchOne('SELECT * FROM boxes WHERE id = :id', [':id' => $id])]);
            break;

        default:
            error_response("Ruta no encontrada: center/boxes", 404);
    }
    break;

// ═══════════════════════════════════════════════════
// INCIDENTES
// ═══════════════════════════════════════════════════
case 'incidents':
    switch (true) {

        // Biblioteca de templates
        case $method === 'GET' && $id === 'templates':
            $category = query_param('category');
            $where = ['is_template = 1'];
            $params = [];
            if ($category) { $where[] = 'category = :cat'; $params[':cat'] = $category; }

            $templates = Database::fetchAll(
                "SELECT * FROM center_incidents WHERE " . implode(' AND ', $where) . " ORDER BY category, title",
                $params
            );
            json_response(['templates' => $templates]);
            break;

        // Incidentes activos de una sesión
        case $method === 'GET' && $id === null:
            $sessionId = query_param('sessionId');
            if (!$sessionId) error_response('sessionId requerido', 400);

            $incidents = Database::fetchAll(
                "SELECT i.*, u.username as creator_username, u.full_name as creator_name,
                        r.username as resolver_username
                 FROM center_incidents i
                 LEFT JOIN users u ON i.created_by = u.id
                 LEFT JOIN users r ON i.resolved_by = r.id
                 WHERE i.session_id = :sid AND i.is_template = 0
                 ORDER BY CASE i.status WHEN 'active' THEN 1 WHEN 'discussed' THEN 2 ELSE 3 END, i.created_at",
                [':sid' => $sessionId]
            );
            json_response(['incidents' => $incidents]);
            break;

        // Inyectar incidente en sesión (desde template o custom)
        case $method === 'POST' && $id === null:
            require_auth(['admin', 'docente', 'instructor']);
            $body = get_json_body();
            $errors = validate_required($body, ['sessionId']);
            validate_or_fail($errors);

            $templateId = $body['templateId'] ?? null;
            if ($templateId) {
                $tpl = Database::fetchOne('SELECT * FROM center_incidents WHERE id = :id AND is_template = 1', [':id' => $templateId]);
                if (!$tpl) error_response('Template no encontrado', 404);
                $category = $tpl['category'];
                $title = $tpl['title'];
                $description = $tpl['description'];
                $severity = $tpl['severity'];
            } else {
                $errors2 = validate_required($body, ['title', 'description', 'category']);
                validate_or_fail($errors2);
                $category = $body['category'];
                $title = $body['title'];
                $description = $body['description'];
                $severity = $body['severity'] ?? 'moderate';
            }

            // Reemplazar {box} si se especifica
            $affectedBox = $body['affectedBox'] ?? $body['affected_box'] ?? null;
            if ($affectedBox) {
                $description = str_replace('{box}', (string)$affectedBox, $description);
            }

            $incidentId = Database::uuid();
            Database::execute(
                "INSERT INTO center_incidents (id, session_id, created_by, category, title, description, affected_box, severity, is_template)
                 VALUES (:id, :sid, :uid, :cat, :title, :desc, :box, :sev, 0)",
                [
                    ':id' => $incidentId,
                    ':sid' => $body['sessionId'],
                    ':uid' => $auth['sub'],
                    ':cat' => $category,
                    ':title' => $title,
                    ':desc' => $description,
                    ':box' => $affectedBox,
                    ':sev' => $severity,
                ]
            );

            created_response(['incident' => Database::fetchOne('SELECT * FROM center_incidents WHERE id = :id', [':id' => $incidentId])]);
            break;

        // Resolver incidente
        case $method === 'POST' && $id !== null && $action === 'resolve':
            $body = get_json_body();

            Database::execute(
                "UPDATE center_incidents SET status = 'resolved', resolution_notes = :notes, resolved_by = :uid WHERE id = :id",
                [':id' => $id, ':notes' => $body['notes'] ?? $body['resolutionNotes'] ?? null, ':uid' => $auth['sub']]
            );
            json_response(['message' => 'Incidente resuelto']);
            break;

        // Marcar para discusión en reunión
        case $method === 'POST' && $id !== null && $action === 'discuss':
            Database::execute("UPDATE center_incidents SET status = 'discussed' WHERE id = :id", [':id' => $id]);
            json_response(['message' => 'Marcado para reunión clínica']);
            break;

        default:
            error_response("Ruta no encontrada: center/incidents", 404);
    }
    break;

// ═══════════════════════════════════════════════════
// REUNIONES CLÍNICAS
// ═══════════════════════════════════════════════════
case 'meetings':
    switch (true) {

        // Listar reuniones
        case $method === 'GET' && $id === null:
            $sessionId = query_param('sessionId');
            if (!$sessionId) error_response('sessionId requerido', 400);

            $meetings = Database::fetchAll(
                "SELECT m.*, u.full_name as caller_name,
                        (SELECT COUNT(*) FROM meeting_participants mp WHERE mp.meeting_id = m.id) as participant_count,
                        (SELECT COUNT(*) FROM meeting_incidents mi WHERE mi.meeting_id = m.id) as incident_count
                 FROM clinical_meetings m
                 LEFT JOIN users u ON m.called_by = u.id
                 WHERE m.session_id = :sid
                 ORDER BY m.created_at DESC",
                [':sid' => $sessionId]
            );
            json_response(['meetings' => $meetings]);
            break;

        // Convocar reunión
        case $method === 'POST' && $id === null:
            $body = get_json_body();
            $errors = validate_required($body, ['sessionId', 'title']);
            validate_or_fail($errors);

            $meetingId = Database::uuid();
            Database::execute(
                "INSERT INTO clinical_meetings (id, session_id, called_by, title, agenda_text, scheduled_at)
                 VALUES (:id, :sid, :uid, :title, :agenda, :sched)",
                [
                    ':id' => $meetingId,
                    ':sid' => $body['sessionId'],
                    ':uid' => $auth['sub'],
                    ':title' => $body['title'],
                    ':agenda' => $body['agendaText'] ?? null,
                    ':sched' => $body['scheduledAt'] ?? date('c'),
                ]
            );

            // Agregar participantes (todos los del grupo de la sesión)
            $session = Database::fetchOne('SELECT group_id FROM practice_sessions WHERE id = :sid', [':sid' => $body['sessionId']]);
            if ($session && $session['group_id']) {
                $members = Database::fetchAll(
                    "SELECT user_id FROM group_members WHERE group_id = :gid",
                    [':gid' => $session['group_id']]
                );
                foreach ($members as $m) {
                    Database::execute(
                        "INSERT OR IGNORE INTO meeting_participants (meeting_id, user_id) VALUES (:mid, :uid)",
                        [':mid' => $meetingId, ':uid' => $m['user_id']]
                    );
                }
            }

            // Vincular incidentes pendientes
            $incidentIds = $body['incidentIds'] ?? [];
            foreach ($incidentIds as $incId) {
                Database::execute(
                    "INSERT OR IGNORE INTO meeting_incidents (meeting_id, incident_id) VALUES (:mid, :iid)",
                    [':mid' => $meetingId, ':iid' => $incId]
                );
            }

            // Enviar notificación por chat
            Database::execute(
                "INSERT INTO chat_messages (id, sender_id, group_id, session_id, message, message_type)
                 VALUES (:id, :uid, :gid, :sid, :msg, 'meeting_call')",
                [
                    ':id' => Database::uuid(),
                    ':uid' => $auth['sub'],
                    ':gid' => $session['group_id'] ?? null,
                    ':sid' => $body['sessionId'],
                    ':msg' => '📋 Reunión clínica convocada: ' . $body['title'],
                ]
            );

            created_response(['meeting' => Database::fetchOne('SELECT * FROM clinical_meetings WHERE id = :id', [':id' => $meetingId])]);
            break;

        // Iniciar reunión
        case $method === 'POST' && $id !== null && $action === 'start':
            Database::execute(
                "UPDATE clinical_meetings SET status = 'in_progress', started_at = datetime('now') WHERE id = :id",
                [':id' => $id]
            );
            json_response(['message' => 'Reunión iniciada']);
            break;

        // Finalizar reunión
        case $method === 'POST' && $id !== null && $action === 'end':
            $body = get_json_body();
            Database::execute(
                "UPDATE clinical_meetings SET status = 'completed', ended_at = datetime('now'),
                 minutes_text = :minutes, decisions_text = :decisions WHERE id = :id",
                [
                    ':id' => $id,
                    ':minutes' => $body['minutesText'] ?? $body['minutes'] ?? null,
                    ':decisions' => $body['decisionsText'] ?? $body['decisions'] ?? null,
                ]
            );
            json_response(['message' => 'Reunión finalizada']);
            break;

        // Actualizar acta
        case $method === 'PUT' && $id !== null:
            $body = get_json_body();
            $fields = [];
            $params = [':id' => $id];

            if (isset($body['minutesText'])) { $fields[] = 'minutes_text = :min'; $params[':min'] = $body['minutesText']; }
            if (isset($body['decisionsText'])) { $fields[] = 'decisions_text = :dec'; $params[':dec'] = $body['decisionsText']; }
            if (isset($body['agendaText'])) { $fields[] = 'agenda_text = :ag'; $params[':ag'] = $body['agendaText']; }

            if (!empty($fields)) {
                Database::execute("UPDATE clinical_meetings SET " . implode(', ', $fields) . " WHERE id = :id", $params);
            }
            json_response(['meeting' => Database::fetchOne('SELECT * FROM clinical_meetings WHERE id = :id', [':id' => $id])]);
            break;

        default:
            error_response("Ruta no encontrada: center/meetings", 404);
    }
    break;

// ═══════════════════════════════════════════════════
// CHAT DEL CENTRO
// ═══════════════════════════════════════════════════
case 'chat':
    switch (true) {

        // Obtener mensajes
        case $method === 'GET':
            $sessionId = query_param('sessionId');
            if (!$sessionId) error_response('sessionId requerido', 400);

            $since = query_param('since', '1970-01-01');

            $messages = Database::fetchAll(
                "SELECT cm.*, u.username as sender_username, u.full_name as sender_name
                 FROM chat_messages cm
                 JOIN users u ON cm.sender_id = u.id
                 WHERE cm.session_id = :sid AND cm.created_at > :since
                 AND (cm.recipient_id IS NULL OR cm.recipient_id = :uid OR cm.sender_id = :uid2)
                 ORDER BY cm.created_at",
                [':sid' => $sessionId, ':since' => $since, ':uid' => $auth['sub'], ':uid2' => $auth['sub']]
            );

            // Marcar como leídos
            Database::execute(
                "UPDATE chat_messages SET is_read = 1 WHERE session_id = :sid AND recipient_id = :uid AND is_read = 0",
                [':sid' => $sessionId, ':uid' => $auth['sub']]
            );

            json_response(['messages' => $messages]);
            break;

        // Enviar mensaje
        case $method === 'POST':
            $body = get_json_body();
            $errors = validate_required($body, ['sessionId', 'message']);
            validate_or_fail($errors);

            // Validar permisos de chat
            if ($auth['role'] === 'estudiante') {
                // Estudiantes solo pueden enviar a su grupo de box
                if (!empty($body['recipientId'])) {
                    // Verificar que el destinatario está en el mismo grupo de box
                    $sameBox = Database::fetchOne(
                        "SELECT 1 FROM boxes b1 JOIN boxes b2 ON b1.session_id = b2.session_id
                         WHERE b1.student_id = :uid AND b2.student_id = :rid AND b1.session_id = :sid",
                        [':uid' => $auth['sub'], ':rid' => $body['recipientId'], ':sid' => $body['sessionId']]
                    );
                    // Permitir si es del mismo grupo de sesión o es docente/instructor
                    $isStaff = Database::fetchOne(
                        "SELECT 1 FROM users WHERE id = :rid AND role IN ('admin','docente','instructor')",
                        [':rid' => $body['recipientId']]
                    );
                    if (!$sameBox && !$isStaff) {
                        error_response('Solo puedes escribir a miembros de tu grupo o al docente', 403);
                    }
                }
            }

            $msgId = Database::uuid();
            Database::execute(
                "INSERT INTO chat_messages (id, sender_id, recipient_id, group_id, session_id, message, message_type)
                 VALUES (:id, :uid, :rid, :gid, :sid, :msg, :type)",
                [
                    ':id' => $msgId,
                    ':uid' => $auth['sub'],
                    ':rid' => $body['recipientId'] ?? null,
                    ':gid' => $body['groupId'] ?? null,
                    ':sid' => $body['sessionId'],
                    ':msg' => $body['message'],
                    ':type' => $body['messageType'] ?? 'text',
                ]
            );

            json_response(['message' => Database::fetchOne('SELECT * FROM chat_messages WHERE id = :id', [':id' => $msgId])]);
            break;

        default:
            error_response("Ruta no encontrada: center/chat", 404);
    }
    break;

default:
    error_response("Sección no encontrada: center/$section", 404);
}
