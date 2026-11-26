<?php

declare(strict_types=1);

/**
 * Página de prueba para las tablets kiosko (Android 4.1). Sirve para ir
 * ajustando el hosting hasta que la tablet la vea: si carga, la conexión
 * por http funciona; después corre en la tablet lo que necesitan
 * kiosko/pauta.php y kiosko/preguntas.php (JS ES5, XHR, PHP, localStorage)
 * y muestra cada cosa con OK o FALLA.
 *
 * Cada visita (GET) y cada resultado (POST ?registrar=1) se anotan en
 * data/kiosko_pruebas.log, que se lee de lejos con
 * `python3 scripts/consola.py leer kiosko_pruebas.log`: así se sabe qué pasó en
 * la tablet sin mirarla. No guarda nada personal: IP, navegador y resultados.
 * No depende de bootstrap.php, para que una falla del resto no la tape.
 */

$log = __DIR__ . '/../../data/kiosko_pruebas.log';
$https = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
    || strtolower((string) ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '')) === 'https';
$ua = substr((string) ($_SERVER['HTTP_USER_AGENT'] ?? ''), 0, 200);

$anotar = static function (array $fila) use ($log): void {
    if (!is_dir(dirname($log))) {
        return;
    }
    if (@filesize($log) > 300000) {
        @rename($log, $log . '.1');
    }
    $fila = ['hora' => date('Y-m-d H:i:s'), 'ip' => $_SERVER['REMOTE_ADDR'] ?? ''] + $fila;
    @file_put_contents($log, json_encode($fila, JSON_UNESCAPED_UNICODE | JSON_UNESCAPED_SLASHES) . "\n", FILE_APPEND | LOCK_EX);
};

header('Cache-Control: no-store');

if (isset($_GET['registrar'])) {
    $res = json_decode((string) ($_POST['resultados'] ?? ''), true);
    $anotar(['tipo' => 'resultados', 'protocolo' => $https ? 'https' : 'http', 'ua' => $ua,
             'resultados' => is_array($res) ? array_slice($res, 0, 60) : null]);
    header('Content-Type: application/json; charset=utf-8');
    echo json_encode(['ok' => true, 'guardado' => is_dir(dirname($log))]);
    exit;
}

$anotar(['tipo' => 'visita', 'protocolo' => $https ? 'https' : 'http', 'ua' => $ua]);
header('Content-Type: text/html; charset=utf-8');
$v = static fn (string $f): string => (string) (@filemtime(__DIR__ . '/' . $f) ?: time());
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<meta name="robots" content="noindex, nofollow">
<title>Prueba de la tablet kiosko</title>
<style>
* { -webkit-box-sizing: border-box; box-sizing: border-box; }
body { margin: 0; padding: 20px 16px 40px 100px; font: 18px/1.4 Roboto, "Droid Sans", sans-serif; background: #f7f7f7; color: #1f2328; }
h1 { font-size: 26px; margin: 0 0 4px; }
.grande { font-size: 30px; font-weight: bold; padding: 14px 16px; border-radius: 10px; margin: 12px 0; }
.ok { background: #dcfce7; color: #14532d; }
.mal { background: #fde8e8; color: #991b1b; }
.info { background: #fff; border: 1px solid #ddd; }
table { width: 100%; border-collapse: collapse; background: #fff; border: 1px solid #ddd; }
td { padding: 8px 10px; border-top: 1px solid #eee; vertical-align: top; }
td.r { width: 110px; font-weight: bold; text-align: center; }
td.r.ok { color: #15803d; background: #f0fdf4; }
td.r.mal { color: #b91c1c; background: #fef2f2; }
td.r.esp { color: #92400e; background: #fffbeb; }
.muted { color: #666; font-size: 15px; }
button { font: bold 20px Roboto, sans-serif; padding: 12px 26px; border-radius: 8px; border: 0; background: #5d1049; color: #fff; margin-top: 16px; }
</style>
</head>
<body>
<h1>Prueba de la tablet kiosko</h1>
<div class="muted">LabSim · OSCE · <?= htmlspecialchars(date('Y-m-d H:i:s')) ?> (hora del servidor)</div>

<div class="grande ok">1. La página cargó: la conexión funciona.</div>
<div class="grande <?= $https ? 'info' : 'ok' ?>">Llegó por <?= $https ? 'HTTPS' : 'HTTP' ?><?= $https ? ' (en la tablet vieja debe ser HTTP)' : '' ?></div>

<div class="grande mal" id="sin-js">2. JavaScript no corrió. Avisa: hay que revisar el log.</div>

<table id="tabla"></table>

<p class="muted" id="estado">Probando…</p>
<button type="button" id="repetir">Repetir pruebas</button>
<p class="muted">Navegador: <?= htmlspecialchars($ua) ?></p>

<script>
(function () {
    'use strict';
    var resultados = [];
    var tabla = document.getElementById('tabla');
    var SERVIDOR_EPOCH = <?= time() ?>;

    function fila(nombre, estado, detalle) {
        // estado: 'ok', 'mal' o 'esp' (informativo: no cuenta como falla)
        resultados.push({ prueba: nombre, estado: estado, detalle: detalle || '' });
        var tr = document.createElement('tr');
        var rotulo = estado === 'ok' ? 'OK' : (estado === 'esp' ? 'INFO' : 'FALLA');
        tr.innerHTML = '<td class="r ' + estado + '">' + rotulo + '</td><td>' + nombre
            + (detalle ? '<div class="muted">' + String(detalle).replace(/</g, '&lt;') + '</div>' : '') + '</td>';
        tabla.appendChild(tr);
    }
    function probar(nombre, fn) {
        try {
            var r = fn();
            if (r === true) fila(nombre, 'ok');
            else fila(nombre, 'mal', r === false ? '' : String(r));
        } catch (e) {
            fila(nombre, 'mal', 'error: ' + e.message);
        }
    }
    function xhr(metodo, url, cuerpo, listo) {
        var x = new XMLHttpRequest(), hecho = false;
        var corte = setTimeout(function () {
            if (hecho) return;
            hecho = true;
            try { x.abort(); } catch (e) {}
            listo(0, '', true);
        }, 12000);
        x.onreadystatechange = function () {
            if (x.readyState !== 4 || hecho) return;
            hecho = true;
            clearTimeout(corte);
            listo(x.status, x.responseText, false);
        };
        x.open(metodo, url + (url.indexOf('?') >= 0 ? '&' : '?') + '_=' + Date.now(), true);
        if (cuerpo !== null) x.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded; charset=UTF-8');
        x.send(cuerpo);
    }

    function correr() {
        resultados = [];
        tabla.innerHTML = '';
        document.getElementById('estado').textContent = 'Probando…';

        // -- Lo que usan las páginas de kiosko/ ---------------------------------
        probar('JSON (parse y stringify)', function () { return JSON.parse(JSON.stringify({ a: [1] })).a[0] === 1; });
        probar('localStorage (guardar y leer)', function () {
            localStorage.setItem('kiosko_prueba', 'x');
            var ok = localStorage.getItem('kiosko_prueba') === 'x';
            localStorage.removeItem('kiosko_prueba');
            return ok;
        });
        probar('addEventListener', function () { return typeof document.addEventListener === 'function'; });
        probar('querySelector / querySelectorAll', function () { return !!document.querySelector('body') && document.querySelectorAll('td').length >= 0; });
        probar('matchesSelector (para reemplazar closest)', function () {
            var b = document.body;
            var f = b.matches || b.webkitMatchesSelector;
            return f ? f.call(b, 'body') : 'no existe';
        });
        probar('Date.now', function () { return typeof Date.now() === 'number'; });
        probar('Array forEach / indexOf', function () { var n = 0; [1, 2].forEach(function (x) { n += x; }); return n === 3 && [5, 6].indexOf(6) === 1; });
        probar('XMLHttpRequest', function () { return typeof XMLHttpRequest !== 'undefined'; });
        probar('Evento input en campos de texto', function () { return 'oninput' in document.createElement('input'); });
        probar('Hora de la tablet', function () {
            var dif = Math.round(Date.now() / 1000 - SERVIDOR_EPOCH);
            return Math.abs(dif) < 120 ? true : 'desfase de ' + dif + ' s con el servidor (el reloj del OSCE lo corrige solo)';
        });
        fila('Pantalla', 'ok', window.innerWidth + '×' + window.innerHeight + ' px, devicePixelRatio ' + (window.devicePixelRatio || 1)
            + ', ' + (window.innerWidth > window.innerHeight ? 'horizontal' : 'vertical'));

        // -- Red (en cadena, para que se lea en orden) ---------------------------
        xhr('GET', 'kiosko.css', null, function (st) {
            fila('Archivo de kiosko/ por XHR (kiosko.css)', st === 200 ? 'ok' : 'mal', 'respuesta ' + st);
            xhr('GET', 'api_reloj.php?r=000000000000000000000000', null, function (st2, txt) {
                var d = null;
                try { d = JSON.parse(txt); } catch (e) {}
                fila('PHP de kiosko/ responde JSON (api_reloj.php)', d && d.error ? 'ok' : 'mal',
                     'respuesta ' + st2 + (d && d.error ? ' · "' + d.error + '" (lo esperado con un token falso)' : ''));
                xhr('GET', '../css/base.css', null, function (st3, t3, corte) {
                    // Fuera de kiosko/ todo sigue yendo a https: en la tablet vieja tiene que fallar.
                    var proto = location.protocol === 'http:';
                    // Informativo: no impide usar la tablet.
                    fila('Archivo fuera de kiosko/ (../css/base.css)', 'esp',
                         proto ? (st3 === 200 ? 'carga por http: el resto del sitio también va por http (no debería, pero no impide nada)'
                                               : 'no carga por http: correcto, solo kiosko/ va por http')
                               : 'respuesta ' + st3 + ' (por https)');
                    var cuerpo = 'resultados=' + encodeURIComponent(JSON.stringify(resultados));
                    xhr('POST', 'prueba.php?registrar=1', cuerpo, function (st4, txt4) {
                        var d4 = null;
                        try { d4 = JSON.parse(txt4); } catch (e) {}
                        fila('POST al servidor (resultados guardados en el log)', d4 && d4.ok ? 'ok' : 'mal',
                             'respuesta ' + st4 + (d4 && d4.ok && !d4.guardado ? ' · el servidor no tiene carpeta data/' : ''));
                        var fallas = 0;
                        for (var i = 0; i < resultados.length; i++) if (resultados[i].estado === 'mal') fallas++;
                        if (!(d4 && d4.ok)) fallas++;
                        document.getElementById('estado').textContent = fallas === 0
                            ? 'Todo bien: esta tablet puede usar las páginas del OSCE.'
                            : fallas + ' prueba(s) con FALLA. Avisa para revisarlo.';
                    });
                });
            });
        });
    }

    document.getElementById('sin-js').className = 'grande ok';
    document.getElementById('sin-js').innerHTML = '2. JavaScript corre.';
    document.getElementById('repetir').addEventListener('click', correr, false);
    correr();
})();
</script>
</body>
</html>
