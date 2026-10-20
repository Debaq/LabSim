<?php

declare(strict_types=1);

/**
 * Bibliografía de la vía central (CentralReferences): toda fuente tiene
 * ficha, todo número apunta a una fuente o dice que es calculado, y todo
 * cuadro central del generador tiene respaldo.
 */

require_once dirname(__DIR__) . '/src/CentralReferences.php';
require_once dirname(__DIR__) . '/src/CaseProfile.php';

foreach (CentralReferences::FUENTES as $fid => $f) {
    foreach (['cita', 'n', 'protocolo', 'enlace'] as $campo) {
        t_true(isset($f[$campo]) && $f[$campo] !== '', "Fuente central {$fid}: tiene {$campo}");
    }
    t_true(strpos($f['enlace'], 'http') === 0, "Fuente central {$fid}: el enlace es una URL");
}

foreach (CentralReferences::LIMITES as $clave => $lim) {
    foreach ($lim['fuentes'] as $fid) {
        t_true(isset(CentralReferences::FUENTES[$fid]), "Número central {$clave}: la fuente {$fid} está citada");
    }
    t_true($lim['fuentes'] !== [] || stripos($lim['nota'], 'calculado') === 0,
        "Número central {$clave}: sin fuente tiene que decir que es calculado");
}

foreach (CaseProfile::CENTRAL_SCENARIOS as $clave => $_) {
    $cuadro = CentralReferences::CUADROS[$clave] ?? null;
    t_true($cuadro !== null && $cuadro['fuentes'] !== [], "Cuadro central {$clave}: tiene bibliografía");
    foreach ($cuadro['fuentes'] ?? [] as $fid) {
        t_true(isset(CentralReferences::FUENTES[$fid]), "Cuadro central {$clave}: la fuente {$fid} está citada");
    }
}
foreach (CentralReferences::CUADROS as $clave => $_) {
    t_true(isset(CaseProfile::CENTRAL_SCENARIOS[$clave]), "Bibliografía del cuadro central {$clave}: el cuadro existe");
}

// La fórmula de la P1 que se cita es la que usa el cliente.
$py = (string) file_get_contents(__DIR__ . '/../../src/abr/cortical.py');
t_true(strpos($py, 'P1_INTERCEPT_MS = 155.6') !== false && strpos($py, 'P1_SLOPE_MS = 32.746') !== false,
       'P1: el cliente usa la regresión de Sharma 2002 que se cita');
t_true(strpos($py, 'ELECTRODE_EFFECT_LIMIT = 0.50') !== false,
       'Efecto electrodo: el cliente usa el 50 % que se cita');
