<?php

declare(strict_types=1);

require_once __DIR__ . '/HelveticaWidths.php';
require_once __DIR__ . '/MiniPdf.php';
require_once __DIR__ . '/CaseBuilder.php';
require_once __DIR__ . '/CaseProfile.php';
require_once __DIR__ . '/CaseCharts.php';
require_once __DIR__ . '/PdfImage.php';
require_once __DIR__ . '/PatientPhoto.php';
require_once __DIR__ . '/OtoscopiaPhoto.php';

/**
 * El PDF de la ficha completa de un caso: todo lo que el docente cargó (o
 * derivó del perfil) en un documento imprimible, con los mismos gráficos
 * que ve en el editor.
 *
 * No es el informe del ALUMNO (eso es ReportPdfBuilder, que arma lo que el
 * estudiante entrega tras atender el caso): esto es la hoja de respuestas
 * del caso -- audiograma, impedanciometría, acumetría, logoaudiometría,
 * supraliminares, ABR, OEA y VEMP-- para revisar, archivar o repartir en
 * clase.
 *
 * Es función pura sobre arrays: entra `cases.data` y sale el PDF en bytes.
 * No toca PDO ni $_GET, así se puede testear sin base de datos (ver
 * tests/test_case_sheet_pdf.php).
 */
final class CaseSheetPdf
{
    private const MARGEN = 40.0;
    /** Y a partir de la cual hay que cortar la página. */
    private const PIE = 40.0;

    /**
     * Alto de la letra sobre la línea base, como fracción del cuerpo. La Y
     * del documento apunta al BORDE SUPERIOR del bloque que sigue, y el PDF
     * escribe desde la línea base: sin este corrimiento, todo párrafo que
     * viniera después de una tabla o de un gráfico se le montaba encima.
     */
    private const ASCENDENTE = 0.8;

    private const GRIS_TITULO = '#222222';
    private const GRIS_TEXTO = '#333333';
    private const GRIS_SUAVE = '#666666';
    private const FONDO_TABLA = '#eeeeee';
    private const FONDO_CABECERA = '#dde3ea';

    /** Etiquetas cortas del patrón retrococlear (ver views/case/_perfil.php). */
    private const NEURAL_LABELS = [
        'i_iii_ms' => 'Prolongación I-III (ms)',
        'iii_v_ms' => 'Prolongación III-V (ms)',
        'global_delay_ms' => 'Retraso global (ms)',
        'v_i_factor' => 'Razón V/I',
        'bloqueo' => 'Bloqueo',
        'microfonica' => 'Microfónico coclear',
        'desincronia' => 'Desincronía',
        'sensibilidad_tasa' => 'Sensibilidad a la tasa',
    ];

    private MiniPdf $pdf;
    private float $y;
    private float $anchoContenido;
    private string $encabezadoCorrido;
    private string $caseId;
    /** Modo alumno: sin perfil ni parámetros del generador (ver build()). */
    private bool $paraAlumno;

    private function __construct(string $caseId, string $encabezadoCorrido, bool $paraAlumno)
    {
        $this->pdf = new MiniPdf();
        $this->anchoContenido = $this->pdf->pageWidth() - 2 * self::MARGEN;
        $this->y = self::MARGEN;
        $this->caseId = $caseId;
        $this->encabezadoCorrido = $encabezadoCorrido;
        $this->paraAlumno = $paraAlumno;
    }

    /**
     * @param array<string,mixed> $data cases.data
     * @param array{nombre?:string,rut?:string,fecha_nac?:string} $patient
     * @param bool $paraAlumno versión repartible: se va el perfil auditivo
     *        (dónde está la lesión) y todo parámetro del generador --patrón
     *        retrococlear, condiciones de captura, atenuación y sello de la
     *        OEA, desviaciones por onda--. Queda lo que el alumno podría
     *        medir él mismo. Lo clínico no se recorta: el que decide qué
     *        repartir y cuándo es el docente.
     * @return string bytes del PDF
     */
    public static function build(string $caseId, array $data, array $patient = [], string $emisor = '', string $fecha = '', bool $paraAlumno = false): string
    {
        $nombre = trim((string) ($patient['nombre'] ?? ''));
        $doc = new self($caseId, 'Ficha ' . $caseId . ($nombre !== '' ? ' - ' . $nombre : ''), $paraAlumno);
        $doc->portada($caseId, $data, $patient, $emisor, $fecha !== '' ? $fecha : date('d-m-Y'));
        $doc->resumenPorOido($data);
        $doc->audiometria($data);
        $doc->acumetria($data);
        $doc->impedanciometria($data);
        $doc->logoaudiometria($data);
        $doc->supraliminares($data);
        $doc->abr($data);
        $doc->eoas($data);
        $doc->vemp($data);
        $doc->clinica($data);
        return $doc->pdf->output();
    }

    // -----------------------------------------------------------------
    // Secciones
    // -----------------------------------------------------------------

    private function portada(string $caseId, array $data, array $patient, string $emisor, string $fecha): void
    {
        $this->pdf->text(self::MARGEN, $this->y + 4, 'Ficha del caso', 19, true, self::GRIS_TITULO);
        $this->pdf->textRight(self::MARGEN + $this->anchoContenido, $this->y + 4, $caseId, 13, true, self::GRIS_SUAVE);
        $this->y += 14;
        $this->pdf->line(self::MARGEN, $this->y, self::MARGEN + $this->anchoContenido, $this->y, 1.2, self::GRIS_TITULO);
        $this->y += 16;

        // Foto del paciente a la derecha de los datos, si el caso la tiene.
        // El avatar es png (PatientPhoto) y el PDF solo lleva JPEG: lo
        // convierte PdfImage, y si el servidor no tiene GD simplemente no
        // hay foto -- la ficha no depende de ella.
        $yDatos = $this->y;
        $foto = PdfImage::jpegBytes(PatientPhoto::avatarPath($this->caseId))
            ?? PdfImage::jpegBytes(PatientPhoto::originalPath($this->caseId));
        if ($foto !== null) {
            $ladoFoto = 62.0;
            $altoFoto = min($ladoFoto, PdfImage::altoProporcional($foto, $ladoFoto));
            $xFoto = self::MARGEN + $this->anchoContenido - $ladoFoto;
            $this->pdf->imageJpeg(
                $foto['data'],
                $foto['w'],
                $foto['h'],
                'paciente:' . $this->caseId,
                $xFoto,
                $yDatos,
                $ladoFoto,
                $altoFoto
            );
            $this->pdf->rect($xFoto, $yDatos, $ladoFoto, $altoFoto, 0.5, self::GRIS_SUAVE);
        }

        $nombre = trim(((string) ($patient['nombre'] ?? '')) . ' ' . ((string) ($patient['apellido'] ?? '')));
        $edad = isset($data['edad']) ? (string) $data['edad'] . ' años' : 'N/D';
        $sexo = ((int) ($data['gender'] ?? 0)) === 1 ? 'Femenino' : 'Masculino';

        $this->filasKv([
            ['Paciente', $nombre !== '' ? $nombre : 'Sin cita asociada'],
            ['RUT', (string) ($patient['rut'] ?? 'N/D')],
            ['Edad / sexo', $edad . '  ·  ' . $sexo],
            ['Emitido', $fecha . ($emisor !== '' ? '  ·  ' . $emisor : '')],
        ]);
        $this->y += 6;
    }

    /**
     * Lo que el perfil dice de cada oído, que es el encabezado clínico del
     * caso: dónde está la lesión y cuánto pesa. El promedio va en las dos
     * versiones que se usan --PTP clásico (500-1k-2k) y promedio BIAP
     * (500-1k-2k-4k)-- porque el grado del catálogo se calcula con el
     * segundo y el informe de un alumno suele citar el primero.
     */
    private function resumenPorOido(array $data): void
    {
        // El perfil dice DÓNDE está la lesión: es la respuesta del ejercicio,
        // no un resultado que el alumno pueda medir.
        if ($this->paraAlumno) {
            return;
        }
        $this->titulo('Perfil auditivo');

        $perfil = CaseProfile::normalize($data);
        $aerea = self::desarmar($data['Aerea'] ?? []);
        $osea = self::desarmar($data['Osea'] ?? []);

        $filas = [['', 'OD', 'OI']];
        $porLado = [];
        foreach (['od' => 'OD', 'oi' => 'OI'] as $ladoForm => $lado) {
            $idx = $ladoForm === 'od' ? 0 : 1;
            $decomp = CaseProfile::decompose(
                $data['Aerea'] ?? [],
                $data['Osea'] ?? [],
                $idx,
                (float) $perfil[$lado]['cce_pct']
            );
            $retro = $perfil[$lado]['retro'];
            $porLado[$ladoForm] = [
                'tipo' => CaseProfile::derivedType($decomp, (float) $perfil[$lado]['cce_pct'], $retro),
                'ptp' => self::promedio($aerea[$ladoForm], [2, 3, 4]),
                'biap' => self::promedio($aerea[$ladoForm], [2, 3, 4, 6]),
                'biapOsea' => self::promedio($osea[$ladoForm], [2, 3, 4, 6]),
                'cce' => (float) $perfil[$lado]['cce_pct'],
                'retroActivo' => CaseProfile::retroActivo($retro),
            ];
        }

        $filas[] = ['Clasificación', self::tipoLabel($porLado['od']['tipo']), self::tipoLabel($porLado['oi']['tipo'])];
        $filas[] = [
            'PTP aéreo (500-1k-2k)',
            self::db($porLado['od']['ptp']),
            self::db($porLado['oi']['ptp']),
        ];
        $filas[] = [
            'Promedio BIAP aéreo',
            self::db($porLado['od']['biap']) . '  (' . self::grado($porLado['od']['biap']) . ')',
            self::db($porLado['oi']['biap']) . '  (' . self::grado($porLado['oi']['biap']) . ')',
        ];
        $filas[] = [
            'Promedio BIAP óseo',
            self::db($porLado['od']['biapOsea']),
            self::db($porLado['oi']['biapOsea']),
        ];
        $filas[] = [
            'Gap aéreo-óseo (promedio)',
            self::db($porLado['od']['biap'] - $porLado['od']['biapOsea']),
            self::db($porLado['oi']['biap'] - $porLado['oi']['biapOsea']),
        ];
        $filas[] = [
            'Componente coclear (CCE)',
            round($porLado['od']['cce']) . ' %',
            round($porLado['oi']['cce']) . ' %',
        ];
        $filas[] = [
            'Patrón retrococlear',
            $porLado['od']['retroActivo'] ? 'Sí (ver ABR)' : 'No',
            $porLado['oi']['retroActivo'] ? 'Sí (ver ABR)' : 'No',
        ];

        $this->tabla($filas, [0.36, 0.32, 0.32], true);

        $autos = [];
        foreach ($perfil['auto'] as $modulo => $activo) {
            if ($activo) {
                $autos[] = $modulo;
            }
        }
        $this->parrafo(
            'Módulos derivados del perfil: ' . ($autos === [] ? 'ninguno (todo cargado a mano)' : implode(', ', $autos)) . '.',
            7.5
        );
    }

    private function audiometria(array $data): void
    {
        $this->titulo('Audiometría tonal', 250.0);

        $aerea = self::desarmar($data['Aerea'] ?? []);
        $osea = self::desarmar($data['Osea'] ?? []);
        $ldl = self::desarmar($data['LDL'] ?? []);
        // "LDL no medido" se guarda como 130 en las nueve frecuencias (ver
        // case_create.php): si ninguna difiere, ese oído no tiene LDL.
        $ldlMedido = [];
        foreach (['od', 'oi'] as $lado) {
            $ldlMedido[$lado] = count(array_filter($ldl[$lado], static fn ($v) => (int) $v !== 130)) > 0;
        }

        $alto = 210.0;
        $this->espacio($alto + 26);
        CaseCharts::audiogram($this->pdf, self::MARGEN, $this->y, $this->anchoContenido * 0.62, $alto, $aerea, $osea, $ldl, $ldlMedido);

        // Al lado del gráfico, la leyenda de símbolos: un audiograma sin
        // leyenda obliga a recordar la convención de memoria.
        $xLeyenda = self::MARGEN + $this->anchoContenido * 0.66;
        $anchoLeyenda = $this->anchoContenido * 0.34;
        $yLeyenda = CaseCharts::symbolLegend($this->pdf, $xLeyenda, $this->y + 16, $anchoLeyenda);
        $this->pdf->textBlock(
            $xLeyenda,
            $yLeyenda + 6,
            'El enmascaramiento no se carga a mano: se infiere de la atenuación interaural por frecuencia y del gap del propio oído.',
            $anchoLeyenda - 4,
            6.5,
            false,
            8,
            self::GRIS_SUAVE
        );
        $this->y += $alto + 10;

        // Tabla de umbrales: lo que el gráfico muestra, en números.
        $filas = [array_merge([''], array_map(static fn ($hz) => self::hz($hz), CaseBuilder::FREQUENCIES))];
        foreach ([
            ['Aérea OD', $aerea['od']], ['Ósea OD', $osea['od']],
            ['Aérea OI', $aerea['oi']], ['Ósea OI', $osea['oi']],
        ] as [$rotulo, $vals]) {
            $filas[] = array_merge([$rotulo], array_map(static fn ($v) => (string) (int) $v, $vals));
        }
        foreach (['od' => 'Gap OD', 'oi' => 'Gap OI'] as $lado => $rotulo) {
            $gap = [];
            foreach (CaseBuilder::FREQUENCIES as $i => $hz) {
                $gap[] = (string) (int) round($aerea[$lado][$i] - $osea[$lado][$i]);
            }
            $filas[] = array_merge([$rotulo], $gap);
        }
        foreach (['od', 'oi'] as $lado) {
            if ($ldlMedido[$lado]) {
                $filas[] = array_merge(['LDL ' . strtoupper($lado)], array_map(static fn ($v) => (string) (int) $v, $ldl[$lado]));
            }
        }
        $anchos = array_merge([0.16], array_fill(0, count(CaseBuilder::FREQUENCIES), 0.84 / count(CaseBuilder::FREQUENCIES)));
        $this->tabla($filas, $anchos, true);
        $this->parrafo('Umbrales en dB HL. Gap = aérea - ósea del mismo oído.', 7);
    }

    private function acumetria(array $data): void
    {
        $this->titulo('Acumetría (diapasones)');

        $filas = [['Frecuencia', 'Rinne OD', 'Rinne OI', 'Weber']];
        foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $idx) {
            $filas[] = [
                self::hz((int) $hz) . ' Hz',
                CaseBuilder::RINNE_LABELS[$data['Rinne'][$hz]['od'] ?? 'positivo'] ?? 'N/D',
                CaseBuilder::RINNE_LABELS[$data['Rinne'][$hz]['oi'] ?? 'positivo'] ?? 'N/D',
                CaseBuilder::WEBER_LABELS[$data['Weber'][$hz] ?? 'centrado'] ?? 'N/D',
            ];
        }
        $this->tabla($filas, [0.13, 0.3, 0.3, 0.27], true);
    }

    private function impedanciometria(array $data): void
    {
        $this->titulo('Impedanciometría', 210.0);

        $alto = 150.0;
        $this->espacio($alto + 30);
        $ancho = ($this->anchoContenido - 20) / 2;
        $volumen = is_array($data['volume'] ?? null) ? $data['volume'] : [];
        $etf = is_array($data['ETF'] ?? null) ? $data['ETF'] : ['Normal', 'Normal'];

        foreach ([
            ['od', 'OD', (string) ($data['Z_OD'] ?? 'A'), CaseCharts::COLOR_OD, self::MARGEN, (string) ($volumen[0] ?? 'N/D'), (string) ($etf[0] ?? 'Normal')],
            ['oi', 'OI', (string) ($data['Z_OI'] ?? 'A'), CaseCharts::COLOR_OI, self::MARGEN + $ancho + 20, (string) ($volumen[1] ?? 'N/D'), (string) ($etf[1] ?? 'Normal')],
        ] as [$lado, $rotulo, $tipo, $color, $x, $vol, $etfLado]) {
            $this->pdf->text($x, $this->y + self::ASCENDENTE * 8, $rotulo . ' - curva tipo ' . $tipo, 8, true, $color);
            CaseCharts::tympanogram($this->pdf, $x, $this->y + 11, $ancho, $alto, $tipo, $color);
            $this->pdf->text(
                $x,
                $this->y + $alto + 20,
                'Volumen: ' . $vol . ' mL   ·   Función tubaria: ' . $etfLado,
                7,
                false,
                self::GRIS_TEXTO
            );
        }
        $this->y += $alto + 30;

        // Reflejos: ausente se guarda como REFLEX_ABSENT_DB, que es "fuera
        // de escala", no un umbral de 130 dB que alguien midió.
        $reflex = is_array($data['Reflex'] ?? null) ? $data['Reflex'] : [];
        $ipsi = self::desarmar($reflex['ipsi'] ?? [], count(CaseProfile::REFLEX_FREQS_IPSI));
        $contra = self::desarmar($reflex['contra'] ?? [], count(CaseProfile::REFLEX_FREQS_CONTRA));

        $cabecera = ['Sonda'];
        foreach (CaseProfile::REFLEX_FREQS_IPSI as $hz) {
            $cabecera[] = 'Ipsi ' . self::hz((int) $hz);
        }
        foreach (CaseProfile::REFLEX_FREQS_CONTRA as $hz) {
            $cabecera[] = 'Contra ' . (is_int($hz) ? self::hz($hz) : (string) $hz);
        }
        $filas = [$cabecera];
        foreach (['od' => 'OD', 'oi' => 'OI'] as $lado => $rotulo) {
            $fila = [$rotulo];
            foreach ($ipsi[$lado] as $v) {
                $fila[] = self::reflejo((float) $v);
            }
            foreach ($contra[$lado] as $v) {
                $fila[] = self::reflejo((float) $v);
            }
            $filas[] = $fila;
        }
        $cols = count($cabecera);
        $this->tabla($filas, array_merge([0.1], array_fill(0, $cols - 1, 0.9 / ($cols - 1))), true);

        $tipos = $reflex['tipo'] ?? [];
        $this->parrafo(
            'Umbrales en dB HL; "ausente" = sin respuesta en toda la escala. '
            . 'Morfología de la curva: OD ' . (string) ($tipos['od'] ?? 'normal') . ', OI ' . (string) ($tipos['oi'] ?? 'normal') . '.',
            7
        );
    }

    private function logoaudiometria(array $data): void
    {
        $this->titulo('Logoaudiometría', 205.0);

        $umd = is_array($data['UMD'] ?? null) ? $data['UMD'] : [];
        $sdt = is_array($data['SDT'] ?? null) ? $data['SDT'] : [0, 0];
        $srt = is_array($data['SRT'] ?? null) ? $data['SRT'] : [0, 0];
        $recruit = is_array($data['recruit'] ?? null) ? $data['recruit'] : [false, false];

        $porLado = [];
        foreach (['od' => 0, 'oi' => 1] as $lado => $i) {
            $porLado[$lado] = [
                'sdt' => (float) ($sdt[$i] ?? 0),
                'srt' => (float) ($srt[$i] ?? 0),
                'umd_int' => (float) ($umd[$i]['int'] ?? 35),
                'umd_pct' => (float) ($umd[$i]['percentage'] ?? 100),
                'recruit' => !empty($recruit[$i]),
            ];
        }

        $alto = 165.0;
        $this->espacio($alto + 40);
        CaseCharts::logogram($this->pdf, self::MARGEN, $this->y, $this->anchoContenido * 0.55, $alto, $porLado);
        CaseCharts::legend($this->pdf, self::MARGEN + 26, $this->y + $alto + 10, 'SRT = vertical punteada, UMD = triángulo');

        $x = self::MARGEN + $this->anchoContenido * 0.6;
        $ancho = $this->anchoContenido * 0.4;
        $filas = [['', 'OD', 'OI']];
        $filas[] = ['SDT (dB)', self::db($porLado['od']['sdt']), self::db($porLado['oi']['sdt'])];
        $filas[] = ['SRT (dB)', self::db($porLado['od']['srt']), self::db($porLado['oi']['srt'])];
        $filas[] = ['UMD (%)', self::pct($porLado['od']['umd_pct']), self::pct($porLado['oi']['umd_pct'])];
        $filas[] = ['UMD a (dB)', self::db($porLado['od']['umd_int']), self::db($porLado['oi']['umd_int'])];
        $filas[] = ['Rollover', $porLado['od']['recruit'] ? 'Sí' : 'No', $porLado['oi']['recruit'] ? 'Sí' : 'No'];
        $yTabla = $this->tablaEn($x, $this->y + 10, $ancho, $filas, [0.4, 0.3, 0.3], true);

        $this->y = max($this->y + $alto + 24, $yTabla + 6);
    }

    private function supraliminares(array $data): void
    {
        $this->titulo('Pruebas supraliminares');

        $sisi = is_array($data['SISI'] ?? null) ? $data['SISI'] : [0, 0];
        $recruit = is_array($data['recruit'] ?? null) ? $data['recruit'] : [false, false];
        $stenger = is_array($data['Stenger'] ?? null) ? $data['Stenger'] : [false, false];

        $filas = [['', 'OD', 'OI']];
        $filas[] = ['SISI', self::pct((float) ($sisi[0] ?? 0)), self::pct((float) ($sisi[1] ?? 0))];
        $filas[] = ['Reclutamiento', !empty($recruit[0]) ? 'Presente' : 'Ausente', !empty($recruit[1]) ? 'Presente' : 'Ausente'];
        $filas[] = ['Stenger', !empty($stenger[0]) ? 'Positivo' : 'Negativo', !empty($stenger[1]) ? 'Positivo' : 'Negativo'];
        $this->tabla($filas, [0.36, 0.32, 0.32], true);

        // Fowler: el patrón es por FRECUENCIA, no uno por oído -- compara
        // los dos y por eso solo existe donde la asimetría califica.
        $patrones = (array) (($data['Fowler'] ?? [])['patterns'] ?? []);
        if ($patrones !== []) {
            $filas = [['Fowler', 'Patrón de crecimiento de sonoridad']];
            foreach ($patrones as $freqIdx => $patron) {
                $hz = CaseBuilder::FREQUENCIES[(int) $freqIdx] ?? null;
                $filas[] = [
                    $hz !== null ? self::hz($hz) . ' Hz' : (string) $freqIdx,
                    CaseBuilder::FOWLER_PATTERN_LABELS[(string) $patron] ?? (string) $patron,
                ];
            }
            $this->tabla($filas, [0.2, 0.8], true);
        } else {
            $this->parrafo('Fowler: sin frecuencias que califiquen (hace falta asimetría interaural entre 20 y 40 dB).', 7.5);
        }
        if (!empty(($data['Fowler'] ?? [])['diplacusia'])) {
            $this->parrafo('Diplacusia referida por el paciente.', 7.5);
        }

        // Deterioro tonal: las tres pruebas usan protocolos distintos y por
        // eso no comparten frecuencias (ver CaseProfile::DECAY_FREQ_IDX).
        foreach (['Carhart' => 'carhart', 'Stat' => 'stat', 'Rosemberg' => 'rosemberg'] as $rotulo => $modo) {
            $indices = CaseProfile::DECAY_FREQ_IDX[$modo];
            $vals = self::desarmar($data[$rotulo] ?? [], count($indices));
            $cabecera = [$rotulo];
            foreach ($indices as $freqIdx) {
                $cabecera[] = self::hz(CaseBuilder::FREQUENCIES[$freqIdx]);
            }
            $filas = [$cabecera];
            foreach (['od' => 'OD', 'oi' => 'OI'] as $lado => $tag) {
                $fila = [$tag];
                foreach ($vals[$lado] as $v) {
                    $fila[] = self::db((float) $v);
                }
                $filas[] = $fila;
            }
            $cols = count($cabecera);
            $this->tabla($filas, array_merge([0.2], array_fill(0, $cols - 1, 0.8 / ($cols - 1))), true);
        }
        $this->parrafo(
            'Deterioro tonal en dB de caída sostenida. Carhart reinicia el minuto en cada nivel, '
            . 'Rosemberg lo acumula y Stat se toma a nivel fijo.',
            7
        );
    }

    private function abr(array $data): void
    {
        $this->titulo('Potenciales evocados auditivos de tronco (ABR)', 130.0);

        $abr = is_array($data['ABR'] ?? null) ? $data['ABR'] : [];
        $perfil = CaseProfile::normalize($data);

        foreach (['od' => 'OD', 'oi' => 'OI'] as $ladoForm => $lado) {
            $cfg = is_array($abr[$lado] ?? null) ? $abr[$lado] : [];
            $color = $ladoForm === 'od' ? CaseCharts::COLOR_OD : CaseCharts::COLOR_OI;

            $this->espacio(120);
            $this->pdf->text(
                self::MARGEN,
                $this->y + self::ASCENDENTE * 8,
                $this->paraAlumno
                    ? $lado
                    : $lado . '  ·  patología: ' . (string) ($cfg['type'] ?? 'normal')
                      . '  ·  umbral cargado: ' . self::db((float) ($cfg['umbral'] ?? 20)),
                8,
                true,
                $color
            );
            $this->y += 13;

            // Umbral por estímulo: no es el mismo número para todos. Sale
            // del perfil (CaseProfile::abrThresholds), que es lo que el
            // equipo va a mostrar, con la corrección nHL ya aplicada.
            $decomp = CaseProfile::decompose(
                $data['Aerea'] ?? [],
                $data['Osea'] ?? [],
                $ladoForm === 'od' ? 0 : 1,
                (float) $perfil[$lado]['cce_pct']
            );
            $umbrales = CaseProfile::abrThresholds($decomp);
            $barras = [];
            foreach ($umbrales as $estimulo => $db) {
                $barras[self::estimuloLabel((string) $estimulo)] = $db === null ? null : (float) $db;
            }
            $anchoBarras = $this->paraAlumno ? $this->anchoContenido * 0.7 : $this->anchoContenido * 0.52;
            $yBarras = CaseCharts::bars($this->pdf, self::MARGEN, $this->y, $anchoBarras, $barras, (float) CaseProfile::ABR_MAX_DB, $color, 'nHL');

            if ($this->paraAlumno) {
                // El patrón retrococlear, las desviaciones por onda y las
                // condiciones de captura son los mandos del generador: con
                // eso a la vista, el ejercicio ya está resuelto.
                $this->y = $yBarras + 6;
                continue;
            }

            // Al lado, el patrón retrococlear: los ocho parámetros que
            // deciden la forma de la curva.
            $neural = CaseProfile::normalizeRetro(is_array($cfg['neural'] ?? null) ? $cfg['neural'] : []);
            $filas = [['Patrón retrococlear', '']];
            foreach (self::NEURAL_LABELS as $clave => $etiqueta) {
                $filas[] = [$etiqueta, (string) ($neural[$clave] ?? '')];
            }
            $yTabla = $this->tablaEn(
                self::MARGEN + $this->anchoContenido * 0.56,
                $this->y,
                $this->anchoContenido * 0.44,
                $filas,
                [0.62, 0.38],
                true
            );

            $this->y = max($yBarras, $yTabla) + 6;

            $desv = is_array($cfg['desviaciones'] ?? null) ? $cfg['desviaciones'] : [];
            $partes = [];
            foreach (['onda_I' => 'I', 'onda_III' => 'III', 'onda_V' => 'V'] as $clave => $onda) {
                $partes[] = sprintf(
                    '%s: %+.2f ms / %+.2f µV',
                    $onda,
                    (float) ($desv[$clave]['lat'] ?? 0),
                    (float) ($desv[$clave]['amp'] ?? 0)
                );
            }
            $falsaV = is_array($cfg['falsa_v'] ?? null) ? $cfg['falsa_v'] : [];
            $this->parrafo('Desviaciones por onda -- ' . implode('   ', $partes), 7);

            $this->parrafo(sprintf(
                'Captura: promediaciones %s · variabilidad de réplica %s µV · inquietud %s · PAM %s · FSP objetivo %s%s',
                (string) ($cfg['average_objetivo'] ?? 2000),
                (string) ($cfg['repro_var'] ?? 0.2),
                (string) ($cfg['inquietud'] ?? 0),
                (string) ($cfg['pam'] ?? 0),
                (string) (($cfg['fsp_puntos'] ?? [])['objetivo'] ?? 3.0),
                ((float) ($falsaV['amp'] ?? 0)) > 0
                    ? sprintf(' · falsa onda V %s µV a %s ms', (string) $falsaV['amp'], (string) ($falsaV['lat'] ?? 5.6))
                    : ''
            ), 7);
            $this->y += 4;
        }
    }

    private function eoas(array $data): void
    {
        $this->titulo('Emisiones otoacústicas (OEA)', 190.0);

        $eoas = is_array($data['EOAS'] ?? null) ? $data['EOAS'] : [];
        $porLado = [];
        foreach (['od' => 'OD', 'oi' => 'OI'] as $ladoForm => $lado) {
            $cfg = is_array($eoas[$lado] ?? null) ? $eoas[$lado] : [];
            $porLado[$ladoForm] = is_array($cfg['desviaciones'] ?? null) ? $cfg['desviaciones'] : [];
        }

        $alto = 140.0;
        $this->espacio($alto + 60);
        CaseCharts::oaeDeviation($this->pdf, self::MARGEN, $this->y, $this->anchoContenido * 0.55, $alto, $porLado);
        CaseCharts::legend($this->pdf, self::MARGEN + 26, $this->y + $alto + 10, 'más dB = emisión más caída');

        // Patología, atenuación, ruido y sello son mandos del generador: en
        // la versión del alumno queda solo la curva.
        if ($this->paraAlumno) {
            $this->y += $alto + 24;
            return;
        }
        $filas = [['', 'OD', 'OI']];
        foreach ([
            ['Patología', 'type', 'normal'],
            ['Umbral (dB HL)', 'umbral', 20],
            ['Atenuación (dB)', 'atten_db', 0],
            ['Ruido (dB)', 'ruido_db', 0],
            ['Sello (%)', 'sello_pct', 90],
            ['SOAE', 'soae_mode', 'auto'],
        ] as [$rotulo, $clave, $default]) {
            $filas[] = [
                $rotulo,
                (string) ((is_array($eoas['OD'] ?? null) ? $eoas['OD'][$clave] ?? $default : $default)),
                (string) ((is_array($eoas['OI'] ?? null) ? $eoas['OI'][$clave] ?? $default : $default)),
            ];
        }
        $yTabla = $this->tablaEn(
            self::MARGEN + $this->anchoContenido * 0.6,
            $this->y + 10,
            $this->anchoContenido * 0.4,
            $filas,
            [0.44, 0.28, 0.28],
            true
        );
        $this->y = max($this->y + $alto + 24, $yTabla + 6);
    }

    private function vemp(array $data): void
    {
        $this->titulo('Potenciales vestibulares (VEMP)', 110.0);

        $vemp = is_array($data['VEMP'] ?? null) ? $data['VEMP'] : [];
        foreach (['od' => 'OD', 'oi' => 'OI'] as $ladoForm => $lado) {
            $cfg = is_array($vemp[$lado] ?? null) ? $vemp[$lado] : [];
            $color = $ladoForm === 'od' ? CaseCharts::COLOR_OD : CaseCharts::COLOR_OI;
            $subtipos = is_array($cfg['subtipos'] ?? null) ? $cfg['subtipos'] : [];

            $this->espacio(70);
            $this->pdf->text(
                self::MARGEN,
                $this->y + self::ASCENDENTE * 8,
                $this->paraAlumno ? $lado : $lado . '  ·  patología: ' . (string) ($cfg['type'] ?? 'normal'),
                8,
                true,
                $color
            );
            $this->y += 13;

            $barras = [];
            $detalle = [];
            foreach (CaseBuilder::VEMP_SUBTIPOS as $subtipo) {
                $sub = is_array($subtipos[$subtipo] ?? null) ? $subtipos[$subtipo] : [];
                $umbral = (float) ($sub['umbral'] ?? CaseBuilder::VEMP_DEFAULTS[$subtipo]['umbral']);
                $barras[CaseBuilder::VEMP_SUBTIPO_LABELS[$subtipo]] = $umbral;

                $desv = is_array($sub['desviaciones'] ?? null) ? $sub['desviaciones'] : [];
                $picos = [];
                foreach (CaseBuilder::VEMP_PEAKS[$subtipo] as $pico) {
                    $picos[] = sprintf('%s %+.2f ms / %+.2f µV', $pico, (float) ($desv[$pico]['lat'] ?? 0), (float) ($desv[$pico]['amp'] ?? 0));
                }
                $detalle[] = $subtipo . ': ' . implode('  ', $picos);
            }
            $this->y = CaseCharts::bars($this->pdf, self::MARGEN, $this->y, $this->anchoContenido * 0.6, $barras, 100.0, $color) + 3;
            foreach ($this->paraAlumno ? [] : $detalle as $linea) {
                $this->parrafo($linea, 7);
            }
            $this->y += 4;
        }
        $this->parrafo('Umbral en dB. Un VEMP "normal" declarado a propósito también es un hallazgo (ver ANSD).', 7);
    }

    private function clinica(array $data): void
    {
        $this->titulo('Antecedentes y hallazgos clínicos', 80.0);

        // Otoscopia por fases: cada fase describe qué cambió desde la
        // anterior, así que se imprimen en orden y numeradas.
        $fases = (array) (($data['Otoscopia'] ?? [])['fases'] ?? []);
        $this->subtitulo('Otoscopia');
        if ($fases === []) {
            $this->parrafo('Sin otoscopia cargada.', 8);
        } else {
            foreach (array_values($fases) as $i => $fase) {
                $texto = trim((string) (is_array($fase) ? ($fase['texto'] ?? '') : ''));
                $this->parrafo(sprintf('Fase %d: %s', $i + 1, $texto !== '' ? $texto : '(sin texto)'), 8);
                $this->fotosOtoscopia($i);
            }
        }

        $this->subtitulo('Acúfeno');
        $this->parrafo(CaseBuilder::describeTinnitus((array) ($data['Tinnitus'] ?? [])), 8);

        $this->subtitulo('Anamnesis');
        $anamnesis = (array) ($data['Anamnesis'] ?? []);
        $antecedentes = (array) ($anamnesis['antecedentes'] ?? []);
        $marcados = [];
        foreach (CaseBuilder::HIST_CHECKBOXES as $clave) {
            if (!empty($antecedentes[$clave])) {
                $marcados[] = CaseBuilder::HIST_LABELS[$clave] ?? $clave;
            }
        }
        $this->parrafo('Antecedentes: ' . ($marcados === [] ? 'ninguno marcado' : implode(', ', $marcados)), 8);
        foreach ([
            'Medicamentos' => (string) ($anamnesis['medicamentos'] ?? ''),
            'Cirugías' => (string) ($anamnesis['cirugias'] ?? ''),
            'Otros' => (string) ($anamnesis['otros'] ?? ''),
            'Comportamiento en la consulta' => (string) ($data['PatientBehavior'] ?? ''),
        ] as $rotulo => $texto) {
            if (trim($texto) !== '') {
                $this->parrafo($rotulo . ': ' . $texto, 8);
            }
        }
        $this->parrafo('Disposición del paciente: ' . (string) ($data['PatientDisposition'] ?? 0), 8);
    }

    /**
     * Las dos fotos de otoscopia de una fase, lado a lado.
     *
     * Se guardan cuadradas de 640x640 (OtoscopiaPhoto), casi siempre en
     * webp: PdfImage las convierte. Si falta una --o el servidor no tiene
     * GD-- se omite ese hueco en vez de dejar un recuadro vacío: media
     * otoscopia impresa es más útil que ninguna.
     */
    private function fotosOtoscopia(int $faseIdx): void
    {
        $fotos = [];
        foreach (['od' => 'OD', 'oi' => 'OI'] as $lado => $rotulo) {
            $img = PdfImage::jpegBytes(OtoscopiaPhoto::path($this->caseId, $lado, $faseIdx));
            if ($img !== null) {
                $fotos[] = [$lado, $rotulo, $img];
            }
        }
        if ($fotos === []) {
            return;
        }

        $ancho = 108.0;
        $this->espacio($ancho + 24);
        $x = self::MARGEN;
        $altoMax = 0.0;
        foreach ($fotos as [$lado, $rotulo, $img]) {
            $alto = PdfImage::altoProporcional($img, $ancho);
            $color = $lado === 'od' ? CaseCharts::COLOR_OD : CaseCharts::COLOR_OI;
            $this->pdf->text($x, $this->y + self::ASCENDENTE * 7, $rotulo, 7, true, $color);
            $this->pdf->imageJpeg(
                $img['data'],
                $img['w'],
                $img['h'],
                sprintf('oto:%s:%s:%d', $this->caseId, $lado, $faseIdx),
                $x,
                $this->y + 9,
                $ancho,
                $alto
            );
            $this->pdf->rect($x, $this->y + 9, $ancho, $alto, 0.5, self::GRIS_SUAVE);
            $altoMax = max($altoMax, $alto);
            $x += $ancho + 14;
        }
        $this->y += $altoMax + 16;
    }

    // -----------------------------------------------------------------
    // Layout
    // -----------------------------------------------------------------

    /** Corta la página si lo que viene no entra. */
    private function espacio(float $necesario): void
    {
        if ($this->y + $necesario <= $this->pdf->pageHeight() - self::PIE) {
            return;
        }
        $this->pdf->addPage();
        $this->y = self::MARGEN;
        $this->pdf->text(self::MARGEN, $this->y - 12, $this->encabezadoCorrido, 7, false, self::GRIS_SUAVE);
    }

    /**
     * Encabezado de sección. `$reserva` es cuánto ocupa lo PRIMERO que
     * viene debajo (el alto del gráfico, normalmente): sin eso, un título
     * quedaba solo al pie de una página y su contenido arrancaba en la
     * siguiente.
     */
    private function titulo(string $texto, float $reserva = 60.0): void
    {
        $this->espacio($reserva + 30);
        $this->y += 8;
        $this->pdf->rectFilled(self::MARGEN, $this->y, $this->anchoContenido, 15, self::FONDO_CABECERA);
        $this->pdf->text(self::MARGEN + 5, $this->y + 11, $texto, 10.5, true, self::GRIS_TITULO);
        $this->y += 21;
    }

    private function subtitulo(string $texto): void
    {
        // Reserva el subtítulo Y su primer párrafo, por el mismo motivo.
        $this->espacio(44);
        $this->y += 4;
        $this->pdf->text(self::MARGEN, $this->y + self::ASCENDENTE * 8.5, $texto, 8.5, true, self::GRIS_TITULO);
        $this->y += 13;
    }

    private function parrafo(string $texto, float $size = 8, ?float $ancho = null): void
    {
        $this->espacio(($size * 1.35) * 2);
        $base = $this->y + self::ASCENDENTE * $size;
        $fin = $this->pdf->textBlock(
            self::MARGEN,
            $base,
            $texto,
            $ancho ?? $this->anchoContenido,
            $size,
            false,
            0,
            self::GRIS_TEXTO
        );
        $this->y = $fin - self::ASCENDENTE * $size + 2;
    }

    /** @param array<int,array{0:string,1:string}> $filas */
    private function filasKv(array $filas): void
    {
        foreach ($filas as [$clave, $valor]) {
            $this->espacio(14);
            $this->pdf->text(self::MARGEN, $this->y + self::ASCENDENTE * 8, $clave, 8, true, self::GRIS_SUAVE);
            $this->pdf->text(self::MARGEN + 90, $this->y + self::ASCENDENTE * 8, $valor, 8.5, false, self::GRIS_TEXTO);
            $this->y += 13;
        }
    }

    /**
     * Tabla en el ancho completo, avanzando la Y del documento.
     *
     * @param array<int,array<int,string>> $filas la primera es la cabecera si $conCabecera
     * @param array<int,float> $anchos proporciones que suman 1
     */
    private function tabla(array $filas, array $anchos, bool $conCabecera = false): void
    {
        $alto = 12.0 * count($filas) + 4;
        $this->espacio($alto);
        $this->y = $this->tablaEn(self::MARGEN, $this->y, $this->anchoContenido, $filas, $anchos, $conCabecera) + 4;
    }

    /**
     * Tabla en una posición arbitraria (para poner una al lado de un
     * gráfico). Devuelve la Y del final, y NO toca la del documento.
     */
    private function tablaEn(float $x, float $y, float $ancho, array $filas, array $anchos, bool $conCabecera = false): float
    {
        $altoFila = 12.0;
        foreach ($filas as $i => $fila) {
            $esCabecera = $conCabecera && $i === 0;
            if ($esCabecera) {
                $this->pdf->rectFilled($x, $y, $ancho, $altoFila, self::FONDO_TABLA);
            }
            $cx = $x;
            foreach (array_values($fila) as $j => $celda) {
                $anchoCol = $ancho * (float) ($anchos[$j] ?? (1 / max(1, count($fila))));
                $primera = $j === 0;
                $this->pdf->text(
                    $cx + 3,
                    $y + $altoFila - 3.5,
                    (string) $celda,
                    7.2,
                    $esCabecera || $primera,
                    $esCabecera ? self::GRIS_TITULO : self::GRIS_TEXTO
                );
                $cx += $anchoCol;
            }
            $this->pdf->line($x, $y + $altoFila, $x + $ancho, $y + $altoFila, 0.3, '#bbbbbb');
            $y += $altoFila;
        }
        return $y;
    }

    // -----------------------------------------------------------------
    // Lectura de cases.data
    // -----------------------------------------------------------------

    /**
     * Pares [od, oi] por frecuencia -> dos listas. Es el mismo desarmado de
     * CaseBuilder::caseDataToForm: el JSON del caso guarda los dos oídos
     * entrelazados porque así los lee el cliente.
     *
     * @return array{od:array<int,float>,oi:array<int,float>}
     */
    private static function desarmar(array $pares, ?int $cuantos = null): array
    {
        $cuantos ??= count(CaseBuilder::FREQUENCIES);
        $od = [];
        $oi = [];
        for ($n = 0; $n < $cuantos; $n++) {
            $od[] = (float) ($pares[$n][0] ?? 0);
            $oi[] = (float) ($pares[$n][1] ?? 0);
        }
        return ['od' => $od, 'oi' => $oi];
    }

    /** @param array<int,float> $vals @param array<int,int> $indices */
    private static function promedio(array $vals, array $indices): float
    {
        $suma = 0.0;
        foreach ($indices as $i) {
            $suma += (float) ($vals[$i] ?? 0);
        }
        return $indices === [] ? 0.0 : $suma / count($indices);
    }

    private static function grado(float $promedio): string
    {
        foreach (CaseProfile::GRADES as $clave => $g) {
            if ($promedio >= $g['rango'][0] && $promedio <= $g['rango'][1]) {
                return $clave;
            }
        }
        return $promedio < CaseProfile::GRADES['leve']['rango'][0] ? 'normal' : 'profunda';
    }

    private static function tipoLabel(string $tipo): string
    {
        return [
            'normal' => 'Normal',
            'transmission' => 'Transmisión (conductiva)',
            'coclear' => 'Coclear',
            'neural' => 'Retrococlear',
        ][$tipo] ?? $tipo;
    }

    private static function estimuloLabel(string $estimulo): string
    {
        // strpos() y no str_starts_with(): el hosting corre PHP 7.4 (ver
        // tests/test_php_baseline.php).
        if (strpos($estimulo, 'tone_burst_') === 0) {
            return 'Burst ' . str_replace(['tone_burst_', 'Hz'], ['', ''], $estimulo) . ' Hz';
        }
        return ['click' => 'Click', 'ce_chirp' => 'CE-Chirp', 'ls_chirp' => 'LS-Chirp'][$estimulo] ?? $estimulo;
    }

    private static function reflejo(float $db): string
    {
        return $db >= CaseProfile::REFLEX_ABSENT_DB ? 'ausente' : (string) (int) round($db);
    }

    private static function db(float $v): string
    {
        return (string) (int) round($v);
    }

    private static function pct(float $v): string
    {
        return (string) (int) round($v) . ' %';
    }

    private static function hz(int $hz): string
    {
        return $hz >= 1000 ? rtrim(rtrim(number_format($hz / 1000, 1, '.', ''), '0'), '.') . 'k' : (string) $hz;
    }
}
