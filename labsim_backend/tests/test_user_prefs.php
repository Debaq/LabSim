<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/UserPrefs.php';

/**
 * Preferencias de la app (users.prefs): solo se guarda lo que se reconoce.
 */

$p = UserPrefs::normalizar([
    'mouse_zurdo' => 1,
    'atajos' => [
        'a_ch1_subir' => 'q',          // minúscula -> mayúscula
        'a_ch1_bajar' => 'Down',
        'z_estimulo' => 'Space',
        'a_freq_mas' => 'F5',
        'inventada' => 'X',            // acción desconocida
        'a_ch2_subir' => 'Ctrl+X',     // combinación: no
        'a_ch2_bajar' => '',           // vacía: no
        'a_estimulo_ch1' => ['V'],     // no es texto
    ],
    'otra_cosa' => 'x',
]);
t_eq($p['mouse_zurdo'], true, 'Mouse para zurdos como booleano');
t_eq((array) $p['atajos'], [
    'a_ch1_subir' => 'Q', 'a_ch1_bajar' => 'Down', 'z_estimulo' => 'Space', 'a_freq_mas' => 'F5',
], 'Solo acciones conocidas con teclas simples');
t_true(!isset($p['otra_cosa']), 'Claves desconocidas no se guardan');

$vacio = UserPrefs::normalizar('basura');
t_eq($vacio['mouse_zurdo'], false, 'Sin datos: mouse normal');
t_eq(json_encode($vacio['atajos']), '{}', 'Atajos vacíos viajan como objeto JSON, no lista');
