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

<?php
// Qué boxes de la app tiene cada curso, para las etiquetas de la tarjeta:
// dicen de un vistazo si es un curso de audiología, de electrofisiología o
// los dos, sin entrar a la pestaña Módulos.
$boxDeModulo = [];
foreach (Courses::modulesGroupedByBox() as $boxLabel => $boxModules) {
    foreach (array_keys($boxModules) as $code) {
        $boxDeModulo[$code] = preg_replace('/^Box\s+/u', '', $boxLabel);
    }
}
?>
<div class="cursos-grid">
    <?php foreach ($courses as $c): ?>
    <?php
    $codes = array_filter(explode(',', (string) ($c['module_codes'] ?? '')));
    $boxes = [];
    foreach ($codes as $code) {
        $b = $boxDeModulo[$code] ?? null;
        if ($b !== null && $b !== 'Otros módulos' && $b !== 'Sala de Espera') {
            $boxes[$b] = true;
        }
    }
    ?>
    <a class="curso-card<?= $c['active'] ? '' : ' curso-card--archivado' ?>" href="courses.php?id=<?= (int) $c['id'] ?>">
        <span class="curso-card-arriba">
            <span class="tag <?= $c['active'] ? 'tag--success' : 'tag--muted' ?>"><?= $c['active'] ? 'activo' : 'archivado' ?></span>
            <?php foreach (array_keys($boxes) as $b): ?>
            <span class="tag curso-box"><?= htmlspecialchars($b) ?></span>
            <?php endforeach; ?>
        </span>
        <span class="curso-nombre"><?= htmlspecialchars($c['name']) ?></span>
        <span class="curso-docentes"><?= $c['teacher_names'] ? htmlspecialchars((string) $c['teacher_names']) : 'Sin docente asignado' ?></span>
        <span class="curso-cifras">
            <span><strong><?= (int) $c['n_students'] ?></strong> alumnos</span>
            <span><strong><?= (int) $c['n_groups'] ?></strong> grupos</span>
            <span><strong><?= count($codes) ?></strong> módulos</span>
        </span>
    </a>
    <?php endforeach; ?>

    <?php if ($isFullAdmin): ?>
    <form method="post" class="curso-card curso-card--nuevo">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="create_course">
        <span class="curso-nombre">+ Curso nuevo</span>
        <input class="input" type="text" name="name" placeholder="Nombre, ej. Audiología aplicada ETMP176" required>
        <button class="btn btn--sm" type="submit">Crear</button>
    </form>
    <?php endif; ?>
</div>
<?php if (!$courses && !$isFullAdmin): ?>
<p class="muted">Ningún curso creado todavía.</p>
<?php endif; ?>
