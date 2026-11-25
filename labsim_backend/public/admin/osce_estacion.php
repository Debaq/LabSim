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
                OsceApp::guardarTarea($est, (int) ($_POST['tarea'] ?? 0), $_POST);
                $est = Osce::estacion($estId);
                $success = 'Tarea guardada y criterios rehechos.';
                break;
            case 'tarea_quitar':
                OsceApp::quitarTarea($est, (int) ($_POST['tarea'] ?? -1));
                $est = Osce::estacion($estId);
                $success = 'Tarea quitada.';
                break;
            case 'tarea_up':
            case 'tarea_down':
                OsceApp::moverTarea($est, (int) ($_POST['tarea'] ?? -1), $accion === 'tarea_up' ? -1 : 1);
                $est = Osce::estacion($estId);
                break;
            case 'pesos':
                OsceApp::guardarPesos($est, (array) ($_POST['peso'] ?? []));
                $est = Osce::estacion($estId);
                $success = 'Pesos guardados.';
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
                : ($est['tipo'] === 'conclusion'
                    ? 'La app registra las curvas del caso; el alumno las marca y escribe hallazgos y conclusión en el informe del equipo. La IA corrige el informe criterio por criterio y tú lo revisas.'
                    : 'El alumno hace el examen completo: parte con el equipo al azar y el montaje hecho, configura, registra, marca y busca el umbral. Se evalúa cómo tomó cada curva (parámetros) y la secuencia (estrategia).')) ?></p>
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
    $tareas = OsceApp::tareas($est);
    $nTareas = count($tareas);
    // Tarea que se edita: ?tarea=k (k = nTareas es una nueva, con ?examen=).
    $kTarea = isset($_GET['tarea']) ? max(0, min($nTareas, (int) $_GET['tarea'])) : (isset($_POST['tarea']) && $error !== null ? (int) $_POST['tarea'] : 0);
    $nueva = $kTarea >= $nTareas;
    $appCfg = $nueva ? [] : $tareas[$kTarea];
    $examen = (string) ($appCfg['examen'] ?? ($_GET['examen'] ?? ($_POST['examen'] ?? $est['examen'])));
    if (!isset(Osce::EXAMENES[$examen])) {
        $examen = 'peatc';
    }
    $modulo = OsceApp::modulo($examen);
    $casos = OsceApp::casos($modulo);
    $esProtocolo = $est['tipo'] === 'protocolo';
    $esperado = $esProtocolo
        ? ($appCfg['esperado_curvas'] ?? OsceApp::ESPERADO_CURVAS[$examen] ?? [])
        : ($appCfg['esperado'] ?? OsceApp::ESPERADO[$examen] ?? []);
    $puntosItem = [];
    foreach ($appCfg['items'] ?? [] as $it) {
        if (in_array($it['config']['regla'] ?? '', ['param', 'curvas_param'], true)) {
            $puntosItem[$it['config']['clave']] = ['puntaje' => $it['puntaje'], 'critico' => !empty($it['critico'])];
        }
    }
    $estrategia = OsceApp::estrategia($appCfg + ['examen' => $examen]);
    $ondaResp = $appCfg['onda'] ?? OsceApp::ondas($examen)[1][0];
    $sumaPesos = OsceApp::sumaPesos($tareas);
    $variantes = array_values($appCfg['variantes'] ?? []);
    $filasVar = array_merge($variantes, array_fill(0, max(1, 3 - count($variantes)), ['case_id' => '', 'conclusion_esperada' => '']));
    $curvasBase = $modulo === 'VEMP' ? "OD 120\nOD 110\nOD 100\nOI 120\nOI 110\nOI 100"
        : (in_array($examen, ['latencia_media', 'latencia_tardia', 'p300', 'mmn'], true) ? "OD 70\nOI 70"
        : ($examen === 'ecochg' ? "OD 90\nOI 90" : OsceApp::CURVAS_BASE));
    ?>
<div class="card">
    <h2>PC de la estación</h2>
    <p>En el PC de la estación, abre LabSim y en la ventana de ingreso elige <strong>Ingresar con usuario y contraseña → Estación OSCE</strong>. Escribe este código:</p>
    <p class="mono" style="font-size:2.2rem; font-weight:700; letter-spacing:0.08em; margin:0.3rem 0;"><?= htmlspecialchars($appCodigo) ?></p>
    <p class="help">El PC queda como esta estación. Cada alumno escribe su número, que solo sirve en su turno según el reloj; hace las tareas en orden (pasa a la siguiente cuando quiere, sin volver) y al terminar el tiempo la app entrega sola.</p>
    <?php if (!$tareas): ?><p class="text-warn">Falta al menos una tarea con su paciente: sin eso la estación no abre.</p><?php endif; ?>
</div>

<div class="card">
    <h2>Tareas</h2>
    <p class="help">Cada tarea es una competencia corta con su <strong>peso</strong> dentro de la estación: sus puntos se escalan a ese porcentaje, así una tarea con muchos ítems no pesa más que otra con pocos. A cada alumno le toca uno de los pacientes de la tarea según su número (variantes de igual dificultad, para que no sirva pasarse la respuesta).</p>
    <?php if ($tareas): ?>
    <form method="post" id="f-pesos"><?= csrf_field() ?><input type="hidden" name="id" value="<?= $estId ?>"><input type="hidden" name="accion" value="pesos"></form>
    <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>Tarea</th><th>Examen</th><th>Pacientes</th><th>Peso %</th><th></th></tr></thead>
        <tbody>
        <?php foreach ($tareas as $k => $t): ?>
            <tr<?= $k === $kTarea ? ' style="background:var(--color-surface-2, #f3eef2);"' : '' ?>>
                <td><?= $k + 1 ?></td>
                <td><a href="?id=<?= $estId ?>&amp;tarea=<?= $k ?>#contenido"><?= htmlspecialchars((string) $t['titulo']) ?></a></td>
                <td><?= htmlspecialchars(Osce::EXAMENES[$t['examen']] ?? $t['examen']) ?></td>
                <td><?= count($t['variantes'] ?? []) ?></td>
                <td><input form="f-pesos" type="text" inputmode="decimal" name="peso[<?= $k ?>]" value="<?= $fmt($t['peso']) ?>" class="input--narrow"<?= $editable ? '' : ' disabled' ?>></td>
                <td class="row row--gap-sm">
                    <?php if ($editable): foreach ([['tarea_up', '↑', $k > 0], ['tarea_down', '↓', $k < $nTareas - 1], ['tarea_quitar', 'Quitar', true]] as [$acc, $txt, $ver]): if (!$ver) { continue; } ?>
                    <form method="post"<?= $acc === 'tarea_quitar' ? ' onsubmit="return confirm(\'¿Quitar la tarea?\')"' : '' ?>><?= csrf_field() ?><input type="hidden" name="id" value="<?= $estId ?>"><input type="hidden" name="accion" value="<?= $acc ?>"><input type="hidden" name="tarea" value="<?= $k ?>"><button class="btn btn--sm btn--ghost"><?= $txt ?></button></form>
                    <?php endforeach; endif; ?>
                </td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table></div>
    <p class="<?= abs($sumaPesos - 100) > 0.01 ? 'text-warn' : 'help' ?>">Suma de los pesos: <strong><?= $fmt($sumaPesos) ?> %</strong><?= abs($sumaPesos - 100) > 0.01 ? ' (debería ser 100: la nota se calcula igual sobre el total, pero cada peso deja de ser su porcentaje)' : '' ?>
        <?php if ($editable && $nTareas > 1): ?><button form="f-pesos" class="btn btn--sm">Guardar pesos</button><?php endif; ?></p>
    <?php endif; ?>
    <?php if ($editable && $nTareas < 8): ?>
    <form method="get" class="row row--gap-sm row--center" action="#contenido">
        <input type="hidden" name="id" value="<?= $estId ?>"><input type="hidden" name="tarea" value="<?= $nTareas ?>">
        <label class="row row--gap-sm row--center">Agregar tarea de
            <select name="examen" style="width:auto;"><?php foreach (Osce::EXAMENES as $ck => $cr): if ($ck === 'general') { continue; } ?><option value="<?= $ck ?>"><?= htmlspecialchars($cr) ?></option><?php endforeach; ?></select></label>
        <button class="btn btn--sm btn--ghost">Agregar</button>
    </form>
    <?php endif; ?>
</div>

<div class="card" id="contenido">
    <h2><?= $nueva ? 'Nueva tarea' : 'Tarea ' . ($kTarea + 1) . ': ' . htmlspecialchars((string) $appCfg['titulo']) ?> · <?= htmlspecialchars(Osce::EXAMENES[$examen] ?? $examen) ?></h2>
    <form method="post">
        <?= csrf_field() ?>
        <input type="hidden" name="id" value="<?= $estId ?>">
        <input type="hidden" name="accion" value="app">
        <input type="hidden" name="tarea" value="<?= $kTarea ?>">
        <input type="hidden" name="examen" value="<?= htmlspecialchars($examen) ?>">
        <fieldset <?= $editable ? '' : 'disabled' ?> style="border:0; padding:0; margin:0;">
        <div class="row row--gap-lg">
            <label>Nombre de la tarea <input type="text" name="titulo" value="<?= htmlspecialchars((string) ($appCfg['titulo'] ?? (Osce::EXAMENES[$examen] ?? ''))) ?>" maxlength="80"></label>
            <label>Peso (% de la estación) <input type="text" inputmode="decimal" name="peso" value="<?= $fmt($appCfg['peso'] ?? ($nTareas ? max(1, 100 - $sumaPesos) : 100)) ?>" class="input--narrow"></label>
        </div>
        <h3 style="margin-top:0.8rem;">Pacientes (variantes de igual dificultad)</h3>
        <p class="help">Abre el equipo <strong><?= $modulo ?></strong> en <strong><?= htmlspecialchars(OsceApp::PRUEBA_DE_EXAMEN[$examen] ?? 'ABR') ?></strong>. Con 3 pacientes, al N.º 1 le toca el 1.º, al 2 el 2.º, al 3 el 3.º, al 4 de nuevo el 1.º (corrido en cada tarea). Una fila vacía no cuenta.
            <?= $modulo === 'VEMP' ? 'El VEMP de LabSim mide la intensidad en dB SPL (el protocolo dice "100 dB nHL"): escribe tú la intensidad esperada.' : '' ?></p>
        <?php foreach ($filasVar as $vk => $v): ?>
        <div class="row row--gap-lg" style="align-items:flex-start; margin-bottom:0.4rem;">
            <label>Paciente <?= $vk + 1 ?>
                <select name="variantes[<?= $vk ?>][case_id]">
                    <option value="">—</option>
                    <?php foreach ($casos as $c): ?>
                    <option value="<?= htmlspecialchars($c['id']) ?>"<?= ($v['case_id'] ?? '') === $c['id'] ? ' selected' : '' ?>><?= htmlspecialchars($c['rotulo']) ?></option>
                    <?php endforeach; ?>
                </select></label>
            <?php if ($est['tipo'] === 'conclusion'): ?>
            <label style="flex:1 1 24rem;">Conclusión esperada de este paciente (la referencia de la IA)
                <textarea name="variantes[<?= $vk ?>][conclusion_esperada]" rows="3" style="display:block; width:100%;" placeholder="OD: ... OI: ... Conclusión: ..."><?= htmlspecialchars((string) ($v['conclusion_esperada'] ?? '')) ?></textarea></label>
            <?php endif; ?>
        </div>
        <?php endforeach; ?>
        <?php if ($est['tipo'] === 'conclusion'): ?>
        <div class="row row--gap-lg">
            <label>Curvas que registra la app (una por línea)
                <textarea name="curvas" rows="8" style="display:block; width:14rem;"><?= htmlspecialchars(isset($appCfg['curvas']) ? OsceApp::curvasTexto($appCfg['curvas']) : $curvasBase) ?></textarea></label>
        </div>
        <label>Criterios que corrige la IA (uno por línea: <code>texto | puntos</code>)
            <textarea name="criterios" rows="7" style="display:block; width:100%;"><?= htmlspecialchars(OsceApp::criteriosTexto(array_map(static fn ($it) => [$it['texto'], (float) $it['puntaje']], $appCfg['items'] ?? [])
                ?: (OsceApp::CRITERIOS_CONCLUSION[$examen] ?? OsceApp::CRITERIOS_CONCLUSION['otro']))) ?></textarea></label>
        <p class="help">El alumno ve las curvas ya registradas, las marca y escribe hallazgos y conclusión en el informe del equipo. Al entregar, la IA corrige cada criterio contra la conclusión esperada, los datos reales del caso (umbrales, latencias, si había respuesta) y lo que el alumno marcó. Tú revisas y ajustas en "Revisión". Criterios precargados del formato de informe del Protocolo Técnico ORL 2019.</p>
        <?php elseif ($est['tipo'] === 'marcaje'): ?>
        <div class="row row--gap-lg">
            <label>Curvas que registra la app (una por línea: oído e intensidad)
                <textarea name="curvas" rows="8" style="display:block; width:14rem;"><?= htmlspecialchars(isset($appCfg['curvas']) ? OsceApp::curvasTexto($appCfg['curvas']) : $curvasBase) ?></textarea></label>
            <label>Tolerancia de latencia (ms)
                <input type="text" inputmode="decimal" name="tol_ms" value="<?= $fmt($appCfg['tol_ms'] ?? (OsceApp::TOL_MS[$examen] ?? 0.2)) ?>" class="input--narrow"></label>
        </div>
        <?php [$ondasMax, $ondasResto] = OsceApp::ondas($examen); $canalL = OsceApp::CANAL_LECTURA[$examen] ?? null; ?>
        <p class="help">Se evalúan <?= htmlspecialchars(implode(', ', $ondasMax)) ?> en la intensidad más alta de cada oído y <?= htmlspecialchars(implode(', ', $ondasResto)) ?> en las demás (1 punto cada una)<?= $canalL ? ', marcadas en el canal <strong>' . $canalL . '</strong>' : '' ?>.</p>
        <?php else: ?>
        <p class="help"><?= $esProtocolo
            ? '<strong>Parámetros de cada curva registrada:</strong> el puntaje es la proporción de curvas que cumplen.'
            : '<strong>Configuración al entregar.</strong>' ?>
            Esperado: un valor, varios separados por <code>|</code> (cualquiera vale) o un rango <code>10–12</code>. Vacío = no se evalúa. <?= in_array($examen, ['peatc', 'cvemp', 'ovemp'], true) ? 'Precargado del Protocolo Técnico ORL 2019' : 'El protocolo ORL 2019 no trae esta prueba: precargado con la configuración de rutina de LabSim (la de la clase), ajústala si quieres' ?><?= $examen === 'peatc' ? ' (la ventana del protocolo dice "10 s", es 10 ms; ganancia "10k" = 10000)' : '' ?>.</p>
        <div class="table-wrap"><table>
            <thead><tr><th>Parámetro</th><th>Esperado</th><th>Puntos</th><th>Crítico</th></tr></thead>
            <tbody>
            <?php foreach (OsceApp::parametros($examen) as $clave => [$fuente, $rotulo]):
                if (!$esProtocolo && $clave === 'emg_ok') { continue; }
                $itp = $puntosItem[$clave] ?? null; ?>
                <tr>
                    <td><?= htmlspecialchars($rotulo) ?><?= $modulo === 'ABR' && !$esProtocolo ? ' <span class="help help--xs">' . ($fuente === 'equipo' ? 'parámetros avanzados' : 'panel') . '</span>' : '' ?></td>
                    <td><input type="text" name="esperado[<?= $clave ?>]" value="<?= htmlspecialchars((string) ($esperado[$clave] ?? '')) ?>"></td>
                    <td><input type="text" inputmode="decimal" name="puntos[<?= $clave ?>]" value="<?= $itp ? $fmt($itp['puntaje']) : '1' ?>" class="input--narrow"></td>
                    <td><input type="checkbox" name="critico[<?= $clave ?>]" value="1"<?= $itp && $itp['critico'] ? ' checked' : '' ?>></td>
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
        <h3 style="margin-top:1rem;">Estrategias extra según el caso</h3>
        <p class="help">Lo que este caso en particular pide además de la escalera: se cumple si el alumno registró <strong>alguna curva</strong> con ese parámetro en ese valor. Activa las que correspondan al caso (vienen apagadas) y agrega las tuyas en las filas vacías. Por defecto son bonificación.</p>
        <?php $extrasEst = OsceApp::extras($appCfg + ['examen' => $examen]); $parExtra = OsceApp::parametrosExtra($examen);
              $filasExtra = array_merge($extrasEst, array_fill(0, 3, ['activa' => false, 'texto' => '', 'clave' => 'stim', 'esperado' => '', 'puntos' => 1, 'bonus' => true])); ?>
        <div class="table-wrap"><table>
            <thead><tr><th>Activa</th><th>Estrategia</th><th>Parámetro</th><th>Valor en alguna curva</th><th>Puntos</th><th>Bonificación</th></tr></thead>
            <tbody>
            <?php foreach ($filasExtra as $k => $x): ?>
                <tr>
                    <td><input type="checkbox" name="extras[<?= $k ?>][activa]" value="1"<?= !empty($x['activa']) ? ' checked' : '' ?>></td>
                    <td><input type="text" name="extras[<?= $k ?>][texto]" value="<?= htmlspecialchars((string) $x['texto']) ?>" placeholder="Qué hace el alumno"></td>
                    <td><select name="extras[<?= $k ?>][clave]" style="width:auto;">
                        <?php foreach ($parExtra as $ck => $cr): ?><option value="<?= $ck ?>"<?= $ck === $x['clave'] ? ' selected' : '' ?>><?= htmlspecialchars($cr) ?></option><?php endforeach; ?>
                    </select></td>
                    <td><input type="text" name="extras[<?= $k ?>][esperado]" value="<?= htmlspecialchars((string) $x['esperado']) ?>" placeholder="valor, a | b o 1–120"></td>
                    <td><input type="text" inputmode="decimal" name="extras[<?= $k ?>][puntos]" value="<?= $fmt($x['puntos']) ?>" class="input--narrow"></td>
                    <td><input type="checkbox" name="extras[<?= $k ?>][bonus]" value="1"<?= !empty($x['bonus']) ? ' checked' : '' ?>></td>
                </tr>
            <?php endforeach; ?>
            </tbody>
        </table></div>
        <?php endif; ?>
        <?php if ($editable): ?><button type="submit" class="btn btn--sm"><?= $nueva ? 'Agregar tarea' : 'Guardar tarea' ?></button><?php endif; ?>
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
