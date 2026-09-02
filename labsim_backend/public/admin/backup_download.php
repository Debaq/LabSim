<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Backups.php';

Auth::requireFullAdminSession();

try {
    $path = Backups::path((string) ($_GET['file'] ?? ''));
} catch (Throwable $e) {
    http_response_code(404);
    exit('Backup no encontrado.');
}

header('Content-Type: application/octet-stream');
header('Content-Disposition: attachment; filename="' . basename($path) . '"');
header('Content-Length: ' . (string) filesize($path));
header('Cache-Control: no-store');
readfile($path);
