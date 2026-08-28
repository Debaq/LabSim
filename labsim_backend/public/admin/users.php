<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Users.php';
require_once __DIR__ . '/_layout.php';

$me = Auth::requireFullAdminSession();

$error = null;
$success = null;

// 'docente' no es un role de tabla (el CHECK solo admite student|admin) --
// se guarda como role='admin' con permission acotado (ver
// Auth::PERMISSION_DOCENTE); Auth::requireFullAdminSession() es lo que en
// la práctica separa a un docente de un admin completo.
$roleToPermission = [
    'student' => 444,
    'docente' => Auth::PERMISSION_DOCENTE,
    'admin' => Auth::PERMISSION_ADMIN,
];

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['form_action'] ?? '';

    if ($action === 'create') {
        $roleChoice = (string) ($_POST['role'] ?? 'student');
        $username = trim((string) ($_POST['username'] ?? ''));
        $displayName = trim((string) ($_POST['display_name'] ?? '')) ?: $username;
        $password = (string) ($_POST['password'] ?? '');

        if (!isset($roleToPermission[$roleChoice])) {
            $error = "Rol inválido.";
        } elseif ($username === '' || strlen($password) < 8) {
            $error = 'Falta usuario o contraseña (mínimo 8 caracteres).';
        } else {
            $role = $roleChoice === 'student' ? 'student' : 'admin';
            $permission = $roleToPermission[$roleChoice];
            Users::createOrUpdateLocal($role, $username, $displayName, $password, $permission, ['A', 'Z']);
            $success = "Usuario '{$username}' guardado.";
        }
    } elseif ($action === 'update_user') {
        // A diferencia de 'create', esto NO toca password_hash -- cambiar
        // el rol de un alumno a docente (o al revés) no debería obligar a
        // resetearle la clave cada vez.
        $userId = (int) ($_POST['user_id'] ?? 0);
        $roleChoice = (string) ($_POST['role'] ?? 'student');
        $displayName = trim((string) ($_POST['display_name'] ?? ''));

        if ($userId <= 0 || !isset($roleToPermission[$roleChoice])) {
            $error = 'Datos inválidos.';
        } elseif ($displayName === '') {
            $error = 'Falta el nombre a mostrar.';
        } else {
            $role = $roleChoice === 'student' ? 'student' : 'admin';
            Users::updateProfile($userId, $role, $roleToPermission[$roleChoice], $displayName);
            $success = 'Usuario actualizado.';
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

function fmt_role(array $u): string
{
    if ($u['role'] !== 'admin') {
        return 'Alumno';
    }
    return (int) $u['permission'] === Auth::PERMISSION_ADMIN ? 'Admin' : 'Docente';
}

/** Inverso de $roleToPermission -- para preseleccionar el <select> del form de editar. */
function role_choice_of(array $u): string
{
    if ($u['role'] !== 'admin') {
        return 'student';
    }
    return (int) $u['permission'] === Auth::PERMISSION_ADMIN ? 'admin' : 'docente';
}

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
                <option value="docente">Docente</option>
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
        <tr><th>Rol</th><th>Usuario</th><th>Nombre</th><th>LTI</th><th>Activo</th><th></th><th></th></tr>
        <?php foreach ($users as $u): ?>
        <tr>
            <td><?= htmlspecialchars(fmt_role($u)) ?></td>
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
            <td>
                <details>
                    <summary>Editar</summary>
                    <form method="post" style="margin-top:0.4rem;">
                        <input type="hidden" name="form_action" value="update_user">
                        <input type="hidden" name="user_id" value="<?= (int) $u['id'] ?>">
                        <label>Rol
                            <select name="role">
                                <option value="student" <?= role_choice_of($u) === 'student' ? 'selected' : '' ?>>Alumno</option>
                                <option value="docente" <?= role_choice_of($u) === 'docente' ? 'selected' : '' ?>>Docente</option>
                                <option value="admin" <?= role_choice_of($u) === 'admin' ? 'selected' : '' ?>>Admin</option>
                            </select>
                        </label>
                        <label>Nombre a mostrar
                            <input type="text" name="display_name" value="<?= htmlspecialchars($u['display_name']) ?>" required>
                        </label>
                        <button type="submit" class="secondary" style="margin-top:0.4rem; padding:0.2rem 0.6rem; font-size:0.8rem;">Guardar</button>
                    </form>
                </details>
            </td>
        </tr>
        <?php endforeach; ?>
    </table>
</div>
<?php
admin_footer();
