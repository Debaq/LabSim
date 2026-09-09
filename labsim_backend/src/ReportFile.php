<?php

declare(strict_types=1);

/**
 * Archivos de un informe (imágenes de curvas + PDF final): mismo patrón que
 * OtoscopiaPhoto/PatientPhoto -- fuera de public/, en data/reports/, con
 * nombre determinista a partir del report_id (no hay columnas de imagen en
 * `reports`, solo pdf_filename que apunta al PDF ya armado).
 *
 * A diferencia de OtoscopiaPhoto, las imágenes de un informe NO se procesan
 * (no se recortan/redimensionan, no requieren GD): son capturas de gráficos
 * que ReportPdfBuilder embebe tal cual en el PDF (por eso deben venir como
 * JPEG -- ver MiniPdf::image(), que solo sabe incrustar JPEG/DCTDecode sin
 * pasar por GD).
 */
final class ReportFile
{
    public static function dir(): string
    {
        $dir = __DIR__ . '/../data/reports';
        if (!is_dir($dir) && !mkdir($dir, 0775, true) && !is_dir($dir)) {
            throw new RuntimeException("No se pudo crear {$dir} (revisa permisos).");
        }
        return $dir;
    }

    private static function safeSlug(int $reportId, string $suffix): string
    {
        $safe = preg_replace('/[^A-Za-z0-9_-]/', '', $suffix) ?? '';
        if ($reportId <= 0 || $safe === '') {
            throw new InvalidArgumentException('report_id o sufijo de imagen inválido.');
        }
        return "report_{$reportId}_{$safe}";
    }

    /** Ruta donde guardar/leer una imagen del informe (ej. suffix='0', '1', 'lat_int'). */
    public static function imagePath(int $reportId, string $suffix): string
    {
        return self::dir() . '/' . self::safeSlug($reportId, $suffix) . '.jpg';
    }

    /** Ruta del PDF final del informe. */
    public static function pdfPath(int $reportId): string
    {
        if ($reportId <= 0) {
            throw new InvalidArgumentException('report_id inválido.');
        }
        return self::dir() . "/report_{$reportId}.pdf";
    }

    /**
     * Guarda una imagen subida (ya validada como JPEG por el caller) para
     * el informe. Sobreescribe si ya existía (rehacer informe mientras la
     * atención sigue 'atendiendo', ver schema.sql).
     */
    public static function saveImage(int $reportId, string $suffix, string $tmpPath): void
    {
        $dest = self::imagePath($reportId, $suffix);
        if (!move_uploaded_file($tmpPath, $dest) && !copy($tmpPath, $dest)) {
            throw new RuntimeException('No se pudo guardar la imagen del informe.');
        }
    }

    /**
     * Borra el PDF ya armado (queda desactualizado en cuanto cambia
     * `reports.data` o se resube una imagen -- report_pdf.php lo
     * reconstruye al vuelo si falta). NO toca las imágenes: cada suffix se
     * sobreescribe solo si el caller vuelve a subirlo (ver saveImage()); un
     * informe rehecho sin reenviar, por ejemplo, la imagen de OI conserva
     * la anterior en vez de perderla.
     */
    public static function deletePdf(int $reportId): void
    {
        $pdf = self::dir() . "/report_{$reportId}.pdf";
        if (is_file($pdf)) {
            unlink($pdf);
        }
    }
}
