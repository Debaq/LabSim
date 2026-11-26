/*
 * Base común de las páginas para las tablets kiosko viejas (Lenovo IdeaTab
 * A1000L-F: WebView de Android 4.1, WebKit 534, nivel Safari 5.1). Solo ES5:
 * nada de flechas, let/const, fetch, Promise, closest(), NodeList.forEach,
 * performance.now ni requestAnimationFrame. Si las tablets se cambian, esta
 * carpeta entera se puede borrar: las páginas modernas son
 * admin/osce_evaluar.php y student/osce_estacion.php.
 *
 *   Kiosko.$(id), Kiosko.esc(s), Kiosko.cerca(el, selector, tope)
 *   Kiosko.get(url, ok, mal) / Kiosko.post(url, datos, ok, mal)   (JSON, con tiempo límite)
 *   Kiosko.mostrar(el, si)
 *   Kiosko.reloj(url, alTic)       cuenta del OSCE: alTic(datos, reloj, t)
 *   Kiosko.mmss(s)
 * Los errores de JavaScript se mandan al servidor (kiosko/error.php): en
 * estas tablets no hay depuración remota.
 */
(function () {
    'use strict';

    var BASE = (function () {
        var s = document.getElementsByTagName('script');
        var src = s[s.length - 1].src || '';
        return src.replace(/[^\/]*$/, '');
    })();

    function $(id) { return document.getElementById(id); }

    function esc(s) {
        return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    // closest() no existe en WebKit 534.
    function coincide(el, sel) {
        var f = el.matches || el.webkitMatchesSelector || el.msMatchesSelector;
        return f ? f.call(el, sel) : false;
    }
    function cerca(el, sel, tope) {
        while (el && el.nodeType === 1 && el !== tope) {
            if (coincide(el, sel)) return el;
            el = el.parentNode;
        }
        return null;
    }

    function mostrar(el, si) {
        if (typeof el === 'string') el = $(el);
        if (el) el.style.display = si ? '' : 'none';
    }

    function codificar(datos) {
        var partes = [];
        for (var k in datos) {
            if (Object.prototype.hasOwnProperty.call(datos, k)) {
                partes.push(encodeURIComponent(k) + '=' + encodeURIComponent(datos[k] == null ? '' : datos[k]));
            }
        }
        return partes.join('&');
    }

    // XHR con tiempo límite propio (xhr.timeout no existe en este motor).
    function pedir(metodo, url, cuerpo, ok, mal) {
        var xhr = new XMLHttpRequest(), listo = false;
        var corte = setTimeout(function () {
            if (listo) return;
            listo = true;
            try { xhr.abort(); } catch (e) {}
            if (mal) mal('Sin conexión', 0);
        }, 15000);
        xhr.onreadystatechange = function () {
            if (xhr.readyState !== 4 || listo) return;
            listo = true;
            clearTimeout(corte);
            var d = null;
            try { d = JSON.parse(xhr.responseText); } catch (e) {}
            if (xhr.status >= 200 && xhr.status < 300 && d !== null) {
                if (ok) ok(d);
            } else if (mal) {
                mal(d && d.error ? d.error : (xhr.status ? 'Error ' + xhr.status : 'Sin conexión'), xhr.status);
            }
        };
        xhr.open(metodo, url, true);
        if (cuerpo !== null) xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
        xhr.send(cuerpo);
    }
    function get(url, ok, mal) {
        pedir('GET', url + (url.indexOf('?') >= 0 ? '&' : '?') + '_=' + Date.now(), null, ok, mal);
    }
    function post(url, datos, ok, mal) { pedir('POST', url, codificar(datos), ok, mal); }

    function mmss(s) {
        s = Math.max(0, Math.ceil(s));
        var m = Math.floor(s / 60), r = s % 60;
        return m + ':' + (r < 10 ? '0' : '') + r;
    }

    // Mismo reloj que js/osce_reloj.js: el servidor decide la fase por turnos;
    // entre pedidos la cuenta baja con el reloj local.
    function reloj(url, alTic, cadaMs) {
        var datos = null, base = 0, baseLocal = 0, pidiendo = false;
        function traer() {
            pidiendo = true;
            get(url, function (d) {
                setTimeout(function () { pidiendo = false; }, 1500);
                if (d.error) return;
                datos = d;
                base = d.transcurrido_s;
                baseLocal = Date.now();
                tic();
            }, function () { pidiendo = false; });
        }
        function tic() {
            if (!datos) return;
            var t = null, r = null;
            if (base !== null && base !== undefined) {
                var corre = !datos.pausado && datos.estado === 'en_curso';
                var dt = corre ? (Date.now() - baseLocal) / 1000 : 0;
                t = base + dt;
                if (datos.reloj) {
                    r = {};
                    for (var k in datos.reloj) r[k] = datos.reloj[k];
                    if (r.restante_s !== null && r.restante_s !== undefined) r.restante_s = Math.max(0, r.restante_s - dt);
                    if (corre && r.restante_s === 0 && r.fase !== 'estacion' && !pidiendo) traer();
                }
            }
            alTic(datos, r, t);
        }
        traer();
        setInterval(traer, cadaMs || 5000);
        setInterval(tic, 500);
        return { refrescar: traer };
    }

    // Errores al servidor (máximo 20 por carga, para no inundar).
    var enviados = 0;
    window.onerror = function (msg, url, linea) {
        if (enviados++ >= 20) return false;
        try {
            post(BASE + 'error.php', { msg: String(msg), url: String(url || location.href), linea: linea || 0 });
        } catch (e) {}
        return false;
    };

    window.Kiosko = { $: $, esc: esc, cerca: cerca, mostrar: mostrar, get: get, post: post, mmss: mmss, reloj: reloj };
})();
