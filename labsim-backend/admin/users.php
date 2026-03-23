<?php
require_once __DIR__ . '/layout.php';
$auth = require_admin();

$message = null;
$error = null;

// ─── Acciones POST ──────────────────────────────────
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';

    if ($action === 'create') {
        $errors = [];
        if (empty($_POST['username'])) $errors[] = 'Username requerido';
        if (empty($_POST['password'])) $errors[] = 'Contraseña requerida';
        if (strlen($_POST['password'] ?? '') < 6) $errors[] = 'Contraseña mínimo 6 caracteres';

        if (empty($errors)) {
            $existing = Database::fetchOne('SELECT id FROM users WHERE username = :u', [':u' => $_POST['username']]);
            if ($existing) {
                $error = 'El username ya existe';
            } else {
                Database::execute(
                    "INSERT INTO users (id, username, email, password_hash, role, full_name, institution, must_change_password)
                     VALUES (:id, :u, :e, :h, :r, :n, :i, 1)",
                    [
                        ':id' => Database::uuid(),
                        ':u' => $_POST['username'],
                        ':e' => $_POST['email'] ?: null,
                        ':h' => password_hash($_POST['password'], PASSWORD_BCRYPT),
                        ':r' => $_POST['role'] ?? 'estudiante',
                        ':n' => $_POST['full_name'] ?: null,
                        ':i' => $_POST['institution'] ?: null,
                    ]
                );
                $message = 'Usuario creado exitosamente';
            }
        } else {
            $error = implode('. ', $errors);
        }
    }

    if ($action === 'toggle_active') {
        $userId = $_POST['user_id'] ?? '';
        if ($userId !== $auth['sub']) {
            $user = Database::fetchOne('SELECT is_active FROM users WHERE id = :id', [':id' => $userId]);
            if ($user) {
                $newState = $user['is_active'] ? 0 : 1;
                Database::execute("UPDATE users SET is_active = :s, updated_at = datetime('now') WHERE id = :id",
                    [':s' => $newState, ':id' => $userId]);
                $message = $newState ? 'Usuario activado' : 'Usuario desactivado';
            }
        } else {
            $error = 'No puedes desactivarte a ti mismo';
        }
    }

    if ($action === 'edit') {
        $userId = $_POST['user_id'] ?? '';
        if ($userId === $auth['sub'] && isset($_POST['role']) && $_POST['role'] !== 'admin') {
            $error = 'No puedes quitarte el rol admin a ti mismo';
        } else {
            $user = Database::fetchOne('SELECT id FROM users WHERE id = :id', [':id' => $userId]);
            if ($user) {
                $fields = [];
                $params = [':id' => $userId];

                if (isset($_POST['full_name'])) {
                    $fields[] = 'full_name = :fn';
                    $params[':fn'] = $_POST['full_name'] ?: null;
                }
                if (isset($_POST['email'])) {
                    $fields[] = 'email = :em';
                    $params[':em'] = $_POST['email'] ?: null;
                }
                if (!empty($_POST['role']) && in_array($_POST['role'], ['admin', 'docente', 'instructor', 'estudiante'])) {
                    $fields[] = 'role = :rl';
                    $params[':rl'] = $_POST['role'];
                }
                if (isset($_POST['institution'])) {
                    $fields[] = 'institution = :inst';
                    $params[':inst'] = $_POST['institution'] ?: null;
                }

                if (!empty($fields)) {
                    $fields[] = "updated_at = datetime('now')";
                    Database::execute(
                        "UPDATE users SET " . implode(', ', $fields) . " WHERE id = :id",
                        $params
                    );
                    $message = 'Usuario actualizado';
                }
            } else {
                $error = 'Usuario no encontrado';
            }
        }
    }

    if ($action === 'reset_password') {
        $userId = $_POST['user_id'] ?? '';
        $newPass = $_POST['new_password'] ?? '';
        if (strlen($newPass) >= 6) {
            Database::execute("UPDATE users SET password_hash = :h, must_change_password = 1, updated_at = datetime('now') WHERE id = :id",
                [':h' => password_hash($newPass, PASSWORD_BCRYPT), ':id' => $userId]);
            Database::execute('DELETE FROM refresh_tokens WHERE user_id = :uid', [':uid' => $userId]);
            $message = 'Contraseña actualizada. El usuario deberá cambiarla al ingresar.';
        } else {
            $error = 'La contraseña debe tener al menos 6 caracteres';
        }
    }
}

// ─── Filtros ────────────────────────────────────────
$roleFilter = $_GET['role'] ?? '';
$searchFilter = $_GET['search'] ?? '';
$page = max(1, (int)($_GET['page'] ?? 1));

$where = ['1=1'];
$params = [];

if ($roleFilter) {
    $where[] = 'role = :role';
    $params[':role'] = $roleFilter;
}
if ($searchFilter) {
    $where[] = "(username LIKE :s OR full_name LIKE :s OR email LIKE :s)";
    $params[':s'] = "%$searchFilter%";
}

$sql = "SELECT id, username, email, role, full_name, institution, is_active, created_at
        FROM users WHERE " . implode(' AND ', $where) . " ORDER BY created_at DESC";

$result = Database::paginate($sql, $params, $page, 20);
$users = $result['items'];
$pagination = $result['pagination'];

render_header('Usuarios', 'users');
?>

<?php if ($message): ?><div class="alert alert-success"><?= htmlspecialchars($message) ?></div><?php endif; ?>
<?php if ($error): ?><div class="alert alert-error"><?= htmlspecialchars($error) ?></div><?php endif; ?>

<div class="toolbar">
    <form class="toolbar-filters" method="GET">
        <select name="role" class="auto-filter">
            <option value="">Todos los roles</option>
            <option value="admin" <?= $roleFilter === 'admin' ? 'selected' : '' ?>>Admin</option>
            <option value="docente" <?= $roleFilter === 'docente' ? 'selected' : '' ?>>Docente</option>
            <option value="instructor" <?= $roleFilter === 'instructor' ? 'selected' : '' ?>>Instructor</option>
            <option value="estudiante" <?= $roleFilter === 'estudiante' ? 'selected' : '' ?>>Estudiante</option>
        </select>
        <input type="text" name="search" placeholder="Buscar..." value="<?= htmlspecialchars($searchFilter) ?>">
        <button type="submit" class="btn btn-sm btn-outline">Filtrar</button>
    </form>
    <button onclick="openModal('modal-create')" class="btn btn-primary">+ Nuevo usuario</button>
</div>

<?php
render_table(
    ['Username', 'Nombre', 'Email', 'Rol', 'Institución', 'Estado', 'Creado', 'Acciones'],
    $users,
    function($u) use ($auth) {
        $badge = render_badge($u['role'], $u['role']);
        $statusBadge = $u['is_active']
            ? render_badge('Activo', 'success')
            : render_badge('Inactivo', 'danger');
        $date = date('d M Y', strtotime($u['created_at']));
        $toggleLabel = $u['is_active'] ? 'Desactivar' : 'Activar';
        $toggleClass = $u['is_active'] ? 'btn-danger' : 'btn-success';

        $actions = '<div style="display:flex;gap:6px">';
        if ($u['id'] !== $auth['sub']) {
            $actions .= '<form method="POST" style="display:inline">
                <input type="hidden" name="action" value="toggle_active">
                <input type="hidden" name="user_id" value="' . $u['id'] . '">
                <button type="submit" class="btn btn-sm ' . $toggleClass . '" data-confirm="¿' . $toggleLabel . ' a ' . htmlspecialchars($u['username']) . '?">' . $toggleLabel . '</button>
            </form>';
        }
        $actions .= '<button class="btn btn-sm btn-outline" onclick="editUser(\'' . $u['id'] . '\',\'' . htmlspecialchars($u['username']) . '\',\'' . htmlspecialchars($u['full_name'] ?? '') . '\',\'' . htmlspecialchars($u['email'] ?? '') . '\',\'' . $u['role'] . '\',\'' . htmlspecialchars($u['institution'] ?? '') . '\')">Editar</button>';
        $actions .= '<button class="btn btn-sm btn-outline" onclick="resetPassword(\'' . $u['id'] . '\',\'' . htmlspecialchars($u['username']) . '\')">Reset pass</button>';
        $actions .= '</div>';

        return "<tr>
            <td><strong>" . htmlspecialchars($u['username']) . "</strong></td>
            <td>" . htmlspecialchars($u['full_name'] ?? '—') . "</td>
            <td>" . htmlspecialchars($u['email'] ?? '—') . "</td>
            <td>$badge</td>
            <td>" . htmlspecialchars($u['institution'] ?? '—') . "</td>
            <td>$statusBadge</td>
            <td>$date</td>
            <td>$actions</td>
        </tr>";
    }
);

$baseUrl = "users.php?role=$roleFilter&search=$searchFilter";
render_pagination($pagination['page'], $pagination['pages'], $baseUrl);
?>

<!-- Modal: Crear usuario -->
<div id="modal-create" class="modal-overlay">
    <div class="modal">
        <h3>Nuevo usuario</h3>
        <form method="POST">
            <input type="hidden" name="action" value="create">
            <div class="form-row">
                <div class="form-group">
                    <label>Username *</label>
                    <input type="text" name="username" required pattern="[a-zA-Z0-9._-]{3,50}">
                </div>
                <div class="form-group">
                    <label>Rol *</label>
                    <select name="role" required>
                        <option value="estudiante">Estudiante</option>
                        <option value="instructor">Instructor</option>
                        <option value="docente">Docente</option>
                        <option value="admin">Admin</option>
                    </select>
                </div>
            </div>
            <div class="form-group">
                <label>Nombre completo</label>
                <input type="text" name="full_name">
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" name="email">
            </div>
            <div class="form-group">
                <label>Institución</label>
                <input type="text" name="institution">
            </div>
            <div class="form-group">
                <label>Contraseña *</label>
                <input type="password" name="password" required minlength="6">
            </div>
            <div class="modal-actions">
                <button type="button" class="btn btn-outline" onclick="closeModal('modal-create')">Cancelar</button>
                <button type="submit" class="btn btn-primary">Crear usuario</button>
            </div>
        </form>
    </div>
</div>

<!-- Modal: Reset password -->
<div id="modal-reset" class="modal-overlay">
    <div class="modal">
        <h3>Reset contraseña: <span id="reset-username"></span></h3>
        <form method="POST">
            <input type="hidden" name="action" value="reset_password">
            <input type="hidden" name="user_id" id="reset-user-id">
            <div class="form-group">
                <label>Nueva contraseña *</label>
                <input type="password" name="new_password" required minlength="6">
            </div>
            <div class="modal-actions">
                <button type="button" class="btn btn-outline" onclick="closeModal('modal-reset')">Cancelar</button>
                <button type="submit" class="btn btn-warning">Cambiar contraseña</button>
            </div>
        </form>
    </div>
</div>

<!-- Modal: Editar usuario -->
<div id="modal-edit" class="modal-overlay">
    <div class="modal">
        <h3>Editar usuario: <span id="edit-username"></span></h3>
        <form method="POST">
            <input type="hidden" name="action" value="edit">
            <input type="hidden" name="user_id" id="edit-user-id">
            <div class="form-group">
                <label>Nombre completo</label>
                <input type="text" name="full_name" id="edit-full-name">
            </div>
            <div class="form-group">
                <label>Email</label>
                <input type="email" name="email" id="edit-email">
            </div>
            <div class="form-group">
                <label>Rol</label>
                <select name="role" id="edit-role">
                    <option value="estudiante">Estudiante</option>
                    <option value="instructor">Instructor</option>
                    <option value="docente">Docente</option>
                    <option value="admin">Admin</option>
                </select>
            </div>
            <div class="form-group">
                <label>Institución</label>
                <input type="text" name="institution" id="edit-institution">
            </div>
            <div class="modal-actions">
                <button type="button" class="btn btn-outline" onclick="closeModal('modal-edit')">Cancelar</button>
                <button type="submit" class="btn btn-primary">Guardar cambios</button>
            </div>
        </form>
    </div>
</div>

<script>
function editUser(userId, username, fullName, email, role, institution) {
    document.getElementById('edit-user-id').value = userId;
    document.getElementById('edit-username').textContent = username;
    document.getElementById('edit-full-name').value = fullName;
    document.getElementById('edit-email').value = email;
    document.getElementById('edit-role').value = role;
    document.getElementById('edit-institution').value = institution;
    openModal('modal-edit');
}

function resetPassword(userId, username) {
    document.getElementById('reset-user-id').value = userId;
    document.getElementById('reset-username').textContent = username;
    openModal('modal-reset');
}
</script>

<?php render_footer(); ?>
