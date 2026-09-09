<?php
/**
 * Ficha 2 -- Sala: quién viene con el paciente (ver Sala.php).
 *
 * Vive fuera de public/ a propósito: el docroot del hosting es la raíz de
 * labsim_backend/ y public/.htaccess re-habilita todo lo que cuelga de
 * public/, así que ahí adentro esta ficha sería alcanzable por URL y
 * correría sin la sesión de admin que valida case_create.php.
 *
 * Incluido por admin/case_create.php, que comparte su scope: este archivo
 * NO declara lo que usa. Espera del padre $salaRows, $salaInformante, $pacienteConciencia, $pacienteConfiabilidad, $dispOpts, $photoCaseId.
 */
?>
<div class="tab-panel" data-tab="sala">
<div class="card">
    <strong>Sala de atención</strong>
    <p class="help">Quiénes vienen con el paciente. Un lactante no cuenta su historia: la cuenta la madre. Y hay adultos que niegan lo que el acompañante ve todos los días -- ese desacuerdo <em>es</em> el hallazgo clínico del caso, y el alumno tiene que darse cuenta de a quién le está preguntando.</p>
    <p class="help">El alumno no elige a quién le habla con un menú: lo dice escribiendo ("mamita, ¿su hijo escucha bien?", "prefiero que me conteste él") y responde quien corresponda. Un caso sin acompañantes es una conversación con el paciente y nadie más.</p>

    <div class="section-sep" style="border-top:1px dashed var(--color-border);">
        <strong>El paciente en la entrevista</strong>
        <p class="help">Su comportamiento y su sensibilidad se editan en la pestaña Anamnesis. Acá va solo lo que cambia cuando viene acompañado.</p>
        <div class="two-col">
            <label>Conciencia de su problema (0-100)
                <input type="number" name="paciente_conciencia" min="0" max="100" value="<?= htmlspecialchars($pacienteConciencia) ?>">
            </label>
            <label>Confiabilidad de su relato (0-100)
                <input type="number" name="paciente_confiabilidad" min="0" max="100" value="<?= htmlspecialchars($pacienteConfiabilidad) ?>">
            </label>
        </div>
        <p class="help">Bajo <?= Sala::CONCIENCIA_BAJA ?> de conciencia el paciente niega o minimiza lo suyo ("yo escucho bien, hablan bajo") y el acompañante que sí lo nota se mete a corregirlo. Bajo <?= Sala::CONFIABILIDAD_BAJA ?> de confiabilidad confunde fechas y detalles, pero los cuenta con seguridad.</p>
        <label class="inline-check">
            <input type="radio" name="sala_informante" value="p1" <?= $salaInformante === 'p1' ? 'checked' : '' ?>> El paciente es quien cuenta la historia
        </label>
        <p class="help">Quien lleva la voz cantante: el que contesta cuando el alumno pregunta al aire, sin dirigirse a nadie. En un lactante no puede ser el paciente.</p>
    </div>
</div>

<div class="card">
    <strong>Acompañantes</strong>
    <p class="help">Cada uno responde por sí mismo, con su propia foto y su propia versión. Sabe lo que el paciente no puede saber: fechas, remedios, cómo fue el parto.</p>
    <p class="help">La tendencia a interrumpir es lo que decide si esta persona contesta por el paciente o espera su turno.</p>
    <?php
    // Una sola definición de fila para los dos usos: las que ya tiene el
    // caso y la plantilla que clona el navegador al agregar a alguien. El
    // id de persona es lo que amarra la foto (ver PatientPhoto::key), así
    // que en la plantilla va como marcador y el JS lo reemplaza por uno
    // nuevo -- si dependiera de la posición, borrar una fila de más arriba
    // le correría la cara a todos los demás.
    $salaRowHtml = static function (array $ac, string $pid) use ($photoCaseId, $salaInformante, $dispOpts): string {
        $hasFoto = $pid !== '__ID__' && PatientPhoto::hasAvatar(PatientPhoto::key($photoCaseId, $pid));
        ob_start();
        ?>
        <div class="sala-row" data-persona="<?= htmlspecialchars($pid) ?>" style="border:1px solid var(--color-border); border-radius:var(--radius-md); padding:0.8rem; margin-bottom:0.8rem;">
            <input type="hidden" name="sala_id[]" value="<?= htmlspecialchars($pid) ?>">
            <div class="three-col">
                <label>Qué es del paciente
                    <select name="sala_rol[]">
                        <?php foreach (Sala::ROLES as $rolKey => $rolLabel): ?>
                            <?php if ($rolKey === 'paciente') { continue; } ?>
                            <option value="<?= $rolKey ?>" <?= ((string) ($ac['rol'] ?? 'madre')) === $rolKey ? 'selected' : '' ?>><?= htmlspecialchars($rolLabel) ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
                <label>Nombre
                    <input type="text" name="sala_nombre[]" value="<?= htmlspecialchars((string) ($ac['nombre'] ?? '')) ?>">
                </label>
                <label>Edad
                    <input type="number" name="sala_edad[]" min="0" max="110" value="<?= htmlspecialchars((string) ($ac['edad'] ?? '')) ?>">
                </label>
            </div>
            <div class="three-col">
                <label>Género
                    <select name="sala_genero[]">
                        <option value="0" <?= (int) ($ac['genero'] ?? 0) === 0 ? 'selected' : '' ?>>Hombre</option>
                        <option value="1" <?= (int) ($ac['genero'] ?? 0) === 1 ? 'selected' : '' ?>>Mujer</option>
                    </select>
                </label>
                <label>Tendencia a contestar por el paciente (0-100)
                    <input type="number" name="sala_interrumpe[]" min="0" max="100" value="<?= htmlspecialchars((string) ($ac['interrumpe'] ?? Sala::RASGOS_DEFAULT['interrumpe'])) ?>">
                </label>
                <label>Confiabilidad de su relato (0-100)
                    <input type="number" name="sala_confiabilidad[]" min="0" max="100" value="<?= htmlspecialchars((string) ($ac['confiabilidad'] ?? Sala::RASGOS_DEFAULT['confiabilidad'])) ?>">
                </label>
            </div>
            <label>Su versión de los hechos
                <textarea name="sala_version[]" rows="2" class="input" placeholder="Ej: no escucha nada hace años, sube la tele al máximo y contesta cualquier cosa."><?= htmlspecialchars((string) ($ac['version'] ?? '')) ?></textarea>
            </label>
            <p class="help">Lo que ESTA persona sostiene, aunque el paciente diga otra cosa. Con esto escrito, se mete a contradecir cuando el tema sale en la conversación.</p>
            <div class="two-col">
                <label>Comportamiento
                    <input type="text" name="sala_comportamiento[]" value="<?= htmlspecialchars((string) ($ac['comportamiento'] ?? '')) ?>" placeholder="Ej: ansiosa, contesta por él, apurada...">
                </label>
                <label>Sensibilidad
                    <select name="sala_disposicion[]">
                        <?php foreach ($dispOpts as $dVal => $dLabel): ?>
                            <option value="<?= $dVal ?>" <?= (int) ($ac['disposicion'] ?? 0) === $dVal ? 'selected' : '' ?>><?= htmlspecialchars($dLabel) ?></option>
                        <?php endforeach; ?>
                    </select>
                </label>
            </div>
            <div style="display:flex; align-items:center; gap:1rem; margin-top:0.6rem;">
                <img class="patient-avatar sala-avatar" src="patient_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;persona=<?= urlencode($pid) ?>&amp;type=avatar&amp;v=<?= time() ?>" alt="" <?= $hasFoto ? '' : 'hidden' ?>>
                <div class="patient-avatar patient-avatar-empty sala-avatar-empty" <?= $hasFoto ? 'hidden' : '' ?>>Sin foto</div>
                <div>
                    <input type="file" class="sala-photo-input" data-persona="<?= htmlspecialchars($pid) ?>" accept="image/jpeg,image/png,image/webp">
                    <label class="inline-check">
                        <input type="radio" name="sala_informante" value="<?= htmlspecialchars($pid) ?>" <?= $salaInformante === $pid ? 'checked' : '' ?>> Es quien cuenta la historia
                    </label>
                </div>
                <button type="button" class="secondary sala-remove" style="margin-left:auto;">Quitar</button>
            </div>
        </div>
        <?php
        return (string) ob_get_clean();
    };
    ?>
    <div id="sala-rows">
        <?php foreach ($salaRows as $idx => $ac): ?>
            <?= $salaRowHtml($ac, (string) ($ac['id'] ?? ('p' . ($idx + 2)))) ?>
        <?php endforeach; ?>
    </div>
    <template id="sala-row-tpl"><?= $salaRowHtml([], '__ID__') ?></template>
    <button type="button" id="sala-add" class="secondary">Agregar acompañante</button>
    <p class="help">La foto se puede subir apenas se agrega la fila, antes de guardar el caso.</p>
</div>
</div>
