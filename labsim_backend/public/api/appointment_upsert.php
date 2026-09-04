<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Patients.php';

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
];

$pdo = Db::get();

if ($fields['fecha'] !== '' && $fields['hora'] !== '') {
    $stmt = $pdo->prepare(
        'SELECT id FROM appointments WHERE fecha = ? AND hora = ? AND id != ?'
    );
    $stmt->execute([$fields['fecha'], $fields['hora'], $id]);
    if ($stmt->fetch()) {
        Response::error('Ya existe una cita agendada en esa fecha y hora', 409);
    }
}

// Un solo punto de entrada para escribir identidad de paciente (Patients) --
// si la cita ya tenía patient_id lo actualiza in-place, si no (cita nueva, o
// fila legado sin migrar) lo resuelve/crea por rut. Cascadea a todas las
// citas del mismo paciente.
$existingPatientId = null;
if ($id > 0) {
    $stmt = $pdo->prepare('SELECT patient_id FROM appointments WHERE id = ?');
    $stmt->execute([$id]);
    $found = $stmt->fetchColumn();
    $existingPatientId = ($found !== false && $found !== null) ? (int) $found : null;
}
if ($existingPatientId !== null) {
    Patients::update($pdo, $existingPatientId, $fields['rut'], $fields['nombre'], $fields['apellido'], $fields['fecha_nac']);
    $patientId = $existingPatientId;
} else {
    $patientId = Patients::upsertByRut($pdo, $fields['rut'], $fields['nombre'], $fields['apellido'], $fields['fecha_nac']);
}

if ($id > 0) {
    $stmt = $pdo->prepare(
        'UPDATE appointments SET fecha = ?, hora = ?, rut = ?, nombre = ?, apellido = ?, fecha_nac = ?,
                procedimiento = ?, case_id = ?, nota_admin = ?, cancelada = 0, patient_id = ?, updated_at = CURRENT_TIMESTAMP
         WHERE id = ?'
    );
    $stmt->execute([
        $fields['fecha'], $fields['hora'], $fields['rut'], $fields['nombre'], $fields['apellido'],
        $fields['fecha_nac'], $fields['procedimiento'], $fields['case_id'], $fields['nota_admin'],
        $patientId, $id,
    ]);
} else {
    $stmt = $pdo->prepare(
        'INSERT INTO appointments (fecha, hora, rut, nombre, apellido, fecha_nac, procedimiento, case_id, nota_admin, patient_id)
         VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
    );
    $stmt->execute([
        $fields['fecha'], $fields['hora'], $fields['rut'], $fields['nombre'], $fields['apellido'],
        $fields['fecha_nac'], $fields['procedimiento'], $fields['case_id'], $fields['nota_admin'],
        $patientId,
    ]);
    $id = (int) $pdo->lastInsertId();
}

if ($fields['case_id']) {
    $pdo->prepare('UPDATE cases SET patient_id = ? WHERE id = ?')->execute([$patientId, $fields['case_id']]);
}

$stmt = $pdo->prepare('SELECT * FROM appointments WHERE id = ?');
$stmt->execute([$id]);
Response::json(['appointment' => Db::castAppointment($stmt->fetch())]);
