<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseForm.php';

/**
 * Diploacusia por frecuencia del Fowler (Fowler.diplacusia = {índice: bool}):
 * la casilla de cada frecuencia manda su 0 escondido; sin dato, se sugiere
 * con el patrón (con reclutamiento, sí); el formato viejo (un bool para
 * todo el caso) se sigue leyendo.
 */

$fdPdo = (new ReflectionClass(PDO::class))->newInstanceWithoutConstructor();
$fdMe = ['id' => 1, 'username' => 'docente'];
// OD 5 / OI 35 sensorioneural en 1000 y 2000 Hz (índices 3 y 4): califican.
$fdAerea = ['od' => array_fill(0, 9, '5'), 'oi' => ['5', '5', '5', '35', '35', '5', '5', '5', '5']];
$fdRun = static function (array $extra) use ($fdPdo, $fdMe, $fdAerea): array {
    $v = array_merge([
        'age' => '30', 'nombre1' => 'Ana', 'apellido1' => 'Paz', 'nombre' => 'Ana', 'apellido' => 'Paz',
        'acumetria_auto' => '1', 'perfil_confirmar' => '1',
        'aerea' => $fdAerea, 'osea' => $fdAerea,
        'fowler_pattern' => ['3' => 'complete', '4' => 'none'],
    ], $extra);
    // Edición (id dado): no reserva id, así que no toca la base.
    return CaseForm::fromPost($v, $fdPdo, $fdMe, '1', true)->data['Fowler'];
};

$fd = $fdRun([]);
t_eq(array_keys($fd['patterns']), [3, 4], 'Fowler: califican 1000 y 2000 Hz');
t_eq($fd['diplacusia'], ['3' => true, '4' => false],
    'Diploacusia sin dato: la sugerida por el patrón (con reclutamiento sí)');

$fd = $fdRun(['diplacusia' => ['3' => '0', '4' => '1']]);
t_eq($fd['diplacusia'], ['3' => false, '4' => true],
    'Diploacusia marcada por el docente: manda sobre la sugerida');

$fd = $fdRun(['diplacusia' => ['3' => '0']]);
t_eq($fd['diplacusia'], ['3' => false, '4' => false],
    'Diploacusia: una frecuencia sin dato toma la sugerida, la otra la del docente');

$fd = $fdRun(['diplacusia' => '1']);
t_eq($fd['diplacusia'], ['3' => true, '4' => true], 'Diploacusia formato viejo: todo el caso');

t_true(CaseBuilder::fowlerDiplacusia(['diplacusia' => ['3' => true]], 3)
    && !CaseBuilder::fowlerDiplacusia(['diplacusia' => ['3' => true]], 4)
    && CaseBuilder::fowlerDiplacusia(['diplacusia' => true], 6)
    && !CaseBuilder::fowlerDiplacusia(['diplacusia' => []], 3),
    'fowlerDiplacusia lee por frecuencia y el bool viejo');

// Ida y vuelta por el formulario: cada frecuencia vuelve con su 1/0.
$fdV = CaseBuilder::caseDataToForm(['Fowler' => ['patterns' => ['3' => 'complete', '4' => 'none'],
    'diplacusia' => ['3' => false, '4' => true]]]);
t_eq($fdV['diplacusia'], ['3' => '0', '4' => '1'], 'caseDataToForm: diploacusia por frecuencia');
$fdV = CaseBuilder::caseDataToForm(['Fowler' => ['patterns' => ['3' => 'complete'], 'diplacusia' => true]]);
t_eq($fdV['diplacusia'], ['3' => '1'], 'caseDataToForm: el bool viejo se reparte en sus frecuencias');

// La proyección del perfil (supraliminares en auto): la diploacusia sigue al
// patrón proyectado, salvo la que ya viene marcada o desmarcada.
$fdProy = static function (array $extra) use ($fdAerea): array {
    $v = array_merge(['age' => '30', 'aerea' => $fdAerea, 'osea' => $fdAerea,
        'perfil' => ['od' => ['cce_pct' => '100'], 'oi' => ['cce_pct' => '100'], 'auto' => ['recruit' => '1']]], $extra);
    $r = CaseForm::completarConProyeccion($v);
    return [$r['fowler_pattern'] ?? null, $r['diplacusia'] ?? null];
};
[$fdPat, $fdDip] = $fdProy([]);
t_eq($fdPat, ['3' => 'complete', '4' => 'complete'], 'Proyección: coclear pura recluta completo');
t_eq($fdDip, ['3' => '1', '4' => '1'], 'Proyección: con reclutamiento sugiere diploacusia');
[, $fdDip] = $fdProy(['diplacusia' => ['3' => '0']]);
t_eq($fdDip, ['3' => '0', '4' => '1'], 'Proyección: no pisa la diploacusia que desmarcó el docente');
