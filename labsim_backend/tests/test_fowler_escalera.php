<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/CaseBuilder.php';

/**
 * La escalera del Fowler que dibuja la ficha (CaseBuilder::fowlerEscalera)
 * es la que da el motor de la cabina (src/audiometria/Fowler.py): el sano de
 * 20 en 20 desde su umbral, el afectado de 5 en 5 hasta igualar.
 */

// Sin reclutamiento: paralelas, la diferencia interaural se mantiene.
t_eq(CaseBuilder::fowlerEscalera(5, 25, 'none', 115, 115),
    [[5, 25], [25, 45], [45, 65], [65, 85], [85, 105]],
    'Fowler sin reclutamiento: escalones paralelos hasta el techo del oído afectado');

// El oído sano puede ser el OI: los pares siguen siendo [OD, OI].
t_eq(CaseBuilder::fowlerEscalera(35, 5, 'none', 120, 115)[1], [55, 25],
    'Fowler con referencia OI: el par va [OD, OI]');

// El sano no pasa de su LDL: con LDL 60 el último escalón es 45.
t_eq(count(CaseBuilder::fowlerEscalera(5, 25, 'none', 60, 120)), 3,
    'Fowler: el oído sano se detiene antes de su LDL');

// Los patrones con reclutamiento: la diferencia de 20 dB sigue paralela
// hasta 15 dB sobre el umbral del sano y desde ahí se achica.
t_eq(CaseBuilder::fowlerEscalera(5, 25, 'partial', 120, 120),
    [[5, 25], [25, 45], [45, 55], [65, 75], [85, 95], [105, 115]],
    'Fowler parcial: la diferencia baja a la mitad y no cierra');
t_eq(CaseBuilder::fowlerEscalera(5, 25, 'complete', 120, 120),
    [[5, 25], [25, 45], [45, 55], [65, 65], [85, 85], [105, 105]],
    'Fowler completo: iguala al mismo nivel desde el final del reclutamiento');
t_eq(CaseBuilder::fowlerEscalera(5, 25, 'over', 120, 120),
    [[5, 25], [25, 45], [45, 55], [65, 65], [85, 80], [105, 100]],
    'Fowler sobre-reclutamiento: el afectado iguala 5 dB bajo el sano');
t_eq(CaseBuilder::fowlerEscalera(40, 10, 'complete', 120, 120),
    [[40, 10], [60, 30], [70, 50], [80, 70], [90, 90], [110, 110]],
    'Fowler completo con referencia OI');
