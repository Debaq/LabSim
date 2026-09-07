<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Configuración global (no por curso): catálogos de referencia bibliográfica
 * que alimentan los "autocompletar" de las fichas clínicas -- hoy solo ABR
 * (baselines de onda I/III/V por población, lat/amp), a futuro otros exámenes
 * (ver comentario de AppConfig.php: "ABR primero, P300/electrococleografía
 * después"). No confundir con la normativa de estímulos ABR por curso
 * (courses.php, key normative_data.abr) -- esa es cuánto se desvía
 * chirp/burst respecto al click DE ESE CASO; esto es de dónde sale el click
 * "normal" en primer lugar, según el autor elegido al crear el paciente.
 */

const ABR_AUTHORS_KEY = 'abr_reference_authors';
const ABR_WAVES = ['I', 'III', 'V'];
const ABR_POPULATION_LABELS = [
    'adult_male' => 'Adulto (hombre, 18-50)',
    'adult_female' => 'Adulto (mujer, 18-50)',
    'child' => 'Niño (2-12)',
    'neonate' => 'Neonato (0-3 meses)',
    'elderly' => 'Adulto mayor (60-85)',
];

// Mismos números que el pseudo-autor "LabSim (default)" hardcodeado en
// case_create.php y que ABR_generator_v3.py trae de fábrica en
// resources/abr/normative_data.json (población "click", vía aérea).
// Mantener sincronizado a mano si ese JSON cambia -- es el punto de
// referencia (offset 0) contra el que se calculan los demás autores.
const ABR_DEFAULT_POPULATIONS = [
    'adult_male'   => ['I' => ['lat' => 1.65, 'amp' => 0.30], 'III' => ['lat' => 3.85, 'amp' => 0.35], 'V' => ['lat' => 5.70, 'amp' => 0.50]],
    'adult_female' => ['I' => ['lat' => 1.62, 'amp' => 0.21], 'III' => ['lat' => 3.68, 'amp' => 0.37], 'V' => ['lat' => 5.47, 'amp' => 0.60]],
    'child'        => ['I' => ['lat' => 1.58, 'amp' => 0.28], 'III' => ['lat' => 3.78, 'amp' => 0.33], 'V' => ['lat' => 5.60, 'amp' => 0.48]],
    'neonate'      => ['I' => ['lat' => 2.10, 'amp' => 0.20], 'III' => ['lat' => 4.70, 'amp' => 0.24], 'V' => ['lat' => 6.80, 'amp' => 0.35]],
    'elderly'      => ['I' => ['lat' => 1.75, 'amp' => 0.27], 'III' => ['lat' => 4.00, 'amp' => 0.32], 'V' => ['lat' => 5.90, 'amp' => 0.45]],
];

function slugify_author(string $label): string
{
    $slug = strtolower(trim($label));
    $slug = preg_replace('/[^a-z0-9]+/', '_', $slug) ?? '';
    $slug = trim($slug, '_');
    return $slug !== '' ? $slug : 'autor_' . substr(md5($label), 0, 6);
}

/** Lee abr[population][wave][lat|amp] del POST hacia el shape guardado. */
function parse_author_populations(array $post): array
{
    $out = [];
    foreach (array_keys(ABR_POPULATION_LABELS) as $pop) {
        foreach (ABR_WAVES as $wave) {
            foreach (['lat', 'amp'] as $field) {
                $val = trim((string) ($post[$pop][$wave][$field] ?? ''));
                if ($val !== '' && is_numeric($val)) {
                    $out[$pop][$wave][$field] = (float) $val;
                }
            }
        }
    }
    return $out;
}

$me = Auth::requireFullAdminSession();
$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $action = (string) ($_POST['form_action'] ?? '');
    $authors = AppConfig::getEffective(ABR_AUTHORS_KEY, null) ?? [];

    if ($action === 'add_author') {
        $label = trim((string) ($_POST['label'] ?? ''));
        if ($label === '') {
            $error = 'Falta el nombre del autor/set.';
        } else {
            $id = slugify_author($label);
            if (isset($authors[$id])) {
                $error = 'Ya existe un set con ese nombre.';
            } else {
                $populations = parse_author_populations((array) ($_POST['pop'] ?? []));
                $authors[$id] = ['label' => $label, 'populations' => $populations];
                AppConfig::set(ABR_AUTHORS_KEY, $authors, null);
                $success = "Set '{$label}' creado.";
                AdminAudit::log($me, 'abr_author_add', ['author_id' => $id, 'label' => $label]);
            }
        }
    } elseif ($action === 'update_author') {
        $id = (string) ($_POST['author_id'] ?? '');
        $label = trim((string) ($_POST['label'] ?? ''));
        if ($id === '' || !isset($authors[$id])) {
            $error = 'Set no encontrado.';
        } elseif ($label === '') {
            $error = 'Falta el nombre del autor/set.';
        } else {
            $populations = parse_author_populations((array) ($_POST['pop'] ?? []));
            $authors[$id] = ['label' => $label, 'populations' => $populations];
            AppConfig::set(ABR_AUTHORS_KEY, $authors, null);
            $success = "Set '{$label}' actualizado.";
            AdminAudit::log($me, 'abr_author_update', ['author_id' => $id, 'label' => $label]);
        }
    } elseif ($action === 'delete_author') {
        $id = (string) ($_POST['author_id'] ?? '');
        if (isset($authors[$id])) {
            $label = $authors[$id]['label'] ?? $id;
            unset($authors[$id]);
            AppConfig::set(ABR_AUTHORS_KEY, $authors, null);
            $success = "Set '{$label}' eliminado.";
            AdminAudit::log($me, 'abr_author_delete', ['author_id' => $id]);
        }
    }
}

$authors = AppConfig::getEffective(ABR_AUTHORS_KEY, null) ?? [];

admin_header('Normativas', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <strong>ABR -- autores de referencia</strong>
    <p class="help help--mt">
        Baselines de onda I/III/V (latencia en ms, amplitud en µV a 80dB) por población, según distintos autores/estudios.
        Se usan en el creador de paciente (pestaña ABR): al elegir un autor y hacer clic en "Autocompletar", la diferencia
        entre el baseline de ese autor y el default de la app se suma a la sugerencia -- así "Normal" según Hall no es
        necesariamente el mismo número que "Normal" según Chiappa. No afecta casos ya creados, solo la sugerencia al crear/editar.
    </p>
</div>

<div class="card">
    <details>
        <summary><strong>LabSim (default)</strong> -- referencia fija, no editable</summary>
        <p class="help help--mt">Es la que trae la app de fábrica (resources/abr/normative_data.json). Todos los demás autores se comparan contra esta.</p>
        <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:0.8rem; margin-top:0.4rem;">
            <?php foreach (ABR_POPULATION_LABELS as $pop => $popLabel): ?>
            <div>
                <strong style="font-weight:600;"><?= htmlspecialchars($popLabel) ?></strong>
                <?php foreach (ABR_WAVES as $wave): ?>
                <div style="font-size:0.85em; opacity:0.85;">
                    Onda <?= $wave ?>: lat <?= ABR_DEFAULT_POPULATIONS[$pop][$wave]['lat'] ?> ms / amp <?= ABR_DEFAULT_POPULATIONS[$pop][$wave]['amp'] ?> µV
                </div>
                <?php endforeach; ?>
            </div>
            <?php endforeach; ?>
        </div>
    </details>
</div>

<?php foreach ($authors as $authorId => $author): ?>
<div class="card">
    <details>
        <summary><strong><?= htmlspecialchars($author['label'] ?? $authorId) ?></strong></summary>
        <form method="post" style="margin-top:0.5rem;">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="update_author">
            <input type="hidden" name="author_id" value="<?= htmlspecialchars($authorId) ?>">
            <label>Nombre
                <input type="text" name="label" value="<?= htmlspecialchars($author['label'] ?? '') ?>" required>
            </label>
            <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:0.8rem; margin-top:0.6rem;">
                <?php foreach (ABR_POPULATION_LABELS as $pop => $popLabel): ?>
                <div>
                    <strong style="font-weight:600;"><?= htmlspecialchars($popLabel) ?></strong>
                    <?php foreach (ABR_WAVES as $wave): ?>
                    <?php $cur = $author['populations'][$pop][$wave] ?? ABR_DEFAULT_POPULATIONS[$pop][$wave]; ?>
                    <div style="margin-top:0.3rem;">
                        <span style="font-weight:normal; font-size:0.85em;">Onda <?= $wave ?></span>
                        <label style="font-weight:normal; display:inline-block; margin-right:0.4rem;">
                            lat <input type="number" step="0.01" style="width:5.5em;" name="pop[<?= $pop ?>][<?= $wave ?>][lat]" value="<?= htmlspecialchars((string) $cur['lat']) ?>">
                        </label>
                        <label style="font-weight:normal; display:inline-block;">
                            amp <input type="number" step="0.01" style="width:5.5em;" name="pop[<?= $pop ?>][<?= $wave ?>][amp]" value="<?= htmlspecialchars((string) $cur['amp']) ?>">
                        </label>
                    </div>
                    <?php endforeach; ?>
                </div>
                <?php endforeach; ?>
            </div>
            <div class="form-actions-sticky">
                <button type="submit" class="btn btn--secondary">Guardar</button>
            </div>
        </form>
        <form method="post" style="margin-top:0.4rem;"
              onsubmit="return confirm('¿Eliminar este set de autor? Los casos que ya usaron sus valores no cambian, solo deja de estar disponible para autocompletar.');">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="delete_author">
            <input type="hidden" name="author_id" value="<?= htmlspecialchars($authorId) ?>">
            <button type="submit" class="btn btn--danger btn--sm">Eliminar set</button>
        </form>
    </details>
</div>
<?php endforeach; ?>

<div class="card">
    <details>
        <summary><strong>+ Agregar autor nuevo</strong></summary>
        <form method="post" style="margin-top:0.5rem;">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="add_author">
            <label>Nombre (ej. "Hall (2015)")
                <input type="text" name="label" required>
            </label>
            <p class="help help--mt">Prellenado con el default de la app -- edita solo lo que ese autor reporta distinto.</p>
            <div style="display:grid; grid-template-columns:repeat(auto-fill, minmax(220px, 1fr)); gap:0.8rem; margin-top:0.6rem;">
                <?php foreach (ABR_POPULATION_LABELS as $pop => $popLabel): ?>
                <div>
                    <strong style="font-weight:600;"><?= htmlspecialchars($popLabel) ?></strong>
                    <?php foreach (ABR_WAVES as $wave): ?>
                    <?php $cur = ABR_DEFAULT_POPULATIONS[$pop][$wave]; ?>
                    <div style="margin-top:0.3rem;">
                        <span style="font-weight:normal; font-size:0.85em;">Onda <?= $wave ?></span>
                        <label style="font-weight:normal; display:inline-block; margin-right:0.4rem;">
                            lat <input type="number" step="0.01" style="width:5.5em;" name="pop[<?= $pop ?>][<?= $wave ?>][lat]" value="<?= htmlspecialchars((string) $cur['lat']) ?>">
                        </label>
                        <label style="font-weight:normal; display:inline-block;">
                            amp <input type="number" step="0.01" style="width:5.5em;" name="pop[<?= $pop ?>][<?= $wave ?>][amp]" value="<?= htmlspecialchars((string) $cur['amp']) ?>">
                        </label>
                    </div>
                    <?php endforeach; ?>
                </div>
                <?php endforeach; ?>
            </div>
            <div class="form-actions-sticky">
                <button type="submit" class="btn btn--secondary">Crear set</button>
            </div>
        </form>
    </details>
</div>

<?php
admin_footer();
