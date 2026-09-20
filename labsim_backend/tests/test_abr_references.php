<?php

declare(strict_types=1);

/**
 * Bibliografía normativa del ABR (AbrReferences).
 *
 * Lo que se cuida acá: que cada set publicado apunte a una fuente que
 * exista y con cita completa, que no se cuele un valor imposible, y que el
 * catálogo del caso mezcle bien los sets de fábrica con los del docente.
 */

require_once dirname(__DIR__) . '/src/AbrReferences.php';

// --- Fuentes -------------------------------------------------------------

t_true(count(AbrReferences::FUENTES) >= 10, 'Hay bibliografía cargada');
foreach (AbrReferences::FUENTES as $fid => $f) {
    foreach (['cita', 'n', 'protocolo', 'enlace'] as $campo) {
        t_true(isset($f[$campo]) && $f[$campo] !== '', "Fuente {$fid}: tiene {$campo}");
    }
}

// --- Anclaje del set de fábrica -----------------------------------------

foreach (AbrReferences::ANCLAJE as $pop => $anclas) {
    foreach ($anclas as $que => $fid) {
        t_true(
            $fid === 'calculada' || isset(AbrReferences::FUENTES[$fid]),
            "Anclaje {$pop}/{$que}: la fuente {$fid} está citada"
        );
    }
}

// --- Sets publicados ------------------------------------------------------

$poblaciones = ['adult_male', 'adult_female', 'child', 'neonate', 'elderly'];
foreach (AbrReferences::SETS as $id => $set) {
    t_true(isset(AbrReferences::FUENTES[$set['fuente']]), "Set {$id}: su fuente está citada");
    t_true(($set['nota'] ?? '') !== '', "Set {$id}: dice qué publica y qué no");
    foreach ($set['populations'] as $pop => $ondas) {
        t_true(in_array($pop, $poblaciones, true), "Set {$id}: población {$pop} conocida");
        $previa = 0.0;
        foreach (['I', 'III', 'V'] as $onda) {
            if (!isset($ondas[$onda]['lat'])) {
                continue;
            }
            $lat = (float) $ondas[$onda]['lat'];
            t_true($lat > $previa, "Set {$id}/{$pop}: la onda {$onda} va después de la anterior");
            t_true($lat > 0.5 && $lat < 12.0, "Set {$id}/{$pop}/{$onda}: latencia plausible");
            $previa = $lat;
        }
    }
}

// --- Catálogo del caso ----------------------------------------------------

$propios = ['mi_set' => ['label' => 'Mío', 'populations' => []]];
$catalogo = AbrReferences::catalog($propios);
t_true(isset($catalogo['mi_set']), 'catalog(): entra el set del docente');
t_true(isset($catalogo['sanfins_2026']), 'catalog(): entran los publicados');
t_true(!empty($catalogo['sanfins_2026']['bibliografico']), 'catalog(): los publicados quedan marcados');

// Un set propio con el mismo id pisa al de fábrica: es la vía para corregir
// uno sin tocar código.
$pisado = AbrReferences::catalog(['hood' => ['label' => 'Hood corregido']]);
t_eq($pisado['hood']['label'], 'Hood corregido', 'catalog(): el set propio pisa al de fábrica');
t_eq(count($pisado), count(AbrReferences::SETS), 'catalog(): pisar no duplica la entrada');

// --- Planilla -------------------------------------------------------------

t_true(
    AbrReferences::planilla() !== null,
    'La planilla de referencia viaja con el backend (el docente no ve el repo del cliente)'
);
