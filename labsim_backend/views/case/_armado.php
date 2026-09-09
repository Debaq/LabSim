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
    <p class="legend help">Se configura todo acá y se genera de una sola vez: el audiograma completo (aérea y ósea, los dos oídos), el timpanograma, la función tubaria, el sitio de la lesión, el patrón retrococlear, las ondas del ABR y las emisiones otoacústicas. Un botón, un caso entero y coherente.</p>
    <p class="legend help">No hay que elegir nada dos veces. Lo que decís acá sobre el oído define todo lo demás por proyección: la OEA sale del componente coclear, los reflejos del oído medio y del sitio de la lesión, los supraliminares del mismo número. Antes había que fijar el grado de la OEA por separado, y era la forma más fácil de armar un caso que se contradice a sí mismo.</p>
    <p class="legend help">Nada de esto es obligatorio ni definitivo: un caso se arma entero a mano, pestaña por pestaña, y lo que el botón escribe queda en los campos de cada pestaña y se edita igual que si lo hubieras tipeado.</p>
</div>

<div class="card">
    <strong>Paciente</strong>
    <p class="legend help">El <strong>sexo</strong> decide el nombre, que lo escribe "Generar caso" junto con el resto -- ya no hay un botón aparte para eso. La <strong>edad</strong> pesa más: fija la fecha de nacimiento y el RUT, elige la población de referencia del ABR --un neonato no tiene las latencias de un adulto--, es obligatoria para la anamnesis con IA, y define <strong>qué es normal</strong> en este paciente (ver abajo).</p>
    <p class="legend help">Son los mismos campos de <a href="#" class="tab-link" data-goto-tab="paciente">Paciente</a>, no una copia: cambiarlos en cualquiera de los dos lados los cambia en el otro. El RUT, la foto y la historia clínica se cargan allá.</p>
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
</div>

<div class="card">
    <strong>El cuadro clínico, oído por oído</strong>
    <p class="legend help"><strong>Cada oído lleva lo suyo.</strong> Un paciente puede tener el OD sano y una otitis en el OI, o una presbiacusia de un lado y un schwannoma del otro. El oído que no tiene nada se pide con "Normal para la edad", que no es un cero.</p>

    <label class="inline-check" style="margin-left:0;">
        <input type="checkbox" id="armado-igualar" checked>
        Los dos oídos iguales
    </label>
    <p class="legend help">Con esto marcado, lo que elijas en el OD se copia al OI --que es el caso de la mayoría de los cuadros bilaterales-- y los dos oídos comparten magnitud, con unos pocos dB de asimetría biológica. Destildalo para un caso unilateral o asimétrico.</p>

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

    <p class="legend help">La <strong>categoría</strong> dice dónde está la lesión y filtra los cuadros. El <strong>cuadro</strong> da la forma de la curva; el <strong>grado</strong>, cuánto. Elegido el grado se escala la forma completa --lo sensorioneural y el gap con el mismo factor-- hasta que el promedio caiga en el rango pedido: la proporción entre conductivo y sensorioneural es del cuadro y no cambia con el grado.</p>
    <p class="legend help">Cada cuadro ofrece solo los grados que puede dar sin dejar de ser ese cuadro. Una conductiva pura no pasa de moderada porque la vía ósea le pone techo (más que eso ya es mixta); una muesca de 4 kHz no es una hipoacusia severa por promedio; un descendente puro no llega a severa sin aplanarse.</p>
    <p class="legend help">El grado se mide sobre el <strong>promedio de <?= implode(', ', CaseProfile::GRADE_FREQS) ?> Hz en vía aérea</strong> (BIAP). Audición normal hasta 20 dB HL, así que el leve arranca en 21. <strong>Ojo:</strong> el equipo le muestra al alumno el promedio de Fletcher (mejores 2 de 500, 1000 y 2000), que ignora 4 kHz -- en un descendente el número que él calcule va a dar más bajo que el grado con que armaste el caso. Es la diferencia entre las dos escalas, no un error.</p>

    <div class="section-sep" style="border-top:1px dashed var(--color-border);">
        <button type="button" id="perfil-generar">Generar caso</button>
        <span id="armado-estado" class="legend"></span>
    </div>
    <p class="legend help">Generar <strong>pisa</strong> el audiograma, la timpanometría, el perfil, el ABR y la OEA de los dos oídos, y el nombre del paciente. No toca la edad, el RUT, la foto, la historia clínica, la otoscopia, el tinnitus, el VEMP ni la anamnesis.</p>
    <p class="legend help">Si el paciente es <strong>menor de 18</strong> y la sala está vacía, le agrega la madre: un menor no llega solo, y ella aporta lo que el niño no puede contar por más que hable bien --embarazo, parto, screening neonatal, colegio--. Hasta los 13 la historia la cuenta ella; de 14 a 17 la cuenta el paciente y ella completa. Cuánto se mete y cuánto le creemos varían en cada generación. Si la sala <em>ya</em> tiene gente, no la toca.</p>
    <p class="legend help">Al editar un caso que ya existe, el nombre NO se toca: ahí el nombre es del paciente y cambiarlo afectaría a todas sus otras citas.</p>
    <p class="legend help">Lo que queda para decidir a mano después es lo que ninguna cuenta puede sacar del audiograma: el VEMP, y el detalle fino de la función tubaria. El editor los reclama al guardar si quedaron sin tocar.</p>
</div>

<div class="card">
    <strong>Lo normal depende de la edad</strong>
    <p class="legend help">Un niño de 10 que oye bien da 0 dB en todas las frecuencias. Un hombre de 70 que también oye bien llega a 30 dB en 4 kHz, y sigue siendo <strong>normal para su edad</strong>. Por eso el umbral mediano de <a href="https://www.iso.org/standard/42916.html" target="_blank" rel="noopener">ISO 7029</a> se suma como piso a todos los cuadros, no solo al normal: un señor de 70 con una otitis media tiene la otitis <em>y</em> su presbiacusia.</p>
    <p class="legend help">Esto es lo que hace posible el ejercicio de decidir si una presbiacusia es más de lo esperable para la edad, que con todos los "normales" en 0 no se podía plantear.</p>
    <div id="armado-norma-edad" class="legend"></div>
</div>

<div class="card">
    <strong>Después de generar: la anamnesis con IA</strong>
    <p class="gen-step-dest">Escribe en <a href="#" class="tab-link" data-goto-tab="anamnesis">11. Anamnesis</a></p>
    <p class="legend help"><strong>Esto va al final, aparte, y a propósito.</strong> El modelo escribe los antecedentes que EXPLICAN los hallazgos que ya están cargados: una muesca en 4 kHz pide exposición a ruido, una otitis a repetición pide una conductiva con timpanograma B, una neuropatía en un recién nacido pide hiperbilirrubinemia. Con la ficha vacía no tiene nada que explicar, así que se aprieta después de generar el caso y de revisarlo.</p>
    <p class="legend help">No inventa el diagnóstico ni menciona umbrales -- eso lo tiene que medir el alumno. Las derivaciones las escribe por el estudio ("se deriva a evaluación auditiva", "a BERA"), nunca por la profesión de quien atiende. Las <strong>atenciones previas</strong> no salen de acá: se escriben a mano en Historia clínica (<a href="#" class="tab-link" data-goto-tab="paciente">Paciente</a>), con las fechas relativas <code>{{-N}}</code>.</p>
    <p class="legend help"><strong>Es un borrador y hay que leerlo.</strong> El modelo puede inventar una cirugía que no existe o un fármaco que no es ototóxico, y eso le llega al alumno como parte del caso, indistinguible de lo que escribiste vos. Al terminar te deja en <a href="#" class="tab-link" data-goto-tab="anamnesis">Anamnesis</a> para que lo leas: hasta que tildes la verificación ahí, el caso no se guarda.</p>
    <button type="button" class="secondary" id="anamnesis-ia-btn">Redactar borrador con IA</button>
    <span id="anamnesis-ia-estado" class="legend"></span>
    <input type="hidden" name="anamnesis_ia[generado]" id="anamnesis-ia-generado" value="<?= fv($v, ['anamnesis_ia', 'generado'], '') ? '1' : '' ?>">
    <input type="hidden" name="anamnesis_ia[generado_en]" id="anamnesis-ia-generado-en" value="<?= htmlspecialchars((string) fv($v, ['anamnesis_ia', 'generado_en'], '')) ?>">
</div>
</div>
