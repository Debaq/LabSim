// Logoaudiograma: curva % discriminación vs intensidad (dB HL), por oído.
// Mismo plot box que el audiograma pero ejes lineales (ver logogram_x()/
// logogram_y() en PHP arriba). Se dibuja REDONDEADA, como en un informe: la
// quebrada de segmentos rectos era un artefacto de unir los puntos con
// polyline. Las tangentes son las de Fritsch-Carlson (cúbica monótona), las
// mismas que CaseCharts::curvaSuave usa para el PDF -- monótona y no un
// spline cualquiera porque la curva no puede pasar de 100 % ni bajar de 0.
//
// La curva es pctLogo(): la MISMA función que CaseCharts::pctLogo (PDF) y
// src/audiometria/logo_curva.py (lo que mide el alumno en la app). El SRT
// del caso es donde pasa la mitad de su máximo, llega al máximo en la UMD y
// de ahí meseta, o rollover si el perfil le da RI > 0 (componente
// retrococlear, CaseProfile::rolloverIndex; el RI llega con la proyección
// del perfil en window.LOGO_RI, ver profile-preview.js). Si cambia algo
// acá, cambia en los otros dos: tests/test_charts_vs_js.php corre esta
// función con node y la compara con la del PHP.
// SRT se marca aparte como línea vertical, ya que es un umbral, no un punto
// de la curva de discriminación.
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

    // Constantes de la curva: las mismas de CaseCharts (LOGO_*).
    var LOGO_PIE_DB = 10;
    var LOGO_PENDIENTE = 0.05;
    var LOGO_ROLL_DB = 25;
    var LOGO_TECHO_DB = 100;

    /** % de palabras a `db` dB HL. Espejo exacto de CaseCharts::pctLogo. */
    function pctLogo(cfg, db) {
        var pmax = Math.max(0, Math.min(100, cfg.umd_pct));
        if (pmax <= 0) { return 0; }
        var lmax = cfg.umd_int;
        var l50 = Math.min(cfg.srt, lmax - 5);
        var lon = Math.min(cfg.sdt, l50 - LOGO_PIE_DB);
        var hA = l50 - lon, hB = lmax - l50;
        var k = Math.min(LOGO_PENDIENTE, 1.5 / hA, 1.5 / hB);
        var s, t;
        if (db <= lon) {
            s = 0;
        } else if (db <= l50) {
            t = (db - lon) / hA;
            s = 0.5 * (3 * t * t - 2 * t * t * t) + hA * k * (t * t * t - t * t);
        } else if (db <= lmax) {
            t = (db - l50) / hB;
            s = 0.5 * (2 * t * t * t - 3 * t * t + 1) + hB * k * (t * t * t - 2 * t * t + t)
                + (3 * t * t - 2 * t * t * t);
        } else {
            s = 1;
            var ri = Math.max(0, Math.min(1, cfg.ri || 0));
            var ltop = Math.min(lmax + LOGO_ROLL_DB, LOGO_TECHO_DB);
            if (ri > 0 && ltop > lmax) {
                t = Math.min(1, (db - lmax) / (ltop - lmax));
                s = 1 - ri * (3 * t * t - 2 * t * t * t);
            }
        }
        return pmax * Math.max(0, Math.min(1, s));
    }

    function cfgDe(side) {
        var ri = (window.LOGO_RI && window.LOGO_RI[side]) || 0;
        return {
            sdt: val('.sdt-input', side, 0),
            srt: val('.srt-input', side, 0),
            umd_int: val('.umd-int-input', side, 35),
            umd_pct: val('.umd-pct-input', side, 100),
            ri: ri
        };
    }

    // Muestreada cada 1 dB, como CaseCharts::logogramPoints().
    function curvePoints(side) {
        var cfg = cfgDe(side);
        var pts = [];
        for (var db = -10; db <= 120; db++) { pts.push([db, pctLogo(cfg, db)]); }
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

    function drawLogogram() {
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
    }
    // Expuesta para tests/test_charts_vs_js.php (la corre con node).
    drawLogogram.pctLogo = pctLogo;
    return drawLogogram;
})();
