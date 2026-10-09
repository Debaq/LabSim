<?php
/**
 * Técnica de audiometría en el tiempo y pasos que más cuestan: lo mismo en
 * la ficha del docente (admin/student.php) y en la del alumno
 * (student/mis_pacientes.php). Estilos en css/indicadores.css.
 */

require_once __DIR__ . '/../../src/AudiometriaTecnicaVista.php';

/**
 * Un punto por audiometría sobre las bandas 85/60 %.
 *
 * @param array<int,array{pct:int, fecha:string, paciente:string, practica:bool, href:string}> $serie
 *        en orden cronológico (la más vieja primero)
 */
function indicadores_tecnica_grafico(array $serie): void
{
    // x = orden de la atención, y = % de logro. El SVG se estira a lo ancho;
    // los puntos van en HTML encima para que sean redondos y tengan enlace.
    $n = count($serie);
    $ancho = 600;
    $alto = 140;
    $margen = 14;
    $x = static fn(int $i): float => $n === 1 ? $ancho / 2 : $margen + $i * ($ancho - 2 * $margen) / ($n - 1);
    $y = static fn(int $pct): float => $margen + (100 - $pct) * ($alto - 2 * $margen) / 100;
    $puntos = [];
    foreach ($serie as $i => $p) {
        $puntos[] = round($x($i), 1) . ',' . round($y($p['pct']), 1);
    }
    ?>
    <svg class="tec-grafico" viewBox="0 0 <?= $ancho ?> <?= $alto ?>" preserveAspectRatio="none" role="img"
         aria-label="Logro de la técnica en cada audiometría, de la primera a la última">
        <rect x="0" y="<?= $y(100) ?>" width="<?= $ancho ?>" height="<?= $y(85) - $y(100) ?>" class="tec-banda tec-banda--bien"/>
        <rect x="0" y="<?= $y(85) ?>" width="<?= $ancho ?>" height="<?= $y(60) - $y(85) ?>" class="tec-banda tec-banda--medio"/>
        <rect x="0" y="<?= $y(60) ?>" width="<?= $ancho ?>" height="<?= $y(0) - $y(60) ?>" class="tec-banda tec-banda--bajo"/>
        <?php if ($n > 1): ?><polyline points="<?= implode(' ', $puntos) ?>" class="tec-linea" vector-effect="non-scaling-stroke"/><?php endif; ?>
    </svg>
    <div class="tec-puntos">
        <?php foreach ($serie as $i => $p): ?>
        <a class="tec-punto<?= $p['practica'] ? ' tec-punto--practica' : '' ?>"
           style="left:<?= round($x($i) / $ancho * 100, 2) ?>%; top:<?= round($y($p['pct']) / $alto * 100, 2) ?>%; --c:<?= AudiometriaTecnicaVista::color($p['pct']) ?>;"
           href="<?= htmlspecialchars($p['href']) ?>"
           title="<?= htmlspecialchars($p['fecha'] . ' · ' . ($p['paciente'] ?: 'sin nombre') . ' · ' . $p['pct'] . ' %' . ($p['practica'] ? ' (práctica libre)' : '')) ?>"></a>
        <?php endforeach; ?>
    </div>
    <?php
}

/**
 * Los pasos que no cumplió, con la barra de cuántas veces.
 *
 * @param array<int,array{seccion:string, texto:string, fallos:int, evaluadas:int}> $pasos
 *        de AlumnoIndicadores::pasosDificiles
 */
function indicadores_pasos(array $pasos): void
{
    ?>
    <div class="pasos">
        <?php foreach ($pasos as $paso): ?>
        <?php $pctFallo = (int) round(100 * $paso['fallos'] / $paso['evaluadas']); ?>
        <div class="paso">
            <span class="tag tag--muted"><?= htmlspecialchars($paso['seccion']) ?></span>
            <span class="paso-texto"><?= htmlspecialchars($paso['texto']) ?></span>
            <span class="paso-barra" title="<?= $pctFallo ?> %"><span style="width:<?= $pctFallo ?>%;"></span></span>
            <span class="paso-cuenta"><?= $paso['fallos'] ?> de <?= $paso['evaluadas'] ?></span>
        </div>
        <?php endforeach; ?>
    </div>
    <?php
}
