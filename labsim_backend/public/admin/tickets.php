<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/Tickets.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Reportes de problemas mandados desde la app (ver Tickets). Lista, detalle
 * con la cola del registro y descarga del registro completo. Al usuario no
 * se le avisa nada: estado y nota son para ordenar el trabajo de acá.
 */

$me = Auth::requireFullAdminSession();

$id = (int) ($_GET['id'] ?? 0);

if ($id > 0 && isset($_GET['descargar'])) {
    $texto = Tickets::leerLog($id);
    if ($texto === null) {
        http_response_code(404);
        exit('Este ticket no tiene registro.');
    }
    header('Content-Type: text/plain; charset=utf-8');
    header('Content-Disposition: attachment; filename="labsim_ticket_' . $id . '.log"');
    echo $texto;
    exit;
}

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST' && $id > 0) {
    Auth::requireCsrf();
    $estado = (string) ($_POST['estado'] ?? '');
    $nota = (string) ($_POST['nota'] ?? '');
    try {
        Tickets::actualizar($id, $estado, $nota);
        AdminAudit::log($me, 'ticket_update', ['ticket_id' => $id, 'estado' => $estado]);
        $success = 'Ticket actualizado.';
    } catch (InvalidArgumentException $e) {
        $error = $e->getMessage();
    }
}

$fecha = static function (string $utc): string {
    return Clock::fromUtc($utc)->format('Y-m-d H:i');
};
$quien = static function (array $t): string {
    if ($t['username'] === null) {
        return 'usuario borrado';
    }
    return (string) $t['display_name'] . ' (' . (string) $t['username'] . ')';
};

if ($id > 0) {
    $t = Tickets::obtener($id);
    if ($t === null) {
        http_response_code(404);
        exit('Ticket no encontrado.');
    }
    $detalle = json_decode((string) $t['detalle'], true) ?: [];
    $log = (int) $t['log_bytes'] > 0 ? Tickets::leerLog($id) : null;

    admin_header("Ticket #{$id}", $me);
    ?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<p><a href="tickets.php">← Todos los tickets</a></p>

<div class="card">
    <h2>Qué pasó</h2>
    <?php if (trim((string) $t['descripcion']) !== ''): ?>
        <p style="white-space:pre-wrap;"><?= htmlspecialchars((string) $t['descripcion']) ?></p>
    <?php else: ?>
        <p class="muted">Sin descripción: solo mandó el registro.</p>
    <?php endif; ?>
    <p class="muted">
        <?= htmlspecialchars($fecha((string) $t['created_at'])) ?> · <?= htmlspecialchars($quien($t)) ?>
    </p>
</div>

<div class="card">
    <h2>Equipo</h2>
    <div class="table-wrap">
    <table>
        <tr><th>Equipo</th><td><?= htmlspecialchars((string) $t['equipo_nombre']) ?></td></tr>
        <tr><th>Sistema</th><td><?= htmlspecialchars((string) $t['so']) ?></td></tr>
        <tr><th>Versión de la app</th><td class="mono"><?= htmlspecialchars((string) $t['version']) ?><?= (int) $t['empaquetada'] ? '' : ' <span class="tag tag--muted">desarrollo</span>' ?></td></tr>
        <tr><th>Id del equipo</th><td class="mono"><?= htmlspecialchars((string) $t['equipo_id']) ?></td></tr>
        <?php foreach ($detalle as $k => $v): ?>
        <tr><th><?= htmlspecialchars(str_replace('_', ' ', (string) $k)) ?></th><td><?= htmlspecialchars((string) $v) ?></td></tr>
        <?php endforeach; ?>
    </table>
    </div>
</div>

<div class="card">
    <h2>Registro de la app</h2>
    <?php if ($log === null): ?>
        <p class="muted">No vino registro<?= (int) $t['log_bytes'] > 0 ? ' (o no se pudo leer)' : '' ?>.</p>
    <?php else: ?>
        <p>
            <a href="tickets.php?id=<?= $id ?>&amp;descargar=1">Descargar el registro completo</a>
            <span class="muted">(<?= number_format(strlen($log) / 1024, 0, ',', '.') ?> KB)</span>
        </p>
        <p class="muted">Últimas 300 líneas:</p>
        <pre class="mono" style="max-height:32rem;overflow:auto;font-size:0.78rem;white-space:pre-wrap;"><?= htmlspecialchars(Tickets::cola($log, 300)) ?></pre>
    <?php endif; ?>
</div>

<div class="card">
    <h2>Seguimiento</h2>
    <p class="muted">Solo para el equipo de LabSim: a quien lo envió no le llega nada.</p>
    <form method="post">
        <?= csrf_field() ?>
        <label>Estado
            <select name="estado">
                <?php foreach (Tickets::ESTADOS as $e): ?>
                <option value="<?= $e ?>"<?= $t['estado'] === $e ? ' selected' : '' ?>><?= $e ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Nota (p. ej. el issue donde quedó)
            <textarea name="nota" rows="3"><?= htmlspecialchars((string) $t['nota']) ?></textarea>
        </label>
        <button type="submit">Guardar</button>
    </form>
</div>
<?php
    admin_footer();
    exit;
}

$filtro = (string) ($_GET['estado'] ?? 'abierto');
$tickets = Tickets::listar(in_array($filtro, Tickets::ESTADOS, true) ? $filtro : null);

admin_header('Tickets de la app', $me);
?>
<div class="card">
    <p class="muted">
        Reportes enviados desde la app (Configuración → Reportar un problema), con el registro del
        equipo. A quien lo envía no se le contesta: sirven para abrir issues.
    </p>
    <p>
        Mostrar:
        <a href="tickets.php?estado=abierto"<?= $filtro === 'abierto' ? ' aria-current="page"' : '' ?>>abiertos</a> ·
        <a href="tickets.php?estado=cerrado"<?= $filtro === 'cerrado' ? ' aria-current="page"' : '' ?>>cerrados</a> ·
        <a href="tickets.php?estado=todos"<?= $filtro === 'todos' ? ' aria-current="page"' : '' ?>>todos</a>
    </p>
    <div class="table-wrap">
    <table>
        <tr><th>#</th><th>Fecha</th><th>Usuario</th><th>Equipo</th><th>Versión</th><th>Qué pasó</th><th>Estado</th></tr>
        <?php foreach ($tickets as $t): ?>
        <?php $desc = trim((string) $t['descripcion']); ?>
        <tr>
            <td><a href="tickets.php?id=<?= (int) $t['id'] ?>">#<?= (int) $t['id'] ?></a></td>
            <td><?= htmlspecialchars($fecha((string) $t['created_at'])) ?></td>
            <td><?= htmlspecialchars($quien($t)) ?></td>
            <td><?= htmlspecialchars((string) $t['equipo_nombre']) ?> <span class="muted"><?= htmlspecialchars((string) $t['so']) ?></span></td>
            <td class="mono"><?= htmlspecialchars((string) $t['version']) ?></td>
            <td>
                <?php if ($desc === ''): ?>
                    <span class="muted">solo registro</span>
                <?php else: ?>
                    <?= htmlspecialchars(function_exists('mb_strimwidth') ? mb_strimwidth($desc, 0, 90, '…') : substr($desc, 0, 90)) ?>
                <?php endif; ?>
            </td>
            <td><span class="tag <?= $t['estado'] === 'abierto' ? 'tag--warn' : 'tag--muted' ?>"><?= htmlspecialchars((string) $t['estado']) ?></span></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$tickets): ?>
        <tr><td colspan="7" class="muted">No hay tickets.</td></tr>
        <?php endif; ?>
    </table>
    </div>
</div>
<?php
admin_footer();
