// Exámenes que trae el paciente (ver ExamenesPrevios.php): agregar/quitar
// filas. Cada fila se clona de la plantilla #previo-row-tpl, que dibuja PHP.
(function () {
    var container = document.getElementById('previo-rows');
    var tpl = document.getElementById('previo-row-tpl');
    var addBtn = document.getElementById('previo-add');
    if (!container || !tpl || !addBtn) { return; }

    addBtn.addEventListener('click', function () {
        var wrap = document.createElement('div');
        wrap.innerHTML = tpl.innerHTML;
        var row = wrap.querySelector('.previo-row');
        container.appendChild(row);
        var dias = row.querySelector('input[name="prev_dias[]"]');
        if (dias) { dias.focus(); }
    });

    container.addEventListener('click', function (e) {
        if (!e.target.classList.contains('previo-remove')) { return; }
        var row = e.target.closest('.previo-row');
        if (row) { row.remove(); }
    });
})();
