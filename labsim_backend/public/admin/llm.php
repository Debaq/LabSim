<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/_layout.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/../../src/LlmConfig.php';

// Solo admin completo: acá vive el api_key del proveedor del LLM.
$me = Auth::requireFullAdminSession();

$error = null;
$success = null;

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    Auth::requireCsrf();

    $postAction = (string) ($_POST['form_action'] ?? 'save');

    if ($postAction === 'reset_prompt') {
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
