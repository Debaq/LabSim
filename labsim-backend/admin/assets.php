<?php
require_once __DIR__ . '/layout.php';
require_once __DIR__ . '/../core/upload.php';
$auth = require_admin();

$message = null;
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';

    if ($action === 'upload') {
        if (!isset($_FILES['file']) || $_FILES['file']['error'] === UPLOAD_ERR_NO_FILE) {
            $error = 'Selecciona un archivo';
        } else {
            $upload = handle_upload('file', 'assets', ALLOWED_ASSET_TYPES);
            Database::execute(
                "INSERT INTO assets (id, name, category, file_path, file_size, mime_type, uploaded_by)
                 VALUES (:id, :name, :cat, :path, :size, :mime, :uid)",
                [
                    ':id' => Database::uuid(),
                    ':name' => $_POST['name'] ?: $upload['original_name'],
                    ':cat' => $_POST['category'] ?: null,
                    ':path' => $upload['path'],
                    ':size' => $upload['size'],
                    ':mime' => $upload['mime'],
                    ':uid' => $auth['sub'],
                ]
            );
            $message = 'Archivo subido';
        }
    }

    if ($action === 'delete') {
        $asset = Database::fetchOne('SELECT id, file_path FROM assets WHERE id = :id', [':id' => $_POST['asset_id'] ?? '']);
        if ($asset) {
            delete_upload($asset['file_path']);
            Database::execute('DELETE FROM assets WHERE id = :id', [':id' => $asset['id']]);
            $message = 'Archivo eliminado';
        }
    }
}

$assets = Database::fetchAll(
    "SELECT a.*, u.username as uploader FROM assets a LEFT JOIN users u ON a.uploaded_by = u.id ORDER BY a.created_at DESC"
);

render_header('Archivos', 'assets');
?>

<?php if ($message): ?><div class="alert alert-success"><?= htmlspecialchars($message) ?></div><?php endif; ?>
<?php if ($error): ?><div class="alert alert-error"><?= htmlspecialchars($error) ?></div><?php endif; ?>

<div class="toolbar">
    <div></div>
    <button onclick="openModal('modal-upload')" class="btn btn-primary">+ Subir archivo</button>
</div>

<?php
function formatSize($bytes) {
    if ($bytes < 1024) return $bytes . ' B';
    if ($bytes < 1048576) return round($bytes / 1024, 1) . ' KB';
    return round($bytes / 1048576, 1) . ' MB';
}

render_table(
    ['Nombre', 'Categoría', 'Tipo', 'Tamaño', 'Subido por', 'Fecha', 'Acciones'],
    $assets,
    function($a) {
        $size = formatSize($a['file_size'] ?? 0);
        return "<tr>
            <td><strong>" . htmlspecialchars($a['name']) . "</strong></td>
            <td>" . htmlspecialchars($a['category'] ?? '—') . "</td>
            <td>" . htmlspecialchars($a['mime_type'] ?? '—') . "</td>
            <td>$size</td>
            <td>" . htmlspecialchars($a['uploader'] ?? '—') . "</td>
            <td>" . date('d M Y', strtotime($a['created_at'])) . "</td>
            <td>
                <a href='../api/index.php?route=assets/{$a['id']}/download' class='btn btn-sm btn-outline'>Descargar</a>
                <form method='POST' style='display:inline'>
                    <input type='hidden' name='action' value='delete'>
                    <input type='hidden' name='asset_id' value='{$a['id']}'>
                    <button class='btn btn-sm btn-danger' data-confirm='¿Eliminar archivo?'>Eliminar</button>
                </form>
            </td>
        </tr>";
    }
);
?>

<div id="modal-upload" class="modal-overlay">
    <div class="modal">
        <h3>Subir archivo</h3>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="action" value="upload">
            <div class="form-group">
                <label>Archivo *</label>
                <input type="file" name="file" required>
            </div>
            <div class="form-row">
                <div class="form-group">
                    <label>Nombre</label>
                    <input type="text" name="name" placeholder="Nombre descriptivo">
                </div>
                <div class="form-group">
                    <label>Categoría</label>
                    <input type="text" name="category" placeholder="material, guia, imagen...">
                </div>
            </div>
            <div class="modal-actions">
                <button type="button" class="btn btn-outline" onclick="closeModal('modal-upload')">Cancelar</button>
                <button type="submit" class="btn btn-primary">Subir</button>
            </div>
        </form>
    </div>
</div>

<?php render_footer(); ?>
