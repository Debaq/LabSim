<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

// LTI 1.1 llega como un solo POST directo (firmado OAuth1), sin pasar por
// login.php; LTI 1.3 llega vía el redirect OIDC (id_token + state).
if (isset($_POST['oauth_consumer_key'])) {
    try {
        $result = Lti::validateLaunch11($_POST);
    } catch (RuntimeException $e) {
        Response::error('Launch LTI 1.1 inválido: ' . $e->getMessage(), 400);
    }
    $userId = Lti::upsertStudentFromLti11($result['platform'], $result['params']);
} else {
    $idToken = $_POST['id_token'] ?? '';
    $state = $_POST['state'] ?? '';

    if ($idToken === '' || $state === '') {
        Response::error('Launch LTI incompleto', 400);
    }

    try {
        $result = Lti::validateLaunch($idToken, $state);
    } catch (RuntimeException $e) {
        Response::error('Launch LTI 1.3 inválido: ' . $e->getMessage(), 400);
    }
    $userId = Lti::upsertStudent($result['platform'], $result['claims']);
}

$code = Auth::createPairingCode($userId);

header('Content-Type: text/html; charset=utf-8');
?>
<!doctype html>
<html lang="es">
<head><meta charset="utf-8"><title>LabSim</title></head>
<body style="font-family: sans-serif; text-align: center; margin-top: 4rem;">
    <h1>Ingreso correcto</h1>
    <p>Abre LabSim en tu computador y escribe este código para continuar:</p>
    <p style="font-size: 3rem; font-weight: bold; letter-spacing: 0.3em;"><?= htmlspecialchars($code) ?></p>
    <p>El código vence en unos minutos.</p>
</body>
</html>
