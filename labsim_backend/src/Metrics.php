<?php

final class Metrics
{
    /**
     * Nombre técnico (el que manda Audiometer.py/_log, Z.py/_log, ver
     * src/*.py del cliente) -> etiqueta en español para el panel admin.
     * Un docente no sabe qué es "audio_intensity_change". Si aparece una
     * acción nueva que no está acá, actionLabel() humaniza el nombre
     * técnico en vez de romper -- no hace falta tocar este archivo para
     * que la página siga funcionando, solo para que se vea prolijo.
     */
    private const ACTION_LABELS = [
        // Audiómetro
        'audio_intensity_change' => 'Cambio de intensidad (dB)',
        'audio_freq_change' => 'Cambio de frecuencia (Hz)',
        'audio_stim_select' => 'Selección de estímulo (tono/ruido)',
        'audio_output_select' => 'Selección de salida (audífono/vibrador/altavoz)',
        'audio_trans_select' => 'Selección de transductor',
        'audio_reverse_toggle' => 'Inversión de canal (reverse)',
        'audio_pulsatil_toggle' => 'Alternar tono pulsátil/continuo',
        'audio_alternate_toggle' => 'Alternar tono alternado',
        'audio_high_frec_toggle' => 'Alternar rango de alta frecuencia',
        'audio_ext_range_toggle' => 'Alternar rango extendido',
        'audio_step_change' => 'Cambio de paso (dB/Hz)',
        'audio_talkback_press' => 'Uso de talkback (habla al paciente)',
        'audio_logo_reset' => 'Reinicio de logoaudiometría',
        // Impedanciómetro (Z)
        'z_dial_change' => 'Movimiento de dial',
        'z_direction_change' => 'Cambio de dirección de barrido',
        'z_height_change' => 'Cambio de altura del trazado',
        'z_move_mark' => 'Movimiento de marca/cursor',
        'z_pressure_change' => 'Cambio de presión (daPa)',
        'z_reflex_freq_change' => 'Cambio de frecuencia de reflejo',
        'z_reflex_mode_change' => 'Cambio de modo de reflejo (ipsi/contra)',
        'z_screen_change' => 'Cambio de pantalla (timpanograma/reflejo/decay/ETF)',
        'z_side_change' => 'Cambio de oído',
        'z_stimulus_click' => 'Estímulo manual (click)',
        // Sistema
        'session_login' => 'Inicio de sesión',
        'session_logout' => 'Cierre de sesión',
        'console' => 'Mensaje de consola (debug)',
    ];

    public static function actionLabel(string $action): string
    {
        if (isset(self::ACTION_LABELS[$action])) {
            return self::ACTION_LABELS[$action];
        }
        return ucfirst(str_replace('_', ' ', $action));
    }

    /**
     * Decodifica el payload JSON de una fila de action_logs y expone
     * case_id/appointment_id/con_paciente a nivel de columna -- el cliente
     * los manda dentro del payload (ver Audiometer.py/_log, Z.py/_log), no
     * hay columnas propias en el schema para no migrar la tabla.
     */
    public static function decodeLog(array $row): array
    {
        $payload = $row['payload'] ? json_decode((string) $row['payload'], true) : null;
        if (!is_array($payload)) {
            $payload = [];
        }
        $row['case_id'] = $payload['case_id'] ?? null;
        $row['appointment_id'] = $payload['appointment_id'] ?? null;
        $row['con_paciente'] = $payload['con_paciente'] ?? ($row['case_id'] !== null);
        return $row;
    }

    public static function decodeLogs(array $rows): array
    {
        return array_map([self::class, 'decodeLog'], $rows);
    }

    /**
     * Agrupa filas de action_logs (ya decodificadas, mismo orden que la
     * tabla) en sesiones: corta cuando cambia la atención (appointment_id
     * o case_id) o cuando pasan más de $gapSeconds sin actividad -- así el
     * modo "sin paciente" (varias veces libres a lo largo del día) queda
     * separado en sesiones distintas en vez de una sola bolsa infinita.
     */
    public static function buildSessions(array $decodedLogs, int $gapSeconds = 300): array
    {
        $sessions = [];
        $current = null;
        foreach ($decodedLogs as $log) {
            $ts = strtotime((string) $log['client_ts']) ?: 0;
            $sameBucket = $current
                && $current['appointment_id'] === $log['appointment_id']
                && $current['case_id'] === $log['case_id'];
            $withinGap = $current && ($ts - $current['last_ts']) <= $gapSeconds;

            if ($current && $sameBucket && $withinGap) {
                $current['actions'][] = [
                    'ts' => $log['client_ts'],
                    'action' => $log['action'],
                    'delta_s' => $ts - $current['last_ts'],
                ];
                $current['end'] = $log['client_ts'];
                $current['last_ts'] = $ts;
                continue;
            }

            if ($current) {
                $sessions[] = $current;
            }
            $current = [
                'user_id' => $log['user_id'],
                'case_id' => $log['case_id'],
                'appointment_id' => $log['appointment_id'],
                'con_paciente' => $log['con_paciente'],
                'start' => $log['client_ts'],
                'end' => $log['client_ts'],
                'last_ts' => $ts,
                // delta_s null (no 0): es el inicio de la sesión, no hay
                // "acción anterior" real con la que comparar -- si se
                // pusiera 0 contaminaría las métricas de "acción sin pausa"
                // más abajo (cada sesión sumaría un falso 0).
                'actions' => [['ts' => $log['client_ts'], 'action' => $log['action'], 'delta_s' => null]],
            ];
        }
        if ($current) {
            $sessions[] = $current;
        }

        foreach ($sessions as &$s) {
            $s['n_actions'] = count($s['actions']);
            $s['duration_s'] = max(0, (strtotime((string) $s['end']) ?: 0) - (strtotime((string) $s['start']) ?: 0));
        }
        unset($s);

        return $sessions;
    }

    /**
     * Resume sesiones ya construidas (buildSessions) en señales de
     * comportamiento -- lo que realmente importa: no "cuántos logs" sino
     * "se demora o duda mucho" (pausas largas) vs "clickea sin pensar"
     * (varias acciones en el mismo segundo, delta_s = 0).
     */
    public static function summarizeSessions(array $sessions, int $longPauseSeconds = 30): array
    {
        $totalDuration = 0;
        $deltas = [];
        $longPauses = 0;
        $noPause = 0;
        $lastEnd = null;
        foreach ($sessions as $s) {
            $totalDuration += $s['duration_s'];
            foreach ($s['actions'] as $a) {
                if ($a['delta_s'] === null) {
                    continue; // primera acción de la sesión, sin referencia previa
                }
                $deltas[] = $a['delta_s'];
                if ($a['delta_s'] >= $longPauseSeconds) {
                    $longPauses++;
                } elseif ($a['delta_s'] === 0) {
                    $noPause++;
                }
            }
            if ($lastEnd === null || $s['end'] > $lastEnd) {
                $lastEnd = $s['end'];
            }
        }
        return [
            'n_sessions' => count($sessions),
            'total_duration_s' => $totalDuration,
            'avg_delta_s' => $deltas ? round(array_sum($deltas) / count($deltas), 1) : null,
            'long_pauses' => $longPauses,
            'no_pause_actions' => $noPause,
            'last_activity' => $lastEnd,
        ];
    }

    /**
     * Distribución de los deltas entre acciones en baldes fijos -- un
     * promedio esconde si el alumno tiene un patrón bimodal (rápido casi
     * siempre, pero con algunas dudas largas) vs uno parejo.
     */
    public static function deltaHistogram(array $sessions): array
    {
        $buckets = ['0s' => 0, '1-5s' => 0, '6-15s' => 0, '16-30s' => 0, '30s+' => 0];
        foreach ($sessions as $s) {
            foreach ($s['actions'] as $a) {
                $d = $a['delta_s'];
                if ($d === null) {
                    continue;
                }
                if ($d === 0) {
                    $buckets['0s']++;
                } elseif ($d <= 5) {
                    $buckets['1-5s']++;
                } elseif ($d <= 15) {
                    $buckets['6-15s']++;
                } elseif ($d <= 30) {
                    $buckets['16-30s']++;
                } else {
                    $buckets['30s+']++;
                }
            }
        }
        return $buckets;
    }

    /**
     * Cuenta atenciones distintas (case_id/appointment_id únicos, ignora
     * "modo libre" sin paciente) -- a diferencia de buildSessions(), NO
     * corta por pausa: un alumno que se queda 10 min pensando con el mismo
     * paciente sigue siendo UNA atención, no dos. buildSessions() sirve para
     * el timeline de pausas del admin, no para "cuántos pacientes atendió".
     */
    public static function countAttentions(array $decodedLogs): int
    {
        return count(self::attentionKeys($decodedLogs));
    }

    /** Atenciones distintas agrupadas por semana ISO -- mismo criterio que countAttentions(). */
    public static function attentionsByWeek(array $decodedLogs): array
    {
        $weeks = [];
        foreach ($decodedLogs as $log) {
            if (!($log['con_paciente'] ?? false)) {
                continue;
            }
            $ts = strtotime((string) $log['client_ts']) ?: 0;
            $week = date('o-\WW', $ts);
            $weeks[$week][self::attentionKey($log)] = true;
        }
        ksort($weeks);
        $out = [];
        foreach ($weeks as $week => $set) {
            $out[$week] = count($set);
        }
        return $out;
    }

    private static function attentionKey(array $log): string
    {
        return ($log['case_id'] ?? '') . '|' . ($log['appointment_id'] ?? '');
    }

    private static function attentionKeys(array $decodedLogs): array
    {
        $keys = [];
        foreach ($decodedLogs as $log) {
            if (!($log['con_paciente'] ?? false)) {
                continue;
            }
            $keys[self::attentionKey($log)] = true;
        }
        return $keys;
    }

    /**
     * Cuenta sesiones de uso reales: una por cada session_login (ver
     * src/main.py, se manda al abrir la app). A diferencia de
     * buildSessions() (que corta por 5 min de inactividad y por eso
     * infla el conteo si el alumno se queda pensando en la misma
     * atención), esto refleja "cuántas veces entró a la app", no
     * "cuántos bloques de actividad separados por pausa hubo".
     */
    public static function countLoginSessions(array $decodedLogs): int
    {
        $n = 0;
        foreach ($decodedLogs as $log) {
            if ($log['action'] === 'session_login') {
                $n++;
            }
        }
        return $n;
    }

    /**
     * Sesiones agrupadas por semana ISO (lunes a domingo) -- para ver
     * evolución en el semestre: ¿el delta promedio baja con las semanas?
     */
    public static function sessionsByWeek(array $sessions): array
    {
        $weeks = [];
        foreach ($sessions as $s) {
            $ts = strtotime((string) $s['start']) ?: 0;
            $week = date('o-\WW', $ts);
            if (!isset($weeks[$week])) {
                $weeks[$week] = ['n_sessions' => 0, 'deltas' => []];
            }
            $weeks[$week]['n_sessions']++;
            foreach ($s['actions'] as $a) {
                if ($a['delta_s'] !== null) {
                    $weeks[$week]['deltas'][] = $a['delta_s'];
                }
            }
        }
        ksort($weeks);
        $out = [];
        foreach ($weeks as $week => $w) {
            $out[$week] = [
                'n_sessions' => $w['n_sessions'],
                'avg_delta_s' => $w['deltas'] ? round(array_sum($w['deltas']) / count($w['deltas']), 1) : null,
            ];
        }
        return $out;
    }
}
