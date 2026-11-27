// Opción "B · perforación seca" del selector de Z (CaseBuilder::
// Z_PERFORACION_SECA_LABEL). Tiene el mismo valor 'B' que la B común: la
// ficha guarda Z = 'B' y la membrana perforada la declaran el volumen del
// conducto ('alto') y la ETF (Permeable / No permeable). Este archivo
// mantiene las tres cosas contando la misma historia:
//  - elegir la perforación seca pone el volumen en alto y, si la ETF era
//    de membrana íntegra, la pasa a Permeable (lo más frecuente);
//  - dejarla por otra curva (salvo NR, que ignora volumen y ETF) vuelve el
//    volumen a normal y saca la ETF de membrana perforada;
//  - con Z = 'B', la opción que se ve sigue al volumen: alto = perforación
//    seca. Así lo que escribe el generador (z.value = 'B' + volumen) o lo
//    que el docente cambia a mano en el volumen se refleja en el selector.
(function () {
    var ETF_PERFORADA = ['Permeable', 'No permeable'];

    function campos(lado) {
        return {
            z: document.getElementById('z_' + lado),
            vol: document.querySelector('select[name="volumen_cae_' + lado + '"]'),
            etf: document.querySelector('select[name="etf_' + lado + '"]')
        };
    }

    function esPerforada(z) {
        var opt = z && z.options[z.selectedIndex];
        return !!(opt && opt.dataset.perforada);
    }

    function poner(el, valor) {
        if (!el || el.value === valor) { return; }
        el.value = valor;
        el.dispatchEvent(new Event('change', { bubbles: true }));
    }

    // La opción visible sigue al volumen cuando la curva es B. Devuelve si
    // quedó en perforación seca.
    window.sincronizarPerforacion = function (lado) {
        var c = campos(lado);
        if (!c.z) { return false; }
        if (c.z.value === 'B' && c.vol) {
            var quiere = c.vol.value === 'alto';
            for (var i = 0; i < c.z.options.length; i++) {
                var opt = c.z.options[i];
                if (opt.value === 'B' && !!opt.dataset.perforada === quiere) {
                    c.z.selectedIndex = i;
                    break;
                }
            }
        }
        c.z.dataset.eraPerforada = esPerforada(c.z) ? '1' : '';
        return esPerforada(c.z);
    };

    document.addEventListener('change', function (e) {
        var m = e.target.id && /^z_(od|oi)$/.exec(e.target.id);
        if (m) {
            var lado = m[1], c = campos(lado);
            if (esPerforada(c.z)) {
                poner(c.vol, 'alto');
                if (c.etf && ETF_PERFORADA.indexOf(c.etf.value) < 0) { poner(c.etf, 'Permeable'); }
            } else if (c.z.dataset.eraPerforada && c.z.value !== 'NR') {
                // Sale de la perforación seca: la membrana vuelve a estar
                // íntegra. B común = oído medio ocupado, trompa que no ventila.
                poner(c.vol, 'normal');
                if (c.etf && ETF_PERFORADA.indexOf(c.etf.value) >= 0) {
                    poner(c.etf, c.z.value === 'B' ? 'Disfunción tubaria' : 'Normal');
                }
            }
            c.z.dataset.eraPerforada = esPerforada(c.z) ? '1' : '';
            return;
        }
        var v = e.target.name && /^volumen_cae_(od|oi)$/.exec(e.target.name);
        if (v) { window.sincronizarPerforacion(v[1]); }
    });

    ['od', 'oi'].forEach(function (lado) { window.sincronizarPerforacion(lado); });
})();
