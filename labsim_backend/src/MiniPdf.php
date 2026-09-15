<?php

declare(strict_types=1);

/**
 * Generador de PDF mínimo, propio (sin Composer, sin librería de terceros
 * vendorizada): texto con Helvetica/Helvetica-Bold (fuentes core, sin
 * embeber), líneas/rectángulos/polilíneas/polígonos/círculos con color y
 * trazo punteado, e imágenes JPEG (incrustadas tal cual via DCTDecode, sin
 * pasar por GD -- este hosting puede no tenerlo, ver ReportFile.php).
 *
 * El color y el punteado entran por parámetro en cada primitiva, no como
 * estado del objeto: cada dibujo se emite dentro de su propio q/Q, así una
 * curva roja no puede teñir a la que venga después. Es lo que hace posible
 * dibujar el audiograma de los dos oídos sin arrastrar estado (ver
 * CaseCharts).
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
    /** Título del documento: lo que muestra el visor en la pestaña. */
    private string $titulo = '';
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
    private function drawWinAnsiLine(float $x, float $y, string $winAnsiText, float $size, bool $bold, ?string $color = null): void
    {
        $font = $bold ? '/FB' : '/F1';
        $encoded = self::esc($winAnsiText);
        $pdfY = $this->pageH - $y;
        $ops = sprintf("BT %s %.2F Tf %.2F %.2F Td (%s) Tj ET\n", $font, $size, $x, $pdfY, $encoded);
        if ($color === null) {
            $this->currentStream .= $ops;
            return;
        }
        $this->wrapped($ops, null, $color);
    }

    /** $text en UTF-8 (como llega de la app/BD) -- se convierte a WinAnsi acá. */
    public function text(float $x, float $y, string $text, float $size = 10, bool $bold = false, ?string $color = null): void
    {
        $this->drawWinAnsiLine($x, $y, self::toWinAnsi($text), $size, $bold, $color);
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

    /**
     * Dibuja texto envuelto empezando en (x,y), devuelve la Y siguiente
     * (después de la última línea).
     *
     * `$justificado` estira el espacio ENTRE palabras (operador `Tw` del
     * PDF) para que cada línea, salvo la última del bloque, llegue exacto
     * a `$maxWidth` -- como un texto de verdad impreso, no en bandera. La
     * última línea queda alineada a la izquierda, sin estirar (una línea
     * corta justificada se ve peor, con las palabras separadas por kilómetros).
     * Una línea de una sola palabra tampoco se estira: no hay espacio que
     * mover.
     */
    public function textBlock(float $x, float $y, string $text, float $maxWidth, float $size = 10, bool $bold = false, float $lineHeight = 0, ?string $color = null, bool $justificado = false): float
    {
        $lineHeight = $lineHeight > 0 ? $lineHeight : $size * 1.35;
        $lineas = $this->wrapText($text, $size, $maxWidth, $bold);
        $ultima = count($lineas) - 1;
        foreach ($lineas as $i => $line) {
            if ($justificado && $i !== $ultima) {
                $this->drawJustifiedLine($x, $y, $line, $size, $bold, $maxWidth, $color);
            } else {
                $this->drawWinAnsiLine($x, $y, $line, $size, $bold, $color);
            }
            $y += $lineHeight;
        }
        return $y;
    }

    /**
     * Una línea YA en WinAnsi, estirada con `Tw` (espaciado entre
     * palabras) para llegar justo a `$maxWidth`. El `Tw` es estado de
     * texto que persiste en el content stream más allá de este BT/ET --
     * por eso se resetea a 0 ANTES de cerrar, para no correr el espaciado
     * de todo el texto que se dibuje después.
     */
    private function drawJustifiedLine(float $x, float $y, string $winAnsiLine, float $size, bool $bold, float $maxWidth, ?string $color = null): void
    {
        $espacios = substr_count($winAnsiLine, ' ');
        if ($espacios < 1) {
            $this->drawWinAnsiLine($x, $y, $winAnsiLine, $size, $bold, $color);
            return;
        }
        $anchoNatural = HelveticaWidths::width($winAnsiLine, $size, $bold);
        $extra = max(0.0, ($maxWidth - $anchoNatural) / $espacios);

        $font = $bold ? '/FB' : '/F1';
        $encoded = self::esc($winAnsiLine);
        $pdfY = $this->pageH - $y;
        $ops = sprintf(
            "BT %s %.2F Tf %.2F Tw %.2F %.2F Td (%s) Tj 0 Tw ET\n",
            $font, $size, $extra, $x, $pdfY, $encoded
        );
        if ($color === null) {
            $this->currentStream .= $ops;
            return;
        }
        $this->wrapped($ops, null, $color);
    }

    public function line(float $x1, float $y1, float $x2, float $y2, float $width = 0.5, ?string $color = null, ?array $dash = null): void
    {
        $py1 = $this->pageH - $y1;
        $py2 = $this->pageH - $y2;
        $this->wrapped(
            sprintf("%.2F w%s %.2F %.2F m %.2F %.2F l S\n", $width, self::dashOp($dash), $x1, $py1, $x2, $py2),
            $color,
            null
        );
    }

    public function rect(float $x, float $y, float $w, float $h, float $lineWidth = 0.5, ?string $color = null): void
    {
        $py = $this->pageH - $y - $h;
        $this->wrapped(sprintf("%.2F w %.2F %.2F %.2F %.2F re S\n", $lineWidth, $x, $py, $w, $h), $color, null);
    }

    /** Rectángulo relleno sin borde -- fondos de tabla y barras. */
    public function rectFilled(float $x, float $y, float $w, float $h, string $color): void
    {
        $py = $this->pageH - $y - $h;
        $this->wrapped(sprintf("%.2F %.2F %.2F %.2F re f\n", $x, $py, $w, $h), null, $color);
    }

    /**
     * Polilínea abierta por puntos [[x,y], ...] en coordenadas de la API
     * (Y hacia abajo). Es el trazo de las curvas: audiograma, timpanograma,
     * logograma, desviación de la OEA.
     *
     * @param array<int,array{0:float,1:float}> $pts
     * @param array<int,float>|null $dash patrón [on, off] en pt, o null
     */
    public function polyline(array $pts, float $width = 1.0, ?string $color = null, ?array $dash = null): void
    {
        $pts = array_values(array_filter($pts, static fn ($p) => is_array($p) && count($p) >= 2));
        if (count($pts) < 2) {
            return;
        }
        $ops = sprintf("%.2F w%s\n", $width, self::dashOp($dash));
        foreach ($pts as $i => $pt) {
            $ops .= sprintf("%.2F %.2F %s\n", $pt[0], $this->pageH - $pt[1], $i === 0 ? 'm' : 'l');
        }
        $this->wrapped($ops . "S\n", $color, null);
    }

    /**
     * Polígono cerrado. Con $fillColor se rellena; con $strokeColor se
     * dibuja el borde; los dos juntos hacen las dos cosas.
     *
     * @param array<int,array{0:float,1:float}> $pts
     */
    public function polygon(array $pts, ?string $strokeColor = null, ?string $fillColor = null, float $width = 1.0): void
    {
        $pts = array_values(array_filter($pts, static fn ($p) => is_array($p) && count($p) >= 2));
        if (count($pts) < 3) {
            return;
        }
        $ops = sprintf("%.2F w\n", $width);
        foreach ($pts as $i => $pt) {
            $ops .= sprintf("%.2F %.2F %s\n", $pt[0], $this->pageH - $pt[1], $i === 0 ? 'm' : 'l');
        }
        $ops .= 'h ' . self::paintOp($strokeColor, $fillColor) . "\n";
        $this->wrapped($ops, $strokeColor, $fillColor);
    }

    /**
     * Curva por segmentos bezier cúbicos. Cada segmento es
     * [x0,y0, c1x,c1y, c2x,c2y, x1,y1] en coordenadas de la API; el punto
     * final de uno es el inicial del siguiente.
     *
     * La usa la curva de discriminación, que en un informe real se dibuja
     * redondeada y no como una quebrada (ver CaseCharts::curvaSuave).
     *
     * @param array<int,array<int,float>> $segmentos
     */
    public function bezier(array $segmentos, float $width = 1.0, ?string $color = null, ?array $dash = null): void
    {
        $segmentos = array_values(array_filter($segmentos, static fn ($s) => is_array($s) && count($s) >= 8));
        if ($segmentos === []) {
            return;
        }
        $ops = sprintf("%.2F w%s\n", $width, self::dashOp($dash));
        $ops .= sprintf("%.2F %.2F m\n", $segmentos[0][0], $this->pageH - $segmentos[0][1]);
        foreach ($segmentos as $s) {
            $ops .= sprintf(
                "%.2F %.2F %.2F %.2F %.2F %.2F c\n",
                $s[2],
                $this->pageH - $s[3],
                $s[4],
                $this->pageH - $s[5],
                $s[6],
                $this->pageH - $s[7]
            );
        }
        $this->wrapped($ops . "S\n", $color, null);
    }

    /**
     * Círculo por cuatro bezier (el PDF no tiene primitiva de arco). La
     * constante 0.5523 es la razón conocida que hace que una bezier cúbica
     * aproxime un cuarto de circunferencia.
     */
    public function circle(float $cx, float $cy, float $r, ?string $strokeColor = null, ?string $fillColor = null, float $width = 1.0): void
    {
        $k = $r * 0.5523;
        $py = $this->pageH - $cy;
        $ops = sprintf("%.2F w\n", $width);
        $ops .= sprintf("%.2F %.2F m\n", $cx + $r, $py);
        $ops .= sprintf("%.2F %.2F %.2F %.2F %.2F %.2F c\n", $cx + $r, $py + $k, $cx + $k, $py + $r, $cx, $py + $r);
        $ops .= sprintf("%.2F %.2F %.2F %.2F %.2F %.2F c\n", $cx - $k, $py + $r, $cx - $r, $py + $k, $cx - $r, $py);
        $ops .= sprintf("%.2F %.2F %.2F %.2F %.2F %.2F c\n", $cx - $r, $py - $k, $cx - $k, $py - $r, $cx, $py - $r);
        $ops .= sprintf("%.2F %.2F %.2F %.2F %.2F %.2F c\n", $cx + $k, $py - $r, $cx + $r, $py - $k, $cx + $r, $py);
        $ops .= self::paintOp($strokeColor, $fillColor) . "\n";
        $this->wrapped($ops, $strokeColor, $fillColor);
    }

    /** Ancho real de un texto en pt (Helvetica), para centrar o alinear a la derecha. */
    public function textWidth(string $text, float $size, bool $bold = false): float
    {
        return HelveticaWidths::width(self::toWinAnsi($text), $size, $bold);
    }

    /** Texto centrado en $xCenter. */
    public function textCenter(float $xCenter, float $y, string $text, float $size = 10, bool $bold = false, ?string $color = null): void
    {
        $this->text($xCenter - $this->textWidth($text, $size, $bold) / 2, $y, $text, $size, $bold, $color);
    }

    /** Texto terminado en $xRight (números de tabla, que se leen alineados). */
    public function textRight(float $xRight, float $y, string $text, float $size = 10, bool $bold = false, ?string $color = null): void
    {
        $this->text($xRight - $this->textWidth($text, $size, $bold), $y, $text, $size, $bold, $color);
    }

    /** '#rrggbb' -> "r g b" en 0..1, que es como el PDF pide el color. */
    private static function rgb(string $hex): string
    {
        $hex = ltrim(trim($hex), '#');
        if (strlen($hex) !== 6 || !ctype_xdigit($hex)) {
            return '0 0 0';
        }
        return sprintf(
            '%.3F %.3F %.3F',
            hexdec(substr($hex, 0, 2)) / 255,
            hexdec(substr($hex, 2, 2)) / 255,
            hexdec(substr($hex, 4, 2)) / 255
        );
    }

    /** Operador de pintado según qué colores se pidieron (borde, relleno o los dos). */
    private static function paintOp(?string $stroke, ?string $fill): string
    {
        if ($fill !== null && $stroke !== null) {
            return 'B';
        }
        return $fill !== null ? 'f' : 'S';
    }

    private static function dashOp(?array $dash): string
    {
        if ($dash === null || $dash === []) {
            return '';
        }
        return sprintf(' [%.2F %.2F] 0 d', (float) $dash[0], (float) ($dash[1] ?? $dash[0]));
    }

    /**
     * Emite $ops dentro de q/Q con los colores pedidos. Todo dibujo pasa por
     * acá: sin el q/Q, el color y el punteado quedarían activos para lo que
     * se dibuje después, que es la clase de bug que aparece recién al mirar
     * el PDF impreso.
     */
    private function wrapped(string $ops, ?string $strokeColor, ?string $fillColor): void
    {
        $this->currentStream .= "q\n";
        if ($strokeColor !== null) {
            $this->currentStream .= self::rgb($strokeColor) . " RG\n";
        }
        if ($fillColor !== null) {
            $this->currentStream .= self::rgb($fillColor) . " rg\n";
        }
        $this->currentStream .= $ops;
        $this->currentStream .= "Q\n";
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

        $this->embedJpeg($data, $info[0], $info[1], $colorSpace, $path . '#' . filemtime($path), $x, $y, $w, $h);
    }

    /**
     * Incrusta un JPEG que ya está en memoria, sin pasar por disco.
     *
     * Existe para las fotos del caso: se guardan en webp (otoscopia) o png
     * (avatar del paciente) y hay que convertirlas con GD para el PDF (ver
     * PdfImage). Escribir el JPEG convertido a un archivo temporal solo para
     * que image() lo vuelva a leer sería trabajo de más y basura en disco.
     *
     * @param string $jpegBytes contenido de un JPEG válido
     * @param string $clave identidad de la imagen: dos incrustaciones con la
     *                      misma clave comparten un solo objeto en el PDF
     */
    public function imageJpeg(string $jpegBytes, int $wPx, int $hPx, string $clave, float $x, float $y, float $w, float $h, bool $gris = false): void
    {
        $this->embedJpeg($jpegBytes, $wPx, $hPx, $gris ? 'DeviceGray' : 'DeviceRGB', $clave, $x, $y, $w, $h);
    }

    private function embedJpeg(string $data, int $wPx, int $hPx, string $colorSpace, string $key, float $x, float $y, float $w, float $h): void
    {
        if (!isset($this->images[$key])) {
            $this->images[$key] = [
                'width' => $wPx,
                'height' => $hPx,
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

    /**
     * Título del documento (diccionario /Info). Sin esto el visor muestra el
     * nombre del archivo o el de la URL, que es el del script que lo sirve.
     */
    public function setTitle(string $titulo): void
    {
        $this->titulo = $titulo;
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

        $infoNum = 0;
        if ($this->titulo !== '') {
            $infoNum = $nextObj++;
            $objects[$infoNum] = sprintf(
                "<< /Title (%s) /Producer (LabSim) >>",
                self::esc(self::toWinAnsi($this->titulo))
            );
        }

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
        $info = $infoNum > 0 ? " /Info {$infoNum} 0 R" : '';
        $out .= "trailer\n<< /Size {$total} /Root {$catalogNum} 0 R{$info} >>\nstartxref\n{$xrefOffset}\n%%EOF";

        return $out;
    }
}
