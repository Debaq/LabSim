<?php

declare(strict_types=1);

/**
 * Errores de JavaScript de las tablets kiosko (kiosko/kiosko.js los manda
 * con window.onerror). En esas tablets no hay depuración remota: esto es lo
 * único que avisa de una falla. Va al log de PHP y no devuelve nada útil.
 */

header('Cache-Control: no-store');
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $corto = static fn ($s, int $n): string => substr(preg_replace('/[\x00-\x1f]+/', ' ', (string) $s), 0, $n);
    error_log(sprintf('[kiosko js] %s | %s:%d | %s', $corto($_POST['msg'] ?? '', 300), $corto($_POST['url'] ?? '', 200),
                      (int) ($_POST['linea'] ?? 0), $corto($_SERVER['HTTP_USER_AGENT'] ?? '', 160)));
}
http_response_code(204);
