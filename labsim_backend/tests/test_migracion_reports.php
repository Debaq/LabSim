<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Db.php';

/**
 * La migración del CHECK de reports con versiones ya guardadas.
 *
 * En producción (2026-10-20) fallaba con "FOREIGN KEY constraint failed":
 * renombrar reports arrastraba el REFERENCES de report_versions a la tabla
 * renombrada, y el DROP de esa chocaba con las versiones.
 */

if (!extension_loaded('pdo_sqlite')) {
    echo "  (sin pdo_sqlite: se saltan las pruebas con base)\n";
    return;
}

// En archivo y no en memoria: así se parece a producción (otra conexión
// lee lo que dejó la migración).
$archivo = tempnam(sys_get_temp_dir(), 'mig');
$abrir = static function () use ($archivo): PDO {
    $pdo = new PDO('sqlite:' . $archivo);
    $pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    $pdo->exec('PRAGMA foreign_keys = ON');
    return $pdo;
};
$pdo = $abrir();
$pdo->exec('CREATE TABLE attendances (id INTEGER PRIMARY KEY)');
$pdo->exec('CREATE TABLE reports_old (id INTEGER PRIMARY KEY, x TEXT)');
$pdo->exec("CREATE TABLE reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    attendance_id INTEGER NOT NULL REFERENCES attendances(id),
    tipo TEXT NOT NULL CHECK (tipo IN ('ABR', 'AABR', 'EOA', 'VEMP', 'ELECTROCOCLEO', 'OTOSCOPIA')),
    data TEXT NOT NULL,
    version INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (attendance_id, tipo))");
$pdo->exec('CREATE INDEX idx_reports_attendance ON reports (attendance_id)');
$pdo->exec("CREATE TABLE report_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL REFERENCES reports(id),
    version INTEGER NOT NULL, data TEXT NOT NULL, guardado_at TEXT NOT NULL,
    reemplazado_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP)");
$pdo->exec('INSERT INTO attendances VALUES (1), (2)');
$pdo->exec("INSERT INTO reports (id, attendance_id, tipo, data, version) VALUES (7, 1, 'ABR', '{}', 3), (9, 2, 'EOA', '{}', 1)");
$pdo->exec("INSERT INTO report_versions (report_id, version, data, guardado_at) VALUES (7, 1, 'a', 'x'), (7, 2, 'b', 'y')");

$error = null;
try {
    Db::migrateReportsTipos($pdo);
} catch (Throwable $e) {
    $error = $e->getMessage();
}
t_eq($error, null, 'Migra con versiones guardadas sin chocar con la clave foránea');
t_eq((int) $pdo->query('PRAGMA foreign_keys')->fetchColumn(), 1, 'Deja las claves foráneas encendidas');

$otra = $abrir();
$sql = (string) $otra->query("SELECT sql FROM sqlite_master WHERE name = 'reports'")->fetchColumn();
t_true(strpos($sql, "'MMN'") !== false && strpos($sql, "'PEALM'") !== false, 'El CHECK acepta los tipos corticales');
t_true(strpos($sql, "'ASSR'") !== false, 'El CHECK acepta el ASSR');
t_eq($otra->query('SELECT group_concat(id || ":" || version) FROM (SELECT * FROM reports ORDER BY id)')->fetchColumn(),
     '7:3,9:1', 'Conserva ids y versiones');
$rv = (string) $otra->query("SELECT sql FROM sqlite_master WHERE name = 'report_versions'")->fetchColumn();
t_true(strpos($rv, 'REFERENCES reports(id)') !== false, 'report_versions sigue apuntando a reports');
t_eq(count($otra->query('PRAGMA foreign_key_check')->fetchAll()), 0, 'Sin claves foráneas rotas');
t_eq((int) $otra->query("SELECT count(*) FROM sqlite_master WHERE name LIKE 'reports_migracion%'")->fetchColumn(),
     0, 'No queda la tabla temporal');
t_eq((int) $otra->query("SELECT count(*) FROM sqlite_master WHERE name = 'idx_reports_attendance'")->fetchColumn(),
     1, 'Recrea el índice');
t_eq((int) $otra->query("SELECT count(*) FROM sqlite_master WHERE name = 'reports_old'")->fetchColumn(),
     1, 'No toca reports_old');
$otra->exec("INSERT INTO reports (attendance_id, tipo, data) VALUES (1, 'MMN', '{}')");
$otra->exec("INSERT INTO reports (attendance_id, tipo, data) VALUES (1, 'ASSR', '{}')");
$rechazada = false;
try {
    $otra->exec("INSERT INTO report_versions (report_id, version, data, guardado_at) VALUES (999, 1, 'c', 'z')");
} catch (PDOException $e) {
    $rechazada = true;
}
t_true($rechazada, 'La clave foránea de report_versions sigue funcionando');

$error = null;
try {
    Db::migrateReportsTipos($otra);
} catch (Throwable $e) {
    $error = $e->getMessage();
}
t_eq($error, null, 'Una segunda corrida no hace nada');
$pdo = $otra = null;
@unlink($archivo);
