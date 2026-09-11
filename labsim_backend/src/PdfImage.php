<?php

declare(strict_types=1);

/**
 * Una imagen del caso, lista para incrustar en un PDF.
 *
 * El PDF solo sabe llevar JPEG (MiniPdf usa DCTDecode, sin pasar por GD),
 * pero las fotos del caso NO se guardan en JPEG: la otoscopia va en webp
 * cuando el servidor lo soporta (OtoscopiaPhoto::save) y el avatar del
 * paciente en png (PatientPhoto). Esta clase es el puente: devuelve los
 * bytes JPEG de cualquiera de las tres, convirtiendo con GD cuando hace
 * falta.
 *
 * Convierte EN MEMORIA y no cachea a disco a propósito: la foto se puede
 * reemplazar desde el editor, y un JPEG guardado al lado quedaría mostrando
 * la foto vieja hasta que a alguien se le ocurra mirar la fecha del archivo.
 * Son 640x640 como máximo; el costo de reconvertir es irrelevante frente a
 * imprimir una ficha equivocada.
 *
 * Si no hay GD, o el formato no se puede leer, devuelve null y el que llama
 * omite esa foto. Nunca lanza: que falte una foto no puede tumbar la ficha
 * entera (el mismo criterio que ReportPdfBuilder con sus imágenes).
 */
final class PdfImage
{
    /** Calidad del JPEG que se incrusta. 85 es el mismo número que usa OtoscopiaPhoto al guardar. */
    private const CALIDAD = 85;

    /**
     * @return array{data:string,w:int,h:int}|null bytes JPEG y tamaño en px
     */
    public static function jpegBytes(string $path): ?array
    {
        if ($path === '' || !is_file($path)) {
            return null;
        }
        $info = @getimagesize($path);
        if ($info === false) {
            return null;
        }

        // Ya es JPEG: se incrusta tal cual, sin recomprimir (recomprimir un
        // JPEG solo le saca calidad).
        if (($info[2] ?? 0) === IMAGETYPE_JPEG) {
            $data = @file_get_contents($path);
            return $data === false ? null : ['data' => $data, 'w' => (int) $info[0], 'h' => (int) $info[1]];
        }

        if (!extension_loaded('gd')) {
            return null;
        }
        $src = self::abrir($path, (string) ($info['mime'] ?? ''));
        if ($src === null) {
            return null;
        }

        // Fondo blanco: el png del avatar puede traer transparencia, y el
        // JPEG no la tiene -- sin esto el recorte sale sobre negro.
        $w = imagesx($src);
        $h = imagesy($src);
        $plano = imagecreatetruecolor($w, $h);
        imagefill($plano, 0, 0, imagecolorallocate($plano, 255, 255, 255));
        imagecopy($plano, $src, 0, 0, 0, 0, $w, $h);
        imagedestroy($src);

        ob_start();
        imagejpeg($plano, null, self::CALIDAD);
        $bytes = (string) ob_get_clean();
        imagedestroy($plano);

        return $bytes === '' ? null : ['data' => $bytes, 'w' => $w, 'h' => $h];
    }

    /**
     * Alto que le corresponde a la imagen dentro de un ancho dado,
     * respetando la proporción.
     */
    public static function altoProporcional(array $img, float $ancho): float
    {
        $w = max(1, (int) $img['w']);
        return $ancho * ((int) $img['h'] / $w);
    }

    /** @return resource|\GdImage|null */
    private static function abrir(string $path, string $mime)
    {
        if ($mime === 'image/png') {
            $img = @imagecreatefrompng($path);
        } elseif ($mime === 'image/webp' && function_exists('imagecreatefromwebp')) {
            $img = @imagecreatefromwebp($path);
        } elseif ($mime === 'image/gif') {
            $img = @imagecreatefromgif($path);
        } else {
            return null;
        }
        return $img === false ? null : $img;
    }
}
