<?php
/**
 * Editor de un parámetro configurable por curso. Un solo render para todos:
 * la forma (grupos, filas, campos) sale del registro CourseParams, no de
 * código escrito para cada examen -- antes ABR y VEMP tenían cada uno su
 * propia copia de esta card en courses.php.
 *
 * Espera: $paramKey (string), $def (CourseParams::all()[$paramKey]),
 *         $courseId (int), $override (?array, AppConfig::courseOverride()).
 */
$hasOverride = !empty($override);
?>
<div class="card">
    <div class="row row--between" style="margin:0; align-items:center;">
        <strong><?= htmlspecialchars($def['title']) ?></strong>
        <?php if ($hasOverride): ?>
        <span class="tag tag--warn">configuración propia del curso</span>
        <?php else: ?>
        <span class="tag tag--muted">heredando el default de la app</span>
        <?php endif; ?>
    </div>
    <p class="help help--mt"><?= htmlspecialchars($def['help']) ?></p>

    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="set_params">
        <input type="hidden" name="course_id" value="<?= (int) $courseId ?>">
        <input type="hidden" name="param_key" value="<?= htmlspecialchars($paramKey) ?>">
        <?php foreach ($def['groups'] as $groupKey => $group): ?>
        <?php
            $groupTouched = isset($override[$groupKey]);
        ?>
        <details style="margin-top:0.5rem;" <?= $groupTouched ? 'open' : '' ?>>
            <summary>
                <strong><?= htmlspecialchars($group['label']) ?></strong>
                <?php if ($groupTouched): ?><span class="tag tag--warn">modificado</span><?php endif; ?>
            </summary>
            <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(170px, 1fr)); gap:0.6rem 1rem; margin-top:0.4rem;">
                <?php foreach ($group['rows'] as $rowKey => $rowLabel): ?>
                <div>
                    <strong style="font-weight:600;"><?= htmlspecialchars($rowLabel) ?></strong>
                    <?php foreach ($def['fields'] as $fieldKey => $field): ?>
                    <label class="normal" style="display:block; margin-top:0.2rem;">
                        <?= htmlspecialchars($field['label']) ?>
                        <input type="number"
                               step="<?= htmlspecialchars((string) $field['step']) ?>"
                               <?= isset($field['min']) ? 'min="' . htmlspecialchars((string) $field['min']) . '"' : '' ?>
                               <?= isset($field['max']) ? 'max="' . htmlspecialchars((string) $field['max']) . '"' : '' ?>
                               name="params[<?= htmlspecialchars($groupKey) ?>][<?= htmlspecialchars($rowKey) ?>][<?= htmlspecialchars($fieldKey) ?>]"
                               value="<?= htmlspecialchars(CourseParams::displayValue($def, $override, (string) $groupKey, (string) $rowKey, (string) $fieldKey)) ?>">
                    </label>
                    <?php endforeach; ?>
                </div>
                <?php endforeach; ?>
            </div>
        </details>
        <?php endforeach; ?>
        <div class="form-actions-sticky">
            <button type="submit" class="btn btn--secondary">Guardar configuración</button>
        </div>
    </form>

    <?php if ($hasOverride): ?>
    <form method="post" style="margin-top:0.5rem;"
          onsubmit="return confirm('¿Restablecer al valor por defecto de la app? Se pierde la configuración propia de este curso.');">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="reset_params">
        <input type="hidden" name="course_id" value="<?= (int) $courseId ?>">
        <input type="hidden" name="param_key" value="<?= htmlspecialchars($paramKey) ?>">
        <button type="submit" class="btn btn--danger btn--sm">Volver a default</button>
    </form>
    <?php endif; ?>
</div>
