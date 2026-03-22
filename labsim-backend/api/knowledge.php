<?php
/**
 * LabSim Backend - Base de Conocimiento
 *
 * Artículos de ayuda organizados por categoría, editables por docentes.
 *
 * GET    /knowledge                → Listar artículos (opcionalmente por categoría)
 * GET    /knowledge/categories     → Listar categorías
 * GET    /knowledge/:id            → Detalle de un artículo
 * POST   /knowledge                → Crear artículo (docente/admin)
 * PUT    /knowledge/:id            → Actualizar artículo (docente/admin)
 * DELETE /knowledge/:id            → Eliminar artículo (docente/admin)
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;

switch (true) {

    // ─── LISTAR CATEGORÍAS ─────────────────────────────
    case $method === 'GET' && $id === 'categories':
        $auth = require_auth();

        $categories = Database::fetchAll(
            "SELECT * FROM kb_categories WHERE is_active = 1 ORDER BY sort_order, label"
        );
        json_response(['categories' => $categories]);
        break;

    // ─── LISTAR ARTÍCULOS ──────────────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth();

        // Verificar si hay cambios desde la última sincronización
        $since = query_param('since');
        if ($since) {
            $lastChange = Database::fetchOne(
                "SELECT MAX(updated_at) as last FROM kb_articles WHERE is_active = 1"
            );
            $serverLast = $lastChange['last'] ?? null;

            // Si no hay cambios después de 'since', responder sin datos
            if ($serverLast && $serverLast <= $since) {
                json_response(['changed' => false, 'lastModified' => $serverLast]);
                break;
            }
        }

        $categoryId = query_param('category');

        if ($categoryId) {
            $articles = Database::fetchAll(
                "SELECT a.*, c.label as category_label, c.icon as category_icon,
                        u.full_name as author_name
                 FROM kb_articles a
                 JOIN kb_categories c ON a.category_id = c.id
                 LEFT JOIN users u ON a.author_id = u.id
                 WHERE a.category_id = :cat AND a.is_active = 1
                 ORDER BY a.sort_order, a.title",
                [':cat' => $categoryId]
            );
        } else {
            $articles = Database::fetchAll(
                "SELECT a.*, c.label as category_label, c.icon as category_icon,
                        u.full_name as author_name
                 FROM kb_articles a
                 JOIN kb_categories c ON a.category_id = c.id
                 LEFT JOIN users u ON a.author_id = u.id
                 WHERE a.is_active = 1
                 ORDER BY c.sort_order, a.sort_order, a.title"
            );
        }

        // Agrupar por categoría para el frontend
        $categories = Database::fetchAll(
            "SELECT * FROM kb_categories WHERE is_active = 1 ORDER BY sort_order, label"
        );

        $grouped = [];
        foreach ($categories as $cat) {
            $cat['articles'] = array_values(array_filter($articles, fn($a) => $a['category_id'] === $cat['id']));
            $grouped[] = $cat;
        }

        // Calcular último cambio
        $lastMod = Database::fetchOne(
            "SELECT MAX(updated_at) as last FROM kb_articles WHERE is_active = 1"
        );

        json_response([
            'changed' => true,
            'lastModified' => $lastMod['last'] ?? null,
            'categories' => $grouped,
        ]);
        break;

    // ─── DETALLE DE ARTÍCULO ───────────────────────────
    case $method === 'GET' && $id !== null:
        $auth = require_auth();

        $article = Database::fetchOne(
            "SELECT a.*, c.label as category_label, u.full_name as author_name
             FROM kb_articles a
             JOIN kb_categories c ON a.category_id = c.id
             LEFT JOIN users u ON a.author_id = u.id
             WHERE a.id = :id",
            [':id' => $id]
        );
        if (!$article) error_response('Artículo no encontrado', 404);

        json_response(['article' => $article]);
        break;

    // ─── CREAR ARTÍCULO ────────────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth(['admin', 'docente']);
        $body = get_json_body();

        $errors = validate_required($body, ['title', 'content', 'categoryId']);
        validate_or_fail($errors);

        // Verificar que la categoría existe
        $cat = Database::fetchOne(
            "SELECT id FROM kb_categories WHERE id = :id AND is_active = 1",
            [':id' => $body['categoryId']]
        );
        if (!$cat) error_response('Categoría no encontrada', 404);

        $articleId = Database::uuid();
        Database::execute(
            "INSERT INTO kb_articles (id, category_id, title, content, author_id)
             VALUES (:id, :cat, :title, :content, :author)",
            [
                ':id' => $articleId,
                ':cat' => $body['categoryId'],
                ':title' => $body['title'],
                ':content' => $body['content'],
                ':author' => $auth['sub'],
            ]
        );

        $article = Database::fetchOne('SELECT * FROM kb_articles WHERE id = :id', [':id' => $articleId]);
        created_response(['article' => $article]);
        break;

    // ─── ACTUALIZAR ARTÍCULO ───────────────────────────
    case $method === 'PUT' && $id !== null:
        $auth = require_auth(['admin', 'docente']);

        $article = Database::fetchOne('SELECT * FROM kb_articles WHERE id = :id', [':id' => $id]);
        if (!$article) error_response('Artículo no encontrado', 404);

        $body = get_json_body();
        $fields = [];
        $params = [':id' => $id];

        if (isset($body['title'])) {
            $fields[] = 'title = :title';
            $params[':title'] = $body['title'];
        }
        if (isset($body['content'])) {
            $fields[] = 'content = :content';
            $params[':content'] = $body['content'];
        }
        if (isset($body['categoryId'])) {
            $fields[] = 'category_id = :cat';
            $params[':cat'] = $body['categoryId'];
        }

        if (empty($fields)) error_response('No hay campos para actualizar', 400);

        $fields[] = "updated_at = datetime('now')";
        Database::execute("UPDATE kb_articles SET " . implode(', ', $fields) . " WHERE id = :id", $params);

        json_response(['article' => Database::fetchOne('SELECT * FROM kb_articles WHERE id = :id', [':id' => $id])]);
        break;

    // ─── ELIMINAR ARTÍCULO ─────────────────────────────
    case $method === 'DELETE' && $id !== null:
        $auth = require_auth(['admin', 'docente']);

        $article = Database::fetchOne('SELECT id FROM kb_articles WHERE id = :id', [':id' => $id]);
        if (!$article) error_response('Artículo no encontrado', 404);

        Database::execute(
            "UPDATE kb_articles SET is_active = 0, updated_at = datetime('now') WHERE id = :id",
            [':id' => $id]
        );
        json_response(['message' => 'Artículo eliminado']);
        break;

    default:
        error_response("Ruta no encontrada: knowledge/" . implode('/', $routeSegments), 404);
}
