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
