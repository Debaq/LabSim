<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

/**
 * Práctica libre: las carpetas (una por capítulo del libro) y sus pacientes,
 * en el orden en que los ve el alumno en la app. Es la misma para todos los
 * cursos, así que la arma el admin completo. Sacar un paciente o borrar una
 * carpeta los desactiva: los intentos ya hechos se conservan. Ver
 * src/Practica.php y docs/roadmap_practica_libro.md.
 */

$me = Auth::requireFullAdminSession();
// Como patients.php con las carpetas de fichas: la página que se usa para
// armar la práctica crea sus tablas, sin esperar a "Aplicar schema".
Db::migratePracticeFoldersIfNeeded();

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();
    $accion = (string) ($_POST['form_action'] ?? '');
    $folderId = (int) ($_POST['folder_id'] ?? 0);
    $itemId = (int) ($_POST['item_id'] ?? 0);
    $sentido = (int) ($_POST['sentido'] ?? 0);
    switch ($accion) {
        case 'carpeta_crear':
            $nombre = (string) ($_POST['nombre'] ?? '');
            $error = Practica::crearCarpeta($nombre, (int) $me['id']);
            $success = $error === null ? 'Carpeta creada.' : null;
            AdminAudit::log($me, 'practica_carpeta_crear', ['nombre' => trim($nombre)]);
            break;
        case 'carpeta_renombrar':
            $error = Practica::renombrarCarpeta($folderId, (string) ($_POST['nombre'] ?? ''));
            $success = $error === null ? 'Carpeta renombrada.' : null;
            break;
        case 'carpeta_mover':
            Practica::moverCarpeta($folderId, $sentido);
            break;
        case 'carpeta_borrar':
            $error = Practica::borrarCarpeta($folderId);
            $success = $error === null ? 'Carpeta borrada.' : null;
            AdminAudit::log($me, 'practica_carpeta_borrar', ['folder_id' => $folderId]);
            break;
        case 'paciente_agregar':
            $caseId = trim((string) ($_POST['case_id'] ?? ''));
            $error = $caseId === '' ? 'Falta elegir la ficha.' : Practica::agregarPaciente(
                $folderId,
                $caseId,
                (string) ($_POST['procedimiento'] ?? ''),
                ($_POST['show_study_sheet'] ?? '') === '1',
                (int) $me['id']
            );
            $success = $error === null ? 'Paciente agregado al final de la carpeta.' : null;
            AdminAudit::log($me, 'practica_paciente_agregar', ['folder_id' => $folderId, 'case_id' => $caseId]);
            break;
        case 'paciente_mover':
            Practica::moverPaciente($itemId, $sentido);
            break;
        case 'paciente_quitar':
            Practica::quitarPaciente($itemId);
            $success = 'Paciente sacado de la carpeta (sus intentos se conservan).';
            AdminAudit::log($me, 'practica_paciente_quitar', ['item_id' => $itemId]);
            break;
        case 'paciente_ficha':
            Practica::setMostrarFicha($itemId, ($_POST['show_study_sheet'] ?? '') === '1');
            break;
        default:
            $error = 'Acción desconocida.';
    }
}

$listas = Practica::carpetasListas();
$carpetas = Practica::carpetas();

/** Botón de una acción de una fila: un form propio, sin JS. */
function practica_boton(string $accion, array $campos, string $texto, string $clase = 'btn btn--secondary', string $confirmar = ''): void
{
    ?>
    <form method="post" style="display:inline;"<?= $confirmar !== '' ? ' onsubmit="return confirm(' . htmlspecialchars(json_encode($confirmar), ENT_QUOTES) . ');"' : '' ?>>
        <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="<?= htmlspecialchars($accion) ?>">
        <?php foreach ($campos as $k => $v): ?>
        <input type="hidden" name="<?= htmlspecialchars($k) ?>" value="<?= htmlspecialchars((string) $v) ?>">
        <?php endforeach; ?>
        <button type="submit" class="<?= htmlspecialchars($clase) ?>"><?= htmlspecialchars($texto) ?></button>
    </form>
    <?php
}

admin_add_css('course.css');   // .practica-check, como la pestaña que reemplaza
admin_header('Práctica libre', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <strong>Práctica libre</strong>
    <p class="help help--mt">
        Lo que el alumno ve en la app en "Práctica libre": las carpetas en este orden y, dentro de cada una, los
        pacientes numerados. Es la misma para todos los cursos. Cada vez que un alumno abre un paciente queda un
        intento aparte, con su evolución, informes y técnica, que ves en la ficha de cada alumno; los intentos no
        entran a la agenda ni a las estadísticas de los prácticos. Las carpetas vacías no se muestran en la app.
    </p>
    <?php if (!$listas): ?>
    <p class="error">La base todavía no tiene las carpetas de la práctica libre: aplica el schema en Base de datos.</p>
    <?php else: ?>
    <form method="post" class="row" style="margin-top:0.5rem; align-items:flex-end; flex-wrap:wrap;">
        <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="carpeta_crear">
        <label>Carpeta nueva
            <input type="text" name="nombre" required placeholder="Cap. 3 · Membrana y cadena">
        </label>
        <button type="submit" class="btn">Crear carpeta</button>
    </form>
    <?php endif; ?>
</div>

<?php if ($listas && !$carpetas): ?>
<div class="card"><p class="muted">Todavía no hay carpetas.</p></div>
<?php endif; ?>

<?php foreach ($carpetas as $n => $carpeta): ?>
<?php $casos = Practica::casosParaAgregar($carpeta['id']); ?>
<div class="card">
    <div class="row" style="align-items:center; flex-wrap:wrap; gap:0.4rem;">
        <strong><?= htmlspecialchars($carpeta['nombre']) ?></strong>
        <span class="muted">· <?= count($carpeta['items']) ?> paciente(s)</span>
        <span style="flex:1;"></span>
        <?php if ($n > 0) { practica_boton('carpeta_mover', ['folder_id' => $carpeta['id'], 'sentido' => -1], '↑ Subir'); } ?>
        <?php if ($n < count($carpetas) - 1) { practica_boton('carpeta_mover', ['folder_id' => $carpeta['id'], 'sentido' => 1], '↓ Bajar'); } ?>
        <?php if (!$carpeta['items']) { practica_boton('carpeta_borrar', ['folder_id' => $carpeta['id']], 'Borrar', 'btn btn--danger', '¿Borrar esta carpeta?'); } ?>
    </div>
    <details style="margin-top:0.4rem;">
        <summary class="help">Renombrar</summary>
        <form method="post" class="row" style="margin-top:0.4rem; align-items:flex-end;">
            <?= csrf_field() ?>
            <input type="hidden" name="form_action" value="carpeta_renombrar">
            <input type="hidden" name="folder_id" value="<?= (int) $carpeta['id'] ?>">
            <input type="text" name="nombre" required value="<?= htmlspecialchars($carpeta['nombre']) ?>">
            <button type="submit" class="btn btn--secondary">Guardar</button>
        </form>
    </details>

    <?php if ($carpeta['items']): ?>
    <div class="table-wrap">
    <table style="margin-top:0.5rem;">
        <tr><th>N°</th><th>Paciente</th><th>Ficha</th><th>Procedimiento</th><th>Ficha de estudio al cerrar</th><th>Alumnos</th><th>Intentos</th><th></th></tr>
        <?php foreach ($carpeta['items'] as $i => $it): ?>
        <tr>
            <td><?= (int) $it['orden'] ?></td>
            <td>
                <?= htmlspecialchars(trim($it['nombre'] . ' ' . $it['apellido'])) ?: '—' ?>
                <?php if ($it['archived_at'] !== null): ?><span class="badge-warn">· ficha archivada: no se ve en la app</span><?php endif; ?>
            </td>
            <td class="mono"><?= htmlspecialchars((string) $it['case_id']) ?></td>
            <td><?= htmlspecialchars((string) $it['procedimiento']) ?></td>
            <td>
                <form method="post">
                    <?= csrf_field() ?>
                    <input type="hidden" name="form_action" value="paciente_ficha">
                    <input type="hidden" name="item_id" value="<?= (int) $it['id'] ?>">
                    <input type="hidden" name="show_study_sheet" value="0">
                    <label class="help help--xs">
                        <input type="checkbox" name="show_study_sheet" value="1" <?= $it['show_study_sheet'] ? 'checked' : '' ?>
                               onchange="this.form.submit()"> mostrar
                    </label>
                </form>
            </td>
            <td><?= (int) $it['alumnos'] ?></td>
            <td><?= (int) $it['intentos'] ?></td>
            <td style="white-space:nowrap;">
                <?php if ($i > 0) { practica_boton('paciente_mover', ['item_id' => $it['id'], 'sentido' => -1], '↑'); } ?>
                <?php if ($i < count($carpeta['items']) - 1) { practica_boton('paciente_mover', ['item_id' => $it['id'], 'sentido' => 1], '↓'); } ?>
                <?php practica_boton('paciente_quitar', ['item_id' => $it['id']], 'Sacar', 'btn btn--secondary',
                    '¿Sacar este paciente de la carpeta? Los intentos ya hechos se conservan.'); ?>
            </td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php endif; ?>

    <?php if ($casos): ?>
    <form method="post" class="row" style="margin-top:0.5rem; align-items:flex-end; flex-wrap:wrap;">
        <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="paciente_agregar">
        <input type="hidden" name="folder_id" value="<?= (int) $carpeta['id'] ?>">
        <label>Ficha
            <select name="case_id" required>
                <option value="">Elegir…</option>
                <?php foreach ($casos as $c): ?>
                <option value="<?= htmlspecialchars((string) $c['id']) ?>"><?= htmlspecialchars(trim(($c['apellido'] ?? '') . ' ' . ($c['nombre'] ?? '')) ?: 'Sin nombre') ?> · <?= htmlspecialchars((string) $c['id']) ?></option>
                <?php endforeach; ?>
            </select>
        </label>
        <label>Procedimiento
            <input type="text" name="procedimiento" placeholder="Audiometría">
        </label>
        <label class="inline-check practica-check">
            <input type="checkbox" name="show_study_sheet" value="1"> Ficha de estudio al cerrar
        </label>
        <button type="submit" class="btn">Agregar al final</button>
    </form>
    <p class="help help--xs">Solo fichas completas y sin archivar, con el mismo criterio que para agendarlas.</p>
    <?php endif; ?>
</div>
<?php endforeach; ?>
<?php
admin_footer();
