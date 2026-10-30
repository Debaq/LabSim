// Ficha Nariz, tarjeta Pulmón: la espirometría del caso (cases.data['ESPIRO'])
// en un hidden.
//
// Todo el estado vive en <input name="espiro_json"> (#espiro-json, lo pone
// case_create.php en el formulario para todos). La casilla apagada lo deja
// vacío, y vacío es "este caso no trae espirometría". Encendida, el hidden
// lleva {talla, peso, pre: {fvc, fev1, pef}, bd?, tope_e, tope_i,
// colaboracion}, lo que lee la app (nasal.espirometria.desde_caso).
//
// Los previstos salen de GLI-2012 (window.CASE_CONST.espiro.gli, los mismos
// coeficientes que la app) con el sexo y la edad de la ficha Paciente. Nada
// se bloquea: el servidor valida al guardar (CaseForm::parseEspiro).
(function () {
    var hidden = document.getElementById('espiro-json');
    var presente = document.getElementById('pulmon-presente');
    var campos = document.getElementById('pulmon-campos');
    var selector = document.getElementById('pulmon-cuadro');
    var previstos = document.getElementById('pulmon-previstos');
    var conf = window.CASE_CONST && window.CASE_CONST.espiro;
    if (!hidden || !presente || !campos || !selector || !conf) return;

    function $(id) { return document.getElementById('pulmon-' + id); }

    // Cuadros de partida: fracción del previsto (FVC, FEV1) y del PEF de
    // referencia (2 × FEV1 previsto); bd igual; topes en L/s.
    var CUADROS = [
        ['normal', 'Función normal', { pre: [1.0, 1.0, 1.0] }],
        ['asma', 'Obstrucción con respuesta al broncodilatador', { pre: [0.92, 0.72, 0.75], bd: [0.97, 0.86, 0.9] }],
        ['epoc', 'Obstrucción sin respuesta significativa', { pre: [0.85, 0.55, 0.5], bd: [0.88, 0.59, 0.53] }],
        ['restriccion', 'Volúmenes bajos con razón conservada', { pre: [0.65, 0.68, 0.8] }],
        ['mixto', 'Obstrucción con volúmenes bajos', { pre: [0.65, 0.45, 0.5] }],
        ['fija', 'Tope de flujo espiratorio e inspiratorio (fija)', { pre: [1.0, 0.95, 1.0], tope_e: 3.2, tope_i: 3.0 }],
        ['extratoracica', 'Tope de flujo inspiratorio (variable extratorácica)', { pre: [1.0, 1.0, 1.0], tope_i: 2.5 }],
        ['intratoracica', 'Tope de flujo espiratorio (variable intratorácica)', { pre: [1.0, 0.95, 1.0], tope_e: 3.0 }]
    ];

    // --- GLI-2012 (nasal/espirometria.lms) -----------------------------
    function lms(sexo, par, edad, talla) {
        var d = conf.gli[sexo + '_' + par];
        if (!d) return null;
        var c = d.c;
        edad = Math.min(Math.max(edad, 3), 95);
        var i = (edad - 3) / 0.25;
        var i0 = Math.min(Math.floor(i), d.L.length - 2);
        var fr = i - i0;
        function sp(k) { return d[k][i0] + (d[k][i0 + 1] - d[k][i0]) * fr; }
        var L = c.q0 + c.q1 * Math.log(edad) + sp('L');
        var M = Math.exp(c.a0 + c.a1 * Math.log(talla) + c.a2 * Math.log(edad) + sp('M'));
        var S = Math.exp(c.p0 + c.p1 * Math.log(edad) + sp('S'));
        return { L: L, M: M, S: S };
    }
    function lin(p) { return p.M * Math.pow(1 + p.L * p.S * -1.645, 1 / p.L); }
    function z(p, v) { return (Math.pow(v / p.M, p.L) - 1) / (p.L * p.S); }

    function paciente() {
        var edad = parseFloat((document.getElementById('patient-age') || {}).value);
        var g = document.querySelector('input[name="gender"]:checked');
        var talla = parseFloat($('talla').value);
        return { sexo: g && g.value === '1' ? 'F' : 'M', edad: edad, talla: talla };
    }

    function prevs() {
        var p = paciente();
        if (!(p.edad >= 3) || !(p.talla > 0)) return null;
        var out = {};
        ['FVC', 'FEV1', 'FEV1FVC'].forEach(function (par) { out[par] = lms(p.sexo, par, p.edad, p.talla); });
        return out;
    }

    function num(v, d) { return v == null || isNaN(v) ? '—' : v.toFixed(d).replace('.', ','); }
    function leeNum(id) { var v = parseFloat($(id).value); return isNaN(v) ? null : v; }

    // --- hidden <-> campos ---------------------------------------------
    function aDatos() {
        var d = {
            talla: leeNum('talla'), peso: leeNum('peso'),
            pre: { fvc: leeNum('pre-fvc'), fev1: leeNum('pre-fev1'), pef: leeNum('pre-pef') },
            tope_e: leeNum('tope-e'), tope_i: leeNum('tope-i'),
            colaboracion: $('colaboracion').value
        };
        var bd = { fvc: leeNum('bd-fvc'), fev1: leeNum('bd-fev1'), pef: leeNum('bd-pef') };
        if (bd.fvc != null || bd.fev1 != null || bd.pef != null) d.bd = bd;
        return d;
    }

    function guarda() {
        var nuevo = presente.checked ? JSON.stringify(aDatos()) : '';
        if (hidden.value !== nuevo) {
            hidden.value = nuevo;
            hidden.dispatchEvent(new Event('change', { bubbles: true }));
        }
        pintaPrevistos();
    }

    function pon(id, v, d) { $(id).value = v == null ? '' : (+v).toFixed(d); }

    function aCampos(d) {
        pon('talla', d.talla, 0);
        pon('peso', d.peso, 0);
        ['pre', 'bd'].forEach(function (f) {
            var x = d[f] || {};
            pon(f + '-fvc', x.fvc, 2);
            pon(f + '-fev1', x.fev1, 2);
            pon(f + '-pef', x.pef, 1);
        });
        pon('tope-e', d.tope_e, 1);
        pon('tope-i', d.tope_i, 1);
        $('colaboracion').value = d.colaboracion || 'buena';
    }

    function pintaPrevistos() {
        var p = prevs();
        if (!p) {
            previstos.textContent = 'Para ver los previstos hacen falta la edad (ficha Paciente, desde 3 años) y la talla.';
            return;
        }
        var partes = ['Previstos GLI-2012 caucásico: FVC ' + num(p.FVC.M, 2) + ' L (LIN ' + num(lin(p.FVC), 2) +
            '), FEV1 ' + num(p.FEV1.M, 2) + ' L (LIN ' + num(lin(p.FEV1), 2) + '), FEV1/FVC ' +
            num(p.FEV1FVC.M * 100, 1) + ' % (LIN ' + num(lin(p.FEV1FVC) * 100, 1) + ').'];
        ['pre', 'bd'].forEach(function (f) {
            var fvc = leeNum(f + '-fvc'), fev1 = leeNum(f + '-fev1');
            if (fvc && fev1) {
                partes.push((f === 'pre' ? 'Antes' : 'Con broncodilatador') + ': z FVC ' + num(z(p.FVC, fvc), 2) +
                    ', z FEV1 ' + num(z(p.FEV1, fev1), 2) + ', z FEV1/FVC ' + num(z(p.FEV1FVC, fev1 / fvc), 2) + '.');
            }
        });
        var a = leeNum('pre-fev1'), b = leeNum('bd-fev1');
        if (a && b) {
            partes.push('Cambio del FEV1: ' + num((b - a) * 100 / p.FEV1.M, 1) + ' % del previsto.');
        }
        previstos.textContent = partes.join(' ');
    }

    function cargar() {
        var p = prevs();
        if (!p) { pintaPrevistos(); return; }
        var cuadro = CUADROS.filter(function (c) { return c[0] === selector.value; })[0];
        if (!cuadro) return;
        var k = cuadro[2];
        function fila(fr) {
            var fvc = p.FVC.M * fr[0];
            var fev1 = Math.min(p.FEV1.M * fr[1], fvc * 0.97);
            return { fvc: +fvc.toFixed(2), fev1: +fev1.toFixed(2), pef: +(2 * p.FEV1.M * fr[2]).toFixed(1) };
        }
        var d = aDatos();
        d.pre = fila(k.pre);
        delete d.bd;
        if (k.bd) d.bd = fila(k.bd);
        d.tope_e = k.tope_e || null;
        d.tope_i = k.tope_i || null;
        aCampos(d);
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
        if (presente.checked && !$('talla').value) {
            var g = document.querySelector('input[name="gender"]:checked');
            $('talla').value = g && g.value === '1' ? 160 : 172;
            $('peso').value = g && g.value === '1' ? 62 : 75;
            selector.value = 'normal';
            cargar();
        }
        guarda();
    });
    document.getElementById('pulmon-cargar').addEventListener('click', cargar);
    campos.addEventListener('input', guarda);
    campos.addEventListener('change', function (e) { if (e.target !== selector) guarda(); });
    ['patient-age'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) el.addEventListener('input', pintaPrevistos);
    });
    document.querySelectorAll('input[name="gender"]').forEach(function (r) {
        r.addEventListener('change', pintaPrevistos);
    });
    pintaPrevistos();
})();
