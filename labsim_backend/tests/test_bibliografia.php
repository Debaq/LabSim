<?php

declare(strict_types=1);

/**
 * Bibliografía central (Bibliografia): toda cita que se muestra tiene a
 * qué corresponde, y ninguna fuente de la planilla ABR se pierde -- o
 * respalda algo o queda en la lista de "sin uso", nunca en ninguna.
 */

require_once dirname(__DIR__) . '/src/Bibliografia.php';

foreach (Bibliografia::SECCIONES as $sid => $sec) {
    $fuentes = Bibliografia::fuentes($sid);
    t_true(count($fuentes) > 0, "Bibliografía {$sid}: tiene fuentes");
    foreach ($fuentes as $fid => $f) {
        t_true(!empty($f['cita']), "Bibliografía {$sid}/{$fid}: tiene cita");
        t_true(!empty($f['usa']), "Bibliografía {$sid}/{$fid}: dice a qué corresponde");
        t_true(isset($f['enlace']), "Bibliografía {$sid}/{$fid}: tiene enlace (o 'Sin enlace')");
        if (($f['verificada'] ?? true) === false) {
            t_true(!empty($f['nota']), "Bibliografía {$sid}/{$fid}: sin verificar y dice qué falta");
        }
    }
}

$abr = array_keys(Bibliografia::fuentes('abr'));
$sinUso = array_keys(Bibliografia::sinUsoAbr());
foreach (array_keys(AbrReferences::FUENTES) as $fid) {
    t_true(in_array($fid, $abr, true) xor in_array($fid, $sinUso, true),
        "Fuente ABR {$fid}: está una sola vez, con uso o sin uso");
}
t_eq(count(AbrReferences::FUENTES), 27, 'Las 27 fuentes de la planilla están cargadas');
foreach (array_keys(Bibliografia::USO_ABR) as $fid) {
    t_true(isset(AbrReferences::FUENTES[$fid]), "Uso ABR {$fid}: la fuente existe");
}

// --- Técnicas de examen -----------------------------------------------------

// La técnica es la referencia del indicador de efectividad: sin pasos no hay
// nada contra qué comparar. Sus fuentes, cuando lleguen, siguen las mismas
// reglas que las demás.
foreach (Bibliografia::TECNICAS as $tid => $t) {
    t_true(!empty($t['titulo']) && !empty($t['pasos']), "Técnica {$tid}: tiene título y pasos");
    t_true(!empty($t['usa']), "Técnica {$tid}: dice a qué corresponde");
    t_true(is_array($t['fuentes']), "Técnica {$tid}: fuentes es una lista (vacía si falta investigar)");
    foreach ($t['fuentes'] as $fid => $f) {
        t_true(!empty($f['cita']) && isset($f['enlace']), "Técnica {$tid}/{$fid}: tiene cita y enlace");
        if (($f['verificada'] ?? true) === false) {
            t_true(!empty($f['nota']), "Técnica {$tid}/{$fid}: sin verificar y dice qué falta");
        }
    }
}

// --- Patologías del generador ----------------------------------------------

// El porqué se lee de los comentarios de CaseProfile.php: si el parser se
// rompe (cambió la indentación, se movió la constante), el cuadro se
// queda sin ejes o con ejes repetidos sin que nadie lo note.
$catalogo = Bibliografia::cuadros();
t_eq(count($catalogo['cuadros']), count(CaseProfile::SCENARIOS), 'Bibliografía: están todos los cuadros');
$conPorque = 0;
foreach (CaseProfile::SCENARIOS as $clave => $sc) {
    $ejes = [];
    foreach ($catalogo['cuadros'][$clave]['filas'] ?? [] as $fila) {
        $ejes = array_merge($ejes, $fila['ejes']);
        if ($fila['porque'] !== '') {
            $conPorque++;
        }
    }
    $esperados = array_values(array_intersect(array_keys(Bibliografia::EJES), array_keys($sc)));
    sort($ejes);
    sort($esperados);
    t_eq($ejes, $esperados, "Cuadro {$clave}: cada eje aparece una sola vez");
}
t_true($conPorque > 100, 'Bibliografía: el parser encontró los comentarios de los cuadros');
foreach (Bibliografia::PATOLOGIAS as $clave => $citas) {
    t_true(isset(CaseProfile::SCENARIOS[$clave]), "Bibliografía de {$clave}: el cuadro existe");
    foreach ($citas as $i => $c) {
        t_true(isset(Bibliografia::EJES[$c['eje']]) || $c['eje'] === 'general', "Cita {$clave}#{$i}: eje válido");
        t_true(!empty($c['cita']) && !empty($c['respalda']), "Cita {$clave}#{$i}: tiene cita y qué respalda");
        t_true(in_array($c['coincide'] ?? '', ['si', 'parcial', 'no'], true), "Cita {$clave}#{$i}: dice si coincide");
    }
}

// Revisión del 2026-10-08: todo cuadro tiene literatura y ninguna cita queda
// "a medias". Si la literatura difiere, o se aplica al generador o la nota
// dice por qué el generador difiere a propósito.
foreach (CaseProfile::SCENARIOS as $clave => $_) {
    t_true(!empty(Bibliografia::PATOLOGIAS[$clave]), "Cuadro {$clave}: tiene bibliografía");
}
foreach (Bibliografia::PATOLOGIAS as $clave => $citas) {
    foreach ($citas as $i => $c) {
        t_eq($c['coincide'], 'si', "Cita {$clave}#{$i}: revisada (ni parcial ni contradicha)");
    }
}

// "Para su teoría": lo que el generador muestra siempre alterado y en la
// realidad no siempre tiene que quedar a la vista del docente, no enterrado
// en la nota de una cita.
$decisiones = Bibliografia::decisiones();
$ejesDe = function (string $clave) use ($decisiones): array {
    return array_column($decisiones[$clave] ?? [], 'eje');
};
t_true(in_array('ecochg', $ejesDe('meniere'), true), 'Para su teoría: el Ménière con ECochG normal');
t_true(in_array('vemp', $ejesDe('esclerosis_multiple'), true), 'Para su teoría: la EM con VEMP normal');
foreach ($decisiones as $clave => $lista) {
    foreach ($lista as $d) {
        t_true($d['texto'] !== '', "Para su teoría de {$clave}: dice algo");
    }
}
$pagina = (string) @file_get_contents(dirname(__DIR__) . '/public/admin/bibliografia.php');
t_true(strpos($pagina, 'id="decisiones"') !== false, 'La página tiene la sección Para su teoría');
