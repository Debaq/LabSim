<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseBuilder.php';
require_once __DIR__ . '/../src/CaseProfile.php';

/**
 * Electrococleografía: el bloque del caso.
 *
 * El cliente (src/abr/ecochg.py) no registra nada si el oído no trae este
 * bloque -- no inventa un oído normal. O sea que si esto no llega, la
 * prueba no existe para el alumno: es la parte que hay que proteger.
 */

// ---------------------------------------------------------------- defaults

t_eq(CaseBuilder::ECOCHG_DEFAULTS['sp_ap'], 0.25,
     'La razón PS/PA de un oído sano arranca bajo el límite timpánico (0.40)');
t_true(CaseBuilder::ECOCHG_DEFAULTS['sp_ap'] < 0.40,
       'El default no puede ser ya un hidrops');
t_eq(CaseBuilder::ECOCHG_MC_OPTIONS, CaseBuilder::ABR_NEURAL_MICROFONICA_OPTIONS,
     'La microfónica del ECochG y la del patrón retro son el mismo potencial');

// ------------------------------------------------------------ ida y vuelta

$conEcochg = [
    'ABR' => [
        'OD' => ['type' => 'coclear', 'umbral' => 40,
                 'ecochg' => ['sp_ap' => 0.58, 'tasa' => 2.2,
                              'rar_cond_ms' => 0.4, 'mc' => 'normal']],
        'OI' => ['type' => 'normal'],
    ],
];
$v = CaseBuilder::caseDataToForm($conEcochg);
t_eq($v['abr']['od']['ecochg']['sp_ap'], '0.58',
     'La razón guardada vuelve al formulario');
t_eq($v['abr']['od']['ecochg']['tasa'], '2.2',
     'La adaptación por tasa vuelve al formulario');
t_true(!isset($v['abr']['od']['ecochg']['mc']),
       'La microfónica NO es un campo del formulario: sale del patrón retro');

// Un caso guardado antes de que el ECochG existiera no trae la clave. En
// el CASO eso significa "este oído no registra ECochG"; en el FORMULARIO
// hay que mostrar algo, y lo que se muestra es un oído sano.
$v = CaseBuilder::caseDataToForm(['ABR' => ['OD' => ['type' => 'normal']]]);
t_eq($v['abr']['od']['ecochg']['sp_ap'], '0.25',
     'Caso viejo: el formulario dibuja un oído sano');

// ------------------------------------------------------------- los cuadros

$meniere = CaseProfile::SCENARIOS['meniere'];
t_true(isset($meniere['ecochg']), 'El Ménière trae eje de electrococleografía');
t_true($meniere['ecochg']['sp_ap'][0] > 0.40,
       'El Ménière arranca por encima del límite timpánico');
t_true($meniere['ecochg']['tasa'][0] > 1.0,
       'El Ménière se adapta más que un oído sano al subir la tasa');
t_true($meniere['ecochg']['rar_cond_ms'][0] > CaseBuilder::ECOCHG_DEFAULTS['rar_cond_ms'],
       'El Ménière separa más las dos polaridades');

$retardado = CaseProfile::SCENARIOS['hidrops_retardado'];
t_true(isset($retardado['ecochg']),
       'El hidrops retardado es el mismo hidrops: también trae el eje');

// Ningún otro cuadro declara ECochG: el eje es del hidrops y nada más. Si
// mañana se agrega otro, este test lo hace explícito en vez de que aparezca
// una razón alta en un cuadro donde nadie la esperaba.
$conEje = [];
foreach (CaseProfile::SCENARIOS as $clave => $esc) {
    if (isset($esc['ecochg'])) {
        $conEje[] = $clave;
    }
}
sort($conEje);
t_eq($conEje, ['hidrops_retardado', 'meniere'],
     'El eje de ECochG está solo en los cuadros de hidrops');

// Los rangos declarados tienen que caber en lo que el formulario acepta:
// un cuadro que sortea 1.2 sobre un campo con tope 0.90 genera un caso que
// el editor recorta en silencio.
foreach (CaseProfile::SCENARIOS as $clave => $esc) {
    if (!isset($esc['ecochg'])) {
        continue;
    }
    $topes = ['sp_ap' => CaseBuilder::ECOCHG_SP_AP_MAX,
              'tasa' => CaseBuilder::ECOCHG_TASA_MAX,
              'rar_cond_ms' => CaseBuilder::ECOCHG_RAR_COND_MAX_MS];
    foreach ($esc['ecochg'] as $param => $rango) {
        t_true(isset($topes[$param]), "$clave: parámetro conocido ($param)");
        t_true($rango[0] <= $rango[1], "$clave/$param: el rango no está dado vuelta");
        t_true($rango[1] <= $topes[$param],
               "$clave/$param: el tope del cuadro cabe en el del formulario");
    }
}
