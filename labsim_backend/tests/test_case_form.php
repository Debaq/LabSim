<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseForm.php';

/**
 * El POST del formulario de casos -> cases.data.
 *
 * Esto vivía adentro de admin/case_create.php, así que la única forma de
 * ejercitarlo era abrir el navegador y guardar un caso. Estos tests cubren
 * lo que decidía en silencio: la acumetría automática, "igualar ósea a
 * aérea", el LDL deshabilitado, la fase 1 de otoscopia sin texto, y qué
 * aporta la proyección del perfil sin pisar lo que mandó el docente.
 *
 * CaseForm no toca la base salvo para reservar el id del caso nuevo, así
 * que alcanza con un PDO de mentira -- este entorno no tiene pdo_sqlite.
 */

final class CaseFormFakeStmt
{
    public function fetchColumn()
    {
        return 41; // el próximo id será "42"
    }
}

final class CaseFormFakePdo extends PDO
{
    public function __construct()
    {
        // A propósito sin parent::__construct(): no hay driver que abrir.
    }

    #[\ReturnTypeWillChange]
    public function query(string $query, ?int $fetchMode = null, ...$args)
    {
        return new CaseFormFakeStmt();
    }
}

$cfPdo = new CaseFormFakePdo();
$cfMe = ['id' => 1, 'username' => 'docente'];

/**
 * Un POST mínimo que guarda. `perfil_confirmar` se da por tildado: los
 * avisos de incoherencia tienen su propio test más abajo.
 */
$cfPost = static function (array $extra = []): array {
    return array_merge([
        'age' => '30',
        'nombre1' => 'Ana',
        'apellido1' => 'Paz',
        'acumetria_auto' => '1',
        'perfil_confirmar' => '1',
    ], $extra);
};

$cfRun = static function (array $extra = []) use ($cfPost, $cfPdo, $cfMe): CaseForm {
    return CaseForm::fromPost($cfPost($extra), $cfPdo, $cfMe, null, false);
};

/**
 * Las once fichas dadas por revisadas (ver CaseReview): lo que tilda el
 * docente en el Resumen antes de guardar. No entra en el POST base a
 * propósito -- la mayoría de estos tests miran qué queda en cases.data, y
 * revisar una ficha apaga los pendientes que el editor le reclama.
 */
$cfRevisado = ['revisado' => array_fill_keys(array_keys(CaseReview::revisables()), '1')];

// --- Validaciones que bloquean el guardado ---------------------------------

t_eq(CaseForm::fromPost(['age' => '0'], $cfPdo, $cfMe, null, false)->error,
    'Falta la edad.', 'Sin edad no se guarda');
t_eq(CaseForm::fromPost(['age' => '30'], $cfPdo, $cfMe, null, false)->error,
    'Falta el nombre del paciente: generalo con "Generar caso" (Armado rápido) o escribilo a mano en la pestaña Paciente.',
    'Al crear, sin nombre no se guarda');
t_eq($cfRun(['z_od' => 'ZZZ'])->error, 'Tipo de timpanograma inválido.', 'Timpanograma fuera del catálogo');
t_eq($cfRun(['etf_oi' => 'chanta'])->error, 'Valor de ETF inválido.', 'ETF fuera del catálogo');
t_eq($cfRun(['abr' => ['od' => ['type' => 'inventada']]])->error, 'Patología ABR inválida.', 'Patología ABR fuera del catálogo');
t_eq($cfRun(['eoas' => ['od' => ['sello_pct' => '3']]])->error,
    'Sello de sonda EOA fuera de rango (5-100%).', 'Sello de sonda por debajo del mínimo');
// `presente` va explícito: desde que el acúfeno es opcional, un bloque de
// tinnitus sin esa casilla no se valida (el paciente no tiene acúfeno y da
// igual lo que digan los otros campos).
t_eq($cfRun(['tinnitus' => ['presente' => '1', 'lateralidad' => 'unilateral', 'oido' => '']])->error,
    'Falta el oído del tinnitus (unilateral, hay que indicar cuál).', 'Tinnitus unilateral sin oído');
t_eq($cfRun(['tinnitus' => ['lateralidad' => 'unilateral', 'oido' => '']])->error, null,
    'Sin la casilla "tiene tinnitus" no se valida nada del acúfeno');

// Rinne/Weber a mano: el "auto" global apagado deja que el docente escriba,
// pero solo valores del catálogo.
$cfManualMalo = CaseForm::fromPost([
    'age' => '30', 'nombre1' => 'Ana', 'apellido1' => 'Paz', 'perfil_confirmar' => '1',
    'rinne' => ['500' => ['od' => 'chanta', 'oi' => 'positivo'], '1000' => ['od' => 'positivo', 'oi' => 'positivo']],
], $cfPdo, $cfMe, null, false);
t_eq($cfManualMalo->error, 'Valor de Rinne/Weber inválido.', 'Rinne fuera del catálogo');

// --- Audiometría: lo que el formulario decide solo ------------------------

// Pérdida conductiva en OD (gap 50 dB), OI sano.
$cfConductiva = ['aerea' => ['od' => array_fill(0, 9, 60), 'oi' => array_fill(0, 9, 5)],
                 'osea' => ['od' => array_fill(0, 9, 10), 'oi' => array_fill(0, 9, 5)]];
$cfF = $cfRun($cfConductiva);
t_eq($cfF->error, null, 'Caso conductivo simple: se guarda');
t_eq($cfF->data['Aerea'][0], [60, 5], 'Los umbrales viajan como pares [OD, OI]');
t_eq($cfF->data['Rinne']['500']['od'], 'negativo', 'Rinne auto: gap >= 15 dB da negativo');
t_eq($cfF->data['Rinne']['500']['oi'], 'positivo', 'Rinne auto: sin gap da positivo');
t_eq($cfF->data['Weber']['500'], 'centrado', 'Weber auto: óseas parejas quedan centradas');

// Weber lateraliza al oído de mejor umbral óseo.
$cfF = $cfRun(['aerea' => ['od' => array_fill(0, 9, 50), 'oi' => array_fill(0, 9, 5)],
               'osea' => ['od' => array_fill(0, 9, 50), 'oi' => array_fill(0, 9, 5)]]);
t_eq($cfF->data['Weber']['500'], 'oi', 'Weber auto: lateraliza al oído con mejor ósea');

// "Igualar ósea a aérea" borra el gap, y con él el Rinne negativo.
$cfF = $cfRun($cfConductiva + ['igualar' => ['od' => '1']]);
t_eq($cfF->data['Osea'][0], [60, 5], 'Igualar: la ósea de ese oído copia la aérea');
t_eq($cfF->data['Rinne']['500']['od'], 'positivo', 'Igualar: sin gap el Rinne pasa a positivo');

// El LDL sin tildar es "no medido" (130), no un 0 que se lea como disconfort
// a volumen mínimo.
$cfF = $cfRun(['ldl' => ['od' => array_fill(0, 9, 95), 'oi' => array_fill(0, 9, 95)],
               'ldl_habilitado' => ['od' => '1']]);
t_eq($cfF->data['LDL'][0], [95, 130], 'LDL: el oído sin habilitar queda en 130 (ausente)');

// --- Otoscopia -----------------------------------------------------------

$cfF = $cfRun(['otoscopia' => ['fase_count' => '3',
    'texto' => [0 => 'esto no viaja', 1 => 'tras limpieza', 2 => 'final']]]);
t_eq($cfF->data['Otoscopia']['fases'],
    [['texto' => ''], ['texto' => 'tras limpieza'], ['texto' => 'final']],
    'Otoscopia: la fase 1 nunca lleva texto, no hay fase anterior que describir');

// --- Borrador de anamnesis por IA ----------------------------------------

$cfF = $cfRun(['anamnesis_ia' => ['generado' => '1']]);
t_true(!$cfF->ok(), 'Un borrador de IA sin verificar bloquea el guardado');
t_eq(array_column($cfF->faltantes, 'tab'), ['anamnesis'], 'El pendiente apunta a la pestaña Anamnesis');
t_eq($cfF->data['Anamnesis']['ia']['verificado'], false, 'Sin tildar, el borrador no queda verificado');

$cfF = $cfRun(array_merge($cfRevisado, ['anamnesis_ia' => ['generado' => '1', 'verificado' => '1']]));
t_true($cfF->ok(), 'Verificado y revisado, el caso con borrador de IA se guarda');
t_eq($cfF->data['Anamnesis']['ia']['verificado_por'], 'docente', 'Queda quién lo verificó');

// Y el borrador sin verificar NO se acepta desde el Resumen: tildar la ficha
// dice "miré esto", y acá lo que falta es exactamente eso, sobre un texto
// que escribió una máquina.
$cfF = $cfRun(array_merge($cfRevisado, ['anamnesis_ia' => ['generado' => '1']]));
t_eq(array_column($cfF->faltantes, 'tab'), ['anamnesis'],
    'Anamnesis de IA: revisar la ficha no reemplaza verificar el borrador');
t_true(!$cfF->ok(), 'Con el borrador sin verificar el caso sigue sin guardarse');

// --- Revisión ficha por ficha (Resumen) -----------------------------------

$cfSinRevisar = $cfRun();
t_true(!$cfSinRevisar->ok(), 'Un caso sin revisar no se guarda, aunque no le falte ningún dato');
t_eq(count($cfSinRevisar->sinRevisar), count(CaseReview::revisables()),
    'Sin tildar nada, faltan por revisar las once fichas');
t_eq($cfRun($cfRevisado)->sinRevisar, [], 'Tildadas las once, no queda nada por revisar');
t_eq(array_keys($cfRun(array_merge($cfRevisado, ['revisado' => ['paciente' => '1']]))->sinRevisar),
    array_values(array_diff(array_keys(CaseReview::revisables()), ['paciente'])),
    'La lista dice exactamente qué fichas quedaron sin tildar');

// Lo que se guarda es la revisión, no un puntaje: qué fichas y quién.
$cfRevF = $cfRun($cfRevisado);
t_eq($cfRevF->data['Revision']['tabs']['vemp'], true, 'La revisión viaja a cases.data');
t_eq($cfRevF->data['Revision']['by'], 'docente', 'Y queda quién la hizo');

// Revisar una ficha acepta lo que el editor le reclamaba: un timpanograma en
// A con 40 dB de gap es un pendiente hasta que el docente dice que es así.
$cfGap = ['aerea' => ['od' => array_fill(0, 9, 45), 'oi' => array_fill(0, 9, 0)],
          'osea' => ['od' => array_fill(0, 9, 0), 'oi' => array_fill(0, 9, 0)]];
t_true(in_array('timpanometria', array_column($cfRun($cfGap)->faltantes, 'tab'), true),
    'El gap con timpanograma en A se reclama');
t_true(!in_array('timpanometria', array_column($cfRun(array_merge($cfGap, $cfRevisado))->faltantes, 'tab'), true),
    'Revisada la ficha, el mismo caso deja de reclamarlo');

// --- Perfil auditivo ------------------------------------------------------

// 55 dB planos con un ABR "normal" a 20 dB nHL es justo la incoherencia que
// el perfil tiene que hacer notar antes de dejar guardar.
$cfSordera = ['aerea' => ['od' => array_fill(0, 9, 55), 'oi' => array_fill(0, 9, 55)],
              'osea' => ['od' => array_fill(0, 9, 55), 'oi' => array_fill(0, 9, 55)]];
$cfSinConfirmar = CaseForm::fromPost(array_merge(
    ['age' => '30', 'nombre1' => 'Ana', 'apellido1' => 'Paz', 'acumetria_auto' => '1'],
    $cfSordera
), $cfPdo, $cfMe, null, false);
t_true(count($cfSinConfirmar->avisos) > 0, 'Sin confirmar, la incoherencia con el perfil avisa');
t_true(!$cfSinConfirmar->ok(), 'Un aviso sin leer no deja guardar todavía');
t_eq($cfRun($cfSordera)->avisos, [], 'Tildada la casilla, los mismos avisos dejan pasar el caso');

// La derivación sugiere, no manda: el formulario ya llega con la proyección
// encima (la escribe case/profile-preview.js), así que al guardar gana lo
// posteado, encendida o no la casilla. Lo único que la proyección sigue
// aportando es lo que el formulario no tiene cómo mandar: el umbral por
// estímulo del ABR.
$cfAbr = ['abr' => ['od' => ['umbral' => '20'], 'oi' => ['umbral' => '20']]];
$cfManual = $cfRun($cfSordera + $cfAbr);
t_eq($cfManual->data['ABR']['OD']['umbral'], 20, 'Perfil en manual: el umbral del ABR es del docente');
t_eq($cfManual->data['ABR']['OD']['type'], 'normal', 'Perfil en manual: la patología del ABR es del docente');
t_true(!isset($cfManual->data['ABR']['OD']['umbral_por_estimulo']),
    'Perfil en manual: no hay umbral por estímulo');

$cfAuto = $cfRun($cfSordera + $cfAbr + ['perfil' => ['auto' => ['abr' => '1']]]);
t_eq($cfAuto->data['ABR']['OD']['umbral'], 20, 'Perfil en automático: la corrección a mano del umbral se respeta');
t_eq($cfAuto->data['ABR']['OD']['type'], 'normal', 'Perfil en automático: y también la de la patología');
t_true(isset($cfAuto->data['ABR']['OD']['umbral_por_estimulo']['click']),
    'Perfil en automático: la proyección igual aporta el umbral por estímulo');

// --- Id del caso ----------------------------------------------------------

t_eq($cfRun()->caseId, '42', 'Al crear se reserva el id siguiente');
t_eq(CaseForm::fromPost([
    'age' => '30', 'nombre' => 'Ana', 'apellido' => 'Paz',
    'acumetria_auto' => '1', 'perfil_confirmar' => '1',
], $cfPdo, $cfMe, '7', true)->caseId, '7', 'Al editar se conserva el id del caso');

// --- Los dos helpers de lectura del POST ----------------------------------
//
// Sutiles y muy usados (92 llamadas entre el parseo y el form al
// redibujarse), así que van pinchados: una clave presente en null tiene que
// contar como ausente, y el par sin contraparte se completa con 0 (no con
// el valor del otro oído, que sería inventarle un umbral).

t_eq(CaseForm::val(['a' => ['b' => 3]], ['a', 'b']), 3, 'val: lee anidado');
t_eq(CaseForm::val(['a' => ['b' => 3]], ['a', 'z'], 'def'), 'def', 'val: clave ausente da el default');
t_eq(CaseForm::val(['a' => null], ['a'], 'def'), 'def', 'val: una clave en null cuenta como ausente');
t_eq(CaseForm::val(['a' => 'texto'], ['a', 'b'], 'def'), 'def', 'val: bajar por algo que no es array da el default');
t_eq(CaseForm::val(['a' => ['b' => 0]], ['a', 'b'], 'def'), 0, 'val: un 0 es un valor, no un ausente');

t_eq(CaseForm::zip([1, 2], [3, 4]), [[1, 3], [2, 4]], 'zip: arma los pares [OD, OI]');
t_eq(CaseForm::zip([1, 2], [3]), [[1, 3], [2, 0]], 'zip: sin contraparte, el OI queda en 0');
t_eq(CaseForm::zip([], []), [], 'zip: vacío da vacío');


// --- VEMP: los tres subtipos ----------------------------------------------

$cfVemp = $cfRun([
    'vemp' => [
        'od' => [
            'type' => 'sacular',
            'CVEMP' => ['umbral' => '45', 'repro' => '1', 'lat_p13' => '1.5', 'amp_p13' => '-90'],
            'OVEMP' => ['umbral' => '65'],
            'MVEMP' => ['umbral' => '70', 'amp_p13' => '-10'],
        ],
    ],
])->data['VEMP'];
t_eq($cfVemp['OD']['type'], 'sacular', 'VEMP: una patología por oído');
t_eq($cfVemp['OD']['subtipos']['CVEMP']['umbral'], 45, 'VEMP: el umbral del cervical');
t_eq($cfVemp['OD']['subtipos']['OVEMP']['umbral'], 65, 'VEMP: el umbral del ocular es otro');
t_eq($cfVemp['OD']['subtipos']['CVEMP']['desviaciones']['p13']['amp'], -90.0, 'VEMP: P13 del cervical');
t_eq($cfVemp['OD']['subtipos']['MVEMP']['desviaciones']['p13']['amp'], -10.0,
    'VEMP: P13 del masetero es independiente del cervical (mismo nombre, otro músculo)');
t_eq($cfVemp['OD']['subtipos']['OVEMP']['peaks'], ['n10', 'p16'], 'VEMP: el ocular lleva sus propios picos');
t_true(!isset($cfVemp['OD']['subtipos']['OVEMP']['repro']) || $cfVemp['OD']['subtipos']['OVEMP']['repro'] === false,
    'VEMP: la casilla no tildada de un subtipo no arrastra la del otro');
// Los subtipos que el POST no menciona igual se persisten, en su default.
t_eq($cfVemp['OI']['subtipos']['CVEMP']['umbral'], CaseBuilder::VEMP_DEFAULTS['CVEMP']['umbral'],
    'VEMP: un oído que el POST no toca queda en los defaults de cada subtipo');

// Coherencia: patología Normal con ondas cargadas se reclama, y dice en
// CUÁL de los tres VEMP está el problema.
$cfVempIncoherente = $cfRun([
    'vemp' => ['od' => ['type' => 'normal', 'MVEMP' => ['lat_p13' => '3.0']]],
])->error;
t_true($cfVempIncoherente !== null && strpos($cfVempIncoherente, 'mVEMP') !== false,
    'VEMP: la incoherencia nombra el subtipo donde está el problema');
t_eq($cfRun(['vemp' => ['od' => ['type' => 'normal', 'MVEMP' => ['lat_p13' => '0']]]])->error, null,
    'VEMP: patología normal con las ondas en 0 guarda sin chistar');
