<?php
/**
 * Pestaña Avance: cómo va el curso. Cifras del curso, objetivos de
 * aprendizaje (texto del docente, opcionalmente atado a un indicador con
 * meta), quién necesita atención, lo que más le cuesta al curso, la marcha
 * por semana y la tabla de alumnos. Cálculo en CourseAvance.
 *
 * Espera: $courseId, $objetivos, $faltaSchema, $avanceAlumnos,
 *         $avanceSemanas, $pasosCurso, $necesitan, $agendaAvance,
 *         $estadisticas (CursoEstadisticas::calcular).
 */
$indicadores = CourseAvance::indicadores();
$nAlumnos = count($avanceAlumnos);
$conActividad = count(array_filter($avanceAlumnos, static fn(array $a): bool => $a['atenciones'] > 0));
$atencionesCurso = array_sum(array_column($avanceAlumnos, 'atenciones'));
$informesCurso = array_sum(array_column($avanceAlumnos, 'informes'));
$practicaCurso = array_sum(array_column($avanceAlumnos, 'practica'));
$promedios = array_values(array_filter(array_column($avanceAlumnos, 'tecnica_promedio'), static fn($v): bool => $v !== null));
$tecnicaCurso = AlumnoIndicadores::promedio($promedios);
// Tendencia del curso: todas las audiometrías en orden de fecha.
$todas = [];
foreach ($avanceAlumnos as $al) {
    foreach ($al['serie'] as $p) {
        $todas[] = $p;
    }
}
usort($todas, static fn(array $a, array $b): int => $a[0] <=> $b[0]);
$tendenciaCurso = AlumnoIndicadores::tendencia(array_column($todas, 1));
$duracionesCurso = array_merge([], ...array_values(array_column($avanceAlumnos, 'duraciones')));
$duracionPromedio = AlumnoIndicadores::promedio($duracionesCurso);
$duracionMediana = AlumnoIndicadores::mediana($duracionesCurso);
// Tendencia de la duración: las primeras atenciones del curso contra las últimas.
$durSemanas = array_values(array_filter(array_column($avanceSemanas, 'duracion_s'), static fn($v): bool => $v !== null));
$durTendencia = count($durSemanas) >= 2 ? AlumnoIndicadores::tendencia($durSemanas) : null;
$medidos = array_values(array_filter($objetivos, static fn(array $o): bool => $o['indicador'] !== ''));
$cumplenTotal = array_sum(array_column($medidos, 'cumplen'));
$evaluadosTotal = $cumplenTotal + array_sum(array_column($medidos, 'no_cumplen'));
$pctObjetivos = $evaluadosTotal > 0 ? (int) round(100 * $cumplenTotal / $evaluadosTotal) : null;

/** <select> de indicadores, con el elegido marcado. */
$selectIndicador = static function (string $elegido) use ($indicadores): void {
    ?>
    <select name="indicador" class="select">
        <option value="">Sin medición automática</option>
        <?php foreach ($indicadores as $k => $def): ?>
        <option value="<?= htmlspecialchars($k) ?>"<?= $k === $elegido ? ' selected' : '' ?>><?= htmlspecialchars($def['label']) ?> (<?= $def['comparar'] === '<=' ? 'máximo' : 'mínimo' ?><?= $def['unidad'] !== '' ? ', ' . $def['unidad'] : '' ?>)</option>
        <?php endforeach; ?>
    </select>
    <?php
};
?>
<?php if ($faltaSchema): ?>
<p class="error">Falta la tabla de objetivos: un admin completo tiene que ir a Base de datos y aplicar schema.sql. El resto de la pestaña funciona igual.</p>
<?php endif; ?>

<div class="kpis-curso">
    <div class="kpi-c">
        <div class="kpi-c-valor"><?= $conActividad ?><span class="kpi-c-de"> / <?= $nAlumnos ?></span></div>
        <div class="kpi-c-nombre">Alumnos con atenciones</div>
    </div>
    <div class="kpi-c">
        <div class="kpi-c-valor"><?= $atencionesCurso ?></div>
        <div class="kpi-c-nombre">Atenciones cerradas</div>
        <div class="kpi-c-pie"><?= $practicaCurso ?> intento(s) de práctica libre aparte</div>
    </div>
    <div class="kpi-c">
        <div class="kpi-c-valor"><?= htmlspecialchars(AlumnoIndicadores::minutos($duracionPromedio)) ?></div>
        <div class="kpi-c-nombre">Duración promedio de una atención</div>
        <div class="kpi-c-pie">
            <?php if ($durTendencia !== null && abs($durTendencia) >= 60): ?>
            <span class="<?= $durTendencia < 0 ? 'kpi-sube' : 'kpi-baja' ?>"><?= $durTendencia < 0 ? '▼ ' : '▲ +' ?><?= htmlspecialchars(AlumnoIndicadores::minutos(abs($durTendencia))) ?></span>
            de las primeras semanas a las últimas<br>
            <?php endif; ?>
            <span title="No cuenta las atenciones de más de <?= intdiv(CourseAvance::DURACION_MAX_S, 3600) ?> h: quedaron abiertas y no dicen cuánto demoró el alumno">mediana <?= htmlspecialchars(AlumnoIndicadores::minutos($duracionMediana)) ?> · <?= count($duracionesCurso) ?> atención(es)</span>
        </div>
    </div>
    <div class="kpi-c">
        <div class="kpi-c-valor" style="color:<?= AudiometriaTecnicaVista::color($tecnicaCurso) ?>;"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($tecnicaCurso)) ?></div>
        <div class="kpi-c-nombre">Técnica de audiometría</div>
        <div class="kpi-c-pie">
            <?php if ($tendenciaCurso !== null): ?>
            <span class="<?= $tendenciaCurso > 0 ? 'kpi-sube' : ($tendenciaCurso < 0 ? 'kpi-baja' : '') ?>"><?= $tendenciaCurso > 0 ? '▲ +' : ($tendenciaCurso < 0 ? '▼ ' : '= ') ?><?= $tendenciaCurso ?> pts</span>
            de las primeras a las últimas <?= count($todas) ?>
            <?php else: ?>
            promedio de los alumnos
            <?php endif; ?>
        </div>
    </div>
    <div class="kpi-c">
        <div class="kpi-c-valor"><?= $informesCurso ?></div>
        <div class="kpi-c-nombre">Informes entregados</div>
    </div>
    <div class="kpi-c">
        <div class="kpi-c-valor"><?= $pctObjetivos !== null ? $pctObjetivos . ' %' : '—' ?></div>
        <div class="kpi-c-nombre">Objetivos cumplidos</div>
        <div class="kpi-c-pie"><?= $medidos ? 'de los alumnos con datos, en ' . count($medidos) . ' objetivo(s) medido(s)' : 'sin objetivos medidos todavía' ?></div>
    </div>
</div>

<div class="card">
    <strong>Objetivos de aprendizaje</strong>
    <p class="help help--mt">
        El texto lo escribe el docente. Si se elige un indicador y una meta, se cuenta qué alumnos la alcanzan con lo que ya
        registra la app en este curso; un alumno sin datos para ese indicador todavía no cuenta ni a favor ni en contra.
        Sin indicador, el objetivo solo se lista.
    </p>

    <?php if ($objetivos): ?>
    <ol class="objetivos">
        <?php foreach ($objetivos as $i => $o): ?>
        <?php $evaluados = $o['cumplen'] + $o['no_cumplen']; $pct = $evaluados > 0 ? (int) round(100 * $o['cumplen'] / $evaluados) : null; ?>
        <li class="objetivo">
            <div class="objetivo-cabeza">
                <span class="objetivo-texto"><?= htmlspecialchars($o['texto']) ?></span>
                <span class="objetivo-acciones">
                    <form method="post" class="inline">
                    <?= csrf_field() ?>
                        <input type="hidden" name="form_action" value="objective_move">
                        <input type="hidden" name="course_id" value="<?= $courseId ?>">
                        <input type="hidden" name="objective_id" value="<?= (int) $o['id'] ?>">
                        <button type="submit" name="dir" value="up" class="btn btn--ghost btn--xs" title="Subir"<?= $i === 0 ? ' disabled' : '' ?>>▲</button>
                        <button type="submit" name="dir" value="down" class="btn btn--ghost btn--xs" title="Bajar"<?= $i === count($objetivos) - 1 ? ' disabled' : '' ?>>▼</button>
                    </form>
                    <details class="row-menu objetivo-editar">
                        <summary class="btn btn--ghost btn--xs" title="Editar">✎</summary>
                        <div class="objetivo-panel">
                            <form method="post" class="objetivo-form">
                            <?= csrf_field() ?>
                                <input type="hidden" name="course_id" value="<?= $courseId ?>">
                                <input type="hidden" name="objective_id" value="<?= (int) $o['id'] ?>">
                                <label class="field-label">Objetivo
                                    <textarea name="texto" class="textarea objetivo-textarea" rows="2" required><?= htmlspecialchars($o['texto']) ?></textarea>
                                </label>
                                <label class="field-label">Se mide con <?php $selectIndicador((string) $o['indicador']); ?></label>
                                <label class="field-label">Meta
                                    <input type="text" inputmode="decimal" name="meta" class="input input--narrow" value="<?= $o['meta'] !== null ? htmlspecialchars(rtrim(rtrim((string) $o['meta'], '0'), '.')) : '' ?>">
                                </label>
                                <div class="row">
                                    <button type="submit" name="form_action" value="objective_edit" class="btn btn--sm">Guardar</button>
                                    <button type="submit" name="form_action" value="objective_delete" class="btn btn--danger btn--sm"
                                            onclick="return confirm('¿Eliminar este objetivo?');">Eliminar</button>
                                </div>
                            </form>
                        </div>
                    </details>
                </span>
            </div>
            <?php if ($o['indicador'] !== '' && isset($indicadores[$o['indicador']])): ?>
            <div class="objetivo-medida">
                <span class="tag"><?= htmlspecialchars($indicadores[$o['indicador']]['label']) ?> <?= htmlspecialchars(CourseAvance::metaTexto($o['indicador'], $o['meta'])) ?></span>
                <span class="objetivo-barra" title="<?= $o['cumplen'] ?> cumplen · <?= $o['no_cumplen'] ?> no · <?= $o['sin_datos'] ?> sin datos">
                    <span class="objetivo-barra-si" style="width:<?= $nAlumnos ? round(100 * $o['cumplen'] / $nAlumnos, 1) : 0 ?>%;"></span><span class="objetivo-barra-no" style="width:<?= $nAlumnos ? round(100 * $o['no_cumplen'] / $nAlumnos, 1) : 0 ?>%;"></span>
                </span>
                <span class="objetivo-cuenta">
                    <strong><?= $o['cumplen'] ?></strong> de <?= $evaluados ?> con datos<?= $pct !== null ? " ({$pct} %)" : '' ?><?= $o['sin_datos'] ? ' · ' . $o['sin_datos'] . ' sin datos' : '' ?>
                </span>
            </div>
            <?php else: ?>
            <div class="objetivo-medida"><span class="help help--xs">Sin medición automática.</span></div>
            <?php endif; ?>
        </li>
        <?php endforeach; ?>
    </ol>
    <?php elseif (!$faltaSchema): ?>
    <p class="muted">Este curso todavía no tiene objetivos.</p>
    <?php endif; ?>

    <?php if (!$faltaSchema): ?>
    <details class="section-sep objetivo-nuevo"<?= $objetivos ? '' : ' open' ?>>
        <summary><strong>+ Agregar objetivo</strong></summary>
        <form method="post" class="objetivo-form objetivo-form--linea">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="objective_add">
            <input type="hidden" name="course_id" value="<?= $courseId ?>">
            <label class="field-label objetivo-campo-texto">Objetivo
                <input type="text" name="texto" class="input" maxlength="500" required>
            </label>
            <label class="field-label">Se mide con <?php $selectIndicador(''); ?></label>
            <label class="field-label">Meta
                <input type="text" inputmode="decimal" name="meta" class="input input--narrow">
            </label>
            <button type="submit" class="btn btn--sm">Agregar</button>
        </form>
    </details>
    <?php endif; ?>
</div>

<div class="avance-columnas">
    <div class="card">
        <strong>Necesitan atención (<?= count($necesitan) ?>)</strong>
        <p class="help help--xs">Sin atenciones cerradas, sin cerrar una hace <?= CourseAvance::DIAS_SIN_ACTIVIDAD ?> días o más, técnica bajo 60 % o bajando 10 puntos o más.</p>
        <?php if ($necesitan): ?>
        <ul class="avance-lista">
            <?php foreach ($necesitan as $uid => $n): ?>
            <li>
                <a href="student.php?id=<?= (int) $uid ?>"><?= htmlspecialchars($n['nombre']) ?></a>
                <?php foreach ($n['motivos'] as $m): ?><span class="tag tag--warn"><?= htmlspecialchars($m) ?></span><?php endforeach; ?>
            </li>
            <?php endforeach; ?>
        </ul>
        <?php else: ?>
        <p class="muted">Nadie por ahora.</p>
        <?php endif; ?>
    </div>

    <div class="card">
        <strong>Lo que más le cuesta al curso</strong>
        <p class="help help--xs">Pasos de la técnica de audiometría que cada alumno no cumplió en la mayoría de sus audiometrías.</p>
        <?php if ($pasosCurso): ?>
        <div class="pasos-curso">
            <?php foreach ($pasosCurso as $p): ?>
            <?php $pct = (int) round(100 * $p['alumnos'] / $p['evaluados']); ?>
            <div class="paso-curso">
                <div class="paso-curso-texto"><span class="tag tag--muted"><?= htmlspecialchars($p['seccion']) ?></span> <?= htmlspecialchars($p['texto']) ?></div>
                <div class="paso-curso-pie">
                    <span class="paso-barra"><span style="width:<?= $pct ?>%;"></span></span>
                    <span class="help help--xs"><?= $p['alumnos'] ?> de <?= $p['evaluados'] ?> alumnos</span>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
        <?php else: ?>
        <p class="muted"><?= $todas ? 'Ningún paso se le escapa a la mayoría de un alumno.' : 'Todavía no hay audiometrías en este curso.' ?></p>
        <?php endif; ?>
    </div>
</div>

<?php if (!empty($estadisticas['n'])): ?>
<?php
$ek = $estadisticas['kpis'];
$secT = ['orden' => 'Orden', 'pertinencia' => 'Pertinencia', 'aereos' => 'Aéreos', 'oseos' => 'Óseos', 'enmascaramiento' => 'Enmasc.', 'tinnitus' => 'Tinnit.'];
$pctCelda = static function (?int $v): string {
    return '<td class="est-num" style="color:' . AudiometriaTecnicaVista::color($v) . ';">' . htmlspecialchars(AudiometriaTecnicaVista::pct($v)) . '</td>';
};
$fraccion = static function (array $f): string {
    return $f[1] > 0 ? (int) $f[0] . '/' . (int) $f[1] : '—';
};
$meses = ['01' => 'enero', '02' => 'febrero', '03' => 'marzo', '04' => 'abril', '05' => 'mayo', '06' => 'junio', '07' => 'julio',
    '08' => 'agosto', '09' => 'septiembre', '10' => 'octubre', '11' => 'noviembre', '12' => 'diciembre'];
?>
<div class="card">
    <strong>Audiometría del curso</strong>
    <p class="help help--xs"><?= (int) $estadisticas['n'] ?> audiometrías de prácticos (sin práctica libre). Logro ponderado: cada paso pesa según su gravedad y descuenta en proporción a cuánto se falló.</p>
    <div class="kpis-curso">
        <div class="kpi-c"><div class="kpi-c-valor" style="color:<?= AudiometriaTecnicaVista::color($ek['logro']) ?>;"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($ek['logro'])) ?></div><div class="kpi-c-nombre">Logro de la técnica</div></div>
        <div class="kpi-c"><div class="kpi-c-valor"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($ek['a_5db'])) ?></div><div class="kpi-c-nombre">Umbrales aéreos a ±5 dB del real</div></div>
        <div class="kpi-c"><div class="kpi-c-valor"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($ek['verificacion'])) ?></div><div class="kpi-c-nombre">Frecuencias cerradas con 2 de 3</div></div>
        <div class="kpi-c"><div class="kpi-c-valor"><?= $ek['duracion_mediana'] === null ? '—' : htmlspecialchars(number_format($ek['duracion_mediana'], 2, ',', '')) . ' s' ?></div><div class="kpi-c-nombre">Duración típica del estímulo<?= $ek['bajo_1s'] !== null ? ' (' . (int) $ek['bajo_1s'] . ' % bajo 1 s)' : '' ?></div></div>
    </div>

    <?php if ($estadisticas['recomendaciones']): ?>
    <div style="margin-top:0.8rem;"><strong>Recomendaciones para los docentes</strong></div>
    <p class="help help--xs">Salen de los datos: cada una aparece cuando el curso queda bajo su corte (verificar 2 de 3 bajo <?= CursoEstadisticas::CORTES['verificacion'] ?> %, óseos tomados bajo <?= CursoEstadisticas::CORTES['oseos'] ?> %, enmascaramiento bajo <?= CursoEstadisticas::CORTES['enmascaramiento'] ?> %, adaptación bajo <?= CursoEstadisticas::CORTES['adaptacion'] ?> %, estímulo bajo 1 s, orden bajo <?= CursoEstadisticas::CORTES['orden'] ?> %, tinnitumetría bajo <?= CursoEstadisticas::CORTES['tinnitus'] ?> %).</p>
    <ol class="recomendaciones">
        <?php foreach ($estadisticas['recomendaciones'] as $r): ?>
        <li style="margin:0 0 0.6rem;">
            <strong><?= htmlspecialchars($r['titulo']) ?>.</strong> <?= htmlspecialchars($r['evidencia']) ?>
            <div><strong>Qué hacer:</strong> <?= htmlspecialchars($r['accion']) ?></div>
            <?php if ($r['alumnos']): ?>
            <div class="help help--xs">Mirar en particular<?= $r['alumnos_motivo'] !== '' ? ' (' . htmlspecialchars($r['alumnos_motivo']) . ')' : '' ?>:
                <?php foreach ($r['alumnos'] as $n): ?><span class="tag tag--muted"><?= htmlspecialchars($n) ?></span> <?php endforeach; ?></div>
            <?php endif; ?>
        </li>
        <?php endforeach; ?>
    </ol>
    <?php endif; ?>

    <details style="margin-top:0.6rem;">
        <summary><strong>Por alumno</strong> <span class="help help--xs">conductas clave</span></summary>
        <p class="help help--xs">2 de 3: frecuencias aéreas verificadas. ±5 dB: umbrales aéreos (verificados o no) cerca del real. Óseos, adaptación: hechas sobre las atenciones que las pedían. Enmasc.: parte de los umbrales que pedían ruido y lo tuvieron. Tend.: segunda mitad de sus atenciones menos la primera.</p>
        <div class="table-wrap">
        <table class="table-dense">
            <tr><th>Alumno</th><th class="est-num">Atenc.</th><th class="est-num">Logro</th><th class="est-num">Tend.</th><th class="est-num">2 de 3</th><th class="est-num">±5 dB</th><th class="est-num">Estímulo</th><th class="est-num">Óseos</th><th class="est-num">Adapt.</th><th class="est-num">Enmasc.</th><th class="est-num">Logo</th></tr>
            <?php foreach ($estadisticas['alumnos'] as $uid => $a): ?>
            <tr>
                <td><a href="student.php?id=<?= (int) $uid ?>"><?= htmlspecialchars($a['nombre']) ?></a></td>
                <td class="est-num"><?= (int) $a['n'] ?></td>
                <?= $pctCelda($a['logro']) ?>
                <td class="est-num"<?= $a['tendencia'] !== null && $a['tendencia'] <= -10 ? ' style="color:#c0392b;"' : '' ?>><?= $a['tendencia'] === null ? '—' : sprintf('%+d', $a['tendencia']) ?></td>
                <td class="est-num"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($a['verificacion'])) ?></td>
                <td class="est-num"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($a['a_5db'])) ?></td>
                <td class="est-num nowrap"><?= $a['duracion_mediana'] === null ? '—' : htmlspecialchars(number_format($a['duracion_mediana'], 2, ',', '')) . ' s' ?></td>
                <td class="est-num"><?= $fraccion($a['oseos']) ?></td>
                <td class="est-num"><?= $fraccion($a['adaptacion']) ?></td>
                <td class="est-num"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($a['enmascaramiento'])) ?></td>
                <td class="est-num"><?= $fraccion($a['logo']) ?></td>
            </tr>
            <?php endforeach; ?>
        </table>
        </div>
    </details>

    <details style="margin-top:0.4rem;">
        <summary><strong>Por paciente</strong> <span class="help help--xs">qué caso costó más</span></summary>
        <div class="table-wrap">
        <table class="table-dense">
            <tr><th>Fecha</th><th>Paciente</th><th class="est-num">Atenc.</th><th class="est-num">Logro</th><?php foreach ($secT as $t): ?><th class="est-num"><?= $t ?></th><?php endforeach; ?></tr>
            <?php foreach ($estadisticas['pacientes'] as $p): ?>
            <tr>
                <td class="nowrap"><?= htmlspecialchars(CursoEstadisticas::fechaCorta($p['fecha'])) ?></td>
                <td><?= htmlspecialchars((string) $p['paciente']) ?></td>
                <td class="est-num"><?= (int) $p['n'] ?></td>
                <?= $pctCelda($p['logro']) ?>
                <?php foreach (array_keys($secT) as $k): ?><?= $pctCelda($p['secciones'][$k] ?? null) ?><?php endforeach; ?>
            </tr>
            <?php endforeach; ?>
        </table>
        </div>
    </details>

    <details style="margin-top:0.4rem;">
        <summary><strong>Por mes</strong></summary>
        <div class="table-wrap">
        <table class="table-dense">
            <tr><th>Mes</th><th class="est-num">Atenc.</th><th class="est-num">Logro</th><?php foreach ($secT as $t): ?><th class="est-num"><?= $t ?></th><?php endforeach; ?></tr>
            <?php foreach ($estadisticas['meses'] as $mes => $m): ?>
            <tr>
                <td><?= htmlspecialchars(ucfirst($meses[substr((string) $mes, 5, 2)] ?? (string) $mes)) ?> <?= htmlspecialchars(substr((string) $mes, 0, 4)) ?></td>
                <td class="est-num"><?= (int) $m['n'] ?></td>
                <?= $pctCelda($m['logro']) ?>
                <?php foreach (array_keys($secT) as $k): ?><?= $pctCelda($m['secciones'][$k] ?? null) ?><?php endforeach; ?>
            </tr>
            <?php endforeach; ?>
        </table>
        </div>
    </details>
</div>
<?php endif; ?>

<?php if (!empty($agendaAvance['hay'])): ?>
<div class="card">
    <strong>Agenda con duración</strong>
    <p class="help help--xs">Solo citas con duración. <strong>Atraso al iniciar</strong>: hora en que el alumno abrió la atención menos el inicio de su turno (mediana; negativo = antes). <strong>Box pasado</strong>: cuánto después del fin de su bloque cerró su última atención de cada día (mediana; 0 = terminó a tiempo). Sin el registro de turnos de la app de ese día no hay atraso ni box. <strong>Horario libre</strong>: lo que dejó para después (continuaciones que pidió y pacientes que no atendió en su día) y cómo terminó: a tiempo (antes de su práctico siguiente), fuera de plazo, vencido sin atender o abierto todavía.</p>
    <div class="table-wrap">
    <table class="grid-table">
        <tr><th>Alumno</th><th>Días</th><th>Atraso al iniciar</th><th>Box pasado</th><th>Libre a tiempo</th><th>Fuera de plazo</th><th>Vencidos</th><th>Abiertos</th></tr>
        <?php foreach ($agendaAvance['alumnos'] as $uid => $g): ?>
        <tr>
            <td><a href="student.php?id=<?= (int) $uid ?>"><?= htmlspecialchars($g['nombre']) ?></a></td>
            <td><?= (int) $g['dias'] ?></td>
            <td><?= $g['atraso_min'] === null ? '—' : (int) $g['atraso_min'] . ' min' ?></td>
            <td><?= $g['box_min'] === null ? '—' : (int) $g['box_min'] . ' min' ?></td>
            <td><?= (int) $g['libre']['a_tiempo'] ?></td>
            <td><?= (int) $g['libre']['fuera_de_plazo'] ?: '' ?></td>
            <td><?= $g['libre']['vencido'] ? '<span class="tag tag--warn">' . (int) $g['libre']['vencido'] . '</span>' : '' ?></td>
            <td><?= (int) $g['libre']['abierto'] ?: '' ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php if ($agendaAvance['pacientes']): ?>
    <p class="help help--xs" style="margin-top:0.8rem;">Por paciente: la duración que se le dio contra lo que realmente duraron las atenciones cerradas (mediana). Si casi todos se pasan, la duración está corta para lo que pide el caso.</p>
    <div class="table-wrap">
    <table class="grid-table">
        <tr><th>Paciente</th><th>Planificado</th><th>Real</th><th>Se pasaron</th></tr>
        <?php foreach ($agendaAvance['pacientes'] as $p): ?>
        <tr>
            <td><?= htmlspecialchars($p['nombre']) ?></td>
            <td><?= (int) $p['duracion_min'] ?> min</td>
            <td><?= $p['real_min'] === null ? '—' : (int) $p['real_min'] . ' min' ?></td>
            <td><?= $p['n'] ? (int) $p['pasados'] . ' de ' . (int) $p['n'] : '—' ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php endif; ?>
</div>
<?php endif; ?>

<?php if ($avanceSemanas): ?>
<div class="card">
    <strong>Semana a semana</strong>
    <p class="help help--xs">Atenciones cerradas (barra), su duración promedio y la técnica promedio de las audiometrías de cada semana.</p>
    <?php $maxAt = max(array_column($avanceSemanas, 'atenciones') ?: [1]) ?: 1; ?>
    <div class="semanas">
        <?php foreach ($avanceSemanas as $lunes => $s): ?>
        <div class="semana">
            <span class="semana-fecha"><?= htmlspecialchars(date('d-m', strtotime($lunes))) ?></span>
            <span class="semana-barra"><span style="width:<?= round(100 * $s['atenciones'] / $maxAt, 1) ?>%;"></span></span>
            <span class="semana-n"><?= $s['atenciones'] ?></span>
            <span class="semana-dur" title="Duración promedio"><?= htmlspecialchars(AlumnoIndicadores::minutos($s['duracion_s'])) ?></span>
            <span class="semana-tec" style="color:<?= AudiometriaTecnicaVista::color($s['tecnica']) ?>;"
                  title="<?= $s['n_tecnica'] ?> audiometría(s)"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($s['tecnica'])) ?></span>
        </div>
        <?php endforeach; ?>
    </div>
</div>
<?php endif; ?>

<div class="card">
    <strong>Alumnos (<?= $nAlumnos ?>)</strong>
    <p class="help help--xs">✓ alcanza la meta · ✗ no la alcanza · — sin datos todavía. El nombre lleva a su ficha.</p>
    <div class="table-wrap">
    <table class="table-dense avance-tabla">
        <tr>
            <th>Alumno</th><th>Atenciones</th><th title="Mediana de sus atenciones cerradas">Duración</th><th>Técnica</th><th>Informes</th><th>Última</th>
            <?php foreach ($medidos as $j => $o): ?>
            <th class="col-objetivo" title="<?= htmlspecialchars($o['texto'] . ' — ' . ($indicadores[$o['indicador']]['label'] ?? '') . ' ' . CourseAvance::metaTexto($o['indicador'], $o['meta'])) ?>">Obj. <?= $j + 1 ?></th>
            <?php endforeach; ?>
        </tr>
        <?php foreach ($avanceAlumnos as $uid => $al): ?>
        <tr>
            <td><a href="student.php?id=<?= (int) $uid ?>"><?= htmlspecialchars($al['nombre']) ?></a></td>
            <td><?= $al['atenciones'] ?><?= $al['en_curso'] ? ' <span class="help help--xs">+' . $al['en_curso'] . ' en curso</span>' : '' ?></td>
            <td class="nowrap"><?= $al['duracion'] !== null ? $al['duracion'] . ' min' : '—' ?></td>
            <td style="color:<?= AudiometriaTecnicaVista::color($al['tecnica_promedio']) ?>; font-weight:600;"><?= htmlspecialchars(AudiometriaTecnicaVista::pct($al['tecnica_promedio'])) ?></td>
            <td><?= $al['informes'] ?></td>
            <td class="nowrap help"><?= htmlspecialchars($al['ultima'] ?? '—') ?></td>
            <?php foreach ($medidos as $o): ?>
            <?php $v = $al[$o['indicador']] ?? null; $c = CourseAvance::cumple($o['indicador'], $v, $o['meta']); ?>
            <td class="col-objetivo <?= $c === null ? '' : ($c ? 'obj-si' : 'obj-no') ?>" title="<?= $v === null ? 'sin datos' : htmlspecialchars((string) $v . ($indicadores[$o['indicador']]['unidad'] !== '' ? ' ' . $indicadores[$o['indicador']]['unidad'] : '')) ?>">
                <?= $c === null ? '—' : ($c ? '✓' : '✗') ?>
            </td>
            <?php endforeach; ?>
        </tr>
        <?php endforeach; ?>
        <?php if (!$avanceAlumnos): ?>
        <tr><td colspan="<?= 6 + count($medidos) ?>" class="muted">Sin alumnos matriculados.</td></tr>
        <?php endif; ?>
    </table>
    </div>
</div>
