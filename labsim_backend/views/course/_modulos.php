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
        <div class="modulos-box">
            <div class="modulos-box-titulo"><?= htmlspecialchars($boxLabel) ?></div>
            <div class="modulos-grid">
                <?php foreach ($boxModules as $code => $label): ?>
                <label class="modulo-tile">
                    <input type="checkbox" name="modules[]" value="<?= htmlspecialchars($code) ?>" <?= in_array($code, $enabledModules, true) ? 'checked' : '' ?>>
                    <span class="modulo-tile-nombre"><?= htmlspecialchars($label) ?></span>
                </label>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endforeach; ?>
        <button type="submit" class="btn" style="margin-top:var(--space-5);">Guardar módulos</button>
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

