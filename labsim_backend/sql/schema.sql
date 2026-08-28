-- labsim_backend schema (SQLite)
-- Pensado para hosting compartido, ~14 clientes: SQLite en modo WAL soporta
-- bien varios lectores concurrentes + un escritor ocasional, y no requiere
-- crear una base MySQL aparte en el panel del hosting (solo un archivo).
-- Sync incremental via columna updated_at (no requiere websockets: los
-- clientes hacen polling a /api/sync.php?since=<updated_at>).

PRAGMA foreign_keys = ON;

-- version = '1.3' (OIDC, columnas issuer.. jwks_url) o '1.1' (OAuth1,
-- columnas consumer_key/shared_secret) -- se soportan ambas a la vez
-- porque no todas las Moodle tienen bien expuesto el LTI Advantage.
CREATE TABLE IF NOT EXISTS lti_platforms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    version TEXT NOT NULL DEFAULT '1.3',
    issuer TEXT NOT NULL DEFAULT '',
    client_id TEXT NOT NULL DEFAULT '',
    deployment_id TEXT NOT NULL DEFAULT '',
    auth_login_url TEXT NOT NULL DEFAULT '',
    auth_token_url TEXT NOT NULL DEFAULT '',
    jwks_url TEXT NOT NULL DEFAULT '',
    consumer_key TEXT NOT NULL DEFAULT '',
    shared_secret TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 1
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_lti_platforms_13
    ON lti_platforms (issuer, client_id, deployment_id) WHERE version = '1.3';
CREATE UNIQUE INDEX IF NOT EXISTS idx_lti_platforms_11
    ON lti_platforms (consumer_key) WHERE version = '1.1' AND consumer_key <> '';

-- Nonces de OAuth1 (launch LTI 1.1), anti-replay. Vida corta: migrate.php
-- limpia lo viejo de vez en cuando en cada llamada a Lti::validateLaunch11.
CREATE TABLE IF NOT EXISTS lti_oauth_nonces (
    consumer_key TEXT NOT NULL,
    nonce TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (consumer_key, nonce)
);

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role TEXT NOT NULL CHECK (role IN ('student', 'admin')),
    username TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    password_hash TEXT,                       -- solo admin (login local, no LTI)
    lti_platform_id INTEGER REFERENCES lti_platforms(id),
    lti_sub TEXT,                             -- id del usuario en Moodle
    permission INTEGER NOT NULL DEFAULT 444,
    modules TEXT,                             -- JSON como texto plano (se maneja en PHP)
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (lti_platform_id, lti_sub)
);

-- Códigos de emparejamiento temporales: puente entre el login LTI (navegador)
-- y la app de escritorio, que no puede recibir el redirect del LMS.
CREATE TABLE IF NOT EXISTS pairing_codes (
    code TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    expires_at TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Tokens de sesión de la app (bearer opaco, revocable). Reemplaza JWT del
-- lado app<->backend: más simple de invalidar desde el panel admin.
CREATE TABLE IF NOT EXISTS tokens (
    token TEXT PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Nonces/state de OIDC (LTI login flow), de vida corta.
CREATE TABLE IF NOT EXISTS lti_states (
    state TEXT PRIMARY KEY,
    nonce TEXT NOT NULL,
    lti_platform_id INTEGER NOT NULL REFERENCES lti_platforms(id),
    expires_at TEXT NOT NULL
);

-- Primer diseño (agenda con 1 alumno por fila) resultó no calzar con el
-- modelo real: la agenda es una cola compartida, cualquier alumno puede
-- atender cualquier cita, y cada uno lleva su propio progreso. Se reemplaza
-- por cases/appointments/attendances más abajo. DROP seguro: en el momento
-- de este cambio estas tablas seguían vacías (nada las usaba todavía).
DROP TABLE IF EXISTS agenda;
DROP TABLE IF EXISTS patients;

-- Casos clínicos (antes cases.json). id = mismo case_id que ya usa la app.
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL,               -- JSON: Anamnesis, audiometría, etc. (definición del caso)
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Citas de la agenda (antes cada fila de schedule.json["agenda_1"]).
-- Compartidas: cualquier alumno puede atenderlas (ver attendances abajo).
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL DEFAULT '',   -- 'dd-MM-yy', vacío = paciente sin agendar aún
    hora TEXT NOT NULL DEFAULT '',    -- 'HH:mm'
    rut TEXT NOT NULL DEFAULT '',
    nombre TEXT NOT NULL DEFAULT '',
    apellido TEXT NOT NULL DEFAULT '',
    fecha_nac TEXT NOT NULL DEFAULT '',
    procedimiento TEXT NOT NULL DEFAULT '',
    case_id TEXT REFERENCES cases(id),
    nota_admin TEXT NOT NULL DEFAULT '',
    cancelada INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_appointments_updated ON appointments (updated_at);
CREATE INDEX IF NOT EXISTS idx_appointments_fecha ON appointments (fecha);
CREATE INDEX IF NOT EXISTS idx_appointments_rut ON appointments (rut);

-- Progreso de CADA alumno sobre una cita (antes entry[8], el dict por
-- username). Varios alumnos pueden tener fila propia para la misma cita.
CREATE TABLE IF NOT EXISTS attendances (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER NOT NULL REFERENCES appointments(id),
    student_id INTEGER NOT NULL REFERENCES users(id),
    estado TEXT NOT NULL CHECK (estado IN ('atendiendo', 'atendido', 'no_show')),
    nota TEXT NOT NULL DEFAULT '',
    hora_real TEXT NOT NULL DEFAULT '',
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (appointment_id, student_id)
);
CREATE INDEX IF NOT EXISTS idx_attendances_updated ON attendances (updated_at);
CREATE INDEX IF NOT EXISTS idx_attendances_student ON attendances (student_id);

-- Registro de acciones del estudiante (reemplaza el print a consola).
-- El cliente junta eventos localmente y los sube en lotes -> nunca streaming.
CREATE TABLE IF NOT EXISTS action_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    client_ts TEXT NOT NULL,          -- hora en el cliente cuando ocurrió
    action TEXT NOT NULL,
    payload TEXT,                     -- JSON
    received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_logs_user_ts ON action_logs (user_id, client_ts);

-- Configuración compartida (equivalente a preferences.json / config_*.json,
-- pero editable por el admin y sincronizada a todos).
CREATE TABLE IF NOT EXISTS app_config (
    k TEXT PRIMARY KEY,
    v TEXT NOT NULL,                  -- JSON
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
