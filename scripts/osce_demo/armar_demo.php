<?php
// Arma en la base local los 3 OSCE de demostración (ETMP196, curso 2 de
// prod) con el código del sistema; después exportar.php los pasa a SQL.
declare(strict_types=1);
$B = __DIR__ . '/backend';
$_SERVER['HTTP_HOST'] = 'tmeduca.org';
$_SERVER['HTTPS'] = 'on';
$_SERVER['SCRIPT_NAME'] = '/labsim/backend/public/admin/x.php';
require $B . '/public/bootstrap.php';
foreach (['Osce', 'OsceApp', 'OscePauta', 'OscePreguntas'] as $c) {
    require_once $B . "/src/{$c}.php";
}

const CURSO = 2;      // ETMP196 en prod
const DOCENTE = 1;    // Nicolás Baier (admin) en prod
$pdo = Db::get();
$pdo->exec("INSERT OR IGNORE INTO courses (id, name) VALUES (2, 'MÉTODOS DE EXPLORACIÓN ELECTROFISIOLÓGICO ETMP196-20262')");

$sinTest = static function (array $e): array { unset($e['test']); return $e; };   // la prueba va fija en la estación
$var = static fn (array $ids, array $concl = []): array => array_map(
    static fn ($id) => ['case_id' => (string) $id, 'conclusion_esperada' => $concl[$id] ?? ''], $ids);
$criterios = static fn (string $ex): string => OsceApp::criteriosTexto(array_map(
    static fn ($c) => [$c[0], $c[1]], OsceApp::CRITERIOS_CONCLUSION[$ex]));

$ADULTOS = [110, 115, 133];          // adultos con PEATC, ECochG y VEMP normales
$CENTRAL = [157, 158, 159];          // adultos con latencia media y tardía normales
$LACTANTES = [102, 104, 26];         // lactantes, PEATC normal
$HIDROPS = [38, 119, 136];           // un oído coclear con PS/PA elevado (caso integrado)

$conclPeatc = [
    38 => 'OD: ondas I, III y V presentes y replicables a 80 dB nHL, con latencias absolutas e interpeaks (I-III, III-V, I-V) dentro de lo normal; la onda V se sigue hasta 20 dB nHL (umbral cerca de 15-20 dB nHL): audición normal. '
        . 'OI: ondas I, III y V presentes a 80 dB nHL, con latencias e interpeaks dentro de lo normal (onda I de menor amplitud); la onda V está a 40 dB y no a 20 dB nHL (umbral cerca de 35-40 dB nHL): hipoacusia sensorioneural de tipo coclear leve en el rango 2-4 kHz (unos 25-30 dB HL). Interpeaks normales: sin signos de compromiso retrococlear.',
    119 => 'OD: ondas I, III y V presentes a 80 dB nHL, con latencias e interpeaks dentro de lo normal; la onda V está a 40 dB y no a 20 dB nHL (umbral cerca de 30-40 dB nHL): hipoacusia sensorioneural de tipo coclear leve en el rango 2-4 kHz (unos 20-30 dB HL). Interpeaks normales: sin signos de compromiso retrococlear. '
        . 'OI: ondas I, III y V presentes y replicables a 80 dB nHL, con latencias absolutas e interpeaks dentro de lo normal; la onda V se sigue hasta 20 dB nHL (umbral cerca de 10-20 dB nHL): audición normal.',
    136 => 'OD: ondas I, III y V presentes y replicables a 80 dB nHL, con latencias absolutas e interpeaks dentro de lo normal; la onda V se sigue hasta 20 dB nHL (umbral cerca de 15-20 dB nHL): audición normal. '
        . 'OI: ondas I, III y V presentes a 80 dB nHL, con latencias e interpeaks dentro de lo normal (onda I de menor amplitud); la onda V está a 60 dB y no a 40 dB nHL (umbral cerca de 50-60 dB nHL): hipoacusia sensorioneural de tipo coclear moderada en el rango 2-4 kHz (unos 40-50 dB HL). Interpeaks normales: sin signos de compromiso retrococlear.',
];
$conclEcochg = [
    38 => 'OD: PS y PA presentes, razón PS/PA cerca de 0,25, dentro de lo normal: no compatible con hidrops. OI: PS y PA presentes, razón PS/PA cerca de 0,55, sobre el límite del electrodo (conducto 0,50): compatible con hidrops endolinfático en OI.',
    119 => 'OD: PS y PA presentes, razón PS/PA cerca de 0,64, sobre el límite del electrodo (conducto 0,50): compatible con hidrops endolinfático en OD. OI: PS y PA presentes, razón PS/PA cerca de 0,27, dentro de lo normal: no compatible con hidrops.',
    136 => 'OD: PS y PA presentes, razón PS/PA cerca de 0,17, dentro de lo normal: no compatible con hidrops. OI: PS y PA presentes, razón PS/PA cerca de 0,63, sobre el límite del electrodo (conducto 0,50): compatible con hidrops endolinfático en OI.',
];

$PREGUNTAS = [
    ['En el PEATC clínico, ¿qué polaridad indica el protocolo?', "*Alternada\nRarefacción\nCondensación"],
    ['¿Cuál es el límite de impedancia de cada electrodo en el PEATC clínico?', "*Menor a 5 kΩ\nMenor a 12 kΩ\nMenor a 20 kΩ\nNo hay límite si el registro se ve limpio"],
    ['En el PEATC, la diferencia de impedancia entre electrodos (interelectrodo) debe ser:', "*Menor a 2 kΩ\nMenor a 5 kΩ\nCualquiera, si cada electrodo está bajo 5 kΩ"],
    ['En el montaje del PEATC, ¿dónde va el electrodo rojo?', "*Mastoides derecha\nMastoides izquierda\nVértex\nFrente (ceja)"],
    ['¿Qué filtros indica el protocolo para el PEATC clínico?', "*100 a 3000 Hz\n1 a 30 Hz\n3 a 1500 Hz\n10 a 300 Hz"],
    ['Ante sospecha de neuropatía auditiva, ¿qué tasa de estimulación agrega el protocolo en el PEATC?', "*81,1 est/s\n11,1 est/s\n5,1 est/s"],
    ['Durante el cVEMP, ¿qué hace el paciente?', "*Gira la cabeza hacia el lado contrario al oído estimulado y la mantiene (contrae el esternocleidomastoideo)\nMira hacia arriba unos 30°\nCierra los ojos y se relaja\nAprieta los dientes"],
];

$IND = [
    'cfg_peatc' => 'Adulto derivado a PEATC clínico para estimar umbral. El montaje ya está hecho. Deja el equipo configurado según el protocolo para la primera curva (intensidad de partida incluida), lanza una curva para verificar que sale bien y, cuando estés de acuerdo, pasa al siguiente caso.',
    'cfg_ecochg' => 'Adulto derivado a electrococleografía por sospecha de hidrops. El montaje ya está hecho. Configura el equipo como se vio en clases, lanza una curva para verificar y, cuando estés de acuerdo, pasa al siguiente caso.',
    'cfg_p300' => 'Adulto derivado a P300. El montaje ya está hecho. Configura el oddball y el registro como se vio en clases (incluida la instrucción al paciente), lanza una curva para verificar y pasa al siguiente caso.',
    'cfg_cvemp' => 'Adulto derivado a cVEMP por vértigo. El montaje ya está hecho. Configura el equipo según el protocolo (incluida la maniobra del paciente), lanza una curva para verificar y termina.',
    'marcaje' => 'Las curvas ya están registradas. Marca las ondas que pide cada curva; donde no haya onda, no la marques. Puedes ir y volver entre los casos mientras te quede tiempo.',
    'protocolo' => 'Lactante de 3 meses que refiere en el tamizaje auditivo de ambos oídos. Llega dormido después de mamar y el montaje ya está hecho. Haz el PEATC clínico según el protocolo: busca el umbral de la onda V en cada oído.',
    'concl_peatc' => 'Adulto con hipoacusia y plenitud ótica de un lado. Las curvas del PEATC ya están registradas: márcalas y escribe el informe en el equipo (hallazgos y conclusión por oído).',
    'concl_ecochg' => 'El mismo paciente: las curvas de electrococleografía ya están registradas. Márcalas y escribe el informe (hallazgos y conclusión por oído).',
];

$BLOQUES = [['9:00', '2026-11-26 09:00', 5], ['10:00', '2026-11-26 10:00', 5], ['14:00', '2026-11-26 14:00', 4]];
$out = [];
foreach ($BLOQUES as [$hora, $inicio, $n]) {
    $id = Osce::crear(CURSO, Osce::limpiarConfig([
        'nombre' => "Demo OSCE ETMP196 · {$hora}", 'inicio_programado' => $inicio,
        'duracion_min' => 6, 'pausa_min' => 1, 'pausa_vueltas_min' => 0, 'circuitos' => 1,
        'exigencia' => 60, 'nota_aprobacion' => '4.0', 'rotacion' => 'cadena', 'por_turno' => 2,
    ]), DOCENTE, true);
    // Tarjetas: tantas como alumnos del bloque, sin dueño (cada uno amarra la suya con el QR).
    $ins = $pdo->prepare('INSERT INTO osce_participante (osce_id, user_id, numero, codigo, token) VALUES (?, NULL, ?, ?, ?)');
    $usados = [];
    for ($num = 1; $num <= $n; $num++) {
        do { $cod = Osce::nuevoCodigo(); } while (isset($usados[$cod]));
        $usados[$cod] = true;
        $ins->execute([$id, $num, $cod, bin2hex(random_bytes(12))]);
    }
    Osce::reasignar($id);

    $est = [];
    foreach (Osce::estaciones($id) as $e) {
        $est[$e['tipo']] = $e;
    }
    OscePauta::cargarBase((int) $est['pauta_docente']['id'], 'peatc');
    foreach ($PREGUNTAS as [$enun, $ops]) {
        OscePreguntas::agregar((int) $est['preguntas']['id'],
            OscePreguntas::limpiar(['tipo' => 'alternativa', 'enunciado' => $enun, 'opciones' => $ops, 'puntaje' => '1']));
    }
    OscePreguntas::tokenTablet((int) $est['preguntas']['id']);
    OscePreguntas::tokenTablet((int) $est['pauta_docente']['id']);

    $tarea = static function (string $tipo, array $t) use (&$est): void {
        $e = Osce::estacion((int) $est[$tipo]['id']);
        OsceApp::guardarTarea($e, count(OsceApp::tareas($e)), $t);
    };
    // 3 · Configuración: 4 tareas.
    $tarea('config_equipo', ['examen' => 'peatc', 'titulo' => 'PEATC umbral', 'peso' => 30, 'variantes' => $var($ADULTOS),
        'esperado' => OsceApp::ESPERADO_PEATC, 'indicaciones' => $IND['cfg_peatc']]);
    $tarea('config_equipo', ['examen' => 'ecochg', 'titulo' => 'Electrococleografía', 'peso' => 25, 'variantes' => $var($ADULTOS),
        'esperado' => $sinTest(OsceApp::ESPERADO['ecochg']), 'indicaciones' => $IND['cfg_ecochg']]);
    $tarea('config_equipo', ['examen' => 'p300', 'titulo' => 'P300', 'peso' => 25, 'variantes' => $var($CENTRAL),
        'esperado' => $sinTest(OsceApp::ESPERADO['p300']), 'indicaciones' => $IND['cfg_p300']]);
    $tarea('config_equipo', ['examen' => 'cvemp', 'titulo' => 'cVEMP', 'peso' => 20, 'variantes' => $var($ADULTOS),
        'esperado' => OsceApp::ESPERADO['cvemp'], 'indicaciones' => $IND['cfg_cvemp']]);
    // 4 · Marcaje: 6 tareas.
    foreach ([['peatc', 'PEATC', 25, $ADULTOS, "OD 80\nOD 40\nOI 80\nOI 40"], ['cvemp', 'cVEMP', 20, $ADULTOS, "OD 120\nOI 120"],
              ['ecochg', 'Electrococleografía', 15, $ADULTOS, "OD 90\nOI 90"], ['latencia_media', 'Latencia media (MLR)', 15, $CENTRAL, "OD 70\nOI 70"],
              ['latencia_tardia', 'Latencia tardía (CAEP)', 15, $CENTRAL, "OD 70\nOI 70"], ['p300', 'P300', 10, $CENTRAL, "OD 70"]] as [$ex, $tit, $peso, $ids, $curvas]) {
        $tarea('marcaje', ['examen' => $ex, 'titulo' => $tit, 'peso' => $peso, 'variantes' => $var($ids), 'curvas' => $curvas,
                           'indicaciones' => $IND['marcaje']]);
    }
    // 5 · Protocolo: lactante, PEATC con su estrategia del protocolo.
    $estr = [];
    foreach (OsceApp::ESTRATEGIA_BASE['peatc'] as $clave => [$activa, $valor, $pts, $bonus]) {
        $estr[$clave] = ['activa' => $activa ? '1' : '', 'valor' => $valor, 'puntos' => (string) $pts, 'bonus' => $bonus ? '1' : ''];
    }
    $tarea('protocolo', ['examen' => 'peatc', 'titulo' => 'Lactante: PEATC de umbral', 'peso' => 100, 'variantes' => $var($LACTANTES),
        'onda' => 'V', 'esperado' => OsceApp::ESPERADO_CURVAS['peatc'], 'estrategia' => $estr,
        'extras' => OsceApp::extras(['examen' => 'peatc']), 'indicaciones' => $IND['protocolo']]);
    // 6 · Conclusión: caso integrado PEATC + ECochG del mismo paciente (mismo orden de pacientes).
    $tarea('conclusion', ['examen' => 'peatc', 'titulo' => 'PEATC', 'peso' => 50, 'variantes' => $var($HIDROPS, $conclPeatc),
        'curvas' => OsceApp::CURVAS_BASE, 'criterios' => $criterios('peatc'), 'indicaciones' => $IND['concl_peatc']]);
    $tarea('conclusion', ['examen' => 'ecochg', 'titulo' => 'Electrococleografía', 'peso' => 50, 'variantes' => $var($HIDROPS, $conclEcochg),
        'curvas' => "OD 90\nOI 90", 'criterios' => $criterios('ecochg'), 'indicaciones' => $IND['concl_ecochg']]);
    foreach (['config_equipo', 'marcaje', 'protocolo', 'conclusion'] as $t) {
        OsceApp::codigoEstacion((int) $est[$t]['id']);
    }
    $out[] = ['osce' => $id, 'bloque' => $hora, 'tarjetas' => $n];
}
echo json_encode($out, JSON_UNESCAPED_UNICODE), "\n";
