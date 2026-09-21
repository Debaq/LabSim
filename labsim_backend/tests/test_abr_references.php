<?php

declare(strict_types=1);

/**
 * Bibliografía normativa del ABR (AbrReferences).
 *
 * Lo que se cuida acá: que cada set publicado apunte a una fuente que
 * exista y con cita completa, que no se cuele un valor imposible, y que el
 * catálogo del caso mezcle bien los sets de fábrica con los del docente.
 */

require_once dirname(__DIR__) . '/src/AbrReferences.php';

// --- Fuentes -------------------------------------------------------------

t_true(count(AbrReferences::FUENTES) >= 10, 'Hay bibliografía cargada');
foreach (AbrReferences::FUENTES as $fid => $f) {
    foreach (['cita', 'n', 'protocolo', 'enlace'] as $campo) {
        t_true(isset($f[$campo]) && $f[$campo] !== '', "Fuente {$fid}: tiene {$campo}");
    }
}

// --- Anclaje del set de fábrica -----------------------------------------

foreach (AbrReferences::ANCLAJE as $pop => $anclas) {
    foreach ($anclas as $que => $fid) {
        t_true(
            $fid === 'calculada' || isset(AbrReferences::FUENTES[$fid]),
            "Anclaje {$pop}/{$que}: la fuente {$fid} está citada"
        );
    }
}

// --- Sets publicados ------------------------------------------------------

$poblaciones = ['adult_male', 'adult_female', 'child', 'neonate', 'elderly'];
foreach (AbrReferences::SETS as $id => $set) {
    t_true(isset(AbrReferences::FUENTES[$set['fuente']]), "Set {$id}: su fuente está citada");
    t_true(($set['nota'] ?? '') !== '', "Set {$id}: dice qué publica y qué no");
    foreach ($set['populations'] as $pop => $ondas) {
        t_true(in_array($pop, $poblaciones, true), "Set {$id}: población {$pop} conocida");
        $previa = 0.0;
        foreach (['I', 'III', 'V'] as $onda) {
            if (!isset($ondas[$onda]['lat'])) {
                continue;
            }
            $lat = (float) $ondas[$onda]['lat'];
            t_true($lat > $previa, "Set {$id}/{$pop}: la onda {$onda} va después de la anterior");
            t_true($lat > 0.5 && $lat < 12.0, "Set {$id}/{$pop}/{$onda}: latencia plausible");
            $previa = $lat;
        }
    }
}

// --- Catálogo del caso ----------------------------------------------------

$propios = ['mi_set' => ['label' => 'Mío', 'populations' => []]];
$catalogo = AbrReferences::catalog($propios);
t_true(isset($catalogo['mi_set']), 'catalog(): entra el set del docente');
t_true(isset($catalogo['sanfins_2026']), 'catalog(): entran los publicados');
t_true(!empty($catalogo['sanfins_2026']['bibliografico']), 'catalog(): los publicados quedan marcados');

// Un set propio con el mismo id pisa al de fábrica: es la vía para corregir
// uno sin tocar código.
$pisado = AbrReferences::catalog(['hood' => ['label' => 'Hood corregido']]);
t_eq($pisado['hood']['label'], 'Hood corregido', 'catalog(): el set propio pisa al de fábrica');
t_eq(count($pisado), count(AbrReferences::SETS), 'catalog(): pisar no duplica la entrada');

// --- Planilla -------------------------------------------------------------

t_true(
    AbrReferences::planilla() !== null,
    'La planilla de referencia viaja con el backend (el docente no ve el repo del cliente)'
);

// --- Default de la app ----------------------------------------------------

$def = AbrReferences::defaults();
t_true(isset($def['adult_female']['V']['lat']), 'defaults(): forma onda => lat/amp');
t_close($def['adult_female']['V']['lat'], 5.54, 0.001, 'defaults(): sale de CaseWaveforms, ya reanclado');

// --- resolve(): lo que el set no publica lo pone el default --------------

$hood = AbrReferences::resolve('hood', 'adult_female');
t_close($hood['V']['lat'], 5.47, 0.001, 'resolve(): la latencia la pone el set');
t_close($hood['V']['amp'], $def['adult_female']['V']['amp'], 0.001,
    'resolve(): la amplitud, que Hood no publica, la pone el default');

$sanfins = AbrReferences::resolve('sanfins_2026', 'adult_female');
t_close($sanfins['I']['amp'], 0.36, 0.001, 'resolve(): Sanfins sí publica amplitud de onda I');
t_close($sanfins['III']['amp'], $def['adult_female']['III']['amp'], 0.001,
    'resolve(): pero no la de la III, que cae al default');

// Una población que el set no cubre queda entera en el default: un set
// parcial no puede dejar sin baseline a un paciente.
$hoodNeo = AbrReferences::resolve('hood', 'neonate');
t_close($hoodNeo['V']['lat'], $def['neonate']['V']['lat'], 0.001,
    'resolve(): población no cubierta por el set = default completo');

// --- Caso: con qué se construyó -------------------------------------------

// PDO de mentira: CaseForm no consulta nada para esto, pero la firma lo
// pide. Clase propia y no la de test_case_form porque los archivos de test
// se cargan por orden alfabético y este corre antes.
require_once dirname(__DIR__) . '/src/CaseForm.php';

class AbrRefFakeStmt
{
    public function fetch($mode = null) { return false; }
    public function fetchAll($mode = null) { return []; }
    public function execute($params = null) { return true; }
    public function fetchColumn($col = 0) { return 0; }
}

class AbrRefFakePdo extends PDO
{
    public function __construct()
    {
        // A propósito sin parent::__construct(): no hay driver que abrir.
    }

    #[\ReturnTypeWillChange]
    public function prepare(string $query, array $options = [])
    {
        return new AbrRefFakeStmt();
    }

    #[\ReturnTypeWillChange]
    public function query(string $query, ?int $fetchMode = null, ...$args)
    {
        return new AbrRefFakeStmt();
    }
}

$arPdo = new AbrRefFakePdo();
$arMe = ['id' => 1, 'username' => 'docente'];
$arPost = static function (array $extra = []): array {
    return array_merge([
        'age' => '30',
        // Mujer adulta: es la población que los sets publicados cubren
        // mejor (Hood solo trae esa).
        'gender' => '1',
        'nombre1' => 'Ana',
        'apellido1' => 'Paz',
        'acumetria_auto' => '1',
        'perfil_confirmar' => '1',
    ], $extra);
};

$conHood = CaseForm::fromPost($arPost(['abr' => ['autor' => 'hood']]), $arPdo, $arMe, null, false);
t_eq($conHood->error, null, 'El caso guarda con un set publicado elegido');
$autor = $conHood->data['ABR']['autor'] ?? [];
t_eq($autor['set'] ?? null, 'hood', 'El caso registra el set con el que se construyó');
t_true(($autor['baseline']['V']['lat'] ?? 0) > 0, 'Y registra el baseline resuelto, no solo el id');
t_close((float) ($autor['baseline']['V']['lat'] ?? 0), 5.47, 0.001,
    'El baseline guardado es el del set, no el de la app');
t_eq($autor['poblacion'] ?? null, 'adult_female', 'Queda dicho para qué población se resolvió');

// Sin elegir nada, el caso igual dice con qué se armó.
$porDefecto = CaseForm::fromPost($arPost(), $arPdo, $arMe, null, false);
t_eq($porDefecto->data['ABR']['autor']['set'] ?? null, '__default__',
    'Un caso sin autor elegido registra el default, no queda vacío');

// Un set que no existe no puede quedar registrado como si existiera.
$inventado = CaseForm::fromPost($arPost(['abr' => ['autor' => 'no_existe']]), $arPdo, $arMe, null, false);
t_eq($inventado->data['ABR']['autor']['set'] ?? null, 'no_existe',
    'Un set propio (o inventado) queda por su id: el rastro no se pierde');
t_close((float) ($inventado->data['ABR']['autor']['baseline']['V']['lat'] ?? 0),
    AbrReferences::defaults()[$inventado->data['ABR']['autor']['poblacion']]['V']['lat'], 0.001,
    'Pero su baseline resuelto es el default, no un invento');
