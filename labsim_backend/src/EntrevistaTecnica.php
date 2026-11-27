<?php

declare(strict_types=1);

require_once __DIR__ . '/CaseBuilder.php';

/**
 * La entrevista con el paciente (chat, llm_chat_logs): qué temas de la
 * anamnesis cubrió el alumno, con la lista del libro (H1, "La anamnesis").
 *
 * Un tema está cubierto si el alumno lo preguntó, o si el paciente lo contó
 * sin que se lo preguntaran (el dato se obtuvo igual). Se reconoce por
 * palabras en los mensajes, sin contar la instrucción de un examen ("van a
 * sonar unos pitidos, levante la mano"). Las palabras de cada tema se
 * probaron contra el chat real de ETMP176 y ETMP196 (2.312 mensajes).
 *
 * El acúfeno pesa el doble: sin esa pregunta no se sabe si corresponde la
 * tinnitumetría (T03). Los demás pesan 1. En el menor de 6 años la lista es
 * la del niño (embarazo y parto, tamizaje, lenguaje, otitis, familia).
 *
 * $completa = false (parámetro del curso) deja solo el acúfeno: hay cursos
 * donde la anamnesis no es lo que se evalúa. Null si no hubo chat.
 */
final class EntrevistaTecnica
{
    /** Tema => [texto de la regla, patrón]. Orden de la anamnesis del libro. */
    public const TEMAS = [
        'motivo' => ['Motivo de consulta: qué lo trae.',
            '/por ?qu[eé] (vino|viene|consulta|est[aá] aqu)|qu[eé] (lo|la|te|le) trae|motivo|en qu[eé] (le|lo|la|te) (puedo|podemos) ayudar|c[uú][eé]nteme|qu[eé] (le|te) (pasa|pas[oó]|sucede|ocurre)|raz[oó]n de (su |la )?(visita|consulta)|a qu[eé] (se debe|viene)|para qu[eé] (vino|viene)|qu[eé] (lo|la) hizo venir|cu[aá]l es (su|el) problema/iu'],
        'evolucion' => ['Desde cuándo y cómo empezó (de golpe, de a poco, fluctuante).',
            '/desde cu[aá]ndo|hace cu[aá]nto|cu[aá]nto tiempo|cu[aá]ndo (empez|comenz|not|part|se dio|le pas|inici)|de golpe|repentin|s[uú]bit|progresiv|de a poco|poco a poco|ha ido (empeorando|aumentando|disminuyendo)|ha empeorado|fue (r[aá]pido|lento)|va y viene|fluct/iu'],
        'lado' => ['Un oído o los dos.',
            '/(qu[eé]|cu[aá]l|en qu[eé]) o[ií]do|(un|uno de|ambos|los dos|cada) o[ií]dos?|derecho o (el )?izquierdo|izquierdo o (el )?derecho|de qu[eé] lado|en ambos|de los dos lados|un solo lado|ambos lados/iu'],
        'acufeno' => ['Acúfeno (pito, zumbido, ruido en el oído).',
            '/tinnit|ac[uú]fen|zumbi|\bpit(o|ido|ito)s?\b|pitodo|silbid|ruidos? (en|dentro de) (el|los|su|tu|sus)? ?o[ií]d|ruido en la cabeza/iu'],
        'vertigo' => ['Vértigo o mareo.',
            '/v[eé]rtig|mare(o|a|ado)|\bgira|da vueltas|equilibrio|inestab|se (cae|ha ca[ií]do)/iu'],
        'otalgia' => ['Dolor de oído.', '/dolor|duel[ea]|otalgia/iu'],
        'otorrea' => ['Secreción por el oído.', '/secreci|supur|\bpus\b|l[ií]quido|otorrea|le sale (algo|agua)|humed|flu[ij]/iu'],
        'plenitud' => ['Oído tapado o plenitud.', '/tapad|taponad|plenitud|presi[oó]n (en|dentro)|lleno|sensaci[oó]n de (oc|ta)|oclu/iu'],
        'otologicos' => ['Antecedentes otológicos: otitis, perforaciones, cirugías, audífonos, exámenes anteriores.',
            '/otitis|infecci|perforac|cirug|operad|operaci[oó]n|tubito|tubos? de ventilaci|colleras|aud[ií]fono(s)? (usa|tiene|ha usado|utiliza)|usa(do)? aud[ií]fono|ex[aá]men(es)? (anteriores|previos|antes)|se ha hecho (alg[uú]n|un|otros?|estos) (examen|ex[aá]menes|audiometr|estudio)|audiometr[ií]as? (antes|anteriores|previa)|le han hecho|ha (consultado|ido) (antes |al |a otro|con)/iu'],
        'morbidos' => ['Antecedentes mórbidos: enfermedades, traumatismos.',
            '/enfermedad|diabet|hipertens|presi[oó]n (alta|arterial)|cr[oó]nic|patolog|m[oó]rbid|antecedentes|problemas? de salud|condici[oó]n|traumatismo|golpe(s)? en la cabeza|meningitis|radioterapia|c[aá]ncer|accidente/iu'],
        'farmacos' => ['Fármacos que usa o usó (ototóxicos).',
            '/medicament|f[aá]rmac|remedio|pastilla|toma (alg|usted)|est[aá] tomando|tomando alg|antibi[oó]tic|ototox|quimio|tratamiento/iu'],
        'ruido' => ['Exposición a ruido (trabajo, recreación).',
            '/ruido (laboral|en (el|su) trabajo|fuerte|intenso)|ruidos fuertes|trabaj|expuest|exposici|ambiente ruidoso|m[uú]sica|maquinari|disparo|discoteca|conciert|protecci[oó]n auditiva|protector|ocupaci|a qu[eé] se dedica|ruidoso/iu'],
        'familiares' => ['Hipoacusia en la familia.',
            '/famili|hered|gen[eé]tic|(padres?|mam[aá]|pap[aá]|herman\w*|abuel\w*|t[ií]os?)\b[^?]{0,40}(o[ií]d|audici|sord|escuch|problem|enferm|aud[ií]fon)/iu'],
        'perinatal' => ['Embarazo, parto y tamizaje auditivo neonatal.',
            '/embaraz|gestaci|naci[oó]|nacimiento|parto|prematur|peso al nacer|incubadora|\buci\b|neonat|hospitaliz|ictericia|tamizaje|screening/iu'],
        'lenguaje' => ['Lenguaje y conducta auditiva (responde a su nombre, se asusta con ruidos).',
            '/\bhabla\b|palabras|balbuc|lenguaje|responde a su nombre|reacciona (a|con|cuando)|se asusta|responde a (los )?(ruidos|sonidos)/iu'],
    ];
    /** Frases que delatan otro sentido de las palabras de un tema. */
    private const EXCLUIR = [
        'otalgia' => '/no (le |te )?(va a |deber[ií]a )?doler|no duele|indolor|idoloro|si (es que )?algo le duele/iu',
        'morbidos' => '/famili|auditiv|o[ií]do/iu',
    ];
    public const ADULTO = ['motivo', 'evolucion', 'lado', 'acufeno', 'vertigo', 'otalgia', 'otorrea', 'plenitud',
        'otologicos', 'morbidos', 'farmacos', 'ruido', 'familiares'];
    public const NINO = ['motivo', 'perinatal', 'lenguaje', 'otologicos', 'familiares'];
    /** Edad (años) bajo la cual va la lista del niño. */
    public const EDAD_NINO = 6;

    /** Lo que delata una instrucción de examen, no una pregunta de la entrevista. */
    private const INSTRUCCION = '/van a sonar|vas? a escuchar|escuchar[aá] (unos|un|una)|levant(e|a|ar) la mano|levanatar|cuando escuche|cada vez que|le voy a (colocar|poner)|le colocar[eé]|le pondr[eé]|le podr[eé]|sonar[aá]|sonidos? fuertes|aud[ií]fonos|\bfonos\b|oliva|gomita|avise cuando/iu';

    /**
     * $mensajes: el chat de UNA atención en orden ('role' user | assistant,
     * 'content').
     */
    public static function evaluar(array $mensajes, array $caso, bool $completa = true, bool $fichaRevisada = false): ?array
    {
        if (!array_filter($mensajes, static function ($m) { return ($m['role'] ?? '') === 'user'; })) {
            return null;
        }
        $nino = (float) ($caso['edad'] ?? 30) < self::EDAD_NINO;
        $temas = $completa ? ($nino ? self::NINO : self::ADULTO) : ($nino ? [] : ['acufeno']);
        if (!$temas) {
            return null;
        }
        $tieneAcufeno = CaseBuilder::tinnitusPresente(is_array($caso['Tinnitus'] ?? null) ? $caso['Tinnitus'] : []);
        $reglas = [];
        $cubiertos = [];
        foreach ($temas as $tema) {
            [$pregunta, $respuesta, $contado] = self::buscar($mensajes, $tema);
            // Lo que la ficha ya dice no hace falta preguntarlo, si se leyó.
            $enFicha = $pregunta === null && $contado === null && $fichaRevisada && self::enFicha($caso, $tema);
            $cubierto = $pregunta !== null || $contado !== null || $enFicha;
            $cubiertos[$tema] = $cubierto;
            $doc = $pregunta !== null
                ? 'Preguntó: "' . self::corto($pregunta) . '"' . ($respuesta !== null ? ' — Respondió: "' . self::corto($respuesta) . '"' : '')
                : ($contado !== null ? 'El paciente: "' . self::corto($contado) . '"' : '');
            if ($tema === 'acufeno') {
                $doc = ($tieneAcufeno ? 'El paciente tiene acúfeno. ' : 'El paciente no tiene acúfeno. ') . $doc;
            }
            $reglas[] = [
                'texto' => self::TEMAS[$tema][0],
                'cumple' => $cubierto,
                'detalle' => $pregunta !== null ? 'Lo preguntó.' : ($contado !== null ? 'Lo contó el paciente.' : ($enFicha ? 'Lo leyó en la ficha.'
                    : ($tema === 'acufeno' ? 'No se le preguntó: sin eso no se sabe si corresponde la tinnitumetría.' : 'No se preguntó.'))),
                'detalle_docente' => trim($doc),
                'peso' => $tema === 'acufeno' ? 2 : 1,
            ];
        }
        return ['hecha' => true, 'reglas' => $reglas, 'oidos' => [], 'observaciones' => [],
            'temas' => $cubiertos, 'nino' => $nino,
            'acufeno' => ['pregunto' => $cubiertos['acufeno'] ?? null, 'paciente_tiene' => $tieneAcufeno]];
    }

    /**
     * Si la ficha del paciente ya trae ese tema: los datos del nacimiento
     * (lactante) o la historia clínica escrita por el docente.
     */
    public static function enFicha(array $caso, string $tema): bool
    {
        if ($tema === 'perinatal' && is_array($caso['nacimiento'] ?? null) && $caso['nacimiento'] !== []) {
            return true;
        }
        $hc = $caso['historia_clinica'] ?? '';
        $texto = is_array($hc) ? json_encode($hc, JSON_UNESCAPED_UNICODE) : (string) $hc;
        return $texto !== '' && (bool) preg_match(self::TEMAS[$tema][1], $texto)
            && !(isset(self::EXCLUIR[$tema]) && preg_match(self::EXCLUIR[$tema], $texto));
    }

    /** Si un mensaje del alumno pregunta por ese tema (y no es la instrucción de un examen). */
    public static function pregunta(string $tema, string $texto): bool
    {
        return (bool) preg_match(self::TEMAS[$tema][1], $texto)
            && !preg_match(self::INSTRUCCION, $texto)
            && !(isset(self::EXCLUIR[$tema]) && preg_match(self::EXCLUIR[$tema], $texto));
    }

    /** Compatibilidad: ¿pregunta por el acúfeno? */
    public static function preguntaAcufeno(string $texto): bool
    {
        return self::pregunta('acufeno', $texto);
    }

    /** [pregunta del alumno, respuesta del paciente, lo que el paciente contó sin pregunta] */
    private static function buscar(array $mensajes, string $tema): array
    {
        $n = count($mensajes);
        $contado = null;
        for ($i = 0; $i < $n; $i++) {
            $m = $mensajes[$i];
            $texto = (string) ($m['content'] ?? '');
            if (($m['role'] ?? '') === 'user' && self::pregunta($tema, $texto)) {
                $resp = null;
                for ($j = $i + 1; $j < $n; $j++) {
                    if (($mensajes[$j]['role'] ?? '') === 'assistant') {
                        $resp = (string) $mensajes[$j]['content'];
                        break;
                    }
                }
                return [$texto, $resp, null];
            }
            if ($contado === null && ($m['role'] ?? '') === 'assistant' && preg_match(self::TEMAS[$tema][1], $texto)
                && !(isset(self::EXCLUIR[$tema]) && preg_match(self::EXCLUIR[$tema], $texto))) {
                $contado = $texto;
            }
        }
        return [null, null, $contado];
    }

    private static function corto(string $t): string
    {
        $t = trim(preg_replace('/\s+/u', ' ', $t) ?? $t);
        return mb_strlen($t) > 140 ? mb_substr($t, 0, 137) . '…' : $t;
    }
}
