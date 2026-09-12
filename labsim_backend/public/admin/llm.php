<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/LlmConfig.php';
require_once __DIR__ . '/../../src/LlmUsage.php';

// Solo admin completo: acá vive el api_key del proveedor del LLM.
$me = Auth::requireFullAdminSession();

$error = null;
$success = null;
// Resultado de "Consultar saldo" -- null mientras nadie lo pida. No se
// consulta en cada carga de la página: es una llamada de red al proveedor y
// el saldo no cambia lo suficiente como para pagarla en cada visita.
$saldo = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();

    $postAction = (string) ($_POST['form_action'] ?? 'save');

    if ($postAction === 'save_prices') {
        // Las tarifas se guardan solas, sin arrastrar el resto del form:
        // son cuatro números que se copian del sitio del proveedor, y
        // hacerlas pasar por el formulario grande obligaría a repetir ahí
        // cada campo de conexión como hidden.
        $current = LlmConfig::get();
        $current['api_key'] = ''; // vacío = no toca la key guardada
        $current['price_cache_hit'] = (float) ($_POST['price_cache_hit'] ?? 0);
        $current['price_cache_miss'] = (float) ($_POST['price_cache_miss'] ?? 0);
        $current['price_output'] = (float) ($_POST['price_output'] ?? 0);
        LlmConfig::save($current);
        $success = 'Tarifas guardadas. El costo del histórico se recalcula con estos valores.';
        AdminAudit::log($me, 'llm_prices_save', [
            'cache_hit' => $current['price_cache_hit'],
            'cache_miss' => $current['price_cache_miss'],
            'output' => $current['price_output'],
        ]);
    } elseif ($postAction === 'check_balance') {
        try {
            $saldo = LlmUsage::saldo(LlmConfig::get());
        } catch (Throwable $e) {
            $error = $e->getMessage();
        }
    } elseif ($postAction === 'reset_prompt') {
        // Guarda todo lo demás tal cual estaba, solo vacía la plantilla ->
        // effectivePrompt() vuelve a caer en LlmConfig::DEFAULT_PROMPT.
        $current = LlmConfig::get();
        $current['system_prompt_template'] = '';
        $current['api_key'] = ''; // vacío = LlmConfig::save() no toca la key ya guardada
        LlmConfig::save($current);
        $success = 'Plantilla restablecida al prompt por defecto.';
        AdminAudit::log($me, 'llm_prompt_reset');
    } elseif ($postAction === 'reset_sala_prompt') {
        $current = LlmConfig::get();
        $current['sala_prompt_template'] = '';
        $current['api_key'] = '';
        LlmConfig::save($current);
        $success = 'Prompt de la consulta con acompañantes restablecido al por defecto.';
        AdminAudit::log($me, 'llm_sala_prompt_reset');
    } elseif ($postAction === 'reset_oirs_prompt') {
        $current = LlmConfig::get();
        $current['oirs_prompt_template'] = '';
        $current['api_key'] = '';
        LlmConfig::save($current);
        $success = 'Prompt del evaluador OIRS restablecido al por defecto.';
        AdminAudit::log($me, 'llm_oirs_prompt_reset');
    } else {
        $model = trim((string) ($_POST['model'] ?? ''));
        $temperature = (float) ($_POST['temperature'] ?? 0.7);

        if ($model === '') {
            $error = 'Falta el nombre del modelo.';
        } elseif ($temperature < 0 || $temperature > 2) {
            $error = 'La temperatura debe estar entre 0 y 2.';
        } else {
            LlmConfig::save($_POST);
            $success = 'Configuración del LLM guardada.';
            AdminAudit::log($me, 'llm_config_save', ['provider' => $_POST['provider'] ?? '', 'model' => $model, 'active' => !empty($_POST['active'])]);
        }
    }
}

$config = LlmConfig::get();
$hasApiKey = $config['api_key'] !== '';
$apiKeyHint = $hasApiKey ? ('••••' . substr($config['api_key'], -4)) : '(sin configurar)';

// --- Consumo de la API (ver LlmUsage.php) -------------------------------
// Todo junto y tolerante a fallas: si la tabla todavía no existe (schema sin
// aplicar) o la consulta muere, el panel de consumo sale vacío pero la
// página de configuración -- que es para lo que la mayoría entra acá -- sigue
// funcionando.
$uso = ['hoy' => null, 'sem' => null, 'mes' => null];
$porTarea = $porModelo = $porCurso = $porDia = [];
$cursosNombre = [];
$primerRegistro = null;
try {
    LlmUsage::purgar();
    $uso['hoy'] = LlmUsage::total(LlmUsage::desde(0), $config);
    $uso['sem'] = LlmUsage::total(LlmUsage::desde(7), $config);
    $uso['mes'] = LlmUsage::total(LlmUsage::desde(30), $config);
    $desdeMes = LlmUsage::desde(30);
    $porTarea = LlmUsage::resumen($desdeMes, 'tarea', $config);
    $porModelo = LlmUsage::resumen($desdeMes, 'model', $config);
    $porCurso = LlmUsage::resumen($desdeMes, 'course_id', $config);
    $porDia = LlmUsage::porDia($desdeMes, $config);
    $primerRegistro = LlmUsage::primerRegistro();
} catch (Throwable $e) {
    $uso = ['hoy' => null, 'sem' => null, 'mes' => null];
}

// Aparte del bloque de arriba: si esta consulta falla (tabla courses de una
// instalación vieja), el consumo ya calculado no se tira -- la tabla por
// curso muestra "Curso #3" en vez del nombre y nada más.
try {
    foreach (Db::get()->query('SELECT id, name FROM courses')->fetchAll() as $c) {
        $cursosNombre[(string) $c['id']] = (string) $c['name'];
    }
} catch (Throwable $e) {
    $cursosNombre = [];
}

$ventanaAhora = LlmUsage::ventana((string) $config['provider']);
$hayTarifas = ((float) $config['price_cache_miss'] > 0 || (float) $config['price_output'] > 0);

/** Tokens con separador de miles, o un guion si no hubo. */
$fmtTok = static function ($n): string {
    return (int) $n > 0 ? number_format((int) $n, 0, ',', '.') : '--';
};
/** Costo en USD. Sin tarifas cargadas no se inventa nada: guion. */
$fmtUsd = static function ($v) use ($hayTarifas): string {
    if (!$hayTarifas) {
        return '--';
    }
    return 'US$ ' . number_format((float) $v, (float) $v < 1 ? 4 : 2, ',', '.');
};
/** Porcentaje del prompt que pegó en cache -- es lo que más mueve la factura. */
$fmtCache = static function (?array $u): string {
    if (!$u) {
        return '--';
    }
    $prompt = (int) $u['cache_hit'] + (int) $u['cache_miss'];
    return $prompt > 0 ? round(100 * $u['cache_hit'] / $prompt) . '%' : '--';
};

admin_header('IA Paciente (LLM)', $me);
?>
<?php if ($error !== null): ?><p class="error"><?= htmlspecialchars($error) ?></p><?php endif; ?>
<?php if ($success !== null): ?><p class="success"><?= htmlspecialchars($success) ?></p><?php endif; ?>

<div class="card">
    <strong>Conexión al proveedor</strong>
    <p class="muted">
        El alumno conversa por texto con el paciente del caso; el backend hace de puente hacia el LLM
        (la app nunca ve el api_key). Compatible con DeepSeek y cualquier otro backend que hable el
        mismo formato de Chat Completions.
    </p>
    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="save">
        <?php /* Las tarifas viajan como hidden en todos los formularios que guardan: sin esto, guardar la conexión o una plantilla las dejaría en 0 y el panel de consumo perdería el costo del histórico. */ ?>
        <input type="hidden" name="price_cache_hit" value="<?= htmlspecialchars((string) $config['price_cache_hit']) ?>">
        <input type="hidden" name="price_cache_miss" value="<?= htmlspecialchars((string) $config['price_cache_miss']) ?>">
        <input type="hidden" name="price_output" value="<?= htmlspecialchars((string) $config['price_output']) ?>">

        <label>Proveedor
            <select name="provider">
                <option value="deepseek" <?= $config['provider'] === 'deepseek' ? 'selected' : '' ?>>DeepSeek</option>
                <option value="openai_compatible" <?= $config['provider'] === 'openai_compatible' ? 'selected' : '' ?>>Otro compatible con OpenAI (base URL propia)</option>
            </select>
        </label>

        <label>API key
            <input type="password" name="api_key" placeholder="Dejar en blanco para no cambiar la actual" autocomplete="off">
        </label>
        <p class="mono" style="margin-top:0.2rem; color:var(--color-muted);">Actual: <?= htmlspecialchars($apiKeyHint) ?></p>

        <label>Base URL de la API
            <input type="text" name="api_base_url" value="<?= htmlspecialchars($config['api_base_url']) ?>" placeholder="https://api.deepseek.com" required>
        </label>

        <label>Modelo
            <input type="text" name="model" value="<?= htmlspecialchars($config['model']) ?>" placeholder="deepseek-chat" required>
        </label>

        <label>Temperatura (0 a 2)
            <input type="number" name="temperature" value="<?= htmlspecialchars((string) $config['temperature']) ?>" min="0" max="2" step="0.1">
        </label>

        <label>Máximo de tokens por respuesta (chat con el paciente)
            <input type="number" name="max_tokens" value="<?= (int) $config['max_tokens'] ?>" min="1" max="4000" step="1">
        </label>

        <label>Modelo del borrador de anamnesis (opcional)
            <input type="text" name="anamnesis_model" value="<?= htmlspecialchars((string) $config['anamnesis_model']) ?>" placeholder="vacío = usa el modelo de arriba">
        </label>
        <p class="help">Las dos tareas piden cosas opuestas. El chat con el paciente se beneficia de un modelo que razona: tiene que sostener un personaje y contestar en contexto. El borrador solo devuelve un JSON de seis campos, y ahí razonar es tiempo, plata y fallas por presupuesto sin mejorar el resultado. Si el chat te anda bien con un modelo de razonamiento, poné acá uno liviano (deepseek-chat) y listo.</p>

        <label>Máximo de tokens del borrador de anamnesis
            <input type="number" name="anamnesis_max_tokens" value="<?= (int) $config['anamnesis_max_tokens'] ?>" min="1" max="16000" step="1">
        </label>
        <p class="help">Va aparte porque son dos tareas distintas: el chat contesta una frase hablada y con 400 sobra, mientras que el borrador devuelve un JSON completo que ya ocupa varios cientos. Si el modelo es de razonamiento (piensa antes de escribir, como deepseek-v4-flash), gasta el presupuesto ANTES de responder y puede irse a varios miles de tokens en una tarea chica. Si falla igual, el borrador reintenta solo una vez con el triple; ante el segundo error subí este número, no el de arriba.</p>


        <label style="display:flex; align-items:center; gap:0.5rem; font-weight:600;">
            <input type="checkbox" name="active" value="1" style="width:auto;" <?= $config['active'] ? 'checked' : '' ?>>
            Habilitar el chat con el paciente en la app
        </label>

        <input type="hidden" name="system_prompt_template" value="<?= htmlspecialchars($config['system_prompt_template']) ?>">
        <input type="hidden" name="oirs_prompt_template" value="<?= htmlspecialchars($config['oirs_prompt_template']) ?>">
        <input type="hidden" name="sala_prompt_template" value="<?= htmlspecialchars($config['sala_prompt_template']) ?>">
        <div class="form-actions-sticky">
            <button type="submit">Guardar</button>
        </div>
    </form>
</div>

<div class="card">
    <strong>Consumo de la API</strong>
    <p class="muted">
        DeepSeek no expone ningún endpoint para consultar el consumo: su API solo dice cuánto saldo
        queda, y el desglose por día o por modelo vive únicamente en su panel web. Así que la cuenta la
        lleva LabSim: cada llamada al LLM anota los tokens que reportó el proveedor, y acá se traducen a
        plata con las tarifas de más abajo. Se guardan tokens y no el costo ya calculado -- si corriges
        una tarifa mal escrita, el histórico entero se recalcula solo.
    </p>
    <?php if ($primerRegistro === null): ?>
    <p class="muted">
        Todavía no hay ninguna llamada anotada. Si el chat ya se está usando, aplica el schema en
        <a href="database.php">Base de datos</a>: la tabla del consumo es nueva.
    </p>
    <?php else: ?>
    <p class="muted">Se anota desde <?= htmlspecialchars(substr($primerRegistro, 0, 16)) ?> (UTC) y se conserva <?= LlmUsage::RETENCION_DIAS ?> días.</p>
    <?php endif; ?>

    <div class="table-wrap">
    <table>
        <tr>
            <th>Período</th><th>Llamadas</th><th>Prompt (cache / nuevo)</th>
            <th>Respuesta</th><th>Total</th><th>% cache</th><th>Costo estimado</th>
        </tr>
        <?php foreach (['hoy' => 'Hoy', 'sem' => 'Últimos 7 días', 'mes' => 'Últimos 30 días'] as $k => $etiqueta): ?>
        <?php $u = $uso[$k]; ?>
        <tr>
            <td><?= $etiqueta ?></td>
            <td><?= $u ? (int) $u['llamadas'] : '--' ?><?= $u && $u['fallidas'] > 0 ? ' <span class="muted">(' . (int) $u['fallidas'] . ' sin respuesta usable)</span>' : '' ?></td>
            <td><?= $u ? $fmtTok($u['cache_hit']) . ' / ' . $fmtTok($u['cache_miss']) : '--' ?></td>
            <td><?= $u ? $fmtTok($u['completion']) : '--' ?><?= $u && $u['razonamiento'] > 0 ? ' <span class="muted">(' . $fmtTok($u['razonamiento']) . ' pensando)</span>' : '' ?></td>
            <td><?= $u ? $fmtTok($u['total']) : '--' ?></td>
            <td><?= $fmtCache($u) ?></td>
            <td><?= $fmtUsd($u ? $u['costo'] : 0) ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <p class="help">
        El corte del día es a medianoche hora de Chile. "Prompt (cache / nuevo)" es lo que decide la
        factura y no se adivina mirando el total: un token que pegó en la cache del proveedor cuesta unas
        50 veces menos que uno que no, así que un % de cache alto es plata, no un detalle técnico. Sube
        solo si el system prompt se manda igual entre llamadas -- por eso conviene no tocar las
        plantillas en mitad de una clase. "Pensando" son los tokens de razonamiento: se cobran como
        respuesta aunque el alumno no los vea nunca.
    </p>

    <?php if ($porTarea): ?>
    <p class="muted" style="margin-top:1rem;"><strong>Últimos 30 días, por tarea</strong></p>
    <div class="table-wrap">
    <table>
        <tr><th>Tarea</th><th>Llamadas</th><th>Tokens</th><th>Costo estimado</th><th>Por llamada</th></tr>
        <?php foreach ($porTarea as $fila): ?>
        <tr>
            <td><?= htmlspecialchars(\LlmUsage::TAREAS[$fila['grupo']] ?? $fila['grupo']) ?></td>
            <td><?= (int) $fila['llamadas'] ?></td>
            <td><?= $fmtTok($fila['total']) ?></td>
            <td><?= $fmtUsd($fila['costo']) ?></td>
            <td><?= $fila['llamadas'] > 0 ? $fmtUsd($fila['costo'] / $fila['llamadas']) : '--' ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <p class="help">El borrador de anamnesis es de lejos lo más caro por llamada: manda el caso entero y, con un modelo de razonamiento, gasta miles de tokens pensando antes de escribir. El chat del paciente cuesta poco por mensaje pero se repite mucho -- mira la columna del total, no la de por llamada.</p>
    <?php endif; ?>

    <?php if ($porModelo): ?>
    <p class="muted" style="margin-top:1rem;"><strong>Últimos 30 días, por modelo</strong></p>
    <div class="table-wrap">
    <table>
        <tr><th>Modelo</th><th>Llamadas</th><th>Tokens</th><th>Costo estimado</th></tr>
        <?php foreach ($porModelo as $fila): ?>
        <tr>
            <td class="mono"><?= htmlspecialchars($fila['grupo'] !== '' ? $fila['grupo'] : '(sin nombre)') ?></td>
            <td><?= (int) $fila['llamadas'] ?></td>
            <td><?= $fmtTok($fila['total']) ?></td>
            <td><?= $fmtUsd($fila['costo']) ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <p class="help">Las tarifas de abajo son una sola para todos los modelos. Si acá aparece más de uno con precios distintos, el costo de la tabla es una aproximación -- toma como buena la fila del modelo que corresponde a las tarifas cargadas.</p>
    <?php endif; ?>

    <?php if (count($porCurso) > 1 || (count($porCurso) === 1 && key($porCurso) !== '')): ?>
    <p class="muted" style="margin-top:1rem;"><strong>Últimos 30 días, por curso</strong></p>
    <div class="table-wrap">
    <table>
        <tr><th>Curso</th><th>Llamadas</th><th>Tokens</th><th>Costo estimado</th></tr>
        <?php foreach ($porCurso as $fila): ?>
        <tr>
            <td><?= htmlspecialchars($cursosNombre[$fila['grupo']] ?? ($fila['grupo'] !== '' ? 'Curso #' . $fila['grupo'] : 'Fuera de una cita')) ?></td>
            <td><?= (int) $fila['llamadas'] ?></td>
            <td><?= $fmtTok($fila['total']) ?></td>
            <td><?= $fmtUsd($fila['costo']) ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <p class="help">"Fuera de una cita" son las pruebas del admin y el borrador de anamnesis: no pasan por una cita agendada, así que no pertenecen a ningún curso.</p>
    <?php endif; ?>

    <?php if ($porDia): ?>
    <p class="muted" style="margin-top:1rem;"><strong>Día por día</strong></p>
    <div class="table-wrap">
    <table>
        <tr><th>Día</th><th>Llamadas</th><th>Tokens</th><th>Costo estimado</th></tr>
        <?php foreach ($porDia as $fila): ?>
        <tr>
            <td><?= htmlspecialchars($fila['dia']) ?></td>
            <td><?= (int) $fila['llamadas'] ?></td>
            <td><?= $fmtTok($fila['total']) ?></td>
            <td><?= $fmtUsd($fila['costo']) ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <?php endif; ?>
</div>

<div class="card">
    <strong>Horario diferido del proveedor</strong>
    <?php if ($config['provider'] === 'deepseek'): ?>
    <p class="muted">
        DeepSeek cobra precio pleno solo de <strong>lunes a viernes, 01:00-04:00 y 06:00-10:00 UTC</strong>;
        el resto del tiempo la tarifa es la mitad. En hora de Chile esa franja cara cae de madrugada
        (21:00-00:00 y 02:00-06:00), así que <strong>todo el horario de clases paga la tarifa rebajada</strong>
        sin que haya que hacer nada. Igual se anota la franja de cada llamada: el día que se agende algo
        de madrugada, o que el proveedor mueva el horario, el histórico tiene que seguir cuadrando.
    </p>
    <p>
        Ahora mismo (<?= htmlspecialchars(gmdate('H:i')) ?> UTC):
        <strong><?= $ventanaAhora === 'peak' ? 'precio pleno' : 'precio rebajado (mitad)' ?></strong>.
    </p>
    <?php else: ?>
    <p class="muted">
        El descuento por horario es propio de DeepSeek. Con un backend compatible con OpenAI se asume
        tarifa plana: toda llamada se anota a precio pleno y se cobra tal cual lo que cargues abajo.
    </p>
    <?php endif; ?>

    <form method="post" style="display:inline;">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="check_balance">
        <button type="submit" class="secondary">Consultar saldo en el proveedor</button>
    </form>
    <p class="help">Lo único que la API de DeepSeek responde sobre plata es cuánto saldo queda -- no hay endpoint de consumo, por eso la tabla de arriba la llevamos nosotros. No se consulta en cada carga de esta página: es una llamada de red y el saldo no cambia tan rápido.</p>

    <?php if ($saldo !== null): ?>
    <div class="table-wrap">
    <table>
        <tr><th>Moneda</th><th>Saldo total</th><th>Regalado</th><th>Recargado</th></tr>
        <?php foreach ($saldo['saldos'] as $b): ?>
        <tr>
            <td><?= htmlspecialchars($b['moneda']) ?></td>
            <td><?= htmlspecialchars($b['total']) ?></td>
            <td><?= htmlspecialchars($b['regalado']) ?></td>
            <td><?= htmlspecialchars($b['recargado']) ?></td>
        </tr>
        <?php endforeach; ?>
    </table>
    </div>
    <p class="<?= $saldo['disponible'] ? 'success' : 'error' ?>">
        <?= $saldo['disponible'] ? 'Hay saldo suficiente para seguir llamando a la API.' : 'Sin saldo: las llamadas al LLM van a fallar.' ?>
    </p>
    <?php endif; ?>
</div>

<div class="card">
    <strong>Tarifas del proveedor</strong>
    <p class="muted">
        En dólares por millón de tokens, <strong>a precio pleno</strong> (en la franja rebajada se aplica
        la mitad sola). Cópialas de la página de precios del proveedor. Si las dejas en cero, el panel de
        arriba sigue contando tokens y solo deja de traducirlos a plata -- no se inventa ningún precio por
        defecto, porque un número inventado en una columna que dice "US$" nadie lo vuelve a revisar.
    </p>
    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="save_prices">

        <label>Entrada, tokens que pegaron en cache (USD / 1M)
            <input type="number" name="price_cache_hit" value="<?= htmlspecialchars((string) $config['price_cache_hit']) ?>" min="0" step="0.001">
        </label>

        <label>Entrada, tokens nuevos (USD / 1M)
            <input type="number" name="price_cache_miss" value="<?= htmlspecialchars((string) $config['price_cache_miss']) ?>" min="0" step="0.001">
        </label>

        <label>Respuesta (USD / 1M)
            <input type="number" name="price_output" value="<?= htmlspecialchars((string) $config['price_output']) ?>" min="0" step="0.001">
        </label>
        <p class="help">Los tokens de razonamiento se cobran como respuesta, no llevan tarifa aparte. La entrada va separada en dos porque el proveedor cobra muchísimo menos por lo que ya tenía en cache, y con un precio único el total no se parece a la factura.</p>

        <div class="form-actions-sticky">
            <button type="submit">Guardar tarifas</button>
        </div>
    </form>
</div>

<div class="card">
    <strong>Prompt por defecto del paciente</strong>
    <p class="muted">
        Plantilla que arma el system prompt para cada conversación. Se completa con los datos del
        paciente y de la anamnesis del caso -- usa estas variables donde correspondan:
    </p>
    <div class="table-wrap">
    <table>
        <tr><th>Variable</th><th>Qué reemplaza</th></tr>
        <?php foreach (\LlmConfig::PLACEHOLDERS as $ph => $desc): ?>
        <tr><td><code><?= htmlspecialchars($ph) ?></code></td><td><?= htmlspecialchars($desc) ?></td></tr>
        <?php endforeach; ?>
    </table>
    </div>
    <p class="muted">
        El paciente nunca debe saber su diagnóstico ni datos técnicos (dB, Hz, nombres de patologías) --
        solo puede describir lo que siente si se lo preguntan (por ejemplo, si escucha un pitido).
    </p>

    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="save">
        <?php /* Las tarifas viajan como hidden en todos los formularios que guardan: sin esto, guardar la conexión o una plantilla las dejaría en 0 y el panel de consumo perdería el costo del histórico. */ ?>
        <input type="hidden" name="price_cache_hit" value="<?= htmlspecialchars((string) $config['price_cache_hit']) ?>">
        <input type="hidden" name="price_cache_miss" value="<?= htmlspecialchars((string) $config['price_cache_miss']) ?>">
        <input type="hidden" name="price_output" value="<?= htmlspecialchars((string) $config['price_output']) ?>">
        <input type="hidden" name="provider" value="<?= htmlspecialchars($config['provider']) ?>">
        <input type="hidden" name="api_base_url" value="<?= htmlspecialchars($config['api_base_url']) ?>">
        <input type="hidden" name="model" value="<?= htmlspecialchars($config['model']) ?>">
        <input type="hidden" name="temperature" value="<?= htmlspecialchars((string) $config['temperature']) ?>">
        <input type="hidden" name="max_tokens" value="<?= (int) $config['max_tokens'] ?>">
        <input type="hidden" name="anamnesis_max_tokens" value="<?= (int) $config['anamnesis_max_tokens'] ?>">
        <input type="hidden" name="anamnesis_model" value="<?= htmlspecialchars((string) $config['anamnesis_model']) ?>">
        <?php if ($config['active']): ?><input type="hidden" name="active" value="1"><?php endif; ?>
        <input type="hidden" name="oirs_prompt_template" value="<?= htmlspecialchars($config['oirs_prompt_template']) ?>">
        <input type="hidden" name="sala_prompt_template" value="<?= htmlspecialchars($config['sala_prompt_template']) ?>">

        <label>Plantilla (precargada con el prompt por defecto -- edítala directamente; "Restablecer" abajo la vuelve a este punto de partida)
            <textarea name="system_prompt_template" rows="16" style="width:100%; padding:0.45rem; border:1px solid var(--color-border-strong); border-radius:var(--radius-md); font-family:var(--font-mono); font-size:0.85rem;"><?= htmlspecialchars(\LlmConfig::effectivePrompt()) ?></textarea>
        </label>
        <div class="form-actions-sticky">
            <button type="submit">Guardar plantilla</button>
        </div>
    </form>

    <form method="post" style="display:inline;" onsubmit="return confirm('¿Restablecer al prompt por defecto? Se pierde la plantilla personalizada.');">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="reset_prompt">
        <button type="submit" class="secondary">Restablecer al prompt por defecto</button>
    </form>
</div>

<div class="card">
    <strong>Prompt de la consulta con acompañantes</strong>
    <p class="muted">
        Cuando el caso tiene acompañantes (pestaña Sala del editor de casos), el modelo interpreta a
        <strong>todos</strong> los presentes con esta plantilla y decide en cada turno quién contesta: si
        el alumno escribe "mamita, ¿su hijo escucha bien?", responde la madre. Un paciente que viene solo
        no pasa por acá -- sigue usando el prompt de más arriba y contestando en texto plano.
    </p>
    <p class="muted">
        La ficha de cada persona (quién es, qué puede contar por su edad, cuánto tiende a contestar por el
        paciente, su versión de los hechos) la arma el código y entra por <code>{{sala}}</code>. Variables
        disponibles:
    </p>
    <div class="table-wrap">
    <table>
        <tr><th>Variable</th><th>Qué reemplaza</th></tr>
        <?php foreach (\LlmConfig::SALA_PLACEHOLDERS as $ph => $desc): ?>
        <tr><td><code><?= htmlspecialchars($ph) ?></code></td><td><?= htmlspecialchars($desc) ?></td></tr>
        <?php endforeach; ?>
    </table>
    </div>
    <p class="muted">
        Debe responder JSON estricto: cada intervención se pinta con la cara y el nombre de quien la dijo,
        así que si editas la plantilla conserva la instrucción de responder solo
        <code>{"turnos": [{"id": ..., "texto": ...}]}</code>. Si el modelo devuelve otra cosa, el turno no
        se pierde -- se muestra completo a nombre de quien lleva la voz cantante.
    </p>

    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="save">
        <?php /* Las tarifas viajan como hidden en todos los formularios que guardan: sin esto, guardar la conexión o una plantilla las dejaría en 0 y el panel de consumo perdería el costo del histórico. */ ?>
        <input type="hidden" name="price_cache_hit" value="<?= htmlspecialchars((string) $config['price_cache_hit']) ?>">
        <input type="hidden" name="price_cache_miss" value="<?= htmlspecialchars((string) $config['price_cache_miss']) ?>">
        <input type="hidden" name="price_output" value="<?= htmlspecialchars((string) $config['price_output']) ?>">
        <input type="hidden" name="provider" value="<?= htmlspecialchars($config['provider']) ?>">
        <input type="hidden" name="api_base_url" value="<?= htmlspecialchars($config['api_base_url']) ?>">
        <input type="hidden" name="model" value="<?= htmlspecialchars($config['model']) ?>">
        <input type="hidden" name="temperature" value="<?= htmlspecialchars((string) $config['temperature']) ?>">
        <input type="hidden" name="max_tokens" value="<?= (int) $config['max_tokens'] ?>">
        <input type="hidden" name="anamnesis_max_tokens" value="<?= (int) $config['anamnesis_max_tokens'] ?>">
        <input type="hidden" name="anamnesis_model" value="<?= htmlspecialchars((string) $config['anamnesis_model']) ?>">
        <?php if ($config['active']): ?><input type="hidden" name="active" value="1"><?php endif; ?>
        <input type="hidden" name="system_prompt_template" value="<?= htmlspecialchars($config['system_prompt_template']) ?>">
        <input type="hidden" name="oirs_prompt_template" value="<?= htmlspecialchars($config['oirs_prompt_template']) ?>">

        <label>Plantilla de la consulta con acompañantes (precargada con el prompt por defecto -- edítala directamente; "Restablecer" abajo la vuelve a este punto de partida)
            <textarea name="sala_prompt_template" rows="16" style="width:100%; padding:0.45rem; border:1px solid var(--color-border-strong); border-radius:var(--radius-md); font-family:var(--font-mono); font-size:0.85rem;"><?= htmlspecialchars(\LlmConfig::effectiveSalaPrompt()) ?></textarea>
        </label>
        <div class="form-actions-sticky">
            <button type="submit">Guardar plantilla</button>
        </div>
    </form>

    <form method="post" style="display:inline;" onsubmit="return confirm('¿Restablecer al prompt por defecto? Se pierde la plantilla personalizada.');">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="reset_sala_prompt">
        <button type="submit" class="secondary">Restablecer al prompt por defecto</button>
    </form>
</div>

<div class="card">
    <strong>Prompt del evaluador OIRS</strong>
    <p class="muted">
        Al cerrar una atención (botón "Atender" -> nota final), esta plantilla decide -- releyendo el chat
        completo del alumno con el paciente -- si corresponde un reclamo, un mérito, o nada, y redacta el
        aviso que le llega al alumno en su Bandeja OIRS (ver Admin -> ficha del alumno para revisarlos ahí
        también). Solo juzga el TRATO recibido, no el conocimiento clínico. Único placeholder disponible:
        <code>{{disposicion}}</code> (<?= htmlspecialchars(\LlmConfig::PLACEHOLDERS['{{disposicion}}']) ?>).
        Debe responder JSON estricto -- si editas la plantilla, conserva la instrucción de responder solo
        <code>{"veredicto": ..., "asunto": ..., "cuerpo": ...}</code> o el aviso dejará de generarse.
    </p>

    <form method="post">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="save">
        <?php /* Las tarifas viajan como hidden en todos los formularios que guardan: sin esto, guardar la conexión o una plantilla las dejaría en 0 y el panel de consumo perdería el costo del histórico. */ ?>
        <input type="hidden" name="price_cache_hit" value="<?= htmlspecialchars((string) $config['price_cache_hit']) ?>">
        <input type="hidden" name="price_cache_miss" value="<?= htmlspecialchars((string) $config['price_cache_miss']) ?>">
        <input type="hidden" name="price_output" value="<?= htmlspecialchars((string) $config['price_output']) ?>">
        <input type="hidden" name="provider" value="<?= htmlspecialchars($config['provider']) ?>">
        <input type="hidden" name="api_base_url" value="<?= htmlspecialchars($config['api_base_url']) ?>">
        <input type="hidden" name="model" value="<?= htmlspecialchars($config['model']) ?>">
        <input type="hidden" name="temperature" value="<?= htmlspecialchars((string) $config['temperature']) ?>">
        <input type="hidden" name="max_tokens" value="<?= (int) $config['max_tokens'] ?>">
        <input type="hidden" name="anamnesis_max_tokens" value="<?= (int) $config['anamnesis_max_tokens'] ?>">
        <input type="hidden" name="anamnesis_model" value="<?= htmlspecialchars((string) $config['anamnesis_model']) ?>">
        <?php if ($config['active']): ?><input type="hidden" name="active" value="1"><?php endif; ?>
        <input type="hidden" name="system_prompt_template" value="<?= htmlspecialchars($config['system_prompt_template']) ?>">
        <input type="hidden" name="sala_prompt_template" value="<?= htmlspecialchars($config['sala_prompt_template']) ?>">

        <label>Plantilla del evaluador (precargada con el prompt por defecto -- edítala directamente; "Restablecer" abajo la vuelve a este punto de partida)
            <textarea name="oirs_prompt_template" rows="16" style="width:100%; padding:0.45rem; border:1px solid var(--color-border-strong); border-radius:var(--radius-md); font-family:var(--font-mono); font-size:0.85rem;"><?= htmlspecialchars(\LlmConfig::effectiveOirsPrompt()) ?></textarea>
        </label>
        <div class="form-actions-sticky">
            <button type="submit">Guardar plantilla</button>
        </div>
    </form>

    <form method="post" style="display:inline;" onsubmit="return confirm('¿Restablecer al prompt por defecto? Se pierde la plantilla personalizada.');">
    <?= csrf_field() ?>
        <input type="hidden" name="form_action" value="reset_oirs_prompt">
        <button type="submit" class="secondary">Restablecer al prompt por defecto</button>
    </form>
</div>
<?php
admin_footer();
