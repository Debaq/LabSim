<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Osce.php';
require_once __DIR__ . '/../../src/OscePauta.php';
require_once __DIR__ . '/../../src/OscePreguntas.php';
require_once __DIR__ . '/../../src/OsceApp.php';

/**
 * Página del QR de la tarjeta OSCE. Sin login: el alumno la abre en su
 * teléfono escaneando el QR (token largo aleatorio en ?t=). Durante el OSCE
 * muestra dónde le toca estar y cuánto queda; al final, su resultado, pero
 * solo cuando el docente lo publica (estado 'publicado'): nota, detalle por
 * estación con el feedback, y la réplica de las respuestas de preguntas.
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
.numero { font-size: 3.4rem; font-weight: 800; color: var(--color-primary, #5d1049); line-height: 1; }
.numero small { display: block; font-size: 0.8rem; font-weight: 600; color: var(--color-text-muted, #666); }
.nota { font-size: 2.6rem; font-weight: 700; font-variant-numeric: tabular-nums; margin: 0.2rem 0; }
.det-lista { list-style: none; padding: 0; margin: 0; }
.det-lista li { padding: 0.5rem 0; border-bottom: 1px solid var(--color-border, #ddd); }
.det-lista li > span:first-child { display: block; }
.det-v { font-weight: 600; font-size: 0.95rem; }
.det-cumple { color: #15803d; } .det-parcial { color: #b45309; } .det-no_cumple { color: #b91c1c; }
.det-com { font-size: 0.92rem; color: var(--color-text-muted, #555); margin-top: 0.3rem; }
.det-q { padding: 0.6rem 0; border-bottom: 1px solid var(--color-border, #ddd); }
.det-ops { list-style: none; padding: 0; margin: 0.3rem 0; }
.op-ok { color: #15803d; font-weight: 600; } .op-mal { color: #b91c1c; } .op-falto { color: #15803d; }
.det-resp { background: var(--color-surface-2, #f4f4f6); border-radius: 0.4rem; padding: 0.5rem 0.7rem; }
.det-rep { border-left: 3px solid #b45309; padding-left: 0.6rem; margin-top: 0.5rem; font-size: 0.95rem; }
.det-rep-form summary { cursor: pointer; font-size: 0.92rem; margin-top: 0.4rem; color: var(--color-primary, #7a1f3d); }
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

// Tarjeta sorteada sin dueño: el alumno la amarra eligiendo su nombre.
if ($p['user_id'] === null) {
    $errTarjeta = null;
    if ($_SERVER['REQUEST_METHOD'] === 'POST' && hash_equals($token, (string) ($_POST['t'] ?? ''))) {
        try {
            Osce::reclamarTarjeta($p, (int) ($_POST['user_id'] ?? 0));
            header('Location: osce.php?t=' . rawurlencode($token));
            exit;
        } catch (InvalidArgumentException $e) {
            $errTarjeta = $e->getMessage();
        }
    }
    $conTarjeta = [];
    foreach (Osce::participantes((int) $o['id']) as $x) {
        if ($x['user_id'] !== null) {
            $conTarjeta[(int) $x['user_id']] = true;
        }
    }
    $libres = array_filter(Osce::alumnosDelCurso((int) $o['course_id']), static fn ($u) => !isset($conTarjeta[(int) $u['id']]));
    $cabeza('OSCE · tarjeta ' . (int) $p['numero']);
    ?>
<main id="main-content">
<div class="card">
    <div class="muted"><?= htmlspecialchars($o['nombre']) ?></div>
    <div class="numero"><small>N.º</small><?= (int) $p['numero'] ?></div>
    <h1 style="font-size:1.3rem; margin:0.4rem 0;">¿Quién eres?</h1>
    <p>Elige tu nombre para quedarte con esta tarjeta. Desde aquí verás tu avance y, al final, tu nota.</p>
    <?php if ($errTarjeta !== null): ?><p class="error"><?= htmlspecialchars($errTarjeta) ?></p><?php endif; ?>
    <form method="post">
        <input type="hidden" name="t" value="<?= htmlspecialchars($token) ?>">
        <select name="user_id" required style="width:100%; font-size:1.1rem; padding:0.5rem;">
            <option value="">— Tu nombre —</option>
            <?php foreach ($libres as $u): ?><option value="<?= (int) $u['id'] ?>"><?= htmlspecialchars((string) $u['display_name']) ?></option><?php endforeach; ?>
        </select>
        <button type="submit" class="btn" style="margin-top:0.8rem; width:100%;">Esta es mi tarjeta</button>
    </form>
    <p class="help help--mt">Si tu nombre no aparece o te equivocaste, avisa al docente.</p>
</div>
</main>
</body></html>
<?php
    exit;
}

$recorrido = Osce::recorrido($o, $p);
$publicado = $o['estado'] === 'publicado';

// Réplica de una respuesta (solo con resultados publicados). Sin sesión: el
// token del QR es la identidad, y tiene que venir también en el formulario.
$msgReplica = null;
$errReplica = null;
if ($_SERVER['REQUEST_METHOD'] === 'POST' && $publicado && hash_equals($token, (string) ($_POST['t'] ?? ''))) {
    try {
        OscePreguntas::replicar((int) $p['id'], (int) ($_POST['resultado'] ?? 0), (string) ($_POST['texto'] ?? ''));
        header('Location: osce.php?t=' . rawurlencode($token) . '&replica=1#r' . (int) ($_POST['resultado'] ?? 0));
        exit;
    } catch (InvalidArgumentException $e) {
        $errReplica = $e->getMessage();
    }
}
if (isset($_GET['replica'])) {
    $msgReplica = 'Réplica enviada. El docente la revisará y verás su respuesta aquí.';
}
$pts = static fn ($x): string => $x === null ? '—' : rtrim(rtrim(number_format((float) $x, 2, ',', ''), '0'), ',');

// Resultado: nota por estación y final ponderada por peso.
$resultado = null;
if ($publicado) {
    $sumaPeso = 0.0;
    $sumaPct = 0.0;
    $filas = [];
    foreach ($recorrido as $f) {
        if ($f['paciente'] !== null) {
            continue;   // el turno de paciente no se evalúa
        }
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
            'estacion' => $e,
            'entrega' => $en,
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
    <div class="row row--between row--center">
        <div class="numero"><small>N.º</small><?= (int) $p['numero'] ?></div>
        <div style="text-align:right;"><div class="cod" style="font-size:1.3rem;"><?= htmlspecialchars($p['codigo']) ?></div>
            <div><?= htmlspecialchars((string) $p['display_name']) ?></div></div>
    </div>
</div>

<?php if ($msgReplica !== null): ?><p class="success"><?= htmlspecialchars($msgReplica) ?></p><?php endif; ?>
<?php if ($errReplica !== null): ?><p class="error"><?= htmlspecialchars($errReplica) ?></p><?php endif; ?>
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

<?php foreach ($resultado['filas'] as $f): $e = $f['estacion']; if ($f['entrega'] === null) { continue; } ?>
<div class="card detalle">
    <h2><?= htmlspecialchars($e['titulo']) ?> <span class="muted" style="font-size:1rem;"><?= $pts($f['entrega']['puntaje']) ?> / <?= $pts($f['entrega']['puntaje_max']) ?> pt</span></h2>
    <?php if ($e['tipo'] === 'pauta_docente'):
        $guardado = OscePauta::cargar((int) $e['id'], (int) $p['id'])['items']; ?>
        <ul class="det-lista">
        <?php foreach (OscePauta::items((int) $e['id']) as $it): $g = $guardado[(int) $it['id']] ?? null; ?>
            <li>
                <span><?= htmlspecialchars($it['texto']) ?><?= (int) $it['critico'] ? ' <span class="tag tag--danger">crítico</span>' : '' ?></span>
                <?php if ($it['tipo'] === 'impedancias'):
                    $calc = $g['valor']['calculo'] ?? null; ?>
                    <span class="det-v"><?= $calc && $calc['inter'] !== null
                        ? htmlspecialchars(implode(' · ', array_map(static fn ($x) => $x === null ? '—' : str_replace('.', ',', (string) $x), $calc['valores']))) . ' kΩ · interelectrodo ' . str_replace('.', ',', (string) $calc['inter'])
                        : 'sin registro' ?></span>
                <?php else: ?>
                    <span class="det-v det-<?= htmlspecialchars((string) ($g['valor'] ?? '')) ?>"><?= htmlspecialchars(OscePauta::TICK[$g['valor'] ?? ''] ?? 'Sin marcar') ?></span>
                <?php endif; ?>
                <?php if ($g && trim((string) $g['comentario']) !== ''): ?><div class="det-com"><?= nl2br(htmlspecialchars((string) $g['comentario'])) ?></div><?php endif; ?>
            </li>
        <?php endforeach; ?>
        </ul>
    <?php elseif (OsceApp::esApp((string) $e['tipo'])): ?>
        <ul class="det-lista">
        <?php foreach (OsceApp::detalle((int) $e['id'], (int) $p['id']) as $d): $ev = $d['eval'] ?? []; $r = $d['resultado']; ?>
            <li>
                <span><?= htmlspecialchars($d['item']['texto']) ?><?= (int) $d['item']['critico'] ? ' <span class="tag tag--danger">crítico</span>' : '' ?>
                    <span class="muted">· <?= $pts($r['puntaje'] ?? null) ?> / <?= $pts($d['item']['puntaje']) ?> pt<?= !empty($d['item']['cfg']['bonus']) ? ' extra' : '' ?></span></span>
                <?php if (!empty($ev['ia']) || !empty($ev['pendiente'])): ?>
                <span class="det-com"><?= htmlspecialchars((string) ($ev['pendiente'] ?? false ? 'Pendiente de corrección.' : ($ev['alumno'] ?? ''))) ?></span>
                <?php else: ?>
                <span class="det-v <?= !empty($ev['ok']) ? 'det-cumple' : 'det-no_cumple' ?>">Tú: <?= htmlspecialchars((string) ($ev['alumno'] ?? '—')) ?></span>
                <span class="det-com">Esperado: <?= htmlspecialchars((string) ($ev['esperado'] ?? '—')) ?></span>
                <?php endif; ?>
                <?php if ($r && trim((string) $r['comentario']) !== ''): ?><div class="det-com"><strong>Docente:</strong> <?= nl2br(htmlspecialchars((string) $r['comentario'])) ?></div><?php endif; ?>
            </li>
        <?php endforeach; ?>
        </ul>
    <?php elseif ($e['tipo'] === 'preguntas'): ?>
        <?php foreach (OscePreguntas::detalleAlumno((int) $e['id'], (int) $p['id']) as $n => $d):
            $q = $d['pregunta']; $r = $d['resultado']; ?>
        <div class="det-q" id="r<?= $r ? (int) $r['id'] : 0 ?>">
            <p><strong><?= $n + 1 ?>.</strong> <?= nl2br(htmlspecialchars($q['enunciado'])) ?>
               <span class="muted">· <?= $pts($r['puntaje'] ?? null) ?> / <?= $pts($q['puntaje']) ?> pt</span></p>
            <?php if ($q['tipo'] === 'alternativa'): $marc = is_array($d['valor']) ? $d['valor'] : []; ?>
                <ul class="det-ops">
                <?php foreach ($q['opciones'] as $i => $op): $esC = in_array($i, $q['correctas'], true); $m = in_array($i, $marc, true); ?>
                    <li class="<?= $m ? ($esC ? 'op-ok' : 'op-mal') : ($esC ? 'op-falto' : '') ?>"><?= $m ? '☑' : '☐' ?> <?= htmlspecialchars($op) ?><?= $esC ? ' <span class="muted">(correcta)</span>' : '' ?></li>
                <?php endforeach; ?>
                </ul>
            <?php else: ?>
                <div class="det-resp"><?= trim((string) $d['valor']) === '' ? '<span class="muted">(sin respuesta)</span>' : nl2br(htmlspecialchars((string) $d['valor'])) ?></div>
            <?php endif; ?>
            <?php if ($r && trim((string) $r['ia_comentario']) !== '' && $r['fuente'] !== 'docente'): ?>
                <div class="det-com"><?= nl2br(htmlspecialchars((string) $r['ia_comentario'])) ?></div>
            <?php endif; ?>
            <?php if ($r && trim((string) $r['comentario']) !== ''): ?>
                <div class="det-com"><strong>Docente:</strong> <?= nl2br(htmlspecialchars((string) $r['comentario'])) ?></div>
            <?php endif; ?>
            <?php if ($r && $r['replica_texto'] !== null): ?>
                <div class="det-rep">
                    <strong>Tu réplica:</strong> <?= nl2br(htmlspecialchars((string) $r['replica_texto'])) ?><br>
                    <?php if ($r['replica_estado'] === 'pendiente'): ?>
                        <span class="muted">En revisión.</span>
                    <?php else: ?>
                        <strong><?= $r['replica_estado'] === 'aceptada' ? 'Aceptada' : 'No aceptada' ?>.</strong>
                        <?= nl2br(htmlspecialchars((string) $r['replica_respuesta'])) ?>
                    <?php endif; ?>
                </div>
            <?php elseif ($r && (float) $r['puntaje'] < (float) $q['puntaje']): ?>
                <details class="det-rep-form">
                    <summary>Hacer réplica de esta respuesta</summary>
                    <form method="post" action="osce.php?t=<?= htmlspecialchars(rawurlencode($token)) ?>">
                        <input type="hidden" name="t" value="<?= htmlspecialchars($token) ?>">
                        <input type="hidden" name="resultado" value="<?= (int) $r['id'] ?>">
                        <textarea name="texto" rows="3" required maxlength="2000" placeholder="Explica por qué crees que tu respuesta merece otro puntaje" style="width:100%;"></textarea>
                        <button type="submit" class="btn btn--sm">Enviar réplica</button>
                    </form>
                </details>
            <?php endif; ?>
        </div>
        <?php endforeach; ?>
    <?php endif; ?>
    <?php if (trim((string) $f['feedback']) !== ''): ?>
        <div class="det-com"><strong>Comentario general:</strong> <?= nl2br(htmlspecialchars((string) $f['feedback'])) ?></div>
    <?php endif; ?>
</div>
<?php endforeach; ?>
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
        <li data-inicio="<?= (int) $f['inicio_s'] ?>" data-nombre="<?= htmlspecialchars($f['paciente'] !== null
                ? 'Paciente en ' . $f['estacion']['titulo'] . ' (te limpia el N.º ' . (int) $f['paciente'] . ')'
                : $f['estacion']['titulo']) ?>" data-paciente="<?= $f['paciente'] !== null ? 1 : 0 ?>">
            <span><?= $f['paciente'] !== null
                ? '<em>Paciente</em> en ' . htmlspecialchars($f['estacion']['titulo']) . ' <span class="muted">(te limpia el N.º ' . (int) $f['paciente'] . ')</span>'
                : htmlspecialchars($f['estacion']['titulo']) ?></span>
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

    // El estado sale de las horas del recorrido (sirve igual en vueltas y en
    // cadena, y con el turno de paciente): dónde está ahora, a dónde va.
    OsceReloj.iniciar(url, function (d, reloj, t) {
        var dur = d.cfg.duracion_s, pausa = d.cfg.pausa_s;
        var t0 = null;
        if (d.inicio_real && d.estado !== 'en_curso') t0 = d.inicio_real;
        else if (t !== null) t0 = Date.now() / 1000 - t;
        else if (d.inicio_programado) {
            var m = /^(\d{4})-(\d\d)-(\d\d) (\d\d):(\d\d)$/.exec(d.inicio_programado);
            if (m) t0 = new Date(+m[1], m[2] - 1, +m[3], +m[4], +m[5]).getTime() / 1000;
        }
        var filas = Array.prototype.map.call(items, function (li) {
            return { li: li, ini: +li.dataset.inicio, nombre: li.dataset.nombre, paciente: li.dataset.paciente === '1' };
        });
        var termine = d.estado === 'cerrado' || d.estado === 'publicado'
            || (t !== null && filas.length && t >= filas[filas.length - 1].ini + dur);
        var actual = null, siguiente = null;
        filas.forEach(function (f) {
            f.li.querySelector('.hora').textContent = t0 !== null ? hora(t0 + f.ini) : '';
            var en = t !== null && t >= f.ini && t < f.ini + dur;
            if (en) actual = f;
            if (t !== null && f.ini > t && siguiente === null) siguiente = f;
            f.li.classList.toggle('actual', !termine && en);
            f.li.classList.toggle('hecha', termine || (t !== null && t >= f.ini + dur));
        });
        if (!$('ahora')) return;
        var fase = '', est = '', cuenta = '';
        if (termine) {
            fase = 'Terminaste el OSCE';
            est = 'Gracias. Tu resultado aparecerá aquí cuando se publique.';
        } else if (t === null || (reloj && reloj.fase === 'antes')) {
            fase = 'Aún no parte';
            est = filas.length ? 'Primero: ' + filas[0].nombre : '';
            cuenta = t0 !== null && filas.length ? hora(t0 + filas[0].ini) : '';
        } else if (actual) {
            fase = actual.paciente ? 'Ahora eres' : 'Estás en';
            est = actual.nombre;
            cuenta = OsceReloj.mmss(actual.ini + dur - t);
        } else if (siguiente) {
            var falta = siguiente.ini - t;
            fase = falta <= pausa ? 'Cambio: dirígete a' : (t < filas[0].ini ? 'Espera tu turno en la sala' : 'Espera: lo próximo es');
            est = siguiente.nombre;
            cuenta = falta <= pausa ? OsceReloj.mmss(falta) : 'en ' + OsceReloj.mmss(falta);
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
