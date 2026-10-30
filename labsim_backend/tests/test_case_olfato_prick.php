<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseForm.php';

/**
 * Las tarjetas Olfato y Prick (ficha Nariz): la olfatometría y el prick test
 * viajan en los hidden `olfato_json` y `prick_json` y terminan en
 * cases.data['OLFATO'] / ['PRICK'], con los mismos rangos que valida la app
 * (nasal/olfatometria.normaliza y nasal/prick.normaliza). Vacío es "sin ese
 * examen"; un valor fuera de rango bloquea el guardado diciendo cuál;
 * reeditar el caso sin tocar la ficha no lo pierde.
 */

final class OlfPrickFakeStmt
{
    public function fetchColumn()
    {
        return 41;
    }
}

final class OlfPrickFakePdo extends PDO
{
    public function __construct()
    {
    }

    #[\ReturnTypeWillChange]
    public function query(string $query, ?int $fetchMode = null, ...$args)
    {
        return new OlfPrickFakeStmt();
    }
}

// --- Olfato ---
$olNorm = ['lados' => ['D' => ['T' => 10, 'D' => 13, 'I' => 14], 'I' => ['T' => 3.5, 'D' => 7, 'I' => 6]],
           'conducta' => 'distraida', 'preparacion' => 'fumo'];
$olE = null;
$olOk = CaseForm::parseOlfato(json_encode($olNorm), $olE);
t_eq($olE, null, 'Olfato: el caso válido no da error');
t_eq($olOk['lados']['I'], ['T' => 3.5, 'D' => 7, 'I' => 6], 'Olfato: conserva los puntajes de cada narina');
t_eq([$olOk['conducta'], $olOk['preparacion']], ['distraida', 'fumo'], 'Olfato: conserva conducta y preparación');
t_eq(CaseForm::parseOlfato('', $olE), null, 'Olfato: vacío da null');
t_eq($olE, null, 'Olfato: vacío no es error');

$olRara = $olNorm;
$olRara['conducta'] = 'rara';
unset($olRara['preparacion']);
$olR = CaseForm::parseOlfato(json_encode($olRara), $olE);
t_eq([$olR['conducta'], $olR['preparacion']], ['buena', 'ok'], 'Olfato: conducta desconocida cae en buena y sin preparación en ok');

$olMal = $olNorm;
$olMal['lados']['D']['T'] = 0;
CaseForm::parseOlfato(json_encode($olMal), $olE);
t_true(strpos((string) $olE, '"T"') !== false && strpos((string) $olE, 'entre 1 y 16') !== false, 'Olfato: T en 0 avisa (el piso es 1)');
$olMal = $olNorm;
$olMal['lados']['I']['D'] = 17;
CaseForm::parseOlfato(json_encode($olMal), $olE);
t_true(strpos((string) $olE, 'izquierda') !== false, 'Olfato: D sobre 16 dice de qué narina');
$olMal = $olNorm;
$olMal['lados']['D']['I'] = 0;
t_eq(CaseForm::parseOlfato(json_encode($olMal), $olE)['lados']['D']['I'], 0, 'Olfato: I en 0 es válido');
unset($olMal['lados']['I']);
CaseForm::parseOlfato(json_encode($olMal), $olE);
t_true(strpos((string) $olE, 'izquierda') !== false, 'Olfato: falta una narina');
CaseForm::parseOlfato('{roto', $olE);
t_true(strpos((string) $olE, 'JSON') !== false, 'Olfato: JSON roto avisa');

// --- Prick ---
$prH29 = ['histamina' => 6, 'dermografismo' => 0,
          'alergenos' => ['dpte' => 8, 'dfar' => 6, 'gato' => 3, 'perro' => 2, 'pastos' => 5, 'alternaria' => 0],
          'farmaco' => null];
$prE = null;
$prOk = CaseForm::parsePrick(json_encode($prH29), $prE);
t_eq($prE, null, 'Prick: el ejemplo de H29 es válido');
t_eq($prOk['alergenos']['dpte'], 8, 'Prick: conserva la pápula de cada alérgeno');
t_eq(count($prOk['alergenos']), 18, 'Prick: completa los alérgenos que faltan con 0');
t_eq($prOk['alergenos']['olivo'], 0, 'Prick: un alérgeno sin dato vale 0');
t_eq($prOk['farmaco'], null, 'Prick: sin fármaco, null');
t_eq(CaseForm::parsePrick('', $prE), null, 'Prick: vacío da null');
t_eq($prE, null, 'Prick: vacío no es error');

$prFar = $prH29;
$prFar['farmaco'] = ['clave' => 'cetirizina', 'horas' => 24];
$prF = CaseForm::parsePrick(json_encode($prFar), $prE);
t_eq($prF['farmaco'], ['clave' => 'cetirizina', 'horas' => 24], 'Prick: guarda el fármaco');
$prFar['farmaco'] = ['clave' => 'inventado', 'horas' => 24];
t_eq(CaseForm::parsePrick(json_encode($prFar), $prE)['farmaco'], null, 'Prick: un fármaco desconocido se descarta');
$prFar['farmaco'] = ['clave' => 'cetirizina', 'horas' => 2000];
CaseForm::parsePrick(json_encode($prFar), $prE);
t_true(strpos((string) $prE, 'Cetirizina') !== false && strpos((string) $prE, '1440') !== false, 'Prick: horas fuera de rango dice cuál fármaco');

$prMal = $prH29;
$prMal['histamina'] = 20;
CaseForm::parsePrick(json_encode($prMal), $prE);
t_true(strpos((string) $prE, 'Histamina') !== false, 'Prick: histamina fuera de rango dice cuál');
$prMal = $prH29;
$prMal['alergenos']['gato'] = 30;
CaseForm::parsePrick(json_encode($prMal), $prE);
t_true(strpos((string) $prE, 'Gato') !== false, 'Prick: un alérgeno fuera de rango dice cuál');
$prMal = $prH29;
$prMal['dermografismo'] = 9;
CaseForm::parsePrick(json_encode($prMal), $prE);
t_true(strpos((string) $prE, 'Dermografismo') !== false, 'Prick: dermografismo fuera de rango avisa');
CaseForm::parsePrick(json_encode(['alergenos' => []]), $prE);
t_true(strpos((string) $prE, 'Histamina') !== false, 'Prick: sin histamina avisa');
CaseForm::parsePrick('{roto', $prE);
t_true(strpos((string) $prE, 'JSON') !== false, 'Prick: JSON roto avisa');

// --- El formulario entero y la ida y vuelta ---
$pdo = new OlfPrickFakePdo();
$me = ['id' => 1, 'username' => 'admin'];
$base = ['age' => '35', 'nombre1' => 'Óscar', 'apellido1' => 'Cárdenas', 'acumetria_auto' => '1', 'perfil_confirmar' => '1'];
$form = CaseForm::fromPost($base + ['olfato_json' => json_encode($olNorm), 'prick_json' => json_encode($prH29)], $pdo, $me, null, false);
t_eq($form->error, null, 'POST con olfato y prick no da error');
t_eq($form->data['OLFATO']['lados']['D'], $olNorm['lados']['D'], 'El POST deja data[OLFATO]');
t_eq($form->data['PRICK']['alergenos']['dpte'], 8, 'El POST deja data[PRICK]');
$sin = CaseForm::fromPost($base + ['olfato_json' => '', 'prick_json' => ''], $pdo, $me, null, false);
t_true(!array_key_exists('OLFATO', $sin->data) && !array_key_exists('PRICK', $sin->data), 'Hidden vacíos: el caso no trae OLFATO ni PRICK');
$falla = CaseForm::fromPost($base + ['olfato_json' => json_encode($olMal = ['lados' => ['D' => ['T' => 99, 'D' => 1, 'I' => 1], 'I' => ['T' => 1, 'D' => 1, 'I' => 1]]])], $pdo, $me, null, false);
t_true(strpos((string) $falla->error, 'Olfato') !== false, 'Un puntaje inválido de olfato bloquea el guardado');
$falla = CaseForm::fromPost($base + ['prick_json' => json_encode(['histamina' => 99])], $pdo, $me, null, false);
t_true(strpos((string) $falla->error, 'Prick') !== false, 'Un valor inválido de prick bloquea el guardado');
$vuelta = CaseBuilder::caseDataToForm($form->data);
t_true(($vuelta['olfato_json'] ?? '') !== '' && ($vuelta['prick_json'] ?? '') !== '', 'Al reabrir el caso, los hidden vienen cargados');
$otra = CaseForm::fromPost($base + ['olfato_json' => $vuelta['olfato_json'], 'prick_json' => $vuelta['prick_json']], $pdo, $me, null, false);
t_eq($otra->data['OLFATO'], $form->data['OLFATO'], 'Reeditar sin tocar la ficha no cambia OLFATO');
t_eq($otra->data['PRICK'], $form->data['PRICK'], 'Reeditar sin tocar la ficha no cambia PRICK');

// La ficha lee las mismas normas que la app.
$normas = CaseBuilder::olfatoNormas();
t_eq(count($normas['grupos']), 9, 'Olfato: nueve grupos de edad');
t_eq($normas['cortes'][1][0], 30.5, 'Olfato: el corte de hiposmia es 30,5');
