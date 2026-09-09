// Aviso de "esto te tocó otra ficha".
//
// Los autocompletados del formulario (la proyección del perfil auditivo,
// "igualar ósea a aérea", el auto de Fletcher, la acumetría automática, el
// generador de Armado rápido) escriben campos que casi nunca están en la
// pestaña que el docente tiene abierta. Antes eso pasaba en silencio: se
// cambiaba un umbral en Audiometría y los reflejos de Timpanometría y el
// umbral del ABR quedaban distintos sin que nada lo dijera, incluso en una
// ficha ya tildada como revisada en el Resumen.
//
// Ahora cada autocompletado avisa qué fichas reescribió, con un link a cada
// una, y las destilda del Resumen: lo revisado es una versión de la ficha,
// no la ficha (mismo criterio que resumen.js aplica al editar a mano).
(function () {
    var caja = document.getElementById('auto-cambios');
    if (!caja) { return; }
    var texto = document.getElementById('auto-cambios-texto');
    var links = document.getElementById('auto-cambios-links');
    var cerrar = document.getElementById('auto-cambios-cerrar');

    // Ficha -> por qué se tocó. Se acumulan hasta que el docente las visita
    // o cierra el aviso: dos cambios seguidos no borran el primero.
    var pendientes = {};

    function etiqueta(tab) {
        var btn = document.querySelector('.tab-btn[data-tab="' + tab + '"]');
        return btn ? btn.textContent.trim() : tab;
    }
    function tabActiva() {
        var btn = document.querySelector('.tab-btn.active');
        return btn ? btn.dataset.tab : null;
    }

    function pintar() {
        var tabs = Object.keys(pendientes);
        if (!tabs.length) { caja.hidden = true; return; }
        var motivos = [];
        tabs.forEach(function (tab) {
            if (motivos.indexOf(pendientes[tab]) < 0) { motivos.push(pendientes[tab]); }
        });
        texto.textContent = 'Lo que acabás de cambiar reescribió ' +
            (tabs.length === 1 ? 'otra ficha' : 'otras ' + tabs.length + ' fichas') +
            ' (' + motivos.join('; ') + '). Conviene revisarlas antes de guardar.';
        links.innerHTML = '';
        tabs.forEach(function (tab) {
            var a = document.createElement('a');
            a.href = '#';
            a.className = 'tab-link';
            a.setAttribute('data-goto-tab', tab);
            a.textContent = etiqueta(tab);
            a.addEventListener('click', function () {
                delete pendientes[tab];
                // El salto de pestaña lo hace tabs.js con el mismo click.
                setTimeout(pintar, 0);
            });
            links.appendChild(a);
        });
        caja.hidden = false;
    }

    /**
     * @param {string[]} tabs  fichas que un autocompletado acaba de reescribir
     * @param {string} motivo  qué las reescribió, en una frase corta
     */
    window.avisarCambioAutomatico = function (tabs, motivo) {
        var activa = tabActiva();
        var hay = false;
        tabs.forEach(function (tab) {
            // La ficha abierta no se avisa: el cambio se está viendo.
            if (!tab || tab === activa) { return; }
            pendientes[tab] = motivo;
            hay = true;
        });
        // Destildar es lo que de verdad frena un guardado a ciegas: el
        // Resumen exige las 11 fichas tildadas.
        if (window.resumenDestildar) { window.resumenDestildar(tabs); }
        if (hay) { pintar(); }
    };

    if (cerrar) {
        cerrar.addEventListener('click', function () {
            pendientes = {};
            pintar();
        });
    }
})();
