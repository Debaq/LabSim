<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseLibrary.php';

/**
 * Lo que se puede probar de CaseLibrary sin base: la limpieza de la lista de
 * ids que llega del formulario de checkboxes.
 *
 * Es el único punto donde entra input del navegador a las operaciones en
 * tanda --archivar, mover, ELIMINAR-- y de él depende cuántas fichas toca
 * cada una. Un id vacío colado en la lista arma un `IN (?, ?)` con un
 * parámetro de más; uno repetido hace que el contador de "40 fichas
 * eliminadas" mienta. Este entorno no tiene pdo_sqlite, así que el resto
 * (transacción del borrado, conteos) se prueba en el servidor.
 */

t_eq(CaseLibrary::limpiarIds([]), [], 'lista vacía -> vacía');
t_eq(CaseLibrary::limpiarIds(['12', '13']), ['12', '13'], 'ids normales pasan tal cual');
t_eq(CaseLibrary::limpiarIds(['12', '12', '13']), ['12', '13'], 'los repetidos se colapsan');
t_eq(CaseLibrary::limpiarIds(['', '  ', '12']), ['12'], 'los vacíos y en blanco se caen');
t_eq(CaseLibrary::limpiarIds([' 12 ']), ['12'], 'se recortan los espacios de los costados');
// El form manda strings, pero un id que llegue como int no puede cambiar de
// comportamiento: cases.id es TEXT y '7' y 7 son la misma ficha.
t_eq(CaseLibrary::limpiarIds([7, '7']), ['7'], 'int y string del mismo id son uno solo');
// Reindexado: array_keys() ya lo garantiza, pero el IN dinámico arma los
// placeholders con array_fill(0, count(...)), así que una lista con huecos
// de índices desalinearía los parámetros.
t_eq(array_keys(CaseLibrary::limpiarIds(['a', 'b', 'c'])), [0, 1, 2], 'la lista vuelve reindexada');

// Tema, número y título salen del nombre de la carpeta (vista de carpetas).
t_eq(CaseLibrary::partesNombre('ABR 2 · Recién nacido con hipoacusia'),
     ['tema' => 'ABR', 'numero' => '2', 'titulo' => 'Recién nacido con hipoacusia'], 'Tema con número');
t_eq(CaseLibrary::partesNombre('Revisar · duplicados'),
     ['tema' => 'Revisar', 'numero' => '', 'titulo' => 'duplicados'], 'Tema sin número');
t_eq(CaseLibrary::partesNombre('Semestre 1'),
     ['tema' => '', 'numero' => '', 'titulo' => 'Semestre 1'], 'Sin " · " no hay tema, el número es parte del título');
$grupos = CaseLibrary::agruparPorTema([
    ['id' => 1, 'name' => 'ABR 1 · A'], ['id' => 2, 'name' => 'abr 2 · B'],
    ['id' => 3, 'name' => 'Suelta'], ['id' => 4, 'name' => 'Audiología 1 · C'],
]);
t_eq(array_column($grupos, 'tema'), ['ABR', 'Audiología', ''], 'Temas sin distinguir mayúsculas, sin tema al final');
t_eq(array_column($grupos[0]['carpetas'], 'id'), [1, 2], 'Carpetas del tema en su orden');
