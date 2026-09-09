// Aviso de los módulos derivados del perfil auditivo.
//
// La derivación es una SUGERENCIA, no un candado: escribe los campos (lo
// hace profile-preview.js, en vivo) y ahí termina. El docente puede editar
// cualquiera de esos campos y lo que quede en pantalla es lo que se guarda
// -- el servidor ya no los pisa. Antes quedaban readOnly/disabled, y un
// reflejo o un umbral que no se dejaba tocar no tiene forma de ser "una
// sugerencia".
//
// Lo que sí hace falta es decir de dónde salieron esos números y qué los
// vuelve a mover: cambiar el audiograma o el perfil vuelve a sugerir y pisa
// la edición a mano. Eso es lo único que queda acá.
(function () {
    function aplicar(modulo) {
        var chk = document.querySelector('input[name="perfil[auto][' + modulo + ']"]');
        if (!chk) return;
        document.querySelectorAll('.derivado-aviso[data-derivado="' + modulo + '"]').forEach(function (aviso) {
            aviso.hidden = !chk.checked;
        });
    }

    ['abr', 'eoas', 'reflex', 'recruit', 'logo'].forEach(function (modulo) {
        var chk = document.querySelector('input[name="perfil[auto][' + modulo + ']"]');
        if (chk) { chk.addEventListener('change', function () { aplicar(modulo); }); }
        aplicar(modulo);
    });
})();
