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
 * 'paso5' (iguala la intensidad de a 5 dB), 'sin_octava', 'ir_corta'.
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
    $x->decir('acufeno_deje_de_escuchar');
    $x->paso(5);
    $x->canal(1, ['stim' => 'Narrow Band Noise', 'output' => 'Izquierda', 'int' => 50]);
    $x->prender(1, true);
    for ($db = 55; $db <= 70; $db += 5) {
        $x->canal(1, ['int' => $db]);
    }
    $x->mano(true);
    $x->prender(1, false);
    $x->mano(false);

    // inhibición residual: tono una octava arriba, NME + 10, un minuto en OI
    $x->decir('acufeno_un_minuto');
    $x->canal(0, ['output' => 'Izquierda', 'freq' => 8000, 'int' => 80]);
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

$sec = tin_evaluar(tin_examen(['ir_corta']))['tinnitus'];
t_eq(tin_regla($sec, 'Inhibición residual: el estímulo dura un minuto')['cumple'], false, 'T03: inhibición de medio minuto');

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
