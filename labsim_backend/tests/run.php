<?php

declare(strict_types=1);

/**
 * Runner de tests del backend. `php labsim_backend/tests/run.php`.
 *
 * Plano a propósito: sin composer ni PHPUnit. El backend no tiene ninguna
 * dependencia externa hoy (se despliega copiando archivos a un hosting con
 * PHP y nada más) y agregar un gestor de paquetes solo para esto cambiaría
 * cómo se instala el proyecto entero.
 *
 * Cada archivo tests/test_*.php se incluye y llama a t_eq()/t_true(). El
 * proceso sale con código 1 si algo falla, así sirve en CI.
 */

$GLOBALS['__t'] = ['ok' => 0, 'fail' => []];

function t_eq($actual, $expected, string $msg): void
{
    if ($actual == $expected) {
        $GLOBALS['__t']['ok']++;
        return;
    }
    $GLOBALS['__t']['fail'][] = sprintf(
        "%s\n    esperado: %s\n    obtenido: %s",
        $msg,
        var_export($expected, true),
        var_export($actual, true)
    );
}

function t_true($cond, string $msg): void
{
    t_eq((bool) $cond, true, $msg);
}

/** Igualdad con tolerancia, para los dB y ms que salen de una división. */
function t_close(float $actual, float $expected, float $tol, string $msg): void
{
    if (abs($actual - $expected) <= $tol) {
        $GLOBALS['__t']['ok']++;
        return;
    }
    $GLOBALS['__t']['fail'][] = sprintf(
        "%s\n    esperado: %s (±%s)\n    obtenido: %s",
        $msg, (string) $expected, (string) $tol, (string) $actual
    );
}

foreach (glob(__DIR__ . '/test_*.php') ?: [] as $archivo) {
    require $archivo;
}

$t = $GLOBALS['__t'];
if ($t['fail'] === []) {
    printf("OK -- %d asserts\n", $t['ok']);
    exit(0);
}
printf("FALLARON %d de %d asserts:\n\n", count($t['fail']), $t['ok'] + count($t['fail']));
foreach ($t['fail'] as $f) {
    echo "  - $f\n\n";
}
exit(1);
