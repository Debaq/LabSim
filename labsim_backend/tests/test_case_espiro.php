<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseForm.php';

/**
 * La tarjeta Pulmón (ficha Nariz): la espirometría viaja en el hidden
 * `espiro_json` y termina en cases.data['ESPIRO'], con los mismos rangos que
 * valida la app (nasal/espirometria.normaliza). Vacío es "sin espirometría";
 * un valor fuera de rango bloquea el guardado diciendo cuál; reeditar el
 * caso sin tocar la ficha no lo pierde.
 */

final class EspiroFakeStmt
{
    public function fetchColumn()
    {
        return 41;
    }
}

final class EspiroFakePdo extends PDO
{
    public function __construct()
    {
    }

    #[\ReturnTypeWillChange]
    public function query(string $query, ?int $fetchMode = null, ...$args)
    {
        return new EspiroFakeStmt();
    }
}

$esAsma = ['talla' => 176, 'peso' => 74, 'pre' => ['fvc' => 4.9, 'fev1' => 3.2, 'pef' => 7.4],
           'bd' => ['fvc' => 5.1, 'fev1' => 3.8, 'pef' => 8.8], 'colaboracion' => 'buena'];
$esE = null;
$esOk = CaseForm::parseEspiro(json_encode($esAsma), $esE);
t_eq($esE, null, 'Pulmón: el asma del cap. 37 es válida');
t_eq($esOk['pre'], $esAsma['pre'], 'Pulmón: conserva la maniobra pre');
t_eq($esOk['bd']['fev1'], 3.8, 'Pulmón: conserva la del broncodilatador');
t_eq($esOk['tope_e'], null, 'Pulmón: sin tope, null');
t_eq(CaseForm::parseEspiro('', $esE), null, 'Pulmón: vacío da null');
t_eq($esE, null, 'Pulmón: vacío no es error');

$esFija = $esAsma;
unset($esFija['bd']);
$esFija['tope_e'] = 3.2;
$esFija['tope_i'] = 3;
$esFija['colaboracion'] = 'cualquiera';
$esF = CaseForm::parseEspiro(json_encode($esFija), $esE);
t_eq([$esF['tope_e'], $esF['tope_i']], [3.2, 3], 'Pulmón: guarda los topes');
t_true(!isset($esF['bd']), 'Pulmón: sin bd no inventa una');
t_eq($esF['colaboracion'], 'buena', 'Pulmón: una colaboración desconocida cae en buena');

$esMal = $esAsma;
$esMal['pre']['fev1'] = 5.0;
CaseForm::parseEspiro(json_encode($esMal), $esE);
t_true(strpos((string) $esE, 'menor que la FVC') !== false, 'Pulmón: FEV1 sobre la FVC avisa');
$esMal = $esAsma;
$esMal['talla'] = 30;
CaseForm::parseEspiro(json_encode($esMal), $esE);
t_true(strpos((string) $esE, 'Talla') !== false, 'Pulmón: talla fuera de rango dice cuál');
CaseForm::parseEspiro('{roto', $esE);
t_true(strpos((string) $esE, 'JSON') !== false, 'Pulmón: JSON roto avisa');

// El formulario entero y la ida y vuelta.
$esPdo = new EspiroFakePdo();
$esMe = ['id' => 1, 'username' => 'admin'];
$esBase = ['age' => '27', 'nombre1' => 'Óscar', 'apellido1' => 'Cárdenas', 'acumetria_auto' => '1', 'perfil_confirmar' => '1'];
$esForm = CaseForm::fromPost($esBase + ['espiro_json' => json_encode($esAsma)], $esPdo, $esMe, null, false);
t_eq($esForm->error, null, 'Pulmón: el POST con espirometría no da error');
t_eq($esForm->data['ESPIRO']['pre'], $esAsma['pre'], 'Pulmón: el POST deja data[ESPIRO]');
$esSin = CaseForm::fromPost($esBase + ['espiro_json' => ''], $esPdo, $esMe, null, false);
t_true(!array_key_exists('ESPIRO', $esSin->data), 'Pulmón: hidden vacío, el caso no trae ESPIRO');
$esFalla = CaseForm::fromPost($esBase + ['espiro_json' => json_encode($esMal)], $esPdo, $esMe, null, false);
t_true(strpos((string) $esFalla->error, 'Talla') !== false, 'Pulmón: un valor inválido bloquea el guardado');
$esVuelta = CaseBuilder::caseDataToForm($esForm->data);
t_true(($esVuelta['espiro_json'] ?? '') !== '', 'Pulmón: al reabrir el caso, el hidden viene cargado');
$esOtra = CaseForm::fromPost($esBase + ['espiro_json' => $esVuelta['espiro_json']], $esPdo, $esMe, null, false);
t_eq($esOtra->data['ESPIRO'], $esForm->data['ESPIRO'], 'Pulmón: reeditar sin tocar la ficha no cambia nada');

// La ficha lee los mismos coeficientes que la app.
$esGli = CaseBuilder::gli2012();
t_true(isset($esGli['M_FEV1']['c']['a0']) && count($esGli['F_FVC']['L']) === 370, 'Pulmón: GLI-2012 completo para la ficha');
t_eq(md5_file(__DIR__ . '/../resources/nasal/gli2012.json'), md5_file(__DIR__ . '/../../resources/nasal/gli2012.json'),
     'Pulmón: el GLI del backend es el mismo archivo que el de la app');
