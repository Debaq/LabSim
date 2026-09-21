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

// --- Calibración ósea del lactante ---------------------------------------

// El cráneo sin suturar transmite mejor, sobre todo en graves, y el vibrador
// está calibrado sobre cráneo adulto: el mismo oído da un umbral óseo más
// bajo en el dial. Lo que importa clínicamente es que eso INFLA el gap
// aéreo-óseo aparente, y es un error de lectura clásico en screening.

t_close(CaseProfile::infantBoneFactor(null), 0.0, 0.01, 'Sin edad no se inventa un lactante');
t_close(CaseProfile::infantBoneFactor(3), 1.0, 0.01, 'Bajo 6 meses la calibración aplica entera');
t_close(CaseProfile::infantBoneFactor(24), 0.0, 0.01, 'A los 2 años ya no queda: las suturas se cerraron');
t_true(
    CaseProfile::infantBoneFactor(12) > 0 && CaseProfile::infantBoneFactor(12) < 1,
    'Entre los 6 y los 24 meses se va de a poco'
);

$lactante = neo_proyeccion(null, [], 3.0);
$adulto = neo_proyeccion(null, [], 360.0);
$dosAnios = neo_proyeccion(null, [], 24.0);

$graveLact = $lactante['abr']['OD']['umbral_por_estimulo_oseo']['tone_burst_500Hz'];
$graveAdulto = $adulto['abr']['OD']['umbral_por_estimulo_oseo']['tone_burst_500Hz'];

t_true($graveLact < $graveAdulto, 'En 500 Hz el lactante lee un umbral óseo más bajo que el adulto');
t_eq(
    $lactante['abr']['OD']['umbral_por_estimulo_oseo']['tone_burst_4000Hz'],
    $adulto['abr']['OD']['umbral_por_estimulo_oseo']['tone_burst_4000Hz'],
    'En 4 kHz no hay diferencia: el efecto es de graves'
);
t_eq(
    $dosAnios['abr']['OD']['umbral_por_estimulo_oseo']['tone_burst_500Hz'],
    $graveAdulto,
    'A los 2 años el umbral óseo ya es el de adulto'
);
t_eq(
    $lactante['abr']['OD']['umbral_por_estimulo']['tone_burst_500Hz'],
    $adulto['abr']['OD']['umbral_por_estimulo']['tone_burst_500Hz'],
    'La vía aérea no cambia con la calibración ósea'
);

// Y el efecto que hay que saber leer: gap aparente en un oído normal.
$gapLact = $lactante['abr']['OD']['umbral_por_estimulo']['tone_burst_500Hz'] - $graveLact;
$gapAdulto = $adulto['abr']['OD']['umbral_por_estimulo']['tone_burst_500Hz'] - $graveAdulto;
t_eq($gapAdulto, 0, 'En el adulto normal no hay gap');
t_true($gapLact >= 10, 'En el lactante normal aparece un gap de calibración, que no es conductivo');
