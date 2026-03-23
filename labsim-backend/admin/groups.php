<?php
require_once __DIR__ . '/layout.php';
$auth = require_admin();

$message = null;
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';

    if ($action === 'create') {
        if (empty($_POST['name'])) {
            $error = 'Nombre requerido';
        } else {
            Database::execute(
                "INSERT INTO student_groups (id, name, description, institution, created_by)
                 VALUES (:id, :name, :desc, :inst, :uid)",
                [
                    ':id' => Database::uuid(),
                    ':name' => $_POST['name'],
                    ':desc' => $_POST['description'] ?: null,
                    ':inst' => $_POST['institution'] ?: null,
                    ':uid' => $auth['sub'],
                ]
            );
            $message = 'Grupo creado';
        }
    }

    if ($action === 'add_member') {
        $groupId = $_POST['group_id'] ?? '';
        $username = $_POST['member_username'] ?? '';
        $memberRole = $_POST['member_role'] ?? 'student';

        $user = Database::fetchOne('SELECT id FROM users WHERE username = :u AND is_active = 1', [':u' => $username]);
        if (!$user) {
            $error = "Usuario '$username' no encontrado";
        } else {
            $exists = Database::fetchOne(
                'SELECT group_id FROM group_members WHERE group_id = :gid AND user_id = :uid',
                [':gid' => $groupId, ':uid' => $user['id']]
            );
            if ($exists) {
                $error = 'El usuario ya es miembro del grupo';
            } else {
                Database::execute(
                    "INSERT INTO group_members (group_id, user_id, member_role) VALUES (:gid, :uid, :role)",
                    [':gid' => $groupId, ':uid' => $user['id'], ':role' => $memberRole]
                );
                $message = "Miembro agregado al grupo";
            }
        }
    }

    if ($action === 'remove_member') {
        Database::execute(
            'DELETE FROM group_members WHERE group_id = :gid AND user_id = :uid',
            [':gid' => $_POST['group_id'], ':uid' => $_POST['user_id']]
        );
        $message = 'Miembro removido';
    }
    if ($action === 'delete') {
        $groupId = $_POST['group_id'] ?? '';
        Database::execute('DELETE FROM group_members WHERE group_id = :gid', [':gid' => $groupId]);
        Database::execute('DELETE FROM student_groups WHERE id = :id', [':id' => $groupId]);
        $message = 'Grupo eliminado';
    }
    if ($action === 'toggle_active') {
        $groupId = $_POST['group_id'] ?? '';
        $g = Database::fetchOne('SELECT is_active FROM student_groups WHERE id = :id', [':id' => $groupId]);
        if ($g) {
            $new = $g['is_active'] ? 0 : 1;
            Database::execute("UPDATE student_groups SET is_active = :a WHERE id = :id", [':a' => $new, ':id' => $groupId]);
            $message = $new ? 'Grupo activado' : 'Grupo archivado';
        }
    }
    if ($action === 'duplicate') {
        $groupId = $_POST['group_id'] ?? '';
        $g = Database::fetchOne('SELECT * FROM student_groups WHERE id = :id', [':id' => $groupId]);
        if ($g) {
            $newId = Database::uuid();
            Database::execute(
                "INSERT INTO student_groups (id, name, description, institution, created_by)
                 VALUES (:id, :name, :desc, :inst, :uid)",
                [':id' => $newId, ':name' => 'Copia de ' . $g['name'], ':desc' => $g['description'], ':inst' => $g['institution'], ':uid' => $auth['sub']]
            );
            $message = 'Grupo duplicado';
        }
    }
}

// ─── Vista de detalle de grupo ──────────────────────
$detailId = $_GET['id'] ?? null;

if ($detailId) {
    $group = Database::fetchOne("SELECT g.*, u.username as creator FROM student_groups g LEFT JOIN users u ON g.created_by = u.id WHERE g.id = :id", [':id' => $detailId]);
    if (!$group) { header('Location: groups.php'); exit; }

    $members = Database::fetchAll(
        "SELECT gm.member_role, u.id, u.username, u.full_name, u.role, u.email
         FROM group_members gm JOIN users u ON gm.user_id = u.id WHERE gm.group_id = :gid ORDER BY gm.member_role, u.full_name",
        [':gid' => $detailId]
    );

    render_header('Grupo: ' . $group['name'], 'groups');
    ?>
    <?php if ($message): ?><div class="alert alert-success"><?= htmlspecialchars($message) ?></div><?php endif; ?>
    <?php if ($error): ?><div class="alert alert-error"><?= htmlspecialchars($error) ?></div><?php endif; ?>

    <a href="groups.php" class="btn btn-sm btn-outline" style="margin-bottom:20px">← Volver</a>

    <div class="detail-grid">
        <div class="detail-item"><label>Nombre</label><div class="value"><?= htmlspecialchars($group['name']) ?></div></div>
        <div class="detail-item"><label>Creador</label><div class="value"><?= htmlspecialchars($group['creator'] ?? '—') ?></div></div>
        <div class="detail-item"><label>Institución</label><div class="value"><?= htmlspecialchars($group['institution'] ?? '—') ?></div></div>
        <div class="detail-item"><label>Estado</label><div class="value"><?= $group['is_active'] ? render_badge('Activo', 'success') : render_badge('Inactivo', 'danger') ?></div></div>
    </div>
    <?php if ($group['description']): ?>
        <p style="margin-bottom:20px;color:var(--text-secondary)"><?= htmlspecialchars($group['description']) ?></p>
    <?php endif; ?>

    <h3 style="margin-bottom:15px">Miembros (<?= count($members) ?>)</h3>

    <form method="POST" style="display:flex;gap:10px;margin-bottom:15px;align-items:flex-end">
        <input type="hidden" name="action" value="add_member">
        <input type="hidden" name="group_id" value="<?= $detailId ?>">
        <div class="form-group" style="margin:0">
            <label>Username</label>
            <input type="text" name="member_username" required placeholder="username">
        </div>
        <div class="form-group" style="margin:0">
            <label>Rol en grupo</label>
            <select name="member_role">
                <option value="student">Estudiante</option>
                <option value="instructor">Instructor</option>
                <option value="docente">Docente</option>
            </select>
        </div>
        <button type="submit" class="btn btn-sm btn-primary">Agregar</button>
    </form>

    <?php
    render_table(
        ['Username', 'Nombre', 'Rol sistema', 'Rol grupo', 'Email', ''],
        $members,
        function($m) use ($detailId) {
            return "<tr>
                <td><strong>" . htmlspecialchars($m['username']) . "</strong></td>
                <td>" . htmlspecialchars($m['full_name'] ?? '—') . "</td>
                <td>" . render_badge($m['role'], $m['role']) . "</td>
                <td>" . render_badge($m['member_role'], $m['member_role'] === 'student' ? 'estudiante' : $m['member_role']) . "</td>
                <td>" . htmlspecialchars($m['email'] ?? '—') . "</td>
                <td>
                    <form method='POST' style='display:inline'>
                        <input type='hidden' name='action' value='remove_member'>
                        <input type='hidden' name='group_id' value='$detailId'>
                        <input type='hidden' name='user_id' value='{$m['id']}'>
                        <button type='submit' class='btn btn-sm btn-danger' data-confirm='¿Quitar a {$m['username']}?'>Quitar</button>
                    </form>
                </td>
            </tr>";
        }
    );
    render_footer();
    exit;
}

// ─── Lista de grupos ────────────────────────────────
$groups = Database::fetchAll(
    "SELECT g.*, u.username as creator,
            (SELECT COUNT(*) FROM group_members gm WHERE gm.group_id = g.id) as member_count
     FROM student_groups g
     LEFT JOIN users u ON g.created_by = u.id
     ORDER BY g.created_at DESC"
);

render_header('Grupos', 'groups');
?>

<?php if ($message): ?><div class="alert alert-success"><?= htmlspecialchars($message) ?></div><?php endif; ?>
<?php if ($error): ?><div class="alert alert-error"><?= htmlspecialchars($error) ?></div><?php endif; ?>

<div class="toolbar">
    <div></div>
    <button onclick="openModal('modal-create')" class="btn btn-primary">+ Nuevo grupo</button>
</div>

<?php
render_table(
    ['Nombre', 'Institución', 'Creador', 'Miembros', 'Estado', 'Creado', ''],
    $groups,
    function($g) {
        $status = $g['is_active'] ? render_badge('Activo', 'success') : render_badge('Inactivo', 'danger');
        return "<tr>
            <td><a href='groups.php?id={$g['id']}' style='color:var(--accent)'><strong>" . htmlspecialchars($g['name']) . "</strong></a></td>
            <td>" . htmlspecialchars($g['institution'] ?? '—') . "</td>
            <td>" . htmlspecialchars($g['creator'] ?? '—') . "</td>
            <td>{$g['member_count']}</td>
            <td>$status</td>
            <td>" . date('d M Y', strtotime($g['created_at'])) . "</td>
            <td>
                <div style='display:flex;gap:4px;flex-wrap:wrap'>
                <a href='groups.php?id={$g['id']}' class='btn btn-sm btn-outline'>Ver</a>
                <form method='POST' style='display:inline'><input type='hidden' name='action' value='toggle_active'><input type='hidden' name='group_id' value='{$g['id']}'><button class='btn btn-sm btn-outline'>" . ($g['is_active'] ? 'Archivar' : 'Activar') . "</button></form>
                <form method='POST' style='display:inline'><input type='hidden' name='action' value='duplicate'><input type='hidden' name='group_id' value='{$g['id']}'><button class='btn btn-sm btn-outline'>Duplicar</button></form>
                <form method='POST' style='display:inline'><input type='hidden' name='action' value='delete'><input type='hidden' name='group_id' value='{$g['id']}'><button class='btn btn-sm btn-danger' data-confirm='¿Eliminar este grupo y todos sus miembros?'>Eliminar</button></form>
                </div>
            </td>
        </tr>";
    }
);
?>

<div id="modal-create" class="modal-overlay">
    <div class="modal">
        <h3>Nuevo grupo</h3>
        <form method="POST">
            <input type="hidden" name="action" value="create">
            <div class="form-group">
                <label>Nombre *</label>
                <input type="text" name="name" required>
            </div>
            <div class="form-group">
                <label>Descripción</label>
                <textarea name="description"></textarea>
            </div>
            <div class="form-group">
                <label>Institución</label>
                <input type="text" name="institution">
            </div>
            <div class="modal-actions">
                <button type="button" class="btn btn-outline" onclick="closeModal('modal-create')">Cancelar</button>
                <button type="submit" class="btn btn-primary">Crear grupo</button>
            </div>
        </form>
    </div>
</div>

<?php render_footer(); ?>
