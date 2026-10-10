<?php

declare(strict_types=1);

/**
 * AudiometriaTecnicaGrafico: los gráficos sin palabras de "Tu última
 * atención" (lti/launch.php).
 */

require_once dirname(__DIR__) . '/src/AudiometriaTecnicaGrafico.php';

function grafico_fila(int $hz, ?int $est, string $estado, array $extra = []): array
{
    return $extra + [
        'freq' => $hz, 'repeticion' => false, 'innecesaria' => false, 'estimado' => $est, 'aprox' => $est,
        'real' => 77, 'sombra' => 33, 'con_ruido' => false, 'sin_respuesta' => false, 'maximo' => 120,
        'estado' => $estado,
    ];
}

$tecnica = [
    'orden' => ['reglas' => [['texto' => 'Orden', 'cumple' => true]]],
    'aereos' => [
        'reglas' => [['texto' => 'Instrucción', 'cumple' => true], ['texto' => 'No aplica', 'cumple' => null]],
        'oidos' => ['OD' => [['texto' => 'Repite 1 kHz', 'cumple' => false]]],
        'umbrales' => [
            'OD' => [grafico_fila(1000, 40, 'coincide'), grafico_fila(2000, 50, 'sombra'), grafico_fila(1000, 45, 'coincide', ['repeticion' => true])],
            'OI' => [grafico_fila(4000, null, 'coincide', ['sin_respuesta' => true])],
        ],
    ],
    'oseos' => ['reglas' => [], 'umbrales' => []],
];

$svg = AudiometriaTecnicaGrafico::audiograma($tecnica);
t_eq(substr_count($svg, 'fill-opacity="0.4"'), 1, 'Gráfico técnica: solo el umbral que no corresponde lleva halo');
t_true(strpos($svg, '2 kHz · 50 dB · curva sombra') !== false, 'Gráfico técnica: el halo es del umbral en curva sombra');
t_true(strpos($svg, '1 kHz · 45 dB') !== false && strpos($svg, '1 kHz · 40 dB') === false,
    'Gráfico técnica: de 1 kHz vale la repetición, la última vez que lo tomó');
t_true(strpos($svg, '77 dB') === false && strpos($svg, '33 dB') === false,
    'Gráfico técnica: nunca dibuja el umbral real ni el de la sombra (sería la respuesta)');
t_true(strpos($svg, '4 kHz · 120 dB') !== false, 'Gráfico técnica: sin respuesta va en el tope que alcanzó');

$pasos = AudiometriaTecnicaGrafico::pasos($tecnica);
t_eq(substr_count($pasos, '<rect '), 3, 'Gráfico técnica: un cuadrito por regla evaluable (la que no aplica no)');
t_eq(substr_count($pasos, '#c0392b'), 1, 'Gráfico técnica: la regla no cumplida va en rojo');
t_eq(AudiometriaTecnicaGrafico::pasos(['orden' => ['reglas' => []]]), '', 'Gráfico técnica: sin reglas no hay fila');
