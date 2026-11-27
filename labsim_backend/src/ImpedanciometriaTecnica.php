<?php

declare(strict_types=1);

require_once __DIR__ . '/EquiposTecnica.php';
require_once __DIR__ . '/AudiometriaPertinencia.php';
require_once __DIR__ . '/CaseBuilder.php';
require_once __DIR__ . '/CaseProfile.php';

/**
 * Técnica de la impedanciometría (libro, H7). Cada prueba (timpanograma,
 * reflejos ipsi, reflejos contra, deterioro, función tubaria) se evalúa si
 * el alumno la hizo en algún oído: entonces se pide completa en los oídos
 * donde se puede medir. Si no la hizo, se advierte y no descuenta (no todas
 * las atenciones piden todo).
 *
 * - Antes: otoscopía primero, explicar el examen, avisar los sonidos fuertes
 *   antes de los reflejos; en el menor de 6 meses, sonda de 1000 Hz.
 * - Timpanograma en cada oído realizable, antes de sus reflejos.
 * - Reflejos en 500, 1000, 2000 y 4000 Hz; contralaterales solo si el otro
 *   oído también se puede medir. Umbral buscado subiendo de 5 en 5 hasta la
 *   respuesta (con el umbral del caso: llegó a 5 dB de él, o subió hasta
 *   100 dB si no hay reflejo).
 * - Deterioro: en 500 o 1000 Hz, con reflejo presente, 10 dB sobre su
 *   umbral; sin sospecha retrococlear no hacía falta (advertencia).
 * - Función tubaria: la prueba de membrana íntegra o la de perforada según
 *   el caso (ETF Permeable / No permeable = perforada); en la íntegra, un
 *   timpanograma basal antes de las maniobras.
 *
 * Meter la sonda en un oído NR es falta grave (FaltasGraves) y no se cuenta
 * acá otra vez. Null si el alumno no midió nada con el paciente.
 */
final class ImpedanciometriaTecnica
{
    private const OIDOS = ['OD', 'OI'];
    public const FRECUENCIAS = ['500', '1000', '2000', '4000'];
    /** Fila de cada frecuencia en Reflex ipsi/contra del caso (contra tiene además NBN). */
    private const FILA = ['500' => 0, '1000' => 1, '2000' => 2, '4000' => 3, 'NBN' => 4];
    /** Sin reflejo en el caso (o sobre el dial): se da por buscado si subió hasta acá. */
    public const AUSENTE_HASTA_DB = 100;
    /** Edad (años) bajo la cual va la sonda de 1000 Hz. */
    public const EDAD_SONDA_1000 = 0.5;

    public static function evaluar(array $logs, array $caso): ?array
    {
        $medidas = self::medidas($logs);
        $etf = EquiposTecnica::filas($logs, 'z_etf_test');
        if (!$medidas && !$etf) {
            return null;
        }
        $realizables = array_values(array_filter([0, 1], static function ($o) use ($caso) {
            return ($caso[$o === 0 ? 'Z_OD' : 'Z_OI'] ?? null) !== CaseBuilder::Z_NO_REALIZABLE;
        }));
        $reglas = [];
        $oidos = [];
        $obs = [];
        $t0 = min(array_merge(array_column($medidas, 't'), array_map([EquiposTecnica::class, 't'], $etf)));

        // ---- antes de medir ----------------------------------------------------
        $fechaOto = substr((string) ($logs[0]['client_ts'] ?? ''), 0, 10) >= EquiposTecnica::OTOSCOPIO_DESDE;
        $tOto = EquiposTecnica::primera($logs, static function ($l) { return $l['action'] === 'ot_otoscopio'; });
        if ($tOto === null && $fechaOto) {
            $obs[] = 'Puso la sonda sin otoscopía en esta atención: la otoscopía decide en qué oído se puede medir.';
        } elseif ($tOto !== null) {
            $reglas[] = [
                'texto' => 'La otoscopía va antes de la sonda.',
                'cumple' => $tOto <= $t0,
                'detalle' => $tOto <= $t0 ? 'Así fue.' : 'La otoscopía fue después.',
                'peso' => 2,
            ];
        }
        $fecha = substr((string) ($logs[0]['client_ts'] ?? ''), 0, 10);
        $conInstrucciones = $fecha >= EquiposTecnica::Z_INSTRUCCIONES_DESDE;
        $tExplica = EquiposTecnica::primera($logs, static function ($l) {
            return $l['action'] === 'z_instruccion' && in_array($l['payload']['clave'] ?? '', ['explicar_examen', 'colocar_sonda'], true);
        });
        if ($conInstrucciones) {
            $reglas[] = [
                'texto' => 'Se le explica el examen antes de medir.',
                'cumple' => $tExplica !== null && $tExplica <= $t0,
                'detalle' => $tExplica === null ? 'No se le explicó.' : ($tExplica <= $t0 ? 'Se le explicó antes.' : 'Se le explicó después de empezar.'),
                'peso' => 1,
            ];
        }
        $reflejos = array_values(array_filter($medidas, static function ($m) { return $m['screen'] === 'reflex'; }));
        if ($reflejos && $conInstrucciones) {
            $tAviso = EquiposTecnica::primera($logs, static function ($l) {
                return $l['action'] === 'z_instruccion' && ($l['payload']['clave'] ?? '') === 'sonidos_fuertes';
            });
            $reglas[] = [
                'texto' => 'Antes de los reflejos se le avisa que oirá sonidos fuertes.',
                'cumple' => $tAviso !== null && $tAviso <= $reflejos[0]['t'],
                'detalle' => $tAviso === null ? 'No se le avisó.' : ($tAviso <= $reflejos[0]['t'] ? 'Se le avisó antes.' : 'Se le avisó después.'),
                'peso' => 1,
            ];
        }
        $timpanos = array_values(array_filter($medidas, static function ($m) { return $m['screen'] === 'tymp'; }));
        $edad = (float) ($caso['edad'] ?? 30);
        if ($timpanos && $edad < self::EDAD_SONDA_1000) {
            $con1000 = count(array_filter($timpanos, static function ($m) { return $m['sonda'] === '1000'; }));
            $reglas[] = [
                'texto' => 'En el menor de 6 meses el timpanograma va con la sonda de 1000 Hz.',
                'cumple' => $con1000 === count($timpanos),
                'logro' => $con1000 / count($timpanos),
                'detalle' => "{$con1000} de " . count($timpanos) . ' timpanograma(s) con 1000 Hz.',
                'peso' => 2,
            ];
        }

        // ---- por oído ------------------------------------------------------------
        $hayIpsi = (bool) array_filter($reflejos, static function ($m) { return $m['mode'] === 'IPSI'; });
        $hayContra = (bool) array_filter($reflejos, static function ($m) { return $m['mode'] === 'CONTRA'; });
        $series = [];
        foreach ($realizables as $o) {
            $r = [];
            $tymp = array_values(array_filter($timpanos, static function ($m) use ($o) { return $m['oido'] === $o; }));
            $refl = array_values(array_filter($reflejos, static function ($m) use ($o) { return $m['oido'] === $o; }));
            if ($timpanos) {
                $r[] = [
                    'texto' => 'Timpanograma.',
                    'cumple' => $tymp !== [],
                    'detalle' => $tymp ? 'Se hizo.' : 'No se hizo en este oído.',
                    'peso' => 3,
                ];
                if ($tymp && $refl) {
                    $r[] = [
                        'texto' => 'El timpanograma va antes de los reflejos.',
                        'cumple' => $tymp[0]['t'] <= $refl[0]['t'],
                        'detalle' => $tymp[0]['t'] <= $refl[0]['t'] ? 'Así fue.' : 'Hizo reflejos antes del timpanograma.',
                        'peso' => 1,
                    ];
                }
            }
            foreach (['IPSI' => $hayIpsi, 'CONTRA' => $hayContra] as $modo => $hay) {
                if (!$hay || ($modo === 'CONTRA' && !in_array(1 - $o, $realizables, true))) {
                    continue;
                }
                $hechas = [];
                foreach ($refl as $m) {
                    if ($m['mode'] === $modo && in_array($m['freq'], self::FRECUENCIAS, true)) {
                        $hechas[$m['freq']] = true;
                        $series[$o][$modo][$m['freq']][] = $m;
                    }
                }
                $faltan = array_diff(self::FRECUENCIAS, array_keys($hechas));
                $r[] = [
                    'texto' => $modo === 'IPSI'
                        ? 'Reflejos ipsilaterales en 500, 1000, 2000 y 4000 Hz.'
                        : 'Reflejos contralaterales (sonda en este oído, tono en el otro) en 500, 1000, 2000 y 4000 Hz.',
                    'cumple' => $faltan === [],
                    'logro' => count($hechas) / count(self::FRECUENCIAS),
                    'detalle' => $faltan === [] ? 'Las cuatro.' : 'Faltó ' . EquiposTecnica::lista(array_map(static function ($f) { return $f . ' Hz'; }, $faltan)) . '.',
                    'peso' => 2,
                ];
            }
            // Cada reflejo: el paso (de 5 en 5 mientras no responde) y si se
            // llegó al umbral (o se subió lo bastante si no hay): son dos
            // errores distintos y cada uno descuenta una vez.
            $pasosOk = $llegoOk = $total = 0;
            $malPaso = $malUmbral = $doc = [];
            foreach ($series[$o] ?? [] as $modo => $porFreq) {
                foreach ($porFreq as $freq => $clicks) {
                    $total++;
                    $umbral = self::umbralReflejo($caso, $modo, (string) $freq, $o);
                    $b = self::busqueda($clicks, $umbral);
                    $nombre = strtolower($modo) . " {$freq} Hz";
                    $pasosOk += $b['pasos'] ? 1 : 0;
                    $llegoOk += $b['llego'] ? 1 : 0;
                    if (!$b['pasos']) {
                        $malPaso[] = $nombre;
                    }
                    if (!$b['llego']) {
                        $malUmbral[] = "{$nombre} ({$b['porque']})";
                    }
                    if (!$b['pasos'] || !$b['llego']) {
                        $doc[] = "{$nombre}: " . implode('→', array_column($clicks, 'dB')) . ' dB, umbral ' . ($umbral ?? 'ausente');
                    }
                }
            }
            if ($total > 0) {
                $r[] = [
                    'texto' => 'Mientras no hay reflejo, se sube de 5 en 5 dB.',
                    'cumple' => $pasosOk === $total,
                    'logro' => $pasosOk / $total,
                    'detalle' => $pasosOk === $total ? "Así en los {$total} reflejos." : "{$pasosOk} de {$total}. Saltos distintos de 5 dB en " . EquiposTecnica::lista($malPaso) . '.',
                    'detalle_docente' => implode('; ', $doc),
                    'peso' => 1,
                ];
                $r[] = [
                    'texto' => 'Se encuentra el umbral de cada reflejo (o se sube hasta ' . self::AUSENTE_HASTA_DB . ' dB si no aparece).',
                    'cumple' => $llegoOk === $total,
                    'logro' => $llegoOk / $total,
                    'detalle' => $llegoOk === $total ? "En los {$total} reflejos." : "{$llegoOk} de {$total}. Revisar: " . EquiposTecnica::lista($malUmbral) . '.',
                    'peso' => 2,
                ];
            }
            $oidos[self::OIDOS[$o]] = $r;
        }
        if ($medidas && !$timpanos) {
            $obs[] = 'No hizo timpanograma.';
        }
        if ($timpanos && !$reflejos) {
            $obs[] = 'No hizo reflejos estapediales.';
        }

        // ---- deterioro del reflejo ---------------------------------------------
        $decays = array_values(array_filter($medidas, static function ($m) { return $m['screen'] === 'decay'; }));
        $asimetria = AudiometriaPertinencia::asimetriaSensorioneural(new AudiometriaPaciente($caso), 20);
        if ($decays) {
            $frecOk = $conReflejo = $nivelOk = 0;
            foreach ($decays as $d) {
                $frecOk += in_array($d['freq'], ['500', '1000'], true) ? 1 : 0;
                $u = self::umbralReflejo($caso, $d['mode'], $d['freq'], $d['oido']);
                if ($u !== null) {
                    $conReflejo++;
                    $nivelOk += abs($d['dB'] - ($u + 10)) <= 5 ? 1 : 0;
                }
            }
            $n = count($decays);
            $reglas[] = [
                'texto' => 'El deterioro del reflejo se mide en 500 o 1000 Hz (sobre 1000 Hz también decaen los oídos sanos).',
                'cumple' => $frecOk === $n, 'logro' => $frecOk / $n,
                'detalle' => "{$frecOk} de {$n} medición(es) en 500 o 1000 Hz.", 'peso' => 1,
            ];
            $reglas[] = [
                'texto' => 'El deterioro se mide donde hay reflejo (sin reflejo no hay qué deteriorar).',
                'cumple' => $conReflejo === $n, 'logro' => $conReflejo / $n,
                'detalle' => "{$conReflejo} de {$n} donde había reflejo.", 'peso' => 2,
            ];
            if ($conReflejo > 0) {
                $reglas[] = [
                    'texto' => 'El tono del deterioro va 10 dB sobre el umbral del reflejo.',
                    'cumple' => $nivelOk === $conReflejo, 'logro' => $nivelOk / $conReflejo,
                    'detalle' => "{$nivelOk} de {$conReflejo} a ese nivel.", 'peso' => 1,
                ];
            }
            if ($asimetria === null) {
                $obs[] = 'Midió el deterioro del reflejo sin una asimetría sensorioneural que haga sospechar algo retrococlear: no hacía falta.';
            }
        } elseif ($asimetria !== null && $reflejos) {
            $obs[] = 'Con una pérdida sensorioneural asimétrica, el deterioro del reflejo ayuda a descartar lo retrococlear: no se midió.';
        }

        // ---- función tubaria ---------------------------------------------------
        if ($etf) {
            $porOido = [];
            foreach ($etf as $e) {
                $o = EquiposTecnica::oido($e['payload']['side'] ?? null);
                if ($o !== null) {
                    $porOido[$o][] = $e;
                }
            }
            $bien = 0;
            $malDoc = [];
            $basalOk = $integras = 0;
            foreach ($porOido as $o => $lista) {
                $perforada = in_array((string) ($caso['ETF'][$o] ?? ''), CaseBuilder::ETF_PERFORADA, true);
                $esperada = $perforada ? 'perforada' : 'integra';
                $hizo = array_values(array_unique(array_map(static function ($e) { return (string) ($e['payload']['prueba'] ?? ''); }, $lista)));
                if (in_array($esperada, $hizo, true) && count($hizo) === 1) {
                    $bien++;
                } else {
                    $malDoc[] = self::OIDOS[$o] . ': hizo ' . implode(' y ', $hizo) . ', membrana ' . ($perforada ? 'perforada' : 'íntegra');
                }
                if (!$perforada) {
                    $integ = array_values(array_filter($lista, static function ($e) { return ($e['payload']['prueba'] ?? '') === 'integra'; }));
                    if ($integ) {
                        $integras++;
                        $basalOk += ($integ[0]['payload']['maniobra'] ?? '') === 'reposo' ? 1 : 0;
                    }
                }
            }
            $n = count($porOido);
            if ($n > 0) {
                $reglas[] = [
                    'texto' => 'La prueba de trompa corresponde al estado de la membrana (íntegra o perforada).',
                    'cumple' => $bien === $n, 'logro' => $bien / $n,
                    'detalle' => $bien === $n ? 'Eligió bien.' : "Eligió bien en {$bien} de {$n} oído(s).",
                    'detalle_docente' => implode('; ', $malDoc), 'peso' => 2,
                ];
            }
            if ($integras > 0) {
                $reglas[] = [
                    'texto' => 'Con la membrana íntegra, un timpanograma basal (en reposo) antes de las maniobras.',
                    'cumple' => $basalOk === $integras, 'logro' => $basalOk / $integras,
                    'detalle' => "Partió en reposo en {$basalOk} de {$integras} oído(s).", 'peso' => 1,
                ];
            }
            $sinPresion = count(EquiposTecnica::filas($logs, 'z_etf_sin_presion'));
            if ($sinPresion > 0) {
                $obs[] = "En la prueba de membrana perforada intentó partir {$sinPresion} vez(veces) sin presurizar el conducto.";
            }
        }

        $sinSello = count(EquiposTecnica::filas($logs, 'z_sin_sello'));
        if ($sinSello >= 3) {
            $obs[] = "Intentó medir {$sinSello} veces sin la sonda sellada (sin sonda o con una oliva que no sella).";
        }
        return ['hecha' => true, 'reglas' => $reglas, 'oidos' => $oidos, 'observaciones' => $obs];
    }

    /**
     * Mediciones que llegaron a hacerse (z_stimulus_click que el equipo no
     * bloqueó por falta de sello o por oído NR en el mismo instante).
     *
     * @return array<int,array{t:float, screen:string, oido:?int, mode:string, freq:string, dB:int, sonda:string}>
     */
    public static function medidas(array $logs): array
    {
        $out = [];
        $sonda = '226';
        $n = count($logs);
        for ($i = 0; $i < $n; $i++) {
            $l = $logs[$i];
            if ($l['action'] === 'z_probe_freq_change') {
                $sonda = (string) ($l['payload']['freq'] ?? $sonda);
                continue;
            }
            if ($l['action'] !== 'z_stimulus_click') {
                continue;
            }
            $t = EquiposTecnica::t($l);
            $bloqueada = false;
            for ($j = $i + 1; $j < $n && EquiposTecnica::t($logs[$j]) - $t <= 1.0; $j++) {
                if (in_array($logs[$j]['action'], ['z_sin_sello', 'z_no_realizable'], true)) {
                    $bloqueada = true;
                    break;
                }
                if ($logs[$j]['action'] === 'z_stimulus_click') {
                    break;
                }
            }
            if ($bloqueada) {
                continue;
            }
            $p = $l['payload'];
            $out[] = [
                't' => $t,
                'screen' => (string) ($p['screen'] ?? ''),
                'oido' => EquiposTecnica::oido($p['side'] ?? null),
                'mode' => strtoupper((string) ($p['mode'] ?? 'IPSI')),
                'freq' => (string) ($p['freq'] ?? ''),
                'dB' => (int) ($p['dB'] ?? 0),
                'sonda' => $sonda,
            ];
        }
        return $out;
    }

    /** Umbral del reflejo del caso (sonda en $oido), o null si no hay reflejo. */
    public static function umbralReflejo(array $caso, string $modo, string $freq, ?int $oido): ?int
    {
        $fila = self::FILA[$freq] ?? null;
        if ($fila === null || $oido === null) {
            return null;
        }
        $v = $caso['Reflex'][strtolower($modo)][$fila][$oido] ?? null;
        if (!is_numeric($v) || (int) $v >= 130 || (int) $v > CaseProfile::REFLEX_DIAL_MAX_DB) {
            return null;
        }
        return (int) $v;
    }

    /**
     * Una serie de estímulos en la misma vía y frecuencia: 'pasos' (mientras
     * no responde, cada subida es de 5 dB), 'llego' (la primera respuesta
     * quedó a 5 dB del umbral, o subió hasta AUSENTE_HASTA_DB si no hay
     * reflejo) y 'porque' (si no llegó).
     *
     * @return array{pasos:bool, llego:bool, porque:string}
     */
    public static function busqueda(array $clicks, ?int $umbral): array
    {
        $pasos = true;
        for ($i = 1, $n = count($clicks); $i < $n; $i++) {
            $antes = $clicks[$i - 1]['dB'];
            $ahora = $clicks[$i]['dB'];
            $respondio = $umbral !== null && $antes >= $umbral;
            if (!$respondio && $ahora > $antes && $ahora - $antes !== 5) {
                $pasos = false;
            }
        }
        $niveles = array_column($clicks, 'dB');
        if ($umbral === null) {
            $llego = max($niveles) >= self::AUSENTE_HASTA_DB;
            $porque = 'sin reflejo: no subió hasta ' . self::AUSENTE_HASTA_DB . ' dB';
        } else {
            $sobre = array_filter($niveles, static function ($d) use ($umbral) { return $d >= $umbral; });
            $llego = $sobre !== [] && min($sobre) <= $umbral + 5;
            $porque = $sobre === [] ? 'no llegó a la respuesta' : 'la primera respuesta quedó lejos del umbral';
        }
        return ['pasos' => $pasos, 'llego' => $llego, 'porque' => $porque];
    }
}
