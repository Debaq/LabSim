// Fecha de nacimiento y RUT del paciente: no se tipean a mano -- se derivan
// de la edad (mismo criterio que CaseBuilder::rutFromAge/randomFechaNacForAge
// del lado servidor, que es el fallback si JS está deshabilitado). Cada vez
// que cambia la edad se recalculan: año de nacimiento = año actual - edad,
// día/mes al azar dentro de ese año. La fecha queda readonly; el RUT sigue
// editable a mano por si el docente quiere ajustarlo después del cálculo.
(function () {
    var ageInput = document.getElementById('patient-age');
    var fechaInput = document.getElementById('patient-fecha-nac');
    var rutInput = document.getElementById('patient-rut');
    if (!ageInput || !fechaInput || !rutInput) { return; }

    // Misma regresión lineal fija que CaseBuilder::rutFromAge (helpers.py
    // rut_from_age) -- no inventar otra, tiene que dar edades consistentes
    // con get_age_from_rut del lado cliente.
    var RUT_SLOPE = 3.3363697569700348e-06;
    var RUT_INTERCEPT = 1932.2573852507373;
    var lastAge = null;

    function pad2(n) { return n < 10 ? '0' + n : '' + n; }

    function recompute() {
        var age = parseInt(ageInput.value, 10);
        if (isNaN(age) || age < 0 || age === lastAge) { return; }
        lastAge = age;

        var hoy = new Date();
        var currentYear = hoy.getFullYear();
        var birthYear = currentYear - age;
        var randomDayOffset = Math.floor(Math.random() * 365);
        var birthDate = new Date(birthYear, 0, 1 + randomDayOffset);
        // Nadie nace en el futuro: con edad 0 el año es el actual y el
        // sorteo caía después de hoy una de cada tres veces.
        if (birthDate > hoy) {
            birthDate = new Date(hoy.getTime() - Math.floor(Math.random() * 31) * 86400000);
            randomDayOffset = Math.floor(
                (birthDate - new Date(birthDate.getFullYear(), 0, 1)) / 86400000);
        }
        // Y si es un recién nacido con edad exacta cargada, la fecha sale
        // de sus horas de vida: nació hoy o ayer, no en febrero.
        var valorEdad = document.getElementById('patient-edad-valor');
        var unidadEdad = document.getElementById('patient-edad-unidad');
        var nExacta = valorEdad ? parseFloat(valorEdad.value) : NaN;
        if (age === 0 && !isNaN(nExacta)) {
            var factor = { horas: 1, dias: 24, meses: 720 };
            var horas = nExacta * (factor[unidadEdad ? unidadEdad.value : 'horas'] || 1);
            birthDate = new Date(hoy.getTime() - horas * 3600000);
            randomDayOffset = Math.floor(
                (birthDate - new Date(birthDate.getFullYear(), 0, 1)) / 86400000);
        }
        fechaInput.value = birthDate.getFullYear() + '-' + pad2(birthDate.getMonth() + 1) + '-' + pad2(birthDate.getDate());

        var birthDateFloat = birthYear + (randomDayOffset / 365);
        var rutApprox = Math.trunc((birthDateFloat - RUT_INTERCEPT) / RUT_SLOPE);
        rutInput.value = String(rutApprox);
    }

    ageInput.addEventListener('input', recompute);
    ageInput.addEventListener('change', recompute);
    // La edad exacta también mueve la fecha: es la que manda en un recién
    // nacido.
    ['patient-edad-valor', 'patient-edad-unidad'].forEach(function (id) {
        var el = document.getElementById(id);
        if (el) {
            ['input', 'change'].forEach(function (ev) {
                el.addEventListener(ev, function () { lastAge = null; recompute(); });
            });
        }
    });
})();
