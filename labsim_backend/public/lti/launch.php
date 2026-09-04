<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Metrics.php';

/**
 * Un JSON crudo de error acá lo ve el alumno en el navegador (esta página
 * la abre el iframe de Moodle o una pestaña nueva, no una app que interprete
 * el JSON) -- muestra una página legible en su lugar, con la acción que
 * puede tomar.
 */
function render_launch_error(string $message): void
{
    header('Content-Type: text/html; charset=utf-8');
    ?>
    <!doctype html>
    <html lang="es">
    <head><meta charset="utf-8"><title>LabSim</title></head>
    <body style="font-family: sans-serif; text-align: center; margin-top: 4rem;">
        <h1>No se pudo generar el código</h1>
        <p><?= htmlspecialchars($message) ?></p>
        <p>Vuelve a abrir la actividad desde la plataforma para intentarlo de nuevo.</p>
    </body>
    </html>
    <?php
    exit;
}

// LTI 1.1 llega como un solo POST directo (firmado OAuth1), sin pasar por
// login.php; LTI 1.3 llega vía el redirect OIDC (id_token + state).
// platformId/contextId solo se llenan en un launch no-replay (recién ahí hay
// claims/params confiables) -- ver Lti::autoEnrollIfMapped/findCourseForContext.
$platformId = null;
$contextId = null;

if (isset($_POST['oauth_consumer_key'])) {
    try {
        $result = Lti::validateLaunch11($_POST);
    } catch (RuntimeException $e) {
        render_launch_error('Launch LTI 1.1 inválido: ' . $e->getMessage());
    }
    if ($result['replay'] ?? false) {
        $userId = $result['user_id'];
        $previousCode = $result['issued_code'];
    } else {
        $userId = Lti::upsertStudentFromLti11($result['platform'], $result['params']);
        $previousCode = null;
        $platformId = (int) $result['platform']['id'];
        $contextId = $result['params']['context_id'] ?? null;
        $contextLabel = $result['params']['context_title'] ?? ($result['params']['context_label'] ?? null);
        Lti::autoEnrollIfMapped($platformId, $contextId, $userId);
        Lti::recordContextSighting($userId, $platformId, $contextId, $contextLabel);
    }
    $markCode = static fn (string $code) => Lti::markNonceCode($result['consumer_key'], $result['nonce'], $userId, $code);
    $refreshKey = 'nonce:' . $result['consumer_key'] . '|' . $result['nonce'];
} else {
    $idToken = $_POST['id_token'] ?? '';
    $state = $_POST['state'] ?? '';

    if ($idToken === '' || $state === '') {
        render_launch_error('Launch LTI incompleto.');
    }

    try {
        $result = Lti::validateLaunch($idToken, $state);
    } catch (RuntimeException $e) {
        render_launch_error('Launch LTI 1.3 inválido: ' . $e->getMessage());
    }
    if ($result['replay'] ?? false) {
        $userId = $result['user_id'];
        $previousCode = $result['issued_code'];
    } else {
        $userId = Lti::upsertStudent($result['platform'], $result['claims']);
        $previousCode = null;
        $platformId = (int) $result['platform']['id'];
        $contextClaim = $result['claims']['https://purl.imsglobal.org/spec/lti/claim/context'] ?? [];
        $contextId = $contextClaim['id'] ?? null;
        $contextLabel = $contextClaim['title'] ?? ($contextClaim['label'] ?? null);
        Lti::autoEnrollIfMapped($platformId, $contextId, $userId);
        Lti::recordContextSighting($userId, $platformId, $contextId, $contextLabel);
    }
    $markCode = static fn (string $code) => Lti::markStateCode($state, $userId, $code);
    $refreshKey = 'state:' . $state;
}

$issued = Auth::codeForLaunch($userId, $previousCode);
if ($issued['renewed']) {
    $markCode($issued['code']);
}

$code = $issued['code'];
$expiresIn = Auth::secondsUntil($issued['expires_at']);

// Docente/admin promovido a mano desde el panel (ver admin/users.php) --
// LTI siempre crea la cuenta como role='student', así que esto solo es
// true si un admin ya lo ascendió antes de este launch. Se abre sesión de
// portal acá mismo porque el launch LTI ya autenticó al usuario; no tiene
// contraseña de portal para hacer login normal.
$stmt = Db::get()->prepare("SELECT role, active FROM users WHERE id = ?");
$stmt->execute([$userId]);
$userRow = $stmt->fetch();
$isPortalUser = $userRow && $userRow['role'] === 'admin' && (int) $userRow['active'] === 1;
// launch.php corre dentro del iframe de Moodle -- cookie de tercero, no
// sirve para levantar la sesión de portal ahí mismo (varios navegadores la
// descartan). El botón manda a admin/sso.php, que canjea este token de un
// solo uso en una pestaña nueva (primer partido) y ahí sí levanta la sesión.
// Si este curso de Moodle todavía no está vinculado a un curso de LabSim,
// se manda al docente/admin directo a courses.php con el contexto en la URL
// para que lo vincule ahí (una vez) -- ver comentario de course_lti_contexts
// en schema.sql y el bloque "link_lti_context" en admin/courses.php.
$needsLtiLink = $isPortalUser && $platformId !== null && $contextId !== null
    && Lti::findCourseForContext($platformId, $contextId) === null;
$portalUrl = $isPortalUser
    ? '../admin/sso.php?token=' . urlencode(Auth::issuePortalSsoToken($userId))
        . ($needsLtiLink ? '&link_platform=' . $platformId . '&link_context=' . urlencode($contextId) : '')
    : null;

// Stats embebidas en la misma pantalla del código (el docente/alumno no
// entra a la plataforma para verlas -- ver dashboard.php para el detalle
// completo por sesión, esto es solo el resumen a simple vista).
if ($isPortalUser) {
    // Docente/admin: agregado de todos los alumnos (mismo criterio sin
    // filtro que dashboard.php -- no hay noción de "curso" en el schema,
    // cada instalación de LabSim es de un solo cliente/institución).
    // Un ranking top-10 no le dice al docente qué hacer -- lo accionable es
    // quién no ha partido, cómo va la participación general, y si la
    // actividad se frenó últimamente.
    $allStudents = Db::get()->query("SELECT id, display_name FROM users WHERE role = 'student' AND active = 1")->fetchAll();
    $totalStudents = count($allStudents);

    $rows = Db::get()->query(
        "SELECT al.* FROM action_logs al JOIN users u ON u.id = al.user_id WHERE u.role = 'student' ORDER BY al.id"
    )->fetchAll();
    $logsByUser = [];
    foreach (Metrics::decodeLogs($rows) as $log) {
        $logsByUser[(int) $log['user_id']][] = $log;
    }

    $noActivity = [];
    $totalAttentions = 0;
    $activeStudents = 0;
    foreach ($allStudents as $s) {
        $n = Metrics::countAttentions($logsByUser[(int) $s['id']] ?? []);
        if ($n === 0) {
            $noActivity[] = $s['display_name'];
        } else {
            $activeStudents++;
            $totalAttentions += $n;
        }
    }
    $avgAttentions = $activeStudents > 0 ? round($totalAttentions / $activeStudents, 1) : 0;

    // Últimos 7 días vs los 7 anteriores -- ¿la actividad se frenó? La clave
    // incluye user_id: la agenda es cola compartida, distintos alumnos
    // pueden atender la misma cita, cada uno cuenta su propia atención.
    $recentCutoff = time() - 7 * 86400;
    $priorCutoff = time() - 14 * 86400;
    $recentSet = [];
    $priorSet = [];
    foreach ($logsByUser as $uid => $logsForUser) {
        foreach ($logsForUser as $log) {
            if (!($log['con_paciente'] ?? false)) {
                continue;
            }
            $ts = strtotime((string) $log['client_ts']) ?: 0;
            $key = $uid . '|' . ($log['case_id'] ?? '') . '|' . ($log['appointment_id'] ?? '');
            if ($ts >= $recentCutoff) {
                $recentSet[$key] = true;
            } elseif ($ts >= $priorCutoff) {
                $priorSet[$key] = true;
            }
        }
    }
    $recentAttentions = count($recentSet);
    $priorAttentions = count($priorSet);
} else {
    $stmt = Db::get()->prepare('SELECT * FROM action_logs WHERE user_id = ? ORDER BY id');
    $stmt->execute([$userId]);
    $myLogs = Metrics::decodeLogs($stmt->fetchAll());
    $mySessions = Metrics::buildSessions($myLogs);
    $mySummary = Metrics::summarizeSessions($mySessions);
    $myAttentions = Metrics::countAttentions($myLogs);
    $myWeeks = Metrics::attentionsByWeek($myLogs);

    // Última atención: mismo detalle (timeline por bloques + comportamiento)
    // que ve el docente en admin/dashboard.php para un alumno puntual, pero
    // acotado al caso/cita más reciente del propio alumno -- ver
    // Metrics::buildSessions para el criterio de corte por bloque.
    $lastAttentionKey = null;
    $lastAttentionEnd = null;
    foreach ($mySessions as $s) {
        if (!$s['con_paciente']) {
            continue;
        }
        if ($lastAttentionEnd === null || $s['end'] > $lastAttentionEnd) {
            $lastAttentionEnd = $s['end'];
            $lastAttentionKey = ['appointment_id' => $s['appointment_id'], 'case_id' => $s['case_id']];
        }
    }
    $lastAttentionSessions = [];
    $lastAttentionAppt = null;
    if ($lastAttentionKey !== null) {
        foreach ($mySessions as $s) {
            if ($s['appointment_id'] === $lastAttentionKey['appointment_id'] && $s['case_id'] === $lastAttentionKey['case_id']) {
                $lastAttentionSessions[] = $s;
            }
        }
        $lastAttentionStats = Metrics::summarizeSessions($lastAttentionSessions);
        // Leyenda de colores no interactiva: el alumno ve esto en el iframe
        // de Moodle (a veces desde el celular), no puede pasar el mouse
        // sobre cada barra como el docente en dashboard.php -- necesita el
        // significado de cada color a simple vista.
        $lastAttentionLegend = [];
        foreach ($lastAttentionSessions as $s) {
            foreach ($s['actions'] as $a) {
                $lastAttentionLegend[(string) $a['action']] = Metrics::actionLabel((string) $a['action']);
            }
        }
        asort($lastAttentionLegend);
        if ($lastAttentionKey['appointment_id'] !== null) {
            $stmt = Db::get()->prepare('SELECT nombre, apellido, procedimiento FROM appointments WHERE id = ?');
            $stmt->execute([(int) $lastAttentionKey['appointment_id']]);
            $lastAttentionAppt = $stmt->fetch() ?: null;
        }
    }
}

// hue estable por tipo de acción -- mismo criterio que admin/dashboard.php
// (crc32 del nombre técnico) para que un alumno vea el mismo color que su
// docente si comparan pantallas.
function launch_action_hue(string $action): int
{
    return crc32($action) % 360;
}

function render_attention_timeline(array $session): void
{
    ?>
    <div class="session-meta">
        <?= htmlspecialchars((string) $session['start']) ?> &rarr; <?= htmlspecialchars((string) $session['end']) ?>
        &nbsp;·&nbsp; <?= $session['n_actions'] ?> acciones &nbsp;·&nbsp; <?= $session['duration_s'] ?>s
    </div>
    <div class="timeline">
        <?php foreach ($session['actions'] as $a):
            $delta = $a['delta_s'];
            $w = $delta === null ? 6 : (int) min(max($delta, 0) * 5, 200);
            $w = max($w, 6);
            $hue = launch_action_hue((string) $a['action']);
            $isPause = $delta !== null && $delta >= 30;
            $title = Metrics::actionLabel((string) $a['action']) . ' · ' . ($delta === null ? 'inicio de sesión' : $delta . 's desde la acción anterior');
        ?>
        <div class="tl-seg<?= $isPause ? ' tl-pause' : '' ?>"
             style="width:<?= $w ?>px; background:hsl(<?= $hue ?>,60%,55%);"
             title="<?= htmlspecialchars($title) ?>"></div>
        <?php endforeach; ?>
    </div>
    <?php
}

header('Content-Type: text/html; charset=utf-8');
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>LabSim</title>
<style>
    body { font-family: sans-serif; text-align: center; margin-top: 4rem; }
    .code { font-size: 3rem; font-weight: bold; letter-spacing: 0.3em; }
    .countdown.low { color: #c00; font-weight: bold; }
    button { font-size: 1rem; padding: 0.6rem 1.4rem; margin-top: 1.5rem; cursor: pointer; }
    .status { min-height: 1.2em; color: #555; }
    .stats { margin-top: 2.5rem; text-align: left; max-width: 560px; margin-left: auto; margin-right: auto; }
    .stats h2 { font-size: 1.1rem; text-align: center; }
    .stats-summary, .stats-caption { text-align: center; color: #555; font-size: 0.9rem; }
    .stats-empty { text-align: center; color: #888; font-size: 0.9rem; }
    .chart-wrap { max-height: 320px; margin-top: 0.5rem; }
    .no-activity-list { columns: 2; column-gap: 1.5rem; font-size: 0.9rem; margin: 0.3rem 0; padding-left: 1.2rem; }
    .last-attention { margin-top: 1.8rem; }
    .last-attention h3 { font-size: 1rem; margin-bottom: 0.2rem; }
    .timeline { display: flex; align-items: flex-end; gap: 2px; height: 34px; padding: 4px 0 8px; overflow-x: auto; }
    .tl-seg { height: 100%; border-radius: 2px; flex-shrink: 0; }
    .tl-seg.tl-pause { border-top: 4px solid #c0392b; }
    .session-meta { font-size: 0.8rem; color: #555; margin: 0.9rem 0 0.1rem; }
    .badge-warn { color: #a33; font-weight: 600; }
    .legend-list { list-style: none; padding: 0; margin: 0.4rem 0 0; font-size: 0.82rem; color: #444; }
    .legend-list li { display: flex; align-items: center; gap: 0.5rem; padding: 0.15rem 0; }
    .legend-swatch { width: 14px; height: 14px; border-radius: 3px; flex-shrink: 0; }
</style>
</head>
<body>
    <h1>Ingreso correcto</h1>
    <p>Abre LabSim en tu computador y escribe este código para continuar:</p>
    <p class="code" id="code"><?= htmlspecialchars($code) ?></p>
    <p>Vence en <span id="countdown" class="countdown"><?= $expiresIn ?></span> segundos.</p>
    <button id="refresh" type="button">Generar código nuevo</button>
    <?php if ($isPortalUser): ?>
        <a href="<?= htmlspecialchars($portalUrl) ?>" target="_blank" rel="noopener"><button type="button">Ir a plataforma</button></a>
        <?php if ($needsLtiLink): ?>
            <p class="status">Este curso de Moodle aún no está vinculado a un curso de LabSim -- en la plataforma te pediremos vincularlo (una sola vez).</p>
        <?php endif; ?>
    <?php endif; ?>
    <p class="status" id="status"></p>

    <div class="stats">
        <?php if ($isPortalUser): ?>
            <h2>Actividad de los alumnos</h2>
            <?php if ($totalStudents === 0): ?>
                <p class="stats-empty">Todavía no hay alumnos registrados.</p>
            <?php else: ?>
                <p class="stats-summary">
                    <?= $activeStudents ?>/<?= $totalStudents ?> alumnos con al menos un paciente atendido
                    <?php if ($activeStudents > 0): ?>
                        · promedio <?= $avgAttentions ?> pacientes por alumno activo
                    <?php endif; ?>
                </p>
                <p class="stats-summary">
                    <?= $recentAttentions ?> atenciones en los últimos 7 días
                    <?php if ($priorAttentions > 0): ?>
                        (<?= $recentAttentions >= $priorAttentions ? '+' : '' ?><?= $recentAttentions - $priorAttentions ?> vs los 7 anteriores)
                    <?php elseif ($recentAttentions === 0): ?>
                        · sin actividad esta semana
                    <?php endif; ?>
                </p>
                <?php if ($noActivity): ?>
                    <p class="stats-caption">Alumnos sin ningún paciente atendido todavía:</p>
                    <ul class="no-activity-list">
                        <?php foreach (array_slice($noActivity, 0, 15) as $name): ?>
                            <li><?= htmlspecialchars($name) ?></li>
                        <?php endforeach; ?>
                    </ul>
                    <?php if (count($noActivity) > 15): ?>
                        <p class="stats-caption">+<?= count($noActivity) - 15 ?> más</p>
                    <?php endif; ?>
                <?php else: ?>
                    <p class="stats-empty">Todos los alumnos han atendido al menos un paciente.</p>
                <?php endif; ?>
            <?php endif; ?>
        <?php elseif ($myAttentions > 0): ?>
            <h2>Tu actividad</h2>
            <p class="stats-summary">
                <?= $myAttentions ?> paciente<?= $myAttentions === 1 ? '' : 's' ?> atendido<?= $myAttentions === 1 ? '' : 's' ?> · <?= round($mySummary['total_duration_s'] / 60, 1) ?> min en total
                <?php if ($mySummary['avg_delta_s'] !== null): ?>
                    · <?= $mySummary['avg_delta_s'] ?>s promedio entre acciones
                <?php endif; ?>
            </p>
            <p class="stats-caption">Pacientes atendidos por semana</p>
            <div class="chart-wrap"><canvas id="statsChart"></canvas></div>

            <?php if ($lastAttentionKey !== null): ?>
            <div class="last-attention">
                <h3>Tu última atención</h3>
                <p class="stats-summary">
                    <?php if ($lastAttentionAppt): ?>
                        <?= htmlspecialchars(trim($lastAttentionAppt['nombre'] . ' ' . $lastAttentionAppt['apellido'])) ?: 'Paciente' ?>
                        · <?= htmlspecialchars($lastAttentionAppt['procedimiento'] ?: '—') ?>
                    <?php else: ?>
                        Caso <?= htmlspecialchars((string) ($lastAttentionKey['case_id'] ?? '—')) ?>
                    <?php endif; ?>
                </p>
                <p class="stats-summary">
                    delta promedio: <?= $lastAttentionStats['avg_delta_s'] ?? '—' ?>s
                    &nbsp;·&nbsp; <span class="<?= $lastAttentionStats['long_pauses'] > 0 ? 'badge-warn' : '' ?>">pausas largas: <?= $lastAttentionStats['long_pauses'] ?></span>
                    &nbsp;·&nbsp; sin pausa (0s): <?= $lastAttentionStats['no_pause_actions'] ?>
                </p>
                <p class="stats-caption">Cada barra es una acción; ancho = demora desde la anterior. Borde rojo arriba = pausa ≥30s.</p>
                <?php foreach ($lastAttentionSessions as $s): ?>
                <?php render_attention_timeline($s); ?>
                <?php endforeach; ?>
                <?php if ($lastAttentionLegend): ?>
                <ul class="legend-list">
                    <?php foreach ($lastAttentionLegend as $action => $label): ?>
                    <li><span class="legend-swatch" style="background:hsl(<?= launch_action_hue($action) ?>,60%,55%);"></span><?= htmlspecialchars($label) ?></li>
                    <?php endforeach; ?>
                </ul>
                <?php endif; ?>
            </div>
            <?php endif; ?>
        <?php endif; ?>
    </div>

    <?php if (!$isPortalUser && $myAttentions > 0): ?>
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4"></script>
    <?php endif; ?>
    <script>
    <?php if (!$isPortalUser && $myAttentions > 0): ?>
    (function () {
        var statsCanvas = document.getElementById('statsChart');
        if (statsCanvas && window.Chart) {
            new Chart(statsCanvas, {
                type: 'bar',
                data: {
                    labels: <?= json_encode(array_keys($myWeeks)) ?>,
                    datasets: [{
                        label: 'Pacientes atendidos',
                        data: <?= json_encode(array_values($myWeeks)) ?>,
                        backgroundColor: '#4a7dbd'
                    }]
                },
                options: {
                    plugins: { legend: { display: false } },
                    scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
                }
            });
        }
    })();
    <?php endif; ?>
    (function () {
        var KEY = <?= json_encode($refreshKey) ?>;
        var remaining = <?= $expiresIn ?>;
        var codeEl = document.getElementById('code');
        var countdownEl = document.getElementById('countdown');
        var statusEl = document.getElementById('status');
        var btn = document.getElementById('refresh');
        var busy = false;

        function renew() {
            if (busy) { return; }
            busy = true;
            statusEl.textContent = 'Generando código nuevo...';
            fetch('refresh_code.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: KEY })
            }).then(function (r) {
                if (!r.ok) { return r.json().then(function (d) { throw new Error(d.error || ('http ' + r.status)); }); }
                return r.json();
            }).then(function (data) {
                codeEl.textContent = data.code;
                remaining = data.expires_in;
                countdownEl.textContent = remaining;
                countdownEl.className = 'countdown';
                statusEl.textContent = '';
            }).catch(function (err) {
                statusEl.textContent = err.message || 'No se pudo generar un código nuevo. Vuelve a abrir la actividad desde la plataforma.';
            }).finally(function () {
                busy = false;
            });
        }

        setInterval(function () {
            remaining -= 1;
            if (remaining <= 0) {
                countdownEl.textContent = '0';
                renew();
                return;
            }
            countdownEl.textContent = remaining;
            countdownEl.className = remaining <= 30 ? 'countdown low' : 'countdown';
        }, 1000);

        btn.addEventListener('click', renew);
    })();
    </script>
</body>
</html>
