<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/OtoscopiaBiblioteca.php';

/**
 * Base de otoscopias (ver src/OtoscopiaBiblioteca.php): se suben muchas
 * fotos de una vez y después se pasan una por una para girarlas,
 * encuadrarlas, marcar hacia dónde queda anterior y ponerles tipo. Las
 * acciones van por fetch a otoscopia_biblioteca.php; acá solo se dibuja.
 *
 * Solo el administrador completo: corregir una foto acá reescribe la foto
 * de todos los casos que la usan. Los docentes la usan desde la ficha del
 * caso (botón "Elegir de la base").
 */

$me = Auth::requireFullAdminSession();
OtoscopiaBiblioteca::asegurarTablas();

$filtro = (string) ($_GET['filtro'] ?? '');
if ($filtro !== '' && $filtro !== 'pendientes' && !isset(OtoscopiaBiblioteca::TIPOS[$filtro])) {
    $filtro = '';
}
$conteos = OtoscopiaBiblioteca::conteos();
$fotos = OtoscopiaBiblioteca::lista($filtro);

$editar = null;
$usosEditar = 0;
if (isset($_GET['id'])) {
    try {
        $editar = OtoscopiaBiblioteca::fila((int) $_GET['id']);
        $stmt = Db::get()->prepare('SELECT COUNT(*) FROM otoscopia_biblioteca_uso WHERE biblioteca_id = ?');
        $stmt->execute([(int) $editar['id']]);
        $usosEditar = (int) $stmt->fetchColumn();
        $stmt->closeCursor();
    } catch (Throwable $e) {
        $editar = null;
    }
}

$url = static function (array $q) use ($filtro): string {
    $q = $q + ['filtro' => $filtro];
    $q = array_filter($q, static function ($v) { return $v !== '' && $v !== null; });
    return 'otoscopias.php' . ($q ? '?' . http_build_query($q) : '');
};

admin_add_css('otoscopias.css');
admin_add_js('otoscopias.js');
admin_header('Base de otoscopias', $me);
?>
<p class="help">Cada foto se sube una vez y se usa en cualquier caso, en OD o en OI. Gírala y encuádrala hasta que se vea como debe verse y marca hacia qué lado de la imagen queda adelante: al ponerla en un caso, el sistema la deja tal cual o la da vuelta según el oído (en OD lo anterior va a la derecha de la imagen, en OI a la izquierda). Si después corriges una foto acá, se reescribe en todos los casos que la usan. En la ficha del caso, cada oído tiene "Elegir de la base"; solo aparecen las fotos con lado y tipo marcados.</p>

<div class="card">
    <strong>Subir fotos</strong>
    <p class="help">Puedes elegir muchas a la vez (JPG, PNG o WEBP, hasta 12 MB cada una). Entran sin clasificar y sin girar; al terminar se abre la primera para clasificarla.</p>
    <input type="file" id="oto-subir" accept="image/jpeg,image/png,image/webp" multiple>
    <p id="oto-subir-msg" class="help" hidden></p>
</div>

<?php if ($editar): ?>
<?php
$editarJs = [
    'id' => (int) $editar['id'],
    'ancho' => (int) $editar['ancho'],
    'alto' => (int) $editar['alto'],
    'rotacion' => (float) $editar['rotacion'],
    'centro_x' => (float) $editar['centro_x'],
    'centro_y' => (float) $editar['centro_y'],
    'lado' => (float) $editar['lado'],
    'anterior' => $editar['anterior'],
    'original' => 'otoscopia_biblioteca.php?img=' . (int) $editar['id'] . '&v=original',
    'volver' => $url([]),
    'siguienteUrl' => $url(['id' => '__ID__']),
];
?>
<div class="card oto-editor" id="oto-editor">
    <div class="oto-editor-head">
        <strong>Foto #<?= (int) $editar['id'] ?></strong>
        <?php if ($editar['nombre_archivo'] !== ''): ?><span class="help"><?= htmlspecialchars($editar['nombre_archivo']) ?></span><?php endif; ?>
        <?php if (!OtoscopiaBiblioteca::clasificada($editar)): ?><span class="badge-warn">Sin clasificar</span><?php endif; ?>
        <a href="<?= htmlspecialchars($url([])) ?>" class="oto-cerrar">Cerrar</a>
    </div>
    <div class="oto-editor-cuerpo">
        <div class="oto-lienzo-col">
            <div class="oto-lienzo-wrap">
                <canvas id="oto-lienzo" width="440" height="440"></canvas>
                <span class="oto-marca-adelante izq" hidden>◀ adelante</span>
                <span class="oto-marca-adelante der" hidden>adelante ▶</span>
            </div>
            <p class="help">Arrastra para mover; la rueda del mouse o el control de abajo acercan y alejan.</p>
            <div class="oto-controles">
                <label>Giro <output id="oto-giro-valor">0°</output></label>
                <div class="oto-giro-botones">
                    <button type="button" class="secondary" data-girar="-90">⟲ 90°</button>
                    <button type="button" class="secondary" data-girar="-1">−1°</button>
                    <input type="range" id="oto-giro" min="-180" max="180" step="0.5" value="0">
                    <button type="button" class="secondary" data-girar="1">+1°</button>
                    <button type="button" class="secondary" data-girar="90">⟳ 90°</button>
                </div>
                <label>Acercar
                    <input type="range" id="oto-zoom" min="0" max="1" step="0.001" value="0">
                </label>
                <button type="button" class="secondary" id="oto-restablecer">Volver a la foto sin girar</button>
            </div>
        </div>
        <div class="oto-datos-col">
            <fieldset class="oto-adelante">
                <legend>¿Hacia qué lado de la imagen queda adelante?</legend>
                <?php foreach (OtoscopiaBiblioteca::ANTERIOR as $clave => $rotulo): ?>
                <label class="oto-adelante-op">
                    <input type="radio" name="oto-anterior" value="<?= $clave ?>" <?= $editar['anterior'] === $clave ? 'checked' : '' ?>>
                    <?= $clave === 'izq' ? '◀ ' : '' ?><?= htmlspecialchars(ucfirst($rotulo)) ?><?= $clave === 'der' ? ' ▶' : '' ?>
                </label>
                <?php endforeach; ?>
            </fieldset>
            <label>Tipo
                <select id="oto-tipo">
                    <option value="">-- elegir --</option>
                    <?php foreach (OtoscopiaBiblioteca::TIPOS as $clave => $rotulo): ?>
                    <option value="<?= $clave ?>" <?= $editar['tipo'] === $clave ? 'selected' : '' ?>><?= htmlspecialchars($rotulo) ?></option>
                    <?php endforeach; ?>
                </select>
            </label>
            <label>Notas (solo para el docente)
                <textarea id="oto-notas" rows="2"><?= htmlspecialchars((string) $editar['notas']) ?></textarea>
            </label>
            <div class="oto-vistas">
                <figure>
                    <canvas id="oto-vista-od" width="150" height="150"></canvas>
                    <figcaption><span class="side-tag od">OD</span> así queda</figcaption>
                </figure>
                <figure>
                    <canvas id="oto-vista-oi" width="150" height="150"></canvas>
                    <figcaption><span class="side-tag oi">OI</span> así queda</figcaption>
                </figure>
            </div>
            <p class="help" id="oto-vistas-nota">Marca hacia dónde queda adelante para ver cómo queda en cada oído.</p>
            <?php if ($usosEditar > 0): ?>
            <p class="help">Usada en <?= $usosEditar ?> foto<?= $usosEditar === 1 ? '' : 's' ?> de casos: al guardar se reescriben.</p>
            <?php endif; ?>
            <div class="oto-acciones">
                <button type="button" id="oto-guardar-siguiente">Guardar y siguiente sin clasificar</button>
                <button type="button" class="secondary" id="oto-guardar">Guardar</button>
                <button type="button" class="danger oto-borrar" id="oto-borrar">Sacar de la base</button>
            </div>
            <p id="oto-editor-msg" class="help" hidden></p>
        </div>
    </div>
</div>
<script>window.OTO_EDITAR = <?= json_encode($editarJs, JSON_UNESCAPED_SLASHES) ?>;</script>
<?php endif; ?>

<nav class="oto-filtros">
    <a href="otoscopias.php" <?= $filtro === '' ? 'aria-current="page"' : '' ?>>Todas (<?= $conteos['total'] ?>)</a>
    <a href="otoscopias.php?filtro=pendientes" <?= $filtro === 'pendientes' ? 'aria-current="page"' : '' ?>>Sin clasificar (<?= $conteos['pendientes'] ?>)</a>
    <?php foreach (OtoscopiaBiblioteca::TIPOS as $clave => $rotulo): ?>
    <?php if (!empty($conteos['por_tipo'][$clave])): ?>
    <a href="otoscopias.php?filtro=<?= $clave ?>" <?= $filtro === $clave ? 'aria-current="page"' : '' ?>><?= htmlspecialchars($rotulo) ?> (<?= $conteos['por_tipo'][$clave] ?>)</a>
    <?php endif; ?>
    <?php endforeach; ?>
</nav>

<?php if (!$fotos): ?>
<p class="help">No hay fotos<?= $filtro !== '' ? ' en este filtro' : ' todavía' ?>.</p>
<?php else: ?>
<div class="oto-grilla">
    <?php foreach ($fotos as $f): ?>
    <a class="oto-tarjeta<?= $editar && (int) $editar['id'] === (int) $f['id'] ? ' activa' : '' ?>" href="<?= htmlspecialchars($url(['id' => (int) $f['id']])) ?>">
        <img loading="lazy" src="otoscopia_biblioteca.php?img=<?= (int) $f['id'] ?>&amp;t=<?= urlencode((string) $f['updated_at']) ?>" alt="Otoscopia #<?= (int) $f['id'] ?>">
        <span class="oto-tarjeta-pie">
            #<?= (int) $f['id'] ?> ·
            <?php if (OtoscopiaBiblioteca::clasificada($f)): ?>
            <?= htmlspecialchars(OtoscopiaBiblioteca::TIPOS[$f['tipo']] ?? $f['tipo']) ?>
            · adelante <?= htmlspecialchars(OtoscopiaBiblioteca::ANTERIOR[$f['anterior']] ?? '') ?>
            <?php else: ?>
            <span class="badge-warn">Sin clasificar</span>
            <?php endif; ?>
            <?php if ((int) $f['usos'] > 0): ?>· en <?= (int) $f['usos'] ?> caso<?= (int) $f['usos'] === 1 ? '' : 's' ?><?php endif; ?>
        </span>
    </a>
    <?php endforeach; ?>
</div>
<?php endif; ?>
<?= csrf_field() ?>
<?php
admin_footer();
