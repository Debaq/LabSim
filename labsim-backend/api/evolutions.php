<?php
/**
 * LabSim Backend - Evoluciones Clínicas
 *
 * GET    /evolutions?agenda_item_id=X  → Listar evoluciones de una cita
 * POST   /evolutions                    → Crear evolución
 * PUT    /evolutions/:id                → Editar evolución (solo autor)
 * DELETE /evolutions/:id                → Eliminar evolución (solo autor)
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;

switch (true) {

    // ─── LISTAR EVOLUCIONES ──────────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth();

        $agendaItemId = query_param('agenda_item_id');
        if (!$agendaItemId) {
            error_response('Se requiere agenda_item_id', 400);
        }

        $sql = "SELECT e.*, u.username as student_username, u.full_name as student_name
                FROM evolutions e
                LEFT JOIN users u ON e.student_id = u.id
                WHERE e.agenda_item_id = :aid
                ORDER BY e.created_at DESC";

        $rows = Database::fetchAll($sql, [':aid' => $agendaItemId]);
        json_response(['data' => $rows]);
        break;

    // ─── CREAR EVOLUCIÓN ─────────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth();
        $body = get_json_body();

        $errors = validate_required($body, ['agendaItemId']);
        validate_or_fail($errors);

        // Verificar que la cita existe
        $cita = Database::fetchOne('SELECT id FROM agenda_items WHERE id = :id', [':id' => $body['agendaItemId']]);
        if (!$cita) {
            error_response('Cita no encontrada', 404);
        }

        $evoId = Database::uuid();
        Database::execute(
            "INSERT INTO evolutions (id, agenda_item_id, student_id,
                motivo_consulta, anamnesis_proxima, examen_fisico,
                hipotesis_diagnostica, plan_estudio, plan_terapeutico, observaciones)
             VALUES (:id, :aid, :sid, :mc, :ap, :ef, :hd, :pe, :pt, :obs)",
            [
                ':id' => $evoId,
                ':aid' => $body['agendaItemId'],
                ':sid' => $auth['sub'],
                ':mc' => $body['motivoConsulta'] ?? null,
                ':ap' => $body['anamnesisProxima'] ?? null,
                ':ef' => $body['examenFisico'] ?? null,
                ':hd' => $body['hipotesisDiagnostica'] ?? null,
                ':pe' => $body['planEstudio'] ?? null,
                ':pt' => $body['planTerapeutico'] ?? null,
                ':obs' => $body['observaciones'] ?? null,
            ]
        );

        $evo = Database::fetchOne('SELECT * FROM evolutions WHERE id = :id', [':id' => $evoId]);
        created_response(['evolution' => $evo]);
        break;

    // ─── EDITAR EVOLUCIÓN ────────────────────────────
    case $method === 'PUT' && $id !== null:
        $auth = require_auth();
        $body = get_json_body();

        $evo = Database::fetchOne('SELECT id, student_id FROM evolutions WHERE id = :id', [':id' => $id]);
        if (!$evo) {
            error_response('Evolución no encontrada', 404);
        }

        if ($auth['role'] !== 'admin' && $auth['sub'] !== $evo['student_id']) {
            error_response('Solo el autor o un admin puede editar esta evolución', 403);
        }

        $fields = [];
        $params = [':id' => $id];

        $editableFields = [
            'motivoConsulta' => 'motivo_consulta',
            'anamnesisProxima' => 'anamnesis_proxima',
            'examenFisico' => 'examen_fisico',
            'hipotesisDiagnostica' => 'hipotesis_diagnostica',
            'planEstudio' => 'plan_estudio',
            'planTerapeutico' => 'plan_terapeutico',
            'observaciones' => 'observaciones',
        ];

        foreach ($editableFields as $jsonKey => $dbCol) {
            if (isset($body[$jsonKey])) {
                $fields[] = "$dbCol = :$dbCol";
                $params[":$dbCol"] = $body[$jsonKey];
            }
        }

        if (empty($fields)) {
            error_response('No hay campos para actualizar', 400);
        }

        $fields[] = "updated_at = datetime('now')";
        Database::execute("UPDATE evolutions SET " . implode(', ', $fields) . " WHERE id = :id", $params);

        $updated = Database::fetchOne('SELECT * FROM evolutions WHERE id = :id', [':id' => $id]);
        json_response(['evolution' => $updated]);
        break;

    // ─── ELIMINAR EVOLUCIÓN ──────────────────────────
    case $method === 'DELETE' && $id !== null:
        $auth = require_auth();

        $evo = Database::fetchOne('SELECT id, student_id FROM evolutions WHERE id = :id', [':id' => $id]);
        if (!$evo) {
            error_response('Evolución no encontrada', 404);
        }

        if ($auth['role'] !== 'admin' && $auth['sub'] !== $evo['student_id']) {
            error_response('Solo el autor o un admin puede eliminar esta evolución', 403);
        }

        Database::execute('DELETE FROM evolutions WHERE id = :id', [':id' => $id]);
        json_response(['message' => 'Evolución eliminada']);
        break;

    default:
        error_response("Ruta no encontrada: evolutions/$id", 404);
}
