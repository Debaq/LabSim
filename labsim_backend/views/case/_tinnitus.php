<?php
/**
 * Ficha 10 -- Tinnitus: lateralidad, forma y acufenometría.
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
<div class="tab-panel" data-tab="tinnitus">
<div class="card">
    <strong>Tinnitus (acufenometría)</strong>
    <p class="help">La mayoría de los pacientes no tiene acúfeno: la ficha arranca sin tinnitus y hay que marcarlo para que aparezca. Sin la casilla, el paciente responde que no escucha ruidos ni pitidos y la acufenometría no es parte del caso.</p>
    <label class="inline-check" style="margin-left:0;">
        <input type="checkbox" id="tinnitus-presente" name="tinnitus[presente]" value="1" <?= !empty($v['tinnitus']['presente']) ? 'checked' : '' ?>>
        Este paciente tiene tinnitus
    </label>
    <div id="tinnitus-campos">
    <p class="help">Lateralidad y permanente/ocasional son independientes (un tinnitus unilateral puede ser permanente igual que uno bilateral). Unilateral pide oído; bilateral admite predominio (asimetría). Forma: tipo de ruido + frecuencia de matching.</p>
    <?php $tinLateralidad = $v['tinnitus']['lateralidad'] ?? 'craneal'; ?>
    <div class="two-col">
        <label>Lateralidad
            <select id="tinnitus-lateralidad" name="tinnitus[lateralidad]">
                <?php $lateralidadLabels = ['craneal' => 'Craneal', 'unilateral' => 'Unilateral', 'bilateral' => 'Bilateral']; ?>
                <?php foreach ($lateralidadLabels as $opt => $optLabel): ?>
                <option value="<?= $opt ?>" <?= $tinLateralidad === $opt ? 'selected' : '' ?>><?= $optLabel ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label class="inline-check" style="margin-top:1.4rem;"><input type="checkbox" name="tinnitus[pulsatil]" <?= isset($v['tinnitus']['pulsatil']) ? 'checked' : '' ?>> Pulsátil</label>
        <label class="inline-check" style="margin-top:1.4rem;"><input type="checkbox" name="tinnitus[permanente]" <?= isset($v['tinnitus']['permanente']) ? 'checked' : '' ?>> Permanente (sin marcar = ocasional)</label>
    </div>
    <div class="two-col" style="margin-top:0.6rem;">
        <label id="tinnitus-oido-field" data-show-for="unilateral">Oído
            <select name="tinnitus[oido]">
                <?php foreach (CaseBuilder::LADOS as $opt => $optLabel): ?>
                <option value="<?= $opt ?>" <?= ($v['tinnitus']['oido'] ?? 'od') === $opt ? 'selected' : '' ?>><?= $optLabel ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label id="tinnitus-predominio-field" data-show-for="bilateral">Predominio
            <select name="tinnitus[predominio]">
                <?php $predominioLabels = ['igual' => 'Igual en ambos', 'od' => 'Mayor en OD', 'oi' => 'Mayor en OI']; ?>
                <?php foreach ($predominioLabels as $opt => $optLabel): ?>
                <option value="<?= $opt ?>" <?= ($v['tinnitus']['predominio'] ?? 'igual') === $opt ? 'selected' : '' ?>><?= $optLabel ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Ruido
            <select name="tinnitus[ruido]">
                <?php foreach (CaseBuilder::TINNITUS_RUIDO_OPTIONS as $opt): ?>
                <option value="<?= $opt ?>" <?= ($v['tinnitus']['ruido'] ?? CaseBuilder::TINNITUS_RUIDO_OPTIONS[0]) === $opt ? 'selected' : '' ?>><?= htmlspecialchars($opt) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Frecuencia (Hz, matching)
            <select name="tinnitus[frecuencia]">
                <?php foreach (CaseBuilder::FREQUENCIES as $freq): ?>
                <option value="<?= $freq ?>" <?= (int) ($v['tinnitus']['frecuencia'] ?? CaseBuilder::FREQUENCIES[0]) === $freq ? 'selected' : '' ?>><?= $freq ?> Hz</option>
                <?php endforeach; ?>
            </select>
        </label>
    </div>
    <p class="help" style="margin-top:0.8rem;">Tinnitumetría en el audiómetro: lo que responde el paciente. Vacío o <em>Auto</em> = la app lo sortea al abrir el caso y queda fijo para ese paciente (sonoridad de 2 a 10 dB SL; NME de 5 a 15 dB sobre la sonoridad; inhibición negativa, parcial o total). Los dB SL son sobre el umbral aéreo del oído y la frecuencia donde se mide.</p>
    <div class="two-col">
        <label>Sonoridad (dB SL, vacío = sortear)
            <input type="number" min="0" max="<?= CaseBuilder::TINNITUS_SONORIDAD_MAX_SL ?>" step="1" name="tinnitus[sonoridad_sl]" value="<?= htmlspecialchars((string) ($v['tinnitus']['sonoridad_sl'] ?? '')) ?>" placeholder="Auto">
        </label>
        <label>Nivel mínimo de enmascaramiento (dB SL, vacío = sortear)
            <input type="number" min="0" max="<?= CaseBuilder::TINNITUS_NME_MAX_SL ?>" step="1" name="tinnitus[nme_sl]" value="<?= htmlspecialchars((string) ($v['tinnitus']['nme_sl'] ?? '')) ?>" placeholder="Auto">
        </label>
        <label>Inhibición residual
            <select name="tinnitus[inhibicion]">
                <?php foreach (CaseBuilder::TINNITUS_INHIBICION_OPTIONS as $opt => $optLabel): ?>
                <option value="<?= $opt ?>" <?= ($v['tinnitus']['inhibicion'] ?? 'auto') === $opt ? 'selected' : '' ?>><?= htmlspecialchars($optLabel) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>¿La inhibición dura un minuto más?
            <select name="tinnitus[inhibicion_mantiene]">
                <?php foreach (CaseBuilder::TINNITUS_MANTIENE_OPTIONS as $opt => $optLabel): ?>
                <option value="<?= $opt ?>" <?= ($v['tinnitus']['inhibicion_mantiene'] ?? 'auto') === $opt ? 'selected' : '' ?>><?= htmlspecialchars($optLabel) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
    </div>
    </div>
</div>
</div>
