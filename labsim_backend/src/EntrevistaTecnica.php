<?php

declare(strict_types=1);

require_once __DIR__ . '/CaseBuilder.php';

/**
 * La entrevista con el paciente (chat, llm_chat_logs): lo que el alumno
 * preguntó. Hoy mide una cosa: si preguntó por el acúfeno. Sin esa pregunta
 * el alumno no sabe si corresponde la tinnitumetría (T03), y el chat es el
 * único lugar donde queda.
 *
 * Se reconoce por palabras (acúfeno, tinnitus, pitido, zumbido, silbido,
 * ruido en el oído...) en un mensaje del alumno que no sea la instrucción de
 * un examen ("van a sonar unos pitidos, levante la mano"). Probado contra el
 * chat del curso ETMP176: 155 preguntas y 11 instrucciones bien separadas.
 * Null si en la atención no hubo chat.
 */
final class EntrevistaTecnica
{
    /** Palabras del acúfeno. */
    private const ACUFENO = '/tinnit|ac[uú]fen|zumbi|\bpit(o|ido|ito)s?\b|pitodo|silbid|ruidos? (en|dentro de) (el|los|su|tu|sus)? ?o[ií]d|ruido en la cabeza/iu';
    /** Lo que delata una instrucción de examen, no una pregunta de la entrevista. */
    private const INSTRUCCION = '/van a sonar|vas? a escuchar|escuchar[aá] (unos|un|una)|levant(e|a|ar) la mano|levanatar|cuando escuche|cada vez que|le voy a (colocar|poner)|le colocar[eé]|le pondr[eé]|le podr[eé]|sonar[aá]|sonidos? fuertes|aud[ií]fonos|fonos|oliva|gomita|avise cuando/iu';

    /**
     * $mensajes: filas del chat de UNA atención en orden ('role' user |
     * assistant, 'content').
     */
    public static function evaluar(array $mensajes, array $caso): ?array
    {
        $preguntas = array_values(array_filter($mensajes, static function ($m) { return ($m['role'] ?? '') === 'user'; }));
        if (!$preguntas) {
            return null;
        }
        $pregunta = null;
        $respuesta = null;
        $n = count($mensajes);
        for ($i = 0; $i < $n; $i++) {
            $m = $mensajes[$i];
            if (($m['role'] ?? '') === 'user' && self::preguntaAcufeno((string) $m['content'])) {
                $pregunta = (string) $m['content'];
                for ($j = $i + 1; $j < $n; $j++) {
                    if (($mensajes[$j]['role'] ?? '') === 'assistant') {
                        $respuesta = (string) $mensajes[$j]['content'];
                        break;
                    }
                }
                break;
            }
        }
        $tiene = CaseBuilder::tinnitusPresente(is_array($caso['Tinnitus'] ?? null) ? $caso['Tinnitus'] : []);
        $reglas = [[
            'texto' => 'Se pregunta por el acúfeno (pito, zumbido, ruido en el oído).',
            'cumple' => $pregunta !== null,
            'detalle' => $pregunta !== null ? 'Lo preguntó.' : 'No se le preguntó: sin eso no se sabe si corresponde la tinnitumetría.',
            'detalle_docente' => ($tiene ? 'El paciente tiene acúfeno.' : 'El paciente no tiene acúfeno.')
                . ($pregunta !== null ? ' Preguntó: "' . self::corto($pregunta) . '"' . ($respuesta !== null ? ' — Respondió: "' . self::corto($respuesta) . '"' : '') : ''),
            'peso' => 2,
        ]];
        return ['hecha' => true, 'reglas' => $reglas, 'oidos' => [], 'observaciones' => [],
            'acufeno' => ['pregunto' => $pregunta !== null, 'paciente_tiene' => $tiene]];
    }

    /** Si un mensaje del alumno pregunta por el acúfeno (y no es la instrucción de un examen). */
    public static function preguntaAcufeno(string $texto): bool
    {
        return (bool) preg_match(self::ACUFENO, $texto) && !preg_match(self::INSTRUCCION, $texto);
    }

    private static function corto(string $t): string
    {
        $t = trim(preg_replace('/\s+/u', ' ', $t) ?? $t);
        return mb_strlen($t) > 140 ? mb_substr($t, 0, 137) . '…' : $t;
    }
}
