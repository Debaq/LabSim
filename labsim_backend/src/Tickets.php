<?php

declare(strict_types=1);

require_once __DIR__ . '/Equipos.php';

/**
 * Tickets de problemas enviados desde la app de escritorio (Configuración →
 * Reportar un problema; ver core/soporte.py del cliente). Cada ticket trae
 * lo que el usuario aceptó mandar: qué pasó, el equipo (mismo bloque que el
 * login, ver Equipos), detalles del sistema y el registro de la app.
 *
 * Al usuario no se le contesta: el ticket es materia prima para abrir
 * issues después. Por eso hay estado (abierto/cerrado) y una nota interna,
 * pero ningún aviso de vuelta.
 *
 * El registro se guarda tal como llega (gzip) en data/tickets/, fuera de
 * public/, con nombre derivado del id -- mismo patrón que ReportFile.
 */
final class Tickets
{
    /** Tope del registro comprimido. El cliente manda la cola del archivo. */
    public const MAX_LOG_BYTES = 2 * 1024 * 1024;

    /** Tope de tickets por usuario y hora: un botón apretado en loop no llena el disco. */
    public const MAX_POR_HORA = 5;

    public const ESTADOS = ['abierto', 'cerrado'];

    public static function dir(): string
    {
        $dir = __DIR__ . '/../data/tickets';
        if (!is_dir($dir) && !mkdir($dir, 0775, true) && !is_dir($dir)) {
            throw new RuntimeException("No se pudo crear {$dir} (revisa permisos).");
        }
        return $dir;
    }

    public static function logPath(int $id): string
    {
        if ($id <= 0) {
            throw new InvalidArgumentException('id de ticket inválido.');
        }
        return self::dir() . "/ticket_{$id}.log.gz";
    }

    /**
     * Detalles del sistema que manda la app (versión del SO, arquitectura,
     * Python, Qt, pantalla...). Solo pares texto→texto cortos: es para
     * leerlo, no para procesarlo.
     *
     * @param mixed $raw
     * @return array<string, string>
     */
    public static function normalizarDetalle($raw): array
    {
        if (!is_array($raw)) {
            return [];
        }
        $out = [];
        foreach ($raw as $k => $v) {
            if (count($out) >= 30 || !is_string($k) || !preg_match('/^[a-z0-9_]{1,32}$/', $k)) {
                continue;
            }
            if (is_bool($v)) {
                $v = $v ? 'sí' : 'no';
            }
            if (!is_scalar($v)) {
                continue;
            }
            $out[$k] = self::texto($v, 200);
        }
        return $out;
    }

    /** ¿Es un gzip? (los dos bytes mágicos; lo demás lo valida quien lo abra) */
    public static function esGzip(string $bytes): bool
    {
        return strlen($bytes) >= 2 && substr($bytes, 0, 2) === "\x1f\x8b";
    }

    public static function migrar(): void
    {
        $pdo = Db::get();
        $pdo->exec(
            "CREATE TABLE IF NOT EXISTS app_tickets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                descripcion TEXT NOT NULL DEFAULT '',
                equipo_id TEXT NOT NULL DEFAULT '',
                equipo_nombre TEXT NOT NULL DEFAULT '',
                so TEXT NOT NULL DEFAULT '',
                version TEXT NOT NULL DEFAULT '',
                empaquetada INTEGER NOT NULL DEFAULT 1,
                detalle TEXT NOT NULL DEFAULT '{}',
                log_bytes INTEGER NOT NULL DEFAULT 0,
                estado TEXT NOT NULL DEFAULT 'abierto',
                nota TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )"
        );
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_app_tickets_created ON app_tickets(created_at)');
    }

    public static function excedeLimite(int $userId): bool
    {
        self::migrar();
        $stmt = Db::get()->prepare(
            "SELECT COUNT(*) FROM app_tickets WHERE user_id = ? AND created_at > datetime('now', '-1 hour')"
        );
        $stmt->execute([$userId]);
        return (int) $stmt->fetchColumn() >= self::MAX_POR_HORA;
    }

    /** Reportes de cierre inesperado sin sesión (user_id NULL): por equipo y en total. */
    public const MAX_ANONIMOS_POR_EQUIPO_HORA = 3;
    public const MAX_ANONIMOS_HORA = 60;

    public static function excedeLimiteAnonimo(string $equipoId): bool
    {
        self::migrar();
        $pdo = Db::get();
        $stmt = $pdo->prepare(
            "SELECT COUNT(*) FROM app_tickets WHERE user_id IS NULL AND created_at > datetime('now', '-1 hour')"
        );
        $stmt->execute();
        if ((int) $stmt->fetchColumn() >= self::MAX_ANONIMOS_HORA) {
            return true;
        }
        $stmt = $pdo->prepare(
            "SELECT COUNT(*) FROM app_tickets
             WHERE user_id IS NULL AND equipo_id = ? AND created_at > datetime('now', '-1 hour')"
        );
        $stmt->execute([$equipoId]);
        return (int) $stmt->fetchColumn() >= self::MAX_ANONIMOS_POR_EQUIPO_HORA;
    }

    /**
     * Crea el ticket y guarda el registro. Devuelve el id.
     *
     * @param mixed $equipoRaw
     * @param mixed $detalleRaw
     */
    public static function crear(?int $userId, string $descripcion, $equipoRaw, $detalleRaw, ?string $logGz): int
    {
        self::migrar();
        // El bloque del equipo es el mismo del login; si viene raro igual
        // se guarda el ticket, sin equipo: lo importante es lo que pasó.
        $equipo = Equipos::normalizar($equipoRaw) ?? [
            'id' => '', 'nombre' => '', 'so' => '', 'version' => '', 'empaquetada' => 1,
        ];
        $detalle = self::normalizarDetalle($detalleRaw);
        $pdo = Db::get();
        $pdo->prepare(
            'INSERT INTO app_tickets (user_id, descripcion, equipo_id, equipo_nombre, so, version,
                                      empaquetada, detalle, log_bytes)
             VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)'
        )->execute([
            $userId,
            self::texto($descripcion, 4000, true),
            $equipo['id'], $equipo['nombre'], $equipo['so'], $equipo['version'], $equipo['empaquetada'],
            json_encode($detalle, JSON_UNESCAPED_UNICODE),
            $logGz === null ? 0 : strlen($logGz),
        ]);
        $id = (int) $pdo->lastInsertId();
        if ($logGz !== null && file_put_contents(self::logPath($id), $logGz) === false) {
            // Sin registro el ticket igual sirve (descripción + equipo).
            error_log("Tickets::crear: no se pudo guardar el registro del ticket {$id}");
            $pdo->prepare('UPDATE app_tickets SET log_bytes = 0 WHERE id = ?')->execute([$id]);
        }
        return $id;
    }

    /** @return array<int, array<string, mixed>> el más nuevo primero */
    public static function listar(?string $estado = null): array
    {
        self::migrar();
        $sql = 'SELECT t.*, u.username, u.display_name
                FROM app_tickets t LEFT JOIN users u ON u.id = t.user_id';
        $params = [];
        if ($estado !== null) {
            $sql .= ' WHERE t.estado = ?';
            $params[] = $estado;
        }
        $stmt = Db::get()->prepare($sql . ' ORDER BY t.id DESC');
        $stmt->execute($params);
        return $stmt->fetchAll();
    }

    /** @return array<string, mixed>|null */
    public static function obtener(int $id): ?array
    {
        self::migrar();
        $stmt = Db::get()->prepare(
            'SELECT t.*, u.username, u.display_name
             FROM app_tickets t LEFT JOIN users u ON u.id = t.user_id WHERE t.id = ?'
        );
        $stmt->execute([$id]);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    public static function actualizar(int $id, string $estado, string $nota): void
    {
        if (!in_array($estado, self::ESTADOS, true)) {
            throw new InvalidArgumentException('Estado inválido.');
        }
        self::migrar();
        Db::get()->prepare('UPDATE app_tickets SET estado = ?, nota = ? WHERE id = ?')
            ->execute([$estado, self::texto($nota, 4000, true), $id]);
    }

    /** Texto del registro, o null si no hay (o no se puede descomprimir). */
    public static function leerLog(int $id): ?string
    {
        $ruta = self::logPath($id);
        if (!is_file($ruta)) {
            return null;
        }
        $gz = file_get_contents($ruta);
        if ($gz === false || !function_exists('gzdecode')) {
            return null;
        }
        $texto = @gzdecode($gz);
        return $texto === false ? null : $texto;
    }

    /** Las últimas $n líneas, para mirar sin descargar. */
    public static function cola(string $texto, int $n): string
    {
        $lineas = preg_split('/\r?\n/', rtrim($texto)) ?: [];
        return implode("\n", array_slice($lineas, -$n));
    }

    /** @param mixed $v */
    private static function texto($v, int $max, bool $multilinea = false): string
    {
        $patron = $multilinea ? '/[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]/u' : '/[\x00-\x1F\x7F]/u';
        $s = trim(preg_replace($patron, '', (string) $v) ?? '');
        return function_exists('mb_substr') ? mb_substr($s, 0, $max) : substr($s, 0, $max);
    }
}
