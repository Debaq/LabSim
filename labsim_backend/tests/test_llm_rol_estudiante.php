<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/LlmConfig.php';

/**
 * El paciente acepta que un tecnólogo no le dé el diagnóstico si se lo
 * explican bien, y uno difícil se puede calmar (LlmConfig::rolDelEstudiante).
 * La OIRS no lo cuenta como mala atención (LlmConfig::OIRS_ROL). Los dos van
 * fuera de la plantilla: una plantilla propia del curso no los pierde.
 */

$solo = LlmConfig::rolDelEstudiante(false);
$sala = LlmConfig::rolDelEstudiante(true);
t_true(strpos($solo, 'no médico') !== false && strpos($solo, 'lo aceptas') !== false,
    'El paciente acepta que el diagnóstico lo da el médico');
t_true(strpos($solo, 'te vas calmando de a poco') !== false, 'Un paciente molesto se puede calmar');
t_true(strpos($sala, 'lo aceptan') !== false && strpos($sala, 'se va calmando') !== false,
    'Con acompañantes, lo mismo para todos los presentes');
t_true(strpos($solo, '{{') === false && strpos($sala, '{{') === false, 'Sin placeholders sueltos');

$llmChat = (string) file_get_contents(__DIR__ . '/../public/api/llm_chat.php');
t_true(strpos($llmChat, 'LlmConfig::rolDelEstudiante($acompanado)') !== false,
    'llm_chat.php lo agrega al prompt del paciente');

t_true(strpos(LlmConfig::OIRS_ROL, 'NO es motivo') !== false, 'Declinar con respeto no es motivo para la OIRS');
t_true(strpos(LlmConfig::OIRS_ROL, 'no el ánimo con que llegó') !== false,
    'La OIRS juzga lo que hizo el estudiante, no cómo llegó el paciente');
