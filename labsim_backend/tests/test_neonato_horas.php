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
