<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Metrics.php';

/**
 * Detalle de una atención propia ya cerrada: stats de comportamiento, ficha
 * clínica (historia_clinica + tu propio historial con ese paciente) y la
 * conversación con el paciente simulado, con la retroalimentación que tu
 * docente haya dejado turno a turno (chat_comments) -- todo solo lectura,
 * scopeado a la sesión de alumno (ver sso.php), nunca a otro appointment_id
 * o student_id que no sea el propio.
 */

// Llaves {{N}} dentro de historia_clinica (N = offset en días respecto a la
// fecha de la cita) -- mismo criterio que agenda.Agenda/core.ficha en la app.
function resolver_fechas_historia_clinica(string $texto, ?string $fechaCitaStr): string
{
    if ($texto === '' || !$fechaCitaStr) {
        return $texto;
    }
    $fechaCita = DateTime::createFromFormat('d-m-y', $fechaCitaStr);
    if (!$fechaCita) {
        return $texto;
    }
    return preg_replace_callback('/\{\{([+-]?\d+)\}\}/', static function (array $m) use ($fechaCita) {
        $fecha = clone $fechaCita;
        $fecha->modify(((int) $m[1] >= 0 ? '+' : '') . (int) $m[1] . ' days');
        return $fecha->format('d-m-Y');
    }, $texto);
}

$me = Auth::requireStudentSession();
$pdo = Db::get();

$appointmentId = (int) ($_GET['appointment_id'] ?? 0);

$stmt = $pdo->prepare('SELECT nota, hora_real, updated_at FROM attendances WHERE appointment_id = ? AND student_id = ? AND estado = ?');
$stmt->execute([$appointmentId, $me['id'], 'atendido']);
$attendance = $stmt->fetch();

$stmt = $pdo->prepare(
    'SELECT id, fecha, hora, rut, nombre, apellido, fecha_nac, procedimiento, patient_id
     FROM appointments WHERE id = ?'
);
$stmt->execute([$appointmentId]);
$appointment = $stmt->fetch();

if (!$attendance || !$appointment) {
    student_header('Atención', $me);
    echo '<p class="error">No encontramos esa atención.</p><p><a class="back" href="mis_pacientes.php">&larr; Volver</a></p>';
    student_footer();
    exit;
}

$stmt = $pdo->prepare('SELECT user_id, client_ts, action, payload FROM action_logs WHERE user_id = ? ORDER BY id');
$stmt->execute([$me['id']]);
$sessions = array_values(array_filter(
    Metrics::buildSessions(Metrics::decodeLogs($stmt->fetchAll())),
    static fn (array $s) => $s['appointment_id'] !== null && (int) $s['appointment_id'] === $appointmentId
));
$stats = Metrics::summarizeSessions($sessions);

$historiaClinica = '';
if ($appointment['patient_id']) {
    $stmt = $pdo->prepare('SELECT historia_clinica FROM patients WHERE id = ?');
    $stmt->execute([(int) $appointment['patient_id']]);
    $historiaClinica = (string) ($stmt->fetchColumn() ?: '');
}

$historial = [];
if ($appointment['patient_id']) {
    $stmt = $pdo->prepare(
        "SELECT att2.nota, att2.hora_real, a2.fecha
         FROM attendances att2 JOIN appointments a2 ON a2.id = att2.appointment_id
         WHERE att2.student_id = ? AND att2.estado = 'atendido' AND a2.patient_id = ?
         ORDER BY a2.fecha, a2.hora"
    );
    $stmt->execute([$me['id'], (int) $appointment['patient_id']]);
    $historial = $stmt->fetchAll();
}

$stmt = $pdo->prepare(
    'SELECT id, role, content, created_at FROM llm_chat_logs
     WHERE appointment_id = ? AND student_id = ? ORDER BY id'
);
$stmt->execute([$appointmentId, $me['id']]);
$log = $stmt->fetchAll();

$comments = [];
if ($log) {
    $logIds = array_column($log, 'id');
    $placeholders = implode(',', array_fill(0, count($logIds), '?'));
    $stmt = $pdo->prepare(
        "SELECT c.chat_log_id, c.comment, c.created_at, u.display_name AS teacher_name
         FROM chat_comments c JOIN users u ON u.id = c.teacher_id
         WHERE c.chat_log_id IN ($placeholders) ORDER BY c.id"
    );
    $stmt->execute($logIds);
    foreach ($stmt->fetchAll() as $c) {
        $comments[(int) $c['chat_log_id']][] = $c;
    }
}

$paciente = trim("{$appointment['nombre']} {$appointment['apellido']}") ?: 'Paciente sin nombre';

student_header($paciente, $me);
?>
<a class="back" href="mis_pacientes.php">&larr; Mis pacientes</a>
<h1><?= htmlspecialchars($paciente) ?></h1>

<div class="card">
    <h2>Datos de la atención</h2>
    <p>
        <b>Procedimiento:</b> <?= htmlspecialchars($appointment['procedimiento'] ?: '—') ?><br>
        <b>Cita:</b> <?= htmlspecialchars($appointment['fecha'] ?: '—') ?> <?= htmlspecialchars($appointment['hora'] ?: '') ?><br>
        <b>Inicio real:</b> <?= htmlspecialchars($attendance['hora_real'] ?: '—') ?><br>
        <b>Cerrada:</b> <?= htmlspecialchars($attendance['updated_at']) ?>
    </p>
</div>

<div class="card">
    <h2>Comportamiento durante la atención</h2>
    <table>
        <tr><td>Bloques de actividad</td><td><b><?= $stats['n_sessions'] ?></b></td></tr>
        <tr><td>Duración total</td><td><b><?= $stats['total_duration_s'] ?>s</b></td></tr>
        <tr><td>Delta promedio entre acciones</td><td><b><?= $stats['avg_delta_s'] ?? '—' ?><?= $stats['avg_delta_s'] !== null ? 's' : '' ?></b></td></tr>
        <tr><td>Pausas largas (&ge;30s)</td><td><b<?= $stats['long_pauses'] > 0 ? ' class="badge-warn"' : '' ?>><?= $stats['long_pauses'] ?></b></td></tr>
        <tr><td>Acciones sin pausa (0s)</td><td><b><?= $stats['no_pause_actions'] ?></b></td></tr>
    </table>
    <?php if ($attendance['nota']): ?>
    <h2 style="margin-top:1rem;">Tu evolución registrada</h2>
    <p><?= nl2br(htmlspecialchars($attendance['nota'])) ?></p>
    <?php endif; ?>
</div>

<div class="card">
    <h2>Ficha clínica</h2>
    <p>
        <b>Rut:</b> <?= htmlspecialchars($appointment['rut'] ?: '—') ?><br>
        <b>Fecha de nacimiento:</b> <?= htmlspecialchars($appointment['fecha_nac'] ?: '—') ?>
    </p>
    <?php if ($historiaClinica): ?>
    <p><b>Historia clínica:</b> <?= nl2br(htmlspecialchars(resolver_fechas_historia_clinica($historiaClinica, $appointment['fecha']))) ?></p>
    <?php endif; ?>
    <p class="legend">Tu historial con este paciente (otras atenciones tuyas que hayas cerrado):</p>
    <?php if (!$historial): ?>
    <p class="empty">Esta es la primera vez que lo atendiste.</p>
    <?php else: ?>
    <ul>
        <?php foreach ($historial as $h): ?>
        <li><b><?= htmlspecialchars($h['fecha'] ?: 'sin fecha') ?> <?= htmlspecialchars($h['hora_real']) ?></b> —
            <?= htmlspecialchars($h['nota'] ?: 'sin comentario') ?></li>
        <?php endforeach; ?>
    </ul>
    <?php endif; ?>
</div>

<div class="card">
    <h2>Conversación con el paciente</h2>
    <p class="legend">Los globos amarillos son retroalimentación de tu docente sobre ese turno puntual -- solo la ve el equipo docente hasta que se comparte contigo acá.</p>
    <?php if (!$log): ?>
    <p class="empty">Sin conversación registrada para esta atención.</p>
    <?php else: ?>
    <div style="display:flex; flex-direction:column; gap:1rem; width:100%; max-width:44rem; margin:0 auto;">
        <?php foreach ($log as $turn):
            $role = $turn['role'] === 'assistant' ? 'assistant' : 'user';
            $turnComments = $comments[(int) $turn['id']] ?? [];
        ?>
        <div>
            <div style="display:flex; justify-content:<?= $role === 'user' ? 'flex-end' : 'flex-start' ?>;">
                <div style="max-width:80%; padding:0.5rem 0.8rem; border-radius:12px; font-size:0.9rem; white-space:pre-wrap;
                    <?= $role === 'user' ? 'background:#3b5bdb; color:#fff;' : 'background:#fff; border:1px solid #e5e5ea;' ?>">
                    <span style="display:block; font-size:0.68rem; opacity:0.75; margin-bottom:0.15rem;">
                        <?= $role === 'assistant' ? 'Paciente' : 'Tú' ?> · <?= htmlspecialchars($turn['created_at']) ?>
                    </span>
                    <?= htmlspecialchars($turn['content']) ?>
                </div>
            </div>
            <?php foreach ($turnComments as $c): ?>
            <div style="display:flex; justify-content:center; margin-top:0.3rem;">
                <div style="max-width:80%; background:#fff9ea; border:1px solid #f3dfa0; border-radius:10px; padding:0.4rem 0.65rem; font-size:0.85rem;">
                    <span style="display:block; font-size:0.68rem; color:#a3822f; font-weight:600; margin-bottom:0.1rem;">
                        <?= htmlspecialchars($c['teacher_name']) ?> (docente) · <?= htmlspecialchars($c['created_at']) ?>
                    </span>
                    <?= nl2br(htmlspecialchars($c['comment'])) ?>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
        <?php endforeach; ?>
    </div>
    <?php endif; ?>
</div>
<?php
student_footer();
