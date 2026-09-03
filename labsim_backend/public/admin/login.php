<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';

Auth::startSession();
if (!empty($_SESSION['admin_user_id'])) {
    $stmt = Db::get()->prepare("SELECT permission FROM users WHERE id = ? AND role = 'admin' AND active = 1");
    $stmt->execute([$_SESSION['admin_user_id']]);
    $permission = (int) ($stmt->fetchColumn() ?: 0);
    header('Location: ' . ($permission === Auth::PERMISSION_ADMIN ? 'index.php' : 'courses.php'));
    exit;
}

$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = trim((string) ($_POST['username'] ?? ''));
    $password = (string) ($_POST['password'] ?? '');
    $ip = (string) ($_SERVER['REMOTE_ADDR'] ?? 'unknown');

    if (Auth::loginBlocked($username, $ip)) {
        $error = 'Demasiados intentos fallidos. Espera unos minutos e inténtalo de nuevo.';
    } else {
        $user = Auth::verifyAdminPassword($username, $password);
        Auth::recordLoginAttempt($username, $ip, $user !== null);
        if ($user === null) {
            $error = 'Usuario o contraseña incorrectos.';
        } else {
            // Session fixation: si el atacante fijó este PHPSESSID antes del
            // login (link con sesión precargada, cookie mal scopeada), un
            // ID nuevo post-auth invalida esa sesión pre-fijada.
            session_regenerate_id(true);
            $_SESSION['admin_user_id'] = $user['id'];
            // Docente (permission 555) no tiene acceso a index.php (Estado,
            // requireFullAdminSession) -- mandarlo ahí daba 403 en blanco.
            $landing = (int) $user['permission'] === Auth::PERMISSION_ADMIN ? 'index.php' : 'courses.php';
            header('Location: ' . $landing);
            exit;
        }
    }
}

admin_header('Ingresar');
?>
<?php if ($error !== null): ?>
    <p class="error"><?= htmlspecialchars($error) ?></p>
<?php endif; ?>
<div class="card" style="max-width:360px;">
    <form method="post">
        <label>Usuario
            <input type="text" name="username" required autofocus>
        </label>
        <label>Contraseña
            <input type="password" name="password" required>
        </label>
        <button type="submit">Ingresar</button>
    </form>
</div>
<?php
admin_footer();
