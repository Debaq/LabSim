<?php
/**
 * Ficha 7 -- ABR: patología, ondas y patrón retrococlear por oído.
 *
 * Vive fuera de public/ a propósito: el docroot del hosting es la raíz de
 * labsim_backend/ y public/.htaccess re-habilita todo lo que cuelga de
 * public/, así que ahí adentro esta ficha sería alcanzable por URL y
 * correría sin la sesión de admin que valida case_create.php.
 *
 * Incluido por admin/case_create.php, que comparte su scope: este archivo
 * NO declara lo que usa. Espera del padre $v, $abrAuthorCatalog.
 */
?>
<div class="tab-panel" data-tab="abr">
<div class="card">
    <strong>Autor de referencia</strong>
    <p class="help">Set normativo con el que se calculan las ondas, uno solo para todo el paciente. Cada autor reporta baselines de latencia y amplitud levemente distintos según la población. La lista trae los sets publicados (con su cita y su protocolo en <a href="normativas.php">Configuración &rsaquo; Normativas</a>) y los que haya armado usted; un set que no cubre una población o una onda la completa con el default, campo por campo. Los números finales quedan en cada campo; en el caso queda además registrado CON QUÉ set se construyó y qué baseline tenía, para poder rastrearlo después.</p>
    <label style="max-width:22em;">Autor
        <select id="abr-author-select" name="abr[autor]">
            <option value="__default__"<?= ($v['abr']['autor'] ?? '__default__') === '__default__' ? ' selected' : '' ?>>LabSim (default)</option>
            <?php foreach ($abrAuthorCatalog as $authorId => $author): ?>
            <option value="<?= htmlspecialchars($authorId) ?>"<?= ($v['abr']['autor'] ?? '') === $authorId ? ' selected' : '' ?>><?= htmlspecialchars($author['label'] ?? $authorId) ?></option>
            <?php endforeach; ?>
        </select>
    </label>
    <p class="help">Las ondas ya las escribió <a href="#" class="tab-link" data-goto-tab="armado">Armado rápido</a> al generar el caso. Los botones de acá abajo son para volver a sortearlas de un oído sin regenerar todo -- por ejemplo después de cambiar el autor.</p>
</div>
<div class="two-col">
<?php foreach (CaseBuilder::LADOS as $lado => $ladoLabel): ?>
<div class="card">
    <strong>ABR <?= $ladoLabel ?></strong>
    <p class="help">Patología de este oído para el generador de curvas ABR -- no es el resultado del alumno, es lo que el caso simula. Si se deja "Normal" con todo en 0, el oído no tiene hallazgos.</p>
    <p class="derivado-aviso" data-derivado="abr" hidden>La patología y el umbral de este oído los sugiere el <a href="#" class="tab-link" data-goto-tab="perfil">Perfil auditivo</a>, porque la casilla <em>ABR: umbral por estímulo</em> está encendida: se escriben solos con lo que predice el perfil y <strong>se pueden editar</strong>: lo que quede en pantalla es lo que se guarda. Cambiar el audiograma o el perfil vuelve a sugerir y pisa lo editado a mano; para que no se toquen más, apagar esa casilla.</p>

    <p class="help">Latencias y amplitudes onda por onda. "Volver a sortear" toma la patología y el umbral que ya tiene este oído --que los fija el perfil, no este botón-- y le calcula ondas plausibles con el sexo, la edad y el autor de referencia. Es un punto de partida al azar: cualquier campo se edita después.</p>
    <button type="button" class="secondary abr-autofill-btn" data-lado="<?= $lado ?>" style="margin-top:0;">Volver a sortear las ondas de este oído</button>
    <div class="three-col">
        <label>Patología
            <select name="abr[<?= $lado ?>][type]" class="abr-type-select" data-lado="<?= $lado ?>">
                <?php foreach (CaseBuilder::ABR_TYPE_OPTIONS as $opt): ?>
                <option value="<?= $opt ?>" <?= ($v['abr'][$lado]['type'] ?? 'normal') === $opt ? 'selected' : '' ?>><?= ucfirst($opt) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Umbral (dB) <span class="muted help--xs">referido a 2000 barridos</span>
            <input type="number" name="abr[<?= $lado ?>][umbral]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['umbral'] ?? '20')) ?>" title="El nivel donde el equipo declara respuesta en la mitad de los registros CON 2000 BARRIDOS. Quien promedie más puede encontrar respuesta algo por debajo, y está bien: es lo que pasa con un paciente tranquilo y mucho promediado.">
        </label>
        <label class="inline-check" style="align-self:end;">
            <input type="checkbox" name="abr[<?= $lado ?>][repro]" <?= ($v['abr'][$lado]['repro'] ?? '1') === '1' ? 'checked' : '' ?>>
            Reproducible
        </label>
        <label>Jitter si no reproducible (ms)
            <input type="number" step="0.01" min="0" name="abr[<?= $lado ?>][repro_var]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['repro_var'] ?? '0.2')) ?>">
        </label>
        <label>Inquietud durante la captura (0-1)
            <input type="number" step="0.1" min="0" max="1" name="abr[<?= $lado ?>][inquietud]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['inquietud'] ?? '0')) ?>">
        </label>
        <label>Reflejo post-auricular PAM (0-1)
            <input type="number" step="0.1" min="0" max="1" name="abr[<?= $lado ?>][pam]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['pam'] ?? '0')) ?>">
        </label>
    </div>
    <p class="help">Inquietud: 0 es un paciente quieto. Por encima de 0 la captura tiene tramos en que el paciente se mueve: el EEG crudo se ensucia, el equipo descarta esos barridos y el promedio se queda quieto hasta que se calma (el contador de aceptados se separa del de presentados). Si el alumno apagó el rechazo de artefacto, en cambio, esa basura entra al promedio y el FSP no cruza nunca.</p>
    <p class="help">PAM: 0 lo desactiva. Por encima de 0 se agrega el potencial miogénico a partir de 60 dB, creciendo con el nivel y centrado en 13 ms. A diferencia de la falsa onda V, se promedia como respuesta y <strong>replica en A y B</strong>: si lo que querés es un artefacto que los subpromedios delaten, ese es el campo de abajo, no éste.</p>
    <p class="help">El patrón retrococlear (I-III, III-V, bloqueo, razón V/I, microfónico, desincronía, sensibilidad a la tasa) se configura en la pestaña <a href="#" class="tab-link" data-goto-tab="perfil">Perfil auditivo</a>, junto al resto del sitio de la lesión: los mismos parámetros gobiernan lo que se ve en el ABR y lo que NO se ve en la OEA.</p>
    <p class="help">Promediaciones que el caso realmente necesita para que la onda se vea resuelta (independiente de cuántas pida el alumno en el equipo) -- si el alumno detiene la captura antes de llegar a este número, la curva queda parcialmente sin resolver.</p>
    <div class="three-col">
        <label>Promediaciones objetivo
            <input type="number" step="1" min="1" name="abr[<?= $lado ?>][average_objetivo]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['average_objetivo'] ?? '2000')) ?>">
        </label>
    </div>
    <p class="help">Valor de la onda a 80 dB (ms de latencia, µV de amplitud) -- precargado con el normativo de la población/autor elegidos arriba, edítelo para fijar el valor real del paciente. El generador calcula solo el resto de la serie de intensidades a partir de este punto.</p>
    <div class="three-col">
        <?php
        $abrWaveFields = [
            ['I', 'lat', 'Onda I -- latencia'], ['III', 'lat', 'Onda III -- latencia'], ['V', 'lat', 'Onda V -- latencia'],
            ['I', 'amp', 'Onda I -- amplitud'], ['III', 'amp', 'Onda III -- amplitud'], ['V', 'amp', 'Onda V -- amplitud'],
        ];
        foreach ($abrWaveFields as [$abrWave, $abrField, $abrLabel]):
            $abrName = $abrField . '_' . $abrWave;
        ?>
        <label><?= $abrLabel ?>
            <input type="number" step="0.01" class="abr-abs-input" data-lado="<?= $lado ?>" data-wave="<?= $abrWave ?>" data-field="<?= $abrField ?>">
        </label>
        <input type="hidden" name="abr[<?= $lado ?>][<?= $abrName ?>]" class="abr-delta-input" data-lado="<?= $lado ?>" data-wave="<?= $abrWave ?>" data-field="<?= $abrField ?>" value="<?= htmlspecialchars((string) ($v['abr'][$lado][$abrName] ?? '0')) ?>">
        <?php endforeach; ?>
    </div>
    <p class="help">Falsa onda V. Se inyecta en UNA sola mitad de los barridos: el promedio la muestra, los subpromedios A/B la delatan (uno la tiene entera, el otro no) y no sube el FSP. La latencia que fijes es fija --no migra al bajar la intensidad-- y el rango acota en qué intensidades aparece; fuera de ese rango la serie queda limpia. Amplitud 0 = desactivada. El autocompletar por patología no la toca: se arma a mano.</p>
    <div class="three-col">
        <label>Falsa V: amplitud en el promedio (µV)
            <input type="number" step="0.01" min="0" name="abr[<?= $lado ?>][falsa_v_amp]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['falsa_v_amp'] ?? '0')) ?>">
        </label>
        <label>Falsa V: latencia (ms)
            <input type="number" step="0.1" min="0" name="abr[<?= $lado ?>][falsa_v_lat]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['falsa_v_lat'] ?? '5.6')) ?>">
        </label>
        <label>Falsa V: desde (dB)
            <input type="number" step="5" min="0" name="abr[<?= $lado ?>][falsa_v_int_min]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['falsa_v_int_min'] ?? '0')) ?>">
        </label>
        <label>Falsa V: hasta (dB)
            <input type="number" step="5" min="0" name="abr[<?= $lado ?>][falsa_v_int_max]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['falsa_v_int_max'] ?? '120')) ?>">
        </label>
        <label>Falsa V: mitad afectada
            <?php $fvMitad = (string) ($v['abr'][$lado]['falsa_v_mitad'] ?? 'auto'); ?>
            <select name="abr[<?= $lado ?>][falsa_v_mitad]">
                <?php foreach (['auto' => 'Al azar', 'a' => 'Subpromedio A', 'b' => 'Subpromedio B'] as $fvKey => $fvLabel): ?>
                <option value="<?= $fvKey ?>" <?= $fvMitad === $fvKey ? 'selected' : '' ?>><?= $fvLabel ?></option>
                <?php endforeach; ?>
            </select>
        </label>
    </div>
    <p class="help">Electrococleografía de este oído. Es otra prueba del mismo equipo (combo <em>Test</em> del panel del alumno), no otro módulo: se registra con los mismos electrodos y el mismo promediador, pero con electrodo de oído y ventana corta. Estos tres campos son lo único que el ECochG agrega al oído; la microfónica sale del patrón retrococlear del <a href="#" class="tab-link" data-goto-tab="perfil">Perfil auditivo</a>, porque es el mismo potencial registrado con otro electrodo.</p>
    <p class="help">La razón PS/PA se escribe <strong>una sola vez, como la mediría el electrodo apoyado en el tímpano</strong> (el «Timpánico (ECochG)» del combo Montaje del alumno). Con los otros dos electrodos el cliente la recalcula en la misma proporción que su límite, así que el oído no cambia de veredicto al cambiar de electrodo: debajo del campo se ve lo que va a leer el alumno con cada uno. Es la razón medida a nivel alto: el PS sale entero desde 50 dB por encima del umbral del click (90 dB nHL alcanza con umbral de hasta 40) y más abajo se achica. De dónde sale cada límite, con su bibliografía: <a href="bibliografia.php#ecochg">Configuración &rsaquo; Bibliografía</a>.</p>
    <div class="three-col">
        <label>Razón PS/PA (electrodo en el tímpano)
            <input type="number" step="0.01" min="0" max="<?= CaseBuilder::ECOCHG_SP_AP_MAX ?>" name="abr[<?= $lado ?>][ecochg][sp_ap]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['ecochg']['sp_ap'] ?? CaseBuilder::ECOCHG_DEFAULTS['sp_ap'])) ?>" title="Lo que mide el alumno con las marcas bien puestas es este número. Por encima del límite del electrodo la celda le sale en rojo.">
            <span class="help help--xs ecochg-equiv" data-lado="<?= $lado ?>" data-limites="<?= htmlspecialchars(json_encode(CaseBuilder::ECOCHG_SP_AP_LIMITS)) ?>"></span>
        </label>
        <label>Adaptación del PA por tasa (×)
            <input type="number" step="0.1" min="1" max="<?= CaseBuilder::ECOCHG_TASA_MAX ?>" name="abr[<?= $lado ?>][ecochg][tasa]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['ecochg']['tasa'] ?? CaseBuilder::ECOCHG_DEFAULTS['tasa'])) ?>" title="1 = se adapta como un oído sano. Por encima, el PA se atrasa y se achica más al subir la tasa; el alumno lo ve comparando dos curvas del mismo oído a distinta tasa.">
        </label>
        <label>Separación rarefacción-condensación (ms)
            <input type="number" step="0.01" min="0" max="<?= CaseBuilder::ECOCHG_RAR_COND_MAX_MS ?>" name="abr[<?= $lado ?>][ecochg][rar_cond_ms]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['ecochg']['rar_cond_ms'] ?? CaseBuilder::ECOCHG_DEFAULTS['rar_cond_ms'])) ?>" title="Cuánto más tarde llega el PA en condensación que en rarefacción. 0,1 ms es lo de un oído sano (es el efecto de polaridad de la onda I). Es lo que mide el alumno comparando una curva de cada polaridad al mismo nivel; por encima de 0,38 ms la celda le sale en rojo.">
        </label>
    </div>
    <p class="help">Cuánto ruido trae este paciente. No se declara el FSP --que es el RESULTADO y depende del nivel y de cuánto se promedie-- sino las condiciones en que se midió: a tal nivel, hicieron falta tantos barridos para que el equipo declarara respuesta. De ahí sale el ruido del paciente, y ese ruido vale para todos los demás niveles.</p>
    <div class="three-col">
        <label>Nivel de referencia (dB nHL)
            <input type="number" step="5" min="0" max="100" placeholder="el umbral" name="abr[<?= $lado ?>][nivel_referencia]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['nivel_referencia'] ?? '')) ?>" title="Vacío = el propio umbral de este oído, que es lo habitual: así el umbral declarado es el nivel donde el equipo declara respuesta en la mitad de los registros.">
        </label>
        <label>Barridos para el criterio
            <input type="number" step="100" min="100" max="8000" name="abr[<?= $lado ?>][barridos_criterio]" value="<?= htmlspecialchars((string) ($v['abr'][$lado]['barridos_criterio'] ?? '2000')) ?>" title="Barridos que hicieron falta para llegar a FSP 3,1 a ese nivel. Más barridos = paciente más ruidoso. Con la referencia vacía, 2000 deja el umbral del caso en el 50% de detección.">
        </label>
        <label>Respuesta a ese nivel
            <select name="abr[<?= $lado ?>][respuesta_en_referencia]">
                <?php foreach (['presente' => 'Presente', 'ausente' => 'Ausente'] as $rKey => $rLabel): ?>
                <option value="<?= $rKey ?>" <?= (($v['abr'][$lado]['respuesta_en_referencia'] ?? 'presente') === $rKey) ? 'selected' : '' ?>><?= $rLabel ?></option>
                <?php endforeach; ?>
            </select>
        </label>
    </div>
</div>
<?php endforeach; ?>
</div>
<div class="card">
    <strong>Vía central: latencia media y tardía</strong>
    <p class="help">Es del <strong>paciente</strong>, no de un oído: el MLR (PEALM) se registra en C3, Cz y C4 y lo que localiza es el hemisferio; el CAEP, la P300 y la MMN son de la corteza. Son otras pruebas del mismo equipo (combo <em>Test</em> del panel del alumno). Un caso guardado antes de que existiera este bloque no registra ninguna de las cuatro hasta que se guarde de nuevo. El cuadro se sortea en <a href="#" class="tab-link" data-goto-tab="armado">Armado rápido</a>; acá se ajusta a mano. De dónde sale cada número: <a href="bibliografia.php#central">Configuración &rsaquo; Bibliografía</a>.</p>
    <?php
    $cv = function (string $clave) use ($v): string {
        return htmlspecialchars((string) ($v['central'][$clave] ?? CaseBuilder::CENTRAL_DEFAULTS[$clave]));
    };
    $cLim = CaseBuilder::CENTRAL_LIMITS;
    $cOpt = function (string $clave, array $rotulos) use ($v): string {
        $actual = (string) ($v['central'][$clave] ?? CaseBuilder::CENTRAL_DEFAULTS[$clave]);
        $html = '';
        foreach (CaseBuilder::CENTRAL_OPTIONS[$clave] as $op) {
            $html .= '<option value="' . htmlspecialchars($op) . '"' . ($actual === $op ? ' selected' : '') . '>'
                . htmlspecialchars($rotulos[$op] ?? $op) . '</option>';
        }
        return $html;
    };
    ?>
    <div class="three-col">
        <label>Estado durante el registro
            <select name="central[estado]" title="Dormido o sedado, la Pa del niño puede no aparecer sin que haya lesión, y no hay P300 (no puede hacer la tarea).">
                <?= $cOpt('estado', ['despierto' => 'Despierto', 'somnoliento' => 'Somnoliento', 'dormido' => 'Dormido', 'sedado' => 'Sedado']) ?>
            </select>
        </label>
        <label>Tensión cervical (0-1)
            <input type="number" step="0.05" min="<?= $cLim['tension_cervical'][0] ?>" max="<?= $cLim['tension_cervical'][1] ?>" name="central[tension_cervical]" value="<?= $cv('tension_cervical') ?>" title="Cuánto reflejo postauricular (PAM, 12-15 ms) aparece en el MLR. Con referencia en mastoides se ve varias veces más que con el lóbulo.">
        </label>
        <label>Error al contar los raros (fracción)
            <input type="number" step="0.05" min="<?= $cLim['conteo_error'][0] ?>" max="<?= $cLim['conteo_error'][1] ?>" name="central[conteo_error]" value="<?= $cv('conteo_error') ?>" title="P300: cuánto se equivoca el paciente al contar. 0 = cuenta bien. Un conteo malo invalida la interpretación.">
        </label>
    </div>
    <p class="help"><strong>PEALM.</strong> El hemisferio comprometido pierde Na-Pa en el electrodo que tiene encima (C3 izquierdo, C4 derecho) con <em>cualquier</em> oído: es el efecto electrodo. La reducción es la fracción de Na-Pa que pierde ese electrodo (0,6 = 60 % menos); Cz pierde un tercio de eso. El efecto oído baja el Na-Pa de un oído en los tres electrodos.</p>
    <div class="three-col">
        <label>Hemisferio comprometido
            <select name="central[mlr_hemisferio]">
                <?= $cOpt('mlr_hemisferio', ['ninguno' => 'Ninguno', 'izquierdo' => 'Izquierdo (C3)', 'derecho' => 'Derecho (C4)', 'bilateral' => 'Bilateral']) ?>
            </select>
        </label>
        <label>Reducción del Na-Pa (0-1)
            <input type="number" step="0.05" min="<?= $cLim['mlr_reduccion'][0] ?>" max="<?= $cLim['mlr_reduccion'][1] ?>" name="central[mlr_reduccion]" value="<?= $cv('mlr_reduccion') ?>">
        </label>
        <label>Retardo de Pa en ese electrodo (ms)
            <input type="number" step="0.5" min="<?= $cLim['mlr_pa_retardo_ms'][0] ?>" max="<?= $cLim['mlr_pa_retardo_ms'][1] ?>" name="central[mlr_pa_retardo_ms]" value="<?= $cv('mlr_pa_retardo_ms') ?>">
        </label>
        <label>Efecto oído
            <select name="central[mlr_oido]">
                <?= $cOpt('mlr_oido', ['ninguno' => 'Ninguno', 'OD' => 'OD', 'OI' => 'OI']) ?>
            </select>
        </label>
        <label>Reducción por oído (0-1)
            <input type="number" step="0.05" min="<?= $cLim['mlr_oido_reduccion'][0] ?>" max="<?= $cLim['mlr_oido_reduccion'][1] ?>" name="central[mlr_oido_reduccion]" value="<?= $cv('mlr_oido_reduccion') ?>">
        </label>
    </div>
    <p class="help"><strong>PEALT.</strong> La latencia normal de la P1 y de la P300 la pone el cliente por edad; acá va solo cuánto se aparta este paciente. La P1 atrasada es la privación auditiva (implante tardío); la P300 atrasada con exógenos normales, el deterioro cognitivo. Sin diferencia entre el estímulo frecuente y el raro no hay P300 ni MMN: eso lo decide el equipo, no el caso.</p>
    <div class="three-col">
        <label>Retardo de la P1 (ms)
            <input type="number" step="5" min="<?= $cLim['p1_retardo_ms'][0] ?>" max="<?= $cLim['p1_retardo_ms'][1] ?>" name="central[p1_retardo_ms]" value="<?= $cv('p1_retardo_ms') ?>">
        </label>
        <label>Reducción del N1-P2 (0-1)
            <input type="number" step="0.05" min="<?= $cLim['n1p2_reduccion'][0] ?>" max="<?= $cLim['n1p2_reduccion'][1] ?>" name="central[n1p2_reduccion]" value="<?= $cv('n1p2_reduccion') ?>">
        </label>
        <label>Retardo de la P300 (ms)
            <input type="number" step="5" min="<?= $cLim['p300_retardo_ms'][0] ?>" max="<?= $cLim['p300_retardo_ms'][1] ?>" name="central[p300_retardo_ms]" value="<?= $cv('p300_retardo_ms') ?>">
        </label>
        <label>Reducción de la P300 (0-1)
            <input type="number" step="0.05" min="<?= $cLim['p300_reduccion'][0] ?>" max="<?= $cLim['p300_reduccion'][1] ?>" name="central[p300_reduccion]" value="<?= $cv('p300_reduccion') ?>">
        </label>
        <label>Reducción de la MMN (0-1)
            <input type="number" step="0.05" min="<?= $cLim['mmn_reduccion'][0] ?>" max="<?= $cLim['mmn_reduccion'][1] ?>" name="central[mmn_reduccion]" value="<?= $cv('mmn_reduccion') ?>">
        </label>
    </div>
</div>
<div class="card">
    <strong>Vista previa: serie 100&rarr;0 dBnHL</strong>
    <p class="help">Simulación simplificada (sin ruido ni promediación) de cómo se vería la serie de intensidades para este oído, según la patología y las desviaciones cargadas arriba. Se redibuja sola, en vivo, al tipear. Los marcadores verticales señalan dónde queda cada onda y la línea punteada sigue el pico a través de las intensidades (función latencia-intensidad). Es referencia visual para el docente: el generador real, con ruido, FSP y promediación, es el que corre en el equipo del alumno.</p>
    <div class="two-col">
        <div>
            <strong class="od-text">OD</strong>
            <div id="abr-preview-od" class="abr-preview"></div>
        </div>
        <div>
            <strong class="oi-text">OI</strong>
            <div id="abr-preview-oi" class="abr-preview"></div>
        </div>
    </div>
</div>
</div>
