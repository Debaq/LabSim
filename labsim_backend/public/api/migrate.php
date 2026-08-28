<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Aplica sql/schema.sql contra la base ya instalada -- para cuando el
 * schema cambia después del install.php inicial (como esta migración a
 * cases/appointments/attendances). Idempotente: todo el schema usa
 * CREATE TABLE/INDEX IF NOT EXISTS. Requiere admin logueado (no una key
 * estática como el instalador: ya hay un admin real para autenticar esto).
 */

Auth::requireAdmin();

try {
    Db::migrateLtiPlatformsIfNeeded();
    $sql = file_get_contents(__DIR__ . '/../../sql/schema.sql');
    Db::get()->exec($sql);
} catch (Throwable $e) {
    Response::error('Error aplicando schema: ' . $e->getMessage(), 500);
}

Response::json(['ok' => true, 'message' => 'Schema actualizado']);
