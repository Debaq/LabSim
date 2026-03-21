<?php
require_once __DIR__ . '/layout.php';
$auth = require_admin();

$message = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    $subId = $_POST['submission_id'] ?? '';

    if ($action === 'review' && $subId) {
        Database::execute(
            "UPDATE submissions SET status = 'reviewed', grade = :grade, feedback = :fb,
             reviewed_by = :uid, reviewed_at = datetime('now') WHERE id = :id AND status = 'submitted'",
            [':id' => $subId, ':grade' => $_POST['grade'] ?: null, ':fb' => $_POST['feedback'] ?: null, ':uid' => $auth['sub']]
        );
        $message = 'Entrega calificada';
    }
    if ($action === 'return' && $subId) {
        Database::execute(
            "UPDATE submissions SET status = 'returned', feedback = :fb,
             reviewed_by = :uid, reviewed_at = datetime('now') WHERE id = :id AND status = 'submitted'",
            [':id' => $subId, ':fb' => $_POST['feedback'] ?: 'Revisar y corregir', ':uid' => $auth['sub']]
        );
        $message = 'Entrega devuelta';
    }
}

// Detalle
$detailId = $_GET['id'] ?? null;
if ($detailId) {
    $sub = Database::fetchOne(
        "SELECT s.*, u.username as student, u.full_name as student_name,
                c.title as case_title, c.profile_json,
                ps.title as session_title,
                r.username as reviewer
         FROM submissions s
         JOIN users u ON s.student_id = u.id
         JOIN cases c ON s.case_id = c.id
         JOIN practice_sessions ps ON s.session_id = ps.id
         LEFT JOIN users r ON s.reviewed_by = r.id
         WHERE s.id = :id",
        [':id' => $detailId]
    );
    if (!$sub) { header('Location: submissions.php'); exit; }

    render_header('Entrega: ' . $sub['student'] . ' — ' . $sub['case_title'], 'submissions');
    ?>
    <?php if ($message): ?><div class="alert alert-success"><?= htmlspecialchars($message) ?></div><?php endif; ?>
    <a href="submissions.php" class="btn btn-sm btn-outline" style="margin-bottom:20px">← Volver</a>

    <div class="detail-grid">
        <div class="detail-item"><label>Estudiante</label><div class="value"><?= htmlspecialchars($sub['student_name'] ?? $sub['student']) ?></div></div>
        <div class="detail-item"><label>Sesión</label><div class="value"><?= htmlspecialchars($sub['session_title']) ?></div></div>
        <div class="detail-item"><label>Caso</label><div class="value"><?= htmlspecialchars($sub['case_title']) ?></div></div>
        <div class="detail-item"><label>Estado</label><div class="value"><?php
            $sm = ['draft' => ['Borrador','default'], 'submitted' => ['Enviada','info'], 'reviewed' => ['Calificada','success'], 'returned' => ['Devuelta','warning']];
            $s2 = $sm[$sub['status']] ?? [$sub['status'], 'default'];
            echo render_badge($s2[0], $s2[1]);
        ?></div></div>
        <div class="detail-item"><label>Nota</label><div class="value"><?= $sub['grade'] !== null ? number_format($sub['grade'], 1) : '—' ?></div></div>
        <div class="detail-item"><label>Revisor</label><div class="value"><?= htmlspecialchars($sub['reviewer'] ?? '—') ?></div></div>
        <div class="detail-item"><label>Enviada</label><div class="value"><?= $sub['submitted_at'] ? date('d M Y H:i', strtotime($sub['submitted_at'])) : '—' ?></div></div>
        <div class="detail-item"><label>Revisada</label><div class="value"><?= $sub['reviewed_at'] ? date('d M Y H:i', strtotime($sub['reviewed_at'])) : '—' ?></div></div>
    </div>

    <?php if ($sub['feedback']): ?>
        <div class="card" style="margin-bottom:20px">
            <h4 style="margin-bottom:8px;color:var(--accent)">Feedback</h4>
            <p><?= nl2br(htmlspecialchars($sub['feedback'])) ?></p>
        </div>
    <?php endif; ?>

    <?php if ($sub['status'] === 'submitted'): ?>
    <div class="card" style="margin-bottom:20px">
        <h4 style="margin-bottom:12px;color:var(--accent)">Calificar</h4>
        <form method="POST">
            <input type="hidden" name="submission_id" value="<?= $detailId ?>">
            <div class="form-row">
                <div class="form-group">
                    <label>Nota (0-10)</label>
                    <input type="number" name="grade" step="0.1" min="0" max="10">
                </div>
            </div>
            <div class="form-group">
                <label>Feedback</label>
                <textarea name="feedback" rows="3"></textarea>
            </div>
            <div style="display:flex;gap:10px">
                <button type="submit" name="action" value="review" class="btn btn-success">Calificar</button>
                <button type="submit" name="action" value="return" class="btn btn-warning">Devolver para corrección</button>
            </div>
        </form>
    </div>
    <?php endif; ?>

    <h3 style="margin:20px 0 10px">Entrega del estudiante (JSON)</h3>
    <div class="json-viewer"><?= htmlspecialchars(json_encode(json_decode($sub['submission_json']), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)) ?></div>

    <h3 style="margin:20px 0 10px">Caso original (JSON)</h3>
    <div class="json-viewer"><?= htmlspecialchars(json_encode(json_decode($sub['profile_json']), JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE)) ?></div>
    <?php
    render_footer();
    exit;
}

// Lista
$statusFilter = $_GET['status'] ?? '';
$page = max(1, (int)($_GET['page'] ?? 1));

$where = ['1=1'];
$params = [];
if ($statusFilter) { $where[] = 's.status = :status'; $params[':status'] = $statusFilter; }

$sql = "SELECT s.id, s.status, s.grade, s.submitted_at, s.reviewed_at,
               u.username as student, u.full_name as student_name,
               c.title as case_title, ps.title as session_title
        FROM submissions s
        JOIN users u ON s.student_id = u.id
        JOIN cases c ON s.case_id = c.id
        JOIN practice_sessions ps ON s.session_id = ps.id
        WHERE " . implode(' AND ', $where) . " ORDER BY s.created_at DESC";

$result = Database::paginate($sql, $params, $page, 20);

render_header('Entregas', 'submissions');
?>

<?php if ($message): ?><div class="alert alert-success"><?= htmlspecialchars($message) ?></div><?php endif; ?>

<div class="toolbar">
    <form class="toolbar-filters" method="GET">
        <select name="status" class="auto-filter">
            <option value="">Todos</option>
            <option value="draft" <?= $statusFilter === 'draft' ? 'selected' : '' ?>>Borrador</option>
            <option value="submitted" <?= $statusFilter === 'submitted' ? 'selected' : '' ?>>Enviada</option>
            <option value="reviewed" <?= $statusFilter === 'reviewed' ? 'selected' : '' ?>>Calificada</option>
            <option value="returned" <?= $statusFilter === 'returned' ? 'selected' : '' ?>>Devuelta</option>
        </select>
    </form>
</div>

<?php
render_table(
    ['Estudiante', 'Caso', 'Sesión', 'Estado', 'Nota', 'Enviada', ''],
    $result['items'],
    function($s) {
        $sm = ['submitted' => ['Enviada','info'], 'reviewed' => ['Calificada','success'], 'returned' => ['Devuelta','warning']];
        $s2 = $sm[$s['status']] ?? [$s['status'], 'default'];
        $badge = render_badge($s2[0], $s2[1]);
        $grade = $s['grade'] !== null ? number_format($s['grade'], 1) : '—';
        $date = $s['submitted_at'] ? date('d M Y', strtotime($s['submitted_at'])) : '—';

        return "<tr>
            <td><strong>" . htmlspecialchars($s['student_name'] ?? $s['student']) . "</strong></td>
            <td>" . htmlspecialchars($s['case_title']) . "</td>
            <td>" . htmlspecialchars($s['session_title']) . "</td>
            <td>$badge</td>
            <td>$grade</td>
            <td>$date</td>
            <td><a href='submissions.php?id={$s['id']}' class='btn btn-sm btn-outline'>Ver</a></td>
        </tr>";
    }
);

render_pagination($result['pagination']['page'], $result['pagination']['pages'], "submissions.php?status=$statusFilter");
render_footer();
?>
