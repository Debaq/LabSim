// No salir de la edición con cambios sin guardar.
//
// El bloqueo de datos faltantes vive en el servidor (CaseCompleteness), y
// solo puede actuar cuando el docente aprieta Guardar. Lo que se escapaba
// era el otro camino: tocar el caso, irse por "Cancelar" o cerrar la
// pestaña, y dejarlo a medias sin que nadie lo mire nunca más.
(function () {
    var form = document.getElementById('case-form');
    if (!form) return;
    var sucio = false;
    var guardando = false;

    form.addEventListener('input', function () { sucio = true; });
    form.addEventListener('change', function () { sucio = true; });
    form.addEventListener('submit', function () { guardando = true; });

    window.addEventListener('beforeunload', function (e) {
        if (!sucio || guardando) return;
        // El texto lo pone el navegador; lo que importa es preventDefault.
        e.preventDefault();
        e.returnValue = '';
    });

    // "Cancelar" es un <a>, no dispara submit: se pregunta a mano para
    // poder decir de qué se trata en vez del texto genérico del navegador.
    document.addEventListener('click', function (e) {
        var link = e.target.closest ? e.target.closest('a[href$="patients.php"]') : null;
        if (!link || !sucio) return;
        if (!window.confirm('Hay cambios sin guardar en este caso. Si salís ahora se pierden.')) {
            e.preventDefault();
        } else {
            guardando = true;   // evita la segunda pregunta del navegador
        }
    });
})();
