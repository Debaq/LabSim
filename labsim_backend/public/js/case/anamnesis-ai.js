// Borrador de anamnesis por LLM.
//
// Trae el texto y lo deja en los campos, pero NO lo da por bueno: enciende
// la casilla de verificación y la deja sin tildar. Mientras siga así, el
// servidor no guarda el caso ni la agenda lo cita (CaseCompleteness). El
// modelo puede inventar una cirugía que no existe, y al alumno le llega
// indistinguible de lo que escribió el docente.
(function () {
    var CSRF = window.CASE_CONST.csrf;
    var HIST = window.CASE_CONST.histCheckboxes;
    var FREQS = window.CASE_CONST.freqs;
    var NEURAL_PARAMS = window.CASE_CONST.neuralParams;

    var boton = document.getElementById('anamnesis-ia-btn');
    var estado = document.getElementById('anamnesis-ia-estado');
    var bloque = document.getElementById('anamnesis-ia-verificacion');
    var generado = document.getElementById('anamnesis-ia-generado');
    var generadoEn = document.getElementById('anamnesis-ia-generado-en');
    var verificado = document.getElementById('anamnesis-ia-verificado');
    if (!boton || !bloque || !generado || !verificado) return;

    function campo(name) { return document.querySelector('#case-form [name="' + name + '"]'); }
    function curva(clave, lado) {
        var out = [];
        for (var n = 0; n < FREQS.length; n++) {
            var el = document.getElementById(clave + '_' + lado + '_' + n);
            out.push(el ? (parseInt(el.value, 10) || 0) : 0);
        }
        return out;
    }

    /** Solo los hallazgos: el prompt no ve el resto de la ficha. */
    function estadoClinico() {
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
        var edad = campo('age'), genero = document.querySelector('#case-form [name="gender"]:checked');
        var zOd = campo('z_od'), zOi = campo('z_oi');
        var tinnitus = {};
        ['lateralidad', 'oido', 'predominio', 'ruido'].forEach(function (k) {
            var el = campo('tinnitus[' + k + ']');
            if (el) { tinnitus[k] = el.value; }
        });
        ['pulsatil', 'permanente'].forEach(function (k) {
            var el = campo('tinnitus[' + k + ']');
            if (el && el.checked) { tinnitus[k] = true; }
        });
        return {
            case_id: (campo('case_id') || {}).value || '',
            edad: edad ? parseInt(edad.value, 10) || 0 : 0,
            gender: genero ? parseInt(genero.value, 10) || 0 : 0,
            aerea: { od: curva('aerea', 'od'), oi: curva('aerea', 'oi') },
            osea: { od: curva('osea', 'od'), oi: curva('osea', 'oi') },
            z: { od: zOd ? zOd.value : 'A', oi: zOi ? zOi.value : 'A' },
            perfil: perfil,
            tinnitus: tinnitus
        };
    }

    function aplicar(b) {
        // El relato va a la pestaña Paciente, no a Anamnesis: es historia
        // del paciente, no del caso. Es además el campo que hace útil al
        // borrador -- sin él, un paciente sin antecedentes formales
        // quedaba con la ficha vacía.
        var relato = campo('historia_clinica');
        if (relato && b.historia_clinica) { relato.value = b.historia_clinica; }
        HIST.forEach(function (clave) {
            var chk = campo('hist[' + clave + ']');
            if (chk) { chk.checked = !!b.antecedentes[clave]; }
        });
        ['medicamentos', 'cirugias', 'otros', 'comportamiento'].forEach(function (k) {
            var el = campo(k);
            if (el) { el.value = b[k] || ''; }
        });
        var disp = campo('disposicion');
        if (disp) { disp.value = b.disposicion; }
    }

    boton.addEventListener('click', function () {
        boton.disabled = true;
        // Puede tardar: un modelo de razonamiento genera miles de tokens
        // antes de escribir, y si se queda corto el servidor reintenta.
        estado.textContent = 'Redactando... (puede tardar un minuto o dos)';
        var body = new URLSearchParams();
        body.set('csrf_token', CSRF);
        body.set('payload', JSON.stringify(estadoClinico()));
        fetch('case_anamnesis_ai.php', { method: 'POST', body: body })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (!data.ok) { throw new Error(data.error || 'No se pudo redactar.'); }
                aplicar(data.borrador);
                generado.value = '1';
                if (generadoEn) { generadoEn.value = new Date().toISOString(); }
                // Texto nuevo: nadie lo leyó todavía.
                verificado.checked = false;
                bloque.hidden = false;
                var sinBorrador = document.getElementById('anamnesis-ia-sin-borrador');
                if (sinBorrador) { sinBorrador.hidden = true; }
                // El consumo a la vista: en un modelo de razonamiento el
                // grueso son tokens de pensamiento que no se ven en el
                // texto, y sin esto no hay forma de notar que un borrador
                // costó veinte veces más que otro.
                var u = data.uso || {};
                var costo = u.total
                    ? ' — ' + u.total + ' tokens'
                        + (u.razonamiento ? ' (' + u.razonamiento + ' de razonamiento)' : '')
                        + (u.intentos > 1 ? ', ' + u.intentos + ' intentos' : '')
                    : '';
                estado.textContent = 'Borrador listo' + costo + '.';
                var eco = document.getElementById('anamnesis-ia-estado-eco');
                if (eco) {
                    eco.textContent = 'Borrador recién redactado' + costo
                        + '. Las atenciones previas quedaron en la pestaña Paciente.';
                    eco.hidden = false;
                }
                // El botón vive en "Armado rápido" y el texto que hay que leer
                // está en Anamnesis: sin este salto el docente tilda la
                // verificación sin haber visto nunca lo que el modelo escribió.
                if (window.gotoTab) { window.gotoTab('anamnesis'); }
            })
            .catch(function (err) { estado.textContent = 'Error: ' + err.message; })
            .finally(function () { boton.disabled = false; });
    });
})();
