<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/CaseProfile.php';

/**
 * Proyección del perfil auditivo para la vista previa en vivo del creador
 * de casos -- fetch(), no <form>, por eso devuelve JSON.
 *
 * Existe para que el formulario no tenga que reimplementar las leyes en
 * JavaScript. Sin esto, el docente cambiaba el audiograma o sorteaba un
 * caso y la OEA, los reflejos y las supraliminares seguían mostrando los
 * valores viejos hasta guardar y volver a abrir: no había forma de saber
 * qué iba a quedar guardado. Duplicar las fórmulas en JS era la otra
 * opción, y se separan de la de PHP el primer día que alguien toca una.
 *
 * No toca la base: es una función pura sobre lo que viene en el POST (ver
 * CaseProfile::project). No guarda nada, así que tampoco audita.
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

/** [od0,od1,...] + [oi0,oi1,...] -> [[od0,oi0],...], el shape de cases.data. */
$pares = static function ($od, $oi): array {
    $out = [];
    foreach (CaseBuilder::FREQUENCIES as $n => $_) {
        $out[] = [(float) (is_array($od) ? ($od[$n] ?? 0) : 0),
                  (float) (is_array($oi) ? ($oi[$n] ?? 0) : 0)];
    }
    return $out;
};

$airPairs = $pares($payload['aerea']['od'] ?? [], $payload['aerea']['oi'] ?? []);
$bonePairs = $pares($payload['osea']['od'] ?? [], $payload['osea']['oi'] ?? []);

// El perfil llega del formulario, no de la base: es justamente el estado
// que todavía no se guardó. normalizeRetro() rellena lo que falte con los
// defaults que comparte con el generador.
$perfil = ['version' => CaseProfile::VERSION];
foreach (CaseBuilder::LADOS as $ladoForm => $lado) {
    $cce = $payload['perfil'][$ladoForm]['cce_pct'] ?? CaseProfile::DEFAULT_CCE_PCT;
    $perfil[$lado] = [
        'cce_pct' => max(0.0, min(100.0, (float) $cce)),
        'retro' => CaseProfile::normalizeRetro(
            is_array($payload['perfil'][$ladoForm]['retro'] ?? null)
                ? $payload['perfil'][$ladoForm]['retro'] : []
        ),
    ];
}
$perfil['auto'] = [];
foreach (CaseProfile::AUTO_MODULES as $modulo) {
    $perfil['auto'][$modulo] = !empty($payload['auto'][$modulo]);
}

$tymp = [
    'OD' => in_array($payload['z']['od'] ?? 'A', CaseBuilder::Z_OPTIONS, true) ? (string) $payload['z']['od'] : 'A',
    'OI' => in_array($payload['z']['oi'] ?? 'A', CaseBuilder::Z_OPTIONS, true) ? (string) $payload['z']['oi'] : 'A',
];

// Edad: decide el transitorio de las primeras horas y la calibración ósea
// del lactante (ver CaseProfile). La vista previa tiene que mostrar lo
// mismo que se va a guardar.
$edadAnios = max(0, (int) ($_POST['age'] ?? 0));
$horasVida = null;
$valorEdad = $_POST['edad_valor'] ?? '';
if ($edadAnios === 0 && $valorEdad !== '' && is_numeric($valorEdad)) {
    $factor = ['horas' => 1, 'dias' => 24, 'meses' => 720];
    $unidad = (string) ($_POST['edad_unidad'] ?? 'horas');
    $horasVida = max(0, min((int) round((float) $valorEdad * ($factor[$unidad] ?? 1)), 8760));
}
$edadMeses = $horasVida !== null ? $horasVida / 720.0 : $edadAnios * 12.0;

$proyeccion = CaseProfile::project($airPairs, $bonePairs, $perfil, $tymp, $horasVida, $edadMeses);

// La descomposición es un detalle interno (nueve frecuencias por seis
// curvas por oído): no la necesita el navegador y solo engorda la respuesta.
unset($proyeccion['decomp']);

echo json_encode(['ok' => true, 'proyeccion' => $proyeccion], JSON_UNESCAPED_UNICODE);
