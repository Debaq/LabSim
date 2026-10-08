<?php

declare(strict_types=1);

require_once __DIR__ . '/AudiometriaPaciente.php';

/**
 * Lee el examen del audiómetro desde action_logs: cada presentación de tono
 * con oído, vía, frecuencia, intensidad, ruido en el otro oído, instrucción
 * vigente, duración y si el paciente levantó la mano.
 *
 * Mixto (ver docs/decisiones.md, "Audiometría: leer el examen del alumno
 * desde el registro"):
 * - Registro v2 (payload con "v"): cada estímulo trae la foto del equipo y
 *   la mano viene en audio_respuesta. Se lee tal cual.
 * - Registro viejo: el estado se reconstruye repasando los eventos desde
 *   los valores con que abre el audiómetro, y la mano se recalcula con
 *   AudiometriaPaciente. La hora viene en segundos enteros, así que la
 *   duración no se mide. Queda marcado 'reconstruido'.
 */
final class AudiometriaRegistro
{
    /** Instrucciones del talkback por prueba (resources/json/command_voice.json). */
    public const INSTR_AEREA = ['colocar_fonos', 'aerea_+_ruido'];
    public const INSTR_OSEA = ['colocar_vibrador', 'vibrador_+_ruido'];
    public const INSTR_LOGO = ['escuche_mi_voz', 'dictar_palabras'];
    public const INSTR_SUPRA = [
        'pitos_fuertes', 'dos_pitos', 'cambie_de_volumen', 'mano_levantada',
        'mano_levantada_en_ruido', 'ruido_blanco_contralateral', 'rosemberg_bilateral',
        'sonidos_iguales', 'en_qué_oído',
    ];

    /**
     * $logs: filas de action_logs de UNA atención, en orden de id, ya con el
     * payload decodificado en 'payload' (array). Las que no son del
     * audiómetro se ignoran.
     *
     * Devuelve ['reconstruido' => bool, 'con_ms' => bool,
     *   'presentaciones' => [...], 'pruebas' => [[t, prueba], ...]].
     */
    public static function leer(array $logs, array $caso): array
    {
        $logs = array_values(array_filter($logs, static function ($l) {
            return strpos((string) $l['action'], 'audio_') === 0;
        }));
        $v2 = false;
        foreach ($logs as $l) {
            if (isset($l['payload']['v'])) {
                $v2 = true;
            }
        }
        $paciente = new AudiometriaPaciente($caso);

        $estado = [
            'prueba' => 'Umbrales',
            'freq' => 1000,
            'freq_idx' => 3,
            'instruccion' => null,
            'canales' => [
                ['on' => false, 'invertido' => false, 'int' => 20, 'stim' => 'Tono', 'output' => 'Derecha', 'trans' => 'Aerea'],
                ['on' => false, 'invertido' => false, 'int' => 20, 'stim' => 'Narrow Band Noise', 'output' => 'Izquierda', 'trans' => 'Aerea'],
            ],
        ];
        $mano = false;
        $abiertas = [null, null];
        $presentaciones = [];
        $pruebas = [];

        foreach ($logs as $l) {
            $p = $l['payload'] ?? [];
            $t = self::segundos((string) $l['client_ts']);
            // la duración solo se mide con milisegundos en las dos puntas
            $ms = (bool) preg_match('/\.\d{3}$/', (string) $l['client_ts']);
            $accion = (string) $l['action'];
            if (isset($p['estado']) && is_array($p['estado'])) {
                $estado = self::aplicarFoto($estado, $p['estado']);
            }
            $ch = isset($p['ch']) ? ((int) $p['ch'] === 1 ? 1 : 0) : null;
            $cambioEncendido = false;

            switch ($accion) {
                case 'audio_talkback_press':
                    $cmd = $p['command'] ?? null;
                    if ($cmd !== 'pa_pa_pa') {
                        $estado['instruccion'] = $cmd;
                    }
                    $fase = self::pruebaDeInstruccion($cmd);
                    if ($fase === 'logo' || $fase === 'supra') {
                        $pruebas[] = [$t, $fase];
                    }
                    break;
                case 'audio_stim_button':
                    if ($ch === null) {
                        break;
                    }
                    if (!isset($p['estado'])) {
                        // registro viejo: el estímulo trae su propio canal
                        $estado = self::aplicarCanal($estado, $ch, $p);
                        if (isset($p['freq'])) {
                            $estado = self::ponerFrecuencia($estado, (int) $p['freq']);
                        }
                    }
                    $estado['canales'][$ch]['on'] = (bool) ($p['play'] ?? false);
                    $cambioEncendido = true;
                    break;
                case 'audio_reverse_toggle':
                    if ($ch !== null) {
                        $inv = ($p['state'] ?? '') === 'Invertido';
                        $estado['canales'][$ch]['invertido'] = $inv;
                        $estado['canales'][$ch]['on'] = $inv;
                        $cambioEncendido = true;
                    }
                    break;
                case 'audio_intensity_change':
                    if ($ch !== null && isset($p['intensity'])) {
                        $estado['canales'][$ch]['int'] = (int) $p['intensity'];
                    }
                    break;
                case 'audio_freq_change':
                    if (isset($p['freq'])) {
                        $estado = self::ponerFrecuencia($estado, (int) $p['freq']);
                    }
                    break;
                case 'audio_output_select':
                    if ($ch !== null && isset($p['output'])) {
                        $estado['canales'][$ch]['output'] = (string) $p['output'];
                    }
                    break;
                case 'audio_trans_select':
                    if ($ch !== null && isset($p['trans'])) {
                        $estado['canales'][$ch]['trans'] = (string) $p['trans'];
                    }
                    break;
                case 'audio_stim_select':
                    if ($ch !== null && isset($p['stim'])) {
                        $estado['canales'][$ch]['stim'] = (string) $p['stim'];
                    }
                    break;
                case 'audio_prueba_change':
                    if (isset($p['prueba'])) {
                        $estado['prueba'] = (string) $p['prueba'];
                    }
                    break;
                case 'audio_respuesta':
                    $mano = (bool) ($p['mano'] ?? false);
                    foreach ([0, 1] as $c) {
                        if ($abiertas[$c] !== null && $mano) {
                            $presentaciones[$abiertas[$c]]['oyo'] = true;
                        }
                    }
                    break;
            }

            if (!$cambioEncendido) {
                continue;
            }
            if (!$v2) {
                $mano = $paciente->mano(self::estadoMotor($estado), $mano);
            }
            foreach ([0, 1] as $c) {
                $on = $estado['canales'][$c]['on'];
                if ($abiertas[$c] !== null && !$on) {
                    $i = $abiertas[$c];
                    $presentaciones[$i]['t_off'] = $t;
                    $presentaciones[$i]['duracion'] = $ms && $presentaciones[$i]['ms']
                        ? round($t - $presentaciones[$i]['t_on'], 3) : null;
                    $abiertas[$c] = null;
                } elseif ($abiertas[$c] === null && $on && self::esTono($estado['canales'][$c]['stim'])) {
                    $presentaciones[] = self::presentacion($estado, $c, $t, $mano) + ['ms' => $ms];
                    $abiertas[$c] = count($presentaciones) - 1;
                    $pruebas[] = [$t, $presentaciones[$abiertas[$c]]['prueba']];
                } elseif ($on && ($estado['canales'][$c]['stim'] === 'Habla')) {
                    $pruebas[] = [$t, 'logo'];
                }
            }
        }

        $conMs = false;
        foreach ($presentaciones as $x) {
            if ($x['duracion'] !== null) {
                $conMs = true;
            }
        }
        return [
            'reconstruido' => !$v2,
            'con_ms' => $conMs,
            'presentaciones' => $presentaciones,
            'pruebas' => $pruebas,
        ];
    }

    /** Una presentación nueva del tono del canal $c. */
    private static function presentacion(array $estado, int $c, float $t, ?bool $mano): array
    {
        $canal = $estado['canales'][$c];
        $otro = $estado['canales'][1 - $c];
        $ruido = null;
        if ($otro['on'] && in_array($otro['stim'], ['Narrow Band Noise', 'Withe Noise', 'Speech Noise', 'Pink Noise'], true)) {
            $ruido = ['int' => (int) $otro['int'], 'stim' => $otro['stim'], 'oido' => self::oido($otro['output'])];
        }
        $via = $canal['trans'] === 'Aerea' ? 'aerea' : ($canal['trans'] === 'Oséa' ? 'osea' : 'campo');
        return [
            't_on' => $t,
            't_off' => null,
            'duracion' => null,
            'canal' => $c,
            'oido' => self::oido($canal['output']),
            'via' => $via,
            'freq' => (int) $estado['freq'],
            'int' => (int) $canal['int'],
            'ruido' => $ruido,
            'instruccion' => $estado['instruccion'],
            'prueba' => self::pruebaDe($estado, $via),
            'oyo' => $mano,
        ];
    }

    /** A qué prueba de la audiometría pertenece un tono (T00). */
    private static function pruebaDe(array $estado, string $via): string
    {
        $porInstr = self::pruebaDeInstruccion($estado['instruccion']);
        if ($porInstr === 'supra' || $porInstr === 'logo') {
            return $porInstr;
        }
        if ($estado['prueba'] !== 'Umbrales') {
            return 'logo';
        }
        return $via === 'osea' ? 'oseos' : 'aereos';
    }

    public static function pruebaDeInstruccion(?string $cmd): ?string
    {
        if ($cmd === null) {
            return null;
        }
        if (in_array($cmd, self::INSTR_AEREA, true)) {
            return 'aereos';
        }
        if (in_array($cmd, self::INSTR_OSEA, true)) {
            return 'oseos';
        }
        if (in_array($cmd, self::INSTR_LOGO, true)) {
            return 'logo';
        }
        if (in_array($cmd, self::INSTR_SUPRA, true)) {
            return 'supra';
        }
        return null;
    }

    /** El estado en los índices que usa el motor del paciente. */
    private static function estadoMotor(array $estado): array
    {
        $canales = [];
        foreach ($estado['canales'] as $c) {
            $stim = array_search($c['stim'], AudiometriaPaciente::ESTIMULOS, true);
            $trans = array_search($c['trans'], AudiometriaPaciente::TRANSDUCTORES, true);
            $canales[] = [
                'on' => $c['on'],
                'int' => $c['int'],
                'output' => $c['output'] === 'Derecha' ? 0 : 1,
                'trans' => $trans === false ? 0 : $trans,
                'stim' => $stim === false ? 0 : $stim,
            ];
        }
        return [
            'prueba' => $estado['prueba'],
            'freq_idx' => $estado['freq_idx'],
            'instruccion' => $estado['instruccion'],
            'canales' => $canales,
        ];
    }

    /** La foto v2 (Audiometer._estado) pisa el estado reconstruido. */
    private static function aplicarFoto(array $estado, array $foto): array
    {
        if (isset($foto['prueba'])) {
            $estado['prueba'] = (string) $foto['prueba'];
        }
        if (isset($foto['freq'])) {
            $estado = self::ponerFrecuencia($estado, (int) $foto['freq']);
        }
        if (array_key_exists('instruccion', $foto)) {
            $estado['instruccion'] = $foto['instruccion'];
        }
        foreach ([0, 1] as $c) {
            $fc = $foto['canales'][$c] ?? null;
            if (!is_array($fc)) {
                continue;
            }
            $estado = self::aplicarCanal($estado, $c, $fc);
            $estado['canales'][$c]['on'] = (bool) ($fc['on'] ?? false);
            $estado['canales'][$c]['invertido'] = (bool) ($fc['invertido'] ?? false);
        }
        return $estado;
    }

    private static function aplicarCanal(array $estado, int $c, array $datos): array
    {
        if (isset($datos['intensity'])) {
            $estado['canales'][$c]['int'] = (int) $datos['intensity'];
        }
        foreach (['stim', 'output', 'trans'] as $k) {
            if (isset($datos[$k])) {
                $estado['canales'][$c][$k] = (string) $datos[$k];
            }
        }
        return $estado;
    }

    /** Una frecuencia fuera de la tabla del motor deja el índice anterior (como response.py). */
    private static function ponerFrecuencia(array $estado, int $hz): array
    {
        if ($hz <= 0) {
            return $estado;
        }
        $estado['freq'] = $hz;
        $idx = array_search($hz, AudiometriaPaciente::FRECUENCIAS, true);
        if ($idx !== false) {
            $estado['freq_idx'] = $idx;
        }
        return $estado;
    }

    private static function esTono(string $stim): bool
    {
        return $stim === 'Tono' || $stim === 'FM';
    }

    /** 0 derecho, 1 izquierdo, null simultáneo. */
    private static function oido(string $output): ?int
    {
        if ($output === 'Derecha') {
            return 0;
        }
        return $output === 'Izquierda' ? 1 : null;
    }

    /** client_ts a segundos, con los milisegundos si los trae. */
    public static function segundos(string $ts): float
    {
        $ms = 0.0;
        if (preg_match('/^(.*)\.(\d{1,6})$/', $ts, $m)) {
            $ts = $m[1];
            $ms = (float) ('0.' . $m[2]);
        }
        $base = strtotime($ts);
        return ($base === false ? 0.0 : (float) $base) + $ms;
    }
}
