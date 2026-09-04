<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Metrics.php';
require_once __DIR__ . '/../../src/Courses.php';

$me = Auth::requireAdminSession();
$pdo = Db::get();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;

$studentId = (int) ($_GET['id'] ?? 0);
// Sin filtro de role: si el usuario después pasó a docente/admin, su
// actividad histórica como alumno no debería desaparecer de esta vista.
$stmt = $pdo->prepare('SELECT * FROM users WHERE id = ?');
$stmt->execute([$studentId]);
$student = $stmt->fetch();

// Docente: solo fichas de alumnos matriculados en su(s) curso(s) -- mismo
// scoping que dashboard.php/agenda.php.
if ($student && !$isFullAdmin) {
    $roster = Courses::rosterUserIds(Courses::teacherCourseIds((int) $me['id']));
    if (!in_array($studentId, $roster, true)) {
        $student = null;
    }
}

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
    "SELECT m.id, m.tipo, m.remitente, m.asunto, m.cuerpo, m.created_at,
            a.id AS appointment_id, a.fecha, a.hora, a.procedimiento
     FROM inbox_messages m
     LEFT JOIN appointments a ON a.id = m.appointment_id
     WHERE m.student_id = ?
     ORDER BY m.created_at DESC"
);
$stmt->execute([$studentId]);
$inboxMessages = $stmt->fetchAll();

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

$stmt = $pdo->prepare('SELECT user_id, client_ts, action, payload FROM action_logs WHERE user_id = ? ORDER BY id');
$stmt->execute([$studentId]);
$allLogs = Metrics::decodeLogs($stmt->fetchAll());
$sessions = Metrics::buildSessions($allLogs);
$behaviorStats = Metrics::summarizeSessions($sessions);
$weekly = Metrics::sessionsByWeek($sessions);
$histogram = Metrics::deltaHistogram($sessions);
$histTotal = array_sum($histogram) ?: 1;

// buildSessions() ya corta una sesión nueva cuando cambia appointment_id/case_id
// (ver Metrics::buildSessions), así que agrupar por ahí separa correctamente
// las métricas de comportamiento por atención -- necesario porque en una
// misma sesión de trabajo el alumno puede pasar por más de un paciente y el
// análisis (para nota/feedback) es por caso, no por el total mezclado.
$sessionsByAppt = [];
foreach ($sessions as $s) {
    $key = $s['appointment_id'] !== null ? (int) $s['appointment_id'] : 0;
    $sessionsByAppt[$key][] = $s;
}
$statsByAppt = [];
foreach ($sessionsByAppt as $key => $group) {
    $stats = Metrics::summarizeSessions($group);
    // total_duration_s de summarizeSessions() suma solo los bloques activos
    // y esconde pausas >5min dentro de la misma atención (ver
    // Metrics::wallClockDurationSeconds) -- acá sí queremos el reloj real,
    // porque es lo que se compara contra "cuánto duró la atención" cronometrado.
    $stats['total_duration_s'] = Metrics::wallClockDurationSeconds($group);
    $statsByAppt[$key] = $stats;
}

// Duración total del resumen: mismo criterio real por atención que usa la
// tabla "Atenciones" (hora_real->updated_at si está cerrada, si no reloj
// real de bloques) -- $behaviorStats['total_duration_s'] no sirve acá
// porque solo suma bloques activos y esconde pausas largas (ver comentario
// arriba y Metrics::wallClockDurationSeconds).
$totalDurationRealS = 0;
foreach ($attendances as $a) {
    $aStats = $statsByAppt[(int) $a['appointment_id']] ?? null;
    $realDuration = $a['estado'] === 'atendido'
        ? Metrics::attendanceDurationSeconds($a['hora_real'], $a['updated_at'])
        : null;
    $totalDurationRealS += $realDuration ?? ($aStats['total_duration_s'] ?? 0);
}

admin_header('Alumno: ' . $student['display_name'], $me);
?>
<style>
    .week-bar { display: inline-block; height: 10px; background: #1a2744; border-radius: 2px; margin-right: 0.4rem; vertical-align: middle; }
    .hist-bar { display: flex; width: 100%; max-width: 24rem; height: 16px; border-radius: 3px; overflow: hidden; background: #eee; margin-top: 0.4rem; }
    .hist-bar span { height: 100%; display: block; }
    .legend { font-size: 0.78rem; color: #777; margin-top: 0.4rem; }
</style>
<div class="card">
    <p>
        <strong><?= htmlspecialchars($student['display_name']) ?></strong>
        &nbsp;·&nbsp; <span class="mono"><?= htmlspecialchars($student['username']) ?></span>
        &nbsp;·&nbsp; <?= $student['active'] ? 'activo' : 'inactivo' ?>
        &nbsp;·&nbsp; alumno desde <?= htmlspecialchars($student['created_at']) ?>
        &nbsp;·&nbsp; <a href="ver_como.php?id=<?= (int) $studentId ?>">Ver como alumno →</a>
    </p>
</div>

<div class="card">
    <strong>Resumen</strong>
    <p class="legend">Total acumulado de <strong>todas</strong> las atenciones del alumno (todos los pacientes juntos) -- para ver el detalle caso por caso, revisa la tabla "Atenciones" más abajo.</p>
    <table>
        <tr><td>Atendiendo (en curso)</td><td><strong><?= $estadoCounts['atendiendo'] ?></strong></td></tr>
        <tr><td>Atendidos (cerrados)</td><td><strong><?= $estadoCounts['atendido'] ?></strong></td></tr>
        <tr><td>No-show</td><td><strong><?= $estadoCounts['no_show'] ?></strong></td></tr>
        <tr><td>Acciones registradas (total)</td><td><strong><?= $totalActions ?></strong></td></tr>
        <tr><td>Sesiones (login-logout)</td><td><strong><?= Metrics::countLoginSessions($allLogs) ?></strong></td></tr>
        <tr><td>Atenciones (pacientes distintos)</td><td><strong><?= Metrics::countAttentions($allLogs) ?></strong></td></tr>
        <tr><td>Bloques de actividad</td><td><strong><?= $behaviorStats['n_sessions'] ?></strong></td></tr>
        <tr><td>Duración total</td><td><strong><?= htmlspecialchars(Metrics::formatDurationHms($totalDurationRealS)) ?></strong></td></tr>
        <tr><td>Delta promedio entre acciones</td><td><strong><?= isset($behaviorStats['avg_delta_s']) ? htmlspecialchars(Metrics::formatDurationHms((int) round($behaviorStats['avg_delta_s']))) : '—' ?></strong></td></tr>
        <tr><td>Pausas largas (≥30s)</td><td><strong<?= $behaviorStats['long_pauses'] > 0 ? ' class="badge-warn"' : '' ?>><?= $behaviorStats['long_pauses'] ?></strong></td></tr>
        <tr><td>Acciones sin pausa (0s)</td><td><strong><?= $behaviorStats['no_pause_actions'] ?></strong></td></tr>
    </table>
    <div class="hist-bar" title="0s: <?= $histogram['0s'] ?? 0 ?> · 1-5s: <?= $histogram['1-5s'] ?? 0 ?> · 6-15s: <?= $histogram['6-15s'] ?? 0 ?> · 16-30s: <?= $histogram['16-30s'] ?? 0 ?> · 30s+: <?= $histogram['30s+'] ?? 0 ?>">
        <?php foreach (['0s' => '#2e7d32', '1-5s' => '#9ccc65', '6-15s' => '#ffb300', '16-30s' => '#fb8c00', '30s+' => '#c0392b'] as $bucket => $color):
            $pct = round((($histogram[$bucket] ?? 0) / $histTotal) * 100, 1);
            if ($pct <= 0) { continue; }
        ?>
        <span style="width:<?= $pct ?>%; background:<?= $color ?>;"></span>
        <?php endforeach; ?>
    </div>
    <p class="legend">Distribución de pausas entre acciones: verde (sin pausa) a rojo (pausa ≥30s).</p>
</div>

<div class="card">
    <strong>Evolución semanal</strong>
    <p class="legend">Bloques de actividad (corte por atención distinta o &gt;5 min de pausa) y delta promedio por semana -- para ver si el alumno mejora (deltas bajando) con el tiempo.</p>
    <table>
        <tr><th>Semana</th><th>Bloques</th><th>Delta promedio</th></tr>
        <?php $maxSessions = max(array_column($weekly, 'n_sessions') ?: [1]); ?>
        <?php foreach ($weekly as $week => $w): ?>
        <tr>
            <td><?= htmlspecialchars($week) ?></td>
            <td><span class="week-bar" style="width:<?= round(($w['n_sessions'] / $maxSessions) * 100, 1) ?>%;"></span><?= $w['n_sessions'] ?></td>
            <td><?= isset($w['avg_delta_s']) ? htmlspecialchars(Metrics::formatDurationHms((int) round($w['avg_delta_s']))) : '—' ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$weekly): ?>
        <tr><td colspan="3" style="color:#888;">Sin datos suficientes todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>

<div class="card">
    <strong>Atenciones (<?= count($attendances) ?>)</strong>
    <p class="legend">Comportamiento aislado por cada atención (cita/paciente) -- así un caso no ensucia las métricas de otro cuando el alumno revisó más de uno.</p>
    <table>
        <tr><th>Cita</th><th>Paciente</th><th>Procedimiento</th><th>Estado</th><th>Bloques</th><th>Duración</th><th>Delta prom.</th><th>Pausas largas</th><th>Hora real</th><th>Nota</th><th>Actualizado</th><th>Detalle</th></tr>
        <?php foreach ($attendances as $a):
            $aStats = $statsByAppt[(int) $a['appointment_id']] ?? null;
            // Duración real (Atender -> Atendido) siempre que esté cerrada;
            // más confiable que el cálculo por action_logs, que arranca recién
            // cuando el alumno toca el audiómetro/impedanciómetro y se pierde
            // el rato leyendo el caso -- ver Metrics::attendanceDurationSeconds.
            $realDuration = $a['estado'] === 'atendido'
                ? Metrics::attendanceDurationSeconds($a['hora_real'], $a['updated_at'])
                : null;
            $durationS = $realDuration ?? ($aStats['total_duration_s'] ?? null);
        ?>
        <tr>
            <td><a href="dashboard.php?appointment_id=<?= (int) $a['appointment_id'] ?>&student_id=<?= (int) $studentId ?>#student-<?= (int) $studentId ?>">#<?= (int) $a['appointment_id'] ?> (<?= htmlspecialchars($a['fecha'] ?: '—') ?> <?= htmlspecialchars($a['hora'] ?: '') ?>)</a></td>
            <td><?= htmlspecialchars(trim("{$a['nombre']} {$a['apellido']}")) ?: '—' ?></td>
            <td><?= htmlspecialchars($a['procedimiento']) ?></td>
            <td><?= htmlspecialchars($a['estado']) ?></td>
            <td><?= $aStats['n_sessions'] ?? '—' ?></td>
            <td><?= $durationS !== null ? htmlspecialchars(Metrics::formatDurationHms((int) $durationS)) : '—' ?></td>
            <td><?= isset($aStats['avg_delta_s']) ? htmlspecialchars(Metrics::formatDurationHms((int) round($aStats['avg_delta_s']))) : '—' ?></td>
            <td<?= ($aStats['long_pauses'] ?? 0) > 0 ? ' class="badge-warn"' : '' ?>><?= $aStats['long_pauses'] ?? '—' ?></td>
            <td><?= htmlspecialchars($a['hora_real'] ?: '—') ?></td>
            <td style="font-size:0.85rem;"><?= htmlspecialchars($a['nota'] ?: '—') ?></td>
            <td><?= htmlspecialchars($a['updated_at']) ?></td>
            <td><a href="chat_detail.php?appointment_id=<?= (int) $a['appointment_id'] ?>&student_id=<?= (int) $studentId ?>">Ver atención</a></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$attendances): ?>
        <tr><td colspan="12" style="color:#888;">Sin atenciones registradas todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>

<?php
$tipoLabels = ['reclamo' => 'Reclamo', 'merito' => 'Mérito', 'mensaje' => 'Mensaje docente'];
?>
<div class="card">
    <strong>Bandeja de entrada (<?= count($inboxMessages) ?>)</strong>
    <p class="legend">Avisos automáticos sobre el trato a pacientes (ver Admin -> IA Paciente) y mensajes que algún docente le mandó directo. Misma bandeja que ve el alumno en la app.</p>
    <table>
        <tr><th>Tipo</th><th>Remitente</th><th>Cita</th><th>Asunto</th><th>Cuerpo</th><th>Fecha</th></tr>
        <?php foreach ($inboxMessages as $m): ?>
        <tr>
            <td<?= $m['tipo'] === 'reclamo' ? ' class="badge-warn"' : '' ?>><?= htmlspecialchars($tipoLabels[$m['tipo']] ?? $m['tipo']) ?></td>
            <td><?= htmlspecialchars($m['remitente']) ?></td>
            <td><?= $m['appointment_id'] ? '#' . (int) $m['appointment_id'] . ' (' . htmlspecialchars($m['fecha'] ?: '—') . ' ' . htmlspecialchars($m['hora'] ?: '') . ') -- ' . htmlspecialchars($m['procedimiento']) : '—' ?></td>
            <td><?= htmlspecialchars($m['asunto']) ?></td>
            <td style="font-size:0.85rem;"><?= htmlspecialchars($m['cuerpo']) ?></td>
            <td><?= htmlspecialchars($m['created_at']) ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$inboxMessages): ?>
        <tr><td colspan="6" style="color:#888;">Sin mensajes todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>

<div class="card">
    <strong>Acciones por tipo</strong>
    <table>
        <tr><th>Acción</th><th>Veces</th><th>Última vez</th></tr>
        <?php foreach ($actionCounts as $ac): ?>
        <tr>
            <td><?= htmlspecialchars(Metrics::actionLabel($ac['action'])) ?> <span class="mono" style="font-size:0.75rem; color:#888;"><?= htmlspecialchars($ac['action']) ?></span></td>
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
    &nbsp;·&nbsp;
    <a href="logs_download.php?id=<?= (int) $studentId ?>">Descargar registro completo (CSV, <?= $totalActions ?>)</a>
    &nbsp;·&nbsp;
    <a href="dashboard_report.php?student_id=<?= (int) $studentId ?>">Descargar informe de sesiones (CSV)</a>
    <table>
        <tr><th>Cuándo (cliente)</th><th>Acción</th><th>Payload</th></tr>
        <?php foreach ($recentLogs as $log): ?>
        <tr>
            <td><?= htmlspecialchars($log['client_ts']) ?></td>
            <td><?= htmlspecialchars(Metrics::actionLabel($log['action'])) ?></td>
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
