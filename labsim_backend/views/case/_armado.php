<?php
/**
 * Armado rápido: los autocompletados que llenan el resto de las fichas.
 *
 * Vive fuera de public/ a propósito: el docroot del hosting es la raíz de
 * labsim_backend/ y public/.htaccess re-habilita todo lo que cuelga de
 * public/, así que ahí adentro esta ficha sería alcanzable por URL y
 * correría sin la sesión de admin que valida case_create.php.
 *
 * Incluido por admin/case_create.php, que comparte su scope: este archivo
 * NO declara lo que usa. Espera del padre $v, $isEdit.
 */
?>
<div class="tab-panel<?= $isEdit ? '' : ' active' ?>" data-tab="armado">
<div class="card">
    <strong>Armado rápido</strong>
    <p class="help">Se configura todo acá y se genera de una sola vez: el audiograma completo (aérea y ósea, los dos oídos), el timpanograma, la función tubaria, el sitio de la lesión, el patrón retrococlear, las ondas del ABR y las emisiones otoacústicas. Un botón, un caso entero y coherente.</p>
    <p class="help">No hay que elegir nada dos veces. Lo que decís acá sobre el oído define todo lo demás por proyección: la OEA sale del componente coclear, los reflejos del oído medio y del sitio de la lesión, los supraliminares del mismo número. El grado de la OEA no se fija aparte, justamente para que el caso no pueda contradecirse a sí mismo.</p>
    <p class="help">Nada de esto es obligatorio ni definitivo: un caso se arma entero a mano, pestaña por pestaña, y lo que el botón escribe queda en los campos de cada pestaña y se edita igual que si lo hubieras tipeado.</p>
</div>

<div class="card">
    <strong>Paciente</strong>
    <p class="help">El <strong>sexo</strong> decide el nombre, que lo escribe "Generar caso" junto con el resto. La <strong>edad</strong> pesa más: fija la fecha de nacimiento y el RUT, elige la población de referencia del ABR, es obligatoria para la anamnesis con IA, y fija el piso por edad que se suma a todos los cuadros (ver abajo).</p>
    <p class="help">Son los mismos campos de <a href="#" class="tab-link" data-goto-tab="paciente">Paciente</a>, no una copia: cambiarlos en cualquiera de los dos lados los cambia en el otro. El RUT, la foto y la historia clínica se cargan allá.</p>
    <div class="three-col">
        <label>Sexo
            <select id="armado-gender">
                <option value="0" <?= ($v['gender'] ?? '0') === '0' ? 'selected' : '' ?>>Hombre</option>
                <option value="1" <?= ($v['gender'] ?? '0') === '1' ? 'selected' : '' ?>>Mujer</option>
            </select>
        </label>
        <label>Edad
            <input type="number" id="armado-age" min="0" max="110" value="<?= htmlspecialchars((string) ($v['age'] ?? '')) ?>">
        </label>
    </div>

    <div id="armado-rn" hidden>
        <p class="help help--mt-md"><strong>Recién nacido.</strong> Con la edad en 0 hace falta la edad exacta: un bebé de 8 horas y uno de 8 meses son los dos "0 años" y no se parecen en nada. Las horas de vida deciden cuánto refiere el tamizaje --a las 6 horas la TEOAE refiere en más de la mitad de los recién nacidos SANOS mientras el AABR pasa en el 85 %-- y el parto, las semanas y el peso lo mueven de ahí. Todo esto se escribe en la ficha <a href="#" class="tab-link" data-goto-tab="paciente">Paciente</a>, donde se edita igual.</p>
        <div class="three-col">
            <label>Edad exacta
                <span style="display:flex; gap:0.3rem;">
                    <input type="number" id="armado-edad-valor" min="0" max="8760" step="1" style="width:5em;" placeholder="10">
                    <select id="armado-edad-unidad">
                        <option value="horas">horas</option>
                        <option value="dias">días</option>
                        <option value="meses">meses</option>
                    </select>
                </span>
            </label>
            <label>Parto
                <select id="armado-parto">
                    <option value="vaginal">Vaginal</option>
                    <option value="cesarea">Cesárea</option>
                </select>
            </label>
            <label>Semanas / peso (g)
                <span style="display:flex; gap:0.3rem;">
                    <input type="number" id="armado-semanas" min="24" max="42" step="1" style="width:4.5em;" placeholder="40">
                    <input type="number" id="armado-peso" min="400" max="6000" step="10" style="width:6em;" placeholder="3200">
                </span>
            </label>
        </div>
        <div class="two-col">
            <label>Infección congénita (TORCH)
                <select id="armado-torch">
                    <?php foreach (CaseBuilder::TORCH_OPTIONS as $tKey => $tLabel): ?>
                    <option value="<?= $tKey ?>"><?= htmlspecialchars($tLabel) ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
            <label>Días en UCI neonatal
                <input type="number" id="armado-uci" min="0" max="180" step="1" placeholder="0">
            </label>
        </div>
        <label class="inline-check"><input type="checkbox" id="armado-ototoxicos"> Aminoglucósidos u otros ototóxicos</label>
        <label class="inline-check"><input type="checkbox" id="armado-exanguino"> Hiperbilirrubinemia con exanguinotransfusión</label>
        <p class="help">Los indicadores de riesgo <strong>no</strong> inventan una hipoacusia ni mueven el tamizaje: el cuadro se elige abajo. Lo que hacen es que el caso tenga sentido clínico --un kernícterus sin exanguinotransfusión, o una ANSD sin UCI, se leen raro-- y obligan a seguimiento aunque el tamizaje pase.</p>
    </div>
</div>

<div class="card">
    <strong>El cuadro clínico, oído por oído</strong>
    <p class="help"><strong>Cada oído se elige por separado</strong>: categoría, cuadro y grado propios. El oído sin hallazgos se pide con "Normal para la edad", que no escribe ceros sino el piso por edad más la variabilidad.</p>

    <label class="inline-check" style="margin-left:0;">
        <input type="checkbox" id="armado-igualar" checked>
        Los dos oídos iguales
    </label>
    <p class="help">Con esto marcado, lo que elijas en el OD se copia al OI --que es el caso de la mayoría de los cuadros bilaterales-- y los dos oídos comparten magnitud, con unos pocos dB de asimetría biológica. Destildalo para un caso unilateral o asimétrico.</p>

    <div class="two-col">
    <?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
        <div class="side-block" data-lado="<?= $lado ?>">
            <div class="side-heading"><strong>Oído <?= $ladoLabel ?></strong></div>
            <label>Categoría
                <select class="perfil-categoria" data-lado="<?= $lado ?>">
                    <?php foreach (CaseProfile::CATEGORIAS as $catKey => $catLabel): ?>
                    <option value="<?= htmlspecialchars($catKey) ?>"><?= htmlspecialchars($catLabel) ?></option>
                    <?php endforeach; ?>
                    <option value="__random__">Cualquiera (al azar)</option>
                </select>
            </label>
            <label>Cuadro
                <select class="perfil-escenario" data-lado="<?= $lado ?>"></select>
            </label>
            <label>Grado
                <select class="perfil-grado" data-lado="<?= $lado ?>">
                    <option value="random">Cualquiera (al azar)</option>
                </select>
            </label>
        </div>
    <?php endforeach; ?>
    </div>

    <p class="help">La <strong>categoría</strong> dice dónde está la lesión y filtra los cuadros. El <strong>cuadro</strong> da la forma de la curva; el <strong>grado</strong>, cuánto. Elegido el grado se escala la forma completa --lo sensorioneural y el gap con el mismo factor-- hasta que el promedio caiga en el rango pedido: la proporción entre conductivo y sensorioneural es del cuadro y no cambia con el grado.</p>
    <p class="help">El selector de grado ofrece solo los que ese cuadro puede dar: la lista sale del cuadro, no es la misma para todos. Algunos además traen un techo en dB que recorta el grado aunque figure en la lista.</p>
    <p class="help">El grado se mide sobre el <strong>promedio de <?= implode(', ', CaseProfile::GRADE_FREQS) ?> Hz en vía aérea</strong> (BIAP). Audición normal hasta 20 dB HL, así que el leve arranca en 21. <strong>Ojo:</strong> el equipo le muestra al alumno el promedio de Fletcher (mejores 2 de 500, 1000 y 2000), que ignora 4 kHz. En los cuadros descendentes el número del equipo va a dar más bajo que el grado que pediste acá: son dos escalas distintas, no un error.</p>

    <div class="section-sep" style="border-top:1px dashed var(--color-border);">
        <button type="button" id="perfil-generar">Generar caso</button>
        <span id="armado-estado" class="help"></span>
    </div>
    <p class="help">Generar <strong>pisa</strong> el audiograma, la timpanometría, el perfil, el ABR, la OEA y el VEMP de los dos oídos, el tinnitus, los rasgos del paciente en la entrevista, el nombre y el comentario del docente. No toca la edad, el RUT, la foto, la historia clínica, la otoscopia ni la anamnesis.</p>
    <p class="help">El <strong>comentario del docente</strong> (en <a href="#" class="tab-link" data-goto-tab="paciente">Paciente</a>, privado) queda escrito con el cuadro y el grado que salieron, nada más. Apenas escribas ahí, el campo pasa a ser tuyo y Generar deja de tocarlo.</p>
    <p class="help">La <strong>acumetría</strong> y el <strong>SDT/SRT</strong> vuelven a "auto", así se recalculan desde el audiograma nuevo en vez de quedar con los del anterior. Se destildan de vuelta en <a href="#" class="tab-link" data-goto-tab="audiometria">Audiometría</a>.</p>
    <p class="help">Si el paciente es <strong>menor de 18</strong> y la sala está vacía, le agrega la madre en <a href="#" class="tab-link" data-goto-tab="sala">Sala</a>, con nombre, edad y rasgos sorteados --distintos en cada generación, para que dos casos del mismo cuadro no den la misma entrevista--. Hasta los 13 la deja como informante principal; de 14 a 17 el informante sigue siendo el paciente. Si la sala <em>ya</em> tiene gente, no la toca.</p>
    <p class="help">Al editar un caso que ya existe, el nombre NO se toca: ahí el nombre es del paciente y cambiarlo afectaría a todas sus otras citas.</p>
    <p class="help">El <strong>VEMP</strong> queda escrito en <a href="#" class="tab-link" data-goto-tab="vemp">VEMP</a>: la patología del oído y el umbral de los tres subtipos. El umbral sale de un rango por cuadro, salvo en las conductivas y mixtas, donde sale del gap que se acaba de generar. Las desviaciones por onda vuelven a 0.</p>
    <p class="help">Los cuadros sin eje vestibular cargado --entre ellos la súbita y la ototóxica-- salen con VEMP normal, y eso es lo que el generador escribe, no un pendiente que quedó. Si el caso pide otra cosa, se carga a mano en la pestaña.</p>
    <p class="help">El <strong>tinnitus</strong> se sortea con la probabilidad que tenga el cuadro, así que dos casos del mismo cuadro pueden salir uno con acúfeno y otro sin. La lateralidad sale de a cuántos oídos les tocó un cuadro con acúfeno; el ruido y la frecuencia de matching, del cuadro. Pulsátil nunca se genera: se marca a mano en <a href="#" class="tab-link" data-goto-tab="tinnitus">Tinnitus</a>. El estado de acá arriba dice qué salió.</p>
    <p class="help">La <strong>conciencia</strong> y la <strong>confiabilidad</strong> del paciente (en <a href="#" class="tab-link" data-goto-tab="sala">Sala</a>) se sortean en vez de quedar en el valor por defecto, y el rango de conciencia lo corre el cuadro. Van al prompt del LLM: son de lo que más cambia la entrevista, y calcados en todos los casos el alumno la memoriza. Lo mismo con el comportamiento y la sensibilidad de la madre.</p>
    <p class="help">Lo que queda para decidir a mano después es el detalle fino de la función tubaria. El editor lo reclama al guardar si quedó sin tocar.</p>
    <p class="help">Generar <strong>destilda todas las fichas</strong> del <a href="#" class="tab-link" data-goto-tab="resumen">Resumen</a>: lo que estaba revisado era el caso anterior, y este es otro. Un caso generado al azar no se guarda hasta que alguien lo haya recorrido ficha por ficha y lo haya dado por bueno ahí.</p>
</div>

<div class="card">
    <strong>Lo normal depende de la edad</strong>
    <p class="help">El umbral mediano de <a href="https://www.iso.org/standard/42916.html" target="_blank" rel="noopener">ISO 7029</a> para la edad y el sexo cargados se suma como <strong>piso a todos los cuadros</strong>, no solo al normal: el cuadro que elegís se apila encima. La tabla de abajo muestra el piso que se está usando ahora mismo, y se actualiza al cambiar edad o sexo.</p>
    <div id="armado-norma-edad" class="help"></div>
</div>

<div class="card">
    <strong>Después de generar: la anamnesis con IA</strong>
    <p class="gen-step-dest">Escribe en <a href="#" class="tab-link" data-goto-tab="anamnesis">11. Anamnesis</a></p>
    <p class="help"><strong>Esto va al final, aparte, y a propósito.</strong> El modelo lee los hallazgos que ya están cargados (audiograma, timpanograma, perfil, tinnitus, edad) y escribe los antecedentes que los explican. Con la ficha vacía no tiene nada que leer, así que este botón va después de generar el caso y de revisarlo.</p>
    <p class="help">No inventa el diagnóstico ni menciona umbrales -- eso lo tiene que medir el alumno. Las derivaciones las escribe por el estudio ("se deriva a evaluación auditiva", "a BERA"), nunca por la profesión de quien atiende. Las <strong>atenciones previas</strong> no salen de acá: se escriben a mano en Historia clínica (<a href="#" class="tab-link" data-goto-tab="paciente">Paciente</a>), con las fechas relativas <code>{{-N}}</code>.</p>
    <p class="help"><strong>Es un borrador y hay que leerlo.</strong> El modelo puede inventar una cirugía que no existe o un fármaco que no es ototóxico, y eso le llega al alumno como parte del caso, indistinguible de lo que escribiste vos. Al terminar te deja en <a href="#" class="tab-link" data-goto-tab="anamnesis">Anamnesis</a> para que lo leas: hasta que tildes la verificación ahí, el caso no se guarda.</p>
    <button type="button" class="secondary" id="anamnesis-ia-btn">Redactar borrador con IA</button>
    <span id="anamnesis-ia-estado" class="help"></span>
    <input type="hidden" name="anamnesis_ia[generado]" id="anamnesis-ia-generado" value="<?= fv($v, ['anamnesis_ia', 'generado'], '') ? '1' : '' ?>">
    <input type="hidden" name="anamnesis_ia[generado_en]" id="anamnesis-ia-generado-en" value="<?= htmlspecialchars((string) fv($v, ['anamnesis_ia', 'generado_en'], '')) ?>">
</div>
</div>
