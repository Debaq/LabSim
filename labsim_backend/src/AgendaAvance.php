<?php

declare(strict_types=1);

require_once __DIR__ . '/AlumnoIndicadores.php';
require_once __DIR__ . '/Metrics.php';

/**
 * Avance de la agenda relativa (parte 4; docs/decisiones.md "Agenda
 * relativa al ingreso del alumno"): para que el docente vea si el problema
 * es del alumno o de la agenda.
 *
 * Por alumno:
 *   - atraso al iniciar: hora en que abrió la atención menos el inicio de
 *     su turno (mediana, minutos; negativo = antes);
 *   - box pasado: cuánto después del fin de su bloque (fin del último turno
 *     del día) cerró su última atención de ese día (mediana por día, 0 si
 *     terminó a tiempo);
 *   - horario libre: lo que quedó para después (continuaciones que pidió y
 *     pacientes con duración que no atendió en su día) y cómo terminó: a
 *     tiempo, fuera de plazo, vencido sin atender o todavía abierto.
 * Por paciente (caso + duración planificada): duración real (mediana) y
 * cuántas atenciones se pasaron. Si casi todos se pasan, la duración está
 * corta.
 *
 * Los turnos los calcula la app y los registra una vez al día en
 * action_logs ('agenda_turnos', core/agenda_relativa.py): sin ese registro
 * no hay atraso ni box para ese día, el resto sale de la base.
 *
 * Horas: attendances.hora_real y updated_at están en UTC (SQLite); los
 * turnos, en la hora local del laboratorio (Clock::ZONA).
 */
final class AgendaAvance
{
    /** Primer día de práctico después de $fechaBase ('d-m-y'), o null. @param list<string> $fechasPractico */
    public static function plazo(string $fechaBase, array $fechasPractico): ?string
    {
        $base = self::fecha($fechaBase);
        if ($base === null) {
            return null;
        }
        $mejor = null;
        foreach ($fechasPractico as $f) {
            $d = self::fecha($f);
            if ($d !== null && $d > $base && ($mejor === null || $d < $mejor)) {
                $mejor = $d;
            }
        }
        return $mejor;
    }

    /**
     * Cómo terminó un pendiente de horario libre.
     * $cierre: fecha local 'Y-m-d' en que se atendió, o null.
     */
    public static function estadoPendiente(?string $cierre, ?string $plazo, string $hoy): string
    {
        if ($cierre !== null) {
            return ($plazo === null || $cierre < $plazo) ? 'a_tiempo' : 'fuera_de_plazo';
        }
        return ($plazo !== null && $hoy >= $plazo) ? 'vencido' : 'abierto';
    }

    /** Inicio (local) de una atención: hora_real UTC del día de updated_at (o el anterior). */
    public static function inicioLocal(?string $horaReal, ?string $updatedAt): ?DateTimeImmutable
    {
        $dur = Metrics::attendanceDurationSeconds($horaReal, $updatedAt);
        $fin = self::cierreLocal($updatedAt);
        return ($dur === null || $fin === null) ? null : $fin->modify('-' . $dur . ' seconds');
    }

    public static function cierreLocal(?string $updatedAt): ?DateTimeImmutable
    {
        if (!$updatedAt) {
            return null;
        }
        try {
            return Clock::fromUtc($updatedAt);
        } catch (Exception $e) {
            return null;
        }
    }

    /**
     * @param array<int,string> $alumnos [user_id => nombre]
     * @return array{hay:bool, alumnos:array<int,array>, pacientes:list<array>}
     */
    public static function porCurso(int $courseId, array $alumnos): array
    {
        $vacio = ['hay' => false, 'alumnos' => [], 'pacientes' => []];
        if (!$alumnos || !Db::tieneColumna('appointments', 'duracion_min')) {
            return $vacio;
        }
        $pdo = Db::get();
        $conCont = Db::tieneColumna('appointments', 'continua_de');
        $sinCont = $conCont ? ' AND continua_de IS NULL' : '';
        $stmt = $pdo->prepare(
            'SELECT id, fecha, hora, nombre, apellido, case_id, duracion_min, assigned_student_id, assigned_group_id
               FROM appointments WHERE course_id = ? AND duracion_min IS NOT NULL' . $sinCont . ' AND ' . Practica::sinPractica()
        );
        $stmt->execute([$courseId]);
        $relativas = [];
        foreach ($stmt->fetchAll() as $r) {
            $relativas[(int) $r['id']] = $r;
        }
        $continuaciones = [];
        if ($conCont) {
            $stmt = $pdo->prepare(
                'SELECT id, fecha, continua_de, assigned_student_id FROM appointments
                  WHERE course_id = ? AND continua_de IS NOT NULL'
            );
            $stmt->execute([$courseId]);
            $continuaciones = $stmt->fetchAll();
        }
        if (!$relativas && !$continuaciones) {
            return $vacio;
        }
        $fechasPractico = array_values(array_unique(array_column($relativas, 'fecha')));
        $hoy = Clock::now()->format('Y-m-d');
        $ids = array_keys($alumnos);
        $ph = implode(',', array_fill(0, count($ids), '?'));

        // Atenciones de los alumnos sobre esas citas.
        $citas = array_merge(array_keys($relativas), array_map(static fn($c) => (int) $c['id'], $continuaciones));
        $atenciones = [];   // [appointment_id][student_id] => fila
        if ($citas) {
            $phc = implode(',', array_fill(0, count($citas), '?'));
            $stmt = $pdo->prepare(
                "SELECT appointment_id, student_id, estado, hora_real, updated_at FROM attendances
                  WHERE appointment_id IN ({$phc}) AND student_id IN ({$ph})"
            );
            $stmt->execute(array_merge($citas, $ids));
            foreach ($stmt->fetchAll() as $a) {
                $atenciones[(int) $a['appointment_id']][(int) $a['student_id']] = $a;
            }
        }

        // Quién ve cada cita relativa (todo el curso, su grupo o él).
        $grupos = [];
        foreach ($pdo->query('SELECT group_id, user_id FROM group_members') as $g) {
            $grupos[(int) $g['group_id']][] = (int) $g['user_id'];
        }
        $leToca = static function (array $cita, int $uid) use ($grupos): bool {
            if ($cita['assigned_student_id'] !== null) {
                return (int) $cita['assigned_student_id'] === $uid;
            }
            if ($cita['assigned_group_id'] !== null) {
                return in_array($uid, $grupos[(int) $cita['assigned_group_id']] ?? [], true);
            }
            return true;
        };

        // Turnos registrados por la app: el primero de cada alumno y día.
        $turnos = [];   // [uid][fecha] => [appointment_id => [inicio, fin]]
        $desde = null;
        foreach ($fechasPractico as $f) {
            $d = self::fecha($f);
            if ($d !== null && ($desde === null || $d < $desde)) {
                $desde = $d;
            }
        }
        if ($desde !== null) {
            $stmt = $pdo->prepare(
                "SELECT user_id, payload FROM action_logs
                  WHERE user_id IN ({$ph}) AND client_ts >= ? AND action = 'agenda_turnos' ORDER BY id"
            );
            $stmt->execute(array_merge($ids, [$desde]));
            foreach ($stmt->fetchAll() as $l) {
                $p = json_decode((string) $l['payload'], true);
                $uid = (int) $l['user_id'];
                $f = is_array($p) ? (string) ($p['fecha'] ?? '') : '';
                if ($f === '' || isset($turnos[$uid][$f]) || !is_array($p['turnos'] ?? null)) {
                    continue;
                }
                foreach ($p['turnos'] as $t) {
                    $turnos[$uid][$f][(int) ($t['appointment_id'] ?? 0)] = [(string) ($t['inicio'] ?? ''), (string) ($t['fin'] ?? '')];
                }
            }
        }

        $out = [];
        foreach ($alumnos as $uid => $nombre) {
            $atrasos = $boxes = [];
            foreach ($turnos[$uid] ?? [] as $fecha => $delDia) {
                $fd = self::fecha($fecha);
                if ($fd === null) {
                    continue;
                }
                $finBox = null;
                $ultimoCierre = null;
                foreach ($delDia as $cita => [$ini, $fin]) {
                    $finT = self::local($fd, $fin);
                    if ($finT !== null && ($finBox === null || $finT > $finBox)) {
                        $finBox = $finT;
                    }
                    $a = $atenciones[$cita][$uid] ?? null;
                    if ($a === null) {
                        continue;
                    }
                    $inicio = self::inicioLocal($a['hora_real'], $a['updated_at']);
                    $iniT = self::local($fd, $ini);
                    if ($inicio !== null && $iniT !== null && $inicio->format('Y-m-d') === $fd) {
                        $atrasos[] = ($inicio->getTimestamp() - $iniT->getTimestamp()) / 60;
                    }
                    $cierre = $a['estado'] === 'atendido' ? self::cierreLocal($a['updated_at']) : null;
                    if ($cierre !== null && $cierre->format('Y-m-d') === $fd && ($ultimoCierre === null || $cierre > $ultimoCierre)) {
                        $ultimoCierre = $cierre;
                    }
                }
                if ($finBox !== null && $ultimoCierre !== null) {
                    $boxes[] = max(0, ($ultimoCierre->getTimestamp() - $finBox->getTimestamp()) / 60);
                }
            }

            $libre = ['a_tiempo' => 0, 'fuera_de_plazo' => 0, 'vencido' => 0, 'abierto' => 0];
            foreach ($continuaciones as $c) {
                if ((int) $c['assigned_student_id'] !== $uid) {
                    continue;
                }
                $a = $atenciones[(int) $c['id']][$uid] ?? null;
                $cierre = ($a !== null && $a['estado'] === 'atendido') ? self::cierreLocal($a['updated_at']) : null;
                $libre[self::estadoPendiente($cierre ? $cierre->format('Y-m-d') : null,
                    self::plazo((string) $c['fecha'], $fechasPractico), $hoy)]++;
            }
            foreach ($relativas as $id => $cita) {
                $fd = self::fecha((string) $cita['fecha']);
                if ($fd === null || $fd >= $hoy || !$leToca($cita, $uid)) {
                    continue;
                }
                $a = $atenciones[$id][$uid] ?? null;
                $cierre = ($a !== null && $a['estado'] === 'atendido') ? self::cierreLocal($a['updated_at']) : null;
                if ($cierre !== null && $cierre->format('Y-m-d') <= $fd) {
                    continue;   // atendido en su día: no quedó pendiente
                }
                $libre[self::estadoPendiente($cierre ? $cierre->format('Y-m-d') : null,
                    self::plazo((string) $cita['fecha'], $fechasPractico), $hoy)]++;
            }

            $med = AlumnoIndicadores::mediana($atrasos);
            $medBox = AlumnoIndicadores::mediana($boxes);
            $out[$uid] = [
                'nombre' => $nombre,
                'dias' => count($turnos[$uid] ?? []),
                'atraso_min' => $med !== null ? (int) round($med) : null,
                'box_min' => $medBox !== null ? (int) round($medBox) : null,
                'libre' => $libre,
            ];
        }

        // Por paciente: caso + duración planificada.
        $pacientes = [];
        foreach ($relativas as $id => $cita) {
            $k = $cita['case_id'] . '|' . $cita['duracion_min'];
            $pacientes[$k] = $pacientes[$k] ?? [
                'nombre' => trim($cita['nombre'] . ' ' . $cita['apellido']),
                'duracion_min' => (int) $cita['duracion_min'], 'duraciones' => [],
            ];
            foreach ($atenciones[$id] ?? [] as $a) {
                if ($a['estado'] !== 'atendido') {
                    continue;
                }
                $d = Metrics::attendanceDurationSeconds($a['hora_real'], $a['updated_at']);
                if ($d !== null && $d <= CourseAvance::DURACION_MAX_S) {
                    $pacientes[$k]['duraciones'][] = $d / 60;
                }
            }
        }
        $lista = [];
        foreach ($pacientes as $p) {
            $n = count($p['duraciones']);
            $med = AlumnoIndicadores::mediana($p['duraciones']);
            $lista[] = [
                'nombre' => $p['nombre'], 'duracion_min' => $p['duracion_min'], 'n' => $n,
                'real_min' => $med !== null ? (int) round($med) : null,
                'pasados' => count(array_filter($p['duraciones'], static fn($d) => $d > $p['duracion_min'])),
            ];
        }
        usort($lista, static fn($a, $b) => strcmp($a['nombre'], $b['nombre']));

        return ['hay' => true, 'alumnos' => $out, 'pacientes' => $lista];
    }

    /** 'd-m-y' -> 'Y-m-d', o null. */
    private static function fecha(string $dmy): ?string
    {
        $d = DateTimeImmutable::createFromFormat('!d-m-y', $dmy, new DateTimeZone(Clock::ZONA));
        return $d === false ? null : $d->format('Y-m-d');
    }

    /** 'Y-m-d' + 'H:i' en la hora local. */
    private static function local(string $ymd, string $hm): ?DateTimeImmutable
    {
        $d = DateTimeImmutable::createFromFormat('Y-m-d H:i', $ymd . ' ' . substr($hm, 0, 5), new DateTimeZone(Clock::ZONA));
        return $d === false ? null : $d;
    }
}
