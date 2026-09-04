<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Metrics.php';

/**
 * Lista de pacientes atendidos por el alumno logueado (sesión propia, ver
 * sso.php) -- mismo alcance que admin/student.php le muestra al docente
 * sobre un alumno, pero acá scopeado por sesión (nunca puede ver a otro) y
 * sin las columnas de gestión que no le sirven a un alumno.
 */

$me = Auth::requireStudentSession();
$pdo = Db::get();

$stmt = $pdo->prepare(
    "SELECT att.hora_real, att.updated_at,
            a.id AS appointment_id, a.fecha, a.hora, a.nombre, a.apellido, a.procedimiento
     FROM attendances att
     JOIN appointments a ON a.id = att.appointment_id
     WHERE att.student_id = ? AND att.estado = 'atendido'
     ORDER BY att.updated_at DESC"
);
$stmt->execute([$me['id']]);
$attendances = $stmt->fetchAll();

$stmt = $pdo->prepare('SELECT user_id, client_ts, action, payload FROM action_logs WHERE user_id = ? ORDER BY id');
$stmt->execute([$me['id']]);
$sessions = Metrics::buildSessions(Metrics::decodeLogs($stmt->fetchAll()));
$sessionsByAppt = [];
foreach ($sessions as $s) {
    if ($s['appointment_id'] !== null) {
        $sessionsByAppt[(int) $s['appointment_id']][] = $s;
    }
}

student_header('Mis pacientes', $me);
?>
<h1>Pacientes que has atendido (<?= count($attendances) ?>)</h1>
<div class="card">
    <?php if (!$attendances): ?>
    <p class="empty">Todavía no has cerrado ninguna atención.</p>
    <?php else: ?>
    <div class="table-wrap">
    <table>
        <tr><th>Fecha</th><th>Paciente</th><th>Procedimiento</th><th>Duración</th><th>Bloques</th><th>Delta prom.</th><th>Pausas largas</th></tr>
        <?php foreach ($attendances as $a):
            $stats = Metrics::summarizeSessions($sessionsByAppt[(int) $a['appointment_id']] ?? []);
            // Duración real (Atender -> Atendido), mismo criterio que
            // admin/student.php -- más confiable que sumar action_logs.
            $duracionS = Metrics::attendanceDurationSeconds($a['hora_real'], $a['updated_at']);
        ?>
        <tr class="clickable" onclick="location.href='atencion.php?appointment_id=<?= (int) $a['appointment_id'] ?>'">
            <td><?= htmlspecialchars($a['fecha'] ?: '—') ?> <?= htmlspecialchars($a['hora'] ?: '') ?></td>
            <td><?= htmlspecialchars(trim("{$a['nombre']} {$a['apellido']}")) ?: '—' ?></td>
            <td><?= htmlspecialchars($a['procedimiento']) ?></td>
            <td><?= $duracionS !== null ? htmlspecialchars(Metrics::formatDurationHms($duracionS)) : '—' ?></td>
            <td><?= $stats['n_sessions'] ?></td>
            <td><?= $stats['avg_delta_s'] ?? '—' ?><?= $stats['avg_delta_s'] !== null ? 's' : '' ?></td>
            <td<?= $stats['long_pauses'] > 0 ? ' class="badge-warn"' : '' ?>><?= $stats['long_pauses'] ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <p class="legend">Pincha una fila para ver el detalle: tu conversación con el paciente (con la retroalimentación
        de tu docente si dejó alguna) y la ficha clínica.</p>
    <?php endif; ?>
</div>
<?php
student_footer();
