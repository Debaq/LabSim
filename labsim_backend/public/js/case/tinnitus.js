// Tinnitus: oído solo aplica si es unilateral, predominio solo si es
// bilateral -- sin JS quedan ambos campos visibles (degradan con gracia,
// el backend ya ignora el que no corresponda según la lateralidad elegida).
(function () {
    var select = document.getElementById('tinnitus-lateralidad');
    if (!select) return;
    var fields = document.querySelectorAll('[data-show-for]');

    function update() {
        fields.forEach(function (field) {
            field.style.display = field.dataset.showFor === select.value ? '' : 'none';
        });
    }

    select.addEventListener('change', update);
    update();
})();
