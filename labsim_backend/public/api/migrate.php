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
    Db::migrateLtiReplayColumnsIfNeeded();
    Db::migratePatientColumnsIfNeeded();
    $sql = file_get_contents(__DIR__ . '/../../sql/schema.sql');
    Db::get()->exec($sql);
    // Después del exec: llm_config ya existe (el exec de arriba la crea si
    // la instalación no la tenía) -- recién ahí se le puede agregar la
    // columna si faltaba en una instalación que sí la tenía pero de antes.
    Db::migrateLlmOirsPromptIfNeeded();
    // Crea courses/student_groups (REFERENCES de las columnas nuevas de
    // appointments) si la instalación no las tenía.
    Db::migrateCoursesIfNeeded();
    // Después de courses: patients ya existe (la creó el exec de arriba),
    // recién ahí se puede backfillear patient_id en appointments/cases.
    Db::migratePatientsIfNeeded();
} catch (Throwable $e) {
    Response::error('Error aplicando schema: ' . $e->getMessage(), 500);
}

Response::json(['ok' => true, 'message' => 'Schema actualizado']);
