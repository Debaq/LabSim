<?php
/**
 * Ficha 3 -- Perfil auditivo: sitio de la lesión y qué módulos deriva.
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
<div class="tab-panel" data-tab="perfil">
<div class="card">
    <strong>Perfil auditivo</strong>
    <p class="help">Dónde está la lesión de este paciente. El audiograma (pestaña Audiometría) ya dice cuánta pérdida hay y cuánta es conductiva, frecuencia por frecuencia; lo único que no puede decir es qué parte del componente sensorioneural es coclear y qué parte es retrococlear. Eso se define acá, una vez, y desde acá se proyecta a los exámenes que tengan la casilla de derivación encendida.</p>
    <p class="help">Sin ninguna casilla marcada nada cambia: cada pestaña se sigue cargando a mano, como siempre. La derivación existe para que el caso no se contradiga solo (una OEA normal con un gap de 40 dB, un ABR normal con un audiograma profundo), no para impedir armar un caso incoherente a propósito -- el Stenger, la falsa onda V y la simulación necesitan esa incoherencia.</p>
    <p class="help">El cuadro clínico de cada oído (que escribe el audiograma, el sitio de la lesión, el timpanograma y estas mismas casillas) se genera desde <a href="#" class="tab-link" data-goto-tab="armado">Armado rápido</a>. Acá se edita el resultado, o se arma el perfil a mano.</p>

    <p class="help">Qué exámenes se derivan del perfil</p>
    <div class="three-col">
        <label class="inline-check">
            <input type="checkbox" id="perfil-auto-abr" name="perfil[auto][abr]" value="1" <?= fv($v, ['perfil', 'auto', 'abr'], null) ? 'checked' : '' ?>>
            ABR: umbral por estímulo
        </label>
        <label class="inline-check">
            <input type="checkbox" name="perfil[auto][eoas]" value="1" <?= fv($v, ['perfil', 'auto', 'eoas'], null) ? 'checked' : '' ?>>
            OEA: perfil por frecuencia
        </label>
        <label class="inline-check">
            <input type="checkbox" name="perfil[auto][reflex]" value="1" <?= fv($v, ['perfil', 'auto', 'reflex'], null) ? 'checked' : '' ?>>
            Reflejos acústicos
        </label>
        <label class="inline-check">
            <input type="checkbox" name="perfil[auto][recruit]" value="1" <?= fv($v, ['perfil', 'auto', 'recruit'], null) ? 'checked' : '' ?>>
            Supraliminares (Fowler, SISI, deterioro tonal, LDL)
        </label>
        <label class="inline-check">
            <input type="checkbox" name="perfil[auto][logo]" value="1" <?= fv($v, ['perfil', 'auto', 'logo'], null) ? 'checked' : '' ?>>
            Logoaudiometría (máxima discriminación)
        </label>
    </div>
    <p class="help">OEA: la atenuación pasa a salir del componente coclear y del gap, frecuencia por frecuencia. Reflejos: la sonda decide si el reflejo se ve (oído medio) y el oído estimulado a qué nivel aparece; una coclear no sube el umbral en proporción a la pérdida (Metz) y una retrococlear sí, y el patrón OFF --el reflejo que no se sostiene-- sale del componente retro. Supraliminares: reclutamiento, deterioro tonal y LDL miden el mismo eje desde tres lados, así que salen del mismo número y no pueden contradecirse; el LDL no sube con la pérdida coclear, y por eso el campo dinámico se cierra solo.</p>
    <p class="help">Logoaudiometría: la discriminación máxima cae despacio en una coclear y se desploma en una retrococlear, muy por debajo de lo que predice el audiograma -- es la disociación audio-verbal. El gap no la baja: una conductiva no distorsiona, solo pide más intensidad. El rollover (la curva que cae pasado el máximo) ya venía del reclutamiento.</p>
    <p class="help">El timpanograma no se deriva: qué curva sale depende de la patología concreta (B ocupación, As rígido, Ad hipercompliante, C retracción) y esa es una decisión clínica, no una cuenta. Lo que sí se hace es avisar si contradice al gap.</p>
</div>
<div class="card">
    <strong>Umbral por estímulo, derivado del audiograma</strong>
    <p class="help">Con esto encendido, el umbral del ABR deja de ser un número por oído y pasa a calcularse por estímulo desde la audiometría del caso: el burst de 500 Hz responde según el umbral en 500, el de 4 kHz según el de 4 kHz, el click según la base coclear (2-4 kHz) y el chirp con más peso en los graves. Es lo que permite pedir una evaluación frecuencia específica en una hipoacusia descendente. La vía ósea usa los umbrales óseos, así que el gap conductivo del ABR sale del audiograma solo.</p>
    <p class="help">Los números de la tabla están en dB nHL, no en dB HL: incluyen la corrección conductual-electrofisiológica (+20 dB en 500 Hz, +15 en 1 k, +10 en 2 k, +5 en 4 k, +10 el click, +5 el chirp). Por eso un oído de 0 dB HL igual muestra 20 dB nHL con burst de 500 -- convertir nHL a eHL es parte de lo que el alumno tiene que hacer.</p>
    <div id="abr-threshold-preview" hidden>
        <table class="reflex-pattern-table" style="margin-top:0.6rem;">
            <thead>
                <tr>
                    <th>Estímulo</th>
                    <th>OD aérea</th><th>OD ósea</th>
                    <th>OI aérea</th><th>OI ósea</th>
                </tr>
            </thead>
            <tbody id="abr-threshold-rows"></tbody>
        </table>
        <p class="help">El campo "Umbral (dB)" de cada oído queda de solo lectura: lo escribe esta tabla (con el valor del click, que es lo que mostraría un ABR de rutina).</p>
    </div>
</div>
<div class="two-col">
<?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
<div class="card">
    <strong>Oído <?= $ladoLabel ?></strong>
    <div class="three-col">
        <label>Proporción coclear del componente sensorioneural (%)
            <input type="number" step="5" min="0" max="100" name="perfil[<?= $lado ?>][cce_pct]" value="<?= htmlspecialchars((string) fv($v, ['perfil', $lado, 'cce_pct'], '100')) ?>">
        </label>
    </div>
    <p class="help">100 % = pérdida coclear pura: las células ciliadas externas están dañadas, la OEA cae con el umbral y hay reclutamiento. 0 % = pérdida retrococlear pura: la cóclea está viva, la OEA se conserva con el umbral elevado y el ABR es el que se desarma -- es la neuropatía auditiva, y ese contraste entre OEA y ABR es el hallazgo. Los valores intermedios reparten la pérdida entre los dos sitios.</p>
    <p class="help">Esto no toca el audiograma: la pérdida en dB la fija la pestaña Audiometría. Acá se dice de qué está hecha esa pérdida.</p>
    <?php $vn = $v['abr'][$lado]['neural'] ?? []; ?>
    <div class="abr-neural-block" data-lado="<?= $lado ?>">
        <p class="help">Patrón retrococlear. El PEATC no distingue las entidades entre sí (un schwannoma y un meningioma del ángulo dan el mismo trazado) -- lo que distingue son estos patrones, así que el caso guarda los números, no el diagnóstico. El preset es solo un punto de partida: precarga los valores y después se editan.</p>
        <div class="three-col">
            <label>Preset clínico
                <select class="abr-neural-preset-select" data-lado="<?= $lado ?>">
                    <option value="">-- elegir --</option>
                    <?php foreach (CaseBuilder::ABR_NEURAL_PRESETS as $presetKey => $preset): ?>
                    <option value="<?= $presetKey ?>"><?= htmlspecialchars($preset['label']) ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
            <label style="align-self:end;">
                <button type="button" class="secondary abr-neural-preset-btn" data-lado="<?= $lado ?>">Aplicar preset</button>
            </label>
        </div>
        <p class="help abr-neural-preset-nota" data-lado="<?= $lado ?>"></p>
        <div class="three-col">
            <label>Prolongación I-III (ms)
                <input type="number" step="0.05" min="0" max="<?= CaseBuilder::ABR_NEURAL_MAX_MS ?>" name="abr[<?= $lado ?>][neural][i_iii_ms]" class="abr-neural-input" data-lado="<?= $lado ?>" data-param="i_iii_ms" value="<?= htmlspecialchars((string) ($vn['i_iii_ms'] ?? CaseBuilder::ABR_NEURAL_DEFAULTS['i_iii_ms'])) ?>">
            </label>
            <label>Prolongación III-V (ms)
                <input type="number" step="0.05" min="0" max="<?= CaseBuilder::ABR_NEURAL_MAX_MS ?>" name="abr[<?= $lado ?>][neural][iii_v_ms]" class="abr-neural-input" data-lado="<?= $lado ?>" data-param="iii_v_ms" value="<?= htmlspecialchars((string) ($vn['iii_v_ms'] ?? CaseBuilder::ABR_NEURAL_DEFAULTS['iii_v_ms'])) ?>">
            </label>
            <label>Retraso global (ms)
                <input type="number" step="0.05" min="0" max="<?= CaseBuilder::ABR_NEURAL_MAX_MS ?>" name="abr[<?= $lado ?>][neural][global_delay_ms]" class="abr-neural-input" data-lado="<?= $lado ?>" data-param="global_delay_ms" value="<?= htmlspecialchars((string) ($vn['global_delay_ms'] ?? CaseBuilder::ABR_NEURAL_DEFAULTS['global_delay_ms'])) ?>">
            </label>
            <label>Razón V/I (1 = sin caída)
                <input type="number" step="0.05" min="0.05" max="1" name="abr[<?= $lado ?>][neural][v_i_factor]" class="abr-neural-input" data-lado="<?= $lado ?>" data-param="v_i_factor" value="<?= htmlspecialchars((string) ($vn['v_i_factor'] ?? CaseBuilder::ABR_NEURAL_DEFAULTS['v_i_factor'])) ?>">
            </label>
            <label>Bloqueo
                <select name="abr[<?= $lado ?>][neural][bloqueo]" class="abr-neural-input" data-lado="<?= $lado ?>" data-param="bloqueo">
                    <?php foreach (CaseBuilder::ABR_NEURAL_BLOQUEO_OPTIONS as $opt): ?>
                    <option value="<?= $opt ?>" <?= ($vn['bloqueo'] ?? CaseBuilder::ABR_NEURAL_DEFAULTS['bloqueo']) === $opt ? 'selected' : '' ?>><?= htmlspecialchars(CaseBuilder::ABR_NEURAL_BLOQUEO_LABELS[$opt]) ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
            <label>Microfónico coclear
                <select name="abr[<?= $lado ?>][neural][microfonica]" class="abr-neural-input" data-lado="<?= $lado ?>" data-param="microfonica">
                    <?php foreach (CaseBuilder::ABR_NEURAL_MICROFONICA_OPTIONS as $opt): ?>
                    <option value="<?= $opt ?>" <?= ($vn['microfonica'] ?? CaseBuilder::ABR_NEURAL_DEFAULTS['microfonica']) === $opt ? 'selected' : '' ?>><?= htmlspecialchars(CaseBuilder::ABR_NEURAL_MICROFONICA_LABELS[$opt]) ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
            <label>Desincronía (morfología)
                <select name="abr[<?= $lado ?>][neural][desincronia]" class="abr-neural-input" data-lado="<?= $lado ?>" data-param="desincronia">
                    <?php foreach (CaseBuilder::ABR_NEURAL_DESINCRONIA_OPTIONS as $opt): ?>
                    <option value="<?= $opt ?>" <?= ($vn['desincronia'] ?? CaseBuilder::ABR_NEURAL_DEFAULTS['desincronia']) === $opt ? 'selected' : '' ?>><?= ucfirst($opt) ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
            <label>Sensibilidad a la tasa
                <select name="abr[<?= $lado ?>][neural][sensibilidad_tasa]" class="abr-neural-input" data-lado="<?= $lado ?>" data-param="sensibilidad_tasa">
                    <?php foreach (CaseBuilder::ABR_NEURAL_TASA_OPTIONS as $opt): ?>
                    <option value="<?= $opt ?>" <?= ($vn['sensibilidad_tasa'] ?? CaseBuilder::ABR_NEURAL_DEFAULTS['sensibilidad_tasa']) === $opt ? 'selected' : '' ?>><?= ucfirst($opt) ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
        </div>
        <p class="help">La diferencia interaural de onda V (IT5) no se configura acá: sale de que los dos oídos tengan patrones distintos. Y la replicabilidad pobre es la casilla "Reproducible" de arriba.</p>
    </div>
</div>
<?php endforeach; ?>
</div>
</div>
