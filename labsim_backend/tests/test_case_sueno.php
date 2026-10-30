<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseForm.php';

/**
 * La tarjeta Sueño (ficha Nariz): el estudio de sueño viaja en el hidden
 * `sueno_json` y termina en cases.data['SUENO'], con las mismas reglas que
 * valida la app (nasal/sueno.normaliza). Vacío es "sin estudio"; un valor
 * fuera de rango bloquea el guardado diciendo cuál; reeditar el caso sin
 * tocar la ficha no lo pierde.
 */

final class SuenoFakeStmt
{
    public function fetchColumn()
    {
        return 41;
    }
}

final class SuenoFakePdo extends PDO
{
    public function __construct()
    {
    }

    #[\ReturnTypeWillChange]
    public function query(string $query, ?int $fetchMode = null, ...$args)
    {
        return new SuenoFakeStmt();
    }
}

$e = null;
foreach (['roncador', 'moderado', 'grave', 'dudosa'] as $perfil) {
    $r = CaseForm::parseSueno(json_encode(['perfil' => $perfil]), $e);
    t_eq($e, null, "Sueño: el perfil {$perfil} es válido");
    t_eq($r, ['perfil' => $perfil, 'params' => null, 'canula_suelta' => null, 'cpap' => null], "Sueño: {$perfil} no lleva params ni cánula");
}
t_eq(CaseForm::parseSueno('', $e), null, 'Sueño: vacío da null');
t_eq($e, null, 'Sueño: vacío no es error');

// Personalizado: los que faltan toman el default.
$r = CaseForm::parseSueno(json_encode(['perfil' => 'personalizado', 'params' => ['tasa' => 40, 'tib' => 420]]), $e);
t_eq($e, null, 'Sueño: personalizado válido');
t_eq(count($r['params']), 14, 'Sueño: personalizado trae los 14 parámetros');
t_eq([$r['params']['tasa'], $r['params']['tib'], $r['params']['rem'], $r['params']['spo2_basal']], [40, 420, 2.0, 95.5], 'Sueño: conserva lo dado y completa con el default');
$r = CaseForm::parseSueno(json_encode(['perfil' => 'personalizado']), $e);
t_eq($r['params']['semilla'], 1, 'Sueño: personalizado sin params usa los defaults');

// Rangos.
foreach ([['tasa', 121], ['rem', 0.1], ['supino', 5], ['caida_hipopnea', 2], ['spo2_basal', 80], ['tib', 299], ['semilla', 0]] as $par) {
    CaseForm::parseSueno(json_encode(['perfil' => 'personalizado', 'params' => [$par[0] => $par[1]]]), $e);
    t_true(strpos((string) $e, $par[0]) !== false, "Sueño: {$par[0]} fuera de rango avisa");
}
CaseForm::parseSueno(json_encode(['perfil' => 'personalizado', 'params' => ['tasa' => 'mucho']]), $e);
t_true(strpos((string) $e, 'número') !== false, 'Sueño: un parámetro que no es número avisa');
// Mezcla en cero.
$cero = ['obstructivas' => 0, 'mixtas' => 0, 'centrales' => 0, 'hipopneas' => 0, 'rera' => 0];
CaseForm::parseSueno(json_encode(['perfil' => 'personalizado', 'params' => $cero]), $e);
t_true(strpos((string) $e, 'suma cero') !== false, 'Sueño: la mezcla en cero avisa');
$r = CaseForm::parseSueno(json_encode(['perfil' => 'personalizado', 'params' => ['obstructivas' => 0, 'mixtas' => 0, 'centrales' => 0, 'hipopneas' => 0, 'rera' => 1]]), $e);
t_eq($e, null, 'Sueño: solo RERA es una mezcla válida');

// Cánula suelta.
$r = CaseForm::parseSueno(json_encode(['perfil' => 'dudosa', 'canula_suelta' => ['desde' => 120, 'hasta' => 200]]), $e);
t_eq($r['canula_suelta'], ['desde' => 120, 'hasta' => 200], 'Sueño: guarda la cánula suelta');
$r = CaseForm::parseSueno(json_encode(['perfil' => 'dudosa', 'canula_suelta' => null]), $e);
t_eq($r['canula_suelta'], null, 'Sueño: cánula null es sin cánula suelta');
CaseForm::parseSueno(json_encode(['perfil' => 'dudosa', 'canula_suelta' => ['desde' => 200, 'hasta' => 200]]), $e);
t_true(strpos((string) $e, 'canula_suelta.hasta') !== false, 'Sueño: hasta tiene que pasar de desde');
CaseForm::parseSueno(json_encode(['perfil' => 'dudosa', 'canula_suelta' => ['desde' => 601, 'hasta' => 602]]), $e);
t_true(strpos((string) $e, 'canula_suelta.desde') !== false, 'Sueño: desde sobre 600 avisa');
CaseForm::parseSueno(json_encode(['perfil' => 'dudosa', 'canula_suelta' => ['desde' => 10, 'hasta' => 700]]), $e);
t_true(strpos((string) $e, 'canula_suelta.hasta') !== false, 'Sueño: hasta sobre 601 avisa');
CaseForm::parseSueno(json_encode(['perfil' => 'dudosa', 'canula_suelta' => ['desde' => 10]]), $e);
t_true($e !== null, 'Sueño: cánula sin hasta avisa');

// Titulación de CPAP.
$r = CaseForm::parseSueno(json_encode(['perfil' => 'moderado']), $e);
t_eq($r['cpap'], null, 'Sueño: sin cpap da null');
$r = CaseForm::parseSueno(json_encode(['perfil' => 'moderado', 'cpap' => ['p_eficaz' => 11.5, 'supino' => 2, 'rem' => 1.5, 'boca' => true, 'talla' => 'L']]), $e);
t_eq($e, null, 'Sueño: cpap completo válido');
t_eq($r['cpap'], ['p_eficaz' => 11.5, 'supino' => 2, 'rem' => 1.5, 'boca' => true, 'talla' => 'L'], 'Sueño: conserva el cpap completo');
$r = CaseForm::parseSueno(json_encode(['perfil' => 'grave', 'cpap' => ['p_eficaz' => 14]]), $e);
t_eq($r['cpap'], ['p_eficaz' => 14], 'Sueño: cpap parcial conserva solo lo dado');
$r = CaseForm::parseSueno(json_encode(['perfil' => 'grave', 'cpap' => ['boca' => false]]), $e);
t_eq($r['cpap'], ['boca' => false], 'Sueño: boca falsa se conserva');
$r = CaseForm::parseSueno(json_encode(['perfil' => 'grave', 'cpap' => (object) []]), $e);
t_eq($r['cpap'], null, 'Sueño: cpap vacío es null');
$r = CaseForm::parseSueno(json_encode(['perfil' => 'grave', 'cpap' => ['talla' => 'XL']]), $e);
t_eq([$e, $r['cpap']], [null, null], 'Sueño: talla desconocida se ignora');
foreach ([['p_eficaz', 3], ['p_eficaz', 21], ['supino', 7], ['rem', -1]] as $par) {
    CaseForm::parseSueno(json_encode(['perfil' => 'grave', 'cpap' => [$par[0] => $par[1]]]), $e);
    t_true(strpos((string) $e, 'cpap.' . $par[0]) !== false, "Sueño: cpap.{$par[0]} fuera de rango avisa");
}
CaseForm::parseSueno(json_encode(['perfil' => 'grave', 'cpap' => ['p_eficaz' => 'alta']]), $e);
t_true(strpos((string) $e, 'número') !== false, 'Sueño: cpap.p_eficaz que no es número avisa');

// Perfil desconocido y JSON roto.
CaseForm::parseSueno(json_encode(['perfil' => 'inventado']), $e);
t_true(strpos((string) $e, 'perfil') !== false, 'Sueño: perfil desconocido avisa');
CaseForm::parseSueno('{roto', $e);
t_true(strpos((string) $e, 'JSON') !== false, 'Sueño: JSON roto avisa');

// El formulario entero y la ida y vuelta.
$pdo = new SuenoFakePdo();
$me = ['id' => 1, 'username' => 'admin'];
$base = ['age' => '35', 'nombre1' => 'Óscar', 'apellido1' => 'Cárdenas', 'acumetria_auto' => '1', 'perfil_confirmar' => '1'];
$bloque = ['perfil' => 'personalizado', 'params' => ['tasa' => 35.5, 'tib' => 450], 'canula_suelta' => ['desde' => 60, 'hasta' => 120]];
$form = CaseForm::fromPost($base + ['sueno_json' => json_encode($bloque)], $pdo, $me, null, false);
t_eq($form->error, null, 'POST con sueño no da error');
t_eq($form->data['SUENO']['params']['tasa'], 35.5, 'El POST deja data[SUENO]');
$sin = CaseForm::fromPost($base + ['sueno_json' => ''], $pdo, $me, null, false);
t_true(!array_key_exists('SUENO', $sin->data), 'Hidden vacío: el caso no trae SUENO');
$falla = CaseForm::fromPost($base + ['sueno_json' => json_encode(['perfil' => 'personalizado', 'params' => ['tasa' => 500]])], $pdo, $me, null, false);
t_true(strpos((string) $falla->error, 'Sueño') !== false, 'Un valor inválido de sueño bloquea el guardado');
$vuelta = CaseBuilder::caseDataToForm($form->data);
t_true(($vuelta['sueno_json'] ?? '') !== '', 'Al reabrir el caso, el hidden viene cargado');
$otra = CaseForm::fromPost($base + ['sueno_json' => $vuelta['sueno_json']], $pdo, $me, null, false);
t_eq($otra->data['SUENO'], $form->data['SUENO'], 'Reeditar sin tocar la ficha no cambia SUENO');

// Ida y vuelta con la parte cpap.
$bloqueC = ['perfil' => 'moderado', 'params' => null, 'canula_suelta' => null, 'cpap' => ['p_eficaz' => 12, 'boca' => true, 'talla' => 'S']];
$fc = CaseForm::fromPost($base + ['sueno_json' => json_encode($bloqueC)], $pdo, $me, null, false);
t_eq($fc->error, null, 'POST con cpap no da error');
t_eq($fc->data['SUENO']['cpap'], ['p_eficaz' => 12, 'boca' => true, 'talla' => 'S'], 'El POST deja el cpap en data[SUENO]');
$vc = CaseBuilder::caseDataToForm($fc->data);
$oc = CaseForm::fromPost($base + ['sueno_json' => $vc['sueno_json']], $pdo, $me, null, false);
t_eq($oc->data['SUENO'], $fc->data['SUENO'], 'Reeditar sin tocar no cambia el cpap');
