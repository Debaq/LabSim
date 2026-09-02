<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';

Auth::startSession();
if (!empty($_SESSION['admin_user_id'])) {
    header('Location: index.php');
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
            header('Location: index.php');
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
