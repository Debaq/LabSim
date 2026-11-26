<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Osce.php';
require_once __DIR__ . '/../../src/OscePreguntas.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Réplicas y observaciones de los alumnos de un OSCE, de todas las
 * estaciones (preguntas y app) en un solo lugar. El alumno las escribe desde
 * su enlace (student/osce.php) con resultados publicados o, si el OSCE tiene
 * "resultados al entregar", apenas entrega. Aceptar una réplica no cambia el
 * puntaje solo: se ajusta en la revisión de la estación.
 */

$me = Auth::requireAdminSession();
$id = (int) ($_GET['id'] ?? $_POST['id'] ?? 0);
$osce = Osce::obtener($id);
if ($osce === null || !Courses::canAdminister((int) $osce['course_id'], $me)) {
    http_response_code(404);
    exit('OSCE no encontrado.');
}

$success = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    OscePreguntas::responderReplicas($id, (array) ($_POST['rep'] ?? []));
    AdminAudit::log($me, 'osce_replicas', ['osce_id' => $id]);
    header('Location: osce_replicas.php?id=' . $id . '&ok=1');
    exit;
}
if (isset($_GET['ok'])) {
    $success = 'Respuestas guardadas.';
}

$reps = OscePreguntas::replicasDelOsce($id);
$pend = count(array_filter($reps, static fn ($r) => $r['estado'] === 'pendiente'));

admin_header('Réplicas · ' . $osce['nombre'], $me);
?>
<p><a href="osce.php?id=<?= $id ?>">← Volver al OSCE</a></p>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>
<p><strong><?= count($reps) ?></strong> réplicas u observaciones · <strong><?= $pend ?></strong> pendientes.
   Si aceptas una, ajusta el puntaje en la revisión de esa estación.</p>
<?php if (!$reps): ?>
<p class="muted">Todavía no hay réplicas.</p>
<?php else: ?>
<form method="post">
    <?= csrf_field() ?>
    <input type="hidden" name="id" value="<?= $id ?>">
    <?php foreach ($reps as $r):
        $rev = $r['tipo'] === 'preguntas' ? 'osce_revision.php?estacion=' . (int) $r['estacion_id'] : 'osce_app_revision.php?estacion=' . (int) $r['estacion_id']; ?>
    <div class="card" style="margin-bottom:.8rem;">
        <div class="row row--between">
            <strong>N.º <?= (int) $r['numero'] ?> · <?= htmlspecialchars((string) $r['display_name']) ?></strong>
            <span class="tag<?= $r['estado'] === 'pendiente' ? ' tag--warn' : ' tag--muted' ?>"><?= htmlspecialchars(ucfirst((string) $r['estado'])) ?></span>
        </div>
        <div class="muted"><?= htmlspecialchars((string) $r['estacion']) ?> · <a href="<?= htmlspecialchars($rev) ?>">revisión de la estación</a></div>
        <?php if (trim((string) $r['que']) !== ''): ?><p><em><?= htmlspecialchars(mb_substr((string) $r['que'], 0, 300)) ?></em></p><?php endif; ?>
        <p><strong>El alumno:</strong> <?= nl2br(htmlspecialchars((string) $r['texto'])) ?></p>
        <label>Respuesta
            <textarea name="rep[<?= (int) $r['id'] ?>][respuesta]" rows="2" style="width:100%;"><?= htmlspecialchars((string) $r['respuesta']) ?></textarea></label>
        <label>Estado
            <select name="rep[<?= (int) $r['id'] ?>][estado]" style="width:auto;">
                <?php foreach (['pendiente' => 'Pendiente', 'aceptada' => 'Aceptada (ajusta el puntaje en la revisión)', 'rechazada' => 'Rechazada'] as $ek => $ev): ?>
                <option value="<?= $ek ?>"<?= $r['estado'] === $ek ? ' selected' : '' ?>><?= $ev ?></option>
                <?php endforeach; ?>
            </select></label>
    </div>
    <?php endforeach; ?>
    <button type="submit" class="btn">Guardar respuestas</button>
</form>
<?php endif; ?>
<?php admin_footer(); ?>
