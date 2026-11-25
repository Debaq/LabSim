<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Osce.php';
require_once __DIR__ . '/../../src/OscePauta.php';
require_once __DIR__ . '/../../src/OsceApp.php';
require_once __DIR__ . '/../../src/QrSvg.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * OSCE del curso: lista, creación y armado (configuración, estaciones,
 * alumnos con código y QR). Plan en docs/osce_plan.md. El reloj en vivo
 * está en osce_vivo.php.
 */

$me = Auth::requireAdminSession();
$esAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$misCursos = $esAdmin ? null : Courses::teacherCourseIds((int) $me['id']);
$ctx = admin_course_context($me);
$cursosElegibles = admin_context_courses($me);

$id = (int) ($_GET['id'] ?? $_POST['id'] ?? 0);
$osce = $id > 0 ? Osce::obtener($id) : null;
if ($id > 0 && ($osce === null || !Courses::canAdminister((int) $osce['course_id'], $me))) {
    http_response_code(404);
    exit('OSCE no encontrado.');
}

/** URL absoluta de la página del alumno (la que abre el QR). */
$urlAlumno = static fn (string $token): string => Osce::urlPublica('student/osce.php?t=' . rawurlencode($token));

$min = static fn (int $s): string => rtrim(rtrim(number_format($s / 60, 1, ',', ''), '0'), ',');

// Hora local de inicio (si ya partió, la real; si no, la programada).
$inicioEpoch = static function (array $o): ?int {
    if ($o['inicio_epoch'] !== null) {
        return (int) $o['inicio_epoch'] + (int) $o['pausado_acum_s'];
    }
    if ($o['inicio_programado'] === '') {
        return null;
    }
    $t = strtotime($o['inicio_programado']);
    return $t === false ? null : $t;
};

// -- Tarjetas para imprimir (página suelta, sin el layout del panel) --------
// Se imprimen SIN NOMBRE: el número se sortea en papel el día del OSCE. Una
// sola pieza, el gafete, que va en el pecho a la vista de los evaluadores:
// el número grande y, abajo y en chico, el QR y el código (él: "así no
// imprimo dos cosas aparte"). Con el QR el alumno amarra la tarjeta y ve su
// avance y su nota (student/osce.php). Dos por fila en A4.
if ($osce !== null && isset($_GET['tarjetas'])) {
    $parts = Osce::participantes($id);
    $estaciones = Osce::estaciones($id);
    $S = count($estaciones);
    $cfg = Osce::cfgReloj($osce, $S, count($parts));
    $t0 = $inicioEpoch($osce);
    header('Content-Type: text/html; charset=utf-8');
    ?>
<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>Tarjetas OSCE — <?= htmlspecialchars($osce['nombre']) ?></title>
<style>
body { font-family: system-ui, sans-serif; margin: 0; color: #111; }
.hoja { display: grid; grid-template-columns: repeat(2, 92mm); gap: 4mm; justify-content: center; }
.gafete { width: 92mm; height: 64mm; border: 1px dashed #999; box-sizing: border-box; padding: 3mm 4mm; break-inside: avoid;
          display: grid; grid-template-rows: auto 1fr auto; }
.gafete .osce { font-size: 8pt; color: #666; text-transform: uppercase; letter-spacing: 1pt; text-align: center; }
.gafete .num { font-size: 92pt; font-weight: 900; color: #5d1049; line-height: .85; text-align: center; align-self: center; }
.gafete .pie { display: grid; grid-template-columns: auto 1fr; gap: 3mm; align-items: center; }
.gafete .pie svg { width: 17mm; height: 17mm; display: block; }
.gafete .cod { font: 700 9pt ui-monospace, monospace; letter-spacing: .5pt; }
.gafete .det { font-size: 6.5pt; color: #333; line-height: 1.3; }
.no-print { padding: 1rem; }
@media print { .no-print { display: none; } @page { margin: 8mm; } }
</style></head><body>
<div class="no-print"><button onclick="window.print()">Imprimir</button> · <?= count($parts) ?> tarjetas · <a href="osce.php?id=<?= $id ?>">Volver</a>
    · Se recorta por la línea punteada. El gafete va en el pecho; el alumno escanea su QR apenas lo saca, así la tarjeta queda a su nombre.</div>
<div class="hoja">
<?php foreach ($parts as $p):
    $entra = null;
    if ($S > 0 && ($cfg['modo'] ?? '') === 'cadena') {
        $g = Osce::grupo((int) $p['numero'], $cfg['por_turno']);
        $tp = $g === 0 ? 0 : Osce::turnoPaciente($g, $cfg['grupos']);
        $entra = Osce::inicioSlot($cfg, 0, (int) $tp);
    } elseif ($S > 0) {
        $entra = Osce::inicioSlot($cfg, (int) $p['vuelta'], 0);
    }
    ?>
<div class="gafete">
    <div class="osce"><?= htmlspecialchars($osce['nombre']) ?></div>
    <div class="num"><?= (int) $p['numero'] ?></div>
    <div class="pie">
        <?= QrSvg::svg($urlAlumno((string) $p['token']), 3) ?>
        <div>
            <div class="cod"><?= htmlspecialchars($p['codigo']) ?></div>
            <div class="det">Escanea el QR y elige tu nombre: tu avance y tu nota.
                <?php if ($entra !== null): ?><br>Limpieza: <strong><?= $t0 !== null ? date('H:i', $t0 + $entra) : '+' . $min($entra) . ' min' ?></strong> · <?php else: ?><br><?php endif; ?>En las estaciones escribe tu número.</div>
        </div>
    </div>
</div>
<?php endforeach; ?>
</div>
</body></html>
<?php
    exit;
}

// -- Acciones ---------------------------------------------------------------
$error = null;
$success = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $accion = (string) ($_POST['accion'] ?? '');
    try {
        if ($accion === 'crear') {
            $courseId = (int) ($_POST['course_id'] ?? 0);
            Courses::assertAdministers($courseId, $me);
            $cfg = Osce::limpiarConfig($_POST);
            $nuevo = Osce::crear($courseId, $cfg, (int) $me['id'], !empty($_POST['estaciones_base']));
            // Las estaciones de pauta parten con la del protocolo de su examen.
            foreach (Osce::estaciones($nuevo) as $e) {
                if ($e['tipo'] === 'pauta_docente') {
                    OscePauta::cargarBase((int) $e['id'], (string) $e['examen']);
                }
            }
            Osce::sincronizarAlumnos($nuevo);
            AdminAudit::log($me, 'osce_crear', ['osce_id' => $nuevo, 'course_id' => $courseId]);
            header('Location: osce.php?id=' . $nuevo . '&creado=1');
            exit;
        }
        if ($osce === null) {
            throw new InvalidArgumentException('OSCE no encontrado.');
        }
        $estId = (int) ($_POST['estacion_id'] ?? 0);
        switch ($accion) {
            case 'config':
                Osce::actualizarConfig($id, Osce::limpiarConfig($_POST));
                $success = 'Configuración guardada.';
                break;
            case 'est_add':
                Osce::agregarEstacion($id, $_POST);
                $success = 'Estación agregada.';
                break;
            case 'est_edit':
                Osce::editarEstacion($id, $estId, $_POST);
                $success = 'Estación guardada.';
                break;
            case 'est_del':
                Osce::quitarEstacion($id, $estId);
                $success = 'Estación quitada.';
                break;
            case 'est_up':
            case 'est_down':
                Osce::moverEstacion($id, $estId, $accion === 'est_up' ? -1 : 1);
                break;
            case 'sync':
                $r = Osce::sincronizarAlumnos($id);
                $success = "Tarjetas al día con el curso: {$r['agregados']} nuevas, {$r['quitados']} quitadas.";
                break;
            case 'asignar':
                $uid = (string) ($_POST['user_id'] ?? '');
                Osce::asignarTarjeta($id, (int) ($_POST['participante_id'] ?? 0), $uid === '' ? null : (int) $uid);
                $success = $uid === '' ? 'Tarjeta sin dueño.' : 'Tarjeta asignada.';
                break;
            case 'quitar':
                Osce::quitarParticipante($id, (int) ($_POST['participante_id'] ?? 0));
                $success = 'Alumno quitado del OSCE.';
                break;
            case 'publicar':
            case 'despublicar':
                Osce::publicar($id, $accion === 'publicar');
                $success = $accion === 'publicar'
                    ? 'Resultados publicados: cada alumno los ve (y puede hacer réplica) desde su QR.'
                    : 'Publicación retirada.';
                break;
            case 'eliminar':
                Osce::eliminar($id);
                AdminAudit::log($me, 'osce_eliminar', ['osce_id' => $id]);
                header('Location: osce.php');
                exit;
            default:
                throw new InvalidArgumentException('Acción desconocida.');
        }
        if ($accion === 'est_add' || $accion === 'est_edit') {
            // Una estación de pauta sin ítems parte con la del protocolo de su examen.
            foreach (Osce::estaciones($id) as $e) {
                if ($e['tipo'] === 'pauta_docente' && !OscePauta::items((int) $e['id'])) {
                    OscePauta::cargarBase((int) $e['id'], (string) $e['examen']);
                }
            }
        }
        AdminAudit::log($me, 'osce_' . $accion, ['osce_id' => $id]);
        $osce = Osce::obtener($id);
    } catch (InvalidArgumentException $e) {
        $error = $e->getMessage();
    }
}
if (isset($_GET['creado'])) {
    $success = 'OSCE creado con una tarjeta por alumno del curso. Revisa las estaciones y luego imprime las tarjetas.';
}

$tipoOpts = static function (string $sel): string {
    $h = '';
    foreach (Osce::TIPOS as $k => $v) {
        $h .= '<option value="' . $k . '"' . ($k === $sel ? ' selected' : '') . '>' . htmlspecialchars($v) . '</option>';
    }
    return $h;
};
$examenOpts = static function (string $sel): string {
    $h = '';
    foreach (Osce::EXAMENES as $k => $v) {
        $h .= '<option value="' . $k . '"' . ($k === $sel ? ' selected' : '') . '>' . htmlspecialchars($v) . '</option>';
    }
    return $h;
};

// -- Lista + crear ----------------------------------------------------------
if ($osce === null) {
    $ids = $ctx !== null ? [$ctx] : $misCursos;
    $lista = Osce::porCurso($ids);
    admin_header('OSCE', $me);
    ?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>

<div class="card">
    <h2>Evaluaciones OSCE</h2>
    <?php if (!$lista): ?>
        <p class="empty-state">Todavía no hay OSCE<?= $ctx !== null ? ' en este curso' : '' ?>.</p>
    <?php else: ?>
    <div class="table-wrap"><table>
        <thead><tr><th>Nombre</th><th>Curso</th><th>Inicio</th><th>Estaciones</th><th>Alumnos</th><th>Estado</th></tr></thead>
        <tbody>
        <?php foreach ($lista as $o): ?>
            <tr>
                <td><a href="osce.php?id=<?= (int) $o['id'] ?>"><?= htmlspecialchars($o['nombre']) ?></a></td>
                <td><?= htmlspecialchars($o['curso']) ?></td>
                <td class="nowrap"><?= htmlspecialchars($o['inicio_programado'] ?: '—') ?></td>
                <td><?= (int) $o['n_estaciones'] ?></td>
                <td><?= (int) $o['n_alumnos'] ?></td>
                <td><span class="tag<?= $o['estado'] === 'en_curso' ? ' tag--warn' : ($o['estado'] === 'borrador' ? ' tag--muted' : ' tag--success') ?>"><?= htmlspecialchars(Osce::ESTADOS[$o['estado']] ?? $o['estado']) ?></span></td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table></div>
    <?php endif; ?>
</div>

<div class="card">
    <h2>Nuevo OSCE</h2>
    <?php if (!$cursosElegibles): ?>
        <p class="muted">No tienes cursos a cargo.</p>
    <?php else: ?>
    <form method="post">
        <?= csrf_field() ?>
        <input type="hidden" name="accion" value="crear">
        <label>Curso
            <select name="course_id" required>
                <?php foreach ($cursosElegibles as $c): ?>
                <option value="<?= (int) $c['id'] ?>"<?= $ctx === (int) $c['id'] ? ' selected' : '' ?>><?= htmlspecialchars($c['name']) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Nombre <input type="text" name="nombre" required maxlength="120" placeholder="Prueba práctica electrofisiología"></label>
        <label>Inicio <input type="datetime-local" name="inicio_programado"></label>
        <div class="row row--gap-lg">
            <label>Rotación
                <select name="rotacion" style="width:auto;">
                    <option value="cadena" selected>En cadena: todos parten en la 1 y entran por grupos</option>
                    <option value="vueltas">En vueltas: cada uno parte en una estación distinta</option>
                </select></label>
            <label>Alumnos por estación a la vez <input type="number" name="por_turno" value="2" min="1" max="8" class="input--narrow"></label>
        </div>
        <div class="row row--gap-lg">
            <label>Duración de la estación (min) <input type="number" name="duracion_min" value="8" min="1" max="60" step="0.5" class="input--narrow"></label>
            <label>Pausa entre estaciones (min) <input type="number" name="pausa_min" value="2" min="0" max="30" step="0.5" class="input--narrow"></label>
            <label>Pausa entre vueltas (min, solo en vueltas) <input type="number" name="pausa_vueltas_min" value="10" min="0" max="120" step="1" class="input--narrow"></label>
            <label>Circuitos (solo en vueltas) <input type="number" name="circuitos" value="1" min="1" max="6" class="input--narrow"></label>
        </div>
        <div class="row row--gap-lg">
            <label>Exigencia (%) <input type="number" name="exigencia" value="60" min="30" max="90" class="input--narrow"></label>
            <label>Nota de aprobación <input type="number" name="nota_aprobacion" value="4.0" min="1" max="7" step="0.1" class="input--narrow"></label>
        </div>
        <label class="inline-check"><input type="checkbox" name="estaciones_base" value="1" checked>
            Partir con las 6 estaciones de electrofisiología (limpieza y preparación, preguntas, configuración, marcaje, protocolo, conclusión)</label>
        <p class="help">Se crea una tarjeta numerada por alumno del curso (con código y QR, sin nombre: el número se sortea en papel y cada uno amarra la suya escaneando el QR). En cadena, "alumnos por estación" es cuántos se evalúan a la vez en cada estación: si entran de a 4 a la limpieza (2 limpian a 2), son 2. Todo se puede cambiar hasta que el OSCE parta.</p>
        <button type="submit" class="btn">Crear OSCE</button>
    </form>
    <?php endif; ?>
</div>
<?php
    admin_footer();
    exit;
}

// -- Detalle ----------------------------------------------------------------
$estaciones = Osce::estaciones($id);
$parts = Osce::participantes($id);
$S = count($estaciones);
$N = count($parts);
$cfg = Osce::cfgReloj($osce, $S, $N);
$total = Osce::duracionTotal($cfg);
$t0 = $inicioEpoch($osce);
$editable = $osce['estado'] === 'borrador';
$cadena = ($cfg['modo'] ?? '') === 'cadena';
$hhmm = static fn (int $seg): string => $t0 !== null ? date('H:i', $t0 + $seg) : '+' . $min($seg) . ' min';
$alumnosCurso = Osce::alumnosDelCurso((int) $osce['course_id']);
$porId = [];
foreach ($parts as $p) {
    if ($p['user_id'] !== null) {
        $porId[(int) $p['user_id']] = (int) $p['numero'];
    }
}
$porEstacionPeso = array_sum(array_map(static fn ($e) => (float) $e['peso'], $estaciones));

admin_header('OSCE · ' . $osce['nombre'], $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<p class="row row--between">
    <a href="osce.php">← Todos los OSCE</a>
    <span class="row row--gap-sm">
        <a class="btn btn--sm" href="osce_vivo.php?id=<?= $id ?>">Panel de control</a>
        <a class="btn btn--sm btn--secondary" href="osce.php?id=<?= $id ?>&amp;tarjetas=1" target="_blank">Tarjetas para imprimir</a>
    </span>
</p>

<div class="card">
    <h2>Resumen</h2>
    <p>
        <strong><?= htmlspecialchars($osce['curso']) ?></strong> ·
        <span class="tag<?= $editable ? ' tag--muted' : ' tag--warn' ?>"><?= htmlspecialchars(Osce::ESTADOS[$osce['estado']] ?? $osce['estado']) ?></span>
    </p>
    <?php if ($osce['estado'] === 'cerrado' || $osce['estado'] === 'publicado'): ?>
    <form method="post" class="row row--gap-sm row--center">
        <?= csrf_field() ?>
        <input type="hidden" name="id" value="<?= $id ?>">
        <?php if ($osce['estado'] === 'cerrado'): ?>
        <button type="submit" name="accion" value="publicar" class="btn btn--sm" onclick="return confirm('¿Publicar? Cada alumno verá su nota, el detalle y el feedback desde su QR, y podrá hacer réplica en las preguntas.')">Publicar resultados</button>
        <span class="help">Antes de publicar, revisa las estaciones de preguntas (corrección IA y feedback).</span>
        <?php else: ?>
        <button type="submit" name="accion" value="despublicar" class="btn btn--sm btn--secondary">Retirar publicación</button>
        <span class="help">Publicado <?= htmlspecialchars(Clock::fromUtc((string) $osce['publicado_at'])->format('d-m-Y H:i')) ?>. Las réplicas llegan a la revisión de cada estación de preguntas.</span>
        <?php endif; ?>
    </form>
    <?php endif; ?>
    <?php if ($S === 0 || $N === 0): ?>
        <p class="text-warn">Faltan <?= $S === 0 ? 'estaciones' : 'tarjetas' ?> para calcular el horario.</p>
    <?php elseif ($cadena):
        $k = $cfg['por_turno']; ?>
        <p>
            <?= $N ?> tarjetas · <?= $S ?> estaciones · <strong><?= $k ?> por estación a la vez</strong>
            (entran de a <?= 2 * $k ?> a la limpieza: <?= $k ?> limpian a <?= $k ?>) →
            <?= $cfg['grupos'] ?> grupos, <strong><?= $cfg['turnos'] ?> turnos</strong>.
        </p>
        <p>
            Cada turno <?= $min((int) $osce['duracion_s']) ?> min + <?= $min((int) $osce['pausa_s']) ?> min de cambio.
            Duración total: <strong><?= intdiv($total, 3600) ?> h <?= str_pad((string) intdiv($total % 3600, 60), 2, '0', STR_PAD_LEFT) ?> min</strong>
            <?php if ($t0 !== null): ?>(<?= date('d-m-Y H:i', $t0) ?> → <?= date('H:i', $t0 + $total) ?>)<?php endif; ?>.
            Necesitas <?= $k ?> puesto<?= $k > 1 ? 's' : '' ?> por estación (camillas, tablets, PCs).
            El primer grupo se queda hasta el final: es el paciente del último.
        </p>
        <div class="table-wrap"><table>
            <thead><tr><th>Grupo</th><th>Números</th><th>Paciente en limpieza</th><th>Limpia (estación 1)</th><th>Termina</th></tr></thead>
            <tbody>
            <?php for ($g = 0; $g < $cfg['grupos']; $g++):
                $desde = $g * $k + 1;
                $hasta = min($N, ($g + 1) * $k);
                $tp = Osce::turnoPaciente($g, $cfg['grupos']);
                $fin = Osce::inicioSlot($cfg, 0, $g + $S - 1) + (int) $osce['duracion_s']; ?>
                <tr><td><?= $g + 1 ?></td>
                    <td>N.º <?= $desde ?><?= $hasta > $desde ? '–' . $hasta : '' ?></td>
                    <td><?= $tp === null ? '—' : $hhmm(Osce::inicioSlot($cfg, 0, $tp)) . ($g === 0 ? ' (al final)' : '') ?></td>
                    <td><?= $hhmm(Osce::inicioSlot($cfg, 0, $g)) ?></td>
                    <td><?= $hhmm($fin) ?></td></tr>
            <?php endfor; ?>
            </tbody>
        </table></div>
    <?php else: ?>
        <p>
            <?= $N ?> tarjetas · <?= $S ?> estaciones × <?= (int) $osce['circuitos'] ?> circuito<?= (int) $osce['circuitos'] > 1 ? 's' : '' ?>
            = <?= $S * (int) $osce['circuitos'] ?> puestos por vuelta →
            <strong><?= $cfg['vueltas'] ?> vuelta<?= $cfg['vueltas'] > 1 ? 's' : '' ?></strong>.
        </p>
        <p>
            Cada estación <?= $min((int) $osce['duracion_s']) ?> min + <?= $min((int) $osce['pausa_s']) ?> min de cambio;
            <?= $min((int) $osce['pausa_vueltas_s']) ?> min entre vueltas.
            Duración total: <strong><?= intdiv($total, 3600) ?> h <?= str_pad((string) intdiv($total % 3600, 60), 2, '0', STR_PAD_LEFT) ?> min</strong>
            <?php if ($t0 !== null): ?>(<?= date('d-m-Y H:i', $t0) ?> → <?= date('H:i', $t0 + $total) ?>)<?php endif; ?>
        </p>
        <div class="table-wrap table-wrap--narrow"><table>
            <thead><tr><th>Vuelta</th><th>Empieza</th><th>Termina</th></tr></thead>
            <tbody>
            <?php for ($v = 0; $v < $cfg['vueltas']; $v++):
                $a = Osce::inicioSlot($cfg, $v, 0);
                $b = Osce::inicioSlot($cfg, $v, $S - 1) + (int) $osce['duracion_s']; ?>
                <tr><td><?= $v + 1 ?></td><td><?= $hhmm($a) ?></td><td><?= $hhmm($b) ?></td></tr>
            <?php endfor; ?>
            </tbody>
        </table></div>
    <?php endif; ?>
</div>

<div class="card">
    <h2>Configuración</h2>
    <?php if (!$editable): ?><p class="help">El OSCE ya partió: la configuración queda fija.</p><?php endif; ?>
    <form method="post">
        <?= csrf_field() ?>
        <input type="hidden" name="accion" value="config">
        <input type="hidden" name="id" value="<?= $id ?>">
        <fieldset <?= $editable ? '' : 'disabled' ?> style="border:0; padding:0; margin:0;">
        <label>Nombre <input type="text" name="nombre" required maxlength="120" value="<?= htmlspecialchars($osce['nombre']) ?>"></label>
        <label>Inicio <input type="datetime-local" name="inicio_programado" value="<?= htmlspecialchars(str_replace(' ', 'T', $osce['inicio_programado'])) ?>"></label>
        <div class="row row--gap-lg">
            <label>Rotación
                <select name="rotacion" style="width:auto;">
                    <option value="cadena"<?= $cadena ? ' selected' : '' ?>>En cadena: todos parten en la 1 y entran por grupos</option>
                    <option value="vueltas"<?= $cadena ? '' : ' selected' ?>>En vueltas: cada uno parte en una estación distinta</option>
                </select></label>
            <label>Alumnos por estación a la vez <input type="number" name="por_turno" value="<?= (int) $osce['por_turno'] ?>" min="1" max="8" class="input--narrow"></label>
        </div>
        <div class="row row--gap-lg">
            <label>Duración de la estación (min) <input type="number" name="duracion_min" value="<?= $osce['duracion_s'] / 60 ?>" min="1" max="60" step="0.5" class="input--narrow"></label>
            <label>Pausa entre estaciones (min) <input type="number" name="pausa_min" value="<?= $osce['pausa_s'] / 60 ?>" min="0" max="30" step="0.5" class="input--narrow"></label>
            <label>Pausa entre vueltas (min, solo en vueltas) <input type="number" name="pausa_vueltas_min" value="<?= $osce['pausa_vueltas_s'] / 60 ?>" min="0" max="120" class="input--narrow"></label>
            <label>Circuitos (solo en vueltas) <input type="number" name="circuitos" value="<?= (int) $osce['circuitos'] ?>" min="1" max="6" class="input--narrow"></label>
        </div>
        <div class="row row--gap-lg">
            <label>Exigencia (%) <input type="number" name="exigencia" value="<?= (int) $osce['exigencia'] ?>" min="30" max="90" class="input--narrow"></label>
            <label>Nota de aprobación <input type="number" name="nota_aprobacion" value="<?= htmlspecialchars((string) $osce['nota_aprobacion']) ?>" min="1" max="7" step="0.1" class="input--narrow"></label>
        </div>
        <?php if ($editable): ?><button type="submit" class="btn">Guardar configuración</button><?php endif; ?>
        </fieldset>
    </form>
</div>

<div class="card">
    <h2>Estaciones (orden del circuito)</h2>
    <p class="help"><?= $cadena
        ? 'Todos parten en la 1 y avanzan en este orden: la primera debe ser la de limpieza (ahí el grupo que entra hace de paciente del que limpia).'
        : 'Cada alumno parte en una estación y avanza a la siguiente; al terminar la última sigue con la primera.' ?> El peso define cuánto vale cada estación en la nota final.</p>
    <?php if (!$estaciones): ?>
        <p class="empty-state">Sin estaciones.</p>
    <?php else: ?>
    <div class="table-wrap"><table>
        <thead><tr><th>#</th><th>Título</th><th>Tipo</th><th>Examen</th><th>Peso</th><th></th></tr></thead>
        <tbody>
        <?php foreach ($estaciones as $k => $e): $fid = 'est' . (int) $e['id']; ?>
            <tr>
                <td><?= $k + 1 ?></td>
                <?php if ($editable): ?>
                <td><input form="<?= $fid ?>" type="text" name="titulo" value="<?= htmlspecialchars($e['titulo']) ?>" maxlength="120"></td>
                <td><select form="<?= $fid ?>" name="tipo"><?= $tipoOpts($e['tipo']) ?></select></td>
                <td><select form="<?= $fid ?>" name="examen"><?= $examenOpts($e['examen']) ?></select></td>
                <td><input form="<?= $fid ?>" type="number" name="peso" value="<?= htmlspecialchars((string) $e['peso']) ?>" min="0.1" max="100" step="0.1" class="input--narrow">
                    <span class="help help--xs"><?= $porEstacionPeso > 0 ? round(100 * (float) $e['peso'] / $porEstacionPeso) : 0 ?> %</span></td>
                <td class="nowrap">
                    <form id="<?= $fid ?>" method="post" style="display:inline">
                        <?= csrf_field() ?>
                        <input type="hidden" name="id" value="<?= $id ?>">
                        <input type="hidden" name="estacion_id" value="<?= (int) $e['id'] ?>">
                        <a href="osce_estacion.php?id=<?= (int) $e['id'] ?>" class="btn btn--xs btn--secondary">Contenido</a>
                        <button type="submit" name="accion" value="est_edit" class="btn btn--xs">Guardar</button>
                        <button type="submit" name="accion" value="est_up" class="btn btn--xs btn--ghost" title="Subir"<?= $k === 0 ? ' disabled' : '' ?>>↑</button>
                        <button type="submit" name="accion" value="est_down" class="btn btn--xs btn--ghost" title="Bajar"<?= $k === $S - 1 ? ' disabled' : '' ?>>↓</button>
                        <button type="submit" name="accion" value="est_del" class="btn btn--xs btn--danger" onclick="return confirm('¿Quitar esta estación?')">Quitar</button>
                    </form>
                </td>
                <?php else: ?>
                <td><?= htmlspecialchars($e['titulo']) ?></td>
                <td><?= htmlspecialchars(Osce::TIPOS[$e['tipo']] ?? $e['tipo']) ?></td>
                <td><?= htmlspecialchars(Osce::EXAMENES[$e['examen']] ?? $e['examen']) ?></td>
                <td><?= htmlspecialchars((string) $e['peso']) ?> (<?= $porEstacionPeso > 0 ? round(100 * (float) $e['peso'] / $porEstacionPeso) : 0 ?> %)</td>
                <td class="nowrap">
                    <a href="osce_estacion.php?id=<?= (int) $e['id'] ?>" class="btn btn--xs btn--secondary">Contenido</a>
                    <?php if ($e['tipo'] === 'pauta_docente'): ?><a href="osce_evaluar.php?estacion=<?= (int) $e['id'] ?>" class="btn btn--xs">Evaluar</a><?php endif; ?>
                    <?php if ($e['tipo'] === 'preguntas'): ?><a href="osce_revision.php?estacion=<?= (int) $e['id'] ?>" class="btn btn--xs">Revisión</a><?php endif; ?>
                    <?php if (OsceApp::esApp((string) $e['tipo'])): ?><a href="osce_app_revision.php?estacion=<?= (int) $e['id'] ?>" class="btn btn--xs">Revisión</a><?php endif; ?>
                </td>
                <?php endif; ?>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table></div>
    <?php endif; ?>
    <?php if ($editable): ?>
    <form method="post" class="row row--gap-sm row--baseline" style="margin-top:0.8rem; flex-wrap:wrap;">
        <?= csrf_field() ?>
        <input type="hidden" name="accion" value="est_add">
        <input type="hidden" name="id" value="<?= $id ?>">
        <input type="text" name="titulo" placeholder="Título" maxlength="120" aria-label="Título" style="width:auto; flex:1 1 14rem;">
        <select name="tipo" aria-label="Tipo" style="width:auto;"><?= $tipoOpts('pauta_docente') ?></select>
        <select name="examen" aria-label="Examen" style="width:auto;"><?= $examenOpts('peatc') ?></select>
        <label class="row row--gap-sm row--baseline" style="margin:0;">Peso <input type="number" name="peso" value="1" min="0.1" max="100" step="0.1" class="input--narrow"></label>
        <button type="submit" class="btn btn--sm">Agregar estación</button>
    </form>
    <?php endif; ?>
</div>

<div class="card">
    <h2>Tarjetas (<?= $N ?>) · <?= count($porId) ?> con dueño</h2>
    <p class="help">El día del OSCE cada alumno saca una tarjeta al azar, escanea el QR y elige su nombre. Aquí ves quién tiene cada una y puedes corregir.</p>
    <?php if ($editable): ?>
    <form method="post" class="row row--gap-sm" style="margin-bottom:0.8rem;">
        <?= csrf_field() ?>
        <input type="hidden" name="id" value="<?= $id ?>">
        <button type="submit" name="accion" value="sync" class="btn btn--sm">Ajustar tarjetas al curso (<?= count($alumnosCurso) ?> alumnos)</button>
    </form>
    <?php endif; ?>
    <?php if (!$parts): ?>
        <p class="empty-state">Sin tarjetas. El curso no tiene alumnos inscritos o hay que ajustarlas.</p>
    <?php else: ?>
    <div class="table-wrap"><table>
        <thead><tr><th>N.º</th><th>Código</th><th>Alumno</th><th><?= $cadena ? 'Paciente / limpia' : 'Vuelta · parte en' ?></th><th></th></tr></thead>
        <tbody>
        <?php foreach ($parts as $p):
            if ($cadena && $S > 0) {
                $g = Osce::grupo((int) $p['numero'], $cfg['por_turno']);
                $tp = Osce::turnoPaciente($g, $cfg['grupos']);
                $cuando = ($tp === null ? '' : $hhmm(Osce::inicioSlot($cfg, 0, $tp)) . ' / ') . $hhmm(Osce::inicioSlot($cfg, 0, $g));
            } else {
                $cuando = 'Vuelta ' . ((int) $p['vuelta'] + 1) . ' · ' . ($S > 0 ? $estaciones[Osce::estacionEn((int) $p['puesto'], 0, $S)]['titulo'] : '—');
            } ?>
            <tr>
                <td><strong style="font-size:1.15rem;"><?= (int) $p['numero'] ?></strong></td>
                <td class="mono"><?= htmlspecialchars($p['codigo']) ?></td>
                <td>
                    <form method="post" class="row row--gap-sm row--center" style="margin:0; flex-wrap:nowrap;">
                        <?= csrf_field() ?>
                        <input type="hidden" name="id" value="<?= $id ?>">
                        <input type="hidden" name="participante_id" value="<?= (int) $p['id'] ?>">
                        <input type="hidden" name="accion" value="asignar">
                        <select name="user_id" style="width:auto; max-width:16rem;" onchange="this.form.submit()" aria-label="Alumno de la tarjeta <?= (int) $p['numero'] ?>">
                            <option value="">— sin dueño —</option>
                            <?php foreach ($alumnosCurso as $u): $tiene = $porId[(int) $u['id']] ?? null; ?>
                            <option value="<?= (int) $u['id'] ?>"<?= (int) $p['user_id'] === (int) $u['id'] ? ' selected' : '' ?><?= $tiene !== null && (int) $p['user_id'] !== (int) $u['id'] ? ' disabled' : '' ?>><?= htmlspecialchars((string) $u['display_name']) ?><?= $tiene !== null && (int) $p['user_id'] !== (int) $u['id'] ? " (N.º {$tiene})" : '' ?></option>
                            <?php endforeach; ?>
                        </select>
                        <noscript><button type="submit" class="btn btn--xs">Guardar</button></noscript>
                    </form>
                </td>
                <td class="nowrap"><?= htmlspecialchars($cuando) ?></td>
                <td class="nowrap">
                    <a href="<?= htmlspecialchars($urlAlumno((string) $p['token'])) ?>" target="_blank" class="btn btn--xs btn--ghost">Su página</a>
                    <?php if ($editable && $p['user_id'] === null): ?>
                    <form method="post" style="display:inline">
                        <?= csrf_field() ?>
                        <input type="hidden" name="id" value="<?= $id ?>">
                        <input type="hidden" name="participante_id" value="<?= (int) $p['id'] ?>">
                        <button type="submit" name="accion" value="quitar" class="btn btn--xs btn--danger" onclick="return confirm('¿Quitar la tarjeta N.º <?= (int) $p['numero'] ?>?')">Quitar</button>
                    </form>
                    <?php endif; ?>
                </td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table></div>
    <?php endif; ?>
</div>

<?php if ($editable): ?>
<div class="card">
    <h2>Eliminar</h2>
    <form method="post">
        <?= csrf_field() ?>
        <input type="hidden" name="id" value="<?= $id ?>">
        <button type="submit" name="accion" value="eliminar" class="btn btn--danger btn--sm" onclick="return confirm('¿Eliminar este OSCE con sus estaciones y alumnos? No se puede deshacer.')">Eliminar OSCE</button>
    </form>
</div>
<?php endif; ?>
<?php
admin_footer();
