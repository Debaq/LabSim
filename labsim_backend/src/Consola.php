<?php

/**
 * Consola remota: SQL libre y lectura de data/ con un token temporal (ver
 * admin/consola.php y api/consola.php). Pensada para que el admin le dé
 * acceso a la base viva a quien diagnostica (Claude, en una sesión de
 * trabajo) sin pasarle su contraseña.
 *
 * Sin red de seguridad a propósito -- el admin pidió SQL libre, escritura
 * incluida. Lo que sí hay: el token vence solo, se revoca desde el panel,
 * se guarda solo su hash, cada llamada queda registrada (consola_consultas)
 * y la acción "backup" deja una copia antes de tocar algo.
 */
final class Consola
{
    public const PREFIJO = 'lsc_';
    /** Duraciones que ofrece el panel, en horas. */
    public const DURACIONES = [1, 4, 8, 24, 72];
    public const MAX_FILAS = 5000;
    public const MAX_TEXTO_LOG = 20000;
    public const MAX_LECTURA_BYTES = 4 * 1024 * 1024;

    /** Horas pedidas llevadas a una de las DURACIONES (la más cercana sin pasarse; 1 h si es menos). */
    public static function normalizarHoras(int $horas): int
    {
        $elegida = self::DURACIONES[0];
        foreach (self::DURACIONES as $d) {
            if ($d <= $horas) {
                $elegida = $d;
            }
        }
        return $elegida;
    }

    public static function hash(string $token): string
    {
        return hash('sha256', $token);
    }

    /** Crea un token y devuelve el texto en claro -- es la única vez que existe fuera de quien lo recibe. */
    public static function crearToken(array $admin, int $horas, string $etiqueta): string
    {
        $horas = self::normalizarHoras($horas);
        $token = self::PREFIJO . bin2hex(random_bytes(32));
        Db::get()->prepare(
            "INSERT INTO consola_tokens (token_hash, etiqueta, created_by, created_by_username, expires_at)
             VALUES (?, ?, ?, ?, datetime('now', ?))"
        )->execute([
            self::hash($token),
            mb_substr(trim($etiqueta), 0, 80),
            (int) $admin['id'],
            (string) $admin['username'],
            "+{$horas} hours",
        ]);
        return $token;
    }

    public static function revocar(int $id): void
    {
        Db::get()->prepare(
            'UPDATE consola_tokens SET revoked_at = CURRENT_TIMESTAMP WHERE id = ? AND revoked_at IS NULL'
        )->execute([$id]);
    }

    /** El token del header si está vigente (no vencido ni revocado), o null. */
    public static function tokenVigente(string $token): ?array
    {
        if (strpos($token, self::PREFIJO) !== 0) {
            return null;
        }
        $stmt = Db::get()->prepare(
            "SELECT * FROM consola_tokens
              WHERE token_hash = ? AND revoked_at IS NULL AND expires_at > datetime('now')"
        );
        $stmt->execute([self::hash($token)]);
        $row = $stmt->fetch();
        $stmt->closeCursor();   // ver Db::get: lectura abierta + escritura = "database is locked"
        return $row ?: null;
    }

    /** Tokens para el panel: vigentes primero, después los últimos vencidos/revocados. */
    public static function listarTokens(): array
    {
        return Db::get()->query(
            "SELECT *, (revoked_at IS NULL AND expires_at > datetime('now')) AS vigente
               FROM consola_tokens ORDER BY vigente DESC, id DESC LIMIT 30"
        )->fetchAll();
    }

    public static function ultimasConsultas(int $limite = 100): array
    {
        $stmt = Db::get()->prepare(
            'SELECT q.*, t.etiqueta FROM consola_consultas q
               LEFT JOIN consola_tokens t ON t.id = q.token_id
              ORDER BY q.id DESC LIMIT ?'
        );
        $stmt->bindValue(1, $limite, PDO::PARAM_INT);
        $stmt->execute();
        return $stmt->fetchAll();
    }

    /**
     * Una sentencia, con parámetros "?" o ":nombre". Si devuelve columnas,
     * vienen las filas (hasta MAX_FILAS); si no, cuántas tocó.
     */
    public static function ejecutar(string $sql, array $params = []): array
    {
        $pdo = Db::get();
        $inicio = microtime(true);
        return Db::reintentar(static function () use ($pdo, $sql, $params, $inicio): array {
            $stmt = $pdo->prepare($sql);
            $stmt->execute(self::paramsPdo($params));
            $columnas = [];
            for ($i = 0; $i < $stmt->columnCount(); $i++) {
                $meta = $stmt->getColumnMeta($i);
                $columnas[] = $meta['name'] ?? "col{$i}";
            }
            $filas = [];
            $truncado = false;
            if ($columnas) {
                while (($fila = $stmt->fetch(PDO::FETCH_NUM)) !== false) {
                    if (count($filas) >= self::MAX_FILAS) {
                        $truncado = true;
                        break;
                    }
                    $filas[] = $fila;
                }
            }
            $cambios = $columnas ? 0 : $stmt->rowCount();
            $stmt->closeCursor();
            return [
                'columnas' => $columnas,
                'filas' => $filas,
                'n' => count($filas),
                'truncado' => $truncado,
                'cambios' => $cambios,
                'ms' => (int) round((microtime(true) - $inicio) * 1000),
            ];
        });
    }

    /**
     * Varias sentencias separadas por ";" en UNA transacción: o entran todas
     * o ninguna. Sin filas de vuelta (para eso, ejecutar()).
     */
    public static function script(string $sql): array
    {
        $pdo = Db::get();
        $inicio = microtime(true);
        return Db::reintentar(static function () use ($pdo, $sql, $inicio): array {
            $antes = (int) $pdo->query('SELECT total_changes()')->fetchColumn();
            // IMMEDIATE: toma la escritura al empezar, no a mitad del script.
            $pdo->exec('BEGIN IMMEDIATE');
            try {
                $pdo->exec($sql);
                $pdo->exec('COMMIT');
            } catch (Throwable $e) {
                if ($pdo->inTransaction()) {
                    $pdo->rollBack();
                } else {
                    try {
                        $pdo->exec('ROLLBACK');
                    } catch (Throwable $ignorado) {
                    }
                }
                throw $e;
            }
            $despues = (int) $pdo->query('SELECT total_changes()')->fetchColumn();
            return [
                'cambios' => $despues - $antes,
                'ms' => (int) round((microtime(true) - $inicio) * 1000),
            ];
        });
    }

    /** CREATE de todas las tablas, índices y triggers. */
    public static function esquema(): array
    {
        return Db::get()->query(
            "SELECT type, name, tbl_name, sql FROM sqlite_master
              WHERE name NOT LIKE 'sqlite_%' ORDER BY tbl_name, type DESC, name"
        )->fetchAll();
    }

    /** Carpeta data/ (base, backups, informes, tickets...): lo único que se lee como archivo. */
    public static function dirData(): string
    {
        return (string) realpath(dirname(Db::config()['db']['path']));
    }

    /**
     * Ruta relativa a data/ resuelta y verificada: null si no existe o si
     * se sale de data/ (".." o un enlace hacia afuera).
     */
    public static function resolverRuta(string $base, string $relativa): ?string
    {
        $relativa = ltrim(str_replace('\\', '/', $relativa), '/');
        $real = realpath($base . ($relativa === '' ? '' : '/' . $relativa));
        if ($real === false) {
            return null;
        }
        if ($real !== $base && strpos($real, $base . DIRECTORY_SEPARATOR) !== 0) {
            return null;
        }
        return $real;
    }

    public static function listarArchivos(string $relativa): array
    {
        $base = self::dirData();
        $dir = self::resolverRuta($base, $relativa);
        if ($dir === null || !is_dir($dir)) {
            throw new RuntimeException('No existe esa carpeta dentro de data/.');
        }
        $salida = [];
        foreach (scandir($dir) ?: [] as $nombre) {
            if ($nombre === '.' || $nombre === '..') {
                continue;
            }
            $p = $dir . '/' . $nombre;
            $salida[] = [
                'nombre' => $nombre,
                'tipo' => is_dir($p) ? 'dir' : 'archivo',
                'bytes' => is_file($p) ? (int) filesize($p) : null,
                'modificado' => date('Y-m-d H:i:s', (int) filemtime($p)),
            ];
        }
        return $salida;
    }

    /**
     * Contenido de un archivo de data/. Los .gz (registros de tickets) se
     * descomprimen. Lo que no es texto vuelve en base64.
     */
    public static function leerArchivo(string $relativa): array
    {
        $base = self::dirData();
        $p = self::resolverRuta($base, $relativa);
        if ($p === null || !is_file($p)) {
            throw new RuntimeException('No existe ese archivo dentro de data/.');
        }
        $bytes = (int) filesize($p);
        if ($bytes > self::MAX_LECTURA_BYTES) {
            throw new RuntimeException("Archivo de {$bytes} bytes, pasa el tope de " . self::MAX_LECTURA_BYTES . '.');
        }
        $contenido = (string) file_get_contents($p);
        $gz = substr($p, -3) === '.gz' && function_exists('gzdecode');
        if ($gz) {
            $descomprimido = @gzdecode($contenido);
            if ($descomprimido !== false) {
                $contenido = $descomprimido;
            }
        }
        $esTexto = mb_check_encoding($contenido, 'UTF-8') && strpos($contenido, "\0") === false;
        return [
            'ruta' => ltrim(substr($p, strlen($base)), '/'),
            'bytes' => $bytes,
            'descomprimido' => $gz,
            'codificacion' => $esTexto ? 'texto' : 'base64',
            'contenido' => $esTexto ? $contenido : base64_encode($contenido),
        ];
    }

    /** Anota la llamada y el uso del token. Que no se pueda anotar no corta la respuesta. */
    public static function registrar(int $tokenId, string $tipo, string $texto, ?array $resultado, ?string $error, string $ip): void
    {
        try {
            $pdo = Db::get();
            $pdo->prepare(
                'INSERT INTO consola_consultas (token_id, tipo, texto, filas, cambios, ms, error, ip)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?)'
            )->execute([
                $tokenId,
                $tipo,
                mb_substr($texto, 0, self::MAX_TEXTO_LOG),
                isset($resultado['n']) ? (int) $resultado['n'] : null,
                isset($resultado['cambios']) ? (int) $resultado['cambios'] : null,
                isset($resultado['ms']) ? (int) $resultado['ms'] : null,
                $error !== null ? mb_substr($error, 0, 2000) : null,
                $ip,
            ]);
            $pdo->prepare(
                'UPDATE consola_tokens SET last_used_at = CURRENT_TIMESTAMP, usos = usos + 1 WHERE id = ?'
            )->execute([$tokenId]);
        } catch (Throwable $e) {
            error_log('[Consola] no se pudo registrar: ' . $e->getMessage());
        }
    }

    /** Params del JSON a lo que espera PDO: lista para "?", mapa para ":nombre" (con o sin los dos puntos). */
    public static function paramsPdo(array $params): array
    {
        if ($params === [] || array_keys($params) === range(0, count($params) - 1)) {
            return array_values($params);
        }
        $salida = [];
        foreach ($params as $k => $v) {
            $k = (string) $k;
            $salida[$k[0] === ':' ? $k : ':' . $k] = $v;
        }
        return $salida;
    }
}
