// Recién nacido: los campos del parto viven en la ficha Paciente --son los
// que viajan en el POST-- y el Armado rápido los espeja, igual que el sexo y
// la edad (ver sex-mirror.js). Sin esto, armar un caso de recién nacido con
// el botón dejaba un paciente de "0 años" sin horas de vida: sin transitorio
// de las primeras horas y sin tamizaje, o sea sin el turno.
//
// Además el bloque entero se muestra solo cuando la edad va en 0: a un
// adulto no le sobra un campo de semanas de gestación.
(function () {
    var bloque = document.getElementById('armado-rn');
    var edadReal = document.getElementById('patient-age');
    if (!bloque || !edadReal) { return; }

    // [id en Armado, name en Paciente]. Los checkbox van aparte.
    var CAMPOS = [
        ['armado-edad-valor', 'edad_valor'],
        ['armado-edad-unidad', 'edad_unidad'],
        ['armado-parto', 'nacimiento[parto]'],
        ['armado-semanas', 'nacimiento[semanas]'],
        ['armado-peso', 'nacimiento[peso_g]'],
        ['armado-torch', 'nacimiento[torch]'],
        ['armado-uci', 'nacimiento[uci_dias]']
    ];
    var CHECKS = [
        ['armado-ototoxicos', 'nacimiento[ototoxicos]'],
        ['armado-exanguino', 'nacimiento[exanguinotransfusion]']
    ];

    function real(name) {
        return document.querySelector('#case-form [name="' + name + '"]');
    }

    var propagando = false;
    function espejar(desde, hacia) {
        if (propagando || !desde || !hacia) { return; }
        propagando = true;
        if (hacia.type === 'checkbox') {
            hacia.checked = desde.checked;
        } else {
            hacia.value = desde.value;
        }
        hacia.dispatchEvent(new Event('input', { bubbles: true }));
        hacia.dispatchEvent(new Event('change', { bubbles: true }));
        propagando = false;
    }

    CAMPOS.concat(CHECKS).forEach(function (par) {
        var aqui = document.getElementById(par[0]);
        var alla = real(par[1]);
        if (!aqui || !alla) { return; }
        // Estado inicial: manda el de Paciente, que trae el valor del POST.
        if (alla.type === 'checkbox') { aqui.checked = alla.checked; } else if (alla.value !== '') { aqui.value = alla.value; }
        ['input', 'change'].forEach(function (ev) {
            aqui.addEventListener(ev, function () { espejar(aqui, alla); });
            alla.addEventListener(ev, function () { espejar(alla, aqui); });
        });
    });

    // El bloque aparece con la edad en 0 y se lleva con él el <details> de
    // Paciente, que si no hay que ir a abrir a mano.
    function refrescar() {
        var anios = parseInt(edadReal.value, 10);
        var esBebe = !isNaN(anios) && anios === 0;
        bloque.hidden = !esBebe;
        var det = document.querySelector('#case-form details.nacimiento, #case-form [name="nacimiento[parto]"]');
        if (esBebe && det) {
            var cont = det.closest ? det.closest('details') : null;
            if (cont) { cont.open = true; }
        }
    }
    ['input', 'change'].forEach(function (ev) { edadReal.addEventListener(ev, refrescar); });
    refrescar();

    // Aviso de riesgo en la ficha Paciente: el docente tiene que ver por qué
    // este bebé refiere más que el de al lado, sin ir a buscarlo al código.
    var aviso = document.getElementById('nac-riesgo-aviso');
    var semanas = real('nacimiento[semanas]');
    var peso = real('nacimiento[peso_g]');
    var PESO_MUY_BAJO = (window.CASE_CONST && window.CASE_CONST.pesoMuyBajoG) || 1500;
    function avisar() {
        if (!aviso) { return; }
        var s = semanas ? parseInt(semanas.value, 10) : NaN;
        var p = peso ? parseInt(peso.value, 10) : NaN;
        var partes = [];
        if (!isNaN(s) && s < 34) {
            partes.push('prematuro de ' + s + ' semanas: el tamizaje refiere bastante más, y el AABR también');
        } else if (!isNaN(s) && s <= 36) {
            partes.push('pretérmino tardío: refiere más en la EOA, el AABR casi no se mueve');
        }
        if (!isNaN(p) && p < PESO_MUY_BAJO) {
            partes.push('muy bajo peso (< ' + PESO_MUY_BAJO + ' g): indicador de riesgo del JCIH y más "refiere"');
        }
        aviso.hidden = partes.length === 0;
        aviso.textContent = partes.length ? 'Este bebé: ' + partes.join(' · ') + '.' : '';
    }
    [semanas, peso].forEach(function (el) {
        if (el) { ['input', 'change'].forEach(function (ev) { el.addEventListener(ev, avisar); }); }
    });
    avisar();
})();
