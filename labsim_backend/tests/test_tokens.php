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
