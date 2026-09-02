<?php

declare(strict_types=1);

/**
 * Foto de paciente: se guardan dos archivos por caso en data/patient_photos/
 * (fuera de public/, no queda expuesta por URL directa -- se sirve vía
 * patient_photo.php, mismo patrón que backup_download.php). No hay columnas
 * nuevas en `cases`: el nombre de archivo es determinista a partir del
 * case_id, así que ni hace falta guardar la ruta en la BD.
 *
 * - "original": la foto tal cual la subieron, solo reducida (lado mayor
 *   <= 1024px) para no acumular fotos de celular de varios MB.
 * - "avatar": recorte circular (PNG con alfa) según el rectángulo que el
 *   admin eligió en el modal de case_create.php, sobre la imagen YA
 *   corregida de orientación EXIF (fotos de celular vienen rotadas).
 */
final class PatientPhoto
{
    private const MAX_ORIGINAL_DIM = 1024;
    private const AVATAR_SIZE = 320;

    public static function dir(): string
    {
        $dir = __DIR__ . '/../data/patient_photos';
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

    public static function originalPath(string $caseId): string
    {
        return self::dir() . '/' . self::safeId($caseId) . '_original.jpg';
    }

    public static function avatarPath(string $caseId): string
    {
        return self::dir() . '/' . self::safeId($caseId) . '_avatar.png';
    }

    public static function hasAvatar(string $caseId): bool
    {
        try {
            return is_file(self::avatarPath($caseId));
        } catch (InvalidArgumentException $e) {
            return false;
        }
    }

    public static function delete(string $caseId): void
    {
        foreach ([self::originalPath($caseId), self::avatarPath($caseId)] as $p) {
            if (is_file($p)) {
                unlink($p);
            }
        }
    }

    /**
     * $cropX/$cropY/$cropSize: recuadro cuadrado en coordenadas de píxel de
     * la imagen ORIGINAL (naturalWidth/Height tal como las ve el navegador),
     * calculado en el modal de recorte -- ver JS en case_create.php.
     */
    public static function save(string $caseId, string $tmpPath, float $cropX, float $cropY, float $cropSize): void
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

        self::saveReducedOriginal($src, $w, $h, self::originalPath($caseId));
        self::saveCircularAvatar($src, $w, $h, $cropX, $cropY, $cropSize, self::avatarPath($caseId));

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

    /** @param resource|\GdImage $src */
    private static function saveReducedOriginal($src, int $w, int $h, string $destPath): void
    {
        $scale = min(1.0, self::MAX_ORIGINAL_DIM / max($w, $h));
        $dstW = max(1, (int) round($w * $scale));
        $dstH = max(1, (int) round($h * $scale));

        $dst = imagecreatetruecolor($dstW, $dstH);
        imagecopyresampled($dst, $src, 0, 0, 0, 0, $dstW, $dstH, $w, $h);
        imagejpeg($dst, $destPath, 85);
        imagedestroy($dst);
    }

    /** @param resource|\GdImage $src */
    private static function saveCircularAvatar($src, int $w, int $h, float $cropX, float $cropY, float $cropSize, string $destPath): void
    {
        // El recuadro se calculó en el navegador contra naturalWidth/Height,
        // pero puede venir levemente afuera por redondeo -- clamp defensivo.
        $cropSize = max(1.0, min($cropSize, (float) min($w, $h)));
        $cropX = max(0.0, min($cropX, $w - $cropSize));
        $cropY = max(0.0, min($cropY, $h - $cropSize));

        $size = self::AVATAR_SIZE;
        $square = imagecreatetruecolor($size, $size);
        imagecopyresampled(
            $square,
            $src,
            0,
            0,
            (int) round($cropX),
            (int) round($cropY),
            $size,
            $size,
            (int) round($cropSize),
            (int) round($cropSize)
        );

        $avatar = imagecreatetruecolor($size, $size);
        imagealphablending($avatar, false);
        imagesavealpha($avatar, true);
        $transparent = imagecolorallocatealpha($avatar, 0, 0, 0, 127);
        imagefill($avatar, 0, 0, $transparent);

        // Máscara circular con 1px de borde suavizado (si no, el círculo
        // queda dentado/pixelado en los bordes).
        $radius = $size / 2;
        $cx = $radius;
        $cy = $radius;
        for ($y = 0; $y < $size; $y++) {
            for ($x = 0; $x < $size; $x++) {
                $dx = $x - $cx + 0.5;
                $dy = $y - $cy + 0.5;
                $dist = sqrt($dx * $dx + $dy * $dy);
                if ($dist > $radius + 0.5) {
                    continue;
                }
                $rgb = imagecolorat($square, $x, $y);
                $r = ($rgb >> 16) & 0xFF;
                $g = ($rgb >> 8) & 0xFF;
                $b = $rgb & 0xFF;
                $alpha = $dist <= $radius - 0.5 ? 0 : (int) round(($dist - ($radius - 0.5)) * 127);
                $color = imagecolorallocatealpha($avatar, $r, $g, $b, max(0, min(127, $alpha)));
                imagesetpixel($avatar, $x, $y, $color);
            }
        }

        imagepng($avatar, $destPath);
        imagedestroy($square);
        imagedestroy($avatar);
    }
}
