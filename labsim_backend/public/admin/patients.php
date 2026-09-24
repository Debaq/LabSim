<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/CaseCompleteness.php';
require_once __DIR__ . '/../../src/CaseLibrary.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/LlmUsage.php';
require_once __DIR__ . '/../../src/EstudioRedactor.php';

/**
 * Base de datos de fichas clínicas (pacientes/casos) -- separado de agenda.php,
 * que ahora es solo el lugar para configurar/agendar citas por curso, grupo o
 * alumno. Acá se ve y mantiene la biblioteca COMPLETA de casos del sistema,
 * agendados o no, sin acotar por curso.
 *
 * La lista es una TABLA DENSA a propósito: una fila por ficha, de una línea,
 * donde lo que ocupa el ancho es lo que identifica al caso (id, nombre) y
 * todo lo demás son etiquetas cortas. El comentario del docente --que suele
 * ser un párrafo entero-- se muestra recortado a una línea bajo el nombre,
 * con el texto completo en el tooltip y en la ficha: antes tenía columna
 * propia de 22rem y tres o cuatro casos llenaban la pantalla.
 *
 * El mantenimiento de la biblioteca (carpetas, archivar, borrar en tanda)
 * vive en CaseLibrary.php; acá solo está el HTTP.
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$myCourseIds = $isFullAdmin ? null : Courses::teacherCourseIds((int) $me['id']);

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $action = $_POST['form_action'] ?? '';
    // Ids de las fichas tildadas. El borrado de a una manda un solo case_id
    // por el mismo camino: una tanda de uno es una tanda.
    $seleccion = CaseLibrary::limpiarIds((array) ($_POST['case_ids'] ?? []));
    if ($seleccion === [] && trim((string) ($_POST['case_id'] ?? '')) !== '') {
        $seleccion = [trim((string) $_POST['case_id'])];
    }

    if ($action === 'delete_case' || $action === 'bulk_delete') {
        if ($seleccion === []) {
            $error = 'No había ninguna ficha seleccionada.';
        } else {
            $borrado = CaseLibrary::deleteCases($seleccion);
            $success = sprintf(
                '%d ficha(s) eliminada(s), con %d cita(s) y %d atención(es) de alumnos.',
                $borrado['fichas'], $borrado['citas'], $borrado['atenciones']
            );
            AdminAudit::log($me, 'case_delete', [
                'case_ids' => $seleccion,
                'appointments_deleted' => $borrado['citas'],
                'attendances_deleted' => $borrado['atenciones'],
            ]);
        }
    } elseif ($action === 'bulk_archive' || $action === 'bulk_unarchive') {
        $archivar = $action === 'bulk_archive';
        if ($seleccion === []) {
            $error = 'No había ninguna ficha seleccionada.';
        } else {
            $n = $archivar ? CaseLibrary::archive($seleccion) : CaseLibrary::unarchive($seleccion);
            $success = $archivar
                ? "{$n} ficha(s) archivada(s). Siguen completas: salen de la lista y del selector de agendar, nada más."
                : "{$n} ficha(s) desarchivada(s).";
            AdminAudit::log($me, $archivar ? 'case_archive' : 'case_unarchive', ['case_ids' => $seleccion, 'n' => $n]);
        }
    } elseif ($action === 'bulk_move') {
        $destino = (string) ($_POST['folder_destino'] ?? '');
        if ($seleccion === []) {
            $error = 'No había ninguna ficha seleccionada.';
        } else {
            $folderId = $destino === '' ? null : (int) $destino;
            $n = CaseLibrary::moveToFolder($seleccion, $folderId);
            $success = $folderId === null
                ? "{$n} ficha(s) fuera de toda carpeta."
                : "{$n} ficha(s) movida(s) de carpeta.";
            AdminAudit::log($me, 'case_move_folder', ['case_ids' => $seleccion, 'folder_id' => $folderId]);
        }
    } elseif ($action === 'folder_create') {
        $nombre = trim((string) ($_POST['folder_name'] ?? ''));
        $nuevo = CaseLibrary::createFolder($nombre, (int) $me['id']);
        if ($nuevo === null) {
            $error = $nombre === '' ? 'Falta el nombre de la carpeta.' : 'Ya hay una carpeta con ese nombre.';
        } else {
            $success = 'Carpeta creada.';
            AdminAudit::log($me, 'case_folder_create', ['folder_id' => $nuevo, 'name' => $nombre]);
        }
    } elseif ($action === 'folder_rename') {
        $folderId = (int) ($_POST['folder_id'] ?? 0);
        $nombre = trim((string) ($_POST['folder_name'] ?? ''));
        if ($folderId <= 0 || !CaseLibrary::renameFolder($folderId, $nombre)) {
            $error = $nombre === '' ? 'Falta el nombre de la carpeta.' : 'Ya hay una carpeta con ese nombre.';
        } else {
            $success = 'Carpeta renombrada.';
            AdminAudit::log($me, 'case_folder_rename', ['folder_id' => $folderId, 'name' => $nombre]);
        }
    } elseif ($action === 'folder_delete') {
        $folderId = (int) ($_POST['folder_id'] ?? 0);
        if ($folderId > 0) {
            $sueltas = CaseLibrary::deleteFolder($folderId);
            $success = "Carpeta eliminada. {$sueltas} ficha(s) quedaron sin carpeta -- ninguna se borró.";
            AdminAudit::log($me, 'case_folder_delete', ['folder_id' => $folderId, 'cases_loose' => $sueltas]);
        }
    } elseif ($action === 'regen_estudio') {
        // Acción de UNA ficha, pero llega por el mismo form de la tabla: el
        // menú de la fila tilda su checkbox y destilda el resto (selectOnly).
        $caseId = $seleccion[0] ?? '';
        $stmt = $pdo->prepare('SELECT data FROM cases WHERE id = ?');
        $stmt->execute([$caseId]);
        $row = $stmt->fetch();
        $data = $row ? json_decode((string) $row['data'], true) : null;
        if (!is_array($data)) {
            $error = 'Caso no encontrado o su ficha no se puede leer.';
        } else {
            try {
                EstudioRedactor::regenerate($caseId, $data, (int) $me['id']);
                $success = 'Redacción de la ficha de estudio regenerada.';
                AdminAudit::log($me, 'estudio_redaccion_regenerar', ['case_id' => $caseId]);
            } catch (Throwable $e) {
                $error = 'No se pudo regenerar la redacción: ' . $e->getMessage();
            }
        }
    }
}

/** Arma un link a patients.php conservando los GET actuales. */
function patients_url(array $overrides = []): string
{
    $params = array_merge($_GET, $overrides);
    $params = array_filter($params, static fn($v): bool => $v !== null && $v !== '');
    return 'patients.php' . ($params ? '?' . http_build_query($params) : '');
}

/**
 * Timestamp de la base (UTC, CURRENT_TIMESTAMP de SQLite) en hora de Chile y
 * formato local. Sin esto, "creado ayer a las 22:00" se leía como hoy.
 */
function patients_fecha_local(?string $utc): string
{
    $utc = trim((string) $utc);
    if ($utc === '') {
        return '';
    }
    try {
        $dt = new DateTime($utc, new DateTimeZone('UTC'));
    } catch (Throwable $e) {
        return $utc;
    }
    $dt->setTimezone(new DateTimeZone(LlmUsage::ZONA_INFORME));
    return $dt->format('d-m-Y H:i');
}

/** El comentario del docente, recortado a una línea de tabla. */
function patients_resumen(string $texto, int $max = 110): string
{
    $texto = trim(preg_replace('/\s+/', ' ', $texto) ?? '');
    if ($texto === '' || mb_strlen($texto) <= $max) {
        return $texto;
    }
    return mb_substr($texto, 0, $max - 1) . '…';
}

$folders = CaseLibrary::folders();
$folderNombre = [];
foreach ($folders as $f) {
    $folderNombre[(int) $f['id']] = (string) $f['name'];
}

// Vista: carpeta (id, o 'sin' para las sueltas, o '' para todas) y si se
// miran las archivadas. El archivado es una VISTA aparte y no un filtro más
// de la barra: lo archivado no se mezcla con lo vivo ni por accidente.
$verArchivadas = ($_GET['archivadas'] ?? '') === '1';
$folderFiltro = (string) ($_GET['folder'] ?? '');

// Docente: solo ve casos sin agendar (biblioteca compartida) + citas de
// su(s) curso(s) + citas legado sin curso (course_id NULL) -- nunca citas
// de un curso ajeno. Admin completo sin filtro. Esta lista NO se acota por
// curso/grupo/alumno -- es la biblioteca completa del sistema (para eso está
// el filtro de agenda.php). Tampoco la acota el foco de curso del header
// (admin_course_context(), que sí aplican agenda, dashboard y bandeja): una
// ficha no pertenece a un curso, se comparte entre todos, y esconderla por
// estar parado en un curso haría creer que hay que volver a armarla.
$permissionSql = '1=1';
$permissionParams = [];
if (!$isFullAdmin) {
    if ($myCourseIds) {
        $placeholders = implode(',', array_fill(0, count($myCourseIds), '?'));
        $permissionSql = "(a.course_id IS NULL OR a.course_id IN ({$placeholders}))";
        $permissionParams = $myCourseIds;
    } else {
        $permissionSql = 'a.course_id IS NULL';
    }
}

$filtroSql = [$verArchivadas ? 'c.archived_at IS NOT NULL' : 'c.archived_at IS NULL'];
$filtroParams = [];
if ($folderFiltro === 'sin') {
    $filtroSql[] = 'c.folder_id IS NULL';
} elseif ($folderFiltro !== '') {
    $filtroSql[] = 'c.folder_id = ?';
    $filtroParams[] = (int) $folderFiltro;
}
$whereSql = ' WHERE (a.id IS NULL OR (' . $permissionSql . ')) AND ' . implode(' AND ', $filtroSql);

Db::migrateCaseLibraryIfNeeded();
$stmt = $pdo->prepare(
    "SELECT c.id, c.data, c.updated_at, c.created_at, c.folder_id, c.archived_at,
            a.id AS appointment_id, a.fecha, a.hora, a.rut, a.nombre, a.apellido, a.fecha_nac,
            a.procedimiento, a.nota_admin,
            p.comentario_docente,
            -- Autoría de la ficha (cases.created_by/updated_by): el nombre se
            -- resuelve en vivo con JOIN, no se copia en la fila, para que un
            -- cambio de display_name se vea también en las fichas viejas.
            -- NULL = caso anterior a esas columnas que el backfill no pudo
            -- atribuir (ver Db::migrateCaseAuthorshipIfNeeded).
            uc.display_name AS creador_nombre, uc.username AS creador_username,
            ue.display_name AS editor_nombre, ue.username AS editor_username,
            -- Suma TODAS las rondas del caso (no solo la última cita) --
            -- si solo se contara att.appointment_id = a.id (última cita),
            -- cada reagendamiento hacía parecer que las atenciones de
            -- rondas previas se \"perdían\" (volvía a 0).
            (SELECT COUNT(*) FROM attendances att
                JOIN appointments ap2 ON ap2.id = att.appointment_id
                WHERE ap2.case_id = c.id) AS atenciones_count,
            (SELECT COUNT(*) FROM appointments WHERE case_id = c.id) AS rondas_count
     FROM cases c
     LEFT JOIN appointments a ON a.id = (
         SELECT id FROM appointments WHERE case_id = c.id ORDER BY id DESC LIMIT 1
     )
     LEFT JOIN patients p ON p.id = c.patient_id
     LEFT JOIN users uc ON uc.id = c.created_by
     LEFT JOIN users ue ON ue.id = c.updated_by
     {$whereSql}
     ORDER BY CASE WHEN a.fecha IS NULL OR a.fecha = '' THEN 1 ELSE 0 END, a.fecha, a.hora, c.updated_at DESC"
);
$stmt->execute(array_merge($permissionParams, $filtroParams));
$cases = $stmt->fetchAll();

// Cuántas hay del otro lado (archivadas / vivas), para que el enlace a la
// otra vista diga cuántas son en vez de mandar a una pantalla vacía.
$otroLado = (int) $pdo->query(
    'SELECT COUNT(*) FROM cases WHERE archived_at IS ' . ($verArchivadas ? 'NULL' : 'NOT NULL')
)->fetchColumn();

admin_add_css('patients.css');
admin_header('Fichas Clínicas', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <div class="row row--between">
        <strong><?= $verArchivadas ? 'Fichas archivadas' : 'Fichas clínicas' ?> (<?= count($cases) ?>)</strong>
        <span class="row row--center row--gap-sm">
            <a class="btn" href="case_create.php">+ Crear caso nuevo</a>
            <a class="btn secondary" href="case_import.php" title="Pegar una lista de casos en JSON: para armar la tanda de una práctica de una sola vez.">Importar JSON</a>
        </span>
    </div>

    <?php /* Carpetas: filtro y, a la vez, destino de "mover". Planas, en una
             fila de pastillas -- con doscientas fichas lo que hace falta es
             separar por semestre/práctica, no un árbol para navegar. */ ?>
    <div class="folder-bar">
        <a class="folder-pill<?= $folderFiltro === '' ? ' is-active' : '' ?>" href="<?= htmlspecialchars(patients_url(['folder' => null])) ?>">Todas</a>
        <a class="folder-pill<?= $folderFiltro === 'sin' ? ' is-active' : '' ?>" href="<?= htmlspecialchars(patients_url(['folder' => 'sin'])) ?>">Sin carpeta</a>
        <?php foreach ($folders as $f): ?>
        <a class="folder-pill<?= $folderFiltro === (string) $f['id'] ? ' is-active' : '' ?>"
           href="<?= htmlspecialchars(patients_url(['folder' => (string) $f['id']])) ?>">
            <?= htmlspecialchars((string) $f['name']) ?> <span class="folder-pill-count"><?= (int) $f['n_fichas'] ?></span>
        </a>
        <?php endforeach; ?>
        <details class="row-menu folder-admin">
            <summary class="row-menu-btn" title="Carpetas" aria-label="Administrar carpetas">+</summary>
            <div class="row-menu-dropdown row-menu-dropdown--wide">
                <form method="post" class="folder-form">
                <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="folder_create">
                    <input type="text" name="folder_name" placeholder="Carpeta nueva..." required>
                    <button type="submit">Crear</button>
                </form>
                <?php foreach ($folders as $f): ?>
                <form method="post" class="folder-form">
                <?= csrf_field() ?>
                    <input type="hidden" name="folder_id" value="<?= (int) $f['id'] ?>">
                    <input type="text" name="folder_name" value="<?= htmlspecialchars((string) $f['name']) ?>">
                    <?php /* Cada botón dice qué hace con su propio name/value:
                             con un hidden form_action + un botón del mismo
                             nombre, cuál gana depende del orden en el DOM. */ ?>
                    <button type="submit" name="form_action" value="folder_rename" title="Renombrar">✓</button>
                    <button type="submit" name="form_action" value="folder_delete" class="link-danger"
                            title="Eliminar la carpeta (las fichas quedan sin carpeta, no se borran)"
                            onclick="return confirm('Eliminar la carpeta. Las fichas que tenga adentro quedan sin carpeta -- no se borra ninguna. ¿Seguir?');">✕</button>
                </form>
                <?php endforeach; ?>
                <?php if (!$folders): ?>
                <p class="help" style="padding:0 0.9rem;">Todavía no hay carpetas.</p>
                <?php endif; ?>
            </div>
        </details>
        <a class="folder-pill folder-pill--archive<?= $verArchivadas ? ' is-active' : '' ?>"
           href="<?= htmlspecialchars(patients_url(['archivadas' => $verArchivadas ? null : '1'])) ?>">
            <?= $verArchivadas ? '← Volver a las activas' : 'Archivadas' ?> <span class="folder-pill-count"><?= $otroLado ?></span>
        </a>
    </div>

    <form method="post" id="patients-form">
    <?= csrf_field() ?>
    <div class="patients-toolbar">
        <input type="text" id="patients-search" placeholder="Buscar por nombre, rut o ID..." autocomplete="off" oninput="filterPatientsTable()">
        <select id="patients-filter-estado" onchange="filterPatientsTable()">
            <option value="">Todas, en agenda o no</option>
            <option value="agendada">En agenda</option>
            <option value="sin_agendar">Sin agendar</option>
        </select>
        <span class="toolbar-count" id="patients-toolbar-count"></span>
    </div>

    <?php /* Barra de acciones en tanda: aparece recién cuando hay algo
             tildado, para que "Eliminar" no esté nunca a un clic de
             distancia sin haber elegido qué. */ ?>
    <div class="bulk-bar" id="patients-bulk" hidden>
        <strong><span id="patients-bulk-count">0</span> seleccionada(s)</strong>
        <?php if ($verArchivadas): ?>
        <button type="submit" name="form_action" value="bulk_unarchive" class="btn btn--secondary">Desarchivar</button>
        <?php else: ?>
        <button type="submit" name="form_action" value="bulk_archive" class="btn btn--secondary">Archivar</button>
        <?php endif; ?>
        <span class="bulk-move">
            <select name="folder_destino">
                <option value="">(sin carpeta)</option>
                <?php foreach ($folders as $f): ?>
                <option value="<?= (int) $f['id'] ?>"><?= htmlspecialchars((string) $f['name']) ?></option>
                <?php endforeach; ?>
            </select>
            <button type="submit" name="form_action" value="bulk_move" class="btn btn--secondary">Mover</button>
        </span>
        <button type="submit" name="form_action" value="bulk_delete" class="btn btn--danger" id="patients-bulk-delete"
                onclick="return confirmBulkDelete();">Eliminar</button>
        <button type="button" class="btn btn--ghost" onclick="clearPatientsSelection()">Limpiar</button>
    </div>

    <div class="table-wrap table-wrap--wide">
    <table id="patients-table" class="table-dense">
        <tr>
            <th class="col-check"><input type="checkbox" id="patients-check-all" onclick="togglePatientsAll(this)" title="Seleccionar todo lo visible"></th>
            <th>Ficha</th>
            <th title="Si el caso está puesto en alguna agenda, si le falta algo por decidir y en qué carpeta vive">Estado</th>
            <th title="Alumnos que la han atendido · veces que fue agendada (rondas)">Uso</th>
            <th title="Quién la armó y quién la tocó por última vez">Autoría</th>
            <th>Acciones</th>
        </tr>
        <?php foreach ($cases as $c): ?>
        <?php
        $data = json_decode($c['data'] ?? '', true);
        $snapshot = is_array($data) ? ($data['paciente_snapshot'] ?? null) : null;
        $nombreVivo = $c['appointment_id'] ? trim(($c['nombre'] ?? '') . ' ' . ($c['apellido'] ?? '')) : '';
        $nombreSnapshot = $snapshot ? trim(($snapshot['nombre'] ?? '') . ' ' . ($snapshot['apellido'] ?? '')) : '';
        $nombreRow = $nombreVivo ?: $nombreSnapshot;
        $estadoRow = (!$c['appointment_id'] || $c['fecha'] === '' || $c['hora'] === '') ? 'sin_agendar' : 'agendada';
        $comentarioDocente = trim((string) ($c['comentario_docente'] ?? ''));
        // Lo que el perfil no puede calcular y nadie decidió todavía. Un
        // caso así no se puede citar (ver agenda.php), así que se marca acá
        // para que aparezca como trabajo pendiente y no como sorpresa al
        // intentar agendarlo. Ver CaseCompleteness.
        $faltantesRow = CaseCompleteness::pendingTexts(is_array($data) ? $data : []);
        // "incompleto" entra al blob de búsqueda: con el buscador que ya
        // existe alcanza para juntar todos los casos que hay que completar,
        // sin agregar otro filtro a la barra.
        $creadorRow = trim((string) ($c['creador_nombre'] ?? ''));
        $editorRow = trim((string) ($c['editor_nombre'] ?? ''));
        $carpetaRow = $c['folder_id'] !== null ? ($folderNombre[(int) $c['folder_id']] ?? '') : '';
        $searchBlob = mb_strtolower($c['id'] . ' ' . $nombreRow . ' ' . ($c['rut'] ?? '')
            . ' ' . $comentarioDocente . ' ' . $creadorRow . ' ' . $editorRow . ' ' . $carpetaRow
            . ($faltantesRow !== [] ? ' incompleto' : ''));
        ?>
        <tr data-estado="<?= $estadoRow ?>" data-search="<?= htmlspecialchars($searchBlob) ?>">
            <td class="col-check">
                <input type="checkbox" name="case_ids[]" value="<?= htmlspecialchars($c['id']) ?>"
                       class="patients-check" onclick="updatePatientsSelection()">
            </td>
            <td class="col-ficha">
                <span class="ficha-id"><?= htmlspecialchars($c['id']) ?></span>
                <?php if ($nombreRow !== ''): ?>
                    <a class="ficha-nombre" href="case_create.php?edit=<?= urlencode($c['id']) ?>"><?= htmlspecialchars($nombreRow) ?></a>
                    <?php if ($nombreVivo === '' && $nombreSnapshot !== ''): ?>
                    <span class="tag tag--warn" title="La cita que tenía se eliminó<?= !empty($snapshot['cita_eliminada_en']) ? ' el ' . htmlspecialchars($snapshot['cita_eliminada_en']) : '' ?>">cita eliminada</span>
                    <?php endif; ?>
                <?php else: ?>
                    <a class="ficha-nombre ficha-nombre--vacio" href="case_create.php?edit=<?= urlencode($c['id']) ?>">— sin cita —</a>
                <?php endif; ?>
                <?php if ($comentarioDocente !== ''): ?>
                <span class="ficha-comentario" title="<?= htmlspecialchars($comentarioDocente) ?>"><?= htmlspecialchars(patients_resumen($comentarioDocente)) ?></span>
                <?php endif; ?>
            </td>
            <td class="col-estado">
                <?php if ($c['archived_at'] !== null): ?>
                <span class="tag tag--muted" title="Archivada el <?= htmlspecialchars(patients_fecha_local($c['archived_at'])) ?>">archivada</span>
                <?php endif; ?>
                <?php if ($faltantesRow !== []): ?>
                <span class="tag tag--warn" title="<?= htmlspecialchars(implode("\n", $faltantesRow)) ?>">incompleto</span>
                <?php endif; ?>
                <?php /* Solo si está o no en agenda: la fecha/hora de la cita
                          no va acá -- un caso puede estar agendado varias veces
                          (rondas) y mostrar una sola fecha hacía parecer que esa
                          era LA fecha del caso. Eso se ve en Agendas. */ ?>
                <?php if ($estadoRow === 'sin_agendar'): ?>
                <span class="tag tag--muted">sin agendar</span>
                <?php else: ?>
                <span class="tag tag--success">en agenda</span>
                <?php endif; ?>
                <?php if ($carpetaRow !== ''): ?>
                <span class="tag" title="Carpeta"><?= htmlspecialchars($carpetaRow) ?></span>
                <?php endif; ?>
            </td>
            <td class="col-uso">
                <?php if ((int) $c['atenciones_count'] > 0 || (int) $c['rondas_count'] > 0): ?>
                <a href="agenda.php?history=<?= urlencode($c['id']) ?>#historial"
                   title="<?= (int) $c['atenciones_count'] ?> atención(es) de alumnos en <?= (int) $c['rondas_count'] ?> ronda(s) -- ver historial">
                    <?= (int) $c['atenciones_count'] ?> · <?= (int) $c['rondas_count'] ?>
                </a>
                <?php else: ?>
                <span class="muted">—</span>
                <?php endif; ?>
            </td>
            <td class="col-autoria">
                <span title="Creada por <?= htmlspecialchars($creadorRow !== '' ? $creadorRow . ' (' . (string) $c['creador_username'] . ')' : 'autor desconocido') ?> el <?= htmlspecialchars(patients_fecha_local($c['created_at'])) ?>&#10;Última edición: <?= htmlspecialchars($editorRow !== '' ? $editorRow : 'sin registro') ?> el <?= htmlspecialchars(patients_fecha_local($c['updated_at'])) ?>">
                    <?= htmlspecialchars($creadorRow !== '' ? $creadorRow : '—') ?>
                    <span class="muted nowrap"><?= htmlspecialchars(substr(patients_fecha_local($c['updated_at']), 0, 10)) ?></span>
                </span>
            </td>
            <td class="col-acciones nowrap">
                <a href="case_create.php?edit=<?= urlencode($c['id']) ?>" class="action-btn secondary">Editar</a>
                <a href="agenda.php?schedule=<?= urlencode($c['id']) ?>" class="action-btn primary"
                   title="<?= $c['appointment_id'] ? 'Edita la cita que ya tiene, o desde ahí agenda una cita nueva sin tocarla' : 'Le agenda una cita a este caso' ?>">Agendar</a>
                <details class="row-menu">
                    <summary class="row-menu-btn" title="Más acciones" aria-label="Más acciones">&#8942;</summary>
                    <div class="row-menu-dropdown">
                        <a class="row-menu-item" href="case_sheet_pdf.php?id=<?= urlencode($c['id']) ?>" target="_blank" rel="noopener"
                           title="Ficha completa en PDF: perfil, audiograma, impedanciometría, acumetría, logoaudiometría, supraliminares, ABR, OEA y VEMP">PDF de la ficha</a>
                        <a class="row-menu-item" href="case_sheet_pdf.php?id=<?= urlencode($c['id']) ?>&amp;modo=estudio" target="_blank" rel="noopener"
                           title="Los mismos exámenes, sin el perfil auditivo ni los parámetros del generador -- para repartir al alumno">PDF de estudio</a>
                        <button type="submit" class="row-menu-item" name="form_action" value="regen_estudio"
                                onclick="return selectOnly(this, '<?= htmlspecialchars($c['id'], ENT_QUOTES) ?>', '¿Redactar de nuevo la anamnesis de la ficha de estudio con IA? Reemplaza el texto guardado.');">
                            Redactar de nuevo anamnesis (IA)
                        </button>
                        <?php if ($c['archived_at'] === null): ?>
                        <button type="submit" class="row-menu-item" name="form_action" value="bulk_archive"
                                onclick="return selectOnly(this, '<?= htmlspecialchars($c['id'], ENT_QUOTES) ?>', '');">Archivar</button>
                        <?php else: ?>
                        <button type="submit" class="row-menu-item" name="form_action" value="bulk_unarchive"
                                onclick="return selectOnly(this, '<?= htmlspecialchars($c['id'], ENT_QUOTES) ?>', '');">Desarchivar</button>
                        <?php endif; ?>
                        <button type="submit" class="row-menu-item link-danger" name="form_action" value="bulk_delete"
                                onclick="return selectOnly(this, '<?= htmlspecialchars($c['id'], ENT_QUOTES) ?>', <?= htmlspecialchars(json_encode("¿Eliminar el caso {$c['id']}" . ($nombreRow !== '' ? ' (' . $nombreRow . ')' : '') . "? También se eliminan sus citas/rondas ({$c['rondas_count']}) y las atenciones registradas ({$c['atenciones_count']}). No se puede deshacer."), ENT_QUOTES) ?>);">
                            Eliminar ficha
                        </button>
                    </div>
                </details>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$cases): ?>
        <tr><td colspan="6" class="muted">
            <?= $verArchivadas ? 'No hay fichas archivadas.' : 'Ninguna ficha acá todavía.' ?>
        </td></tr>
        <?php endif; ?>
    </table>
    </div>
    <p class="muted help--mt">
        Biblioteca completa de fichas del sistema (agendadas o no). Para agendar, reagendar o eliminar citas,
        usa <a href="agenda.php">Agendas</a>. Archivar no borra nada: la ficha sale de esta lista y del selector
        de agendar, y sus citas y atenciones quedan como están.
    </p>
    </form>
</div>
<script>
/* Un solo <form> envuelve la tabla entera: las acciones en tanda mandan los
   checkboxes tildados, y las acciones de una fila (menú de tres puntos)
   tildan esa sola antes de enviar -- así el servidor recibe siempre la misma
   forma (case_ids[]) sin importar de dónde vino el clic. */
function patientsRows() {
    return Array.prototype.slice.call(document.querySelectorAll('#patients-table tr[data-search]'));
}
function filterPatientsTable() {
    var q = document.getElementById('patients-search').value.toLowerCase().trim();
    var estado = document.getElementById('patients-filter-estado').value;
    var visible = 0;
    patientsRows().forEach(function (row) {
        var matchQ = q === '' || (row.dataset.search || '').indexOf(q) !== -1;
        var matchEstado = estado === '' || row.dataset.estado === estado;
        var show = matchQ && matchEstado;
        row.style.display = show ? '' : 'none';
        /* Una fila escondida por el filtro no puede seguir contando como
           seleccionada: si no, "Eliminar" se llevaba casos que no estaban ni
           en pantalla. */
        if (!show) {
            var cb = row.querySelector('.patients-check');
            if (cb) cb.checked = false;
        }
        if (show) visible++;
    });
    document.getElementById('patients-toolbar-count').textContent = visible + ' de ' + patientsRows().length;
    updatePatientsSelection();
}
function selectedChecks() {
    return patientsRows()
        .filter(function (row) { return row.style.display !== 'none'; })
        .map(function (row) { return row.querySelector('.patients-check'); })
        .filter(function (cb) { return cb && cb.checked; });
}
function updatePatientsSelection() {
    var n = selectedChecks().length;
    var bar = document.getElementById('patients-bulk');
    bar.hidden = n === 0;
    document.getElementById('patients-bulk-count').textContent = n;
}
function togglePatientsAll(master) {
    patientsRows().forEach(function (row) {
        if (row.style.display === 'none') return;
        var cb = row.querySelector('.patients-check');
        if (cb) cb.checked = master.checked;
    });
    updatePatientsSelection();
}
function clearPatientsSelection() {
    patientsRows().forEach(function (row) {
        var cb = row.querySelector('.patients-check');
        if (cb) cb.checked = false;
    });
    document.getElementById('patients-check-all').checked = false;
    updatePatientsSelection();
}
function confirmBulkDelete() {
    var n = selectedChecks().length;
    if (n === 0) return false;
    return confirm('Se eliminan ' + n + ' ficha(s) con TODAS sus citas y las atenciones que los alumnos ya registraron. No se puede deshacer.');
}
/* Acción de una sola fila: destilda todo, tilda esa, y recién ahí envía. */
function selectOnly(btn, caseId, mensaje) {
    if (mensaje && !confirm(mensaje)) return false;
    patientsRows().forEach(function (row) {
        var cb = row.querySelector('.patients-check');
        if (cb) cb.checked = cb.value === caseId;
    });
    return true;
}
filterPatientsTable();
</script>
<?php
admin_footer();
