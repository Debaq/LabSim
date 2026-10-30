<?php
/**
 * Ficha Nariz -- el paciente de RinoSim para los equipos nasales.
 *
 * Demo interna: la dibuja admin/case_create.php solo con permission 777
 * (CaseReview::TABS la marca `solo_admin`). No es revisable: no entra en el
 * Resumen ni bloquea el guardado.
 *
 * Vive fuera de public/ a propósito (ver las otras fichas). Incluido por
 * admin/case_create.php, que comparte su scope: espera $v. El estado entero
 * vive en el hidden #nasal-json (name="nasal_json") que case_create.php pone
 * en el formulario para todos; public/js/case/nariz.js lo mantiene al día y
 * dibuja la tabla de parámetros dentro de #nariz-parametros.
 *
 * La tarjeta Pulmón es la espirometría (cases.data['ESPIRO']): su estado
 * vive en el hidden #espiro-json y lo mantiene public/js/case/pulmon.js.
 */
?>
<div class="tab-panel" data-tab="nariz">
<div class="card">
    <strong>Nariz (equipos nasales)</strong>
    <p class="help">Demo interna: solo la ve el administrador. Sin la casilla, el caso se guarda sin nariz y los equipos nasales (rinoscopía, rinomanometría y rinometría acústica) no tienen nariz que mirar ni medir. Con ella, el paciente lleva los números de abajo: el equipo simulado calcula la curva de cada fosa y dibuja lo que se ve por el espéculo a partir de ellos.</p>
    <label class="inline-check" style="margin-left:0;">
        <input type="checkbox" id="nariz-presente">
        El paciente trae nariz para los equipos nasales
    </label>
    <div id="nariz-campos">
    <p class="help">Un cuadro de ejemplo es un punto de partida: carga todos los números de una vez. "Otra variante" corre cada número un poco (hay 8 precalculadas por cuadro, rotan en orden); "Cuadro tal cual" vuelve a los números base del cuadro. Después se puede tocar cualquier valor, y el nombre pasa a "(editado)".</p>
    <div class="two-col">
        <label>Cuadro de ejemplo
            <select id="nariz-cuadro"></select>
        </label>
        <div>
            <button type="button" id="nariz-variante" class="secondary">Otra variante de este cuadro</button>
            <button type="button" id="nariz-tal-cual" class="secondary">Cuadro tal cual</button>
        </div>
    </div>
    <p class="help" id="nariz-descripcion"></p>
    <p class="help"><strong>Paciente:</strong> <span id="nariz-nombre"></span></p>
    <p class="help">FND es la fosa nasal derecha y FNI la izquierda. Narina, válvula, cornete, desviación, meato y pólipos son las áreas de la sección de cada fosa a lo largo de la nariz (distancias desde la narina); la congestión es cuánto de la mucosa del cornete está hinchada (el vasoconstrictor la lleva a cero). El colapso de la válvula es cuánto se cierra al inspirar fuerte. El ciclo nasal oscila la congestión de las dos fosas en contrafase, con ese periodo. La perforación septal pone un área de comunicación entre las fosas a esa distancia; con área 0 no hay perforación. Mucosa y secreción solo cambian lo que se ve en la rinoscopía (no las curvas): el color de la mucosa de toda la fosa y la secreción en el piso y el meato medio.</p>
    <div id="nariz-parametros"></div>
    </div>
</div>
<div class="card">
    <strong>Pulmón (espirometría)</strong>
    <p class="help">Demo interna, como la nariz. Sin la casilla, el caso se guarda sin pulmón y el espirómetro no mide. Con ella, el espirómetro simulado usa estos números como la maniobra perfecta del paciente: lo que mide el alumno sale de ellos más la variabilidad entre maniobras, el esfuerzo del paciente y lo que el alumno hace.</p>
    <label class="inline-check" style="margin-left:0;">
        <input type="checkbox" id="pulmon-presente">
        El paciente trae espirometría
    </label>
    <div id="pulmon-campos">
    <p class="help">Un cuadro de partida carga los números como fracción de los previstos GLI-2012 (grupo caucásico) del sexo y la edad de la ficha Paciente y de la talla de abajo; el PEF, que GLI no trae, se calcula como el doble del FEV1 previsto. Después se puede tocar cualquier valor.</p>
    <div class="two-col">
        <label>Cuadro de partida
            <select id="pulmon-cuadro"></select>
        </label>
        <div><button type="button" id="pulmon-cargar" class="secondary">Cargar el cuadro</button></div>
    </div>
    <div class="two-col">
        <label>Talla (cm) <input type="number" id="pulmon-talla" step="1"></label>
        <label>Peso (kg) <input type="number" id="pulmon-peso" step="1"></label>
    </div>
    <p class="help">Antes del broncodilatador y con su efecto pleno: FVC y FEV1 en litros, PEF en L/s. Con los valores "con broncodilatador" vacíos, el broncodilatador no cambia nada. El efecto llega de a poco: al cumplirse la espera del fármaco (15 minutos el salbutamol, 30 el ipratropio) está en 95 %.</p>
    <table class="pulmon-tabla">
        <tr><th></th><th>FVC (L)</th><th>FEV1 (L)</th><th>PEF (L/s)</th></tr>
        <tr><td class="side-label">Antes</td>
            <td><input type="number" id="pulmon-pre-fvc" step="0.01"></td>
            <td><input type="number" id="pulmon-pre-fev1" step="0.01"></td>
            <td><input type="number" id="pulmon-pre-pef" step="0.1"></td></tr>
        <tr><td class="side-label">Con broncodilatador</td>
            <td><input type="number" id="pulmon-bd-fvc" step="0.01"></td>
            <td><input type="number" id="pulmon-bd-fev1" step="0.01"></td>
            <td><input type="number" id="pulmon-bd-pef" step="0.1"></td></tr>
    </table>
    <p class="help">Tope de flujo de una obstrucción de la vía aérea superior, en L/s: el flujo no pasa de ese valor. Espiratorio e inspiratorio a la vez es la obstrucción fija; uno solo, la variable. Vacío, sin tope. La colaboración cambia el esfuerzo del paciente, cuánto sigue soplando sin que lo animen y cada cuánto comete un error por su cuenta (tos, inicio lento, no llenar los pulmones).</p>
    <div class="two-col">
        <label>Tope espiratorio (L/s) <input type="number" id="pulmon-tope-e" step="0.1"></label>
        <label>Tope inspiratorio (L/s) <input type="number" id="pulmon-tope-i" step="0.1"></label>
    </div>
    <label>Colaboración
        <select id="pulmon-colaboracion">
            <option value="buena">Buena</option>
            <option value="regular">Regular</option>
            <option value="mala">Mala</option>
        </select>
    </label>
    <p class="help" id="pulmon-previstos"></p>
    </div>
</div>
</div>
