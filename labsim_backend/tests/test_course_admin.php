<?php

declare(strict_types=1);

/**
 * La página de curso quedó partida en pestañas (views/course/_*.php) y el
 * POST, en CourseAdmin. Eso deja dos costuras que solo se notan en
 * producción: un formulario cuya acción no tiene pestaña asociada devuelve
 * al docente al Resumen y su aviso se pierde de vista, y una pestaña que se
 * nombra pero cuyo archivo no existe es un include roto (página en blanco a
 * mitad de carga). Las dos se cazan leyendo el código.
 */

require_once dirname(__DIR__) . '/src/CourseAdmin.php';
require_once dirname(__DIR__) . '/src/CourseOverview.php';

$raiz = dirname(__DIR__);
$fuente = (string) file_get_contents($raiz . '/src/CourseAdmin.php');

// Cada `case 'accion':` del switch tiene que estar en el mapa de pestañas.
// create_course es la excepción: redirige al curso nuevo, no vuelve a una
// pestaña del curso actual.
preg_match_all("/case '([a-z_]+)':/", $fuente, $m);
$acciones = array_unique($m[1]);
t_true(count($acciones) >= 15, 'CourseAdmin: el switch conserva todas las acciones (' . count($acciones) . ')');
foreach ($acciones as $accion) {
    if ($accion === 'create_course') {
        continue;
    }
    t_true(
        CourseAdmin::tabForAction($accion) !== null,
        "CourseAdmin: la acción '{$accion}' sabe a qué pestaña vuelve"
    );
}

// Y al revés: no queda un mapeo apuntando a una acción que ya no existe.
foreach (array_keys(CourseAdmin::TAB_BY_ACTION) as $accion) {
    t_true(
        in_array($accion, $acciones, true),
        "CourseAdmin: '{$accion}' está mapeada y sigue existiendo en el switch"
    );
}

// Toda pestaña nombrada tiene su partial.
foreach (array_unique(array_values(CourseAdmin::TAB_BY_ACTION)) as $tab) {
    t_true(is_file($raiz . "/views/course/_{$tab}.php"), "views/course/_{$tab}.php existe");
}
foreach (['resumen', 'personas', 'modulos', 'agenda', 'vinculos', 'pruebas', 'lista', 'tabs', 'params'] as $tab) {
    t_true(is_file($raiz . "/views/course/_{$tab}.php"), "views/course/_{$tab}.php existe");
}

// Las pestañas que ofrece el controlador también tienen que existir.
$controlador = (string) file_get_contents($raiz . '/public/admin/courses.php');
preg_match('/\$courseTabs = \[(.*?)\];/s', $controlador, $mt);
t_true(isset($mt[1]), 'courses.php declara $courseTabs');
if (isset($mt[1])) {
    preg_match_all("/'([a-z]+)' => \['label'/", $mt[1], $mk);
    foreach ($mk[1] as $tab) {
        t_true(is_file($raiz . "/views/course/_{$tab}.php"), "pestaña '{$tab}' del controlador tiene partial");
    }
}

t_eq(CourseAdmin::tabForAction('accion_que_no_existe'), null, 'tabForAction(): acción desconocida es null');

// --- Ventana de fechas del Resumen ----------------------------------------
// Las citas guardan la fecha como texto "dd-MM-yy", así que la ventana no
// puede ser un BETWEEN en SQL: se resuelve en PHP y hay que probarla.
$hoy = new DateTimeImmutable('2026-09-12');
t_true(CourseOverview::dentroDeVentana('12-09-26', $hoy, 7), 'ventana: hoy entra');
t_true(CourseOverview::dentroDeVentana('19-09-26', $hoy, 7), 'ventana: el último día entra');
t_true(!CourseOverview::dentroDeVentana('20-09-26', $hoy, 7), 'ventana: un día después no entra');
t_true(!CourseOverview::dentroDeVentana('11-09-26', $hoy, 7), 'ventana: ayer no entra');
t_true(!CourseOverview::dentroDeVentana('', $hoy, 7), 'ventana: paciente sin agendar (fecha vacía) no entra');
t_true(!CourseOverview::dentroDeVentana(null, $hoy, 7), 'ventana: fecha nula no entra');
t_true(!CourseOverview::dentroDeVentana('no-es-fecha', $hoy, 7), 'ventana: basura no entra');
// Cruce de año: el bug clásico de comparar "dd-MM-yy" como string.
$fin = new DateTimeImmutable('2026-12-28');
t_true(CourseOverview::dentroDeVentana('03-01-27', $fin, 7), 'ventana: cruza el año (03-01-27 desde el 28-12-26)');
t_true(!CourseOverview::dentroDeVentana('03-01-26', $fin, 7), 'ventana: mismo día y mes del año anterior no entra');

// --- Foco de curso del header ---------------------------------------------
// Solo la parte que no toca la base: con un admin completo,
// Courses::canAdminister() responde true sin consultar nada.
require_once dirname(__DIR__) . '/src/Auth.php';
require_once dirname(__DIR__) . '/src/Courses.php';
require_once dirname(__DIR__) . '/public/admin/_layout.php';

$admin = ['id' => 1, 'permission' => Auth::PERMISSION_ADMIN];
/** El foco se memoiza por request; los tests simulan varios seguidos. */
$olvidarFoco = static function (): void {
    unset($GLOBALS['__admin_course_ctx']);
};

$_SESSION = [];
$_GET = ['curso' => '7'];
$olvidarFoco();
t_eq(admin_course_context($admin), 7, 'foco: ?curso=7 lo elige');
t_eq($_SESSION['admin_course_ctx'] ?? null, 7, 'foco: queda guardado en la sesión');

$_GET = [];
$olvidarFoco();
t_eq(admin_course_context($admin), 7, 'foco: sin ?curso sigue el de la sesión');

$_GET = ['curso' => 'todos'];
$olvidarFoco();
t_eq(admin_course_context($admin), null, 'foco: ?curso=todos lo saca');
t_true(!isset($_SESSION['admin_course_ctx']), 'foco: y lo borra de la sesión');

$_GET = ['curso' => 'no-es-un-id'];
$olvidarFoco();
t_eq(admin_course_context($admin), null, 'foco: basura en ?curso no elige nada');

admin_set_course_context(4);
t_eq(admin_course_context($admin), 4, 'foco: entrar a un curso lo deja en foco');
t_eq(admin_course_context(null), null, 'foco: sin usuario no hay foco');

// Los GET actuales sobreviven al cambio de curso (el mes de la agenda, la
// página de la bandeja), salvo el id del curso cuando ya estás en su página.
$_GET = ['month' => '2026-09', 'curso' => '3', 'pagina' => '2'];
$_SERVER['PHP_SELF'] = '/admin/agenda.php';
$campos = admin_context_hidden_fields();
t_true(strpos($campos, 'name="month" value="2026-09"') !== false, 'foco: conserva el mes de la agenda');
t_true(strpos($campos, 'name="pagina" value="2"') !== false, 'foco: conserva la página');
t_true(strpos($campos, 'name="curso"') === false, 'foco: no duplica el propio curso');

$_GET = ['id' => '5', 'tab' => 'personas'];
$_SERVER['PHP_SELF'] = '/admin/courses.php';
$campos = admin_context_hidden_fields();
t_true(strpos($campos, 'name="id"') === false, 'foco: en courses.php el id viejo no viaja');
t_true(strpos($campos, 'name="tab" value="personas"') !== false, 'foco: pero sí la pestaña');

$_GET = [];
$_SESSION = [];
$olvidarFoco();
