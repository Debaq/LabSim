// Timpanograma: curva estilizada según el tipo Jerger elegido en Z OD/Z OI
// -- el form solo guarda la categoría (A/As/Ad/C/Cs/B), no una curva medida.
// El ápice va EN PUNTA (exponencial de la distancia al pico, no gaussiana):
// así se imprime un timpanograma, con el ancho como parte del hallazgo. La
// altura y la presión del pico salen del rango que la app sortea para esa
// letra (Z_225.create_auto en src/impedanciometria/z_generator.py); se
// dibuja el centro, porque el sorteo lleva una semilla por paciente que acá
// no se puede reproducir. Mismas coordenadas (presión -400..200 daPa,
// compliance 0..2 mL) que tymp_x()/tymp_y() en PHP arriba, que dibujan la
// grilla fija de fondo, y misma forma que CaseCharts::tympanogramPoints en
// el PDF de la ficha.
window.drawTympanogram = (function () {
    var NS = 'http://www.w3.org/2000/svg';
    function xPos(p) { p = Math.max(-400, Math.min(200, p)); return 32 + (p - (-400)) / 600 * 280; }
    function yPos(c) { c = Math.max(0, Math.min(2, c)); return 276 - c / 2 * 266; }

    // [compliance mín, compliance máx, presión mín, presión máx] por letra.
    var SHAPES = {
        A: [0.3, 1.6, -100, 20],
        As: [0.01, 0.3, -100, 20],
        Ad: [1.8, 4.0, -100, 20],
        C: [0.3, 1.6, -400, -100],
        Cs: [0.01, 1.3, -400, -100],
        B: [0.0, 0.003, -100, 20]
    };
    // Ancho de la curva impresa (daPa), espejo de CaseCharts::ANCHOS_TIMPANOGRAMA.
    var WIDTHS = { A: 60, As: 50, Ad: 70, C: 70, Cs: 60, B: 400 };
    var GRADIENT_DELTA = 50;   // la gradiente se lee a +-50 daPa del pico
    var GRADIENT_COLOR = '#b08900';
    var GRADIENT_FILL = '#fbf3d0';

    function values(type) {
        var s = SHAPES[type] || SHAPES.A;
        return {
            c: Math.round((s[0] + s[1]) / 2 * 100) / 100,
            p: Math.round((s[2] + s[3]) / 2),
            width: WIDTHS[type] || WIDTHS.A
        };
    }

    function curvePoints(type) {
        var v = values(type);
        var pts = [];
        for (var p = -400; p <= 200; p += 5) {
            pts.push([p, v.c * Math.exp(-Math.abs(p - v.p) / v.width)]);
        }
        return pts;
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

        [['z_od', window.sideColor('od')], ['z_oi', window.sideColor('oi')]].forEach(function (pair) {
            var node = document.getElementById(pair[0]);
            var type = node ? node.value : 'A';
            var v = values(type);

            // Ventana de la gradiente: rectángulo de 100 daPa centrado en el
            // pico y de la altura del pico, igual que lo marca el equipo
            // (ZZscreen.set_gradient_box). La gradiente es cuánto de ese alto
            // conserva la curva en los bordes del rectángulo.
            if (v.c > 0) {
                var x0 = xPos(v.p - GRADIENT_DELTA), x1 = xPos(v.p + GRADIENT_DELTA);
                var yTop = yPos(v.c);
                group.appendChild(el('rect', {
                    x: x0, y: yTop, width: x1 - x0, height: 276 - yTop,
                    fill: GRADIENT_FILL, stroke: GRADIENT_COLOR,
                    'stroke-width': '0.8', 'stroke-dasharray': '2,2'
                }));
                group.appendChild(el('line', {
                    x1: xPos(v.p), y1: 10, x2: xPos(v.p), y2: 276,
                    stroke: pair[1], 'stroke-width': '0.8', 'stroke-dasharray': '1.5,2'
                }));
            }

            group.appendChild(el('polyline', {
                points: curvePoints(type).map(function (pt) { return xPos(pt[0]) + ',' + yPos(pt[1]); }).join(' '),
                fill: 'none', stroke: pair[1], 'stroke-width': '1.5'
            }));
        });
    };
})();
