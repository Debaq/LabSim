/**
 * Aviso y corte de sesión por inactividad en los dos portales (docente/admin
 * y alumno).
 *
 * El problema que resuelve: la sesión moría callada y la página seguía ahí,
 * editable. Se escribía media ficha contra una sesión muerta y el POST
 * rebotaba al login, perdiendo lo escrito.
 *
 * Reglas:
 *  - Escribir/clickear cuenta como actividad y renueva la sesión en el
 *    servidor (ping, a lo sumo uno cada RENOVAR_CADA_MS). Una ficha larga no
 *    se cae por estar tecleando.
 *  - Sin actividad, AVISO_SEGUNDOS antes del corte aparece un cartel con la
 *    cuenta regresiva y el botón para seguir conectado.
 *  - Al llegar a cero se va al login (o se recarga, en el portal de alumno):
 *    la página deja de aceptar escritura a ciegas.
 *
 * Config por data-* en el <script> que lo carga (ver admin/_layout.php).
 */
(function () {
    var script = document.currentScript || document.querySelector('script[data-session-guard]');
    if (!script) { return; }

    var TOTAL_SEGUNDOS = parseInt(script.dataset.segundos || '0', 10);
    var PING_URL = script.dataset.ping || '';
    var DESTINO = script.dataset.destino || '';       // vacío = recargar
    var AVISO_SEGUNDOS = parseInt(script.dataset.aviso || '120', 10);
    var RENOVAR_CADA_MS = 5 * 60 * 1000;

    if (!TOTAL_SEGUNDOS || !PING_URL) { return; }

    var vence = Date.now() + TOTAL_SEGUNDOS * 1000;
    var ultimoPing = Date.now();
    var pidiendo = false;
    var caja = null;
    var cuenta = null;

    function quedan() {
        return Math.max(0, Math.round((vence - Date.now()) / 1000));
    }

    function mmss(segundos) {
        var m = Math.floor(segundos / 60);
        var s = segundos % 60;
        return m + ':' + (s < 10 ? '0' : '') + s;
    }

    function salir() {
        if (DESTINO) {
            window.location.href = DESTINO;
        } else {
            window.location.reload();
        }
    }

    function renovar() {
        if (pidiendo) { return; }
        pidiendo = true;
        fetch(PING_URL, { method: 'POST', credentials: 'same-origin', headers: { 'Accept': 'application/json' } })
            .then(function (r) { return r.ok ? r.json() : null; })
            .then(function (data) {
                pidiendo = false;
                if (!data || !data.ok) { salir(); return; }
                vence = Date.now() + data.quedan * 1000;
                ultimoPing = Date.now();
                ocultarAviso();
            })
            .catch(function () {
                // Sin red: no se corta la sesión por un fetch fallido, se
                // reintenta en la próxima actividad o al tocar el botón.
                pidiendo = false;
            });
    }

    function crearAviso() {
        var fondo = document.createElement('div');
        fondo.style.cssText = 'position:fixed; inset:0; background:rgba(0,0,0,0.45); z-index:9999;'
            + 'display:flex; align-items:center; justify-content:center; padding:1rem;';
        var box = document.createElement('div');
        box.setAttribute('role', 'alertdialog');
        box.setAttribute('aria-live', 'assertive');
        box.style.cssText = 'background:var(--color-surface, #fff); color:var(--color-text, #111);'
            + 'border-radius:0.6rem; padding:1.2rem 1.4rem; max-width:26rem; width:100%;'
            + 'box-shadow:0 10px 40px rgba(0,0,0,0.3); font-size:0.95rem;';
        box.innerHTML = '<strong style="display:block; margin-bottom:0.5rem;">Tu sesión está por cerrarse</strong>'
            + '<p style="margin:0 0 0.4rem;">Llevas un rato sin actividad. Se cierra en '
            + '<span data-cuenta style="font-variant-numeric:tabular-nums; font-weight:600;"></span>.</p>'
            + '<p style="margin:0 0 0.9rem; opacity:0.75;">Si estabas escribiendo algo, sigue conectado antes de que'
            + ' llegue a cero: al cerrarse, la página vuelve al inicio y lo no guardado se pierde.</p>'
            + '<div style="display:flex; gap:0.5rem; flex-wrap:wrap;">'
            + '<button type="button" data-seguir class="btn">Seguir conectado</button>'
            + '<button type="button" data-cerrar class="btn btn--secondary">Cerrar sesión ahora</button>'
            + '</div>';
        fondo.appendChild(box);
        document.body.appendChild(fondo);
        box.querySelector('[data-seguir]').addEventListener('click', renovar);
        box.querySelector('[data-cerrar]').addEventListener('click', salir);
        cuenta = box.querySelector('[data-cuenta]');
        return fondo;
    }

    function mostrarAviso() {
        if (!caja) { caja = crearAviso(); }
        caja.hidden = false;
        caja.style.display = 'flex';
    }

    function ocultarAviso() {
        if (caja) { caja.style.display = 'none'; }
    }

    function tick() {
        var restan = quedan();
        if (restan <= 0) { salir(); return; }
        if (restan <= AVISO_SEGUNDOS) {
            mostrarAviso();
            if (cuenta) { cuenta.textContent = mmss(restan); }
        }
    }

    function huboActividad() {
        // Con el cartel puesto, escribir no alcanza: la decisión de seguir es
        // explícita (botón), si no bastaría rozar el teclado para no enterarse
        // nunca de que la sesión vencía.
        if (quedan() <= AVISO_SEGUNDOS) { return; }
        if (Date.now() - ultimoPing >= RENOVAR_CADA_MS) { renovar(); }
    }

    ['keydown', 'pointerdown', 'input', 'change'].forEach(function (evento) {
        document.addEventListener(evento, huboActividad, { passive: true });
    });

    setInterval(tick, 1000);
    tick();
})();
