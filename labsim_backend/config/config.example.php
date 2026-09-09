<?php
// Referencia: install.php genera config.php automáticamente, no hace falta
// tocar esto a mano. Sirve solo para saber qué forma tiene.

return [
    'db' => ['path' => __DIR__ . '/../data/labsim.sqlite'],
    'sync_poll_seconds' => 15,
    'lti_jwks_cache_seconds' => 3600,
    'pairing_code_ttl_seconds' => 300,
];
