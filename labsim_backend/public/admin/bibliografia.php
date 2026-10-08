<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/Bibliografia.php';

/**
 * Toda la bibliografía de la app, por examen, con a qué corresponde cada
 * cita. Solo lectura: las fichas viven en src/Bibliografia.php y en las
 * clases que la usan (AbrReferences, EcochgReferences). Es para el
 * docente; el alumno no ve citas en ningún lado.
 */

$me = Auth::requireFullAdminSession();

/** Una ficha: cita, n/protocolo si los hay, enlace y "corresponde a". */
function bib_ficha(string $fid, array $f): void
{
    $verificada = $f['verificada'] ?? true;
    $detalle = array_filter([
        $f['n'] ?? '',
        $f['protocolo'] ?? '',
    ], static function ($x) { return $x !== ''; });
    $enlace = (string) ($f['enlace'] ?? '');
    ?>
    <div style="margin-top:0.8rem; font-size:0.9em;">
        <strong><?= htmlspecialchars($fid) ?></strong> ·
        <?= htmlspecialchars($f['cita']) ?>
        <?php if (!$verificada): ?><span class="badge-warn">· sin verificar</span><?php endif; ?>
        <?php if ($detalle): ?>
        <div style="opacity:0.8;"><?= htmlspecialchars(implode(' · ', $detalle)) ?></div>
        <?php endif; ?>
        <?php if (strpos($enlace, 'http') === 0): ?>
        <div><a href="<?= htmlspecialchars($enlace) ?>" target="_blank" rel="noopener"><?= htmlspecialchars($enlace) ?></a></div>
        <?php elseif ($enlace !== ''): ?>
        <div style="opacity:0.8;"><?= htmlspecialchars($enlace) ?></div>
        <?php endif; ?>
        <?php if (!empty($f['nota'])): ?>
        <div style="opacity:0.8;"><em><?= htmlspecialchars($f['nota']) ?></em></div>
        <?php endif; ?>
        <?php if (!empty($f['usa'])): ?>
        <div style="margin-top:0.2rem;">Corresponde a:</div>
        <ul style="margin:0.1rem 0 0 1.2rem; padding:0;">
            <?php foreach ($f['usa'] as $uso): ?>
            <li><?= htmlspecialchars($uso) ?></li>
            <?php endforeach; ?>
        </ul>
        <?php endif; ?>
    </div>
    <?php
}

admin_header('Bibliografía', $me);
?>

<div class="card">
    <strong>Bibliografía</strong>
    <p class="help help--mt">De dónde sale cada número de la app, ordenado por examen. Cada cita dice a qué corresponde: qué valor, qué límite o qué comportamiento respalda. Es para usted: el alumno no ve citas ni en la app ni en su ficha. Lo que ninguna fuente publica lo calcula el generador, y donde importa se dice.</p>
    <ul style="margin:0.4rem 0 0 1.2rem; padding:0;">
        <?php foreach (Bibliografia::SECCIONES as $sid => $sec): ?>
        <li><a href="#<?= htmlspecialchars($sid) ?>"><?= htmlspecialchars($sec['titulo']) ?></a>
            (<?= count(Bibliografia::fuentes($sid)) ?> fuentes)</li>
        <?php endforeach; ?>
    </ul>
</div>

<?php foreach (Bibliografia::SECCIONES as $sid => $sec): ?>
<div class="card" id="<?= htmlspecialchars($sid) ?>">
    <details open>
        <summary><strong><?= htmlspecialchars($sec['titulo']) ?></strong></summary>
        <p class="help help--mt"><?= htmlspecialchars($sec['resumen']) ?></p>

        <?php if ($sid === 'abr'): ?>
        <p class="help"><a href="normativa_planilla.php">Descargar la planilla completa</a> (483 filas, 27 fuentes: latencias, interpicos, amplitudes y factores modificadores). Los sets de autor y los valores de fábrica se ven en <a href="normativas.php">Normativas</a>.</p>
        <?php endif; ?>

        <?php if ($sid === 'ecochg'): ?>
        <p class="help help--mt"><strong>De dónde sale cada límite</strong></p>
        <?php foreach (EcochgReferences::LIMITES as $lim): ?>
        <div style="margin-top:0.5rem; font-size:0.9em;">
            <strong><?= htmlspecialchars($lim['label']) ?>:</strong> <?= htmlspecialchars($lim['valor']) ?>
            · <?= $lim['fuentes'] ? htmlspecialchars(implode(', ', $lim['fuentes'])) : 'calculado' ?>
            <div style="opacity:0.8;"><?= htmlspecialchars($lim['nota']) ?></div>
        </div>
        <?php endforeach; ?>
        <p class="help help--mt"><strong>Fuentes</strong></p>
        <?php endif; ?>

        <?php foreach (Bibliografia::fuentes($sid) as $fid => $f): ?>
        <?php bib_ficha((string) $fid, $f); ?>
        <?php endforeach; ?>

        <?php if ($sid === 'abr'): ?>
        <details style="margin-top:1rem;">
            <summary>En la planilla, pero sin ningún número de la app detrás (<?= count(Bibliografia::sinUsoAbr()) ?>)</summary>
            <p class="help help--mt">Se revisaron y quedaron como consulta: otra serie cubría lo mismo con mejor n o protocolo, o no publican lo que el modelo necesita.</p>
            <?php foreach (Bibliografia::sinUsoAbr() as $fid => $f): ?>
            <?php bib_ficha((string) $fid, $f); ?>
            <?php endforeach; ?>
        </details>
        <?php endif; ?>
    </details>
</div>
<?php endforeach; ?>

<?php
admin_footer();
