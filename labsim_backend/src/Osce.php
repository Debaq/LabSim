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
                user_id INTEGER NOT NULL REFERENCES users(id),
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
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_osce_course ON osce(course_id)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_osce_estacion ON osce_estacion(osce_id, orden)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_osce_item ON osce_item(estacion_id, orden)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_osce_pregunta ON osce_pregunta(estacion_id, orden)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_osce_entrega ON osce_entrega(estacion_id)');
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_osce_resultado ON osce_resultado(entrega_id)');
        $hecho = true;
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
        return $vuelta * ($cfg['estaciones'] * $paso + $cfg['pausa_vueltas_s']) + $slot * $paso;
    }

    /** Duración total del OSCE en segundos (sin la pausa tras la última estación). */
    public static function duracionTotal(array $cfg): int
    {
        if ($cfg['vueltas'] <= 0 || $cfg['estaciones'] <= 0) {
            return 0;
        }
        return self::inicioSlot($cfg, $cfg['vueltas'] - 1, $cfg['estaciones'] - 1) + $cfg['duracion_s'];
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
        $S = $cfg['estaciones'];
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
        return [
            'nombre' => mb_substr($nombre, 0, 120),
            'inicio_programado' => $inicio,
            'duracion_s' => $min($in['duracion_min'] ?? 8, 1, 60, 'Duración de la estación'),
            'pausa_s' => $min($in['pausa_min'] ?? 2, 0, 30, 'Pausa entre estaciones'),
            'pausa_vueltas_s' => $min($in['pausa_vueltas_min'] ?? 10, 0, 120, 'Pausa entre vueltas'),
            'circuitos' => $circuitos,
            'exigencia' => $exigencia,
            'nota_aprobacion' => round($nota, 1),
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
                                   circuitos, exigencia, nota_aprobacion, reloj_token, created_by)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            )->execute([
                $courseId, $cfg['nombre'], $cfg['inicio_programado'], $cfg['duracion_s'], $cfg['pausa_s'],
                $cfg['pausa_vueltas_s'], $cfg['circuitos'], $cfg['exigencia'], $cfg['nota_aprobacion'],
                bin2hex(random_bytes(12)), $userId,
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
                                 circuitos = ?, exigencia = ?, nota_aprobacion = ? WHERE id = ?'
            )->execute([
                $cfg['nombre'], $cfg['inicio_programado'], $cfg['duracion_s'], $cfg['pausa_s'], $cfg['pausa_vueltas_s'],
                $cfg['circuitos'], $cfg['exigencia'], $cfg['nota_aprobacion'], $id,
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
               JOIN users u ON u.id = p.user_id
              WHERE p.osce_id = ? ORDER BY p.vuelta, p.circuito, p.puesto, p.id'
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
            'SELECT p.*, u.display_name FROM osce_participante p JOIN users u ON u.id = p.user_id WHERE p.token = ?'
        );
        $stmt->execute([$token]);
        $row = $stmt->fetch();
        $stmt->closeCursor();
        return $row ?: null;
    }

    public static function participantePorCodigo(int $osceId, string $codigo): ?array
    {
        self::migrar();
        $stmt = Db::get()->prepare(
            'SELECT p.*, u.display_name FROM osce_participante p JOIN users u ON u.id = p.user_id
              WHERE p.osce_id = ? AND p.codigo = ?'
        );
        $stmt->execute([$osceId, self::normalizarCodigo($codigo)]);
        $row = $stmt->fetch();
        $stmt->closeCursor();
        return $row ?: null;
    }

    /**
     * Agrega a los alumnos del curso que falten (sin el alumno demo) con
     * código y token nuevos, y saca a los que ya no están en el curso. Los
     * que siguen conservan su código. Después reparte vueltas y puestos.
     *
     * @return array{agregados:int, quitados:int}
     */
    public static function sincronizarAlumnos(int $osceId): array
    {
        self::exigirBorrador($osceId);
        $o = self::obtener($osceId);
        $curso = array_filter(Courses::students((int) $o['course_id']), static fn ($u) => !(int) $u['is_demo']);
        $enCurso = array_map(static fn ($u) => (int) $u['id'], $curso);
        $actuales = array_map(static fn ($p) => (int) $p['user_id'], self::participantes($osceId));
        $nuevos = array_values(array_diff($enCurso, $actuales));
        $fuera = array_values(array_diff($actuales, $enCurso));

        Db::reintentar(static function () use ($osceId, $nuevos, $fuera): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            if ($fuera) {
                $pdo->prepare(
                    'DELETE FROM osce_participante WHERE osce_id = ? AND user_id IN (' . implode(',', array_fill(0, count($fuera), '?')) . ')'
                )->execute(array_merge([$osceId], $fuera));
            }
            $stmt = $pdo->prepare('SELECT codigo FROM osce_participante WHERE osce_id = ?');
            $stmt->execute([$osceId]);
            $usados = array_flip($stmt->fetchAll(PDO::FETCH_COLUMN));
            $ins = $pdo->prepare('INSERT INTO osce_participante (osce_id, user_id, codigo, token) VALUES (?, ?, ?, ?)');
            foreach ($nuevos as $uid) {
                do {
                    $codigo = self::nuevoCodigo();
                } while (isset($usados[$codigo]));
                $usados[$codigo] = true;
                $ins->execute([$osceId, $uid, $codigo, bin2hex(random_bytes(12))]);
            }
            $pdo->commit();
        });
        self::reasignar($osceId, true);
        return ['agregados' => count($nuevos), 'quitados' => count($fuera)];
    }

    /**
     * Reparte vueltas, circuitos y puestos. Con $sortear, el orden de los
     * alumnos se baraja (quién va en qué vuelta); si no, se mantiene el
     * orden que ya tenían y solo se recalcula (cambió el n° de estaciones o
     * de circuitos).
     */
    public static function reasignar(int $osceId, bool $sortear = false): void
    {
        $o = self::obtener($osceId);
        $S = count(self::estaciones($osceId));
        $parts = self::participantes($osceId);
        if ($sortear) {
            // Fisher-Yates con random_int: shuffle() usa el generador no criptográfico.
            for ($i = count($parts) - 1; $i > 0; $i--) {
                $j = random_int(0, $i);
                [$parts[$i], $parts[$j]] = [$parts[$j], $parts[$i]];
            }
        }
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

    /** Configuración que necesita estadoReloj(), con las vueltas ya calculadas. */
    public static function cfgReloj(array $o, int $estaciones, int $alumnos): array
    {
        $cupo = max(1, $estaciones * max(1, (int) $o['circuitos']));
        return [
            'estaciones' => $estaciones,
            'vueltas' => $alumnos > 0 && $estaciones > 0 ? (int) ceil($alumnos / $cupo) : 0,
            'duracion_s' => (int) $o['duracion_s'],
            'pausa_s' => (int) $o['pausa_s'],
            'pausa_vueltas_s' => (int) $o['pausa_vueltas_s'],
        ];
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
            'transcurrido_s' => $t,
            'pausado' => $o['pausado_desde'] !== null,
            'cfg' => $cfg,
            'circuitos' => (int) $o['circuitos'],
            'total_s' => self::duracionTotal($cfg),
            'reloj' => $t === null ? null : self::estadoReloj($cfg, $t),
            'estaciones' => array_map(static fn ($e) => ['titulo' => $e['titulo'], 'tipo' => $e['tipo']], $estaciones),
        ];
        if ($participante !== null) {
            $out['participante'] = [
                'codigo' => $participante['codigo'],
                'vuelta' => (int) $participante['vuelta'],
                'circuito' => (int) $participante['circuito'],
                'puesto' => (int) $participante['puesto'],
            ];
        }
        return $out;
    }

    /**
     * Recorrido de un alumno: estación por tiempo, con el segundo de inicio
     * de cada una (desde el inicio del reloj) y la entrega si ya la hay.
     */
    public static function recorrido(array $o, array $p): array
    {
        $estaciones = self::estaciones((int) $o['id']);
        $S = count($estaciones);
        $stmt = Db::get()->prepare('SELECT COUNT(*) FROM osce_participante WHERE osce_id = ?');
        $stmt->execute([(int) $o['id']]);
        $cfg = self::cfgReloj($o, $S, (int) $stmt->fetchColumn());
        $stmt->closeCursor();
        $stmt = Db::get()->prepare('SELECT * FROM osce_entrega WHERE participante_id = ?');
        $stmt->execute([(int) $p['id']]);
        $entregas = [];
        foreach ($stmt->fetchAll() as $en) {
            $entregas[(int) $en['estacion_id']] = $en;
        }
        $filas = [];
        for ($slot = 0; $slot < $S; $slot++) {
            $e = $estaciones[self::estacionEn((int) $p['puesto'], $slot, $S)];
            $filas[] = [
                'slot' => $slot,
                'estacion' => $e,
                'inicio_s' => self::inicioSlot($cfg, (int) $p['vuelta'], $slot),
                'entrega' => $entregas[(int) $e['id']] ?? null,
            ];
        }
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
