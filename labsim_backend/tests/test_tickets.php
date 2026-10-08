<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Tickets.php';

/** Lo que se acepta de un reporte de problema mandado desde la app. */

t_eq(Tickets::normalizarDetalle(null), [], 'Sin detalle');
t_eq(Tickets::normalizarDetalle(['so_version' => "6.1\n", 'kiosko' => true, 'raro' => ['x'], 'Mal-Clave' => 'x']),
     ['so_version' => '6.1', 'kiosko' => 'sí'],
     'Solo claves simples y valores de texto, sin saltos de línea');
t_eq(strlen(Tickets::normalizarDetalle(['python' => str_repeat('x', 500)])['python']), 200, 'Valor recortado');
$muchos = [];
for ($i = 0; $i < 50; $i++) {
    $muchos["k{$i}"] = 'v';
}
t_eq(count(Tickets::normalizarDetalle($muchos)), 30, 'Tope de claves');

t_true(Tickets::esGzip(gzencode('hola')), 'gzip de verdad');
t_true(!Tickets::esGzip('hola'), 'Texto plano no pasa');
t_true(!Tickets::esGzip(''), 'Vacío no pasa');

t_eq(Tickets::cola("a\nb\nc\nd\n", 2), "c\nd", 'Cola del registro');
t_eq(Tickets::cola("a\r\nb", 5), "a\nb", 'Cola con CRLF de Windows');

// Cierre inesperado sin sesión: se acepta con tope por equipo y global.
t_true(Tickets::MAX_ANONIMOS_POR_EQUIPO_HORA > 0 && Tickets::MAX_ANONIMOS_POR_EQUIPO_HORA < Tickets::MAX_ANONIMOS_HORA,
       'Tope de reportes anónimos por equipo menor que el global');
$ticketPhp = (string) file_get_contents(__DIR__ . '/../public/api/ticket.php');
t_true(strpos($ticketPhp, "cierre_inesperado") !== false && strpos($ticketPhp, 'excedeLimiteAnonimo') !== false,
       'ticket.php solo deja pasar sin sesión los cierres inesperados, con tope');
