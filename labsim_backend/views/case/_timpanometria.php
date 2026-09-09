<?php
/**
 * Ficha 6 -- Timpanometría: curva, ETF y reflejos.
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
<div class="tab-panel" data-tab="timpanometria">
<div class="audiometria-layout">

<div class="audiogram-stack">
<div class="audiogram-card card">
    <strong>Timpanograma</strong>
    <svg id="tympanogram-svg" viewBox="0 0 320 300" style="width:100%; height:auto; margin-top:0.5rem;">
        <rect x="32" y="10" width="280" height="266" fill="none" stroke="#ccc"></rect>
        <?php foreach ([0, 0.5, 1, 1.5, 2, 2.5] as $c):
            $y = tymp_y($c);
        ?>
        <line x1="32" y1="<?= $y ?>" x2="312" y2="<?= $y ?>" stroke="#eee"></line>
        <text x="28" y="<?= $y + 3 ?>" text-anchor="end" font-size="8" fill="#666"><?= $c ?></text>
        <?php endforeach; ?>
        <?php foreach ([-400, -300, -200, -100, 0, 100, 200] as $p):
            $x = tymp_x($p);
        ?>
        <line x1="<?= $x ?>" y1="10" x2="<?= $x ?>" y2="276" stroke="#f2f2f2"></line>
        <text x="<?= $x ?>" y="288" text-anchor="middle" font-size="8" fill="#666"><?= $p ?></text>
        <?php endforeach; ?>
        <text x="4" y="14" font-size="8" fill="#888">mL</text>
        <text x="270" y="288" font-size="8" fill="#888">daPa</text>
        <g id="tympanogram-data"></g>
    </svg>
    <div class="audiogram-legend">
        <span><svg width="12" height="12"><line x1="1" y1="6" x2="11" y2="6" class="sym-od" stroke-width="1.6"></line></svg> OD</span>
        <span><svg width="12" height="12"><line x1="1" y1="6" x2="11" y2="6" class="sym-oi" stroke-width="1.6"></line></svg> OI</span>
    </div>
</div>

<div class="audiogram-card card">
    <strong>Patrón de reflejos</strong>
    <?php
    // Filas de frecuencia: ipsi solo tiene 500/1000/2000/4000 (índices 0-3),
    // WN es exclusivo de contra (índice 4) -- las celdas ipsi de esa fila
    // quedan marcadas "n/a" (no existe ese dato).
    $reflexPatternRows = [
        ['label' => '500 Hz', 'n' => 0, 'hasIpsi' => true],
        ['label' => '1000 Hz', 'n' => 1, 'hasIpsi' => true],
        ['label' => '2000 Hz', 'n' => 2, 'hasIpsi' => true],
        ['label' => '4000 Hz', 'n' => 3, 'hasIpsi' => true],
        ['label' => 'WN', 'n' => 4, 'hasIpsi' => false],
    ];
    ?>
    <div class="table-wrap">
    <table class="reflex-pattern-table">
        <tr>
            <th class="reflex-head od">OD Contra</th>
            <th class="reflex-head od">OD Ipsi</th>
            <th>Frec.</th>
            <th class="reflex-head oi">OI Ipsi</th>
            <th class="reflex-head oi">OI Contra</th>
        </tr>
        <?php foreach ($reflexPatternRows as $row): ?>
        <tr>
            <td class="reflex-cell" data-mode="contra" data-side="od" data-n="<?= $row['n'] ?>"></td>
            <?php if ($row['hasIpsi']): ?>
            <td class="reflex-cell" data-mode="ipsi" data-side="od" data-n="<?= $row['n'] ?>"></td>
            <?php else: ?>
            <td class="reflex-cell na">&mdash;</td>
            <?php endif; ?>
            <td class="freq-label"><?= htmlspecialchars($row['label']) ?></td>
            <?php if ($row['hasIpsi']): ?>
            <td class="reflex-cell" data-mode="ipsi" data-side="oi" data-n="<?= $row['n'] ?>"></td>
            <?php else: ?>
            <td class="reflex-cell na">&mdash;</td>
            <?php endif; ?>
            <td class="reflex-cell" data-mode="contra" data-side="oi" data-n="<?= $row['n'] ?>"></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>

</div>
</div>

<div class="audiometria-fields">
<div class="card">
    <strong>Timpanometría (Z)</strong>
    <div class="two-col">
        <label>Z OD
            <select id="z_od" name="z_od">
                <?php foreach (CaseBuilder::Z_OPTIONS as $opt): ?>
                <option value="<?= $opt ?>" <?= ($v['z_od'] ?? 'A') === $opt ? 'selected' : '' ?>><?= $opt ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Z OI
            <select id="z_oi" name="z_oi">
                <?php foreach (CaseBuilder::Z_OPTIONS as $opt): ?>
                <option value="<?= $opt ?>" <?= ($v['z_oi'] ?? 'A') === $opt ? 'selected' : '' ?>><?= $opt ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>ETF OD
            <select name="etf_od">
                <?php foreach (CaseBuilder::ETF_OPTIONS as $opt): ?>
                <option value="<?= $opt ?>" <?= ($v['etf_od'] ?? 'Normal') === $opt ? 'selected' : '' ?>><?= $opt ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>ETF OI
            <select name="etf_oi">
                <?php foreach (CaseBuilder::ETF_OPTIONS as $opt): ?>
                <option value="<?= $opt ?>" <?= ($v['etf_oi'] ?? 'Normal') === $opt ? 'selected' : '' ?>><?= $opt ?></option>
                <?php endforeach; ?>
            </select>
        </label>
    </div>
</div>

<div class="card">
    <strong>Reflejos acústicos (dB HL, 130 = ausente)</strong>
    <p class="derivado-aviso" data-derivado="reflex" hidden>Los umbrales y el tipo de curva los sugiere el <a href="#" class="tab-link" data-goto-tab="perfil">Perfil auditivo</a>, porque la casilla <em>Reflejos acústicos</em> está encendida: se escriben solos con lo que predice el perfil y <strong>se pueden editar</strong>: lo que quede en pantalla es lo que se guarda. Cambiar el audiograma o el perfil vuelve a sugerir y pisa lo editado a mano; para que no se toquen más, apagar esa casilla.</p>
    <?php
    $reflexGroups = ['ipsi' => ['label' => 'Ipsilateral', 'freqs' => [500, 1000, 2000, 4000]],
                      'contra' => ['label' => 'Contralateral', 'freqs' => [500, 1000, 2000, 4000, 'WN']]];
    foreach ($reflexGroups as $mode => $info):
    ?>
    <div class="table-wrap">
    <table class="grid-table">
        <tr><th class="side-label"><?= htmlspecialchars($info['label']) ?></th><?php foreach ($info['freqs'] as $f): ?><th><?= is_int($f) ? $f . ' Hz' : $f ?></th><?php endforeach; ?></tr>
        <?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
        <tr>
            <td class="side-label"><?= $ladoLabel ?></td>
            <?php foreach ($info['freqs'] as $n => $f): ?>
            <td><input type="number" step="5" id="reflex_<?= $mode ?>_<?= $lado ?>_<?= $n ?>" name="reflex_<?= $mode ?>[<?= $lado ?>][<?= $n ?>]" value="<?= htmlspecialchars((string) fv($v, ['reflex_' . $mode, $lado, (string) $n], 130)) ?>"></td>
            <?php endforeach; ?>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php endforeach; ?>
    <div class="table-wrap">
    <table class="grid-table">
        <tr><th class="side-label">Tipo de reflejo</th><th>Curva</th></tr>
        <?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel):
            $reflexTypeSelected = (string) fv($v, ['reflex_type', $lado], 'normal');
        ?>
        <tr>
            <td class="side-label"><?= $ladoLabel ?></td>
            <td>
                <select id="reflex_type_<?= $lado ?>" name="reflex_type[<?= $lado ?>]">
                    <?php foreach (CaseBuilder::REFLEX_CURVE_LABELS as $typeKey => $typeLabel): ?>
                    <option value="<?= $typeKey ?>" <?= $reflexTypeSelected === $typeKey ? 'selected' : '' ?>><?= htmlspecialchars($typeLabel) ?></option>
                    <?php endforeach; ?>
                </select>
            </td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
</div>
</div>
</div>
</div>
