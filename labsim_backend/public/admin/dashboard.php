<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Metrics.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/ReportFile.php';
require_once __DIR__ . '/../../src/AlumnoIndicadores.php';
require_once __DIR__ . '/../../src/AudiometriaTecnica.php';
require_once __DIR__ . '/../../src/AudiometriaTecnicaVista.php';
require_once __DIR__ . '/../../src/CourseAvance.php';
require_once __DIR__ . '/../../src/DashboardDatos.php';

/**
 * Dashboard: la página donde aterriza el docente (ver sso.php). Dos vistas:
 *
 * - General: qué pasó esta semana, quién está atendiendo ahora, las últimas
 *   atenciones, los pacientes y los alumnos, en datos que se entienden
 *   (tiempo, preguntas, técnica, informes). Sale de las atenciones, no del
 *   registro de acciones: antes cargaba action_logs entero (100 mil filas)
 *   en cada visita y hablaba de "bloques", "delta" y "pausas".
 * - Una cita (?appointment_id=): cada alumno que la atendió, con lo mismo
 *   más el uso de cada equipo, y las acciones de gestión (cerrar, reactivar,
 *   eliminar, referencia). Lee solo los registros de esa cita.
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;

// Foco de curso del header (ver admin_course_context()): acota al roster de
// ESE curso. Un docente de dos cursos veía las dos cohortes mezcladas.
$contextCourseId = admin_course_context($me);
$contextCourseName = null;
if ($contextCourseId !== null) {
    $curso = Courses::find($contextCourseId);
    $contextCourseName = $curso ? (string) $curso['name'] : null;
}
$permitidos = DashboardDatos::alumnosVisibles($me, $contextCourseId);

$estados = [
    'atendiendo' => ['atendiendo', 'tag--warn'],
    'atendido' => ['cerrada', 'tag--success'],
    'no_show' => ['no se presentó', 'tag--muted'],
];
$ahora = time();
$haceDe = static fn(string $utc): string => AlumnoIndicadores::hace(max(0, $ahora - (int) strtotime($utc . ' UTC')));
$horaLocal = static fn(string $utc): string => Clock::fromUtc($utc)->format('d-m H:i');
$paciente = static function (array $a): string {
    $n = trim(($a['nombre'] ?? '') . ' ' . ($a['apellido'] ?? ''));
    return $n !== '' ? $n : 'Paciente sin nombre';
};
// En las tablas, el curso por su código ("ETMP176"): el nombre completo de
// un curso en cada fila tapaba lo demás.
$cursoCorto = static function (?string $nombre): string {
    $nombre = trim((string) $nombre);
    if (preg_match('/\b[A-Z]{2,}\d{2,}[\w-]*/u', $nombre, $m)) {
        return $m[0];
    }
    return mb_strimwidth($nombre, 0, 24, '…');
};
$duracion = static function (array $a): ?int {
    if ($a['estado'] !== 'atendido') {
        return null;
    }
    $d = Metrics::attendanceDurationSeconds($a['hora_real'], $a['updated_at']);
    return $d !== null && $d <= CourseAvance::DURACION_MAX_S ? $d : null;
};

$appointmentId = isset($_GET['appointment_id']) && $_GET['appointment_id'] !== '' ? (int) $_GET['appointment_id'] : null;
$focusStudentId = isset($_GET['student_id']) && $_GET['student_id'] !== '' ? (int) $_GET['student_id'] : null;

// ===================================================================== cita
if ($appointmentId !== null) {
    $stmt = $pdo->prepare('SELECT id, fecha, hora, nombre, apellido, procedimiento, case_id, course_id FROM appointments WHERE id = ?');
    $stmt->execute([$appointmentId]);
    $appt = $stmt->fetch() ?: null;
    $stmt->closeCursor();

    // Referencia profesional: en app_config bajo una clave por caso, así toda
    // cita futura del mismo caso hereda la misma referencia.
    $referenceKey = $appt && $appt['case_id'] ? 'reference_appointment:' . $appt['case_id'] : null;

    $atencionesCita = DashboardDatos::atenciones($permitidos, true, $appointmentId);
    $porAlumno = [];
    foreach ($atencionesCita as $a) {
        $porAlumno[(int) $a['student_id']] = $a;
    }

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        Auth::requireCsrf();
        $postAction = (string) ($_POST['form_action'] ?? '');
        $uid = (int) ($_POST['user_id'] ?? 0);
        // Solo sobre alumnos de esta cita que el docente puede ver.
        if ($uid > 0 && !isset($porAlumno[$uid])) {
            header('Location: dashboard.php?appointment_id=' . $appointmentId);
            exit;
        }

        if ($postAction === 'reactivate_attendance' && $uid > 0) {
            // Distinto de "reagendar" (agenda.php crea una ronda nueva): reabre
            // la MISMA atención, para cuando el alumno cerró y le faltó algo.
            $pdo->prepare(
                "UPDATE attendances SET estado = 'atendiendo', updated_at = CURRENT_TIMESTAMP
                 WHERE appointment_id = ? AND student_id = ? AND estado IN ('atendido', 'no_show')"
            )->execute([$appointmentId, $uid]);
            AdminAudit::log($me, 'attendance_reactivate', ['appointment_id' => $appointmentId, 'student_id' => $uid]);
            header('Location: dashboard.php?appointment_id=' . $appointmentId . '#student-' . $uid);
            exit;
        }

        if ($postAction === 'close_attendance' && $uid > 0) {
            // Contraparte de "Reactivar": el alumno no puede cerrar desde la app
            // (no llega su informe, se cayó el equipo) y el docente ve que lo
            // hecho ya está en el servidor. La evolución que escribió vive en
            // su equipo y no llega, así que la nota lo dice.
            $pdo->prepare(
                "UPDATE attendances SET estado = 'atendido',
                    nota = CASE WHEN nota IS NULL OR TRIM(nota) = ''
                                THEN 'Atención cerrada por el docente desde el panel.'
                                ELSE nota END,
                    updated_at = CURRENT_TIMESTAMP
                 WHERE appointment_id = ? AND student_id = ? AND estado = 'atendiendo'"
            )->execute([$appointmentId, $uid]);
            AdminAudit::log($me, 'attendance_close', ['appointment_id' => $appointmentId, 'student_id' => $uid]);
            header('Location: dashboard.php?appointment_id=' . $appointmentId . '#student-' . $uid);
            exit;
        }

        if ($postAction === 'delete_attendance' && $uid > 0) {
            // Borra el resultado de un alumno puntual en esta cita (intentos de
            // prueba, duplicados): su atención y sus acciones de esta cita.
            $idsToDelete = array_map(static fn(array $l): int => (int) $l['id'], DashboardDatos::logsDeCita($appointmentId, [$uid])[$uid] ?? []);
            $pdo->prepare('DELETE FROM attendances WHERE appointment_id = ? AND student_id = ?')->execute([$appointmentId, $uid]);
            foreach (array_chunk($idsToDelete, 500) as $lote) {
                $pdo->prepare('DELETE FROM action_logs WHERE id IN (' . implode(',', array_fill(0, count($lote), '?')) . ')')->execute($lote);
            }
            AdminAudit::log($me, 'attendance_delete', ['appointment_id' => $appointmentId, 'student_id' => $uid, 'logs_deleted' => count($idsToDelete)]);
            header('Location: dashboard.php?appointment_id=' . $appointmentId);
            exit;
        }

        if ($referenceKey !== null && $isFullAdmin) {
            if ($postAction === 'mark_reference') {
                $pdo->prepare(
                    "INSERT INTO app_config (k, course_id, v) VALUES (?, NULL, ?)
                     ON CONFLICT(k) WHERE course_id IS NULL DO UPDATE SET v = excluded.v, updated_at = CURRENT_TIMESTAMP"
                )->execute([$referenceKey, json_encode(['appointment_id' => $appointmentId, 'user_id' => $uid])]);
                AdminAudit::log($me, 'reference_mark', ['appointment_id' => $appointmentId, 'student_id' => $uid]);
            } elseif ($postAction === 'unmark_reference') {
                $pdo->prepare('DELETE FROM app_config WHERE k = ? AND course_id IS NULL')->execute([$referenceKey]);
                AdminAudit::log($me, 'reference_unmark', ['appointment_id' => $appointmentId]);
            }
            header('Location: dashboard.php?appointment_id=' . $appointmentId);
            exit;
        }
    }

    $referenceUserId = null;
    if ($referenceKey !== null) {
        $stmt = $pdo->prepare('SELECT v FROM app_config WHERE k = ? AND course_id IS NULL');
        $stmt->execute([$referenceKey]);
        $refRaw = $stmt->fetchColumn();
        $stmt->closeCursor();
        $refData = $refRaw ? json_decode((string) $refRaw, true) : null;
        if (is_array($refData) && (int) ($refData['appointment_id'] ?? 0) === $appointmentId) {
            $referenceUserId = (int) ($refData['user_id'] ?? 0);
        }
    }
    // La referencia va primera.
    if ($referenceUserId !== null && isset($porAlumno[$referenceUserId])) {
        $porAlumno = [$referenceUserId => $porAlumno[$referenceUserId]] + $porAlumno;
    }

    $logsCita = DashboardDatos::logsDeCita($appointmentId, array_keys($porAlumno));
    $preguntas = DashboardDatos::preguntas([$appointmentId]);
    $informes = DashboardDatos::informes(array_column($atencionesCita, 'attendance_id'));
    $tecnicas = [];
    foreach (array_keys($porAlumno) as $uid) {
        $tecnicas[$uid] = AudiometriaTecnica::deAtenciones($uid, [$appointmentId], $logsCita[$uid] ?? [])[$appointmentId] ?? null;
    }

    admin_add_css('dashboard.css');
    admin_header('Cita · ' . ($appt ? $paciente($appt) : '#' . $appointmentId), $me);
    ?>
    <div class="card dash-cita-cabecera">
        <a href="dashboard.php">&larr; Volver al dashboard</a>
        <?php if ($appt): ?>
        <p>
            <strong><?= htmlspecialchars($appt['procedimiento'] ?: 'Sin procedimiento') ?></strong>
            &nbsp;·&nbsp; cita <?= htmlspecialchars(trim(($appt['fecha'] ?: 'sin fecha') . ' ' . ($appt['hora'] ?: ''))) ?>
            &nbsp;·&nbsp; <?= count($porAlumno) ?> alumno(s)
            <?php if ($appt['case_id']): ?>&nbsp;·&nbsp; <a href="case_create.php?edit=<?= urlencode((string) $appt['case_id']) ?>">ver la ficha del caso</a><?php endif; ?>
        </p>
        <?php else: ?>
        <p class="error">No existe esa cita.</p>
        <?php endif; ?>
    </div>

    <?php if (!$porAlumno): ?>
    <div class="card muted">Ningún alumno abrió esta cita todavía.</div>
    <?php endif; ?>

    <div class="student-grid">
    <?php foreach ($porAlumno as $uid => $a):
        $isReference = $uid === $referenceUserId;
        [$estadoTexto, $estadoClase] = $estados[$a['estado']] ?? [$a['estado'], 'tag--muted'];
        $d = $duracion($a);
        $tec = $tecnicas[$uid]['puntaje'] ?? null;
        $susInformes = $informes[(int) $a['attendance_id']] ?? [];
        $uso = AlumnoIndicadores::usoEquipos($logsCita[$uid] ?? []);
        $nombre = (string) $a['display_name'];
    ?>
    <div class="card dash-alumno<?= $isReference ? ' card-reference' : '' ?><?= $uid === $focusStudentId ? ' dash-alumno--foco' : '' ?>" id="student-<?= $uid ?>">
        <div class="dash-alumno-cabeza">
            <a class="dash-alumno-nombre" href="student.php?id=<?= $uid ?>"><?= htmlspecialchars($nombre) ?></a>
            <span class="tag <?= $estadoClase ?>"><?= htmlspecialchars($estadoTexto) ?></span>
            <?php if ($isReference): ?><span class="badge-ref">Referencia</span><?php endif; ?>
        </div>

        <dl class="dash-datos">
            <div><dt>Tiempo con el paciente</dt><dd><?= $d !== null ? htmlspecialchars(AlumnoIndicadores::minutos($d)) : ($a['estado'] === 'atendiendo' ? 'abierta ' . htmlspecialchars($haceDe((string) $a['updated_at'])) : '—') ?></dd></div>
            <div><dt>Preguntas al paciente</dt><dd><?= $preguntas[$appointmentId][$uid] ?? 0 ?></dd></div>
            <div><dt>Técnica de audiometría</dt><dd>
                <?php if ($tec !== null && $tec['pct'] !== null): ?>
                <a href="chat_detail.php?appointment_id=<?= $appointmentId ?>&amp;student_id=<?= $uid ?>#tecnica" style="color:<?= AudiometriaTecnicaVista::color($tec['pct']) ?>; font-weight:700;"
                   title="<?= (int) $tec['cumple'] ?> de <?= (int) $tec['total'] ?> pasos"><?= (int) $tec['pct'] ?> %</a>
                <?php else: ?>—<?php endif; ?>
            </dd></div>
            <div><dt>Informes</dt><dd>
                <?php foreach ($susInformes as $r): ?>
                <a class="tag" href="report_pdf.php?id=<?= (int) $r['id'] ?>" target="_blank" title="Subido <?= htmlspecialchars($horaLocal((string) $r['updated_at'])) ?>"><?= htmlspecialchars(ReportFile::SHORT_LABELS[$r['tipo']] ?? $r['tipo']) ?></a>
                <?php endforeach; ?>
                <?php if (!$susInformes): ?>ninguno<?php endif; ?>
            </dd></div>
        </dl>

        <?php if ($uso): ?>
        <div class="dash-uso">
            <span class="help help--xs">Usó</span>
            <?php foreach ($uso as $equipo => $u): ?>
            <span class="dash-uso-equipo" title="<?= $u['acciones'] ?> acciones registradas"><strong><?= htmlspecialchars($equipo) ?></strong> <?= htmlspecialchars(AlumnoIndicadores::minutos($u['segundos'])) ?></span>
            <?php endforeach; ?>
        </div>
        <?php endif; ?>

        <?php if (trim((string) $a['nota']) !== ''): ?>
        <p class="dash-nota" title="<?= htmlspecialchars((string) $a['nota']) ?>"><span class="help help--xs">Evolución:</span> <?= htmlspecialchars(mb_strimwidth(preg_replace('/\s+/', ' ', (string) $a['nota']) ?? '', 0, 180, '…')) ?></p>
        <?php endif; ?>

        <div class="dash-acciones">
            <a class="btn btn--sm" href="chat_detail.php?appointment_id=<?= $appointmentId ?>&amp;student_id=<?= $uid ?>">Ver atención</a>
            <?php if ($a['estado'] === 'atendiendo'): ?>
            <?php $lista = $susInformes ? implode(', ', array_map(static fn(array $r): string => $r['tipo'] . ' (' . Clock::fromUtc((string) $r['updated_at'])->format('H:i') . ')', $susInformes)) : 'ninguno'; ?>
            <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Cerrar la atención de ' . $nombre . '? Queda "atendido" con los informes que tiene el servidor: ' . $lista . '. Lo que no haya llegado desde su equipo ya no se va a poder subir. La evolución que escribió en la app no llega.'), ENT_QUOTES) ?>);">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="close_attendance">
                <input type="hidden" name="user_id" value="<?= $uid ?>">
                <button type="submit" class="btn btn--secondary btn--sm">Cerrar atención</button>
            </form>
            <?php endif; ?>
            <?php if (in_array($a['estado'], ['atendido', 'no_show'], true)): ?>
            <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Reactivar la atención de ' . $nombre . '? Vuelve a quedar "atendiendo" para que el alumno la retome, sin crear una cita nueva.'), ENT_QUOTES) ?>);">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="reactivate_attendance">
                <input type="hidden" name="user_id" value="<?= $uid ?>">
                <button type="submit" class="btn btn--secondary btn--sm">Reactivar</button>
            </form>
            <?php endif; ?>
            <?php if ($referenceKey !== null && $isFullAdmin): ?>
            <form method="post" class="inline">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="<?= $isReference ? 'unmark_reference' : 'mark_reference' ?>">
                <input type="hidden" name="user_id" value="<?= $uid ?>">
                <button type="submit" class="btn btn--ghost btn--sm" title="La referencia va primera en esta cita y en las próximas del mismo caso"><?= $isReference ? 'Quitar referencia' : 'Marcar como referencia' ?></button>
            </form>
            <?php endif; ?>
            <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Eliminar el resultado de ' . $nombre . ' para esta cita? Se borran su atención y sus acciones registradas en esta cita. No se puede deshacer.'), ENT_QUOTES) ?>);">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="delete_attendance">
                <input type="hidden" name="user_id" value="<?= $uid ?>">
                <button type="submit" class="btn btn--ghost btn--sm link-danger">Eliminar resultado</button>
            </form>
        </div>

        <?php if (!empty($logsCita[$uid])): ?>
        <details class="dash-registro">
            <summary>Cada acción registrada (<?= count($logsCita[$uid]) ?>)</summary>
            <div class="table-wrap scrollbox scrollbox--short">
            <table class="table-dense">
                <tr><th>Hora (equipo)</th><th>Acción</th></tr>
                <?php foreach ($logsCita[$uid] as $l): ?>
                <tr><td class="nowrap"><?= htmlspecialchars(substr((string) $l['client_ts'], 11, 8)) ?></td><td><?= htmlspecialchars(Metrics::actionLabel((string) $l['action'])) ?></td></tr>
                <?php endforeach; ?>
            </table>
            </div>
        </details>
        <?php endif; ?>
    </div>
    <?php endforeach; ?>
    </div>
    <?php
    admin_footer();
    exit;
}

// ================================================================== general
$todas = DashboardDatos::atenciones($permitidos);
$preguntas = DashboardDatos::preguntas(array_column($todas, 'appointment_id'));
$informes = DashboardDatos::informes(array_column($todas, 'attendance_id'));
// Técnica: guardada para las cerradas (ver AudiometriaTecnica::deAtenciones).
$citasPorAlumno = [];
foreach ($todas as $a) {
    if ($a['estado'] === 'atendido') {
        $citasPorAlumno[(int) $a['student_id']][] = (int) $a['appointment_id'];
    }
}
$tecnica = [];
foreach ($citasPorAlumno as $uid => $citas) {
    foreach (AudiometriaTecnica::deAtenciones($uid, $citas) as $ap => $t) {
        if ($t !== null && $t['puntaje']['pct'] !== null) {
            $tecnica[$ap][$uid] = (int) $t['puntaje']['pct'];
        }
    }
}
$tecDe = static fn(array $a): ?int => $tecnica[(int) $a['appointment_id']][(int) $a['student_id']] ?? null;

$semana = gmdate('Y-m-d H:i:s', $ahora - 7 * 86400);
$enCurso = array_values(array_filter($todas, static fn(array $a): bool => $a['estado'] === 'atendiendo'));
$cerradas = array_values(array_filter($todas, static fn(array $a): bool => $a['estado'] === 'atendido'));
$cerradasSemana = array_values(array_filter($cerradas, static fn(array $a): bool => (string) $a['updated_at'] >= $semana));
$alumnosSemana = count(array_unique(array_column($cerradasSemana, 'student_id')));
$durSemana = array_values(array_filter(array_map($duracion, $cerradasSemana), static fn($v): bool => $v !== null));
$tecSemana = array_values(array_filter(array_map($tecDe, $cerradasSemana), static fn($v): bool => $v !== null));

// Alumnos: todos los del roster visible (también los que no han atendido) o,
// para el admin sin foco de curso, los que tienen atenciones.
$alumnos = [];
if ($permitidos !== null && $permitidos) {
    $stmt = $pdo->prepare(
        "SELECT u.id, u.display_name FROM users u
          WHERE u.role = 'student' AND u.is_demo = 0 AND u.active = 1 AND u.id IN (" . implode(',', array_fill(0, count($permitidos), '?')) . ')'
    );
    $stmt->execute(array_map('intval', $permitidos));
    foreach ($stmt->fetchAll() as $u) {
        $alumnos[(int) $u['id']] = ['nombre' => (string) $u['display_name']];
    }
}
foreach ($todas as $a) {
    $uid = (int) $a['student_id'];
    $alumnos[$uid] = ($alumnos[$uid] ?? []) + ['nombre' => (string) $a['display_name']];
}
foreach ($alumnos as $uid => &$al) {
    $al += ['cerradas' => 0, 'en_curso' => 0, 'ultima' => null, 'informes' => 0, 'cursos' => [], 'tec' => [], 'dur' => []];
}
unset($al);
foreach ($todas as $a) {
    $al = &$alumnos[(int) $a['student_id']];
    if ($a['course_name']) {
        $al['cursos'][$a['course_name']] = true;
    }
    if ($a['estado'] === 'atendido') {
        $al['cerradas']++;
        $al['ultima'] = max((string) $al['ultima'], (string) $a['updated_at']);
        $al['informes'] += count($informes[(int) $a['attendance_id']] ?? []);
        if (($t = $tecDe($a)) !== null) {
            $al['tec'][] = $t;
        }
        if (($d = $duracion($a)) !== null) {
            $al['dur'][] = $d;
        }
    } elseif ($a['estado'] === 'atendiendo') {
        $al['en_curso']++;
    }
    unset($al);
}
uasort($alumnos, static fn(array $x, array $y): int => [(string) $y['ultima'], $x['nombre']] <=> [(string) $x['ultima'], $y['nombre']]);

// Pacientes (una fila por cita), el de actividad más reciente primero.
$citas = [];
foreach ($todas as $a) {
    $ap = (int) $a['appointment_id'];
    if (!isset($citas[$ap])) {
        $citas[$ap] = ['a' => $a, 'cerradas' => 0, 'en_curso' => 0, 'ultima' => (string) $a['updated_at'], 'tec' => [], 'dur' => []];
    }
    $c = &$citas[$ap];
    if ($a['estado'] === 'atendido') {
        $c['cerradas']++;
        if (($t = $tecDe($a)) !== null) {
            $c['tec'][] = $t;
        }
        if (($d = $duracion($a)) !== null) {
            $c['dur'][] = $d;
        }
    } elseif ($a['estado'] === 'atendiendo') {
        $c['en_curso']++;
    }
    unset($c);
}

admin_add_css('dashboard.css');
admin_header('Dashboard', $me);
if ($contextCourseName !== null) {
    echo '<p class="help help--xs" style="margin-top:-0.6rem;">Acotado a <strong>'
        . htmlspecialchars($contextCourseName)
        . '</strong> -- se cambia en el selector de curso del header.</p>';
}
?>
<div class="dash-kpis">
    <div class="dash-kpi">
        <div class="dash-kpi-valor"><?= count($cerradasSemana) ?></div>
        <div class="dash-kpi-nombre">Atenciones cerradas esta semana</div>
        <div class="dash-kpi-pie"><?= count($cerradas) ?> en total</div>
    </div>
    <div class="dash-kpi">
        <div class="dash-kpi-valor"><?= $alumnosSemana ?><?php if ($permitidos !== null): ?><span class="dash-kpi-de"> / <?= count($alumnos) ?></span><?php endif; ?></div>
        <div class="dash-kpi-nombre">Alumnos que atendieron esta semana</div>
    </div>
    <div class="dash-kpi<?= $enCurso ? ' dash-kpi--aviso' : '' ?>">
        <div class="dash-kpi-valor"><?= count($enCurso) ?></div>
        <div class="dash-kpi-nombre">Atendiendo ahora</div>
        <div class="dash-kpi-pie"><?= $enCurso ? 'abiertas sin cerrar' : 'nadie con una atención abierta' ?></div>
    </div>
    <div class="dash-kpi">
        <div class="dash-kpi-valor"><?= htmlspecialchars(AlumnoIndicadores::minutos(AlumnoIndicadores::promedio($durSemana))) ?></div>
        <div class="dash-kpi-nombre">Tiempo promedio por atención</div>
        <div class="dash-kpi-pie">esta semana</div>
    </div>
    <div class="dash-kpi">
        <?php $tp = AlumnoIndicadores::promedio($tecSemana); ?>
        <div class="dash-kpi-valor" style="color:<?= AudiometriaTecnicaVista::color($tp) ?>;"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($tp)) ?></div>
        <div class="dash-kpi-nombre">Técnica de audiometría</div>
        <div class="dash-kpi-pie">promedio de <?= count($tecSemana) ?> audiometría(s) esta semana</div>
    </div>
</div>

<?php if ($enCurso): ?>
<div class="card">
    <strong>Atendiendo ahora (<?= count($enCurso) ?>)</strong>
    <p class="help help--xs">Atenciones abiertas. Si una lleva mucho rato, puede que el alumno no haya podido cerrarla: entra a la cita para cerrarla o reactivarla.</p>
    <div class="dash-lista">
        <?php foreach ($enCurso as $a): ?>
        <a class="dash-fila" href="dashboard.php?appointment_id=<?= (int) $a['appointment_id'] ?>#student-<?= (int) $a['student_id'] ?>">
            <span class="dash-fila-principal"><strong><?= htmlspecialchars((string) $a['display_name']) ?></strong> con <?= htmlspecialchars($paciente($a)) ?></span>
            <span class="help"><?= htmlspecialchars($a['procedimiento'] ?: '') ?></span>
            <span class="dash-fila-dato">abierta <?= htmlspecialchars($haceDe((string) $a['updated_at'])) ?></span>
        </a>
        <?php endforeach; ?>
    </div>
</div>
<?php endif; ?>

<div class="card">
    <strong>Últimas atenciones cerradas</strong>
    <?php if (!$cerradas): ?>
    <p class="muted">Todavía no hay atenciones cerradas.</p>
    <?php else: ?>
    <div class="table-wrap">
    <table class="table-dense">
        <tr><th>Cuándo</th><th>Alumno</th><th>Paciente</th><th>Procedimiento</th><th>Tiempo</th><th title="Preguntas al paciente">Preguntas</th><th>Técnica</th><th>Informes</th><th></th></tr>
        <?php foreach (array_slice($cerradas, 0, 12) as $a):
            $ap = (int) $a['appointment_id'];
            $uid = (int) $a['student_id'];
            $d = $duracion($a);
            $t = $tecDe($a);
        ?>
        <tr>
            <td class="nowrap" title="<?= htmlspecialchars($horaLocal((string) $a['updated_at'])) ?>"><?= htmlspecialchars($haceDe((string) $a['updated_at'])) ?></td>
            <td><a href="student.php?id=<?= $uid ?>"><?= htmlspecialchars((string) $a['display_name']) ?></a></td>
            <td><a href="dashboard.php?appointment_id=<?= $ap ?>"><?= htmlspecialchars($paciente($a)) ?></a></td>
            <td><?= htmlspecialchars($a['procedimiento'] ?: '—') ?></td>
            <td class="nowrap"><?= $d !== null ? htmlspecialchars(AlumnoIndicadores::minutos($d)) : '—' ?></td>
            <td><?= $preguntas[$ap][$uid] ?? 0 ?></td>
            <td><?php if ($t !== null): ?><span style="color:<?= AudiometriaTecnicaVista::color($t) ?>; font-weight:700;"><?= $t ?> %</span><?php else: ?>—<?php endif; ?></td>
            <td><?php foreach ($informes[(int) $a['attendance_id']] ?? [] as $r): ?><span class="tag"><?= htmlspecialchars(ReportFile::SHORT_LABELS[$r['tipo']] ?? $r['tipo']) ?></span><?php endforeach; ?></td>
            <td class="nowrap"><a href="chat_detail.php?appointment_id=<?= $ap ?>&amp;student_id=<?= $uid ?>">Ver atención</a></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php endif; ?>
</div>

<div class="dash-columnas">
<div class="card">
    <strong>Alumnos (<?= count($alumnos) ?>)</strong>
    <p class="help help--xs">El que atendió más recién primero. Técnica y tiempo son promedios de sus atenciones cerradas.</p>
    <div class="table-wrap">
    <table class="table-dense">
        <tr><th>Alumno</th><th>Atenciones</th><th>Última</th><th>Técnica</th><th>Tiempo</th><th>Informes</th></tr>
        <?php foreach ($alumnos as $uid => $al):
            $tp = AlumnoIndicadores::promedio($al['tec']);
        ?>
        <tr>
            <td><a href="student.php?id=<?= (int) $uid ?>"><?= htmlspecialchars($al['nombre']) ?></a><?php if (count($al['cursos']) > 0 && $contextCourseId === null): ?><br><span class="help help--xs" title="<?= htmlspecialchars(implode(', ', array_keys($al['cursos']))) ?>"><?= htmlspecialchars(implode(', ', array_map($cursoCorto, array_keys($al['cursos'])))) ?></span><?php endif; ?></td>
            <td><?= $al['cerradas'] ?><?= $al['en_curso'] ? ' <span class="tag tag--warn">+' . $al['en_curso'] . ' abierta</span>' : '' ?></td>
            <td class="nowrap help"><?= $al['ultima'] ? htmlspecialchars($haceDe($al['ultima'])) : 'nunca' ?></td>
            <td><?php if ($tp !== null): ?><span style="color:<?= AudiometriaTecnicaVista::color($tp) ?>; font-weight:700;"><?= $tp ?> %</span><?php else: ?>—<?php endif; ?></td>
            <td class="nowrap"><?= htmlspecialchars(AlumnoIndicadores::minutos(AlumnoIndicadores::promedio($al['dur']))) ?></td>
            <td><?= $al['informes'] ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$alumnos): ?>
        <tr><td colspan="6" class="muted">Sin alumnos todavía.</td></tr>
        <?php endif; ?>
    </table>
    </div>
</div>

<div class="card">
    <strong>Pacientes (<?= count($citas) ?>)</strong>
    <p class="help help--xs">Cada cita con los alumnos que la atendieron. Pincha una para ver a cada alumno y cerrar o reactivar su atención.</p>
    <div class="table-wrap">
    <table class="table-dense">
        <tr><th>Paciente</th><th>Alumnos</th><th>Tiempo</th><th>Técnica</th><th>Última</th></tr>
        <?php $i = 0; foreach ($citas as $ap => $c):
            $tp = AlumnoIndicadores::promedio($c['tec']);
            $i++;
        ?>
        <tr<?= $i > 15 ? ' class="dash-mas" hidden' : '' ?>>
            <td><a href="dashboard.php?appointment_id=<?= (int) $ap ?>"><?= htmlspecialchars($paciente($c['a'])) ?></a><br><span class="help help--xs"><?= htmlspecialchars(trim(($c['a']['procedimiento'] ?: '') . ($contextCourseId === null && $c['a']['course_name'] ? ' · ' . $cursoCorto($c['a']['course_name']) : ''))) ?></span></td>
            <td><?= $c['cerradas'] ?><?= $c['en_curso'] ? ' <span class="tag tag--warn">+' . $c['en_curso'] . ' abierta</span>' : '' ?></td>
            <td class="nowrap"><?= htmlspecialchars(AlumnoIndicadores::minutos(AlumnoIndicadores::promedio($c['dur']))) ?></td>
            <td><?php if ($tp !== null): ?><span style="color:<?= AudiometriaTecnicaVista::color($tp) ?>; font-weight:700;"><?= $tp ?> %</span><?php else: ?>—<?php endif; ?></td>
            <td class="nowrap help"><?= htmlspecialchars($haceDe($c['ultima'])) ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$citas): ?>
        <tr><td colspan="5" class="muted">Ningún paciente atendido todavía.</td></tr>
        <?php endif; ?>
    </table>
    </div>
    <?php if (count($citas) > 15): ?>
    <button type="button" class="btn btn--ghost btn--sm" onclick="this.closest('.card').querySelectorAll('.dash-mas').forEach(function (f) { f.hidden = false; }); this.remove();">Ver los otros <?= count($citas) - 15 ?></button>
    <?php endif; ?>
</div>
</div>
<?php
admin_footer();
