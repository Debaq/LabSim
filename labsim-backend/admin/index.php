<?php
require_once __DIR__ . '/layout.php';
$auth = require_admin();

// Obtener estadísticas
$totalUsers = Database::fetchOne("SELECT COUNT(*) as c FROM users WHERE is_active = 1")['c'];
$usersByRole = Database::fetchAll("SELECT role, COUNT(*) as count FROM users WHERE is_active = 1 GROUP BY role");
$totalCases = Database::fetchOne("SELECT COUNT(*) as c FROM cases")['c'];
$publishedCases = Database::fetchOne("SELECT COUNT(*) as c FROM cases WHERE is_published = 1")['c'];
$activeGroups = Database::fetchOne("SELECT COUNT(*) as c FROM student_groups WHERE is_active = 1")['c'];
$activeSessions = Database::fetchOne("SELECT COUNT(*) as c FROM practice_sessions WHERE status IN ('approved','active')")['c'];
$pendingApproval = Database::fetchOne("SELECT COUNT(*) as c FROM practice_sessions WHERE status = 'pending_approval'")['c'];
$pendingSubmissions = Database::fetchOne("SELECT COUNT(*) as c FROM submissions WHERE status = 'submitted'")['c'];
$totalAppSessions = Database::fetchOne("SELECT COUNT(*) as c FROM app_sessions")['c'];
$totalEvents = Database::fetchOne("SELECT COUNT(*) as c FROM simulator_events")['c'];

// Actividad reciente
$recentActivity = Database::fetchAll(
    "SELECT DATE(created_at) as date, COUNT(*) as sessions
     FROM app_sessions WHERE created_at > datetime('now', '-30 days')
     GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 14"
);

// Entregas recientes
$recentSubmissions = Database::fetchAll(
    "SELECT s.id, s.status, s.grade, s.submitted_at,
            u.username as student, c.title as caso, ps.title as sesion
     FROM submissions s
     JOIN users u ON s.student_id = u.id
     JOIN cases c ON s.case_id = c.id
     JOIN practice_sessions ps ON s.session_id = ps.id
     ORDER BY s.created_at DESC LIMIT 10"
);

render_header('Dashboard', 'dashboard');
?>

<div class="cards-grid">
    <div class="card card-stat">
        <div class="value"><?= $totalUsers ?></div>
        <div class="label">Usuarios activos</div>
    </div>
    <div class="card card-stat">
        <div class="value"><?= $totalCases ?></div>
        <div class="label">Casos clínicos (<?= $publishedCases ?> publicados)</div>
    </div>
    <div class="card card-stat">
        <div class="value"><?= $activeGroups ?></div>
        <div class="label">Grupos activos</div>
    </div>
    <div class="card card-stat">
        <div class="value"><?= $activeSessions ?></div>
        <div class="label">Sesiones activas</div>
    </div>
    <div class="card card-stat">
        <div class="value" style="color: var(--warning)"><?= $pendingApproval ?></div>
        <div class="label">Sesiones pendientes aprobación</div>
    </div>
    <div class="card card-stat">
        <div class="value" style="color: var(--info)"><?= $pendingSubmissions ?></div>
        <div class="label">Entregas por revisar</div>
    </div>
    <div class="card card-stat">
        <div class="value"><?= $totalAppSessions ?></div>
        <div class="label">Sesiones de app (telemetría)</div>
    </div>
    <div class="card card-stat">
        <div class="value"><?= number_format($totalEvents) ?></div>
        <div class="label">Eventos de simulador</div>
    </div>
</div>

<h2 style="margin-bottom:15px">Usuarios por rol</h2>
<div class="cards-grid" style="margin-bottom:30px">
    <?php foreach ($usersByRole as $r): ?>
    <div class="card" style="display:flex;align-items:center;gap:12px">
        <?= render_badge($r['role'], $r['role']) ?>
        <span style="font-size:1.2rem;font-weight:600"><?= $r['count'] ?></span>
    </div>
    <?php endforeach; ?>
</div>

<?php if ($pendingSubmissions > 0): ?>
<h2 style="margin-bottom:15px">Entregas recientes</h2>
<?php
render_table(
    ['Estudiante', 'Caso', 'Sesión', 'Estado', 'Nota', 'Fecha'],
    $recentSubmissions,
    function($s) {
        $statusMap = [
            'submitted' => ['Enviada', 'info'],
            'reviewed' => ['Calificada', 'success'],
            'returned' => ['Devuelta', 'warning'],
        ];
        $sm = $statusMap[$s['status']] ?? [$s['status'], 'default'];
        $statusBadge = render_badge($sm[0], $sm[1]);
        $grade = $s['grade'] !== null ? number_format($s['grade'], 1) : '—';
        $date = $s['submitted_at'] ? date('d M Y', strtotime($s['submitted_at'])) : '—';
        return "<tr>
            <td>" . htmlspecialchars($s['student']) . "</td>
            <td>" . htmlspecialchars($s['caso']) . "</td>
            <td>" . htmlspecialchars($s['sesion']) . "</td>
            <td>$statusBadge</td>
            <td>$grade</td>
            <td>$date</td>
        </tr>";
    }
);
?>
<?php endif; ?>

<?php if (!empty($recentActivity)): ?>
<h2 style="margin:25px 0 15px">Actividad últimos 14 días</h2>
<div class="card" style="padding:20px">
    <div style="display:flex;align-items:flex-end;gap:4px;height:120px">
        <?php
        $maxSessions = max(array_column($recentActivity, 'sessions'));
        foreach (array_reverse($recentActivity) as $day):
            $height = $maxSessions > 0 ? ($day['sessions'] / $maxSessions * 100) : 0;
            $date = date('d/m', strtotime($day['date']));
        ?>
        <div style="flex:1;display:flex;flex-direction:column;align-items:center;gap:4px">
            <span style="font-size:0.7rem;color:var(--text-muted)"><?= $day['sessions'] ?></span>
            <div style="width:100%;background:var(--accent);border-radius:3px 3px 0 0;height:<?= $height ?>px;min-height:2px"></div>
            <span style="font-size:0.65rem;color:var(--text-muted)"><?= $date ?></span>
        </div>
        <?php endforeach; ?>
    </div>
</div>
<?php endif; ?>

<?php render_footer(); ?>
