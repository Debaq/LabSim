<?php
require_once __DIR__ . '/layout.php';
$auth = require_admin();

$from = $_GET['from'] ?? date('Y-m-d', strtotime('-30 days'));
$to = $_GET['to'] ?? date('Y-m-d');

// Métricas generales en rango
$encounterStats = Database::fetchOne(
    "SELECT COUNT(*) as total, AVG(total_duration_secs) as avg_duration,
            MIN(total_duration_secs) as min_duration, MAX(total_duration_secs) as max_duration,
            AVG(modules_completed) as avg_modules
     FROM patient_encounter_stats WHERE started_at >= :from AND started_at <= :to",
    [':from' => $from, ':to' => "$to 23:59:59"]
);

// Top estudiantes por actividad
$topStudents = Database::fetchAll(
    "SELECT u.username, u.full_name, COUNT(pes.id) as encounters,
            AVG(pes.total_duration_secs) as avg_duration, AVG(sub.grade) as avg_grade
     FROM users u
     LEFT JOIN patient_encounter_stats pes ON pes.user_id = u.id AND pes.started_at >= :from AND pes.started_at <= :to
     LEFT JOIN submissions sub ON sub.student_id = u.id AND sub.status = 'reviewed'
     WHERE u.role = 'estudiante' AND u.is_active = 1
     GROUP BY u.id HAVING encounters > 0
     ORDER BY encounters DESC LIMIT 15",
    [':from' => $from, ':to' => "$to 23:59:59"]
);

// Uso por simulador
$simulatorUsage = Database::fetchAll(
    "SELECT simulator, COUNT(*) as events, COUNT(DISTINCT user_id) as users
     FROM simulator_events
     WHERE event_timestamp >= :from AND event_timestamp <= :to
     GROUP BY simulator ORDER BY events DESC",
    [':from' => $from, ':to' => "$to 23:59:59"]
);

// Tiempos promedio por módulo
$moduleAvgs = Database::fetchAll(
    "SELECT module_id, AVG(time_spent_secs) as avg_time, COUNT(*) as uses
     FROM module_interaction_stats
     WHERE first_opened_at >= :from OR last_saved_at <= :to
     GROUP BY module_id ORDER BY avg_time DESC",
    [':from' => $from, ':to' => "$to 23:59:59"]
);

// Distribución de calificaciones
$gradeDistribution = Database::fetchAll(
    "SELECT
        CASE WHEN grade >= 9 THEN 'Excelente (9-10)'
             WHEN grade >= 7 THEN 'Bueno (7-8.9)'
             WHEN grade >= 5 THEN 'Aprobado (5-6.9)'
             ELSE 'Reprobado (<5)' END as range,
        COUNT(*) as count
     FROM submissions WHERE status = 'reviewed' AND grade IS NOT NULL
     GROUP BY range ORDER BY MIN(grade) DESC"
);

render_header('Estadísticas', 'stats');
?>

<div class="toolbar" style="margin-bottom:20px">
    <form class="toolbar-filters" method="GET">
        <label style="font-size:0.85rem;color:var(--text-secondary)">Desde:</label>
        <input type="date" name="from" value="<?= $from ?>">
        <label style="font-size:0.85rem;color:var(--text-secondary)">Hasta:</label>
        <input type="date" name="to" value="<?= $to ?>">
        <button type="submit" class="btn btn-sm btn-primary">Filtrar</button>
    </form>
    <a href="../api/index.php?route=stats/export&format=csv&from=<?= $from ?>&to=<?= $to ?>"
       class="btn btn-sm btn-outline" target="_blank">Exportar CSV</a>
</div>

<div class="cards-grid">
    <div class="card card-stat">
        <div class="value"><?= $encounterStats['total'] ?? 0 ?></div>
        <div class="label">Encuentros en período</div>
    </div>
    <div class="card card-stat">
        <div class="value"><?= $encounterStats['avg_duration'] ? round($encounterStats['avg_duration'] / 60, 1) . 'm' : '—' ?></div>
        <div class="label">Duración promedio</div>
    </div>
    <div class="card card-stat">
        <div class="value"><?= round($encounterStats['avg_modules'] ?? 0, 1) ?></div>
        <div class="label">Módulos prom. completados</div>
    </div>
</div>

<?php if (!empty($topStudents)): ?>
<h2 style="margin:25px 0 15px">Top estudiantes</h2>
<?php
render_table(
    ['Estudiante', 'Encuentros', 'Duración prom.', 'Nota prom.'],
    $topStudents,
    function($s) {
        $avgDur = $s['avg_duration'] ? round($s['avg_duration'] / 60, 1) . ' min' : '—';
        $avgGrade = $s['avg_grade'] !== null ? number_format($s['avg_grade'], 1) : '—';
        return "<tr>
            <td><strong>" . htmlspecialchars($s['full_name'] ?? $s['username']) . "</strong></td>
            <td>{$s['encounters']}</td>
            <td>$avgDur</td>
            <td>$avgGrade</td>
        </tr>";
    }
);
endif; ?>

<?php if (!empty($simulatorUsage)): ?>
<h2 style="margin:25px 0 15px">Uso por simulador</h2>
<?php render_table(['Simulador', 'Eventos', 'Usuarios únicos'], $simulatorUsage, function($s) {
    return "<tr><td><strong>" . htmlspecialchars($s['simulator']) . "</strong></td><td>" . number_format($s['events']) . "</td><td>{$s['users']}</td></tr>";
});
endif; ?>

<?php if (!empty($moduleAvgs)): ?>
<h2 style="margin:25px 0 15px">Tiempo promedio por módulo</h2>
<?php render_table(['Módulo', 'Tiempo promedio', 'Usos'], $moduleAvgs, function($m) {
    $time = $m['avg_time'] ? round($m['avg_time'] / 60, 1) . ' min' : '—';
    return "<tr><td><strong>" . htmlspecialchars($m['module_id']) . "</strong></td><td>$time</td><td>{$m['uses']}</td></tr>";
});
endif; ?>

<?php if (!empty($gradeDistribution)): ?>
<h2 style="margin:25px 0 15px">Distribución de calificaciones</h2>
<div class="card" style="padding:20px">
    <?php foreach ($gradeDistribution as $g):
        $maxCount = max(array_column($gradeDistribution, 'count'));
        $width = $maxCount > 0 ? ($g['count'] / $maxCount * 100) : 0;
        $color = (strpos($g['range'], 'Excelente') !== false) ? 'var(--success)' :
                ((strpos($g['range'], 'Bueno') !== false) ? 'var(--accent)' :
                ((strpos($g['range'], 'Aprobado') !== false) ? 'var(--warning)' : 'var(--danger)'));
    ?>
    <div style="display:flex;align-items:center;gap:12px;margin-bottom:8px">
        <span style="width:150px;font-size:0.85rem"><?= $g['range'] ?></span>
        <div style="flex:1;background:var(--bg-primary);border-radius:4px;height:24px">
            <div style="background:<?= $color ?>;width:<?= $width ?>%;height:100%;border-radius:4px;display:flex;align-items:center;padding-left:8px;font-size:0.75rem;font-weight:600;min-width:30px">
                <?= $g['count'] ?>
            </div>
        </div>
    </div>
    <?php endforeach; ?>
</div>
<?php endif; ?>

<?php render_footer(); ?>
