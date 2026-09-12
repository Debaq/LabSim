<?php
/**
 * Pestaña Módulos y parámetros: qué equipos ve el alumno de este curso en la
 * app, y los números que el curso puede correr respecto del default de la app
 * (normativa ABR, VEMP y lo que sume el registro CourseParams).
 *
 * Espera: $courseId, $enabledModules.
 */
?>
<div class="card">
    <strong>Módulos habilitados</strong>
    <p class="help help--mt">
        Qué ve un alumno de este curso en la app de escritorio. Sin marcar nada, el curso queda sin módulos habilitados.
    </p>
    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="set_modules">
        <input type="hidden" name="course_id" value="<?= $courseId ?>">
        <?php foreach (Courses::modulesGroupedByBox() as $boxLabel => $boxModules): ?>
        <div class="section-sep">
            <strong><?= htmlspecialchars($boxLabel) ?></strong>
            <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(230px, 1fr)); gap:0.4rem 1rem; margin-top:0.4rem;">
                <?php foreach ($boxModules as $code => $label): ?>
                <label style="font-weight:normal; display:flex; align-items:center; gap:0.3rem; margin:0;">
                    <input type="checkbox" name="modules[]" value="<?= htmlspecialchars($code) ?>" <?= in_array($code, $enabledModules, true) ? 'checked' : '' ?>>
                    <?= htmlspecialchars($label) ?>
                </label>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endforeach; ?>
        <button type="submit" class="btn btn--secondary" style="margin-top:0.6rem;">Guardar módulos</button>
    </form>
</div>

<?php
// Un editor por parámetro configurable del curso, generado desde el
// registro (CourseParams) -- solo los de módulos habilitados.
foreach (CourseParams::forModules($enabledModules) as $paramKey => $def) {
    $override = AppConfig::courseOverride($paramKey, $courseId);
    include __DIR__ . '/_params.php';
}
?>

