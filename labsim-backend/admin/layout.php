<?php
/**
 * LabSim Admin Panel - Layout compartido
 */

require_once __DIR__ . '/../core/config.php';
require_once __DIR__ . '/../core/db.php';
require_once __DIR__ . '/../core/jwt.php';

function admin_auth(): ?array {
    $token = $_COOKIE['labsim_admin_token'] ?? null;
    if (!$token) return null;

    try {
        $payload = JWT::decode($token);
        if (($payload['role'] ?? '') !== 'admin') return null;
        return $payload;
    } catch (Exception $e) {
        return null;
    }
}

function require_admin(): array {
    $auth = admin_auth();
    if (!$auth) {
        header('Location: login.php');
        exit;
    }
    return $auth;
}

function render_header(string $title, string $activePage = ''): void {
    $auth = admin_auth();
    $username = $auth['username'] ?? 'Admin';
?>
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title><?= htmlspecialchars($title) ?> — LabSim Admin</title>
    <link rel="stylesheet" href="static/style.css">
</head>
<body>
    <nav class="sidebar">
        <div class="sidebar-header">
            <h2>LabSim</h2>
            <span class="badge">Admin</span>
        </div>
        <ul class="nav-links">
            <li class="<?= $activePage === 'dashboard' ? 'active' : '' ?>">
                <a href="index.php">📊 Dashboard</a>
            </li>
            <li class="<?= $activePage === 'users' ? 'active' : '' ?>">
                <a href="users.php">👥 Usuarios</a>
            </li>
            <li class="<?= $activePage === 'groups' ? 'active' : '' ?>">
                <a href="groups.php">🏫 Grupos</a>
            </li>
            <li class="<?= $activePage === 'sessions' ? 'active' : '' ?>">
                <a href="sessions.php">📋 Sesiones</a>
            </li>
            <li class="<?= $activePage === 'cases' ? 'active' : '' ?>">
                <a href="cases.php">🩺 Casos</a>
            </li>
            <li class="<?= $activePage === 'submissions' ? 'active' : '' ?>">
                <a href="submissions.php">📝 Entregas</a>
            </li>
            <li class="<?= $activePage === 'stats' ? 'active' : '' ?>">
                <a href="stats.php">📈 Estadísticas</a>
            </li>
            <li class="<?= $activePage === 'releases' ? 'active' : '' ?>">
                <a href="releases.php">🚀 Releases</a>
            </li>
            <li class="<?= $activePage === 'assets' ? 'active' : '' ?>">
                <a href="assets.php">📁 Archivos</a>
            </li>
        </ul>
        <div class="sidebar-footer">
            <span><?= htmlspecialchars($username) ?></span>
            <a href="login.php?logout=1" class="btn-logout">Cerrar sesión</a>
        </div>
    </nav>
    <main class="content">
        <header class="content-header">
            <h1><?= htmlspecialchars($title) ?></h1>
        </header>
        <div class="content-body">
<?php
}

function render_footer(): void {
?>
        </div>
    </main>
    <script src="static/admin.js"></script>
</body>
</html>
<?php
}

/**
 * Renderiza una tabla genérica
 */
function render_table(array $headers, array $rows, ?callable $rowRenderer = null): void {
    echo '<div class="table-wrapper"><table>';
    echo '<thead><tr>';
    foreach ($headers as $h) {
        echo '<th>' . htmlspecialchars($h) . '</th>';
    }
    echo '</tr></thead><tbody>';

    if (empty($rows)) {
        echo '<tr><td colspan="' . count($headers) . '" class="empty">No hay datos</td></tr>';
    } else {
        foreach ($rows as $row) {
            if ($rowRenderer) {
                echo $rowRenderer($row);
            } else {
                echo '<tr>';
                foreach ($row as $val) {
                    echo '<td>' . htmlspecialchars((string)($val ?? '')) . '</td>';
                }
                echo '</tr>';
            }
        }
    }

    echo '</tbody></table></div>';
}

/**
 * Renderiza paginación
 */
function render_pagination(int $page, int $totalPages, string $baseUrl): void {
    if ($totalPages <= 1) return;

    echo '<div class="pagination">';
    if ($page > 1) {
        echo '<a href="' . $baseUrl . '&page=' . ($page - 1) . '" class="btn btn-sm">← Anterior</a>';
    }
    echo '<span class="page-info">Página ' . $page . ' de ' . $totalPages . '</span>';
    if ($page < $totalPages) {
        echo '<a href="' . $baseUrl . '&page=' . ($page + 1) . '" class="btn btn-sm">Siguiente →</a>';
    }
    echo '</div>';
}

function render_badge(string $text, string $type = 'default'): string {
    return '<span class="badge badge-' . $type . '">' . htmlspecialchars($text) . '</span>';
}
