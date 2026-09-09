<?php
/**
 * Ficha 9 -- VEMP: subtipo, patología y picos por oído.
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
<div class="two-col">
<?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
<?php $vSubtipo = (string) ($v['vemp'][$lado]['subtipo'] ?? 'CVEMP'); ?>
<div class="card">
    <strong>VEMP <?= $ladoLabel ?></strong>
    <p class="help">Patología vestibular de este oído para el generador de VEMP. El subtipo define el músculo donde se mide y por lo tanto los picos que el alumno va a marcar (CVEMP cervical: P13/N23 sobre SCM; OVEMP ocular: N10/P16 sobre oblicuo inferior; MVEMP masetero: P13/N23 sobre masetero). Los 4 picos se rinden siempre; el cliente usa solo los del subtipo activo.</p>
    <div class="three-col">
        <label>Subtipo
            <select name="vemp[<?= $lado ?>][subtipo]" class="vemp-subtipo-select" data-lado="<?= $lado ?>">
                <?php foreach (CaseBuilder::VEMP_SUBTIPOS as $sub): ?>
                <option value="<?= $sub ?>" <?= $vSubtipo === $sub ? 'selected' : '' ?>><?= $sub ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Patología
            <select name="vemp[<?= $lado ?>][type]">
                <?php foreach (CaseBuilder::VEMP_TYPE_OPTIONS as $opt): ?>
                <option value="<?= $opt ?>" <?= ($v['vemp'][$lado]['type'] ?? 'normal') === $opt ? 'selected' : '' ?>><?= ucfirst($opt) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Umbral (dB)
            <input type="number" name="vemp[<?= $lado ?>][umbral]" value="<?= htmlspecialchars((string) ($v['vemp'][$lado]['umbral'] ?? '60')) ?>">
        </label>
        <label class="inline-check" style="align-self:end;">
            <input type="checkbox" name="vemp[<?= $lado ?>][repro]" <?= ($v['vemp'][$lado]['repro'] ?? '1') === '1' ? 'checked' : '' ?>>
            Reproducible
        </label>
        <label>Jitter si no reproducible (ms)
            <input type="number" step="0.01" min="0" name="vemp[<?= $lado ?>][repro_var]" value="<?= htmlspecialchars((string) ($v['vemp'][$lado]['repro_var'] ?? '0.2')) ?>">
        </label>
        <label>Promediaciones objetivo
            <input type="number" step="1" min="1" name="vemp[<?= $lado ?>][average_objetivo]" value="<?= htmlspecialchars((string) ($v['vemp'][$lado]['average_objetivo'] ?? '200')) ?>">
        </label>
    </div>
    <p class="help">Desviaciones por pico (latencia ms / amplitud µV) -- valores absolutos que el generador espera a 80 dB. Los picos irrelevantes para el subtipo activo se guardan igual pero el cliente los ignora.</p>
    <div class="three-col">
        <?php
        $vempWaveFields = [
            ['p13', 'lat', 'P13 -- latencia'], ['p13', 'amp', 'P13 -- amplitud'],
            ['n23', 'lat', 'N23 -- latencia'], ['n23', 'amp', 'N23 -- amplitud'],
            ['n10', 'lat', 'N10 -- latencia'], ['n10', 'amp', 'N10 -- amplitud'],
            ['p16', 'lat', 'P16 -- latencia'], ['p16', 'amp', 'P16 -- amplitud'],
        ];
        foreach ($vempWaveFields as [$vempWave, $vempField, $vempLabel]):
            $vempName = $vempField . '_' . $vempWave;
        ?>
        <label><?= $vempLabel ?>
            <input type="number" step="0.01" name="vemp[<?= $lado ?>][<?= $vempName ?>]" value="<?= htmlspecialchars((string) ($v['vemp'][$lado][$vempName] ?? '0')) ?>">
        </label>
        <?php endforeach; ?>
    </div>
</div>
<?php endforeach; ?>
</div>
</div>
