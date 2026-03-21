<?php
/**
 * LabSim Backend - Assets y Releases
 *
 * GET    /assets                → Lista assets
 * POST   /assets                → Subir asset (admin/docente)
 * GET    /assets/:id/download   → Descargar asset
 * DELETE /assets/:id            → Eliminar asset
 * GET    /releases/latest       → Última versión
 * POST   /releases              → Crear release (admin)
 */

require_once __DIR__ . '/../core/auth_middleware.php';
require_once __DIR__ . '/../core/upload.php';

$id = $routeSegments[0] ?? null;
$action = $routeSegments[1] ?? null;

// Detectar si es /releases o /assets por el resource del router
$isRelease = ($resource === 'releases');

if ($isRelease) {
    switch (true) {

        // ─── LATEST RELEASE ─────────────────────────
        case $method === 'GET' && $id === 'latest':
            $release = Database::fetchOne(
                "SELECT * FROM app_releases WHERE is_latest = 1 ORDER BY published_at DESC LIMIT 1"
            );
            if (!$release) {
                $release = Database::fetchOne("SELECT * FROM app_releases ORDER BY published_at DESC LIMIT 1");
            }
            if (!$release) error_response('No hay releases disponibles', 404);

            json_response(['release' => $release]);
            break;

        // ─── LISTAR RELEASES ────────────────────────
        case $method === 'GET' && $id === null:
            $auth = require_auth('admin');
            $releases = Database::fetchAll("SELECT * FROM app_releases ORDER BY published_at DESC");
            json_response(['releases' => $releases]);
            break;

        // ─── CREAR RELEASE ──────────────────────────
        case $method === 'POST' && $id === null:
            $auth = require_auth('admin');

            $version = $_POST['version'] ?? null;
            if (!$version) error_response('version requerida', 400);

            $existing = Database::fetchOne('SELECT id FROM app_releases WHERE version = :v', [':v' => $version]);
            if ($existing) error_response('Ya existe una release con esta versión', 409);

            $releaseId = Database::uuid();
            $urls = [];

            // Subir binarios si vienen
            foreach (['linux', 'windows', 'macos'] as $platform) {
                $field = "file_$platform";
                if (isset($_FILES[$field]) && $_FILES[$field]['error'] === UPLOAD_ERR_OK) {
                    $upload = handle_upload($field, 'releases', ALLOWED_RELEASE_TYPES);
                    $urls[$platform] = $upload['path'];
                }
            }

            // Marcar esta como latest y quitar de las demás
            Database::execute("UPDATE app_releases SET is_latest = 0");

            Database::execute(
                "INSERT INTO app_releases (id, version, release_notes, download_url_linux, download_url_windows,
                    download_url_macos, checksum_sha256, is_latest, is_mandatory)
                 VALUES (:id, :ver, :notes, :linux, :win, :mac, :hash, 1, :mandatory)",
                [
                    ':id' => $releaseId,
                    ':ver' => $version,
                    ':notes' => $_POST['releaseNotes'] ?? $_POST['release_notes'] ?? null,
                    ':linux' => $urls['linux'] ?? $_POST['downloadUrlLinux'] ?? null,
                    ':win' => $urls['windows'] ?? $_POST['downloadUrlWindows'] ?? null,
                    ':mac' => $urls['macos'] ?? $_POST['downloadUrlMacos'] ?? null,
                    ':hash' => $_POST['checksumSha256'] ?? $_POST['checksum_sha256'] ?? null,
                    ':mandatory' => (int)($_POST['isMandatory'] ?? $_POST['is_mandatory'] ?? 0),
                ]
            );

            created_response(['release' => Database::fetchOne('SELECT * FROM app_releases WHERE id = :id', [':id' => $releaseId])]);
            break;

        default:
            error_response("Ruta no encontrada: releases/" . implode('/', $routeSegments), 404);
    }
} else {
    switch (true) {

        // ─── LISTAR ASSETS ──────────────────────────
        case $method === 'GET' && $id === null:
            $auth = require_auth();

            $where = ['1=1'];
            $params = [];

            $category = query_param('category');
            if ($category) {
                $where[] = 'category = :cat';
                $params[':cat'] = $category;
            }

            $sql = "SELECT a.*, u.username as uploader_username
                    FROM assets a
                    LEFT JOIN users u ON a.uploaded_by = u.id
                    WHERE " . implode(' AND ', $where) . "
                    ORDER BY a.created_at DESC";

            $page = query_int('page', 1);
            $limit = query_int('limit', DEFAULT_PAGE_SIZE);
            json_response(Database::paginate($sql, $params, $page, $limit));
            break;

        // ─── SUBIR ASSET ────────────────────────────
        case $method === 'POST' && $id === null:
            $auth = require_auth(['admin', 'docente']);

            $upload = handle_upload('file', 'assets', ALLOWED_ASSET_TYPES);

            $assetId = Database::uuid();
            Database::execute(
                "INSERT INTO assets (id, name, category, file_path, file_size, mime_type, uploaded_by)
                 VALUES (:id, :name, :cat, :path, :size, :mime, :uid)",
                [
                    ':id' => $assetId,
                    ':name' => $_POST['name'] ?? $upload['original_name'],
                    ':cat' => $_POST['category'] ?? null,
                    ':path' => $upload['path'],
                    ':size' => $upload['size'],
                    ':mime' => $upload['mime'],
                    ':uid' => $auth['sub'],
                ]
            );

            created_response(['asset' => Database::fetchOne('SELECT * FROM assets WHERE id = :id', [':id' => $assetId])]);
            break;

        // ─── DESCARGAR ASSET ────────────────────────
        case $method === 'GET' && $id !== null && $action === 'download':
            $auth = require_auth();

            $asset = Database::fetchOne('SELECT file_path, name FROM assets WHERE id = :id', [':id' => $id]);
            if (!$asset) error_response('Asset no encontrado', 404);

            send_file_download($asset['file_path'], $asset['name']);
            break;

        // ─── ELIMINAR ASSET ────────────────────────
        case $method === 'DELETE' && $id !== null:
            $auth = require_auth('admin');

            $asset = Database::fetchOne('SELECT id, file_path FROM assets WHERE id = :id', [':id' => $id]);
            if (!$asset) error_response('Asset no encontrado', 404);

            delete_upload($asset['file_path']);
            Database::execute('DELETE FROM assets WHERE id = :id', [':id' => $id]);

            json_response(['message' => 'Asset eliminado']);
            break;

        default:
            error_response("Ruta no encontrada: assets/" . implode('/', $routeSegments), 404);
    }
}
