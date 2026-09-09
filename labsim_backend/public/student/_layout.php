<?php

declare(strict_types=1);

/**
 * Layout minimal del mini-portal de alumno (mis_pacientes.php/atencion.php).
 * A propósito NO reusa admin/_layout.php: nada de nav de gestión (cursos,
 * usuarios, LTI...), el alumno solo ve sus propios datos. Mismo criterio
 * "legible en el celular" que launch.php -- el alumno suele abrir esto desde
 * el navegador del teléfono, no siempre desde el computador.
 */
function student_header(string $title, array $currentUser): void
{
    header('Content-Type: text/html; charset=utf-8');
    $viendoComoAdmin = isset($_SESSION['admin_view_as_id'], $_SESSION['admin_user_id']);
    ?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LabSim - <?= htmlspecialchars($title) ?></title>
<script>
// Anti-FOUC: aplica el data-theme ANTES del primer render si el usuario
// eligió tema oscuro en una sesión previa.
(function () {
    try {
        var t = localStorage.getItem('labsim-theme');
        if (t === 'dark' || t === 'light') {
            document.documentElement.dataset.theme = t;
        }
    } catch (e) {}
})();
</script>
<?php
$cssV = static fn (string $path): string => (string) (@filemtime($path) ?: time());
?>
<link rel="stylesheet" href="../css/tokens.css?v=<?= $cssV(__DIR__ . '/../css/tokens.css') ?>">
<link rel="stylesheet" href="../css/base.css?v=<?= $cssV(__DIR__ . '/../css/base.css') ?>">
<link rel="stylesheet" href="../css/student.css?v=<?= $cssV(__DIR__ . '/../css/student.css') ?>">
</head>
<body>
<a href="#main-content" class="skip-link">Saltar al contenido principal</a>
<header>
    <div>
        <div class="brand">LabSim</div>
        <div class="sub"><?= htmlspecialchars($currentUser['display_name']) ?> · Mis pacientes atendidos</div>
    </div>
    <button type="button" id="theme-toggle" class="btn btn--ghost btn--sm" style="margin-top:0; padding:0.3rem 0.6rem;" aria-label="Cambiar tema claro/oscuro" title="Cambiar tema">
        <span data-theme-icon="light" hidden>☀</span>
        <span data-theme-icon="dark" hidden>☾</span>
    </button>
</header>
<?php if ($viendoComoAdmin): ?>
<div style="background:var(--color-warn-bg); color:var(--color-warn-text); padding:0.5rem 1rem; font-size:0.85rem; text-align:center;">
    Viendo como <?= htmlspecialchars($currentUser['display_name']) ?> (modo docente, solo lectura)
    &nbsp;·&nbsp; <a href="../admin/ver_como.php?salir=1" style="color:var(--color-warn-text); font-weight:600;">Volver a la ficha</a>
</div>
<?php endif; ?>
<main id="main-content">
<?php
}

function student_footer(): void
{
    ?>
</main>
<script>
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
    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', paint);
    paint();
})();
</script>
</body>
</html>
<?php
}
