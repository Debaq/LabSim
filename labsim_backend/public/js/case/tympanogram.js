// Timpanograma: curva estilizada según el tipo Jerger elegido en Z OD/Z OI
// -- el form solo guarda la categoría (A/As/Ad/C/Cs/B), no una curva medida.
// La forma es la MISMA que genera la app del alumno (Z_225.curve_z en
// src/impedanciometria/z_generator.py): coseno alzado a cada lado del pico,
// con pendiente cero en el ápice y en el empalme con la línea base, y ancho
// fijo de 200 daPa por lado. Compliance y presión las sortea la app dentro
// de un rango por letra; acá se dibuja el centro de ese rango. Espejo de
// CaseCharts::curvaTimpanograma / FORMAS_TIMPANOGRAMA, que dibuja lo mismo
// en el PDF de la ficha.
window.drawTympanogram = (function () {
    var NS = 'http://www.w3.org/2000/svg';

    // [compliance mín, compliance máx, presión mín, presión máx] por letra.
    var SHAPES = {
        A: [0.3, 1.6, -100, 20],
        As: [0.01, 0.3, -100, 20],
        Ad: [1.8, 4.0, -100, 20],
        C: [0.3, 1.6, -400, -100],
        Cs: [0.01, 1.3, -400, -100],
        B: [0.0, 0.003, -100, 20]
    };
    var PRESSURE_MAX = 200;       // pressure_max de Z_225: semiancho de la curva
    var NUM_PTS = 20;             // num_pts de Z_225
    var GRADIENT_DELTA = 50;      // la gradiente se lee a +-50 daPa del pico
    var HEIGHTS = [1, 2, 5, 8];   // topes del eje que ofrece el botón cc
    var GRADIENT_COLOR = '#b08900';
    var GRADIENT_FILL = '#fbf3d0';

    function values(type) {
        var s = SHAPES[type] || SHAPES.A;
        var c = Math.round((s[0] + s[1]) / 2 * 100) / 100;
        return { cMin: s[0], cMax: s[1], pMin: s[2], pMax: s[3], c: c, p: Math.round((s[2] + s[3]) / 2) };
    }

    function scale(compliances) {
        var alto = Math.max.apply(null, compliances);
        for (var i = 0; i < HEIGHTS.length; i++) {
            if (alto <= HEIGHTS[i]) { return HEIGHTS[i]; }
        }
        return HEIGHTS[HEIGHTS.length - 1];
    }

    function xPos(p) { p = Math.max(-400, Math.min(200, p)); return 32 + (p - (-400)) / 600 * 280; }
    function makeY(tope) {
        return function (c) { c = Math.max(0, Math.min(tope, c)); return 276 - c / tope * 266; };
    }

    // Curva del equipo + línea base a los costados hasta el fin de la ventana.
    function curvePoints(type) {
        var v = values(type);
        var pts = [], i, t;
        for (i = 0; i < NUM_PTS; i++) {
            t = i / (NUM_PTS - 1);
            pts.push([v.p - PRESSURE_MAX + t * PRESSURE_MAX, v.c * (0.5 - 0.5 * Math.cos(Math.PI * t))]);
        }
        for (i = 1; i < NUM_PTS; i++) {
            t = i / (NUM_PTS - 1);
            pts.push([v.p + t * PRESSURE_MAX, v.c * (0.5 + 0.5 * Math.cos(Math.PI * t))]);
        }
        var izq = [], der = [], p;
        for (p = -400; p < pts[0][0]; p += 10) { izq.push([p, 0]); }
        for (p = pts[pts.length - 1][0] + 10; p <= 200; p += 10) { der.push([p, 0]); }
        return izq.concat(pts, der);
    }

    function el(name, attrs) {
        var node = document.createElementNS(NS, name);
        Object.keys(attrs).forEach(function (k) { node.setAttribute(k, attrs[k]); });
        return node;
    }

    return function drawTympanogram() {
        var group = document.getElementById('tympanogram-data');
        if (!group) return;
        while (group.firstChild) group.removeChild(group.firstChild);

        var lados = [['z_od', window.sideColor('od')], ['z_oi', window.sideColor('oi')]].map(function (pair) {
            var node = document.getElementById(pair[0]);
            var type = node ? node.value : 'A';
            return { type: type, color: pair[1], v: values(type) };
        });

        // Escala común a los dos oídos: si uno es Ad hay que subir el eje,
        // igual que el alumno tiene que subirlo en el equipo.
        var tope = scale(lados.map(function (l) { return l.v.c; }));
        var yPos = makeY(tope);
        Array.prototype.forEach.call(document.querySelectorAll('.tymp-ytick'), function (t) {
            var frac = parseFloat(t.getAttribute('data-frac')) || 0;
            // Dos decimales sólo si el paso los necesita: con tope 1 mL las
            // divisiones caen en 0,25 y "0.3" sería un rótulo mentiroso.
            t.textContent = (tope * frac).toFixed(tope % 2 === 0 ? 1 : 2);
        });

        lados.forEach(function (lado) {
            // Ventana de la gradiente: rectángulo de 100 daPa centrado en el
            // pico y de la altura del pico. La gradiente es cuánto llena la
            // curva por los costados (ZZscreen.set_gradient_box).
            if (lado.v.c > 0) {
                var x0 = xPos(lado.v.p - GRADIENT_DELTA), x1 = xPos(lado.v.p + GRADIENT_DELTA);
                var yTop = yPos(lado.v.c);
                group.appendChild(el('rect', {
                    x: x0, y: yTop, width: x1 - x0, height: 276 - yTop,
                    fill: GRADIENT_FILL, stroke: GRADIENT_COLOR,
                    'stroke-width': '0.8', 'stroke-dasharray': '2,2'
                }));
                group.appendChild(el('line', {
                    x1: xPos(lado.v.p), y1: 10, x2: xPos(lado.v.p), y2: 276,
                    stroke: lado.color, 'stroke-width': '0.8', 'stroke-dasharray': '1.5,2'
                }));
            }

            var pts = curvePoints(lado.type).map(function (pt) { return xPos(pt[0]) + ',' + yPos(pt[1]); });
            group.appendChild(el('polyline', {
                points: pts.join(' '), fill: 'none', stroke: lado.color, 'stroke-width': '1.5'
            }));
        });
    };
})();
