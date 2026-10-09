<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/AlumnoIndicadores.php';

/** Indicadores de la ficha del alumno (admin/student.php). */

$regla = static fn(string $t, ?bool $c): array => ['texto' => $t, 'cumple' => $c];
$tec1 = [
    'orden' => ['reglas' => [$regla('Orden de pruebas', true)]],
    'aereos' => ['reglas' => [$regla('Parte en 1 kHz', false)],
                 'oidos' => ['od' => [$regla('Bajar 10 subir 5', true)], 'oi' => [$regla('Bajar 10 subir 5', false)]]],
    'oseos' => ['reglas' => [$regla('Sin evaluar', null)]],
];
$tec2 = [
    'orden' => ['reglas' => [$regla('Orden de pruebas', false)]],
    'aereos' => ['reglas' => [$regla('Parte en 1 kHz', false)],
                 'oidos' => ['od' => [$regla('Bajar 10 subir 5', true)], 'oi' => [$regla('Bajar 10 subir 5', true)]]],
];
$pasos = AlumnoIndicadores::pasosDificiles([$tec1, $tec2]);
t_eq(array_column($pasos, 'texto'), ['Parte en 1 kHz', 'Orden de pruebas', 'Bajar 10 subir 5'],
     'Pasos fallados, el que más falla (por proporción) primero');
t_eq([$pasos[0]['fallos'], $pasos[0]['evaluadas']], [2, 2], 'Falló en 2 de 2');
t_eq([$pasos[2]['fallos'], $pasos[2]['evaluadas']], [1, 2], 'Por oído cuenta una vez por atención: falló si falló en uno');
t_eq($pasos[0]['seccion'], 'Aéreos', 'Sección legible');
t_true(!in_array('Sin evaluar', array_column($pasos, 'texto'), true), 'Lo no evaluable no aparece');
t_eq(AlumnoIndicadores::pasosDificiles([]), [], 'Sin audiometrías no hay pasos');

t_eq(AlumnoIndicadores::tendencia([50]), null, 'Un punto no tiene tendencia');
t_eq(AlumnoIndicadores::tendencia([40, 60, 80, 100]), 40, 'Mitad nueva menos mitad vieja');
t_eq(AlumnoIndicadores::tendencia([80, 0, 60]), -20, 'Con impar, el del medio no cuenta');

t_eq(AlumnoIndicadores::mediana([]), null, 'Mediana vacía');
t_eq(AlumnoIndicadores::mediana([9, 1, 5]), 5, 'Mediana impar');
t_eq(AlumnoIndicadores::mediana([1, 2, 3, 10]), 3, 'Mediana par redondeada');
t_eq(AlumnoIndicadores::promedio([50, 100]), 75, 'Promedio');

t_eq(AlumnoIndicadores::minutos(null), '—', 'Sin duración');
t_eq(AlumnoIndicadores::minutos(750), '13 min', 'Minutos redondeados');
t_eq(AlumnoIndicadores::minutos(3900), '1 h 05 min', 'Más de una hora');
