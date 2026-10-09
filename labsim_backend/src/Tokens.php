<?php

declare(strict_types=1);

require_once __DIR__ . '/AppConfig.php';

/**
 * Sesiones de la app de escritorio (tabla `tokens`: bearer opaco, uno por
 * dispositivo/login) vistas y revocadas desde el panel (admin/tokens.php).
 *
 * Revocar = borrar la fila: el dispositivo vuelve a pedir el login. Se puede
 * de a uno, los marcados, o todos los que deja el filtro. Para lo último el
 * servidor vuelve a armar el conjunto con el mismo filtro (no confía en una
 * lista que mande el navegador).
 */
final class Tokens
{
    public const ROLES = ['admin', 'student'];

    // Vida máxima de una sesión desde que se inició (no desde el último
    // uso: así un token en uso tampoco vive para siempre). Se cambia en
    // admin/tokens.php; se guarda en app_config global.
    public const DURACION_KEY = 'sesion.duracion';
    public const DURACION_DEFAULT_HORAS = 12;
    public const DURACION_MIN_HORAS = 1;
    public const DURACION_MAX_HORAS = 720;   // 30 días

    /** @var int|null por petición: requireUser la consulta en cada llamada */
    private static $duracionCache = null;

    public static function duracionHoras(): int
    {
        if (self::$duracionCache === null) {
            $guardada = null;
            try {
                $guardada = AppConfig::getEffective(self::DURACION_KEY, null);
            } catch (Throwable $e) {
                error_log('[Tokens] no se pudo leer la duración: ' . $e->getMessage());
            }
            $horas = is_array($guardada) && isset($guardada['horas'])
                ? (int) $guardada['horas'] : self::DURACION_DEFAULT_HORAS;
            self::$duracionCache = self::acotarHoras($horas);
        }
        return self::$duracionCache;
    }

    public static function acotarHoras(int $horas): int
    {
        return max(self::DURACION_MIN_HORAS, min(self::DURACION_MAX_HORAS, $horas));
    }

    public static function guardarDuracionHoras(int $horas): int
    {
        $horas = self::acotarHoras($horas);
        AppConfig::set(self::DURACION_KEY, ['horas' => $horas], null);
        self::$duracionCache = $horas;
        return $horas;
    }

    /** Para comparar con created_at en SQLite: datetime('now', ?). */
    public static function limiteSql(): string
    {
        return '-' . self::duracionHoras() . ' hours';
    }

    /** Borra las sesiones que ya pasaron su vida máxima. Devuelve cuántas. */
    public static function purgarVencidas(PDO $pdo): int
    {
        $stmt = $pdo->prepare("DELETE FROM tokens WHERE created_at <= datetime('now', ?)");
        $stmt->execute([self::limiteSql()]);
        return $stmt->rowCount();
    }
    // Última actividad: hoy, la última semana, o más vieja que una semana.
    public const ACTIVIDAD = ['hoy', 'semana', 'vieja'];

    /**
     * Filtros que entiende el panel, saneados. Lo desconocido se ignora.
     *
     * @param array<string, mixed> $entrada ($_GET o $_POST)
     * @return array{q: string, rol: string, actividad: string}
     */
    public static function filtros(array $entrada): array
    {
        $rol = (string) ($entrada['rol'] ?? '');
        $actividad = (string) ($entrada['actividad'] ?? '');
        return [
            'q' => trim(mb_substr((string) ($entrada['q'] ?? ''), 0, 100)),
            'rol' => in_array($rol, self::ROLES, true) ? $rol : '',
            'actividad' => in_array($actividad, self::ACTIVIDAD, true) ? $actividad : '',
        ];
    }

    /**
     * WHERE (sobre `tokens t JOIN users u`) y sus parámetros.
     *
     * @param array{q: string, rol: string, actividad: string} $f
     * @return array{0: string, 1: list<string>}
     */
    public static function where(array $f): array
    {
        $partes = [];
        $params = [];
        if ($f['q'] !== '') {
            // Usuario, nombre o el final del token (lo que muestra la tabla).
            $like = '%' . strtr($f['q'], ['\\' => '\\\\', '%' => '\\%', '_' => '\\_']) . '%';
            $partes[] = "(u.username LIKE ? ESCAPE '\\' OR u.display_name LIKE ? ESCAPE '\\'"
                . " OR substr(t.token, -8) LIKE ? ESCAPE '\\')";
            array_push($params, $like, $like, $like);
        }
        if ($f['rol'] !== '') {
            $partes[] = 'u.role = ?';
            $params[] = $f['rol'];
        }
        if ($f['actividad'] === 'hoy') {
            $partes[] = "t.last_seen_at >= datetime('now', '-1 day')";
        } elseif ($f['actividad'] === 'semana') {
            $partes[] = "t.last_seen_at >= datetime('now', '-7 days')";
        } elseif ($f['actividad'] === 'vieja') {
            $partes[] = "t.last_seen_at < datetime('now', '-7 days')";
        }
        return [$partes ? implode(' AND ', $partes) : '1', $params];
    }

    /**
     * @param array{q: string, rol: string, actividad: string} $f
     * @return list<array<string, mixed>>
     */
    public static function listar(PDO $pdo, array $f): array
    {
        [$where, $params] = self::where($f);
        $stmt = $pdo->prepare(
            "SELECT t.token, t.created_at, t.last_seen_at, u.id AS user_id, u.username,
                    u.display_name, u.role,
                    datetime(t.created_at, '+" . self::duracionHoras() . " hours') AS vence_at
             FROM tokens t JOIN users u ON u.id = t.user_id
             WHERE {$where}
             ORDER BY t.last_seen_at DESC"
        );
        $stmt->execute($params);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    /**
     * Revoca los tokens dados (los que existan). Devuelve cuántos por usuario,
     * para el mensaje y la auditoría.
     *
     * @param list<string> $tokens
     * @return array<string, int> username => revocados
     */
    public static function revocar(PDO $pdo, array $tokens): array
    {
        $tokens = array_values(array_unique(array_filter($tokens, 'is_string')));
        if (!$tokens) {
            return [];
        }
        $porUsuario = [];
        $pdo->beginTransaction();
        try {
            // De a 500: SQLite tiene tope de parámetros por consulta.
            foreach (array_chunk($tokens, 500) as $lote) {
                $marcas = implode(',', array_fill(0, count($lote), '?'));
                $stmt = $pdo->prepare(
                    "SELECT u.username, COUNT(*) FROM tokens t JOIN users u ON u.id = t.user_id
                     WHERE t.token IN ({$marcas}) GROUP BY u.username"
                );
                $stmt->execute($lote);
                foreach ($stmt->fetchAll(PDO::FETCH_NUM) as [$usuario, $n]) {
                    $porUsuario[$usuario] = ($porUsuario[$usuario] ?? 0) + (int) $n;
                }
                $stmt->closeCursor();
                $pdo->prepare("DELETE FROM tokens WHERE token IN ({$marcas})")->execute($lote);
            }
            $pdo->commit();
        } catch (Throwable $e) {
            $pdo->rollBack();
            throw $e;
        }
        return $porUsuario;
    }

    /**
     * Revoca todo lo que deja el filtro (sin filtro: todas las sesiones).
     *
     * @param array{q: string, rol: string, actividad: string} $f
     * @return array<string, int>
     */
    public static function revocarFiltrados(PDO $pdo, array $f): array
    {
        return self::revocar($pdo, array_column(self::listar($pdo, $f), 'token'));
    }
}
