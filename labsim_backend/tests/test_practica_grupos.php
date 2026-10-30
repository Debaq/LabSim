<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Practica.php';

/**
 * El libro como carpeta y los capítulos como subcarpetas
 * (practice_folders.grupo): Practica::agrupar arma los bloques que ven el
 * panel y la agenda, en el orden de las carpetas; las sueltas van solas.
 */

$c = function (int $id, string $nombre, ?string $grupo): array {
    return ['id' => $id, 'nombre' => $nombre, 'grupo' => $grupo, 'items' => []];
};
$libro = 'Evaluación y rehabilitación en otorrinolaringología';
$bloques = Practica::agrupar([
    $c(1, 'H1 · Anamnesis', $libro), $c(2, 'Cap. 1 · El conducto', $libro),
    $c(3, 'Del curso', null), $c(4, 'Cap. 2 · Líquido', $libro), $c(5, 'Vestibular 1', 'Otro libro'),
]);
t_true(count($bloques) === 3, 'Tres bloques: el libro, la suelta y el otro libro');
t_true($bloques[0]['grupo'] === $libro && array_column($bloques[0]['carpetas'], 'id') === [1, 2, 4],
       'El libro junta sus carpetas en su orden, aunque haya una suelta en medio');
t_true($bloques[1]['grupo'] === null && $bloques[1]['carpetas'][0]['id'] === 3, 'La suelta va sola, en su lugar');
t_true($bloques[2]['grupo'] === 'Otro libro', 'Otro libro, su propio bloque');
t_true(Practica::agrupar([]) === [], 'Sin carpetas, sin bloques');

$panel = (string) file_get_contents(__DIR__ . '/../public/admin/practica.php');
t_true(strpos($panel, 'Practica::agrupar($carpetas)') !== false && strpos($panel, "'carpeta_grupo'") !== false,
       'El panel agrupa por libro y deja cambiar el libro de una carpeta');
$agenda = (string) file_get_contents(__DIR__ . '/../public/admin/agenda.php');
t_true(strpos($agenda, 'id="new-case-carpeta"') !== false && strpos($agenda, 'data-carpetas=') !== false,
       'Nueva cita filtra por libro y capítulo');
