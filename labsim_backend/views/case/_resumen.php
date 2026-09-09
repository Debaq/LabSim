<?php
/**
 * Ficha 12 -- Resumen: la pasada final, ficha por ficha, antes de guardar.
 *
 * Vive fuera de public/ a propósito: el docroot del hosting es la raíz de
 * labsim_backend/ y public/.htaccess re-habilita todo lo que cuelga de
 * public/, así que ahí adentro esta ficha sería alcanzable por URL y
 * correría sin la sesión de admin que valida case_create.php.
 *
 * Incluido por admin/case_create.php, que comparte su scope: este archivo
 * NO declara lo que usa. Espera del padre $v y $pendientesPorTab.
 *
 * El estado de cada ficha ("PTA aérea OD 48 · OI 12 dB") lo escribe
 * public/js/case/resumen.js leyendo el formulario en vivo, no PHP: lo que
 * hay que revisar es lo que está cargado en la pantalla en este momento,
 * que después de generar un caso ya no es lo que tiene la base.
 */
?>
<div class="tab-panel" data-tab="resumen">
<div class="card">
    <strong>Resumen</strong>
    <p class="help">Una fila por ficha, con lo que quedó cargado. <strong>Tildar es aceptar</strong>: "miré esto y el caso sale así". Hasta que estén las <?= count(CaseReview::revisables()) ?> tildadas el caso no se guarda.</p>
    <p class="help">Lo que aparece <span class="resumen-alerta-inline">en rojo</span> es lo que el editor no puede calcular y encontró sin decidir (ver el detalle en cada fila). Tildar igual es una respuesta válida y la ficha deja de reclamarlo: el que sabe si un timpanograma en A con ese gap es un descuido o el ejercicio sos vos. La única que no se acepta de acá es la anamnesis que escribió el modelo de lenguaje -- esa se lee en su ficha y se tilda ahí.</p>
    <p class="help">Editar una ficha ya tildada la <strong>destilda sola</strong>, y "Generar caso" las destilda todas: lo revisado es la versión que se revisó, no la ficha en abstracto.</p>
    <div class="resumen-contador" id="resumen-contador"></div>
</div>

<div class="card">
<?php foreach (CaseReview::revisables() as $tabResumen => $labelResumen):
    $pendientesFicha = $pendientesPorTab[$tabResumen] ?? [];
?>
    <div class="resumen-row<?= $pendientesFicha ? ' con-pendiente' : '' ?>" data-tab="<?= $tabResumen ?>">
        <label class="inline-check" style="margin-left:0;">
            <input type="checkbox" class="resumen-check" value="1"
                   name="revisado[<?= $tabResumen ?>]"
                   data-tab="<?= $tabResumen ?>"
                   <?= !empty($v['revisado'][$tabResumen]) ? 'checked' : '' ?>>
            <span class="resumen-label"><?= htmlspecialchars($labelResumen) ?></span>
        </label>
        <div class="resumen-detalle">
            <div class="resumen-estado" data-resumen="<?= $tabResumen ?>"></div>
            <?php if ($pendientesFicha): ?>
            <ul class="resumen-pendientes">
                <?php foreach ($pendientesFicha as $pendiente): ?>
                <li><?= htmlspecialchars($pendiente['texto']) ?></li>
                <?php endforeach; ?>
            </ul>
            <?php endif; ?>
        </div>
        <a href="#" class="tab-link resumen-ir" data-goto-tab="<?= $tabResumen ?>">Ir a la ficha &rarr;</a>
    </div>
<?php endforeach; ?>
</div>
</div>
