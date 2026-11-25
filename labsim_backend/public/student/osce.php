<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Osce.php';

/**
 * Página del QR de la tarjeta OSCE. Sin login: el alumno la abre en su
 * teléfono escaneando el QR (token largo aleatorio en ?t=). Durante el OSCE
 * muestra dónde le toca estar y cuánto queda; al final, su resultado, pero
 * solo cuando el docente lo publica (estado 'publicado').
 */

header('Content-Type: text/html; charset=utf-8');
header('Cache-Control: no-store');
header('Referrer-Policy: no-referrer');

$token = (string) ($_GET['t'] ?? '');
$p = Osce::participantePorToken($token);
$o = $p !== null ? Osce::obtener((int) $p['osce_id']) : null;

$cssV = static fn (string $path): string => (string) (@filemtime($path) ?: time());
$cabeza = static function (string $titulo) use ($cssV): void { ?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title><?= htmlspecialchars($titulo) ?></title>
<link rel="stylesheet" href="../css/tokens.css?v=<?= $cssV(__DIR__ . '/../css/tokens.css') ?>">
<link rel="stylesheet" href="../css/base.css?v=<?= $cssV(__DIR__ . '/../css/base.css') ?>">
<style>
body { max-width: 34rem; margin: 0 auto; padding: 1rem; }
.cod { font: 700 2.2rem ui-monospace, monospace; letter-spacing: 0.05em; margin: 0.2rem 0; }
.ahora { text-align: center; padding: 1.2rem 1rem; }
.ahora .fase { font-size: 1.05rem; color: var(--color-text-muted, #555); }
.ahora .estacion { font-size: 1.5rem; font-weight: 700; margin: 0.3rem 0; }
.ahora .cuenta { font: 700 3.2rem/1.1 ui-monospace, monospace; }
.recorrido li { padding: 0.45rem 0; border-bottom: 1px solid var(--color-border, #ddd); display: flex; justify-content: space-between; gap: 0.5rem; }
.recorrido li.actual { font-weight: 700; }
.recorrido li.hecha { color: var(--color-text-muted, #777); }
.recorrido { list-style: none; padding: 0; margin: 0; }
.nota { font: 700 2.4rem ui-monospace, monospace; }
</style>
</head>
<body>
<?php };

if ($p === null || $o === null) {
    http_response_code(404);
    $cabeza('OSCE');
    echo '<div class="card"><h1>Código no encontrado</h1><p>Revisa que escaneaste el QR de tu tarjeta. Si el problema sigue, avisa al docente.</p></div></body></html>';
    exit;
}

$recorrido = Osce::recorrido($o, $p);
$publicado = $o['estado'] === 'publicado';

// Resultado: nota por estación y final ponderada por peso.
$resultado = null;
if ($publicado) {
    $sumaPeso = 0.0;
    $sumaPct = 0.0;
    $filas = [];
    foreach ($recorrido as $f) {
        $e = $f['estacion'];
        $en = $f['entrega'];
        $peso = (float) $e['peso'];
        $pct = null;
        if ($en !== null && $en['puntaje'] !== null && (float) $en['puntaje_max'] > 0) {
            $pct = (float) $en['puntaje'] / (float) $en['puntaje_max'];
        }
        $sumaPeso += $peso;
        $sumaPct += $peso * ($pct ?? 0.0);
        $filas[] = [
            'titulo' => $e['titulo'],
            'pct' => $pct,
            'nota' => $pct === null ? null : Osce::nota($pct * 100, 100, (int) $o['exigencia'], (float) $o['nota_aprobacion']),
            'critico' => $en !== null && (int) $en['critico_fallado'] === 1,
            'feedback' => $en['feedback'] ?? '',
        ];
    }
    $pctFinal = $sumaPeso > 0 ? $sumaPct / $sumaPeso : 0.0;
    $resultado = [
        'filas' => $filas,
        'nota' => Osce::nota($pctFinal * 100, 100, (int) $o['exigencia'], (float) $o['nota_aprobacion']),
        'pct' => $pctFinal,
    ];
}

$cabeza('OSCE · ' . $o['nombre']);
?>
<main id="main-content">
<div class="card">
    <div class="muted"><?= htmlspecialchars($o['nombre']) ?></div>
    <div class="cod"><?= htmlspecialchars($p['codigo']) ?></div>
    <div><?= htmlspecialchars((string) $p['display_name']) ?> · vuelta <?= (int) $p['vuelta'] + 1 ?><?= (int) $o['circuitos'] > 1 ? ' · circuito ' . ((int) $p['circuito'] + 1) : '' ?></div>
</div>

<?php if ($resultado !== null): ?>
<div class="card">
    <h2>Tu resultado</h2>
    <p class="nota"><?= number_format($resultado['nota'], 1, ',', '') ?></p>
    <p class="muted"><?= round($resultado['pct'] * 100) ?> % de logro · exigencia <?= (int) $o['exigencia'] ?> %</p>
    <ul class="recorrido">
    <?php foreach ($resultado['filas'] as $f): ?>
        <li><span><?= htmlspecialchars($f['titulo']) ?><?= $f['critico'] ? ' <span class="tag tag--danger">ítem crítico</span>' : '' ?></span>
            <span><?= $f['nota'] === null ? 'sin entrega' : number_format($f['nota'], 1, ',', '') . ' (' . round($f['pct'] * 100) . ' %)' ?></span></li>
        <?php if (trim((string) $f['feedback']) !== ''): ?>
        <li style="display:block; border-bottom:0;" class="muted"><?= nl2br(htmlspecialchars((string) $f['feedback'])) ?></li>
        <?php endif; ?>
    <?php endforeach; ?>
    </ul>
</div>
<?php else: ?>
<div class="card ahora" id="ahora">
    <div class="fase" id="ahora-fase">Cargando…</div>
    <div class="estacion" id="ahora-estacion"></div>
    <div class="cuenta" id="ahora-cuenta"></div>
</div>
<?php endif; ?>

<div class="card">
    <h2>Tu recorrido</h2>
    <ol class="recorrido" id="recorrido">
    <?php foreach ($recorrido as $f): ?>
        <li data-slot="<?= (int) $f['slot'] ?>" data-inicio="<?= (int) $f['inicio_s'] ?>">
            <span><?= (int) $f['slot'] + 1 ?>. <?= htmlspecialchars($f['estacion']['titulo']) ?></span>
            <span class="hora muted"></span>
        </li>
    <?php endforeach; ?>
    </ol>
    <?php if (!$publicado): ?>
    <p class="help help--mt">Tu resultado aparecerá aquí cuando el docente lo publique. Guarda este enlace o vuelve a escanear tu tarjeta.</p>
    <?php endif; ?>
</div>
</main>

<script src="../js/osce_reloj.js?v=<?= $cssV(__DIR__ . '/../js/osce_reloj.js') ?>"></script>
<script>
(function () {
    'use strict';
    var url = '../api/osce_reloj.php?t=<?= htmlspecialchars($token) ?>';
    var $ = function (id) { return document.getElementById(id); };
    var items = document.querySelectorAll('#recorrido li');

    function hora(epoch) {
        var d = new Date(epoch * 1000);
        return (d.getHours() < 10 ? '0' : '') + d.getHours() + ':' + (d.getMinutes() < 10 ? '0' : '') + d.getMinutes();
    }

    OsceReloj.iniciar(url, function (d, reloj, t) {
        var yo = d.participante, S = d.cfg.estaciones;
        // Hora estimada de cada estación: con el reloj andando, ahora - t; si
        // no, el inicio programado (hora del curso, tal como se escribió).
        var t0 = null;
        if (t !== null) t0 = Date.now() / 1000 - t;
        else if (d.inicio_programado) {
            var m = /^(\d{4})-(\d\d)-(\d\d) (\d\d):(\d\d)$/.exec(d.inicio_programado);
            if (m) t0 = new Date(+m[1], m[2] - 1, +m[3], +m[4], +m[5]).getTime() / 1000;
        }
        var miSlot = -1, termine = false;
        if (reloj) {
            if (reloj.fase === 'terminado' || reloj.vuelta > yo.vuelta
                || (reloj.vuelta === yo.vuelta && reloj.fase === 'entre_vueltas')) termine = true;
            else if (reloj.vuelta === yo.vuelta) miSlot = reloj.slot;
        }
        if (d.estado === 'cerrado' || d.estado === 'publicado') termine = true;
        for (var i = 0; i < items.length; i++) {
            var li = items[i], slot = +li.dataset.slot;
            li.querySelector('.hora').textContent = t0 !== null ? hora(t0 + +li.dataset.inicio) : '';
            li.classList.toggle('actual', !termine && slot === miSlot && reloj && reloj.fase === 'estacion');
            li.classList.toggle('hecha', termine || (miSlot >= 0 && (slot < miSlot || (slot === miSlot && reloj.fase !== 'estacion'))));
        }
        if (!$('ahora')) return;
        var fase = '', est = '', cuenta = '';
        if (termine) {
            fase = 'Terminaste el OSCE';
            est = 'Gracias. Tu resultado aparecerá aquí cuando se publique.';
        } else if (!reloj || reloj.fase === 'antes') {
            fase = 'Aún no parte';
            var primera = items[0] ? items[0].querySelector('span').textContent.replace(/^\d+\.\s*/, '') : '';
            est = 'Partes en: ' + primera;
            cuenta = t0 !== null ? hora(t0 + +items[0].dataset.inicio) : '';
        } else if (reloj.vuelta < yo.vuelta) {
            fase = 'Esperando tu vuelta (' + (yo.vuelta + 1) + ')';
            est = 'Partes en: ' + items[0].querySelector('span').textContent.replace(/^\d+\.\s*/, '');
            var falta = OsceReloj.inicioSlot(d.cfg, yo.vuelta, 0) - t;
            cuenta = 'en ' + OsceReloj.mmss(falta);
        } else if (reloj.fase === 'estacion') {
            fase = 'Estás en';
            est = items[miSlot].querySelector('span').textContent;
            cuenta = OsceReloj.mmss(reloj.restante_s);
        } else {
            fase = reloj.fase === 'cambio' ? 'Cambio: dirígete a' : 'Pausa';
            est = miSlot + 1 < S ? items[miSlot + 1].querySelector('span').textContent : '';
            cuenta = OsceReloj.mmss(reloj.restante_s);
        }
        if (d.pausado) fase += ' · EN PAUSA';
        $('ahora-fase').textContent = fase;
        $('ahora-estacion').textContent = est;
        $('ahora-cuenta').textContent = cuenta;
    }, 10000);
})();
</script>
</body>
</html>
