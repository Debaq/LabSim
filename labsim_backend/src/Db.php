<?php

final class Db
{
    private static ?PDO $pdo = null;

    public static function get(): PDO
    {
        if (self::$pdo === null) {
            $cfg = self::config();
            $path = $cfg['db']['path'];

            self::$pdo = new PDO('sqlite:' . $path, null, null, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                // Sin esto, este hosting devuelve columnas INTEGER como
                // string ("0"/"777" en vez de 0/777) -- json_encode las
                // manda como texto y el cliente Python las trata como
                // truthy (cualquier string no vacío es verdadero, aunque
                // diga "0"). Ya mordió dos veces (permission, cancelada);
                // esto lo corta de raíz para toda columna numérica.
                PDO::ATTR_STRINGIFY_FETCHES => false,
            ]);
            // WAL: permite varios lectores concurrentes (polling de los 14
            // clientes) mientras hay un escritor ocasional, sin bloquearse.
            self::$pdo->exec('PRAGMA journal_mode = WAL');
            self::$pdo->exec('PRAGMA foreign_keys = ON');
            self::$pdo->exec('PRAGMA busy_timeout = 5000');
        }
        return self::$pdo;
    }

    /**
     * Suelta el handle activo -- usado por Backups::restore() antes de
     * reemplazar el archivo .sqlite en disco, para que este mismo request no
     * siga con una conexión abierta al archivo viejo. Cualquier Db::get()
     * posterior en el mismo request abre una conexión nueva (ya contra el
     * archivo restaurado).
     */
    public static function closeForRestore(): void
    {
        self::$pdo = null;
    }

    public static function config(): array
    {
        $path = __DIR__ . '/../config/config.php';
        if (!is_file($path)) {
            throw new RuntimeException('Backend no instalado: corre install.php primero.');
        }
        return require $path;
    }

    /**
     * PDO_SQLITE en este hosting devuelve columnas INTEGER como string
     * ("0"/"1"), no como número/bool -- json_encode las manda entonces
     * como "0" en vez de 0, y el cliente Python las trata como truthy
     * (un string no vacío siempre es verdadero, aunque diga "0"). Mismo
     * bug que ya se dio con `permission` en Auth::userProfile(). Cast acá
     * antes de responder para cualquier endpoint que devuelva citas.
     */
    public static function castAppointment(array $row): array
    {
        $row['id'] = (int) $row['id'];
        unset($row['cancelada']);
        if (array_key_exists('patient_id', $row)) {
            $row['patient_id'] = $row['patient_id'] !== null ? (int) $row['patient_id'] : null;
        }
        return $row;
    }

    public static function castAppointments(array $rows): array
    {
        return array_map([self::class, 'castAppointment'], $rows);
    }

    /**
     * Migra un lti_platforms viejo (issuer/client_id/.. NOT NULL sin
     * default, UNIQUE inline -- de antes de soportar LTI 1.1 a la vez) al
     * shape nuevo, y repara cualquier tabla que una corrida anterior de
     * esta misma migración haya dejado apuntando a "..._old" (ver abajo).
     * Llamar SIEMPRE antes de aplicar schema.sql (CREATE TABLE IF NOT
     * EXISTS no toca una tabla que ya existe con columnas de menos).
     */
    public static function migrateLtiPlatformsIfNeeded(): void
    {
        $pdo = self::get();
        $cols = array_column($pdo->query('PRAGMA table_info(lti_platforms)')->fetchAll(), 'name');
        $needsLtiFix = $cols && !in_array('version', $cols, true);

        if (!$needsLtiFix && !self::anyTableDangling($pdo)) {
            return;
        }

        // legacy_alter_table=ON: por default (SQLite >= 3.25) un RENAME TO
        // reescribe automáticamente el REFERENCES de CUALQUIER tabla que
        // apunte a la tabla renombrada -- así fue como una corrida anterior
        // de este método (con solo foreign_keys=OFF, que NO evita esto)
        // dejó a `users` apuntando a "lti_platforms_old", y después a
        // tokens/pairing_codes/attendances/action_logs apuntando a
        // "users_old" -- ambas ya borradas, referencias colgando.
        $pdo->exec('PRAGMA legacy_alter_table = ON');
        $pdo->exec('PRAGMA foreign_keys = OFF');
        try {
            if ($needsLtiFix) {
                $pdo->exec('ALTER TABLE lti_platforms RENAME TO lti_platforms_old');
                $pdo->exec(
                    "CREATE TABLE lti_platforms (
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
                    )"
                );
                $pdo->exec(
                    "INSERT INTO lti_platforms (id, version, issuer, client_id, deployment_id, auth_login_url, auth_token_url, jwks_url, active)
                     SELECT id, '1.3', issuer, client_id, deployment_id, auth_login_url, auth_token_url, jwks_url, active FROM lti_platforms_old"
                );
                $pdo->exec('DROP TABLE lti_platforms_old');
            }

            self::repairIfDangling($pdo, 'users', "
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    role TEXT NOT NULL CHECK (role IN ('student', 'admin')),
                    username TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    password_hash TEXT,
                    lti_platform_id INTEGER REFERENCES lti_platforms(id),
                    lti_sub TEXT,
                    permission INTEGER NOT NULL DEFAULT 444,
                    modules TEXT,
                    active INTEGER NOT NULL DEFAULT 1,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (lti_platform_id, lti_sub)
                )
            ");
            self::repairIfDangling($pdo, 'lti_states', '
                CREATE TABLE lti_states (
                    state TEXT PRIMARY KEY,
                    nonce TEXT NOT NULL,
                    lti_platform_id INTEGER NOT NULL REFERENCES lti_platforms(id),
                    expires_at TEXT NOT NULL
                )
            ');
            self::repairIfDangling($pdo, 'tokens', '
                CREATE TABLE tokens (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    last_seen_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ');
            self::repairIfDangling($pdo, 'pairing_codes', '
                CREATE TABLE pairing_codes (
                    code TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    expires_at TEXT NOT NULL,
                    used INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ');
            self::repairIfDangling($pdo, 'attendances', "
                CREATE TABLE attendances (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    appointment_id INTEGER NOT NULL REFERENCES appointments(id),
                    student_id INTEGER NOT NULL REFERENCES users(id),
                    estado TEXT NOT NULL CHECK (estado IN ('atendiendo', 'atendido', 'no_show')),
                    nota TEXT NOT NULL DEFAULT '',
                    hora_real TEXT NOT NULL DEFAULT '',
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (appointment_id, student_id)
                )
            ");
            self::repairIfDangling($pdo, 'action_logs', '
                CREATE TABLE action_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id),
                    client_ts TEXT NOT NULL,
                    action TEXT NOT NULL,
                    payload TEXT,
                    received_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                )
            ');
        } finally {
            $pdo->exec('PRAGMA foreign_keys = ON');
            $pdo->exec('PRAGMA legacy_alter_table = OFF');
        }
    }

    /**
     * Agrega user_id/issued_code a lti_states y lti_oauth_nonces si faltan
     * -- instalaciones de antes de soportar el replay del launch (F5 en la
     * página de código). CREATE TABLE IF NOT EXISTS de schema.sql no toca
     * columnas de una tabla que ya existe, por eso el ALTER TABLE acá.
     */
    public static function migrateLtiReplayColumnsIfNeeded(): void
    {
        $pdo = self::get();
        self::addColumnIfMissing($pdo, 'lti_states', 'user_id', 'INTEGER REFERENCES users(id)');
        self::addColumnIfMissing($pdo, 'lti_states', 'issued_code', 'TEXT');
        self::addColumnIfMissing($pdo, 'lti_oauth_nonces', 'user_id', 'INTEGER REFERENCES users(id)');
        self::addColumnIfMissing($pdo, 'lti_oauth_nonces', 'issued_code', 'TEXT');
    }

    /**
     * course_id/assigned_student_id/assigned_group_id en appointments --
     * instalaciones de antes de soportar cursos. Nullable: NULL en las 3 es
     * la cola compartida de siempre (ver comentario en sql/schema.sql sobre
     * `courses`), así que agregar la columna no cambia el comportamiento de
     * ninguna cita ya existente.
     */
    /**
     * Agrega oirs_prompt_template a llm_config -- instalaciones de antes de
     * que existiera el evaluador OIRS (ver OirsEvaluator.php). A diferencia
     * de migratePatientColumnsIfNeeded, esto SÍ debe llamarse DESPUÉS del
     * exec de schema.sql: una instalación vieja puede no tener la tabla
     * llm_config todavía (se agregó recién con el chat), y PRAGMA
     * table_info() sobre una tabla inexistente no avisa que falta -- el
     * ALTER TABLE de abajo fallaría con "no such table" si llm_config no
     * existe aún. El exec la crea primero si hace falta.
     */
    public static function migrateLlmOirsPromptIfNeeded(): void
    {
        self::addColumnIfMissing(self::get(), 'llm_config', 'oirs_prompt_template', "TEXT NOT NULL DEFAULT ''");
    }

    /**
     * Agrega anamnesis_max_tokens a llm_config -- instalaciones de antes de
     * que el borrador de anamnesis tuviera presupuesto propio. Mismo motivo
     * que migrateLlmOirsPromptIfNeeded.
     */
    public static function migrateLlmAnamnesisTokensIfNeeded(): void
    {
        self::addColumnIfMissing(self::get(), 'llm_config', 'anamnesis_max_tokens', 'INTEGER NOT NULL DEFAULT 6000');
        self::addColumnIfMissing(self::get(), 'llm_config', 'anamnesis_model', "TEXT NOT NULL DEFAULT ''");
    }

    /**
     * Agrega sala_prompt_template a llm_config y las columnas de hablante a
     * llm_chat_logs -- instalaciones anteriores a que el paciente pudiera
     * venir acompañado (ver Sala.php). Mismo motivo y mismo orden de
     * llamada que migrateLlmOirsPromptIfNeeded: después del exec de
     * schema.sql.
     */
    public static function migrateSalaIfNeeded(): void
    {
        $pdo = self::get();
        self::migrateLlmSalaPromptIfNeeded();
        self::addColumnIfMissing($pdo, 'llm_chat_logs', 'speaker_id', "TEXT NOT NULL DEFAULT ''");
        self::addColumnIfMissing($pdo, 'llm_chat_logs', 'speaker_label', "TEXT NOT NULL DEFAULT ''");
    }

    /**
     * Solo la columna de la plantilla: es lo único que necesita
     * LlmConfig::save(), que puede correr antes de que nadie haya aplicado
     * el schema.
     */
    public static function migrateLlmSalaPromptIfNeeded(): void
    {
        self::addColumnIfMissing(self::get(), 'llm_config', 'sala_prompt_template', "TEXT NOT NULL DEFAULT ''");
    }

    /**
     * La tabla de consumo (ver LlmUsage.php) y las tarifas en llm_config --
     * instalaciones anteriores a que se llevara la cuenta de lo que gasta
     * la API.
     *
     * A diferencia del resto de migrateLlm*, esta CREA la tabla en vez de
     * esperar a schema.sql: la llama LlmUsage::registrar() en el camino del
     * chat, que corre mucho antes de que alguien pase por "Aplicar schema",
     * y sin la tabla no se anotaría nada durante todo ese tiempo. El CREATE
     * es idéntico al de schema.sql (IF NOT EXISTS en los dos lados, así que
     * corran en el orden que corran no se pisan).
     */
    public static function migrateLlmUsageIfNeeded(): void
    {
        $pdo = self::get();
        $pdo->exec(
            "CREATE TABLE IF NOT EXISTS llm_usage (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tarea TEXT NOT NULL DEFAULT '',
                model TEXT NOT NULL DEFAULT '',
                provider TEXT NOT NULL DEFAULT '',
                course_id INTEGER,
                user_id INTEGER,
                cache_hit INTEGER NOT NULL DEFAULT 0,
                cache_miss INTEGER NOT NULL DEFAULT 0,
                completion INTEGER NOT NULL DEFAULT 0,
                razonamiento INTEGER NOT NULL DEFAULT 0,
                total INTEGER NOT NULL DEFAULT 0,
                ventana TEXT NOT NULL DEFAULT 'peak',
                ok INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"
        );
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_llm_usage_created ON llm_usage(created_at)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_llm_usage_course ON llm_usage(course_id, created_at)');
        self::migrateLlmPricesIfNeeded();
    }

    /**
     * Solo las tarifas: es lo único que necesita LlmConfig::save(), que
     * puede correr antes de que nadie haya aplicado el schema (mismo caso
     * que migrateLlmSalaPromptIfNeeded).
     */
    public static function migrateLlmPricesIfNeeded(): void
    {
        $pdo = self::get();
        // llm_config puede no existir todavía (instalación recién creada, o
        // schema.sql sin aplicar): PRAGMA table_info sobre una tabla que no
        // está no avisa, y el ALTER de abajo moriría con "no such table".
        // Se sale en silencio -- schema.sql la crea ya con las columnas.
        if (!$pdo->query("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'llm_config'")->fetch()) {
            return;
        }
        self::addColumnIfMissing($pdo, 'llm_config', 'price_cache_hit', 'REAL NOT NULL DEFAULT 0');
        self::addColumnIfMissing($pdo, 'llm_config', 'price_cache_miss', 'REAL NOT NULL DEFAULT 0');
        self::addColumnIfMissing($pdo, 'llm_config', 'price_output', 'REAL NOT NULL DEFAULT 0');
    }

    /**
     * Agrega historia_clinica a patients -- instalaciones de antes de que
     * esa columna existiera. CREATE TABLE IF NOT EXISTS de schema.sql no
     * toca columnas de una tabla que ya existe, por eso el ALTER TABLE acá.
     */
    public static function migratePatientHistoriaClinicaIfNeeded(): void
    {
        self::addColumnIfMissing(self::get(), 'patients', 'historia_clinica', "TEXT NOT NULL DEFAULT ''");
    }

    /**
     * Agrega comentario_docente a patients -- instalaciones de antes de que
     * esa columna existiera. Mismo motivo que migratePatientHistoriaClinicaIfNeeded.
     */
    public static function migratePatientComentarioDocenteIfNeeded(): void
    {
        self::addColumnIfMissing(self::get(), 'patients', 'comentario_docente', "TEXT NOT NULL DEFAULT ''");
    }

    /**
     * Agrega la autoría de la ficha a cases (created_at/created_by/updated_by)
     * -- instalaciones de antes de que existieran. El created_at se agrega con
     * DEFAULT '' y no CURRENT_TIMESTAMP: SQLite rechaza un default no constante
     * en ALTER TABLE ADD COLUMN ("Cannot add a column with non-constant
     * default"), así que el valor de las filas viejas lo pone el backfill de
     * abajo. Todo INSERT de cases escribe created_at explícito, así que el
     * default nunca se usa en una fila nueva.
     *
     * Backfill: created_at = updated_at (lo más cercano a la fecha de creación
     * que hay), y el autor sale de admin_audit_log, que ya venía registrando
     * case_create/case_update con el case_id en details -- primer case_create
     * para created_by, último case_create/case_update para updated_by. Las
     * filas que no aparecen en el log (creadas desde la app por
     * api/case_upsert.php, que no audita) quedan con autor NULL: patients.php
     * las muestra como "—", no se inventa un autor.
     */
    public static function migrateCaseAuthorshipIfNeeded(): void
    {
        $pdo = self::get();
        $cols = array_column($pdo->query('PRAGMA table_info(cases)')->fetchAll(), 'name');
        $yaEstaba = in_array('created_by', $cols, true);
        self::addColumnIfMissing($pdo, 'cases', 'created_at', "TEXT NOT NULL DEFAULT ''");
        self::addColumnIfMissing($pdo, 'cases', 'created_by', 'INTEGER REFERENCES users(id)');
        self::addColumnIfMissing($pdo, 'cases', 'updated_by', 'INTEGER REFERENCES users(id)');
        $pdo->exec("UPDATE cases SET created_at = updated_at WHERE created_at = ''");
        if ($yaEstaba) {
            // Segunda corrida: no re-adivinar autores desde el log, ya
            // están escritos (y pisar lo real con lo adivinado sería peor).
            return;
        }
        self::backfillCaseAuthorshipFromAuditLog($pdo);
    }

    /** Autores de cases.created_by/updated_by deducidos de admin_audit_log. */
    private static function backfillCaseAuthorshipFromAuditLog(PDO $pdo): void
    {
        $rows = $pdo->query(
            "SELECT admin_user_id, action, details FROM admin_audit_log
             WHERE action IN ('case_create', 'case_update') AND admin_user_id IS NOT NULL
             ORDER BY id ASC"
        )->fetchAll();

        $creadores = [];   // case_id => user_id del primer case_create
        $editores = [];    // case_id => user_id del último evento
        foreach ($rows as $row) {
            $details = json_decode((string) $row['details'], true);
            $caseId = is_array($details) ? trim((string) ($details['case_id'] ?? '')) : '';
            if ($caseId === '') {
                continue;
            }
            $userId = (int) $row['admin_user_id'];
            if ($row['action'] === 'case_create' && !isset($creadores[$caseId])) {
                $creadores[$caseId] = $userId;
            }
            $editores[$caseId] = $userId;
        }
        if (!$creadores && !$editores) {
            return;
        }

        $pdo->beginTransaction();
        try {
            $stmtCreado = $pdo->prepare('UPDATE cases SET created_by = ? WHERE id = ? AND created_by IS NULL');
            foreach ($creadores as $caseId => $userId) {
                $stmtCreado->execute([$userId, $caseId]);
            }
            $stmtEditado = $pdo->prepare('UPDATE cases SET updated_by = ? WHERE id = ? AND updated_by IS NULL');
            foreach ($editores as $caseId => $userId) {
                $stmtEditado->execute([$userId, $caseId]);
            }
            $pdo->commit();
        } catch (Throwable $e) {
            $pdo->rollBack();
            throw $e;
        }
    }

    public static function migrateCoursesIfNeeded(): void
    {
        $pdo = self::get();
        self::addColumnIfMissing($pdo, 'appointments', 'course_id', 'INTEGER REFERENCES courses(id)');
        self::addColumnIfMissing($pdo, 'appointments', 'assigned_student_id', 'INTEGER REFERENCES users(id)');
        self::addColumnIfMissing($pdo, 'appointments', 'assigned_group_id', 'INTEGER REFERENCES student_groups(id)');
    }

    /**
     * Docentes que quedaron en el roster de alumnos: LTI crea toda cuenta
     * como role='student' y el ascenso a docente (role='admin', permission
     * 555) es posterior, así que su fila vieja de course_students nunca se
     * limpiaba. Consecuencias: Auth::resolveModules los buscaba en
     * course_teachers y les devolvía modules=[] (pestañas visibles, ningún
     * equipo), y Courses::rosterUserIds los contaba como alumnos del curso.
     * Esto los mueve de course_students a course_teachers, curso por curso.
     * El admin completo (777) no se toca: ve todo sin restricción y su
     * matrícula, si la tiene, es deliberada (probar el flujo de alumno).
     * Devuelve cuántas filas movió (0 si no había nada que arreglar).
     */
    public static function migrateTeacherRosterIfNeeded(): int
    {
        $pdo = self::get();
        $sel = "SELECT cs.course_id, cs.user_id FROM course_students cs
                JOIN users u ON u.id = cs.user_id
                WHERE u.role = 'admin' AND u.permission <> 777";
        $rows = $pdo->query($sel)->fetchAll();
        if (!$rows) {
            return 0;
        }
        $pdo->beginTransaction();
        try {
            $ins = $pdo->prepare('INSERT OR IGNORE INTO course_teachers (course_id, user_id) VALUES (?, ?)');
            $del = $pdo->prepare('DELETE FROM course_students WHERE course_id = ? AND user_id = ?');
            foreach ($rows as $row) {
                $ins->execute([(int) $row['course_id'], (int) $row['user_id']]);
                $del->execute([(int) $row['course_id'], (int) $row['user_id']]);
            }
            $pdo->commit();
        } catch (Throwable $e) {
            $pdo->rollBack();
            throw $e;
        }
        return count($rows);
    }

    /**
     * Agrega lti_platform_id/context_id a pairing_codes/tokens -- instalaciones
     * de antes de que la sesión guardara el contexto LTI de origen (ver
     * comentario de esas columnas en sql/schema.sql). NULL en ambas para
     * cualquier fila ya existente no cambia nada: sigue resolviendo sin
     * curso asociado, igual que hoy.
     */
    public static function migrateSessionLtiContextIfNeeded(): void
    {
        $pdo = self::get();
        self::addColumnIfMissing($pdo, 'pairing_codes', 'lti_platform_id', 'INTEGER REFERENCES lti_platforms(id)');
        self::addColumnIfMissing($pdo, 'pairing_codes', 'context_id', 'TEXT');
        self::addColumnIfMissing($pdo, 'tokens', 'lti_platform_id', 'INTEGER REFERENCES lti_platforms(id)');
        self::addColumnIfMissing($pdo, 'tokens', 'context_id', 'TEXT');
        self::addColumnIfMissing($pdo, 'lti_states', 'context_id', 'TEXT');
        self::addColumnIfMissing($pdo, 'lti_oauth_nonces', 'context_id', 'TEXT');
    }

    /**
     * Curso al que matricula una clave LTI por sí sola (ver el comentario de
     * lti_platforms.default_course_id en schema.sql).
     *
     * La llaman Lti::defaultCourseFor/setDefaultCourse, que corren en el
     * camino del launch: sin esto, una instalación que todavía no pasó por
     * "Aplicar schema" reventaría con "no such column: default_course_id" en
     * cada entrada desde Moodle. Es idempotente y barata (un PRAGMA).
     */
    public static function migrateLtiDefaultCourseIfNeeded(): void
    {
        // Una vez por request: esto cuelga del camino del launch y de cada
        // emisión de token, y el PRAGMA de addColumnIfMissing no hace falta
        // repetirlo dentro de la misma corrida.
        static $hecho = false;
        if ($hecho) {
            return;
        }
        $hecho = true;
        self::addColumnIfMissing(self::get(), 'lti_platforms', 'default_course_id', 'INTEGER REFERENCES courses(id)');
    }

    /**
     * Reconstruye app_config para soportar override por curso (ver comentario
     * de esa tabla en sql/schema.sql). La PK vieja era (k) solo: un simple
     * ALTER TABLE ADD COLUMN course_id no alcanza porque esa PK seguiría
     * rechazando una fila override que comparte key con la fila global -- hay
     * que reconstruir la tabla completa. course_id NULL para todo lo
     * existente no cambia nada (sigue siendo el default global de siempre).
     * Debe llamarse ANTES de aplicar schema.sql: ese archivo trae
     * `CREATE UNIQUE INDEX ... ON app_config(k, course_id) ...`, que en una
     * base ya existente falla con "no such column: course_id" si esta
     * migración no corrió antes (mismo motivo que migratePatientColumnsIfNeeded).
     */
    public static function migrateAppConfigCourseIdIfNeeded(): void
    {
        $pdo = self::get();
        $cols = array_column($pdo->query('PRAGMA table_info(app_config)')->fetchAll(), 'name');
        if (in_array('course_id', $cols, true)) {
            return;
        }
        $pdo->exec('ALTER TABLE app_config RENAME TO app_config_old');
        $pdo->exec(
            'CREATE TABLE app_config (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                k TEXT NOT NULL,
                course_id INTEGER REFERENCES courses(id),
                v TEXT NOT NULL,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )'
        );
        $pdo->exec(
            'INSERT INTO app_config (k, course_id, v, updated_at)
             SELECT k, NULL, v, updated_at FROM app_config_old'
        );
        $pdo->exec('DROP TABLE app_config_old');
    }

    /**
     * Amplía el CHECK de reports.tipo para aceptar 'OTOSCOPIA' (informe de
     * otoscopia por cuadrantes que sube el alumno desde el módulo de
     * otoscopia). SQLite no permite modificar un CHECK con ALTER TABLE:
     * hay que reconstruir la tabla y copiar las filas, como en
     * migrateAppConfigCourseIdIfNeeded. Debe llamarse ANTES de aplicar
     * schema.sql, que recrea el índice de la tabla.
     */
    public static function migrateReportsOtoscopiaIfNeeded(): void
    {
        $pdo = self::get();
        $stmt = $pdo->prepare("SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'reports'");
        $stmt->execute();
        $sql = (string) $stmt->fetchColumn();
        // Tabla todavía inexistente (instalación nueva): la crea schema.sql
        // ya con el CHECK nuevo, no hay nada que migrar.
        if ($sql === '' || strpos($sql, 'OTOSCOPIA') !== false) {
            return;
        }
        $pdo->exec('ALTER TABLE reports RENAME TO reports_old');
        $pdo->exec(
            "CREATE TABLE reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                attendance_id INTEGER NOT NULL REFERENCES attendances(id),
                tipo TEXT NOT NULL CHECK (tipo IN ('ABR', 'EOA', 'VEMP', 'ELECTROCOCLEO', 'OTOSCOPIA')),
                data TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (attendance_id, tipo)
            )"
        );
        // Se conservan los id: el PDF y las imágenes en disco se nombran a
        // partir de reports.id (ver ReportFile::pdfPath()), reasignarlos
        // dejaría cada informe apuntando a los archivos de otro.
        $pdo->exec(
            'INSERT INTO reports (id, attendance_id, tipo, data, created_at, updated_at)
             SELECT id, attendance_id, tipo, data, created_at, updated_at FROM reports_old'
        );
        $pdo->exec('DROP TABLE reports_old');
    }

    /**
     * Agrega users.is_demo/courses.demo_user_id -- instalaciones de antes
     * del estudiante demo por curso (ver comentarios de esas columnas en
     * sql/schema.sql). 0/NULL respectivamente no cambia nada de lo ya
     * existente: ningún usuario/curso queda marcado como demo solo.
     */
    /**
     * Agrega users.username_locked -- instalaciones de antes de que el
     * docente pudiera elegir su usuario de login en admin/perfil.php.
     */
    public static function migrateProfileLoginIfNeeded(): void
    {
        self::addColumnIfMissing(self::get(), 'users', 'username_locked', 'INTEGER NOT NULL DEFAULT 0');
    }

    /**
     * Índice único de users.username insensible a mayúsculas. Si la base ya
     * trae duplicados que solo difieren en el caso, el CREATE INDEX falla:
     * se detectan antes para poder decir cuáles son, porque arreglarlos es
     * una decisión (a cuál de las dos cuentas renombrar) y no algo que esta
     * migración pueda tomar sola.
     */
    public static function migrateUsernameNoCaseIfNeeded(): void
    {
        $pdo = self::get();
        // Instalación nueva: users todavía no existe (la crea schema.sql, con
        // el índice incluido). Va antes del exec de schema.sql a propósito:
        // ahí el CREATE INDEX fallaría con un error crudo de SQLite en una
        // base que ya trae duplicados, en vez del aviso de abajo.
        $tablas = $pdo->query("SELECT name FROM sqlite_master WHERE type = 'table' AND name = 'users'")->fetchAll();
        if (!$tablas) {
            return;
        }
        $duplicados = $pdo->query(
            'SELECT group_concat(username, " / ") AS nombres FROM users
             GROUP BY lower(username) HAVING COUNT(*) > 1'
        )->fetchAll();
        if ($duplicados) {
            throw new RuntimeException(
                'Hay usuarios que solo se diferencian por mayúsculas y no pueden convivir: '
                . implode(' | ', array_column($duplicados, 'nombres'))
                . '. Renombra uno de cada par en Usuarios y vuelve a aplicar el schema.'
            );
        }
        $pdo->exec('CREATE UNIQUE INDEX IF NOT EXISTS idx_users_username_nocase ON users (username COLLATE NOCASE)');
    }

    public static function migrateDemoStudentIfNeeded(): void
    {
        $pdo = self::get();
        self::addColumnIfMissing($pdo, 'users', 'is_demo', 'INTEGER NOT NULL DEFAULT 0');
        self::addColumnIfMissing($pdo, 'courses', 'demo_user_id', 'INTEGER REFERENCES users(id)');
    }

    /**
     * Solo agrega patient_id a appointments/cases (sin tocar `patients` ni
     * backfillear nada) -- instalaciones de antes de que esa columna
     * existiera. Llamar SIEMPRE antes de aplicar schema.sql: ese archivo
     * trae `CREATE INDEX ... ON appointments (patient_id)` / `ON cases
     * (patient_id)`, que en una base ya existente fallan con "no such
     * column: patient_id" si la columna no está puesta todavía (mismo
     * motivo que migrateLtiReplayColumnsIfNeeded se llama antes del exec).
     */
    public static function migratePatientColumnsIfNeeded(): void
    {
        $pdo = self::get();
        self::addColumnIfMissing($pdo, 'appointments', 'patient_id', 'INTEGER REFERENCES patients(id)');
        self::addColumnIfMissing($pdo, 'cases', 'patient_id', 'INTEGER REFERENCES patients(id)');
    }

    /**
     * Backfillea `patients` a partir de datos legado -- instalaciones de
     * antes de que esa tabla existiera (ver sql/schema.sql). Requiere que
     * `patients` ya exista (la crea el exec de schema.sql) y que
     * appointments/cases ya tengan patient_id (ver
     * migratePatientColumnsIfNeeded, llamar ANTES de aplicar schema.sql).
     * Un patient por cada rut distinto ya usado en appointments (si el mismo
     * rut tiene nombre/apellido/fecha_nac inconsistentes entre citas viejas,
     * gana la fila con id más alto -- la más reciente), enlaza cada cita a su
     * patient, y de ahí enlaza cases.patient_id (primero desde el
     * paciente_snapshot de casos huérfanos, después espejando el patient_id
     * de la cita viva más reciente de cada caso). Filas con rut='' quedan sin
     * patient_id -- no hay forma confiable de identificarlas como la misma
     * persona, se resuelven la primera vez que alguien las edite a mano.
     */
    public static function migratePatientsIfNeeded(): void
    {
        $pdo = self::get();
        self::migratePatientColumnsIfNeeded();

        $pdo->beginTransaction();
        try {
            $rows = $pdo->query(
                "SELECT id, rut, nombre, apellido, fecha_nac FROM appointments WHERE rut <> '' AND patient_id IS NULL ORDER BY id ASC"
            )->fetchAll();

            $patientIdByRut = [];
            foreach ($rows as $row) {
                $rut = $row['rut'];
                if (!isset($patientIdByRut[$rut])) {
                    $stmt = $pdo->prepare('SELECT id FROM patients WHERE rut = ?');
                    $stmt->execute([$rut]);
                    $existing = $stmt->fetchColumn();
                    $patientIdByRut[$rut] = $existing !== false ? (int) $existing : null;
                }
                if ($patientIdByRut[$rut] === null) {
                    $pdo->prepare(
                        'INSERT INTO patients (rut, nombre, apellido, fecha_nac) VALUES (?, ?, ?, ?)'
                    )->execute([$rut, $row['nombre'], $row['apellido'], $row['fecha_nac']]);
                    $patientIdByRut[$rut] = (int) $pdo->lastInsertId();
                } else {
                    // Fila más reciente de este rut (ORDER BY id ASC, se
                    // pisa en cada vuelta) -- deja sus datos como los
                    // vigentes del patient.
                    $pdo->prepare(
                        'UPDATE patients SET nombre = ?, apellido = ?, fecha_nac = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
                    )->execute([$row['nombre'], $row['apellido'], $row['fecha_nac'], $patientIdByRut[$rut]]);
                }
                $pdo->prepare('UPDATE appointments SET patient_id = ? WHERE id = ?')
                    ->execute([$patientIdByRut[$rut], $row['id']]);
            }

            // Casos huérfanos (sin cita viva) que solo tienen paciente_snapshot.
            $orphanCases = $pdo->query(
                "SELECT id, data FROM cases WHERE patient_id IS NULL"
            )->fetchAll();
            foreach ($orphanCases as $case) {
                $data = json_decode($case['data'] ?? '', true);
                $snapshot = is_array($data) ? ($data['paciente_snapshot'] ?? null) : null;
                $rut = is_array($snapshot) ? (string) ($snapshot['rut'] ?? '') : '';
                if ($rut === '') {
                    continue;
                }
                if (!isset($patientIdByRut[$rut])) {
                    $stmt = $pdo->prepare('SELECT id FROM patients WHERE rut = ?');
                    $stmt->execute([$rut]);
                    $existing = $stmt->fetchColumn();
                    if ($existing !== false) {
                        $patientIdByRut[$rut] = (int) $existing;
                    } else {
                        $pdo->prepare(
                            'INSERT INTO patients (rut, nombre, apellido, fecha_nac) VALUES (?, ?, ?, ?)'
                        )->execute([
                            $rut,
                            (string) ($snapshot['nombre'] ?? ''),
                            (string) ($snapshot['apellido'] ?? ''),
                            (string) ($snapshot['fecha_nac'] ?? ''),
                        ]);
                        $patientIdByRut[$rut] = (int) $pdo->lastInsertId();
                    }
                }
                $pdo->prepare('UPDATE cases SET patient_id = ? WHERE id = ?')
                    ->execute([$patientIdByRut[$rut], $case['id']]);
            }

            // Resto de los casos: espejar desde su cita viva más reciente.
            $pdo->exec(
                "UPDATE cases SET patient_id = (
                    SELECT a.patient_id FROM appointments a
                    WHERE a.case_id = cases.id AND a.patient_id IS NOT NULL
                    ORDER BY a.id DESC LIMIT 1
                ) WHERE patient_id IS NULL"
            );

            $pdo->commit();
        } catch (Throwable $e) {
            $pdo->rollBack();
            throw $e;
        }
    }

    private static function addColumnIfMissing(PDO $pdo, string $table, string $column, string $definition): void
    {
        $cols = array_column($pdo->query("PRAGMA table_info({$table})")->fetchAll(), 'name');
        if (in_array($column, $cols, true)) {
            return;
        }
        $sql = "ALTER TABLE {$table} ADD COLUMN {$column} {$definition}";
        try {
            $pdo->exec($sql);
        } catch (PDOException $e) {
            // "database table is locked" (SQLITE_LOCKED, error 6): esta misma
            // conexión tiene un cursor abierto sobre la tabla -- basta con un
            // SELECT del que se leyó una fila y no se agotó (fetch() sin
            // fetchAll()) para que el motor rechace el cambio de esquema. Una
            // conexión limpia no arrastra esos cursores; en WAL un lector no
            // bloquea a este escritor.
            if (!self::esBloqueoDeTabla($e)) {
                throw $e;
            }
            $otra = self::nuevaConexion();
            $otra->exec($sql);
        }
    }

    /** ¿La excepción es SQLITE_LOCKED/SQLITE_BUSY y no un error real de SQL? */
    private static function esBloqueoDeTabla(PDOException $e): bool
    {
        $codigo = (int) ($e->errorInfo[1] ?? 0);
        return $codigo === 5 || $codigo === 6;
    }

    /**
     * Conexión nueva al mismo archivo, con los mismos PRAGMA. No reemplaza a
     * self::$pdo -- es para operaciones que no pueden convivir con los
     * cursores abiertos de la conexión del request (ver addColumnIfMissing).
     */
    private static function nuevaConexion(): PDO
    {
        $cfg = self::config();
        $pdo = new PDO('sqlite:' . $cfg['db']['path'], null, null, [
            PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
            PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
            PDO::ATTR_STRINGIFY_FETCHES => false,
        ]);
        $pdo->exec('PRAGMA foreign_keys = ON');
        $pdo->exec('PRAGMA busy_timeout = 15000');
        return $pdo;
    }

    private static function anyTableDangling(PDO $pdo): bool
    {
        foreach (['users', 'lti_states', 'tokens', 'pairing_codes', 'attendances', 'action_logs'] as $table) {
            if (self::isDangling($pdo, $table)) {
                return true;
            }
        }
        return false;
    }

    private static function isDangling(PDO $pdo, string $table): bool
    {
        $sql = (string) $pdo->query("SELECT sql FROM sqlite_master WHERE type='table' AND name='{$table}'")->fetchColumn();
        return $sql !== '' && strpos($sql, '_old') !== false;
    }

    /** Si $table quedó con un REFERENCES colgando a "..._old", la recrea con $createSql (que debe tener las mismas columnas). */
    private static function repairIfDangling(PDO $pdo, string $table, string $createSql): void
    {
        if (!self::isDangling($pdo, $table)) {
            return;
        }
        $tmp = "{$table}_fixtmp";
        $pdo->exec("ALTER TABLE {$table} RENAME TO {$tmp}");
        $pdo->exec($createSql);
        $pdo->exec("INSERT INTO {$table} SELECT * FROM {$tmp}");
        $pdo->exec("DROP TABLE {$tmp}");
    }
}
