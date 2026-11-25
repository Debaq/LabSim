<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Osce.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Reloj del OSCE para el proyector: fase, cuenta regresiva, timbre y quién
 * está en cada estación. Los controles (iniciar, pausar, correr el reloj,
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

$error = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $accion = (string) ($_POST['accion'] ?? '');
    try {
        switch ($accion) {
            case 'iniciar': Osce::iniciar($id); break;
            case 'pausar': Osce::pausar($id); break;
            case 'reanudar': Osce::reanudar($id); break;
            case 'adelantar': Osce::ajustar($id, 60); break;
            case 'atrasar': Osce::ajustar($id, -60); break;
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
    'codigo' => $p['codigo'],
    'vuelta' => (int) $p['vuelta'],
    'circuito' => (int) $p['circuito'],
    'puesto' => (int) $p['puesto'],
], Osce::participantes($id));

admin_header('Reloj · ' . $osce['nombre'], $me);
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
            <?= $boton('atrasar', '−1 min', 'btn--sm btn--ghost') ?>
            <?= $boton('adelantar', '+1 min', 'btn--sm btn--ghost') ?>
            <?= $boton('cerrar', 'Cerrar OSCE', 'btn--sm btn--danger', '¿Cerrar el OSCE? El reloj se detiene para todos.') ?>
            <?= $boton('borrador', 'Volver a borrador', 'btn--sm btn--ghost', 'Solo si se inició por error: el reloj vuelve a cero. ¿Seguir?') ?>
        <?php endif; ?>
        <button type="button" class="btn btn--sm btn--secondary" id="osce-sonido">🔇 Activar timbre</button>
        <button type="button" class="btn btn--sm btn--ghost" id="osce-pantalla">Pantalla completa</button>
    </span>
</div>

<div class="card osce-vivo" id="osce-vivo" data-fase="">
    <div class="osce-sub"><?= htmlspecialchars($osce['nombre']) ?></div>
    <div class="osce-fase" id="osce-fase">Cargando…</div>
    <div class="osce-cuenta" id="osce-cuenta">--:--</div>
    <div class="osce-sub" id="osce-donde"></div>
    <div class="table-wrap" style="margin-top:1.2rem;">
        <table class="osce-puestos">
            <thead><tr><th>Estación</th><th id="osce-col-ahora">Ahora</th><th id="osce-col-sig">Siguiente</th></tr></thead>
            <tbody id="osce-tabla"></tbody>
        </table>
    </div>
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
            this.textContent = '🔔 Timbre activo';
            pitar(1, 880, 0.15);
        }
    });
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

    function quien(cfg, vuelta, slot, estacion, circuito) {
        var S = cfg.estaciones;
        var puesto = ((estacion - slot) % S + S) % S;
        for (var i = 0; i < parts.length; i++) {
            var p = parts[i];
            if (p.vuelta === vuelta && p.circuito === circuito && p.puesto === puesto) return p.codigo;
        }
        return '—';
    }

    var faseAnterior = null, avisoMinuto = null;
    OsceReloj.iniciar(url, function (d, reloj) {
        var cfg = d.cfg, S = cfg.estaciones, C = d.circuitos;
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
            $('osce-cuenta').textContent = fase === 'terminado' ? '0:00' : OsceReloj.mmss(reloj.restante_s);
            $('osce-donde').textContent = fase === 'terminado' ? '' :
                'Vuelta ' + (reloj.vuelta + 1) + ' de ' + cfg.vueltas + ' · Tiempo ' + (reloj.slot + 1) + ' de ' + S;

            // Timbre: fin de estación (3 largos), empieza la siguiente (1), queda 1 minuto (2 cortos).
            var clave = fase + ':' + reloj.vuelta + ':' + reloj.slot;
            if (faseAnterior !== null && clave !== faseAnterior && !d.pausado) {
                if (fase === 'estacion') pitar(1, 880, 0.6);
                else if (fase === 'cambio' || fase === 'entre_vueltas' || fase === 'terminado') pitar(3, 660, 0.5);
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
            if (fase === 'entre_vueltas' || sigJ >= S) { sigV = ahoraV + 1; sigJ = 0; }
            var haySig = sigV < cfg.vueltas && fase !== 'terminado';
            $('osce-col-ahora').textContent = fase === 'estacion' ? 'Ahora' : 'Recién';
            for (var e = 0; e < S; e++) {
                for (var c = 0; c < C; c++) {
                    filas += '<tr><td>' + (e + 1) + '. ' + escapar(d.estaciones[e].titulo) + (C > 1 ? ' · circuito ' + (c + 1) : '') + '</td>'
                        + '<td class="mono">' + (fase === 'terminado' ? '—' : quien(cfg, ahoraV, ahoraJ, e, c)) + '</td>'
                        + '<td class="mono">' + (haySig ? quien(cfg, sigV, sigJ, e, c) : '—') + '</td></tr>';
                }
            }
            $('osce-tabla').innerHTML = filas;
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
