<?php

final class Patients
{
    /**
     * Busca un patient por rut; si existe, actualiza sus datos (y cascadea
     * el cambio a todas las citas de ese paciente vía update()); si no
     * existe, lo crea. rut='' nunca hace match (ver índice único parcial en
     * schema.sql) -- siempre crea uno nuevo, cada cita sin rut es su propio
     * paciente hasta que alguien le ponga un rut real.
     */
    public static function upsertByRut(PDO $pdo, string $rut, string $nombre, string $apellido, string $fechaNac): int
    {
        $existing = null;
        if ($rut !== '') {
            $stmt = $pdo->prepare('SELECT id FROM patients WHERE rut = ?');
            $stmt->execute([$rut]);
            $found = $stmt->fetchColumn();
            $existing = $found !== false ? (int) $found : null;
        }

        if ($existing !== null) {
            self::update($pdo, $existing, $rut, $nombre, $apellido, $fechaNac);
            return $existing;
        }

        $pdo->prepare(
            'INSERT INTO patients (rut, nombre, apellido, fecha_nac) VALUES (?, ?, ?, ?)'
        )->execute([$rut, $nombre, $apellido, $fechaNac]);
        return (int) $pdo->lastInsertId();
    }

    /**
     * Actualiza un patient ya identificado por id, y cascadea los datos a
     * TODAS las citas de appointments que lo referencian -- son caché
     * desnormalizada (ver comentario en sql/schema.sql), este es el único
     * lugar que debe escribirlas.
     */
    public static function update(PDO $pdo, int $patientId, string $rut, string $nombre, string $apellido, string $fechaNac): void
    {
        $pdo->prepare(
            'UPDATE patients SET rut = ?, nombre = ?, apellido = ?, fecha_nac = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        )->execute([$rut, $nombre, $apellido, $fechaNac, $patientId]);

        $pdo->prepare(
            'UPDATE appointments SET rut = ?, nombre = ?, apellido = ?, fecha_nac = ?, updated_at = CURRENT_TIMESTAMP WHERE patient_id = ?'
        )->execute([$rut, $nombre, $apellido, $fechaNac, $patientId]);
    }

    public static function find(PDO $pdo, int $patientId): ?array
    {
        $stmt = $pdo->prepare('SELECT id, rut, nombre, apellido, fecha_nac, historia_clinica, comentario_docente FROM patients WHERE id = ?');
        $stmt->execute([$patientId]);
        $row = $stmt->fetch();
        return $row !== false ? $row : null;
    }

    /**
     * Solo toca historia_clinica -- separado de update() para que ningún
     * caller de update()/upsertByRut() (agenda.php, appointment_upsert.php,
     * que no conocen este campo) pueda pisarla sin querer con ''. Es texto
     * libre editado por el admin en case_create.php; distinto de
     * attendances.nota (nota individual de cada alumno por atención, no se
     * edita acá).
     *
     * Un mismo patient puede tener varios cases (una cita = un case, un
     * paciente puede reagendarse). historia_clinica vive en patients (fuente
     * única), pero el cliente de escritorio no sincroniza patients, solo
     * cases -- por eso hay que cascadear el valor a cases.data['historia_clinica']
     * de TODOS los cases de este patient, no solo el que se está editando,
     * o la ficha del paciente en Agenda.py queda con el valor viejo/vacío
     * cuando se la abre desde una cita distinta a la que se editó.
     */
    public static function updateHistoriaClinica(PDO $pdo, int $patientId, string $historiaClinica): void
    {
        $pdo->prepare(
            'UPDATE patients SET historia_clinica = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        )->execute([$historiaClinica, $patientId]);

        $stmt = $pdo->prepare('SELECT id, data FROM cases WHERE patient_id = ?');
        $stmt->execute([$patientId]);
        foreach ($stmt->fetchAll() as $case) {
            $data = json_decode($case['data'], true);
            if (!is_array($data)) {
                $data = [];
            }
            $data['historia_clinica'] = $historiaClinica;
            $pdo->prepare('UPDATE cases SET data = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
                ->execute([json_encode($data, JSON_UNESCAPED_UNICODE), $case['id']]);
        }
    }

    /**
     * Solo toca comentario_docente -- nota privada del docente (ej. la
     * patología real que representa el caso), a diferencia de
     * historia_clinica NO se cascadea a cases.data ni se sincroniza al
     * cliente de escritorio: es exclusiva del panel admin, para que nunca
     * llegue a la ficha que ve el alumno.
     */
    public static function updateComentarioDocente(PDO $pdo, int $patientId, string $comentarioDocente): void
    {
        $pdo->prepare(
            'UPDATE patients SET comentario_docente = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?'
        )->execute([$comentarioDocente, $patientId]);
    }
}
