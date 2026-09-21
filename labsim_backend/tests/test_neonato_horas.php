<?php

declare(strict_types=1);

/**
 * El recién nacido de turno: horas de vida, screening y transitorio.
 *
 * Es el escenario que la edad en años enteros no podía representar. Un bebé
 * de seis horas y uno de once meses son los dos "0 años" y no se parecen en
 * nada: el primero tiene vérnix en el conducto y mesénquima en el oído
 * medio, así que la EOA refiere en más de la mitad de los recién nacidos
 * SANOS mientras el AABR pasa en el 85%.
 *
 * Las tasas salen de la bibliografía (ver NewbornScreening) y los decibeles
 * salen de las tasas, no al revés. Por eso el test que más importa es el que
 * comprueba que el modelo REPRODUCE la tabla publicada.
 */

require_once dirname(__DIR__) . '/src/CaseProfile.php';
require_once dirname(__DIR__) . '/src/CaseBuilder.php';
require_once dirname(__DIR__) . '/src/NewbornScreening.php';

/** Oído normal: 10 dB HL parejos por aire y por hueso. */
function neo_audiograma(): array
{
    $curva = [];
    foreach (CaseBuilder::FREQUENCIES as $f) {
        $curva[] = [10, 10];
    }
    return $curva;
}

function neo_proyeccion($horas, array $nacimiento = [], $meses = null): array
{
    $curva = neo_audiograma();
    return CaseProfile::project(
        $curva, $curva,
        ['OD' => ['cce_pct' => 0, 'retro' => []], 'OI' => ['cce_pct' => 0, 'retro' => []]],
        ['OD' => 'A', 'OI' => 'A'],
        $horas, $meses, $nacimiento
    );
}

// --- Lo central: se reproduce la tabla publicada -------------------------

// Se barre el percentil de punta a punta y se cuenta qué proporción pasa.
// Si alguien toca los umbrales en dB, esto lo caza.
foreach ([[6, 0.40, 0.85], [18, 0.55, 0.92], [30, 0.75, 0.95],
          [42, 0.85, 0.96], [60, 0.93, 0.97], [96, 0.95, 0.97]] as [$h, $objTeoae, $objAabr]) {
    $pasaTeoae = 0;
    $pasaAabr = 0;
    $n = 2000;
    for ($i = 0; $i < $n; $i++) {
        $db = NewbornScreening::transientDb((float) $h, [], ($i + 0.5) / $n);
        $r = NewbornScreening::resultado($db);
        $pasaTeoae += $r['teoae'] === 'pasa' ? 1 : 0;
        $pasaAabr += $r['aabr'] === 'pasa' ? 1 : 0;
    }
    t_close($pasaTeoae / $n, $objTeoae, 0.01, "A las {$h} h la TEOAE pasa en la proporción publicada");
    t_close($pasaAabr / $n, $objAabr, 0.01, "A las {$h} h el AABR pasa en la proporción publicada");
}

// El AABR siempre aguanta más que la TEOAE: es la misma conductiva y el
// AABR necesita mucha más para caerse.
for ($i = 1; $i < 20; $i++) {
    $db = NewbornScreening::transientDb(6.0, [], $i / 20);
    $r = NewbornScreening::resultado($db);
    t_true(
        !($r['aabr'] === 'refiere' && $r['teoae'] === 'pasa'),
        'Ningún bebé refiere el AABR y pasa la TEOAE por el transitorio'
    );
}

// --- Modificadores --------------------------------------------------------

// Cesárea: sin trabajo de parto no se exprime el líquido, así que a la misma
// edad pasa menos.
t_true(
    NewbornScreening::passProbability('teoae', 30.0, ['cesarea' => true])
    < NewbornScreening::passProbability('teoae', 30.0),
    'Cesárea: a la misma edad la TEOAE pasa menos'
);
// Y le pega mucho menos al AABR que a la EOA (-4 h contra -12 h).
$caidaTeoae = NewbornScreening::passProbability('teoae', 30.0)
    - NewbornScreening::passProbability('teoae', 30.0, ['cesarea' => true]);
$caidaAabr = NewbornScreening::passProbability('aabr', 30.0)
    - NewbornScreening::passProbability('aabr', 30.0, ['cesarea' => true]);
t_true($caidaTeoae > $caidaAabr, 'La cesárea le pega más a la EOA que al AABR');

t_true(
    NewbornScreening::passProbability('teoae', 30.0, ['peg' => true])
    > NewbornScreening::passProbability('teoae', 30.0),
    'Pequeño para la edad gestacional: pasa algo mejor'
);

// Limpiar el vérnix no cambia la edad: corta a la mitad lo que refiere.
$sinLimpiar = 1.0 - NewbornScreening::passProbability('teoae', 6.0);
$limpiado = 1.0 - NewbornScreening::passProbability('teoae', 6.0, ['vernix_limpiado' => true]);
t_close($limpiado, $sinLimpiar * 0.5, 0.001, 'Limpiar el vérnix corta a la mitad lo que refiere la TEOAE');

// Líquido persistente: deja de ser cuestión de horas.
t_close(NewbornScreening::passProbability('teoae', 96.0, ['liquido_persistente' => true]),
    0.20, 0.001, 'Con líquido persistente la TEOAE pasa en 20% aunque hayan pasado días');
t_close(NewbornScreening::passProbability('aabr', 96.0, ['liquido_persistente' => true]),
    0.80, 0.001, 'Y el AABR en 80%');

// Pasado el primer mes esto ya no es screening neonatal.
t_close(NewbornScreening::transientDb(2000.0, [], 0.99), 0.0, 0.001,
    'A los tres meses no queda transitorio del parto');

// --- Lo que ve el alumno en los tres exámenes ----------------------------

// Un bebé con MUCHO transitorio (percentil alto) a las 6 horas.
$cargado = ['percentil' => ['OD' => 0.99, 'OI' => 0.99]];
$recien = neo_proyeccion(6.0, $cargado);
$dosDias = neo_proyeccion(48.0, $cargado);
$sinDato = neo_proyeccion(null);

t_true(
    ($recien['eoas']['OD']['atten_db'] ?? 0) > 10.0,
    'Con el transitorio cargado la EOA queda bajo criterio: refiere'
);
t_eq($sinDato['eoas']['OD']['atten_db'] ?? null, null, 'Sin horas de vida no se toca la EOA');

// El tipo del oído NO cambia: es un oído normal con un transitorio, no una
// patología de transmisión. Si se derivara como conductivo, el alumno leería
// una hipoacusia donde no la hay.
t_eq($recien['eoas']['OD']['type'], 'normal', 'El oído sigue siendo normal, el transitorio no es patología');
t_eq($recien['abr']['OD']['type'], 'normal', 'Y el ABR tampoco se vuelve conductivo');

// Aérea sí, ósea no: el vibrador saltea conducto y oído medio.
$aereo = $recien['abr']['OD']['umbral_por_estimulo']['click'];
$oseo = $recien['abr']['OD']['umbral_por_estimulo_oseo']['click'];
t_true($aereo > $sinDato['abr']['OD']['umbral_por_estimulo']['click'],
    'El ABR aéreo del recién nacido cargado sale elevado');
t_eq($oseo, $sinDato['abr']['OD']['umbral_por_estimulo_oseo']['click'],
    'El ABR óseo NO: el vibrador saltea conducto y oído medio');

// A las 48 horas el mismo bebé ya está limpio.
t_true(
    ($dosDias['eoas']['OD']['atten_db'] ?? 0) < ($recien['eoas']['OD']['atten_db'] ?? 0),
    'A las 48 horas queda mucho menos transitorio que a las 6'
);

// Los dos oídos pueden dar distinto: es lo que se ve en el turno.
$dispar = neo_proyeccion(6.0, ['percentil' => ['OD' => 0.05, 'OI' => 0.99]]);
t_true(
    ($dispar['eoas']['OD']['atten_db'] ?? 0) < ($dispar['eoas']['OI']['atten_db'] ?? 0),
    'Cada oído tiene su propio percentil: uno puede referir y el otro no'
);

// --- Referencia de la vía ósea ---------------------------------------------

// El 0 dB nHL óseo no está referenciado como el aéreo: la fuerza que lo
// define se mide sobre cráneo adulto. Cobb y Stuart 2016 miden, con click y
// audición normal: adultos 3,75 dB nHL por aire contra 18,75 por hueso;
// lactantes 3,75 y 1,25. O sea, el que muestra gap aparente es el ADULTO.

t_close(CaseProfile::boneNhlOffset(360), 15.0, 0.01, 'Adulto: la ósea lee ~15 dB más alto que la aérea');
t_close(CaseProfile::boneNhlOffset(1), -2.5, 0.01, 'Lactante: la ósea lee igual o algo mejor que la aérea');
t_true(
    CaseProfile::boneNhlOffset(12) > CaseProfile::boneNhlOffset(3)
    && CaseProfile::boneNhlOffset(12) < CaseProfile::boneNhlOffset(360),
    'Entre los 6 y los 24 meses la referencia se va corriendo a la de adulto'
);
t_close(CaseProfile::boneNhlOffset(null), 15.0, 0.01, 'Sin edad se asume adulto, no lactante');

$adulto = neo_proyeccion(null, [], 360.0);
$bebe = neo_proyeccion(null, [], 3.0);

$aAdulto = $adulto['abr']['OD']['umbral_por_estimulo']['click'];
$oAdulto = $adulto['abr']['OD']['umbral_por_estimulo_oseo']['click'];
$aBebe = $bebe['abr']['OD']['umbral_por_estimulo']['click'];
$oBebe = $bebe['abr']['OD']['umbral_por_estimulo_oseo']['click'];

t_true($oAdulto - $aAdulto >= 10, 'El adulto normal muestra gap aéreo-óseo aparente, que no es conductivo');
t_true(abs($oBebe - $aBebe) <= 5, 'El lactante normal no lo muestra: sus dos vías dan casi lo mismo');
t_true($oBebe < $oAdulto, 'Y su umbral óseo es más bajo que el del adulto con la misma audición');

// --- El vibrador no llega: la ventana útil es angosta ---------------------

// Con la referencia corregida, un normoyente adulto ya gasta la mitad del
// margen. Una sensorial leve deja la vía ósea fuera de alcance, y eso NO es
// un error del examen: es por qué el ABR óseo sirve para pérdidas leves y
// moderadas y deja de servir enseguida.
function neo_umbral_oseo(float $hlAire, float $hlOseo, float $meses)
{
    $aire = [];
    $oseo = [];
    foreach (CaseBuilder::FREQUENCIES as $f) {
        $aire[] = [$hlAire, $hlAire];
        $oseo[] = [$hlOseo, $hlOseo];
    }
    $p = CaseProfile::project(
        $aire, $oseo,
        ['OD' => ['cce_pct' => 0, 'retro' => []], 'OI' => ['cce_pct' => 0, 'retro' => []]],
        ['OD' => 'A', 'OI' => 'A'], null, $meses
    );
    return $p['abr']['OD']['umbral_por_estimulo_oseo']['click'];
}

t_true(neo_umbral_oseo(0, 0, 360) <= CaseProfile::BONE_MAX_OUTPUT_DB,
    'El adulto normal todavía entra en el rango del vibrador');
t_true(neo_umbral_oseo(30, 30, 360) !== null,
    'Con sensorial de 30 dB HL la ósea todavía entra, justo en el tope');
t_eq(neo_umbral_oseo(35, 35, 360), null,
    'Con 35 dB HL el vibrador ya no llega: sin respuesta por vía ósea');
// La conductiva es para lo que sirve: la ósea se queda abajo aunque la
// aérea se vaya lejos.
t_true(neo_umbral_oseo(60, 10, 360) !== null,
    'Una conductiva de 50 dB deja ver la ósea perfectamente');
t_true(neo_umbral_oseo(40, 0, 360) !== null,
    'Una conductiva de 40 dB sí deja ver la ósea: es justo para lo que sirve');
