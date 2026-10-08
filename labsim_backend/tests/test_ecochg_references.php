<?php

declare(strict_types=1);

/**
 * Bibliografía del ECochG (EcochgReferences): cada límite apunta a una
 * fuente que existe, y los límites por electrodo que se citan son los
 * mismos que usa la ficha (espejo de ecochg.SP_AP_LIMIT del cliente).
 */

require_once dirname(__DIR__) . '/src/EcochgReferences.php';
require_once dirname(__DIR__) . '/src/CaseBuilder.php';

foreach (EcochgReferences::FUENTES as $fid => $f) {
    foreach (['cita', 'n', 'protocolo', 'enlace'] as $campo) {
        t_true(isset($f[$campo]) && $f[$campo] !== '', "Fuente ECochG {$fid}: tiene {$campo}");
    }
    t_true(strpos($f['enlace'], 'http') === 0, "Fuente ECochG {$fid}: el enlace es una URL");
}

foreach (EcochgReferences::LIMITES as $clave => $lim) {
    foreach ($lim['fuentes'] as $fid) {
        t_true(isset(EcochgReferences::FUENTES[$fid]),
            "Límite ECochG {$clave}: la fuente {$fid} está citada");
    }
    t_true($lim['fuentes'] !== [] || stripos($lim['nota'], 'calculado') === 0,
        "Límite ECochG {$clave}: sin fuente tiene que decir que es calculado");
}

foreach (CaseBuilder::ECOCHG_SP_AP_LIMITS as $montaje => $limite) {
    $lim = EcochgReferences::LIMITES['sp_ap_' . $montaje] ?? null;
    t_true($lim !== null, "Límite ECochG del electrodo {$montaje} citado");
    if ($lim !== null) {
        t_eq((float) str_replace(',', '.', $lim['valor']), $limite,
            "Límite ECochG {$montaje}: la cita dice el mismo número que la ficha");
    }
}
