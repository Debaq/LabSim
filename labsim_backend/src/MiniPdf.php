<?php

declare(strict_types=1);

/**
 * Generador de PDF mínimo, propio (sin Composer, sin librería de terceros
 * vendorizada) -- alcanza para lo que necesita ReportPdfBuilder: texto con
 * Helvetica/Helvetica-Bold (fuentes core, sin embeber), líneas/rectángulos,
 * e imágenes JPEG (incrustadas tal cual via DCTDecode, sin pasar por GD --
 * este hosting puede no tenerlo, ver ReportFile.php).
 *
 * No soporta: PNG (por eso ReportFile solo acepta JPEG), compresión de
 * streams (FlateDecode) ni fuentes embebidas/Unicode completo -- el texto
 * se recodifica a WinAnsiEncoding (~cp1252, cubre español con tildes/ñ) y
 * lo que no entra ahí se transcribe lo mejor posible (iconv//TRANSLIT).
 *
 * Coordenadas de la API: origen arriba-izquierda, Y crece hacia abajo
 * (como el resto del layout de la app) -- se convierten internamente al
 * sistema de PDF (origen abajo-izquierda).
 */
final class MiniPdf
{
    private float $pageW;
    private float $pageH;
    /** @var array<int, string> contenido (stream) de cada página ya cerrada */
    private array $pageStreams = [];
    /** @var array<int, array<int, string>> imágenes usadas por cada página: [pageIndex => [xobjName => imageObjKey]] */
    private array $pageImages = [];
    private string $currentStream = '';
    private array $currentPageImages = [];
    /** @var array<string, array{width:int,height:int,colorSpace:string,bits:int,data:string}> */
    private array $images = [];
    private int $imageCounter = 0;

    public function __construct(float $widthPt = 595.28, float $heightPt = 841.89)
    {
        $this->pageW = $widthPt;
        $this->pageH = $heightPt;
    }

    public function addPage(): void
    {
        $this->closeCurrentPage();
        $this->currentStream = '';
        $this->currentPageImages = [];
    }

    private function closeCurrentPage(): void
    {
        if ($this->currentStream !== '' || count($this->pageStreams) === 0) {
            $this->pageStreams[] = $this->currentStream;
            $this->pageImages[] = $this->currentPageImages;
        }
    }

    private static function esc(string $s): string
    {
        return str_replace(['\\', '(', ')'], ['\\\\', '\\(', '\\)'], $s);
    }

    /** UTF-8 (como llega de la app/BD) -> WinAnsiEncoding (~cp1252) para el content stream. */
    /**
     * mbstring primero (casi siempre presente, incluso en hostings sin
     * iconv), iconv como respaldo, y si ninguna extensión está cargada,
     * solo deja pasar ASCII imprimible (pierde tildes/ñ, pero no revienta).
     */
    private static function toWinAnsi(string $utf8): string
    {
        if (function_exists('mb_convert_encoding')) {
            $out = @mb_convert_encoding($utf8, 'Windows-1252', 'UTF-8');
            if ($out !== false && $out !== '') {
                return $out;
            }
        }
        if (function_exists('iconv')) {
            $out = @iconv('UTF-8', 'Windows-1252//TRANSLIT//IGNORE', $utf8);
            if ($out !== false) {
                return $out;
            }
        }
        return preg_replace('/[^\x20-\x7E]/', '?', $utf8) ?? '';
    }

    /** Dibuja una línea YA en WinAnsi (un byte por char) -- no reconvierte. Uso interno de text()/textBlock(). */
    private function drawWinAnsiLine(float $x, float $y, string $winAnsiText, float $size, bool $bold): void
    {
        $font = $bold ? '/FB' : '/F1';
        $encoded = self::esc($winAnsiText);
        $pdfY = $this->pageH - $y;
        $this->currentStream .= sprintf("BT %s %.2F Tf %.2F %.2F Td (%s) Tj ET\n", $font, $size, $x, $pdfY, $encoded);
    }

    /** $text en UTF-8 (como llega de la app/BD) -- se convierte a WinAnsi acá. */
    public function text(float $x, float $y, string $text, float $size = 10, bool $bold = false): void
    {
        $this->drawWinAnsiLine($x, $y, self::toWinAnsi($text), $size, $bold);
    }

    /**
     * Envuelve $text (UTF-8) en líneas de ancho <= $maxWidth (pt), usando el
     * ancho real de Helvetica. La conversión a WinAnsi se hace UNA vez acá
     * (antes de medir) -- las líneas devueltas ya están en WinAnsi, listas
     * para drawWinAnsiLine() sin reconvertir.
     */
    public function wrapText(string $text, float $size, float $maxWidth, bool $bold = false): array
    {
        $winAnsi = self::toWinAnsi($text);
        $lines = [];
        foreach (preg_split('/\r\n|\r|\n/', $winAnsi) ?: [$winAnsi] as $paragraph) {
            $words = preg_split('/\s+/', trim($paragraph));
            $current = '';
            foreach ($words as $word) {
                if ($word === '') {
                    continue;
                }
                $candidate = $current === '' ? $word : $current . ' ' . $word;
                if (HelveticaWidths::width($candidate, $size, $bold) > $maxWidth && $current !== '') {
                    $lines[] = $current;
                    $current = $word;
                } else {
                    $current = $candidate;
                }
            }
            $lines[] = $current;
        }
        return $lines;
    }

    /** Dibuja texto envuelto empezando en (x,y), devuelve la Y siguiente (después de la última línea). */
    public function textBlock(float $x, float $y, string $text, float $maxWidth, float $size = 10, bool $bold = false, float $lineHeight = 0): float
    {
        $lineHeight = $lineHeight > 0 ? $lineHeight : $size * 1.35;
        foreach ($this->wrapText($text, $size, $maxWidth, $bold) as $line) {
            $this->drawWinAnsiLine($x, $y, $line, $size, $bold);
            $y += $lineHeight;
        }
        return $y;
    }

    public function line(float $x1, float $y1, float $x2, float $y2, float $width = 0.5): void
    {
        $py1 = $this->pageH - $y1;
        $py2 = $this->pageH - $y2;
        $this->currentStream .= sprintf("%.2F w %.2F %.2F m %.2F %.2F l S\n", $width, $x1, $py1, $x2, $py2);
    }

    public function rect(float $x, float $y, float $w, float $h, float $lineWidth = 0.5): void
    {
        $py = $this->pageH - $y - $h;
        $this->currentStream .= sprintf("%.2F w %.2F %.2F %.2F %.2F re S\n", $lineWidth, $x, $py, $w, $h);
    }

    /**
     * Incrusta un JPEG ya existente en disco. $path debe ser un JPEG válido
     * (el caller -- ReportPdfBuilder -- ya lo validó al guardarlo, ver
     * ReportFile). Lanza RuntimeException si no se puede leer/parsear.
     */
    public function image(string $path, float $x, float $y, float $w, float $h): void
    {
        $info = @getimagesize($path);
        if ($info === false || $info[2] !== IMAGETYPE_JPEG) {
            throw new RuntimeException("Imagen inválida para el informe: {$path}");
        }
        $data = file_get_contents($path);
        if ($data === false) {
            throw new RuntimeException("No se pudo leer la imagen: {$path}");
        }
        $channels = $info['channels'] ?? 3;
        $colorSpace = $channels === 1 ? 'DeviceGray' : ($channels === 4 ? 'DeviceCMYK' : 'DeviceRGB');

        $key = $path . '#' . filemtime($path);
        if (!isset($this->images[$key])) {
            $this->images[$key] = [
                'width' => $info[0],
                'height' => $info[1],
                'colorSpace' => $colorSpace,
                'bits' => 8,
                'data' => $data,
            ];
        }
        $this->imageCounter++;
        $name = 'Im' . $this->imageCounter;
        $this->currentPageImages[$name] = $key;

        $pdfY = $this->pageH - $y - $h;
        $this->currentStream .= sprintf("q %.2F 0 0 %.2F %.2F %.2F cm /%s Do Q\n", $w, $h, $x, $pdfY, $name);
    }

    public function pageWidth(): float
    {
        return $this->pageW;
    }

    public function pageHeight(): float
    {
        return $this->pageH;
    }

    /** Arma el PDF completo y lo devuelve como string (el caller lo guarda con file_put_contents). */
    public function output(): string
    {
        $this->closeCurrentPage();

        $objects = []; // 1-indexed: $objects[n] = cuerpo del objeto n (sin "n 0 obj"/"endobj")
        $nextObj = 1;

        $catalogNum = $nextObj++;
        $pagesNum = $nextObj++;
        $fontRegularNum = $nextObj++;
        $fontBoldNum = $nextObj++;

        $objects[$fontRegularNum] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>";
        $objects[$fontBoldNum] = "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>";

        // Un objeto de imagen por clave única (reusa si la misma imagen se
        // incrustó en más de una página, aunque hoy solo generamos 1 página).
        $imageObjNums = [];
        foreach ($this->images as $key => $img) {
            $num = $nextObj++;
            $imageObjNums[$key] = $num;
            $stream = $img['data'];
            $objects[$num] = sprintf(
                "<< /Type /XObject /Subtype /Image /Width %d /Height %d /ColorSpace /%s /BitsPerComponent %d /Filter /DCTDecode /Length %d >>\nstream\n%s\nendstream",
                $img['width'],
                $img['height'],
                $img['colorSpace'],
                $img['bits'],
                strlen($stream),
                $stream
            );
        }

        $pageNums = [];
        foreach ($this->pageStreams as $i => $stream) {
            $contentNum = $nextObj++;
            $objects[$contentNum] = sprintf("<< /Length %d >>\nstream\n%s\nendstream", strlen($stream), $stream);

            $xobjEntries = [];
            foreach ($this->pageImages[$i] as $name => $key) {
                $xobjEntries[] = "/{$name} {$imageObjNums[$key]} 0 R";
            }
            $xobjDict = count($xobjEntries) > 0 ? ' /XObject << ' . implode(' ', $xobjEntries) . ' >>' : '';

            $pageNum = $nextObj++;
            $pageNums[] = $pageNum;
            $objects[$pageNum] = sprintf(
                "<< /Type /Page /Parent %d 0 R /MediaBox [0 0 %.2F %.2F] /Resources << /Font << /F1 %d 0 R /FB %d 0 R >>%s >> /Contents %d 0 R >>",
                $pagesNum,
                $this->pageW,
                $this->pageH,
                $fontRegularNum,
                $fontBoldNum,
                $xobjDict,
                $contentNum
            );
        }

        $kids = implode(' ', array_map(static fn ($n) => "{$n} 0 R", $pageNums));
        $objects[$pagesNum] = sprintf("<< /Type /Pages /Kids [%s] /Count %d >>", $kids, count($pageNums));
        $objects[$catalogNum] = "<< /Type /Catalog /Pages {$pagesNum} 0 R >>";

        ksort($objects, SORT_NUMERIC);

        $out = "%PDF-1.4\n";
        $offsets = [0 => 0];
        foreach ($objects as $num => $body) {
            $offsets[$num] = strlen($out);
            $out .= "{$num} 0 obj\n{$body}\nendobj\n";
        }

        $xrefOffset = strlen($out);
        $total = count($objects) + 1;
        $out .= "xref\n0 {$total}\n";
        $out .= "0000000000 65535 f \n";
        for ($n = 1; $n < $total; $n++) {
            $out .= sprintf("%010d 00000 n \n", $offsets[$n] ?? 0);
        }
        $out .= "trailer\n<< /Size {$total} /Root {$catalogNum} 0 R >>\nstartxref\n{$xrefOffset}\n%%EOF";

        return $out;
    }
}
