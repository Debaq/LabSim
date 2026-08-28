<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';

/**
 * Gestión de agenda desde el navegador -- antes solo se podía crear/editar
 * citas desde la app de escritorio (con permission=777). Reimplementa la
 * misma lógica que appointment_upsert.php/appointment_delete.php pero
 * autenticada con la sesión de portal (Auth::requireAdminSession) en vez
 * de un Bearer token, como el resto de admin/*.php.
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['form_action'] ?? '';

    if ($action === 'save') {
        $id = (int) ($_POST['id'] ?? 0);
        // La app (Agenda.py) compara la fecha de esta cita contra
        // QDate::toString("dd-MM-yy") como STRING EXACTO para decidir si
        // se muestra hoy -- un typo de formato acá (año de 4 dígitos, otro
        // separador) hace que la cita exista pero nunca aparezca. Por eso
        // <input type="date"> en vez de texto libre, y se convierte aquí.
        $fechaIso = trim((string) ($_POST['fecha'] ?? ''));
        $fecha = $fechaIso !== '' ? date('d-m-y', strtotime($fechaIso)) : '';
        $hora = trim((string) ($_POST['hora'] ?? ''));
        $rut = trim((string) ($_POST['rut'] ?? ''));
        $nombre = trim((string) ($_POST['nombre'] ?? ''));
        $apellido = trim((string) ($_POST['apellido'] ?? ''));
        $fechaNacIso = trim((string) ($_POST['fecha_nac'] ?? ''));
        $fechaNac = $fechaNacIso !== '' ? date('d-m-Y', strtotime($fechaNacIso)) : '';
        $procedimiento = trim((string) ($_POST['procedimiento'] ?? '')) ?: 'Audiometría';
        $caseId = trim((string) ($_POST['case_id'] ?? '')) ?: null;
        $notaAdmin = trim((string) ($_POST['nota_admin'] ?? ''));

        if ($fecha !== '' && $hora !== '') {
            $stmt = $pdo->prepare('SELECT id FROM appointments WHERE fecha = ? AND hora = ? AND cancelada = 0 AND id != ?');
            $stmt->execute([$fecha, $hora, $id]);
            if ($stmt->fetch()) {
                $error = 'Ya existe una cita agendada en esa fecha y hora.';
            }
        }

        if ($error === null) {
            if ($id > 0) {
                $pdo->prepare(
                    'UPDATE appointments SET fecha = ?, hora = ?, rut = ?, nombre = ?, apellido = ?, fecha_nac = ?,
                            procedimiento = ?, case_id = ?, nota_admin = ?, updated_at = CURRENT_TIMESTAMP
                     WHERE id = ?'
                )->execute([$fecha, $hora, $rut, $nombre, $apellido, $fechaNac, $procedimiento, $caseId, $notaAdmin, $id]);
                $success = 'Cita actualizada.';
            } else {
                $pdo->prepare(
                    'INSERT INTO appointments (fecha, hora, rut, nombre, apellido, fecha_nac, procedimiento, case_id, nota_admin)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
                )->execute([$fecha, $hora, $rut, $nombre, $apellido, $fechaNac, $procedimiento, $caseId, $notaAdmin]);
                $success = 'Cita creada.';
            }
        }
    } elseif ($action === 'toggle_cancel') {
        $id = (int) ($_POST['id'] ?? 0);
        $cancelar = ($_POST['cancelada'] ?? '') === '1';
        $pdo->prepare('UPDATE appointments SET cancelada = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
            ->execute([$cancelar ? 1 : 0, $id]);
        $success = $cancelar ? 'Cita cancelada.' : 'Cita restaurada.';
    } elseif ($action === 'delete') {
        $id = (int) ($_POST['id'] ?? 0);
        $pdo->beginTransaction();
        $pdo->prepare('DELETE FROM attendances WHERE appointment_id = ?')->execute([$id]);
        $pdo->prepare('DELETE FROM appointments WHERE id = ?')->execute([$id]);
        $pdo->commit();
        $success = 'Cita eliminada.';
    }
}

/**
 * Convierte una fecha guardada en formato legado (dd-MM-yy o dd-MM-yyyy) a
 * ISO para precargar un <input type="date">. DateTime::createFromFormat
 * con 'Y' acepta un año de 2 dígitos sin fallar (lo toma literal: "26" ->
 * año 26, no 2026) -- por eso se elige el formato mirando el largo del
 * año en vez de confiar en eso.
 */
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

$editId = isset($_GET['edit']) ? (int) $_GET['edit'] : null;
$editRow = null;
if ($editId) {
    $stmt = $pdo->prepare('SELECT * FROM appointments WHERE id = ?');
    $stmt->execute([$editId]);
    $editRow = $stmt->fetch() ?: null;
}

$cases = $pdo->query('SELECT id FROM cases ORDER BY CAST(id AS INTEGER)')->fetchAll();

$appointments = $pdo->query(
    "SELECT a.*,
            (SELECT GROUP_CONCAT(u.display_name || ' (' || att.estado || ')', ', ')
             FROM attendances att JOIN users u ON u.id = att.student_id
             WHERE att.appointment_id = a.id) AS atenciones
     FROM appointments a
     ORDER BY CASE WHEN a.fecha = '' THEN 1 ELSE 0 END, a.fecha, a.hora, a.id DESC"
)->fetchAll();

admin_header('Agenda', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <strong><?= $editRow ? 'Editar cita #' . (int) $editRow['id'] : 'Nueva cita' ?></strong>
    <p style="font-size:0.85rem; color:#555;">
        Ojo: en la app del alumno, la Agenda por defecto solo muestra las citas de <strong>hoy</strong>
        (hay un selector de fecha y una casilla "Ver todas las citas habilitadas" para ver otros días).
        Si agendas para otra fecha, el alumno no la va a ver salvo que cambie el filtro.
    </p>
    <form method="post">
        <input type="hidden" name="form_action" value="save">
        <input type="hidden" name="id" value="<?= (int) ($editRow['id'] ?? 0) ?>">
        <label>Fecha (vacío = sin agendar aún)
            <input type="date" name="fecha" value="<?= htmlspecialchars(legacy_to_iso($editRow['fecha'] ?? '')) ?>">
        </label>
        <label>Hora
            <input type="time" name="hora" value="<?= htmlspecialchars($editRow['hora'] ?? '') ?>">
        </label>
        <label>RUT
            <input type="text" name="rut" value="<?= htmlspecialchars($editRow['rut'] ?? '') ?>">
        </label>
        <label>Nombre
            <input type="text" name="nombre" value="<?= htmlspecialchars($editRow['nombre'] ?? '') ?>">
        </label>
        <label>Apellido
            <input type="text" name="apellido" value="<?= htmlspecialchars($editRow['apellido'] ?? '') ?>">
        </label>
        <label>Fecha de nacimiento
            <input type="date" name="fecha_nac" value="<?= htmlspecialchars(legacy_to_iso($editRow['fecha_nac'] ?? '')) ?>">
        </label>
        <label>Procedimiento
            <input type="text" name="procedimiento" value="<?= htmlspecialchars($editRow['procedimiento'] ?? 'Audiometría') ?>">
        </label>
        <label>Caso clínico (ID)
            <select name="case_id">
                <option value="">— sin caso —</option>
                <?php foreach ($cases as $c): ?>
                <option value="<?= htmlspecialchars($c['id']) ?>" <?= (($editRow['case_id'] ?? '') === $c['id']) ? 'selected' : '' ?>>
                    <?= htmlspecialchars($c['id']) ?>
                </option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Nota admin
            <input type="text" name="nota_admin" value="<?= htmlspecialchars($editRow['nota_admin'] ?? '') ?>">
        </label>
        <button type="submit"><?= $editRow ? 'Guardar cambios' : 'Crear cita' ?></button>
        <?php if ($editRow): ?>
        <a href="agenda.php" style="margin-left:1rem; font-size:0.85rem;">Cancelar edición</a>
        <?php endif; ?>
    </form>
</div>

<div class="card">
    <strong>Citas (<?= count($appointments) ?>)</strong>
    <table>
        <tr>
            <th>ID</th><th>Fecha</th><th>Hora</th><th>Paciente</th><th>Procedimiento</th>
            <th>Caso</th><th>Atenciones</th><th>Estado</th><th></th>
        </tr>
        <?php foreach ($appointments as $a): ?>
        <tr>
            <td><?= (int) $a['id'] ?></td>
            <td><?= htmlspecialchars($a['fecha'] ?: '—') ?></td>
            <td><?= htmlspecialchars($a['hora'] ?: '—') ?></td>
            <td><?= htmlspecialchars(trim("{$a['nombre']} {$a['apellido']}")) ?: '—' ?></td>
            <td><?= htmlspecialchars($a['procedimiento']) ?></td>
            <td><?= htmlspecialchars($a['case_id'] ?? '—') ?></td>
            <td style="font-size:0.8rem;"><?= htmlspecialchars($a['atenciones'] ?? '') ?: '—' ?></td>
            <td>
                <?php if ($a['cancelada']): ?>
                <span style="color:#a33;">cancelada</span>
                <?php elseif ($a['fecha'] === '' || $a['hora'] === ''): ?>
                <span style="color:#886400;">sin agendar</span>
                <?php else: ?>
                agendada
                <?php endif; ?>
            </td>
            <td style="white-space:nowrap;">
                <a href="agenda.php?edit=<?= (int) $a['id'] ?>" style="font-size:0.8rem;">Editar</a>
                <form method="post" class="inline">
                    <input type="hidden" name="form_action" value="toggle_cancel">
                    <input type="hidden" name="id" value="<?= (int) $a['id'] ?>">
                    <input type="hidden" name="cancelada" value="<?= $a['cancelada'] ? '0' : '1' ?>">
                    <button type="submit" class="secondary" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">
                        <?= $a['cancelada'] ? 'Restaurar' : 'Cancelar' ?>
                    </button>
                </form>
                <form method="post" class="inline" onsubmit="return confirm('¿Eliminar esta cita y todas sus atenciones? No se puede deshacer.');">
                    <input type="hidden" name="form_action" value="delete">
                    <input type="hidden" name="id" value="<?= (int) $a['id'] ?>">
                    <button type="submit" class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Eliminar</button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$appointments): ?>
        <tr><td colspan="9" style="color:#888;">Ninguna cita todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>
<?php
admin_footer();
