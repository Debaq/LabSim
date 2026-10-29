<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Layout.php';
require_once __DIR__ . '/../src/Courses.php';

/**
 * Nariz y sueño son demo interna (docs/roadmap_nasal.md): el alumno no ve
 * sus boxes ni puede activar sus equipos, y ningún curso los puede prender.
 * Solo el admin los ve, por el override del cliente. Si esto falla, alguien
 * los soltó: que sea a propósito.
 */

$nasales = ['RS', 'RM', 'RA', 'OLF', 'PRICK', 'ESP', 'PSG', 'CPAP'];
$enBoxes = array_merge(Layout::BOXS['Box_4'][1], Layout::BOXS['Box_5'][1]);
sort($enBoxes);
$esperados = $nasales;
sort($esperados);
t_eq($enBoxes, $esperados, 'Box_4 y Box_5 llevan exactamente los equipos nasales y de sueño');
t_eq(Layout::BOXS['Box_4'][0], false, 'Box Rinología inactivo para el alumno');
t_eq(Layout::BOXS['Box_5'][0], false, 'Laboratorio de sueño inactivo para el alumno');
foreach ($nasales as $codigo) {
    t_eq(Layout::APPS[$codigo][5] ?? null, 'development', "$codigo en development");
    t_true(!isset(Courses::MODULES[$codigo]), "$codigo fuera de Courses::MODULES");
}
