<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/CaseBuilder.php';
require_once __DIR__ . '/../../src/CaseProfile.php';
require_once __DIR__ . '/../../src/CaseCompleteness.php';
require_once __DIR__ . '/../../src/CaseForm.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/PatientPhoto.php';
require_once __DIR__ . '/../../src/OtoscopiaPhoto.php';
require_once __DIR__ . '/../../src/Patients.php';
require_once __DIR__ . '/../../src/Sala.php';

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

// fv()/zip_pairs(): la lógica vive en CaseForm (el parseo del POST la usa
// tanto como el form al redibujarse). Acá quedan como funciones sueltas
// porque las plantillas de más abajo las llaman 29 veces y `CaseForm::val`
// en cada atributo HTML no se lee.
/** Lee un valor anidado de un array (ej. $v['aerea']['od'][3]) con default si falta. */
function fv(array $arr, array $path, $default = null)
{
    return CaseForm::val($arr, $path, $default);
}

/** [od0,od1,...] + [oi0,oi1,...] -> [[od0,oi0],[od1,oi1],...] -- shape que espera cases.data. */
function zip_pairs(array $od, array $oi): array
{
    return CaseForm::zip($od, $oi);
}

// Geometría del audiograma SVG de más abajo (dibujado en el navegador, ver
// public/js/case/audiogram.js) -- escala logarítmica en frecuencia (así 3000/6000 caen
// a mitad de camino entre sus octavas, como en un audiograma real) y lineal
// en dB HL, -10 arriba (mejor audición) a 120 abajo. Mismo plot box (32,10)-(312,276)
// que usan drawAudiogram()/xPos()/yPos() en case/audiogram.js -- si se cambia
// acá, cambiar allá también.
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
// drawLogogram()/logoX()/logoY() en case/logogram.js.
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
// mL (0..2.5) -- si se cambia acá, cambiar también en case/tympanogram.js.
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

// Sala: quién viene con el paciente (ver Sala.php). Mismo problema de
// shape que otoscopia -- al editar, $v trae 'acompanantes' ya armado por
// Sala::toForm(); en un submit fallido trae los arrays paralelos crudos del
// POST (sala_rol[], sala_nombre[], ...). Se normaliza acá a una lista de
// filas para que la tabla se dibuje igual en los dos casos.
if (isset($v['acompanantes']) && is_array($v['acompanantes'])) {
    $salaRows = $v['acompanantes'];
} else {
    $salaRows = [];
    foreach (array_keys((array) ($v['sala_rol'] ?? [])) as $i) {
        $campoSala = static fn(string $k, $def = '') => ((array) ($v[$k] ?? []))[$i] ?? $def;
        $salaRows[] = [
            'id' => (string) $campoSala('sala_id'),
            'rol' => (string) $campoSala('sala_rol', 'madre'),
            'nombre' => (string) $campoSala('sala_nombre'),
            'edad' => (string) $campoSala('sala_edad', ''),
            'genero' => (int) $campoSala('sala_genero', 0),
            'interrumpe' => (int) $campoSala('sala_interrumpe', Sala::RASGOS_DEFAULT['interrumpe']),
            'confiabilidad' => (int) $campoSala('sala_confiabilidad', Sala::RASGOS_DEFAULT['confiabilidad']),
            'version' => (string) $campoSala('sala_version'),
            'comportamiento' => (string) $campoSala('sala_comportamiento'),
            'disposicion' => (int) $campoSala('sala_disposicion', 0),
        ];
    }
}
// Escala de sensibilidad (cases.data PatientDisposition / disposicion de
// cada acompañante). Vive acá y no en cada pestaña porque la usan dos: el
// paciente en Anamnesis y cada acompañante en Sala.
$dispOpts = [
    -2 => 'Muy quisquilloso/a (se ofende con facilidad)',
    -1 => 'Algo sensible',
    0 => 'Normal',
    1 => 'Cálido/a y agradecido/a',
    2 => 'Muy positivo/a (elogia con facilidad)',
];
$salaInformante = (string) ($v['sala_informante'] ?? 'p1');
$pacienteConciencia = (string) ($v['paciente_conciencia'] ?? Sala::RASGOS_DEFAULT['conciencia']);
$pacienteConfiabilidad = (string) ($v['paciente_confiabilidad'] ?? Sala::RASGOS_DEFAULT['confiabilidad']);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $formAction = (string) ($v['form_action'] ?? '');

    if ($formAction === 'create_case' || $formAction === 'update_case') {
        $isUpdate = $formAction === 'update_case';
        // Todo el POST -> cases.data pasa por CaseForm. Acá queda solo lo que
        // es HTTP: el gate de form_action de arriba, y el guardado con su
        // redirect de abajo.
        $form = CaseForm::fromPost($v, $pdo, $me, $editId, $isUpdate);
        $error = $form->error;
        $avisosPerfil = $form->avisos;
        $faltantes = $form->faltantes;

        if ($form->ok()) {
            $data = $form->data;
            $id = $form->caseId;
            $age = $form->age;
            $nombre1 = $form->nombre1;
            $apellido1 = $form->apellido1;
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
// El JS de esta página vive en public/js/case/*.js y se emite al final del
// <body> EN ESTE ORDEN (admin_footer). El orden importa: side-color publica
// window.sideColor, que usa todo lo que dibuja; audiogram/logogram/
// tympanogram/reflex-pattern publican window.drawAudiogram y compañía, y
// live-preview las llama apenas carga -- así que van antes que ella.
admin_add_js('case/side-color.js');
admin_add_js('case/age-rut.js');
admin_add_js('case/anamnesis-ai.js');
admin_add_js('case/unsaved-guard.js');
admin_add_js('case/derived-fields.js');
admin_add_js('case/generator.js');
admin_add_js('case/profile-preview.js');
admin_add_js('case/abr.js');
admin_add_js('case/oae.js');
admin_add_js('case/patient-photo.js');
admin_add_js('case/sala.js');
admin_add_js('case/otoscopia.js');
admin_add_js('case/sex-mirror.js');
admin_add_js('case/tabs.js');
admin_add_js('case/tinnitus.js');
admin_add_js('case/audiogram.js');
admin_add_js('case/logogram.js');
admin_add_js('case/tympanogram.js');
admin_add_js('case/reflex-pattern.js');
admin_add_js('case/live-preview.js');
admin_add_js('case/acumetria.js');
admin_add_js('case/fowler.js');
admin_add_js('case/chat-test.js');
admin_header($isEdit ? 'Editar caso clínico ' . $editId : 'Crear caso clínico', $me);
?>

<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if (!empty($faltantes)): ?>
<div class="card pendientes-card">
    <strong>Falta decidir lo que el perfil no puede calcular</strong>
    <ul>
        <?php foreach ($faltantes as $falta): ?>
        <li><a href="#" class="tab-link" data-goto-tab="<?= htmlspecialchars($falta['tab']) ?>"><?= htmlspecialchars($falta['texto']) ?></a></li>
        <?php endforeach; ?>
    </ul>
    <p class="legend help">Esto no es opcional y no se guarda igual: son datos clínicos que ninguna cuenta puede sacar del audiograma. Sin ellos el alumno se encuentra con un paciente que no cierra, y vos no te enterás. Cliqueá cada línea para ir a la pestaña donde se arregla.</p>
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
    <button type="button" class="tab-btn<?= $isEdit ? '' : ' active' ?>" data-tab="armado">Armado rápido</button>
    <span class="tab-group">Quién es</span>
    <button type="button" class="tab-btn<?= $isEdit ? ' active' : '' ?>" data-tab="paciente">1. Paciente</button>
    <button type="button" class="tab-btn" data-tab="sala">2. Sala</button>
    <span class="tab-group">El caso</span>
    <button type="button" class="tab-btn" data-tab="perfil">3. Perfil auditivo</button>
    <span class="tab-group">Exámenes</span>
    <button type="button" class="tab-btn" data-tab="audiometria">4. Audiometría</button>
    <button type="button" class="tab-btn" data-tab="otoscopia">5. Otoscopia</button>
    <button type="button" class="tab-btn" data-tab="timpanometria">6. Timpanometría</button>
    <button type="button" class="tab-btn" data-tab="abr">7. ABR</button>
    <button type="button" class="tab-btn" data-tab="eoas">8. EOA</button>
    <button type="button" class="tab-btn" data-tab="vemp">9. VEMP</button>
    <button type="button" class="tab-btn" data-tab="tinnitus">10. Tinnitus</button>
    <span class="tab-group">Entrevista</span>
    <button type="button" class="tab-btn" data-tab="anamnesis">11. Anamnesis</button>
</div>

<div class="tab-panel<?= $isEdit ? '' : ' active' ?>" data-tab="armado">
<div class="card">
    <strong>Armado rápido</strong>
    <p class="legend help">Se configura todo acá y se genera de una sola vez: el audiograma completo (aérea y ósea, los dos oídos), el timpanograma, la función tubaria, el sitio de la lesión, el patrón retrococlear, las ondas del ABR y las emisiones otoacústicas. Un botón, un caso entero y coherente.</p>
    <p class="legend help">No hay que elegir nada dos veces. Lo que decís acá sobre el oído define todo lo demás por proyección: la OEA sale del componente coclear, los reflejos del oído medio y del sitio de la lesión, los supraliminares del mismo número. Antes había que fijar el grado de la OEA por separado, y era la forma más fácil de armar un caso que se contradice a sí mismo.</p>
    <p class="legend help">Nada de esto es obligatorio ni definitivo: un caso se arma entero a mano, pestaña por pestaña, y lo que el botón escribe queda en los campos de cada pestaña y se edita igual que si lo hubieras tipeado.</p>
</div>

<div class="card">
    <strong>Paciente</strong>
    <p class="legend help">El <strong>sexo</strong> decide el nombre, que lo escribe "Generar caso" junto con el resto -- ya no hay un botón aparte para eso. La <strong>edad</strong> pesa más: fija la fecha de nacimiento y el RUT, elige la población de referencia del ABR --un neonato no tiene las latencias de un adulto--, es obligatoria para la anamnesis con IA, y define <strong>qué es normal</strong> en este paciente (ver abajo).</p>
    <p class="legend help">Son los mismos campos de <a href="#" class="tab-link" data-goto-tab="paciente">Paciente</a>, no una copia: cambiarlos en cualquiera de los dos lados los cambia en el otro. El RUT, la foto y la historia clínica se cargan allá.</p>
    <div class="three-col">
        <label>Sexo
            <select id="armado-gender">
                <option value="0" <?= ($v['gender'] ?? '0') === '0' ? 'selected' : '' ?>>Hombre</option>
                <option value="1" <?= ($v['gender'] ?? '0') === '1' ? 'selected' : '' ?>>Mujer</option>
            </select>
        </label>
        <label>Edad
            <input type="number" id="armado-age" min="0" max="110" value="<?= htmlspecialchars((string) ($v['age'] ?? '')) ?>">
        </label>
    </div>
</div>

<div class="card">
    <strong>El cuadro clínico, oído por oído</strong>
    <p class="legend help"><strong>Cada oído lleva lo suyo.</strong> Un paciente puede tener el OD sano y una otitis en el OI, o una presbiacusia de un lado y un schwannoma del otro. El oído que no tiene nada se pide con "Normal para la edad", que no es un cero.</p>

    <label class="inline-check" style="margin-left:0;">
        <input type="checkbox" id="armado-igualar" checked>
        Los dos oídos iguales
    </label>
    <p class="legend help">Con esto marcado, lo que elijas en el OD se copia al OI --que es el caso de la mayoría de los cuadros bilaterales-- y los dos oídos comparten magnitud, con unos pocos dB de asimetría biológica. Destildalo para un caso unilateral o asimétrico.</p>

    <div class="two-col">
    <?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
        <div class="side-block" data-lado="<?= $lado ?>">
            <div class="side-heading"><strong>Oído <?= $ladoLabel ?></strong></div>
            <label>Categoría
                <select class="perfil-categoria" data-lado="<?= $lado ?>">
                    <?php foreach (CaseProfile::CATEGORIAS as $catKey => $catLabel): ?>
                    <option value="<?= htmlspecialchars($catKey) ?>"><?= htmlspecialchars($catLabel) ?></option>
                    <?php endforeach; ?>
                    <option value="__random__">Cualquiera (al azar)</option>
                </select>
            </label>
            <label>Cuadro
                <select class="perfil-escenario" data-lado="<?= $lado ?>"></select>
            </label>
            <label>Grado
                <select class="perfil-grado" data-lado="<?= $lado ?>">
                    <option value="random">Cualquiera (al azar)</option>
                </select>
            </label>
        </div>
    <?php endforeach; ?>
    </div>

    <p class="legend help">La <strong>categoría</strong> dice dónde está la lesión y filtra los cuadros. El <strong>cuadro</strong> da la forma de la curva; el <strong>grado</strong>, cuánto. Elegido el grado se escala la forma completa --lo sensorioneural y el gap con el mismo factor-- hasta que el promedio caiga en el rango pedido: la proporción entre conductivo y sensorioneural es del cuadro y no cambia con el grado.</p>
    <p class="legend help">Cada cuadro ofrece solo los grados que puede dar sin dejar de ser ese cuadro. Una conductiva pura no pasa de moderada porque la vía ósea le pone techo (más que eso ya es mixta); una muesca de 4 kHz no es una hipoacusia severa por promedio; un descendente puro no llega a severa sin aplanarse.</p>
    <p class="legend help">El grado se mide sobre el <strong>promedio de <?= implode(', ', CaseProfile::GRADE_FREQS) ?> Hz en vía aérea</strong> (BIAP). Audición normal hasta 20 dB HL, así que el leve arranca en 21. <strong>Ojo:</strong> el equipo le muestra al alumno el promedio de Fletcher (mejores 2 de 500, 1000 y 2000), que ignora 4 kHz -- en un descendente el número que él calcule va a dar más bajo que el grado con que armaste el caso. Es la diferencia entre las dos escalas, no un error.</p>

    <div class="section-sep" style="border-top:1px dashed var(--color-border);">
        <button type="button" id="perfil-generar">Generar caso</button>
        <span id="armado-estado" class="legend"></span>
    </div>
    <p class="legend help">Generar <strong>pisa</strong> el audiograma, la timpanometría, el perfil, el ABR y la OEA de los dos oídos, y el nombre del paciente. No toca la edad, el RUT, la foto, la historia clínica, la otoscopia, el tinnitus, el VEMP ni la anamnesis.</p>
    <p class="legend help">Si el paciente es <strong>menor de 18</strong> y la sala está vacía, le agrega la madre: un menor no llega solo, y ella aporta lo que el niño no puede contar por más que hable bien --embarazo, parto, screening neonatal, colegio--. Hasta los 13 la historia la cuenta ella; de 14 a 17 la cuenta el paciente y ella completa. Cuánto se mete y cuánto le creemos varían en cada generación. Si la sala <em>ya</em> tiene gente, no la toca.</p>
    <p class="legend help">Al editar un caso que ya existe, el nombre NO se toca: ahí el nombre es del paciente y cambiarlo afectaría a todas sus otras citas.</p>
    <p class="legend help">Lo que queda para decidir a mano después es lo que ninguna cuenta puede sacar del audiograma: el VEMP, y el detalle fino de la función tubaria. El editor los reclama al guardar si quedaron sin tocar.</p>
</div>

<div class="card">
    <strong>Lo normal depende de la edad</strong>
    <p class="legend help">Un niño de 10 que oye bien da 0 dB en todas las frecuencias. Un hombre de 70 que también oye bien llega a 30 dB en 4 kHz, y sigue siendo <strong>normal para su edad</strong>. Por eso el umbral mediano de <a href="https://www.iso.org/standard/42916.html" target="_blank" rel="noopener">ISO 7029</a> se suma como piso a todos los cuadros, no solo al normal: un señor de 70 con una otitis media tiene la otitis <em>y</em> su presbiacusia.</p>
    <p class="legend help">Esto es lo que hace posible el ejercicio de decidir si una presbiacusia es más de lo esperable para la edad, que con todos los "normales" en 0 no se podía plantear.</p>
    <div id="armado-norma-edad" class="legend"></div>
</div>

<div class="card">
    <strong>Después de generar: la anamnesis con IA</strong>
    <p class="gen-step-dest">Escribe en <a href="#" class="tab-link" data-goto-tab="anamnesis">11. Anamnesis</a></p>
    <p class="legend help"><strong>Esto va al final, aparte, y a propósito.</strong> El modelo escribe los antecedentes que EXPLICAN los hallazgos que ya están cargados: una muesca en 4 kHz pide exposición a ruido, una otitis a repetición pide una conductiva con timpanograma B, una neuropatía en un recién nacido pide hiperbilirrubinemia. Con la ficha vacía no tiene nada que explicar, así que se aprieta después de generar el caso y de revisarlo.</p>
    <p class="legend help">No inventa el diagnóstico ni menciona umbrales -- eso lo tiene que medir el alumno. Las derivaciones las escribe por el estudio ("se deriva a evaluación auditiva", "a BERA"), nunca por la profesión de quien atiende. Las <strong>atenciones previas</strong> no salen de acá: se escriben a mano en Historia clínica (<a href="#" class="tab-link" data-goto-tab="paciente">Paciente</a>), con las fechas relativas <code>{{-N}}</code>.</p>
    <p class="legend help"><strong>Es un borrador y hay que leerlo.</strong> El modelo puede inventar una cirugía que no existe o un fármaco que no es ototóxico, y eso le llega al alumno como parte del caso, indistinguible de lo que escribiste vos. Al terminar te deja en <a href="#" class="tab-link" data-goto-tab="anamnesis">Anamnesis</a> para que lo leas: hasta que tildes la verificación ahí, el caso no se guarda.</p>
    <button type="button" class="secondary" id="anamnesis-ia-btn">Redactar borrador con IA</button>
    <span id="anamnesis-ia-estado" class="legend"></span>
    <input type="hidden" name="anamnesis_ia[generado]" id="anamnesis-ia-generado" value="<?= fv($v, ['anamnesis_ia', 'generado'], '') ? '1' : '' ?>">
    <input type="hidden" name="anamnesis_ia[generado_en]" id="anamnesis-ia-generado-en" value="<?= htmlspecialchars((string) fv($v, ['anamnesis_ia', 'generado_en'], '')) ?>">
</div>
</div>

<div class="tab-panel<?= $isEdit ? ' active' : '' ?>" data-tab="paciente">
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
    <p class="legend help">El nombre al azar se genera desde <a href="#" class="tab-link" data-goto-tab="armado">Armado rápido</a>, junto con el resto de los autocompletados.</p>
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
        <textarea name="historia_clinica" rows="6" class="input" placeholder="{{-20}} Nace de 38 semanas, parto vaginal, 3.240 g. Screening auditivo: refiere OD.&#10;{{-5}} Control con pediatra, se deriva a evaluación auditiva."><?= htmlspecialchars((string) ($v['historia_clinica'] ?? '')) ?></textarea>
    </label>
    <p class="legend" class="help">Las <strong>atenciones previas</strong> del paciente: qué le hicieron antes de llegar acá y qué se encontró, una por línea y de la más antigua a la más reciente. Es del <strong>paciente</strong>, no del caso. No incluye las notas individuales de cada alumno por atención -- esas se ven en la agenda/asistencia, no se editan acá.</p>
    <p class="legend" class="help">Las fechas no se escriben a mano: poné <code>{{-N}}</code> al principio de la línea, donde N son los <strong>días antes</strong> de la cita que va a atender el alumno, y la app lo reemplaza por la fecha real. Así el mismo caso sirve en cualquier fecha. Ejemplos: <code>{{-5}}</code> hace cinco días, <code>{{-30}}</code> hace un mes, <code>{{-730}}</code> hace dos años. En un recién nacido, el nacimiento es la primera línea: <code>{{-20}} Nace de 38 semanas, parto vaginal, 3.240 g. Screening auditivo: refiere OD.</code></p>

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

<div class="tab-panel" data-tab="sala">
<div class="card">
    <strong>Sala de atención</strong>
    <p class="legend help">Quiénes vienen con el paciente. Un lactante no cuenta su historia: la cuenta la madre. Y hay adultos que niegan lo que el acompañante ve todos los días -- ese desacuerdo <em>es</em> el hallazgo clínico del caso, y el alumno tiene que darse cuenta de a quién le está preguntando.</p>
    <p class="legend help">El alumno no elige a quién le habla con un menú: lo dice escribiendo ("mamita, ¿su hijo escucha bien?", "prefiero que me conteste él") y responde quien corresponda. Un caso sin acompañantes se comporta exactamente como antes: una conversación con el paciente y nadie más.</p>

    <div class="section-sep" style="border-top:1px dashed var(--color-border);">
        <strong>El paciente en la entrevista</strong>
        <p class="legend help">Su comportamiento y su sensibilidad se editan en la pestaña Anamnesis. Acá va solo lo que cambia cuando viene acompañado.</p>
        <div class="two-col">
            <label>Conciencia de su problema (0-100)
                <input type="number" name="paciente_conciencia" min="0" max="100" value="<?= htmlspecialchars($pacienteConciencia) ?>">
            </label>
            <label>Confiabilidad de su relato (0-100)
                <input type="number" name="paciente_confiabilidad" min="0" max="100" value="<?= htmlspecialchars($pacienteConfiabilidad) ?>">
            </label>
        </div>
        <p class="legend">Bajo <?= Sala::CONCIENCIA_BAJA ?> de conciencia el paciente niega o minimiza lo suyo ("yo escucho bien, hablan bajo") y el acompañante que sí lo nota se mete a corregirlo. Bajo <?= Sala::CONFIABILIDAD_BAJA ?> de confiabilidad confunde fechas y detalles, pero los cuenta con seguridad.</p>
        <label class="inline-check">
            <input type="radio" name="sala_informante" value="p1" <?= $salaInformante === 'p1' ? 'checked' : '' ?>> El paciente es quien cuenta la historia
        </label>
        <p class="legend">Quien lleva la voz cantante: el que contesta cuando el alumno pregunta al aire, sin dirigirse a nadie. En un lactante no puede ser el paciente.</p>
    </div>
</div>

<div class="card">
    <strong>Acompañantes</strong>
    <p class="legend help">Cada uno responde por sí mismo, con su propia foto y su propia versión. Sabe lo que el paciente no puede saber: fechas, remedios, cómo fue el parto.</p>
    <p class="legend">La tendencia a interrumpir es lo que decide si esta persona contesta por el paciente o espera su turno.</p>
    <?php
    // Una sola definición de fila para los dos usos: las que ya tiene el
    // caso y la plantilla que clona el navegador al agregar a alguien. El
    // id de persona es lo que amarra la foto (ver PatientPhoto::key), así
    // que en la plantilla va como marcador y el JS lo reemplaza por uno
    // nuevo -- si dependiera de la posición, borrar una fila de más arriba
    // le correría la cara a todos los demás.
    $salaRowHtml = static function (array $ac, string $pid) use ($photoCaseId, $salaInformante, $dispOpts): string {
        $hasFoto = $pid !== '__ID__' && PatientPhoto::hasAvatar(PatientPhoto::key($photoCaseId, $pid));
        ob_start();
        ?>
        <div class="sala-row" data-persona="<?= htmlspecialchars($pid) ?>" style="border:1px solid var(--color-border); border-radius:var(--radius-md); padding:0.8rem; margin-bottom:0.8rem;">
            <input type="hidden" name="sala_id[]" value="<?= htmlspecialchars($pid) ?>">
            <div class="three-col">
                <label>Qué es del paciente
                    <select name="sala_rol[]">
                        <?php foreach (Sala::ROLES as $rolKey => $rolLabel): ?>
                            <?php if ($rolKey === 'paciente') { continue; } ?>
                            <option value="<?= $rolKey ?>" <?= ((string) ($ac['rol'] ?? 'madre')) === $rolKey ? 'selected' : '' ?>><?= htmlspecialchars($rolLabel) ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
                <label>Nombre
                    <input type="text" name="sala_nombre[]" value="<?= htmlspecialchars((string) ($ac['nombre'] ?? '')) ?>">
                </label>
                <label>Edad
                    <input type="number" name="sala_edad[]" min="0" max="110" value="<?= htmlspecialchars((string) ($ac['edad'] ?? '')) ?>">
                </label>
            </div>
            <div class="three-col">
                <label>Género
                    <select name="sala_genero[]">
                        <option value="0" <?= (int) ($ac['genero'] ?? 0) === 0 ? 'selected' : '' ?>>Hombre</option>
                        <option value="1" <?= (int) ($ac['genero'] ?? 0) === 1 ? 'selected' : '' ?>>Mujer</option>
                    </select>
                </label>
                <label>Tendencia a contestar por el paciente (0-100)
                    <input type="number" name="sala_interrumpe[]" min="0" max="100" value="<?= htmlspecialchars((string) ($ac['interrumpe'] ?? Sala::RASGOS_DEFAULT['interrumpe'])) ?>">
                </label>
                <label>Confiabilidad de su relato (0-100)
                    <input type="number" name="sala_confiabilidad[]" min="0" max="100" value="<?= htmlspecialchars((string) ($ac['confiabilidad'] ?? Sala::RASGOS_DEFAULT['confiabilidad'])) ?>">
                </label>
            </div>
            <label>Su versión de los hechos
                <textarea name="sala_version[]" rows="2" class="input" placeholder="Ej: no escucha nada hace años, sube la tele al máximo y contesta cualquier cosa."><?= htmlspecialchars((string) ($ac['version'] ?? '')) ?></textarea>
            </label>
            <p class="legend">Lo que ESTA persona sostiene, aunque el paciente diga otra cosa. Con esto escrito, se mete a contradecir cuando el tema sale en la conversación.</p>
            <div class="two-col">
                <label>Comportamiento
                    <input type="text" name="sala_comportamiento[]" value="<?= htmlspecialchars((string) ($ac['comportamiento'] ?? '')) ?>" placeholder="Ej: ansiosa, contesta por él, apurada...">
                </label>
                <label>Sensibilidad
                    <select name="sala_disposicion[]">
                        <?php foreach ($dispOpts as $dVal => $dLabel): ?>
                            <option value="<?= $dVal ?>" <?= (int) ($ac['disposicion'] ?? 0) === $dVal ? 'selected' : '' ?>><?= htmlspecialchars($dLabel) ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
            </div>
            <div style="display:flex; align-items:center; gap:1rem; margin-top:0.6rem;">
                <img class="patient-avatar sala-avatar" src="patient_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;persona=<?= urlencode($pid) ?>&amp;type=avatar&amp;v=<?= time() ?>" alt="" <?= $hasFoto ? '' : 'hidden' ?>>
                <div class="patient-avatar patient-avatar-empty sala-avatar-empty" <?= $hasFoto ? 'hidden' : '' ?>>Sin foto</div>
                <div>
                    <input type="file" class="sala-photo-input" data-persona="<?= htmlspecialchars($pid) ?>" accept="image/jpeg,image/png,image/webp">
                    <label class="inline-check">
                        <input type="radio" name="sala_informante" value="<?= htmlspecialchars($pid) ?>" <?= $salaInformante === $pid ? 'checked' : '' ?>> Es quien cuenta la historia
                    </label>
                </div>
                <button type="button" class="secondary sala-remove" style="margin-left:auto;">Quitar</button>
            </div>
        </div>
        <?php
        return (string) ob_get_clean();
    };
    ?>
    <div id="sala-rows">
        <?php foreach ($salaRows as $idx => $ac): ?>
            <?= $salaRowHtml($ac, (string) ($ac['id'] ?? ('p' . ($idx + 2)))) ?>
        <?php endforeach; ?>
    </div>
    <template id="sala-row-tpl"><?= $salaRowHtml([], '__ID__') ?></template>
    <button type="button" id="sala-add" class="secondary">Agregar acompañante</button>
    <p class="legend">La foto se puede subir apenas se agrega la fila, antes de guardar el caso.</p>
</div>
</div>

<div class="tab-panel" data-tab="perfil">
<div class="card">
    <strong>Perfil auditivo</strong>
    <p class="legend help">Dónde está la lesión de este paciente. El audiograma (pestaña Audiometría) ya dice cuánta pérdida hay y cuánta es conductiva, frecuencia por frecuencia; lo único que no puede decir es qué parte del componente sensorioneural es coclear y qué parte es retrococlear. Eso se define acá, una vez, y desde acá se proyecta a los exámenes que tengan la casilla de derivación encendida.</p>
    <p class="legend help">Sin ninguna casilla marcada nada cambia: cada pestaña se sigue cargando a mano, como siempre. La derivación existe para que el caso no se contradiga solo (una OEA normal con un gap de 40 dB, un ABR normal con un audiograma profundo), no para impedir armar un caso incoherente a propósito -- el Stenger, la falsa onda V y la simulación necesitan esa incoherencia.</p>
    <p class="legend help">El cuadro clínico de cada oído (que escribe el audiograma, el sitio de la lesión, el timpanograma y estas mismas casillas) se genera desde <a href="#" class="tab-link" data-goto-tab="armado">Armado rápido</a>. Acá se edita el resultado, o se arma el perfil a mano.</p>

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
<?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
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
        <span><svg width="12" height="12"><circle cx="6" cy="6" r="4" fill="none" class="sym-od" stroke-width="1.4"></circle></svg> Aérea OD</span>
        <span><svg width="12" height="12"><polygon points="6,2 2,10 10,10" fill="none" class="sym-od" stroke-width="1.4"></polygon></svg> Aérea OD enmasc.</span>
        <span><svg width="12" height="12"><line x1="2" y1="2" x2="10" y2="10" class="sym-oi" stroke-width="1.4"></line><line x1="2" y1="10" x2="10" y2="2" class="sym-oi" stroke-width="1.4"></line></svg> Aérea OI</span>
        <span><svg width="12" height="12"><rect x="2" y="2" width="8" height="8" fill="none" class="sym-oi" stroke-width="1.4"></rect></svg> Aérea OI enmasc.</span>
        <span><svg width="12" height="12"><polyline points="9,2 3,6 9,10" fill="none" class="sym-od" stroke-width="1.4"></polyline></svg> Ósea OD</span>
        <span><svg width="12" height="12"><polyline points="8,2 3,2 3,10 8,10" fill="none" class="sym-od" stroke-width="1.4"></polyline></svg> Ósea OD enmasc.</span>
        <span><svg width="12" height="12"><polyline points="3,2 9,6 3,10" fill="none" class="sym-oi" stroke-width="1.4"></polyline></svg> Ósea OI</span>
        <span><svg width="12" height="12"><polyline points="4,2 9,2 9,10 4,10" fill="none" class="sym-oi" stroke-width="1.4"></polyline></svg> Ósea OI enmasc.</span>
        <span><svg width="12" height="12"><polygon points="6,9 2,3 10,3" class="sym-od-fill" stroke="none"></polygon></svg> LDL OD</span>
        <span><svg width="12" height="12"><polygon points="6,9 2,3 10,3" class="sym-oi-fill" stroke="none"></polygon></svg> LDL OI</span>
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
        <?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
        <tr>
            <td class="side-label">Rinne <?= $ladoLabel ?></td>
            <?php foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $freqIdx):
                $rinneVal = (string) fv($v, ['rinne', $hz, $lado], 'positivo');
            ?>
            <td>
                <select id="rinne_<?= $freqIdx ?>_<?= $lado ?>" class="rinne-select" data-freq="<?= $freqIdx ?>" data-side="<?= $lado ?>"
                        name="rinne[<?= $hz ?>][<?= $lado ?>]" <?= $acumetriaIsAuto ? 'disabled' : '' ?>>
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
                <input type="number" step="5" class="umd-int-input" data-side="<?= $lado ?>" name="umd_int[<?= $lado ?>]" value="<?= htmlspecialchars((string) fv($v, ['umd_int', $lado], 35)) ?>" class="input input--narrow" style="display:inline-block;">
                / <input type="number" step="4" class="umd-pct-input" data-side="<?= $lado ?>" name="umd_pct[<?= $lado ?>]" value="<?= htmlspecialchars((string) fv($v, ['umd_pct', $lado], 100)) ?>" class="input input--narrow" style="display:inline-block;">
            </label>
            <label>SISI <input type="number" step="5" name="sisi[<?= $lado ?>]" value="<?= htmlspecialchars((string) fv($v, ['sisi', $lado], 0)) ?>"></label>
            <label class="inline-check"><input type="checkbox" name="stenger[<?= $lado ?>]" <?= isset($v['stenger'][$lado]) ? 'checked' : '' ?>> Stenger</label>
            <label class="inline-check"><input type="checkbox" class="recruit-toggle" data-side="<?= $lado ?>" name="recruit[<?= $lado ?>]" <?= isset($v['recruit'][$lado]) ? 'checked' : '' ?>> Reclutamiento</label>
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
                <?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
                <div class="otoscopia-photo-slot">
                    <span class="side-tag <?= $lado ?>"><?= $ladoLabel ?></span><br>
                    <?php $hasOto = OtoscopiaPhoto::has($photoCaseId, $lado, $faseIdx); ?>
                    <img class="otoscopia-thumb" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>"
                         src="otoscopia_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;side=<?= $lado ?>&amp;fase=<?= $faseIdx ?>&amp;v=<?= time() ?>"
                         alt="Otoscopia <?= $ladoLabel ?> fase <?= $faseIdx + 1 ?>" <?= $hasOto ? '' : 'hidden' ?>>
                    <div class="otoscopia-thumb-empty" <?= $hasOto ? 'hidden' : '' ?>>Sin imagen</div>
                    <input type="file" class="otoscopia-photo-input" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>" accept="image/jpeg,image/png,image/webp">
                    <button type="button" class="secondary otoscopia-delete-photo" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>" <?= $hasOto ? '' : 'hidden' ?>>Borrar foto</button>
                    <a class="otoscopia-download-photo" href="otoscopia_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;side=<?= $lado ?>&amp;fase=<?= $faseIdx ?>&amp;download=1" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>" <?= $hasOto ? '' : 'hidden' ?>>Descargar</a>
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

<div class="tab-panel" data-tab="abr">
<?php $abrAuthorCatalog = AppConfig::getEffective('abr_reference_authors', null) ?? []; ?>
<div class="card">
    <strong>Autor de referencia</strong>
    <p class="legend help">Set normativo con el que se calculan las ondas, uno solo para todo el paciente. Cada autor reporta baselines de latencia y amplitud levemente distintos según la población -- se configuran en <a href="normativas.php">Configuración &rsaquo; Normativas</a>. No queda guardado en el caso, solo se usa para calcular; los números finales sí quedan en cada campo.</p>
    <label style="max-width:22em;">Autor
        <select id="abr-author-select">
            <option value="__default__">LabSim (default)</option>
            <?php foreach ($abrAuthorCatalog as $authorId => $author): ?>
            <option value="<?= htmlspecialchars($authorId) ?>"><?= htmlspecialchars($author['label'] ?? $authorId) ?></option>
            <?php endforeach; ?>
        </select>
    </label>
    <p class="legend help">Las ondas ya las escribió <a href="#" class="tab-link" data-goto-tab="armado">Armado rápido</a> al generar el caso. Los botones de acá abajo son para volver a sortearlas de un oído sin regenerar todo -- por ejemplo después de cambiar el autor.</p>
</div>
<div class="two-col">
<?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
<div class="card">
    <strong>ABR <?= $ladoLabel ?></strong>
    <p class="legend help">Patología de este oído para el generador de curvas ABR -- no es el resultado del alumno, es lo que el caso simula. Si se deja "Normal" con todo en 0, el oído no tiene hallazgos.</p>
    <p class="derivado-aviso" data-derivado="abr" hidden>La patología y el umbral de este oído los escribe el <a href="#" class="tab-link" data-goto-tab="perfil">Perfil auditivo</a>, porque la casilla <em>ABR: umbral por estímulo</em> está encendida: quedan grises y se recalculan al guardar. Para editarlos a mano hay que apagar esa casilla.</p>

    <p class="legend help">Latencias y amplitudes onda por onda. "Volver a sortear" toma la patología y el umbral que ya tiene este oído --que los fija el perfil, no este botón-- y le calcula ondas plausibles con el sexo, la edad y el autor de referencia. Es un punto de partida al azar: cualquier campo se edita después.</p>
    <button type="button" class="secondary abr-autofill-btn" data-lado="<?= $lado ?>" style="margin-top:0;">Volver a sortear las ondas de este oído</button>
    <div class="three-col">
        <label>Patología
            <select name="abr[<?= $lado ?>][type]" class="abr-type-select" data-lado="<?= $lado ?>">
                <?php foreach (CaseBuilder::ABR_TYPE_OPTIONS as $opt): ?>
                <option value="<?= $opt ?>" <?= ($v['abr'][$lado]['type'] ?? 'normal') === $opt ? 'selected' : '' ?>><?= ucfirst($opt) ?></option>
                <?php endforeach; ?>
            </select>
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
            <strong class="od-text">OD</strong>
            <div id="abr-preview-od" class="abr-preview"></div>
        </div>
        <div>
            <strong class="oi-text">OI</strong>
            <div id="abr-preview-oi" class="abr-preview"></div>
        </div>
    </div>
</div>
</div>

<div class="tab-panel" data-tab="eoas">
<div class="two-col">
<?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
<div class="card">
    <strong>EOA <?= $ladoLabel ?></strong>
    <p class="legend help">Patología de este oído para el generador de Emisiones Otoacústicas (TEOAE/DPOAE/SOAE/SFOAE). "Coclear" y "Transmisión" atenúan la OEA según el umbral (a mayor umbral, más atenuada -- por sobre ~35-40 dB suele quedar bajo el noise floor, REFER). "Neural" deja la OEA normal aunque el umbral esté elevado: la cóclea está intacta, es el contraste clínico con ABR.</p>
    <p class="derivado-aviso" data-derivado="eoas" hidden>La patología, el umbral y el perfil por frecuencia de este oído los escribe el <a href="#" class="tab-link" data-goto-tab="perfil">Perfil auditivo</a>, porque la casilla <em>OEA: perfil por frecuencia</em> está encendida: quedan grises y se recalculan al guardar. Para editarlos a mano hay que apagar esa casilla.</p>
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
    <p class="legend help">El umbral y el perfil por frecuencia los escribe el perfil auditivo, derivados del audiograma y del componente coclear: no hay que elegir el grado de la OEA aparte, y por eso este oído no puede contradecir a su propia audiometría. Lo que el botón sortea son las <strong>condiciones de registro</strong> (ruido del paciente, sello de la sonda, variabilidad), que sí son del caso y no se derivan de nada.</p>
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
    <p class="legend help">"Auto" deja que el cliente decida al azar si este oído tiene SOAE (~45%, algo más en OD) -- estable para el mismo caso, pero no se puede saber de antemano. Para mostrarlas en clase o evaluar sobre un hallazgo fijo usá "Presentes" y cargá los picos: frecuencia en Hz y nivel de la emisión (los SOAE reales rondan 0 dB SPL, rara vez pasan 20; en blanco toma <?= CaseBuilder::EOAS_SOAE_DEFAULT_PEAK_DB ?> dB SPL). "Presentes" sin picos cargados = el cliente los genera al azar pero garantiza al menos uno. Los picos cargados NO se atenúan por patología ni por sello: el nivel que pongas es el que se va a ver, aunque el ruido del paciente igual puede taparlos. "Ausentes" fuerza un registro sin SOAE (lo normal en coclear/transmisión, y también posible en un oído sano).</p>
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

<div class="tab-panel" data-tab="vemp">
<div class="two-col">
<?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
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
</div>
</div>

<div class="tab-panel" data-tab="anamnesis">
<div class="card">
    <strong>El borrador de IA hay que leerlo</strong>
    <p class="legend help">Lo escribe el modelo desde <a href="#" class="tab-link" data-goto-tab="armado">Armado rápido</a> y queda en los campos de abajo. Puede inventar una cirugía que no existe o un fármaco que no es ototóxico, y eso le llega al alumno como parte del caso, indistinguible de lo que escribiste vos.</p>
    <div id="anamnesis-ia-verificacion" <?= fv($v, ['anamnesis_ia', 'generado'], '') ? '' : 'hidden' ?> style="border-left:4px solid var(--color-danger); padding-left:0.6rem; margin-top:0.6rem;">
        <label class="inline-check">
            <input type="checkbox" name="anamnesis_ia[verificado]" id="anamnesis-ia-verificado" value="1" <?= fv($v, ['anamnesis_ia', 'verificado'], '') ? 'checked' : '' ?>>
            Leí el borrador y verifico que es clínicamente correcto para este caso
        </label>
        <?php if (fv($v, ['anamnesis_ia', 'verificado_por'], '')): ?>
        <p class="legend help">Verificado por <?= htmlspecialchars((string) fv($v, ['anamnesis_ia', 'verificado_por'], '')) ?><?= fv($v, ['anamnesis_ia', 'verificado_en'], '') ? ' el ' . htmlspecialchars((string) fv($v, ['anamnesis_ia', 'verificado_en'], '')) : '' ?>.</p>
        <?php endif; ?>
        <p class="legend help">Volver a generar borra la verificación: el texto nuevo no lo leyó nadie. Hasta que esté tildada, el caso no se guarda.</p>
    </div>
    <p class="legend" id="anamnesis-ia-estado-eco" hidden></p>
    <p class="legend help" id="anamnesis-ia-sin-borrador" <?= fv($v, ['anamnesis_ia', 'generado'], '') ? 'hidden' : '' ?>>Este caso no tiene borrador de IA pendiente: lo de abajo se escribió a mano.</p>
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
// Lo único que el JS de esta página no puede sacar de un archivo estático:
// las constantes que vive del lado servidor (CaseBuilder/CaseProfile) y el id
// del caso. El resto está en public/js/case/*.js -- ver los admin_add_js() de
// más arriba, que los emiten en ese orden al final del <body>. Si se agrega
// una constante acá, se lee como window.CASE_CONST.<clave> allá.
window.CASE_CONST = <?= json_encode([
    'csrf' => Auth::csrfToken(),
    'caseId' => $photoCaseId,
    'freqs' => CaseBuilder::FREQUENCIES,
    'histCheckboxes' => CaseBuilder::HIST_CHECKBOXES,
    'nombres' => CaseBuilder::nameBank(),
    'otoscopiaMaxFases' => CaseBuilder::OTOSCOPIA_MAX_FASES,
    'rinneGap' => CaseBuilder::RINNE_GAP_THRESHOLD,
    'weberAsym' => CaseBuilder::WEBER_ASYMMETRY_THRESHOLD,
    // implode/array_values: ACUMETRIA_FREQS es Hz => índice, al JS solo le
    // sirven los índices.
    'acumetriaFreqIdx' => array_values(CaseBuilder::ACUMETRIA_FREQS),
    'neuralParams' => array_keys(CaseBuilder::ABR_NEURAL_DEFAULTS),
    'neuralDefaults' => CaseBuilder::ABR_NEURAL_DEFAULTS,
    'abrNeuralPresets' => CaseBuilder::ABR_NEURAL_PRESETS,
    'abrAuthorCatalog' => $abrAuthorCatalog,
    'eoasFreqs' => CaseBuilder::EOAS_FREQS,
    'eoasShapes' => CaseBuilder::EOAS_AUTOFILL_SHAPES,
    'eoasGrades' => CaseBuilder::EOAS_AUTOFILL_GRADES,
    'eoasJitter' => CaseBuilder::EOAS_AUTOFILL_JITTER_DB,
    'eoasMaxAtten' => CaseBuilder::EOAS_MAX_PATHOLOGY_ATTEN_DB,
    'escenarios' => CaseProfile::SCENARIOS,
    'categorias' => CaseProfile::CATEGORIAS,
    'grades' => CaseProfile::GRADES,
    'gradeFreqs' => CaseProfile::GRADE_FREQS,
    'iso7029' => CaseProfile::ISO7029_COEF,
    'iso7029EdadBase' => CaseProfile::ISO7029_EDAD_BASE,
    'autoModules' => CaseProfile::AUTO_MODULES,
    'decayModes' => array_keys(CaseProfile::DECAY_FREQ_IDX),
], JSON_UNESCAPED_UNICODE | JSON_HEX_TAG) ?>;
</script>
<?php
admin_footer();
