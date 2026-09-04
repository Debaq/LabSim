<?php

declare(strict_types=1);

/**
 * Imágenes de otoscopia: una por oído (modo "única") o varias por oído
 * -- una por fase -- en modo "por fase" (ver CaseBuilder::buildCaseData,
 * clave Otoscopia). Mismo patrón que PatientPhoto: archivos fuera de
 * public/ en data/otoscopia_photos/, servidos vía otoscopia_photo.php, sin
 * columnas nuevas en `cases` -- el nombre de archivo es determinista a
 * partir de case_id + oído + índice de fase (0 = fase 1 / única).
 *
 * A diferencia de PatientPhoto no hay selector de recorte manual: se recorta
 * un cuadrado centrado (lado = el menor de ancho/alto) y se reescala a
 * OUTPUT_SIZE fijo. Necesario porque fotos de celular vienen en cualquier
 * proporción -- sin esto, OD y OI quedaban con tamaños/proporciones
 * distintos y la ficha (tanto el editor admin como la app del alumno) se
 * veía dispareja entre ambos oídos y entre casos.
 *
 * Formato de salida: WebP si el GD del servidor lo soporta (~25-35% más
 * liviano que JPEG a calidad equivalente -- importa acá porque puede haber
 * varias fotos por caso, una por oído y fase), si no JPEG. Qt no necesita
 * saber cuál es: QPixmap::loadFromData detecta el formato solo por los
 * magic bytes. La extensión en el nombre de archivo SÍ importa acá: es lo
 * que dice con qué formato quedó guardada cada imagen (no hay columna en
 * la BD que lo registre), así que path()/has()/delete() prueban ambas.
 */
final class OtoscopiaPhoto
{
    private const OUTPUT_SIZE = 640; // cuadrado fijo -- normaliza tamaño/proporción entre fotos
    private const FORMATS = ['webp', 'jpg']; // orden de preferencia al buscar cuál existe

    public static function dir(): string
    {
        $dir = __DIR__ . '/../data/otoscopia_photos';
        if (!is_dir($dir) && !mkdir($dir, 0775, true) && !is_dir($dir)) {
            throw new RuntimeException("No se pudo crear {$dir} (revisa permisos).");
        }
        return $dir;
    }

    private static function safeId(string $caseId): string
    {
        $safe = preg_replace('/[^A-Za-z0-9_-]/', '', $caseId) ?? '';
        if ($safe === '') {
            throw new InvalidArgumentException('case_id inválido.');
        }
        return $safe;
    }

    private static function safeSide(string $side): string
    {
        if (!in_array($side, ['od', 'oi'], true)) {
            throw new InvalidArgumentException('Oído inválido.');
        }
        return $side;
    }

    private static function pathForFormat(string $caseId, string $side, int $faseIdx, string $ext): string
    {
        if ($faseIdx < 0) {
            throw new InvalidArgumentException('Índice de fase inválido.');
        }
        return self::dir() . '/' . self::safeId($caseId) . '_' . self::safeSide($side) . '_' . $faseIdx . '.' . $ext;
    }

    /** Ruta de la imagen que efectivamente existe en disco (webp o jpg, ver FORMATS) -- si ninguna existe, devuelve la ruta jpg (para que is_file() del caller dé false, mismo comportamiento que antes). */
    public static function path(string $caseId, string $side, int $faseIdx): string
    {
        foreach (self::FORMATS as $ext) {
            $p = self::pathForFormat($caseId, $side, $faseIdx, $ext);
            if (is_file($p)) {
                return $p;
            }
        }
        return self::pathForFormat($caseId, $side, $faseIdx, 'jpg');
    }

    public static function mimeType(string $path): string
    {
        return substr($path, -5) === '.webp' ? 'image/webp' : 'image/jpeg';
    }

    public static function has(string $caseId, string $side, int $faseIdx): bool
    {
        try {
            return is_file(self::path($caseId, $side, $faseIdx));
        } catch (InvalidArgumentException $e) {
            return false;
        }
    }

    public static function delete(string $caseId, string $side, int $faseIdx): void
    {
        try {
            foreach (self::FORMATS as $ext) {
                $p = self::pathForFormat($caseId, $side, $faseIdx, $ext);
                if (is_file($p)) {
                    unlink($p);
                }
            }
        } catch (InvalidArgumentException $e) {
            // faseIdx/caseId inválido -- nada que borrar.
        }
    }

    /**
     * Renombra TODAS las imágenes (cualquier oído/fase/formato) subidas con
     * un id temporal (ver $uploadTempId en case_create.php -- permite subir
     * otoscopia ANTES de que el caso tenga un case_id real) a su case_id
     * definitivo. No-op si no hay nada que reclamar (caso nuevo sin
     * otoscopia subida).
     */
    public static function claim(string $tempId, string $realCaseId): void
    {
        $tempSafe = self::safeId($tempId);
        $realSafe = self::safeId($realCaseId);
        if ($tempSafe === $realSafe) {
            return;
        }
        foreach (glob(self::dir() . '/' . $tempSafe . '_*') ?: [] as $path) {
            $suffix = substr(basename($path), strlen($tempSafe));
            rename($path, self::dir() . '/' . $realSafe . $suffix);
        }
    }

    public static function save(string $caseId, string $side, int $faseIdx, string $tmpPath): void
    {
        if (!extension_loaded('gd')) {
            throw new RuntimeException('El servidor no tiene la extensión GD -- no se pueden procesar imágenes.');
        }

        $info = @getimagesize($tmpPath);
        if ($info === false) {
            throw new RuntimeException('El archivo no es una imagen válida.');
        }
        $mime = $info['mime'];

        if ($mime === 'image/jpeg') {
            $src = imagecreatefromjpeg($tmpPath);
        } elseif ($mime === 'image/png') {
            $src = imagecreatefrompng($tmpPath);
        } elseif ($mime === 'image/webp' && function_exists('imagecreatefromwebp')) {
            $src = imagecreatefromwebp($tmpPath);
        } else {
            $src = false;
        }
        if ($src === false) {
            throw new RuntimeException('Formato de imagen no soportado (usa JPG, PNG o WEBP).');
        }

        $src = self::applyExifOrientation($src, $tmpPath, $mime);
        $w = imagesx($src);
        $h = imagesy($src);

        // Recorte cuadrado centrado sobre el lado menor -- normaliza
        // proporción antes de reescalar (ver comentario de clase).
        $cropSize = min($w, $h);
        $cropX = (int) round(($w - $cropSize) / 2);
        $cropY = (int) round(($h - $cropSize) / 2);

        $size = self::OUTPUT_SIZE;
        $dst = imagecreatetruecolor($size, $size);
        imagecopyresampled($dst, $src, 0, 0, $cropX, $cropY, $size, $size, $cropSize, $cropSize);

        // Borra lo que hubiera antes (pudo haber quedado en el otro formato
        // si el soporte de webp del servidor cambió entre subidas).
        self::delete($caseId, $side, $faseIdx);
        if (function_exists('imagewebp')) {
            imagewebp($dst, self::pathForFormat($caseId, $side, $faseIdx, 'webp'), 80);
        } else {
            imagejpeg($dst, self::pathForFormat($caseId, $side, $faseIdx, 'jpg'), 85);
        }
        imagedestroy($dst);
        imagedestroy($src);
    }

    /** @param resource|\GdImage $img */
    private static function applyExifOrientation($img, string $path, string $mime)
    {
        if ($mime !== 'image/jpeg' || !function_exists('exif_read_data')) {
            return $img;
        }
        $exif = @exif_read_data($path);
        $orientation = is_array($exif) ? (int) ($exif['Orientation'] ?? 1) : 1;
        if ($orientation === 3) {
            $img = imagerotate($img, 180, 0);
        } elseif ($orientation === 6) {
            $img = imagerotate($img, -90, 0);
        } elseif ($orientation === 8) {
            $img = imagerotate($img, 90, 0);
        }
        return $img;
    }
}
