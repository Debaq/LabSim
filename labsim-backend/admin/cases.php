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
        // Verificar que no esté en uso en sesiones activas
        $inUse = Database::fetchOne(
            "SELECT COUNT(*) as count FROM practice_session_cases psc
             JOIN practice_sessions ps ON psc.session_id = ps.id
             WHERE psc.case_id = :cid AND ps.status IN ('approved','active')",
            [':cid' => $caseId]
        );
        if (($inUse['count'] ?? 0) > 0) {
            $message = 'No se puede eliminar: el caso está asignado a sesiones activas';
        } else {
            Database::execute('DELETE FROM cases WHERE id = :id', [':id' => $caseId]);
            $message = 'Caso eliminado';
        }
    }
    if ($action === 'toggle_archive' && $caseId) {
        $caso = Database::fetchOne('SELECT is_archived FROM cases WHERE id = :id', [':id' => $caseId]);
        if ($caso) {
            $new = ($caso['is_archived'] ?? 0) ? 0 : 1;
            Database::execute("UPDATE cases SET is_archived = :a, updated_at = datetime('now') WHERE id = :id",
                [':a' => $new, ':id' => $caseId]);
            $message = $new ? 'Caso archivado' : 'Caso desarchivado';
        }
    }
    if ($action === 'duplicate' && $caseId) {
        $caso = Database::fetchOne('SELECT * FROM cases WHERE id = :id', [':id' => $caseId]);
        if ($caso) {
            $newId = Database::uuid();
            Database::execute(
                "INSERT INTO cases (id, title, description, author_id, profile_json, schema_version, tags, difficulty, is_published, is_archived)
                 VALUES (:id, :title, :desc, :author, :profile, :schema, :tags, :diff, 0, 0)",
                [
                    ':id' => $newId,
                    ':title' => 'Copia de ' . $caso['title'],
                    ':desc' => $caso['description'],
                    ':author' => $auth['sub'],
                    ':profile' => $caso['profile_json'],
                    ':schema' => $caso['schema_version'],
                    ':tags' => $caso['tags'],
                    ':diff' => $caso['difficulty'],
                ]
            );
            $message = 'Caso duplicado';
        }
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
        $archLabel = ($c['is_archived'] ?? 0) ? 'Desarchivar' : 'Archivar';
        $archBadge = ($c['is_archived'] ?? 0) ? render_badge('Archivado', 'default') : '';

        return "<tr>
            <td><a href='cases.php?id={$c['id']}' style='color:var(--accent)'><strong>" . htmlspecialchars($c['title']) . "</strong></a></td>
            <td>" . htmlspecialchars($c['author_name'] ?? $c['author'] ?? '—') . "</td>
            <td>$diffBadge</td>
            <td>" . htmlspecialchars($c['tags'] ?: '—') . "</td>
            <td>$pubBadge $archBadge</td>
            <td>" . date('d M Y', strtotime($c['updated_at'])) . "</td>
            <td>
                <div style='display:flex;gap:4px;flex-wrap:wrap'>
                <a href='cases.php?id={$c['id']}' class='btn btn-sm btn-outline'>Ver</a>
                <form method='POST' style='display:inline'><input type='hidden' name='action' value='toggle_publish'><input type='hidden' name='case_id' value='{$c['id']}'><button class='btn btn-sm btn-outline'>$pubLabel</button></form>
                <form method='POST' style='display:inline'><input type='hidden' name='action' value='toggle_archive'><input type='hidden' name='case_id' value='{$c['id']}'><button class='btn btn-sm btn-outline'>$archLabel</button></form>
                <form method='POST' style='display:inline'><input type='hidden' name='action' value='duplicate'><input type='hidden' name='case_id' value='{$c['id']}'><button class='btn btn-sm btn-outline'>Duplicar</button></form>
                <form method='POST' style='display:inline'><input type='hidden' name='action' value='delete'><input type='hidden' name='case_id' value='{$c['id']}'><button class='btn btn-sm btn-danger' data-confirm='¿Eliminar este caso?'>Eliminar</button></form>
                </div>
            </td>
        </tr>";
    }
);

render_pagination($result['pagination']['page'], $result['pagination']['pages'], "cases.php?search=$search&published=$published");
render_footer();
?>
