<?php

declare(strict_types=1);

require_once __DIR__ . '/CaseCompleteness.php';

/**
 * Práctica deliberada: pacientes que el docente deja disponibles en un curso
 * para que el alumno los abra cuando quiera (en su casa, por ejemplo) y
 * cuantas veces quiera. Ver practice_cases en sql/schema.sql.
 *
 * Cada intento es una cita propia en appointments (practice_id = el
 * paciente de la lista, asignada al alumno, con la fecha y hora en que la
 * abrió). Así la atención, los informes, el chat, la técnica de audiometría
 * y la OIRS funcionan igual que en un práctico, sin un camino aparte. El
 * costo es que toda vista de agenda o estadística de PRÁCTICOS tiene que
 * dejar fuera estas citas: para eso está sinPractica().
 *
 * Decidido con el docente (2026-10-08): intentos ilimitados y separados;
 * al cerrar, la ficha de estudio del caso se libera o no según la casilla
 * de cada paciente; en las estadísticas va aparte de los prácticos.
 */
final class Practica
{
    /**
     * ¿La base ya tiene practice_cases y appointments.practice_id? Si no, lo
     * crea al vuelo. Nunca lanza: entre el despliegue y "Aplicar schema" lo
     * llaman sync.php y la agenda, y una migración que revienta en un
     * endpoint así tumba la app entera (incidente de informes, 2026-10-08).
     * Si no se pudo, las consultas siguen como antes de la práctica.
     */
    public static function listo(): bool
    {
        static $listo = null;
        if ($listo !== null) {
            return $listo;
        }
        $marca = __DIR__ . '/../data/.migracion_practica_fallo';
        $reciente = is_file($marca) && (time() - (int) @filemtime($marca)) < 3600;
        try {
            $cols = array_column(Db::get()->query('PRAGMA table_info(appointments)')->fetchAll(), 'name');
            $listo = in_array('practice_id', $cols, true);
            if (!$listo && !$reciente) {
                Db::migratePracticeIfNeeded();
                $cols = array_column(Db::get()->query('PRAGMA table_info(appointments)')->fetchAll(), 'name');
                $listo = in_array('practice_id', $cols, true);
            }
        } catch (Throwable $e) {
            error_log('[Practica::listo] ' . $e->getMessage());
            @file_put_contents($marca, date('c') . ' ' . $e->getMessage() . "\n");
            $listo = false;
        }
        if ($listo && is_file($marca)) {
            @unlink($marca);
        }
        return $listo;
    }

    /** Condición SQL "es cita de práctico" (no intento de práctica). */
    public static function sinPractica(string $alias = ''): string
    {
        if (!self::listo()) {
            return '1=1';
        }
        return ($alias !== '' ? $alias . '.' : '') . 'practice_id IS NULL';
    }

    /** Condición SQL "es intento de práctica". */
    public static function soloPractica(string $alias = ''): string
    {
        if (!self::listo()) {
            return '0=1';
        }
        return ($alias !== '' ? $alias . '.' : '') . 'practice_id IS NOT NULL';
    }

    /**
     * Pacientes de la lista de un curso (activos), con cuántos alumnos los
     * practicaron y cuántos intentos cerrados suman.
     */
    public static function delCurso(int $courseId): array
    {
        if (!self::listo()) {
            return [];
        }
        $stmt = Db::get()->prepare(
            "SELECT pc.id, pc.case_id, pc.procedimiento, pc.show_study_sheet, pc.created_at,
                    p.nombre, p.apellido, p.rut,
                    (SELECT COUNT(*) FROM attendances att JOIN appointments a ON a.id = att.appointment_id
                      WHERE a.practice_id = pc.id AND att.estado = 'atendido') AS intentos,
                    (SELECT COUNT(DISTINCT att.student_id) FROM attendances att JOIN appointments a ON a.id = att.appointment_id
                      WHERE a.practice_id = pc.id AND att.estado = 'atendido') AS alumnos
               FROM practice_cases pc
               JOIN cases c ON c.id = pc.case_id
               LEFT JOIN patients p ON p.id = c.patient_id
              WHERE pc.course_id = ? AND pc.active = 1
              ORDER BY pc.id"
        );
        $stmt->execute([$courseId]);
        return $stmt->fetchAll();
    }

    /** Fichas que se pueden sumar a la lista: no archivadas y que no estén ya. */
    public static function casosParaAgregar(int $courseId): array
    {
        if (!self::listo()) {
            return [];
        }
        $stmt = Db::get()->prepare(
            "SELECT c.id, p.nombre, p.apellido
               FROM cases c
               LEFT JOIN patients p ON p.id = c.patient_id
              WHERE c.archived_at IS NULL
                AND c.id NOT IN (SELECT case_id FROM practice_cases WHERE course_id = ? AND active = 1)
              ORDER BY p.apellido, p.nombre, c.id"
        );
        $stmt->execute([$courseId]);
        return $stmt->fetchAll();
    }

    /** Suma un paciente a la lista. Devuelve el error para el docente, o null. */
    public static function agregar(int $courseId, string $caseId, string $procedimiento, bool $mostrarFicha, int $userId): ?string
    {
        if (!self::listo()) {
            return 'La base todavía no tiene la práctica deliberada: aplica el schema en Base de datos.';
        }
        $pdo = Db::get();
        $stmt = $pdo->prepare('SELECT data, archived_at FROM cases WHERE id = ?');
        $stmt->execute([$caseId]);
        $filas = $stmt->fetchAll();
        if (!$filas) {
            return 'No existe esa ficha.';
        }
        if ($filas[0]['archived_at'] !== null) {
            return 'Esa ficha está archivada.';
        }
        // Mismo criterio que agendar: un caso al que le falta lo que no se
        // puede calcular deja al alumno con un paciente que no cierra.
        $data = json_decode((string) $filas[0]['data'], true);
        $faltantes = CaseCompleteness::pendingTexts(is_array($data) ? $data : []);
        if ($faltantes !== []) {
            return 'El caso ' . $caseId . ' está incompleto y no se puede dejar para práctica: ' . implode(' | ', $faltantes);
        }
        $procedimiento = trim($procedimiento) !== '' ? trim($procedimiento) : 'Audiometría';
        // Si ya estuvo y se quitó, vuelve la misma fila: sus intentos viejos
        // siguen colgando de ella.
        Db::reintentar(static function () use ($pdo, $courseId, $caseId, $procedimiento, $mostrarFicha, $userId): void {
            $pdo->prepare(
                'INSERT INTO practice_cases (course_id, case_id, procedimiento, show_study_sheet, created_by)
                 VALUES (?, ?, ?, ?, ?)
                 ON CONFLICT(course_id, case_id) DO UPDATE SET
                    active = 1, procedimiento = excluded.procedimiento,
                    show_study_sheet = excluded.show_study_sheet, updated_at = CURRENT_TIMESTAMP'
            )->execute([$courseId, $caseId, $procedimiento, $mostrarFicha ? 1 : 0, $userId]);
        });
        return null;
    }

    public static function quitar(int $itemId, int $courseId): void
    {
        if (!self::listo()) {
            return;
        }
        Db::reintentar(static function () use ($itemId, $courseId): void {
            Db::get()->prepare(
                'UPDATE practice_cases SET active = 0, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND course_id = ?'
            )->execute([$itemId, $courseId]);
        });
    }

    public static function setMostrarFicha(int $itemId, int $courseId, bool $mostrar): void
    {
        if (!self::listo()) {
            return;
        }
        Db::reintentar(static function () use ($itemId, $courseId, $mostrar): void {
            Db::get()->prepare(
                'UPDATE practice_cases SET show_study_sheet = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND course_id = ?'
            )->execute([$mostrar ? 1 : 0, $itemId, $courseId]);
        });
    }

    /**
     * Lo que ve el alumno: los pacientes de práctica de sus cursos activos,
     * con sus propios intentos (cerrados, el último, y el que tenga abierto).
     */
    public static function paraAlumno(int $userId): array
    {
        if (!self::listo()) {
            return [];
        }
        $stmt = Db::get()->prepare(
            "SELECT pc.id, pc.case_id, pc.procedimiento, pc.show_study_sheet,
                    co.name AS curso,
                    p.nombre, p.apellido, p.rut, p.fecha_nac,
                    (SELECT COUNT(*) FROM attendances att JOIN appointments a ON a.id = att.appointment_id
                      WHERE a.practice_id = pc.id AND att.student_id = :me AND att.estado = 'atendido') AS intentos,
                    (SELECT MAX(att.updated_at) FROM attendances att JOIN appointments a ON a.id = att.appointment_id
                      WHERE a.practice_id = pc.id AND att.student_id = :me AND att.estado = 'atendido') AS ultimo,
                    (SELECT a.id FROM attendances att JOIN appointments a ON a.id = att.appointment_id
                      WHERE a.practice_id = pc.id AND att.student_id = :me AND att.estado = 'atendido'
                      ORDER BY att.updated_at DESC, a.id DESC LIMIT 1) AS ultimo_cerrado
               FROM practice_cases pc
               JOIN courses co ON co.id = pc.course_id AND co.active = 1
               JOIN course_students cs ON cs.course_id = pc.course_id AND cs.user_id = :me
               JOIN cases c ON c.id = pc.case_id AND c.archived_at IS NULL
               LEFT JOIN patients p ON p.id = c.patient_id
              WHERE pc.active = 1
              ORDER BY co.name, p.apellido, p.nombre, pc.id"
        );
        $stmt->bindValue(':me', $userId, PDO::PARAM_INT);
        $stmt->execute();
        $items = $stmt->fetchAll();
        foreach ($items as &$it) {
            $it['id'] = (int) $it['id'];
            $it['intentos'] = (int) $it['intentos'];
            $it['show_study_sheet'] = (bool) $it['show_study_sheet'];
            $it['ultimo_cerrado'] = $it['ultimo_cerrado'] !== null ? (int) $it['ultimo_cerrado'] : null;
            $it['abierto'] = self::intentoAbierto($it['id'], $userId);
        }
        unset($it);
        return $items;
    }

    /**
     * Cita del intento que el alumno dejó a medias en este paciente, o null.
     * Cuenta también la cita creada sin atención todavía (la app se cayó
     * entre "Practicar" y marcar "atendiendo"): sin esto quedaría huérfana y
     * cada clic dejaría otra.
     */
    private static function intentoAbierto(int $itemId, int $userId): ?int
    {
        $stmt = Db::get()->prepare(
            "SELECT a.id FROM appointments a
               LEFT JOIN attendances att ON att.appointment_id = a.id AND att.student_id = ?
              WHERE a.practice_id = ? AND a.assigned_student_id = ?
                AND (att.id IS NULL OR att.estado = 'atendiendo')
              ORDER BY a.id DESC LIMIT 1"
        );
        $stmt->execute([$userId, $itemId, $userId]);
        $filas = $stmt->fetchAll();
        return $filas ? (int) $filas[0]['id'] : null;
    }

    /**
     * Abre un intento: devuelve la cita (la que quedó abierta, o una nueva).
     * Lanza RuntimeException con un texto para el alumno si no corresponde.
     */
    public static function iniciar(int $userId, int $itemId): array
    {
        if (!self::listo()) {
            throw new RuntimeException('La práctica todavía no está disponible en el servidor.');
        }
        $pdo = Db::get();
        $stmt = $pdo->prepare(
            "SELECT pc.id, pc.course_id, pc.case_id, pc.procedimiento, c.patient_id, c.data
               FROM practice_cases pc
               JOIN courses co ON co.id = pc.course_id AND co.active = 1
               JOIN course_students cs ON cs.course_id = pc.course_id AND cs.user_id = ?
               JOIN cases c ON c.id = pc.case_id AND c.archived_at IS NULL
              WHERE pc.id = ? AND pc.active = 1"
        );
        $stmt->execute([$userId, $itemId]);
        $filas = $stmt->fetchAll();
        if (!$filas) {
            throw new RuntimeException('Este paciente ya no está en tu lista de práctica.');
        }
        $item = $filas[0];

        $abierto = self::intentoAbierto($itemId, $userId);
        if ($abierto === null) {
            $identidad = self::identidad($item);
            $abierto = (int) Db::reintentar(static function () use ($pdo, $item, $identidad, $userId): int {
                // fecha 'dd-MM-yy' y hora 'HH:mm', como toda cita: es cuándo
                // lo abrió, y así se ordena con lo demás en su historial.
                $pdo->prepare(
                    'INSERT INTO appointments (fecha, hora, rut, nombre, apellido, fecha_nac, procedimiento, case_id,
                                               course_id, assigned_student_id, patient_id, practice_id)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
                )->execute([
                    date('d-m-y'), date('H:i'),
                    $identidad['rut'], $identidad['nombre'], $identidad['apellido'], $identidad['fecha_nac'],
                    (string) $item['procedimiento'], (string) $item['case_id'],
                    (int) $item['course_id'], $userId,
                    $item['patient_id'] !== null ? (int) $item['patient_id'] : null,
                    (int) $item['id'],
                ]);
                return (int) $pdo->lastInsertId();
            });
        }

        $stmt = $pdo->prepare('SELECT * FROM appointments WHERE id = ?');
        $stmt->execute([$abierto]);
        return Db::castAppointment($stmt->fetchAll()[0]);
    }

    /** Identidad del paciente del caso; si no tiene, la del snapshot de la ficha. */
    private static function identidad(array $item): array
    {
        if ($item['patient_id'] !== null) {
            $stmt = Db::get()->prepare('SELECT rut, nombre, apellido, fecha_nac FROM patients WHERE id = ?');
            $stmt->execute([(int) $item['patient_id']]);
            $filas = $stmt->fetchAll();
            if ($filas) {
                return array_map('strval', $filas[0]);
            }
        }
        $data = json_decode((string) $item['data'], true);
        $snap = is_array($data) && is_array($data['paciente_snapshot'] ?? null) ? $data['paciente_snapshot'] : [];
        return [
            'rut' => (string) ($snap['rut'] ?? ''),
            'nombre' => (string) ($snap['nombre'] ?? ''),
            'apellido' => (string) ($snap['apellido'] ?? ''),
            'fecha_nac' => (string) ($snap['fecha_nac'] ?? ''),
        ];
    }

    /**
     * PDF de la ficha de estudio del caso para el alumno: el mismo que el
     * docente baja con ?modo=estudio en admin/case_sheet_pdf.php (sin perfil
     * auditivo ni mandos del generador). Quien llama ya revisó el permiso
     * con fichaDeEstudioPermitida().
     *
     * @return array{0: string, 1: string} bytes del PDF y nombre de archivo
     */
    public static function pdfFichaDeEstudio(string $caseId, int $userId): array
    {
        require_once __DIR__ . '/CaseSheetPdf.php';
        require_once __DIR__ . '/EstudioRedactor.php';
        $stmt = Db::get()->prepare('SELECT data, patient_id FROM cases WHERE id = ?');
        $stmt->execute([$caseId]);
        $filas = $stmt->fetchAll();
        if (!$filas) {
            throw new RuntimeException('Caso no encontrado.');
        }
        $data = json_decode((string) $filas[0]['data'], true);
        if (!is_array($data)) {
            throw new RuntimeException('La ficha de este caso no se puede leer.');
        }
        // Redactada con IA la primera vez y cacheada en el caso (ver
        // EstudioRedactor): las siguientes, de cualquier alumno, la reusan.
        $data = EstudioRedactor::ensureFresh($caseId, $data, $userId);
        $patient = self::identidad(['patient_id' => $filas[0]['patient_id'], 'data' => json_encode($data)]);
        if ($patient['rut'] === '') {
            $patient['rut'] = 'N/D';
        }
        $bytes = CaseSheetPdf::build($caseId, $data, $patient, '', date('d-m-Y'), true);
        $nombre = 'ficha_estudio_' . CaseSheetPdf::identificador($caseId, $patient) . '.pdf';
        return [$bytes, $nombre];
    }

    /**
     * ¿El alumno puede bajar la ficha de estudio de esta cita? Solo si es un
     * intento suyo de práctica, ya cerrado, y el docente tiene marcada la
     * casilla en ese paciente. Devuelve el case_id, o null.
     */
    public static function fichaDeEstudioPermitida(int $appointmentId, int $userId): ?string
    {
        if (!self::listo()) {
            return null;
        }
        $stmt = Db::get()->prepare(
            "SELECT a.case_id
               FROM appointments a
               JOIN practice_cases pc ON pc.id = a.practice_id
               JOIN attendances att ON att.appointment_id = a.id AND att.student_id = ?
              WHERE a.id = ? AND a.assigned_student_id = ? AND att.estado = 'atendido'
                AND pc.show_study_sheet = 1"
        );
        $stmt->execute([$userId, $appointmentId, $userId]);
        $filas = $stmt->fetchAll();
        return $filas && $filas[0]['case_id'] !== null ? (string) $filas[0]['case_id'] : null;
    }
}
