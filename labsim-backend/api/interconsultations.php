<?php
/**
 * LabSim Backend - Interconsultas
 *
 * GET    /interconsultations?agenda_item_id=X  → Listar interconsultas
 * POST   /interconsultations                    → Crear interconsulta
 * PUT    /interconsultations/:id                → Responder/actualizar
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;

switch (true) {

    // ─── LISTAR INTERCONSULTAS ───────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth();

        $agendaItemId = query_param('agenda_item_id');
        if (!$agendaItemId) {
            error_response('Se requiere agenda_item_id', 400);
        }

        $sql = "SELECT ic.*,
                       req.username as requester_username, req.full_name as requester_name,
                       resp.username as responder_username, resp.full_name as responder_name
                FROM interconsultations ic
                LEFT JOIN users req ON ic.requester_id = req.id
                LEFT JOIN users resp ON ic.responder_id = resp.id
                WHERE ic.agenda_item_id = :aid
                ORDER BY ic.created_at DESC";

        $rows = Database::fetchAll($sql, [':aid' => $agendaItemId]);
        json_response(['data' => $rows]);
        break;

    // ─── CREAR INTERCONSULTA ─────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth();
        $body = get_json_body();

        $errors = validate_required($body, ['agendaItemId', 'targetSpecialty', 'reason']);
        validate_or_fail($errors);

        // Verificar que la cita existe
        $cita = Database::fetchOne('SELECT id FROM agenda_items WHERE id = :id', [':id' => $body['agendaItemId']]);
        if (!$cita) {
            error_response('Cita no encontrada', 404);
        }

        $icId = Database::uuid();
        Database::execute(
            "INSERT INTO interconsultations (id, agenda_item_id, requester_id, target_specialty, reason, priority)
             VALUES (:id, :aid, :rid, :spec, :reason, :prio)",
            [
                ':id' => $icId,
                ':aid' => $body['agendaItemId'],
                ':rid' => $auth['sub'],
                ':spec' => $body['targetSpecialty'],
                ':reason' => $body['reason'],
                ':prio' => $body['priority'] ?? 'normal',
            ]
        );

        $ic = Database::fetchOne('SELECT * FROM interconsultations WHERE id = :id', [':id' => $icId]);
        created_response(['interconsultation' => $ic]);
        break;

    // ─── RESPONDER/ACTUALIZAR INTERCONSULTA ──────────
    case $method === 'PUT' && $id !== null:
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $body = get_json_body();

        $ic = Database::fetchOne('SELECT id FROM interconsultations WHERE id = :id', [':id' => $id]);
        if (!$ic) {
            error_response('Interconsulta no encontrada', 404);
        }

        $fields = [];
        $params = [':id' => $id];

        if (isset($body['responseText'])) {
            $fields[] = 'response_text = :resp';
            $params[':resp'] = $body['responseText'];
            $fields[] = 'responder_id = :responder';
            $params[':responder'] = $auth['sub'];
            $fields[] = "responded_at = datetime('now')";
        }
        if (isset($body['status'])) {
            $fields[] = 'status = :status';
            $params[':status'] = $body['status'];
        }

        if (empty($fields)) {
            error_response('No hay campos para actualizar', 400);
        }

        Database::execute("UPDATE interconsultations SET " . implode(', ', $fields) . " WHERE id = :id", $params);

        $updated = Database::fetchOne(
            "SELECT ic.*, req.full_name as requester_name, resp.full_name as responder_name
             FROM interconsultations ic
             LEFT JOIN users req ON ic.requester_id = req.id
             LEFT JOIN users resp ON ic.responder_id = resp.id
             WHERE ic.id = :id",
            [':id' => $id]
        );
        json_response(['interconsultation' => $updated]);
        break;

    default:
        error_response("Ruta no encontrada: interconsultations/$id", 404);
}
