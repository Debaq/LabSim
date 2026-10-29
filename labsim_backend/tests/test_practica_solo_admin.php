<?php

declare(strict_types=1);

/**
 * Las carpetas de práctica solo_admin (demo interna: los pacientes nasales)
 * no les llegan a alumnos ni docentes: la lista y el "iniciar" filtran por
 * la columna, el endpoint pasa si es permission 777, y la columna la crea
 * la migración y el schema. Si esto falla, la demo se les aparece a todos.
 */

$leer = function (string $ruta): string {
    return (string) file_get_contents(__DIR__ . '/../' . $ruta);
};
$practica = $leer('src/Practica.php');
t_eq(substr_count($practica, 'JOIN practice_folders f ON f.id = pi.folder_id AND f.active = 1{$soloAdmin}'), 2,
     'lista e iniciar filtran las carpetas solo_admin');
t_true(strpos($practica, "' AND f.solo_admin = 0'") !== false, 'El filtro deja fuera solo_admin = 1');
$api = $leer('public/api/practica.php');
t_true(strpos($api, 'Auth::PERMISSION_ADMIN') !== false, 'El endpoint mira si es permission 777, no el rol');
t_true(strpos($api, '$verSoloAdmin);') !== false, 'Lo pasa a lista e iniciar');
t_true(strpos($leer('src/Db.php'), "'practice_folders', 'solo_admin'") !== false, 'La migración agrega la columna');
t_true(preg_match('/CREATE TABLE IF NOT EXISTS practice_folders \([^;]*solo_admin INTEGER NOT NULL DEFAULT 0/s',
                  $leer('sql/schema.sql')) === 1, 'El schema trae la columna');
