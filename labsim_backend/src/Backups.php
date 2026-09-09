<?php

/**
 * Copias de seguridad de la base sqlite -- data/backups/ vive fuera de
 * public/ (igual que data/labsim.sqlite), así que no es accesible por URL
 * directa aunque no tenga su propio .htaccess: la protección es la misma
 * que ya usa la base viva.
 */
final class Backups
{
    private const PREFIX = 'labsim_';
    private const NAME_RE = '/^labsim_\d{4}-\d{2}-\d{2}_\d{6}(?:_[0-9a-f]{4})?\.sqlite$/';

    public static function dir(): string
    {
        $dir = dirname(Db::config()['db']['path']) . '/backups';
        if (!is_dir($dir) && !mkdir($dir, 0775, true) && !is_dir($dir)) {
            throw new RuntimeException("No se pudo crear la carpeta {$dir} (revisa permisos).");
        }
        return $dir;
    }

    /** Copia atómica y consistente del archivo vivo (incluye lo que esté en el WAL sin volcar todavía) a un archivo nuevo con fecha. Devuelve el nombre creado. */
    public static function create(): string
    {
        $dir = self::dir();
        $filename = self::PREFIX . date('Y-m-d_His') . '.sqlite';
        if (is_file($dir . '/' . $filename)) {
            // Dos backups en el mismo segundo (poco probable, pero el nombre
            // debe ser único -- VACUUM INTO falla si el destino ya existe).
            $filename = self::PREFIX . date('Y-m-d_His') . '_' . substr(bin2hex(random_bytes(2)), 0, 4) . '.sqlite';
        }
        $path = $dir . '/' . $filename;

        $pdo = Db::get();
        $pdo->exec('VACUUM INTO ' . $pdo->quote($path));

        return $filename;
    }

    public static function list(): array
    {
        $files = glob(self::dir() . '/' . self::PREFIX . '*.sqlite') ?: [];
        rsort($files);
        return array_map(static function (string $path): array {
            return [
                'filename' => basename($path),
                'size' => filesize($path),
                'created_at' => date('Y-m-d H:i:s', filemtime($path)),
            ];
        }, $files);
    }

    /** Nombre de archivo -> ruta completa, validando que sea un backup real (nunca confiar en el nombre que manda el navegador tal cual). */
    public static function path(string $filename): string
    {
        $safe = basename($filename);
        if (!preg_match(self::NAME_RE, $safe)) {
            throw new InvalidArgumentException('Nombre de backup inválido.');
        }
        $path = self::dir() . '/' . $safe;
        if (!is_file($path)) {
            throw new InvalidArgumentException('Backup no encontrado.');
        }
        return $path;
    }

    public static function delete(string $filename): void
    {
        unlink(self::path($filename));
    }

    /**
     * Restaura $filename como la base viva. Antes de tocar nada toma un
     * backup de seguridad del estado actual -- así un restore por error
     * también se puede deshacer restaurando ESE backup. Devuelve el nombre
     * de ese backup de seguridad.
     */
    public static function restore(string $filename): string
    {
        $backupPath = self::path($filename);
        $liveDbPath = Db::config()['db']['path'];

        $preRestoreBackup = self::create();

        Db::closeForRestore();

        if (!copy($backupPath, $liveDbPath)) {
            throw new RuntimeException('No se pudo restaurar el backup.');
        }
        // Sidecars de WAL/SHM de la base anterior -- si quedan, SQLite
        // intentaría recombinarlos con el archivo recién restaurado.
        @unlink($liveDbPath . '-wal');
        @unlink($liveDbPath . '-shm');

        return $preRestoreBackup;
    }

    public static function formatBytes(int $bytes): string
    {
        if ($bytes >= 1024 * 1024) {
            return round($bytes / (1024 * 1024), 1) . ' MB';
        }
        if ($bytes >= 1024) {
            return round($bytes / 1024, 1) . ' KB';
        }
        return $bytes . ' B';
    }
}
