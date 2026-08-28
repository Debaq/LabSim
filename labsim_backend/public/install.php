<?php

declare(strict_types=1);

/**
 * Instalador de un solo uso: crea config/config.php, la base sqlite (con el
 * schema aplicado) y el primer usuario admin, todo desde el navegador --
 * pensado para hosting compartido sin SSH. Al terminar se borra a sí mismo,
 * así no queda una puerta abierta para reinstalar por accidente.
 */

$backendRoot = dirname(__DIR__);
$configPath = $backendRoot . '/config/config.php';
$dbPath = $backendRoot . '/data/labsim.sqlite';
$schemaPath = $backendRoot . '/sql/schema.sql';

$alreadyInstalled = is_file($configPath);
$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && !$alreadyInstalled) {
    $username = trim((string) ($_POST['username'] ?? ''));
    $displayName = trim((string) ($_POST['display_name'] ?? '')) ?: $username;
    $password = (string) ($_POST['password'] ?? '');
    $passwordConfirm = (string) ($_POST['password_confirm'] ?? '');

    if ($username === '') {
        $error = 'Falta el usuario admin.';
    } elseif (strlen($password) < 8) {
        $error = 'La contraseña debe tener al menos 8 caracteres.';
    } elseif ($password !== $passwordConfirm) {
        $error = 'Las contraseñas no coinciden.';
    } else {
        try {
            $dataDir = dirname($dbPath);
            if (!is_dir($dataDir) && !mkdir($dataDir, 0775, true) && !is_dir($dataDir)) {
                throw new RuntimeException("No se pudo crear la carpeta {$dataDir} (revisa permisos).");
            }

            $configContents = "<?php\n\nreturn [\n"
                . "    'db' => ['path' => __DIR__ . '/../data/labsim.sqlite'],\n"
                . "    'sync_poll_seconds' => 15,\n"
                . "    'lti_jwks_cache_seconds' => 3600,\n"
                . "    'pairing_code_ttl_seconds' => 300,\n"
                . "];\n";
            if (file_put_contents($configPath, $configContents) === false) {
                throw new RuntimeException("No se pudo escribir {$configPath} (revisa permisos).");
            }

            $pdo = new PDO('sqlite:' . $dbPath, null, null, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            ]);
            $pdo->exec('PRAGMA journal_mode = WAL');
            $pdo->exec('PRAGMA foreign_keys = ON');

            $schema = file_get_contents($schemaPath);
            if ($schema === false) {
                throw new RuntimeException("No se encontró {$schemaPath}.");
            }
            $pdo->exec($schema);

            $hash = password_hash($password, PASSWORD_DEFAULT);
            $stmt = $pdo->prepare(
                "INSERT INTO users (role, username, display_name, password_hash, permission, modules)
                 VALUES ('admin', ?, ?, ?, 777, '[\"A\", \"Z\"]')"
            );
            $stmt->execute([$username, $displayName, $hash]);

            $success = "Admin '{$username}' creado. Backend instalado correctamente.";
            $alreadyInstalled = true;
        } catch (Throwable $e) {
            $error = 'Error durante la instalación: ' . $e->getMessage();
            // Si algo falló a mitad de camino, no dejar un config.php a medio
            // escribir -- mejor que el instalador se pueda reintentar.
            if (is_file($configPath) && $success === null) {
                unlink($configPath);
            }
        }

        if ($success !== null) {
            // Autodestrucción: nadie más puede volver a correr el instalador.
            @unlink(__FILE__);
        }
    }
}

header('Content-Type: text/html; charset=utf-8');
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>LabSim Backend - Instalación</title>
<style>
    body { font-family: system-ui, sans-serif; max-width: 480px; margin: 4rem auto; color: #222; }
    label { display: block; margin-top: 1rem; font-weight: 600; }
    input { width: 100%; padding: 0.5rem; margin-top: 0.25rem; box-sizing: border-box; }
    button { margin-top: 1.5rem; padding: 0.6rem 1.2rem; cursor: pointer; }
    .error { background: #fdecea; color: #611a15; padding: 0.75rem; border-radius: 4px; }
    .success { background: #e8f5e9; color: #1b5e20; padding: 0.75rem; border-radius: 4px; }
</style>
</head>
<body>
<h1>LabSim Backend</h1>

<?php if ($success !== null): ?>
    <p class="success"><?= htmlspecialchars($success) ?></p>
    <p>Este instalador ya se borró del servidor. Guarda el usuario/contraseña admin en un lugar seguro.</p>
<?php elseif ($alreadyInstalled): ?>
    <p class="success">Ya está instalado (existe config/config.php).</p>
    <p>Si necesitas reinstalar, borra <code>config/config.php</code> (y opcionalmente <code>data/labsim.sqlite</code> si quieres partir de cero) y vuelve a cargar esta página.</p>
<?php else: ?>
    <p>Primer y único paso: crea el usuario admin. Esto arma la base de datos y borra este instalador solo.</p>
    <?php if ($error !== null): ?>
        <p class="error"><?= htmlspecialchars($error) ?></p>
    <?php endif; ?>
    <form method="post">
        <label>Usuario admin
            <input type="text" name="username" required>
        </label>
        <label>Nombre a mostrar (opcional)
            <input type="text" name="display_name">
        </label>
        <label>Contraseña (mínimo 8 caracteres)
            <input type="password" name="password" required minlength="8">
        </label>
        <label>Repetir contraseña
            <input type="password" name="password_confirm" required minlength="8">
        </label>
        <button type="submit">Instalar</button>
    </form>
<?php endif; ?>
</body>
</html>
