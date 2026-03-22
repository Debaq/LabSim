<?php
/**
 * LabSim Backend - Estadísticas
 *
 * GET /stats/overview          → Dashboard global (admin)
 * GET /stats/students          → Stats de estudiantes (docente)
 * GET /stats/students/:id      → Detalle de un estudiante
 * GET /stats/me                → Mis propias stats
 * GET /stats/simulators        → Uso por simulador
 * GET /stats/encounters        → Tiempos por caso/encuentro
 * GET /stats/export            → Export CSV (admin)
 */

require_once __DIR__ . '/../core/auth_middleware.php';

$action = $routeSegments[0] ?? null;
$subId = $routeSegments[1] ?? null;

switch (true) {

    // ─── OVERVIEW (admin) ───────────────────────────
    case $method === 'GET' && $action === 'overview':
        $auth = require_auth('admin');

        $stats = [
            'totalUsers' => Database::fetchOne("SELECT COUNT(*) as c FROM users WHERE is_active = 1")['c'],
            'usersByRole' => Database::fetchAll("SELECT role, COUNT(*) as count FROM users WHERE is_active = 1 GROUP BY role"),
            'totalCases' => Database::fetchOne("SELECT COUNT(*) as c FROM cases")['c'],
            'publishedCases' => Database::fetchOne("SELECT COUNT(*) as c FROM cases WHERE is_published = 1")['c'],
            'totalGroups' => Database::fetchOne("SELECT COUNT(*) as c FROM student_groups WHERE is_active = 1")['c'],
            'activeSessions' => Database::fetchOne("SELECT COUNT(*) as c FROM practice_sessions WHERE status IN ('approved','active')")['c'],
            'pendingApproval' => Database::fetchOne("SELECT COUNT(*) as c FROM practice_sessions WHERE status = 'pending_approval'")['c'],
            'pendingSubmissions' => Database::fetchOne("SELECT COUNT(*) as c FROM submissions WHERE status = 'submitted'")['c'],
            'totalAppSessions' => Database::fetchOne("SELECT COUNT(*) as c FROM app_sessions")['c'],
            'totalEvents' => Database::fetchOne("SELECT COUNT(*) as c FROM simulator_events")['c'],
            'recentActivity' => Database::fetchAll(
                "SELECT DATE(created_at) as date, COUNT(*) as sessions
                 FROM app_sessions WHERE created_at > datetime('now', '-30 days')
                 GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 30"
            ),
        ];

        json_response($stats);
        break;

    // ─── STUDENTS LIST (docente/instructor) ─────────
    case $method === 'GET' && $action === 'students' && $subId === null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $where = ["u.role = 'estudiante'", 'u.is_active = 1'];
        $params = [];

        $from = query_param('from');
        $to = query_param('to');

        $studentId = query_param('studentId');
        if ($studentId) {
            $where[] = 'u.id = :sid';
            $params[':sid'] = $studentId;
        }

        // Docente/instructor solo ven sus estudiantes (mismos grupos)
        if ($auth['role'] !== 'admin') {
            $where[] = "EXISTS (
                SELECT 1 FROM group_members gm1
                JOIN group_members gm2 ON gm1.group_id = gm2.group_id
                WHERE gm1.user_id = :uid AND gm2.user_id = u.id
            )";
            $params[':uid'] = $auth['sub'];
        }

        $dateFilter = '';
        if ($from) { $dateFilter .= " AND pes.started_at >= :from"; $params[':from'] = $from; }
        if ($to) { $dateFilter .= " AND pes.started_at <= :to"; $params[':to'] = $to; }

        $sql = "SELECT u.id, u.username, u.full_name, u.institution,
                       COUNT(DISTINCT pes.id) as total_encounters,
                       AVG(pes.total_duration_secs) as avg_duration,
                       COUNT(DISTINCT sub.id) as total_submissions,
                       AVG(sub.grade) as avg_grade,
                       MAX(pes.started_at) as last_activity
                FROM users u
                LEFT JOIN patient_encounter_stats pes ON pes.user_id = u.id $dateFilter
                LEFT JOIN submissions sub ON sub.student_id = u.id AND sub.status = 'reviewed'
                WHERE " . implode(' AND ', $where) . "
                GROUP BY u.id
                ORDER BY u.full_name";

        $page = query_int('page', 1);
        $limit = query_int('limit', DEFAULT_PAGE_SIZE);
        json_response(Database::paginate($sql, $params, $page, $limit));
        break;

    // ─── STUDENT DETAIL ─────────────────────────────
    case $method === 'GET' && $action === 'students' && $subId !== null:
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $student = Database::fetchOne(
            "SELECT id, username, full_name, institution, created_at FROM users WHERE id = :id AND role = 'estudiante'",
            [':id' => $subId]
        );
        if (!$student) error_response('Estudiante no encontrado', 404);

        // Encounters
        $student['encounters'] = Database::fetchAll(
            "SELECT pes.*, c.title as case_title
             FROM patient_encounter_stats pes
             LEFT JOIN cases c ON pes.case_id = c.id
             WHERE pes.user_id = :uid
             ORDER BY pes.started_at DESC LIMIT 50",
            [':uid' => $subId]
        );

        // Submissions
        $student['submissions'] = Database::fetchAll(
            "SELECT s.id, s.status, s.grade, s.feedback, s.submitted_at, s.reviewed_at,
                    c.title as case_title, ps.title as session_title
             FROM submissions s
             JOIN cases c ON s.case_id = c.id
             JOIN practice_sessions ps ON s.session_id = ps.id
             WHERE s.student_id = :uid
             ORDER BY s.created_at DESC LIMIT 50",
            [':uid' => $subId]
        );

        // Module stats
        $student['moduleStats'] = Database::fetchAll(
            "SELECT module_id, SUM(time_spent_secs) as total_time, AVG(time_spent_secs) as avg_time,
                    SUM(edits_count) as total_edits, COUNT(*) as sessions
             FROM module_interaction_stats WHERE user_id = :uid
             GROUP BY module_id ORDER BY total_time DESC",
            [':uid' => $subId]
        );

        json_response(['student' => $student]);
        break;

    // ─── MIS STATS (estudiante) ─────────────────────
    case $method === 'GET' && $action === 'me':
        $auth = require_auth();

        $stats = [];

        // Resumen general
        $stats['summary'] = Database::fetchOne(
            "SELECT COUNT(*) as total_encounters,
                    AVG(total_duration_secs) as avg_duration,
                    SUM(modules_completed) as total_modules_completed,
                    SUM(total_edits) as total_edits
             FROM patient_encounter_stats WHERE user_id = :uid",
            [':uid' => $auth['sub']]
        );

        // Últimos encounters
        $stats['recentEncounters'] = Database::fetchAll(
            "SELECT pes.*, c.title as case_title
             FROM patient_encounter_stats pes
             LEFT JOIN cases c ON pes.case_id = c.id
             WHERE pes.user_id = :uid
             ORDER BY pes.started_at DESC LIMIT 20",
            [':uid' => $auth['sub']]
        );

        // Mis entregas
        $stats['submissions'] = Database::fetchAll(
            "SELECT s.id, s.status, s.grade, s.feedback, s.submitted_at,
                    c.title as case_title, ps.title as session_title
             FROM submissions s
             JOIN cases c ON s.case_id = c.id
             JOIN practice_sessions ps ON s.session_id = ps.id
             WHERE s.student_id = :uid
             ORDER BY s.created_at DESC LIMIT 20",
            [':uid' => $auth['sub']]
        );

        // Tiempo por módulo
        $stats['moduleBreakdown'] = Database::fetchAll(
            "SELECT module_id, SUM(time_spent_secs) as total_time, AVG(time_spent_secs) as avg_time, COUNT(*) as uses
             FROM module_interaction_stats WHERE user_id = :uid
             GROUP BY module_id ORDER BY total_time DESC",
            [':uid' => $auth['sub']]
        );

        // Progresión temporal (últimos 30 encuentros)
        $stats['progression'] = Database::fetchAll(
            "SELECT total_duration_secs, modules_completed, started_at
             FROM patient_encounter_stats WHERE user_id = :uid
             ORDER BY started_at DESC LIMIT 30",
            [':uid' => $auth['sub']]
        );

        json_response($stats);
        break;

    // ─── SIMULATORS USAGE ───────────────────────────
    case $method === 'GET' && $action === 'simulators':
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $where = ['1=1'];
        $params = [];

        $simulator = query_param('simulator');
        if ($simulator) {
            $where[] = 'se.simulator = :sim';
            $params[':sim'] = $simulator;
        }

        $from = query_param('from');
        if ($from) { $where[] = 'se.event_timestamp >= :from'; $params[':from'] = $from; }
        $to = query_param('to');
        if ($to) { $where[] = 'se.event_timestamp <= :to'; $params[':to'] = $to; }

        $stats = Database::fetchAll(
            "SELECT se.simulator, se.event_type, COUNT(*) as count
             FROM simulator_events se
             WHERE " . implode(' AND ', $where) . "
             GROUP BY se.simulator, se.event_type
             ORDER BY count DESC",
            $params
        );

        json_response(['simulators' => $stats]);
        break;

    // ─── ENCOUNTERS ─────────────────────────────────
    case $method === 'GET' && $action === 'encounters':
        $auth = require_auth(['admin', 'docente', 'instructor']);

        $where = ['1=1'];
        $params = [];

        $caseId = query_param('caseId');
        if ($caseId) { $where[] = 'pes.case_id = :cid'; $params[':cid'] = $caseId; }

        $from = query_param('from');
        if ($from) { $where[] = 'pes.started_at >= :from'; $params[':from'] = $from; }
        $to = query_param('to');
        if ($to) { $where[] = 'pes.started_at <= :to'; $params[':to'] = $to; }

        if ($auth['role'] !== 'admin') {
            $where[] = "EXISTS (
                SELECT 1 FROM group_members gm1 JOIN group_members gm2 ON gm1.group_id = gm2.group_id
                WHERE gm1.user_id = :uid AND gm2.user_id = pes.user_id
            )";
            $params[':uid'] = $auth['sub'];
        }

        $sql = "SELECT pes.*, u.username, u.full_name, c.title as case_title
                FROM patient_encounter_stats pes
                LEFT JOIN users u ON pes.user_id = u.id
                LEFT JOIN cases c ON pes.case_id = c.id
                WHERE " . implode(' AND ', $where) . "
                ORDER BY pes.started_at DESC";

        $page = query_int('page', 1);
        $limit = query_int('limit', DEFAULT_PAGE_SIZE);
        json_response(Database::paginate($sql, $params, $page, $limit));
        break;

    // ─── EXPORT CSV (admin) ─────────────────────────
    case $method === 'GET' && $action === 'export':
        $auth = require_auth('admin');

        $format = query_param('format', 'csv');
        $from = query_param('from');
        $to = query_param('to');

        $where = ['1=1'];
        $params = [];
        if ($from) { $where[] = 'pes.started_at >= :from'; $params[':from'] = $from; }
        if ($to) { $where[] = 'pes.started_at <= :to'; $params[':to'] = $to; }

        $data = Database::fetchAll(
            "SELECT pes.id as encounter_id,
                    pes.user_id,
                    pes.case_id,
                    pes.total_duration_secs,
                    pes.anamnesis_duration_secs,
                    pes.audiometry_duration_secs,
                    pes.logoaudiometry_duration_secs,
                    pes.impedance_duration_secs,
                    pes.oae_duration_secs,
                    pes.abr_duration_secs,
                    pes.oct_duration_secs,
                    pes.perimetry_duration_secs,
                    pes.modules_completed,
                    pes.modules_visited,
                    pes.total_edits,
                    pes.audio_thresholds_recorded,
                    pes.audio_frequency_changes,
                    pes.audio_intensity_changes,
                    pes.audio_masking_used,
                    pes.vf_test_completed,
                    pes.vf_test_duration_secs,
                    pes.oct_views_consulted,
                    pes.started_at,
                    pes.completed_at
             FROM patient_encounter_stats pes
             WHERE " . implode(' AND ', $where) . "
             ORDER BY pes.started_at",
            $params
        );

        if ($format === 'json') {
            json_response(['data' => $data, 'count' => count($data)]);
            break;
        }

        // CSV export
        header('Content-Type: text/csv; charset=utf-8');
        header('Content-Disposition: attachment; filename="labsim_encounters_' . date('Y-m-d') . '.csv"');

        $output = fopen('php://output', 'w');
        if (!empty($data)) {
            fputcsv($output, array_keys($data[0]));
            foreach ($data as $row) {
                fputcsv($output, $row);
            }
        }
        fclose($output);
        exit;

    // ─── STATS DEL CENTRO ───────────────────────────
    case $method === 'GET' && $action === 'center':
        $auth = require_auth(['admin', 'docente', 'instructor']);
        $sessionId = query_param('sessionId');

        $stats = [];

        // Incidentes
        $incidentWhere = $sessionId ? "WHERE ci.session_id = :sid" : "WHERE 1=1";
        $incidentParams = $sessionId ? [':sid' => $sessionId] : [];

        $stats['incidents'] = [
            'total' => Database::fetchOne("SELECT COUNT(*) as c FROM center_incidents $incidentWhere", $incidentParams)['c'],
            'bySeverity' => Database::fetchAll("SELECT severity, COUNT(*) as count FROM center_incidents $incidentWhere GROUP BY severity", $incidentParams),
            'byCategory' => Database::fetchAll("SELECT category, COUNT(*) as count FROM center_incidents $incidentWhere GROUP BY category ORDER BY count DESC", $incidentParams),
            'byStatus' => Database::fetchAll("SELECT status, COUNT(*) as count FROM center_incidents $incidentWhere GROUP BY status", $incidentParams),
        ];

        // Reuniones
        $meetingWhere = $sessionId ? "WHERE cm.session_id = :sid" : "WHERE 1=1";
        $meetingParams = $sessionId ? [':sid' => $sessionId] : [];
        $stats['meetings'] = [
            'total' => Database::fetchOne("SELECT COUNT(*) as c FROM clinical_meetings cm $meetingWhere", $meetingParams)['c'],
            'completed' => Database::fetchOne("SELECT COUNT(*) as c FROM clinical_meetings cm $meetingWhere AND cm.status = 'completed'", $meetingParams)['c'],
        ];

        // Planes de mejora
        $planWhere = $sessionId ? "WHERE ip.session_id = :sid" : "WHERE 1=1";
        $planParams = $sessionId ? [':sid' => $sessionId] : [];
        $stats['plans'] = [
            'total' => Database::fetchOne("SELECT COUNT(*) as c FROM improvement_plans ip $planWhere", $planParams)['c'],
            'byStatus' => Database::fetchAll("SELECT status, COUNT(*) as count FROM improvement_plans ip $planWhere GROUP BY status", $planParams),
            'tasksCompleted' => Database::fetchOne("SELECT COUNT(*) as c FROM improvement_tasks WHERE is_completed = 1")['c'],
            'tasksTotal' => Database::fetchOne("SELECT COUNT(*) as c FROM improvement_tasks")['c'],
        ];

        // Validaciones
        $stats['validations'] = [
            'total' => Database::fetchOne("SELECT COUNT(*) as c FROM validation_requests")['c'],
            'pending' => Database::fetchOne("SELECT COUNT(*) as c FROM validation_requests WHERE status = 'pending'")['c'],
            'approved' => Database::fetchOne("SELECT COUNT(*) as c FROM validation_requests WHERE status = 'approved'")['c'],
            'returned' => Database::fetchOne("SELECT COUNT(*) as c FROM validation_requests WHERE status = 'returned'")['c'],
        ];

        // Feedback pacientes
        $stats['feedback'] = [
            'complaints' => Database::fetchOne("SELECT COUNT(*) as c FROM patient_feedback WHERE feedback_type = 'complaint'")['c'],
            'compliments' => Database::fetchOne("SELECT COUNT(*) as c FROM patient_feedback WHERE feedback_type = 'compliment'")['c'],
            'byReason' => Database::fetchAll("SELECT reason, feedback_type, COUNT(*) as count FROM patient_feedback GROUP BY reason, feedback_type ORDER BY count DESC"),
        ];

        json_response($stats);
        break;

    default:
        error_response("Ruta no encontrada: stats/" . implode('/', $routeSegments), 404);
}
