<?php

declare(strict_types=1);

require_once __DIR__ . '/HelveticaWidths.php';
require_once __DIR__ . '/MiniPdf.php';
require_once __DIR__ . '/CaseBuilder.php';

/**
 * Los gráficos de la ficha, dibujados sobre un MiniPdf.
 *
 * Es el mismo dibujo que el docente ve en el editor, en otro lenguaje: las
 * escalas, los símbolos y las reglas de enmascaramiento son las de
 * public/js/case/audiogram.js, tympanogram.js y logogram.js. Si cambia una
 * convención clínica hay que cambiarla en los dos lados, y por eso cada
 * función dice de cuál JS es espejo.
 *
 * Cada método recibe un rectángulo (x, y, ancho, alto) en puntos y dibuja
 * ahí adentro: grilla, ejes rotulados y datos. No sabe de `cases.data` --
 * recibe arrays de números ya extraídos (eso lo hace CaseSheetPdf), así se
 * puede testear sin armar un caso completo.
 */
final class CaseCharts
{
    // Espejo de --color-od/--color-oi en public/css/case.css. Es la única
    // copia fuera del CSS, y existe porque un PDF no resuelve var().
    public const COLOR_OD = '#b33a3a';
    public const COLOR_OI = '#2255aa';

    private const COLOR_GRID = '#cfcfcf';
    private const COLOR_GRID_FUERTE = '#8f8f8f';
    private const COLOR_ROTULO = '#444444';

    /** Margen interno del recuadro para los rótulos de los ejes (pt). */
    private const EJE_IZQ = 24.0;
    private const EJE_SUP = 11.0;
    private const EJE_INF = 11.0;

    /**
     * Reglas de enmascaramiento: las mismas de airMasked()/boneMasked() en
     * public/js/case/audiogram.js. Públicas para que
     * tests/test_case_sheet_pdf.php pueda comprobar que las dos copias
     * siguen diciendo lo mismo -- el PDF y el editor tienen que dibujar el
     * mismo símbolo para el mismo umbral.
     */
    public const ATENUACION_AEREA_POR_FREQ = [35, 40, 40, 40, 40, 45, 45, 50, 50];
    public const GAP_ENMASCARA_OSEA = 10;

    /**
     * Campana por tipo Jerger: [presión del pico (daPa), altura (mL), ancho,
     * línea base]. Espejo de SHAPES en public/js/case/tympanogram.js.
     */
    public const FORMAS_TIMPANOGRAMA = [
        'A'  => [0.0, 0.8, 60.0, 0.1],
        'As' => [0.0, 0.3, 50.0, 0.1],
        'Ad' => [0.0, 1.8, 70.0, 0.1],
        'C'  => [-150.0, 0.8, 70.0, 0.1],
        'Cs' => [-150.0, 0.3, 60.0, 0.1],
        'B'  => [0.0, 0.15, 400.0, 0.15],
    ];

    // -----------------------------------------------------------------
    // Audiograma
    // -----------------------------------------------------------------

    /**
     * Audiograma tonal completo: grilla, vía aérea con línea y símbolo, vía
     * ósea sin línea (convención estándar) y LDL punteado.
     *
     * Símbolos ASHA, igual que en el editor: círculo/cruz = aérea OD/OI sin
     * enmascarar, triángulo/cuadrado = aérea enmascarada, "<"/">" = ósea sin
     * enmascarar, "["/"]" = ósea enmascarada, triángulo relleno = LDL.
     *
     * @param array{od:array<int,float>,oi:array<int,float>} $aerea 9 umbrales por oído
     * @param array{od:array<int,float>,oi:array<int,float>} $osea
     * @param array{od:array<int,float>,oi:array<int,float>} $ldl
     * @param array{od:bool,oi:bool} $ldlMedido qué oídos tienen LDL medido
     */
    public static function audiogram(
        MiniPdf $pdf,
        float $x,
        float $y,
        float $w,
        float $h,
        array $aerea,
        array $osea,
        array $ldl,
        array $ldlMedido
    ): void {
        [$px, $py, $pw, $ph] = self::plotBox($x, $y, $w, $h);
        $freqs = CaseBuilder::FREQUENCIES;
        $minLog = log(125, 2);
        $maxLog = log(8000, 2);

        $fx = static fn (float $hz): float => $px + (log($hz, 2) - $minLog) / ($maxLog - $minLog) * $pw;
        $fy = static fn (float $db): float => $py + (max(-10.0, min(120.0, $db)) + 10) / 130 * $ph;

        // Grilla: una vertical por frecuencia del audiómetro y una
        // horizontal cada 10 dB, con la de 0 dB marcada (el "techo" de lo
        // normal es lo primero que se busca al leer un audiograma).
        foreach ($freqs as $hz) {
            $lineX = $fx((float) $hz);
            $pdf->line($lineX, $py, $lineX, $py + $ph, 0.4, self::COLOR_GRID);
            $pdf->textCenter($lineX, $py - 3, self::freqLabel($hz), 5.5, false, self::COLOR_ROTULO);
        }
        for ($db = -10; $db <= 120; $db += 10) {
            $lineY = $fy((float) $db);
            $fuerte = $db === 0;
            $pdf->line($px, $lineY, $px + $pw, $lineY, $fuerte ? 0.7 : 0.4, $fuerte ? self::COLOR_GRID_FUERTE : self::COLOR_GRID);
            if ($db % 20 === 0) {
                $pdf->textRight($px - 3, $lineY + 2, (string) $db, 5.5, false, self::COLOR_ROTULO);
            }
        }
        $pdf->rect($px, $py, $pw, $ph, 0.7, self::COLOR_GRID_FUERTE);
        $pdf->text($x, $y + $h - 1, 'dB HL / Hz', 5.5, false, self::COLOR_ROTULO);

        // Vía aérea: línea continua + símbolo por punto.
        foreach (['od' => self::COLOR_OD, 'oi' => self::COLOR_OI] as $lado => $color) {
            $pts = [];
            foreach ($freqs as $i => $hz) {
                $pts[] = [$fx((float) $hz), $fy((float) ($aerea[$lado][$i] ?? 0))];
            }
            $pdf->polyline($pts, 1.1, $color);
        }
        foreach ($freqs as $i => $hz) {
            $cx = $fx((float) $hz);
            $aOd = (float) ($aerea['od'][$i] ?? 0);
            $aOi = (float) ($aerea['oi'][$i] ?? 0);
            $oOd = (float) ($osea['od'][$i] ?? 0);
            $oOi = (float) ($osea['oi'][$i] ?? 0);

            $enmascaradaOd = ($aOd - $oOi) >= self::ATENUACION_AEREA_POR_FREQ[$i];
            $enmascaradaOi = ($aOi - $oOd) >= self::ATENUACION_AEREA_POR_FREQ[$i];
            if ($enmascaradaOd) {
                self::triangulo($pdf, $cx, $fy($aOd), self::COLOR_OD, false);
            } else {
                $pdf->circle($cx, $fy($aOd), 3.4, self::COLOR_OD, null, 1.1);
            }
            if ($enmascaradaOi) {
                $pdf->rect($cx - 3, $fy($aOi) - 3, 6, 6, 1.1, self::COLOR_OI);
            } else {
                self::cruz($pdf, $cx, $fy($aOi), self::COLOR_OI);
            }

            // Ósea: sin línea, y enmascarada si hay gap >= 10 dB en el
            // mismo oído (la atenuación interaural ósea es ~0).
            self::corchete($pdf, $cx, $fy($oOd), self::COLOR_OD, 'izq', ($aOd - $oOd) >= self::GAP_ENMASCARA_OSEA);
            self::corchete($pdf, $cx, $fy($oOi), self::COLOR_OI, 'der', ($aOi - $oOi) >= self::GAP_ENMASCARA_OSEA);
        }

        // LDL: solo el oído que lo tiene medido. Si no se midió, el caso
        // guarda 130 en las nueve frecuencias y dibujarlo sería mostrar un
        // dato que nadie tomó.
        foreach (['od' => self::COLOR_OD, 'oi' => self::COLOR_OI] as $lado => $color) {
            if (empty($ldlMedido[$lado])) {
                continue;
            }
            $pts = [];
            foreach ($freqs as $i => $hz) {
                $pts[] = [$fx((float) $hz), $fy((float) ($ldl[$lado][$i] ?? 130))];
            }
            $pdf->polyline($pts, 0.8, $color, [1.6, 1.6]);
            foreach ($pts as $pt) {
                $pdf->polygon(
                    [[$pt[0] - 3, $pt[1] - 1.8], [$pt[0] + 3, $pt[1] - 1.8], [$pt[0], $pt[1] + 2.2]],
                    null,
                    $color
                );
            }
        }
    }

    /**
     * Un símbolo del audiograma, suelto. Existe para que la leyenda dibuje
     * los MISMOS trazos que el gráfico: una leyenda hecha con letras ("O",
     * "X") deja de describir el dibujo apenas cambia un símbolo.
     */
    public static function symbol(MiniPdf $pdf, string $clave, float $x, float $y, string $color): void
    {
        switch ($clave) {
            case 'aerea_od':    $pdf->circle($x, $y, 3.4, $color, null, 1.1); break;
            case 'aerea_oi':    self::cruz($pdf, $x, $y, $color); break;
            case 'aerea_od_m':  self::triangulo($pdf, $x, $y, $color, false); break;
            case 'aerea_oi_m':  $pdf->rect($x - 3, $y - 3, 6, 6, 1.1, $color); break;
            case 'osea_od':     self::corchete($pdf, $x, $y, $color, 'izq', false); break;
            case 'osea_oi':     self::corchete($pdf, $x, $y, $color, 'der', false); break;
            case 'osea_od_m':   self::corchete($pdf, $x, $y, $color, 'izq', true); break;
            case 'osea_oi_m':   self::corchete($pdf, $x, $y, $color, 'der', true); break;
            case 'ldl':         $pdf->polygon([[$x - 3, $y - 1.8], [$x + 3, $y - 1.8], [$x, $y + 2.2]], null, $color); break;
        }
    }

    /**
     * Leyenda de símbolos del audiograma, una fila por símbolo. Devuelve la
     * Y del final.
     */
    public static function symbolLegend(MiniPdf $pdf, float $x, float $y, float $ancho): float
    {
        $pdf->text($x, $y, 'Símbolos (ASHA)', 8, true, '#222222');
        $y += 11;
        foreach ([
            ['aerea_od', 'Aérea OD', self::COLOR_OD],
            ['aerea_oi', 'Aérea OI', self::COLOR_OI],
            ['aerea_od_m', 'Aérea OD enmascarada', self::COLOR_OD],
            ['aerea_oi_m', 'Aérea OI enmascarada', self::COLOR_OI],
            ['osea_od', 'Ósea OD', self::COLOR_OD],
            ['osea_oi', 'Ósea OI', self::COLOR_OI],
            ['osea_od_m', 'Ósea OD enmascarada', self::COLOR_OD],
            ['osea_oi_m', 'Ósea OI enmascarada', self::COLOR_OI],
            ['ldl', 'LDL (línea punteada)', self::COLOR_ROTULO],
        ] as [$clave, $texto, $color]) {
            self::symbol($pdf, $clave, $x + 4, $y - 2, $color);
            $pdf->text($x + 14, $y, $texto, 7, false, '#333333');
            $y += 10.5;
        }
        return $y;
    }

    // -----------------------------------------------------------------
    // Timpanograma
    // -----------------------------------------------------------------

    /**
     * Curva timpanométrica del tipo Jerger elegido. Espejo de
     * tympanogram.js: la ficha guarda la CATEGORÍA (A/As/Ad/C/Cs/B), no una
     * curva medida, así que se sintetiza una campana gaussiana por tipo --
     * lo que se lee es la forma, no los mililitros exactos.
     */
    public static function tympanogram(MiniPdf $pdf, float $x, float $y, float $w, float $h, string $tipo, string $color): void
    {
        [$px, $py, $pw, $ph] = self::plotBox($x, $y, $w, $h);
        $fx = static fn (float $daPa): float => $px + (max(-400.0, min(200.0, $daPa)) + 400) / 600 * $pw;
        $fy = static fn (float $ml): float => $py + $ph - max(0.0, min(2.5, $ml)) / 2.5 * $ph;

        foreach ([-400, -300, -200, -100, 0, 100, 200] as $daPa) {
            $lineX = $fx((float) $daPa);
            $pdf->line($lineX, $py, $lineX, $py + $ph, 0.4, $daPa === 0 ? self::COLOR_GRID_FUERTE : self::COLOR_GRID);
            $pdf->textCenter($lineX, $py + $ph + self::EJE_INF - 3, (string) $daPa, 5.0, false, self::COLOR_ROTULO);
        }
        for ($ml = 0.0; $ml <= 2.5; $ml += 0.5) {
            $lineY = $fy($ml);
            $pdf->line($px, $lineY, $px + $pw, $lineY, 0.4, self::COLOR_GRID);
            $pdf->textRight($px - 3, $lineY + 2, number_format($ml, 1), 5.0, false, self::COLOR_ROTULO);
        }
        $pdf->rect($px, $py, $pw, $ph, 0.7, self::COLOR_GRID_FUERTE);
        $pdf->text($x, $y + 6, 'mL / daPa', 5.0, false, self::COLOR_ROTULO);

        $pts = [];
        foreach (self::tympanogramPoints($tipo) as [$daPa, $ml]) {
            $pts[] = [$fx($daPa), $fy($ml)];
        }
        $pdf->polyline($pts, 1.2, $color);
    }

    /**
     * Puntos de la campana por tipo (ver FORMAS_TIMPANOGRAMA).
     *
     * @return array<int,array{0:float,1:float}> pares [presión, compliance]
     */
    public static function tympanogramPoints(string $tipo): array
    {
        $formas = self::FORMAS_TIMPANOGRAMA;
        [$pico, $altura, $ancho, $base] = $formas[$tipo] ?? $formas['A'];

        $pts = [];
        for ($p = -400.0; $p <= 200.0; $p += 10.0) {
            $pts[] = [$p, $base + ($altura - $base) * exp(-(($p - $pico) ** 2) / (2 * $ancho * $ancho))];
        }
        return $pts;
    }

    // -----------------------------------------------------------------
    // Logoaudiograma
    // -----------------------------------------------------------------

    /**
     * Curva de discriminación (% vs dB HL) por oído. Espejo de logogram.js:
     * 0 % en el SDT, sube hasta la UMD y de ahí meseta, o cae si hay
     * reclutamiento (rollover). El SRT va como vertical punteada porque es
     * un umbral, no un punto de la curva.
     *
     * @param array<string,array{sdt:float,srt:float,umd_int:float,umd_pct:float,recruit:bool}> $porLado
     */
    public static function logogram(MiniPdf $pdf, float $x, float $y, float $w, float $h, array $porLado): void
    {
        [$px, $py, $pw, $ph] = self::plotBox($x, $y, $w, $h);
        $fx = static fn (float $db): float => $px + (max(-10.0, min(120.0, $db)) + 10) / 130 * $pw;
        $fy = static fn (float $pct): float => $py + (100 - max(0.0, min(100.0, $pct))) / 100 * $ph;

        for ($db = 0; $db <= 120; $db += 20) {
            $lineX = $fx((float) $db);
            $pdf->line($lineX, $py, $lineX, $py + $ph, 0.4, self::COLOR_GRID);
            $pdf->textCenter($lineX, $py + $ph + self::EJE_INF - 3, (string) $db, 5.0, false, self::COLOR_ROTULO);
        }
        for ($pct = 0; $pct <= 100; $pct += 20) {
            $lineY = $fy((float) $pct);
            $pdf->line($px, $lineY, $px + $pw, $lineY, 0.4, self::COLOR_GRID);
            $pdf->textRight($px - 3, $lineY + 2, (string) $pct, 5.0, false, self::COLOR_ROTULO);
        }
        $pdf->rect($px, $py, $pw, $ph, 0.7, self::COLOR_GRID_FUERTE);
        $pdf->text($x, $y + 6, '% / dB HL', 5.0, false, self::COLOR_ROTULO);

        foreach (['od' => self::COLOR_OD, 'oi' => self::COLOR_OI] as $lado => $color) {
            $cfg = $porLado[$lado] ?? null;
            if (!is_array($cfg)) {
                continue;
            }
            $pts = [];
            foreach (self::logogramPoints($cfg) as [$db, $pct]) {
                $pts[] = [$fx($db), $fy($pct)];
            }
            $pdf->polyline($pts, 1.2, $color);

            $srtX = $fx((float) $cfg['srt']);
            $pdf->line($srtX, $py, $srtX, $py + $ph, 0.7, $color, [1.6, 1.6]);
            $pdf->circle($fx((float) $cfg['sdt']), $fy(0.0), 2.0, null, $color);
            $umdX = $fx((float) $cfg['umd_int']);
            $umdY = $fy((float) $cfg['umd_pct']);
            $pdf->polygon([[$umdX, $umdY - 3.2], [$umdX - 3.2, $umdY + 2.6], [$umdX + 3.2, $umdY + 2.6]], null, $color);
        }
    }

    /**
     * Puntos de la curva de discriminación. Misma forma que curvePoints() en
     * logogram.js, incluido el rollover: con reclutamiento la curva CAE
     * pasada la UMD en vez de quedarse en meseta.
     *
     * @param array{sdt:float,srt:float,umd_int:float,umd_pct:float,recruit:bool} $cfg
     * @return array<int,array{0:float,1:float}>
     */
    public static function logogramPoints(array $cfg): array
    {
        $sdt = (float) $cfg['sdt'];
        $umdInt = (float) $cfg['umd_int'];
        $umdPct = (float) $cfg['umd_pct'];

        $pts = [[-10.0, 0.0], [$sdt, 0.0], [$umdInt, $umdPct]];
        $pts[] = !empty($cfg['recruit'])
            ? [120.0, max(0.0, $umdPct - (120 - $umdInt) / 5 * 5)]
            : [120.0, $umdPct];
        usort($pts, static fn ($a, $b) => $a[0] <=> $b[0]);
        return $pts;
    }

    // -----------------------------------------------------------------
    // Barras y curva de desviación
    // -----------------------------------------------------------------

    /**
     * Barras horizontales con rótulo a la izquierda y valor a la derecha:
     * el umbral del ABR por estímulo y el del VEMP por subtipo. El eje va
     * de 0 al máximo que se le pase, así dos bloques distintos (nHL del ABR
     * y dB del VEMP) no se comparan entre sí por accidente.
     *
     * @param array<string,float|null> $valores rótulo => valor (null = sin respuesta)
     */
    public static function bars(MiniPdf $pdf, float $x, float $y, float $w, array $valores, float $max, string $color, string $unidad = 'dB'): float
    {
        if ($valores === []) {
            return $y;
        }
        $alto = 7.0;
        $paso = 9.5;
        $anchoRotulo = 62.0;
        $anchoValor = 34.0;
        $anchoBarra = max(20.0, $w - $anchoRotulo - $anchoValor);

        foreach ($valores as $rotulo => $valor) {
            $pdf->text($x, $y + $alto - 1.5, (string) $rotulo, 6.5, false, self::COLOR_ROTULO);
            $pdf->rect($x + $anchoRotulo, $y, $anchoBarra, $alto, 0.4, self::COLOR_GRID);
            if ($valor === null) {
                $pdf->text($x + $anchoRotulo + 3, $y + $alto - 1.5, 'sin respuesta', 6.0, false, self::COLOR_ROTULO);
            } else {
                $largo = $max > 0 ? max(0.6, min(1.0, (float) $valor / $max) * $anchoBarra) : 0.6;
                $pdf->rectFilled($x + $anchoRotulo, $y, $largo, $alto, $color);
                $pdf->textRight($x + $w, $y + $alto - 1.5, self::num((float) $valor) . ' ' . $unidad, 6.5, false, self::COLOR_ROTULO);
            }
            $y += $paso;
        }
        return $y;
    }

    /**
     * Curva de desviación de la OEA por banda (dB POR DEBAJO de lo esperado,
     * mismo criterio "más número, peor oído" que el tab EOA): eje invertido,
     * así una emisión caída se dibuja hacia abajo como en el audiograma.
     *
     * @param array<string,array<int|string,float>> $porLado lado => [Hz => dB]
     */
    public static function oaeDeviation(MiniPdf $pdf, float $x, float $y, float $w, float $h, array $porLado, float $max = 45.0): void
    {
        [$px, $py, $pw, $ph] = self::plotBox($x, $y, $w, $h);
        $bandas = CaseBuilder::EOAS_FREQS;
        $minLog = log((float) $bandas[0], 2);
        $maxLog = log((float) $bandas[count($bandas) - 1], 2);

        $fx = static fn (float $hz): float => $px + (log($hz, 2) - $minLog) / max(0.001, $maxLog - $minLog) * $pw;
        $fy = static fn (float $db): float => $py + max(0.0, min($max, $db)) / $max * $ph;

        foreach ($bandas as $hz) {
            $lineX = $fx((float) $hz);
            $pdf->line($lineX, $py, $lineX, $py + $ph, 0.4, self::COLOR_GRID);
            $pdf->textCenter($lineX, $py - 3, self::freqLabel((int) $hz), 5.0, false, self::COLOR_ROTULO);
        }
        for ($db = 0; $db <= (int) $max; $db += 15) {
            $lineY = $fy((float) $db);
            $pdf->line($px, $lineY, $px + $pw, $lineY, 0.4, $db === 0 ? self::COLOR_GRID_FUERTE : self::COLOR_GRID);
            $pdf->textRight($px - 3, $lineY + 2, (string) $db, 5.0, false, self::COLOR_ROTULO);
        }
        $pdf->rect($px, $py, $pw, $ph, 0.7, self::COLOR_GRID_FUERTE);
        $pdf->text($x, $y + $h - 1.5, 'dB de caída / Hz', 5.0, false, self::COLOR_ROTULO);

        foreach (['od' => self::COLOR_OD, 'oi' => self::COLOR_OI] as $lado => $color) {
            $desv = $porLado[$lado] ?? null;
            if (!is_array($desv)) {
                continue;
            }
            $pts = [];
            foreach ($bandas as $hz) {
                $pts[] = [$fx((float) $hz), $fy((float) ($desv[(string) $hz] ?? $desv[$hz] ?? 0))];
            }
            $pdf->polyline($pts, 1.2, $color);
            foreach ($pts as $pt) {
                $pdf->circle($pt[0], $pt[1], 1.6, null, $color);
            }
        }
    }

    /** Leyenda OD/OI en una línea, para poner debajo de un gráfico. */
    public static function legend(MiniPdf $pdf, float $x, float $y, string $extra = ''): void
    {
        $pdf->rectFilled($x, $y - 4, 7, 2, self::COLOR_OD);
        $pdf->text($x + 10, $y, 'OD', 6.5, true, self::COLOR_OD);
        $pdf->rectFilled($x + 26, $y - 4, 7, 2, self::COLOR_OI);
        $pdf->text($x + 36, $y, 'OI', 6.5, true, self::COLOR_OI);
        if ($extra !== '') {
            $pdf->text($x + 54, $y, $extra, 6.0, false, self::COLOR_ROTULO);
        }
    }

    // -----------------------------------------------------------------
    // Interno
    // -----------------------------------------------------------------

    /** Área de dibujo dentro del recuadro, descontando los rótulos de los ejes. */
    private static function plotBox(float $x, float $y, float $w, float $h): array
    {
        return [
            $x + self::EJE_IZQ,
            $y + self::EJE_SUP,
            max(10.0, $w - self::EJE_IZQ - 2),
            max(10.0, $h - self::EJE_SUP - self::EJE_INF),
        ];
    }

    private static function freqLabel(int $hz): string
    {
        return $hz >= 1000 ? rtrim(rtrim(number_format($hz / 1000, 1, '.', ''), '0'), '.') . 'k' : (string) $hz;
    }

    /** Número corto: sin decimales si es entero, con uno si no. */
    private static function num(float $v): string
    {
        return abs($v - round($v)) < 0.05 ? (string) (int) round($v) : number_format($v, 1);
    }

    private static function cruz(MiniPdf $pdf, float $x, float $y, string $color): void
    {
        $r = 3.4;
        $pdf->line($x - $r, $y - $r, $x + $r, $y + $r, 1.1, $color);
        $pdf->line($x - $r, $y + $r, $x + $r, $y - $r, 1.1, $color);
    }

    private static function triangulo(MiniPdf $pdf, float $x, float $y, string $color, bool $relleno): void
    {
        $r = 3.8;
        $pts = [[$x, $y - $r], [$x - $r, $y + $r * 0.8], [$x + $r, $y + $r * 0.8]];
        $pdf->polygon($pts, $relleno ? null : $color, $relleno ? $color : null, 1.1);
    }

    /** "<"/">" sin enmascarar, "["/"]" enmascarado: mismo trazo, distinto cierre. */
    private static function corchete(MiniPdf $pdf, float $x, float $y, string $color, string $dir, bool $enmascarada): void
    {
        $r = 3.4;
        if (!$enmascarada) {
            $pts = $dir === 'izq'
                ? [[$x + $r, $y - $r], [$x - $r, $y], [$x + $r, $y + $r]]
                : [[$x - $r, $y - $r], [$x + $r, $y], [$x - $r, $y + $r]];
        } else {
            $pts = $dir === 'izq'
                ? [[$x + $r * 0.6, $y - $r], [$x - $r, $y - $r], [$x - $r, $y + $r], [$x + $r * 0.6, $y + $r]]
                : [[$x - $r * 0.6, $y - $r], [$x + $r, $y - $r], [$x + $r, $y + $r], [$x - $r * 0.6, $y + $r]];
        }
        $pdf->polyline($pts, 1.1, $color);
    }
}
