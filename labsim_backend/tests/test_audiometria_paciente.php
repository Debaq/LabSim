<?php

declare(strict_types=1);

/**
 * AudiometriaPaciente (copia en PHP de response.py) da la misma mano que el
 * cliente en los casos de referencia. El mismo fixture lo corre
 * tests/test_audiometria_paciente.py contra response.py.
 */

require_once dirname(__DIR__) . '/src/AudiometriaPaciente.php';

$datos = json_decode((string) file_get_contents(__DIR__ . '/fixtures/audiometria_paciente.json'), true);
t_true(count($datos['escenas']) >= 15, 'Paciente: el fixture tiene los casos de referencia');
foreach ($datos['escenas'] as $e) {
    $paciente = new AudiometriaPaciente($datos['casos'][$e['caso']]);
    t_eq($paciente->mano($e['estado'], $e['previa']), $e['esperado'], "Paciente: {$e['nombre']}");
}

// Lo que no se reconstruye (supraliminares) vuelve null, no una mano inventada.
$caso = $datos['casos']['sn_oi'];
$estado = [
    'prueba' => 'Umbrales', 'freq_idx' => 3, 'instruccion' => 'mano_levantada',
    'canales' => [
        ['on' => true, 'int' => 60, 'output' => 1, 'trans' => 0, 'stim' => 0],
        ['on' => false, 'int' => 20, 'output' => 0, 'trans' => 0, 'stim' => 3],
    ],
];
t_eq((new AudiometriaPaciente($caso))->mano($estado, false), null, 'Paciente: Carhart no se reconstruye');
