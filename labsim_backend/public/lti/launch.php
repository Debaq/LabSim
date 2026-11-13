<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Metrics.php';
require_once __DIR__ . '/../../src/AudiometriaTecnica.php';
require_once __DIR__ . '/../../src/AudiometriaTecnicaGrafico.php';

/**
 * Un JSON crudo de error acá lo ve el alumno en el navegador (esta página
 * la abre el iframe de Moodle o una pestaña nueva, no una app que interprete
 * el JSON) -- muestra una página legible en su lugar, con la acción que
 * puede tomar.
 */
function render_launch_error(string $message): void
{
    header('Content-Type: text/html; charset=utf-8');
    ?>
    <!doctype html>
    <html lang="es">
    <head><meta charset="utf-8"><title>LabSim</title></head>
    <body style="font-family: sans-serif; text-align: center; margin-top: 4rem;">
        <h1>No se pudo generar el código</h1>
        <p><?= htmlspecialchars($message) ?></p>
        <p>Vuelve a abrir la actividad desde la plataforma para intentarlo de nuevo.</p>
    </body>
    </html>
    <?php
    exit;
}

// LTI 1.1 llega como un solo POST directo (firmado OAuth1), sin pasar por
// login.php; LTI 1.3 llega vía el redirect OIDC (id_token + state).
// platformId/contextId solo se llenan en un launch no-replay (recién ahí hay
// claims/params confiables) -- ver Lti::autoEnrollIfMapped/findCourseForContext.
$platformId = null;
$contextId = null;

if (isset($_POST['oauth_consumer_key'])) {
    try {
        $result = Lti::validateLaunch11($_POST);
    } catch (RuntimeException $e) {
        render_launch_error('Launch LTI 1.1 inválido: ' . $e->getMessage());
    }
    if ($result['replay'] ?? false) {
        $userId = $result['user_id'];
        $previousCode = $result['issued_code'];
    } else {
        $userId = Lti::upsertStudentFromLti11($result['platform'], $result['params']);
        $previousCode = null;
        $platformId = (int) $result['platform']['id'];
        $contextId = $result['params']['context_id'] ?? null;
        $contextLabel = $result['params']['context_title'] ?? ($result['params']['context_label'] ?? null);
        Lti::autoEnrollIfMapped($platformId, $contextId, $userId);
        Lti::recordContextSighting($userId, $platformId, $contextId, $contextLabel);
    }
    $markCode = static fn (string $code) => Lti::markNonceCode($result['consumer_key'], $result['nonce'], $userId, $code, $contextId);
    $refreshKey = 'nonce:' . $result['consumer_key'] . '|' . $result['nonce'];
} else {
    $idToken = $_POST['id_token'] ?? '';
    $state = $_POST['state'] ?? '';

    if ($idToken === '' || $state === '') {
        render_launch_error('Launch LTI incompleto.');
    }

    try {
        $result = Lti::validateLaunch($idToken, $state);
    } catch (RuntimeException $e) {
        render_launch_error('Launch LTI 1.3 inválido: ' . $e->getMessage());
    }
    if ($result['replay'] ?? false) {
        $userId = $result['user_id'];
        $previousCode = $result['issued_code'];
    } else {
        $userId = Lti::upsertStudent($result['platform'], $result['claims']);
        $previousCode = null;
        $platformId = (int) $result['platform']['id'];
        $contextClaim = $result['claims']['https://purl.imsglobal.org/spec/lti/claim/context'] ?? [];
        $contextId = $contextClaim['id'] ?? null;
        $contextLabel = $contextClaim['title'] ?? ($contextClaim['label'] ?? null);
        Lti::autoEnrollIfMapped($platformId, $contextId, $userId);
        Lti::recordContextSighting($userId, $platformId, $contextId, $contextLabel);
    }
    $markCode = static fn (string $code) => Lti::markStateCode($state, $userId, $code, $contextId);
    $refreshKey = 'state:' . $state;
}

$issued = Auth::codeForLaunch($userId, $previousCode, $platformId, $contextId);
if ($issued['renewed']) {
    $markCode($issued['code']);
}

$code = $issued['code'];
$expiresIn = Auth::secondsUntil($issued['expires_at']);

// Docente/admin promovido a mano desde el panel (ver admin/users.php) --
// LTI siempre crea la cuenta como role='student', así que esto solo es
// true si un admin ya lo ascendió antes de este launch. Se abre sesión de
// portal acá mismo porque el launch LTI ya autenticó al usuario; no tiene
// contraseña de portal para hacer login normal.
$stmt = Db::get()->prepare("SELECT role, active FROM users WHERE id = ?");
$stmt->execute([$userId]);
$userRow = $stmt->fetch();
$isPortalUser = $userRow && $userRow['role'] === 'admin' && (int) $userRow['active'] === 1;
// launch.php corre dentro del iframe de Moodle -- cookie de tercero, no
// sirve para levantar la sesión de portal ahí mismo (varios navegadores la
// descartan). El botón manda a admin/sso.php, que canjea este token de un
// solo uso en una pestaña nueva (primer partido) y ahí sí levanta la sesión.
// Si este launch todavía no resuelve a ningún curso de LabSim --ni por el
// contexto de Moodle ni por el curso por defecto de la clave-- se manda al
// docente/admin directo a courses.php con el contexto en la URL para que lo
// vincule ahí (una vez) -- ver comentario de course_lti_contexts en
// schema.sql y el bloque "link_lti_context" en admin/courses.php. Una clave
// creada para un curso no pasa por acá: ya matricula sola.
$needsLtiLink = $isPortalUser && $platformId !== null && $contextId !== null
    && Lti::courseForLaunch($platformId, $contextId) === null;
$portalUrl = $isPortalUser
    ? '../admin/sso.php?token=' . urlencode(Auth::issuePortalSsoToken($userId))
        . ($needsLtiLink ? '&link_platform=' . $platformId . '&link_context=' . urlencode($contextId) : '')
    : null;

// Mini-portal de alumno (lista de pacientes atendidos + detalle: stats,
// conversación con comentarios del docente, ficha clínica) -- mismo
// mecanismo de handoff que $portalUrl arriba (token de un solo uso, ver
// student/sso.php), pero para role='student' en vez de admin/docente.
$misPacientesUrl = !$isPortalUser
    ? '../student/sso.php?token=' . urlencode(Auth::issuePortalSsoToken($userId))
    : null;

// Stats embebidas en la misma pantalla del código, solo para el alumno. El
// docente no tiene resumen acá: para eso entra a la plataforma (el botón de
// abajo). Antes se cargaba action_logs entero para armarle uno y, al pasar
// las 180 mil filas, el hosting respondía 503 en el iframe de Moodle.
if (!$isPortalUser) {
    $stmt = Db::get()->prepare('SELECT * FROM action_logs WHERE user_id = ? ORDER BY id');
    $stmt->execute([$userId]);
    $myLogs = Metrics::decodeLogs($stmt->fetchAll());
    $mySessions = Metrics::buildSessions($myLogs);
    $mySummary = Metrics::summarizeSessions($mySessions);
    // Los intentos de práctica libre se cuentan aparte, como en Mis
    // pacientes: si no, acá decía 5 atendidos y allá "3 + 2 de práctica".
    $citasPractica = [];
    if (Practica::listo()) {
        $stmt = Db::get()->prepare('SELECT id FROM appointments WHERE assigned_student_id = ? AND ' . Practica::soloPractica());
        $stmt->execute([$userId]);
        $citasPractica = array_fill_keys(array_map('intval', array_column($stmt->fetchAll(), 'id')), true);
    }
    $esPractica = static function (array $log) use ($citasPractica): bool {
        return isset($citasPractica[(int) ($log['appointment_id'] ?? 0)]);
    };
    $myPracticas = Metrics::countAttentions(array_filter($myLogs, $esPractica));
    // Cuántos casos del libro lleva (lo mismo que ve arriba de las carpetas
    // en la práctica libre de la app).
    $avanceLibro = Practica::avance((int) $userId);
    $myAttentions = Metrics::countAttentions(array_filter($myLogs, static function (array $l) use ($esPractica): bool {
        return !$esPractica($l);
    }));

    // Última atención: el logro de su técnica de audiometría en gráficos sin
    // palabras (ver AudiometriaTecnicaGrafico). Antes iba la franja de acciones del
    // dashboard docente, que al alumno no le decía nada.
    $lastAttentionKey = null;
    $lastAttentionEnd = null;
    foreach ($mySessions as $s) {
        if (!$s['con_paciente']) {
            continue;
        }
        if ($lastAttentionEnd === null || $s['end'] > $lastAttentionEnd) {
            $lastAttentionEnd = $s['end'];
            $lastAttentionKey = ['appointment_id' => $s['appointment_id'], 'case_id' => $s['case_id']];
        }
    }
    $lastAttentionAppt = null;
    $lastTecnica = null;
    if ($lastAttentionKey !== null) {
        if ($lastAttentionKey['appointment_id'] !== null) {
            $stmt = Db::get()->prepare('SELECT nombre, apellido, procedimiento FROM appointments WHERE id = ?');
            $stmt->execute([(int) $lastAttentionKey['appointment_id']]);
            $lastAttentionAppt = $stmt->fetch() ?: null;
            // Pasos de la técnica de audiometría, solo con la atención ya
            // cerrada (igual que student/atencion.php, donde está el detalle).
            $stmt = Db::get()->prepare("SELECT 1 FROM attendances WHERE appointment_id = ? AND student_id = ? AND estado = 'atendido'");
            $stmt->execute([(int) $lastAttentionKey['appointment_id'], $userId]);
            if ($stmt->fetchColumn()) {
                $lastTecnica = AudiometriaTecnica::paraAtencion((int) $lastAttentionKey['appointment_id'], (int) $userId, $myLogs);
            }
        }
    }
    // El logro de todas sus audiometrías cerradas, en orden (práctica libre
    // incluida, como en Mis pacientes): la curva marca dónde cae la última.
    $logroSerie = [];
    $logroActual = null;
    if ($lastTecnica !== null) {
        $stmt = Db::get()->prepare("SELECT appointment_id FROM attendances WHERE student_id = ? AND estado = 'atendido' ORDER BY updated_at");
        $stmt->execute([$userId]);
        $citas = array_map('intval', array_column($stmt->fetchAll(), 'appointment_id'));
        $tecnicas = AudiometriaTecnica::deAtenciones((int) $userId, $citas, $myLogs);
        foreach ($citas as $ap) {
            $pct = $tecnicas[$ap]['puntaje']['pct'] ?? null;
            if ($pct !== null) {
                if ($ap === (int) $lastAttentionKey['appointment_id']) {
                    $logroActual = count($logroSerie);
                }
                $logroSerie[] = (int) $pct;
            }
        }
    }
}

header('Content-Type: text/html; charset=utf-8');
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>LabSim</title>
<style>
    * { box-sizing: border-box; }
    body { font-family: sans-serif; text-align: center; margin: 4rem 1rem 2rem; overflow-x: hidden; }
    .code { font-size: clamp(1.8rem, 10vw, 3rem); font-weight: bold; letter-spacing: 0.3em; }
    .countdown.low { color: #c00; font-weight: bold; }
    button { font-size: 1rem; padding: 0.6rem 1.4rem; margin-top: 1.5rem; cursor: pointer; }
    .status { min-height: 1.2em; color: #555; }
    .stats { margin-top: 2.5rem; text-align: left; max-width: 560px; margin-left: auto; margin-right: auto; }
    .stats h2 { font-size: 1.1rem; text-align: center; }
    .stats-summary { text-align: center; color: #555; font-size: 0.9rem; }
    .last-attention { margin-top: 1.8rem; }
    .last-attention h3 { font-size: 1rem; margin-bottom: 0.2rem; text-align: center; }
    .tecnica-logro { display: flex; justify-content: center; align-items: center; gap: 1.2rem; margin-top: 0.8rem; flex-wrap: wrap; }
    .tecnica-anillo { width: 96px; height: 96px; flex-shrink: 0; }
    .tecnica-evolucion { width: 260px; max-width: 100%; height: auto; border-radius: 4px; }
    .tecnica-pasos { display: block; max-width: 100%; height: 34px; margin: 0.8rem auto 0; }
    .avance-libro { margin-top: 1.8rem; }
    .avance-libro h3 { font-size: 1rem; margin-bottom: 0.4rem; text-align: center; }
    .avance-barra { height: 8px; border-radius: 4px; background: #ece6ec; overflow: hidden; margin: 0.4rem 0 0.6rem; }
    .avance-barra span { display: block; height: 100%; background: #5d1049; }
    .avance-libro details { font-size: 0.9rem; }
    .avance-libro summary { cursor: pointer; text-align: center; color: #555; }
    .avance-carpetas { list-style: none; padding: 0; margin: 0.6rem 0 0; }
    .avance-carpetas li { display: flex; justify-content: space-between; gap: 1rem; padding: 0.25rem 0; border-bottom: 1px solid #eee; }
    .avance-carpetas .listo { color: #2e7d4f; font-weight: bold; }

    @media (max-width: 30rem) {
        body { margin-top: 2rem; }
    }
</style>
</head>
<body>
    <h1>Ingreso correcto</h1>
    <p>Abre LabSim en tu computador y escribe este código para continuar:</p>
    <p class="code" id="code"><?= htmlspecialchars($code) ?></p>
    <p>Vence en <span id="countdown" class="countdown"><?= $expiresIn ?></span> segundos.</p>
    <button id="refresh" type="button">Generar código nuevo</button>
    <?php if ($isPortalUser): ?>
        <a href="<?= htmlspecialchars($portalUrl) ?>" target="_blank" rel="noopener"><button type="button">Ir a plataforma</button></a>
        <?php if ($needsLtiLink): ?>
            <p class="status">Este curso de Moodle aún no está vinculado a un curso de LabSim -- en la plataforma te pediremos vincularlo (una sola vez).</p>
        <?php endif; ?>
    <?php elseif ($misPacientesUrl !== null): ?>
        <a href="<?= htmlspecialchars($misPacientesUrl) ?>" target="_blank" rel="noopener"><button type="button">Ver mis pacientes</button></a>
    <?php endif; ?>
    <p class="status" id="status"></p>

    <div class="stats">
        <?php if (!$isPortalUser && $myAttentions + $myPracticas > 0): ?>
            <h2>Tu actividad</h2>
            <p class="stats-summary">
                <?= $myAttentions ?> paciente<?= $myAttentions === 1 ? '' : 's' ?> atendido<?= $myAttentions === 1 ? '' : 's' ?><?= $myPracticas ? ' (+ ' . $myPracticas . ' de práctica libre)' : '' ?> · <?= (int) round($mySummary['total_duration_s'] / 60) ?> min en total
            </p>

            <?php if ($lastAttentionKey !== null): ?>
            <div class="last-attention">
                <h3>Tu última atención</h3>
                <p class="stats-summary">
                    <?php if ($lastAttentionAppt): ?>
                        <?= htmlspecialchars(trim($lastAttentionAppt['nombre'] . ' ' . $lastAttentionAppt['apellido'])) ?: 'Paciente' ?>
                        · <?= htmlspecialchars($lastAttentionAppt['procedimiento'] ?: '—') ?>
                    <?php else: ?>
                        Caso <?= htmlspecialchars((string) ($lastAttentionKey['case_id'] ?? '—')) ?>
                    <?php endif; ?>
                </p>
                <?php if ($lastTecnica !== null): ?>
                <div class="tecnica-logro">
                    <?= AudiometriaTecnicaGrafico::anillo($lastTecnica['puntaje']['pct'] ?? null) ?>
                    <?= $logroActual !== null ? AudiometriaTecnicaGrafico::evolucion($logroSerie, $logroActual) : '' ?>
                </div>
                <?= AudiometriaTecnicaGrafico::pasos($lastTecnica) ?>
                <?php endif; ?>
            </div>
            <?php endif; ?>
        <?php endif; ?>

        <?php if (!$isPortalUser && $avanceLibro['casos'] > 0):
            $terminadas = count(array_filter($avanceLibro['carpetas'], static function (array $c): bool {
                return $c['hechos'] === $c['casos'];
            }));
            $pct = (int) round(100 * $avanceLibro['hechos'] / $avanceLibro['casos']); ?>
        <div class="avance-libro">
            <h3>Tu avance en el libro</h3>
            <p class="stats-summary">
                <?= $avanceLibro['hechos'] ?> de <?= $avanceLibro['casos'] ?> casos practicados
                · <?= $terminadas ?> de <?= count($avanceLibro['carpetas']) ?> capítulos completos
            </p>
            <div class="avance-barra" role="progressbar" aria-valuemin="0" aria-valuemax="<?= $avanceLibro['casos'] ?>"
                 aria-valuenow="<?= $avanceLibro['hechos'] ?>"><span style="width: <?= $pct ?>%"></span></div>
            <details>
                <summary>Ver por capítulo</summary>
                <ul class="avance-carpetas">
                    <?php foreach ($avanceLibro['carpetas'] as $c): ?>
                    <li>
                        <span><?= htmlspecialchars($c['nombre']) ?></span>
                        <span class="<?= $c['hechos'] === $c['casos'] ? 'listo' : '' ?>"><?= $c['hechos'] ?>/<?= $c['casos'] ?><?= $c['hechos'] === $c['casos'] ? ' ✓' : '' ?></span>
                    </li>
                    <?php endforeach; ?>
                </ul>
            </details>
        </div>
        <?php endif; ?>
    </div>

    <script>
    (function () {
        var KEY = <?= json_encode($refreshKey) ?>;
        var remaining = <?= $expiresIn ?>;
        var codeEl = document.getElementById('code');
        var countdownEl = document.getElementById('countdown');
        var statusEl = document.getElementById('status');
        var btn = document.getElementById('refresh');
        var busy = false;

        function renew() {
            if (busy) { return; }
            busy = true;
            statusEl.textContent = 'Generando código nuevo...';
            fetch('refresh_code.php', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: KEY })
            }).then(function (r) {
                if (!r.ok) { return r.json().then(function (d) { throw new Error(d.error || ('http ' + r.status)); }); }
                return r.json();
            }).then(function (data) {
                codeEl.textContent = data.code;
                remaining = data.expires_in;
                countdownEl.textContent = remaining;
                countdownEl.className = 'countdown';
                statusEl.textContent = '';
            }).catch(function (err) {
                statusEl.textContent = err.message || 'No se pudo generar un código nuevo. Vuelve a abrir la actividad desde la plataforma.';
            }).finally(function () {
                busy = false;
            });
        }

        setInterval(function () {
            remaining -= 1;
            if (remaining <= 0) {
                countdownEl.textContent = '0';
                renew();
                return;
            }
            countdownEl.textContent = remaining;
            countdownEl.className = remaining <= 30 ? 'countdown low' : 'countdown';
        }, 1000);

        btn.addEventListener('click', renew);
    })();
    </script>
</body>
</html>
