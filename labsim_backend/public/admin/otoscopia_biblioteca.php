<?php

declare(strict_types=1);

require_once __DIR__ . '/../bootstrap.php';
require_once __DIR__ . '/../../src/OtoscopiaBiblioteca.php';
require_once __DIR__ . '/../../src/AdminAudit.php';

/**
 * Base de otoscopias, la parte que no es página (ver otoscopias.php):
 *
 *   GET  ?img=ID&v=base|original   la imagen (cualquier sesión del panel)
 *   GET  ?lista=1                  las clasificadas, en JSON, para elegir
 *                                  desde la ficha del caso (ídem)
 *   POST action=subir|guardar|borrar   solo el administrador completo: lo
 *                                  que se corrige acá reescribe la foto de
 *                                  todos los casos que la usan.
 *
 * Asignar una foto a un caso va por otoscopia_photo_upload.php
 * (action=biblioteca), que es donde se valida el caso.
 */

if ($_SERVER['REQUEST_METHOD'] === 'GET') {
    Auth::requireAdminSession();

    if (isset($_GET['img'])) {
        $id = (int) $_GET['img'];
        $ruta = (($_GET['v'] ?? 'base') === 'original')
            ? OtoscopiaBiblioteca::rutaOriginal($id)
            : OtoscopiaBiblioteca::rutaBase($id);
        if ($id <= 0 || !is_file($ruta)) {
            http_response_code(404);
            exit;
        }
        header('Content-Type: ' . (substr($ruta, -5) === '.webp' ? 'image/webp' : 'image/jpeg'));
        // La URL lleva &t=updated_at: puede quedar en caché sin miedo.
        header('Cache-Control: private, max-age=86400');
        readfile($ruta);
        exit;
    }

    header('Content-Type: application/json');
    $fotos = [];
    foreach (OtoscopiaBiblioteca::lista() as $f) {
        if (!OtoscopiaBiblioteca::clasificada($f)) {
            continue;
        }
        $fotos[] = [
            'id' => (int) $f['id'],
            'tipo' => (string) $f['tipo'],
            'tipo_label' => OtoscopiaBiblioteca::TIPOS[$f['tipo']] ?? (string) $f['tipo'],
            'anterior' => (string) $f['anterior'],
            'notas' => (string) $f['notas'],
            't' => (string) $f['updated_at'],
        ];
    }
    echo json_encode(['ok' => true, 'tipos' => OtoscopiaBiblioteca::TIPOS, 'fotos' => $fotos]);
    exit;
}

header('Content-Type: application/json');

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['ok' => false, 'error' => 'Método no permitido.']);
    exit;
}

$me = Auth::requireFullAdminSession();
try {
    Auth::requireCsrf();
} catch (Throwable $e) {
    http_response_code(403);
    echo json_encode(['ok' => false, 'error' => 'Sesión expirada, recarga la página.']);
    exit;
}

$action = (string) ($_POST['action'] ?? '');

try {
    if ($action === 'subir') {
        $file = $_FILES['photo'] ?? null;
        if (!$file || $file['error'] !== UPLOAD_ERR_OK) {
            throw new RuntimeException('No se pudo recibir el archivo.');
        }
        if ($file['size'] > 12 * 1024 * 1024) {
            throw new RuntimeException('La imagen pesa más de 12MB.');
        }
        $id = OtoscopiaBiblioteca::agregar($file['tmp_name'], (string) ($file['name'] ?? ''), (int) $me['id']);
        AdminAudit::log($me, 'otoscopia_biblioteca_subir', ['id' => $id, 'archivo' => (string) ($file['name'] ?? '')]);
        echo json_encode(['ok' => true, 'id' => $id]);
        exit;
    }

    $id = (int) ($_POST['id'] ?? 0);
    if ($id <= 0) {
        throw new RuntimeException('Falta la foto.');
    }

    if ($action === 'guardar') {
        $anterior = (string) ($_POST['anterior'] ?? '');
        $tipo = (string) ($_POST['tipo'] ?? '');
        $casos = OtoscopiaBiblioteca::guardar($id, [
            'rotacion' => (float) ($_POST['rotacion'] ?? 0),
            'centro_x' => (float) ($_POST['centro_x'] ?? 0),
            'centro_y' => (float) ($_POST['centro_y'] ?? 0),
            'lado' => (float) ($_POST['lado'] ?? 0),
            'anterior' => $anterior === '' ? null : $anterior,
            'tipo' => $tipo === '' ? null : $tipo,
            'notas' => (string) ($_POST['notas'] ?? ''),
        ]);
        AdminAudit::log($me, 'otoscopia_biblioteca_guardar', ['id' => $id, 'anterior' => $anterior, 'tipo' => $tipo, 'casos' => $casos]);
        echo json_encode([
            'ok' => true,
            'casos' => $casos,
            'siguiente' => OtoscopiaBiblioteca::siguientePendiente($id),
        ]);
        exit;
    }

    if ($action === 'borrar') {
        OtoscopiaBiblioteca::borrar($id);
        AdminAudit::log($me, 'otoscopia_biblioteca_borrar', ['id' => $id]);
        echo json_encode(['ok' => true]);
        exit;
    }

    throw new RuntimeException('Acción desconocida.');
} catch (Throwable $e) {
    echo json_encode(['ok' => false, 'error' => $e->getMessage()]);
}
