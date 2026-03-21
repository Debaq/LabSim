<?php
/**
 * LabSim Backend - Script de instalación inicial
 * Ejecutar UNA vez, luego ELIMINAR este archivo.
 *
 * Uso: php install.php
 * O visitar: https://tmeduca.org/labsim/backend/install.php
 */

$isCli = php_sapi_name() === 'cli';

function out(string $msg, bool $isCli): void {
    echo $isCli ? "$msg\n" : "<p>$msg</p>";
}

if (!$isCli) {
    echo '<!DOCTYPE html><html><head><title>LabSim Install</title>
    <style>body{font-family:monospace;max-width:700px;margin:40px auto;padding:20px;background:#1a1a2e;color:#e0e0e0}
    p{margin:4px 0}.ok{color:#4ade80}.err{color:#f87171}.warn{color:#fbbf24}h1{color:#818cf8}</style></head><body>';
    echo '<h1>LabSim Backend - Instalación</h1>';
}

// Verificar PHP
$phpVersion = phpversion();
if (version_compare($phpVersion, '7.4', '<')) {
    out("<span class='err'>✗ PHP $phpVersion — Se requiere 7.4+</span>", $isCli);
    exit(1);
}
out($isCli ? "✓ PHP $phpVersion" : "<span class='ok'>✓ PHP $phpVersion</span>", $isCli);

// Verificar extensiones
$required = ['pdo', 'pdo_sqlite', 'json', 'mbstring'];
foreach ($required as $ext) {
    if (!extension_loaded($ext)) {
        out($isCli ? "✗ Falta extensión: $ext" : "<span class='err'>✗ Falta extensión: $ext</span>", $isCli);
        exit(1);
    }
    out($isCli ? "✓ Extensión: $ext" : "<span class='ok'>✓ Extensión: $ext</span>", $isCli);
}

require_once __DIR__ . '/core/config.php';
require_once __DIR__ . '/core/db.php';

// Crear directorio data
if (!is_dir(DATA_PATH)) {
    mkdir(DATA_PATH, 0750, true);
    out($isCli ? "✓ Directorio data/ creado" : "<span class='ok'>✓ Directorio data/ creado</span>", $isCli);
}

// Proteger data/ con .htaccess propio
$dataHtaccess = DATA_PATH . '/.htaccess';
if (!file_exists($dataHtaccess)) {
    file_put_contents($dataHtaccess, "Require all denied\n");
    out($isCli ? "✓ data/.htaccess creado" : "<span class='ok'>✓ data/.htaccess creado</span>", $isCli);
}

// Crear directorios de uploads
foreach (['guides', 'releases', 'assets'] as $dir) {
    $path = UPLOADS_PATH . "/$dir";
    if (!is_dir($path)) {
        mkdir($path, 0750, true);
    }
}
out($isCli ? "✓ Directorios uploads/ creados" : "<span class='ok'>✓ Directorios uploads/ creados</span>", $isCli);

// Crear tablas
$db = Database::get();

out($isCli ? "\n— Creando tablas..." : "<br><strong>Creando tablas...</strong>", $isCli);

$schemas = [
    'users' => "CREATE TABLE IF NOT EXISTS users (
        id TEXT PRIMARY KEY,
        username TEXT NOT NULL UNIQUE,
        email TEXT,
        password_hash TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'estudiante'
            CHECK (role IN ('admin','docente','instructor','estudiante')),
        full_name TEXT,
        institution TEXT,
        is_active INTEGER NOT NULL DEFAULT 1,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )",

    'cases' => "CREATE TABLE IF NOT EXISTS cases (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        author_id TEXT NOT NULL REFERENCES users(id),
        profile_json TEXT NOT NULL DEFAULT '{}',
        schema_version INTEGER NOT NULL DEFAULT 1,
        tags TEXT DEFAULT '',
        difficulty TEXT DEFAULT 'medium' CHECK (difficulty IN ('easy','medium','hard')),
        is_published INTEGER NOT NULL DEFAULT 0,
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
    )",

    'student_groups' => "CREATE TABLE IF NOT EXISTS student_groups (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        description TEXT,
        institution TEXT,
        created_by TEXT REFERENCES users(id),
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    )",

    'boxes' => "CREATE TABLE IF NOT EXISTS boxes (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES practice_sessions(id),
        box_number INTEGER NOT NULL,
        name TEXT,
        student_id TEXT REFERENCES users(id),
        equipment_list TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE (session_id, box_number)
    )",

    'center_incidents' => "CREATE TABLE IF NOT EXISTS center_incidents (
        id TEXT PRIMARY KEY,
        session_id TEXT REFERENCES practice_sessions(id),
        created_by TEXT REFERENCES users(id),
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
    )",

    'clinical_meetings' => "CREATE TABLE IF NOT EXISTS clinical_meetings (
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
    )",

    'meeting_participants' => "CREATE TABLE IF NOT EXISTS meeting_participants (
        meeting_id TEXT NOT NULL REFERENCES clinical_meetings(id),
        user_id TEXT NOT NULL REFERENCES users(id),
        attended INTEGER DEFAULT 0,
        notes TEXT,
        PRIMARY KEY (meeting_id, user_id)
    )",

    'meeting_incidents' => "CREATE TABLE IF NOT EXISTS meeting_incidents (
        meeting_id TEXT NOT NULL REFERENCES clinical_meetings(id),
        incident_id TEXT NOT NULL REFERENCES center_incidents(id),
        PRIMARY KEY (meeting_id, incident_id)
    )",

    'chat_messages' => "CREATE TABLE IF NOT EXISTS chat_messages (
        id TEXT PRIMARY KEY,
        sender_id TEXT NOT NULL REFERENCES users(id),
        recipient_id TEXT REFERENCES users(id),
        group_id TEXT,
        session_id TEXT REFERENCES practice_sessions(id),
        message TEXT NOT NULL,
        message_type TEXT DEFAULT 'text' CHECK (message_type IN ('text','system','incident','meeting_call')),
        is_read INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )",

    'group_members' => "CREATE TABLE IF NOT EXISTS group_members (
        group_id TEXT NOT NULL REFERENCES student_groups(id),
        user_id TEXT NOT NULL REFERENCES users(id),
        member_role TEXT DEFAULT 'student'
            CHECK (member_role IN ('student','instructor','docente')),
        joined_at TEXT DEFAULT (datetime('now')),
        PRIMARY KEY (group_id, user_id)
    )",

    'practice_sessions' => "CREATE TABLE IF NOT EXISTS practice_sessions (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT,
        created_by TEXT NOT NULL REFERENCES users(id),
        approved_by TEXT REFERENCES users(id),
        status TEXT DEFAULT 'draft'
            CHECK (status IN ('draft','pending_approval','approved','active','completed','cancelled')),
        scheduled_date TEXT,
        scheduled_time TEXT,
        duration_minutes INTEGER DEFAULT 90,
        location TEXT,
        group_id TEXT REFERENCES student_groups(id),
        instructions TEXT,
        max_submissions INTEGER DEFAULT 1,
        allow_late_submission INTEGER DEFAULT 0,
        due_date TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )",

    'practice_session_cases' => "CREATE TABLE IF NOT EXISTS practice_session_cases (
        session_id TEXT NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
        case_id TEXT NOT NULL REFERENCES cases(id),
        order_index INTEGER DEFAULT 0,
        is_required INTEGER DEFAULT 1,
        PRIMARY KEY (session_id, case_id)
    )",

    'session_guides' => "CREATE TABLE IF NOT EXISTS session_guides (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES practice_sessions(id) ON DELETE CASCADE,
        uploaded_by TEXT REFERENCES users(id),
        title TEXT NOT NULL,
        description TEXT,
        file_path TEXT NOT NULL,
        file_size INTEGER,
        mime_type TEXT,
        guide_type TEXT DEFAULT 'document'
            CHECK (guide_type IN ('document','image','video','reference','link','other')),
        external_url TEXT,
        created_at TEXT DEFAULT (datetime('now'))
    )",

    'submissions' => "CREATE TABLE IF NOT EXISTS submissions (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES practice_sessions(id),
        case_id TEXT NOT NULL REFERENCES cases(id),
        student_id TEXT NOT NULL REFERENCES users(id),
        submission_json TEXT NOT NULL DEFAULT '{}',
        status TEXT DEFAULT 'draft'
            CHECK (status IN ('draft','submitted','reviewed','returned')),
        grade REAL,
        feedback TEXT,
        reviewed_by TEXT REFERENCES users(id),
        submitted_at TEXT,
        reviewed_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        UNIQUE (session_id, case_id, student_id)
    )",

    'procedures' => "CREATE TABLE IF NOT EXISTS procedures (
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
    )",

    'agenda_items' => "CREATE TABLE IF NOT EXISTS agenda_items (
        id TEXT PRIMARY KEY,
        author_id TEXT NOT NULL REFERENCES users(id),
        patient_name TEXT NOT NULL,
        patient_age INTEGER,
        patient_gender TEXT,
        patient_notes TEXT,
        procedure_id TEXT REFERENCES procedures(id),
        scheduled_date TEXT NOT NULL,
        scheduled_time TEXT NOT NULL,
        duration_minutes INTEGER DEFAULT 30,
        status TEXT DEFAULT 'scheduled'
            CHECK (status IN ('scheduled','in_progress','completed','cancelled','rescheduled','no_show')),
        case_id TEXT REFERENCES cases(id),
        assigned_to TEXT REFERENCES users(id),
        session_id TEXT REFERENCES practice_sessions(id),
        rescheduled_from TEXT REFERENCES agenda_items(id),
        rescheduled_date TEXT,
        rescheduled_time TEXT,
        completion_notes TEXT,
        is_active INTEGER DEFAULT 1,
        created_at TEXT DEFAULT (datetime('now'))
    )",

    'app_releases' => "CREATE TABLE IF NOT EXISTS app_releases (
        id TEXT PRIMARY KEY,
        version TEXT NOT NULL UNIQUE,
        release_notes TEXT,
        download_url_linux TEXT,
        download_url_windows TEXT,
        download_url_macos TEXT,
        checksum_sha256 TEXT,
        is_latest INTEGER DEFAULT 0,
        is_mandatory INTEGER DEFAULT 0,
        published_at TEXT DEFAULT (datetime('now'))
    )",

    'assets' => "CREATE TABLE IF NOT EXISTS assets (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        category TEXT,
        file_path TEXT NOT NULL,
        file_size INTEGER,
        mime_type TEXT,
        uploaded_by TEXT REFERENCES users(id),
        created_at TEXT DEFAULT (datetime('now'))
    )",

    'sync_log' => "CREATE TABLE IF NOT EXISTS sync_log (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id),
        device_id TEXT,
        entity_type TEXT NOT NULL,
        entity_id TEXT NOT NULL,
        action TEXT NOT NULL CHECK (action IN ('push','pull')),
        synced_at TEXT DEFAULT (datetime('now'))
    )",

    'app_sessions' => "CREATE TABLE IF NOT EXISTS app_sessions (
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
    )",

    'simulator_events' => "CREATE TABLE IF NOT EXISTS simulator_events (
        id TEXT PRIMARY KEY,
        session_id TEXT NOT NULL REFERENCES app_sessions(id),
        user_id TEXT NOT NULL,
        simulator TEXT NOT NULL,
        event_type TEXT NOT NULL,
        event_data TEXT DEFAULT '{}',
        event_timestamp TEXT NOT NULL
    )",

    'patient_encounter_stats' => "CREATE TABLE IF NOT EXISTS patient_encounter_stats (
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
    )",

    'module_interaction_stats' => "CREATE TABLE IF NOT EXISTS module_interaction_stats (
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
    )",

    'karime_directives' => "CREATE TABLE IF NOT EXISTS karime_directives (
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
    )",

    'patient_feedback' => "CREATE TABLE IF NOT EXISTS patient_feedback (
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
    )",

    'time_alerts' => "CREATE TABLE IF NOT EXISTS time_alerts (
        id TEXT PRIMARY KEY,
        agenda_item_id TEXT NOT NULL REFERENCES agenda_items(id),
        student_id TEXT NOT NULL REFERENCES users(id),
        alert_type TEXT NOT NULL CHECK (alert_type IN ('warning','urgent','critical')),
        minutes_over INTEGER NOT NULL,
        message TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    )",

    'login_attempts' => "CREATE TABLE IF NOT EXISTS login_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        ip_address TEXT NOT NULL,
        attempted_at TEXT DEFAULT (datetime('now'))
    )",

    'refresh_tokens' => "CREATE TABLE IF NOT EXISTS refresh_tokens (
        id TEXT PRIMARY KEY,
        user_id TEXT NOT NULL REFERENCES users(id),
        token_hash TEXT NOT NULL,
        expires_at TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now'))
    )",
];

foreach ($schemas as $name => $sql) {
    $db->exec($sql);
    out($isCli ? "  ✓ $name" : "<span class='ok'>  ✓ $name</span>", $isCli);
}

// Índices
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
    $db->exec($sql);
}
out($isCli ? "  ✓ Índices creados" : "<span class='ok'>  ✓ Índices creados</span>", $isCli);

// Crear usuario admin por defecto
$adminId = Database::uuid();
$adminExists = Database::fetchOne("SELECT id FROM users WHERE username = 'admin'");

if (!$adminExists) {
    Database::execute(
        "INSERT INTO users (id, username, password_hash, role, full_name, is_active)
         VALUES (:id, 'admin', :hash, 'admin', 'Administrador', 1)",
        [
            ':id' => $adminId,
            ':hash' => password_hash('labsim2025', PASSWORD_BCRYPT),
        ]
    );
    out($isCli ? "\n✓ Usuario admin creado (admin / labsim2025)" : "<br><span class='ok'>✓ Usuario admin creado (admin / labsim2025)</span>", $isCli);
} else {
    out($isCli ? "\n⚠ Usuario admin ya existe" : "<br><span class='warn'>⚠ Usuario admin ya existe</span>", $isCli);
}

// Cartera de procedimientos por defecto
$procedureExists = Database::fetchOne("SELECT id FROM procedures LIMIT 1");
if (!$procedureExists) {
    $procedures = [
        // Audiología
        ['Audiometría tonal liminar', 'AUD-001', 'audiologia', 30, 'Evaluación de umbrales auditivos por vía aérea y ósea', 'audiometro'],
        ['Logoaudiometría', 'AUD-002', 'audiologia', 20, 'Evaluación de discriminación del habla (SRT, SD)', 'audiometro'],
        ['Audiometría supraliminar', 'AUD-003', 'audiologia', 25, 'Pruebas supraliminares (SISI, Tone Decay, etc.)', 'audiometro'],
        ['Impedanciometría', 'AUD-004', 'audiologia', 20, 'Timpanometría y reflejos estapediales', 'impedanciometro'],
        ['Emisiones otoacústicas (EOA)', 'AUD-005', 'audiologia', 15, 'TEOAE y/o DPOAE', null],
        ['Potenciales evocados auditivos (PEATC)', 'AUD-006', 'electrodiagnostico', 45, 'ABR / BERA', null],
        ['Electrococleografía', 'AUD-007', 'electrodiagnostico', 40, 'ECoG', null],
        ['Evaluación de audífonos', 'AUD-008', 'audiologia', 45, 'Selección, adaptación y verificación de audífonos', null],
        ['Evaluación audiológica completa', 'AUD-009', 'audiologia', 60, 'Audiometría + logoaudiometría + impedanciometría', 'audiometro,impedanciometro'],
        // Oftalmología
        ['Tomografía de coherencia óptica (OCT)', 'OFT-001', 'oftalmologia', 15, 'OCT de retina, RNFL, GCL', 'oct'],
        ['Campimetría / Perimetría', 'OFT-002', 'oftalmologia', 25, 'Campo visual computarizado', 'perimetro'],
        ['Evaluación oftalmológica completa', 'OFT-003', 'oftalmologia', 45, 'OCT + campimetría + evaluación clínica', 'oct,perimetro'],
        // Vestibular
        ['Videonistagmografía (VNG)', 'VES-001', 'vestibular', 40, 'Evaluación vestibular con VNG', null],
        ['Prueba calórica', 'VES-002', 'vestibular', 30, 'Irrigación calórica bilateral', null],
        ['vHIT', 'VES-003', 'vestibular', 20, 'Video Head Impulse Test', null],
        // Otros
        ['Consulta general', 'GEN-001', 'otro', 30, 'Consulta de evaluación inicial', null],
        ['Control / Seguimiento', 'GEN-002', 'otro', 20, 'Control post-tratamiento', null],
    ];

    $stmt = $db->prepare(
        "INSERT INTO procedures (id, name, code, category, default_duration_minutes, description, requires_equipment)
         VALUES (:id, :name, :code, :cat, :dur, :desc, :equip)"
    );

    foreach ($procedures as $p) {
        $stmt->execute([
            ':id' => Database::uuid(),
            ':name' => $p[0],
            ':code' => $p[1],
            ':cat' => $p[2],
            ':dur' => $p[3],
            ':desc' => $p[4],
            ':equip' => $p[5],
        ]);
    }
    out($isCli ? "✓ Cartera de procedimientos creada (" . count($procedures) . " procedimientos)" : "<span class='ok'>✓ Cartera de procedimientos creada (" . count($procedures) . ")</span>", $isCli);
} else {
    out($isCli ? "⚠ Procedimientos ya existen" : "<span class='warn'>⚠ Procedimientos ya existen</span>", $isCli);
}

// Biblioteca de incidentes/problemas del centro (templates)
$incidentExists = Database::fetchOne("SELECT id FROM center_incidents WHERE is_template = 1 LIMIT 1");
if (!$incidentExists) {
    $incidents = [
        // Accesibilidad
        ['accesibilidad', 'Paciente en silla de ruedas', 'Un paciente llegó en silla de ruedas y no puede acceder a la cámara sonoamortiguada. La puerta es muy angosta y no hay rampa interna. El acompañante pide solución.', 'high', 10],
        ['accesibilidad', 'Paciente con discapacidad visual', 'Llegó un paciente con discapacidad visual sin acompañante. Necesita asistencia para moverse por el centro y para entender las instrucciones del examen.', 'moderate', 15],
        ['accesibilidad', 'Adulto mayor con movilidad reducida', 'Un paciente de 87 años no puede subirse a la camilla del box. Necesita ayuda y el box no tiene escalón auxiliar.', 'moderate', 20],

        // Equipamiento
        ['equipamiento', 'Calibración vencida del audiómetro', 'Se detectó que el audiómetro del Box {box} tiene la calibración vencida hace 2 semanas. Los resultados podrían no ser confiables. ¿Se siguen atendiendo pacientes o se suspende?', 'critical', 5],
        ['equipamiento', 'Impedanciómetro no enciende', 'El impedanciómetro del Box {box} no enciende. Hay pacientes citados para timpanometría. ¿Se redistribuyen a otro box o se reagendan?', 'high', 8],
        ['equipamiento', 'Falta de olivas para impedanciómetro', 'Se acabaron las olivas de tamaño pequeño y mediano. Solo quedan grandes. Hay 3 pacientes pediátricos en agenda.', 'moderate', 25],
        ['equipamiento', 'Campímetro muestra error de software', 'El campímetro del Box {box} muestra un error de software y se reinicia solo durante los exámenes. Ya perdió los datos de un paciente.', 'high', 12],
        ['equipamiento', 'Auriculares con canal obstruido', 'Los auriculares TDH-39 del Box {box} tienen el canal izquierdo parcialmente obstruido. Los tonos se escuchan distorsionados.', 'high', 15],

        // Infraestructura
        ['infraestructura', 'Aire acondicionado no funciona', 'El aire acondicionado de la sala de espera dejó de funcionar. Hay 30°C y los pacientes se quejan. Algunos quieren irse.', 'moderate', 30],
        ['infraestructura', 'Baños sin agua', 'Los baños del centro no tienen agua desde hace 1 hora. Varios pacientes han preguntado y hay quejas.', 'high', 20],
        ['infraestructura', 'Asiento roto en sala de espera', 'Un asiento de la sala de espera se rompió cuando un paciente se sentó. No hubo lesiones pero el paciente está molesto.', 'low', 35],
        ['infraestructura', 'Ruido de construcción afecta exámenes', 'Hay obras de construcción en el edificio contiguo. El ruido penetra la cámara sonoamortiguada y afecta los umbrales en frecuencias bajas.', 'critical', 10],
        ['infraestructura', 'Corte de luz', 'Se cortó la electricidad en el centro. Los equipos se apagaron. Hay pacientes a medio examinar. El generador no arrancó automáticamente.', 'critical', 0],

        // Paciente
        ['paciente', 'Paciente con crisis de ansiedad', 'Un paciente tuvo una crisis de ansiedad dentro de la cámara sonoamortiguada. Está hiperventilando y no quiere volver a entrar.', 'high', 15],
        ['paciente', 'Niño que no coopera', 'Un paciente pediátrico de 4 años no coopera con el examen. Llora, se saca los auriculares y los padres están frustrados.', 'moderate', 10],
        ['paciente', 'Paciente llega con otitis activa', 'Un paciente citado para impedanciometría llegó con otorrea activa (infección con supuración). ¿Se realiza el examen o se deriva?', 'moderate', 5],
        ['paciente', 'Reclamo por tiempo de espera', 'Un paciente lleva 45 minutos esperando y está furioso. Amenaza con irse y poner un reclamo formal. Tiene derivación del otorrino con urgencia.', 'high', 40],

        // Administrativo
        ['administrativo', 'Doble agendamiento', 'Se agendaron dos pacientes a la misma hora en el Box {box}. Ambos ya llegaron y ambos insisten en que tienen cita.', 'high', 0],
        ['administrativo', 'Paciente sin orden médica', 'Llegó un paciente sin orden médica ni derivación. Dice que el doctor le dijo que viniera directamente. ¿Se atiende o se le pide que vuelva con la orden?', 'low', 5],
        ['administrativo', 'Informe extraviado', 'Un paciente viene a retirar su informe del mes pasado pero no aparece en el sistema ni en los archivos físicos. Está muy molesto.', 'moderate', 30],

        // Bioseguridad
        ['bioseguridad', 'Paciente con sospecha de COVID', 'Un paciente en sala de espera empezó a toser y tiene fiebre. No declaró síntomas al ingresar. Hay otros 5 pacientes en la sala.', 'critical', 10],
        ['bioseguridad', 'Falta de alcohol gel', 'Se acabó el alcohol gel en todos los dispensadores del centro. Están usando agua y jabón pero hay quejas.', 'moderate', 25],

        // Emergencia
        ['emergencia', 'Paciente se desmayó en sala de espera', 'Un paciente se desmayó en la sala de espera. Está consciente pero desorientado. No se sabe si tiene condiciones previas. Somos un centro de especialidad, NO somos urgencias. ¿Qué protocolo se activa?', 'critical', 0],
        ['emergencia', 'Reacción alérgica a gel conductor', 'Un paciente presentó una reacción alérgica (enrojecimiento, picazón) al gel conductor usado en ABR. La zona está inflamada.', 'high', 5],
        ['emergencia', 'Paciente pediátrico convulsiona', 'Un niño de 6 años comenzó a convulsionar durante la audiometría. Los padres están desesperados. Somos centro de especialidad, no contamos con equipo de reanimación avanzado.', 'critical', 0],

        // Personal / Recursos humanos
        ['administrativo', 'Colega no vino a trabajar', 'El audiólogo del Box {box} no se presentó a trabajar y no contestó el teléfono. Tiene 6 pacientes agendados. ¿Se redistribuyen entre los demás boxes o se reagendan?', 'high', 0],
        ['administrativo', 'Doble agenda por ausencia', 'Debido a la ausencia del colega, usted debe asumir su agenda además de la propia. Son 4 pacientes adicionales. Reorganice los tiempos.', 'high', 5],
        ['administrativo', 'Técnico de mantenimiento no disponible', 'Se reportó una falla en un equipo pero el técnico de mantenimiento no está disponible hasta mañana. Hay pacientes que requieren ese equipo hoy.', 'moderate', 20],

        // Infraestructura adicional
        ['infraestructura', 'Filtración de agua en box', 'Está lloviendo y hay una filtración de agua en el techo del Box {box}. El agua gotea cerca del equipo. ¿Se traslada el equipo, se suspende la atención o se busca solución temporal?', 'high', 15],
        ['infraestructura', 'Cámara sonoamortiguada con humedad', 'La cámara sonoamortiguada tiene problemas de humedad. Hay olor a moho y las paredes están húmedas. Podría afectar la salud y el rendimiento acústico.', 'high', 25],
        ['infraestructura', 'Puerta del box no cierra bien', 'La puerta del Box {box} no cierra herméticamente. Se filtra ruido del pasillo y afecta los exámenes audiológicos.', 'moderate', 10],

        // Equipamiento adicional
        ['equipamiento', 'Software del equipo requiere actualización', 'El software del campímetro muestra un mensaje de actualización obligatoria. Si no se actualiza, no permite realizar exámenes. La actualización toma 45 minutos.', 'high', 8],
        ['equipamiento', 'Se acabó el papel de impresión', 'La impresora del centro se quedó sin papel. Hay informes pendientes de imprimir y pacientes esperando sus resultados.', 'low', 30],
        ['equipamiento', 'Otoscopio sin batería', 'El otoscopio del Box {box} se quedó sin batería y no hay repuestos. No se puede hacer la otoscopia previa al examen.', 'moderate', 5],

        // Situaciones éticas/profesionales
        ['paciente', 'Familiar exige resultados por teléfono', 'El hijo de un paciente adulto mayor llama por teléfono exigiendo los resultados del examen de su padre. El paciente no firmó autorización de entrega a terceros.', 'moderate', 20],
        ['paciente', 'Paciente pide que le cambien de profesional', 'Un paciente solicita ser atendido por otro profesional porque dice que el estudiante "se ve muy joven" y no le tiene confianza.', 'moderate', 15],
        ['paciente', 'Sospecha de maltrato infantil', 'Durante la anamnesis de un niño de 5 años, se observan marcas sospechosas y el niño se muestra temeroso. El acompañante evita preguntas.', 'critical', 10],
        ['administrativo', 'Paciente quiere grabar la consulta', 'Un paciente sacó su teléfono y está grabando video de la consulta sin pedir permiso. Dice que es su derecho.', 'moderate', 12],
    ];

    $stmt = $db->prepare(
        "INSERT INTO center_incidents (id, session_id, created_by, category, title, description, severity, is_template, trigger_time_minutes)
         VALUES (:id, NULL, NULL, :cat, :title, :desc, :sev, 1, :trigger)"
    );

    foreach ($incidents as $inc) {
        $stmt->execute([
            ':id' => Database::uuid(),
            ':cat' => $inc[0],
            ':title' => $inc[1],
            ':desc' => $inc[2],
            ':sev' => $inc[3],
            ':trigger' => $inc[4],
        ]);
    }
    out($isCli ? "✓ Biblioteca de incidentes creada (" . count($incidents) . " templates)" : "<span class='ok'>✓ Biblioteca de incidentes (" . count($incidents) . " templates)</span>", $isCli);
} else {
    out($isCli ? "⚠ Incidentes template ya existen" : "<span class='warn'>⚠ Incidentes template ya existen</span>", $isCli);
}

// Resumen
out("", $isCli);
out($isCli ? "═══════════════════════════════════════" : "<hr>", $isCli);
out($isCli ? "✓ Instalación completada" : "<span class='ok'><strong>✓ Instalación completada</strong></span>", $isCli);
out($isCli ? "  BD: " . DB_PATH : "<span class='ok'>  BD: " . DB_PATH . "</span>", $isCli);
out($isCli ? "" : "", $isCli);
out($isCli
    ? "⚠ ELIMINA este archivo (install.php) antes de usar en producción"
    : "<br><span class='warn'>⚠ <strong>ELIMINA este archivo (install.php) antes de usar en producción</strong></span>",
    $isCli
);

if (!$isCli) {
    echo '</body></html>';
}
