<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';

$me = Auth::requireFullAdminSession();
$pdo = Db::get();

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
<div class="card">
    <p><strong>Base de datos:</strong> conectada (SQLite, WAL) &nbsp;·&nbsp; <strong>PHP:</strong> <?= htmlspecialchars(PHP_VERSION) ?></p>
    <table>
        <?php foreach ($counts as $label => $n): ?>
        <tr><td><?= htmlspecialchars($label) ?></td><td><strong><?= $n ?></strong></td></tr>
        <?php endforeach; ?>
    </table>
</div>
<div class="card">
    <p>Gestión de usuarios (alumnos de prueba, admins) en <a href="users.php">Usuarios</a> -- pincha un alumno para ver sus métricas.</p>
    <p>Agendar, cancelar y eliminar casos/citas en <a href="agenda.php">Fichas Clínicas</a>.</p>
    <p>Registrar Moodle como plataforma LTI y ver las URLs que necesita en <a href="lti.php">LTI</a>.</p>
    <p>Aplicar actualizaciones de schema y gestionar backups en <a href="database.php">Base de datos</a>.</p>
</div>
<?php
admin_footer();
