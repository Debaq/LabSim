<?php

declare(strict_types=1);

/**
 * El backend corre en PHP 7.4 y se desarrolla en PHP 8.
 *
 * Nada avisa de la diferencia: el código se escribe y se testea en una
 * máquina con PHP 8, pasa el lint, pasa los tests, y revienta recién en el
 * hosting con "Call to undefined function". Pasó con str_starts_with() en
 * el PDF de la ficha, y la única forma de que no vuelva a pasar es que el
 * runner lo cace acá.
 *
 * El piso es 7.4 y no 7.0 porque el código ya usa propiedades tipadas
 * (MiniPdf) y arrow functions (HistoriaClinica), que son de 7.4. Si algún
 * día el hosting sube a PHP 8, este archivo se borra entero.
 *
 * Esto es una red, no una garantía: caza las formas que ya mordieron, no
 * todo PHP 8. La comprobación completa es parsear con un 7.4 de verdad:
 *
 *   podman run --rm -v "$PWD":/app:ro -w /app docker.io/library/php:7.4-cli \
 *     sh -c 'for f in $(find src public -name "*.php"); do php -l "$f" >/dev/null || echo "FALLA $f"; done'
 */

/**
 * Sintaxis de PHP 8.0+ que en 7.4 es un fatal (o, peor, un parse error que
 * se lleva el archivo entero). Regex para no confundir `match (` con
 * `preg_match (`.
 */
const PHP8_PROHIBIDO = [
    '/\bstr_contains\s*\(/' => 'str_contains() es de PHP 8.0 -- usar strpos(...) !== false',
    '/\bstr_starts_with\s*\(/' => 'str_starts_with() es de PHP 8.0 -- usar strpos(...) === 0',
    '/\bstr_ends_with\s*\(/' => 'str_ends_with() es de PHP 8.0 -- usar substr(...) === ...',
    '/\barray_is_list\s*\(/' => 'array_is_list() es de PHP 8.1',
    '/\bget_debug_type\s*\(/' => 'get_debug_type() es de PHP 8.0 -- usar gettype()',
    '/(?<![_a-zA-Z0-9$>])match\s*\(/' => 'match es de PHP 8.0 -- usar switch',
    '/\?->/' => 'el operador nullsafe ?-> es de PHP 8.0',
    '/^\s*enum\s+[A-Za-z_]/' => 'enum es de PHP 8.1',
    '/,\s*\)\s*:?\s*[a-zA-Z?]*\s*$/m' => 'coma final en una lista de parámetros: es de PHP 8.0',
];

$raiz = dirname(__DIR__);
$archivos = [];
// views/ también corre en el hosting (lo incluye case_create.php), y `php -l`
// no lo salva: una llamada a str_contains() PARSEA bien y falla recién al
// ejecutarse. tests/ queda afuera a propósito: no se despliega.
foreach (['src', 'public', 'views'] as $dir) {
    $iter = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($raiz . '/' . $dir));
    foreach ($iter as $archivo) {
        if ($archivo->isFile() && $archivo->getExtension() === 'php') {
            $archivos[] = $archivo->getPathname();
        }
    }
}

t_true(count($archivos) > 20, 'El escaneo encuentra los .php del backend');
t_true(count(array_filter($archivos, static fn (string $r): bool => strpos($r, '/views/') !== false)) > 0,
    'El escaneo incluye las vistas, que también corren en el hosting');

// Un solo assert con TODOS los hallazgos: si falla, el mensaje lista archivo,
// línea y qué usar en su lugar, que es lo que hace falta para arreglarlo.
$hallazgos = [];
foreach ($archivos as $ruta) {
    $relativa = str_replace($raiz . '/', '', $ruta);
    $lineas = preg_split('/\r\n|\r|\n/', (string) file_get_contents($ruta)) ?: [];
    foreach ($lineas as $n => $linea) {
        // Los comentarios no se cuentan: uno que NOMBRA la función (como el
        // de CaseSheetPdf explicando por qué no la usa) no es una llamada.
        $limpia = ltrim($linea);
        if ($limpia === '' || $limpia[0] === '*' || $limpia[0] === '#' || strncmp($limpia, '//', 2) === 0) {
            continue;
        }
        foreach (PHP8_PROHIBIDO as $patron => $porque) {
            if (preg_match($patron, $linea) === 1) {
                $hallazgos[] = sprintf('%s:%d -- %s', $relativa, $n + 1, $porque);
            }
        }
    }
}
t_eq($hallazgos, [], 'El backend se mantiene dentro de PHP 7.4, que es lo que corre el hosting');
