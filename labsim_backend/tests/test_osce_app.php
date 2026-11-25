<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/OsceApp.php';

/**
 * Estaciones del OSCE en la app (ABR o VEMP): configuración del equipo,
 * marcaje y protocolo, corregidas desde lo que manda la app (panel, curvas
 * en orden con sus marcas, verdad del generador).
 */

$item = static fn (array $cfg, float $pts = 1.0): array => ['puntaje' => $pts, 'critico' => 0, 'cfg' => $cfg];
$curva = static function (string $nombre, string $lado, $int, array $marcas = [], array $extra = []): array {
    return array_merge(['nombre' => $nombre, 'side' => $lado, 'int' => $int, 'stim' => 'Click', 'pol' => 'Alternada',
                        'rate' => 21.1, 'filter_passhigh' => '100', 'filter_down' => '3000', 'transducer' => 'insert_earphone',
                        'window_ms' => 10.0, 'marcas' => $marcas], $extra);
};

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
t_true(OsceApp::cumpleEsperado(true, 'sí'), 'Booleano: sí');

// -- Curvas del marcaje -----------------------------------------------------
t_eq(OsceApp::leerCurvas("OD 80\nod60\n\nOI 80\nOD 80\nXX 3\nOI 200"), [['OD', 80], ['OD', 60], ['OI', 80]],
     'Curvas: una por línea, sin repetidas ni inválidas');
t_eq(OsceApp::curvasTexto([['OD', 80], ['OI', 40]]), "OD 80\nOI 40", 'Y de vuelta a texto');
t_eq(OsceApp::modulo('cvemp'), 'VEMP', 'cVEMP abre el VEMP');
t_eq(OsceApp::modulo('ecochg'), 'ABR', 'ECochG abre el ABR');

// -- Parámetros (configuración al entregar) -----------------------------------
$entrega = [
    'panel' => ['stim' => 'Click', 'pol' => 'Rarefacción', 'int' => 80, 'rate' => 21.1, 'filter_passhigh' => '100', 'filter_down' => '3000'],
    'equipo' => ['window_ms' => 12.0, 'gain' => 100000.0, 'transducer' => 'insert_earphone'],
];
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
    'curvas' => [
        $curva('R1', 'OD', 80, ['I' => 1.62, 'III' => 3.95, 'V' => 5.71]),
        $curva('R2', 'OD', 20, ['V' => 8.1]),
        $curva('R3', 'OD', 40, ['V' => null]),
    ],
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
$sinV['curvas'][1]['marcas']['V'] = null;
t_eq(OsceApp::evaluarItem($marca(20, 'V'), $sinV)['ok'], true, 'Sin respuesta y sin marca: bien');
t_eq(OsceApp::evaluarItem($marca(60, 'V'), $entrega)['alumno'], 'sin curva', 'Curva que no está en la entrega');
// VEMP: los picos con sus nombres
$vemp = ['curvas' => [$curva('C-OD-1', 'OD', 120, ['p13' => 13.4, 'n23' => 22.0])],
         'verdad' => ['C-OD-1' => ['visible' => true, 'waves' => ['p13' => ['lat' => 13.3], 'n23' => ['lat' => 22.6]]]]];
$m = static fn (string $onda) => $item(['regla' => 'marca', 'lado' => 'OD', 'int' => 120, 'onda' => $onda, 'tol_ms' => 0.5]);
t_eq([OsceApp::evaluarItem($m('p13'), $vemp)['ok'], OsceApp::evaluarItem($m('n23'), $vemp)['ok']], [true, false], 'VEMP: p13 bien, n23 a 0,6 ms mal');

// -- Protocolo: parámetros de cada curva ----------------------------------------
$prot = [
    'curvas' => [
        $curva('R1', 'OD', 80, ['V' => 5.6]),
        $curva('R2', 'OD', 80, ['V' => 5.6]),
        $curva('R3', 'OD', 60, ['V' => 6.0], ['filter_passhigh' => '30']),
        $curva('R4', 'OD', 40, ['V' => 6.6]),
        $curva('R5', 'OD', 20, []),
        $curva('R6', 'OD', 30, ['V' => 7.5]),
        $curva('R7', 'OD', 30, ['V' => 7.5]),
        $curva('L1', 'OI', 80, ['V' => 5.6], ['stim' => 'CE-Chirp LS']),
        $curva('L2', 'OI', 50, ['V' => 6.4], ['stim' => 'CE-Chirp LS']),
        $curva('L3', 'OI', 40, [], ['stim' => 'CE-Chirp LS']),
    ],
    'verdad' => [
        'R6' => ['visible' => true, 'threshold' => 25.0], 'R7' => ['visible' => true, 'threshold' => 25.0],
        'L2' => ['visible' => true, 'threshold' => 45.0], 'L3' => ['visible' => false, 'threshold' => 45.0],
    ],
];
$reg = static fn (string $regla, string $valor = '', bool $bonus = false, float $pts = 1.0) =>
    $item(['regla' => $regla, 'valor' => $valor, 'onda' => 'V', 'bonus' => $bonus], $pts);
$r = OsceApp::evaluarItem($item(['regla' => 'curvas_param', 'clave' => 'filter_passhigh', 'esperado' => '100'], 2.0), $prot);
t_eq([$r['puntaje'], $r['alumno']], [1.8, '9 de 10 curvas (también 30)'], 'Filtros: 9 de 10 curvas = 90 %');
t_eq(OsceApp::evaluarItem($reg('inicio', '80'), $prot)['puntaje'], 1.0, 'Parte cada oído en 80');
t_eq(OsceApp::evaluarItem($reg('ambos'), $prot)['puntaje'], 1.0, 'Ambos oídos');
// OD: 80→80 (réplica) 80→60 bien, 60→40 bien, 40→20 bien; OI: 80→50 mal (30), 50→40 mal (10)
$r = OsceApp::evaluarItem($reg('baja', '20'), $prot);
t_eq($r['puntaje'], 0.5, 'Baja de 20: OD todo bien, OI ningún paso bien = 50 %');
t_true(strpos($r['alumno'], 'OI 80→50') !== false, 'Dice dónde se salió del paso: ' . $r['alumno']);
$r = OsceApp::evaluarItem($reg('sube', '10'), $prot);
t_eq($r['puntaje'], 1.0, 'Sube de 10 tras no ver respuesta (OD 20→30); OI no subió: no aplica a ese oído');
t_eq(OsceApp::evaluarItem($reg('sube_max', '90–100'), $prot)['alumno'], 'no aplica', 'Siempre vio respuesta al partir: no aplica');
$r = OsceApp::evaluarItem($reg('replica_max'), $prot);
t_eq([$r['puntaje'], $r['alumno']], [0.5, 'OD 80 dB: 2 curvas · OI 80 dB: 1 curva'], 'Réplica en el máximo: solo OD');
t_eq(OsceApp::evaluarItem($reg('replica_umbral'), $prot)['puntaje'], 0.5, 'Réplica en el umbral: OD 30 dos veces, OI 50 una');
$r = OsceApp::evaluarItem($reg('umbral', '10', false, 2.0), $prot);
t_eq([$r['puntaje'], $r['alumno']], [2.0, 'OD 30 (real 25) · OI 50 (real 45)'], 'Umbrales a ±10 del real: completo');
t_eq(OsceApp::evaluarItem($reg('umbral', '3'), $prot)['puntaje'], 0.0, 'Con ±3 dB ninguno');
$r = OsceApp::evaluarItem($reg('umbral_chirp', '10', true), $prot);
t_eq([$r['puntaje'], $r['alumno']], [0.5, 'OD sin umbral con chirp · OI 50 (real 45)'], 'Bonificación chirp: un oído');
$extra = static fn (string $clave, string $esperado) => $item(['regla' => 'alguna_curva', 'clave' => $clave, 'esperado' => $esperado, 'bonus' => true]);
t_eq(OsceApp::evaluarItem($extra('rate', '81.1'), $prot)['alumno'], 'ninguna curva', 'Extra: sin curva a 81,1');
$r = OsceApp::evaluarItem($extra('stim', 'CE-Chirp LS'), $prot);
t_eq([$r['puntaje'], $r['alumno']], [1.0, 'sí: OI 80 dB, CE-Chirp LS'], 'Extra: alguna curva con chirp');
$conMkg = $prot;
$conMkg['curvas'][3]['mkg'] = 50;
$conMkg['curvas'][4]['clamp'] = 'sí';
$conMkg['curvas'][4]['transducer'] = 'bone_vibrator';
t_eq(OsceApp::evaluarItem($extra('mkg', '1–120'), $conMkg)['ok'], true, 'Extra: enmascaró');
t_eq(OsceApp::evaluarItem($extra('clamp', 'sí'), $conMkg)['ok'], true, 'Extra: pinzó el tubo');
t_eq(OsceApp::evaluarItem($extra('transducer', 'bone_vibrator'), $conMkg)['alumno'], 'sí: OD 20 dB, Vibrador óseo', 'Extra: vía ósea');
t_eq(OsceApp::evaluarItem($reg('polaridades'), $prot)['puntaje'], 0.0, 'Polaridades: no registró las dos');
$pol = $prot;
$pol['curvas'][] = $curva('R8', 'OD', 80, [], ['pol' => 'Rarefacción']);
$pol['curvas'][] = $curva('R9', 'OD', 80, [], ['pol' => 'Condensación']);
t_eq(OsceApp::evaluarItem($reg('polaridades'), $pol)['alumno'], 'sí: OD 80 dB', 'Polaridades: rarefacción y condensación en OD 80');
t_true(count(OsceApp::EXTRAS_BASE['peatc']) === 5, 'PEATC: 5 estrategias extra precargadas');
$cp = static fn (string $tambien = '') => $item(['regla' => 'curvas_param', 'clave' => 'transducer', 'esperado' => 'insert_earphone', 'tambien' => $tambien]);
t_eq(OsceApp::evaluarItem($cp(), $conMkg)['alumno'], '9 de 10 curvas (también Vibrador óseo)', 'Sin la estrategia del caso, la vía ósea descuenta');
$r = OsceApp::evaluarItem($cp('bone_vibrator'), $conMkg);
t_eq([$r['puntaje'], $r['esperado']], [1.0, 'Fono de inserción (o Vibrador óseo, por el caso)'], 'Con vía ósea pedida por el caso, no descuenta');
// Nunca bajó viendo respuesta: no buscó el umbral
$quieto = ['curvas' => [$curva('R1', 'OD', 80, ['V' => 5.6]), $curva('R2', 'OD', 80, ['V' => 5.6])]];
t_eq(OsceApp::evaluarItem($reg('baja', '20'), $quieto)['puntaje'], 0.0, 'Vio respuesta y nunca bajó: 0');
// Sin respuesta en ningún nivel: bien si de verdad no había
$sorda = ['curvas' => [$curva('R1', 'OD', 80, []), $curva('R2', 'OD', 90, []), $curva('R3', 'OD', 100, [])],
          'verdad' => ['R3' => ['visible' => false, 'threshold' => 120.0]]];
$r = OsceApp::evaluarItem($reg('umbral', '10'), $sorda);
t_eq([$r['puntaje'], $r['alumno']], [0.5, 'OD sin respuesta hasta 100 · OI sin curvas'], 'Sin respuesta y de verdad no había: bien ese oído');
t_eq(OsceApp::evaluarItem($reg('sube_max', '90–100'), $sorda)['puntaje'], 1.0, 'Sin V a 80 subió a 90–100');

// -- Totales: la bonificación no sube el máximo -----------------------------
$t = OsceApp::totales([
    ['item' => ['puntaje' => 2, 'critico' => 0, 'cfg' => []], 'puntaje' => 2.0],
    ['item' => ['puntaje' => 2, 'critico' => 0, 'cfg' => []], 'puntaje' => 1.0],
    ['item' => ['puntaje' => 1, 'critico' => 0, 'cfg' => ['bonus' => true]], 'puntaje' => 1.0],
]);
t_eq([$t['puntaje'], $t['puntaje_max']], [4.0, 4.0], 'Bonificación: completa el máximo pero no lo sube');
$t = OsceApp::totales([
    ['item' => ['puntaje' => 2, 'critico' => 0, 'cfg' => []], 'puntaje' => 2.0],
    ['item' => ['puntaje' => 1, 'critico' => 0, 'cfg' => ['bonus' => true]], 'puntaje' => 1.0],
]);
t_eq($t['puntaje'], 2.0, 'Nunca pasa del 100 %');

// -- Precargas ----------------------------------------------------------------
t_eq(OsceApp::ESPERADO['cvemp']['filter_passhigh'], '3', 'cVEMP: 3 Hz – 1,5 kHz');
t_eq(OsceApp::ESPERADO['ovemp']['filter_down'], '1000', 'oVEMP: 1 Hz – 1 kHz');
t_eq(OsceApp::ESTRATEGIA_BASE['cvemp']['sube'][1], '5', 'cVEMP: sin respuesta sube 5');
t_true(OsceApp::ESTRATEGIA_BASE['peatc']['umbral_chirp'][3], 'PEATC: el chirp es bonificación');
t_true(OsceApp::ESTRATEGIA_BASE['peatc']['polaridades'][3], 'PEATC: polaridades opuestas es bonificación');
t_eq(OsceApp::textoRegla('baja', '20'), 'Con respuesta, baja de 20 en 20 dB', 'Texto del criterio');

// -- Conclusión (la corrige la IA) -------------------------------------------
t_eq(OsceApp::leerCriterios("Describe ondas | 2\n\nConcluye | 1,5\nSin puntos\nMalo | 0"),
     [['Describe ondas', 2.0], ['Concluye', 1.5], ['Sin puntos', 1.0]], 'Criterios: "texto | puntos", sin puntos = 1, 0 no vale');
t_eq(OsceApp::leerCriterios(OsceApp::criteriosTexto(OsceApp::CRITERIOS_CONCLUSION['peatc'])), array_map(
    static fn ($c) => [$c[0], (float) $c[1]], OsceApp::CRITERIOS_CONCLUSION['peatc']), 'Criterios precargados ida y vuelta');
$r = OsceApp::evaluarItem($item(['regla' => 'ia', 'n' => 1]), []);
t_eq([$r['puntaje'], $r['pendiente']], [null, true], 'Criterio de IA sin corregir: pendiente, sin puntaje');
$ia = OsceApp::parsearIaConclusion('```json
{"criterios": [{"n": 1, "puntaje": 1.3, "comentario": "Bien OD."}, {"n": 2, "puntaje": 9, "comentario": "x"}, {"n": 7, "puntaje": 1}],
 "comentario_general": "Buen informe."}
```', [1 => 2.0, 2 => 2.0]);
t_eq($ia['criterios'], [1 => [1.5, 'Bien OD.'], 2 => [2.0, 'x']], 'IA: redondea a 0,5, recorta al máximo e ignora criterios que no existen');
t_eq($ia['general'], 'Buen informe.', 'IA: comentario general');
t_eq(OsceApp::parsearIaConclusion('no sé', [1 => 1.0]), null, 'IA ilegible: null');
$t = OsceApp::totales([
    ['item' => ['puntaje' => 2, 'critico' => 0, 'cfg' => ['regla' => 'ia']], 'puntaje' => null],
    ['item' => ['puntaje' => 2, 'critico' => 1, 'cfg' => ['regla' => 'ia']], 'puntaje' => null],
]);
t_eq([$t['puntaje'], $t['puntaje_max'], $t['critico_fallado']], [0.0, 4.0, false], 'Pendientes: cuentan 0 y no reprueban por crítico');
$datos = OsceApp::datosReales(['curvas' => [$curva('R1', 'OD', 80, ['V' => 5.6]), $curva('R2', 'OD', 10, [])],
    'verdad' => ['R1' => ['visible' => true, 'waves' => ['V' => ['lat' => 5.62, 'amp' => 0.5]], 'threshold' => 20.0],
                 'R2' => ['visible' => false, 'waves' => [], 'threshold' => 20.0]]],
    ['ABR' => ['OD' => ['type' => 'normal'], 'OI' => ['type' => 'coclear']]]);
t_true(strpos($datos, 'ABR OD: cuadro del caso = normal') !== false && strpos($datos, 'ABR OI: cuadro del caso = coclear') !== false, 'Datos reales: el cuadro de cada oído');
$soloV = OsceApp::datosReales(['modulo' => 'ABR', 'curvas' => [$curva('R1', 'OD', 20, [])],
    'verdad' => ['R1' => ['visible' => true, 'waves' => ['I' => ['lat' => 3.9, 'amp' => 0.0], 'V' => ['lat' => 7.7, 'amp' => 0.24]], 'threshold' => 20.0]]],
    ['ABR' => ['OD' => ['type' => 'normal']], 'VEMP' => ['OD' => ['type' => 'sacular']]]);
t_true(strpos($soloV, 'I 3,9') === false && strpos($soloV, 'V 7,70') !== false, 'Datos reales: sin las ondas que ya no se ven');
t_true(strpos($soloV, 'VEMP') === false, 'Datos reales: solo el equipo de la estación');
t_true(strpos($datos, 'OD 80 dB Click: HAY respuesta; V 5,62 ms') !== false, 'Datos reales: latencia verdadera');
t_true(strpos($datos, 'OD 10 dB Click: SIN respuesta; umbral real del oído 20 dB') !== false, 'Datos reales: sin respuesta y umbral');
t_true(strpos(OsceApp::informe(['abr' => ['hallazgos' => 'h', 'conclusion' => 'c']]), "HALLAZGOS:\nh\n\nCONCLUSIÓN:\nc") === 0, 'Informe del alumno');

// -- Tareas de una estación ------------------------------------------------------
$tarea = ['variantes' => [['case_id' => 'a'], ['case_id' => 'b'], ['case_id' => 'c']]];
t_eq(array_map(static fn ($n) => OsceApp::variante($tarea, $n, 0)['case_id'], [1, 2, 3, 4]), ['a', 'b', 'c', 'a'],
     'Variantes: el paciente sale del número del alumno');
t_eq(OsceApp::variante($tarea, 1, 1)['case_id'], 'b', 'Y se corre en cada tarea (no siempre "la primera" al mismo)');
t_eq(OsceApp::variante(['variantes' => []], 3, 0), null, 'Tarea sin paciente');
$varias = ['tareas' => [['panel' => ['pol' => 'Alternada']], ['panel' => ['pol' => 'Rarefacción']]]];
t_eq(OsceApp::payloadDe($varias, 1)['panel']['pol'], 'Rarefacción', 'Entrega por tarea: cada ítem lee la suya');
t_eq(OsceApp::payloadDe(['panel' => ['pol' => 'X']], 0)['panel']['pol'], 'X', 'Entrega de una sola tarea (como antes)');
t_eq(OsceApp::payloadDe($varias, 5), [], 'Tarea a la que no llegó: vacía');
t_eq(OsceApp::ondas('ecochg'), [['PS', 'PA'], ['PA']], 'ECochG: PS y PA arriba, PA en las demás');
t_eq(OsceApp::CANAL_LECTURA['mmn'], 'Fz', 'MMN se marca en Fz');
t_true(isset(OsceApp::parametros('p300')['tarea']) && !isset(OsceApp::parametros('peatc')['tarea']),
       'La instrucción al paciente solo en el oddball');
$cortical = ['curvas' => [
    ['nombre' => 'R1.Fz', 'canal' => 'Fz', 'side' => 'OD', 'int' => 70, 'marcas' => ['P3' => 300.0]],
    ['nombre' => 'R1.Pz', 'canal' => 'Pz', 'side' => 'OD', 'int' => 70, 'marcas' => ['P3' => 318.0]]],
    'verdad' => ['R1.Pz' => ['visible' => true, 'waves' => ['P3' => ['lat' => 330.0, 'amp' => 9.0]]]]];
$r = OsceApp::evaluarItem($item(['regla' => 'marca', 'lado' => 'OD', 'int' => 70, 'onda' => 'P3', 'tol_ms' => 25.0, 'canal' => 'Pz']), $cortical);
t_eq([$r['ok'], $r['alumno']], [true, '318,00 ms'], 'P3 se corrige en Pz, no en el primer canal');
