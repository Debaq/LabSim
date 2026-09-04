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
            a.procedimiento, a.nota_admin, a.course_id, a.assigned_student_id, a.assigned_group_id,
            (SELECT COUNT(*) FROM attendances att WHERE att.appointment_id = a.id) AS atenciones_count,
            (SELECT COUNT(*) FROM appointments WHERE case_id = c.id) AS rondas_count
     FROM cases c
     LEFT JOIN appointments a ON a.id = (
         SELECT id FROM appointments WHERE case_id = c.id ORDER BY id DESC LIMIT 1
     ){$courseScopeSql}
     ORDER BY CASE WHEN a.fecha IS NULL OR a.fecha = '' THEN 1 ELSE 0 END, a.fecha, a.hora, c.updated_at DESC"
);
$stmt->execute($permissionParams);
$cases = $stmt->fetchAll();

$courseNameById = [];
foreach ($pdo->query('SELECT id, name FROM courses')->fetchAll() as $cn) {
    $courseNameById[(int) $cn['id']] = $cn['name'];
}
$groupNameById = [];
foreach ($pdo->query('SELECT id, name FROM student_groups')->fetchAll() as $gn) {
    $groupNameById[(int) $gn['id']] = $gn['name'];
}
$userNameById = [];
foreach ($pdo->query('SELECT id, display_name FROM users')->fetchAll() as $un) {
    $userNameById[(int) $un['id']] = $un['display_name'];
}

admin_header('Fichas Clínicas', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <strong>Pacientes registrados (<?= count($cases) ?>)</strong>
    &nbsp;·&nbsp; <a href="case_create.php">+ Crear caso nuevo</a>
    <p style="font-size:0.85rem; color:#555;">
        Biblioteca completa de fichas del sistema (agendadas o no). Para agendar, reagendar o eliminar citas,
        usa <a href="agenda.php">Agendas</a>.
    </p>
    <table>
        <tr><th>ID</th><th>Paciente</th><th>Estado</th><th>Curso / asignado a</th><th>Atenciones</th><th>Rondas</th><th></th></tr>
        <?php foreach ($cases as $c): ?>
        <?php
        $data = json_decode($c['data'] ?? '', true);
        $snapshot = is_array($data) ? ($data['paciente_snapshot'] ?? null) : null;
        $nombreVivo = $c['appointment_id'] ? trim(($c['nombre'] ?? '') . ' ' . ($c['apellido'] ?? '')) : '';
        $nombreSnapshot = $snapshot ? trim(($snapshot['nombre'] ?? '') . ' ' . ($snapshot['apellido'] ?? '')) : '';

        $assignLabel = '—';
        if ($c['appointment_id']) {
            if ($c['course_id']) {
                $assignLabel = $courseNameById[(int) $c['course_id']] ?? ('Curso #' . $c['course_id']);
                if ($c['assigned_student_id']) {
                    $assignLabel .= ' · ' . ($userNameById[(int) $c['assigned_student_id']] ?? ('Alumno #' . $c['assigned_student_id']));
                } elseif ($c['assigned_group_id']) {
                    $assignLabel .= ' · grupo ' . ($groupNameById[(int) $c['assigned_group_id']] ?? ('#' . $c['assigned_group_id']));
                } else {
                    $assignLabel .= ' · todo el curso (legado)';
                }
            } else {
                $assignLabel = 'cola libre (legado)';
            }
        }
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
            <td>
                <?php if (!$c['appointment_id']): ?>
                <span style="color:#886400;">sin agendar</span>
                <?php elseif ($c['fecha'] === '' || $c['hora'] === ''): ?>
                <span style="color:#886400;">sin agendar</span>
                <?php else: ?>
                agendada (<?= htmlspecialchars($c['fecha']) ?> <?= htmlspecialchars($c['hora']) ?>)
                <?php endif; ?>
            </td>
            <td style="font-size:0.78rem;"><?= htmlspecialchars($assignLabel) ?></td>
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
                <a href="case_create.php?edit=<?= urlencode($c['id']) ?>" style="font-size:0.8rem;">Editar ficha</a>
                <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode("¿Eliminar el caso {$c['id']}" . ($nombreVivo || $nombreSnapshot ? ' (' . ($nombreVivo ?: $nombreSnapshot) . ')' : '') . "? También se eliminan todas sus citas/rondas ({$c['rondas_count']}) y las atenciones registradas. No se puede deshacer."), ENT_QUOTES) ?>);">
                <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="delete_case">
                    <input type="hidden" name="case_id" value="<?= htmlspecialchars($c['id']) ?>">
                    <button type="submit" class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Eliminar</button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$cases): ?>
        <tr><td colspan="7" style="color:#888;">Ningún caso guardado todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>
<?php
admin_footer();
