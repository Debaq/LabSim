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

    public function __construct(bool $v2)
    {
        $this->v2 = $v2;
        $this->t = strtotime('2026-10-08 10:00:00');
        $this->caso = new AudiometriaPaciente(at_caso());
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
t_eq(array_column($res['aereos']['umbrales']['OD'], 'estimado'), array_fill(0, 9, 10), 'Técnica: umbrales aéreos OD estimados');
t_eq(array_column($res['aereos']['umbrales']['OI'], 'estimado'), array_fill(0, 9, 30), 'Técnica: umbrales aéreos OI estimados');
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
t_eq(array_column($resViejo['aereos']['umbrales']['OD'], 'estimado'), array_fill(0, 9, 10), 'Técnica: reconstruido da los mismos umbrales OD');
t_eq(array_column($resViejo['aereos']['umbrales']['OI'], 'estimado'), array_fill(0, 9, 30), 'Técnica: reconstruido da los mismos umbrales OI');
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
