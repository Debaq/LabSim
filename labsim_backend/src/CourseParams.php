<?php

/**
 * Registro de los parámetros que un curso puede sobreescribir sobre el
 * default de la app (tabla app_config, ver AppConfig.php). Cada entrada
 * describe la FORMA de la key --grupos, filas y campos numéricos-- y los
 * valores por defecto; con eso alcanza tanto para pintar el editor
 * (views/course/_params.php) como para leer el POST (parse()).
 *
 * Existe para cortar la copia: el editor del ABR y el del VEMP eran ~210
 * líneas gemelas en courses.php (handler + render), y los parámetros de
 * audiometría por curso (ver TODO.md) iban a ser la tercera copia. Sumar un
 * examen configurable ahora es agregar una entrada acá.
 *
 * Cada definición:
 *   module    código de Courses::MODULES -- el editor solo se muestra si el
 *             curso tiene ese módulo habilitado.
 *   title     título de la card.
 *   help      qué hace el software con estos números (mecánica, no clínica:
 *             el docente es el experto en lo clínico).
 *   groups    [clave => ['label' => ..., 'rows' => [clave => etiqueta]]]
 *   fields    [clave => ['label' => ..., 'step' => ..., 'min' => ..., 'max' => ...]]
 *   defaults  [grupo][fila][campo] => float, el valor que trae la app.
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
        'normative_data.abr' => 'resources/abr/normative_data.json (adult_female, vía aérea)',
        'normative_data.vemp' => 'resources/vemp/normative_data.json (adult_female, 500Hz)',
    ];

    public static function all(): array
    {
        return [
            'normative_data.abr' => [
                'module' => 'ABR',
                'title' => 'Desviación de estímulos ABR (potenciales evocados)',
                'help' => 'El click de cada paciente lo define el caso (case_create.php, campo "desviaciones") -- acá NO se edita click. '
                    . 'Esto configura cuánto se desvían los chirps y el burst respecto al click de ESE paciente, como factor multiplicador (ratio) por onda: '
                    . 'ej. ratio de amplitud 1.4 en la onda V del chirp = la V del chirp sale 40% más grande que la V (ya ajustada) del click de ese caso. '
                    . 'Los campos muestran el valor por defecto de la app; el curso guarda solo los que quedes distintos del default.',
                'groups' => [
                    'ce_chirp' => ['label' => 'CE-Chirp', 'rows' => ['I' => 'Onda I', 'III' => 'Onda III', 'V' => 'Onda V']],
                    'ce_chirp_ls' => ['label' => 'CE-Chirp LS', 'rows' => ['I' => 'Onda I', 'III' => 'Onda III', 'V' => 'Onda V']],
                    'nb_ce_chirp_ls_500Hz' => ['label' => 'NB CE-Chirp LS 500 Hz', 'rows' => ['I' => 'Onda I', 'III' => 'Onda III', 'V' => 'Onda V']],
                    'nb_ce_chirp_ls_1000Hz' => ['label' => 'NB CE-Chirp LS 1 kHz', 'rows' => ['I' => 'Onda I', 'III' => 'Onda III', 'V' => 'Onda V']],
                    'nb_ce_chirp_ls_2000Hz' => ['label' => 'NB CE-Chirp LS 2 kHz', 'rows' => ['I' => 'Onda I', 'III' => 'Onda III', 'V' => 'Onda V']],
                    'nb_ce_chirp_ls_4000Hz' => ['label' => 'NB CE-Chirp LS 4 kHz', 'rows' => ['I' => 'Onda I', 'III' => 'Onda III', 'V' => 'Onda V']],
                    'tone_burst_500Hz' => ['label' => 'Burst 500 Hz', 'rows' => ['I' => 'Onda I', 'III' => 'Onda III', 'V' => 'Onda V']],
                    'tone_burst_1000Hz' => ['label' => 'Burst 1 kHz', 'rows' => ['I' => 'Onda I', 'III' => 'Onda III', 'V' => 'Onda V']],
                    'tone_burst_2000Hz' => ['label' => 'Burst 2 kHz', 'rows' => ['I' => 'Onda I', 'III' => 'Onda III', 'V' => 'Onda V']],
                    'tone_burst_4000Hz' => ['label' => 'Burst 4 kHz', 'rows' => ['I' => 'Onda I', 'III' => 'Onda III', 'V' => 'Onda V']],
                ],
                'fields' => [
                    // Ratio, no valor absoluto: 0 o negativo no significa nada
                    // (la onda desaparecería o se invertiría), y arriba de 5x
                    // el trazado deja de ser un ABR.
                    'lat_ratio' => ['label' => 'Ratio latencia', 'step' => 0.0001, 'min' => 0.1, 'max' => 5.0],
                    'amp_ratio' => ['label' => 'Ratio amplitud', 'step' => 0.0001, 'min' => 0.1, 'max' => 5.0],
                ],
                // Ver ABR_generator.py::get_baseline_values.
                'defaults' => [
                    'ce_chirp' => [
                        'I' => ['lat_ratio' => 0.8951, 'amp_ratio' => 2.1429],
                        'III' => ['lat_ratio' => 0.9783, 'amp_ratio' => 1.4054],
                        'V' => ['lat_ratio' => 0.9872, 'amp_ratio' => 1.2167],
                    ],
                    'ce_chirp_ls' => [
                        'I' => ['lat_ratio' => 0.9074, 'amp_ratio' => 1.8095],
                        'III' => ['lat_ratio' => 0.9918, 'amp_ratio' => 1.1892],
                        'V' => ['lat_ratio' => 0.9963, 'amp_ratio' => 1.0333],
                    ],
                    'nb_ce_chirp_ls_500Hz' => [
                        'I' => ['lat_ratio' => 1.1173, 'amp_ratio' => 1.4143],
                        'III' => ['lat_ratio' => 1.2581, 'amp_ratio' => 0.9851],
                        'V' => ['lat_ratio' => 1.298, 'amp_ratio' => 0.855],
                    ],
                    'nb_ce_chirp_ls_1000Hz' => [
                        'I' => ['lat_ratio' => 1.0, 'amp_ratio' => 1.7357],
                        'III' => ['lat_ratio' => 1.144, 'amp_ratio' => 1.1676],
                        'V' => ['lat_ratio' => 1.1426, 'amp_ratio' => 0.9675],
                    ],
                    'nb_ce_chirp_ls_2000Hz' => [
                        'I' => ['lat_ratio' => 0.9383, 'amp_ratio' => 1.7858],
                        'III' => ['lat_ratio' => 1.0353, 'amp_ratio' => 1.1824],
                        'V' => ['lat_ratio' => 1.0421, 'amp_ratio' => 0.9791],
                    ],
                    'nb_ce_chirp_ls_4000Hz' => [
                        'I' => ['lat_ratio' => 0.9012, 'amp_ratio' => 1.9047],
                        'III' => ['lat_ratio' => 1.0, 'amp_ratio' => 1.25],
                        'V' => ['lat_ratio' => 1.0055, 'amp_ratio' => 1.0416],
                    ],
                    'tone_burst_500Hz' => [
                        'I' => ['lat_ratio' => 1.4506, 'amp_ratio' => 1.0476],
                        'III' => ['lat_ratio' => 1.4538, 'amp_ratio' => 0.7297],
                        'V' => ['lat_ratio' => 1.4625, 'amp_ratio' => 0.6333],
                    ],
                    'tone_burst_1000Hz' => [
                        'I' => ['lat_ratio' => 1.2037, 'amp_ratio' => 1.2857],
                        'III' => ['lat_ratio' => 1.2636, 'amp_ratio' => 0.8649],
                        'V' => ['lat_ratio' => 1.2431, 'amp_ratio' => 0.7167],
                    ],
                    'tone_burst_2000Hz' => [
                        'I' => ['lat_ratio' => 1.0494, 'amp_ratio' => 1.4286],
                        'III' => ['lat_ratio' => 1.1005, 'amp_ratio' => 0.9459],
                        'V' => ['lat_ratio' => 1.0969, 'amp_ratio' => 0.7833],
                    ],
                    'tone_burst_4000Hz' => [
                        'I' => ['lat_ratio' => 0.9568, 'amp_ratio' => 1.5238],
                        'III' => ['lat_ratio' => 1.0326, 'amp_ratio' => 1.0000],
                        'V' => ['lat_ratio' => 1.0329, 'amp_ratio' => 0.8333],
                    ],
                ],
            ],

            'normative_data.vemp' => [
                'module' => 'VEMP',
                'title' => 'Normativa VEMP (potenciales evocados vestibulares miogénicos)',
                'help' => 'VEMP ajusta el baseline por pico y subtipo con valores ABSOLUTOS, a diferencia del ABR (donde el click lo pone el paciente y el resto son ratios): '
                    . 'acá el baseline es del equipo, no del paciente. El paciente desvía aparte, vía "desviaciones" en case_create.php. '
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
            return (string) $override[$groupKey][$rowKey][$fieldKey];
        }
        return isset($def['defaults'][$groupKey][$rowKey][$fieldKey])
            ? (string) $def['defaults'][$groupKey][$rowKey][$fieldKey]
            : '';
    }
}
