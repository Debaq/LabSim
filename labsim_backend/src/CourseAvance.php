<?php

declare(strict_types=1);

require_once __DIR__ . '/AlumnoIndicadores.php';
require_once __DIR__ . '/AudiometriaTecnica.php';
require_once __DIR__ . '/Metrics.php';
require_once __DIR__ . '/ReportFile.php';

/**
 * Avance del curso (pestaña Avance de courses.php): los indicadores de cada
 * alumno dentro de ESTE curso (citas con appointments.course_id = curso, los
 * intentos de práctica libre incluidos porque también llevan el curso) y los
 * objetivos de aprendizaje que escribe el docente.
 *
 * Un objetivo es texto del docente; si se ata a un indicador con una meta,
 * se cuenta quién lo cumple. El sistema no propone objetivos: el contenido
 * docente lo pone el docente.
 */
final class CourseAvance
{
    /** Días sin cerrar una atención para que un alumno aparezca en "necesitan atención". */
    public const DIAS_SIN_ACTIVIDAD = 14;

    /**
     * Una atención que duró más que esto no se cuenta en las duraciones: la
     * dejaron abierta (se cerró al otro día, o al volver de almuerzo) y no
     * dice cuánto demoró el alumno con el paciente.
     */
    public const DURACION_MAX_S = 3 * 3600;

    /**
     * Indicadores a los que se puede atar un objetivo: rótulo, unidad y si la
     * meta es un mínimo (>=) o un máximo (<=).
     *
     * @return array<string,array{label:string, unidad:string, comparar:string}>
     */
    public static function indicadores(): array
    {
        $out = [
            'atenciones' => ['label' => 'Atenciones cerradas', 'unidad' => '', 'comparar' => '>='],
            'tecnica_promedio' => ['label' => 'Técnica de audiometría, promedio', 'unidad' => '%', 'comparar' => '>='],
            'tecnica_ultima' => ['label' => 'Técnica de audiometría, la última', 'unidad' => '%', 'comparar' => '>='],
            'informes' => ['label' => 'Informes entregados (cualquier examen)', 'unidad' => '', 'comparar' => '>='],
        ];
        foreach (ReportFile::LABELS as $tipo => $label) {
            $out['informes_' . $tipo] = ['label' => 'Informes de ' . $label, 'unidad' => '', 'comparar' => '>='];
        }
        $out += [
            'practica' => ['label' => 'Intentos de práctica libre cerrados', 'unidad' => '', 'comparar' => '>='],
            'preguntas' => ['label' => 'Preguntas al paciente por atención (mediana)', 'unidad' => '', 'comparar' => '>='],
            'duracion' => ['label' => 'Duración típica de una atención', 'unidad' => 'min', 'comparar' => '<='],
            'felicitaciones' => ['label' => 'Felicitaciones de pacientes', 'unidad' => '', 'comparar' => '>='],
            'sugerencias' => ['label' => 'Sugerencias de mejora de pacientes', 'unidad' => '', 'comparar' => '<='],
        ];
        return $out;
    }

    /** "≥ 85 %", "≤ 20 min": la meta escrita como se lee. */
    public static function metaTexto(string $indicador, ?float $meta): string
    {
        $def = self::indicadores()[$indicador] ?? null;
        if ($def === null || $meta === null) {
            return '';
        }
        $n = rtrim(rtrim(number_format($meta, 1, ',', ''), '0'), ',');
        return ($def['comparar'] === '<=' ? '≤ ' : '≥ ') . $n . ($def['unidad'] !== '' ? ' ' . $def['unidad'] : '');
    }

    /**
     * Si un valor cumple la meta del indicador. null si no hay con qué
     * medir (sin indicador, sin meta o el alumno sin datos todavía): un
     * alumno sin audiometrías no "falla" la técnica, todavía no se sabe.
     *
     * @param int|float|null $valor
     */
    public static function cumple(string $indicador, $valor, ?float $meta): ?bool
    {
        $def = self::indicadores()[$indicador] ?? null;
        if ($def === null || $meta === null || $valor === null) {
            return null;
        }
        return $def['comparar'] === '<=' ? $valor <= $meta : $valor >= $meta;
    }

    // ---- Objetivos ----------------------------------------------------------

    public static function objetivos(int $courseId): array
    {
        $stmt = Db::get()->prepare('SELECT * FROM course_objectives WHERE course_id = ? ORDER BY orden, id');
        $stmt->execute([$courseId]);
        return array_map(static function (array $o): array {
            $o['meta'] = $o['meta'] !== null ? (float) $o['meta'] : null;
            return $o;
        }, $stmt->fetchAll());
    }

    /** null si quedó guardado, o el error para mostrar. */
    public static function crearObjetivo(int $courseId, string $texto, string $indicador, string $meta, int $userId): ?string
    {
        $texto = trim($texto);
        if ($texto === '') {
            return 'Falta el texto del objetivo.';
        }
        [$indicador, $metaNum, $error] = self::validarMedicion($indicador, $meta);
        if ($error !== null) {
            return $error;
        }
        $pdo = Db::get();
        $stmt = $pdo->prepare('SELECT COALESCE(MAX(orden), 0) + 1 FROM course_objectives WHERE course_id = ?');
        $stmt->execute([$courseId]);
        $orden = (int) $stmt->fetchColumn();
        $stmt->closeCursor();   // ver Db::get: lectura abierta + escritura = "database is locked"
        $pdo->prepare('INSERT INTO course_objectives (course_id, texto, indicador, meta, orden, created_by) VALUES (?, ?, ?, ?, ?, ?)')
            ->execute([$courseId, mb_substr($texto, 0, 500), $indicador, $metaNum, $orden, $userId]);
        return null;
    }

    public static function editarObjetivo(int $courseId, int $id, string $texto, string $indicador, string $meta): ?string
    {
        $texto = trim($texto);
        if ($texto === '') {
            return 'Falta el texto del objetivo.';
        }
        [$indicador, $metaNum, $error] = self::validarMedicion($indicador, $meta);
        if ($error !== null) {
            return $error;
        }
        Db::get()->prepare('UPDATE course_objectives SET texto = ?, indicador = ?, meta = ? WHERE id = ? AND course_id = ?')
            ->execute([mb_substr($texto, 0, 500), $indicador, $metaNum, $id, $courseId]);
        return null;
    }

    public static function borrarObjetivo(int $courseId, int $id): void
    {
        Db::get()->prepare('DELETE FROM course_objectives WHERE id = ? AND course_id = ?')->execute([$id, $courseId]);
    }

    /** Sube o baja un objetivo un lugar ($delta -1 / +1). */
    public static function moverObjetivo(int $courseId, int $id, int $delta): void
    {
        $ids = array_map('intval', array_column(self::objetivos($courseId), 'id'));
        $i = array_search($id, $ids, true);
        $j = $i === false ? false : $i + $delta;
        if ($i === false || $j < 0 || $j >= count($ids)) {
            return;
        }
        [$ids[$i], $ids[$j]] = [$ids[$j], $ids[$i]];
        $stmt = Db::get()->prepare('UPDATE course_objectives SET orden = ? WHERE id = ? AND course_id = ?');
        foreach ($ids as $orden => $oid) {
            $stmt->execute([$orden + 1, $oid, $courseId]);
        }
    }

    /** @return array{0:string, 1:?float, 2:?string} indicador, meta, error */
    public static function validarMedicion(string $indicador, string $meta): array
    {
        $indicador = trim($indicador);
        if ($indicador === '') {
            return ['', null, null];
        }
        if (!isset(self::indicadores()[$indicador])) {
            return ['', null, 'Ese indicador no existe.'];
        }
        $meta = str_replace(',', '.', trim($meta));
        if ($meta === '' || !is_numeric($meta) || (float) $meta < 0) {
            return ['', null, 'Para medirlo hace falta una meta: un número mayor o igual a 0.'];
        }
        return [$indicador, (float) $meta, null];
    }

    // ---- Indicadores por alumno ---------------------------------------------

    /**
     * Los valores de cada alumno del curso (sin el demo), por id. Para cada
     * uno: los de indicadores() más 'nombre', 'username', 'ultima' (fecha de
     * su última atención cerrada), 'serie' (técnica en orden cronológico:
     * [fecha, pct]) y 'tecnicas' (resultados completos, para los pasos).
     */
    public static function porAlumno(int $courseId): array
    {
        $pdo = Db::get();
        $stmt = $pdo->prepare(
            'SELECT u.id, u.username, u.display_name FROM course_students cs
               JOIN users u ON u.id = cs.user_id
              WHERE cs.course_id = ? AND u.is_demo = 0 ORDER BY u.display_name'
        );
        $stmt->execute([$courseId]);
        $alumnos = [];
        foreach ($stmt->fetchAll() as $u) {
            $alumnos[(int) $u['id']] = [
                'nombre' => (string) $u['display_name'], 'username' => (string) $u['username'],
                'atenciones' => 0, 'en_curso' => 0, 'practica' => 0, 'informes' => 0,
                'felicitaciones' => 0, 'sugerencias' => 0,
                'tecnica_promedio' => null, 'tecnica_ultima' => null, 'preguntas' => null, 'duracion' => null,
                'ultima' => null, 'serie' => [], 'tecnicas' => [], 'duraciones' => [],
            ] + array_fill_keys(array_map(static function (string $t): string {
                return 'informes_' . $t;
            }, array_keys(ReportFile::LABELS)), 0);
        }
        if (!$alumnos) {
            return [];
        }
        $ids = array_keys($alumnos);
        $ph = implode(',', array_fill(0, count($ids), '?'));

        $stmt = $pdo->prepare(
            "SELECT att.id AS attendance_id, att.student_id, att.estado, att.hora_real, att.updated_at,
                    a.id AS appointment_id, a.practice_id
               FROM attendances att JOIN appointments a ON a.id = att.appointment_id
              WHERE a.course_id = ? AND att.student_id IN ({$ph})
              ORDER BY att.updated_at"
        );
        $stmt->execute(array_merge([$courseId], $ids));
        $atenciones = $stmt->fetchAll();

        $preguntas = self::porCita($pdo, "SELECT l.appointment_id, l.student_id, COUNT(*) AS n FROM llm_chat_logs l
                JOIN appointments a ON a.id = l.appointment_id
               WHERE a.course_id = ? AND l.role = 'user' GROUP BY l.appointment_id, l.student_id", [$courseId]);

        $stmt = $pdo->prepare(
            "SELECT att.student_id, r.tipo, COUNT(*) AS n FROM reports r
               JOIN attendances att ON att.id = r.attendance_id
               JOIN appointments a ON a.id = att.appointment_id
              WHERE a.course_id = ? GROUP BY att.student_id, r.tipo"
        );
        $stmt->execute([$courseId]);
        foreach ($stmt->fetchAll() as $r) {
            $uid = (int) $r['student_id'];
            if (isset($alumnos[$uid])) {
                $alumnos[$uid]['informes'] += (int) $r['n'];
                $k = 'informes_' . $r['tipo'];
                if (array_key_exists($k, $alumnos[$uid])) {
                    $alumnos[$uid][$k] += (int) $r['n'];
                }
            }
        }

        $stmt = $pdo->prepare(
            "SELECT m.student_id, m.tipo, COUNT(*) AS n FROM inbox_messages m
               JOIN appointments a ON a.id = m.appointment_id
              WHERE a.course_id = ? AND m.tipo IN ('merito', 'reclamo') GROUP BY m.student_id, m.tipo"
        );
        $stmt->execute([$courseId]);
        foreach ($stmt->fetchAll() as $r) {
            $uid = (int) $r['student_id'];
            if (isset($alumnos[$uid])) {
                $alumnos[$uid][$r['tipo'] === 'merito' ? 'felicitaciones' : 'sugerencias'] += (int) $r['n'];
            }
        }

        // Técnica: una consulta por alumno solo para lo que no esté guardado
        // (ver AudiometriaTecnica::deAtenciones). Antes se traían de una vez
        // todas las filas del audiómetro del curso (~70 mil): 11 s y 70 MB.
        $citasAlumno = [];
        foreach ($atenciones as $a) {
            $citasAlumno[(int) $a['student_id']][] = (int) $a['appointment_id'];
        }
        $tecnicas = [];
        foreach ($citasAlumno as $uid => $citas) {
            $tecnicas[$uid] = AudiometriaTecnica::deAtenciones($uid, $citas);
        }

        $duraciones = $preguntasAlumno = [];
        foreach ($atenciones as $a) {
            $uid = (int) $a['student_id'];
            $ap = (int) $a['appointment_id'];
            $practica = $a['practice_id'] !== null;
            if ($a['estado'] === 'atendido') {
                $alumnos[$uid][$practica ? 'practica' : 'atenciones']++;
                $alumnos[$uid]['ultima'] = substr((string) $a['updated_at'], 0, 10);
                if (!$practica) {
                    $d = Metrics::attendanceDurationSeconds($a['hora_real'], $a['updated_at']);
                    if ($d !== null && $d <= self::DURACION_MAX_S) {
                        $duraciones[$uid][] = $d;
                    }
                }
            } elseif ($a['estado'] === 'atendiendo' && !$practica) {
                $alumnos[$uid]['en_curso']++;
            }
            if (!$practica && isset($preguntas[$ap][$uid])) {
                $preguntasAlumno[$uid][] = $preguntas[$ap][$uid];
            }
            $tec = $tecnicas[$uid][$ap] ?? null;
            if ($tec !== null) {
                if ($tec['puntaje']['pct'] !== null) {
                    $alumnos[$uid]['tecnicas'][] = $tec;
                    $alumnos[$uid]['serie'][] = [substr((string) $a['updated_at'], 0, 10), (int) $tec['puntaje']['pct']];
                }
            }
        }
        foreach ($alumnos as $uid => &$al) {
            $pcts = array_column($al['serie'], 1);
            $al['tecnica_promedio'] = AlumnoIndicadores::promedio($pcts);
            $al['tecnica_ultima'] = $pcts ? end($pcts) : null;
            $al['tendencia'] = AlumnoIndicadores::tendencia($pcts);
            $al['preguntas'] = AlumnoIndicadores::mediana($preguntasAlumno[$uid] ?? []);
            $med = AlumnoIndicadores::mediana($duraciones[$uid] ?? []);
            $al['duracion'] = $med !== null ? (int) round($med / 60) : null;
            $al['duraciones'] = $duraciones[$uid] ?? [];
        }
        unset($al);
        return $alumnos;
    }

    /** [appointment_id][student_id] => n */
    private static function porCita(PDO $pdo, string $sql, array $args): array
    {
        $stmt = $pdo->prepare($sql);
        $stmt->execute($args);
        $out = [];
        foreach ($stmt->fetchAll() as $r) {
            $out[(int) $r['appointment_id']][(int) $r['student_id']] = (int) $r['n'];
        }
        return $out;
    }

    // ---- Lo que se pinta ----------------------------------------------------

    /**
     * Cada objetivo con cuántos alumnos lo cumplen, cuántos no y cuántos
     * todavía sin datos.
     */
    public static function resumenObjetivos(array $objetivos, array $alumnos): array
    {
        foreach ($objetivos as &$o) {
            $o['cumplen'] = $o['no_cumplen'] = $o['sin_datos'] = 0;
            if ($o['indicador'] === '') {
                continue;
            }
            foreach ($alumnos as $al) {
                $c = self::cumple($o['indicador'], $al[$o['indicador']] ?? null, $o['meta']);
                $o[$c === null ? 'sin_datos' : ($c ? 'cumplen' : 'no_cumplen')]++;
            }
        }
        unset($o);
        return $objetivos;
    }

    /**
     * Por semana (lunes): atenciones cerradas de prácticos, su duración
     * promedio y el promedio de la técnica de las audiometrías de esa
     * semana. Semanas sin nada no salen.
     *
     * @return array<string,array{atenciones:int, duracion_s:?int, tecnica:?int, n_tecnica:int}> 'Y-m-d' del lunes => ...
     */
    public static function porSemana(array $alumnos, int $courseId): array
    {
        $stmt = Db::get()->prepare(
            "SELECT att.updated_at, att.hora_real FROM attendances att JOIN appointments a ON a.id = att.appointment_id
              WHERE a.course_id = ? AND att.estado = 'atendido' AND a.practice_id IS NULL"
        );
        $stmt->execute([$courseId]);
        $semanas = $durSemana = [];
        $lunes = static function (string $fecha): string {
            $t = strtotime($fecha);
            return date('Y-m-d', $t - ((int) date('N', $t) - 1) * 86400);
        };
        foreach ($stmt->fetchAll() as $r) {
            $k = $lunes((string) $r['updated_at']);
            $semanas[$k]['atenciones'] = ($semanas[$k]['atenciones'] ?? 0) + 1;
            $d = Metrics::attendanceDurationSeconds($r['hora_real'], $r['updated_at']);
            if ($d !== null && $d <= self::DURACION_MAX_S) {
                $durSemana[$k][] = $d;
            }
        }
        foreach ($durSemana as $k => $lista) {
            $semanas[$k]['duracion_s'] = AlumnoIndicadores::promedio($lista);
        }
        $pcts = [];
        foreach ($alumnos as $al) {
            foreach ($al['serie'] as [$fecha, $pct]) {
                $pcts[$lunes($fecha)][] = $pct;
            }
        }
        foreach ($pcts as $k => $lista) {
            $semanas[$k]['tecnica'] = AlumnoIndicadores::promedio($lista);
            $semanas[$k]['n_tecnica'] = count($lista);
        }
        foreach ($semanas as &$s) {
            $s += ['atenciones' => 0, 'tecnica' => null, 'n_tecnica' => 0, 'duracion_s' => null];
        }
        unset($s);
        ksort($semanas);
        return $semanas;
    }

    /**
     * Pasos de la técnica que más le cuestan al curso, contando ALUMNOS (no
     * atenciones): "7 de 12 alumnos no parten por el oído mejor". Un alumno
     * cuenta como que falla un paso si lo falló en la mayoría de las
     * audiometrías donde se evaluó, así un error de la primera semana no lo
     * deja marcado para siempre.
     *
     * @return array<int,array{seccion:string, texto:string, alumnos:int, evaluados:int}>
     */
    public static function pasosDelCurso(array $alumnos): array
    {
        $cuenta = [];
        foreach ($alumnos as $al) {
            foreach (AlumnoIndicadores::conteoPasos($al['tecnicas']) as $k => $p) {
                if (!isset($cuenta[$k])) {
                    $cuenta[$k] = ['seccion' => $p['seccion'], 'texto' => $p['texto'], 'alumnos' => 0, 'evaluados' => 0];
                }
                $cuenta[$k]['evaluados']++;
                if (2 * $p['fallos'] > $p['evaluadas']) {
                    $cuenta[$k]['alumnos']++;
                }
            }
        }
        $out = array_values(array_filter($cuenta, static function (array $c): bool {
            return $c['alumnos'] > 0;
        }));
        usort($out, static function (array $a, array $b): int {
            return [$b['alumnos'] / $b['evaluados'], $b['alumnos']] <=> [$a['alumnos'] / $a['evaluados'], $a['alumnos']];
        });
        return $out;
    }

    /**
     * Alumnos que el docente debería mirar, con el motivo: sin ninguna
     * atención cerrada, sin cerrar una hace DIAS_SIN_ACTIVIDAD días, técnica
     * promedio bajo 60 % o que viene bajando 10 puntos o más.
     *
     * @return array<int,array{nombre:string, motivos:array<int,string>}> por id de alumno
     */
    public static function necesitanAtencion(array $alumnos, string $hoy): array
    {
        $out = [];
        $limite = date('Y-m-d', strtotime($hoy) - self::DIAS_SIN_ACTIVIDAD * 86400);
        foreach ($alumnos as $uid => $al) {
            $motivos = [];
            if ($al['atenciones'] === 0) {
                $motivos[] = 'sin atenciones cerradas';
            } elseif ($al['ultima'] !== null && $al['ultima'] < $limite) {
                $motivos[] = 'sin cerrar atenciones desde ' . $al['ultima'];
            }
            if ($al['tecnica_promedio'] !== null && $al['tecnica_promedio'] < 60) {
                $motivos[] = 'técnica ' . $al['tecnica_promedio'] . ' %';
            }
            if (($al['tendencia'] ?? null) !== null && $al['tendencia'] <= -10) {
                $motivos[] = 'técnica bajando (' . $al['tendencia'] . ' pts)';
            }
            if ($motivos) {
                $out[$uid] = ['nombre' => $al['nombre'], 'motivos' => $motivos];
            }
        }
        return $out;
    }
}
