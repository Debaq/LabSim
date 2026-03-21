<?php
/**
 * LabSim Backend - Helpers para subir archivos
 */

require_once __DIR__ . '/config.php';
require_once __DIR__ . '/db.php';

/**
 * Procesa un archivo subido
 * @param string $fieldName nombre del campo en $_FILES
 * @param string $subdir subdirectorio dentro de uploads/
 * @param array $allowedTypes MIME types permitidos
 * @param int $maxSize tamaño máximo en bytes
 * @return array ['path' => ruta relativa, 'size' => bytes, 'mime' => tipo, 'original_name' => nombre]
 */
function handle_upload(
    string $fieldName,
    string $subdir,
    array $allowedTypes,
    int $maxSize = MAX_UPLOAD_SIZE
): array {
    if (!isset($_FILES[$fieldName]) || $_FILES[$fieldName]['error'] === UPLOAD_ERR_NO_FILE) {
        error_response("No se recibió archivo en '$fieldName'", 400);
    }

    $file = $_FILES[$fieldName];

    if ($file['error'] !== UPLOAD_ERR_OK) {
        $errors = [
            UPLOAD_ERR_INI_SIZE => 'Archivo excede límite del servidor',
            UPLOAD_ERR_FORM_SIZE => 'Archivo excede límite del formulario',
            UPLOAD_ERR_PARTIAL => 'Archivo subido parcialmente',
            UPLOAD_ERR_NO_TMP_DIR => 'Directorio temporal no disponible',
            UPLOAD_ERR_CANT_WRITE => 'Error al escribir archivo',
            UPLOAD_ERR_EXTENSION => 'Extensión bloqueada',
        ];
        error_response($errors[$file['error']] ?? 'Error al subir archivo', 500);
    }

    // Validar tamaño
    if ($file['size'] > $maxSize) {
        error_response('Archivo excede el tamaño máximo (' . round($maxSize / 1024 / 1024) . 'MB)', 413);
    }

    // Validar MIME type
    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $mime = finfo_file($finfo, $file['tmp_name']);
    finfo_close($finfo);

    if (!in_array($mime, $allowedTypes, true)) {
        error_response("Tipo de archivo no permitido: $mime", 415);
    }

    // Generar nombre seguro
    $ext = pathinfo($file['name'], PATHINFO_EXTENSION);
    $ext = preg_replace('/[^a-zA-Z0-9]/', '', $ext);
    $safeName = Database::uuid() . ($ext ? ".$ext" : '');

    // Crear directorio si no existe
    $targetDir = UPLOADS_PATH . '/' . $subdir;
    if (!is_dir($targetDir)) {
        mkdir($targetDir, 0750, true);
    }

    $targetPath = $targetDir . '/' . $safeName;

    if (!move_uploaded_file($file['tmp_name'], $targetPath)) {
        error_response('Error al guardar archivo', 500);
    }

    return [
        'path' => "$subdir/$safeName",
        'size' => $file['size'],
        'mime' => $mime,
        'original_name' => $file['name'],
    ];
}

/**
 * Elimina un archivo subido
 */
function delete_upload(string $relativePath): bool {
    $fullPath = UPLOADS_PATH . '/' . $relativePath;
    if (file_exists($fullPath)) {
        return unlink($fullPath);
    }
    return false;
}

/**
 * Envía un archivo para descarga
 */
function send_file_download($relativePath, $filename) {
    $fullPath = UPLOADS_PATH . '/' . $relativePath;

    if (!file_exists($fullPath)) {
        error_response('Archivo no encontrado', 404);
    }

    $finfo = finfo_open(FILEINFO_MIME_TYPE);
    $mime = finfo_file($finfo, $fullPath);
    finfo_close($finfo);

    header('Content-Type: ' . $mime);
    header('Content-Disposition: attachment; filename="' . basename($filename) . '"');
    header('Content-Length: ' . filesize($fullPath));
    header('Cache-Control: no-store');

    readfile($fullPath);
    exit;
}
