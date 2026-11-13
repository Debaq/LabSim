// Base de otoscopias (admin/otoscopias.php): subida de muchas fotos y el
// editor de una (giro, encuadre, lado anterior, tipo).
//
// El encuadre es el mismo modelo que OtoscopiaBiblioteca::renderizarBase
// en el servidor: un recuadro cuadrado de lado S (px del original) centrado
// en (ux, uy) del original y girado θ grados en sentido horario. Punto del
// canvas = C/2 + (C/S) · giro(θ) · (punto del original − (ux, uy)). Así lo
// que se ve acá es exactamente la imagen que queda guardada.
(function () {
    function csrfToken() {
        var el = document.querySelector('input[name="csrf_token"]');
        return el ? el.value : '';
    }

    function post(datos) {
        var fd = new FormData();
        fd.append('csrf_token', csrfToken());
        Object.keys(datos).forEach(function (k) { fd.append(k, datos[k]); });
        return fetch('otoscopia_biblioteca.php', { method: 'POST', body: fd })
            .then(function (r) { return r.json(); });
    }

    // --- Subida de varias fotos, de a una por pedido (el hosting limita el
    // tamaño de cada POST; de a una además se ve el avance). ---
    var subir = document.getElementById('oto-subir');
    var subirMsg = document.getElementById('oto-subir-msg');
    if (subir) {
        subir.addEventListener('change', function () {
            var archivos = Array.prototype.slice.call(subir.files || []);
            if (!archivos.length) { return; }
            var ids = [];
            var errores = [];
            subir.disabled = true;
            subirMsg.hidden = false;
            subirMsg.style.color = '';
            var i = 0;
            function siguiente() {
                if (i >= archivos.length) {
                    subir.disabled = false;
                    if (errores.length) {
                        subirMsg.style.color = '#a33';
                        subirMsg.textContent = 'Subidas ' + ids.length + ' de ' + archivos.length + '. Fallaron: ' + errores.join(' · ');
                        if (ids.length) {
                            var a = document.createElement('a');
                            a.href = 'otoscopias.php?filtro=pendientes&id=' + ids[0];
                            a.textContent = ' Clasificar las subidas';
                            subirMsg.appendChild(a);
                        }
                        return;
                    }
                    window.location.href = 'otoscopias.php?filtro=pendientes&id=' + ids[0];
                    return;
                }
                var f = archivos[i];
                subirMsg.textContent = 'Subiendo ' + (i + 1) + ' de ' + archivos.length + ': ' + f.name;
                post({ action: 'subir', photo: f })
                    .then(function (data) {
                        if (data.ok) { ids.push(data.id); } else { errores.push(f.name + ' (' + (data.error || 'error') + ')'); }
                    })
                    .catch(function () { errores.push(f.name + ' (error de red)'); })
                    .then(function () { i++; siguiente(); });
            }
            siguiente();
        });
    }

    // --- Editor ---
    var E = window.OTO_EDITAR;
    var lienzo = document.getElementById('oto-lienzo');
    if (!E || !lienzo) { return; }

    var ctx = lienzo.getContext('2d');
    var C = lienzo.width;
    var W = E.ancho, H = E.alto;
    var theta = E.rotacion, ux = E.centro_x, uy = E.centro_y, S = E.lado;
    var SMAX = Math.sqrt(W * W + H * H);
    var SMIN = Math.max(8, Math.min(W, H) / 8);

    var giroInput = document.getElementById('oto-giro');
    var giroValor = document.getElementById('oto-giro-valor');
    var zoomInput = document.getElementById('oto-zoom');
    var vistaOd = document.getElementById('oto-vista-od');
    var vistaOi = document.getElementById('oto-vista-oi');
    var vistasNota = document.getElementById('oto-vistas-nota');
    var msg = document.getElementById('oto-editor-msg');
    var marcaIzq = document.querySelector('.oto-marca-adelante.izq');
    var marcaDer = document.querySelector('.oto-marca-adelante.der');

    var img = new Image();
    img.onload = function () { sincronizarControles(); dibujar(); };
    img.src = E.original;

    function normalizarGiro(g) {
        g = g % 360;
        if (g > 180) { g -= 360; }
        if (g <= -180) { g += 360; }
        return Math.round(g * 100) / 100;
    }

    function anterior() {
        var r = document.querySelector('input[name="oto-anterior"]:checked');
        return r ? r.value : '';
    }

    // Igual que OtoscopiaBiblioteca::debeEspejar: OD quiere anterior a la
    // derecha, OI a la izquierda.
    function debeEspejar(lado) {
        var a = anterior();
        if (a === 'der') { return lado === 'oi'; }
        if (a === 'izq') { return lado === 'od'; }
        return false;
    }

    function pintar(c, tam, espejar) {
        var g = c.getContext('2d');
        g.setTransform(1, 0, 0, 1, 0, 0);
        g.fillStyle = '#000';
        g.fillRect(0, 0, tam, tam);
        if (!img.complete || !img.naturalWidth) { return; }
        g.save();
        if (espejar) { g.translate(tam, 0); g.scale(-1, 1); }
        g.translate(tam / 2, tam / 2);
        g.scale(tam / S, tam / S);
        g.rotate(theta * Math.PI / 180);
        g.translate(-ux, -uy);
        g.imageSmoothingQuality = 'high';
        g.drawImage(img, 0, 0);
        g.restore();
    }

    function dibujar() {
        pintar(lienzo, C, false);
        var a = anterior();
        marcaIzq.hidden = a !== 'izq';
        marcaDer.hidden = a !== 'der';
        if (a) {
            pintar(vistaOd, vistaOd.width, debeEspejar('od'));
            pintar(vistaOi, vistaOi.width, debeEspejar('oi'));
            vistasNota.hidden = true;
        } else {
            [vistaOd, vistaOi].forEach(function (c) {
                var g = c.getContext('2d');
                g.setTransform(1, 0, 0, 1, 0, 0);
                g.fillStyle = '#000';
                g.fillRect(0, 0, c.width, c.height);
            });
            vistasNota.hidden = false;
        }
    }

    function sincronizarControles() {
        giroInput.value = String(theta);
        giroValor.textContent = (Math.round(theta * 10) / 10) + '°';
        var z = Math.log(S / SMAX) / Math.log(SMIN / SMAX);
        zoomInput.value = String(Math.max(0, Math.min(1, z)));
    }

    function fijarGiro(g) {
        theta = normalizarGiro(g);
        sincronizarControles();
        dibujar();
    }

    giroInput.addEventListener('input', function () { fijarGiro(parseFloat(giroInput.value)); });
    document.querySelectorAll('[data-girar]').forEach(function (b) {
        b.addEventListener('click', function () { fijarGiro(theta + parseFloat(b.getAttribute('data-girar'))); });
    });

    function fijarLado(nuevo) {
        S = Math.max(SMIN, Math.min(SMAX, nuevo));
        sincronizarControles();
        dibujar();
    }
    zoomInput.addEventListener('input', function () {
        var z = parseFloat(zoomInput.value);
        S = SMAX * Math.pow(SMIN / SMAX, z);
        giroValor.textContent = (Math.round(theta * 10) / 10) + '°';
        dibujar();
    });
    lienzo.addEventListener('wheel', function (e) {
        e.preventDefault();
        fijarLado(S * (e.deltaY > 0 ? 1.08 : 1 / 1.08));
    }, { passive: false });

    document.getElementById('oto-restablecer').addEventListener('click', function () {
        theta = 0; ux = W / 2; uy = H / 2; S = Math.min(W, H);
        sincronizarControles();
        dibujar();
    });

    // Arrastre: lo que se movió en pantalla, llevado a px del original
    // (deshaciendo escala y giro).
    var arrastrando = false, ultX = 0, ultY = 0;
    function empezar(x, y) { arrastrando = true; ultX = x; ultY = y; }
    function mover(x, y) {
        if (!arrastrando) { return; }
        var k = C / lienzo.clientWidth;
        var dx = (x - ultX) * k, dy = (y - ultY) * k;
        ultX = x; ultY = y;
        var t = theta * Math.PI / 180;
        var f = S / C;
        ux -= f * (dx * Math.cos(t) + dy * Math.sin(t));
        uy -= f * (-dx * Math.sin(t) + dy * Math.cos(t));
        ux = Math.max(0, Math.min(W, ux));
        uy = Math.max(0, Math.min(H, uy));
        dibujar();
    }
    function terminar() { arrastrando = false; }
    lienzo.addEventListener('mousedown', function (e) { empezar(e.clientX, e.clientY); });
    window.addEventListener('mousemove', function (e) { mover(e.clientX, e.clientY); });
    window.addEventListener('mouseup', terminar);
    lienzo.addEventListener('touchstart', function (e) { empezar(e.touches[0].clientX, e.touches[0].clientY); }, { passive: true });
    lienzo.addEventListener('touchmove', function (e) {
        mover(e.touches[0].clientX, e.touches[0].clientY);
        e.preventDefault();
    }, { passive: false });
    lienzo.addEventListener('touchend', terminar);

    document.querySelectorAll('input[name="oto-anterior"]').forEach(function (r) {
        r.addEventListener('change', dibujar);
    });

    function aviso(texto, error) {
        msg.textContent = texto;
        msg.style.color = error ? '#a33' : '#2a7a2a';
        msg.hidden = false;
    }

    var botones = Array.prototype.slice.call(document.querySelectorAll('.oto-acciones button'));
    function ocupado(si) { botones.forEach(function (b) { b.disabled = si; }); }

    function guardar(yLuego) {
        ocupado(true);
        aviso('Guardando...', false);
        post({
            action: 'guardar',
            id: E.id,
            rotacion: theta,
            centro_x: ux,
            centro_y: uy,
            lado: S,
            anterior: anterior(),
            tipo: document.getElementById('oto-tipo').value,
            notas: document.getElementById('oto-notas').value
        }).then(function (data) {
            ocupado(false);
            if (!data.ok) { aviso(data.error || 'No se pudo guardar.', true); return; }
            var extra = data.casos ? ' Se reescribieron ' + data.casos + ' foto(s) de casos.' : '';
            if (yLuego) {
                if (data.siguiente) {
                    window.location.href = E.siguienteUrl.replace('__ID__', data.siguiente);
                } else {
                    window.location.href = 'otoscopias.php';
                }
                return;
            }
            aviso('Guardada.' + extra, false);
        }).catch(function () {
            ocupado(false);
            aviso('Error de red al guardar.', true);
        });
    }

    document.getElementById('oto-guardar').addEventListener('click', function () { guardar(false); });
    document.getElementById('oto-guardar-siguiente').addEventListener('click', function () { guardar(true); });
    document.getElementById('oto-borrar').addEventListener('click', function () {
        if (!confirm('¿Sacar la foto #' + E.id + ' de la base? Los casos que ya la usan conservan su copia.')) { return; }
        ocupado(true);
        post({ action: 'borrar', id: E.id }).then(function (data) {
            if (data.ok) { window.location.href = E.volver; return; }
            ocupado(false);
            aviso(data.error || 'No se pudo sacar.', true);
        }).catch(function () {
            ocupado(false);
            aviso('Error de red.', true);
        });
    });
})();
