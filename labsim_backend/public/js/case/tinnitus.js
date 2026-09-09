// Tinnitus: la casilla "Este paciente tiene tinnitus" manda sobre toda la
// ficha -- apagada (el default) el resto queda deshabilitado, no viaja en el
// POST y el caso se guarda sin acúfeno. Dentro, oído solo aplica si es
// unilateral y predominio solo si es bilateral.
//
// Sin JS quedan todos los campos visibles y editables (degradan con gracia):
// el backend ya decide por la casilla y por la lateralidad elegida, así que
// lo que no corresponda se ignora igual.
(function () {
    var presente = document.getElementById('tinnitus-presente');
    var campos = document.getElementById('tinnitus-campos');
    var select = document.getElementById('tinnitus-lateralidad');
    if (!presente || !campos || !select) return;
    var fields = campos.querySelectorAll('[data-show-for]');
    var controles = campos.querySelectorAll('input, select');

    function update() {
        var hay = presente.checked;
        campos.classList.toggle('bloque-apagado', !hay);
        controles.forEach(function (control) { control.disabled = !hay; });
        fields.forEach(function (field) {
            field.style.display = field.dataset.showFor === select.value ? '' : 'none';
        });
    }

    presente.addEventListener('change', update);
    select.addEventListener('change', update);
    update();
})();
