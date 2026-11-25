<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Osce.php';
require_once __DIR__ . '/../../src/OscePauta.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Contenido de una estación del OSCE. Hoy: la pauta docente (ítems tick e
 * impedancias), precargable desde el Protocolo Técnico ORL 2019 según el
 * examen. Los demás tipos se arman en los pasos 3 a 6 de docs/osce_plan.md.
 *
 * La pauta se puede editar hasta que la estación tenga la primera
 * evaluación: después, cambiarla dejaría a los alumnos medidos con
 * pautas distintas.
 */

$me = Auth::requireAdminSession();
$estId = (int) ($_GET['id'] ?? $_POST['id'] ?? 0);
$est = Osce::estacion($estId);
$osce = $est !== null ? Osce::obtener((int) $est['osce_id']) : null;
if ($osce === null || !Courses::canAdminister((int) $osce['course_id'], $me)) {
    http_response_code(404);
    exit('Estación no encontrada.');
}
$osceId = (int) $osce['id'];
$evaluados = count(OscePauta::estadosEstacion($estId));
$editable = $evaluados === 0;

$error = null;
$success = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $accion = (string) ($_POST['accion'] ?? '');
    $itemId = (int) ($_POST['item_id'] ?? 0);
    try {
        if (!$editable) {
            throw new InvalidArgumentException('La estación ya tiene evaluaciones: la pauta queda fija.');
        }
        switch ($accion) {
            case 'base':
                OscePauta::cargarBase($estId, (string) $est['examen']);
                $success = 'Pauta del protocolo cargada.';
                break;
            case 'add':
                OscePauta::agregarItem($estId, $_POST);
                $success = 'Ítem agregado.';
                break;
            case 'edit':
                OscePauta::editarItem($estId, $itemId, $_POST);
                $success = 'Ítem guardado.';
                break;
            case 'del':
                OscePauta::quitarItem($estId, $itemId);
                $success = 'Ítem quitado.';
                break;
            case 'up':
            case 'down':
                OscePauta::moverItem($estId, $itemId, $accion === 'up' ? -1 : 1);
                break;
            default:
                throw new InvalidArgumentException('Acción desconocida.');
        }
        AdminAudit::log($me, 'osce_pauta_' . $accion, ['osce_id' => $osceId, 'estacion_id' => $estId]);
    } catch (InvalidArgumentException $e) {
        $error = $e->getMessage();
    }
}

$items = OscePauta::items($estId);
$totalPts = array_sum(array_map(static fn ($i) => (float) $i['puntaje'], $items));
$montaje = OscePauta::montaje((string) $est['examen']);
$fmt = static fn ($x): string => rtrim(rtrim(number_format((float) $x, 2, ',', ''), '0'), ',');

admin_header('Estación · ' . $est['titulo'], $me);
?>
<style>
.pauta-item textarea { min-height: 3.2rem; display: block; width: 100%; }
.pauta-imp label { display: flex; flex-direction: column; justify-content: space-between; }
.pauta-item td { vertical-align: top; }
.pauta-imp { display: grid; grid-template-columns: 1fr auto auto; gap: 0.5rem; margin-top: 0.4rem; }
.pauta-imp textarea { min-height: 7.5rem; font-size: 0.9rem; }
</style>

<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="row row--between row--center" style="margin-bottom:1rem;">
    <a href="osce.php?id=<?= $osceId ?>">← <?= htmlspecialchars($osce['nombre']) ?></a>
    <?php if ($est['tipo'] === 'pauta_docente'): ?>
    <a class="btn btn--sm" href="osce_evaluar.php?estacion=<?= $estId ?>">Evaluar en esta estación</a>
    <?php endif; ?>
</div>

<div class="card">
    <p>
        <strong><?= htmlspecialchars(Osce::TIPOS[$est['tipo']] ?? $est['tipo']) ?></strong> ·
        <?= htmlspecialchars(Osce::EXAMENES[$est['examen']] ?? $est['examen']) ?> ·
        peso <?= $fmt($est['peso']) ?>
    </p>
    <?php if ($est['tipo'] !== 'pauta_docente'): ?>
        <p class="muted">El contenido de este tipo de estación se arma en los pasos siguientes del plan (docs/osce_plan.md).</p>
    <?php else: ?>
        <p class="help">Cumple = puntaje completo, parcial = la mitad, no cumple = 0. Impedancias: completo si cumplen el límite por electrodo y el interelectrodo, la mitad si cumple uno. Un ítem <strong>crítico</strong> en "no cumple" reprueba la estación aunque sume puntos.</p>
        <?php if (!$editable): ?>
            <p class="text-warn"><?= $evaluados ?> alumno<?= $evaluados > 1 ? 's' : '' ?> ya evaluado<?= $evaluados > 1 ? 's' : '' ?>: la pauta queda fija.</p>
        <?php endif; ?>
    <?php endif; ?>
</div>

<?php if ($est['tipo'] === 'pauta_docente'): ?>
<div class="card">
    <h2>Pauta (<?= count($items) ?> ítems · <?= $fmt($totalPts) ?> puntos)</h2>
    <?php if ($editable): ?>
    <form method="post" class="row row--gap-sm row--center" style="margin-bottom:0.8rem;">
        <?= csrf_field() ?>
        <input type="hidden" name="id" value="<?= $estId ?>">
        <button type="submit" name="accion" value="base" class="btn btn--sm btn--secondary"
            <?= $items ? 'onclick="return confirm(\'Esto reemplaza los ítems actuales por la pauta del protocolo. ¿Seguir?\')"' : '' ?>>
            Cargar pauta del protocolo · <?= htmlspecialchars(Osce::EXAMENES[$est['examen']] ?? $est['examen']) ?>
        </button>
        <span class="help help--xs"><?= htmlspecialchars($montaje['fuente']) ?></span>
    </form>
    <?php endif; ?>

    <?php if (!$items): ?>
        <p class="empty-state">Sin ítems. Carga la pauta del protocolo o agrega ítems a mano.</p>
    <?php else: ?>
    <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>Ítem</th><th>Puntos</th><th>Crítico</th><th></th></tr></thead>
        <tbody>
        <?php foreach ($items as $k => $it): $fid = 'it' . (int) $it['id']; $imp = $it['tipo'] === 'impedancias'; ?>
            <tr class="pauta-item">
                <td><?= $k + 1 ?></td>
                <?php if ($editable): ?>
                <td>
                    <textarea form="<?= $fid ?>" name="texto" rows="2"><?= htmlspecialchars($it['texto']) ?></textarea>
                    <input form="<?= $fid ?>" type="hidden" name="tipo" value="<?= htmlspecialchars($it['tipo']) ?>">
                    <?php if ($imp): ?>
                    <div class="pauta-imp">
                        <label>Electrodos (uno por línea)
                            <textarea form="<?= $fid ?>" name="electrodos"><?= htmlspecialchars(implode("\n", $it['cfg']['electrodos'] ?? [])) ?></textarea></label>
                        <label>Límite por electrodo (kΩ)
                            <input form="<?= $fid ?>" type="text" inputmode="decimal" name="max_kohm" value="<?= htmlspecialchars($fmt($it['cfg']['max_kohm'] ?? '')) ?>" class="input--narrow"></label>
                        <label>Interelectrodo (kΩ)
                            <input form="<?= $fid ?>" type="text" inputmode="decimal" name="inter_kohm" value="<?= isset($it['cfg']['inter_kohm']) ? htmlspecialchars($fmt($it['cfg']['inter_kohm'])) : '' ?>" class="input--narrow" placeholder="sin límite"></label>
                    </div>
                    <?php endif; ?>
                </td>
                <td><input form="<?= $fid ?>" type="text" inputmode="decimal" name="puntaje" value="<?= $fmt($it['puntaje']) ?>" class="input--narrow"></td>
                <td><input form="<?= $fid ?>" type="checkbox" name="critico" value="1"<?= (int) $it['critico'] ? ' checked' : '' ?> aria-label="Crítico"></td>
                <td class="nowrap">
                    <form id="<?= $fid ?>" method="post" style="display:inline">
                        <?= csrf_field() ?>
                        <input type="hidden" name="id" value="<?= $estId ?>">
                        <input type="hidden" name="item_id" value="<?= (int) $it['id'] ?>">
                        <button type="submit" name="accion" value="edit" class="btn btn--xs">Guardar</button>
                        <button type="submit" name="accion" value="up" class="btn btn--xs btn--ghost" title="Subir"<?= $k === 0 ? ' disabled' : '' ?>>↑</button>
                        <button type="submit" name="accion" value="down" class="btn btn--xs btn--ghost" title="Bajar"<?= $k === count($items) - 1 ? ' disabled' : '' ?>>↓</button>
                        <button type="submit" name="accion" value="del" class="btn btn--xs btn--danger" onclick="return confirm('¿Quitar este ítem?')">Quitar</button>
                    </form>
                </td>
                <?php else: ?>
                <td><?= htmlspecialchars($it['texto']) ?>
                    <?php if ($imp): ?><div class="help help--xs"><?= htmlspecialchars(implode(' · ', $it['cfg']['electrodos'] ?? [])) ?> — &lt; <?= $fmt($it['cfg']['max_kohm'] ?? 0) ?> kΩ<?= isset($it['cfg']['inter_kohm']) ? ', interelectrodo &lt; ' . $fmt($it['cfg']['inter_kohm']) . ' kΩ' : '' ?></div><?php endif; ?></td>
                <td><?= $fmt($it['puntaje']) ?></td>
                <td><?= (int) $it['critico'] ? '<span class="tag tag--danger">crítico</span>' : '' ?></td>
                <td></td>
                <?php endif; ?>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table></div>
    <?php endif; ?>

    <?php if ($editable): ?>
    <h3 style="margin-top:1.2rem;">Agregar ítem</h3>
    <form method="post">
        <?= csrf_field() ?>
        <input type="hidden" name="id" value="<?= $estId ?>">
        <input type="hidden" name="accion" value="add">
        <label>Texto <textarea name="texto" rows="2" required style="display:block; width:100%;"></textarea></label>
        <div class="row row--gap-lg row--center">
            <label>Tipo
                <select name="tipo" id="nuevo-tipo">
                    <option value="tick">Cumple / parcial / no cumple</option>
                    <option value="impedancias">Impedancias (kΩ por cable)</option>
                </select></label>
            <label>Puntos <input type="text" inputmode="decimal" name="puntaje" value="1" class="input--narrow"></label>
            <label class="inline-check"><input type="checkbox" name="critico" value="1"> Crítico</label>
        </div>
        <div class="pauta-imp" id="nuevo-imp" hidden>
            <label>Electrodos (uno por línea)
                <textarea name="electrodos"><?= htmlspecialchars(implode("\n", array_map(static fn ($e) => $e[0] . ' · ' . $e[1], $montaje['electrodos']))) ?></textarea></label>
            <label>Límite por electrodo (kΩ) <input type="text" inputmode="decimal" name="max_kohm" value="<?= $fmt($montaje['max_kohm']) ?>" class="input--narrow"></label>
            <label>Interelectrodo (kΩ) <input type="text" inputmode="decimal" name="inter_kohm" value="<?= $montaje['inter_kohm'] !== null ? $fmt($montaje['inter_kohm']) : '' ?>" class="input--narrow" placeholder="sin límite"></label>
        </div>
        <button type="submit" class="btn btn--sm">Agregar ítem</button>
    </form>
    <script>
    document.getElementById('nuevo-tipo').addEventListener('change', function () {
        document.getElementById('nuevo-imp').hidden = this.value !== 'impedancias';
    });
    </script>
    <?php endif; ?>
</div>
<?php endif; ?>
<?php
admin_footer();
