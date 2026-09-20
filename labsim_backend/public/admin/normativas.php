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
 * después"). Esto define de dónde sale el click "normal" según el autor
 * elegido al crear el paciente; cómo se desvían chirp y burst de ese click
 * NO se configura: el generador lo deriva (ver ABR_generator.py,
 * _rescale_ratio_block). Hubo un editor por curso para eso y se sacó.
 */

/**
 * Bibliografía de la que sale cada valor de fábrica. Se muestra ACÁ y no
 * en la app: el alumno lee un examen, no una tabla normativa con citas.
 */
const ABR_FUENTES = [
    'F01' => [
        'cita' => "Sanfins MD, Santillo MEA, Martins MFP, Silva DLdS, Gos E, Skarzynski PH, Hall JW III. The Influence of Sex, Ear, and Age on Auditory Brainstem Response. Diagnostics. 2026;16(7):971.",
        'n' => "244 sujetos (134 H / 110 M), 3-79 anios",
        'protocolo' => "Click 0.1 ms rarefaccion, 80 dB nHL, 19.3/s, ER-3A, Fz-mastoides ipsi, filtro 0.1-3 kHz, 2x2000 barridos",
        'enlace' => "https://doi.org/10.3390/diagnostics16070971",
    ],
    'F04' => [
        'cita' => "Chalak S, Kale A, Deshpande VK, Biswas DA. Establishment of Normative Data for Monaural Recordings of Auditory Brainstem Response. J Clin Diagn Res. 2013.",
        'n' => "40 ninios, edad media 7.62 +/- 2.39 anios",
        'protocolo' => "Click monoaural con enmascaramiento contralateral, 70 dB nHL, 11.1/s, filtro 100/250-5000 Hz, 2000 barridos",
        'enlace' => "https://doi.org/10.7860/JCDR/2013/6768.3730",
    ],
    'F07' => [
        'cita' => "Auditory Brainstem Response: reference-values for age (neonatos por edad gestacional).",
        'n' => "40 neonatos por grupo de edad gestacional",
        'protocolo' => "Click; grupos de 35-36 y 37-38 semanas",
        'enlace' => "https://www.researchgate.net/publication/263015732",
    ],
    'F09' => [
        'cita' => "Jerger J, Hall J. Effects of age and sex on auditory brainstem response. Arch Otolaryngol. 1980;106(7):387-391.",
        'n' => "319 sujetos (182 H / 137 M), 98 normoyentes",
        'protocolo' => "Click; latencia y amplitud de onda V por edad y sexo",
        'enlace' => "https://doi.org/10.1001/archotol.1980.00790310011003",
    ],
    'F10' => [
        'cita' => "Stockard JE, Stockard JJ, Westmoreland BF, Corfits JL. Brainstem auditory-evoked responses: normal variation as a function of stimulus and subject characteristics. Arch Neurol. 1979.",
        'n' => "64 adultos + 77 neonatos de termino",
        'protocolo' => "Click rarefaccion vs condensacion, 30-70 dB SL/HL, 10 y 80 clicks/s",
        'enlace' => "https://pubmed.ncbi.nlm.nih.gov/508145/",
    ],
    'F13' => [
        'cita' => "Jiang ZD et al. The effect of click rate on latency and interpeak interval of the brain-stem auditory evoked potentials in children from birth to 6 years. Electroencephalogr Clin Neurophysiol. 1991.",
        'n' => "80 ninios (0-6 anios) + 21 adultos",
        'protocolo' => "Click a 10, 30, 50, 70 y 90/s; 70, 40 y 20 dB HL/SL",
        'enlace' => "https://www.sciencedirect.com/science/article/abs/pii/016855979190044X",
    ],
    'F18' => [
        'cita' => "Normalization of Bone Conduction Auditory Brainstem Evoked Responses in Normal Hearing Individuals. J Int Adv Otol.",
        'n' => "100 sujetos (50 H / 50 M), 10-60 anios, 200 oidos",
        'protocolo' => "ABR por via osea a 50, 30 y 10 dB nHL (el vibrador no entrega mas), 5 grupos etarios",
        'enlace' => "https://advancedotology.org//en/normalization-of-bone-conduction-auditory-brainstem-evoked-responses-in-normal-hearing-individuals-131309",
    ],
    'F21' => [
        'cita' => "Aguilar-Madrid G et al. Latencias de los potenciales evocados auditivos de tronco cerebral en trabajadores. 2015. PMID 26960049.",
        'n' => "196 sujetos (107 H / 89 M), 16-65 anios",
        'protocolo' => "Nicolet Viking Quest, 2000 clicks de rarefaccion, 33/s, ventana 10 ms, camara sonoamortiguada",
        'enlace' => "https://www.redalyc.org/pdf/4577/457745149012.pdf",
    ],
    'F24' => [
        'cita' => "Cargnelutti M, Coser PL, Biaggio EP. LS CE-Chirp vs. Click in the neuroaudiological diagnosis by ABR. Braz J Otorhinolaryngol. 2017;83(3):313-317.",
        'n' => "30 sujetos / 60 oidos normoyentes",
        'protocolo' => "85 dB nHL, polaridad alternante, 17.1/s, filtro 100-3000 Hz; click y chirp en los MISMOS sujetos",
        'enlace' => "https://doi.org/10.1016/j.bjorl.2016.04.018",
    ],
    'F25' => [
        'cita' => "Rosa LAC et al. Auditory Brainstem Response: reference-values for age. CoDAS. 2014.",
        'n' => "80 lactantes por edad posconcepcional",
        'protocolo' => "Click; grupos de 35-36, 37-38, 39-40 semanas y 6 meses",
        'enlace' => "https://doi.org/10.1590/2317-1782/2014469in",
    ],
    'F26' => [
        'cita' => "Hood LJ. Clinical Applications of the Auditory Brainstem Response. Singular Publishing Group. Tabla 2-3.",
        'n' => "Mujeres normoyentes 20-30 anios; n de 2 a 20 segun celda",
        'protocolo' => "Click, serie completa de 90 a 20 dB nHL, ondas I a VI e interpicos",
        'enlace' => "Transcripcion aportada por el usuario; verificar contra el libro impreso",
    ],
    'F27' => [
        'cita' => "Da Silva Nunes C, Gentile Matas C. Audiometria de tronco encefalico utilizando diferentes polaridades de presentacion del estimulo acustico. Rev Chil Fonoaudiol. 2005;6(2).",
        'n' => "50 adultos (25 H / 25 M), 18-40 anios, 100 oidos",
        'protocolo' => "Bio-Logic Traveler Express, click 0.1 ms, 11.1/s, 80 dB HL, 2000 estimulos con replica",
        'enlace' => "Revista Chilena de Fonoaudiologia, vol. 6, num. 2, 2005",
    ],
];

/** Qué ancla cada fuente en la tabla de fábrica. */
const ABR_FUENTE_DE = [
    'adult_male' => ['lat' => 'F01', 'amp' => 'F27'],
    'adult_female' => ['lat' => 'F01', 'amp' => 'F27'],
    'child' => ['lat' => 'F04', 'amp' => 'calculada'],
    'neonate' => ['lat' => 'F25', 'amp' => 'calculada'],
    'elderly' => ['lat' => 'F21', 'amp' => 'F09'],
];

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
// case_create.php y que ABR_generator.py trae de fábrica en
// resources/abr/normative_data.json (población "click", vía aérea).
// Mantener sincronizado a mano si ese JSON cambia -- es el punto de
// referencia (offset 0) contra el que se calculan los demás autores.
//
// De dónde sale cada fila (ver ABR_FUENTES abajo): latencias de adulto de
// F01, amplitudes de adulto de F27, niño de F04, neonato de F25/F07 y
// adulto mayor de F21. Lo que ninguna serie publica --ondas II, IV, VI,
// VII, microfónica y las amplitudes pediátricas-- se calcula de esas.
const ABR_DEFAULT_POPULATIONS = [
    'adult_male'   => ['I' => ['lat' => 1.47, 'amp' => 0.320], 'III' => ['lat' => 3.75, 'amp' => 0.370], 'V' => ['lat' => 5.68, 'amp' => 0.400]],
    'adult_female' => ['I' => ['lat' => 1.46, 'amp' => 0.440], 'III' => ['lat' => 3.65, 'amp' => 0.470], 'V' => ['lat' => 5.54, 'amp' => 0.540]],
    'child'        => ['I' => ['lat' => 1.48, 'amp' => 0.239], 'III' => ['lat' => 3.50, 'amp' => 0.282], 'V' => ['lat' => 5.50, 'amp' => 0.410]],
    'neonate'      => ['I' => ['lat' => 1.79, 'amp' => 0.171], 'III' => ['lat' => 4.56, 'amp' => 0.205], 'V' => ['lat' => 7.00, 'amp' => 0.299]],
    'elderly'      => ['I' => ['lat' => 1.84, 'amp' => 0.342], 'III' => ['lat' => 3.91, 'amp' => 0.378], 'V' => ['lat' => 5.84, 'amp' => 0.423]],
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
                <div style="font-size:0.78em; opacity:0.7;">
                    lat <?= htmlspecialchars(ABR_FUENTE_DE[$pop]['lat']) ?> ·
                    amp <?= htmlspecialchars(ABR_FUENTE_DE[$pop]['amp']) ?>
                </div>
                <?php foreach (ABR_WAVES as $wave): ?>
                <div style="font-size:0.85em; opacity:0.85;">
                    Onda <?= $wave ?>: lat <?= ABR_DEFAULT_POPULATIONS[$pop][$wave]['lat'] ?> ms / amp <?= ABR_DEFAULT_POPULATIONS[$pop][$wave]['amp'] ?> µV
                </div>
                <?php endforeach; ?>
            </div>
            <?php endforeach; ?>
        </div>
        <p class="help help--mt">Las ondas II, IV, VI y VII, la microfónica y las amplitudes de niño y neonato no las publica ninguna de estas series: se calculan de las que sí (posición relativa entre ondas ancladas). La vía ósea tampoco tiene tabla publicada -- F18 existe pero no la trae -- así que se deriva de la aérea de su población.</p>
    </details>
</div>

<div class="card">
    <details>
        <summary><strong>Fuentes</strong> -- de dónde sale cada número</summary>
        <p class="help help--mt">Estas citas son para usted. No se muestran en la app ni en la ficha del alumno.</p>
        <?php foreach (ABR_FUENTES as $fid => $f): ?>
        <div style="margin-top:0.6rem; font-size:0.85em;">
            <strong><?= htmlspecialchars($fid) ?></strong> ·
            <?= htmlspecialchars($f['cita']) ?>
            <div style="opacity:0.8;"><?= htmlspecialchars($f['n']) ?> · <?= htmlspecialchars($f['protocolo']) ?></div>
            <?php if (strpos($f['enlace'], 'http') === 0): ?>
            <div><a href="<?= htmlspecialchars($f['enlace']) ?>" target="_blank" rel="noopener"><?= htmlspecialchars($f['enlace']) ?></a></div>
            <?php else: ?>
            <div style="opacity:0.8;"><?= htmlspecialchars($f['enlace']) ?></div>
            <?php endif; ?>
        </div>
        <?php endforeach; ?>
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
