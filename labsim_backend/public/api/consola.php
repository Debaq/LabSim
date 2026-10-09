<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Backups.php';
require_once __DIR__ . '/../../src/Consola.php';

/**
 * Consola remota (ver src/Consola.php). POST JSON con
 * Authorization: Bearer lsc_... (token generado en admin/consola.php).
 *
 *   {"sql": "SELECT ...", "params": [..] o {..}}   una sentencia, con filas
 *   {"script": "UPDATE ...; DELETE ...;"}          varias, en una transacción
 *   {"accion": "esquema"}                          CREATE de toda la base
 *   {"accion": "backup"}                           copia de la base (data/backups/)
 *   {"accion": "archivos", "ruta": "tickets"}      listado dentro de data/
 *   {"accion": "leer", "ruta": "tickets/x.log.gz"} un archivo de data/
 *   {"accion": "ping"}                             datos del token
 */

if (($_SERVER['REQUEST_METHOD'] ?? '') !== 'POST') {
    Response::error('Usar POST con JSON', 405);
}

$header = $_SERVER['HTTP_AUTHORIZATION'] ?? '';
if (!preg_match('/^Bearer\s+(\S+)$/', $header, $m)) {
    Response::error('Falta token de autorización', 401);
}
try {
    $token = Consola::tokenVigente($m[1]);
} catch (PDOException $e) {
    // Sin la tabla todavía: no se crea acá (una migración desde un endpoint
    // ya tumbó los informes en producción, ver docs/decisiones.md).
    Response::error('Falta aplicar schema.sql (admin → Base de datos)', 503);
}
if ($token === null) {
    Response::error('Token inválido, vencido o revocado', 401);
}

$body = json_decode((string) file_get_contents('php://input'), true);
if (!is_array($body)) {
    Response::error('El cuerpo tiene que ser un objeto JSON', 400);
}

$tokenId = (int) $token['id'];
$ip = (string) ($_SERVER['REMOTE_ADDR'] ?? '');
@set_time_limit(120);

$tipo = 'ping';
$texto = '';
$resultado = null;
try {
    if (isset($body['sql'])) {
        $tipo = 'sql';
        $texto = (string) $body['sql'];
        $params = $body['params'] ?? [];
        if (!is_array($params)) {
            throw new InvalidArgumentException('"params" tiene que ser lista u objeto');
        }
        $resultado = Consola::ejecutar($texto, $params);
    } elseif (isset($body['script'])) {
        $tipo = 'script';
        $texto = (string) $body['script'];
        $resultado = Consola::script($texto);
    } else {
        $tipo = (string) ($body['accion'] ?? 'ping');
        $texto = (string) ($body['ruta'] ?? '');
        if ($tipo === 'esquema') {
            $resultado = ['objetos' => Consola::esquema()];
        } elseif ($tipo === 'backup') {
            $resultado = ['archivo' => Backups::create()];
        } elseif ($tipo === 'archivos') {
            $resultado = ['ruta' => $texto, 'entradas' => Consola::listarArchivos($texto)];
        } elseif ($tipo === 'leer') {
            $resultado = Consola::leerArchivo($texto);
        } elseif ($tipo === 'ping') {
            $resultado = [
                'etiqueta' => $token['etiqueta'],
                'creado_por' => $token['created_by_username'],
                // Las fechas de la base son UTC (CURRENT_TIMESTAMP); la del
                // servidor, en la zona de Clock.
                'vence_utc' => $token['expires_at'],
                'ahora_utc' => Db::get()->query("SELECT datetime('now')")->fetchColumn(),
                'hora_servidor' => (new DateTime())->format('Y-m-d H:i:s'),
                'php' => PHP_VERSION,
                'sqlite' => Db::get()->query('SELECT sqlite_version()')->fetchColumn(),
            ];
        } else {
            throw new InvalidArgumentException("Acción desconocida: {$tipo}");
        }
    }
} catch (Throwable $e) {
    Consola::registrar($tokenId, $tipo, $texto, null, $e->getMessage(), $ip);
    Response::error($e->getMessage(), $e instanceof InvalidArgumentException ? 400 : 422);
}

Consola::registrar($tokenId, $tipo, $texto, $resultado, null, $ip);
Response::json($resultado);
