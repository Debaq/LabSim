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

// =====================================================================
// VEMP: tres subtipos por oído
// =====================================================================

// Caso guardado con el shape nuevo: cada subtipo se relee con lo suyo.
$conVemp = $viejo;
$conVemp['VEMP'] = [
    'OD' => [
        'type' => 'sacular',
        'subtipos' => [
            'CVEMP' => ['umbral' => 45, 'repro' => false, 'repro_var' => 0.4,
                        'average_objetivo' => 250,
                        'desviaciones' => ['p13' => ['lat' => 1.5, 'amp' => -90.0],
                                           'n23' => ['lat' => 0.0, 'amp' => -55.0]]],
            'OVEMP' => ['umbral' => 65, 'repro' => true, 'repro_var' => 0.2,
                        'average_objetivo' => 300,
                        'desviaciones' => ['n10' => ['lat' => 0.0, 'amp' => 0.0],
                                           'p16' => ['lat' => 0.0, 'amp' => 0.0]]],
            'MVEMP' => ['umbral' => 70, 'repro' => true, 'repro_var' => 0.2,
                        'average_objetivo' => 300,
                        'desviaciones' => ['p13' => ['lat' => 0.3, 'amp' => -10.0],
                                           'n23' => ['lat' => 0.0, 'amp' => 0.0]]],
        ],
    ],
    'OI' => ['type' => 'normal'],
];
$v = CaseBuilder::caseDataToForm($conVemp);
t_eq($v['vemp']['od']['type'], 'sacular', 'VEMP: la patología es del oído, una sola');
t_eq($v['vemp']['od']['CVEMP']['umbral'], '45', 'VEMP: cada subtipo relee su umbral');
t_eq($v['vemp']['od']['OVEMP']['umbral'], '65', 'VEMP: el umbral del ocular no es el del cervical');
t_true(!isset($v['vemp']['od']['CVEMP']['repro']),
    'VEMP: un subtipo marcado como no reproducible vuelve sin la casilla');
t_eq($v['vemp']['od']['OVEMP']['repro'], '1', 'VEMP: reproducible vuelve tildado');
// El punto de separarlos: cVEMP y mVEMP comparten los nombres de pico y
// antes se pisaban en los mismos cuatro campos.
t_eq($v['vemp']['od']['CVEMP']['amp_p13'], '-90', 'VEMP: P13 del cervical');
t_eq($v['vemp']['od']['MVEMP']['amp_p13'], '-10', 'VEMP: P13 del masetero NO es el del cervical');

// Oído sin nada guardado: los tres arrancan en su propio default.
t_eq($v['vemp']['oi']['CVEMP']['umbral'], (string) CaseBuilder::VEMP_DEFAULTS['CVEMP']['umbral'],
    'VEMP: un oído sin configurar cae en el default de cada subtipo');
t_eq($v['vemp']['oi']['MVEMP']['average_objetivo'], (string) CaseBuilder::VEMP_DEFAULTS['MVEMP']['average_objetivo'],
    'VEMP: las promediaciones por defecto son las del subtipo, no una sola para los tres');

// Caso viejo (un solo subtipo, valores en la raíz del oído): se los queda
// el subtipo que el caso decía y los otros dos arrancan limpios -- no había
// nada cargado en ellos, y copiárselos inventaría un hallazgo.
$vempLegado = $viejo;
$vempLegado['VEMP'] = [
    'OD' => [
        'subtipo' => 'OVEMP',
        'type' => 'utricular',
        'umbral' => 85,
        'repro' => true,
        'repro_var' => 0.3,
        'average_objetivo' => 400,
        'desviaciones' => ['n10' => ['lat' => 1.2, 'amp' => -6.0], 'p16' => ['lat' => 0.0, 'amp' => 0.0],
                           'p13' => ['lat' => 0.0, 'amp' => 0.0], 'n23' => ['lat' => 0.0, 'amp' => 0.0]],
    ],
    'OI' => ['type' => 'normal'],
];
$v = CaseBuilder::caseDataToForm($vempLegado);
t_eq($v['vemp']['od']['type'], 'utricular', 'VEMP legado: la patología se conserva');
t_eq($v['vemp']['od']['OVEMP']['umbral'], '85', 'VEMP legado: el umbral va al subtipo que el caso decía');
t_eq($v['vemp']['od']['OVEMP']['amp_n10'], '-6', 'VEMP legado: las ondas también');
t_eq($v['vemp']['od']['CVEMP']['umbral'], (string) CaseBuilder::VEMP_DEFAULTS['CVEMP']['umbral'],
    'VEMP legado: los otros dos subtipos arrancan en default, no copian al guardado');
t_eq($v['vemp']['od']['CVEMP']['amp_p13'], '0',
    'VEMP legado: los picos de un subtipo nunca configurado quedan en 0');

// La revisión ficha por ficha vuelve tildada al reeditar (ver CaseReview).
$revisado = $viejo;
$revisado['Revision'] = ['tabs' => ['vemp' => true, 'abr' => false]];
$v = CaseBuilder::caseDataToForm($revisado);
t_eq($v['revisado']['vemp'], '1', 'Revisión: la ficha revisada vuelve tildada');
t_true(!isset($v['revisado']['abr']), 'Revisión: la ficha sin revisar no trae el flag');

// El flag viejo "ya decidí lo vestibular" (por oído, casilla de la ficha
// VEMP) cuenta como la ficha VEMP revisada: un caso guardado con él no
// tiene por qué volver a pasar por el Resumen para eso.
$vempDecidido = $viejo;
$vempDecidido['VEMP'] = [
    'OD' => ['type' => 'normal', 'decidido' => true],
    'OI' => ['type' => 'normal', 'decidido' => true],
];
$v = CaseBuilder::caseDataToForm($vempDecidido);
t_eq($v['revisado']['vemp'], '1', 'VEMP legado: "decidido" en los dos oídos vale como ficha revisada');
$vempMedio = $viejo;
$vempMedio['VEMP'] = ['OD' => ['type' => 'normal', 'decidido' => true], 'OI' => ['type' => 'normal']];
$v = CaseBuilder::caseDataToForm($vempMedio);
t_true(!isset($v['revisado']['vemp']), 'VEMP legado: con un solo oído decidido la ficha sigue sin revisar');
