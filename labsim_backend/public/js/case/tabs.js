// Tabs de fichas -- se activan solo si corre JS (body.js-tabs), así sin JS
// el form queda igual que antes: todas las secciones apiladas y visibles.
(function () {
    var tabButtons = document.querySelectorAll('.tab-btn');
    var tabPanels = document.querySelectorAll('.tab-panel');
    if (!tabButtons.length || !tabPanels.length) return;

    document.body.classList.add('js-tabs');

    function activate(name) {
        tabButtons.forEach(function (btn) { btn.classList.toggle('active', btn.dataset.tab === name); });
        tabPanels.forEach(function (panel) { panel.classList.toggle('active', panel.dataset.tab === name); });
        window.scrollTo(0, 0);
    }

    // Los autocompletados viven todos en "Armado rápido" y las pestañas que
    // llenan quedan en otra parte, así que la ficha necesita mandarse sola de
    // una pestaña a otra: los <a class="tab-link" data-goto-tab="..."> del
    // texto y el salto después de redactar la anamnesis con IA.
    window.gotoTab = activate;

    tabButtons.forEach(function (btn) {
        btn.addEventListener('click', function () { activate(btn.dataset.tab); });
    });

    document.addEventListener('click', function (e) {
        var link = e.target.closest('.tab-link[data-goto-tab]');
        if (!link) return;
        e.preventDefault();
        activate(link.getAttribute('data-goto-tab'));
    });

    // Punto rojo en la pestaña que tiene algo pendiente (CaseCompleteness
    // devuelve el `tab` de cada faltante). Sin esto el docente lee la lista
    // de arriba y después tiene que adivinar dónde estaba cada cosa.
    document.querySelectorAll('.pendientes-card [data-goto-tab]').forEach(function (link) {
        var btn = document.querySelector('.tab-btn[data-tab="' + link.getAttribute('data-goto-tab') + '"]');
        if (!btn || btn.querySelector('.tab-error-dot')) return;
        var dot = document.createElement('span');
        dot.className = 'tab-error-dot';
        btn.appendChild(dot);
    });

    // Si el usuario llega con un campo inválido dentro de una ficha oculta,
    // el navegador la deja invisible y el submit falla en silencio -- al
    // interceptar el evento se salta a la ficha que tiene el campo inválido.
    document.getElementById('case-form').addEventListener('invalid', function (e) {
        var panel = e.target.closest('.tab-panel');
        if (panel) activate(panel.dataset.tab);
    }, true);
})();
