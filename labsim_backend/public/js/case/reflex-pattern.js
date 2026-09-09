// Patrón de reflejos: tabla espejada (ipsi al centro, contra afuera), una
// celda +/- por frecuencia/modo/oído, leída en vivo de los campos
// reflex_ipsi/reflex_contra -- presente (valor != 130) rellena con gris
// oscuro fijo; el color del "+" marca el oído que recibió el estímulo: en
// ipsi coincide con la columna (OD=rojo, OI=azul), en contra es el
// cruzado (columna OD con estímulo en OI=azul, columna OI con estímulo en
// OD=rojo). Ausente (130) queda vacía.
window.drawReflexPattern = function drawReflexPattern() {
    document.querySelectorAll('.reflex-cell[data-mode]').forEach(function (cell) {
        var mode = cell.dataset.mode, side = cell.dataset.side, n = cell.dataset.n;
        var el = document.getElementById('reflex_' + mode + '_' + side + '_' + n);
        var val = el ? (parseInt(el.value, 10) || 0) : 130;
        var present = val < 130;
        var stimulusSide = mode === 'ipsi' ? side : (side === 'od' ? 'oi' : 'od');
        cell.textContent = present ? '+' : String.fromCharCode(8722);
        cell.classList.toggle('present', present);
        cell.classList.toggle('mark-od', present && stimulusSide === 'od');
        cell.classList.toggle('mark-oi', present && stimulusSide === 'oi');
    });
};

(function () {
    var form = document.getElementById('case-form');
    if (!form) return;
    // Delegado: cubre tipeo directo en vía aérea/ósea/LDL. El caso de
    // "igualar" (que escribe osea.value por JS sin evento input) se cubre
    // aparte, llamando drawAudiogram() desde syncOsea() más abajo.
    form.addEventListener('input', function (e) {
        if (e.target.id && /^(aerea|osea|ldl)_/.test(e.target.id)) window.drawAudiogram();
        if (e.target.classList && (e.target.classList.contains('sdt-input') || e.target.classList.contains('srt-input')
            || e.target.classList.contains('umd-int-input') || e.target.classList.contains('umd-pct-input'))) window.drawLogogram();
        if (e.target.id && /^reflex_/.test(e.target.id)) window.drawReflexPattern();
    });
    // El toggle "LDL medido" decide si esa serie se grafica o no, no solo
    // un valor -- necesita su propio listener aparte del 'input' de arriba.
    form.addEventListener('change', function (e) {
        if (e.target.classList && e.target.classList.contains('ldl-toggle')) window.drawAudiogram();
        if (e.target.classList && e.target.classList.contains('recruit-toggle')) window.drawLogogram();
        if (e.target.id === 'z_od' || e.target.id === 'z_oi') window.drawTympanogram();
    });
    window.drawAudiogram();
    window.drawLogogram();
    window.drawTympanogram();
    window.drawReflexPattern();
})();
