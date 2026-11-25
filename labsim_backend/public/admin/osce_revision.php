<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/OscePreguntas.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Revisión de una estación de preguntas del OSCE: lo que respondió cada
 * alumno, la corrección automática (alternativas) y la de la IA
 * (desarrollo), y lo manual: ajustar puntajes, feedback por respuesta y
 * general, y resolver réplicas. Un puntaje que el docente cambia queda como
 * suyo y la IA ya no lo pisa.
 */

$me = Auth::requireAdminSession();
$estId = (int) ($_GET['estacion'] ?? $_POST['estacion'] ?? 0);
$est = Osce::estacion($estId);
$osce = $est !== null ? Osce::obtener((int) $est['osce_id']) : null;
if ($osce === null || !Courses::canAdminister((int) $osce['course_id'], $me) || $est['tipo'] !== 'preguntas') {
    http_response_code(404);
    exit('Estación no encontrada.');
}

$error = null;
$success = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $accion = (string) ($_POST['accion'] ?? '');
    if ($accion === 'ia') {
        try {
            $v = OscePreguntas::corregirIa((int) ($_POST['resultado'] ?? 0));
            Response::json(['ok' => true] + $v);
        } catch (Throwable $e) {
            Response::error($e->getMessage(), 502);
        }
    }
    if ($accion === 'guardar') {
        try {
            $entregaId = (int) ($_POST['entrega'] ?? 0);
            OscePreguntas::guardarRevision($estId, $entregaId, (array) ($_POST['r'] ?? []), (array) ($_POST['rep'] ?? []),
                                           (string) ($_POST['feedback'] ?? ''), (int) $me['id']);
            AdminAudit::log($me, 'osce_revision', ['estacion_id' => $estId, 'entrega_id' => $entregaId]);
            header('Location: osce_revision.php?estacion=' . $estId . '&ok=' . $entregaId . '#e' . $entregaId);
            exit;
        } catch (InvalidArgumentException $e) {
            $error = $e->getMessage();
        }
    }
}
if (isset($_GET['ok'])) {
    $success = 'Revisión guardada.';
}

$vencidas = OscePreguntas::cerrarVencidas($osce, $est);
$preguntas = [];
foreach (OscePreguntas::preguntas($estId) as $q) {
    $preguntas[(int) $q['id']] = $q;
}
$entregas = OscePreguntas::revision($estId);
$pendientesIa = OscePreguntas::pendientesIa($estId);
$replicasPend = 0;
foreach ($entregas as $e) {
    foreach ($e['respuestas'] as $r) {
        if ($r['replica_id'] !== null && $r['replica_estado'] === 'pendiente') {
            $replicasPend++;
        }
    }
}
$soloReplicas = isset($_GET['replicas']);
$fmt = static fn ($x): string => $x === null ? '' : rtrim(rtrim(number_format((float) $x, 2, ',', ''), '0'), ',');

admin_header('Revisión · ' . $est['titulo'], $me);
?>
<style>
.rev-q { border-top: 1px solid var(--color-border, #ddd); padding: 0.7rem 0; }
.rev-q:first-child { border-top: 0; }
.rev-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 0.8rem; }
@media (max-width: 900px) { .rev-grid { grid-template-columns: 1fr; } }
.rev-resp { background: var(--color-surface-2, #f4f4f6); border-radius: 0.4rem; padding: 0.5rem 0.7rem; white-space: pre-wrap; }
.rev-ia { font-size: 0.92rem; border-left: 3px solid #6366f1; padding-left: 0.6rem; }
.rev-rep { border-left: 3px solid #b45309; padding-left: 0.6rem; margin-top: 0.5rem; }
.rev-q textarea { width: 100%; min-height: 2.6rem; }
.op-ok { color: #15803d; } .op-mal { color: #b91c1c; }
.rev-q ul { list-style: none; padding-left: 0.2rem; }
details.rev > summary { cursor: pointer; padding: 0.4rem 0; font-size: 1.05rem; }
</style>

<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="row row--between row--center" style="margin-bottom:1rem;">
    <a href="osce_estacion.php?id=<?= $estId ?>">← Preguntas de la estación</a>
    <span class="muted"><?= htmlspecialchars($osce['nombre']) ?></span>
</div>

<div class="card">
    <p>
        <strong><?= count($entregas) ?></strong> entregas ·
        <strong id="n-pend"><?= count($pendientesIa) ?></strong> respuestas de desarrollo sin corregir ·
        <strong><?= $replicasPend ?></strong> réplicas pendientes
        <?php if ($vencidas > 0): ?> · <?= $vencidas ?> entrega<?= $vencidas > 1 ? 's' : '' ?> cerrada<?= $vencidas > 1 ? 's' : '' ?> por tiempo<?php endif; ?>
    </p>
    <div class="row row--gap-sm">
        <?php if ($pendientesIa): ?>
        <button type="button" class="btn btn--sm" id="ia-todo">Corregir con IA las <?= count($pendientesIa) ?> pendientes</button>
        <?php endif; ?>
        <a class="btn btn--sm btn--secondary" href="osce_revision.php?estacion=<?= $estId ?><?= $soloReplicas ? '' : '&amp;replicas=1' ?>"><?= $soloReplicas ? 'Ver todas' : 'Solo con réplica pendiente' ?></a>
    </div>
    <p class="help" id="ia-estado"></p>
</div>

<?php if (!$entregas): ?>
<p class="empty-state">Todavía nadie entregó en esta estación.</p>
<?php endif; ?>

<?php foreach ($entregas as $e):
    $tieneRep = false;
    foreach ($e['respuestas'] as $r) {
        if ($r['replica_id'] !== null && $r['replica_estado'] === 'pendiente') {
            $tieneRep = true;
        }
    }
    if ($soloReplicas && !$tieneRep) {
        continue;
    }
    $pend = count(array_filter($e['respuestas'], static fn ($r) => $r['puntaje'] === null));
    $abierta = (isset($_GET['ok']) && (int) $_GET['ok'] === (int) $e['id']) || $tieneRep;
    ?>
<div class="card" id="e<?= (int) $e['id'] ?>">
<details class="rev"<?= $abierta ? ' open' : '' ?>>
    <summary>
        <strong class="mono"><?= htmlspecialchars($e['codigo']) ?></strong>
        <span class="muted"><?= htmlspecialchars((string) $e['display_name']) ?></span> ·
        <?= $fmt($e['puntaje']) ?> / <?= $fmt($e['puntaje_max']) ?> pt
        <?= $e['estado'] !== 'enviada' ? '<span class="tag tag--warn">respondiendo</span>' : '' ?>
        <?= $pend ? '<span class="tag tag--muted">' . $pend . ' sin corregir</span>' : '' ?>
        <?= $tieneRep ? '<span class="tag tag--warn">réplica</span>' : '' ?>
    </summary>
    <form method="post">
        <?= csrf_field() ?>
        <input type="hidden" name="estacion" value="<?= $estId ?>">
        <input type="hidden" name="entrega" value="<?= (int) $e['id'] ?>">
        <input type="hidden" name="accion" value="guardar">
        <?php $n = 0; foreach ($preguntas as $qid => $q): $n++; $r = $e['respuestas'][$qid] ?? null; ?>
        <div class="rev-q">
            <p><strong><?= $n ?>.</strong> <?= nl2br(htmlspecialchars($q['enunciado'])) ?> <span class="muted">(<?= $fmt($q['puntaje']) ?> pt)</span></p>
            <?php if ($r === null): ?>
                <p class="muted">Sin respuesta.</p>
            <?php else: ?>
            <div class="rev-grid">
                <div>
                    <?php if ($q['tipo'] === 'alternativa'): $marc = is_array($r['valor']) ? $r['valor'] : []; ?>
                        <ul style="margin:0;">
                        <?php foreach ($q['opciones'] as $i => $op): $esC = in_array($i, $q['correctas'], true); $m = in_array($i, $marc, true); ?>
                            <li class="<?= $m ? ($esC ? 'op-ok' : 'op-mal') : '' ?>"><?= $m ? '☑' : '☐' ?> <?= htmlspecialchars($op) ?><?= $esC ? ' <span class="muted">(correcta)</span>' : '' ?></li>
                        <?php endforeach; ?>
                        </ul>
                    <?php else: ?>
                        <div class="rev-resp"><?= trim((string) $r['valor']) === '' ? '<span class="muted">(vacía)</span>' : htmlspecialchars((string) $r['valor']) ?></div>
                        <p class="help help--xs">Pauta: <?= htmlspecialchars($q['pauta']) ?></p>
                    <?php endif; ?>
                </div>
                <div>
                    <label>Puntaje (máx. <?= $fmt($q['puntaje']) ?>)
                        <input type="text" inputmode="decimal" name="r[<?= (int) $r['id'] ?>][puntaje]" value="<?= $fmt($r['puntaje']) ?>" class="input--narrow"
                               placeholder="<?= $r['puntaje'] === null ? 'sin corregir' : '' ?>" data-rid="<?= (int) $r['id'] ?>">
                        <span class="help help--xs"><?= $r['fuente'] === 'docente' ? 'puesto por docente' : ($r['fuente'] === 'ia' ? 'IA' : 'automático') ?></span>
                    </label>
                    <?php if ($r['ia_puntaje'] !== null || trim((string) $r['ia_comentario']) !== ''): ?>
                    <div class="rev-ia"><strong>IA: <?= $fmt($r['ia_puntaje']) ?> pt.</strong> <?= htmlspecialchars((string) $r['ia_comentario']) ?></div>
                    <?php endif; ?>
                    <label>Feedback para el alumno
                        <textarea name="r[<?= (int) $r['id'] ?>][comentario]" rows="2"><?= htmlspecialchars((string) $r['comentario']) ?></textarea></label>
                    <?php if ($r['replica_id'] !== null): ?>
                    <div class="rev-rep">
                        <strong>Réplica del alumno:</strong> <?= nl2br(htmlspecialchars((string) $r['replica_texto'])) ?>
                        <label>Respuesta a la réplica
                            <textarea name="rep[<?= (int) $r['replica_id'] ?>][respuesta]" rows="2"><?= htmlspecialchars((string) $r['replica_respuesta']) ?></textarea></label>
                        <label>Estado
                            <select name="rep[<?= (int) $r['replica_id'] ?>][estado]" style="width:auto;">
                                <?php foreach (['pendiente' => 'Pendiente', 'aceptada' => 'Aceptada (ajusta el puntaje arriba)', 'rechazada' => 'Rechazada'] as $ek => $ev): ?>
                                <option value="<?= $ek ?>"<?= $r['replica_estado'] === $ek ? ' selected' : '' ?>><?= $ev ?></option>
                                <?php endforeach; ?>
                            </select></label>
                    </div>
                    <?php endif; ?>
                </div>
            </div>
            <?php endif; ?>
        </div>
        <?php endforeach; ?>
        <label>Comentario general para el alumno
            <textarea name="feedback" rows="2" style="width:100%;"><?= htmlspecialchars((string) $e['feedback']) ?></textarea></label>
        <button type="submit" class="btn btn--sm">Guardar revisión de <?= htmlspecialchars($e['codigo']) ?></button>
    </form>
</details>
</div>
<?php endforeach; ?>

<?php if ($pendientesIa): ?>
<script>
(function () {
    'use strict';
    var pendientes = <?= json_encode($pendientesIa) ?>;
    var CSRF = <?= json_encode(Auth::csrfToken()) ?>;
    var btn = document.getElementById('ia-todo'), estado = document.getElementById('ia-estado');
    btn.addEventListener('click', function () {
        btn.disabled = true;
        var hechas = 0, fallas = [];
        (function siguiente(i) {
            if (i >= pendientes.length) {
                estado.textContent = 'Listo: ' + hechas + ' corregidas' + (fallas.length ? ', ' + fallas.length + ' con error (' + fallas[0] + ')' : '') + '. Recargando…';
                setTimeout(function () { location.reload(); }, 1200);
                return;
            }
            estado.textContent = 'Corrigiendo ' + (i + 1) + ' de ' + pendientes.length + '…';
            var fd = new FormData();
            fd.append('csrf_token', CSRF);
            fd.append('estacion', <?= $estId ?>);
            fd.append('accion', 'ia');
            fd.append('resultado', pendientes[i]);
            fetch('osce_revision.php', { method: 'POST', body: fd, credentials: 'same-origin' })
                .then(function (r) { return r.json().then(function (d) { if (!r.ok) throw new Error(d.error); return d; }); })
                .then(function (d) {
                    hechas++;
                    var inp = document.querySelector('[data-rid="' + pendientes[i] + '"]');
                    if (inp) inp.value = String(d.puntaje).replace('.', ',');
                })
                .catch(function (e) { fallas.push(e.message); })
                .then(function () { siguiente(i + 1); });
        })(0);
    });
})();
</script>
<?php endif; ?>
<?php
admin_footer();
