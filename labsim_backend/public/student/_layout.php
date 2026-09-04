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
    ?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LabSim - <?= htmlspecialchars($title) ?></title>
<style>
    * { box-sizing: border-box; }
    html { -webkit-text-size-adjust: 100%; }
    body { font-family: system-ui, sans-serif; margin: 0; color: #1a1a1a; background: #f7f7f8; overflow-x: hidden; }
    header { background: #1a2744; color: #fff; padding: 0.9rem 1.2rem; }
    header .brand { font-weight: 700; font-size: 1.05rem; }
    header .sub { opacity: 0.8; font-size: 0.85rem; margin-top: 0.1rem; }
    main { width: 100%; max-width: 62rem; margin: 1.5rem auto; padding: 0 1rem 3rem; }
    h1 { font-size: 1.25rem; word-break: break-word; }
    a.back { display: inline-block; margin-bottom: 1rem; color: #1a2744; font-size: 0.88rem; text-decoration: none; }
    a.back:hover { text-decoration: underline; }
    .table-wrap { width: 100%; overflow-x: auto; -webkit-overflow-scrolling: touch; }
    .table-wrap table { min-width: 30rem; }
    table { width: 100%; border-collapse: collapse; margin: 1rem 0; background: #fff; }
    th, td { text-align: left; padding: 0.5rem 0.7rem; border-bottom: 1px solid #e5e5e5; font-size: 0.9rem; }
    th { background: #eef0f4; }
    tr.clickable { cursor: pointer; }
    tr.clickable:hover { background: #f3f5fa; }
    .card { background: #fff; border-radius: 8px; padding: 1.1rem 1.4rem; margin-bottom: 1.2rem; box-shadow: 0 1px 2px rgba(0,0,0,0.06); max-width: 100%; }
    .card h2 { font-size: 1rem; margin: 0 0 0.6rem; }
    .legend { font-size: 0.8rem; color: #777; }
    .badge-warn { color: #a33; font-weight: 600; }
    .empty { color: #888; text-align: center; padding: 2rem 0; }
    .error { background: #fdecea; color: #611a15; padding: 0.6rem 0.8rem; border-radius: 4px; margin-bottom: 1rem; }
    .mono { font-family: ui-monospace, monospace; }

    @media (max-width: 40rem) {
        header { padding: 0.75rem 1rem; }
        main { padding: 0 0.6rem 2.5rem; margin-top: 1rem; }
        .card { padding: 0.9rem 1rem; border-radius: 6px; }
        h1 { font-size: 1.1rem; }
        th, td { padding: 0.4rem 0.5rem; font-size: 0.82rem; }
        .table-wrap table { min-width: 26rem; }
    }
</style>
</head>
<body>
<header>
    <div class="brand">LabSim</div>
    <div class="sub"><?= htmlspecialchars($currentUser['display_name']) ?> · Mis pacientes atendidos</div>
</header>
<main>
<?php
}

function student_footer(): void
{
    ?>
</main>
</body>
</html>
<?php
}
