// Autocompletar ABR: sugiere desviaciones/umbral/FSP plausibles para la
// patología elegida en cada oído, usando sexo+edad del paciente para elegir
// la población de referencia y el autor elegido arriba para elegir DE QUÉ
// baseline parte esa población. Los baselines de onda I/III/V (ABR_DEFAULT)
// y los rangos por patología (threshold_range, wave_I_reduction,
// interpeak_prolongation, etc.) son los mismos que usa
// resources/abr/normative_data.json / ABR_generator -- mantener
// sincronizado a mano si esos cambian (mismo criterio que la normativa por
// curso en courses.php). ABR_AUTHOR_CATALOG sale de AppConfig
// ('abr_reference_authors', global, ver admin/normativas.php).
// Es una sugerencia al azar dentro de un rango clínicamente razonable, no un
// valor fijo -- el docente la edita después.
(function () {
    var ABR_DEFAULT_POPULATIONS = {
        adult_male:   { I: { lat: 1.65, amp: 0.30 }, III: { lat: 3.85, amp: 0.35 }, V: { lat: 5.70, amp: 0.50 } },
        adult_female: { I: { lat: 1.62, amp: 0.21 }, III: { lat: 3.68, amp: 0.37 }, V: { lat: 5.47, amp: 0.60 } },
        child:        { I: { lat: 1.58, amp: 0.28 }, III: { lat: 3.78, amp: 0.33 }, V: { lat: 5.60, amp: 0.48 } },
        neonate:      { I: { lat: 2.10, amp: 0.20 }, III: { lat: 4.70, amp: 0.24 }, V: { lat: 6.80, amp: 0.35 } },
        elderly:      { I: { lat: 1.75, amp: 0.27 }, III: { lat: 4.00, amp: 0.32 }, V: { lat: 5.90, amp: 0.45 } }
    };
    var ABR_AUTHOR_CATALOG = window.CASE_CONST.abrAuthorCatalog;

    function rand(min, max) { return min + Math.random() * (max - min); }

    function pickPopulation() {
        var ageInput = document.getElementById('patient-age');
        var age = ageInput ? parseFloat(ageInput.value) : NaN;
        if (isNaN(age)) { age = 30; }
        var genderChecked = document.querySelector('input[name="gender"]:checked');
        var isFemale = !!genderChecked && genderChecked.value === '1';
        if (age <= 0.25) { return 'neonate'; }
        if (age <= 12) { return 'child'; }
        if (age >= 60) { return 'elderly'; }
        return isFemale ? 'adult_female' : 'adult_male';
    }

    // Baseline "real" a usar para esta población: la del autor elegido,
    // completada campo a campo con el default donde el autor no definió
    // esa onda/población (autor incompleto = no obliga a cargar los 30
    // campos para poder usarlo).
    function resolveBaseline(pop) {
        var d = ABR_DEFAULT_POPULATIONS[pop];
        var authorSelect = document.getElementById('abr-author-select');
        var authorId = authorSelect ? authorSelect.value : '__default__';
        var author = ABR_AUTHOR_CATALOG[authorId];
        var authorPop = author && author.populations ? author.populations[pop] : null;
        var out = {};
        ['I', 'III', 'V'].forEach(function (wave) {
            var aw = authorPop ? authorPop[wave] : null;
            out[wave] = {
                lat: aw && aw.lat !== undefined ? aw.lat : d[wave].lat,
                amp: aw && aw.amp !== undefined ? aw.amp : d[wave].amp
            };
        });
        return { def: d, author: out };
    }

    // Cada rango viene de pathology_modifiers en normative_data.json; las
    // desviaciones de latencia son deltas en ms sobre el baseline DEL AUTOR
    // elegido (más el offset autor-vs-default, para que el cliente -que
    // siempre suma la desviación sobre SU propio default- reconstruya el
    // valor absoluto del autor). Las de amplitud son fracción del baseline
    // del autor (así el mismo % de reducción da un delta distinto en un
    // adulto que en un neonato, o entre autores).
    function buildValues(type, pop) {
        var baseline = resolveBaseline(pop);
        var d = baseline.def, b = baseline.author;
        var latOffset = { I: b.I.lat - d.I.lat, III: b.III.lat - d.III.lat, V: b.V.lat - d.V.lat };
        var ampOffset = { I: b.I.amp - d.I.amp, III: b.III.amp - d.III.amp, V: b.V.amp - d.V.amp };
        var v = {
            umbral: 20, repro: true, repro_var: 0, average_objetivo: 1500,
            lat_I: 0, lat_III: 0, lat_V: 0, amp_I: 0, amp_III: 0, amp_V: 0,
            fsp_800: 2.3, fsp_2000: 2.8, fsp_obj: 3.0
        };
        if (type === 'coclear') {
            // Sensorial: umbral elevado (recruitment), onda I reducida,
            // onda V preservada relativa a I, latencias casi normales a
            // intensidad supraumbral.
            v.umbral = Math.round(rand(30, 90));
            v.lat_I = latOffset.I + rand(0, 0.15); v.lat_III = latOffset.III + rand(0, 0.15); v.lat_V = latOffset.V + rand(0, 0.15);
            v.amp_I = ampOffset.I + b.I.amp * rand(-0.5, -0.2);
            v.amp_III = ampOffset.III + b.III.amp * rand(-0.2, 0.05);
            v.amp_V = ampOffset.V + b.V.amp * rand(-0.05, 0.15);
            v.average_objetivo = Math.round(rand(1500, 2500));
            v.fsp_800 = 2.3 * rand(0.8, 1.0); v.fsp_2000 = 2.8 * rand(0.8, 1.0); v.fsp_obj = 3.0 * rand(0.8, 1.0);
        } else if (type === 'transmission') {
            // Conductivo: desplazamiento uniforme de latencia y reducción
            // uniforme de amplitud en I/III/V -- interpicos quedan normales.
            var shift = rand(0.15, 0.35);
            var ampFactor = rand(-0.4, -0.2);
            v.umbral = Math.round(rand(20, 60));
            v.lat_I = latOffset.I + shift; v.lat_III = latOffset.III + shift; v.lat_V = latOffset.V + shift;
            v.amp_I = ampOffset.I + b.I.amp * ampFactor; v.amp_III = ampOffset.III + b.III.amp * ampFactor; v.amp_V = ampOffset.V + b.V.amp * ampFactor;
            v.average_objetivo = Math.round(rand(1500, 2200));
            v.fsp_800 = 2.3 * rand(0.85, 1.0); v.fsp_2000 = 2.8 * rand(0.85, 1.0); v.fsp_obj = 3.0 * rand(0.85, 1.0);
        } else if (type === 'neural') {
            // Retrococlear: las latencias y amplitudes NO se sortean acá.
            // El patrón (I-III, III-V, razón V/I, bloqueo...) es su propio
            // juego de parámetros -- ver el bloque "Patrón retrococlear" y
            // los presets. Si además se cargaran desviaciones por onda, el
            // efecto se sumaría dos veces. Acá queda solo el ruido de
            // test-retest y las condiciones de registro.
            v.umbral = Math.round(rand(0, 60));
            v.lat_I = latOffset.I + rand(-0.05, 0.05);
            v.lat_III = latOffset.III + rand(-0.05, 0.05);
            v.lat_V = latOffset.V + rand(-0.05, 0.05);
            v.amp_I = ampOffset.I + b.I.amp * rand(-0.08, 0.08);
            v.amp_III = ampOffset.III + b.III.amp * rand(-0.08, 0.08);
            v.amp_V = ampOffset.V + b.V.amp * rand(-0.08, 0.08);
            v.repro = Math.random() >= 0.6;
            v.repro_var = v.repro ? 0 : rand(0.15, 0.4);
            v.average_objetivo = Math.round(rand(2500, 4000));
            v.fsp_800 = rand(1.2, 1.8); v.fsp_2000 = rand(1.6, 2.2); v.fsp_obj = rand(2.0, 2.6);
        } else {
            // Normal: sin hallazgos, solo ruido de test-retest.
            v.umbral = Math.round(rand(0, 20));
            v.lat_I = latOffset.I + rand(-0.05, 0.05); v.lat_III = latOffset.III + rand(-0.05, 0.05); v.lat_V = latOffset.V + rand(-0.05, 0.05);
            v.amp_I = ampOffset.I + b.I.amp * rand(-0.08, 0.08);
            v.amp_III = ampOffset.III + b.III.amp * rand(-0.08, 0.08);
            v.amp_V = ampOffset.V + b.V.amp * rand(-0.08, 0.08);
            v.average_objetivo = Math.round(rand(1200, 1800));
            v.fsp_800 = 2.3 + rand(-0.1, 0.1); v.fsp_2000 = 2.8 + rand(-0.1, 0.1); v.fsp_obj = 3.0 + rand(-0.1, 0.1);
        }
        return v;
    }

    function fieldEl(lado, field) {
        return document.querySelector('[name="abr[' + lado + '][' + field + ']"]');
    }

    function setNum(lado, field, value, decimals) {
        var el = fieldEl(lado, field);
        if (el) { el.value = value.toFixed(decimals); }
    }

    // Los 6 campos de onda se muestran como valor ABSOLUTO a 80dB (lo que el
    // docente quiere fijar), pero se guardan como desviacion respecto del
    // normativo (lo que espera CaseBuilder.php/ABR_generator.py -- cambiar
    // ese contrato es un cambio de esquema más grande, no solo de este
    // formulario). El input visible (.abr-abs-input) no tiene name, no se
    // manda; el hidden (.abr-delta-input, mismo name de siempre) es el que
    // se envía.
    var ABR_WAVE_FIELDS = [['I', 'lat'], ['III', 'lat'], ['V', 'lat'], ['I', 'amp'], ['III', 'amp'], ['V', 'amp']];

    function absFieldEl(lado, wave, field) {
        return document.querySelector('.abr-abs-input[data-lado="' + lado + '"][data-wave="' + wave + '"][data-field="' + field + '"]');
    }

    function deltaFieldEl(lado, wave, field) {
        return fieldEl(lado, field + '_' + wave);
    }

    // Normativo -> lo que se muestra. Se llama al cargar la pagina y despues
    // de "Autocompletar" (que recalcula la desviacion sugerida).
    function syncAbsFromDelta(lado) {
        var baseline = resolveBaseline(pickPopulation()).author;
        ABR_WAVE_FIELDS.forEach(function (pair) {
            var wave = pair[0], field = pair[1];
            var absEl = absFieldEl(lado, wave, field);
            var deltaEl = deltaFieldEl(lado, wave, field);
            if (!absEl || !deltaEl) { return; }
            var delta = parseFloat(deltaEl.value) || 0;
            absEl.value = (baseline[wave][field] + delta).toFixed(2);
        });
    }

    // Lo que se muestra -> desviacion real a guardar. Se llama al tipear un
    // valor absoluto (ese campo) o al cambiar la poblacion de referencia
    // (todos, ver mas abajo) -- en ese caso el valor absoluto que el docente
    // ya fijo queda igual, se recalcula la desviacion contra el nuevo
    // normativo.
    function syncDeltaFromAbs(lado, wave, field) {
        var baseline = resolveBaseline(pickPopulation()).author;
        var absEl = absFieldEl(lado, wave, field);
        var deltaEl = deltaFieldEl(lado, wave, field);
        if (!absEl || !deltaEl) { return; }
        var absVal = parseFloat(absEl.value);
        if (isNaN(absVal)) { return; }
        deltaEl.value = (absVal - baseline[wave][field]).toFixed(4);
    }

    // Cambio de poblacion (edad/sexo/autor): un campo que el docente jamas
    // tipeo a mano (data-touched) sigue mostrando "el normativo" -- se
    // actualiza al normativo nuevo, la desviacion guardada (probablemente 0)
    // no cambia. Un campo que SI se tipeo mantiene el numero absoluto fijo
    // -- se recalcula la desviacion contra el normativo nuevo para que ese
    // numero no se mueva.
    function onAbrPopulationChange() {
        ['od', 'oi'].forEach(function (lado) {
            ABR_WAVE_FIELDS.forEach(function (pair) {
                var absEl = absFieldEl(lado, pair[0], pair[1]);
                if (absEl && absEl.dataset.touched === '1') {
                    syncDeltaFromAbs(lado, pair[0], pair[1]);
                }
            });
            syncAbsFromDelta(lado);
        });
        window.drawAbrPreview();
    }

    function autofillAbr(lado) {
        var typeSel = fieldEl(lado, 'type');
        var type = typeSel ? typeSel.value : 'normal';
        var v = buildValues(type, pickPopulation());
        // Retrococlear: el patrón se sortea aparte, no como desviaciones de
        // onda. Un caso al azar es un punto de partida -- para un cuadro
        // clínico concreto está el selector de presets.
        if (type === 'neural') { randomizeNeuralPattern(lado); }
        setNum(lado, 'umbral', v.umbral, 0);
        var reproEl = fieldEl(lado, 'repro');
        if (reproEl) { reproEl.checked = v.repro; }
        setNum(lado, 'repro_var', v.repro_var, 2);
        setNum(lado, 'average_objetivo', v.average_objetivo, 0);
        setNum(lado, 'lat_I', v.lat_I, 2);
        setNum(lado, 'lat_III', v.lat_III, 2);
        setNum(lado, 'lat_V', v.lat_V, 2);
        setNum(lado, 'amp_I', v.amp_I, 2);
        setNum(lado, 'amp_III', v.amp_III, 2);
        setNum(lado, 'amp_V', v.amp_V, 2);
        setNum(lado, 'fsp_800', v.fsp_800, 2);
        setNum(lado, 'fsp_2000', v.fsp_2000, 2);
        setNum(lado, 'fsp_obj', v.fsp_obj, 2);
        // La sugerencia es relativa a la poblacion actual (no un numero que
        // el docente fijo a mano) -- vuelve a seguir el normativo si despues
        // cambia edad/sexo/autor, ver onAbrPopulationChange.
        ABR_WAVE_FIELDS.forEach(function (pair) {
            var absEl = absFieldEl(lado, pair[0], pair[1]);
            if (absEl) { delete absEl.dataset.touched; }
        });
        syncAbsFromDelta(lado);
        if (window.drawAbrPreview) { window.drawAbrPreview(); }
    }

    // Los parámetros del patrón retrococlear solo existen dentro de
    // "Neural": con coclear o transmisión no hay lesión que tipificar y el
    // bloque confunde. Se oculta, no se borra -- si el docente vuelve a
    // Neural recupera lo que tenía, y los valores se siguen enviando (el
    // generador solo los mira si la patología es neural).
    function syncNeuralBlockVisibility(lado) {
        var bloque = document.querySelector('.abr-neural-block[data-lado="' + lado + '"]');
        if (!bloque) { return; }
        bloque.style.display = abrPathology(lado) === 'neural' ? '' : 'none';
    }

    var typeSelects = document.querySelectorAll('.abr-type-select');
    for (var ts = 0; ts < typeSelects.length; ts++) {
        syncNeuralBlockVisibility(typeSelects[ts].getAttribute('data-lado'));
        typeSelects[ts].addEventListener('change', function (e) {
            syncNeuralBlockVisibility(e.target.getAttribute('data-lado'));
        });
    }

    // Presets: precargan los parámetros y quedan editables. La etiqueta NO
    // se guarda -- el caso persiste los números, así el alumno nunca puede
    // leer el diagnóstico desde el caso ni la curva depender de un nombre.
    var ABR_NEURAL_PRESETS = window.CASE_CONST.abrNeuralPresets;

    function neuralFieldEl(lado, param) {
        return document.querySelector('.abr-neural-input[data-lado="' + lado + '"][data-param="' + param + '"]');
    }

    function applyNeuralPreset(lado) {
        var sel = document.querySelector('.abr-neural-preset-select[data-lado="' + lado + '"]');
        var nota = document.querySelector('.abr-neural-preset-nota[data-lado="' + lado + '"]');
        var preset = sel && sel.value ? ABR_NEURAL_PRESETS[sel.value] : null;
        if (!preset) { if (nota) { nota.textContent = ''; } return; }
        Object.keys(preset.params).forEach(function (param) {
            var el = neuralFieldEl(lado, param);
            if (el) { el.value = preset.params[param]; }
        });
        if (nota) { nota.textContent = preset.nota || ''; }
        if (window.drawAbrPreview) { window.drawAbrPreview(); }
    }

    // Elegir el preset solo muestra su nota; los valores se pisan al apretar
    // "Aplicar" -- asi un click de curiosidad no borra un patron ya tipeado.
    var presetSelects = document.querySelectorAll('.abr-neural-preset-select');
    for (var ps = 0; ps < presetSelects.length; ps++) {
        presetSelects[ps].addEventListener('change', function (e) {
            var lado = e.target.getAttribute('data-lado');
            var nota = document.querySelector('.abr-neural-preset-nota[data-lado="' + lado + '"]');
            var preset = e.target.value ? ABR_NEURAL_PRESETS[e.target.value] : null;
            if (nota) { nota.textContent = preset ? (preset.nota || '') : ''; }
        });
    }

    var presetBtns = document.querySelectorAll('.abr-neural-preset-btn');
    for (var pb = 0; pb < presetBtns.length; pb++) {
        presetBtns[pb].addEventListener('click', function (e) {
            applyNeuralPreset(e.currentTarget.getAttribute('data-lado'));
        });
    }

    // Sorteo del patrón retrococlear: no un valor fijo "correcto", sino un
    // caso plausible distinto cada vez (el alumno tiene que leer la curva,
    // no memorizar el caso). Se sortea DÓNDE está la lesión y después cuánto.
    function randomizeNeuralPattern(lado) {
        var proximal = Math.random() < 0.5;   // nervio vs tronco
        var params = {
            i_iii_ms: proximal ? rand(0.3, 0.8) : rand(0.0, 0.15),
            iii_v_ms: proximal ? rand(0.1, 0.4) : rand(0.4, 0.9),
            global_delay_ms: 0,
            v_i_factor: rand(0.25, 0.6),
            bloqueo: 'ninguno',
            microfonica: 'normal',
            desincronia: Math.random() < 0.5 ? 'leve' : 'alta',
            sensibilidad_tasa: Math.random() < 0.7 ? 'severa' : 'moderada'
        };
        Object.keys(params).forEach(function (param) {
            var el = neuralFieldEl(lado, param);
            if (!el) { return; }
            el.value = typeof params[param] === 'number' ? params[param].toFixed(2) : params[param];
        });
        var sel = document.querySelector('.abr-neural-preset-select[data-lado="' + lado + '"]');
        var nota = document.querySelector('.abr-neural-preset-nota[data-lado="' + lado + '"]');
        if (sel) { sel.value = ''; }
        if (nota) { nota.textContent = ''; }
    }

    var buttons = document.querySelectorAll('.abr-autofill-btn');
    for (var i = 0; i < buttons.length; i++) {
        buttons[i].addEventListener('click', function (e) {
            autofillAbr(e.currentTarget.getAttribute('data-lado'));
        });
    }

    // Vista previa en vivo: serie 100->0 dBnHL, version limpia (sin ruido,
    // sin promediacion, sin filtros) de ABRGenerator.calculate_wave_parameters
    // + build_target_curve (ver src/abr/ABR_generator.py) restringida a
    // I/III/V -- las mismas ondas que el formulario deja editar. Solo para
    // que el docente vea el efecto de sus valores, no reemplaza al generador
    // real (que corre server-side/en el cliente con ruido y FSP).
    var WAVE_SIGMA_PREVIEW = { I: 0.22, III: 0.22, V: 0.18 };
    var ABR_PREVIEW_INTENSITIES = [100, 90, 80, 70, 60, 50, 40, 30, 20, 10, 0];
    // Mismo umbral de visibilidad que usa el generador para decir si una
    // onda esta presente: por debajo no se le pone marcador.
    var WAVE_VISIBLE_UV = 0.02;
    // Piso de la escala automatica de amplitud. Sin esto, una serie sin
    // respuesta se amplificaria hasta llenar la fila y una linea plana
    // pareceria una onda.
    var AMP_SCALE_FLOOR_UV = 0.08;

    // Constantes espejadas de ABR_generator.py -- si cambian alla, cambian
    // aca: la previa tiene que mostrar la misma curva que va a ver el
    // alumno. Antes esta previa iba por su cuenta (amplitud lineal contra
    // un techo de 80 dB, la onda I con el escalon "disappear_offset" que
    // el generador ya no tiene, y CERO efecto de la patologia: un ANSD se
    // dibujaba con ondas normales).
    var LAT_SHIFT_FACTOR = { I: 0.85, III: 0.92, V: 1.0 };
    var WAVE_AMP_GROWTH = {
        I: { sl_min: 20, tau: 13 },
        III: { sl_min: 5, tau: 16 },
        V: { sl_min: -4, tau: 20 }
    };
    var PATHOLOGY_TAU_FACTOR = { coclear: 0.65 };
    var NORMAL_THRESHOLD_REF = 15;
    var COCHLEAR_LI_SL_REF = 40, COCHLEAR_LI_SLOPE = 0.15;
    var DEV_LI_GAIN = 0.35, DEV_LI_MAX = 1.5;
    // Reparto del retraso y de la caída de amplitud por onda (espejo de
    // NEURAL_LAT_SHARE / NEURAL_LAT_SHARE_IIIV / NEURAL_AMP_SHARE).
    var NEURAL_SHARE_I_III = { I: 0.0, III: 1.0, V: 1.0 };
    var NEURAL_SHARE_III_V = { I: 0.0, III: 0.0, V: 1.0 };
    var NEURAL_AMP_SHARE = { I: 0.0, III: 0.5, V: 1.0 };
    var NEURAL_BLOCK_AMP_FACTOR = 0.02;
    var NEURAL_DESYNC_WIDTH = { ninguna: 1.0, leve: 1.35, alta: 1.9 };

    function abrPathology(lado) {
        var el = document.querySelector('[name="abr[' + lado + '][type]"]');
        return el ? el.value : 'normal';
    }

    function abrNeuralParams(lado) {
        var out = {};
        ['i_iii_ms', 'iii_v_ms', 'global_delay_ms', 'v_i_factor',
         'bloqueo', 'desincronia'].forEach(function (param) {
            var el = document.querySelector('.abr-neural-input[data-lado="' + lado + '"][data-param="' + param + '"]');
            out[param] = el ? el.value : null;
        });
        return out;
    }

    // Mismo quiebre que ABRGenerator.latency_intensity_shift: ~0.12ms/10dB
    // cerca del techo (sobre 70dB), ~0.3ms/10dB de ahi para abajo
    // (Hood: ~0.3ms/10dB entre 70 y 50dB).
    function latShiftForIntensity(intensity) {
        if (intensity >= 70) { return (80 - intensity) / 10 * 0.12; }
        return (80 - 70) / 10 * 0.12 + (70 - intensity) / 10 * 0.3;
    }

    // Corrimiento con patologia: la transmision atenua el estimulo (GAP) y
    // corre la funcion en paralelo; la coclear la EMPINA cerca del umbral.
    function latShiftForCase(intensity, threshold, pathology) {
        var gap = pathology === 'transmission' ? Math.max(threshold - NORMAL_THRESHOLD_REF, 0) : 0;
        var shift = latShiftForIntensity(intensity - gap);
        if (pathology === 'coclear') {
            shift += COCHLEAR_LI_SLOPE * Math.max(0, COCHLEAR_LI_SL_REF - (intensity - threshold)) / 10;
        }
        return shift;
    }

    function widthFactorForSl(sl) {
        if (sl >= 50) { return 1.0; }
        if (sl >= 30) { return 1.0 + (50 - sl) * 0.03; }
        return Math.min(1.6 + (30 - sl) * 0.05, 2.6);
    }

    // Curva de crecimiento saturante sobre el SL, con el codo suave
    // (softplus) del generador.
    function ampFactorForWave(wave, sl, pathology) {
        var growth = WAVE_AMP_GROWTH[wave];
        var tau = growth.tau * (PATHOLOGY_TAU_FACTOR[pathology] || 1.0);
        var knee = 0.3 * tau;
        var x = (sl - growth.sl_min) / knee;
        // logaddexp(0, x) estable para x grande.
        var slEff = knee * (x > 30 ? x : Math.log(1 + Math.exp(x)));
        return 1.0 - Math.exp(-slEff / tau);
    }

    function gaussian(t, center, amp, sigma) {
        var z = (t - center) / sigma;
        return amp * Math.exp(-0.5 * z * z);
    }

    function computeWaveValues(lado, pop, intensity) {
        var baseline = resolveBaseline(pop).author;
        var threshold = parseFloat(fieldEl(lado, 'umbral').value) || 0;
        var pathology = abrPathology(lado);
        var neural = pathology === 'neural';
        var np = neural ? abrNeuralParams(lado) : null;
        var sl = intensity - threshold;
        var latShift = latShiftForCase(intensity, threshold, pathology);
        var devScale = Math.min(1.0 + DEV_LI_GAIN * Math.max(latShift, 0), DEV_LI_MAX);
        var width = widthFactorForSl(sl);
        var out = {};
        ['I', 'III', 'V'].forEach(function (wave) {
            var deltaLatEl = fieldEl(lado, 'lat_' + wave);
            var deltaAmpEl = fieldEl(lado, 'amp_' + wave);
            var deltaLat = deltaLatEl ? (parseFloat(deltaLatEl.value) || 0) : 0;
            var deltaAmp = deltaAmpEl ? (parseFloat(deltaAmpEl.value) || 0) : 0;
            var lat = baseline[wave].lat + latShift * LAT_SHIFT_FACTOR[wave] + deltaLat * devScale;
            var amp = baseline[wave].amp * ampFactorForWave(wave, sl, pathology);
            var sigmaGain = 1.0;
            if (neural) {
                lat += (parseFloat(np.global_delay_ms) || 0)
                    + (parseFloat(np.i_iii_ms) || 0) * NEURAL_SHARE_I_III[wave]
                    + (parseFloat(np.iii_v_ms) || 0) * NEURAL_SHARE_III_V[wave];
                var vi = parseFloat(np.v_i_factor);
                if (isNaN(vi)) { vi = 1.0; }
                amp *= Math.max(1.0 - (1.0 - vi) * NEURAL_AMP_SHARE[wave], 0);
                if (np.bloqueo === 'total' || (np.bloqueo === 'post_i' && wave !== 'I')) {
                    amp *= NEURAL_BLOCK_AMP_FACTOR;
                }
                sigmaGain = NEURAL_DESYNC_WIDTH[np.desincronia] || 1.0;
            }
            amp = Math.max(amp + deltaAmp, 0.001);
            out[wave] = { lat: lat, amp: amp, sigma: WAVE_SIGMA_PREVIEW[wave] * width * sigmaGain };
        });
        return out;
    }

    // Traza la suma de las 3 gaussianas y, de paso, devuelve la altura del
    // trazo en la latencia de cada onda: ahi va el marcador, asi la marca
    // toca la curva en vez de flotar.
    function buildRow(values, xPos, rowBaseY, ampScale) {
        function yAt(t) {
            var y = 0;
            ['I', 'III', 'V'].forEach(function (wave) {
                var v = values[wave];
                // Una onda por debajo del umbral de visibilidad no se
                // dibuja: si no, el residuo que deja el bloqueo se
                // amplificaba con la escala automatica y una serie SIN
                // respuesta mostraba ondulaciones que no existen.
                if (v.amp <= WAVE_VISIBLE_UV) { return; }
                y += gaussian(t, v.lat, v.amp, v.sigma);
            });
            return y;
        }
        var pts = [];
        for (var t = 0; t <= 12; t += 0.06) {
            pts.push(xPos(t).toFixed(1) + ',' + (rowBaseY - yAt(t) * ampScale).toFixed(1));
        }
        var picos = {};
        ['I', 'III', 'V'].forEach(function (wave) {
            picos[wave] = {
                x: xPos(values[wave].lat),
                y: rowBaseY - yAt(values[wave].lat) * ampScale,
                visible: values[wave].amp > WAVE_VISIBLE_UV
            };
        });
        return { points: pts.join(' '), picos: picos };
    }

    function renderAbrPreviewSide(lado, color) {
        var container = document.getElementById('abr-preview-' + lado);
        if (!container) { return; }
        var umbralEl = fieldEl(lado, 'umbral');
        if (!umbralEl) { return; }
        var pop = pickPopulation();
        var threshold = parseFloat(umbralEl.value) || 0;

        var marginLeft = 34, marginRight = 12, marginTop = 16, marginBottom = 22;
        var rowHeight = 26, plotWidth = 380;
        var totalWidth = marginLeft + plotWidth + marginRight;
        var plotTop = marginTop;
        var plotBottom = marginTop + ABR_PREVIEW_INTENSITIES.length * rowHeight;
        var totalHeight = plotBottom + marginBottom;
        function xPos(t) { return marginLeft + (t / 12) * plotWidth; }

        // Escala vertical automatica: la onda mas grande de TODA la serie
        // ocupa una fraccion fija de la fila. Con una escala fija, un oido
        // con amplitudes chicas se veia como una linea plana y uno normal
        // se salia de la fila.
        var serie = ABR_PREVIEW_INTENSITIES.map(function (intensity) {
            return computeWaveValues(lado, pop, intensity);
        });
        var ampMax = 0;
        serie.forEach(function (values) {
            ['I', 'III', 'V'].forEach(function (wave) {
                if (values[wave].amp > ampMax) { ampMax = values[wave].amp; }
            });
        });
        // Piso: sin esto, una serie sin respuesta amplificaria el residuo
        // hasta llenar la fila y una linea plana pareceria una onda.
        if (ampMax < AMP_SCALE_FLOOR_UV) { ampMax = AMP_SCALE_FLOOR_UV; }
        var ampScale = (rowHeight * 0.62) / ampMax;

        var svg = '<svg viewBox="0 0 ' + totalWidth + ' ' + totalHeight + '" xmlns="http://www.w3.org/2000/svg">';

        // Grilla de tiempo + eje ms
        for (var ms = 0; ms <= 12; ms += 1) {
            var x = xPos(ms);
            var mayor = ms % 2 === 0;
            svg += '<line x1="' + x + '" y1="' + plotTop + '" x2="' + x + '" y2="' + plotBottom +
                '" stroke="#000" stroke-opacity="' + (mayor ? 0.10 : 0.05) + '"></line>';
            if (mayor) {
                svg += '<text x="' + x + '" y="' + (plotBottom + 9) + '" font-size="6" text-anchor="middle" fill="currentColor">' + ms + '</text>';
            }
        }
        svg += '<text x="' + (marginLeft + plotWidth / 2) + '" y="' + (totalHeight - 2) + '" font-size="6" text-anchor="middle" fill="currentColor">ms</text>';
        svg += '<text x="2" y="' + (plotTop - 6) + '" font-size="6" fill="currentColor">dBnHL</text>';

        // Escala de amplitud: una barra de largo conocido dice cuanto es
        // un microvolt en este dibujo (el zoom cambia con el caso).
        var refUv = ampMax >= 0.4 ? 0.5 : (ampMax >= 0.15 ? 0.2 : 0.05);
        var barX = totalWidth - marginRight - 3;
        var barBottom = plotTop - 4;
        var barTop = barBottom - refUv * ampScale;
        svg += '<line x1="' + barX + '" y1="' + barTop + '" x2="' + barX + '" y2="' + barBottom + '" stroke="currentColor" stroke-width="0.8"></line>';
        svg += '<text x="' + (barX - 3) + '" y="' + (barBottom - 1) + '" font-size="5.5" text-anchor="end" fill="currentColor">' + refUv + ' uV</text>';

        // Sin ondas (bloqueo total): la previa dibuja I/III/V y no hay
        // ninguna. La linea plana ES el resultado -- se avisa para que no se
        // lea como "la previa no anda". El microfonico no se grafica aca.
        if (abrPathology(lado) === 'neural') {
            var npPrev = abrNeuralParams(lado);
            var microfonicaEl = neuralFieldEl(lado, 'microfonica');
            var avisoPrev = npPrev.bloqueo === 'total'
                ? 'Sin ondas' + (microfonicaEl && microfonicaEl.value === 'amplificada'
                    ? ': solo microfonico coclear (no se grafica aca)' : '')
                : (npPrev.bloqueo === 'post_i' ? 'Solo onda I: bloqueo proximal' : '');
            if (avisoPrev) {
                // Al pie: arriba chocaba con las etiquetas I/III/V.
                svg += '<text x="' + marginLeft + '" y="' + (totalHeight - 2) +
                    '" font-size="6" fill="' + color + '">' + avisoPrev + '</text>';
            }
        }

        // Filas: fondo de la fila del umbral, etiqueta de intensidad y trazo.
        var seguimiento = { I: [], III: [], V: [] };
        var trazos = '';
        ABR_PREVIEW_INTENSITIES.forEach(function (intensity, i) {
            var rowTop = plotTop + i * rowHeight;
            var rowBaseY = rowTop + rowHeight * 0.72;
            var isThresholdRow = Math.abs(intensity - Math.round(threshold / 10) * 10) < 0.01;
            if (isThresholdRow) {
                svg += '<rect x="0" y="' + rowTop + '" width="' + totalWidth + '" height="' + rowHeight +
                    '" fill="' + color + '" fill-opacity="0.07"></rect>';
            }
            svg += '<line x1="' + marginLeft + '" y1="' + rowBaseY + '" x2="' + (marginLeft + plotWidth) +
                '" y2="' + rowBaseY + '" stroke="#000" stroke-opacity="0.08"></line>';
            svg += '<text x="' + (marginLeft - 4) + '" y="' + (rowBaseY + 2) + '" font-size="6.5" text-anchor="end" fill="' +
                (isThresholdRow ? color : 'currentColor') + '" font-weight="' + (isThresholdRow ? 'bold' : 'normal') + '">' +
                intensity + '</text>';

            // Latencias de la fila de 80 dB: es el nivel al que el docente
            // fija los valores absolutos en los campos de arriba, asi que
            // ver ahi el numero cierra el circulo con lo que acaba de tipear.
            if (intensity === 80) {
                var etiquetas = ['I', 'III', 'V'].filter(function (wave) {
                    return serie[i][wave].amp > WAVE_VISIBLE_UV;
                }).map(function (wave) {
                    return wave + ' ' + serie[i][wave].lat.toFixed(2);
                }).join('   ');
                if (etiquetas) {
                    svg += '<text x="' + (marginLeft + plotWidth - 2) + '" y="' + (rowTop + 7) +
                        '" font-size="5.5" text-anchor="end" fill="' + color + '" fill-opacity="0.75">' +
                        etiquetas + ' ms</text>';
                }
            }

            var fila = buildRow(serie[i], xPos, rowBaseY, ampScale);
            trazos += '<polyline points="' + fila.points + '" fill="none" stroke="' + color + '" stroke-width="1"></polyline>';
            ['I', 'III', 'V'].forEach(function (wave) {
                var pico = fila.picos[wave];
                if (!pico.visible) { return; }
                seguimiento[wave].push(pico);
                // Marcador vertical sobre el pico: baja desde el techo de la
                // fila hasta tocar la curva.
                trazos += '<line x1="' + pico.x.toFixed(1) + '" y1="' + (rowTop + 1.5) + '" x2="' + pico.x.toFixed(1) +
                    '" y2="' + pico.y.toFixed(1) + '" stroke="' + color + '" stroke-width="0.4" stroke-opacity="0.3"></line>';
                trazos += '<circle cx="' + pico.x.toFixed(1) + '" cy="' + pico.y.toFixed(1) + '" r="0.9" fill="' + color + '"></circle>';
            });
        });

        // Seguimiento del pico entre intensidades: es la funcion
        // latencia-intensidad dibujada sobre la propia serie -- lo que hace
        // evidente si la onda se corre al bajar dB o se queda clavada.
        ['I', 'III', 'V'].forEach(function (wave) {
            var puntos = seguimiento[wave];
            if (puntos.length < 2) { return; }
            svg += '<polyline points="' + puntos.map(function (p) {
                return p.x.toFixed(1) + ',' + p.y.toFixed(1);
            }).join(' ') + '" fill="none" stroke="' + color + '" stroke-width="0.6" stroke-opacity="0.45" stroke-dasharray="2 1.5"></polyline>';
            var primero = puntos[0];
            svg += '<text x="' + primero.x.toFixed(1) + '" y="' + (plotTop - 6) + '" font-size="6" text-anchor="middle" fill="' +
                color + '" font-weight="bold">' + wave + '</text>';
        });

        svg += trazos;
        svg += '</svg>';
        container.innerHTML = svg;
    }

    window.drawAbrPreview = function () {
        renderAbrPreviewSide('od', '#b33a3a');
        renderAbrPreviewSide('oi', '#2255aa');
    };

    var abrPreviewForm = document.getElementById('case-form');
    if (abrPreviewForm) {
        abrPreviewForm.addEventListener('input', function (e) {
            if (e.target.name && /^abr\[/.test(e.target.name)) { window.drawAbrPreview(); }
            if (e.target.classList && e.target.classList.contains('abr-abs-input')) {
                e.target.dataset.touched = '1';
                syncDeltaFromAbs(e.target.getAttribute('data-lado'), e.target.getAttribute('data-wave'), e.target.getAttribute('data-field'));
                window.drawAbrPreview();
            }
        });
        abrPreviewForm.addEventListener('change', function (e) {
            if (e.target.name === 'gender') { onAbrPopulationChange(); return; }
            if (e.target.name && /^abr\[/.test(e.target.name)) { window.drawAbrPreview(); }
        });
    }
    var abrAuthorSelectEl = document.getElementById('abr-author-select');
    if (abrAuthorSelectEl) { abrAuthorSelectEl.addEventListener('change', onAbrPopulationChange); }
    var abrAgeEl = document.getElementById('patient-age');
    if (abrAgeEl) {
        abrAgeEl.addEventListener('input', onAbrPopulationChange);
        abrAgeEl.addEventListener('change', onAbrPopulationChange);
    }
    ['od', 'oi'].forEach(syncAbsFromDelta);
    window.drawAbrPreview();
})();
