<?php

declare(strict_types=1);

require_once __DIR__ . '/AudiometriaPaciente.php';
require_once __DIR__ . '/AudiometriaRegistro.php';

/**
 * Indicador "Pruebas que correspondían" (Bibliografia::TECNICAS T05): qué
 * pruebas de la audiometría pedía el audiograma del caso y si las que hizo
 * el alumno tenían con qué hacerse. La técnica de cada prueba (cómo se
 * hace) va en su propia sección; acá va el criterio clínico de elegirla.
 *
 * Tres tipos de situación, con pesos distintos:
 * - Indicada y no hecha: regla (descuenta). Logoaudiometría en toda
 *   audiometría; prueba de adaptación con una sensorioneural asimétrica;
 *   Stenger en el caso marcado con pérdida no orgánica.
 * - Hecha sin el requisito que la hace válida: regla (descuenta), porque
 *   el resultado no se puede interpretar. Fowler sin un oído normal y el
 *   otro 20 dB peor en esa frecuencia; Reger sin una frecuencia conservada
 *   y otra 20 a 40 dB peor en el mismo oído; Stenger sin 20 dB de
 *   diferencia entre oídos.
 * - Hecha sin necesidad: advertencia (no descuenta), como los óseos en un
 *   oído sano. SISI, Carhart, Rosemberg y STAT en un oído o frecuencia sin
 *   pérdida sensorioneural.
 *
 * El audiograma que manda es el que DA el paciente (Aerea_mkg/Osea_mkg): es
 * el que ve el alumno. En un caso Stenger es el que finge.
 *
 * Los detalles nombran oídos y frecuencias, nunca umbrales: los lee el
 * alumno. Los números van en 'detalle_docente'.
 */
final class AudiometriaPertinencia
{
    /** Instrucción del talkback -> supraliminar (resources/json/command_voice.json). */
    public const SUPRA = [
        'pitos_fuertes' => 'LDL',
        'dos_pitos' => 'Fowler',
        'sonidos_iguales' => 'Fowler',
        'cambie_de_volumen' => 'SISI',
        'mano_levantada' => 'Deterioro tonal',
        'rosemberg_bilateral' => 'Rosemberg bilateral',
        'ruido_blanco_contralateral' => 'STAT',
        'weber_audiometrico' => 'Weber audiométrico',
        'reger' => 'Reger',
    ];
    /** Las que buscan reclutamiento o adaptación: solo dicen algo con pérdida sensorioneural. */
    private const DE_COCLEA_O_NERVIO = ['SISI', 'Deterioro tonal', 'Rosemberg bilateral', 'STAT'];
    /** Las que buscan adaptación (sospecha retrococlear). */
    private const DE_ADAPTACION = ['Deterioro tonal', 'Rosemberg bilateral', 'STAT'];

    /** Diferencia entre oídos que pide el Fowler y el Stenger, y la mínima del Reger. */
    public const DIFERENCIA_DB = 20;
    /** Máxima diferencia entre las dos frecuencias del Reger. */
    public const REGER_MAX_DB = 40;
    /** Gap aéreo-óseo desde el que una pérdida tiene componente conductivo. */
    public const GAP_DB = 15;
    /** Asimetría que pide descartar lo retrococlear: en dos frecuencias seguidas de 500 a 4000 Hz. */
    public const ASIMETRIA_DB = 15;
    /** Índices de AudiometriaPaciente::FRECUENCIAS de 500 a 4000 Hz. */
    private const ASIMETRIA_IDX = [2, 3, 4, 5, 6];
    /** Promedio desde el que no hay logoaudiometría posible (cofosis o profunda bilateral). */
    public const SIN_LOGO_DB = 90;

    private const OIDOS = ['OD', 'OI'];

    /**
     * $registro: AudiometriaRegistro::leer(); $corte: dB HL hasta donde un
     * umbral aéreo es normal (parámetro 'oido_sano' del curso);
     * $aereosHechos: si el alumno tomó umbrales aéreos (sin audiometría no
     * se exige nada). Null si no hay nada que decir.
     */
    public static function evaluar(array $registro, array $caso, int $corte, bool $aereosHechos): ?array
    {
        $paciente = new AudiometriaPaciente($caso);
        $hechas = self::supraHechas($registro['presentaciones']);
        $logo = false;
        foreach ($registro['pruebas'] as [, $prueba]) {
            if ($prueba === 'logo') {
                $logo = true;
            }
        }
        $stengerCaso = array_map('boolval', array_values((array) ($caso['Stenger'] ?? [false, false])) + [false, false]);
        $simulado = ($stengerCaso[0] xor $stengerCaso[1]);

        $reglas = [];
        $obs = [];

        // ---- indicadas ------------------------------------------------------
        if ($aereosHechos) {
            $pta = [self::pta($paciente, 0), self::pta($paciente, 1)];
            if (min($pta) >= self::SIN_LOGO_DB) {
                if ($logo) {
                    $obs[] = 'Con una pérdida profunda en los dos oídos la logoaudiometría no da resultado: no hacía falta.';
                }
            } else {
                $reglas[] = [
                    'texto' => 'Toda audiometría lleva logoaudiometría.',
                    'cumple' => $logo,
                    'detalle' => $logo ? 'Se hizo.' : 'No se hizo.',
                ];
            }

            $asim = $simulado ? null : self::asimetriaSensorioneural($paciente, $corte);
            if ($asim !== null) {
                $adapt = array_values(array_intersect(self::DE_ADAPTACION, array_keys($hechas)));
                $reglas[] = [
                    'texto' => 'Con una pérdida sensorioneural asimétrica se busca adaptación (Carhart, Rosemberg o STAT).',
                    'cumple' => $adapt !== [],
                    'detalle' => $adapt !== [] ? 'Se hizo ' . self::lista($adapt) . '.' : 'No se hizo ninguna prueba de adaptación.',
                    'detalle_docente' => sprintf('%s peor en %s.', self::OIDOS[$asim['oido']],
                        self::lista(array_map([self::class, 'hz'], $asim['freqs']))),
                ];
            }

            if ($simulado) {
                $hizo = isset($hechas['Stenger']);
                $reglas[] = [
                    'texto' => 'Con una pérdida unilateral que no calza con el resto del examen se hace el Stenger.',
                    'cumple' => $hizo,
                    'detalle' => $hizo ? 'Se hizo.' : 'No se hizo.',
                    'detalle_docente' => 'Caso marcado con pérdida no orgánica en ' . self::OIDOS[$stengerCaso[0] ? 0 : 1] . '.',
                ];
            }
        }

        // ---- requisitos de las que se hicieron --------------------------------
        if (isset($hechas['Fowler'])) {
            $malas = [];
            $numeros = [];
            foreach (array_keys(self::freqsDe($hechas['Fowler'])) as $hz) {
                $f = self::idx($hz);
                if ($f === null) {
                    continue;
                }
                $a = [$paciente->umbralReal('aerea', $f, 0), $paciente->umbralReal('aerea', $f, 1)];
                if (!(min($a) <= $corte && abs($a[0] - $a[1]) >= self::DIFERENCIA_DB)) {
                    $malas[] = self::hz($hz);
                    $numeros[] = sprintf('%s: OD %d, OI %d dB', self::hz($hz), $a[0], $a[1]);
                }
            }
            $reglas[] = [
                'texto' => sprintf('El Fowler se hace en una frecuencia con un oído normal y el otro al menos %d dB peor.', self::DIFERENCIA_DB),
                'cumple' => $malas === [],
                'detalle' => $malas === [] ? 'Las frecuencias elegidas lo cumplen.'
                    : 'No lo cumple en ' . self::lista($malas) . ': ahí el balance no tiene un oído de referencia.',
                'detalle_docente' => implode('; ', $numeros),
            ];
        }

        if (isset($hechas['Reger'])) {
            $malos = [];
            $numeros = [];
            foreach ($hechas['Reger'] as $o => $freqs) {
                $niveles = [];
                foreach (array_keys($freqs) as $hz) {
                    $f = self::idx($hz);
                    if ($f !== null) {
                        $niveles[$hz] = $paciente->umbralReal('aerea', $f, $o);
                    }
                }
                $ok = false;
                foreach ($niveles as $ref) {
                    foreach ($niveles as $pat) {
                        $d = $pat - $ref;
                        if ($ref <= $corte && $pat > $corte && $d >= self::DIFERENCIA_DB && $d <= self::REGER_MAX_DB) {
                            $ok = true;
                        }
                    }
                }
                if (!$ok) {
                    $malos[] = self::OIDOS[$o];
                    $numeros[] = self::OIDOS[$o] . ': ' . implode(', ', array_map(static function ($hz, $db) {
                        return self::hz($hz) . ' ' . $db . ' dB';
                    }, array_keys($niveles), $niveles));
                }
            }
            $reglas[] = [
                'texto' => sprintf('El Reger compara en el mismo oído una frecuencia normal con otra entre %d y %d dB peor.',
                    self::DIFERENCIA_DB, self::REGER_MAX_DB),
                'cumple' => $malos === [],
                'detalle' => $malos === [] ? 'Las frecuencias elegidas lo cumplen.'
                    : 'No lo cumple en ' . self::lista($malos) . '.',
                'detalle_docente' => implode('; ', $numeros),
            ];
        }

        if (isset($hechas['Stenger'])) {
            $malas = [];
            $numeros = [];
            foreach (array_keys(self::freqsDe($hechas['Stenger'])) as $hz) {
                $f = self::idx($hz);
                if ($f === null) {
                    continue;
                }
                $a = [$paciente->umbralReal('aerea', $f, 0), $paciente->umbralReal('aerea', $f, 1)];
                if (abs($a[0] - $a[1]) < self::DIFERENCIA_DB) {
                    $malas[] = self::hz($hz);
                    $numeros[] = sprintf('%s: OD %d, OI %d dB', self::hz($hz), $a[0], $a[1]);
                }
            }
            $reglas[] = [
                'texto' => sprintf('El Stenger se hace en una frecuencia con al menos %d dB de diferencia entre oídos.', self::DIFERENCIA_DB),
                'cumple' => $malas === [],
                'detalle' => $malas === [] ? 'Las frecuencias elegidas lo cumplen.'
                    : 'No lo cumple en ' . self::lista($malas) . ': con oídos parejos el Stenger no dice nada.',
                'detalle_docente' => implode('; ', $numeros),
            ];
        }

        // ---- hechas sin necesidad ---------------------------------------------
        foreach (self::DE_COCLEA_O_NERVIO as $prueba) {
            if (!isset($hechas[$prueba])) {
                continue;
            }
            $sin = [];
            foreach ($hechas[$prueba] as $o => $freqs) {
                foreach (array_keys($freqs) as $hz) {
                    $f = self::idx($hz);
                    if ($f !== null && !self::sensorioneural($paciente, $f, $o, $corte)) {
                        $sin[] = self::OIDOS[$o] . ' ' . self::hz($hz);
                    }
                }
            }
            if ($sin) {
                $obs[] = sprintf('%s en %s, sin pérdida sensorioneural ahí: no aporta.', self::nombre($prueba), self::lista($sin));
            }
        }

        if ($reglas === [] && $obs === []) {
            return null;
        }
        return ['reglas' => $reglas, 'observaciones' => $obs, 'hechas' => array_map([self::class, 'nombre'], array_keys($hechas))];
    }

    /**
     * Supraliminares hechas: prueba => oído => frecuencia => true. El
     * Stenger se reconoce porque es supraliminar con la instrucción de los
     * umbrales aéreos (AudiometriaRegistro::esStenger).
     *
     * @return array<string,array<int,array<int,bool>>>
     */
    public static function supraHechas(array $presentaciones): array
    {
        $out = [];
        foreach ($presentaciones as $x) {
            if ($x['prueba'] !== 'supra' || $x['oido'] === null) {
                continue;
            }
            $instr = (string) $x['instruccion'];
            if (isset(self::SUPRA[$instr])) {
                $prueba = self::SUPRA[$instr];
            } elseif (in_array($instr, AudiometriaRegistro::INSTR_AEREA, true) || $instr === '') {
                $prueba = 'Stenger';
            } else {
                continue;
            }
            $out[$prueba][(int) $x['oido']][(int) $x['freq']] = true;
        }
        return $out;
    }

    /**
     * Pérdida sensorioneural asimétrica: el mismo oído peor por al menos
     * ASIMETRIA_DB en dos frecuencias seguidas de 500 a 4000 Hz, con
     * componente sensorioneural en esas frecuencias. Null si no hay.
     *
     * @return array{oido:int, freqs:array<int,int>}|null
     */
    public static function asimetriaSensorioneural(AudiometriaPaciente $paciente, int $corte): ?array
    {
        foreach ([0, 1] as $peor) {
            $racha = [];
            $mejorRacha = [];
            foreach (self::ASIMETRIA_IDX as $f) {
                $d = $paciente->umbralReal('aerea', $f, $peor) - $paciente->umbralReal('aerea', $f, 1 - $peor);
                if ($d >= self::ASIMETRIA_DB && self::sensorioneural($paciente, $f, $peor, $corte)) {
                    $racha[] = AudiometriaPaciente::FRECUENCIAS[$f];
                    if (count($racha) > count($mejorRacha)) {
                        $mejorRacha = $racha;
                    }
                } else {
                    $racha = [];
                }
            }
            if (count($mejorRacha) >= 2) {
                return ['oido' => $peor, 'freqs' => $mejorRacha];
            }
        }
        return null;
    }

    /** Hay pérdida y no es solo conductiva: la vía ósea también cayó, o el gap es chico. */
    private static function sensorioneural(AudiometriaPaciente $paciente, int $f, int $o, int $corte): bool
    {
        $a = $paciente->umbralReal('aerea', $f, $o);
        $b = $paciente->umbralReal('osea', $f, $o);
        return $a > $corte && ($b > $corte || $a - $b < self::GAP_DB);
    }

    /** Promedio aéreo 500-1000-2000-4000 Hz. */
    private static function pta(AudiometriaPaciente $paciente, int $o): float
    {
        $s = 0;
        foreach ([2, 3, 4, 6] as $f) {
            $s += $paciente->umbralReal('aerea', $f, $o);
        }
        return $s / 4;
    }

    /** @param array<int,array<int,bool>> $porOido */
    private static function freqsDe(array $porOido): array
    {
        $out = [];
        foreach ($porOido as $freqs) {
            $out += $freqs;
        }
        ksort($out);
        return $out;
    }

    private static function nombre(string $prueba): string
    {
        return $prueba === 'Deterioro tonal' ? 'Deterioro tonal (Carhart o Rosemberg)' : $prueba;
    }

    private static function idx(int $hz): ?int
    {
        $i = array_search($hz, AudiometriaPaciente::FRECUENCIAS, true);
        return $i === false ? null : (int) $i;
    }

    private static function hz(int $hz): string
    {
        return $hz >= 1000 ? rtrim(rtrim(number_format($hz / 1000, 1, ',', ''), '0'), ',') . ' kHz' : $hz . ' Hz';
    }

    private static function lista(array $items): string
    {
        $items = array_values($items);
        if (count($items) <= 1) {
            return implode('', $items);
        }
        $ultimo = array_pop($items);
        return implode(', ', $items) . ' y ' . $ultimo;
    }
}
