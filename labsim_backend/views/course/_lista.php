<?php
/**
 * Lista de cursos: la ve el admin completo (todos) y el docente con dos o
 * más cursos; con uno solo, courses.php entra directo a su detalle.
 *
 * También es donde aterriza el docente que entró desde un curso de Moodle
 * todavía sin vincular: hay que elegir a qué curso de LabSim va, y eso es
 * una decisión entre cursos, no dentro de uno.
 *
 * Espera: $courses, $isFullAdmin, $hasPendingLink, $pendingLinkPlatform,
 *         $pendingLinkContext.
 */
?>
<?php if ($hasPendingLink): ?>
<div class="card" style="border: 2px solid var(--color-info-border);">
    <strong>Vincular curso de Moodle</strong>
    <p class="muted">Entraste desde un curso de Moodle que todavía no está vinculado a ningún curso de LabSim. Vincúlalo una sola vez y cada alumno que entre desde ahí se matriculará solo -- sin que tengas que agregarlos a mano ni conocer sus nombres.</p>
    <?php if (!$courses): ?>
    <p class="muted">No tienes ningún curso de LabSim todavía -- créalo primero (o pide que te asignen como docente de uno) y vuelve a entrar desde Moodle.</p>
    <?php else: ?>
    <form method="post" class="row">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="link_lti_context">
        <input type="hidden" name="lti_platform_id" value="<?= $pendingLinkPlatform ?>">
        <input type="hidden" name="lti_context_id" value="<?= htmlspecialchars($pendingLinkContext) ?>">
        <label style="flex:1; margin:0;">Curso de LabSim
            <select name="course_id" required>
                <option value="">-- elegir --</option>
                <?php foreach ($courses as $c): ?>
                <option value="<?= $c['id'] ?>"><?= htmlspecialchars($c['name']) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <button type="submit">Vincular</button>
    </form>
    <?php endif; ?>
</div>
<?php endif; ?>

<?php if ($isFullAdmin): ?>
<div class="card">
    <strong>Crear curso</strong>
    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="create_course">
        <label class="field-label">Nombre
            <input class="input" type="text" name="name" required>
        </label>
        <div class="form-actions-sticky">
            <button class="btn" type="submit">Crear</button>
        </div>
    </form>
</div>
<?php endif; ?>

<div class="card">
    <strong>Cursos</strong>
    <div class="table-wrap">
    <table>
        <tr><th>Nombre</th><th>Estado</th><th>Docentes</th><th>Alumnos</th></tr>
        <?php foreach ($courses as $c): ?>
        <tr>
            <td><a href="courses.php?id=<?= $c['id'] ?>"><?= htmlspecialchars($c['name']) ?></a></td>
            <td><?= $c['active'] ? 'activo' : 'archivado' ?></td>
            <td><?= (int) $c['n_teachers'] ?></td>
            <td><?= (int) $c['n_students'] ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$courses): ?>
        <tr><td colspan="4" class="muted">Ningún curso creado todavía.</td></tr>
        <?php endif; ?>
    </table>
    </div>
</div>
