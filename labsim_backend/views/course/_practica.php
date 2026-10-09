<?php
/**
 * Pestaña Práctica: la lista de pacientes de práctica deliberada del curso
 * (ver src/Practica.php). El alumno los ve en la app aparte de la agenda y
 * los abre cuando quiere, cuantas veces quiera; cada vez es un intento nuevo.
 *
 * Espera: $courseId, $practicaItems, $practicaCasos.
 */
?>
<div class="card">
    <strong>Pacientes de práctica</strong>
    <p class="help help--mt">
        Los alumnos del curso ven estos pacientes en la app, en "Práctica libre", sin fecha ni hora: los abren cuando
        quieren y cuantas veces quieran. Cada vez que abren uno queda un intento aparte, con su evolución, informes y
        técnica, que ves en la ficha de cada alumno. Los intentos no entran a la agenda ni a las estadísticas de los
        prácticos.
    </p>
    <p class="help">
        "Ficha de estudio al cerrar": cuando el alumno cierra un intento puede bajar la ficha de estudio del caso (la
        misma que bajas tú desde Fichas Clínicas) para comparar con lo que obtuvo. Vale lo que marques ahora, también
        para sus intentos anteriores.
    </p>
    <?php if (!$practicaItems): ?>
    <p class="muted">Todavía no hay pacientes de práctica en este curso.</p>
    <?php else: ?>
    <div class="table-wrap">
    <table style="margin-top:0.5rem;">
        <tr><th>Paciente</th><th>Ficha</th><th>Procedimiento</th><th>Ficha de estudio al cerrar</th><th>Alumnos</th><th>Intentos</th><th></th></tr>
        <?php foreach ($practicaItems as $it): ?>
        <tr>
            <td><?= htmlspecialchars(trim($it['nombre'] . ' ' . $it['apellido'])) ?: '—' ?></td>
            <td class="mono"><?= htmlspecialchars((string) $it['case_id']) ?></td>
            <td><?= htmlspecialchars((string) $it['procedimiento']) ?></td>
            <td>
                <form method="post">
                    <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="practice_set_sheet">
                    <input type="hidden" name="course_id" value="<?= (int) $courseId ?>">
                    <input type="hidden" name="practice_id" value="<?= (int) $it['id'] ?>">
                    <input type="hidden" name="show_study_sheet" value="0">
                    <label class="help help--xs">
                        <input type="checkbox" name="show_study_sheet" value="1" <?= $it['show_study_sheet'] ? 'checked' : '' ?>
                               onchange="this.form.submit()"> mostrar
                    </label>
                </form>
            </td>
            <td><?= (int) $it['alumnos'] ?></td>
            <td><?= (int) $it['intentos'] ?></td>
            <td>
                <form method="post" onsubmit="return confirm('¿Quitar este paciente de la lista de práctica? Los intentos ya hechos se conservan.');">
                    <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="practice_remove">
                    <input type="hidden" name="course_id" value="<?= (int) $courseId ?>">
                    <input type="hidden" name="practice_id" value="<?= (int) $it['id'] ?>">
                    <button type="submit" class="btn btn--secondary">Quitar</button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php endif; ?>
</div>

<div class="card">
    <strong>Agregar paciente</strong>
    <?php if (!$practicaCasos): ?>
    <p class="muted">No quedan fichas disponibles para agregar (las archivadas no aparecen).</p>
    <?php else: ?>
    <form method="post" class="row" style="margin-top:0.5rem; align-items:flex-end; flex-wrap:wrap;">
        <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="practice_add">
        <input type="hidden" name="course_id" value="<?= (int) $courseId ?>">
        <label>Ficha
            <select name="case_id" required>
                <option value="">Elegir…</option>
                <?php foreach ($practicaCasos as $c): ?>
                <option value="<?= htmlspecialchars((string) $c['id']) ?>"><?= htmlspecialchars(trim(($c['apellido'] ?? '') . ' ' . ($c['nombre'] ?? '')) ?: 'Sin nombre') ?> · <?= htmlspecialchars((string) $c['id']) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Procedimiento
            <input type="text" name="procedimiento" placeholder="Audiometría">
        </label>
        <label class="inline-check practica-check">
            <input type="checkbox" name="show_study_sheet" value="1"> Ficha de estudio al cerrar
        </label>
        <button type="submit" class="btn">Agregar</button>
    </form>
    <p class="help help--xs">Solo se pueden agregar fichas completas, con el mismo criterio que para agendarlas.</p>
    <?php endif; ?>
</div>
