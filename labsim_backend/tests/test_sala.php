<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Sala.php';

/**
 * La sala de atención y su motor de turnos (ver Sala.php).
 *
 * El motor decide quién contesta cada pregunta, así que se prueba con el
 * dado inyectado: `siempre` = todos los que puedan meterse se meten,
 * `nunca` = solo habla el destinatario. Con random_int de verdad estos
 * tests serían intermitentes y no dirían nada.
 */

$siempre = static fn(int $max) => 1;    // roll 1 <= puntaje, salvo puntaje 0
$nunca = static fn(int $max) => 101;    // nunca <= puntaje

/** Sala de lactante: guagua de 1 año + madre informante. El caso pediátrico base. */
function sala_lactante(): array
{
    return Sala::normalize(['personas' => [
        ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'Benja', 'edad' => 1, 'es_paciente' => true],
        ['id' => 'p2', 'rol' => 'madre', 'nombre' => 'Rosa', 'edad' => 32, 'genero' => 1, 'informante' => true],
    ]]);
}

/** Adulto mayor que niega su hipoacusia + esposa que la nota. El caso de oro. */
function sala_negador(): array
{
    return Sala::normalize(['personas' => [
        ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'Luis', 'edad' => 78,
         'es_paciente' => true, 'conciencia' => 10, 'informante' => true],
        ['id' => 'p2', 'rol' => 'conyuge', 'nombre' => 'Ana', 'edad' => 75, 'genero' => 1,
         'interrumpe' => 30, 'version' => 'no escucha nada hace años y sube la tele al máximo'],
    ]]);
}

// -- Capacidad de relato por edad ---------------------------------------

t_eq(Sala::capacidad(1), Sala::CAP_NULO, 'Guagua de 1 año: no habla');
t_eq(Sala::capacidad(2), Sala::CAP_NULO, 'A los 2 todavía no cuenta su historia');
t_eq(Sala::capacidad(4), Sala::CAP_MINIMO, 'A los 4 dice su nombre y dónde le duele');
t_eq(Sala::capacidad(10), Sala::CAP_PARCIAL, 'A los 10 cuenta síntomas, no fechas ni remedios');
t_eq(Sala::capacidad(15), Sala::CAP_CASI_TOTAL, 'A los 15 cuenta casi todo lo suyo');
t_eq(Sala::capacidad(40), Sala::CAP_TOTAL, 'El adulto cuenta su historia completa');

t_true(!Sala::maneja(Sala::CAP_PARCIAL, Sala::T_FARMACO), 'Un niño de 10 no sabe qué remedios toma');
t_true(!Sala::maneja(Sala::CAP_PARCIAL, Sala::T_TEMPORAL), 'Ni desde cuándo con precisión');
t_true(Sala::maneja(Sala::CAP_PARCIAL, Sala::T_SINTOMA), 'Pero sí lo que siente');
t_true(!Sala::maneja(Sala::CAP_CASI_TOTAL, Sala::T_PERINATAL), 'Ni el adolescente sabe de su propio parto');
t_true(!Sala::maneja(Sala::CAP_NULO, Sala::T_IDENTIDAD), 'La guagua no dice ni su nombre');

// -- Clasificación de la pregunta ---------------------------------------

t_eq(Sala::tipoPregunta('¿Desde cuándo le pasa esto?'), Sala::T_TEMPORAL, 'Desde cuándo = temporal');
t_eq(Sala::tipoPregunta('desde cuando le pasa'), Sala::T_TEMPORAL, 'Sin tildes clasifica igual');
t_eq(Sala::tipoPregunta('¿Cómo fue el parto?'), Sala::T_PERINATAL, 'Parto = perinatal');
t_eq(Sala::tipoPregunta('¿Desde cuándo toma ese remedio?'), Sala::T_FARMACO,
    'El dato pedido es el remedio, no la fecha: lo sabe quien lo compra');
t_eq(Sala::tipoPregunta('¿Le duele el oído?'), Sala::T_SINTOMA, 'Duele = síntoma');
t_eq(Sala::tipoPregunta('¿Cómo te llamas?'), Sala::T_IDENTIDAD, 'Nombre = identidad');
t_eq(Sala::tipoPregunta('Buenos días, tome asiento'), Sala::T_GENERAL, 'Lo demás cae en general');

// -- Normalización: invariantes que el resto del código da por ciertas ---

$dosPacientes = Sala::normalize(['personas' => [
    ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'A', 'edad' => 30, 'es_paciente' => true],
    ['id' => 'p2', 'rol' => 'paciente', 'nombre' => 'B', 'edad' => 31, 'es_paciente' => true],
]]);
t_eq(count(array_filter($dosPacientes['personas'], fn($p) => $p['es_paciente'])), 1,
    'Dos marcados como paciente: queda uno solo');

$sinPaciente = Sala::normalize(['personas' => [
    ['id' => 'p1', 'rol' => 'madre', 'nombre' => 'Rosa', 'edad' => 32],
]]);
t_true($sinPaciente['personas'][0]['es_paciente'], 'Sin paciente marcado: se promueve el primero');

$idsRepetidos = Sala::normalize(['personas' => [
    ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'A', 'edad' => 30],
    ['id' => 'p1', 'rol' => 'madre', 'nombre' => 'B', 'edad' => 55],
]]);
t_true($idsRepetidos['personas'][0]['id'] !== $idsRepetidos['personas'][1]['id'],
    'Ids repetidos se separan: la foto de cada persona se guarda por id');

$lactante = sala_lactante();
t_true(Sala::persona($lactante, 'p2')['informante'], 'La madre queda de informante del lactante');
t_true(!Sala::persona($lactante, 'p1')['informante'], 'La guagua no es informante de sí misma');
t_true(Sala::persona($lactante, 'p2')['obligatorio'], 'A la madre no se le puede pedir que salga');

$conPadre = Sala::normalize(['personas' => [
    ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'Beni', 'edad' => 6, 'es_paciente' => true],
    ['id' => 'p2', 'rol' => 'padre', 'nombre' => 'Jorge', 'edad' => 40],
    ['id' => 'p3', 'rol' => 'abuelo', 'nombre' => 'Elsa', 'edad' => 70],
]]);
t_true(Sala::persona($conPadre, 'p2')['obligatorio'], 'Al padre no se le puede impedir estar (regla chilena)');
t_true(!Sala::persona($conPadre, 'p3')['obligatorio'], 'A la abuela sí se le puede pedir que espere afuera');

// -- Retrocompatibilidad: casos guardados antes del chat grupal ----------

$viejo = Sala::desde([
    'edad' => 45, 'gender' => 1,
    'PatientBehavior' => 'desconfiado', 'PatientDisposition' => -1,
], 'Marta', 45);
t_eq(count($viejo['personas']), 1, 'Caso sin sala: queda un chat 1 a 1 como antes');
t_eq($viejo['personas'][0]['nombre'], 'Marta', 'Y toma el nombre de la cita');
t_eq($viejo['personas'][0]['comportamiento'], 'desconfiado', 'Conserva el comportamiento que ya existía');
t_eq($viejo['personas'][0]['disposicion'], -1, 'Y la sensibilidad, que usa OIRS');

$conSala = Sala::desde(['Sala' => sala_lactante(), 'edad' => 1], 'Benjamín', 1);
t_eq(Sala::paciente($conSala)['nombre'], 'Benjamín',
    'El nombre real del paciente es el de la cita, no el guardado en la sala');

// -- Validación ---------------------------------------------------------

t_eq(Sala::problemas(sala_lactante()), [], 'Lactante con madre: sala válida');

$menorSolo = Sala::normalize(['personas' => [
    ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'Beni', 'edad' => 9, 'es_paciente' => true],
]]);
$problemas = Sala::problemas($menorSolo);
t_true(count($problemas) > 0, 'Menor de 14 sin acompañante: la sala está mal armada');
t_true(strpos($problemas[0], '14') !== false, 'Y el aviso nombra el límite legal');

// -- Motor de turnos ----------------------------------------------------

$t = Sala::turno(sala_lactante(), 'p2', '¿Desde cuándo le nota esto?', [], $nunca);
t_eq($t['destinatario']['id'], 'p2', 'Pregunta dirigida a la madre: contesta la madre');
t_eq(count($t['hablan']), 1, 'Y nadie más se mete');
t_eq($t['hablan'][0]['motivo'], 'responde', 'La madre sí maneja las fechas');

$t = Sala::turno(sala_lactante(), 'p1', '¿Cómo te llamas?', [], $nunca);
t_eq($t['hablan'][0]['motivo'], 'no_verbal', 'Le hablan a la guagua: solo hay conducta observable');
t_eq(count($t['hablan']), 2, 'Y la madre entra igual aunque el dado diga que no: si no, el turno queda vacío');
t_eq($t['hablan'][1]['persona']['id'], 'p2', 'Quien entra es la madre');
t_eq($t['hablan'][1]['motivo'], 'aporta_dato', 'Porque el dato no está al alcance de la guagua');

$t = Sala::turno(sala_lactante(), 'sala', 'Buenos días', [], $nunca);
t_eq($t['destinatario']['id'], 'p2', 'Preguntar al aire lo toma el informante principal');

// El niño de 10 puede contar lo que siente, pero no qué remedios toma.
$escolar = Sala::normalize(['personas' => [
    ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'Beni', 'edad' => 10, 'es_paciente' => true],
    ['id' => 'p2', 'rol' => 'madre', 'nombre' => 'Rosa', 'edad' => 38, 'interrumpe' => 0],
]]);
$t = Sala::turno($escolar, 'p1', '¿Te duele el oído?', [], $nunca);
t_eq(count($t['hablan']), 1, 'Al niño se le puede preguntar por lo que siente');
t_eq($t['hablan'][0]['motivo'], 'responde', 'Y contesta él');

$t = Sala::turno($escolar, 'p1', '¿Qué remedios estás tomando?', [], $nunca);
t_eq($t['hablan'][0]['motivo'], 'no_sabe', 'Los remedios no los sabe: lo dice, no los inventa');
t_eq($t['hablan'][1]['persona']['id'], 'p2', 'Y los aporta la madre, aunque su interrupción base sea 0');

// El caso de oro: el paciente niega, la esposa desmiente.
$t = Sala::turno(sala_negador(), 'p1', '¿Usted escucha bien?', [], $siempre);
t_eq(count($t['hablan']), 2, 'El paciente niega y la esposa se mete');
t_eq($t['hablan'][1]['motivo'], 'corrige', 'Porque él tiene baja conciencia de su problema');

$t = Sala::turno(sala_negador(), 'p1', '¿Usted escucha bien?', [], $nunca);
t_eq(count($t['hablan']), 1, 'Con el dado en contra no se mete: la interrupción no es determinista');

// Contención: la maniobra de entrevista que se quiere enseñar.
$t = Sala::turno(sala_negador(), 'p1', 'Señora, déjelo contestar a él por favor', [], $siempre);
t_eq(count($t['hablan']), 1, 'Contenida, la esposa no interrumpe ese turno');
t_eq($t['silenciados']['p2'], Sala::SILENCIO_TURNOS, 'Y queda callada por varios turnos');

$t2 = Sala::turno(sala_negador(), 'p1', '¿Y hace cuánto le pasa?', $t['silenciados'], $siempre);
t_eq(count($t2['hablan']), 1, 'Al turno siguiente sigue callada');
t_eq($t2['silenciados']['p2'], Sala::SILENCIO_TURNOS - 1, 'Pero le queda un turno menos de silencio');

$silencioPorVencer = Sala::turno(sala_negador(), 'p1', '¿Y escucha la tele fuerte?', ['p2' => 1], $siempre);
t_eq(count($silencioPorVencer['hablan']), 2, 'Cuando se acaba el silencio vuelve a meterse');

// Alguien fuera del box no habla ni recibe preguntas.
$afuera = sala_negador();
$afuera['personas'][1]['presente'] = false;
$t = Sala::turno($afuera, 'p2', '¿Usted qué nota en la casa?', [], $siempre);
t_eq($t['destinatario']['id'], 'p1', 'Si el destinatario salió del box, la pregunta la toma quien quedó');
t_eq(count($t['hablan']), 1, 'Y el que está afuera no interrumpe desde la sala de espera');

// -- Formulario del editor: ida y vuelta --------------------------------

$post = [
    'sala_aforo' => '3',
    'sala_informante' => 'p2',
    'paciente_conciencia' => '15',
    'paciente_confiabilidad' => '60',
    'sala_id' => ['p2', ''],
    'sala_rol' => ['conyuge', 'otro'],
    'sala_nombre' => ['Ana', ''],
    'sala_edad' => ['75', ''],
    'sala_genero' => ['1', '0'],
    'sala_interrumpe' => ['70', '20'],
    'sala_confiabilidad' => ['90', '80'],
    'sala_version' => ['sube la tele al maximo', ''],
    'sala_comportamiento' => ['contesta por el', ''],
    'sala_disposicion' => ['0', '0'],
];
$armada = Sala::fromForm($post, [
    'nombre' => 'Luis', 'edad' => 78, 'genero' => 0,
    'comportamiento' => 'tranquilo', 'disposicion' => -1,
]);
t_eq(count($armada['personas']), 2, 'La fila vacía del final del editor no crea un acompañante fantasma');
t_eq($armada['aforo'], 3, 'El aforo sale del formulario');
t_eq(Sala::paciente($armada)['conciencia'], 15, 'La conciencia del paciente se guarda');
t_eq(Sala::paciente($armada)['comportamiento'], 'tranquilo',
    'El comportamiento del paciente sigue viniendo de Anamnesis, no de la sala');
t_true(Sala::persona($armada, 'p2')['informante'], 'La esposa quedó de informante principal');
t_true(!Sala::paciente($armada)['informante'], 'Y el paciente dejó de serlo');

$deVuelta = Sala::toForm($armada);
t_eq($deVuelta['sala_informante'], 'p2', 'El editor repinta marcada a la informante');
t_eq($deVuelta['paciente_conciencia'], '15', 'Y la conciencia tal como se guardó');
t_eq(count($deVuelta['acompanantes']), 1, 'El paciente no aparece entre los acompañantes');
t_eq($deVuelta['acompanantes'][0]['nombre'], 'Ana', 'La acompañante vuelve con su nombre');

// El id viaja en el formulario: borrar una fila de más arriba no le puede
// correr la foto (que se guarda por id) al que queda.
$postSinPrimero = [
    'sala_id' => ['aXYZ'],
    'sala_rol' => ['abuelo'],
    'sala_nombre' => ['Elsa'],
    'sala_edad' => ['70'],
];
$sala2 = Sala::fromForm($postSinPrimero, ['nombre' => 'Beni', 'edad' => 6]);
t_eq($sala2['personas'][1]['id'], 'aXYZ', 'El id del acompañante es el del formulario, no su posición');

// -- Bloque de sala del prompt ------------------------------------------
// Es lo que se le pega a cada personaje para que no escriba los diálogos de
// los demás ni conteste lo que no le toca.

require_once __DIR__ . '/../src/LlmConfig.php';

$bloque = LlmConfig::bloqueSala(Sala::persona(sala_lactante(), 'p1'), sala_lactante(), 'no_verbal');
t_true(strpos($bloque, 'Rosa (Madre)') !== false, 'El prompt dice quién más está en el box');
t_true(strpos($bloque, 'eres tú') !== false, 'Y cuál de todos es el personaje');
t_true(strpos($bloque, 'guagua') !== false, 'A un lactante se le dice que no habla');
t_true(strpos($bloque, 'entre paréntesis') !== false, 'Y que solo devuelva conducta observable');

$bloqueEsposa = LlmConfig::bloqueSala(Sala::persona(sala_negador(), 'p2'), sala_negador(), 'corrige');
t_true(strpos($bloqueEsposa, 'minimizando o negando') !== false,
    'A quien corrige se le dice por qué le toca hablar');
t_true(strpos($bloqueEsposa, 'Hablas SOLO por ti') !== false,
    'Y a todos, que no escriban lo que dicen los demás');

$bloqueNegador = LlmConfig::bloqueSala(Sala::persona(sala_negador(), 'p1'), sala_negador(), 'responde');
t_true(strpos($bloqueNegador, 'No crees tener un problema') !== false,
    'Con conciencia baja, el paciente niega lo suyo');

// Contener sin haber elegido destinatario: el alumno le habla al aire y la
// que contestaba era la esposa. "Déjelo contestar a él" tiene que devolverle
// la palabra al paciente, no dejar la sala muda.
// La informante es ella, que es lo que pasa en la consulta real con el
// viejito que no escucha: la señora toma la palabra.
$hablaElla = Sala::normalize(['personas' => [
    ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'Luis', 'edad' => 78,
     'es_paciente' => true, 'conciencia' => 10],
    ['id' => 'p2', 'rol' => 'conyuge', 'nombre' => 'Ana', 'edad' => 75, 'genero' => 1,
     'interrumpe' => 80, 'informante' => true],
]]);
t_eq(Sala::turno($hablaElla, '', '¿Usted escucha bien?', [], $nunca)['destinatario']['id'], 'p2',
    'Al aire contesta ella, que es la informante');
$contieneAlAire = Sala::turno($hablaElla, '', 'Señora, déjelo contestar a él', [], $siempre);
t_eq($contieneAlAire['destinatario']['id'], 'p1', 'La contención al aire le devuelve el turno al paciente');
t_eq(count($contieneAlAire['hablan']), 1, 'Y la esposa no se mete ese turno');
t_eq($contieneAlAire['silenciados']['p2'], Sala::SILENCIO_TURNOS, 'Queda contenida por varios turnos');
