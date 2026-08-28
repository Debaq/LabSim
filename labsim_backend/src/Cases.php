<?php

final class Cases
{
    /**
     * El caso clínico (tabla cases) nunca guarda el nombre del paciente --
     * lo genera el cliente al crear el caso y lo escribe solo en la fila de
     * la cita (appointments.nombre/apellido/rut), nunca en cases.data. Si
     * se borra la cita sin pasar por acá, el caso queda en la base pero
     * sin ninguna forma de saber de quién era (cases.php lo mostraba como
     * "— sin cita —", indistinguible de cualquier otro caso huérfano).
     * Llamar SIEMPRE antes del DELETE de una cita que tenga case_id: copia
     * los datos del paciente al caso para que se sigan viendo en
     * cases.php aunque la cita ya no exista.
     */
    public static function snapshotBeforeAppointmentDelete(int $appointmentId): void
    {
        $pdo = Db::get();
        $stmt = $pdo->prepare('SELECT case_id, nombre, apellido, rut, fecha_nac, procedimiento, fecha, hora FROM appointments WHERE id = ?');
        $stmt->execute([$appointmentId]);
        $appointment = $stmt->fetch();
        if (!$appointment || !$appointment['case_id']) {
            return;
        }

        $stmt = $pdo->prepare('SELECT data FROM cases WHERE id = ?');
        $stmt->execute([$appointment['case_id']]);
        $caseRow = $stmt->fetch();
        if (!$caseRow) {
            return;
        }

        $data = json_decode($caseRow['data'], true);
        if (!is_array($data)) {
            $data = [];
        }
        $data['paciente_snapshot'] = [
            'nombre' => $appointment['nombre'],
            'apellido' => $appointment['apellido'],
            'rut' => $appointment['rut'],
            'fecha_nac' => $appointment['fecha_nac'],
            'procedimiento' => $appointment['procedimiento'],
            'cita_fecha' => $appointment['fecha'],
            'cita_hora' => $appointment['hora'],
            'cita_eliminada_en' => date('Y-m-d H:i:s'),
        ];

        $pdo->prepare('UPDATE cases SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
            ->execute([json_encode($data, JSON_UNESCAPED_UNICODE), $appointment['case_id']]);
    }
}
