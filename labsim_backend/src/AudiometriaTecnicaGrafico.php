<?php

declare(strict_types=1);

require_once __DIR__ . '/AudiometriaPaciente.php';
require_once __DIR__ . '/CaseCharts.php';

/**
 * La técnica de audiometría de una atención en dos gráficos sin palabras
 * (SVG inline, sin JS: se ve igual en el iframe de la plataforma del curso y
 * en el celular). Reemplaza a la franja de acciones de "Tu última atención"
 * en lti/launch.php, que no decía nada.
 *
 * - audiograma(): los umbrales que obtuvo el alumno, con los símbolos de
 *   siempre. Los que no corresponden a la audición del paciente llevan un
 *   halo ámbar. NUNCA se dibuja el umbral real: sería darle la respuesta.
 * - pasos(): un cuadrito por regla de la técnica (verde = cumplida, rojo =
 *   no), agrupados por prueba bajo su símbolo (→ orden, O X aéreos, < >
 *   óseos).
 *
 * El detalle con palabras está en student/atencion.php; acá solo el <title>
 * de cada elemento, para quien pase el mouse.
 *
 * Entrada: el resultado de AudiometriaTecnica::evaluar().
 */
final class AudiometriaTecnicaGrafico
{
    private const ANCHO = 360;
    private const ALTO = 232;
    private const IZQ = 30;
    private const ARRIBA = 24;
    private const DER = 10;
    private const ABAJO = 8;
    private const DB_MIN = -10;
    private const DB_MAX = 120;
    private const HALO = '#f0a020';
    private const OK = '#2f8f46';
    private const MAL = '#c0392b';
    private const ESTADOS = [
        'coincide' => 'corresponde',
        'sombra' => 'curva sombra',
        'difiere' => 'no corresponde',
        'sin verificar' => 'no verificó 2/3 ni 3/5',
        'sin dato' => '',
    ];

    public static function audiograma(array $tecnica): string
    {
        $w = self::ANCHO - self::IZQ - self::DER;
        $h = self::ALTO - self::ARRIBA - self::ABAJO;
        $freqs = AudiometriaPaciente::FRECUENCIAS;
        $fx = static function (int $hz) use ($freqs, $w): ?float {
            $i = array_search($hz, $freqs, true);
            return $i === false ? null : self::IZQ + ($i + 0.5) * $w / count($freqs);
        };
        $fy = static function (float $db) use ($h): float {
            $db = max(self::DB_MIN, min(self::DB_MAX, $db));
            return self::ARRIBA + ($db - self::DB_MIN) / (self::DB_MAX - self::DB_MIN) * $h;
        };

        $o = [];
        $o[] = sprintf('<svg class="tecnica-audiograma" viewBox="0 0 %d %d" role="img" aria-label="Audiograma con los umbrales que obtuviste">', self::ANCHO, self::ALTO);
        $o[] = sprintf('<rect x="%d" y="%d" width="%d" height="%d" fill="#fff" stroke="#bbb"/>', self::IZQ, self::ARRIBA, $w, $h);
        for ($db = self::DB_MIN; $db <= self::DB_MAX; $db += 10) {
            $y = $fy($db);
            $o[] = sprintf('<line x1="%d" y1="%s" x2="%d" y2="%s" stroke="%s" stroke-width="%s"/>',
                self::IZQ, self::n($y), self::IZQ + $w, self::n($y), $db === 20 ? '#999' : '#e4e4e4', $db === 20 ? '1' : '0.6');
            if ($db % 20 === 0) {
                $o[] = sprintf('<text x="%d" y="%s" font-size="8" fill="#777" text-anchor="end">%d</text>', self::IZQ - 4, self::n($y + 3), $db);
            }
        }
        foreach ($freqs as $hz) {
            $x = $fx($hz);
            $o[] = sprintf('<line x1="%s" y1="%d" x2="%s" y2="%d" stroke="#eee" stroke-width="0.6"/>', self::n($x), self::ARRIBA, self::n($x), self::ARRIBA + $h);
            $o[] = sprintf('<text x="%s" y="%d" font-size="8" fill="#777" text-anchor="middle">%s</text>',
                self::n($x), self::ARRIBA - 7, $hz >= 1000 ? ($hz / 1000) . 'k' : (string) $hz);
        }

        foreach (['aereos', 'oseos'] as $via) {
            foreach (($tecnica[$via]['umbrales'] ?? []) as $oido => $filas) {
                $color = $oido === 'OD' ? CaseCharts::COLOR_OD : CaseCharts::COLOR_OI;
                $puntos = self::ultimoPorFrecuencia($filas);
                ksort($puntos);
                if ($via === 'aereos') {
                    $linea = [];
                    foreach ($puntos as $hz => $f) {
                        if ($f['estimado'] !== null) {
                            $linea[] = self::n($fx($hz)) . ',' . self::n($fy((float) $f['estimado']));
                        }
                    }
                    if (count($linea) > 1) {
                        $o[] = sprintf('<polyline points="%s" fill="none" stroke="%s" stroke-width="1.2"/>', implode(' ', $linea), $color);
                    }
                }
                foreach ($puntos as $hz => $f) {
                    $db = $f['estimado'] ?? ($f['sin_respuesta'] ? $f['maximo'] ?? null : $f['aprox']);
                    if ($db === null) {
                        continue;
                    }
                    $x = $fx($hz);
                    if ($via === 'oseos') {
                        $x += $oido === 'OD' ? -7 : 7;
                    }
                    $y = $fy((float) $db);
                    $titulo = sprintf('%s · %s · %s · %d dB%s', $oido, $via === 'aereos' ? 'aérea' : 'ósea',
                        $hz >= 1000 ? ($hz / 1000) . ' kHz' : $hz . ' Hz', $db,
                        self::ESTADOS[$f['estado']] !== '' ? ' · ' . self::ESTADOS[$f['estado']] : '');
                    $o[] = '<g><title>' . htmlspecialchars($titulo) . '</title>';
                    if ($f['estado'] !== 'coincide' && $f['estado'] !== 'sin dato') {
                        $o[] = sprintf('<circle cx="%s" cy="%s" r="9" fill="%s" fill-opacity="0.4"/>', self::n($x), self::n($y), self::HALO);
                    }
                    $o[] = self::simbolo($via, $oido, (bool) $f['con_ruido'], $x, $y, $color);
                    if ($f['estimado'] === null && $f['sin_respuesta']) {
                        $dx = $oido === 'OD' ? -1 : 1;
                        // Sin respuesta al tope del equipo: la flecha hacia abajo, hacia afuera.
                        $x1 = $x + 9 * $dx;
                        $y1 = $y + 12;
                        $o[] = sprintf('<path d="M%s %s L%s %s M%s %s L%s %s L%s %s" fill="none" stroke="%s" stroke-width="1.2"/>',
                            self::n($x + 4 * $dx), self::n($y + 5), self::n($x1), self::n($y1),
                            self::n($x1 - 4 * $dx), self::n($y1), self::n($x1), self::n($y1), self::n($x1), self::n($y1 - 4), $color);
                    }
                    $o[] = '</g>';
                }
            }
        }
        $o[] = '</svg>';
        return implode("\n", $o);
    }

    public static function pasos(array $tecnica): string
    {
        $grupos = [];
        foreach (['orden', 'aereos', 'oseos'] as $k) {
            $reglas = $tecnica[$k]['reglas'] ?? [];
            foreach (($tecnica[$k]['oidos'] ?? []) as $porOido) {
                $reglas = array_merge($reglas, $porOido);
            }
            $reglas = array_values(array_filter($reglas, static function ($r) { return $r['cumple'] !== null; }));
            if ($reglas !== []) {
                $grupos[$k] = $reglas;
            }
        }
        if ($grupos === []) {
            return '';
        }
        $lado = 12;
        $paso = 15;
        $hueco = 18;
        $ancho = 0;
        foreach ($grupos as $reglas) {
            $ancho += count($reglas) * $paso - ($paso - $lado) + $hueco;
        }
        $ancho -= $hueco;
        $o = [];
        $o[] = sprintf('<svg class="tecnica-pasos" viewBox="0 0 %d 34" role="img" aria-label="Pasos de la técnica: verde cumplido, rojo no">', $ancho);
        $x = 0;
        foreach ($grupos as $k => $reglas) {
            $anchoGrupo = count($reglas) * $paso - ($paso - $lado);
            $o[] = self::iconoGrupo($k, $x + $anchoGrupo / 2, 8);
            foreach ($reglas as $r) {
                $o[] = sprintf('<rect x="%s" y="18" width="%d" height="%d" rx="2" fill="%s"><title>%s</title></rect>',
                    self::n($x), $lado, $lado, $r['cumple'] ? self::OK : self::MAL, htmlspecialchars((string) $r['texto']));
                $x += $paso;
            }
            $x += $hueco - ($paso - $lado);
        }
        $o[] = '</svg>';
        return implode("\n", $o);
    }

    /**
     * Una fila por frecuencia: la última vez que la tomó (la repetición de
     * 1 kHz pisa a la primera; es la que vale al final del oído).
     */
    private static function ultimoPorFrecuencia(array $filas): array
    {
        $porHz = [];
        foreach ($filas as $f) {
            $porHz[(int) $f['freq']] = $f;
        }
        return $porHz;
    }

    private static function simbolo(string $via, string $oido, bool $enmascarado, float $x, float $y, string $c): string
    {
        $cx = self::n($x);
        $cy = self::n($y);
        $trazo = sprintf('fill="none" stroke="%s" stroke-width="1.5"', $c);
        if ($via === 'aereos') {
            if ($oido === 'OD') {
                return $enmascarado
                    ? sprintf('<path d="M%s %s l5 9 h-10 z" %s/>', $cx, self::n($y - 5.5), $trazo)
                    : sprintf('<circle cx="%s" cy="%s" r="4.5" fill="#fff" stroke="%s" stroke-width="1.5"/>', $cx, $cy, $c);
            }
            return $enmascarado
                ? sprintf('<rect x="%s" y="%s" width="9" height="9" %s/>', self::n($x - 4.5), self::n($y - 4.5), $trazo)
                : sprintf('<path d="M%s %s l9 9 m0 -9 l-9 9" %s/>', self::n($x - 4.5), self::n($y - 4.5), $trazo);
        }
        if ($oido === 'OD') {
            return $enmascarado
                ? sprintf('<path d="M%s %s h-4 v10 h4" %s/>', self::n($x + 2), self::n($y - 5), $trazo)
                : sprintf('<path d="M%s %s l-5 5 l5 5" %s/>', self::n($x + 2.5), self::n($y - 5), $trazo);
        }
        return $enmascarado
            ? sprintf('<path d="M%s %s h4 v10 h-4" %s/>', self::n($x - 2), self::n($y - 5), $trazo)
            : sprintf('<path d="M%s %s l5 5 l-5 5" %s/>', self::n($x - 2.5), self::n($y - 5), $trazo);
    }

    private static function iconoGrupo(string $grupo, float $x, float $y): string
    {
        $gris = 'fill="none" stroke="#666" stroke-width="1.4"';
        if ($grupo === 'orden') {
            return sprintf('<g><title>Orden de las pruebas</title><path d="M%s %s h12 m-4 -4 l4 4 l-4 4" %s/></g>', self::n($x - 6), self::n($y), $gris);
        }
        if ($grupo === 'aereos') {
            return sprintf('<g><title>Umbrales aéreos</title><circle cx="%s" cy="%s" r="4" fill="none" stroke="%s" stroke-width="1.4"/>'
                . '<path d="M%s %s l8 8 m0 -8 l-8 8" fill="none" stroke="%s" stroke-width="1.4"/></g>',
                self::n($x - 6), self::n($y), CaseCharts::COLOR_OD, self::n($x + 2), self::n($y - 4), CaseCharts::COLOR_OI);
        }
        return sprintf('<g><title>Umbrales óseos</title><path d="M%s %s l-4 4 l4 4" fill="none" stroke="%s" stroke-width="1.4"/>'
            . '<path d="M%s %s l4 4 l-4 4" fill="none" stroke="%s" stroke-width="1.4"/></g>',
            self::n($x - 3), self::n($y - 4), CaseCharts::COLOR_OD, self::n($x + 3), self::n($y - 4), CaseCharts::COLOR_OI);
    }

    private static function n(float $v): string
    {
        return rtrim(rtrim(number_format($v, 1, '.', ''), '0'), '.');
    }
}
