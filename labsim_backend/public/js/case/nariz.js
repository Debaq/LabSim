// Ficha Nariz: el paciente de RinoSim (cases.data['NASAL']) en un hidden.
//
// Todo el estado vive en <input name="nasal_json"> (#nasal-json, lo pone
// case_create.php en el formulario para todos). La casilla apagada lo deja
// vacío, y vacío es "este caso no trae nariz". Encendida, el hidden lleva el
// paciente entero: {nombre, cuadro, semilla, lados: {D, I}, ciclo,
// perforacion}, el mismo shape que RinoSim y que lee la app
// (nasal.sesion.desde_caso). La tabla de parámetros y los cuadros salen de
// window.CASE_CONST.nasalCuadros, que genera scripts/nasal/cuadros_backend.py.
//
// Nada se bloquea: cualquier número se puede escribir; el servidor valida el
// rango al guardar (CaseForm::parseNasal) y avisa cuál no cierra.
(function () {
    var hidden = document.getElementById('nasal-json');
    var presente = document.getElementById('nariz-presente');
    var campos = document.getElementById('nariz-campos');
    var selector = document.getElementById('nariz-cuadro');
    var tabla = document.getElementById('nariz-parametros');
    var descripcion = document.getElementById('nariz-descripcion');
    var rotuloNombre = document.getElementById('nariz-nombre');
    var datos = window.CASE_CONST && window.CASE_CONST.nasalCuadros;
    if (!hidden || !presente || !campos || !selector || !tabla || !datos || !datos.cuadros) return;

    var LADOS = [['D', 'FND'], ['I', 'FNI']];
    var paciente = null;      // el paciente en edición; null con la casilla apagada
    var variante = {};        // cuadro -> índice de la última variante mostrada

    function clona(o) { return JSON.parse(JSON.stringify(o)); }

    function lee(obj, ruta) {
        return ruta.split('.').reduce(function (o, k) { return o == null ? o : o[k]; }, obj);
    }

    function escribe(obj, ruta, valor) {
        var ks = ruta.split('.');
        var ultimo = ks.pop();
        ks.forEach(function (k) { obj = obj[k]; });
        obj[ultimo] = valor;
    }

    function escapa(t) {
        return String(t).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/"/g, '&quot;');
    }

    // Al hidden: el paciente, o vacío con la casilla apagada. Se dispara
    // 'change' para que el aviso de cambios sin guardar se entere.
    function guarda() {
        var nuevo = presente.checked && paciente ? JSON.stringify(paciente) : '';
        if (hidden.value === nuevo) return;
        hidden.value = nuevo;
        hidden.dispatchEvent(new Event('change', { bubbles: true }));
    }

    function dibujaTabla() {
        var filas = datos.parametros.map(function (d) {
            return '<tr><td class="side-label">' + escapa(d.nombre) + '</td>' + LADOS.map(function (l) {
                var v = lee(paciente.lados[l[0]], d.ruta);
                return '<td><input type="number" data-lado="' + l[0] + '" data-ruta="' + d.ruta + '" min="' + d.min +
                    '" max="' + d.max + '" step="' + d.paso + '" value="' + redondea(v) + '"></td>';
            }).join('') + '</tr>';
        });
        var extras = datos.extras.map(function (d) {
            return '<tr><td class="side-label">' + escapa(d.nombre) + '</td><td colspan="2"><input type="number" data-ruta="' +
                d.ruta + '" min="' + d.min + '" max="' + d.max + '" step="' + d.paso + '" value="' + redondea(lee(paciente, d.ruta)) + '"></td></tr>';
        });
        tabla.innerHTML = '<table class="grid-table"><thead><tr><th class="side-label">Parámetro</th><th>FND</th><th>FNI</th></tr></thead><tbody>' +
            filas.join('') + extras.join('') + '</tbody></table>';
    }

    function redondea(v) { return typeof v === 'number' ? +v.toFixed(3) : ''; }

    function dibuja() {
        campos.classList.toggle('bloque-apagado', !presente.checked);
        if (!paciente) { tabla.innerHTML = ''; rotuloNombre.textContent = ''; descripcion.textContent = ''; return; }
        var c = datos.cuadros[selector.value];
        descripcion.textContent = c ? c.descripcion : '';
        rotuloNombre.textContent = paciente.nombre +
            (paciente.semilla != null && paciente.semilla !== '' ? ' (variante ' + paciente.semilla + ')' : '');
        dibujaTabla();
    }

    function carga(p) {
        paciente = clona(p);
        dibuja();
        guarda();
    }

    function cuadroActual() { return datos.cuadros[selector.value]; }

    function talCual() { if (cuadroActual()) carga(cuadroActual().tipo); }

    function otraVariante() {
        var c = cuadroActual();
        if (!c || !c.variantes.length) return;
        var i = ((variante[selector.value] == null ? -1 : variante[selector.value]) + 1) % c.variantes.length;
        variante[selector.value] = i;
        carga(c.variantes[i]);
    }

    // Opciones: los cuadros de ejemplo. Si el caso trae un paciente con
    // cuadro desconocido, queda el primero seleccionado sin tocar lo guardado.
    Object.keys(datos.cuadros).forEach(function (clave) {
        var o = document.createElement('option');
        o.value = clave;
        o.textContent = datos.cuadros[clave].nombre;
        selector.appendChild(o);
    });

    // Hidratar desde lo guardado (data['NASAL'] -> hidden); si no hay nada,
    // la casilla queda apagada y el hidden vacío.
    var guardado = null;
    try { guardado = hidden.value ? JSON.parse(hidden.value) : null; } catch (e) { guardado = null; }
    if (guardado && guardado.lados) {
        presente.checked = true;
        paciente = guardado;
        if (guardado.cuadro && datos.cuadros[guardado.cuadro]) selector.value = guardado.cuadro;
    }
    dibuja();

    presente.addEventListener('change', function () {
        // Primera vez encendida: parte del cuadro elegido tal cual.
        if (presente.checked && !paciente) { talCual(); return; }
        dibuja();
        guarda();
    });

    selector.addEventListener('change', function () {
        presente.checked = true;
        talCual();
    });
    document.getElementById('nariz-variante').addEventListener('click', function () {
        presente.checked = true;
        otraVariante();
    });
    document.getElementById('nariz-tal-cual').addEventListener('click', function () {
        presente.checked = true;
        talCual();
    });

    // Tocar un número: el paciente pasa a "<cuadro> (editado)", como en
    // RinoSim. Un campo vacío o no numérico no se escribe (el valor anterior
    // sigue en el hidden).
    tabla.addEventListener('input', function (e) {
        var input = e.target;
        if (!input.matches || !input.matches('input[data-ruta]') || !paciente) return;
        var v = parseFloat(input.value);
        if (!isFinite(v)) return;
        if (input.dataset.lado) escribe(paciente.lados[input.dataset.lado], input.dataset.ruta, v);
        else escribe(paciente, input.dataset.ruta, v);
        var c = datos.cuadros[paciente.cuadro];
        paciente.nombre = (c ? c.nombre : 'Paciente') + ' (editado)';
        rotuloNombre.textContent = paciente.nombre;
        guarda();
    });
})();
