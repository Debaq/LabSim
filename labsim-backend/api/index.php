<?php
/**
 * LabSim Backend - API Router
 *
 * Todas las rutas llegan aquí via .htaccess:
 *   /api/v1/auth/login → ?route=auth/login
 */

require_once __DIR__ . '/../core/config.php';
require_once __DIR__ . '/../core/response.php';
require_once __DIR__ . '/../core/db.php';

// Error handler global
set_error_handler(function (int $errno, string $errstr, string $errfile, int $errline) {
    if (LABSIM_DEBUG) {
        error_response("Error: $errstr en $errfile:$errline", 500);
    }
    error_response('Error interno del servidor', 500);
});

set_exception_handler(function (Throwable $e) {
    if (LABSIM_DEBUG) {
        error_response($e->getMessage(), 500, [
            'file' => $e->getFile(),
            'line' => $e->getLine(),
        ]);
    }
    error_response('Error interno del servidor', 500);
});

// CORS
handle_cors();

// Obtener ruta y método
$route = trim($_GET['route'] ?? '', '/');
$method = $_SERVER['REQUEST_METHOD'];

// Parsear segmentos de la ruta
$segments = $route ? explode('/', $route) : [];
$resource = $segments[0] ?? '';

// Despachar al handler correcto
$handlers = [
    'auth'        => __DIR__ . '/auth.php',
    'users'       => __DIR__ . '/users.php',
    'cases'       => __DIR__ . '/cases.php',
    'groups'      => __DIR__ . '/groups.php',
    'sessions'    => __DIR__ . '/sessions.php',
    'submissions' => __DIR__ . '/submissions.php',
    'agenda'      => __DIR__ . '/agenda.php',
    'procedures'  => __DIR__ . '/procedures.php',
    'feedback'    => __DIR__ . '/feedback.php',
    'directives'  => __DIR__ . '/directives.php',
    'center'      => __DIR__ . '/center.php',
    'telemetry'   => __DIR__ . '/telemetry.php',
    'stats'       => __DIR__ . '/stats.php',
    'assets'      => __DIR__ . '/assets.php',
    'releases'    => __DIR__ . '/assets.php',
    'sync'        => __DIR__ . '/sync.php',
    'institutions' => __DIR__ . '/institutions.php',
    'courses'     => __DIR__ . '/courses.php',
    'patient-logs' => __DIR__ . '/patient-logs.php',
    'evolutions'  => __DIR__ . '/evolutions.php',
    'interconsultations' => __DIR__ . '/interconsultations.php',
];

if (!isset($handlers[$resource])) {
    // Ruta raíz: info de la API
    if ($route === '' || $route === '/') {
        json_response([
            'name' => 'LabSim Backend API',
            'version' => '1.0.0',
            'status' => 'ok',
        ]);
    }
    error_response('Ruta no encontrada: ' . $route, 404);
}

// Pasar segmentos restantes al handler
$routeSegments = array_slice($segments, 1);

require $handlers[$resource];
