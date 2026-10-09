<?php

declare(strict_types=1);

/**
 * Indicadores de técnica de la audiometría (AudiometriaRegistro +
 * AudiometriaTecnica): un examen simulado que sigue la técnica al pie de la
 * letra cumple todo; cada error típico aparece en su regla, y un registro
 * viejo (sin "v", hora en segundos) se reconstruye con los mismos umbrales.
 */

require_once dirname(__DIR__) . '/src/AudiometriaTecnica.php';

/** Caso: OD 10 dB parejo (mejor), OI 30 dB sensorioneural. */
function at_caso(): array
{
    $filas = array_fill(0, 15, [10, 30]);
    return ['Aerea_mkg' => $filas, 'Osea_mkg' => $filas, 'Aerea' => $filas, 'Osea' => $filas];
}

/**
 * Examinador simulado. Produce las filas de action_logs (payload ya
 * decodificado) de una atención. $v2 = registro nuevo (foto del equipo,
 * mano registrada, milisegundos); si no, como los registros viejos.
 */
final class AtExaminador
{
    public $logs = [];
    private $t;
    private $v2;
    private $caso;
    private $estado;

    public function __construct(bool $v2, ?array $caso = null)
    {
        $this->v2 = $v2;
        $this->t = strtotime('2026-10-08 10:00:00');
        $this->caso = new AudiometriaPaciente($caso ?? at_caso());
        $this->estado = [
            'prueba' => 'Umbrales', 'freq' => '1000 Hz', 'step' => 5, 'instruccion' => null,
            'canales' => [
                ['on' => false, 'invertido' => false, 'intensity' => '20 dB HL', 'stim' => 'Tono', 'output' => 'Derecha', 'trans' => 'Aerea', 'contin' => 'Continuo'],
                ['on' => false, 'invertido' => false, 'intensity' => '20 dB HL', 'stim' => 'Narrow Band Noise', 'output' => 'Izquierda', 'trans' => 'Aerea', 'contin' => 'Continuo'],
            ],
        ];
    }

    private function log(string $accion, array $payload, float $dt = 0.5): void
    {
        $this->t += $dt;
        $payload['appointment_id'] = 7;
        $payload['case_id'] = 3;
        if ($this->v2) {
            $payload['v'] = 2;
            $ms = (int) floor(round($this->t, 3) * 1000);
            $ts = date('Y-m-d H:i:s', intdiv($ms, 1000)) . sprintf('.%03d', $ms % 1000);
        } else {
            $ts = date('Y-m-d H:i:s', (int) floor($this->t));
        }
        $this->logs[] = ['client_ts' => $ts, 'action' => $accion, 'payload' => $payload];
    }

    public function instruccion(string $cmd): void
    {
        $this->estado['instruccion'] = $cmd;
        $this->log('audio_talkback_press', ['command' => $cmd]);
    }

    public function transductor(string $trans): void
    {
        $this->estado['canales'][0]['trans'] = $trans;
        $this->log('audio_trans_select', ['ch' => 0, 'trans' => $trans]);
    }

    public function oido(int $o): void
    {
        $this->estado['canales'][0]['output'] = $o === 0 ? 'Derecha' : 'Izquierda';
        $this->log('audio_output_select', ['ch' => 0, 'output' => $this->estado['canales'][0]['output']]);
    }

    public function frecuencia(int $hz): void
    {
        $this->estado['freq'] = "{$hz} Hz";
        $this->log('audio_freq_change', ['freq' => $hz]);
    }

    /** Un estímulo de $dur segundos a $db. Devuelve si respondió. */
    public function tono(int $db, float $dur = 1.5): bool
    {
        if ($this->estado['canales'][0]['intensity'] !== "{$db} dB HL") {
            $this->estado['canales'][0]['intensity'] = "{$db} dB HL";
            $this->log('audio_intensity_change', ['ch' => 0, 'intensity' => $db, 'freq' => (int) $this->estado['freq']]);
        }
        $c = $this->estado['canales'][0];
        $base = ['ch' => 0, 'freq' => $this->estado['freq'], 'intensity' => $c['intensity'], 'stim' => $c['stim'], 'output' => $c['output'], 'trans' => $c['trans']];
        $hz = (int) $this->estado['freq'];
        $f = array_search($hz, AudiometriaPaciente::FRECUENCIAS, true);
        $o = $c['output'] === 'Derecha' ? 0 : 1;
        $via = $c['trans'] === 'Aerea' ? 'aerea' : 'osea';
        $oye = $db >= $this->caso->umbralSinRuido($via, (int) $f, $o);
        $this->log('audio_stim_button', $base + ['play' => true] + ($this->v2 ? ['estado' => $this->estado] : []));
        $this->estado['canales'][0]['on'] = true;
        if ($this->v2 && $oye) {
            $this->log('audio_respuesta', ['mano' => true], 0.3);
        }
        $this->log('audio_stim_button', $base + ['play' => false] + ($this->v2 ? ['estado' => $this->estado] : []), $dur - ($this->v2 && $oye ? 0.3 : 0));
        $this->estado['canales'][0]['on'] = false;
        if ($this->v2 && $oye) {
            $this->log('audio_respuesta', ['mano' => false], 0.05);
        }
        $this->t += 1.0;
        return $oye;
    }

    /**
     * Una frecuencia con la técnica: familiarización +10, después -10 tras
     * responder, +5 tras no responder, cierra con 2 respuestas subiendo.
     * $errores: 'sube10' (sube 10 en vez de 5).
     */
    public function umbral(int $inicio, array $errores = []): int
    {
        $db = $inicio;
        while (!$this->tono($db)) {
            $db += 10;
        }
        $asc = [];
        $vieneDeAbajo = false;
        for ($guard = 0; $guard < 40; $guard++) {
            $db -= 10;
            $vieneDeAbajo = false;
            while (true) {
                $oye = $this->tono($db);
                if ($oye) {
                    if ($vieneDeAbajo) {
                        $asc[$db] = ($asc[$db] ?? 0) + 1;
                        if ($asc[$db] >= 2) {
                            return $db;
                        }
                    }
                    break;
                }
                $db += in_array('sube10', $errores, true) ? 10 : 5;
                $vieneDeAbajo = true;
            }
        }
        return $db;
    }

    /** Un oído completo: orden de la técnica y repetición de 1 kHz. */
    public function oidoCompleto(int $o, array $orden, int $inicio = 40, bool $repetir = true): void
    {
        $this->oido($o);
        $previo = null;
        foreach ($orden as $hz) {
            $this->frecuencia($hz);
            $previo = $this->umbral($previo === null ? $inicio : $previo + 10);
        }
        if ($repetir) {
            $this->frecuencia(1000);
            $this->umbral($previo + 10);
        }
    }
}

function at_reglas(array $r): array
{
    $out = [];
    foreach ($r['reglas'] as $x) {
        $out[$x['texto']] = $x['cumple'];
    }
    foreach ($r['oidos'] as $oido => $reglas) {
        foreach ($reglas as $x) {
            $out[$oido . ' · ' . $x['texto']] = $x['cumple'];
        }
    }
    return $out;
}

function at_falla(array $reglas, string $fragmento): ?bool
{
    foreach ($reglas as $texto => $cumple) {
        if (strpos($texto, $fragmento) !== false && $cumple === false) {
            return true;
        }
    }
    return false;
}

$params = AudiometriaTecnica::parametrosDefault();
$aereos = AudiometriaTecnica::ORDEN_FRECUENCIAS['aereos'];
$oseos = AudiometriaTecnica::ORDEN_FRECUENCIAS['oseos'];

// --- Examen al pie de la letra (v2) ---------------------------------------
$ex = new AtExaminador(true);
$ex->instruccion('colocar_fonos');
$ex->oidoCompleto(0, $aereos);
$ex->oidoCompleto(1, $aereos);
$ex->instruccion('colocar_vibrador');
$ex->transductor('Oséa');
$ex->oidoCompleto(1, $oseos);
$res = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($ex->logs, at_caso()), at_caso(), $params);

t_eq($res['reconstruido'], false, 'Técnica: el registro v2 se lee directo');
t_eq($res['con_ms'], true, 'Técnica: el registro v2 trae milisegundos');
foreach (at_reglas($res['aereos']) as $texto => $cumple) {
    t_eq($cumple, true, "Técnica perfecta (aéreos): {$texto}");
}
foreach (at_reglas($res['oseos']) as $texto => $cumple) {
    // la ósea del OI sin enmascarar da la sombra del OD (10 dB): eso es
    // del enmascaramiento, que la T02 todavía no evalúa
    if (strpos($texto, 'corresponden a la audición') !== false) {
        continue;
    }
    t_eq($cumple, true, "Técnica perfecta (óseos): {$texto}");
}
t_eq(array_column($res['aereos']['umbrales']['OD'], 'estimado'), array_fill(0, 10, 10), 'Técnica: umbrales aéreos OD estimados (9 frecuencias y la repetición)');
t_eq(array_column($res['aereos']['umbrales']['OI'], 'estimado'), array_fill(0, 10, 30), 'Técnica: umbrales aéreos OI estimados');
t_eq(array_column($res['aereos']['umbrales']['OD'], 'freq'), array_merge($aereos, [1000]), 'Técnica: la tabla va en el orden en que tomó los umbrales');
t_eq(array_column($res['aereos']['umbrales']['OD'], 'repeticion'), array_merge(array_fill(0, 9, false), [true]), 'Técnica: la repetición de 1 kHz es su propia fila');
t_eq(array_unique(array_column($res['oseos']['umbrales']['OI'], 'estado')), ['sombra'], 'Técnica: ósea OI sin enmascarar = curva sombra');
t_eq($res['oseos']['observaciones'], [], 'Técnica: ósea solo en el oído que la necesita, sin observaciones');
t_eq($res['orden']['hechas'], ['Umbrales aéreos', 'Umbrales óseos'], 'Técnica: pruebas reconocidas');
t_eq($res['orden']['reglas'][0]['cumple'], true, 'Técnica: aéreos antes que óseos');
t_true($res['puntaje']['total'] > 15 && $res['puntaje']['cumple'] === $res['puntaje']['total'] - 1, 'Técnica: puntaje (todo menos la sombra ósea)');

// --- El mismo examen en registro viejo: se reconstruye ---------------------
$viejo = new AtExaminador(false);
$viejo->instruccion('colocar_fonos');
$viejo->oidoCompleto(0, $aereos);
$viejo->oidoCompleto(1, $aereos);
$resViejo = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($viejo->logs, at_caso()), at_caso(), $params);
t_eq($resViejo['reconstruido'], true, 'Técnica: registro viejo queda reconstruido');
t_eq($resViejo['con_ms'], false, 'Técnica: registro viejo sin milisegundos');
t_eq(array_column($resViejo['aereos']['umbrales']['OD'], 'estimado'), array_fill(0, 10, 10), 'Técnica: reconstruido da los mismos umbrales OD');
t_eq(array_column($resViejo['aereos']['umbrales']['OI'], 'estimado'), array_fill(0, 10, 30), 'Técnica: reconstruido da los mismos umbrales OI');
$duracion = null;
foreach ($resViejo['aereos']['reglas'] as $r) {
    if (strpos($r['texto'], 'segundos') !== false) {
        $duracion = $r;
    }
}
t_true($duracion !== null && $duracion['cumple'] === null, 'Técnica: sin milisegundos la duración no se evalúa');

// --- Errores típicos --------------------------------------------------------
$mal = new AtExaminador(true);
$mal->instruccion('colocar_fonos');
$mal->oidoCompleto(1, $aereos, 50, false);   // oído peor, 50 dB, sin repetir 1 kHz
$mal->oidoCompleto(0, [1000, 2000, 4000, 3000, 6000, 8000, 500, 250, 125]);
$r = at_reglas(AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($mal->logs, at_caso()), at_caso(), $params)['aereos']);
t_true(at_falla($r, 'oído mejor'), 'Técnica: partir por el oído peor se marca');
t_true(at_falla($r, 'OI · Se parte en 1 kHz a 40'), 'Técnica: partir en 50 dB se marca');
t_true(at_falla($r, 'OI · Se repite 1 kHz'), 'Técnica: no repetir 1 kHz se marca');
t_true(at_falla($r, 'OD · Orden de frecuencias'), 'Técnica: frecuencias fuera de orden se marcan');
t_eq(at_falla($r, 'OD · Se parte en 1 kHz'), false, 'Técnica: el OD sí partió bien');

$sube = new AtExaminador(true);
$sube->instruccion('colocar_fonos');
$sube->oido(0);
$sube->frecuencia(1000);
$sube->umbral(40, ['sube10']);
$r = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($sube->logs, at_caso()), at_caso(), $params);
t_true(at_falla(at_reglas($r['aereos']), 'OD · Familiarización'), 'Técnica: subir 10 tras no responder (en la técnica) se marca');

$corto = new AtExaminador(true);
$corto->oido(0);
$corto->frecuencia(1000);
for ($i = 0; $i < 6; $i++) {
    $corto->tono(40, 0.4);
}
$r = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($corto->logs, at_caso()), at_caso(), $params);
$rr = at_reglas($r['aereos']);
t_true(at_falla($rr, 'segundos'), 'Técnica: estímulos de 0,4 s se marcan');
t_true(at_falla($rr, 'instrucción'), 'Técnica: tonos sin instrucción se marcan');

// Ósea en un oído sano: observación, la técnica se evalúa igual.
$sano = new AtExaminador(true);
$sano->instruccion('colocar_vibrador');
$sano->transductor('Oséa');
$sano->oidoCompleto(0, $oseos);
$r = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($sano->logs, at_caso()), at_caso(), $params);
t_eq(count($r['oseos']['observaciones']), 1, 'Técnica: ósea en el oído sano queda como observación');
t_true(isset($r['oseos']['oidos']['OD']), 'Técnica: y su técnica se evalúa igual');
t_true(at_falla(at_reglas($r['oseos']), 'umbrales de OI'), 'Técnica: falta la ósea del OI, que sí la necesitaba');

// Orden: óseos antes que aéreos.
$orden = new AtExaminador(true);
$orden->instruccion('colocar_vibrador');
$orden->transductor('Oséa');
$orden->oido(1);
$orden->tono(40);
$orden->instruccion('colocar_fonos');
$orden->transductor('Aerea');
$orden->tono(40);
$orden->instruccion('colocar_vibrador');
$orden->transductor('Oséa');
$orden->tono(40);
$orden->instruccion('colocar_fonos');
$orden->transductor('Aerea');
$orden->tono(40);
$r = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($orden->logs, at_caso()), at_caso(), $params);
t_eq($r['orden']['reglas'][0]['cumple'], false, 'Técnica: óseos antes que aéreos se marca');
t_eq(count($r['orden']['observaciones']), 1, 'Técnica: volver a una prueba anterior queda como observación');

// Sin audiómetro, nada que evaluar.
t_eq(AudiometriaTecnica::evaluar(AudiometriaRegistro::leer([], at_caso()), at_caso(), $params), null, 'Técnica: atención sin audiómetro');

// --- Vista: el docente ve los umbrales del paciente, el alumno no ----------
require_once dirname(__DIR__) . '/src/AudiometriaTecnicaVista.php';
$malRes = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($mal->logs, at_caso()), at_caso(), $params);
ob_start();
AudiometriaTecnicaVista::render($malRes, true);
$htmlDocente = (string) ob_get_clean();
ob_start();
AudiometriaTecnicaVista::render($malRes, false);
$htmlAlumno = (string) ob_get_clean();
t_true(strpos($htmlDocente, 'No cumple') !== false && strpos($htmlDocente, '<th style="text-align:left; padding:0.2rem 0.6rem 0.2rem 0;">Paciente</th>') !== false, 'Vista docente: cumple/no cumple y la columna del paciente');
t_true(strpos($htmlAlumno, 'Para revisar') !== false, 'Vista alumno: "Para revisar", no "No cumple"');
t_eq(strpos($htmlAlumno, 'No cumple'), false, 'Vista alumno: nunca "No cumple"');
t_eq(strpos($htmlAlumno, '>Paciente</th>'), false, 'Vista alumno: sin los umbrales del paciente');
t_eq(substr_count($htmlDocente, '<div') , substr_count($htmlDocente, '</div>'), 'Vista: divs balanceados');

// --- La mano y la carga del caso no cuentan como acciones del alumno -------
require_once dirname(__DIR__) . '/src/Metrics.php';
$filas = array_map(static function ($l) {
    return ['user_id' => 1, 'client_ts' => $l['client_ts'], 'action' => $l['action'], 'payload' => json_encode($l['payload'])];
}, $corto->logs);
$acciones = [];
foreach (Metrics::buildSessions(Metrics::decodeLogs($filas)) as $s) {
    foreach ($s['actions'] as $a) {
        $acciones[$a['action']] = true;
    }
}
t_true(isset($acciones['audio_stim_button']), 'Métricas: los estímulos sí son acciones');
t_eq(isset($acciones['audio_respuesta']), false, 'Métricas: la mano del paciente no es una acción del alumno');

// --- 2 de 3 son estímulos: tres seguidos al mismo nivel llegando desde abajo
$tres = new AtExaminador(true);
$tres->instruccion('colocar_fonos');
$tres->oido(0);
$tres->frecuencia(1000);
foreach ([40, 30, 20, 10, 0, 5, 10, 10, 10] as $db) {
    $tres->tono($db);
}
$r = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($tres->logs, at_caso()), at_caso(), $params);
t_eq($r['aereos']['umbrales']['OD'][0]['estimado'], 10, 'Técnica: tres estímulos seguidos a 10 dB llegando desde abajo cierran el umbral');
t_eq(at_falla(at_reglas($r['aereos']), 'OD · Familiarización'), false, 'Técnica: repetir estímulos en el mismo nivel no es un desvío de paso');


// --- Familiarización: casos que tienen que pasar sin desvíos ---------------
/** Caída simétrica (sin sombra): 60 dB en graves y 1 kHz, 80 dB en 2-3 kHz, sin respuesta desde 4 kHz. */
function at_caida(): array
{
    $od = [60, 60, 60, 60, 80, 80, 130, 130, 130];
    $filas = [];
    foreach ($od as $i => $v) {
        $filas[$i] = [$v, $v];
    }
    $filas = array_merge($filas, array_fill(0, 6, [130, 130]));
    return ['Aerea_mkg' => $filas, 'Osea_mkg' => $filas, 'Aerea' => $filas, 'Osea' => $filas];
}

function at_secuencia(AtExaminador $ex, int $hz, array $niveles): void
{
    $ex->frecuencia($hz);
    foreach ($niveles as $db) {
        $ex->tono($db);
    }
}

$caida = new AtExaminador(true, at_caida());
$caida->instruccion('colocar_fonos');
$caida->oido(0);
// 1 kHz: familiarización 40, 50 (sin respuesta) -> 60 responde; técnica.
at_secuencia($caida, 1000, [40, 50, 60, 50, 55, 60, 50, 55, 60]);
// 2 kHz: parte en 70 (60 + 10), no responde -> familiarización 80; técnica.
at_secuencia($caida, 2000, [70, 80, 70, 75, 80, 70, 75, 80]);
// 3 kHz: parte en 90 (80 + 10), responde; técnica.
at_secuencia($caida, 3000, [90, 80, 70, 75, 80, 70, 75, 80]);
// 4 kHz: parte en 90, sube de 10 en 10 hasta el tope (100) sin respuesta.
at_secuencia($caida, 4000, [90, 100]);
$r = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($caida->logs, at_caida()), at_caida(), $params);
$od = [];
foreach ($r['aereos']['oidos']['OD'] as $x) {
    $od[$x['texto']] = $x;
}
$pasos = null;
$cierre = null;
$inicio = null;
foreach ($od as $texto => $x) {
    if (strpos($texto, 'Familiarización') === 0) {
        $pasos = $x;
    } elseif (strpos($texto, 'Se verifica el umbral') === 0) {
        $cierre = $x;
    } elseif (strpos($texto, 'Cada frecuencia nueva') === 0) {
        $inicio = $x;
    }
}
t_eq($pasos['cumple'], true, 'Familiarización: +10 hasta responder y después -10/+5, sin desvíos (' . $pasos['detalle'] . ')');
t_eq($inicio['cumple'], true, 'Familiarización: cada frecuencia parte 10 sobre la anterior aunque no responda (' . $inicio['detalle'] . ')');
t_eq($cierre['cumple'], true, 'Familiarización: llegar al tope sin respuesta cierra la frecuencia (' . $cierre['detalle'] . ')');
$u = array_column($r['aereos']['umbrales']['OD'], 'estado', 'freq');
t_eq($u[4000] ?? null, 'coincide', 'Familiarización: sin respuesta al tope corresponde a un oído sin respuesta');
t_eq(array_column($r['aereos']['umbrales']['OD'], 'estimado', 'freq'), [1000 => 60, 2000 => 80, 3000 => 80, 4000 => null], 'Familiarización: umbrales de la caída');

// Familiarización subiendo de 5 en 5: desvío.
$cinco = new AtExaminador(true, at_caida());
$cinco->instruccion('colocar_fonos');
$cinco->oido(0);
at_secuencia($cinco, 1000, [40, 45, 50, 55, 60, 50, 55, 60, 50, 55, 60]);
$r = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($cinco->logs, at_caida()), at_caida(), $params);
t_true(at_falla(at_reglas($r['aereos']), 'OD · Familiarización'), 'Familiarización: subir de 5 antes de la primera respuesta es un desvío');

// Vía ósea en 250 Hz: el equipo llega a 45 dB; desde 40 no se puede subir 10.
$tope = new AtExaminador(true, at_caida());
$tope->instruccion('colocar_vibrador');
$tope->transductor('Oséa');
$tope->oido(0);
at_secuencia($tope, 250, [40, 45]);
$r = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($tope->logs, at_caida()), at_caida(), $params);
t_eq(at_falla(at_reglas($r['oseos']), 'OD · Familiarización'), false, 'Familiarización: subir al tope del equipo (45 dB en 250 Hz óseo) no es un desvío');
t_eq(at_falla(at_reglas($r['oseos']), 'OD · Se verifica el umbral'), false, 'Familiarización: tope del equipo sin respuesta cierra la frecuencia');

// Los topes son los del audiómetro (intency_dict del cliente).
$cfg = dirname(__DIR__, 2) . '/resources/json/config_audiometer.json';
if (is_file($cfg)) {
    $dict = json_decode((string) file_get_contents($cfg), true)['intency_dict'];
    foreach (['aereos' => 0, 'oseos' => 1] as $via => $trans) {
        foreach (AudiometriaTecnica::TOPES[$via] as $hz => $tope) {
            $fila = $dict[(string) $hz][$trans];
            t_eq($tope, [$fila[0][1], $fila[1][0]], "Topes {$via} {$hz} Hz: iguales a config_audiometer.json");
        }
    }
} else {
    t_true(true, 'Topes: sin config_audiometer.json a mano -- comparación omitida');
}

// --- Porcentaje de logro ---------------------------------------------------
$p = $res['puntaje'];
t_eq($p['pct'], (int) round(100 * $p['cumple'] / $p['total']), 'Logro: el porcentaje sale de pasos cumplidos sobre evaluables');
t_eq($res['aereos']['puntaje']['pct'], 100, 'Logro: examen aéreo al pie de la letra = 100 %');
t_eq(array_keys($res['aereos']['puntaje_oidos']), ['OD', 'OI'], 'Logro: también por oído');
t_eq(AudiometriaTecnica::sumar([['reglas' => []]])['pct'], null, 'Logro: sin pasos evaluables no hay porcentaje');
ob_start();
AudiometriaTecnicaVista::render($res, false);
$html = (string) ob_get_clean();
t_true(strpos($html, (string) $p['pct'] . ' %') !== false, 'Logro: la vista muestra el porcentaje general');
t_eq(substr_count($html, '<details'), substr_count($html, '</details>'), 'Logro: secciones plegables balanceadas');

// No repetir 1 kHz descuenta una vez: el orden de frecuencias igual se cumple.
$sinRepetir = new AtExaminador(true);
$sinRepetir->instruccion('colocar_fonos');
$sinRepetir->oidoCompleto(0, $aereos, 40, false);
$rr = at_reglas(AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($sinRepetir->logs, at_caso()), at_caso(), $params)['aereos']);
t_true(at_falla($rr, 'OD · Se repite 1 kHz'), 'Logro: sin repetir 1 kHz se marca');
t_eq(at_falla($rr, 'OD · Orden de frecuencias'), false, 'Logro: y no descuenta además el orden');

// --- Repetir sin necesidad: advertencia con el tiempo, no descuenta ---------
$repite = new AtExaminador(true);
$repite->instruccion('colocar_fonos');
$repite->oido(0);
$previo = null;
foreach ([1000, 2000, 3000, 2000, 1000, 4000, 6000, 8000, 500, 250, 125, 1000] as $i => $hz) {
    $repite->frecuencia($hz);
    $u = $repite->umbral($previo === null ? 40 : $previo + 10);
    $previo = $u;
}
$repite->oidoCompleto(1, $aereos);
$repite->oido(0);
$repite->frecuencia(4000);
$repite->umbral(20);
$r = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($repite->logs, at_caso()), at_caso(), $params);
t_eq($r['aereos']['puntaje']['pct'], 100, 'Repetir sin necesidad: no descuenta (' . json_encode(array_keys(array_filter(at_reglas($r['aereos']), static function ($c) { return $c === false; })), JSON_UNESCAPED_UNICODE) . ')');
$obs = implode(' ', $r['aereos']['observaciones']);
t_true(strpos($obs, 'Repitió sin necesidad OD 2 kHz (ya verificado en 10 dB), OD 1 kHz (ya verificado en 10 dB) y OD 4 kHz') !== false, 'Repetir sin necesidad: dice cuáles (' . $obs . ')');
t_true(preg_match('/habría ganado (\d+ min( \d+ s)?|\d+ s)\./', $obs) === 1, 'Repetir sin necesidad: dice cuánto tiempo habría ganado');
$filas = $r['aereos']['umbrales']['OD'];
t_eq(array_column(array_filter($filas, static function ($f) { return $f['innecesaria']; }), 'freq'), [2000, 1000, 4000], 'Repetir sin necesidad: marcadas en la tabla, en orden');
t_eq(array_sum(array_column($filas, 'repeticion')), 4, 'Repetir sin necesidad: la repetición final de 1 kHz no es innecesaria');
t_eq(AudiometriaTecnica::tiempo(80), '1 min 20 s', 'Tiempo: minutos y segundos');
t_eq(AudiometriaTecnica::tiempo(45), '45 s', 'Tiempo: solo segundos');

// Volver a una frecuencia que no había verificado no es repetir sin necesidad.
$vuelve = new AtExaminador(true);
$vuelve->instruccion('colocar_fonos');
$vuelve->oido(0);
at_secuencia($vuelve, 1000, [40, 30, 20, 10, 0, 5, 10, 0, 5, 10]);
at_secuencia($vuelve, 2000, [20, 10, 0, 5]);   // se va sin verificar
at_secuencia($vuelve, 3000, [20, 10, 0, 5, 10, 0, 5, 10]);
at_secuencia($vuelve, 2000, [20, 10, 0, 5, 10, 0, 5, 10]);
$r = AudiometriaTecnica::evaluar(AudiometriaRegistro::leer($vuelve->logs, at_caso()), at_caso(), $params);
t_eq($r['aereos']['observaciones'], [], 'Volver a verificar: no es repetir sin necesidad');
t_true(at_falla(at_reglas($r['aereos']), 'OD · Se verifica el umbral'), 'Volver a verificar: irse sin verificar igual se marca');

// Registros repartidos por cita, decodificando una sola vez (deAtenciones).
$porCita = AudiometriaTecnica::logsPorCita([
    ['client_ts' => 't1', 'action' => 'audio_freq_change', 'payload' => '{"appointment_id":"4","freq":1000}'],
    ['client_ts' => 't2', 'action' => 'audio_freq_change', 'payload' => ['appointment_id' => 5]],
    ['client_ts' => 't3', 'action' => 'chat_send', 'payload' => '{"appointment_id":4}'],
    ['client_ts' => 't4', 'action' => 'audio_stim_button', 'payload' => '{"appointment_id":9}'],
    ['client_ts' => 't5', 'action' => 'audio_stim_button', 'payload' => null],
], [4, 5]);
t_eq(array_keys($porCita), [4, 5], 'Técnica: solo las citas pedidas (el id puede venir como texto)');
t_eq(count($porCita[4]), 1, 'Técnica: lo que no es del audiómetro no entra');
t_eq($porCita[4][0]['payload']['freq'], 1000, 'Técnica: payload decodificado');
