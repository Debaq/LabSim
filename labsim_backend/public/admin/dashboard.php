<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Metrics.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/AdminAudit.php';

$me = Auth::requireAdminSession();
$pdo = Db::get();

// Docente: acotado al roster de su(s) curso(s) -- admin completo sigue sin
// filtro. null = sin filtro (admin completo); array (posiblemente vacío) =
// los únicos user_id que un docente puede ver.
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$allowedStudentIds = $isFullAdmin ? null : Courses::rosterUserIds(Courses::teacherCourseIds((int) $me['id']));

if ($allowedStudentIds === null) {
    $rows = $pdo->query('SELECT id, user_id, client_ts, action, payload FROM action_logs ORDER BY id')->fetchAll();
} elseif ($allowedStudentIds) {
    $placeholders = implode(',', array_fill(0, count($allowedStudentIds), '?'));
    $stmt = $pdo->prepare("SELECT id, user_id, client_ts, action, payload FROM action_logs WHERE user_id IN ({$placeholders}) ORDER BY id");
    $stmt->execute($allowedStudentIds);
    $rows = $stmt->fetchAll();
} else {
    $rows = [];
}
$logs = Metrics::decodeLogs($rows);

// Excluye admins/docentes (role='admin') del dashboard: sus acciones de
// prueba en la app no deben aparecer como "resultados de alumno".
$adminIds = array_map(
    'intval',
    array_column($pdo->query("SELECT id FROM users WHERE role = 'admin'")->fetchAll(), 'id')
);
$logs = array_values(array_filter(
    $logs,
    static fn(array $l): bool => !in_array((int) $l['user_id'], $adminIds, true)
));

// Sin filtro adicional de role aquí: los action_logs/attendances de un
// alumno quedan asociados a su user_id para siempre; si después se cambia
// de alumno a docente, ya quedó excluido arriba, pero si vuelve a ser
// alumno su historial no se pierde (y su link a student.php sigue sirviendo
// porque este query no filtra por role='student').
$students = $pdo->query('SELECT id, display_name, username FROM users')->fetchAll();
if ($allowedStudentIds !== null) {
    $students = array_values(array_filter(
        $students,
        static fn(array $s): bool => in_array((int) $s['id'], $allowedStudentIds, true)
    ));
}
$studentsById = [];
foreach ($students as $s) {
    $studentsById[(int) $s['id']] = $s;
}

$appointments = $pdo->query('SELECT id, nombre, apellido, procedimiento, case_id FROM appointments')->fetchAll();
$apptById = [];
foreach ($appointments as $a) {
    $apptById[(int) $a['id']] = $a;
}

function fmt_appt_paciente(?array $appt): string
{
    if (!$appt) {
        return '—';
    }
    $nombre = trim(($appt['nombre'] ?? '') . ' ' . ($appt['apellido'] ?? ''));
    return $nombre !== '' ? $nombre : '—';
}

function fmt_duration_hms(int $totalSeconds): string
{
    return Metrics::formatDurationHms($totalSeconds);
}

// hue estable por tipo de acción -- así "audio_intensity_change" siempre
// pinta el mismo color en cualquier sesión/alumno, se puede reconocer el
// patrón a simple vista en vez de leer cada etiqueta.
function action_hue(string $action): int
{
    return crc32($action) % 360;
}

function render_timeline(array $session): void
{
    ?>
    <div class="session-meta">
        <?= htmlspecialchars((string) $session['start']) ?> &rarr; <?= htmlspecialchars((string) $session['end']) ?>
        &nbsp;·&nbsp; <?= $session['n_actions'] ?> acciones &nbsp;·&nbsp; <?= htmlspecialchars(fmt_duration_hms((int) $session['duration_s'])) ?>
        <?= $session['con_paciente'] ? '' : ' &nbsp;·&nbsp; <strong>sin paciente (modo libre)</strong>' ?>
    </div>
    <div class="timeline">
        <?php foreach ($session['actions'] as $a):
            $delta = $a['delta_s'];
            $w = $delta === null ? 6 : (int) min(max($delta, 0) * 5, 200);
            $w = max($w, 6);
            $hue = action_hue((string) $a['action']);
            $isPause = $delta !== null && $delta >= 30;
            $title = Metrics::actionLabel((string) $a['action']) . ' · ' . ($delta === null ? 'inicio de sesión' : $delta . 's desde la acción anterior');
        ?>
        <div class="tl-seg<?= $isPause ? ' tl-pause' : '' ?>"
             style="width:<?= $w ?>px; background:hsl(<?= $hue ?>,60%,55%);"
             title="<?= htmlspecialchars($title) ?>"></div>
        <?php endforeach; ?>
    </div>
    <details>
        <summary>Ver detalle en tabla</summary>
        <table>
            <tr><th>Hora</th><th>Acción</th><th>Pausa antes</th></tr>
            <?php foreach ($session['actions'] as $a): ?>
            <tr>
                <td><?= htmlspecialchars((string) $a['ts']) ?></td>
                <td><?= htmlspecialchars(Metrics::actionLabel((string) $a['action'])) ?></td>
                <td><?= $a['delta_s'] === null ? '—' : $a['delta_s'] . 's' ?></td>
            </tr>
            <?php endforeach; ?>
        </table>
    </details>
    <?php
}

$dashboardStyle = <<<CSS
    .timeline { display: flex; align-items: flex-end; gap: 2px; height: 34px; padding: 4px 0 8px; overflow-x: auto; }
    .tl-seg { height: 100%; border-radius: 2px; flex-shrink: 0; }
    .tl-seg.tl-pause { border-top: 4px solid #c0392b; }
    .session-meta { font-size: 0.8rem; color: #555; margin: 0.9rem 0 0.1rem; }
    .legend { font-size: 0.78rem; color: #777; margin-top: 0.4rem; }
    details summary { cursor: pointer; font-size: 0.82rem; color: #555; margin-top: 0.3rem; }
    .badge-warn { color: #a33; font-weight: 600; }
    .card:target { outline: 2px solid #1a2744; }
    .hist-bar { display: flex; width: 100%; min-width: 8rem; height: 14px; border-radius: 3px; overflow: hidden; background: #eee; }
    .hist-bar span { height: 100%; display: block; }
    .card-reference { border: 2px solid #2e7d32; }
    .badge-ref { background: #2e7d32; color: #fff; font-size: 0.7rem; padding: 0.1rem 0.4rem; border-radius: 3px; margin-left: 0.4rem; }
    .dash-grid { display: grid; grid-template-columns: minmax(260px, 420px) 1fr; gap: 1.2rem; align-items: start; }
    .dash-grid .card { margin-bottom: 0; }
    .student-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(440px, 1fr)); gap: 1.2rem; align-items: start; }
    .student-grid .card { margin-bottom: 0; }
    @media (max-width: 900px) {
        .dash-grid { grid-template-columns: 1fr; }
    }
CSS;

$appointmentId = isset($_GET['appointment_id']) && $_GET['appointment_id'] !== ''
    ? (int) $_GET['appointment_id']
    : null;
$focusStudentId = isset($_GET['student_id']) && $_GET['student_id'] !== ''
    ? (int) $_GET['student_id']
    : null;

if ($appointmentId !== null) {
    $appt = $apptById[$appointmentId] ?? null;

    // Referencia profesional: sin migrar schema, se guarda en app_config
    // (k/v JSON libre que ya existe) bajo una clave por caso -- así toda
    // cita futura del mismo caso hereda la misma referencia.
    $referenceKey = $appt && $appt['case_id'] ? 'reference_appointment:' . $appt['case_id'] : null;

    // Estado actual por alumno para esta cita -- distinto de "reagendar"
    // (agenda.php crea una ronda/cita nueva y conserva el historial): acá se
    // reabre la MISMA atención in-place, para cuando el alumno cerró pero le
    // faltó algo o se equivocó, sin generar una entrada nueva de historial.
    $attByStudent = [];
    $attStmt = $pdo->prepare('SELECT student_id, estado FROM attendances WHERE appointment_id = ?');
    $attStmt->execute([$appointmentId]);
    foreach ($attStmt->fetchAll() as $a) {
        $attByStudent[(int) $a['student_id']] = $a['estado'];
    }

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        Auth::requireCsrf();
        $postAction = (string) ($_POST['form_action'] ?? '');

        if ($postAction === 'reactivate_attendance') {
            $reactUserId = (int) ($_POST['user_id'] ?? 0);
            if ($reactUserId > 0) {
                $pdo->prepare(
                    "UPDATE attendances SET estado = 'atendiendo', updated_at = CURRENT_TIMESTAMP
                     WHERE appointment_id = ? AND student_id = ? AND estado IN ('atendido', 'no_show')"
                )->execute([$appointmentId, $reactUserId]);
                $attByStudent[$reactUserId] = 'atendiendo';
                AdminAudit::log($me, 'attendance_reactivate', ['appointment_id' => $appointmentId, 'student_id' => $reactUserId]);
            }
            header('Location: dashboard.php?appointment_id=' . $appointmentId . '#student-' . $reactUserId);
            exit;
        }

        if ($postAction === 'delete_attendance') {
            // Borra el resultado (atención) de un alumno puntual para esta
            // cita -- útil para limpiar intentos de prueba/duplicados cuando
            // decenas de alumnos atendieron al mismo paciente. Los action_logs
            // no tienen columna appointment_id propia (va dentro del payload,
            // ver Metrics::decodeLog), así que hay que filtrarlos a mano.
            $delUserId = (int) ($_POST['user_id'] ?? 0);
            if ($delUserId > 0) {
                $pdo->prepare('DELETE FROM attendances WHERE appointment_id = ? AND student_id = ?')
                    ->execute([$appointmentId, $delUserId]);

                $logStmt = $pdo->prepare('SELECT id, payload FROM action_logs WHERE user_id = ?');
                $logStmt->execute([$delUserId]);
                $idsToDelete = [];
                foreach ($logStmt->fetchAll() as $row) {
                    $payload = $row['payload'] ? json_decode((string) $row['payload'], true) : null;
                    if (is_array($payload) && (int) ($payload['appointment_id'] ?? 0) === $appointmentId) {
                        $idsToDelete[] = (int) $row['id'];
                    }
                }
                if ($idsToDelete) {
                    $placeholders = implode(',', array_fill(0, count($idsToDelete), '?'));
                    $pdo->prepare("DELETE FROM action_logs WHERE id IN ({$placeholders})")->execute($idsToDelete);
                }
                AdminAudit::log($me, 'attendance_delete', ['appointment_id' => $appointmentId, 'student_id' => $delUserId, 'logs_deleted' => count($idsToDelete)]);
            }
            header('Location: dashboard.php?appointment_id=' . $appointmentId);
            exit;
        } elseif ($referenceKey !== null && (int) $me['permission'] === Auth::PERMISSION_ADMIN) {
            if ($postAction === 'mark_reference') {
                $refUserId = (int) ($_POST['user_id'] ?? 0);
                $pdo->prepare(
                    "INSERT INTO app_config (k, v) VALUES (?, ?)
                     ON CONFLICT(k) DO UPDATE SET v = excluded.v, updated_at = CURRENT_TIMESTAMP"
                )->execute([$referenceKey, json_encode(['appointment_id' => $appointmentId, 'user_id' => $refUserId])]);
                AdminAudit::log($me, 'reference_mark', ['appointment_id' => $appointmentId, 'student_id' => $refUserId]);
            } elseif ($postAction === 'unmark_reference') {
                $pdo->prepare('DELETE FROM app_config WHERE k = ?')->execute([$referenceKey]);
                AdminAudit::log($me, 'reference_unmark', ['appointment_id' => $appointmentId]);
            }
        }
    }

    $referenceUserId = null;
    if ($referenceKey !== null) {
        $stmt = $pdo->prepare('SELECT v FROM app_config WHERE k = ?');
        $stmt->execute([$referenceKey]);
        $refRaw = $stmt->fetchColumn();
        if ($refRaw) {
            $refData = json_decode((string) $refRaw, true);
            if (is_array($refData) && (int) ($refData['appointment_id'] ?? 0) === $appointmentId) {
                $referenceUserId = (int) ($refData['user_id'] ?? 0);
            }
        }
    }

    $apptLogs = array_values(array_filter($logs, static fn(array $l): bool => (int) ($l['appointment_id'] ?? -1) === $appointmentId));
    $byStudent = [];
    foreach ($apptLogs as $l) {
        $byStudent[(int) $l['user_id']][] = $l;
    }

    // La referencia siempre va primera; ?compare= (elegido a mano) pasa por
    // encima de eso si el docente quiere comparar a alguien más contra ella.
    if ($referenceUserId !== null && isset($byStudent[$referenceUserId])) {
        $byStudent = [$referenceUserId => $byStudent[$referenceUserId]] + $byStudent;
    }
    $compareUserId = isset($_GET['compare']) && $_GET['compare'] !== '' ? (int) $_GET['compare'] : null;
    if ($compareUserId !== null && isset($byStudent[$compareUserId])) {
        $byStudent = [$compareUserId => $byStudent[$compareUserId]] + $byStudent;
    }

    admin_header('Dashboard · Cita #' . $appointmentId, $me);
    ?>
    <style><?= $dashboardStyle ?></style>
    <div class="card">
        <p><a href="dashboard.php">&larr; Volver al dashboard</a></p>
        <p>
            <strong>Paciente:</strong> <?= htmlspecialchars(fmt_appt_paciente($appt)) ?>
            &nbsp;·&nbsp; <strong>Procedimiento:</strong> <?= htmlspecialchars($appt['procedimiento'] ?? '—') ?>
            &nbsp;·&nbsp; <strong>Caso:</strong> <?= htmlspecialchars((string) ($appt['case_id'] ?? '—')) ?>
        </p>
        <p class="legend">Cada barra = una acción. Ancho = cuánto se demoró en hacerla desde la anterior (tope visual 40s). Borde rojo arriba = pausa ≥30s. Color = tipo de acción (mismo color siempre).</p>
    </div>

    <?php if (!$byStudent): ?>
    <div class="card" style="color:#888;">Sin acciones registradas para esta cita todavía.</div>
    <?php endif; ?>

    <?php if ($focusStudentId !== null && !isset($byStudent[$focusStudentId])):
        $focusStudent = $studentsById[$focusStudentId] ?? null;
    ?>
    <div class="card" id="student-<?= $focusStudentId ?>" style="border:1px solid #e0b34d;">
        <strong><?= htmlspecialchars($focusStudent['display_name'] ?? ('Alumno #' . $focusStudentId)) ?></strong>
        &nbsp;·&nbsp; sin logs registrados para esta cita.
        <p class="legend">Puede ser una atención de antes de que el cliente empezara a mandar <code>appointment_id</code> en cada acción -- revisa la tabla "Acciones por tipo" en el perfil del alumno para ver si igual hay actividad sin cita asociada.</p>
    </div>
    <?php endif; ?>

    <div class="student-grid">
    <?php foreach ($byStudent as $uid => $slogs):
        $sessions = Metrics::buildSessions($slogs);
        $stats = Metrics::summarizeSessions($sessions);
        $student = $studentsById[$uid] ?? null;
        $isReference = $uid === $referenceUserId;
    ?>
    <div class="card<?= $isReference ? ' card-reference' : '' ?>" id="student-<?= $uid ?>">
        <strong>
            <?php if ($student): ?>
            <a href="student.php?id=<?= $uid ?>"><?= htmlspecialchars($student['display_name']) ?></a>
            <?php else: ?>
            Alumno #<?= $uid ?>
            <?php endif; ?>
        </strong>
        <?php if ($isReference): ?><span class="badge-ref">Referencia</span><?php endif; ?>
        <?php $curEstado = $attByStudent[$uid] ?? null; ?>
        <?php if ($curEstado !== null): ?>
        &nbsp;·&nbsp; estado: <strong><?= htmlspecialchars($curEstado) ?></strong>
        <?php endif; ?>
        &nbsp;·&nbsp; delta promedio: <?= $stats['avg_delta_s'] ?? '—' ?>s
        &nbsp;·&nbsp; <span class="<?= $stats['long_pauses'] > 0 ? 'badge-warn' : '' ?>">pausas largas: <?= $stats['long_pauses'] ?></span>
        &nbsp;·&nbsp; acciones sin pausa (0s): <?= $stats['no_pause_actions'] ?>
        <?php if (!$isReference): ?>
        <a href="?appointment_id=<?= $appointmentId ?>&compare=<?= $uid ?>" style="font-size:0.78rem; margin-left:0.6rem;">Comparar primero</a>
        <?php endif; ?>
        <?php if ($referenceKey !== null && (int) $me['permission'] === Auth::PERMISSION_ADMIN): ?>
        <form method="post" class="inline" style="margin-left:0.6rem;">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="<?= $isReference ? 'unmark_reference' : 'mark_reference' ?>">
            <input type="hidden" name="user_id" value="<?= $uid ?>">
            <button type="submit" class="secondary" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;"><?= $isReference ? 'Quitar referencia' : 'Marcar como referencia' ?></button>
        </form>
        <?php endif; ?>
        <?php if (in_array($curEstado, ['atendido', 'no_show'], true)): ?>
        <form method="post" class="inline" style="margin-left:0.6rem;" onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Reactivar la atención de ' . ($student['display_name'] ?? ('Alumno #' . $uid)) . '? Vuelve a quedar "atendiendo" para que el alumno la retome, sin crear una cita/ronda nueva.'), ENT_QUOTES) ?>);">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="reactivate_attendance">
            <input type="hidden" name="user_id" value="<?= $uid ?>">
            <button type="submit" class="secondary" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Reactivar atención</button>
        </form>
        <?php endif; ?>
        <form method="post" class="inline" style="margin-left:0.6rem;" onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Eliminar el resultado de ' . ($student['display_name'] ?? ('Alumno #' . $uid)) . ' para esta cita? Se borran su atención y sus acciones registradas para esta cita. No se puede deshacer.'), ENT_QUOTES) ?>);">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="delete_attendance">
            <input type="hidden" name="user_id" value="<?= $uid ?>">
            <button type="submit" class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Eliminar resultado</button>
        </form>

        <?php foreach ($sessions as $s): ?>
        <?php render_timeline($s); ?>
        <?php endforeach; ?>
    </div>
    <?php endforeach; ?>
    </div>
    <?php
    admin_footer();
    exit;
}

$byUserLogs = [];
foreach ($logs as $l) {
    $byUserLogs[(int) $l['user_id']][] = $l;
}

// Duración total por alumno: mismo criterio real por atención que usa
// student.php (hora_real->updated_at si está cerrada, si no reloj real de
// bloques) -- summarizeSessions()['total_duration_s'] no sirve acá porque
// solo suma bloques activos y esconde pausas largas (ver Metrics::wallClockDurationSeconds).
if ($allowedStudentIds === null) {
    $attRows = $pdo->query('SELECT student_id, appointment_id, estado, hora_real, updated_at FROM attendances')->fetchAll();
} elseif ($allowedStudentIds) {
    $placeholders = implode(',', array_fill(0, count($allowedStudentIds), '?'));
    $attStmt2 = $pdo->prepare("SELECT student_id, appointment_id, estado, hora_real, updated_at FROM attendances WHERE student_id IN ({$placeholders})");
    $attStmt2->execute($allowedStudentIds);
    $attRows = $attStmt2->fetchAll();
} else {
    $attRows = [];
}
$attByUser = [];
foreach ($attRows as $a) {
    $attByUser[(int) $a['student_id']][] = $a;
}

$studentStats = [];
$studentHist = [];
$studentDurationRealS = [];
$apptAgg = [];
foreach ($byUserLogs as $uid => $ulogs) {
    $sessions = Metrics::buildSessions($ulogs);
    $studentStats[$uid] = Metrics::summarizeSessions($sessions);
    $studentHist[$uid] = Metrics::deltaHistogram($sessions);

    $byAppt = [];
    foreach ($ulogs as $l) {
        if ($l['appointment_id'] === null || $l['appointment_id'] === '') {
            continue;
        }
        $byAppt[(int) $l['appointment_id']][] = $l;
    }
    foreach ($byAppt as $aid => $alogs) {
        $apptAgg[$aid]['students'][$uid] = true;
        $apptAgg[$aid]['sessions'] = ($apptAgg[$aid]['sessions'] ?? 0) + count(Metrics::buildSessions($alogs));
    }

    $userSessionsByAppt = [];
    foreach (Metrics::buildSessions($ulogs) as $s) {
        $key = $s['appointment_id'] !== null ? (int) $s['appointment_id'] : 0;
        $userSessionsByAppt[$key][] = $s;
    }
    $durationRealS = 0;
    foreach ($attByUser[$uid] ?? [] as $att) {
        $group = $userSessionsByAppt[(int) $att['appointment_id']] ?? null;
        $realDuration = $att['estado'] === 'atendido'
            ? Metrics::attendanceDurationSeconds($att['hora_real'], $att['updated_at'])
            : null;
        $durationRealS += $realDuration ?? ($group ? Metrics::wallClockDurationSeconds($group) : 0);
    }
    $studentDurationRealS[$uid] = $durationRealS;
}
uasort($studentStats, static fn(array $a, array $b): int => (string) ($b['last_activity'] ?? '') <=> (string) ($a['last_activity'] ?? ''));
uasort($apptAgg, static fn(array $a, array $b): int => $b['sessions'] <=> $a['sessions']);

$totalConPaciente = 0;
$totalSinPaciente = 0;
foreach ($logs as $l) {
    if ($l['con_paciente']) {
        $totalConPaciente++;
    } else {
        $totalSinPaciente++;
    }
}

admin_header('Dashboard de actividad', $me);
?>
<style><?= $dashboardStyle ?></style>
<div class="dash-grid" style="margin-bottom: 1.2rem;">
<div class="card">
    <strong>Resumen global</strong>
    <table>
        <tr><td>Acciones con paciente</td><td><strong><?= $totalConPaciente ?></strong></td></tr>
        <tr><td>Acciones sin paciente (modo libre)</td><td><strong><?= $totalSinPaciente ?></strong></td></tr>
        <tr><td>Alumnos con actividad registrada</td><td><strong><?= count($studentStats) ?></strong></td></tr>
        <tr><td>Citas con actividad registrada</td><td><strong><?= count($apptAgg) ?></strong></td></tr>
    </table>
</div>

<div class="card">
    <strong>Por paciente / cita</strong>
    <table>
        <tr><th>Cita</th><th>Paciente</th><th>Procedimiento</th><th>Alumnos</th><th>Bloques totales</th></tr>
        <?php foreach ($apptAgg as $aid => $agg):
            $appt = $apptById[$aid] ?? null;
        ?>
        <tr>
            <td><a href="dashboard.php?appointment_id=<?= $aid ?>">#<?= $aid ?></a></td>
            <td><?= htmlspecialchars(fmt_appt_paciente($appt)) ?></td>
            <td><?= htmlspecialchars($appt['procedimiento'] ?? '—') ?></td>
            <td><?= count($agg['students']) ?></td>
            <td><?= $agg['sessions'] ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$apptAgg): ?>
        <tr><td colspan="5" style="color:#888;">Sin actividad registrada todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>
</div>

<div class="card">
    <strong>Por alumno</strong>
    <p class="legend">No es cantidad de logs -- es cómo se comporta: delta promedio entre acciones, cuántas pausas largas (posible duda) y cuántas acciones dispara sin pausa (posible clickeo sin pensar). La barra de distribución va de verde (sin pausa) a rojo (pausa ≥30s).
        <strong>Ojo:</strong> esto suma <strong>todas</strong> las atenciones del alumno (todos los pacientes juntos) -- si revisó más de un caso, pincha su nombre para ver el desglose por atención en su ficha, o usa la tabla "Por paciente / cita" de abajo para entrar directo a una cita puntual.</p>
    <table>
        <tr><th>Alumno</th><th>Última actividad</th><th>Sesiones</th><th>Atenciones</th><th>Bloques</th><th>Duración total</th><th>Delta promedio</th><th>Pausas largas (≥30s)</th><th>Sin pausa (0s)</th><th>Distribución de pausas</th></tr>
        <?php foreach ($studentStats as $uid => $st):
            $student = $studentsById[$uid] ?? null;
            $hist = $studentHist[$uid] ?? [];
            $histTotal = array_sum($hist) ?: 1;
        ?>
        <tr>
            <td><a href="student.php?id=<?= $uid ?>"><?= htmlspecialchars($student['display_name'] ?? ('Alumno #' . $uid)) ?></a></td>
            <td><?= htmlspecialchars((string) ($st['last_activity'] ?? '—')) ?></td>
            <td><?= Metrics::countLoginSessions($byUserLogs[$uid]) ?></td>
            <td><?= Metrics::countAttentions($byUserLogs[$uid]) ?></td>
            <td><?= $st['n_sessions'] ?></td>
            <td><?= htmlspecialchars(fmt_duration_hms($studentDurationRealS[$uid] ?? 0)) ?></td>
            <td><?= $st['avg_delta_s'] ?? '—' ?>s</td>
            <td<?= $st['long_pauses'] > 0 ? ' class="badge-warn"' : '' ?>><?= $st['long_pauses'] ?></td>
            <td><?= $st['no_pause_actions'] ?></td>
            <td>
                <div class="hist-bar" title="0s: <?= $hist['0s'] ?? 0 ?> · 1-5s: <?= $hist['1-5s'] ?? 0 ?> · 6-15s: <?= $hist['6-15s'] ?? 0 ?> · 16-30s: <?= $hist['16-30s'] ?? 0 ?> · 30s+: <?= $hist['30s+'] ?? 0 ?>">
                    <?php foreach (['0s' => '#2e7d32', '1-5s' => '#9ccc65', '6-15s' => '#ffb300', '16-30s' => '#fb8c00', '30s+' => '#c0392b'] as $bucket => $color):
                        $pct = round((($hist[$bucket] ?? 0) / $histTotal) * 100, 1);
                        if ($pct <= 0) { continue; }
                    ?>
                    <span style="width:<?= $pct ?>%; background:<?= $color ?>;"></span>
                    <?php endforeach; ?>
                </div>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$studentStats): ?>
        <tr><td colspan="10" style="color:#888;">Sin actividad registrada todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>
<?php
admin_footer();
