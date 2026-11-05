<?php

declare(strict_types=1);

/**
 * El docente reinicia desde el panel el montaje de electrodos de un alumno
 * (attendances.montaje_reinicio): la columna nace con "Aplicar schema" y no
 * desde un endpoint, y el panel no se cae si todavía no está.
 */

$schema = (string) file_get_contents(__DIR__ . '/../sql/schema.sql');
t_true(preg_match('/CREATE TABLE IF NOT EXISTS attendances \(.*?montaje_reinicio INTEGER NOT NULL DEFAULT 0.*?\);/s', $schema) === 1,
    'schema.sql trae la columna en attendances');

$db = (string) file_get_contents(__DIR__ . '/../src/Db.php');
t_true(strpos($db, "addColumnIfMissing(self::get(), 'attendances', 'montaje_reinicio'") !== false,
    'Db::migrateMontajeReinicioIfNeeded agrega la columna en bases viejas');

$database = (string) file_get_contents(__DIR__ . '/../public/admin/database.php');
t_true(strpos($database, 'Db::migrateMontajeReinicioIfNeeded()') !== false, 'Va en los pasos de Aplicar schema');

$dashboard = (string) file_get_contents(__DIR__ . '/../public/admin/dashboard.php');
t_true(strpos($dashboard, "postAction === 'reset_montaje'") !== false
    && strpos($dashboard, 'montaje_reinicio = montaje_reinicio + 1') !== false, 'El panel suma un pedido');
t_true(strpos($dashboard, 'catch (PDOException $e)') !== false, 'Sin la columna avisa en vez de romper');
t_true(strpos($dashboard, 'migrateMontajeReinicio') === false, 'El endpoint no migra');
