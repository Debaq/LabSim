<?php
/**
 * Ficha 4 -- Audiometría: tonal, acumetría, supraliminares, deterioro y Fowler.
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
<div class="tab-panel" data-tab="audiometria">
<div class="audiometria-layout">

<div class="audiogram-stack">
<div class="audiogram-card card">
    <strong>Audiograma</strong>
    <svg id="audiogram-svg" viewBox="0 0 320 300" style="width:100%; height:auto; margin-top:0.5rem;">
        <rect x="32" y="10" width="280" height="266" fill="none" stroke="#ccc"></rect>
        <?php
        // La audición normal llega hasta 20 dB HL inclusive (por eso el grado
        // leve arranca en 21, ver CaseProfile::GRADES): esa línea va gruesa,
        // porque es la que se busca primero al leer un audiograma. Lo mismo
        // hace el PDF de la ficha (CaseCharts::LIMITE_NORMALIDAD_DB).
        $limiteNormal = CaseProfile::GRADES['leve']['rango'][0] - 1;
        foreach ([0, 20, 40, 60, 80, 100, 120] as $db):
            $y = audiogram_y($db);
            $esLimite = $db === $limiteNormal;
        ?>
        <line x1="32" y1="<?= $y ?>" x2="312" y2="<?= $y ?>" stroke="<?= $esLimite ? '#555' : '#eee' ?>" stroke-width="<?= $esLimite ? '1.6' : '1' ?>"></line>
        <text x="28" y="<?= $y + 3 ?>" text-anchor="end" font-size="8" fill="<?= $esLimite ? '#555' : '#666' ?>"<?= $esLimite ? ' font-weight="bold"' : '' ?>><?= $db ?></text>
        <?php endforeach; ?>
        <?php
        $freqLabels = [125 => '125', 250 => '250', 500 => '500', 1000 => '1K', 2000 => '2K', 3000 => '3K', 4000 => '4K', 6000 => '6K', 8000 => '8K'];
        foreach (CaseBuilder::FREQUENCIES as $freq):
            $x = audiogram_x($freq);
        ?>
        <line x1="<?= $x ?>" y1="10" x2="<?= $x ?>" y2="276" stroke="#f2f2f2"></line>
        <text x="<?= $x ?>" y="288" text-anchor="middle" font-size="8" fill="#666"><?= $freqLabels[$freq] ?></text>
        <?php endforeach; ?>
        <text x="4" y="14" font-size="8" fill="#888">dB HL</text>
        <g id="audiogram-data"></g>
    </svg>
    <div class="audiogram-legend">
        <span><svg width="12" height="12"><circle cx="6" cy="6" r="4" fill="none" class="sym-od" stroke-width="1.4"></circle></svg> Aérea OD</span>
        <span><svg width="12" height="12"><polygon points="6,2 2,10 10,10" fill="none" class="sym-od" stroke-width="1.4"></polygon></svg> Aérea OD enmasc.</span>
        <span><svg width="12" height="12"><line x1="2" y1="2" x2="10" y2="10" class="sym-oi" stroke-width="1.4"></line><line x1="2" y1="10" x2="10" y2="2" class="sym-oi" stroke-width="1.4"></line></svg> Aérea OI</span>
        <span><svg width="12" height="12"><rect x="2" y="2" width="8" height="8" fill="none" class="sym-oi" stroke-width="1.4"></rect></svg> Aérea OI enmasc.</span>
        <span><svg width="12" height="12"><polyline points="9,2 3,6 9,10" fill="none" class="sym-od" stroke-width="1.4"></polyline></svg> Ósea OD</span>
        <span><svg width="12" height="12"><polyline points="8,2 3,2 3,10 8,10" fill="none" class="sym-od" stroke-width="1.4"></polyline></svg> Ósea OD enmasc.</span>
        <span><svg width="12" height="12"><polyline points="3,2 9,6 3,10" fill="none" class="sym-oi" stroke-width="1.4"></polyline></svg> Ósea OI</span>
        <span><svg width="12" height="12"><polyline points="4,2 9,2 9,10 4,10" fill="none" class="sym-oi" stroke-width="1.4"></polyline></svg> Ósea OI enmasc.</span>
        <span><svg width="12" height="12"><polygon points="7,3 7,9 2,9" class="sym-od-fill" stroke="none"></polygon></svg> LDL OD</span>
        <span><svg width="12" height="12"><polygon points="5,3 5,9 10,9" class="sym-oi-fill" stroke="none"></polygon></svg> LDL OI</span>
    </div>
</div>

<div class="audiogram-card card">
    <strong>Logoaudiograma</strong>
    <svg id="logogram-svg" viewBox="0 0 320 300" style="width:100%; height:auto; margin-top:0.5rem;">
        <rect x="32" y="10" width="280" height="266" fill="none" stroke="#ccc"></rect>
        <?php foreach ([0, 20, 40, 60, 80, 100] as $pct):
            $y = logogram_y($pct);
        ?>
        <line x1="32" y1="<?= $y ?>" x2="312" y2="<?= $y ?>" stroke="#eee"></line>
        <text x="28" y="<?= $y + 3 ?>" text-anchor="end" font-size="8" fill="#666"><?= $pct ?></text>
        <?php endforeach; ?>
        <?php foreach ([-10, 0, 20, 40, 60, 80, 100, 120] as $db):
            $x = logogram_x($db);
        ?>
        <line x1="<?= $x ?>" y1="10" x2="<?= $x ?>" y2="276" stroke="#f2f2f2"></line>
        <text x="<?= $x ?>" y="288" text-anchor="middle" font-size="8" fill="#666"><?= $db ?></text>
        <?php endforeach; ?>
        <text x="4" y="14" font-size="8" fill="#888">%</text>
        <text x="270" y="288" font-size="8" fill="#888">dB HL</text>
        <g id="logogram-data"></g>
    </svg>
    <div class="audiogram-legend">
        <span><svg width="12" height="12"><circle cx="6" cy="6" r="3" class="sym-od-fill" stroke="none"></circle></svg> SDT OD</span>
        <span><svg width="12" height="12"><circle cx="6" cy="6" r="3" class="sym-oi-fill" stroke="none"></circle></svg> SDT OI</span>
        <span><svg width="12" height="12"><line x1="6" y1="1" x2="6" y2="11" class="sym-od" stroke-width="1.4" stroke-dasharray="2,2"></line></svg> SRT OD</span>
        <span><svg width="12" height="12"><line x1="6" y1="1" x2="6" y2="11" class="sym-oi" stroke-width="1.4" stroke-dasharray="2,2"></line></svg> SRT OI</span>
        <span><svg width="12" height="12"><polygon points="6,2 2,10 10,10" class="sym-od-fill" stroke="none"></polygon></svg> UMD OD</span>
        <span><svg width="12" height="12"><polygon points="6,2 2,10 10,10" class="sym-oi-fill" stroke="none"></polygon></svg> UMD OI</span>
    </div>
</div>
</div>

<div class="audiometria-fields">
<?php $seriesShort = ['aerea' => 'Aérea', 'osea' => 'Ósea', 'ldl' => 'LDL']; ?>
<div class="card">
    <strong>Umbrales tonales</strong>
    <?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
    <div class="side-block">
        <div class="side-heading">
            <span class="side-tag <?= $lado ?>"><?= $ladoLabel ?></span>
            <label class="inline-check"><input type="checkbox" class="igualar-toggle" data-side="<?= $lado ?>" name="igualar[<?= $lado ?>]" <?= isset($v['igualar'][$lado]) ? 'checked' : '' ?>> Igualar ósea a aérea</label>
            <label class="inline-check"><input type="checkbox" class="ldl-toggle" data-side="<?= $lado ?>" name="ldl_habilitado[<?= $lado ?>]" <?= isset($v['ldl_habilitado'][$lado]) ? 'checked' : '' ?>> LDL medido</label>
        </div>
        <div class="table-wrap">
        <table class="grid-table">
            <tr><th></th><?php foreach (CaseBuilder::FREQUENCIES as $f): ?><th><?= $f ?> Hz</th><?php endforeach; ?></tr>
            <?php foreach ($seriesShort as $key => $label): ?>
            <tr>
                <td class="side-label"><?= $label ?></td>
                <?php foreach (CaseBuilder::FREQUENCIES as $n => $freq):
                    $default = $key === 'ldl' ? 130 : 0;
                    $val = fv($v, [$key, $lado, (string) $n], $default);
                ?>
                <td><input type="number" step="5" min="-10" max="130"
                           id="<?= $key ?>_<?= $lado ?>_<?= $n ?>"
                           name="<?= $key ?>[<?= $lado ?>][<?= $n ?>]"
                           value="<?= htmlspecialchars((string) $val) ?>"></td>
                <?php endforeach; ?>
            </tr>
            <?php endforeach; ?>
        </table>
        </div>
    </div>
    <?php endforeach; ?>
    <p class="help">LDL sin marcar = no medido, se guarda como ausente (130) sin importar lo que quede escrito arriba.</p>
</div>

<div class="card">
    <strong>Acumetría (Rinne / Weber) &mdash; diapasones 500 y 1000 Hz</strong>
    <?php
    // Sticky (POST): checked solo si vino tildado en el submit. Nuevo/editar
    // (GET): default tildado salvo que caseDataToForm() ya haya puesto '' (edición).
    $acumetriaIsAuto = $_SERVER['REQUEST_METHOD'] === 'POST'
        ? isset($v['acumetria_auto'])
        : (!isset($v['acumetria_auto']) || (bool) $v['acumetria_auto']);
    ?>
    <p class="help">
        <label class="inline-check"><input type="checkbox" id="acumetria-auto-toggle" name="acumetria_auto" value="1"
               <?= $acumetriaIsAuto ? 'checked' : '' ?>>auto (calcular Rinne y Weber desde los umbrales tonales)</label>
    </p>
    <?php // Las 6 celdas quedan EDITABLES con el auto encendido, igual que el
          // resto de lo que sugiere el formulario: el auto muestra el cálculo,
          // no lo impone. Estaban con `disabled` mientras el auto estuviera
          // tildado, y al destildarlo nadie las volvía a habilitar: quedaban
          // muertas hasta recargar la página. ?>
    <p class="help">Con <em>auto</em> encendido se escriben solas desde los umbrales y <strong>se pueden editar</strong>: lo que quede en pantalla es lo que se guarda. Volver a tocar un umbral las recalcula y pisa lo editado a mano; para que no se toquen más, apagar la casilla.</p>
    <div class="table-wrap">
    <table class="grid-table" style="margin-bottom:0.5rem;">
        <tr><th></th><?php foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx): ?><th><?= $hz ?> Hz</th><?php endforeach; ?></tr>
        <?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
        <tr>
            <td class="side-label">Rinne <?= $ladoLabel ?></td>
            <?php foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx):
                $rinneVal = (string) fv($v, ['rinne', $hz, $lado], 'positivo');
            ?>
            <td>
                <select id="rinne_<?= $freqIdx ?>_<?= $lado ?>" class="rinne-select" data-freq="<?= $freqIdx ?>" data-side="<?= $lado ?>"
                        name="rinne[<?= $hz ?>][<?= $lado ?>]">
                    <?php foreach (CaseBuilder::RINNE_LABELS as $opt => $optLabel): ?>
                    <option value="<?= $opt ?>" <?= $rinneVal === $opt ? 'selected' : '' ?>><?= htmlspecialchars($optLabel) ?></option>
                    <?php endforeach; ?>
                </select>
            </td>
            <?php endforeach; ?>
        </tr>
        <?php endforeach; ?>
        <tr>
            <td class="side-label">Weber</td>
            <?php foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx):
                $weberVal = (string) fv($v, ['weber', $hz], 'centrado');
            ?>
            <td>
                <select id="weber_<?= $freqIdx ?>" class="weber-select" data-freq="<?= $freqIdx ?>"
                        name="weber[<?= $hz ?>]">
                    <?php foreach (CaseBuilder::WEBER_LABELS as $opt => $optLabel): ?>
                    <option value="<?= $opt ?>" <?= $weberVal === $opt ? 'selected' : '' ?>><?= htmlspecialchars($optLabel) ?></option>
                    <?php endforeach; ?>
                </select>
            </td>
            <?php endforeach; ?>
        </tr>
    </table>
    </div>
</div>

<div class="card">
    <strong>Logoaudiometría y pruebas especiales</strong>
    <p class="derivado-aviso" data-derivado="logo" hidden>La máxima discriminación (UMD) y a qué intensidad se alcanza las sugiere el <a href="#" class="tab-link" data-goto-tab="perfil">Perfil auditivo</a>, porque la casilla <em>Logoaudiometría</em> está encendida: se escriben solos con lo que predice el perfil y <strong>se pueden editar</strong>: lo que quede en pantalla es lo que se guarda. Cambiar el audiograma o el perfil vuelve a sugerir y pisa lo editado a mano; para que no se toquen más, apagar esa casilla.</p>
    <p class="derivado-aviso" data-derivado="recruit" hidden>El SISI, el reclutamiento, el Fowler, el deterioro tonal y el LDL los sugiere el <a href="#" class="tab-link" data-goto-tab="perfil">Perfil auditivo</a>, porque la casilla <em>Supraliminares</em> está encendida: se escriben solos con lo que predice el perfil y <strong>se pueden editar</strong>: lo que quede en pantalla es lo que se guarda. Cambiar el audiograma o el perfil vuelve a sugerir y pisa lo editado a mano; para que no se toquen más, apagar esa casilla.</p>
    <div class="table-wrap">
    <table class="grid-table" style="margin-bottom:1rem;">
        <tr><th></th><th>SDT</th><th>SRT</th></tr>
        <?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
        <tr>
            <td class="side-label"><?= $ladoLabel ?></td>
            <td>
                <input type="number" step="5" class="sdt-input" data-side="<?= $lado ?>" name="sdt[<?= $lado ?>]" value="<?= htmlspecialchars((string) fv($v, ['sdt', $lado], 0)) ?>">
                <label class="inline-check"><input type="checkbox" class="auto-toggle" data-target="sdt-input" data-side="<?= $lado ?>" name="sdt_auto[<?= $lado ?>]" <?= !isset($v['sdt_auto']) || isset($v['sdt_auto'][$lado]) ? 'checked' : '' ?>>auto (Fletcher)</label>
            </td>
            <td>
                <input type="number" step="5" class="srt-input" data-side="<?= $lado ?>" name="srt[<?= $lado ?>]" value="<?= htmlspecialchars((string) fv($v, ['srt', $lado], 0)) ?>">
                <label class="inline-check"><input type="checkbox" class="auto-toggle" data-target="srt-input" data-side="<?= $lado ?>" name="srt_auto[<?= $lado ?>]" <?= !isset($v['srt_auto']) || isset($v['srt_auto'][$lado]) ? 'checked' : '' ?>>auto (Fletcher)</label>
            </td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>

    <div class="two-col">
        <?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
        <div class="side-block">
            <div class="side-heading"><span class="side-tag <?= $lado ?>"><?= $ladoLabel ?></span></div>
            <label>UMD (int / %)
                <input type="number" step="5" class="umd-int-input input input--narrow" data-side="<?= $lado ?>" name="umd_int[<?= $lado ?>]" value="<?= htmlspecialchars((string) fv($v, ['umd_int', $lado], 35)) ?>" style="display:inline-block;">
                / <input type="number" step="4" class="umd-pct-input input input--narrow" data-side="<?= $lado ?>" name="umd_pct[<?= $lado ?>]" value="<?= htmlspecialchars((string) fv($v, ['umd_pct', $lado], 100)) ?>" style="display:inline-block;">
            </label>
            <label>SISI <input type="number" step="5" name="sisi[<?= $lado ?>]" value="<?= htmlspecialchars((string) fv($v, ['sisi', $lado], 0)) ?>"></label>
            <label class="inline-check"><input type="checkbox" name="stenger[<?= $lado ?>]" <?= isset($v['stenger'][$lado]) ? 'checked' : '' ?>> Stenger</label>
            <label class="inline-check"><input type="checkbox" class="recruit-toggle" data-side="<?= $lado ?>" name="recruit[<?= $lado ?>]" <?= isset($v['recruit'][$lado]) ? 'checked' : '' ?>> Reclutamiento</label>
        </div>
        <?php endforeach; ?>
    </div>

    <p class="help">Deterioro tonal (Carhart / Stat / Rosemberg): dB que hay que subir sobre el umbral aéreo para que el oído sostenga el tono 1 minuto completo. Dejar en 0 equivale a no administrarla: en la ficha de estudio sale "/" en vez de un número. Si nunca alcanza a sostenerlo ni en el techo (salida máxima o LDL, lo que sea menor), pon un valor igual o mayor a ese rango.</p>
    <p class="help">Cada prueba usa ese número distinto, porque el software las administra como se administran de verdad: en el <b>Carhart</b> cada subida de 5 dB reinicia el minuto; en el <b>Rosemberg</b> el minuto es total y subir el nivel no devuelve tiempo, así que con el mismo valor el alumno llega más arriba en dB; el <b>Stat</b> se administra a un nivel fijo de 100 dB HL con ruido blanco contralateral, sin escalar, así que ahí el valor solo decide si el oído aguanta el minuto a ese nivel (queda positivo si supera 100 dB HL menos el umbral aéreo).</p>
    <?php
    $decayGroups = [
        'carhart' => ['label' => 'Carhart', 'freqs' => [500, 1000, 2000, 4000]],
        'stat' => ['label' => 'Stat', 'freqs' => [500, 1000, 2000]],
        'rosemberg' => ['label' => 'Rosemberg', 'freqs' => [500, 1000, 2000, 4000]],
    ];
    foreach ($decayGroups as $mode => $info):
    ?>
    <div class="table-wrap">
    <table class="grid-table" style="margin-bottom:0.5rem;">
        <tr><th class="side-label"><?= htmlspecialchars($info['label']) ?></th><?php foreach ($info['freqs'] as $f): ?><th><?= $f ?> Hz</th><?php endforeach; ?></tr>
        <?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
        <tr>
            <td class="side-label"><?= $ladoLabel ?></td>
            <?php foreach ($info['freqs'] as $n => $f): ?>
            <td><input type="number" step="5" min="0" name="<?= $mode ?>[<?= $lado ?>][<?= $n ?>]" value="<?= htmlspecialchars((string) fv($v, [$mode, $lado, (string) $n], 0)) ?>"></td>
            <?php endforeach; ?>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php endforeach; ?>

    <?php
    // Render-time: recalcula qué frecuencias califican para Fowler a partir
    // de los umbrales ya tipeados en $v (sticky POST o precarga de edición).
    // Independiente del bloque de procesamiento de arriba (que solo corre
    // en submit) -- esto es lo que se ve al cargar/editar el form.
    $fwAerea = ['od' => [], 'oi' => []];
    $fwOsea = ['od' => [], 'oi' => []];
    foreach (['od', 'oi'] as $fwSide) {
        foreach (CaseBuilder::FREQUENCIES as $fwN => $fwFreq) {
            $fwAerea[$fwSide][] = (int) fv($v, ['aerea', $fwSide, (string) $fwN], 0);
            $fwOsea[$fwSide][] = (int) fv($v, ['osea', $fwSide, (string) $fwN], 0);
        }
    }
    $fwAirPairs = zip_pairs($fwAerea['od'], $fwAerea['oi']);
    $fwBonePairs = zip_pairs($fwOsea['od'], $fwOsea['oi']);
    $fwQualifying = CaseBuilder::fowlerQualifyingFreqs($fwAirPairs, $fwBonePairs);
    ?>
    <div class="side-block" id="fowler-block">
        <div class="side-heading"><span class="side-tag">Fowler</span></div>
        <p class="help">Se detectan solas las frecuencias (250-4000 Hz) donde los umbrales ya tipeados arriba cumplen los requisitos ABLB -- puede calificar más de una a la vez. Para cada una, indica qué le pasa al paciente al hacer la prueba ahí (por defecto, sin reclutamiento).</p>
        <div class="table-wrap">
        <table class="grid-table" id="fowler-table" <?= $fwQualifying ? '' : 'hidden' ?>>
            <thead>
                <tr><th>Frecuencia</th><th>Diferencia interaural</th><th>Patrón</th></tr>
            </thead>
            <tbody id="fowler-rows">
                <?php foreach ($fwQualifying as $fwFreqIdx):
                    $fwAir = $fwAirPairs[$fwFreqIdx];
                    $fwDiff = abs($fwAir[0] - $fwAir[1]);
                    $fwSelected = (string) fv($v, ['fowler_pattern', (string) $fwFreqIdx], 'none');
                ?>
                <tr data-freq="<?= $fwFreqIdx ?>">
                    <td><?= CaseBuilder::FREQUENCIES[$fwFreqIdx] ?> Hz</td>
                    <td><?= $fwDiff ?> dB</td>
                    <td>
                        <select name="fowler_pattern[<?= $fwFreqIdx ?>]" data-freq="<?= $fwFreqIdx ?>">
                            <?php foreach (CaseBuilder::FOWLER_PATTERN_LABELS as $fwKey => $fwLabel): ?>
                            <option value="<?= $fwKey ?>" <?= $fwSelected === $fwKey ? 'selected' : '' ?>><?= $fwLabel ?></option>
                            <?php endforeach; ?>
                        </select>
                    </td>
                </tr>
                <?php endforeach; ?>
            </tbody>
        </table>
        </div>
        <p class="help" id="fowler-none-msg" <?= $fwQualifying ? 'hidden' : '' ?>>Ningún umbral actual cumple los requisitos ABLB -- Fowler queda deshabilitado en este caso.</p>
        <label class="inline-check"><input type="checkbox" name="diplacusia" <?= isset($v['diplacusia']) ? 'checked' : '' ?>> Paciente refiere diploacusia</label>
        <p class="help">Requisitos ABLB: oído de referencia ≤ <?= CaseBuilder::FOWLER_NORMAL_HL ?> dB HL, oído en estudio &gt; <?= CaseBuilder::FOWLER_NORMAL_HL ?> dB HL y sensorioneural (gap aéreo-óseo ≤ <?= CaseBuilder::FOWLER_SNHL_GAP_MAX ?> dB), diferencia interaural <?= CaseBuilder::FOWLER_DIFF_MIN ?>-<?= CaseBuilder::FOWLER_DIFF_MAX ?> dB en cada frecuencia evaluada.</p>
        <p class="help">Sin reclutamiento = el paciente nunca iguala. Parcial = se acerca pero no cierra del todo. Completo = iguala sonoridad. Sobre-reclutamiento = en niveles altos el oído afectado empieza a sonar más fuerte que el sano.</p>
    </div>
    <p class="help">Auto (SDT/SRT) = mejor promedio de 2 de 3 (500/1000/2000 Hz vía aérea), redondeado a múltiplo de 5. Destildar para escribir un valor manual.</p>
</div>
</div>

</div>
</div>
