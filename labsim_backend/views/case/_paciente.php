<?php
/**
 * Ficha 1 -- Paciente: identidad, edad, sexo y foto.
 *
 * Vive fuera de public/ a propósito: el docroot del hosting es la raíz de
 * labsim_backend/ y public/.htaccess re-habilita todo lo que cuelga de
 * public/, así que ahí adentro esta ficha sería alcanzable por URL y
 * correría sin la sesión de admin que valida case_create.php.
 *
 * Incluido por admin/case_create.php, que comparte su scope: este archivo
 * NO declara lo que usa. Espera del padre $v, $isEdit, $photoCaseId, $editDisplayName.
 */
?>
<div class="tab-panel<?= $isEdit ? ' active' : '' ?>" data-tab="paciente">
<div class="card">
    <strong>Paciente</strong>
    <?php if ($isEdit): ?><input type="hidden" id="chat-static-name" value="<?= htmlspecialchars($editDisplayName) ?>"><?php endif; ?>
    <label class="inline-check"><input type="radio" name="gender" value="0" <?= ($v['gender'] ?? '0') === '0' ? 'checked' : '' ?>> Hombre</label>
    <label class="inline-check"><input type="radio" name="gender" value="1" <?= ($v['gender'] ?? '0') === '1' ? 'checked' : '' ?>> Mujer</label>
    <div class="three-col">
        <label>Edad
            <input type="number" name="age" id="patient-age" min="0" max="110" value="<?= htmlspecialchars((string) ($v['age'] ?? '')) ?>">
        </label>
        <label>Fecha de nacimiento
            <input type="text" name="fecha_nac" id="patient-fecha-nac" value="<?= htmlspecialchars((string) ($v['fecha_nac'] ?? '')) ?>" readonly title="Se calcula sola a partir de la edad (día y mes al azar)." placeholder="AAAA-MM-DD">
        </label>
        <label>RUT
            <input type="text" name="rut" id="patient-rut" value="<?= htmlspecialchars((string) ($v['rut'] ?? '')) ?>">
        </label>
    </div>
    <?php if (!$isEdit): ?>
    <div class="two-col">
        <label>Nombre
            <input type="text" name="nombre1" value="<?= htmlspecialchars((string) ($v['nombre1'] ?? '')) ?>">
        </label>
        <label>Segundo nombre
            <input type="text" name="nombre2" value="<?= htmlspecialchars((string) ($v['nombre2'] ?? '')) ?>">
        </label>
        <label>Apellido
            <input type="text" name="apellido1" value="<?= htmlspecialchars((string) ($v['apellido1'] ?? '')) ?>">
        </label>
        <label>Segundo apellido
            <input type="text" name="apellido2" value="<?= htmlspecialchars((string) ($v['apellido2'] ?? '')) ?>">
        </label>
    </div>
    <p class="help">El nombre al azar se genera desde <a href="#" class="tab-link" data-goto-tab="armado">Armado rápido</a>, junto con el resto de los autocompletados.</p>
    <?php else: ?>
    <div class="two-col">
        <label>Nombre
            <input type="text" name="nombre" value="<?= htmlspecialchars((string) ($v['nombre'] ?? '')) ?>">
        </label>
        <label>Apellido
            <input type="text" name="apellido" value="<?= htmlspecialchars((string) ($v['apellido'] ?? '')) ?>">
        </label>
    </div>
    <p class="help" class="help">Esto edita al <strong>paciente</strong>: el cambio se aplica también a cualquier otra cita/ronda de la misma persona.</p>
    <?php endif; ?>

    <label>Historia clínica
        <textarea name="historia_clinica" rows="6" class="input" placeholder="{{-20}} Nace de 38 semanas, parto vaginal, 3.240 g. Screening auditivo: refiere OD.&#10;{{-5}} Control con pediatra, se deriva a evaluación auditiva."><?= htmlspecialchars((string) ($v['historia_clinica'] ?? '')) ?></textarea>
    </label>
    <p class="help" class="help">Las <strong>atenciones previas</strong> del paciente: qué le hicieron antes de llegar acá y qué se encontró, una por línea y de la más antigua a la más reciente. Es del <strong>paciente</strong>, no del caso. No incluye las notas individuales de cada alumno por atención -- esas se ven en la agenda/asistencia, no se editan acá.</p>
    <p class="help" class="help">Las fechas no se escriben a mano: poné <code>{{-N}}</code> al principio de la línea, donde N son los <strong>días antes</strong> de la cita que va a atender el alumno, y la app lo reemplaza por la fecha real. Así el mismo caso sirve en cualquier fecha. Ejemplos: <code>{{-5}}</code> hace cinco días, <code>{{-30}}</code> hace un mes, <code>{{-730}}</code> hace dos años. En un recién nacido, el nacimiento es la primera línea: <code>{{-20}} Nace de 38 semanas, parto vaginal, 3.240 g. Screening auditivo: refiere OD.</code></p>

    <label>Comentario del docente <span style="font-weight:400; color:var(--color-danger);">(privado -- el alumno nunca lo ve)</span>
        <textarea name="comentario_docente" rows="3" class="input" placeholder="Ej: hipoacusia sensorioneural bilateral leve, caso pensado para practicar enmascaramiento..."><?= htmlspecialchars((string) ($v['comentario_docente'] ?? '')) ?></textarea>
    </label>
    <p class="help" class="help">Nota interna del <strong>paciente</strong> (ej. qué patología representa el caso). Solo la ve el docente en este panel -- no se sincroniza a la ficha del alumno ni al cliente de escritorio.</p>

    <div class="photo-block">
        <strong style="display:block; margin-bottom:0.4rem;">Foto</strong>
        <p id="photo-msg" class="help" hidden></p>
        <?php $hasAvatar = PatientPhoto::hasAvatar($photoCaseId); ?>
        <div style="display:flex; align-items:center; gap:1rem;">
            <img id="patient-avatar-preview" class="patient-avatar"
                 src="patient_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;type=avatar&amp;v=<?= time() ?>"
                 alt="Avatar del paciente" <?= $hasAvatar ? '' : 'hidden' ?>>
            <div id="patient-avatar-empty" class="patient-avatar patient-avatar-empty" <?= $hasAvatar ? 'hidden' : '' ?>>Sin foto</div>
            <div>
                <input type="file" id="patient-photo-input" accept="image/jpeg,image/png,image/webp">
                <p class="help">Al elegir una foto se abre un recorte circular -- se guarda una versión reducida completa y el avatar recortado.</p>
                <p class="help">
                    <a id="patient-download-original" href="patient_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;type=original&amp;download=1" <?= $hasAvatar ? '' : 'hidden' ?>>Descargar foto grande</a>
                    &nbsp;|&nbsp;
                    <a id="patient-download-avatar" href="patient_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;type=avatar&amp;download=1" <?= $hasAvatar ? '' : 'hidden' ?>>Descargar foto recortada</a>
                </p>
            </div>
        </div>
    </div>
</div>
</div>
