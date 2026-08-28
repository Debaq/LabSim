<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';

$me = Auth::requireAdminSession();
$pdo = Db::get();

$studentId = (int) ($_GET['id'] ?? 0);
$stmt = $pdo->prepare("SELECT * FROM users WHERE id = ? AND role = 'student'");
$stmt->execute([$studentId]);
$student = $stmt->fetch();

if (!$student) {
    admin_header('Alumno', $me);
    echo '<p class="error">Alumno no encontrado.</p>';
    admin_footer();
    exit;
}

$stmt = $pdo->prepare(
    "SELECT att.estado, att.nota, att.hora_real, att.updated_at,
            a.id AS appointment_id, a.fecha, a.hora, a.nombre, a.apellido, a.procedimiento
     FROM attendances att
     JOIN appointments a ON a.id = att.appointment_id
     WHERE att.student_id = ?
     ORDER BY att.updated_at DESC"
);
$stmt->execute([$studentId]);
$attendances = $stmt->fetchAll();

$estadoCounts = ['atendiendo' => 0, 'atendido' => 0, 'no_show' => 0];
foreach ($attendances as $a) {
    if (isset($estadoCounts[$a['estado']])) {
        $estadoCounts[$a['estado']]++;
    }
}

$stmt = $pdo->prepare(
    'SELECT action, COUNT(*) AS n, MAX(client_ts) AS last_ts
     FROM action_logs WHERE user_id = ? GROUP BY action ORDER BY n DESC'
);
$stmt->execute([$studentId]);
$actionCounts = $stmt->fetchAll();
$totalActions = array_sum(array_column($actionCounts, 'n'));

$stmt = $pdo->prepare(
    'SELECT client_ts, action, payload FROM action_logs WHERE user_id = ? ORDER BY id DESC LIMIT 30'
);
$stmt->execute([$studentId]);
$recentLogs = $stmt->fetchAll();

admin_header('Alumno: ' . $student['display_name'], $me);
?>
<div class="card">
    <p>
        <strong><?= htmlspecialchars($student['display_name']) ?></strong>
        &nbsp;·&nbsp; <span class="mono"><?= htmlspecialchars($student['username']) ?></span>
        &nbsp;·&nbsp; <?= $student['active'] ? 'activo' : 'inactivo' ?>
        &nbsp;·&nbsp; alumno desde <?= htmlspecialchars($student['created_at']) ?>
    </p>
</div>

<div class="card">
    <strong>Resumen</strong>
    <table>
        <tr><td>Atendiendo (en curso)</td><td><strong><?= $estadoCounts['atendiendo'] ?></strong></td></tr>
        <tr><td>Atendidos (cerrados)</td><td><strong><?= $estadoCounts['atendido'] ?></strong></td></tr>
        <tr><td>No-show</td><td><strong><?= $estadoCounts['no_show'] ?></strong></td></tr>
        <tr><td>Acciones registradas (total)</td><td><strong><?= $totalActions ?></strong></td></tr>
    </table>
</div>

<div class="card">
    <strong>Atenciones (<?= count($attendances) ?>)</strong>
    <table>
        <tr><th>Cita</th><th>Paciente</th><th>Procedimiento</th><th>Estado</th><th>Hora real</th><th>Nota</th><th>Actualizado</th></tr>
        <?php foreach ($attendances as $a): ?>
        <tr>
            <td>#<?= (int) $a['appointment_id'] ?> (<?= htmlspecialchars($a['fecha'] ?: '—') ?> <?= htmlspecialchars($a['hora'] ?: '') ?>)</td>
            <td><?= htmlspecialchars(trim("{$a['nombre']} {$a['apellido']}")) ?: '—' ?></td>
            <td><?= htmlspecialchars($a['procedimiento']) ?></td>
            <td><?= htmlspecialchars($a['estado']) ?></td>
            <td><?= htmlspecialchars($a['hora_real'] ?: '—') ?></td>
            <td style="font-size:0.85rem;"><?= htmlspecialchars($a['nota'] ?: '—') ?></td>
            <td><?= htmlspecialchars($a['updated_at']) ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$attendances): ?>
        <tr><td colspan="7" style="color:#888;">Sin atenciones registradas todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>

<div class="card">
    <strong>Acciones por tipo</strong>
    <table>
        <tr><th>Acción</th><th>Veces</th><th>Última vez</th></tr>
        <?php foreach ($actionCounts as $ac): ?>
        <tr>
            <td><?= htmlspecialchars($ac['action']) ?></td>
            <td><?= (int) $ac['n'] ?></td>
            <td><?= htmlspecialchars($ac['last_ts']) ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$actionCounts): ?>
        <tr><td colspan="3" style="color:#888;">Sin acciones registradas todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>

<div class="card">
    <strong>Últimas 30 acciones (detalle)</strong>
    <table>
        <tr><th>Cuándo (cliente)</th><th>Acción</th><th>Payload</th></tr>
        <?php foreach ($recentLogs as $log): ?>
        <tr>
            <td><?= htmlspecialchars($log['client_ts']) ?></td>
            <td><?= htmlspecialchars($log['action']) ?></td>
            <td class="mono" style="font-size:0.75rem;"><?= htmlspecialchars($log['payload'] ?? '') ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$recentLogs): ?>
        <tr><td colspan="3" style="color:#888;">Sin acciones registradas todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>
<?php
admin_footer();
