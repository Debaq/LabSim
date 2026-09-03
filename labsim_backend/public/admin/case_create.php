<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/CaseBuilder.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/PatientPhoto.php';
require_once __DIR__ . '/../../src/Patients.php';

/**
 * Crea un caso clínico completo desde el navegador -- equivalente web de
 * src/create_a.py (hoy solo existe en la app de escritorio, permission=777).
 * Guarda en `cases` con el mismo shape de JSON que espera el cliente
 * (Audiometer.py/Z.py/ListWords.py al atender), y redirige a agenda.php
 * para completar fecha/hora/RUT -- ese formulario ya existe, no se duplica.
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();

// Editar un caso existente: ?edit=<id> precarga el formulario con lo ya
// guardado (reverso de CaseBuilder::buildCaseData). En un POST el id viaja
// en el campo oculto "case_id" -- $_GET no sobrevive el submit.
$editId = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $editId = trim((string) ($_POST['case_id'] ?? '')) ?: null;
} elseif (isset($_GET['edit'])) {
    $editId = trim((string) $_GET['edit']) ?: null;
}
$editCase = null;
if ($editId !== null) {
    $stmt = $pdo->prepare('SELECT id, data FROM cases WHERE id = ?');
    $stmt->execute([$editId]);
    $editCase = $stmt->fetch();
    if ($editCase === false) {
        admin_header('Editar caso clínico', $me);
        echo '<p class="error">El caso ' . htmlspecialchars($editId) . ' no existe.</p>';
        echo '<p><a href="agenda.php">&larr; Volver</a></p>';
        admin_footer();
        exit;
    }
}
$isEdit = $editCase !== null;

// Paciente real: vive en `patients`, referenciado por cases.patient_id (ver
// Db::migratePatientsIfNeeded para casos que existían de antes de esa
// tabla). $editAge de acá abajo es solo un fallback a partir de fecha_nac
// para casos viejos guardados antes de que 'edad' existiera en cases.data --
// la edad en sí es propia del caso, no depende del paciente.
$editPatientId = null;
$editPatient = null;
$editAge = null;
$editFechaNacDisplay = '';
if ($isEdit) {
    $stmt = $pdo->prepare('SELECT patient_id FROM cases WHERE id = ?');
    $stmt->execute([$editId]);
    $pid = $stmt->fetchColumn();
    $editPatientId = ($pid !== false && $pid !== null) ? (int) $pid : null;
    if ($editPatientId !== null) {
        $editPatient = Patients::find($pdo, $editPatientId);
    }
    $fechaNac = $editPatient['fecha_nac'] ?? '';
    if ($fechaNac === '') {
        // Caso huérfano nunca migrado a patients (sin patient_id todavía) --
        // mismo fallback que antes al paciente_snapshot legado.
        $existingData = json_decode($editCase['data'] ?? '', true);
        $snapshot = is_array($existingData) ? ($existingData['paciente_snapshot'] ?? []) : [];
        $fechaNac = $snapshot['fecha_nac'] ?? '';
        if ($editPatient === null) {
            $editPatient = [
                'rut' => $snapshot['rut'] ?? '',
                'nombre' => $snapshot['nombre'] ?? '',
                'apellido' => $snapshot['apellido'] ?? '',
                'fecha_nac' => $fechaNac,
            ];
        }
    }
    foreach (['d-m-Y', 'd-m-y'] as $fmt) {
        $birth = DateTime::createFromFormat($fmt, $fechaNac);
        if ($birth !== false) {
            $year = (int) $birth->format('Y');
            if ($fmt === 'd-m-y' && $year > (int) date('Y')) {
                $year -= 100;
            }
            $editAge = max(0, (int) date('Y') - $year);
            $editFechaNacDisplay = sprintf('%04d-%02d-%02d', $year, (int) $birth->format('m'), (int) $birth->format('d'));
            break;
        }
    }
}
$editDisplayName = $editPatient !== null ? trim(($editPatient['nombre'] ?? '') . ' ' . ($editPatient['apellido'] ?? '')) : '';

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

// Geometría del logoaudiograma (curva de discriminación % vs intensidad),
// mismo plot box que el audiograma pero ejes lineales en ambos sentidos:
// X = dB HL (-10..120, igual rango que audiogram_y), Y = % discriminación
// (0 abajo, 100 arriba) -- si se cambia acá, cambiar también en
// drawLogogram()/logoX()/logoY() en el <script> de más abajo.
function logogram_x(float $db): float
{
    $db = max(-10, min(120, $db));
    return 32 + ($db - (-10)) / 130 * 280;
}
function logogram_y(float $pct): float
{
    $pct = max(0, min(100, $pct));
    return 10 + (100 - $pct) / 100 * 266;
}

// Geometría del timpanograma (compliance vs presión), mismo plot box que el
// audiograma. X = presión en daPa (-400..200), Y = compliance/admitancia en
// mL (0..2.5) -- si se cambia acá, cambiar también en drawTympanogram() en JS.
function tymp_x(float $daPa): float
{
    $daPa = max(-400, min(200, $daPa));
    return 32 + ($daPa - (-400)) / 600 * 280;
}
function tymp_y(float $compliance): float
{
    $compliance = max(0, min(2.5, $compliance));
    return 276 - $compliance / 2.5 * 266;
}

$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $v = $_POST; // sticky form: se redibuja con lo ya tipeado, tanto al generar nombre como si falla la validación
} elseif ($isEdit) {
    $existingData = json_decode($editCase['data'] ?? '', true);
    $v = CaseBuilder::caseDataToForm(is_array($existingData) ? $existingData : []);
    if ($v['age'] === '') {
        // Caso guardado antes de que 'edad' existiera en cases.data -- fallback
        // único a la fecha_nac de la cita, solo para no dejar el campo vacío.
        $v['age'] = (string) ($editAge ?? '');
    }
    $v['rut'] = $editPatient['rut'] ?? '';
    $v['nombre'] = $editPatient['nombre'] ?? '';
    $v['apellido'] = $editPatient['apellido'] ?? '';
    $v['fecha_nac'] = $editFechaNacDisplay;
} else {
    $v = [];
}

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
    } elseif ($formAction === 'create_case' || $formAction === 'update_case') {
        $isUpdate = $formAction === 'update_case';
        // Edad = propia del paciente/caso, se guarda en cases.data ('edad').
        // Editable siempre acá, en creación y en edición -- la agenda no
        // incide en esto para nada, solo guarda la fecha de la cita.
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

        $reflexType = ['od' => 'normal', 'oi' => 'normal'];
        foreach (['od', 'oi'] as $side) {
            $type = (string) fv($v, ['reflex_type', $side], 'normal');
            if (in_array($type, CaseBuilder::REFLEX_CURVE_TYPES, true)) {
                $reflexType[$side] = $type;
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

        // Acumetría (Rinne/Weber), auto-calculada desde los umbrales tonales
        // ya cargados arriba ($aerea/$osea, índices de CaseBuilder::ACUMETRIA_FREQS)
        // salvo que el docente haya destildado el "auto" de ese campo -- mismo
        // patrón que sdt_auto/srt_auto con Fletcher.
        $rinne = [];
        $weber = [];
        $acumetriaValid = true;
        foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx) {
            $rinne[$hz] = [];
            foreach (['od', 'oi'] as $side) {
                $isAuto = !isset($v['rinne_auto']) || isset($v['rinne_auto'][$hz][$side]);
                if ($isAuto) {
                    $rinne[$hz][$side] = CaseBuilder::rinneAuto($aerea[$side][$freqIdx], $osea[$side][$freqIdx]);
                } else {
                    $manual = (string) fv($v, ['rinne', $hz, $side], 'positivo');
                    if (!in_array($manual, CaseBuilder::RINNE_OPTIONS, true)) {
                        $acumetriaValid = false;
                    }
                    $rinne[$hz][$side] = $manual;
                }
            }
            $isWeberAuto = !isset($v['weber_auto']) || isset($v['weber_auto'][$hz]);
            if ($isWeberAuto) {
                $weber[$hz] = CaseBuilder::weberAuto($osea['od'][$freqIdx], $osea['oi'][$freqIdx]);
            } else {
                $manualWeber = (string) fv($v, ['weber', $hz], 'centrado');
                if (!in_array($manualWeber, CaseBuilder::WEBER_OPTIONS, true)) {
                    $acumetriaValid = false;
                }
                $weber[$hz] = $manualWeber;
            }
        }
        $bonePairs = zip_pairs($osea['od'], $osea['oi']);
        // Qué frecuencias califican para Fowler/I.W.A. se detecta solo de
        // los umbrales -- el alumno puede encontrarlo en cualquiera de
        // ellas, así que se pide un patrón de reclutamiento por cada una
        // (no una única frecuencia "elegida" al crear el caso).
        $fowlerQualifying = CaseBuilder::fowlerQualifyingFreqs($airPairs, $bonePairs);
        $fowlerPatterns = [];
        foreach ($fowlerQualifying as $freq) {
            $pattern = (string) fv($v, ['fowler_pattern', (string) $freq], 'none');
            if (!array_key_exists($pattern, CaseBuilder::FOWLER_PATTERNS)) {
                $pattern = 'none';
            }
            $fowlerPatterns[(string) $freq] = $pattern;
        }
        $fowlerEnabled = count($fowlerPatterns) > 0;
        $fowlerDiplacusia = isset($v['diplacusia']);

        // Acufenometría: lateralidad (craneal/unilateral/bilateral) es
        // independiente de permanente/ocasional -- un tinnitus unilateral
        // puede ser permanente igual que uno bilateral. Solo "unilateral"
        // pide oído; "bilateral" admite predominio (asimetría), opcional.
        // Pulsátil es otro flag aparte. Ruido + frecuencia (matching, Hz)
        // son "la forma".
        $tinnitusLateralidad = (string) ($v['tinnitus']['lateralidad'] ?? 'craneal');
        $tinnitusOido = (string) ($v['tinnitus']['oido'] ?? 'od');
        $tinnitusPredominio = (string) ($v['tinnitus']['predominio'] ?? 'igual');
        $tinnitusPermanente = isset($v['tinnitus']['permanente']);
        $tinnitusRuido = (string) ($v['tinnitus']['ruido'] ?? CaseBuilder::TINNITUS_RUIDO_OPTIONS[0]);
        $tinnitusFrecuencia = (int) ($v['tinnitus']['frecuencia'] ?? CaseBuilder::FREQUENCIES[0]);

        if ($age <= 0) {
            $error = 'Falta la edad.';
        } elseif (!$isUpdate && ($nombre1 === '' || $apellido1 === '')) {
            $error = 'Falta el nombre del paciente (generalo con el botón o escríbelo a mano).';
        } elseif ($isUpdate && (trim((string) ($v['nombre'] ?? '')) === '' || trim((string) ($v['apellido'] ?? '')) === '')) {
            $error = 'Falta el nombre del paciente.';
        } elseif (!in_array($zOd, CaseBuilder::Z_OPTIONS, true) || !in_array($zOi, CaseBuilder::Z_OPTIONS, true)) {
            $error = 'Tipo de timpanograma inválido.';
        } elseif (!in_array($etfOd, CaseBuilder::ETF_OPTIONS, true) || !in_array($etfOi, CaseBuilder::ETF_OPTIONS, true)) {
            $error = 'Valor de ETF inválido.';
        } elseif (!$acumetriaValid) {
            $error = 'Valor de Rinne/Weber inválido.';
        } elseif (!in_array($tinnitusLateralidad, CaseBuilder::TINNITUS_LATERALIDAD_OPTIONS, true)) {
            $error = 'Lateralidad del tinnitus inválida.';
        } elseif ($tinnitusLateralidad === 'unilateral' && !in_array($tinnitusOido, ['od', 'oi'], true)) {
            $error = 'Falta el oído del tinnitus (unilateral, hay que indicar cuál).';
        } elseif (!in_array($tinnitusPredominio, CaseBuilder::TINNITUS_PREDOMINIO_OPTIONS, true)) {
            $error = 'Predominio del tinnitus inválido.';
        } elseif (!in_array($tinnitusRuido, CaseBuilder::TINNITUS_RUIDO_OPTIONS, true)) {
            $error = 'Tipo de ruido del tinnitus inválido.';
        } elseif (!in_array($tinnitusFrecuencia, CaseBuilder::FREQUENCIES, true)) {
            $error = 'Frecuencia del tinnitus inválida.';
        }

        if ($error === null) {
            $antecedentes = [];
            foreach (CaseBuilder::HIST_CHECKBOXES as $h) {
                $antecedentes[$h] = isset($v['hist'][$h]);
            }

            $id = $isUpdate ? $editId : CaseBuilder::nextCaseId($pdo);
            $data = CaseBuilder::buildCaseData([
                'gender' => $gender,
                'age' => $age,
                'id' => $id,
                'aerea' => $airPairs,
                'osea' => zip_pairs($osea['od'], $osea['oi']),
                'ldl' => zip_pairs($ldl['od'], $ldl['oi']),
                'z_od' => $zOd,
                'z_oi' => $zOi,
                'rinne' => $rinne,
                'weber' => $weber,
                'umd' => [
                    ['int' => (int) fv($v, ['umd_int', 'od'], 35), 'percentage' => (int) fv($v, ['umd_pct', 'od'], 100)],
                    ['int' => (int) fv($v, ['umd_int', 'oi'], 35), 'percentage' => (int) fv($v, ['umd_pct', 'oi'], 100)],
                ],
                'sdt' => $sdt,
                'srt' => $srt,
                'fowler' => [
                    'enabled' => $fowlerEnabled,
                    'patterns' => $fowlerPatterns,
                    'diplacusia' => $fowlerDiplacusia,
                ],
                'stenger' => [isset($v['stenger']['od']), isset($v['stenger']['oi'])],
                'sisi' => [(int) fv($v, ['sisi', 'od'], 0), (int) fv($v, ['sisi', 'oi'], 0)],
                'recruit' => [isset($v['recruit']['od']), isset($v['recruit']['oi'])],
                'decay' => [isset($v['decay']['od']), isset($v['decay']['oi'])],
                'reflex' => [
                    'ipsi' => zip_pairs($reflexIpsi['od'], $reflexIpsi['oi']),
                    'contra' => zip_pairs($reflexContra['od'], $reflexContra['oi']),
                    'tipo' => $reflexType,
                ],
                'etf_od' => $etfOd,
                'etf_oi' => $etfOi,
                'tinnitus' => [
                    'lateralidad' => $tinnitusLateralidad,
                    'oido' => $tinnitusLateralidad === 'unilateral' ? $tinnitusOido : null,
                    'predominio' => $tinnitusLateralidad === 'bilateral' ? $tinnitusPredominio : null,
                    'pulsatil' => isset($v['tinnitus']['pulsatil']),
                    'permanente' => $tinnitusPermanente,
                    'ruido' => $tinnitusRuido,
                    'frecuencia' => $tinnitusFrecuencia,
                ],
                'anamnesis' => [
                    'antecedentes' => $antecedentes,
                    'medicamentos' => trim((string) ($v['medicamentos'] ?? '')),
                    'cirugias' => trim((string) ($v['cirugias'] ?? '')),
                    'otros' => trim((string) ($v['otros'] ?? '')),
                ],
                'comportamiento' => trim((string) ($v['comportamiento'] ?? '')),
                'disposicion' => (int) ($v['disposicion'] ?? 0),
            ]);

            if ($isUpdate) {
                $editRut = trim((string) ($v['rut'] ?? ''));
                $editNombre = trim((string) ($v['nombre'] ?? ''));
                $editApellido = trim((string) ($v['apellido'] ?? ''));
                $editFechaNacIso = trim((string) ($v['fecha_nac'] ?? ''));
                $editFechaNacVal = $editFechaNacIso !== '' ? date('d-m-Y', strtotime($editFechaNacIso)) : '';

                if ($editPatientId !== null) {
                    Patients::update($pdo, $editPatientId, $editRut, $editNombre, $editApellido, $editFechaNacVal);
                } else {
                    $editPatientId = Patients::upsertByRut($pdo, $editRut, $editNombre, $editApellido, $editFechaNacVal);
                }

                // paciente_snapshot: se mantiene sincronizado con patients --
                // agenda.php lo sigue leyendo para precargar el formulario de
                // "Agendar" cuando el caso todavía no tiene cita propia (ver
                // Cases::snapshotBeforeAppointmentDelete).
                $priorData = json_decode($editCase['data'] ?? '', true);
                $priorSnapshot = (is_array($priorData) && isset($priorData['paciente_snapshot'])) ? $priorData['paciente_snapshot'] : [];
                $data['paciente_snapshot'] = array_merge($priorSnapshot, [
                    'nombre' => $editNombre,
                    'apellido' => $editApellido,
                    'rut' => $editRut,
                    'fecha_nac' => $editFechaNacVal,
                ]);

                $pdo->prepare(
                    'UPDATE cases SET data = ?, patient_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
                )->execute([json_encode($data, JSON_UNESCAPED_UNICODE), $editPatientId, $id]);
                AdminAudit::log($me, 'case_update', ['case_id' => $id]);
                AdminAudit::log($me, 'patient_update', ['case_id' => $id, 'patient_id' => $editPatientId]);

                header('Location: agenda.php');
                exit;
            }

            // paciente_snapshot: mismo mecanismo que Cases::snapshotBeforeAppointmentDelete
            // -- agenda.php ya sabe leer esta clave para precargar el formulario de
            // agendado cuando el caso todavía no tiene cita propia, así no hay que
            // re-tipear nombre/RUT que recién se generaron acá.
            $nombre2 = trim((string) ($v['nombre2'] ?? ''));
            $apellido2 = trim((string) ($v['apellido2'] ?? ''));
            $snapshotNombre = trim($nombre1 . ' ' . $nombre2);
            $snapshotApellido = trim($apellido1 . ' ' . $apellido2);
            $snapshotRut = (string) CaseBuilder::rutFromAge($age);
            $snapshotFechaNac = sprintf('01-01-%04d', (int) date('Y') - $age);
            $data['paciente_snapshot'] = [
                'nombre' => $snapshotNombre,
                'apellido' => $snapshotApellido,
                'rut' => $snapshotRut,
                'fecha_nac' => $snapshotFechaNac,
                'procedimiento' => 'Audiometría',
            ];

            $newPatientId = Patients::upsertByRut($pdo, $snapshotRut, $snapshotNombre, $snapshotApellido, $snapshotFechaNac);

            $pdo->prepare(
                "INSERT INTO cases (id, data, updated_at, patient_id) VALUES (?, ?, CURRENT_TIMESTAMP, ?)
                 ON CONFLICT(id) DO UPDATE SET data = excluded.data, updated_at = CURRENT_TIMESTAMP, patient_id = excluded.patient_id"
            )->execute([$id, json_encode($data, JSON_UNESCAPED_UNICODE), $newPatientId]);
            AdminAudit::log($me, 'case_create', ['case_id' => $id, 'nombre' => $snapshotNombre, 'apellido' => $snapshotApellido]);

            header('Location: agenda.php?schedule=' . urlencode($id));
            exit;
        }
    }
}

admin_header($isEdit ? 'Editar caso clínico ' . $editId : 'Crear caso clínico', $me);
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
    .audiogram-stack { position: sticky; top: 1rem; display: flex; flex-direction: column; gap: 1rem; }
    @media (max-width: 960px) {
        .audiometria-layout { grid-template-columns: 1fr; }
        .audiogram-stack { position: static; }
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

    /* Patrón de reflejos: tabla espejada -- columnas ipsi al centro (una
       junto a la otra), contra hacia afuera, para leer ambos oídos "de
       frente" como en la ficha en papel. */
    .reflex-pattern-table { width: 100%; border-collapse: collapse; margin-top: 0.5rem; font-size: 0.8rem; }
    .reflex-pattern-table th, .reflex-pattern-table td { text-align: center; padding: 0.35rem 0.2rem; border: 1px solid #ddd; }
    .reflex-pattern-table td.freq-label { font-weight: 600; background: #f7f7f7; }
    /* th.od/th.oi con color: NO reusar .side-tag acá -- su display:
       inline-block rompe el layout de columnas de una tabla (th deja de
       comportarse como table-cell), que fue justo lo que descuadró el
       encabezado. */
    th.reflex-head.od { color: #b33a3a; }
    th.reflex-head.oi { color: #2255aa; }
    .reflex-cell { font-weight: 700; color: #999; }
    .reflex-cell.na { color: #ccc; background: #f5f5f5; }
    /* Presente = fondo gris oscuro fijo (no varía por lado); el color del
       "+" marca el oído que recibió el estímulo -- en ipsi coincide con la
       columna (OD=rojo, OI=azul), en contra es el cruzado (columna OD con
       estímulo en OI=azul, columna OI con estímulo en OD=rojo). */
    .reflex-cell.present { background: #3a3a3a; }
    .reflex-cell.present.mark-od { color: #e05c5c; }
    .reflex-cell.present.mark-oi { color: #6fa8e8; }

    /* Foto de paciente: avatar circular + modal de recorte. */
    .photo-block { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid #eee; }
    .patient-avatar { width: 84px; height: 84px; border-radius: 50%; object-fit: cover; background: #eee; flex-shrink: 0; }
    .patient-avatar-empty { display: flex; align-items: center; justify-content: center; color: #999; font-size: 0.7rem; text-align: center; }

    .photo-modal { position: fixed; inset: 0; background: rgba(0,0,0,0.6); z-index: 100;
                   display: flex; align-items: center; justify-content: center; }
    .photo-modal[hidden] { display: none; }
    .photo-modal-box { background: #fff; border-radius: 8px; padding: 1.2rem; max-width: 22rem; width: 90%; }
    .photo-crop-viewport { position: relative; width: 280px; height: 280px; margin: 0 auto;
                            overflow: hidden; background: #333; cursor: grab; touch-action: none; }
    .photo-crop-viewport:active { cursor: grabbing; }
    .photo-crop-viewport img { position: absolute; left: 0; top: 0; transform-origin: 0 0; max-width: none; user-select: none; -webkit-user-drag: none; }
    .photo-crop-ring { position: absolute; inset: 0; border-radius: 50%; box-shadow: 0 0 0 2000px rgba(0,0,0,0.5); pointer-events: none; }
    .photo-modal-actions { display: flex; justify-content: flex-end; gap: 0.5rem; margin-top: 0.8rem; }
</style>

<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>

<form method="post" id="case-form">
<?= csrf_field() ?>
<?php if ($isEdit): ?><input type="hidden" name="case_id" value="<?= htmlspecialchars($editId) ?>"><?php endif; ?>
<div class="tabs" role="tablist">
    <button type="button" class="tab-btn active" data-tab="paciente">Paciente</button>
    <button type="button" class="tab-btn" data-tab="audiometria">Audiometría</button>
    <button type="button" class="tab-btn" data-tab="timpanometria">Timpanometría</button>
    <button type="button" class="tab-btn" data-tab="tinnitus">Tinnitus</button>
    <button type="button" class="tab-btn" data-tab="anamnesis">Anamnesis</button>
</div>

<div class="tab-panel active" data-tab="paciente">
<div class="card">
    <strong>Paciente</strong>
    <?php if ($isEdit): ?><input type="hidden" id="chat-static-name" value="<?= htmlspecialchars($editDisplayName) ?>"><?php endif; ?>
    <label class="inline-check"><input type="radio" name="gender" value="0" <?= ($v['gender'] ?? '0') === '0' ? 'checked' : '' ?>> Hombre</label>
    <label class="inline-check"><input type="radio" name="gender" value="1" <?= ($v['gender'] ?? '0') === '1' ? 'checked' : '' ?>> Mujer</label>
    <label>Edad
        <input type="number" name="age" min="0" max="110" value="<?= htmlspecialchars((string) ($v['age'] ?? '')) ?>">
    </label>
    <?php if (!$isEdit): ?>
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
    <?php else: ?>
    <div class="two-col">
        <label>Nombre
            <input type="text" name="nombre" value="<?= htmlspecialchars((string) ($v['nombre'] ?? '')) ?>">
        </label>
        <label>Apellido
            <input type="text" name="apellido" value="<?= htmlspecialchars((string) ($v['apellido'] ?? '')) ?>">
        </label>
        <label>RUT
            <input type="text" name="rut" value="<?= htmlspecialchars((string) ($v['rut'] ?? '')) ?>">
        </label>
        <label>Fecha de nacimiento
            <input type="date" name="fecha_nac" value="<?= htmlspecialchars((string) ($v['fecha_nac'] ?? '')) ?>">
        </label>
    </div>
    <p class="legend" style="font-size:0.8rem;">Esto edita al <strong>paciente</strong>: el cambio se aplica también a cualquier otra cita/ronda de la misma persona.</p>
    <?php endif; ?>

    <?php if ($isEdit): ?>
    <div class="photo-block">
        <strong style="display:block; margin-bottom:0.4rem;">Foto</strong>
        <p id="photo-msg" class="legend" hidden></p>
        <?php $hasAvatar = PatientPhoto::hasAvatar($editId); ?>
        <div style="display:flex; align-items:center; gap:1rem;">
            <img id="patient-avatar-preview" class="patient-avatar"
                 src="patient_photo.php?case_id=<?= urlencode($editId) ?>&amp;type=avatar&amp;v=<?= time() ?>"
                 alt="Avatar del paciente" <?= $hasAvatar ? '' : 'hidden' ?>>
            <div id="patient-avatar-empty" class="patient-avatar patient-avatar-empty" <?= $hasAvatar ? 'hidden' : '' ?>>Sin foto</div>
            <div>
                <input type="file" id="patient-photo-input" accept="image/jpeg,image/png,image/webp">
                <p class="legend">Al elegir una foto se abre un recorte circular -- se guarda una versión reducida completa y el avatar recortado.</p>
            </div>
        </div>
    </div>
    <?php else: ?>
    <p class="legend" style="margin-top:1rem;">La foto se sube después de guardar el paciente por primera vez.</p>
    <?php endif; ?>
</div>
</div>

<div class="tab-panel" data-tab="audiometria">
<div class="audiometria-layout">

<div class="audiogram-stack">
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
        <span><svg width="12" height="12"><polygon points="6,2 2,10 10,10" fill="none" stroke="#b33a3a" stroke-width="1.4"></polygon></svg> Aérea OD enmasc.</span>
        <span><svg width="12" height="12"><line x1="2" y1="2" x2="10" y2="10" stroke="#2255aa" stroke-width="1.4"></line><line x1="2" y1="10" x2="10" y2="2" stroke="#2255aa" stroke-width="1.4"></line></svg> Aérea OI</span>
        <span><svg width="12" height="12"><rect x="2" y="2" width="8" height="8" fill="none" stroke="#2255aa" stroke-width="1.4"></rect></svg> Aérea OI enmasc.</span>
        <span><svg width="12" height="12"><polyline points="9,2 3,6 9,10" fill="none" stroke="#b33a3a" stroke-width="1.4"></polyline></svg> Ósea OD</span>
        <span><svg width="12" height="12"><polyline points="8,2 3,2 3,10 8,10" fill="none" stroke="#b33a3a" stroke-width="1.4"></polyline></svg> Ósea OD enmasc.</span>
        <span><svg width="12" height="12"><polyline points="3,2 9,6 3,10" fill="none" stroke="#2255aa" stroke-width="1.4"></polyline></svg> Ósea OI</span>
        <span><svg width="12" height="12"><polyline points="4,2 9,2 9,10 4,10" fill="none" stroke="#2255aa" stroke-width="1.4"></polyline></svg> Ósea OI enmasc.</span>
        <span><svg width="12" height="12"><polygon points="6,9 2,3 10,3" fill="#b33a3a" stroke="none"></polygon></svg> LDL OD</span>
        <span><svg width="12" height="12"><polygon points="6,9 2,3 10,3" fill="#2255aa" stroke="none"></polygon></svg> LDL OI</span>
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
        <span><svg width="12" height="12"><circle cx="6" cy="6" r="3" fill="#b33a3a" stroke="none"></circle></svg> SDT OD</span>
        <span><svg width="12" height="12"><circle cx="6" cy="6" r="3" fill="#2255aa" stroke="none"></circle></svg> SDT OI</span>
        <span><svg width="12" height="12"><line x1="6" y1="1" x2="6" y2="11" stroke="#b33a3a" stroke-width="1.4" stroke-dasharray="2,2"></line></svg> SRT OD</span>
        <span><svg width="12" height="12"><line x1="6" y1="1" x2="6" y2="11" stroke="#2255aa" stroke-width="1.4" stroke-dasharray="2,2"></line></svg> SRT OI</span>
        <span><svg width="12" height="12"><polygon points="6,2 2,10 10,10" fill="#b33a3a" stroke="none"></polygon></svg> UMD OD</span>
        <span><svg width="12" height="12"><polygon points="6,2 2,10 10,10" fill="#2255aa" stroke="none"></polygon></svg> UMD OI</span>
    </div>
</div>
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
    <strong>Acumetría (Rinne / Weber) &mdash; diapasones 500 y 1000 Hz</strong>
    <table class="grid-table" style="margin-bottom:0.5rem;">
        <tr><th></th><?php foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx): ?><th><?= $hz ?> Hz</th><?php endforeach; ?></tr>
        <?php foreach (['od' => 'OD', 'oi' => 'OI'] as $side => $sideLabel): ?>
        <tr>
            <td class="side-label">Rinne <?= $sideLabel ?></td>
            <?php foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx):
                $rinneIsAuto = !isset($v['rinne_auto']) || isset($v['rinne_auto'][$hz][$side]);
                $rinneVal = (string) fv($v, ['rinne', $hz, $side], 'positivo');
            ?>
            <td>
                <select id="rinne_<?= $freqIdx ?>_<?= $side ?>" class="rinne-select" data-freq="<?= $freqIdx ?>" data-side="<?= $side ?>"
                        name="rinne[<?= $hz ?>][<?= $side ?>]" <?= $rinneIsAuto ? 'disabled' : '' ?>>
                    <?php foreach (CaseBuilder::RINNE_LABELS as $opt => $optLabel): ?>
                    <option value="<?= $opt ?>" <?= $rinneVal === $opt ? 'selected' : '' ?>><?= htmlspecialchars($optLabel) ?></option>
                    <?php endforeach; ?>
                </select>
                <label class="inline-check"><input type="checkbox" class="rinne-auto-toggle" data-freq="<?= $freqIdx ?>" data-side="<?= $side ?>"
                       name="rinne_auto[<?= $hz ?>][<?= $side ?>]" <?= $rinneIsAuto ? 'checked' : '' ?>>auto</label>
            </td>
            <?php endforeach; ?>
        </tr>
        <?php endforeach; ?>
        <tr>
            <td class="side-label">Weber</td>
            <?php foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx):
                $weberIsAuto = !isset($v['weber_auto']) || isset($v['weber_auto'][$hz]);
                $weberVal = (string) fv($v, ['weber', $hz], 'centrado');
            ?>
            <td>
                <select id="weber_<?= $freqIdx ?>" class="weber-select" data-freq="<?= $freqIdx ?>"
                        name="weber[<?= $hz ?>]" <?= $weberIsAuto ? 'disabled' : '' ?>>
                    <?php foreach (CaseBuilder::WEBER_LABELS as $opt => $optLabel): ?>
                    <option value="<?= $opt ?>" <?= $weberVal === $opt ? 'selected' : '' ?>><?= htmlspecialchars($optLabel) ?></option>
                    <?php endforeach; ?>
                </select>
                <label class="inline-check"><input type="checkbox" class="weber-auto-toggle" data-freq="<?= $freqIdx ?>"
                       name="weber_auto[<?= $hz ?>]" <?= $weberIsAuto ? 'checked' : '' ?>>auto</label>
            </td>
            <?php endforeach; ?>
        </tr>
    </table>
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
                <input type="number" step="5" class="umd-int-input" data-side="<?= $side ?>" name="umd_int[<?= $side ?>]" value="<?= htmlspecialchars((string) fv($v, ['umd_int', $side], 35)) ?>" style="width:5rem; display:inline-block;">
                / <input type="number" step="5" class="umd-pct-input" data-side="<?= $side ?>" name="umd_pct[<?= $side ?>]" value="<?= htmlspecialchars((string) fv($v, ['umd_pct', $side], 100)) ?>" style="width:5rem; display:inline-block;">
            </label>
            <label>SISI <input type="number" step="5" name="sisi[<?= $side ?>]" value="<?= htmlspecialchars((string) fv($v, ['sisi', $side], 0)) ?>"></label>
            <label class="inline-check"><input type="checkbox" name="stenger[<?= $side ?>]" <?= isset($v['stenger'][$side]) ? 'checked' : '' ?>> Stenger</label>
            <label class="inline-check"><input type="checkbox" class="recruit-toggle" data-side="<?= $side ?>" name="recruit[<?= $side ?>]" <?= isset($v['recruit'][$side]) ? 'checked' : '' ?>> Reclutamiento</label>
            <label class="inline-check"><input type="checkbox" name="decay[<?= $side ?>]" <?= isset($v['decay'][$side]) ? 'checked' : '' ?>> Decay</label>
        </div>
        <?php endforeach; ?>
    </div>

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
        <p class="legend">Se detectan solas las frecuencias (250-4000 Hz) donde los umbrales ya tipeados arriba cumplen los requisitos ABLB -- puede calificar más de una a la vez. Para cada una, indica qué le pasa al paciente al hacer la prueba ahí (por defecto, sin reclutamiento).</p>
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
        <p class="legend" id="fowler-none-msg" <?= $fwQualifying ? 'hidden' : '' ?>>Ningún umbral actual cumple los requisitos ABLB -- Fowler queda deshabilitado en este caso.</p>
        <label class="inline-check"><input type="checkbox" name="diplacusia" <?= isset($v['diplacusia']) ? 'checked' : '' ?>> Paciente refiere diploacusia</label>
        <p class="legend">Requisitos ABLB: oído de referencia ≤ <?= CaseBuilder::FOWLER_NORMAL_HL ?> dB HL, oído en estudio &gt; <?= CaseBuilder::FOWLER_NORMAL_HL ?> dB HL y sensorioneural (gap aéreo-óseo ≤ <?= CaseBuilder::FOWLER_SNHL_GAP_MAX ?> dB), diferencia interaural <?= CaseBuilder::FOWLER_DIFF_MIN ?>-<?= CaseBuilder::FOWLER_DIFF_MAX ?> dB en cada frecuencia evaluada.</p>
        <p class="legend">Sin reclutamiento = el paciente nunca iguala. Parcial = se acerca pero no cierra del todo. Completo = iguala sonoridad. Sobre-reclutamiento = en niveles altos el oído afectado empieza a sonar más fuerte que el sano.</p>
    </div>
    <p class="legend">Auto (SDT/SRT) = mejor promedio de 2 de 3 (500/1000/2000 Hz vía aérea), redondeado a múltiplo de 5. Destildar para escribir un valor manual.</p>
</div>
</div>

</div>
</div>

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
        <span><svg width="12" height="12"><line x1="1" y1="6" x2="11" y2="6" stroke="#b33a3a" stroke-width="1.6"></line></svg> OD</span>
        <span><svg width="12" height="12"><line x1="1" y1="6" x2="11" y2="6" stroke="#2255aa" stroke-width="1.6"></line></svg> OI</span>
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
            <td><input type="number" step="5" id="reflex_<?= $mode ?>_<?= $side ?>_<?= $n ?>" name="reflex_<?= $mode ?>[<?= $side ?>][<?= $n ?>]" value="<?= htmlspecialchars((string) fv($v, ['reflex_' . $mode, $side, (string) $n], 130)) ?>"></td>
            <?php endforeach; ?>
        </tr>
        <?php endforeach; ?>
    </table>
    <?php endforeach; ?>
    <table class="grid-table">
        <tr><th class="side-label">Tipo de reflejo</th><th>Curva</th></tr>
        <?php foreach (['od' => 'OD', 'oi' => 'OI'] as $side => $sideLabel):
            $reflexTypeSelected = (string) fv($v, ['reflex_type', $side], 'normal');
        ?>
        <tr>
            <td class="side-label"><?= $sideLabel ?></td>
            <td>
                <select id="reflex_type_<?= $side ?>" name="reflex_type[<?= $side ?>]">
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

<div class="tab-panel" data-tab="tinnitus">
<div class="card">
    <strong>Tinnitus (acufenometría)</strong>
    <p class="legend">Lateralidad y permanente/ocasional son independientes (un tinnitus unilateral puede ser permanente igual que uno bilateral). Unilateral pide oído; bilateral admite predominio (asimetría). Forma: tipo de ruido + frecuencia de matching.</p>
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
                <?php foreach (['od' => 'OD', 'oi' => 'OI'] as $opt => $optLabel): ?>
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
    <label>Comportamiento del paciente
        <textarea name="comportamiento" id="chat-comportamiento" rows="2" style="width:100%; padding:0.45rem; margin-top:0.2rem; border:1px solid #ccc; border-radius:4px;" placeholder="Ej: nervioso, minimiza los síntomas, muy hablador, desconfiado, colaborador..."><?= htmlspecialchars((string) ($v['comportamiento'] ?? '')) ?></textarea>
    </label>
    <p class="legend">Cómo debe actuar el paciente al conversar con el alumno (tono, actitud) -- va directo al prompt del LLM, junto con la anamnesis de arriba.</p>
    <label>Sensibilidad del paciente
        <select name="disposicion" id="chat-disposicion">
            <?php $dispOpts = [
                -2 => 'Muy quisquilloso/a (se ofende con facilidad)',
                -1 => 'Algo sensible',
                0 => 'Normal',
                1 => 'Cálido/a y agradecido/a',
                2 => 'Muy positivo/a (elogia con facilidad)',
            ]; ?>
            <?php foreach ($dispOpts as $val => $label): ?>
            <option value="<?= $val ?>" <?= ((string) ($v['disposicion'] ?? '0') === (string) $val) ? 'selected' : '' ?>><?= htmlspecialchars($label) ?></option>
            <?php endforeach; ?>
        </select>
    </label>
    <p class="legend">Qué tan fácil se ofende o se pone contento este paciente -- define el umbral del aviso OIRS (reclamo/mérito) que puede dejar al cerrar la atención.</p>
</div>

<div class="card" id="chat-test-card">
    <strong>Probar conversación con el paciente</strong>
    <p class="legend">
        Chatea con el paciente usando lo que ya escribiste en esta ficha (sin necesidad de guardar antes,
        cada mensaje toma los campos tal como están en ese momento) -- útil para revisar que responda bien
        antes de asignarlo a un alumno. Requiere tener configurado el LLM en
        <a href="llm.php" target="_blank">Admin → IA Paciente</a>. Si cambias la anamnesis a mitad de una
        conversación, reinícala para que el paciente "olvide" lo que dijo con los datos anteriores.
    </p>
    <div id="chat-test-log" style="border:1px solid #e5e5e5; border-radius:6px; padding:0.7rem; min-height:3rem; max-height:22rem; overflow-y:auto; margin:0.6rem 0; background:#fafafa; font-size:0.88rem;"></div>
    <div style="display:flex; gap:0.5rem;">
        <input type="text" id="chat-test-input" placeholder="Escribe como si fueras el alumno..." style="flex:1; padding:0.45rem; border:1px solid #ccc; border-radius:4px;">
        <button type="button" id="chat-test-send" class="secondary" style="margin-top:0;">Enviar</button>
        <button type="button" id="chat-test-reset" class="secondary" style="margin-top:0;">Reiniciar conversación</button>
    </div>
    <div style="margin-top:0.6rem; padding-top:0.6rem; border-top:1px dashed #ddd;">
        <button type="button" id="oirs-test-btn" class="secondary" style="margin-top:0;">Simular término de sesión (ver veredicto OIRS)</button>
        <p class="legend">Corre el evaluador de <a href="llm.php" target="_blank">Admin → IA Paciente</a> sobre esta conversación de prueba, tal como se ejecutaría al cerrar una atención real -- útil para ajustar el prompt del evaluador o la sensibilidad del paciente.</p>
        <div id="oirs-test-result"></div>
    </div>
</div>
</div>

<div class="card">
    <?php if ($isEdit): ?>
    <button type="submit" name="form_action" value="update_case">Guardar cambios</button>
    <?php else: ?>
    <button type="submit" name="form_action" value="create_case">Crear caso</button>
    <?php endif; ?>
    <a href="agenda.php" style="margin-left:1rem; font-size:0.85rem;">Cancelar</a>
</div>
</form>

<?php if ($isEdit): ?>
<div id="photo-crop-modal" class="photo-modal" hidden>
    <div class="photo-modal-box">
        <strong style="display:block; margin-bottom:0.6rem;">Recortar foto</strong>
        <div class="photo-crop-viewport" id="photo-crop-viewport">
            <img id="photo-crop-img" alt="">
            <div class="photo-crop-ring"></div>
        </div>
        <input type="range" id="photo-crop-zoom" min="1" max="4" step="0.01" value="1" style="width:100%; margin-top:0.8rem;">
        <p class="legend" style="text-align:center;">Arrastra para mover, usa el control para acercar/alejar.</p>
        <div class="photo-modal-actions">
            <button type="button" id="photo-crop-cancel" class="secondary">Cancelar</button>
            <button type="button" id="photo-crop-confirm">Guardar foto</button>
        </div>
    </div>
</div>
<script>
// Foto de paciente: elegir archivo -> modal de recorte circular (pan/zoom
// con mouse o touch) -> fetch con FormData a patient_photo_upload.php. El
// crop se manda como rectángulo (crop_x/y/size) en píxeles de la imagen
// ORIGINAL -- PatientPhoto::save() hace el recorte real server-side con GD,
// acá solo se calcula el rectángulo a partir del pan/zoom en pantalla.
(function () {
    var fileInput = document.getElementById('patient-photo-input');
    var modal = document.getElementById('photo-crop-modal');
    var viewport = document.getElementById('photo-crop-viewport');
    var img = document.getElementById('photo-crop-img');
    var zoomSlider = document.getElementById('photo-crop-zoom');
    var cancelBtn = document.getElementById('photo-crop-cancel');
    var confirmBtn = document.getElementById('photo-crop-confirm');
    var avatarPreview = document.getElementById('patient-avatar-preview');
    var avatarEmpty = document.getElementById('patient-avatar-empty');
    var msgEl = document.getElementById('photo-msg');
    if (!fileInput || !modal) { return; }

    var CASE_ID = <?= json_encode($editId) ?>;
    var VIEWPORT = 280;
    var naturalW = 0, naturalH = 0, coverScale = 1, scale = 1;
    var tx = 0, ty = 0;
    var dragging = false, dragStartX = 0, dragStartY = 0, dragOrigTx = 0, dragOrigTy = 0;
    var selectedFile = null;

    function clampPan() {
        var dispW = naturalW * scale;
        var dispH = naturalH * scale;
        var minTx = Math.min(0, VIEWPORT - dispW);
        var minTy = Math.min(0, VIEWPORT - dispH);
        tx = Math.max(minTx, Math.min(0, tx));
        ty = Math.max(minTy, Math.min(0, ty));
    }

    function applyTransform() {
        img.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')';
    }

    function openModal(file) {
        selectedFile = file;
        img.onload = function () {
            naturalW = img.naturalWidth;
            naturalH = img.naturalHeight;
            coverScale = Math.max(VIEWPORT / naturalW, VIEWPORT / naturalH);
            scale = coverScale;
            tx = (VIEWPORT - naturalW * scale) / 2;
            ty = (VIEWPORT - naturalH * scale) / 2;
            zoomSlider.value = '1';
            applyTransform();
            modal.hidden = false;
        };
        img.src = URL.createObjectURL(file);
    }

    function closeModal() {
        modal.hidden = true;
        fileInput.value = '';
        selectedFile = null;
    }

    function showMsg(text, isError) {
        msgEl.textContent = text;
        msgEl.style.color = isError ? '#a33' : '#2a7a2a';
        msgEl.hidden = false;
    }

    fileInput.addEventListener('change', function () {
        if (fileInput.files && fileInput.files[0]) {
            openModal(fileInput.files[0]);
        }
    });

    cancelBtn.addEventListener('click', closeModal);

    zoomSlider.addEventListener('input', function () {
        var z = parseFloat(zoomSlider.value);
        // Ancla el zoom al centro del viewport, no a la esquina.
        var cx = VIEWPORT / 2, cy = VIEWPORT / 2;
        var imgCx = (cx - tx) / scale;
        var imgCy = (cy - ty) / scale;
        scale = coverScale * z;
        tx = cx - imgCx * scale;
        ty = cy - imgCy * scale;
        clampPan();
        applyTransform();
    });

    function pointerDown(x, y) {
        dragging = true;
        dragStartX = x; dragStartY = y;
        dragOrigTx = tx; dragOrigTy = ty;
    }
    function pointerMove(x, y) {
        if (!dragging) { return; }
        tx = dragOrigTx + (x - dragStartX);
        ty = dragOrigTy + (y - dragStartY);
        clampPan();
        applyTransform();
    }
    function pointerUp() { dragging = false; }

    viewport.addEventListener('mousedown', function (e) { pointerDown(e.clientX, e.clientY); });
    window.addEventListener('mousemove', function (e) { pointerMove(e.clientX, e.clientY); });
    window.addEventListener('mouseup', pointerUp);
    viewport.addEventListener('touchstart', function (e) {
        pointerDown(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });
    viewport.addEventListener('touchmove', function (e) {
        pointerMove(e.touches[0].clientX, e.touches[0].clientY);
        e.preventDefault();
    }, { passive: false });
    viewport.addEventListener('touchend', pointerUp);

    confirmBtn.addEventListener('click', function () {
        if (!selectedFile) { return; }
        // Recuadro visible en pantalla = el viewport completo (0,0)-(V,V);
        // se convierte a coordenadas de píxel de la imagen ORIGINAL.
        var srcSize = VIEWPORT / scale;
        var srcX = -tx / scale;
        var srcY = -ty / scale;

        confirmBtn.disabled = true;
        confirmBtn.textContent = 'Guardando...';

        var fd = new FormData();
        fd.append('csrf_token', document.querySelector('input[name="csrf_token"]').value);
        fd.append('case_id', CASE_ID);
        fd.append('crop_x', Math.round(srcX));
        fd.append('crop_y', Math.round(srcY));
        fd.append('crop_size', Math.round(srcSize));
        fd.append('photo', selectedFile);

        fetch('patient_photo_upload.php', { method: 'POST', body: fd })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Guardar foto';
                if (data.ok) {
                    avatarPreview.src = 'patient_photo.php?case_id=' + encodeURIComponent(CASE_ID) + '&type=avatar&v=' + Date.now();
                    avatarPreview.hidden = false;
                    avatarEmpty.hidden = true;
                    showMsg('Foto actualizada.', false);
                    closeModal();
                } else {
                    showMsg(data.error || 'No se pudo guardar la foto.', true);
                }
            })
            .catch(function () {
                confirmBtn.disabled = false;
                confirmBtn.textContent = 'Guardar foto';
                showMsg('Error de red al subir la foto.', true);
            });
    });
})();
</script>
<?php endif; ?>

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

// Tinnitus: oído solo aplica si es unilateral, predominio solo si es
// bilateral -- sin JS quedan ambos campos visibles (degradan con gracia,
// el backend ya ignora el que no corresponda según la lateralidad elegida).
(function () {
    var select = document.getElementById('tinnitus-lateralidad');
    if (!select) return;
    var fields = document.querySelectorAll('[data-show-for]');

    function update() {
        fields.forEach(function (field) {
            field.style.display = field.dataset.showFor === select.value ? '' : 'none';
        });
    }

    select.addEventListener('change', update);
    update();
})();

// Audiograma: se redibuja solo con lo que hay en los campos de vía
// aérea/ósea/LDL -- mismas coordenadas (log de frecuencia, -10..120 dB HL)
// que audiogram_x()/audiogram_y() en PHP, que dibujan la grilla fija de
// fondo. Símbolos clínicos estándar (ASHA): círculo/cruz = aérea OD/OI sin
// enmascarar, triángulo/cuadrado = aérea OD/OI enmascarada; "<"/">" = ósea
// OD/OI sin enmascarar, "["/"]" = ósea OD/OI enmascarada; triángulo relleno
// = LDL. El enmascaramiento no se tipea a mano: se infiere solo de la
// atenuación interaural (ver reglas en airMasked/boneMasked abajo), mismo
// criterio que enseña Katz, Handbook of Clinical Audiology (ver también
// CaseBuilder::earVolume, que cita la misma fuente).
window.drawAudiogram = (function () {
    var NS = 'http://www.w3.org/2000/svg';
    var MIN_LOG = Math.log(125) / Math.LN2;
    var MAX_LOG = Math.log(8000) / Math.LN2;
    var FREQS = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000];
    // Reglas de enmascaramiento (simplificadas, uso docente): aérea se
    // enmascara si el umbral propio supera al óseo del oído contralateral
    // en >= la atenuación interaural de ESA frecuencia (misma tabla que
    // ResponseAudiometry.attenuations en src/audiometria/response.py de la
    // app de escritorio -- ahí simula qué tan bien el auricular aísla al
    // oído contrario). Ósea se enmascara si hay gap aéreo-óseo del MISMO
    // oído >= 10 dB (la atenuación interaural ósea es prácticamente 0).
    var AIR_ATTENUATION_BY_FREQ = [35, 40, 40, 40, 40, 45, 45, 50, 50];
    var BONE_MASKING_GAP = 10;

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
    function isLdlMeasured(side) {
        var t = document.querySelector('.ldl-toggle[data-side="' + side + '"]');
        return !t || t.checked;
    }
    function airMasked(acSelf, bcOther, freqIndex) { return (acSelf - bcOther) >= AIR_ATTENUATION_BY_FREQ[freqIndex]; }
    function boneMasked(acSelf, bcSelf) { return (acSelf - bcSelf) >= BONE_MASKING_GAP; }

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
    function makeTriangle(x, y, color) {
        var r = 5;
        var t = document.createElementNS(NS, 'polygon');
        t.setAttribute('points', x + ',' + (y - r) + ' ' + (x - r) + ',' + (y + r * 0.8) + ' ' + (x + r) + ',' + (y + r * 0.8));
        t.setAttribute('fill', 'none'); t.setAttribute('stroke', color); t.setAttribute('stroke-width', '1.5');
        return t;
    }
    function makeSquare(x, y, color) {
        var r = 4;
        var rect = document.createElementNS(NS, 'rect');
        rect.setAttribute('x', x - r); rect.setAttribute('y', y - r);
        rect.setAttribute('width', 2 * r); rect.setAttribute('height', 2 * r);
        rect.setAttribute('fill', 'none'); rect.setAttribute('stroke', color); rect.setAttribute('stroke-width', '1.5');
        return rect;
    }
    /** "<"/">" sin enmascarar, "["/"]" enmascarado -- mismo trazo, distinto cierre del ángulo. */
    function makeBracket(x, y, color, dir, masked) {
        var r = 4.5;
        var pts;
        if (!masked) {
            pts = dir === 'left'
                ? (x + r) + ',' + (y - r) + ' ' + (x - r) + ',' + y + ' ' + (x + r) + ',' + (y + r)
                : (x - r) + ',' + (y - r) + ' ' + (x + r) + ',' + y + ' ' + (x - r) + ',' + (y + r);
        } else {
            pts = dir === 'left'
                ? (x + r * 0.6) + ',' + (y - r) + ' ' + (x - r) + ',' + (y - r) + ' ' + (x - r) + ',' + (y + r) + ' ' + (x + r * 0.6) + ',' + (y + r)
                : (x - r * 0.6) + ',' + (y - r) + ' ' + (x + r) + ',' + (y - r) + ' ' + (x + r) + ',' + (y + r) + ' ' + (x - r * 0.6) + ',' + (y + r);
        }
        var p = document.createElementNS(NS, 'polyline');
        p.setAttribute('points', pts);
        p.setAttribute('fill', 'none'); p.setAttribute('stroke', color); p.setAttribute('stroke-width', '1.5');
        return p;
    }
    function makeLdlMark(x, y, color) {
        var r = 4;
        var t = document.createElementNS(NS, 'polygon');
        t.setAttribute('points', (x - r) + ',' + (y - r * 0.6) + ' ' + (x + r) + ',' + (y - r * 0.6) + ' ' + x + ',' + (y + r * 0.7));
        t.setAttribute('fill', color); t.setAttribute('stroke', 'none');
        return t;
    }

    return function drawAudiogram() {
        var group = document.getElementById('audiogram-data');
        if (!group) return;
        while (group.firstChild) group.removeChild(group.firstChild);

        function drawLine(vals, color, dashed) {
            var poly = document.createElementNS(NS, 'polyline');
            poly.setAttribute('points', vals.map(function (v, i) { return xPos(FREQS[i]) + ',' + yPos(v); }).join(' '));
            poly.setAttribute('fill', 'none');
            poly.setAttribute('stroke', color);
            poly.setAttribute('stroke-width', dashed ? '1' : '1.3');
            if (dashed) poly.setAttribute('stroke-dasharray', '2,2');
            group.appendChild(poly);
        }

        var aereaOd = readVals('aerea', 'od'), aereaOi = readVals('aerea', 'oi');
        var oseaOd = readVals('osea', 'od'), oseaOi = readVals('osea', 'oi');

        // Vía aérea: línea + símbolo por punto (enmascarado si el umbral
        // propio supera al óseo del oído contrario en >= la atenuación
        // interaural de esa frecuencia, ver AIR_ATTENUATION_BY_FREQ).
        drawLine(aereaOd, '#b33a3a');
        drawLine(aereaOi, '#2255aa');
        for (var n = 0; n < FREQS.length; n++) {
            var x = xPos(FREQS[n]);
            var maskedOd = airMasked(aereaOd[n], oseaOi[n], n);
            group.appendChild((maskedOd ? makeTriangle : makeCircle)(x, yPos(aereaOd[n]), '#b33a3a'));
            var maskedOi = airMasked(aereaOi[n], oseaOd[n], n);
            group.appendChild((maskedOi ? makeSquare : makeCross)(x, yPos(aereaOi[n]), '#2255aa'));
        }

        // Vía ósea: sin línea (convención estándar), enmascarada si hay gap
        // aéreo-óseo >=10dB en el mismo oído.
        for (var m = 0; m < FREQS.length; m++) {
            var x2 = xPos(FREQS[m]);
            group.appendChild(makeBracket(x2, yPos(oseaOd[m]), '#b33a3a', 'left', boneMasked(aereaOd[m], oseaOd[m])));
            group.appendChild(makeBracket(x2, yPos(oseaOi[m]), '#2255aa', 'right', boneMasked(aereaOi[m], oseaOi[m])));
        }

        // LDL: solo si "LDL medido" está activo para ese oído -- si no, el
        // valor que se guarda es 130 (ausente) sin importar lo escrito, así
        // que graficarlo igual sería mostrar un dato que nunca se va a guardar.
        if (isLdlMeasured('od')) {
            var ldlOd = readVals('ldl', 'od');
            drawLine(ldlOd, '#b33a3a', true);
            ldlOd.forEach(function (v, i) { group.appendChild(makeLdlMark(xPos(FREQS[i]), yPos(v), '#b33a3a')); });
        }
        if (isLdlMeasured('oi')) {
            var ldlOi = readVals('ldl', 'oi');
            drawLine(ldlOi, '#2255aa', true);
            ldlOi.forEach(function (v, i) { group.appendChild(makeLdlMark(xPos(FREQS[i]), yPos(v), '#2255aa')); });
        }
    };
})();

// Logoaudiograma: curva % discriminación vs intensidad (dB HL), por oído.
// Mismo plot box que el audiograma pero ejes lineales (ver logogram_x()/
// logogram_y() en PHP arriba). Curva simplificada para vista previa en vivo
// -- no replica CalculateLogo.cal_new_umd completo (src/audiometria/
// logoaudiometry.py de la app de escritorio), pero sigue la misma forma:
// 0% en SDT, sube hasta UMD(int,%), y desde ahí meseta plana o cae si hay
// reclutamiento (rollover). SRT se marca aparte como línea vertical, ya que
// es un umbral de detección, no un punto de la curva de discriminación.
window.drawLogogram = (function () {
    var NS = 'http://www.w3.org/2000/svg';
    function logoX(db) { db = Math.max(-10, Math.min(120, db)); return 32 + (db - (-10)) / 130 * 280; }
    function logoY(pct) { pct = Math.max(0, Math.min(100, pct)); return 10 + (100 - pct) / 100 * 266; }

    function val(selector, side, def) {
        var el = document.querySelector(selector + '[data-side="' + side + '"]');
        return el ? (parseInt(el.value, 10) || 0) : def;
    }

    function makeDot(x, y, color) {
        var c = document.createElementNS(NS, 'circle');
        c.setAttribute('cx', x); c.setAttribute('cy', y); c.setAttribute('r', 3);
        c.setAttribute('fill', color); c.setAttribute('stroke', 'none');
        return c;
    }
    function makeUmdMark(x, y, color) {
        var r = 4;
        var t = document.createElementNS(NS, 'polygon');
        t.setAttribute('points', x + ',' + (y - r) + ' ' + (x - r) + ',' + (y + r * 0.8) + ' ' + (x + r) + ',' + (y + r * 0.8));
        t.setAttribute('fill', color); t.setAttribute('stroke', 'none');
        return t;
    }
    function makeSrtLine(x, color) {
        var l = document.createElementNS(NS, 'line');
        l.setAttribute('x1', x); l.setAttribute('y1', 10); l.setAttribute('x2', x); l.setAttribute('y2', 276);
        l.setAttribute('stroke', color); l.setAttribute('stroke-width', '1'); l.setAttribute('stroke-dasharray', '2,2');
        return l;
    }

    function curvePoints(side) {
        var sdt = val('.sdt-input', side, 0);
        var umdInt = val('.umd-int-input', side, 35);
        var umdPct = val('.umd-pct-input', side, 100);
        var recruitEl = document.querySelector('.recruit-toggle[data-side="' + side + '"]');
        var recruit = !!(recruitEl && recruitEl.checked);

        var pts = [[-10, 0], [sdt, 0], [umdInt, umdPct]];
        pts.push(recruit ? [120, Math.max(0, umdPct - (120 - umdInt) / 5 * 5)] : [120, umdPct]);
        // Ordenado por dB creciente -- si SDT/UMD quedan invertidos (dato mal
        // tipeado) igual se dibuja algo coherente en vez de una polyline en zigzag.
        pts.sort(function (a, b) { return a[0] - b[0]; });
        return pts;
    }

    return function drawLogogram() {
        var group = document.getElementById('logogram-data');
        if (!group) return;
        while (group.firstChild) group.removeChild(group.firstChild);

        ['od', 'oi'].forEach(function (side) {
            var color = side === 'od' ? '#b33a3a' : '#2255aa';
            var pts = curvePoints(side);
            var poly = document.createElementNS(NS, 'polyline');
            poly.setAttribute('points', pts.map(function (p) { return logoX(p[0]) + ',' + logoY(p[1]); }).join(' '));
            poly.setAttribute('fill', 'none');
            poly.setAttribute('stroke', color);
            poly.setAttribute('stroke-width', '1.3');
            group.appendChild(poly);

            var sdt = val('.sdt-input', side, 0);
            var srt = val('.srt-input', side, 0);
            var umdInt = val('.umd-int-input', side, 35);
            var umdPct = val('.umd-pct-input', side, 100);
            group.appendChild(makeSrtLine(logoX(srt), color));
            group.appendChild(makeDot(logoX(sdt), logoY(0), color));
            group.appendChild(makeUmdMark(logoX(umdInt), logoY(umdPct), color));
        });
    };
})();

// Timpanograma: curva estilizada según el tipo Jerger elegido en Z OD/Z OI
// -- el form solo guarda la categoría (A/As/Ad/C/Cs/B), no una curva medida,
// así que se sintetiza una campana gaussiana por tipo. Mismas coordenadas
// (presión -400..200 daPa, compliance 0..2.5 mL) que tymp_x()/tymp_y() en
// PHP arriba, que dibujan la grilla fija de fondo.
window.drawTympanogram = (function () {
    var NS = 'http://www.w3.org/2000/svg';
    function xPos(p) { p = Math.max(-400, Math.min(200, p)); return 32 + (p - (-400)) / 600 * 280; }
    function yPos(c) { c = Math.max(0, Math.min(2.5, c)); return 276 - c / 2.5 * 266; }

    // [posición del pico (daPa), altura del pico (mL), ancho de la campana, línea base]
    var SHAPES = {
        A: [0, 0.8, 60, 0.1],
        As: [0, 0.3, 50, 0.1],
        Ad: [0, 1.8, 70, 0.1],
        C: [-150, 0.8, 70, 0.1],
        Cs: [-150, 0.3, 60, 0.1],
        B: [0, 0.15, 400, 0.15]
    };

    function curvePoints(type) {
        var s = SHAPES[type] || SHAPES.A;
        var peakPos = s[0], peakHeight = s[1], width = s[2], baseline = s[3];
        var pts = [];
        for (var p = -400; p <= 200; p += 10) {
            var c = baseline + (peakHeight - baseline) * Math.exp(-((p - peakPos) * (p - peakPos)) / (2 * width * width));
            pts.push([p, c]);
        }
        return pts;
    }

    return function drawTympanogram() {
        var group = document.getElementById('tympanogram-data');
        if (!group) return;
        while (group.firstChild) group.removeChild(group.firstChild);

        [['z_od', '#b33a3a'], ['z_oi', '#2255aa']].forEach(function (pair) {
            var el = document.getElementById(pair[0]);
            var pts = curvePoints(el ? el.value : 'A');
            var poly = document.createElementNS(NS, 'polyline');
            poly.setAttribute('points', pts.map(function (pt) { return xPos(pt[0]) + ',' + yPos(pt[1]); }).join(' '));
            poly.setAttribute('fill', 'none');
            poly.setAttribute('stroke', pair[1]);
            poly.setAttribute('stroke-width', '1.5');
            group.appendChild(poly);
        });
    };
})();

// Patrón de reflejos: tabla espejada (ipsi al centro, contra afuera), una
// celda +/- por frecuencia/modo/oído, leída en vivo de los campos
// reflex_ipsi/reflex_contra -- presente (valor != 130) rellena con gris
// oscuro fijo; el color del "+" marca el oído que recibió el estímulo: en
// ipsi coincide con la columna (OD=rojo, OI=azul), en contra es el
// cruzado (columna OD con estímulo en OI=azul, columna OI con estímulo en
// OD=rojo). Ausente (130) queda vacía.
window.drawReflexPattern = function drawReflexPattern() {
    document.querySelectorAll('.reflex-cell[data-mode]').forEach(function (cell) {
        var mode = cell.dataset.mode, side = cell.dataset.side, n = cell.dataset.n;
        var el = document.getElementById('reflex_' + mode + '_' + side + '_' + n);
        var val = el ? (parseInt(el.value, 10) || 0) : 130;
        var present = val < 130;
        var stimulusSide = mode === 'ipsi' ? side : (side === 'od' ? 'oi' : 'od');
        cell.textContent = present ? '+' : String.fromCharCode(8722);
        cell.classList.toggle('present', present);
        cell.classList.toggle('mark-od', present && stimulusSide === 'od');
        cell.classList.toggle('mark-oi', present && stimulusSide === 'oi');
    });
};

(function () {
    var form = document.getElementById('case-form');
    if (!form) return;
    // Delegado: cubre tipeo directo en vía aérea/ósea/LDL. El caso de
    // "igualar" (que escribe osea.value por JS sin evento input) se cubre
    // aparte, llamando drawAudiogram() desde syncOsea() más abajo.
    form.addEventListener('input', function (e) {
        if (e.target.id && /^(aerea|osea|ldl)_/.test(e.target.id)) window.drawAudiogram();
        if (e.target.classList && (e.target.classList.contains('sdt-input') || e.target.classList.contains('srt-input')
            || e.target.classList.contains('umd-int-input') || e.target.classList.contains('umd-pct-input'))) window.drawLogogram();
        if (e.target.id && /^reflex_/.test(e.target.id)) window.drawReflexPattern();
    });
    // El toggle "LDL medido" decide si esa serie se grafica o no, no solo
    // un valor -- necesita su propio listener aparte del 'input' de arriba.
    form.addEventListener('change', function (e) {
        if (e.target.classList && e.target.classList.contains('ldl-toggle')) window.drawAudiogram();
        if (e.target.classList && e.target.classList.contains('recruit-toggle')) window.drawLogogram();
        if (e.target.id === 'z_od' || e.target.id === 'z_oi') window.drawTympanogram();
    });
    window.drawAudiogram();
    window.drawLogogram();
    window.drawTympanogram();
    window.drawReflexPattern();
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
                if (window.drawLogogram) window.drawLogogram();
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

// Acumetría (Rinne/Weber) auto -- espejo en JS de CaseBuilder::rinneAuto()/
// weberAuto() (PHP recalcula igual al enviar; esto es solo para que el
// docente vea el resultado en vivo mientras tipea los umbrales tonales).
(function () {
    var RINNE_GAP = <?= CaseBuilder::RINNE_GAP_THRESHOLD ?>;
    var WEBER_ASYM = <?= CaseBuilder::WEBER_ASYMMETRY_THRESHOLD ?>;
    var FREQ_IDX = [<?= implode(',', CaseBuilder::ACUMETRIA_FREQS) ?>];

    function threshold(kind, side, n) {
        var el = document.getElementById(kind + '_' + side + '_' + n);
        return el ? (parseInt(el.value, 10) || 0) : 0;
    }
    function rinneAuto(air, bone) {
        return (air - bone) >= RINNE_GAP ? 'negativo' : 'positivo';
    }
    function weberAuto(boneOd, boneOi) {
        if (Math.abs(boneOd - boneOi) < WEBER_ASYM) return 'centrado';
        return boneOd < boneOi ? 'od' : 'oi';
    }

    function syncAll() {
        FREQ_IDX.forEach(function (n) {
            ['od', 'oi'].forEach(function (side) {
                var auto = document.querySelector('.rinne-auto-toggle[data-freq="' + n + '"][data-side="' + side + '"]');
                var select = document.getElementById('rinne_' + n + '_' + side);
                if (!auto || !select) return;
                if (auto.checked) {
                    select.value = rinneAuto(threshold('aerea', side, n), threshold('osea', side, n));
                    select.disabled = true;
                } else {
                    select.disabled = false;
                }
            });
            var weberAutoEl = document.querySelector('.weber-auto-toggle[data-freq="' + n + '"]');
            var weberSelect = document.getElementById('weber_' + n);
            if (!weberAutoEl || !weberSelect) return;
            if (weberAutoEl.checked) {
                weberSelect.value = weberAuto(threshold('osea', 'od', n), threshold('osea', 'oi', n));
                weberSelect.disabled = true;
            } else {
                weberSelect.disabled = false;
            }
        });
    }

    document.querySelectorAll('.rinne-auto-toggle, .weber-auto-toggle').forEach(function (el) {
        el.addEventListener('change', syncAll);
    });
    FREQ_IDX.forEach(function (n) {
        ['od', 'oi'].forEach(function (side) {
            var a = document.getElementById('aerea_' + side + '_' + n);
            var o = document.getElementById('osea_' + side + '_' + n);
            if (a) a.addEventListener('input', syncAll);
            if (o) o.addEventListener('input', syncAll);
        });
    });
    syncAll();
})();

// Filas de Fowler/I.W.A. por frecuencia -- espejo en JS de
// CaseBuilder::fowlerQualifyingFreqs()/fowlerValidationError() (PHP recalcula
// todo igual al enviar, esto es solo para que el docente vea en vivo en
// cuáles frecuencias calificó cada vez que cambia un umbral, y pueda elegir
// el patrón de reclutamiento en cada una sin perder lo ya elegido).
(function () {
    var table = document.getElementById('fowler-table');
    var container = document.getElementById('fowler-rows');
    var noneMsg = document.getElementById('fowler-none-msg');
    if (!table || !container) return;

    var NORMAL_HL = 20, GAP_MAX = 10, DIFF_MIN = 20, DIFF_MAX = 40;
    var FREQ_HZ = { 1: 250, 2: 500, 3: 1000, 4: 2000, 5: 3000, 6: 4000 }; // mismos índices que CaseBuilder::FREQUENCIES
    var FREQ_INDEXES = Object.keys(FREQ_HZ).map(Number);
    var PATTERNS = [
        ['none', 'Sin reclutamiento'],
        ['partial', 'Reclutamiento parcial'],
        ['complete', 'Reclutamiento completo'],
        ['over', 'Sobre-reclutamiento']
    ];
    var DEFAULT_PATTERN = 'none';

    function val(id) {
        var el = document.getElementById(id);
        return el ? (parseInt(el.value, 10) || 0) : 0;
    }

    function qualifyingFreqs() {
        var out = [];
        FREQ_INDEXES.forEach(function (i) {
            var od = val('aerea_od_' + i), oi = val('aerea_oi_' + i);
            var refSide = od <= oi ? 'od' : 'oi';
            var studySide = refSide === 'od' ? 'oi' : 'od';
            var refTh = refSide === 'od' ? od : oi;
            var studyTh = studySide === 'od' ? od : oi;
            var diff = studyTh - refTh;
            if (refTh > NORMAL_HL || studyTh <= NORMAL_HL || diff < DIFF_MIN || diff > DIFF_MAX) return;
            var boneStudy = val('osea_' + studySide + '_' + i);
            if (studyTh - boneStudy > GAP_MAX) return;
            out.push({ idx: i, diff: diff });
        });
        return out;
    }

    function rebuild() {
        // Preserva lo ya elegido en cada fila antes de reconstruir -- si
        // cambiar un umbral en OTRA frecuencia no debería resetear esta.
        var current = {};
        container.querySelectorAll('select[data-freq]').forEach(function (sel) {
            current[sel.dataset.freq] = sel.value;
        });

        var qualifying = qualifyingFreqs();
        container.innerHTML = '';

        qualifying.forEach(function (q) {
            var tr = document.createElement('tr');
            tr.dataset.freq = String(q.idx);

            var tdFreq = document.createElement('td');
            tdFreq.textContent = FREQ_HZ[q.idx] + ' Hz';
            tr.appendChild(tdFreq);

            var tdDiff = document.createElement('td');
            tdDiff.textContent = q.diff + ' dB';
            tr.appendChild(tdDiff);

            var tdSelect = document.createElement('td');
            var select = document.createElement('select');
            select.name = 'fowler_pattern[' + q.idx + ']';
            select.dataset.freq = String(q.idx);
            PATTERNS.forEach(function (p) {
                var opt = document.createElement('option');
                opt.value = p[0];
                opt.textContent = p[1];
                select.appendChild(opt);
            });
            select.value = current[q.idx] || DEFAULT_PATTERN;
            tdSelect.appendChild(select);
            tr.appendChild(tdSelect);

            container.appendChild(tr);
        });

        table.hidden = qualifying.length === 0;
        if (noneMsg) { noneMsg.hidden = qualifying.length > 0; }
    }

    FREQ_INDEXES.forEach(function (i) {
        ['aerea_od_', 'aerea_oi_', 'osea_od_', 'osea_oi_'].forEach(function (prefix) {
            var el = document.getElementById(prefix + i);
            if (el) el.addEventListener('input', rebuild);
        });
    });
    // "Igualar ósea a aérea" copia los valores por JS (sin disparar 'input'
    // en los campos de ósea) -- sin este listener aparte, activar el toggle
    // no actualizaba qué frecuencias calificaban hasta que se volvía a
    // tipear algo. Corre después del listener que hace la copia (registrado
    // antes en el archivo), así que ya lee los valores de ósea al día.
    document.querySelectorAll('.igualar-toggle').forEach(function (el) {
        el.addEventListener('change', rebuild);
    });
    rebuild();
})();

// Chat de prueba con el paciente (ficha Anamnesis) -- manda a
// llm_chat_test.php lo que hay AHORA MISMO en el formulario (sin guardar),
// mismo criterio con el que LlmConfig::buildSystemPrompt() arma el prompt
// real más adelante en la app. HIST_KEYS espejea CaseBuilder::HIST_CHECKBOXES.
(function () {
    var sendBtn = document.getElementById('chat-test-send');
    var resetBtn = document.getElementById('chat-test-reset');
    var input = document.getElementById('chat-test-input');
    var log = document.getElementById('chat-test-log');
    if (!sendBtn || !input || !log) return;

    var HIST_KEYS = ['hipoacusia_familiar', 'ototoxicos', 'trauma_acustico', 'otitis', 'meningitis', 'tce', 'diabetes', 'hta'];
    var history = [];
    var sending = false;

    function fieldValue(name) {
        var el = document.querySelector('[name="' + name + '"]');
        return el ? el.value : '';
    }

    function currentName() {
        var n1 = document.querySelector('[name="nombre1"]');
        if (n1) {
            var parts = [n1.value, fieldValue('nombre2'), fieldValue('apellido1'), fieldValue('apellido2')].filter(function (p) { return p; });
            if (parts.length) return parts.join(' ');
        }
        var staticName = document.getElementById('chat-static-name');
        return (staticName && staticName.value) || 'el paciente';
    }

    function currentAntecedentes() {
        var out = {};
        HIST_KEYS.forEach(function (key) {
            var el = document.querySelector('[name="hist[' + key + ']"]');
            out[key] = !!(el && el.checked);
        });
        return out;
    }

    function currentTinnitus() {
        return {
            lateralidad: fieldValue('tinnitus[lateralidad]'),
            oido: fieldValue('tinnitus[oido]'),
            predominio: fieldValue('tinnitus[predominio]'),
            ruido: fieldValue('tinnitus[ruido]'),
            frecuencia: fieldValue('tinnitus[frecuencia]'),
            pulsatil: !!document.querySelector('[name="tinnitus[pulsatil]"]:checked'),
            permanente: !!document.querySelector('[name="tinnitus[permanente]"]:checked'),
        };
    }

    function addBubble(role, text) {
        var wrap = document.createElement('div');
        wrap.style.margin = '0.4rem 0';
        var tag = document.createElement('strong');
        tag.textContent = role === 'user' ? 'Alumno: ' : (role === 'error' ? 'Error: ' : 'Paciente: ');
        tag.style.color = role === 'user' ? '#1a2744' : (role === 'error' ? '#a33' : '#2e7d32');
        var body = document.createElement('span');
        body.textContent = text;
        wrap.appendChild(tag);
        wrap.appendChild(body);
        log.appendChild(wrap);
        log.scrollTop = log.scrollHeight;
    }

    function send() {
        var message = input.value.trim();
        if (!message || sending) return;
        sending = true;
        sendBtn.disabled = true;
        addBubble('user', message);
        input.value = '';

        var payload = {
            csrf_token: document.querySelector('input[name="csrf_token"]').value,
            message: message,
            history: history,
            nombre: currentName(),
            edad: fieldValue('age'),
            genero: (document.querySelector('input[name="gender"]:checked') || {}).value || '0',
            antecedentes: currentAntecedentes(),
            medicamentos: fieldValue('medicamentos'),
            cirugias: fieldValue('cirugias'),
            otros: fieldValue('otros'),
            comportamiento: fieldValue('comportamiento'),
            disposicion: fieldValue('disposicion'),
            tinnitus: currentTinnitus(),
        };

        fetch('llm_chat_test.php', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        }).then(function (res) {
            return res.json().then(function (data) { return { ok: res.ok, data: data }; });
        }).then(function (result) {
            if (!result.ok || result.data.error) {
                addBubble('error', result.data.error || 'Error desconocido.');
                return;
            }
            history.push({ role: 'user', content: message });
            history.push({ role: 'assistant', content: result.data.reply });
            addBubble('assistant', result.data.reply);
        }).catch(function (err) {
            addBubble('error', 'No se pudo contactar al servidor: ' + err.message);
        }).finally(function () {
            sending = false;
            sendBtn.disabled = false;
            input.focus();
        });
    }

    sendBtn.addEventListener('click', send);
    input.addEventListener('keydown', function (e) {
        if (e.key === 'Enter') { e.preventDefault(); send(); }
    });
    if (resetBtn) {
        resetBtn.addEventListener('click', function () {
            history = [];
            log.innerHTML = '';
            input.focus();
            var result = document.getElementById('oirs-test-result');
            if (result) result.innerHTML = '';
        });
    }

    var oirsBtn = document.getElementById('oirs-test-btn');
    var oirsResult = document.getElementById('oirs-test-result');
    if (oirsBtn && oirsResult) {
        var VEREDICTO_LABELS = {
            reclamo: { text: 'Reclamo', color: '#a33', bg: '#fbeaea' },
            merito: { text: 'Mérito', color: '#2e7d32', bg: '#eaf6ea' },
            neutro: { text: 'Neutro (sin aviso)', color: '#666', bg: '#f0f0f0' },
        };

        oirsBtn.addEventListener('click', function () {
            oirsBtn.disabled = true;
            oirsResult.innerHTML = '<p class="legend">Evaluando…</p>';

            fetch('oirs_test.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    csrf_token: document.querySelector('input[name="csrf_token"]').value,
                    history: history,
                    disposicion: fieldValue('disposicion'),
                }),
            }).then(function (res) {
                return res.json().then(function (data) { return { ok: res.ok, data: data }; });
            }).then(function (result) {
                if (!result.ok || result.data.error) {
                    oirsResult.innerHTML = '';
                    var err = document.createElement('p');
                    err.style.color = '#a33';
                    err.textContent = result.data.error || 'Error desconocido.';
                    oirsResult.appendChild(err);
                    return;
                }
                var v = result.data;
                var style = VEREDICTO_LABELS[v.veredicto] || VEREDICTO_LABELS.neutro;
                oirsResult.innerHTML = '';

                var badge = document.createElement('span');
                badge.textContent = style.text;
                badge.style.cssText = 'display:inline-block; padding:0.15rem 0.6rem; border-radius:12px; font-weight:600; font-size:0.8rem; color:' + style.color + '; background:' + style.bg + ';';
                oirsResult.appendChild(badge);

                if (v.veredicto !== 'neutro') {
                    var mail = document.createElement('div');
                    mail.style.cssText = 'margin-top:0.5rem; padding:0.7rem; border:1px solid #e5e5e5; border-radius:6px; background:#fafafa; font-size:0.88rem;';
                    var from = document.createElement('div');
                    from.style.color = '#888';
                    from.textContent = 'De: Oficina de Informaciones, Reclamos y Sugerencias (OIRS)';
                    var subject = document.createElement('div');
                    subject.style.cssText = 'font-weight:600; margin-top:0.2rem;';
                    subject.textContent = 'Asunto: ' + v.asunto;
                    var body = document.createElement('div');
                    body.style.marginTop = '0.5rem';
                    body.style.whiteSpace = 'pre-wrap';
                    body.textContent = v.cuerpo;
                    mail.appendChild(from);
                    mail.appendChild(subject);
                    mail.appendChild(body);
                    oirsResult.appendChild(mail);
                }
            }).catch(function (err) {
                oirsResult.innerHTML = '';
                var errEl = document.createElement('p');
                errEl.style.color = '#a33';
                errEl.textContent = 'No se pudo contactar al servidor: ' + err.message;
                oirsResult.appendChild(errEl);
            }).finally(function () {
                oirsBtn.disabled = false;
            });
        });
    }
})();
</script>
<?php
admin_footer();
