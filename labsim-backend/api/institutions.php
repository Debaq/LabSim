<?php
/**
 * LabSim Backend - Instituciones
 *
 * GET    /institutions          → Listar
 * POST   /institutions          → Crear (admin)
 * GET    /institutions/:id      → Detalle
 * PUT    /institutions/:id      → Actualizar (admin)
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;

switch (true) {

    // ─── LISTAR ──────────────────────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth(['admin']);

        $rows = Database::fetchAll(
            "SELECT * FROM institutions WHERE is_active = 1 ORDER BY name"
        );
        json_response(['data' => $rows]);
        break;

    // ─── CREAR ───────────────────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth(['admin']);
        $body = get_json_body();

        $errors = validate_required($body, ['name', 'slug']);
        validate_or_fail($errors);

        // Verificar slug único
        $existing = Database::fetchOne('SELECT id FROM institutions WHERE slug = :s', [':s' => $body['slug']]);
        if ($existing) {
            error_response('Ya existe una institución con ese slug', 409);
        }

        $instId = Database::uuid();
        Database::execute(
            "INSERT INTO institutions (id, name, slug, config_json) VALUES (:id, :name, :slug, :config)",
            [
                ':id' => $instId,
                ':name' => $body['name'],
                ':slug' => $body['slug'],
                ':config' => json_encode($body['config'] ?? new stdClass(), JSON_UNESCAPED_UNICODE),
            ]
        );

        $inst = Database::fetchOne('SELECT * FROM institutions WHERE id = :id', [':id' => $instId]);
        created_response(['institution' => $inst]);
        break;

    // ─── DETALLE ─────────────────────────────────────
    case $method === 'GET' && $id !== null:
        $auth = require_auth();

        $inst = Database::fetchOne('SELECT * FROM institutions WHERE id = :id', [':id' => $id]);
        if (!$inst) error_response('Institución no encontrada', 404);

        json_response(['institution' => $inst]);
        break;

    // ─── ACTUALIZAR ──────────────────────────────────
    case $method === 'PUT' && $id !== null:
        $auth = require_auth(['admin']);
        $body = get_json_body();

        $inst = Database::fetchOne('SELECT id FROM institutions WHERE id = :id', [':id' => $id]);
        if (!$inst) error_response('Institución no encontrada', 404);

        $fields = [];
        $params = [':id' => $id];

        if (isset($body['name'])) {
            $fields[] = 'name = :name';
            $params[':name'] = $body['name'];
        }
        if (isset($body['config'])) {
            $fields[] = 'config_json = :config';
            $params[':config'] = json_encode($body['config'], JSON_UNESCAPED_UNICODE);
        }
        if (isset($body['isActive'])) {
            $fields[] = 'is_active = :active';
            $params[':active'] = (int)$body['isActive'];
        }

        if (empty($fields)) error_response('No hay campos para actualizar', 400);

        Database::execute("UPDATE institutions SET " . implode(', ', $fields) . " WHERE id = :id", $params);

        $updated = Database::fetchOne('SELECT * FROM institutions WHERE id = :id', [':id' => $id]);
        json_response(['institution' => $updated]);
        break;

    default:
        error_response("Ruta no encontrada: institutions/$id", 404);
}
