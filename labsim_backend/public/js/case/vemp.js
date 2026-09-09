// Vista previa de los tres VEMP, por oído.
//
// Espejo en JS de VEMPGeneratorV1.calculate_wave_parameters +
// build_target_curve (src/vemp/VEMP_generator_v1.py), versión limpia: sin
// EMG, sin promediación, sin drift. Sirve para que el docente vea qué
// respuesta describen sus números antes de guardar -- no reemplaza al
// generador real, que corre en el cliente.
//
// La normativa es el MISMO archivo que carga la app
// (resources/vemp/normative_data.json), serializado en CASE_CONST: los
// números no se re-tipean acá.
//
// UNA diferencia a propósito con el generador de la app: acá la polaridad
// sale del nombre del pico (p13 hacia arriba, n23 hacia abajo). El
// generador suma las dos gaussianas positivas y dibuja dos jorobas del
// mismo lado, que no es la morfología bifásica de un VEMP. Cuando se toque
// la app hay que corregirlo allá; mientras tanto la previa muestra la
// respuesta que los números describen, no la que el generador dibuja mal.
(function () {
    var NORM = window.CASE_CONST.vempNormative || {};
    var POBLACIONES = NORM.populations || {};
    var PATH_MODS = NORM.pathology_modifiers || {};
    var SUBTIPOS = window.CASE_CONST.vempSubtipos || [];
    var PEAKS = window.CASE_CONST.vempPeaks || {};
    // Normativa del curso (courses.php): pisa lat/amp por pico. Va DESPUÉS
    // de la patología y de las desviaciones, igual que en el generador.
    var OVERRIDE = window.CASE_CONST.vempBaselineOverride || {};

    // Anchos base (sigma ms) por pico -- WAVE_SIGMA del generador.
    var WAVE_SIGMA = { p13: 0.40, n23: 0.45, n10: 0.35, p16: 0.40 };
    // Ventana del registro: 35 ms, como la del equipo.
    var T_MAX = 35;
    // Serie de intensidades. Tiene que ser una serie y no una sola fila:
    // la amplitud sale de (intensidad - umbral) normalizada por
    // (80 - umbral), así que A 80 dB DA LO MISMO cualquier umbral -- el
    // campo no movía nada en la pantalla. En la serie el umbral se ve
    // donde la respuesta se apaga, que es como se lee.
    //
    // Arranca EN 80 y no más arriba a propósito: la normativa está definida
    // a 80 dB y esa fórmula interpola entre el umbral y 80, no extrapola.
    // Pedirle 100 dB con umbral 85 devuelve 1930 µV, catorce veces la
    // amplitud normativa. (El generador de la app tiene la misma fórmula
    // sin tope: si el equipo deja subir de 80, allá pasa lo mismo.)
    //
    // Y baja hasta UNA fila debajo del umbral, no hasta el final: es como
    // se busca un umbral en la clínica --se desciende hasta que la
    // respuesta desaparece y se confirma un nivel más abajo-- y las filas
    // que sobran son alto desperdiciado. Con menos filas cada una se hace
    // más alta, que es donde se lee la amplitud.
    var VEMP_TOP = 80, VEMP_STEP = 10, VEMP_FLOOR = 30;
    // Alto del área de dibujo, repartido entre las filas que haya (5 x 26
    // = el alto fijo que tenía antes).
    var VEMP_PLOT_H = 130;
    var VEMP_FILA_H_MIN = 22, VEMP_FILA_H_MAX = 52;
    // La normativa está definida a 80 dB: es la fila donde el docente ve
    // los números que acaba de tipear.
    var INTENSIDAD_REF = 80;

    function intensidadesDe(umbral) {
        var piso = Math.round(umbral / VEMP_STEP) * VEMP_STEP - VEMP_STEP;
        piso = Math.max(VEMP_FLOOR, Math.min(piso, VEMP_TOP));
        var out = [];
        for (var dB = VEMP_TOP; dB >= piso; dB -= VEMP_STEP) { out.push(dB); }
        return out;
    }

    var contenedores = document.querySelectorAll('.vemp-preview');
    if (!contenedores.length || !SUBTIPOS.length) { return; }

    function campo(name) { return document.querySelector('#case-form [name="' + name + '"]'); }
    function num(name, def) {
        var el = campo(name);
        var n = el ? parseFloat(el.value) : NaN;
        return isNaN(n) ? def : n;
    }

    /**
     * Población normativa del paciente. Mismas cuatro que el generador; la
     * edad manda sobre el sexo, que solo separa a los adultos.
     */
    function poblacion() {
        var el = document.getElementById('patient-age');
        var edad = el ? parseInt(el.value, 10) : NaN;
        if (isNaN(edad)) { edad = 30; }
        if (edad < 18) { return 'child'; }
        if (edad >= 65) { return 'elderly'; }
        var g = document.querySelector('#case-form input[name="gender"]:checked');
        return (g && g.value === '1') ? 'adult_female' : 'adult_male';
    }

    function baseline(subtipo) {
        var pop = POBLACIONES[poblacion()] || POBLACIONES.adult_female || {};
        var tb = ((pop.air_conduction || {}).tone_burst || {})['500Hz'] || {};
        if (!tb[subtipo]) {
            var fb = (((POBLACIONES.adult_female || {}).air_conduction || {}).tone_burst || {})['500Hz'] || {};
            return fb[subtipo] || {};
        }
        return tb[subtipo];
    }

    /** Latencia y amplitud de cada pico -- calculate_wave_parameters. */
    function picosDe(lado, subtipo, patologia, INTENSIDAD) {
        var base = baseline(subtipo);
        var umbral = num('vemp[' + lado + '][' + subtipo + '][umbral]', 60);
        var mods = PATH_MODS[patologia] || {};
        var latShift = ((80 - INTENSIDAD) / 10) * 0.05;
        var lista = PEAKS[subtipo] || [];
        var out = [];

        lista.forEach(function (pico, i) {
            if (!base[pico]) { return; }
            var lat = base[pico].lat + latShift;
            var amp = base[pico].amp;

            // Amplitud lineal con (intensidad - umbral), piso de ruido.
            if (INTENSIDAD >= umbral) {
                var rango = Math.max(80 - umbral, 1);
                amp *= 0.05 + 0.95 * ((INTENSIDAD - umbral) / rango);
            } else {
                amp *= Math.max(0.05 * (1 - (umbral - INTENSIDAD) / 10), 0.001);
            }

            // Patología: el cruce patología x subtipo es el hallazgo.
            if (patologia === 'sacular' && subtipo === 'CVEMP') {
                if (pico === 'p13') {
                    amp *= mods.cvemp_p13_amp_reduction !== undefined ? mods.cvemp_p13_amp_reduction : 0.25;
                    lat += mods.cvemp_p13_lat_prolongation_ms !== undefined ? mods.cvemp_p13_lat_prolongation_ms : 1.5;
                } else if (pico === 'n23') {
                    amp *= mods.cvemp_n23_amp_reduction !== undefined ? mods.cvemp_n23_amp_reduction : 0.30;
                }
            } else if (patologia === 'utricular' && subtipo === 'OVEMP') {
                if (pico === 'n10') {
                    amp *= mods.ovemp_n10_amp_reduction !== undefined ? mods.ovemp_n10_amp_reduction : 0.20;
                    lat += mods.ovemp_n10_lat_prolongation_ms !== undefined ? mods.ovemp_n10_lat_prolongation_ms : 1.2;
                } else if (pico === 'p16') {
                    amp *= mods.ovemp_p16_amp_reduction !== undefined ? mods.ovemp_p16_amp_reduction : 0.25;
                }
            } else if (patologia === 'neural') {
                amp *= mods.amplitude_reduction_uniform !== undefined ? mods.amplitude_reduction_uniform : 0.40;
                if (i === 1) {
                    lat += mods.interpeak_prolongation_ms !== undefined ? mods.interpeak_prolongation_ms : 1.5;
                }
            }

            // Desviaciones del caso, encima de todo lo anterior.
            lat += num('vemp[' + lado + '][' + subtipo + '][lat_' + pico + ']', 0);
            amp += num('vemp[' + lado + '][' + subtipo + '][amp_' + pico + ']', 0);

            // Override del curso: pisa el valor calculado, no lo corrige.
            var ovr = (OVERRIDE[subtipo] || {})[pico];
            if (ovr) {
                if (ovr.lat !== undefined) { lat = ovr.lat; }
                if (ovr.amp !== undefined) { amp = ovr.amp; }
            }

            out.push({
                pico: pico,
                lat: lat,
                // La polaridad la dice la inicial del pico (ver cabecera).
                amp: Math.max(Math.abs(amp), 0.001) * (pico.charAt(0) === 'n' ? -1 : 1),
                sigma: WAVE_SIGMA[pico] || 0.40
            });
        });
        return out;
    }

    /** Suma de gaussianas -- build_target_curve. */
    function curva(picos, t) {
        var y = 0;
        picos.forEach(function (p) {
            var z = (t - p.lat) / p.sigma;
            y += p.amp * Math.exp(-0.5 * z * z);
        });
        return y;
    }

    function dibujar(caja) {
        var lado = caja.dataset.lado;
        var subtipo = caja.dataset.subtipo;
        var tipoSel = document.querySelector('.vemp-type-select[data-lado="' + lado + '"]');
        var patologia = tipoSel ? tipoSel.value : 'normal';
        var umbral = num('vemp[' + lado + '][' + subtipo + '][umbral]', 60);

        var intensidades = intensidadesDe(umbral);
        var serie = intensidades.map(function (dB) {
            return picosDe(lado, subtipo, patologia, dB);
        });
        if (!serie[0].length) {
            caja.innerHTML = '<p class="help">Sin normativa para este subtipo.</p>';
            return;
        }

        var ml = 30, mr = 10, mt = 12, mb = 20;
        var filaH = Math.max(VEMP_FILA_H_MIN,
            Math.min(VEMP_FILA_H_MAX, VEMP_PLOT_H / intensidades.length));
        var plotW = 370;
        var W = ml + plotW + mr;
        var plotTop = mt, plotBottom = mt + intensidades.length * filaH;
        var H = plotBottom + mb;
        function xPos(t) { return ml + (t / T_MAX) * plotW; }

        // Escala automática: la onda más grande de TODA la serie ocupa una
        // fracción fija de la fila. Es obligatorio que sea por gráfico -- el
        // cVEMP ronda los 150 µV y el oVEMP los 10, y una escala común
        // dejaría el ocular en una raya plana.
        var ampMax = 0;
        serie.forEach(function (picos) {
            picos.forEach(function (p) { ampMax = Math.max(ampMax, Math.abs(p.amp)); });
        });
        // Piso proporcional a la normativa del subtipo (no absoluto, por lo
        // mismo): sin esto una serie sin respuesta amplifica el residuo
        // hasta llenar la fila y una línea plana parece una onda.
        var base = baseline(subtipo);
        var baseMax = 0;
        Object.keys(base).forEach(function (k) { baseMax = Math.max(baseMax, Math.abs(base[k].amp)); });
        ampMax = Math.max(ampMax, baseMax * 0.05, 1e-6);
        var escala = (filaH * 0.40) / ampMax;

        var color = window.sideColor ? window.sideColor(lado) : '#333';
        var svg = '<svg viewBox="0 0 ' + W + ' ' + H + '" xmlns="http://www.w3.org/2000/svg" role="img">';

        for (var ms = 0; ms <= T_MAX; ms += 5) {
            svg += '<line x1="' + xPos(ms).toFixed(1) + '" y1="' + plotTop + '" x2="' + xPos(ms).toFixed(1) +
                   '" y2="' + plotBottom + '" stroke="currentColor" stroke-opacity="0.08"/>';
            svg += '<text x="' + xPos(ms).toFixed(1) + '" y="' + (H - 6) +
                   '" font-size="6.5" text-anchor="middle" fill="currentColor" fill-opacity="0.6">' + ms + '</text>';
        }
        svg += '<text x="' + (W - mr) + '" y="' + (H - 6) +
               '" font-size="6.5" text-anchor="end" fill="currentColor" fill-opacity="0.6">ms</text>';

        intensidades.forEach(function (dB, i) {
            var filaTop = plotTop + i * filaH;
            var baseY = filaTop + filaH * 0.62;
            // Fila del umbral resaltada: es donde la respuesta se apaga, y
            // es lo que el docente está fijando con el campo de arriba.
            var esUmbral = Math.abs(dB - Math.round(umbral / 10) * 10) < 0.01;
            if (esUmbral) {
                svg += '<rect x="0" y="' + filaTop + '" width="' + W + '" height="' + filaH +
                       '" fill="' + color + '" fill-opacity="0.07"/>';
            }
            svg += '<line x1="' + ml + '" y1="' + baseY + '" x2="' + (ml + plotW) + '" y2="' + baseY +
                   '" stroke="currentColor" stroke-opacity="0.10"/>';
            svg += '<text x="' + (ml - 4) + '" y="' + (baseY + 2) + '" font-size="6.5" text-anchor="end" fill="' +
                   (esUmbral ? color : 'currentColor') + '" font-weight="' + (esUmbral ? 'bold' : 'normal') + '">' +
                   dB + '</text>';

            var picos = serie[i];
            var d = '';
            for (var k = 0; k <= 160; k++) {
                var t = T_MAX * k / 160;
                d += (k ? 'L' : 'M') + xPos(t).toFixed(1) + ' ' + (baseY - curva(picos, t) * escala).toFixed(1);
            }
            svg += '<path d="' + d + '" fill="none" stroke="' + color + '" stroke-width="1.1"/>';

            // Los picos se etiquetan solo en la fila de referencia: en las
            // otras se superpondrían con el trazo de la fila de al lado.
            if (dB === INTENSIDAD_REF) {
                picos.forEach(function (p) {
                    if (p.lat < 0 || p.lat > T_MAX) { return; }
                    svg += '<text x="' + xPos(p.lat).toFixed(1) + '" y="' +
                           (baseY - p.amp * escala + (p.amp >= 0 ? -3 : 7)).toFixed(1) +
                           '" font-size="6.5" text-anchor="middle" fill="' + color + '">' +
                           p.pico.toUpperCase() + ' ' + p.lat.toFixed(1) + '</text>';
                });
            }
        });
        svg += '<text x="' + ml + '" y="' + (plotTop - 3) +
               '" font-size="6.5" fill="currentColor" fill-opacity="0.6">dB / escala ' +
               ampMax.toFixed(ampMax < 20 ? 1 : 0) + ' µV</text>';
        svg += '</svg>';
        // Un umbral arriba del techo de la serie da una previa plana, que es
        // la lectura correcta (respuesta ausente) pero parece un gráfico
        // roto si no se dice.
        if (umbral > VEMP_TOP) {
            svg += '<p class="help">Umbral ' + umbral + ' dB: por encima de la serie, no hay respuesta en ' +
                   'ninguna intensidad. Es un VEMP ausente, no un gráfico vacío.</p>';
        }
        caja.innerHTML = svg;
    }

    function dibujarTodo() {
        contenedores.forEach(dibujar);
    }

    // Cualquier campo del VEMP, la patología, y la edad/sexo (que eligen la
    // población normativa) mueven la curva.
    document.addEventListener('input', function (e) {
        var name = e.target.getAttribute && e.target.getAttribute('name');
        if (e.target.id === 'patient-age' || (name && name.indexOf('vemp[') === 0)) { dibujarTodo(); }
    });
    document.addEventListener('change', function (e) {
        var name = e.target.getAttribute && e.target.getAttribute('name');
        if (name === 'gender' || (name && name.indexOf('vemp[') === 0)) { dibujarTodo(); }
    });
    window.drawVempPreview = dibujarTodo;
    dibujarTodo();
})();
