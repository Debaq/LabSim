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
$msg = excepcion(fn() => LlmChat::extractContent($razonando, '{"raw":1}', 'deepseek-v4-flash', 400,
    'Máximo de tokens del borrador de anamnesis'));
t_true(strpos($msg, 'sin tokens razonando') !== false,
    'Modelo de razonamiento sin presupuesto: el error nombra la causa real');
t_true(strpos($msg, 'deepseek-v4-flash') !== false, 'Y nombra el modelo configurado');
t_true(strpos($msg, '400') !== false, 'Y el límite que se aplicó, que es lo que hay que subir');
t_true(strpos($msg, 'Body crudo') === false, 'Ya no vuelca el body: no le sirve a nadie acá');
t_true(strpos($msg, 'borrador de anamnesis') !== false,
    'Y nombra el campo que hay que subir: hay más de uno y subir el que no es no arregla nada');

// Sin decir la tarea, el mensaje apunta al campo del chat, que es el default.
$msg = excepcion(fn() => LlmChat::extractContent($razonando, '{}', 'x', 400));
t_true(strpos($msg, 'Máximo de tokens por respuesta') !== false,
    'Sin rótulo, el error apunta al campo del chat');

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

// ---------------------------------------------------------------------
// Reintento del borrador de anamnesis cuando el modelo razona de más.
// ---------------------------------------------------------------------

require_once __DIR__ . '/../src/AnamnesisDraft.php';

t_eq(AnamnesisDraft::retryBudget(2000), 6000, 'El reintento pide el triple');
t_eq(AnamnesisDraft::retryBudget(6000), 12000, 'Con el default nuevo, el reintento llega al techo');
t_eq(AnamnesisDraft::retryBudget(10000), AnamnesisDraft::MAX_TOKENS_REINTENTO,
    'El triple se corta en el techo, no se dispara');
t_eq(AnamnesisDraft::retryBudget(20000), 20000,
    'Si ya se pidió más que el techo, no se reintenta con menos');
t_true(AnamnesisDraft::retryBudget(AnamnesisDraft::MAX_TOKENS_REINTENTO) <= AnamnesisDraft::MAX_TOKENS_REINTENTO,
    'En el techo el reintento no aporta nada y quien llama corta');

// La falla de presupuesto tiene clase propia: es la única que se arregla
// reintentando, y distinguirla por el texto del mensaje sería frágil.
$razonando2 = ['choices' => [['message' => ['content' => '', 'reasoning_content' => 'pensando...']]]];
$clase = '';
try {
    LlmChat::extractContent($razonando2, '{}', 'm', 400);
} catch (Throwable $e) {
    $clase = get_class($e);
}
t_eq($clase, 'LlmBudgetException', 'Sin presupuesto lanza LlmBudgetException');
t_true(is_subclass_of('LlmBudgetException', 'RuntimeException'),
    'Y sigue siendo RuntimeException: quien no la distingue la sigue atrapando igual');

$otro = ['choices' => []];
$clase = '';
try {
    LlmChat::extractContent($otro, '{}', 'm', 400);
} catch (Throwable $e) {
    $clase = get_class($e);
}
t_eq($clase, 'RuntimeException', 'Un shape raro NO es falla de presupuesto: reintentar no lo arregla');

// El timeout de esta tarea tiene que ser mayor que el del chat: el chat lo
// mira un alumno en vivo, el borrador lo espera un docente que apretó un
// botón.
t_true(AnamnesisDraft::TIMEOUT_S > LlmChat::TIMEOUT_DEFAULT_S,
    'El borrador espera más que el chat con el paciente');

// ---------------------------------------------------------------------
// Opciones por tarea: cada una pisa lo que la config fija para el chat.
// ---------------------------------------------------------------------

$op = AnamnesisDraft::opciones(6000, 'deepseek-chat');
t_eq($op['max_tokens'], 6000, 'El presupuesto pedido viaja en las opciones');
t_eq($op['timeout'], AnamnesisDraft::TIMEOUT_S, 'Y su propia espera');
t_eq($op['campo_tokens'], 'Máximo de tokens del borrador de anamnesis',
    'Y el rótulo del campo que hay que subir, que no es el del chat');
t_eq($op['model'], 'deepseek-chat',
    'Y su propio modelo: la tarea no tiene por qué usar el del chat con el paciente');

$vacias = LlmChat::opcionesTarea([]);
t_eq($vacias['model'], null, 'Sin opciones, el modelo lo pone la configuración general');
t_eq($vacias['max_tokens'], null, 'Y el presupuesto también');
t_eq($vacias['campo_tokens'], 'Máximo de tokens por respuesta',
    'El rótulo por defecto apunta al campo del chat');

// "Vacío = usa el general" es la semántica del campo en Admin -> IA
// Paciente: un modelo en blanco no puede llegar a la API como modelo "".
foreach (['', '   '] as $blanco) {
    t_eq(LlmChat::opcionesTarea(['model' => $blanco])['model'], null,
        'Un modelo en blanco cae al general, no viaja vacío a la API');
}
t_eq(LlmChat::opcionesTarea(['model' => ' deepseek-chat '])['model'], 'deepseek-chat',
    'El modelo se recorta: un espacio pegado no es otro modelo');
