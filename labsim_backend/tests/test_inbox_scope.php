<?php

declare(strict_types=1);

/**
 * "Los alumnos de este docente" -- la regla que decide qué buzones ve el
 * listado de la bandeja (admin/inbox_send.php). Es la costura peligrosa de
 * esa página: si el ámbito se ensancha, un docente termina leyendo los
 * mensajes de alumnos de otro curso. Se prueba sin base porque
 * Courses::studentScopeSql() solo arma el WHERE (ver el comentario allá).
 */

require_once dirname(__DIR__) . '/src/Courses.php';

$mios = [10, 11];
$global = 'm.student_id IN (SELECT user_id FROM course_students)';

// Docente, un curso puntual: sale el curso pedido y nada más.
list($sql, $params) = Courses::studentScopeSql('curso', 10, $mios);
t_true(strpos($sql, 'course_id IN (?)') !== false, 'docente/curso: filtra por course_students');
t_eq($params, [10], 'docente/curso: solo el curso pedido');

// Docente, todos sus cursos: los suyos, no los del vecino.
list($sql, $params) = Courses::studentScopeSql('todos', 0, $mios);
t_true(strpos($sql, 'course_id IN (?,?)') !== false, 'docente/todos: un placeholder por curso suyo');
t_eq($params, [10, 11], 'docente/todos: exactamente sus cursos');

// Curso ajeno metido a mano en la URL: WHERE falso, cero filas. Nunca cae
// al listado global ni al primero de sus cursos.
list($sql, $params) = Courses::studentScopeSql('curso', 99, $mios);
t_eq($sql, '0', 'docente/curso ajeno: no devuelve nada');
t_eq($params, [], 'docente/curso ajeno: sin params');
t_true(strpos($sql, 'course_students') === false, 'docente/curso ajeno: ni siquiera consulta el roster');

// Docente sin cursos todavía: mismo cero, no "todos".
list($sql, $params) = Courses::studentScopeSql('todos', 0, []);
t_eq($sql, '0', 'docente sin cursos: no devuelve nada');
list($sql, $params) = Courses::studentScopeSql('curso', 10, []);
t_eq($sql, '0', 'docente sin cursos: tampoco por curso puntual');

// El ámbito global es SOLO del admin completo (myCourseIds === null).
list($sql, $params) = Courses::studentScopeSql('todos', 0, null);
t_eq($sql, $global, 'admin completo/todos: todos los alumnos matriculados');
t_eq($params, [], 'admin completo/todos: sin params');
list($sql, $params) = Courses::studentScopeSql('todos', 0, $mios);
t_true($sql !== $global, 'docente/todos: nunca el ámbito global del admin');

// Admin completo mirando un curso puntual: ese curso, sin intersección.
list($sql, $params) = Courses::studentScopeSql('curso', 99, null);
t_eq($params, [99], 'admin completo/curso: cualquier curso');

// Un alcance raro en la URL cae al curso puntual, no a "todos".
list($sql, $params) = Courses::studentScopeSql('cualquier_cosa', 10, $mios);
t_eq($params, [10], 'alcance desconocido: se trata como curso puntual');

// La página no rehace la regla por su cuenta.
$pagina = (string) file_get_contents(dirname(__DIR__) . '/public/admin/inbox_send.php');
t_true(strpos($pagina, 'Courses::studentScopeSql(') !== false, 'inbox_send.php usa el helper');
t_eq(substr_count($pagina, 'FROM course_students)'), 0, 'inbox_send.php no arma un ámbito global propio');

// El listado no puede crecer sin techo: abre en resumen y, cuando se busca,
// pagina contra un tope. La página no se puede incluir acá (arranca sesión y
// base), así que la costura se lee del código.
t_true((bool) preg_match('/const INBOX_ALUMNOS_RESUMEN = (\d+);/', $pagina, $mResumen), 'inbox_send.php: define el tamaño del resumen');
t_true((bool) preg_match('/const INBOX_ALUMNOS_MAX = (\d+);/', $pagina, $mMax), 'inbox_send.php: define el tope del listado completo');
t_true((int) $mResumen[1] > 0 && (int) $mResumen[1] <= 10, 'el resumen es corto (' . $mResumen[1] . ')');
t_true((int) $mMax[1] >= (int) $mResumen[1], 'el tope no es menor que el resumen');
t_true(strpos($pagina, 'LIMIT " . $porPaginaAlumnos . \' OFFSET ?\'') !== false, 'el listado limita por el modo, no por un número fijo');
t_true(strpos($pagina, '$verTodos = ') !== false && strpos($pagina, '$hayBusqueda') !== false, 'buscar abre el listado completo');
