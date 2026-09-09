<?php
/**
 * Ficha 8 -- EOA: patología, desviaciones por frecuencia y picos SOAE.
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
<div class="tab-panel" data-tab="eoas">
<div class="two-col">
<?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
<div class="card">
    <strong>EOA <?= $ladoLabel ?></strong>
    <p class="help">Patología de este oído para el generador de Emisiones Otoacústicas (TEOAE/DPOAE/SOAE/SFOAE). "Coclear" y "Transmisión" atenúan la emisión en función del umbral: por sobre ~35-40 dB la dejan bajo el piso de ruido y el registro sale REFER. "Neural" no la atenúa aunque el umbral esté alto, así que el registro sale PASS con el ABR alterado.</p>
    <p class="derivado-aviso" data-derivado="eoas" hidden>La patología, el umbral y el perfil por frecuencia de este oído los sugiere el <a href="#" class="tab-link" data-goto-tab="perfil">Perfil auditivo</a>, porque la casilla <em>OEA: perfil por frecuencia</em> está encendida: se escriben solos con lo que predice el perfil y <strong>se pueden editar</strong>: lo que quede en pantalla es lo que se guarda. Cambiar el audiograma o el perfil vuelve a sugerir y pisa lo editado a mano; para que no se toquen más, apagar esa casilla.</p>
    <div class="three-col">
        <label>Patología
            <select name="eoas[<?= $lado ?>][type]" class="eoas-type-select" data-lado="<?= $lado ?>">
                <?php foreach (CaseBuilder::EOAS_TYPE_OPTIONS as $opt): ?>
                <option value="<?= $opt ?>" <?= ($v['eoas'][$lado]['type'] ?? 'normal') === $opt ? 'selected' : '' ?>><?= ucfirst($opt) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Umbral (dB)
            <input type="number" step="any" name="eoas[<?= $lado ?>][umbral]" value="<?= htmlspecialchars((string) ($v['eoas'][$lado]['umbral'] ?? (string) CaseBuilder::EOAS_DEFAULTS['umbral'])) ?>">
        </label>
    </div>
    <p class="help">El umbral y el perfil por frecuencia los escribe el perfil auditivo, derivados del audiograma y del componente coclear: el grado de la OEA no se elige acá, y por eso este oído no puede contradecir a su propia audiometría. Lo que el botón sortea son las <strong>condiciones de registro</strong> (ruido del paciente, sello de la sonda, variabilidad), que sí son del caso y no se derivan de nada.</p>
    <div class="two-col">
        <label>Grado a sortear
            <select name="eoas_grade[<?= $lado ?>]" class="eoas-grade-select" data-lado="<?= $lado ?>">
                <option value="random">Cualquiera (al azar)</option>
            </select>
        </label>
        <label style="align-self:end;">
            <button type="button" class="secondary eoas-autofill-btn" data-lado="<?= $lado ?>" style="margin-top:0;">Volver a sortear este oído</button>
        </label>
    </div>
    <p class="help">Condiciones de registro de este oído -- lo que hace que dos pacientes con la misma cóclea no den la misma pantalla.</p>
    <div class="three-col">
        <label>Atenuación extra (dB)
            <input type="number" step="any" name="eoas[<?= $lado ?>][atten_db]" value="<?= htmlspecialchars((string) ($v['eoas'][$lado]['atten_db'] ?? (string) CaseBuilder::EOAS_DEFAULTS['atten_db'])) ?>">
        </label>
        <label>Ruido del paciente (dB)
            <input type="number" step="any" min="-20" name="eoas[<?= $lado ?>][ruido_db]" value="<?= htmlspecialchars((string) ($v['eoas'][$lado]['ruido_db'] ?? (string) CaseBuilder::EOAS_DEFAULTS['ruido_db'])) ?>">
        </label>
        <label>Sello de sonda (%)
            <input type="number" step="1" min="5" max="100" name="eoas[<?= $lado ?>][sello_pct]" value="<?= htmlspecialchars((string) ($v['eoas'][$lado]['sello_pct'] ?? (string) CaseBuilder::EOAS_DEFAULTS['sello_pct'])) ?>">
        </label>
        <label>Variabilidad biológica (dB)
            <input type="number" step="any" min="0" name="eoas[<?= $lado ?>][variabilidad_db]" value="<?= htmlspecialchars((string) ($v['eoas'][$lado]['variabilidad_db'] ?? (string) CaseBuilder::EOAS_DEFAULTS['variabilidad_db'])) ?>">
        </label>
    </div>
    <p class="help">"Atenuación extra" se suma a la que ya calcula la patología (útil para forzar un REFER limpio sin tocar el umbral). "Ruido del paciente" sube el piso de ruido de la captura: tapa el DP-grama en graves y baja la reproducibilidad TEOAE <strong>sin tocar la cóclea</strong>, así que sirve para armar un registro malo en un oído sano. "Sello de sonda" es a qué % converge el probe fit (bajo = estímulo débil y captura inestable). "Variabilidad biológica" es la estructura fina: 0 da una curva de libro, 3-4 dB da un registro real.</p>
    <p class="help">Emisiones espontáneas (SOAE) de este oído -- el tab SOAE del emisor registra en silencio y busca picos sobre el piso de ruido.</p>
    <div class="three-col">
        <label>SOAE
            <select name="eoas[<?= $lado ?>][soae_mode]">
                <?php foreach (CaseBuilder::EOAS_SOAE_MODES as $opt): ?>
                <option value="<?= $opt ?>" <?= ($v['eoas'][$lado]['soae_mode'] ?? CaseBuilder::EOAS_DEFAULTS['soae_mode']) === $opt ? 'selected' : '' ?>><?= htmlspecialchars(CaseBuilder::EOAS_SOAE_MODE_LABELS[$opt]) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
    </div>
    <table class="grid-table">
        <thead>
        <tr><th>Pico</th><?php for ($i = 1; $i <= CaseBuilder::EOAS_SOAE_MAX_PEAKS; $i++): ?><th><?= $i ?></th><?php endfor; ?></tr>
        </thead>
        <tbody>
        <tr>
            <td class="side-label">Hz</td>
            <?php for ($i = 0; $i < CaseBuilder::EOAS_SOAE_MAX_PEAKS; $i++): ?>
            <td><input type="number" step="1" min="<?= CaseBuilder::EOAS_SOAE_FREQ_MIN ?>" max="<?= CaseBuilder::EOAS_SOAE_FREQ_MAX ?>" placeholder="--" name="eoas[<?= $lado ?>][soae_peaks][<?= $i ?>][hz]" value="<?= htmlspecialchars((string) ($v['eoas'][$lado]['soae_peaks'][$i]['hz'] ?? '')) ?>"></td>
            <?php endfor; ?>
        </tr>
        <tr>
            <td class="side-label">dB SPL</td>
            <?php for ($i = 0; $i < CaseBuilder::EOAS_SOAE_MAX_PEAKS; $i++): ?>
            <td><input type="number" step="any" min="-15" max="30" placeholder="<?= CaseBuilder::EOAS_SOAE_DEFAULT_PEAK_DB ?>" name="eoas[<?= $lado ?>][soae_peaks][<?= $i ?>][db]" value="<?= htmlspecialchars((string) ($v['eoas'][$lado]['soae_peaks'][$i]['db'] ?? '')) ?>"></td>
            <?php endfor; ?>
        </tr>
        </tbody>
    </table>
    <p class="help">"Auto" sortea al azar si este oído tiene SOAE (~45%, algo más en OD) -- estable para el mismo caso, pero no se puede saber de antemano. Para mostrarlas en clase o evaluar sobre un hallazgo fijo usá "Presentes" y cargá los picos: frecuencia en Hz y nivel de la emisión (los SOAE reales rondan 0 dB SPL, rara vez pasan 20; en blanco toma <?= CaseBuilder::EOAS_SOAE_DEFAULT_PEAK_DB ?> dB SPL). "Presentes" sin picos cargados = se sortean al azar, pero garantiza al menos uno. Los picos cargados NO se atenúan por patología ni por sello: el nivel que pongas es el que se va a ver, aunque el ruido del paciente igual puede taparlos. "Ausentes" fuerza un registro sin SOAE (lo normal en coclear/transmisión, y también posible en un oído sano).</p>
    <p class="help">Perfil por frecuencia -- dB de caída respecto de lo esperado (positivo = OEA más chica). Se aplica a las cuatro pruebas: bandas TEOAE, puntos del DP-grama, curva de sintonía SFOAE y los picos SOAE sorteados.</p>
    <table class="grid-table">
        <thead>
        <tr><th>Hz</th><?php foreach (CaseBuilder::EOAS_FREQS as $hz): ?><th><?= $hz ?></th><?php endforeach; ?></tr>
        </thead>
        <tbody>
        <tr>
            <td class="side-label">Δ dB</td>
            <?php foreach (CaseBuilder::EOAS_FREQS as $hz): ?>
            <td><input type="number" step="any" class="eoas-desv-input" data-lado="<?= $lado ?>" data-hz="<?= $hz ?>" name="eoas[<?= $lado ?>][desv][<?= $hz ?>]" value="<?= htmlspecialchars((string) ($v['eoas'][$lado]['desv'][(string) $hz] ?? '0')) ?>"></td>
            <?php endforeach; ?>
        </tr>
        </tbody>
    </table>
</div>
<?php endforeach; ?>
</div>
<div class="card">
    <strong>Vista previa: DP-grama y bandas TEOAE</strong>
    <p class="help">Simulación simplificada (sin ruido por barrido ni promediación) de lo que va a ver el alumno con esta configuración. Arriba el nivel DP por f2 contra el área normal y el piso de ruido; abajo el SNR por banda TEOAE con la línea de criterio (6 dB): banda bajo la línea = REFER.</p>
    <div class="two-col">
        <div>
            <strong class="od-text">OD</strong>
            <div id="eoa-preview-od" class="eoa-preview"></div>
        </div>
        <div>
            <strong class="oi-text">OI</strong>
            <div id="eoa-preview-oi" class="eoa-preview"></div>
        </div>
    </div>
</div>
</div>
