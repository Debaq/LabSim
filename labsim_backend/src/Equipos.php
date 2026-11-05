<?php

declare(strict_types=1);

require_once __DIR__ . '/AppReleases.php';

/**
 * Equipos donde se usa la app de escritorio y qué versión tienen, para
 * admin/versiones.php. La app manda un bloque "equipo" junto con el login
 * (api/admin_login.php y api/pair_exchange.php; ver core/equipo.py del
 * cliente) y acá queda la última vez que se entró desde cada uno.
 *
 * La clave es un id derivado del machine-id (Linux) o MachineGuid (Windows),
 * no el nombre: las máquinas del laboratorio salen de la misma imagen y
 * pueden compartir hostname.
 */
final class Equipos
{
    /** Un equipo que no entra hace este tiempo se deja de mostrar. */
    private const OLVIDAR_DIAS = 180;
    /** El historial de ingresos (quién usó qué equipo) se guarda un año. */
    public const GUARDAR_DIAS = 365;

    /**
     * El bloque tal como lo manda la app, validado; null si no sirve (app
     * vieja que no lo manda, o datos raros).
     *
     * @param mixed $raw
     * @return array{id: string, nombre: string, so: string, version: string, empaquetada: int}|null
     */
    public static function normalizar($raw): ?array
    {
        if (!is_array($raw)) {
            return null;
        }
        $id = (string) ($raw['id'] ?? '');
        $version = (string) ($raw['version'] ?? '');
        if (!preg_match('/^[0-9a-f]{16}$/', $id) || !preg_match('/^[0-9A-Za-z.\-]{1,40}$/', $version)) {
            return null;
        }
        return [
            'id' => $id,
            'nombre' => self::texto($raw['nombre'] ?? '', 64),
            'so' => self::texto($raw['so'] ?? '', 20),
            'version' => $version,
            'empaquetada' => empty($raw['empaquetada']) ? 0 : 1,
        ];
    }

    /**
     * Anota el ingreso. Nunca lanza: un login no puede fallar por esto.
     *
     * @param mixed $raw
     */
    public static function registrar($raw, int $userId): void
    {
        $equipo = self::normalizar($raw);
        if ($equipo === null) {
            return;
        }
        try {
            Db::migrateAppEquiposIfNeeded();
            $pdo = Db::get();
            $pdo->prepare(
                'INSERT OR REPLACE INTO app_equipos (id, nombre, so, version, empaquetada, user_id, last_seen_at)
                 VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)'
            )->execute([$equipo['id'], $equipo['nombre'], $equipo['so'], $equipo['version'],
                        $equipo['empaquetada'], $userId]);
            $pdo->exec(
                "DELETE FROM app_equipos WHERE last_seen_at < datetime('now', '-" . self::OLVIDAR_DIAS . " days')"
            );
            // El historial: quién entró desde este equipo y cuándo.
            $pdo->prepare('INSERT INTO app_equipos_ingresos (equipo_id, nombre, user_id, ip) VALUES (?, ?, ?, ?)')
                ->execute([$equipo['id'], $equipo['nombre'], $userId,
                           substr((string) ($_SERVER['REMOTE_ADDR'] ?? ''), 0, 45)]);
            $pdo->exec(
                "DELETE FROM app_equipos_ingresos WHERE created_at < datetime('now', '-" . self::GUARDAR_DIAS . " days')"
            );
        } catch (Throwable $e) {
            error_log('Equipos::registrar: ' . $e->getMessage());
        }
    }

    /**
     * Ingresos de un día (fecha local 'YYYY-MM-DD'), del más antiguo al más
     * reciente, con el equipo y el usuario. Cada ingreso dura hasta el
     * siguiente del mismo equipo: eso lo arma la vista.
     *
     * @return array<int, array<string, mixed>>
     */
    public static function ingresos(string $fechaLocal): array
    {
        Db::migrateAppEquiposIfNeeded();
        $zona = new DateTimeZone(Clock::ZONA);
        $desde = DateTimeImmutable::createFromFormat('!Y-m-d', $fechaLocal, $zona);
        if ($desde === false) {
            return [];
        }
        $utc = new DateTimeZone('UTC');
        $stmt = Db::get()->prepare(
            'SELECT i.equipo_id, i.nombre, i.ip, i.created_at, u.username, u.display_name
             FROM app_equipos_ingresos i LEFT JOIN users u ON u.id = i.user_id
             WHERE i.created_at >= ? AND i.created_at < ?
             ORDER BY i.created_at, i.id'
        );
        $stmt->execute([$desde->setTimezone($utc)->format('Y-m-d H:i:s'),
                        $desde->modify('+1 day')->setTimezone($utc)->format('Y-m-d H:i:s')]);
        return $stmt->fetchAll();
    }

    /** @return array<int, array<string, mixed>> el más reciente primero */
    public static function listar(): array
    {
        Db::migrateAppEquiposIfNeeded();
        return Db::get()->query(
            'SELECT e.*, u.username, u.display_name
             FROM app_equipos e LEFT JOIN users u ON u.id = e.user_id
             ORDER BY e.last_seen_at DESC'
        )->fetchAll();
    }

    /**
     * Qué tan al día está una versión contra la lista publicada.
     * clave: al_dia | atrasado | no_publicada | desarrollo | sin_lista
     *
     * @param array<int, array<string, mixed>> $releases
     * @return array{clave: string, texto: string}
     */
    public static function estado(string $version, bool $empaquetada, array $releases): array
    {
        if (!$empaquetada) {
            return ['clave' => 'desarrollo', 'texto' => 'desarrollo'];
        }
        if (!$releases) {
            return ['clave' => 'sin_lista', 'texto' => 'sin lista'];
        }
        usort($releases, static function (array $a, array $b): int {
            return strcmp((string) $b['created_at'], (string) $a['created_at']);
        });
        foreach ($releases as $i => $r) {
            if (substr((string) $r['tag_name'], strlen(AppReleases::PREFIJO)) !== $version) {
                continue;
            }
            if ($i === 0) {
                return ['clave' => 'al_dia', 'texto' => 'al día'];
            }
            return ['clave' => 'atrasado', 'texto' => $i === 1 ? '1 versión atrás' : "{$i} versiones atrás"];
        }
        return ['clave' => 'no_publicada', 'texto' => 'no publicada'];
    }

    /** @param mixed $v */
    private static function texto($v, int $max): string
    {
        $s = trim(preg_replace('/[\x00-\x1F\x7F]/u', '', (string) $v) ?? '');
        return function_exists('mb_substr') ? mb_substr($s, 0, $max) : substr($s, 0, $max);
    }
}
