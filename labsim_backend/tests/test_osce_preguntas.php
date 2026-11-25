<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/OscePreguntas.php';

/**
 * Estación de preguntas del OSCE: corrección de alternativas, GIFT,
 * respuesta de la IA, barajado por alumno y ventana de tiempo de la tablet.
 */

// -- Alternativas ---------------------------------------------------------
t_eq(OscePreguntas::puntajeAlternativa([2], [2], 2.0), 2.0, 'Una correcta, acierta: todo');
t_eq(OscePreguntas::puntajeAlternativa([2], [1], 2.0), 0.0, 'Una correcta, falla: nada');
t_eq(OscePreguntas::puntajeAlternativa([2], [2, 1], 2.0), 0.0, 'Una correcta: marcar dos no vale');
t_eq(OscePreguntas::puntajeAlternativa([2], [], 2.0), 0.0, 'Sin marcar: 0');
t_eq(OscePreguntas::puntajeAlternativa([0, 2], [0, 2], 2.0), 2.0, 'Varias correctas, todas: completo');
t_eq(OscePreguntas::puntajeAlternativa([0, 2], [0], 2.0), 1.0, 'Varias: la mitad de las correctas = la mitad');
t_eq(OscePreguntas::puntajeAlternativa([0, 2], [0, 1], 2.0), 0.0, 'Varias: una buena y una mala se anulan');
t_eq(OscePreguntas::puntajeAlternativa([0, 2], [1, 3], 2.0), 0.0, 'Varias: nunca bajo 0');
t_eq(OscePreguntas::puntajeAlternativa([0, 1, 2], [0, 1, 2, 3], 3.0), 2.0, 'Marcar todo no regala puntaje');

// -- Editor ---------------------------------------------------------------
$q = OscePreguntas::limpiar(['tipo' => 'alternativa', 'enunciado' => '¿Polaridad?', 'puntaje' => '1,5',
                             'opciones' => "*Alternada\n\nRarefacción\n* Condensación"]);
t_eq([json_decode($q['alternativas'], true), json_decode($q['clave'], true), $q['puntaje']],
     [['Alternada', 'Rarefacción', 'Condensación'], [0, 2], 1.5], 'Las correctas se marcan con *');
$falla = static function (array $in): bool {
    try {
        OscePreguntas::limpiar($in);
    } catch (InvalidArgumentException $e) {
        return true;
    }
    return false;
};
t_true($falla(['tipo' => 'alternativa', 'enunciado' => 'x', 'opciones' => "a\nb"]), 'Sin correcta marcada: se rechaza');
t_true($falla(['tipo' => 'desarrollo', 'enunciado' => 'x', 'pauta' => '']), 'Desarrollo sin pauta: se rechaza (la IA no tendría con qué)');
$dec = ['opciones' => ['A', 'B', 'C'], 'correctas' => [1]];
t_eq(OscePreguntas::opcionesTexto($dec), "A\n*B\nC", 'El editor vuelve a mostrar el *');

// -- GIFT -----------------------------------------------------------------
$gift = <<<'G'
// comentario
$CATEGORY: $course$/OSCE

::P1:: ¿Qué polaridad indica el protocolo del PEATC? {
  =Alternada
  ~Rarefacción#No es la del protocolo
  ~Condensación
}

::P2:: Marque las referencias del montaje {~%50%Mastoide derecha ~%50%Mastoide izquierda ~%-100%Vértex}

La onda V se usa para el umbral {T}

::P4:: Explique por qué se usa tasa 81,1 en sospecha de neuropatía {}

::P5:: Empareje {=a -> 1 =b -> 2}

Ventana de 10 ms \{no 10 s\} {=Correcto ~Incorrecto}
G;
$r = OscePreguntas::leerGift($gift);
t_eq(count($r['preguntas']), 5, 'GIFT: 5 preguntas útiles');
t_eq(count($r['errores']), 1, 'GIFT: el emparejamiento no se importa y se avisa');
$p1 = $r['preguntas'][0];
t_eq([$p1['tipo'], $p1['opciones'], $p1['correctas']], ['alternativa', ['Alternada', 'Rarefacción', 'Condensación'], [0]],
     'GIFT: = correcta, ~ incorrecta, sin el feedback #');
t_eq($p1['enunciado'], '¿Qué polaridad indica el protocolo del PEATC?', 'GIFT: sin el título ::P1::');
t_eq($r['preguntas'][1]['correctas'], [0, 1], 'GIFT: ~%50% cuenta como correcta, ~%-100% no');
t_eq([$r['preguntas'][2]['opciones'], $r['preguntas'][2]['correctas']], [['Verdadero', 'Falso'], [0]], 'GIFT: {T} = verdadero/falso');
t_eq($r['preguntas'][3]['tipo'], 'desarrollo', 'GIFT: {} = desarrollo');
t_eq($r['preguntas'][4]['enunciado'], 'Ventana de 10 ms {no 10 s}', 'GIFT: llaves escapadas quedan en el enunciado');

// -- Respuesta de la IA ---------------------------------------------------
t_eq(OscePreguntas::parsearIa('{"puntaje": 1.3, "justificacion": "Bien."}', 2.0), ['puntaje' => 1.5, 'justificacion' => 'Bien.'],
     'IA: se redondea a 0,5');
t_eq(OscePreguntas::parsearIa("```json\n{\"puntaje\": 9, \"justificacion\": \"x\"}\n```", 2.0)['puntaje'], 2.0,
     'IA: con bloque de código y sobre el máximo, se recorta');
t_eq(OscePreguntas::parsearIa('Claro: {"puntaje": -1, "justificacion": ""}', 2.0)['puntaje'], 0.0, 'IA: con texto alrededor y negativo');
t_eq(OscePreguntas::parsearIa('no sé', 2.0), null, 'IA: sin JSON = null');
t_eq(OscePreguntas::parsearIa('{"justificacion": "x"}', 2.0), null, 'IA: sin puntaje = null');

// -- Barajado por alumno ----------------------------------------------------
$o1 = OscePreguntas::ordenOpciones(15, 3, 5);
t_eq($o1, OscePreguntas::ordenOpciones(15, 3, 5), 'El orden de un alumno es siempre el mismo');
$s = $o1;
sort($s);
t_eq($s, [0, 1, 2, 3, 4], 'El orden es una permutación');
$distintos = 0;
for ($pid = 1; $pid <= 17; $pid++) {
    if (OscePreguntas::ordenOpciones($pid, 3, 5) !== [0, 1, 2, 3, 4]) {
        $distintos++;
    }
}
t_true($distintos >= 14, 'Casi nadie ve las opciones en el orden original');

// -- Ventana de la tablet -------------------------------------------------
$cfg = ['estaciones' => 6, 'vueltas' => 3, 'duracion_s' => 480, 'pausa_s' => 120, 'pausa_vueltas_s' => 600];
$alumno = ['vuelta' => 0, 'puesto' => 5];   // parte en la estación 6; la 2 (índice 1) le toca en el tiempo 2
$v = Osce::ventana($cfg, $alumno, 1);
t_eq($v, ['slot' => 2, 'inicio_s' => 1200, 'fin_s' => 1680], 'Ventana: estación 2 del alumno que parte en la 6');
t_true(Osce::enVentana($cfg, $alumno, 1, 1100), 'Puede escribir su código durante el cambio previo');
t_true(!Osce::enVentana($cfg, $alumno, 1, 1000), 'Antes del cambio previo: no');
t_true(Osce::enVentana($cfg, $alumno, 1, 1700), 'Gracia tras el timbre para que la tablet entregue');
t_true(!Osce::enVentana($cfg, $alumno, 1, 1900), 'Pasada la gracia: no');
