<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Backups.php';
require_once __DIR__ . '/_layout.php';

$me = Auth::requireFullAdminSession();
$pdo = Db::get();
$cfg = Db::config();

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

$dbSize = is_file($cfg['db']['path']) ? Backups::formatBytes(filesize($cfg['db']['path'])) : '—';
$backups = Backups::list(); // ya viene ordenado por fecha, ver Backups::list()
$lastBackup = $backups[0] ?? null;

// Módulos PHP que el backend necesita para funcionar completo -- chequeo
// en vivo (no basta con requirements documentados: el PHP del hosting
// puede diferir del de desarrollo, y algunos módulos como GD-con-WebP
// solo se saben con function_exists, no hay paquete "webp" propio que
// extension_loaded reconozca). Cada uno anota QUÉ se rompe si falta.
$modules = [
    ['label' => 'PDO SQLite', 'ok' => extension_loaded('pdo_sqlite'), 'required' => true,
        'detail' => 'Base de datos (Db.php) -- sin esto el backend entero no arranca.'],
    ['label' => 'GD', 'ok' => extension_loaded('gd'), 'required' => true,
        'detail' => 'Foto de paciente e imágenes de otoscopia (PatientPhoto.php, OtoscopiaPhoto.php).'],
    ['label' => 'GD con WebP', 'ok' => function_exists('imagewebp'), 'required' => false,
        'detail' => 'Las imágenes de otoscopia se guardan en WebP (~25-35% más liviano); sin esto caen a JPEG solo.'],
    ['label' => 'EXIF', 'ok' => extension_loaded('exif'), 'required' => false,
        'detail' => 'Corrige la orientación de fotos tomadas con celular antes de guardarlas.'],
    ['label' => 'mbstring', 'ok' => extension_loaded('mbstring'), 'required' => true,
        'detail' => 'Texto multibyte en fichas clínicas (CaseBuilder.php).'],
    ['label' => 'OpenSSL', 'ok' => extension_loaded('openssl'), 'required' => true,
        'detail' => 'Verificación de firma LTI (Jwt.php) -- sin esto el ingreso desde Moodle falla.'],
    ['label' => 'cURL', 'ok' => extension_loaded('curl'), 'required' => true,
        'detail' => 'Llamadas al proveedor LLM para "Hablar con el paciente" (LlmChat.php).'],
];
$modulesMissingRequired = array_filter($modules, static fn($m) => $m['required'] && !$m['ok']);

admin_header('Estado del backend', $me);
?>
<div class="card">
    <p><strong>Base de datos:</strong> conectada (SQLite, WAL) &nbsp;·&nbsp; <strong>PHP:</strong> <?= htmlspecialchars(PHP_VERSION) ?></p>
    <table>
        <tr><td>Tamaño de la base de datos</td><td><strong><?= htmlspecialchars($dbSize) ?></strong></td></tr>
        <tr>
            <td>Último backup</td>
            <td>
                <?php if ($lastBackup): ?>
                <strong><?= htmlspecialchars($lastBackup['created_at']) ?></strong>
                <span style="color:#888;">(<?= htmlspecialchars(Backups::formatBytes($lastBackup['size'])) ?>)</span>
                <?php else: ?>
                <strong style="color:#a33;">Ninguno todavía</strong>
                <?php endif; ?>
            </td>
        </tr>
        <?php foreach ($counts as $label => $n): ?>
        <tr><td><?= htmlspecialchars($label) ?></td><td><strong><?= $n ?></strong></td></tr>
        <?php endforeach; ?>
    </table>
</div>
<div class="card">
    <p><strong>Módulos PHP</strong></p>
    <?php if ($modulesMissingRequired): ?>
    <p style="color:#a33;">Faltan módulos obligatorios -- partes del backend no van a funcionar hasta instalarlos en el servidor.</p>
    <?php endif; ?>
    <table>
        <?php foreach ($modules as $m): ?>
        <tr>
            <td style="white-space:nowrap;">
                <?php if ($m['ok']): ?>
                <span style="color:#2a7a2a;">✓</span>
                <?php elseif ($m['required']): ?>
                <span style="color:#a33; font-weight:700;">✗</span>
                <?php else: ?>
                <span style="color:#c90;">✗</span>
                <?php endif; ?>
                <strong><?= htmlspecialchars($m['label']) ?></strong>
                <?php if (!$m['required']): ?><span style="color:#888; font-size:0.8rem;"> (opcional)</span><?php endif; ?>
            </td>
            <td style="color:#666; font-size:0.85rem;"><?= htmlspecialchars($m['detail']) ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
</div>
<div class="card">
    <p>Gestión de usuarios (alumnos de prueba, admins) en <a href="users.php">Usuarios</a> -- pincha un alumno para ver sus métricas.</p>
    <p>Base de datos de pacientes/casos en <a href="patients.php">Fichas Clínicas</a>; agendar, cancelar y eliminar citas por curso/grupo/alumno en <a href="agenda.php">Agendas</a>.</p>
    <p>Registrar Moodle como plataforma LTI y ver las URLs que necesita en <a href="lti.php">LTI</a>.</p>
    <p>Aplicar actualizaciones de schema y gestionar backups en <a href="database.php">Base de datos</a>.</p>
</div>
<?php
admin_footer();
