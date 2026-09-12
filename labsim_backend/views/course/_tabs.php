<?php
/**
 * Barra de pestañas de la página de curso. Cada pestaña es su propia carga
 * (enlace, no JS): así el docente puede tener abierta la agenda de un curso
 * y las personas de otro, y el back del navegador hace lo que se espera.
 *
 * Espera: $courseTabs (clave => ['label', 'count'?]), $activeTab, $courseId.
 */
?>
<nav class="tabs" aria-label="Secciones del curso">
    <?php foreach ($courseTabs as $key => $tab): ?>
    <a class="tab-btn<?= $key === $activeTab ? ' active' : '' ?>"
       href="courses.php?id=<?= (int) $courseId ?>&amp;tab=<?= htmlspecialchars($key) ?>"
       <?= $key === $activeTab ? 'aria-current="page"' : '' ?>><?= htmlspecialchars($tab['label']) ?><?php if (isset($tab['count'])): ?> <span class="tab-count"><?= (int) $tab['count'] ?></span><?php endif; ?></a>
    <?php endforeach; ?>
</nav>
