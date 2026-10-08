<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/ReportFile.php';

/**
 * Sube (o rehace) el informe de un módulo "de examen" (ABR/EOA/VEMP/
 * electrococleo/otoscopia) para una atención propia -- ver tabla `reports` en
 * schema.sql. multipart/form-data:
 *   appointment_id (int), tipo (string), data (JSON string),
 *   image_0 / image_1 / image_lat_int (archivos JPEG, todos opcionales --
 *   el módulo manda los que tenga).
 *
 * Recibe appointment_id (no attendance_id): el cliente de escritorio es
 * offline-first y no siempre conoce el id interno de attendances (fila
 * creada por attendance_action.php, puede sincronizarse un rato después de
 * que el alumno empieza a atender) -- acá se resuelve con
 * (appointment_id, student_id=el del token), igual que hace el resto de la
 * app para todo lo demás.
 *
 * Solo guarda datos+imágenes -- el PDF NO se arma acá. Se genera la
 * primera vez que alguien lo pide (ver report_pdf.php) y queda cacheado en
 * disco: evita rehacer el PDF en cada guardado intermedio del alumno
 * cuando probablemente nadie lo va a descargar todavía.
 *
 * Mientras attendances.estado siga 'atendiendo' esto es un upsert libre
 * (el alumno puede rehacer el informe cuantas veces quiera). Una vez
 * 'atendido' queda fijo para todos los exámenes: rechaza con 409 en vez de
 * sobreescribir. (Hasta 2026-09-24 el ABR/electrococleo aceptaba marcas y
 * conclusiones después de cerrar; se sacó: cerrada la atención, no se
 * actualiza nada.)
 *
 * Opcional: version_base (int), ver reports.version / report_versions.
 * Responde {ok, report_id, version}.
 */

const REPORT_TIPOS = ['ABR', 'AABR', 'EOA', 'VEMP', 'ELECTROCOCLEO', 'OTOSCOPIA'];
// '0'/'1'/'lat_int': OD/OI/latencia-intensidad de ABR y VEMP. Los
// <prueba>_<oido> son de EOA, que no tiene "un" gráfico por oído sino uno
// por prueba (TEOAE/DPOAE/SOAE/SFOAE) y oído -- ver OaeMainWindow.
const REPORT_IMAGE_SUFFIXES = [
    '0', '1', 'lat_int',
    'teoae_od', 'teoae_oi', 'dpoae_od', 'dpoae_oi',
    'soae_od', 'soae_oi', 'sfoae_od', 'sfoae_oi',
];

$user = Auth::requireUser();

$appointmentId = (int) ($_POST['appointment_id'] ?? 0);
$tipo = (string) ($_POST['tipo'] ?? '');
$dataRaw = (string) ($_POST['data'] ?? '');

if ($appointmentId <= 0) {
    Response::error('Falta appointment_id.', 400);
}
if (!in_array($tipo, REPORT_TIPOS, true)) {
    Response::error('tipo inválido.', 400);
}
$data = json_decode($dataRaw, true);
if (!is_array($data)) {
    Response::error('Falta data (JSON) del informe.', 400);
}

$pdo = Db::get();
// Si la tabla no se pudo poner al día, se guarda como antes de las
// versiones: un informe que no se guarda es peor que uno sin versión.
$versionado = Db::ensureReportVersioning();

$stmt = $pdo->prepare(
    'SELECT id, estado FROM attendances WHERE appointment_id = ? AND student_id = ?'
);
$stmt->execute([$appointmentId, $user['id']]);
$attendance = $stmt->fetch();

if (!$attendance) {
    // Puede ser que attendance_action.php (estado 'atendiendo') todavía no
    // haya sincronizado desde el cliente -- quien llama (AbrMainWindow)
    // trata esto como "reintentar más tarde", no como error fatal.
    Response::error('Todavía no hay una atención registrada para esa cita.', 404);
}
$attendanceId = (int) $attendance['id'];
if ($attendance['estado'] === 'atendido') {
    Response::error('La atención ya está cerrada, el informe quedó fijo.', 409);
}

// Validar imágenes subidas ANTES de tocar la base -- todo o nada.
$imageFiles = [];
foreach (REPORT_IMAGE_SUFFIXES as $suffix) {
    $field = "image_{$suffix}";
    if (!isset($_FILES[$field]) || $_FILES[$field]['error'] === UPLOAD_ERR_NO_FILE) {
        continue;
    }
    if ($_FILES[$field]['error'] !== UPLOAD_ERR_OK) {
        Response::error("Error al subir {$field} (código {$_FILES[$field]['error']}).", 400);
    }
    $tmpPath = $_FILES[$field]['tmp_name'];
    $info = @getimagesize($tmpPath);
    if ($info === false || $info[2] !== IMAGETYPE_JPEG) {
        Response::error("{$field} debe ser una imagen JPEG válida.", 400);
    }
    $imageFiles[$suffix] = $tmpPath;
}

// version_base: la versión sobre la que la app armó este informe (0 =
// no conocía ninguna). Si la que hay no es esa, alguien guardó en el
// medio -- el alumno siguió en otro equipo, o retomó sin red y el módulo
// arrancó vacío -- y lo que se pisa se aparta en report_versions en vez
// de perderse. Sin version_base (app de antes de esto) se pisa como antes.
$versionBase = isset($_POST['version_base']) ? (int) $_POST['version_base'] : null;
$dataJson = json_encode($data, JSON_UNESCAPED_UNICODE);

if (!$versionado) {
    $pdo->prepare(
        'INSERT INTO reports (attendance_id, tipo, data, updated_at)
         VALUES (?, ?, ?, CURRENT_TIMESTAMP)
         ON CONFLICT(attendance_id, tipo) DO UPDATE SET
            data = excluded.data, updated_at = CURRENT_TIMESTAMP'
    )->execute([$attendanceId, $tipo, $dataJson]);
    $stmt = $pdo->prepare('SELECT id FROM reports WHERE attendance_id = ? AND tipo = ?');
    $stmt->execute([$attendanceId, $tipo]);
    $reportId = (int) $stmt->fetchColumn();
    $version = null;
} else {
    // Con varios kioskos guardando a la vez, la transacción puede chocar
    // con otra escritura ("database is locked"): se reintenta en vez de
    // perder la subida.
    for ($intento = 1; ; $intento++) {
        try {
            $pdo->beginTransaction();
            try {
                $stmt = $pdo->prepare('SELECT id, data, version, updated_at FROM reports WHERE attendance_id = ? AND tipo = ?');
                $stmt->execute([$attendanceId, $tipo]);
                $previo = $stmt->fetch();
                $stmt->closeCursor();
                if ($previo) {
                    $reportId = (int) $previo['id'];
                    $version = (int) $previo['version'] + 1;
                    if ($versionBase !== null && $versionBase !== (int) $previo['version']
                            && $previo['data'] !== $dataJson) {
                        $pdo->prepare(
                            'INSERT INTO report_versions (report_id, version, data, guardado_at) VALUES (?, ?, ?, ?)'
                        )->execute([$reportId, (int) $previo['version'], $previo['data'], $previo['updated_at']]);
                    }
                    $pdo->prepare(
                        'UPDATE reports SET data = ?, version = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
                    )->execute([$dataJson, $version, $reportId]);
                } else {
                    $version = 1;
                    $pdo->prepare(
                        'INSERT INTO reports (attendance_id, tipo, data, version, updated_at)
                         VALUES (?, ?, ?, 1, CURRENT_TIMESTAMP)'
                    )->execute([$attendanceId, $tipo, $dataJson]);
                    $reportId = (int) $pdo->lastInsertId();
                }
                $pdo->commit();
            } catch (Throwable $e) {
                $pdo->rollBack();
                throw $e;
            }
            break;
        } catch (PDOException $e) {
            if ($intento >= 4 || stripos($e->getMessage(), 'locked') === false) {
                throw $e;
            }
            usleep(250000 * $intento);
        }
    }
}

// El PDF (si ya se había generado en una subida anterior) queda
// desactualizado apenas cambia data o alguna imagen -- se borra acá y se
// reconstruye recién cuando alguien lo pida (report_pdf.php). Las
// imágenes NO se borran en bloque: cada suffix se sobreescribe solo si
// viene en este request (ver ReportFile::deletePdf()).
ReportFile::deletePdf($reportId);
foreach ($imageFiles as $suffix => $tmpPath) {
    ReportFile::saveImage($reportId, $suffix, $tmpPath);
}

Response::json(['ok' => true, 'report_id' => $reportId, 'version' => $version]);
