<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Patients.php';
require_once __DIR__ . '/../../src/Appointments.php';

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

// El choque es por audiencia, no por fecha/hora global: el mismo paciente puede
// repetirse el mismo día a otra hora, y dos grupos distintos pueden atender a la
// misma hora. Ver Appointments. La asignación (curso/grupo/alumno) no viaja en
// este endpoint -- se conserva la de la cita, y una cita creada desde el cliente
// nace sin curso (cola global legado).
$asignacion = ['course_id' => null, 'assigned_group_id' => null, 'assigned_student_id' => null];
if ($id > 0) {
    $stmt = $pdo->prepare('SELECT course_id, assigned_group_id, assigned_student_id FROM appointments WHERE id = ?');
    $stmt->execute([$id]);
    $guardada = $stmt->fetch();
    if ($guardada !== false) {
        $asignacion = [
            'course_id' => $guardada['course_id'],
            'assigned_group_id' => $guardada['assigned_group_id'],
            'assigned_student_id' => $guardada['assigned_student_id'],
        ];
    }
}
$choque = Appointments::buscarChoque($pdo, array_merge($asignacion, [
    'fecha' => $fields['fecha'],
    'hora' => $fields['hora'],
]), $id);
if ($choque !== null) {
    Response::error(Appointments::textoChoque($pdo, $choque), 409);
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
