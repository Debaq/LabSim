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
require_once __DIR__ . '/CaseCompleteness.php';

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
    /** Y a partir de la cual hay que cortar la página (deja lugar al pie). */
    private const PIE = 46.0;

    /**
     * Alto de la letra sobre la línea base, como fracción del cuerpo. La Y
     * del documento apunta al BORDE SUPERIOR del bloque que sigue, y el PDF
     * escribe desde la línea base: sin este corrimiento, todo párrafo que
     * viniera después de una tabla o de un gráfico se le montaba encima.
     */
    private const ASCENDENTE = 0.8;

    /**
     * El logo del backend, en JPEG. El original de la app es
     * resources/img/LogoBN.png (raíz del repo), que no se despliega con el
     * backend y además es PNG: MiniPdf solo lleva JPEG y convertirlo en cada
     * pedido obligaría a tener GD en el hosting. Se guarda ya convertido.
     */
    private const LOGO = __DIR__ . '/../resources/img/logo.jpg';

    /** Marca del pie, en todas las páginas. El año es el de impresión. */
    private const PIE_TEXTO = 'Desarrollado con LabSim %s para la simulación en evaluación auditiva y vestibular';

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
    private string $anio;
    private int $pagina = 1;

    private function __construct(string $caseId, string $encabezadoCorrido, string $anio)
    {
        $this->anio = $anio;
        $this->pdf = new MiniPdf();
        $this->anchoContenido = $this->pdf->pageWidth() - 2 * self::MARGEN;
        $this->y = self::MARGEN;
        $this->caseId = $caseId;
        $this->encabezadoCorrido = $encabezadoCorrido;
        $this->pie();
    }

    /**
     * Identidad de la ficha para el título del documento y el nombre del
     * archivo: número de caso, paciente y RUT, separados por guiones bajos.
     *
     * El paciente va abreviado --iniciales de los nombres y los apellidos
     * completos-- porque el nombre entero hace un archivo impresentable, y
     * el RUT va sin puntos: el punto en un nombre de archivo se lee como
     * extensión. Todo sin tildes ni eñes, por el mismo motivo.
     *
     * @param array{nombre?:string,apellido?:string,rut?:string} $patient
     */
    public static function identificador(string $caseId, array $patient = []): string
    {
        $partes = [self::soloArchivo($caseId)];

        $iniciales = '';
        foreach (preg_split('/\s+/', trim((string) ($patient['nombre'] ?? ''))) ?: [] as $nombre) {
            if ($nombre !== '') {
                $iniciales .= mb_strtoupper(mb_substr($nombre, 0, 1));
            }
        }
        if ($iniciales !== '') {
            $partes[] = self::soloArchivo($iniciales);
        }
        foreach (preg_split('/\s+/', trim((string) ($patient['apellido'] ?? ''))) ?: [] as $apellido) {
            if ($apellido !== '') {
                $partes[] = self::soloArchivo($apellido);
            }
        }

        $rut = str_replace('.', '', trim((string) ($patient['rut'] ?? '')));
        if ($rut !== '' && $rut !== 'N/D') {
            $partes[] = self::soloArchivo($rut);
        }

        return implode('_', array_filter($partes, static fn (string $p): bool => $p !== ''));
    }

    /** Deja solo lo que sobrevive a un nombre de archivo, sin tildes. */
    private static function soloArchivo(string $texto): string
    {
        $texto = strtr($texto, [
            'á' => 'a', 'é' => 'e', 'í' => 'i', 'ó' => 'o', 'ú' => 'u', 'ü' => 'u', 'ñ' => 'n',
            'Á' => 'A', 'É' => 'E', 'Í' => 'I', 'Ó' => 'O', 'Ú' => 'U', 'Ü' => 'U', 'Ñ' => 'N',
        ]);
        return trim((string) preg_replace('/[^A-Za-z0-9-]+/', '', $texto));
    }

    /**
     * @param array<string,mixed> $data cases.data
     * @param array{nombre?:string,rut?:string,fecha_nac?:string} $patient
     * @return string bytes del PDF
     */
    public static function build(string $caseId, array $data, array $patient = [], string $emisor = '', string $fecha = ''): string
    {
        $nombre = trim((string) ($patient['nombre'] ?? ''));
        $fecha = $fecha !== '' ? $fecha : date('d-m-Y');
        // El año del pie es el de la impresión, no el del caso: la marca
        // dice cuándo se generó este papel.
        $doc = new self($caseId, 'Ficha #' . $caseId . ($nombre !== '' ? ' - ' . $nombre : ''), date('Y'));
        // Lo que el visor muestra en la pestaña. Sin esto queda el nombre
        // del script que sirve el PDF (case_sheet_pdf.pdf).
        $doc->pdf->setTitle(self::identificador($caseId, $patient));
        $doc->portada($caseId, $data, $patient, $emisor, $fecha);
        $doc->resumenPorOido($data);
        // La historia antes que los exámenes, como se lee una ficha: quién
        // es el paciente y qué cuenta, y recién después qué mide cada
        // prueba.
        $doc->clinica($data);

        $doc->paginaNueva();
        $doc->audiometria($data);
        $doc->acumetria($data);
        // Las supraliminares van pegadas al tonal: son el mismo audiómetro y
        // se leen sobre los umbrales de arriba.
        $doc->supraliminares($data);
        $doc->logoaudiometria($data);

        $doc->paginaNueva();
        $doc->impedanciometria($data);

        $doc->paginaNueva();
        $doc->abr($data);

        $doc->paginaNueva();
        $doc->eoas($data);

        $doc->paginaNueva();
        $doc->vemp($data);
        return $doc->pdf->output();
    }

    // -----------------------------------------------------------------
    // Secciones
    // -----------------------------------------------------------------

    private function portada(string $caseId, array $data, array $patient, string $emisor, string $fecha): void
    {
        $xTitulo = self::MARGEN;
        $logo = PdfImage::jpegBytes(self::LOGO);
        if ($logo !== null) {
            // Alineado con el alto del título, no con el borde de la hoja,
            // y con aire hasta la línea del encabezado.
            $lado = 22.0;
            $this->pdf->imageJpeg($logo['data'], $logo['w'], $logo['h'], 'logo', self::MARGEN, $this->y - 14, $lado, $lado);
            $xTitulo += $lado + 9;
        }
        $this->pdf->text($xTitulo, $this->y + 4, 'Ficha del caso', 19, true, self::GRIS_TITULO);
        $this->pdf->textRight(self::MARGEN + $this->anchoContenido, $this->y + 4, '#' . $caseId, 13, true, self::GRIS_SUAVE);
        $this->y += 20;
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

        // Lo que el caso todavía no decidió. El docente que apoya en vivo
        // tiene que saber si va a encontrarse con un examen a medio armar
        // antes de que se lo encuentre el alumno.
        $pendientes = CaseCompleteness::pendingTexts($data);
        if ($pendientes !== []) {
            $this->pdf->text(
                self::MARGEN,
                $this->y + self::ASCENDENTE * 8,
                'Este caso tiene ' . count($pendientes) . ' ' . (count($pendientes) === 1 ? 'ficha sin decidir' : 'fichas sin decidir') . ':',
                8,
                true,
                CaseCharts::COLOR_OD
            );
            $this->y += 12;
            foreach ($pendientes as $pendiente) {
                $this->parrafo('- ' . $pendiente, 7.5);
            }
            $this->y += 4;
        }
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
                'huecos' => self::hayHuecos($aerea[$ladoForm], [2, 3, 4, 6])
                    || self::hayHuecos($osea[$ladoForm], [2, 3, 4, 6]),
            ];
        }

        $filas[] = ['Clasificación', self::tipoLabel($porLado['od']['tipo']), self::tipoLabel($porLado['oi']['tipo'])];
        $gap = static function (?float $aereo, ?float $oseo): ?float {
            return $aereo === null || $oseo === null ? null : $aereo - $oseo;
        };
        $filas[] = [
            'PTP aéreo (500-1k-2k Hz)',
            self::promedio2($porLado['od']['ptp']),
            self::promedio2($porLado['oi']['ptp']),
        ];
        $filas[] = [
            'Promedio BIAP aéreo (500-1k-2k-4k Hz)',
            self::promedio2($porLado['od']['biap']) . self::conGrado($porLado['od']['biap']),
            self::promedio2($porLado['oi']['biap']) . self::conGrado($porLado['oi']['biap']),
        ];
        $filas[] = [
            'Promedio BIAP óseo (500-1k-2k-4k Hz)',
            self::promedio2($porLado['od']['biapOsea']),
            self::promedio2($porLado['oi']['biapOsea']),
        ];
        $filas[] = [
            'Gap aéreo-óseo (500-1k-2k-4k Hz)',
            self::promedio2($gap($porLado['od']['biap'], $porLado['od']['biapOsea'])),
            self::promedio2($gap($porLado['oi']['biap'], $porLado['oi']['biapOsea'])),
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
        $aviso = $porLado['od']['huecos'] || $porLado['oi']['huecos']
            ? 'Hay frecuencias sin umbral: los promedios se calculan solo con las que responden. '
            : '';
        $this->parrafo(
            $aviso . 'Módulos derivados del perfil: '
            . ($autos === [] ? 'ninguno (todo cargado a mano)' : implode(', ', $autos)) . '.',
            7.5
        );
    }

    private function audiometria(array $data): void
    {
        $this->titulo('Audiometría tonal', 195.0);

        $aerea = self::desarmar($data['Aerea'] ?? []);
        $osea = self::desarmar($data['Osea'] ?? []);
        $ldl = self::desarmar($data['LDL'] ?? []);
        // "LDL no medido" se guarda como 130 en las nueve frecuencias (ver
        // case_create.php): si ninguna difiere, ese oído no tiene LDL.
        $ldlMedido = [];
        foreach (['od', 'oi'] as $lado) {
            $ldlMedido[$lado] = count(array_filter($ldl[$lado], static fn ($v) => (int) $v !== 130)) > 0;
        }

        $alto = 168.0;
        $this->espacio($alto + 22);
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
            'Rango con la meseta entre paréntesis; / = ese umbral no cruza. Aérea: mín = UAE - AI - UONE '
            . '+ UANE, máx = UOE + AI. Ósea: mín = UOE - UONE + UANE + efecto oclusivo, máx = UOE + AI. '
            . 'Calculado con NBN (CE 0).',
            6.5
        );
    }

    /**
     * Acumetría, escrita como se escribe a mano y en dos columnas.
     *
     * Rinne y Weber comparten el mismo eje --OD a la izquierda, la
     * frecuencia al medio, OI a la derecha-- y el mismo estilo de fila. Son
     * dos lecturas del mismo diapasón: ponerle tabla a una y otra cosa a la
     * otra las hacía parecer exámenes distintos, y apiladas gastaban el doble
     * de alto para cuatro líneas.
     *
     * El Rinne se anota (+) cuando la aérea supera a la ósea y (-) cuando es
     * al revés; el falso negativo va escrito, porque no es un resultado de
     * ese oído. El Weber no es un resultado por oído sino uno solo: una
     * flecha hacia el lado al que lateraliza, y dos flechas cuando no.
     */
    private function acumetria(array $data): void
    {
        $this->titulo('Acumetría (diapasones)', 100.0);

        $gap = 30.0;
        $xRinne = self::MARGEN + 100.0;
        $xWeber = self::MARGEN + 300.0;
        $this->espacio(16 + 12 + 14 * count(CaseBuilder::ACUMETRIA_FREQS));
        $yBase = $this->y;

        // --- Rinne, a la izquierda ------------------------------------
        $y = $yBase;
        $this->pdf->text(self::MARGEN, $y + self::ASCENDENTE * 8.5, 'Rinne', 8.5, true, self::GRIS_TITULO);
        $y += 14;
        $base = $y + self::ASCENDENTE * 7;
        $this->pdf->textRight($xRinne - $gap, $base, 'OD', 7, true, CaseCharts::COLOR_OD);
        $this->pdf->textCenter($xRinne, $base, 'Frecuencia', 7, true, self::GRIS_SUAVE);
        $this->pdf->text($xRinne + $gap, $base, 'OI', 7, true, CaseCharts::COLOR_OI);
        $y += 12;

        foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $idx) {
            $base = $y + self::ASCENDENTE * 8;
            $this->pdf->textRight(
                $xRinne - $gap,
                $base,
                self::rinne((string) ($data['Rinne'][$hz]['od'] ?? 'positivo')),
                8,
                true,
                CaseCharts::COLOR_OD
            );
            $this->pdf->textCenter($xRinne, $base, self::hz((int) $hz) . ' Hz', 8, true, self::GRIS_TITULO);
            $this->pdf->text(
                $xRinne + $gap,
                $base,
                self::rinne((string) ($data['Rinne'][$hz]['oi'] ?? 'positivo')),
                8,
                true,
                CaseCharts::COLOR_OI
            );
            $y += 14;
        }
        $finRinne = $y;

        // --- Weber, a la derecha, con las filas alineadas -------------
        $y = $yBase;
        $this->pdf->text($xWeber - 60, $y + self::ASCENDENTE * 8.5, 'Weber', 8.5, true, self::GRIS_TITULO);
        $y += 26;

        foreach (CaseBuilder::ACUMETRIA_FREQS as $hz => $idx) {
            $lado = (string) ($data['Weber'][$hz] ?? 'centrado');
            $base = $y + self::ASCENDENTE * 8;
            $centro = $y + 4;

            // Las flechas ocupan las mismas columnas que los (+)/(-) del
            // Rinne. Se dibujan: el carácter -> no existe en WinAnsi, que es
            // la codificación del texto del PDF.
            if ($lado === 'od' || $lado === 'centrado') {
                $this->flecha($xWeber - $gap, $centro, -16.0, $lado === 'od' ? CaseCharts::COLOR_OD : self::GRIS_SUAVE);
            }
            if ($lado === 'oi' || $lado === 'centrado') {
                $this->flecha($xWeber + $gap, $centro, 16.0, $lado === 'oi' ? CaseCharts::COLOR_OI : self::GRIS_SUAVE);
            }
            $this->pdf->textCenter($xWeber, $base, self::hz((int) $hz) . ' Hz', 8, true, self::GRIS_TITULO);
            $this->pdf->text(
                $xWeber + 58,
                $base,
                CaseBuilder::WEBER_LABELS[$lado] ?? $lado,
                7.5,
                false,
                self::GRIS_TEXTO
            );
            $y += 14;
        }

        $this->y = max($finRinne, $y) + 4;
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
            // El eje llega a 2 mL, que es lo que trae el equipo: un pico más
            // alto se sale por arriba ahí y acá igual, así que se avisa en
            // vez de cambiarle la escala a esta ficha sola.
            $picoMl = CaseCharts::valoresTimpanograma($tipo)['estatica'];
            if ($picoMl > CaseCharts::ESCALA_TIMPANOGRAMA_ML) {
                $this->pdf->textRight(
                    $x + $ancho,
                    $this->y + self::ASCENDENTE * 8,
                    'pico sobre 2 mL, fuera de escala',
                    7,
                    false,
                    self::GRIS_TEXTO
                );
            }
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
        // En CONTRA el estímulo entra por el oído opuesto al de la sonda, así
        // que esas dos columnas --encabezado incluido-- llevan el color del
        // oído estimulado y no el de la columna. Es la misma convención con
        // la que el editor pinta el patrón (public/js/case/reflex-pattern.js).
        $finReflejos = $this->tablaEn(
            self::MARGEN,
            $yTablasZ,
            $anchoReflejos,
            $filas,
            [0.22, 0.19, 0.2, 0.19, 0.2],
            true,
            [
                0 => CaseCharts::COLOR_OI,
                1 => CaseCharts::COLOR_OD,
                2 => '',
                3 => CaseCharts::COLOR_OI,
                4 => CaseCharts::COLOR_OD,
            ]
        );

        // Al lado, los números de la curva. El caso guarda SOLO la letra de
        // Jerger: la compliance y la presión las sortea la app dentro de un
        // rango por letra, con una semilla por paciente que el backend no
        // puede reproducir. Por eso va el rango y no un número inventado
        // --el que lea el alumno va a caer ahí dentro. La gradiente sí es
        // predecible: se calcula igual que en el equipo, sobre la curva que
        // se dibuja arriba (ver CaseCharts::gradienteTimpanograma).
        $tipoOd = (string) ($data['Z_OD'] ?? 'A');
        $tipoOi = (string) ($data['Z_OI'] ?? 'A');
        $vOd = CaseCharts::valoresTimpanograma($tipoOd);
        $vOi = CaseCharts::valoresTimpanograma($tipoOi);
        $presion = static function (array $v): string {
            if ($v['plana']) {
                return 'sin pico';
            }

            return self::db($v['p_min']) . ' a ' . self::db($v['p_max']) . ' daPa';
        };
        $compliance = static function (array $v): string {
            // Un B queda por debajo de la resolución del equipo: "0,00 a
            // 0,00" se leería como un dato medido y no lo es.
            if ($v['c_max'] < 0.01) {
                return 'menor a 0.01 mL';
            }

            return number_format($v['c_min'], 2) . ' a ' . number_format($v['c_max'], 2) . ' mL';
        };
        $gradiente = static function (array $v): string {
            return number_format($v['gradiente'], 2);
        };
        $gradienteEquipo = static function (array $v): string {
            return number_format($v['gradiente_equipo'], 2);
        };

        $filasZ = [
            ['Timpanograma', 'OD', 'OI'],
            ['Tipo (Jerger)', $tipoOd, $tipoOi],
            ['Compliance estática', $compliance($vOd), $compliance($vOi)],
            ['Presión del pico', $presion($vOd), $presion($vOi)],
            ['Gradiente', $gradiente($vOd), $gradiente($vOi)],
            ['Gradiente en el equipo', $gradienteEquipo($vOd), $gradienteEquipo($vOi)],
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
        $this->parrafo(
            'El caso guarda sólo la letra de Jerger: la compliance y la presión las sortea el equipo '
            . 'dentro del rango de arriba, distintas para cada paciente, y la curva de acá usa el centro. '
            . 'El recuadro amarillo es de donde sale la gradiente --alto del pico por 100 daPa a su '
            . 'alrededor--, que es cuánto de ese alto conserva la curva en los bordes. La segunda fila '
            . 'es la que va a leer el alumno: el equipo dibuja todas las curvas con el mismo ancho, así '
            . 'que ahí da 0,85 en cualquier curva con pico y no distingue una letra de otra.',
            7
        );
    }

    private function logoaudiometria(array $data): void
    {
        $this->titulo('Logoaudiometría', 98.0);

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

        $alto = 98.0;
        $this->espacio($alto + 24);
        CaseCharts::logogram($this->pdf, self::MARGEN, $this->y, $this->anchoContenido * 0.55, $alto, $porLado);
        CaseCharts::legend($this->pdf, self::MARGEN + 26, $this->y + $alto + 8, 'SRT = vertical punteada, UMD = triángulo');

        $x = self::MARGEN + $this->anchoContenido * 0.6;
        $ancho = $this->anchoContenido * 0.4;
        $filas = [['', 'OD', 'OI']];
        $filas[] = ['SDT (dB)', self::db($porLado['od']['sdt']), self::db($porLado['oi']['sdt'])];
        $filas[] = ['SRT (dB)', self::db($porLado['od']['srt']), self::db($porLado['oi']['srt'])];
        // La UMD se anota como una sola cosa: "96 % a 70 dB". Partida en dos
        // filas se leía como si fueran dos resultados distintos.
        $filas[] = [
            'UMD',
            self::pct($porLado['od']['umd_pct']) . ' a ' . self::db($porLado['od']['umd_int']) . ' dB',
            self::pct($porLado['oi']['umd_pct']) . ' a ' . self::db($porLado['oi']['umd_int']) . ' dB',
        ];
        $filas[] = ['Rollover', $porLado['od']['recruit'] ? 'Sí' : 'No', $porLado['oi']['recruit'] ? 'Sí' : 'No'];
        $yTabla = $this->tablaEn($x, $this->y + 8, $ancho, $filas, [0.4, 0.3, 0.3], true);

        $this->y = max($this->y + $alto + 18, $yTabla + 4);
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

        // El LDL no va en números: ya está dibujado en el audiograma con su
        // propia línea. Repetir en una tabla lo que el gráfico muestra
        // obliga a leer dos veces lo mismo y a dudar de cuál manda.

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

        // --- Umbral por estímulo, contra el conductual ----------------
        // La columna que importa es la comparación: el ABR se lee en dB nHL
        // y el audiograma en dB HL, y el ejercicio es ver cuánto se separan.
        $aereaAbr = self::desarmar($data['Aerea'] ?? []);
        $filas = [['Estímulo', 'OD nHL', 'OD cond.', 'OI nHL', 'OI cond.']];
        foreach (array_keys($porLado['od']['umbrales']) as $estimulo) {
            $filas[] = [
                self::estimuloLabel((string) $estimulo),
                self::umbralAbr($porLado['od']['umbrales'][$estimulo] ?? null),
                self::conductual((string) $estimulo, $aereaAbr['od']),
                self::umbralAbr($porLado['oi']['umbrales'][$estimulo] ?? null),
                self::conductual((string) $estimulo, $aereaAbr['oi']),
            ];
        }
        $anchoTabla = ($this->anchoContenido - 16) / 2;
        $yTablas = $this->y;
        $finUmbrales = $this->tablaEn(self::MARGEN, $yTablas, $anchoTabla, $filas, [0.34, 0.17, 0.16, 0.17, 0.16], true);

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

        // --- Lo que el equipo va a mostrar a 80 dB --------------------
        // Latencias, amplitudes e interpicos del click a nivel alto, que es
        // como se leen los informes. Salen del mismo trazo de arriba, con
        // las desviaciones del caso ya aplicadas.
        $ondas80 = [];
        foreach (['od', 'oi'] as $ladoForm) {
            $datos = $porLado[$ladoForm];
            $ondas80[$ladoForm] = CaseWaveforms::ondasClick(
                80.0,
                (float) ($datos['umbrales']['click'] ?? 20),
                $datos['tipo'],
                $datos['neural'],
                $datos['desv'],
                $poblacion
            );
        }

        $limites = CaseWaveforms::limitesNormativos($poblacion, 80.0);

        $filas = [['A 80 dB nHL', 'OD lat', 'OD amp', 'OI lat', 'OI amp']];
        foreach (['I', 'III', 'V'] as $onda) {
            $techo = $limites['lat'][$onda][1];
            $filas[] = [
                'Onda ' . $onda,
                self::marcada(self::ms($ondas80['od'][$onda]), $ondas80['od'][$onda]['lat'], $techo, $ondas80['od'][$onda]),
                self::uv($ondas80['od'][$onda]),
                self::marcada(self::ms($ondas80['oi'][$onda]), $ondas80['oi'][$onda]['lat'], $techo, $ondas80['oi'][$onda]),
                self::uv($ondas80['oi'][$onda]),
            ];
        }
        foreach ([['I', 'III'], ['III', 'V'], ['I', 'V']] as [$desde, $hasta]) {
            $clave = $desde . '-' . $hasta;
            $techo = $limites['interpeak'][$clave][1];
            $filas[] = [
                'Interpico ' . $clave,
                self::interpicoMarcado($ondas80['od'], $desde, $hasta, $techo),
                '',
                self::interpicoMarcado($ondas80['oi'], $desde, $hasta, $techo),
                '',
            ];
        }
        // La razón V/I va con los demás valores medidos, en la columna de
        // amplitud: es una razón entre amplitudes.
        $filas[] = [
            'Razón V/I',
            '',
            self::razonVI($ondas80['od'], $limites['v_i_min']),
            '',
            self::razonVI($ondas80['oi'], $limites['v_i_min']),
        ];

        // Y la diferencia interaural de la V, que no es de un oído sino de
        // la comparación: valor único, en la primera columna de valores.
        $vOd = $ondas80['od']['V'];
        $vOi = $ondas80['oi']['V'];
        $hayIT5 = $vOd['amp'] >= CaseWaveforms::AMP_VISIBLE && $vOi['amp'] >= CaseWaveforms::AMP_VISIBLE;
        $it5 = $hayIT5 ? abs($vOd['lat'] - $vOi['lat']) : null;
        $filas[] = [
            'Dif. interaural V (IT5)',
            $it5 === null ? '--' : number_format($it5, 2) . ($it5 > $limites['interaural_v'] ? ' *' : ''),
            '',
            '',
            '',
        ];
        $yTablas2 = $this->y;
        $fin80 = $this->tablaEn(self::MARGEN, $yTablas2, $anchoTabla, $filas, [0.36, 0.16, 0.16, 0.16, 0.16], true);

        // --- Captura y FSP -------------------------------------------
        // El FSP decide cuándo el equipo da la curva por buena: sin estos
        // números el docente no puede anticipar si el alumno va a llegar al
        // objetivo o se va a quedar promediando.
        $cap = static fn (string $clave, $default): array => [
            (string) ($porLado['od']['cfg'][$clave] ?? $default),
            (string) ($porLado['oi']['cfg'][$clave] ?? $default),
        ];
        $fsp = static fn (string $clave, $default): array => [
            (string) ((($porLado['od']['cfg']['fsp_puntos'] ?? [])[$clave]) ?? $default),
            (string) ((($porLado['oi']['cfg']['fsp_puntos'] ?? [])[$clave]) ?? $default),
        ];
        $alcanza = static function (string $lado) use ($porLado): string {
            $puntos = $porLado[$lado]['cfg']['fsp_puntos'] ?? [];
            $objetivo = (float) ($puntos['objetivo'] ?? 3.0);
            if ((float) ($puntos['800'] ?? 2.3) >= $objetivo) {
                return 'Sí, a 800';
            }
            if ((float) ($puntos['2000'] ?? 2.8) >= $objetivo) {
                return 'Sí, a 2000';
            }
            return 'No llega';
        };

        $filas = [['Captura y FSP', 'OD', 'OI']];
        $filas[] = ['Reproducible', self::repro($porLado['od']['cfg']), self::repro($porLado['oi']['cfg'])];
        $filas[] = array_merge(['Jitter si no repro. (ms)'], $cap('repro_var', 0.2));
        $filas[] = array_merge(['Promediaciones'], $cap('average_objetivo', 2000));
        $filas[] = array_merge(['Inquietud (0-1)'], $cap('inquietud', 0));
        $filas[] = array_merge(['PAM (0-1)'], $cap('pam', 0));
        $filas[] = array_merge(['FSP @ 800 prom.'], $fsp('800', 2.3));
        $filas[] = array_merge(['FSP @ 2000 prom.'], $fsp('2000', 2.8));
        $filas[] = array_merge(['FSP objetivo'], $fsp('objetivo', 3.0));
        $filas[] = ['¿Alcanza el objetivo?', $alcanza('od'), $alcanza('oi')];

        $finCap = $this->tablaEn(
            self::MARGEN + $anchoTabla + 16,
            $yTablas2,
            $anchoTabla,
            $filas,
            [0.46, 0.27, 0.27],
            true
        );
        $this->y = max($fin80, $finCap) + 6;

        // --- La referencia con la que se leen esos números -------------
        // Media ± 2 DE de la población que le toca al paciente por edad y
        // sexo, con la latencia corrida por la misma función L-I que dibuja
        // la curva. Son los mismos límites con los que el módulo juzga la
        // tabla del alumno.
        $filas = [['Referencia · ' . self::poblacionLabel($poblacion) . ' · 80 dB', 'Normal']];
        foreach (['I', 'III', 'V'] as $onda) {
            $filas[] = ['Onda ' . $onda, self::rango($limites['lat'][$onda])];
        }
        foreach (['I-III', 'III-V', 'I-V'] as $clave) {
            $filas[] = ['Interpico ' . $clave, self::rango($limites['interpeak'][$clave])];
        }

        $filas[] = ['Razón V/I', 'mayor que ' . number_format($limites['v_i_min'], 2)];
        $filas[] = ['Dif. interaural V (IT5)', 'hasta ' . number_format($limites['interaural_v'], 2)];

        $yRef = $this->y;
        $finRef = $this->tablaEn(self::MARGEN, $yRef, $anchoTabla, $filas, [0.46, 0.54], true);
        $this->y = $finRef + 4;
        $this->parrafo('* fuera de la referencia (la razón V/I, por debajo).', 6.5);

        // Las desviaciones cargadas a mano, solo si hay alguna: en cero no
        // dicen nada y los valores de arriba ya las llevan aplicadas.
        foreach (['od' => 'OD', 'oi' => 'OI'] as $ladoForm => $lado) {
            $partes = [];
            foreach (['onda_I' => 'I', 'onda_III' => 'III', 'onda_V' => 'V'] as $clave => $onda) {
                $lat = (float) ($porLado[$ladoForm]['desv'][$clave]['lat'] ?? 0);
                $amp = (float) ($porLado[$ladoForm]['desv'][$clave]['amp'] ?? 0);
                if (abs($lat) < 0.001 && abs($amp) < 0.001) {
                    continue;
                }
                $partes[] = sprintf('%s %+.2f ms / %+.2f µV', $onda, $lat, $amp);
            }
            $falsaV = is_array($porLado[$ladoForm]['cfg']['falsa_v'] ?? null) ? $porLado[$ladoForm]['cfg']['falsa_v'] : [];
            if (((float) ($falsaV['amp'] ?? 0)) > 0) {
                $partes[] = sprintf('falsa onda V %s µV a %s ms', (string) $falsaV['amp'], (string) ($falsaV['lat'] ?? 5.6));
            }
            if ($partes === []) {
                continue;
            }
            $this->parrafo(
                $lado . ' -- cargado a mano: ' . implode('   ', $partes),
                6.5,
                null,
                $ladoForm === 'od' ? CaseCharts::COLOR_OD : CaseCharts::COLOR_OI
            );
        }
    }

    /**
     * Acúfeno: la frase que escucha el paciente, y detrás los datos con los
     * que el alumno va a tener que cuadrar su acufenometría.
     */
    private static function acufeno(array $tinnitus): string
    {
        $frase = CaseBuilder::describeTinnitus($tinnitus);
        if (!CaseBuilder::tinnitusPresente($tinnitus)) {
            return $frase;
        }
        $datos = [
            (string) ($tinnitus['ruido'] ?? ''),
            self::hz((int) ($tinnitus['frecuencia'] ?? 0)) . ' Hz',
            (string) ($tinnitus['lateralidad'] ?? 'craneal'),
        ];
        if (($tinnitus['lateralidad'] ?? '') === 'unilateral') {
            $datos[] = strtoupper((string) ($tinnitus['oido'] ?? 'od'));
        }
        if (($tinnitus['lateralidad'] ?? '') === 'bilateral' && ($tinnitus['predominio'] ?? 'igual') !== 'igual') {
            $datos[] = 'predomina ' . strtoupper((string) $tinnitus['predominio']);
        }
        $datos[] = empty($tinnitus['permanente']) ? 'ocasional' : 'permanente';
        if (!empty($tinnitus['pulsatil'])) {
            $datos[] = 'pulsátil';
        }
        return $frase . '  [' . implode(' · ', array_filter($datos)) . ']';
    }

    /**
     * Razón V/I medida. Hace falta que la I se vea: sin ella no hay razón
     * que calcular, y no es lo mismo que una razón baja.
     */
    private static function razonVI(array $ondas, float $minimo): string
    {
        if ($ondas['I']['amp'] < CaseWaveforms::AMP_VISIBLE || $ondas['V']['amp'] < CaseWaveforms::AMP_VISIBLE) {
            return '--';
        }
        $razon = $ondas['V']['amp'] / $ondas['I']['amp'];
        // Acá el asterisco marca lo que queda POR DEBAJO: una V chica
        // respecto de la I es el hallazgo, no una V grande.
        return number_format($razon, 2) . ($razon < $minimo ? ' *' : '');
    }

    /** Agrega el asterisco si el valor se pasa del techo normativo. */
    private static function marcada(string $texto, float $valor, float $techo, array $onda): string
    {
        if ($texto === '--' || $onda['amp'] < CaseWaveforms::AMP_VISIBLE) {
            return $texto;
        }
        return $valor > $techo ? $texto . ' *' : $texto;
    }

    /** Interpico con su asterisco. */
    private static function interpicoMarcado(array $ondas, string $desde, string $hasta, float $techo): string
    {
        $texto = self::interpico($ondas, $desde, $hasta);
        if ($texto === '--') {
            return $texto;
        }
        return ($ondas[$hasta]['lat'] - $ondas[$desde]['lat']) > $techo ? $texto . ' *' : $texto;
    }

    /** @param array{0:float,1:float} $rango */
    private static function rango(array $rango): string
    {
        return number_format($rango[0], 2) . ' - ' . number_format($rango[1], 2);
    }

    /** Nombre legible de la población normativa. */
    private static function poblacionLabel(string $poblacion): string
    {
        return [
            'adult_male' => 'adulto',
            'adult_female' => 'adulta',
            'child' => 'niño',
            'neonate' => 'neonato',
            'elderly' => 'adulto mayor',
        ][$poblacion] ?? $poblacion;
    }

    /** Latencia de una onda a ese nivel, o -- si no se ve. */
    private static function ms(array $onda): string
    {
        return $onda['amp'] >= CaseWaveforms::AMP_VISIBLE ? number_format($onda['lat'], 2) : '--';
    }

    /** Amplitud de una onda, o -- si no se ve. */
    private static function uv(array $onda): string
    {
        return $onda['amp'] >= CaseWaveforms::AMP_VISIBLE ? number_format($onda['amp'], 2) : '--';
    }

    /** Interpico entre dos ondas: hace falta que las DOS se vean. */
    private static function interpico(array $ondas, string $desde, string $hasta): string
    {
        if ($ondas[$desde]['amp'] < CaseWaveforms::AMP_VISIBLE || $ondas[$hasta]['amp'] < CaseWaveforms::AMP_VISIBLE) {
            return '--';
        }
        return number_format($ondas[$hasta]['lat'] - $ondas[$desde]['lat'], 2);
    }

    /**
     * Si la curva es reproducible. Un caso guardado antes de que existiera
     * la casilla no trae la clave y se toma como reproducible, igual que
     * hace CaseBuilder al releer la ficha.
     */
    private static function repro(array $cfg): string
    {
        if (!array_key_exists('repro', $cfg)) {
            return 'Sí';
        }
        return empty($cfg['repro']) ? 'No' : 'Sí';
    }

    /**
     * Umbral conductual (dB HL) con el que se compara cada estímulo del ABR.
     *
     * Sale de CaseProfile::STIM_WEIGHTS, que es la misma tabla con la que el
     * motor deriva el umbral electrofisiológico: el burst es frecuencial y
     * pesa su propia frecuencia; el click pesa 2, 3 y 4 kHz, que es la zona
     * coclear que lo domina.
     *
     * Los chirp quedan sin referencia a propósito. Hoy el catálogo tiene
     * "CE-Chirp" y "LS-Chirp" como si fueran dos estímulos de banda ancha, y
     * eso está mal: falta separar el NB-chirp, que es frecuencial, del
     * CE-chirp de banda ancha. Poner un promedio ahí sería tapar el error
     * con un número.
     *
     * @param array<int,float> $aereaLado umbrales aéreos del oído
     */
    private static function conductual(string $estimulo, array $aereaLado): string
    {
        if (strpos($estimulo, 'chirp') !== false) {
            return '--';
        }
        $pesos = CaseProfile::STIM_WEIGHTS[$estimulo] ?? [];
        $suma = 0.0;
        $total = 0.0;
        foreach ($pesos as $hz => $peso) {
            $i = array_search((int) $hz, CaseBuilder::FREQUENCIES, true);
            if ($i === false) {
                continue;
            }
            $umbral = (float) ($aereaLado[$i] ?? 0);
            // Una frecuencia sin respuesta no entra al promedio: el 130 no
            // es un umbral y metido en la cuenta inventa la referencia
            // contra la que se lee el ABR.
            if ($umbral >= CaseProfile::SIN_RESPUESTA_DB) {
                continue;
            }
            $suma += $umbral * $peso;
            $total += $peso;
        }
        return $total > 0 ? self::db($suma / $total) : 'sin resp.';
    }

    /** Umbral del ABR, o el aviso de que no hubo respuesta. */
    private static function umbralAbr($db): string
    {
        // Abreviado: la columna es angosta y "sin respuesta" se montaba
        // sobre la de al lado.
        return $db === null ? 'sin resp.' : self::db((float) $db);
    }

    /**
     * Las cuatro pruebas de OEA: los cuatro gráficos en cuadrícula y, abajo,
     * los números que el alumno va a leer del equipo.
     */
    private function eoas(array $data): void
    {
        $this->titulo('Emisiones otoacústicas (OEA)', 260.0);

        $eoas = is_array($data['EOAS'] ?? null) ? $data['EOAS'] : [];
        $cfg = [
            'od' => is_array($eoas['OD'] ?? null) ? $eoas['OD'] : [],
            'oi' => is_array($eoas['OI'] ?? null) ? $eoas['OI'] : [],
        ];
        $pruebas = ['od' => CaseOae::pruebas($cfg['od']), 'oi' => CaseOae::pruebas($cfg['oi'])];

        $ancho = ($this->anchoContenido - 14) / 2;
        $alto = 104.0;
        $xDer = self::MARGEN + $ancho + 14;

        // --- Fila 1: TEOAE y DP-grama --------------------------------
        $this->espacio(2 * ($alto + 26) + 10);
        $yFila1 = $this->y;

        // El TEOAE trae los dos oídos en un solo panel: una barra por oído y
        // banda con el ruido superpuesto en gris adentro. Lo que asoma por
        // encima del gris es la relación señal/ruido.
        $bandasTe = array_keys($pruebas['od']['teoae']['bandas']);
        $senalTe = [];
        $ruidoTe = [];
        $pasaTe = [];
        foreach (['od', 'oi'] as $lado) {
            foreach ($bandasTe as $hz) {
                $banda = $pruebas[$lado]['teoae']['bandas'][$hz];
                $senalTe[$lado][$hz] = $banda['respuesta'];
                $ruidoTe[$lado][$hz] = $pruebas[$lado]['teoae']['piso'];
                $pasaTe[$lado][$hz] = $banda['pasa'];
            }
        }
        $this->pdf->text(self::MARGEN, $yFila1 + self::ASCENDENTE * 7, 'TEOAE (transientes)', 7, true, self::GRIS_TITULO);
        // -5 a 20 dB SPL: ahí cae todo lo que se lee en un transiente -- el
        // piso promediado (~2), la respuesta normal (8-12 según el JSON
        // normativo) y el criterio de 6 dB sobre el ruido.
        CaseCharts::oaeBars($this->pdf, self::MARGEN, $yFila1 + 9, $ancho, $alto, $bandasTe, $senalTe, $ruidoTe, $pasaTe, [-5.0, 20.0]);

        $xPie = self::MARGEN;
        $this->pdf->rectFilled($xPie, $yFila1 + $alto + 14, 5, 5, '#9a9a9a');
        $this->pdf->text($xPie + 7, $yFila1 + $alto + 18, 'ruido', 6, false, self::GRIS_TEXTO);
        $xPie += 7 + $this->pdf->textWidth('ruido', 6) + 9;
        foreach (['od' => CaseCharts::COLOR_OD, 'oi' => CaseCharts::COLOR_OI] as $lado => $colorLado) {
            $texto = strtoupper($lado) . ': ' . count(array_filter($pasaTe[$lado])) . '/' . count($bandasTe);
            $this->pdf->rectFilled($xPie, $yFila1 + $alto + 14, 5, 5, $colorLado);
            $this->pdf->text($xPie + 7, $yFila1 + $alto + 18, $texto, 6, false, $colorLado);
            $xPie += 7 + $this->pdf->textWidth($texto, 6) + 9;
        }
        $this->pdf->text($xPie, $yFila1 + $alto + 18, 'tick = pasa · R = no llega', 6, false, self::GRIS_TEXTO);

        $this->panelCurva($pruebas, 'dpoae', 'DP-grama (productos de distorsión)', $xDer, $yFila1, $ancho, $alto, [-30.0, 25.0], 'dB SPL');

        // --- Fila 2: SFOAE y SOAE ------------------------------------
        $yFila2 = $yFila1 + $alto + 26;
        $this->panelCurva($pruebas, 'sfoae', 'SFOAE (frecuencia específica)', self::MARGEN, $yFila2, $ancho, $alto, [-20.0, 15.0], 'dB');

        $soae = ['od' => CaseOae::soae($cfg['od']), 'oi' => CaseOae::soae($cfg['oi'])];
        $this->pdf->text($xDer, $yFila2 + self::ASCENDENTE * 7, 'SOAE (espontáneas, sin estímulo)', 7, true, self::GRIS_TITULO);
        CaseCharts::soaeSpectrum(
            $this->pdf,
            $xDer,
            $yFila2 + 9,
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
            },
            CaseOae::SOAE['picos_hz']
        );
        $xModo = $xDer;
        foreach (['od' => CaseCharts::COLOR_OD, 'oi' => CaseCharts::COLOR_OI] as $lado => $colorLado) {
            $detalle = [];
            foreach ($soae[$lado]['picos'] as $pico) {
                $detalle[] = self::hz((int) $pico['hz']) . ' Hz ' . self::db((float) $pico['db']) . ' dB';
            }
            $texto = strtoupper($lado) . ': ' . $soae[$lado]['modo']
                . ($detalle !== [] ? ' (' . implode(', ', $detalle) . ')' : '');
            $this->pdf->text($xModo, $yFila2 + $alto + 18, $texto, 6, false, $colorLado);
            $xModo += $this->pdf->textWidth($texto, 6) + 10;
        }
        $this->pdf->text($xDer, $yFila2 + $alto + 26, 'franja gris = donde se buscan los picos', 6, false, self::GRIS_SUAVE);

        $this->y = $yFila2 + $alto + 32;

        // --- Los números -----------------------------------------------
        // Los gráficos muestran la forma; acá está lo que el alumno va a
        // leer del equipo: la emisión, el piso de ruido y la relación entre
        // los dos, que es lo que decide el PASS/REFER.
        $filas = [['Prueba · banda', 'OD emis.', 'OD ruido', 'OD S/R', 'OI emis.', 'OI ruido', 'OI S/R']];
        foreach (['teoae' => 'TEOAE', 'dpoae' => 'DP', 'sfoae' => 'SFOAE'] as $clave => $rotuloPrueba) {
            foreach (array_keys($pruebas['od'][$clave]['bandas']) as $hz) {
                $fila = [$rotuloPrueba . ' ' . self::hz((int) $hz)];
                foreach (['od', 'oi'] as $lado) {
                    $banda = $pruebas[$lado][$clave]['bandas'][$hz];
                    $emision = (float) $banda['respuesta'];
                    $piso = (float) ($banda['piso'] ?? $pruebas[$lado][$clave]['piso']);
                    $fila[] = number_format($emision, 1);
                    $fila[] = number_format($piso, 1);
                    // El S/R lleva el REFER pegado: son el mismo dato leído
                    // dos veces y separarlos obliga a comparar a mano.
                    $fila[] = number_format($emision - $piso, 1) . ($banda['pasa'] ? '' : ' R');
                }
                $filas[] = $fila;
            }
        }
        $this->tabla($filas, [0.22, 0.13, 0.13, 0.13, 0.13, 0.13, 0.13], true);
        $this->parrafo('En dB SPL (SFOAE en dB). S/R = emisión menos ruido; R = no llega al criterio de esa prueba.', 6.5);

        // --- El perfil que armó esos números ---------------------------
        $yParams = $this->y;
        $filas = [['Perfil del oído', 'OD', 'OI']];
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
        $finParams = $this->tablaEn(self::MARGEN, $yParams, $ancho, $filas, [0.44, 0.28, 0.28], true);

        // La caída por banda: no es "del DP" -- el caso guarda UN perfil por
        // oído en las bandas de EOAS_FREQS y el cliente lo aplica a las
        // cuatro pruebas, cada una interpolando a las suyas.
        $cabecera = ['Caída del perfil (dB)'];
        foreach (CaseBuilder::EOAS_FREQS as $hz) {
            $cabecera[] = self::hz((int) $hz);
        }
        $filas = [$cabecera];
        foreach (['od' => 'OD', 'oi' => 'OI'] as $lado => $tag) {
            $cargadas = is_array($cfg[$lado]['desviaciones'] ?? null) ? $cfg[$lado]['desviaciones'] : [];
            $fila = [$tag . ' cargada'];
            foreach (CaseBuilder::EOAS_FREQS as $hz) {
                $fila[] = self::db((float) ($cargadas[(string) $hz] ?? $cargadas[$hz] ?? 0));
            }
            $filas[] = $fila;
        }
        $cols = count($cabecera);
        $this->y = $finParams + 6;
        $this->tabla($filas, array_merge([0.2], array_fill(0, $cols - 1, 0.8 / ($cols - 1))), true);
    }

    /**
     * Un panel de curva por banda con su área normal y el conteo por oído.
     * Lo comparten el DP-grama y el SFOAE, que se leen igual.
     */
    private function panelCurva(array $pruebas, string $clave, string $rotulo, float $x, float $y, float $ancho, float $alto, array $rangoY, string $unidad): void
    {
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

        $this->pdf->text($x, $y + self::ASCENDENTE * 7, $rotulo, 7, true, self::GRIS_TITULO);
        CaseCharts::oaePanel($this->pdf, $x, $y + 9, $ancho, $alto, $bandas, $area, $piso, $porLado, $rangoY, $unidad);

        $xResumen = $x;
        foreach (['od' => CaseCharts::COLOR_OD, 'oi' => CaseCharts::COLOR_OI] as $lado => $colorLado) {
            $pasan = 0;
            foreach ($pruebas[$lado][$clave]['bandas'] as $banda) {
                $pasan += $banda['pasa'] ? 1 : 0;
            }
            $texto = strtoupper($lado) . ': ' . $pasan . '/' . count($bandas) . ' sobre el ruido';
            $this->pdf->text($xResumen, $y + $alto + 18, $texto, 6, false, $colorLado);
            $xResumen += $this->pdf->textWidth($texto, 6) + 10;
        }
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
        // Los normativos del VEMP también son por población: un niño tiene
        // la p13 casi un milisegundo antes que un adulto mayor.
        $poblacion = CaseWaveforms::poblacion(
            isset($data['edad']) ? (int) $data['edad'] : null,
            (int) ($data['gender'] ?? 0)
        );
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
                    $pts = CaseWaveforms::trazoVemp($subtipo, $nivel, $umbral, $desv, 40.0, 200, $poblacion);
                    $picosNivel = CaseWaveforms::picosVemp($subtipo, $nivel, $umbral, $desv, $poblacion);
                    $marcas = [];
                    // Sin respuesta a ese nivel no se marca nada: un trazo
                    // plano con "p13" encima enseña a marcar lo que no está.
                    if (CaseWaveforms::hayRespuestaVemp($subtipo, $picosNivel, $poblacion)) {
                        foreach ($picosNivel as $nombre => $pico) {
                            // El valor se lee del TRAZO y no de la gaussiana
                            // del pico: p13 y n23 están a 10 ms y se solapan,
                            // así que la marca tiene que caer sobre la línea.
                            $marcas[] = [
                                't' => $pico['lat'],
                                'v' => self::valorEn($pts, $pico['lat']),
                                'texto' => $nombre,
                            ];
                        }
                    }
                    $series[] = [
                        'rotulo' => self::db($nivel),
                        'pts' => $pts,
                        'marcas' => $marcas,
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

        // Umbral, amplitud y asimetría: lo que se lee de un VEMP. Antes acá
        // iban las DESVIACIONES, que en un caso sin retoques son todas
        // "+0.0/+0.0" y no dicen nada.
        $filas = [['Subtipo', 'Umbral OD', 'Umbral OI', 'p-p OD (µV)', 'p-p OI (µV)', 'Asimetría']];
        $picos100 = [];
        foreach (CaseBuilder::VEMP_SUBTIPOS as $subtipo) {
            $pp = [];
            foreach (['od', 'oi'] as $ladoForm) {
                $sub = is_array($porLado[$ladoForm]['subtipos'][$subtipo] ?? null)
                    ? $porLado[$ladoForm]['subtipos'][$subtipo]
                    : [];
                $umbral = (float) ($sub['umbral'] ?? CaseBuilder::VEMP_DEFAULTS[$subtipo]['umbral']);
                $desv = is_array($sub['desviaciones'] ?? null) ? $sub['desviaciones'] : [];
                // A 100 dB, que es el nivel al que se informa la amplitud.
                $picos100[$subtipo][$ladoForm] = CaseWaveforms::picosVemp($subtipo, 100.0, $umbral, $desv, $poblacion);
                $picos100[$subtipo][$ladoForm . '_umbral'] = $umbral;
                $picos100[$subtipo][$ladoForm . '_hay'] = CaseWaveforms::hayRespuestaVemp(
                    $subtipo,
                    $picos100[$subtipo][$ladoForm],
                    $poblacion
                );
                $pp[$ladoForm] = $picos100[$subtipo][$ladoForm . '_hay']
                    ? self::picoAPico($picos100[$subtipo][$ladoForm])
                    : null;
            }
            $hayLosDos = $pp['od'] !== null && $pp['oi'] !== null;
            $filas[] = [
                CaseBuilder::VEMP_SUBTIPO_LABELS[$subtipo],
                self::db($picos100[$subtipo]['od_umbral']) . ' dB',
                self::db($picos100[$subtipo]['oi_umbral']) . ' dB',
                $pp['od'] === null ? 'no se observa' : number_format($pp['od'], 1),
                $pp['oi'] === null ? 'no se observa' : number_format($pp['oi'], 1),
                // Sin respuesta en un lado no hay razón que calcular: no es
                // una asimetría de 100 %, es que falta el dato.
                $hayLosDos ? self::asimetria($pp['od'], $pp['oi']) : '--',
            ];
        }
        $this->tabla($filas, [0.22, 0.14, 0.14, 0.17, 0.17, 0.16], true);

        // Y los picos en detalle, a 100 dB: latencia y amplitud de cada uno.
        $filas = [['A 100 dB', 'OD lat (ms)', 'OD amp (µV)', 'OI lat (ms)', 'OI amp (µV)']];
        foreach (CaseBuilder::VEMP_SUBTIPOS as $subtipo) {
            foreach (CaseBuilder::VEMP_PEAKS[$subtipo] as $pico) {
                $fila = [$subtipo . ' ' . $pico];
                foreach (['od', 'oi'] as $ladoForm) {
                    if (!$picos100[$subtipo][$ladoForm . '_hay']) {
                        $fila[] = 'no se observa';
                        $fila[] = '';
                        continue;
                    }
                    $fila[] = number_format($picos100[$subtipo][$ladoForm][$pico]['lat'], 1);
                    $fila[] = number_format($picos100[$subtipo][$ladoForm][$pico]['amp'], 1);
                }
                $filas[] = $fila;
            }
        }
        $this->tabla($filas, [0.24, 0.19, 0.19, 0.19, 0.19], true);
    }

    /** Amplitud pico a pico: la distancia entre el pico positivo y el negativo. */
    private static function picoAPico(array $picos): float
    {
        $valores = array_map(static fn (array $p): float => (float) $p['amp'], $picos);
        return $valores === [] ? 0.0 : max($valores) - min($valores);
    }

    /**
     * Razón de asimetría interaural, en %: la diferencia entre los dos oídos
     * sobre la suma. Es LA lectura del VEMP -- una amplitud sola no dice
     * nada sin el otro lado.
     */
    private static function asimetria(float $ppOd, float $ppOi): string
    {
        $suma = $ppOd + $ppOi;
        if ($suma <= 0.001) {
            return '--';
        }
        return (string) (int) round(abs($ppOd - $ppOi) / $suma * 100) . ' %';
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
            ['Acúfeno', self::acufeno((array) ($data['Tinnitus'] ?? []))],
        ]);

        // Si el texto lo escribió la IA, el docente tiene que saberlo antes
        // de apoyarse en él -- y si alguien lo leyó y lo dio por bueno.
        $ia = is_array($anamnesis['ia'] ?? null) ? $anamnesis['ia'] : [];
        if (!empty($ia['generado'])) {
            $verificado = !empty($ia['verificado'])
                ? 'verificado' . (($ia['verificado_por'] ?? '') !== '' ? ' por ' . $ia['verificado_por'] : '')
                    . (($ia['verificado_en'] ?? '') !== '' ? ' el ' . $ia['verificado_en'] : '')
                : 'SIN verificar';
            $this->campos([[
                'Borrador IA',
                'La anamnesis la escribió la IA'
                . (($ia['generado_en'] ?? '') !== '' ? ' el ' . $ia['generado_en'] : '') . '; ' . $verificado . '.',
            ]]);
        }

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

    /**
     * Arranca una página nueva, salvo que ya estemos al principio de una.
     *
     * La ficha tiene una paginación FIJA --generales y anamnesis, tonal,
     * impedanciometría, ABR, OEA, VEMP-- para que cada examen se pueda
     * imprimir, repartir o archivar suelto sin partirlo al medio.
     */
    private function paginaNueva(): void
    {
        if ($this->y <= self::MARGEN + 1) {
            return;
        }
        $this->abrirPagina();
    }

    /**
     * Página nueva con su encabezado corrido, su pie y su número.
     *
     * El número se escribe al abrir cada página y sin total: MiniPdf
     * escribe las páginas a medida que se llenan y no hay una segunda
     * pasada donde se pudiera saber cuántas son.
     */
    private function abrirPagina(): void
    {
        $this->pdf->addPage();
        $this->pagina++;
        $this->y = self::MARGEN;
        $this->pdf->text(self::MARGEN, $this->y - 12, $this->encabezadoCorrido, 7, false, self::GRIS_SUAVE);
        $this->pie();
    }

    /** Marca y número de página, al pie. */
    private function pie(): void
    {
        $y = $this->pdf->pageHeight() - 24;
        $this->pdf->line(self::MARGEN, $y - 8, self::MARGEN + $this->anchoContenido, $y - 8, 0.3, '#dddddd');
        $this->pdf->text(self::MARGEN, $y, sprintf(self::PIE_TEXTO, $this->anio), 6, false, self::GRIS_SUAVE);
        $this->pdf->textRight(self::MARGEN + $this->anchoContenido, $y, (string) $this->pagina, 6.5, true, self::GRIS_SUAVE);
    }

    /** Corta la página si lo que viene no entra. */
    private function espacio(float $necesario): void
    {
        if ($this->y + $necesario <= $this->pdf->pageHeight() - self::PIE) {
            return;
        }
        $this->abrirPagina();
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
        $this->y += 6;
        $this->pdf->rectFilled(self::MARGEN, $this->y, $this->anchoContenido, 14, self::FONDO_CABECERA);
        $this->pdf->text(self::MARGEN + 5, $this->y + 10.5, $texto, 10.5, true, self::GRIS_TITULO);
        $this->y += 18;
    }

    private function subtitulo(string $texto): void
    {
        // Reserva el subtítulo Y su primer párrafo, por el mismo motivo.
        $this->espacio(44);
        $this->y += 3;
        $this->pdf->text(self::MARGEN, $this->y + self::ASCENDENTE * 8.5, $texto, 8.5, true, self::GRIS_TITULO);
        $this->y += 12;
    }

    private function parrafo(string $texto, float $size = 8, ?float $ancho = null, ?string $color = null): void
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
            $color ?? self::GRIS_TEXTO
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
    private function tablaEn(
        float $x,
        float $y,
        float $ancho,
        array $filas,
        array $anchos,
        bool $conCabecera = false,
        array $coloresColumna = []
    ): float {
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
                // El color del oído manda sobre el gris: leer una ficha es
                // ir saltando entre OD y OI, y el color es lo que permite
                // hacerlo sin volver a la cabecera. Una columna puede pedir
                // el suyo (los reflejos contra van cruzados).
                $color = array_key_exists($j, $coloresColumna)
                    ? $coloresColumna[$j]
                    : self::colorDeOido((string) $celda);
                if ($color === null || $color === '') {
                    $color = $esCabecera ? self::GRIS_TITULO : self::GRIS_TEXTO;
                }
                $this->pdf->text(
                    $cx + 3,
                    $y + $altoFila - 3.5,
                    (string) $celda,
                    7.2,
                    $esCabecera || $primera,
                    $color
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

    /**
     * Promedio de las frecuencias que SÍ tienen umbral.
     *
     * Un 130 no es un umbral de 130 dB: es "no se midió" o "no hubo
     * respuesta", y meterlo en la cuenta inventa un promedio que nadie
     * puede informar. Devuelve null si no queda ninguna.
     *
     * @param array<int,float> $vals
     * @param array<int,int> $indices
     */
    private static function promedio(array $vals, array $indices): ?float
    {
        $suma = 0.0;
        $cuantas = 0;
        foreach ($indices as $i) {
            $valor = (float) ($vals[$i] ?? 0);
            if ($valor >= CaseCharts::SIN_UMBRAL_DB) {
                continue;
            }
            $suma += $valor;
            $cuantas++;
        }
        return $cuantas === 0 ? null : $suma / $cuantas;
    }

    /** ¿Alguna de esas frecuencias quedó sin umbral? */
    private static function hayHuecos(array $vals, array $indices): bool
    {
        foreach ($indices as $i) {
            if ((float) ($vals[$i] ?? 0) >= CaseCharts::SIN_UMBRAL_DB) {
                return true;
            }
        }
        return false;
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
        // Sin umbral no hay nada que enmascarar ni rango que calcular: es
        // distinto de "no cruza", y se dice distinto.
        if (!empty($via['sin_umbral'])) {
            return 'sin respuesta';
        }
        // "/" y no "(-)": en los reflejos el guión entre paréntesis es un
        // RESULTADO --ausente-- y acá significa que no hay nada que hacer.
        if (!$via['cruza']) {
            return '/';
        }
        if ($via['dilema']) {
            return 'DILEMA (' . self::db($via['meseta']) . ')';
        }
        return self::db($via['min']) . ' - ' . self::db($via['max']) . ' (' . self::db($via['meseta']) . ')';
    }

    /**
     * Valor del trazo en la muestra más cercana a $t.
     *
     * @param array<int,array{0:float,1:float}> $pts
     */
    private static function valorEn(array $pts, float $t): float
    {
        $mejor = 0.0;
        $distancia = INF;
        foreach ($pts as [$x, $y]) {
            $d = abs($x - $t);
            if ($d < $distancia) {
                $distancia = $d;
                $mejor = (float) $y;
            }
        }
        return $mejor;
    }

    /**
     * Color del oído que nombra un texto, o null si no nombra ninguno (o
     * los dos). Con límites de palabra: "sin vía ósea" no es un OD.
     */
    private static function colorDeOido(string $texto): ?string
    {
        $od = preg_match('/\bOD\b/', $texto) === 1;
        $oi = preg_match('/\bOI\b/', $texto) === 1;
        if ($od === $oi) {
            return null;
        }
        return $od ? CaseCharts::COLOR_OD : CaseCharts::COLOR_OI;
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
     * Promedio tal cual, con hasta dos decimales y sin ceros de relleno:
     * 42.5 sale "42.5" y 40 sale "40". El grado se lee sobre este mismo
     * valor, no sobre uno redondeado.
     */
    private static function promedio2(?float $v): string
    {
        if ($v === null) {
            return 'sin umbral';
        }
        $redondeado = round($v, 2);
        return rtrim(rtrim(number_format($redondeado, 2, '.', ''), '0'), '.');
    }

    /** El grado entre paréntesis, cuando hay promedio del que leerlo. */
    private static function conGrado(?float $promedio): string
    {
        return $promedio === null ? '' : '  (' . self::grado($promedio) . ')';
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
