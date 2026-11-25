<?php

declare(strict_types=1);

/**
 * OSCE: evaluación por estaciones (plan en docs/osce_plan.md).
 *
 * Todo lo del evento se configura al crearlo (curso, inicio, duración de la
 * estación, pausa, circuitos, estaciones, exigencia); el sistema calcula el
 * resto: vueltas, recorrido de cada alumno, códigos y QR, y el reloj.
 *
 * Rotación: un circuito tiene un puesto por estación. En cada vuelta entran
 * hasta (estaciones × circuitos) alumnos; cada uno parte en un puesto y
 * avanza uno por tiempo hasta pasar por todas. Con más alumnos que puestos
 * hay más vueltas, repartidas parejas (17 en 6 puestos: 6 + 6 + 5).
 *
 * Reloj: corre desde que el docente aprieta "Iniciar" (inicio_epoch) menos
 * lo que estuvo en pausa. Todas las pantallas (proyector, página del QR,
 * estaciones) calculan la fase con estadoReloj() y la misma configuración.
 */
final class Osce
{
    public const TIPOS = [
        'pauta_docente' => 'Pauta docente (presencial)',
        'preguntas' => 'Preguntas en tablet',
        'config_equipo' => 'Configuración del equipo (LabSim)',
        'marcaje' => 'Marcaje de curvas (LabSim)',
        'protocolo' => 'Ejecución del protocolo (LabSim)',
        'conclusion' => 'Conclusión / informe',
    ];

    public const EXAMENES = [
        'peatc' => 'PEATC clínico',
        'aabr' => 'PEATC automatizado (AABR)',
        'ecochg' => 'Electrococleografía',
        'latencia_media' => 'Latencia media',
        'latencia_tardia' => 'Latencia tardía',
        'estado_estable' => 'Estado estable',
        'cvemp' => 'cVEMP',
        'ovemp' => 'oVEMP',
        'general' => 'General / varios',
    ];

    public const ESTADOS = [
        'borrador' => 'Borrador',
        'en_curso' => 'En curso',
        'cerrado' => 'Cerrado',
        'publicado' => 'Resultados publicados',
    ];

    /** Las seis estaciones del plan, para empezar un OSCE de electrofisiología. */
    public const ESTACIONES_BASE = [
        ['pauta_docente', 'Limpieza y preparación de electrodos', 'peatc'],
        ['preguntas', 'Preguntas', 'general'],
        ['config_equipo', 'Configuración del examen', 'peatc'],
        ['marcaje', 'Marcaje y detección de curvas', 'peatc'],
        ['protocolo', 'Protocolo de evaluación', 'peatc'],
        ['conclusion', 'Conclusión', 'peatc'],
    ];

    /** Sin 0/O, 1/I/L: el código se dicta y se escribe a mano. */
    private const ALFABETO = '23456789ABCDEFGHJKMNPQRSTUVWXYZ';

    public static function migrar(): void
    {
        static $hecho = false;
        if ($hecho) {
            return;
        }
        $pdo = Db::get();
        $pdo->exec(
            "CREATE TABLE IF NOT EXISTS osce (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                course_id INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
                nombre TEXT NOT NULL,
                inicio_programado TEXT NOT NULL DEFAULT '',
                duracion_s INTEGER NOT NULL DEFAULT 480,
                pausa_s INTEGER NOT NULL DEFAULT 120,
                pausa_vueltas_s INTEGER NOT NULL DEFAULT 600,
                circuitos INTEGER NOT NULL DEFAULT 1,
                exigencia INTEGER NOT NULL DEFAULT 60,
                nota_aprobacion REAL NOT NULL DEFAULT 4.0,
                rotacion TEXT NOT NULL DEFAULT 'cadena',
                por_turno INTEGER NOT NULL DEFAULT 2,
                estado TEXT NOT NULL DEFAULT 'borrador',
                inicio_epoch INTEGER,
                pausado_desde INTEGER,
                pausado_acum_s INTEGER NOT NULL DEFAULT 0,
                reloj_token TEXT NOT NULL,
                created_by INTEGER,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                publicado_at TEXT
            )"
        );
        $pdo->exec(
            "CREATE TABLE IF NOT EXISTS osce_estacion (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                osce_id INTEGER NOT NULL REFERENCES osce(id) ON DELETE CASCADE,
                orden INTEGER NOT NULL DEFAULT 0,
                tipo TEXT NOT NULL,
                titulo TEXT NOT NULL,
                examen TEXT NOT NULL DEFAULT 'general',
                peso REAL NOT NULL DEFAULT 1,
                config TEXT NOT NULL DEFAULT '{}'
            )"
        );
        $pdo->exec(
            "CREATE TABLE IF NOT EXISTS osce_item (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estacion_id INTEGER NOT NULL REFERENCES osce_estacion(id) ON DELETE CASCADE,
                orden INTEGER NOT NULL DEFAULT 0,
                texto TEXT NOT NULL,
                puntaje REAL NOT NULL DEFAULT 1,
                critico INTEGER NOT NULL DEFAULT 0,
                tipo TEXT NOT NULL DEFAULT 'tick',
                config TEXT NOT NULL DEFAULT '{}'
            )"
        );
        $pdo->exec(
            "CREATE TABLE IF NOT EXISTS osce_pregunta (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                estacion_id INTEGER NOT NULL REFERENCES osce_estacion(id) ON DELETE CASCADE,
                orden INTEGER NOT NULL DEFAULT 0,
                tipo TEXT NOT NULL DEFAULT 'alternativa',
                enunciado TEXT NOT NULL,
                alternativas TEXT NOT NULL DEFAULT '[]',
                clave TEXT NOT NULL DEFAULT '',
                pauta TEXT NOT NULL DEFAULT '',
                puntaje REAL NOT NULL DEFAULT 1
            )"
        );
        $pdo->exec(
            "CREATE TABLE IF NOT EXISTS osce_participante (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                osce_id INTEGER NOT NULL REFERENCES osce(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id),
                numero INTEGER NOT NULL DEFAULT 0,
                codigo TEXT NOT NULL,
                token TEXT NOT NULL UNIQUE,
                vuelta INTEGER NOT NULL DEFAULT 0,
                circuito INTEGER NOT NULL DEFAULT 0,
                puesto INTEGER NOT NULL DEFAULT 0,
                variante TEXT NOT NULL DEFAULT '{}',
                UNIQUE (osce_id, user_id),
                UNIQUE (osce_id, codigo)
            )"
        );
        // Lo que el alumno hizo en una estación: una fila por estación, con
        // el puntaje total; el detalle por ítem o pregunta va en osce_resultado.
        $pdo->exec(
            "CREATE TABLE IF NOT EXISTS osce_entrega (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                participante_id INTEGER NOT NULL REFERENCES osce_participante(id) ON DELETE CASCADE,
                estacion_id INTEGER NOT NULL REFERENCES osce_estacion(id) ON DELETE CASCADE,
                estado TEXT NOT NULL DEFAULT 'en_curso',
                inicio_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                enviada_at TEXT,
                puntaje REAL,
                puntaje_max REAL,
                critico_fallado INTEGER NOT NULL DEFAULT 0,
                feedback TEXT NOT NULL DEFAULT '',
                UNIQUE (participante_id, estacion_id)
            )"
        );
        $pdo->exec(
            "CREATE TABLE IF NOT EXISTS osce_resultado (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entrega_id INTEGER NOT NULL REFERENCES osce_entrega(id) ON DELETE CASCADE,
                item_id INTEGER REFERENCES osce_item(id) ON DELETE SET NULL,
                pregunta_id INTEGER REFERENCES osce_pregunta(id) ON DELETE SET NULL,
                valor TEXT NOT NULL DEFAULT '',
                puntaje REAL,
                comentario TEXT NOT NULL DEFAULT '',
                ia_puntaje REAL,
                ia_comentario TEXT NOT NULL DEFAULT '',
                fuente TEXT NOT NULL DEFAULT 'docente',
                evaluador_id INTEGER,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"
        );
        $pdo->exec(
            "CREATE TABLE IF NOT EXISTS osce_replica (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                resultado_id INTEGER NOT NULL REFERENCES osce_resultado(id) ON DELETE CASCADE,
                texto TEXT NOT NULL,
                respuesta TEXT NOT NULL DEFAULT '',
                estado TEXT NOT NULL DEFAULT 'pendiente',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                resuelta_at TEXT
            )"
        );
        self::migrarTarjetas($pdo);
        // Columnas que llegaron después de crear la tabla (paso 3: corrección con IA).
        $cols = array_column($pdo->query('PRAGMA table_info(osce_resultado)')->fetchAll(), 'name');
        if (!in_array('ia_puntaje', $cols, true)) {
            $pdo->exec('ALTER TABLE osce_resultado ADD COLUMN ia_puntaje REAL');
        }
        if (!in_array('ia_comentario', $cols, true)) {
            $pdo->exec("ALTER TABLE osce_resultado ADD COLUMN ia_comentario TEXT NOT NULL DEFAULT ''");
        }
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_osce_course ON osce(course_id)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_osce_estacion ON osce_estacion(osce_id, orden)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_osce_item ON osce_item(estacion_id, orden)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_osce_pregunta ON osce_pregunta(estacion_id, orden)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_osce_entrega ON osce_entrega(estacion_id)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_osce_resultado ON osce_resultado(entrega_id)');
        $hecho = true;
    }

    /**
     * URL absoluta de una página bajo public/ ($rel = 'student/osce.php?t=...'),
     * para los QR. Sale del request actual: el hosting puede vivir en una
     * subcarpeta y no hay una URL base configurada.
     */
    public static function urlPublica(string $rel): string
    {
        $https = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off')
            || strtolower((string) ($_SERVER['HTTP_X_FORWARDED_PROTO'] ?? '')) === 'https';
        $host = (string) ($_SERVER['HTTP_HOST'] ?? 'localhost');
        $script = str_replace('\\', '/', (string) ($_SERVER['SCRIPT_NAME'] ?? '/public/admin/x.php'));
        $pos = strrpos($script, '/public/');
        $base = $pos === false ? rtrim(dirname(dirname($script)), '/') : substr($script, 0, $pos + 7);
        return ($https ? 'https' : 'http') . '://' . $host . $base . '/' . ltrim($rel, '/');
    }

    /**
     * Tarjetas sorteadas (2026-11-25): la tarjeta nace sin dueño (user_id
     * NULL) y con número de entrada; rotación en cadena y "de a cuántos" en
     * osce. Bases creadas antes: se agregan las columnas y se rehace
     * osce_participante (user_id dejaba de poder ser NULL).
     */
    private static function migrarTarjetas(PDO $pdo): void
    {
        $cols = array_column($pdo->query('PRAGMA table_info(osce)')->fetchAll(), 'name');
        if (!in_array('rotacion', $cols, true)) {
            $pdo->exec("ALTER TABLE osce ADD COLUMN rotacion TEXT NOT NULL DEFAULT 'vueltas'");
        }
        if (!in_array('por_turno', $cols, true)) {
            $pdo->exec('ALTER TABLE osce ADD COLUMN por_turno INTEGER NOT NULL DEFAULT 2');
        }
        $info = $pdo->query('PRAGMA table_info(osce_participante)')->fetchAll();
        if (in_array('numero', array_column($info, 'name'), true)) {
            return;
        }
        $pdo->exec('PRAGMA foreign_keys = OFF');
        $pdo->beginTransaction();
        $pdo->exec(
            "CREATE TABLE osce_participante_n (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                osce_id INTEGER NOT NULL REFERENCES osce(id) ON DELETE CASCADE,
                user_id INTEGER REFERENCES users(id),
                numero INTEGER NOT NULL DEFAULT 0,
                codigo TEXT NOT NULL,
                token TEXT NOT NULL UNIQUE,
                vuelta INTEGER NOT NULL DEFAULT 0,
                circuito INTEGER NOT NULL DEFAULT 0,
                puesto INTEGER NOT NULL DEFAULT 0,
                variante TEXT NOT NULL DEFAULT '{}',
                UNIQUE (osce_id, user_id),
                UNIQUE (osce_id, codigo)
            )"
        );
        $pdo->exec('INSERT INTO osce_participante_n (id, osce_id, user_id, numero, codigo, token, vuelta, circuito, puesto, variante)
                    SELECT id, osce_id, user_id, 0, codigo, token, vuelta, circuito, puesto, variante FROM osce_participante');
        $pdo->exec('DROP TABLE osce_participante');
        $pdo->exec('ALTER TABLE osce_participante_n RENAME TO osce_participante');
        // Número de entrada para lo que ya había: en el orden de su vuelta y puesto.
        $filas = $pdo->query('SELECT id, osce_id FROM osce_participante ORDER BY osce_id, vuelta, circuito, puesto, id')->fetchAll();
        $upd = $pdo->prepare('UPDATE osce_participante SET numero = ? WHERE id = ?');
        $n = [];
        foreach ($filas as $f) {
            $n[$f['osce_id']] = ($n[$f['osce_id']] ?? 0) + 1;
            $upd->execute([$n[$f['osce_id']], $f['id']]);
        }
        $pdo->commit();
        $pdo->exec('PRAGMA foreign_keys = ON');
    }

    // -- Cálculos puros (sin base) ---------------------------------------

    /** Código legible tipo K7F-3QM. */
    public static function nuevoCodigo(): string
    {
        $a = self::ALFABETO;
        $c = '';
        for ($i = 0; $i < 6; $i++) {
            $c .= $a[random_int(0, strlen($a) - 1)];
        }
        return substr($c, 0, 3) . '-' . substr($c, 3);
    }

    /** Normaliza lo que el alumno escribe: mayúsculas, sin espacios, con guion. */
    public static function normalizarCodigo(string $raw): string
    {
        $c = strtoupper(preg_replace('/[^0-9A-Za-z]/', '', $raw) ?? '');
        return strlen($c) === 6 ? substr($c, 0, 3) . '-' . substr($c, 3) : $c;
    }

    /**
     * Vuelta, circuito y puesto inicial de cada alumno, en el orden dado.
     * Las vueltas quedan parejas (la diferencia entre ellas es a lo más 1).
     *
     * @return array<int, array{vuelta:int, circuito:int, puesto:int}>
     */
    public static function planVueltas(int $alumnos, int $estaciones, int $circuitos): array
    {
        if ($alumnos <= 0 || $estaciones <= 0) {
            return [];
        }
        $circuitos = max(1, $circuitos);
        $cupo = $estaciones * $circuitos;
        $vueltas = (int) ceil($alumnos / $cupo);
        $base = intdiv($alumnos, $vueltas);
        $extra = $alumnos % $vueltas;
        $plan = [];
        for ($v = 0; $v < $vueltas; $v++) {
            $enVuelta = $base + ($v < $extra ? 1 : 0);
            for ($k = 0; $k < $enVuelta; $k++) {
                $plan[] = [
                    'vuelta' => $v,
                    'circuito' => $k % $circuitos,
                    'puesto' => intdiv($k, $circuitos),
                ];
            }
        }
        return $plan;
    }

    /** Índice de la estación (0..S-1) que le toca a un puesto en el tiempo $slot. */
    public static function estacionEn(int $puesto, int $slot, int $estaciones): int
    {
        return ($puesto + $slot) % max(1, $estaciones);
    }

    /**
     * Segundos desde el inicio hasta que empieza el tiempo $slot de la
     * vuelta $vuelta.
     */
    public static function inicioSlot(array $cfg, int $vuelta, int $slot): int
    {
        $paso = $cfg['duracion_s'] + $cfg['pausa_s'];
        $turnos = $cfg['turnos'] ?? $cfg['estaciones'];
        return $vuelta * ($turnos * $paso + $cfg['pausa_vueltas_s']) + $slot * $paso;
    }

    /** Duración total del OSCE en segundos (sin la pausa tras la última estación). */
    public static function duracionTotal(array $cfg): int
    {
        $turnos = $cfg['turnos'] ?? $cfg['estaciones'];
        if ($cfg['vueltas'] <= 0 || $turnos <= 0) {
            return 0;
        }
        return self::inicioSlot($cfg, $cfg['vueltas'] - 1, $turnos - 1) + $cfg['duracion_s'];
    }

    /**
     * En qué fase está el OSCE a $t segundos del inicio.
     * fase: antes | estacion | cambio | entre_vueltas | terminado.
     * La pausa tras la última estación de una vuelta se suma a la pausa
     * entre vueltas (es un solo descanso).
     *
     * @param array{estaciones:int, vueltas:int, duracion_s:int, pausa_s:int, pausa_vueltas_s:int} $cfg
     * @return array{fase:string, vuelta:int, slot:int, restante_s:int}
     */
    public static function estadoReloj(array $cfg, int $t): array
    {
        // Tiempos por vuelta: en vueltas, uno por estación; en cadena, todos
        // los turnos van en una sola vuelta.
        $S = $cfg['turnos'] ?? $cfg['estaciones'];
        $V = $cfg['vueltas'];
        $dur = $cfg['duracion_s'];
        $paso = $dur + $cfg['pausa_s'];
        if ($S <= 0 || $V <= 0) {
            return ['fase' => 'terminado', 'vuelta' => 0, 'slot' => 0, 'restante_s' => 0];
        }
        if ($t < 0) {
            return ['fase' => 'antes', 'vuelta' => 0, 'slot' => 0, 'restante_s' => -$t];
        }
        $largoVuelta = $S * $paso + $cfg['pausa_vueltas_s'];
        $v = intdiv($t, $largoVuelta);
        if ($v >= $V) {
            return ['fase' => 'terminado', 'vuelta' => $V - 1, 'slot' => $S - 1, 'restante_s' => 0];
        }
        $r = $t - $v * $largoVuelta;
        $j = min(intdiv($r, $paso), $S - 1);
        $rr = $r - $j * $paso;
        if ($rr < $dur) {
            return ['fase' => 'estacion', 'vuelta' => $v, 'slot' => $j, 'restante_s' => $dur - $rr];
        }
        if ($j < $S - 1) {
            return ['fase' => 'cambio', 'vuelta' => $v, 'slot' => $j, 'restante_s' => $paso - $rr];
        }
        if ($v === $V - 1) {
            return ['fase' => 'terminado', 'vuelta' => $v, 'slot' => $j, 'restante_s' => 0];
        }
        return ['fase' => 'entre_vueltas', 'vuelta' => $v, 'slot' => $j, 'restante_s' => $largoVuelta - $r];
    }

    /** Grupo de entrada (0, 1, ...) y carril (puesto dentro del grupo) de una tarjeta en cadena. */
    public static function grupo(int $numero, int $porTurno): int
    {
        return intdiv(max(1, $numero) - 1, max(1, $porTurno));
    }

    public static function carril(int $numero, int $porTurno): int
    {
        return (max(1, $numero) - 1) % max(1, $porTurno);
    }

    /**
     * En cadena, el turno en que el grupo hace de paciente en la limpieza
     * (la primera estación): el turno anterior al suyo; el primer grupo es
     * el paciente del último (por eso los primeros se quedan hasta el
     * final). null si hay un solo grupo.
     */
    public static function turnoPaciente(int $grupo, int $grupos): ?int
    {
        if ($grupos <= 1) {
            return null;
        }
        return $grupo === 0 ? $grupos - 1 : $grupo - 1;
    }

    /** Segundos de reloj corridos (descontando pausas); null si no ha partido. */
    public static function transcurrido(array $osce, int $ahora): ?int
    {
        if ($osce['inicio_epoch'] === null) {
            return null;
        }
        $hasta = $osce['pausado_desde'] !== null ? (int) $osce['pausado_desde'] : $ahora;
        return max(0, $hasta - (int) $osce['inicio_epoch'] - (int) $osce['pausado_acum_s']);
    }

    // -- Base ----------------------------------------------------------

    public static function porCurso(?array $courseIds): array
    {
        self::migrar();
        $sql = 'SELECT o.*, c.name AS curso,
                       (SELECT COUNT(*) FROM osce_estacion e WHERE e.osce_id = o.id) AS n_estaciones,
                       (SELECT COUNT(*) FROM osce_participante p WHERE p.osce_id = o.id) AS n_alumnos
                  FROM osce o JOIN courses c ON c.id = o.course_id';
        $args = [];
        if ($courseIds !== null) {
            if (!$courseIds) {
                return [];
            }
            $sql .= ' WHERE o.course_id IN (' . implode(',', array_fill(0, count($courseIds), '?')) . ')';
            $args = $courseIds;
        }
        $stmt = Db::get()->prepare($sql . ' ORDER BY o.inicio_programado DESC, o.id DESC');
        $stmt->execute($args);
        return $stmt->fetchAll();
    }

    public static function obtener(int $id): ?array
    {
        self::migrar();
        $stmt = Db::get()->prepare('SELECT o.*, c.name AS curso FROM osce o JOIN courses c ON c.id = o.course_id WHERE o.id = ?');
        $stmt->execute([$id]);
        $row = $stmt->fetch();
        $stmt->closeCursor();
        return $row ?: null;
    }

    public static function porRelojToken(string $token): ?array
    {
        self::migrar();
        $stmt = Db::get()->prepare('SELECT o.*, c.name AS curso FROM osce o JOIN courses c ON c.id = o.course_id WHERE o.reloj_token = ?');
        $stmt->execute([$token]);
        $row = $stmt->fetch();
        $stmt->closeCursor();
        return $row ?: null;
    }

    /** Valida y normaliza los datos del formulario de configuración. */
    public static function limpiarConfig(array $in): array
    {
        $nombre = trim((string) ($in['nombre'] ?? ''));
        if ($nombre === '') {
            throw new InvalidArgumentException('Falta el nombre del OSCE.');
        }
        $inicio = trim((string) ($in['inicio_programado'] ?? ''));
        $inicio = str_replace('T', ' ', $inicio);
        if ($inicio !== '' && !preg_match('/^\d{4}-\d{2}-\d{2} \d{2}:\d{2}$/', $inicio)) {
            throw new InvalidArgumentException('Fecha y hora de inicio no válidas.');
        }
        $min = static function ($v, float $lo, float $hi, string $que): int {
            $x = (float) str_replace(',', '.', (string) $v);
            if ($x < $lo || $x > $hi) {
                throw new InvalidArgumentException("{$que}: entre {$lo} y {$hi} minutos.");
            }
            return (int) round($x * 60);
        };
        $exigencia = (int) ($in['exigencia'] ?? 60);
        if ($exigencia < 30 || $exigencia > 90) {
            throw new InvalidArgumentException('Exigencia: entre 30 y 90 %.');
        }
        $nota = (float) str_replace(',', '.', (string) ($in['nota_aprobacion'] ?? '4.0'));
        if ($nota < 1.0 || $nota > 7.0) {
            throw new InvalidArgumentException('Nota de aprobación: entre 1,0 y 7,0.');
        }
        $circuitos = (int) ($in['circuitos'] ?? 1);
        if ($circuitos < 1 || $circuitos > 6) {
            throw new InvalidArgumentException('Circuitos: entre 1 y 6.');
        }
        $rotacion = (string) ($in['rotacion'] ?? 'cadena');
        if (!in_array($rotacion, ['cadena', 'vueltas'], true)) {
            throw new InvalidArgumentException('Rotación no válida.');
        }
        $porTurno = (int) ($in['por_turno'] ?? 2);
        if ($porTurno < 1 || $porTurno > 8) {
            throw new InvalidArgumentException('Alumnos por estación: entre 1 y 8.');
        }
        return [
            'nombre' => mb_substr($nombre, 0, 120),
            'inicio_programado' => $inicio,
            'duracion_s' => $min($in['duracion_min'] ?? 8, 1, 60, 'Duración de la estación'),
            'pausa_s' => $min($in['pausa_min'] ?? 2, 0, 30, 'Pausa entre estaciones'),
            'pausa_vueltas_s' => $min($in['pausa_vueltas_min'] ?? 10, 0, 120, 'Pausa entre vueltas'),
            'circuitos' => $circuitos,
            'exigencia' => $exigencia,
            'nota_aprobacion' => round($nota, 1),
            'rotacion' => $rotacion,
            'por_turno' => $porTurno,
        ];
    }

    public static function crear(int $courseId, array $cfg, ?int $userId, bool $estacionesBase): int
    {
        self::migrar();
        $pdo = Db::get();
        return (int) Db::reintentar(static function () use ($pdo, $courseId, $cfg, $userId, $estacionesBase) {
            $pdo->beginTransaction();
            $pdo->prepare(
                'INSERT INTO osce (course_id, nombre, inicio_programado, duracion_s, pausa_s, pausa_vueltas_s,
                                   circuitos, exigencia, nota_aprobacion, rotacion, por_turno, reloj_token, created_by)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            )->execute([
                $courseId, $cfg['nombre'], $cfg['inicio_programado'], $cfg['duracion_s'], $cfg['pausa_s'],
                $cfg['pausa_vueltas_s'], $cfg['circuitos'], $cfg['exigencia'], $cfg['nota_aprobacion'],
                $cfg['rotacion'], $cfg['por_turno'], bin2hex(random_bytes(12)), $userId,
            ]);
            $id = (int) $pdo->lastInsertId();
            if ($estacionesBase) {
                $ins = $pdo->prepare('INSERT INTO osce_estacion (osce_id, orden, tipo, titulo, examen) VALUES (?, ?, ?, ?, ?)');
                foreach (self::ESTACIONES_BASE as $i => [$tipo, $titulo, $examen]) {
                    $ins->execute([$id, $i + 1, $tipo, $titulo, $examen]);
                }
            }
            $pdo->commit();
            return $id;
        });
    }

    public static function actualizarConfig(int $id, array $cfg): void
    {
        self::exigirBorrador($id);
        Db::reintentar(static function () use ($id, $cfg): void {
            Db::get()->prepare(
                'UPDATE osce SET nombre = ?, inicio_programado = ?, duracion_s = ?, pausa_s = ?, pausa_vueltas_s = ?,
                                 circuitos = ?, exigencia = ?, nota_aprobacion = ?, rotacion = ?, por_turno = ? WHERE id = ?'
            )->execute([
                $cfg['nombre'], $cfg['inicio_programado'], $cfg['duracion_s'], $cfg['pausa_s'], $cfg['pausa_vueltas_s'],
                $cfg['circuitos'], $cfg['exigencia'], $cfg['nota_aprobacion'], $cfg['rotacion'], $cfg['por_turno'], $id,
            ]);
        });
        self::reasignar($id);
    }

    public static function eliminar(int $id): void
    {
        self::exigirBorrador($id);
        Db::reintentar(static function () use ($id): void {
            Db::get()->prepare('DELETE FROM osce WHERE id = ?')->execute([$id]);
        });
    }

    /** La estructura (estaciones, alumnos, tiempos) solo cambia antes de partir. */
    private static function exigirBorrador(int $id): void
    {
        $o = self::obtener($id);
        if ($o === null) {
            throw new InvalidArgumentException('OSCE no encontrado.');
        }
        if ($o['estado'] !== 'borrador' || $o['inicio_epoch'] !== null) {
            throw new InvalidArgumentException('El OSCE ya partió: la estructura no se puede cambiar.');
        }
    }

    // -- Estaciones ----------------------------------------------------

    public static function estaciones(int $osceId): array
    {
        self::migrar();
        $stmt = Db::get()->prepare('SELECT * FROM osce_estacion WHERE osce_id = ? ORDER BY orden, id');
        $stmt->execute([$osceId]);
        return $stmt->fetchAll();
    }

    public static function estacion(int $estacionId): ?array
    {
        self::migrar();
        $stmt = Db::get()->prepare('SELECT * FROM osce_estacion WHERE id = ?');
        $stmt->execute([$estacionId]);
        $row = $stmt->fetch();
        $stmt->closeCursor();
        return $row ?: null;
    }

    private static function limpiarEstacion(array $in): array
    {
        $tipo = (string) ($in['tipo'] ?? '');
        if (!isset(self::TIPOS[$tipo])) {
            throw new InvalidArgumentException('Tipo de estación no válido.');
        }
        $examen = (string) ($in['examen'] ?? 'general');
        if (!isset(self::EXAMENES[$examen])) {
            throw new InvalidArgumentException('Examen no válido.');
        }
        $titulo = trim((string) ($in['titulo'] ?? ''));
        if ($titulo === '') {
            $titulo = self::TIPOS[$tipo];
        }
        $peso = (float) str_replace(',', '.', (string) ($in['peso'] ?? '1'));
        if ($peso <= 0 || $peso > 100) {
            throw new InvalidArgumentException('Peso de la estación: mayor que 0 y hasta 100.');
        }
        return ['tipo' => $tipo, 'examen' => $examen, 'titulo' => mb_substr($titulo, 0, 120), 'peso' => $peso];
    }

    public static function agregarEstacion(int $osceId, array $in): void
    {
        self::exigirBorrador($osceId);
        $e = self::limpiarEstacion($in);
        Db::reintentar(static function () use ($osceId, $e): void {
            $pdo = Db::get();
            $stmt = $pdo->prepare('SELECT COALESCE(MAX(orden), 0) + 1 FROM osce_estacion WHERE osce_id = ?');
            $stmt->execute([$osceId]);
            $orden = (int) $stmt->fetchColumn();
            $stmt->closeCursor();
            $pdo->prepare('INSERT INTO osce_estacion (osce_id, orden, tipo, titulo, examen, peso) VALUES (?, ?, ?, ?, ?, ?)')
                ->execute([$osceId, $orden, $e['tipo'], $e['titulo'], $e['examen'], $e['peso']]);
        });
        self::reasignar($osceId);
    }

    public static function editarEstacion(int $osceId, int $estacionId, array $in): void
    {
        self::exigirBorrador($osceId);
        $e = self::limpiarEstacion($in);
        Db::reintentar(static function () use ($osceId, $estacionId, $e): void {
            Db::get()->prepare('UPDATE osce_estacion SET tipo = ?, titulo = ?, examen = ?, peso = ? WHERE id = ? AND osce_id = ?')
                ->execute([$e['tipo'], $e['titulo'], $e['examen'], $e['peso'], $estacionId, $osceId]);
        });
    }

    public static function quitarEstacion(int $osceId, int $estacionId): void
    {
        self::exigirBorrador($osceId);
        Db::reintentar(static function () use ($osceId, $estacionId): void {
            Db::get()->prepare('DELETE FROM osce_estacion WHERE id = ? AND osce_id = ?')->execute([$estacionId, $osceId]);
        });
        self::renumerar($osceId);
        self::reasignar($osceId);
    }

    /** Sube (-1) o baja (+1) una estación en el circuito. */
    public static function moverEstacion(int $osceId, int $estacionId, int $dir): void
    {
        self::exigirBorrador($osceId);
        $ids = array_map('intval', array_column(self::estaciones($osceId), 'id'));
        $i = array_search($estacionId, $ids, true);
        $j = $i === false ? false : $i + ($dir < 0 ? -1 : 1);
        if ($i === false || $j < 0 || $j >= count($ids)) {
            return;
        }
        [$ids[$i], $ids[$j]] = [$ids[$j], $ids[$i]];
        self::renumerar($osceId, $ids);
    }

    private static function renumerar(int $osceId, ?array $ids = null): void
    {
        $ids = $ids ?? array_map('intval', array_column(self::estaciones($osceId), 'id'));
        Db::reintentar(static function () use ($osceId, $ids): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $upd = $pdo->prepare('UPDATE osce_estacion SET orden = ? WHERE id = ? AND osce_id = ?');
            foreach ($ids as $k => $id) {
                $upd->execute([$k + 1, $id, $osceId]);
            }
            $pdo->commit();
        });
    }

    // -- Participantes -------------------------------------------------

    public static function participantes(int $osceId): array
    {
        self::migrar();
        $stmt = Db::get()->prepare(
            'SELECT p.*, u.display_name, u.username FROM osce_participante p
               LEFT JOIN users u ON u.id = p.user_id
              WHERE p.osce_id = ? ORDER BY p.numero, p.id'
        );
        $stmt->execute([$osceId]);
        return $stmt->fetchAll();
    }

    public static function participantePorToken(string $token): ?array
    {
        self::migrar();
        if (!preg_match('/^[0-9a-f]{24}$/', $token)) {
            return null;
        }
        $stmt = Db::get()->prepare(
            'SELECT p.*, u.display_name FROM osce_participante p LEFT JOIN users u ON u.id = p.user_id WHERE p.token = ?'
        );
        $stmt->execute([$token]);
        $row = $stmt->fetch();
        $stmt->closeCursor();
        return $row ?: null;
    }

    /**
     * Tarjeta por lo que el alumno escribe en una estación: su NÚMERO (lo
     * que se usa el día del OSCE: es más rápido) o su código.
     */
    public static function participantePorCodigo(int $osceId, string $codigo): ?array
    {
        self::migrar();
        $raw = trim($codigo);
        $porNumero = ctype_digit($raw);
        $stmt = Db::get()->prepare(
            'SELECT p.*, u.display_name FROM osce_participante p LEFT JOIN users u ON u.id = p.user_id
              WHERE p.osce_id = ? AND ' . ($porNumero ? 'p.numero = ?' : 'p.codigo = ?')
        );
        $stmt->execute([$osceId, $porNumero ? (int) $raw : self::normalizarCodigo($raw)]);
        $row = $stmt->fetch();
        $stmt->closeCursor();
        return $row ?: null;
    }

    /** Alumnos del curso que cuentan para el OSCE (sin el alumno demo). */
    public static function alumnosDelCurso(int $courseId): array
    {
        return array_values(array_filter(Courses::students($courseId), static fn ($u) => !(int) $u['is_demo']));
    }

    /**
     * Deja tantas tarjetas como alumnos tiene el curso (sin el demo),
     * numeradas 1..N. Las tarjetas nacen SIN DUEÑO: el número se sortea en
     * papel el día del OSCE y cada alumno amarra la suya escaneando el QR
     * (reclamarTarjeta) o el docente la asigna en el panel. Si sobran, se
     * quitan las de número más alto que no tienen dueño.
     *
     * @return array{agregados:int, quitados:int}
     */
    public static function sincronizarAlumnos(int $osceId): array
    {
        self::exigirBorrador($osceId);
        $o = self::obtener($osceId);
        $n = count(self::alumnosDelCurso((int) $o['course_id']));
        $actuales = self::participantes($osceId);
        $agregados = 0;
        $quitados = 0;
        Db::reintentar(static function () use ($osceId, $n, $actuales, &$agregados, &$quitados): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $usados = array_flip(array_column($actuales, 'codigo'));
            $numeros = array_map('intval', array_column($actuales, 'numero'));
            $ins = $pdo->prepare('INSERT INTO osce_participante (osce_id, user_id, numero, codigo, token) VALUES (?, NULL, ?, ?, ?)');
            for ($num = 1; $num <= $n; $num++) {
                if (in_array($num, $numeros, true)) {
                    continue;
                }
                do {
                    $codigo = self::nuevoCodigo();
                } while (isset($usados[$codigo]));
                $usados[$codigo] = true;
                $ins->execute([$osceId, $num, $codigo, bin2hex(random_bytes(12))]);
                $agregados++;
            }
            $del = $pdo->prepare('DELETE FROM osce_participante WHERE id = ? AND user_id IS NULL');
            foreach ($actuales as $p) {
                if ((int) $p['numero'] > $n && $p['user_id'] === null) {
                    $del->execute([(int) $p['id']]);
                    $quitados++;
                }
            }
            $pdo->commit();
        });
        self::reasignar($osceId);
        return ['agregados' => $agregados, 'quitados' => $quitados];
    }

    /**
     * El alumno amarra la tarjeta que sacó (escaneando su QR): solo si la
     * tarjeta no tiene dueño y él no tiene otra en este OSCE.
     */
    public static function reclamarTarjeta(array $p, int $userId): void
    {
        $o = self::obtener((int) $p['osce_id']);
        if ($p['user_id'] !== null) {
            throw new InvalidArgumentException('Esta tarjeta ya tiene dueño. Si es un error, avisa al docente.');
        }
        if (!in_array($userId, array_map(static fn ($u) => (int) $u['id'], self::alumnosDelCurso((int) $o['course_id'])), true)) {
            throw new InvalidArgumentException('Ese alumno no es del curso.');
        }
        self::asignarTarjeta((int) $p['osce_id'], (int) $p['id'], $userId);
    }

    /** El docente asigna (o suelta, con null) la tarjeta de un alumno. */
    public static function asignarTarjeta(int $osceId, int $participanteId, ?int $userId): void
    {
        Db::reintentar(static function () use ($osceId, $participanteId, $userId): void {
            $pdo = Db::get();
            if ($userId !== null) {
                $stmt = $pdo->prepare('SELECT numero FROM osce_participante WHERE osce_id = ? AND user_id = ? AND id <> ?');
                $stmt->execute([$osceId, $userId, $participanteId]);
                $otra = $stmt->fetchColumn();
                $stmt->closeCursor();
                if ($otra !== false) {
                    throw new InvalidArgumentException("Ese alumno ya tiene la tarjeta N.º {$otra}.");
                }
            }
            $pdo->prepare('UPDATE osce_participante SET user_id = ? WHERE id = ? AND osce_id = ?')
                ->execute([$userId, $participanteId, $osceId]);
        });
    }

    /**
     * Reparte vueltas, circuitos y puestos (rotación en vueltas) según el
     * número de cada tarjeta. En cadena no hace falta: el número ya dice el
     * grupo y el carril (grupo(), carril()).
     */
    public static function reasignar(int $osceId): void
    {
        $o = self::obtener($osceId);
        $S = count(self::estaciones($osceId));
        $parts = self::participantes($osceId);
        $plan = self::planVueltas(count($parts), $S, (int) $o['circuitos']);
        Db::reintentar(static function () use ($parts, $plan): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $upd = $pdo->prepare('UPDATE osce_participante SET vuelta = ?, circuito = ?, puesto = ? WHERE id = ?');
            foreach ($parts as $k => $p) {
                $a = $plan[$k] ?? ['vuelta' => 0, 'circuito' => 0, 'puesto' => 0];
                $upd->execute([$a['vuelta'], $a['circuito'], $a['puesto'], (int) $p['id']]);
            }
            $pdo->commit();
        });
    }

    public static function quitarParticipante(int $osceId, int $participanteId): void
    {
        self::exigirBorrador($osceId);
        Db::reintentar(static function () use ($osceId, $participanteId): void {
            Db::get()->prepare('DELETE FROM osce_participante WHERE id = ? AND osce_id = ?')->execute([$participanteId, $osceId]);
        });
        self::reasignar($osceId);
    }

    // -- Reloj ---------------------------------------------------------

    /**
     * Configuración que necesita estadoReloj(), con las vueltas o turnos ya
     * calculados. En cadena: grupos de "por_turno" alumnos que entran uno
     * por turno y recorren las estaciones en orden; los turnos son
     * grupos + estaciones − 1, en una sola vuelta.
     */
    public static function cfgReloj(array $o, int $estaciones, int $alumnos): array
    {
        $cfg = [
            'modo' => ($o['rotacion'] ?? 'vueltas') === 'cadena' ? 'cadena' : 'vueltas',
            'estaciones' => $estaciones,
            'duracion_s' => (int) $o['duracion_s'],
            'pausa_s' => (int) $o['pausa_s'],
            'pausa_vueltas_s' => (int) $o['pausa_vueltas_s'],
            'por_turno' => max(1, (int) ($o['por_turno'] ?? 1)),
        ];
        if ($cfg['modo'] === 'cadena') {
            $grupos = $alumnos > 0 ? (int) ceil($alumnos / $cfg['por_turno']) : 0;
            $cfg['grupos'] = $grupos;
            $cfg['turnos'] = $grupos > 0 && $estaciones > 0 ? $grupos + $estaciones - 1 : 0;
            $cfg['vueltas'] = $cfg['turnos'] > 0 ? 1 : 0;
            $cfg['pausa_vueltas_s'] = 0;
            return $cfg;
        }
        $cupo = max(1, $estaciones * max(1, (int) $o['circuitos']));
        $cfg['vueltas'] = $alumnos > 0 && $estaciones > 0 ? (int) ceil($alumnos / $cupo) : 0;
        $cfg['turnos'] = $estaciones;
        return $cfg;
    }

    public static function iniciar(int $id): void
    {
        $o = self::obtener($id);
        if ($o === null || $o['estado'] !== 'borrador') {
            throw new InvalidArgumentException('Solo se inicia un OSCE en borrador.');
        }
        if (count(self::estaciones($id)) === 0 || count(self::participantes($id)) === 0) {
            throw new InvalidArgumentException('Faltan estaciones o alumnos para iniciar.');
        }
        Db::reintentar(static function () use ($id): void {
            Db::get()->prepare("UPDATE osce SET estado = 'en_curso', inicio_epoch = ?, pausado_desde = NULL, pausado_acum_s = 0 WHERE id = ?")
                ->execute([time(), $id]);
        });
    }

    public static function pausar(int $id): void
    {
        Db::reintentar(static function () use ($id): void {
            Db::get()->prepare("UPDATE osce SET pausado_desde = ? WHERE id = ? AND estado = 'en_curso' AND pausado_desde IS NULL")
                ->execute([time(), $id]);
        });
    }

    public static function reanudar(int $id): void
    {
        Db::reintentar(static function () use ($id): void {
            Db::get()->prepare(
                "UPDATE osce SET pausado_acum_s = pausado_acum_s + (? - pausado_desde), pausado_desde = NULL
                  WHERE id = ? AND estado = 'en_curso' AND pausado_desde IS NOT NULL"
            )->execute([time(), $id]);
        });
    }

    /** Corre el reloj $seg segundos (positivo adelanta, negativo atrasa). */
    public static function ajustar(int $id, int $seg): void
    {
        Db::reintentar(static function () use ($id, $seg): void {
            Db::get()->prepare("UPDATE osce SET inicio_epoch = inicio_epoch - ? WHERE id = ? AND estado = 'en_curso'")
                ->execute([$seg, $id]);
        });
    }

    public static function cerrar(int $id): void
    {
        Db::reintentar(static function () use ($id): void {
            Db::get()->prepare(
                "UPDATE osce SET estado = 'cerrado',
                        pausado_acum_s = pausado_acum_s + CASE WHEN pausado_desde IS NULL THEN 0 ELSE ? - pausado_desde END,
                        pausado_desde = NULL
                  WHERE id = ? AND estado = 'en_curso'"
            )->execute([time(), $id]);
        });
    }

    /** Los alumnos ven su resultado (y pueden hacer réplica) desde el QR. */
    public static function publicar(int $id, bool $publicar): void
    {
        Db::reintentar(static function () use ($id, $publicar): void {
            if ($publicar) {
                Db::get()->prepare("UPDATE osce SET estado = 'publicado', publicado_at = CURRENT_TIMESTAMP WHERE id = ? AND estado = 'cerrado'")
                    ->execute([$id]);
            } else {
                Db::get()->prepare("UPDATE osce SET estado = 'cerrado' WHERE id = ? AND estado = 'publicado'")->execute([$id]);
            }
        });
    }

    /**
     * Cuándo le toca a un alumno una estación: segundos desde el inicio del
     * reloj en que empieza y termina su tiempo ahí.
     *
     * @return array{slot:int, inicio_s:int, fin_s:int}
     */
    public static function ventana(array $cfg, array $p, int $indiceEstacion): array
    {
        if (($cfg['modo'] ?? 'vueltas') === 'cadena') {
            $slot = self::grupo((int) $p['numero'], (int) $cfg['por_turno']) + $indiceEstacion;
            $inicio = self::inicioSlot($cfg, 0, $slot);
            return ['slot' => $slot, 'inicio_s' => $inicio, 'fin_s' => $inicio + $cfg['duracion_s']];
        }
        $S = max(1, $cfg['estaciones']);
        $slot = (($indiceEstacion - (int) $p['puesto']) % $S + $S) % $S;
        $inicio = self::inicioSlot($cfg, (int) $p['vuelta'], $slot);
        return ['slot' => $slot, 'inicio_s' => $inicio, 'fin_s' => $inicio + $cfg['duracion_s']];
    }

    /**
     * ¿Puede el alumno trabajar ahora en esa estación? Desde la pausa que la
     * antecede (llega y escribe su código durante el cambio) hasta el fin de
     * su tiempo más una gracia para que la tablet alcance a entregar sola.
     */
    public static function enVentana(array $cfg, array $p, int $indiceEstacion, int $t): bool
    {
        $v = self::ventana($cfg, $p, $indiceEstacion);
        $gracia = max(30, $cfg['pausa_s']);
        return $t >= $v['inicio_s'] - max(30, $cfg['pausa_s']) && $t <= $v['fin_s'] + $gracia;
    }

    /**
     * Cierra solo el OSCE cuando terminó el último turno, con margen para que
     * las tablets y los PCs alcancen a entregar solos (lo llaman las
     * pantallas al pedir el reloj). Devuelve el OSCE como quedó.
     */
    public static function cerrarSiTermino(array $o): array
    {
        if ($o['estado'] !== 'en_curso' || $o['pausado_desde'] !== null) {
            return $o;
        }
        $S = count(self::estaciones((int) $o['id']));
        $stmt = Db::get()->prepare('SELECT COUNT(*) FROM osce_participante WHERE osce_id = ?');
        $stmt->execute([(int) $o['id']]);
        $cfg = self::cfgReloj($o, $S, (int) $stmt->fetchColumn());
        $stmt->closeCursor();
        $t = self::transcurrido($o, time());
        $margen = max(60, $cfg['pausa_s']) + 60;
        if ($t === null || $t < self::duracionTotal($cfg) + $margen) {
            return $o;
        }
        self::cerrar((int) $o['id']);
        return self::obtener((int) $o['id']) ?? $o;
    }

    /**
     * El alumno entró a una estación (tablet o PC): queda la entrega abierta,
     * para que el panel de control vea quién está y quién falta.
     */
    public static function marcarEntrada(int $participanteId, int $estacionId): void
    {
        Db::reintentar(static function () use ($participanteId, $estacionId): void {
            Db::get()->prepare(
                'INSERT INTO osce_entrega (participante_id, estacion_id) VALUES (?, ?)
                 ON CONFLICT (participante_id, estacion_id) DO NOTHING'
            )->execute([$participanteId, $estacionId]);
        });
    }

    /** Estado de cada entrega del OSCE: estacion_id => numero => en_curso|enviada. */
    public static function estadosEntregas(int $osceId): array
    {
        $stmt = Db::get()->prepare(
            'SELECT e.estacion_id, p.numero, e.estado FROM osce_entrega e
               JOIN osce_participante p ON p.id = e.participante_id WHERE p.osce_id = ?'
        );
        $stmt->execute([$osceId]);
        $out = [];
        foreach ($stmt->fetchAll() as $r) {
            $out[(int) $r['estacion_id']][(int) $r['numero']] = $r['estado'];
        }
        return $out;
    }

    /** Vuelve a borrador un OSCE que se inició por error (sin entregas). */
    public static function volverABorrador(int $id): void
    {
        $stmt = Db::get()->prepare(
            'SELECT COUNT(*) FROM osce_entrega en JOIN osce_participante p ON p.id = en.participante_id WHERE p.osce_id = ?'
        );
        $stmt->execute([$id]);
        $n = (int) $stmt->fetchColumn();
        $stmt->closeCursor();
        if ($n > 0) {
            throw new InvalidArgumentException('Ya hay entregas: no se puede volver a borrador.');
        }
        Db::reintentar(static function () use ($id): void {
            Db::get()->prepare(
                "UPDATE osce SET estado = 'borrador', inicio_epoch = NULL, pausado_desde = NULL, pausado_acum_s = 0 WHERE id = ?"
            )->execute([$id]);
        });
    }

    /**
     * Lo que necesita cualquier pantalla del reloj: configuración, fase
     * actual y el nombre de cada estación. $participante agrega su recorrido.
     */
    public static function estadoPublico(array $o, ?array $participante = null): array
    {
        $o = self::cerrarSiTermino($o);
        $estaciones = self::estaciones((int) $o['id']);
        $S = count($estaciones);
        $stmt = Db::get()->prepare('SELECT COUNT(*) FROM osce_participante WHERE osce_id = ?');
        $stmt->execute([(int) $o['id']]);
        $n = (int) $stmt->fetchColumn();
        $stmt->closeCursor();
        $cfg = self::cfgReloj($o, $S, $n);
        $ahora = time();
        $t = self::transcurrido($o, $ahora);
        $out = [
            'nombre' => $o['nombre'],
            'estado' => $o['estado'],
            'inicio_programado' => $o['inicio_programado'],
            'servidor_epoch' => $ahora,
            // Hora real de partida corrida por las pausas: con el OSCE
            // cerrado, las horas del recorrido salen de acá y no de "ahora".
            'inicio_real' => $o['inicio_epoch'] === null ? null : (int) $o['inicio_epoch'] + (int) $o['pausado_acum_s'],
            'transcurrido_s' => $t,
            'pausado' => $o['pausado_desde'] !== null,
            'cfg' => $cfg,
            'circuitos' => (int) $o['circuitos'],
            'total_s' => self::duracionTotal($cfg),
            'reloj' => $t === null ? null : self::estadoReloj($cfg, $t),
            'estaciones' => array_map(static fn ($e) => ['id' => (int) $e['id'], 'titulo' => $e['titulo'], 'tipo' => $e['tipo']], $estaciones),
        ];
        if ($participante !== null) {
            $out['participante'] = [
                'codigo' => $participante['codigo'],
                'numero' => (int) $participante['numero'],
                'vuelta' => (int) $participante['vuelta'],
                'circuito' => (int) $participante['circuito'],
                'puesto' => (int) $participante['puesto'],
                'grupo' => self::grupo((int) $participante['numero'], $cfg['por_turno']),
                'carril' => self::carril((int) $participante['numero'], $cfg['por_turno']),
            ];
        }
        return $out;
    }

    /**
     * Recorrido de un alumno, en orden de tiempo: cada estación con el
     * segundo en que empieza (desde el inicio del reloj) y la entrega si ya
     * la hay. En cadena va además su turno de PACIENTE en la limpieza (la
     * primera estación), con el número de quien lo limpia.
     */
    public static function recorrido(array $o, array $p): array
    {
        $estaciones = self::estaciones((int) $o['id']);
        $S = count($estaciones);
        $stmt = Db::get()->prepare('SELECT COUNT(*) FROM osce_participante WHERE osce_id = ?');
        $stmt->execute([(int) $o['id']]);
        $n = (int) $stmt->fetchColumn();
        $stmt->closeCursor();
        $cfg = self::cfgReloj($o, $S, $n);
        $stmt = Db::get()->prepare('SELECT * FROM osce_entrega WHERE participante_id = ?');
        $stmt->execute([(int) $p['id']]);
        $entregas = [];
        foreach ($stmt->fetchAll() as $en) {
            $entregas[(int) $en['estacion_id']] = $en;
        }
        $filas = [];
        foreach ($estaciones as $i => $e) {
            $v = self::ventana($cfg, $p, $i);
            $filas[] = ['slot' => $v['slot'], 'estacion' => $e, 'inicio_s' => $v['inicio_s'],
                        'entrega' => $entregas[(int) $e['id']] ?? null, 'paciente' => null];
        }
        if ($cfg['modo'] === 'cadena' && $S > 0) {
            $k = $cfg['por_turno'];
            $tp = self::turnoPaciente(self::grupo((int) $p['numero'], $k), $cfg['grupos']);
            $quien = $tp === null ? null : $tp * $k + self::carril((int) $p['numero'], $k) + 1;
            if ($tp !== null && $quien <= $n) {
                $filas[] = ['slot' => $tp, 'estacion' => $estaciones[0], 'inicio_s' => self::inicioSlot($cfg, 0, $tp),
                            'entrega' => null, 'paciente' => $quien];
            }
        }
        usort($filas, static fn ($a, $b) => $a['inicio_s'] <=> $b['inicio_s']);
        return $filas;
    }

    /** Nota chilena por puntaje con exigencia (escala 1,0–7,0). */
    public static function nota(float $puntaje, float $max, int $exigencia, float $notaAprob): float
    {
        if ($max <= 0) {
            return 1.0;
        }
        $corte = $max * $exigencia / 100;
        if ($puntaje < $corte) {
            $n = 1.0 + ($notaAprob - 1.0) * $puntaje / $corte;
        } else {
            $n = $max > $corte ? $notaAprob + (7.0 - $notaAprob) * ($puntaje - $corte) / ($max - $corte) : 7.0;
        }
        return round(max(1.0, min(7.0, $n)), 1);
    }
}
