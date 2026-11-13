<?php

declare(strict_types=1);

require_once __DIR__ . '/AudiometriaPaciente.php';
require_once __DIR__ . '/AudiometriaRegistro.php';
require_once __DIR__ . '/CaseBuilder.php';

/**
 * Indicador de la tinnitumetría (Bibliografia::TECNICAS T03): compara lo que
 * hizo el alumno con la técnica.
 *
 * Lee la línea de tiempo que arma AudiometriaRegistro::leer() ('tinnitus'):
 * la verdad del acúfeno que mandó la app al cargar el caso (con lo que
 * sorteó: src/audiometria/acufeno.py) y una foto del equipo por evento
 * mientras rige una instrucción de tinnitumetría, más las respuestas del
 * paciente a sus dos preguntas.
 *
 * Los detalles cuentan lo que hizo el alumno, no la verdad del caso: el
 * alumno los ve.
 */
final class AudiometriaTinnitus
{
    private const TONO = 'acufeno_cual_se_parece';
    private const SONORIDAD = 'acufeno_igual_fuerte';
    private const NME = 'acufeno_deje_de_escuchar';
    private const INHIBICION = 'acufeno_un_minuto';
    private const PREG_CUAL = 'acufeno_cual';
    private const PREG_COMO = 'acufeno_como_esta';

    private const ORDINALES = ['elprimero' => 0, 'elsegundo' => 1, 'eltercero' => 2];
    private const DE_COMPARACION = ['Tono', 'FM', 'Narrow Band Noise'];
    private const DE_BANDA_ANCHA = ['White Noise', 'Speech Noise', 'Pink Noise'];
    private const OIDOS = ['OD', 'OI'];

    /** Minuto de la inhibición residual, con la tolerancia de quien mira el reloj. */
    private const MINUTO_S = 55;
    /** Paso fino para igualar la intensidad. */
    private const PASO_FINO_DB = 2;
    /** El estímulo de la inhibición: NME + 10, con un paso de 5 dB de holgura hacia abajo. */
    private const SOBRE_NME_DB = 10;
    private const SOBRE_NME_TOL_DB = 2;

    /**
     * $tin: AudiometriaRegistro::leer()['tinnitus']. Devuelve la sección
     * ('reglas', 'observaciones', 'hecha') o null si no hay nada que decir
     * (sin acúfeno y sin tinnitumetría).
     */
    public static function evaluar(array $tin, array $caso): ?array
    {
        $bloque = is_array($caso['Tinnitus'] ?? null) ? $caso['Tinnitus'] : [];
        $verdad = is_array($tin['verdad'] ?? null) ? $tin['verdad'] : null;
        $presente = $verdad !== null ? !empty($verdad['presente']) : CaseBuilder::tinnitusPresente($bloque);
        $pulsatil = $verdad !== null ? !empty($verdad['pulsatil']) : !empty($bloque['pulsatil']);
        $eventos = $tin['eventos'] ?? [];
        $hecha = false;
        foreach ($eventos as $e) {
            if ($e['instruccion'] !== null || $e['accion'] === 'audio_acufeno_respuesta') {
                $hecha = true;
                break;
            }
        }

        $reglas = [];
        $obs = [];
        if (!$presente) {
            if (!$hecha) {
                return null;
            }
            $obs[] = 'El paciente no tenía acúfeno: la tinnitumetría no correspondía.';
            return ['reglas' => [], 'observaciones' => $obs, 'hecha' => true];
        }
        if ($pulsatil) {
            $reglas[] = [
                'texto' => 'Un acúfeno pulsátil no se iguala: se deriva para buscar su causa.',
                'cumple' => !$hecha,
                'detalle' => $hecha ? 'Se hizo la tinnitumetría.' : 'No se hizo la tinnitumetría.',
            ];
            return ['reglas' => $reglas, 'observaciones' => $obs, 'hecha' => $hecha];
        }
        if (!$hecha) {
            $reglas[] = [
                'texto' => 'Con acúfeno el día del examen se hace la tinnitumetría.',
                'cumple' => false,
                'detalle' => 'No se hizo.',
            ];
            return ['reglas' => $reglas, 'observaciones' => $obs, 'hecha' => false];
        }

        $paciente = new AudiometriaPaciente($caso);
        $oidosAcufeno = $verdad['oidos'] ?? self::oidosDelBloque($bloque);
        $oidoComparacion = $verdad !== null && array_key_exists('oido_comparacion', $verdad)
            ? $verdad['oido_comparacion'] : self::comparacionDelBloque($bloque);
        $fAcufeno = (int) ($verdad['freq'] ?? ($bloque['frecuencia'] ?? 4000));

        // ---- lo que sonó en cada parte -------------------------------------
        $muestras = [self::TONO => [], self::SONORIDAD => [], self::NME => [], self::INHIBICION => []];
        $respuestasCual = [];
        $respuestasComo = [];
        $nmeNivel = null;
        $nmeOido = null;
        $nmeFreq = null;
        $igualo = null;   // la última vez que levantó la mano en la intensidad
        $pasosGruesos = [];
        $tPrimeraCual = null;
        foreach ($eventos as $e) {
            if ($e['accion'] === 'audio_acufeno_respuesta') {
                $p = $e['p'];
                if (($p['pregunta'] ?? '') === self::PREG_CUAL) {
                    $respuestasCual[] = $p;
                    $tPrimeraCual = $tPrimeraCual ?? $e['t'];
                } elseif (($p['pregunta'] ?? '') === self::PREG_COMO) {
                    $respuestasComo[] = $p;
                }
                continue;
            }
            $instr = $e['instruccion'];
            if ($instr === null) {
                continue;
            }
            foreach ([0, 1] as $c) {
                $canal = $e['canales'][$c];
                if (empty($canal['on'])) {
                    continue;
                }
                $muestras[$instr][] = [
                    't' => $e['t'],
                    'stim' => AudiometriaPaciente::estimulo((string) $canal['stim']),
                    'oido' => self::oido((string) $canal['output']),
                    'freq' => $e['freq'],
                    'int' => (int) $canal['int'],
                    'antes_de_cual' => $tPrimeraCual === null,
                ];
            }
            // solo con el estímulo sonando: ajustar el nivel de partida con
            // el tono apagado no es igualar
            $sonando = !empty($e['canales'][0]['on']) || !empty($e['canales'][1]['on']);
            if ($instr === self::SONORIDAD && $sonando && $e['accion'] === 'audio_intensity_change' && $e['step'] > self::PASO_FINO_DB) {
                $pasosGruesos[] = (int) $e['step'];
            }
            if ($instr === self::SONORIDAD && $e['mano']) {
                foreach ([0, 1] as $c) {
                    $canal = $e['canales'][$c];
                    $stim = AudiometriaPaciente::estimulo((string) $canal['stim']);
                    if (!empty($canal['on']) && (in_array($stim, self::DE_COMPARACION, true) || $stim === 'White Noise')) {
                        $igualo = ['int' => (int) $canal['int'], 'oido' => self::oido((string) $canal['output']),
                            'freq' => $e['freq'], 'stim' => $stim];
                    }
                }
            }
            if ($instr === self::NME && $e['mano'] && $nmeNivel === null) {
                foreach ([0, 1] as $c) {
                    $canal = $e['canales'][$c];
                    $stim = AudiometriaPaciente::estimulo((string) $canal['stim']);
                    if (!empty($canal['on']) && ($stim === 'Narrow Band Noise' || in_array($stim, self::DE_BANDA_ANCHA, true))) {
                        $nmeNivel = (int) $canal['int'];
                        $nmeOido = self::oido((string) $canal['output']);
                        $nmeFreq = in_array($stim, self::DE_BANDA_ANCHA, true) ? $fAcufeno : $e['freq'];
                    }
                }
            }
        }
        $comparacion = array_merge(
            array_values(array_filter($muestras[self::TONO], static function ($m) {
                return in_array($m['stim'], self::DE_COMPARACION, true);
            })),
            array_values(array_filter($muestras[self::SONORIDAD], static function ($m) {
                return in_array($m['stim'], self::DE_COMPARACION, true) || $m['stim'] === 'White Noise';
            }))
        );

        // ---- las cuatro partes ---------------------------------------------
        $partes = [
            'tono' => $respuestasCual !== [],
            'intensidad' => $muestras[self::SONORIDAD] !== [],
            'NME' => $muestras[self::NME] !== [],
            'inhibición residual' => $muestras[self::INHIBICION] !== [],
        ];
        $ldlTapa = false;
        if ($nmeNivel !== null) {
            foreach ($oidosAcufeno as $o) {
                $idx = self::idx($fAcufeno);
                if ($idx !== null && $nmeNivel + self::SOBRE_NME_DB >= (int) ($caso['LDL'][$idx][$o] ?? 999)) {
                    $ldlTapa = true;
                }
            }
        }
        $faltan = array_keys(array_filter($partes, static function ($h) { return !$h; }));
        if ($ldlTapa && !$partes['inhibición residual']) {
            $faltan = array_values(array_diff($faltan, ['inhibición residual']));
            $obs[] = 'El NME + 10 dB llegaba a la molestia del paciente: la inhibición residual no se hace, y se anota por qué.';
        }
        $reglas[] = [
            'texto' => 'Se hacen las cuatro partes: tono, intensidad, NME e inhibición residual.',
            'cumple' => $faltan === [],
            'detalle' => $faltan === [] ? 'Se hicieron todas.' : 'Faltó: ' . self::lista($faltan) . '.',
        ];

        // ---- oído de comparación -------------------------------------------
        if ($comparacion !== []) {
            $usados = array_values(array_unique(array_map(static function ($m) {
                return $m['oido'] === null ? 'los dos oídos' : self::OIDOS[$m['oido']];
            }, $comparacion)));
            $reglas[] = [
                'texto' => 'Los sonidos de comparación van al oído contrario al acúfeno (o al de acúfeno más débil).',
                'cumple' => $oidoComparacion === null ? null : count($usados) === 1 && $usados[0] === self::OIDOS[$oidoComparacion],
                'detalle' => 'Se comparó en ' . self::lista($usados) . '.',
            ];
        }

        // ---- tono ------------------------------------------------------------
        $elegida = self::elegida($respuestasCual);
        if ($partes['tono']) {
            $iniciales = array_values(array_unique(array_map(static function ($m) { return $m['freq']; },
                array_filter($muestras[self::TONO], static function ($m) { return $m['antes_de_cual']; }))));
            $reglas[] = [
                'texto' => 'Tono: se parte con tres estímulos de distinta frecuencia.',
                'cumple' => count($iniciales) >= 3,
                'detalle' => 'Antes de la primera pregunta: ' . (count($iniciales) ? self::lista(array_map([self::class, 'hz'], $iniciales)) : 'ninguno') . '.',
            ];
            if ($elegida !== null) {
                $presentadas = array_unique(array_map(static function ($m) { return $m['freq']; }, $muestras[self::TONO]));
                $faltaOct = [];
                foreach ([self::octavaArriba($elegida), intdiv($elegida, 2)] as $oct) {
                    if (self::idx($oct) !== null && !in_array($oct, $presentadas, true)) {
                        $faltaOct[] = self::hz($oct);
                    }
                }
                $reglas[] = [
                    'texto' => 'Control de octava: se presenta la frecuencia elegida una octava arriba y una abajo.',
                    'cumple' => $faltaOct === [],
                    'detalle' => 'Elegida: ' . self::hz($elegida) . '.' . ($faltaOct ? ' Faltó ' . self::lista($faltaOct) . '.' : ''),
                ];
            }
        }

        // ---- intensidad ------------------------------------------------------
        if ($partes['intensidad']) {
            $primera = $muestras[self::SONORIDAD][0];
            $idx = self::idx($primera['freq']);
            if ($primera['oido'] !== null && $idx !== null) {
                $umbral = $paciente->umbralReal('aerea', $idx, $primera['oido']);
                $reglas[] = [
                    'texto' => 'Intensidad: se parte bajo el umbral.',
                    'cumple' => $primera['int'] < $umbral,
                    'detalle' => 'Partió en ' . $primera['int'] . ' dB HL.',
                ];
            }
            $reglas[] = [
                'texto' => 'Intensidad: se sube de 1 en 1 dB hasta que suenen igual de fuerte.',
                'cumple' => $pasosGruesos === [],
                'detalle' => $pasosGruesos === [] ? 'Subió en pasos finos.'
                    : 'Usó pasos de ' . self::lista(array_map('strval', array_values(array_unique($pasosGruesos)))) . ' dB.',
            ];
            if ($elegida !== null) {
                $fs = array_values(array_unique(array_map(static function ($m) { return $m['freq']; }, $muestras[self::SONORIDAD])));
                $reglas[] = [
                    'texto' => 'Intensidad: con la frecuencia elegida.',
                    'cumple' => $fs === [$elegida],
                    'detalle' => 'Se igualó en ' . self::lista(array_map([self::class, 'hz'], $fs)) . '.',
                ];
            }
            // el resultado se informa en dB SL: el nivel igualado menos el
            // umbral del oído donde se igualó, a esa frecuencia
            $reglas[] = [
                'texto' => 'Intensidad: el paciente avisa que suena igual de fuerte, y se informa en dB SL.',
                'cumple' => $igualo !== null,
                'detalle' => $igualo === null ? 'El paciente no avisó que sonara igual de fuerte.'
                    : 'Igualó con ' . $igualo['int'] . ' dB HL en ' . self::donde($igualo['oido']) . ' a ' . self::hz($igualo['freq'])
                        . self::enSl($paciente, $igualo['int'], $igualo['oido'], $igualo['freq']) . '.',
            ];
        }

        // ---- NME -------------------------------------------------------------
        if ($partes['NME']) {
            $ruidos = array_values(array_filter($muestras[self::NME], static function ($m) {
                return $m['stim'] === 'Narrow Band Noise' || in_array($m['stim'], self::DE_BANDA_ANCHA, true);
            }));
            $centro = $elegida ?? $fAcufeno;
            $malos = [];
            foreach ($ruidos as $m) {
                $oidoBien = $m['oido'] === null || in_array($m['oido'], $oidosAcufeno, true);
                $ruidoBien = in_array($m['stim'], self::DE_BANDA_ANCHA, true)
                    || abs(log($m['freq'] / $centro, 2)) <= 0.5;
                if (!$oidoBien) {
                    $malos['oído'] = 'el ruido fue al oído sin acúfeno';
                }
                if (!$ruidoBien) {
                    $malos['banda'] = 'la banda estrecha no estaba centrada en la frecuencia elegida';
                }
            }
            // lo que sonó, por estímulo y oído, con el máximo al que llegó:
            // un tono, o el ruido en el oído sin acúfeno, no lo tapan
            $sono = [];
            foreach ($muestras[self::NME] as $m) {
                $k = $m['stim'] . ' en ' . self::donde($m['oido']);
                $sono[$k] = max($sono[$k] ?? -999, $m['int']);
            }
            $sonoTxt = self::lista(array_map(static function ($k, $max) {
                return $k . ' (hasta ' . $max . ' dB HL)';
            }, array_keys($sono), $sono));
            $reglas[] = [
                'texto' => 'NME: en el oído del acúfeno, con banda estrecha centrada en él o ruido blanco.',
                'cumple' => $ruidos === [] ? false : $malos === [],
                'detalle' => $ruidos === [] ? 'No se presentó ruido: sonó ' . $sonoTxt . ', y con eso el acúfeno no se tapa.'
                    : ($malos ? ucfirst(self::lista(array_values($malos))) . ': sonó ' . $sonoTxt . '.'
                        : 'Ruido en ' . self::lista(array_values(array_unique(array_map(static function ($m) {
                            return self::donde($m['oido']);
                        }, $ruidos)))) . '.'),
            ];
            if ($nmeNivel !== null) {
                $nmeDetalle = 'Lo dejó de oír con ' . $nmeNivel . ' dB HL en ' . self::donde($nmeOido)
                    . self::enSl($paciente, $nmeNivel, $nmeOido, (int) $nmeFreq) . '.';
            } elseif ($ruidos === [] || $malos !== []) {
                $nmeDetalle = 'El paciente no avisó que lo dejara de oír: el estímulo no podía taparlo (ver la regla anterior).';
            } else {
                $nmeDetalle = 'El paciente no avisó que lo dejara de oír: el ruido llegó hasta '
                    . max(array_map(static function ($m) { return $m['int']; }, $ruidos)) . ' dB HL y no alcanzó.';
            }
            $reglas[] = [
                'texto' => 'NME: se sube hasta que el paciente deja de oír su acúfeno, y se informa en dB SL.',
                'cumple' => $nmeNivel !== null,
                'detalle' => $nmeDetalle,
            ];
        }

        // ---- inhibición residual ---------------------------------------------
        if ($partes['inhibición residual']) {
            $ir = $muestras[self::INHIBICION];
            $centro = $elegida ?? $fAcufeno;
            $enOido = true;
            $octava = true;
            $maxInt = 0;
            $pasaLdl = false;
            foreach ($ir as $m) {
                if ($m['oido'] !== null && !in_array($m['oido'], $oidosAcufeno, true)) {
                    $enOido = false;
                }
                if (!in_array($m['stim'], self::DE_BANDA_ANCHA, true)
                        && abs(abs(log($m['freq'] / $centro, 2)) - 1) > 0.01) {
                    $octava = false;
                }
                $maxInt = max($maxInt, $m['int']);
                $idx = self::idx($m['freq']);
                foreach ($m['oido'] === null ? [0, 1] : [$m['oido']] as $o) {
                    if ($idx !== null && $m['int'] >= (int) ($caso['LDL'][$idx][$o] ?? 999)) {
                        $pasaLdl = true;
                    }
                }
            }
            $reglas[] = [
                'texto' => 'Inhibición residual: en el oído del acúfeno.',
                'cumple' => $enOido,
                'detalle' => $enOido ? 'Se presentó en el oído del acúfeno.' : 'Se presentó en el oído sin acúfeno.',
            ];
            $reglas[] = [
                'texto' => 'Inhibición residual: una octava arriba o abajo de la frecuencia del acúfeno.',
                'cumple' => $octava,
                'detalle' => 'Se usó ' . self::lista(array_map([self::class, 'hz'], array_values(array_unique(array_map(static function ($m) { return $m['freq']; }, $ir))))) . '.',
            ];
            $reglas[] = [
                'texto' => 'Inhibición residual: 10 dB sobre el NME.',
                'cumple' => $nmeNivel === null ? null : $maxInt >= $nmeNivel + self::SOBRE_NME_DB - self::SOBRE_NME_TOL_DB,
                'detalle' => $nmeNivel === null ? 'Sin NME medido no se puede comparar.' : 'NME ' . $nmeNivel . ' dB HL; estímulo hasta ' . $maxInt . ' dB HL.',
            ];
            $reglas[] = [
                'texto' => 'Inhibición residual: el estímulo no pasa la molestia del paciente.',
                'cumple' => !$pasaLdl,
                'detalle' => $pasaLdl ? 'El estímulo llegó a su nivel de molestia.' : 'Quedó bajo su molestia.',
            ];
            $corrida = null;
            foreach ($respuestasComo as $r) {
                if (is_array($r['corrida'] ?? null) && $r['corrida']['desde_s'] !== null) {
                    $corrida = $corrida ?? $r['corrida'];
                }
            }
            $reglas[] = [
                'texto' => 'Inhibición residual: el estímulo dura un minuto.',
                'cumple' => $corrida === null ? false : $corrida['duracion_s'] >= self::MINUTO_S,
                'detalle' => $corrida === null ? 'No se preguntó con el estímulo apagado.'
                    : 'Duró ' . AudiometriaTecnica::tiempo((float) $corrida['duracion_s']) . '.',
            ];
            $alApagar = $alMinuto = false;
            foreach ($respuestasComo as $r) {
                $desde = $r['corrida']['desde_s'] ?? null;
                if ($desde === null) {
                    continue;
                }
                if ($desde < 30) {
                    $alApagar = true;
                } elseif ($desde >= self::MINUTO_S) {
                    $alMinuto = true;
                }
            }
            $reglas[] = [
                'texto' => 'Inhibición residual: se pregunta al apagar el estímulo y otra vez un minuto después.',
                'cumple' => $alApagar && $alMinuto,
                'detalle' => $alApagar && $alMinuto ? 'Preguntó las dos veces.'
                    : ($alApagar ? 'Faltó preguntar al minuto.' : ($alMinuto ? 'Faltó preguntar al apagarlo.' : 'No preguntó con el estímulo apagado.')),
            ];
        }

        return ['reglas' => $reglas, 'observaciones' => $obs, 'hecha' => true];
    }

    /** La frecuencia que eligió el paciente en la última comparación. */
    private static function elegida(array $respuestas): ?int
    {
        for ($i = count($respuestas) - 1; $i >= 0; $i--) {
            $r = $respuestas[$i];
            $pos = self::ORDINALES[$r['respuesta'] ?? ''] ?? null;
            if ($pos !== null && isset($r['comparados'][$pos]['freq'])) {
                return (int) $r['comparados'][$pos]['freq'];
            }
        }
        return null;
    }

    /** Para casos sin la verdad en el registro (app anterior). */
    private static function oidosDelBloque(array $t): array
    {
        if (($t['lateralidad'] ?? 'craneal') === 'unilateral') {
            return [($t['oido'] ?? 'od') === 'oi' ? 1 : 0];
        }
        return [0, 1];
    }

    private static function comparacionDelBloque(array $t): ?int
    {
        $lat = $t['lateralidad'] ?? 'craneal';
        if ($lat === 'unilateral') {
            return ($t['oido'] ?? 'od') === 'oi' ? 0 : 1;
        }
        if ($lat === 'bilateral' && in_array($t['predominio'] ?? 'igual', ['od', 'oi'], true)) {
            return $t['predominio'] === 'od' ? 1 : 0;
        }
        return null;
    }

    private static function octavaArriba(int $hz): int
    {
        return $hz * 2;
    }

    private static function idx(int $hz): ?int
    {
        $i = array_search($hz, AudiometriaPaciente::FRECUENCIAS, true);
        return $i === false ? null : (int) $i;
    }

    private static function donde(?int $oido): string
    {
        return $oido === null ? 'los dos oídos' : self::OIDOS[$oido];
    }

    /**
     * ": N dB SL sobre el umbral de ese oído (U dB HL)", o '' si no se sabe
     * el oído o la frecuencia no está en el audiograma.
     */
    private static function enSl(AudiometriaPaciente $paciente, int $nivel, ?int $oido, int $hz): string
    {
        $idx = self::idx($hz);
        if ($oido === null || $idx === null) {
            return '';
        }
        $umbral = $paciente->umbralReal('aerea', $idx, $oido);
        return ': ' . ($nivel - $umbral) . ' dB SL sobre el umbral de ese oído (' . $umbral . ' dB HL)';
    }

    private static function oido(string $output): ?int
    {
        if ($output === 'Derecha') {
            return 0;
        }
        return $output === 'Izquierda' ? 1 : null;
    }

    public static function hz(int $hz): string
    {
        return AudiometriaTecnica::hz($hz);
    }

    private static function lista(array $items): string
    {
        if (count($items) <= 1) {
            return implode('', $items);
        }
        $ultimo = array_pop($items);
        return implode(', ', $items) . ' y ' . $ultimo;
    }
}
