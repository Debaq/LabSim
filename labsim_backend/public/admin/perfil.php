<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Users.php';
require_once __DIR__ . '/../../src/Courses.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Perfil de la propia cuenta (docente o admin completo): nombre a mostrar,
 * usuario de login y contraseña.
 *
 * Existe porque el docente entra al portal por LTI (sin contraseña) pero la
 * app de escritorio pide usuario + contraseña (api/admin_login.php) -- hasta
 * ahora la única forma de tener una era que un admin completo se la pusiera
 * desde Usuarios, y el docente ni siquiera veía cuál era su usuario. Acá se
 * lo arma él y lo lee en pantalla.
 *
 * Solo toca la cuenta de quien está logeado ($me['id']): rol y permisos se
 * cambian en users.php, que es de admin completo.
 */

$me = Auth::requireAdminSession();
$pdo = Db::get();

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $action = (string) ($_POST['form_action'] ?? '');

    if ($action === 'account') {
        $displayName = trim((string) ($_POST['display_name'] ?? ''));
        $username = trim((string) ($_POST['username'] ?? ''));

        if ($displayName === '') {
            $error = 'Falta el nombre a mostrar.';
        } elseif ($username !== $me['username'] && !Users::usernameValido($username)) {
            // El formato se exige solo al cambiarlo: una cuenta vieja con un
            // username raro (el "Nombre (1:42)" que arma LTI sin email) no
            // queda obligada a cambiarlo para poder editar el nombre.
            $error = 'El usuario debe tener entre 3 y 64 caracteres, y solo letras, números, punto, arroba, más, '
                . 'guion o guion bajo (se escribe a mano en la app, por eso sin espacios ni tildes).';
        } elseif (Users::usernameTaken($username, (int) $me['id'])) {
            $error = 'Ese usuario ya lo tiene otra cuenta. Elige otro.';
        } else {
            Users::setDisplayName((int) $me['id'], $displayName);
            if ($username !== $me['username']) {
                try {
                    Users::setUsername((int) $me['id'], $username);
                } catch (PDOException $e) {
                    // Entre el chequeo de arriba y este UPDATE alguien pudo
                    // tomar el mismo usuario (o un launch LTI escribirlo). La
                    // UNIQUE es la que corta de verdad; acá solo se traduce a
                    // un mensaje en vez de volcar el SQLSTATE en pantalla.
                    $error = 'Ese usuario lo tomó otra cuenta recién. Elige otro.';
                }
                if ($error === null) {
                    AdminAudit::log($me, 'perfil_username', ['antes' => $me['username'], 'ahora' => $username]);
                }
            }
            if ($error === null) {
                $success = 'Perfil actualizado.';
            }
            $me = Auth::requireAdminSession(); // relee la fila con los datos nuevos
        }
    } elseif ($action === 'password') {
        $actual = (string) ($_POST['password_actual'] ?? '');
        $nueva = (string) ($_POST['password_nueva'] ?? '');
        $repetir = (string) ($_POST['password_repetir'] ?? '');
        $tienePassword = !empty($me['password_hash']);

        if ($tienePassword && !password_verify($actual, (string) $me['password_hash'])) {
            // Pide la actual aunque la sesión ya esté abierta: la sesión del
            // portal se levanta por LTI sin escribir ninguna contraseña, así
            // que un equipo prestado no puede quedar dueño de la cuenta.
            $error = 'La contraseña actual no es correcta.';
        } elseif (strlen($nueva) < 8) {
            $error = 'La contraseña nueva tiene que tener al menos 8 caracteres.';
        } elseif ($nueva !== $repetir) {
            $error = 'Las dos contraseñas nuevas no coinciden.';
        } else {
            Users::setPassword((int) $me['id'], $nueva);
            $success = $tienePassword
                ? 'Contraseña cambiada. Usa la nueva para entrar a la app.'
                : 'Contraseña creada. Ya puedes entrar a la app con tu usuario y esta contraseña.';
            AdminAudit::log($me, 'perfil_password', ['user_id' => (int) $me['id']]);
            $me = Auth::requireAdminSession();
        }
    }
}

$isFullAdmin = (int) $me['permission'] === Auth::PERMISSION_ADMIN;
$tienePassword = !empty($me['password_hash']);
$vieneDeLti = !empty($me['lti_sub']);

// Cursos donde este docente dicta -- solo informativo (se asignan en Cursos).
$misCursos = [];
if (!$isFullAdmin) {
    foreach (Courses::teacherCourseIds((int) $me['id']) as $cid) {
        $curso = Courses::find($cid);
        if ($curso !== null) {
            $misCursos[] = $curso;
        }
    }
}

admin_header('Mi perfil', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<?php if (!$tienePassword): ?>
<p class="error">
    Todavía no tienes contraseña propia: puedes entrar al portal por Moodle, pero <strong>no</strong> a la app de
    escritorio. Créala más abajo.
</p>
<?php endif; ?>

<div class="card">
    <strong>Entrar a la app LabSim</strong>
    <p class="muted">La app de escritorio pide usuario y contraseña, no pasa por Moodle. Estos son los tuyos:</p>
    <p style="font-size:1.1rem; margin:0.4rem 0;">
        Usuario: <code id="mi-usuario" style="font-size:1.15rem; padding:0.2rem 0.5rem;"><?= htmlspecialchars($me['username']) ?></code>
        <button type="button" class="btn btn--ghost btn--sm" onclick="copiarUsuario()">Copiar</button>
        <span id="copiado" class="muted" hidden>copiado</span>
    </p>
    <p class="muted">
        Contraseña: la que definas en "Contraseña" acá abajo (no es la de Moodle: LabSim no la conoce ni puede leerla).
        <?php if ($vieneDeLti): ?>
        Entrar por Moodle sigue funcionando igual; esto es solo para la app.
        <?php endif; ?>
    </p>
</div>

<div class="card">
    <strong>Cuenta</strong>
    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="account">
        <label>Nombre a mostrar
            <input type="text" name="display_name" value="<?= htmlspecialchars($me['display_name']) ?>" required>
        </label>
        <p class="muted">Es el nombre que ven los alumnos y el que aparece en el dashboard y la auditoría.</p>
        <label>Usuario (para entrar a la app)
            <input type="text" name="username" value="<?= htmlspecialchars($me['username']) ?>" required
                   autocapitalize="off" autocorrect="off" spellcheck="false">
        </label>
        <p class="muted">
            Entre 3 y 64 caracteres: letras, números, punto, arroba, más, guion o guion bajo. Sin espacios ni
            tildes, porque se escribe a mano en la app.
            <?php if ($vieneDeLti && (int) ($me['username_locked'] ?? 0) !== 1): ?>
            Tu cuenta vino de Moodle, así que hoy tu usuario es el que manda Moodle y se reescribe en cada entrada:
            apenas lo cambies acá queda fijo y ya no lo pisa.
            <?php endif; ?>
        </p>
        <div><button type="submit">Guardar</button></div>
    </form>
</div>

<div class="card">
    <strong>Contraseña</strong>
    <p class="muted">
        <?= $tienePassword
            ? 'Cámbiala cuando quieras. Se usa en la app de escritorio y en el login del portal (admin/login.php).'
            : 'Créala para poder entrar a la app de escritorio con tu usuario.' ?>
    </p>
    <form method="post" autocomplete="off">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="password">
        <?php if ($tienePassword): ?>
        <label>Contraseña actual
            <input type="password" name="password_actual" required autocomplete="current-password">
        </label>
        <?php endif; ?>
        <label>Contraseña nueva
            <input type="password" name="password_nueva" required minlength="8" autocomplete="new-password">
        </label>
        <label>Repetir contraseña nueva
            <input type="password" name="password_repetir" required minlength="8" autocomplete="new-password">
        </label>
        <p class="muted">Mínimo 8 caracteres.</p>
        <div><button type="submit"><?= $tienePassword ? 'Cambiar contraseña' : 'Crear contraseña' ?></button></div>
    </form>
    <?php if ($tienePassword): ?>
    <p class="muted">
        ¿La olvidaste? Un admin completo la reemplaza desde <?= $isFullAdmin ? '<a href="users.php">Usuarios</a>' : 'Usuarios' ?>
        (no hay forma de recuperarla: se guarda solo el hash).
    </p>
    <?php endif; ?>
</div>

<div class="card">
    <strong>Datos de la cuenta</strong>
    <div class="table-wrap">
    <table>
        <tr><th>Rol</th><td><?= $isFullAdmin ? 'Admin completo' : 'Docente' ?></td></tr>
        <tr><th>Origen</th><td><?= $vieneDeLti ? 'Cuenta creada desde Moodle (LTI)' : 'Cuenta local (usuario/contraseña)' ?></td></tr>
        <tr><th>Alta</th><td><?= htmlspecialchars((string) ($me['created_at'] ?? '—')) ?></td></tr>
        <?php if (!$isFullAdmin): ?>
        <tr>
            <th>Mis cursos</th>
            <td>
                <?php if ($misCursos): ?>
                <?= htmlspecialchars(implode(', ', array_column($misCursos, 'name'))) ?>
                <?php else: ?>
                <span class="muted">Ninguno asignado todavía (lo hace un admin completo desde Cursos).</span>
                <?php endif; ?>
            </td>
        </tr>
        <?php endif; ?>
    </table>
    </div>
    <p class="muted">Rol, permisos y cursos no se cambian desde acá: los administra un admin completo.</p>
</div>

<script>
function copiarUsuario() {
    var texto = document.getElementById('mi-usuario').textContent;
    var aviso = document.getElementById('copiado');
    function avisar() { aviso.hidden = false; setTimeout(function () { aviso.hidden = true; }, 1500); }
    if (navigator.clipboard) {
        navigator.clipboard.writeText(texto).then(avisar);
        return;
    }
    // Sin clipboard API (http sin TLS, navegador viejo): selección manual.
    var rango = document.createRange();
    rango.selectNode(document.getElementById('mi-usuario'));
    window.getSelection().removeAllRanges();
    window.getSelection().addRange(rango);
}
</script>
<?php
admin_footer();
