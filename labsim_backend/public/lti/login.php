<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

// Moodle llama a este endpoint (GET o POST) para iniciar el login OIDC.
$params = $_REQUEST;
$issuer = $params['iss'] ?? '';
$clientId = $params['client_id'] ?? '';

if ($issuer === '' || !isset($params['login_hint'])) {
    Response::error('Request de login LTI incompleto', 400);
}

$platform = Lti::findPlatform($issuer, $clientId);
if (!$platform) {
    Response::error('Plataforma LTI no registrada', 403);
}

// Se arma desde la request en vez de hardcodear la ruta: así no se rompe
// si el backend termina viviendo en otra subcarpeta del hosting.
$scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
$dir = rtrim(str_replace('\\', '/', dirname($_SERVER['SCRIPT_NAME'])), '/');
$redirectUri = "{$scheme}://{$_SERVER['HTTP_HOST']}{$dir}/launch.php";
$url = Lti::buildAuthRedirect($platform, $params, $redirectUri);

header("Location: {$url}");
exit;
