<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseForm.php';

/**
 * La ficha Nariz: el paciente de RinoSim viaja en el hidden `nasal_json` y
 * termina en cases.data['NASAL'].
 *
 * Lo que se cuida: que vacío sea "sin nariz", que un número fuera de rango o
 * un bloque a medias dé un error que diga cuál, que solo se guarden las
 * claves conocidas, que el caso vuelva a la ficha al reabrirlo (y que un
 * docente que no ve la ficha no lo pierda al guardar), y que la ficha no
 * sume una casilla al Resumen ni renumere las demás.
 */

final class NasalFakeStmt
{
    public function fetchColumn()
    {
        return 41;
    }
}

final class NasalFakePdo extends PDO
{
    public function __construct()
    {
        // A propósito sin parent::__construct(): no hay driver que abrir.
    }

    #[\ReturnTypeWillChange]
    public function query(string $query, ?int $fetchMode = null, ...$args)
    {
        return new NasalFakeStmt();
    }
}

$nsTabla = CaseBuilder::nasalCuadros();
t_true(count($nsTabla['cuadros']) >= 8, 'Nariz: el JSON de cuadros trae los cuadros de ejemplo');
t_eq(count($nsTabla['cuadros']['polipos']['variantes']), 8, 'Nariz: ocho variantes por cuadro');
$nsPac = $nsTabla['cuadros']['desviacion_derecha']['variantes'][2];

$nsErr = null;
$nsOk = CaseForm::parseNasal(json_encode($nsPac), $nsErr);
t_eq($nsErr, null, 'Nariz: un paciente de los cuadros es válido');
t_eq($nsOk['cuadro'], 'desviacion_derecha', 'Nariz: conserva el cuadro');
t_eq($nsOk['semilla'], 3, 'Nariz: conserva la semilla');
t_eq($nsOk['lados']['D']['valvula']['area'], $nsPac['lados']['D']['valvula']['area'], 'Nariz: conserva los números de la fosa');
t_eq($nsOk['ciclo']['periodo'], $nsPac['ciclo']['periodo'], 'Nariz: conserva el ciclo');

// Todos los cuadros y variantes pasan la validación (si no, el editor
// propondría algo que él mismo rechaza al guardar).
$nsTodos = true;
foreach ($nsTabla['cuadros'] as $c) {
    foreach (array_merge([$c['tipo']], $c['variantes']) as $p) {
        CaseForm::parseNasal(json_encode($p), $nsE);
        $nsTodos = $nsTodos && $nsE === null;
    }
}
t_true($nsTodos, 'Nariz: ningún cuadro ni variante precalculada viola su propio rango');

// Vacío y sin casilla: sin NASAL, sin error.
foreach (['', '   ', null] as $vacio) {
    t_eq(CaseForm::parseNasal($vacio, $nsE), null, 'Nariz: vacío da null');
    t_eq($nsE, null, 'Nariz: vacío no es un error');
}

// Inválidos, con el mensaje que dice cuál.
$nsMal = static function (callable $f) use ($nsPac): ?string {
    $p = $nsPac;
    $f($p);
    $r = CaseForm::parseNasal(json_encode($p), $nsE);
    return $r === null ? $nsE : 'VALIDO';
};
t_true(strpos((string) CaseForm::parseNasal('{no es json', $nsE) ?: $nsE, 'JSON') !== false, 'Nariz: JSON roto avisa');
t_true(strpos((string) $nsMal(static function (&$p) { $p['lados']['D']['narina'] = 9; }), 'FND') !== false, 'Nariz: narina fuera de rango nombra la fosa D');
t_true(strpos((string) $nsMal(static function (&$p) { $p['lados']['I']['valvula']['area'] = -1; }), 'Válvula: área') !== false, 'Nariz: válvula negativa nombra el parámetro');
t_true(strpos((string) $nsMal(static function (&$p) { $p['lados']['I']['congestion'] = 'mucha'; }), 'número') !== false, 'Nariz: texto en vez de número');
t_true(strpos((string) $nsMal(static function (&$p) { unset($p['lados']['I']); }), 'FNI') !== false, 'Nariz: falta una fosa');
t_true(strpos((string) $nsMal(static function (&$p) { unset($p['lados']['D']['cornete']['oseo']); }), 'Cornete') !== false, 'Nariz: falta un parámetro');
t_true(strpos((string) $nsMal(static function (&$p) { $p['ciclo']['amplitud'] = 0.9; }), 'amplitud') !== false, 'Nariz: amplitud del ciclo sobre 0,5');
t_true(strpos((string) $nsMal(static function (&$p) { $p['ciclo']['periodo'] = 0; }), 'periodo') !== false, 'Nariz: periodo cero');
t_true(strpos((string) $nsMal(static function (&$p) { $p['perforacion']['area'] = -0.1; }), 'Perforación') !== false, 'Nariz: perforación con área negativa');
t_true(strpos((string) $nsMal(static function (&$p) { $p['ciclo']['fase'] = 'x'; }), 'fase') !== false, 'Nariz: fase no numérica');
t_eq($nsMal(static function (&$p) { $p['lados']['D']['narina'] = 1.6; }), 'VALIDO', 'Nariz: el borde del rango vale');

// Solo las claves conocidas; nombre vacío cae en "Paciente editado".
$nsSucio = $nsPac;
$nsSucio['intruso'] = 'x';
$nsSucio['lados']['D']['otro'] = 5;
$nsSucio['nombre'] = '  ';
$nsSucio['cuadro'] = 'no_existe';
$nsLimpio = CaseForm::parseNasal(json_encode($nsSucio), $nsE);
t_eq(array_keys($nsLimpio), ['nombre', 'cuadro', 'semilla', 'lados', 'ciclo', 'perforacion'], 'Nariz: solo las claves conocidas');
t_true(!isset($nsLimpio['lados']['D']['otro']), 'Nariz: el parámetro desconocido se descarta');
t_eq($nsLimpio['nombre'], 'Paciente editado', 'Nariz: nombre vacío');
t_eq($nsLimpio['cuadro'], null, 'Nariz: cuadro desconocido pasa a null');

// El formulario entero: de nasal_json a data['NASAL'], y el error bloquea.
$nsPdo = new NasalFakePdo();
$nsMe = ['id' => 1, 'username' => 'admin'];
$nsBase = ['age' => '30', 'nombre1' => 'Ana', 'apellido1' => 'Paz', 'acumetria_auto' => '1', 'perfil_confirmar' => '1'];
$nsForm = CaseForm::fromPost($nsBase + ['nasal_json' => json_encode($nsPac)], $nsPdo, $nsMe, null, false);
t_eq($nsForm->error, null, 'Nariz: el POST con nariz no da error');
t_eq($nsForm->data['NASAL']['lados']['I'], $nsOk['lados']['I'], 'Nariz: el POST deja data[NASAL]');
$nsSin = CaseForm::fromPost($nsBase + ['nasal_json' => ''], $nsPdo, $nsMe, null, false);
t_true(!array_key_exists('NASAL', $nsSin->data), 'Nariz: hidden vacío, el caso no trae NASAL');
$nsRoto = $nsPac;
$nsRoto['lados']['D']['polipos'] = 99;
$nsFalla = CaseForm::fromPost($nsBase + ['nasal_json' => json_encode($nsRoto)], $nsPdo, $nsMe, null, false);
t_true(strpos((string) $nsFalla->error, 'Pólipos') !== false, 'Nariz: un valor inválido bloquea el guardado con su mensaje');

// Ida y vuelta: data['NASAL'] -> formulario (hidden) -> data['NASAL'], sin
// pasar por la ficha (el docente que edita un caso con nariz).
$nsVuelta = CaseBuilder::caseDataToForm($nsForm->data);
t_true(isset($nsVuelta['nasal_json']) && $nsVuelta['nasal_json'] !== '', 'Nariz: al reabrir el caso, el hidden viene cargado');
$nsOtra = CaseForm::fromPost($nsBase + ['nasal_json' => $nsVuelta['nasal_json']], $nsPdo, $nsMe, null, false);
t_eq($nsOtra->data['NASAL'], $nsForm->data['NASAL'], 'Nariz: reeditar sin tocar la ficha no cambia la nariz');
t_true(!isset(CaseBuilder::caseDataToForm(['gender' => 0])['nasal_json']), 'Nariz: un caso sin NASAL no carga el hidden');

// La ficha no es revisable: ni al Resumen ni a la numeración.
t_true(isset(CaseReview::TABS['nariz']) && !empty(CaseReview::TABS['nariz']['solo_admin']), 'Nariz: ficha de solo admin');
t_true(!isset(CaseReview::revisables()['nariz']), 'Nariz: no entra en las revisables');
t_eq(count(CaseReview::revisables()), 11, 'Nariz: siguen siendo once las fichas a revisar');
t_eq(CaseReview::label('nariz'), 'Nariz', 'Nariz: label sin número');
t_eq(CaseReview::label('anamnesis'), '11. Anamnesis', 'Nariz: no renumera las demás');
t_eq(array_keys(CaseReview::TABS)[array_search('tinnitus', array_keys(CaseReview::TABS), true) + 1], 'nariz', 'Nariz: va después de Tinnitus');
t_true(!isset(CaseReview::sinRevisar([])['nariz']), 'Nariz: nunca queda "sin revisar"');
