// Sala: agregar/quitar acompañantes. Cada fila se clona de la plantilla
// (#sala-row-tpl, renderizada por PHP para no tener dos versiones del mismo
// HTML) y estrena un id de persona propio, que es con lo que se guarda su
// foto (ver PatientPhoto::key) y con lo que se marca al informante. Los ids
// nunca se reciclan ni se reindexan: si se reindexaran, borrar una fila le
// pondría a un acompañante la cara de otro.
(function () {
    var container = document.getElementById('sala-rows');
    var tpl = document.getElementById('sala-row-tpl');
    var addBtn = document.getElementById('sala-add');
    if (!container || !tpl || !addBtn) { return; }

    function nuevoId() {
        // Alfanumérico y corto: Sala::safeId() descarta lo demás y lo
        // recorta a 16, y el id termina siendo parte de un nombre de
        // archivo en disco.
        return 'a' + Date.now().toString(36) + Math.floor(Math.random() * 1000).toString(36);
    }

    addBtn.addEventListener('click', function () {
        var id = nuevoId();
        var html = tpl.innerHTML.split('__ID__').join(id);
        var wrap = document.createElement('div');
        wrap.innerHTML = html;
        var row = wrap.querySelector('.sala-row');
        container.appendChild(row);
        var nombre = row.querySelector('input[name="sala_nombre[]"]');
        if (nombre) { nombre.focus(); }
    });

    container.addEventListener('click', function (e) {
        if (!e.target.classList.contains('sala-remove')) { return; }
        var row = e.target.closest('.sala-row');
        if (!row) { return; }
        var eraInformante = row.querySelector('input[name="sala_informante"]:checked');
        row.remove();
        // Si se fue el informante principal, la historia la cuenta el
        // paciente: dejar la sala sin nadie marcado haría que el backend lo
        // eligiera solo, y el docente no vería por qué.
        if (eraInformante) {
            var delPaciente = document.querySelector('input[name="sala_informante"][value="p1"]');
            if (delPaciente) { delPaciente.checked = true; }
        }
    });
})();
