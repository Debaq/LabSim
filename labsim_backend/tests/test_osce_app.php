<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/OsceApp.php';

/**
 * Estaciones del OSCE en la app: configuración del equipo y marcaje de
 * curvas, corregidas desde lo que manda la app (sesión del ABR, panel y
 * verdad del generador).
 */

// -- Esperado ---------------------------------------------------------------
t_true(OsceApp::cumpleEsperado('21.1', '21.1'), 'Igual numérico');
t_true(OsceApp::cumpleEsperado(21.1, '21,1'), 'Coma decimal en lo esperado');
t_true(!OsceApp::cumpleEsperado('21.0', '21.1'), 'Tasa 21 no es 21,1');
t_true(OsceApp::cumpleEsperado('Alternada', 'alternada'), 'Texto sin distinguir mayúsculas');
t_true(OsceApp::cumpleEsperado('Burst 1 kHz', 'Click | Burst 1 kHz'), 'Lista: cualquiera vale');
t_true(!OsceApp::cumpleEsperado('Rarefacción', 'Click | Burst 1 kHz'), 'Lista: fuera de la lista no');
t_true(OsceApp::cumpleEsperado('11', '10–12'), 'Rango con raya');
t_true(OsceApp::cumpleEsperado('10', '10-12'), 'Rango con guion, borde incluido');
t_true(!OsceApp::cumpleEsperado('15', '10–12'), 'Fuera del rango');
t_true(!OsceApp::cumpleEsperado(null, '80'), 'Sin valor no cumple');
t_true(OsceApp::cumpleEsperado(10000.0, '10000'), 'Ganancia ×10.000');

// -- Curvas del marcaje -----------------------------------------------------
t_eq(OsceApp::leerCurvas("OD 80\nod60\n\nOI 80\nOD 80\nXX 3\nOI 200"), [['OD', 80], ['OD', 60], ['OI', 80]],
     'Curvas: una por línea, sin repetidas ni inválidas');
t_eq(OsceApp::curvasTexto([['OD', 80], ['OI', 40]]), "OD 80\nOI 40", 'Y de vuelta a texto');

// -- Parámetros -------------------------------------------------------------
$entrega = [
    'panel' => ['stim' => 'Click', 'pol' => 'Rarefacción', 'int' => 80, 'rate' => 21.1, 'filter_passhigh' => '100', 'filter_down' => '3000'],
    'abr' => ['equipo' => ['window_ms' => 12.0, 'gain' => 100000.0, 'transducer' => 'insert_earphone'], 'curvas' => []],
];
$item = static fn (array $cfg, float $pts = 1.0): array => ['puntaje' => $pts, 'critico' => 0, 'cfg' => $cfg];
$r = OsceApp::evaluarItem($item(['regla' => 'param', 'fuente' => 'panel', 'clave' => 'pol', 'esperado' => 'Alternada']), $entrega);
t_eq([$r['ok'], $r['puntaje'], $r['alumno']], [false, 0.0, 'Rarefacción'], 'Polaridad mal: 0 y muestra lo que dejó');
$r = OsceApp::evaluarItem($item(['regla' => 'param', 'fuente' => 'panel', 'clave' => 'rate', 'esperado' => '21.1'], 2.0), $entrega);
t_eq([$r['ok'], $r['puntaje']], [true, 2.0], 'Tasa bien: puntaje completo');
$r = OsceApp::evaluarItem($item(['regla' => 'param', 'fuente' => 'equipo', 'clave' => 'gain', 'esperado' => '10000']), $entrega);
t_eq([$r['ok'], $r['alumno'], $r['esperado']], [false, '×100.000', '×10.000'], 'Ganancia leída de Parámetros avanzados');
$r = OsceApp::evaluarItem($item(['regla' => 'param', 'fuente' => 'equipo', 'clave' => 'transducer', 'esperado' => 'insert_earphone']), $entrega);
t_eq([$r['ok'], $r['alumno']], [true, 'Fono de inserción'], 'Transductor con su nombre');
$r = OsceApp::evaluarItem($item(['regla' => 'param', 'fuente' => 'panel', 'clave' => 'stim', 'esperado' => OsceApp::ESPERADO_PEATC['stim']]), $entrega);
t_eq([$r['ok'], $r['esperado']], [true, 'cualquiera de 11 opciones'], 'Estímulo: el protocolo acepta todos');

// -- Marcas ------------------------------------------------------------------
$entrega = [
    'abr' => ['curvas' => [
        'R1' => ['side' => 'OD', 'int' => 80, 'LatAmp' => ['I' => [1.62, 0.3], 'III' => [3.95, 0.4], 'V' => [5.71, 0.6]]],
        'R2' => ['side' => 'OD', 'int' => 20, 'LatAmp' => ['V' => [8.1, 0.1]]],
        'R3' => ['side' => 'OD', 'int' => 40, 'LatAmp' => ['V' => [null, null]]],
    ]],
    'verdad' => [
        'R1' => ['visible' => true, 'waves' => ['I' => ['lat' => 1.6], 'III' => ['lat' => 3.7], 'V' => ['lat' => 5.6]]],
        'R2' => ['visible' => false, 'waves' => ['V' => ['lat' => 8.2]]],
        'R3' => ['visible' => true, 'waves' => ['V' => ['lat' => 7.0]]],
    ],
];
$marca = static fn (int $int, string $onda) => $item(['regla' => 'marca', 'lado' => 'OD', 'int' => $int, 'onda' => $onda, 'tol_ms' => 0.2]);
t_eq(OsceApp::evaluarItem($marca(80, 'I'), $entrega)['ok'], true, 'I a 0,02 ms: bien');
t_eq(OsceApp::evaluarItem($marca(80, 'III'), $entrega)['ok'], false, 'III a 0,25 ms: fuera de ±0,2');
t_eq(OsceApp::evaluarItem($marca(80, 'V'), $entrega)['ok'], true, 'V a 0,11 ms: bien');
$r = OsceApp::evaluarItem($marca(20, 'V'), $entrega);
t_eq([$r['ok'], $r['esperado']], [false, 'sin onda V (no marcar)'], 'Marcar V donde no hay respuesta: mal');
$r = OsceApp::evaluarItem($marca(40, 'V'), $entrega);
t_eq([$r['ok'], $r['alumno']], [false, 'sin marca'], 'No marcar V donde sí hay: mal');
$sinV = $entrega;
$sinV['abr']['curvas']['R2']['LatAmp']['V'] = [null, null];
t_eq(OsceApp::evaluarItem($marca(20, 'V'), $sinV)['ok'], true, 'Sin respuesta y sin marca: bien');
t_eq(OsceApp::evaluarItem($marca(60, 'V'), $entrega)['alumno'], 'sin curva', 'Curva que no está en la entrega');
