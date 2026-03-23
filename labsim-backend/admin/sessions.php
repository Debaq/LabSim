<?php
require_once __DIR__ . '/layout.php';
$auth = require_admin();

$message = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $action = $_POST['action'] ?? '';
    $sessionId = $_POST['session_id'] ?? '';

    if ($action === 'approve' && $sessionId) {
        Database::execute(
            "UPDATE practice_sessions SET status = 'approved', approved_by = :uid, updated_at = datetime('now') WHERE id = :id AND status = 'pending_approval'",
            [':id' => $sessionId, ':uid' => $auth['sub']]
        );
        $message = 'Sesión aprobada';
    }
    if ($action === 'reject' && $sessionId) {
        Database::execute(
            "UPDATE practice_sessions SET status = 'cancelled', updated_at = datetime('now') WHERE id = :id AND status = 'pending_approval'",
            [':id' => $sessionId]
        );
        $message = 'Sesión rechazada';
    }
    if ($action === 'activate' && $sessionId) {
        Database::execute(
            "UPDATE practice_sessions SET status = 'active', updated_at = datetime('now') WHERE id = :id AND status = 'approved'",
            [':id' => $sessionId]
        );
        $message = 'Sesión activada';
    }
    if ($action === 'complete' && $sessionId) {
        Database::execute(
            "UPDATE practice_sessions SET status = 'completed', updated_at = datetime('now') WHERE id = :id AND status IN ('active','approved')",
            [':id' => $sessionId]
        );
        $message = 'Sesión completada';
    }
    if ($action === 'delete' && $sessionId) {
        Database::execute('DELETE FROM agenda_items WHERE session_id = :sid', [':sid' => $sessionId]);
        Database::execute('DELETE FROM practice_session_cases WHERE session_id = :sid', [':sid' => $sessionId]);
        Database::execute('DELETE FROM session_guides WHERE session_id = :sid', [':sid' => $sessionId]);
        Database::execute('DELETE FROM practice_sessions WHERE id = :id', [':id' => $sessionId]);
        $message = 'Sesión eliminada';
    }
    if ($action === 'toggle_archive' && $sessionId) {
        $s = Database::fetchOne('SELECT is_archived FROM practice_sessions WHERE id = :id', [':id' => $sessionId]);
        if ($s) {
            $new = ($s['is_archived'] ?? 0) ? 0 : 1;
            Database::execute("UPDATE practice_sessions SET is_archived = :a, updated_at = datetime('now') WHERE id = :id",
                [':a' => $new, ':id' => $sessionId]);
            $message = $new ? 'Sesión archivada' : 'Sesión desarchivada';
        }
    }
    if ($action === 'duplicate' && $sessionId) {
        $s = Database::fetchOne('SELECT * FROM practice_sessions WHERE id = :id', [':id' => $sessionId]);
        if ($s) {
            $newId = Database::uuid();
            Database::execute(
                "INSERT INTO practice_sessions (id, title, description, created_by, status,
                    scheduled_date, scheduled_time, duration_minutes, location,
                    instructions, max_submissions, allow_late_submission, due_date,
                    session_type, course_id, centro_enabled, end_date)
                 VALUES (:id, :title, :desc, :uid, 'draft',
                    :date, :time, :dur, :loc,
                    :instr, :max, :late, :due,
                    :stype, :cid, :centro, :edate)",
                [
                    ':id' => $newId,
                    ':title' => 'Copia de ' . $s['title'],
                    ':desc' => $s['description'],
                    ':uid' => $auth['sub'],
                    ':date' => $s['scheduled_date'],
                    ':time' => $s['scheduled_time'],
                    ':dur' => $s['duration_minutes'],
                    ':loc' => $s['location'],
                    ':instr' => $s['instructions'],
                    ':max' => $s['max_submissions'],
                    ':late' => $s['allow_late_submission'],
                    ':due' => $s['due_date'],
                    ':stype' => $s['session_type'],
                    ':cid' => $s['course_id'],
                    ':centro' => $s['centro_enabled'],
                    ':edate' => $s['end_date'],
                ]
            );
            // Copiar casos asociados
            $cases = Database::fetchAll(
                'SELECT case_id, order_index, is_required FROM practice_session_cases WHERE session_id = :sid',
                [':sid' => $sessionId]
            );
            foreach ($cases as $c) {
                Database::execute(
                    "INSERT INTO practice_session_cases (session_id, case_id, order_index, is_required)
                     VALUES (:sid, :cid, :ord, :req)",
                    [':sid' => $newId, ':cid' => $c['case_id'], ':ord' => $c['order_index'], ':req' => $c['is_required']]
                );
            }
            $message = 'Sesión duplicada';
        }
    }
}

// Filtros
$statusFilter = $_GET['status'] ?? '';
$page = max(1, (int)($_GET['page'] ?? 1));

$where = ['1=1'];
$params = [];
if ($statusFilter) {
    $where[] = 'ps.status = :status';
    $params[':status'] = $statusFilter;
}

$sql = "SELECT ps.*, u.username as creator, u.full_name as creator_name,
               g.name as group_name,
               (SELECT COUNT(*) FROM practice_session_cases psc WHERE psc.session_id = ps.id) as case_count,
               (SELECT COUNT(*) FROM submissions s WHERE s.session_id = ps.id) as submission_count
        FROM practice_sessions ps
        LEFT JOIN users u ON ps.created_by = u.id
        LEFT JOIN student_groups g ON ps.group_id = g.id
        WHERE " . implode(' AND ', $where) . "
        ORDER BY ps.scheduled_date DESC, ps.created_at DESC";

$result = Database::paginate($sql, $params, $page, 20);

render_header('Sesiones Prácticas', 'sessions');
?>

<?php if ($message): ?><div class="alert alert-success"><?= htmlspecialchars($message) ?></div><?php endif; ?>

<div class="toolbar">
    <form class="toolbar-filters" method="GET">
        <select name="status" class="auto-filter">
            <option value="">Todos los estados</option>
            <option value="draft" <?= $statusFilter === 'draft' ? 'selected' : '' ?>>Borrador</option>
            <option value="pending_approval" <?= $statusFilter === 'pending_approval' ? 'selected' : '' ?>>Pendiente aprobación</option>
            <option value="approved" <?= $statusFilter === 'approved' ? 'selected' : '' ?>>Aprobada</option>
            <option value="active" <?= $statusFilter === 'active' ? 'selected' : '' ?>>Activa</option>
            <option value="completed" <?= $statusFilter === 'completed' ? 'selected' : '' ?>>Completada</option>
            <option value="cancelled" <?= $statusFilter === 'cancelled' ? 'selected' : '' ?>>Cancelada</option>
        </select>
    </form>
</div>

<?php
$statusColors = [
    'draft' => 'default', 'pending_approval' => 'warning', 'approved' => 'info',
    'active' => 'success', 'completed' => 'docente', 'cancelled' => 'danger',
];

render_table(
    ['Título', 'Creador', 'Grupo', 'Fecha', 'Casos', 'Entregas', 'Estado', 'Acciones'],
    $result['items'],
    function($s) use ($statusColors, $auth) {
        $badge = render_badge($s['status'], $statusColors[$s['status']] ?? 'default');
        $date = $s['scheduled_date'] ? date('d M Y', strtotime($s['scheduled_date'])) . ($s['scheduled_time'] ? " {$s['scheduled_time']}" : '') : '—';

        $actions = '<div style="display:flex;gap:4px;flex-wrap:wrap">';
        if ($s['status'] === 'pending_approval') {
            $actions .= '<form method="POST" style="display:inline"><input type="hidden" name="action" value="approve"><input type="hidden" name="session_id" value="' . $s['id'] . '"><button class="btn btn-sm btn-success">Aprobar</button></form>';
            $actions .= '<form method="POST" style="display:inline"><input type="hidden" name="action" value="reject"><input type="hidden" name="session_id" value="' . $s['id'] . '"><button class="btn btn-sm btn-danger" data-confirm="¿Rechazar sesión?">Rechazar</button></form>';
        } elseif ($s['status'] === 'approved') {
            $actions .= '<form method="POST" style="display:inline"><input type="hidden" name="action" value="activate"><input type="hidden" name="session_id" value="' . $s['id'] . '"><button class="btn btn-sm btn-success">Activar</button></form>';
        } elseif ($s['status'] === 'active') {
            $actions .= '<form method="POST" style="display:inline"><input type="hidden" name="action" value="complete"><input type="hidden" name="session_id" value="' . $s['id'] . '"><button class="btn btn-sm btn-outline">Completar</button></form>';
        }
        $archLabel = ($s['is_archived'] ?? 0) ? 'Desarchivar' : 'Archivar';
        $actions .= '<form method="POST" style="display:inline"><input type="hidden" name="action" value="toggle_archive"><input type="hidden" name="session_id" value="' . $s['id'] . '"><button class="btn btn-sm btn-outline">' . $archLabel . '</button></form>';
        $actions .= '<form method="POST" style="display:inline"><input type="hidden" name="action" value="duplicate"><input type="hidden" name="session_id" value="' . $s['id'] . '"><button class="btn btn-sm btn-outline">Duplicar</button></form>';
        $actions .= '<form method="POST" style="display:inline"><input type="hidden" name="action" value="delete"><input type="hidden" name="session_id" value="' . $s['id'] . '"><button class="btn btn-sm btn-danger" data-confirm="¿Eliminar esta sesión y todos sus datos?">Eliminar</button></form>';
        $actions .= '</div>';

        $archBadge = ($s['is_archived'] ?? 0) ? ' ' . render_badge('Archivada', 'default') : '';

        return "<tr>
            <td><strong>" . htmlspecialchars($s['title']) . "</strong></td>
            <td>" . htmlspecialchars($s['creator_name'] ?? $s['creator'] ?? '—') . "</td>
            <td>" . htmlspecialchars($s['group_name'] ?? '—') . "</td>
            <td>$date</td>
            <td>{$s['case_count']}</td>
            <td>{$s['submission_count']}</td>
            <td>$badge$archBadge</td>
            <td>$actions</td>
        </tr>";
    }
);

render_pagination($result['pagination']['page'], $result['pagination']['pages'], "sessions.php?status=$statusFilter");
render_footer();
?>
