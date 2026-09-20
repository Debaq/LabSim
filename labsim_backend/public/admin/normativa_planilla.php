<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

// La planilla de referencia del ABR (483 filas, 27 fuentes) tal cual, para
// que el docente la revise o la extienda. Va por acá y no desde public/
// directo porque es material de la asignatura, no un asset del sitio: pide
// sesión de administración como cualquier otra pantalla de configuración.

Auth::requireAdminSession();
require_once __DIR__ . '/../../src/AbrReferences.php';

$ruta = AbrReferences::planilla();
if ($ruta === null) {
    http_response_code(404);
    exit('La planilla no está en este despliegue.');
}

header('Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet');
header('Content-Disposition: attachment; filename="ABR_valores_referencia.xlsx"');
header('Content-Length: ' . (string) filesize($ruta));
readfile($ruta);
