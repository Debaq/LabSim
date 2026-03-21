<?php
require_once __DIR__ . '/layout.php';

// Logout
if (isset($_GET['logout'])) {
    setcookie('labsim_admin_token', '', time() - 3600, '/', '', true, true);
    header('Location: login.php');
    exit;
}

// Ya autenticado
if (admin_auth()) {
    header('Location: index.php');
    exit;
}

$error = null;

// Procesar login
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = $_POST['username'] ?? '';
    $password = $_POST['password'] ?? '';

    $user = Database::fetchOne(
        'SELECT id, username, password_hash, role, is_active FROM users WHERE username = :u',
        [':u' => $username]
    );

    if (!$user || !password_verify($password, $user['password_hash'])) {
        $error = 'Credenciales inválidas';
    } elseif ($user['role'] !== 'admin') {
        $error = 'Solo administradores pueden acceder al panel';
    } elseif (!$user['is_active']) {
        $error = 'Cuenta desactivada';
    } else {
        $token = JWT::createAccessToken($user['id'], $user['username'], $user['role']);
        setcookie('labsim_admin_token', $token, [
            'expires' => time() + 86400,
            'path' => '/',
            'secure' => true,
            'httponly' => true,
            'samesite' => 'Strict',
        ]);
        header('Location: index.php');
        exit;
    }
}
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Login — LabSim Admin</title>
    <link rel="stylesheet" href="static/style.css">
</head>
<body>
    <div class="login-container">
        <div class="login-box">
            <h1>LabSim</h1>
            <p class="subtitle">Panel de Administración</p>

            <?php if ($error): ?>
                <div class="alert alert-error"><?= htmlspecialchars($error) ?></div>
            <?php endif; ?>

            <form method="POST">
                <div class="form-group">
                    <label>Usuario</label>
                    <input type="text" name="username" required autofocus
                           value="<?= htmlspecialchars($_POST['username'] ?? '') ?>">
                </div>
                <div class="form-group">
                    <label>Contraseña</label>
                    <input type="password" name="password" required>
                </div>
                <button type="submit" class="btn btn-primary" style="width:100%;margin-top:10px">
                    Iniciar sesión
                </button>
            </form>
        </div>
    </div>
</body>
</html>
