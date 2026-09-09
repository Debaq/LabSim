// Vista previa en vivo de la proyección del perfil auditivo.
//
// Las fórmulas NO se reimplementan acá: se le piden a admin/case_project.php,
// que llama al mismo CaseProfile::project() que corre al guardar. Antes esto
// era una copia en JS de la ley del ABR, y las otras tres (OEA, reflejos,
// supraliminares) directamente no se veían hasta guardar y reabrir el caso:
// el docente generaba un caso y la pestaña EOA seguía mostrando lo viejo.
(function () {
    var CSRF = window.CASE_CONST.csrf;
    var FREQS = window.CASE_CONST.freqs;
    var EOAS_FREQS = window.CASE_CONST.eoasFreqs;
    var NEURAL_PARAMS = window.CASE_CONST.neuralParams;
    var DECAY_MODES = window.CASE_CONST.decayModes;
    var ETIQUETAS = {
        'click': 'Click', 'ce_chirp': 'CE-chirp', 'ls_chirp': 'Ls-chirp',
        'tone_burst_500Hz': 'Burst 500 Hz', 'tone_burst_1000Hz': 'Burst 1 kHz',
        'tone_burst_2000Hz': 'Burst 2 kHz', 'tone_burst_4000Hz': 'Burst 4 kHz'
    };
    // Graves a agudos y después los de banda ancha, que es como se lee un
    // protocolo frecuencia específica.
    var ORDEN = ['tone_burst_500Hz', 'tone_burst_1000Hz', 'tone_burst_2000Hz',
                 'tone_burst_4000Hz', 'click', 'ce_chirp', 'ls_chirp'];

    var MODULOS = window.CASE_CONST.autoModules;
    var preview = document.getElementById('abr-threshold-preview');
    var tbody = document.getElementById('abr-threshold-rows');

    function campo(name) { return document.querySelector('#case-form [name="' + name + '"]'); }
    function autoOn(modulo) {
        var chk = campo('perfil[auto][' + modulo + ']');
        return !!(chk && chk.checked);
    }
    function curva(clave, lado) {
        var out = [];
        for (var n = 0; n < FREQS.length; n++) {
            var el = document.getElementById(clave + '_' + lado + '_' + n);
            out.push(el ? (parseInt(el.value, 10) || 0) : 0);
        }
        return out;
    }

    /** Lo que hay cargado en el formulario ahora mismo, sin guardar nada. */
    function estado() {
        var perfil = {};
        ['od', 'oi'].forEach(function (lado) {
            var cce = campo('perfil[' + lado + '][cce_pct]');
            var retro = {};
            NEURAL_PARAMS.forEach(function (param) {
                var el = document.querySelector('.abr-neural-input[data-lado="' + lado + '"][data-param="' + param + '"]');
                if (el) { retro[param] = el.value; }
            });
            perfil[lado] = { cce_pct: cce ? cce.value : 100, retro: retro };
        });
        var auto = {};
        MODULOS.forEach(function (m) { auto[m] = autoOn(m); });
        var zOd = campo('z_od'), zOi = campo('z_oi');
        return {
            aerea: { od: curva('aerea', 'od'), oi: curva('aerea', 'oi') },
            osea: { od: curva('osea', 'od'), oi: curva('osea', 'oi') },
            perfil: perfil, auto: auto,
            z: { od: zOd ? zOd.value : 'A', oi: zOi ? zOi.value : 'A' }
        };
    }

    // Qué ficha muestra cada módulo derivado: es lo que se avisa cuando la
    // proyección reescribe algo que no está en la pestaña abierta.
    var TAB_DE_MODULO = { abr: 'abr', eoas: 'eoas', reflex: 'timpanometria',
                          recruit: 'audiometria', logo: 'audiometria' };
    // Módulo que se está hidratando y fichas que cambiaron de verdad en esta
    // pasada (escribir el mismo número que ya estaba no es un cambio).
    var moduloActual = null;
    var tabsTocadas = {};
    var primeraPasada = true;

    function marcarTocado() {
        var tab = TAB_DE_MODULO[moduloActual];
        if (tab) { tabsTocadas[tab] = true; }
    }
    function setVal(name, valor) {
        var el = campo(name);
        if (!el || valor === undefined || valor === null) { return; }
        if (String(el.value) !== String(valor)) { marcarTocado(); }
        el.value = valor;
    }

    function pintarTablaAbr(abr) {
        if (!preview || !tbody) return;
        tbody.innerHTML = '';
        ORDEN.forEach(function (stim) {
            var tr = document.createElement('tr');
            var celdas = [ETIQUETAS[stim],
                abr.OD.umbral_por_estimulo[stim] + ' dB nHL',
                abr.OD.umbral_por_estimulo_oseo[stim] + ' dB nHL',
                abr.OI.umbral_por_estimulo[stim] + ' dB nHL',
                abr.OI.umbral_por_estimulo_oseo[stim] + ' dB nHL'];
            celdas.forEach(function (texto, i) {
                var td = document.createElement(i === 0 ? 'th' : 'td');
                td.textContent = texto;
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    function hidratar(p) {
        if (preview) { preview.hidden = !autoOn('abr'); }
        tabsTocadas = {};

        if (autoOn('abr')) {
            moduloActual = 'abr';
            pintarTablaAbr(p.abr);
            ['od', 'oi'].forEach(function (lado) {
                var lo = lado.toUpperCase();
                setVal('abr[' + lado + '][type]', p.abr[lo].type);
                setVal('abr[' + lado + '][umbral]', p.abr[lo].umbral);
            });
        }

        if (autoOn('eoas')) {
            moduloActual = 'eoas';
            ['od', 'oi'].forEach(function (lado) {
                var lo = lado.toUpperCase();
                setVal('eoas[' + lado + '][type]', p.eoas[lo].type);
                setVal('eoas[' + lado + '][umbral]', p.eoas[lo].umbral);
                EOAS_FREQS.forEach(function (hz) {
                    setVal('eoas[' + lado + '][desv][' + hz + ']', p.eoas[lo].desviaciones[hz]);
                });
            });
        }

        if (autoOn('reflex')) {
            moduloActual = 'reflex';
            ['ipsi', 'contra'].forEach(function (modo) {
                ['od', 'oi'].forEach(function (lado) {
                    (p.reflex[modo][lado] || []).forEach(function (valor, n) {
                        setVal('reflex_' + modo + '[' + lado + '][' + n + ']', valor);
                    });
                });
            });
            ['od', 'oi'].forEach(function (lado) {
                setVal('reflex_type[' + lado + ']', p.reflex.tipo[lado]);
            });
            // La tabla-resumen de reflejos se dibuja desde los inputs.
            if (window.drawReflexPattern) { window.drawReflexPattern(); }
        }

        if (autoOn('recruit')) {
            moduloActual = 'recruit';
            ['od', 'oi'].forEach(function (lado, i) {
                setVal('sisi[' + lado + ']', p.recruit.sisi[i]);
                var chk = campo('recruit[' + lado + ']');
                if (chk && chk.checked !== !!p.recruit.recruit[i]) { marcarTocado(); }
                if (chk) { chk.checked = !!p.recruit.recruit[i]; }
            });
            Object.keys(p.recruit.fowler).forEach(function (freqIdx) {
                setVal('fowler_pattern[' + freqIdx + ']', p.recruit.fowler[freqIdx]);
            });
            DECAY_MODES.forEach(function (modo) {
                ['od', 'oi'].forEach(function (lado) {
                    (p.recruit.decay[modo][lado] || []).forEach(function (valor, n) {
                        setVal(modo + '[' + lado + '][' + n + ']', valor);
                    });
                });
            });
            ['od', 'oi'].forEach(function (lado) {
                (p.recruit.ldl[lado] || []).forEach(function (valor, n) {
                    setVal('ldl[' + lado + '][' + n + ']', valor);
                });
                // Derivado, el LDL siempre está medido: dejarlo en "no
                // medido" esconde justo el hallazgo del reclutamiento.
                var medido = campo('ldl_habilitado[' + lado + ']');
                if (medido) { medido.checked = true; }
            });
            if (window.drawAudiogram) { window.drawAudiogram(); }
        }

        if (autoOn('logo')) {
            moduloActual = 'logo';
            ['od', 'oi'].forEach(function (lado) {
                var lo = lado.toUpperCase();
                setVal('umd_int[' + lado + ']', p.logo[lo].int);
                setVal('umd_pct[' + lado + ']', p.logo[lo].pct);
            });
            if (window.drawLogogram) { window.drawLogogram(); }
        }
        moduloActual = null;

        // La primera proyección es la de abrir el caso: pone en pantalla lo
        // que el caso ya tenía guardado, así que no hay nada que revisar.
        var tabs = Object.keys(tabsTocadas);
        if (tabs.length && !primeraPasada && window.avisarCambioAutomatico) {
            window.avisarCambioAutomatico(tabs, 'el perfil auditivo volvió a derivar');
        }
        primeraPasada = false;
    }

    var pendiente = null;
    /**
     * Devuelve una promesa que se resuelve cuando el formulario YA tiene la
     * proyección encima. El generador la encadena: las ondas del ABR se
     * sortean por patología, y la patología la decide esta proyección.
     */
    function proyectar() {
        // Sin ningún módulo derivado no hay nada que pintar: el formulario
        // es del docente y no se le toca ni un campo.
        if (!MODULOS.some(autoOn)) {
            if (preview) { preview.hidden = true; }
            return Promise.resolve();
        }
        var body = new URLSearchParams();
        body.set('csrf_token', CSRF);
        body.set('payload', JSON.stringify(estado()));
        return fetch('case_project.php', { method: 'POST', body: body })
            .then(function (r) { return r.json(); })
            .then(function (data) { if (data.ok) { hidratar(data.proyeccion); } })
            .catch(function () { /* sin conexión el formulario sigue usable a mano */ });
    }
    function proyectarPronto() {
        clearTimeout(pendiente);
        pendiente = setTimeout(proyectar, 350);
    }
    // Generar el cuadro escribe el audiograma completo y necesita repintar ya.
    window.proyectarPerfil = proyectar;

    document.addEventListener('input', function (e) {
        var id = e.target.id || '';
        var name = e.target.getAttribute('name') || '';
        if (/^(aerea|osea)_/.test(id) || /^perfil\[(od|oi)\]\[cce_pct\]$/.test(name)
            || (e.target.classList && e.target.classList.contains('abr-neural-input'))) {
            proyectarPronto();
        }
    });
    document.addEventListener('change', function (e) {
        var name = e.target.getAttribute('name') || '';
        if (/^perfil\[auto\]\[/.test(name) || /^igualar\[/.test(name)
            || name === 'z_od' || name === 'z_oi'
            || (e.target.classList && e.target.classList.contains('abr-neural-input'))) {
            // Debounce también acá: generar el cuadro enciende las cuatro casillas
            // de un saque y no hacen falta cuatro viajes al servidor.
            proyectarPronto();
        }
    });
    proyectar();
})();
