<?php

declare(strict_types=1);

/**
 * Código QR como SVG, sin dependencias (el backend se despliega copiando
 * archivos; ver tests/run.php). Lo usan las tarjetas del OSCE: cada alumno
 * lleva un QR a su página de avance (student/osce.php?t=...).
 *
 * Alcance acotado a lo que se necesita: modo byte, corrección M, versiones
 * 1 a 10 (hasta 213 bytes; una URL con token cabe holgada en la 6 o la 7).
 * Sigue la norma ISO/IEC 18004 en la forma en que la implementa Nayuki
 * (qrcodegen): mismos patrones, mismo orden de colocación, misma
 * penalización para elegir la máscara. Verificado leyendo los SVG con
 * zbarimg.
 */
final class QrSvg
{
    /**
     * Por versión, corrección M: bloques de datos (bytes por bloque) y bytes
     * de corrección por bloque.
     */
    private const BLOQUES_M = [
        1 => [[16], 10],
        2 => [[28], 16],
        3 => [[44], 26],
        4 => [[32, 32], 18],
        5 => [[43, 43], 24],
        6 => [[27, 27, 27, 27], 16],
        7 => [[31, 31, 31, 31], 18],
        8 => [[38, 38, 39, 39], 22],
        9 => [[36, 36, 36, 37, 37], 22],
        10 => [[43, 43, 43, 43, 44], 26],
    ];

    private const ALINEACION = [
        1 => [], 2 => [6, 18], 3 => [6, 22], 4 => [6, 26], 5 => [6, 30],
        6 => [6, 34], 7 => [6, 22, 38], 8 => [6, 24, 42], 9 => [6, 26, 46], 10 => [6, 28, 50],
    ];

    private const INFO_VERSION = [7 => 0x07C94, 8 => 0x085BC, 9 => 0x09A99, 10 => 0x0A4D3];

    /** @var array<int, array<int, bool>> [fila][columna] */
    private array $m = [];
    /** @var array<int, array<int, bool>> módulos de patrón (no llevan datos ni máscara) */
    private array $fijo = [];
    private int $n = 0;

    /** SVG listo para incrustar en HTML; $modulo = px por módulo. */
    public static function svg(string $texto, int $modulo = 4): string
    {
        $mat = self::matriz($texto);
        $n = count($mat);
        $borde = 4;
        $lado = ($n + 2 * $borde) * $modulo;
        $d = '';
        for ($y = 0; $y < $n; $y++) {
            for ($x = 0; $x < $n; $x++) {
                if ($mat[$y][$x]) {
                    $d .= 'M' . ($x + $borde) . ',' . ($y + $borde) . 'h1v1h-1z';
                }
            }
        }
        $total = $n + 2 * $borde;
        return '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ' . $total . ' ' . $total
            . '" width="' . $lado . '" height="' . $lado . '" shape-rendering="crispEdges" role="img" aria-label="Código QR">'
            . '<rect width="100%" height="100%" fill="#fff"/><path d="' . $d . '" fill="#000"/></svg>';
    }

    /**
     * La matriz de módulos (true = oscuro), sin zona de silencio.
     *
     * @return array<int, array<int, bool>>
     */
    public static function matriz(string $texto): array
    {
        $len = strlen($texto);
        $version = 0;
        foreach (self::BLOQUES_M as $v => [$bloques]) {
            $bitsCuenta = $v < 10 ? 8 : 16;
            if (4 + $bitsCuenta + 8 * $len <= 8 * array_sum($bloques)) {
                $version = $v;
                break;
            }
        }
        if ($version === 0) {
            throw new InvalidArgumentException('Texto demasiado largo para el QR (máximo versión 10).');
        }
        $qr = new self();
        return $qr->construir($texto, $version);
    }

    /** @return array<int, array<int, bool>> */
    private function construir(string $texto, int $version): array
    {
        $this->n = 17 + 4 * $version;
        $fila = array_fill(0, $this->n, false);
        $this->m = array_fill(0, $this->n, $fila);
        $this->fijo = array_fill(0, $this->n, $fila);

        $this->patrones($version);
        $palabras = $this->palabras($texto, $version);
        $this->colocar($palabras);

        // La máscara de menor penalización.
        $mejor = 0;
        $menor = PHP_INT_MAX;
        for ($mask = 0; $mask < 8; $mask++) {
            $this->aplicarMascara($mask);
            $this->formato($mask);
            $p = $this->penalizacion();
            if ($p < $menor) {
                $menor = $p;
                $mejor = $mask;
            }
            $this->aplicarMascara($mask); // XOR: la deshace
        }
        $this->aplicarMascara($mejor);
        $this->formato($mejor);
        return $this->m;
    }

    private function poner(int $x, int $y, bool $oscuro): void
    {
        $this->m[$y][$x] = $oscuro;
        $this->fijo[$y][$x] = true;
    }

    private function patrones(int $version): void
    {
        $n = $this->n;
        for ($i = 0; $i < $n; $i++) {
            $this->poner(6, $i, $i % 2 === 0);
            $this->poner($i, 6, $i % 2 === 0);
        }
        foreach ([[3, 3], [$n - 4, 3], [3, $n - 4]] as [$cx, $cy]) {
            for ($dy = -4; $dy <= 4; $dy++) {
                for ($dx = -4; $dx <= 4; $dx++) {
                    $x = $cx + $dx;
                    $y = $cy + $dy;
                    if ($x >= 0 && $x < $n && $y >= 0 && $y < $n) {
                        $dist = max(abs($dx), abs($dy));
                        $this->poner($x, $y, $dist !== 2 && $dist !== 4);
                    }
                }
            }
        }
        $pos = self::ALINEACION[$version];
        $k = count($pos);
        for ($i = 0; $i < $k; $i++) {
            for ($j = 0; $j < $k; $j++) {
                if (($i === 0 && $j === 0) || ($i === 0 && $j === $k - 1) || ($i === $k - 1 && $j === 0)) {
                    continue;
                }
                for ($dy = -2; $dy <= 2; $dy++) {
                    for ($dx = -2; $dx <= 2; $dx++) {
                        $this->poner($pos[$i] + $dx, $pos[$j] + $dy, max(abs($dx), abs($dy)) !== 1);
                    }
                }
            }
        }
        $this->formato(0); // reserva el lugar; se reescribe con la máscara elegida
        if ($version >= 7) {
            $bits = self::INFO_VERSION[$version];
            for ($i = 0; $i < 18; $i++) {
                $bit = (($bits >> $i) & 1) === 1;
                $a = $n - 11 + $i % 3;
                $b = intdiv($i, 3);
                $this->poner($a, $b, $bit);
                $this->poner($b, $a, $bit);
            }
        }
    }

    private function formato(int $mask): void
    {
        $datos = (0 << 3) | $mask; // nivel M = 00
        $rem = $datos;
        for ($i = 0; $i < 10; $i++) {
            $rem = ($rem << 1) ^ (($rem >> 9) * 0x537);
        }
        $bits = (($datos << 10) | $rem) ^ 0x5412;
        $bit = static fn (int $i): bool => (($bits >> $i) & 1) === 1;
        $n = $this->n;
        for ($i = 0; $i <= 5; $i++) {
            $this->poner(8, $i, $bit($i));
        }
        $this->poner(8, 7, $bit(6));
        $this->poner(8, 8, $bit(7));
        $this->poner(7, 8, $bit(8));
        for ($i = 9; $i < 15; $i++) {
            $this->poner(14 - $i, 8, $bit($i));
        }
        for ($i = 0; $i < 8; $i++) {
            $this->poner($n - 1 - $i, 8, $bit($i));
        }
        for ($i = 8; $i < 15; $i++) {
            $this->poner(8, $n - 15 + $i, $bit($i));
        }
        $this->poner(8, $n - 8, true); // módulo oscuro fijo
    }

    /** @return int[] palabras finales (datos y corrección intercalados) */
    private function palabras(string $texto, int $version): array
    {
        [$bloques, $ec] = self::BLOQUES_M[$version];
        $capacidad = array_sum($bloques);

        $bits = [];
        $agregar = static function (int $valor, int $largo) use (&$bits): void {
            for ($i = $largo - 1; $i >= 0; $i--) {
                $bits[] = ($valor >> $i) & 1;
            }
        };
        $agregar(0b0100, 4);
        $agregar(strlen($texto), $version < 10 ? 8 : 16);
        foreach (str_split($texto) as $c) {
            $agregar(ord($c), 8);
        }
        $agregar(0, min(4, $capacidad * 8 - count($bits)));
        $agregar(0, (8 - count($bits) % 8) % 8);
        $datos = [];
        foreach (array_chunk($bits, 8) as $byte) {
            $datos[] = (int) bindec(implode('', $byte));
        }
        for ($relleno = 0xEC; count($datos) < $capacidad; $relleno ^= 0xEC ^ 0x11) {
            $datos[] = $relleno;
        }

        $divisor = self::divisor($ec);
        $partes = [];
        $correcciones = [];
        $desde = 0;
        foreach ($bloques as $largo) {
            $parte = array_slice($datos, $desde, $largo);
            $desde += $largo;
            $partes[] = $parte;
            $correcciones[] = self::resto($parte, $divisor);
        }
        $salida = [];
        $max = max($bloques);
        for ($i = 0; $i < $max; $i++) {
            foreach ($partes as $parte) {
                if ($i < count($parte)) {
                    $salida[] = $parte[$i];
                }
            }
        }
        for ($i = 0; $i < $ec; $i++) {
            foreach ($correcciones as $corr) {
                $salida[] = $corr[$i];
            }
        }
        return $salida;
    }

    private static function mul(int $x, int $y): int
    {
        $z = 0;
        for ($i = 7; $i >= 0; $i--) {
            $z = (($z << 1) ^ (($z >> 7) * 0x11D)) & 0xFF;
            $z ^= (($y >> $i) & 1) * $x;
        }
        return $z;
    }

    /** @return int[] */
    private static function divisor(int $grado): array
    {
        $r = array_fill(0, $grado, 0);
        $r[$grado - 1] = 1;
        $raiz = 1;
        for ($i = 0; $i < $grado; $i++) {
            for ($j = 0; $j < $grado; $j++) {
                $r[$j] = self::mul($r[$j], $raiz);
                if ($j + 1 < $grado) {
                    $r[$j] ^= $r[$j + 1];
                }
            }
            $raiz = self::mul($raiz, 0x02);
        }
        return $r;
    }

    /** @param int[] $datos @param int[] $divisor @return int[] */
    private static function resto(array $datos, array $divisor): array
    {
        $grado = count($divisor);
        $r = array_fill(0, $grado, 0);
        foreach ($datos as $b) {
            $factor = $b ^ $r[0];
            array_shift($r);
            $r[] = 0;
            for ($i = 0; $i < $grado; $i++) {
                $r[$i] ^= self::mul($divisor[$i], $factor);
            }
        }
        return $r;
    }

    /** @param int[] $palabras */
    private function colocar(array $palabras): void
    {
        $n = $this->n;
        $total = count($palabras) * 8;
        $i = 0;
        for ($der = $n - 1; $der >= 1; $der -= 2) {
            if ($der === 6) {
                $der = 5;
            }
            for ($v = 0; $v < $n; $v++) {
                for ($j = 0; $j < 2; $j++) {
                    $x = $der - $j;
                    $sube = (($der + 1) & 2) === 0;
                    $y = $sube ? $n - 1 - $v : $v;
                    if (!$this->fijo[$y][$x] && $i < $total) {
                        $this->m[$y][$x] = (($palabras[$i >> 3] >> (7 - ($i & 7))) & 1) === 1;
                        $i++;
                    }
                }
            }
        }
    }

    private function aplicarMascara(int $mask): void
    {
        $n = $this->n;
        for ($y = 0; $y < $n; $y++) {
            for ($x = 0; $x < $n; $x++) {
                if ($this->fijo[$y][$x]) {
                    continue;
                }
                switch ($mask) {
                    case 0: $inv = ($x + $y) % 2 === 0; break;
                    case 1: $inv = $y % 2 === 0; break;
                    case 2: $inv = $x % 3 === 0; break;
                    case 3: $inv = ($x + $y) % 3 === 0; break;
                    case 4: $inv = (intdiv($x, 3) + intdiv($y, 2)) % 2 === 0; break;
                    case 5: $inv = $x * $y % 2 + $x * $y % 3 === 0; break;
                    case 6: $inv = ($x * $y % 2 + $x * $y % 3) % 2 === 0; break;
                    default: $inv = (($x + $y) % 2 + $x * $y % 3) % 2 === 0; break;
                }
                if ($inv) {
                    $this->m[$y][$x] = !$this->m[$y][$x];
                }
            }
        }
    }

    private function penalizacion(): int
    {
        $n = $this->n;
        $p = 0;
        $oscuros = 0;
        $lineas = [];
        for ($i = 0; $i < $n; $i++) {
            $fila = [];
            $col = [];
            for ($j = 0; $j < $n; $j++) {
                $fila[] = $this->m[$i][$j] ? 1 : 0;
                $col[] = $this->m[$j][$i] ? 1 : 0;
            }
            $lineas[] = $fila;
            $lineas[] = $col;
            $oscuros += array_sum($fila);
        }
        foreach ($lineas as $l) {
            // Regla 1: corridas de 5 o más del mismo color.
            $corrida = 1;
            for ($j = 1; $j <= $n; $j++) {
                if ($j < $n && $l[$j] === $l[$j - 1]) {
                    $corrida++;
                    continue;
                }
                if ($corrida >= 5) {
                    $p += 3 + ($corrida - 5);
                }
                $corrida = 1;
            }
            // Regla 3: patrón parecido al buscador, con 4 claros a un lado.
            $s = '0000' . implode('', $l) . '0000';
            foreach (['10111010000', '00001011101'] as $patron) {
                $desde = 0;
                while (($pos = strpos($s, $patron, $desde)) !== false) {
                    $p += 40;
                    $desde = $pos + 1;
                }
            }
        }
        // Regla 2: bloques de 2x2 del mismo color.
        for ($y = 0; $y < $n - 1; $y++) {
            for ($x = 0; $x < $n - 1; $x++) {
                $c = $this->m[$y][$x];
                if ($c === $this->m[$y][$x + 1] && $c === $this->m[$y + 1][$x] && $c === $this->m[$y + 1][$x + 1]) {
                    $p += 3;
                }
            }
        }
        // Regla 4: proporción de oscuros lejos del 50 %.
        $total = $n * $n;
        $k = intdiv(abs($oscuros * 20 - $total * 10) + $total - 1, $total) - 1;
        return $p + max(0, $k) * 10;
    }
}
