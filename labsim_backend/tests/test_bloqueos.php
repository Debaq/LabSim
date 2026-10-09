<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Bloqueos.php';

/**
 * Bloquear una cuenta: corta sus sesiones, no la deja volver a entrar y
 * deja quién, cuándo y por qué (Bloqueos, admin/tokens.php, users.php).
 */

$auth = (string) file_get_contents(__DIR__ . '/../src/Auth.php');
t_true(strpos($auth, 'throw new CuentaBloqueada()') !== false
       && substr_count($auth, 'throw new CuentaBloqueada()') === 2,
       'Login con contraseña y canje del código de Moodle rechazan la cuenta bloqueada');
t_true(strpos($auth, "Response::error(Bloqueos::MENSAJE, 403, ['codigo' => Bloqueos::CODIGO])") !== false,
       'Un token de una cuenta bloqueada responde 403 con el código');
foreach (['admin_login.php', 'pair_exchange.php'] as $api) {
    $src = (string) file_get_contents(__DIR__ . '/../public/api/' . $api);
    t_true(strpos($src, 'catch (CuentaBloqueada $e)') !== false, "{$api} responde cuenta bloqueada");
}

if (!extension_loaded('pdo_sqlite')) {
    echo "  (sin pdo_sqlite: se saltan las pruebas con base)\n";
    return;
}

// Base en memoria. AdminAudit escribe con Db::get() (no está acá: falla
// callado, como en producción si la auditoría se rompe); el registro que lee
// listar() se siembra a mano.
$pdo = new PDO('sqlite::memory:');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->exec("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, display_name TEXT, role TEXT,
            active INTEGER NOT NULL DEFAULT 1, updated_at TEXT)");
$pdo->exec("CREATE TABLE tokens (token TEXT PRIMARY KEY, user_id INTEGER, created_at TEXT, last_seen_at TEXT)");
$pdo->exec("CREATE TABLE admin_audit_log (id INTEGER PRIMARY KEY AUTOINCREMENT, admin_user_id INTEGER,
            admin_username TEXT, action TEXT, details TEXT, created_at TEXT DEFAULT CURRENT_TIMESTAMP)");
$pdo->exec("INSERT INTO users (id, username, display_name, role) VALUES
            (1,'admin','Admin','admin'), (5,'ana@x','Ana','student'), (50,'beto@x','Beto','student')");
$pdo->exec("INSERT INTO tokens VALUES ('t1',5,datetime('now'),datetime('now')), ('t2',5,datetime('now'),datetime('now')),
            ('t3',50,datetime('now'),datetime('now'))");
$admin = ['id' => 1, 'username' => 'admin'];

$err = null;
try {
    Bloqueos::bloquear($pdo, $admin, 1, '');
} catch (InvalidArgumentException $e) {
    $err = $e->getMessage();
}
t_eq($err, 'No puedes bloquear tu propia cuenta.', 'No se bloquea a sí mismo');

t_eq(Bloqueos::bloquear($pdo, $admin, 5, 'copió el examen'), 2, 'Bloquear corta sus 2 sesiones');
t_true(Bloqueos::estaBloqueado($pdo, 5), 'Queda bloqueada');
t_true(!Bloqueos::estaBloqueado($pdo, 50), 'La otra cuenta no');
t_eq((int) $pdo->query("SELECT COUNT(*) FROM tokens WHERE user_id = 50")->fetchColumn(), 1,
     'Las sesiones de otros siguen');

// Lo que dejaría AdminAudit (y uno de user_id 50 para ver que no se mezclan).
$pdo->exec("INSERT INTO admin_audit_log (admin_user_id, admin_username, action, details) VALUES
            (1, 'admin', 'user_block', '{\"user_id\":5,\"username\":\"ana@x\",\"motivo\":\"copió el examen\"}'),
            (1, 'admin', 'user_block', '{\"user_id\":50,\"username\":\"beto@x\",\"motivo\":\"otro\"}')");
$lista = Bloqueos::listar($pdo);
t_eq(array_column($lista, 'username'), ['ana@x'], 'Lista solo las bloqueadas');
t_eq($lista[0]['motivo'], 'copió el examen', 'Con su motivo (no el de user_id 50)');
t_eq($lista[0]['bloqueado_por'], 'admin', 'Y quién la bloqueó');

Bloqueos::desbloquear($pdo, $admin, 5);
t_true(!Bloqueos::estaBloqueado($pdo, 5), 'Desbloquear la deja entrar de nuevo');
t_eq(Bloqueos::listar($pdo), [], 'Ya no hay bloqueadas');
