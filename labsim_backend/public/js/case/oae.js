// Tab EOA: autocompletado del perfil por patología + vista previa
// (DP-grama y SNR por banda TEOAE).
//
// Los normativos replicados acá son los defaults bundled del cliente
// (resources/oae/normative_data.json). Si se tocan allá, tocar acá: esta
// vista es referencia visual para el docente, el examen real lo genera el
// cliente -- que además puede tener el normativo overrideado por curso
// (app_config normative_data.teoae/dpoae/soae/sfoae).
(function () {
    var EOAS_FREQS = window.CASE_CONST.eoasFreqs;
    var EOAS_SHAPES = window.CASE_CONST.eoasShapes;
    var EOAS_GRADES = window.CASE_CONST.eoasGrades;
    var EOAS_JITTER = window.CASE_CONST.eoasJitter;
    var EOAS_MAX_ATTEN = window.CASE_CONST.eoasMaxAtten;
    var DP = {
        f2List: [1000, 1500, 2000, 3000, 4000, 6000, 8000],
        peakF2: 3000, peakDb: 12, rollLow: 4, rollHigh: 7,
        nfDb: -22, nfLfRise: 8, minSnr: 6, passMin: 4,
        band: {
            '1000': [-5, 13], '1500': [-3, 15], '2000': [-1, 16], '3000': [0, 17],
            '4000': [-1, 16], '6000': [-4, 13], '8000': [-8, 9]
        }
    };
    var TE = {
        bands: [1000, 1500, 2000, 3000, 4000],
        expected: { '1000': 8, '1500': 10, '2000': 12, '3000': 11, '4000': 9 },
        nfSweepDb: 14, nSweeps: 260, minSnr: 6, passMin: 3
    };

    function numField(lado, field) {
        return document.querySelector('[name="eoas[' + lado + '][' + field + ']"]');
    }
    function numVal(lado, field, fallback) {
        var el = numField(lado, field);
        if (!el) { return fallback; }
        var n = parseFloat(el.value);
        return isNaN(n) ? fallback : n;
    }
    function typeVal(lado) {
        var el = document.querySelector('[name="eoas[' + lado + '][type]"]');
        return el ? el.value : 'normal';
    }
    function desvInput(lado, hz) {
        return document.querySelector('[name="eoas[' + lado + '][desv][' + hz + ']"]');
    }

    // Mismo criterio que oae_attenuation_db() en src/oae/generators/base.py
    // (1.2 dB/dB sobre 15 dB HL en coclear, 2 sobre 8 en transmisión, con
    // tope EOAS_MAX_PATHOLOGY_ATTEN_DB). Si se toca allá, tocar acá.
    function pathologyAtten(type, umbral) {
        if (type === 'coclear') { return Math.min(Math.max(0, umbral - 15) * 1.2, EOAS_MAX_ATTEN); }
        if (type === 'transmission') { return Math.min(Math.max(0, umbral - 8) * 2, EOAS_MAX_ATTEN); }
        return 0;
    }

    // Pérdida de sello = pérdida de nivel de estímulo en el conducto, y por
    // lo tanto de emisión (20*log10 del fit, igual que probe_check.py).
    function selloLossDb(lado) {
        var fit = Math.min(100, Math.max(5, numVal(lado, 'sello_pct', 85))) / 100;
        return -20 * Math.log(fit) / Math.LN10;
    }

    // Desviación por frecuencia, interpolada en log2 sobre el perfil que
    // cargó el docente (mismo interp que usa el cliente).
    function desvAt(lado, freq) {
        var xs = [], ys = [];
        for (var i = 0; i < EOAS_FREQS.length; i++) {
            var el = desvInput(lado, EOAS_FREQS[i]);
            var val = el ? parseFloat(el.value) : 0;
            xs.push(Math.log(EOAS_FREQS[i]) / Math.LN2);
            ys.push(isNaN(val) ? 0 : val);
        }
        var lf = Math.log(freq) / Math.LN2;
        if (lf <= xs[0]) { return ys[0]; }
        if (lf >= xs[xs.length - 1]) { return ys[ys.length - 1]; }
        for (var k = 1; k < xs.length; k++) {
            if (lf <= xs[k]) {
                var t = (lf - xs[k - 1]) / (xs[k] - xs[k - 1]);
                return ys[k - 1] + t * (ys[k] - ys[k - 1]);
            }
        }
        return 0;
    }

    function totalAtten(lado, freq) {
        return pathologyAtten(typeVal(lado), numVal(lado, 'umbral', 20))
            + numVal(lado, 'atten_db', 0)
            + selloLossDb(lado)
            + desvAt(lado, freq);
    }

    function dpNoiseFloor(lado, f2) {
        var lf = Math.log(2000 / f2) / Math.LN2;
        return DP.nfDb + DP.nfLfRise * Math.max(0, lf) + numVal(lado, 'ruido_db', 0);
    }

    function dpLevel(lado, f2) {
        var oct = Math.log(f2 / DP.peakF2) / Math.LN2;
        var roll = oct > 0 ? DP.rollHigh : DP.rollLow;
        return DP.peakDb - Math.abs(oct) * roll - totalAtten(lado, f2);
    }

    // SNR por banda TEOAE. El piso baja 10*log10(N) al promediar N barridos.
    function teoaeSnr(lado, band) {
        var nf = TE.nfSweepDb - 10 * Math.log(TE.nSweeps) / Math.LN10
            + numVal(lado, 'ruido_db', 0);
        var resp = TE.expected[String(band)] - totalAtten(lado, band);
        return resp - nf;
    }

    function eoasRand(min, max) { return min + Math.random() * (max - min); }

    function gradesFor(type) {
        return EOAS_GRADES[type] || EOAS_GRADES['normal'];
    }

    // Grado elegido en el select del oído; "random" (o un valor que ya no
    // exista para esa patología) sortea entre los grados de la patología.
    function pickGrade(lado) {
        var grades = gradesFor(typeVal(lado));
        var sel = document.querySelector('[name="eoas_grade[' + lado + ']"]');
        var key = sel ? sel.value : 'random';
        for (var i = 0; i < grades.length; i++) {
            if (grades[i].key === key) { return grades[i]; }
        }
        return grades[Math.floor(Math.random() * grades.length)];
    }

    // Rellena el select de grado con los grados de la patología actual.
    // Se llama al cargar y cada vez que cambia la patología del oído.
    function syncGradeOptions(lado) {
        var sel = document.querySelector('[name="eoas_grade[' + lado + ']"]');
        if (!sel) { return; }
        var grades = gradesFor(typeVal(lado));
        var previo = sel.value;
        var html = '<option value="random">Cualquiera (al azar)</option>';
        for (var i = 0; i < grades.length; i++) {
            html += '<option value="' + grades[i].key + '">' + grades[i].label + '</option>';
        }
        sel.innerHTML = html;
        sel.value = 'random';
        for (var j = 0; j < grades.length; j++) {
            if (grades[j].key === previo) { sel.value = previo; }
        }
    }

    function setNumField(lado, field, value, decimals) {
        var el = numField(lado, field);
        if (el) { el.value = decimals ? value.toFixed(decimals) : String(Math.round(value)); }
    }

    // "Autocompletar": sortea un caso plausible del grado elegido -- umbral,
    // perfil por frecuencia y condiciones de registro. Antes solo escribía
    // desviaciones fijas y dejaba el umbral en 20, así que un "coclear"
    // recién creado no se distinguía de un normal en ninguna de las cuatro
    // pruebas. Es un punto de partida al azar, editable campo a campo.
    function autofillEoas(lado) {
        var type = typeVal(lado);
        var grade = pickGrade(lado);
        var shape = EOAS_SHAPES[type] || EOAS_SHAPES['normal'];
        var scale = eoasRand(grade.scale[0], grade.scale[1]);
        setNumField(lado, 'umbral', eoasRand(grade.umbral[0], grade.umbral[1]));
        for (var i = 0; i < EOAS_FREQS.length; i++) {
            var hz = EOAS_FREQS[i];
            var el = desvInput(lado, hz);
            if (!el) { continue; }
            var base = shape[String(hz)] !== undefined ? shape[String(hz)] : 0;
            var jitter = eoasRand(-EOAS_JITTER, EOAS_JITTER);
            el.value = Math.max(0, base * scale + jitter).toFixed(1);
        }
        // Condiciones de registro: son las que hacen que dos pacientes con
        // la misma cóclea no den la misma pantalla.
        setNumField(lado, 'ruido_db', eoasRand(grade.ruido[0], grade.ruido[1]), 1);
        setNumField(lado, 'sello_pct', eoasRand(grade.sello[0], grade.sello[1]));
        setNumField(lado, 'variabilidad_db', eoasRand(1.5, 3.5), 1);
        drawEoaPreview();
    }

    function renderEoaSide(lado, color) {
        var container = document.getElementById('eoa-preview-' + lado);
        if (!container) { return; }

        var W = 400, marginLeft = 26, marginRight = 6;
        var plotW = W - marginLeft - marginRight;
        var dpTop = 12, dpH = 92, gap = 26, barH = 60;
        var H = dpTop + dpH + gap + barH + 26;
        // Eje Y del DP-grama: -30..25 dB SPL (cubre el piso de ruido en
        // graves y el techo del área normal).
        var yMin = -30, yMax = 25;
        function yDp(db) { return dpTop + dpH * (1 - (Math.max(yMin, Math.min(yMax, db)) - yMin) / (yMax - yMin)); }
        var lf0 = Math.log(DP.f2List[0]) / Math.LN2;
        var lf1 = Math.log(DP.f2List[DP.f2List.length - 1]) / Math.LN2;
        function xF2(f2) { return marginLeft + plotW * ((Math.log(f2) / Math.LN2 - lf0) / (lf1 - lf0)); }

        var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" xmlns="http://www.w3.org/2000/svg">';

        // Área normal (p5-p95 del nivel DP por f2).
        var top = [], bot = [];
        DP.f2List.forEach(function (f2) {
            var b = DP.band[String(f2)];
            top.push(xF2(f2).toFixed(1) + ',' + yDp(b[1]).toFixed(1));
            bot.unshift(xF2(f2).toFixed(1) + ',' + yDp(b[0]).toFixed(1));
        });
        svg += '<polygon points="' + top.concat(bot).join(' ') + '" fill="#2e9e5b" fill-opacity="0.13"></polygon>';

        // Grilla + etiquetas de dB.
        [-20, 0, 20].forEach(function (db) {
            svg += '<line x1="' + marginLeft + '" y1="' + yDp(db) + '" x2="' + (W - marginRight) + '" y2="' + yDp(db) + '" stroke="#000" stroke-opacity="0.08"></line>';
            svg += '<text x="' + (marginLeft - 3) + '" y="' + (yDp(db) + 2) + '" font-size="6" text-anchor="end" fill="currentColor">' + db + '</text>';
        });

        // Curva DP + piso de ruido + puntos PASS/REFER.
        var dpPts = [], nfPts = [], marks = '';
        DP.f2List.forEach(function (f2) {
            var dp = dpLevel(lado, f2), nf = dpNoiseFloor(lado, f2);
            dpPts.push(xF2(f2).toFixed(1) + ',' + yDp(dp).toFixed(1));
            nfPts.push(xF2(f2).toFixed(1) + ',' + yDp(nf).toFixed(1));
            var pass = (dp - nf) >= DP.minSnr;
            marks += '<circle cx="' + xF2(f2).toFixed(1) + '" cy="' + yDp(dp).toFixed(1) + '" r="2.2" fill="' +
                (pass ? color : '#ffffff') + '" stroke="' + color + '" stroke-width="0.8"></circle>';
        });
        svg += '<polyline points="' + nfPts.join(' ') + '" fill="none" stroke="#888" stroke-width="0.8" stroke-dasharray="3 2"></polyline>';
        svg += '<polyline points="' + dpPts.join(' ') + '" fill="none" stroke="' + color + '" stroke-width="1.2"></polyline>';
        svg += marks;
        DP.f2List.forEach(function (f2) {
            svg += '<text x="' + xF2(f2).toFixed(1) + '" y="' + (dpTop + dpH + 8) + '" font-size="5.5" text-anchor="middle" fill="currentColor">' + (f2 / 1000) + '</text>';
        });
        svg += '<text x="' + (marginLeft + plotW / 2) + '" y="' + (dpTop + dpH + 16) + '" font-size="6" text-anchor="middle" fill="currentColor">DP-grama -- f2 (kHz), nivel DP en dB SPL</text>';

        // Barras de SNR por banda TEOAE, con la línea de criterio.
        var barTop = dpTop + dpH + gap;
        var snrMax = 30;
        function yBar(snr) { return barTop + barH * (1 - Math.max(0, Math.min(snrMax, snr)) / snrMax); }
        svg += '<line x1="' + marginLeft + '" y1="' + yBar(0) + '" x2="' + (W - marginRight) + '" y2="' + yBar(0) + '" stroke="#000" stroke-opacity="0.25"></line>';
        svg += '<line x1="' + marginLeft + '" y1="' + yBar(TE.minSnr) + '" x2="' + (W - marginRight) + '" y2="' + yBar(TE.minSnr) + '" stroke="#c0392b" stroke-width="0.8" stroke-dasharray="4 2"></line>';
        svg += '<text x="' + (marginLeft - 3) + '" y="' + (yBar(TE.minSnr) + 2) + '" font-size="6" text-anchor="end" fill="#c0392b">' + TE.minSnr + '</text>';
        var slot = plotW / TE.bands.length;
        TE.bands.forEach(function (band, i) {
            var snr = teoaeSnr(lado, band);
            var x = marginLeft + slot * i + slot * 0.22;
            var w = slot * 0.56;
            var y = yBar(Math.max(0, snr));
            svg += '<rect x="' + x.toFixed(1) + '" y="' + y.toFixed(1) + '" width="' + w.toFixed(1) + '" height="' + Math.max(0.6, yBar(0) - y).toFixed(1) +
                '" fill="' + (snr >= TE.minSnr ? color : '#c0392b') + '" fill-opacity="' + (snr >= TE.minSnr ? '0.75' : '0.5') + '"></rect>';
            svg += '<text x="' + (x + w / 2).toFixed(1) + '" y="' + (yBar(0) + 8) + '" font-size="5.5" text-anchor="middle" fill="currentColor">' + (band / 1000) + '</text>';
        });
        svg += '<text x="' + (marginLeft + plotW / 2) + '" y="' + (yBar(0) + 16) + '" font-size="6" text-anchor="middle" fill="currentColor">TEOAE -- SNR por banda (kHz), criterio ' + TE.minSnr + ' dB</text>';

        // Resumen PASS/REFER de las dos pruebas, igual criterio que el cliente.
        var dpPass = DP.f2List.filter(function (f2) { return (dpLevel(lado, f2) - dpNoiseFloor(lado, f2)) >= DP.minSnr; }).length;
        var tePass = TE.bands.filter(function (b) { return teoaeSnr(lado, b) >= TE.minSnr; }).length;
        var veredicto = 'DPOAE ' + dpPass + '/' + DP.f2List.length + ' ' + (dpPass >= DP.passMin ? 'PASS' : 'REFER') +
            '  --  TEOAE ' + tePass + '/' + TE.bands.length + ' ' + (tePass >= TE.passMin ? 'PASS' : 'REFER');
        svg += '<text x="' + marginLeft + '" y="' + (H - 2) + '" font-size="6.5" fill="currentColor">' + veredicto + '</text>';
        svg += '</svg>';
        container.innerHTML = svg;
    }

    function drawEoaPreview() {
        renderEoaSide('od', window.sideColor('od'));
        renderEoaSide('oi', window.sideColor('oi'));
    }
    window.drawEoaPreview = drawEoaPreview;

    var eoasForm = document.getElementById('case-form');
    if (eoasForm) {
        eoasForm.addEventListener('input', function (e) {
            if (e.target.name && /^eoas\[/.test(e.target.name)) { drawEoaPreview(); }
        });
        eoasForm.addEventListener('change', function (e) {
            if (e.target.name && /^eoas\[/.test(e.target.name)) { drawEoaPreview(); }
        });
    }
    var eoasButtons = document.querySelectorAll('.eoas-autofill-btn');
    for (var i = 0; i < eoasButtons.length; i++) {
        eoasButtons[i].addEventListener('click', function (e) {
            autofillEoas(e.target.getAttribute('data-lado'));
        });
    }
    // Los grados dependen de la patología del oído: se recargan al cambiarla
    // (una coclear tiene leve/moderada/severa, una neural una sola).
    var eoasTypeSelects = document.querySelectorAll('.eoas-type-select');
    for (var t = 0; t < eoasTypeSelects.length; t++) {
        syncGradeOptions(eoasTypeSelects[t].getAttribute('data-lado'));
        eoasTypeSelects[t].addEventListener('change', function (e) {
            syncGradeOptions(e.target.getAttribute('data-lado'));
        });
    }
    // El generador lo llama directo, después de que la proyección escribió
    // la patología del oído. La proyección setea el .value del selector sin
    // disparar 'change', así que los grados hay que recargarlos acá: si no,
    // el sorteo elige entre los grados de la patología anterior.
    window.eoasAutofill = function (lado) {
        syncGradeOptions(lado);
        autofillEoas(lado);
    };
    drawEoaPreview();
})();
