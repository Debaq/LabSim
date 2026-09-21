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
        <label>Edad exacta <span class="help" style="font-weight:normal;">(solo si va en 0)</span>
            <span style="display:flex; gap:0.3rem;">
                <input type="number" name="edad_valor" id="patient-edad-valor" min="0" max="8760" step="1" style="width:5em;" value="<?= htmlspecialchars((string) ($v['edad_valor'] ?? '')) ?>">
                <select name="edad_unidad" id="patient-edad-unidad">
                    <?php foreach (['horas' => 'horas', 'dias' => 'días', 'meses' => 'meses'] as $u => $uLabel): ?>
                    <option value="<?= $u ?>"<?= ($v['edad_unidad'] ?? 'horas') === $u ? ' selected' : '' ?>><?= $uLabel ?></option>
                    <?php endforeach; ?>
                </select>
            </span>
        </label>
        <label>Fecha de nacimiento
            <input type="text" name="fecha_nac" id="patient-fecha-nac" value="<?= htmlspecialchars((string) ($v['fecha_nac'] ?? '')) ?>" readonly title="Se calcula sola a partir de la edad (día y mes al azar)." placeholder="AAAA-MM-DD">
        </label>
        <label>RUT
            <input type="text" name="rut" id="patient-rut" value="<?= htmlspecialchars((string) ($v['rut'] ?? '')) ?>">
        </label>
    </div>

    <?php $nac = $v['nacimiento'] ?? []; ?>
    <details class="nacimiento"<?= ($v['edad_valor'] ?? '') !== '' ? ' open' : '' ?>>
        <summary><strong>Recién nacido: parto y antecedentes</strong></summary>
        <p class="help help--mt">Solo aplica si la edad va en 0 y se cargó la edad exacta. Lo de arriba mueve cuánto refiere el tamizaje en las primeras horas --el líquido del oído medio se exprime en el canal del parto, así que una cesárea sin trabajo de parto se comporta como un bebé 12 horas más joven para la EOA-- y <strong>no cambia la audición del paciente</strong>.</p>
        <div class="three-col">
            <label>Parto
                <select name="nacimiento[parto]">
                    <option value="vaginal"<?= (($nac['parto'] ?? 'vaginal') === 'vaginal') ? ' selected' : '' ?>>Vaginal</option>
                    <option value="cesarea"<?= (($nac['parto'] ?? '') === 'cesarea') ? ' selected' : '' ?>>Cesárea</option>
                </select>
            </label>
            <label>Edad gestacional (semanas)
                <input type="number" name="nacimiento[semanas]" id="nac-semanas" min="24" max="42" step="1" value="<?= htmlspecialchars((string) ($nac['semanas'] ?? '')) ?>" placeholder="40" title="Menos de 34 semanas pesa mucho más que el pretérmino tardío (34-36): conducto más colapsable y vía todavía madurando, así que el AABR también se resiente.">
            </label>
            <label>Peso al nacer (g)
                <input type="number" name="nacimiento[peso_g]" id="nac-peso" min="400" max="6000" step="10" value="<?= htmlspecialchars((string) ($nac['peso_g'] ?? '')) ?>" placeholder="3200" title="Bajo <?= CaseBuilder::PESO_MUY_BAJO_G ?> g (muy bajo peso, JCIH 2019) el tamizaje refiere bastante más, y se suma a lo de las semanas.">
            </label>
        </div>
        <p class="help" id="nac-riesgo-aviso" hidden></p>
        <label class="inline-check"><input type="checkbox" name="nacimiento[peg]" value="1" <?= !empty($nac['peg']) ? 'checked' : '' ?>> Pequeño para la edad gestacional</label>
        <label class="inline-check"><input type="checkbox" name="nacimiento[vernix_limpiado]" value="1" <?= !empty($nac['vernix_limpiado']) ? 'checked' : '' ?>> Se limpió el vérnix del conducto antes de medir</label>
        <label class="inline-check"><input type="checkbox" name="nacimiento[liquido_persistente]" value="1" <?= !empty($nac['liquido_persistente']) ? 'checked' : '' ?>> Líquido o vérnix persistente (no se resolvió con las horas)</label>

        <p class="help help--mt-md"><strong>Indicadores de riesgo (JCIH 2019).</strong> Estos <strong>no</strong> mueven el tamizaje ni inventan una hipoacusia: son el antecedente que obliga a seguimiento y lo que hace que el caso tenga sentido clínico. Varias TORCH dan hipoacusia progresiva o de aparición tardía, así que "pasó el tamizaje" no cierra el problema.</p>
        <div class="three-col">
            <label>Infección congénita
                <select name="nacimiento[torch]">
                    <?php foreach (CaseBuilder::TORCH_OPTIONS as $tKey => $tLabel): ?>
                    <option value="<?= $tKey ?>"<?= (((string) ($nac['torch'] ?? '')) === (string) $tKey) ? ' selected' : '' ?>><?= htmlspecialchars($tLabel) ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
            <label>Días en UCI neonatal
                <input type="number" name="nacimiento[uci_dias]" min="0" max="180" step="1" value="<?= htmlspecialchars((string) ($nac['uci_dias'] ?? '')) ?>" placeholder="0" title="Más de 5 días es indicador de riesgo por sí solo (JCIH 2019).">
            </label>
        </div>
        <label class="inline-check"><input type="checkbox" name="nacimiento[torch_sintomatica]" value="1" <?= !empty($nac['torch_sintomatica']) ? 'checked' : '' ?>> Infección sintomática al nacer (mucho más riesgo que la asintomática)</label>
        <label class="inline-check"><input type="checkbox" name="nacimiento[ototoxicos]" value="1" <?= !empty($nac['ototoxicos']) ? 'checked' : '' ?>> Aminoglucósidos u otros ototóxicos</label>
        <label class="inline-check"><input type="checkbox" name="nacimiento[exanguinotransfusion]" value="1" <?= !empty($nac['exanguinotransfusion']) ? 'checked' : '' ?>> Hiperbilirrubinemia con exanguinotransfusión</label>
        <?php foreach (['OD', 'OI'] as $ladoNac): ?>
        <input type="hidden" name="nacimiento[percentil][<?= $ladoNac ?>]" value="<?= htmlspecialchars((string) ($nac['percentil'][$ladoNac] ?? '')) ?>">
        <?php endforeach; ?>
    </details>
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
    <p class="help">Esto edita al <strong>paciente</strong>: el cambio se aplica también a cualquier otra cita/ronda de la misma persona.</p>
    <?php endif; ?>

    <label>Historia clínica
        <textarea name="historia_clinica" rows="6" class="input" placeholder="{{-20}} Nace de 38 semanas, parto vaginal, 3.240 g. Screening auditivo: refiere OD.&#10;{{-5}} Control con pediatra, se deriva a evaluación auditiva."><?= htmlspecialchars((string) ($v['historia_clinica'] ?? '')) ?></textarea>
    </label>
    <p class="help">Las <strong>atenciones previas</strong> del paciente: qué le hicieron antes de llegar acá y qué se encontró, una por línea y de la más antigua a la más reciente. Es del <strong>paciente</strong>, no del caso. No incluye las notas individuales de cada alumno por atención -- esas se ven en la agenda/asistencia, no se editan acá.</p>
    <p class="help">Las fechas no se escriben a mano: poné <code>{{-N}}</code> al principio de la línea, donde N son los <strong>días antes</strong> de la cita que va a atender el alumno, y la app lo reemplaza por la fecha real. Así el mismo caso sirve en cualquier fecha. Ejemplos: <code>{{-5}}</code> hace cinco días, <code>{{-30}}</code> hace un mes, <code>{{-730}}</code> hace dos años. En un recién nacido, el nacimiento es la primera línea: <code>{{-20}} Nace de 38 semanas, parto vaginal, 3.240 g. Screening auditivo: refiere OD.</code></p>

    <label>Comentario del docente <span style="font-weight:400; color:var(--color-danger);">(privado -- el alumno nunca lo ve)</span>
        <textarea name="comentario_docente" rows="3" class="input" placeholder="Ej: hipoacusia sensorioneural bilateral leve, caso pensado para practicar enmascaramiento..."><?= htmlspecialchars((string) ($v['comentario_docente'] ?? '')) ?></textarea>
    </label>
    <p class="help">Nota interna del <strong>paciente</strong> (ej. qué patología representa el caso). Solo la ve el docente en este panel: no llega al alumno, ni en la ficha ni en el equipo.</p>

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
                <!-- El "|" que separa los dos enlaces es texto suelto, no un
                     elemento: ocultando cada <a> por separado quedaba flotando
                     solo en un paciente sin foto. Se oculta el parrafo entero,
                     que ademas es lo unico que hay adentro. -->
                <p class="help" id="patient-download-links" <?= $hasAvatar ? '' : 'hidden' ?>>
                    <a id="patient-download-original" href="patient_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;type=original&amp;download=1">Descargar foto grande</a>
                    &nbsp;|&nbsp;
                    <a id="patient-download-avatar" href="patient_photo.php?case_id=<?= urlencode($photoCaseId) ?>&amp;type=avatar&amp;download=1">Descargar foto recortada</a>
                </p>
            </div>
        </div>
    </div>
</div>
</div>
