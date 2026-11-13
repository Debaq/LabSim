<?php

declare(strict_types=1);

/**
 * Feedback al feedback (ComentarioRespuestas). Sin base: solo la limpieza
 * del texto, que decide si una respuesta se guarda y cómo. El candado de
 * pertenencia (deAlumno) es SQL y se prueba en el servidor de verdad.
 */

require_once dirname(__DIR__) . '/src/ComentarioRespuestas.php';

t_eq(ComentarioRespuestas::limpiar(''), null, 'respuesta vacía: no se guarda');
t_eq(ComentarioRespuestas::limpiar("  \n\t "), null, 'solo espacios: no se guarda');
t_eq(ComentarioRespuestas::limpiar("  Entendí.  "), 'Entendí.', 'recorta espacios de los bordes');
t_eq(ComentarioRespuestas::limpiar("uno\r\ndos"), "uno\ndos", 'saltos de Windows a \\n');

$largo = str_repeat('ñ', ComentarioRespuestas::MAX_CHARS + 50);
t_eq(mb_strlen((string) ComentarioRespuestas::limpiar($largo)), ComentarioRespuestas::MAX_CHARS,
    'corta en MAX_CHARS caracteres (no bytes)');

// Editar / eliminar lo del docente (ComentariosDocente::puedeTocar): cada
// uno lo suyo, el admin completo todo.
require_once dirname(__DIR__) . '/src/ComentariosDocente.php';
t_true(ComentariosDocente::puedeTocar(5, 5, false), 'docente: puede tocar lo suyo');
t_true(!ComentariosDocente::puedeTocar(5, 6, false), 'docente: no toca lo de otro docente');
t_true(ComentariosDocente::puedeTocar(5, 1, true), 'admin completo: toca lo de cualquiera');
t_eq(ComentariosDocente::TIPOS, ['atencion', 'chat', 'respuesta'], 'tipos editables: nada del alumno');
