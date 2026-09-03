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
 * A diferencia de PatientPhoto no hay recorte circular: solo se reduce el
 * lado mayor a MAX_DIM para no acumular fotos de celular de varios MB.
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
    private const MAX_DIM = 1024;
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
        return str_ends_with($path, '.webp') ? 'image/webp' : 'image/jpeg';
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

        $scale = min(1.0, self::MAX_DIM / max($w, $h));
        $dstW = max(1, (int) round($w * $scale));
        $dstH = max(1, (int) round($h * $scale));

        $dst = imagecreatetruecolor($dstW, $dstH);
        imagecopyresampled($dst, $src, 0, 0, 0, 0, $dstW, $dstH, $w, $h);

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
