// Resumen: qué quedó cargado en cada ficha, y qué fichas dio por revisadas
// el docente antes de guardar (ver views/case/_resumen.php y src/CaseReview.php).
//
// El estado de cada fila se lee del FORMULARIO, no del caso guardado: lo que
// hay que revisar es lo que está en pantalla ahora, que después de "Generar
// caso" ya no es lo que tiene la base. Por eso vive acá y no en PHP.
//
// Los textos son deliberadamente cortos --lo justo para reconocer la ficha y
// darse cuenta de que algo quedó en el default-- y no reemplazan abrirla: el
// botón "Ir a la ficha" está en cada fila para eso.
(function () {
    var form = document.getElementById('case-form');
    var panel = document.querySelector('.tab-panel[data-tab="resumen"]');
    if (!form || !panel) { return; }

    var CONST = window.CASE_CONST || {};
    var FREQS = CONST.freqs || [];
    var GRADE_FREQS = CONST.gradeFreqs || [];

    function campo(name) { return form.querySelector('[name="' + name + '"]'); }
    function valor(name) { var el = campo(name); return el ? el.value.trim() : ''; }
    function numero(name) { var el = campo(name); return el ? parseFloat(el.value) : NaN; }
    function tildado(name) { var el = campo(name); return !!(el && el.checked); }
    /** El texto de la opción elegida ("Timpanograma B"), no su clave. */
    function etiqueta(name) {
        var el = campo(name);
        if (!el || !el.options) { return ''; }
        var opt = el.options[el.selectedIndex];
        return opt ? opt.textContent.trim() : '';
    }
    function porOido(fn) { return 'OD ' + fn('od') + ' · OI ' + fn('oi'); }

    /** Promedio tonal aéreo de las frecuencias del grado (BIAP), por oído. */
    function pta(lado) {
        var suma = 0, n = 0;
        GRADE_FREQS.forEach(function (hz) {
            var idx = FREQS.indexOf(hz);
            if (idx < 0) { return; }
            var db = numero('aerea[' + lado + '][' + idx + ']');
            if (!isNaN(db)) { suma += db; n++; }
        });
        return n ? Math.round(suma / n) + ' dB' : 's/d';
    }

    // Una función por ficha: devuelve la línea que se muestra bajo su nombre.
    var ESTADO = {
        paciente: function () {
            // Al crear el nombre va partido (nombre1/nombre2); al editar es
            // uno solo y viene del paciente, que ya existe en la base.
            var nombre = (valor('nombre1') + ' ' + valor('apellido1')).trim()
                || (valor('nombre') + ' ' + valor('apellido')).trim();
            var edad = valor('age');
            var sexo = form.querySelector('[name="gender"]:checked');
            var partes = [nombre || 'sin nombre'];
            partes.push(edad === '' ? 'sin edad' : edad + ' años');
            partes.push(sexo && sexo.value === '1' ? 'mujer' : 'hombre');
            if (valor('historia_clinica')) { partes.push('con historia clínica'); }
            return partes.join(', ');
        },
        sala: function () {
            var filas = form.querySelectorAll('[name="sala_rol[]"]').length;
            // El informante es un radio por persona (el del paciente vale
            // "p1"); el nombre y el rol viven en la fila que lo contiene.
            var elegido = form.querySelector('[name="sala_informante"]:checked');
            var quien = 'el paciente';
            if (elegido && elegido.value !== 'p1') {
                var fila = elegido.closest('.sala-row');
                var nombre = fila ? fila.querySelector('[name="sala_nombre[]"]') : null;
                var rol = fila ? fila.querySelector('[name="sala_rol[]"]') : null;
                quien = (nombre && nombre.value.trim())
                    || (rol && rol.options[rol.selectedIndex].textContent.trim())
                    || 'un acompañante';
            }
            if (!filas) { return 'El paciente viene solo'; }
            return filas + (filas === 1 ? ' acompañante' : ' acompañantes') +
                ', cuenta la historia ' + quien;
        },
        perfil: function () {
            var autos = [];
            [['abr', 'ABR'], ['eoas', 'OEA'], ['reflex', 'reflejos'],
             ['recruit', 'supraliminares'], ['logo', 'logoaudiometría']]
                .forEach(function (par) {
                    if (tildado('perfil[auto][' + par[0] + ']')) { autos.push(par[1]); }
                });
            return 'Componente coclear ' + porOido(function (lado) {
                return valor('perfil[' + lado + '][cce_pct]') + ' %';
            }) + ' — ' + (autos.length ? 'deriva ' + autos.join(', ') : 'no deriva nada');
        },
        audiometria: function () {
            return 'Promedio tonal aéreo ' + porOido(pta);
        },
        otoscopia: function () {
            var fases = form.querySelectorAll('[name^="otoscopia[texto]"]').length || 1;
            var conTexto = 0;
            form.querySelectorAll('[name^="otoscopia[texto]"]').forEach(function (el) {
                if (el.value.trim()) { conTexto++; }
            });
            return fases + (fases === 1 ? ' fase, ' : ' fases, ') +
                (conTexto ? conTexto + ' con descripción escrita' : 'sin describir');
        },
        timpanometria: function () {
            return 'Curva ' + porOido(function (lado) { return valor('z_' + lado); }) +
                ' — trompa ' + porOido(function (lado) { return etiqueta('etf_' + lado); });
        },
        abr: function () {
            return porOido(function (lado) { return etiqueta('abr[' + lado + '][type]'); });
        },
        eoas: function () {
            return porOido(function (lado) { return etiqueta('eoas[' + lado + '][type]'); });
        },
        vemp: function () {
            return porOido(function (lado) { return etiqueta('vemp[' + lado + '][type]'); });
        },
        tinnitus: function () {
            if (!tildado('tinnitus[presente]')) { return 'Sin acúfeno'; }
            return 'Con acúfeno ' + etiqueta('tinnitus[lateralidad]').toLowerCase() +
                ', ' + etiqueta('tinnitus[ruido]').toLowerCase();
        },
        anamnesis: function () {
            var antecedentes = form.querySelectorAll('[name^="hist["]:checked').length;
            var texto = (valor('medicamentos') + valor('cirugias') + valor('otros')).length;
            var ia = campo('anamnesis_ia[generado]');
            var partes = [antecedentes + (antecedentes === 1 ? ' antecedente' : ' antecedentes')];
            partes.push(texto ? texto + ' caracteres escritos' : 'sin texto libre');
            if (ia && ia.value) {
                partes.push(tildado('anamnesis_ia[verificado]')
                    ? 'borrador de IA verificado'
                    : 'borrador de IA SIN verificar');
            }
            return partes.join(', ');
        }
    };

    var checks = Array.prototype.slice.call(panel.querySelectorAll('.resumen-check'));
    var contador = document.getElementById('resumen-contador');

    function pintarEstados() {
        panel.querySelectorAll('.resumen-estado').forEach(function (el) {
            var fn = ESTADO[el.dataset.resumen];
            if (!fn) { return; }
            try {
                el.textContent = fn();
            } catch (e) {
                // Una ficha que no se pudo leer no puede romper el Resumen
                // entero: la fila queda sin texto y el docente la abre.
                el.textContent = '';
            }
        });
    }

    function pintarContador() {
        var faltan = checks.filter(function (c) { return !c.checked; });
        panel.querySelectorAll('.resumen-row').forEach(function (row) {
            var check = row.querySelector('.resumen-check');
            row.classList.toggle('revisada', !!(check && check.checked));
        });
        if (!contador) { return; }
        if (!faltan.length) {
            contador.textContent = 'Las ' + checks.length + ' fichas revisadas: el caso se puede guardar.';
            contador.classList.add('completo');
            return;
        }
        contador.textContent = 'Faltan ' + faltan.length + ' de ' + checks.length +
            ': ' + faltan.map(function (c) {
                return c.parentNode.querySelector('.resumen-label').textContent;
            }).join(', ') + '.';
        contador.classList.remove('completo');
    }

    /**
     * Editar una ficha ya revisada la destilda.
     *
     * Lo revisado es una VERSIÓN de la ficha, no la ficha: si se tilda
     * Audiometría y después se corrige un umbral, nadie miró ese umbral. Sin
     * esto la tilde se vuelve un trámite que se hace una vez al principio.
     */
    function alEditar(e) {
        var panelTocado = e.target.closest ? e.target.closest('.tab-panel') : null;
        if (!panelTocado || panelTocado === panel) { return; }
        var check = panel.querySelector('.resumen-check[data-tab="' + panelTocado.dataset.tab + '"]');
        if (check && check.checked) {
            check.checked = false;
            pintarContador();
        }
    }

    /** Generar un caso nuevo destilda todo: es otro caso (ver generator.js). */
    window.resumenDestildarTodo = function () {
        checks.forEach(function (c) { c.checked = false; });
        pintarEstados();
        pintarContador();
    };

    form.addEventListener('input', function (e) { alEditar(e); pintarEstados(); });
    form.addEventListener('change', function (e) { alEditar(e); pintarEstados(); });
    checks.forEach(function (c) { c.addEventListener('change', pintarContador); });

    // Intentar guardar con fichas sin revisar manda al Resumen en vez de ir
    // al servidor a que lo rechace: es el mismo criterio que valida CaseForm,
    // pero sin perder el viaje.
    form.addEventListener('submit', function (e) {
        if (checks.every(function (c) { return c.checked; })) { return; }
        e.preventDefault();
        if (window.gotoTab) { window.gotoTab('resumen'); }
        pintarContador();
    });

    // Si el servidor devolvió el formulario porque faltaba revisar, esta es
    // la pestaña donde está lo que hay que hacer.
    if (document.querySelector('.pendientes-card [data-goto-tab="resumen"]') && window.gotoTab) {
        window.gotoTab('resumen');
    }

    pintarEstados();
    pintarContador();
})();
