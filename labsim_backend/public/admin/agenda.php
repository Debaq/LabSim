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

        if ($error === null) {
            if ($appointmentId > 0) {
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
                $success = 'Caso agendado.';
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
            (SELECT GROUP_CONCAT(u.display_name || ' (' || att.estado || ')', ', ')
             FROM attendances att JOIN users u ON u.id = att.student_id
             WHERE att.appointment_id = a.id) AS atenciones
     FROM cases c
     LEFT JOIN appointments a ON a.id = (
         SELECT id FROM appointments WHERE case_id = c.id ORDER BY id DESC LIMIT 1
     )
     ORDER BY CASE WHEN a.fecha IS NULL OR a.fecha = '' THEN 1 ELSE 0 END, a.fecha, a.hora, c.updated_at DESC"
)->fetchAll();

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

admin_header('Agenda', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<?php if ($scheduleRow !== null): ?>
<div class="card">
    <strong><?= $scheduleRow['appointment_id'] ? 'Reagendar caso ' . htmlspecialchars($scheduleRow['id']) : 'Agendar caso ' . htmlspecialchars($scheduleRow['id']) ?></strong>
    <p style="font-size:0.85rem; color:#555;">
        Ojo: en la app del alumno, la Agenda por defecto solo muestra las citas de <strong>hoy</strong>
        (hay un selector de fecha y una casilla "Ver todas las citas habilitadas" para ver otros días).
    </p>
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
        <button type="submit"><?= $scheduleRow['appointment_id'] ? 'Guardar cambios' : 'Agendar' ?></button>
        <a href="agenda.php" style="margin-left:1rem; font-size:0.85rem;">Cancelar</a>
    </form>
</div>
<?php endif; ?>

<div class="card">
    <strong>Casos (<?= count($cases) ?>)</strong>
    <p style="font-size:0.85rem; color:#555;">
        "Cita eliminada" = el caso perdió su cita (se conserva el nombre que tenía) --
        "Agendar" para reingresarlo con esos mismos datos precargados.
    </p>
    <table>
        <tr><th>ID</th><th>Paciente</th><th>Fecha</th><th>Hora</th><th>Procedimiento</th><th>Estado</th><th>Atenciones</th><th></th></tr>
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
            <td style="font-size:0.8rem;"><?= htmlspecialchars($c['atenciones'] ?? '') ?: '—' ?></td>
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
                <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode("¿Eliminar el caso {$c['id']}" . ($nombreVivo || $nombreSnapshot ? ' (' . ($nombreVivo ?: $nombreSnapshot) . ')' : '') . "? También se elimina su cita y las atenciones registradas. No se puede deshacer."), ENT_QUOTES) ?>);">
                    <input type="hidden" name="form_action" value="delete_case">
                    <input type="hidden" name="case_id" value="<?= htmlspecialchars($c['id']) ?>">
                    <button type="submit" class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Eliminar</button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$cases): ?>
        <tr><td colspan="8" style="color:#888;">Ningún caso guardado todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>
<?php
admin_footer();
