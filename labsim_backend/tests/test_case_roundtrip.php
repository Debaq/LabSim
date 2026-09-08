<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseBuilder.php';
require_once __DIR__ . '/../src/CaseProfile.php';

/**
 * El perfil tiene que sobrevivir el viaje cases.data -> formulario ->
 * cases.data. Sin esto, editar y guardar un caso lo volvería a inferir
 * desde cero y apagaría los `auto` que el docente había encendido.
 */

// Caso guardado antes de que el perfil existiera.
$viejo = [
    'ABR' => ['OD' => ['type' => 'coclear', 'umbral' => 40], 'OI' => ['type' => 'normal']],
    'EOAS' => ['OD' => ['type' => 'coclear'], 'OI' => ['type' => 'normal']],
];
$v = CaseBuilder::caseDataToForm($viejo);
t_eq($v['perfil']['od']['cce_pct'], '100', 'Caso viejo: el formulario recibe el cce_pct inferido');
t_eq($v['perfil']['auto'], [], 'Caso viejo: ningún módulo en automático');

// Caso con perfil ya guardado.
$conPerfil = $viejo;
$conPerfil['Perfil'] = [
    'version' => 1,
    'OD' => ['cce_pct' => 35.0, 'retro' => CaseBuilder::ABR_NEURAL_DEFAULTS],
    'OI' => ['cce_pct' => 100.0, 'retro' => CaseBuilder::ABR_NEURAL_DEFAULTS],
    'auto' => ['abr' => true, 'eoas' => false, 'reflex' => false, 'recruit' => false],
];
$v = CaseBuilder::caseDataToForm($conPerfil);
t_eq($v['perfil']['od']['cce_pct'], '35', 'El cce_pct guardado vuelve al formulario');
t_eq($v['perfil']['auto']['abr'], '1', 'Un módulo en automático vuelve como checkbox marcado');
t_true(!isset($v['perfil']['auto']['eoas']), 'Un módulo en manual no aparece en el shape del form');

// El patrón retro sigue viniendo del tab ABR (hasta la fase 3), y el
// formulario tiene que redibujarlo igual que antes.
$conNeural = $viejo;
$conNeural['ABR']['OD'] = ['type' => 'neural', 'neural' => ['iii_v_ms' => 0.6, 'desincronia' => 'alta']];
$v = CaseBuilder::caseDataToForm($conNeural);
t_eq($v['abr']['od']['neural']['iii_v_ms'], '0.6', 'El patrón retro del tab ABR se relee sin cambios');
t_eq($v['abr']['od']['neural']['bloqueo'], CaseBuilder::ABR_NEURAL_DEFAULTS['bloqueo'],
    'Las claves ausentes del patrón retro caen en los defaults del generador');
