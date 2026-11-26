<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Osce.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Panel de control del docente que coordina el OSCE: fase, cuenta
 * regresiva, quién debería estar en cada estación y, en vivo, si ya entró o
 * entregó y cuánto le queda (las tablets y los PCs avisan los tiempos a cada
 * alumno; acá se ve el conjunto). Por turnos: cuando todas las estaciones
 * cerraron parte el cambio y este equipo dice "cambio" en voz alta. Si una
 * estación no cierra, "Forzar cambio"; un alumno que no vino se marca
 * ausente y sus estaciones no lo esperan. Los controles (iniciar, pausar, correr el reloj,
 * cerrar) mueven el reloj de todas las pantallas a la vez: el estado vive en
 * la base (Osce::iniciar/pausar/...) y cada pantalla lo lee de
 * api/osce_reloj.php.
 */

$me = Auth::requireAdminSession();
$id = (int) ($_GET['id'] ?? $_POST['id'] ?? 0);
$osce = Osce::obtener($id);
if ($osce === null || !Courses::canAdminister((int) $osce['course_id'], $me)) {
    http_response_code(404);
    exit('OSCE no encontrado.');
}

if (isset($_GET['estado'])) {
    // Quién entró y quién entregó en cada estación, y cómo va cada alumno del
    // turno en curso (lo pide el panel cada pocos segundos).
    $o = Osce::avanzar($osce);
    $ctx = Osce::contexto($o);
    $t = Osce::transcurrido($o, time());
    $st = $t === null ? null : Osce::estadoTurno($ctx['cfg'], $ctx['estaciones'], $ctx['parts'], $ctx['entregas'], (int) $o['turno'], $t);
    Response::json([
        'entregas' => (object) array_map(static fn ($m) => (object) $m, Osce::estadosEntregas($id)),
        'turno' => $st['pares'] ?? [],
        'ausentes' => array_values(array_map(static fn ($p) => (int) $p['numero'],
            array_filter($ctx['parts'], static fn ($p) => (int) ($p['ausente'] ?? 0) === 1))),
    ]);
}

$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $accion = (string) ($_POST['accion'] ?? '');
    try {
        switch ($accion) {
            case 'iniciar': Osce::iniciar($id); break;
            case 'pausar': Osce::pausar($id); break;
            case 'reanudar': Osce::reanudar($id); break;
            // El reloj corre para todos: +1 min les da un minuto más a todos los que trabajan.
            case 'mas_tiempo': Osce::ajustar($id, -60); break;
            case 'menos_tiempo': Osce::ajustar($id, 60); break;
            case 'forzar_cambio': Osce::forzarCambio($id); break;
            case 'ausente': Osce::marcarAusente($id, (int) ($_POST['numero'] ?? 0), !empty($_POST['valor'])); break;
            case 'cerrar': Osce::cerrar($id); break;
            case 'borrador': Osce::volverABorrador($id); break;
            default: throw new InvalidArgumentException('Acción desconocida.');
        }
        AdminAudit::log($me, 'osce_reloj_' . $accion, ['osce_id' => $id]);
        header('Location: osce_vivo.php?id=' . $id);
        exit;
    } catch (InvalidArgumentException $e) {
        $error = $e->getMessage();
    }
}

$parts = array_map(static fn ($p) => [
    'numero' => (int) $p['numero'],
    'codigo' => $p['codigo'],
    'vuelta' => (int) $p['vuelta'],
    'circuito' => (int) $p['circuito'],
    'puesto' => (int) $p['puesto'],
    'ausente' => (int) ($p['ausente'] ?? 0) === 1,
], Osce::participantes($id));

admin_header('Panel de control · ' . $osce['nombre'], $me);
?>
<style>
.osce-vivo { text-align: center; }
.osce-fase { font-size: 2rem; font-weight: 700; margin: 0.4rem 0; }
.osce-cuenta { font: 700 clamp(5rem, 18vw, 14rem)/1 ui-monospace, monospace; letter-spacing: -0.02em; margin: 0.2rem 0 0.6rem; }
.osce-sub { font-size: 1.25rem; color: var(--color-text-muted, #555); }
.osce-vivo[data-fase="estacion"] .osce-cuenta { color: var(--color-text, #111); }
.osce-vivo[data-fase="cambio"] .osce-cuenta,
.osce-vivo[data-fase="entre_vueltas"] .osce-cuenta { color: #b45309; }
.osce-vivo[data-fase="estacion"][data-ultimo="1"] .osce-cuenta { color: #b91c1c; }
.osce-puestos td, .osce-puestos th { font-size: 1.05rem; }
.osce-puestos .mono { font-size: 1.2rem; }
.osce-controles form { display: inline; margin: 0; }
.chip { display: inline-block; padding: 0.1rem 0.5rem; border-radius: 1rem; margin: 0.1rem 0.15rem; font-weight: 700; border: 1.5px solid #c9c2cc; color: #6b6070; }
.chip.en_curso { border-color: #b45309; color: #b45309; background: #fff7e6; }
.chip.enviada { border-color: #15803d; color: #fff; background: #15803d; }
.chip.trabajando { border-color: #b45309; color: #b45309; background: #fff7e6; }
.chip.entregada { border-color: #15803d; color: #fff; background: #15803d; }
.chip.vencida { border-color: #6b7280; color: #fff; background: #6b7280; }
.chip.ausente, .chip.descanso { border-style: dashed; color: #9ca3af; text-decoration: line-through; }
.chip small { font: 400 0.85em system-ui, sans-serif; margin-left: 0.3rem; letter-spacing: 0; }
.osce-ausentes { margin-top: 1rem; font-size: 0.95rem; }
.osce-ausentes form { display: inline; margin: 0; }
.osce-ausentes button { margin: 0.1rem; min-width: 2.6rem; }
.osce-ausentes button[aria-pressed="true"] { background: #6b7280; color: #fff; border-color: #6b7280; text-decoration: line-through; }
.leyenda { font-size: 0.9rem; color: var(--color-text-muted, #666); margin-top: 0.4rem; }
.osce-controles .btn { margin: 0; }
.osce-vivo:fullscreen { background: var(--color-surface, #fff); padding: 2rem; overflow: auto; }
</style>

<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>

<div class="row row--between row--center" style="margin-bottom:1rem;">
    <a href="osce.php?id=<?= $id ?>">← Armado del OSCE</a>
    <span class="row row--gap-sm osce-controles">
        <?php $boton = static function (string $accion, string $texto, string $clase = 'btn--sm', string $confirmar = '') use ($id): string {
            return '<form method="post">' . csrf_field() . '<input type="hidden" name="id" value="' . $id . '">'
                . '<button type="submit" name="accion" value="' . $accion . '" class="btn ' . $clase . '"'
                . ($confirmar !== '' ? ' onclick="return confirm(\'' . htmlspecialchars($confirmar, ENT_QUOTES) . '\')"' : '')
                . '>' . htmlspecialchars($texto) . '</button></form>';
        }; ?>
        <?php if ($osce['estado'] === 'borrador'): ?>
            <?= $boton('iniciar', '▶ Iniciar OSCE', 'btn--sm', '¿Iniciar el OSCE? El reloj parte ahora para todos y la estructura queda fija.') ?>
        <?php elseif ($osce['estado'] === 'en_curso'): ?>
            <?= $osce['pausado_desde'] === null ? $boton('pausar', '⏸ Pausar') : $boton('reanudar', '▶ Reanudar') ?>
            <?= $boton('menos_tiempo', '−1 min a todos', 'btn--sm btn--ghost') ?>
            <?= $boton('mas_tiempo', '+1 min a todos', 'btn--sm btn--ghost') ?>
            <?= $boton('forzar_cambio', 'Forzar cambio', 'btn--sm btn--secondary', '¿Dar el turno por terminado? Parte el cambio aunque alguna estación siga abierta.') ?>
            <?= $boton('cerrar', 'Cerrar OSCE', 'btn--sm btn--danger', '¿Cerrar el OSCE? El reloj se detiene para todos.') ?>
            <?= $boton('borrador', 'Volver a borrador', 'btn--sm btn--ghost', 'Solo si se inició por error: el reloj vuelve a cero. ¿Seguir?') ?>
        <?php endif; ?>
        <button type="button" class="btn btn--sm btn--secondary" id="osce-sonido">🔇 Voz y timbre en este equipo</button>
        <button type="button" class="btn btn--sm btn--ghost" id="osce-pantalla">Pantalla completa</button>
    </span>
</div>

<div class="card osce-vivo" id="osce-vivo" data-fase="">
    <div class="osce-sub"><?= htmlspecialchars($osce['nombre']) ?></div>
    <div class="osce-fase" id="osce-fase">Cargando…</div>
    <div class="osce-cuenta" id="osce-cuenta">--:--</div>
    <div class="osce-sub" id="osce-donde"></div>
    <div class="osce-sub" id="osce-sala" style="margin-top:0.8rem;"></div>
    <div class="table-wrap" style="margin-top:1.2rem;">
        <table class="osce-puestos">
            <thead><tr><th>Estación</th><th id="osce-col-ahora">Ahora</th><th id="osce-col-sig">Siguiente</th></tr></thead>
            <tbody id="osce-tabla"></tbody>
        </table>
    </div>
    <div class="leyenda" id="osce-leyenda"></div>
    <?php if ($osce['estado'] === 'en_curso'): ?>
    <div class="osce-ausentes">Ausentes (toca un número para marcarlo; sus estaciones no lo esperan):
        <div id="osce-ausentes"><?php foreach ($parts as $pp): ?><form method="post"><?= csrf_field() ?>
            <input type="hidden" name="id" value="<?= $id ?>"><input type="hidden" name="accion" value="ausente">
            <input type="hidden" name="numero" value="<?= $pp['numero'] ?>">
            <input type="hidden" name="valor" value="<?= $pp['ausente'] ? '' : '1' ?>">
            <button type="submit" class="btn btn--xs btn--ghost" aria-pressed="<?= $pp['ausente'] ? 'true' : 'false' ?>"><?= $pp['numero'] ?></button></form><?php endforeach; ?></div>
    </div>
    <?php endif; ?>
</div>

<script src="../js/osce_reloj.js?v=<?= admin_asset_version(__DIR__ . '/../js/osce_reloj.js') ?>"></script>
<script>
(function () {
    'use strict';
    var parts = <?= json_encode($parts) ?>;
    var url = '../api/osce_reloj.php?r=<?= htmlspecialchars($osce['reloj_token']) ?>';
    var NOMBRE_FASE = {
        antes: 'Aún no parte', estacion: 'En estación', cambio: 'Cambio de estación',
        entre_vueltas: 'Pausa entre vueltas', terminado: 'OSCE terminado'
    };
    var $ = function (id) { return document.getElementById(id); };

    // -- Timbre (WebAudio; el navegador exige un clic antes de sonar) --------
    var audio = null;
    $('osce-sonido').addEventListener('click', function () {
        if (!audio) {
            audio = new (window.AudioContext || window.webkitAudioContext)();
            this.textContent = '🔔 Voz y timbre activos';
            pitar(1, 880, 0.15);
            decir('Voz activa');
        }
    });
    // "Cambio" en voz alta (síntesis del navegador, en español).
    function decir(texto) {
        if (!audio || !window.speechSynthesis) return;
        var u = new SpeechSynthesisUtterance(texto);
        var voces = window.speechSynthesis.getVoices().filter(function (v) { return /^es/i.test(v.lang); });
        var cl = voces.filter(function (v) { return /CL|419|MX|US/i.test(v.lang); })[0] || voces[0];
        if (cl) u.voice = cl;
        u.lang = cl ? cl.lang : 'es-CL';
        u.rate = 0.95;
        u.volume = 1;
        window.speechSynthesis.cancel();
        window.speechSynthesis.speak(u);
    }
    function pitar(veces, hz, largo) {
        if (!audio) return;
        for (var i = 0; i < veces; i++) {
            var t = audio.currentTime + i * (largo + 0.18);
            var o = audio.createOscillator(), g = audio.createGain();
            o.frequency.value = hz;
            g.gain.setValueAtTime(0.0001, t);
            g.gain.exponentialRampToValueAtTime(0.6, t + 0.02);
            g.gain.exponentialRampToValueAtTime(0.0001, t + largo);
            o.connect(g); g.connect(audio.destination);
            o.start(t); o.stop(t + largo + 0.05);
        }
    }

    $('osce-pantalla').addEventListener('click', function () {
        var el = $('osce-vivo');
        if (el.requestFullscreen) el.requestFullscreen();
    });

    // En cadena: el grupo g está en la estación e en el turno g + e.
    var ENTREGAS = {}, TURNO = [], TURNO_LOCAL = 0;
    function pedirEstados() {
        fetch('osce_vivo.php?id=<?= $id ?>&estado=1', { credentials: 'same-origin', cache: 'no-store' })
            .then(function (r) { return r.json(); }).then(function (d) {
                ENTREGAS = d.entregas || {};
                TURNO = d.turno || [];
                TURNO_LOCAL = performance.now();
            })
            .catch(function () {});
    }
    // Alumnos del turno en curso en la estación de índice e: chip con su estado y lo que le queda.
    var ROTULO = { esperando: 'no ha entrado', trabajando: '', entregada: '✓', vencida: 'tiempo', ausente: 'ausente', descanso: 'descanso' };
    function ahoraEn(e) {
        var dt = (performance.now() - TURNO_LOCAL) / 1000;
        var lista = TURNO.filter(function (x) { return x.indice === e; });
        if (!lista.length) return '—';
        return lista.map(function (x) {
            var extra = x.estado === 'trabajando' && x.restante_s !== null ? OsceReloj.mmss(Math.max(0, x.restante_s - dt)) : ROTULO[x.estado];
            return '<span class="chip ' + x.estado + '">' + x.numero + (extra ? '<small>' + extra + '</small>' : '') + '</span>';
        }).join('');
    }
    pedirEstados();
    setInterval(pedirEstados, 5000);
    function grupoEn(cfg, turno, estacion, estId) {
        var g = turno - estacion;
        if (g < 0 || g >= cfg.grupos) return '—';
        return numerosDe(cfg, g, estId);
    }
    // Con estId, cada número dice si entró (naranjo) o entregó (verde).
    function numerosDe(cfg, g, estId) {
        var ns = parts.filter(function (p) { return Math.floor((p.numero - 1) / cfg.por_turno) === g; })
                      .map(function (p) { return p.numero; });
        if (!ns.length) return '—';
        if (estId === undefined) return 'N.º ' + ns.join(' · ');
        var est = ENTREGAS[estId] || {};
        return ns.map(function (n) {
            var st = est[n] || '';
            return '<span class="chip ' + st + '">' + n + (st === 'enviada' ? ' ✓' : '') + '</span>';
        }).join('');
    }
    function quien(cfg, vuelta, slot, estacion, circuito, estId) {
        if (cfg.modo === 'cadena') return grupoEn(cfg, slot, estacion, estId);
        var S = cfg.estaciones;
        var puesto = ((estacion - slot) % S + S) % S;
        for (var i = 0; i < parts.length; i++) {
            var p = parts[i];
            if (p.vuelta === vuelta && p.circuito === circuito && p.puesto === puesto) return p.codigo;
        }
        return '—';
    }

    var faseAnterior = null, avisoMinuto = null, ultimaActividad = 0;
    OsceReloj.iniciar(url, function (d, reloj) {
        // El proyector pasa horas sin que nadie lo toque: mientras el OSCE
        // corre cuenta como actividad (si no, la sesión se corta a los 72 min).
        if (d.estado === 'en_curso' && window.LabSimSesion && Date.now() - ultimaActividad > 60000) {
            ultimaActividad = Date.now();
            window.LabSimSesion.actividad();
        }
        var cfg = d.cfg, S = cfg.estaciones, T = cfg.turnos || S;
        var C = cfg.modo === 'cadena' ? 1 : d.circuitos;
        var cont = $('osce-vivo');
        if (!reloj) {
            $('osce-fase').textContent = d.estado === 'borrador' ? 'Aún no parte' : (NOMBRE_FASE[d.estado] || d.estado);
            $('osce-cuenta').textContent = '--:--';
            $('osce-donde').textContent = d.inicio_programado ? 'Programado: ' + d.inicio_programado.replace(/^(\d{4})-(\d\d)-(\d\d)/, '$3-$2-$1') : '';
            cont.dataset.fase = 'antes';
        } else {
            var fase = reloj.fase;
            if (d.estado === 'cerrado' || d.estado === 'publicado') fase = 'terminado';
            cont.dataset.fase = fase;
            cont.dataset.ultimo = fase === 'estacion' && reloj.restante_s <= 60 ? '1' : '0';
            $('osce-fase').textContent = (NOMBRE_FASE[fase] || fase) + (d.pausado ? ' · EN PAUSA' : '');
            // En estación: lo que le queda al último que entró (cada alumno tiene su tiempo).
            $('osce-cuenta').textContent = fase === 'terminado' ? '0:00'
                : (reloj.restante_s === null ? '--:--' : OsceReloj.mmss(reloj.restante_s));
            if (fase === 'estacion') {
                $('osce-fase').textContent += reloj.restante_s === null ? ' · esperando que entren'
                    : ' · ' + (reloj.abiertos === 1 ? 'falta 1 alumno por terminar' : 'faltan ' + reloj.abiertos + ' alumnos por terminar');
            }
            $('osce-donde').textContent = fase === 'terminado' ? '' :
                (cfg.modo === 'cadena'
                    ? 'Turno ' + (reloj.slot + 1) + ' de ' + T
                    : 'Vuelta ' + (reloj.vuelta + 1) + ' de ' + cfg.vueltas + ' · Tiempo ' + (reloj.slot + 1) + ' de ' + S);

            // Todas las estaciones cerraron: "cambio" en voz alta. Empieza el turno nuevo: un timbre.
            var clave = fase + ':' + reloj.turno;
            if (faseAnterior !== null && clave !== faseAnterior && !d.pausado) {
                if (fase === 'estacion') pitar(1, 880, 0.6);
                else if (fase === 'cambio') { pitar(1, 660, 0.4); setTimeout(function () { decir('Cambio'); }, 500); }
                else if (fase === 'entre_vueltas') { pitar(1, 660, 0.4); setTimeout(function () { decir('Cambio. Pausa entre vueltas'); }, 500); }
                else if (fase === 'terminado') { pitar(3, 660, 0.5); setTimeout(function () { decir('Fin del OSCE'); }, 1800); }
            }
            faseAnterior = clave;
            if (fase === 'estacion' && reloj.restante_s <= 60 && reloj.restante_s > 55 && avisoMinuto !== clave) {
                avisoMinuto = clave;
                pitar(2, 990, 0.15);
            }

            // Quién está en cada estación ahora y quién viene.
            var filas = '';
            var ahoraV = reloj.vuelta, ahoraJ = reloj.slot;
            var sigV = ahoraV, sigJ = ahoraJ + 1;
            if (fase === 'entre_vueltas' || sigJ >= T) { sigV = ahoraV + 1; sigJ = 0; }
            var haySig = sigV < cfg.vueltas && fase !== 'terminado';
            $('osce-col-ahora').textContent = fase === 'estacion' ? 'Ahora' : 'Recién';
            for (var e = 0; e < S; e++) {
                for (var c = 0; c < C; c++) {
                    filas += '<tr><td>' + (e + 1) + '. ' + escapar(d.estaciones[e].titulo) + (C > 1 ? ' · circuito ' + (c + 1) : '') + '</td>'
                        + '<td class="mono">' + (fase === 'terminado' ? '—' : (fase === 'estacion' ? ahoraEn(e) : quien(cfg, ahoraV, ahoraJ, e, c, d.estaciones[e].id))) + '</td>'
                        + '<td class="mono">' + (haySig ? quien(cfg, sigV, sigJ, e, c) : '—') + '</td></tr>';
                }
            }
            $('osce-tabla').innerHTML = filas;
            $('osce-leyenda').innerHTML = '<span class="chip esperando">N.º</span> no ha entrado · <span class="chip trabajando">N.º<small>m:ss</small></span> trabajando (le queda)'
                + ' · <span class="chip entregada">N.º</span> entregó · <span class="chip vencida">N.º</span> se le acabó el tiempo · <span class="chip ausente">N.º</span> ausente';
            // Cadena: quiénes hacen de paciente en la limpieza y quiénes entran después.
            var sala = '';
            if (cfg.modo === 'cadena' && fase !== 'terminado') {
                var turnoP = fase === 'estacion' ? ahoraJ : sigJ;
                var gp = turnoP + 1 < cfg.grupos ? turnoP + 1 : (cfg.grupos > 1 && turnoP === cfg.grupos - 1 ? 0 : -1);
                if (gp >= 0) sala += 'Pacientes en la limpieza: ' + numerosDe(cfg, gp) + (gp === 0 ? ' (el primer grupo vuelve)' : '');
                var gs = turnoP + 2;
                if (gs < cfg.grupos) sala += (sala ? '  ·  ' : '') + 'Prepárense: ' + numerosDe(cfg, gs);
            }
            $('osce-sala').textContent = sala;
        }
    });

    function escapar(s) {
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }
})();
</script>
<?php
admin_footer();
