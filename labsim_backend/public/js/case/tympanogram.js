// Timpanograma: curva estilizada según el tipo Jerger elegido en Z OD/Z OI
// -- el form solo guarda la categoría (A/As/Ad/C/Cs/B), no una curva medida,
// así que se sintetiza una campana gaussiana por tipo. Mismas coordenadas
// (presión -400..200 daPa, compliance 0..2.5 mL) que tymp_x()/tymp_y() en
// PHP arriba, que dibujan la grilla fija de fondo.
window.drawTympanogram = (function () {
    var NS = 'http://www.w3.org/2000/svg';
    function xPos(p) { p = Math.max(-400, Math.min(200, p)); return 32 + (p - (-400)) / 600 * 280; }
    function yPos(c) { c = Math.max(0, Math.min(2.5, c)); return 276 - c / 2.5 * 266; }

    // [posición del pico (daPa), altura del pico (mL), ancho de la campana, línea base]
    var SHAPES = {
        A: [0, 0.8, 60, 0.1],
        As: [0, 0.3, 50, 0.1],
        Ad: [0, 1.8, 70, 0.1],
        C: [-150, 0.8, 70, 0.1],
        Cs: [-150, 0.3, 60, 0.1],
        B: [0, 0.15, 400, 0.15]
    };

    function curvePoints(type) {
        var s = SHAPES[type] || SHAPES.A;
        var peakPos = s[0], peakHeight = s[1], width = s[2], baseline = s[3];
        var pts = [];
        for (var p = -400; p <= 200; p += 10) {
            var c = baseline + (peakHeight - baseline) * Math.exp(-((p - peakPos) * (p - peakPos)) / (2 * width * width));
            pts.push([p, c]);
        }
        return pts;
    }

    return function drawTympanogram() {
        var group = document.getElementById('tympanogram-data');
        if (!group) return;
        while (group.firstChild) group.removeChild(group.firstChild);

        [['z_od', '#b33a3a'], ['z_oi', '#2255aa']].forEach(function (pair) {
            var el = document.getElementById(pair[0]);
            var pts = curvePoints(el ? el.value : 'A');
            var poly = document.createElementNS(NS, 'polyline');
            poly.setAttribute('points', pts.map(function (pt) { return xPos(pt[0]) + ',' + yPos(pt[1]); }).join(' '));
            poly.setAttribute('fill', 'none');
            poly.setAttribute('stroke', pair[1]);
            poly.setAttribute('stroke-width', '1.5');
            group.appendChild(poly);
        });
    };
})();
