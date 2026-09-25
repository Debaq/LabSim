<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/AppReleases.php';

/**
 * Versiones de la app de escritorio (ver AppReleases): el cliente pregunta
 * acá si hay una nueva en vez de ir a la API de GitHub, que deja 60
 * consultas por hora por IP y el laboratorio comparte una.
 *
 * Anónimo a propósito, como layout.php: se pide al arrancar, antes del
 * login. Es lo mismo que publica el repo en GitHub.
 *
 * 503 si no hay una lista confiable (GitHub no respondió y la guardada es
 * muy vieja): el cliente cae a consultar GitHub él mismo.
 */

$lista = AppReleases::lista();
if ($lista === null) {
    Response::error('Sin lista de versiones reciente', 503);
}
Response::json([
    'consultado' => gmdate('Y-m-d\TH:i:s\Z', $lista['consultado']),
    'releases' => $lista['releases'],
]);
