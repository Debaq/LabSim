<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/AdminAudit.php';

/**
 * Base de datos de fichas clínicas (pacientes/casos) -- separado de agenda.php,
 * que ahora es solo el lugar para configurar/agendar citas por curso, grupo o
 * alumno. Acá se ve y mantiene la biblioteca COMPLETA de casos del sistema,
 * agendados o no, sin acotar por curso.
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$myCourseIds = $isFullAdmin ? null : Courses::teacherCourseIds((int) $me['id']);

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $action = $_POST['form_action'] ?? '';

    if ($action === 'delete_case') {
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
            AdminAudit::log($me, 'case_delete', ['case_id' => $caseId, 'appointments_deleted' => count($appointmentIds)]);
        }
    }
}

/** Arma un link a patients.php conservando los GET actuales. */
function patients_url(array $overrides = []): string
{
    $params = array_merge($_GET, $overrides);
    $params = array_filter($params, static fn($v): bool => $v !== null && $v !== '');
    return 'patients.php' . ($params ? '?' . http_build_query($params) : '');
}

// Docente: solo ve casos sin agendar (biblioteca compartida) + citas de
// su(s) curso(s) + citas legado sin curso (course_id NULL) -- nunca citas
// de un curso ajeno. Admin completo sin filtro. Esta lista NO se acota por
// curso/grupo/alumno -- es la biblioteca completa del sistema (para eso está
// el filtro de agenda.php).
$permissionSql = '1=1';
$permissionParams = [];
if (!$isFullAdmin) {
    if ($myCourseIds) {
        $placeholders = implode(',', array_fill(0, count($myCourseIds), '?'));
        $permissionSql = "(a.course_id IS NULL OR a.course_id IN ({$placeholders}))";
        $permissionParams = $myCourseIds;
    } else {
        $permissionSql = 'a.course_id IS NULL';
    }
}

$courseScopeSql = " WHERE a.id IS NULL OR ({$permissionSql})";
$stmt = $pdo->prepare(
    "SELECT c.id, c.data, c.updated_at,
            a.id AS appointment_id, a.fecha, a.hora, a.rut, a.nombre, a.apellido, a.fecha_nac,
            a.procedimiento, a.nota_admin,
            p.comentario_docente,
            -- Suma TODAS las rondas del caso (no solo la última cita) --
            -- si solo se contara att.appointment_id = a.id (última cita),
            -- cada reagendamiento hacía parecer que las atenciones de
            -- rondas previas se \"perdían\" (volvía a 0).
            (SELECT COUNT(*) FROM attendances att
                JOIN appointments ap2 ON ap2.id = att.appointment_id
                WHERE ap2.case_id = c.id) AS atenciones_count,
            (SELECT COUNT(*) FROM appointments WHERE case_id = c.id) AS rondas_count
     FROM cases c
     LEFT JOIN appointments a ON a.id = (
         SELECT id FROM appointments WHERE case_id = c.id ORDER BY id DESC LIMIT 1
     )
     LEFT JOIN patients p ON p.id = c.patient_id
     {$courseScopeSql}
     ORDER BY CASE WHEN a.fecha IS NULL OR a.fecha = '' THEN 1 ELSE 0 END, a.fecha, a.hora, c.updated_at DESC"
);
$stmt->execute($permissionParams);
$cases = $stmt->fetchAll();

admin_header('Fichas Clínicas', $me);
?>
<style>
    .btn-link {
        display: inline-block; padding: 0.5rem 1.1rem; background: #1a2744; color: #fff;
        border-radius: 4px; text-decoration: none; font-size: 0.9rem; font-weight: 600;
    }
    .btn-link:hover { opacity: 0.9; }
    .patients-toolbar { display: flex; flex-wrap: wrap; align-items: center; gap: 0.6rem; margin: 0.9rem 0; }
    .patients-toolbar input[type="text"] { width: auto; flex: 1 1 240px; margin-top: 0; }
    .patients-toolbar select { width: auto; margin-top: 0; }
    .patients-toolbar .toolbar-count { font-size: 0.8rem; color: #666; margin-left: auto; }
    .action-btn {
        display: inline-block; padding: 0.15rem 0.5rem; margin: 0 0.15rem 0.15rem 0; font-size: 0.75rem;
        border-radius: 4px; text-decoration: none; color: #fff; border: none; cursor: pointer; line-height: 1.6;
    }
    .action-btn.primary { background: #1a2744; }
    .action-btn.secondary { background: #888; }
    .action-btn.danger { background: #a33; }
    .action-btn:hover { opacity: 0.85; }
</style>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <div style="display:flex; justify-content:space-between; align-items:center;">
        <strong>Pacientes registrados (<?= count($cases) ?>)</strong>
        <a class="btn-link" href="case_create.php">+ Crear caso nuevo</a>
    </div>
    <p style="font-size:0.85rem; color:#555;">
        Biblioteca completa de fichas del sistema (agendadas o no). Para agendar, reagendar o eliminar citas,
        usa <a href="agenda.php">Agendas</a>.
    </p>
    <div class="patients-toolbar">
        <input type="text" id="patients-search" placeholder="Buscar por nombre, rut o ID..." autocomplete="off" oninput="filterPatientsTable()">
        <select id="patients-filter-estado" onchange="filterPatientsTable()">
            <option value="">Todos los estados</option>
            <option value="agendada">Agendada</option>
            <option value="sin_agendar">Sin agendar</option>
        </select>
        <span class="toolbar-count" id="patients-toolbar-count"></span>
    </div>
    <table id="patients-table">
        <tr>
            <th>ID</th>
            <th>Nombre</th>
            <th>Comentario</th>
            <th>Estado</th>
            <th title="Total de alumnos que han atendido este caso, sumando todas las rondas (citas/reagendos)">Atenciones</th>
            <th title="Cantidad de veces que este caso fue agendado -- cada reagendamiento suma una ronda nueva">Rondas</th>
            <th>Acciones</th>
        </tr>
        <?php foreach ($cases as $c): ?>
        <?php
        $data = json_decode($c['data'] ?? '', true);
        $snapshot = is_array($data) ? ($data['paciente_snapshot'] ?? null) : null;
        $nombreVivo = $c['appointment_id'] ? trim(($c['nombre'] ?? '') . ' ' . ($c['apellido'] ?? '')) : '';
        $nombreSnapshot = $snapshot ? trim(($snapshot['nombre'] ?? '') . ' ' . ($snapshot['apellido'] ?? '')) : '';
        $estadoRow = (!$c['appointment_id'] || $c['fecha'] === '' || $c['hora'] === '') ? 'sin_agendar' : 'agendada';
        $comentarioDocente = trim((string) ($c['comentario_docente'] ?? ''));
        $searchBlob = mb_strtolower($c['id'] . ' ' . ($nombreVivo ?: $nombreSnapshot) . ' ' . ($c['rut'] ?? '') . ' ' . $comentarioDocente);
        ?>
        <tr data-estado="<?= $estadoRow ?>" data-search="<?= htmlspecialchars($searchBlob) ?>">
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
            <td style="font-size:0.8rem; color:#a00; max-width:22rem;">
                <?= $comentarioDocente !== '' ? htmlspecialchars($comentarioDocente) : '<span style="color:#bbb;">—</span>' ?>
            </td>
            <td>
                <?php if (!$c['appointment_id']): ?>
                <span style="color:#886400;">sin agendar</span>
                <?php elseif ($c['fecha'] === '' || $c['hora'] === ''): ?>
                <span style="color:#886400;">sin agendar</span>
                <?php else: ?>
                agendada (<?= htmlspecialchars($c['fecha']) ?> <?= htmlspecialchars($c['hora']) ?>)
                <?php endif; ?>
            </td>
            <td style="font-size:0.8rem;">
                <?php if ((int) $c['atenciones_count'] > 0): ?>
                <a href="agenda.php?history=<?= urlencode($c['id']) ?>#historial"><?= (int) $c['atenciones_count'] ?> alumno<?= (int) $c['atenciones_count'] === 1 ? '' : 's' ?></a>
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
                <a href="agenda.php?schedule=<?= urlencode($c['id']) ?>" class="action-btn primary">
                    <?= $c['appointment_id'] ? 'Reagendar' : 'Agendar' ?>
                </a>
                <a href="case_create.php?edit=<?= urlencode($c['id']) ?>" class="action-btn secondary">Editar ficha</a>
                <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode("¿Eliminar el caso {$c['id']}" . ($nombreVivo || $nombreSnapshot ? ' (' . ($nombreVivo ?: $nombreSnapshot) . ')' : '') . "? También se eliminan todas sus citas/rondas ({$c['rondas_count']}) y las atenciones registradas. No se puede deshacer."), ENT_QUOTES) ?>);">
                <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="delete_case">
                    <input type="hidden" name="case_id" value="<?= htmlspecialchars($c['id']) ?>">
                    <button type="submit" class="action-btn danger">Eliminar</button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$cases): ?>
        <tr><td colspan="7" style="color:#888;">Ningún caso guardado todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>
<script>
function filterPatientsTable() {
    var q = document.getElementById('patients-search').value.toLowerCase().trim();
    var estado = document.getElementById('patients-filter-estado').value;
    var rows = document.querySelectorAll('#patients-table tr[data-search]');
    var visible = 0;
    rows.forEach(function (row) {
        var matchQ = q === '' || (row.dataset.search || '').indexOf(q) !== -1;
        var matchEstado = estado === '' || row.dataset.estado === estado;
        var show = matchQ && matchEstado;
        row.style.display = show ? '' : 'none';
        if (show) visible++;
    });
    document.getElementById('patients-toolbar-count').textContent = visible + ' de ' + rows.length;
}
filterPatientsTable();
</script>
<?php
admin_footer();
