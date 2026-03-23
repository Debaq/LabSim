<?php
/**
 * LabSim Backend - Configuración
 */

// Entorno
define('LABSIM_ENV', getenv('LABSIM_ENV') ?: 'production');
define('LABSIM_DEBUG', LABSIM_ENV === 'development');

// Rutas
define('BASE_PATH', dirname(__DIR__));
define('DATA_PATH', BASE_PATH . '/data');
define('UPLOADS_PATH', BASE_PATH . '/uploads');
define('DB_PATH', DATA_PATH . '/labsim_server.db');

// JWT
define('JWT_SECRET', getenv('LABSIM_JWT_SECRET') ?: 'CHANGE_THIS_IN_PRODUCTION_' . md5(__DIR__));
define('JWT_ACCESS_TTL', 28800);     // 8 horas
define('JWT_REFRESH_TTL', 2592000);  // 30 días
define('JWT_ISSUER', 'labsim-backend');
define('JWT_ALGORITHM', 'HS256');

// CORS
define('CORS_ORIGINS', [
    'tauri://localhost',
    'https://tauri.localhost',
    'http://localhost:1420',   // dev vite
    'https://tmeduca.org',
]);

// Uploads
define('MAX_UPLOAD_SIZE', 50 * 1024 * 1024);  // 50MB
define('ALLOWED_GUIDE_TYPES', ['application/pdf', 'image/jpeg', 'image/png', 'image/webp', 'video/mp4', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']);
define('ALLOWED_ASSET_TYPES', ['application/pdf', 'image/jpeg', 'image/png', 'image/webp', 'application/zip', 'application/x-tar', 'application/gzip']);
define('ALLOWED_RELEASE_TYPES', ['application/x-debian-package', 'application/x-executable', 'application/zip', 'application/x-msi', 'application/x-apple-diskimage', 'application/octet-stream', 'application/gzip', 'application/x-tar']);

// Rate limiting
define('LOGIN_MAX_ATTEMPTS', 5);
define('LOGIN_LOCKOUT_MINUTES', 15);

// Paginación
define('DEFAULT_PAGE_SIZE', 20);
define('MAX_PAGE_SIZE', 100);

// Telemetría
define('TELEMETRY_BATCH_MAX', 500);  // máximo eventos por batch
