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
        $stmt = $pdo->prepare('SELECT id, rut, nombre, apellido, fecha_nac FROM patients WHERE id = ?');
        $stmt->execute([$patientId]);
        $row = $stmt->fetch();
        return $row !== false ? $row : null;
    }
}
