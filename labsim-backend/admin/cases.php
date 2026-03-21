<?php
require_once __DIR__ . '/layout.php';
$auth = require_admin();

$message = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    $caseId = $_POST['case_id'] ?? '';

    if ($action === 'toggle_publish' && $caseId) {
        $caso = Database::fetchOne('SELECT is_published FROM cases WHERE id = :id', [':id' => $caseId]);
        if ($caso) {
            $new = $caso['is_published'] ? 0 : 1;
            Database::execute("UPDATE cases SET is_published = :p, updated_at = datetime('now') WHERE id = :id",
                [':p' => $new, ':id' => $caseId]);
            $message = $new ? 'Caso publicado' : 'Caso despublicado';
        }
    }
    if ($action === 'delete' && $caseId) {
        Database::execute('DELETE FROM cases WHERE id = :id', [':id' => $caseId]);
        $message = 'Caso eliminado';
    }
}

// Detalle
$detailId = $_GET['id'] ?? null;
if ($detailId) {
    $caso = Database::fetchOne(
        "SELECT c.*, u.username as author, u.full_name as author_name FROM cases c LEFT JOIN users u ON c.author_id = u.id WHERE c.id = :id",
        [':id' => $detailId]
    );
    if (!$caso) { header('Location: cases.php'); exit; }

    render_header('Caso: ' . $caso['title'], 'cases');
    ?>
    <a href="cases.php" class="btn btn-sm btn-outline" style="margin-bottom:20px">← Volver</a>

    <div class="detail-grid">
        <div class="detail-item"><label>Título</label><div class="value"><?= htmlspecialchars($caso['title']) ?></div></div>
        <div class="detail-item"><label>Autor</label><div class="value"><?= htmlspecialchars($caso['author_name'] ?? $caso['author'] ?? '—') ?></div></div>
        <div class="detail-item"><label>Dificultad</label><div class="value"><?= render_badge($caso['difficulty'], $caso['difficulty'] === 'hard' ? 'danger' : ($caso['difficulty'] === 'easy' ? 'success' : 'warning')) ?></div></div>
        <div class="detail-item"><label>Estado</label><div class="value"><?= $caso['is_published'] ? render_badge('Publicado', 'success') : render_badge('Borrador', 'default') ?></div></div>
        <div class="detail-item"><label>Tags</label><div class="value"><?= htmlspecialchars($caso['tags'] ?: '—') ?></div></div>
        <div class="detail-item"><label>Schema v.</label><div class="value"><?= $caso['schema_version'] ?></div></div>
    </div>

    <?php if ($caso['description']): ?>
        <p style="margin-bottom:20px;color:var(--text-secondary)"><?= htmlspecialchars($caso['description']) ?></p>
    <?php endif; ?>

    <h3 style="margin-bottom:10px">Profile JSON</h3>
    <div class="json-viewer"><?= htmlspecialchars(json_encode(json_decode($caso['profile_json']), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)) ?></div>
    <?php
    render_footer();
    exit;
}

// Lista
$page = max(1, (int)($_GET['page'] ?? 1));
$search = $_GET['search'] ?? '';
$published = $_GET['published'] ?? '';

$where = ['1=1'];
$params = [];
if ($search) { $where[] = "(c.title LIKE :s OR c.description LIKE :s)"; $params[':s'] = "%$search%"; }
if ($published !== '') { $where[] = 'c.is_published = :p'; $params[':p'] = (int)$published; }

$sql = "SELECT c.id, c.title, c.description, c.difficulty, c.tags, c.is_published, c.created_at, c.updated_at,
               u.username as author, u.full_name as author_name
        FROM cases c LEFT JOIN users u ON c.author_id = u.id
        WHERE " . implode(' AND ', $where) . " ORDER BY c.updated_at DESC";

$result = Database::paginate($sql, $params, $page, 20);

render_header('Casos Clínicos', 'cases');
?>

<?php if ($message): ?><div class="alert alert-success"><?= htmlspecialchars($message) ?></div><?php endif; ?>

<div class="toolbar">
    <form class="toolbar-filters" method="GET">
        <input type="text" name="search" placeholder="Buscar..." value="<?= htmlspecialchars($search) ?>">
        <select name="published" class="auto-filter">
            <option value="">Todos</option>
            <option value="1" <?= $published === '1' ? 'selected' : '' ?>>Publicados</option>
            <option value="0" <?= $published === '0' ? 'selected' : '' ?>>Borradores</option>
        </select>
        <button type="submit" class="btn btn-sm btn-outline">Filtrar</button>
    </form>
</div>

<?php
render_table(
    ['Título', 'Autor', 'Dificultad', 'Tags', 'Estado', 'Actualizado', 'Acciones'],
    $result['items'],
    function($c) {
        $diffBadge = render_badge($c['difficulty'], $c['difficulty'] === 'hard' ? 'danger' : ($c['difficulty'] === 'easy' ? 'success' : 'warning'));
        $pubBadge = $c['is_published'] ? render_badge('Publicado', 'success') : render_badge('Borrador', 'default');
        $pubLabel = $c['is_published'] ? 'Despublicar' : 'Publicar';

        return "<tr>
            <td><a href='cases.php?id={$c['id']}' style='color:var(--accent)'><strong>" . htmlspecialchars($c['title']) . "</strong></a></td>
            <td>" . htmlspecialchars($c['author_name'] ?? $c['author'] ?? '—') . "</td>
            <td>$diffBadge</td>
            <td>" . htmlspecialchars($c['tags'] ?: '—') . "</td>
            <td>$pubBadge</td>
            <td>" . date('d M Y', strtotime($c['updated_at'])) . "</td>
            <td>
                <form method='POST' style='display:inline'><input type='hidden' name='action' value='toggle_publish'><input type='hidden' name='case_id' value='{$c['id']}'><button class='btn btn-sm btn-outline'>$pubLabel</button></form>
                <a href='cases.php?id={$c['id']}' class='btn btn-sm btn-outline'>Ver</a>
            </td>
        </tr>";
    }
);

render_pagination($result['pagination']['page'], $result['pagination']['pages'], "cases.php?search=$search&published=$published");
render_footer();
?>
