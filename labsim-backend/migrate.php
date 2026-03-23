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
add_column($db, 'users', 'is_demo', "INTEGER NOT NULL DEFAULT 0", $isCli);

// cases
add_column($db, 'cases', 'is_archived', "INTEGER NOT NULL DEFAULT 0", $isCli);
add_column($db, 'cases', 'is_locked', "INTEGER NOT NULL DEFAULT 0", $isCli);

// practice_sessions: tipo de sesión y vínculo a curso
add_column($db, 'practice_sessions', 'session_type', "TEXT DEFAULT 'conjunto'", $isCli);
add_column($db, 'practice_sessions', 'course_id', "TEXT REFERENCES courses(id)", $isCli);
add_column($db, 'practice_sessions', 'centro_enabled', "INTEGER DEFAULT 0", $isCli);
add_column($db, 'practice_sessions', 'end_date', "TEXT", $isCli);

// users: institución y número de identificación
add_column($db, 'users', 'institution_id', "TEXT REFERENCES institutions(id)", $isCli);
add_column($db, 'users', 'student_id_number', "TEXT", $isCli);

// agenda_items: vinculación a cursos + configuración de sesión
add_column($db, 'agenda_items', 'course_id', "TEXT REFERENCES courses(id)", $isCli);
add_column($db, 'agenda_items', 'session_config_json', "TEXT DEFAULT '{}'", $isCli);

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

// Instituciones
create_table($db, 'institutions', "CREATE TABLE IF NOT EXISTS institutions (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    config_json TEXT DEFAULT '{}',
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

// Cursos
create_table($db, 'courses', "CREATE TABLE IF NOT EXISTS courses (
    id TEXT PRIMARY KEY,
    institution_id TEXT NOT NULL REFERENCES institutions(id),
    name TEXT NOT NULL,
    code TEXT,
    description TEXT,
    created_by TEXT NOT NULL REFERENCES users(id),
    period TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

// Miembros de cursos
create_table($db, 'course_members', "CREATE TABLE IF NOT EXISTS course_members (
    course_id TEXT NOT NULL REFERENCES courses(id),
    user_id TEXT NOT NULL REFERENCES users(id),
    role TEXT DEFAULT 'estudiante' CHECK (role IN ('estudiante','instructor','docente')),
    enrolled_at TEXT DEFAULT (datetime('now')),
    PRIMARY KEY (course_id, user_id)
)", $isCli);

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

// ─── Larissa: Evoluciones clínicas ──────────────────
create_table($db, 'evolutions', "CREATE TABLE IF NOT EXISTS evolutions (
    id TEXT PRIMARY KEY,
    agenda_item_id TEXT NOT NULL REFERENCES agenda_items(id),
    student_id TEXT NOT NULL REFERENCES users(id),
    motivo_consulta TEXT,
    anamnesis_proxima TEXT,
    examen_fisico TEXT,
    hipotesis_diagnostica TEXT,
    plan_estudio TEXT,
    plan_terapeutico TEXT,
    observaciones TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
)", $isCli);

// ─── Larissa: Interconsultas ────────────────────────
create_table($db, 'interconsultations', "CREATE TABLE IF NOT EXISTS interconsultations (
    id TEXT PRIMARY KEY,
    agenda_item_id TEXT NOT NULL REFERENCES agenda_items(id),
    requester_id TEXT NOT NULL REFERENCES users(id),
    target_specialty TEXT NOT NULL,
    reason TEXT NOT NULL,
    priority TEXT DEFAULT 'normal' CHECK (priority IN ('normal','urgente')),
    response_text TEXT,
    responder_id TEXT REFERENCES users(id),
    status TEXT DEFAULT 'solicitada' CHECK (status IN ('solicitada','respondida','completada')),
    created_at TEXT DEFAULT (datetime('now')),
    responded_at TEXT
)", $isCli);

// ─── Centro: Planes de mejora ────────────────────────
create_table($db, 'improvement_plans', "CREATE TABLE IF NOT EXISTS improvement_plans (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL REFERENCES practice_sessions(id),
    meeting_id TEXT REFERENCES clinical_meetings(id),
    created_by TEXT NOT NULL REFERENCES users(id),
    title TEXT NOT NULL,
    description TEXT,
    status TEXT DEFAULT 'pendiente' CHECK (status IN ('pendiente','en_progreso','completado','cancelado')),
    deadline TEXT,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
)", $isCli);

create_table($db, 'improvement_tasks', "CREATE TABLE IF NOT EXISTS improvement_tasks (
    id TEXT PRIMARY KEY,
    plan_id TEXT NOT NULL REFERENCES improvement_plans(id) ON DELETE CASCADE,
    assigned_to TEXT REFERENCES users(id),
    title TEXT NOT NULL,
    description TEXT,
    is_completed INTEGER DEFAULT 0,
    completed_at TEXT,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

// ─── Supervisión: Validaciones docente ──────────────
create_table($db, 'validation_requests', "CREATE TABLE IF NOT EXISTS validation_requests (
    id TEXT PRIMARY KEY,
    agenda_item_id TEXT NOT NULL REFERENCES agenda_items(id),
    student_id TEXT NOT NULL REFERENCES users(id),
    procedure_name TEXT,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending','approved','returned')),
    docente_id TEXT REFERENCES users(id),
    docente_notes TEXT,
    requested_at TEXT DEFAULT (datetime('now')),
    resolved_at TEXT
)", $isCli);

// ─── Pacientes vivos: memoria de interacciones ──────
create_table($db, 'patient_interaction_logs', "CREATE TABLE IF NOT EXISTS patient_interaction_logs (
    id TEXT PRIMARY KEY,
    case_id TEXT NOT NULL REFERENCES cases(id),
    agenda_item_id TEXT REFERENCES agenda_items(id),
    student_id TEXT NOT NULL REFERENCES users(id),
    student_name TEXT,
    summary TEXT NOT NULL,
    mood_at_end TEXT,
    tests_performed TEXT DEFAULT '[]',
    duration_minutes INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

// ─── Base de Conocimiento ─────────────────────────────
create_table($db, 'kb_categories', "CREATE TABLE IF NOT EXISTS kb_categories (
    id TEXT PRIMARY KEY,
    label TEXT NOT NULL,
    icon TEXT DEFAULT 'help-circle',
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now'))
)", $isCli);

create_table($db, 'kb_articles', "CREATE TABLE IF NOT EXISTS kb_articles (
    id TEXT PRIMARY KEY,
    category_id TEXT NOT NULL REFERENCES kb_categories(id),
    title TEXT NOT NULL,
    content TEXT NOT NULL,
    author_id TEXT REFERENCES users(id),
    sort_order INTEGER DEFAULT 0,
    is_active INTEGER DEFAULT 1,
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
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
    "CREATE INDEX IF NOT EXISTS idx_evolutions_agenda ON evolutions(agenda_item_id)",
    "CREATE INDEX IF NOT EXISTS idx_evolutions_student ON evolutions(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_interconsultations_agenda ON interconsultations(agenda_item_id)",
    "CREATE INDEX IF NOT EXISTS idx_interconsultations_requester ON interconsultations(requester_id)",
    "CREATE INDEX IF NOT EXISTS idx_agenda_course ON agenda_items(course_id)",
    "CREATE INDEX IF NOT EXISTS idx_improvement_plans_session ON improvement_plans(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_improvement_tasks_plan ON improvement_tasks(plan_id)",
    "CREATE INDEX IF NOT EXISTS idx_validation_requests_student ON validation_requests(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_validation_requests_status ON validation_requests(status)",
    "CREATE INDEX IF NOT EXISTS idx_patient_logs_case ON patient_interaction_logs(case_id)",
    "CREATE INDEX IF NOT EXISTS idx_patient_logs_student ON patient_interaction_logs(student_id)",
    "CREATE INDEX IF NOT EXISTS idx_courses_institution ON courses(institution_id)",
    "CREATE INDEX IF NOT EXISTS idx_courses_creator ON courses(created_by)",
    "CREATE INDEX IF NOT EXISTS idx_course_members_user ON course_members(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_users_institution ON users(institution_id)",
    "CREATE INDEX IF NOT EXISTS idx_users_student_id ON users(student_id_number)",
    "CREATE INDEX IF NOT EXISTS idx_kb_articles_category ON kb_articles(category_id)",
    "CREATE INDEX IF NOT EXISTS idx_kb_articles_active ON kb_articles(is_active)",
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

// ─── Seed: institución por defecto ──────────────────
$instCount = 0;
if (table_exists($db, 'institutions')) {
    $instCount = $db->query("SELECT COUNT(*) as c FROM institutions")->fetch()['c'] ?? 0;
}
if ($instCount == 0 && table_exists($db, 'institutions')) {
    out($isCli ? "\n— Creando institución por defecto..." : "<br><strong>Institución por defecto...</strong>", $isCli);
    $defaultInstId = Database::uuid();
    Database::execute(
        "INSERT INTO institutions (id, name, slug) VALUES (:id, :name, :slug)",
        [':id' => $defaultInstId, ':name' => 'LabSim Dev', ':slug' => 'labsim']
    );
    out($isCli ? "  ✓ Institución 'LabSim Dev' creada" : "<span class='ok'>  ✓ Institución 'LabSim Dev' creada</span>", $isCli);

    // Asignar todos los usuarios existentes a la institución por defecto
    $orphans = Database::execute(
        "UPDATE users SET institution_id = :iid WHERE institution_id IS NULL",
        [':iid' => $defaultInstId]
    );
    if ($orphans > 0) {
        out($isCli ? "  ✓ $orphans usuarios asignados a institución por defecto" : "<span class='ok'>  ✓ $orphans usuarios migrados</span>", $isCli);
    }
} else {
    out($isCli ? "\n· Institución ya existe" : "<span class='skip'>· Institución ya existe</span>", $isCli);
}

// ─── Usuario demo ────────────────────────────────────
$demoUser = $db->query("SELECT id FROM users WHERE username = 'demo'")->fetch();
if (!$demoUser) {
    out($isCli ? "\n— Creando usuario demo..." : "<br><strong>Usuario demo...</strong>", $isCli);
    $demoId = Database::uuid();
    Database::execute(
        "INSERT INTO users (id, username, email, password_hash, role, full_name, institution, is_active, is_demo)
         VALUES (:id, 'demo', 'demo@labsim.local', :hash, 'docente', 'Usuario Demo', 'LabSim Demo', 1, 1)",
        [
            ':id' => $demoId,
            ':hash' => password_hash('test', PASSWORD_BCRYPT),
        ]
    );
    // Asignar institución por defecto si existe
    $defaultInst = $db->query("SELECT id FROM institutions LIMIT 1")->fetch();
    if ($defaultInst) {
        Database::execute(
            "UPDATE users SET institution_id = :iid WHERE id = :uid",
            [':iid' => $defaultInst['id'], ':uid' => $demoId]
        );
    }
    out($isCli ? "  ✓ Usuario demo creado (demo / test)" : "<span class='ok'>  ✓ Usuario demo creado (demo / test)</span>", $isCli);
} else {
    // Asegurar que is_demo=1 y contraseña actualizada
    Database::execute(
        "UPDATE users SET is_demo = 1, password_hash = :hash, is_active = 1 WHERE username = 'demo'",
        [':hash' => password_hash('test', PASSWORD_BCRYPT)]
    );
    out($isCli ? "\n· Usuario demo ya existe (actualizado)" : "<span class='skip'>· Usuario demo ya existe (actualizado)</span>", $isCli);
}

// ─── Seed: Base de Conocimiento ────────────────────────
if (table_exists($db, 'kb_categories')) {
    $kbCount = $db->query("SELECT COUNT(*) as c FROM kb_categories")->fetch()['c'] ?? 0;
    if ($kbCount == 0) {
        out($isCli ? "\n— Insertando base de conocimiento..." : "<br><strong>Base de conocimiento...</strong>", $isCli);

        $kbCategories = [
            ['id' => 'app',              'label' => 'Usar LabSim',            'icon' => 'monitor',     'sort' => 1],
            ['id' => 'audiometria',      'label' => 'Audiometría',            'icon' => 'headphones',  'sort' => 2],
            ['id' => 'impedanciometria', 'label' => 'Impedanciometría',       'icon' => 'activity',    'sort' => 3],
            ['id' => 'oftalmologia',     'label' => 'Oftalmología',           'icon' => 'eye',         'sort' => 4],
            ['id' => 'otoneurologia',    'label' => 'Otoneurología',          'icon' => 'brain',       'sort' => 5],
            ['id' => 'clinica',          'label' => 'Flujo clínico',          'icon' => 'clipboard',   'sort' => 6],
            ['id' => 'equipos',          'label' => 'Equipamiento',           'icon' => 'settings',    'sort' => 7],
            ['id' => 'rehabilitacion',   'label' => 'Rehabilitación auditiva','icon' => 'ear',         'sort' => 8],
        ];

        foreach ($kbCategories as $cat) {
            Database::execute(
                "INSERT INTO kb_categories (id, label, icon, sort_order) VALUES (:id, :label, :icon, :sort)",
                [':id' => $cat['id'], ':label' => $cat['label'], ':icon' => $cat['icon'], ':sort' => $cat['sort']]
            );
        }

        $kbArticles = [
            // ── Usar LabSim ──
            ['app', 'Primeros pasos', "LabSim simula un centro clínico completo. Desde el escritorio puedes abrir simuladores de equipos médicos, gestionar pacientes, agendar atenciones y comunicarte con la secretaria Karime.\n\nHaz doble click en los iconos del escritorio para abrir cada aplicación. También puedes usar el menú Inicio (botón LabSim en la barra de tareas)."],
            ['app', 'Ventanas y escritorio', "Las ventanas se pueden mover arrastrando la barra de título, redimensionar desde los bordes, minimizar y maximizar.\n\nLa barra de tareas inferior muestra las ventanas abiertas. Click para enfocar o minimizar.\n\nClick derecho en el escritorio abre un menú con opciones rápidas."],
            ['app', 'Inteligencia Artificial', "LabSim incluye IA local (no requiere internet). Desde Configuración > Inteligencia Artificial puedes descargar un modelo LLM (Qwen) que permite que Karime y los pacientes respondan de forma inteligente.\n\nTambién puedes activar reconocimiento de voz (Whisper) y síntesis de voz (Piper) desde la misma sección."],
            ['app', 'Personalización', "Click derecho > Personalizar escritorio, o Configuración > Apariencia.\n\nTres temas: Midnight (oscuro), Clínico (claro) y Nord. Puedes cambiar tamaño de fuente y color de fondo."],
            ['app', 'Mensajes y Karime', "El sistema de mensajes permite comunicarte con Karime (secretaria del centro). Ella gestiona la agenda, avisa sobre pacientes y te notifica atrasos.\n\nSi la IA está activada, Karime responde de forma inteligente según su personalidad. Sin IA, usa respuestas predeterminadas."],
            ['app', 'Mis Documentos', "Mis Documentos organiza los archivos de tu práctica clínica en carpetas: Exámenes (por tipo), Informes, Evoluciones, Interconsultas y Notas.\n\nPuedes navegar con doble click en carpetas y usar los botones de atrás e inicio."],
            ['app', 'Conexión al servidor', "El indicador Wi-Fi en la barra de tareas muestra el estado de conexión:\n• Verde: conectado al servidor\n• Amarillo: verificando\n• Rojo: sin conexión\n\nClick en el icono para forzar una verificación. Puedes trabajar offline y sincronizar después."],

            // ── Audiometría ──
            ['audiometria', '¿Qué es una audiometría?', "La audiometría tonal liminar evalúa los umbrales auditivos por vía aérea (VA) y vía ósea (VO) en frecuencias de 250 Hz a 8000 Hz.\n\nPermite determinar el tipo de hipoacusia (conductiva, sensorioneural o mixta), el grado de pérdida y la configuración audiométrica."],
            ['audiometria', 'Procedimiento paso a paso', "1. Otoscopía previa para descartar obstrucciones\n2. Instrucciones al paciente\n3. Colocar auriculares (rojo = oído derecho, azul = izquierdo)\n4. Comenzar por el mejor oído a 1000 Hz\n5. Descender de 10 en 10 dB, ascender de 5 en 5 dB\n6. El umbral es el nivel más bajo donde responde 2 de 3 veces\n7. Evaluar: 1000, 2000, 4000, 8000, 500, 250 Hz\n8. Repetir vía ósea si hay pérdida por vía aérea"],
            ['audiometria', 'Enmascaramiento', "Se requiere enmascaramiento cuando existe riesgo de audición cruzada.\n\nVía aérea: enmascarar cuando la diferencia entre VA del oído evaluado y VO del no evaluado es ≥ 40 dB (auriculares supraurales) o ≥ 55 dB (insertos).\n\nVía ósea: enmascarar cuando existe GAP aéreo-óseo ≥ 10 dB en el oído evaluado.\n\nMétodo de plateau: aumentar el ruido en pasos de 5 dB hasta que el umbral se mantenga estable en al menos 3 niveles consecutivos."],
            ['audiometria', 'Interpretación del audiograma', "Tipos de hipoacusia:\n• Conductiva: VA descendida, VO normal, GAP > 10 dB\n• Sensorioneural: VA y VO descendidas sin GAP significativo\n• Mixta: VO descendida + GAP > 10 dB\n\nGrados (PTA 500-4000 Hz):\n• Normal: ≤ 20 dB HL\n• Leve: 21-40 dB\n• Moderada: 41-55 dB\n• Moderada-severa: 56-70 dB\n• Severa: 71-90 dB\n• Profunda: > 90 dB HL"],
            ['audiometria', 'Configuraciones audiométricas', "• Plana: umbrales similares en todas las frecuencias\n• Descendente: pérdida mayor en agudos (presbiacusia, trauma acústico)\n• Ascendente: pérdida mayor en graves (Ménière, hidrops)\n• En U: pérdida en medias con conservación de graves y agudos\n• Escotoma: pérdida aislada en una frecuencia (4000 Hz en trauma acústico)\n• Esquina: solo restos auditivos en graves (hipoacusia profunda)"],
            ['audiometria', 'Simbología audiométrica', "Oído derecho (rojo):\n• VA sin enmascarar: O\n• VA enmascarada: △\n• VO sin enmascarar: <\n• VO enmascarada: [\n\nOído izquierdo (azul):\n• VA sin enmascarar: X\n• VA enmascarada: □\n• VO sin enmascarar: >\n• VO enmascarada: ]\n\nSin respuesta: flecha hacia abajo en el símbolo correspondiente."],
            ['audiometria', 'Logoaudiometría', "Evalúa la capacidad de discriminación del habla.\n\nMediciones principales:\n• SRT (Speech Reception Threshold): nivel donde el paciente repite correctamente el 50% de las palabras. Debe coincidir ±10 dB con el PTA.\n• SDS (Speech Discrimination Score): porcentaje de palabras correctas a 30-40 dB sobre SRT.\n\nUn SDS bajo con buena audiometría sugiere patología retrococlear."],
            ['audiometria', 'Screening auditivo neonatal', "Todo recién nacido debe ser evaluado antes del mes de vida.\n\nMétodos:\n• OAE (Emisiones Otoacústicas): evalúan función de células ciliadas externas.\n• BERA automático (aABR): evalúa la vía auditiva hasta tronco encefálico.\n\nProtocolo: si falla el primer screening, repetir al mes. Si persiste, derivar a evaluación audiológica completa antes de los 3 meses."],

            // ── Impedanciometría ──
            ['impedanciometria', '¿Qué es la impedanciometría?', "Evalúa la función del oído medio mediante análisis de la impedancia acústica. Incluye timpanometría y reflejos acústicos estapediales.\n\nEs un examen objetivo (no requiere respuesta del paciente) y complementa la audiometría tonal."],
            ['impedanciometria', 'Timpanometría', "Mide la compliancia del sistema tímpano-osicular en función de la presión.\n\nCurvas de Jerger:\n• Tipo A: normal (pico entre -100 y +50 daPa)\n• Tipo As: pico reducido (fijación osicular, otosclerosis)\n• Tipo Ad: pico muy elevado (disyunción osicular, membrana flácida)\n• Tipo B: plana (líquido en oído medio, perforación, cerumen)\n• Tipo C: pico desplazado a negativos > -100 daPa (disfunción tubárica)"],
            ['impedanciometria', 'Reflejos acústicos', "El reflejo estapedial es la contracción bilateral del músculo del estribo ante un estímulo sonoro intenso (70-100 dB sobre umbral).\n\nSe evalúa ipsi y contralateral. Su presencia, ausencia y umbral orientan sobre:\n• Integridad de la vía auditiva del tronco\n• Lesiones retrococleares (decaimiento del reflejo)\n• Patología de oído medio\n• Reclutamiento (reflejo presente a baja sensación en hipoacusias cocleares)"],
            ['impedanciometria', 'Función tubárica', "La tuba auditiva ventila el oído medio. Su disfunción causa presión negativa y otitis media con efusión.\n\nEvaluación:\n• Timpanometría: curva tipo C indica disfunción\n• Test de Williams: timpanograma con y sin maniobra de Valsalva/Toynbee\n• En perforación: la compliancia cambia al deglutir con la sonda puesta"],
            ['impedanciometria', 'Impedanciometría pediátrica', "En lactantes < 6 meses se usa tono sonda de 1000 Hz (no 226 Hz) porque el conducto auditivo del lactante es más compliante.\n\nEn niños mayores se usa el protocolo estándar. La timpanometría es especialmente útil para detectar otitis media con efusión en preescolares."],

            // ── Oftalmología ──
            ['oftalmologia', 'Campimetría', "La perimetría computarizada evalúa el campo visual detectando estímulos luminosos.\n\nÍndices principales:\n• MD (Mean Deviation): defecto promedio global\n• PSD (Pattern Standard Deviation): irregularidad del defecto\n• VFI (Visual Field Index): porcentaje de campo visual funcional\n• GHT (Glaucoma Hemifield Test): compara hemicampos superior e inferior"],
            ['oftalmologia', 'Patrones de defecto campimétrico', "• Escotoma arciforme: distribución de fibras nerviosas, típico glaucoma\n• Escalón nasal: asimetría nasal, glaucoma\n• Hemianopsia homónima: mismo lado en ambos ojos, lesión retroquiasmática\n• Hemianopsia bitemporal: compresión quiasmática\n• Constricción concéntrica: retinitis pigmentosa, glaucoma avanzado\n• Escotoma central/cecocentral: neuritis óptica, maculopatía"],
            ['oftalmologia', 'OCT', "Tomografía de Coherencia Óptica: imágenes de alta resolución de las capas retinianas.\n\nAplicaciones:\n• RNFL (capa de fibras nerviosas) para glaucoma\n• Espesor macular para edema, membranas, agujeros\n• Cabeza del nervio óptico\n• OCT-Angiografía: vascularización sin contraste"],
            ['oftalmologia', 'OCT en glaucoma', "Mide grosor de RNFL peripapilar y complejo de células ganglionares maculares.\n\nComparación con base normativa:\n• Verde: normal (p > 5%)\n• Amarillo: borderline (p 1-5%)\n• Rojo: fuera de límites (p < 1%)\n\nProgresión: análisis de tendencia y evento."],
            ['oftalmologia', 'Topografía corneal', "Mapea la curvatura de la superficie corneal.\n\nUsos:\n• Detección de queratocono y ectasias\n• Adaptación de lentes de contacto\n• Planificación de cirugía refractiva\n• Seguimiento post-quirúrgico\n\nMapas: axial, tangencial, elevación anterior/posterior, paquimetría."],
            ['oftalmologia', 'Queratocono', "Ectasia corneal progresiva.\n\nSignos topográficos:\n• Asimetría I-S > 1.4 D\n• KISA% > 100%\n• Adelgazamiento corneal descentrado\n• Elevación posterior aumentada\n\nClasificación Amsler-Krumeich: 4 estadios según K máximo, astigmatismo, paquimetría y cicatrices."],
            ['oftalmologia', 'Scheimpflug (Pentacam)', "Cámara rotacional para segmento anterior.\n\nEvalúa:\n• Topografía anterior y posterior\n• Paquimetría punto a punto\n• Profundidad de cámara anterior\n• Densitometría del cristalino\n• Índices de ectasia (BAD-D, Belin-Ambrósio)\n\nÚtil para screening pre-refractivo."],
            ['oftalmologia', 'Autorefractometría', "Mide objetivamente el error refractivo: miopía, hipermetropía y astigmatismo.\n\nProporciona esfera, cilindro y eje como punto de partida para la refracción subjetiva.\n\nLimitaciones: tiende a sobre-menos por acomodación. En niños se requiere cicloplejia."],
            ['oftalmologia', 'Retinografía', "Fotografía del fondo de ojo.\n\nAplicaciones:\n• Retinopatía diabética\n• Excavación papilar en glaucoma\n• Degeneración macular\n• Oclusiones vasculares\n• Desprendimiento de retina\n\nLa retinografía de campo amplio captura hasta 200° del fondo."],

            // ── Otoneurología ──
            ['otoneurologia', 'VNG (Videonistagmografía)', "Registra movimientos oculares con cámaras infrarrojas.\n\nIncluye:\n• Pruebas oculomotoras: sacadas, seguimiento suave, optocinético\n• Pruebas posicionales: Dix-Hallpike, roll test\n• Prueba calórica bitérmica\n\nDiferencia lesiones vestibulares periféricas de centrales."],
            ['otoneurologia', 'Prueba calórica', "Estimula cada laberinto con temperatura fría (30°C) y caliente (44°C).\n\nFórmula de Jongkees:\n• Paresia canalicular: asimetría > 20-25% → lesión periférica\n• Preponderancia direccional: asimetría > 30%\n\nCOWS: Cold Opposite, Warm Same."],
            ['otoneurologia', 'vHIT', "Video Head Impulse Test: evalúa VOR de alta frecuencia.\n\n• Ganancia normal: 0.8-1.2\n• Ganancia reducida: hipofunción del canal\n• Sacadas covert: durante el impulso\n• Sacadas overt: después del impulso\n\nEvalúa los 6 canales, más fisiológico que la calórica."],
            ['otoneurologia', 'VPPB', "Vértigo Posicional Paroxístico Benigno: la causa más frecuente de vértigo.\n\nDiagnóstico:\n• Canal posterior (90%): Dix-Hallpike → nistagmo torsional geotrópico\n• Canal horizontal: roll test\n\nTratamiento:\n• Canal posterior: maniobra de Epley o Semont\n• Canal horizontal: maniobra de Lempert"],
            ['otoneurologia', 'Enfermedad de Ménière', "Tríada: vértigo episódico + hipoacusia fluctuante + tinnitus + plenitud aural.\n\nCriterios AAO-HNS 2015:\n• ≥ 2 episodios de vértigo de 20 min a 12 h\n• Hipoacusia sensorioneural documentada\n• Síntomas aurales fluctuantes\n\nAudiometría: hipoacusia sensorioneural ascendente en etapas iniciales."],
            ['otoneurologia', 'Schwannoma vestibular', "Tumor benigno del VIII par.\n\nSospecha:\n• Hipoacusia sensorioneural unilateral progresiva\n• Tinnitus unilateral\n• Discriminación verbal desproporcionadamente mala\n• Reflejos acústicos ausentes o con decaimiento\n\nConfirmación: RMN con gadolinio. ABR: prolongación de onda V."],

            // ── Flujo clínico ──
            ['clinica', 'Agenda y atención de pacientes', "La agenda muestra los pacientes citados. Desde ella puedes:\n• Ver datos del paciente y motivo de consulta\n• Llamar al paciente cuando sea su turno\n• Registrar la atención y procedimientos\n\nKarime te avisará si hay atrasos o cambios."],
            ['clinica', 'Ficha clínica (Larissa)', "Larissa es el sistema de ficha clínica formato MINSAL:\n• Datos de identificación\n• Anamnesis y antecedentes\n• Exámenes y resultados\n• Evoluciones clínicas\n• Interconsultas y derivaciones\n\nCada estudiante tiene su propia versión del paciente."],
            ['clinica', 'Evoluciones e interconsultas', "Después de cada atención registra una evolución con:\n• Motivo de consulta\n• Hallazgos de los exámenes\n• Hipótesis diagnóstica\n• Plan de manejo\n\nSi el caso lo requiere, genera una interconsulta a otra especialidad."],
            ['clinica', 'Anamnesis audiológica', "Preguntas fundamentales:\n• Motivo de consulta y cronología\n• Hipoacusia: lateralidad, inicio, progresión\n• Tinnitus: unilateral/bilateral, tono\n• Vértigo: tipo, duración, desencadenantes\n• Otalgia, otorrea, plenitud aural\n• Exposición a ruido\n• Antecedentes: ototóxicos, cirugías, familia\n• Desarrollo del lenguaje (en niños)"],
            ['clinica', 'Otoscopía', "Inspección del CAE y membrana timpánica.\n\nDescribir:\n• CAE: permeable, cerumen, exostosis\n• Membrana: color, integridad, posición, movilidad\n• Triángulo luminoso\n• Mango del martillo\n\nAlteraciones frecuentes: perforación, retracción, nivel hidroaéreo, miringitis, tubos."],
            ['clinica', 'Redacción de informes', "Estructura del informe audiológico:\n1. Datos del paciente y fecha\n2. Motivo del examen\n3. Exámenes realizados\n4. Resultados\n5. Correlación clínica\n6. Conclusión diagnóstica\n7. Recomendaciones\n\nLenguaje claro, objetivo y profesional."],

            // ── Equipamiento ──
            ['equipos', 'Audiómetro clínico', "El audiómetro clínico de dos canales permite:\n• Tono puro por vía aérea y ósea\n• Ruido enmascarante\n• Logoaudiometría\n• Campo libre\n\nCalibración según norma ISO 389. Verificar biológicamente cada día."],
            ['equipos', 'Impedanciómetro', "Equipo para timpanometría y reflejos acústicos.\n\nComponentes:\n• Sonda: altavoz, micrófono, bomba de presión\n• Auricular contralateral para reflejos\n\nVerificar hermeticidad del sello. En niños < 6 meses usar tono sonda de 1000 Hz."],
            ['equipos', 'Calibración y mantenimiento', "• Calibración electroacústica anual según ISO/IEC\n• Verificación biológica diaria\n• Limpieza de auriculares y olivas después de cada paciente\n• Almacenar en ambiente controlado\n• Registro de calibraciones en bitácora\n\nUn equipo descalibrado genera diagnósticos erróneos."],
            ['equipos', 'Cabina audiométrica', "Requisitos según ANSI S3.1:\n• Nivel de ruido ambiental máximo por frecuencia\n• Paredes con aislamiento acústico y absorción interna\n• Puerta con sello hermético\n• Ventana de observación\n• Sistema de comunicación\n• Iluminación adecuada\n\nVerificar periódicamente con sonómetro."],

            // ── Rehabilitación ──
            ['rehabilitacion', 'Audífonos: tipos y selección', "Tipos principales:\n• BTE (retroauricular): versátil\n• RIC (receptor en canal): discreto\n• ITE/ITC/CIC (intraauricular): estéticos\n\nSelección según grado de pérdida, necesidades comunicativas, destreza manual, anatomía y presupuesto."],
            ['rehabilitacion', 'Proceso de adaptación', "1. Evaluación audiológica completa\n2. Selección del audífono\n3. Toma de impresión\n4. Programación inicial (NAL-NL2 o DSL)\n5. Verificación con medición en oído real\n6. Validación subjetiva (APHAB, IOI-HA)\n7. Seguimiento y ajustes\n8. Consejería sobre uso y expectativas"],
            ['rehabilitacion', 'Implante coclear', "Estimula directamente el nervio auditivo.\n\nCriterios:\n• Hipoacusia sensorioneural severa-profunda bilateral\n• Beneficio limitado con audífonos\n• Evaluación multidisciplinaria\n\nComponentes: procesador externo + implante interno con electrodo intracoclear."],
            ['rehabilitacion', 'Terapia auditiva', "Rehabilitación complementaria:\n• Entrenamiento auditivo: detección, discriminación, identificación, comprensión\n• Lectura labial como apoyo visual\n• Estrategias comunicativas para paciente y familia\n• Manejo del tinnitus (TRT, CBT)\n\nEn niños: terapia auditivo-verbal para desarrollo del lenguaje."],
        ];

        $stmt = $db->prepare(
            "INSERT INTO kb_articles (id, category_id, title, content, sort_order)
             VALUES (:id, :cat, :title, :content, :sort)"
        );
        $sortIdx = 0;
        $currentCat = '';
        foreach ($kbArticles as $a) {
            if ($a[0] !== $currentCat) { $sortIdx = 0; $currentCat = $a[0]; }
            $stmt->execute([
                ':id' => Database::uuid(),
                ':cat' => $a[0],
                ':title' => $a[1],
                ':content' => $a[2],
                ':sort' => ++$sortIdx,
            ]);
        }
        $total = count($kbArticles);
        out($isCli ? "  ✓ $total artículos insertados en " . count($kbCategories) . " categorías" : "<span class='ok'>  ✓ $total artículos insertados</span>", $isCli);
    } else {
        out($isCli ? "\n· Base de conocimiento ya existe ($kbCount categorías)" : "<span class='skip'>· Base de conocimiento ya existe</span>", $isCli);
    }
}

// ─── Resumen ────────────────────────────────────────
out("", $isCli);
out($isCli ? "═══════════════════════════════════════" : "<hr>", $isCli);
out($isCli ? "✓ Migración completada" : "<span class='ok'><strong>✓ Migración completada</strong></span>", $isCli);

if (!$isCli) echo '</body></html>';
