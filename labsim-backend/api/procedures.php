<?php
/**
 * LabSim Backend - Cartera de Procedimientos
 *
 * GET    /procedures           → Lista procedimientos activos
 * GET    /procedures/:id       → Detalle procedimiento
 * POST   /procedures           → Crear procedimiento (admin)
 * PUT    /procedures/:id       → Actualizar procedimiento (admin)
 * DELETE /procedures/:id       → Desactivar procedimiento (admin)
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;

switch (true) {

    // ─── LISTAR PROCEDIMIENTOS ──────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth();

        $where = ['is_active = 1'];
        $params = [];

        $category = query_param('category');
        if ($category) {
            $where[] = 'category = :cat';
            $params[':cat'] = $category;
        }

        $search = query_param('search');
        if ($search) {
            $where[] = "(name LIKE :s OR code LIKE :s OR description LIKE :s)";
            $params[':s'] = "%$search%";
        }

        $procedures = Database::fetchAll(
            "SELECT * FROM procedures WHERE " . implode(' AND ', $where) . " ORDER BY category, name",
            $params
        );

        json_response(['procedures' => $procedures]);
        break;

    // ─── DETALLE ────────────────────────────────────
    case $method === 'GET' && $id !== null:
        $auth = require_auth();

        $proc = Database::fetchOne('SELECT * FROM procedures WHERE id = :id', [':id' => $id]);
        if (!$proc) error_response('Procedimiento no encontrado', 404);

        json_response(['procedure' => $proc]);
        break;

    // ─── CREAR ──────────────────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth('admin');
        $body = get_json_body();

        $errors = validate_required($body, ['name', 'category', 'defaultDurationMinutes']);
        $errors[] = validate_enum(
            $body['category'] ?? null,
            ['audiologia', 'oftalmologia', 'vestibular', 'electrodiagnostico', 'otro'],
            'category'
        );
        validate_or_fail($errors);

        $procId = Database::uuid();
        Database::execute(
            "INSERT INTO procedures (id, name, code, category, default_duration_minutes, description, requires_equipment)
             VALUES (:id, :name, :code, :cat, :dur, :desc, :equip)",
            [
                ':id' => $procId,
                ':name' => $body['name'],
                ':code' => $body['code'] ?? null,
                ':cat' => $body['category'],
                ':dur' => $body['defaultDurationMinutes'] ?? $body['default_duration_minutes'] ?? 30,
                ':desc' => $body['description'] ?? null,
                ':equip' => $body['requiresEquipment'] ?? $body['requires_equipment'] ?? null,
            ]
        );

        created_response(['procedure' => Database::fetchOne('SELECT * FROM procedures WHERE id = :id', [':id' => $procId])]);
        break;

    // ─── ACTUALIZAR ─────────────────────────────────
    case $method === 'PUT' && $id !== null:
        $auth = require_auth('admin');

        $proc = Database::fetchOne('SELECT id FROM procedures WHERE id = :id', [':id' => $id]);
        if (!$proc) error_response('Procedimiento no encontrado', 404);

        $body = get_json_body();
        $fields = [];
        $params = [':id' => $id];

        $mapping = [
            'name' => 'name', 'code' => 'code', 'category' => 'category',
            'description' => 'description',
            'defaultDurationMinutes' => 'default_duration_minutes',
            'default_duration_minutes' => 'default_duration_minutes',
            'requiresEquipment' => 'requires_equipment',
            'requires_equipment' => 'requires_equipment',
        ];

        foreach ($body as $key => $value) {
            if (isset($mapping[$key])) {
                $dbKey = $mapping[$key];
                $fields[] = "$dbKey = :$dbKey";
                $params[":$dbKey"] = $value;
            }
        }

        if (empty($fields)) error_response('No hay campos para actualizar', 400);

        Database::execute("UPDATE procedures SET " . implode(', ', $fields) . " WHERE id = :id", $params);
        json_response(['procedure' => Database::fetchOne('SELECT * FROM procedures WHERE id = :id', [':id' => $id])]);
        break;

    // ─── DESACTIVAR ─────────────────────────────────
    case $method === 'DELETE' && $id !== null:
        $auth = require_auth('admin');

        $proc = Database::fetchOne('SELECT id FROM procedures WHERE id = :id', [':id' => $id]);
        if (!$proc) error_response('Procedimiento no encontrado', 404);

        Database::execute("UPDATE procedures SET is_active = 0 WHERE id = :id", [':id' => $id]);
        json_response(['message' => 'Procedimiento desactivado']);
        break;

    default:
        error_response("Ruta no encontrada: procedures/" . implode('/', $routeSegments), 404);
}
