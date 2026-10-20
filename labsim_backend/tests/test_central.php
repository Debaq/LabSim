<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseBuilder.php';
require_once __DIR__ . '/../src/CaseProfile.php';
require_once __DIR__ . '/../src/CaseForm.php';

/**
 * Vía central (latencia media y tardía): el bloque `Central` del caso.
 *
 * Como el ECochG, el cliente (src/abr/cortical.py) no registra nada si el
 * caso no trae el bloque. Lo que se protege acá es que llegue, que vuelva
 * al formulario y que los cuadros no escriban fuera de los topes.
 */

// --------------------------------------------- espejo del cliente (Python)

$py = (string) file_get_contents(__DIR__ . '/../../src/abr/cortical.py');
preg_match('/^CASE_DEFAULTS = \{(.*?)^\}/ms', $py, $m);
preg_match_all("/^    '([a-z0-9_]+)':/m", $m[1] ?? '', $claves);
t_eq($claves[1], array_keys(CaseBuilder::CENTRAL_DEFAULTS),
     'Central: las claves del bloque son las mismas que lee el cliente');
foreach (CaseBuilder::CENTRAL_OPTIONS as $clave => $opciones) {
    t_eq($opciones[0], CaseBuilder::CENTRAL_DEFAULTS[$clave],
         "Central {$clave}: el default es la primera opción (la sana)");
}
foreach (CaseBuilder::CENTRAL_LIMITS as $clave => $rango) {
    t_true(CaseBuilder::CENTRAL_DEFAULTS[$clave] >= $rango[0]
           && CaseBuilder::CENTRAL_DEFAULTS[$clave] <= $rango[1],
           "Central {$clave}: el default está dentro del rango");
    t_true(isset(CaseBuilder::CENTRAL_DEFAULTS[$clave]), "Central {$clave}: tiene default");
}

// ------------------------------------------------------------ ida y vuelta

$v = CaseBuilder::caseDataToForm(['Central' => ['mlr_hemisferio' => 'derecho',
                                                'mlr_reduccion' => 0.6]]);
t_eq($v['central']['mlr_hemisferio'], 'derecho', 'Central: el hemisferio vuelve al formulario');
t_eq($v['central']['mlr_reduccion'], '0.6', 'Central: la reducción vuelve al formulario');
t_eq($v['central']['estado'], 'despierto', 'Central: lo que no estaba vuelve sano');

// Caso viejo, sin el bloque: el formulario muestra una vía sana (guardarlo
// desde el editor lo escribe).
$v = CaseBuilder::caseDataToForm([]);
t_eq($v['central']['p300_retardo_ms'], '0', 'Central: caso viejo, el formulario dibuja una vía sana');

$parseado = CaseForm::parseCentral(['central' => [
    'estado' => 'hipnotizado', 'mlr_hemisferio' => 'izquierdo',
    'mlr_reduccion' => '3', 'p1_retardo_ms' => '', 'p300_retardo_ms' => '45',
]]);
t_eq($parseado['estado'], 'despierto', 'Central: una opción inválida cae al default');
t_eq($parseado['mlr_hemisferio'], 'izquierdo', 'Central: una opción válida se guarda');
t_eq($parseado['mlr_reduccion'], 1.0, 'Central: un número fuera de rango se recorta');
t_eq($parseado['p1_retardo_ms'], 0.0, 'Central: un campo vacío toma el default');
t_eq($parseado['p300_retardo_ms'], 45.0, 'Central: el retardo se guarda');
t_eq(array_keys($parseado), array_keys(CaseBuilder::CENTRAL_DEFAULTS),
     'Central: el bloque guardado trae todas las claves');

// buildCaseData lo deja en 'Central' (y vacío si el form no lo trae, como
// un caso de create_a.py: así el cliente no registra).
$src = (string) file_get_contents(__DIR__ . '/../src/CaseBuilder.php');
t_true(strpos($src, "'Central' => \$form['central'] ?? []") !== false,
       'Central: buildCaseData guarda el bloque bajo Central');

// ------------------------------------------------------------- los cuadros

t_true(isset(CaseProfile::CENTRAL_SCENARIOS['central_normal']),
       'Central: existe el cuadro sin compromiso');
t_eq(CaseProfile::CENTRAL_SCENARIOS['central_normal']['central'], [],
     'Central: el cuadro normal no toca nada');
foreach (CaseProfile::CENTRAL_SCENARIOS as $clave => $esc) {
    t_true(!empty($esc['label']), "Cuadro central {$clave}: tiene rótulo");
    t_true(is_array($esc['edad']) && count($esc['edad']) === 2, "Cuadro central {$clave}: rango de edad");
    foreach ($esc['central'] as $param => $regla) {
        t_true(array_key_exists($param, CaseBuilder::CENTRAL_DEFAULTS),
               "Cuadro central {$clave}: {$param} es un campo del bloque");
        if (isset(CaseBuilder::CENTRAL_OPTIONS[$param])) {
            foreach ($regla as $op) {
                t_true(in_array($op, CaseBuilder::CENTRAL_OPTIONS[$param], true),
                       "Cuadro central {$clave}: {$param}={$op} es una opción válida");
            }
            continue;
        }
        $rango = CaseBuilder::CENTRAL_LIMITS[$param];
        t_true($regla[0] <= $regla[1] && $regla[0] >= $rango[0] && $regla[1] <= $rango[1],
               "Cuadro central {$clave}: {$param} dentro de los topes del formulario");
    }
}
$acv = CaseProfile::CENTRAL_SCENARIOS['acv_temporal']['central'];
t_true(!in_array('ninguno', $acv['mlr_hemisferio'], true),
       'El ACV temporal siempre compromete un hemisferio (efecto electrodo)');
t_true($acv['mlr_reduccion'][0] >= 0.5,
       'El ACV temporal llega al criterio de efecto electrodo (50 %)');
