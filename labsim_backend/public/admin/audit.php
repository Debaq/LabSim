<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';

/**
 * Solo lectura: quién hizo qué desde el panel admin (crear/borrar usuario,
 * restaurar backup, eliminar caso...). Ver src/AdminAudit.php -- cada acción
 * mutante del panel escribe acá. Sin paginación real todavía -- alcanza con
 * las últimas 300 mientras el volumen de acciones admin sea bajo.
 */

$me = Auth::requireFullAdminSession();
$pdo = Db::get();

$rows = [];
try {
    $rows = $pdo->query('SELECT * FROM admin_audit_log ORDER BY id DESC LIMIT 300')->fetchAll();
} catch (PDOException $e) {
    // Tabla nueva -- puede no existir todavía si no se ha aplicado schema.sql.
}

admin_header('Auditoría', $me);
?>
<div class="card">
    <p style="font-size:0.85rem; color:#555;">
        Últimas <?= count($rows) ?> acciones de administración registradas (más reciente primero).
        Si esta tabla está vacía y ya hay actividad, ve a <a href="database.php">Base de datos</a> y aplica schema.sql.
    </p>
    <table>
        <tr><th>Fecha</th><th>Admin</th><th>Acción</th><th>Detalles</th></tr>
        <?php foreach ($rows as $r): ?>
        <tr>
            <td class="mono" style="font-size:0.8rem; white-space:nowrap;"><?= htmlspecialchars($r['created_at']) ?></td>
            <td><?= htmlspecialchars($r['admin_username']) ?></td>
            <td><?= htmlspecialchars($r['action']) ?></td>
            <td class="mono" style="font-size:0.78rem;"><?= htmlspecialchars($r['details'] ?? '') ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$rows): ?>
        <tr><td colspan="4" style="color:#888;">Sin acciones registradas todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>
<?php
admin_footer();
