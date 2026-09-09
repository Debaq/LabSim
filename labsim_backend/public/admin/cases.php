<?php

declare(strict_types=1);

// Casos ahora viven en patients.php (fichas clínicas), separado de agenda.php.
// Este archivo queda solo por si algo todavía apunta a la URL vieja.
header('Location: patients.php');
exit;
