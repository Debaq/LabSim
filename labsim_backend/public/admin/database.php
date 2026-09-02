<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Backups.php';
require_once __DIR__ . '/_layout.php';

/**
 * Todo lo que toca el archivo .sqlite en un solo lugar: aplicar
 * actualizaciones de schema y backups/restaurar. Antes había un botón
 * "Aplicar schema.sql" acá y OTRO en Estado (admin/index.php) haciendo
 * exactamente lo mismo -- confuso y quedaba fácil desincronizarlos (pasó:
 * uno de los dos no tenía la migración de cursos). Ahora Estado es solo
 * lectura y este es el único lugar que escribe sobre el schema/la base.
 * Todo admin completo -- un backup contiene TODO (alumnos, atenciones,
 * notas), y restaurar reemplaza la base viva entera.
 */

$me = Auth::requireFullAdminSession();
$pdo = Db::get();

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = (string) ($_POST['form_action'] ?? '');
    $filename = (string) ($_POST['filename'] ?? '');

    try {
        if ($action === 'apply_schema') {
            Db::migrateLtiPlatformsIfNeeded();
            Db::migrateLtiReplayColumnsIfNeeded();
            $sql = file_get_contents(__DIR__ . '/../../sql/schema.sql');
            $pdo->exec($sql);
            // Después del exec: agrega columnas nuevas a tablas que ya
            // existían de antes (CREATE TABLE IF NOT EXISTS no las toca).
            Db::migrateCoursesIfNeeded();
            $success = 'Schema aplicado correctamente.';
        } elseif ($action === 'create') {
            $created = Backups::create();
            $success = "Backup creado: {$created}.";
        } elseif ($action === 'delete') {
            Backups::delete($filename);
            $success = 'Backup eliminado.';
        } elseif ($action === 'restore') {
            // Confirmación escrita a mano (no solo un confirm() de JS) --
            // restaurar reemplaza TODA la base viva, es la acción más
            // destructiva de todo el panel admin.
            $confirmText = trim((string) ($_POST['confirm_filename'] ?? ''));
            if ($confirmText !== $filename) {
                $error = 'El nombre escrito no coincide -- no se restauró nada.';
            } else {
                $safetyBackup = Backups::restore($filename);
                $success = "Base restaurada desde {$filename}. Se guardó el estado anterior como {$safetyBackup} por si esto fue un error.";
            }
        }
    } catch (Throwable $e) {
        $error = $e->getMessage();
    }
}

$backups = Backups::list();

admin_header('Base de datos', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <strong>Actualizar schema</strong>
    <p style="font-size:0.85rem; color:#555;">
        Idempotente (CREATE TABLE/INDEX IF NOT EXISTS) -- correrlo de nuevo no borra datos.
        Úsalo después de subir cambios al schema. Único lugar del panel que aplica esto.
    </p>
    <form method="post">
        <input type="hidden" name="form_action" value="apply_schema">
        <button type="submit">Aplicar schema.sql</button>
    </form>
</div>

<div class="card">
    <strong>Crear backup ahora</strong>
    <p style="font-size:0.85rem; color:#555;">
        Copia completa de la base (alumnos, cursos, casos, citas, atenciones, logs) al momento de pinchar el botón.
        No hay backups automáticos programados -- este panel es manual, guárdalos con la frecuencia que necesites.
    </p>
    <form method="post">
        <input type="hidden" name="form_action" value="create">
        <button type="submit">Crear backup</button>
    </form>
</div>

<div class="card">
    <strong>Backups guardados (<?= count($backups) ?>)</strong>
    <p style="font-size:0.85rem; color:#555;">
        Viven en <code>data/backups/</code> en el servidor (fuera de la carpeta pública, no accesibles por URL directa).
        Para tener una copia fuera del servidor, descárgalos a tu computador de vez en cuando -- si el hosting completo
        se pierde, los backups que solo viven ahí mismo no sirven de nada.
    </p>
    <table>
        <tr><th>Fecha</th><th>Archivo</th><th>Tamaño</th><th></th></tr>
        <?php foreach ($backups as $b): ?>
        <tr>
            <td><?= htmlspecialchars($b['created_at']) ?></td>
            <td class="mono" style="font-size:0.8rem;"><?= htmlspecialchars($b['filename']) ?></td>
            <td><?= htmlspecialchars(Backups::formatBytes($b['size'])) ?></td>
            <td style="white-space:nowrap;">
                <a href="backup_download.php?file=<?= urlencode($b['filename']) ?>" style="font-size:0.8rem;">Descargar</a>
                &nbsp;·&nbsp;
                <button type="button" class="secondary" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;"
                    onclick="openRestore('<?= htmlspecialchars($b['filename'], ENT_QUOTES) ?>')">Restaurar</button>
                &nbsp;·&nbsp;
                <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Eliminar el backup ' . $b['filename'] . '? No se puede deshacer.'), ENT_QUOTES) ?>);">
                    <input type="hidden" name="form_action" value="delete">
                    <input type="hidden" name="filename" value="<?= htmlspecialchars($b['filename']) ?>">
                    <button type="submit" class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Eliminar</button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$backups): ?>
        <tr><td colspan="4" style="color:#888;">Ningún backup creado todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>

<div id="restore-modal" style="display:none; position:fixed; inset:0; background:rgba(0,0,0,0.5); align-items:center; justify-content:center; z-index:10;">
    <div class="card" style="max-width:480px;">
        <strong style="color:#a33;">Restaurar backup</strong>
        <p style="font-size:0.85rem;">
            Vas a restaurar <strong id="restore-filename-label"></strong>. Esto reemplaza <strong>toda</strong> la
            base de datos viva (alumnos, cursos, citas, atenciones, logs -- todo lo que se haya cargado después
            de ese backup se pierde). Se guarda automáticamente un backup del estado actual antes de restaurar,
            así que esto mismo se puede deshacer si fue un error.
        </p>
        <form method="post">
            <input type="hidden" name="form_action" value="restore">
            <input type="hidden" name="filename" id="restore-filename-input">
            <label>Escribe el nombre exacto del archivo para confirmar
                <input type="text" name="confirm_filename" id="restore-confirm-input" required autocomplete="off">
            </label>
            <button type="button" class="secondary" onclick="closeRestore()">Cancelar</button>
            <button type="submit" class="danger">Restaurar (reemplaza todo)</button>
        </form>
    </div>
</div>
<script>
    function openRestore(filename) {
        document.getElementById('restore-filename-label').textContent = filename;
        document.getElementById('restore-filename-input').value = filename;
        document.getElementById('restore-confirm-input').value = '';
        document.getElementById('restore-modal').style.display = 'flex';
    }
    function closeRestore() {
        document.getElementById('restore-modal').style.display = 'none';
    }
</script>
<?php
admin_footer();
