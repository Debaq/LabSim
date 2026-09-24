<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/ReportRevision.php';

/**
 * Revisión de un informe de ABR con la atención ya cerrada: entran marcas y
 * conclusiones, las curvas quedan como se registraron.
 */

$guardado = [
    'curvas' => [
        'R1' => [
            'int' => 80, 'average' => 2000,
            'traza' => ['t' => [0, 1], 'ipsi' => [0.1, 0.2]],
            'tecnica' => ['barridos_presentados' => 2000],
            'LatAmp' => ['V' => [null, null]],
            'marcas_graf' => [],
        ],
        'R2' => [
            'int' => 60,
            'traza' => ['t' => [0, 1], 'ipsi' => [0.0, 0.1]],
            'LatAmp' => ['V' => [6.1, 0.3]],
        ],
    ],
    'tecnica' => ['montaje' => 'Cz-A1'],
    'hallazgos' => '',
    'conclusion' => '',
];

$entrante = [
    'curvas' => [
        'R1' => [
            'int' => 20,                                  // no se puede
            'traza' => ['t' => [0, 1], 'ipsi' => [9, 9]], // no se puede
            'LatAmp' => ['V' => [5.6, 0.5]],
            'marcas_graf' => ['V' => [5.6, 0.48]],
        ],
        'R9' => ['int' => 40, 'traza' => ['t' => [0], 'ipsi' => [1]]], // curva nueva
    ],
    'tecnica' => ['montaje' => 'otro'],
    'hallazgos' => 'V presente a 80',
    'conclusion' => 'Normal',
];

$r = ReportRevision::fusionar($guardado, $entrante, '2026-09-24T10:00:00');

t_eq($r['curvas']['R1']['LatAmp']['V'], [5.6, 0.5], 'las marcas de la curva entran');
t_eq($r['curvas']['R1']['marcas_graf']['V'], [5.6, 0.48], 'las marcas del gráfico entran');
t_eq($r['curvas']['R1']['traza']['ipsi'], [0.1, 0.2], 'el trazo registrado no cambia');
t_eq($r['curvas']['R1']['int'], 80, 'el setting de la curva no cambia');
t_eq($r['curvas']['R1']['tecnica'], ['barridos_presentados' => 2000], 'la técnica de la curva no cambia');
t_true(!isset($r['curvas']['R9']), 'una curva que no se registró no entra');
t_eq($r['curvas']['R2']['LatAmp']['V'], [6.1, 0.3], 'la curva que no vino se conserva');
t_eq($r['tecnica'], ['montaje' => 'Cz-A1'], 'la técnica del informe no cambia');
t_eq($r['hallazgos'], 'V presente a 80', 'los hallazgos entran');
t_eq($r['conclusion'], 'Normal', 'la conclusión entra');
t_eq($r['revisiones'], ['2026-09-24T10:00:00'], 'queda anotado que se revisó');

$r2 = ReportRevision::fusionar($r, ['conclusion' => 'Normal bilateral'], '2026-09-25T09:00:00');
t_eq($r2['revisiones'], ['2026-09-24T10:00:00', '2026-09-25T09:00:00'], 'las revisiones se acumulan');
t_eq($r2['curvas']['R1']['LatAmp']['V'], [5.6, 0.5], 'sin curvas en lo que llega, las marcas quedan');

t_true(ReportRevision::admite('ABR'), 'el ABR se revisa');
t_true(ReportRevision::admite('ELECTROCOCLEO'), 'el ECochG se revisa');
t_true(!ReportRevision::admite('VEMP'), 'el resto sigue fijo al cerrar');
