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
    // Sin las archivadas, para que este número y el de la biblioteca de
    // fichas (admin/patients.php) digan lo mismo. admin_count() devuelve '—'
    // si la columna todavía no existe, así que no hace falta migrar acá.
    'Casos clínicos' => admin_count($pdo, 'SELECT COUNT(*) FROM cases WHERE archived_at IS NULL'),
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

$reloj = Clock::info($GLOBALS['ZONA_PHP_INI'] ?? null);
try {
    $reloj['base_ahora'] = (string) $pdo->query('SELECT CURRENT_TIMESTAMP')->fetchColumn();
    $relojDesfase = strtotime($reloj['base_ahora'] . ' UTC') - $reloj['epoch'];
    $reloj['base_en_utc'] = abs($relojDesfase) < 120;
} catch (Throwable $e) {
    $reloj['base_ahora'] = null;
    $reloj['base_en_utc'] = null;
}

admin_header('Estado del backend', $me);
?>
<div class="card">
    <p><strong>Reloj</strong></p>
    <p class="help">Las fechas se guardan en UTC y se calculan y muestran en la zona de la
    aplicación, que está declarada en el código (<code>Clock::ZONA</code>) y no depende del
    php.ini del servidor. Acá se puede confirmar eso, y ver en qué zona está el hosting.
    Si el reloj de este computador no coincide, se avisa abajo: las horas de las citas son
    las del curso, no las del que mira, así que no se reinterpretan -- pero un computador
    con la hora corrida hace llegar tarde a su dueño.</p>
    <div class="table-wrap">
    <table>
        <tr>
            <td>Zona de la aplicación</td>
            <td><strong><?= htmlspecialchars($reloj['zona']) ?></strong>
                <span class="muted">UTC<?= sprintf('%+d:%02d', intdiv($reloj['zona_offset_min'], 60), abs($reloj['zona_offset_min']) % 60) ?><?= $reloj['horario_verano'] ? ', horario de verano' : '' ?></span></td>
        </tr>
        <tr>
            <td>Hora del servidor</td>
            <td><strong><?= htmlspecialchars($reloj['local']) ?></strong>
                <span class="muted">(<?= htmlspecialchars($reloj['utc']) ?> UTC)</span></td>
        </tr>
        <tr>
            <td>Zona que trae el servidor (php.ini)</td>
            <td>
                <strong><?= htmlspecialchars($reloj['php_ini']) ?></strong>
                <?php if ($reloj['php_ini_coincide']): ?>
                <span style="color:var(--color-success-text);">✓ igual a la de la aplicación</span>
                <?php else: ?>
                <span class="muted">distinta de la de la aplicación, y no importa: la fija
                <code>bootstrap.php</code> en cada request</span>
                <?php endif; ?>
            </td>
        </tr>
        <tr>
            <td>La base guarda en</td>
            <td>
                <?php if ($reloj['base_en_utc'] === true): ?>
                <strong>UTC</strong> <span style="color:var(--color-success-text);">✓</span>
                <?php elseif ($reloj['base_en_utc'] === false): ?>
                <strong style="color:var(--color-danger);">NO está en UTC</strong>
                <span class="muted">dice <?= htmlspecialchars((string) $reloj['base_ahora']) ?>;
                todas las conversiones de fecha quedan corridas</span>
                <?php else: ?>
                <span class="muted">—</span>
                <?php endif; ?>
            </td>
        </tr>
        <tr>
            <td>Reloj de este computador</td>
            <td id="reloj-cliente" data-epoch="<?= (int) $reloj['epoch'] ?>"><span class="muted">comprobando…</span></td>
        </tr>
    </table>
    </div>
</div>
<script>
// Comparación contra el reloj del que mira. No ajusta nada: informa.
(function () {
    var celda = document.getElementById('reloj-cliente');
    if (!celda) { return; }
    var servidor = parseInt(celda.getAttribute('data-epoch'), 10) * 1000;
    var zona = '—';
    try { zona = Intl.DateTimeFormat().resolvedOptions().timeZone || '—'; } catch (e) {}
    var desfase = Math.round((Date.now() - servidor) / 1000);
    var texto = '<strong>' + zona + '</strong>';
    if (Math.abs(desfase) <= 120) {
        texto += ' <span style="color:var(--color-success-text);">\u2713 en hora</span>';
    } else {
        var minutos = Math.round(Math.abs(desfase) / 60);
        texto += ' <strong style="color:var(--color-danger);">' + minutos + ' min ' +
                 (desfase > 0 ? 'adelantado' : 'atrasado') + '</strong>' +
                 ' <span class="muted">respecto del servidor</span>';
    }
    celda.innerHTML = texto;
})();
</script>
<div class="card">
    <p><strong>Base de datos:</strong> conectada (SQLite, WAL) &nbsp;·&nbsp; <strong>PHP:</strong> <?= htmlspecialchars(PHP_VERSION) ?></p>
    <div class="table-wrap">
    <table>
        <tr><td>Tamaño de la base de datos</td><td><strong><?= htmlspecialchars($dbSize) ?></strong></td></tr>
        <tr>
            <td>Último backup</td>
            <td>
                <?php if ($lastBackup): ?>
                <strong><?= htmlspecialchars($lastBackup['created_at']) ?></strong>
                <span class="muted">(<?= htmlspecialchars(Backups::formatBytes($lastBackup['size'])) ?>)</span>
                <?php else: ?>
                <strong style="color:var(--color-danger);">Ninguno todavía</strong>
                <?php endif; ?>
            </td>
        </tr>
        <?php foreach ($counts as $label => $n): ?>
        <tr><td><?= htmlspecialchars($label) ?></td><td><strong><?= $n ?></strong></td></tr>
        <?php endforeach; ?>
    </table>
    </div>
</div>
<div class="card">
    <p><strong>Módulos PHP</strong></p>
    <?php if ($modulesMissingRequired): ?>
    <p style="color:var(--color-danger);">Faltan módulos obligatorios -- partes del backend no van a funcionar hasta instalarlos en el servidor.</p>
    <?php endif; ?>
    <div class="table-wrap">
    <table>
        <?php foreach ($modules as $m): ?>
        <tr>
            <td class="nowrap">
                <?php if ($m['ok']): ?>
                <span style="color:var(--color-success-text);">✓</span>
                <?php elseif ($m['required']): ?>
                <span style="color:var(--color-danger); font-weight:700;">✗</span>
                <?php else: ?>
                <span style="color:var(--color-warn-text);">✗</span>
                <?php endif; ?>
                <strong><?= htmlspecialchars($m['label']) ?></strong>
                <?php if (!$m['required']): ?><span style="color:var(--color-muted); font-size:0.8rem;"> (opcional)</span><?php endif; ?>
            </td>
            <td style="color:var(--color-muted); font-size:0.85rem;"><?= htmlspecialchars($m['detail']) ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
</div>
<div class="card">
    <p>Gestión de usuarios (alumnos de prueba, admins) en <a href="users.php">Usuarios</a> -- pincha un alumno para ver sus métricas.</p>
    <p>Base de datos de pacientes/casos en <a href="patients.php">Fichas Clínicas</a>; agendar, cancelar y eliminar citas por curso/grupo/alumno en <a href="agenda.php">Agendas</a>.</p>
    <p>Registrar Moodle como plataforma LTI y ver las URLs que necesita en <a href="lti.php">LTI</a>.</p>
    <p>Aplicar actualizaciones de schema y gestionar backups en <a href="database.php">Base de datos</a>.</p>
</div>
<?php
admin_footer();
