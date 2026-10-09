<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Metrics.php';
require_once __DIR__ . '/../../src/Oirs.php';
require_once __DIR__ . '/../../src/ReportFile.php';
require_once __DIR__ . '/../../src/AlumnoIndicadores.php';
require_once __DIR__ . '/../../src/CourseAvance.php';
require_once __DIR__ . '/../../views/indicadores/tecnica.php';

/**
 * El resumen del alumno logueado (sesión propia, ver sso.php; nunca puede
 * ver a otro): cómo va, en palabras de alumno, y los pacientes que atendió.
 * Lo mismo que el docente ve en admin/student.php, menos lo de gestión.
 *
 * Antes mostraba "bloques", "delta promedio" y "pausas largas", que salen
 * del registro de acciones y no le dicen nada a un alumno (y obligaban a
 * leer ese registro entero en cada visita). Ahora no se lee: la técnica
 * sale guardada (AudiometriaTecnica::deAtenciones).
 */

$me = Auth::requireStudentSession();
$pdo = Db::get();
$uid = (int) $me['id'];

$stmt = $pdo->prepare(
    "SELECT att.id AS attendance_id, att.hora_real, att.updated_at,
            a.id AS appointment_id, a.fecha, a.hora, a.nombre, a.apellido, a.procedimiento,
            " . (Practica::listo() ? 'a.practice_id' : 'NULL') . " AS practice_id
     FROM attendances att
     JOIN appointments a ON a.id = att.appointment_id
     WHERE att.student_id = ? AND att.estado = 'atendido'
     ORDER BY att.updated_at DESC"
);
$stmt->execute([$uid]);
$todas = $stmt->fetchAll();
// Los intentos de práctica libre van en su propia lista (ver Practica).
$attendances = array_values(array_filter($todas, static fn (array $a): bool => $a['practice_id'] === null));
$practicas = array_values(array_filter($todas, static fn (array $a): bool => $a['practice_id'] !== null));

$tecnicas = array_filter(AudiometriaTecnica::deAtenciones($uid, array_map('intval', array_column($todas, 'appointment_id'))));

// Por cita: preguntas al paciente, informes, comentarios del docente y avisos.
$porCita = static function (string $sql, array $args) use ($pdo): array {
    $stmt = $pdo->prepare($sql);
    $stmt->execute($args);
    $out = [];
    foreach ($stmt->fetchAll() as $r) {
        $out[(int) $r['k']][] = $r;
    }
    return $out;
};
$preguntas = array_map(static fn (array $f): int => (int) $f[0]['n'], $porCita(
    "SELECT appointment_id AS k, COUNT(*) AS n FROM llm_chat_logs WHERE student_id = ? AND role = 'user' GROUP BY appointment_id", [$uid]
));
$informes = $porCita(
    'SELECT att.appointment_id AS k, r.id, r.tipo FROM reports r JOIN attendances att ON att.id = r.attendance_id
      WHERE att.student_id = ? ORDER BY r.tipo', [$uid]
);
$comentariosChat = $porCita(
    'SELECT l.appointment_id AS k, COUNT(*) AS n FROM chat_comments c JOIN llm_chat_logs l ON l.id = c.chat_log_id
      WHERE l.student_id = ? GROUP BY l.appointment_id', [$uid]
);
$comentariosAtencion = $porCita(
    'SELECT att.appointment_id AS k, COUNT(*) AS n FROM attendance_comments ac JOIN attendances att ON att.id = ac.attendance_id
      WHERE att.student_id = ? GROUP BY att.appointment_id', [$uid]
);
Oirs::normalizarGuardados($pdo);
$avisos = $porCita(
    "SELECT appointment_id AS k, tipo FROM inbox_messages WHERE student_id = ? AND appointment_id IS NOT NULL AND tipo IN ('merito', 'reclamo')", [$uid]
);
$comentariosDe = static function (int $ap) use ($comentariosChat, $comentariosAtencion): int {
    return (int) ($comentariosChat[$ap][0]['n'] ?? 0) + (int) ($comentariosAtencion[$ap][0]['n'] ?? 0);
};

// Indicadores de arriba (solo prácticos, salvo la técnica: la práctica
// libre también es audiometría y cuenta para ver si mejora).
$serie = [];
foreach (array_reverse($todas) as $a) {
    $ap = (int) $a['appointment_id'];
    if (isset($tecnicas[$ap]) && $tecnicas[$ap]['puntaje']['pct'] !== null) {
        $serie[] = [
            'pct' => (int) $tecnicas[$ap]['puntaje']['pct'],
            'fecha' => (string) ($a['fecha'] ?: substr((string) $a['updated_at'], 0, 10)),
            'paciente' => trim("{$a['nombre']} {$a['apellido']}"),
            'practica' => $a['practice_id'] !== null,
            'href' => 'atencion.php?appointment_id=' . $ap . '#tecnica',
        ];
    }
}
$pcts = array_column($serie, 'pct');
$tecnicaPromedio = AlumnoIndicadores::promedio($pcts);
$tendencia = AlumnoIndicadores::tendencia($pcts);
$pasos = array_slice(AlumnoIndicadores::pasosDificiles(array_values($tecnicas)), 0, 5);
$duraciones = [];
foreach ($attendances as $a) {
    $d = Metrics::attendanceDurationSeconds($a['hora_real'], $a['updated_at']);
    if ($d !== null && $d <= CourseAvance::DURACION_MAX_S) {
        $duraciones[] = $d;
    }
}
$preguntasPracticos = [];
foreach ($attendances as $a) {
    if (isset($preguntas[(int) $a['appointment_id']])) {
        $preguntasPracticos[] = $preguntas[(int) $a['appointment_id']];
    }
}
$informesPorTipo = [];
foreach ($informes as $lista) {
    foreach ($lista as $r) {
        $informesPorTipo[$r['tipo']] = ($informesPorTipo[$r['tipo']] ?? 0) + 1;
    }
}
arsort($informesPorTipo);
$totalComentarios = 0;
$conComentarios = 0;
foreach ($todas as $a) {
    $n = $comentariosDe((int) $a['appointment_id']);
    $totalComentarios += $n;
    $conComentarios += $n > 0 ? 1 : 0;
}

// Objetivos de sus cursos: los que el docente escribió, con su avance.
$objetivosCursos = [];
$stmt = $pdo->prepare('SELECT c.id, c.name FROM courses c JOIN course_students cs ON cs.course_id = c.id WHERE cs.user_id = ? AND c.active = 1 ORDER BY c.name');
$stmt->execute([$uid]);
foreach ($stmt->fetchAll() as $curso) {
    try {
        $objs = CourseAvance::objetivos((int) $curso['id']);
    } catch (PDOException $e) {
        $objs = [];   // antes de aplicar schema.sql
    }
    if (!$objs) {
        continue;
    }
    $yo = CourseAvance::porAlumno((int) $curso['id'])[$uid] ?? null;
    $objetivosCursos[] = ['nombre' => $curso['name'], 'objetivos' => $objs, 'yo' => $yo];
}
$indicadores = CourseAvance::indicadores();

student_header('Mis pacientes', $me);

/** Lista de atenciones cerradas (prácticos o intentos de práctica). */
$lista = static function (array $filas) use ($tecnicas, $preguntas, $informes, $avisos, $comentariosDe): void {
    ?>
    <div class="atenciones">
        <?php foreach ($filas as $a):
            $ap = (int) $a['appointment_id'];
            $duracionS = Metrics::attendanceDurationSeconds($a['hora_real'], $a['updated_at']);
            $tec = $tecnicas[$ap]['puntaje'] ?? null;
            $nComentarios = $comentariosDe($ap);
        ?>
        <a class="atencion" href="atencion.php?appointment_id=<?= $ap ?>">
            <span class="atencion-cabeza">
                <span class="atencion-paciente"><?= htmlspecialchars(trim("{$a['nombre']} {$a['apellido']}")) ?: 'Paciente sin nombre' ?></span>
                <span class="atencion-fecha"><?= htmlspecialchars($a['fecha'] ?: substr((string) $a['updated_at'], 0, 10)) ?></span>
            </span>
            <span class="atencion-proc"><?= htmlspecialchars($a['procedimiento'] ?: '—') ?></span>
            <span class="atencion-datos">
                <?php if ($duracionS !== null): ?><span class="dato" title="Desde que apretaste Atender hasta que cerraste">⏱ <?= htmlspecialchars(AlumnoIndicadores::minutos($duracionS)) ?></span><?php endif; ?>
                <?php if (isset($preguntas[$ap])): ?><span class="dato" title="Preguntas que le hiciste al paciente">💬 <?= $preguntas[$ap] ?> pregunta<?= $preguntas[$ap] === 1 ? '' : 's' ?></span><?php endif; ?>
                <?php if ($tec !== null && $tec['pct'] !== null): ?><span class="dato dato--fuerte" style="color:<?= AudiometriaTecnicaVista::color($tec['pct']) ?>;" title="<?= (int) $tec['cumple'] ?> de <?= (int) $tec['total'] ?> pasos de la técnica">Técnica <?= (int) $tec['pct'] ?> %</span><?php endif; ?>
                <?php foreach ($informes[$ap] ?? [] as $r): ?><span class="tag"><?= htmlspecialchars(ReportFile::SHORT_LABELS[$r['tipo']] ?? $r['tipo']) ?></span><?php endforeach; ?>
                <?php if ($nComentarios > 0): ?><span class="tag tag--info">Tu docente comentó (<?= $nComentarios ?>)</span><?php endif; ?>
                <?php foreach ($avisos[$ap] ?? [] as $m): ?>
                <span class="tag <?= $m['tipo'] === 'merito' ? 'tag--success' : 'tag--warn' ?>"><?= htmlspecialchars(Oirs::label((string) $m['tipo'])) ?></span>
                <?php endforeach; ?>
            </span>
        </a>
        <?php endforeach; ?>
    </div>
    <?php
};
?>
<h1>Cómo vas</h1>
<div class="kpis">
    <div class="kpi">
        <div class="kpi-valor"><?= count($attendances) ?></div>
        <div class="kpi-nombre">Pacientes atendidos</div>
        <div class="kpi-pie"><?= $practicas ? '+ ' . count($practicas) . ' de práctica libre' : 'en los prácticos' ?></div>
    </div>
    <div class="kpi">
        <div class="kpi-valor" style="color:<?= AudiometriaTecnicaVista::color($tecnicaPromedio) ?>;"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($tecnicaPromedio)) ?></div>
        <div class="kpi-nombre">Tu técnica de audiometría</div>
        <div class="kpi-pie">
            <?php if ($tendencia !== null && $tendencia !== 0): ?>
            <span class="<?= $tendencia > 0 ? 'kpi-sube' : 'kpi-baja' ?>"><?= $tendencia > 0 ? '▲ subiste ' . $tendencia : '▼ bajaste ' . abs($tendencia) ?> puntos</span> desde tus primeras audiometrías
            <?php elseif ($pcts): ?>
            pasos de la técnica que cumpliste, en promedio
            <?php else: ?>
            cuando hagas una audiometría aparece acá
            <?php endif; ?>
        </div>
    </div>
    <div class="kpi">
        <div class="kpi-valor"><?= htmlspecialchars(AlumnoIndicadores::minutos(AlumnoIndicadores::mediana($duraciones))) ?></div>
        <div class="kpi-nombre">Tiempo por paciente</div>
        <div class="kpi-pie">lo que te demoras normalmente, de Atender a cerrar</div>
    </div>
    <div class="kpi">
        <div class="kpi-valor"><?= AlumnoIndicadores::mediana($preguntasPracticos) ?? '—' ?></div>
        <div class="kpi-nombre">Preguntas al paciente</div>
        <div class="kpi-pie">las que haces normalmente en la anamnesis</div>
    </div>
    <div class="kpi">
        <div class="kpi-valor"><?= array_sum($informesPorTipo) ?></div>
        <div class="kpi-nombre">Informes entregados</div>
        <div class="kpi-pie">
            <?php foreach ($informesPorTipo as $tipo => $n): ?><span class="tag"><?= htmlspecialchars(ReportFile::SHORT_LABELS[$tipo] ?? $tipo) ?> <?= $n ?></span><?php endforeach; ?>
            <?php if (!$informesPorTipo): ?>ninguno todavía<?php endif; ?>
        </div>
    </div>
    <div class="kpi">
        <div class="kpi-valor"><?= $totalComentarios ?></div>
        <div class="kpi-nombre">Comentarios de tu docente</div>
        <div class="kpi-pie"><?= $conComentarios ? 'en ' . $conComentarios . ' atención(es): ábrelas para leerlos' : 'todavía ninguno' ?></div>
    </div>
</div>

<?php foreach ($objetivosCursos as $oc): ?>
<div class="card">
    <h2>Objetivos de <?= htmlspecialchars($oc['nombre']) ?></h2>
    <ul class="mis-objetivos">
        <?php foreach ($oc['objetivos'] as $o): ?>
        <?php
        $medido = $o['indicador'] !== '' && isset($indicadores[$o['indicador']]);
        $valor = $medido && $oc['yo'] ? ($oc['yo'][$o['indicador']] ?? null) : null;
        $c = $medido ? CourseAvance::cumple($o['indicador'], $valor, $o['meta']) : null;
        ?>
        <li class="mi-objetivo<?= $c === true ? ' mi-objetivo--si' : '' ?>">
            <span class="mi-objetivo-marca"><?= $c === true ? '✓' : ($c === false ? '○' : '·') ?></span>
            <span>
                <span class="mi-objetivo-texto"><?= htmlspecialchars($o['texto']) ?></span>
                <?php if ($medido): ?>
                <span class="legend">
                    <?= htmlspecialchars($indicadores[$o['indicador']]['label']) ?> <?= htmlspecialchars(CourseAvance::metaTexto($o['indicador'], $o['meta'])) ?>
                    · <?php if ($valor === null): ?>todavía sin datos<?php else: ?>llevas <?= htmlspecialchars((string) $valor) ?><?= $indicadores[$o['indicador']]['unidad'] !== '' ? ' ' . htmlspecialchars($indicadores[$o['indicador']]['unidad']) : '' ?><?= $c ? ' — logrado' : '' ?><?php endif; ?>
                </span>
                <?php endif; ?>
            </span>
        </li>
        <?php endforeach; ?>
    </ul>
</div>
<?php endforeach; ?>

<?php if ($serie): ?>
<div class="card">
    <h2>Tu técnica de audiometría, atención por atención</h2>
    <p class="legend">Cada punto es una audiometría: verde desde 85 %, ámbar desde 60 %. Los huecos son de práctica libre. Pincha un punto para ver qué pasos cumpliste.</p>
    <?php indicadores_tecnica_grafico($serie); ?>
    <?php if ($pasos): ?>
    <h2 style="margin-top:var(--space-6);">En qué fijarte</h2>
    <p class="legend">Los pasos de la técnica que más se te pasan, y en cuántas audiometrías.</p>
    <?php indicadores_pasos($pasos); ?>
    <?php else: ?>
    <p class="legend" style="margin-top:var(--space-4);">Cumpliste todos los pasos que se pudieron revisar. ¡Bien!</p>
    <?php endif; ?>
</div>
<?php endif; ?>

<h1>Pacientes que has atendido (<?= count($attendances) ?>)</h1>
<?php if (!$attendances): ?>
<div class="card"><p class="empty">Todavía no has cerrado ninguna atención.</p></div>
<?php else: ?>
<p class="legend">Pincha un paciente para ver el detalle: tu conversación con él (con los comentarios de tu docente, si dejó alguno), los pasos de tu técnica y la ficha clínica.</p>
<?php $lista($attendances); ?>
<?php endif; ?>

<?php if ($practicas): ?>
<h1>Práctica libre (<?= count($practicas) ?> intento<?= count($practicas) === 1 ? '' : 's' ?>)</h1>
<p class="legend">Cada vez que abres un paciente de práctica queda como un intento aparte.</p>
<?php $lista($practicas); ?>
<?php endif; ?>
<?php
student_footer();
