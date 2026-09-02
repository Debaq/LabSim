<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/AdminAudit.php';

$me = Auth::requireFullAdminSession();

$error = null;
$success = null;
$generated11 = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $id = $_POST['id'] !== '' ? (int) $_POST['id'] : null;
    $ltiVersion = $_POST['lti_version'] ?? '1.3';

    if ($ltiVersion === '1.1') {
        // El backend genera las credenciales (como hace Moodle al registrar
        // un tool) en vez de que el admin las invente a mano -- menos typos,
        // más entropía. El shared_secret solo se muestra esta vez.
        $consumerKey = bin2hex(random_bytes(16));
        $sharedSecret = bin2hex(random_bytes(24));
        Lti::upsertPlatform11($id, $consumerKey, $sharedSecret);
        $success = $id !== null ? 'Credenciales LTI 1.1 regeneradas.' : 'Herramienta LTI 1.1 creada.';
        $generated11 = ['consumer_key' => $consumerKey, 'shared_secret' => $sharedSecret];
        AdminAudit::log($me, $id !== null ? 'lti11_regenerate' : 'lti11_create', ['id' => $id]);
    } else {
        $issuer = trim((string) ($_POST['issuer'] ?? ''));
        $clientId = trim((string) ($_POST['client_id'] ?? ''));
        $deploymentId = trim((string) ($_POST['deployment_id'] ?? ''));
        $authLoginUrl = trim((string) ($_POST['auth_login_url'] ?? ''));
        $authTokenUrl = trim((string) ($_POST['auth_token_url'] ?? ''));
        $jwksUrl = trim((string) ($_POST['jwks_url'] ?? ''));

        if ($issuer === '' || $clientId === '' || $deploymentId === '' || $authLoginUrl === '' || $jwksUrl === '') {
            $error = 'Completa issuer, client_id, deployment_id, auth_login_url y jwks_url (todos vienen de la pantalla "External tool" de Moodle).';
        } else {
            Lti::upsertPlatform13($id, $issuer, $clientId, $deploymentId, $authLoginUrl, $authTokenUrl ?: $authLoginUrl, $jwksUrl);
            $success = 'Plataforma LTI 1.3 guardada.';
            AdminAudit::log($me, 'lti13_upsert', ['id' => $id, 'issuer' => $issuer]);
        }
    }
}

$scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
$baseDir = rtrim(str_replace('\\', '/', dirname(dirname($_SERVER['SCRIPT_NAME']))), '/');
$loginUrl = "{$scheme}://{$_SERVER['HTTP_HOST']}{$baseDir}/lti/login.php";
$launchUrl = "{$scheme}://{$_SERVER['HTTP_HOST']}{$baseDir}/lti/launch.php";

$platforms = Lti::listPlatforms();

admin_header('Conexión LTI (Moodle)', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <strong>LTI 1.1 (OAuth1) -- más simple, recomendado si 1.3 da problemas</strong>
    <p style="font-size:0.85rem; color:#555;">
        Primero crea la herramienta acá abajo (el backend genera las credenciales), después regístrala en Moodle:
        Administración del sitio → Plugins → Herramientas externas → Gestionar herramientas →
        Configurar una herramienta manualmente, versión LTI <strong>1.0/1.1</strong>.
    </p>

    <?php if ($generated11 !== null): ?>
    <div style="background:#fffbe6; border:1px solid #e0c200; padding:0.75rem; margin:0.5rem 0;">
        <strong>Copia esto en Moodle ahora -- el shared secret no se vuelve a mostrar:</strong>
        <p>Tool URL<br><span class="mono"><?= htmlspecialchars($launchUrl) ?></span></p>
        <p>Consumer key<br><span class="mono"><?= htmlspecialchars($generated11['consumer_key']) ?></span></p>
        <p>Shared secret<br><span class="mono"><?= htmlspecialchars($generated11['shared_secret']) ?></span></p>
    </div>
    <?php endif; ?>

    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="id" value="">
        <input type="hidden" name="lti_version" value="1.1">
        <button type="submit">Crear nueva herramienta LTI 1.1</button>
    </form>
</div>

<div class="card">
    <strong>LTI 1.3 (OIDC) -- URLs para registrar LabSim como "herramienta externa" en Moodle</strong>
    <p style="font-size:0.85rem; color:#555;">
        Configura una herramienta manualmente, versión LTI 1.3.
    </p>
    <label>Initiate login URL</label>
    <p class="mono"><?= htmlspecialchars($loginUrl) ?></p>
    <label>Redirection URI (Tool launch URL)</label>
    <p class="mono"><?= htmlspecialchars($launchUrl) ?></p>
    <p style="font-size:0.85rem; color:#555;">
        Moodle, a cambio, te va a dar <code>Platform ID</code> (issuer), <code>Client ID</code>,
        <code>Public keyset URL</code> (jwks_url) y <code>Access token URL</code> -- pégalos abajo
        junto con el <code>Deployment ID</code> (aparece después de guardar la herramienta en Moodle).
    </p>
    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="id" value="">
        <input type="hidden" name="lti_version" value="1.3">
        <label>Issuer (Platform ID)
            <input type="text" name="issuer" placeholder="https://tu-moodle.cl" required>
        </label>
        <label>Client ID
            <input type="text" name="client_id" required>
        </label>
        <label>Deployment ID
            <input type="text" name="deployment_id" required>
        </label>
        <label>Auth login URL (Moodle: "Authentication request URL")
            <input type="text" name="auth_login_url" required>
        </label>
        <label>Auth token URL (opcional, no se usa en este flujo)
            <input type="text" name="auth_token_url">
        </label>
        <label>JWKS URL (Moodle: "Public keyset URL")
            <input type="text" name="jwks_url" required>
        </label>
        <button type="submit">Guardar</button>
    </form>
</div>

<div class="card">
    <strong>Plataformas registradas</strong>
    <table>
        <tr><th>Versión</th><th>Issuer / Consumer key</th><th>Client ID</th><th>Deployment ID</th><th>Activa</th><th></th></tr>
        <?php foreach ($platforms as $p): ?>
        <tr>
            <td><?= htmlspecialchars($p['version']) ?></td>
            <td><?= htmlspecialchars($p['version'] === '1.1' ? $p['consumer_key'] : $p['issuer']) ?></td>
            <td><?= htmlspecialchars($p['client_id']) ?></td>
            <td><?= htmlspecialchars($p['deployment_id']) ?></td>
            <td><?= $p['active'] ? 'sí' : 'no' ?></td>
            <td>
                <?php if ($p['version'] === '1.1'): ?>
                <form method="post" onsubmit="return confirm('Esto invalida el shared secret actual -- hay que actualizarlo en Moodle también. ¿Regenerar?');">
                <?= csrf_field() ?>
                    <input type="hidden" name="id" value="<?= (int) $p['id'] ?>">
                    <input type="hidden" name="lti_version" value="1.1">
                    <button type="submit">Regenerar</button>
                </form>
                <?php endif; ?>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$platforms): ?>
        <tr><td colspan="6" style="color:#888;">Ninguna registrada todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>
<?php
admin_footer();
