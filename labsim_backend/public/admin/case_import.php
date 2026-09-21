<?php

declare(strict_types=1);

/**
 * Importar casos pegando un JSON.
 *
 * Para armar una tanda entera de una vez: la práctica de mañana son ocho
 * recién nacidos y hacerlos a mano en el formulario, uno por uno, no entra
 * en el rato que hay antes de la clase.
 *
 * El JSON es una LISTA de casos, y cada caso tiene exactamente los campos
 * del formulario de creación (los `name=` de case_create.php). No es un
 * formato nuevo: se arma el POST que el formulario habría mandado y se pasa
 * por el MISMO camino --CaseForm::fromPost-- así que valida igual, proyecta
 * igual y guarda igual. Un caso importado es indistinguible de uno hecho a
 * mano, y el día que cambie una regla del formulario cambia para los dos.
 *
 * Lo mínimo por caso: edad, nombre1, apellido1. Todo lo demás cae en los
 * defaults del formulario.
 */
require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/CaseForm.php';
require_once __DIR__ . '/../../src/CaseReview.php';
require_once __DIR__ . '/../../src/CaseBuilder.php';
require_once __DIR__ . '/../../src/Patients.php';
require_once __DIR__ . '/../../src/AdminAudit.php';
require_once __DIR__ . '/_layout.php';

$me = Auth::requireAdminSession();
$pdo = Db::get();

$resultados = [];
$errorGeneral = '';
$json = '';

if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $json = (string) ($_POST['casos'] ?? '');
    $casos = json_decode($json, true);
    if (!is_array($casos)) {
        $errorGeneral = 'El JSON no se puede leer: ' . json_last_error_msg();
    } elseif ($casos !== [] && !isset($casos[0])) {
        // Un solo caso suelto también vale: se envuelve.
        $casos = [$casos];
    }

    if ($errorGeneral === '' && $casos === []) {
        $errorGeneral = 'La lista viene vacía.';
    }

    foreach (is_array($casos) ? $casos : [] as $i => $post) {
        $etiqueta = '#' . ($i + 1);
        if (!is_array($post)) {
            $resultados[] = ['ok' => false, 'que' => $etiqueta, 'detalle' => 'No es un objeto.'];
            continue;
        }
        $etiqueta .= ' ' . trim((string) ($post['nombre1'] ?? '') . ' ' . (string) ($post['apellido1'] ?? ''));

        // Los mismos defaults que hacen falta para que un POST mínimo pase:
        // la acumetría se calcula sola y el perfil se da por revisado (quien
        // importa ya decidió lo que está importando).
        $post = array_merge([
            'acumetria_auto' => '1',
            'perfil_confirmar' => '1',
        ], $post);
        // Las once fichas, dadas por revisadas: el importador no es el lugar
        // para el checklist, que existe para el que arma el caso a mano.
        $post['revisado'] = array_fill_keys(array_keys(CaseReview::revisables()), '1');

        try {
            $form = CaseForm::fromPost($post, $pdo, $me, null, false);
        } catch (Throwable $e) {
            $resultados[] = ['ok' => false, 'que' => $etiqueta, 'detalle' => $e->getMessage()];
            continue;
        }
        if (!$form->ok()) {
            $resultados[] = ['ok' => false, 'que' => $etiqueta,
                             'detalle' => (string) $form->error];
            continue;
        }

        // Alta: el mismo bloque que case_create.php para un caso nuevo.
        $data = $form->data;

        // Umbral del ABR: si el JSON no lo trae, se toma el que proyectó el
        // perfil en vez del default del formulario (20). Son dB nHL, no los
        // dB HL del audiograma, y confundirlos es el error fácil de este
        // importador: un oído con 35 dB HL de conductiva tiene el ABR en 55
        // nHL, no en 35. Con el campo vacío, el caso queda coherente solo.
        foreach (['od' => 'OD', 'oi' => 'OI'] as $ladoForm => $lado) {
            if (isset($post['abr'][$ladoForm]['umbral'])
                && $post['abr'][$ladoForm]['umbral'] !== '') {
                continue;
            }
            $proyectado = $data['ABR'][$lado]['umbral_por_estimulo']['click'] ?? null;
            if ($proyectado !== null) {
                $data['ABR'][$lado]['umbral'] = (int) $proyectado;
            }
        }
        $nombre = trim($form->nombre1 . ' ' . trim((string) ($post['nombre2'] ?? '')));
        $apellido = trim($form->apellido1 . ' ' . trim((string) ($post['apellido2'] ?? '')));
        $rut = trim((string) ($post['rut'] ?? '')) !== ''
            ? trim((string) $post['rut'])
            : (string) CaseBuilder::rutFromAge($form->age);
        $fechaNacIso = trim((string) ($post['fecha_nac'] ?? ''));
        $fechaNac = $fechaNacIso !== ''
            ? date('d-m-Y', strtotime($fechaNacIso))
            : CaseBuilder::randomFechaNacForAge($form->age);

        $data['paciente_snapshot'] = [
            'nombre' => $nombre,
            'apellido' => $apellido,
            'rut' => $rut,
            'fecha_nac' => $fechaNac,
            'procedimiento' => 'Audiometría',
        ];
        $historia = trim((string) ($post['historia_clinica'] ?? ''));
        $data['historia_clinica'] = $historia;

        $patientId = Patients::upsertByRut($pdo, $rut, $nombre, $apellido, $fechaNac);
        Patients::updateHistoriaClinica($pdo, $patientId, $historia, (int) $me['id']);
        Patients::updateComentarioDocente($pdo, $patientId,
            trim((string) ($post['comentario_docente'] ?? '')));

        $pdo->prepare(
            "INSERT INTO cases (id, data, updated_at, patient_id, created_at, created_by, updated_by)
                 VALUES (?, ?, CURRENT_TIMESTAMP, ?, CURRENT_TIMESTAMP, ?, ?)
             ON CONFLICT(id) DO UPDATE SET data = excluded.data, updated_at = CURRENT_TIMESTAMP,
                 patient_id = excluded.patient_id, updated_by = excluded.updated_by"
        )->execute([$form->caseId, json_encode($data, JSON_UNESCAPED_UNICODE),
                    $patientId, (int) $me['id'], (int) $me['id']]);
        AdminAudit::log($me, 'case_import', ['case_id' => $form->caseId,
                                             'nombre' => $nombre, 'apellido' => $apellido]);

        $resultados[] = ['ok' => true, 'que' => $etiqueta, 'detalle' => $form->caseId];
    }
}

admin_header('Importar casos', $me);
?>
<div class="card">
    <strong>Importar casos desde JSON</strong>
    <p class="help">Una lista de casos. Cada uno lleva los mismos campos del formulario de creación, así que se guardan por el mismo camino: validan, proyectan y quedan igual que si los hubieras hecho a mano. Lo mínimo es <code>age</code>, <code>nombre1</code> y <code>apellido1</code>; el resto cae en los defaults.</p>
    <p class="help"><strong>Ojo con las unidades:</strong> el audiograma va en <strong>dB HL</strong> y el umbral del ABR en <strong>dB nHL</strong>, que no son lo mismo -- un oído con 35 dB HL de conductiva tiene el ABR en 55 nHL. Lo más seguro es <strong>no mandar</strong> <code>abr[od][umbral]</code>: si viene vacío, se toma el que proyecta el perfil desde el audiograma.</p>
    <p class="help"><strong>Ojo con el tipo:</strong> lo posteado le gana a la proyección, así que el tipo de cada oído se declara --<code>abr[od][type]</code> y <code>eoas[od][type]</code>, con <code>normal</code>, <code>transmission</code>, <code>coclear</code> o <code>neural</code>--. Si no viene, el caso queda "normal" aunque el audiograma diga otra cosa. Los módulos en automático van en <code>perfil[auto][abr]</code>, <code>[eoas]</code>, <code>[reflex]</code>, <code>[recruit]</code> y <code>[logo]</code>; el patrón retrococlear, en <code>abr[od][neural]</code>.</p>
    <p class="help">Para un recién nacido: <code>age</code> en 0 y <code>edad_valor</code>/<code>edad_unidad</code> con la edad exacta. El audiograma va como <code>"aerea": {"od": {"0": 10, "1": 10, ...}, "oi": {...}}</code> y lo mismo <code>osea</code>, con una entrada por frecuencia en este orden: <?= implode(', ', CaseBuilder::FREQUENCIES) ?> Hz. El perfil por oído va en <code>perfil[od][cce_pct]</code> y <code>perfil[od][retro][...]</code>.</p>

    <?php if ($errorGeneral !== ''): ?>
    <p class="help" style="color:#b71c1c;"><strong><?= htmlspecialchars($errorGeneral) ?></strong></p>
    <?php endif; ?>

    <?php if ($resultados !== []): ?>
    <table>
        <thead><tr><th>Caso</th><th>Resultado</th></tr></thead>
        <tbody>
        <?php foreach ($resultados as $r): ?>
            <tr>
                <td><?= htmlspecialchars($r['que']) ?></td>
                <td style="color:<?= $r['ok'] ? '#1b5e20' : '#b71c1c' ?>;">
                    <?= $r['ok'] ? 'creado · ' : 'no se pudo: ' ?><?= htmlspecialchars($r['detalle']) ?>
                </td>
            </tr>
        <?php endforeach; ?>
        </tbody>
    </table>
    <p class="help">Los creados ya están en <a href="patients.php">Pacientes</a>, listos para agendar.</p>
    <?php endif; ?>

    <form method="post">
        <label>JSON
            <textarea name="casos" rows="18" style="width:100%; font-family:monospace; font-size:12px;"><?= htmlspecialchars($json) ?></textarea>
        </label>
        <button type="submit">Importar</button>
    </form>
</div>
<?php
admin_footer();
