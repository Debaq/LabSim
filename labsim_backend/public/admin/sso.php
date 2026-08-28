<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Handoff desde el botón "Ir a plataforma" de launch.php (LTI). Ese launch
 * corre dentro del iframe de Moodle -- cookie de tercero, varios navegadores
 * hoy la descartan -- así que no basta con levantar la sesión de portal ahí
 * mismo. Esta página se abre en pestaña nueva (primer partido) y canjea el
 * token de un solo uso (Auth::issuePortalSsoToken) para recién ahí levantar
 * la sesión de portal de verdad.
 */

function render_sso_error(string $message): void
{
    header('Content-Type: text/html; charset=utf-8');
    ?>
    <!doctype html>
    <html lang="es">
    <head><meta charset="utf-8"><title>LabSim</title></head>
    <body style="font-family: sans-serif; text-align: center; margin-top: 4rem;">
        <h1>No se pudo entrar a la plataforma</h1>
        <p><?= htmlspecialchars($message) ?></p>
        <p>Vuelve a abrir la actividad desde Moodle y pincha "Ir a plataforma" de nuevo.</p>
    </body>
    </html>
    <?php
    exit;
}

$token = (string) ($_GET['token'] ?? '');
$userId = $token !== '' ? Auth::consumePortalSsoToken($token) : null;
if ($userId === null) {
    http_response_code(403);
    render_sso_error('El enlace venció o ya se usó.');
}

$stmt = Db::get()->prepare("SELECT permission, active FROM users WHERE id = ? AND role = 'admin'");
$stmt->execute([$userId]);
$user = $stmt->fetch();
if (!$user || (int) $user['active'] !== 1) {
    http_response_code(403);
    render_sso_error('La cuenta no tiene permisos de portal.');
}

if (session_status() !== PHP_SESSION_ACTIVE) {
    session_start();
}
$_SESSION['admin_user_id'] = $userId;

// index.php exige admin completo (777) -- gestión de schema/usuarios/LTI,
// no es para docente. Docente (555) entra a dashboard.php (requireAdminSession
// sin nivel completo), que ya es donde están las métricas por alumno.
$dest = (int) $user['permission'] === Auth::PERMISSION_ADMIN ? 'index.php' : 'dashboard.php';
header('Location: ' . $dest);
exit;
