<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Mensajes que el docente/admin manda a mano a la bandeja de entrada
 * (tabla inbox_messages, tipo 'mensaje') -- para avisos de curso, o
 * simplemente para probar cómo se ve la bandeja sin tener que cerrar una
 * atención real y esperar al veredicto del LLM (ver OirsEvaluator.php).
 * Mismo scoping que courses.php: el admin completo ve/manda a cualquier
 * curso, un docente solo a los suyos.
 *
 * Destinatario puede ser un alumno del curso (individual/grupo/todos) o
 * otro docente adscrito al MISMO curso (individual/todos) -- la columna
 * inbox_messages.student_id acepta cualquier user_id, así que el mismo
 * buzón sirve para ambos casos (lo lee cualquier rol vía requireUser()).
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();
$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$myCourseIds = $isFullAdmin ? null : Courses::teacherCourseIds((int) $me['id']);

$courses = $isFullAdmin
    ? Courses::listActive()
    : array_filter(Courses::listActive(), fn (array $c) => in_array((int) $c['id'], $myCourseIds, true));

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && ($_POST['accion'] ?? '') === 'marcar_leido') {
    Auth::requireCsrf();
    $id = (int) ($_POST['id'] ?? 0);
    // student_id = $me['id'] en el WHERE -- basta para que nadie marque
    // como leído un mensaje ajeno editando el id, sin necesitar más checks.
    $pdo->prepare('UPDATE inbox_messages SET leido = 1 WHERE id = ? AND student_id = ?')
        ->execute([$id, (int) $me['id']]);
    $backTo = (int) ($_POST['course_id'] ?? 0);
    $backPagina = max(1, (int) ($_POST['pagina'] ?? 1));
    // El form no lleva action, así que postea a la URL con su query string:
    // los filtros del listado "Recibidos por los alumnos" siguen en $_GET y
    // se devuelven al redirect para no perder la vista que estaba puesta.
    $filtrosVista = array_intersect_key(
        $_GET,
        array_flip(['alcance', 'alumno_id', 'tipo', 'estado', 'q', 'ver', 'pag_alumnos'])
    );
    $qs = array_filter(array_merge(
        ['course_id' => $backTo ?: null, 'pagina' => $backPagina > 1 ? $backPagina : null],
        $filtrosVista
    ));
    header('Location: inbox_send.php' . ($qs ? '?' . http_build_query($qs) : ''));
    exit;
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $courseId = (int) ($_POST['course_id'] ?? 0);
    Courses::assertAdministers($courseId, $me);

    $asunto = trim((string) ($_POST['asunto'] ?? ''));
    $cuerpo = trim((string) ($_POST['cuerpo'] ?? ''));
    $destinatario = (string) ($_POST['destinatario'] ?? 'alumno');
    $modo = (string) ($_POST['modo'] ?? 'individual');

    // Nunca confiar en los ids/grupo tal cual vienen del form -- solo
    // alumnos/docentes que de verdad pertenecen a ESTE curso (mismo courseId
    // ya validado arriba), para que nadie mande un mensaje a un user_id o
    // grupo ajeno editando el POST.
    if ($destinatario === 'docente') {
        $teachers = array_filter(Courses::teachers($courseId), fn (array $t) => (int) $t['id'] !== (int) $me['id']);
        $teacherIds = array_column($teachers, 'id');
        if (!empty($_POST['todos_docentes'])) {
            $targetIds = $teacherIds;
        } else {
            $selectedIds = array_map('intval', (array) ($_POST['teacher_ids'] ?? []));
            $targetIds = array_values(array_intersect($teacherIds, $selectedIds));
        }
    } else {
        $roster = Courses::students($courseId);
        $rosterIds = array_column($roster, 'id');
        if ($modo === 'todos') {
            $targetIds = $rosterIds;
        } elseif ($modo === 'grupo') {
            $grupoId = (int) ($_POST['grupo_id'] ?? 0);
            $stmt = $pdo->prepare('SELECT 1 FROM student_groups WHERE id = ? AND course_id = ?');
            $stmt->execute([$grupoId, $courseId]);
            $grupoIds = $stmt->fetch() ? array_column(Courses::membersOfGroup($grupoId), 'id') : [];
            $targetIds = array_values(array_intersect($rosterIds, $grupoIds));
        } else {
            $selectedIds = array_map('intval', (array) ($_POST['student_ids'] ?? []));
            $targetIds = array_values(array_intersect($rosterIds, $selectedIds));
        }
    }

    if ($asunto === '' || $cuerpo === '') {
        $error = 'Falta el asunto o el cuerpo del mensaje.';
    } elseif (!$targetIds) {
        $error = $destinatario === 'docente'
            ? 'Selecciona al menos un docente (o "Todos los docentes").'
            : 'Selecciona al menos un alumno (o "Todo el curso", o un grupo).';
    } else {
        $remitente = ($me['permission'] === Auth::PERMISSION_ADMIN ? 'Admin ' : 'Docente ') . $me['display_name'];
        $stmt = $pdo->prepare(
            'INSERT INTO inbox_messages (student_id, tipo, remitente, asunto, cuerpo, sender_admin_id)
             VALUES (?, ?, ?, ?, ?, ?)'
        );
        foreach ($targetIds as $userId) {
            $stmt->execute([$userId, 'mensaje', $remitente, $asunto, $cuerpo, $me['id']]);
        }
        $success = 'Mensaje enviado a ' . count($targetIds) . ' ' . ($destinatario === 'docente' ? 'docente(s)' : 'alumno(s)') . '.';
        AdminAudit::log($me, 'inbox_send', [
            'course_id' => $courseId, 'asunto' => $asunto, 'n_destinatarios' => count($targetIds),
            'destinatario' => $destinatario,
            'modo' => $destinatario === 'docente' ? (!empty($_POST['todos_docentes']) ? 'todos' : 'individual') : $modo,
        ]);
    }
}

// El curso lo fija el selector del header (ver admin_course_context()), que
// es el mismo foco que usan agenda, fichas y dashboard: acá había un
// <select> propio que obligaba a volver a elegir lo ya elegido. El POST
// manda igual su course_id (el aviso se envía al curso que estaba a la
// vista), y sin foco se cae al primer curso disponible.
$contextCourseId = admin_course_context($me);
$selectedCourseId = (int) ($_POST['course_id'] ?? $contextCourseId ?? 0);
if ($selectedCourseId <= 0 && $courses) {
    $selectedCourseId = (int) reset($courses)['id'];
}
$cursoElegidoANombre = null;
foreach ($courses as $c) {
    if ((int) $c['id'] === $selectedCourseId) {
        $cursoElegidoANombre = (string) $c['name'];
    }
}
if ($selectedCourseId > 0) {
    Courses::assertAdministers($selectedCourseId, $me);
}
$roster = $selectedCourseId > 0 ? Courses::students($selectedCourseId) : [];
$grupos = $selectedCourseId > 0 ? Courses::groupsForCourse($selectedCourseId) : [];
$teachers = $selectedCourseId > 0
    ? array_values(array_filter(Courses::teachers($selectedCourseId), fn (array $t) => (int) $t['id'] !== (int) $me['id']))
    : [];

// Lo que a MÍ me han mandado -- avisos automáticos de OirsEvaluator y
// mensajes de otros docentes/admin (esta misma página). El cliente de
// escritorio también los lee (ver core/inbox.py -> api/inbox.php), pero ese
// usa token propio (Auth::requireUser) y esta página usa sesión de admin,
// así que necesita su propia lectura.
//
// Paginado (POR_PAGINA + 1 para saber si hay página siguiente sin un
// segundo COUNT(*)) -- el contador de no leídos es una query aparte, sin
// límite, porque un mensaje sin leer viejo no debe desaparecer del badge
// solo por quedar fuera de la página actual.
const INBOX_POR_PAGINA = 50;
// El listado de lo que recibieron los alumnos abre como resumen: los
// últimos RESUMEN mensajes, que es lo que uno mira al entrar. En cuanto se
// busca (alumno, tipo, estado o texto) pasa a mostrar TODAS las
// coincidencias -- el sentido de buscar es no perderse ninguna. MAX es el
// tope duro de esa segunda modalidad: sin él, un filtro ancho en un curso
// grande manda miles de filas al navegador de una sola vez. Pasado el tope
// el listado sigue completo, pero paginado.
const INBOX_ALUMNOS_RESUMEN = 5;
const INBOX_ALUMNOS_MAX = 500;
$pagina = max(1, (int) ($_GET['pagina'] ?? 1));
$offset = ($pagina - 1) * INBOX_POR_PAGINA;

$stmtNoLeidos = $pdo->prepare('SELECT COUNT(*) FROM inbox_messages WHERE student_id = ? AND leido = 0');
$stmtNoLeidos->execute([(int) $me['id']]);
$noLeidos = (int) $stmtNoLeidos->fetchColumn();

$stmtRecibidos = $pdo->prepare(
    "SELECT * FROM inbox_messages WHERE student_id = ? ORDER BY created_at DESC LIMIT " . (INBOX_POR_PAGINA + 1) . ' OFFSET ?'
);
$stmtRecibidos->execute([(int) $me['id'], $offset]);
$misMensajes = $stmtRecibidos->fetchAll();
$hayPaginaSiguiente = count($misMensajes) > INBOX_POR_PAGINA;
$misMensajes = array_slice($misMensajes, 0, INBOX_POR_PAGINA);

// Lo que YO he mandado (esta página, avisos manuales) -- cada envío a N
// destinatarios queda como N filas (mismo asunto/cuerpo/created_at, distinto
// student_id), así que se agrupan por lote para mostrar un solo renglón por
// envío con la lista de destinatarios y cuántos lo han leído.
$stmtEnviados = $pdo->prepare(
    "SELECT m.asunto, m.cuerpo, m.created_at, COUNT(*) AS n_destinatarios,
            SUM(m.leido) AS n_leidos, GROUP_CONCAT(u.display_name, ', ') AS destinatarios
     FROM inbox_messages m
     JOIN users u ON u.id = m.student_id
     WHERE m.sender_admin_id = ? AND m.tipo = 'mensaje'
     GROUP BY m.asunto, m.cuerpo, m.created_at
     ORDER BY m.created_at DESC
     LIMIT 50"
);
$stmtEnviados->execute([(int) $me['id']]);
$misEnvios = $stmtEnviados->fetchAll();

// Lo que han recibido LOS ALUMNOS -- la misma bandeja que ve cada uno en la
// app, pero de corrido: avisos automáticos de OirsEvaluator y mensajes que
// mandó cualquier docente, sin tener que entrar ficha por ficha a
// student.php. Scoping de siempre: el admin completo puede mirar todos los
// cursos, el docente solo los que administra.
$alcance = ($_GET['alcance'] ?? '') === 'todos' ? 'todos' : 'curso';
$filtroAlumno = (int) ($_GET['alumno_id'] ?? 0);
$filtroTipo = (string) ($_GET['tipo'] ?? '');
if (!in_array($filtroTipo, ['reclamo', 'merito', 'mensaje'], true)) {
    $filtroTipo = '';
}
$filtroEstado = (string) ($_GET['estado'] ?? '');
if (!in_array($filtroEstado, ['leidos', 'no_leidos'], true)) {
    $filtroEstado = '';
}
$filtroTexto = trim((string) ($_GET['q'] ?? ''));
// Cambiar de curso no es "buscar": ensancha el listado, pero sigue siendo
// la vista de entrada, así que no saca del resumen. El "Ver todos" sí.
$hayBusqueda = $filtroAlumno > 0 || $filtroTipo !== '' || $filtroEstado !== '' || $filtroTexto !== '';
$verTodos = ($_GET['ver'] ?? '') === 'todos' || $hayBusqueda;
$porPaginaAlumnos = $verTodos ? INBOX_ALUMNOS_MAX : INBOX_ALUMNOS_RESUMEN;

// Solo los alumnos de ESTE docente -- los matriculados en los cursos que
// administra. La regla y el porqué de la subconsulta están en
// Courses::studentScopeSql(); acá no se rehace, para que no haya dos
// versiones de "sus alumnos" que se puedan ir separando.
list($scopeSql, $scopeParams) = Courses::studentScopeSql(
    $alcance,
    $selectedCourseId,
    $isFullAdmin ? null : $myCourseIds
);

$whereAlumnos = [$scopeSql];
$paramsAlumnos = $scopeParams;
if ($filtroAlumno > 0) {
    $whereAlumnos[] = 'm.student_id = ?';
    $paramsAlumnos[] = $filtroAlumno;
}
if ($filtroTipo !== '') {
    $whereAlumnos[] = 'm.tipo = ?';
    $paramsAlumnos[] = $filtroTipo;
}
if ($filtroEstado !== '') {
    $whereAlumnos[] = 'm.leido = ' . ($filtroEstado === 'leidos' ? '1' : '0');
}
if ($filtroTexto !== '') {
    $whereAlumnos[] = '(m.asunto LIKE ? OR m.cuerpo LIKE ? OR u.display_name LIKE ?)';
    $like = '%' . $filtroTexto . '%';
    $paramsAlumnos[] = $like;
    $paramsAlumnos[] = $like;
    $paramsAlumnos[] = $like;
}
$whereAlumnosSql = implode(' AND ', $whereAlumnos);

// Acá sí conviene el COUNT(*) aparte (y no el LIMIT+1 de la bandeja
// propia): con filtros puestos, saber cuántos mensajes hay en total es
// parte de la respuesta, no solo si queda otra página.
$stmt = $pdo->prepare(
    "SELECT COUNT(*) FROM inbox_messages m JOIN users u ON u.id = m.student_id WHERE {$whereAlumnosSql}"
);
$stmt->execute($paramsAlumnos);
$totalAlumnos = (int) $stmt->fetchColumn();

$paginaAlumnos = max(1, (int) ($_GET['pag_alumnos'] ?? 1));
// En modo resumen no hay paginado: son los 5 más recientes y un link para
// abrir el listado completo -- paginar de a 5 sería peor que abrirlo.
$totalPaginasAlumnos = $verTodos ? max(1, (int) ceil($totalAlumnos / $porPaginaAlumnos)) : 1;
$paginaAlumnos = min($paginaAlumnos, $totalPaginasAlumnos);
$stmt = $pdo->prepare(
    "SELECT m.id, m.student_id, m.tipo, m.remitente, m.asunto, m.cuerpo, m.leido, m.created_at,
            u.display_name, u.username,
            a.fecha, a.hora, a.procedimiento
     FROM inbox_messages m
     JOIN users u ON u.id = m.student_id
     LEFT JOIN appointments a ON a.id = m.appointment_id
     WHERE {$whereAlumnosSql}
     ORDER BY m.created_at DESC, m.id DESC
     LIMIT " . $porPaginaAlumnos . ' OFFSET ?'
);
$stmt->execute(array_merge($paramsAlumnos, [($paginaAlumnos - 1) * $porPaginaAlumnos]));
$mensajesAlumnos = $stmt->fetchAll();

// Alumnos que pueblan el <select> del filtro -- los del mismo alcance que
// el listado, para no ofrecer nombres que después no devuelven nada.
if ($alcance === 'todos') {
    if ($isFullAdmin) {
        $alumnosFiltro = $pdo->query(
            'SELECT DISTINCT u.id, u.display_name, u.username FROM course_students cs
             JOIN users u ON u.id = cs.user_id ORDER BY u.display_name'
        )->fetchAll();
    } elseif ($myCourseIds) {
        $ph = implode(',', array_fill(0, count($myCourseIds), '?'));
        $stmt = $pdo->prepare(
            "SELECT DISTINCT u.id, u.display_name, u.username FROM course_students cs
             JOIN users u ON u.id = cs.user_id WHERE cs.course_id IN ({$ph}) ORDER BY u.display_name"
        );
        $stmt->execute($myCourseIds);
        $alumnosFiltro = $stmt->fetchAll();
    } else {
        $alumnosFiltro = [];
    }
} else {
    $alumnosFiltro = $roster;
}

$hayFiltrosAlumnos = $alcance === 'todos' || $filtroAlumno > 0 || $filtroTipo !== ''
    || $filtroEstado !== '' || $filtroTexto !== '';

// Base de los links de paginado: conserva filtros + la página de la bandeja
// propia, que es otra numeración distinta (parámetro 'pagina').
$qsAlumnos = array_filter([
    'course_id' => $selectedCourseId > 0 ? $selectedCourseId : null,
    'pagina' => $pagina > 1 ? $pagina : null,
    'alcance' => $alcance === 'todos' ? 'todos' : null,
    'alumno_id' => $filtroAlumno > 0 ? $filtroAlumno : null,
    'tipo' => $filtroTipo ?: null,
    'estado' => $filtroEstado ?: null,
    'q' => $filtroTexto !== '' ? $filtroTexto : null,
    'ver' => $verTodos && !$hayBusqueda ? 'todos' : null,
]);
$linkAlumnos = function (int $n) use ($qsAlumnos): string {
    return '?' . http_build_query(array_merge($qsAlumnos, ['pag_alumnos' => $n])) . '#alumnos';
};

$tipoLabels = ['reclamo' => 'Reclamo', 'merito' => 'Mérito', 'mensaje' => 'Mensaje docente'];

admin_header('Bandeja de entrada', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <strong>Mensajes recibidos<?= $noLeidos > 0 ? " ({$noLeidos} sin leer)" : '' ?></strong>
    <?php if (!$misMensajes): ?>
    <p class="help">Sin mensajes todavía.</p>
    <?php else: ?>
    <div class="scrollbox" style="margin-top:0.5rem;">
        <?php foreach ($misMensajes as $m): ?>
        <details class="pane" style="margin-bottom:0.4rem;" <?= !$m['leido'] ? 'open' : '' ?>>
            <summary style="cursor:pointer; <?= !$m['leido'] ? 'font-weight:700;' : '' ?>">
                <?= !$m['leido'] ? '● ' : '' ?><?= htmlspecialchars($m['asunto']) ?>
                <span class="help normal">-- <?= htmlspecialchars($m['remitente'] ?: 'Sistema') ?>, <?= htmlspecialchars($m['created_at']) ?></span>
            </summary>
            <p style="white-space:pre-wrap; margin:0.5rem 0 0.3rem;"><?= htmlspecialchars($m['cuerpo']) ?></p>
            <?php if (!$m['leido']): ?>
            <form method="post" style="margin:0;">
                <?= csrf_field() ?>
                <input type="hidden" name="accion" value="marcar_leido">
                <input type="hidden" name="id" value="<?= (int) $m['id'] ?>">
                <input type="hidden" name="course_id" value="<?= $selectedCourseId ?>">
                <input type="hidden" name="pagina" value="<?= $pagina ?>">
                <button type="submit" style="font-size:0.8rem; padding:0.2rem 0.6rem;">Marcar leído</button>
            </form>
            <?php endif; ?>
        </details>
        <?php endforeach; ?>
    </div>
    <div style="display:flex; justify-content:space-between; margin-top:0.5rem;">
        <?php if ($pagina > 1): ?>
        <a href="?pagina=<?= $pagina - 1 ?><?= $selectedCourseId > 0 ? '&course_id=' . $selectedCourseId : '' ?>">« Más recientes</a>
        <?php else: ?><span></span><?php endif; ?>
        <?php if ($hayPaginaSiguiente): ?>
        <a href="?pagina=<?= $pagina + 1 ?><?= $selectedCourseId > 0 ? '&course_id=' . $selectedCourseId : '' ?>">Más antiguos »</a>
        <?php endif; ?>
    </div>
    <?php endif; ?>
</div>

<div class="card" id="alumnos">
    <strong>Recibidos por los alumnos (<?= $totalAlumnos ?>)</strong>
    <p class="legend">
        Todo lo que ha llegado a la bandeja de los alumnos: los avisos automáticos sobre el trato a
        pacientes (ver <a href="llm.php">Admin &rarr; IA Paciente</a>) y los mensajes que mandó cualquier
        docente del curso, no solo tú. Es la misma bandeja que ve el alumno en la app; la ficha de uno
        solo está en <em>Alumnos</em>. Abre con los <?= INBOX_ALUMNOS_RESUMEN ?> más recientes; al filtrar
        salen todas las coincidencias.
    </p>

    <form method="get" style="display:flex; flex-wrap:wrap; align-items:center; gap:0.6rem; margin:0.7rem 0;">
        <?php if ($selectedCourseId > 0): ?>
        <input type="hidden" name="course_id" value="<?= $selectedCourseId ?>">
        <?php endif; ?>
        <?php if ($pagina > 1): ?>
        <input type="hidden" name="pagina" value="<?= $pagina ?>">
        <?php endif; ?>
        <?php if ($verTodos && !$hayBusqueda): ?>
        <input type="hidden" name="ver" value="todos">
        <?php endif; ?>
        <select name="alcance" class="input--auto">
            <option value="curso"<?= $alcance === 'curso' ? ' selected' : '' ?>>
                <?= $cursoElegidoANombre !== null ? htmlspecialchars($cursoElegidoANombre) : 'Curso en foco' ?>
            </option>
            <option value="todos"<?= $alcance === 'todos' ? ' selected' : '' ?>>
                <?= $isFullAdmin ? 'Todos los cursos' : 'Todos mis cursos' ?>
            </option>
        </select>
        <select name="alumno_id" class="input--auto">
            <option value="">Todos los alumnos</option>
            <?php foreach ($alumnosFiltro as $a): ?>
            <option value="<?= (int) $a['id'] ?>"<?= $filtroAlumno === (int) $a['id'] ? ' selected' : '' ?>>
                <?= htmlspecialchars($a['display_name']) ?>
            </option>
            <?php endforeach; ?>
        </select>
        <select name="tipo" class="input--auto">
            <option value="">Todos los tipos</option>
            <?php foreach ($tipoLabels as $codigo => $etiqueta): ?>
            <option value="<?= $codigo ?>"<?= $filtroTipo === $codigo ? ' selected' : '' ?>><?= $etiqueta ?></option>
            <?php endforeach; ?>
        </select>
        <select name="estado" class="input--auto">
            <option value="">Leídos y sin leer</option>
            <option value="no_leidos"<?= $filtroEstado === 'no_leidos' ? ' selected' : '' ?>>Sin leer</option>
            <option value="leidos"<?= $filtroEstado === 'leidos' ? ' selected' : '' ?>>Leídos</option>
        </select>
        <input type="text" name="q" value="<?= htmlspecialchars($filtroTexto) ?>" placeholder="Buscar en asunto, cuerpo o alumno"
               class="input--auto" style="flex:1 1 220px; margin-top:0;" autocomplete="off">
        <button type="submit">Filtrar</button>
        <?php if ($hayFiltrosAlumnos): ?>
        <a href="inbox_send.php<?= $selectedCourseId > 0 ? '?course_id=' . $selectedCourseId : '' ?>#alumnos">Limpiar</a>
        <?php endif; ?>
    </form>

    <?php if ($mensajesAlumnos): ?>
    <p class="help" style="margin:0 0 0.4rem;">
        <?php if (!$verTodos && $totalAlumnos > count($mensajesAlumnos)): ?>
        Los <?= count($mensajesAlumnos) ?> más recientes de <?= $totalAlumnos ?>.
        <a href="<?= htmlspecialchars('?' . http_build_query(array_merge($qsAlumnos, ['ver' => 'todos']))) ?>#alumnos">Ver todos</a>
        <?php elseif ($hayBusqueda): ?>
        <?= $totalAlumnos ?> coincidencia<?= $totalAlumnos === 1 ? '' : 's' ?><?= $totalAlumnos > INBOX_ALUMNOS_MAX
            ? ' -- se muestran de a ' . INBOX_ALUMNOS_MAX . ', afina el filtro si buscas algo puntual' : '' ?>.
        <?php else: ?>
        <?= $totalAlumnos ?> mensaje<?= $totalAlumnos === 1 ? '' : 's' ?><?= $totalAlumnos > INBOX_ALUMNOS_MAX
            ? ' -- se muestran de a ' . INBOX_ALUMNOS_MAX : '' ?>.
        <?php endif; ?>
    </p>
    <?php endif; ?>

    <div class="table-wrap">
    <table>
        <tr>
            <th>Alumno</th><th>Tipo</th><th>Remitente</th><th>Asunto y mensaje</th>
            <th>Cita</th><th>Estado</th><th>Fecha</th>
        </tr>
        <?php foreach ($mensajesAlumnos as $m): ?>
        <tr>
            <td class="nowrap">
                <a href="student.php?id=<?= (int) $m['student_id'] ?>"><?= htmlspecialchars($m['display_name']) ?></a>
            </td>
            <td<?= $m['tipo'] === 'reclamo' ? ' class="badge-warn"' : '' ?>>
                <?= htmlspecialchars($tipoLabels[$m['tipo']] ?? $m['tipo']) ?>
            </td>
            <td><?= htmlspecialchars($m['remitente'] ?: 'Sistema') ?></td>
            <td>
                <details>
                    <summary style="cursor:pointer;"><?= htmlspecialchars($m['asunto']) ?></summary>
                    <p style="white-space:pre-wrap; margin:0.4rem 0 0;" class="help"><?= htmlspecialchars($m['cuerpo']) ?></p>
                </details>
            </td>
            <td class="help help--xs">
                <?= $m['fecha'] ? htmlspecialchars($m['fecha'] . ' ' . ($m['hora'] ?: '')) . '<br>' . htmlspecialchars((string) $m['procedimiento']) : '—' ?>
            </td>
            <td class="nowrap"><?= $m['leido'] ? 'Leído' : '● Sin leer' ?></td>
            <td class="mono nowrap" style="font-size:0.8rem;"><?= htmlspecialchars($m['created_at']) ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$mensajesAlumnos): ?>
        <tr><td colspan="7" class="muted">
            <?= $hayFiltrosAlumnos ? 'Ningún mensaje coincide con el filtro.' : 'Tus alumnos no han recibido mensajes todavía.' ?>
        </td></tr>
        <?php endif; ?>
    </table>
    </div>

    <?php if ($totalPaginasAlumnos > 1): ?>
    <div style="display:flex; justify-content:space-between; align-items:center; margin-top:0.5rem;">
        <?php if ($paginaAlumnos > 1): ?>
        <a href="<?= htmlspecialchars($linkAlumnos($paginaAlumnos - 1)) ?>">« Más recientes</a>
        <?php else: ?><span></span><?php endif; ?>
        <span class="help">Página <?= $paginaAlumnos ?> de <?= $totalPaginasAlumnos ?></span>
        <?php if ($paginaAlumnos < $totalPaginasAlumnos): ?>
        <a href="<?= htmlspecialchars($linkAlumnos($paginaAlumnos + 1)) ?>">Más antiguos »</a>
        <?php else: ?><span></span><?php endif; ?>
    </div>
    <?php endif; ?>
</div>

<div class="card">
    <strong>Mensajes enviados</strong>
    <?php if (!$misEnvios): ?>
    <p class="help">Todavía no has mandado mensajes.</p>
    <?php else: ?>
    <div class="scrollbox" style="margin-top:0.5rem;">
        <?php foreach ($misEnvios as $e): ?>
        <details class="pane" style="margin-bottom:0.4rem;">
            <summary style="cursor:pointer;">
                <?= htmlspecialchars($e['asunto']) ?>
                <span class="help normal">
                    -- <?= (int) $e['n_destinatarios'] ?> destinatario<?= (int) $e['n_destinatarios'] === 1 ? '' : 's' ?>
                    (<?= (int) $e['n_leidos'] ?> leído<?= (int) $e['n_leidos'] === 1 ? '' : 's' ?>), <?= htmlspecialchars($e['created_at']) ?>
                </span>
            </summary>
            <p style="white-space:pre-wrap; margin:0.5rem 0 0.3rem;"><?= htmlspecialchars($e['cuerpo']) ?></p>
            <p class="help" style="margin:0;">Para: <?= htmlspecialchars($e['destinatarios']) ?></p>
        </details>
        <?php endforeach; ?>
    </div>
    <?php endif; ?>
</div>

<div class="card">
    <strong>Enviar mensaje</strong>
    <p class="muted">
        Llega a la misma bandeja de entrada donde el alumno ve los avisos automáticos sobre el trato a
        pacientes (ver <a href="llm.php">Admin → IA Paciente</a>) -- útil para avisos de curso, o para
        probar cómo se ve la bandeja sin esperar a que un alumno cierre una atención de verdad.
    </p>
    <?php if (!$courses): ?>
    <p class="help">No tienes cursos todavía -- créalos o pide que te agreguen en <a href="courses.php">Cursos</a>.</p>
    <?php else: ?>
    <p class="help" style="margin-bottom:0.5rem;">
        <?php if ($cursoElegidoANombre !== null): ?>
        Curso: <strong><?= htmlspecialchars($cursoElegidoANombre) ?></strong><?= $contextCourseId === null && count($courses) > 1 ? ' (el primero de la lista)' : '' ?>.
        <?php if (count($courses) > 1): ?>Se cambia en el selector de curso del header.<?php endif; ?>
        <?php else: ?>
        No tienes ningún curso al que mandar avisos.
        <?php endif; ?>
    </p>

    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="course_id" value="<?= $selectedCourseId ?>">

        <div style="display:flex; gap:1.2rem; margin-bottom:0.4rem;">
            <label style="display:flex; align-items:center; gap:0.4rem; font-weight:600;">
                <input type="radio" name="destinatario" value="alumno" id="dest-alumno" class="input--auto" checked>
                Alumnos
            </label>
            <label style="display:flex; align-items:center; gap:0.4rem; font-weight:600;">
                <input type="radio" name="destinatario" value="docente" id="dest-docente" class="input--auto" <?= !$teachers ? 'disabled' : '' ?>>
                Otros docentes del curso
            </label>
        </div>

        <div id="bloque-alumnos">
        <div style="display:flex; flex-direction:column; gap:0.3rem;">
            <label style="display:flex; align-items:center; gap:0.5rem; font-weight:600;">
                <input type="radio" name="modo" value="individual" id="modo-individual" class="input--auto" checked>
                Alumnos individuales
            </label>
            <label style="display:flex; align-items:center; gap:0.5rem; font-weight:600;">
                <input type="radio" name="modo" value="grupo" id="modo-grupo" class="input--auto" <?= !$grupos ? 'disabled' : '' ?>>
                Grupo
                <select name="grupo_id" id="sel-grupo" <?= !$grupos ? 'disabled' : '' ?>>
                    <?php foreach ($grupos as $g): ?>
                    <option value="<?= (int) $g['id'] ?>"><?= htmlspecialchars($g['name']) ?> (<?= (int) $g['member_count'] ?>)</option>
                    <?php endforeach; ?>
                </select>
                <?php if (!$grupos): ?><span class="help">Este curso no tiene grupos todavía.</span><?php endif; ?>
            </label>
            <label style="display:flex; align-items:center; gap:0.5rem; font-weight:600;">
                <input type="radio" name="modo" value="todos" id="modo-todos" class="input--auto">
                Todo el curso (<?= count($roster) ?> alumno<?= count($roster) === 1 ? '' : 's' ?>)
            </label>
        </div>

        <div id="roster-box" class="scrollbox scrollbox--short pane" style="margin-top:0.4rem;">
            <?php foreach ($roster as $r): ?>
            <label class="inline-check" style="display:block; font-weight:400;">
                <input type="checkbox" name="student_ids[]" value="<?= (int) $r['id'] ?>" class="chk-alumno">
                <?= htmlspecialchars($r['display_name']) ?> <span class="mono help help--xs">(<?= htmlspecialchars($r['username']) ?>)</span>
            </label>
            <?php endforeach; ?>
            <?php if (!$roster): ?>
            <p class="help">Este curso no tiene alumnos matriculados todavía.</p>
            <?php endif; ?>
        </div>
        </div>

        <div id="bloque-docentes" class="hidden">
            <label style="display:flex; align-items:center; gap:0.5rem; font-weight:600;">
                <input type="checkbox" name="todos_docentes" value="1" id="chk-todos-docentes" class="input--auto">
                Todos los docentes del curso (<?= count($teachers) ?>)
            </label>
            <div id="teacher-box" class="scrollbox scrollbox--short pane" style="margin-top:0.4rem;">
                <?php foreach ($teachers as $t): ?>
                <label class="inline-check" style="display:block; font-weight:400;">
                    <input type="checkbox" name="teacher_ids[]" value="<?= (int) $t['id'] ?>" class="chk-docente">
                    <?= htmlspecialchars($t['display_name']) ?> <span class="mono help help--xs">(<?= htmlspecialchars($t['username']) ?>)</span>
                </label>
                <?php endforeach; ?>
                <?php if (!$teachers): ?>
                <p class="help">No hay otros docentes en este curso todavía.</p>
                <?php endif; ?>
            </div>
        </div>

        <label>Asunto
            <input type="text" name="asunto" placeholder="Ej: Recordatorio de la próxima clase" required>
        </label>
        <label>Mensaje
            <textarea name="cuerpo" rows="6" style="width:100%; padding:0.45rem; margin-top:0.2rem; border:1px solid var(--color-border-strong); border-radius:var(--radius-md);" required></textarea>
        </label>

        <button type="submit">Enviar</button>
    </form>

    <script>
        (function () {
            var radios = document.querySelectorAll('input[name="modo"]');
            var box = document.getElementById('roster-box');
            var selGrupo = document.getElementById('sel-grupo');
            if (radios.length && box) {
                function modoActivo() {
                    var checked = document.querySelector('input[name="modo"]:checked');
                    return checked ? checked.value : 'individual';
                }
                function syncAlumnos() {
                    var modo = modoActivo();
                    var esIndividual = modo === 'individual';
                    box.querySelectorAll('.chk-alumno').forEach(function (el) {
                        el.disabled = !esIndividual;
                    });
                    box.style.opacity = esIndividual ? '1' : '0.5';
                    if (selGrupo) selGrupo.disabled = modo !== 'grupo' || selGrupo.options.length === 0;
                }
                radios.forEach(function (r) { r.addEventListener('change', syncAlumnos); });
                if (selGrupo) selGrupo.addEventListener('focus', function () {
                    document.getElementById('modo-grupo').checked = true;
                    syncAlumnos();
                });
                syncAlumnos();
            }

            var destRadios = document.querySelectorAll('input[name="destinatario"]');
            var bloqueAlumnos = document.getElementById('bloque-alumnos');
            var bloqueDocentes = document.getElementById('bloque-docentes');
            var chkTodosDocentes = document.getElementById('chk-todos-docentes');
            var teacherBox = document.getElementById('teacher-box');
            if (destRadios.length && bloqueAlumnos && bloqueDocentes) {
                function syncDestinatario() {
                    var checked = document.querySelector('input[name="destinatario"]:checked');
                    var esDocente = checked && checked.value === 'docente';
                    bloqueAlumnos.style.display = esDocente ? 'none' : '';
                    bloqueDocentes.style.display = esDocente ? '' : 'none';
                }
                destRadios.forEach(function (r) { r.addEventListener('change', syncDestinatario); });
                syncDestinatario();
            }
            if (chkTodosDocentes && teacherBox) {
                function syncDocentes() {
                    teacherBox.querySelectorAll('.chk-docente').forEach(function (el) {
                        el.disabled = chkTodosDocentes.checked;
                    });
                    teacherBox.style.opacity = chkTodosDocentes.checked ? '0.5' : '1';
                }
                chkTodosDocentes.addEventListener('change', syncDocentes);
                syncDocentes();
            }
        })();
    </script>
    <?php endif; ?>
</div>
<?php
admin_footer();
