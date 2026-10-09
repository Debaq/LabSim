<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Consola.php';

/** Consola remota: lo que no necesita base (duración, params, rutas de data/). */

t_eq(Consola::normalizarHoras(0), 1, 'Menos de 1 h queda en 1 h');
t_eq(Consola::normalizarHoras(4), 4, 'Duración del panel se respeta');
t_eq(Consola::normalizarHoras(10), 8, 'Una intermedia baja a la de abajo');
t_eq(Consola::normalizarHoras(10000), 72, 'Tope de 72 h');

t_eq(Consola::paramsPdo([]), [], 'Sin params');
t_eq(Consola::paramsPdo([1, 'x']), [1, 'x'], 'Lista para "?"');
t_eq(Consola::paramsPdo(['id' => 3, ':u' => 'a']), [':id' => 3, ':u' => 'a'], 'Mapa con o sin dos puntos');

t_eq(strlen(Consola::hash('lsc_x')), 64, 'sha256 en hex');

$base = sys_get_temp_dir() . '/consola_test_' . bin2hex(random_bytes(4));
mkdir($base . '/tickets', 0775, true);
file_put_contents($base . '/tickets/a.log', 'x');
$base = (string) realpath($base);
t_eq(Consola::resolverRuta($base, ''), $base, 'Raíz de data/');
t_eq(Consola::resolverRuta($base, 'tickets/a.log'), $base . '/tickets/a.log', 'Archivo adentro');
t_eq(Consola::resolverRuta($base, '/tickets'), $base . '/tickets', 'Barra inicial no saca de data/');
t_eq(Consola::resolverRuta($base, '../'), null, '".." no sale de data/');
t_eq(Consola::resolverRuta($base, 'tickets/../../etc'), null, '".." al medio tampoco');
t_eq(Consola::resolverRuta($base, 'no_existe'), null, 'Lo que no existe');
@symlink(sys_get_temp_dir(), $base . '/afuera');
if (is_link($base . '/afuera')) {
    t_eq(Consola::resolverRuta($base, 'afuera'), null, 'Enlace hacia afuera de data/');
    unlink($base . '/afuera');
}
unlink($base . '/tickets/a.log');
rmdir($base . '/tickets');
rmdir($base);

$api = (string) file_get_contents(__DIR__ . '/../public/api/consola.php');
t_true(strpos($api, 'Consola::tokenVigente') !== false && strpos($api, 'CREATE TABLE') === false,
       'api/consola.php valida el token y no migra la base');
$admin = (string) file_get_contents(__DIR__ . '/../public/admin/consola.php');
t_true(strpos($admin, 'requireFullAdminSession') !== false && strpos($admin, 'requireCsrf') !== false,
       'admin/consola.php solo para admin completo y con CSRF');
