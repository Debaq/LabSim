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
        $row['cancelada'] = (bool) $row['cancelada'];
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

    public static function migrateCoursesIfNeeded(): void
    {
        $pdo = self::get();
        self::addColumnIfMissing($pdo, 'appointments', 'course_id', 'INTEGER REFERENCES courses(id)');
        self::addColumnIfMissing($pdo, 'appointments', 'assigned_student_id', 'INTEGER REFERENCES users(id)');
        self::addColumnIfMissing($pdo, 'appointments', 'assigned_group_id', 'INTEGER REFERENCES student_groups(id)');
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
        $pdo->exec("ALTER TABLE {$table} ADD COLUMN {$column} {$definition}");
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
