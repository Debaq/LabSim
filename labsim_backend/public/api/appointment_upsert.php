<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

/**
 * Crea o edita una cita de agenda. Sin id (o id <= 0) crea una nueva.
 * Cubre lo que antes eran ediciones directas de fila en schedule.json:
 * habilitar (fecha/hora), edición inline de datos del paciente, nota
 * admin, cancelar/restaurar.
 */

Auth::requireAdmin();

$body = json_decode(file_get_contents('php://input'), true) ?? [];
$id = (int) ($body['id'] ?? 0);

$fields = [
    'fecha' => (string) ($body['fecha'] ?? ''),
    'hora' => (string) ($body['hora'] ?? ''),
    'rut' => (string) ($body['rut'] ?? ''),
    'nombre' => (string) ($body['nombre'] ?? ''),
    'apellido' => (string) ($body['apellido'] ?? ''),
    'fecha_nac' => (string) ($body['fecha_nac'] ?? ''),
    'procedimiento' => (string) ($body['procedimiento'] ?? ''),
    'case_id' => $body['case_id'] ?? null,
    'nota_admin' => (string) ($body['nota_admin'] ?? ''),
    'cancelada' => !empty($body['cancelada']) ? 1 : 0,
];

$pdo = Db::get();

if ($fields['fecha'] !== '' && $fields['hora'] !== '' && !$fields['cancelada']) {
    $stmt = $pdo->prepare(
        'SELECT id FROM appointments WHERE fecha = ? AND hora = ? AND cancelada = 0 AND id != ?'
    );
    $stmt->execute([$fields['fecha'], $fields['hora'], $id]);
    if ($stmt->fetch()) {
        Response::error('Ya existe una cita agendada en esa fecha y hora', 409);
    }
}

if ($id > 0) {
    $stmt = $pdo->prepare(
        'UPDATE appointments SET fecha = ?, hora = ?, rut = ?, nombre = ?, apellido = ?, fecha_nac = ?,
                procedimiento = ?, case_id = ?, nota_admin = ?, cancelada = ?, updated_at = CURRENT_TIMESTAMP
         WHERE id = ?'
    );
    $stmt->execute([
        $fields['fecha'], $fields['hora'], $fields['rut'], $fields['nombre'], $fields['apellido'],
        $fields['fecha_nac'], $fields['procedimiento'], $fields['case_id'], $fields['nota_admin'],
        $fields['cancelada'], $id,
    ]);
} else {
    $stmt = $pdo->prepare(
        'INSERT INTO appointments (fecha, hora, rut, nombre, apellido, fecha_nac, procedimiento, case_id, nota_admin, cancelada)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    );
    $stmt->execute([
        $fields['fecha'], $fields['hora'], $fields['rut'], $fields['nombre'], $fields['apellido'],
        $fields['fecha_nac'], $fields['procedimiento'], $fields['case_id'], $fields['nota_admin'],
        $fields['cancelada'],
    ]);
    $id = (int) $pdo->lastInsertId();
}

$stmt = $pdo->prepare('SELECT * FROM appointments WHERE id = ?');
$stmt->execute([$id]);
Response::json(['appointment' => Db::castAppointment($stmt->fetch())]);
