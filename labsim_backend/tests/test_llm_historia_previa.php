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
