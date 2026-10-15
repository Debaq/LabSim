<?php
/**
 * Faltas graves de una atención (ver src/FaltasGraves.php): recuadro rojo
 * en la atención (admin/chat_detail.php, student/atencion.php) y etiqueta
 * en las listas de atenciones. Estilos en css/base.css (.falta-grave).
 */

require_once __DIR__ . '/../../src/FaltasGraves.php';

/**
 * @param list<array{texto:string, detalle:string, hora:string}> $faltas
 */
function faltas_graves_recuadro(array $faltas, bool $docente): void
{
    if (!$faltas) {
        return;
    }
    ?>
<div class="card falta-grave" id="faltas-graves">
    <h2>⚠ Falta grave</h2>
    <p><?= $docente
        ? 'En esta atención el alumno hizo algo que no se hace nunca. No descuenta del porcentaje de la técnica: va aparte.'
        : 'En esta atención hiciste algo que no se hace nunca. No descuenta del porcentaje de la técnica: va aparte, y es lo primero que hay que corregir.' ?></p>
    <ul>
        <?php foreach ($faltas as $f): ?>
        <li><strong><?= htmlspecialchars($f['texto']) ?></strong><?php if ($f['detalle'] !== ''): ?> — <?= htmlspecialchars($f['detalle']) ?><?php endif; ?><?php if ($f['hora'] !== ''): ?> <span class="muted">(<?= htmlspecialchars($f['hora']) ?>)</span><?php endif; ?></li>
        <?php endforeach; ?>
    </ul>
</div>
    <?php
}

/** Etiqueta para las listas de atenciones. */
function faltas_graves_etiqueta(array $faltas): string
{
    return $faltas ? '<span class="tag tag--danger" title="' . htmlspecialchars($faltas[0]['texto']) . '">⚠ Falta grave</span>' : '';
}
