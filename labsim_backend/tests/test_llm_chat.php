<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/LlmChat.php';

/**
 * Lectura de la respuesta del LLM. Es la rama que más se rompe y no depende
 * de nuestro código sino del modelo configurado: los de razonamiento
 * contestan con un shape distinto.
 */

/** Corre $fn y devuelve el mensaje de la excepción, o '' si no lanzó. */
function excepcion(callable $fn): string
{
    try {
        $fn();
        return '';
    } catch (Throwable $e) {
        return $e->getMessage();
    }
}

$ok = ['choices' => [['index' => 0, 'message' => ['role' => 'assistant', 'content' => '{"antecedentes":[]}']]]];
t_eq(LlmChat::extractContent($ok, '{}', 'deepseek-chat', 400), '{"antecedentes":[]}',
    'Respuesta normal: devuelve el content');

// El body que devolvió deepseek-v4-flash: todo el presupuesto se fue en
// reasoning_content y content quedó vacío. El mensaje tiene que decir qué
// hacer, no volcar el body y dejar al docente adivinando.
$razonando = ['choices' => [['index' => 0, 'message' => [
    'role' => 'assistant', 'content' => '',
    'reasoning_content' => 'We need to produce an anamnesis for a 20-year-old woman...',
]]]];
$msg = excepcion(fn() => LlmChat::extractContent($razonando, '{"raw":1}', 'deepseek-v4-flash', 400));
t_true(strpos($msg, 'sin tokens razonando') !== false,
    'Modelo de razonamiento sin presupuesto: el error nombra la causa real');
t_true(strpos($msg, 'deepseek-v4-flash') !== false, 'Y nombra el modelo configurado');
t_true(strpos($msg, '400') !== false, 'Y el límite que se aplicó, que es lo que hay que subir');
t_true(strpos($msg, 'Body crudo') === false, 'Ya no vuelca el body: no le sirve a nadie acá');

// finish_reason "length" sin reasoning_content es el mismo problema.
$cortado = ['choices' => [['index' => 0, 'finish_reason' => 'length',
    'message' => ['role' => 'assistant', 'content' => '']]]];
t_true(strpos(excepcion(fn() => LlmChat::extractContent($cortado, '{}', 'x', 2000)), 'sin tokens') !== false,
    'finish_reason "length" con content vacío: misma causa, mismo mensaje');

// Cualquier otro shape raro sigue mostrando el body, que es lo único que
// se puede decir cuando no sabemos qué pasó.
$raro = ['choices' => []];
$msg = excepcion(fn() => LlmChat::extractContent($raro, '{"algo":"inesperado"}', 'x', 400));
t_true(strpos($msg, 'Body crudo') !== false, 'Shape desconocido: se muestra el body para diagnosticar');
t_true(strpos($msg, 'inesperado') !== false, 'Y el body va de verdad, no truncado a cero');
