<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';

Auth::startSession();
$_SESSION = [];
session_destroy();
header('Location: login.php');
