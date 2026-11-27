<?php

declare(strict_types=1);

require_once __DIR__ . '/AudiometriaTecnica.php';
require_once __DIR__ . '/OtoscopiaTecnica.php';
require_once __DIR__ . '/AcumetriaTecnica.php';
require_once __DIR__ . '/ImpedanciometriaTecnica.php';
require_once __DIR__ . '/EntrevistaTecnica.php';

/**
 * Técnica de la atención fuera del audiómetro: la entrevista (chat con el
 * paciente), otoscopio (ot_), diapasones (ac_) e impedanciómetro (z_). Cada uno se evalúa SOLO si
 * el alumno lo usó con el paciente: no todas las atenciones piden todos los
 * exámenes, así que no hacer uno no descuenta. Lo que sí se mira es que lo
 * que se hizo, se haga bien, y el orden entre equipos (otoscopía antes de la
 * sonda y del diapasón).
 *
 * La técnica es la de los capítulos H1 (otoscopía), H2 (acumetría) y H7
 * (impedanciometría) del libro del curso. Las secciones tienen la misma forma
 * que las de AudiometriaTecnica (reglas con peso y logro, por oído,
 * advertencias) y se pintan con AudiometriaTecnicaVista::seccionEquipo.
 */
final class EquiposTecnica
{
    /**
     * Desde cuándo la app tiene cada cosa (registros de prod): antes no se
     * puede exigir. Instrucciones del impedanciómetro (z_instruccion) desde
     * el 31-10-2026; otoscopio y diapasones en la app desde el 06-11-2026.
     */
    public const Z_INSTRUCCIONES_DESDE = '2026-10-31';
    public const OTOSCOPIO_DESDE = '2026-11-06';

    public const EQUIPOS = [
        'entrevista' => 'Entrevista',
        'otoscopia' => 'Otoscopía',
        'acumetria' => 'Diapasones',
        'impedanciometria' => 'Impedanciometría',
    ];

    /**
     * Evalúa los tres equipos sobre las filas de action_logs de UNA atención
     * (payload decodificado, en orden). $extra: 'informe_otoscopia' (data del
     * informe OTOSCOPIA o null) y 'tipos_otoscopia' (['od' => tipo de la
     * biblioteca de otoscopías o null, 'oi' => ...]) y 'chat' (mensajes
     * del chat con el paciente, para la entrevista).
     *
     * @return array{entrevista:?array, otoscopia:?array, acumetria:?array, impedanciometria:?array}
     */
    public static function evaluar(array $logs, array $caso, array $extra = []): array
    {
        $logs = array_values(array_filter($logs, static function ($l) {
            return ($l['payload']['con_paciente'] ?? true) !== false;
        }));
        $out = [
            'entrevista' => EntrevistaTecnica::evaluar($extra['chat'] ?? [], $caso, (bool) ($extra['anamnesis_completa'] ?? true)),
            'otoscopia' => OtoscopiaTecnica::evaluar($logs, $caso, $extra['informe_otoscopia'] ?? null, $extra['tipos_otoscopia'] ?? []),
            'acumetria' => AcumetriaTecnica::evaluar($logs, $caso, $extra['informe_otoscopia'] ?? null),
            'impedanciometria' => ImpedanciometriaTecnica::evaluar($logs, $caso),
        ];
        foreach ($out as $k => $sec) {
            if ($sec !== null) {
                $sec = AudiometriaTecnica::ponderar($sec);
                $sec['puntaje'] = AudiometriaTecnica::sumar([$sec]);
                foreach ($sec['oidos'] ?? [] as $o => $reglas) {
                    $sec['puntaje_oidos'][$o] = AudiometriaTecnica::sumar([['reglas' => $reglas]]);
                }
                $out[$k] = $sec;
            }
        }
        return $out;
    }

    /** Los equipos de una atención, leyendo de la base lo que hace falta. */
    public static function paraAtencion(int $appointmentId, int $studentId): array
    {
        $pdo = Db::get();
        $stmt = $pdo->prepare(
            "SELECT a.case_id, a.course_id, c.data, att.id AS attendance_id FROM appointments a
               LEFT JOIN cases c ON c.id = a.case_id
               LEFT JOIN attendances att ON att.appointment_id = a.id AND att.student_id = ?
              WHERE a.id = ?"
        );
        $stmt->execute([$studentId, $appointmentId]);
        $cita = $stmt->fetch();
        $stmt->closeCursor();
        $caso = $cita && $cita['data'] ? json_decode((string) $cita['data'], true) : null;
        if (!is_array($caso)) {
            return ['entrevista' => null, 'otoscopia' => null, 'acumetria' => null, 'impedanciometria' => null];
        }

        $stmt = $pdo->prepare(
            "SELECT client_ts, action, payload FROM action_logs WHERE user_id = ?
                AND (action LIKE 'z\\_%' ESCAPE '\\' OR action LIKE 'ot\\_%' ESCAPE '\\' OR action LIKE 'ac\\_%' ESCAPE '\\')
              ORDER BY id"
        );
        $stmt->execute([$studentId]);
        $logs = [];
        while (($l = $stmt->fetch()) !== false) {
            if (!preg_match('/"appointment_id":"?(\d+)/', (string) $l['payload'], $m) || (int) $m[1] !== $appointmentId) {
                continue;
            }
            $p = json_decode((string) $l['payload'], true);
            if (is_array($p)) {
                $logs[] = ['client_ts' => $l['client_ts'], 'action' => $l['action'], 'payload' => $p];
            }
        }
        $stmt->closeCursor();

        $informe = null;
        if ($cita['attendance_id'] !== null) {
            try {
                $stmt = $pdo->prepare("SELECT data FROM reports WHERE attendance_id = ? AND tipo = 'OTOSCOPIA'");
                $stmt->execute([(int) $cita['attendance_id']]);
                $d = $stmt->fetchColumn();
                $stmt->closeCursor();
                $informe = $d ? json_decode((string) $d, true) : null;
            } catch (PDOException $e) {
                $informe = null;
            }
        }
        $tipos = [];
        try {
            $stmt = $pdo->prepare(
                "SELECT u.side, b.tipo FROM otoscopia_biblioteca_uso u JOIN otoscopia_biblioteca b ON b.id = u.biblioteca_id
                  WHERE u.case_id = ? ORDER BY u.fase"
            );
            $stmt->execute([(string) $cita['case_id']]);
            foreach ($stmt->fetchAll() as $f) {
                $tipos[strtolower((string) $f['side'])] = $tipos[strtolower((string) $f['side'])] ?? $f['tipo'];
            }
        } catch (PDOException $e) {
            $tipos = [];
        }
        $chat = [];
        try {
            $stmt = $pdo->prepare('SELECT role, content FROM llm_chat_logs WHERE appointment_id = ? AND student_id = ? ORDER BY id');
            $stmt->execute([$appointmentId, $studentId]);
            $chat = $stmt->fetchAll();
            $stmt->closeCursor();
        } catch (PDOException $e) {
            $chat = [];
        }
        $completa = true;
        try {
            $cfg = AppConfig::getEffective('entrevista.anamnesis', $cita['course_id'] !== null ? (int) $cita['course_id'] : null);
            $completa = (float) ($cfg['anamnesis']['general']['completa'] ?? 1) >= 1;
        } catch (Throwable $e) {
            $completa = true;
        }
        return self::evaluar($logs, $caso, ['informe_otoscopia' => is_array($informe) ? $informe : null, 'tipos_otoscopia' => $tipos,
            'chat' => $chat, 'anamnesis_completa' => $completa]);
    }

    // ---- ayudas comunes ------------------------------------------------------

    /** Segundos desde la hora del cliente (con milisegundos si los trae). */
    public static function t(array $l): float
    {
        return AudiometriaRegistro::segundos((string) $l['client_ts']);
    }

    /** 'od'/'OD' -> 0, 'oi'/'OI' -> 1, otra cosa -> null. */
    public static function oido($o): ?int
    {
        $o = strtolower((string) $o);
        return $o === 'od' ? 0 : ($o === 'oi' ? 1 : null);
    }

    /** Las filas de una acción (o de varias), en orden. */
    public static function filas(array $logs, $acciones): array
    {
        $acciones = (array) $acciones;
        return array_values(array_filter($logs, static function ($l) use ($acciones) {
            return in_array($l['action'], $acciones, true);
        }));
    }

    /** Hora de la primera fila que cumple, o null. */
    public static function primera(array $logs, callable $f): ?float
    {
        foreach ($logs as $l) {
            if ($f($l)) {
                return self::t($l);
            }
        }
        return null;
    }

    public static function lista(array $items): string
    {
        $items = array_values($items);
        if (count($items) <= 1) {
            return implode('', $items);
        }
        $ultimo = array_pop($items);
        return implode(', ', $items) . ' y ' . $ultimo;
    }
}
