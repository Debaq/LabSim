<?php
/**
 * Ficha 9 -- VEMP: los tres subtipos por oído, con vista previa de cada uno.
 *
 * Vive fuera de public/ a propósito: el docroot del hosting es la raíz de
 * labsim_backend/ y public/.htaccess re-habilita todo lo que cuelga de
 * public/, así que ahí adentro esta ficha sería alcanzable por URL y
 * correría sin la sesión de admin que valida case_create.php.
 *
 * Incluido por admin/case_create.php, que comparte su scope: este archivo
 * NO declara lo que usa. Espera del padre $v.
 */
?>
<div class="tab-panel" data-tab="vemp">
<div class="card">
    <strong>VEMP</strong>
    <p class="help"><strong>Los tres se arman siempre</strong>, y no hay selector de subtipo acá: el que elige cuál correr es el <strong>alumno</strong>, en el equipo. Configurar uno solo dejaba los otros dos normales pasara lo que pasara.</p>
    <p class="help">La <strong>patología va una sola vez</strong>, para el oído. El generador la aplica al subtipo que corresponde: <em>sacular</em> sobre el cVEMP, <em>utricular</em> sobre el oVEMP, <em>neural</em> sobre los dos. El que no toca queda con la respuesta que le dé su propio umbral.</p>
    <p class="help">El <strong>umbral</strong> y las <strong>ondas</strong> son de cada VEMP por separado. El cVEMP y el mVEMP comparten los nombres de los picos (P13/N23), así que cada uno lleva sus propios campos: hasta acá se pisaban en los mismos cuatro.</p>
</div>

<div class="two-col">
<?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
<div class="card">
    <strong>Oído <?= $ladoLabel ?></strong>
    <label>Patología vestibular
        <select name="vemp[<?= $lado ?>][type]" class="vemp-type-select" data-lado="<?= $lado ?>">
            <?php foreach (CaseBuilder::VEMP_TYPE_OPTIONS as $opt): ?>
            <option value="<?= $opt ?>" <?= ($v['vemp'][$lado]['type'] ?? 'normal') === $opt ? 'selected' : '' ?>><?= ucfirst($opt) ?></option>
            <?php endforeach; ?>
        </select>
    </label>
    <p class="help">Con "Normal" las ondas tienen que quedar en 0: un VEMP alterado con patología normal es un caso que se contradice y el editor lo reclama al guardar.</p>

    <?php
    // Sticky (POST): una casilla destildada no viaja, así que ahí manda
    // isset() y no el valor precargado.
    $vempDecidido = $_SERVER['REQUEST_METHOD'] === 'POST'
        ? isset($v['vemp'][$lado]['decidido'])
        : !empty($v['vemp'][$lado]['decidido']);
    ?>
    <label class="inline-check" style="margin-left:0;">
        <input type="checkbox" value="1" name="vemp[<?= $lado ?>][decidido]" <?= $vempDecidido ? 'checked' : '' ?>>
        Ya decidí qué pasa en el VEMP de este oído
    </label>
    <p class="help">El editor reclama el VEMP de todo caso con patrón retrococlear cargado. Tildá esto cuando el VEMP normal <strong>sea</strong> la respuesta: es lo único que lo distingue de una ficha que nadie abrió, y sin la casilla el caso no se guarda. La tilda sola "Generar caso" (<a href="#" class="tab-link" data-goto-tab="armado">Armado rápido</a>).</p>

    <?php foreach (CaseBuilder::VEMP_SUBTIPOS as $subtipo):
        $def = CaseBuilder::VEMP_DEFAULTS[$subtipo];
        $sv = $v['vemp'][$lado][$subtipo] ?? [];
        // Sticky (POST): una casilla destildada no viaja, así que ahí manda
        // isset() y no el default. Con `?? '1'` un docente que destildaba
        // "reproducible" y se comía un error de validación lo encontraba
        // tildado de nuevo al redibujarse el formulario.
        $svRepro = $_SERVER['REQUEST_METHOD'] === 'POST'
            ? isset($sv['repro'])
            : (($sv['repro'] ?? '1') === '1');
    ?>
    <div class="side-block vemp-sub" data-lado="<?= $lado ?>" data-subtipo="<?= $subtipo ?>">
        <div class="side-heading"><strong><?= htmlspecialchars(CaseBuilder::VEMP_SUBTIPO_LABELS[$subtipo]) ?></strong></div>

        <div class="three-col">
            <label>Umbral (dB)
                <input type="number" step="5" class="vemp-input" name="vemp[<?= $lado ?>][<?= $subtipo ?>][umbral]" value="<?= htmlspecialchars((string) ($sv['umbral'] ?? $def['umbral'])) ?>">
            </label>
            <label>Promediaciones objetivo
                <input type="number" step="1" min="1" class="vemp-input" name="vemp[<?= $lado ?>][<?= $subtipo ?>][average_objetivo]" value="<?= htmlspecialchars((string) ($sv['average_objetivo'] ?? $def['average_objetivo'])) ?>">
            </label>
            <label>Jitter si no reproducible (ms)
                <input type="number" step="0.01" min="0" class="vemp-input" name="vemp[<?= $lado ?>][<?= $subtipo ?>][repro_var]" value="<?= htmlspecialchars((string) ($sv['repro_var'] ?? CaseBuilder::VEMP_REPRO_VAR_DEFAULT)) ?>">
            </label>
        </div>
        <label class="inline-check" style="margin-left:0;">
            <input type="checkbox" class="vemp-input" value="1" name="vemp[<?= $lado ?>][<?= $subtipo ?>][repro]" <?= $svRepro ? 'checked' : '' ?>>
            Reproducible
        </label>

        <p class="help">Desviaciones por pico (latencia ms / amplitud &micro;V) sobre lo que la normativa espera a 80 dB para la edad y el sexo del paciente.</p>
        <div class="three-col">
            <?php foreach (CaseBuilder::VEMP_PEAKS[$subtipo] as $pico): ?>
            <label><?= strtoupper($pico) ?> &mdash; latencia
                <input type="number" step="0.01" class="vemp-input" name="vemp[<?= $lado ?>][<?= $subtipo ?>][lat_<?= $pico ?>]" value="<?= htmlspecialchars((string) ($sv['lat_' . $pico] ?? '0')) ?>">
            </label>
            <label><?= strtoupper($pico) ?> &mdash; amplitud
                <input type="number" step="0.01" class="vemp-input" name="vemp[<?= $lado ?>][<?= $subtipo ?>][amp_<?= $pico ?>]" value="<?= htmlspecialchars((string) ($sv['amp_' . $pico] ?? '0')) ?>">
            </label>
            <?php endforeach; ?>
        </div>

        <div class="vemp-preview" data-lado="<?= $lado ?>" data-subtipo="<?= $subtipo ?>"></div>
    </div>
    <?php endforeach; ?>
</div>
<?php endforeach; ?>
</div>
</div>
