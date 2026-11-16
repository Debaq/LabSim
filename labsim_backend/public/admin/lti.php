<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/Courses.php';

$me = Auth::requireFullAdminSession();

$error = null;
$success = null;
$generated11 = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $id = $_POST['id'] !== '' ? (int) $_POST['id'] : null;
    $ltiVersion = $_POST['lti_version'] ?? '1.3';

    // Curso al que matricula la clave por sí sola: se guarda igual para las
    // dos versiones de LTI y también solo, sin tocar las credenciales (ese
    // es el caso de la tabla de abajo, donde cambiar el curso no puede
    // implicar regenerar el shared secret).
    if (($_POST['form_action'] ?? '') === 'set_default_course') {
        $courseId = (int) ($_POST['default_course_id'] ?? 0);
        if ($id === null) {
            $error = 'Falta la clave LTI.';
        } else {
            Lti::setDefaultCourse($id, $courseId > 0 ? $courseId : null);
            $success = $courseId > 0
                ? 'Listo: quien entre con esa clave queda matriculado en ese curso.'
                : 'Esa clave ya no matricula sola.';
            AdminAudit::log($me, 'lti_set_default_course', ['id' => $id, 'course_id' => $courseId ?: null]);
        }
    } elseif ($ltiVersion === '1.1') {
        // El backend genera las credenciales (como hace Moodle al registrar
        // un tool) en vez de que el admin las invente a mano -- menos typos,
        // más entropía. El shared_secret queda a la vista del admin completo
        // ("Ver secreto" en la tabla): sin él no se puede reusar la clave en
        // otro curso del mismo Moodle.
        $consumerKey = bin2hex(random_bytes(16));
        $sharedSecret = bin2hex(random_bytes(24));
        $nuevoId = Lti::upsertPlatform11($id, $consumerKey, $sharedSecret);
        // Una clave por curso, en un solo paso: si se eligió curso al
        // crearla, queda matriculando desde el primer launch. Al regenerar
        // credenciales el campo no viene, y el curso ya asignado no se toca.
        if (isset($_POST['default_course_id'])) {
            $courseId = (int) $_POST['default_course_id'];
            Lti::setDefaultCourse($nuevoId, $courseId > 0 ? $courseId : null);
        }
        $success = $id !== null ? 'Credenciales LTI 1.1 regeneradas.' : 'Herramienta LTI 1.1 creada.';
        $generated11 = ['consumer_key' => $consumerKey, 'shared_secret' => $sharedSecret];
        AdminAudit::log($me, $id !== null ? 'lti11_regenerate' : 'lti11_create', ['id' => $id]);
    } else {
        $issuer = trim((string) ($_POST['issuer'] ?? ''));
        $clientId = trim((string) ($_POST['client_id'] ?? ''));
        $deploymentId = trim((string) ($_POST['deployment_id'] ?? ''));
        $authLoginUrl = trim((string) ($_POST['auth_login_url'] ?? ''));
        $authTokenUrl = trim((string) ($_POST['auth_token_url'] ?? ''));
        $jwksUrl = trim((string) ($_POST['jwks_url'] ?? ''));

        if ($issuer === '' || $clientId === '' || $deploymentId === '' || $authLoginUrl === '' || $jwksUrl === '') {
            $error = 'Completa issuer, client_id, deployment_id, auth_login_url y jwks_url (todos vienen de la pantalla "External tool" de Moodle).';
        } else {
            $nuevoId = Lti::upsertPlatform13($id, $issuer, $clientId, $deploymentId, $authLoginUrl, $authTokenUrl ?: $authLoginUrl, $jwksUrl);
            if (isset($_POST['default_course_id'])) {
                $courseId = (int) $_POST['default_course_id'];
                Lti::setDefaultCourse($nuevoId, $courseId > 0 ? $courseId : null);
            }
            $success = 'Plataforma LTI 1.3 guardada.';
            AdminAudit::log($me, 'lti13_upsert', ['id' => $id, 'issuer' => $issuer]);
        }
    }
}

$scheme = (!empty($_SERVER['HTTPS']) && $_SERVER['HTTPS'] !== 'off') ? 'https' : 'http';
$baseDir = rtrim(str_replace('\\', '/', dirname(dirname($_SERVER['SCRIPT_NAME']))), '/');
$loginUrl = "{$scheme}://{$_SERVER['HTTP_HOST']}{$baseDir}/lti/login.php";
$launchUrl = "{$scheme}://{$_SERVER['HTTP_HOST']}{$baseDir}/lti/launch.php";
// El ícono de la actividad en Moodle ("URL del icono" y "URL del icono
// seguro": la segunda es la misma en https, que es como corre el backend).
$iconUrl = "{$scheme}://{$_SERVER['HTTP_HOST']}{$baseDir}/img/labsim_icono.png";

$platforms = Lti::listPlatforms();
$cursos = Courses::listActive();
$cursoNombre = [];
foreach ($cursos as $c) {
    $cursoNombre[(int) $c['id']] = (string) $c['name'];
}

/** El <select> de curso de una clave, igual en el alta y en la tabla. */
$selectCurso = static function (?int $seleccionado) use ($cursos): string {
    $html = '<select name="default_course_id">';
    $html .= '<option value="0">-- ninguno: no matricula sola --</option>';
    foreach ($cursos as $c) {
        $html .= '<option value="' . (int) $c['id'] . '"'
            . ($seleccionado === (int) $c['id'] ? ' selected' : '') . '>'
            . htmlspecialchars((string) $c['name']) . '</option>';
    }
    return $html . '</select>';
};

admin_header('Conexión LTI (Moodle)', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <strong>Datos para la herramienta en Moodle (LTI 1.1)</strong>
    <p class="muted">Lo que va en cada campo de "Editar herramienta" (en el curso de Moodle o en el sitio):</p>
    <table>
        <tr><td>URL de la herramienta</td><td class="mono"><?= htmlspecialchars($launchUrl) ?></td></tr>
        <tr><td>Versión LTI</td><td>LTI 1.0/1.1</td></tr>
        <tr><td>Clave de cliente y Secreto compartido</td><td>Los de la clave en la tabla de abajo ("Ver secreto").</td></tr>
        <tr><td>URL del icono</td><td class="mono"><?= htmlspecialchars($iconUrl) ?></td></tr>
        <tr><td>URL del icono seguro</td><td class="mono"><?= htmlspecialchars($iconUrl) ?></td></tr>
        <tr><td>Admite enlaces profundos / URL de selección de contenido</td>
            <td>Sin marcar y vacía. Es para herramientas que dejan elegir un contenido al crear la actividad
                (un libro, un video); LabSim no lo usa: la actividad siempre abre la misma pantalla.</td></tr>
        <tr><td>Contenedor de inicio</td><td>Incrustar, sin bloques (o Nueva ventana).</td></tr>
        <tr><td>Privacidad</td>
            <td>Compartir el nombre <strong>Siempre</strong> y el correo <strong>Siempre</strong> (si no, el
                usuario del alumno en LabSim queda como "NOMBRE (clave:id)"); aceptar calificaciones:
                Nunca.</td></tr>
    </table>
    <p class="muted">
        <strong>Un mismo Moodle, una sola clave.</strong> LabSim reconoce a la persona por la clave y su id de
        Moodle: si un alumno entra a dos cursos del mismo Moodle con claves distintas, queda con dos cuentas
        (la segunda, vacía). Para otro curso del mismo Moodle se usa la clave que ya existe y ese curso de
        Moodle se vincula al curso de LabSim en <a href="courses.php">Cursos → Vínculos</a>; el vínculo manda
        sobre el curso por defecto de la clave.
    </p>
</div>

<div class="card">
    <strong>LTI 1.1 (OAuth1) -- más simple, recomendado si 1.3 da problemas</strong>
    <p class="muted">
        Primero crea la herramienta acá abajo (el backend genera las credenciales), después regístrala en Moodle:
        Administración del sitio → Plugins → Herramientas externas → Gestionar herramientas →
        Configurar una herramienta manualmente, versión LTI <strong>1.0/1.1</strong>.
    </p>

    <?php if ($generated11 !== null): ?>
    <div style="background:var(--color-warn-bg); border:1px solid var(--color-warn-text); padding:0.75rem; margin:0.5rem 0;">
        <strong>Copia esto en Moodle (el secreto queda después en "Ver secreto" de la tabla):</strong>
        <p>Tool URL<br><span class="mono"><?= htmlspecialchars($launchUrl) ?></span></p>
        <p>Consumer key<br><span class="mono"><?= htmlspecialchars($generated11['consumer_key']) ?></span></p>
        <p>Shared secret<br><span class="mono"><?= htmlspecialchars($generated11['shared_secret']) ?></span></p>
    </div>
    <?php endif; ?>

    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="id" value="">
        <input type="hidden" name="lti_version" value="1.1">
        <label>Matricular en este curso a quien entre con esta clave
            <?= $selectCurso(null) ?>
        </label>
        <p class="muted">
            Con un curso elegido acá, la clave <strong>matricula sola</strong>: el alumno entra
            desde Moodle y queda en el roster de ese curso en el primer launch, sin que nadie lo
            agregue a mano ni vincule nada después. Una clave nueva es para <strong>otro
            Moodle</strong>: para otro curso del mismo Moodle se reusa la que ya existe y se vincula
            ese curso desde <a href="courses.php">Cursos → Vínculos</a> (con dos claves, el alumno
            que está en los dos cursos queda con dos cuentas).
        </p>
        <button type="submit">Crear nueva herramienta LTI 1.1</button>
    </form>
</div>

<div class="card">
    <strong>LTI 1.3 (OIDC) -- URLs para registrar LabSim como "herramienta externa" en Moodle</strong>
    <p class="muted">
        Configura una herramienta manualmente, versión LTI 1.3.
    </p>
    <label>Initiate login URL</label>
    <p class="mono"><?= htmlspecialchars($loginUrl) ?></p>
    <label>Redirection URI (Tool launch URL)</label>
    <p class="mono"><?= htmlspecialchars($launchUrl) ?></p>
    <p class="muted">
        Moodle, a cambio, te va a dar <code>Platform ID</code> (issuer), <code>Client ID</code>,
        <code>Public keyset URL</code> (jwks_url) y <code>Access token URL</code> -- pégalos abajo
        junto con el <code>Deployment ID</code> (aparece después de guardar la herramienta en Moodle).
    </p>
    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="id" value="">
        <input type="hidden" name="lti_version" value="1.3">
        <label>Issuer (Platform ID)
            <input type="text" name="issuer" placeholder="https://tu-moodle.cl" required>
        </label>
        <label>Client ID
            <input type="text" name="client_id" required>
        </label>
        <label>Deployment ID
            <input type="text" name="deployment_id" required>
        </label>
        <label>Auth login URL (Moodle: "Authentication request URL")
            <input type="text" name="auth_login_url" required>
        </label>
        <label>Auth token URL (opcional, no se usa en este flujo)
            <input type="text" name="auth_token_url">
        </label>
        <label>JWKS URL (Moodle: "Public keyset URL")
            <input type="text" name="jwks_url" required>
        </label>
        <label>Matricular en este curso a quien entre con esta clave
            <?= $selectCurso(null) ?>
        </label>
        <p class="muted">Mismo criterio que en 1.1: con un curso elegido, la matrícula es inmediata en el primer launch.</p>
        <div class="form-actions-sticky">
            <button type="submit">Guardar</button>
        </div>
    </form>
</div>

<div class="card">
    <strong>Plataformas registradas</strong>
    <div class="table-wrap">
    <table>
        <tr><th>Versión</th><th>Issuer / Consumer key</th><th>Client ID</th><th>Deployment ID</th><th>Matricula en</th><th>Activa</th><th></th></tr>
        <?php foreach ($platforms as $p): ?>
        <?php $defaultCourse = isset($p['default_course_id']) && $p['default_course_id'] !== null
            ? (int) $p['default_course_id'] : null; ?>
        <tr>
            <td><?= htmlspecialchars($p['version']) ?></td>
            <td>
                <span class="mono"><?= htmlspecialchars($p['version'] === '1.1' ? $p['consumer_key'] : $p['issuer']) ?></span>
                <?php if ($p['version'] === '1.1' && (string) $p['shared_secret'] !== ''): ?>
                <details><summary>Ver secreto</summary>
                    <span class="mono"><?= htmlspecialchars((string) $p['shared_secret']) ?></span>
                </details>
                <?php endif; ?>
            </td>
            <td><?= htmlspecialchars($p['client_id']) ?></td>
            <td><?= htmlspecialchars($p['deployment_id']) ?></td>
            <td>
                <form method="post">
                <?= csrf_field() ?>
                    <input type="hidden" name="id" value="<?= (int) $p['id'] ?>">
                    <input type="hidden" name="form_action" value="set_default_course">
                    <?= $selectCurso($defaultCourse) ?>
                    <button type="submit">Guardar</button>
                </form>
            </td>
            <td><?= $p['active'] ? 'sí' : 'no' ?></td>
            <td>
                <?php if ($p['version'] === '1.1'): ?>
                <form method="post" onsubmit="return confirm('Esto invalida el shared secret actual -- hay que actualizarlo en Moodle también. ¿Regenerar?');">
                <?= csrf_field() ?>
                    <input type="hidden" name="id" value="<?= (int) $p['id'] ?>">
                    <input type="hidden" name="lti_version" value="1.1">
                    <button type="submit">Regenerar</button>
                </form>
                <?php endif; ?>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$platforms): ?>
        <tr><td colspan="7" class="muted">Ninguna registrada todavía.</td></tr>
        <?php endif; ?>
    </table>
    </div>
</div>
<?php
admin_footer();
