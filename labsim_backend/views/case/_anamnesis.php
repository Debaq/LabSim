<?php
/**
 * Ficha 11 -- Anamnesis: antecedentes, borrador por IA y chat de prueba.
 *
 * Vive fuera de public/ a propósito: el docroot del hosting es la raíz de
 * labsim_backend/ y public/.htaccess re-habilita todo lo que cuelga de
 * public/, así que ahí adentro esta ficha sería alcanzable por URL y
 * correría sin la sesión de admin que valida case_create.php.
 *
 * Incluido por admin/case_create.php, que comparte su scope: este archivo
 * NO declara lo que usa. Espera del padre $v, $dispOpts.
 */
?>
<div class="tab-panel" data-tab="anamnesis">
<div class="card">
    <strong>El borrador de IA hay que leerlo</strong>
    <p class="help">Lo escribe el modelo desde <a href="#" class="tab-link" data-goto-tab="armado">Armado rápido</a> y queda en los campos de abajo. Puede inventar una cirugía que no existe o un fármaco que no es ototóxico, y eso le llega al alumno como parte del caso, indistinguible de lo que escribiste vos.</p>
    <div id="anamnesis-ia-verificacion" <?= fv($v, ['anamnesis_ia', 'generado'], '') ? '' : 'hidden' ?> style="border-left:4px solid var(--color-danger); padding-left:0.6rem; margin-top:0.6rem;">
        <label class="inline-check">
            <input type="checkbox" name="anamnesis_ia[verificado]" id="anamnesis-ia-verificado" value="1" <?= fv($v, ['anamnesis_ia', 'verificado'], '') ? 'checked' : '' ?>>
            Leí el borrador y verifico que es clínicamente correcto para este caso
        </label>
        <?php if (fv($v, ['anamnesis_ia', 'verificado_por'], '')): ?>
        <p class="help">Verificado por <?= htmlspecialchars((string) fv($v, ['anamnesis_ia', 'verificado_por'], '')) ?><?= fv($v, ['anamnesis_ia', 'verificado_en'], '') ? ' el ' . htmlspecialchars((string) fv($v, ['anamnesis_ia', 'verificado_en'], '')) : '' ?>.</p>
        <?php endif; ?>
        <p class="help">Volver a generar borra la verificación: el texto nuevo no lo leyó nadie. Hasta que esté tildada, el caso no se guarda.</p>
    </div>
    <p class="help" id="anamnesis-ia-estado-eco" hidden></p>
    <p class="help" id="anamnesis-ia-sin-borrador" <?= fv($v, ['anamnesis_ia', 'generado'], '') ? 'hidden' : '' ?>>Este caso no tiene borrador de IA pendiente: lo de abajo se escribió a mano.</p>
</div>
<div class="card">
    <strong>Anamnesis</strong>
    <?php
    $histLabels = [
        'hipoacusia_familiar' => 'Hipoacusia familiar', 'ototoxicos' => 'Ototóxicos',
        'trauma_acustico' => 'Trauma acústico', 'otitis' => 'Otitis', 'meningitis' => 'Meningitis',
        'tce' => 'TCE', 'diabetes' => 'Diabetes', 'hta' => 'HTA',
    ];
    foreach ($histLabels as $key => $label): ?>
    <label class="inline-check"><input type="checkbox" name="hist[<?= $key ?>]" <?= isset($v['hist'][$key]) ? 'checked' : '' ?>> <?= htmlspecialchars($label) ?></label>
    <?php endforeach; ?>
    <label>Medicamentos
        <input type="text" name="medicamentos" value="<?= htmlspecialchars((string) ($v['medicamentos'] ?? '')) ?>">
    </label>
    <label>Cirugías
        <input type="text" name="cirugias" value="<?= htmlspecialchars((string) ($v['cirugias'] ?? '')) ?>">
    </label>
    <label>Lo que el paciente cuenta de sí mismo
        <textarea name="otros" rows="5" class="input" placeholder="En qué trabaja, cómo es su día, qué hace en su tiempo libre, desde cuándo lo nota, en qué situaciones le molesta más, qué le preocupa, qué ya probó..."><?= htmlspecialchars((string) ($v['otros'] ?? '')) ?></textarea>
    </label>
    <p class="help">Su vida, su trabajo, su rutina, desde cuándo lo nota, en qué situaciones le molesta, qué le preocupa, qué ya probó. De acá sale <strong>todo lo que el paciente tiene para responder</strong> cuando el alumno lo entrevista: vacío contesta en monosílabos y no hay nada que preguntarle. No es la historia clínica (esa la lee el alumno en la ficha) ni la lista de antecedentes de arriba: es lo que esta persona cuenta si se lo preguntan.</p>
    <label>Comportamiento del paciente
        <textarea name="comportamiento" id="chat-comportamiento" rows="2" class="input" placeholder="Ej: nervioso, minimiza los síntomas, muy hablador, desconfiado, colaborador..."><?= htmlspecialchars((string) ($v['comportamiento'] ?? '')) ?></textarea>
    </label>
    <p class="help">Cómo debe actuar el paciente al conversar con el alumno (tono, actitud) -- va directo al prompt del LLM, junto con la anamnesis de arriba.</p>
    <label>Sensibilidad del paciente
        <select name="disposicion" id="chat-disposicion">
            <?php foreach ($dispOpts as $val => $label): ?>
            <option value="<?= $val ?>" <?= ((string) ($v['disposicion'] ?? '0') === (string) $val) ? 'selected' : '' ?>><?= htmlspecialchars($label) ?></option>
            <?php endforeach; ?>
        </select>
    </label>
    <p class="help">Qué tan fácil se ofende o se pone contento este paciente -- define el umbral del aviso OIRS (sugerencia de mejora/felicitación) que puede dejar al cerrar la atención.</p>
</div>

<div class="card" id="chat-test-card">
    <strong>Probar conversación con el paciente</strong>
    <p class="help">
        Chatea con el paciente usando lo que ya escribiste en esta ficha (sin necesidad de guardar antes,
        cada mensaje toma los campos tal como están en ese momento) -- útil para revisar que responda bien
        antes de asignarlo a un alumno. Requiere tener configurado el LLM en
        <a href="llm.php" target="_blank">Admin → IA Paciente</a>. Si cambias la anamnesis a mitad de una
        conversación, reinícala para que el paciente "olvide" lo que dijo con los datos anteriores.
    </p>
    <div id="chat-test-log" style="border:1px solid var(--color-border); border-radius:var(--radius-lg); padding:0.7rem; min-height:3rem; max-height:22rem; overflow-y:auto; margin:0.6rem 0; background:var(--color-row-alt); font-size:0.88rem;"></div>
    <div style="display:flex; gap:0.5rem;">
        <input type="text" id="chat-test-input" placeholder="Escribe como si fueras el alumno..." style="flex:1; padding:0.45rem; border:1px solid var(--color-border-strong); border-radius:var(--radius-md);">
        <button type="button" id="chat-test-send" class="secondary" style="margin-top:0;">Enviar</button>
        <button type="button" id="chat-test-reset" class="secondary" style="margin-top:0;">Reiniciar conversación</button>
    </div>
    <div class="section-sep" style="border-top:1px dashed var(--color-border);">
        <button type="button" id="oirs-test-btn" class="secondary" style="margin-top:0;">Simular término de sesión (ver veredicto OIRS)</button>
        <p class="help">Corre el evaluador de <a href="llm.php" target="_blank">Admin → IA Paciente</a> sobre esta conversación de prueba, tal como se ejecutaría al cerrar una atención real -- útil para ajustar el prompt del evaluador o la sensibilidad del paciente.</p>
        <div id="oirs-test-result"></div>
    </div>
</div>
</div>
