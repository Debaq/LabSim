<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/AppReleases.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Versiones de la app de escritorio publicadas en GitHub, desde la lista que
 * guarda el backend (ver AppReleases). Mirar la página no consulta a GitHub;
 * el botón sí, y deja la lista nueva para los equipos del laboratorio.
 */

$me = Auth::requireFullAdminSession();

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    if ((string) ($_POST['form_action'] ?? '') === 'consultar') {
        $ahora = time();
        $lista = AppReleases::lista(null, null, $ahora, true);
        if ($lista !== null && $lista['consultado'] === $ahora) {
            $success = 'Lista de versiones actualizada desde GitHub.';
            AdminAudit::log($me, 'app_releases_refresh');
        } else {
            $error = 'GitHub no respondió: se muestra la última lista guardada.';
        }
    }
}

$guardada = AppReleases::guardada();
$releases = $guardada['releases'] ?? [];
$prefijo = 'pyinstaller-v';

admin_header('Versiones de la app', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <p>
        <strong>Última consulta a GitHub:</strong>
        <?php if ($guardada !== null): ?>
            <?= htmlspecialchars(date('Y-m-d H:i', $guardada['consultado'])) ?>
        <?php else: ?>
            <span class="muted">nunca</span>
        <?php endif; ?>
    </p>
    <p class="muted">
        Los equipos preguntan al backend si hay una versión nueva, y el backend consulta a GitHub
        cada <?= (int) (AppReleases::TTL / 3600) ?> h, al aplicar el schema o con este botón.
        Una versión recién publicada no llega a los equipos hasta la próxima consulta.
    </p>
    <form method="post" class="inline">
        <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="consultar">
        <button type="submit">Consultar ahora</button>
    </form>
</div>

<div class="card">
    <p class="muted">
        Si a una versión le falta el instalador de Windows, falló el build de Windows (GitHub Actions)
        y los equipos Windows no la reciben.
    </p>
    <div class="table-wrap">
    <table>
        <tr>
            <th>Versión</th><th>Publicada</th>
            <?php foreach (array_keys(AppReleases::ARCHIVOS) as $etiqueta): ?>
            <th><?= htmlspecialchars($etiqueta) ?></th>
            <?php endforeach; ?>
        </tr>
        <?php foreach ($releases as $r): ?>
        <?php
            $tag = (string) $r['tag_name'];
            $ts = strtotime((string) $r['created_at']);
        ?>
        <tr>
            <td>
                <a href="https://github.com/Debaq/LabSim/releases/tag/<?= rawurlencode($tag) ?>" target="_blank" rel="noopener">
                    <?= htmlspecialchars(substr($tag, strlen($prefijo))) ?>
                </a>
            </td>
            <td><?= $ts !== false ? htmlspecialchars(date('Y-m-d H:i', $ts)) : '' ?></td>
            <?php foreach (AppReleases::archivos($r) as $etiqueta => $esta): ?>
            <td>
                <?php if ($esta): ?>
                    <span class="tag tag--success">sí</span>
                <?php elseif ($etiqueta === 'Windows' || $etiqueta === 'Linux'): ?>
                    <span class="tag tag--warn">falta</span>
                <?php else: ?>
                    <span class="tag tag--muted">no</span>
                <?php endif; ?>
            </td>
            <?php endforeach; ?>
        </tr>
        <?php endforeach; ?>
        <?php if (!$releases): ?>
        <tr><td colspan="<?= 2 + count(AppReleases::ARCHIVOS) ?>" class="muted">Sin lista guardada todavía.</td></tr>
        <?php endif; ?>
    </table>
    </div>
</div>
<?php
admin_footer();
