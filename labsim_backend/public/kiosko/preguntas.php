<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/OscePreguntas.php';

/**
 * Tablet de preguntas del OSCE para las tablets kiosko viejas (Android 4.1,
 * por http). Hace lo mismo que student/osce_estacion.php (número → "¿Eres
 * X?" → preguntas con su tiempo → entrega, sola al llegar a cero) y usa la
 * misma API (api/osce_tablet.php vía kiosko/api_tablet.php), pero escrita en
 * ES5 y con CSS que ese navegador entiende. La página moderna no se toca.
 */

header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store');
header('Referrer-Policy: no-referrer');

$k = (string) ($_GET['k'] ?? '');
$est = OscePreguntas::estacionPorToken($k);
$v = static fn (string $f): string => (string) (@filemtime(__DIR__ . '/' . $f) ?: time());
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<meta name="robots" content="noindex, nofollow">
<title>OSCE · <?= htmlspecialchars($est['titulo'] ?? 'Estación') ?></title>
<link rel="stylesheet" href="kiosko.css?v=<?= $v('kiosko.css') ?>">
<style>
.preg .enun { margin-bottom: 10px; }
.op { display: block; padding: 12px 12px 12px 52px; border: 2px solid #ddd; border-radius: 8px; margin: 8px 0; position: relative; background: #fff; }
.op input { position: absolute; left: 14px; top: 50%; margin-top: -12px; width: 24px; height: 24px; }
.op.marcada { border-color: #5d1049; background: #f5edf3; }
.preg textarea { width: 100%; height: 160px; font-size: 18px; padding: 8px; border: 1px solid #bbb; border-radius: 6px; }
.preg-img { display: block; max-width: 100%; max-height: 380px; margin: 6px 0 10px; border: 1px solid #ddd; border-radius: 6px; background: #fff; }
.listo { text-align: center; padding: 50px 10px; font-size: 24px; }
</style>
</head>
<body>
<?php if ($est === null || $est['tipo'] !== 'preguntas'): ?>
<div class="k-tarjeta"><h1>Estación no encontrada</h1><p>El enlace de esta tablet no es válido. Pide al docente que lo copie de nuevo desde la estación.</p></div>
</body></html>
<?php exit; endif; ?>

<div class="k-barra"><table><tr>
    <td class="k-izq"><div class="k-tit"><?= htmlspecialchars($est['titulo']) ?></div><div class="k-sub" id="quien"></div></td>
    <td class="k-der"><div class="k-cuenta" id="cuenta"></div></td>
</tr></table></div>

<div class="k-centro" id="p-entrar">
    <h1>Escribe tu número</h1>
    <p class="muted">El número grande de tu tarjeta.</p>
    <form id="f-entrar" autocomplete="off">
        <input type="tel" id="codigo" class="k-numero" maxlength="8" autocomplete="off" aria-label="Número">
        <br><br><button type="submit" class="k-btn">Entrar</button>
    </form>
    <div class="k-error" id="error-entrar"></div>
</div>

<div class="k-centro" id="p-confirmar" style="display:none">
    <h1 id="conf-numero"></h1>
    <p style="font-size:26px;">¿Eres <strong id="conf-nombre"></strong>?</p>
    <p class="muted">Tu tiempo parte cuando confirmas.</p>
    <button type="button" class="k-btn" id="conf-si">Sí, soy yo: empezar</button><span class="k-espacio"></span>
    <button type="button" class="k-btn k-btn--claro" id="conf-no">No soy yo</button>
    <div class="k-error" id="error-confirmar"></div>
</div>

<div id="p-preguntas" style="display:none">
    <div class="k-aviso" id="aviso-fin" style="display:none">Queda menos de 1 minuto: al llegar a cero tus respuestas se entregan solas.</div>
    <div id="preguntas"></div>
</div>

<div class="k-pie" id="pie" style="display:none"><table><tr>
    <td style="text-align:left"><span class="muted" id="guardado"></span></td>
    <td style="text-align:right"><button type="button" class="k-btn" id="entregar">Entregar</button></td>
</tr></table></div>

<div class="listo" id="p-listo" style="display:none">
    <p><strong id="listo-titulo">Entregado</strong></p>
    <p class="muted" style="font-size:18px">Pasa a la siguiente estación. Tu resultado aparecerá en la página de tu tarjeta cuando el docente lo publique.</p>
</div>

<script src="kiosko.js?v=<?= $v('kiosko.js') ?>"></script>
<script>
(function () {
    'use strict';
    var K = <?= json_encode($k) ?>;
    var API = 'api_tablet.php';
    var $ = Kiosko.$, esc = Kiosko.esc;
    var sesion = null;          // {codigo, numero, ventana, preguntas}
    var respuestas = {};
    var pendiente = false, timer = null, enviando = false, entregando = false, autoEntrega = false;
    var porConfirmar = null;

    function mostrar(cual) {
        var ids = ['p-entrar', 'p-confirmar', 'p-preguntas', 'p-listo'];
        for (var i = 0; i < ids.length; i++) Kiosko.mostrar(ids[i], ids[i] === cual);
        Kiosko.mostrar('pie', cual === 'p-preguntas');
    }
    function post(datos, ok, mal) {
        datos.k = K;
        Kiosko.post(API, datos, ok, mal);
    }
    function claveLocal(codigo) { return 'osce_q_' + K + '_' + codigo; }
    function guardarLocal() {
        if (!sesion) return;
        try { localStorage.setItem(claveLocal(sesion.codigo), JSON.stringify({ respuestas: respuestas, pendiente: pendiente })); } catch (e) {}
    }

    // -- Entrar: número, luego confirma su nombre y parte su tiempo -----------
    $('f-entrar').addEventListener('submit', function (e) {
        e.preventDefault();
        var codigo = $('codigo').value.replace(/^\s+|\s+$/g, '');
        if (!codigo) return;
        $('error-entrar').textContent = 'Buscando…';
        post({ accion: 'entrar', codigo: codigo }, function (d) {
            porConfirmar = codigo;
            $('error-entrar').textContent = '';
            $('conf-numero').textContent = 'N.º ' + d.numero;
            $('conf-nombre').textContent = d.nombre;
            $('error-confirmar').textContent = '';
            $('codigo').value = '';
            $('codigo').blur();
            mostrar('p-confirmar');
        }, function (msg) { $('error-entrar').textContent = msg; });
    }, false);
    $('conf-no').addEventListener('click', function () {
        porConfirmar = null;
        mostrar('p-entrar');
        $('error-entrar').textContent = 'Revisa el número de tu tarjeta.';
    }, false);
    $('conf-si').addEventListener('click', function () {
        if (!porConfirmar) return;
        var btn = this;
        btn.disabled = true;
        post({ accion: 'confirmar', codigo: porConfirmar }, function (d) {
            btn.disabled = false;
            porConfirmar = null;
            sesion = d;
            autoEntrega = false;
            pendiente = false;
            respuestas = {};
            for (var i = 0; i < d.preguntas.length; i++) {
                if (d.preguntas[i].respuesta !== null) respuestas[d.preguntas[i].id] = d.preguntas[i].respuesta;
            }
            try {
                var local = JSON.parse(localStorage.getItem(claveLocal(d.codigo)) || 'null');
                if (local && local.pendiente) { respuestas = local.respuestas; pendiente = true; }
            } catch (err) {}
            pintar();
            mostrar('p-preguntas');
            window.scrollTo(0, 0);
            $('quien').textContent = 'N.º ' + d.numero;
            if (pendiente) aGuardar();
        }, function (msg) { btn.disabled = false; $('error-confirmar').textContent = msg; });
    }, false);

    // -- Preguntas ------------------------------------------------------------
    function pintar() {
        var h = '';
        for (var n = 0; n < sesion.preguntas.length; n++) {
            var q = sesion.preguntas[n];
            var pts = (Math.round(q.puntaje * 100) / 100).toString().replace('.', ',');
            h += '<div class="k-tarjeta preg" data-q="' + q.id + '"><div class="enun"><strong>' + (n + 1) + '.</strong> '
               + esc(q.enunciado).replace(/\n/g, '<br>') + ' <span class="muted">(' + pts + ' pt)</span></div>';
            if (q.imagen) {
                h += '<img class="preg-img" alt="Imagen de la pregunta" src="api_imagen.php?k=' + encodeURIComponent(K) + '&q=' + q.id + '">';
            }
            if (q.tipo === 'alternativa') {
                if (q.varias) h += '<p class="muted">Marca todas las correctas. Cada marca incorrecta descuenta.</p>';
                var marcadas = respuestas[q.id] || [];
                for (var j = 0; j < q.opciones.length; j++) {
                    var op = q.opciones[j], si = marcadas.indexOf(op.i) >= 0;
                    h += '<label class="op' + (si ? ' marcada' : '') + '"><input type="' + (q.varias ? 'checkbox' : 'radio')
                       + '" name="q' + q.id + '" value="' + op.i + '"' + (si ? ' checked' : '') + '>'
                       + '<span>' + esc(op.texto) + '</span></label>';
                }
            } else {
                h += '<textarea data-texto placeholder="Escribe tu respuesta">' + esc(respuestas[q.id] || '') + '</textarea>';
            }
            h += '</div>';
        }
        $('preguntas').innerHTML = h;
        $('guardado').textContent = '';
        $('entregar').textContent = 'Entregar';
        entregando = false;
    }
    function leer(e) {
        var cont = Kiosko.cerca(e.target, '[data-q]', $('preguntas'));
        if (!cont) return;
        var id = +cont.getAttribute('data-q');
        if (e.target.hasAttribute('data-texto')) {
            respuestas[id] = e.target.value;
        } else if (e.type === 'change') {
            var lista = [], inputs = cont.getElementsByTagName('input');
            for (var i = 0; i < inputs.length; i++) {
                var lab = Kiosko.cerca(inputs[i], 'label', cont);
                if (inputs[i].checked) lista.push(+inputs[i].value);
                if (lab) lab.className = 'op' + (inputs[i].checked ? ' marcada' : '');
            }
            respuestas[id] = lista;
        } else {
            return;
        }
        aGuardar();
    }
    $('preguntas').addEventListener('change', leer, false);
    $('preguntas').addEventListener('input', leer, false);

    function aGuardar() {
        pendiente = true;
        guardarLocal();
        $('guardado').textContent = 'Guardando…';
        clearTimeout(timer);
        timer = setTimeout(function () { enviar(false); }, 900);
    }
    function enviar(entregar) {
        if (!sesion) return;
        if (enviando) { clearTimeout(timer); timer = setTimeout(function () { enviar(entregar); }, 400); return; }
        enviando = true;
        pendiente = false;
        var codigo = sesion.codigo;
        post({ accion: 'guardar', codigo: codigo, respuestas: JSON.stringify(respuestas), entregar: entregar ? '1' : '' }, function () {
            enviando = false;
            guardarLocal();
            if (entregar) terminar(codigo, 'Entregado');
            else $('guardado').textContent = 'Guardado';
        }, function (msg, status) {
            enviando = false;
            if (status && /ya entregaste|no te toca|termin|acab/i.test(msg)) {
                terminar(codigo, msg);        // el servidor ya la cerró
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
        post({ accion: 'corregir', codigo: codigo });    // la IA corrige en el servidor; no se espera
        try { localStorage.removeItem(claveLocal(codigo)); } catch (e) {}
        sesion = null;
        respuestas = {};
        $('listo-titulo').textContent = titulo;
        $('quien').textContent = '';
        mostrar('p-listo');
        window.scrollTo(0, 0);
        setTimeout(function () { if (!sesion) mostrar('p-entrar'); }, 8000);
    }
    $('entregar').addEventListener('click', function () {
        if (!sesion) return;
        if (!entregando) {
            entregando = true;
            this.textContent = '¿Seguro? Toca de nuevo';
            var b = this;
            setTimeout(function () { if (entregando && sesion) { entregando = false; b.textContent = 'Entregar'; } }, 4000);
            return;
        }
        clearTimeout(timer);
        enviar(true);
    }, false);

    // -- Reloj (si la red falla al abrir, reintenta) -----------------------------
    function arrancarReloj() {
        Kiosko.get(API + '?k=' + encodeURIComponent(K), function (info) {
            Kiosko.reloj('api_reloj.php?r=' + info.reloj, function (d, reloj, t) {
                var c = $('cuenta');
                if (!sesion) {
                    c.innerHTML = reloj && (reloj.fase === 'cambio' || reloj.fase === 'entre_vueltas') && reloj.restante_s !== null
                        ? 'Cambio ' + Kiosko.mmss(reloj.restante_s) : '';
                    c.className = 'k-cuenta';
                    return;
                }
                if (t === null) return;
                var queda = sesion.ventana.fin_s - t;
                c.textContent = Kiosko.mmss(queda);
                c.className = 'k-cuenta' + (queda <= 60 ? ' k-rojo' : '');
                Kiosko.mostrar('aviso-fin', queda <= 60 && queda > 0);
                if (queda <= 0 && !autoEntrega) {     // se acabó el tiempo: entrega sola
                    autoEntrega = true;
                    clearTimeout(timer);
                    enviar(true);
                }
            });
        }, function () { setTimeout(arrancarReloj, 5000); });
    }
    arrancarReloj();
})();
</script>
</body>
</html>
