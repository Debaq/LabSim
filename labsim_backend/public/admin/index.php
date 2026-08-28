<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';

$me = Auth::requireAdminSession();
$pdo = Db::get();

$migrateMessage = null;
$migrateError = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['form_action'] ?? '') === 'migrate') {
    try {
        Db::migrateLtiPlatformsIfNeeded();
        Db::migrateLtiReplayColumnsIfNeeded();
        $sql = file_get_contents(__DIR__ . '/../../sql/schema.sql');
        $pdo->exec($sql);
        $migrateMessage = 'Schema aplicado correctamente.';
    } catch (Throwable $e) {
        $migrateError = 'Error aplicando schema: ' . $e->getMessage();
    }
}

function admin_count(PDO $pdo, string $sql): string
{
    // Antes de aplicar schema.sql (primera vez, o tras un cambio de schema)
    // algunas tablas pueden no existir todavía -- no debe tumbar la página
    // que justamente sirve para aplicarlo.
    try {
        return (string) $pdo->query($sql)->fetchColumn();
    } catch (PDOException $e) {
        return '—';
    }
}

$counts = [
    'Alumnos' => admin_count($pdo, "SELECT COUNT(*) FROM users WHERE role='student'"),
    'Admins' => admin_count($pdo, "SELECT COUNT(*) FROM users WHERE role='admin'"),
    'Casos clínicos' => admin_count($pdo, 'SELECT COUNT(*) FROM cases'),
    'Citas de agenda' => admin_count($pdo, 'SELECT COUNT(*) FROM appointments'),
    'Atenciones registradas' => admin_count($pdo, 'SELECT COUNT(*) FROM attendances'),
    'Plataformas LTI registradas' => admin_count($pdo, 'SELECT COUNT(*) FROM lti_platforms'),
    'Tokens de sesión activos' => admin_count($pdo, 'SELECT COUNT(*) FROM tokens'),
];

admin_header('Estado del backend', $me);
?>
<?php if ($migrateMessage !== null): ?><p class="success"><?= htmlspecialchars($migrateMessage) ?></p><?php endif; ?>
<?php if ($migrateError !== null): ?><p class="error"><?= htmlspecialchars($migrateError) ?></p><?php endif; ?>
<div class="card">
    <p><strong>Base de datos:</strong> conectada (SQLite, WAL) &nbsp;·&nbsp; <strong>PHP:</strong> <?= htmlspecialchars(PHP_VERSION) ?></p>
    <table>
        <?php foreach ($counts as $label => $n): ?>
        <tr><td><?= htmlspecialchars($label) ?></td><td><strong><?= $n ?></strong></td></tr>
        <?php endforeach; ?>
    </table>
</div>
<div class="card">
    <strong>Aplicar schema.sql</strong>
    <p style="font-size:0.85rem; color:#555;">
        Idempotente (CREATE TABLE/INDEX IF NOT EXISTS) -- correrlo de nuevo no borra datos.
        Úsalo después de subir cambios al schema.
    </p>
    <form method="post">
        <input type="hidden" name="form_action" value="migrate">
        <button type="submit">Aplicar schema.sql</button>
    </form>
</div>
<div class="card">
    <p>Gestión de usuarios (alumnos de prueba, admins) en <a href="users.php">Usuarios</a> -- pincha un alumno para ver sus métricas.</p>
    <p>Agendar, cancelar y eliminar casos/citas en <a href="agenda.php">Agenda</a>.</p>
    <p>Registrar Moodle como plataforma LTI y ver las URLs que necesita en <a href="lti.php">LTI</a>.</p>
</div>
<?php
admin_footer();
