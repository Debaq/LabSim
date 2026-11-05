<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseBuilder.php';
require_once __DIR__ . '/../src/LlmConfig.php';

/**
 * De dónde viene el paciente, en el prompt del chat (LlmConfig::historiaPrevia).
 * Sin esto el paciente del libro no sabía que traía la audiometría que la
 * ficha le muestra al alumno, y podía negarla.
 */

$historia = "{{-5470}} Neonatología: prematura de 33 semanas.\n{{-60}} Profesora jefe: se deriva a evaluación auditiva.";
$bloque = LlmConfig::historiaPrevia($historia, ['Audiometría']);
t_true(strpos($bloque, '- Hace 15 años: Neonatología: prematura de 33 semanas.') !== false,
    'Las llaves {{N}} se dicen como "hace N años"');
t_true(strpos($bloque, '- Hace 2 meses: Profesora jefe') !== false, '60 días = hace 2 meses');
t_true(strpos($bloque, 'Hace 2 semanas: te hicieron un examen de audición en cabina (audiometría), y traes el informe') !== false,
    'La audiometría que trae va al final, 14 días antes, como en la ficha');
t_true(strpos($bloque, '{{') === false, 'No queda ninguna llave a la vista del modelo');

t_eq(LlmConfig::historiaPrevia('', []), '', 'Sin historia ni audiometría el prompt queda como antes');
t_true(strpos(LlmConfig::historiaPrevia('', ['Audiometría']), 'audiometría') !== false,
    'Sin historia, la audiometría que trae igual se cuenta');
t_true(strpos(LlmConfig::historiaPrevia("Sin fecha legible.\n\n", []), '- Sin fecha legible.') !== false,
    'Una línea sin llave pasa tal cual y las vacías se saltan');
t_true(strpos(LlmConfig::historiaPrevia('', ['Audiometría'], true), 'al paciente le hicieron') !== false,
    'Con acompañantes se cuenta en tercera persona');
t_true(strpos(LlmConfig::historiaPrevia('{{-1}} Control.', []), '- Ayer: Control.') !== false, '1 día = ayer');
t_true(strpos(LlmConfig::historiaPrevia('{{-30}} Control.', []), '- Hace 4 semanas: Control.') !== false,
    '30 días = hace 4 semanas');
t_true(strpos(LlmConfig::historiaPrevia('{{-365}} Control.', []), '- Hace 12 meses: Control.') !== false,
    '365 días = hace 12 meses');

t_eq(LlmConfig::diasAudiometriaPrevia("{{-90}} Urgencia.\n{{-12}} ORL deriva."), 11,
    'La audiometría va después del otorrino que la pidió (mismo cálculo que la ficha)');
t_eq(LlmConfig::diasAudiometriaPrevia('{{-60}} Profesora jefe deriva.'), 14, 'Sin nada reciente: 14 días');
t_eq(LlmConfig::diasAudiometriaPrevia('{{-1}} ORL deriva ayer.'), 1, 'Nunca el mismo día de la cita');
t_eq(LlmConfig::diasAudiometriaPrevia(''), 14, 'Sin historia: 14 días');
t_true(strpos(LlmConfig::historiaPrevia('{{-12}} ORL deriva.', ['Audiometría']), '- Hace 11 días: te hicieron un examen de audición') !== false,
    'El chat dice la misma fecha que la ficha');

$dos = LlmConfig::historiaPrevia('', ['Audiometría', 'Impedanciometría', 'Inventado']);
t_true(strpos($dos, 'te hicieron un examen de audición en cabina (audiometría) y un examen del oído con una sonda') !== false
       && strpos($dos, 'traes los informes impresos') !== false, 'Varios exámenes: en plural, y lo desconocido no entra');

// Entrega de los informes por el chat
$conTrae = LlmConfig::historiaPrevia('', ['Audiometría', 'Impedanciometría']);
t_true(strpos($conTrae, '[ENTREGA: Audiometría, Impedanciometría]') !== false, 'El prompt dice cómo entregar, con los nombres exactos');
t_true(strpos(LlmConfig::historiaPrevia('{{-5}} ORL.', []), 'ENTREGA') === false, 'Sin nada que traer no hay marca');
[$t, $e] = LlmConfig::separarEntrega("Sí, aquí tiene los papeles. [ENTREGA: Audiometria, impedanciometría]", ['Audiometría', 'Impedanciometría']);
t_eq($t, 'Sí, aquí tiene los papeles.', 'La marca no llega a la burbuja');
t_eq($e, ['Audiometría', 'Impedanciometría'], 'Se reconoce aunque falte la tilde o cambie la mayúscula');
[, $e] = LlmConfig::separarEntrega('Tome. [ENTREGA: VEMP, Audiometría]', ['Audiometría']);
t_eq($e, ['Audiometría'], 'No entrega lo que no trae');
[, $e] = LlmConfig::separarEntrega('Todo lo que traigo. [ENTREGA: todos]', ['Audiometría', 'EOA']);
t_eq($e, ['Audiometría', 'EOA'], '"todos" entrega todo lo que trae');
[$t, $e] = LlmConfig::separarEntrega('Me hicieron una audiometría hace poco.', ['Audiometría']);
t_eq([$t, $e], ['Me hicieron una audiometría hace poco.', []], 'Contarlo no es entregarlo');

// Sin nada que entregar, el paciente dice que no los trajo (2026-11-05: la
// mamá de un lactante "entregaba" con palabras el tamizaje que contaba la
// historia y en la ficha no aparecía nada).
t_true(strpos(LlmConfig::historiaPrevia('{{-122}} Tamizaje al alta: refiere.', []), 'di que no los trajiste') !== false,
       'Con historia y nada que traer: dice que no los trajo');
t_true(strpos(LlmConfig::historiaPrevia('{{-122}} Tamizaje al alta: refiere.', [], true), 'no los trajeron') !== false,
       'Con acompañantes también');

// Exámenes que marcó el docente (ExamenesPrevios): en toda cita, cada uno en su día
require_once __DIR__ . '/../src/ExamenesPrevios.php';
$previos = ExamenesPrevios::fromForm([
    'prev_dias' => ['122', '', '30'],
    'prev_prueba' => ['Tamizaje auditivo al alta', '', 'Retamizaje, EOA [hospital]'],
    'prev_od' => ['Refiere', '', 'Pasa'],
    'prev_oi' => ['Refiere', '', 'Refiere'],
]);
t_eq(array_column($previos, 'prueba'), ['Tamizaje auditivo al alta', 'Retamizaje EOA hospital'],
     'Fila vacía fuera; sin comas ni corchetes (rompen la marca); del más antiguo al más reciente');
t_eq($previos[0]['dias'], -122, 'Días antes = {{-N}}');
$dup = ExamenesPrevios::fromForm(['prev_dias' => ['10', '5'], 'prev_prueba' => ['EOA', 'eoa'],
                                  'prev_od' => ['', ''], 'prev_oi' => ['', '']]);
t_eq(array_column($dup, 'prueba'), ['EOA', 'eoa (2)'], 'Dos con el mismo nombre se distinguen');
$caso = ['examenes_previos' => $previos];
$nombres = ExamenesPrevios::nombres($caso);
$conDocente = LlmConfig::historiaPrevia('{{-150}} Nace.', $nombres, true, ExamenesPrevios::delCaso($caso));
t_true(strpos($conDocente, '[ENTREGA: Tamizaje auditivo al alta, Retamizaje EOA hospital]') !== false,
       'Lo marcado por el docente se entrega con su nombre');
t_true(strpos($conDocente, 'Hace 4 meses: al paciente le hicieron «Tamizaje auditivo al alta»') !== false,
       'Cada uno en su día');
t_true(strpos($conDocente, 'no lo trajeron') !== false, 'Lo demás que sabe: no lo trajo');
[, $e] = LlmConfig::separarEntrega('Tome. [ENTREGA: tamizaje auditivo al alta]', $nombres);
t_eq($e, ['Tamizaje auditivo al alta'], 'separarEntrega acepta los nombres del docente');
$mismo = LlmConfig::historiaPrevia('', ['Audiometría'], false, [['dias' => -20, 'prueba' => 'Audiometría', 'OD' => '', 'OI' => '']]);
t_true(substr_count($mismo, '«Audiometría»') === 1 && strpos($mismo, 'examen de audición') === false,
       'Un nombre del docente igual a uno del libro no se cuenta dos veces');
