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
    /** Línea del límite de normalidad: más oscura que la grilla, para que se vea sola. */
    private const COLOR_LIMITE_NORMAL = '#555555';
    private const COLOR_ROTULO = '#444444';

    /**
     * Aire a cada lado del eje X, como fracción del ancho útil: el primer y
     * el último punto no se pegan al marco. Un símbolo de 125 Hz montado
     * sobre la línea del recuadro se lee peor y queda feo.
     */
    private const AIRE_EJE = 0.05;

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
     * Trazos del audiograma, en pt [marca, espacio]. La aérea va con línea
     * llena; la ósea se une con PUNTOS y el LDL con guiones más largos, para
     * que las dos líneas discontinuas no se confundan entre sí. Mismos
     * patrones que en public/js/case/audiogram.js.
     */
    public const TRAZO_OSEA = [1.0, 2.0];
    public const TRAZO_LDL = [3.0, 2.0];

    /**
     * Frecuencias en las que SÍ se mide vía ósea y LDL: 250 a 4000 Hz.
     *
     * Ni 125 ni 6000/8000 se prueban por vía ósea --el vibrador no entrega
     * nivel útil ahí y la vibración táctil se confunde con audición-- y el
     * LDL se busca en el mismo rango. Dibujar esos puntos mostraba umbrales
     * que nadie tomó.
     */
    public const FREQS_OSEA = [250, 500, 1000, 2000, 3000, 4000];

    /**
     * Valor con el que el caso marca que NO hay umbral en esa frecuencia:
     * no se midió, o no hubo respuesta. No es un umbral de 130 dB.
     *
     * Importa porque el eje llega a 120: sin este corte, un 130 se dibujaba
     * recortado contra el borde y se leía como un umbral profundo, y la
     * línea lo unía con sus vecinos como si fuera parte de la curva.
     */
    public const SIN_UMBRAL_DB = 130;

    /**
     * Límite de la audición normal (dB HL). En Chile llega hasta 20 dB HL
     * inclusive, así que el grado leve arranca en 21 -- es el mismo número
     * que `CaseProfile::GRADES['leve']` (y un test comprueba que sigan de
     * acuerdo). Se dibuja más gruesa que el resto de la grilla porque es la
     * línea que se busca primero al leer un audiograma: lo que queda encima
     * es audición normal, lo que queda debajo es hipoacusia.
     */
    public const LIMITE_NORMALIDAD_DB = 20;

    /**
     * Campana por tipo Jerger: [presión del pico (daPa), altura (mL), ancho,
     * línea base]. Espejo de SHAPES en public/js/case/tympanogram.js.
     */
    /**
     * Tope del eje Y del timpanograma (mL). Fijo: los dos oídos y todos los
     * casos se leen en la misma escala, que es lo que permite comparar una
     * ficha con otra de un vistazo.
     */
    public const ESCALA_TIMPANOGRAMA_ML = 2.0;

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
     * Audiograma tonal completo: grilla, vía aérea con línea llena y
     * símbolo, vía ósea unida con línea punteada y LDL con guiones.
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

        $aire = $pw * self::AIRE_EJE;
        $util = $pw - 2 * $aire;
        $fx = static fn (float $hz): float => $px + $aire + (log($hz, 2) - $minLog) / ($maxLog - $minLog) * $util;
        $fy = static fn (float $db): float => $py + (max(-10.0, min(120.0, $db)) + 10) / 130 * $ph;

        // Grilla: una vertical por frecuencia del audiómetro y una
        // horizontal cada 10 dB, con la del límite de normalidad marcada
        // gruesa (ver LIMITE_NORMALIDAD_DB).
        foreach ($freqs as $hz) {
            $lineX = $fx((float) $hz);
            $pdf->line($lineX, $py, $lineX, $py + $ph, 0.4, self::COLOR_GRID);
            $pdf->textCenter($lineX, $py - 3, self::freqLabel($hz), 5.5, false, self::COLOR_ROTULO);
        }
        for ($db = -10; $db <= 120; $db += 10) {
            $lineY = $fy((float) $db);
            // Las dos líneas que se buscan al leer un audiograma: el 0 dB HL
            // y el límite de la audición normal.
            $marcada = $db === 0 || $db === self::LIMITE_NORMALIDAD_DB;
            $pdf->line(
                $px,
                $lineY,
                $px + $pw,
                $lineY,
                $marcada ? 1.4 : 0.4,
                $marcada ? self::COLOR_LIMITE_NORMAL : self::COLOR_GRID
            );
            if ($db % 20 === 0) {
                $pdf->textRight($px - 3, $lineY + 2, (string) $db, 5.5, false, $marcada ? self::COLOR_LIMITE_NORMAL : self::COLOR_ROTULO);
            }
        }
        $pdf->rect($px, $py, $pw, $ph, 0.7, self::COLOR_GRID_FUERTE);
        $pdf->text($x, $y + $h - 1, 'dB HL / Hz', 5.5, false, self::COLOR_ROTULO);

        // Vía aérea: línea continua + símbolo por punto. La línea se parte
        // en las frecuencias sin umbral en vez de saltarlas de largo.
        foreach (['od' => self::COLOR_OD, 'oi' => self::COLOR_OI] as $lado => $color) {
            foreach (self::tramosConUmbral($aerea[$lado] ?? [], $freqs, $fx, $fy) as $tramo) {
                $pdf->polyline($tramo, 1.1, $color);
            }
        }
        // Vía ósea: unida con línea punteada, por oído, y SOLO en las
        // frecuencias donde se mide (ver FREQS_OSEA). Se dibuja antes que
        // los símbolos para que el corchete quede encima de la línea.
        $freqsOsea = array_filter($freqs, static fn ($hz): bool => in_array($hz, self::FREQS_OSEA, true));
        foreach (['od' => self::COLOR_OD, 'oi' => self::COLOR_OI] as $lado => $color) {
            foreach (self::tramosConUmbral($osea[$lado] ?? [], $freqsOsea, $fx, $fy) as $tramo) {
                $pdf->polyline($tramo, 0.9, $color, self::TRAZO_OSEA);
            }
        }

        foreach ($freqs as $i => $hz) {
            $cx = $fx((float) $hz);
            $aOd = (float) ($aerea['od'][$i] ?? 0);
            $aOi = (float) ($aerea['oi'][$i] ?? 0);
            $oOd = (float) ($osea['od'][$i] ?? 0);
            $oOi = (float) ($osea['oi'][$i] ?? 0);

            $enmascaradaOd = ($aOd - $oOi) >= self::ATENUACION_AEREA_POR_FREQ[$i];
            $enmascaradaOi = ($aOi - $oOd) >= self::ATENUACION_AEREA_POR_FREQ[$i];
            if ($aOd < self::SIN_UMBRAL_DB) {
                if ($enmascaradaOd) {
                    self::triangulo($pdf, $cx, $fy($aOd), self::COLOR_OD, false);
                } else {
                    $pdf->circle($cx, $fy($aOd), 3.4, self::COLOR_OD, null, 1.1);
                }
            }
            if ($aOi < self::SIN_UMBRAL_DB) {
                if ($enmascaradaOi) {
                    $pdf->rect($cx - 3, $fy($aOi) - 3, 6, 6, 1.1, self::COLOR_OI);
                } else {
                    self::cruz($pdf, $cx, $fy($aOi), self::COLOR_OI);
                }
            }

            // Ósea enmascarada si hay gap >= 10 dB en el mismo oído (la
            // atenuación interaural ósea es ~0). Solo donde se mide.
            if (in_array($hz, self::FREQS_OSEA, true)) {
                if ($oOd < self::SIN_UMBRAL_DB) {
                    self::corchete($pdf, $cx, $fy($oOd), self::COLOR_OD, 'izq', ($aOd - $oOd) >= self::GAP_ENMASCARA_OSEA);
                }
                if ($oOi < self::SIN_UMBRAL_DB) {
                    self::corchete($pdf, $cx, $fy($oOi), self::COLOR_OI, 'der', ($aOi - $oOi) >= self::GAP_ENMASCARA_OSEA);
                }
            }
        }

        // LDL: solo el oído que lo tiene medido. Si no se midió, el caso
        // guarda 130 en las nueve frecuencias y dibujarlo sería mostrar un
        // dato que nadie tomó.
        foreach (['od' => self::COLOR_OD, 'oi' => self::COLOR_OI] as $lado => $color) {
            if (empty($ldlMedido[$lado])) {
                continue;
            }
            // El 130 acá es "no se buscó el LDL en esta frecuencia": ni
            // símbolo ni tramo de línea.
            foreach (self::tramosConUmbral($ldl[$lado] ?? [], $freqsOsea, $fx, $fy) as $tramo) {
                $pdf->polyline($tramo, 0.8, $color, self::TRAZO_LDL);
                foreach ($tramo as $pt) {
                    self::symbol($pdf, $lado === 'od' ? 'ldl_od' : 'ldl_oi', $pt[0], $pt[1], $color);
                }
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
            case 'ldl_od':      self::ldl($pdf, $x, $y, $color, -1); break;
            case 'ldl_oi':      self::ldl($pdf, $x, $y, $color, 1); break;
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
            ['ldl_od', 'LDL OD (línea de guiones)', self::COLOR_OD],
            ['ldl_oi', 'LDL OI', self::COLOR_OI],
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
        $tope = self::ESCALA_TIMPANOGRAMA_ML;
        $aire = $pw * self::AIRE_EJE;
        $util = $pw - 2 * $aire;
        $fx = static fn (float $daPa): float => $px + $aire + (max(-400.0, min(200.0, $daPa)) + 400) / 600 * $util;
        $fy = static fn (float $ml) => $py + $ph - max(0.0, min($tope, $ml)) / $tope * $ph;

        foreach ([-400, -300, -200, -100, 0, 100, 200] as $daPa) {
            $lineX = $fx((float) $daPa);
            $pdf->line($lineX, $py, $lineX, $py + $ph, 0.4, $daPa === 0 ? self::COLOR_GRID_FUERTE : self::COLOR_GRID);
            $pdf->textCenter($lineX, $py + $ph + self::EJE_INF - 3, (string) $daPa, 5.0, false, self::COLOR_ROTULO);
        }
        // Cuatro divisiones de 0.5 mL sobre la escala fija.
        for ($n = 0; $n <= 4; $n++) {
            $ml = $tope * $n / 4;
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
     * Los números que se leen de la curva sintetizada: presión del pico,
     * compliance y ancho.
     *
     * La ficha guarda solo la categoría Jerger, así que estos valores salen
     * de la misma forma que se dibuja -- no son un dato aparte que alguien
     * pueda editar por su cuenta, y por eso siempre coinciden con el
     * gráfico de al lado.
     *
     * `estatica` es la compliance compensada (pico menos línea base), que es
     * la que se informa; `ancho` es el ancho a media altura (TW), que en una
     * caída exponencial vale 2 * w * ln 2.
     *
     * @return array{pico_dapa:float,maxima:float,estatica:float,ancho_dapa:float,plana:bool}
     */
    public static function valoresTimpanograma(string $tipo): array
    {
        $forma = self::FORMAS_TIMPANOGRAMA[$tipo] ?? self::FORMAS_TIMPANOGRAMA['A'];
        [$pico, $altura, $ancho, $base] = $forma;
        $estatica = $altura - $base;

        return [
            'pico_dapa' => $pico,
            'maxima' => $altura,
            'estatica' => $estatica,
            'ancho_dapa' => 2 * $ancho * log(2),
            // Sin pico no hay presión que informar: el tipo B es plano por
            // definición y su "pico" sería el primer punto del barrido.
            'plana' => $estatica < 0.1,
        ];
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

        // Exponencial de |distancia| y no una gaussiana: el timpanograma
        // real tiene el ápice EN PUNTA, no redondeado -- la campana de Gauss
        // dibujaba una loma que ningún equipo imprime. El paso también baja
        // a 5 daPa, porque con 10 la punta se recortaba en el muestreo.
        $pts = [];
        for ($p = -400.0; $p <= 200.0; $p += 5.0) {
            $pts[] = [$p, $base + ($altura - $base) * exp(-abs($p - $pico) / $ancho)];
        }
        return $pts;
    }

    // -----------------------------------------------------------------
    // Logoaudiograma
    // -----------------------------------------------------------------

    /**
     * Curva de discriminación (% vs dB HL) por oído, redondeada. Espejo de
     * logogram.js: 0 % en el SDT, sube hasta la UMD y de ahí meseta, o cae
     * si hay reclutamiento (rollover). El SRT va como vertical punteada
     * porque es un umbral, no un punto de la curva.
     *
     * @param array<string,array{sdt:float,srt:float,umd_int:float,umd_pct:float,recruit:bool}> $porLado
     */
    public static function logogram(MiniPdf $pdf, float $x, float $y, float $w, float $h, array $porLado): void
    {
        [$px, $py, $pw, $ph] = self::plotBox($x, $y, $w, $h);
        $aire = $pw * self::AIRE_EJE;
        $util = $pw - 2 * $aire;
        $fx = static fn (float $db): float => $px + $aire + (max(-10.0, min(120.0, $db)) + 10) / 130 * $util;
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
            // Redondeada, como en un informe: la quebrada de segmentos rectos
            // es un artefacto de dibujar punto a punto, no la curva que
            // describe cómo crece la discriminación.
            $pdf->bezier(self::curvaSuave($pts), 1.2, $color);

            $srtX = $fx((float) $cfg['srt']);
            $pdf->line($srtX, $py, $srtX, $py + $ph, 0.7, $color, [1.6, 1.6]);
            $pdf->circle($fx((float) $cfg['sdt']), $fy(0.0), 2.0, null, $color);
            $umdX = $fx((float) $cfg['umd_int']);
            $umdY = $fy((float) $cfg['umd_pct']);
            $pdf->polygon([[$umdX, $umdY - 3.2], [$umdX - 3.2, $umdY + 2.6], [$umdX + 3.2, $umdY + 2.6]], null, $color);
        }
    }

    /**
     * Convierte una serie de puntos en segmentos bezier que pasan por todos
     * ellos, con las tangentes de Fritsch-Carlson (interpolación cúbica
     * MONÓTONA).
     *
     * Monótona y no un spline cualquiera: una curva de discriminación no
     * puede pasar de 100 % ni bajar de 0, y un Catmull-Rom clásico se
     * sobrepasa en cuanto hay un tramo empinado seguido de una meseta --
     * dibujaría un 104 % que no existe. Fritsch-Carlson anula la tangente en
     * los máximos y mínimos, que además es justo la forma redondeada con que
     * se dibuja el rollover en un informe de verdad.
     *
     * @param array<int,array{0:float,1:float}> $pts en X creciente
     * @return array<int,array<int,float>> segmentos [x0,y0,c1x,c1y,c2x,c2y,x1,y1]
     */
    public static function curvaSuave(array $pts): array
    {
        // Puntos con la misma X no aportan tramo y romperían la pendiente.
        $limpios = [];
        foreach ($pts as $pt) {
            if ($limpios === [] || abs($pt[0] - $limpios[count($limpios) - 1][0]) > 1e-9) {
                $limpios[] = [(float) $pt[0], (float) $pt[1]];
            }
        }
        $n = count($limpios);
        if ($n < 2) {
            return [];
        }

        // Pendiente de cada tramo.
        $d = [];
        for ($i = 0; $i < $n - 1; $i++) {
            $d[$i] = ($limpios[$i + 1][1] - $limpios[$i][1]) / ($limpios[$i + 1][0] - $limpios[$i][0]);
        }

        // Tangente en cada punto: la media de los dos tramos que llegan.
        $m = [$d[0]];
        for ($i = 1; $i < $n - 1; $i++) {
            $m[$i] = ($d[$i - 1] + $d[$i]) / 2;
        }
        $m[$n - 1] = $d[$n - 2];

        // Y acá se fuerza la monotonía tramo a tramo (Fritsch-Carlson).
        for ($i = 0; $i < $n - 1; $i++) {
            if (abs($d[$i]) < 1e-12) {
                $m[$i] = 0.0;
                $m[$i + 1] = 0.0;
                continue;
            }
            $a = $m[$i] / $d[$i];
            $b = $m[$i + 1] / $d[$i];
            if ($a < 0) {
                $m[$i] = 0.0;
                $a = 0.0;
            }
            if ($b < 0) {
                $m[$i + 1] = 0.0;
                $b = 0.0;
            }
            $suma = $a * $a + $b * $b;
            if ($suma > 9.0) {
                $t = 3.0 / sqrt($suma);
                $m[$i] = $t * $a * $d[$i];
                $m[$i + 1] = $t * $b * $d[$i];
            }
        }

        $segmentos = [];
        for ($i = 0; $i < $n - 1; $i++) {
            $h = $limpios[$i + 1][0] - $limpios[$i][0];
            $segmentos[] = [
                $limpios[$i][0], $limpios[$i][1],
                $limpios[$i][0] + $h / 3, $limpios[$i][1] + $m[$i] * $h / 3,
                $limpios[$i + 1][0] - $h / 3, $limpios[$i + 1][1] - $m[$i + 1] * $h / 3,
                $limpios[$i + 1][0], $limpios[$i + 1][1],
            ];
        }
        return $segmentos;
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
    // Trazos apilados (ABR / VEMP)
    // -----------------------------------------------------------------

    /**
     * Una pila de trazos, uno por intensidad, como los imprime cualquier
     * equipo de potenciales: el eje X es el tiempo en ms y cada trazo va
     * corrido hacia abajo, rotulado con su nivel.
     *
     * La ganancia vertical es ÚNICA para toda la pila y sale del trazo más
     * grande: si cada uno se escalara a su propio máximo, la respuesta del
     * umbral se vería igual de alta que la de 80 dB y desaparecería
     * justamente lo que hay que leer.
     *
     * @param array<int,array{rotulo:string,pts:array<int,array{0:float,1:float}>,marcas?:array<int,array{t:float,v:float,texto:string}>}> $series
     */
    public static function waveformStack(
        MiniPdf $pdf,
        float $x,
        float $y,
        float $w,
        float $h,
        array $series,
        string $color,
        float $hasta = 12.0,
        string $unidadX = 'ms'
    ): void {
        $series = array_values(array_filter($series, static fn ($s) => !empty($s['pts'])));
        if ($series === []) {
            return;
        }
        [$px, $py, $pw, $ph] = self::plotBox($x, $y, $w, $h);

        $fx = static fn (float $t): float => $px + max(0.0, min($hasta, $t)) / $hasta * $pw;

        // Grilla temporal: una línea cada 2 ms (cada 5 si la ventana es
        // larga, como la del VEMP).
        $paso = $hasta > 20 ? 5.0 : 2.0;
        for ($t = 0.0; $t <= $hasta + 0.01; $t += $paso) {
            $lineX = $fx($t);
            $pdf->line($lineX, $py, $lineX, $py + $ph, 0.4, self::COLOR_GRID);
            $pdf->textCenter($lineX, $py + $ph + self::EJE_INF - 3, self::num($t), 5.0, false, self::COLOR_ROTULO);
        }
        $pdf->rect($px, $py, $pw, $ph, 0.7, self::COLOR_GRID_FUERTE);
        $pdf->text($x, $y + 6, $unidadX, 5.0, false, self::COLOR_ROTULO);

        $pico = 0.0;
        foreach ($series as $serie) {
            foreach ($serie['pts'] as $pt) {
                $pico = max($pico, abs((float) $pt[1]));
            }
        }
        $pico = max(0.05, $pico);

        $separacion = $ph / count($series);
        $ganancia = $separacion * 0.40 / $pico;

        foreach ($series as $i => $serie) {
            $base = $py + $separacion * ($i + 0.5);
            // Línea de base: sin ella un trazo plano (sin respuesta) no se
            // distingue de un trazo que no se dibujó.
            $pdf->line($px, $base, $px + $pw, $base, 0.3, self::COLOR_GRID);

            $pts = [];
            foreach ($serie['pts'] as [$t, $v]) {
                $pts[] = [$fx((float) $t), $base - (float) $v * $ganancia];
            }
            $pdf->polyline($pts, 0.9, $color);
            $pdf->textRight($px - 3, $base + 2, (string) $serie['rotulo'], 5.5, false, self::COLOR_ROTULO);

            foreach ($serie['marcas'] ?? [] as $marca) {
                $mx = $fx((float) $marca['t']);
                $my = $base - (float) $marca['v'] * $ganancia;
                $pdf->textCenter($mx, $my - 3, (string) $marca['texto'], 6.0, true, $color);
                $pdf->circle($mx, $my, 1.0, null, $color);
            }
        }
    }

    // -----------------------------------------------------------------
    // Curvas de OEA
    // -----------------------------------------------------------------

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

        $aire = $pw * self::AIRE_EJE;
        $util = $pw - 2 * $aire;
        $fx = static fn (float $hz): float => $px + $aire + (log($hz, 2) - $minLog) / max(0.001, $maxLog - $minLog) * $util;
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

    /**
     * Panel de una prueba de OEA: área normal sombreada, piso de ruido y la
     * respuesta de cada oído.
     *
     * El área es lo que faltaba para poder leer el gráfico: una emisión de
     * 4 dB SPL no dice nada sola -- dice todo cuando se ve que la banda
     * normal de esa frecuencia empieza en 0 y el piso de ruido está en -20.
     *
     * @param array<int,int> $bandas frecuencias de ESTA prueba
     * @param array<int,array{0:float,1:float}> $area Hz => [mínimo, máximo] normal
     * @param array<int,float> $piso Hz => piso de ruido
     * @param array<string,array<int,float>> $porLado 'od'/'oi' => Hz => dB
     * @param array{0:float,1:float} $rangoY
     */
    public static function oaePanel(
        MiniPdf $pdf,
        float $x,
        float $y,
        float $w,
        float $h,
        array $bandas,
        array $area,
        array $piso,
        array $porLado,
        array $rangoY,
        string $unidad = 'dB SPL'
    ): void {
        if ($bandas === []) {
            return;
        }
        [$px, $py, $pw, $ph] = self::plotBox($x, $y, $w, $h);
        $minY = $rangoY[0];
        $maxY = $rangoY[1];
        $minLog = log((float) $bandas[0], 2);
        $maxLog = log((float) $bandas[count($bandas) - 1], 2);

        $aire = $pw * self::AIRE_EJE;
        $util = $pw - 2 * $aire;
        $fx = static fn (float $hz): float => $px + $aire + (log($hz, 2) - $minLog) / max(0.001, $maxLog - $minLog) * $util;
        $fy = static fn (float $db): float => $py + ($maxY - max($minY, min($maxY, $db))) / ($maxY - $minY) * $ph;

        // Área normal primero: todo lo demás va encima.
        $arriba = [];
        $abajo = [];
        foreach ($bandas as $hz) {
            if (!isset($area[$hz])) {
                continue;
            }
            $arriba[] = [$fx((float) $hz), $fy((float) $area[$hz][1])];
            array_unshift($abajo, [$fx((float) $hz), $fy((float) $area[$hz][0])]);
        }
        if (count($arriba) > 1) {
            $pdf->polygon(array_merge($arriba, $abajo), null, '#e4ebf2');
        }

        foreach ($bandas as $hz) {
            $lineX = $fx((float) $hz);
            $pdf->line($lineX, $py, $lineX, $py + $ph, 0.4, self::COLOR_GRID);
            $pdf->textCenter($lineX, $py - 3, self::freqLabel((int) $hz), 5.0, false, self::COLOR_ROTULO);
        }
        $paso = ($maxY - $minY) > 40 ? 10 : 5;
        for ($db = $minY; $db <= $maxY; $db += $paso) {
            $lineY = $fy((float) $db);
            $pdf->line($px, $lineY, $px + $pw, $lineY, 0.3, self::COLOR_GRID);
            $pdf->textRight($px - 3, $lineY + 2, (string) (int) $db, 5.0, false, self::COLOR_ROTULO);
        }
        $pdf->rect($px, $py, $pw, $ph, 0.7, self::COLOR_GRID_FUERTE);
        $pdf->text($x, $y + $h - 1.5, $unidad, 5.0, false, self::COLOR_ROTULO);

        // Piso de ruido: punteado, que es como lo dibuja cualquier equipo.
        $ptsPiso = [];
        foreach ($bandas as $hz) {
            if (isset($piso[$hz])) {
                $ptsPiso[] = [$fx((float) $hz), $fy((float) $piso[$hz])];
            }
        }
        $pdf->polyline($ptsPiso, 0.7, '#777777', [1.5, 1.5]);

        foreach (['od' => self::COLOR_OD, 'oi' => self::COLOR_OI] as $lado => $color) {
            $vals = $porLado[$lado] ?? null;
            if (!is_array($vals)) {
                continue;
            }
            $pts = [];
            foreach ($bandas as $hz) {
                if (isset($vals[$hz])) {
                    $pts[] = [$fx((float) $hz), $fy((float) $vals[$hz])];
                }
            }
            $pdf->polyline($pts, 1.1, $color);
            foreach ($pts as $pt) {
                $pdf->circle($pt[0], $pt[1], 1.5, null, $color);
            }
        }
    }

    /**
     * TEOAE: una barra por oído y banda, con el ruido SUPERPUESTO en gris
     * dentro de la misma barra, que es como lo dibuja un equipo de
     * transientes. Lo que asoma por encima del gris es la relación
     * señal/ruido: se lee como altura, sin restar dos barras con el ojo.
     *
     * Sobre cada barra va su marca --un tick si esa banda pasa el criterio,
     * una R si no-- EN EL COLOR DEL OÍDO. No es decoración: cuando el ruido
     * tapa a la emisión la barra se ve toda gris, y sin esa marca no habría
     * forma de saber de qué oído es.
     *
     * @param array<int,int> $bandas
     * @param array<string,array<int,float>> $senal lado => Hz => dB SPL
     * @param array<string,array<int,float>> $ruido lado => Hz => dB SPL
     * @param array<string,array<int,bool>> $pasa lado => Hz => supera el criterio
     */
    public static function oaeBars(
        MiniPdf $pdf,
        float $x,
        float $y,
        float $w,
        float $h,
        array $bandas,
        array $senal,
        array $ruido,
        array $pasa,
        array $rangoY
    ): void {
        if ($bandas === []) {
            return;
        }
        [$px, $py, $pw, $ph] = self::plotBox($x, $y, $w, $h);
        $minY = $rangoY[0];
        $maxY = $rangoY[1];
        $fy = static fn (float $db): float => $py + ($maxY - max($minY, min($maxY, $db))) / ($maxY - $minY) * $ph;

        for ($db = $minY; $db <= $maxY; $db += 5) {
            $lineY = $fy((float) $db);
            $cero = abs($db) < 0.01;
            $pdf->line($px, $lineY, $px + $pw, $lineY, $cero ? 0.6 : 0.3, $cero ? self::COLOR_GRID_FUERTE : self::COLOR_GRID);
            if ((int) $db % 10 === 0) {
                $pdf->textRight($px - 3, $lineY + 2, (string) (int) $db, 5.0, false, self::COLOR_ROTULO);
            }
        }
        $pdf->rect($px, $py, $pw, $ph, 0.7, self::COLOR_GRID_FUERTE);
        $pdf->text($x, $y + $h - 1.5, 'dB SPL', 5.0, false, self::COLOR_ROTULO);

        $celda = $pw / count($bandas);
        $anchoBarra = min(10.0, $celda * 0.3);
        $base = $fy($minY);

        foreach (array_values($bandas) as $i => $hz) {
            $centro = $px + $celda * ($i + 0.5);
            $pdf->textCenter($centro, $py + $ph + self::EJE_INF - 3, self::freqLabel((int) $hz), 5.0, false, self::COLOR_ROTULO);

            foreach ([
                ['od', self::COLOR_OD, $centro - $anchoBarra * 0.6 - $anchoBarra / 2],
                ['oi', self::COLOR_OI, $centro + $anchoBarra * 0.6 - $anchoBarra / 2],
            ] as [$lado, $color, $xBarra]) {
                $valorSenal = (float) ($senal[$lado][$hz] ?? $minY);
                $valorRuido = (float) ($ruido[$lado][$hz] ?? $minY);

                // La emisión primero y el ruido encima: si el ruido la tapa,
                // la barra se ve gris entera, que es exactamente lo que pasó.
                foreach ([[$valorSenal, $color], [$valorRuido, '#9a9a9a']] as [$valor, $colorBarra]) {
                    $yValor = $fy($valor);
                    $alto = $base - $yValor;
                    if ($alto > 0.4) {
                        $pdf->rectFilled($xBarra, $yValor, $anchoBarra, $alto, $colorBarra);
                    }
                }

                $marca = max($fy($valorSenal), $fy($valorRuido)) === $fy($valorSenal)
                    ? $fy($valorRuido)
                    : $fy($valorSenal);
                $yMarca = min($fy($valorSenal), $fy($valorRuido)) - 4;
                if (!empty($pasa[$lado][$hz])) {
                    self::tick($pdf, $xBarra + $anchoBarra / 2, $yMarca, $color);
                } else {
                    $pdf->textCenter($xBarra + $anchoBarra / 2, $yMarca + 2, 'R', 5.5, true, $color);
                }
            }
        }
    }

    /** Tick de "pasa", dibujado: el carácter no existe en WinAnsi. */
    private static function tick(MiniPdf $pdf, float $x, float $y, string $color): void
    {
        $pdf->polyline([[$x - 2.4, $y - 0.6], [$x - 0.8, $y + 1.4], [$x + 2.6, $y - 2.8]], 1.1, $color);
    }

    /**
     * Espectro del SOAE: el piso de ruido y los picos declarados. Sin
     * estímulo -- es un registro en silencio, así que lo único que hay que
     * mostrar es dónde asoma algo sobre el ruido.
     *
     * @param array<string,array<int,array{hz:float,db:float}>> $porLado
     */
    public static function soaeSpectrum(
        MiniPdf $pdf,
        float $x,
        float $y,
        float $w,
        float $h,
        array $porLado,
        array $rangoHz,
        array $rangoY,
        callable $piso,
        ?array $zonaPicos = null
    ): void {
        [$px, $py, $pw, $ph] = self::plotBox($x, $y, $w, $h);
        $minLog = log((float) $rangoHz[0], 2);
        $maxLog = log((float) $rangoHz[1], 2);
        $aire = $pw * self::AIRE_EJE;
        $util = $pw - 2 * $aire;
        $fx = static fn (float $hz): float => $px + $aire + (log(max(1.0, $hz), 2) - $minLog) / max(0.001, $maxLog - $minLog) * $util;
        $fy = static fn (float $db): float => $py + ($rangoY[1] - max($rangoY[0], min($rangoY[1], $db))) / ($rangoY[1] - $rangoY[0]) * $ph;

        // La franja donde los picos son posibles: sin ella, un registro sin
        // picos es un rectángulo vacío que no dice ni dónde se los busca.
        if ($zonaPicos !== null) {
            $pdf->rectFilled(
                $fx((float) $zonaPicos[0]),
                $py,
                $fx((float) $zonaPicos[1]) - $fx((float) $zonaPicos[0]),
                $ph,
                '#eef2f6'
            );
        }

        foreach ([500, 1000, 2000, 4000, 7000] as $hz) {
            if ($hz < $rangoHz[0] || $hz > $rangoHz[1]) {
                continue;
            }
            $lineX = $fx((float) $hz);
            $pdf->line($lineX, $py, $lineX, $py + $ph, 0.4, self::COLOR_GRID);
            $pdf->textCenter($lineX, $py - 3, self::freqLabel($hz), 5.0, false, self::COLOR_ROTULO);
        }
        for ($db = $rangoY[0]; $db <= $rangoY[1]; $db += 10) {
            $lineY = $fy((float) $db);
            $pdf->line($px, $lineY, $px + $pw, $lineY, 0.3, self::COLOR_GRID);
            $pdf->textRight($px - 3, $lineY + 2, (string) (int) $db, 5.0, false, self::COLOR_ROTULO);
        }
        $pdf->rect($px, $py, $pw, $ph, 0.7, self::COLOR_GRID_FUERTE);
        $pdf->text($x, $y + $h - 1.5, 'dB SPL', 5.0, false, self::COLOR_ROTULO);

        // Piso de ruido: sube en los graves y algo en los agudos.
        $ptsPiso = [];
        for ($hz = (float) $rangoHz[0]; $hz <= $rangoHz[1]; $hz *= 1.08) {
            $ptsPiso[] = [$fx($hz), $fy((float) $piso($hz))];
        }
        $pdf->polyline($ptsPiso, 0.7, '#777777', [1.5, 1.5]);

        foreach (['od' => self::COLOR_OD, 'oi' => self::COLOR_OI] as $lado => $color) {
            foreach ($porLado[$lado] ?? [] as $pico) {
                $hz = (float) $pico['hz'];
                if ($hz < $rangoHz[0] || $hz > $rangoHz[1]) {
                    continue;
                }
                $cx = $fx($hz);
                $pdf->line($cx, $fy((float) $piso($hz)), $cx, $fy((float) $pico['db']), 1.2, $color);
                $pdf->circle($cx, $fy((float) $pico['db']), 1.6, null, $color);
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

    /**
     * Parte una serie en los tramos que SÍ tienen umbral. Los huecos no se
     * unen: una línea que cruza por encima de una frecuencia sin respuesta
     * inventa un umbral que nadie midió.
     *
     * @param array<int,float> $valores por índice de frecuencia
     * @param array<int,int> $freqs frecuencias a considerar (en orden)
     * @param callable $fx Hz -> x
     * @param callable $fy dB -> y
     * @return array<int,array<int,array{0:float,1:float}>> tramos de puntos
     */
    private static function tramosConUmbral(array $valores, array $freqs, callable $fx, callable $fy): array
    {
        $tramos = [];
        $actual = [];
        foreach ($freqs as $i => $hz) {
            $valor = (float) ($valores[$i] ?? 0);
            if ($valor >= self::SIN_UMBRAL_DB) {
                if (count($actual) > 0) {
                    $tramos[] = $actual;
                    $actual = [];
                }
                continue;
            }
            $actual[] = [$fx((float) $hz), $fy($valor)];
        }
        if (count($actual) > 0) {
            $tramos[] = $actual;
        }
        return $tramos;
    }

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

    /**
     * LDL: triángulo RECTÁNGULO con el cateto vertical mirando a la línea de
     * la frecuencia -- el OD a su izquierda y el OI a su derecha, separados
     * un pelo para que no se monten sobre ella ni entre sí.
     *
     * @param int $lado -1 a la izquierda de la línea (OD), 1 a la derecha (OI)
     */
    private static function ldl(MiniPdf $pdf, float $x, float $y, string $color, int $lado): void
    {
        $separacion = 1.6;
        $alto = 5.4;
        $ancho = 4.6;

        // Cateto vertical pegado (con su aire) a la línea; el ángulo recto
        // abajo y la hipotenusa cerrando hacia afuera y hacia arriba.
        $xCateto = $x + $lado * $separacion;
        $xPunta = $xCateto + $lado * $ancho;
        $pdf->polygon(
            [
                [$xCateto, $y - $alto / 2],
                [$xCateto, $y + $alto / 2],
                [$xPunta, $y + $alto / 2],
            ],
            null,
            $color
        );
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
