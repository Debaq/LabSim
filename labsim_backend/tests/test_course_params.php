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

// --- ABR: ya no tiene editor por curso -----------------------------------
// Eran 60 campos (ratio de latencia y amplitud por onda y por estímulo) que
// no son decisiones docentes sino parámetros internos del generador, sin
// forma de tocar uno sin romper la coherencia con los otros 59. El cliente
// los deriva del click de cada población. Si alguien lo vuelve a agregar,
// que sea a propósito y no por inercia.
t_eq(CourseParams::find('normative_data.abr'), null, 'ABR: no hay editor de ratios por curso');
t_eq(array_keys(CourseParams::forModules(['ABR'])), [], 'ABR: un curso con ABR no ve editores de normativa');

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
$vempDef = $defs['normative_data.vemp'];
$igualQueElDefault = [];
foreach ($vempDef['defaults'] as $stim => $ondas) {
    foreach ($ondas as $onda => $campos) {
        foreach ($campos as $campo => $valor) {
            $igualQueElDefault[$stim][$onda][$campo] = (string) $valor;
        }
    }
}
t_eq(
    CourseParams::parse('normative_data.vemp', $igualQueElDefault),
    [],
    'parse(): guardar el formulario sin tocar nada no crea override'
);

$tocado = $igualQueElDefault;
$tocado['CVEMP']['p13']['amp'] = '150';
t_eq(
    CourseParams::parse('normative_data.vemp', $tocado),
    ['CVEMP' => ['p13' => ['amp' => 150.0]]],
    'parse(): solo viaja el valor que el docente cambió'
);

// Fuera de rango: se recorta al tope, no se guarda un trazado imposible.
$fueraDeRango = $igualQueElDefault;
$fueraDeRango['CVEMP']['p13']['lat'] = '999';
$fueraDeRango['CVEMP']['p13']['amp'] = '-3';
t_eq(
    CourseParams::parse('normative_data.vemp', $fueraDeRango),
    ['CVEMP' => ['p13' => ['lat' => 60.0, 'amp' => 0.1]]],
    'parse(): recorta a [min, max] en vez de aceptar cualquier número'
);

// Basura y claves inventadas: se ignoran (el recorrido sale de la definición).
t_eq(
    CourseParams::parse('normative_data.vemp', ['CVEMP' => ['p13' => ['amp' => 'abc']], 'inventado' => ['X' => ['y' => '1']]]),
    [],
    'parse(): descarta lo no numérico y las claves que no están en el registro'
);
t_eq(CourseParams::parse('key.que.no.existe', ['a' => ['b' => ['c' => '1']]]), [], 'parse(): key desconocida devuelve vacío');
t_eq(CourseParams::find('key.que.no.existe'), null, 'find(): key desconocida es null');

// --- forModules(): el editor solo aparece con el módulo habilitado ---------
t_eq(array_keys(CourseParams::forModules(['VEMP'])), ['normative_data.vemp'], 'forModules(): curso con VEMP ve el editor de VEMP');
t_eq(array_keys(CourseParams::forModules([])), [], 'forModules(): curso sin módulos no ve editores');
t_eq(
    count(CourseParams::forModules(['ABR', 'VEMP', 'A'])),
    1,
    'forModules(): un módulo sin parámetros registrados no agrega editores'
);

// --- displayValue(): muestra el override del curso, si no el default -------
$override = ['CVEMP' => ['p13' => ['amp' => 150.0]]];
t_eq(CourseParams::displayValue($vempDef, $override, 'CVEMP', 'p13', 'amp'), '150', 'displayValue(): gana el valor del curso');
t_eq(CourseParams::displayValue($vempDef, $override, 'CVEMP', 'p13', 'lat'), '12.8', 'displayValue(): sin override, el default de la app');
t_eq(CourseParams::displayValue($vempDef, null, 'CVEMP', 'n23', 'lat'), '22.5', 'displayValue(): curso sin override ninguno');

// Cada módulo referenciado tiene que existir en Courses::MODULES, o el
// editor nunca se mostraría (forModules compara contra los códigos de ahí).
require_once dirname(__DIR__) . '/src/Layout.php';
require_once dirname(__DIR__) . '/src/Courses.php';
foreach ($defs as $key => $def) {
    t_true(isset(Courses::MODULES[$def['module']]), "CourseParams[{$key}]: su módulo existe en Courses::MODULES");
}
