<?php

declare(strict_types=1);

/**
 * Arma el PDF de un informe (ABR/EOA/VEMP/electrococleo/otoscopia) a partir de
 * `reports.data` (JSON: curvas + hallazgos + conclusión) y las imágenes ya
 * guardadas en ReportFile -- usa MiniPdf, no delega a ninguna librería.
 *
 * Shape esperado de $data (mismas claves que ya usaba AbrReport.py en el
 * cliente: 'hallazgos' = Descripción, 'conclusion' = Conclusión):
 * {
 *   "curvas": { "<nombre>": {"side":"OD","int":80,"average":1000,
 *                             "LatAmp": {"I":[lat,amp], "III":[...], "V":[...]}}, ... },
 *   "hallazgos": "texto plano",
 *   "conclusion": "texto plano",
 *   "asimetria": {"subtipo":"CVEMP","od":..,"oi":..,"ratio":..} -- solo
 *                 VEMP, con las amplitudes pico-pico marcadas por el
 *                 alumno (ver VempMainWindow::asimetria),
 *   "tecnica": { condiciones de registro -- equipo, electrodos e
 *                impedancias, rechazo, criterio FSP y lo que el equipo
 *                midio (barridos aceptados, FSP, ruido, replicabilidad).
 *                Opcional: los informes viejos no lo traen. }
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
// No hay autoloader: la dependencia se declara donde se usa. Sin estos dos
// require, build() fatalaba con "Class MiniPdf not found" apenas se pedía un
// informe sin PDF ya subido.
require_once __DIR__ . '/HelveticaWidths.php';
require_once __DIR__ . '/MiniPdf.php';

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

        if ($tipo === 'OTOSCOPIA') {
            $y = self::otoscopiaBody($pdf, $data, $y, $contentW);
            self::textSections($pdf, $data, $y, $contentW);
            return $pdf->output();
        }

        if ($tipo === 'RINOSCOPIA') {
            $y = self::rinoscopiaBody($pdf, $data, $y, $contentW);
            self::textSections($pdf, $data, $y, $contentW);
            return $pdf->output();
        }

        if ($tipo === 'RINOMANOMETRIA' || $tipo === 'RINOMETRIA') {
            $y = self::nasalBody($pdf, $reportId, $tipo, $data, $y, $contentW);
            self::textSections($pdf, $data, $y, $contentW);
            return $pdf->output();
        }

        if ($tipo === 'AABR') {
            $y = self::aabrBody($pdf, $data, $y, $contentW);
            $y = self::technicalSection($pdf, $data, $y, $contentW);
            self::textSections($pdf, $data, $y, $contentW);
            return $pdf->output();
        }

        if ($tipo === 'EOA') {
            $y = self::eoaBody($pdf, $reportId, $data, $y, $contentW);
            $y = self::technicalSection($pdf, $data, $y, $contentW);
            self::textSections($pdf, $data, $y, $contentW);
            return $pdf->output();
        }

        if ($tipo === 'ELECTROCOCLEO') {
            $y = self::ecochgBody($pdf, $reportId, $data, $y, $contentW);
            $y = self::technicalSection($pdf, $data, $y, $contentW);
            self::textSections($pdf, $data, $y, $contentW);
            return $pdf->output();
        }

        if ($tipo === 'ASSR') {
            $y = self::assrBody($pdf, $reportId, $data, $y, $contentW);
            $y = self::technicalSection($pdf, $data, $y, $contentW);
            self::textSections($pdf, $data, $y, $contentW);
            return $pdf->output();
        }

        if (in_array($tipo, ['PEALM', 'CAEP', 'P300', 'MMN'], true)) {
            $y = self::corticalBody($pdf, $reportId, $data, $y, $contentW);
            $y = self::technicalSection($pdf, $data, $y, $contentW);
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
                // Como se registro ESTA curva. El alumno puede cambiar
                // estimulo, tasa o filtros entre curvas, asi que el
                // bloque global de condiciones no alcanza.
                $detalle = self::formatCurveSetup($curva);
                if ($detalle !== '') {
                    $pdf->text(self::MARGIN + 12, $y, $detalle, 8);
                    $y += 12;
                }
            }
            $y += 10;
        }

        // Razón de asimetría (VEMP): la manda el cliente ya calculada con
        // las amplitudes pico-pico que marcó el alumno. Se imprime el
        // número y las dos amplitudes, sin lectura -- qué asimetría es
        // patológica lo dice quien informa.
        $asim = is_array($data['asimetria'] ?? null) ? $data['asimetria'] : [];
        if (isset($asim['ratio']) && is_numeric($asim['ratio'])) {
            $y = self::ensureSpace($pdf, $y, 34);
            $pdf->text(self::MARGIN, $y, 'Razón de asimetría', 12, true);
            $y += 18;
            $pdf->text(self::MARGIN, $y, trim((string) ($asim['subtipo'] ?? '')) . '  '
                . self::num($asim['ratio']) . '%  (OD ' . self::num($asim['od'] ?? null)
                . ' µV / OI ' . self::num($asim['oi'] ?? null) . ' µV pico-pico)', 9);
            $y += 14;
            // Con qué se calculó: la razón sale de las amplitudes corregidas
            // por EMG, no de las crudas de la línea de arriba.
            if (isset($asim['od_corregida']) && isset($asim['oi_corregida'])) {
                $pdf->text(self::MARGIN, $y, 'Corregidas por EMG: OD '
                    . self::num($asim['od_corregida']) . ' / OI '
                    . self::num($asim['oi_corregida'])
                    . ' (la razón se calcula con éstas)', 8);
                $y += 12;
            }
            $y += 12;
        }

        // Umbral: lo que el alumno informó, y hasta dónde llegó la serie que
        // midió. Son dos cosas distintas y por eso se imprimen las dos.
        $umbrales = is_array($data['umbral_informado'] ?? null) ? $data['umbral_informado'] : [];
        $lineasUmbral = [];
        foreach (['OD', 'OI'] as $lado) {
            $informado = $umbrales[$lado] ?? null;
            $medido = $asim['umbral_' . strtolower($lado)] ?? null;
            if ($informado === null && $medido === null) {
                continue;
            }
            $texto = $lado . ': ';
            $texto .= $informado === null ? 'sin umbral informado'
                : ('umbral informado ' . self::num($informado) . ' dB');
            if ($medido !== null) {
                $texto .= '  ·  respuesta marcada hasta ' . self::num($medido) . ' dB';
            }
            $lineasUmbral[] = $texto;
        }
        if ($lineasUmbral !== []) {
            $y = self::ensureSpace($pdf, $y, 20 + 14 * count($lineasUmbral));
            $pdf->text(self::MARGIN, $y, 'Umbral', 12, true);
            $y += 18;
            foreach ($lineasUmbral as $linea) {
                $pdf->text(self::MARGIN, $y, $linea, 9);
                $y += 14;
            }
            $y += 10;
        }

        $y = self::technicalSection($pdf, $data, $y, $contentW);
        self::textSections($pdf, $data, $y, $contentW);

        return $pdf->output();
    }

    /**
     * Cuerpo del informe de otoscopia: qué marcó el alumno en cada
     * cuadrante de la membrana, más el CAE y sus observaciones, por oído.
     * Shape que manda el cliente (ver OtoscopiaInforme.InformeOtoscopia):
     * {"od": {"cuadrantes": {"anterior_superior": ["perforation", ...], ...},
     *         "cae": ["cae_cerumen", ...], "observaciones": "texto"},
     *  "oi": {...}}
     * Las claves son las de OtoReport (proyecto aparte) a propósito -- acá
     * se traducen a texto clínico para el PDF que lee el docente.
     */
    private static function otoscopiaBody(MiniPdf $pdf, array $data, float $y, float $contentW): float
    {
        // Mapas y no match(): el hosting corre PHP 7.4 (ver tipoLabel).
        $cuadrantes = [
            'anterior_superior' => 'Anterosuperior',
            'anterior_inferior' => 'Anteroinferior',
            'posterior_superior' => 'Posterosuperior',
            'posterior_inferior' => 'Posteroinferior',
            'pars_flaccida' => 'Pars flácida',
        ];
        $hallazgos = [
            'retraction' => 'Retracción',
            'perforation' => 'Perforación',
            'effusion' => 'Efusión',
            'tympanosclerosis' => 'Timpanoesclerosis',
            'cholesteatoma' => 'Colesteatoma',
            'inflammation' => 'Inflamación',
            'tube' => 'Tubo',
            'myringitis' => 'Miringitis',
        ];
        $cae = [
            'cae_normal' => 'Normal',
            'cae_cerumen' => 'Cerumen',
            'cae_edema' => 'Edema',
            'cae_otorrhea' => 'Otorrea',
            'cae_exostosis' => 'Exostosis',
        ];

        foreach (['od' => 'Oído derecho (OD)', 'oi' => 'Oído izquierdo (OI)'] as $lado => $titulo) {
            $oido = is_array($data[$lado] ?? null) ? $data[$lado] : [];
            $y = self::ensureSpace($pdf, $y, 60);
            $pdf->text(self::MARGIN, $y, $titulo, 12, true);
            $y += 18;

            $marcas = is_array($oido['cuadrantes'] ?? null) ? $oido['cuadrantes'] : [];
            if ($marcas === []) {
                $pdf->text(self::MARGIN + 12, $y, 'Membrana timpánica: sin hallazgos marcados.', 9);
                $y += 14;
            } else {
                // Recorre el mapa (no las marcas) para que el orden sea
                // siempre el mismo, entre por donde entre el alumno.
                foreach ($cuadrantes as $clave => $nombre) {
                    if (!isset($marcas[$clave])) {
                        continue;
                    }
                    // Un cuadrante trae VARIOS hallazgos (en una zona se ve
                    // más de una cosa). Los informes de la primera versión
                    // traían un solo string: se aceptan las dos formas, si
                    // no un informe viejo se imprimiría vacío.
                    $delCuadrante = is_array($marcas[$clave]) ? $marcas[$clave] : [$marcas[$clave]];
                    $etiquetas = [];
                    foreach ($delCuadrante as $hallazgo) {
                        $hallazgo = (string) $hallazgo;
                        if ($hallazgo === '') {
                            continue;
                        }
                        $etiquetas[] = $hallazgos[$hallazgo] ?? $hallazgo;
                    }
                    if ($etiquetas === []) {
                        continue;
                    }
                    $linea = "{$nombre}: " . implode(', ', $etiquetas);
                    $y = self::ensureSpace($pdf, $y, 14);
                    $pdf->text(self::MARGIN + 12, $y, $linea, 9);
                    $y += 14;
                }
            }

            $marcadosCae = [];
            foreach (is_array($oido['cae'] ?? null) ? $oido['cae'] : [] as $clave) {
                $marcadosCae[] = $cae[(string) $clave] ?? (string) $clave;
            }
            $y = self::ensureSpace($pdf, $y, 14);
            $pdf->text(
                self::MARGIN + 12,
                $y,
                'CAE: ' . ($marcadosCae === [] ? 'sin evaluar' : implode(', ', $marcadosCae)),
                9
            );
            $y += 14;

            $obs = trim((string) ($oido['observaciones'] ?? ''));
            if ($obs !== '') {
                $y = self::ensureSpace($pdf, $y, 30);
                $pdf->text(self::MARGIN + 12, $y, 'Observaciones:', 9, true);
                $y += 14;
                $y = $pdf->textBlock(self::MARGIN + 12, $y, $obs, $contentW - 12, 9);
            }
            $y += 16;
        }

        return $y;
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
        // switch y no match(): el hosting corre PHP 7.4 y match es de 8.0
        // (ver tests/test_php_baseline.php). Con match, este archivo ni
        // siquiera parseaba allá, así que report_pdf.php devolvía un 500.
        switch ($clave) {
            case 'teoae':
                return self::teoaeLines($r);
            case 'dpoae':
                return self::dpoaeLines($r);
            case 'soae':
                return self::soaeLines($r);
            case 'sfoae':
                return self::sfoaeLines($r);
            default:
                return [];
        }
    }

    private static function teoaeLines(array $r): array
    {
        $veredicto = !empty($r['overall_pass']) ? 'PASS' : 'REFER';
        // Informes anteriores al selector no traen el modo.
        $modo = ['no_lineal' => ' no lineal', 'lineal' => ' lineal'][$r['modo_click'] ?? ''] ?? '';
        $lineas = [sprintf(
            'Click%s %s dB SPL | %s promedios (%s barridos) | %s: %d/%d bandas sobre criterio',
            $modo,
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

    /**
     * Cuerpo del informe de tamizaje: qué dio cada oído y con qué.
     *
     * No lleva curvas ni imágenes -- un tamizaje no informa morfología,
     * informa PASA o REFIERE--, así que lo que hay que dejar por escrito es
     * el resultado, el nivel al que se tamizó y cuántos barridos costó: con
     * eso se puede discutir el procedimiento, que es lo que se evalúa.
     */
    /**
     * Cuerpo de los informes nasales: los gráficos del equipo y la tabla tal
     * como la vio el alumno. La tabla llega armada desde la app
     * (data['tabla'] = {cabeceras, filas}, ver nasal/equipos.py): el
     * backend no recalcula resistencias ni áreas, que salen del modelo de
     * RinoSim y solo existe en la app.
     */
    /**
     * El vasoconstrictor del informe nasal: true en los informes de antes,
     * o {lados, farmaco: {lado: nombre}, puff: {lado: n}} desde que se
     * elige en la app (nasal/sesion.py, vc_informe).
     */
    private static function nasalVasoconstrictor($vc): string
    {
        if (!is_array($vc)) {
            return $vc ? 'Con prueba de vasoconstrictor.' : '';
        }
        $siglas = ['D' => 'FND', 'I' => 'FNI'];
        $partes = [];
        foreach (is_array($vc['lados'] ?? null) ? $vc['lados'] : [] as $lado) {
            if (!isset($siglas[$lado])) {
                continue;
            }
            $farmaco = (string) ($vc['farmaco'][$lado] ?? 'vasoconstrictor');
            $puff = (int) ($vc['puff'][$lado] ?? 0);
            $partes[] = $farmaco . ($puff > 0 ? ', ' . $puff . ' puff' : '') . ' en ' . $siglas[$lado];
        }
        return $partes === [] ? '' : 'Vasoconstrictor: ' . implode('; ', $partes) . '.';
    }

    private static function nasalBody(MiniPdf $pdf, int $reportId, string $tipo, array $data, float $y, float $contentW): float
    {
        if ($tipo === 'RINOMANOMETRIA') {
            $imgW = ($contentW - 20) / 2;
            $imgH = $imgW * 0.75;
            $dibujo = false;
            foreach ([['rm_curva', 'Presión-flujo', 0.0], ['rm_resistencia', 'Resistencia según la presión', $imgW + 20]] as [$suf, $titulo, $dx]) {
                $ruta = ReportFile::imagePath($reportId, $suf);
                if (is_file($ruta)) {
                    $pdf->text(self::MARGIN + $dx, $y, $titulo, 9, true);
                    $pdf->image($ruta, self::MARGIN + $dx, $y + 4, $imgW, $imgH);
                    $dibujo = true;
                }
            }
            if ($dibujo) {
                $y += $imgH + 24;
            }
        } else {
            $ruta = ReportFile::imagePath($reportId, 'ra_curva');
            if (is_file($ruta)) {
                $imgH = $contentW * 0.45;
                $pdf->text(self::MARGIN, $y, 'Área-distancia', 9, true);
                $pdf->image($ruta, self::MARGIN, $y + 4, $contentW, $imgH);
                $y += $imgH + 24;
            }
        }

        $vc = self::nasalVasoconstrictor($data['vasoconstrictor'] ?? null);
        if ($vc !== '') {
            $y = $pdf->textBlock(self::MARGIN, $y, $vc, $contentW, 10);
            $y += 4;
        }
        // La sala como la midió el equipo (rinomanometría).
        $amb = is_array($data['ambiente'] ?? null) ? $data['ambiente'] : null;
        if ($amb !== null && isset($amb['temperatura'], $amb['humedad'])) {
            $linea = 'Sala: ' . str_replace('.', ',', sprintf('%.1f', (float) $amb['temperatura'])) . ' °C, humedad relativa '
                . (int) $amb['humedad'] . ' %';
            if (!empty($data['segundos'])) {
                $linea .= '; grabación de ' . (int) $data['segundos'] . ' s por fosa';
            }
            $pdf->text(self::MARGIN, $y, $linea . '.', 9);
            $y += 14;
        }
        $tabla = is_array($data['tabla'] ?? null) ? $data['tabla'] : [];
        $cabeceras = is_array($tabla['cabeceras'] ?? null) ? array_map('strval', $tabla['cabeceras']) : [];
        $filas = is_array($tabla['filas'] ?? null) ? $tabla['filas'] : [];
        if ($cabeceras !== [] && $filas !== []) {
            $y = self::ensureSpace($pdf, $y, 40.0);
            $pdf->text(self::MARGIN, $y, 'Resultados', 12, true);
            $y += 18;
            // La primera columna lleva el nombre de la fila (fosa, registro):
            // más ancha que las de números.
            $n = count($cabeceras);
            $primera = min(150.0, $contentW * 0.3);
            $resto = $n > 1 ? ($contentW - $primera) / ($n - 1) : 0.0;
            $fila = function (array $celdas, bool $negrita) use ($pdf, $primera, $resto, &$y, $n) {
                $x = self::MARGIN;
                for ($i = 0; $i < $n; $i++) {
                    $pdf->text($x, $y, (string) ($celdas[$i] ?? ''), 8, $negrita || $i === 0);
                    $x += $i === 0 ? $primera : $resto;
                }
                $y += 13;
            };
            $fila($cabeceras, true);
            foreach ($filas as $celdas) {
                if (is_array($celdas)) {
                    $y = self::ensureSpace($pdf, $y, 14.0);
                    $fila($celdas, false);
                }
            }
            $y += 8;
        }
        foreach (is_array($data['avisos'] ?? null) ? $data['avisos'] : [] as $aviso) {
            $y = $pdf->textBlock(self::MARGIN, $y, '• ' . (string) $aviso, $contentW, 9);
            $y += 2;
        }
        return $y + 10;
    }

    /** Qué dice cada valor del informe de rinoscopía (nasal/RinoscopiaWindow.py). */
    private const RINOSCOPIA_CAMPOS = [
        'tabique' => ['Tabique', ['centrado' => 'Centrado', 'desviado' => 'Desviado hacia esta fosa', 'espolon' => 'Espolón', 'no_se_ve' => 'No se ve']],
        'cornete_inferior' => ['Cornete inferior', ['normal' => 'Normal', 'hipertrofico' => 'Hipertrófico', 'contacta' => 'Contacta el tabique', 'no_se_ve' => 'No se ve']],
        'cornete_medio' => ['Cornete medio', ['normal' => 'Normal', 'aumentado' => 'Aumentado', 'no_se_ve' => 'No se ve']],
        'meato_medio' => ['Meato medio', ['libre' => 'Libre', 'polipos' => 'Pólipos', 'secrecion' => 'Secreción', 'no_se_ve' => 'No se ve']],
        'mucosa' => ['Mucosa', ['rosada' => 'Rosada', 'palida' => 'Pálida', 'violacea' => 'Violácea', 'roja' => 'Roja']],
        'secrecion' => ['Secreción', ['no' => 'Sin secreción', 'acuosa' => 'Acuosa', 'mucosa' => 'Mucosa', 'purulenta' => 'Purulenta']],
    ];

    /**
     * Cuerpo del informe de rinoscopía: lo que el alumno dice haber visto en
     * cada fosa, y cómo miró (qué fosa primero, en qué posiciones de la
     * cabeza: H25 pide la derecha primero y recta, 30° y 60°).
     */
    private static function rinoscopiaBody(MiniPdf $pdf, array $data, float $y, float $contentW): float
    {
        $pdf->text(self::MARGIN, $y, 'Hallazgos por fosa', 12, true);
        $y += 18;
        $cols = [150.0, ($contentW - 150.0) / 2, ($contentW - 150.0) / 2];
        $fila = function (array $celdas, bool $negrita) use ($pdf, $cols, &$y) {
            $x = self::MARGIN;
            foreach ($celdas as $i => $texto) {
                $pdf->text($x, $y, (string) $texto, 9, $negrita || $i === 0);
                $x += $cols[$i];
            }
            $y += 14;
        };
        $fila(['', 'Fosa derecha', 'Fosa izquierda'], true);
        $fosa = static function (string $lado) use ($data): array {
            return is_array($data[$lado] ?? null) ? $data[$lado] : [];
        };
        foreach (self::RINOSCOPIA_CAMPOS as $clave => [$rotulo, $textos]) {
            $celdas = [$rotulo];
            foreach (['D', 'I'] as $lado) {
                $v = (string) ($fosa($lado)[$clave] ?? '');
                $celdas[] = $v === '' ? '—' : ($textos[$v] ?? $v);
            }
            $fila($celdas, false);
        }
        $fila(['Perforación septal', !empty($fosa('D')['perforacion']) ? 'Sí' : 'No', !empty($fosa('I')['perforacion']) ? 'Sí' : 'No'], false);
        $y += 6;
        foreach (['D' => 'Fosa derecha', 'I' => 'Fosa izquierda'] as $lado => $nombre) {
            $obs = trim((string) ($fosa($lado)['observaciones'] ?? ''));
            if ($obs !== '') {
                $y = $pdf->textBlock(self::MARGIN, $y, "{$nombre}: {$obs}", $contentW, 9);
                $y += 4;
            }
        }
        $tec = is_array($data['tecnica'] ?? null) ? $data['tecnica'] : [];
        if ($tec !== []) {
            $y = self::ensureSpace($pdf, $y, 50.0);
            $pdf->text(self::MARGIN, $y + 6, 'Cómo se miró', 12, true);
            $y += 24;
            $primera = ['D' => 'la fosa derecha', 'I' => 'la fosa izquierda'][$tec['primera_fosa'] ?? ''] ?? '—';
            $pdf->text(self::MARGIN, $y, "Primero {$primera}.", 9);
            $y += 13;
            foreach (['D' => 'FND', 'I' => 'FNI'] as $lado => $sigla) {
                $pos = is_array($tec['posiciones'][$lado] ?? null) ? $tec['posiciones'][$lado] : [];
                $texto = $pos === [] ? 'no se miró' : implode(', ', array_map(static function ($g) {
                    return ((int) $g) . '°';
                }, $pos));
                $pdf->text(self::MARGIN, $y, "{$sigla}: cabeza en {$texto}.", 9);
                $y += 13;
            }
            if (!empty($data['vasoconstrictor'])) {
                $pdf->text(self::MARGIN, $y, 'Mirada con vasoconstrictor puesto.', 9);
                $y += 13;
            }
        }
        return $y + 10;
    }

    private static function aabrBody(MiniPdf $pdf, array $data, float $y, float $contentW): float
    {
        $pdf->text(self::MARGIN, $y, 'Resultado del tamizaje', 13, true);
        $y += 18;

        $resultados = is_array($data['resultados'] ?? null) ? $data['resultados'] : [];
        $cols = [70.0, 90.0, 120.0, 90.0];
        $encabezados = ['Oído', 'Resultado', 'Estímulo y nivel', 'Barridos'];
        $x = self::MARGIN;
        foreach ($encabezados as $i => $texto) {
            $pdf->text($x, $y, $texto, 10, true);
            $x += $cols[$i];
        }
        $y += 15;
        foreach (['OD', 'OI'] as $lado) {
            $r = is_array($resultados[$lado] ?? null) ? $resultados[$lado] : [];
            $veredicto = (string) ($r['veredicto'] ?? 'no realizado');
            $nivel = isset($r['nivel'])
                ? sprintf('%s a %d dB nHL', (string) ($r['estimulo'] ?? 'CE-Chirp'), (int) $r['nivel'])
                : '—';
            $barridos = isset($r['barridos']) ? (string) (int) $r['barridos'] : '—';
            $celdas = [$lado, $veredicto, $nivel, $barridos];
            $x = self::MARGIN;
            foreach ($celdas as $i => $texto) {
                $pdf->text($x, $y, $texto, 10, $i === 0);
                $x += $cols[$i];
            }
            $y += 15;
        }
        return $y + 10;
    }

    /**
     * Cuerpo del informe de electrococleografía.
     *
     * No reusa el del ABR porque no comparten NADA de lo que se informa:
     * ahí van latencias de cinco ondas e interpicos, y acá van dos razones
     * entre tres potenciales. Tampoco lleva el gráfico latencia-intensidad
     * (el ECochG no se registra en serie descendente: se hace a nivel alto,
     * que es donde el potencial de sumación es medible).
     *
     * Las medidas las manda el cliente ya calculadas desde las marcas del
     * alumno (ver ecochg.measure_complex): acá no se vuelve a medir nada.
     * Tampoco se interpreta -- qué razón es patológica lo dice quien
     * informa, no el PDF.
     */
    private static function ecochgBody(MiniPdf $pdf, int $reportId, array $data,
                                       float $y, float $contentW): float
    {
        $imgW = ($contentW - 20) / 2;
        $imgH = $imgW * 0.6;
        $dibujo = false;
        foreach ([['0', 'OD', self::MARGIN], ['1', 'OI', self::MARGIN + $imgW + 20]] as $lado) {
            $path = ReportFile::imagePath($reportId, $lado[0]);
            if (!is_file($path)) {
                continue;
            }
            $pdf->text($lado[2], $y, $lado[1], 9, true);
            $pdf->image($path, $lado[2], $y + 4, $imgW, $imgH);
            $dibujo = true;
        }
        if ($dibujo) {
            $y += $imgH + 24;
        }

        $curvas = is_array($data['curvas'] ?? null) ? $data['curvas'] : [];
        if (count($curvas) === 0) {
            return $y;
        }
        $y = self::ensureSpace($pdf, $y, 40);
        $pdf->text(self::MARGIN, $y, 'Medidas', 12, true);
        $y += 18;
        foreach ($curvas as $nombre => $curva) {
            if (!is_array($curva)) {
                continue;
            }
            $m = is_array($curva['ECochG'] ?? null) ? $curva['ECochG'] : [];
            $y = self::ensureSpace($pdf, $y, 40);
            $partes = [
                'PS ' . self::num($m['sp_amp'] ?? null) . ' µV',
                'PA ' . self::num($m['ap_amp'] ?? null) . ' µV',
                'PS/PA ' . self::num($m['sp_ap'] ?? null),
                'áreas ' . self::num($m['area_ratio'] ?? null),
            ];
            $pdf->text(self::MARGIN, $y,
                (string) $nombre . '  ' . implode('   ', $partes), 9);
            $y += 14;
            $detalle = [
                'lat PA ' . self::num($m['ap_lat'] ?? null) . ' ms',
                'ancho PA ' . self::num($m['ancho_pa'] ?? null) . ' ms',
                'complejo ' . self::num($m['ancho'] ?? null) . ' ms',
            ];
            // La microfónica solo si se marcó: se mide en rarefacción o
            // condensación (en alternada se cancela).
            if (isset($m['mc_amp'])) {
                $detalle[] = 'MC ' . self::num($m['mc_amp']) . ' µV p-p a '
                    . self::num($m['mc_lat'] ?? null) . ' ms';
            }
            $pdf->text(self::MARGIN + 12, $y, implode('   ', $detalle), 8);
            $y += 12;
            $setup = self::formatCurveSetup($curva);
            if ($setup !== '') {
                $pdf->text(self::MARGIN + 12, $y, $setup, 8);
                $y += 12;
            }
        }
        $y += 10;

        // Corrimiento por tasa: es una comparación entre dos curvas, así
        // que no puede ir en la línea de ninguna. Lo manda el cliente ya
        // resuelto (ver ecochg.rate_shift).
        $tasa = is_array($data['tasa'] ?? null) ? $data['tasa'] : [];
        if (isset($tasa['d_lat'])) {
            $y = self::ensureSpace($pdf, $y, 34);
            $pdf->text(self::MARGIN, $y, 'Corrimiento por tasa', 12, true);
            $y += 18;
            $pdf->text(self::MARGIN, $y,
                self::num($tasa['rate_lenta'] ?? null) . '/s → '
                . self::num($tasa['rate_rapida'] ?? null) . '/s:  latencia del PA '
                . self::num($tasa['d_lat']) . ' ms   amplitud '
                . self::num($tasa['d_amp_pct'] ?? null) . '%', 9);
            $y += 26;
        }

        // Separación del PA entre rarefacción y condensación: también es
        // una comparación entre dos curvas, una por oído (ver
        // ecochg.polarity_shift).
        $polaridad = is_array($data['polaridad'] ?? null) ? $data['polaridad'] : [];
        $filas = [];
        foreach ($polaridad as $p) {
            if (is_array($p) && isset($p['d_rc'])) {
                $filas[] = $p;
            }
        }
        if (count($filas) > 0) {
            $y = self::ensureSpace($pdf, $y, 20 + 14 * count($filas));
            $pdf->text(self::MARGIN, $y, 'Rarefacción / condensación', 12, true);
            $y += 18;
            // Dos decimales: el criterio es de centésimas (0,38 ms) y num()
            // redondea a uno.
            $ms = function ($v) {
                return is_numeric($v) ? number_format((float) $v, 2, ',', '') : 'N/D';
            };
            foreach ($filas as $p) {
                $pdf->text(self::MARGIN, $y,
                    (string) ($p['oido'] ?? '') . '  ' . self::num($p['int'] ?? null) . ' dB:  PA rar '
                    . $ms($p['lat_rar'] ?? null) . ' ms   cond '
                    . $ms($p['lat_cond'] ?? null) . ' ms   diferencia '
                    . $ms($p['d_rc']) . ' ms', 9);
                $y += 14;
            }
            $y += 12;
        }
        return $y;
    }

    /**
     * Cuerpo de los potenciales corticales y de latencia media (PEALM,
     * CAEP, P300, MMN): imagen por oído y, por oído, una tabla con las
     * marcas de la última captura medida. No interpreta nada (igual que
     * ecochgBody): el docente evalúa contra lo que marcó el alumno.
     *
     * Las curvas se llaman 'R1.C3', 'R1.Cz', ... : la R/L es el oído (R =
     * OD, L = OI), lo que va antes del punto es la captura y el canal es
     * $curva['canal']. Cada curva trae $curva['Cortical'] = {lat, amp}.
     */
    // Instrucción al paciente en el oddball: mismas claves y rótulos que
    // cortical.TAREA_LABELS en el cliente.
    private const TAREAS = [
        'ninguna' => 'Sin instrucción',
        'pasiva' => 'Pasiva: video sin sonido',
        'contar' => 'Contar los raros',
        'boton' => 'Apretar botón con el raro',
    ];

    private static function corticalBody(MiniPdf $pdf, int $reportId, array $data,
                                         float $y, float $contentW): float
    {
        $imgW = ($contentW - 20) / 2;
        $imgH = $imgW * 0.6;
        $dibujo = false;
        foreach ([['0', 'OD', self::MARGIN], ['1', 'OI', self::MARGIN + $imgW + 20]] as $lado) {
            $path = ReportFile::imagePath($reportId, $lado[0]);
            if (!is_file($path)) {
                continue;
            }
            $pdf->text($lado[2], $y, $lado[1], 9, true);
            $pdf->image($path, $lado[2], $y + 4, $imgW, $imgH);
            $dibujo = true;
        }
        if ($dibujo) {
            $y += $imgH + 24;
        }

        $curvas = is_array($data['curvas'] ?? null) ? $data['curvas'] : [];
        // oído => [grupo => [[canal, latencias, amplitudes], ...]]; el orden
        // de aparición manda (la última captura es la última del arreglo).
        $porOido = ['OD' => [], 'OI' => []];
        $tareas = ['OD' => [], 'OI' => []];
        foreach ($curvas as $nombre => $curva) {
            if (!is_array($curva) || !is_array($curva['Cortical'] ?? null)) {
                continue;
            }
            $nombre = (string) $nombre;
            $oido = strtoupper(substr($nombre, 0, 1)) === 'L' ? 'OI' : (strtoupper(substr($nombre, 0, 1)) === 'R' ? 'OD' : '');
            if ($oido === '') {
                continue;
            }
            $punto = strpos($nombre, '.');
            $grupo = $punto === false ? $nombre : substr($nombre, 0, $punto);
            $lat = is_array($curva['Cortical']['lat'] ?? null) ? $curva['Cortical']['lat'] : [];
            $amp = is_array($curva['Cortical']['amp'] ?? null) ? $curva['Cortical']['amp'] : [];
            $canal = (string) ($curva['canal'] ?? ($punto === false ? $nombre : substr($nombre, $punto + 1)));
            $porOido[$oido][$grupo][] = [$canal, $lat, $amp];
            // Instrucción al paciente del oddball (P300/MMN), por captura.
            if (isset($curva['tarea']) && is_string($curva['tarea'])) {
                $tareas[$oido][$grupo] = $curva['tarea'];
            }
        }

        $ordenMarcas = ['Na', 'Pa', 'Nb', 'Pb', 'P1', 'N1', 'P2', 'N2', 'P3', 'MMN'];
        $ordenAmps = ['Na-Pa', 'N1-P2', 'P3', 'MMN'];
        $fmtLat = function ($v) {
            if (!is_numeric($v)) {
                return '—';
            }
            return number_format((float) $v, (float) $v >= 100 ? 0 : 1, ',', '') . ' ms';
        };
        $fmtAmp = function ($v) {
            return is_numeric($v) ? number_format((float) $v, 2, ',', '') . ' µV' : '—';
        };

        foreach ($porOido as $oido => $grupos) {
            // Última captura que tenga alguna marca.
            $canales = null;
            $grupoElegido = null;
            foreach (array_reverse($grupos, true) as $g => $cs) {
                foreach ($cs as $c) {
                    if (count($c[1]) > 0 || count($c[2]) > 0) {
                        $canales = $cs;
                        $grupoElegido = $g;
                        break 2;
                    }
                }
            }
            if ($canales === null) {
                continue;
            }
            $filas = [];
            foreach ($ordenMarcas as $m) {
                $celdas = [];
                $hay = false;
                foreach ($canales as $c) {
                    $hay = $hay || isset($c[1][$m]);
                    $celdas[] = $fmtLat($c[1][$m] ?? null);
                }
                if ($hay) {
                    $filas[] = [$m, $celdas];
                }
            }
            foreach ($ordenAmps as $a) {
                $celdas = [];
                $hay = false;
                foreach ($canales as $c) {
                    $hay = $hay || isset($c[2][$a]);
                    $celdas[] = $fmtAmp($c[2][$a] ?? null);
                }
                if ($hay) {
                    $filas[] = [$a, $celdas];
                }
            }
            if (count($filas) === 0) {
                continue;
            }
            $y = self::ensureSpace($pdf, $y, 36 + 13 * (count($filas) + 1));
            $pdf->text(self::MARGIN, $y, 'Medidas ' . $oido, 12, true);
            $y += 18;
            $tarea = $tareas[$oido][$grupoElegido] ?? null;
            if ($tarea !== null) {
                $pdf->text(self::MARGIN, $y, 'Tarea del paciente: '
                    . (self::TAREAS[$tarea] ?? $tarea), 9);
                $y += 14;
            }
            $colW = min(90.0, ($contentW - 70) / max(1, count($canales)));
            $pdf->text(self::MARGIN, $y, 'Marca', 9, true);
            foreach ($canales as $i => $c) {
                $pdf->text(self::MARGIN + 70 + $i * $colW, $y, $c[0], 9, true);
            }
            $y += 13;
            foreach ($filas as $fila) {
                $y = self::ensureSpace($pdf, $y, 14);
                $pdf->text(self::MARGIN, $y, $fila[0], 9);
                foreach ($fila[1] as $i => $celda) {
                    $pdf->text(self::MARGIN + 70 + $i * $colW, $y, $celda, 9);
                }
                $y += 13;
            }
            $y += 10;
        }

        // Efectos de lateralidad (solo PEALM): comparaciones entre
        // electrodos/oídos, resueltas por el cliente.
        $efectos = is_array($data['efectos'] ?? null) ? $data['efectos'] : [];
        $lineas = [];
        if (isset($efectos['electrodo']) && is_numeric($efectos['electrodo'])) {
            $lineas[] = 'Efecto electrodo (C3/C4): ' . round((float) $efectos['electrodo'] * 100)
                . '% menor en hemisferio ' . (string) ($efectos['hemisferio'] ?? 'N/D');
        }
        if (isset($efectos['oido']) && is_numeric($efectos['oido'])) {
            $lineas[] = 'Efecto oído (OD/OI): ' . round((float) $efectos['oido'] * 100)
                . '% menor en ' . (string) ($efectos['oido_menor'] ?? 'N/D');
        }
        foreach ($lineas as $l) {
            $y = self::ensureSpace($pdf, $y, 16);
            $pdf->text(self::MARGIN, $y, $l, 9);
            $y += 14;
        }

        // Respuesta del paciente a la tarea (solo P300), por oído: conteo de
        // raros o botón (aciertos y falsas alarmas).
        $conteo = is_array($data['conteo'] ?? null) ? $data['conteo'] : [];
        foreach (['OD', 'OI'] as $oido) {
            $c = $conteo[$oido] ?? ($conteo[strtolower($oido)] ?? null);
            if (is_array($c) && isset($c['aciertos'])) {
                $texto = "Botón del paciente ({$oido}): " . self::num($c['aciertos'])
                    . ' aciertos de ' . self::num($c['reales'] ?? null) . ' raros, '
                    . self::num($c['falsas'] ?? 0) . ' falsas alarmas';
            } elseif (is_array($c) && isset($c['dice'])) {
                $texto = "Conteo del paciente ({$oido}): dice " . self::num($c['dice'])
                    . ' de ' . self::num($c['reales'] ?? null) . ' raros presentados';
            } else {
                continue;
            }
            $y = self::ensureSpace($pdf, $y, 16);
            $pdf->text(self::MARGIN, $y, $texto, 9);
            $y += 14;
        }
        return $y + 8;
    }

    /**
     * Cuerpo del informe de ASSR (potenciales de estado estable de 80 Hz).
     *
     * El cliente manda data['assr'] (ver abr/assr.py Recording.snapshot):
     * por portadora ('OD:500', ...) la estadística de la línea (amplitud, ruido
     * de los bins vecinos, razón F, p, estado), el nivel en que quedó, el
     * historial de niveles probados y el umbral crudo (dB HL) y corregido
     * (dB eHL). Las cuatro vistas del panel -- rastro, espectro, vectores y
     * audiograma -- van como imágenes (assr_rastro/fft/polar/audio).
     */
    private static function assrBody(MiniPdf $pdf, int $reportId, array $data,
                                     float $y, float $contentW): float
    {
        $imgW = ($contentW - 20) / 2;
        $imgH = $imgW * 0.6;
        $vistas = [
            ['assr_rastro', 'Rastro (portadora elegida)'],
            ['assr_fft', 'Espectro (FFT)'],
            ['assr_polar', 'Vectores'],
            ['assr_audio', 'Audiograma estimado (dB eHL)'],
        ];
        // Cada vista conserva su proporción (el gráfico de vectores es
        // cuadrado, el espectro apaisado); la fila ocupa lo de la más alta.
        $dibujadas = 0;
        $altoFila = 0.0;
        foreach ($vistas as $v) {
            $path = ReportFile::imagePath($reportId, $v[0]);
            if (!is_file($path)) {
                continue;
            }
            $alto = $imgH;
            $tam = @getimagesize($path);
            if ($tam !== false && $tam[0] > 0) {
                $alto = min($imgW * $tam[1] / $tam[0], $imgW * 1.1);
            }
            if ($dibujadas % 2 === 0) {
                $y = self::ensureSpace($pdf, $y, $imgH + 24);
                $altoFila = 0.0;
            }
            $x = self::MARGIN + ($dibujadas % 2) * ($imgW + 20);
            $pdf->text($x, $y, $v[1], 9, true);
            $pdf->image($path, $x, $y + 4, $imgW, $alto);
            $altoFila = max($altoFila, $alto);
            $dibujadas++;
            if ($dibujadas % 2 === 0) {
                $y += $altoFila + 24;
            }
        }
        if ($dibujadas % 2 === 1) {
            $y += $altoFila + 24;
        }

        $assr = is_array($data['assr'] ?? null) ? $data['assr'] : [];
        $canales = is_array($assr['canales'] ?? null) ? $assr['canales'] : [];
        if ($canales === []) {
            $pdf->text(self::MARGIN, $y, 'Sin registro de portadoras.', 9);
            return $y + 16;
        }

        $y = self::ensureSpace($pdf, $y, 30);
        $segundos = (int) round(((float) ($assr['n'] ?? 0)) * 1.024);
        $pdf->text(self::MARGIN, $y, 'Registro: ' . self::num((int) ($assr['n'] ?? 0))
            . ' épocas aceptadas (' . sprintf('%02d:%02d', intdiv($segundos, 60), $segundos % 60)
            . '), ' . self::num((int) ($assr['rechazadas'] ?? 0)) . ' rechazadas por artefacto', 9);
        $y += 16;

        $fmt = function ($v, int $dec = 0): string {
            return is_numeric($v) ? number_format((float) $v, $dec, ',', '') : '—';
        };
        $fmtP = function ($v): string {
            if (!is_numeric($v)) {
                return '—';
            }
            return (float) $v < 0.001 ? '<0,001' : number_format((float) $v, 3, ',', '');
        };
        $frecs = [500, 1000, 2000, 4000];
        // Columnas: x relativo, rótulo.
        $cols = [
            [0, 'Portadora'], [62, 'Nivel'], [100, 'Épocas'], [140, 'Amp. nV'],
            [190, 'Ruido nV'], [245, 'F'], [280, 'p'], [330, 'Estado'],
            [400, 'Umbral HL'], [465, 'eHL'],
        ];
        foreach (['OD', 'OI'] as $oido) {
            $filas = [];
            foreach ($frecs as $f) {
                $c = $canales[$oido . ':' . $f] ?? null;
                if (!is_array($c)) {
                    continue;
                }
                $st = is_array($c['stats'] ?? null) ? $c['stats'] : [];
                $filas[] = [
                    ($f >= 1000 ? ($f / 1000) . ' kHz' : $f . ' Hz'),
                    $fmt($c['nivel'] ?? null) . ' dB',
                    $fmt($st['n'] ?? null),
                    $fmt($st['amp_nv'] ?? null),
                    $fmt($st['noise_nv'] ?? null),
                    $fmt($st['f_ratio'] ?? null, 1),
                    $fmtP($st['p'] ?? null),
                    (string) ($st['estado'] ?? '—'),
                    isset($c['umbral_hl']) && is_numeric($c['umbral_hl']) ? $fmt($c['umbral_hl']) . ' dB' : 'sin resp.',
                    isset($c['umbral_ehl']) && is_numeric($c['umbral_ehl']) ? $fmt($c['umbral_ehl']) . ' dB' : 'sin resp.',
                ];
            }
            if ($filas === []) {
                continue;
            }
            $y = self::ensureSpace($pdf, $y, 36 + 13 * (count($filas) + 1));
            $pdf->text(self::MARGIN, $y, 'Portadoras ' . $oido, 12, true);
            $y += 18;
            foreach ($cols as $i => $col) {
                $pdf->text(self::MARGIN + $col[0], $y, $col[1], 8, true);
            }
            $y += 13;
            foreach ($filas as $fila) {
                foreach ($cols as $i => $col) {
                    $pdf->text(self::MARGIN + $col[0], $y, $fila[$i], 8);
                }
                $y += 13;
            }
            $y += 10;
        }

        $corr = is_array($assr['correccion'] ?? null) ? $assr['correccion'] : [];
        if ($corr !== []) {
            $partes = [];
            foreach ($frecs as $f) {
                if (isset($corr[(string) $f]) && is_numeric($corr[(string) $f])) {
                    $partes[] = ($f >= 1000 ? ($f / 1000) . ' kHz' : $f . ' Hz') . ' ' . $fmt($corr[(string) $f]) . ' dB';
                }
            }
            if ($partes !== []) {
                $y = self::ensureSpace($pdf, $y, 16);
                $pdf->text(self::MARGIN, $y, 'Corrección a eHL aplicada: ' . implode(', ', $partes), 9);
                $y += 14;
            }
        }
        return $y + 8;
    }

    private static function tipoLabel(string $tipo): string
    {
        // Mapa y no match(): el hosting corre PHP 7.4 (ver el otro caso en
        // eoaLines y tests/test_php_baseline.php).
        $etiquetas = [
            'ABR' => 'PEATC (ABR)',
            'AABR' => 'Tamizaje auditivo automatizado (AABR)',
            'EOA' => 'Emisiones Otoacústicas',
            'VEMP' => 'Potenciales Evocados Vestibulares Miogénicos',
            'ELECTROCOCLEO' => 'Electrococleografía',
            'PEALM' => 'Potencial de latencia media (PEALM)',
            'CAEP' => 'Potencial cortical (P1-N1-P2)',
            'P300' => 'P300',
            'MMN' => 'Negatividad de disparidad (MMN)',
            'ASSR' => 'Potenciales de estado estable (ASSR)',
            'OTOSCOPIA' => 'Otoscopia',
            'RINOMANOMETRIA' => 'Rinomanometría anterior',
            'RINOMETRIA' => 'Rinometría acústica',
            'RINOSCOPIA' => 'Rinoscopía anterior',
        ];
        return $etiquetas[$tipo] ?? $tipo;
    }

    /**
     * Condiciones de registro: COMO se tomo el examen, no que dio.
     *
     * Sin esto el informe deja al docente evaluando el resultado sin poder
     * ver el procedimiento: no hay forma de distinguir un registro bien
     * hecho de uno tomado con los electrodos a 8 kOhm, sin tierra o con el
     * rechazo de artefacto apagado. Lo manda el cliente en data['tecnica']
     * (ver AbrMainWindow.recording_conditions); los informes viejos no lo
     * traen y el bloque simplemente no se dibuja.
     */
    private static function technicalSection(MiniPdf $pdf, array $data, float $y, float $contentW): float
    {
        $tec = is_array($data['tecnica'] ?? null) ? $data['tecnica'] : [];
        if ($tec === []) {
            return $y;
        }

        $lineas = [];
        $equipo = array_filter([
            self::num($tec['transductor'] ?? null) !== 'N/D' ? "Transductor: {$tec['transductor']}" : null,
            isset($tec['montaje']) ? "Montaje: {$tec['montaje']}" : null,
            isset($tec['ventana_ms']) ? 'Ventana: ' . self::num($tec['ventana_ms']) . ' ms' : null,
        ]);
        if ($equipo !== []) {
            $lineas[] = implode('   ', $equipo);
        }

        $electrodos = is_array($tec['electrodos'] ?? null) ? $tec['electrodos'] : [];
        $impedancias = is_array($tec['impedancias_kohm'] ?? null) ? $tec['impedancias_kohm'] : [];
        if ($electrodos !== [] || $impedancias !== []) {
            $rotulos = ['vertex' => 'Activo', 'right' => 'Ref. der', 'left' => 'Ref. izq', 'ground' => 'Tierra'];
            $partes = [];
            foreach ($rotulos as $clave => $rotulo) {
                $pos = $electrodos[$clave] ?? null;
                $imp = $impedancias[$clave] ?? null;
                if ($pos === null && $imp === null) {
                    continue;
                }
                $texto = $rotulo . ' ' . self::num($pos);
                if ($imp !== null) {
                    $texto .= ' (' . self::num($imp) . ' kOhm)';
                }
                $partes[] = $texto;
            }
            if ($partes !== []) {
                $lineas[] = 'Electrodos: ' . implode('   ', $partes);
            }
            if (isset($tec['impedancia_max_kohm'])) {
                $estado = ($tec['impedancia_en_norma'] ?? false) ? 'dentro de norma' : 'FUERA DE NORMA';
                $lineas[] = 'Impedancia: peor ' . self::num($tec['impedancia_max_kohm'])
                    . ' kOhm, desbalance ' . self::num($tec['impedancia_desbalance_kohm'] ?? null)
                    . ' kOhm - ' . $estado;
            }
        }

        $prom = array_filter([
            array_key_exists('rechazo_artefacto_uv', $tec)
                ? 'Rechazo de artefacto: ' . ((float) $tec['rechazo_artefacto_uv'] > 0
                    ? '±' . self::num($tec['rechazo_artefacto_uv']) . ' µV' : 'desactivado')
                : null,
            !empty($tec['criterio_fsp']) ? 'Criterio FSP: ' . self::num($tec['criterio_fsp']) : null,
            isset($tec['ruido_residual_objetivo_nv'])
                ? 'Ruido objetivo: ' . self::num($tec['ruido_residual_objetivo_nv']) . ' nV' : null,
        ]);
        if ($prom !== []) {
            $lineas[] = implode('   ', $prom);
        }

        $medido = array_filter([
            isset($tec['barridos_presentados'])
                ? "Barridos: {$tec['barridos_presentados']} presentados / "
                  . ($tec['barridos_aceptados'] ?? 'N/D') . ' aceptados' : null,
            isset($tec['fsp']) ? 'FSP ' . self::num($tec['fsp']) : null,
            isset($tec['ruido_residual_nv']) ? 'ruido ' . self::num($tec['ruido_residual_nv']) . ' nV' : null,
            isset($tec['replicabilidad'])
                ? 'replicabilidad ' . number_format((float) $tec['replicabilidad'], 2, ',', '')
                : null,
        ]);
        if ($medido !== []) {
            $lineas[] = implode('   ', $medido);
        }

        $avisos = [];
        if (!empty($tec['interferencia_red'])) {
            $avisos[] = 'interferencia de red (50 Hz)';
        }
        if (array_key_exists('canal_contralateral', $tec) && !$tec['canal_contralateral']) {
            $avisos[] = 'sin canal contralateral';
        }
        if ($avisos !== []) {
            $lineas[] = 'Observaciones del equipo: ' . implode(', ', $avisos);
        }

        $y = self::ensureSpace($pdf, $y, 22 + count($lineas) * 13);
        $pdf->text(self::MARGIN, $y, 'Condiciones de registro', 12, true);
        $y += 18;
        foreach ($lineas as $linea) {
            $pdf->text(self::MARGIN, $y, $linea, 9);
            $y += 13;
        }

        return $y + 10;
    }

    /** Parametros con los que se registro una curva puntual. */
    private static function formatCurveSetup(array $curva): string
    {
        $partes = [];
        if (!empty($curva['stim'])) {
            $partes[] = (string) $curva['stim'];
        }
        if (!empty($curva['pol'])) {
            $partes[] = (string) $curva['pol'];
        }
        if (isset($curva['rate'])) {
            $partes[] = self::num($curva['rate']) . '/s';
        }
        if (isset($curva['filter_passhigh']) || isset($curva['filter_down'])) {
            $partes[] = self::num($curva['filter_passhigh'] ?? null) . '-'
                . self::num($curva['filter_down'] ?? null) . ' Hz';
        }
        if (!empty($curva['mkg'])) {
            $partes[] = 'masking ' . self::num($curva['mkg']) . ' dB';
        }
        // VEMP: el estímulo es tone burst (la frecuencia va en 'freq') y
        // sin la maniobra y el EMG con el que se registró, una respuesta
        // ausente no se puede distinguir de un paciente que no contrajo.
        if (!empty($curva['freq'])) {
            $partes[] = 'tone burst ' . $curva['freq'];
        }
        if (!empty($curva['maniobra'])) {
            $partes[] = (string) $curva['maniobra'];
        }
        if (isset($curva['emg_uv'])) {
            $emg = 'EMG ' . self::num($curva['emg_uv']) . ' µV';
            if (array_key_exists('emg_ok', $curva) && !$curva['emg_ok']) {
                $emg .= ' (FUERA DE RANGO)';
            }
            $partes[] = $emg;
        }
        if (isset($curva['p2p']) && is_numeric($curva['p2p'])) {
            $partes[] = 'p-p ' . self::num($curva['p2p']) . ' µV';
        }
        // La amplitud CORREGIDA (pico-pico / EMG rectificado) es la única
        // comparable entre registros: la cruda depende de cuánto contrajo el
        // paciente en ese registro (ver src/vemp/session.py).
        if (isset($curva['p2p_corregida']) && is_numeric($curva['p2p_corregida'])) {
            $partes[] = 'p-p corr. ' . self::num($curva['p2p_corregida']);
        }
        if (!empty($curva['transductor'])) {
            $partes[] = (string) $curva['transductor'];
        }
        $tec = is_array($curva['tecnica'] ?? null) ? $curva['tecnica'] : [];
        if (isset($tec['barridos_aceptados'])) {
            $linea = $tec['barridos_aceptados'] . ' barridos aceptados';
            if (!empty($tec['barridos_rechazados'])) {
                $linea .= ' (' . $tec['barridos_rechazados'] . ' rechazados)';
            }
            $partes[] = $linea;
        }
        if (isset($tec['impedancia_max_kohm'])) {
            $partes[] = 'imp. máx ' . self::num($tec['impedancia_max_kohm']) . ' kOhm';
        }

        return $partes === [] ? '' : implode('  ·  ', $partes);
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
