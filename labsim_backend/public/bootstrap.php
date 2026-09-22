<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Clock.php';

// La zona del intérprete se fija ACÁ, antes de cualquier otra cosa: de otro
// modo `date()` usa la del php.ini del hosting y el mismo código da fechas
// distintas en el servidor y en desarrollo (ver Clock). Se guarda la que
// traía el servidor porque es el único momento en que se puede ver, y es
// justamente lo que el reloj de Estado informa.
$GLOBALS['ZONA_PHP_INI'] = Clock::pin();

require_once __DIR__ . '/../src/Db.php';
require_once __DIR__ . '/../src/AppConfig.php';
require_once __DIR__ . '/../src/Response.php';
require_once __DIR__ . '/../src/Auth.php';
require_once __DIR__ . '/../src/Lti.php';
require_once __DIR__ . '/../src/Cases.php';
require_once __DIR__ . '/../src/Courses.php';
require_once __DIR__ . '/../src/Layout.php';
