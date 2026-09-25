<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/AppReleases.php';

/**
 * El backend consulta a GitHub por todo el laboratorio (ver AppReleases):
 * una vez por TTL, y una lista vieja no se hace pasar por buena.
 */

$dir = sys_get_temp_dir() . '/labsim_app_releases_' . getmypid();
@mkdir($dir);
$cache = $dir . '/app_releases.json';
@unlink($cache);

$llamadas = 0;
$github = function () use (&$llamadas) {
    $llamadas++;
    return [
        ['tag_name' => 'pyinstaller-v0.9.8-raaa', 'created_at' => '2026-09-25T03:00:00Z',
         'body' => 'notas', 'draft' => false, 'author' => ['login' => 'x'],
         'assets' => [['name' => 'manifest.json', 'size' => 10,
                       'browser_download_url' => 'https://github.com/d/manifest.json']]],
        ['tag_name' => 'v3.1.0', 'created_at' => '2026-09-20T00:00:00Z', 'assets' => []],
    ];
};
$caido = function () use (&$llamadas) {
    $llamadas++;
    return null;
};

$t0 = 1_000_000;
$l = AppReleases::lista($github, $cache, $t0);
t_eq(count($l['releases']), 1, 'Solo las versiones de esta app, no las del rewrite Tauri');
t_eq(array_keys($l['releases'][0]), ['tag_name', 'created_at', 'body', 'assets'],
     'Solo los campos que usa el updater');
t_eq($l['releases'][0]['assets'][0],
     ['name' => 'manifest.json', 'browser_download_url' => 'https://github.com/d/manifest.json'],
     'Assets con nombre y URL de descarga');

AppReleases::lista($github, $cache, $t0 + AppReleases::TTL - 1);
t_eq($llamadas, 1, 'Dentro del TTL no se vuelve a consultar a GitHub');

AppReleases::lista($github, $cache, $t0 + AppReleases::TTL);
t_eq($llamadas, 2, 'Vencido el TTL se consulta de nuevo');

$l = AppReleases::lista($caido, $cache, $t0 + AppReleases::TTL + 60);
t_eq($l['consultado'], $t0 + AppReleases::TTL, 'GitHub caído: se sirve la guardada si es reciente');

t_eq(AppReleases::lista($caido, $cache, $t0 + AppReleases::TTL + AppReleases::MAX_VIEJA), null,
     'Una lista demasiado vieja no se sirve: el cliente la tomaría por buena');

@unlink($cache);
t_eq(AppReleases::lista($caido, $cache, $t0), null, 'Sin GitHub ni guardada: null');

@unlink($cache . '.lock');
@rmdir($dir);
