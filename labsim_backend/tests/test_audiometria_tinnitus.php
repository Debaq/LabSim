<?php

declare(strict_types=1);

/**
 * Indicador de la tinnitumetría (T03): AudiometriaRegistro arma la línea de
 * tiempo y AudiometriaTinnitus la evalúa. Una tinnitumetría hecha al pie de
 * la letra cumple todo; los errores típicos aparecen en su regla.
 */

require_once dirname(__DIR__) . '/src/AudiometriaTecnica.php';

/** OD normal (10), OI con caída en agudos; acúfeno en OI, 4 kHz. */
function tin_caso(array $tinnitus = []): array
{
    $oi = [10, 10, 10, 15, 30, 45, 50, 55, 60];
    $filas = [];
    foreach ($oi as $u) {
        $filas[] = [10, $u];
    }
    return [
        'Aerea_mkg' => $filas, 'Osea_mkg' => $filas, 'Aerea' => $filas, 'Osea' => $filas,
        'LDL' => array_fill(0, 9, [100, 100]),
        'Tinnitus' => $tinnitus + ['presente' => true, 'lateralidad' => 'unilateral', 'oido' => 'oi',
            'ruido' => 'Pitido', 'frecuencia' => 4000, 'permanente' => true],
    ];
}

function tin_verdad(): array
{
    return ['presente' => true, 'pulsatil' => false, 'lateralidad' => 'unilateral', 'oidos' => [1],
        'oido_comparacion' => 0, 'tipo' => 'tono', 'freq' => 4000, 'sonoridad_sl' => 6,
        'nme_sl' => 20, 'inhibicion' => 'parcial', 'mantiene' => false, 'sorteados' => []];
}

final class TinExaminador
{
    public $logs = [];
    private $t;
    private $estado;

    public function __construct(?array $verdad)
    {
        $this->t = strtotime('2026-11-06 10:00:00');
        $this->estado = [
            'prueba' => 'Umbrales', 'freq' => '1000 Hz', 'step' => 5, 'instruccion' => null,
            'canales' => [
                ['on' => false, 'invertido' => false, 'intensity' => '20 dB HL', 'stim' => 'Tono', 'output' => 'Derecha', 'trans' => 'Aerea', 'contin' => 'Continuo'],
                ['on' => false, 'invertido' => false, 'intensity' => '20 dB HL', 'stim' => 'Narrow Band Noise', 'output' => 'Izquierda', 'trans' => 'Aerea', 'contin' => 'Continuo'],
            ],
        ];
        $this->log('audio_caso_cargado', ['estado' => $this->estado, 'acufeno' => $verdad]);
    }

    public function log(string $accion, array $payload, float $dt = 0.5): void
    {
        $this->t += $dt;
        $payload['v'] = 2;
        $ms = (int) floor(round($this->t, 3) * 1000);
        $ts = date('Y-m-d H:i:s', intdiv($ms, 1000)) . sprintf('.%03d', $ms % 1000);
        $this->logs[] = ['client_ts' => $ts, 'action' => $accion, 'payload' => $payload];
    }

    public function decir(string $cmd): void
    {
        $this->estado['instruccion'] = $cmd;
        $this->log('audio_talkback_press', ['command' => $cmd]);
    }

    public function contesta(string $pregunta, string $respuesta, array $extra = []): void
    {
        $this->decir($pregunta);
        $this->log('audio_acufeno_respuesta', ['pregunta' => $pregunta, 'respuesta' => $respuesta] + $extra, 2.0);
    }

    public function paso(int $db): void
    {
        $this->estado['step'] = $db;
        $this->log('audio_step_change', ['step' => $db]);
    }

    public function canal(int $ch, array $cambios): void
    {
        foreach ($cambios as $k => $v) {
            if ($k === 'freq') {
                $this->estado['freq'] = "{$v} Hz";
                $this->log('audio_freq_change', ['freq' => $v]);
            } elseif ($k === 'int') {
                $this->estado['canales'][$ch]['intensity'] = "{$v} dB HL";
                $this->log('audio_intensity_change', ['ch' => $ch, 'intensity' => $v, 'freq' => (int) $this->estado['freq']]);
            } elseif ($k === 'stim') {
                $this->estado['canales'][$ch]['stim'] = $v;
                $this->log('audio_stim_select', ['ch' => $ch, 'stim' => $v]);
            } elseif ($k === 'output') {
                $this->estado['canales'][$ch]['output'] = $v;
                $this->log('audio_output_select', ['ch' => $ch, 'output' => $v]);
            }
        }
    }

    public function prender(int $ch, bool $on, float $dt = 0.5): void
    {
        $this->estado['canales'][$ch]['on'] = $on;
        $this->log('audio_stim_button', ['ch' => $ch, 'play' => $on, 'estado' => $this->estado], $dt);
    }

    public function mano(bool $arriba): void
    {
        $this->log('audio_respuesta', ['mano' => $arriba], 0.2);
    }

    public function esperar(float $s): void
    {
        $this->t += $s;
    }
}

/**
 * La técnica completa. $err: 'oido' (compara en el oído del acúfeno),
 * 'paso5' (iguala la intensidad de a 5 dB), 'sin_octava', 'ir_corta',
 * 'nme_tono' (el NME con tono en vez de ruido), 'ir_sin_inicio' (va directo
 * al minuto, sin "solo escuche el mío"), 'ir_poco' (sube 5 dB en vez de 15),
 * 'ir_arriba' (la octava de arriba), 'hoy' (como desde el 2026-11-13: sin
 * "Hasta que no escuche su ruido", el NME es "solo escuche el mío"). Sin
 * 'hoy' es una atención de antes, con el NME de la mano.
 */
function tin_examen(array $err = [], $verdad = 'de fábrica'): array
{
    $x = new TinExaminador($verdad === 'de fábrica' ? tin_verdad() : $verdad);
    $comparacion = in_array('oido', $err, true) ? 'Izquierda' : 'Derecha';
    $x->canal(0, ['output' => $comparacion, 'int' => 60]);
    $x->decir('acufeno_cual_se_parece');
    foreach ([2000, 4000, 6000] as $hz) {
        $x->canal(0, ['freq' => $hz]);
        $x->prender(0, true);
        $x->prender(0, false, 1.5);
    }
    $comp = array_map(static function ($hz) use ($comparacion) {
        return ['stim' => 'Tono', 'freq' => $hz, 'oido' => $comparacion === 'Derecha' ? 0 : 1];
    }, [2000, 4000, 6000]);
    $x->contesta('acufeno_cual', 'elsegundo', ['comparados' => $comp]);
    $x->decir('acufeno_cual_se_parece');
    $octavas = in_array('sin_octava', $err, true) ? [4000] : [8000, 4000];
    foreach ($octavas as $hz) {
        $x->canal(0, ['freq' => $hz]);
        $x->prender(0, true);
        $x->prender(0, false, 1.5);
    }
    if (!in_array('sin_octava', $err, true)) {
        $x->contesta('acufeno_cual', 'elsegundo', ['comparados' => [
            ['stim' => 'Tono', 'freq' => 8000, 'oido' => 0], ['stim' => 'Tono', 'freq' => 4000, 'oido' => 0]]]);
    }

    // intensidad: desde bajo el umbral, de a 1 dB
    $x->decir('acufeno_igual_fuerte');
    $x->canal(0, ['freq' => 4000, 'int' => 5]);
    $paso = in_array('paso5', $err, true) ? 5 : 1;
    $x->paso($paso);
    $x->prender(0, true);
    for ($db = 5 + $paso; $db <= 16; $db += $paso) {
        $x->canal(0, ['int' => $db]);
    }
    $x->mano(true);
    $x->prender(0, false);
    $x->mano(false);

    // NME: banda estrecha de 4 kHz en OI
    if (!in_array('hoy', $err, true)) {
    $x->decir('acufeno_deje_de_escuchar');
    $x->paso(5);
    $x->canal(1, ['stim' => in_array('nme_tono', $err, true) ? 'Tono' : 'Narrow Band Noise', 'output' => 'Izquierda', 'int' => 50]);
    $x->prender(1, true);
    for ($db = 55; $db <= 70; $db += 5) {
        $x->canal(1, ['int' => $db]);
    }
    $x->mano(true);
    $x->prender(1, false);
    $x->mano(false);
    }

    // inhibición residual: tono una octava abajo en OI, se sube hasta que
    // solo escucha el estímulo (50 dB HL: 20 SL sobre 30), +15 y un minuto
    $hzIr = in_array('ir_arriba', $err, true) ? 8000 : 2000;
    $refIr = $hzIr === 8000 ? 80 : 50;
    $finIr = $refIr + (in_array('ir_poco', $err, true) ? 5 : 15);
    if (in_array('ir_sin_inicio', $err, true)) {
        $x->decir('acufeno_un_minuto');
        $x->canal(0, ['output' => 'Izquierda', 'freq' => $hzIr, 'int' => $finIr]);
        $x->prender(0, true);
    } else {
        $x->decir('acufeno_solo_el_mio');
        $x->canal(0, ['output' => 'Izquierda', 'freq' => $hzIr, 'int' => $refIr - 15]);
        $x->prender(0, true);
        for ($db = $refIr - 10; $db <= $refIr; $db += 5) {
            $x->canal(0, ['int' => $db]);
        }
        $x->log('audio_acufeno_respuesta', ['pregunta' => 'acufeno_solo_el_mio', 'respuesta' => 'ahorasoloescuchoelsuyo'], 0.3);
        for ($db = $refIr + 5; $db <= $finIr; $db += 5) {
            $x->canal(0, ['int' => $db]);
        }
        $x->decir('acufeno_un_minuto');
    }
    $dur = in_array('ir_corta', $err, true) ? 30.0 : 61.0;
    $x->prender(0, true);
    $x->prender(0, false, $dur);
    $x->contesta('acufeno_como_esta', 'seescuchamasbajito', ['corrida' => ['duracion_s' => $dur, 'desde_s' => 2.0]]);
    $x->esperar(60);
    $x->contesta('acufeno_como_esta', 'igualqueantes', ['corrida' => ['duracion_s' => $dur, 'desde_s' => 64.0]]);
    return $x->logs;
}

function tin_evaluar(array $logs, ?array $caso = null): ?array
{
    $caso = $caso ?? tin_caso();
    $reg = AudiometriaRegistro::leer($logs, $caso);
    return AudiometriaTecnica::evaluar($reg, $caso, AudiometriaTecnica::parametrosDefault());
}

function tin_regla(array $sec, string $empieza): ?array
{
    foreach ($sec['reglas'] as $r) {
        if (strpos($r['texto'], $empieza) === 0) {
            return $r;
        }
    }
    return null;
}

// ---- la técnica completa cumple todo -------------------------------------
$res = tin_evaluar(tin_examen());
t_true($res !== null && $res['tinnitus'] !== null, 'T03: hay sección de tinnitumetría');
$sec = $res['tinnitus'];
foreach ($sec['reglas'] as $r) {
    t_true($r['cumple'] === true, 'T03 completa cumple: ' . $r['texto'] . ' -- ' . $r['detalle']);
}
t_true(count($sec['reglas']) >= 12, 'T03: evalúa las cuatro partes (' . count($sec['reglas']) . ' reglas)');
t_eq($sec['puntaje']['pct'], 100, 'T03 completa: 100 %');
t_true(in_array('Tinnitumetría', $res['orden']['hechas'], true), 'T00 reconoce la tinnitumetría');

// ---- errores típicos ------------------------------------------------------
$sec = tin_evaluar(tin_examen(['oido']))['tinnitus'];
t_eq(tin_regla($sec, 'Los sonidos de comparación')['cumple'], false, 'T03: comparar en el oído del acúfeno');

$sec = tin_evaluar(tin_examen(['paso5']))['tinnitus'];
t_eq(tin_regla($sec, 'Intensidad: se sube de 1 en 1')['cumple'], false, 'T03: igualar de a 5 dB');

$sec = tin_evaluar(tin_examen(['sin_octava']))['tinnitus'];
t_eq(tin_regla($sec, 'Control de octava')['cumple'], false, 'T03: sin control de octava');

$sec = tin_evaluar(tin_examen())['tinnitus'];
t_eq(tin_regla($sec, 'Intensidad: el paciente avisa')['detalle'],
    'Igualó con 16 dB HL en OD a 4 kHz: 6 dB SL sobre el umbral de ese oído (10 dB HL).', 'T03: la sonoridad en dB SL');
t_eq(tin_regla($sec, 'NME: se sube')['detalle'],
    'Lo dejó de oír con 70 dB HL en OI: 20 dB SL sobre el umbral de ese oído (50 dB HL).', 'T03: el NME en dB SL');

// lo que debería anotar, según las respuestas, y lo del paciente
$res = [];
foreach ($sec['resultado'] as $f) {
    $res[$f['parte']] = $f;
}
t_eq($res['Tono']['anotar'], 'Tono puro de 4 kHz', 'T03 resultado: tono');
t_eq($res['Tono']['paciente'], 'Tono puro de 4 kHz', 'T03 resultado: tono del paciente');
t_true(strpos($res['Intensidad']['anotar'], '16 dB HL en OD a 4 kHz → 6 dB SL') === 0, 'T03 resultado: intensidad -- ' . $res['Intensidad']['anotar']);
t_eq($res['Intensidad']['paciente'], '6 dB SL (16 dB HL en OD).', 'T03 resultado: intensidad del paciente');
t_true(strpos($res['NME']['anotar'], '70 dB HL en OI a 4 kHz → 20 dB SL') === 0, 'T03 resultado: NME -- ' . $res['NME']['anotar']);
t_eq($res['NME']['paciente'], '20 dB SL (70 dB HL en OI).', 'T03 resultado: NME del paciente');
t_eq($res['Inhibición residual']['anotar'], 'Parcial, no se mantiene al minuto.', 'T03 resultado: inhibición');
t_eq($res['Inhibición residual']['paciente'], 'Parcial, no se mantiene al minuto', 'T03 resultado: inhibición del paciente');

// el NME con tono: la mano no sube y el indicador dice qué sonó
$x = tin_examen(['nme_tono']);
$x = array_values(array_filter($x, static function ($l) {
    // sin la mano del NME: con tono el paciente no la levanta
    static $nme = false;
    if ($l['action'] === 'audio_talkback_press') {
        $nme = $l['payload']['command'] === 'acufeno_deje_de_escuchar';
    }
    return !($nme && $l['action'] === 'audio_respuesta');
}));
$sec = tin_evaluar($x)['tinnitus'];
$r = tin_regla($sec, 'NME: en el oído del acúfeno');
t_eq($r['cumple'], false, 'T03: NME con tono no cumple');
t_true(strpos($r['detalle'], 'Tono en OI (hasta 70 dB HL)') !== false, 'T03: NME con tono dice qué sonó -- ' . $r['detalle']);
$r = tin_regla($sec, 'NME: se sube');
t_eq($r['cumple'], false, 'T03: NME con tono no se mide');
t_true(strpos($r['detalle'], 'no podía taparlo') !== false, 'T03: NME con tono dice por qué -- ' . $r['detalle']);

$sec = tin_evaluar(tin_examen())['tinnitus'];
t_eq(tin_regla($sec, 'Inhibición residual: se parte')['detalle'],
    'Dijo "ahora solo escucho el suyo" con 50 dB HL en OI a 2 kHz.', 'T03: nivel de partida de la inhibición');
t_eq(tin_regla($sec, 'Inhibición residual: se sube 15')['detalle'],
    'Solo el estímulo con 50 dB HL; después llegó a 65 dB HL.', 'T03: +15 de la inhibición');

$sec = tin_evaluar(tin_examen(['ir_sin_inicio']))['tinnitus'];
$r = tin_regla($sec, 'Inhibición residual: se parte');
t_eq($r['cumple'], false, 'T03: inhibición sin "solo escuche el mío"');
t_eq($r['detalle'], 'No se pidió: se pasó directo al minuto.', 'T03: inhibición sin inicio dice por qué');
t_eq(tin_regla($sec, 'Inhibición residual: se sube 15')['cumple'], null, 'T03: sin nivel de partida no se compara el +15');

$sec = tin_evaluar(tin_examen(['ir_poco']))['tinnitus'];
t_eq(tin_regla($sec, 'Inhibición residual: se sube 15')['cumple'], false, 'T03: inhibición con +5 dB');

$sec = tin_evaluar(tin_examen(['ir_arriba']))['tinnitus'];
t_eq(tin_regla($sec, 'Inhibición residual: una octava abajo')['cumple'], false, 'T03: inhibición en la octava de arriba');

// sin inhibición: falta, salvo que 15 dB sobre el NME (20 SL) en la octava
// de abajo (2 kHz en OI: 30 + 20 = 50 dB HL) lleguen a la molestia
$x = array_values(array_filter(tin_examen(), static function ($l) {
    static $ir = false;
    if ($l['action'] === 'audio_talkback_press') {
        $c = $l['payload']['command'];
        if (in_array($c, ['acufeno_solo_el_mio', 'acufeno_un_minuto'], true)) {
            $ir = true;
        } elseif ($c !== 'acufeno_como_esta') {
            $ir = false;
        }
    }
    return !$ir;
}));
$sec = tin_evaluar($x)['tinnitus'];
t_eq(tin_regla($sec, 'Se hacen las cuatro partes')['detalle'], 'Faltó: inhibición residual.', 'T03: sin inhibición que cabía, falta');
$molesta = tin_caso();
$molesta['LDL'][4] = [100, 60];
$sec = tin_evaluar($x, $molesta)['tinnitus'];
t_eq(tin_regla($sec, 'Se hacen las cuatro partes')['cumple'], true, 'T03: sin inhibición que no cabía bajo la molestia, no se exige');
t_true(strpos(implode(' ', $sec['observaciones']), 'Subir 15 dB llegaba a la molestia') !== false, 'T03: dice por qué no se hizo');

$sec = tin_evaluar(tin_examen(['ir_corta']))['tinnitus'];
t_eq(tin_regla($sec, 'Inhibición residual: el estímulo dura un minuto')['cumple'], false, 'T03: inhibición de medio minuto');

// ---- hoy: el NME es "solo escuche el mío" (2026-11-13) ----------------------
$sec = tin_evaluar(tin_examen(['hoy']))['tinnitus'];
foreach ($sec['reglas'] as $r) {
    t_true($r['cumple'] === true, 'T03 hoy cumple: ' . $r['texto'] . ' -- ' . $r['detalle']);
}
t_eq($sec['puntaje']['pct'], 100, 'T03 hoy: 100 %');
t_eq(tin_regla($sec, 'NME: con "Solo escuche el mío"')['detalle'],
    'Solo escuchó el estímulo con 50 dB HL en OI a 2 kHz: 20 dB SL sobre el umbral de ese oído (30 dB HL).', 'T03 hoy: el NME en dB SL');
t_eq(tin_regla($sec, 'Inhibición residual: se parte'), null, 'T03 hoy: el paso de partida es la regla del NME');
$res = [];
foreach ($sec['resultado'] as $f) {
    $res[$f['parte']] = $f;
}
t_true(strpos($res['NME']['anotar'], '50 dB HL en OI a 2 kHz → 20 dB SL') === 0, 'T03 hoy resultado: NME -- ' . $res['NME']['anotar']);

$sec = tin_evaluar(tin_examen(['hoy', 'ir_sin_inicio']))['tinnitus'];
t_eq(tin_regla($sec, 'Se hacen las cuatro partes')['detalle'], 'Faltó: NME.', 'T03 hoy: sin "solo escuche el mío" falta el NME');

// se pidió, pero el paciente nunca lo dijo (el estímulo no le tapó el acúfeno)
$x = array_values(array_filter(tin_examen(['hoy']), static function ($l) {
    return !($l['action'] === 'audio_acufeno_respuesta' && ($l['payload']['pregunta'] ?? '') === 'acufeno_solo_el_mio');
}));
$r = tin_regla(tin_evaluar($x)['tinnitus'], 'NME: con "Solo escuche el mío"');
t_eq($r['cumple'], false, 'T03 hoy: sin "solo escucho el suyo" no hay NME');
t_true(strpos($r['detalle'], 'El paciente no dijo que solo escuchara') === 0, 'T03 hoy: dice qué pasó -- ' . $r['detalle']);

// ---- sin acúfeno, pulsátil, y app anterior sin la verdad -------------------
$sin = tin_caso(['presente' => false]);
$sec = tin_evaluar(tin_examen([], ['presente' => false]), $sin)['tinnitus'];
t_eq($sec['reglas'], [], 'T03 sin acúfeno: no evalúa pasos');
t_eq(count($sec['observaciones']), 1, 'T03 sin acúfeno: lo advierte');

$puls = tin_caso(['pulsatil' => true]);
$sec = tin_evaluar(tin_examen([], ['pulsatil' => true] + tin_verdad()), $puls)['tinnitus'];
t_eq($sec['reglas'][0]['cumple'], false, 'T03 pulsátil: no se iguala');

$sec = tin_evaluar(tin_examen([], null), tin_caso())['tinnitus'];
t_true(tin_regla($sec, 'Los sonidos de comparación')['cumple'] === true, 'T03 sin verdad en el registro: oído desde la ficha');
