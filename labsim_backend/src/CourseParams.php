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
        'normative_data.vemp' => 'resources/vemp/normative_data.json (adult_female, 500Hz)',
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
