// Audiograma: se redibuja solo con lo que hay en los campos de vía
// aérea/ósea/LDL -- mismas coordenadas (log de frecuencia, -10..120 dB HL)
// que audiogram_x()/audiogram_y() en PHP, que dibujan la grilla fija de
// fondo. Símbolos clínicos estándar (ASHA): círculo/cruz = aérea OD/OI sin
// enmascarar, triángulo/cuadrado = aérea OD/OI enmascarada; "<"/">" = ósea
// OD/OI sin enmascarar, "["/"]" = ósea OD/OI enmascarada; triángulo relleno
// = LDL. El enmascaramiento no se tipea a mano: se infiere solo de la
// atenuación interaural (ver reglas en airMasked/boneMasked abajo), mismo
// criterio que enseña Katz, Handbook of Clinical Audiology (ver también
// CaseBuilder::earVolume, que cita la misma fuente).
window.drawAudiogram = (function () {
    var NS = 'http://www.w3.org/2000/svg';
    var MIN_LOG = Math.log(125) / Math.LN2;
    var MAX_LOG = Math.log(8000) / Math.LN2;
    var FREQS = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000];
    // Reglas de enmascaramiento (simplificadas, uso docente): aérea se
    // enmascara si el umbral propio supera al óseo del oído contralateral
    // en >= la atenuación interaural de ESA frecuencia (misma tabla que
    // ResponseAudiometry.attenuations en src/audiometria/response.py de la
    // app de escritorio -- ahí simula qué tan bien el auricular aísla al
    // oído contrario). Ósea se enmascara si hay gap aéreo-óseo del MISMO
    // oído >= 10 dB (la atenuación interaural ósea es prácticamente 0).
    var AIR_ATTENUATION_BY_FREQ = [35, 40, 40, 40, 40, 45, 45, 50, 50];
    var BONE_MASKING_GAP = 10;

    function xPos(freq) { return 32 + (Math.log(freq) / Math.LN2 - MIN_LOG) / (MAX_LOG - MIN_LOG) * 280; }
    function yPos(db) {
        db = Math.max(-10, Math.min(120, db));
        return 10 + (db - (-10)) / 130 * 266;
    }
    function readVals(key, side) {
        var vals = [];
        for (var n = 0; n < FREQS.length; n++) {
            var el = document.getElementById(key + '_' + side + '_' + n);
            vals.push(el ? (parseInt(el.value, 10) || 0) : 0);
        }
        return vals;
    }
    function isLdlMeasured(side) {
        var t = document.querySelector('.ldl-toggle[data-side="' + side + '"]');
        return !t || t.checked;
    }
    function airMasked(acSelf, bcOther, freqIndex) { return (acSelf - bcOther) >= AIR_ATTENUATION_BY_FREQ[freqIndex]; }
    function boneMasked(acSelf, bcSelf) { return (acSelf - bcSelf) >= BONE_MASKING_GAP; }

    function makeCross(x, y, color) {
        var g = document.createElementNS(NS, 'g');
        var r = 4.5;
        [[x - r, y - r, x + r, y + r], [x - r, y + r, x + r, y - r]].forEach(function (c) {
            var l = document.createElementNS(NS, 'line');
            l.setAttribute('x1', c[0]); l.setAttribute('y1', c[1]); l.setAttribute('x2', c[2]); l.setAttribute('y2', c[3]);
            l.setAttribute('stroke', color); l.setAttribute('stroke-width', '1.5');
            g.appendChild(l);
        });
        return g;
    }
    function makeCircle(x, y, color) {
        var c = document.createElementNS(NS, 'circle');
        c.setAttribute('cx', x); c.setAttribute('cy', y); c.setAttribute('r', 4.5);
        c.setAttribute('fill', 'none'); c.setAttribute('stroke', color); c.setAttribute('stroke-width', '1.5');
        return c;
    }
    function makeTriangle(x, y, color) {
        var r = 5;
        var t = document.createElementNS(NS, 'polygon');
        t.setAttribute('points', x + ',' + (y - r) + ' ' + (x - r) + ',' + (y + r * 0.8) + ' ' + (x + r) + ',' + (y + r * 0.8));
        t.setAttribute('fill', 'none'); t.setAttribute('stroke', color); t.setAttribute('stroke-width', '1.5');
        return t;
    }
    function makeSquare(x, y, color) {
        var r = 4;
        var rect = document.createElementNS(NS, 'rect');
        rect.setAttribute('x', x - r); rect.setAttribute('y', y - r);
        rect.setAttribute('width', 2 * r); rect.setAttribute('height', 2 * r);
        rect.setAttribute('fill', 'none'); rect.setAttribute('stroke', color); rect.setAttribute('stroke-width', '1.5');
        return rect;
    }
    /** "<"/">" sin enmascarar, "["/"]" enmascarado -- mismo trazo, distinto cierre del ángulo. */
    function makeBracket(x, y, color, dir, masked) {
        var r = 4.5;
        var pts;
        if (!masked) {
            pts = dir === 'left'
                ? (x + r) + ',' + (y - r) + ' ' + (x - r) + ',' + y + ' ' + (x + r) + ',' + (y + r)
                : (x - r) + ',' + (y - r) + ' ' + (x + r) + ',' + y + ' ' + (x - r) + ',' + (y + r);
        } else {
            pts = dir === 'left'
                ? (x + r * 0.6) + ',' + (y - r) + ' ' + (x - r) + ',' + (y - r) + ' ' + (x - r) + ',' + (y + r) + ' ' + (x + r * 0.6) + ',' + (y + r)
                : (x - r * 0.6) + ',' + (y - r) + ' ' + (x + r) + ',' + (y - r) + ' ' + (x + r) + ',' + (y + r) + ' ' + (x - r * 0.6) + ',' + (y + r);
        }
        var p = document.createElementNS(NS, 'polyline');
        p.setAttribute('points', pts);
        p.setAttribute('fill', 'none'); p.setAttribute('stroke', color); p.setAttribute('stroke-width', '1.5');
        return p;
    }
    function makeLdlMark(x, y, color) {
        var r = 4;
        var t = document.createElementNS(NS, 'polygon');
        t.setAttribute('points', (x - r) + ',' + (y - r * 0.6) + ' ' + (x + r) + ',' + (y - r * 0.6) + ' ' + x + ',' + (y + r * 0.7));
        t.setAttribute('fill', color); t.setAttribute('stroke', 'none');
        return t;
    }

    return function drawAudiogram() {
        var group = document.getElementById('audiogram-data');
        if (!group) return;
        while (group.firstChild) group.removeChild(group.firstChild);

        function drawLine(vals, color, dashed) {
            var poly = document.createElementNS(NS, 'polyline');
            poly.setAttribute('points', vals.map(function (v, i) { return xPos(FREQS[i]) + ',' + yPos(v); }).join(' '));
            poly.setAttribute('fill', 'none');
            poly.setAttribute('stroke', color);
            poly.setAttribute('stroke-width', dashed ? '1' : '1.3');
            if (dashed) poly.setAttribute('stroke-dasharray', '2,2');
            group.appendChild(poly);
        }

        var aereaOd = readVals('aerea', 'od'), aereaOi = readVals('aerea', 'oi');
        var oseaOd = readVals('osea', 'od'), oseaOi = readVals('osea', 'oi');

        // Vía aérea: línea + símbolo por punto (enmascarado si el umbral
        // propio supera al óseo del oído contrario en >= la atenuación
        // interaural de esa frecuencia, ver AIR_ATTENUATION_BY_FREQ).
        drawLine(aereaOd, '#b33a3a');
        drawLine(aereaOi, '#2255aa');
        for (var n = 0; n < FREQS.length; n++) {
            var x = xPos(FREQS[n]);
            var maskedOd = airMasked(aereaOd[n], oseaOi[n], n);
            group.appendChild((maskedOd ? makeTriangle : makeCircle)(x, yPos(aereaOd[n]), '#b33a3a'));
            var maskedOi = airMasked(aereaOi[n], oseaOd[n], n);
            group.appendChild((maskedOi ? makeSquare : makeCross)(x, yPos(aereaOi[n]), '#2255aa'));
        }

        // Vía ósea: sin línea (convención estándar), enmascarada si hay gap
        // aéreo-óseo >=10dB en el mismo oído.
        for (var m = 0; m < FREQS.length; m++) {
            var x2 = xPos(FREQS[m]);
            group.appendChild(makeBracket(x2, yPos(oseaOd[m]), '#b33a3a', 'left', boneMasked(aereaOd[m], oseaOd[m])));
            group.appendChild(makeBracket(x2, yPos(oseaOi[m]), '#2255aa', 'right', boneMasked(aereaOi[m], oseaOi[m])));
        }

        // LDL: solo si "LDL medido" está activo para ese oído -- si no, el
        // valor que se guarda es 130 (ausente) sin importar lo escrito, así
        // que graficarlo igual sería mostrar un dato que nunca se va a guardar.
        if (isLdlMeasured('od')) {
            var ldlOd = readVals('ldl', 'od');
            drawLine(ldlOd, '#b33a3a', true);
            ldlOd.forEach(function (v, i) { group.appendChild(makeLdlMark(xPos(FREQS[i]), yPos(v), '#b33a3a')); });
        }
        if (isLdlMeasured('oi')) {
            var ldlOi = readVals('ldl', 'oi');
            drawLine(ldlOi, '#2255aa', true);
            ldlOi.forEach(function (v, i) { group.appendChild(makeLdlMark(xPos(FREQS[i]), yPos(v), '#2255aa')); });
        }
    };
})();
