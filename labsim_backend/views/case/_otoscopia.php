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
 * NO declara lo que usa. Espera del padre $otoscopiaCount, $otoscopiaTextoAt, $photoCaseId,
 * $otoscopiaHallazgosDe (lo que muestra la foto de la fase 1, por oído).
 */
?>
<div class="tab-panel" data-tab="otoscopia">
<div class="card">
    <strong>Otoscopia</strong>
    <p class="help">"Elegir de la base" trae una foto de la base de otoscopias ya orientada para ese oído (la da vuelta sola si hace falta); si después se corrige en la base, se actualiza acá. Subir otra, borrarla o espejarla a mano la deja como foto propia del caso. La misma foto de la base no puede ir en los dos oídos.</p>
    <p class="help"><strong>Lo que muestra la foto</strong> (fase 1, la que ven los alumnos): contra esto se compara el informe de otoscopía del alumno. "Normal" marca conducto normal y membrana sin hallazgos de una vez. Sin esto cargado, el informe del alumno no se puede evaluar.</p>
    <p class="help">Una sola fase (la de por defecto) = una imagen por oído, nada más. Agregar una 2ª fase en adelante es lo que la convierte en "por fase": cada fase desde la 2ª lleva un texto libre que describe qué pasó entremedio (ej. "se realizó un lavado ótico"). Por ahora todos los alumnos ven la fase 1: la fase no avanza sola con el progreso de cada uno, así que las siguientes sirven para preparar el caso, no para mostrárselas todavía.</p>

    <input type="hidden" name="otoscopia[fase_count]" id="otoscopia-fase-count" value="<?= $otoscopiaCount ?>">
    <p id="otoscopia-msg" class="help" hidden></p>

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
                    <?php $usoBase = $hasOto ? OtoscopiaBiblioteca::usoDe($photoCaseId, $lado, $faseIdx) : null; ?>
                    <img class="otoscopia-thumb" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>"
                         src="otoscopia_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;side=<?= $lado ?>&amp;fase=<?= $faseIdx ?>&amp;v=<?= time() ?>"
                         alt="Otoscopia <?= $ladoLabel ?> fase <?= $faseIdx + 1 ?>" <?= $hasOto ? '' : 'hidden' ?>>
                    <div class="otoscopia-thumb-empty" <?= $hasOto ? 'hidden' : '' ?>>Sin imagen</div>
                    <span class="otoscopia-origen" <?= $usoBase ? '' : 'hidden' ?>><?= $usoBase ? htmlspecialchars('De la base: ' . (OtoscopiaBiblioteca::TIPOS[$usoBase['tipo']] ?? $usoBase['tipo']) . ' (#' . (int) $usoBase['id'] . ')') : '' ?></span>
                    <input type="file" class="otoscopia-photo-input" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>" accept="image/jpeg,image/png,image/webp">
                    <button type="button" class="secondary otoscopia-elegir-base" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>">Elegir de la base</button>
                    <button type="button" class="secondary otoscopia-mirror-photo" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>" title="Da vuelta la imagen de izquierda a derecha" <?= $hasOto ? '' : 'hidden' ?>>Espejar</button>
                    <button type="button" class="secondary otoscopia-delete-photo" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>" <?= $hasOto ? '' : 'hidden' ?>>Borrar foto</button>
                    <a class="otoscopia-download-photo" href="otoscopia_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;side=<?= $lado ?>&amp;fase=<?= $faseIdx ?>&amp;download=1" data-side="<?= $lado ?>" data-fase-idx="<?= $faseIdx ?>" <?= $hasOto ? '' : 'hidden' ?>>Descargar</a>
                    <?php if ($faseIdx === 0): ?>
                    <?php $oh = $otoscopiaHallazgosDe($lado, $photoCaseId); $base = "otoscopia[hallazgos][{$lado}]"; ?>
                    <fieldset class="oto-verdad" data-side="<?= $lado ?>">
                        <legend>Lo que muestra la foto</legend>
                        <?php if ($oh['sugerido'] !== null): ?>
                        <p class="help help--xs">Sugerido por la foto de la base (<?= htmlspecialchars(OtoscopiaBiblioteca::TIPOS[$oh['sugerido']] ?? $oh['sugerido']) ?>): revísalo y guarda.</p>
                        <?php endif; ?>
                        <label class="oto-verdad-normal"><input type="checkbox" name="<?= $base ?>[normal]" value="1" <?= $oh['normal'] ? 'checked' : '' ?>> <strong>Normal</strong> <span class="help help--xs">(conducto normal, membrana sin hallazgos)</span></label>
                        <div class="oto-verdad-cae"><span class="help help--xs">Conducto:</span>
                            <?php foreach (CaseBuilder::OTOSCOPIA_CAE as $k => $label): ?>
                            <label><input type="checkbox" name="<?= $base ?>[cae][]" value="<?= $k ?>" <?= in_array($k, $oh['cae'], true) ? 'checked' : '' ?>> <?= htmlspecialchars($label) ?></label>
                            <?php endforeach; ?>
                        </div>
                        <table class="oto-verdad-tabla">
                            <tr><th>Membrana</th><?php foreach (CaseBuilder::OTOSCOPIA_CUADRANTES as $q => $ql): ?><th title="<?= htmlspecialchars($q) ?>"><?= htmlspecialchars($ql) ?></th><?php endforeach; ?></tr>
                            <?php foreach (CaseBuilder::OTOSCOPIA_HALLAZGOS as $hk => $hl): ?>
                            <tr><td><?= htmlspecialchars($hl) ?></td>
                                <?php foreach (CaseBuilder::OTOSCOPIA_CUADRANTES as $q => $ql): ?>
                                <td><input type="checkbox" class="oto-verdad-h" name="<?= $base ?>[cuadrantes][<?= $q ?>][]" value="<?= $hk ?>" aria-label="<?= htmlspecialchars($hl . ' ' . $ql) ?>" <?= in_array($hk, $oh['cuadrantes'][$q] ?? [], true) ? 'checked' : '' ?>></td>
                                <?php endforeach; ?>
                            </tr>
                            <?php endforeach; ?>
                        </table>
                        <label>Descripción (opcional, como la escribiría en un informe)
                            <textarea name="<?= $base ?>[texto]" rows="2"><?= htmlspecialchars($oh['texto']) ?></textarea>
                        </label>
                    </fieldset>
                    <?php endif; ?>
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
            <span class="otoscopia-origen" hidden></span>
            <input type="file" class="otoscopia-photo-input" accept="image/jpeg,image/png,image/webp">
            <button type="button" class="secondary otoscopia-elegir-base">Elegir de la base</button>
            <button type="button" class="secondary otoscopia-mirror-photo" title="Da vuelta la imagen de izquierda a derecha" hidden>Espejar</button>
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

    <div id="otoscopia-base-modal" class="photo-modal" hidden>
        <div class="photo-modal-box oto-elegir-box">
            <strong>Elegir de la base de otoscopias <span id="otoscopia-base-lado"></span></strong>
            <label>Tipo
                <select id="otoscopia-base-tipo"><option value="">Todos</option></select>
            </label>
            <p class="help" id="otoscopia-base-msg">Cargando...</p>
            <div class="oto-grilla" id="otoscopia-base-grilla"></div>
            <div class="photo-modal-actions">
                <button type="button" class="secondary" id="otoscopia-base-cancelar">Cancelar</button>
            </div>
        </div>
    </div>
</div>
</div>
