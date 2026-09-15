// Audiograma: se redibuja solo con lo que hay en los campos de vía
// aérea/ósea/LDL -- mismas coordenadas (log de frecuencia, -10..120 dB HL)
// que audiogram_x()/audiogram_y() en PHP, que dibujan la grilla fija de
// fondo. La aérea va con línea llena, la ósea unida con PUNTOS y el LDL con
// guiones más largos, para que las dos discontinuas no se confundan (los
// mismos patrones están en CaseCharts::TRAZO_OSEA/TRAZO_LDL, que dibuja el
// PDF de la ficha). Símbolos clínicos estándar (ASHA): círculo/cruz = aérea OD/OI sin
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
    // [marca, espacio] en unidades del SVG -- espejo de CaseCharts::TRAZO_*.
    var BONE_DASH = '1,2';
    var LDL_DASH = '3,2';
    // Cuánto se corre el símbolo óseo (no la línea) de la intersección
    // frecuencia/intensidad: OD a la izquierda, OI a la derecha. Centrado,
    // un umbral óseo igual al aéreo -lo más común- queda tapado por el
    // círculo/cruz de la vía aérea en el mismo punto. Espejo de
    // CaseCharts::DESPLAZAMIENTO_OSEA.
    var BONE_OFFSET = 4;
    // Vía ósea y LDL se miden de 250 a 4000 Hz: ni 125 ni 6000/8000 se
    // prueban por vía ósea (el vibrador no entrega nivel útil ahí y la
    // vibración táctil se confunde con audición). Espejo de
    // CaseCharts::FREQS_OSEA, que recorta lo mismo en el PDF.
    var BONE_FREQS = [250, 500, 1000, 2000, 3000, 4000];
    function boneMeasured(i) { return BONE_FREQS.indexOf(FREQS[i]) !== -1; }
    // 130 no es un umbral: es "no respondió al máximo del audiómetro". Se
    // dibuja el símbolo de siempre en el máximo (120) con una flecha hacia
    // abajo, y ese punto NO se une a los demás. Mismo criterio que
    // CaseCharts::SIN_UMBRAL_DB/NIVEL_MAXIMO_DB en el PDF de la ficha.
    var NO_RESPONSE_DB = 130;
    var MAX_LEVEL_DB = 120;
    function noResponse(v) { return v >= NO_RESPONSE_DB; }
    function plotDb(v) { return noResponse(v) ? MAX_LEVEL_DB : v; }

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
    /**
     * Flecha del "no responde", en diagonal hacia afuera (OD a la izquierda,
     * OI a la derecha) para que los dos oídos no se encimen en la misma
     * frecuencia. Espejo de CaseCharts::flechaAbajo.
     */
    function makeNoResponseArrow(x, y, color, lado) {
        var g = document.createElementNS(NS, 'g');
        var largo = 7;
        var x0 = x + lado * 2.6, y0 = y + 3.4;
        var x1 = x0 + lado * largo * 0.7, y1 = y0 + largo;
        [[x0, y0, x1, y1], [x1, y1, x1 - lado * 3.4, y1 - 0.6], [x1, y1, x1 - lado * 0.6, y1 - 3.4]].forEach(function (c) {
            var l = document.createElementNS(NS, 'line');
            l.setAttribute('x1', c[0]); l.setAttribute('y1', c[1]); l.setAttribute('x2', c[2]); l.setAttribute('y2', c[3]);
            l.setAttribute('stroke', color); l.setAttribute('stroke-width', '1.1');
            g.appendChild(l);
        });
        return g;
    }

    /**
     * LDL: triángulo rectángulo con el cateto vertical mirando a la línea de
     * la frecuencia -- el OD queda a su izquierda y el OI a su derecha, con
     * una separación mínima para que no se peguen. Espejo de CaseCharts::ldl.
     */
    function makeLdlMark(x, y, color, side) {
        var lado = side === 'od' ? -1 : 1;
        var sep = 1.6, alto = 5.4, ancho = 4.6;
        var xc = x + lado * sep, xp = xc + lado * ancho;
        var t = document.createElementNS(NS, 'polygon');
        t.setAttribute('points', xc + ',' + (y - alto / 2) + ' ' + xc + ',' + (y + alto / 2) + ' ' + xp + ',' + (y + alto / 2));
        t.setAttribute('fill', color); t.setAttribute('stroke', 'none');
        return t;
    }

    return function drawAudiogram() {
        var group = document.getElementById('audiogram-data');
        if (!group) return;
        while (group.firstChild) group.removeChild(group.firstChild);

        // Une los puntos, cortando en cada frecuencia sin respuesta: un
        // umbral que no existe no puede ser extremo de un segmento.
        function drawLine(vals, color, dash, soloOsea) {
            var tramos = [], actual = [];
            vals.forEach(function (v, i) {
                if (soloOsea && !boneMeasured(i)) { return; }
                if (noResponse(v)) {
                    if (actual.length > 1) { tramos.push(actual); }
                    actual = [];
                    return;
                }
                actual.push(xPos(FREQS[i]) + ',' + yPos(v));
            });
            if (actual.length > 1) { tramos.push(actual); }
            tramos.forEach(function (puntos) {
                var poly = document.createElementNS(NS, 'polyline');
                poly.setAttribute('points', puntos.join(' '));
                poly.setAttribute('fill', 'none');
                poly.setAttribute('stroke', color);
                poly.setAttribute('stroke-width', dash ? '1' : '1.3');
                if (dash) poly.setAttribute('stroke-dasharray', dash);
                group.appendChild(poly);
            });
        }

        var aereaOd = readVals('aerea', 'od'), aereaOi = readVals('aerea', 'oi');
        var oseaOd = readVals('osea', 'od'), oseaOi = readVals('osea', 'oi');

        // Vía aérea: línea + símbolo por punto (enmascarado si el umbral
        // propio supera al óseo del oído contrario en >= la atenuación
        // interaural de esa frecuencia, ver AIR_ATTENUATION_BY_FREQ).
        drawLine(aereaOd, window.sideColor('od'));
        drawLine(aereaOi, window.sideColor('oi'));
        for (var n = 0; n < FREQS.length; n++) {
            var x = xPos(FREQS[n]);
            var yOd = yPos(plotDb(aereaOd[n])), yOi = yPos(plotDb(aereaOi[n]));
            var maskedOd = airMasked(aereaOd[n], oseaOi[n], n);
            group.appendChild((maskedOd ? makeTriangle : makeCircle)(x, yOd, window.sideColor('od')));
            if (noResponse(aereaOd[n])) { group.appendChild(makeNoResponseArrow(x, yOd, window.sideColor('od'), -1)); }
            var maskedOi = airMasked(aereaOi[n], oseaOd[n], n);
            group.appendChild((maskedOi ? makeSquare : makeCross)(x, yOi, window.sideColor('oi')));
            if (noResponse(aereaOi[n])) { group.appendChild(makeNoResponseArrow(x, yOi, window.sideColor('oi'), 1)); }
        }

        // Vía ósea: unida con línea punteada, y enmascarada si hay gap
        // aéreo-óseo >=10dB en el mismo oído. La línea se dibuja antes que
        // los corchetes para que el símbolo quede encima.
        drawLine(oseaOd, window.sideColor('od'), BONE_DASH, true);
        drawLine(oseaOi, window.sideColor('oi'), BONE_DASH, true);
        for (var m = 0; m < FREQS.length; m++) {
            if (!boneMeasured(m)) { continue; }
            var x2 = xPos(FREQS[m]);
            var yBOd = yPos(plotDb(oseaOd[m])), yBOi = yPos(plotDb(oseaOi[m]));
            // El símbolo (no la línea) se corre de la intersección: ver
            // BONE_OFFSET arriba.
            group.appendChild(makeBracket(x2 - BONE_OFFSET, yBOd, window.sideColor('od'), 'left', boneMasked(aereaOd[m], oseaOd[m])));
            if (noResponse(oseaOd[m])) { group.appendChild(makeNoResponseArrow(x2 - BONE_OFFSET, yBOd, window.sideColor('od'), -1)); }
            group.appendChild(makeBracket(x2 + BONE_OFFSET, yBOi, window.sideColor('oi'), 'right', boneMasked(aereaOi[m], oseaOi[m])));
            if (noResponse(oseaOi[m])) { group.appendChild(makeNoResponseArrow(x2 + BONE_OFFSET, yBOi, window.sideColor('oi'), 1)); }
        }

        // LDL: solo si "LDL medido" está activo para ese oído -- si no, el
        // valor que se guarda es 130 (ausente) sin importar lo escrito, así
        // que graficarlo igual sería mostrar un dato que nunca se va a guardar.
        ['od', 'oi'].forEach(function (side) {
            if (!isLdlMeasured(side)) { return; }
            var color = window.sideColor(side);
            var lado = side === 'od' ? -1 : 1;
            var vals = readVals('ldl', side);
            drawLine(vals, color, LDL_DASH, true);
            vals.forEach(function (v, i) {
                if (!boneMeasured(i)) { return; }
                var x3 = xPos(FREQS[i]), y3 = yPos(plotDb(v));
                group.appendChild(makeLdlMark(x3, y3, color, side));
                if (noResponse(v)) { group.appendChild(makeNoResponseArrow(x3, y3, color, lado)); }
            });
        });
    };
})();
