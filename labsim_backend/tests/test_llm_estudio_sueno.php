<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/LlmConfig.php';

/**
 * El estudio de sueño en el prompt del chat (LlmConfig::estudioDeSueno): el
 * paciente viene a pasar la noche, preparado como le dijo la secretaria.
 */

$solo = LlmConfig::estudioDeSueno('Polisomnografía', false);
$sala = LlmConfig::estudioDeSueno('Polisomnografía y titulación de CPAP', true);
foreach (['pijama', 'toda la noche', 'dan sueño', 'orinar', 'alcohol', 'corazón', 'peso', 'drogas'] as $palabra) {
    t_true(mb_stripos($solo, $palabra) !== false, "Solo: el bloque habla de \"{$palabra}\"");
    t_true(mb_stripos($sala, $palabra) !== false, "Con acompañante: el bloque habla de \"{$palabra}\"");
}
t_true(strpos($solo, 'Vienes') !== false && strpos($sala, 'El paciente viene') !== false, 'Segunda persona solo; tercera con acompañante');
t_true(strpos($solo, 'ni lo mencionas') !== false, 'No adelanta lo del baño si no se lo piden');
t_eq(LlmConfig::estudioDeSueno('Titulación de CPAP', false) !== '', true, 'La titulación también es de noche');
t_eq(LlmConfig::estudioDeSueno('Poligrafía respiratoria', false), '', 'La poligrafía es en la casa: nada');
t_eq(LlmConfig::estudioDeSueno('Audiometría', false), '', 'Otro examen: nada');
$llmChat = (string) file_get_contents(__DIR__ . '/../public/api/llm_chat.php');
t_true(strpos($llmChat, 'LlmConfig::estudioDeSueno($procedimiento, $acompanado)') !== false, 'llm_chat lo agrega al prompt');
