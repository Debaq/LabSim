<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Tokens.php';

/**
 * Sesiones de la app en el panel (admin/tokens.php): buscar, filtrar y
 * revocar de a una, las marcadas o todas las del filtro.
 */

$f = Tokens::filtros(['q' => '  ana ', 'rol' => 'root', 'actividad' => 'hoy', 'otro' => 'x']);
t_eq($f, ['q' => 'ana', 'rol' => '', 'actividad' => 'hoy'], 'Filtros saneados: rol desconocido fuera');
t_eq(Tokens::where(Tokens::filtros([])), ['1', []], 'Sin filtro: todas');
[$w, $p] = Tokens::where(Tokens::filtros(['q' => '50%_x']));
t_eq($p[0], '%50\\%\\_x%', 'Comodines de LIKE escapados en la búsqueda');

if (!extension_loaded('pdo_sqlite')) {
    echo "  (sin pdo_sqlite: se saltan las pruebas con base)\n";
    return;
}

$pdo = new PDO('sqlite::memory:');
$pdo->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
$pdo->exec("CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, display_name TEXT, role TEXT)");
$pdo->exec("CREATE TABLE tokens (token TEXT PRIMARY KEY, user_id INTEGER, created_at TEXT,
            last_seen_at TEXT)");
$pdo->exec("INSERT INTO users VALUES (1,'admin','Admin','admin'), (2,'ana@x','Ana Paz','student'),
            (3,'beto@x','Beto','student')");
$ahora = "datetime('now')";
$viejo = "datetime('now','-30 days')";
$pdo->exec("INSERT INTO tokens VALUES
    ('aaaaaaaaadmin001', 1, $ahora, $ahora), ('aaaaaaaaadmin002', 1, $viejo, $viejo),
    ('bbbbbbbbbanatok1', 2, $ahora, $ahora), ('cccccccccbetotk1', 3, $viejo, $viejo)");

$tok = function (array $filas): array {
    $t = array_column($filas, 'token');
    sort($t);
    return $t;
};
t_eq(count(Tokens::listar($pdo, Tokens::filtros([]))), 4, 'Lista todas');
t_eq($tok(Tokens::listar($pdo, Tokens::filtros(['rol' => 'admin']))),
     ['aaaaaaaaadmin001', 'aaaaaaaaadmin002'], 'Filtro por rol');
t_eq($tok(Tokens::listar($pdo, Tokens::filtros(['q' => 'paz']))), ['bbbbbbbbbanatok1'], 'Busca por nombre');
t_eq($tok(Tokens::listar($pdo, Tokens::filtros(['q' => 'betotk1']))), ['cccccccccbetotk1'],
     'Busca por el final del token');
t_eq($tok(Tokens::listar($pdo, Tokens::filtros(['actividad' => 'vieja']))),
     ['aaaaaaaaadmin002', 'cccccccccbetotk1'], 'Filtro por actividad vieja');

t_eq(Tokens::revocar($pdo, ['bbbbbbbbbanatok1', 'no-existe', 'bbbbbbbbbanatok1']), ['ana@x' => 1],
     'Revoca las marcadas que existen, sin contar repetidas');
t_eq(Tokens::revocar($pdo, []), [], 'Nada marcado: nada');
t_eq(Tokens::revocarFiltrados($pdo, Tokens::filtros(['rol' => 'admin'])), ['admin' => 2],
     'Revoca todas las del filtro');
t_eq($tok(Tokens::listar($pdo, Tokens::filtros([]))), ['cccccccccbetotk1'], 'Quedan las que no tocaba');
t_eq(Tokens::revocarFiltrados($pdo, Tokens::filtros([])), ['beto@x' => 1], 'Sin filtro: revoca todas');
t_eq(Tokens::listar($pdo, Tokens::filtros([])), [], 'No queda ninguna');

$pagina = (string) file_get_contents(__DIR__ . '/../public/admin/tokens.php');
t_true(strpos($pagina, 'revocarFiltrados($pdo, $filtros)') !== false,
       'Revocar todas arma el conjunto en el servidor con el mismo filtro');

// Vida máxima de las sesiones (desde que se inician).
t_eq(Tokens::acotarHoras(0), Tokens::DURACION_MIN_HORAS, 'Duración: mínimo');
t_eq(Tokens::acotarHoras(100000), Tokens::DURACION_MAX_HORAS, 'Duración: máximo');
t_eq(Tokens::DURACION_DEFAULT_HORAS, 12, 'Por defecto 12 h');
$cache = new ReflectionProperty(Tokens::class, 'duracionCache');
$cache->setAccessible(true);
$cache->setValue(null, 12);
t_eq(Tokens::limiteSql(), '-12 hours', 'Límite para SQLite');
$pdo->exec("INSERT INTO tokens VALUES
    ('nuevo00000000001', 2, datetime('now','-11 hours'), datetime('now')),
    ('viejo00000000001', 3, datetime('now','-13 hours'), datetime('now'))");
t_eq(Tokens::purgarVencidas($pdo), 1, 'Purga la que pasó las 12 h aunque se haya usado recién');
$quedan = Tokens::listar($pdo, Tokens::filtros([]));
t_eq(array_column($quedan, 'token'), ['nuevo00000000001'], 'Queda la de 11 h');
t_true(strtotime($quedan[0]['vence_at']) - strtotime($quedan[0]['created_at']) === 12 * 3600,
       'Vence a las 12 h de creada');
$cache->setValue(null, null);

$auth = (string) file_get_contents(__DIR__ . '/../src/Auth.php');
t_true(strpos($auth, "t.created_at > datetime(\\'now\\', ?)") !== false
       && strpos($auth, 'Tokens::limiteSql()') !== false,
       'Auth rechaza el token pasada la vida máxima');
