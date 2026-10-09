<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/Consola.php';
require_once __DIR__ . '/_layout.php';

/**
 * Tokens de la consola remota (ver src/Consola.php): se genera uno por
 * sesión de trabajo, se le pasa a Claude y vence solo. Da SQL libre sobre la
 * base viva, escritura incluida -- por eso solo admin completo.
 */

$me = Auth::requireFullAdminSession();

$error = null;
$success = null;
$nuevoToken = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $action = (string) ($_POST['form_action'] ?? '');
    try {
        if ($action === 'crear') {
            $horas = Consola::normalizarHoras((int) ($_POST['horas'] ?? 4));
            $etiqueta = (string) ($_POST['etiqueta'] ?? '');
            $nuevoToken = Consola::crearToken($me, $horas, $etiqueta);
            AdminAudit::log($me, 'consola_token_crear', ['horas' => $horas, 'etiqueta' => $etiqueta]);
        } elseif ($action === 'revocar') {
            $id = (int) ($_POST['id'] ?? 0);
            Consola::revocar($id);
            $success = 'Token revocado.';
            AdminAudit::log($me, 'consola_token_revocar', ['id' => $id]);
        }
    } catch (PDOException $e) {
        $error = 'No se pudo: ' . $e->getMessage() . ' -- si falta la tabla, aplica schema.sql en Base de datos.';
    }
}

$tokens = [];
$consultas = [];
$sinTabla = false;
try {
    $tokens = Consola::listarTokens();
    $consultas = Consola::ultimasConsultas(100);
} catch (PDOException $e) {
    $sinTabla = true;
}

$https = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
    || ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '') === 'https';
$urlApi = ($https ? 'https' : 'http') . '://' . ($_SERVER['HTTP_HOST'] ?? 'localhost')
    . rtrim(dirname(dirname($_SERVER['SCRIPT_NAME'] ?? '/public/admin/consola.php')), '/') . '/api/consola.php';

admin_header('Consola remota', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>
<?php if ($sinTabla): ?>
<p class="error">Faltan las tablas de la consola: ve a <a href="database.php">Base de datos</a> y aplica schema.sql.</p>
<?php endif; ?>

<?php if ($nuevoToken !== null): ?>
<div class="card">
    <h3>Token nuevo</h3>
    <p class="muted">Se muestra solo esta vez. Pégale a Claude el bloque completo:</p>
    <pre id="consola-pegar" class="mono" style="white-space:pre-wrap; word-break:break-all;">LABSIM_CONSOLA_URL=<?= htmlspecialchars($urlApi) ?>

LABSIM_CONSOLA_TOKEN=<?= htmlspecialchars($nuevoToken) ?></pre>
    <button type="button" onclick="copiarConsola()">Copiar</button>
    <span id="copiado" class="muted" hidden>Copiado</span>
</div>
<?php endif; ?>

<div class="card">
    <p class="muted">
        Un token da <strong>SQL libre sobre la base viva</strong> (leer, modificar, borrar), lectura de
        los archivos de <code>data/</code> y backups, sin tu contraseña. Vence solo a las horas elegidas;
        revócalo apenas termines. Todo lo que se ejecuta queda abajo en el registro.
    </p>
    <form method="post">
        <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="crear">
        <label>Para qué
            <input type="text" name="etiqueta" maxlength="80" placeholder="ej. revisar informes que no suben">
        </label>
        <label>Dura
            <select name="horas">
                <?php foreach (Consola::DURACIONES as $h): ?>
                <option value="<?= $h ?>"<?= $h === 4 ? ' selected' : '' ?>><?= $h ?> h</option>
                <?php endforeach; ?>
            </select>
        </label>
        <button type="submit">Generar token</button>
    </form>
</div>

<div class="card">
    <h3>Tokens</h3>
    <div class="table-wrap">
    <table>
        <tr><th>Para qué</th><th>Creado (UTC)</th><th>Vence (UTC)</th><th>Último uso (UTC)</th><th>Usos</th><th>Estado</th><th></th></tr>
        <?php foreach ($tokens as $t): ?>
        <tr>
            <td><?= htmlspecialchars($t['etiqueta'] !== '' ? $t['etiqueta'] : '—') ?>
                <span class="muted">(<?= htmlspecialchars($t['created_by_username']) ?>)</span></td>
            <td class="mono nowrap" style="font-size:0.8rem;"><?= htmlspecialchars($t['created_at']) ?></td>
            <td class="mono nowrap" style="font-size:0.8rem;"><?= htmlspecialchars($t['expires_at']) ?></td>
            <td class="mono nowrap" style="font-size:0.8rem;"><?= htmlspecialchars($t['last_used_at'] ?? '—') ?></td>
            <td><?= (int) $t['usos'] ?></td>
            <td><?= $t['revoked_at'] !== null ? 'Revocado' : ((int) $t['vigente'] ? '<strong>Vigente</strong>' : 'Vencido') ?></td>
            <td>
                <?php if ((int) $t['vigente']): ?>
                <form method="post" class="inline">
                    <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="revocar">
                    <input type="hidden" name="id" value="<?= (int) $t['id'] ?>">
                    <button type="submit" class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Revocar</button>
                </form>
                <?php endif; ?>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$tokens): ?>
        <tr><td colspan="7" class="muted">Ningún token generado.</td></tr>
        <?php endif; ?>
    </table>
    </div>
</div>

<div class="card">
    <h3>Registro</h3>
    <p class="muted">Últimas <?= count($consultas) ?> llamadas, la más reciente primero.</p>
    <div class="table-wrap">
    <table>
        <tr><th>Fecha (UTC)</th><th>Token</th><th>Tipo</th><th>Consulta</th><th>Filas</th><th>Cambios</th><th>ms</th><th>Error</th></tr>
        <?php foreach ($consultas as $q): ?>
        <tr>
            <td class="mono nowrap" style="font-size:0.8rem;"><?= htmlspecialchars($q['created_at']) ?></td>
            <td><?= htmlspecialchars((string) ($q['etiqueta'] ?? '')) ?: '#' . (int) $q['token_id'] ?></td>
            <td><?= htmlspecialchars($q['tipo']) ?></td>
            <td class="mono" style="font-size:0.78rem; white-space:pre-wrap; max-width:40rem;"><?= htmlspecialchars(mb_substr($q['texto'], 0, 600)) ?></td>
            <td><?= $q['filas'] !== null ? (int) $q['filas'] : '' ?></td>
            <td><?= $q['cambios'] !== null ? (int) $q['cambios'] : '' ?></td>
            <td><?= $q['ms'] !== null ? (int) $q['ms'] : '' ?></td>
            <td class="mono" style="font-size:0.78rem;"><?= htmlspecialchars((string) ($q['error'] ?? '')) ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$consultas): ?>
        <tr><td colspan="8" class="muted">Sin llamadas todavía.</td></tr>
        <?php endif; ?>
    </table>
    </div>
</div>

<script>
function copiarConsola() {
    var texto = document.getElementById('consola-pegar').textContent;
    var aviso = document.getElementById('copiado');
    function avisar() { aviso.hidden = false; setTimeout(function () { aviso.hidden = true; }, 1500); }
    if (navigator.clipboard) {
        navigator.clipboard.writeText(texto).then(avisar);
        return;
    }
    var rango = document.createRange();
    rango.selectNode(document.getElementById('consola-pegar'));
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(rango);
}
</script>
<?php
admin_footer();
