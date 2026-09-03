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
 */
final class OtoscopiaPhoto
{
    private const MAX_DIM = 1024;

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

    public static function path(string $caseId, string $side, int $faseIdx): string
    {
        if ($faseIdx < 0) {
            throw new InvalidArgumentException('Índice de fase inválido.');
        }
        return self::dir() . '/' . self::safeId($caseId) . '_' . self::safeSide($side) . '_' . $faseIdx . '.jpg';
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
        $p = self::path($caseId, $side, $faseIdx);
        if (is_file($p)) {
            unlink($p);
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
        imagejpeg($dst, self::path($caseId, $side, $faseIdx), 85);
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
