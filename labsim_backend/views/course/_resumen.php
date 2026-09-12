<?php
/**
 * Pestaña Resumen: en qué estado está el curso, no con qué se configura.
 * Es lo que la página vieja no decía -- un curso sin módulos habilitados o
 * sin ninguna cita agendada se veía igual que uno andando, y el docente se
 * enteraba cuando el alumno abría la app y no tenía nada.
 *
 * Espera: $course, $courseId, $isFullAdmin, $checklist, $proximas,
 *         $sinActividad, $conteoCitas.
 */
$pendientes = array_values(array_filter($checklist, static fn(array $i): bool => !$i['ok'] && !$i['opcional']));
?>
<div class="card">
    <div class="row row--between" style="margin:0; align-items:center;">
        <strong>Estado del curso</strong>
        <?php if (!$pendientes): ?>
        <span class="tag tag--success">listo para usar</span>
        <?php else: ?>
        <span class="tag tag--warn"><?= count($pendientes) ?> cosa(s) por resolver</span>
        <?php endif; ?>
    </div>
    <table style="margin-top:0.6rem;">
        <?php foreach ($checklist as $item): ?>
        <tr>
            <td style="width:2rem;"><?= $item['ok'] ? '&#10003;' : ($item['opcional'] ? '&middot;' : '&#9888;') ?></td>
            <td>
                <a href="courses.php?id=<?= $courseId ?>&amp;tab=<?= htmlspecialchars($item['tab']) ?>"><?= htmlspecialchars($item['label']) ?></a>
                <?php if ($item['opcional']): ?><span class="tag tag--muted">opcional</span><?php endif; ?>
            </td>
            <td class="help help--xs"><?= htmlspecialchars($item['detalle']) ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
</div>

<div class="card">
    <div class="row row--between" style="margin:0; align-items:center;">
        <strong>Próximos 7 días</strong>
        <a href="agenda.php?curso=<?= $courseId ?>">Abrir la agenda del curso</a>
    </div>
    <?php if (!$proximas): ?>
    <p class="muted" style="margin-top:0.5rem;">
        Sin citas en los próximos 7 días<?= $conteoCitas['total'] > 0 ? ' (el curso tiene ' . (int) $conteoCitas['total'] . ' cita(s) en otras fechas).' : '.' ?>
    </p>
    <?php else: ?>
    <div class="table-wrap">
    <table style="margin-top:0.5rem;">
        <tr><th>Fecha</th><th>Hora</th><th>Paciente</th><th>Procedimiento</th><th>Asignada a</th><th>Atenciones</th></tr>
        <?php foreach ($proximas as $c): ?>
        <tr>
            <td><?= htmlspecialchars((string) $c['fecha']) ?></td>
            <td><?= htmlspecialchars((string) $c['hora']) ?></td>
            <td><?= htmlspecialchars(trim($c['nombre'] . ' ' . $c['apellido'])) ?></td>
            <td><?= htmlspecialchars((string) $c['procedimiento']) ?></td>
            <td>
                <?php if ($c['alumno']): ?><?= htmlspecialchars($c['alumno']) ?>
                <?php elseif ($c['grupo']): ?><span class="tag tag--muted"><?= htmlspecialchars($c['grupo']) ?></span>
                <?php else: ?><span class="help help--xs">todo el curso</span><?php endif; ?>
            </td>
            <td><?= (int) $c['atenciones'] ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php endif; ?>
</div>

<div class="card">
    <strong>Alumnos sin actividad (<?= count($sinActividad) ?>)</strong>
    <p class="help help--mt">Matriculados que todavía no registraron ninguna atención en este curso. Los que sí trabajaron se siguen en el dashboard.</p>
    <?php if (!$sinActividad): ?>
    <p class="muted">Todos los matriculados atendieron al menos una vez.</p>
    <?php else: ?>
    <p style="margin-top:0.4rem;">
        <?php foreach ($sinActividad as $s): ?>
        <a class="tag tag--muted" style="margin:0 0.3rem 0.3rem 0;" href="student.php?id=<?= (int) $s['id'] ?>"><?= htmlspecialchars($s['display_name']) ?></a>
        <?php endforeach; ?>
    </p>
    <?php endif; ?>
</div>

<?php if ($isFullAdmin): ?>
<div class="card">
    <details>
        <summary><strong>Nombre y estado del curso</strong></summary>
        <form method="post" style="margin-top:0.5rem;">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="rename_course">
            <input type="hidden" name="course_id" value="<?= $courseId ?>">
            <label>Nombre
                <input type="text" name="name" value="<?= htmlspecialchars($course['name']) ?>" required>
            </label>
            <button type="submit" class="btn btn--secondary btn--sm">Guardar</button>
        </form>
        <form method="post" style="margin-top:0.6rem;"
              onsubmit="return confirm(<?= htmlspecialchars(json_encode($course['active'] ? '¿Archivar el curso? Deja de aparecer entre los cursos activos.' : '¿Activar el curso de nuevo?'), ENT_QUOTES) ?>);">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="toggle_active">
            <input type="hidden" name="course_id" value="<?= $courseId ?>">
            <button type="submit" class="btn btn--secondary btn--sm"><?= $course['active'] ? 'Archivar curso' : 'Activar curso' ?></button>
        </form>
    </details>
</div>
<?php endif; ?>
