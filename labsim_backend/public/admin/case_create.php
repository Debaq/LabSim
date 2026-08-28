<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/CaseBuilder.php';

/**
 * Crea un caso clínico completo desde el navegador -- equivalente web de
 * src/create_a.py (hoy solo existe en la app de escritorio, permission=777).
 * Guarda en `cases` con el mismo shape de JSON que espera el cliente
 * (Audiometer.py/Z.py/ListWords.py al atender), y redirige a agenda.php
 * para completar fecha/hora/RUT -- ese formulario ya existe, no se duplica.
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();

/** Lee un valor anidado de un array (ej. $v['aerea']['od'][3]) con default si falta. */
function fv(array $arr, array $path, $default = null)
{
    $cur = $arr;
    foreach ($path as $p) {
        if (!is_array($cur) || !isset($cur[$p])) {
            return $default;
        }
        $cur = $cur[$p];
    }
    return $cur;
}

/** [od0,od1,...] + [oi0,oi1,...] -> [[od0,oi0],[od1,oi1],...] -- shape que espera cases.data. */
function zip_pairs(array $od, array $oi): array
{
    $out = [];
    foreach ($od as $i => $val) {
        $out[] = [$val, $oi[$i] ?? 0];
    }
    return $out;
}

$error = null;
$v = $_POST; // sticky form: se redibuja con lo ya tipeado, tanto al generar nombre como si falla la validación

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $formAction = (string) ($v['form_action'] ?? '');

    $gender = ($v['gender'] ?? '0') === '1' ? 1 : 0;

    if ($formAction === 'generate_name') {
        [$n1, $n2, $a1, $a2] = CaseBuilder::randomName($gender === 0 ? 'men' : 'women');
        $v['nombre1'] = $n1;
        $v['nombre2'] = $n2;
        $v['apellido1'] = $a1;
        $v['apellido2'] = $a2;
    } elseif ($formAction === 'create_case') {
        $age = max(0, (int) ($v['age'] ?? 0));
        $nombre1 = trim((string) ($v['nombre1'] ?? ''));
        $apellido1 = trim((string) ($v['apellido1'] ?? ''));

        $aerea = ['od' => [], 'oi' => []];
        $osea = ['od' => [], 'oi' => []];
        $ldl = ['od' => [], 'oi' => []];
        foreach (['od', 'oi'] as $side) {
            foreach (CaseBuilder::FREQUENCIES as $n => $freq) {
                $aerea[$side][] = (int) fv($v, ['aerea', $side, (string) $n], 0);
                $osea[$side][] = (int) fv($v, ['osea', $side, (string) $n], 0);
                $ldl[$side][] = (int) fv($v, ['ldl', $side, (string) $n], 130);
            }
            if (isset($v['igualar'][$side])) {
                $osea[$side] = $aerea[$side]; // "igualar ósea a aérea", igual que equal_osea en create_a.py
            }
            if (!isset($v['ldl_habilitado'][$side])) {
                $ldl[$side] = array_fill(0, count(CaseBuilder::FREQUENCIES), 130); // deshabilitado = ausente
            }
        }

        $reflexIpsi = ['od' => [], 'oi' => []];
        $reflexContra = ['od' => [], 'oi' => []];
        foreach (['od', 'oi'] as $side) {
            for ($n = 0; $n < 4; $n++) {
                $reflexIpsi[$side][] = (int) fv($v, ['reflex_ipsi', $side, (string) $n], 130);
            }
            for ($n = 0; $n < 5; $n++) {
                $reflexContra[$side][] = (int) fv($v, ['reflex_contra', $side, (string) $n], 130);
            }
        }

        $airPairs = zip_pairs($aerea['od'], $aerea['oi']);
        $fletcher = CaseBuilder::fletcherAvg($airPairs);
        $sdt = [
            isset($v['sdt_auto']['od']) ? $fletcher[0] : (int) fv($v, ['sdt', 'od'], 0),
            isset($v['sdt_auto']['oi']) ? $fletcher[1] : (int) fv($v, ['sdt', 'oi'], 0),
        ];
        $srt = [
            isset($v['srt_auto']['od']) ? $fletcher[0] : (int) fv($v, ['srt', 'od'], 0),
            isset($v['srt_auto']['oi']) ? $fletcher[1] : (int) fv($v, ['srt', 'oi'], 0),
        ];

        $zOd = (string) ($v['z_od'] ?? 'A');
        $zOi = (string) ($v['z_oi'] ?? 'A');
        $etfOd = (string) ($v['etf_od'] ?? 'Normal');
        $etfOi = (string) ($v['etf_oi'] ?? 'Normal');
        $fowlerFreq = (int) ($v['fowler_freq'] ?? 0);

        if ($age <= 0) {
            $error = 'Falta la edad.';
        } elseif ($nombre1 === '' || $apellido1 === '') {
            $error = 'Falta el nombre del paciente (generalo con el botón o escríbelo a mano).';
        } elseif (!in_array($zOd, CaseBuilder::Z_OPTIONS, true) || !in_array($zOi, CaseBuilder::Z_OPTIONS, true)) {
            $error = 'Tipo de timpanograma inválido.';
        } elseif (!in_array($etfOd, CaseBuilder::ETF_OPTIONS, true) || !in_array($etfOi, CaseBuilder::ETF_OPTIONS, true)) {
            $error = 'Valor de ETF inválido.';
        } elseif ($fowlerFreq < 0 || $fowlerFreq > 8) {
            $error = 'Frecuencia de Fowler inválida.';
        }

        if ($error === null) {
            $antecedentes = [];
            foreach (CaseBuilder::HIST_CHECKBOXES as $h) {
                $antecedentes[$h] = isset($v['hist'][$h]);
            }

            $id = CaseBuilder::nextCaseId($pdo);
            $data = CaseBuilder::buildCaseData([
                'gender' => $gender,
                'id' => $id,
                'aerea' => $airPairs,
                'osea' => zip_pairs($osea['od'], $osea['oi']),
                'ldl' => zip_pairs($ldl['od'], $ldl['oi']),
                'z_od' => $zOd,
                'z_oi' => $zOi,
                'umd' => [
                    ['int' => (int) fv($v, ['umd_int', 'od'], 35), 'percentage' => (int) fv($v, ['umd_pct', 'od'], 100)],
                    ['int' => (int) fv($v, ['umd_int', 'oi'], 35), 'percentage' => (int) fv($v, ['umd_pct', 'oi'], 100)],
                ],
                'sdt' => $sdt,
                'srt' => $srt,
                'fowler' => [
                    'freq' => $fowlerFreq,
                    'cuts' => [(int) ($v['fowler_cut1'] ?? 15), (int) ($v['fowler_cut2'] ?? 30), (int) ($v['fowler_cut3'] ?? 50)],
                ],
                'stenger' => [isset($v['stenger']['od']), isset($v['stenger']['oi'])],
                'sisi' => [(int) fv($v, ['sisi', 'od'], 0), (int) fv($v, ['sisi', 'oi'], 0)],
                'recruit' => [isset($v['recruit']['od']), isset($v['recruit']['oi'])],
                'decay' => [isset($v['decay']['od']), isset($v['decay']['oi'])],
                'reflex' => [
                    'ipsi' => zip_pairs($reflexIpsi['od'], $reflexIpsi['oi']),
                    'contra' => zip_pairs($reflexContra['od'], $reflexContra['oi']),
                ],
                'etf_od' => $etfOd,
                'etf_oi' => $etfOi,
                'anamnesis' => [
                    'antecedentes' => $antecedentes,
                    'medicamentos' => trim((string) ($v['medicamentos'] ?? '')),
                    'cirugias' => trim((string) ($v['cirugias'] ?? '')),
                    'otros' => trim((string) ($v['otros'] ?? '')),
                ],
            ]);

            // paciente_snapshot: mismo mecanismo que Cases::snapshotBeforeAppointmentDelete
            // -- agenda.php ya sabe leer esta clave para precargar el formulario de
            // agendado cuando el caso todavía no tiene cita propia, así no hay que
            // re-tipear nombre/RUT que recién se generaron acá.
            $nombre2 = trim((string) ($v['nombre2'] ?? ''));
            $apellido2 = trim((string) ($v['apellido2'] ?? ''));
            $data['paciente_snapshot'] = [
                'nombre' => trim($nombre1 . ' ' . $nombre2),
                'apellido' => trim($apellido1 . ' ' . $apellido2),
                'rut' => (string) CaseBuilder::rutFromAge($age),
                'fecha_nac' => sprintf('01-01-%04d', (int) date('Y') - $age),
                'procedimiento' => 'Audiometría',
            ];

            $pdo->prepare(
                "INSERT INTO cases (id, data, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)
                 ON CONFLICT(id) DO UPDATE SET data = excluded.data, updated_at = CURRENT_TIMESTAMP"
            )->execute([$id, json_encode($data, JSON_UNESCAPED_UNICODE)]);

            header('Location: agenda.php?schedule=' . urlencode($id));
            exit;
        }
    }
}

admin_header('Crear caso clínico', $me);
?>
<style>
    .grid-table th, .grid-table td { text-align: center; padding: 0.3rem; }
    .grid-table input[type=number] { width: 4.2rem; padding: 0.2rem; text-align: center; }
    .grid-table th.side-label, .grid-table td.side-label { text-align: left; font-weight: 600; }
    .inline-check { display: inline-flex; align-items: center; gap: 0.3rem; font-weight: 400; margin: 0 0 0 1rem; }
    .inline-check input { width: auto; margin: 0; }
    fieldset { border: 1px solid #e5e5e5; border-radius: 6px; margin: 1rem 0; padding: 0.8rem 1rem; }
    legend { font-weight: 600; padding: 0 0.4rem; }
    .two-col { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
</style>

<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>

<form method="post" id="case-form">
<div class="card">
    <strong>Paciente</strong>
    <label class="inline-check"><input type="radio" name="gender" value="0" <?= ($v['gender'] ?? '0') === '0' ? 'checked' : '' ?>> Hombre</label>
    <label class="inline-check"><input type="radio" name="gender" value="1" <?= ($v['gender'] ?? '0') === '1' ? 'checked' : '' ?>> Mujer</label>
    <label>Edad
        <input type="number" name="age" min="0" max="110" value="<?= htmlspecialchars((string) ($v['age'] ?? '')) ?>">
    </label>
    <div class="two-col">
        <label>Nombre
            <input type="text" name="nombre1" value="<?= htmlspecialchars((string) ($v['nombre1'] ?? '')) ?>">
        </label>
        <label>Segundo nombre
            <input type="text" name="nombre2" value="<?= htmlspecialchars((string) ($v['nombre2'] ?? '')) ?>">
        </label>
        <label>Apellido
            <input type="text" name="apellido1" value="<?= htmlspecialchars((string) ($v['apellido1'] ?? '')) ?>">
        </label>
        <label>Segundo apellido
            <input type="text" name="apellido2" value="<?= htmlspecialchars((string) ($v['apellido2'] ?? '')) ?>">
        </label>
    </div>
    <button type="submit" name="form_action" value="generate_name" class="secondary">Generar nombre al azar</button>
</div>

<?php
$series = ['aerea' => 'Vía aérea', 'osea' => 'Vía ósea', 'ldl' => 'LDL (umbral de disconfort)'];
foreach ($series as $key => $label):
?>
<div class="card">
    <strong><?= htmlspecialchars($label) ?></strong>
    <?php if ($key === 'osea'): ?>
    <label class="inline-check"><input type="checkbox" class="igualar-toggle" data-side="od" name="igualar[od]" <?= isset($v['igualar']['od']) ? 'checked' : '' ?>> Igualar OD a vía aérea</label>
    <label class="inline-check"><input type="checkbox" class="igualar-toggle" data-side="oi" name="igualar[oi]" <?= isset($v['igualar']['oi']) ? 'checked' : '' ?>> Igualar OI a vía aérea</label>
    <?php endif; ?>
    <?php if ($key === 'ldl'): ?>
    <label class="inline-check"><input type="checkbox" class="ldl-toggle" data-side="od" name="ldl_habilitado[od]" <?= isset($v['ldl_habilitado']['od']) ? 'checked' : '' ?>> Medido OD</label>
    <label class="inline-check"><input type="checkbox" class="ldl-toggle" data-side="oi" name="ldl_habilitado[oi]" <?= isset($v['ldl_habilitado']['oi']) ? 'checked' : '' ?>> Medido OI</label>
    <p class="legend">Sin marcar = no medido, se guarda como ausente (130) sin importar lo que quede escrito abajo.</p>
    <?php endif; ?>
    <table class="grid-table">
        <tr><th></th><?php foreach (CaseBuilder::FREQUENCIES as $f): ?><th><?= $f ?> Hz</th><?php endforeach; ?></tr>
        <?php foreach (['od' => 'OD', 'oi' => 'OI'] as $side => $sideLabel): ?>
        <tr>
            <td class="side-label"><?= $sideLabel ?></td>
            <?php foreach (CaseBuilder::FREQUENCIES as $n => $freq):
                $default = $key === 'ldl' ? 130 : 0;
                $val = fv($v, [$key, $side, (string) $n], $default);
            ?>
            <td><input type="number" step="5" min="-10" max="130"
                       id="<?= $key ?>_<?= $side ?>_<?= $n ?>"
                       name="<?= $key ?>[<?= $side ?>][<?= $n ?>]"
                       value="<?= htmlspecialchars((string) $val) ?>"></td>
            <?php endforeach; ?>
        </tr>
        <?php endforeach; ?>
    </table>
</div>
<?php endforeach; ?>

<div class="card">
    <strong>SDT / SRT (logoaudiometría)</strong>
    <table class="grid-table">
        <tr><th></th><th>SDT</th><th>SRT</th></tr>
        <?php foreach (['od' => 'OD', 'oi' => 'OI'] as $side => $sideLabel): ?>
        <tr>
            <td class="side-label"><?= $sideLabel ?></td>
            <td>
                <input type="number" step="5" class="sdt-input" data-side="<?= $side ?>" name="sdt[<?= $side ?>]" value="<?= htmlspecialchars((string) fv($v, ['sdt', $side], 0)) ?>">
                <label class="inline-check"><input type="checkbox" class="auto-toggle" data-target="sdt-input" data-side="<?= $side ?>" name="sdt_auto[<?= $side ?>]" <?= !isset($v['sdt_auto']) || isset($v['sdt_auto'][$side]) ? 'checked' : '' ?>>auto (Fletcher)</label>
            </td>
            <td>
                <input type="number" step="5" class="srt-input" data-side="<?= $side ?>" name="srt[<?= $side ?>]" value="<?= htmlspecialchars((string) fv($v, ['srt', $side], 0)) ?>">
                <label class="inline-check"><input type="checkbox" class="auto-toggle" data-target="srt-input" data-side="<?= $side ?>" name="srt_auto[<?= $side ?>]" <?= !isset($v['srt_auto']) || isset($v['srt_auto'][$side]) ? 'checked' : '' ?>>auto (Fletcher)</label>
            </td>
        </tr>
        <?php endforeach; ?>
    </table>
    <p class="legend">Auto = mejor promedio de 2 de 3 (500/1000/2000 Hz vía aérea), redondeado a múltiplo de 5. Destildar para escribir un valor manual.</p>
</div>

<div class="card">
    <strong>Otras pruebas</strong>
    <div class="two-col">
        <div>
            <label>UMD OD (int / %)
                <input type="number" step="5" name="umd_int[od]" value="<?= htmlspecialchars((string) fv($v, ['umd_int', 'od'], 35)) ?>" style="width:5rem; display:inline-block;">
                / <input type="number" step="5" name="umd_pct[od]" value="<?= htmlspecialchars((string) fv($v, ['umd_pct', 'od'], 100)) ?>" style="width:5rem; display:inline-block;">
            </label>
            <label>UMD OI (int / %)
                <input type="number" step="5" name="umd_int[oi]" value="<?= htmlspecialchars((string) fv($v, ['umd_int', 'oi'], 35)) ?>" style="width:5rem; display:inline-block;">
                / <input type="number" step="5" name="umd_pct[oi]" value="<?= htmlspecialchars((string) fv($v, ['umd_pct', 'oi'], 100)) ?>" style="width:5rem; display:inline-block;">
            </label>
            <label>SISI OD <input type="number" step="5" name="sisi[od]" value="<?= htmlspecialchars((string) fv($v, ['sisi', 'od'], 0)) ?>"></label>
            <label>SISI OI <input type="number" step="5" name="sisi[oi]" value="<?= htmlspecialchars((string) fv($v, ['sisi', 'oi'], 0)) ?>"></label>
            <label class="inline-check"><input type="checkbox" name="stenger[od]" <?= isset($v['stenger']['od']) ? 'checked' : '' ?>> Stenger OD</label>
            <label class="inline-check"><input type="checkbox" name="stenger[oi]" <?= isset($v['stenger']['oi']) ? 'checked' : '' ?>> Stenger OI</label>
            <label class="inline-check"><input type="checkbox" name="recruit[od]" <?= isset($v['recruit']['od']) ? 'checked' : '' ?>> Reclutamiento OD</label>
            <label class="inline-check"><input type="checkbox" name="recruit[oi]" <?= isset($v['recruit']['oi']) ? 'checked' : '' ?>> Reclutamiento OI</label>
            <label class="inline-check"><input type="checkbox" name="decay[od]" <?= isset($v['decay']['od']) ? 'checked' : '' ?>> Decay OD</label>
            <label class="inline-check"><input type="checkbox" name="decay[oi]" <?= isset($v['decay']['oi']) ? 'checked' : '' ?>> Decay OI</label>
        </div>
        <div>
            <label>Fowler -- frecuencia
                <select name="fowler_freq">
                    <?php foreach (CaseBuilder::FREQUENCIES as $i => $f): ?>
                    <option value="<?= $i ?>" <?= (int) ($v['fowler_freq'] ?? 0) === $i ? 'selected' : '' ?>><?= $f ?> Hz</option>
                    <?php endforeach; ?>
                </select>
            </label>
            <label>Cortes Fowler
                <input type="number" name="fowler_cut1" value="<?= htmlspecialchars((string) ($v['fowler_cut1'] ?? 15)) ?>" style="width:4rem; display:inline-block;">
                <input type="number" name="fowler_cut2" value="<?= htmlspecialchars((string) ($v['fowler_cut2'] ?? 30)) ?>" style="width:4rem; display:inline-block;">
                <input type="number" name="fowler_cut3" value="<?= htmlspecialchars((string) ($v['fowler_cut3'] ?? 50)) ?>" style="width:4rem; display:inline-block;">
            </label>
        </div>
    </div>
</div>

<div class="card">
    <strong>Timpanometría (Z)</strong>
    <div class="two-col">
        <label>Z OD
            <select name="z_od">
                <?php foreach (CaseBuilder::Z_OPTIONS as $opt): ?>
                <option value="<?= $opt ?>" <?= ($v['z_od'] ?? 'A') === $opt ? 'selected' : '' ?>><?= $opt ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Z OI
            <select name="z_oi">
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
    <?php
    $reflexGroups = ['ipsi' => ['label' => 'Ipsilateral', 'freqs' => [500, 1000, 2000, 4000]],
                      'contra' => ['label' => 'Contralateral', 'freqs' => [500, 1000, 2000, 4000, 'WN']]];
    foreach ($reflexGroups as $mode => $info):
    ?>
    <table class="grid-table">
        <tr><th class="side-label"><?= htmlspecialchars($info['label']) ?></th><?php foreach ($info['freqs'] as $f): ?><th><?= is_int($f) ? $f . ' Hz' : $f ?></th><?php endforeach; ?></tr>
        <?php foreach (['od' => 'OD', 'oi' => 'OI'] as $side => $sideLabel): ?>
        <tr>
            <td class="side-label"><?= $sideLabel ?></td>
            <?php foreach ($info['freqs'] as $n => $f): ?>
            <td><input type="number" step="5" name="reflex_<?= $mode ?>[<?= $side ?>][<?= $n ?>]" value="<?= htmlspecialchars((string) fv($v, ['reflex_' . $mode, $side, (string) $n], 130)) ?>"></td>
            <?php endforeach; ?>
        </tr>
        <?php endforeach; ?>
    </table>
    <?php endforeach; ?>
</div>

<div class="card">
    <strong>Anamnesis</strong>
    <?php
    $histLabels = [
        'hipoacusia_familiar' => 'Hipoacusia familiar', 'ototoxicos' => 'Ototóxicos',
        'trauma_acustico' => 'Trauma acústico', 'otitis' => 'Otitis', 'meningitis' => 'Meningitis',
        'tce' => 'TCE', 'diabetes' => 'Diabetes', 'hta' => 'HTA',
    ];
    foreach ($histLabels as $key => $label): ?>
    <label class="inline-check"><input type="checkbox" name="hist[<?= $key ?>]" <?= isset($v['hist'][$key]) ? 'checked' : '' ?>> <?= htmlspecialchars($label) ?></label>
    <?php endforeach; ?>
    <label>Medicamentos
        <input type="text" name="medicamentos" value="<?= htmlspecialchars((string) ($v['medicamentos'] ?? '')) ?>">
    </label>
    <label>Cirugías
        <input type="text" name="cirugias" value="<?= htmlspecialchars((string) ($v['cirugias'] ?? '')) ?>">
    </label>
    <label>Otros antecedentes
        <textarea name="otros" rows="2" style="width:100%; padding:0.45rem; margin-top:0.2rem; border:1px solid #ccc; border-radius:4px;"><?= htmlspecialchars((string) ($v['otros'] ?? '')) ?></textarea>
    </label>
</div>

<div class="card">
    <button type="submit" name="form_action" value="create_case">Crear caso</button>
    <a href="agenda.php" style="margin-left:1rem; font-size:0.85rem;">Cancelar</a>
</div>
</form>

<script>
// Ayuda visual en vivo -- el servidor recalcula todo igual al enviar,
// así que si JS falla el caso igual queda bien formado.
(function () {
    function pairAvgFloor5(a, b) {
        var vals = [a, b].sort(function (x, y) { return x - y; });
        var avg = (vals[0] + vals[1]) / 2;
        return Math.floor(avg / 5) * 5;
    }
    function fletcher(side) {
        var f500 = parseInt(document.getElementById('aerea_' + side + '_2').value, 10) || 0;
        var f1000 = parseInt(document.getElementById('aerea_' + side + '_3').value, 10) || 0;
        var f2000 = parseInt(document.getElementById('aerea_' + side + '_4').value, 10) || 0;
        var trio = [f500, f1000, f2000].sort(function (x, y) { return x - y; });
        return Math.floor(((trio[0] + trio[1]) / 2) / 5) * 5;
    }

    ['od', 'oi'].forEach(function (side) {
        var igualar = document.querySelector('.igualar-toggle[data-side="' + side + '"]');
        function syncOsea() {
            if (!igualar || !igualar.checked) return;
            for (var n = 0; n < 9; n++) {
                var a = document.getElementById('aerea_' + side + '_' + n);
                var o = document.getElementById('osea_' + side + '_' + n);
                if (a && o) { o.value = a.value; o.readOnly = true; }
            }
        }
        function unlockOsea() {
            for (var n = 0; n < 9; n++) {
                var o = document.getElementById('osea_' + side + '_' + n);
                if (o) { o.readOnly = false; }
            }
        }
        if (igualar) {
            igualar.addEventListener('change', function () { igualar.checked ? syncOsea() : unlockOsea(); });
            for (var n = 0; n < 9; n++) {
                var a = document.getElementById('aerea_' + side + '_' + n);
                if (a) { a.addEventListener('input', syncOsea); }
            }
            if (igualar.checked) { syncOsea(); }
        }

        var ldlToggle = document.querySelector('.ldl-toggle[data-side="' + side + '"]');
        function syncLdlOpacity() {
            if (!ldlToggle) return;
            for (var n = 0; n < 9; n++) {
                var el = document.getElementById('ldl_' + side + '_' + n);
                if (el) { el.style.opacity = ldlToggle.checked ? '1' : '0.4'; }
            }
        }
        if (ldlToggle) { ldlToggle.addEventListener('change', syncLdlOpacity); syncLdlOpacity(); }

        ['sdt', 'srt'].forEach(function (kind) {
            var auto = document.querySelector('.auto-toggle[data-target="' + kind + '-input"][data-side="' + side + '"]');
            var input = document.querySelector('.' + kind + '-input[data-side="' + side + '"]');
            function syncAuto() {
                if (!auto || !input) return;
                if (auto.checked) { input.value = fletcher(side); input.readOnly = true; }
                else { input.readOnly = false; }
            }
            if (auto) {
                auto.addEventListener('change', syncAuto);
                for (var n = 2; n <= 4; n++) {
                    var a = document.getElementById('aerea_' + side + '_' + n);
                    if (a) { a.addEventListener('input', syncAuto); }
                }
                syncAuto();
            }
        });
    });
})();
</script>
<?php
admin_footer();
