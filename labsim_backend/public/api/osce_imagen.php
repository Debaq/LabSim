<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/OscePreguntas.php';

/**
 * Imagen de una pregunta técnica del OSCE. Sin sesión, como la tablet: se
 * pide con el token de la estación (?k=) y el id de la pregunta (?q=), y
 * solo sale si la pregunta es de esa estación. El docente la ve con el
 * mismo enlace desde el editor.
 */

$est = OscePreguntas::estacionPorToken((string) ($_GET['k'] ?? ''));
$q = $est !== null ? OscePreguntas::pregunta((int) $est['id'], (int) ($_GET['q'] ?? 0)) : null;
$ruta = $q !== null ? OscePreguntas::rutaImagen($q) : null;
if ($ruta === null) {
    http_response_code(404);
    exit;
}
$tipos = ['png' => 'image/png', 'jpg' => 'image/jpeg', 'gif' => 'image/gif', 'webp' => 'image/webp'];
header('Content-Type: ' . $tipos[pathinfo($ruta, PATHINFO_EXTENSION)]);
header('Content-Length: ' . filesize($ruta));
header('Cache-Control: private, max-age=3600');
header('X-Content-Type-Options: nosniff');
readfile($ruta);
