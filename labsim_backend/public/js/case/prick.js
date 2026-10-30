// Ficha Nariz, tarjeta Prick: el prick test del caso (cases.data['PRICK'])
// en un hidden.
//
// Todo el estado vive en <input name="prick_json"> (#prick-json, lo pone
// case_create.php en el formulario para todos). La casilla apagada lo deja
// vacío, y vacío es "este caso no trae prick". Encendida, el hidden lleva
// {histamina, dermografismo, alergenos: {clave: mm}, farmaco: null |
// {clave, horas}}, lo que lee la app (nasal.prick.desde_caso).
//
// Las claves y los nombres salen de window.CASE_CONST.prick (los de la app).
// Nada se bloquea: el servidor valida al guardar (CaseForm::parsePrick).
(function () {
    var hidden = document.getElementById('prick-json');
    var presente = document.getElementById('prick-presente');
    var campos = document.getElementById('prick-campos');
    var selector = document.getElementById('prick-cuadro');
    var selFarmaco = document.getElementById('prick-farmaco');
    var lista = document.getElementById('prick-alergenos');
    var conf = window.CASE_CONST && window.CASE_CONST.prick;
    if (!hidden || !presente || !campos || !selector || !selFarmaco || !lista || !conf) return;

    function $(id) { return document.getElementById('prick-' + id); }

    // Cuadros de partida: [clave, nombre, {histamina, dermografismo, alergenos, farmaco}]
    var CUADROS = [
        ['sin', 'Sin sensibilización', { histamina: 6, dermografismo: 0, alergenos: {} }],
        ['acaros', 'Ácaros', { histamina: 6, dermografismo: 0, alergenos: { dpte: 8, dfar: 6 } }],
        ['h29', 'Ácaros + gato + pastos (ejemplo de H29)', {
            histamina: 6, dermografismo: 0,
            alergenos: { dpte: 8, dfar: 6, gato: 3, perro: 2, pastos: 5, alternaria: 0 }
        }],
        ['poli', 'Polisensibilizado', {
            histamina: 7, dermografismo: 0,
            alergenos: { dpte: 9, dfar: 8, gato: 6, perro: 4, pastos: 8, olivo: 6, platano: 5, alternaria: 4, parietaria: 5 }
        }],
        ['antihistaminico', 'Antihistamínico sin suspender (cetirizina hace 24 h)', {
            histamina: 6, dermografismo: 0, alergenos: { dpte: 8, dfar: 6 },
            farmaco: { clave: 'cetirizina', horas: 24 }
        }],
        ['dermografismo', 'Dermografismo', { histamina: 6, dermografismo: 4, alergenos: { dpte: 5 } }]
    ];

    function leeNum(id) { var v = parseFloat($(id).value); return isNaN(v) ? null : v; }
    function pon(id, v) { $(id).value = v == null ? '' : v; }

    // Select de fármacos y una fila por alérgeno.
    var o0 = document.createElement('option');
    o0.value = '';
    o0.textContent = 'Ninguno';
    selFarmaco.appendChild(o0);
    Object.keys(conf.farmacos).forEach(function (k) {
        var o = document.createElement('option');
        o.value = k;
        o.textContent = conf.farmacos[k];
        selFarmaco.appendChild(o);
    });
    Object.keys(conf.alergenos).forEach(function (k) {
        var l = document.createElement('label');
        l.textContent = conf.alergenos[k] + ' (mm) ';
        var i = document.createElement('input');
        i.type = 'number';
        i.step = '0.5';
        i.min = '0';
        i.max = '25';
        i.id = 'prick-a-' + k;
        l.appendChild(i);
        lista.appendChild(l);
    });

    function aDatos() {
        var alergenos = {};
        Object.keys(conf.alergenos).forEach(function (k) {
            var v = leeNum('a-' + k);
            alergenos[k] = v == null ? 0 : v;
        });
        var d = { histamina: leeNum('histamina'), dermografismo: leeNum('dermografismo') || 0, alergenos: alergenos, farmaco: null };
        if (selFarmaco.value) d.farmaco = { clave: selFarmaco.value, horas: leeNum('horas') };
        return d;
    }

    function aCampos(d) {
        pon('histamina', d.histamina);
        pon('dermografismo', d.dermografismo);
        Object.keys(conf.alergenos).forEach(function (k) {
            var v = (d.alergenos || {})[k];
            pon('a-' + k, v ? v : 0);
        });
        selFarmaco.value = d.farmaco && d.farmaco.clave ? d.farmaco.clave : '';
        pon('horas', d.farmaco ? d.farmaco.horas : null);
    }

    function guarda() {
        var nuevo = presente.checked ? JSON.stringify(aDatos()) : '';
        if (hidden.value !== nuevo) {
            hidden.value = nuevo;
            hidden.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    function cargar() {
        var c = CUADROS.filter(function (x) { return x[0] === selector.value; })[0];
        if (!c) return;
        aCampos(c[2]);
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
    if (guardado) aCampos(guardado);
    campos.style.display = presente.checked ? '' : 'none';

    presente.addEventListener('change', function () {
        campos.style.display = presente.checked ? '' : 'none';
        if (presente.checked && $('histamina').value === '') {
            selector.value = 'sin';
            cargar();
        }
        guarda();
    });
    $('cargar').addEventListener('click', cargar);
    campos.addEventListener('input', guarda);
    campos.addEventListener('change', function (e) { if (e.target !== selector) guarda(); });
})();
