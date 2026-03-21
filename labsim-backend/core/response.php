<?php
/**
 * LabSim Backend - Helpers de respuesta JSON
 * Compatible con PHP 7.4+
 */

/**
 * Envía respuesta JSON exitosa
 * @param mixed $data
 * @param int $status
 * @return void
 */
function json_response($data, $status = 200) {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode($data, JSON_UNESCAPED_UNICODE);
    exit;
}

/**
 * Envía respuesta de error
 * @param string $message
 * @param int $status
 * @param array|null $details
 * @return void
 */
function error_response($message, $status = 400, $details = null) {
    http_response_code($status);
    header('Content-Type: application/json; charset=utf-8');
    $body = ['error' => $message];
    if ($details !== null) {
        $body['details'] = $details;
    }
    echo json_encode($body, JSON_UNESCAPED_UNICODE);
    exit;
}

/**
 * Envía respuesta 201 Created con los datos del recurso creado
 * @param mixed $data
 * @return void
 */
function created_response($data) {
    json_response($data, 201);
}

/**
 * Envía respuesta 204 No Content
 * @return void
 */
function no_content_response() {
    http_response_code(204);
    exit;
}

/**
 * Maneja CORS preflight y headers
 */
function handle_cors() {
    $origin = $_SERVER['HTTP_ORIGIN'] ?? '';

    if (in_array($origin, CORS_ORIGINS, true)) {
        header("Access-Control-Allow-Origin: $origin");
        header('Access-Control-Allow-Credentials: true');
    }

    header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Authorization');
    header('Access-Control-Max-Age: 86400');

    // Preflight
    if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
        http_response_code(204);
        exit;
    }
}

/**
 * Lee y decodifica el body JSON del request
 * @return array
 */
function get_json_body() {
    $raw = file_get_contents('php://input');
    if (empty($raw)) {
        return [];
    }

    // Límite de tamaño: 5MB
    if (strlen($raw) > 5 * 1024 * 1024) {
        error_response('Request body demasiado grande', 413);
    }

    $data = json_decode($raw, true);
    if (json_last_error() !== JSON_ERROR_NONE) {
        error_response('JSON inválido: ' . json_last_error_msg(), 400);
    }

    return $data;
}

/**
 * Obtiene parámetro GET con valor por defecto
 * @param string $key
 * @param mixed $default
 * @return mixed
 */
function query_param($key, $default = null) {
    return $_GET[$key] ?? $default;
}

/**
 * Obtiene parámetro GET como entero
 * @param string $key
 * @param int $default
 * @return int
 */
function query_int($key, $default) {
    $val = $_GET[$key] ?? null;
    return $val !== null ? (int)$val : $default;
}
