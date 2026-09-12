<?php
/**
 * Pestaña Vínculos: qué cursos de Moodle entran a este curso. Estaba en la
 * lista de cursos, que es el último lugar donde alguien lo busca -- y el
 * vínculo es lo que hace que los alumnos se matriculen solos, así que
 * conviene poder confirmar que está puesto.
 *
 * Espera: $courseId, $vinculos.
 */
?>
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
