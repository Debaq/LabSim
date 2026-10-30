// Ficha Nariz, tarjeta Sueño: el estudio de sueño del caso (cases.data['SUENO'])
// en un hidden.
//
// Todo el estado vive en <input name="sueno_json"> (#sueno-json, lo pone
// case_create.php en el formulario para todos). La casilla apagada lo deja
// vacío, y vacío es "este caso no trae estudio de sueño". Encendida, el hidden
// lleva {perfil, params (solo personalizado), canula_suelta: null | {desde,
// hasta}, cpap: null | {p_eficaz, supino, rem, boca, talla}}, lo que lee la app (nasal.sueno.normaliza).
//
// Los perfiles y los rangos salen de window.CASE_CONST.sueno (los de la app).
// Nada se bloquea: el servidor valida al guardar (CaseForm::parseSueno).
(function () {
    var hidden = document.getElementById('sueno-json');
    var presente = document.getElementById('sueno-presente');
    var campos = document.getElementById('sueno-campos');
    var selector = document.getElementById('sueno-perfil');
    var personalizado = document.getElementById('sueno-personalizado');
    var lista = document.getElementById('sueno-params');
    var canula = document.getElementById('sueno-canula');
    var canulaCampos = document.getElementById('sueno-canula-campos');
    var conf = window.CASE_CONST && window.CASE_CONST.sueno;
    if (!hidden || !presente || !campos || !selector || !personalizado || !lista || !canula || !canulaCampos || !conf) return;

    function $(id) { return document.getElementById('sueno-' + id); }

    var ROTULOS = {
        tasa: 'Tasa de eventos por hora (N2, de lado)',
        rem: 'Veces la tasa en REM',
        supino: 'Veces la tasa en supino',
        obstructivas: 'Fracción de apneas obstructivas',
        mixtas: 'Fracción de apneas mixtas',
        centrales: 'Fracción de apneas centrales',
        hipopneas: 'Fracción de hipopneas',
        rera: 'Fracción de RERA',
        caida_apnea: 'Caída de SpO2 en la apnea (puntos)',
        caida_hipopnea: 'Caída de SpO2 en la hipopnea (puntos)',
        hip_sin_desaturar: 'Hipopneas que solo dan despertar',
        spo2_basal: 'SpO2 basal (%)',
        tib: 'Minutos en cama',
        semilla: 'Semilla de la noche'
    };
    var ENTEROS = { tib: 1, semilla: 1 };

    Object.keys(conf.perfiles).forEach(function (k) {
        var o = document.createElement('option');
        o.value = k;
        o.textContent = conf.perfiles[k];
        selector.appendChild(o);
    });
    Object.keys(conf.parametros).forEach(function (k) {
        var r = conf.parametros[k];
        var l = document.createElement('label');
        l.textContent = (ROTULOS[k] || k) + ' (' + r[0] + ' a ' + r[1] + ') ';
        var i = document.createElement('input');
        i.type = 'number';
        i.id = 'sueno-p-' + k;
        i.min = r[0];
        i.max = r[1];
        i.step = ENTEROS[k] ? 1 : (r[1] <= 1 ? 0.05 : 0.5);
        l.appendChild(i);
        lista.appendChild(l);
    });

    var cpapConf = conf.cpap || null;
    var cpapTalla = $('cpap-talla');
    var cpapBoca = $('cpap-boca');
    var cpapBocaTocada = false;
    if (cpapConf) {
        cpapConf.tallas.forEach(function (t) {
            var o = document.createElement('option');
            o.value = t;
            o.textContent = t;
            cpapTalla.appendChild(o);
        });
    }

    // El placeholder de la presión eficaz es la del perfil (en el personalizado, 5 + tasa/6, tope 18).
    function placeholderPresion() {
        var el = $('cpap-p_eficaz');
        if (!cpapConf || !el) return;
        var v;
        if (selector.value === 'personalizado') {
            var t = leeNum($('p-tasa'));
            v = Math.min(18, 5 + (t == null ? conf.parametros.tasa[2] : t) / 6);
            v = Math.round(v * 10) / 10;
        } else {
            v = cpapConf.perfil[selector.value];
        }
        el.placeholder = v == null ? '' : String(v).replace('.', ',');
    }

    function leeNum(el) { var v = parseFloat(el.value); return isNaN(v) ? null : v; }

    function aDatos() {
        var d = { perfil: selector.value, params: null, canula_suelta: null };
        if (d.perfil === 'personalizado') {
            d.params = {};
            Object.keys(conf.parametros).forEach(function (k) {
                var v = leeNum($('p-' + k));
                d.params[k] = v == null ? conf.parametros[k][2] : v;
            });
        }
        if (canula.checked) {
            d.canula_suelta = { desde: leeNum($('desde')), hasta: leeNum($('hasta')) };
        }
        var cp = {};
        if (cpapConf) {
            Object.keys(cpapConf.rangos).forEach(function (k) {
                var v = leeNum($('cpap-' + k));
                if (v != null) cp[k] = v;
            });
            if (cpapTalla.value) cp.talla = cpapTalla.value;
            if (cpapBocaTocada) cp.boca = cpapBoca.checked;
        }
        d.cpap = Object.keys(cp).length ? cp : null;
        return d;
    }

    function aCampos(d) {
        selector.value = conf.perfiles[d.perfil] ? d.perfil : 'roncador';
        var p = d.params || {};
        Object.keys(conf.parametros).forEach(function (k) {
            $('p-' + k).value = p[k] != null ? p[k] : conf.parametros[k][2];
        });
        var c = d.canula_suelta;
        canula.checked = !!c;
        $('desde').value = c && c.desde != null ? c.desde : '';
        $('hasta').value = c && c.hasta != null ? c.hasta : '';
        var cp = d.cpap || {};
        if (cpapConf) {
            Object.keys(cpapConf.rangos).forEach(function (k) {
                $('cpap-' + k).value = cp[k] != null ? cp[k] : '';
            });
            cpapTalla.value = cp.talla || '';
            cpapBocaTocada = cp.boca !== undefined;
            cpapBoca.checked = !!cp.boca;
        }
    }

    function muestra() {
        campos.style.display = presente.checked ? '' : 'none';
        personalizado.style.display = selector.value === 'personalizado' ? '' : 'none';
        canulaCampos.style.display = canula.checked ? '' : 'none';
    }

    function guarda() {
        muestra();
        placeholderPresion();
        var nuevo = presente.checked ? JSON.stringify(aDatos()) : '';
        if (hidden.value !== nuevo) {
            hidden.value = nuevo;
            hidden.dispatchEvent(new Event('change', { bubbles: true }));
        }
    }

    var guardado = null;
    try { guardado = hidden.value ? JSON.parse(hidden.value) : null; } catch (e) { guardado = null; }
    aCampos(guardado || { perfil: 'roncador' });
    presente.checked = !!guardado;
    muestra();

    placeholderPresion();
    cpapBoca.addEventListener('change', function () { cpapBocaTocada = true; });
    presente.addEventListener('change', guarda);
    canula.addEventListener('change', function () {
        if (canula.checked && $('desde').value === '') {
            $('desde').value = 120;
            $('hasta').value = 180;
        }
        guarda();
    });
    campos.addEventListener('input', guarda);
    campos.addEventListener('change', guarda);
})();
