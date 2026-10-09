<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/Tokens.php';
require_once __DIR__ . '/../../src/Bloqueos.php';
require_once __DIR__ . '/_layout.php';

/**
 * Sesiones de la app de escritorio (tabla `tokens`). Se buscan por usuario,
 * nombre o final del token, se filtran por rol y por última actividad, y se
 * revocan de a una, las marcadas, o todas las que muestra el filtro (ver
 * Tokens). Revocar corta la sesión al instante: ese equipo vuelve a pedir el
 * login. El panel no usa estos tokens (sesión PHP): revocar los de admin no
 * cierra esta página. Cada sesión vence sola a las N horas de iniciada
 * (Tokens::duracionHoras, se cambia acá). También se bloquean cuentas: se
 * cortan sus sesiones y no pueden volver a entrar (ver Bloqueos).
 */

$me = Auth::requireFullAdminSession();
$pdo = Db::get();

$error = null;
$success = null;
$filtros = Tokens::filtros($_SERVER['REQUEST_METHOD'] === 'POST' ? $_POST : $_GET);

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $action = (string) ($_POST['form_action'] ?? '');
    $uno = (string) ($_POST['revocar_uno'] ?? '');
    $revocados = null;

    $bloquearUno = (int) ($_POST['bloquear_usuario'] ?? 0);
    $motivo = (string) ($_POST['motivo'] ?? '');
    if ($bloquearUno > 0 || $action === 'bloquear_seleccionados') {
        // Usuarios a bloquear: el de la fila, o los dueños de las sesiones
        // marcadas (resueltos acá, no confiando en el navegador).
        $ids = [];
        if ($bloquearUno > 0) {
            $ids = [$bloquearUno];
        } else {
            $marcados = is_array($_POST['tokens'] ?? null) ? array_values($_POST['tokens']) : [];
            foreach (Tokens::listar($pdo, Tokens::filtros([])) as $t) {
                if (in_array($t['token'], $marcados, true)) {
                    $ids[] = (int) $t['user_id'];
                }
            }
            $ids = array_values(array_unique($ids));
        }
        $bloqueados = [];
        foreach ($ids as $id) {
            try {
                Bloqueos::bloquear($pdo, $me, $id, $motivo);
                $bloqueados[] = $id;
            } catch (InvalidArgumentException $e) {
                $error = $e->getMessage();
            }
        }
        if ($bloqueados) {
            $success = (count($bloqueados) === 1 ? '1 usuario bloqueado' : count($bloqueados) . ' usuarios bloqueados')
                . ': ya no pueden entrar a la app y sus sesiones se cerraron.';
        } elseif ($error === null) {
            $error = 'No marcaste ninguna sesión.';
        }
    } elseif ((int) ($_POST['desbloquear_usuario'] ?? 0) > 0) {
        try {
            Bloqueos::desbloquear($pdo, $me, (int) $_POST['desbloquear_usuario']);
            $success = 'Usuario desbloqueado: puede volver a entrar.';
        } catch (InvalidArgumentException $e) {
            $error = $e->getMessage();
        }
    } elseif ($action === 'duracion') {
        $horas = Tokens::guardarDuracionHoras((int) ($_POST['horas'] ?? Tokens::DURACION_DEFAULT_HORAS));
        $purgadas = Tokens::purgarVencidas($pdo);
        $success = "Las sesiones duran ahora {$horas} h desde que se inician."
            . ($purgadas ? " Se cerraron {$purgadas} que ya pasaban ese tiempo." : '');
        AdminAudit::log($me, 'token_duracion', ['horas' => $horas, 'purgadas' => $purgadas]);
    } elseif ($uno !== '') {
        $revocados = Tokens::revocar($pdo, [$uno]);
    } elseif ($action === 'revocar_seleccionados') {
        $marcados = $_POST['tokens'] ?? [];
        $revocados = Tokens::revocar($pdo, is_array($marcados) ? array_values($marcados) : []);
        if (!$revocados) {
            $error = 'No marcaste ninguna sesión.';
        }
    } elseif ($action === 'revocar_filtrados') {
        $revocados = Tokens::revocarFiltrados($pdo, $filtros);
        if (!$revocados) {
            $error = 'No hay sesiones que revocar con este filtro.';
        }
    }

    if ($revocados) {
        $total = array_sum($revocados);
        $detalle = [];
        foreach ($revocados as $usuario => $n) {
            $detalle[] = $n > 1 ? "{$usuario} ({$n})" : $usuario;
        }
        $success = ($total === 1 ? '1 sesión revocada' : "{$total} sesiones revocadas")
            . ': ' . implode(', ', $detalle) . '.';
        AdminAudit::log($me, 'token_revoke', [
            'modo' => $uno !== '' ? 'uno' : $action,
            'filtros' => $action === 'revocar_filtrados' ? $filtros : null,
            'por_usuario' => $revocados,
        ]);
    }
}

// Las vencidas se rechazan igual (Auth); acá se borran para no mostrarlas.
Tokens::purgarVencidas($pdo);
$duracion = Tokens::duracionHoras();
$tokens = Tokens::listar($pdo, $filtros);
$bloqueadas = Bloqueos::listar($pdo);
$hayFiltro = $filtros['q'] !== '' || $filtros['rol'] !== '' || $filtros['actividad'] !== '';
$total = (int) $pdo->query('SELECT COUNT(*) FROM tokens')->fetchColumn();

admin_header('Sesiones (tokens)', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <p class="muted">
        Cada fila es una sesión de la app de escritorio (una por equipo/login).
        Revocar corta la sesión de inmediato: ese equipo vuelve a pedir el inicio de sesión.
        Úsalo si se perdió un equipo, una cuenta quedó comprometida o un token se filtró.
        Esta página no usa estos tokens: revocar los de admin no te saca del panel.
    </p>

    <form method="post" style="display:flex; flex-wrap:wrap; align-items:flex-end; gap:0.6rem; margin:0.7rem 0;
                               padding-bottom:0.7rem; border-bottom:1px solid var(--color-border);">
        <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="duracion">
        <label>Duración de cada sesión (horas)
            <input type="number" name="horas" value="<?= $duracion ?>" required
                   min="<?= Tokens::DURACION_MIN_HORAS ?>" max="<?= Tokens::DURACION_MAX_HORAS ?>" style="width:6rem;">
        </label>
        <button type="submit" style="margin-top:0;">Guardar</button>
        <span class="muted" style="flex-basis:100%;">
            Contadas desde que se inicia sesión, se use o no. Al vencer, la app vuelve a pedir el
            inicio de sesión; lo hecho queda en el equipo y se sube al volver a entrar.
            Bajarla cierra al guardar las sesiones que ya pasan ese tiempo.
        </span>
    </form>

    <form method="get" style="display:flex; flex-wrap:wrap; align-items:flex-end; gap:0.6rem; margin:0.7rem 0;">
        <label>Buscar
            <input type="search" name="q" value="<?= htmlspecialchars($filtros['q']) ?>"
                   placeholder="usuario, nombre o final del token" style="min-width:18rem;">
        </label>
        <label>Rol
            <select name="rol">
                <option value="">todos</option>
                <option value="admin"<?= $filtros['rol'] === 'admin' ? ' selected' : '' ?>>admin</option>
                <option value="student"<?= $filtros['rol'] === 'student' ? ' selected' : '' ?>>alumno</option>
            </select>
        </label>
        <label>Última actividad
            <select name="actividad">
                <option value="">cualquiera</option>
                <option value="hoy"<?= $filtros['actividad'] === 'hoy' ? ' selected' : '' ?>>últimas 24 h</option>
                <option value="semana"<?= $filtros['actividad'] === 'semana' ? ' selected' : '' ?>>última semana</option>
                <option value="vieja"<?= $filtros['actividad'] === 'vieja' ? ' selected' : '' ?>>hace más de una semana</option>
            </select>
        </label>
        <button type="submit" style="margin-top:0;">Filtrar</button>
        <?php if ($hayFiltro): ?><a href="tokens.php">Quitar filtros</a><?php endif; ?>
    </form>

    <form method="post" id="form-tokens">
        <?= csrf_field() ?>
        <input type="hidden" name="q" value="<?= htmlspecialchars($filtros['q']) ?>">
        <input type="hidden" name="rol" value="<?= htmlspecialchars($filtros['rol']) ?>">
        <input type="hidden" name="actividad" value="<?= htmlspecialchars($filtros['actividad']) ?>">
        <input type="hidden" name="motivo" id="motivo-bloqueo" value="">

        <div style="display:flex; flex-wrap:wrap; align-items:center; gap:0.6rem; margin:0.5rem 0;">
            <span class="muted">
                <?= count($tokens) ?> <?= $hayFiltro ? 'con este filtro, de ' . $total : 'en total' ?>
                · <span id="tokens-marcados">0</span> marcadas
            </span>
            <button type="submit" name="form_action" value="revocar_seleccionados" class="danger"
                    style="margin-top:0;" id="btn-revocar-marcadas" disabled
                    onclick="return confirm('¿Revocar las sesiones marcadas? Esos equipos tendrán que volver a iniciar sesión.');">
                Revocar marcadas
            </button>
            <button type="submit" name="form_action" value="bloquear_seleccionados" class="danger"
                    style="margin-top:0;" id="btn-bloquear-marcadas" disabled
                    onclick="return pedirMotivo('¿Bloquear a los usuarios de las sesiones marcadas? No podrán volver a entrar a la app hasta que los desbloquees.');">
                Bloquear a sus usuarios
            </button>
            <?php if ($tokens): ?>
            <button type="submit" name="form_action" value="revocar_filtrados" class="danger" style="margin-top:0;"
                    onclick="return confirm('<?= $hayFiltro
                        ? '¿Revocar las ' . count($tokens) . ' sesiones que muestra el filtro?'
                        : '¿Revocar TODAS las sesiones (' . count($tokens) . ')? Todos los equipos, alumnos incluidos, tendrán que volver a iniciar sesión.' ?>');">
                <?= $hayFiltro ? 'Revocar las ' . count($tokens) . ' del filtro' : 'Revocar todas' ?>
            </button>
            <?php endif; ?>
        </div>

        <div class="table-wrap">
        <table>
            <tr>
                <th style="width:2rem;">
                    <input type="checkbox" id="tokens-todos" title="Seleccionar todos" aria-label="Seleccionar todos">
                </th>
                <th>Usuario</th><th>Rol</th><th>Creado</th><th>Última actividad</th><th>Vence</th><th>Token</th><th></th>
            </tr>
            <?php foreach ($tokens as $t): ?>
            <tr>
                <td><input type="checkbox" name="tokens[]" class="token-marca"
                           value="<?= htmlspecialchars($t['token']) ?>"
                           aria-label="Marcar sesión de <?= htmlspecialchars($t['username']) ?>"></td>
                <td><?= htmlspecialchars($t['display_name']) ?> <span class="muted">(<?= htmlspecialchars($t['username']) ?>)</span></td>
                <td><?= htmlspecialchars($t['role'] === 'student' ? 'alumno' : $t['role']) ?></td>
                <td><?= htmlspecialchars($t['created_at']) ?></td>
                <td><?= htmlspecialchars($t['last_seen_at']) ?></td>
                <td><?= htmlspecialchars((string) $t['vence_at']) ?></td>
                <td class="mono" style="font-size:0.78rem;">&hellip;<?= htmlspecialchars(substr($t['token'], -8)) ?></td>
                <td>
                    <button type="submit" name="revocar_uno" value="<?= htmlspecialchars($t['token']) ?>"
                            class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;"
                            onclick="return confirm('¿Revocar esta sesión? El equipo tendrá que volver a iniciar sesión.');">Revocar</button>
                    <?php if ((int) $t['user_id'] !== (int) $me['id']): ?>
                    <button type="submit" name="bloquear_usuario" value="<?= (int) $t['user_id'] ?>"
                            class="secondary" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;"
                            onclick="return pedirMotivo('¿Bloquear a <?= htmlspecialchars(addslashes($t['username']), ENT_QUOTES) ?>? Se cierran todas sus sesiones y no podrá volver a entrar hasta que lo desbloquees.');">Bloquear usuario</button>
                    <?php endif; ?>
                </td>
            </tr>
            <?php endforeach; ?>
            <?php if (!$tokens): ?>
            <tr><td colspan="8" class="muted"><?= $hayFiltro ? 'Ninguna sesión con este filtro.' : 'Ninguna sesión activa.' ?></td></tr>
            <?php endif; ?>
        </table>
        </div>
    </form>
</div>

<div class="card">
    <h2 style="margin-top:0;">Cuentas bloqueadas</h2>
    <p class="muted">No pueden usar la app ni volver a entrar (contraseña o código de Moodle) hasta que las desbloquees.</p>
    <div class="table-wrap">
    <table>
        <tr><th>Usuario</th><th>Rol</th><th>Bloqueada</th><th>Por</th><th>Motivo</th><th></th></tr>
        <?php foreach ($bloqueadas as $b): ?>
        <tr>
            <td><?= htmlspecialchars($b['display_name']) ?> <span class="muted">(<?= htmlspecialchars($b['username']) ?>)</span></td>
            <td><?= htmlspecialchars($b['role'] === 'student' ? 'alumno' : $b['role']) ?></td>
            <td><?= htmlspecialchars($b['bloqueado_at'] ?: '—') ?></td>
            <td><?= htmlspecialchars($b['bloqueado_por'] ?: '—') ?></td>
            <td><?= htmlspecialchars($b['motivo'] ?: '—') ?></td>
            <td>
                <form method="post" class="inline" onsubmit="return confirm('¿Desbloquear? Podrá volver a entrar a la app.');">
                    <?= csrf_field() ?>
                    <button type="submit" name="desbloquear_usuario" value="<?= (int) $b['id'] ?>"
                            class="secondary" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;">Desbloquear</button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$bloqueadas): ?>
        <tr><td colspan="6" class="muted">Ninguna cuenta bloqueada.</td></tr>
        <?php endif; ?>
    </table>
    </div>
</div>

<style>
#btn-bloquear-marcadas:disabled,
#btn-revocar-marcadas:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
<script>
// Bloquear: confirma y pide un motivo opcional (queda en la auditoría).
function pedirMotivo(pregunta) {
    var m = prompt(pregunta + '\n\nMotivo (opcional):', '');
    if (m === null) return false;
    document.getElementById('motivo-bloqueo').value = m;
    return true;
}
(function () {
    var todos = document.getElementById('tokens-todos');
    var marcas = Array.prototype.slice.call(document.querySelectorAll('.token-marca'));
    var contador = document.getElementById('tokens-marcados');
    var boton = document.getElementById('btn-revocar-marcadas');
    var botonBloquear = document.getElementById('btn-bloquear-marcadas');
    function actualizar() {
        var n = marcas.filter(function (m) { return m.checked; }).length;
        contador.textContent = n;
        boton.disabled = n === 0;
        botonBloquear.disabled = n === 0;
        todos.checked = n > 0 && n === marcas.length;
        todos.indeterminate = n > 0 && n < marcas.length;
    }
    todos.addEventListener('change', function () {
        marcas.forEach(function (m) { m.checked = todos.checked; });
        actualizar();
    });
    marcas.forEach(function (m) { m.addEventListener('change', actualizar); });
    actualizar();
})();
</script>
<?php
admin_footer();
