// Logoaudiograma: curva % discriminación vs intensidad (dB HL), por oído.
// Mismo plot box que el audiograma pero ejes lineales (ver logogram_x()/
// logogram_y() en PHP arriba). Se dibuja REDONDEADA, como en un informe: la
// quebrada de segmentos rectos era un artefacto de unir los puntos con
// polyline. Las tangentes son las de Fritsch-Carlson (cúbica monótona), las
// mismas que CaseCharts::curvaSuave usa para el PDF -- monótona y no un
// spline cualquiera porque la curva no puede pasar de 100 % ni bajar de 0.
// Curva simplificada para vista previa en vivo
// -- no replica CalculateLogo.cal_new_umd completo (src/audiometria/
// logoaudiometry.py de la app de escritorio), pero sigue la misma forma:
// 0% en SDT, sube hasta UMD(int,%), y desde ahí meseta plana o cae si hay
// reclutamiento (rollover). SRT se marca aparte como línea vertical, ya que
// es un umbral de detección, no un punto de la curva de discriminación.
window.drawLogogram = (function () {
    var NS = 'http://www.w3.org/2000/svg';
    function logoX(db) { db = Math.max(-10, Math.min(120, db)); return 32 + (db - (-10)) / 130 * 280; }
    function logoY(pct) { pct = Math.max(0, Math.min(100, pct)); return 10 + (100 - pct) / 100 * 266; }

    function val(selector, side, def) {
        var el = document.querySelector(selector + '[data-side="' + side + '"]');
        return el ? (parseInt(el.value, 10) || 0) : def;
    }

    function makeDot(x, y, color) {
        var c = document.createElementNS(NS, 'circle');
        c.setAttribute('cx', x); c.setAttribute('cy', y); c.setAttribute('r', 3);
        c.setAttribute('fill', color); c.setAttribute('stroke', 'none');
        return c;
    }
    function makeUmdMark(x, y, color) {
        var r = 4;
        var t = document.createElementNS(NS, 'polygon');
        t.setAttribute('points', x + ',' + (y - r) + ' ' + (x - r) + ',' + (y + r * 0.8) + ' ' + (x + r) + ',' + (y + r * 0.8));
        t.setAttribute('fill', color); t.setAttribute('stroke', 'none');
        return t;
    }
    function makeSrtLine(x, color) {
        var l = document.createElementNS(NS, 'line');
        l.setAttribute('x1', x); l.setAttribute('y1', 10); l.setAttribute('x2', x); l.setAttribute('y2', 276);
        l.setAttribute('stroke', color); l.setAttribute('stroke-width', '1'); l.setAttribute('stroke-dasharray', '2,2');
        return l;
    }

    function curvePoints(side) {
        var sdt = val('.sdt-input', side, 0);
        var umdInt = val('.umd-int-input', side, 35);
        var umdPct = val('.umd-pct-input', side, 100);
        var recruitEl = document.querySelector('.recruit-toggle[data-side="' + side + '"]');
        var recruit = !!(recruitEl && recruitEl.checked);

        var pts = [[-10, 0], [sdt, 0], [umdInt, umdPct]];
        pts.push(recruit ? [120, Math.max(0, umdPct - (120 - umdInt) / 5 * 5)] : [120, umdPct]);
        // Ordenado por dB creciente -- si SDT/UMD quedan invertidos (dato mal
        // tipeado) igual se dibuja algo coherente en vez de una polyline en zigzag.
        pts.sort(function (a, b) { return a[0] - b[0]; });
        return pts;
    }

    /**
     * Puntos -> path SVG con bezier cúbicas que pasan por todos ellos.
     * Espejo de CaseCharts::curvaSuave(): mismas tangentes, misma forma.
     */
    function smoothPath(pts) {
        var limpios = [];
        pts.forEach(function (p) {
            if (!limpios.length || Math.abs(p[0] - limpios[limpios.length - 1][0]) > 1e-9) { limpios.push(p); }
        });
        var n = limpios.length;
        if (n < 2) { return ''; }

        var d = [], i;
        for (i = 0; i < n - 1; i++) {
            d[i] = (limpios[i + 1][1] - limpios[i][1]) / (limpios[i + 1][0] - limpios[i][0]);
        }
        var m = [d[0]];
        for (i = 1; i < n - 1; i++) { m[i] = (d[i - 1] + d[i]) / 2; }
        m[n - 1] = d[n - 2];

        // Monotonía tramo a tramo: anula la tangente en máximos y mínimos, que
        // es lo que redondea el rollover sin pasarse del 100 %.
        for (i = 0; i < n - 1; i++) {
            if (Math.abs(d[i]) < 1e-12) { m[i] = 0; m[i + 1] = 0; continue; }
            var a = m[i] / d[i], b = m[i + 1] / d[i];
            if (a < 0) { m[i] = 0; a = 0; }
            if (b < 0) { m[i + 1] = 0; b = 0; }
            var suma = a * a + b * b;
            if (suma > 9) {
                var t = 3 / Math.sqrt(suma);
                m[i] = t * a * d[i];
                m[i + 1] = t * b * d[i];
            }
        }

        var path = 'M ' + limpios[0][0].toFixed(2) + ' ' + limpios[0][1].toFixed(2);
        for (i = 0; i < n - 1; i++) {
            var h = limpios[i + 1][0] - limpios[i][0];
            path += ' C ' + (limpios[i][0] + h / 3).toFixed(2) + ' ' + (limpios[i][1] + m[i] * h / 3).toFixed(2)
                  + ', ' + (limpios[i + 1][0] - h / 3).toFixed(2) + ' ' + (limpios[i + 1][1] - m[i + 1] * h / 3).toFixed(2)
                  + ', ' + limpios[i + 1][0].toFixed(2) + ' ' + limpios[i + 1][1].toFixed(2);
        }
        return path;
    }

    return function drawLogogram() {
        var group = document.getElementById('logogram-data');
        if (!group) return;
        while (group.firstChild) group.removeChild(group.firstChild);

        ['od', 'oi'].forEach(function (side) {
            var color = window.sideColor(side);
            var pts = curvePoints(side).map(function (p) { return [logoX(p[0]), logoY(p[1])]; });
            var curva = document.createElementNS(NS, 'path');
            curva.setAttribute('d', smoothPath(pts));
            curva.setAttribute('fill', 'none');
            curva.setAttribute('stroke', color);
            curva.setAttribute('stroke-width', '1.3');
            group.appendChild(curva);

            var sdt = val('.sdt-input', side, 0);
            var srt = val('.srt-input', side, 0);
            var umdInt = val('.umd-int-input', side, 35);
            var umdPct = val('.umd-pct-input', side, 100);
            group.appendChild(makeSrtLine(logoX(srt), color));
            group.appendChild(makeDot(logoX(sdt), logoY(0), color));
            group.appendChild(makeUmdMark(logoX(umdInt), logoY(umdPct), color));
        });
    };
})();
