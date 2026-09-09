<?php
/**
 * Ficha 5 -- Otoscopia: fases y sus fotos.
 *
 * Vive fuera de public/ a propósito: el docroot del hosting es la raíz de
 * labsim_backend/ y public/.htaccess re-habilita todo lo que cuelga de
 * public/, así que ahí adentro esta ficha sería alcanzable por URL y
 * correría sin la sesión de admin que valida case_create.php.
 *
 * Incluido por admin/case_create.php, que comparte su scope: este archivo
 * NO declara lo que usa. Espera del padre $otoscopiaCount, $otoscopiaTextoAt, $photoCaseId.
 */
?>
<div class="tab-panel" data-tab="otoscopia">
<div class="card">
    <strong>Otoscopia</strong>
    <p class="legend">Una sola fase (la de por defecto) = una imagen por oído, nada más. Agregar una 2ª fase en adelante es lo que la convierte en "por fase": cada fase desde la 2ª lleva un texto libre que describe qué pasó entremedio (ej. "se realizó un lavado ótico"). Qué fase le corresponde ver a cada alumno según su propio avance con este paciente no está implementado todavía (ver TODO.md); por ahora siempre se muestra la fase 1.</p>

    <input type="hidden" name="otoscopia[fase_count]" id="otoscopia-fase-count" value="<?= $otoscopiaCount ?>">
    <p id="otoscopia-msg" class="legend" hidden></p>

    <div id="otoscopia-fases">
        <?php for ($faseIdx = 0; $faseIdx < $otoscopiaCount; $faseIdx++): ?>
        <div class="otoscopia-fase" data-fase-idx="<?= $faseIdx ?>">
            <div class="side-heading">
                <span class="side-tag">Fase <?= $faseIdx + 1 ?></span>
                <?php if ($faseIdx > 0): ?>
                <button type="button" class="secondary otoscopia-remove-fase" data-fase-idx="<?= $faseIdx ?>" <?= $faseIdx === $otoscopiaCount - 1 ? '' : 'hidden' ?>>Quitar esta fase</button>
                <?php endif; ?>
            </div>
            <?php if ($faseIdx > 0): ?>
            <label>¿Qué pasó desde la fase anterior? (texto libre, se muestra al alumno)
                <textarea name="otoscopia[texto][<?= $faseIdx ?>]" rows="2"><?= htmlspecialchars($otoscopiaTextoAt($faseIdx)) ?></textarea>
            </label>
            <?php endif; ?>
            <div class="two-col">
                <?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
                <div class="otoscopia-photo-slot">
                    <span class="side-tag <?= $lado ?>"><?= $ladoLabel ?></span><br>
                    <?php $hasOto = OtoscopiaPhoto::has($photoCaseId, $lado, $faseIdx); ?>
                    <img class="otoscopia-thumb" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>"
                         src="otoscopia_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;side=<?= $lado ?>&amp;fase=<?= $faseIdx ?>&amp;v=<?= time() ?>"
                         alt="Otoscopia <?= $ladoLabel ?> fase <?= $faseIdx + 1 ?>" <?= $hasOto ? '' : 'hidden' ?>>
                    <div class="otoscopia-thumb-empty" <?= $hasOto ? 'hidden' : '' ?>>Sin imagen</div>
                    <input type="file" class="otoscopia-photo-input" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>" accept="image/jpeg,image/png,image/webp">
                    <button type="button" class="secondary otoscopia-delete-photo" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>" <?= $hasOto ? '' : 'hidden' ?>>Borrar foto</button>
                    <a class="otoscopia-download-photo" href="otoscopia_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;side=<?= $lado ?>&amp;fase=<?= $faseIdx ?>&amp;download=1" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>" <?= $hasOto ? '' : 'hidden' ?>>Descargar</a>
                </div>
                <?php endforeach; ?>
            </div>
        </div>
        <?php endfor; ?>
    </div>

    <button type="button" id="otoscopia-add-fase" class="secondary">+ Agregar fase</button>

    <!-- Fuente única del markup de un slot/fase vacíos: usado por JS al agregar fase (#otoscopia-add-fase).
         El render inicial (arriba, PHP) es aparte porque necesita mostrar la foto ya guardada si existe. -->
    <template id="otoscopia-slot-tpl">
        <div class="otoscopia-photo-slot">
            <span class="side-tag"></span><br>
            <img class="otoscopia-thumb" hidden>
            <div class="otoscopia-thumb-empty">Sin imagen</div>
            <input type="file" class="otoscopia-photo-input" accept="image/jpeg,image/png,image/webp">
            <button type="button" class="secondary otoscopia-delete-photo" hidden>Borrar foto</button>
            <a class="otoscopia-download-photo" hidden>Descargar</a>
        </div>
    </template>
    <template id="otoscopia-fase-tpl">
        <div class="otoscopia-fase">
            <div class="side-heading">
                <span class="side-tag">Fase</span>
                <button type="button" class="secondary otoscopia-remove-fase">Quitar esta fase</button>
            </div>
            <label>¿Qué pasó desde la fase anterior? (texto libre, se muestra al alumno)
                <textarea rows="2"></textarea>
            </label>
            <div class="two-col"></div>
        </div>
    </template>
</div>
</div>
