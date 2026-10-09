<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/Tokens.php';
require_once __DIR__ . '/_layout.php';

/**
 * Sesiones de la app de escritorio (tabla `tokens`). Se buscan por usuario,
 * nombre o final del token, se filtran por rol y por última actividad, y se
 * revocan de a una, las marcadas, o todas las que muestra el filtro (ver
 * Tokens). Revocar corta la sesión al instante: ese equipo vuelve a pedir el
 * login. El panel no usa estos tokens (sesión PHP): revocar los de admin no
 * cierra esta página.
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

    if ($uno !== '') {
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

$tokens = Tokens::listar($pdo, $filtros);
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
                <th>Usuario</th><th>Rol</th><th>Creado</th><th>Última actividad</th><th>Token</th><th></th>
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
                <td class="mono" style="font-size:0.78rem;">&hellip;<?= htmlspecialchars(substr($t['token'], -8)) ?></td>
                <td>
                    <button type="submit" name="revocar_uno" value="<?= htmlspecialchars($t['token']) ?>"
                            class="danger" style="margin-top:0; padding:0.15rem 0.5rem; font-size:0.75rem;"
                            onclick="return confirm('¿Revocar esta sesión? El equipo tendrá que volver a iniciar sesión.');">Revocar</button>
                </td>
            </tr>
            <?php endforeach; ?>
            <?php if (!$tokens): ?>
            <tr><td colspan="7" class="muted"><?= $hayFiltro ? 'Ninguna sesión con este filtro.' : 'Ninguna sesión activa.' ?></td></tr>
            <?php endif; ?>
        </table>
        </div>
    </form>
</div>

<style>
#btn-revocar-marcadas:disabled { opacity: 0.45; cursor: not-allowed; }
</style>
<script>
(function () {
    var todos = document.getElementById('tokens-todos');
    var marcas = Array.prototype.slice.call(document.querySelectorAll('.token-marca'));
    var contador = document.getElementById('tokens-marcados');
    var boton = document.getElementById('btn-revocar-marcadas');
    function actualizar() {
        var n = marcas.filter(function (m) { return m.checked; }).length;
        contador.textContent = n;
        boton.disabled = n === 0;
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
