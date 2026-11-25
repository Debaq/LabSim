<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Osce.php';
require_once __DIR__ . '/../../src/OscePauta.php';
require_once __DIR__ . '/../../src/OscePreguntas.php';
require_once __DIR__ . '/../../src/OsceApp.php';
require_once __DIR__ . '/../../src/QrSvg.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Contenido de una estación del OSCE: la pauta docente (ítems tick e
 * impedancias, precargable desde el Protocolo Técnico ORL 2019 según el
 * examen) o las preguntas (alternativas y desarrollo, importables en GIFT,
 * con el enlace y QR de la tablet de la estación). Los demás tipos se arman
 * en los pasos 4 a 6 de docs/osce_plan.md.
 *
 * Pauta y preguntas se pueden editar hasta la primera entrega de la
 * estación: después, cambiarlas dejaría a los alumnos medidos distinto.
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
            throw new InvalidArgumentException('La estación ya tiene entregas: su contenido queda fijo.');
        }
        $qId = (int) ($_POST['pregunta_id'] ?? 0);
        switch ($accion) {
            case 'q_add':
                OscePreguntas::agregar($estId, OscePreguntas::limpiar($_POST));
                $success = 'Pregunta agregada.';
                break;
            case 'q_edit':
                OscePreguntas::editar($estId, $qId, OscePreguntas::limpiar($_POST));
                $success = 'Pregunta guardada.';
                break;
            case 'q_del':
                OscePreguntas::quitar($estId, $qId);
                $success = 'Pregunta quitada.';
                break;
            case 'q_up':
            case 'q_down':
                OscePreguntas::mover($estId, $qId, $accion === 'q_up' ? -1 : 1);
                break;
            case 'app':
                OsceApp::guardarContenido($est, $_POST);
                $est = Osce::estacion($estId);
                $success = 'Contenido de la estación guardado y criterios rehechos.';
                break;
            case 'gift':
                $r = OscePreguntas::importarGift($estId, (string) ($_POST['gift'] ?? ''));
                $success = "Importadas {$r['importadas']} preguntas." . ($r['errores'] ? ' No se importó: ' . implode(' ', $r['errores']) : '');
                break;
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
$preguntas = $est['tipo'] === 'preguntas' ? OscePreguntas::preguntas($estId) : [];
$urlTablet = $est['tipo'] === 'preguntas' ? Osce::urlPublica('student/osce_estacion.php?k=' . OscePreguntas::tokenTablet($estId)) : '';
$esApp = OsceApp::esApp((string) $est['tipo']);
$appCfg = $esApp ? OsceApp::config($est) : [];
$appCodigo = $esApp ? OsceApp::codigoEstacion($estId) : '';
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
    <?php elseif ($est['tipo'] === 'preguntas'): ?>
    <a class="btn btn--sm" href="osce_revision.php?estacion=<?= $estId ?>">Revisión y réplicas</a>
    <?php elseif (OsceApp::esApp((string) $est['tipo'])): ?>
    <a class="btn btn--sm" href="osce_app_revision.php?estacion=<?= $estId ?>">Revisión</a>
    <?php endif; ?>
</div>

<div class="card">
    <p>
        <strong><?= htmlspecialchars(Osce::TIPOS[$est['tipo']] ?? $est['tipo']) ?></strong> ·
        <?= htmlspecialchars(Osce::EXAMENES[$est['examen']] ?? $est['examen']) ?> ·
        peso <?= $fmt($est['peso']) ?>
    </p>
    <?php if ($est['tipo'] === 'preguntas'): ?>
        <p class="help">Alternativas: con una correcta, todo o nada; con varias, el alumno marca todas las que crea correctas y cada marca incorrecta descuenta una correcta (nunca bajo 0). Las opciones salen en orden distinto para cada alumno. Desarrollo: la IA corrige contra la pauta al entregar; tú revisas, ajustas y das el feedback en "Revisión y réplicas".</p>
        <?php if (!$editable): ?>
            <p class="text-warn"><?= $evaluados ?> entrega<?= $evaluados > 1 ? 's' : '' ?>: las preguntas quedan fijas.</p>
        <?php endif; ?>
    <?php elseif ($esApp): ?>
        <p class="help"><?= $est['tipo'] === 'config_equipo'
            ? 'El alumno encuentra el ABR con el montaje hecho y todos los controles al azar; al entregar (o al terminar el tiempo) se compara lo que dejó configurado con lo esperado. Cada parámetro es un criterio.'
            : ($est['tipo'] === 'marcaje'
                ? 'La app registra sola las curvas indicadas, con el equipo en su configuración de rutina, y el alumno solo marca. Se compara cada marca con la latencia verdadera del generador; donde no hay onda, lo correcto es no marcarla.'
                : 'El alumno hace el examen completo: parte con el equipo al azar y el montaje hecho, configura, registra, marca y busca el umbral. Se evalúa cómo tomó cada curva (parámetros) y la secuencia (estrategia).') ?></p>
        <?php if (!$editable): ?>
            <p class="text-warn"><?= $evaluados ?> entrega<?= $evaluados > 1 ? 's' : '' ?>: el contenido queda fijo.</p>
        <?php endif; ?>
    <?php elseif ($est['tipo'] !== 'pauta_docente'): ?>
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

<?php if ($esApp):
    $modulo = OsceApp::modulo((string) $est['examen']);
    $casos = OsceApp::casos($modulo);
    $esProtocolo = $est['tipo'] === 'protocolo';
    $esperado = $esProtocolo
        ? ($appCfg['esperado_curvas'] ?? OsceApp::ESPERADO_CURVAS[$est['examen']] ?? [])
        : ($appCfg['esperado'] ?? OsceApp::ESPERADO[$est['examen']] ?? []);
    $puntosItem = [];
    foreach ($items as $it) {
        if (in_array($it['cfg']['regla'] ?? '', ['param', 'curvas_param'], true)) {
            $puntosItem[$it['cfg']['clave']] = $it;
        }
    }
    $estrategia = OsceApp::estrategia($est);
    $ondaResp = $appCfg['onda'] ?? OsceApp::ondas((string) $est['examen'])[1][0];
    ?>
<div class="card">
    <h2>PC de la estación</h2>
    <p>En el PC de la estación, abre LabSim y en la ventana de ingreso elige <strong>Ingresar con usuario y contraseña → Estación OSCE</strong>. Escribe este código:</p>
    <p class="mono" style="font-size:2.2rem; font-weight:700; letter-spacing:0.08em; margin:0.3rem 0;"><?= htmlspecialchars($appCodigo) ?></p>
    <p class="help">El PC queda como esta estación (solo el <?= $modulo ?>). Cada alumno escribe su código, que solo sirve en su turno según el reloj; al terminar el tiempo la app entrega sola.</p>
    <?php if (empty($appCfg['case_id'])): ?><p class="text-warn">Falta elegir el paciente y guardar el contenido: sin eso la estación no abre.</p><?php endif; ?>
</div>

<div class="card">
    <h2>Contenido</h2>
    <form method="post">
        <?= csrf_field() ?>
        <input type="hidden" name="id" value="<?= $estId ?>">
        <input type="hidden" name="accion" value="app">
        <fieldset <?= $editable ? '' : 'disabled' ?> style="border:0; padding:0; margin:0;">
        <label>Paciente (caso con <?= $modulo ?>)
            <select name="case_id" required>
                <option value="">— Elegir —</option>
                <?php foreach ($casos as $c): ?>
                <option value="<?= htmlspecialchars($c['id']) ?>"<?= ($appCfg['case_id'] ?? '') === $c['id'] ? ' selected' : '' ?>><?= htmlspecialchars($c['rotulo']) ?></option>
                <?php endforeach; ?>
            </select></label>
        <p class="help">Abre el equipo <strong><?= $modulo ?></strong> en <strong><?= htmlspecialchars(OsceApp::PRUEBA_DE_EXAMEN[$est['examen']] ?? 'ABR') ?></strong> (según el examen de la estación).
            <?= $modulo === 'VEMP' ? 'El VEMP de LabSim mide la intensidad en dB SPL (el protocolo dice "100 dB nHL"): escribe tú la intensidad esperada.' : '' ?></p>
        <?php if ($est['tipo'] === 'marcaje'): ?>
        <div class="row row--gap-lg">
            <label>Curvas que registra la app (una por línea: oído e intensidad)
                <textarea name="curvas" rows="8" style="display:block; width:14rem;"><?= htmlspecialchars(isset($appCfg['curvas']) ? OsceApp::curvasTexto($appCfg['curvas']) : ($modulo === 'VEMP' ? "OD 120\nOD 110\nOD 100\nOI 120\nOI 110\nOI 100" : OsceApp::CURVAS_BASE)) ?></textarea></label>
            <label>Tolerancia de latencia (ms)
                <input type="text" inputmode="decimal" name="tol_ms" value="<?= $fmt($appCfg['tol_ms'] ?? 0.2) ?>" class="input--narrow"></label>
        </div>
        <?php [$ondasMax, $ondasResto] = OsceApp::ondas((string) $est['examen']); ?>
        <p class="help">Se evalúan las ondas <?= htmlspecialchars(implode(', ', $ondasMax)) ?> en la intensidad más alta de cada oído y <?= htmlspecialchars(implode(', ', $ondasResto)) ?> en las demás (1 punto cada una).</p>
        <?php else: ?>
        <p class="help"><?= $esProtocolo
            ? '<strong>Parámetros de cada curva registrada:</strong> el puntaje es la proporción de curvas que cumplen.'
            : '<strong>Configuración al entregar.</strong>' ?>
            Esperado: un valor, varios separados por <code>|</code> (cualquiera vale) o un rango <code>10–12</code>. Vacío = no se evalúa. Precargado del Protocolo Técnico ORL 2019<?= $est['examen'] === 'peatc' ? ' (la ventana del protocolo dice "10 s", es 10 ms; ganancia "10k" = 10000)' : '' ?>.</p>
        <div class="table-wrap"><table>
            <thead><tr><th>Parámetro</th><th>Esperado</th><th>Puntos</th><th>Crítico</th></tr></thead>
            <tbody>
            <?php foreach (OsceApp::parametros((string) $est['examen']) as $clave => [$fuente, $rotulo]):
                if (!$esProtocolo && $clave === 'emg_ok') { continue; }
                $itp = $puntosItem[$clave] ?? null; ?>
                <tr>
                    <td><?= htmlspecialchars($rotulo) ?><?= $modulo === 'ABR' && !$esProtocolo ? ' <span class="help help--xs">' . ($fuente === 'equipo' ? 'parámetros avanzados' : 'panel') . '</span>' : '' ?></td>
                    <td><input type="text" name="esperado[<?= $clave ?>]" value="<?= htmlspecialchars((string) ($esperado[$clave] ?? '')) ?>"></td>
                    <td><input type="text" inputmode="decimal" name="puntos[<?= $clave ?>]" value="<?= $itp ? $fmt($itp['puntaje']) : '1' ?>" class="input--narrow"></td>
                    <td><input type="checkbox" name="critico[<?= $clave ?>]" value="1"<?= $itp && (int) $itp['critico'] ? ' checked' : '' ?>></td>
                </tr>
            <?php endforeach; ?>
            </tbody>
        </table></div>
        <?php endif; ?>
        <?php if ($esProtocolo): ?>
        <h3 style="margin-top:1rem;">Estrategia</h3>
        <label>Onda que define "hay respuesta" <input type="text" name="onda" value="<?= htmlspecialchars((string) $ondaResp) ?>" class="input--narrow"></label>
        <p class="help">Para juzgar la estrategia, hay respuesta en una curva si el alumno marcó esa onda: se evalúa si lo que hizo es coherente con lo que vio. Solo el umbral se compara con el real (del estímulo con que lo encontró). Una <strong>bonificación</strong> suma pero no sube el máximo: no la tener no descuenta. Los criterios que no aplican (por ejemplo, subir de nivel si siempre hubo respuesta) dan el puntaje completo.</p>
        <div class="table-wrap"><table>
            <thead><tr><th>Activa</th><th>Criterio</th><th>Valor</th><th>Puntos</th><th>Bonificación</th></tr></thead>
            <tbody>
            <?php foreach (OsceApp::ESTRATEGIA as $clave => [$rotulo, $pide]): $r = $estrategia[$clave] ?? ['activa' => false, 'valor' => '', 'puntos' => 1, 'bonus' => false]; ?>
                <tr>
                    <td><input type="checkbox" name="estrategia[<?= $clave ?>][activa]" value="1"<?= !empty($r['activa']) ? ' checked' : '' ?>></td>
                    <td><?= htmlspecialchars(str_replace('{v}', '…', $rotulo)) ?></td>
                    <td><?php if ($pide !== ''): ?><input type="text" name="estrategia[<?= $clave ?>][valor]" value="<?= htmlspecialchars((string) $r['valor']) ?>" placeholder="<?= htmlspecialchars($pide) ?>" class="input--narrow"><?php endif; ?></td>
                    <td><input type="text" inputmode="decimal" name="estrategia[<?= $clave ?>][puntos]" value="<?= $fmt($r['puntos']) ?>" class="input--narrow"></td>
                    <td><input type="checkbox" name="estrategia[<?= $clave ?>][bonus]" value="1"<?= !empty($r['bonus']) ? ' checked' : '' ?>></td>
                </tr>
            <?php endforeach; ?>
            </tbody>
        </table></div>
        <?php endif; ?>
        <?php if ($editable): ?><button type="submit" class="btn btn--sm">Guardar contenido</button><?php endif; ?>
        </fieldset>
    </form>
</div>

<?php if ($items): ?>
<div class="card">
    <h2>Criterios (<?= count($items) ?> · <?= $fmt($totalPts) ?> puntos)</h2>
    <ul>
    <?php foreach ($items as $it): ?>
        <li><?= htmlspecialchars($it['texto']) ?><?= in_array($it['cfg']['regla'] ?? '', ['param', 'curvas_param'], true) ? ': <span class="mono">' . htmlspecialchars((string) $it['cfg']['esperado']) . '</span>' : '' ?>
            <span class="muted">(<?= $fmt($it['puntaje']) ?> pt)</span><?= (int) $it['critico'] ? ' <span class="tag tag--danger">crítico</span>' : '' ?></li>
    <?php endforeach; ?>
    </ul>
</div>
<?php endif; ?>
<?php endif; ?>

<?php if ($est['tipo'] === 'preguntas'): $totalQ = array_sum(array_map(static fn ($q) => (float) $q['puntaje'], $preguntas)); ?>
<div class="card">
    <h2>Tablet de la estación</h2>
    <div class="row row--gap-lg row--center">
        <?= QrSvg::svg($urlTablet, 3) ?>
        <div>
            <p>Abre este enlace en la tablet de la estación (o escanea el QR con ella) y déjala ahí. Cada alumno escribe su código; solo entra cuando el reloj dice que le toca, y la tablet entrega sola al terminar el tiempo.</p>
            <p><a href="<?= htmlspecialchars($urlTablet) ?>" target="_blank" class="mono" style="word-break:break-all;"><?= htmlspecialchars($urlTablet) ?></a></p>
        </div>
    </div>
</div>

<div class="card">
    <h2>Preguntas (<?= count($preguntas) ?> · <?= $fmt($totalQ) ?> puntos)</h2>
    <?php if (!$preguntas): ?>
        <p class="empty-state">Sin preguntas. Agrégalas abajo o impórtalas en formato GIFT.</p>
    <?php endif; ?>
    <?php foreach ($preguntas as $k => $q): $fid = 'q' . (int) $q['id']; ?>
    <div class="card" style="margin:0.6rem 0; padding:0.8rem;">
        <?php if ($editable): ?>
        <form id="<?= $fid ?>" method="post">
            <?= csrf_field() ?>
            <input type="hidden" name="id" value="<?= $estId ?>">
            <input type="hidden" name="pregunta_id" value="<?= (int) $q['id'] ?>">
            <div class="row row--gap-lg row--center">
                <strong><?= $k + 1 ?>.</strong>
                <label>Tipo <select name="tipo" style="width:auto;" data-q-tipo>
                    <?php foreach (OscePreguntas::TIPOS as $tk => $tv): ?><option value="<?= $tk ?>"<?= $tk === $q['tipo'] ? ' selected' : '' ?>><?= htmlspecialchars($tv) ?></option><?php endforeach; ?>
                </select></label>
                <label>Puntos <input type="text" inputmode="decimal" name="puntaje" value="<?= $fmt($q['puntaje']) ?>" class="input--narrow"></label>
            </div>
            <label>Enunciado <textarea name="enunciado" rows="2" style="display:block; width:100%;"><?= htmlspecialchars($q['enunciado']) ?></textarea></label>
            <label data-para="alternativa"<?= $q['tipo'] === 'alternativa' ? '' : ' hidden' ?>>Alternativas (una por línea; <strong>*</strong> al inicio en las correctas)
                <textarea name="opciones" rows="<?= max(3, count($q['opciones'])) ?>" style="display:block; width:100%;"><?= htmlspecialchars(OscePreguntas::opcionesTexto($q)) ?></textarea></label>
            <label data-para="desarrollo"<?= $q['tipo'] === 'desarrollo' ? '' : ' hidden' ?>>Pauta para la IA (qué debe contener la respuesta y cuánto vale cada parte)
                <textarea name="pauta" rows="3" style="display:block; width:100%;"><?= htmlspecialchars($q['pauta']) ?></textarea></label>
            <div class="row row--gap-sm">
                <button type="submit" name="accion" value="q_edit" class="btn btn--xs">Guardar</button>
                <button type="submit" name="accion" value="q_up" class="btn btn--xs btn--ghost"<?= $k === 0 ? ' disabled' : '' ?>>↑</button>
                <button type="submit" name="accion" value="q_down" class="btn btn--xs btn--ghost"<?= $k === count($preguntas) - 1 ? ' disabled' : '' ?>>↓</button>
                <button type="submit" name="accion" value="q_del" class="btn btn--xs btn--danger" onclick="return confirm('¿Quitar esta pregunta?')">Quitar</button>
            </div>
        </form>
        <?php else: ?>
            <p><strong><?= $k + 1 ?>.</strong> <?= nl2br(htmlspecialchars($q['enunciado'])) ?> <span class="muted">(<?= $fmt($q['puntaje']) ?> pt)</span></p>
            <?php if ($q['tipo'] === 'alternativa'): ?>
            <ul><?php foreach ($q['opciones'] as $i => $o): ?><li<?= in_array($i, $q['correctas'], true) ? ' style="font-weight:600"' : '' ?>><?= htmlspecialchars($o) ?><?= in_array($i, $q['correctas'], true) ? ' ✓' : '' ?></li><?php endforeach; ?></ul>
            <?php else: ?>
            <p class="help">Pauta: <?= nl2br(htmlspecialchars($q['pauta'])) ?></p>
            <?php endif; ?>
        <?php endif; ?>
    </div>
    <?php endforeach; ?>

    <?php if ($editable): ?>
    <h3 style="margin-top:1.2rem;">Agregar pregunta</h3>
    <form method="post">
        <?= csrf_field() ?>
        <input type="hidden" name="id" value="<?= $estId ?>">
        <input type="hidden" name="accion" value="q_add">
        <div class="row row--gap-lg row--center">
            <label>Tipo <select name="tipo" id="q-tipo" style="width:auto;">
                <?php foreach (OscePreguntas::TIPOS as $tk => $tv): ?><option value="<?= $tk ?>"><?= htmlspecialchars($tv) ?></option><?php endforeach; ?>
            </select></label>
            <label>Puntos <input type="text" inputmode="decimal" name="puntaje" value="1" class="input--narrow"></label>
        </div>
        <label>Enunciado <textarea name="enunciado" rows="2" required style="display:block; width:100%;"></textarea></label>
        <label id="q-opciones">Alternativas (una por línea; <strong>*</strong> al inicio en las correctas)
            <textarea name="opciones" rows="4" style="display:block; width:100%;" placeholder="*Alternada&#10;Rarefacción&#10;Condensación"></textarea></label>
        <label id="q-pauta" hidden>Pauta para la IA (qué debe contener la respuesta y cuánto vale cada parte)
            <textarea name="pauta" rows="3" style="display:block; width:100%;" placeholder="Menciona X (1 pt) y explica Y (1 pt)."></textarea></label>
        <button type="submit" class="btn btn--sm">Agregar pregunta</button>
    </form>
    <script>
    document.getElementById('q-tipo').addEventListener('change', function () {
        document.getElementById('q-opciones').hidden = this.value !== 'alternativa';
        document.getElementById('q-pauta').hidden = this.value !== 'desarrollo';
    });
    document.querySelectorAll('[data-q-tipo]').forEach(function (sel) {
        sel.addEventListener('change', function () {
            sel.form.querySelectorAll('[data-para]').forEach(function (l) { l.hidden = l.dataset.para !== sel.value; });
        });
    });
    </script>

    <h3 style="margin-top:1.2rem;">Importar GIFT</h3>
    <form method="post">
        <?= csrf_field() ?>
        <input type="hidden" name="id" value="<?= $estId ?>">
        <input type="hidden" name="accion" value="gift">
        <p class="help">Alternativas (<code>=correcta ~incorrecta</code>, varias correctas con <code>~%50%</code>), verdadero/falso (<code>{T}</code>) y ensayo (<code>{}</code>). A los ensayos hay que escribirles la pauta después.</p>
        <textarea name="gift" rows="6" style="display:block; width:100%;" placeholder="::P1:: ¿Qué polaridad usa el protocolo del PEATC? {=Alternada ~Rarefacción ~Condensación}"></textarea>
        <button type="submit" class="btn btn--sm btn--secondary">Importar</button>
    </form>
    <?php endif; ?>
</div>
<?php endif; ?>
<?php
admin_footer();
