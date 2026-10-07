<?php

/**
 * Registro de los parámetros que un curso puede sobreescribir sobre el
 * default de la app (tabla app_config, ver AppConfig.php). Cada entrada
 * describe la FORMA de la key --grupos, filas y campos numéricos-- y los
 * valores por defecto; con eso alcanza tanto para pintar el editor
 * (views/course/_params.php) como para leer el POST (parse()).
 *
 * Existe para cortar la copia: los editores por examen eran ~210 líneas
 * gemelas en courses.php (handler + render), y los parámetros de
 * audiometría por curso (ver TODO.md) iban a ser otra copia. Sumar un
 * examen configurable ahora es agregar una entrada acá.
 *
 * NO va acá lo que el modelo puede derivar solo. El ABR tuvo su editor
 * (60 campos: ratio de latencia y amplitud por onda y por estímulo) y se
 * sacó: eran parámetros internos del generador, no decisiones docentes,
 * nadie podía tocar uno sin romper la coherencia con los otros 59, y hoy
 * el cliente los deriva del click de cada población (ver
 * ABRGenerator._rescale_ratio_block).
 *
 * Cada definición:
 *   module    código de Courses::MODULES -- el editor solo se muestra si el
 *             curso tiene ese módulo habilitado.
 *   title     título de la card.
 *   help      qué hace el software con estos números (mecánica, no clínica:
 *             el docente es el experto en lo clínico).
 *   groups    [clave => ['label' => ..., 'rows' => [clave => etiqueta]]]
 *   fields    [clave => ['label' => ..., 'step' => ..., 'min' => ..., 'max' => ...]]
 *             o, para texto, ['label' => ..., 'type' => 'lines', 'max_lines' => ...,
 *             'max_len' => ...]: un textarea con una entrada por línea que se
 *             guarda como lista de strings.
 *   layout    opcional, 'stack': una fila debajo de otra a todo el ancho (lo
 *             que lleva textareas no cabe en la grilla de números).
 *   defaults  [grupo][fila][campo] => float (o lista de strings), el valor que trae la app.
 *
 * Los defaults son copia a mano de los JSON del cliente (repos separados);
 * tests/test_course_params.php falla si se desincronizan.
 */
final class CourseParams
{
    /**
     * Fuente de los defaults, para el test de sincronía: ruta del JSON en el
     * repo del cliente y cómo se lee cada valor. Solo documental acá.
     */
    public const SOURCES = [
        'normative_data.vemp' => 'resources/vemp/normative_data.json (adult_female, 500Hz)',
        'secretaria.avisos' => 'resources/json/secretaria_avisos.json',
    ];

    public static function all(): array
    {
        return [
            'normative_data.vemp' => [
                'module' => 'VEMP',
                'title' => 'Normativa VEMP (potenciales evocados vestibulares miogénicos)',
                'help' => 'VEMP ajusta el baseline por pico y subtipo con valores ABSOLUTOS: acá el baseline es del equipo, no del paciente. '
                    . 'El paciente desvía aparte, vía "desviaciones" en case_create.php. '
                    . 'Los campos muestran el default de la app; el curso guarda solo los que queden distintos.',
                'groups' => [
                    'CVEMP' => ['label' => 'CVEMP (cervical / SCM)', 'rows' => ['p13' => 'P13', 'n23' => 'N23']],
                    'OVEMP' => ['label' => 'OVEMP (ocular / oblicuo inferior)', 'rows' => ['n10' => 'N10', 'p16' => 'P16']],
                    'MVEMP' => ['label' => 'MVEMP (masetero -- experimental)', 'rows' => ['p13' => 'P13', 'n23' => 'N23']],
                ],
                'fields' => [
                    // Absolutos: la ventana de registro del VEMP es de ~60 ms
                    // y las amplitudes van de µV (OVEMP) a cientos de µV
                    // (CVEMP); fuera de esos topes el trazado no se dibuja.
                    'lat' => ['label' => 'Latencia (ms)', 'step' => 0.01, 'min' => 0.5, 'max' => 60.0],
                    'amp' => ['label' => 'Amplitud (µV)', 'step' => 0.01, 'min' => 0.1, 'max' => 1000.0],
                ],
                'defaults' => [
                    'CVEMP' => [
                        'p13' => ['lat' => 12.8, 'amp' => 135.0],
                        'n23' => ['lat' => 22.5, 'amp' => 185.0],
                    ],
                    'OVEMP' => [
                        'n10' => ['lat' => 9.8, 'amp' => 8.5],
                        'p16' => ['lat' => 15.8, 'amp' => 11.5],
                    ],
                    'MVEMP' => [
                        'p13' => ['lat' => 12.8, 'amp' => 45.0],
                        'n23' => ['lat' => 22.5, 'amp' => 60.0],
                    ],
                ],
            ],
            // Karime, la secretaria (ver core/secretaria.py en el cliente):
            // avisos emergentes durante la atención para apurar al alumno.
            'secretaria.avisos' => [
                'module' => 'AGENDA',
                'title' => 'Avisos de la secretaria durante la atención',
                'help' => 'Minutos desde que el alumno presiona "Atender" hasta cada aviso de Karime, que aparece unos segundos abajo a la derecha y se va solo. '
                    . 'En 0 ese aviso no aparece. Si el alumno retoma la atención (reabrir la app), los minutos vuelven a contar desde cero. '
                    . 'Cada aviso sortea una de sus frases (una por línea) y no repite la que dijo la vez anterior. '
                    . '"Con paciente siguiente" se usa si el alumno tiene otra cita sin atender ese mismo día y puede llevar {nombre} y {hora} de esa cita; '
                    . '"Sin paciente siguiente" se usa si no la tiene. Ambas pueden llevar {minutos} (los del aviso). '
                    . 'Una frase que pide un dato que no hay se salta. Si se borran todas las líneas, vuelven las de la app.',
                'layout' => 'stack',
                'groups' => [
                    'avisos' => ['label' => 'Avisos', 'rows' => ['aviso_1' => 'Primer aviso', 'aviso_2' => 'Segundo aviso', 'aviso_3' => 'Tercer aviso']],
                ],
                'fields' => [
                    'min' => ['label' => 'Minutos', 'step' => 1, 'min' => 0, 'max' => 240],
                    'con_paciente' => ['label' => 'Frases con paciente siguiente (una por línea)', 'type' => 'lines', 'max_lines' => 60, 'max_len' => 300],
                    'sin_paciente' => ['label' => 'Frases sin paciente siguiente (una por línea)', 'type' => 'lines', 'max_lines' => 60, 'max_len' => 300],
                ],
                'defaults' => [
                    'avisos' => [
                        'aviso_1' => [
                            'min' => 20,
                            'con_paciente' => [
                                'Te aviso que {nombre} ya llegó, tenía hora a las {hora}. Está en la sala de espera.',
                                'Llegó {nombre} para su hora de las {hora}. Ya le tomé los datos, queda esperando afuera.',
                                'Permiso, solo para avisarte que {nombre} ya está en la sala de espera. Su hora es a las {hora}.',
                                '{nombre} acaba de llegar, con hora para las {hora}. Avísame cuando puedas recibirle.',
                                'Hola, disculpa la interrupción: ya llegó {nombre}, hora de las {hora}.',
                                'Te cuento que {nombre} ya está aquí para su hora de las {hora}. Le pedí que esperara un ratito.',
                                'Ya está {nombre} en recepción, tiene hora a las {hora}. Tú me dices.',
                                'Aviso rápido: {nombre} ya llegó. Su atención es a las {hora}.',
                                '{nombre} ya está en la sala de espera. Venía para las {hora}, no te apures pero tenlo en cuenta.',
                                'Perdona que entre así. Llegó {nombre}, su hora era a las {hora}.',
                                'Ya llegó tu paciente de las {hora}, {nombre}. Está en la sala.',
                                'Te dejo el aviso: {nombre}, hora de las {hora}, ya está esperando.',
                            ],
                            'sin_paciente' => [
                                'Ya van {minutos} minutos de atención. Recuerda que el box se ocupa en el bloque siguiente.',
                                'Te aviso que llevas {minutos} minutos. El box está reservado para después.',
                                'Permiso, solo para que tengas el tiempo: van {minutos} minutos.',
                                'Llevas {minutos} minutos con tu paciente. Todo bien, solo para que lo tengas presente.',
                                'Disculpa la interrupción, ¿cómo vas? Ya van {minutos} minutos.',
                                'Te cuento que el box lo necesitan después de ti. Llevas {minutos} minutos.',
                                'Aviso de recepción: {minutos} minutos de atención hasta ahora.',
                                'Hola, paso a recordarte el tiempo: van {minutos} minutos.',
                                'Ya van {minutos} minutos. Avísame si necesitas algo de recepción.',
                                'Solo un recordatorio: llevas {minutos} minutos y el box tiene otra reserva más tarde.',
                                'Van {minutos} minutos. Cuando termines, avísame para dejar el box listo.',
                                'Te dejo el dato: {minutos} minutos de atención. Sigue nomás.',
                            ],
                        ],
                        'aviso_2' => [
                            'min' => 30,
                            'con_paciente' => [
                                '{nombre} sigue esperando en la sala. ¿Te falta mucho?',
                                'Disculpa, {nombre} me preguntó si falta mucho. ¿Qué le digo?',
                                'Oye, {nombre} ya lleva un rato en la sala. ¿Cómo vas?',
                                '{nombre} sigue afuera esperando su hora de las {hora}. ¿Te queda poquito?',
                                'Te vuelvo a molestar: {nombre} sigue en la sala de espera.',
                                '¿Vas a demorar mucho más? {nombre} está esperando desde hace rato.',
                                '{nombre} se acercó al mesón a preguntar por su hora. Le dije que ya casi.',
                                'Solo para que sepas: la hora de {nombre} era a las {hora} y sigue esperando.',
                                '¿Cuánto te falta más o menos? Es para avisarle a {nombre}.',
                                '{nombre} ya miró el reloj un par de veces... ¿cómo vamos?',
                                'La sala se está llenando y {nombre} sigue esperando. ¿Te falta mucho?',
                                'Le ofrecí un vaso de agua a {nombre} mientras espera. ¿Cuánto te queda?',
                            ],
                            'sin_paciente' => [
                                'Van {minutos} minutos. Voy a necesitar el box pronto.',
                                '¿Te falta mucho? Llevas {minutos} minutos y viene otro equipo a usar el box.',
                                'Ya son {minutos} minutos. ¿Cómo vas?',
                                'Oye, el siguiente bloque empieza pronto y llevas {minutos} minutos.',
                                'Te vuelvo a molestar: {minutos} minutos. ¿Te queda poco?',
                                'Me están preguntando por el box. Llevas {minutos} minutos, ¿cuánto te falta?',
                                'Van {minutos} minutos. Ojo con el tiempo.',
                                'Disculpa, ¿vas a demorar mucho más? Ya son {minutos} minutos.',
                                'Tu atención ya va en {minutos} minutos. Ve pensando en el cierre.',
                                '{minutos} minutos ya. Hay gente esperando el box.',
                                'Ya llevas {minutos} minutos. ¿Necesitas más tiempo o vas terminando?',
                                'Paso de nuevo: van {minutos} minutos y la agenda del box viene apretada.',
                            ],
                        ],
                        'aviso_3' => [
                            'min' => 40,
                            'con_paciente' => [
                                '{nombre} ya lleva rato esperando y está preguntando por su hora. ¿Le digo que pase?',
                                'Oye, a {nombre} se le está acabando la paciencia. Necesito que vayas cerrando.',
                                '{nombre} me dijo que tiene que irse pronto. ¿Puedes ir terminando?',
                                'Ya vamos bien atrasados con {nombre}, su hora era a las {hora}. Por favor ve cerrando.',
                                '{nombre} pidió hablar con alguien por la demora. ¿Te falta mucho de verdad?',
                                'Te pido que vayas terminando: {nombre} lleva mucho esperando y se está atrasando toda la agenda.',
                                'Disculpa la insistencia, pero {nombre} está pensando en reagendar. ¿Le digo que espere un poco más o ya terminas?',
                                'Esto ya se está alargando mucho. {nombre} espera desde las {hora}.',
                                'Último aviso, de verdad: {nombre} sigue afuera y la agenda viene atrasada.',
                                'Si no terminas pronto voy a tener que reagendar a {nombre}. ¿Qué hago?',
                                '{nombre} ya me preguntó tres veces. Por favor ve cerrando la atención.',
                                'Ya no sé qué decirle a {nombre}. ¿Vas a alcanzar a atenderle o le doy otra hora?',
                            ],
                            'sin_paciente' => [
                                'Ya van {minutos} minutos. Por favor ve cerrando la atención.',
                                'Necesito el box ya, llevas {minutos} minutos. Ve terminando por favor.',
                                'Esto se alargó mucho: {minutos} minutos. Cierra la atención cuando puedas, pero pronto.',
                                'Último aviso: {minutos} minutos. El siguiente bloque ya está esperando.',
                                'Van {minutos} minutos y me están reclamando el box. ¿Terminas?',
                                'Disculpa la insistencia, pero ya son {minutos} minutos. Hay que ir cerrando.',
                                'Ya pasamos de largo el tiempo: {minutos} minutos. Por favor termina.',
                                '{minutos} minutos. Ya no puedo atrasar más al grupo que viene.',
                                'Te pido que vayas terminando, llevas {minutos} minutos.',
                                'Ya son {minutos} minutos de atención. Hay que liberar el box.',
                                'Van {minutos} minutos. Me pidieron avisarte que cierres ahora.',
                                'Ya es mucho rato, {minutos} minutos. Por favor ve despidiendo al paciente.',
                            ],
                        ],
                    ],
                ],
            ],
        ];
    }

    /** La definición de $key, o null si no está registrada (POST inventado). */
    public static function find(string $key): ?array
    {
        $all = self::all();
        return isset($all[$key]) ? $all[$key] : null;
    }

    /** Las definiciones cuyo módulo está habilitado en el curso -- el resto ni se muestra. */
    public static function forModules(array $enabledModules): array
    {
        $out = [];
        foreach (self::all() as $key => $def) {
            if (in_array($def['module'], $enabledModules, true)) {
                $out[$key] = $def;
            }
        }
        return $out;
    }

    /**
     * Arma el override a guardar a partir del POST: recorre la definición
     * (no el POST, así una clave inventada no entra), descarta lo vacío o no
     * numérico, recorta a [min, max] y --clave-- OMITE lo que quedó igual al
     * default. Guardar el formulario sin tocar nada no crea override: el
     * curso sigue heredando, y "volver a default" no depende de que el
     * docente borre campo por campo.
     */
    public static function parse(string $key, array $raw): array
    {
        $def = self::find($key);
        if ($def === null) {
            return [];
        }
        $override = [];
        foreach ($def['groups'] as $groupKey => $group) {
            foreach ($group['rows'] as $rowKey => $_rowLabel) {
                foreach ($def['fields'] as $fieldKey => $field) {
                    if (self::isLines($field)) {
                        $lines = self::parseLines($field, $raw[$groupKey][$rowKey][$fieldKey] ?? '');
                        $default = isset($def['defaults'][$groupKey][$rowKey][$fieldKey])
                            ? array_values((array) $def['defaults'][$groupKey][$rowKey][$fieldKey])
                            : [];
                        // Vacío = vuelve el default (el aviso no queda mudo).
                        if ($lines && $lines !== $default) {
                            $override[$groupKey][$rowKey][$fieldKey] = $lines;
                        }
                        continue;
                    }
                    $posted = isset($raw[$groupKey][$rowKey][$fieldKey]) ? trim((string) $raw[$groupKey][$rowKey][$fieldKey]) : '';
                    if ($posted === '' || !is_numeric($posted)) {
                        continue;
                    }
                    $value = (float) $posted;
                    if (isset($field['min'])) {
                        $value = max($value, (float) $field['min']);
                    }
                    if (isset($field['max'])) {
                        $value = min($value, (float) $field['max']);
                    }
                    $default = isset($def['defaults'][$groupKey][$rowKey][$fieldKey])
                        ? (float) $def['defaults'][$groupKey][$rowKey][$fieldKey]
                        : null;
                    if ($default !== null && abs($value - $default) < 1e-9) {
                        continue;
                    }
                    $override[$groupKey][$rowKey][$fieldKey] = $value;
                }
            }
        }
        return $override;
    }

    /**
     * Valor a mostrar en el input: el del curso si lo cambió, si no el
     * default de la app. $override es lo que devuelve
     * AppConfig::courseOverride() (solo lo propio del curso).
     */
    public static function displayValue(array $def, ?array $override, string $groupKey, string $rowKey, string $fieldKey): string
    {
        if (isset($override[$groupKey][$rowKey][$fieldKey])) {
            $value = $override[$groupKey][$rowKey][$fieldKey];
        } elseif (isset($def['defaults'][$groupKey][$rowKey][$fieldKey])) {
            $value = $def['defaults'][$groupKey][$rowKey][$fieldKey];
        } else {
            return '';
        }
        return is_array($value) ? implode("\n", $value) : (string) $value;
    }

    /** Campo de texto libre con una entrada por línea (frases), no un número. */
    public static function isLines(array $field): bool
    {
        return ($field['type'] ?? 'number') === 'lines';
    }

    /**
     * Textarea -> lista de frases: una por línea, sin vacías, recortadas a
     * max_len caracteres y a max_lines líneas (un pegado gigante no infla
     * la config que viaja a cada cliente en el sync).
     */
    private static function parseLines(array $field, $raw): array
    {
        $maxLines = (int) ($field['max_lines'] ?? 60);
        $maxLen = (int) ($field['max_len'] ?? 300);
        $lines = [];
        foreach (preg_split('/\r\n|\r|\n/', is_string($raw) ? $raw : '') as $line) {
            $line = trim($line);
            if ($line === '') {
                continue;
            }
            $lines[] = mb_substr($line, 0, $maxLen, 'UTF-8');
            if (count($lines) >= $maxLines) {
                break;
            }
        }
        return $lines;
    }
}
