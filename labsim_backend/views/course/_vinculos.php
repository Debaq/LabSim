<?php
/**
 * Pestaña Vínculos: qué cursos de Moodle entran a este curso. Estaba en la
 * lista de cursos, que es el último lugar donde alguien lo busca -- y el
 * vínculo es lo que hace que los alumnos se matriculen solos, así que
 * conviene poder confirmar que está puesto.
 *
 * Espera: $courseId, $vinculos, $clavesLti, $isFullAdmin.
 */
?>
<div class="card">
    <strong>Claves LTI que matriculan en este curso (<?= count($clavesLti) ?>)</strong>
    <p class="help help--mt">
        Una clave asignada a este curso matricula <strong>en el acto</strong>: cualquiera que entre desde Moodle con esa clave queda en el roster en su primer launch, sin vincular nada ni esperar a que un docente entre primero. Se crean y se asignan en <?php if ($isFullAdmin): ?><a href="lti.php">Conexión LTI</a><?php else: ?><strong>Conexión LTI</strong> (lo hace el administrador)<?php endif; ?>, y lo habitual es una clave por curso.
    </p>
    <?php if (!$clavesLti): ?>
    <p class="muted">Ninguna clave apunta a este curso: los alumnos entran por el vínculo del curso de Moodle (abajo) o se matriculan a mano en la pestaña Personas.</p>
    <?php else: ?>
    <div class="table-wrap">
    <table style="margin-top:0.5rem;">
        <tr><th>Clave</th><th>Versión</th></tr>
        <?php foreach ($clavesLti as $k): ?>
        <tr>
            <td class="help help--xs"><code><?= htmlspecialchars((string) ($k['issuer'] !== '' ? $k['issuer'] : $k['consumer_key'])) ?></code></td>
            <td>LTI <?= htmlspecialchars((string) $k['version']) ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php endif; ?>
</div>
<div class="card">
    <strong>Cursos de Moodle vinculados (<?= count($vinculos) ?>)</strong>
    <p class="help help--mt">
        Cada alumno que entra por el launch LTI de un curso vinculado se matricula solo en este curso, sin que haya que agregarlo a mano ni conocer su usuario. El vínculo se crea una sola vez: entrando desde Moodle con tu cuenta de docente y eligiendo este curso en el aviso que aparece.
    </p>
    <?php if (!$vinculos): ?>
    <p class="muted">Sin vínculo -- hoy los alumnos de este curso se matriculan a mano (pestaña Personas).</p>
    <?php else: ?>
    <div class="table-wrap">
    <table style="margin-top:0.5rem;">
        <tr><th>Curso de Moodle</th><th>Plataforma</th><th>Contexto</th><th>Entraron</th><th>Vinculado</th></tr>
        <?php foreach ($vinculos as $v): ?>
        <tr>
            <td><?= htmlspecialchars($v['label'] !== null && $v['label'] !== '' ? $v['label'] : '(sin nombre informado)') ?></td>
            <td class="help help--xs"><?= htmlspecialchars((string) ($v['issuer'] !== '' ? $v['issuer'] : $v['consumer_key'])) ?> · LTI <?= htmlspecialchars((string) $v['version']) ?></td>
            <td class="help help--xs"><code><?= htmlspecialchars((string) $v['context_id']) ?></code></td>
            <td><?= (int) $v['vistos'] ?> usuario(s)</td>
            <td class="help help--xs"><?= htmlspecialchars(substr((string) $v['created_at'], 0, 10)) ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php endif; ?>
</div>
