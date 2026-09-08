<?php

require_once __DIR__ . '/CaseProfile.php';
require_once __DIR__ . '/LlmChat.php';

/**
 * Borrador de anamnesis escrito por el LLM a partir de los hallazgos del
 * caso.
 *
 * La anamnesis es el único bloque de la ficha que no sale de ninguna
 * cuenta: es relato clínico. Pero tampoco es libre -- tiene que ser
 * coherente con el oído que el docente ya definió. Un audiograma con muesca
 * en 4 kHz pide exposición a ruido; una conductiva unilateral con
 * timpanograma B pide otitis a repetición; una neuropatía en un neonato
 * pide hiperbilirrubinemia. Escribir eso a mano para cada caso es lo que
 * hace que en la práctica queden todos vacíos.
 *
 * Lo que devuelve es un BORRADOR y nada más. El texto no entra al caso sin
 * que un docente lo lea y lo verifique explícitamente: ver
 * CaseCompleteness, que bloquea el guardado y el agendamiento mientras
 * `Anamnesis.ia.verificado` esté en false. El modelo puede inventar una
 * cirugía que no existe o un fármaco que no es ototóxico, y eso llega al
 * alumno como si fuera parte del caso.
 */
final class AnamnesisDraft
{
    /** Tope de caracteres por campo de texto, para que un modelo suelto no llene la ficha. */
    public const MAX_TEXTO = 400;

    /**
     * Presupuesto de tokens de esta tarea. Tiene su propio campo en
     * Admin -> IA Paciente (`anamnesis_max_tokens`), aparte del del chat:
     * el chat contesta una frase hablada y con 400 sobra, mientras que acá
     * el JSON completo ya ocupa varios cientos y un modelo de RAZONAMIENTO
     * gasta presupuesto pensando ANTES de escribir -- con 400 devuelve el
     * razonamiento cortado a la mitad y `content` vacío.
     */
    public static function maxTokens(): int
    {
        return max(1, (int) LlmConfig::get()['anamnesis_max_tokens']);
    }

    /** Modelo efectivo de esta tarea: el propio, o el general si está vacío. */
    public static function model(): string
    {
        return LlmConfig::effectiveAnamnesisModel();
    }

    /**
     * Techo del reintento automático. Un modelo de razonamiento puede
     * gastar varios miles de tokens pensando una tarea chica, y cuánto
     * exactamente no se sabe de antemano: depende del caso. En vez de
     * hacer que el docente adivine el número subiéndolo de a poco, se
     * reintenta una vez con el triple, hasta acá.
     */
    public const MAX_TOKENS_REINTENTO = 12000;

    /**
     * Segundos de espera de esta tarea. Los 30 del chat están puestos
     * porque ahí hay un alumno mirando la pantalla; acá el docente aprieta
     * un botón y espera, así que se puede aguantar bastante más. Un modelo
     * de razonamiento generando varios miles de tokens no entra en 30.
     */
    public const TIMEOUT_S = 90;

    /**
     * Lo que esta tarea pisa de la configuración del chat: su modelo, su
     * presupuesto, su espera y el rótulo del campo que hay que subir si el
     * presupuesto no alcanza.
     *
     * Recibe modelo y presupuesto en vez de leerlos: así queda pura (se
     * testea sin base) y generate() consulta la configuración una sola vez
     * en lugar de una por intento.
     *
     * @return array<string,mixed>
     */
    public static function opciones(int $presupuesto, string $modelo): array
    {
        return [
            'model' => $modelo,
            'max_tokens' => $presupuesto,
            'timeout' => self::TIMEOUT_S,
            'campo_tokens' => 'Máximo de tokens del borrador de anamnesis',
        ];
    }

    /**
     * Presupuesto del reintento: el triple, con techo. Si ya se pidió el
     * techo o más, devuelve lo mismo y quien llama no reintenta -- volver a
     * gastar el mismo presupuesto que ya falló no lleva a ningún lado.
     */
    public static function retryBudget(int $presupuesto): int
    {
        return max($presupuesto, min(self::MAX_TOKENS_REINTENTO, $presupuesto * 3));
    }

    /**
     * Instrucciones fijas del generador. Van como system prompt: describen
     * la tarea y el formato, nunca el caso (eso va en el mensaje de
     * usuario, armado por describeCase()).
     */
    public const SYSTEM_PROMPT = <<<'TXT'
Sos un fonoaudiólogo clínico que redacta la anamnesis de un paciente para un
caso de simulación docente. Te dan los hallazgos audiológicos ya definidos y
tenés que escribir los antecedentes que los EXPLICAN de manera plausible.

Reglas:
- La anamnesis tiene que ser COHERENTE con los hallazgos, no repetirlos. No
  menciones umbrales, dB, ni nombres de exámenes: eso lo mide el alumno.
- No inventes diagnósticos ya hechos ni digas qué tiene el paciente. La
  anamnesis es lo que el paciente cuenta y lo que figura en su historia.
- Escribí en español de Chile, en tercera persona, breve y clínico.
- Si un campo no corresponde a este paciente, devolvelo como string vacío.
  Un paciente sano no toma medicamentos ni tuvo cirugías: no rellenes.
- "comportamiento" describe cómo actúa el paciente al conversar (tono,
  actitud), no su patología.

No razones en voz alta ni expliques tu respuesta: escribí el JSON directo.

Respondé SOLO con un objeto JSON, sin ```, con exactamente estas claves:
{"antecedentes": [...], "medicamentos": "", "cirugias": "", "otros": "",
 "comportamiento": "", "disposicion": 0}

"antecedentes" es una lista con las claves que correspondan, de esta lista
cerrada y ninguna otra: hipoacusia_familiar, ototoxicos, trauma_acustico,
otitis, meningitis, tce, diabetes, hta.
"disposicion" es un entero de -2 (muy quisquilloso) a 2 (muy positivo).
TXT;

    /**
     * Los hallazgos del caso en prosa, para que el modelo escriba una
     * historia que los explique.
     *
     * Se le pasa lo que un clínico vería, no el JSON crudo: el modelo
     * escribe mejor sobre "pérdida en agudos del oído derecho" que sobre
     * una lista de nueve enteros.
     *
     * @param array<string,mixed> $data cases.data ya armado
     */
    public static function describeCase(array $data): string
    {
        $edad = (int) ($data['edad'] ?? 0);
        $genero = ((int) ($data['gender'] ?? 0)) === 1 ? 'mujer' : 'hombre';
        $perfil = CaseProfile::normalize($data);
        $airPairs = is_array($data['Aerea'] ?? null) ? $data['Aerea'] : [];
        $bonePairs = is_array($data['Osea'] ?? null) ? $data['Osea'] : [];

        $lineas = ["Paciente: {$genero} de {$edad} años."];

        foreach (['OD' => 0, 'OI' => 1] as $lado => $idx) {
            $ccePct = (float) ($perfil[$lado]['cce_pct'] ?? 100.0);
            $retro = CaseProfile::normalizeRetro($perfil[$lado]['retro'] ?? []);
            $decomp = CaseProfile::decompose($airPairs, $bonePairs, $idx, $ccePct);
            $tipo = CaseProfile::derivedType($decomp, $ccePct, $retro);
            $grave = CaseProfile::levelAt($decomp['air'], 500.0) ?? 0.0;
            $agudo = CaseProfile::levelAt($decomp['air'], 4000.0) ?? 0.0;

            $etiqueta = [
                'normal' => 'audición dentro de rango normal',
                'coclear' => 'pérdida de oído interno (células ciliadas)',
                'transmission' => 'pérdida de conducción, por oído medio',
                'neural' => 'compromiso del nervio auditivo, con la cóclea conservada',
            ][$tipo] ?? $tipo;

            $forma = 'plana';
            if ($agudo - $grave >= 20) {
                $forma = 'que cae en las frecuencias agudas';
            } elseif ($grave - $agudo >= 20) {
                $forma = 'que afecta más las frecuencias graves';
            }

            $oido = $lado === 'OD' ? 'derecho' : 'izquierdo';
            $lineas[] = sprintf('Oído %s: %s%s.', $oido, $etiqueta,
                $tipo === 'normal' ? '' : ', ' . $forma);
        }

        $tymp = ['OD' => (string) ($data['Z_OD'] ?? 'A'), 'OI' => (string) ($data['Z_OI'] ?? 'A')];
        foreach ($tymp as $lado => $curva) {
            if ($curva !== 'A') {
                $oido = $lado === 'OD' ? 'derecho' : 'izquierdo';
                $lineas[] = "Oído medio {$oido}: timpanograma tipo {$curva} (no es normal).";
            }
        }

        $tinnitus = is_array($data['Tinnitus'] ?? null) ? $data['Tinnitus'] : [];
        if ($tinnitus !== []) {
            $lineas[] = 'Acúfeno: ' . CaseBuilder::describeTinnitus($tinnitus);
        }

        return implode("\n", $lineas);
    }

    /**
     * Pide el borrador al LLM y lo devuelve ya validado.
     *
     * Todo lo que vuelve del modelo se filtra contra la lista cerrada de
     * antecedentes y se recorta a MAX_TEXTO: la respuesta es texto que
     * escribió un tercero, no un dato de confianza. Si el JSON no viene o
     * no se puede parsear, lanza RuntimeException con algo legible.
     *
     * @param array<string,mixed> $data cases.data
     * @return array{antecedentes:array<string,bool>, medicamentos:string,
     *               cirugias:string, otros:string, comportamiento:string,
     *               disposicion:int}
     */
    public static function generate(array $data): array
    {
        $prompt = self::describeCase($data);
        $presupuesto = self::maxTokens();
        $modelo = self::model();
        try {
            $raw = LlmChat::reply(self::SYSTEM_PROMPT, [], $prompt, self::opciones($presupuesto, $modelo));
        } catch (LlmBudgetException $e) {
            // Un solo reintento con más aire. Cuánto razona el modelo
            // depende del caso, así que el número "correcto" no existe:
            // pedirle al docente que lo vaya subiendo a mano es hacerle
            // pagar nuestro problema.
            $reintento = self::retryBudget($presupuesto);
            if ($reintento <= $presupuesto) {
                throw $e;
            }
            $raw = LlmChat::reply(self::SYSTEM_PROMPT, [], $prompt, self::opciones($reintento, $modelo));
        }
        $draft = self::parse($raw);
        if ($draft === null) {
            throw new RuntimeException(
                'El modelo no devolvió un JSON usable. Probá de nuevo; si sigue, revisá el modelo en Admin -> IA Paciente.'
            );
        }
        return $draft;
    }

    /**
     * Parsea y sanea la respuesta del modelo, o null si no sirve.
     *
     * Mismo pelado de ``` que OirsEvaluator::parseVerdict: el modelo a
     * veces envuelve el JSON pese a la instrucción.
     */
    public static function parse(string $raw): ?array
    {
        $limpio = trim($raw);
        if (substr($limpio, 0, 3) === '```') {
            $limpio = trim((string) preg_replace('/^```[a-zA-Z]*\n?|```$/', '', $limpio));
        }
        $json = json_decode($limpio, true);
        if (!is_array($json)) {
            return null;
        }

        // Lista cerrada: una clave que no está en HIST_CHECKBOXES se
        // descarta en silencio, no se agrega un antecedente inventado.
        $antecedentes = [];
        $pedidos = is_array($json['antecedentes'] ?? null) ? $json['antecedentes'] : [];
        foreach (CaseBuilder::HIST_CHECKBOXES as $clave) {
            $antecedentes[$clave] = in_array($clave, $pedidos, true);
        }

        $texto = static function ($valor): string {
            $s = trim((string) ($valor ?? ''));
            return mb_substr($s, 0, self::MAX_TEXTO);
        };

        return [
            'antecedentes' => $antecedentes,
            'medicamentos' => $texto($json['medicamentos'] ?? ''),
            'cirugias' => $texto($json['cirugias'] ?? ''),
            'otros' => $texto($json['otros'] ?? ''),
            'comportamiento' => $texto($json['comportamiento'] ?? ''),
            'disposicion' => max(-2, min(2, (int) ($json['disposicion'] ?? 0))),
        ];
    }
}
