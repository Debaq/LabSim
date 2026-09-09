<?php

declare(strict_types=1);

/**
 * Quiénes vienen a la consulta: el paciente y quienes lo acompañan.
 *
 * Hasta ahora un caso era exactamente una persona y el chat era 1 a 1. Eso
 * deja fuera la mitad de la clínica real: el lactante no habla y todo lo
 * cuenta la madre; el adulto mayor que niega su hipoacusia lo desmiente la
 * esposa que sí la nota. Ese contraste entre lo que el paciente dice y lo que el acompañante
 * afirma ES el hallazgo clínico, y sin acompañantes no existe.
 *
 * Este archivo es el elenco: quién es cada uno, qué sabe y cómo se
 * comporta. NO decide quién contesta cada pregunta -- eso lo resuelve el
 * modelo leyendo la conversación (ver LlmConfig::buildSalaPrompt y
 * llm_chat.php); acá solo se LEE a quién le atribuyó cada frase
 * (intervenciones()), que es distinto y sí tiene que ser determinista. Si el alumno escribe "mamita, ¿su hijo escucha bien?",
 * contesta la madre porque el mensaje lo dice, no porque una tabla de
 * palabras clave lo haya clasificado.
 *
 * Un caso guardado antes de esto no tiene sala: desde($data) le arma una de
 * una sola persona a partir de los campos que ya existían
 * (PatientBehavior/PatientDisposition), así que nada se rompe y el chat
 * viejo sigue comportándose igual.
 */
final class Sala
{
    public const VERSION = 1;

    /**
     * Roles posibles. `paciente` es un rol más y no una entidad aparte: es
     * lo que permite tratar a todos igual y que un acompañante conteste una
     * pregunta que iba dirigida al paciente.
     */
    public const ROLES = [
        'paciente' => 'Paciente',
        'madre' => 'Madre',
        'padre' => 'Padre',
        'conyuge' => 'Cónyuge / pareja',
        'hijo' => 'Hijo/a',
        'abuelo' => 'Abuelo/a',
        'cuidador' => 'Cuidador/a',
        'hermano' => 'Hermano/a',
        'otro' => 'Otro acompañante',
    ];

    /**
     * Qué puede contar el propio paciente según su edad. No es un detalle
     * de ambientación: define de quién sale el dato clínico y, por lo
     * tanto, a quién tiene que terminar preguntándole el alumno. Va como
     * texto al prompt de la sala.
     */
    public const CAP_NULO = 'nulo';             // 0-2: no habla; solo conducta observable
    public const CAP_MINIMO = 'minimo';         // 3-5: nombre, "me duele acá", sí/no
    public const CAP_PARCIAL = 'parcial';       // 6-13: síntomas y colegio, no fechas ni fármacos
    public const CAP_CASI_TOTAL = 'casi_total'; // 14-17: casi todo, pero no lo perinatal
    public const CAP_TOTAL = 'total';           // adulto

    public const CAPACIDAD_DESC = [
        self::CAP_NULO => 'No habla: es una guagua. No produce frases. Lo suyo es conducta observable (llanto, sonrisa, girar la cabeza hacia un ruido, sacarse el fono, buscar a su mamá), y se escribe entre paréntesis.',
        self::CAP_MINIMO => 'Habla poco y como niño pequeño: dice su nombre, su edad si la sabe, "me duele acá", "sí", "no". No maneja fechas, ni nombres de remedios, ni antecedentes.',
        self::CAP_PARCIAL => 'Habla como niño de escuela: cuenta lo que siente, lo que le pasa en el colegio, si escucha mal la tele. No sabe desde cuándo con precisión, ni qué remedios toma, ni nada de su embarazo o su parto.',
        self::CAP_CASI_TOTAL => 'Habla como adolescente: cuenta casi todo lo suyo con sus palabras. De su embarazo, su parto y sus primeros años solo sabe lo que le han contado, y no siempre bien.',
        self::CAP_TOTAL => 'Habla como adulto: puede contar su historia completa, hasta donde la recuerde y hasta donde tenga conciencia de su problema.',
    ];

    /** Umbral de conciencia bajo el cual el paciente niega o minimiza lo suyo. */
    public const CONCIENCIA_BAJA = 40;

    /** Umbral de confiabilidad bajo el cual el relato es impreciso. */
    public const CONFIABILIDAD_BAJA = 40;

    public const RASGOS_DEFAULT = [
        'interrumpe' => 20,
        'conciencia' => 80,
        'confiabilidad' => 80,
    ];

    /**
     * El rasgo `interrumpe` dicho en palabras: al modelo hay que decirle
     * cómo se comporta esta persona en la conversación, no pasarle un
     * número para que lo interprete a su gusto.
     */
    public const INTERRUMPE_DESC = [
        'nada' => 'Espera su turno: habla solo cuando le hablan a ella.',
        'poco' => 'Rara vez se mete: solo si le preguntan al paciente algo que ella sabe y él no.',
        'medio' => 'Se mete cuando el paciente no sabe, se equivoca o minimiza algo que a ella le consta.',
        'mucho' => 'Tiende a contestar por el paciente, incluso cuando la pregunta era para él. Si le piden que lo deje contestar, hace el intento, pero al poco rato vuelve a meterse.',
    ];

    // -----------------------------------------------------------------
    // Modelo
    // -----------------------------------------------------------------

    /** Capacidad de relato que le corresponde a una edad en años. */
    public static function capacidad(int $edad): string
    {
        if ($edad <= 2) {
            return self::CAP_NULO;
        }
        if ($edad <= 5) {
            return self::CAP_MINIMO;
        }
        if ($edad <= 13) {
            return self::CAP_PARCIAL;
        }
        if ($edad <= 17) {
            return self::CAP_CASI_TOTAL;
        }
        return self::CAP_TOTAL;
    }

    /** Tramo de INTERRUMPE_DESC que le corresponde a un 0-100. */
    public static function nivelInterrupcion(int $valor): string
    {
        if ($valor <= 10) {
            return 'nada';
        }
        if ($valor <= 35) {
            return 'poco';
        }
        if ($valor <= 65) {
            return 'medio';
        }
        return 'mucho';
    }

    /**
     * Normaliza una persona suelta contra los defaults. Las claves
     * desconocidas se descartan: esto viene de cases.data, que un docente
     * puede haber editado a mano desde una versión anterior del formulario.
     */
    public static function normalizePersona(array $p, int $indice = 0): array
    {
        $rol = (string) ($p['rol'] ?? 'otro');
        if (!isset(self::ROLES[$rol])) {
            $rol = 'otro';
        }
        $esPaciente = (bool) ($p['es_paciente'] ?? ($rol === 'paciente'));

        return [
            'id' => self::safeId((string) ($p['id'] ?? ''), $indice),
            'rol' => $rol,
            'nombre' => trim((string) ($p['nombre'] ?? '')),
            'edad' => max(0, (int) ($p['edad'] ?? 0)),
            'genero' => (int) ($p['genero'] ?? 0) === 1 ? 1 : 0,
            'es_paciente' => $esPaciente,
            'informante' => (bool) ($p['informante'] ?? false),
            'interrumpe' => self::pct($p['interrumpe'] ?? self::RASGOS_DEFAULT['interrumpe']),
            'conciencia' => self::pct($p['conciencia'] ?? self::RASGOS_DEFAULT['conciencia']),
            'confiabilidad' => self::pct($p['confiabilidad'] ?? self::RASGOS_DEFAULT['confiabilidad']),
            'version' => trim((string) ($p['version'] ?? '')),
            'comportamiento' => trim((string) ($p['comportamiento'] ?? '')),
            'disposicion' => max(-2, min(2, (int) ($p['disposicion'] ?? 0))),
        ];
    }

    /**
     * Normaliza la sala completa y deja invariantes que el resto del código
     * da por ciertas: hay exactamente un paciente, hay exactamente un
     * informante principal, y todos los ids son distintos.
     */
    public static function normalize(array $sala): array
    {
        $personas = [];
        $i = 0;
        foreach ((array) ($sala['personas'] ?? []) as $p) {
            if (!is_array($p)) {
                continue;
            }
            $personas[] = self::normalizePersona($p, $i);
            $i++;
        }
        $personas = self::dedupIds($personas);

        // Un solo paciente: si el formulario mandó dos marcados (o ninguno),
        // gana el primero, y si no hay ninguno se promueve el primero de la
        // lista -- una sala sin paciente no es representable río abajo.
        $vistoPaciente = false;
        foreach ($personas as $k => $p) {
            if ($p['es_paciente'] && !$vistoPaciente) {
                $vistoPaciente = true;
                continue;
            }
            if ($p['es_paciente']) {
                $personas[$k]['es_paciente'] = false;
            }
        }
        if (!$vistoPaciente && $personas) {
            $personas[0]['es_paciente'] = true;
            $personas[0]['rol'] = 'paciente';
        }

        $personas = self::asignarInformante($personas);

        return [
            'version' => self::VERSION,
            'personas' => array_values($personas),
        ];
    }

    /**
     * Deja un único informante principal: quien lleva la voz cantante, el
     * que arranca contando el motivo de consulta.
     *
     * Si el docente no marcó a nadie, se elige solo: el paciente si su edad
     * le da para contar su historia, y si no el primer acompañante adulto.
     * Un lactante que viene solo termina siendo informante de sí mismo, que
     * es absurdo pero irrepresentable de otra forma -- eso lo reclama
     * problemas(), porque deja al alumno sin nadie a quien preguntarle.
     */
    private static function asignarInformante(array $personas): array
    {
        $idx = null;
        foreach ($personas as $k => $p) {
            // Un lactante marcado como quien cuenta la historia se corrige
            // solo si hay alguien más que sí habla: no se avisa ni se
            // bloquea nada, simplemente el prompt no puede decirle al
            // modelo que lleva la voz cantante alguien que no produce
            // frases.
            if ($p['informante'] && self::capacidad((int) $p['edad']) !== self::CAP_NULO) {
                $idx = $idx ?? $k;
            }
            $personas[$k]['informante'] = false;
        }
        if ($idx === null) {
            foreach ($personas as $k => $p) {
                $cap = self::capacidad($p['edad']);
                if ($p['es_paciente'] && $cap !== self::CAP_NULO && $cap !== self::CAP_MINIMO) {
                    $idx = $k;
                    break;
                }
            }
        }
        if ($idx === null) {
            foreach ($personas as $k => $p) {
                if (!$p['es_paciente'] && $p['edad'] >= 18) {
                    $idx = $k;
                    break;
                }
            }
        }
        if ($idx === null && $personas) {
            $idx = 0;
        }
        if ($idx !== null) {
            $personas[$idx]['informante'] = true;
        }
        return $personas;
    }

    private static function dedupIds(array $personas): array
    {
        $vistos = [];
        foreach ($personas as $k => $p) {
            $id = $p['id'];
            if (isset($vistos[$id])) {
                $id = 'p' . ($k + 1) . '_' . $k;
            }
            $vistos[$id] = true;
            $personas[$k]['id'] = $id;
        }
        return $personas;
    }

    /**
     * Id usable como nombre de archivo (la foto de cada persona se guarda
     * con el id pegado al case_id, ver PatientPhoto::key) y como rótulo con
     * el que el modelo dice quién habló. Vacío o con basura => pN por
     * posición.
     */
    private static function safeId(string $id, int $indice): string
    {
        $safe = preg_replace('/[^A-Za-z0-9]/', '', $id) ?? '';
        return $safe !== '' ? substr($safe, 0, 16) : 'p' . ($indice + 1);
    }

    private static function pct($valor): int
    {
        return max(0, min(100, (int) $valor));
    }

    /**
     * Sala efectiva de un caso guardado. Si el caso no trae sala (creado
     * antes de esto, o desde create_a.py), se arma una de una sola persona
     * con los campos de paciente que ya existían: el chat se comporta
     * exactamente como antes, un paciente y nadie más.
     *
     * $nombre/$edad vienen de la cita (no viven en cases.data, ver
     * llm_chat.php) y pisan lo guardado para el paciente.
     */
    public static function desde(array $caseData, string $nombre = '', int $edad = 0): array
    {
        $sala = $caseData['Sala'] ?? null;
        if (is_array($sala) && !empty($sala['personas'])) {
            $normal = self::normalize($sala);
            // El nombre/edad reales del paciente son los de la cita: la
            // sala guardada puede haberse escrito con un nombre de ejemplo.
            foreach ($normal['personas'] as $k => $p) {
                if ($p['es_paciente']) {
                    if ($nombre !== '') {
                        $normal['personas'][$k]['nombre'] = $nombre;
                    }
                    if ($edad > 0) {
                        $normal['personas'][$k]['edad'] = $edad;
                    }
                    break;
                }
            }
            return $normal;
        }

        return self::normalize([
            'personas' => [[
                'id' => 'p1',
                'rol' => 'paciente',
                'nombre' => $nombre !== '' ? $nombre : 'el paciente',
                'edad' => $edad > 0 ? $edad : (int) ($caseData['edad'] ?? 0),
                'genero' => (int) ($caseData['gender'] ?? 0),
                'es_paciente' => true,
                'informante' => true,
                'comportamiento' => (string) ($caseData['PatientBehavior'] ?? ''),
                'disposicion' => (int) ($caseData['PatientDisposition'] ?? 0),
            ]],
        ]);
    }

    /** @return array<string,mixed>|null la persona con ese id, o null. */
    public static function persona(array $sala, string $id): ?array
    {
        foreach ($sala['personas'] as $p) {
            if ($p['id'] === $id) {
                return $p;
            }
        }
        return null;
    }

    public static function paciente(array $sala): ?array
    {
        foreach ($sala['personas'] as $p) {
            if ($p['es_paciente']) {
                return $p;
            }
        }
        return null;
    }

    public static function informante(array $sala): ?array
    {
        foreach ($sala['personas'] as $p) {
            if ($p['informante']) {
                return $p;
            }
        }
        return $sala['personas'][0] ?? null;
    }

    /**
     * Encuentra a quién se refiere un rótulo suelto: el `id` que devolvió el
     * modelo, o el nombre con el que escribió la frase.
     *
     * Existe porque el modelo no siempre respeta el id: escribe "Sofía",
     * "la madre" o el nombre completo del paciente donde se le pidió "p2".
     * Buscar solo por id exacto dejaba esas frases sin dueño y todas
     * terminaban atribuidas a quien lleva la voz cantante -- el alumno le
     * preguntaba la edad a Pepe y la respuesta salía con la cara de la mamá.
     *
     * Se busca de lo más específico a lo menos: id, nombre o etiqueta
     * completa, rol, y por último un solo nombre de pila.
     */
    public static function resolver(array $sala, string $texto): ?array
    {
        $clave = self::claveComparable($texto);
        if ($clave === '') {
            return null;
        }

        foreach ($sala['personas'] as $p) {
            if (self::claveComparable($p['id']) === $clave) {
                return $p;
            }
        }
        foreach ($sala['personas'] as $p) {
            $candidatos = [$p['nombre'], self::etiqueta($p), self::ROLES[$p['rol']] ?? '', $p['rol']];
            foreach ($candidatos as $c) {
                if ($c !== '' && self::claveComparable((string) $c) === $clave) {
                    return $p;
                }
            }
        }
        // "la madre", "el paciente": el rol dicho con artículo.
        foreach ($sala['personas'] as $p) {
            $rol = self::claveComparable(self::ROLES[$p['rol']] ?? '');
            if ($rol !== '' && preg_match('/^(el|la|mi|su)\s+' . preg_quote($rol, '/') . '$/', $clave)) {
                return $p;
            }
        }
        // Nombre de pila solo, que es como se llama a alguien en una consulta.
        foreach ($sala['personas'] as $p) {
            foreach (preg_split('/\s+/', self::claveComparable($p['nombre'])) ?: [] as $parte) {
                if ($parte !== '' && $parte === $clave) {
                    return $p;
                }
            }
        }
        return null;
    }

    /**
     * Separa el rótulo que el modelo a veces deja pegado al principio de la
     * frase ("Sofía García (Madre): buenas tardes") del texto hablado.
     *
     * Devuelve [persona o null, texto sin rótulo]. Si el rótulo no
     * corresponde a nadie de esta consulta no se toca nada: puede ser parte
     * de la frase ("le dije: no escucho").
     *
     * @return array{0: array<string,mixed>|null, 1: string}
     */
    public static function separaRotulo(array $sala, string $texto): array
    {
        $limpio = trim($texto);
        // El modelo a veces lo pone en negrita markdown: **Sofía:** ...
        if (preg_match('/^\*\*(.{1,80}?)\*\*\s*:?\s*(.*)$/su', $limpio, $m)
            && ($persona = self::resolver($sala, $m[1])) !== null) {
            return [$persona, trim($m[2])];
        }
        if (!preg_match('/^([^:\n]{1,80}):\s*(.+)$/su', $limpio, $m)) {
            return [null, $limpio];
        }
        $persona = self::resolver($sala, $m[1]);
        return $persona !== null ? [$persona, trim($m[2])] : [null, $limpio];
    }

    /** Minúsculas sin tildes ni puntuación: para comparar rótulos escritos a mano. */
    private static function claveComparable(string $texto): string
    {
        $t = mb_strtolower(trim($texto), 'UTF-8');
        $t = strtr($t, ['á' => 'a', 'é' => 'e', 'í' => 'i', 'ó' => 'o', 'ú' => 'u', 'ü' => 'u', 'ñ' => 'n']);
        $t = preg_replace('/[^a-z0-9 ]+/u', ' ', $t) ?? '';
        return trim((string) preg_replace('/\s+/', ' ', $t));
    }

    /**
     * Lee el JSON con el que el modelo dice quién habló ({"turnos":[{"id","texto"}]}).
     *
     * Es deliberadamente tolerante, porque un modelo conversacional no entrega
     * siempre el mismo shape y perder el turno es peor que cualquier rareza de
     * formato:
     *
     * - Envuelve el JSON en ```json ... ```: se pela el fence.
     * - Deja texto antes o después de las llaves: se recorta al bloque JSON.
     * - Manda el nombre donde iba el id ("Sofía", "la madre", "Pepe Andrés
     *   García Contreras"): lo resuelve resolver().
     * - Deja el rótulo pegado dentro del texto ("Sofía: buenas tardes"): se
     *   separa, y ese rótulo es quien habla aunque el id diga otra cosa.
     * - Contesta en texto plano rotulado por líneas: cada línea que empieza con
     *   alguien de esta consulta se vuelve una intervención suya.
     *
     * Recién si nada de eso da con alguien se atribuye todo a quien lleva la voz
     * cantante: una conversación cortada porque el modelo se comió una llave es
     * peor que una atribuida al que más probablemente hablaba.
     *
     * @return list<array{persona_id: string, etiqueta: string, texto: string}>
     */
    public static function intervenciones(string $raw, array $sala): array
    {
        $clean = trim($raw);
        // El modelo a veces envuelve el JSON en ```json ... ``` pese a la
        // instrucción de no hacerlo -- se pela el fence si aparece (mismo
        // criterio que OirsEvaluator::parseVerdict).
        if (substr($clean, 0, 3) === '```') {
            $clean = trim((string) preg_replace('/^```[a-zA-Z]*\n?|```$/', '', $clean));
        }

        $turnos = self::turnosDelJson($clean);
        $out = [];
        foreach ($turnos as $t) {
            $texto = trim((string) ($t['texto'] ?? ''));
            if ($texto === '') {
                continue;
            }
            [$porRotulo, $texto] = self::separaRotulo($sala, $texto);
            if ($texto === '') {
                continue;
            }
            // Manda el rótulo que venía dentro de la frase: si el modelo
            // escribió "Pepe: tengo cinco" bajo el id de la madre, quien
            // habla es Pepe y el id es el que se equivocó. Recién después
            // vale el id, y al final quien lleva la voz cantante.
            $persona = $porRotulo
                ?? self::resolver($sala, (string) ($t['id'] ?? ''))
                ?? self::informante($sala);
            if ($persona === null) {
                continue;
            }
            $out[] = [
                'persona_id' => $persona['id'],
                'etiqueta' => self::etiqueta($persona),
                'texto' => $texto,
            ];
        }

        if ($out) {
            return $out;
        }

        $out = self::intervencionesDesdeTextoPlano($clean, $sala);
        if ($out) {
            return $out;
        }

        $informante = self::informante($sala);
        return [[
            'persona_id' => $informante['id'] ?? '',
            'etiqueta' => $informante !== null ? self::etiqueta($informante) : '',
            'texto' => $clean !== '' ? $clean : $raw,
        ]];
    }

    /**
     * Turnos de una respuesta que se supone JSON, aceptando los shapes vecinos
     * que el modelo produce solo: {"turnos":[...]}, la lista pelada, un turno
     * suelto {"id","texto"}, o el JSON envuelto en prosa.
     *
     * @return list<array<string,mixed>>
     */
    private static function turnosDelJson(string $clean): array
    {
        $data = json_decode($clean, true);
        if (!is_array($data)) {
            // "Claro, acá va: { ... }" -- se recorta al bloque de llaves.
            $ini = strpos($clean, '{');
            $fin = strrpos($clean, '}');
            if ($ini !== false && $fin !== false && $fin > $ini) {
                $data = json_decode(substr($clean, $ini, $fin - $ini + 1), true);
            }
        }
        if (!is_array($data)) {
            return [];
        }

        $turnos = $data['turnos'] ?? $data;
        if (isset($turnos['texto'])) {
            $turnos = [$turnos];  // un turno suelto, sin la lista alrededor
        }
        if (!is_array($turnos)) {
            return [];
        }

        $out = [];
        foreach ($turnos as $t) {
            if (is_array($t) && isset($t['texto'])) {
                $out[] = $t;
            }
        }
        return $out;
    }

    /**
     * Respuesta en texto plano rotulada por líneas ("Sofía: buenas tardes"),
     * que es como contesta el modelo cuando ignora el formato JSON. Las líneas
     * sin rótulo siguen siendo de quien habló recién.
     *
     * Devuelve vacío si ninguna línea nombra a alguien de esta consulta: ahí no
     * hay nada que atribuir y decide quien llama.
     *
     * @return list<array{persona_id: string, etiqueta: string, texto: string}>
     */
    private static function intervencionesDesdeTextoPlano(string $texto, array $sala): array
    {
        $out = [];
        foreach (preg_split('/\R+/', $texto) ?: [] as $linea) {
            $linea = trim($linea);
            if ($linea === '') {
                continue;
            }
            [$persona, $frase] = self::separaRotulo($sala, $linea);
            if ($persona === null) {
                if ($out) {
                    $out[count($out) - 1]['texto'] = trim($out[count($out) - 1]['texto'] . ' ' . $frase);
                }
                continue;
            }
            if ($frase === '') {
                continue;
            }
            $out[] = [
                'persona_id' => $persona['id'],
                'etiqueta' => self::etiqueta($persona),
                'texto' => $frase,
            ];
        }
        return $out;
    }

    /** ¿Hay alguien además del paciente? Decide si el chat es grupal o 1 a 1. */
    public static function tieneAcompanantes(array $sala): bool
    {
        return count($sala['personas']) > 1;
    }

    /** Etiqueta corta para la UI: "Rosa (Madre)" -- o solo el rol si no hay nombre. */
    public static function etiqueta(array $persona): string
    {
        $rol = self::ROLES[$persona['rol']] ?? 'Acompañante';
        $nombre = $persona['nombre'];
        if ($nombre === '') {
            return $rol;
        }
        return $persona['es_paciente'] ? $nombre : "{$nombre} ({$rol})";
    }

    /**
     * La sala tal como la pinta el cliente: quién es cada uno, para poder
     * mostrar su cara y su nombre en la burbuja que le corresponda. Los
     * rasgos -- cuánta conciencia tiene de su problema, cuánto interrumpe --
     * se quedan en el servidor: son la respuesta del ejercicio.
     */
    public static function paraCliente(array $sala): array
    {
        $out = [];
        foreach ($sala['personas'] as $p) {
            $out[] = [
                'id' => $p['id'],
                'nombre' => $p['nombre'],
                'rol' => $p['rol'],
                'etiqueta' => self::etiqueta($p),
                'es_paciente' => $p['es_paciente'],
                'informante' => $p['informante'],
            ];
        }
        return $out;
    }

    // -----------------------------------------------------------------
    // Formulario del editor de casos (case_create.php)
    // -----------------------------------------------------------------

    /**
     * Arma la sala desde el $_POST del editor de casos. Los acompañantes
     * viajan como arrays paralelos (sala_rol[], sala_nombre[], ...), que es
     * lo que produce una tabla de filas que se agregan y se borran en el
     * navegador.
     *
     * El paciente NO viene en esas filas: sus datos ya están en el resto
     * del formulario (edad, género, comportamiento, sensibilidad) y
     * repetirlos acá sería tener dos verdades para lo mismo. Se inyecta
     * como primera persona con $paciente.
     *
     * @param array $paciente nombre, edad, genero, comportamiento, disposicion
     */
    public static function fromForm(array $v, array $paciente): array
    {
        $personas = [[
            'id' => 'p1',
            'rol' => 'paciente',
            'nombre' => trim((string) ($paciente['nombre'] ?? '')),
            'edad' => (int) ($paciente['edad'] ?? 0),
            'genero' => (int) ($paciente['genero'] ?? 0),
            'es_paciente' => true,
            'informante' => ((string) ($v['sala_informante'] ?? 'p1')) === 'p1',
            'comportamiento' => (string) ($paciente['comportamiento'] ?? ''),
            'disposicion' => (int) ($paciente['disposicion'] ?? 0),
            'conciencia' => self::pct($v['paciente_conciencia'] ?? self::RASGOS_DEFAULT['conciencia']),
            'confiabilidad' => self::pct($v['paciente_confiabilidad'] ?? self::RASGOS_DEFAULT['confiabilidad']),
        ]];

        $roles = (array) ($v['sala_rol'] ?? []);
        foreach (array_keys($roles) as $i) {
            $campo = static fn(string $k, $default = '') => ((array) ($v[$k] ?? []))[$i] ?? $default;
            $nombre = trim((string) $campo('sala_nombre'));
            $rol = (string) $campo('sala_rol');
            // Fila en blanco: el editor deja una plantilla vacía al final y
            // guardarla crearía un acompañante fantasma sin nombre ni rol.
            if ($nombre === '' && ($rol === '' || $rol === 'otro')) {
                continue;
            }
            // El id viaja en el formulario (sala_id[]) y no se deriva de la
            // posición: la foto de cada acompañante se guarda con ese id
            // (ver PatientPhoto::key), así que borrar una fila de más arriba
            // no puede correrle la cara a los demás.
            $id = self::safeId((string) $campo('sala_id'), $i + 1);
            $personas[] = [
                'id' => $id,
                'rol' => $rol,
                'nombre' => $nombre,
                'edad' => (int) $campo('sala_edad', 0),
                'genero' => (int) $campo('sala_genero', 0),
                'es_paciente' => false,
                'informante' => ((string) ($v['sala_informante'] ?? '')) === $id,
                'interrumpe' => $campo('sala_interrumpe', self::RASGOS_DEFAULT['interrumpe']),
                'confiabilidad' => $campo('sala_confiabilidad', self::RASGOS_DEFAULT['confiabilidad']),
                'version' => (string) $campo('sala_version'),
                'comportamiento' => (string) $campo('sala_comportamiento'),
                'disposicion' => (int) $campo('sala_disposicion', 0),
            ];
        }

        return self::normalize(['personas' => $personas]);
    }

    /**
     * Inverso de fromForm(): el shape que espera el editor para repintar
     * las filas de una sala ya guardada. El paciente queda fuera de
     * `acompanantes` por el mismo motivo que en fromForm.
     */
    public static function toForm(array $sala): array
    {
        $acompanantes = [];
        $informante = 'p1';
        $conciencia = self::RASGOS_DEFAULT['conciencia'];
        $confiabilidad = self::RASGOS_DEFAULT['confiabilidad'];

        foreach ($sala['personas'] as $p) {
            if ($p['informante']) {
                $informante = $p['id'];
            }
            if ($p['es_paciente']) {
                $conciencia = $p['conciencia'];
                $confiabilidad = $p['confiabilidad'];
                continue;
            }
            $acompanantes[] = $p;
        }

        return [
            'sala_informante' => $informante,
            'paciente_conciencia' => (string) $conciencia,
            'paciente_confiabilidad' => (string) $confiabilidad,
            'acompanantes' => $acompanantes,
        ];
    }

    // -----------------------------------------------------------------
    // Validación (la consume CaseCompleteness)
    // -----------------------------------------------------------------

    /**
     * Problemas de la sala de un caso, en texto para el docente. Vacío =
     * la sala está bien armada.
     *
     * Deliberadamente NO valida quién acompaña a quién. Que un menor venga
     * con un adulto, o que el padre pueda estar presente, son
     * recomendaciones y formalidades, no requisitos: un menor se atiende
     * solo si se puede atender solo. Bloquear un caso por eso sería
     * inventar una regla que en la práctica no existe.
     *
     * Lo único que sí se reclama es lo que deja el ejercicio sin salida:
     * un paciente que por su edad no habla y que además viene solo. Ahí no
     * hay nadie que pueda contar la historia y el alumno se queda frente a
     * una consulta muda.
     *
     * @return array<int,string>
     */
    public static function problemas(array $sala): array
    {
        $paciente = self::paciente($sala);
        if ($paciente === null) {
            return ['La sala no tiene paciente.'];
        }

        if (self::capacidad((int) $paciente['edad']) === self::CAP_NULO
            && !self::tieneAcompanantes($sala)) {
            return [sprintf(
                'El paciente tiene %d años y viene solo: por su edad no puede contar nada, '
                . 'así que no hay con quién levantar la historia. Agrega a quien lo trae.',
                (int) $paciente['edad']
            )];
        }

        return [];
    }
}
