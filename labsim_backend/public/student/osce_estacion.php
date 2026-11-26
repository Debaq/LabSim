<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/OscePreguntas.php';

/**
 * Tablet de una estación de preguntas del OSCE. El docente la abre una vez
 * (enlace o QR en admin/osce_estacion.php) y queda en la estación; cada
 * alumno escribe su código, responde y entrega (o la tablet entrega sola al
 * terminar su tiempo). Toda la lógica de permisos está en api/osce_tablet.php.
 */

header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store');
header('Referrer-Policy: no-referrer');

$k = (string) ($_GET['k'] ?? '');
$est = OscePreguntas::estacionPorToken($k);
$cssV = static fn (string $path): string => (string) (@filemtime($path) ?: time());
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>OSCE · <?= htmlspecialchars($est['titulo'] ?? 'Estación') ?></title>
<link rel="stylesheet" href="../css/tokens.css?v=<?= $cssV(__DIR__ . '/../css/tokens.css') ?>">
<link rel="stylesheet" href="../css/base.css?v=<?= $cssV(__DIR__ . '/../css/base.css') ?>">
<style>
body { max-width: 52rem; margin: 0 auto; padding: 0 1rem 6rem; font-size: 1.1rem; }
.barra { position: sticky; top: 0; z-index: 5; background: var(--color-bg, #f7f7f7); padding: 0.7rem 0;
         display: flex; justify-content: space-between; align-items: center; gap: 1rem; border-bottom: 1px solid var(--color-border, #ddd); }
.barra .tit { font-weight: 700; }
.barra .cuenta { font: 700 2rem ui-monospace, monospace; }
.barra .cuenta.ultimo { color: #b91c1c; }
.pantalla { margin-top: 1.5rem; }
.entrar { text-align: center; padding: 2rem 1rem; }
.entrar input { font: 700 2.2rem ui-monospace, monospace; text-align: center; letter-spacing: 0.1em; max-width: 14rem; text-transform: uppercase; }
.entrar button { font-size: 1.3rem; padding: 0.7rem 2rem; margin-top: 1rem; }
.error-grande { color: #b91c1c; font-weight: 600; margin-top: 1rem; min-height: 1.5rem; }
.preg { background: var(--color-surface, #fff); border: 1px solid var(--color-border, #ddd); border-radius: 0.7rem; padding: 1rem; margin: 1rem 0; }
.preg .enun { margin-bottom: 0.8rem; }
.op { display: flex; gap: 0.8rem; align-items: center; padding: 0.75rem 0.8rem; border: 2px solid var(--color-border, #ddd);
      border-radius: 0.5rem; margin: 0.45rem 0; cursor: pointer; }
.op input { width: 1.4rem; height: 1.4rem; flex: none; }
.op:has(input:checked) { border-color: var(--color-primary, #7a1f3d); background: var(--color-surface-2, #f4eef1); }
.preg textarea { width: 100%; min-height: 9rem; font-size: 1.05rem; }
.pie { position: fixed; left: 0; right: 0; bottom: 0; background: var(--color-surface, #fff); border-top: 1px solid var(--color-border, #ddd);
       padding: 0.7rem 1rem; display: flex; justify-content: center; align-items: center; gap: 1.2rem; }
.pie button { font-size: 1.2rem; padding: 0.7rem 2rem; }
.listo { text-align: center; padding: 3rem 1rem; font-size: 1.4rem; }
.preg-img { display:block; max-width:100%; max-height:60vh; margin:0.4rem 0 0.6rem; border:1px solid #ddd; border-radius:6px; background:#fff; }
</style>
</head>
<body>
<?php if ($est === null || $est['tipo'] !== 'preguntas'): ?>
<div class="card" style="margin-top:2rem;"><h1>Estación no encontrada</h1><p>El enlace de esta tablet no es válido. Pide al docente que lo abra de nuevo desde la estación.</p></div>
</body></html>
<?php exit; endif; ?>

<div class="barra">
    <div>
        <div class="tit"><?= htmlspecialchars($est['titulo']) ?></div>
        <div class="muted" id="quien"></div>
    </div>
    <div class="cuenta" id="cuenta"></div>
</div>

<div class="pantalla entrar" id="p-entrar">
    <h1>Escribe tu número</h1>
    <p class="muted">El número grande de tu tarjeta.</p>
    <form id="f-entrar" autocomplete="off">
        <input type="text" id="codigo" maxlength="8" inputmode="numeric" autocapitalize="characters" spellcheck="false" aria-label="Número">
        <br><button type="submit" class="btn">Entrar</button>
    </form>
    <div class="error-grande" id="error-entrar"></div>
</div>

<div class="pantalla entrar" id="p-confirmar" hidden>
    <h1 id="conf-numero"></h1>
    <p style="font-size:1.4rem;">¿Eres <strong id="conf-nombre"></strong>?</p>
    <p class="muted">Tu tiempo parte cuando confirmas.</p>
    <button type="button" class="btn" id="conf-si">Sí, soy yo: empezar</button>
    <button type="button" class="btn btn--ghost" id="conf-no" style="margin-left:0.6rem;">No soy yo</button>
    <div class="error-grande" id="error-confirmar"></div>
</div>

<div class="pantalla" id="p-preguntas" hidden>
    <p id="aviso-fin" hidden style="background:#fde8e8;color:#991b1b;border-radius:0.5rem;padding:0.6rem 0.9rem;font-weight:600;margin:0.8rem 0 0;">Queda menos de 1 minuto: al llegar a cero tus respuestas se entregan solas.</p>
    <div id="preguntas"></div>
    <div class="pie">
        <span class="muted" id="guardado"></span>
        <button type="button" class="btn" id="entregar">Entregar</button>
    </div>
</div>

<div class="pantalla listo" id="p-listo" hidden>
    <p><strong id="listo-titulo">Entregado ✓</strong></p>
    <p class="muted" id="listo-texto">Pasa a la siguiente estación. Tu resultado aparecerá en la página de tu tarjeta cuando el docente lo publique.</p>
</div>

<script src="../js/osce_reloj.js?v=<?= $cssV(__DIR__ . '/../js/osce_reloj.js') ?>"></script>
<script>
(function () {
    'use strict';
    var K = <?= json_encode($k) ?>;
    var API = '../api/osce_tablet.php';
    var $ = function (id) { return document.getElementById(id); };
    var sesion = null;          // {codigo, ventana, preguntas}
    var respuestas = {};
    var pendiente = false, timer = null, enviando = false, entregando = false;
    var tActual = null, autoEntrega = false;

    function esc(s) {
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    function mostrar(cual) {
        ['p-entrar', 'p-confirmar', 'p-preguntas', 'p-listo'].forEach(function (id) { $(id).hidden = id !== cual; });
    }
    function post(datos) {
        var fd = new FormData();
        fd.append('k', K);
        Object.keys(datos).forEach(function (c) { fd.append(c, datos[c]); });
        return fetch(API, { method: 'POST', body: fd }).then(function (r) {
            return r.json().then(function (d) { if (!r.ok) throw new Error(d.error || 'Error'); return d; });
        });
    }
    function claveLocal() { return 'osce_q_' + K + '_' + (sesion ? sesion.codigo : ''); }
    function guardarLocal() {
        try { localStorage.setItem(claveLocal(), JSON.stringify({ respuestas: respuestas, pendiente: pendiente })); } catch (e) {}
    }

    // -- Entrar: número, luego confirma su nombre y parte su tiempo -----------
    var porConfirmar = null;
    $('f-entrar').addEventListener('submit', function (e) {
        e.preventDefault();
        var codigo = $('codigo').value.trim();
        if (!codigo) return;
        $('error-entrar').textContent = '';
        post({ accion: 'entrar', codigo: codigo }).then(function (d) {
            porConfirmar = codigo;
            $('conf-numero').textContent = 'N.º ' + d.numero;
            $('conf-nombre').textContent = d.nombre;
            $('error-confirmar').textContent = '';
            $('codigo').value = '';
            mostrar('p-confirmar');
        }).catch(function (err) { $('error-entrar').textContent = err.message; });
    });
    $('conf-no').addEventListener('click', function () {
        porConfirmar = null;
        mostrar('p-entrar');
        $('error-entrar').textContent = 'Revisa el número de tu tarjeta.';
        $('codigo').focus();
    });
    $('conf-si').addEventListener('click', function () {
        if (!porConfirmar) return;
        var codigo = porConfirmar, btn = this;
        btn.disabled = true;
        post({ accion: 'confirmar', codigo: codigo }).then(function (d) {
            btn.disabled = false;
            porConfirmar = null;
            sesion = d;
            autoEntrega = false;
            respuestas = {};
            d.preguntas.forEach(function (q) { if (q.respuesta !== null) respuestas[q.id] = q.respuesta; });
            try {
                var local = JSON.parse(localStorage.getItem(claveLocal()) || 'null');
                if (local && local.pendiente) { respuestas = local.respuestas; pendiente = true; }
            } catch (err) {}
            pintar();
            mostrar('p-preguntas');
            $('quien').textContent = 'N.º ' + d.numero;
            if (pendiente) aGuardar();
        }).catch(function (err) { btn.disabled = false; $('error-confirmar').textContent = err.message; });
    });

    // -- Preguntas ------------------------------------------------------------
    function pintar() {
        var h = '';
        sesion.preguntas.forEach(function (q, n) {
            var pts = (Math.round(q.puntaje * 100) / 100).toString().replace('.', ',');
            h += '<div class="preg" data-q="' + q.id + '"><div class="enun"><strong>' + (n + 1) + '.</strong> '
               + esc(q.enunciado).replace(/\n/g, '<br>') + ' <span class="muted">(' + pts + ' pt)</span></div>';
            if (q.imagen) {
                h += '<img class="preg-img" alt="Imagen de la pregunta" src="../api/osce_imagen.php?k=' + encodeURIComponent(K) + '&q=' + q.id + '">';
            }
            if (q.tipo === 'alternativa') {
                if (q.varias) h += '<p class="muted">Marca todas las correctas. Cada marca incorrecta descuenta.</p>';
                var marcadas = respuestas[q.id] || [];
                q.opciones.forEach(function (op) {
                    var tipo = q.varias ? 'checkbox' : 'radio';
                    var ch = marcadas.indexOf(op.i) >= 0 ? ' checked' : '';
                    h += '<label class="op"><input type="' + tipo + '" name="q' + q.id + '" value="' + op.i + '"' + ch + '>'
                       + '<span>' + esc(op.texto) + '</span></label>';
                });
            } else {
                h += '<textarea data-texto placeholder="Escribe tu respuesta">' + esc(respuestas[q.id] || '') + '</textarea>';
            }
            h += '</div>';
        });
        $('preguntas').innerHTML = h;
        $('guardado').textContent = '';
        $('entregar').textContent = 'Entregar';
        entregando = false;
    }
    $('preguntas').addEventListener('change', leer);
    $('preguntas').addEventListener('input', leer);
    function leer(e) {
        var cont = e.target.closest('[data-q]');
        if (!cont) return;
        var id = +cont.dataset.q;
        if (e.target.hasAttribute('data-texto')) {
            respuestas[id] = e.target.value;
        } else if (e.type === 'change') {
            respuestas[id] = Array.prototype.map.call(cont.querySelectorAll('input:checked'), function (i) { return +i.value; });
        } else {
            return;
        }
        aGuardar();
    }
    function aGuardar() {
        pendiente = true;
        guardarLocal();
        $('guardado').textContent = 'Guardando…';
        clearTimeout(timer);
        timer = setTimeout(function () { enviar(false); }, 900);
    }
    function enviar(entregar) {
        if (!sesion) return Promise.resolve();
        if (enviando) { clearTimeout(timer); timer = setTimeout(function () { enviar(entregar); }, 400); return Promise.resolve(); }
        enviando = true;
        pendiente = false;
        var codigo = sesion.codigo;
        return post({ accion: 'guardar', codigo: codigo, respuestas: JSON.stringify(respuestas), entregar: entregar ? '1' : '' })
            .then(function () {
                enviando = false;
                guardarLocal();
                if (entregar) terminar(codigo, 'Entregado ✓');
                else $('guardado').textContent = 'Guardado ✓';
            })
            .catch(function (err) {
                enviando = false;
                if (/ya entregaste|no te toca|terminó/i.test(err.message)) {
                    // El servidor ya la cerró (o se acabó la ventana): no hay más que hacer acá.
                    terminar(codigo, err.message);
                    return;
                }
                pendiente = true;
                guardarLocal();
                $('guardado').textContent = 'Sin conexión: tus respuestas quedan en la tablet, reintentando…';
                clearTimeout(timer);
                timer = setTimeout(function () { enviar(entregar); }, 4000);
            });
    }
    function terminar(codigo, titulo) {
        // La IA corrige el desarrollo en el servidor; la tablet no espera.
        post({ accion: 'corregir', codigo: codigo }).catch(function () {});
        try { localStorage.removeItem('osce_q_' + K + '_' + codigo); } catch (e) {}
        sesion = null;
        respuestas = {};
        $('listo-titulo').textContent = titulo;
        $('quien').textContent = '';
        mostrar('p-listo');
        setTimeout(function () { if (!sesion) { mostrar('p-entrar'); $('codigo').focus(); } }, 8000);
    }
    $('entregar').addEventListener('click', function () {
        if (!sesion) return;
        if (!entregando) {
            entregando = true;
            this.textContent = '¿Seguro? Toca de nuevo para entregar';
            var b = this;
            setTimeout(function () { if (entregando && sesion) { entregando = false; b.textContent = 'Entregar'; } }, 4000);
            return;
        }
        clearTimeout(timer);
        enviar(true);
    });

    // -- Reloj ------------------------------------------------------------------
    fetch(API + '?k=' + encodeURIComponent(K)).then(function (r) { return r.json(); }).then(function (info) {
        OsceReloj.iniciar('../api/osce_reloj.php?r=' + info.reloj, function (d, reloj, t) {
            tActual = t;
            var c = $('cuenta');
            if (!sesion) {
                // Sin alumno: en el cambio, cuánto falta para que la estación reciba.
                c.textContent = reloj && (reloj.fase === 'cambio' || reloj.fase === 'entre_vueltas') && reloj.restante_s !== null
                    ? 'Cambio ' + OsceReloj.mmss(reloj.restante_s) : '';
                c.classList.remove('ultimo');
                return;
            }
            if (t === null) return;
            var queda = sesion.ventana.fin_s - t;
            c.textContent = OsceReloj.mmss(queda);
            c.classList.toggle('ultimo', queda <= 60);
            $('aviso-fin').hidden = !(queda <= 60 && queda > 0);
            // Se acabó el tiempo: entrega sola con lo que haya.
            if (queda <= 0 && !autoEntrega) {
                autoEntrega = true;
                clearTimeout(timer);
                enviar(true);
            }
        });
    });
    $('codigo').focus();
})();
</script>
</body>
</html>
