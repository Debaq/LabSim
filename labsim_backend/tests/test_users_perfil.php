<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/Users.php';

/**
 * Formato del usuario de login que el docente elige en admin/perfil.php.
 * Solo la validación pura -- el resto de Users toca base y acá no hay
 * pdo_sqlite.
 */

t_true(Users::usernameValido('nbaier'), 'usuario simple');
t_true(Users::usernameValido('n.baier_2'), 'punto y guion bajo');
t_true(Users::usernameValido('abc'), '3 caracteres es el mínimo');
t_true(!Users::usernameValido('ab'), 'menos de 3 no sirve');
t_true(!Users::usernameValido(str_repeat('a', 65)), 'más de 64 no sirve');
t_true(!Users::usernameValido('nicolás'), 'sin tildes: se tipea en la app');
t_true(!Users::usernameValido('juan perez'), 'sin espacios');
t_true(
    !Users::usernameValido('Juan Pérez (1:42)'),
    'el usuario que arma LTI cuando Moodle no comparte el email no sirve para tipear en la app'
);
t_true(
    Users::usernameValido('correo@dominio.cl'),
    'el email sirve: es lo que LTI deja como username cuando Moodle lo comparte, y se puede tipear'
);
