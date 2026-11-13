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
    /**
     * NME con la mano ("Hasta que no escuche su ruido"): salió de la app el
     * 2026-11-13; queda para leer las atenciones anteriores. Desde ese día
     * el NME es "Solo escuche el mío": el nivel en que el paciente dice
     * "ahora solo escucho el suyo".
     */
    private const NME = 'acufeno_deje_de_escuchar';
    private const SOLO_EL_MIO = 'acufeno_solo_el_mio';
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
    /**
     * El estímulo de la inhibición: 15 dB sobre el nivel en que el paciente
     * dijo "ahora solo escucho el suyo", con 2 dB de holgura hacia abajo.
     */
    private const SOBRE_REF_DB = 15;
    private const SOBRE_REF_TOL_DB = 2;
    private const SOLO_EL_SUYO = 'ahorasoloescuchoelsuyo';

    /** Lo que contesta el paciente a "¿Cómo está su ruido?" -> inhibición residual. */
    private const INHIBICION_DE = ['igualqueantes' => 'negativa', 'seescuchamasbajito' => 'parcial', 'yanoloescucho' => 'total'];

    /**
     * $tin: AudiometriaRegistro::leer()['tinnitus']; $umbralesAlumno: los
     * umbrales aéreos que obtuvo el alumno (AudiometriaTecnica, sección
     * 'aereos' -> 'umbrales'), para pasar a dB SL como lo haría él.
     * Devuelve la sección ('reglas', 'observaciones', 'hecha', 'resultado')
     * o null si no hay nada que decir (sin acúfeno y sin tinnitumetría).
     *
     * 'resultado': el alumno anota la tinnitumetría por escrito, y eso no
     * llega acá. Se deduce lo que debería haber anotado según lo que le
     * contestó el paciente (con su propio umbral para el SL), y al lado lo
     * que tenía el paciente: el docente compara con lo escrito.
     */
    public static function evaluar(array $tin, array $caso, array $umbralesAlumno = []): ?array
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
        $ref = null;            // donde dijo "ahora solo escucho el suyo"
        $pidioSoloElMio = false;
        $dijoUnMinuto = false;
        foreach ($eventos as $e) {
            if ($e['accion'] === 'audio_acufeno_respuesta') {
                $p = $e['p'];
                if (($p['pregunta'] ?? '') === self::PREG_CUAL) {
                    $respuestasCual[] = $p;
                    $tPrimeraCual = $tPrimeraCual ?? $e['t'];
                } elseif (($p['pregunta'] ?? '') === self::PREG_COMO) {
                    $respuestasComo[] = $p;
                } elseif (($p['pregunta'] ?? '') === self::SOLO_EL_MIO && ($p['respuesta'] ?? '') === self::SOLO_EL_SUYO) {
                    // la última vez que lo dijo: si el alumno repite el
                    // paso, vale el nivel de la que siguió
                    $ref = self::nivelInhibicion($e, $fAcufeno) ?? $ref;
                }
                continue;
            }
            $instr = $e['instruccion'];
            if ($instr === null) {
                continue;
            }
            if ($instr === self::INHIBICION) {
                $dijoUnMinuto = true;
            }
            if ($instr === self::SOLO_EL_MIO) {
                // lo que suena va con la inhibición residual: es el mismo
                // estímulo, que después se sube 15 dB
                $pidioSoloElMio = true;
                $instr = self::INHIBICION;
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

        // NME: con la instrucción vieja, la mano; si no, "solo escuche el
        // mío" (el nivel en que dijo "ahora solo escucho el suyo")
        $nmeViejo = $muestras[self::NME] !== [];
        if (!$nmeViejo && $ref !== null) {
            $nmeNivel = $ref['int'];
            $nmeOido = $ref['oido'];
            $nmeFreq = (int) $ref['freq'];
        }
        // la inhibición residual es lo que sigue al NME: subir, el minuto y
        // las preguntas
        $despuesDelNme = $ref === null ? [] : array_values(array_filter($muestras[self::INHIBICION],
            static function ($m) use ($ref) { return $m['t'] > $ref['t']; }));
        $inhibicionHecha = $nmeViejo ? $muestras[self::INHIBICION] !== []
            : ($dijoUnMinuto || $respuestasComo !== [] || $despuesDelNme !== []);

        // ---- las cuatro partes ---------------------------------------------
        $partes = [
            'tono' => $respuestasCual !== [],
            'intensidad' => $muestras[self::SONORIDAD] !== [],
            'NME' => $nmeViejo || $pidioSoloElMio,
            'inhibición residual' => $inhibicionHecha,
        ];
        // si no cabe bajo la molestia, la inhibición no se hace: 15 dB sobre
        // el nivel en que dijo "solo escucho el suyo" o, si no se llegó a
        // eso, sobre el NME llevado a la octava de abajo con el mismo SL
        // (el paciente deja de oírlo al mismo SL en las dos)
        $ldlTapa = false;
        $niveles = [];   // [oído, Hz, dB HL donde solo escucharía el estímulo]
        if ($ref !== null) {
            foreach ($ref['oido'] === null ? $oidosAcufeno : [$ref['oido']] as $o) {
                $niveles[] = [$o, (int) $ref['freq'], $ref['int']];
            }
        } elseif ($nmeNivel !== null && $nmeOido !== null && self::idx((int) $nmeFreq) !== null) {
            $sl = $nmeNivel - $paciente->umbralReal('aerea', self::idx((int) $nmeFreq), $nmeOido);
            $fIr = self::octavaAbajo($fAcufeno) ?? self::octavaArriba($fAcufeno);
            if (self::idx($fIr) !== null) {
                foreach ($oidosAcufeno as $o) {
                    $niveles[] = [$o, $fIr, $paciente->umbralReal('aerea', self::idx($fIr), $o) + $sl];
                }
            }
        }
        foreach ($niveles as [$o, $hz, $nivel]) {
            $idx = self::idx($hz);
            if ($idx !== null && $nivel + self::SOBRE_REF_DB >= (int) ($caso['LDL'][$idx][$o] ?? 999)) {
                $ldlTapa = true;
            }
        }
        $faltan = array_keys(array_filter($partes, static function ($h) { return !$h; }));
        if ($ldlTapa && !$partes['inhibición residual']) {
            $faltan = array_values(array_diff($faltan, ['inhibición residual']));
            $obs[] = 'Subir 15 dB llegaba a la molestia del paciente: la inhibición residual no se hace, y se anota por qué.';
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
        if ($partes['NME'] && !$nmeViejo) {
            if ($ref !== null) {
                $nmeDetalle = 'Solo escuchó el estímulo con ' . $ref['int'] . ' dB HL en ' . self::donde($ref['oido'])
                    . ' a ' . self::hz((int) $ref['freq'])
                    . self::enSl($paciente, $ref['int'], $ref['oido'], (int) $ref['freq']) . '.';
            } else {
                $sono = [];
                foreach ($muestras[self::INHIBICION] as $m) {
                    $k = $m['stim'] . ' de ' . self::hz((int) $m['freq']) . ' en ' . self::donde($m['oido']);
                    $sono[$k] = max($sono[$k] ?? -999, $m['int']);
                }
                $nmeDetalle = 'El paciente no dijo que solo escuchara el estímulo'
                    . ($sono === [] ? '.' : ': sonó ' . self::lista(array_map(static function ($k, $max) {
                        return $k . ' (hasta ' . $max . ' dB HL)';
                    }, array_keys($sono), $sono)) . '; tiene que ir al oído del acúfeno, a una octava o menos de él.');
            }
            $reglas[] = [
                'texto' => 'NME: con "Solo escuche el mío", se sube hasta que el paciente solo escucha el estímulo, y se informa en dB SL.',
                'cumple' => $ref !== null,
                'detalle' => $nmeDetalle,
            ];
        }
        if ($partes['NME'] && $nmeViejo) {
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
            // una octava abajo; si el audiómetro no la tiene (acúfeno de
            // 125 Hz), una arriba
            $objetivo = self::octavaAbajo($centro) ?? self::octavaArriba($centro);
            $enOido = true;
            $octava = true;
            $pasaLdl = false;
            foreach ($ir as $m) {
                if ($m['oido'] !== null && !in_array($m['oido'], $oidosAcufeno, true)) {
                    $enOido = false;
                }
                if (!in_array($m['stim'], self::DE_BANDA_ANCHA, true) && $m['freq'] !== $objetivo) {
                    $octava = false;
                }
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
                'texto' => 'Inhibición residual: una octava abajo de la frecuencia del acúfeno.',
                'cumple' => $octava,
                'detalle' => 'Se usó ' . self::lista(array_map([self::class, 'hz'], array_values(array_unique(array_map(static function ($m) { return $m['freq']; }, $ir))))) . '.',
            ];
            if ($ref !== null) {
                $refDetalle = 'Dijo "ahora solo escucho el suyo" con ' . $ref['int'] . ' dB HL en ' . self::donde($ref['oido'])
                    . ' a ' . self::hz((int) $ref['freq']) . '.';
            } elseif ($pidioSoloElMio) {
                $refDetalle = 'Se pidió, pero el paciente no dijo que solo escuchara el estímulo.';
            } else {
                $refDetalle = 'No se pidió: se pasó directo al minuto.';
            }
            if ($nmeViejo) {
                // sin la NME vieja, este paso es la regla del NME
                $reglas[] = [
                    'texto' => 'Inhibición residual: se parte con "avíseme cuando solo escuche el mío y no el suyo", subiendo hasta que el paciente solo escucha el estímulo.',
                    'cumple' => $ref !== null,
                    'detalle' => $refDetalle,
                ];
            }
            // lo más alto que sonó después de que lo dijo: el minuto
            $despues = $ref === null ? [] : array_values(array_filter($ir, static function ($m) use ($ref) {
                return $m['t'] >= $ref['t'];
            }));
            $maxInt = $despues === [] ? null : max(array_map(static function ($m) { return $m['int']; }, $despues));
            $reglas[] = [
                'texto' => 'Inhibición residual: se sube 15 dB desde ese nivel.',
                'cumple' => $ref === null ? null : $maxInt !== null && $maxInt >= $ref['int'] + self::SOBRE_REF_DB - self::SOBRE_REF_TOL_DB,
                'detalle' => $ref === null ? 'Sin ese nivel no se puede comparar.'
                    : 'Solo el estímulo con ' . $ref['int'] . ' dB HL; después llegó a ' . ($maxInt ?? $ref['int']) . ' dB HL.',
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

        $resultado = self::resultado($verdad, $paciente, $umbralesAlumno, $respuestasCual, $igualo,
            $nmeNivel, $nmeOido, $nmeFreq, $respuestasComo, $oidoComparacion, $oidosAcufeno);
        return ['reglas' => $reglas, 'observaciones' => $obs, 'hecha' => true, 'resultado' => $resultado];
    }

    /**
     * Filas ['parte', 'anotar', 'paciente']: lo que el alumno debería haber
     * anotado según las respuestas del paciente, y lo del caso.
     */
    private static function resultado(?array $verdad, AudiometriaPaciente $paciente, array $umbralesAlumno,
        array $respuestasCual, ?array $igualo, ?int $nmeNivel, ?int $nmeOido, ?int $nmeFreq,
        array $respuestasComo, ?int $oidoComparacion, array $oidosAcufeno): array
    {
        $v = $verdad ?? [];
        $filas = [];

        // tono: la última elección del paciente, con el tipo de estímulo
        $tono = 'El paciente no eligió ningún estímulo.';
        for ($i = count($respuestasCual) - 1; $i >= 0; $i--) {
            $r = $respuestasCual[$i];
            $pos = self::ORDINALES[$r['respuesta'] ?? ''] ?? null;
            if ($pos !== null && isset($r['comparados'][$pos]['freq'])) {
                $c = $r['comparados'][$pos];
                $tono = self::nombreEstimulo((string) ($c['stim'] ?? 'Tono')) . ' de ' . self::hz((int) $c['freq']);
                break;
            }
        }
        $filas[] = ['parte' => 'Tono', 'anotar' => $tono,
            'paciente' => isset($v['freq']) ? (($v['tipo'] ?? 'tono') === 'ruido' ? 'Ruido de banda estrecha' : 'Tono puro')
                . ' de ' . self::hz((int) $v['freq']) : '—'];

        // intensidad y NME: el nivel, y el SL con el umbral que obtuvo el alumno
        $filas[] = ['parte' => 'Intensidad',
            'anotar' => $igualo === null ? 'El paciente no avisó que sonara igual de fuerte.'
                : self::nivelSl($igualo["int"], $igualo["oido"], (int) $igualo["freq"], $umbralesAlumno, $paciente),
            'paciente' => isset($v['sonoridad_sl'])
                ? self::slPaciente((int) $v['sonoridad_sl'], $oidoComparacion, (int) ($v['freq'] ?? 0), $paciente) : '—'];
        $filas[] = ['parte' => 'NME',
            'anotar' => $nmeNivel === null ? 'El paciente no avisó que lo dejara de oír: no hay NME.'
                : self::nivelSl($nmeNivel, $nmeOido, (int) $nmeFreq, $umbralesAlumno, $paciente),
            'paciente' => isset($v['nme_sl'])
                ? self::slPaciente((int) $v['nme_sl'], count($oidosAcufeno) === 1 ? $oidosAcufeno[0] : null, (int) ($v['freq'] ?? 0), $paciente) : '—'];

        // inhibición residual: lo que dijo al apagar y al minuto
        $alApagar = $alMinuto = null;
        $dur = null;
        foreach ($respuestasComo as $r) {
            $desde = $r['corrida']['desde_s'] ?? null;
            if ($desde === null) {
                continue;
            }
            $dur = $dur ?? (float) $r['corrida']['duracion_s'];
            if ($desde < 30) {
                $alApagar = $alApagar ?? ($r['respuesta'] ?? null);
            } elseif ($desde >= self::MINUTO_S) {
                $alMinuto = $alMinuto ?? ($r['respuesta'] ?? null);
            }
        }
        if ($alApagar === null) {
            $ir = 'No preguntó con el estímulo recién apagado: no hay inhibición residual.';
        } else {
            $ir = ucfirst(self::INHIBICION_DE[$alApagar] ?? '—');
            if ($alMinuto !== null && $alApagar !== 'igualqueantes') {
                $ir .= ($alMinuto === $alApagar ? ', se mantiene al minuto' : ', no se mantiene al minuto');
            }
            if ($dur !== null && $dur < self::MINUTO_S) {
                $ir .= ' (el estímulo duró ' . AudiometriaTecnica::tiempo($dur) . ': con menos de un minuto no vale)';
            }
            $ir .= '.';
        }
        $irPaciente = '—';
        if (isset($v['inhibicion'])) {
            $irPaciente = ucfirst($v['inhibicion']);
            if ($v['inhibicion'] !== 'negativa') {
                $irPaciente .= !empty($v['mantiene']) ? ', se mantiene al minuto' : ', no se mantiene al minuto';
            }
        }
        $filas[] = ['parte' => 'Inhibición residual', 'anotar' => $ir, 'paciente' => $irPaciente];
        return $filas;
    }

    private static function nombreEstimulo(string $stim): string
    {
        $stim = AudiometriaPaciente::estimulo($stim);
        $nombres = ['Tono' => 'Tono puro', 'FM' => 'Tono FM', 'Narrow Band Noise' => 'Ruido de banda estrecha',
            'White Noise' => 'Ruido blanco'];
        return $nombres[$stim] ?? $stim;
    }

    /** "30 dB HL en OI → 10 dB SL (su umbral: 20 dB HL)". */
    private static function nivelSl(int $nivel, ?int $oido, int $hz, array $umbralesAlumno, AudiometriaPaciente $paciente): string
    {
        $txt = $nivel . ' dB HL en ' . self::donde($oido) . ' a ' . self::hz($hz);
        if ($oido === null) {
            return $txt . '.';
        }
        $umbral = self::umbralAlumno($umbralesAlumno, $oido, $hz);
        if ($umbral === null) {
            // sin umbral propio: el que habría encontrado, avisando que no lo tomó
            $idx = self::idx($hz);
            if ($idx === null) {
                return $txt . '.';
            }
            $real = $paciente->umbralReal('aerea', $idx, $oido);
            return $txt . ' → ' . ($nivel - $real) . ' dB SL con el umbral de ' . self::OIDOS[$oido] . ' en ' . self::hz($hz)
                . ' (' . $real . ' dB HL), que no terminó de tomar en esta atención.';
        }
        return $txt . ' → ' . ($nivel - $umbral) . ' dB SL (su umbral: ' . $umbral . ' dB HL).';
    }

    /** "7 dB SL (27 dB HL en OI)": el SL del caso y a qué nivel cae en ese oído. */
    private static function slPaciente(int $sl, ?int $oido, int $hz, AudiometriaPaciente $paciente): string
    {
        $idx = self::idx($hz);
        if ($oido === null || $idx === null) {
            return $sl . ' dB SL.';
        }
        return $sl . ' dB SL (' . ($paciente->umbralReal('aerea', $idx, $oido) + $sl) . ' dB HL en ' . self::OIDOS[$oido] . ').';
    }

    /** El último umbral que obtuvo el alumno en ese oído y frecuencia, o null. */
    private static function umbralAlumno(array $umbrales, int $oido, int $hz): ?int
    {
        $u = null;
        foreach ($umbrales[self::OIDOS[$oido]] ?? [] as $f) {
            if ((int) $f['freq'] === $hz && ($f['estimado'] ?? null) !== null) {
                $u = (int) $f['estimado'];
            }
        }
        return $u;
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

    /** La octava de abajo, o null si el audiómetro no la tiene. */
    private static function octavaAbajo(int $hz): ?int
    {
        return $hz % 2 === 0 && self::idx(intdiv($hz, 2)) !== null ? intdiv($hz, 2) : null;
    }

    /**
     * ['t', 'int', 'oido', 'freq'] del estímulo de la inhibición en el
     * evento (el más fuerte que sonaba), o null si no sonaba ninguno.
     */
    private static function nivelInhibicion(array $e, int $fAcufeno): ?array
    {
        $mejor = null;
        foreach ([0, 1] as $c) {
            $canal = $e['canales'][$c];
            $stim = AudiometriaPaciente::estimulo((string) $canal['stim']);
            $sirve = in_array($stim, self::DE_COMPARACION, true) || in_array($stim, self::DE_BANDA_ANCHA, true);
            if (empty($canal['on']) || !$sirve || ($mejor !== null && (int) $canal['int'] <= $mejor['int'])) {
                continue;
            }
            $mejor = ['t' => $e['t'], 'int' => (int) $canal['int'], 'oido' => self::oido((string) $canal['output']),
                'freq' => in_array($stim, self::DE_BANDA_ANCHA, true) ? $fAcufeno : $e['freq']];
        }
        return $mejor;
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
