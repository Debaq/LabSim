<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Users.php';
require_once __DIR__ . '/_layout.php';

$me = Auth::requireAdminSession();

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['form_action'] ?? '';

    if ($action === 'create') {
        $role = (string) ($_POST['role'] ?? 'student');
        $username = trim((string) ($_POST['username'] ?? ''));
        $displayName = trim((string) ($_POST['display_name'] ?? '')) ?: $username;
        $password = (string) ($_POST['password'] ?? '');
        $permission = $role === 'admin' ? 777 : 444;

        if (!in_array($role, ['admin', 'student'], true)) {
            $error = "Rol inválido.";
        } elseif ($username === '' || strlen($password) < 8) {
            $error = 'Falta usuario o contraseña (mínimo 8 caracteres).';
        } else {
            Users::createOrUpdateLocal($role, $username, $displayName, $password, $permission, ['A', 'Z']);
            $success = "Usuario '{$username}' guardado.";
        }
    } elseif ($action === 'toggle_active') {
        $userId = (int) ($_POST['user_id'] ?? 0);
        $active = ($_POST['active'] ?? '') === '1';
        if ($userId > 0) {
            Users::setActive($userId, $active);
            $success = 'Usuario actualizado.';
        }
    }
}

$users = Users::listAll();

admin_header('Usuarios', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <strong>Crear / actualizar usuario local</strong>
    <p style="font-size:0.85rem; color:#555;">
        Login con usuario/contraseña, sin pasar por Moodle. Útil para admins reales y para
        cuentas de alumno de prueba (p. ej. <code>labsim</code>) mientras no haya LTI conectado.
        Si el usuario ya existe, esto actualiza su contraseña y rol.
    </p>
    <form method="post">
        <input type="hidden" name="form_action" value="create">
        <label>Rol
            <select name="role">
                <option value="student">Alumno</option>
                <option value="admin">Admin</option>
            </select>
        </label>
        <label>Usuario
            <input type="text" name="username" required>
        </label>
        <label>Nombre a mostrar (opcional)
            <input type="text" name="display_name">
        </label>
        <label>Contraseña (mínimo 8 caracteres)
            <input type="password" name="password" required minlength="8">
        </label>
        <button type="submit">Guardar</button>
    </form>
</div>

<div class="card">
    <strong>Usuarios existentes</strong>
    <table>
        <tr><th>Rol</th><th>Usuario</th><th>Nombre</th><th>LTI</th><th>Activo</th><th></th></tr>
        <?php foreach ($users as $u): ?>
        <tr>
            <td><?= htmlspecialchars($u['role']) ?></td>
            <td><?= htmlspecialchars($u['username']) ?></td>
            <td>
                <?php if ($u['role'] === 'student'): ?>
                <a href="student.php?id=<?= (int) $u['id'] ?>"><?= htmlspecialchars($u['display_name']) ?></a>
                <?php else: ?>
                <?= htmlspecialchars($u['display_name']) ?>
                <?php endif; ?>
            </td>
            <td><?= $u['lti_sub'] ? 'sí' : '—' ?></td>
            <td><?= $u['active'] ? 'sí' : 'no' ?></td>
            <td>
                <form method="post" class="inline">
                    <input type="hidden" name="form_action" value="toggle_active">
                    <input type="hidden" name="user_id" value="<?= (int) $u['id'] ?>">
                    <input type="hidden" name="active" value="<?= $u['active'] ? '0' : '1' ?>">
                    <button type="submit" class="secondary" style="margin-top:0; padding:0.2rem 0.6rem; font-size:0.8rem;">
                        <?= $u['active'] ? 'Desactivar' : 'Activar' ?>
                    </button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
    </table>
</div>
<?php
admin_footer();
