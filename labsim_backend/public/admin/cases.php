<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';

$me = Auth::requireAdminSession();

// LEFT JOIN con appointments: un caso clínico no guarda el nombre del
// paciente (eso vive en la cita) -- así el admin puede confirmar que un
// caso que creó desde la app efectivamente llegó al servidor Y quedó
// enganchado a una cita, que es justo lo que no se podía ver antes.
$cases = Db::get()->query(
    "SELECT c.id, c.updated_at,
            GROUP_CONCAT(TRIM(a.nombre || ' ' || a.apellido), ', ') AS pacientes
     FROM cases c
     LEFT JOIN appointments a ON a.case_id = c.id
     GROUP BY c.id
     ORDER BY c.updated_at DESC"
)->fetchAll();

admin_header('Casos clínicos', $me);
?>
<div class="card">
    <strong>Casos guardados (<?= count($cases) ?>)</strong>
    <p style="font-size:0.85rem; color:#555;">
        Un caso sin paciente en la columna "En cita" se guardó pero no quedó enganchado a
        ninguna cita de la agenda todavía (o la cita que lo referenciaba se borró).
    </p>
    <table>
        <tr><th>ID</th><th>En cita</th><th>Actualizado</th></tr>
        <?php foreach ($cases as $c): ?>
        <tr>
            <td><?= htmlspecialchars($c['id']) ?></td>
            <td><?= $c['pacientes'] ? htmlspecialchars($c['pacientes']) : '<span style="color:#a33;">— sin cita —</span>' ?></td>
            <td><?= htmlspecialchars($c['updated_at']) ?></td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$cases): ?>
        <tr><td colspan="3" style="color:#888;">Ningún caso guardado todavía.</td></tr>
        <?php endif; ?>
    </table>
</div>
<?php
admin_footer();
