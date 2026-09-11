<?php

declare(strict_types=1);

require_once __DIR__ . '/../src/PdfImage.php';

/**
 * PdfImage: el puente entre las fotos del caso (webp/png) y el PDF, que solo
 * lleva JPEG. Lo que se comprueba acá es que NUNCA lance: una foto ilegible,
 * un servidor sin GD o un archivo que no existe tienen que devolver null y
 * dejar que la ficha se imprima sin esa foto.
 */

$tmp = sys_get_temp_dir() . '/labsim_pdfimage_' . getmypid();
@mkdir($tmp, 0777, true);

// JPEG real de 8x6 px (generado aparte y pegado acá para no depender de GD:
// la máquina de desarrollo puede no tenerlo, el hosting sí).
$jpegChico = base64_decode(
    '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAYEBQYFBAYGBQYHBwYIChAKCgkJChQODwwQFxQYGBcUFhYaHSUfGhsjHBYWICwgIyYnKSopGR8tMC0oMCUoKSj/2wBDAQcHBwoIChMKChMoGhYaKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCgoKCj/wAARCAAGAAgDASIAAhEBAxEB/8QAHwAAAQUBAQEBAQEAAAAAAAAAAAECAwQFBgcICQoL/8QAtRAAAgEDAwIEAwUFBAQAAAF9AQIDAAQRBRIhMUEGE1FhByJxFDKBkaEII0KxwRVS0fAkM2JyggkKFhcYGRolJicoKSo0NTY3ODk6Q0RFRkdISUpTVFVWV1hZWmNkZWZnaGlqc3R1dnd4eXqDhIWGh4iJipKTlJWWl5iZmqKjpKWmp6ipqrKztLW2t7i5usLDxMXGx8jJytLT1NXW19jZ2uHi4+Tl5ufo6erx8vP09fb3+Pn6/8QAHwEAAwEBAQEBAQEBAQAAAAAAAAECAwQFBgcICQoL/8QAtREAAgECBAQDBAcFBAQAAQJ3AAECAxEEBSExBhJBUQdhcRMiMoEIFEKRobHBCSMzUvAVYnLRChYkNOEl8RcYGRomJygpKjU2Nzg5OkNERUZHSElKU1RVVldYWVpjZGVmZ2hpanN0dXZ3eHl6goOEhYaHiImKkpOUlZaXmJmaoqOkpaanqKmqsrO0tba3uLm6wsPExcbHyMnK0tPU1dbX2Nna4uPk5ebn6Onq8vP09fb3+Pn6/9oADAMBAAIRAxEAPwDgKKKK+eP2E//Z'
);
$rutaJpeg = $tmp . '/foto.jpg';
file_put_contents($rutaJpeg, $jpegChico);

$img = PdfImage::jpegBytes($rutaJpeg);
t_true(is_array($img), 'Un JPEG se puede incrustar');
t_eq($img['w'] ?? null, 8, 'Lee el ancho real del JPEG');
t_eq($img['h'] ?? null, 6, 'Lee el alto real del JPEG');
t_eq($img['data'] ?? null, $jpegChico, 'El JPEG se incrusta tal cual, sin recomprimir');

t_close(PdfImage::altoProporcional($img, 60.0), 45.0, 0.01,
    'El alto proporcional respeta la forma de la foto (8x6 en 60 pt de ancho)');

// Lo que no se puede incrustar devuelve null, no una excepción.
t_eq(PdfImage::jpegBytes($tmp . '/no_existe.jpg'), null, 'Una foto que no está devuelve null');
t_eq(PdfImage::jpegBytes(''), null, 'Una ruta vacía devuelve null');
file_put_contents($tmp . '/basura.jpg', 'esto no es una imagen');
t_eq(PdfImage::jpegBytes($tmp . '/basura.jpg'), null, 'Un archivo que no es imagen devuelve null');

// PNG: con GD se convierte, sin GD se omite. Las dos son respuestas válidas
// -- lo que no puede pasar es que reviente (el hosting tiene GD porque sin
// ella no se puede ni subir una foto; esta máquina puede no tenerla).
if (extension_loaded('gd')) {
    $png = imagecreatetruecolor(12, 9);
    imagefill($png, 0, 0, imagecolorallocate($png, 10, 120, 200));
    imagepng($png, $tmp . '/foto.png');
    imagedestroy($png);
    $convertida = PdfImage::jpegBytes($tmp . '/foto.png');
    t_true(is_array($convertida), 'Con GD, un PNG se convierte a JPEG');
    t_eq($convertida['w'] ?? null, 12, 'La conversión conserva el ancho');
    t_eq($convertida['h'] ?? null, 9, 'La conversión conserva el alto');
    t_true(strncmp((string) ($convertida['data'] ?? ''), "\xFF\xD8\xFF", 3) === 0,
        'Lo convertido es un JPEG de verdad (empieza con SOI)');
} else {
    file_put_contents($tmp . '/foto.png', "\x89PNG\r\n\x1a\n");
    t_eq(PdfImage::jpegBytes($tmp . '/foto.png'), null,
        'Sin GD, una foto que no es JPEG se omite en vez de fallar');
}

foreach (glob($tmp . '/*') ?: [] as $f) {
    unlink($f);
}
@rmdir($tmp);
