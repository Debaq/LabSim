<?php

declare(strict_types=1);

/** Registra un CSS extra de página para que admin_header lo<link>ee.
 * Uso: admin_add_css('case.css'); admin_header(...); */
function admin_add_css(string $filename): void
{
    $GLOBALS['__admin_extra_css'][] = $filename;
}

function admin_extra_css(): array
{
    return array_values(array_unique($GLOBALS['__admin_extra_css'] ?? []));
}

/** Registra un JS extra de página; admin_footer lo emite al final del <body>,
 * en el orden en que se registró. Uso: admin_add_js('case/tabs.js'); */
function admin_add_js(string $filename): void
{
    $GLOBALS['__admin_extra_js'][] = $filename;
}

function admin_extra_js(): array
{
    return array_values(array_unique($GLOBALS['__admin_extra_js'] ?? []));
}

/** ?v=filemtime: sin esto un deploy de CSS/JS queda con cache vieja. */
function admin_asset_version(string $path): string
{
    return (string) (@filemtime($path) ?: time());
}

/**
 * Curso "en foco" de la sesión admin (F4 del rediseño de cursos, ver
 * docs/decisiones.md). El trabajo docente es todo por curso, y cada página resolvía eso
 * con su propio <select>: agenda tenía el suyo, la bandeja otro, el
 * dashboard ninguno. El foco se elige una vez en el header y lo leen todas.
 *
 * ?curso=N lo cambia, ?curso=todos lo saca. Solo es un recorte de vista: los
 * permisos siguen resolviéndose aparte, con Courses::canAdminister().
 * Devuelve null = sin recorte (el admin ve todo; el docente, todo lo suyo).
 */
function admin_course_context(?array $me): ?int
{
    if (!$me) {
        return null;
    }
    if (!array_key_exists('__admin_course_ctx', $GLOBALS)) {
        $ctx = null;
        if (isset($_GET['curso'])) {
            $raw = trim((string) $_GET['curso']);
            if ($raw === '' || $raw === 'todos') {
                unset($_SESSION['admin_course_ctx']);
            } elseif (ctype_digit($raw) && Courses::canAdminister((int) $raw, $me)) {
                $_SESSION['admin_course_ctx'] = (int) $raw;
            }
        }
        if (isset($_SESSION['admin_course_ctx'])) {
            $ctx = (int) $_SESSION['admin_course_ctx'];
        }
        // El docente de un solo curso está siempre en ese curso: no tiene
        // entre qué elegir y el selector ni se le muestra.
        if ($ctx === null && (int) $me['permission'] !== Auth::PERMISSION_ADMIN) {
            $mis = Courses::teacherCourseIds((int) $me['id']);
            if (count($mis) === 1) {
                $ctx = (int) $mis[0];
            }
        }
        // Un curso que dejó de ser suyo (o que se borró) no puede quedar
        // filtrando en silencio.
        if ($ctx !== null && !Courses::canAdminister($ctx, $me)) {
            unset($_SESSION['admin_course_ctx']);
            $ctx = null;
        }
        $GLOBALS['__admin_course_ctx'] = $ctx;
    }
    return $GLOBALS['__admin_course_ctx'];
}

/** Pone el foco en $courseId (entrar a la página de un curso es elegirlo). */
function admin_set_course_context(int $courseId): void
{
    $_SESSION['admin_course_ctx'] = $courseId;
    $GLOBALS['__admin_course_ctx'] = $courseId;
}

/** Cursos entre los que este usuario puede elegir foco. */
function admin_context_courses(?array $me): array
{
    if (!$me) {
        return [];
    }
    if ((int) $me['permission'] === Auth::PERMISSION_ADMIN) {
        return Db::get()->query('SELECT id, name, active FROM courses ORDER BY active DESC, name')->fetchAll();
    }
    $ids = Courses::teacherCourseIds((int) $me['id']);
    if (!$ids) {
        return [];
    }
    $stmt = Db::get()->prepare(
        'SELECT id, name, active FROM courses WHERE id IN (' . implode(',', array_fill(0, count($ids), '?')) . ')
         ORDER BY active DESC, name'
    );
    $stmt->execute($ids);
    return $stmt->fetchAll();
}

/**
 * Los GET actuales como <input hidden>, para que cambiar de curso no borre
 * el mes que se estaba mirando en la agenda ni la página de la bandeja. En
 * courses.php se omite `id`: ahí cambiar de curso es ir al otro curso, no
 * quedarse en la ficha del anterior.
 */
function admin_context_hidden_fields(): string
{
    $enCursos = basename($_SERVER['PHP_SELF'] ?? '') === 'courses.php';
    $out = '';
    foreach ($_GET as $k => $v) {
        if ($k === 'curso' || !is_scalar($v) || ($enCursos && $k === 'id')) {
            continue;
        }
        $out .= '<input type="hidden" name="' . htmlspecialchars((string) $k) . '" value="' . htmlspecialchars((string) $v) . '">';
    }
    return $out;
}

function admin_header(string $title, ?array $currentUser = null): void
{
    header('Content-Type: text/html; charset=utf-8');
    ?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LabSim Admin - <?= htmlspecialchars($title) ?></title>
<script>
// Anti-FOUC: aplica el data-theme ANTES de que se renderice el CSS.
// Si el usuario eligió "oscuro" en una sesión previa, el primer paint ya es oscuro.
(function () {
    try {
        var t = localStorage.getItem('labsim-theme');
        if (t === 'dark' || t === 'light') {
            document.documentElement.dataset.theme = t;
        }
    } catch (e) { /* localStorage bloqueado = sin override */ }
})();
</script>
<link rel="stylesheet" href="../css/tokens.css?v=<?= admin_asset_version(__DIR__ . '/../css/tokens.css') ?>">
<link rel="stylesheet" href="../css/base.css?v=<?= admin_asset_version(__DIR__ . '/../css/base.css') ?>">
<link rel="stylesheet" href="../css/admin.css?v=<?= admin_asset_version(__DIR__ . '/../css/admin.css') ?>">
<?php foreach (admin_extra_css() as $css): ?>
<link rel="stylesheet" href="../css/<?= htmlspecialchars($css) ?>?v=<?= admin_asset_version(__DIR__ . '/../css/' . $css) ?>">
<?php endforeach; ?>
</head>
<body>
<a href="#main-content" class="skip-link">Saltar al contenido principal</a>
<header>
    <div>
        <span class="brand">LabSim Admin</span>
        <?php $isFullAdmin = $currentUser && (int) $currentUser['permission'] === Auth::PERMISSION_ADMIN; ?>
        <nav class="admin-nav">
            <?php
            // Marca aria-current en el link de la página actual (lector de
            // pantalla: "página actual"). Los grupos arrancan siempre
            // colapsados -- se abren solo al click (ver script en el footer),
            // así el header se ve igual en toda la app sin importar la sección.
            $currentPage = basename($_SERVER['PHP_SELF'] ?? '');
            $ariaCurrent = static fn (string $href): string =>
                basename(parse_url($href, PHP_URL_PATH) ?: '') === $currentPage
                    ? ' aria-current="page"' : '';
            ?>
            <details class="nav-group" name="labsim-nav">
                <summary class="nav-label">Docencia<span class="nav-caret">▾</span></summary>
                <div class="nav-dropdown">
                    <a href="dashboard.php"<?= $ariaCurrent('dashboard.php') ?>>Dashboard</a>
                    <hr>
                    <a href="agenda.php"<?= $ariaCurrent('agenda.php') ?>>Agendas</a>
                    <a href="patients.php"<?= $ariaCurrent('patients.php') ?>>Fichas Clínicas</a>
                    <hr>
                    <a href="courses.php"<?= $ariaCurrent('courses.php') ?>>Cursos</a>
                    <a href="inbox_send.php"<?= $ariaCurrent('inbox_send.php') ?>>Bandeja de entrada</a>
                </div>
            </details>
            <?php if ($isFullAdmin): ?>
            <details class="nav-group" name="labsim-nav">
                <summary class="nav-label">Sistema<span class="nav-caret">▾</span></summary>
                <div class="nav-dropdown">
                    <a href="index.php"<?= $ariaCurrent('index.php') ?>>Estado</a>
                    <hr>
                    <a href="users.php"<?= $ariaCurrent('users.php') ?>>Usuarios</a>
                    <a href="tokens.php"<?= $ariaCurrent('tokens.php') ?>>Sesiones</a>
                    <a href="audit.php"<?= $ariaCurrent('audit.php') ?>>Auditoría</a>
                    <a href="versiones.php"<?= $ariaCurrent('versiones.php') ?>>Versiones de la app</a>
                </div>
            </details>
            <details class="nav-group" name="labsim-nav">
                <summary class="nav-label">Integraciones<span class="nav-caret">▾</span></summary>
                <div class="nav-dropdown">
                    <a href="lti.php"<?= $ariaCurrent('lti.php') ?>>LTI</a>
                </div>
            </details>
            <details class="nav-group" name="labsim-nav">
                <summary class="nav-label">Datos e IA<span class="nav-caret">▾</span></summary>
                <div class="nav-dropdown">
                    <a href="llm.php"<?= $ariaCurrent('llm.php') ?>>IA Paciente</a>
                    <a href="database.php"<?= $ariaCurrent('database.php') ?>>Base de datos</a>
                </div>
            </details>
            <details class="nav-group" name="labsim-nav">
                <summary class="nav-label">Configuración<span class="nav-caret">▾</span></summary>
                <div class="nav-dropdown">
                    <a href="normativas.php"<?= $ariaCurrent('normativas.php') ?>>Normativas</a>
                </div>
            </details>
            <?php endif; ?>
        </nav>
    </div>
    <div class="row row--center">
        <?php
        // Selector de curso: solo cuando hay entre qué elegir (un docente con
        // un curso ya está siempre en el suyo, ver admin_course_context()).
        $ctxCourses = admin_context_courses($currentUser);
        $ctxActual = admin_course_context($currentUser);
        ?>
        <?php if (count($ctxCourses) > 1): ?>
        <form method="get" class="course-context">
            <?= admin_context_hidden_fields() ?>
            <select name="curso" onchange="this.form.submit()" aria-label="Curso en foco" title="Acota agenda, fichas, dashboard y bandeja a un curso">
                <option value="todos"<?= $ctxActual === null ? ' selected' : '' ?>>Todos los cursos</option>
                <?php foreach ($ctxCourses as $cc): ?>
                <option value="<?= (int) $cc['id'] ?>"<?= $ctxActual === (int) $cc['id'] ? ' selected' : '' ?>><?= htmlspecialchars($cc['name']) ?><?= $cc['active'] ? '' : ' (archivado)' ?></option>
                <?php endforeach; ?>
            </select>
            <noscript><button type="submit" class="btn btn--sm">Ir</button></noscript>
        </form>
        <?php endif; ?>
        <?php if ($currentUser): ?>
            <a href="perfil.php" title="Mi perfil: usuario y contraseña para la app"<?= $currentPage === 'perfil.php' ? ' aria-current="page"' : '' ?>><?= htmlspecialchars($currentUser['display_name']) ?></a>
            <a href="logout.php">Salir</a>
        <?php endif; ?>
        <button type="button" id="theme-toggle" class="btn btn--ghost btn--sm" style="margin-top:0; padding:0.3rem 0.6rem;" aria-label="Cambiar tema claro/oscuro" title="Cambiar tema">
            <span data-theme-icon="light" hidden>☀</span>
            <span data-theme-icon="dark" hidden>☾</span>
        </button>
    </div>
</header>
<main id="main-content">
<h1><?= htmlspecialchars($title) ?></h1>
<?php
}

/** Input hidden con el token CSRF de la sesión actual -- va dentro de cada <form method="post">. */
function csrf_field(): string
{
    return '<input type="hidden" name="csrf_token" value="' . htmlspecialchars(Auth::csrfToken()) . '">';
}

function admin_footer(): void
{
    ?>
</main>
<script>
// Toggle de tema: lee la preferencia actual (explícita o sistema), la invierte,
// guarda en localStorage. Aplica data-theme al <html> para que el CSS reaccione.
(function () {
    var btn = document.getElementById('theme-toggle');
    if (!btn) return;

    function currentTheme() {
        var explicit = document.documentElement.dataset.theme;
        if (explicit === 'dark' || explicit === 'light') return explicit;
        return window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
    }

    function paint() {
        var t = currentTheme();
        btn.querySelectorAll('[data-theme-icon]').forEach(function (el) {
            el.hidden = el.dataset.themeIcon !== t;
        });
        btn.setAttribute('aria-pressed', t === 'dark' ? 'true' : 'false');
    }

    btn.addEventListener('click', function () {
        var next = currentTheme() === 'dark' ? 'light' : 'dark';
        document.documentElement.dataset.theme = next;
        try { localStorage.setItem('labsim-theme', next); } catch (e) {}
        paint();
    });

    // Si el sistema cambia de tema mientras la página está abierta, sincroniza el icono.
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', paint);
    paint();
})();

// Nav dropdowns (<details class="nav-group">) y menús de fila
// (<details class="row-menu">, ej. patients.php): <details> nativo no se
// cierra solo al clickear afuera ni cuando abrís otro -- lo agregamos acá.
(function () {
    var groups = document.querySelectorAll('details.nav-group, details.row-menu');
    if (!groups.length) return;

    groups.forEach(function (g) {
        g.addEventListener('toggle', function () {
            if (g.open) {
                groups.forEach(function (other) {
                    if (other !== g) other.open = false;
                });
            }
        });
    });

    document.addEventListener('click', function (e) {
        groups.forEach(function (g) {
            if (g.open && !g.contains(e.target)) g.open = false;
        });
    });
})();
</script>
<?php if (!empty($_SESSION['admin_user_id'])): ?>
<script src="../js/session_guard.js?v=<?= admin_asset_version(__DIR__ . '/../js/session_guard.js') ?>"
        data-session-guard
        data-segundos="<?= Auth::sessionSecondsLeft() ?>"
        data-ping="../session_ping.php"
        data-destino="login.php?expirada=1"></script>
<?php endif; ?>
<?php foreach (admin_extra_js() as $js): ?>
<script src="../js/<?= htmlspecialchars($js) ?>?v=<?= admin_asset_version(__DIR__ . '/../js/' . $js) ?>"></script>
<?php endforeach; ?>
</body>
</html>
<?php
}
