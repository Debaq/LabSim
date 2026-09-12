<?php
/**
 * Pestaña Agenda: lo que viene en este curso. No duplica agenda.php --
 * agendar, reagendar y asignar sigue viviendo allá; acá se ve el mes que
 * viene de un vistazo y se entra a la agenda ya filtrada por el curso.
 *
 * Espera: $courseId, $proximas, $conteoCitas, $ventanaDias.
 */
?>
<div class="card">
    <div class="row row--between" style="margin:0; align-items:center;">
        <strong>Próximos <?= (int) $ventanaDias ?> días</strong>
        <a href="agenda.php?curso=<?= (int) $courseId ?>">Abrir la agenda del curso</a>
    </div>
    <p class="help help--mt">
        <?= (int) $conteoCitas['futuras'] ?> cita(s) de hoy en adelante, <?= (int) $conteoCitas['total'] ?> en total desde que existe el curso.
        Agendar y asignar se hace en la agenda; acá solo se mira.
    </p>
    <?php if (!$proximas): ?>
    <p class="muted">Nada agendado en esta ventana.</p>
    <?php else: ?>
    <div class="table-wrap">
    <table style="margin-top:0.5rem;">
        <tr><th>Fecha</th><th>Hora</th><th>Paciente</th><th>Procedimiento</th><th>Asignada a</th><th>Atenciones</th><th></th></tr>
        <?php foreach ($proximas as $c): ?>
        <tr>
            <td><?= htmlspecialchars((string) $c['fecha']) ?></td>
            <td><?= htmlspecialchars((string) $c['hora']) ?></td>
            <td><?= htmlspecialchars(trim($c['nombre'] . ' ' . $c['apellido'])) ?></td>
            <td><?= htmlspecialchars((string) $c['procedimiento']) ?></td>
            <td>
                <?php if ($c['alumno']): ?><?= htmlspecialchars($c['alumno']) ?>
                <?php elseif ($c['grupo']): ?><span class="tag tag--muted"><?= htmlspecialchars($c['grupo']) ?></span>
                <?php else: ?><span class="help help--xs">todo el curso</span><?php endif; ?>
            </td>
            <td><?= (int) $c['atenciones'] ?></td>
            <td>
                <?php if ($c['case_id']): ?>
                <a class="help help--xs" href="agenda.php?history=<?= urlencode((string) $c['case_id']) ?>">Historial</a>
                <?php endif; ?>
            </td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php endif; ?>
</div>
