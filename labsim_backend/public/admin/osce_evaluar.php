<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Osce.php';
require_once __DIR__ . '/../../src/OscePauta.php';
require_once __DIR__ . '/_layout.php';

/**
 * Tablet del docente en una estación de pauta del OSCE (paso 2 de
 * docs/osce_plan.md). Sigue el reloj: muestra solo el código del alumno que
 * está en la estación y pasa al siguiente cuando parte el tiempo nuevo.
 * Cada toque se guarda solo (y queda copia en la tablet si se cae la red);
 * el puntaje lo calcula el servidor con OscePauta::guardar().
 *
 * GET ?estacion=N              la página
 * GET ?estacion=N&cargar=P     JSON: lo guardado del participante P, su nombre y su tiempo
 * POST estacion, participante, accion=empezar, csrf_token   parte el tiempo del alumno
 * POST estacion, participante, datos (JSON), feedback, terminar, csrf_token
 *
 * Tiempo por alumno (2026-11-25): el alumno confirma su nombre en la tablet
 * ("Soy yo, empezar") y ahí parten sus minutos (Osce::iniciarReloj). Si el
 * docente marca un ítem antes, el tiempo parte igual.
 */

$me = Auth::requireAdminSession();
$estId = (int) ($_GET['estacion'] ?? $_POST['estacion'] ?? 0);
$est = Osce::estacion($estId);
$osce = $est !== null ? Osce::obtener((int) $est['osce_id']) : null;
if ($osce === null || !Courses::canAdminister((int) $osce['course_id'], $me) || $est['tipo'] !== 'pauta_docente') {
    http_response_code(404);
    exit('Estación no encontrada.');
}
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
        'puntaje' => $c['entrega']['puntaje'] ?? null,
        'puntaje_max' => $c['entrega']['puntaje_max'] ?? null,
        'critico_fallado' => (int) ($c['entrega']['critico_fallado'] ?? 0) === 1,
        'nombre' => (string) ($porId[$pid]['display_name'] ?? ''),
        'ventana' => Osce::ventanaReal($osce, $pid, $estId),
    ]);
}

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
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
    // Marcar algo con el OSCE en curso cuenta como empezar (si se olvidó el botón).
    // Solo si la estación es suya en este turno: corregir después a otro alumno no le parte un reloj.
    $ventana = $osce['estado'] === 'en_curso' && Osce::motivoNoToca($osce, $est, $porId[$pid]) === null
        ? Osce::iniciarReloj($osce, $pid, $estId) : Osce::ventanaReal($osce, $pid, $estId);
    $datos = json_decode((string) ($_POST['datos'] ?? '{}'), true);
    $r = OscePauta::guardar($estId, $pid, is_array($datos) ? $datos : [], (string) ($_POST['feedback'] ?? ''),
                            !empty($_POST['terminar']), (int) $me['id']);
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
$parts = array_map(static fn ($p) => [
    'numero' => (int) $p['numero'],
    'id' => (int) $p['id'],
    'codigo' => $p['codigo'],
    'vuelta' => (int) $p['vuelta'],
    'circuito' => (int) $p['circuito'],
    'puesto' => (int) $p['puesto'],
    'estado' => $estados[(int) $p['id']] ?? null,
], $participantes);
usort($parts, static fn ($a, $b) => $a['numero'] <=> $b['numero']);

admin_header('Evaluar · ' . $est['titulo'], $me);
?>
<style>
.ev-barra { position: sticky; top: 0; z-index: 5; background: var(--color-surface, #fff); border-bottom: 1px solid var(--color-border, #ddd);
            padding: 0.6rem 0.2rem; display: flex; flex-wrap: wrap; gap: 0.6rem 1.2rem; align-items: center; justify-content: space-between; }
.ev-cod { font: 700 2rem ui-monospace, monospace; letter-spacing: 0.04em; }
.ev-grupo { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.ev-grupo button { min-width: 6.5rem; min-height: 3.2rem; font-size: 1.3rem; font-weight: 800; border-radius: 0.6rem; border: 2px solid var(--color-border, #ccc);
                   background: var(--color-surface, #fff); color: inherit; cursor: pointer; }
.ev-grupo button[aria-pressed="true"] { background: #5d1049; border-color: #5d1049; color: #fff; }
.ev-reloj { font: 700 1.6rem ui-monospace, monospace; }
.ev-reloj small { font: 400 0.85rem system-ui, sans-serif; color: var(--color-text-muted, #666); display: block; }
.ev-item { border: 1px solid var(--color-border, #ddd); border-radius: 0.6rem; padding: 0.8rem; margin: 0.7rem 0; }
.ev-item.marcado { border-color: transparent; background: var(--color-surface-2, #f4f4f6); }
.ev-item.fallo-critico { border-color: #b91c1c; box-shadow: inset 4px 0 0 #b91c1c; }
.ev-texto { font-size: 1.05rem; margin-bottom: 0.6rem; }
.ev-botones { display: flex; gap: 0.5rem; flex-wrap: wrap; }
.ev-botones button { flex: 1 1 8rem; min-height: 3rem; font-size: 1.05rem; border-radius: 0.5rem; border: 2px solid var(--color-border, #ccc);
                     background: var(--color-surface, #fff); color: inherit; cursor: pointer; }
.ev-botones button[aria-pressed="true"][data-v="cumple"] { background: #15803d; border-color: #15803d; color: #fff; }
.ev-botones button[aria-pressed="true"][data-v="parcial"] { background: #b45309; border-color: #b45309; color: #fff; }
.ev-botones button[aria-pressed="true"][data-v="no_cumple"] { background: #b91c1c; border-color: #b91c1c; color: #fff; }
.ev-botones.escala { display: grid; grid-template-columns: repeat(auto-fit, minmax(12rem, 1fr)); }
.ev-botones.escala button { text-align: left; padding: 0.5rem 0.7rem; font-size: 0.95rem; line-height: 1.25; }
.ev-botones.escala button small { display: block; font-size: 0.82rem; opacity: 0.85; margin-top: 0.2rem; }
.ev-botones button[aria-pressed="true"][data-v="n3"] { background: #15803d; border-color: #15803d; color: #fff; }
.ev-botones button[aria-pressed="true"][data-v="n2"] { background: #4d7c0f; border-color: #4d7c0f; color: #fff; }
.ev-botones button[aria-pressed="true"][data-v="n1"] { background: #b45309; border-color: #b45309; color: #fff; }
.ev-botones button[aria-pressed="true"][data-v="n0"] { background: #b91c1c; border-color: #b91c1c; color: #fff; }
.ev-com { margin-top: 0.5rem; }
.ev-com textarea { width: 100%; min-height: 3rem; }
.ev-imp { display: grid; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr)); gap: 0.6rem; }
.ev-imp label { font-size: 0.9rem; display: flex; flex-direction: column; justify-content: space-between; gap: 0.2rem; }
.ev-imp input { font-size: 1.4rem; text-align: center; padding: 0.4rem; }
.ev-imp .fuera input { border-color: #b91c1c; color: #b91c1c; }
.ev-calc { margin-top: 0.6rem; font-size: 1rem; }
.ev-calc .ok { color: #15803d; font-weight: 700; }
.ev-calc .mal { color: #b91c1c; font-weight: 700; }
.ev-pares { font-size: 0.85rem; color: var(--color-text-muted, #666); margin-top: 0.3rem; }
.ev-pie { position: sticky; bottom: 0; background: var(--color-surface, #fff); border-top: 1px solid var(--color-border, #ddd);
          padding: 0.6rem 0.2rem; display: flex; flex-wrap: wrap; gap: 0.6rem; align-items: center; justify-content: space-between; }
.ev-guardado { font-size: 0.9rem; }
.ev-empezar { display: flex; flex-wrap: wrap; gap: 0.8rem 1.4rem; align-items: center; justify-content: center; background: #f5edf3;
              border: 2px solid #5d1049; border-radius: 0.7rem; padding: 1rem; margin: 0.8rem 0; font-size: 1.15rem; }
.ev-empezar strong { font-size: 1.5rem; }
.ev-empezar button { font-size: 1.2rem; padding: 0.7rem 1.6rem; }
.ev-aviso { background: #fef3c7; color: #78350f; padding: 0.5rem 0.8rem; border-radius: 0.4rem; margin: 0.5rem 0; }
</style>

<div class="row row--between row--center" style="margin-bottom:0.5rem;">
    <a href="osce_estacion.php?id=<?= $estId ?>">← Pauta de la estación</a>
    <span class="muted"><?= htmlspecialchars($osce['nombre']) ?> · estación <?= $indice + 1 ?>: <?= htmlspecialchars($est['titulo']) ?></span>
</div>

<?php if (!$items): ?>
    <p class="error">Esta estación no tiene pauta. <a href="osce_estacion.php?id=<?= $estId ?>">Cárgala primero</a>.</p>
<?php else: ?>
<div class="ev-barra">
    <div>
        <div class="muted" id="ev-quien-label">Alumno</div>
        <div class="ev-cod" id="ev-cod">—</div>
        <div class="muted" id="ev-paciente"></div>
    </div>
    <div class="ev-reloj" id="ev-reloj">--:--<small>Cargando reloj…</small></div>
    <div class="row row--gap-sm row--center">
        <div id="ev-grupo" class="ev-grupo" aria-label="Alumnos en la estación ahora"></div>
        <?php $carriles = $cadena ? 1 : (int) $osce['circuitos']; if ($carriles > 1): ?>
        <label>Circuito
            <select id="ev-circuito" style="width:auto;">
                <?php for ($c = 0; $c < $carriles; $c++): ?><option value="<?= $c ?>">Circuito <?= $c + 1 ?></option><?php endfor; ?>
            </select></label>
        <?php endif; ?>
        <label>Otro alumno
            <select id="ev-elegir" style="width:auto;"><option value="">Seguir el reloj</option></select></label>
    </div>
</div>

<div class="ev-empezar" id="ev-empezar" hidden>
    <span>¿Eres <strong id="ev-nombre"></strong>?</span>
    <button type="button" class="btn" id="ev-btn-empezar">Sí, soy yo: empezar</button>
    <span class="muted">Su tiempo parte al confirmar.</span>
</div>
<div id="ev-avisos"></div>
<div id="ev-items"></div>

<div class="ev-item">
    <div class="ev-texto">Comentario general para el alumno</div>
    <textarea id="ev-feedback" rows="3" style="width:100%;" placeholder="Lo verá cuando se publiquen los resultados"></textarea>
</div>

<div class="ev-pie">
    <div>
        <strong id="ev-puntaje">—</strong>
        <span class="ev-guardado muted" id="ev-guardado"></span>
    </div>
    <button type="button" class="btn" id="ev-terminar">Terminar evaluación</button>
</div>

<script src="../js/osce_reloj.js?v=<?= admin_asset_version(__DIR__ . '/../js/osce_reloj.js') ?>"></script>
<script>
(function () {
    'use strict';
    var ITEMS = <?= json_encode($items, JSON_UNESCAPED_UNICODE) ?>;
    var PARTS = <?= json_encode($parts, JSON_UNESCAPED_UNICODE) ?>;
    var INDICE = <?= $indice ?>;
    var EST = <?= $estId ?>;
    var CSRF = <?= json_encode(Auth::csrfToken()) ?>;
    var URL_RELOJ = '../api/osce_reloj.php?r=<?= htmlspecialchars($osce['reloj_token']) ?>';
    var $ = function (id) { return document.getElementById(id); };
    var circuito = 0;
    var actual = null;       // participante en pantalla
    var estado = null;       // {items: {id: {valor, comentario}}, feedback}
    var sucio = false, guardando = false, timer = null;
    var manual = false;      // el docente eligió a mano: no seguir el reloj
    var ventanas = {};       // participante -> {inicio_s, fin_s}: su tiempo, desde que confirmó

    function esc(s) {
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
    function num(x) { return (Math.round(x * 100) / 100).toString().replace('.', ','); }
    function kohm(raw) {
        var s = String(raw == null ? '' : raw).trim().replace(',', '.');
        if (s === '' || isNaN(+s)) return null;
        var v = +s;
        return v >= 0 && v < 1000 ? Math.round(v * 100) / 100 : null;
    }

    // Misma cuenta que OscePauta::impedancias().
    function impedancias(valores, maxK, interK) {
        var v = valores.map(kohm), medidos = v.filter(function (x) { return x !== null; });
        var completo = v.length > 0 && medidos.length === v.length;
        var pares = [];
        for (var i = 0; i < v.length; i++) for (var j = i + 1; j < v.length; j++)
            if (v[i] !== null && v[j] !== null) pares.push([i, j, Math.round(Math.abs(v[i] - v[j]) * 100) / 100]);
        var fuera = [];
        if (maxK != null) v.forEach(function (x, i) { if (x !== null && x >= maxK) fuera.push(i); });
        var max = medidos.length ? Math.max.apply(null, medidos) : null;
        var min = medidos.length ? Math.min.apply(null, medidos) : null;
        var inter = medidos.length ? Math.round((max - min) * 100) / 100 : null;
        return { valores: v, completo: completo, max: max, min: min, inter: inter, pares: pares, fuera: fuera,
                 ok_abs: completo && maxK != null ? fuera.length === 0 : null,
                 ok_inter: completo && interK != null ? inter < interK : null };
    }

    // -- Copia en la tablet (si se cae la red no se pierde nada) ------------
    function claveLocal(pid) { return 'osce_eval_' + EST + '_' + pid; }
    function guardarLocal() {
        if (!actual) return;
        try { localStorage.setItem(claveLocal(actual.id), JSON.stringify({ estado: estado, pendiente: sucio })); } catch (e) {}
    }
    function leerLocal(pid) {
        try { return JSON.parse(localStorage.getItem(claveLocal(pid)) || 'null'); } catch (e) { return null; }
    }

    // -- Pintar ---------------------------------------------------------------
    function pintar() {
        var h = '';
        ITEMS.forEach(function (it, k) {
            var dato = estado.items[it.id] || {};
            var critico = it.critico ? ' <span class="tag tag--danger">crítico</span>' : '';
            h += '<div class="ev-item" data-item="' + it.id + '">'
               + '<div class="ev-texto"><strong>' + (k + 1) + '.</strong> ' + esc(it.texto) + critico
               + ' <span class="muted">(' + num(it.puntaje) + ' pt)</span></div>';
            if (it.tipo === 'impedancias') {
                var vals = (dato.valor && dato.valor.kohm) || dato.valor || [];
                h += '<div class="ev-imp">';
                (it.cfg.electrodos || []).forEach(function (nombre, i) {
                    var v = vals[i] == null ? '' : String(vals[i]).replace('.', ',');
                    h += '<label data-e="' + i + '">' + esc(nombre) + '<input type="text" inputmode="decimal" autocomplete="off" '
                       + 'data-imp="' + i + '" value="' + esc(v) + '" placeholder="kΩ"></label>';
                });
                h += '</div><div class="ev-calc" data-calc></div><div class="ev-pares" data-pares></div>';
            } else {
                h += '<div class="ev-botones' + (it.tipo === 'escala' ? ' escala' : '') + '">';
                it.ops.forEach(function (o) {
                    h += '<button type="button" data-v="' + o.v + '" aria-pressed="' + (dato.valor === o.v) + '"><b>' + esc(o.rotulo) + '</b>'
                       + (o.desc ? '<small>' + esc(o.desc) + '</small>' : '') + '</button>';
                });
                h += '</div>';
            }
            var com = dato.comentario || '';
            h += '<div class="ev-com"><button type="button" class="btn btn--xs btn--ghost" data-com-btn>'
               + (com ? '💬 Comentario' : '💬 Agregar comentario') + '</button>'
               + '<textarea data-com' + (com ? '' : ' hidden') + ' placeholder="Comentario de este ítem">' + esc(com) + '</textarea></div>';
            h += '</div>';
        });
        $('ev-items').innerHTML = h;
        $('ev-feedback').value = estado.feedback || '';
        ITEMS.forEach(function (it) { if (it.tipo === 'impedancias') pintarCalculo(it); });
        marcarItems();
    }

    function pintarCalculo(it) {
        var cont = document.querySelector('[data-item="' + it.id + '"]');
        var vals = Array.prototype.map.call(cont.querySelectorAll('[data-imp]'), function (inp) { return inp.value; });
        var c = impedancias(vals, it.cfg.max_kohm, it.cfg.inter_kohm);
        cont.querySelectorAll('[data-e]').forEach(function (lab) {
            lab.classList.toggle('fuera', c.fuera.indexOf(+lab.dataset.e) >= 0);
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
        var nombres = it.cfg.electrodos || [];
        cont.querySelector('[data-pares]').textContent = c.pares.map(function (p) {
            return (nombres[p[0]] || '').split(' ')[0] + '–' + (nombres[p[1]] || '').split(' ')[0] + ' ' + num(p[2]);
        }).join(' · ');
        return c;
    }

    // Puntaje en pantalla (el que vale lo devuelve el servidor al guardar).
    function marcarItems() {
        var total = 0, max = 0, critico = false, sin = 0;
        ITEMS.forEach(function (it) {
            var cont = document.querySelector('[data-item="' + it.id + '"]');
            var dato = estado.items[it.id] || {}, pts = 0, marcado = false, fallo = false;
            max += it.puntaje;
            if (it.tipo === 'impedancias') {
                var c = impedancias(dato.valor || [], it.cfg.max_kohm, it.cfg.inter_kohm);
                c.valores = c.valores.slice(0, (it.cfg.electrodos || []).length);
                if (c.completo) {
                    marcado = true;
                    var checks = [c.ok_abs, c.ok_inter].filter(function (x) { return x !== null; });
                    var ok = checks.filter(Boolean).length;
                    pts = it.puntaje * (checks.length ? ok / checks.length : 1);
                    fallo = it.critico && checks.length > 0 && ok === 0;
                }
            } else {
                var op = it.ops.filter(function (o) { return o.v === dato.valor; })[0];
                marcado = !!op;
                pts = op ? it.puntaje * op.frac : 0;
                fallo = it.critico && !!op && op.frac <= 0;
            }
            total += pts;
            critico = critico || fallo;
            if (!marcado) sin++;
            cont.classList.toggle('marcado', marcado);
            cont.classList.toggle('fallo-critico', fallo);
        });
        var pct = max > 0 ? Math.round(100 * total / max) : 0;
        $('ev-puntaje').innerHTML = num(total) + ' / ' + num(max) + ' pt (' + pct + ' %)'
            + (critico ? ' · <span style="color:#b91c1c">ítem crítico fallado</span>' : '')
            + (sin ? ' · <span class="muted">' + sin + ' sin marcar</span>' : '');
    }

    // -- Guardar ----------------------------------------------------------
    function aGuardar() {
        sucio = true;
        guardarLocal();
        $('ev-guardado').textContent = 'Guardando…';
        clearTimeout(timer);
        timer = setTimeout(guardar, 700);
    }

    function guardar(terminar) {
        if (!actual || guardando) {
            if (guardando) { clearTimeout(timer); timer = setTimeout(function () { guardar(terminar); }, 500); }
            return Promise.resolve();
        }
        guardando = true;
        sucio = false;
        var pid = actual.id;
        var fd = new FormData();
        fd.append('csrf_token', CSRF);
        fd.append('estacion', EST);
        fd.append('participante', pid);
        fd.append('datos', JSON.stringify(estado.items));
        fd.append('feedback', estado.feedback || '');
        if (terminar) fd.append('terminar', '1');
        return fetch('osce_evaluar.php?estacion=' + EST, { method: 'POST', body: fd, credentials: 'same-origin' })
            .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
            .then(function (res) {
                guardando = false;
                if (!res.ok) throw new Error(res.d.error || 'Error');
                var p = PARTS.filter(function (x) { return x.id === pid; })[0];
                if (p) p.estado = res.d.estado;
                if (res.d.ventana) {
                    ventanas[pid] = res.d.ventana;
                    if (actual && actual.id === pid) $('ev-empezar').hidden = true;
                }
                if (actual && actual.id === pid) {
                    if (!sucio) guardarLocal();
                    $('ev-guardado').textContent = res.d.estado === 'enviada' ? 'Guardado · evaluación terminada ✓' : 'Guardado ✓';
                }
                llenarSelector();
            })
            .catch(function (e) {
                guardando = false;
                sucio = true;
                guardarLocal();
                $('ev-guardado').textContent = 'Sin conexión: quedó guardado en la tablet, reintentando… (' + e.message + ')';
                clearTimeout(timer);
                timer = setTimeout(guardar, 5000);
            });
    }

    // -- Cambiar de alumno ------------------------------------------------
    // Lo guardado trae las impedancias como {kohm, calculo}: en pantalla van como lista.
    function normalizar(items) {
        ITEMS.forEach(function (it) {
            var d = items[it.id];
            if (it.tipo === 'impedancias' && d && d.valor && !Array.isArray(d.valor)) d.valor = d.valor.kohm || [];
        });
        return items;
    }

    var objetivo;            // a quién se está abriendo (evita abrir dos veces por tic del reloj)
    function abrir(p) {
        p = p || null;
        if (objetivo === p) return;
        objetivo = p;
        var antes = sucio ? guardar() : Promise.resolve();
        antes.then(function () {
            if (objetivo !== p) return;
            actual = p;
            if (!p) {
                $('ev-cod').textContent = '—';
                $('ev-paciente').textContent = '';
                $('ev-items').innerHTML = '<p class="muted">No hay alumno en esta estación en este momento.</p>';
                $('ev-puntaje').textContent = '—';
                $('ev-guardado').textContent = '';
                return;
            }
            $('ev-cod').textContent = 'N.º ' + p.numero;
            $('ev-guardado').textContent = 'Cargando…';
            $('ev-empezar').hidden = true;
            fetch('osce_evaluar.php?estacion=' + EST + '&cargar=' + p.id, { credentials: 'same-origin' })
                .then(function (r) { return r.json(); })
                .then(function (d) {
                    if (!actual || actual.id !== p.id) return;
                    ventanas[p.id] = d.ventana || null;
                    $('ev-nombre').textContent = d.nombre || ('N.º ' + p.numero);
                    $('ev-empezar').hidden = !!d.ventana || d.estado === 'enviada' || !d.nombre;
                    var local = leerLocal(p.id);
                    if (local && local.pendiente) {
                        estado = { items: normalizar(local.estado.items || {}), feedback: local.estado.feedback || '' };
                        pintar();
                        aGuardar();
                        return;
                    }
                    estado = { items: normalizar(d.items || {}), feedback: d.feedback || '' };
                    pintar();
                    $('ev-guardado').textContent = d.estado === 'enviada' ? 'Evaluación terminada ✓ (puedes corregir)' : (d.estado ? 'Guardado ✓' : 'Sin evaluar');
                })
                .catch(function () {
                    var local = leerLocal(p.id);
                    estado = local ? local.estado : { items: {}, feedback: '' };
                    pintar();
                    $('ev-guardado').textContent = 'Sin conexión: trabajando con la copia de la tablet.';
                    if (local && local.pendiente) aGuardar();
                });
        });
    }

    function llenarSelector() {
        var sel = $('ev-elegir'), val = sel.value;
        var h = '<option value="">Seguir el reloj</option>';
        PARTS.forEach(function (p) {
            h += '<option value="' + p.id + '">N.º ' + p.numero + ' · ' + esc(p.codigo)
               + (p.estado === 'enviada' ? ' ✓' : p.estado ? ' …' : '') + '</option>';
        });
        sel.innerHTML = h;
        sel.value = val;
    }

    // -- Eventos ----------------------------------------------------------
    $('ev-items').addEventListener('click', function (e) {
        var b = e.target.closest('button');
        if (!b || !estado) return;
        var cont = b.closest('[data-item]'), id = +cont.dataset.item;
        if (b.hasAttribute('data-com-btn')) {
            var ta = cont.querySelector('[data-com]');
            ta.hidden = false;
            ta.focus();
            return;
        }
        if (b.dataset.v) {
            var dato = estado.items[id] || (estado.items[id] = {});
            dato.valor = dato.valor === b.dataset.v ? '' : b.dataset.v;   // tocar de nuevo desmarca
            cont.querySelectorAll('[data-v]').forEach(function (x) { x.setAttribute('aria-pressed', String(x.dataset.v === dato.valor)); });
            marcarItems();
            aGuardar();
        }
    });
    $('ev-items').addEventListener('input', function (e) {
        var cont = e.target.closest('[data-item]');
        if (!cont || !estado) return;
        var id = +cont.dataset.item, dato = estado.items[id] || (estado.items[id] = {});
        if (e.target.hasAttribute('data-com')) {
            dato.comentario = e.target.value;
        } else if (e.target.hasAttribute('data-imp')) {
            dato.valor = Array.prototype.map.call(cont.querySelectorAll('[data-imp]'), function (inp) { return inp.value; });
            var it = ITEMS.filter(function (x) { return x.id === id; })[0];
            pintarCalculo(it);
            marcarItems();
        }
        aGuardar();
    });
    $('ev-feedback').addEventListener('input', function () {
        if (!estado) return;
        estado.feedback = this.value;
        aGuardar();
    });
    $('ev-btn-empezar').addEventListener('click', function () {
        if (!actual) return;
        var pid = actual.id, fd = new FormData();
        fd.append('csrf_token', CSRF);
        fd.append('estacion', EST);
        fd.append('participante', pid);
        fd.append('accion', 'empezar');
        this.disabled = true;
        var btn = this;
        fetch('osce_evaluar.php?estacion=' + EST, { method: 'POST', body: fd, credentials: 'same-origin' })
            .then(function (r) { return r.json().then(function (d) { return { ok: r.ok, d: d }; }); })
            .then(function (res) {
                btn.disabled = false;
                if (!res.ok) throw new Error(res.d.error || 'Error');
                ventanas[pid] = res.d.ventana;
                if (actual && actual.id === pid) $('ev-empezar').hidden = true;
            })
            .catch(function (e) { btn.disabled = false; $('ev-guardado').textContent = 'No se pudo empezar: ' + e.message; });
    });
    $('ev-terminar').addEventListener('click', function () {
        if (!actual) return;
        clearTimeout(timer);
        guardar(true);
    });
    $('ev-elegir').addEventListener('change', function () {
        manual = this.value !== '';
        if (manual) abrir(PARTS.filter(function (p) { return p.id === +this.value; }, this)[0]);
        else seguirReloj(ultimoReloj);
    });
    $('ev-grupo').addEventListener('click', function (e) {
        var b = e.target.closest('button');
        if (!b) return;
        var botones = Array.prototype.slice.call(this.querySelectorAll('button'));
        pos = botones.indexOf(b);
        manual = false;
        $('ev-elegir').value = '';
        botones.forEach(function (x) { x.setAttribute('aria-pressed', String(x === b)); });
        abrir(PARTS.filter(function (p) { return p.id === +b.dataset.id; })[0]);
        grupoPintado = null;
    });
    if ($('ev-circuito')) $('ev-circuito').addEventListener('change', function () { circuito = +this.value; manual = false; $('ev-elegir').value = ''; seguirReloj(ultimoReloj); });
    window.addEventListener('beforeunload', function (e) { if (sucio) { e.preventDefault(); e.returnValue = ''; } });

    // -- Reloj: quién está en esta estación ----------------------------------
    var ultimoReloj = null, ultimaActividad = 0;
    // En cadena (CADENA): el grupo g está en esta estación en el turno g + INDICE;
    // en la camilla c, el de número g*k + c + 1. Su paciente es el de la misma
    // camilla del grupo siguiente (el último limpia al primero).
    var CADENA = <?= $cadena ? 'true' : 'false' ?>, K = <?= $porTurno ?>;
    function porNumero(n) { return PARTS.filter(function (p) { return p.numero === n; })[0] || null; }
    // El docente elige a quién evalúa tocando su número entre los que están
    // ahora en la estación; al cambiar de turno queda en la misma posición.
    var pos = 0, grupoPintado = null;
    function miembros(cfg, g) {
        if (g < 0 || g >= cfg.grupos) return [];
        return PARTS.filter(function (p) { return Math.floor((p.numero - 1) / K) === g; });
    }
    function pintarGrupo(lista, elegido) {
        var clave = lista.map(function (p) { return p.id + (ausente(p) ? 'a' : ''); }).join(',') + '|' + (elegido ? elegido.id : '');
        if (clave === grupoPintado) return;
        grupoPintado = clave;
        $('ev-grupo').innerHTML = lista.length > 1 ? lista.map(function (p) {
            return '<button type="button" data-id="' + p.id + '" aria-pressed="' + (elegido && elegido.id === p.id) + '"'
                + (ausente(p) ? ' disabled title="Ausente"' : '') + '>N.º ' + p.numero + (ausente(p) ? ' · ausente' : '') + '</button>';
        }).join('') : '';
    }
    var AUSENTES = [];   // números marcados ausentes en el panel (llegan con el reloj)
    function ausente(p) { return !!p && AUSENTES.indexOf(p.numero) >= 0; }
    function enEstacion(cfg, vuelta, slot) {
        if (CADENA) {
            var g = slot - INDICE, lista = miembros(cfg, g);
            var p = lista.length ? lista[Math.min(pos, lista.length - 1)] : null;
            // Un ausente no se evalúa: si hay otro en la camilla, va ese.
            if (ausente(p)) p = lista.filter(function (x) { return !ausente(x); })[0] || null;
            // Su paciente (solo en la limpieza): el de la misma posición del grupo
            // siguiente; el último grupo limpia al primero.
            var pac = null;
            if (p && INDICE === 0 && cfg.grupos > 1) {
                var siguientes = miembros(cfg, g + 1 < cfg.grupos ? g + 1 : 0);
                pac = siguientes[Math.min(lista.indexOf(p), siguientes.length - 1)] || null;
            }
            $('ev-paciente').textContent = pac ? 'Limpia a N.º ' + pac.numero : '';
            pintarGrupo(lista, p);
            return p;
        }
        var S = cfg.estaciones, puesto = ((INDICE - slot) % S + S) % S;
        return PARTS.filter(function (p) { return p.vuelta === vuelta && p.circuito === circuito && p.puesto === puesto; })[0] || null;
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
        // En el cambio de estación se queda el que acaba de salir (para terminar de anotar).
        if (reloj.fase === 'estacion') {
            abrir(enEstacion(d.cfg, reloj.vuelta, reloj.slot));
            $('ev-quien-label').textContent = 'Alumno en la estación';
        } else {
            $('ev-quien-label').textContent = 'Recién salió';
        }
    }

    llenarSelector();
    OsceReloj.iniciar(URL_RELOJ, function (d, reloj, t) {
        ultimoReloj = { d: d, reloj: reloj };
        AUSENTES = d.ausentes || [];
        var nombres = { antes: 'Aún no parte', estacion: 'En estación', cambio: 'Cambio', entre_vueltas: 'Pausa entre vueltas', terminado: 'Terminado' };
        var fase = reloj ? reloj.fase : 'antes';
        if (d.estado === 'cerrado' || d.estado === 'publicado') fase = 'terminado';
        // En estación manda el tiempo del alumno en pantalla (parte cuando confirma).
        var v = actual ? ventanas[actual.id] : null, queda = null;
        if (fase === 'estacion' && v && t !== null) queda = v.fin_s - t;
        else if (reloj && fase !== 'estacion' && fase !== 'terminado') queda = reloj.restante_s;
        $('ev-reloj').style.color = fase === 'estacion' && queda !== null && queda <= 60 ? '#b91c1c' : '';
        $('ev-reloj').innerHTML = (queda !== null ? OsceReloj.mmss(queda) : (fase === 'estacion' ? 'sin partir' : '--:--'))
            + '<small>' + nombres[fase] + (d.pausado ? ' · en pausa' : '') + (reloj ? (CADENA ? ' · turno ' + (reloj.slot + 1) : ' · vuelta ' + (reloj.vuelta + 1)) : '') + '</small>';
        seguirReloj(ultimoReloj);
        if (d.estado === 'en_curso' && window.LabSimSesion && Date.now() - ultimaActividad > 60000) {
            ultimaActividad = Date.now();
            window.LabSimSesion.actividad();
        }
    });
})();
</script>
<?php endif; ?>
<?php
admin_footer();
