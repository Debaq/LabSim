<?php

declare(strict_types=1);

/**
 * El recién nacido de turno: horas de vida y su transitorio.
 *
 * Es el escenario que la edad en años enteros no podía representar. Un bebé
 * de seis horas y uno de once meses son los dos "0 años" y no se parecen en
 * nada: el primero tiene vérnix en el conducto y mesénquima en el oído
 * medio, así que la EOA sale AUSENTE en un oído que oye perfecto, mientras
 * el ABR --y sobre todo el ABR óseo-- dice que no hay hipoacusia.
 */

require_once dirname(__DIR__) . '/src/CaseProfile.php';
require_once dirname(__DIR__) . '/src/CaseBuilder.php';

/** Oído normal: 10 dB HL parejos por aire y por hueso. */
function neo_audiograma(): array
{
    $curva = [];
    foreach (CaseBuilder::FREQUENCIES as $f) {
        $curva[] = [10, 10];
    }
    return $curva;
}

function neo_proyeccion($horas): array
{
    $curva = neo_audiograma();
    return CaseProfile::project(
        $curva, $curva,
        ['OD' => ['cce_pct' => 0, 'retro' => []], 'OI' => ['cce_pct' => 0, 'retro' => []]],
        ['OD' => 'A', 'OI' => 'A'],
        $horas
    );
}

// --- La ley del transitorio ----------------------------------------------

t_close(CaseProfile::neonatalTransientDb(null), 0.0, 0.01, 'Sin horas de vida no hay transitorio');
t_close(CaseProfile::neonatalTransientDb(''), 0.0, 0.01, 'Campo vacío tampoco');
t_true(CaseProfile::neonatalTransientDb(0) > 25.0, 'Recién nacido: el transitorio arranca fuerte');
t_true(
    CaseProfile::neonatalTransientDb(0) > CaseProfile::neonatalTransientDb(24),
    'A las 24 horas ya bajó'
);
t_true(CaseProfile::neonatalTransientDb(48) < 5.0, 'A las 48 horas casi no queda');
t_close(CaseProfile::neonatalTransientDb(168), 0.0, 0.01, 'A la semana no queda nada');
t_close(CaseProfile::neonatalTransientDb(500), 0.0, 0.01, 'Y no reaparece después');

// --- El hallazgo: EOA ausente con audición normal -------------------------

$recien = neo_proyeccion(6);
$dosDias = neo_proyeccion(48);
$sinDato = neo_proyeccion(null);

t_true(
    ($recien['eoas']['OD']['atten_db'] ?? 0) > 40.0,
    'A las 6 horas la EOA queda por debajo del piso: sale ausente'
);
t_true(
    ($dosDias['eoas']['OD']['atten_db'] ?? 0) < 12.0,
    'A las 48 horas la EOA vuelve'
);
t_eq($sinDato['eoas']['OD']['atten_db'] ?? null, null, 'Sin horas de vida no se toca la EOA');

// El tipo del oído NO cambia: es un oído normal con un transitorio, no una
// patología de transmisión. Si se derivara como conductivo, el alumno leería
// una hipoacusia donde no la hay.
t_eq($recien['eoas']['OD']['type'], 'normal', 'El oído sigue siendo normal, el transitorio no es patología');
t_eq($recien['abr']['OD']['type'], 'normal', 'Y el ABR tampoco se vuelve conductivo');

// --- Aérea sí, ósea no ----------------------------------------------------

$aereo = $recien['abr']['OD']['umbral_por_estimulo']['click'];
$oseo = $recien['abr']['OD']['umbral_por_estimulo_oseo']['click'];
$aereoSano = $sinDato['abr']['OD']['umbral_por_estimulo']['click'];
$oseoSano = $sinDato['abr']['OD']['umbral_por_estimulo_oseo']['click'];

t_true($aereo > $aereoSano, 'El ABR aéreo del recién nacido sale algo elevado');
t_eq($oseo, $oseoSano, 'El ABR óseo NO: el vibrador saltea conducto y oído medio');
t_true($aereo - $oseo > 5, 'Queda un gap aéreo-óseo, que es lo que dice que es transitorio');

// A las 48 horas el gap se cerró solo.
t_eq(
    $dosDias['abr']['OD']['umbral_por_estimulo']['click'],
    $dosDias['abr']['OD']['umbral_por_estimulo_oseo']['click'],
    'A las 48 horas el gap ya no está'
);

// --- La EOA sufre más que el ABR ------------------------------------------

t_true(
    CaseProfile::NEONATAL_OAE_FACTOR > CaseProfile::NEONATAL_ABR_FACTOR * 2,
    'La EOA cruza el conducto de ida y vuelta: le pega mucho más que al ABR'
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

function neo_proyeccion_meses(float $meses): array
{
    $curva = neo_audiograma();
    return CaseProfile::project(
        $curva, $curva,
        ['OD' => ['cce_pct' => 0, 'retro' => []], 'OI' => ['cce_pct' => 0, 'retro' => []]],
        ['OD' => 'A', 'OI' => 'A'],
        null, $meses
    );
}

$lactante = neo_proyeccion_meses(3.0);
$adulto = neo_proyeccion_meses(360.0);
$dosAnios = neo_proyeccion_meses(24.0);

$graveLact = $lactante['abr']['OD']['umbral_por_estimulo_oseo']['tone_burst_500Hz'];
$graveAdulto = $adulto['abr']['OD']['umbral_por_estimulo_oseo']['tone_burst_500Hz'];
$agudoLact = $lactante['abr']['OD']['umbral_por_estimulo_oseo']['tone_burst_4000Hz'];
$agudoAdulto = $adulto['abr']['OD']['umbral_por_estimulo_oseo']['tone_burst_4000Hz'];

t_true($graveLact < $graveAdulto, 'En 500 Hz el lactante lee un umbral óseo más bajo que el adulto');
t_eq($agudoLact, $agudoAdulto, 'En 4 kHz no hay diferencia: el efecto es de graves');
t_eq(
    $dosAnios['abr']['OD']['umbral_por_estimulo_oseo']['tone_burst_500Hz'],
    $graveAdulto,
    'A los 2 años el umbral óseo ya es el de adulto'
);

// La vía AÉREA no se toca: entra por el conducto y no le importa el cráneo.
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
