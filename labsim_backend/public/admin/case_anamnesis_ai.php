<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/AnamnesisDraft.php';
require_once __DIR__ . '/../../src/AdminAudit.php';

/**
 * Borrador de anamnesis escrito por el LLM, para el creador de casos --
 * fetch(), no <form>, por eso devuelve JSON.
 *
 * Trabaja sobre lo que está cargado en el formulario AHORA, no sobre lo
 * guardado: la anamnesis se escribe mientras se arma el caso, antes de que
 * exista en la base.
 *
 * Devuelve un BORRADOR. No lo guarda ni lo da por bueno: el docente tiene
 * que leerlo y verificarlo, y hasta que lo haga el caso no se guarda ni se
 * cita (ver CaseCompleteness). Acá solo se audita que se pidió.
 */

header('Content-Type: application/json; charset=utf-8');

$me = Auth::requireAdminSession();

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Método no permitido.']);
    exit;
}

try {
    Auth::requireCsrf();
} catch (Throwable $e) {
    http_response_code(403);
    echo json_encode(['ok' => false, 'error' => 'Sesión expirada, recarga la página.']);
    exit;
}

$payload = json_decode((string) ($_POST['payload'] ?? ''), true);
if (!is_array($payload)) {
    http_response_code(422);
    echo json_encode(['ok' => false, 'error' => 'Payload inválido.']);
    exit;
}

/** [od0,...] + [oi0,...] -> [[od0,oi0],...], el shape de cases.data. */
$pares = static function ($od, $oi): array {
    $out = [];
    foreach (CaseBuilder::FREQUENCIES as $n => $_) {
        $out[] = [(float) (is_array($od) ? ($od[$n] ?? 0) : 0),
                  (float) (is_array($oi) ? ($oi[$n] ?? 0) : 0)];
    }
    return $out;
};

// Solo lo que describeCase() mira: el resto de la ficha no entra al prompt.
$data = [
    'edad' => max(0, (int) ($payload['edad'] ?? 0)),
    'gender' => ((int) ($payload['gender'] ?? 0)) === 1 ? 1 : 0,
    'Aerea' => $pares($payload['aerea']['od'] ?? [], $payload['aerea']['oi'] ?? []),
    'Osea' => $pares($payload['osea']['od'] ?? [], $payload['osea']['oi'] ?? []),
    'Z_OD' => in_array($payload['z']['od'] ?? 'A', CaseBuilder::Z_OPTIONS, true) ? (string) $payload['z']['od'] : 'A',
    'Z_OI' => in_array($payload['z']['oi'] ?? 'A', CaseBuilder::Z_OPTIONS, true) ? (string) $payload['z']['oi'] : 'A',
    'Tinnitus' => is_array($payload['tinnitus'] ?? null) ? $payload['tinnitus'] : [],
    'Perfil' => [
        'version' => CaseProfile::VERSION,
        'OD' => [
            'cce_pct' => (float) ($payload['perfil']['od']['cce_pct'] ?? CaseProfile::DEFAULT_CCE_PCT),
            'retro' => CaseProfile::normalizeRetro(
                is_array($payload['perfil']['od']['retro'] ?? null) ? $payload['perfil']['od']['retro'] : []
            ),
        ],
        'OI' => [
            'cce_pct' => (float) ($payload['perfil']['oi']['cce_pct'] ?? CaseProfile::DEFAULT_CCE_PCT),
            'retro' => CaseProfile::normalizeRetro(
                is_array($payload['perfil']['oi']['retro'] ?? null) ? $payload['perfil']['oi']['retro'] : []
            ),
        ],
    ],
];

if ($data['edad'] <= 0) {
    http_response_code(422);
    echo json_encode(['ok' => false, 'error' => 'Falta la edad del paciente (pestaña Paciente): la anamnesis depende de ella.']);
    exit;
}

try {
    $borrador = AnamnesisDraft::generate($data);
} catch (Throwable $e) {
    http_response_code(502);
    echo json_encode(['ok' => false, 'error' => $e->getMessage()], JSON_UNESCAPED_UNICODE);
    exit;
}

AdminAudit::log($me, 'anamnesis_ai_draft', [
    'case_id' => (string) ($payload['case_id'] ?? ''),
    'edad' => $data['edad'],
]);

echo json_encode(['ok' => true, 'borrador' => $borrador], JSON_UNESCAPED_UNICODE);
