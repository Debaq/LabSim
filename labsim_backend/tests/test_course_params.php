<?php

declare(strict_types=1);

/**
 * Los defaults del editor de parámetros por curso (CourseParams) son copia a
 * mano de los JSON normativos del cliente: el backend no puede leerlos en
 * runtime (se despliega solo, sin el repo del cliente al lado) y una copia a
 * mano se desincroniza en silencio -- el docente vería en pantalla un
 * "default de la app" que la app ya no usa, y peor: al guardar, parse()
 * descarta lo que coincide con SU default, así que un valor que en realidad
 * cambió quedaría sin override.
 *
 * Acá los dos lados sí conviven (mismo repo), así que se comparan.
 */

require_once dirname(__DIR__) . '/src/CourseParams.php';

$raizCliente = dirname(dirname(__DIR__));

/** Lee un JSON normativo del cliente; null si no está (checkout parcial). */
function cp_json(string $path): ?array
{
    if (!is_file($path)) {
        return null;
    }
    $data = json_decode((string) file_get_contents($path), true);
    return is_array($data) ? $data : null;
}

$defs = CourseParams::all();

// --- ABR: ratios por estímulo/onda (adult_female, vía aérea) --------------
$abr = cp_json($raizCliente . '/resources/abr/normative_data.json');
if ($abr === null) {
    t_true(true, 'ABR: sin resources/abr/normative_data.json a mano -- comparación omitida');
} else {
    $fuente = $abr['populations']['adult_female']['air_conduction'] ?? [];
    $def = $defs['normative_data.abr'];
    foreach ($def['defaults'] as $stim => $ondas) {
        // El override viaja con la clave plana 'tone_burst_500Hz' (así la
        // arma STIM_MAP y así la lee ABR_generator.get_baseline_values),
        // pero en el JSON los bursts cuelgan de tone_burst -> '500Hz'.
        $bloque = strpos((string) $stim, 'tone_burst_') === 0
            ? ($fuente['tone_burst'][substr((string) $stim, strlen('tone_burst_'))] ?? [])
            : ($fuente[$stim] ?? []);
        foreach ($ondas as $onda => $campos) {
            foreach ($campos as $campo => $valor) {
                t_close(
                    (float) ($bloque[$onda][$campo] ?? -1),
                    (float) $valor,
                    1e-6,
                    "ABR {$stim}/{$onda}/{$campo}: CourseParams vs normative_data.json"
                );
            }
        }
    }
    // Al revés: un estímulo nuevo en el JSON del cliente tiene que aparecer
    // en el editor, o el curso no puede configurarlo.
    foreach (['ce_chirp', 'ls_chirp', 'tone_burst_500Hz', 'tone_burst_1000Hz', 'tone_burst_2000Hz', 'tone_burst_4000Hz'] as $stim) {
        t_true(isset($def['groups'][$stim]), "ABR: el editor cubre el estímulo {$stim}");
    }
}

// --- VEMP: baselines absolutos por subtipo/pico (adult_female, 500Hz) -----
$vemp = cp_json($raizCliente . '/resources/vemp/normative_data.json');
if ($vemp === null) {
    t_true(true, 'VEMP: sin resources/vemp/normative_data.json a mano -- comparación omitida');
} else {
    $fuente = $vemp['populations']['adult_female']['air_conduction']['tone_burst']['500Hz'] ?? [];
    foreach ($defs['normative_data.vemp']['defaults'] as $subtipo => $picos) {
        foreach ($picos as $pico => $campos) {
            foreach ($campos as $campo => $valor) {
                t_close(
                    (float) ($fuente[$subtipo][$pico][$campo] ?? -1),
                    (float) $valor,
                    1e-6,
                    "VEMP {$subtipo}/{$pico}/{$campo}: CourseParams vs normative_data.json"
                );
            }
        }
    }
}

// --- parse(): lo que queda igual al default NO se guarda -------------------
$abrDef = $defs['normative_data.abr'];
$igualQueElDefault = [];
foreach ($abrDef['defaults'] as $stim => $ondas) {
    foreach ($ondas as $onda => $campos) {
        foreach ($campos as $campo => $valor) {
            $igualQueElDefault[$stim][$onda][$campo] = (string) $valor;
        }
    }
}
t_eq(
    CourseParams::parse('normative_data.abr', $igualQueElDefault),
    [],
    'parse(): guardar el formulario sin tocar nada no crea override'
);

$tocado = $igualQueElDefault;
$tocado['ce_chirp']['V']['amp_ratio'] = '1.9';
t_eq(
    CourseParams::parse('normative_data.abr', $tocado),
    ['ce_chirp' => ['V' => ['amp_ratio' => 1.9]]],
    'parse(): solo viaja el valor que el docente cambió'
);

// Fuera de rango: se recorta al tope, no se guarda un ABR imposible.
$fueraDeRango = $igualQueElDefault;
$fueraDeRango['ce_chirp']['V']['lat_ratio'] = '99';
$fueraDeRango['ce_chirp']['V']['amp_ratio'] = '-3';
t_eq(
    CourseParams::parse('normative_data.abr', $fueraDeRango),
    ['ce_chirp' => ['V' => ['lat_ratio' => 5.0, 'amp_ratio' => 0.1]]],
    'parse(): recorta a [min, max] en vez de aceptar cualquier número'
);

// Basura y claves inventadas: se ignoran (el recorrido sale de la definición).
t_eq(
    CourseParams::parse('normative_data.abr', ['ce_chirp' => ['V' => ['amp_ratio' => 'abc']], 'inventado' => ['X' => ['y' => '1']]]),
    [],
    'parse(): descarta lo no numérico y las claves que no están en el registro'
);
t_eq(CourseParams::parse('key.que.no.existe', ['a' => ['b' => ['c' => '1']]]), [], 'parse(): key desconocida devuelve vacío');
t_eq(CourseParams::find('key.que.no.existe'), null, 'find(): key desconocida es null');

// --- forModules(): el editor solo aparece con el módulo habilitado ---------
t_eq(array_keys(CourseParams::forModules(['ABR'])), ['normative_data.abr'], 'forModules(): curso con ABR ve solo el editor de ABR');
t_eq(array_keys(CourseParams::forModules([])), [], 'forModules(): curso sin módulos no ve editores');
t_eq(
    count(CourseParams::forModules(['ABR', 'VEMP', 'A'])),
    2,
    'forModules(): un módulo sin parámetros registrados no agrega editores'
);

// --- displayValue(): muestra el override del curso, si no el default -------
$override = ['ce_chirp' => ['V' => ['amp_ratio' => 1.9]]];
t_eq(CourseParams::displayValue($abrDef, $override, 'ce_chirp', 'V', 'amp_ratio'), '1.9', 'displayValue(): gana el valor del curso');
t_eq(CourseParams::displayValue($abrDef, $override, 'ce_chirp', 'V', 'lat_ratio'), '0.9872', 'displayValue(): sin override, el default de la app');
t_eq(CourseParams::displayValue($abrDef, null, 'ce_chirp', 'I', 'lat_ratio'), '0.8951', 'displayValue(): curso sin override ninguno');

// Cada módulo referenciado tiene que existir en Courses::MODULES, o el
// editor nunca se mostraría (forModules compara contra los códigos de ahí).
require_once dirname(__DIR__) . '/src/Layout.php';
require_once dirname(__DIR__) . '/src/Courses.php';
foreach ($defs as $key => $def) {
    t_true(isset(Courses::MODULES[$def['module']]), "CourseParams[{$key}]: su módulo existe en Courses::MODULES");
}
