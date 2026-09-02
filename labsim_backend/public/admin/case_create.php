<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/CaseBuilder.php';
require_once __DIR__ . '/../../src/AdminAudit.php';

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

// Geometría del audiograma SVG de más abajo (dibujado en el navegador, ver
// <script> al final) -- escala logarítmica en frecuencia (así 3000/6000 caen
// a mitad de camino entre sus octavas, como en un audiograma real) y lineal
// en dB HL, -10 arriba (mejor audición) a 120 abajo. Mismo plot box (32,10)-(312,276)
// que usan drawAudiogram()/xPos()/yPos() en JS -- si se cambia acá, cambiar allá también.
function audiogram_x(float $freq): float
{
    $minLog = log(125, 2);
    $maxLog = log(8000, 2);
    return 32 + (log($freq, 2) - $minLog) / ($maxLog - $minLog) * 280;
}
function audiogram_y(float $db): float
{
    $db = max(-10, min(120, $db));
    return 10 + ($db - (-10)) / 130 * 266;
}

$error = null;
$v = $_POST; // sticky form: se redibuja con lo ya tipeado, tanto al generar nombre como si falla la validación

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
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
            AdminAudit::log($me, 'case_create', ['case_id' => $id, 'nombre' => $data['nombre'], 'apellido' => $data['apellido']]);

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

    /* Fichas (tabs): cada <div class="tab-panel"> es una pestaña del caso.
       Sin JS quedan todas visibles apiladas (igual que antes) -- degrada
       con gracia en vez de esconder campos que el navegador no puede volver
       a mostrar. */
    .tabs { display: flex; flex-wrap: wrap; gap: 0.2rem; border-bottom: 2px solid #e5e5e5; margin-bottom: 1.2rem; }
    .tab-btn { padding: 0.6rem 1.1rem; border: none; background: none; cursor: pointer; font-weight: 600;
               font-size: 0.9rem; color: #666; border-bottom: 2px solid transparent; margin-bottom: -2px; }
    .tab-btn:hover { color: #1a2744; }
    .tab-btn.active { color: #1a2744; border-bottom-color: #1a2744; }
    .tab-btn .tab-error-dot { display: inline-block; width: 0.4rem; height: 0.4rem; border-radius: 50%; background: #a33; margin-left: 0.3rem; }
    body.js-tabs .tab-panel { display: none; }
    body.js-tabs .tab-panel.active { display: block; }

    /* Ficha Audiometría: gráfico fijo a la izquierda mientras se scrollea
       la planilla de umbrales a la derecha. */
    .audiometria-layout { display: grid; grid-template-columns: 300px 1fr; gap: 1.2rem; align-items: start; }
    .audiogram-card { position: sticky; top: 1rem; }
    @media (max-width: 960px) {
        .audiometria-layout { grid-template-columns: 1fr; }
        .audiogram-card { position: static; }
    }
    .audiogram-legend { display: flex; flex-wrap: wrap; gap: 0.7rem; font-size: 0.75rem; color: #555; margin-top: 0.5rem; }
    .audiogram-legend span { display: inline-flex; align-items: center; gap: 0.3rem; }

    /* Agrupa campos por oído (OD/OI) dentro de una misma card -- reemplaza
       tener una card aparte por cada tipo de prueba. */
    .side-block { margin-top: 0.9rem; padding-top: 0.9rem; border-top: 1px solid #eee; }
    .side-block:first-child { margin-top: 0; padding-top: 0; border-top: none; }
    .side-heading { display: flex; align-items: center; flex-wrap: wrap; gap: 0.8rem; margin-bottom: 0.4rem; }
    .side-tag { display: inline-block; font-weight: 700; font-size: 0.78rem; padding: 0.2rem 0.55rem; border-radius: 4px; background: #eef0f4; color: #555; }
    .side-tag.od { color: #b33a3a; }
    .side-tag.oi { color: #2255aa; }
</style>

<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>

<form method="post" id="case-form">
<?= csrf_field() ?>
<div class="tabs" role="tablist">
    <button type="button" class="tab-btn active" data-tab="paciente">Paciente</button>
    <button type="button" class="tab-btn" data-tab="audiometria">Audiometría</button>
    <button type="button" class="tab-btn" data-tab="timpanometria">Timpanometría</button>
    <button type="button" class="tab-btn" data-tab="anamnesis">Anamnesis</button>
</div>

<div class="tab-panel active" data-tab="paciente">
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
</div>

<div class="tab-panel" data-tab="audiometria">
<div class="audiometria-layout">

<div class="audiogram-card card">
    <strong>Audiograma</strong>
    <svg id="audiogram-svg" viewBox="0 0 320 300" style="width:100%; height:auto; margin-top:0.5rem;">
        <rect x="32" y="10" width="280" height="266" fill="none" stroke="#ccc"></rect>
        <?php foreach ([0, 20, 40, 60, 80, 100, 120] as $db):
            $y = audiogram_y($db);
        ?>
        <line x1="32" y1="<?= $y ?>" x2="312" y2="<?= $y ?>" stroke="#eee"></line>
        <text x="28" y="<?= $y + 3 ?>" text-anchor="end" font-size="8" fill="#666"><?= $db ?></text>
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
        <span><svg width="12" height="12"><circle cx="6" cy="6" r="4" fill="none" stroke="#b33a3a" stroke-width="1.4"></circle></svg> Aérea OD</span>
        <span><svg width="12" height="12"><line x1="2" y1="2" x2="10" y2="10" stroke="#2255aa" stroke-width="1.4"></line><line x1="2" y1="10" x2="10" y2="2" stroke="#2255aa" stroke-width="1.4"></line></svg> Aérea OI</span>
        <span><svg width="12" height="12"><polyline points="9,2 3,6 9,10" fill="none" stroke="#b33a3a" stroke-width="1.4"></polyline></svg> Ósea OD</span>
        <span><svg width="12" height="12"><polyline points="3,2 9,6 3,10" fill="none" stroke="#2255aa" stroke-width="1.4"></polyline></svg> Ósea OI</span>
    </div>
    <p class="legend">Se dibuja solo con los valores de vía aérea/ósea de la derecha.</p>
</div>

<div class="audiometria-fields">
<?php $seriesShort = ['aerea' => 'Aérea', 'osea' => 'Ósea', 'ldl' => 'LDL']; ?>
<div class="card">
    <strong>Umbrales tonales</strong>
    <?php foreach (['od' => 'OD', 'oi' => 'OI'] as $side => $sideLabel): ?>
    <div class="side-block">
        <div class="side-heading">
            <span class="side-tag <?= $side ?>"><?= $sideLabel ?></span>
            <label class="inline-check"><input type="checkbox" class="igualar-toggle" data-side="<?= $side ?>" name="igualar[<?= $side ?>]" <?= isset($v['igualar'][$side]) ? 'checked' : '' ?>> Igualar ósea a aérea</label>
            <label class="inline-check"><input type="checkbox" class="ldl-toggle" data-side="<?= $side ?>" name="ldl_habilitado[<?= $side ?>]" <?= isset($v['ldl_habilitado'][$side]) ? 'checked' : '' ?>> LDL medido</label>
        </div>
        <table class="grid-table">
            <tr><th></th><?php foreach (CaseBuilder::FREQUENCIES as $f): ?><th><?= $f ?> Hz</th><?php endforeach; ?></tr>
            <?php foreach ($seriesShort as $key => $label): ?>
            <tr>
                <td class="side-label"><?= $label ?></td>
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
    <p class="legend">LDL sin marcar = no medido, se guarda como ausente (130) sin importar lo que quede escrito arriba.</p>
</div>

<div class="card">
    <strong>Logoaudiometría y pruebas especiales</strong>
    <table class="grid-table" style="margin-bottom:1rem;">
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

    <div class="two-col">
        <?php foreach (['od' => 'OD', 'oi' => 'OI'] as $side => $sideLabel): ?>
        <div class="side-block">
            <div class="side-heading"><span class="side-tag <?= $side ?>"><?= $sideLabel ?></span></div>
            <label>UMD (int / %)
                <input type="number" step="5" name="umd_int[<?= $side ?>]" value="<?= htmlspecialchars((string) fv($v, ['umd_int', $side], 35)) ?>" style="width:5rem; display:inline-block;">
                / <input type="number" step="5" name="umd_pct[<?= $side ?>]" value="<?= htmlspecialchars((string) fv($v, ['umd_pct', $side], 100)) ?>" style="width:5rem; display:inline-block;">
            </label>
            <label>SISI <input type="number" step="5" name="sisi[<?= $side ?>]" value="<?= htmlspecialchars((string) fv($v, ['sisi', $side], 0)) ?>"></label>
            <label class="inline-check"><input type="checkbox" name="stenger[<?= $side ?>]" <?= isset($v['stenger'][$side]) ? 'checked' : '' ?>> Stenger</label>
            <label class="inline-check"><input type="checkbox" name="recruit[<?= $side ?>]" <?= isset($v['recruit'][$side]) ? 'checked' : '' ?>> Reclutamiento</label>
            <label class="inline-check"><input type="checkbox" name="decay[<?= $side ?>]" <?= isset($v['decay'][$side]) ? 'checked' : '' ?>> Decay</label>
        </div>
        <?php endforeach; ?>
    </div>

    <div class="side-block">
        <div class="side-heading"><span class="side-tag">Fowler</span></div>
        <div class="two-col">
            <label>Frecuencia
                <select name="fowler_freq">
                    <?php foreach (CaseBuilder::FREQUENCIES as $i => $f): ?>
                    <option value="<?= $i ?>" <?= (int) ($v['fowler_freq'] ?? 0) === $i ? 'selected' : '' ?>><?= $f ?> Hz</option>
                    <?php endforeach; ?>
                </select>
            </label>
            <label>Cortes
                <input type="number" name="fowler_cut1" value="<?= htmlspecialchars((string) ($v['fowler_cut1'] ?? 15)) ?>" style="width:4rem; display:inline-block;">
                <input type="number" name="fowler_cut2" value="<?= htmlspecialchars((string) ($v['fowler_cut2'] ?? 30)) ?>" style="width:4rem; display:inline-block;">
                <input type="number" name="fowler_cut3" value="<?= htmlspecialchars((string) ($v['fowler_cut3'] ?? 50)) ?>" style="width:4rem; display:inline-block;">
            </label>
        </div>
    </div>
    <p class="legend">Auto (SDT/SRT) = mejor promedio de 2 de 3 (500/1000/2000 Hz vía aérea), redondeado a múltiplo de 5. Destildar para escribir un valor manual.</p>
</div>
</div>

</div>
</div>

<div class="tab-panel" data-tab="timpanometria">
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
</div>

<div class="tab-panel" data-tab="anamnesis">
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
</div>

<div class="card">
    <button type="submit" name="form_action" value="create_case">Crear caso</button>
    <a href="agenda.php" style="margin-left:1rem; font-size:0.85rem;">Cancelar</a>
</div>
</form>

<script>
// Tabs de fichas -- se activan solo si corre JS (body.js-tabs), así sin JS
// el form queda igual que antes: todas las secciones apiladas y visibles.
(function () {
    var tabButtons = document.querySelectorAll('.tab-btn');
    var tabPanels = document.querySelectorAll('.tab-panel');
    if (!tabButtons.length || !tabPanels.length) return;

    document.body.classList.add('js-tabs');

    function activate(name) {
        tabButtons.forEach(function (btn) { btn.classList.toggle('active', btn.dataset.tab === name); });
        tabPanels.forEach(function (panel) { panel.classList.toggle('active', panel.dataset.tab === name); });
    }

    tabButtons.forEach(function (btn) {
        btn.addEventListener('click', function () { activate(btn.dataset.tab); });
    });

    // Si el usuario llega con un campo inválido dentro de una ficha oculta,
    // el navegador la deja invisible y el submit falla en silencio -- al
    // interceptar el evento se salta a la ficha que tiene el campo inválido.
    document.getElementById('case-form').addEventListener('invalid', function (e) {
        var panel = e.target.closest('.tab-panel');
        if (panel) activate(panel.dataset.tab);
    }, true);
})();

// Audiograma: se redibuja solo con lo que hay en los campos de vía
// aérea/ósea -- mismas coordenadas (log de frecuencia, -10..120 dB HL)
// que audiogram_x()/audiogram_y() en PHP, que dibujan la grilla fija de
// fondo. Símbolos clínicos estándar: círculo/cruz = aérea OD/OI (rojo/azul),
// "<"/">"= ósea OD/OI.
window.drawAudiogram = (function () {
    var NS = 'http://www.w3.org/2000/svg';
    var MIN_LOG = Math.log(125) / Math.LN2;
    var MAX_LOG = Math.log(8000) / Math.LN2;
    var FREQS = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000];

    function xPos(freq) { return 32 + (Math.log(freq) / Math.LN2 - MIN_LOG) / (MAX_LOG - MIN_LOG) * 280; }
    function yPos(db) {
        db = Math.max(-10, Math.min(120, db));
        return 10 + (db - (-10)) / 130 * 266;
    }
    function readVals(key, side) {
        var vals = [];
        for (var n = 0; n < FREQS.length; n++) {
            var el = document.getElementById(key + '_' + side + '_' + n);
            vals.push(el ? (parseInt(el.value, 10) || 0) : 0);
        }
        return vals;
    }
    function makeCross(x, y, color) {
        var g = document.createElementNS(NS, 'g');
        var r = 4.5;
        [[x - r, y - r, x + r, y + r], [x - r, y + r, x + r, y - r]].forEach(function (c) {
            var l = document.createElementNS(NS, 'line');
            l.setAttribute('x1', c[0]); l.setAttribute('y1', c[1]); l.setAttribute('x2', c[2]); l.setAttribute('y2', c[3]);
            l.setAttribute('stroke', color); l.setAttribute('stroke-width', '1.5');
            g.appendChild(l);
        });
        return g;
    }
    function makeCircle(x, y, color) {
        var c = document.createElementNS(NS, 'circle');
        c.setAttribute('cx', x); c.setAttribute('cy', y); c.setAttribute('r', 4.5);
        c.setAttribute('fill', 'none'); c.setAttribute('stroke', color); c.setAttribute('stroke-width', '1.5');
        return c;
    }
    function makeBracket(x, y, color, dir) {
        var r = 4.5;
        var pts = dir === 'left'
            ? (x + r) + ',' + (y - r) + ' ' + (x - r) + ',' + y + ' ' + (x + r) + ',' + (y + r)
            : (x - r) + ',' + (y - r) + ' ' + (x + r) + ',' + y + ' ' + (x - r) + ',' + (y + r);
        var p = document.createElementNS(NS, 'polyline');
        p.setAttribute('points', pts);
        p.setAttribute('fill', 'none'); p.setAttribute('stroke', color); p.setAttribute('stroke-width', '1.5');
        return p;
    }

    var SERIES = [
        { key: 'aerea', side: 'od', color: '#b33a3a', line: true, make: makeCircle },
        { key: 'aerea', side: 'oi', color: '#2255aa', line: true, make: makeCross },
        { key: 'osea', side: 'od', color: '#b33a3a', line: false, make: function (x, y, c) { return makeBracket(x, y, c, 'left'); } },
        { key: 'osea', side: 'oi', color: '#2255aa', line: false, make: function (x, y, c) { return makeBracket(x, y, c, 'right'); } },
    ];

    return function drawAudiogram() {
        var group = document.getElementById('audiogram-data');
        if (!group) return;
        while (group.firstChild) group.removeChild(group.firstChild);

        SERIES.forEach(function (s) {
            var points = readVals(s.key, s.side).map(function (v, i) { return [xPos(FREQS[i]), yPos(v)]; });
            if (s.line) {
                var poly = document.createElementNS(NS, 'polyline');
                poly.setAttribute('points', points.map(function (p) { return p.join(','); }).join(' '));
                poly.setAttribute('fill', 'none');
                poly.setAttribute('stroke', s.color);
                poly.setAttribute('stroke-width', '1.3');
                group.appendChild(poly);
            }
            points.forEach(function (p) { group.appendChild(s.make(p[0], p[1], s.color)); });
        });
    };
})();

(function () {
    var form = document.getElementById('case-form');
    if (!form) return;
    // Delegado: cubre tipeo directo en vía aérea/ósea. El caso de "igualar"
    // (que escribe osea.value por JS sin evento input) se cubre aparte,
    // llamando drawAudiogram() desde syncOsea() más abajo.
    form.addEventListener('input', function (e) {
        if (e.target.id && /^(aerea|osea)_/.test(e.target.id)) window.drawAudiogram();
    });
    window.drawAudiogram();
})();

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
            if (window.drawAudiogram) window.drawAudiogram();
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
