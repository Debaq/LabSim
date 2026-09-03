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
-- user_id/issued_code quedan null hasta que el launch termina de validarse
-- y emite un código -- si el navegador reenvía el mismo POST (F5), launch.php
-- usa esas columnas para reconocer el replay y reusar/renovar el código en
-- vez de fallar con "nonce reutilizado".
CREATE TABLE IF NOT EXISTS lti_oauth_nonces (
    consumer_key TEXT NOT NULL,
    nonce TEXT NOT NULL,
    user_id INTEGER REFERENCES users(id),
    issued_code TEXT,
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

-- Token de un solo uso para el handoff desde el launch LTI (dentro del
-- iframe de Moodle, cookie de tercero) hacia el portal admin/docente
-- (pestaña nueva, primer partido) -- ver Auth::issuePortalSsoToken() y
-- admin/sso.php. Vida corta (60s), un solo uso.
CREATE TABLE IF NOT EXISTS portal_sso_tokens (
    token TEXT PRIMARY KEY,
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

-- Nonces/state de OIDC (LTI login flow), de vida corta. user_id/issued_code
-- (ver comentario de lti_oauth_nonces arriba) cumplen el mismo rol acá para
-- el flujo LTI 1.3: reconocer el replay del mismo state/id_token y renovar
-- expires_at en vez de fallar con "state inválido o expirado".
CREATE TABLE IF NOT EXISTS lti_states (
    state TEXT PRIMARY KEY,
    nonce TEXT NOT NULL,
    lti_platform_id INTEGER NOT NULL REFERENCES lti_platforms(id),
    user_id INTEGER REFERENCES users(id),
    issued_code TEXT,
    expires_at TEXT NOT NULL
);

-- Primer diseño (agenda con 1 alumno por fila) resultó no calzar con el
-- modelo real: la agenda es una cola compartida, cualquier alumno puede
-- atender cualquier cita, y cada uno lleva su propio progreso. Se reemplaza
-- por cases/appointments/attendances más abajo. DROP seguro: en el momento
-- de este cambio estas tablas seguían vacías (nada las usaba todavía).
DROP TABLE IF EXISTS agenda;
DROP TABLE IF EXISTS patients;

-- Se reintroduce acá con diseño distinto al que se dropeó arriba: paciente
-- como entidad propia, reusada entre citas y casos (antes rut/nombre/
-- apellido/fecha_nac vivían embebidos y duplicados en cada fila de
-- appointments, sin forma de editarlos fuera del flujo de agendar). Ver
-- Db::migratePatientsIfNeeded() para instalaciones que ya tenían
-- appointments/cases sin patient_id.
CREATE TABLE IF NOT EXISTS patients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    rut TEXT NOT NULL DEFAULT '',
    nombre TEXT NOT NULL DEFAULT '',
    apellido TEXT NOT NULL DEFAULT '',
    fecha_nac TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
-- rut='' no es identificador real (citas legado sin rut) -- no debe forzar
-- unicidad entre esas filas.
CREATE UNIQUE INDEX IF NOT EXISTS idx_patients_rut ON patients(rut) WHERE rut <> '';

-- Casos clínicos (antes cases.json). id = mismo case_id que ya usa la app.
CREATE TABLE IF NOT EXISTS cases (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL,               -- JSON: Anamnesis, audiometría, etc. (definición del caso)
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    patient_id INTEGER REFERENCES patients(id)
);
CREATE INDEX IF NOT EXISTS idx_cases_patient_id ON cases(patient_id);

-- Citas de la agenda (antes cada fila de schedule.json["agenda_1"]).
-- Compartidas: cualquier alumno puede atenderlas (ver attendances abajo).
CREATE TABLE IF NOT EXISTS appointments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fecha TEXT NOT NULL DEFAULT '',   -- 'dd-MM-yy', vacío = paciente sin agendar aún
    hora TEXT NOT NULL DEFAULT '',    -- 'HH:mm'
    -- rut/nombre/apellido/fecha_nac: caché desnormalizada, NO fuente de
    -- verdad -- la identidad real vive en patients (patient_id abajo) y se
    -- escribe siempre a través de Patients::upsertByRut()/update(), que
    -- cascadea el cambio a todas las citas del mismo paciente. Se dejan acá
    -- (en vez de sacarlas y hacer JOIN en cada lectura) para no tocar
    -- sync.php/admin_dump.php/dashboard.php/student.php ni el cliente
    -- Python, que asumen estos 4 nombres de columna tal cual en el JSON.
    rut TEXT NOT NULL DEFAULT '',
    nombre TEXT NOT NULL DEFAULT '',
    apellido TEXT NOT NULL DEFAULT '',
    fecha_nac TEXT NOT NULL DEFAULT '',
    procedimiento TEXT NOT NULL DEFAULT '',
    case_id TEXT REFERENCES cases(id),
    nota_admin TEXT NOT NULL DEFAULT '',
    cancelada INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    -- NULL en las 3 = cola compartida de siempre (comportamiento sin curso).
    -- Ver Db::migrateCoursesIfNeeded() para instalaciones que ya tenían esta
    -- tabla sin estas columnas -- acá van inline para que una instalación
    -- NUEVA (install.php, que solo aplica este schema una vez) las tenga
    -- de entrada sin depender de esa migración.
    course_id INTEGER REFERENCES courses(id),
    assigned_student_id INTEGER REFERENCES users(id),
    assigned_group_id INTEGER REFERENCES student_groups(id),
    patient_id INTEGER REFERENCES patients(id)
);
CREATE INDEX IF NOT EXISTS idx_appointments_updated ON appointments (updated_at);
CREATE INDEX IF NOT EXISTS idx_appointments_fecha ON appointments (fecha);
CREATE INDEX IF NOT EXISTS idx_appointments_rut ON appointments (rut);
CREATE INDEX IF NOT EXISTS idx_appointments_patient_id ON appointments (patient_id);

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

-- Config del LLM que hace de "paciente conversacional" (chat de texto en la
-- app). Fila única (id=1) -- APARTE de app_config a propósito: app_config
-- se manda entero a todos los alumnos por sync.php/admin_dump.php, y acá
-- vive el api_key del proveedor, que no puede llegar al cliente. Solo un
-- endpoint del backend (que hace el llamado al LLM por el estudiante) debe
-- leer esta tabla.
CREATE TABLE IF NOT EXISTS llm_config (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    provider TEXT NOT NULL DEFAULT 'deepseek',
    api_key TEXT NOT NULL DEFAULT '',
    api_base_url TEXT NOT NULL DEFAULT 'https://api.deepseek.com',
    model TEXT NOT NULL DEFAULT 'deepseek-chat',
    temperature REAL NOT NULL DEFAULT 0.7,
    max_tokens INTEGER NOT NULL DEFAULT 400,
    -- Vacío = usa LlmConfig::DEFAULT_PROMPT (ver ese archivo) -- así un
    -- "restablecer" no requiere guardar el texto largo acá también.
    system_prompt_template TEXT NOT NULL DEFAULT '',
    active INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Historial de los chats "hablar con el paciente" (LlmChat) -- cada turno
-- (mensaje del alumno + respuesta del LLM) queda como dos filas, para poder
-- reconstruir/estudiar la conversación completa por atención más adelante.
-- Solo se guarda cuando el chat corre dentro de una atención real (ver
-- llm_chat.php): el "Atender (prueba)" del admin no manda appointment_id
-- justamente para no dejar rastro de sus pruebas acá.
CREATE TABLE IF NOT EXISTS llm_chat_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    appointment_id INTEGER NOT NULL REFERENCES appointments(id),
    student_id INTEGER NOT NULL REFERENCES users(id),
    case_id TEXT NOT NULL REFERENCES cases(id),
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_llm_chat_logs_appt ON llm_chat_logs (appointment_id, student_id);

-- Cursos: dos cursos con docentes y casos distintos corriendo en paralelo
-- sobre la misma instalación no eran posibles antes de esto (todo iba a un
-- fondo común). appointments.course_id/assigned_* (ver Db::migrateCoursesIfNeeded)
-- son nullable -- NULL sigue siendo la cola compartida de siempre, esto es
-- opt-in por cita.
CREATE TABLE IF NOT EXISTS courses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS course_teachers (
    course_id INTEGER NOT NULL REFERENCES courses(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    PRIMARY KEY (course_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_course_teachers_user ON course_teachers(user_id);

CREATE TABLE IF NOT EXISTS course_students (
    course_id INTEGER NOT NULL REFERENCES courses(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    PRIMARY KEY (course_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_course_students_user ON course_students(user_id);

-- Grupos dentro de un curso (p. ej. "5 alumnos citados el mismo día") --
-- para asignar un mismo paciente/cita a varios alumnos a la vez sin
-- asignarlos uno por uno.
CREATE TABLE IF NOT EXISTS student_groups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    course_id INTEGER NOT NULL REFERENCES courses(id),
    name TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_student_groups_course ON student_groups(course_id);

CREATE TABLE IF NOT EXISTS group_members (
    group_id INTEGER NOT NULL REFERENCES student_groups(id),
    user_id INTEGER NOT NULL REFERENCES users(id),
    PRIMARY KEY (group_id, user_id)
);
CREATE INDEX IF NOT EXISTS idx_group_members_user ON group_members(user_id);

-- Auditoría de acciones admin/docente (crear/eliminar usuario, restaurar
-- backup, eliminar caso, etc). Separada de action_logs -- esa tabla es el
-- timeline de comportamiento del alumno dentro de una atención (dashboard.php
-- la pinta como línea de tiempo) y mezclar ahí acciones de administración
-- ensuciaría esa vista. admin_user_id nullable a propósito: si el usuario que
-- hizo la acción se borra después, el registro de auditoría no debe
-- desaparecer con él.
CREATE TABLE IF NOT EXISTS admin_audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_user_id INTEGER REFERENCES users(id),
    admin_username TEXT NOT NULL,     -- copia al momento de la acción, sobrevive si se borra el usuario
    action TEXT NOT NULL,
    details TEXT,                     -- JSON
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_admin_audit_log_created ON admin_audit_log(created_at);

-- Rate limit de login.php: sin esto, fuerza bruta contra el password de un
-- admin era trivial (sin límite de intentos). Se cuentan fallos recientes
-- por IP (protege contra un atacante probando muchos usuarios) y por
-- username (protege una cuenta puntual de un atacante con varias IPs).
CREATE TABLE IF NOT EXISTS login_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    ip TEXT NOT NULL,
    success INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_login_attempts_ip ON login_attempts(ip, created_at);
CREATE INDEX IF NOT EXISTS idx_login_attempts_username ON login_attempts(username, created_at);

-- Rate limit de pair_exchange.php: el código de emparejamiento son 6 dígitos
-- (1M combos) con TTL de 300s -- sin límite de intentos, un atacante puede
-- automatizar requests durante esos 5 min y robar la sesión de quien esté
-- emparejando dispositivo. Solo por IP (el código no identifica usuario).
CREATE TABLE IF NOT EXISTS pair_exchange_attempts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ip TEXT NOT NULL,
    success INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_pair_exchange_attempts_ip ON pair_exchange_attempts(ip, created_at);
