<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * El schema de `tokens` ya decía "bearer opaco, revocable... más simple de
 * invalidar desde el panel admin" pero esa UI nunca se construyó -- celular
 * perdido o cuenta comprometida no tenían forma de cortar la sesión desde
 * acá, solo esperar a que expirara sola (nunca expira sola, de hecho).
 */

$me = Auth::requireFullAdminSession();
$pdo = Db::get();

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $action = (string) ($_POST['form_action'] ?? '');

    if ($action === 'revoke') {
        $token = (string) ($_POST['token'] ?? '');
        $stmt = $pdo->prepare('SELECT u.username FROM tokens t JOIN users u ON u.id = t.user_id WHERE t.token = ?');
        $stmt->execute([$token]);
        $owner = $stmt->fetchColumn();
        if ($owner !== false) {
            $pdo->prepare('DELETE FROM tokens WHERE token = ?')->execute([$token]);
            $success = "Sesión de '{$owner}' revocada.";
            AdminAudit::log($me, 'token_revoke', ['username' => $owner, 'token_suffix' => substr($token, -8)]);
        }
    }
}

$tokens = $pdo->query(
    "SELECT t.token, t.created_at, t.last_seen_at, u.id AS user_id, u.username, u.display_name, u.role
     FROM tokens t JOIN users u ON u.id = t.user_id
     ORDER BY t.last_seen_at DESC"
)->fetchAll();

admin_header('Sesiones (tokens)', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <p style="font-size:0.85rem; color:#555;">
        Cada fila es un token bearer activo de la app de escritorio (uno por dispositivo/login).
        Revocar corta la sesión de inmediato -- ese dispositivo vuelve a pedir el código de emparejamiento.
        Útil si se perdió un celular/PC o una cuenta quedó comprometida.
    </p>
    <table>
        <tr><th>Usuario</th><th>Rol</th><th>Creado</th><th>Última actividad</th><th>Token</th><th></th></tr>
        <?php foreach ($tokens as $t): ?>
        <tr>
            <td><?= htmlspecialchars($t['display_name']) ?> <span style="color:#888;">(<?= htmlspecialchars($t['username']) ?>)</span></td>
            <td><?= htmlspecialchars($t['role']) ?></td>
            <td><?= htmlspecialchars($t['created_at']) ?></td>
            <td><?= htmlspecialchars($t['last_seen_at']) ?></td>
            <td class="mono" style="font-size:0.78rem;">&hellip;<?= htmlspecialchars(substr($t['token'], -8)) ?></td>
            <td>
                <form method="post" class="inline" onsubmit="return confirm('¿Revocar esta sesión? El dispositivo tendrá que emparejarse de nuevo.');">
                <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="revoke">
                    <input type="hidden" name="token" value="<?= htmlspecialchars($t['token']) ?>">
                    <button type="submit" class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Revocar</button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$tokens): ?>
        <tr><td colspan="6" style="color:#888;">Ninguna sesión activa.</td></tr>
        <?php endif; ?>
    </table>
</div>
<?php
admin_footer();
