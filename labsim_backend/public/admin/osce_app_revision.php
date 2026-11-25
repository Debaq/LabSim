<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/OsceApp.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Revisión de una estación del OSCE que se rinde en la app (configuración
 * del equipo o marcaje): criterio por criterio, lo que dejó el alumno, lo
 * esperado y el puntaje automático, que el docente puede ajustar (queda como
 * suyo y "Volver a corregir" ya no lo pisa). Con la pauta cambiada, "Volver a
 * corregir" recalcula todas las entregas desde lo que la app mandó.
 */

$me = Auth::requireAdminSession();
$estId = (int) ($_GET['estacion'] ?? $_POST['estacion'] ?? 0);
$est = Osce::estacion($estId);
$osce = $est !== null ? Osce::obtener((int) $est['osce_id']) : null;
if ($osce === null || !Courses::canAdminister((int) $osce['course_id'], $me) || !OsceApp::esApp((string) $est['tipo'])) {
    http_response_code(404);
    exit('Estación no encontrada.');
}

$error = null;
$success = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $accion = (string) ($_POST['accion'] ?? '');
    try {
        if ($accion === 'guardar') {
            $pid = (int) ($_POST['participante'] ?? 0);
            OsceApp::guardarRevision($estId, $pid, (array) ($_POST['it'] ?? []), (string) ($_POST['feedback'] ?? ''));
            AdminAudit::log($me, 'osce_app_revision', ['estacion_id' => $estId, 'participante_id' => $pid]);
            header('Location: osce_app_revision.php?estacion=' . $estId . '&ok=' . $pid . '#p' . $pid);
            exit;
        }
        if ($accion === 'recorregir') {
            $n = 0;
            foreach (Osce::participantes((int) $osce['id']) as $p) {
                if (OsceApp::registro($estId, (int) $p['id']) !== null) {
                    OsceApp::corregir($estId, (int) $p['id']);
                    $n++;
                }
            }
            AdminAudit::log($me, 'osce_app_recorregir', ['estacion_id' => $estId]);
            $success = "{$n} entregas corregidas de nuevo con los criterios actuales (lo ajustado a mano se mantiene).";
        }
    } catch (InvalidArgumentException $e) {
        $error = $e->getMessage();
    }
}
if (isset($_GET['ok'])) {
    $success = 'Revisión guardada.';
}

$entregas = [];
foreach (Osce::participantes((int) $osce['id']) as $p) {
    $reg = OsceApp::registro($estId, (int) $p['id']);
    if ($reg === null) {
        continue;
    }
    $stmt = Db::get()->prepare('SELECT * FROM osce_entrega WHERE estacion_id = ? AND participante_id = ?');
    $stmt->execute([$estId, (int) $p['id']]);
    $en = $stmt->fetch();
    $stmt->closeCursor();
    $entregas[] = ['p' => $p, 'entrega' => $en, 'registro' => $reg, 'detalle' => OsceApp::detalle($estId, (int) $p['id'])];
}
$fmt = static fn ($x): string => $x === null ? '' : rtrim(rtrim(number_format((float) $x, 2, ',', ''), '0'), ',');

admin_header('Revisión · ' . $est['titulo'], $me);
?>
<style>
.ok { color: #15803d; font-weight: 600; } .mal { color: #b91c1c; font-weight: 600; }
.rev td { vertical-align: top; }
.rev textarea { width: 100%; min-height: 2.2rem; }
details.rev-alumno > summary { cursor: pointer; padding: 0.4rem 0; font-size: 1.05rem; }
</style>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="row row--between row--center" style="margin-bottom:1rem;">
    <a href="osce_estacion.php?id=<?= $estId ?>">← Contenido de la estación</a>
    <span class="muted"><?= htmlspecialchars($osce['nombre']) ?></span>
</div>

<div class="card">
    <p><strong><?= count($entregas) ?></strong> entregas desde la app.</p>
    <form method="post">
        <?= csrf_field() ?>
        <input type="hidden" name="estacion" value="<?= $estId ?>">
        <button type="submit" name="accion" value="recorregir" class="btn btn--sm btn--secondary">Volver a corregir todas con los criterios actuales</button>
    </form>
</div>

<?php if (!$entregas): ?><p class="empty-state">Todavía nadie entregó en esta estación.</p><?php endif; ?>

<?php foreach ($entregas as $e): $p = $e['p']; $en = $e['entrega']; $pid = (int) $p['id']; ?>
<div class="card" id="p<?= $pid ?>">
<details class="rev-alumno"<?= isset($_GET['ok']) && (int) $_GET['ok'] === $pid ? ' open' : '' ?>>
    <summary>
        <strong class="mono"><?= htmlspecialchars($p['codigo']) ?></strong>
        <span class="muted"><?= htmlspecialchars((string) $p['display_name']) ?></span> ·
        <?= $fmt($en['puntaje']) ?> / <?= $fmt($en['puntaje_max']) ?> pt
        <?= (int) $en['critico_fallado'] ? '<span class="tag tag--danger">crítico</span>' : '' ?>
    </summary>
    <form method="post">
        <?= csrf_field() ?>
        <input type="hidden" name="estacion" value="<?= $estId ?>">
        <input type="hidden" name="participante" value="<?= $pid ?>">
        <input type="hidden" name="accion" value="guardar">
        <div class="table-wrap"><table class="rev">
            <thead><tr><th>Criterio</th><th>Alumno</th><th>Esperado</th><th>Puntaje</th><th>Comentario</th></tr></thead>
            <tbody>
            <?php foreach ($e['detalle'] as $d): $it = $d['item']; $r = $d['resultado']; $ev = $d['eval'] ?? []; ?>
                <tr>
                    <td><?= htmlspecialchars($it['texto']) ?><?= (int) $it['critico'] ? ' <span class="tag tag--danger">crítico</span>' : '' ?></td>
                    <td class="<?= !empty($ev['ok']) ? 'ok' : 'mal' ?>"><?= htmlspecialchars((string) ($ev['alumno'] ?? '—')) ?></td>
                    <td><?= htmlspecialchars((string) ($ev['esperado'] ?? '—')) ?></td>
                    <td class="nowrap"><input type="text" inputmode="decimal" name="it[<?= (int) $it['id'] ?>][puntaje]" value="<?= $fmt($r['puntaje'] ?? null) ?>" class="input--narrow">
                        <span class="help help--xs">/ <?= $fmt($it['puntaje']) ?><?= ($r['fuente'] ?? '') === 'docente' ? ' · tuyo' : '' ?></span></td>
                    <td><textarea name="it[<?= (int) $it['id'] ?>][comentario]" rows="1"><?= htmlspecialchars((string) ($r['comentario'] ?? '')) ?></textarea></td>
                </tr>
            <?php endforeach; ?>
            </tbody>
        </table></div>
        <?php $abr = $e['registro']['abr'] ?? []; if (trim((string) ($abr['hallazgos'] ?? '')) !== '' || trim((string) ($abr['conclusion'] ?? '')) !== ''): ?>
        <p class="help">Hallazgos: <?= htmlspecialchars((string) ($abr['hallazgos'] ?? '')) ?><br>Conclusión: <?= htmlspecialchars((string) ($abr['conclusion'] ?? '')) ?></p>
        <?php endif; ?>
        <p class="help">Curvas en la entrega: <?= count($abr['curvas'] ?? []) ?>.</p>
        <label>Comentario general para el alumno
            <textarea name="feedback" rows="2" style="width:100%;"><?= htmlspecialchars((string) $en['feedback']) ?></textarea></label>
        <button type="submit" class="btn btn--sm">Guardar revisión de <?= htmlspecialchars($p['codigo']) ?></button>
    </form>
</details>
</div>
<?php endforeach; ?>
<?php
admin_footer();
