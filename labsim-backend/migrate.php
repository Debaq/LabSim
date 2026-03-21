<?php
/**
 * LabSim Backend - Script de migración
 * Actualiza una BD existente agregando columnas y tablas nuevas
 * sin perder datos.
 *
 * Seguro de ejecutar múltiples veces (idempotente).
 */

$isCli = php_sapi_name() === 'cli';

function out($msg, $isCli) {
    echo $isCli ? "$msg\n" : "<p>$msg</p>";
}

if (!$isCli) {
    echo '<!DOCTYPE html><html><head><title>LabSim Migrate</title>
    <style>body{font-family:monospace;max-width:700px;margin:40px auto;padding:20px;background:#1a1a2e;color:#e0e0e0}
    p{margin:4px 0}.ok{color:#4ade80}.err{color:#f87171}.warn{color:#fbbf24}.skip{color:#666}h1{color:#818cf8}</style></head><body>';
    echo '<h1>LabSim Backend - Migración</h1>';
}

require_once __DIR__ . '/core/config.php';
require_once __DIR__ . '/core/db.php';

if (!file_exists(DB_PATH)) {
    out($isCli ? "✗ No se encontró BD en " . DB_PATH . ". Ejecuta install.php primero." : "<span class='err'>✗ No se encontró BD. Ejecuta install.php primero.</span>", $isCli);
    exit(1);
}

$db = Database::get();
out($isCli ? "✓ BD encontrada: " . DB_PATH : "<span class='ok'>✓ BD encontrada</span>", $isCli);

/**
 * Helper: verifica si una columna existe en una tabla
 */
function column_exists($db, $table, $column) {
    $cols = $db->query("PRAGMA table_info($table)")->fetchAll(PDO::FETCH_ASSOC);
    foreach ($cols as $col) {
        if ($col['name'] === $column) return true;
    }
    return false;
}

/**
 * Helper: verifica si una tabla existe
 */
function table_exists($db, $table) {
    $r = $db->query("SELECT name FROM sqlite_master WHERE type='table' AND name='$table'")->fetch();
    return (bool)$r;
}

/**
 * Helper: agrega columna si no existe
 */
function add_column($db, $table, $column, $definition, $isCli) {
    if (!table_exists($db, $table)) {
        out($isCli ? "  ⚠ Tabla '$table' no existe, se omite" : "<span class='warn'>  ⚠ Tabla '$table' no existe</span>", $isCli);
        return;
    }
    if (column_exists($db, $table, $column)) {
        out($isCli ? "  · $table.$column ya existe" : "<span class='skip'>  · $table.$column ya existe</span>", $isCli);
        return;
    }
    $db->exec("ALTER TABLE $table ADD COLUMN $column $definition");
    out($isCli ? "  ✓ $table.$column agregada" : "<span class='ok'>  ✓ $table.$column agregada</span>", $isCli);
}

/**
 * Helper: crea tabla si no existe
 */
function create_table($db, $name, $sql, $isCli) {
    if (table_exists($db, $name)) {
        out($isCli ? "  · $name ya existe" : "<span class='skip'>  · $name ya existe</span>", $isCli);
        return;
    }
    $db->exec($sql);
    out($isCli ? "  ✓ $name creada" : "<span class='ok'>  ✓ $name creada</span>", $isCli);
}

/**
 * Helper: crea índice si no existe
 */
function create_index($db, $sql, $isCli) {
    try {
        $db->exec($sql);
    } catch (Exception $e) {
        // ya existe
    }
}

// ═══════════════════════════════════════════════════════
// MIGRACIONES
// ═══════════════════════════════════════════════════════

out($isCli ? "\n— Columnas nuevas en tablas existentes..." : "<br><strong>Columnas nuevas...</strong>", $isCli);

// users
add_column($db, 'users', 'must_change_password', "INTEGER NOT NULL DEFAULT 0", $isCli);

// agenda_items
add_column($db, 'agenda_items', 'assigned_to', "TEXT REFERENCES users(id)", $isCli);
add_column($db, 'agenda_items', 'session_id', "TEXT REFERENCES practice_sessions(id)", $isCli);
add_column($db, 'agenda_items', 'patient_age', "INTEGER", $isCli);
add_column($db, 'agenda_items', 'patient_gender', "TEXT", $isCli);
add_column($db, 'agenda_items', 'patient_notes', "TEXT", $isCli);
add_column($db, 'agenda_items', 'procedure_id', "TEXT REFERENCES procedures(id)", $isCli);
add_column($db, 'agenda_items', 'status', "TEXT DEFAULT 'scheduled'", $isCli);
add_column($db, 'agenda_items', 'rescheduled_from', "TEXT REFERENCES agenda_items(id)", $isCli);
add_column($db, 'agenda_items', 'rescheduled_date', "TEXT", $isCli);
add_column($db, 'agenda_items', 'rescheduled_time', "TEXT", $isCli);
add_column($db, 'agenda_items', 'completion_notes', "TEXT", $isCli);

// ─── Tablas nuevas ──────────────────────────────────
out($isCli ? "\n— Tablas nuevas..." : "<br><strong>Tablas nuevas...</strong>", $isCli);

create_table($db, 'procedures', "CREATE TABLE IF NOT EXISTS procedures (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    code TEXT UNIQUE,
    category TEXT NOT NULL DEFAULT 'audiologia'
        CHECK (category IN ('audiologia','oftalmologia','vestibular','electrodiagnostico','otro')),
    default_duration_minutes INTEGER NOT NULL DEFAULT 30,
    description TEXT,
    requires_equipment TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

create_table($db, 'boxes', "CREATE TABLE IF NOT EXISTS boxes (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES practice_sessions(id),
    box_number INTEGER NOT NULL,
    name TEXT,
    student_id TEXT REFERENCES users(id),
    equipment_list TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE (session_id, box_number)
)", $isCli);

create_table($db, 'center_incidents', "CREATE TABLE IF NOT EXISTS center_incidents (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    created_by TEXT NOT NULL,
    category TEXT NOT NULL CHECK (category IN (
        'accesibilidad','equipamiento','infraestructura','paciente',
        'administrativo','bioseguridad','emergencia','otro'
    )),
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    affected_box INTEGER,
    severity TEXT DEFAULT 'moderate' CHECK (severity IN ('low','moderate','high','critical')),
    status TEXT DEFAULT 'active' CHECK (status IN ('active','discussed','resolved','dismissed')),
    resolution_notes TEXT,
    resolved_by TEXT REFERENCES users(id),
    trigger_time_minutes INTEGER,
    is_template INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

create_table($db, 'clinical_meetings', "CREATE TABLE IF NOT EXISTS clinical_meetings (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES practice_sessions(id),
    called_by TEXT NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    agenda_text TEXT,
    status TEXT DEFAULT 'scheduled' CHECK (status IN ('scheduled','in_progress','completed','cancelled')),
    scheduled_at TEXT,
    started_at TEXT,
    ended_at TEXT,
    minutes_text TEXT,
    decisions_text TEXT,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

create_table($db, 'meeting_participants', "CREATE TABLE IF NOT EXISTS meeting_participants (
    meeting_id TEXT NOT NULL REFERENCES clinical_meetings(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    attended INTEGER DEFAULT 0,
    notes TEXT,
    PRIMARY KEY (meeting_id, user_id)
)", $isCli);

create_table($db, 'meeting_incidents', "CREATE TABLE IF NOT EXISTS meeting_incidents (
    meeting_id TEXT NOT NULL REFERENCES clinical_meetings(id),
    incident_id TEXT NOT NULL REFERENCES center_incidents(id),
    PRIMARY KEY (meeting_id, incident_id)
)", $isCli);

create_table($db, 'chat_messages', "CREATE TABLE IF NOT EXISTS chat_messages (
    id TEXT PRIMARY KEY,
    sender_id TEXT NOT NULL REFERENCES users(id),
    recipient_id TEXT REFERENCES users(id),
    group_id TEXT,
    session_id TEXT REFERENCES practice_sessions(id),
    message TEXT NOT NULL,
    message_type TEXT DEFAULT 'text' CHECK (message_type IN ('text','system','incident','meeting_call')),
    is_read INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

create_table($db, 'karime_directives', "CREATE TABLE IF NOT EXISTS karime_directives (
    id TEXT PRIMARY KEY,
    scope TEXT NOT NULL CHECK (scope IN ('global','docente','instructor','session')),
    author_id TEXT NOT NULL REFERENCES users(id),
    target_session_id TEXT REFERENCES practice_sessions(id),
    title TEXT NOT NULL,
    student_treatment TEXT DEFAULT 'formal',
    tone TEXT DEFAULT 'profesional'
        CHECK (tone IN ('profesional','amigable','estricto','relajado')),
    pressure_level INTEGER DEFAULT 2 CHECK (pressure_level BETWEEN 1 AND 5),
    custom_messages_json TEXT DEFAULT '{}',
    rules_text TEXT,
    is_locked INTEGER DEFAULT 0,
    approved_by TEXT REFERENCES users(id),
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
)", $isCli);

create_table($db, 'patient_feedback', "CREATE TABLE IF NOT EXISTS patient_feedback (
    id TEXT PRIMARY KEY,
    agenda_item_id TEXT NOT NULL REFERENCES agenda_items(id),
    student_id TEXT NOT NULL REFERENCES users(id),
    feedback_type TEXT NOT NULL CHECK (feedback_type IN ('complaint','compliment')),
    reason TEXT NOT NULL CHECK (reason IN (
        'late_start','overtime','rescheduled','poor_attention','misdiagnosis',
        'fast_service','good_attention','accurate_diagnosis','patient_comfort','other'
    )),
    message TEXT NOT NULL,
    patient_name TEXT,
    severity INTEGER DEFAULT 1 CHECK (severity BETWEEN 1 AND 3),
    is_read_by_docente INTEGER DEFAULT 0,
    is_read_by_instructor INTEGER DEFAULT 0,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

create_table($db, 'time_alerts', "CREATE TABLE IF NOT EXISTS time_alerts (
    id TEXT PRIMARY KEY,
    agenda_item_id TEXT NOT NULL REFERENCES agenda_items(id),
    student_id TEXT NOT NULL REFERENCES users(id),
    alert_type TEXT NOT NULL CHECK (alert_type IN ('warning','urgent','critical')),
    minutes_over INTEGER NOT NULL,
    message TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

create_table($db, 'refresh_tokens', "CREATE TABLE IF NOT EXISTS refresh_tokens (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    token_hash TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

create_table($db, 'login_attempts', "CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip_address TEXT NOT NULL,
    attempted_at TEXT DEFAULT (datetime('now'))
)", $isCli);

// Tablas de telemetría (por si no existen)
create_table($db, 'app_sessions', "CREATE TABLE IF NOT EXISTS app_sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL REFERENCES users(id),
    device_id TEXT,
    started_at TEXT,
    ended_at TEXT,
    duration_seconds INTEGER,
    case_id TEXT,
    practice_session_id TEXT,
    app_version TEXT,
    os TEXT,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

create_table($db, 'simulator_events', "CREATE TABLE IF NOT EXISTS simulator_events (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES app_sessions(id),
    user_id TEXT NOT NULL,
    simulator TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_data TEXT DEFAULT '{}',
    event_timestamp TEXT NOT NULL
)", $isCli);

create_table($db, 'patient_encounter_stats', "CREATE TABLE IF NOT EXISTS patient_encounter_stats (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    user_id TEXT NOT NULL,
    case_id TEXT,
    practice_session_id TEXT,
    total_duration_secs INTEGER,
    anamnesis_duration_secs INTEGER,
    audiometry_duration_secs INTEGER,
    logoaudiometry_duration_secs INTEGER,
    impedance_duration_secs INTEGER,
    oae_duration_secs INTEGER,
    abr_duration_secs INTEGER,
    oct_duration_secs INTEGER,
    perimetry_duration_secs INTEGER,
    report_duration_secs INTEGER,
    modules_completed INTEGER DEFAULT 0,
    modules_visited INTEGER DEFAULT 0,
    total_edits INTEGER DEFAULT 0,
    audio_thresholds_recorded INTEGER DEFAULT 0,
    audio_frequency_changes INTEGER DEFAULT 0,
    audio_intensity_changes INTEGER DEFAULT 0,
    audio_masking_used INTEGER DEFAULT 0,
    vf_test_completed INTEGER DEFAULT 0,
    vf_test_duration_secs INTEGER,
    vf_fixation_loss_pct REAL,
    vf_false_pos_pct REAL,
    vf_false_neg_pct REAL,
    oct_views_consulted INTEGER DEFAULT 0,
    oct_time_on_bscan_secs INTEGER,
    oct_time_on_rnfl_secs INTEGER,
    started_at TEXT,
    completed_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

create_table($db, 'module_interaction_stats', "CREATE TABLE IF NOT EXISTS module_interaction_stats (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    user_id TEXT NOT NULL,
    module_id TEXT NOT NULL,
    time_spent_secs INTEGER,
    fields_filled INTEGER,
    fields_total INTEGER,
    edits_count INTEGER,
    first_opened_at TEXT,
    last_saved_at TEXT
)", $isCli);

// ─── Índices ────────────────────────────────────────
out($isCli ? "\n— Índices..." : "<br><strong>Índices...</strong>", $isCli);

$indices = [
    "CREATE INDEX IF NOT EXISTS idx_sim_events_session ON simulator_events(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_sim_events_user ON simulator_events(user_id, simulator)",
    "CREATE INDEX IF NOT EXISTS idx_encounter_user ON patient_encounter_stats(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_encounter_case ON patient_encounter_stats(case_id)",
    "CREATE INDEX IF NOT EXISTS idx_refresh_tokens_user ON refresh_tokens(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip_address)",
    "CREATE INDEX IF NOT EXISTS idx_cases_author ON cases(author_id)",
    "CREATE INDEX IF NOT EXISTS idx_submissions_student ON submissions(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_submissions_session ON submissions(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_agenda_date ON agenda_items(scheduled_date)",
    "CREATE INDEX IF NOT EXISTS idx_agenda_assigned ON agenda_items(assigned_to)",
    "CREATE INDEX IF NOT EXISTS idx_agenda_procedure ON agenda_items(procedure_id)",
    "CREATE INDEX IF NOT EXISTS idx_app_sessions_user ON app_sessions(user_id)",
];

foreach ($indices as $sql) {
    create_index($db, $sql, $isCli);
}
out($isCli ? "  ✓ Índices verificados" : "<span class='ok'>  ✓ Índices verificados</span>", $isCli);

// ─── Seed: procedimientos ───────────────────────────
$procCount = $db->query("SELECT COUNT(*) as c FROM procedures")->fetch()['c'] ?? 0;
if ($procCount == 0) {
    out($isCli ? "\n— Insertando procedimientos..." : "<br><strong>Insertando procedimientos...</strong>", $isCli);
    require __DIR__ . '/install.php';
    // install.php ya maneja el seed de procedimientos e incidentes
} else {
    out($isCli ? "\n· Procedimientos ya existen ($procCount)" : "<span class='skip'>· Procedimientos ya existen ($procCount)</span>", $isCli);
}

// ─── Resumen ────────────────────────────────────────
out("", $isCli);
out($isCli ? "═══════════════════════════════════════" : "<hr>", $isCli);
out($isCli ? "✓ Migración completada" : "<span class='ok'><strong>✓ Migración completada</strong></span>", $isCli);

if (!$isCli) echo '</body></html>';
