<?php

declare(strict_types=1);

function admin_header(string $title, ?array $currentUser = null): void
{
    header('Content-Type: text/html; charset=utf-8');
    ?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>LabSim Admin - <?= htmlspecialchars($title) ?></title>
<style>
    * { box-sizing: border-box; }
    body { font-family: system-ui, sans-serif; margin: 0; color: #1a1a1a; background: #f7f7f8; }
    header { background: #1a2744; color: #fff; padding: 0.9rem 1.5rem; display: flex; justify-content: space-between; align-items: center; }
    header a { color: #fff; text-decoration: none; margin-right: 1.2rem; font-size: 0.95rem; opacity: 0.85; }
    header a:hover { opacity: 1; text-decoration: underline; }
    header .brand { font-weight: 700; font-size: 1.05rem; margin-right: 2rem; }
    main { width: 100%; margin: 2rem auto; padding: 0 2rem; }
    h1 { font-size: 1.4rem; }
    table { width: 100%; border-collapse: collapse; margin: 1rem 0; background: #fff; }
    th, td { text-align: left; padding: 0.5rem 0.7rem; border-bottom: 1px solid #e5e5e5; font-size: 0.9rem; }
    th { background: #eef0f4; }
    form.inline { display: inline; }
    .card { background: #fff; border-radius: 8px; padding: 1.2rem 1.5rem; margin-bottom: 1.2rem; box-shadow: 0 1px 2px rgba(0,0,0,0.06); }
    label { display: block; margin-top: 0.7rem; font-weight: 600; font-size: 0.85rem; }
    input, select { width: 100%; padding: 0.45rem; margin-top: 0.2rem; border: 1px solid #ccc; border-radius: 4px; }
    button { margin-top: 1rem; padding: 0.5rem 1.1rem; cursor: pointer; border: none; border-radius: 4px; background: #1a2744; color: #fff; }
    button.secondary { background: #888; }
    button.danger { background: #a33; }
    .error { background: #fdecea; color: #611a15; padding: 0.6rem 0.8rem; border-radius: 4px; margin-bottom: 1rem; }
    .success { background: #e8f5e9; color: #1b5e20; padding: 0.6rem 0.8rem; border-radius: 4px; margin-bottom: 1rem; }
    code { background: #eef0f4; padding: 0.15rem 0.4rem; border-radius: 3px; }
    .mono { font-family: ui-monospace, monospace; font-size: 0.85rem; word-break: break-all; }
</style>
</head>
<body>
<header>
    <div>
        <span class="brand">LabSim Admin</span>
        <?php if ($currentUser && (int) $currentUser['permission'] === Auth::PERMISSION_ADMIN): ?>
        <a href="index.php">Estado</a>
        <a href="users.php">Usuarios</a>
        <?php endif; ?>
        <a href="courses.php">Cursos</a>
        <a href="agenda.php">Fichas Clínicas</a>
        <a href="dashboard.php">Dashboard</a>
        <?php if ($currentUser && (int) $currentUser['permission'] === Auth::PERMISSION_ADMIN): ?>
        <a href="lti.php">LTI</a>
        <a href="database.php">Base de datos</a>
        <?php endif; ?>
    </div>
    <div>
        <?php if ($currentUser): ?>
            <span style="opacity:0.8; margin-right:1rem;"><?= htmlspecialchars($currentUser['display_name']) ?></span>
            <a href="logout.php">Salir</a>
        <?php endif; ?>
    </div>
</header>
<main>
<h1><?= htmlspecialchars($title) ?></h1>
<?php
}

function admin_footer(): void
{
    ?>
</main>
</body>
</html>
<?php
}
