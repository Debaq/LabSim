<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Equipos.php';

/** Lo que manda la app al iniciar sesión y cómo se compara contra lo publicado. */

$ok = ['id' => '0123456789abcdef', 'nombre' => "LAB-01\n", 'so' => 'Linux',
       'version' => '0.9.8-rcbd419e', 'empaquetada' => true];
t_eq(Equipos::normalizar($ok),
     ['id' => '0123456789abcdef', 'nombre' => 'LAB-01', 'so' => 'Linux',
      'version' => '0.9.8-rcbd419e', 'empaquetada' => 1],
     'Bloque válido, sin caracteres de control');
t_eq(Equipos::normalizar(null), null, 'App vieja sin bloque: no se registra');
t_eq(Equipos::normalizar(array_merge($ok, ['id' => 'LAB-01'])), null, 'Id con otro formato: no se registra');
t_eq(Equipos::normalizar(array_merge($ok, ['version' => '<b>'])), null, 'Versión rara: no se registra');
t_eq(strlen(Equipos::normalizar(array_merge($ok, ['nombre' => str_repeat('x', 200)]))['nombre']), 64,
     'Nombre recortado');

$releases = [
    ['tag_name' => 'pyinstaller-v0.9.8-rcbd419e', 'created_at' => '2026-09-25T03:00:00Z'],
    ['tag_name' => 'pyinstaller-v0.9.9', 'created_at' => '2026-09-25T19:35:00Z'],
    ['tag_name' => 'pyinstaller-v0.9.8-r84db62b', 'created_at' => '2026-09-24T20:38:00Z'],
];
t_eq(Equipos::estado('0.9.9', true, $releases)['clave'], 'al_dia', 'La más nueva por fecha, no por orden');
t_eq(Equipos::estado('0.9.8-rcbd419e', true, $releases)['texto'], '1 versión atrás', 'Una atrás');
t_eq(Equipos::estado('0.9.8-r84db62b', true, $releases)['texto'], '2 versiones atrás', 'Dos atrás');
t_eq(Equipos::estado('0.9.7', true, $releases)['clave'], 'no_publicada', 'Fuera de la lista');
t_eq(Equipos::estado('0.9.9', false, $releases)['clave'], 'desarrollo', 'Desde el código');
t_eq(Equipos::estado('0.9.9', true, [])['clave'], 'sin_lista', 'Sin lista guardada');
