<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/ReportVersions.php';

/**
 * Versiones anteriores de un informe que otra subida pisó (ver
 * ReportVersions). Se llega desde la ficha del alumno.
 */

$me = Auth::requireAdminSession();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
Db::ensureReportVersioning();

$reportId = (int) ($_GET['report_id'] ?? 0);
$informe = ReportVersions::informe($reportId);
// Docente: solo informes de alumnos de su(s) curso(s), como student.php.
if ($informe && !$isFullAdmin) {
    $roster = Courses::rosterUserIds(Courses::teacherCourseIds((int) $me['id']));
    if (!in_array((int) $informe['student_id'], $roster, true)) {
        $informe = null;
    }
}
if (!$informe) {
    admin_header('Versiones del informe', $me);
    echo '<p class="error">Informe no encontrado.</p>';
    admin_footer();
    exit;
}

$error = null;
$success = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $versionId = (int) ($_POST['version_id'] ?? 0);
    try {
        ReportVersions::restaurar($reportId, $versionId);
        AdminAudit::log($me, 'report_version_restore', ['report_id' => $reportId, 'version_id' => $versionId]);
        $success = 'Versión restaurada. La que estaba quedó en la lista.';
        $informe = ReportVersions::informe($reportId);
    } catch (InvalidArgumentException $e) {
        $error = $e->getMessage();
    }
}

$versiones = ReportVersions::listar($reportId);
$fecha = static function (string $utc): string {
    return Clock::fromUtc($utc)->format('Y-m-d H:i');
};
$rotulo = ReportFile::LABELS[$informe['tipo']] ?? $informe['tipo'];

admin_header('Versiones del informe', $me);
?>
<p><a href="student.php?id=<?= (int) $informe['student_id'] ?>">← Volver al alumno</a></p>
<h2><?= htmlspecialchars($rotulo) ?></h2>
<p class="help">
    Cuando una subida no partía de la última versión guardada (el alumno siguió
    en otro equipo, o retomó sin conexión y el módulo arrancó vacío), la versión
    que se reemplazó queda acá. Restaurar una la vuelve a poner como actual; la
    actual pasa a esta lista. Se restauran los datos (curvas, marcas, conclusión);
    los gráficos del PDF siguen siendo los de la última subida.
</p>
<?php if ($error): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<table>
    <thead>
        <tr><th>Versión</th><th>Guardada</th><th>Reemplazada</th><th>Contenido</th><th></th></tr>
    </thead>
    <tbody>
        <tr>
            <td><?= (int) $informe['version'] ?> (actual)</td>
            <td><?= htmlspecialchars($fecha((string) $informe['updated_at'])) ?></td>
            <td>—</td>
            <td><?= htmlspecialchars(ReportVersions::resumen((string) $informe['data'])) ?></td>
            <td><a href="report_pdf.php?id=<?= (int) $reportId ?>" target="_blank">PDF</a></td>
        </tr>
        <?php foreach ($versiones as $v): ?>
        <tr>
            <td><?= (int) $v['version'] ?></td>
            <td><?= htmlspecialchars($fecha((string) $v['guardado_at'])) ?></td>
            <td><?= htmlspecialchars($fecha((string) $v['reemplazado_at'])) ?></td>
            <td>
                <?= htmlspecialchars(ReportVersions::resumen((string) $v['data'])) ?>
                <details><summary>Datos</summary>
                    <pre><?= htmlspecialchars((string) json_encode(json_decode((string) $v['data'], true), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)) ?></pre>
                </details>
            </td>
            <td>
                <form method="post" onsubmit="return confirm('¿Restaurar esta versión como la actual?');">
                    <?= csrf_field() ?>
                    <input type="hidden" name="version_id" value="<?= (int) $v['id'] ?>">
                    <button type="submit">Restaurar</button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$versiones): ?>
        <tr><td colspan="5" class="muted">No hay versiones reemplazadas.</td></tr>
        <?php endif; ?>
    </tbody>
</table>
<?php
admin_footer();
