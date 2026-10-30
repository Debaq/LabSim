// Ficha Nariz, tarjeta Olfato: la olfatometría del caso (cases.data['OLFATO'])
// en un hidden.
//
// Todo el estado vive en <input name="olfato_json"> (#olfato-json, lo pone
// case_create.php en el formulario para todos). La casilla apagada lo deja
// vacío, y vacío es "este caso no trae olfatometría". Encendida, el hidden
// lleva {lados: {D: {T, D, I}, I: {T, D, I}}, conducta, preparacion}, lo que
// lee la app (nasal.olfatometria.desde_caso).
//
// Las normas (percentil 10 por grupo de edad, cortes del TDI) salen de
// window.CASE_CONST.olfato.normas, las mismas de la app. Nada se bloquea: el
// servidor valida al guardar (CaseForm::parseOlfato).
(function () {
    var hidden = document.getElementById('olfato-json');
    var presente = document.getElementById('olfato-presente');
    var campos = document.getElementById('olfato-campos');
    var selector = document.getElementById('olfato-cuadro');
    var resumen = document.getElementById('olfato-resumen');
    var igual = document.getElementById('olfato-igual');
    var conf = window.CASE_CONST && window.CASE_CONST.olfato;
    if (!hidden || !presente || !campos || !selector || !conf) return;

    function $(id) { return document.getElementById('olfato-' + id); }

    // Cuadros de partida: [clave, nombre, D:[T,D,I], I:[T,D,I], conducta]
    var CUADROS = [
        ['normosmia', 'Normosmia', [10, 13, 14], [10, 13, 14], 'buena'],
        ['hiposmia', 'Hiposmia', [6, 9, 10], [6, 9, 10], 'buena'],
        ['anosmia', 'Anosmia funcional', [1, 5, 4], [1, 5, 4], 'buena'],
        ['asimetrica', 'Asimétrica (un lado peor)', [10, 13, 14], [3, 7, 6], 'buena'],
        ['exagera', 'Exagera la pérdida', [10, 13, 14], [10, 13, 14], 'exagera']
    ];

    function leeNum(id) { var v = parseFloat($(id).value); return isNaN(v) ? null : v; }
    function num(v, d) { return v == null || isNaN(v) ? '—' : v.toFixed(d).replace('.', ','); }

    function aDatos() {
        var lados = {};
        ['D', 'I'].forEach(function (l) {
            lados[l] = { T: leeNum(l + '-T'), D: leeNum(l + '-D'), I: leeNum(l + '-I') };
        });
        return { lados: lados, conducta: $('conducta').value, preparacion: $('preparacion').value };
    }

    function pon(id, v) { $(id).value = v == null ? '' : v; }

    function aCampos(d) {
        ['D', 'I'].forEach(function (l) {
            var x = (d.lados || {})[l] || {};
            pon(l + '-T', x.T);
            pon(l + '-D', x.D);
            pon(l + '-I', x.I);
        });
        $('conducta').value = d.conducta || 'buena';
        $('preparacion').value = d.preparacion || 'ok';
    }

    function completo(x) { return x && x.T != null && x.D != null && x.I != null; }
    function tdi(x) { return x.T + x.D + x.I; }

    function categoria(v) {
        var c = conf.normas.cortes;
        for (var i = 0; i < c.length; i++) { if (v <= c[i][0]) return c[i][2]; }
        return c[c.length - 1][2];
    }

    function grupoEdad() {
        var edad = parseFloat((document.getElementById('patient-age') || {}).value);
        if (isNaN(edad)) return null;
        var g = conf.normas.grupos;
        for (var i = 0; i < g.length; i++) {
            if (edad >= g[i][0] && edad < g[i][1] + 1) return g[i];
        }
        return null;
    }

    function pintaResumen() {
        var d = aDatos(), D = d.lados.D, I = d.lados.I;
        var partes = [];
        if (completo(D)) partes.push('TDI narina derecha: ' + num(tdi(D), 1) + ' (' + categoria(tdi(D)) + ').');
        if (completo(I)) partes.push('TDI narina izquierda: ' + num(tdi(I), 1) + ' (' + categoria(tdi(I)) + ').');
        if (completo(D) && completo(I)) {
            var b = {
                T: Math.max(D.T, I.T), D: Math.max(D.D, I.D), I: Math.max(D.I, I.I)
            };
            partes.push('Con las dos narinas (mejor lado de cada puntaje): T ' + num(b.T, 1) + ', D ' + num(b.D, 0) +
                ', I ' + num(b.I, 0) + ', TDI ' + num(tdi(b), 1) + ', ' + categoria(tdi(b)) + '.');
        }
        var g = grupoEdad();
        partes.push(g ? 'Percentil 10 del grupo de ' + g[0] + ' a ' + g[1] + ' años: ' + num(g[3], 2) + ' (media ' + num(g[2], 2) + ').'
            : 'Para ver el percentil 10 hace falta la edad en la ficha Paciente (desde 5 años).');
        resumen.textContent = partes.join(' ');
    }

    function guarda() {
        var nuevo = presente.checked ? JSON.stringify(aDatos()) : '';
        if (hidden.value !== nuevo) {
            hidden.value = nuevo;
            hidden.dispatchEvent(new Event('change', { bubbles: true }));
        }
        pintaResumen();
    }

    function copiaDerecha() {
        ['T', 'D', 'I'].forEach(function (k) { $('I-' + k).value = $('D-' + k).value; });
    }

    function cargar() {
        var c = CUADROS.filter(function (x) { return x[0] === selector.value; })[0];
        if (!c) return;
        aCampos({
            lados: { D: { T: c[2][0], D: c[2][1], I: c[2][2] }, I: { T: c[3][0], D: c[3][1], I: c[3][2] } },
            conducta: c[4], preparacion: $('preparacion').value
        });
        igual.checked = c[2].join() === c[3].join();
        guarda();
    }

    CUADROS.forEach(function (c) {
        var o = document.createElement('option');
        o.value = c[0];
        o.textContent = c[1];
        selector.appendChild(o);
    });
    var guardado = null;
    try { guardado = hidden.value ? JSON.parse(hidden.value) : null; } catch (e) { guardado = null; }
    presente.checked = !!guardado;
    if (guardado) {
        aCampos(guardado);
        var d0 = guardado.lados || {};
        igual.checked = !!(d0.D && d0.I && ['T', 'D', 'I'].every(function (k) { return d0.D[k] === d0.I[k]; }));
    }
    campos.style.display = presente.checked ? '' : 'none';

    presente.addEventListener('change', function () {
        campos.style.display = presente.checked ? '' : 'none';
        if (presente.checked && $('D-T').value === '') {
            selector.value = 'normosmia';
            cargar();
        }
        guarda();
    });
    $('cargar').addEventListener('click', cargar);
    igual.addEventListener('change', function () {
        if (igual.checked) copiaDerecha();
        guarda();
    });
    campos.addEventListener('input', function (e) {
        if (igual.checked && /^olfato-D-/.test(e.target.id)) copiaDerecha();
        guarda();
    });
    campos.addEventListener('change', function (e) { if (e.target !== selector) guarda(); });
    var edad = document.getElementById('patient-age');
    if (edad) edad.addEventListener('input', pintaResumen);
    pintaResumen();
})();
