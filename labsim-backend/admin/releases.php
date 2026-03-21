<?php
require_once __DIR__ . '/layout.php';
require_once __DIR__ . '/../core/upload.php';
$auth = require_admin();

$message = null;
$error = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';

    if ($action === 'create') {
        $version = $_POST['version'] ?? '';
        if (!$version) {
            $error = 'Versión requerida';
        } else {
            $existing = Database::fetchOne('SELECT id FROM app_releases WHERE version = :v', [':v' => $version]);
            if ($existing) {
                $error = 'Ya existe esta versión';
            } else {
                $urls = [];
                foreach (['linux', 'windows', 'macos'] as $platform) {
                    $field = "file_$platform";
                    if (isset($_FILES[$field]) && $_FILES[$field]['error'] === UPLOAD_ERR_OK) {
                        $upload = handle_upload($field, 'releases', ALLOWED_RELEASE_TYPES);
                        $urls[$platform] = $upload['path'];
                    }
                }

                Database::execute("UPDATE app_releases SET is_latest = 0");

                Database::execute(
                    "INSERT INTO app_releases (id, version, release_notes, download_url_linux, download_url_windows, download_url_macos, is_latest, is_mandatory)
                     VALUES (:id, :v, :notes, :linux, :win, :mac, 1, :mand)",
                    [
                        ':id' => Database::uuid(), ':v' => $version,
                        ':notes' => $_POST['release_notes'] ?: null,
                        ':linux' => $urls['linux'] ?? $_POST['url_linux'] ?? null,
                        ':win' => $urls['windows'] ?? $_POST['url_windows'] ?? null,
                        ':mac' => $urls['macos'] ?? $_POST['url_macos'] ?? null,
                        ':mand' => isset($_POST['is_mandatory']) ? 1 : 0,
                    ]
                );
                $message = "Release $version creada";
            }
        }
    }
}

$releases = Database::fetchAll("SELECT * FROM app_releases ORDER BY published_at DESC");

render_header('Releases', 'releases');
?>

<?php if ($message): ?><div class="alert alert-success"><?= htmlspecialchars($message) ?></div><?php endif; ?>
<?php if ($error): ?><div class="alert alert-error"><?= htmlspecialchars($error) ?></div><?php endif; ?>

<div class="toolbar">
    <div></div>
    <button onclick="openModal('modal-release')" class="btn btn-primary">+ Nueva release</button>
</div>

<?php
render_table(
    ['Versión', 'Notas', 'Linux', 'Windows', 'macOS', 'Latest', 'Obligatoria', 'Fecha'],
    $releases,
    function($r) {
        $latest = $r['is_latest'] ? render_badge('Latest', 'success') : '';
        $mandatory = $r['is_mandatory'] ? render_badge('Sí', 'danger') : render_badge('No', 'default');
        $linux = $r['download_url_linux'] ? render_badge('Sí', 'success') : '—';
        $win = $r['download_url_windows'] ? render_badge('Sí', 'success') : '—';
        $mac = $r['download_url_macos'] ? render_badge('Sí', 'success') : '—';

        return "<tr>
            <td><strong>" . htmlspecialchars($r['version']) . "</strong> $latest</td>
            <td style='max-width:300px'>" . htmlspecialchars(mb_substr($r['release_notes'] ?? '', 0, 100)) . "</td>
            <td>$linux</td><td>$win</td><td>$mac</td>
            <td>$latest</td><td>$mandatory</td>
            <td>" . date('d M Y', strtotime($r['published_at'])) . "</td>
        </tr>";
    }
);
?>

<div id="modal-release" class="modal-overlay">
    <div class="modal">
        <h3>Nueva release</h3>
        <form method="POST" enctype="multipart/form-data">
            <input type="hidden" name="action" value="create">
            <div class="form-group">
                <label>Versión *</label>
                <input type="text" name="version" required placeholder="3.1.0">
            </div>
            <div class="form-group">
                <label>Notas de release</label>
                <textarea name="release_notes" rows="4"></textarea>
            </div>
            <div class="form-group">
                <label>Binario Linux</label>
                <input type="file" name="file_linux">
                <input type="text" name="url_linux" placeholder="O URL directa" style="margin-top:5px">
            </div>
            <div class="form-group">
                <label>Binario Windows</label>
                <input type="file" name="file_windows">
                <input type="text" name="url_windows" placeholder="O URL directa" style="margin-top:5px">
            </div>
            <div class="form-group">
                <label>Binario macOS</label>
                <input type="file" name="file_macos">
                <input type="text" name="url_macos" placeholder="O URL directa" style="margin-top:5px">
            </div>
            <div class="form-group">
                <label><input type="checkbox" name="is_mandatory"> Actualización obligatoria</label>
            </div>
            <div class="modal-actions">
                <button type="button" class="btn btn-outline" onclick="closeModal('modal-release')">Cancelar</button>
                <button type="submit" class="btn btn-primary">Crear release</button>
            </div>
        </form>
    </div>
</div>

<?php render_footer(); ?>
