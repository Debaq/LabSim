<?php
/**
 * Pestaña Personas: el tablero de grupos ES el roster del curso (antes había
 * además una tabla con los mismos alumnos arriba). Cada tarjeta es un alumno
 * y la columna donde está es su grupo; el panel del costado trae a los
 * candidatos, que se matriculan al soltarlos en una columna.
 *
 * Espera: $courseId, $isFullAdmin, $students, $sinGrupo, $groups, $groupedIds,
 *         $enrollable, $origins, $progress, $bulkResults, $teachers,
 *         $teacherOptions.
 */
/** Tarjeta de alumno del tablero: la misma para un matriculado y para un
 * candidato del panel -- lo que cambia es data-enroll y qué controles
 * quedan visibles, así arrastrar un candidato a una columna lo convierte
 * en miembro sin tener que rearmar la tarjeta desde JS. */
$renderCard = static function (array $s, bool $isCandidate) use ($courseId, $progress): void {
    $uid = (int) $s['id'];
    $p = $progress[$uid] ?? ['asignadas' => 0, 'atendidas' => 0, 'ultima' => null];
    $search = mb_strtolower($s['username'] . ' ' . $s['display_name'] . ' ' . (string) ($s['origin'] ?? ''));
    ?>
    <div class="group_card" draggable="true"
         data-user-id="<?= $uid ?>"
         data-enroll="<?= $isCandidate ? '1' : '0' ?>"
         data-origin="<?= htmlspecialchars((string) ($s['origin'] ?? '')) ?>"
         data-search="<?= htmlspecialchars($search) ?>">
        <div class="group_card__head">
            <label class="group_card__pick card-enroll-only" <?= $isCandidate ? '' : 'hidden' ?>>
                <input type="checkbox" form="enroll_form" name="user_ids[]" value="<?= $uid ?>" class="candidate_check">
            </label>
            <a href="student.php?id=<?= $uid ?>" class="group_card__name"><?= htmlspecialchars($s['display_name']) ?></a>
            <form method="post" class="inline card-member-only" <?= $isCandidate ? 'hidden' : '' ?>
                  onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Quitar a ' . $s['username'] . ' del curso? También lo saca de su grupo.'), ENT_QUOTES) ?>);">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="remove_student">
                <input type="hidden" name="course_id" value="<?= $courseId ?>">
                <input type="hidden" name="user_id" value="<?= $uid ?>">
                <button type="submit" class="btn btn--danger btn--xs" title="Quitar del curso">&times;</button>
            </form>
        </div>
        <div class="group_card__meta help help--xs">
            <?= htmlspecialchars($s['username']) ?>
            <span class="card-member-only" <?= $isCandidate ? 'hidden' : '' ?>>
                &nbsp;·&nbsp; <?= $p['asignadas'] ?> cita<?= $p['asignadas'] === 1 ? '' : 's' ?>
                &nbsp;·&nbsp; <?= $p['atendidas'] ?> cerrada<?= $p['atendidas'] === 1 ? '' : 's' ?>
                <?php if ($p['ultima'] !== null): ?>
                &nbsp;·&nbsp; últ. <?= htmlspecialchars(substr((string) $p['ultima'], 0, 10)) ?>
                <?php endif; ?>
            </span>
            <span class="card-enroll-only" <?= $isCandidate ? '' : 'hidden' ?>>
                <?= !empty($s['origin']) ? '&nbsp;·&nbsp; ' . htmlspecialchars((string) $s['origin']) : '' ?>
            </span>
        </div>
    </div>
    <?php
};
?>
<div class="card">
    <div class="row row--between" style="margin:0; align-items:center;">
        <strong>Alumnos y grupos</strong>
        <span class="help help--xs"><?= count($students) ?> matriculado(s) &middot; <?= count($sinGrupo) ?> sin grupo &middot; <?= count($enrollable) ?> candidato(s)</span>
    </div>
    <p class="help help--mt">
        Cada tarjeta es un alumno; arrastrarla a otra columna lo mueve de grupo (pertenece a uno solo a la vez). Los candidatos del panel de la derecha --alumnos activos que todavía no están en este curso-- se matriculan al soltarlos en una columna, o marcándolos y usando el botón, para tandas grandes.
    </p>

    <div class="row" style="margin-top:0.6rem; flex-wrap:wrap; gap:0.6rem;">
        <input type="text" id="people_search" class="input grow" placeholder="Buscar por nombre, usuario u origen...">
        <form method="post" class="row" style="margin:0; gap:0.4rem;">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="create_group">
            <input type="hidden" name="course_id" value="<?= $courseId ?>">
            <input type="text" name="name" class="input input--auto" placeholder="Nuevo grupo" required>
            <button type="submit" class="btn btn--secondary btn--sm">Crear grupo</button>
        </form>
        <?php if ($sinGrupo): ?>
        <form method="post" class="row" style="margin:0; gap:0.4rem;"
              onsubmit="return confirm('Crea los grupos nuevos y reparte entre ellos a los alumnos que hoy están sin grupo. ¿Seguir?');">
        <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="split_groups">
            <input type="hidden" name="course_id" value="<?= $courseId ?>">
            <input type="number" name="n_groups" class="input input--narrow" min="2" max="40" value="4" required title="Cuántos grupos crear">
            <input type="text" name="group_prefix" class="input input--auto" value="Grupo" title="Prefijo del nombre">
            <button type="submit" class="btn btn--secondary btn--sm">Repartir <?= count($sinGrupo) ?> sin grupo</button>
        </form>
        <?php endif; ?>
    </div>

    <p id="board_error" class="error" hidden style="margin-top:0.6rem;"></p>

    <div class="course-people">
        <div id="course_board"
             data-course-id="<?= $courseId ?>"
             data-csrf="<?= htmlspecialchars(Auth::csrfToken()) ?>"
             data-endpoint="group_move.php">
            <div class="pane group_column" data-group-id="">
                <div class="row row--between" style="margin:0; align-items:center;">
                    <strong>Sin grupo (<span class="group_count"><?= count($sinGrupo) ?></span>)</strong>
                </div>
                <div class="group_dropzone">
                    <?php foreach ($sinGrupo as $s) {
                        $renderCard($s, false);
                    } ?>
                </div>
            </div>
            <?php foreach ($groups as $g): ?>
            <div class="pane group_column" data-group-id="<?= (int) $g['id'] ?>">
                <div class="row row--between" style="margin:0; align-items:center;">
                    <strong class="group_title"><?= htmlspecialchars($g['name']) ?> (<span class="group_count"><?= (int) $g['member_count'] ?></span>)</strong>
                    <form method="post" class="inline group_rename" hidden>
                    <?= csrf_field() ?>
                        <input type="hidden" name="form_action" value="rename_group">
                        <input type="hidden" name="course_id" value="<?= $courseId ?>">
                        <input type="hidden" name="group_id" value="<?= (int) $g['id'] ?>">
                        <input type="text" name="name" class="input input--auto" value="<?= htmlspecialchars($g['name']) ?>" required>
                    </form>
                    <span class="row" style="margin:0; gap:0.2rem;">
                        <button type="button" class="btn btn--ghost btn--xs" title="Renombrar grupo" data-rename-toggle>&#9998;</button>
                        <form method="post" class="inline" onsubmit="return confirm(<?= htmlspecialchars(json_encode('¿Eliminar el grupo ' . $g['name'] . '? Sus miembros quedan sin grupo.'), ENT_QUOTES) ?>);">
                        <?= csrf_field() ?>
                            <input type="hidden" name="form_action" value="delete_group">
                            <input type="hidden" name="course_id" value="<?= $courseId ?>">
                            <input type="hidden" name="group_id" value="<?= (int) $g['id'] ?>">
                            <button type="submit" class="btn btn--danger btn--xs" title="Eliminar grupo">&times;</button>
                        </form>
                    </span>
                </div>
                <div class="group_dropzone">
                    <?php foreach ($students as $s): ?>
                    <?php if (($groupedIds[(int) $s['id']] ?? null) !== (int) $g['id']) continue; ?>
                    <?php $renderCard($s, false); ?>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endforeach; ?>
        </div>

        <div class="pane course-candidates">
            <strong>Matricular (<span id="candidate_total"><?= count($enrollable) ?></span>)</strong>
            <p class="help help--xs" style="margin-top:0.3rem;">Arrastra a una columna, o marca y matricula en bloque.</p>
            <?php if ($origins): ?>
            <div style="margin:0.4rem 0;">
                <?php foreach ($origins as $label => $count): ?>
                <button type="button" class="btn btn--secondary btn--xs" style="margin:0 0.3rem 0.3rem 0;"
                        data-origin-select="<?= htmlspecialchars($label) ?>">Todos de "<?= htmlspecialchars($label) ?>" (<?= $count ?>)</button>
                <?php endforeach; ?>
            </div>
            <?php endif; ?>
            <!-- El form queda vacío y las tarjetas afuera: cada tarjeta trae
                 su propio form (quitar del curso) y un form dentro de otro es
                 HTML inválido. Los checkbox se asocian por atributo form=. -->
            <form method="post" id="enroll_form">
            <?= csrf_field() ?>
                <input type="hidden" name="form_action" value="bulk_enroll_selected">
                <input type="hidden" name="course_id" value="<?= $courseId ?>">
            </form>
            <div class="scrollbox" id="candidate_list">
                <?php foreach ($enrollable as $u) {
                    $renderCard($u, true);
                } ?>
                <?php if (!$enrollable): ?>
                <p class="help help--xs">No quedan alumnos activos fuera de este curso.</p>
                <?php endif; ?>
            </div>
            <button type="submit" form="enroll_form" class="btn btn--secondary btn--sm" style="margin-top:0.5rem;">Matricular marcados (<span id="candidate_count">0</span>)</button>

            <details class="section-sep">
                <summary>Alumno nuevo o sin Moodle</summary>
                <form method="post" style="margin-top:0.5rem;">
                <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="add_student">
                    <input type="hidden" name="course_id" value="<?= $courseId ?>">
                    <label>Usuario
                        <input type="text" name="username" required>
                    </label>
                    <label>Nombre completo (si es nuevo)
                        <input type="text" name="display_name" placeholder="Se usa si el usuario no existe todavía">
                    </label>
                    <button type="submit" class="btn btn--secondary btn--sm">Agregar</button>
                </form>
                <p class="help help--xs">Si el usuario no existe, se crea la cuenta con una contraseña temporal que se muestra al agregar.</p>
            </details>

            <details class="section-sep">
                <summary>Pegar una lista</summary>
                <form method="post" style="margin-top:0.5rem;">
                <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="bulk_add_students">
                    <input type="hidden" name="course_id" value="<?= $courseId ?>">
                    <label>Uno por línea: <code>usuario</code>, <code>usuario, nombre</code> o <code>usuario, nombre, clave</code>
                        <textarea name="bulk_students" rows="6" class="textarea" placeholder="jperez&#10;mgonzalez, María González&#10;asilva, Ana Silva, MiClave123"></textarea>
                    </label>
                    <p class="help help--xs">Los que ya existen se matriculan; los que no, se crean con esa clave o con una generada.</p>
                    <button type="submit" class="btn btn--secondary btn--sm">Procesar lista</button>
                </form>
            </details>
        </div>
    </div>

    <?php if ($bulkResults): ?>
    <div class="table-wrap">
    <table style="margin-top:0.8rem;">
        <tr><th>Usuario</th><th>Resultado</th><th>Contraseña</th></tr>
        <?php foreach ($bulkResults as $r): ?>
        <tr>
            <td><?= htmlspecialchars($r['username']) ?></td>
            <td style="color:<?= $r['status'] === 'error' ? 'var(--color-danger)' : 'var(--color-text)' ?>;"><?= htmlspecialchars($r['message']) ?></td>
            <td><?= !empty($r['password']) ? '<code>' . htmlspecialchars($r['password']) . '</code>' : '' ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php endif; ?>
</div>

<?php if ($isFullAdmin): ?>
<datalist id="teachers_datalist">
    <?php foreach ($teacherOptions as $u): ?>
    <option value="<?= htmlspecialchars($u['username']) ?>"><?= htmlspecialchars($u['display_name']) ?></option>
    <?php endforeach; ?>
</datalist>
<div class="card">
    <strong>Docentes (<?= count($teachers) ?>)</strong>
    <div class="table-wrap">
    <table>
        <tr><th>Usuario</th><th>Nombre</th><th></th></tr>
        <?php foreach ($teachers as $t): ?>
        <tr>
            <td><?= htmlspecialchars($t['username']) ?></td>
            <td><?= htmlspecialchars($t['display_name']) ?></td>
            <td>
                <form method="post" class="inline">
                <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="remove_teacher">
                    <input type="hidden" name="course_id" value="<?= $courseId ?>">
                    <input type="hidden" name="user_id" value="<?= $t['id'] ?>">
                    <button type="submit" class="btn btn--danger btn--xs">Quitar</button>
                </form>
            </td>
        </tr>
        <?php endforeach; ?>
        <?php if (!$teachers): ?>
        <tr><td colspan="3" class="muted">Sin docentes asignados todavía.</td></tr>
        <?php endif; ?>
    </table>
    </div>
    <form method="post" class="row" style="margin-top:0.6rem;">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="add_teacher">
        <input type="hidden" name="course_id" value="<?= $courseId ?>">
        <label style="flex:1; margin:0;">Agregar docente (nombre o username)
            <input type="text" name="username" list="teachers_datalist" required>
        </label>
        <button type="submit" class="btn btn--secondary btn--sm">Agregar</button>
    </form>
</div>
<?php endif; ?>

