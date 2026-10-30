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
    /**
     * Eventos que registra el audiómetro y no son acciones del alumno: la
     * mano del paciente y la carga del caso (ver AudiometriaRegistro). Fuera
     * de las sesiones, o la mano, que sube a las décimas del estímulo,
     * contaría como "acción sin pausa".
     */
    public const NO_SON_DEL_ALUMNO = ['audio_respuesta', 'audio_caso_cargado'];

    private const ACTION_LABELS = [
        // Audiómetro
        'audio_intensity_change' => 'Cambio de intensidad (dB)',
        'audio_freq_change' => 'Cambio de frecuencia (Hz)',
        'audio_stim_button' => 'Presentación del estímulo',
        'audio_stim_select' => 'Selección de estímulo (tono/ruido)',
        'audio_logo_response' => 'Acierto o error en logoaudiometría',
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
        'audio_prueba_change' => 'Cambio de prueba (umbrales/logoaudiometría)',
        'audio_respuesta' => 'Respuesta del paciente (mano)',
        'audio_caso_cargado' => 'Paciente cargado en el audiómetro',
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
        'z_probe_freq_change' => 'Cambio de tono de sonda (226/1000 Hz)',
        'z_decay_freq_change' => 'Cambio de frecuencia del tone decay',
        'z_etf_prueba_change' => 'Cambio de prueba de función tubaria',
        'z_etf_test' => 'Prueba de función tubaria',
        'z_no_realizable' => 'FALTA GRAVE: impedanciómetro en un oído donde la sonda no iba',
        // Rinomanómetro, rinómetro acústico y rinoscopía (nasal/, demo interna)
        'rm_adaptador' => 'Adaptador de presión en una narina',
        'rm_mascara' => 'Máscara puesta o sacada',
        'rm_acomodar_mascara' => 'Acomoda la máscara',
        'rm_indicacion' => 'Indicación al paciente',
        'rm_sello' => 'Comprueba el sello del adaptador',
        'rm_vasoconstrictor' => 'Vasoconstrictor',
        'rm_saltar_espera' => 'Salta la espera del vasoconstrictor',
        'rm_error_simulado' => 'Error de técnica simulado (docente)',
        'rm_grabar' => 'Empieza a grabar',
        'rm_cancelar' => 'Cancela la grabación',
        'rm_grabacion' => 'Grabación terminada',
        'ra_calibrar' => 'Calibra el rinómetro',
        'ra_iniciar' => 'Inicia la toma de una fosa',
        'ra_detener' => 'Detiene sin ningún pulso',
        'ra_registro' => 'Registro de una fosa',
        'ra_marcar' => 'Mueve un cursor (MCA1 o MCA2)',
        'ra_cancelar' => 'Toma cortada al cambiar de atención',
        'ra_vasoconstrictor' => 'Vasoconstrictor',
        'ra_error_simulado' => 'Error de técnica simulado (docente)',
        'rs_mirada' => 'Mira una fosa con el espéculo',
        'esp_pinza' => 'Pinza nasal puesta o sacada',
        'esp_boquilla' => 'Boquilla con filtro puesta o sacada',
        'esp_medir' => 'Mide talla y peso',
        'esp_verificar' => 'Verifica el espirómetro con la jeringa de 3 L',
        'esp_calibrar' => 'Calibra el espirómetro',
        'esp_cero' => 'Pone el flujo en cero',
        'esp_iniciar' => 'Inicia una maniobra',
        'esp_indicacion' => 'Indicación al paciente',
        'esp_maniobra' => 'Maniobra terminada',
        'esp_cancelar' => 'Maniobra cancelada o sin espiración forzada',
        'esp_marca' => 'Marca lo que vio en una maniobra',
        'esp_broncodilatador' => 'Broncodilatador',
        'esp_saltar_espera' => 'Salta la espera del broncodilatador',
        'esp_error_simulado' => 'Error de técnica simulado (docente)',
        'olf_venda' => 'Venda o desvenda al paciente',
        'olf_narina' => 'Cambia la narina que se evalúa',
        'olf_prueba' => 'Cambia de prueba (umbral, discriminación, identificación)',
        'olf_presentar' => 'Presenta un trío o un ítem',
        'olf_elegir_igual' => 'Le pide que elija igual (elección forzada)',
        'olf_anotar_sin_eleccion' => 'Anota el ensayo sin que el paciente elija',
        'olf_preguntar_preparacion' => 'Pregunta cómo se preparó el paciente',
        'olf_esperar_preparacion' => 'Espera a que pase la preparación',
        'olf_saltar_espera' => 'Salta la espera de la preparación',
        'olf_borrar_ensayo' => 'Borra un ensayo de la hoja',
        'olf_puntaje' => 'Anota un puntaje (T, D, I o TDI)',
        'olf_categoria' => 'Elige la categoría del olfato',
        'prick_preguntar_farmacos' => 'Pregunta por los fármacos que toma',
        'prick_marcar' => 'Marca un sitio en el antebrazo',
        'prick_quitar' => 'Quita un sitio marcado',
        'prick_lanceta' => 'Elige o cambia la lanceta',
        'prick_puncionar' => 'Punciona un sitio',
        'prick_secar' => 'Seca las gotas',
        'prick_medir' => 'Mide una pápula',
        'prick_resultado' => 'Anota el resultado de un sitio',
        'prick_saltar_espera' => 'Salta la espera de la lectura',
        'psg_estudio' => 'Elige el estudio (polisomnografía o poligrafía)',
        'psg_sensor' => 'Monta o retira un sensor',
        'psg_registrar' => 'Pone en marcha el registro',
        'psg_cambiar' => 'Cambia un evento de la puntuación',
        'psg_borrar' => 'Borra un evento de la puntuación',
        'psg_agregar' => 'Agrega un evento a la puntuación',
        'psg_excluir' => 'Excluye un tramo del registro',
        'psg_volver_auto' => 'Vuelve a la puntuación automática',
        'psg_regla' => 'Cambia la regla de hipopnea',
        'psg_gravedad' => 'Elige la gravedad por el índice',
        'cpap_interfaz' => 'Elige la mascarilla y su talla (CPAP)',
        'cpap_empezar' => 'Empieza la titulación de CPAP',
        'cpap_presion' => 'Cambia la presión del CPAP',
        'cpap_velocidad' => 'Cambia la velocidad de la noche (CPAP)',
        'cpap_pausa' => 'Pausa o reanuda la noche (CPAP)',
        'cpap_terminar' => 'Termina la noche de CPAP',
        'cpap_indicar' => 'Indica la presión y el grado de la titulación',
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

    public static function formatDurationHms(int $totalSeconds): string
    {
        $h = intdiv($totalSeconds, 3600);
        $m = intdiv($totalSeconds % 3600, 60);
        $s = $totalSeconds % 60;
        if ($h > 0) {
            return sprintf('%dh %02dm %02ds', $h, $m, $s);
        }
        if ($m > 0) {
            return sprintf('%dm %02ds', $m, $s);
        }
        return sprintf('%ds', $s);
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
            if (in_array($log['action'], self::NO_SON_DEL_ALUMNO, true)) {
                continue;
            }
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
     * Duración de reloj real de un grupo de sesiones (típicamente todos los
     * bloques de UNA atención): primera acción a última acción, sin
     * descontar las pausas >5min que buildSessions() usa para cortar
     * bloques. summarizeSessions() suma solo la duración de cada bloque
     * (ver total_duration_s) y por eso esconde pausas largas dentro de la
     * misma atención -- si el alumno se pausó 30min a mitad de camino, esos
     * 30min no aparecían en ningún lado. Para "¿cuánto duró la atención?"
     * (lo que un docente cronometra con reloj) hay que usar esta función,
     * no total_duration_s.
     */
    public static function wallClockDurationSeconds(array $sessions): int
    {
        if (!$sessions) {
            return 0;
        }
        $start = null;
        $end = null;
        foreach ($sessions as $s) {
            $sStart = strtotime((string) $s['start']) ?: 0;
            $sEnd = strtotime((string) $s['end']) ?: 0;
            if ($start === null || $sStart < $start) {
                $start = $sStart;
            }
            if ($end === null || $sEnd > $end) {
                $end = $sEnd;
            }
        }
        return max(0, $end - $start);
    }

    /**
     * Duración real de UNA atención: desde que el alumno presiona "Atender"
     * (attendances.hora_real, sellado server-side, sobrevive intacto al
     * UPDATE de "atendido") hasta que la marca "atendido" (updated_at). A
     * diferencia de wallClockDurationSeconds()/total_duration_s (que
     * arrancan desde la primera acción en action_logs), esto no se pierde
     * el tiempo que el alumno pasa leyendo el caso/paciente antes de tocar
     * el audiómetro o impedanciómetro -- que puede ser varios minutos.
     * hora_real solo guarda la hora (sin fecha); se asume el mismo día de
     * updated_at salvo que eso dé un inicio posterior al fin, en cuyo caso
     * se resta un día (atención que cruzó medianoche).
     */
    public static function attendanceDurationSeconds(?string $horaReal, ?string $updatedAt): ?int
    {
        if (!$horaReal || !$updatedAt) {
            return null;
        }
        $endTs = strtotime($updatedAt);
        if ($endTs === false) {
            return null;
        }
        $startTs = strtotime(date('Y-m-d', $endTs) . ' ' . $horaReal);
        if ($startTs === false) {
            return null;
        }
        if ($startTs > $endTs) {
            $startTs = strtotime(date('Y-m-d', $endTs - 86400) . ' ' . $horaReal);
        }
        return $startTs === false ? null : max(0, $endTs - $startTs);
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
