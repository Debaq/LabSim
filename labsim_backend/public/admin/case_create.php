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

// Catálogo de autores de referencia del ABR. Vivía dentro de la ficha ABR,
// pero lo leen dos: esa ficha y el window.CASE_CONST del final. Ahora que la
// ficha es un include, una variable asignada ahí adentro y leída afuera sería
// una dependencia invisible -- se declara acá, antes de las dos. Va después
// del POST y no antes: un guardado exitoso redirige sin dibujar el formulario,
// y esta consulta no haría falta.
$abrAuthorCatalog = AppConfig::getEffective('abr_reference_authors', null) ?? [];
// Normativa VEMP del curso (courses.php -> "Normativa VEMP"): pisa lat/amp
// por pico y subtipo. La vista previa tiene que dibujar con la del curso,
// que es la que va a usar el equipo -- ver VEMP_generator_v1, que la aplica
// después de calcular las ondas.
$vempBaselineOverride = AppConfig::getEffective('normative_data.vemp', null) ?? [];

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
admin_add_js('case/vemp.js');
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
    <p class="help">Esto no es opcional y no se guarda igual: son datos clínicos que ninguna cuenta puede sacar del audiograma. Sin ellos el alumno se encuentra con un paciente que no cierra, y vos no te enterás. Cliqueá cada línea para ir a la pestaña donde se arregla.</p>
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
    <p class="help">Corregí lo que corresponda, o marcá la casilla y volvé a guardar si la incoherencia es parte del ejercicio (simulación, Stenger, falsa onda V).</p>
</div>
<?php endif; ?>

<form method="post" id="case-form">
<?= csrf_field() ?>
<?php if ($isEdit): ?><input type="hidden" name="case_id" value="<?= htmlspecialchars($editId) ?>">
<?php else: ?><input type="hidden" name="upload_temp_id" value="<?= htmlspecialchars($uploadTempId) ?>">
<?php endif; ?>
<?php $photoCaseId = $isEdit ? $editId : $uploadTempId; ?>
<div class="tabs" role="tablist">
    <div class="tab-group">
        <span class="tab-group-label">Empezar acá</span>
        <div class="tab-group-btns">
            <button type="button" class="tab-btn<?= $isEdit ? '' : ' active' ?>" data-tab="armado">Armado rápido</button>
        </div>
    </div>
    <div class="tab-group">
        <span class="tab-group-label">Quién es</span>
        <div class="tab-group-btns">
            <button type="button" class="tab-btn<?= $isEdit ? ' active' : '' ?>" data-tab="paciente">1. Paciente</button>
            <button type="button" class="tab-btn" data-tab="sala">2. Sala</button>
        </div>
    </div>
    <div class="tab-group">
        <span class="tab-group-label">El caso</span>
        <div class="tab-group-btns">
            <button type="button" class="tab-btn" data-tab="perfil">3. Perfil auditivo</button>
        </div>
    </div>
    <div class="tab-group">
        <span class="tab-group-label">Exámenes</span>
        <div class="tab-group-btns">
            <button type="button" class="tab-btn" data-tab="audiometria">4. Audiometría</button>
            <button type="button" class="tab-btn" data-tab="otoscopia">5. Otoscopia</button>
            <button type="button" class="tab-btn" data-tab="timpanometria">6. Timpanometría</button>
            <button type="button" class="tab-btn" data-tab="abr">7. ABR</button>
            <button type="button" class="tab-btn" data-tab="eoas">8. EOA</button>
            <button type="button" class="tab-btn" data-tab="vemp">9. VEMP</button>
            <button type="button" class="tab-btn" data-tab="tinnitus">10. Tinnitus</button>
        </div>
    </div>
    <div class="tab-group">
        <span class="tab-group-label">Entrevista</span>
        <div class="tab-group-btns">
            <button type="button" class="tab-btn" data-tab="anamnesis">11. Anamnesis</button>
        </div>
    </div>
</div>

<?php include __DIR__ . '/../../views/case/_armado.php'; ?>
<?php include __DIR__ . '/../../views/case/_paciente.php'; ?>
<?php include __DIR__ . '/../../views/case/_sala.php'; ?>
<?php include __DIR__ . '/../../views/case/_perfil.php'; ?>
<?php include __DIR__ . '/../../views/case/_audiometria.php'; ?>
<?php include __DIR__ . '/../../views/case/_otoscopia.php'; ?>
<?php include __DIR__ . '/../../views/case/_timpanometria.php'; ?>
<?php include __DIR__ . '/../../views/case/_abr.php'; ?>
<?php include __DIR__ . '/../../views/case/_eoas.php'; ?>
<?php include __DIR__ . '/../../views/case/_vemp.php'; ?>
<?php include __DIR__ . '/../../views/case/_tinnitus.php'; ?>
<?php include __DIR__ . '/../../views/case/_anamnesis.php'; ?>


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
        <p class="help" style="text-align:center;">Arrastra para mover, usa el control para acercar/alejar.</p>
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
        <p class="help" style="text-align:center;">Arrastra para mover, usa el control para acercar/alejar.</p>
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
    'vempSubtipos' => CaseBuilder::VEMP_SUBTIPOS,
    'vempPeaks' => CaseBuilder::VEMP_PEAKS,
    'vempDefaults' => CaseBuilder::VEMP_DEFAULTS,
    // Mismo JSON que carga VEMPGeneratorV1 en la app (fuera de public/: no
    // se puede pedir por HTTP, viaja serializado acá, igual que el banco de
    // nombres) -- lo usa la vista previa de la ficha VEMP.
    'vempNormative' => CaseBuilder::vempNormative(),
    'vempBaselineOverride' => $vempBaselineOverride,
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
