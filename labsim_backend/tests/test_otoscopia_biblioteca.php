<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/OtoscopiaBiblioteca.php';

/**
 * Base de otoscopias: la regla de espejado por oído y la geometría del
 * encuadre (la misma que dibuja el editor en el canvas). Sin GD ni base:
 * el render y la asignación a casos se probaron aparte con GD real.
 */

// OD quiere lo anterior a la derecha de la imagen; OI, a la izquierda.
t_eq(OtoscopiaBiblioteca::debeEspejar('der', 'od'), false, 'Anterior a la derecha va tal cual en OD');
t_eq(OtoscopiaBiblioteca::debeEspejar('der', 'oi'), true, 'Anterior a la derecha se espeja para OI');
t_eq(OtoscopiaBiblioteca::debeEspejar('izq', 'oi'), false, 'Anterior a la izquierda va tal cual en OI');
t_eq(OtoscopiaBiblioteca::debeEspejar('izq', 'od'), true, 'Anterior a la izquierda se espeja para OD');
t_eq(OtoscopiaBiblioteca::debeEspejar('nd', 'od'), false, 'Si no se distingue, nunca se espeja (OD)');
t_eq(OtoscopiaBiblioteca::debeEspejar('nd', 'oi'), false, 'Si no se distingue, nunca se espeja (OI)');
t_eq(OtoscopiaBiblioteca::debeEspejar(null, 'oi'), false, 'Sin clasificar no se espeja');

// Sin giro, la imagen girada es la misma: el punto no se mueve.
[$x, $y] = OtoscopiaBiblioteca::puntoEnGirada(30, 40, 200, 100, 0, 200, 100);
t_close($x, 30, 1e-9, 'Sin giro, x queda igual');
t_close($y, 40, 1e-9, 'Sin giro, y queda igual');

// 90° horario sobre 200x100: la caja pasa a 100x200. El borde derecho al
// medio (200, 50) baja al borde inferior al medio (50, 200); la esquina
// superior izquierda (0, 0) pasa a la superior derecha (100, 0).
[$x, $y] = OtoscopiaBiblioteca::puntoEnGirada(200, 50, 200, 100, 90, 100, 200);
t_close($x, 50, 1e-9, '90° horario: el borde derecho queda abajo (x)');
t_close($y, 200, 1e-9, '90° horario: el borde derecho queda abajo (y)');
[$x, $y] = OtoscopiaBiblioteca::puntoEnGirada(0, 0, 200, 100, 90, 100, 200);
t_close($x, 100, 1e-9, '90° horario: la esquina sup. izq. pasa a la sup. der. (x)');
t_close($y, 0, 1e-9, '90° horario: la esquina sup. izq. pasa a la sup. der. (y)');

// El centro del original siempre cae en el centro de la caja girada.
[$x, $y] = OtoscopiaBiblioteca::puntoEnGirada(100, 50, 200, 100, 33, 240, 190);
t_close($x, 120, 1e-9, 'El centro queda en el centro con cualquier giro (x)');
t_close($y, 95, 1e-9, 'El centro queda en el centro con cualquier giro (y)');

// Encuadre que viene del navegador.
$e = OtoscopiaBiblioteca::encuadreSano(270, 50, 50, 100, 400, 300);
t_close($e['rotacion'], -90, 1e-9, '270° se guarda como -90°');
$e = OtoscopiaBiblioteca::encuadreSano(-180, 50, 50, 100, 400, 300);
t_close($e['rotacion'], 180, 1e-9, '-180° se guarda como 180°');
$e = OtoscopiaBiblioteca::encuadreSano(0, -20, 900, 100, 400, 300);
t_eq([$e['centro_x'], $e['centro_y']], [0.0, 300.0], 'El centro no sale del original');
$e = OtoscopiaBiblioteca::encuadreSano(0, 200, 150, 0, 400, 300);
t_close($e['lado'], 300, 1e-9, 'Lado 0 vuelve al lado corto del original');
$e = OtoscopiaBiblioteca::encuadreSano(0, 200, 150, 99999, 400, 300);
t_close($e['lado'], 1000, 1e-9, 'Lado tope: el doble de la diagonal');
$e = OtoscopiaBiblioteca::encuadreSano(NAN, 200, 150, 2, 400, 300);
t_eq([$e['rotacion'], $e['lado']], [0.0, 8.0], 'Giro inválido vuelve a 0; lado mínimo 8 px');

t_true(OtoscopiaBiblioteca::clasificada(['anterior' => 'nd', 'tipo' => 'cerumen']), 'Con lado y tipo está clasificada');
t_true(!OtoscopiaBiblioteca::clasificada(['anterior' => null, 'tipo' => 'normal']), 'Sin lado no está clasificada');
t_true(!OtoscopiaBiblioteca::clasificada(['anterior' => 'der', 'tipo' => '']), 'Sin tipo no está clasificada');
