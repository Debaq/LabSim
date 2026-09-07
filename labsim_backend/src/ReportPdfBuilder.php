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
 *
 * EOA usa otro shape (no hay "curvas" con latencias, hay 4 pruebas
 * distintas medidas por oído -- ver OaeMainWindow.submit_report):
 * {
 *   "pruebas": {"teoae": {"OD": {...}, "OI": {...}}, "dpoae": {...},
 *               "soae": {...}, "sfoae": {...}},
 *   "hallazgos": "...", "conclusion": "..."
 * }
 * y sus imágenes son un gráfico por prueba y oído: suffixes
 * '<prueba>_od' / '<prueba>_oi'.
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

        if ($tipo === 'EOA') {
            $y = self::eoaBody($pdf, $reportId, $data, $y, $contentW);
            self::textSections($pdf, $data, $y, $contentW);
            return $pdf->output();
        }

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
        // Lista de picos a iterar: cliente VEMP la manda en data['waves'];
        // si falta (informes viejos ABR) usa default I/III/V. Acepta también
        // override por curva (curva['waves']) si una curva puntual midió
        // otro set (ej. cambian de CVEMP a OVEMP a mitad del examen).
        $wavesDefault = is_array($data['waves'] ?? null) && $data['waves'] !== []
            ? array_map('strval', $data['waves'])
            : ['I', 'III', 'V'];
        if (count($curvas) > 0) {
            $pdf->text(self::MARGIN, $y, 'Latencias y amplitudes', 12, true);
            $y += 18;
            foreach ($curvas as $nombreCurva => $curva) {
                if (!is_array($curva)) {
                    continue;
                }
                $linea = self::formatCurveLine((string) $nombreCurva, $curva, $wavesDefault);
                $pdf->text(self::MARGIN, $y, $linea, 9);
                $y += 14;
            }
            $y += 10;
        }

        self::textSections($pdf, $data, $y, $contentW);

        return $pdf->output();
    }

    /** Hallazgos + conclusión (mismo bloque para todos los tipos de informe). */
    private static function textSections(MiniPdf $pdf, array $data, float $y, float $contentW): void
    {
        foreach ([['Hallazgos', 'hallazgos'], ['Conclusión', 'conclusion']] as [$titulo, $clave]) {
            $texto = trim((string) ($data[$clave] ?? ''));
            if ($texto === '') {
                continue;
            }
            // Se paginan por bloque, no línea a línea: un informe largo
            // desbordaba la página y el texto quedaba fuera del papel.
            $alto = 18 + count($pdf->wrapText($texto, 10, $contentW)) * 13.5;
            $y = self::ensureSpace($pdf, $y, min($alto, 200.0));
            $pdf->text(self::MARGIN, $y, $titulo, 12, true);
            $y += 18;
            $y = $pdf->textBlock(self::MARGIN, $y, $texto, $contentW, 10);
            $y += 14;
        }
    }

    /**
     * Cuerpo del informe EOA: por cada prueba capturada, un bloque por oído
     * con el resumen numérico y el gráfico de esa prueba/oído.
     */
    private static function eoaBody(MiniPdf $pdf, int $reportId, array $data, float $y, float $contentW): float
    {
        $pruebas = is_array($data['pruebas'] ?? null) ? $data['pruebas'] : [];
        $labels = [
            'teoae' => 'TEOAE (transientes)',
            'dpoae' => 'DPOAE (producto de distorsión)',
            'soae' => 'SOAE (espontáneas)',
            'sfoae' => 'SFOAE (frecuencia de estímulo / supresión)',
        ];

        $hayAlgo = false;
        foreach ($labels as $clave => $label) {
            $porOido = is_array($pruebas[$clave] ?? null) ? $pruebas[$clave] : [];
            foreach (['OD', 'OI'] as $oido) {
                $resumen = is_array($porOido[$oido] ?? null) ? $porOido[$oido] : null;
                if ($resumen === null) {
                    continue;
                }
                $hayAlgo = true;
                $lineas = self::eoaLines($clave, $resumen);
                $imgPath = ReportFile::imagePath($reportId, "{$clave}_" . strtolower($oido));
                // El bloque entero (título + números + gráfico) se pagina
                // junto: partirlo deja el encabezado colgando al pie de una
                // página y su gráfico en la siguiente.
                $imgH = self::eoaImageHeight($imgPath, $contentW);
                $y = self::ensureSpace($pdf, $y, 20 + count($lineas) * 13 + $imgH + 12);
                $parcial = !empty($resumen['parcial']) ? '  (registro incompleto)' : '';
                $pdf->text(self::MARGIN, $y, "{$label} - {$oido}{$parcial}", 11, true);
                $y += 16;
                foreach ($lineas as $linea) {
                    $y = $pdf->textBlock(self::MARGIN, $y, $linea, $contentW, 9);
                }
                $y += 6;
                if ($imgH > 0.0) {
                    $pdf->image($imgPath, self::MARGIN, $y, $contentW, $imgH);
                    $y += $imgH;
                }
                $y += 12;
            }
        }

        if (!$hayAlgo) {
            $pdf->text(self::MARGIN, $y, 'Sin capturas registradas en este informe.', 10);
            $y += 20;
        }

        return $y;
    }

    /**
     * Alto con el que se va a dibujar el gráfico de una prueba/oído, o 0 si
     * no hay imagen. Usa la proporción real del archivo: forzar una fija
     * estira la captura y las curvas dejan de leerse.
     */
    private static function eoaImageHeight(string $path, float $contentW): float
    {
        if (!is_file($path)) {
            return 0.0;
        }
        $info = @getimagesize($path);
        $ratio = ($info && $info[0] > 0) ? $info[1] / $info[0] : 0.5;
        return min($contentW * $ratio, 210.0);
    }

    /** Líneas de resumen numérico de una prueba EOA en un oído. */
    private static function eoaLines(string $clave, array $r): array
    {
        return match ($clave) {
            'teoae' => self::teoaeLines($r),
            'dpoae' => self::dpoaeLines($r),
            'soae' => self::soaeLines($r),
            'sfoae' => self::sfoaeLines($r),
            default => [],
        };
    }

    private static function teoaeLines(array $r): array
    {
        $veredicto = !empty($r['overall_pass']) ? 'PASS' : 'REFER';
        $lineas = [sprintf(
            'Click %s dB SPL | %s promedios (%s barridos) | %s: %d/%d bandas sobre criterio',
            self::num($r['nivel_click_db_spl'] ?? null),
            self::num($r['n_promedios'] ?? null),
            self::num($r['n_barridos'] ?? null),
            $veredicto,
            (int) ($r['n_pass'] ?? 0),
            (int) ($r['n_bandas'] ?? 0)
        )];
        $lineas[] = sprintf(
            'Reproducibilidad %s%% | estabilidad del estímulo %s%% | respuesta %s dB SPL / ruido %s dB SPL',
            self::num($r['reproducibilidad_pct'] ?? null),
            self::num($r['estabilidad_pct'] ?? null),
            self::num($r['respuesta_db'] ?? null),
            self::num($r['ruido_db'] ?? null)
        );
        $bandas = [];
        foreach (is_array($r['bandas'] ?? null) ? $r['bandas'] : [] as $b) {
            $bandas[] = sprintf(
                '%s Hz: %s dB (%s)',
                self::num($b['hz'] ?? null),
                self::num($b['snr_db'] ?? null),
                !empty($b['pass']) ? 'pasa' : 'no pasa'
            );
        }
        if ($bandas) {
            $lineas[] = 'SNR por banda -- ' . implode('; ', $bandas);
        }
        return $lineas;
    }

    private static function dpoaeLines(array $r): array
    {
        $lineas = [sprintf(
            'L1/L2 %s/%s dB SPL | %s: %d/%d puntos sobre criterio',
            self::num($r['l1_db'] ?? null),
            self::num($r['l2_db'] ?? null),
            (string) ($r['veredicto'] ?? ''),
            (int) ($r['n_pass'] ?? 0),
            (int) ($r['n_total'] ?? 0)
        )];
        $puntos = [];
        foreach (is_array($r['puntos'] ?? null) ? $r['puntos'] : [] as $p) {
            $puntos[] = sprintf(
                '%s Hz: DP %s / NF %s (SNR %s, %s)',
                self::num($p['f2_hz'] ?? null),
                self::num($p['dp_db'] ?? null),
                self::num($p['nf_db'] ?? null),
                self::num($p['snr_db'] ?? null),
                !empty($p['pass']) ? 'pasa' : 'no pasa'
            );
        }
        if ($puntos) {
            $lineas[] = 'DP-grama (dB SPL) -- ' . implode('; ', $puntos);
        }
        if (($r['io_umbral_l2_db'] ?? null) !== null) {
            $lineas[] = sprintf(
                'Curva I/O @ f2 %s Hz: umbral DP en L2 = %s dB SPL',
                self::num($r['io_f2_hz'] ?? null),
                self::num($r['io_umbral_l2_db'])
            );
        }
        return $lineas;
    }

    private static function soaeLines(array $r): array
    {
        $picos = is_array($r['picos'] ?? null) ? $r['picos'] : [];
        if ($picos) {
            $estado = sprintf('SOAE PRESENTES (%d pico(s))', count($picos));
        } elseif (empty($r['concluyente'])) {
            $estado = 'REGISTRO NO CONCLUYENTE (piso de ruido alto)';
        } else {
            $estado = 'SIN SOAE DETECTADAS';
        }
        $lineas = [sprintf(
            'Registro %s s de %s s programados | piso medio %s dB SPL (máx. válido %s) | criterio SNR %s dB',
            self::num($r['duracion_s'] ?? null),
            self::num($r['duracion_programada_s'] ?? null),
            self::num($r['piso_medio_db_spl'] ?? null),
            self::num($r['piso_max_valido_db_spl'] ?? null),
            self::num($r['criterio_snr_db'] ?? null)
        ), $estado];
        $detalle = [];
        foreach ($picos as $pk) {
            $detalle[] = sprintf(
                '%s Hz: %s dB SPL (piso %s, SNR %s)',
                self::num($pk['freq_hz'] ?? null),
                self::num($pk['nivel_db_spl'] ?? null),
                self::num($pk['piso_db_spl'] ?? null),
                self::num($pk['snr_db'] ?? null)
            );
        }
        if ($detalle) {
            $lineas[] = 'Picos -- ' . implode('; ', $detalle);
        }
        return $lineas;
    }

    private static function sfoaeLines(array $r): array
    {
        $lineas = [sprintf(
            'Probe %s Hz a %s dB SPL | %s: magnitud máx %s dB sobre piso %s dB (SNR %s, criterio %s)',
            self::num($r['freq_probe_hz'] ?? null),
            self::num($r['nivel_probe_db_spl'] ?? null),
            (string) ($r['veredicto'] ?? ''),
            self::num($r['magnitud_max_db'] ?? null),
            self::num($r['piso_db'] ?? null),
            self::num($r['snr_db'] ?? null),
            self::num($r['criterio_snr_db'] ?? null)
        )];
        if (($r['sintonia_max_db'] ?? null) !== null) {
            $lineas[] = sprintf(
                'Curva de sintonía: máximo %s dB @ %s Hz (%d frecuencias medidas)',
                self::num($r['sintonia_max_db']),
                self::num($r['sintonia_freq_hz'] ?? null),
                (int) ($r['sintonia_puntos'] ?? 0)
            );
        }
        $sup = [];
        foreach (is_array($r['supresion'] ?? null) ? $r['supresion'] : [] as $pt) {
            $sup[] = sprintf(
                '%s dB: %s dB (fase %s°)',
                self::num($pt['supresor_db_spl'] ?? null),
                self::num($pt['magnitud_db'] ?? null),
                self::num($pt['fase_deg'] ?? null)
            );
        }
        if ($sup) {
            $lineas[] = 'Supresor -- ' . implode('; ', $sup);
        }
        return $lineas;
    }

    /** Número tal cual lo mandó el cliente, o 'N/D' si falta. */
    private static function num($valor): string
    {
        if ($valor === null || $valor === '') {
            return 'N/D';
        }
        if (is_float($valor)) {
            return rtrim(rtrim(number_format($valor, 1, ',', ''), '0'), ',');
        }
        return (string) $valor;
    }

    /** Salta de página si no caben $need puntos; devuelve la Y a usar. */
    private static function ensureSpace(MiniPdf $pdf, float $y, float $need): float
    {
        if ($y + $need > $pdf->pageHeight() - self::MARGIN) {
            $pdf->addPage();
            return self::MARGIN;
        }
        return $y;
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

    private static function formatCurveLine(string $nombre, array $curva, array $wavesDefault): string
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
        // Lista de picos a iterar: override por curva si viene, si no el
        // default del informe (data['waves'] o ['I','III','V'] para ABR).
        $waves = is_array($curva['waves'] ?? null) && $curva['waves'] !== []
            ? array_map('strval', $curva['waves'])
            : $wavesDefault;
        foreach ($waves as $onda) {
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
