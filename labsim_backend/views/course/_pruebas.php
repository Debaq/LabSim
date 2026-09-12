<?php
/**
 * Pestaña Pruebas: el alumno demo del curso.
 *
 * Espera: $courseId, $demoStudent.
 */
?>
<div class="card">
    <details>
    <summary><strong>Área de pruebas</strong></summary>
    <p class="help help--mt">
        Un alumno más del curso para probar la app de punta a punta (agendarle pacientes, atender, etc.) sin tocar datos de alumnos reales. Invisible para los alumnos -- solo docente/admin lo ven acá. Entra con código de 6 dígitos, igual que un alumno LTI -- sin usuario ni contraseña que gestionar.
    </p>
    <div class="row" style="margin-top:0.5rem;">
        <form method="post">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="generate_demo_code">
            <input type="hidden" name="course_id" value="<?= $courseId ?>">
            <button type="submit" class="btn btn--secondary">Generar código de acceso</button>
        </form>
        <?php if ($demoStudent !== null): ?>
        <form method="post" onsubmit="return confirm('¿Borrar todas las citas/atenciones/chats de prueba del demo? La cuenta queda igual.');">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="clean_demo">
            <input type="hidden" name="course_id" value="<?= $courseId ?>">
            <button type="submit" class="btn btn--danger">Limpiar datos de prueba</button>
        </form>
        <?php endif; ?>
    </div>
    </details>
</div>
