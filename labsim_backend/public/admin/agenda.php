<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';

/**
 * Una sola pantalla para casos + citas (antes estaba partido en agenda.php
 * y cases.php -- dos lugares para lo mismo era más lío que ayuda). Cada
 * fila es un caso clínico con su cita (si tiene una agendada): agendar,
 * cancelar/restaurar sin perder el caso, o eliminar todo junto.
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['form_action'] ?? '';

    if ($action === 'schedule') {
        $caseId = trim((string) ($_POST['case_id'] ?? ''));
        $appointmentId = (int) ($_POST['appointment_id'] ?? 0);
        // Agenda.py compara la fecha como STRING EXACTO 'dd-MM-yy' -- por
        // eso <input type="date"> y se convierte acá en vez de guardar el
        // ISO tal cual.
        $fechaIso = trim((string) ($_POST['fecha'] ?? ''));
        $fecha = $fechaIso !== '' ? date('d-m-y', strtotime($fechaIso)) : '';
        $hora = trim((string) ($_POST['hora'] ?? ''));
        $rut = trim((string) ($_POST['rut'] ?? ''));
        $nombre = trim((string) ($_POST['nombre'] ?? ''));
        $apellido = trim((string) ($_POST['apellido'] ?? ''));
        $fechaNacIso = trim((string) ($_POST['fecha_nac'] ?? ''));
        $fechaNac = $fechaNacIso !== '' ? date('d-m-Y', strtotime($fechaNacIso)) : '';
        $procedimiento = trim((string) ($_POST['procedimiento'] ?? '')) ?: 'Audiometría';
        $notaAdmin = trim((string) ($_POST['nota_admin'] ?? ''));

        if ($caseId === '') {
            $error = 'Falta el caso.';
        } elseif ($fecha !== '' && $hora !== '') {
            $stmt = $pdo->prepare('SELECT id FROM appointments WHERE fecha = ? AND hora = ? AND cancelada = 0 AND id != ?');
            $stmt->execute([$fecha, $hora, $appointmentId]);
            if ($stmt->fetch()) {
                $error = 'Ya existe una cita agendada en esa fecha y hora.';
            }
        }

        // Si la cita que se está reagendando ya tiene atenciones registradas,
        // editarla en el sitio borraría/mezclaría el historial de esa ronda
        // (attendances tiene UNIQUE(appointment_id, student_id) con upsert --
        // ver attendance_action.php -- y las métricas de comportamiento se
        // agrupan por appointment_id). Por eso una "ronda nueva" crea una
        // cita (appointment) nueva en vez de pisar la anterior; si todavía
        // no la atendió nadie, no hay nada que perder y se edita en el sitio.
        $isNewRound = false;
        if ($error === null && $appointmentId > 0) {
            $stmt = $pdo->prepare('SELECT 1 FROM attendances WHERE appointment_id = ? LIMIT 1');
            $stmt->execute([$appointmentId]);
            $isNewRound = (bool) $stmt->fetchColumn();
        }

        if ($error === null) {
            if ($appointmentId > 0 && !$isNewRound) {
                $pdo->prepare(
                    'UPDATE appointments SET fecha = ?, hora = ?, rut = ?, nombre = ?, apellido = ?, fecha_nac = ?,
                            procedimiento = ?, nota_admin = ?, updated_at = CURRENT_TIMESTAMP
                     WHERE id = ?'
                )->execute([$fecha, $hora, $rut, $nombre, $apellido, $fechaNac, $procedimiento, $notaAdmin, $appointmentId]);
                $success = 'Cita actualizada.';
            } else {
                $pdo->prepare(
                    'INSERT INTO appointments (fecha, hora, rut, nombre, apellido, fecha_nac, procedimiento, case_id, nota_admin)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
                )->execute([$fecha, $hora, $rut, $nombre, $apellido, $fechaNac, $procedimiento, $caseId, $notaAdmin]);
                $success = $isNewRound ? 'Nueva ronda agendada (se conserva el historial de la anterior).' : 'Caso agendado.';
            }
        }
    } elseif ($action === 'toggle_cancel') {
        $id = (int) ($_POST['id'] ?? 0);
        $cancelar = ($_POST['cancelada'] ?? '') === '1';
        $pdo->prepare('UPDATE appointments SET cancelada = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
            ->execute([$cancelar ? 1 : 0, $id]);
        $success = $cancelar ? 'Cita cancelada (el caso se conserva).' : 'Cita restaurada.';
    } elseif ($action === 'delete_case') {
        $caseId = trim((string) ($_POST['case_id'] ?? ''));
        if ($caseId !== '') {
            $stmt = $pdo->prepare('SELECT id FROM appointments WHERE case_id = ?');
            $stmt->execute([$caseId]);
            $appointmentIds = array_column($stmt->fetchAll(), 'id');

            $pdo->beginTransaction();
            foreach ($appointmentIds as $appId) {
                $pdo->prepare('DELETE FROM attendances WHERE appointment_id = ?')->execute([(int) $appId]);
            }
            $pdo->prepare('DELETE FROM appointments WHERE case_id = ?')->execute([$caseId]);
            $pdo->prepare('DELETE FROM cases WHERE id = ?')->execute([$caseId]);
            $pdo->commit();
            $success = 'Caso eliminado.';
        }
    }
}

/** dd-MM-yy o dd-MM-yyyy (formato legado) -> ISO, para precargar un <input type="date">. */
function legacy_to_iso(string $legacy): string
{
    $parts = explode('-', $legacy);
    if (count($parts) !== 3) {
        return '';
    }
    $fmt = strlen($parts[2]) === 4 ? 'd-m-Y' : 'd-m-y';
    $d = DateTime::createFromFormat($fmt, $legacy);
    return $d !== false ? $d->format('Y-m-d') : '';
}

// Última cita de cada caso (si tiene varias, poco común, se usa la más
// reciente). data trae paciente_snapshot si la cita que tenía se borró --
// ver Cases::snapshotBeforeAppointmentDelete().
$cases = $pdo->query(
    "SELECT c.id, c.data, c.updated_at,
            a.id AS appointment_id, a.fecha, a.hora, a.rut, a.nombre, a.apellido, a.fecha_nac,
            a.procedimiento, a.cancelada, a.nota_admin,
            (SELECT COUNT(*) FROM attendances att WHERE att.appointment_id = a.id) AS atenciones_count,
            (SELECT COUNT(*) FROM appointments WHERE case_id = c.id) AS rondas_count
     FROM cases c
     LEFT JOIN appointments a ON a.id = (
         SELECT id FROM appointments WHERE case_id = c.id ORDER BY id DESC LIMIT 1
     )
     ORDER BY CASE WHEN a.fecha IS NULL OR a.fecha = '' THEN 1 ELSE 0 END, a.fecha, a.hora, c.updated_at DESC"
)->fetchAll();

$historyCaseId = $_GET['history'] ?? null;
$historyRows = [];
if ($historyCaseId !== null) {
    $stmt = $pdo->prepare(
        "SELECT a.id, a.fecha, a.hora, a.procedimiento, a.cancelada, a.nombre, a.apellido,
                (SELECT COUNT(*) FROM attendances att WHERE att.appointment_id = a.id) AS atenciones_count
         FROM appointments a WHERE a.case_id = ? ORDER BY a.id DESC"
    );
    $stmt->execute([$historyCaseId]);
    $historyRows = $stmt->fetchAll();
}

$scheduleCaseId = $_GET['schedule'] ?? null;
$scheduleRow = null;
if ($scheduleCaseId !== null) {
    foreach ($cases as $c) {
        if ($c['id'] === $scheduleCaseId) {
            $scheduleRow = $c;
            break;
        }
    }
}
$scheduleSnapshot = [];
if ($scheduleRow !== null && !$scheduleRow['appointment_id']) {
    $data = json_decode($scheduleRow['data'] ?? '', true);
    $scheduleSnapshot = is_array($data) ? ($data['paciente_snapshot'] ?? []) : [];
}
$scheduleIsNewRound = false;
if ($scheduleRow !== null && $scheduleRow['appointment_id']) {
    $stmt = $pdo->prepare('SELECT 1 FROM attendances WHERE appointment_id = ? LIMIT 1');
    $stmt->execute([$scheduleRow['appointment_id']]);
    $scheduleIsNewRound = (bool) $stmt->fetchColumn();
}

// Calendario mensual: agrupa las citas vigentes (no canceladas) del mes
// pedido para dar una vista de ocupación antes de agendar un caso nuevo.
$month = $_GET['month'] ?? date('Y-m');
if (!preg_match('/^\d{4}-\d{2}$/', $month)) {
    $month = date('Y-m');
}
$monthStart = DateTime::createFromFormat('Y-m-d', $month . '-01');
$prevMonth = (clone $monthStart)->modify('-1 month')->format('Y-m');
$nextMonth = (clone $monthStart)->modify('+1 month')->format('Y-m');
$daysInMonth = (int) $monthStart->format('t');
$firstWeekday = (int) $monthStart->format('N'); // 1=lunes .. 7=domingo
$today = date('Y-m-d');
$monthNames = [1 => 'enero', 2 => 'febrero', 3 => 'marzo', 4 => 'abril', 5 => 'mayo', 6 => 'junio',
               7 => 'julio', 8 => 'agosto', 9 => 'septiembre', 10 => 'octubre', 11 => 'noviembre', 12 => 'diciembre'];

$appointmentsByDay = [];
foreach ($cases as $c) {
    if (!$c['appointment_id'] || $c['cancelada'] || $c['fecha'] === '') {
        continue;
    }
    $iso = legacy_to_iso($c['fecha']);
    if ($iso === '' || substr($iso, 0, 7) !== $month) {
        continue;
    }
    $appointmentsByDay[$iso][] = $c;
}
foreach ($appointmentsByDay as &$dayList) {
    usort($dayList, static fn(array $a, array $b): int => strcmp((string) $a['hora'], (string) $b['hora']));
}
unset($dayList);

admin_header('Fichas Clínicas', $me);
?>
<style>
    .cal-grid { display: grid; grid-template-columns: repeat(7, 1fr); gap: 4px; margin-top: 0.6rem; }
    .cal-dow { font-size: 0.75rem; font-weight: 600; color: #888; text-align: center; padding: 0.2rem 0; }
    .cal-day { min-height: 4.6rem; border: 1px solid #e5e5e5; border-radius: 4px; padding: 0.25rem; font-size: 0.75rem; background: #fafafa; }
    .cal-day.empty { background: transparent; border: none; }
    .cal-day.today { border-color: #1a2744; border-width: 2px; }
    .cal-day .cal-num { font-weight: 600; margin-bottom: 0.15rem; display: block; }
    .cal-day a { display: block; text-decoration: none; color: #1a2744; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
    .cal-day .cal-more { color: #886400; }
</style>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<?php if ($scheduleRow !== null): ?>
<div class="card">
    <strong><?= $scheduleRow['appointment_id'] ? 'Reagendar caso ' . htmlspecialchars($scheduleRow['id']) : 'Agendar caso ' . htmlspecialchars($scheduleRow['id']) ?></strong>
    <p style="font-size:0.85rem; color:#555;">
        Ojo: en la app del alumno, la Agenda por defecto solo muestra las citas de <strong>hoy</strong>
        (hay un selector de fecha y una casilla "Ver todas las citas habilitadas" para ver otros días).
    </p>
    <?php if ($scheduleIsNewRound): ?>
    <p style="font-size:0.85rem; color:#886400;">
        Esta cita ya tiene atenciones registradas -- guardar acá crea una <strong>ronda nueva</strong> (cita distinta)
        en vez de editar la anterior, para no perder el historial de esa ronda. Se puede ver todo el historial del
        caso con "Ver historial" en la lista de abajo.
    </p>
    <?php endif; ?>
    <form method="post">
        <input type="hidden" name="form_action" value="schedule">
        <input type="hidden" name="case_id" value="<?= htmlspecialchars($scheduleRow['id']) ?>">
        <input type="hidden" name="appointment_id" value="<?= (int) ($scheduleRow['appointment_id'] ?? 0) ?>">
        <label>Fecha (vacío = sin agendar aún)
            <input type="date" name="fecha" value="<?= htmlspecialchars(legacy_to_iso($scheduleRow['fecha'] ?? '')) ?>">
        </label>
        <label>Hora
            <input type="time" name="hora" value="<?= htmlspecialchars($scheduleRow['hora'] ?? '') ?>">
        </label>
        <label>RUT
            <input type="text" name="rut" value="<?= htmlspecialchars($scheduleRow['rut'] ?? $scheduleSnapshot['rut'] ?? '') ?>">
        </label>
        <label>Nombre
            <input type="text" name="nombre" value="<?= htmlspecialchars($scheduleRow['nombre'] ?? $scheduleSnapshot['nombre'] ?? '') ?>">
        </label>
        <label>Apellido
            <input type="text" name="apellido" value="<?= htmlspecialchars($scheduleRow['apellido'] ?? $scheduleSnapshot['apellido'] ?? '') ?>">
        </label>
        <label>Fecha de nacimiento
            <input type="date" name="fecha_nac" value="<?= htmlspecialchars(legacy_to_iso($scheduleRow['fecha_nac'] ?? $scheduleSnapshot['fecha_nac'] ?? '')) ?>">
        </label>
        <label>Procedimiento
            <input type="text" name="procedimiento" value="<?= htmlspecialchars($scheduleRow['procedimiento'] ?? $scheduleSnapshot['procedimiento'] ?? 'Audiometría') ?>">
        </label>
        <label>Nota admin
            <input type="text" name="nota_admin" value="<?= htmlspecialchars($scheduleRow['nota_admin'] ?? '') ?>">
        </label>
        <button type="submit"><?= $scheduleIsNewRound ? 'Agendar ronda nueva' : ($scheduleRow['appointment_id'] ? 'Guardar cambios' : 'Agendar') ?></button>
        <a href="agenda.php" style="margin-left:1rem; font-size:0.85rem;">Cancelar</a>
    </form>
</div>
<?php endif; ?>

<div class="card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <a href="agenda.php?month=<?= $prevMonth ?>">&larr; anterior</a>
        <strong><?= $monthNames[(int) $monthStart->format('n')] ?> <?= $monthStart->format('Y') ?></strong>
        <a href="agenda.php?month=<?= $nextMonth ?>">siguiente &rarr;</a>
    </div>
    <div class="cal-grid">
        <?php foreach (['Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb', 'Dom'] as $dow): ?>
        <div class="cal-dow"><?= $dow ?></div>
        <?php endforeach; ?>
        <?php for ($i = 1; $i < $firstWeekday; $i++): ?>
        <div class="cal-day empty"></div>
        <?php endfor; ?>
        <?php for ($day = 1; $day <= $daysInMonth; $day++):
            $iso = sprintf('%s-%02d', $month, $day);
            $dayAppts = $appointmentsByDay[$iso] ?? [];
        ?>
        <div class="cal-day<?= $iso === $today ? ' today' : '' ?>">
            <span class="cal-num"><?= $day ?></span>
            <?php foreach (array_slice($dayAppts, 0, 3) as $a): ?>
            <a href="agenda.php?schedule=<?= urlencode($a['id']) ?>" title="<?= htmlspecialchars(trim($a['hora'] . ' ' . $a['nombre'] . ' ' . $a['apellido'])) ?>">
                <?= htmlspecialchars($a['hora']) ?> <?= htmlspecialchars(trim($a['nombre'] . ' ' . $a['apellido'])) ?>
            </a>
            <?php endforeach; ?>
            <?php if (count($dayAppts) > 3): ?>
            <span class="cal-more">+<?= count($dayAppts) - 3 ?> más</span>
            <?php endif; ?>
        </div>
        <?php endfor; ?>
    </div>
    <p style="font-size:0.85rem; color:#555; margin-top:0.6rem;">
        Para agendar: crea el caso (o usa uno ya existente en la lista de abajo) y pincha "Agendar" -- ahí se elige fecha y hora.
    </p>
</div>

<div class="card">
    <strong>Pacientes registrados (<?= count($cases) ?>)</strong>
    &nbsp;·&nbsp; <a href="case_create.php">+ Crear caso nuevo</a>
    <p style="font-size:0.85rem; color:#555;">
        "Cita eliminada" = el caso perdió su cita (se conserva el nombre que tenía) --
        "Agendar" para reingresarlo con esos mismos datos precargados.
    </p>
    <table>
        <tr><th>ID</th><th>Paciente</th><th>Fecha</th><th>Hora</th><th>Procedimiento</th><th>Estado</th><th>Atenciones</th><th>Rondas</th><th></th></tr>
        <?php foreach ($cases as $c): ?>
        <?php
        $data = json_decode($c['data'] ?? '', true);
        $snapshot = is_array($data) ? ($data['paciente_snapshot'] ?? null) : null;
        $nombreVivo = $c['appointment_id'] ? trim(($c['nombre'] ?? '') . ' ' . ($c['apellido'] ?? '')) : '';
        $nombreSnapshot = $snapshot ? trim(($snapshot['nombre'] ?? '') . ' ' . ($snapshot['apellido'] ?? '')) : '';
        ?>
        <tr>
            <td><?= htmlspecialchars($c['id']) ?></td>
            <td>
                <?php if ($nombreVivo): ?>
                    <?= htmlspecialchars($nombreVivo) ?>
                <?php elseif ($nombreSnapshot): ?>
                    <?= htmlspecialchars($nombreSnapshot) ?>
                    <span style="color:#886400;"> (cita eliminada<?= !empty($snapshot['cita_eliminada_en']) ? ' el ' . htmlspecialchars($snapshot['cita_eliminada_en']) : '' ?>)</span>
                <?php else: ?>
                    <span style="color:#a33;">— sin cita —</span>
                <?php endif; ?>
            </td>
            <td><?= $c['appointment_id'] ? htmlspecialchars($c['fecha'] ?: '—') : '—' ?></td>
            <td><?= $c['appointment_id'] ? htmlspecialchars($c['hora'] ?: '—') : '—' ?></td>
            <td><?= $c['appointment_id'] ? htmlspecialchars($c['procedimiento']) : '—' ?></td>
            <td>
                <?php if (!$c['appointment_id']): ?>
                <span style="color:#886400;">sin agendar</span>
                <?php elseif ($c['cancelada']): ?>
                <span style="color:#a33;">cancelada</span>
                <?php elseif ($c['fecha'] === '' || $c['hora'] === ''): ?>
                <span style="color:#886400;">sin agendar</span>
                <?php else: ?>
                agendada
                <?php endif; ?>
            </td>
            <td style="font-size:0.8rem;">
                <?php if ($c['atenciones_count'] > 0): ?>
                <a href="dashboard.php?appointment_id=<?= (int) $c['appointment_id'] ?>"><?= (int) $c['atenciones_count'] ?> alumno<?= (int) $c['atenciones_count'] === 1 ? '' : 's' ?></a>
                <?php else: ?>
                —
                <?php endif; ?>
            </td>
            <td style="font-size:0.8rem;">
                <?php if ((int) $c['rondas_count'] > 1): ?>
                <a href="agenda.php?history=<?= urlencode($c['id']) ?>#historial"><?= (int) $c['rondas_count'] ?> · Ver historial</a>
                <?php else: ?>
                <?= (int) $c['rondas_count'] ?: '—' ?>
                <?php endif; ?>
            </td>
            <td style="white-space:nowrap;">
                <a href="agenda.php?schedule=<?= urlencode($c['id']) ?>" style="font-size:0.8rem;">
                    <?= $c['appointment_id'] ? 'Reagendar' : 'Agendar' ?>
                </a>
                <?php if ($c['appointment_id']): ?>
                <form method="post" class="inline">
                    <input type="hidden" name="form_action" value="toggle_cancel">
                    <input type="hidden" name="id" value="<?= (int) $c['appointment_id'] ?>">
                    <input type="hidden" name="cancelada" value="<?= $c['cancelada'] ? '0' : '1' ?>">
                    <button type="submit" class="secondary" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">
                        <?= $c['cancelada'] ? 'Restaurar' : 'Cancelar' ?>
                    </button>
                </form>
                <?php endif; ?>
                <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode("¿Eliminar el caso {$c['id']}" . ($nombreVivo || $nombreSnapshot ? ' (' . ($nombreVivo ?: $nombreSnapshot) . ')' : '') . "? También se eliminan todas sus citas/rondas ({$c['rondas_count']}) y las atenciones registradas. No se puede deshacer."), ENT_QUOTES) ?>);">
                    <input type="hidden" name="form_action" value="delete_case">
                    <input type="hidden" name="case_id" value="<?= htmlspecialchars($c['id']) ?>">
                    <button type="submit" class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Eliminar</button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$cases): ?>
        <tr><td colspan="9" style="color:#888;">Ningún caso guardado todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>

<?php if ($historyCaseId !== null): ?>
<div class="card" id="historial">
    <strong>Historial del caso <?= htmlspecialchars($historyCaseId) ?></strong>
    &nbsp;·&nbsp; <a href="agenda.php" style="font-size:0.85rem;">Cerrar</a>
    <p style="font-size:0.85rem; color:#555;">Cada ronda es una cita distinta con su propio historial de atenciones y métricas (no se mezclan entre sí).</p>
    <table>
        <tr><th>Cita</th><th>Fecha</th><th>Hora</th><th>Paciente</th><th>Procedimiento</th><th>Estado</th><th>Atenciones</th></tr>
        <?php foreach ($historyRows as $h): ?>
        <tr>
            <td>#<?= (int) $h['id'] ?></td>
            <td><?= htmlspecialchars($h['fecha'] ?: '—') ?></td>
            <td><?= htmlspecialchars($h['hora'] ?: '—') ?></td>
            <td><?= htmlspecialchars(trim($h['nombre'] . ' ' . $h['apellido'])) ?: '—' ?></td>
            <td><?= htmlspecialchars($h['procedimiento']) ?></td>
            <td><?= $h['cancelada'] ? 'cancelada' : 'agendada' ?></td>
            <td>
                <?php if ((int) $h['atenciones_count'] > 0): ?>
                <a href="dashboard.php?appointment_id=<?= (int) $h['id'] ?>"><?= (int) $h['atenciones_count'] ?> alumno<?= (int) $h['atenciones_count'] === 1 ? '' : 's' ?></a>
                <?php else: ?>
                —
                <?php endif; ?>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$historyRows): ?>
        <tr><td colspan="7" style="color:#888;">Este caso no tiene citas.</td></tr>
        <?php endif; ?>
    </table>
</div>
<?php endif; ?>
<?php
admin_footer();
