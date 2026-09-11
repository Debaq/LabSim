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
require_once __DIR__ . '/Sala.php';
require_once __DIR__ . '/CaseMasking.php';
require_once __DIR__ . '/CaseWaveforms.php';
require_once __DIR__ . '/CaseOae.php';

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

    private function __construct(string $caseId, string $encabezadoCorrido)
    {
        $this->pdf = new MiniPdf();
        $this->anchoContenido = $this->pdf->pageWidth() - 2 * self::MARGEN;
        $this->y = self::MARGEN;
        $this->caseId = $caseId;
        $this->encabezadoCorrido = $encabezadoCorrido;
    }

    /**
     * @param array<string,mixed> $data cases.data
     * @param array{nombre?:string,rut?:string,fecha_nac?:string} $patient
     * @return string bytes del PDF
     */
    public static function build(string $caseId, array $data, array $patient = [], string $emisor = '', string $fecha = ''): string
    {
        $nombre = trim((string) ($patient['nombre'] ?? ''));
        $doc = new self($caseId, 'Ficha ' . $caseId . ($nombre !== '' ? ' - ' . $nombre : ''));
        $doc->portada($caseId, $data, $patient, $emisor, $fecha !== '' ? $fecha : date('d-m-Y'));
        $doc->resumenPorOido($data);
        // La historia antes que los exámenes, como se lee una ficha: quién
        // es el paciente y qué cuenta, y recién después qué mide cada
        // prueba.
        $doc->clinica($data);
        $doc->audiometria($data);
        $doc->acumetria($data);
        $doc->impedanciometria($data);
        $doc->logoaudiometria($data);
        $doc->supraliminares($data);
        $doc->abr($data);
        $doc->eoas($data);
        $doc->vemp($data);
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
            'PTP aéreo (500-1k-2k Hz)',
            self::db5($porLado['od']['ptp']),
            self::db5($porLado['oi']['ptp']),
        ];
        $filas[] = [
            'Promedio BIAP aéreo (500-1k-2k-4k Hz)',
            self::db5($porLado['od']['biap']) . '  (' . self::grado(self::paso5($porLado['od']['biap'])) . ')',
            self::db5($porLado['oi']['biap']) . '  (' . self::grado(self::paso5($porLado['oi']['biap'])) . ')',
        ];
        $filas[] = [
            'Promedio BIAP óseo (500-1k-2k-4k Hz)',
            self::db5($porLado['od']['biapOsea']),
            self::db5($porLado['oi']['biapOsea']),
        ];
        $filas[] = [
            'Gap aéreo-óseo (500-1k-2k-4k Hz)',
            self::db5($porLado['od']['biap'] - $porLado['od']['biapOsea']),
            self::db5($porLado['oi']['biap'] - $porLado['oi']['biapOsea']),
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
            'Los promedios van al paso de 5 dB, que es el mínimo que mueve un audiómetro, y el grado se lee '
            . 'sobre ese valor. Módulos derivados del perfil: '
            . ($autos === [] ? 'ninguno (todo cargado a mano)' : implode(', ', $autos)) . '.',
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
            'El enmascaramiento lo infiere el motor, no se carga a mano.',
            $anchoLeyenda - 4,
            6.5,
            false,
            8,
            self::GRIS_SUAVE
        );
        $this->y += $alto + 10;

        // Debajo del audiograma va el enmascaramiento y no una tabla de
        // umbrales: los umbrales ya están en el gráfico, y lo que no se ve
        // ahí --de qué oído es cada punto, y con cuánto ruido se demuestra--
        // es justo lo que hay que decidir en la cabina. Las cuentas son las
        // de la app (ver CaseMasking).
        $this->enmascaramiento($aerea, $osea);
    }

    /**
     * Qué umbrales hay que enmascarar y con cuánto ruido: una tabla por vía.
     *
     * El "hace falta" no lleva columna propia -- la frecuencia que no se
     * enmascara va con guión y se ve sola. La regla es la del motor: el
     * estímulo cruza cuando lo que llega a la cóclea del otro oído alcanza
     * su umbral óseo. El rango es la meseta: por debajo del mínimo el umbral
     * puede ser del oído contrario (curva sombra) y por encima del máximo el
     * ruido cruzó de vuelta y tapa al oído que se está midiendo.
     *
     * @param array{od:array<int,float>,oi:array<int,float>} $aerea
     * @param array{od:array<int,float>,oi:array<int,float>} $osea
     */
    private function enmascaramiento(array $aerea, array $osea): void
    {
        $this->subtitulo('Enmascaramiento (dB EM de ruido útil)');

        $tablas = [];
        foreach (['od', 'oi'] as $lado) {
            $otro = $lado === 'od' ? 'oi' : 'od';
            $tablas[$lado] = CaseMasking::tabla($aerea[$lado], $osea[$lado], $aerea[$otro], $osea[$otro]);
        }

        // Las dos vías lado a lado: cada celda es el rango con la meseta
        // entre paréntesis, así entran las dos tablas en el alto de una.
        $anchoTabla = ($this->anchoContenido - 16) / 2;
        $this->espacio(12.0 * (count(CaseBuilder::FREQUENCIES) + 1) + 12);
        $yTablas = $this->y;
        $finMax = $yTablas;
        $x = self::MARGEN;

        foreach (['aerea' => 'Vía aérea', 'osea' => 'Vía ósea'] as $via => $rotulo) {
            $filas = [[$rotulo, 'OD', 'OI']];
            foreach (CaseBuilder::FREQUENCIES as $i => $hz) {
                // La vía ósea solo se mide de 250 a 4000: fuera de ahí no
                // hay umbral que enmascarar, así que la fila no existe.
                if ($via === 'osea' && !in_array($hz, CaseCharts::FREQS_OSEA, true)) {
                    continue;
                }
                $filas[] = [
                    self::hz($hz) . ' Hz',
                    self::celdaMkg($tablas['od'][$i][$via]),
                    self::celdaMkg($tablas['oi'][$i][$via]),
                ];
            }
            $fin = $this->tablaEn($x, $yTablas, $anchoTabla, $filas, [0.34, 0.33, 0.33], true);
            $finMax = max($finMax, $fin);
            $x += $anchoTabla + 16;
        }
        $this->y = $finMax + 4;

        $this->parrafo(
            'Rango de ruido útil con la meseta entre paréntesis; (-) = ese umbral no cruza. '
            . 'Aérea: mín = UAE - AI - UONE + UANE, máx = UOE + AI. '
            . 'Ósea: mín = UOE - UONE + UANE + efecto oclusivo, máx = UOE + AI. '
            . 'Calculado con NBN (CE 0); con otro ruido el mínimo sube.',
            7
        );
    }

    /**
     * Acumetría, escrita como se escribe a mano.
     *
     * Rinne y Weber comparten el mismo eje --OD a la izquierda, la
     * frecuencia al medio, OI a la derecha-- y el mismo estilo de fila. Son
     * dos lecturas del mismo diapasón: ponerle tabla a una y otra cosa a la
     * otra las hacía parecer exámenes distintos.
     *
     * El Rinne se anota (+) cuando la aérea supera a la ósea y (-) cuando es
     * al revés; el falso negativo va escrito, porque no es un resultado de
     * ese oído. El Weber no es un resultado por oído sino uno solo: una
     * flecha hacia el lado al que lateraliza, y dos flechas cuando no.
     */
    private function acumetria(array $data): void
    {
        $this->titulo('Acumetría (diapasones)', 120.0);

        $xCentro = self::MARGEN + 120.0;
        $gap = 30.0;

        // Encabezado del eje, una sola vez: vale para las dos pruebas.
        $this->espacio(18);
        $base = $this->y + self::ASCENDENTE * 7;
        $this->pdf->textRight($xCentro - $gap, $base, 'OD', 7, true, CaseCharts::COLOR_OD);
        $this->pdf->textCenter($xCentro, $base, 'Frecuencia', 7, true, self::GRIS_SUAVE);
        $this->pdf->text($xCentro + $gap, $base, 'OI', 7, true, CaseCharts::COLOR_OI);
        $this->y += 12;

        $this->subtitulo('Rinne');
        foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $idx) {
            $this->espacio(16);
            $base = $this->y + self::ASCENDENTE * 8;
            $this->pdf->textRight(
                $xCentro - $gap,
                $base,
                self::rinne((string) ($data['Rinne'][$hz]['od'] ?? 'positivo')),
                8,
                true,
                CaseCharts::COLOR_OD
            );
            $this->pdf->textCenter($xCentro, $base, self::hz((int) $hz) . ' Hz', 8, true, self::GRIS_TITULO);
            $this->pdf->text(
                $xCentro + $gap,
                $base,
                self::rinne((string) ($data['Rinne'][$hz]['oi'] ?? 'positivo')),
                8,
                true,
                CaseCharts::COLOR_OI
            );
            $this->y += 14;
        }

        $this->subtitulo('Weber');
        foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $idx) {
            $lado = (string) ($data['Weber'][$hz] ?? 'centrado');
            $this->espacio(16);
            $base = $this->y + self::ASCENDENTE * 8;
            $centro = $this->y + 4;

            // Las flechas ocupan las mismas columnas que los (+)/(-) del
            // Rinne. Se dibujan: el carácter -> no existe en WinAnsi, que es
            // la codificación del texto del PDF.
            if ($lado === 'od' || $lado === 'centrado') {
                $this->flecha($xCentro - $gap, $centro, -16.0, $lado === 'od' ? CaseCharts::COLOR_OD : self::GRIS_SUAVE);
            }
            if ($lado === 'oi' || $lado === 'centrado') {
                $this->flecha($xCentro + $gap, $centro, 16.0, $lado === 'oi' ? CaseCharts::COLOR_OI : self::GRIS_SUAVE);
            }
            $this->pdf->textCenter($xCentro, $base, self::hz((int) $hz) . ' Hz', 8, true, self::GRIS_TITULO);
            $this->pdf->text(
                $xCentro + 100,
                $base,
                CaseBuilder::WEBER_LABELS[$lado] ?? $lado,
                8,
                false,
                self::GRIS_TEXTO
            );
            $this->y += 14;
        }
    }

    /**
     * Rinne como se anota a mano: (+) y (-), y escrito cuando es otra cosa.
     *
     * El falso negativo no tiene signo porque no es un resultado del oído
     * que se está probando -- es el otro el que oye el diapasón-- y
     * escribirlo como (-) lo haría desaparecer entre los negativos de
     * verdad, que es justo el error que el cuadro existe para enseñar.
     */
    private static function rinne(string $valor): string
    {
        if ($valor === 'positivo') {
            return '(+)';
        }
        if ($valor === 'negativo') {
            return '(-)';
        }
        return 'Falso negativo';
    }

    /**
     * Flecha horizontal desde $x, de $largo pt (negativo = hacia la
     * izquierda), centrada en $y.
     */
    private function flecha(float $x, float $y, float $largo, string $color): void
    {
        $punta = $x + $largo;
        $this->pdf->line($x, $y, $punta, $y, 1.1, $color);
        $sentido = $largo < 0 ? 1 : -1;
        $this->pdf->polygon(
            [
                [$punta, $y],
                [$punta + $sentido * 4, $y - 2.4],
                [$punta + $sentido * 4, $y + 2.4],
            ],
            null,
            $color
        );
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
                'Volumen del CAE: ' . $vol . ' mL',
                7,
                false,
                self::GRIS_TEXTO
            );
        }
        $this->y += $alto + 30;

        // Reflejos: la misma tabla espejada del editor (ipsi al centro,
        // contra afuera). Se lee por FILAS de frecuencia y el patrón --qué
        // se cae y de qué lado-- se ve de un vistazo; con una tabla por oído
        // había que cruzar dos bloques con el dedo. Ausente se guarda como
        // REFLEX_ABSENT_DB: es "fuera de escala", no un umbral de 130 dB que
        // alguien midió.
        $reflex = is_array($data['Reflex'] ?? null) ? $data['Reflex'] : [];
        $ipsi = self::desarmar($reflex['ipsi'] ?? [], count(CaseProfile::REFLEX_FREQS_IPSI));
        $contra = self::desarmar($reflex['contra'] ?? [], count(CaseProfile::REFLEX_FREQS_CONTRA));

        $this->subtitulo('Reflejos acústicos');
        $yTablasZ = $this->y;
        $filas = [['OD contra', 'OD ipsi', 'Frec.', 'OI ipsi', 'OI contra']];
        foreach (CaseProfile::REFLEX_FREQS_CONTRA as $n => $hz) {
            // La fila del ruido no tiene ipsi: ese dato no existe.
            $hayIpsi = isset(CaseProfile::REFLEX_FREQS_IPSI[$n]);
            $filas[] = [
                self::reflejo((float) ($contra['od'][$n] ?? CaseProfile::REFLEX_ABSENT_DB)),
                $hayIpsi ? self::reflejo((float) ($ipsi['od'][$n] ?? CaseProfile::REFLEX_ABSENT_DB)) : '',
                is_int($hz) ? self::hz($hz) . ' Hz' : 'WN',
                $hayIpsi ? self::reflejo((float) ($ipsi['oi'][$n] ?? CaseProfile::REFLEX_ABSENT_DB)) : '',
                self::reflejo((float) ($contra['oi'][$n] ?? CaseProfile::REFLEX_ABSENT_DB)),
            ];
        }
        $anchoReflejos = $this->anchoContenido * 0.56;
        $finReflejos = $this->tablaEn(self::MARGEN, $yTablasZ, $anchoReflejos, $filas, [0.22, 0.19, 0.2, 0.19, 0.2], true);

        // Al lado, los números de la curva. La ficha guarda solo el tipo
        // Jerger, así que compliance, presión y ancho salen de la misma
        // forma que se dibuja arriba (ver CaseCharts::valoresTimpanograma):
        // no hay dos fuentes que puedan discrepar.
        $tipoOd = (string) ($data['Z_OD'] ?? 'A');
        $tipoOi = (string) ($data['Z_OI'] ?? 'A');
        $vOd = CaseCharts::valoresTimpanograma($tipoOd);
        $vOi = CaseCharts::valoresTimpanograma($tipoOi);
        $presion = static fn (array $v): string => $v['plana'] ? 'sin pico' : self::db($v['pico_dapa']) . ' daPa';
        $ancho = static fn (array $v): string => $v['plana'] ? '--' : self::db($v['ancho_dapa']) . ' daPa';

        $filasZ = [
            ['Timpanograma', 'OD', 'OI'],
            ['Tipo (Jerger)', $tipoOd, $tipoOi],
            ['Compliance estática', number_format($vOd['estatica'], 2) . ' mL', number_format($vOi['estatica'], 2) . ' mL'],
            ['Compliance máxima', number_format($vOd['maxima'], 2) . ' mL', number_format($vOi['maxima'], 2) . ' mL'],
            ['Presión del pico', $presion($vOd), $presion($vOi)],
            ['Ancho a media altura', $ancho($vOd), $ancho($vOi)],
            ['Volumen del CAE', (string) ($volumen[0] ?? 'N/D') . ' mL', (string) ($volumen[1] ?? 'N/D') . ' mL'],
            ['Función tubaria', (string) ($etf[0] ?? 'Normal'), (string) ($etf[1] ?? 'Normal')],
        ];
        $finZ = $this->tablaEn(
            self::MARGEN + $anchoReflejos + 14,
            $yTablasZ,
            $this->anchoContenido - $anchoReflejos - 14,
            $filasZ,
            [0.44, 0.28, 0.28],
            true
        );
        $this->y = max($finReflejos, $finZ) + 4;

        $tipos = $reflex['tipo'] ?? [];
        $this->parrafo(
            'Umbrales en dB HL; (-) = sin respuesta en toda la escala. Morfología de la curva: OD '
            . (string) ($tipos['od'] ?? 'normal') . ', OI ' . (string) ($tipos['oi'] ?? 'normal') . '.',
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

        // Fowler: el patrón es por FRECUENCIA, no uno por oído -- compara los
        // dos y por eso solo existe donde la asimetría califica. Lo que se
        // informa no es el nombre del patrón sino DÓNDE pasa cada cosa: los
        // cortes son dB sobre el umbral del oído en estudio (ver
        // CaseBuilder::FOWLER_PATTERNS y Fowler.py), así que puestos en dB HL
        // dicen a qué nivel el alumno va a ver que la sonoridad se empareja.
        $patrones = (array) (($data['Fowler'] ?? [])['patterns'] ?? []);
        if ($patrones !== []) {
            $aereaFowler = self::desarmar($data['Aerea'] ?? []);
            $filas = [['Fowler', 'En estudio', 'Patrón', 'Empieza a igualar', 'Iguala', 'Sobrepasa']];
            foreach ($patrones as $freqIdx => $patron) {
                $i = (int) $freqIdx;
                $hz = CaseBuilder::FREQUENCIES[$i] ?? null;
                // El oído en estudio es el PEOR en esa frecuencia: es de
                // quien se juzga el crecimiento de sonoridad.
                $peor = ($aereaFowler['od'][$i] ?? 0) >= ($aereaFowler['oi'][$i] ?? 0) ? 'od' : 'oi';
                $umbralEstudio = (float) ($aereaFowler[$peor][$i] ?? 0);
                $cortes = CaseBuilder::fowlerCutsForPattern((string) $patron);
                $nivel = static function ($corte) use ($umbralEstudio): string {
                    // 200 = el quiebre no ocurre dentro de la escala.
                    return (float) $corte >= 200 ? 'no ocurre' : self::db($umbralEstudio + (float) $corte) . ' dB';
                };
                $filas[] = [
                    $hz !== null ? self::hz($hz) . ' Hz' : (string) $freqIdx,
                    strtoupper($peor),
                    CaseBuilder::FOWLER_PATTERN_LABELS[(string) $patron] ?? (string) $patron,
                    $nivel($cortes[0]),
                    $nivel($cortes[1]),
                    $nivel($cortes[2]),
                ];
            }
            $this->tabla($filas, [0.11, 0.12, 0.29, 0.16, 0.16, 0.16], true);
            $this->parrafo(
                'Niveles en dB HL del oído en estudio. "No ocurre" = el quiebre queda fuera de la escala del audiómetro.',
                7
            );
        } else {
            $this->parrafo(
                'Fowler: sin frecuencias que califiquen. Hace falta una diferencia interaural de 20 a 40 dB '
                . 'en una misma frecuencia, con el oído bueno en rango normal y sin gap.',
                7.5
            );
        }
        if (!empty(($data['Fowler'] ?? [])['diplacusia'])) {
            $this->parrafo('Diplacusia referida por el paciente.', 7.5);
        }

        // Deterioro tonal: las tres pruebas usan protocolos distintos y por
        // eso no comparten frecuencias (ver CaseProfile::DECAY_FREQ_IDX).
        // Van lado a lado porque son tres tablas de dos filas: apiladas
        // gastaban media página para doce números.
        $anchoDecay = ($this->anchoContenido - 2 * 10) / 3;
        $this->espacio(12 * 3 + 16);
        $yDecay = $this->y;
        $finDecay = $yDecay;
        $xDecay = self::MARGEN;

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
            $finDecay = max($finDecay, $this->tablaEn(
                $xDecay,
                $yDecay,
                $anchoDecay,
                $filas,
                array_merge([0.34], array_fill(0, $cols - 1, 0.66 / ($cols - 1))),
                true
            ));
            $xDecay += $anchoDecay + 10;
        }
        $this->y = $finDecay + 4;
        $this->parrafo('Deterioro tonal en dB de caída sostenida.', 7);
    }

    /**
     * ABR completo en UNA hoja: las dos series del click lado a lado, y
     * debajo los números en tablas.
     *
     * Los umbrales por estímulo iban en barras y no se entendían: una barra
     * no dice si 65 nHL es mucho o poco, y ocupaba media página por oído.
     * En tabla se comparan los dos oídos de un vistazo, que es la lectura
     * que importa.
     */
    private function abr(array $data): void
    {
        // La sección entera arranca en página nueva si no entra: partir la
        // serie del click de la tabla de umbrales obliga a ir y volver.
        $this->titulo('Potenciales evocados auditivos de tronco (ABR)', 420.0);

        $abr = is_array($data['ABR'] ?? null) ? $data['ABR'] : [];
        $perfil = CaseProfile::normalize($data);
        $poblacion = CaseWaveforms::poblacion(
            isset($data['edad']) ? (int) $data['edad'] : null,
            (int) ($data['gender'] ?? 0)
        );

        $porLado = [];
        foreach (['od' => 'OD', 'oi' => 'OI'] as $ladoForm => $lado) {
            $cfg = is_array($abr[$lado] ?? null) ? $abr[$lado] : [];
            $decomp = CaseProfile::decompose(
                $data['Aerea'] ?? [],
                $data['Osea'] ?? [],
                $ladoForm === 'od' ? 0 : 1,
                (float) $perfil[$lado]['cce_pct']
            );
            $porLado[$ladoForm] = [
                'cfg' => $cfg,
                'tipo' => (string) ($cfg['type'] ?? 'normal'),
                'umbrales' => CaseProfile::abrThresholds($decomp),
                'neural' => CaseProfile::normalizeRetro(is_array($cfg['neural'] ?? null) ? $cfg['neural'] : []),
                'desv' => is_array($cfg['desviaciones'] ?? null) ? $cfg['desviaciones'] : [],
            ];
        }

        // --- Las dos series del click, lado a lado --------------------
        $ancho = ($this->anchoContenido - 16) / 2;
        $alto = 168.0;
        $this->espacio($alto + 40);
        $yPilas = $this->y;

        foreach (['od' => 'OD', 'oi' => 'OI'] as $ladoForm => $lado) {
            $color = $ladoForm === 'od' ? CaseCharts::COLOR_OD : CaseCharts::COLOR_OI;
            $x = self::MARGEN + ($ladoForm === 'od' ? 0 : $ancho + 16);
            $datos = $porLado[$ladoForm];
            $umbralClick = (float) ($datos['umbrales']['click'] ?? 20);

            $this->pdf->text(
                $x,
                $yPilas + self::ASCENDENTE * 8,
                $lado . '  ·  ' . $datos['tipo'] . '  ·  umbral cargado ' . self::db((float) ($datos['cfg']['umbral'] ?? 20)),
                8,
                true,
                $color
            );

            $series = [];
            foreach (CaseWaveforms::serieIntensidades($umbralClick) as $nivel) {
                $ondas = CaseWaveforms::ondasClick(
                    $nivel,
                    $umbralClick,
                    $datos['tipo'],
                    $datos['neural'],
                    $datos['desv'],
                    $poblacion
                );
                $marcas = [];
                // Solo se marca la onda que de verdad se ve: rotular una V
                // que quedó bajo el ruido enseñaría a marcar lo que no está.
                foreach (['I', 'III', 'V'] as $onda) {
                    if ($ondas[$onda]['amp'] >= CaseWaveforms::AMP_VISIBLE) {
                        $marcas[] = ['t' => $ondas[$onda]['lat'], 'v' => $ondas[$onda]['amp'], 'texto' => $onda];
                    }
                }
                $series[] = [
                    'rotulo' => self::db($nivel),
                    'pts' => CaseWaveforms::trazo($ondas),
                    'marcas' => $marcas,
                ];
            }
            CaseCharts::waveformStack($this->pdf, $x, $yPilas + 10, $ancho, $alto, $series, $color);
        }
        $this->y = $yPilas + $alto + 18;
        $this->parrafo(
            'Click por vía aérea, de 80 dB nHL al umbral de cada oído. Trazo reconstruido de los parámetros '
            . 'del caso: sin ruido, sin promediación y sin artefactos, así que muestra la forma del examen, '
            . 'no la pantalla del equipo.',
            6.5
        );

        // --- Umbral por estímulo, en tabla ----------------------------
        $filas = [['Estímulo · dB nHL', 'OD', 'OI']];
        foreach (array_keys($porLado['od']['umbrales']) as $estimulo) {
            $filas[] = [
                self::estimuloLabel((string) $estimulo),
                self::umbralAbr($porLado['od']['umbrales'][$estimulo] ?? null),
                self::umbralAbr($porLado['oi']['umbrales'][$estimulo] ?? null),
            ];
        }
        $anchoTabla = ($this->anchoContenido - 16) / 2;
        $yTablas = $this->y;
        $finUmbrales = $this->tablaEn(self::MARGEN, $yTablas, $anchoTabla, $filas, [0.52, 0.24, 0.24], true);

        // --- Patrón retrococlear, al lado -----------------------------
        $filas = [['Patrón retrococlear', 'OD', 'OI']];
        foreach (self::NEURAL_LABELS as $clave => $etiqueta) {
            $filas[] = [
                $etiqueta,
                (string) ($porLado['od']['neural'][$clave] ?? ''),
                (string) ($porLado['oi']['neural'][$clave] ?? ''),
            ];
        }
        $finNeural = $this->tablaEn(
            self::MARGEN + $anchoTabla + 16,
            $yTablas,
            $anchoTabla,
            $filas,
            [0.5, 0.25, 0.25],
            true
        );
        $this->y = max($finUmbrales, $finNeural) + 6;

        // El patrón solo entra en juego si el oído es neural: con los
        // defaults cargados en un oído normal, esos números no dibujan nada.
        if ($porLado['od']['tipo'] !== 'neural' && $porLado['oi']['tipo'] !== 'neural') {
            $this->parrafo(
                'El patrón retrococlear queda cargado pero no se aplica: ninguno de los dos oídos es neural.',
                6.5
            );
        }

        // --- Desviaciones y captura, una línea por oído ---------------
        foreach (['od' => 'OD', 'oi' => 'OI'] as $ladoForm => $lado) {
            $datos = $porLado[$ladoForm];
            $partes = [];
            foreach (['onda_I' => 'I', 'onda_III' => 'III', 'onda_V' => 'V'] as $clave => $onda) {
                $partes[] = sprintf(
                    '%s %+.2f ms / %+.2f µV',
                    $onda,
                    (float) ($datos['desv'][$clave]['lat'] ?? 0),
                    (float) ($datos['desv'][$clave]['amp'] ?? 0)
                );
            }
            $falsaV = is_array($datos['cfg']['falsa_v'] ?? null) ? $datos['cfg']['falsa_v'] : [];
            $this->parrafo(
                $lado . ' -- desviaciones: ' . implode('   ', $partes)
                . sprintf(
                    '   |   promediaciones %s · réplica %s µV · inquietud %s · PAM %s · FSP objetivo %s%s',
                    (string) ($datos['cfg']['average_objetivo'] ?? 2000),
                    (string) ($datos['cfg']['repro_var'] ?? 0.2),
                    (string) ($datos['cfg']['inquietud'] ?? 0),
                    (string) ($datos['cfg']['pam'] ?? 0),
                    (string) (($datos['cfg']['fsp_puntos'] ?? [])['objetivo'] ?? 3.0),
                    ((float) ($falsaV['amp'] ?? 0)) > 0
                        ? sprintf(' · falsa onda V %s µV a %s ms', (string) $falsaV['amp'], (string) ($falsaV['lat'] ?? 5.6))
                        : ''
                ),
                6.5
            );
        }
    }

    /** Umbral del ABR, o "sin respuesta" cuando no hay. */
    private static function umbralAbr($db): string
    {
        return $db === null ? 'sin respuesta' : self::db((float) $db);
    }

    private function eoas(array $data): void
    {
        $this->titulo('Emisiones otoacústicas (OEA)', 230.0);

        $eoas = is_array($data['EOAS'] ?? null) ? $data['EOAS'] : [];
        $cfg = [
            'od' => is_array($eoas['OD'] ?? null) ? $eoas['OD'] : [],
            'oi' => is_array($eoas['OI'] ?? null) ? $eoas['OI'] : [],
        ];
        $pruebas = ['od' => CaseOae::pruebas($cfg['od']), 'oi' => CaseOae::pruebas($cfg['oi'])];

        // Las tres pruebas con estímulo, cada una en SUS bandas y con su
        // área normal sombreada. El caso guarda un solo perfil de emisión
        // por oído, pero las pruebas no comparten ni frecuencias ni escala.
        $ancho = ($this->anchoContenido - 14) / 2;
        $alto = 118.0;
        $paneles = [
            ['teoae', 'TEOAE (clicks)', [-15.0, 25.0], 'dB SPL'],
            ['dpoae', 'DP-grama (productos de distorsión)', [-30.0, 25.0], 'dB SPL'],
            ['sfoae', 'SFOAE (frecuencia específica)', [-20.0, 15.0], 'dB'],
        ];

        $x = self::MARGEN;
        $fila = 0;
        foreach ($paneles as $i => [$clave, $rotulo, $rangoY, $unidad]) {
            if ($i > 0 && $i % 2 === 0) {
                $this->y += $alto + 24;
                $fila++;
            }
            $x = self::MARGEN + ($i % 2) * ($ancho + 14);
            if ($i % 2 === 0) {
                $this->espacio($alto + 30);
            }

            $bandas = array_keys($pruebas['od'][$clave]['bandas']);
            $area = $pruebas['od'][$clave]['area'];
            $piso = [];
            $porLado = ['od' => [], 'oi' => []];
            foreach ($bandas as $hz) {
                $bandaOd = $pruebas['od'][$clave]['bandas'][$hz];
                $piso[$hz] = $bandaOd['piso'] ?? $pruebas['od'][$clave]['piso'];
                $porLado['od'][$hz] = $bandaOd['respuesta'];
                $porLado['oi'][$hz] = $pruebas['oi'][$clave]['bandas'][$hz]['respuesta'] ?? null;
            }

            $this->pdf->text($x, $this->y + self::ASCENDENTE * 7, $rotulo, 7, true, self::GRIS_TITULO);
            CaseCharts::oaePanel(
                $this->pdf,
                $x,
                $this->y + 9,
                $ancho,
                $alto,
                $bandas,
                $area,
                $piso,
                $porLado,
                $rangoY,
                $unidad
            );

            // Debajo, qué banda pasa y cuál no: es el PASS/REFER del equipo.
            $resumen = [];
            foreach (['od' => 'OD', 'oi' => 'OI'] as $lado => $tag) {
                $pasan = 0;
                foreach ($pruebas[$lado][$clave]['bandas'] as $banda) {
                    $pasan += $banda['pasa'] ? 1 : 0;
                }
                $total = count($pruebas[$lado][$clave]['bandas']);
                $resumen[] = $tag . ': ' . $pasan . '/' . $total . ' bandas sobre el ruido';
            }
            $this->pdf->text($x, $this->y + $alto + 18, implode('   ·   ', $resumen), 6, false, self::GRIS_TEXTO);
        }

        // SOAE: el cuarto examen, que no lleva estímulo. Lo que hay que ver
        // es si asoma algún pico sobre el piso, y el caso puede forzarlos.
        $this->y += $alto + 24;
        $this->espacio($alto + 34);
        $x = self::MARGEN + ($ancho + 14);
        $soae = ['od' => CaseOae::soae($cfg['od']), 'oi' => CaseOae::soae($cfg['oi'])];
        $this->pdf->text($x, $this->y + self::ASCENDENTE * 7, 'SOAE (espontáneas, sin estímulo)', 7, true, self::GRIS_TITULO);
        CaseCharts::soaeSpectrum(
            $this->pdf,
            $x,
            $this->y + 9,
            $ancho,
            $alto,
            ['od' => $soae['od']['picos'], 'oi' => $soae['oi']['picos']],
            CaseOae::SOAE['espectro_hz'],
            [-20.0, 20.0],
            static function (float $hz): float {
                // Piso en V: sube hacia los graves y, menos, hacia los agudos.
                $oct = log($hz / 2000.0, 2);
                return CaseOae::SOAE['piso_db']
                    + ($oct < 0 ? abs($oct) * CaseOae::SOAE['piso_subida_grave_db_oct']
                                : $oct * CaseOae::SOAE['piso_subida_agudo_db_oct']);
            }
        );
        $modos = [];
        foreach (['od' => 'OD', 'oi' => 'OI'] as $lado => $tag) {
            $modo = $soae[$lado]['modo'];
            $picos = count($soae[$lado]['picos']);
            $modos[] = $tag . ': ' . $modo . ($picos > 0 ? " ({$picos} pico" . ($picos === 1 ? '' : 's') . ' fijado' . ($picos === 1 ? '' : 's') . ')' : '');
        }
        $this->pdf->text($x, $this->y + $alto + 18, implode('   ·   ', $modos), 6, false, self::GRIS_TEXTO);

        // Al lado del SOAE, los parámetros del oído.
        $filas = [['', 'OD', 'OI']];
        foreach ([
            ['Patología', 'type', 'normal'],
            ['Umbral (dB HL)', 'umbral', 20],
            ['Atenuación (dB)', 'atten_db', 0],
            ['Ruido (dB)', 'ruido_db', 0],
            ['Sello (%)', 'sello_pct', 90],
            ['Variabilidad (dB)', 'variabilidad_db', 0],
        ] as [$rotulo, $clave, $default]) {
            $filas[] = [
                $rotulo,
                (string) ($cfg['od'][$clave] ?? $default),
                (string) ($cfg['oi'][$clave] ?? $default),
            ];
        }
        $this->tablaEn(self::MARGEN, $this->y + 9, $ancho, $filas, [0.44, 0.28, 0.28], true);

        $this->y += $alto + 28;
        CaseCharts::legend($this->pdf, self::MARGEN + 26, $this->y, 'área gris = respuesta normal, punteado = piso de ruido');
        $this->y += 10;
    }

    /**
     * VEMP: las series de los tres subtipos por oído y, debajo, los números
     * en tabla. Sin barras, por lo mismo que el ABR: una barra no dice si un
     * umbral de 90 dB es normal o está desarmado, y la comparación entre
     * oídos --que es toda la lectura del VEMP-- se hace en columnas.
     */
    private function vemp(array $data): void
    {
        $this->titulo('Potenciales vestibulares (VEMP)', 330.0);

        $vemp = is_array($data['VEMP'] ?? null) ? $data['VEMP'] : [];
        $anchoPanel = ($this->anchoContenido - 2 * 12) / 3;
        $altoPanel = 105.0;

        $porLado = [];
        foreach (['od' => 'OD', 'oi' => 'OI'] as $ladoForm => $lado) {
            $cfg = is_array($vemp[$lado] ?? null) ? $vemp[$lado] : [];
            $color = $ladoForm === 'od' ? CaseCharts::COLOR_OD : CaseCharts::COLOR_OI;
            $subtipos = is_array($cfg['subtipos'] ?? null) ? $cfg['subtipos'] : [];
            $porLado[$ladoForm] = ['cfg' => $cfg, 'subtipos' => $subtipos];

            $this->espacio($altoPanel + 34);
            $this->pdf->text(
                self::MARGEN,
                $this->y + self::ASCENDENTE * 8,
                $lado . '  ·  patología: ' . (string) ($cfg['type'] ?? 'normal'),
                8,
                true,
                $color
            );
            $this->y += 13;

            // Un panel por subtipo con la serie de intensidades: la
            // respuesta crece con el nivel y se apaga en el umbral, que es
            // lo que el alumno tiene que encontrar bajando de 5 en 5.
            $xPanel = self::MARGEN;
            foreach (CaseBuilder::VEMP_SUBTIPOS as $subtipo) {
                $sub = is_array($subtipos[$subtipo] ?? null) ? $subtipos[$subtipo] : [];
                $umbral = (float) ($sub['umbral'] ?? CaseBuilder::VEMP_DEFAULTS[$subtipo]['umbral']);
                $desv = is_array($sub['desviaciones'] ?? null) ? $sub['desviaciones'] : [];

                $series = [];
                foreach (CaseWaveforms::serieIntensidades($umbral, 100.0, 10.0) as $nivel) {
                    $series[] = [
                        'rotulo' => self::db($nivel),
                        'pts' => CaseWaveforms::trazoVemp($subtipo, $nivel, $umbral, $desv),
                    ];
                }
                $this->pdf->text(
                    $xPanel,
                    $this->y + self::ASCENDENTE * 7,
                    CaseBuilder::VEMP_SUBTIPO_LABELS[$subtipo],
                    7,
                    true,
                    $color
                );
                CaseCharts::waveformStack(
                    $this->pdf,
                    $xPanel,
                    $this->y + 9,
                    $anchoPanel,
                    $altoPanel,
                    $series,
                    $color,
                    40.0
                );
                $xPanel += $anchoPanel + 12;
            }
            $this->y += $altoPanel + 20;
        }

        // Umbral y desviaciones de los dos oídos, en columnas.
        $filas = [['Subtipo', 'Umbral OD', 'Umbral OI', 'Picos OD (lat / amp)', 'Picos OI (lat / amp)']];
        foreach (CaseBuilder::VEMP_SUBTIPOS as $subtipo) {
            $celda = [];
            $umbral = [];
            foreach (['od', 'oi'] as $ladoForm) {
                $sub = is_array($porLado[$ladoForm]['subtipos'][$subtipo] ?? null)
                    ? $porLado[$ladoForm]['subtipos'][$subtipo]
                    : [];
                $umbral[$ladoForm] = self::db((float) ($sub['umbral'] ?? CaseBuilder::VEMP_DEFAULTS[$subtipo]['umbral'])) . ' dB';
                $desv = is_array($sub['desviaciones'] ?? null) ? $sub['desviaciones'] : [];
                $picos = [];
                foreach (CaseBuilder::VEMP_PEAKS[$subtipo] as $pico) {
                    $picos[] = sprintf(
                        '%s %+.1f/%+.1f',
                        $pico,
                        (float) ($desv[$pico]['lat'] ?? 0),
                        (float) ($desv[$pico]['amp'] ?? 0)
                    );
                }
                $celda[$ladoForm] = implode('  ', $picos);
            }
            $filas[] = [
                CaseBuilder::VEMP_SUBTIPO_LABELS[$subtipo],
                $umbral['od'],
                $umbral['oi'],
                $celda['od'],
                $celda['oi'],
            ];
        }
        $this->tabla($filas, [0.22, 0.13, 0.13, 0.26, 0.26], true);
        $this->parrafo(
            'Umbral en dB; las desviaciones van en ms de latencia y µV de amplitud sobre el valor normal de cada pico.',
            7
        );
    }

    /**
     * Anamnesis y hallazgos clínicos.
     *
     * Los datos vienen de cinco lugares distintos de la ficha --los
     * antecedentes marcados, los textos libres, los rasgos del paciente, la
     * sala y el acúfeno-- y por eso van como campos etiquetados y no como
     * párrafos sueltos: leyendo la columna izquierda se ve QUÉ se está
     * diciendo sin tener que deducirlo del texto.
     */
    private function clinica(array $data): void
    {
        $this->titulo('Anamnesis y hallazgos clínicos', 140.0);

        $anamnesis = (array) ($data['Anamnesis'] ?? []);
        $antecedentes = (array) ($anamnesis['antecedentes'] ?? []);
        $marcados = [];
        foreach (CaseBuilder::HIST_CHECKBOXES as $clave) {
            if (!empty($antecedentes[$clave])) {
                $marcados[] = CaseBuilder::HIST_LABELS[$clave] ?? $clave;
            }
        }

        $this->subtitulo('Historia');
        $this->campos([
            ['Antecedentes', $marcados === [] ? 'Ninguno marcado' : implode(', ', $marcados)],
            ['Medicamentos', (string) ($anamnesis['medicamentos'] ?? '')],
            ['Cirugías', (string) ($anamnesis['cirugias'] ?? '')],
            ['Otros', (string) ($anamnesis['otros'] ?? '')],
            ['Acúfeno', CaseBuilder::describeTinnitus((array) ($data['Tinnitus'] ?? []))],
        ]);

        $this->subtitulo('En la consulta');
        $this->campos([
            ['Comportamiento', (string) ($data['PatientBehavior'] ?? '')],
            ['Disposición', (string) ($data['PatientDisposition'] ?? 0) . ' / 100'],
        ]);

        // Quién cuenta esa historia: en un caso pediátrico el dato no sale
        // del paciente, y de quién sale es parte del ejercicio.
        $this->sala($data);

        // Otoscopia por fases: cada fase describe qué cambió desde la
        // anterior, así que se imprimen en orden y numeradas.
        $fases = (array) (($data['Otoscopia'] ?? [])['fases'] ?? []);
        $this->subtitulo('Otoscopia');
        if ($fases === []) {
            $this->parrafo('Sin otoscopia cargada.', 8);
        } else {
            foreach (array_values($fases) as $i => $fase) {
                $texto = trim((string) (is_array($fase) ? ($fase['texto'] ?? '') : ''));
                $this->campos([
                    ['Fase ' . ($i + 1), $texto !== '' ? $texto : ''],
                ]);
                $this->fotosOtoscopia($i);
            }
        }
    }

    /**
     * Quiénes entran a la consulta con el paciente y qué aporta cada uno.
     *
     * No es ambientación: en un caso pediátrico el dato clínico NO sale del
     * paciente, y de quién sale --y cuánto se le puede creer-- es parte del
     * ejercicio. Por eso van los rasgos de la entrevista (conciencia,
     * confiabilidad, cuánto interrumpe) junto al nombre, y quién es el
     * informante principal.
     *
     * La sala se relee con Sala::desde(), no del crudo: un caso guardado
     * antes de que existieran los acompañantes igual trae su sala de una
     * persona, y ahí esta sección no dice nada y se omite.
     */
    private function sala(array $data): void
    {
        $sala = Sala::desde($data);
        if (!Sala::tieneAcompanantes($sala)) {
            return;
        }

        $this->subtitulo('Quiénes vienen a la consulta');

        $filas = [['Quién', 'Edad', 'Informa', 'Conciencia', 'Confiab.', 'Interrumpe']];
        foreach ($sala['personas'] as $persona) {
            $filas[] = [
                Sala::etiqueta($persona) . ($persona['es_paciente'] ? ' - paciente' : ''),
                $persona['edad'] > 0 ? $persona['edad'] . ' años' : '-',
                $persona['informante'] ? 'principal' : '-',
                (string) $persona['conciencia'],
                (string) $persona['confiabilidad'],
                Sala::nivelInterrupcion((int) $persona['interrumpe']),
            ];
        }
        $this->tabla($filas, [0.34, 0.1, 0.13, 0.14, 0.13, 0.16], true);
        $this->parrafo(
            'Conciencia y confiabilidad van de 0 a 100: cuánto nota esa persona el problema y cuánto se le '
            . 'puede creer lo que cuenta. "Interrumpe" es cuánto se mete cuando la pregunta era para el paciente.',
            7
        );
        // La edad que manda es la del paciente DE LA SALA: en un caso
        // pediátrico la ficha puede traer la edad del adulto que consulta.
        $paciente = Sala::paciente($sala);
        $edadPaciente = (int) ($paciente['edad'] ?? ($data['edad'] ?? 0));
        $this->parrafo(
            'Qué puede contar el paciente por su edad: '
            . (Sala::CAPACIDAD_DESC[Sala::capacidad($edadPaciente)] ?? ''),
            7
        );

        // Lo que cada acompañante trae escrito: su versión de la historia y
        // cómo se comporta en la consulta. Es el texto con el que el LLM lo
        // hace hablar, así que es exactamente lo que el alumno va a escuchar.
        foreach ($sala['personas'] as $persona) {
            $version = trim((string) $persona['version']);
            $comportamiento = trim((string) $persona['comportamiento']);
            if ($version === '' && $comportamiento === '') {
                continue;
            }
            $this->espacio(40);
            $this->pdf->text(
                self::MARGEN,
                $this->y + self::ASCENDENTE * 8,
                Sala::etiqueta($persona),
                8,
                true,
                self::GRIS_TITULO
            );
            $this->y += 12;
            $campos = [];
            if ($version !== '') {
                $campos[] = ['Su versión', $version];
            }
            if ($comportamiento !== '') {
                $campos[] = ['En la consulta', $comportamiento];
            }
            $this->campos($campos, 78.0, 7.5);
        }
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

    /**
     * Campos de ficha: etiqueta a la izquierda y valor a la derecha, con el
     * valor ENVUELTO y una línea fina entre filas.
     *
     * Existe porque una tabla no envuelve texto y la anamnesis son párrafos
     * largos: sin esto quedaban como texto suelto uno abajo del otro, sin
     * que se viera de dónde sale cada cosa.
     *
     * @param array<int,array{0:string,1:string}> $campos etiqueta => valor
     */
    private function campos(array $campos, float $anchoEtiqueta = 96.0, float $size = 8.0): void
    {
        foreach ($campos as [$etiqueta, $valor]) {
            $valor = trim($valor) !== '' ? trim($valor) : '--';
            $anchoValor = $this->anchoContenido - $anchoEtiqueta;
            $lineas = count($this->pdf->wrapText($valor, $size, $anchoValor));
            $alto = max(1, $lineas) * $size * 1.35;

            $this->espacio($alto + 6);
            $base = $this->y + self::ASCENDENTE * $size;
            $this->pdf->text(self::MARGEN, $base, $etiqueta, $size, true, self::GRIS_SUAVE);
            $this->pdf->textBlock(
                self::MARGEN + $anchoEtiqueta,
                $base,
                $valor,
                $anchoValor,
                $size,
                false,
                0,
                self::GRIS_TEXTO
            );
            $this->y += $alto + 2;
            $this->pdf->line(self::MARGEN, $this->y, self::MARGEN + $this->anchoContenido, $this->y, 0.3, '#dddddd');
            $this->y += 3;
        }
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
    /**
     * Tabla en el ancho completo, avanzando la Y del documento. `$fraccion`
     * la angosta: una tabla de cinco números repartidos en toda la hoja se
     * lee peor que una compacta, porque el ojo tiene que cruzar el folio
     * entero para juntar la fila.
     */
    private function tabla(array $filas, array $anchos, bool $conCabecera = false, float $fraccion = 1.0): void
    {
        $alto = 12.0 * count($filas) + 4;
        $this->espacio($alto);
        $ancho = $this->anchoContenido * max(0.1, min(1.0, $fraccion));
        $this->y = $this->tablaEn(self::MARGEN, $this->y, $ancho, $filas, $anchos, $conCabecera) + 4;
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

    /**
     * Celda de enmascaramiento: "mín - máx (meseta)", o el guión cuando esa
     * frecuencia no necesita ruido.
     *
     * @param array{cruza:bool,min:float,max:float,dilema:bool,meseta:float} $via
     */
    private static function celdaMkg(array $via): string
    {
        if (!$via['cruza']) {
            return '(-)';
        }
        if ($via['dilema']) {
            return 'DILEMA (' . self::db($via['meseta']) . ')';
        }
        return self::db($via['min']) . ' - ' . self::db($via['max']) . ' (' . self::db($via['meseta']) . ')';
    }

    /** Umbral del reflejo, o (-) cuando no hay respuesta en toda la escala. */
    private static function reflejo(float $db): string
    {
        return $db >= CaseProfile::REFLEX_ABSENT_DB ? '(-)' : (string) (int) round($db);
    }

    private static function db(float $v): string
    {
        return (string) (int) round($v);
    }

    /**
     * Al paso del audiómetro: 5 dB. Un promedio de umbrales da decimales
     * (42.5), pero ningún audiómetro los puede presentar, así que informar
     * "42" sugiere una precisión que el examen no tiene.
     */
    private static function paso5(float $v): float
    {
        return round($v / 5) * 5;
    }

    private static function db5(float $v): string
    {
        return (string) (int) self::paso5($v);
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
