<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Osce.php';
require_once __DIR__ . '/../../src/OscePauta.php';
require_once __DIR__ . '/../../src/OscePreguntas.php';

/**
 * Tablet del docente en una estación de pauta del OSCE, para las tablets
 * kiosko viejas (Android 4.1, por http). Hace lo mismo que
 * admin/osce_evaluar.php (sigue el reloj, "¿Eres X?" parte el tiempo del
 * alumno, cada toque se guarda solo con copia en la tablet, el puntaje lo
 * calcula OscePauta::guardar), pero:
 *   - sin sesión ni clave: entra con el token de la estación (?k=), el mismo
 *     mecanismo de la tablet de preguntas (OscePreguntas::tokenTablet). Por
 *     http una clave viajaría en claro y la cookie de sesión es Secure;
 *   - ES5 y CSS que entiende WebKit 534. La página moderna no se toca.
 *
 * GET  ?k=TOKEN                  la página
 * GET  ?k=TOKEN&cargar=P         JSON: lo guardado del participante P, su nombre y su tiempo
 * POST k, participante, accion=empezar               parte el tiempo del alumno
 * POST k, participante, datos (JSON), feedback, terminar
 */

header('Cache-Control: no-store');
header('Referrer-Policy: no-referrer');

$k = (string) ($_GET['k'] ?? $_POST['k'] ?? '');
$est = OscePreguntas::estacionPorToken($k);
$osce = $est !== null ? Osce::obtener((int) $est['osce_id']) : null;
$valida = $osce !== null && $est['tipo'] === 'pauta_docente';
$esApi = isset($_GET['cargar']) || $_SERVER['REQUEST_METHOD'] === 'POST';
if (!$valida && $esApi) {
    Response::error('Estación no encontrada.', 404);
}

if ($valida) {
    $estId = (int) $est['id'];
    $osceId = (int) $osce['id'];
    $participantes = Osce::participantes($osceId);
    $porId = [];
    foreach ($participantes as $p) {
        $porId[(int) $p['id']] = $p;
    }

    if (isset($_GET['cargar'])) {
        $pid = (int) $_GET['cargar'];
        if (!isset($porId[$pid])) {
            Response::error('Alumno no encontrado.', 404);
        }
        $c = OscePauta::cargar($estId, $pid);
        Response::json([
            'items' => (object) $c['items'],
            'feedback' => $c['entrega']['feedback'] ?? '',
            'estado' => $c['entrega']['estado'] ?? null,
            'nombre' => (string) ($porId[$pid]['display_name'] ?? ''),
            'ventana' => Osce::ventanaReal($osce, $pid, $estId),
        ]);
    }

    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $pid = (int) ($_POST['participante'] ?? 0);
        if (!isset($porId[$pid])) {
            Response::error('Alumno no encontrado.', 404);
        }
        if ($osce['estado'] === 'publicado') {
            Response::error('Los resultados ya se publicaron: la evaluación queda fija.', 409);
        }
        if (($_POST['accion'] ?? '') === 'empezar') {
            $motivo = Osce::motivoNoToca($osce, $est, $porId[$pid]);
            if ($motivo !== null) {
                Response::error($motivo, 409);
            }
            Response::json(['ok' => true, 'ventana' => Osce::iniciarReloj($osce, $pid, $estId)]);
        }
        // Igual que osce_evaluar.php: marcar con el OSCE en curso, si es su turno, parte el tiempo.
        $ventana = $osce['estado'] === 'en_curso' && Osce::motivoNoToca($osce, $est, $porId[$pid]) === null
            ? Osce::iniciarReloj($osce, $pid, $estId) : Osce::ventanaReal($osce, $pid, $estId);
        $datos = json_decode((string) ($_POST['datos'] ?? '{}'), true);
        $r = OscePauta::guardar($estId, $pid, is_array($datos) ? $datos : [], (string) ($_POST['feedback'] ?? ''),
                                !empty($_POST['terminar']), null);
        Response::json(['ok' => true, 'ventana' => $ventana] + $r);
    }

    $estaciones = Osce::estaciones($osceId);
    $indice = (int) array_search($estId, array_map('intval', array_column($estaciones, 'id')), true);
    $items = array_map(static fn ($it) => [
        'id' => (int) $it['id'],
        'texto' => $it['texto'],
        'puntaje' => (float) $it['puntaje'],
        'critico' => (int) $it['critico'] === 1,
        'tipo' => $it['tipo'],
        'cfg' => $it['cfg'],
        'ops' => $it['tipo'] === 'impedancias' ? [] : OscePauta::opciones($it),
    ], OscePauta::items($estId));
    $estados = OscePauta::estadosEstacion($estId);
    $cadena = ($osce['rotacion'] ?? 'vueltas') === 'cadena';
    $porTurno = max(1, (int) ($osce['por_turno'] ?? 1));
    // Sin el código de la tarjeta: por http solo viaja el número.
    $parts = array_map(static fn ($p) => [
        'numero' => (int) $p['numero'],
        'id' => (int) $p['id'],
        'vuelta' => (int) $p['vuelta'],
        'circuito' => (int) $p['circuito'],
        'puesto' => (int) $p['puesto'],
        'estado' => $estados[(int) $p['id']] ?? null,
    ], $participantes);
    usort($parts, static fn ($a, $b) => $a['numero'] <=> $b['numero']);
    $carriles = $cadena ? 1 : (int) $osce['circuitos'];
}

header('Content-Type: text/html; charset=utf-8');
$v = static fn (string $f): string => (string) (@filemtime(__DIR__ . '/' . $f) ?: time());
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, maximum-scale=1, user-scalable=no">
<meta name="robots" content="noindex, nofollow">
<title>OSCE · <?= htmlspecialchars($valida ? $est['titulo'] : 'Estación') ?></title>
<link rel="stylesheet" href="kiosko.css?v=<?= $v('kiosko.css') ?>">
<style>
body { padding-top: 96px; }
.k-barra, .k-barra table { height: 84px; }
.ev-cod { font: bold 30px "Droid Sans Mono", monospace; }
.k-barra .k-cuenta { font-size: 30px; }
.k-barra .k-der { width: 1%; }
.ev-grupo { white-space: nowrap; }
.ev-grupo button { min-width: 84px; min-height: 48px; font-size: 19px; font-weight: bold; border-radius: 8px; border: 2px solid #ccc;
                   background: #fff; margin-left: 6px; }
.ev-grupo button.si { background: #5d1049; border-color: #5d1049; color: #fff; }
.ev-grupo button[disabled] { opacity: 0.45; }
.ev-sel { font-size: 15px; padding: 4px; margin-top: 4px; width: 180px; }
.ev-item.marcado { background: #f1f1f4; border-color: #f1f1f4; }
.ev-item.fallo { border-color: #b91c1c; border-left-width: 6px; }
.ev-texto { margin-bottom: 10px; }
.tag-critico { display: inline-block; font-size: 13px; padding: 1px 7px; border-radius: 10px; background: #fde8e8; color: #991b1b; font-weight: bold; }
.ev-botones { font-size: 0; }
.ev-botones button { display: inline-block; vertical-align: top; width: 32%; margin: 0 1% 8px 0; min-height: 54px; font-size: 18px;
                     border-radius: 8px; border: 2px solid #ccc; background: #fff; padding: 6px 8px; }
.ev-botones.escala button { width: 49%; text-align: left; font-size: 16px; line-height: 1.25; }
.ev-botones button small { display: block; font-size: 14px; margin-top: 3px; color: #555; }
.ev-botones button.si small { color: #fff; }
.ev-botones button.si { color: #fff; }
.ev-botones button.si.v-cumple, .ev-botones button.si.v-n3 { background: #15803d; border-color: #15803d; }
.ev-botones button.si.v-n2 { background: #4d7c0f; border-color: #4d7c0f; }
.ev-botones button.si.v-parcial, .ev-botones button.si.v-n1 { background: #b45309; border-color: #b45309; }
.ev-botones button.si.v-no_cumple, .ev-botones button.si.v-n0 { background: #b91c1c; border-color: #b91c1c; }
.ev-com-btn { font-size: 15px; padding: 6px 12px; border-radius: 6px; border: 1px solid #ccc; background: #fff; }
.ev-com textarea, #ev-feedback { width: 100%; height: 70px; margin-top: 6px; font-size: 17px; padding: 6px; border: 1px solid #bbb; border-radius: 6px; }
.ev-imp label { display: inline-block; vertical-align: top; width: 180px; margin: 0 10px 10px 0; font-size: 15px; }
.ev-imp input { display: block; width: 100%; font-size: 24px; text-align: center; padding: 6px; border: 2px solid #bbb; border-radius: 6px; margin-top: 3px; }
.ev-imp label.fuera input { border-color: #b91c1c; color: #b91c1c; }
.ev-calc .ok { color: #15803d; font-weight: bold; }
.ev-calc .mal { color: #b91c1c; font-weight: bold; }
.ev-pares { font-size: 14px; color: #666; margin-top: 4px; }
.ev-empezar { text-align: center; background: #f5edf3; border: 2px solid #5d1049; border-radius: 10px; padding: 14px; margin: 6px 0 12px; font-size: 20px; }
.ev-empezar strong { font-size: 26px; }
</style>
</head>
<body>
<?php if (!$valida): ?>
<div class="k-tarjeta"><h1>Estación no encontrada</h1><p>El enlace de esta tablet no es válido. Cópialo de nuevo desde la estación en LabSim.</p></div>
</body></html>
<?php exit; endif; ?>
<?php if (!$items): ?>
<div class="k-tarjeta"><h1><?= htmlspecialchars($est['titulo']) ?></h1><p>Esta estación no tiene pauta. Cárgala primero en LabSim.</p></div>
</body></html>
<?php exit; endif; ?>

<div class="k-barra"><table><tr>
    <td class="k-izq">
        <div class="k-sub" id="ev-quien-label">Alumno</div>
        <div class="ev-cod" id="ev-cod">—</div>
        <div class="k-sub" id="ev-paciente"></div>
    </td>
    <td><div class="k-cuenta" id="ev-reloj">--:--<small>Cargando reloj…</small></div></td>
    <td class="k-der">
        <div class="ev-grupo" id="ev-grupo"></div>
        <?php if ($carriles > 1): ?>
        <select id="ev-circuito" class="ev-sel">
            <?php for ($c = 0; $c < $carriles; $c++): ?><option value="<?= $c ?>">Circuito <?= $c + 1 ?></option><?php endfor; ?>
        </select>
        <?php endif; ?>
        <select id="ev-elegir" class="ev-sel"><option value="">Seguir el reloj</option></select>
    </td>
</tr></table></div>

<div class="ev-empezar" id="ev-empezar" style="display:none">
    ¿Eres <strong id="ev-nombre"></strong>?<span class="k-espacio"></span>
    <button type="button" class="k-btn" id="ev-btn-empezar">Sí, soy yo: empezar</button>
    <div class="muted" style="font-size:15px;margin-top:6px">Su tiempo parte al confirmar.</div>
</div>
<div id="ev-items"></div>

<div class="k-tarjeta">
    <div class="ev-texto">Comentario general para el alumno</div>
    <textarea id="ev-feedback" placeholder="Lo verá cuando se publiquen los resultados"></textarea>
</div>

<div class="k-pie"><table><tr>
    <td style="text-align:left"><strong id="ev-puntaje">—</strong><br><span class="muted" id="ev-guardado" style="font-size:15px"></span></td>
    <td style="text-align:right"><button type="button" class="k-btn" id="ev-terminar">Terminar evaluación</button></td>
</tr></table></div>

<script src="kiosko.js?v=<?= $v('kiosko.js') ?>"></script>
<script>
(function () {
    'use strict';
    var ITEMS = <?= json_encode($items, JSON_UNESCAPED_UNICODE) ?>;
    var PARTS = <?= json_encode($parts, JSON_UNESCAPED_UNICODE) ?>;
    var INDICE = <?= $indice ?>;
    var K = <?= json_encode($k) ?>;
    var URL_RELOJ = 'api_reloj.php?r=<?= htmlspecialchars($osce['reloj_token']) ?>';
    var CADENA = <?= $cadena ? 'true' : 'false' ?>, KT = <?= $porTurno ?>;
    var $ = Kiosko.$, esc = Kiosko.esc, mostrar = Kiosko.mostrar;
    var circuito = 0;
    var actual = null;       // participante en pantalla
    var estado = null;       // {items: {id: {valor, comentario}}, feedback}
    var sucio = false, guardando = false, timer = null;
    var manual = false;      // el docente eligió a mano: no seguir el reloj
    var ventanas = {};       // participante -> {inicio_s, fin_s}

    function cada(lista, fn) { for (var i = 0; i < lista.length; i++) fn(lista[i], i); }
    function primero(lista, fn) { for (var i = 0; i < lista.length; i++) if (fn(lista[i])) return lista[i]; return null; }
    function num(x) { return (Math.round(x * 100) / 100).toString().replace('.', ','); }
    function kohm(raw) {
        var s = String(raw == null ? '' : raw).replace(/^\s+|\s+$/g, '').replace(',', '.');
        if (s === '' || isNaN(+s)) return null;
        var v = +s;
        return v >= 0 && v < 1000 ? Math.round(v * 100) / 100 : null;
    }
    function porId(id) { return primero(PARTS, function (p) { return p.id === id; }); }
    function itemPorId(id) { return primero(ITEMS, function (x) { return x.id === id; }); }

    // Misma cuenta que OscePauta::impedancias().
    function impedancias(valores, maxK, interK) {
        var v = [], medidos = [], i, j;
        for (i = 0; i < valores.length; i++) { v.push(kohm(valores[i])); if (v[i] !== null) medidos.push(v[i]); }
        var completo = v.length > 0 && medidos.length === v.length;
        var pares = [];
        for (i = 0; i < v.length; i++) for (j = i + 1; j < v.length; j++)
            if (v[i] !== null && v[j] !== null) pares.push([i, j, Math.round(Math.abs(v[i] - v[j]) * 100) / 100]);
        var fuera = [];
        if (maxK != null) for (i = 0; i < v.length; i++) if (v[i] !== null && v[i] >= maxK) fuera.push(i);
        var max = medidos.length ? Math.max.apply(null, medidos) : null;
        var min = medidos.length ? Math.min.apply(null, medidos) : null;
        var inter = medidos.length ? Math.round((max - min) * 100) / 100 : null;
        return { valores: v, completo: completo, max: max, min: min, inter: inter, pares: pares, fuera: fuera,
                 ok_abs: completo && maxK != null ? fuera.length === 0 : null,
                 ok_inter: completo && interK != null ? inter < interK : null };
    }

    // -- Copia en la tablet (si se cae la red no se pierde nada) ------------
    function claveLocal(pid) { return 'osce_kev_' + K + '_' + pid; }
    function guardarLocal() {
        if (!actual) return;
        try { localStorage.setItem(claveLocal(actual.id), JSON.stringify({ estado: estado, pendiente: sucio })); } catch (e) {}
    }
    function leerLocal(pid) {
        try { return JSON.parse(localStorage.getItem(claveLocal(pid)) || 'null'); } catch (e) { return null; }
    }

    // -- Pintar ---------------------------------------------------------------
    function contDe(id) { return document.getElementById('it-' + id); }
    function pintar() {
        var h = '';
        cada(ITEMS, function (it, k) {
            var dato = estado.items[it.id] || {};
            h += '<div class="k-tarjeta ev-item" id="it-' + it.id + '" data-item="' + it.id + '">'
               + '<div class="ev-texto"><strong>' + (k + 1) + '.</strong> ' + esc(it.texto)
               + (it.critico ? ' <span class="tag-critico">crítico</span>' : '')
               + ' <span class="muted">(' + num(it.puntaje) + ' pt)</span></div>';
            if (it.tipo === 'impedancias') {
                var vals = (dato.valor && dato.valor.kohm) || dato.valor || [];
                h += '<div class="ev-imp">';
                cada(it.cfg.electrodos || [], function (nombre, i) {
                    var val = vals[i] == null ? '' : String(vals[i]).replace('.', ',');
                    h += '<label data-e="' + i + '">' + esc(nombre) + '<input type="text" autocomplete="off" '
                       + 'data-imp="' + i + '" value="' + esc(val) + '" placeholder="kΩ"></label>';
                });
                h += '</div><div class="ev-calc" data-calc></div><div class="ev-pares" data-pares></div>';
            } else {
                h += '<div class="ev-botones' + (it.tipo === 'escala' ? ' escala' : '') + '">';
                cada(it.ops, function (o) {
                    h += '<button type="button" data-v="' + esc(o.v) + '" class="v-' + esc(o.v) + (dato.valor === o.v ? ' si' : '') + '"><b>'
                       + esc(o.rotulo) + '</b>' + (o.desc ? '<small>' + esc(o.desc) + '</small>' : '') + '</button>';
                });
                h += '</div>';
            }
            var com = dato.comentario || '';
            h += '<div class="ev-com"><button type="button" class="ev-com-btn" data-com-btn>'
               + (com ? 'Comentario' : '+ Agregar comentario') + '</button>'
               + '<textarea data-com placeholder="Comentario de este ítem"' + (com ? '' : ' style="display:none"') + '>' + esc(com) + '</textarea></div>';
            h += '</div>';
        });
        $('ev-items').innerHTML = h;
        $('ev-feedback').value = estado.feedback || '';
        cada(ITEMS, function (it) { if (it.tipo === 'impedancias') pintarCalculo(it); });
        marcarItems();
    }

    function valoresImp(cont) {
        var out = [], ins = cont.getElementsByTagName('input');
        for (var i = 0; i < ins.length; i++) if (ins[i].hasAttribute('data-imp')) out.push(ins[i].value);
        return out;
    }
    function pintarCalculo(it) {
        var cont = contDe(it.id);
        var c = impedancias(valoresImp(cont), it.cfg.max_kohm, it.cfg.inter_kohm);
        cada(cont.getElementsByTagName('label'), function (lab) {
            if (!lab.hasAttribute('data-e')) return;
            lab.className = c.fuera.indexOf(+lab.getAttribute('data-e')) >= 0 ? 'fuera' : '';
        });
        var txt = '';
        if (c.max !== null) {
            txt = 'Máx ' + num(c.max) + ' · mín ' + num(c.min) + ' · <strong>interelectrodo ' + num(c.inter) + ' kΩ</strong>';
            if (c.completo) {
                if (c.ok_abs !== null) txt += ' — por electrodo &lt; ' + num(it.cfg.max_kohm) + ': <span class="' + (c.ok_abs ? 'ok">cumple' : 'mal">no cumple') + '</span>';
                if (c.ok_inter !== null) txt += ' · interelectrodo &lt; ' + num(it.cfg.inter_kohm) + ': <span class="' + (c.ok_inter ? 'ok">cumple' : 'mal">no cumple') + '</span>';
                else txt += ' · interelectrodo sin límite (el protocolo pide valores similares)';
            } else {
                txt += ' <span class="muted">(faltan electrodos)</span>';
            }
        }
        cont.querySelector('[data-calc]').innerHTML = txt;
        var nombres = it.cfg.electrodos || [], pares = [];
        cada(c.pares, function (p) {
            pares.push((nombres[p[0]] || '').split(' ')[0] + '–' + (nombres[p[1]] || '').split(' ')[0] + ' ' + num(p[2]));
        });
        cont.querySelector('[data-pares]').textContent = pares.join(' · ');
    }

    // Puntaje en pantalla (el que vale lo devuelve el servidor al guardar).
    function marcarItems() {
        var total = 0, max = 0, critico = false, sin = 0;
        cada(ITEMS, function (it) {
            var cont = contDe(it.id);
            var dato = estado.items[it.id] || {}, pts = 0, marcado = false, fallo = false;
            max += it.puntaje;
            if (it.tipo === 'impedancias') {
                var c = impedancias(dato.valor || [], it.cfg.max_kohm, it.cfg.inter_kohm);
                if (c.completo) {
                    marcado = true;
                    var checks = [], ok = 0;
                    if (c.ok_abs !== null) checks.push(c.ok_abs);
                    if (c.ok_inter !== null) checks.push(c.ok_inter);
                    cada(checks, function (x) { if (x) ok++; });
                    pts = it.puntaje * (checks.length ? ok / checks.length : 1);
                    fallo = it.critico && checks.length > 0 && ok === 0;
                }
            } else {
                var op = primero(it.ops, function (o) { return o.v === dato.valor; });
                marcado = !!op;
                pts = op ? it.puntaje * op.frac : 0;
                fallo = it.critico && !!op && op.frac <= 0;
            }
            total += pts;
            critico = critico || fallo;
            if (!marcado) sin++;
            cont.className = 'k-tarjeta ev-item' + (marcado ? ' marcado' : '') + (fallo ? ' fallo' : '');
        });
        var pct = max > 0 ? Math.round(100 * total / max) : 0;
        $('ev-puntaje').innerHTML = num(total) + ' / ' + num(max) + ' pt (' + pct + ' %)'
            + (critico ? ' · <span class="k-rojo">ítem crítico fallado</span>' : '')
            + (sin ? ' · <span class="muted">' + sin + ' sin marcar</span>' : '');
    }

    // -- Guardar ----------------------------------------------------------
    function aGuardar() {
        sucio = true;
        guardarLocal();
        $('ev-guardado').textContent = 'Guardando…';
        clearTimeout(timer);
        timer = setTimeout(function () { guardar(false); }, 700);
    }

    // listo() se llama al terminar (bien o mal), para encadenar el cambio de alumno.
    function guardar(terminar, listo) {
        if (!actual || guardando) {
            if (guardando) { clearTimeout(timer); timer = setTimeout(function () { guardar(terminar, listo); }, 500); }
            else if (listo) listo();
            return;
        }
        guardando = true;
        sucio = false;
        var pid = actual.id;
        Kiosko.post('pauta.php', { k: K, participante: pid, datos: JSON.stringify(estado.items), feedback: estado.feedback || '',
                                   terminar: terminar ? '1' : '' }, function (d) {
            guardando = false;
            var p = porId(pid);
            if (p) p.estado = d.estado;
            if (d.ventana) {
                ventanas[pid] = d.ventana;
                if (actual && actual.id === pid) mostrar('ev-empezar', false);
            }
            if (actual && actual.id === pid) {
                if (!sucio) guardarLocal();
                $('ev-guardado').textContent = d.estado === 'enviada' ? 'Guardado · evaluación terminada' : 'Guardado';
            }
            llenarSelector();
            if (listo) listo();
        }, function (msg, status) {
            guardando = false;
            sucio = true;
            guardarLocal();
            if (status === 409) {          // resultados publicados: no hay reintento que valga
                $('ev-guardado').textContent = msg;
                if (listo) listo();
                return;
            }
            $('ev-guardado').textContent = 'Sin conexión: quedó guardado en la tablet, reintentando… (' + msg + ')';
            clearTimeout(timer);
            timer = setTimeout(function () { guardar(terminar); }, 5000);
            if (listo) listo();
        });
    }

    // -- Cambiar de alumno ------------------------------------------------
    function normalizar(items) {
        cada(ITEMS, function (it) {
            var d = items[it.id];
            if (it.tipo === 'impedancias' && d && d.valor && !(d.valor instanceof Array)) d.valor = d.valor.kohm || [];
        });
        return items;
    }

    var objetivo;            // a quién se está abriendo (evita abrir dos veces por tic del reloj)
    function abrir(p) {
        p = p || null;
        if (objetivo === p) return;
        objetivo = p;
        var seguir = function () {
            if (objetivo !== p) return;
            actual = p;
            if (!p) {
                $('ev-cod').textContent = '—';
                $('ev-paciente').textContent = '';
                $('ev-items').innerHTML = '<p class="muted">No hay alumno en esta estación en este momento.</p>';
                $('ev-puntaje').textContent = '—';
                $('ev-guardado').textContent = '';
                mostrar('ev-empezar', false);
                return;
            }
            $('ev-cod').textContent = 'N.º ' + p.numero;
            $('ev-guardado').textContent = 'Cargando…';
            mostrar('ev-empezar', false);
            Kiosko.get('pauta.php?k=' + encodeURIComponent(K) + '&cargar=' + p.id, function (d) {
                if (!actual || actual.id !== p.id) return;
                ventanas[p.id] = d.ventana || null;
                $('ev-nombre').textContent = d.nombre || ('N.º ' + p.numero);
                mostrar('ev-empezar', !d.ventana && d.estado !== 'enviada' && !!d.nombre);
                var local = leerLocal(p.id);
                if (local && local.pendiente) {
                    estado = { items: normalizar(local.estado.items || {}), feedback: local.estado.feedback || '' };
                    pintar();
                    aGuardar();
                    return;
                }
                estado = { items: normalizar(d.items || {}), feedback: d.feedback || '' };
                pintar();
                $('ev-guardado').textContent = d.estado === 'enviada' ? 'Evaluación terminada (puedes corregir)' : (d.estado ? 'Guardado' : 'Sin evaluar');
            }, function () {
                if (!actual || actual.id !== p.id) return;
                var local = leerLocal(p.id);
                estado = local ? local.estado : { items: {}, feedback: '' };
                pintar();
                $('ev-guardado').textContent = 'Sin conexión: trabajando con la copia de la tablet.';
                if (local && local.pendiente) aGuardar();
            });
        };
        if (sucio) guardar(false, seguir); else seguir();
    }

    function llenarSelector() {
        var sel = $('ev-elegir'), val = sel.value;
        var h = '<option value="">Seguir el reloj</option>';
        cada(PARTS, function (p) {
            h += '<option value="' + p.id + '">N.º ' + p.numero
               + (p.estado === 'enviada' ? ' (terminada)' : p.estado ? ' (en curso)' : '') + '</option>';
        });
        sel.innerHTML = h;
        sel.value = val;
    }

    // -- Eventos ----------------------------------------------------------
    $('ev-items').addEventListener('click', function (e) {
        var b = Kiosko.cerca(e.target, 'button', this);
        if (!b || !estado) return;
        var cont = Kiosko.cerca(b, '[data-item]', this), id = +cont.getAttribute('data-item');
        if (b.hasAttribute('data-com-btn')) {
            var ta = cont.querySelector('[data-com]');
            ta.style.display = '';
            ta.focus();
            return;
        }
        var v = b.getAttribute('data-v');
        if (v) {
            var dato = estado.items[id] || (estado.items[id] = {});
            dato.valor = dato.valor === v ? '' : v;   // tocar de nuevo desmarca
            cada(cont.querySelectorAll('[data-v]'), function (x) {
                var xv = x.getAttribute('data-v');
                x.className = 'v-' + xv + (xv === dato.valor ? ' si' : '');
            });
            marcarItems();
            aGuardar();
        }
    }, false);
    $('ev-items').addEventListener('input', function (e) {
        var cont = Kiosko.cerca(e.target, '[data-item]', this);
        if (!cont || !estado) return;
        var id = +cont.getAttribute('data-item'), dato = estado.items[id] || (estado.items[id] = {});
        if (e.target.hasAttribute('data-com')) {
            dato.comentario = e.target.value;
        } else if (e.target.hasAttribute('data-imp')) {
            dato.valor = valoresImp(cont);
            pintarCalculo(itemPorId(id));
            marcarItems();
        }
        aGuardar();
    }, false);
    $('ev-feedback').addEventListener('input', function () {
        if (!estado) return;
        estado.feedback = this.value;
        aGuardar();
    }, false);
    $('ev-btn-empezar').addEventListener('click', function () {
        if (!actual) return;
        var pid = actual.id, btn = this;
        btn.disabled = true;
        Kiosko.post('pauta.php', { k: K, participante: pid, accion: 'empezar' }, function (d) {
            btn.disabled = false;
            ventanas[pid] = d.ventana;
            if (actual && actual.id === pid) mostrar('ev-empezar', false);
        }, function (msg) { btn.disabled = false; $('ev-guardado').textContent = 'No se pudo empezar: ' + msg; });
    }, false);
    $('ev-terminar').addEventListener('click', function () {
        if (!actual) return;
        clearTimeout(timer);
        guardar(true);
    }, false);
    $('ev-elegir').addEventListener('change', function () {
        manual = this.value !== '';
        if (manual) abrir(porId(+this.value));
        else seguirReloj(ultimoReloj);
    }, false);
    $('ev-grupo').addEventListener('click', function (e) {
        var b = Kiosko.cerca(e.target, 'button', this);
        if (!b || b.disabled) return;
        var botones = this.getElementsByTagName('button');
        for (var i = 0; i < botones.length; i++) {
            if (botones[i] === b) pos = i;
            botones[i].className = botones[i] === b ? 'si' : '';
        }
        manual = false;
        $('ev-elegir').value = '';
        abrir(porId(+b.getAttribute('data-id')));
        grupoPintado = null;
    }, false);
    if ($('ev-circuito')) $('ev-circuito').addEventListener('change', function () {
        circuito = +this.value; manual = false; $('ev-elegir').value = ''; seguirReloj(ultimoReloj);
    }, false);

    // -- Reloj: quién está en esta estación ----------------------------------
    // En cadena: el grupo g está en esta estación en el turno g + INDICE; su
    // paciente (solo en la limpieza) es el de la misma posición del grupo
    // siguiente; el último limpia al primero.
    var ultimoReloj = null;
    var pos = 0, grupoPintado = null;
    var AUSENTES = [];
    function ausente(p) { return !!p && AUSENTES.indexOf(p.numero) >= 0; }
    function miembros(cfg, g) {
        var out = [];
        if (g < 0 || g >= cfg.grupos) return out;
        cada(PARTS, function (p) { if (Math.floor((p.numero - 1) / KT) === g) out.push(p); });
        return out;
    }
    function pintarGrupo(lista, elegido) {
        var clave = '';
        cada(lista, function (p) { clave += p.id + (ausente(p) ? 'a' : '') + ','; });
        clave += '|' + (elegido ? elegido.id : '');
        if (clave === grupoPintado) return;
        grupoPintado = clave;
        var h = '';
        if (lista.length > 1) cada(lista, function (p) {
            h += '<button type="button" data-id="' + p.id + '" class="' + (elegido && elegido.id === p.id ? 'si' : '') + '"'
               + (ausente(p) ? ' disabled' : '') + '>N.º ' + p.numero + (ausente(p) ? ' · ausente' : '') + '</button>';
        });
        $('ev-grupo').innerHTML = h;
    }
    function enEstacion(cfg, vuelta, slot) {
        if (CADENA) {
            var g = slot - INDICE, lista = miembros(cfg, g);
            var p = lista.length ? lista[Math.min(pos, lista.length - 1)] : null;
            if (ausente(p)) p = primero(lista, function (x) { return !ausente(x); });
            var pac = null;
            if (p && INDICE === 0 && cfg.grupos > 1) {
                var sig = miembros(cfg, g + 1 < cfg.grupos ? g + 1 : 0);
                pac = sig[Math.min(lista.indexOf(p), sig.length - 1)] || null;
            }
            $('ev-paciente').textContent = pac ? 'Limpia a N.º ' + pac.numero : '';
            pintarGrupo(lista, p);
            return p;
        }
        var S = cfg.estaciones, puesto = ((INDICE - slot) % S + S) % S;
        return primero(PARTS, function (p) { return p.vuelta === vuelta && p.circuito === circuito && p.puesto === puesto; });
    }
    function seguirReloj(info) {
        if (manual || !info) return;
        var d = info.d, reloj = info.reloj;
        if (!reloj || reloj.fase === 'antes') {
            abrir(enEstacion(d.cfg, 0, 0));
            $('ev-quien-label').textContent = 'Primer alumno';
            return;
        }
        if (reloj.fase === 'terminado') { $('ev-quien-label').textContent = 'Último alumno'; return; }
        if (reloj.fase === 'estacion') {
            abrir(enEstacion(d.cfg, reloj.vuelta, reloj.slot));
            $('ev-quien-label').textContent = 'Alumno en la estación';
        } else {
            $('ev-quien-label').textContent = 'Recién salió';     // en el cambio se queda para terminar de anotar
        }
    }

    llenarSelector();
    var NOMBRES = { antes: 'Aún no parte', estacion: 'En estación', cambio: 'Cambio', entre_vueltas: 'Pausa entre vueltas', terminado: 'Terminado' };
    Kiosko.reloj(URL_RELOJ, function (d, reloj, t) {
        ultimoReloj = { d: d, reloj: reloj };
        AUSENTES = d.ausentes || [];
        var fase = reloj ? reloj.fase : 'antes';
        if (d.estado === 'cerrado' || d.estado === 'publicado') fase = 'terminado';
        var v = actual ? ventanas[actual.id] : null, queda = null;
        if (fase === 'estacion' && v && t !== null) queda = v.fin_s - t;
        else if (reloj && fase !== 'estacion' && fase !== 'terminado') queda = reloj.restante_s;
        var el = $('ev-reloj');
        el.className = 'k-cuenta' + (fase === 'estacion' && queda !== null && queda <= 60 ? ' k-rojo' : '');
        el.innerHTML = (queda !== null ? Kiosko.mmss(queda) : (fase === 'estacion' ? 'sin partir' : '--:--'))
            + '<small>' + NOMBRES[fase] + (d.pausado ? ' · en pausa' : '')
            + (reloj ? (CADENA ? ' · turno ' + (reloj.slot + 1) : ' · vuelta ' + (reloj.vuelta + 1)) : '') + '</small>';
        seguirReloj(ultimoReloj);
    });
})();
</script>
</body>
</html>
