<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Handoff desde el botón "Ver mis pacientes" de launch.php (LTI), mismo
 * mecanismo que admin/sso.php para el docente: launch.php corre dentro del
 * iframe de Moodle (cookie de tercero, varios navegadores la descartan), así
 * que no basta con levantar la sesión acá mismo -- se abre en pestaña nueva
 * (primer partido) y canjea el token de un solo uso (Auth::issuePortalSsoToken,
 * reusado tal cual -- no distingue rol, solo guarda user_id) para recién ahí
 * levantar la sesión de alumno.
 */

function render_sso_error(string $message): void
{
    header('Content-Type: text/html; charset=utf-8');
    ?>
    <!doctype html>
    <html lang="es">
    <head><meta charset="utf-8"><title>LabSim</title></head>
    <body style="font-family: sans-serif; text-align: center; margin-top: 4rem;">
        <h1>No se pudo entrar</h1>
        <p><?= htmlspecialchars($message) ?></p>
        <p>Vuelve a abrir la actividad desde Moodle y pincha "Ver mis pacientes" de nuevo.</p>
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

$stmt = Db::get()->prepare("SELECT active FROM users WHERE id = ? AND role = 'student'");
$stmt->execute([$userId]);
$user = $stmt->fetch();
if (!$user || (int) $user['active'] !== 1) {
    http_response_code(403);
    render_sso_error('La cuenta no está disponible.');
}

Auth::startSession();
session_regenerate_id(true);
$_SESSION['student_user_id'] = $userId;

header('Location: mis_pacientes.php');
