// El sexo decide el nombre que sortea "Generar nombre al azar", así que el
// campo tiene que estar al lado del botón: mandar al docente a otra pestaña
// para elegirlo y volver es exactamente lo que "Armado rápido" vino a sacar.
//
// El campo que viaja en el POST sigue siendo el radio de la pestaña Paciente
// --uno solo, sin duplicar el name-- y este select lo espeja en los dos
// sentidos. Sin JS el select no hace nada y el radio sigue estando donde
// estuvo siempre.
(function () {
    var sel = document.getElementById('armado-gender');
    var radios = document.querySelectorAll('#case-form input[name="gender"]');
    if (sel && radios.length) {
        sel.addEventListener('change', function () {
            radios.forEach(function (r) { r.checked = r.value === sel.value; });
        });
        radios.forEach(function (r) {
            r.addEventListener('change', function () { if (r.checked) { sel.value = r.value; } });
        });
        // Estado inicial: manda el radio, que es el que trae el valor del POST.
        radios.forEach(function (r) { if (r.checked) { sel.value = r.value; } });
    }

    // La edad, igual: espejo del input de Paciente, que es el que viaja en el
    // POST. Acá hay que reemitir los eventos además de copiar el valor -- de
    // la edad cuelgan la fecha de nacimiento, el RUT y la población de
    // referencia del ABR, y todos escuchan 'input'/'change' sobre ese input.
    // Copiar el .value en silencio dejaría un paciente de 2 meses con el RUT
    // y las latencias de un adulto.
    var edad = document.getElementById('armado-age');
    var edadReal = document.getElementById('patient-age');
    if (!edad || !edadReal) { return; }

    var propagando = false;
    function espejar(desde, hacia) {
        if (propagando) { return; }
        propagando = true;
        hacia.value = desde.value;
        hacia.dispatchEvent(new Event('input', { bubbles: true }));
        hacia.dispatchEvent(new Event('change', { bubbles: true }));
        propagando = false;
    }
    ['input', 'change'].forEach(function (ev) {
        edad.addEventListener(ev, function () { espejar(edad, edadReal); });
        edadReal.addEventListener(ev, function () { espejar(edadReal, edad); });
    });
})();
