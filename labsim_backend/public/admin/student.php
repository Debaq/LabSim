<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Oirs.php';
require_once __DIR__ . '/../../src/Metrics.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/ReportFile.php';
require_once __DIR__ . '/../../src/ReportVersions.php';
require_once __DIR__ . '/../../src/AudiometriaTecnicaVista.php';
require_once __DIR__ . '/../../src/AlumnoIndicadores.php';

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
            a.id AS appointment_id, a.fecha, a.hora, a.nombre, a.apellido, a.procedimiento,
            " . (Practica::listo() ? 'a.practice_id' : 'NULL') . " AS practice_id
     FROM attendances att
     JOIN appointments a ON a.id = att.appointment_id
     WHERE att.student_id = ?
     ORDER BY att.updated_at DESC"
);
$stmt->execute([$studentId]);
$todasLasAtenciones = $stmt->fetchAll();
// Los intentos de práctica deliberada van en su propia tabla y no entran
// al resumen ni a la evolución semanal, que hablan de los prácticos (ver
// Practica).
$attendances = array_values(array_filter($todasLasAtenciones, static fn(array $a): bool => $a['practice_id'] === null));
$practicas = array_values(array_filter($todasLasAtenciones, static fn(array $a): bool => $a['practice_id'] !== null));
$citasPractica = array_flip(array_map('intval', array_column($practicas, 'appointment_id')));

// Informes de examen (ABR, EOA, VEMP...) por cita, para abrirlos desde acá
// mismo. Antes había que entrar a "Ver atención" y bajar hasta el final.
$stmt = $pdo->prepare(
    'SELECT r.id, r.tipo, att.appointment_id
     FROM reports r
     JOIN attendances att ON att.id = r.attendance_id
     WHERE att.student_id = ?
     ORDER BY r.tipo'
);
$stmt->execute([$studentId]);
$reportsByAppt = [];
foreach ($stmt->fetchAll() as $r) {
    $reportsByAppt[(int) $r['appointment_id']][] = $r;
}
$totalReports = array_sum(array_map('count', $reportsByAppt));
// Versiones que otra subida pisó (ver ReportVersions): se ofrecen al lado.
$versionesPorInforme = ReportVersions::contar(
    array_merge([], ...array_map(static function (array $rs): array {
        return array_column($rs, 'id');
    }, array_values($reportsByAppt)))
);

$estadoCounts = ['atendiendo' => 0, 'atendido' => 0, 'no_show' => 0];
foreach ($attendances as $a) {
    if (isset($estadoCounts[$a['estado']])) {
        $estadoCounts[$a['estado']]++;
    }
}

Oirs::normalizarGuardados($pdo);
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

// El registro técnico (ritmo, acciones, últimas 30) necesita TODAS las filas
// de action_logs del alumno: miles. Se arma solo cuando se pide
// (?registro=1); la vista normal no lee ni una.
$verRegistro = ($_GET['registro'] ?? '') === '1';
$stmt = $pdo->prepare('SELECT COUNT(*) FROM action_logs WHERE user_id = ?');
$stmt->execute([$studentId]);
$totalActions = (int) $stmt->fetchColumn();
$stmt->closeCursor();
$actionCounts = $recentLogs = $allLogs = $weekly = $histogram = [];
$behaviorStats = ['n_sessions' => 0, 'long_pauses' => 0, 'no_pause_actions' => 0];
$statsByAppt = [];
$totalDurationRealS = 0;
$histTotal = 1;
if ($verRegistro) {
    $stmt = $pdo->prepare(
        'SELECT action, COUNT(*) AS n, MAX(client_ts) AS last_ts
         FROM action_logs WHERE user_id = ? GROUP BY action ORDER BY n DESC'
    );
    $stmt->execute([$studentId]);
    $actionCounts = $stmt->fetchAll();

    $stmt = $pdo->prepare(
        'SELECT client_ts, action, payload FROM action_logs WHERE user_id = ? ORDER BY id DESC LIMIT 30'
    );
    $stmt->execute([$studentId]);
    $recentLogs = $stmt->fetchAll();

    $stmt = $pdo->prepare('SELECT user_id, client_ts, action, payload FROM action_logs WHERE user_id = ? ORDER BY id');
    $stmt->execute([$studentId]);
    $allLogs = Metrics::decodeLogs($stmt->fetchAll());
    $sessionsTodas = Metrics::buildSessions($allLogs);
    $logsPracticos = array_values(array_filter(
        $allLogs,
        static fn(array $l): bool => $l['appointment_id'] === null || $l['appointment_id'] === ''
            || !isset($citasPractica[(int) $l['appointment_id']])
    ));
    $sessions = Metrics::buildSessions($logsPracticos);
    $behaviorStats = Metrics::summarizeSessions($sessions);
    $weekly = Metrics::sessionsByWeek($sessions);
    $histogram = Metrics::deltaHistogram($sessions);
    $histTotal = array_sum($histogram) ?: 1;

    // buildSessions() ya corta una sesión nueva cuando cambia appointment_id/case_id
    // (ver Metrics::buildSessions), así que agrupar por ahí separa correctamente
    // las métricas de comportamiento por atención.
    $sessionsByAppt = [];
    foreach ($sessionsTodas as $s) {
        $key = $s['appointment_id'] !== null ? (int) $s['appointment_id'] : 0;
        $sessionsByAppt[$key][] = $s;
    }
    foreach ($sessionsByAppt as $key => $group) {
        $stats = Metrics::summarizeSessions($group);
        // total_duration_s de summarizeSessions() suma solo los bloques activos
        // y esconde pausas >5min (ver Metrics::wallClockDurationSeconds): acá
        // se quiere el reloj real.
        $stats['total_duration_s'] = Metrics::wallClockDurationSeconds($group);
        $statsByAppt[$key] = $stats;
    }

    // Duración total: mismo criterio real por atención que la tabla
    // (hora_real->updated_at si está cerrada, si no reloj real de bloques).
    foreach ($attendances as $a) {
        $aStats = $statsByAppt[(int) $a['appointment_id']] ?? null;
        $realDuration = $a['estado'] === 'atendido'
            ? Metrics::attendanceDurationSeconds($a['hora_real'], $a['updated_at'])
            : null;
        $totalDurationRealS += $realDuration ?? ($aStats['total_duration_s'] ?? 0);
    }
}

// Técnica de la audiometría por atención (ver AudiometriaTecnica): pasos
// cumplidos sobre los evaluables, con el detalle en "Ver atención". Se
// guarda el resultado entero: de ahí salen los pasos que más le cuestan.
// Las cerradas salen guardadas (ver AudiometriaTecnica::deAtenciones).
$tecnicaCompleta = array_filter(AudiometriaTecnica::deAtenciones(
    $studentId,
    array_map('intval', array_column($todasLasAtenciones, 'appointment_id')),
    $verRegistro ? $allLogs : null
));
$tecnicaByAppt = array_map(static function (array $t): array {
    return $t['puntaje'];
}, $tecnicaCompleta);

// Serie cronológica del logro (la más vieja primero) para el gráfico y la
// tendencia. Las atenciones vienen de la más nueva a la más vieja.
$serieTecnica = [];
foreach (array_reverse($todasLasAtenciones) as $a) {
    $p = $tecnicaByAppt[(int) $a['appointment_id']]['pct'] ?? null;
    if ($p !== null) {
        $serieTecnica[] = [
            'pct' => (int) $p,
            'fecha' => (string) ($a['fecha'] ?: substr((string) $a['updated_at'], 0, 10)),
            'paciente' => trim("{$a['nombre']} {$a['apellido']}"),
            'practica' => $a['practice_id'] !== null,
            'appointment_id' => (int) $a['appointment_id'],
        ];
    }
}
$pctsTecnica = array_column($serieTecnica, 'pct');
$tecnicaPromedio = AlumnoIndicadores::promedio($pctsTecnica);
$tecnicaTendencia = AlumnoIndicadores::tendencia($pctsTecnica);
$pasosDificiles = array_slice(AlumnoIndicadores::pasosDificiles(array_values($tecnicaCompleta)), 0, 6);

// Duración típica de una atención cerrada (mediana: una que quedó abierta
// toda la tarde no la arrastra).
$duraciones = [];
foreach ($attendances as $a) {
    if ($a['estado'] === 'atendido') {
        $d = Metrics::attendanceDurationSeconds($a['hora_real'], $a['updated_at']);
        if ($d !== null) {
            $duraciones[] = $d;
        }
    }
}
$duracionTipica = AlumnoIndicadores::mediana($duraciones);

// Preguntas que le hizo al paciente (turnos del alumno en el chat), por cita.
$stmt = $pdo->prepare("SELECT appointment_id, COUNT(*) AS n FROM llm_chat_logs WHERE student_id = ? AND role = 'user' GROUP BY appointment_id");
$stmt->execute([$studentId]);
$preguntasByAppt = [];
foreach ($stmt->fetchAll() as $r) {
    $preguntasByAppt[(int) $r['appointment_id']] = (int) $r['n'];
}
$preguntasPracticos = [];
foreach ($attendances as $a) {
    if (isset($preguntasByAppt[(int) $a['appointment_id']])) {
        $preguntasPracticos[] = $preguntasByAppt[(int) $a['appointment_id']];
    }
}

// Informes entregados por examen.
$informesPorTipo = [];
foreach ($reportsByAppt as $rs) {
    foreach ($rs as $r) {
        $informesPorTipo[$r['tipo']] = ($informesPorTipo[$r['tipo']] ?? 0) + 1;
    }
}
arsort($informesPorTipo);

$oirsCuenta = ['merito' => 0, 'reclamo' => 0];
foreach ($inboxMessages as $m) {
    if (isset($oirsCuenta[$m['tipo']])) {
        $oirsCuenta[$m['tipo']]++;
    }
}
$practicasCerradas = count(array_filter($practicas, static fn(array $a): bool => $a['estado'] === 'atendido'));
$ultimaActividad = $todasLasAtenciones[0]['updated_at'] ?? null;

$stmt = $pdo->prepare('SELECT c.name FROM courses c JOIN course_students cs ON cs.course_id = c.id WHERE cs.user_id = ? ORDER BY c.name');
$stmt->execute([$studentId]);
$cursosAlumno = $stmt->fetchAll(PDO::FETCH_COLUMN);

$estadoTag = ['atendido' => ['cerrada', 'tag--success'], 'atendiendo' => ['en curso', 'tag--warn'], 'no_show' => ['no se presentó', 'tag--muted']];

admin_add_css('student-detail.css');
admin_header('Alumno: ' . $student['display_name'], $me);
?>
<div class="card alumno-cabecera">
    <div>
        <div class="help alumno-meta">
            <span class="mono"><?= htmlspecialchars($student['username']) ?></span>
            &nbsp;·&nbsp; <?= $student['active'] ? 'activo' : '<strong>inactivo</strong>' ?>
            <?php if ($cursosAlumno): ?>&nbsp;·&nbsp; <?= htmlspecialchars(implode(', ', $cursosAlumno)) ?><?php endif; ?>
            <?php if ($ultimaActividad): ?>&nbsp;·&nbsp; última atención <?= htmlspecialchars(substr((string) $ultimaActividad, 0, 10)) ?><?php endif; ?>
        </div>
    </div>
    <a class="btn btn--sm btn--secondary" href="ver_como.php?id=<?= (int) $studentId ?>">Ver como alumno →</a>
</div>

<div class="kpis">
    <div class="kpi">
        <div class="kpi-valor"><?= $estadoCounts['atendido'] ?></div>
        <div class="kpi-nombre">Atenciones cerradas</div>
        <div class="kpi-pie">
            <?= $estadoCounts['atendiendo'] ?> en curso<?= $estadoCounts['no_show'] ? ' · ' . $estadoCounts['no_show'] . ' no se presentó' : '' ?>
        </div>
    </div>
    <div class="kpi">
        <div class="kpi-valor" style="color:<?= AudiometriaTecnicaVista::color($tecnicaPromedio) ?>;"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($tecnicaPromedio)) ?></div>
        <div class="kpi-nombre">Técnica de audiometría</div>
        <div class="kpi-pie">
            <?php if ($tecnicaTendencia !== null): ?>
            <span class="<?= $tecnicaTendencia > 0 ? 'kpi-sube' : ($tecnicaTendencia < 0 ? 'kpi-baja' : '') ?>">
                <?= $tecnicaTendencia > 0 ? '▲ +' : ($tecnicaTendencia < 0 ? '▼ ' : '= ') ?><?= $tecnicaTendencia ?> pts
            </span> de las primeras a las últimas
            <?php elseif ($pctsTecnica): ?>
            de su única audiometría
            <?php else: ?>
            sin audiometrías todavía
            <?php endif; ?>
        </div>
    </div>
    <div class="kpi">
        <div class="kpi-valor"><?= (int) $totalReports ?></div>
        <div class="kpi-nombre">Informes entregados</div>
        <div class="kpi-pie">
            <?php foreach ($informesPorTipo as $tipo => $n): ?>
            <span class="tag"><?= htmlspecialchars(ReportFile::SHORT_LABELS[$tipo] ?? $tipo) ?> <?= $n ?></span>
            <?php endforeach; ?>
            <?php if (!$informesPorTipo): ?>ninguno todavía<?php endif; ?>
        </div>
    </div>
    <div class="kpi">
        <div class="kpi-valor"><?= htmlspecialchars(AlumnoIndicadores::minutos($duracionTipica)) ?></div>
        <div class="kpi-nombre">Duración típica</div>
        <div class="kpi-pie">mediana de <?= count($duraciones) ?> atención(es) cerrada(s)</div>
    </div>
    <div class="kpi">
        <div class="kpi-valor"><?= AlumnoIndicadores::mediana($preguntasPracticos) ?? '—' ?></div>
        <div class="kpi-nombre">Preguntas al paciente</div>
        <div class="kpi-pie">por atención (mediana) en la anamnesis</div>
    </div>
    <div class="kpi">
        <div class="kpi-valor"><?= $practicasCerradas ?></div>
        <div class="kpi-nombre">Práctica libre</div>
        <div class="kpi-pie"><?= count($practicas) ?> intento(s) en total</div>
    </div>
    <div class="kpi">
        <div class="kpi-valor kpi-valor--par">
            <span title="Felicitaciones" style="color:var(--color-success-text);">♥ <?= $oirsCuenta['merito'] ?></span>
            <span title="Sugerencias de mejora" style="color:var(--color-warn-text);">✎ <?= $oirsCuenta['reclamo'] ?></span>
        </div>
        <div class="kpi-nombre">Trato al paciente</div>
        <div class="kpi-pie">felicitaciones · sugerencias de mejora</div>
    </div>
</div>

<?php if ($serieTecnica): ?>
<div class="card">
    <div class="row row--between" style="margin:0; align-items:baseline;">
        <strong>Técnica de audiometría en el tiempo</strong>
        <span class="help help--xs">verde ≥ 85 % · ámbar ≥ 60 % · rojo debajo · ○ práctica libre</span>
    </div>
    <?php
    // Gráfico de línea en SVG: x = orden de la atención, y = % de logro.
    $n = count($serieTecnica);
    $ancho = 600;
    $alto = 140;
    $margen = 14;
    $x = static fn(int $i): float => $n === 1 ? $ancho / 2 : $margen + $i * ($ancho - 2 * $margen) / ($n - 1);
    $y = static fn(int $pct): float => $margen + (100 - $pct) * ($alto - 2 * $margen) / 100;
    $puntos = [];
    foreach ($serieTecnica as $i => $p) {
        $puntos[] = round($x($i), 1) . ',' . round($y($p['pct']), 1);
    }
    ?>
    <svg class="tec-grafico" viewBox="0 0 <?= $ancho ?> <?= $alto ?>" preserveAspectRatio="none" role="img"
         aria-label="Logro de la técnica en cada audiometría, de la primera a la última">
        <rect x="0" y="<?= $y(100) ?>" width="<?= $ancho ?>" height="<?= $y(85) - $y(100) ?>" class="tec-banda tec-banda--bien"/>
        <rect x="0" y="<?= $y(85) ?>" width="<?= $ancho ?>" height="<?= $y(60) - $y(85) ?>" class="tec-banda tec-banda--medio"/>
        <rect x="0" y="<?= $y(60) ?>" width="<?= $ancho ?>" height="<?= $y(0) - $y(60) ?>" class="tec-banda tec-banda--bajo"/>
        <?php if ($n > 1): ?><polyline points="<?= implode(' ', $puntos) ?>" class="tec-linea" vector-effect="non-scaling-stroke"/><?php endif; ?>
    </svg>
    <div class="tec-puntos">
        <?php foreach ($serieTecnica as $i => $p): ?>
        <a class="tec-punto<?= $p['practica'] ? ' tec-punto--practica' : '' ?>"
           style="left:<?= round($x($i) / $ancho * 100, 2) ?>%; top:<?= round($y($p['pct']) / $alto * 100, 2) ?>%; --c:<?= AudiometriaTecnicaVista::color($p['pct']) ?>;"
           href="chat_detail.php?appointment_id=<?= $p['appointment_id'] ?>&student_id=<?= (int) $studentId ?>#tecnica"
           title="<?= htmlspecialchars($p['fecha'] . ' · ' . ($p['paciente'] ?: 'sin nombre') . ' · ' . $p['pct'] . ' %' . ($p['practica'] ? ' (práctica libre)' : '')) ?>"></a>
        <?php endforeach; ?>
    </div>

    <?php if ($pasosDificiles): ?>
    <div class="section-sep">
        <strong>Lo que más le cuesta</strong>
        <p class="help help--xs">Pasos de la técnica que no cumplió, sobre las audiometrías donde se podían evaluar.</p>
        <div class="pasos">
            <?php foreach ($pasosDificiles as $paso): ?>
            <?php $pctFallo = (int) round(100 * $paso['fallos'] / $paso['evaluadas']); ?>
            <div class="paso">
                <span class="tag tag--muted"><?= htmlspecialchars($paso['seccion']) ?></span>
                <span class="paso-texto"><?= htmlspecialchars($paso['texto']) ?></span>
                <span class="paso-barra" title="<?= $pctFallo ?> %"><span style="width:<?= $pctFallo ?>%;"></span></span>
                <span class="paso-cuenta"><?= $paso['fallos'] ?> de <?= $paso['evaluadas'] ?></span>
            </div>
            <?php endforeach; ?>
        </div>
    </div>
    <?php elseif (count($serieTecnica) > 0): ?>
    <p class="help section-sep">Cumplió todos los pasos evaluables en sus audiometrías.</p>
    <?php endif; ?>
</div>
<?php endif; ?>

<?php
/** Tabla de atenciones (prácticos o intentos de práctica), una fila por cita. */
$tablaAtenciones = static function (array $filas, string $vacio) use ($statsByAppt, $studentId, $reportsByAppt, $versionesPorInforme, $tecnicaByAppt, $preguntasByAppt, $estadoTag): void {
    ?>
    <div class="table-wrap">
    <table class="table-dense">
        <tr><th>Cita</th><th>Paciente</th><th>Procedimiento</th><th>Estado</th><th>Duración</th><th title="Preguntas que le hizo al paciente en el chat">Preguntas</th><th title="Logro de la técnica de audiometría (pasos cumplidos sobre los evaluables)">Técnica</th><th>Exámenes</th><th>Nota</th><th></th></tr>
        <?php foreach ($filas as $a):
            $aStats = $statsByAppt[(int) $a['appointment_id']] ?? null;
            // Duración real (Atender -> Atendido) siempre que esté cerrada;
            // más confiable que el cálculo por action_logs, que arranca recién
            // cuando el alumno toca el audiómetro/impedanciómetro y se pierde
            // el rato leyendo el caso -- ver Metrics::attendanceDurationSeconds.
            $realDuration = $a['estado'] === 'atendido'
                ? Metrics::attendanceDurationSeconds($a['hora_real'], $a['updated_at'])
                : null;
            $durationS = $realDuration ?? ($aStats['total_duration_s'] ?? null);
            [$estadoTexto, $estadoClase] = $estadoTag[$a['estado']] ?? [$a['estado'], 'tag--muted'];
        ?>
        <tr>
            <td class="nowrap"><a href="dashboard.php?appointment_id=<?= (int) $a['appointment_id'] ?>&student_id=<?= (int) $studentId ?>#student-<?= (int) $studentId ?>"><?= htmlspecialchars($a['fecha'] ?: '—') ?> <?= htmlspecialchars($a['hora'] ?: '') ?></a></td>
            <td><?= htmlspecialchars(trim("{$a['nombre']} {$a['apellido']}")) ?: '—' ?></td>
            <td><?= htmlspecialchars($a['procedimiento']) ?></td>
            <td><span class="tag <?= $estadoClase ?>"><?= htmlspecialchars($estadoTexto) ?></span></td>
            <td class="nowrap"><?= $durationS !== null ? htmlspecialchars(AlumnoIndicadores::minutos((int) $durationS)) : '—' ?></td>
            <td><?= $preguntasByAppt[(int) $a['appointment_id']] ?? '—' ?></td>
            <td><?php $tec = $tecnicaByAppt[(int) $a['appointment_id']] ?? null; ?>
                <?php if ($tec): ?><a href="chat_detail.php?appointment_id=<?= (int) $a['appointment_id'] ?>&student_id=<?= (int) $studentId ?>#tecnica"
                   title="<?= (int) $tec['cumple'] ?> de <?= (int) $tec['total'] ?> pasos" style="color:<?= AudiometriaTecnicaVista::color($tec['pct']) ?>; font-weight:600;"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($tec['pct'])) ?></a><?php else: ?><span class="muted">—</span><?php endif; ?></td>
            <td>
                <?php foreach ($reportsByAppt[(int) $a['appointment_id']] ?? [] as $r): ?>
                <a class="tag" href="report_pdf.php?id=<?= (int) $r['id'] ?>" target="_blank"
                   title="<?= htmlspecialchars(ReportFile::LABELS[$r['tipo']] ?? $r['tipo']) ?> (PDF)"><?= htmlspecialchars(ReportFile::SHORT_LABELS[$r['tipo']] ?? $r['tipo']) ?></a>
                <?php if (!empty($versionesPorInforme[(int) $r['id']])): ?>
                <a href="report_versions.php?report_id=<?= (int) $r['id'] ?>" class="help"
                   title="Versiones reemplazadas por otra subida">(<?= (int) $versionesPorInforme[(int) $r['id']] ?> ant.)</a>
                <?php endif; ?>
                <?php endforeach; ?>
                <?php if (empty($reportsByAppt[(int) $a['appointment_id']])): ?><span class="muted">—</span><?php endif; ?>
            </td>
            <td class="help"><?= htmlspecialchars($a['nota'] ?: '') ?></td>
            <td class="nowrap"><a href="chat_detail.php?appointment_id=<?= (int) $a['appointment_id'] ?>&student_id=<?= (int) $studentId ?>">Ver atención</a></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$filas): ?>
        <tr><td colspan="10" class="muted"><?= htmlspecialchars($vacio) ?></td></tr>
        <?php endif; ?>
    </table>
    </div>
    <?php
};
?>
<div class="card">
    <strong>Atenciones (<?= count($attendances) ?>)</strong>
    <?php $tablaAtenciones($attendances, 'Sin atenciones registradas todavía.'); ?>
</div>

<?php if ($practicas): ?>
<div class="card">
    <strong>Práctica libre (<?= count($practicas) ?> intento<?= count($practicas) === 1 ? '' : 's' ?>)</strong>
    <p class="legend">Pacientes de la lista de práctica del curso, abiertos cuando el alumno quiso. No entran a los indicadores de los prácticos, salvo la técnica (marcada con ○ en el gráfico).</p>
    <?php $tablaAtenciones($practicas, ''); ?>
</div>
<?php endif; ?>

<?php
$tipoLabels = Oirs::LABELS;
?>
<div class="card">
    <strong>Bandeja de entrada (<?= count($inboxMessages) ?>)</strong>
    <p class="legend">Avisos automáticos sobre el trato a pacientes (ver Admin -> IA Paciente) y mensajes que algún docente le mandó directo. Misma bandeja que ve el alumno en la app.</p>
    <?php if ($inboxMessages): ?>
    <div class="mensajes">
        <?php foreach ($inboxMessages as $m): ?>
        <div class="mensaje mensaje--<?= htmlspecialchars($m['tipo']) ?>">
            <div class="mensaje-cabeza">
                <span class="tag <?= $m['tipo'] === 'merito' ? 'tag--success' : ($m['tipo'] === 'reclamo' ? 'tag--warn' : '') ?>"><?= htmlspecialchars($tipoLabels[$m['tipo']] ?? $m['tipo']) ?></span>
                <strong><?= htmlspecialchars($m['asunto']) ?></strong>
                <span class="help help--xs"><?= htmlspecialchars($m['remitente']) ?> · <?= htmlspecialchars(substr((string) $m['created_at'], 0, 16)) ?><?= $m['appointment_id'] ? ' · ' . htmlspecialchars(trim(($m['fecha'] ?: '') . ' ' . ($m['procedimiento'] ?: ''))) : '' ?></span>
            </div>
            <div class="mensaje-cuerpo"><?= nl2br(htmlspecialchars($m['cuerpo'])) ?></div>
        </div>
        <?php endforeach; ?>
    </div>
    <?php else: ?>
    <p class="muted">Sin mensajes todavía.</p>
    <?php endif; ?>
</div>

<?php /* Lo de abajo es el registro crudo: sirve para investigar un caso
         raro o exportar, no para leer al alumno. Se arma solo al pedirlo. */ ?>
<?php if (!$verRegistro): ?>
<div class="card registro-crudo">
    <a href="student.php?id=<?= (int) $studentId ?>&amp;registro=1#registro"><strong>Ver el registro técnico</strong></a>
    <span class="help">ritmo de trabajo, acciones registradas y descargas (<?= $totalActions ?> acciones; se calcula al abrirlo)</span>
</div>
<?php else: ?>
<details class="card registro-crudo" id="registro" open>
    <summary><strong>Registro técnico</strong> <span class="help">ritmo de trabajo, acciones registradas y descargas (<?= $totalActions ?> acciones)</span></summary>

    <div class="section-sep">
        <a href="logs_download.php?id=<?= (int) $studentId ?>">Descargar registro completo (CSV)</a>
        &nbsp;·&nbsp;
        <a href="dashboard_report.php?student_id=<?= (int) $studentId ?>">Descargar informe de sesiones (CSV)</a>
    </div>

    <div class="section-sep">
        <strong>Ritmo de trabajo</strong>
        <div class="table-wrap">
        <table class="table-dense">
            <tr><td>Sesiones (login-logout)</td><td><strong><?= Metrics::countLoginSessions($allLogs) ?></strong></td></tr>
            <tr><td>Pacientes distintos con actividad</td><td><strong><?= Metrics::countAttentions($logsPracticos) ?></strong></td></tr>
            <tr><td>Bloques de actividad</td><td><strong><?= $behaviorStats['n_sessions'] ?></strong></td></tr>
            <tr><td>Duración total</td><td><strong><?= htmlspecialchars(Metrics::formatDurationHms($totalDurationRealS)) ?></strong></td></tr>
            <tr><td>Tiempo promedio entre acciones</td><td><strong><?= isset($behaviorStats['avg_delta_s']) ? htmlspecialchars(Metrics::formatDurationHms((int) round($behaviorStats['avg_delta_s']))) : '—' ?></strong></td></tr>
            <tr><td>Pausas largas (≥30s)</td><td><strong<?= $behaviorStats['long_pauses'] > 0 ? ' class="badge-warn"' : '' ?>><?= $behaviorStats['long_pauses'] ?></strong></td></tr>
            <tr><td>Acciones sin pausa (0s)</td><td><strong><?= $behaviorStats['no_pause_actions'] ?></strong></td></tr>
        </table>
        </div>
        <div class="hist-bar" title="0s: <?= $histogram['0s'] ?? 0 ?> · 1-5s: <?= $histogram['1-5s'] ?? 0 ?> · 6-15s: <?= $histogram['6-15s'] ?? 0 ?> · 16-30s: <?= $histogram['16-30s'] ?? 0 ?> · 30s+: <?= $histogram['30s+'] ?? 0 ?>">
            <?php foreach (['0s' => '#2e7d32', '1-5s' => '#9ccc65', '6-15s' => '#ffb300', '16-30s' => '#fb8c00', '30s+' => '#c0392b'] as $bucket => $color):
                $pct = round((($histogram[$bucket] ?? 0) / $histTotal) * 100, 1);
                if ($pct <= 0) { continue; }
            ?>
            <span style="width:<?= $pct ?>%; background:<?= $color ?>;"></span>
            <?php endforeach; ?>
        </div>
        <p class="legend">Pausas entre acciones: verde (sin pausa) a rojo (pausa ≥30s).</p>
    </div>

    <div class="section-sep">
        <strong>Por semana</strong>
        <div class="table-wrap">
        <table class="table-dense">
            <tr><th>Semana</th><th>Bloques</th><th>Tiempo promedio entre acciones</th></tr>
            <?php $maxSessions = max(array_column($weekly, 'n_sessions') ?: [1]); ?>
            <?php foreach ($weekly as $week => $w): ?>
            <tr>
                <td><?= htmlspecialchars($week) ?></td>
                <td><span class="week-bar" style="width:<?= round(($w['n_sessions'] / $maxSessions) * 100, 1) ?>%;"></span><?= $w['n_sessions'] ?></td>
                <td><?= isset($w['avg_delta_s']) ? htmlspecialchars(Metrics::formatDurationHms((int) round($w['avg_delta_s']))) : '—' ?></td>
            </tr>
            <?php endforeach; ?>
            <?php if (!$weekly): ?>
            <tr><td colspan="3" class="muted">Sin datos suficientes todavía.</td></tr>
            <?php endif; ?>
        </table>
        </div>
    </div>

    <div class="section-sep">
        <strong>Acciones por tipo</strong>
        <div class="table-wrap">
        <table class="table-dense">
            <tr><th>Acción</th><th>Veces</th><th>Última vez</th></tr>
            <?php foreach ($actionCounts as $ac): ?>
            <tr>
                <td><?= htmlspecialchars(Metrics::actionLabel($ac['action'])) ?> <span class="mono" style="font-size:0.75rem; color:var(--color-muted);"><?= htmlspecialchars($ac['action']) ?></span></td>
                <td><?= (int) $ac['n'] ?></td>
                <td><?= htmlspecialchars($ac['last_ts']) ?></td>
            </tr>
            <?php endforeach; ?>
            <?php if (!$actionCounts): ?>
            <tr><td colspan="3" class="muted">Sin acciones registradas todavía.</td></tr>
            <?php endif; ?>
        </table>
        </div>
    </div>

    <div class="section-sep">
        <strong>Últimas 30 acciones</strong>
        <div class="table-wrap">
        <table class="table-dense">
            <tr><th>Cuándo (cliente)</th><th>Acción</th><th>Payload</th></tr>
            <?php foreach ($recentLogs as $log): ?>
            <tr>
                <td class="nowrap"><?= htmlspecialchars($log['client_ts']) ?></td>
                <td><?= htmlspecialchars(Metrics::actionLabel($log['action'])) ?></td>
                <td class="mono" style="font-size:0.75rem;"><?= htmlspecialchars($log['payload'] ?? '') ?></td>
            </tr>
            <?php endforeach; ?>
            <?php if (!$recentLogs): ?>
            <tr><td colspan="3" class="muted">Sin acciones registradas todavía.</td></tr>
            <?php endif; ?>
        </table>
        </div>
    </div>
</details>
<?php endif; ?>
<?php
admin_footer();
