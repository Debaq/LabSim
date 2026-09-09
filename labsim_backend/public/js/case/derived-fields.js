// Campos que pasan a escribirse solos cuando su módulo está derivado.
//
// Sin esto el docente edita un campo que el servidor va a pisar al guardar,
// y no hay forma de saberlo mirando la pantalla. Los patrones son prefijos
// del atributo name; solo se listan los campos que la proyección REESCRIBE
// (el ruido del paciente o el sello de la sonda, por ejemplo, siguen siendo
// del docente aunque la OEA esté derivada).
(function () {
    var CAMPOS = {
        abr: ['abr[od][type]', 'abr[oi][type]', 'abr[od][umbral]', 'abr[oi][umbral]'],
        eoas: ['eoas[od][type]', 'eoas[oi][type]', 'eoas[od][umbral]', 'eoas[oi][umbral]',
               'eoas[od][desv]', 'eoas[oi][desv]'],
        reflex: ['reflex_ipsi[', 'reflex_contra[', 'reflex_type['],
        recruit: ['sisi[', 'recruit[', 'fowler_pattern[', 'carhart[', 'stat[', 'rosemberg[',
                  'ldl[', 'ldl_habilitado['],
        logo: ['umd_int[', 'umd_pct[']
    };

    function elementos(prefijos) {
        var out = [];
        var todos = document.querySelectorAll('#case-form [name]');
        for (var i = 0; i < todos.length; i++) {
            var name = todos[i].getAttribute('name');
            for (var p = 0; p < prefijos.length; p++) {
                if (name.indexOf(prefijos[p]) === 0) { out.push(todos[i]); break; }
            }
        }
        return out;
    }

    function aplicar(modulo) {
        var chk = document.querySelector('input[name="perfil[auto][' + modulo + ']"]');
        if (!chk) return;
        elementos(CAMPOS[modulo]).forEach(function (el) {
            // readOnly en los number (siguen viajando en el POST y se ven);
            // disabled en select/checkbox, que no lo soportan. No importa
            // que no lleguen: con el módulo derivado el servidor los pisa.
            if (el.tagName === 'SELECT' || el.type === 'checkbox') {
                el.disabled = chk.checked;
            } else {
                el.readOnly = chk.checked;
            }
            el.style.opacity = chk.checked ? '0.6' : '';
            el.title = chk.checked ? 'Derivado del perfil auditivo -- se reescribe al guardar' : '';
        });
        // El gris y el `title` no alcanzan: hay que decir POR QUÉ el campo no
        // se deja editar y dónde se apaga. Sin esto el docente encuentra el
        // selector de patología del ABR apagado y no tiene forma de saber que
        // lo apagó la casilla del perfil.
        document.querySelectorAll('.derivado-aviso[data-derivado="' + modulo + '"]').forEach(function (aviso) {
            aviso.hidden = !chk.checked;
        });
    }

    Object.keys(CAMPOS).forEach(function (modulo) {
        var chk = document.querySelector('input[name="perfil[auto][' + modulo + ']"]');
        if (chk) { chk.addEventListener('change', function () { aplicar(modulo); }); }
        aplicar(modulo);
    });
})();
