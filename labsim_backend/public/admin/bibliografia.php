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

/**
 * Recuadro "para su teoría": lo que el cuadro muestra siempre alterado y en
 * la realidad no siempre (ver Bibliografia::decisiones).
 */
function bib_decisiones(array $lista): void
{
    ?>
    <div style="margin-top:0.5rem; padding:0.4rem 0.6rem; border-left:3px solid var(--color-warn-text); background:var(--color-warn-bg); color:var(--color-warn-text); font-size:0.88em;">
        <strong>Para su teoría:</strong> el generador muestra este cuadro siempre así; en la realidad no siempre.
        <ul style="margin:0.2rem 0 0 1.2rem; padding:0;">
            <?php foreach ($lista as $d): ?>
            <li><strong><?= htmlspecialchars(Bibliografia::EJES[$d['eje']] ?? 'General') ?>:</strong>
                <?= htmlspecialchars($d['texto']) ?>
                <?php $anio = preg_match('/\b(19|20)\d{2}\b/', $d['cita'], $m) ? ' ' . $m[0] : ''; ?>
                <span style="opacity:0.75;">(<?= htmlspecialchars(rtrim((string) strtok($d['cita'], ' '), ',') . $anio) ?>)</span></li>
            <?php endforeach; ?>
        </ul>
    </div>
    <?php
}

$decisiones = Bibliografia::decisiones();

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
        <li><a href="#tecnicas">Técnicas de examen</a>
            (<?= count(Bibliografia::TECNICAS) ?>)</li>
        <li><a href="#decisiones">Para su teoría: lo que el generador muestra siempre alterado</a>
            (<?= count($decisiones) ?> cuadros)</li>
        <li><a href="#patologias">Patologías del generador</a>
            (<?= count(CaseProfile::SCENARIOS) ?> cuadros, <?= count(Bibliografia::PATOLOGIAS) ?> con bibliografía)</li>
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

<div class="card" id="tecnicas">
    <details open>
        <summary><strong>Técnicas de examen</strong></summary>
        <p class="help help--mt">Cómo se toma cada examen, paso a paso, tal como usted lo enseña. Es la referencia contra la que se compara lo que hace el alumno en el equipo.</p>
        <?php foreach (Bibliografia::TECNICAS as $tid => $t): ?>
        <div style="margin-top:0.8rem; font-size:0.9em;">
            <strong><?= htmlspecialchars($tid) ?> · <?= htmlspecialchars($t['titulo']) ?></strong>
            <?php if (!$t['fuentes']): ?><span class="badge-warn">· sin bibliografía todavía</span><?php endif; ?>
            <div style="opacity:0.8;"><?= htmlspecialchars($t['resumen']) ?></div>
            <ol style="margin:0.3rem 0 0 1.2rem; padding:0;">
                <?php foreach ($t['pasos'] as $paso): ?>
                <li><?= htmlspecialchars($paso) ?></li>
                <?php endforeach; ?>
            </ol>
            <?php if (!empty($t['nota'])): ?>
            <div style="opacity:0.8; margin-top:0.2rem;"><em><?= htmlspecialchars($t['nota']) ?></em></div>
            <?php endif; ?>
            <div style="margin-top:0.2rem;">Corresponde a:</div>
            <ul style="margin:0.1rem 0 0 1.2rem; padding:0;">
                <?php foreach ($t['usa'] as $uso): ?>
                <li><?= htmlspecialchars($uso) ?></li>
                <?php endforeach; ?>
            </ul>
            <?php foreach ($t['fuentes'] as $fid => $f): ?>
            <?php bib_ficha((string) $fid, $f); ?>
            <?php endforeach; ?>
        </div>
        <?php endforeach; ?>
    </details>
</div>

<?php
$catalogo = Bibliografia::cuadros();
$categoriaLabel = [
    'normal' => 'Normal', 'conductiva' => 'Conductivas', 'sensorial' => 'Sensoriales',
    'neural' => 'Neurales', 'sensorioneural' => 'Sensorioneurales', 'mixta' => 'Mixtas',
];
$porCategoria = [];
foreach ($catalogo['cuadros'] as $clave => $c) {
    $porCategoria[$c['categoria']][$clave] = $c;
}
?>
<div class="card" id="decisiones">
    <details open>
        <summary><strong>Para su teoría: lo que el generador muestra siempre alterado</strong></summary>
        <p class="help help--mt">El generador enseña cada cuadro en su forma típica y patológica: un Ménière con la electrococleografía alterada, una esclerosis múltiple con el VEMP alterado. En la realidad, una parte de esos pacientes tiene ese examen normal, o el cuadro tiene otras formas. Eso no se sortea: se lo da usted en la teoría, y acá está, cuadro por cuadro, con la cifra y la fuente. Un caso con la forma menos frecuente se arma a mano.</p>
        <?php foreach ($decisiones as $clave => $lista): ?>
        <div style="margin-top:0.7rem;">
            <a href="#cuadro-<?= htmlspecialchars($clave) ?>"><strong><?= htmlspecialchars(CaseProfile::SCENARIOS[$clave]['label']) ?></strong></a>
            <?php bib_decisiones($lista); ?>
        </div>
        <?php endforeach; ?>
    </details>
</div>

<div class="card" id="patologias">
    <details open>
        <summary><strong>Patologías del generador</strong></summary>
        <p class="help help--mt">Cada cuadro que ofrece el autocompletado del caso, con lo que fija en el oído y por qué. El porqué es el que quedó escrito en el código al tomar la decisión, así que es siempre lo que hace el generador hoy. Los valores son rangos: el generador sortea dentro de ellos y usted edita el resultado. Donde no hay bibliografía, el valor es una decisión de diseño.</p>
        <?php foreach ($porCategoria as $cat => $lista): ?>
        <details style="margin-top:0.8rem;">
            <summary><strong><?= htmlspecialchars($categoriaLabel[$cat] ?? $cat) ?></strong> (<?= count($lista) ?>)</summary>
            <?php if (!empty($catalogo['categorias'][$cat])): ?>
            <p class="help help--mt"><?= htmlspecialchars($catalogo['categorias'][$cat]) ?></p>
            <?php endif; ?>
            <?php foreach ($lista as $clave => $c): ?>
            <?php $citas = Bibliografia::PATOLOGIAS[$clave] ?? []; ?>
            <details style="margin:0.6rem 0 0 0.8rem;" id="cuadro-<?= htmlspecialchars($clave) ?>">
                <summary><?= htmlspecialchars($c['label']) ?>
                    <span style="opacity:0.7; font-size:0.85em;">· <?= $citas ? count($citas) . ' citas' : 'sin bibliografía' ?></span>
                    <?php if (!empty($decisiones[$clave])): ?><span class="tag--warn" style="font-size:0.8em; padding:0 0.3rem;">para su teoría</span><?php endif; ?></summary>
                <?php if (!empty($decisiones[$clave])) { bib_decisiones($decisiones[$clave]); } ?>
                <table style="width:100%; font-size:0.85em; margin-top:0.4rem; border-collapse:collapse;">
                    <?php foreach ($c['filas'] as $fila): ?>
                    <tr style="border-top:1px solid var(--color-border, #ddd); vertical-align:top;">
                        <td style="padding:0.3rem 0.5rem 0.3rem 0; width:38%;">
                            <?php if ($fila['ejes'] === []): ?>
                            <em>El cuadro</em>
                            <?php endif; ?>
                            <?php foreach ($fila['ejes'] as $eje): ?>
                            <div><strong><?= htmlspecialchars(Bibliografia::EJES[$eje]) ?>:</strong>
                                <?= htmlspecialchars(Bibliografia::valorEje(CaseProfile::SCENARIOS[$clave][$eje])) ?></div>
                            <?php endforeach; ?>
                        </td>
                        <td style="padding:0.3rem 0; opacity:<?= $fila['porque'] !== '' ? '1' : '0.5' ?>;">
                            <?= $fila['porque'] !== '' ? htmlspecialchars($fila['porque']) : 'Sin fundamento escrito: valores de diseño.' ?>
                        </td>
                    </tr>
                    <?php endforeach; ?>
                </table>
                <?php if ($citas): ?>
                <p class="help help--mt"><strong>Bibliografía del cuadro</strong></p>
                <?php foreach ($citas as $i => $cita): ?>
                <?php
                $coincide = $cita['coincide'] ?? 'si';
                $cita['usa'] = [Bibliografia::EJES[$cita['eje']] ?? 'General'] ;
                $cita['usa'][0] .= ': ' . $cita['respalda']
                    . ($coincide === 'no' ? ' (la literatura NO coincide con el generador)' : ($coincide === 'parcial' ? ' (coincide en parte)' : ''));
                bib_ficha((string) ($i + 1), $cita);
                ?>
                <?php endforeach; ?>
                <?php endif; ?>
            </details>
            <?php endforeach; ?>
        </details>
        <?php endforeach; ?>
    </details>
</div>

<?php
admin_footer();
