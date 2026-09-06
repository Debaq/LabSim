<?php

declare(strict_types=1);

/**
 * Arma el PDF de un informe (ABR/EOA/VEMP/electrococleo) a partir de
 * `reports.data` (JSON: curvas + hallazgos + conclusión) y las imágenes ya
 * guardadas en ReportFile -- usa MiniPdf, no delega a ninguna librería.
 *
 * Shape esperado de $data (mismas claves que ya usaba AbrReport.py en el
 * cliente: 'hallazgos' = Descripción, 'conclusion' = Conclusión):
 * {
 *   "curvas": { "<nombre>": {"side":"OD","int":80,"average":1000,
 *                             "LatAmp": {"I":[lat,amp], "III":[...], "V":[...]}}, ... },
 *   "hallazgos": "texto plano",
 *   "conclusion": "texto plano"
 * }
 *
 * Imágenes (todas opcionales -- si no existe el archivo, se omite ese
 * bloque en vez de fallar): suffix '0' (OD), '1' (OI), 'lat_int'
 * (latencia-intensidad), ver ReportFile::imagePath().
 */
final class ReportPdfBuilder
{
    private const MARGIN = 50.0;

    public static function build(
        int $reportId,
        string $tipo,
        array $data,
        array $patient,
        string $evaluatorName,
        string $fecha
    ): string {
        $pdf = new MiniPdf();
        $pageW = $pdf->pageWidth();
        $contentW = $pageW - 2 * self::MARGIN;
        $y = self::MARGIN;

        $tipoLabel = self::tipoLabel($tipo);
        $pdf->text(self::MARGIN, $y, "Informe {$tipoLabel}", 18, true);
        $y += 26;
        $pdf->line(self::MARGIN, $y, $pageW - self::MARGIN, $y, 1.0);
        $y += 18;

        $nombre = trim(($patient['nombre'] ?? '') . ' ' . ($patient['apellido'] ?? ''));
        $pdf->text(self::MARGIN, $y, "Paciente: " . ($nombre !== '' ? $nombre : 'N/D'), 11, true);
        $y += 16;
        $pdf->text(self::MARGIN, $y, "RUT: " . ($patient['rut'] ?? 'N/D') . "   Fecha nac.: " . ($patient['fecha_nac'] ?? 'N/D'), 10);
        $y += 16;
        $pdf->text(self::MARGIN, $y, "Evaluador: {$evaluatorName}   Fecha informe: {$fecha}", 10);
        $y += 24;

        // Imágenes: OD y OI lado a lado, Lat-Int abajo (todas opcionales).
        $imgW = ($contentW - 20) / 2;
        $imgH = $imgW * 0.6;
        $drewSide = false;
        $odPath = ReportFile::imagePath($reportId, '0');
        $oiPath = ReportFile::imagePath($reportId, '1');
        if (is_file($odPath)) {
            $pdf->text(self::MARGIN, $y, 'OD', 9, true);
            $pdf->image($odPath, self::MARGIN, $y + 4, $imgW, $imgH);
            $drewSide = true;
        }
        if (is_file($oiPath)) {
            $pdf->text(self::MARGIN + $imgW + 20, $y, 'OI', 9, true);
            $pdf->image($oiPath, self::MARGIN + $imgW + 20, $y + 4, $imgW, $imgH);
            $drewSide = true;
        }
        if ($drewSide) {
            $y += $imgH + 24;
        }

        $latIntPath = ReportFile::imagePath($reportId, 'lat_int');
        if (is_file($latIntPath)) {
            $latIntW = $contentW;
            $latIntH = $latIntW * 0.35;
            $pdf->text(self::MARGIN, $y, 'Latencia-Intensidad', 9, true);
            $pdf->image($latIntPath, self::MARGIN, $y + 4, $latIntW, $latIntH);
            $y += $latIntH + 24;
        }

        // Tabla simple de latencias/amplitudes por curva (si hay datos).
        $curvas = is_array($data['curvas'] ?? null) ? $data['curvas'] : [];
        if (count($curvas) > 0) {
            $pdf->text(self::MARGIN, $y, 'Latencias y amplitudes', 12, true);
            $y += 18;
            foreach ($curvas as $nombreCurva => $curva) {
                if (!is_array($curva)) {
                    continue;
                }
                $linea = self::formatCurveLine((string) $nombreCurva, $curva);
                $pdf->text(self::MARGIN, $y, $linea, 9);
                $y += 14;
            }
            $y += 10;
        }

        $hallazgos = trim((string) ($data['hallazgos'] ?? ''));
        if ($hallazgos !== '') {
            $pdf->text(self::MARGIN, $y, 'Hallazgos', 12, true);
            $y += 18;
            $y = $pdf->textBlock(self::MARGIN, $y, $hallazgos, $contentW, 10);
            $y += 14;
        }

        $conclusion = trim((string) ($data['conclusion'] ?? ''));
        if ($conclusion !== '') {
            $pdf->text(self::MARGIN, $y, 'Conclusión', 12, true);
            $y += 18;
            $pdf->textBlock(self::MARGIN, $y, $conclusion, $contentW, 10);
        }

        return $pdf->output();
    }

    private static function tipoLabel(string $tipo): string
    {
        return match ($tipo) {
            'ABR' => 'PEATC (ABR)',
            'EOA' => 'Emisiones Otoacústicas',
            'VEMP' => 'Potenciales Evocados Vestibulares Miogénicos',
            'ELECTROCOCLEO' => 'Electrococleografía',
            default => $tipo,
        };
    }

    private static function formatCurveLine(string $nombre, array $curva): string
    {
        $side = (string) ($curva['side'] ?? '');
        $int = $curva['int'] ?? null;
        $average = $curva['average'] ?? null;
        $partes = ["Curva {$nombre}"];
        if ($side !== '') {
            $partes[] = $side;
        }
        if ($int !== null) {
            $partes[] = "{$int}dB";
        }
        if ($average !== null) {
            $partes[] = "prom={$average}";
        }
        $encabezado = implode(' - ', $partes) . ':';

        $ondas = [];
        $latAmp = is_array($curva['LatAmp'] ?? null) ? $curva['LatAmp'] : [];
        foreach (['I', 'III', 'V'] as $onda) {
            $par = $latAmp[$onda] ?? null;
            if (is_array($par) && $par[0] !== null) {
                $lat = is_numeric($par[0]) ? number_format((float) $par[0], 2) : (string) $par[0];
                $amp = isset($par[1]) && is_numeric($par[1]) ? number_format((float) $par[1], 2) : 'N/D';
                $ondas[] = "{$onda}={$lat}ms/{$amp}µV";
            }
        }

        return $ondas === [] ? $encabezado . ' sin ondas marcadas' : $encabezado . ' ' . implode('  ', $ondas);
    }
}
