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
</div>
