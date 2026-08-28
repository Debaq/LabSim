<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

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
    }
    $markCode = static fn (string $code) => Lti::markNonceCode($result['consumer_key'], $result['nonce'], $userId, $code);
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
    }
    $markCode = static fn (string $code) => Lti::markStateCode($state, $userId, $code);
    $refreshKey = 'state:' . $state;
}

$issued = Auth::codeForLaunch($userId, $previousCode);
if ($issued['renewed']) {
    $markCode($issued['code']);
}

$code = $issued['code'];
$expiresIn = Auth::secondsUntil($issued['expires_at']);

header('Content-Type: text/html; charset=utf-8');
?>
<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<title>LabSim</title>
<style>
    body { font-family: sans-serif; text-align: center; margin-top: 4rem; }
    .code { font-size: 3rem; font-weight: bold; letter-spacing: 0.3em; }
    .countdown.low { color: #c00; font-weight: bold; }
    button { font-size: 1rem; padding: 0.6rem 1.4rem; margin-top: 1.5rem; cursor: pointer; }
    .status { min-height: 1.2em; color: #555; }
</style>
</head>
<body>
    <h1>Ingreso correcto</h1>
    <p>Abre LabSim en tu computador y escribe este código para continuar:</p>
    <p class="code" id="code"><?= htmlspecialchars($code) ?></p>
    <p>Vence en <span id="countdown" class="countdown"><?= $expiresIn ?></span> segundos.</p>
    <button id="refresh" type="button">Generar código nuevo</button>
    <p class="status" id="status"></p>
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
