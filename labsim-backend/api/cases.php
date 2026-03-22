<?php
/**
 * LabSim Backend - CRUD Casos Clínicos
 *
 * GET    /cases              → Lista casos
 * GET    /cases/:id          → Detalle caso
 * POST   /cases              → Crear caso (admin/docente/instructor)
 * PUT    /cases/:id          → Actualizar caso
 * DELETE /cases/:id          → Eliminar caso
 * PUT    /cases/:id/publish  → Publicar/despublicar caso
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/validators.php';

$id = $routeSegments[0] ?? null;
$action = $routeSegments[1] ?? null;

switch (true) {

    // ─── LISTAR CASOS ───────────────────────────────
    case $method === 'GET' && $id === null:
        $auth = require_auth();

        $where = ['1=1'];
        $params = [];

        // Estudiantes solo ven casos publicados
        if ($auth['role'] === 'estudiante') {
            $where[] = 'c.is_published = 1';
        }

        // Filtro de archivados (por defecto ocultar)
        $archived = query_param('archived');
        if ($archived === '1') {
            $where[] = 'c.is_archived = 1';
        } elseif ($archived !== 'all') {
            $where[] = '(c.is_archived = 0 OR c.is_archived IS NULL)';
        }

        $author = query_param('author');
        if ($author) {
            $where[] = 'c.author_id = :author';
            $params[':author'] = $author;
        }

        $published = query_param('published');
        if ($published !== null) {
            $where[] = 'c.is_published = :pub';
            $params[':pub'] = (int)$published;
        }

        $tags = query_param('tags');
        if ($tags) {
            // Buscar en tags (comma-separated)
            foreach (explode(',', $tags) as $i => $tag) {
                $tag = trim($tag);
                if ($tag) {
                    $where[] = "c.tags LIKE :tag$i";
                    $params[":tag$i"] = "%$tag%";
                }
            }
        }

        $difficulty = query_param('difficulty');
        if ($difficulty) {
            $where[] = 'c.difficulty = :diff';
            $params[':diff'] = $difficulty;
        }

        $search = query_param('search');
        if ($search) {
            $where[] = "(c.title LIKE :search OR c.description LIKE :search)";
            $params[':search'] = "%$search%";
        }

        $sql = "SELECT c.id, c.title, c.description, c.author_id, c.tags, c.difficulty,
                       c.is_published, c.is_archived, c.schema_version, c.created_at, c.updated_at,
                       u.username as author_username, u.full_name as author_name
                FROM cases c
                LEFT JOIN users u ON c.author_id = u.id
                WHERE " . implode(' AND ', $where) . "
                ORDER BY c.updated_at DESC";

        $page = query_int('page', 1);
        $limit = query_int('limit', DEFAULT_PAGE_SIZE);

        $result = Database::paginate($sql, $params, $page, $limit);
        json_response($result);
        break;

    // ─── DETALLE CASO ───────────────────────────────
    case $method === 'GET' && $id !== null && $action === null:
        $auth = require_auth();

        $caso = Database::fetchOne(
            "SELECT c.*, u.username as author_username, u.full_name as author_name
             FROM cases c
             LEFT JOIN users u ON c.author_id = u.id
             WHERE c.id = :id",
            [':id' => $id]
        );

        if (!$caso) {
            error_response('Caso no encontrado', 404);
        }

        // Estudiantes solo ven publicados
        if ($auth['role'] === 'estudiante' && !$caso['is_published']) {
            error_response('Caso no encontrado', 404);
        }

        // Decodificar profile_json
        $caso['profile'] = json_decode($caso['profile_json'], true);
        unset($caso['profile_json']);

        json_response(['case' => $caso]);
        break;

    // ─── CREAR CASO ─────────────────────────────────
    case $method === 'POST' && $id === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $body = get_json_body();

        $errors = validate_required($body, ['title']);
        $errors[] = validate_enum($body['difficulty'] ?? 'medium', ['easy', 'medium', 'hard'], 'difficulty');
        validate_or_fail($errors);

        $caseId = Database::uuid();
        $profileJson = json_encode($body['profile'] ?? $body['profileJson'] ?? new stdClass(), JSON_UNESCAPED_UNICODE);

        Database::execute(
            "INSERT INTO cases (id, title, description, author_id, profile_json, schema_version, tags, difficulty, is_published)
             VALUES (:id, :title, :desc, :author, :profile, :schema, :tags, :diff, :pub)",
            [
                ':id' => $caseId,
                ':title' => $body['title'],
                ':desc' => $body['description'] ?? null,
                ':author' => $auth['sub'],
                ':profile' => $profileJson,
                ':schema' => $body['schemaVersion'] ?? $body['schema_version'] ?? 1,
                ':tags' => $body['tags'] ?? '',
                ':diff' => $body['difficulty'] ?? 'medium',
                ':pub' => 0,
            ]
        );

        $caso = Database::fetchOne('SELECT * FROM cases WHERE id = :id', [':id' => $caseId]);
        $caso['profile'] = json_decode($caso['profile_json'], true);
        unset($caso['profile_json']);

        created_response(['case' => $caso]);
        break;

    // ─── ACTUALIZAR CASO ────────────────────────────
    case $method === 'PUT' && $id !== null && $action === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $body = get_json_body();

        $caso = Database::fetchOne('SELECT id, author_id FROM cases WHERE id = :id', [':id' => $id]);
        if (!$caso) {
            error_response('Caso no encontrado', 404);
        }

        // Solo el autor o admin puede editar
        if ($auth['role'] !== 'admin' && $auth['sub'] !== $caso['author_id']) {
            error_response('Solo el autor o un admin puede editar este caso', 403);
        }

        $fields = [];
        $params = [':id' => $id];

        if (isset($body['title'])) {
            $fields[] = 'title = :title';
            $params[':title'] = $body['title'];
        }
        if (isset($body['description'])) {
            $fields[] = 'description = :desc';
            $params[':desc'] = $body['description'];
        }
        if (isset($body['profile']) || isset($body['profileJson'])) {
            $profile = $body['profile'] ?? $body['profileJson'];
            $fields[] = 'profile_json = :profile';
            $params[':profile'] = json_encode($profile, JSON_UNESCAPED_UNICODE);
        }
        if (isset($body['tags'])) {
            $fields[] = 'tags = :tags';
            $params[':tags'] = $body['tags'];
        }
        if (isset($body['difficulty'])) {
            $err = validate_enum($body['difficulty'], ['easy', 'medium', 'hard'], 'difficulty');
            if ($err) error_response($err, 422);
            $fields[] = 'difficulty = :diff';
            $params[':diff'] = $body['difficulty'];
        }
        if (isset($body['schemaVersion']) || isset($body['schema_version'])) {
            $fields[] = 'schema_version = :schema';
            $params[':schema'] = $body['schemaVersion'] ?? $body['schema_version'];
        }

        if (empty($fields)) {
            error_response('No hay campos para actualizar', 400);
        }

        $fields[] = "updated_at = datetime('now')";
        Database::execute("UPDATE cases SET " . implode(', ', $fields) . " WHERE id = :id", $params);

        $updated = Database::fetchOne('SELECT * FROM cases WHERE id = :id', [':id' => $id]);
        $updated['profile'] = json_decode($updated['profile_json'], true);
        unset($updated['profile_json']);

        json_response(['case' => $updated]);
        break;

    // ─── PUBLICAR/DESPUBLICAR ───────────────────────
    case $method === 'PUT' && $id !== null && $action === 'publish':
        $auth = require_auth(['admin', 'docente']);

        $caso = Database::fetchOne('SELECT id, is_published FROM cases WHERE id = :id', [':id' => $id]);
        if (!$caso) {
            error_response('Caso no encontrado', 404);
        }

        $newState = $caso['is_published'] ? 0 : 1;
        Database::execute(
            "UPDATE cases SET is_published = :pub, updated_at = datetime('now') WHERE id = :id",
            [':id' => $id, ':pub' => $newState]
        );

        json_response([
            'message' => $newState ? 'Caso publicado' : 'Caso despublicado',
            'is_published' => $newState,
        ]);
        break;

    // ─── ELIMINAR CASO ──────────────────────────────
    case $method === 'DELETE' && $id !== null && $action === null:
        $auth = require_auth(['admin', 'docente']);

        $caso = Database::fetchOne('SELECT id, author_id FROM cases WHERE id = :id', [':id' => $id]);
        if (!$caso) {
            error_response('Caso no encontrado', 404);
        }

        if ($auth['role'] !== 'admin' && $auth['sub'] !== $caso['author_id']) {
            error_response('Solo el autor o un admin puede eliminar este caso', 403);
        }

        // Verificar que no esté en uso en sesiones activas
        $inUse = Database::fetchOne(
            "SELECT COUNT(*) as count FROM practice_session_cases psc
             JOIN practice_sessions ps ON psc.session_id = ps.id
             WHERE psc.case_id = :cid AND ps.status IN ('approved','active')",
            [':cid' => $id]
        );

        if (($inUse['count'] ?? 0) > 0) {
            error_response('No se puede eliminar: el caso está asignado a sesiones activas', 409);
        }

        Database::execute('DELETE FROM cases WHERE id = :id', [':id' => $id]);

        json_response(['message' => 'Caso eliminado']);
        break;

    // ─── ARCHIVAR/DESARCHIVAR ─────────────────────────
    case $method === 'PUT' && $id !== null && $action === 'archive':
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $caso = Database::fetchOne('SELECT id, is_archived FROM cases WHERE id = :id', [':id' => $id]);
        if (!$caso) {
            error_response('Caso no encontrado', 404);
        }

        $newState = ($caso['is_archived'] ?? 0) ? 0 : 1;
        Database::execute(
            "UPDATE cases SET is_archived = :arch, updated_at = datetime('now') WHERE id = :id",
            [':id' => $id, ':arch' => $newState]
        );

        json_response([
            'message' => $newState ? 'Caso archivado' : 'Caso desarchivado',
            'is_archived' => $newState,
        ]);
        break;

    default:
        error_response("Ruta no encontrada: cases/$id" . ($action ? "/$action" : ''), 404);
}
