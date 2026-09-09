<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Sala.php';

/**
 * El elenco del caso: quién viene con el paciente y qué sabe cada uno (ver
 * Sala.php).
 *
 * Acá NO se prueba quién contesta cada pregunta: eso lo decide el modelo
 * leyendo la conversación, no este código. Lo que se prueba es lo que sí es
 * determinista y le llega al modelo como ficha: la capacidad de relato por
 * edad, las invariantes de la sala y lo que el docente cargó en el editor.
 */

/** Sala de lactante: guagua de 1 año + madre. El caso pediátrico base. */
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
         'es_paciente' => true, 'conciencia' => 10, 'confiabilidad' => 30],
        ['id' => 'p2', 'rol' => 'conyuge', 'nombre' => 'Ana', 'edad' => 75, 'genero' => 1,
         'interrumpe' => 80, 'informante' => true,
         'version' => 'no escucha nada hace años y sube la tele al máximo'],
    ]]);
}

// -- Capacidad de relato por edad ---------------------------------------

t_eq(Sala::capacidad(1), Sala::CAP_NULO, 'Guagua de 1 año: no habla');
t_eq(Sala::capacidad(2), Sala::CAP_NULO, 'A los 2 todavía no cuenta su historia');
t_eq(Sala::capacidad(4), Sala::CAP_MINIMO, 'A los 4 dice su nombre y dónde le duele');
t_eq(Sala::capacidad(10), Sala::CAP_PARCIAL, 'A los 10 cuenta síntomas, no fechas ni remedios');
t_eq(Sala::capacidad(15), Sala::CAP_CASI_TOTAL, 'A los 15 cuenta casi todo lo suyo');
t_eq(Sala::capacidad(40), Sala::CAP_TOTAL, 'El adulto cuenta su historia completa');

t_eq(Sala::nivelInterrupcion(0), 'nada', 'En 0 espera su turno');
t_eq(Sala::nivelInterrupcion(20), 'poco', 'En 20 rara vez se mete');
t_eq(Sala::nivelInterrupcion(50), 'medio', 'En 50 se mete cuando el otro no sabe');
t_eq(Sala::nivelInterrupcion(80), 'mucho', 'En 80 contesta por el paciente');

// -- Invariantes que el resto del código da por ciertas ------------------

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
    'Ids repetidos se separan: la foto de cada persona se guarda por id, y el modelo la nombra por id');

$lactante = sala_lactante();
t_true(Sala::persona($lactante, 'p2')['informante'], 'La madre lleva la voz cantante del lactante');
t_true(!Sala::persona($lactante, 'p1')['informante'], 'La guagua no cuenta su propia historia');
t_true(Sala::tieneAcompanantes($lactante), 'Con madre, la consulta es acompañada');

$soloAdulto = Sala::normalize(['personas' => [
    ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'Marta', 'edad' => 45, 'es_paciente' => true],
]]);
t_true(!Sala::tieneAcompanantes($soloAdulto),
    'Paciente solo: sigue el chat 1 a 1 de siempre, sin prompt de sala ni JSON');

// -- Retrocompatibilidad: casos guardados antes de esto ------------------

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
// A propósito casi no hay: quién acompaña a quién son recomendaciones, no
// requisitos, y un menor se atiende solo si se puede atender solo.

t_eq(Sala::problemas(sala_lactante()), [], 'Lactante con madre: sala válida');

$menorSolo = Sala::normalize(['personas' => [
    ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'Beni', 'edad' => 9, 'es_paciente' => true],
]]);
t_eq(Sala::problemas($menorSolo), [],
    'Un menor que viene solo no es un caso incompleto: no hay regla que lo impida');

$adolescenteSolo = Sala::normalize(['personas' => [
    ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'Cata', 'edad' => 15, 'es_paciente' => true],
]]);
t_eq(Sala::problemas($adolescenteSolo), [], 'Ni un adolescente solo');

// Lo único que sí deja el ejercicio sin salida: nadie puede hablar.
$guaguaSola = Sala::normalize(['personas' => [
    ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'Benja', 'edad' => 1, 'es_paciente' => true],
]]);
$problemas = Sala::problemas($guaguaSola);
t_eq(count($problemas), 1, 'Una guagua sola deja al alumno sin nadie a quien preguntarle');
t_true(strpos($problemas[0], 'viene solo') !== false, 'Y el aviso dice por qué');

// Marcar de informante a quien no habla se corrige solo, sin avisar: el
// prompt no puede decir que lleva la voz cantante alguien que no habla.
$guaguaInformante = Sala::normalize(['personas' => [
    ['id' => 'p1', 'rol' => 'paciente', 'nombre' => 'Benja', 'edad' => 1,
     'es_paciente' => true, 'informante' => true],
    ['id' => 'p2', 'rol' => 'madre', 'nombre' => 'Rosa', 'edad' => 32],
]]);
t_true(Sala::persona($guaguaInformante, 'p2')['informante'],
    'Marcar de informante a una guagua pasa la voz cantante a la madre');
t_eq(Sala::problemas($guaguaInformante), [], 'Y no queda nada pendiente por eso');

// -- Formulario del editor: ida y vuelta --------------------------------

$post = [
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
t_eq(Sala::paciente($armada)['conciencia'], 15, 'La conciencia del paciente se guarda');
t_eq(Sala::paciente($armada)['comportamiento'], 'tranquilo',
    'El comportamiento del paciente sigue viniendo de Anamnesis, no de la sala');
t_true(Sala::persona($armada, 'p2')['informante'], 'La esposa quedó llevando la voz cantante');
t_true(!Sala::paciente($armada)['informante'], 'Y el paciente dejó de llevarla');

$deVuelta = Sala::toForm($armada);
t_eq($deVuelta['sala_informante'], 'p2', 'El editor repinta marcada a la informante');
t_eq($deVuelta['paciente_conciencia'], '15', 'Y la conciencia tal como se guardó');
t_eq(count($deVuelta['acompanantes']), 1, 'El paciente no aparece entre los acompañantes');
t_eq($deVuelta['acompanantes'][0]['nombre'], 'Ana', 'La acompañante vuelve con su nombre');

// El id viaja en el formulario: borrar una fila de más arriba no le puede
// correr la foto (que se guarda por id) al que queda.
$sala2 = Sala::fromForm(
    ['sala_id' => ['aXYZ'], 'sala_rol' => ['abuelo'], 'sala_nombre' => ['Elsa'], 'sala_edad' => ['70']],
    ['nombre' => 'Beni', 'edad' => 6]
);
t_eq($sala2['personas'][1]['id'], 'aXYZ', 'El id del acompañante es el del formulario, no su posición');

// -- Ficha que se le pasa al modelo -------------------------------------
// Es lo único que fija el caso: quién es cada uno y qué sabe. Quién habla
// en cada turno lo decide el modelo con esto a la vista.

require_once __DIR__ . '/../src/LlmConfig.php';

$fichas = LlmConfig::fichasDeSala(sala_negador());
t_true(strpos($fichas, 'id "p1"') !== false, 'Cada persona va con el id con el que el modelo la nombra');
t_true(strpos($fichas, 'Ana (Cónyuge / pareja), 75 años') !== false, 'Con su nombre, su parentesco y su edad');
t_true(strpos($fichas, 'No cree tener un problema') !== false,
    'Con conciencia baja, el paciente niega lo suyo');
t_true(strpos($fichas, 'relato es impreciso') !== false,
    'Con confiabilidad baja, confunde fechas pero las cuenta con seguridad');
t_true(strpos($fichas, 'contestar por el paciente') !== false,
    'La tendencia a interrumpir se le dice en palabras, no como número');
t_true(strpos($fichas, 'sube la tele al máximo') !== false, 'Y su versión de los hechos, tal cual');
t_true(strpos($fichas, 'voz cantante') !== false, 'Se dice quién contesta si preguntan al aire');

$fichasBebe = LlmConfig::fichasDeSala(sala_lactante());
t_true(strpos($fichasBebe, 'guagua') !== false, 'A un lactante se le dice que no habla');
t_true(strpos($fichasBebe, 'entre paréntesis') !== false, 'Y que lo suyo es conducta observable');
t_true(strpos($fichasBebe, 'Sabe lo que el paciente no puede saber') !== false,
    'A la madre se le dice que ella sí maneja fechas, remedios y parto');
