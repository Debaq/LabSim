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
