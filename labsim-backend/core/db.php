<?php
/**
 * LabSim Backend - Conexión PDO SQLite + helpers
 */

require_once __DIR__ . '/config.php';

class Database {
    private static ?PDO $instance = null;

    public static function get(): PDO {
        if (self::$instance === null) {
            $dir = dirname(DB_PATH);
            if (!is_dir($dir)) {
                mkdir($dir, 0750, true);
            }

            self::$instance = new PDO('sqlite:' . DB_PATH, null, null, [
                PDO::ATTR_ERRMODE => PDO::ERRMODE_EXCEPTION,
                PDO::ATTR_DEFAULT_FETCH_MODE => PDO::FETCH_ASSOC,
                PDO::ATTR_EMULATE_PREPARES => false,
            ]);

            // WAL mode para mejor concurrencia
            self::$instance->exec('PRAGMA journal_mode=WAL');
            self::$instance->exec('PRAGMA foreign_keys=ON');
            self::$instance->exec('PRAGMA busy_timeout=5000');
        }

        return self::$instance;
    }

    /**
     * Ejecuta un SELECT y retorna todas las filas
     */
    public static function fetchAll(string $sql, array $params = []): array {
        $stmt = self::get()->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetchAll();
    }

    /**
     * Ejecuta un SELECT y retorna una sola fila
     */
    public static function fetchOne(string $sql, array $params = []): ?array {
        $stmt = self::get()->prepare($sql);
        $stmt->execute($params);
        $row = $stmt->fetch();
        return $row ?: null;
    }

    /**
     * Ejecuta INSERT/UPDATE/DELETE y retorna filas afectadas
     */
    public static function execute(string $sql, array $params = []): int {
        $stmt = self::get()->prepare($sql);
        $stmt->execute($params);
        return $stmt->rowCount();
    }

    /**
     * Genera un UUID v4
     */
    public static function uuid(): string {
        $data = random_bytes(16);
        $data[6] = chr(ord($data[6]) & 0x0f | 0x40);
        $data[8] = chr(ord($data[8]) & 0x3f | 0x80);
        return vsprintf('%s%s-%s-%s-%s-%s%s%s', str_split(bin2hex($data), 4));
    }

    /**
     * Paginación helper
     */
    public static function paginate(string $sql, array $params, int $page, int $limit): array {
        $limit = min($limit, MAX_PAGE_SIZE);
        $offset = ($page - 1) * $limit;

        // Count total
        $countSql = preg_replace('/SELECT .+ FROM/i', 'SELECT COUNT(*) as total FROM', $sql, 1);
        // Quitar ORDER BY para el count
        $countSql = preg_replace('/ORDER BY .+$/i', '', $countSql);
        $total = (int)(self::fetchOne($countSql, $params)['total'] ?? 0);

        // Fetch page
        $sql .= " LIMIT :_limit OFFSET :_offset";
        $params[':_limit'] = $limit;
        $params[':_offset'] = $offset;
        $items = self::fetchAll($sql, $params);

        return [
            'items' => $items,
            'pagination' => [
                'page' => $page,
                'limit' => $limit,
                'total' => $total,
                'pages' => (int)ceil($total / $limit),
            ],
        ];
    }
}
