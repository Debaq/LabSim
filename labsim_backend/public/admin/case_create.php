<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/CaseBuilder.php';
require_once __DIR__ . '/../../src/CaseProfile.php';
require_once __DIR__ . '/../../src/CaseCompleteness.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/PatientPhoto.php';
require_once __DIR__ . '/../../src/OtoscopiaPhoto.php';
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
        echo '<p><a href="patients.php">&larr; Volver</a></p>';
        admin_footer();
        exit;
    }
}
$isEdit = $editCase !== null;

// Id temporal para poder subir fotos (paciente/otoscopia) ANTES de guardar
// el caso por primera vez -- sin esto, no hay case_id real todavía al cual
// amarrar el nombre del archivo. Se sube con esta clave y, al guardar
// (rama create_case más abajo), PatientPhoto::claim()/OtoscopiaPhoto::claim()
// renombran los archivos al case_id real. Sticky entre reintentos (si falla
// la validación, se reusa el mismo id en vez de generar uno nuevo, así no
// se pierden las fotos ya subidas); irrelevante en edición, ahí ya existe
// editId.
$uploadTempId = null;
if (!$isEdit) {
    $postedTempId = trim((string) ($_POST['upload_temp_id'] ?? ''));
    $uploadTempId = $postedTempId !== '' ? $postedTempId : ('tmp' . bin2hex(random_bytes(8)));
}

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
// Avisos de incoherencia con el perfil auditivo (ver CaseProfile::warnings).
// Solo se llenan en un POST de guardado; en GET el formulario se dibuja limpio.
$avisosPerfil = [];
// Datos que el perfil no puede calcular y el docente todavía no decidió
// (ver CaseCompleteness). Bloquean el guardado: no es una incoherencia
// opcional, es un caso incompleto.
$faltantes = [];
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
    $v['historia_clinica'] = $editPatient['historia_clinica'] ?? '';
    $v['comentario_docente'] = $editPatient['comentario_docente'] ?? '';
} else {
    $v = [];
}

// Otoscopia: sin selector de modo -- 1 sola fase (índice 0, sin texto) ES
// el modo "única", no hace falta elegirlo aparte; agregar una 2ª fase es lo
// que la convierte en "por fase". El shape de $v['otoscopia'] difiere
// según de dónde viene: CaseBuilder::caseDataToForm() (carga inicial al
// editar) entrega ['fases' => [['texto'=>...], ...]], mientras que un
// submit fallido deja $v['otoscopia'] = $_POST tal cual (['fase_count',
// 'texto' => [n => ...]]) para redibujar el form sticky. Se normaliza acá
// a variables sueltas en vez de forzar un shape único en $v, para no
// perder los valores ya tipeados si falla la validación.
if (isset($v['otoscopia']['fases']) && is_array($v['otoscopia']['fases'])) {
    $otoscopiaCount = max(1, count($v['otoscopia']['fases']));
    $otoscopiaTextoAt = static function (int $n) use ($v): string {
        return (string) ($v['otoscopia']['fases'][$n]['texto'] ?? '');
    };
} else {
    $otoscopiaCount = max(1, min(CaseBuilder::OTOSCOPIA_MAX_FASES, (int) ($v['otoscopia']['fase_count'] ?? 1)));
    $otoscopiaTextoAt = static function (int $n) use ($v): string {
        return (string) fv($v, ['otoscopia', 'texto', (string) $n], '');
    };
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

        // Deterioro tonal (Carhart/Stat/Rosemberg): dB sobre el umbral aéreo
        // que hay que subir para sostener el tono 1 min, por frecuencia del
        // protocolo de cada prueba (ver ResponseAudiometry.DECAY_TESTS).
        $decayFieldCounts = ['carhart' => 4, 'stat' => 3, 'rosemberg' => 4];
        $decayPairs = [];
        foreach ($decayFieldCounts as $mode => $count) {
            $vals = ['od' => [], 'oi' => []];
            foreach (['od', 'oi'] as $side) {
                for ($n = 0; $n < $count; $n++) {
                    $vals[$side][] = max(0, (int) fv($v, [$mode, $side, (string) $n], 0));
                }
            }
            $decayPairs[$mode] = zip_pairs($vals['od'], $vals['oi']);
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
        // salvo que el docente haya destildado el único "auto" global de la
        // tabla (un solo checkbox para las 6 celdas, no uno por celda).
        $rinne = [];
        $weber = [];
        $acumetriaValid = true;
        $acumetriaIsAuto = isset($v['acumetria_auto']);
        foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx) {
            $rinne[$hz] = [];
            foreach (['od', 'oi'] as $side) {
                if ($acumetriaIsAuto) {
                    $rinne[$hz][$side] = CaseBuilder::rinneAuto($aerea[$side][$freqIdx], $osea[$side][$freqIdx]);
                } else {
                    $manual = (string) fv($v, ['rinne', $hz, $side], 'positivo');
                    if (!in_array($manual, CaseBuilder::RINNE_OPTIONS, true)) {
                        $acumetriaValid = false;
                    }
                    $rinne[$hz][$side] = $manual;
                }
            }
            if ($acumetriaIsAuto) {
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
        // Supraliminares: en variables (y no leídas inline más abajo) porque
        // la proyección del perfil las puede reescribir.
        $sisiVals = [(int) fv($v, ['sisi', 'od'], 0), (int) fv($v, ['sisi', 'oi'], 0)];
        // Logoaudiometría: máxima discriminación por oído, en variable por
        // lo mismo que las supraliminares (la proyección la puede pisar).
        $umd = [
            ['int' => (int) fv($v, ['umd_int', 'od'], 35), 'percentage' => (int) fv($v, ['umd_pct', 'od'], 100)],
            ['int' => (int) fv($v, ['umd_int', 'oi'], 35), 'percentage' => (int) fv($v, ['umd_pct', 'oi'], 100)],
        ];
        $recruitVals = [isset($v['recruit']['od']), isset($v['recruit']['oi'])];

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

        // Otoscopia: sin modo -- 1 sola fase (índice 0) ya ES "única"; una
        // 2ª fase en adelante es lo que la convierte en "por fase".
        $otoscopiaCount = max(1, min(CaseBuilder::OTOSCOPIA_MAX_FASES, (int) ($v['otoscopia']['fase_count'] ?? 1)));
        $otoscopiaFases = [];
        for ($n = 0; $n < $otoscopiaCount; $n++) {
            // Fase 1 (índice 0) nunca tiene texto -- todavía no hay "fase
            // anterior" que describir.
            $texto = $n === 0 ? '' : trim((string) fv($v, ['otoscopia', 'texto', (string) $n], ''));
            $otoscopiaFases[] = ['texto' => $texto];
        }

        // ABR: una patología por oído (ver ABR_TYPE_OPTIONS) -- ya no hay
        // banco de casos compartido, cada paciente trae la suya (ver
        // AbrMainWindow.la_super/DEFAULT_ABR_CASE en el cliente).
        $abrBuild = static function (string $lado) use ($v): array {
            return [
                'type' => (string) fv($v, ['abr', $lado, 'type'], 'normal'),
                // Patrón retrococlear (ver ABR_NEURAL_DEFAULTS): se guarda
                // siempre, el generador solo lo mira si type === 'neural'.
                // Lo que se persiste son los parámetros, nunca la etiqueta
                // del preset -- la curva no puede depender de un nombre.
                'neural' => [
                    'i_iii_ms' => (float) fv($v, ['abr', $lado, 'neural', 'i_iii_ms'], CaseBuilder::ABR_NEURAL_DEFAULTS['i_iii_ms']),
                    'iii_v_ms' => (float) fv($v, ['abr', $lado, 'neural', 'iii_v_ms'], CaseBuilder::ABR_NEURAL_DEFAULTS['iii_v_ms']),
                    'global_delay_ms' => (float) fv($v, ['abr', $lado, 'neural', 'global_delay_ms'], CaseBuilder::ABR_NEURAL_DEFAULTS['global_delay_ms']),
                    'bloqueo' => (string) fv($v, ['abr', $lado, 'neural', 'bloqueo'], CaseBuilder::ABR_NEURAL_DEFAULTS['bloqueo']),
                    'v_i_factor' => (float) fv($v, ['abr', $lado, 'neural', 'v_i_factor'], CaseBuilder::ABR_NEURAL_DEFAULTS['v_i_factor']),
                    'microfonica' => (string) fv($v, ['abr', $lado, 'neural', 'microfonica'], CaseBuilder::ABR_NEURAL_DEFAULTS['microfonica']),
                    'desincronia' => (string) fv($v, ['abr', $lado, 'neural', 'desincronia'], CaseBuilder::ABR_NEURAL_DEFAULTS['desincronia']),
                    'sensibilidad_tasa' => (string) fv($v, ['abr', $lado, 'neural', 'sensibilidad_tasa'], CaseBuilder::ABR_NEURAL_DEFAULTS['sensibilidad_tasa']),
                ],
                'repro' => isset($v['abr'][$lado]['repro']),
                'repro_var' => (float) fv($v, ['abr', $lado, 'repro_var'], 0.2),
                // Cuanto se mueve el paciente DURANTE la captura (ver
                // agitation_run en ABR_generator.py). 0 = quieto.
                'inquietud' => (float) fv($v, ['abr', $lado, 'inquietud'], 0),
                // Reflejo post-auricular (miogenico, ~13 ms): 0 = no
                // aparece. Ver postauricular_reflex en ABR_generator.py.
                'pam' => (float) fv($v, ['abr', $lado, 'pam'], 0),
                // Falsa onda V: artefacto que solo se descubre mirando los
                // subpromedios A/B (ver false_wave en ABR_generator.py).
                // amp = 0 lo desactiva, que es el default: es un ejercicio
                // que el docente arma a proposito, no algo del paciente.
                'falsa_v' => [
                    'amp' => (float) fv($v, ['abr', $lado, 'falsa_v_amp'], 0),
                    'lat' => (float) fv($v, ['abr', $lado, 'falsa_v_lat'], 5.6),
                    // Rango de intensidades donde aparece: fuera de el la
                    // serie queda limpia y coherente, que es lo que deja
                    // usar la migracion de latencia como segunda prueba.
                    'int_min' => (float) fv($v, ['abr', $lado, 'falsa_v_int_min'], 0),
                    'int_max' => (float) fv($v, ['abr', $lado, 'falsa_v_int_max'], 120),
                    'mitad' => in_array(fv($v, ['abr', $lado, 'falsa_v_mitad'], 'auto'), ['auto', 'a', 'b'], true)
                        ? (string) fv($v, ['abr', $lado, 'falsa_v_mitad'], 'auto') : 'auto',
                ],
                'umbral' => (int) fv($v, ['abr', $lado, 'umbral'], 20),
                'average_objetivo' => (int) fv($v, ['abr', $lado, 'average_objetivo'], 2000),
                'desviaciones' => [
                    'onda_I' => ['lat' => (float) fv($v, ['abr', $lado, 'lat_I'], 0), 'amp' => (float) fv($v, ['abr', $lado, 'amp_I'], 0)],
                    'onda_III' => ['lat' => (float) fv($v, ['abr', $lado, 'lat_III'], 0), 'amp' => (float) fv($v, ['abr', $lado, 'amp_III'], 0)],
                    'onda_V' => ['lat' => (float) fv($v, ['abr', $lado, 'lat_V'], 0), 'amp' => (float) fv($v, ['abr', $lado, 'amp_V'], 0)],
                ],
                'fsp_puntos' => [
                    '800' => (float) fv($v, ['abr', $lado, 'fsp_800'], 2.3),
                    '2000' => (float) fv($v, ['abr', $lado, 'fsp_2000'], 2.8),
                    'objetivo' => (float) fv($v, ['abr', $lado, 'fsp_obj'], 3.0),
                ],
            ];
        };
        $abrOd = $abrBuild('od');
        $abrOi = $abrBuild('oi');

        // EOA: patología por oído, mismo shape simplificado (type + umbral)
        // que ABR usa para su curva -- ver oae_attenuation_db en
        // src/oae/generators/base.py.
        $eoasBuild = static function (string $lado) use ($v): array {
            $desv = [];
            foreach (CaseBuilder::EOAS_FREQS as $hz) {
                // Desviación en dB POR DEBAJO de la respuesta esperada
                // (positivo = OEA más chica), igual criterio que la
                // atenuación por patología: así "más número, peor oído".
                $desv[(string) $hz] = (float) fv($v, ['eoas', $lado, 'desv', (string) $hz], 0);
            }
            // SOAE: picos fijados a mano (las filas vacías se ignoran).
            $soaePicos = CaseBuilder::soaePeaksFromForm(fv($v, ['eoas', $lado, 'soae_peaks'], []));
            return [
                'type' => (string) fv($v, ['eoas', $lado, 'type'], 'normal'),
                'umbral' => (int) fv($v, ['eoas', $lado, 'umbral'], CaseBuilder::EOAS_DEFAULTS['umbral']),
                'atten_db' => (float) fv($v, ['eoas', $lado, 'atten_db'], CaseBuilder::EOAS_DEFAULTS['atten_db']),
                'ruido_db' => (float) fv($v, ['eoas', $lado, 'ruido_db'], CaseBuilder::EOAS_DEFAULTS['ruido_db']),
                'sello_pct' => (int) fv($v, ['eoas', $lado, 'sello_pct'], CaseBuilder::EOAS_DEFAULTS['sello_pct']),
                'variabilidad_db' => (float) fv($v, ['eoas', $lado, 'variabilidad_db'], CaseBuilder::EOAS_DEFAULTS['variabilidad_db']),
                'desviaciones' => $desv,
                'soae_mode' => (string) fv($v, ['eoas', $lado, 'soae_mode'], CaseBuilder::EOAS_DEFAULTS['soae_mode']),
                'soae_peaks' => $soaePicos,
            ];
        };
        $eoasOd = $eoasBuild('od');
        $eoasOi = $eoasBuild('oi');

        // Perfil auditivo: el sitio de la lesión (ver src/CaseProfile.php y
        // ROADMAP.md). El audiograma ya dice cuánta pérdida hay y cuánta es
        // conductiva; lo único que no puede decir es qué parte del
        // componente sensorioneural es coclear y cuál retrococlear. Eso es
        // `cce_pct`, y con `retro` es todo lo que el perfil agrega.
        //
        // Todavía no tiene UI propia (fase 3 del roadmap): viaja en inputs
        // ocultos y, en un caso que nunca lo tuvo, se infiere de la
        // patología ya cargada. Los `auto` arrancan apagados, así un caso
        // existente no cambia de comportamiento por abrirlo y guardarlo.
        $perfilLados = [];
        foreach ([['od', 'OD', $abrOd, $eoasOd], ['oi', 'OI', $abrOi, $eoasOi]] as [$lado, $ladoData, $abrLado, $eoasLado]) {
            $ccePost = fv($v, ['perfil', $lado, 'cce_pct'], null);
            $perfilLados[$ladoData] = [
                'cce_pct' => ($ccePost === null || $ccePost === '')
                    ? CaseProfile::inferCcePct($abrLado, $eoasLado)
                    : max(0.0, min(100.0, (float) $ccePost)),
                // El patrón retrococlear sigue viviendo en el tab ABR hasta
                // la fase 3: son los MISMOS inputs, no dos verdades.
                'retro' => CaseProfile::normalizeRetro($abrLado['neural']),
            ];
        }
        $perfilAuto = [];
        foreach (CaseProfile::AUTO_MODULES as $moduloAuto) {
            $perfilAuto[$moduloAuto] = (bool) fv($v, ['perfil', 'auto', $moduloAuto], false);
        }
        $perfil = [
            'version' => CaseProfile::VERSION,
            'OD' => $perfilLados['OD'],
            'OI' => $perfilLados['OI'],
            'auto' => $perfilAuto,
        ];

        // Todo lo que el perfil proyecta, calculado de una pasada (ver
        // CaseProfile::project). La misma función alimenta la vista previa
        // en vivo del formulario, vía admin/case_project.php: una sola
        // implementación de cada ley.
        $proyeccion = CaseProfile::project($airPairs, $bonePairs, $perfil, ['OD' => $zOd, 'OI' => $zOi]);
        $decomp = $proyeccion['decomp'];

        // Qué se aplica y qué no lo dicen los `auto`: un módulo en manual
        // sigue siendo del docente, incluso si el perfil predice otra cosa.
        if ($perfilAuto['abr']) {
            $abrOd = array_merge($abrOd, $proyeccion['abr']['OD']);
            $abrOi = array_merge($abrOi, $proyeccion['abr']['OI']);
        }
        if ($perfilAuto['eoas']) {
            $eoasOd = array_merge($eoasOd, $proyeccion['eoas']['OD']);
            $eoasOi = array_merge($eoasOi, $proyeccion['eoas']['OI']);
        }
        if ($perfilAuto['reflex']) {
            $reflexIpsi = $proyeccion['reflex']['ipsi'];
            $reflexContra = $proyeccion['reflex']['contra'];
            $reflexType = $proyeccion['reflex']['tipo'];
        }
        if ($perfilAuto['recruit']) {
            $sisiVals = $proyeccion['recruit']['sisi'];
            $recruitVals = $proyeccion['recruit']['recruit'];
            // Solo las frecuencias que el formulario ya reconoció como
            // calificantes: la proyección no agrega ni saca ninguna.
            foreach ($fowlerPatterns as $freqFowler => $_) {
                if (isset($proyeccion['recruit']['fowler'][(string) $freqFowler])) {
                    $fowlerPatterns[(string) $freqFowler] = $proyeccion['recruit']['fowler'][(string) $freqFowler];
                }
            }
            foreach ($proyeccion['recruit']['decay'] as $modoDecay => $valsDecay) {
                $decayPairs[$modoDecay] = zip_pairs($valsDecay['od'], $valsDecay['oi']);
            }
            // El LDL es la expresión audiométrica del reclutamiento: el
            // umbral sube y el disconfort no. Derivado, siempre está medido
            // (el 130 de "no medido" dejaría el hallazgo invisible).
            $ldl = $proyeccion['recruit']['ldl'];
        }
        if ($perfilAuto['logo']) {
            $umd = [
                ['int' => $proyeccion['logo']['OD']['int'], 'percentage' => $proyeccion['logo']['OD']['pct']],
                ['int' => $proyeccion['logo']['OI']['int'], 'percentage' => $proyeccion['logo']['OI']['pct']],
            ];
        }

        // VEMP: patología vestibular por oído. El subtipo (CVEMP cervical,
        // OVEMP ocular, MVEMP masetero) define qué picos se observan (ver
        // VEMP_PEAKS); los 4 peaks siempre se rinden en el form porque
        // simplificar con sub-bloques por subtipo haría el form más frágil
        // y no aporta nada pedagógico (el docente los edita y el cliente
        // usa solo los del subtipo activo).
        $vempBuild = static function (string $lado) use ($v): array {
            $subtipo = (string) fv($v, ['vemp', $lado, 'subtipo'], 'CVEMP');
            if (!in_array($subtipo, CaseBuilder::VEMP_SUBTIPOS, true)) {
                $subtipo = 'CVEMP';
            }
            $peaks = CaseBuilder::VEMP_PEAKS[$subtipo];
            $desv = [];
            // siempre persistimos los 4 picos aunque el subtipo use solo 2;
            // los picos no usados quedan con lat=0/amp=0 (no molestan).
            foreach (['p13', 'n23', 'n10', 'p16'] as $pico) {
                $desv[$pico] = [
                    'lat' => (float) fv($v, ['vemp', $lado, "lat_{$pico}"], 0),
                    'amp' => (float) fv($v, ['vemp', $lado, "amp_{$pico}"], 0),
                ];
            }
            return [
                'subtipo' => $subtipo,
                'type' => (string) fv($v, ['vemp', $lado, 'type'], 'normal'),
                'repro' => isset($v['vemp'][$lado]['repro']),
                'repro_var' => (float) fv($v, ['vemp', $lado, 'repro_var'], 0.2),
                'umbral' => (int) fv($v, ['vemp', $lado, 'umbral'], 60),
                'average_objetivo' => (int) fv($v, ['vemp', $lado, 'average_objetivo'], 200),
                'desviaciones' => $desv,
                'peaks' => $peaks,
            ];
        };
        $vempOd = $vempBuild('od');
        $vempOi = $vempBuild('oi');

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
        } elseif (!in_array($abrOd['type'], CaseBuilder::ABR_TYPE_OPTIONS, true) || !in_array($abrOi['type'], CaseBuilder::ABR_TYPE_OPTIONS, true)) {
            $error = 'Patología ABR inválida.';
        } elseif (!in_array($eoasOd['type'], CaseBuilder::EOAS_TYPE_OPTIONS, true) || !in_array($eoasOi['type'], CaseBuilder::EOAS_TYPE_OPTIONS, true)) {
            $error = 'Patología EOA inválida.';
        } elseif ($eoasOd['sello_pct'] < 5 || $eoasOd['sello_pct'] > 100 || $eoasOi['sello_pct'] > 100 || $eoasOi['sello_pct'] < 5) {
            $error = 'Sello de sonda EOA fuera de rango (5-100%).';
        } elseif ($eoasOd['variabilidad_db'] < 0 || $eoasOi['variabilidad_db'] < 0 || $eoasOd['ruido_db'] < -20 || $eoasOi['ruido_db'] < -20) {
            $error = 'Ruido/variabilidad EOA fuera de rango.';
        } elseif (!in_array($eoasOd['soae_mode'], CaseBuilder::EOAS_SOAE_MODES, true) || !in_array($eoasOi['soae_mode'], CaseBuilder::EOAS_SOAE_MODES, true)) {
            $error = 'Modo SOAE inválido.';
        } elseif (($soaeError = CaseBuilder::soaePeaksError($eoasOd) ?? CaseBuilder::soaePeaksError($eoasOi)) !== null) {
            $error = $soaeError;
        } elseif (!in_array($vempOd['type'], CaseBuilder::VEMP_TYPE_OPTIONS, true) || !in_array($vempOi['type'], CaseBuilder::VEMP_TYPE_OPTIONS, true)) {
            $error = 'Patología VEMP inválida.';
        } elseif (($neuralError = CaseBuilder::neuralParamsError($abrOd['neural'], 'OD')
                ?? CaseBuilder::neuralParamsError($abrOi['neural'], 'OI')) !== null) {
            $error = $neuralError;
        // La coherencia se chequea sobre lo que el docente escribió a mano.
        // Un módulo derivado del perfil no puede contradecirse a sí mismo, y
        // además su umbral ya no está en la misma unidad que este chequeo
        // (el del ABR es dB nHL, no dB HL).
        } elseif (($coherencia = CaseBuilder::normalCoherenceError($abrOd, 'ABR', 'OD', !$perfilAuto['abr'])
                ?? CaseBuilder::normalCoherenceError($abrOi, 'ABR', 'OI', !$perfilAuto['abr'])
                ?? ($perfilAuto['eoas'] ? null : CaseBuilder::normalCoherenceError($eoasOd, 'EOA', 'OD'))
                ?? ($perfilAuto['eoas'] ? null : CaseBuilder::normalCoherenceError($eoasOi, 'EOA', 'OI'))
                // VEMP sin chequeo de umbral: el suyo ronda 60-90 dB nHL.
                ?? CaseBuilder::normalCoherenceError($vempOd, 'VEMP', 'OD', false)
                ?? CaseBuilder::normalCoherenceError($vempOi, 'VEMP', 'OI', false)) !== null) {
            $error = $coherencia;
        }

        // Incoherencias entre lo cargado a mano y lo que predice el perfil.
        // Avisan, no bloquean: un caso puede ser incoherente a propósito (el
        // Stenger y la simulación lo NECESITAN). Por eso se muestran una vez
        // y se guardan igual tildando la casilla -- pero el docente tiene que
        // haberlos leído, que es lo que hoy no pasa en ningún lado.
        $avisosPerfil = [];
        if ($error === null && !isset($v['perfil_confirmar'])) {
            $avisosPerfil = CaseProfile::warnings(
                $decomp, $perfil,
                ['OD' => $abrOd, 'OI' => $abrOi],
                ['OD' => $eoasOd, 'OI' => $eoasOi],
                ['ipsi' => $reflexIpsi, 'contra' => $reflexContra],
                ['OD' => $zOd, 'OI' => $zOi]
            );
        }

        if ($error === null && $avisosPerfil === []) {
            $antecedentes = [];
            foreach (CaseBuilder::HIST_CHECKBOXES as $h) {
                $antecedentes[$h] = isset($v['hist'][$h]);
            }

            // Estado del borrador de IA. `generado` lo pone el JS al traer
            // el borrador; `verificado` sale de la casilla que el docente
            // tilda después de leerlo, y se limpia sola al regenerar (el
            // texto nuevo no lo leyó nadie todavía). Se guarda quién y
            // cuándo: si el caso sale mal, hay a quién preguntarle.
            $iaGenerado = !empty($v['anamnesis_ia']['generado']);
            $iaVerificado = $iaGenerado && !empty($v['anamnesis_ia']['verificado']);
            $anamnesisIa = [
                'generado' => $iaGenerado,
                'verificado' => $iaVerificado,
                'generado_en' => trim((string) fv($v, ['anamnesis_ia', 'generado_en'], '')),
                'verificado_por' => $iaVerificado ? (string) ($me['username'] ?? $me['id'] ?? '') : '',
                'verificado_en' => $iaVerificado ? date('c') : '',
            ];

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
                'umd' => $umd,
                'sdt' => $sdt,
                'srt' => $srt,
                'fowler' => [
                    'enabled' => $fowlerEnabled,
                    'patterns' => $fowlerPatterns,
                    'diplacusia' => $fowlerDiplacusia,
                ],
                'stenger' => [isset($v['stenger']['od']), isset($v['stenger']['oi'])],
                'sisi' => $sisiVals,
                'recruit' => $recruitVals,
                'decay' => [false, false], // reemplazado por carhart/stat/rosemberg; se conserva el shape por compatibilidad con casos viejos
                'carhart' => $decayPairs['carhart'],
                'stat' => $decayPairs['stat'],
                'rosemberg' => $decayPairs['rosemberg'],
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
                    // Trazabilidad del borrador escrito por el LLM. Sin
                    // `verificado` en true el caso no se guarda ni se cita
                    // (ver CaseCompleteness): el modelo puede inventar una
                    // cirugía que no existe, y eso le llega al alumno como
                    // parte del caso.
                    'ia' => $anamnesisIa,
                ],
                'comportamiento' => trim((string) ($v['comportamiento'] ?? '')),
                'disposicion' => (int) ($v['disposicion'] ?? 0),
                'otoscopia' => ['fases' => $otoscopiaFases],
                'perfil' => $perfil,
                'abr' => ['OD' => $abrOd, 'OI' => $abrOi],
                'eoas' => ['OD' => $eoasOd, 'OI' => $eoasOi],
                'vemp' => ['OD' => $vempOd, 'OI' => $vempOi],
            ]);

            // Lo que no se puede calcular tiene que estar decidido antes de
            // que el caso salga del editor: un timpanograma en A con 40 dB
            // de gap, o un ABR "coclear" con la morfología de onda de un
            // oído sano, le llegan al alumno como un paciente que no cierra
            // y el docente no se entera nunca. Ver CaseCompleteness.
            //
            // No es lo mismo que $avisosPerfil: aquellos son incoherencias
            // que pueden SER el ejercicio (Stenger, falsa onda V) y se
            // guardan tildando una casilla. Esto es un dato que falta, y no
            // hay caso sin él.
            $faltantes = CaseCompleteness::pendingTexts($data);
        }

        if ($error === null && $avisosPerfil === [] && $faltantes === []) {
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
                $editHistoriaClinica = trim((string) ($v['historia_clinica'] ?? ''));
                Patients::updateHistoriaClinica($pdo, $editPatientId, $editHistoriaClinica);
                Patients::updateComentarioDocente($pdo, $editPatientId, trim((string) ($v['comentario_docente'] ?? '')));
                // También va en cases.data (no solo en patients) para que llegue
                // al cliente de escritorio via sync.php -- ese endpoint sincroniza
                // cases, no patients. Soporta llaves {{N}} (N = offset en días
                // respecto a la fecha de la cita, ej. {{-5}}) que Agenda.py
                // resuelve a una fecha concreta al armar la ficha del alumno.
                $data['historia_clinica'] = $editHistoriaClinica;

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

                header('Location: patients.php');
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
            $postedRut = trim((string) ($v['rut'] ?? ''));
            $postedFechaNacIso = trim((string) ($v['fecha_nac'] ?? ''));
            $snapshotRut = $postedRut !== '' ? $postedRut : (string) CaseBuilder::rutFromAge($age);
            $snapshotFechaNac = $postedFechaNacIso !== '' ? date('d-m-Y', strtotime($postedFechaNacIso)) : CaseBuilder::randomFechaNacForAge($age);
            $data['paciente_snapshot'] = [
                'nombre' => $snapshotNombre,
                'apellido' => $snapshotApellido,
                'rut' => $snapshotRut,
                'fecha_nac' => $snapshotFechaNac,
                'procedimiento' => 'Audiometría',
            ];

            $newPatientId = Patients::upsertByRut($pdo, $snapshotRut, $snapshotNombre, $snapshotApellido, $snapshotFechaNac);
            $newHistoriaClinica = trim((string) ($v['historia_clinica'] ?? ''));
            Patients::updateHistoriaClinica($pdo, $newPatientId, $newHistoriaClinica);
            Patients::updateComentarioDocente($pdo, $newPatientId, trim((string) ($v['comentario_docente'] ?? '')));
            // Ídem rama de edición más arriba: también en cases.data para sync.php.
            $data['historia_clinica'] = $newHistoriaClinica;

            $pdo->prepare(
                "INSERT INTO cases (id, data, updated_at, patient_id) VALUES (?, ?, CURRENT_TIMESTAMP, ?)
                 ON CONFLICT(id) DO UPDATE SET data = excluded.data, updated_at = CURRENT_TIMESTAMP, patient_id = excluded.patient_id"
            )->execute([$id, json_encode($data, JSON_UNESCAPED_UNICODE), $newPatientId]);
            AdminAudit::log($me, 'case_create', ['case_id' => $id, 'nombre' => $snapshotNombre, 'apellido' => $snapshotApellido]);

            // Reclama las fotos (paciente/otoscopia) subidas antes de guardar,
            // si las hubo -- ver $uploadTempId más arriba.
            if ($uploadTempId !== null) {
                PatientPhoto::claim($uploadTempId, $id);
                OtoscopiaPhoto::claim($uploadTempId, $id);
            }

            header('Location: agenda.php?schedule=' . urlencode($id));
            exit;
        }
    }
}

admin_add_css('case.css');
admin_header($isEdit ? 'Editar caso clínico ' . $editId : 'Crear caso clínico', $me);
?>

<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if (!empty($faltantes)): ?>
<div class="card" style="border-left:4px solid #b00;">
    <strong>Falta decidir lo que el perfil no puede calcular</strong>
    <ul>
        <?php foreach ($faltantes as $falta): ?>
        <li><?= htmlspecialchars($falta) ?></li>
        <?php endforeach; ?>
    </ul>
    <p class="legend help">Esto no es opcional y no se guarda igual: son datos clínicos que ninguna cuenta puede sacar del audiograma. Sin ellos el alumno se encuentra con un paciente que no cierra, y vos no te enterás.</p>
</div>
<?php endif; ?>
<?php if (!empty($avisosPerfil)): ?>
<div class="card" style="border-left:4px solid #7a5b00;">
    <strong>El caso no coincide con el perfil auditivo</strong>
    <ul>
        <?php foreach ($avisosPerfil as $aviso): ?>
        <li><?= htmlspecialchars($aviso) ?></li>
        <?php endforeach; ?>
    </ul>
    <p class="legend help">Corregí lo que corresponda, o marcá la casilla y volvé a guardar si la incoherencia es parte del ejercicio (simulación, Stenger, falsa onda V).</p>
</div>
<?php endif; ?>

<form method="post" id="case-form">
<?= csrf_field() ?>
<?php if ($isEdit): ?><input type="hidden" name="case_id" value="<?= htmlspecialchars($editId) ?>">
<?php else: ?><input type="hidden" name="upload_temp_id" value="<?= htmlspecialchars($uploadTempId) ?>">
<?php endif; ?>
<?php $photoCaseId = $isEdit ? $editId : $uploadTempId; ?>
<div class="tabs" role="tablist">
    <button type="button" class="tab-btn active" data-tab="paciente">Paciente</button>
    <button type="button" class="tab-btn" data-tab="perfil">Perfil auditivo</button>
    <button type="button" class="tab-btn" data-tab="otoscopia">Otoscopia</button>
    <button type="button" class="tab-btn" data-tab="audiometria">Audiometría</button>
    <button type="button" class="tab-btn" data-tab="timpanometria">Timpanometría</button>
    <button type="button" class="tab-btn" data-tab="tinnitus">Tinnitus</button>
    <button type="button" class="tab-btn" data-tab="abr">ABR</button>
    <button type="button" class="tab-btn" data-tab="eoas">EOA</button>
    <button type="button" class="tab-btn" data-tab="vemp">VEMP</button>
    <button type="button" class="tab-btn" data-tab="anamnesis">Anamnesis</button>
</div>

<div class="tab-panel active" data-tab="paciente">
<div class="card">
    <strong>Paciente</strong>
    <?php if ($isEdit): ?><input type="hidden" id="chat-static-name" value="<?= htmlspecialchars($editDisplayName) ?>"><?php endif; ?>
    <label class="inline-check"><input type="radio" name="gender" value="0" <?= ($v['gender'] ?? '0') === '0' ? 'checked' : '' ?>> Hombre</label>
    <label class="inline-check"><input type="radio" name="gender" value="1" <?= ($v['gender'] ?? '0') === '1' ? 'checked' : '' ?>> Mujer</label>
    <div class="three-col">
        <label>Edad
            <input type="number" name="age" id="patient-age" min="0" max="110" value="<?= htmlspecialchars((string) ($v['age'] ?? '')) ?>">
        </label>
        <label>Fecha de nacimiento
            <input type="text" name="fecha_nac" id="patient-fecha-nac" value="<?= htmlspecialchars((string) ($v['fecha_nac'] ?? '')) ?>" readonly title="Se calcula sola a partir de la edad (día y mes al azar)." placeholder="AAAA-MM-DD">
        </label>
        <label>RUT
            <input type="text" name="rut" id="patient-rut" value="<?= htmlspecialchars((string) ($v['rut'] ?? '')) ?>">
        </label>
    </div>
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
    </div>
    <p class="legend" class="help">Esto edita al <strong>paciente</strong>: el cambio se aplica también a cualquier otra cita/ronda de la misma persona.</p>
    <?php endif; ?>

    <label>Historia clínica
        <textarea name="historia_clinica" rows="6" class="input" placeholder="Antecedentes generales, evolución, observaciones del paciente..."><?= htmlspecialchars((string) ($v['historia_clinica'] ?? '')) ?></textarea>
    </label>
    <p class="legend" class="help">Historia clínica base del <strong>paciente</strong> (no depende del caso). No incluye las notas individuales de cada alumno por atención -- esas se ven en la agenda/asistencia, no se editan acá.</p>

    <label>Comentario del docente <span style="font-weight:400; color:var(--color-danger);">(privado -- el alumno nunca lo ve)</span>
        <textarea name="comentario_docente" rows="3" class="input" placeholder="Ej: hipoacusia sensorioneural bilateral leve, caso pensado para practicar enmascaramiento..."><?= htmlspecialchars((string) ($v['comentario_docente'] ?? '')) ?></textarea>
    </label>
    <p class="legend" class="help">Nota interna del <strong>paciente</strong> (ej. qué patología representa el caso). Solo la ve el docente en este panel -- no se sincroniza a la ficha del alumno ni al cliente de escritorio.</p>

    <div class="photo-block">
        <strong style="display:block; margin-bottom:0.4rem;">Foto</strong>
        <p id="photo-msg" class="legend" hidden></p>
        <?php $hasAvatar = PatientPhoto::hasAvatar($photoCaseId); ?>
        <div style="display:flex; align-items:center; gap:1rem;">
            <img id="patient-avatar-preview" class="patient-avatar"
                 src="patient_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;type=avatar&amp;v=<?= time() ?>"
                 alt="Avatar del paciente" <?= $hasAvatar ? '' : 'hidden' ?>>
            <div id="patient-avatar-empty" class="patient-avatar patient-avatar-empty" <?= $hasAvatar ? 'hidden' : '' ?>>Sin foto</div>
            <div>
                <input type="file" id="patient-photo-input" accept="image/jpeg,image/png,image/webp">
                <p class="legend">Al elegir una foto se abre un recorte circular -- se guarda una versión reducida completa y el avatar recortado.</p>
                <p class="legend">
                    <a id="patient-download-original" href="patient_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;type=original&amp;download=1" <?= $hasAvatar ? '' : 'hidden' ?>>Descargar foto grande</a>
                    &nbsp;|&nbsp;
                    <a id="patient-download-avatar" href="patient_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;type=avatar&amp;download=1" <?= $hasAvatar ? '' : 'hidden' ?>>Descargar foto recortada</a>
                </p>
            </div>
        </div>
    </div>
</div>
</div>

<div class="tab-panel" data-tab="perfil">
<div class="card">
    <strong>Perfil auditivo</strong>
    <p class="legend help">Dónde está la lesión de este paciente. El audiograma (pestaña Audiometría) ya dice cuánta pérdida hay y cuánta es conductiva, frecuencia por frecuencia; lo único que no puede decir es qué parte del componente sensorioneural es coclear y qué parte es retrococlear. Eso se define acá, una vez, y desde acá se proyecta a los exámenes que tengan la casilla de derivación encendida.</p>
    <p class="legend help">Sin ninguna casilla marcada nada cambia: cada pestaña se sigue cargando a mano, como siempre. La derivación existe para que el caso no se contradiga solo (una OEA normal con un gap de 40 dB, un ABR normal con un audiograma profundo), no para impedir armar un caso incoherente a propósito -- el Stenger, la falsa onda V y la simulación necesitan esa incoherencia.</p>
    <p class="legend">Sortear un cuadro clínico completo</p>
    <div class="three-col">
        <label>Cuadro
            <select id="perfil-escenario">
                <?php foreach (CaseProfile::SCENARIOS as $escKey => $esc): ?>
                <option value="<?= htmlspecialchars($escKey) ?>"><?= htmlspecialchars($esc['label']) ?></option>
                <?php endforeach; ?>
                <option value="__random__">Al azar entre todos</option>
            </select>
        </label>
        <label style="align-self:end;">
            <button type="button" class="secondary" id="perfil-sortear">Sortear caso</button>
        </label>
    </div>
    <p class="legend help">Escribe el audiograma completo (aérea y ósea, los dos oídos), el sitio de la lesión y el patrón retrococlear si corresponde, y enciende las derivaciones. La forma es la del cuadro elegido pero la magnitud se sortea, así dos casos del mismo cuadro no salen calcados. Después se edita cualquier campo a mano.</p>
    <p class="legend help">Los "Autocompletar" de ABR y EOA siguen donde estaban y siguen sirviendo: sortean lo que el perfil no describe (latencias y amplitudes onda por onda, FSP, ruido del paciente, sello de la sonda). Lo que ya no hace falta es usarlos para fijar el umbral y la patología, que es donde se contradecían entre sí.</p>

    <p class="legend">Qué exámenes se derivan del perfil</p>
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
    <p class="legend help">OEA: la atenuación pasa a salir del componente coclear y del gap, frecuencia por frecuencia. Reflejos: la sonda decide si el reflejo se ve (oído medio) y el oído estimulado a qué nivel aparece; una coclear no sube el umbral en proporción a la pérdida (Metz) y una retrococlear sí, y el patrón OFF --el reflejo que no se sostiene-- sale del componente retro. Supraliminares: reclutamiento, deterioro tonal y LDL miden el mismo eje desde tres lados, así que salen del mismo número y no pueden contradecirse; el LDL no sube con la pérdida coclear, y por eso el campo dinámico se cierra solo.</p>
    <p class="legend help">Logoaudiometría: la discriminación máxima cae despacio en una coclear y se desploma en una retrococlear, muy por debajo de lo que predice el audiograma -- es la disociación audio-verbal. El gap no la baja: una conductiva no distorsiona, solo pide más intensidad. El rollover (la curva que cae pasado el máximo) ya venía del reclutamiento.</p>
    <p class="legend help">El timpanograma no se deriva: qué curva sale depende de la patología concreta (B ocupación, As rígido, Ad hipercompliante, C retracción) y esa es una decisión clínica, no una cuenta. Lo que sí se hace es avisar si contradice al gap.</p>
</div>
<div class="card">
    <strong>Umbral por estímulo, derivado del audiograma</strong>
    <p class="legend help">Con esto encendido, el umbral del ABR deja de ser un número por oído y pasa a calcularse por estímulo desde la audiometría del caso: el burst de 500 Hz responde según el umbral en 500, el de 4 kHz según el de 4 kHz, el click según la base coclear (2-4 kHz) y el chirp con más peso en los graves. Es lo que permite pedir una evaluación frecuencia específica en una hipoacusia descendente. La vía ósea usa los umbrales óseos, así que el gap conductivo del ABR sale del audiograma solo.</p>
    <p class="legend help">Los números de la tabla están en dB nHL, no en dB HL: incluyen la corrección conductual-electrofisiológica (+20 dB en 500 Hz, +15 en 1 k, +10 en 2 k, +5 en 4 k, +10 el click, +5 el chirp). Por eso un oído de 0 dB HL igual muestra 20 dB nHL con burst de 500 -- convertir nHL a eHL es parte de lo que el alumno tiene que hacer.</p>
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
        <p class="legend help">El campo "Umbral (dB)" de cada oído queda de solo lectura: lo escribe esta tabla (con el valor del click, que es lo que mostraría un ABR de rutina).</p>
    </div>
</div>
<div class="two-col">
<?php foreach (['od' => 'OD', 'oi' => 'OI'] as $lado => $ladoLabel): ?>
<div class="card">
    <strong>Oído <?= $ladoLabel ?></strong>
    <div class="three-col">
        <label>Proporción coclear del componente sensorioneural (%)
            <input type="number" step="5" min="0" max="100" name="perfil[<?= $lado ?>][cce_pct]" value="<?= htmlspecialchars((string) fv($v, ['perfil', $lado, 'cce_pct'], '100')) ?>">
        </label>
    </div>
    <p class="legend help">100 % = pérdida coclear pura: las células ciliadas externas están dañadas, la OEA cae con el umbral y hay reclutamiento. 0 % = pérdida retrococlear pura: la cóclea está viva, la OEA se conserva con el umbral elevado y el ABR es el que se desarma -- es la neuropatía auditiva, y ese contraste entre OEA y ABR es el hallazgo. Los valores intermedios reparten la pérdida entre los dos sitios.</p>
    <p class="legend help">Esto no toca el audiograma: la pérdida en dB la fija la pestaña Audiometría. Acá se dice de qué está hecha esa pérdida.</p>
    <?php $vn = $v['abr'][$lado]['neural'] ?? []; ?>
    <div class="abr-neural-block" data-lado="<?= $lado ?>">
        <p class="legend">Patrón retrococlear. El PEATC no distingue las entidades entre sí (un schwannoma y un meningioma del ángulo dan el mismo trazado) -- lo que distingue son estos patrones, así que el caso guarda los números, no el diagnóstico. El preset es solo un punto de partida: precarga los valores y después se editan.</p>
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
        <p class="legend help abr-neural-preset-nota" data-lado="<?= $lado ?>"></p>
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
        <p class="legend help">La diferencia interaural de onda V (IT5) no se configura acá: sale de que los dos oídos tengan patrones distintos. Y la replicabilidad pobre es la casilla "Reproducible" de arriba.</p>
    </div>
</div>
<?php endforeach; ?>
</div>
</div>

<div class="tab-panel" data-tab="otoscopia">
<div class="card">
    <strong>Otoscopia</strong>
    <p class="legend">Una sola fase (la de por defecto) = una imagen por oído, nada más. Agregar una 2ª fase en adelante es lo que la convierte en "por fase": cada fase desde la 2ª lleva un texto libre que describe qué pasó entremedio (ej. "se realizó un lavado ótico"). Qué fase le corresponde ver a cada alumno según su propio avance con este paciente no está implementado todavía (ver TODO.md); por ahora siempre se muestra la fase 1.</p>

    <input type="hidden" name="otoscopia[fase_count]" id="otoscopia-fase-count" value="<?= $otoscopiaCount ?>">
    <p id="otoscopia-msg" class="legend" hidden></p>

    <div id="otoscopia-fases">
        <?php for ($faseIdx = 0; $faseIdx < $otoscopiaCount; $faseIdx++): ?>
        <div class="otoscopia-fase" data-fase-idx="<?= $faseIdx ?>">
            <div class="side-heading">
                <span class="side-tag">Fase <?= $faseIdx + 1 ?></span>
                <?php if ($faseIdx > 0): ?>
                <button type="button" class="secondary otoscopia-remove-fase" data-fase-idx="<?= $faseIdx ?>" <?= $faseIdx === $otoscopiaCount - 1 ? '' : 'hidden' ?>>Quitar esta fase</button>
                <?php endif; ?>
            </div>
            <?php if ($faseIdx > 0): ?>
            <label>¿Qué pasó desde la fase anterior? (texto libre, se muestra al alumno)
                <textarea name="otoscopia[texto][<?= $faseIdx ?>]" rows="2"><?= htmlspecialchars($otoscopiaTextoAt($faseIdx)) ?></textarea>
            </label>
            <?php endif; ?>
            <div class="two-col">
                <?php foreach (['od' => 'OD', 'oi' => 'OI'] as $side => $sideLabel): ?>
                <div class="otoscopia-photo-slot">
                    <span class="side-tag <?= $side ?>"><?= $sideLabel ?></span><br>
                    <?php $hasOto = OtoscopiaPhoto::has($photoCaseId, $side, $faseIdx); ?>
                    <img class="otoscopia-thumb" data-side="<?= $side ?>" data-fase-idx="<?= $faseIdx ?>"
                         src="otoscopia_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;side=<?= $side ?>&amp;fase=<?= $faseIdx ?>&amp;v=<?= time() ?>"
                         alt="Otoscopia <?= $sideLabel ?> fase <?= $faseIdx + 1 ?>" <?= $hasOto ? '' : 'hidden' ?>>
                    <div class="otoscopia-thumb-empty" <?= $hasOto ? 'hidden' : '' ?>>Sin imagen</div>
                    <input type="file" class="otoscopia-photo-input" data-side="<?= $side ?>" data-fase-idx="<?= $faseIdx ?>" accept="image/jpeg,image/png,image/webp">
                    <button type="button" class="secondary otoscopia-delete-photo" data-side="<?= $side ?>" data-fase-idx="<?= $faseIdx ?>" <?= $hasOto ? '' : 'hidden' ?>>Borrar foto</button>
                    <a class="otoscopia-download-photo" href="otoscopia_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;side=<?= $side ?>&amp;fase=<?= $faseIdx ?>&amp;download=1" data-side="<?= $side ?>" data-fase-idx="<?= $faseIdx ?>" <?= $hasOto ? '' : 'hidden' ?>>Descargar</a>
                </div>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endfor; ?>
    </div>

    <button type="button" id="otoscopia-add-fase" class="secondary">+ Agregar fase</button>

    <!-- Fuente única del markup de un slot/fase vacíos: usado por JS al agregar fase (#otoscopia-add-fase).
         El render inicial (arriba, PHP) es aparte porque necesita mostrar la foto ya guardada si existe. -->
    <template id="otoscopia-slot-tpl">
        <div class="otoscopia-photo-slot">
            <span class="side-tag"></span><br>
            <img class="otoscopia-thumb" hidden>
            <div class="otoscopia-thumb-empty">Sin imagen</div>
            <input type="file" class="otoscopia-photo-input" accept="image/jpeg,image/png,image/webp">
            <button type="button" class="secondary otoscopia-delete-photo" hidden>Borrar foto</button>
            <a class="otoscopia-download-photo" hidden>Descargar</a>
        </div>
    </template>
    <template id="otoscopia-fase-tpl">
        <div class="otoscopia-fase">
            <div class="side-heading">
                <span class="side-tag">Fase</span>
                <button type="button" class="secondary otoscopia-remove-fase">Quitar esta fase</button>
            </div>
            <label>¿Qué pasó desde la fase anterior? (texto libre, se muestra al alumno)
                <textarea rows="2"></textarea>
            </label>
            <div class="two-col"></div>
        </div>
    </template>
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
        <div class="table-wrap">
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
    </div>
    <?php endforeach; ?>
    <p class="legend">LDL sin marcar = no medido, se guarda como ausente (130) sin importar lo que quede escrito arriba.</p>
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
    <p class="legend">
        <label class="inline-check"><input type="checkbox" id="acumetria-auto-toggle" name="acumetria_auto" value="1"
               <?= $acumetriaIsAuto ? 'checked' : '' ?>>auto (calcular Rinne y Weber desde los umbrales tonales)</label>
    </p>
    <div class="table-wrap">
    <table class="grid-table" style="margin-bottom:0.5rem;">
        <tr><th></th><?php foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx): ?><th><?= $hz ?> Hz</th><?php endforeach; ?></tr>
        <?php foreach (['od' => 'OD', 'oi' => 'OI'] as $side => $sideLabel): ?>
        <tr>
            <td class="side-label">Rinne <?= $sideLabel ?></td>
            <?php foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx):
                $rinneVal = (string) fv($v, ['rinne', $hz, $side], 'positivo');
            ?>
            <td>
                <select id="rinne_<?= $freqIdx ?>_<?= $side ?>" class="rinne-select" data-freq="<?= $freqIdx ?>" data-side="<?= $side ?>"
                        name="rinne[<?= $hz ?>][<?= $side ?>]" <?= $acumetriaIsAuto ? 'disabled' : '' ?>>
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
                        name="weber[<?= $hz ?>]" <?= $acumetriaIsAuto ? 'disabled' : '' ?>>
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
    <div class="table-wrap">
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
    </div>

    <div class="two-col">
        <?php foreach (['od' => 'OD', 'oi' => 'OI'] as $side => $sideLabel): ?>
        <div class="side-block">
            <div class="side-heading"><span class="side-tag <?= $side ?>"><?= $sideLabel ?></span></div>
            <label>UMD (int / %)
                <input type="number" step="5" class="umd-int-input" data-side="<?= $side ?>" name="umd_int[<?= $side ?>]" value="<?= htmlspecialchars((string) fv($v, ['umd_int', $side], 35)) ?>" class="input input--narrow" style="display:inline-block;">
                / <input type="number" step="4" class="umd-pct-input" data-side="<?= $side ?>" name="umd_pct[<?= $side ?>]" value="<?= htmlspecialchars((string) fv($v, ['umd_pct', $side], 100)) ?>" class="input input--narrow" style="display:inline-block;">
            </label>
            <label>SISI <input type="number" step="5" name="sisi[<?= $side ?>]" value="<?= htmlspecialchars((string) fv($v, ['sisi', $side], 0)) ?>"></label>
            <label class="inline-check"><input type="checkbox" name="stenger[<?= $side ?>]" <?= isset($v['stenger'][$side]) ? 'checked' : '' ?>> Stenger</label>
            <label class="inline-check"><input type="checkbox" class="recruit-toggle" data-side="<?= $side ?>" name="recruit[<?= $side ?>]" <?= isset($v['recruit'][$side]) ? 'checked' : '' ?>> Reclutamiento</label>
        </div>
        <?php endforeach; ?>
    </div>

    <p class="legend">Deterioro tonal (Carhart / Stat / Rosemberg): dB que hay que subir sobre el umbral aéreo para que el oído sostenga el tono 1 minuto completo. 0 = sin deterioro (lo sostiene de inmediato). Si nunca alcanza a sostenerlo ni en el techo (salida máxima o LDL, lo que sea menor), pon un valor igual o mayor a ese rango.</p>
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
        <?php foreach (['od' => 'OD', 'oi' => 'OI'] as $side => $sideLabel): ?>
        <tr>
            <td class="side-label"><?= $sideLabel ?></td>
            <?php foreach ($info['freqs'] as $n => $f): ?>
            <td><input type="number" step="5" min="0" name="<?= $mode ?>[<?= $side ?>][<?= $n ?>]" value="<?= htmlspecialchars((string) fv($v, [$mode, $side, (string) $n], 0)) ?>"></td>
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
        <p class="legend">Se detectan solas las frecuencias (250-4000 Hz) donde los umbrales ya tipeados arriba cumplen los requisitos ABLB -- puede calificar más de una a la vez. Para cada una, indica qué le pasa al paciente al hacer la prueba ahí (por defecto, sin reclutamiento).</p>
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
    <?php
    $reflexGroups = ['ipsi' => ['label' => 'Ipsilateral', 'freqs' => [500, 1000, 2000, 4000]],
                      'contra' => ['label' => 'Contralateral', 'freqs' => [500, 1000, 2000, 4000, 'WN']]];
    foreach ($reflexGroups as $mode => $info):
    ?>
    <div class="table-wrap">
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
    </div>
    <?php endforeach; ?>
    <div class="table-wrap">
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

<div class="tab-panel" data-tab="abr">
<?php $abrAuthorCatalog = AppConfig::getEffective('abr_reference_authors', null) ?? []; ?>
<div class="card">
    <strong>Autocompletar ABR</strong>
    <p class="legend help">Autor/set de referencia para los botones "Autocompletar" de abajo (uno solo para todo el paciente, ambos oídos). Cada autor puede reportar baselines de latencia/amplitud levemente distintos según la población -- se configuran en <a href="normativas.php">Configuración &rsaquo; Normativas</a>. No queda guardado en el caso, solo se usa para calcular la sugerencia; los números finales sí quedan en cada campo.</p>
    <label style="max-width:22em;">Autor de referencia
        <select id="abr-author-select">
            <option value="__default__">LabSim (default)</option>
            <?php foreach ($abrAuthorCatalog as $authorId => $author): ?>
            <option value="<?= htmlspecialchars($authorId) ?>"><?= htmlspecialchars($author['label'] ?? $authorId) ?></option>
            <?php endforeach; ?>
        </select>
    </label>
</div>
<div class="two-col">
<?php foreach (['od' => 'OD', 'oi' => 'OI'] as $lado => $ladoLabel): ?>
<div class="card">
    <strong>ABR <?= $ladoLabel ?></strong>
    <p class="legend help">Patología de este oído para el generador de curvas ABR -- no es el resultado del alumno, es lo que el caso simula. Si se deja "Normal" con todo en 0, el oído no tiene hallazgos.</p>

    <p class="legend help">"Autocompletar" sugiere valores plausibles para la patología elegida, usando el sexo y la edad del paciente (pestaña Paciente), el autor de referencia elegido arriba, y las mismas referencias normativas del generador de curvas. Es un punto de partida al azar -- se puede editar cualquier campo después.</p>
    <div class="three-col">
        <label>Patología
            <select name="abr[<?= $lado ?>][type]" class="abr-type-select" data-lado="<?= $lado ?>">
                <?php foreach (CaseBuilder::ABR_TYPE_OPTIONS as $opt): ?>
                <option value="<?= $opt ?>" <?= ($v['abr'][$lado]['type'] ?? 'normal') === $opt ? 'selected' : '' ?>><?= ucfirst($opt) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label style="align-self:end;">
            <button type="button" class="secondary abr-autofill-btn" data-lado="<?= $lado ?>">Autocompletar según patología</button>
        </label>
        <label>Umbral (dB)
            <input type="number" name="abr[<?= $lado ?>][umbral]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['umbral'] ?? '20')) ?>">
        </label>
        <label class="inline-check" style="align-self:end;">
            <input type="checkbox" name="abr[<?= $lado ?>][repro]" <?= ($v['abr'][$lado]['repro'] ?? '1') === '1' ? 'checked' : '' ?>>
            Reproducible
        </label>
        <label>Jitter si no reproducible (ms)
            <input type="number" step="0.01" min="0" name="abr[<?= $lado ?>][repro_var]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['repro_var'] ?? '0.2')) ?>">
        </label>
        <label>Inquietud durante la captura (0-1)
            <input type="number" step="0.1" min="0" max="1" name="abr[<?= $lado ?>][inquietud]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['inquietud'] ?? '0')) ?>">
        </label>
        <label>Reflejo post-auricular PAM (0-1)
            <input type="number" step="0.1" min="0" max="1" name="abr[<?= $lado ?>][pam]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['pam'] ?? '0')) ?>">
        </label>
    </div>
    <p class="legend help">Inquietud: 0 es un paciente quieto. Por encima de 0 la captura tiene tramos en que el paciente se mueve: el EEG crudo se ensucia, el equipo descarta esos barridos y el promedio se queda quieto hasta que se calma (el contador de aceptados se separa del de presentados). Si el alumno apagó el rechazo de artefacto, en cambio, esa basura entra al promedio y el FSP no cruza nunca.</p>
    <p class="legend help">PAM: contracción del músculo auricular posterior ante sonido fuerte. Aparece sobre 60 dB, crece con el nivel y sale a los 13 ms, o sea fuera del complejo I-V y casi fuera de la ventana de rutina. Ojo que es el contraejemplo de la falsa onda V: se promedia como una respuesta, así que replica en A y B -- lo delatan la latencia, el tamaño (µV, no décimas) y que se va si el paciente relaja el cuello o se sube el pasa-alto.</p>
    <p class="legend help">El patrón retrococlear (I-III, III-V, bloqueo, razón V/I, microfónico, desincronía, sensibilidad a la tasa) se configura ahora en la pestaña <strong>Perfil auditivo</strong>, junto al resto del sitio de la lesión: los mismos parámetros gobiernan lo que se ve en el ABR y lo que NO se ve en la OEA, así que vivían mal acá adentro.</p>
    <p class="legend">Promediaciones que el caso realmente necesita para que la onda se vea resuelta (independiente de cuántas pida el alumno en el equipo) -- si el alumno detiene la captura antes de llegar a este número, la curva queda parcialmente sin resolver.</p>
    <div class="three-col">
        <label>Promediaciones objetivo
            <input type="number" step="1" min="1" name="abr[<?= $lado ?>][average_objetivo]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['average_objetivo'] ?? '2000')) ?>">
        </label>
    </div>
    <p class="legend">Valor de la onda a 80 dB (ms de latencia, µV de amplitud) -- precargado con el normativo de la población/autor elegidos arriba, edítelo para fijar el valor real del paciente. El generador calcula solo el resto de la serie de intensidades a partir de este punto.</p>
    <div class="three-col">
        <?php
        $abrWaveFields = [
            ['I', 'lat', 'Onda I -- latencia'], ['III', 'lat', 'Onda III -- latencia'], ['V', 'lat', 'Onda V -- latencia'],
            ['I', 'amp', 'Onda I -- amplitud'], ['III', 'amp', 'Onda III -- amplitud'], ['V', 'amp', 'Onda V -- amplitud'],
        ];
        foreach ($abrWaveFields as [$abrWave, $abrField, $abrLabel]):
            $abrName = $abrField . '_' . $abrWave;
        ?>
        <label><?= $abrLabel ?>
            <input type="number" step="0.01" class="abr-abs-input" data-lado="<?= $lado ?>" data-wave="<?= $abrWave ?>" data-field="<?= $abrField ?>">
        </label>
        <input type="hidden" name="abr[<?= $lado ?>][<?= $abrName ?>]" class="abr-delta-input" data-lado="<?= $lado ?>" data-wave="<?= $abrWave ?>" data-field="<?= $abrField ?>" value="<?= htmlspecialchars((string) ($v['abr'][$lado][$abrName] ?? '0')) ?>">
        <?php endforeach; ?>
    </div>
    <p class="legend">Falsa onda V. Pico con forma de onda que aparece en UNA sola mitad de los barridos: el promedio lo muestra y los subpromedios A/B lo delatan (uno lo tiene entero, el otro no). No sube el FSP. Acotala a las intensidades donde el alumno busca el umbral: fuera de ese rango la serie queda limpia y se nota que la falsa onda no migra en latencia como una V real. Amplitud 0 = desactivada; el autocompletar por patologia no la toca, es un ejercicio que se arma a mano.</p>
    <div class="three-col">
        <label>Falsa V: amplitud en el promedio (µV)
            <input type="number" step="0.01" min="0" name="abr[<?= $lado ?>][falsa_v_amp]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['falsa_v_amp'] ?? '0')) ?>">
        </label>
        <label>Falsa V: latencia (ms)
            <input type="number" step="0.1" min="0" name="abr[<?= $lado ?>][falsa_v_lat]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['falsa_v_lat'] ?? '5.6')) ?>">
        </label>
        <label>Falsa V: desde (dB)
            <input type="number" step="5" min="0" name="abr[<?= $lado ?>][falsa_v_int_min]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['falsa_v_int_min'] ?? '0')) ?>">
        </label>
        <label>Falsa V: hasta (dB)
            <input type="number" step="5" min="0" name="abr[<?= $lado ?>][falsa_v_int_max]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['falsa_v_int_max'] ?? '120')) ?>">
        </label>
        <label>Falsa V: mitad afectada
            <?php $fvMitad = (string) ($v['abr'][$lado]['falsa_v_mitad'] ?? 'auto'); ?>
            <select name="abr[<?= $lado ?>][falsa_v_mitad]">
                <?php foreach (['auto' => 'Al azar', 'a' => 'Subpromedio A', 'b' => 'Subpromedio B'] as $fvKey => $fvLabel): ?>
                <option value="<?= $fvKey ?>" <?= $fvMitad === $fvKey ? 'selected' : '' ?>><?= $fvLabel ?></option>
                <?php endforeach; ?>
            </select>
        </label>
    </div>
    <p class="legend">FSP (Fsp progresivo, referencia de la curva)</p>
    <div class="three-col">
        <label>FSP @ 800 prom.
            <input type="number" step="0.01" name="abr[<?= $lado ?>][fsp_800]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['fsp_800'] ?? '2.3')) ?>">
        </label>
        <label>FSP @ 2000 prom.
            <input type="number" step="0.01" name="abr[<?= $lado ?>][fsp_2000]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['fsp_2000'] ?? '2.8')) ?>">
        </label>
        <label>FSP objetivo
            <input type="number" step="0.01" name="abr[<?= $lado ?>][fsp_obj]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['fsp_obj'] ?? '3.0')) ?>">
        </label>
    </div>
</div>
<?php endforeach; ?>
</div>
<div class="card">
    <strong>Vista previa: serie 100&rarr;0 dBnHL</strong>
    <p class="legend help">Simulación simplificada (sin ruido ni promediación) de cómo se vería la serie de intensidades para este oído, según la patología y las desviaciones cargadas arriba. Se redibuja sola, en vivo, al tipear. Los marcadores verticales señalan dónde queda cada onda y la línea punteada sigue el pico a través de las intensidades (función latencia-intensidad). Es referencia visual para el docente: el generador real, con ruido, FSP y promediación, es el que corre en el equipo del alumno.</p>
    <div class="two-col">
        <div>
            <strong style="color:#b33a3a;">OD</strong>
            <div id="abr-preview-od" class="abr-preview"></div>
        </div>
        <div>
            <strong style="color:#2255aa;">OI</strong>
            <div id="abr-preview-oi" class="abr-preview"></div>
        </div>
    </div>
</div>
</div>

<div class="tab-panel" data-tab="eoas">
<div class="two-col">
<?php foreach (['od' => 'OD', 'oi' => 'OI'] as $lado => $ladoLabel): ?>
<div class="card">
    <strong>EOA <?= $ladoLabel ?></strong>
    <p class="legend help">Patología de este oído para el generador de Emisiones Otoacústicas (TEOAE/DPOAE/SOAE/SFOAE). "Coclear" y "Transmisión" atenúan la OEA según el umbral (a mayor umbral, más atenuada -- por sobre ~35-40 dB suele quedar bajo el noise floor, REFER). "Neural" deja la OEA normal aunque el umbral esté elevado: la cóclea está intacta, es el contraste clínico con ABR.</p>
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
        <label>Grado a sortear
            <select name="eoas_grade[<?= $lado ?>]" class="eoas-grade-select" data-lado="<?= $lado ?>">
                <option value="random">Aleatorio (sortea grado)</option>
            </select>
        </label>
    </div>
    <div class="three-col">
        <label style="align-self:end;">&nbsp;
            <button type="button" class="secondary eoas-autofill-btn" data-lado="<?= $lado ?>">Autocompletar según patología</button>
        </label>
    </div>
    <p class="legend help">"Autocompletar" sortea un caso plausible del grado elegido: umbral, perfil por frecuencia y condiciones de registro (ruido, sello, variabilidad). Las opciones de grado cambian según la patología -- en coclear van de leve (OEA presente pero reducida) a severa (ausente). Es un punto de partida al azar, no un valor fijo: se puede editar cualquier campo después. El grado NO se guarda en el caso, solo los números que deja escritos.</p>
    <p class="legend">Condiciones de registro de este oído -- lo que hace que dos pacientes con la misma cóclea no den la misma pantalla.</p>
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
    <p class="legend help">"Atenuación extra" se suma a la que ya calcula la patología (útil para forzar un REFER limpio sin tocar el umbral). "Ruido del paciente" sube el piso de ruido de la captura: un lactante despierto o un adulto que traga deja el DP-grama tapado en graves y baja la reproducibilidad TEOAE, aunque la cóclea esté sana -- es el error de interpretación clásico. "Sello de sonda" es a qué % converge el probe fit (bajo = estímulo débil y captura inestable). "Variabilidad biológica" es la estructura fina: 0 da una curva de libro, 3-4 dB da un registro real.</p>
    <p class="legend">Emisiones espontáneas (SOAE) de este oído -- el tab SOAE del emisor registra en silencio y busca picos sobre el piso de ruido.</p>
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
    <p class="legend help">"Auto" deja que el cliente sortee si este oído tiene SOAE (~45%, algo más en OD) -- estable para el mismo caso, pero no se puede saber de antemano. Para mostrarlas en clase o evaluar sobre un hallazgo fijo usá "Presentes" y cargá los picos: frecuencia en Hz y nivel de la emisión (los SOAE reales rondan 0 dB SPL, rara vez pasan 20; en blanco toma <?= CaseBuilder::EOAS_SOAE_DEFAULT_PEAK_DB ?> dB SPL). "Presentes" sin picos cargados = el cliente los sortea pero garantiza al menos uno. Los picos cargados NO se atenúan por patología ni por sello: el nivel que pongas es el que se va a ver, aunque el ruido del paciente igual puede taparlos. "Ausentes" fuerza un registro sin SOAE (lo normal en coclear/transmisión, y también posible en un oído sano).</p>
    <p class="legend">Perfil por frecuencia -- dB de caída respecto de lo esperado (positivo = OEA más chica). Se aplica a las cuatro pruebas: bandas TEOAE, puntos del DP-grama, curva de sintonía SFOAE y los picos SOAE sorteados.</p>
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
    <p class="legend help">Simulación simplificada (sin ruido por barrido ni promediación) de lo que va a ver el alumno con esta configuración. Arriba el nivel DP por f2 contra el área normal y el piso de ruido; abajo el SNR por banda TEOAE con la línea de criterio (6 dB): banda bajo la línea = REFER. El generador real corre en el cliente, ver <code>src/oae/generators/</code>.</p>
    <div class="two-col">
        <div>
            <strong style="color:#b33a3a;">OD</strong>
            <div id="eoa-preview-od" class="eoa-preview"></div>
        </div>
        <div>
            <strong style="color:#2255aa;">OI</strong>
            <div id="eoa-preview-oi" class="eoa-preview"></div>
        </div>
    </div>
</div>
</div>

<div class="tab-panel" data-tab="vemp">
<div class="two-col">
<?php foreach (['od' => 'OD', 'oi' => 'OI'] as $lado => $ladoLabel): ?>
<?php $vSubtipo = (string) ($v['vemp'][$lado]['subtipo'] ?? 'CVEMP'); ?>
<div class="card">
    <strong>VEMP <?= $ladoLabel ?></strong>
    <p class="legend help">Patología vestibular de este oído para el generador de VEMP. El subtipo define el músculo donde se mide y por lo tanto los picos que el alumno va a marcar (CVEMP cervical: P13/N23 sobre SCM; OVEMP ocular: N10/P16 sobre oblicuo inferior; MVEMP masetero: P13/N23 sobre masetero). Los 4 picos se rinden siempre; el cliente usa solo los del subtipo activo.</p>
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
    <p class="legend">Desviaciones por pico (latencia ms / amplitud µV) -- valores absolutos que el generador espera a 80 dB. Los picos irrelevantes para el subtipo activo se guardan igual pero el cliente los ignora.</p>
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

<div class="tab-panel" data-tab="anamnesis">
<div class="card">
    <strong>Redactar la anamnesis con IA</strong>
    <p class="legend help">Escribe los antecedentes que EXPLICAN los hallazgos que ya cargaste: una muesca en 4 kHz pide exposición a ruido, una conductiva con timpanograma B pide otitis a repetición, una neuropatía en un recién nacido pide hiperbilirrubinemia. No inventa el diagnóstico ni menciona umbrales -- eso lo tiene que medir el alumno.</p>
    <p class="legend help">Escribe el relato (motivo de consulta, hace cuánto, en qué situaciones molesta) en <strong>Historia clínica</strong>, que está en la pestaña Paciente, y acá los antecedentes, medicamentos, cirugías, comportamiento y sensibilidad.</p>
    <p class="legend help"><strong>Es un borrador y hay que leerlo.</strong> El modelo puede inventar una cirugía que no existe o un fármaco que no es ototóxico, y eso le llega al alumno como parte del caso, indistinguible de lo que escribiste vos. Hasta que tildes la verificación, el caso no se guarda ni se puede citar.</p>
    <button type="button" class="secondary" id="anamnesis-ia-btn">Redactar borrador con IA</button>
    <span id="anamnesis-ia-estado" class="legend"></span>

    <input type="hidden" name="anamnesis_ia[generado]" id="anamnesis-ia-generado" value="<?= fv($v, ['anamnesis_ia', 'generado'], '') ? '1' : '' ?>">
    <input type="hidden" name="anamnesis_ia[generado_en]" id="anamnesis-ia-generado-en" value="<?= htmlspecialchars((string) fv($v, ['anamnesis_ia', 'generado_en'], '')) ?>">

    <div id="anamnesis-ia-verificacion" <?= fv($v, ['anamnesis_ia', 'generado'], '') ? '' : 'hidden' ?> style="border-left:4px solid #b00; padding-left:0.6rem; margin-top:0.6rem;">
        <label class="inline-check">
            <input type="checkbox" name="anamnesis_ia[verificado]" id="anamnesis-ia-verificado" value="1" <?= fv($v, ['anamnesis_ia', 'verificado'], '') ? 'checked' : '' ?>>
            Leí el borrador y verifico que es clínicamente correcto para este caso
        </label>
        <?php if (fv($v, ['anamnesis_ia', 'verificado_por'], '')): ?>
        <p class="legend help">Verificado por <?= htmlspecialchars((string) fv($v, ['anamnesis_ia', 'verificado_por'], '')) ?><?= fv($v, ['anamnesis_ia', 'verificado_en'], '') ? ' el ' . htmlspecialchars((string) fv($v, ['anamnesis_ia', 'verificado_en'], '')) : '' ?>.</p>
        <?php endif; ?>
        <p class="legend help">Volver a generar borra la verificación: el texto nuevo no lo leyó nadie.</p>
    </div>
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
    <label>Lo que el paciente cuenta de sí mismo
        <textarea name="otros" rows="5" class="input" placeholder="En qué trabaja, cómo es su día, qué hace en su tiempo libre, desde cuándo lo nota, en qué situaciones le molesta más, qué le preocupa, qué ya probó..."><?= htmlspecialchars((string) ($v['otros'] ?? '')) ?></textarea>
    </label>
    <p class="legend">Su vida, su trabajo, su rutina, desde cuándo lo nota, en qué situaciones le molesta, qué le preocupa, qué ya probó. De acá sale <strong>todo lo que el paciente tiene para responder</strong> cuando el alumno lo entrevista: vacío contesta en monosílabos y no hay nada que preguntarle. No es la historia clínica (esa la lee el alumno en la ficha) ni la lista de antecedentes de arriba: es lo que esta persona cuenta si se lo preguntan.</p>
    <label>Comportamiento del paciente
        <textarea name="comportamiento" id="chat-comportamiento" rows="2" class="input" placeholder="Ej: nervioso, minimiza los síntomas, muy hablador, desconfiado, colaborador..."><?= htmlspecialchars((string) ($v['comportamiento'] ?? '')) ?></textarea>
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
    <div id="chat-test-log" style="border:1px solid var(--color-border); border-radius:var(--radius-lg); padding:0.7rem; min-height:3rem; max-height:22rem; overflow-y:auto; margin:0.6rem 0; background:var(--color-row-alt); font-size:0.88rem;"></div>
    <div style="display:flex; gap:0.5rem;">
        <input type="text" id="chat-test-input" placeholder="Escribe como si fueras el alumno..." style="flex:1; padding:0.45rem; border:1px solid var(--color-border-strong); border-radius:var(--radius-md);">
        <button type="button" id="chat-test-send" class="secondary" style="margin-top:0;">Enviar</button>
        <button type="button" id="chat-test-reset" class="secondary" style="margin-top:0;">Reiniciar conversación</button>
    </div>
    <div class="section-sep" style="border-top:1px dashed var(--color-border);">
        <button type="button" id="oirs-test-btn" class="secondary" style="margin-top:0;">Simular término de sesión (ver veredicto OIRS)</button>
        <p class="legend">Corre el evaluador de <a href="llm.php" target="_blank">Admin → IA Paciente</a> sobre esta conversación de prueba, tal como se ejecutaría al cerrar una atención real -- útil para ajustar el prompt del evaluador o la sensibilidad del paciente.</p>
        <div id="oirs-test-result"></div>
    </div>
</div>
</div>

<?php if (!empty($avisosPerfil)): ?>
<div class="card" style="border-left:4px solid #7a5b00;">
    <label class="inline-check">
        <input type="checkbox" name="perfil_confirmar" value="1">
        La incoherencia es intencional: guardar igual
    </label>
</div>
<?php endif; ?>

<?php if ($isEdit): ?>
<div class="form-actions-sticky">
    <button type="submit" name="form_action" value="update_case">Guardar cambios</button>
    <a href="patients.php" style="font-size:0.85rem; text-decoration:none;">Cancelar</a>
</div>
<?php else: ?>
<div class="form-actions-sticky">
    <button type="submit" name="form_action" value="create_case">Crear caso</button>
    <a href="patients.php" style="font-size:0.85rem; text-decoration:none;">Cancelar</a>
</div>
<?php endif; ?>
</form>

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
<div id="otoscopia-crop-modal" class="photo-modal" hidden>
    <div class="photo-modal-box">
        <strong style="display:block; margin-bottom:0.6rem;">Recortar foto de otoscopia</strong>
        <div class="photo-crop-viewport" id="otoscopia-crop-viewport">
            <img id="otoscopia-crop-img" alt="">
            <div class="photo-crop-ring square"></div>
        </div>
        <input type="range" id="otoscopia-crop-zoom" min="1" max="4" step="0.01" value="1" style="width:100%; margin-top:0.8rem;">
        <p class="legend" style="text-align:center;">Arrastra para mover, usa el control para acercar/alejar.</p>
        <div class="photo-modal-actions">
            <button type="button" id="otoscopia-crop-cancel" class="secondary">Cancelar</button>
            <button type="button" id="otoscopia-crop-confirm">Guardar foto</button>
        </div>
    </div>
</div>
<script>
// Fecha de nacimiento y RUT del paciente: no se tipean a mano -- se derivan
// de la edad (mismo criterio que CaseBuilder::rutFromAge/randomFechaNacForAge
// del lado servidor, que es el fallback si JS está deshabilitado). Cada vez
// que cambia la edad se recalculan: año de nacimiento = año actual - edad,
// día/mes al azar dentro de ese año. La fecha queda readonly; el RUT sigue
// editable a mano por si el docente quiere ajustarlo después del cálculo.
(function () {
    var ageInput = document.getElementById('patient-age');
    var fechaInput = document.getElementById('patient-fecha-nac');
    var rutInput = document.getElementById('patient-rut');
    if (!ageInput || !fechaInput || !rutInput) { return; }

    // Misma regresión lineal fija que CaseBuilder::rutFromAge (helpers.py
    // rut_from_age) -- no inventar otra, tiene que dar edades consistentes
    // con get_age_from_rut del lado cliente.
    var RUT_SLOPE = 3.3363697569700348e-06;
    var RUT_INTERCEPT = 1932.2573852507373;
    var lastAge = null;

    function pad2(n) { return n < 10 ? '0' + n : '' + n; }

    function recompute() {
        var age = parseInt(ageInput.value, 10);
        if (!age || age < 0 || age === lastAge) { return; }
        lastAge = age;

        var currentYear = new Date().getFullYear();
        var birthYear = currentYear - age;
        var randomDayOffset = Math.floor(Math.random() * 365);
        var birthDate = new Date(birthYear, 0, 1 + randomDayOffset);
        fechaInput.value = birthDate.getFullYear() + '-' + pad2(birthDate.getMonth() + 1) + '-' + pad2(birthDate.getDate());

        var birthDateFloat = birthYear + (randomDayOffset / 365);
        var rutApprox = Math.trunc((birthDateFloat - RUT_INTERCEPT) / RUT_SLOPE);
        rutInput.value = String(rutApprox);
    }

    ageInput.addEventListener('input', recompute);
    ageInput.addEventListener('change', recompute);
})();
</script>

<script>
// Borrador de anamnesis por LLM.
//
// Trae el texto y lo deja en los campos, pero NO lo da por bueno: enciende
// la casilla de verificación y la deja sin tildar. Mientras siga así, el
// servidor no guarda el caso ni la agenda lo cita (CaseCompleteness). El
// modelo puede inventar una cirugía que no existe, y al alumno le llega
// indistinguible de lo que escribió el docente.
(function () {
    var CSRF = <?= json_encode(Auth::csrfToken()) ?>;
    var HIST = <?= json_encode(CaseBuilder::HIST_CHECKBOXES) ?>;
    var FREQS = <?= json_encode(CaseBuilder::FREQUENCIES) ?>;
    var NEURAL_PARAMS = <?= json_encode(array_keys(CaseBuilder::ABR_NEURAL_DEFAULTS)) ?>;

    var boton = document.getElementById('anamnesis-ia-btn');
    var estado = document.getElementById('anamnesis-ia-estado');
    var bloque = document.getElementById('anamnesis-ia-verificacion');
    var generado = document.getElementById('anamnesis-ia-generado');
    var generadoEn = document.getElementById('anamnesis-ia-generado-en');
    var verificado = document.getElementById('anamnesis-ia-verificado');
    if (!boton || !bloque || !generado || !verificado) return;

    function campo(name) { return document.querySelector('#case-form [name="' + name + '"]'); }
    function curva(clave, lado) {
        var out = [];
        for (var n = 0; n < FREQS.length; n++) {
            var el = document.getElementById(clave + '_' + lado + '_' + n);
            out.push(el ? (parseInt(el.value, 10) || 0) : 0);
        }
        return out;
    }

    /** Solo los hallazgos: el prompt no ve el resto de la ficha. */
    function estadoClinico() {
        var perfil = {};
        ['od', 'oi'].forEach(function (lado) {
            var cce = campo('perfil[' + lado + '][cce_pct]');
            var retro = {};
            NEURAL_PARAMS.forEach(function (param) {
                var el = document.querySelector('.abr-neural-input[data-lado="' + lado + '"][data-param="' + param + '"]');
                if (el) { retro[param] = el.value; }
            });
            perfil[lado] = { cce_pct: cce ? cce.value : 100, retro: retro };
        });
        var edad = campo('age'), genero = document.querySelector('#case-form [name="gender"]:checked');
        var zOd = campo('z_od'), zOi = campo('z_oi');
        var tinnitus = {};
        ['lateralidad', 'oido', 'predominio', 'ruido'].forEach(function (k) {
            var el = campo('tinnitus[' + k + ']');
            if (el) { tinnitus[k] = el.value; }
        });
        ['pulsatil', 'permanente'].forEach(function (k) {
            var el = campo('tinnitus[' + k + ']');
            if (el && el.checked) { tinnitus[k] = true; }
        });
        return {
            case_id: (campo('case_id') || {}).value || '',
            edad: edad ? parseInt(edad.value, 10) || 0 : 0,
            gender: genero ? parseInt(genero.value, 10) || 0 : 0,
            aerea: { od: curva('aerea', 'od'), oi: curva('aerea', 'oi') },
            osea: { od: curva('osea', 'od'), oi: curva('osea', 'oi') },
            z: { od: zOd ? zOd.value : 'A', oi: zOi ? zOi.value : 'A' },
            perfil: perfil,
            tinnitus: tinnitus
        };
    }

    function aplicar(b) {
        // El relato va a la pestaña Paciente, no a Anamnesis: es historia
        // del paciente, no del caso. Es además el campo que hace útil al
        // borrador -- sin él, un paciente sin antecedentes formales
        // quedaba con la ficha vacía.
        var relato = campo('historia_clinica');
        if (relato && b.historia_clinica) { relato.value = b.historia_clinica; }
        HIST.forEach(function (clave) {
            var chk = campo('hist[' + clave + ']');
            if (chk) { chk.checked = !!b.antecedentes[clave]; }
        });
        ['medicamentos', 'cirugias', 'otros', 'comportamiento'].forEach(function (k) {
            var el = campo(k);
            if (el) { el.value = b[k] || ''; }
        });
        var disp = campo('disposicion');
        if (disp) { disp.value = b.disposicion; }
    }

    boton.addEventListener('click', function () {
        boton.disabled = true;
        // Puede tardar: un modelo de razonamiento genera miles de tokens
        // antes de escribir, y si se queda corto el servidor reintenta.
        estado.textContent = 'Redactando... (puede tardar un minuto o dos)';
        var body = new URLSearchParams();
        body.set('csrf_token', CSRF);
        body.set('payload', JSON.stringify(estadoClinico()));
        fetch('case_anamnesis_ai.php', { method: 'POST', body: body })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.ok) { throw new Error(data.error || 'No se pudo redactar.'); }
                aplicar(data.borrador);
                generado.value = '1';
                if (generadoEn) { generadoEn.value = new Date().toISOString(); }
                // Texto nuevo: nadie lo leyó todavía.
                verificado.checked = false;
                bloque.hidden = false;
                // El consumo a la vista: en un modelo de razonamiento el
                // grueso son tokens de pensamiento que no se ven en el
                // texto, y sin esto no hay forma de notar que un borrador
                // costó veinte veces más que otro.
                var u = data.uso || {};
                var costo = u.total
                    ? ' — ' + u.total + ' tokens'
                        + (u.razonamiento ? ' (' + u.razonamiento + ' de razonamiento)' : '')
                        + (u.intentos > 1 ? ', ' + u.intentos + ' intentos' : '')
                    : '';
                estado.textContent = 'Borrador listo. Leelo y verificalo antes de guardar'
                    + ' (el relato quedó en la pestaña Paciente).' + costo;
            })
            .catch(function (err) { estado.textContent = 'Error: ' + err.message; })
            .finally(function () { boton.disabled = false; });
    });
})();
</script>

<script>
// No salir de la edición con cambios sin guardar.
//
// El bloqueo de datos faltantes vive en el servidor (CaseCompleteness), y
// solo puede actuar cuando el docente aprieta Guardar. Lo que se escapaba
// era el otro camino: tocar el caso, irse por "Cancelar" o cerrar la
// pestaña, y dejarlo a medias sin que nadie lo mire nunca más.
(function () {
    var form = document.getElementById('case-form');
    if (!form) return;
    var sucio = false;
    var guardando = false;

    form.addEventListener('input', function () { sucio = true; });
    form.addEventListener('change', function () { sucio = true; });
    form.addEventListener('submit', function () { guardando = true; });

    window.addEventListener('beforeunload', function (e) {
        if (!sucio || guardando) return;
        // El texto lo pone el navegador; lo que importa es preventDefault.
        e.preventDefault();
        e.returnValue = '';
    });

    // "Cancelar" es un <a>, no dispara submit: se pregunta a mano para
    // poder decir de qué se trata en vez del texto genérico del navegador.
    document.addEventListener('click', function (e) {
        var link = e.target.closest ? e.target.closest('a[href$="patients.php"]') : null;
        if (!link || !sucio) return;
        if (!window.confirm('Hay cambios sin guardar en este caso. Si salís ahora se pierden.')) {
            e.preventDefault();
        } else {
            guardando = true;   // evita la segunda pregunta del navegador
        }
    });
})();
</script>

<script>
// Campos que pasan a escribirse solos cuando su módulo está derivado.
//
// Sin esto el docente edita un campo que el servidor va a pisar al guardar,
// y no hay forma de saberlo mirando la pantalla. Los patrones son prefijos
// del atributo name; solo se listan los campos que la proyección REESCRIBE
// (el ruido del paciente o el sello de la sonda, por ejemplo, siguen siendo
// del docente aunque la OEA esté derivada).
(function () {
    var CAMPOS = {
        abr: ['abr[od][type]', 'abr[oi][type]', 'abr[od][umbral]', 'abr[oi][umbral]'],
        eoas: ['eoas[od][type]', 'eoas[oi][type]', 'eoas[od][umbral]', 'eoas[oi][umbral]',
               'eoas[od][desv]', 'eoas[oi][desv]'],
        reflex: ['reflex_ipsi[', 'reflex_contra[', 'reflex_type['],
        recruit: ['sisi[', 'recruit[', 'fowler_pattern[', 'carhart[', 'stat[', 'rosemberg[',
                  'ldl[', 'ldl_habilitado['],
        logo: ['umd_int[', 'umd_pct[']
    };

    function elementos(prefijos) {
        var out = [];
        var todos = document.querySelectorAll('#case-form [name]');
        for (var i = 0; i < todos.length; i++) {
            var name = todos[i].getAttribute('name');
            for (var p = 0; p < prefijos.length; p++) {
                if (name.indexOf(prefijos[p]) === 0) { out.push(todos[i]); break; }
            }
        }
        return out;
    }

    function aplicar(modulo) {
        var chk = document.querySelector('input[name="perfil[auto][' + modulo + ']"]');
        if (!chk) return;
        elementos(CAMPOS[modulo]).forEach(function (el) {
            // readOnly en los number (siguen viajando en el POST y se ven);
            // disabled en select/checkbox, que no lo soportan. No importa
            // que no lleguen: con el módulo derivado el servidor los pisa.
            if (el.tagName === 'SELECT' || el.type === 'checkbox') {
                el.disabled = chk.checked;
            } else {
                el.readOnly = chk.checked;
            }
            el.style.opacity = chk.checked ? '0.6' : '';
            el.title = chk.checked ? 'Derivado del perfil auditivo -- se reescribe al guardar' : '';
        });
    }

    Object.keys(CAMPOS).forEach(function (modulo) {
        var chk = document.querySelector('input[name="perfil[auto][' + modulo + ']"]');
        if (chk) { chk.addEventListener('change', function () { aplicar(modulo); }); }
        aplicar(modulo);
    });
})();
</script>

<script>
// Sorteo del perfil: escribe el audiograma, el sitio de la lesión y el
// patrón retro de un cuadro clínico completo, coherentes entre sí.
//
// Reemplaza el uso que se le daba a los dos "Autocompletar" para fijar
// umbral y patología -- cada uno sorteaba por su lado y podían dejar el ABR
// coclear y la OEA neural en el mismo oído. Los escenarios se serializan
// desde CaseProfile::SCENARIOS, no se re-tipean acá.
(function () {
    var ESCENARIOS = <?= json_encode(CaseProfile::SCENARIOS, JSON_UNESCAPED_UNICODE) ?>;
    var FREQS = <?= json_encode(CaseBuilder::FREQUENCIES) ?>;
    var JITTER_DB = 4;   // ruido por frecuencia: ningún audiograma real es liso

    var boton = document.getElementById('perfil-sortear');
    var selector = document.getElementById('perfil-escenario');
    if (!boton || !selector) return;

    function entre(a, b) { return a + Math.random() * (b - a); }
    function aCinco(x) { return Math.max(0, Math.min(120, Math.round(x / 5) * 5)); }

    function escribir(clave, lado, valores) {
        for (var n = 0; n < FREQS.length; n++) {
            var el = document.getElementById(clave + '_' + lado + '_' + n);
            if (el) { el.value = valores[n]; }
        }
    }

    /** Curva de un oído a partir de la forma del cuadro, con escala y jitter. */
    function curvaDeForma(forma, escala) {
        return FREQS.map(function (hz) {
            var base = (forma && forma[hz] !== undefined) ? forma[hz] : 0;
            return base * escala + entre(-JITTER_DB, JITTER_DB);
        });
    }

    function sortearLado(esc, lado, afectado, escalas, asimetria) {
        // El oído sano de un cuadro unilateral no es "cero": es un oído
        // normal, con su propia variabilidad.
        var formaSn = afectado ? esc.sn_shape : ESCENARIOS.normal.sn_shape;
        var escalaSn = afectado ? escalas.sn : entre(0, 0.8);
        var sn = curvaDeForma(formaSn, escalaSn).map(function (v) { return v + asimetria; });
        var gap = afectado && esc.gap_shape && Object.keys(esc.gap_shape).length
            ? curvaDeForma(esc.gap_shape, escalas.gap)
            : FREQS.map(function () { return 0; });

        var osea = sn.map(aCinco);
        var aerea = sn.map(function (v, i) { return aCinco(v + Math.max(0, gap[i])); });
        // La ósea nunca puede quedar peor que la aérea después de redondear.
        osea = osea.map(function (v, i) { return Math.min(v, aerea[i]); });
        escribir('aerea', lado, aerea);
        escribir('osea', lado, osea);
        // "Igualar ósea a aérea" pisaría la ósea recién sorteada al guardar.
        var igualar = document.querySelector('.igualar-toggle[data-side="' + lado + '"]');
        if (igualar && igualar.checked && gap.some(function (g) { return g > 0; })) {
            igualar.checked = false;
        }

        // Oído medio: el gap y el timpanograma tienen que contar la misma
        // historia. Sin esto el cuadro "Conductiva" salía con 35 dB de gap
        // y curva A, o sea con la contradicción adentro desde el sorteo.
        var z = document.getElementById('z_' + lado);
        if (z) {
            var opciones = afectado && esc.z && esc.z.length ? esc.z : ['A'];
            z.value = opciones[Math.floor(Math.random() * opciones.length)];
        }
        var etf = document.querySelector('select[name="etf_' + lado + '"]');
        if (etf) { etf.value = afectado && esc.etf ? esc.etf : 'Normal'; }

        var cce = document.querySelector('input[name="perfil[' + lado + '][cce_pct]"]');
        if (cce) {
            cce.value = afectado
                ? Math.round(entre(esc.cce_pct[0], esc.cce_pct[1]) / 5) * 5
                : 100;
        }

        // Patrón retrococlear: solo en el oído afectado. El preset precarga
        // los valores y después se editan (nunca se persiste su nombre).
        var sel = document.querySelector('.abr-neural-preset-select[data-lado="' + lado + '"]');
        var btn = document.querySelector('.abr-neural-preset-btn[data-lado="' + lado + '"]');
        if (sel && btn && afectado && esc.retro) {
            sel.value = esc.retro;
            btn.click();
        }
    }

    boton.addEventListener('click', function () {
        var claves = Object.keys(ESCENARIOS);
        var clave = selector.value === '__random__'
            ? claves[Math.floor(Math.random() * claves.length)]
            : selector.value;
        var esc = ESCENARIOS[clave];
        if (!esc) return;
        if (selector.value === '__random__') { selector.value = clave; }

        var unilateral = esc.lateralidad === 'unilateral';
        var afectado = Math.random() < 0.5 ? 'od' : 'oi';
        // La escala se sortea UNA vez para todo el paciente, no una por
        // oído: con una escala por lado, una presbiacusia bilateral podía
        // salir con 27 dB en un oído y 67 en el otro, o sea una asimetría
        // enorme --que es un hallazgo, no ruido-- en un cuadro que se
        // define por ser simétrico.
        var escalas = {
            sn: entre(esc.sn_scale[0], esc.sn_scale[1]),
            gap: entre(esc.gap_scale[0], esc.gap_scale[1])
        };
        // La asimetría interaural que SÍ corresponde: unos pocos dB en un
        // oído al azar. En los cuadros unilaterales la asimetría real la da
        // el oído sano, así que acá no se agrega nada.
        var peor = Math.random() < 0.5 ? 'od' : 'oi';
        var asimetria = unilateral ? 0 : entre(0, 8);
        ['od', 'oi'].forEach(function (lado) {
            sortearLado(esc, lado, !unilateral || lado === afectado, escalas,
                        lado === peor ? asimetria : 0);
        });

        // Un caso sorteado nace coherente: las proyecciones se encienden.
        <?= json_encode(CaseProfile::AUTO_MODULES) ?>.forEach(function (modulo) {
            var chk = document.querySelector('input[name="perfil[auto][' + modulo + ']"]');
            if (chk) {
                chk.checked = true;
                chk.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
        if (window.drawAudiogram) { window.drawAudiogram(); }
        if (window.drawReflexPattern) { window.drawReflexPattern(); }
        // Trae de una la proyección del caso recién sorteado: OEA, reflejos
        // y supraliminares se llenan solos, no al guardar.
        if (window.proyectarPerfil) { window.proyectarPerfil(); }
    });
})();
</script>

<script>
// Vista previa en vivo de la proyección del perfil auditivo.
//
// Las fórmulas NO se reimplementan acá: se le piden a admin/case_project.php,
// que llama al mismo CaseProfile::project() que corre al guardar. Antes esto
// era una copia en JS de la ley del ABR, y las otras tres (OEA, reflejos,
// supraliminares) directamente no se veían hasta guardar y reabrir el caso:
// el docente sorteaba un caso y la pestaña EOA seguía mostrando lo viejo.
(function () {
    var CSRF = <?= json_encode(Auth::csrfToken()) ?>;
    var FREQS = <?= json_encode(CaseBuilder::FREQUENCIES) ?>;
    var EOAS_FREQS = <?= json_encode(CaseBuilder::EOAS_FREQS) ?>;
    var NEURAL_PARAMS = <?= json_encode(array_keys(CaseBuilder::ABR_NEURAL_DEFAULTS)) ?>;
    var DECAY_MODES = <?= json_encode(array_keys(CaseProfile::DECAY_FREQ_IDX)) ?>;
    var ETIQUETAS = {
        'click': 'Click', 'ce_chirp': 'CE-chirp', 'ls_chirp': 'Ls-chirp',
        'tone_burst_500Hz': 'Burst 500 Hz', 'tone_burst_1000Hz': 'Burst 1 kHz',
        'tone_burst_2000Hz': 'Burst 2 kHz', 'tone_burst_4000Hz': 'Burst 4 kHz'
    };
    // Graves a agudos y después los de banda ancha, que es como se lee un
    // protocolo frecuencia específica.
    var ORDEN = ['tone_burst_500Hz', 'tone_burst_1000Hz', 'tone_burst_2000Hz',
                 'tone_burst_4000Hz', 'click', 'ce_chirp', 'ls_chirp'];

    var MODULOS = <?= json_encode(CaseProfile::AUTO_MODULES) ?>;
    var preview = document.getElementById('abr-threshold-preview');
    var tbody = document.getElementById('abr-threshold-rows');

    function campo(name) { return document.querySelector('#case-form [name="' + name + '"]'); }
    function autoOn(modulo) {
        var chk = campo('perfil[auto][' + modulo + ']');
        return !!(chk && chk.checked);
    }
    function curva(clave, lado) {
        var out = [];
        for (var n = 0; n < FREQS.length; n++) {
            var el = document.getElementById(clave + '_' + lado + '_' + n);
            out.push(el ? (parseInt(el.value, 10) || 0) : 0);
        }
        return out;
    }

    /** Lo que hay cargado en el formulario ahora mismo, sin guardar nada. */
    function estado() {
        var perfil = {};
        ['od', 'oi'].forEach(function (lado) {
            var cce = campo('perfil[' + lado + '][cce_pct]');
            var retro = {};
            NEURAL_PARAMS.forEach(function (param) {
                var el = document.querySelector('.abr-neural-input[data-lado="' + lado + '"][data-param="' + param + '"]');
                if (el) { retro[param] = el.value; }
            });
            perfil[lado] = { cce_pct: cce ? cce.value : 100, retro: retro };
        });
        var auto = {};
        MODULOS.forEach(function (m) { auto[m] = autoOn(m); });
        var zOd = campo('z_od'), zOi = campo('z_oi');
        return {
            aerea: { od: curva('aerea', 'od'), oi: curva('aerea', 'oi') },
            osea: { od: curva('osea', 'od'), oi: curva('osea', 'oi') },
            perfil: perfil, auto: auto,
            z: { od: zOd ? zOd.value : 'A', oi: zOi ? zOi.value : 'A' }
        };
    }

    function setVal(name, valor) {
        var el = campo(name);
        if (el && valor !== undefined && valor !== null) { el.value = valor; }
    }

    function pintarTablaAbr(abr) {
        if (!preview || !tbody) return;
        tbody.innerHTML = '';
        ORDEN.forEach(function (stim) {
            var tr = document.createElement('tr');
            var celdas = [ETIQUETAS[stim],
                abr.OD.umbral_por_estimulo[stim] + ' dB nHL',
                abr.OD.umbral_por_estimulo_oseo[stim] + ' dB nHL',
                abr.OI.umbral_por_estimulo[stim] + ' dB nHL',
                abr.OI.umbral_por_estimulo_oseo[stim] + ' dB nHL'];
            celdas.forEach(function (texto, i) {
                var td = document.createElement(i === 0 ? 'th' : 'td');
                td.textContent = texto;
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    function hidratar(p) {
        if (preview) { preview.hidden = !autoOn('abr'); }

        if (autoOn('abr')) {
            pintarTablaAbr(p.abr);
            ['od', 'oi'].forEach(function (lado) {
                var lo = lado.toUpperCase();
                setVal('abr[' + lado + '][type]', p.abr[lo].type);
                setVal('abr[' + lado + '][umbral]', p.abr[lo].umbral);
            });
        }

        if (autoOn('eoas')) {
            ['od', 'oi'].forEach(function (lado) {
                var lo = lado.toUpperCase();
                setVal('eoas[' + lado + '][type]', p.eoas[lo].type);
                setVal('eoas[' + lado + '][umbral]', p.eoas[lo].umbral);
                EOAS_FREQS.forEach(function (hz) {
                    setVal('eoas[' + lado + '][desv][' + hz + ']', p.eoas[lo].desviaciones[hz]);
                });
            });
        }

        if (autoOn('reflex')) {
            ['ipsi', 'contra'].forEach(function (modo) {
                ['od', 'oi'].forEach(function (lado) {
                    (p.reflex[modo][lado] || []).forEach(function (valor, n) {
                        setVal('reflex_' + modo + '[' + lado + '][' + n + ']', valor);
                    });
                });
            });
            ['od', 'oi'].forEach(function (lado) {
                setVal('reflex_type[' + lado + ']', p.reflex.tipo[lado]);
            });
            // La tabla-resumen de reflejos se dibuja desde los inputs.
            if (window.drawReflexPattern) { window.drawReflexPattern(); }
        }

        if (autoOn('recruit')) {
            ['od', 'oi'].forEach(function (lado, i) {
                setVal('sisi[' + lado + ']', p.recruit.sisi[i]);
                var chk = campo('recruit[' + lado + ']');
                if (chk) { chk.checked = !!p.recruit.recruit[i]; }
            });
            Object.keys(p.recruit.fowler).forEach(function (freqIdx) {
                setVal('fowler_pattern[' + freqIdx + ']', p.recruit.fowler[freqIdx]);
            });
            DECAY_MODES.forEach(function (modo) {
                ['od', 'oi'].forEach(function (lado) {
                    (p.recruit.decay[modo][lado] || []).forEach(function (valor, n) {
                        setVal(modo + '[' + lado + '][' + n + ']', valor);
                    });
                });
            });
            ['od', 'oi'].forEach(function (lado) {
                (p.recruit.ldl[lado] || []).forEach(function (valor, n) {
                    setVal('ldl[' + lado + '][' + n + ']', valor);
                });
                // Derivado, el LDL siempre está medido: dejarlo en "no
                // medido" esconde justo el hallazgo del reclutamiento.
                var medido = campo('ldl_habilitado[' + lado + ']');
                if (medido) { medido.checked = true; }
            });
            if (window.drawAudiogram) { window.drawAudiogram(); }
        }

        if (autoOn('logo')) {
            ['od', 'oi'].forEach(function (lado) {
                var lo = lado.toUpperCase();
                setVal('umd_int[' + lado + ']', p.logo[lo].int);
                setVal('umd_pct[' + lado + ']', p.logo[lo].pct);
            });
            if (window.drawLogogram) { window.drawLogogram(); }
        }
    }

    var pendiente = null;
    function proyectar() {
        // Sin ningún módulo derivado no hay nada que pintar: el formulario
        // es del docente y no se le toca ni un campo.
        if (!MODULOS.some(autoOn)) {
            if (preview) { preview.hidden = true; }
            return;
        }
        var body = new URLSearchParams();
        body.set('csrf_token', CSRF);
        body.set('payload', JSON.stringify(estado()));
        fetch('case_project.php', { method: 'POST', body: body })
            .then(function (r) { return r.json(); })
            .then(function (data) { if (data.ok) { hidratar(data.proyeccion); } })
            .catch(function () { /* sin conexión el formulario sigue usable a mano */ });
    }
    function proyectarPronto() {
        clearTimeout(pendiente);
        pendiente = setTimeout(proyectar, 350);
    }
    // El sorteo escribe el audiograma completo y necesita repintar ya.
    window.proyectarPerfil = proyectar;

    document.addEventListener('input', function (e) {
        var id = e.target.id || '';
        var name = e.target.getAttribute('name') || '';
        if (/^(aerea|osea)_/.test(id) || /^perfil\[(od|oi)\]\[cce_pct\]$/.test(name)
            || (e.target.classList && e.target.classList.contains('abr-neural-input'))) {
            proyectarPronto();
        }
    });
    document.addEventListener('change', function (e) {
        var name = e.target.getAttribute('name') || '';
        if (/^perfil\[auto\]\[/.test(name) || /^igualar\[/.test(name)
            || name === 'z_od' || name === 'z_oi'
            || (e.target.classList && e.target.classList.contains('abr-neural-input'))) {
            // Debounce también acá: el sorteo enciende las cuatro casillas
            // de un saque y no hacen falta cuatro viajes al servidor.
            proyectarPronto();
        }
    });
    proyectar();
})();
</script>

<script>
// Autocompletar ABR: sugiere desviaciones/umbral/FSP plausibles para la
// patología elegida en cada oído, usando sexo+edad del paciente para elegir
// la población de referencia y el autor elegido arriba para elegir DE QUÉ
// baseline parte esa población. Los baselines de onda I/III/V (ABR_DEFAULT)
// y los rangos por patología (threshold_range, wave_I_reduction,
// interpeak_prolongation, etc.) son los mismos que usa
// resources/abr/normative_data.json / ABR_generator -- mantener
// sincronizado a mano si esos cambian (mismo criterio que la normativa por
// curso en courses.php). ABR_AUTHOR_CATALOG sale de AppConfig
// ('abr_reference_authors', global, ver admin/normativas.php).
// Es una sugerencia al azar dentro de un rango clínicamente razonable, no un
// valor fijo -- el docente la edita después.
(function () {
    var ABR_DEFAULT_POPULATIONS = {
        adult_male:   { I: { lat: 1.65, amp: 0.30 }, III: { lat: 3.85, amp: 0.35 }, V: { lat: 5.70, amp: 0.50 } },
        adult_female: { I: { lat: 1.62, amp: 0.21 }, III: { lat: 3.68, amp: 0.37 }, V: { lat: 5.47, amp: 0.60 } },
        child:        { I: { lat: 1.58, amp: 0.28 }, III: { lat: 3.78, amp: 0.33 }, V: { lat: 5.60, amp: 0.48 } },
        neonate:      { I: { lat: 2.10, amp: 0.20 }, III: { lat: 4.70, amp: 0.24 }, V: { lat: 6.80, amp: 0.35 } },
        elderly:      { I: { lat: 1.75, amp: 0.27 }, III: { lat: 4.00, amp: 0.32 }, V: { lat: 5.90, amp: 0.45 } }
    };
    var ABR_AUTHOR_CATALOG = <?= json_encode($abrAuthorCatalog, JSON_UNESCAPED_UNICODE) ?>;

    function rand(min, max) { return min + Math.random() * (max - min); }

    function pickPopulation() {
        var ageInput = document.getElementById('patient-age');
        var age = ageInput ? parseFloat(ageInput.value) : NaN;
        if (isNaN(age)) { age = 30; }
        var genderChecked = document.querySelector('input[name="gender"]:checked');
        var isFemale = !!genderChecked && genderChecked.value === '1';
        if (age <= 0.25) { return 'neonate'; }
        if (age <= 12) { return 'child'; }
        if (age >= 60) { return 'elderly'; }
        return isFemale ? 'adult_female' : 'adult_male';
    }

    // Baseline "real" a usar para esta población: la del autor elegido,
    // completada campo a campo con el default donde el autor no definió
    // esa onda/población (autor incompleto = no obliga a cargar los 30
    // campos para poder usarlo).
    function resolveBaseline(pop) {
        var d = ABR_DEFAULT_POPULATIONS[pop];
        var authorSelect = document.getElementById('abr-author-select');
        var authorId = authorSelect ? authorSelect.value : '__default__';
        var author = ABR_AUTHOR_CATALOG[authorId];
        var authorPop = author && author.populations ? author.populations[pop] : null;
        var out = {};
        ['I', 'III', 'V'].forEach(function (wave) {
            var aw = authorPop ? authorPop[wave] : null;
            out[wave] = {
                lat: aw && aw.lat !== undefined ? aw.lat : d[wave].lat,
                amp: aw && aw.amp !== undefined ? aw.amp : d[wave].amp
            };
        });
        return { def: d, author: out };
    }

    // Cada rango viene de pathology_modifiers en normative_data.json; las
    // desviaciones de latencia son deltas en ms sobre el baseline DEL AUTOR
    // elegido (más el offset autor-vs-default, para que el cliente -que
    // siempre suma la desviación sobre SU propio default- reconstruya el
    // valor absoluto del autor). Las de amplitud son fracción del baseline
    // del autor (así el mismo % de reducción da un delta distinto en un
    // adulto que en un neonato, o entre autores).
    function buildValues(type, pop) {
        var baseline = resolveBaseline(pop);
        var d = baseline.def, b = baseline.author;
        var latOffset = { I: b.I.lat - d.I.lat, III: b.III.lat - d.III.lat, V: b.V.lat - d.V.lat };
        var ampOffset = { I: b.I.amp - d.I.amp, III: b.III.amp - d.III.amp, V: b.V.amp - d.V.amp };
        var v = {
            umbral: 20, repro: true, repro_var: 0, average_objetivo: 1500,
            lat_I: 0, lat_III: 0, lat_V: 0, amp_I: 0, amp_III: 0, amp_V: 0,
            fsp_800: 2.3, fsp_2000: 2.8, fsp_obj: 3.0
        };
        if (type === 'coclear') {
            // Sensorial: umbral elevado (recruitment), onda I reducida,
            // onda V preservada relativa a I, latencias casi normales a
            // intensidad supraumbral.
            v.umbral = Math.round(rand(30, 90));
            v.lat_I = latOffset.I + rand(0, 0.15); v.lat_III = latOffset.III + rand(0, 0.15); v.lat_V = latOffset.V + rand(0, 0.15);
            v.amp_I = ampOffset.I + b.I.amp * rand(-0.5, -0.2);
            v.amp_III = ampOffset.III + b.III.amp * rand(-0.2, 0.05);
            v.amp_V = ampOffset.V + b.V.amp * rand(-0.05, 0.15);
            v.average_objetivo = Math.round(rand(1500, 2500));
            v.fsp_800 = 2.3 * rand(0.8, 1.0); v.fsp_2000 = 2.8 * rand(0.8, 1.0); v.fsp_obj = 3.0 * rand(0.8, 1.0);
        } else if (type === 'transmission') {
            // Conductivo: desplazamiento uniforme de latencia y reducción
            // uniforme de amplitud en I/III/V -- interpicos quedan normales.
            var shift = rand(0.15, 0.35);
            var ampFactor = rand(-0.4, -0.2);
            v.umbral = Math.round(rand(20, 60));
            v.lat_I = latOffset.I + shift; v.lat_III = latOffset.III + shift; v.lat_V = latOffset.V + shift;
            v.amp_I = ampOffset.I + b.I.amp * ampFactor; v.amp_III = ampOffset.III + b.III.amp * ampFactor; v.amp_V = ampOffset.V + b.V.amp * ampFactor;
            v.average_objetivo = Math.round(rand(1500, 2200));
            v.fsp_800 = 2.3 * rand(0.85, 1.0); v.fsp_2000 = 2.8 * rand(0.85, 1.0); v.fsp_obj = 3.0 * rand(0.85, 1.0);
        } else if (type === 'neural') {
            // Retrococlear: las latencias y amplitudes NO se sortean acá.
            // El patrón (I-III, III-V, razón V/I, bloqueo...) es su propio
            // juego de parámetros -- ver el bloque "Patrón retrococlear" y
            // los presets. Si además se cargaran desviaciones por onda, el
            // efecto se sumaría dos veces. Acá queda solo el ruido de
            // test-retest y las condiciones de registro.
            v.umbral = Math.round(rand(0, 60));
            v.lat_I = latOffset.I + rand(-0.05, 0.05);
            v.lat_III = latOffset.III + rand(-0.05, 0.05);
            v.lat_V = latOffset.V + rand(-0.05, 0.05);
            v.amp_I = ampOffset.I + b.I.amp * rand(-0.08, 0.08);
            v.amp_III = ampOffset.III + b.III.amp * rand(-0.08, 0.08);
            v.amp_V = ampOffset.V + b.V.amp * rand(-0.08, 0.08);
            v.repro = Math.random() >= 0.6;
            v.repro_var = v.repro ? 0 : rand(0.15, 0.4);
            v.average_objetivo = Math.round(rand(2500, 4000));
            v.fsp_800 = rand(1.2, 1.8); v.fsp_2000 = rand(1.6, 2.2); v.fsp_obj = rand(2.0, 2.6);
        } else {
            // Normal: sin hallazgos, solo ruido de test-retest.
            v.umbral = Math.round(rand(0, 20));
            v.lat_I = latOffset.I + rand(-0.05, 0.05); v.lat_III = latOffset.III + rand(-0.05, 0.05); v.lat_V = latOffset.V + rand(-0.05, 0.05);
            v.amp_I = ampOffset.I + b.I.amp * rand(-0.08, 0.08);
            v.amp_III = ampOffset.III + b.III.amp * rand(-0.08, 0.08);
            v.amp_V = ampOffset.V + b.V.amp * rand(-0.08, 0.08);
            v.average_objetivo = Math.round(rand(1200, 1800));
            v.fsp_800 = 2.3 + rand(-0.1, 0.1); v.fsp_2000 = 2.8 + rand(-0.1, 0.1); v.fsp_obj = 3.0 + rand(-0.1, 0.1);
        }
        return v;
    }

    function fieldEl(lado, field) {
        return document.querySelector('[name="abr[' + lado + '][' + field + ']"]');
    }

    function setNum(lado, field, value, decimals) {
        var el = fieldEl(lado, field);
        if (el) { el.value = value.toFixed(decimals); }
    }

    // Los 6 campos de onda se muestran como valor ABSOLUTO a 80dB (lo que el
    // docente quiere fijar), pero se guardan como desviacion respecto del
    // normativo (lo que espera CaseBuilder.php/ABR_generator.py -- cambiar
    // ese contrato es un cambio de esquema más grande, no solo de este
    // formulario). El input visible (.abr-abs-input) no tiene name, no se
    // manda; el hidden (.abr-delta-input, mismo name de siempre) es el que
    // se envía.
    var ABR_WAVE_FIELDS = [['I', 'lat'], ['III', 'lat'], ['V', 'lat'], ['I', 'amp'], ['III', 'amp'], ['V', 'amp']];

    function absFieldEl(lado, wave, field) {
        return document.querySelector('.abr-abs-input[data-lado="' + lado + '"][data-wave="' + wave + '"][data-field="' + field + '"]');
    }

    function deltaFieldEl(lado, wave, field) {
        return fieldEl(lado, field + '_' + wave);
    }

    // Normativo -> lo que se muestra. Se llama al cargar la pagina y despues
    // de "Autocompletar" (que recalcula la desviacion sugerida).
    function syncAbsFromDelta(lado) {
        var baseline = resolveBaseline(pickPopulation()).author;
        ABR_WAVE_FIELDS.forEach(function (pair) {
            var wave = pair[0], field = pair[1];
            var absEl = absFieldEl(lado, wave, field);
            var deltaEl = deltaFieldEl(lado, wave, field);
            if (!absEl || !deltaEl) { return; }
            var delta = parseFloat(deltaEl.value) || 0;
            absEl.value = (baseline[wave][field] + delta).toFixed(2);
        });
    }

    // Lo que se muestra -> desviacion real a guardar. Se llama al tipear un
    // valor absoluto (ese campo) o al cambiar la poblacion de referencia
    // (todos, ver mas abajo) -- en ese caso el valor absoluto que el docente
    // ya fijo queda igual, se recalcula la desviacion contra el nuevo
    // normativo.
    function syncDeltaFromAbs(lado, wave, field) {
        var baseline = resolveBaseline(pickPopulation()).author;
        var absEl = absFieldEl(lado, wave, field);
        var deltaEl = deltaFieldEl(lado, wave, field);
        if (!absEl || !deltaEl) { return; }
        var absVal = parseFloat(absEl.value);
        if (isNaN(absVal)) { return; }
        deltaEl.value = (absVal - baseline[wave][field]).toFixed(4);
    }

    // Cambio de poblacion (edad/sexo/autor): un campo que el docente jamas
    // tipeo a mano (data-touched) sigue mostrando "el normativo" -- se
    // actualiza al normativo nuevo, la desviacion guardada (probablemente 0)
    // no cambia. Un campo que SI se tipeo mantiene el numero absoluto fijo
    // -- se recalcula la desviacion contra el normativo nuevo para que ese
    // numero no se mueva.
    function onAbrPopulationChange() {
        ['od', 'oi'].forEach(function (lado) {
            ABR_WAVE_FIELDS.forEach(function (pair) {
                var absEl = absFieldEl(lado, pair[0], pair[1]);
                if (absEl && absEl.dataset.touched === '1') {
                    syncDeltaFromAbs(lado, pair[0], pair[1]);
                }
            });
            syncAbsFromDelta(lado);
        });
        window.drawAbrPreview();
    }

    function autofillAbr(lado) {
        var typeSel = fieldEl(lado, 'type');
        var type = typeSel ? typeSel.value : 'normal';
        var v = buildValues(type, pickPopulation());
        // Retrococlear: el patrón se sortea aparte, no como desviaciones de
        // onda. Un caso al azar es un punto de partida -- para un cuadro
        // clínico concreto está el selector de presets.
        if (type === 'neural') { randomizeNeuralPattern(lado); }
        setNum(lado, 'umbral', v.umbral, 0);
        var reproEl = fieldEl(lado, 'repro');
        if (reproEl) { reproEl.checked = v.repro; }
        setNum(lado, 'repro_var', v.repro_var, 2);
        setNum(lado, 'average_objetivo', v.average_objetivo, 0);
        setNum(lado, 'lat_I', v.lat_I, 2);
        setNum(lado, 'lat_III', v.lat_III, 2);
        setNum(lado, 'lat_V', v.lat_V, 2);
        setNum(lado, 'amp_I', v.amp_I, 2);
        setNum(lado, 'amp_III', v.amp_III, 2);
        setNum(lado, 'amp_V', v.amp_V, 2);
        setNum(lado, 'fsp_800', v.fsp_800, 2);
        setNum(lado, 'fsp_2000', v.fsp_2000, 2);
        setNum(lado, 'fsp_obj', v.fsp_obj, 2);
        // La sugerencia es relativa a la poblacion actual (no un numero que
        // el docente fijo a mano) -- vuelve a seguir el normativo si despues
        // cambia edad/sexo/autor, ver onAbrPopulationChange.
        ABR_WAVE_FIELDS.forEach(function (pair) {
            var absEl = absFieldEl(lado, pair[0], pair[1]);
            if (absEl) { delete absEl.dataset.touched; }
        });
        syncAbsFromDelta(lado);
        if (window.drawAbrPreview) { window.drawAbrPreview(); }
    }

    // Los parámetros del patrón retrococlear solo existen dentro de
    // "Neural": con coclear o transmisión no hay lesión que tipificar y el
    // bloque confunde. Se oculta, no se borra -- si el docente vuelve a
    // Neural recupera lo que tenía, y los valores se siguen enviando (el
    // generador solo los mira si la patología es neural).
    function syncNeuralBlockVisibility(lado) {
        var bloque = document.querySelector('.abr-neural-block[data-lado="' + lado + '"]');
        if (!bloque) { return; }
        bloque.style.display = abrPathology(lado) === 'neural' ? '' : 'none';
    }

    var typeSelects = document.querySelectorAll('.abr-type-select');
    for (var ts = 0; ts < typeSelects.length; ts++) {
        syncNeuralBlockVisibility(typeSelects[ts].getAttribute('data-lado'));
        typeSelects[ts].addEventListener('change', function (e) {
            syncNeuralBlockVisibility(e.target.getAttribute('data-lado'));
        });
    }

    // Presets: precargan los parámetros y quedan editables. La etiqueta NO
    // se guarda -- el caso persiste los números, así el alumno nunca puede
    // leer el diagnóstico desde el caso ni la curva depender de un nombre.
    var ABR_NEURAL_PRESETS = <?= json_encode(CaseBuilder::ABR_NEURAL_PRESETS, JSON_UNESCAPED_UNICODE) ?>;

    function neuralFieldEl(lado, param) {
        return document.querySelector('.abr-neural-input[data-lado="' + lado + '"][data-param="' + param + '"]');
    }

    function applyNeuralPreset(lado) {
        var sel = document.querySelector('.abr-neural-preset-select[data-lado="' + lado + '"]');
        var nota = document.querySelector('.abr-neural-preset-nota[data-lado="' + lado + '"]');
        var preset = sel && sel.value ? ABR_NEURAL_PRESETS[sel.value] : null;
        if (!preset) { if (nota) { nota.textContent = ''; } return; }
        Object.keys(preset.params).forEach(function (param) {
            var el = neuralFieldEl(lado, param);
            if (el) { el.value = preset.params[param]; }
        });
        if (nota) { nota.textContent = preset.nota || ''; }
        if (window.drawAbrPreview) { window.drawAbrPreview(); }
    }

    // Elegir el preset solo muestra su nota; los valores se pisan al apretar
    // "Aplicar" -- asi un click de curiosidad no borra un patron ya tipeado.
    var presetSelects = document.querySelectorAll('.abr-neural-preset-select');
    for (var ps = 0; ps < presetSelects.length; ps++) {
        presetSelects[ps].addEventListener('change', function (e) {
            var lado = e.target.getAttribute('data-lado');
            var nota = document.querySelector('.abr-neural-preset-nota[data-lado="' + lado + '"]');
            var preset = e.target.value ? ABR_NEURAL_PRESETS[e.target.value] : null;
            if (nota) { nota.textContent = preset ? (preset.nota || '') : ''; }
        });
    }

    var presetBtns = document.querySelectorAll('.abr-neural-preset-btn');
    for (var pb = 0; pb < presetBtns.length; pb++) {
        presetBtns[pb].addEventListener('click', function (e) {
            applyNeuralPreset(e.currentTarget.getAttribute('data-lado'));
        });
    }

    // Sorteo del patrón retrococlear: no un valor fijo "correcto", sino un
    // caso plausible distinto cada vez (el alumno tiene que leer la curva,
    // no memorizar el caso). Se sortea DÓNDE está la lesión y después cuánto.
    function randomizeNeuralPattern(lado) {
        var proximal = Math.random() < 0.5;   // nervio vs tronco
        var params = {
            i_iii_ms: proximal ? rand(0.3, 0.8) : rand(0.0, 0.15),
            iii_v_ms: proximal ? rand(0.1, 0.4) : rand(0.4, 0.9),
            global_delay_ms: 0,
            v_i_factor: rand(0.25, 0.6),
            bloqueo: 'ninguno',
            microfonica: 'normal',
            desincronia: Math.random() < 0.5 ? 'leve' : 'alta',
            sensibilidad_tasa: Math.random() < 0.7 ? 'severa' : 'moderada'
        };
        Object.keys(params).forEach(function (param) {
            var el = neuralFieldEl(lado, param);
            if (!el) { return; }
            el.value = typeof params[param] === 'number' ? params[param].toFixed(2) : params[param];
        });
        var sel = document.querySelector('.abr-neural-preset-select[data-lado="' + lado + '"]');
        var nota = document.querySelector('.abr-neural-preset-nota[data-lado="' + lado + '"]');
        if (sel) { sel.value = ''; }
        if (nota) { nota.textContent = ''; }
    }

    var buttons = document.querySelectorAll('.abr-autofill-btn');
    for (var i = 0; i < buttons.length; i++) {
        buttons[i].addEventListener('click', function (e) {
            autofillAbr(e.currentTarget.getAttribute('data-lado'));
        });
    }

    // Vista previa en vivo: serie 100->0 dBnHL, version limpia (sin ruido,
    // sin promediacion, sin filtros) de ABRGenerator.calculate_wave_parameters
    // + build_target_curve (ver src/abr/ABR_generator.py) restringida a
    // I/III/V -- las mismas ondas que el formulario deja editar. Solo para
    // que el docente vea el efecto de sus valores, no reemplaza al generador
    // real (que corre server-side/en el cliente con ruido y FSP).
    var WAVE_SIGMA_PREVIEW = { I: 0.22, III: 0.22, V: 0.18 };
    var ABR_PREVIEW_INTENSITIES = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0];
    // Mismo umbral de visibilidad que usa el generador para decir si una
    // onda esta presente: por debajo no se le pone marcador.
    var WAVE_VISIBLE_UV = 0.02;
    // Piso de la escala automatica de amplitud. Sin esto, una serie sin
    // respuesta se amplificaria hasta llenar la fila y una linea plana
    // pareceria una onda.
    var AMP_SCALE_FLOOR_UV = 0.08;

    // Constantes espejadas de ABR_generator.py -- si cambian alla, cambian
    // aca: la previa tiene que mostrar la misma curva que va a ver el
    // alumno. Antes esta previa iba por su cuenta (amplitud lineal contra
    // un techo de 80 dB, la onda I con el escalon "disappear_offset" que
    // el generador ya no tiene, y CERO efecto de la patologia: un ANSD se
    // dibujaba con ondas normales).
    var LAT_SHIFT_FACTOR = { I: 0.85, III: 0.92, V: 1.0 };
    var WAVE_AMP_GROWTH = {
        I: { sl_min: 20, tau: 13 },
        III: { sl_min: 5, tau: 16 },
        V: { sl_min: -4, tau: 20 }
    };
    var PATHOLOGY_TAU_FACTOR = { coclear: 0.65 };
    var NORMAL_THRESHOLD_REF = 15;
    var COCHLEAR_LI_SL_REF = 40, COCHLEAR_LI_SLOPE = 0.15;
    var DEV_LI_GAIN = 0.35, DEV_LI_MAX = 1.5;
    // Reparto del retraso y de la caída de amplitud por onda (espejo de
    // NEURAL_LAT_SHARE / NEURAL_LAT_SHARE_IIIV / NEURAL_AMP_SHARE).
    var NEURAL_SHARE_I_III = { I: 0.0, III: 1.0, V: 1.0 };
    var NEURAL_SHARE_III_V = { I: 0.0, III: 0.0, V: 1.0 };
    var NEURAL_AMP_SHARE = { I: 0.0, III: 0.5, V: 1.0 };
    var NEURAL_BLOCK_AMP_FACTOR = 0.02;
    var NEURAL_DESYNC_WIDTH = { ninguna: 1.0, leve: 1.35, alta: 1.9 };

    function abrPathology(lado) {
        var el = document.querySelector('[name="abr[' + lado + '][type]"]');
        return el ? el.value : 'normal';
    }

    function abrNeuralParams(lado) {
        var out = {};
        ['i_iii_ms', 'iii_v_ms', 'global_delay_ms', 'v_i_factor',
         'bloqueo', 'desincronia'].forEach(function (param) {
            var el = document.querySelector('.abr-neural-input[data-lado="' + lado + '"][data-param="' + param + '"]');
            out[param] = el ? el.value : null;
        });
        return out;
    }

    // Mismo quiebre que ABRGenerator.latency_intensity_shift: ~0.12ms/10dB
    // cerca del techo (sobre 70dB), ~0.3ms/10dB de ahi para abajo
    // (Hood: ~0.3ms/10dB entre 70 y 50dB).
    function latShiftForIntensity(intensity) {
        if (intensity >= 70) { return (80 - intensity) / 10 * 0.12; }
        return (80 - 70) / 10 * 0.12 + (70 - intensity) / 10 * 0.3;
    }

    // Corrimiento con patologia: la transmision atenua el estimulo (GAP) y
    // corre la funcion en paralelo; la coclear la EMPINA cerca del umbral.
    function latShiftForCase(intensity, threshold, pathology) {
        var gap = pathology === 'transmission' ? Math.max(threshold - NORMAL_THRESHOLD_REF, 0) : 0;
        var shift = latShiftForIntensity(intensity - gap);
        if (pathology === 'coclear') {
            shift += COCHLEAR_LI_SLOPE * Math.max(0, COCHLEAR_LI_SL_REF - (intensity - threshold)) / 10;
        }
        return shift;
    }

    function widthFactorForSl(sl) {
        if (sl >= 50) { return 1.0; }
        if (sl >= 30) { return 1.0 + (50 - sl) * 0.03; }
        return Math.min(1.6 + (30 - sl) * 0.05, 2.6);
    }

    // Curva de crecimiento saturante sobre el SL, con el codo suave
    // (softplus) del generador.
    function ampFactorForWave(wave, sl, pathology) {
        var growth = WAVE_AMP_GROWTH[wave];
        var tau = growth.tau * (PATHOLOGY_TAU_FACTOR[pathology] || 1.0);
        var knee = 0.3 * tau;
        var x = (sl - growth.sl_min) / knee;
        // logaddexp(0, x) estable para x grande.
        var slEff = knee * (x > 30 ? x : Math.log(1 + Math.exp(x)));
        return 1.0 - Math.exp(-slEff / tau);
    }

    function gaussian(t, center, amp, sigma) {
        var z = (t - center) / sigma;
        return amp * Math.exp(-0.5 * z * z);
    }

    function computeWaveValues(lado, pop, intensity) {
        var baseline = resolveBaseline(pop).author;
        var threshold = parseFloat(fieldEl(lado, 'umbral').value) || 0;
        var pathology = abrPathology(lado);
        var neural = pathology === 'neural';
        var np = neural ? abrNeuralParams(lado) : null;
        var sl = intensity - threshold;
        var latShift = latShiftForCase(intensity, threshold, pathology);
        var devScale = Math.min(1.0 + DEV_LI_GAIN * Math.max(latShift, 0), DEV_LI_MAX);
        var width = widthFactorForSl(sl);
        var out = {};
        ['I', 'III', 'V'].forEach(function (wave) {
            var deltaLatEl = fieldEl(lado, 'lat_' + wave);
            var deltaAmpEl = fieldEl(lado, 'amp_' + wave);
            var deltaLat = deltaLatEl ? (parseFloat(deltaLatEl.value) || 0) : 0;
            var deltaAmp = deltaAmpEl ? (parseFloat(deltaAmpEl.value) || 0) : 0;
            var lat = baseline[wave].lat + latShift * LAT_SHIFT_FACTOR[wave] + deltaLat * devScale;
            var amp = baseline[wave].amp * ampFactorForWave(wave, sl, pathology);
            var sigmaGain = 1.0;
            if (neural) {
                lat += (parseFloat(np.global_delay_ms) || 0)
                    + (parseFloat(np.i_iii_ms) || 0) * NEURAL_SHARE_I_III[wave]
                    + (parseFloat(np.iii_v_ms) || 0) * NEURAL_SHARE_III_V[wave];
                var vi = parseFloat(np.v_i_factor);
                if (isNaN(vi)) { vi = 1.0; }
                amp *= Math.max(1.0 - (1.0 - vi) * NEURAL_AMP_SHARE[wave], 0);
                if (np.bloqueo === 'total' || (np.bloqueo === 'post_i' && wave !== 'I')) {
                    amp *= NEURAL_BLOCK_AMP_FACTOR;
                }
                sigmaGain = NEURAL_DESYNC_WIDTH[np.desincronia] || 1.0;
            }
            amp = Math.max(amp + deltaAmp, 0.001);
            out[wave] = { lat: lat, amp: amp, sigma: WAVE_SIGMA_PREVIEW[wave] * width * sigmaGain };
        });
        return out;
    }

    // Traza la suma de las 3 gaussianas y, de paso, devuelve la altura del
    // trazo en la latencia de cada onda: ahi va el marcador, asi la marca
    // toca la curva en vez de flotar.
    function buildRow(values, xPos, rowBaseY, ampScale) {
        function yAt(t) {
            var y = 0;
            ['I', 'III', 'V'].forEach(function (wave) {
                var v = values[wave];
                // Una onda por debajo del umbral de visibilidad no se
                // dibuja: si no, el residuo que deja el bloqueo se
                // amplificaba con la escala automatica y una serie SIN
                // respuesta mostraba ondulaciones que no existen.
                if (v.amp <= WAVE_VISIBLE_UV) { return; }
                y += gaussian(t, v.lat, v.amp, v.sigma);
            });
            return y;
        }
        var pts = [];
        for (var t = 0; t <= 12; t += 0.06) {
            pts.push(xPos(t).toFixed(1) + ',' + (rowBaseY - yAt(t) * ampScale).toFixed(1));
        }
        var picos = {};
        ['I', 'III', 'V'].forEach(function (wave) {
            picos[wave] = {
                x: xPos(values[wave].lat),
                y: rowBaseY - yAt(values[wave].lat) * ampScale,
                visible: values[wave].amp > WAVE_VISIBLE_UV
            };
        });
        return { points: pts.join(' '), picos: picos };
    }

    function renderAbrPreviewSide(lado, color) {
        var container = document.getElementById('abr-preview-' + lado);
        if (!container) { return; }
        var umbralEl = fieldEl(lado, 'umbral');
        if (!umbralEl) { return; }
        var pop = pickPopulation();
        var threshold = parseFloat(umbralEl.value) || 0;

        var marginLeft = 34, marginRight = 12, marginTop = 16, marginBottom = 22;
        var rowHeight = 26, plotWidth = 380;
        var totalWidth = marginLeft + plotWidth + marginRight;
        var plotTop = marginTop;
        var plotBottom = marginTop + ABR_PREVIEW_INTENSITIES.length * rowHeight;
        var totalHeight = plotBottom + marginBottom;
        function xPos(t) { return marginLeft + (t / 12) * plotWidth; }

        // Escala vertical automatica: la onda mas grande de TODA la serie
        // ocupa una fraccion fija de la fila. Con una escala fija, un oido
        // con amplitudes chicas se veia como una linea plana y uno normal
        // se salia de la fila.
        var serie = ABR_PREVIEW_INTENSITIES.map(function (intensity) {
            return computeWaveValues(lado, pop, intensity);
        });
        var ampMax = 0;
        serie.forEach(function (values) {
            ['I', 'III', 'V'].forEach(function (wave) {
                if (values[wave].amp > ampMax) { ampMax = values[wave].amp; }
            });
        });
        // Piso: sin esto, una serie sin respuesta amplificaria el residuo
        // hasta llenar la fila y una linea plana pareceria una onda.
        if (ampMax < AMP_SCALE_FLOOR_UV) { ampMax = AMP_SCALE_FLOOR_UV; }
        var ampScale = (rowHeight * 0.62) / ampMax;

        var svg = '<svg viewBox="0 0 ' + totalWidth + ' ' + totalHeight + '" xmlns="http://www.w3.org/2000/svg">';

        // Grilla de tiempo + eje ms
        for (var ms = 0; ms <= 12; ms += 1) {
            var x = xPos(ms);
            var mayor = ms % 2 === 0;
            svg += '<line x1="' + x + '" y1="' + plotTop + '" x2="' + x + '" y2="' + plotBottom +
                '" stroke="#000" stroke-opacity="' + (mayor ? 0.10 : 0.05) + '"></line>';
            if (mayor) {
                svg += '<text x="' + x + '" y="' + (plotBottom + 9) + '" font-size="6" text-anchor="middle" fill="currentColor">' + ms + '</text>';
            }
        }
        svg += '<text x="' + (marginLeft + plotWidth / 2) + '" y="' + (totalHeight - 2) + '" font-size="6" text-anchor="middle" fill="currentColor">ms</text>';
        svg += '<text x="2" y="' + (plotTop - 6) + '" font-size="6" fill="currentColor">dBnHL</text>';

        // Escala de amplitud: una barra de largo conocido dice cuanto es
        // un microvolt en este dibujo (el zoom cambia con el caso).
        var refUv = ampMax >= 0.4 ? 0.5 : (ampMax >= 0.15 ? 0.2 : 0.05);
        var barX = totalWidth - marginRight - 3;
        var barBottom = plotTop - 4;
        var barTop = barBottom - refUv * ampScale;
        svg += '<line x1="' + barX + '" y1="' + barTop + '" x2="' + barX + '" y2="' + barBottom + '" stroke="currentColor" stroke-width="0.8"></line>';
        svg += '<text x="' + (barX - 3) + '" y="' + (barBottom - 1) + '" font-size="5.5" text-anchor="end" fill="currentColor">' + refUv + ' uV</text>';

        // Sin ondas (bloqueo total): la previa dibuja I/III/V y no hay
        // ninguna. La linea plana ES el resultado -- se avisa para que no se
        // lea como "la previa no anda". El microfonico no se grafica aca.
        if (abrPathology(lado) === 'neural') {
            var npPrev = abrNeuralParams(lado);
            var microfonicaEl = neuralFieldEl(lado, 'microfonica');
            var avisoPrev = npPrev.bloqueo === 'total'
                ? 'Sin ondas' + (microfonicaEl && microfonicaEl.value === 'amplificada'
                    ? ': solo microfonico coclear (no se grafica aca)' : '')
                : (npPrev.bloqueo === 'post_i' ? 'Solo onda I: bloqueo proximal' : '');
            if (avisoPrev) {
                // Al pie: arriba chocaba con las etiquetas I/III/V.
                svg += '<text x="' + marginLeft + '" y="' + (totalHeight - 2) +
                    '" font-size="6" fill="' + color + '">' + avisoPrev + '</text>';
            }
        }

        // Filas: fondo de la fila del umbral, etiqueta de intensidad y trazo.
        var seguimiento = { I: [], III: [], V: [] };
        var trazos = '';
        ABR_PREVIEW_INTENSITIES.forEach(function (intensity, i) {
            var rowTop = plotTop + i * rowHeight;
            var rowBaseY = rowTop + rowHeight * 0.72;
            var isThresholdRow = Math.abs(intensity - Math.round(threshold / 10) * 10) < 0.01;
            if (isThresholdRow) {
                svg += '<rect x="0" y="' + rowTop + '" width="' + totalWidth + '" height="' + rowHeight +
                    '" fill="' + color + '" fill-opacity="0.07"></rect>';
            }
            svg += '<line x1="' + marginLeft + '" y1="' + rowBaseY + '" x2="' + (marginLeft + plotWidth) +
                '" y2="' + rowBaseY + '" stroke="#000" stroke-opacity="0.08"></line>';
            svg += '<text x="' + (marginLeft - 4) + '" y="' + (rowBaseY + 2) + '" font-size="6.5" text-anchor="end" fill="' +
                (isThresholdRow ? color : 'currentColor') + '" font-weight="' + (isThresholdRow ? 'bold' : 'normal') + '">' +
                intensity + '</text>';

            // Latencias de la fila de 80 dB: es el nivel al que el docente
            // fija los valores absolutos en los campos de arriba, asi que
            // ver ahi el numero cierra el circulo con lo que acaba de tipear.
            if (intensity === 80) {
                var etiquetas = ['I', 'III', 'V'].filter(function (wave) {
                    return serie[i][wave].amp > WAVE_VISIBLE_UV;
                }).map(function (wave) {
                    return wave + ' ' + serie[i][wave].lat.toFixed(2);
                }).join('   ');
                if (etiquetas) {
                    svg += '<text x="' + (marginLeft + plotWidth - 2) + '" y="' + (rowTop + 7) +
                        '" font-size="5.5" text-anchor="end" fill="' + color + '" fill-opacity="0.75">' +
                        etiquetas + ' ms</text>';
                }
            }

            var fila = buildRow(serie[i], xPos, rowBaseY, ampScale);
            trazos += '<polyline points="' + fila.points + '" fill="none" stroke="' + color + '" stroke-width="1"></polyline>';
            ['I', 'III', 'V'].forEach(function (wave) {
                var pico = fila.picos[wave];
                if (!pico.visible) { return; }
                seguimiento[wave].push(pico);
                // Marcador vertical sobre el pico: baja desde el techo de la
                // fila hasta tocar la curva.
                trazos += '<line x1="' + pico.x.toFixed(1) + '" y1="' + (rowTop + 1.5) + '" x2="' + pico.x.toFixed(1) +
                    '" y2="' + pico.y.toFixed(1) + '" stroke="' + color + '" stroke-width="0.4" stroke-opacity="0.3"></line>';
                trazos += '<circle cx="' + pico.x.toFixed(1) + '" cy="' + pico.y.toFixed(1) + '" r="0.9" fill="' + color + '"></circle>';
            });
        });

        // Seguimiento del pico entre intensidades: es la funcion
        // latencia-intensidad dibujada sobre la propia serie -- lo que hace
        // evidente si la onda se corre al bajar dB o se queda clavada.
        ['I', 'III', 'V'].forEach(function (wave) {
            var puntos = seguimiento[wave];
            if (puntos.length < 2) { return; }
            svg += '<polyline points="' + puntos.map(function (p) {
                return p.x.toFixed(1) + ',' + p.y.toFixed(1);
            }).join(' ') + '" fill="none" stroke="' + color + '" stroke-width="0.6" stroke-opacity="0.45" stroke-dasharray="2 1.5"></polyline>';
            var primero = puntos[0];
            svg += '<text x="' + primero.x.toFixed(1) + '" y="' + (plotTop - 6) + '" font-size="6" text-anchor="middle" fill="' +
                color + '" font-weight="bold">' + wave + '</text>';
        });

        svg += trazos;
        svg += '</svg>';
        container.innerHTML = svg;
    }

    window.drawAbrPreview = function () {
        renderAbrPreviewSide('od', '#b33a3a');
        renderAbrPreviewSide('oi', '#2255aa');
    };

    var abrPreviewForm = document.getElementById('case-form');
    if (abrPreviewForm) {
        abrPreviewForm.addEventListener('input', function (e) {
            if (e.target.name && /^abr\[/.test(e.target.name)) { window.drawAbrPreview(); }
            if (e.target.classList && e.target.classList.contains('abr-abs-input')) {
                e.target.dataset.touched = '1';
                syncDeltaFromAbs(e.target.getAttribute('data-lado'), e.target.getAttribute('data-wave'), e.target.getAttribute('data-field'));
                window.drawAbrPreview();
            }
        });
        abrPreviewForm.addEventListener('change', function (e) {
            if (e.target.name === 'gender') { onAbrPopulationChange(); return; }
            if (e.target.name && /^abr\[/.test(e.target.name)) { window.drawAbrPreview(); }
        });
    }
    var abrAuthorSelectEl = document.getElementById('abr-author-select');
    if (abrAuthorSelectEl) { abrAuthorSelectEl.addEventListener('change', onAbrPopulationChange); }
    var abrAgeEl = document.getElementById('patient-age');
    if (abrAgeEl) {
        abrAgeEl.addEventListener('input', onAbrPopulationChange);
        abrAgeEl.addEventListener('change', onAbrPopulationChange);
    }
    ['od', 'oi'].forEach(syncAbsFromDelta);
    window.drawAbrPreview();
})();
</script>
<script>
// Tab EOA: autocompletado del perfil por patología + vista previa
// (DP-grama y SNR por banda TEOAE).
//
// Los normativos replicados acá son los defaults bundled del cliente
// (resources/oae/normative_data.json). Si se tocan allá, tocar acá: esta
// vista es referencia visual para el docente, el examen real lo genera el
// cliente -- que además puede tener el normativo overrideado por curso
// (app_config normative_data.teoae/dpoae/soae/sfoae).
(function () {
    var EOAS_FREQS = <?= json_encode(CaseBuilder::EOAS_FREQS) ?>;
    var EOAS_SHAPES = <?= json_encode(CaseBuilder::EOAS_AUTOFILL_SHAPES) ?>;
    var EOAS_GRADES = <?= json_encode(CaseBuilder::EOAS_AUTOFILL_GRADES, JSON_UNESCAPED_UNICODE) ?>;
    var EOAS_JITTER = <?= CaseBuilder::EOAS_AUTOFILL_JITTER_DB ?>;
    var EOAS_MAX_ATTEN = <?= CaseBuilder::EOAS_MAX_PATHOLOGY_ATTEN_DB ?>;
    var DP = {
        f2List: [1000, 1500, 2000, 3000, 4000, 6000, 8000],
        peakF2: 3000, peakDb: 12, rollLow: 4, rollHigh: 7,
        nfDb: -22, nfLfRise: 8, minSnr: 6, passMin: 4,
        band: {
            '1000': [-5, 13], '1500': [-3, 15], '2000': [-1, 16], '3000': [0, 17],
            '4000': [-1, 16], '6000': [-4, 13], '8000': [-8, 9]
        }
    };
    var TE = {
        bands: [1000, 1500, 2000, 3000, 4000],
        expected: { '1000': 8, '1500': 10, '2000': 12, '3000': 11, '4000': 9 },
        nfSweepDb: 14, nSweeps: 260, minSnr: 6, passMin: 3
    };

    function numField(lado, field) {
        return document.querySelector('[name="eoas[' + lado + '][' + field + ']"]');
    }
    function numVal(lado, field, fallback) {
        var el = numField(lado, field);
        if (!el) { return fallback; }
        var n = parseFloat(el.value);
        return isNaN(n) ? fallback : n;
    }
    function typeVal(lado) {
        var el = document.querySelector('[name="eoas[' + lado + '][type]"]');
        return el ? el.value : 'normal';
    }
    function desvInput(lado, hz) {
        return document.querySelector('[name="eoas[' + lado + '][desv][' + hz + ']"]');
    }

    // Mismo criterio que oae_attenuation_db() en src/oae/generators/base.py
    // (1.2 dB/dB sobre 15 dB HL en coclear, 2 sobre 8 en transmisión, con
    // tope EOAS_MAX_PATHOLOGY_ATTEN_DB). Si se toca allá, tocar acá.
    function pathologyAtten(type, umbral) {
        if (type === 'coclear') { return Math.min(Math.max(0, umbral - 15) * 1.2, EOAS_MAX_ATTEN); }
        if (type === 'transmission') { return Math.min(Math.max(0, umbral - 8) * 2, EOAS_MAX_ATTEN); }
        return 0;
    }

    // Pérdida de sello = pérdida de nivel de estímulo en el conducto, y por
    // lo tanto de emisión (20*log10 del fit, igual que probe_check.py).
    function selloLossDb(lado) {
        var fit = Math.min(100, Math.max(5, numVal(lado, 'sello_pct', 85))) / 100;
        return -20 * Math.log(fit) / Math.LN10;
    }

    // Desviación por frecuencia, interpolada en log2 sobre el perfil que
    // cargó el docente (mismo interp que usa el cliente).
    function desvAt(lado, freq) {
        var xs = [], ys = [];
        for (var i = 0; i < EOAS_FREQS.length; i++) {
            var el = desvInput(lado, EOAS_FREQS[i]);
            var val = el ? parseFloat(el.value) : 0;
            xs.push(Math.log(EOAS_FREQS[i]) / Math.LN2);
            ys.push(isNaN(val) ? 0 : val);
        }
        var lf = Math.log(freq) / Math.LN2;
        if (lf <= xs[0]) { return ys[0]; }
        if (lf >= xs[xs.length - 1]) { return ys[ys.length - 1]; }
        for (var k = 1; k < xs.length; k++) {
            if (lf <= xs[k]) {
                var t = (lf - xs[k - 1]) / (xs[k] - xs[k - 1]);
                return ys[k - 1] + t * (ys[k] - ys[k - 1]);
            }
        }
        return 0;
    }

    function totalAtten(lado, freq) {
        return pathologyAtten(typeVal(lado), numVal(lado, 'umbral', 20))
            + numVal(lado, 'atten_db', 0)
            + selloLossDb(lado)
            + desvAt(lado, freq);
    }

    function dpNoiseFloor(lado, f2) {
        var lf = Math.log(2000 / f2) / Math.LN2;
        return DP.nfDb + DP.nfLfRise * Math.max(0, lf) + numVal(lado, 'ruido_db', 0);
    }

    function dpLevel(lado, f2) {
        var oct = Math.log(f2 / DP.peakF2) / Math.LN2;
        var roll = oct > 0 ? DP.rollHigh : DP.rollLow;
        return DP.peakDb - Math.abs(oct) * roll - totalAtten(lado, f2);
    }

    // SNR por banda TEOAE. El piso baja 10*log10(N) al promediar N barridos.
    function teoaeSnr(lado, band) {
        var nf = TE.nfSweepDb - 10 * Math.log(TE.nSweeps) / Math.LN10
            + numVal(lado, 'ruido_db', 0);
        var resp = TE.expected[String(band)] - totalAtten(lado, band);
        return resp - nf;
    }

    function eoasRand(min, max) { return min + Math.random() * (max - min); }

    function gradesFor(type) {
        return EOAS_GRADES[type] || EOAS_GRADES['normal'];
    }

    // Grado elegido en el select del oído; "random" (o un valor que ya no
    // exista para esa patología) sortea entre los grados de la patología.
    function pickGrade(lado) {
        var grades = gradesFor(typeVal(lado));
        var sel = document.querySelector('[name="eoas_grade[' + lado + ']"]');
        var key = sel ? sel.value : 'random';
        for (var i = 0; i < grades.length; i++) {
            if (grades[i].key === key) { return grades[i]; }
        }
        return grades[Math.floor(Math.random() * grades.length)];
    }

    // Rellena el select de grado con los grados de la patología actual.
    // Se llama al cargar y cada vez que cambia la patología del oído.
    function syncGradeOptions(lado) {
        var sel = document.querySelector('[name="eoas_grade[' + lado + ']"]');
        if (!sel) { return; }
        var grades = gradesFor(typeVal(lado));
        var previo = sel.value;
        var html = '<option value="random">Aleatorio (sortea grado)</option>';
        for (var i = 0; i < grades.length; i++) {
            html += '<option value="' + grades[i].key + '">' + grades[i].label + '</option>';
        }
        sel.innerHTML = html;
        sel.value = 'random';
        for (var j = 0; j < grades.length; j++) {
            if (grades[j].key === previo) { sel.value = previo; }
        }
    }

    function setNumField(lado, field, value, decimals) {
        var el = numField(lado, field);
        if (el) { el.value = decimals ? value.toFixed(decimals) : String(Math.round(value)); }
    }

    // "Autocompletar": sortea un caso plausible del grado elegido -- umbral,
    // perfil por frecuencia y condiciones de registro. Antes solo escribía
    // desviaciones fijas y dejaba el umbral en 20, así que un "coclear"
    // recién creado no se distinguía de un normal en ninguna de las cuatro
    // pruebas. Es un punto de partida al azar, editable campo a campo.
    function autofillEoas(lado) {
        var type = typeVal(lado);
        var grade = pickGrade(lado);
        var shape = EOAS_SHAPES[type] || EOAS_SHAPES['normal'];
        var scale = eoasRand(grade.scale[0], grade.scale[1]);
        setNumField(lado, 'umbral', eoasRand(grade.umbral[0], grade.umbral[1]));
        for (var i = 0; i < EOAS_FREQS.length; i++) {
            var hz = EOAS_FREQS[i];
            var el = desvInput(lado, hz);
            if (!el) { continue; }
            var base = shape[String(hz)] !== undefined ? shape[String(hz)] : 0;
            var jitter = eoasRand(-EOAS_JITTER, EOAS_JITTER);
            el.value = Math.max(0, base * scale + jitter).toFixed(1);
        }
        // Condiciones de registro: son las que hacen que dos pacientes con
        // la misma cóclea no den la misma pantalla.
        setNumField(lado, 'ruido_db', eoasRand(grade.ruido[0], grade.ruido[1]), 1);
        setNumField(lado, 'sello_pct', eoasRand(grade.sello[0], grade.sello[1]));
        setNumField(lado, 'variabilidad_db', eoasRand(1.5, 3.5), 1);
        drawEoaPreview();
    }

    function renderEoaSide(lado, color) {
        var container = document.getElementById('eoa-preview-' + lado);
        if (!container) { return; }

        var W = 400, marginLeft = 26, marginRight = 6;
        var plotW = W - marginLeft - marginRight;
        var dpTop = 12, dpH = 92, gap = 26, barH = 60;
        var H = dpTop + dpH + gap + barH + 26;
        // Eje Y del DP-grama: -30..25 dB SPL (cubre el piso de ruido en
        // graves y el techo del área normal).
        var yMin = -30, yMax = 25;
        function yDp(db) { return dpTop + dpH * (1 - (Math.max(yMin, Math.min(yMax, db)) - yMin) / (yMax - yMin)); }
        var lf0 = Math.log(DP.f2List[0]) / Math.LN2;
        var lf1 = Math.log(DP.f2List[DP.f2List.length - 1]) / Math.LN2;
        function xF2(f2) { return marginLeft + plotW * ((Math.log(f2) / Math.LN2 - lf0) / (lf1 - lf0)); }

        var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" xmlns="http://www.w3.org/2000/svg">';

        // Área normal (p5-p95 del nivel DP por f2).
        var top = [], bot = [];
        DP.f2List.forEach(function (f2) {
            var b = DP.band[String(f2)];
            top.push(xF2(f2).toFixed(1) + ',' + yDp(b[1]).toFixed(1));
            bot.unshift(xF2(f2).toFixed(1) + ',' + yDp(b[0]).toFixed(1));
        });
        svg += '<polygon points="' + top.concat(bot).join(' ') + '" fill="#2e9e5b" fill-opacity="0.13"></polygon>';

        // Grilla + etiquetas de dB.
        [-20, 0, 20].forEach(function (db) {
            svg += '<line x1="' + marginLeft + '" y1="' + yDp(db) + '" x2="' + (W - marginRight) + '" y2="' + yDp(db) + '" stroke="#000" stroke-opacity="0.08"></line>';
            svg += '<text x="' + (marginLeft - 3) + '" y="' + (yDp(db) + 2) + '" font-size="6" text-anchor="end" fill="currentColor">' + db + '</text>';
        });

        // Curva DP + piso de ruido + puntos PASS/REFER.
        var dpPts = [], nfPts = [], marks = '';
        DP.f2List.forEach(function (f2) {
            var dp = dpLevel(lado, f2), nf = dpNoiseFloor(lado, f2);
            dpPts.push(xF2(f2).toFixed(1) + ',' + yDp(dp).toFixed(1));
            nfPts.push(xF2(f2).toFixed(1) + ',' + yDp(nf).toFixed(1));
            var pass = (dp - nf) >= DP.minSnr;
            marks += '<circle cx="' + xF2(f2).toFixed(1) + '" cy="' + yDp(dp).toFixed(1) + '" r="2.2" fill="' +
                (pass ? color : '#ffffff') + '" stroke="' + color + '" stroke-width="0.8"></circle>';
        });
        svg += '<polyline points="' + nfPts.join(' ') + '" fill="none" stroke="#888" stroke-width="0.8" stroke-dasharray="3 2"></polyline>';
        svg += '<polyline points="' + dpPts.join(' ') + '" fill="none" stroke="' + color + '" stroke-width="1.2"></polyline>';
        svg += marks;
        DP.f2List.forEach(function (f2) {
            svg += '<text x="' + xF2(f2).toFixed(1) + '" y="' + (dpTop + dpH + 8) + '" font-size="5.5" text-anchor="middle" fill="currentColor">' + (f2 / 1000) + '</text>';
        });
        svg += '<text x="' + (marginLeft + plotW / 2) + '" y="' + (dpTop + dpH + 16) + '" font-size="6" text-anchor="middle" fill="currentColor">DP-grama -- f2 (kHz), nivel DP en dB SPL</text>';

        // Barras de SNR por banda TEOAE, con la línea de criterio.
        var barTop = dpTop + dpH + gap;
        var snrMax = 30;
        function yBar(snr) { return barTop + barH * (1 - Math.max(0, Math.min(snrMax, snr)) / snrMax); }
        svg += '<line x1="' + marginLeft + '" y1="' + yBar(0) + '" x2="' + (W - marginRight) + '" y2="' + yBar(0) + '" stroke="#000" stroke-opacity="0.25"></line>';
        svg += '<line x1="' + marginLeft + '" y1="' + yBar(TE.minSnr) + '" x2="' + (W - marginRight) + '" y2="' + yBar(TE.minSnr) + '" stroke="#c0392b" stroke-width="0.8" stroke-dasharray="4 2"></line>';
        svg += '<text x="' + (marginLeft - 3) + '" y="' + (yBar(TE.minSnr) + 2) + '" font-size="6" text-anchor="end" fill="#c0392b">' + TE.minSnr + '</text>';
        var slot = plotW / TE.bands.length;
        TE.bands.forEach(function (band, i) {
            var snr = teoaeSnr(lado, band);
            var x = marginLeft + slot * i + slot * 0.22;
            var w = slot * 0.56;
            var y = yBar(Math.max(0, snr));
            svg += '<rect x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + Math.max(0.6, yBar(0) - y).toFixed(1) +
                '" fill="' + (snr >= TE.minSnr ? color : '#c0392b') + '" fill-opacity="' + (snr >= TE.minSnr ? '0.75' : '0.5') + '"></rect>';
            svg += '<text x="' + (x + w / 2).toFixed(1) + '" y="' + (yBar(0) + 8) + '" font-size="5.5" text-anchor="middle" fill="currentColor">' + (band / 1000) + '</text>';
        });
        svg += '<text x="' + (marginLeft + plotW / 2) + '" y="' + (yBar(0) + 16) + '" font-size="6" text-anchor="middle" fill="currentColor">TEOAE -- SNR por banda (kHz), criterio ' + TE.minSnr + ' dB</text>';

        // Resumen PASS/REFER de las dos pruebas, igual criterio que el cliente.
        var dpPass = DP.f2List.filter(function (f2) { return (dpLevel(lado, f2) - dpNoiseFloor(lado, f2)) >= DP.minSnr; }).length;
        var tePass = TE.bands.filter(function (b) { return teoaeSnr(lado, b) >= TE.minSnr; }).length;
        var veredicto = 'DPOAE ' + dpPass + '/' + DP.f2List.length + ' ' + (dpPass >= DP.passMin ? 'PASS' : 'REFER') +
            '  --  TEOAE ' + tePass + '/' + TE.bands.length + ' ' + (tePass >= TE.passMin ? 'PASS' : 'REFER');
        svg += '<text x="' + marginLeft + '" y="' + (H - 2) + '" font-size="6.5" fill="currentColor">' + veredicto + '</text>';
        svg += '</svg>';
        container.innerHTML = svg;
    }

    function drawEoaPreview() {
        renderEoaSide('od', '#b33a3a');
        renderEoaSide('oi', '#2255aa');
    }
    window.drawEoaPreview = drawEoaPreview;

    var eoasForm = document.getElementById('case-form');
    if (eoasForm) {
        eoasForm.addEventListener('input', function (e) {
            if (e.target.name && /^eoas\[/.test(e.target.name)) { drawEoaPreview(); }
        });
        eoasForm.addEventListener('change', function (e) {
            if (e.target.name && /^eoas\[/.test(e.target.name)) { drawEoaPreview(); }
        });
    }
    var eoasButtons = document.querySelectorAll('.eoas-autofill-btn');
    for (var i = 0; i < eoasButtons.length; i++) {
        eoasButtons[i].addEventListener('click', function (e) {
            autofillEoas(e.target.getAttribute('data-lado'));
        });
    }
    // Los grados dependen de la patología del oído: se recargan al cambiarla
    // (una coclear tiene leve/moderada/severa, una neural una sola).
    var eoasTypeSelects = document.querySelectorAll('.eoas-type-select');
    for (var t = 0; t < eoasTypeSelects.length; t++) {
        syncGradeOptions(eoasTypeSelects[t].getAttribute('data-lado'));
        eoasTypeSelects[t].addEventListener('change', function (e) {
            syncGradeOptions(e.target.getAttribute('data-lado'));
        });
    }
    drawEoaPreview();
})();
</script>

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
    var dlOriginal = document.getElementById('patient-download-original');
    var dlAvatar = document.getElementById('patient-download-avatar');
    if (!fileInput || !modal) { return; }

    var CASE_ID = <?= json_encode($photoCaseId) ?>;
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
                    if (dlOriginal) { dlOriginal.hidden = false; }
                    if (dlAvatar) { dlAvatar.hidden = false; }
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

<script>
// Ficha Otoscopia: sin selector de modo -- 1 sola fase ya ES "única"; se
// agrega/quita fase (solo la última -- así no hay que reindexar archivos
// en disco), y se sube/borra cada imagen por fetch + FormData. Mismo
// patrón de recorte manual que la foto de paciente (modal de pan/zoom),
// pero con guía cuadrada (no circular) -- ver #otoscopia-crop-modal y
// OtoscopiaPhoto::save().
(function () {
    var CASE_ID = <?= json_encode($photoCaseId) ?>;
    var countInput = document.getElementById('otoscopia-fase-count');
    var container = document.getElementById('otoscopia-fases');
    var addBtn = document.getElementById('otoscopia-add-fase');
    var msgEl = document.getElementById('otoscopia-msg');
    if (!countInput || !container) { return; }

    // --- Modal de recorte cuadrado (pan/zoom), mismo mecanismo que el de
    // foto de paciente pero reutilizable para cualquier input de la lista
    // (se le pasa el <input> pendiente al abrir). ---
    var cropModal = document.getElementById('otoscopia-crop-modal');
    var cropViewport = document.getElementById('otoscopia-crop-viewport');
    var cropImg = document.getElementById('otoscopia-crop-img');
    var cropZoom = document.getElementById('otoscopia-crop-zoom');
    var cropCancelBtn = document.getElementById('otoscopia-crop-cancel');
    var cropConfirmBtn = document.getElementById('otoscopia-crop-confirm');
    var CROP_VIEWPORT = 280;
    var naturalW = 0, naturalH = 0, coverScale = 1, scale = 1;
    var tx = 0, ty = 0;
    var dragging = false, dragStartX = 0, dragStartY = 0, dragOrigTx = 0, dragOrigTy = 0;
    var pendingInput = null, pendingFile = null;

    function clampPan() {
        var dispW = naturalW * scale;
        var dispH = naturalH * scale;
        var minTx = Math.min(0, CROP_VIEWPORT - dispW);
        var minTy = Math.min(0, CROP_VIEWPORT - dispH);
        tx = Math.max(minTx, Math.min(0, tx));
        ty = Math.max(minTy, Math.min(0, ty));
    }

    function applyTransform() {
        cropImg.style.transform = 'translate(' + tx + 'px,' + ty + 'px) scale(' + scale + ')';
    }

    function openCropModal(input, file) {
        pendingInput = input;
        pendingFile = file;
        cropImg.onload = function () {
            naturalW = cropImg.naturalWidth;
            naturalH = cropImg.naturalHeight;
            coverScale = Math.max(CROP_VIEWPORT / naturalW, CROP_VIEWPORT / naturalH);
            scale = coverScale;
            tx = (CROP_VIEWPORT - naturalW * scale) / 2;
            ty = (CROP_VIEWPORT - naturalH * scale) / 2;
            cropZoom.value = '1';
            applyTransform();
            cropModal.hidden = false;
        };
        cropImg.src = URL.createObjectURL(file);
    }

    function closeCropModal() {
        cropModal.hidden = true;
        if (pendingInput) { pendingInput.value = ''; }
        pendingInput = null;
        pendingFile = null;
    }

    cropCancelBtn.addEventListener('click', closeCropModal);

    cropZoom.addEventListener('input', function () {
        var z = parseFloat(cropZoom.value);
        var cx = CROP_VIEWPORT / 2, cy = CROP_VIEWPORT / 2;
        var imgCx = (cx - tx) / scale;
        var imgCy = (cy - ty) / scale;
        scale = coverScale * z;
        tx = cx - imgCx * scale;
        ty = cy - imgCy * scale;
        clampPan();
        applyTransform();
    });

    function cropPointerDown(x, y) {
        dragging = true;
        dragStartX = x; dragStartY = y;
        dragOrigTx = tx; dragOrigTy = ty;
    }
    function cropPointerMove(x, y) {
        if (!dragging) { return; }
        tx = dragOrigTx + (x - dragStartX);
        ty = dragOrigTy + (y - dragStartY);
        clampPan();
        applyTransform();
    }
    function cropPointerUp() { dragging = false; }

    cropViewport.addEventListener('mousedown', function (e) { cropPointerDown(e.clientX, e.clientY); });
    window.addEventListener('mousemove', function (e) { cropPointerMove(e.clientX, e.clientY); });
    window.addEventListener('mouseup', cropPointerUp);
    cropViewport.addEventListener('touchstart', function (e) {
        cropPointerDown(e.touches[0].clientX, e.touches[0].clientY);
    }, { passive: true });
    cropViewport.addEventListener('touchmove', function (e) {
        cropPointerMove(e.touches[0].clientX, e.touches[0].clientY);
        e.preventDefault();
    }, { passive: false });
    cropViewport.addEventListener('touchend', cropPointerUp);

    cropConfirmBtn.addEventListener('click', function () {
        if (!pendingInput || !pendingFile) { return; }
        var side = pendingInput.getAttribute('data-side');
        var idx = pendingInput.getAttribute('data-fase-idx');
        var slot = pendingInput.closest('.otoscopia-photo-slot');
        var img = slot.querySelector('.otoscopia-thumb');
        var empty = slot.querySelector('.otoscopia-thumb-empty');

        var srcSize = CROP_VIEWPORT / scale;
        var srcX = -tx / scale;
        var srcY = -ty / scale;

        var fd = new FormData();
        fd.append('csrf_token', csrfToken());
        fd.append('case_id', CASE_ID);
        fd.append('side', side);
        fd.append('fase_idx', idx);
        fd.append('crop_x', Math.round(srcX));
        fd.append('crop_y', Math.round(srcY));
        fd.append('crop_size', Math.round(srcSize));
        fd.append('photo', pendingFile);

        var input = pendingInput;
        cropConfirmBtn.disabled = true;
        cropConfirmBtn.textContent = 'Guardando...';
        input.disabled = true;

        fetch('otoscopia_photo_upload.php', { method: 'POST', body: fd })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                cropConfirmBtn.disabled = false;
                cropConfirmBtn.textContent = 'Guardar foto';
                input.disabled = false;
                if (data.ok) {
                    img.src = 'otoscopia_photo.php?case_id=' + encodeURIComponent(CASE_ID) + '&side=' + side + '&fase=' + idx + '&v=' + Date.now();
                    img.hidden = false;
                    empty.hidden = true;
                    var delBtn = slot.querySelector('.otoscopia-delete-photo');
                    if (delBtn) { delBtn.hidden = false; }
                    var dlLink = slot.querySelector('.otoscopia-download-photo');
                    if (dlLink) { dlLink.hidden = false; }
                    showMsg('Imagen actualizada.', false);
                    cropModal.hidden = true;
                    input.value = '';
                    pendingInput = null;
                    pendingFile = null;
                } else {
                    showMsg(data.error || 'No se pudo guardar la imagen.', true);
                }
            })
            .catch(function () {
                cropConfirmBtn.disabled = false;
                cropConfirmBtn.textContent = 'Guardar foto';
                input.disabled = false;
                showMsg('Error de red al subir la imagen.', true);
            });
    });

    function csrfToken() {
        var el = document.querySelector('input[name="csrf_token"]');
        return el ? el.value : '';
    }

    function showMsg(text, isError) {
        if (!msgEl) { return; }
        msgEl.textContent = text;
        msgEl.style.color = isError ? '#a33' : '#2a7a2a';
        msgEl.hidden = false;
    }

    function faseBlocks() {
        return Array.prototype.slice.call(container.querySelectorAll('.otoscopia-fase'));
    }

    // Solo la última fase puede quitarse (sin reindexar imágenes en disco).
    function updateRemoveButtons() {
        var blocks = faseBlocks();
        blocks.forEach(function (block, i) {
            var btn = block.querySelector('.otoscopia-remove-fase');
            if (btn) {
                btn.hidden = i !== blocks.length - 1;
            }
        });
    }

    var slotTpl = document.getElementById('otoscopia-slot-tpl');
    var faseTpl = document.getElementById('otoscopia-fase-tpl');

    function buildSlot(side, label, idx) {
        var slot = slotTpl.content.firstElementChild.cloneNode(true);
        var tag = slot.querySelector('.side-tag');
        tag.textContent = label;
        tag.classList.add(side);
        var img = slot.querySelector('.otoscopia-thumb');
        img.setAttribute('data-side', side);
        img.setAttribute('data-fase-idx', idx);
        img.setAttribute('alt', 'Otoscopia ' + label + ' fase ' + (idx + 1));
        var input = slot.querySelector('.otoscopia-photo-input');
        input.setAttribute('data-side', side);
        input.setAttribute('data-fase-idx', idx);
        var delBtn = slot.querySelector('.otoscopia-delete-photo');
        delBtn.setAttribute('data-side', side);
        delBtn.setAttribute('data-fase-idx', idx);
        var dlLink = slot.querySelector('.otoscopia-download-photo');
        dlLink.setAttribute('data-side', side);
        dlLink.setAttribute('data-fase-idx', idx);
        dlLink.href = 'otoscopia_photo.php?case_id=' + encodeURIComponent(CASE_ID) + '&side=' + side + '&fase=' + idx + '&download=1';
        return slot;
    }

    function buildFaseBlock(idx) {
        var block = faseTpl.content.firstElementChild.cloneNode(true);
        block.setAttribute('data-fase-idx', idx);
        block.querySelector('.side-heading .side-tag').textContent = 'Fase ' + (idx + 1);
        block.querySelector('.otoscopia-remove-fase').setAttribute('data-fase-idx', idx);
        block.querySelector('textarea').setAttribute('name', 'otoscopia[texto][' + idx + ']');
        var twoCol = block.querySelector('.two-col');
        [['od', 'OD'], ['oi', 'OI']].forEach(function (s) {
            twoCol.appendChild(buildSlot(s[0], s[1], idx));
        });
        return block;
    }

    if (addBtn) {
        addBtn.addEventListener('click', function () {
            var count = parseInt(countInput.value, 10) || 1;
            if (count >= <?= CaseBuilder::OTOSCOPIA_MAX_FASES ?>) {
                showMsg('Ya se alcanzó el máximo de fases.', true);
                return;
            }
            container.appendChild(buildFaseBlock(count));
            countInput.value = String(count + 1);
            updateRemoveButtons();
        });
    }

    container.addEventListener('click', function (e) {
        var btn = e.target.closest('.otoscopia-remove-fase');
        if (!btn) { return; }
        var blocks = faseBlocks();
        var idx = parseInt(btn.getAttribute('data-fase-idx'), 10);
        if (idx !== blocks.length - 1 || idx === 0) { return; } // defensivo: solo la última, nunca la 1ª
        if (!confirm('¿Quitar la fase ' + (idx + 1) + '? Se borran también sus imágenes.')) { return; }

        var block = blocks[blocks.length - 1];
        if (CASE_ID) {
            ['od', 'oi'].forEach(function (side) {
                var fd = new FormData();
                fd.append('csrf_token', csrfToken());
                fd.append('case_id', CASE_ID);
                fd.append('side', side);
                fd.append('fase_idx', String(idx));
                fd.append('action', 'delete');
                fetch('otoscopia_photo_upload.php', { method: 'POST', body: fd }); // best-effort, no bloquea el UI
            });
        }
        block.remove();
        countInput.value = String(idx);
        updateRemoveButtons();
    });

    // Elegir archivo: delegado en el contenedor porque las fases agregadas
    // después no existían al cargar la página. Abre el modal de recorte en
    // vez de subir directo -- la subida real ocurre en cropConfirmBtn.
    container.addEventListener('change', function (e) {
        var input = e.target.closest('.otoscopia-photo-input');
        if (!input || !input.files || !input.files[0]) { return; }
        openCropModal(input, input.files[0]);
    });

    container.addEventListener('click', function (e) {
        var btn = e.target.closest('.otoscopia-delete-photo');
        if (!btn) { return; }
        if (!confirm('¿Borrar esta foto?')) { return; }
        var side = btn.getAttribute('data-side');
        var idx = btn.getAttribute('data-fase-idx');
        var slot = btn.closest('.otoscopia-photo-slot');
        var img = slot.querySelector('.otoscopia-thumb');
        var empty = slot.querySelector('.otoscopia-thumb-empty');
        var dlLink = slot.querySelector('.otoscopia-download-photo');

        var fd = new FormData();
        fd.append('csrf_token', csrfToken());
        fd.append('case_id', CASE_ID);
        fd.append('side', side);
        fd.append('fase_idx', idx);
        fd.append('action', 'delete');

        btn.disabled = true;
        fetch('otoscopia_photo_upload.php', { method: 'POST', body: fd })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                btn.disabled = false;
                if (data.ok) {
                    img.hidden = true;
                    img.removeAttribute('src');
                    empty.hidden = false;
                    btn.hidden = true;
                    if (dlLink) { dlLink.hidden = true; }
                    showMsg('Imagen borrada.', false);
                } else {
                    showMsg(data.error || 'No se pudo borrar la imagen.', true);
                }
            })
            .catch(function () {
                btn.disabled = false;
                showMsg('Error de red al borrar la imagen.', true);
            });
    });

    updateRemoveButtons();
})();
</script>

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
        var auto = document.getElementById('acumetria-auto-toggle');
        var isAuto = !!(auto && auto.checked);
        FREQ_IDX.forEach(function (n) {
            ['od', 'oi'].forEach(function (side) {
                var select = document.getElementById('rinne_' + n + '_' + side);
                if (!select) return;
                if (isAuto) {
                    select.value = rinneAuto(threshold('aerea', side, n), threshold('osea', side, n));
                }
                select.disabled = isAuto;
            });
            var weberSelect = document.getElementById('weber_' + n);
            if (!weberSelect) return;
            if (isAuto) {
                weberSelect.value = weberAuto(threshold('osea', 'od', n), threshold('osea', 'oi', n));
            }
            weberSelect.disabled = isAuto;
        });
    }

    var acumetriaAutoToggle = document.getElementById('acumetria-auto-toggle');
    if (acumetriaAutoToggle) { acumetriaAutoToggle.addEventListener('change', syncAll); }
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
