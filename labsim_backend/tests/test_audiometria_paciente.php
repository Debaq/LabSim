<?php

declare(strict_types=1);

/**
 * AudiometriaPaciente (copia en PHP de response.py) da la misma mano que el
 * cliente en los casos de referencia. El mismo fixture lo corre
 * tests/test_audiometria_paciente.py contra response.py.
 */

require_once dirname(__DIR__) . '/src/AudiometriaPaciente.php';
require_once dirname(__DIR__) . '/src/AudiometriaRegistro.php';

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

// --- "Withe Noise": el rótulo viejo de la app sigue leyéndose ---------------

t_eq(AudiometriaPaciente::estimulo('Withe Noise'), 'White Noise', 'Estímulo: el rótulo viejo se traduce al de hoy');
t_eq(AudiometriaPaciente::estimulo('Pink Noise'), 'Pink Noise', 'Estímulo: los demás quedan igual');

// Una presentación con ruido en el otro canal, en un registro viejo (con
// "Withe Noise") y en uno nuevo: el ruido se reconoce igual en los dos.
$wnRegistro = static function (string $rotulo): array {
    $estado = [
        'prueba' => 'Umbrales', 'freq' => '1000 Hz', 'step' => 5, 'instruccion' => 'aerea_+_ruido',
        'canales' => [
            ['on' => false, 'invertido' => false, 'intensity' => '40 dB HL', 'stim' => 'Tono', 'output' => 'Derecha', 'trans' => 'Aerea', 'contin' => 'Continuo'],
            ['on' => true, 'invertido' => true, 'intensity' => '50 dB HL', 'stim' => $rotulo, 'output' => 'Izquierda', 'trans' => 'Aerea', 'contin' => 'Continuo'],
        ],
    ];
    $base = ['ch' => 0, 'freq' => '1000 Hz', 'intensity' => '40 dB HL', 'stim' => 'Tono', 'output' => 'Derecha', 'trans' => 'Aerea',
             'appointment_id' => 7, 'case_id' => 3, 'v' => 2];
    $logs = [
        ['client_ts' => '2026-10-08 10:00:00.000', 'action' => 'audio_talkback_press', 'payload' => ['command' => 'aerea_+_ruido', 'v' => 2]],
        ['client_ts' => '2026-10-08 10:00:01.000', 'action' => 'audio_stim_button', 'payload' => $base + ['play' => true, 'estado' => $estado]],
        ['client_ts' => '2026-10-08 10:00:02.500', 'action' => 'audio_stim_button', 'payload' => $base + ['play' => false, 'estado' => $estado]],
    ];
    $r = AudiometriaRegistro::leer($logs, at_caso_wn());
    return $r['presentaciones'][0]['ruido'] ?? [];
};
function at_caso_wn(): array
{
    $par = array_fill(0, 9, [10, 10]);
    return ['Aerea' => $par, 'Osea' => $par, 'Aerea_mkg' => $par, 'Osea_mkg' => $par, 'Z_OD' => 'A', 'Z_OI' => 'A'];
}
$wnViejo = $wnRegistro('Withe Noise');
$wnNuevo = $wnRegistro('White Noise');
t_eq($wnViejo['stim'] ?? null, 'White Noise', 'Registro viejo: el ruido "Withe Noise" se reconoce como White Noise');
t_eq($wnViejo, $wnNuevo, 'Registro viejo y nuevo: el mismo ruido');
