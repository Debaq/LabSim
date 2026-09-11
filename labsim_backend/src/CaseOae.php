<?php

declare(strict_types=1);

require_once __DIR__ . '/CaseBuilder.php';
require_once __DIR__ . '/CaseProfile.php';

/**
 * Las cuatro pruebas de OEA del caso, cada una en sus propias bandas.
 *
 * El caso guarda UN perfil de emisión por oído (type + umbral +
 * `desviaciones` en las bandas de CaseBuilder::EOAS_FREQS) y el cliente
 * arma con eso las cuatro pruebas, que no comparten ni frecuencias ni
 * escala: el DP-grama va en dB SPL del producto de distorsión sobre un piso
 * de -22, el TEOAE en dB SPL de respuesta sobre un piso de canal, el SFOAE
 * en magnitud de emisión y el SOAE es un espectro en silencio, sin
 * estímulo. Mostrar una sola curva de "desviación" era mostrar un cuarto
 * del examen.
 *
 * Los normativos son los de resources/oae/normative_data.json (un test los
 * compara contra ese archivo, que no se despliega con el backend). Las
 * bandas normales del DP-grama vienen de ahí tal cual; para TEOAE y SFOAE,
 * que no traen banda, se construye con el mismo criterio con el que se
 * juzgan: desde el piso + la relación señal/ruido mínima hasta la respuesta
 * esperada con margen.
 */
final class CaseOae
{
    /** Espejo de teoae.default en resources/oae/normative_data.json. */
    public const TEOAE = [
        'bandas' => [1000, 1500, 2000, 3000, 4000],
        'esperado' => [1000 => 8.0, 1500 => 10.0, 2000 => 12.0, 3000 => 11.0, 4000 => 9.0],
        'min_snr_db' => 6.0,
        'piso_por_barrido_db' => 14.0,
        'barridos' => 260,
    ];

    /** Espejo de dpoae.default. `normal` es la banda normativa por f2. */
    public const DPOAE = [
        'bandas' => [1000, 1500, 2000, 3000, 4000, 6000, 8000],
        'normal' => [
            1000 => [-5.0, 13.0], 1500 => [-3.0, 15.0], 2000 => [-1.0, 16.0],
            3000 => [0.0, 17.0], 4000 => [-1.0, 16.0], 6000 => [-4.0, 13.0], 8000 => [-8.0, 9.0],
        ],
        'pico_f2_hz' => 3000,
        'pico_db' => 12.0,
        'rolloff_grave_db_oct' => 4.0,
        'rolloff_agudo_db_oct' => 7.0,
        'piso_db' => -22.0,
        'piso_subida_grave_db_oct' => 8.0,
        'min_sobre_ruido_db' => 6.0,
    ];

    /** Espejo de sfoae.default. */
    public const SFOAE = [
        'bandas' => [500, 1000, 1500, 2000, 3000, 4000],
        'esperado' => [500 => 3.0, 1000 => 6.0, 1500 => 6.5, 2000 => 5.0, 3000 => 3.5, 4000 => 2.0],
        'piso_db' => -12.0,
        'min_snr_db' => 6.0,
    ];

    /** Espejo de soae.default, solo lo que hace falta para dibujar el espectro. */
    public const SOAE = [
        'espectro_hz' => [500, 7000],
        'piso_db' => -8.0,
        'piso_subida_grave_db_oct' => 9.0,
        'piso_subida_agudo_db_oct' => 2.0,
        'min_snr_db' => 3.0,
        'prevalencia_pct' => 45,
        // Dónde pueden aparecer picos espontáneos: fuera de esa banda no se
        // buscan (peak_freq_min_hz / peak_freq_max_hz en el JSON).
        'picos_hz' => [700, 4500],
    ];

    /**
     * Piso de ruido del TEOAE ya promediado: el del JSON es POR BARRIDO y
     * baja ~1/raíz(N) al promediar (el comentario del propio JSON lo dice).
     */
    public static function pisoTeoae(): float
    {
        return self::TEOAE['piso_por_barrido_db'] - 10 * log10(sqrt((float) self::TEOAE['barridos']));
    }

    /** Piso del DP-grama en una f2: sube hacia los graves. */
    public static function pisoDpoae(float $hz): float
    {
        $octavasBajo = max(0.0, log(4000.0 / max(1.0, $hz), 2));
        return self::DPOAE['piso_db'] + $octavasBajo * self::DPOAE['piso_subida_grave_db_oct'] * 0.5;
    }

    /**
     * Respuesta esperada del DP-grama en un oído SANO: campana centrada en
     * peak_f2_hz con caída distinta hacia graves y agudos.
     */
    public static function dpEsperado(float $hz): float
    {
        $oct = log($hz / self::DPOAE['pico_f2_hz'], 2);
        $caida = $oct < 0
            ? abs($oct) * self::DPOAE['rolloff_grave_db_oct']
            : $oct * self::DPOAE['rolloff_agudo_db_oct'];
        return self::DPOAE['pico_db'] - $caida;
    }

    /**
     * Atenuación (dB) que el perfil del oído le pone a cada banda: la MISMA
     * ley que aplica el cliente (CaseProfile::loadedOaeAttenuation, espejo
     * de oae_attenuation_db en src/oae/generators/base.py), así el informe
     * no predice una emisión distinta de la que el alumno va a medir.
     *
     * @param array<string,mixed> $cfgOido cases.data['EOAS'][lado]
     * @return array<int,float> Hz => dB de caída
     */
    public static function atenuacionPorBanda(array $cfgOido): array
    {
        $cargada = CaseProfile::loadedOaeAttenuation([
            'type' => (string) ($cfgOido['type'] ?? 'normal'),
            'umbral' => (float) ($cfgOido['umbral'] ?? 0),
            'desviaciones' => is_array($cfgOido['desviaciones'] ?? null) ? $cfgOido['desviaciones'] : [],
        ]);
        $out = [];
        foreach (CaseBuilder::EOAS_FREQS as $hz) {
            $out[$hz] = (float) ($cargada[(string) $hz] ?? $cargada[$hz] ?? 0);
        }
        return $out;
    }

    /**
     * Atenuación interpolada a una frecuencia cualquiera (las pruebas no
     * usan las mismas bandas que el perfil). Lineal en log de frecuencia,
     * que es como se lee un audiograma y como se espacian las bandas.
     *
     * @param array<int,float> $porBanda
     */
    public static function atenuacionEn(array $porBanda, float $hz): float
    {
        $bandas = array_keys($porBanda);
        sort($bandas);
        if ($bandas === []) {
            return 0.0;
        }
        if ($hz <= $bandas[0]) {
            return $porBanda[$bandas[0]];
        }
        $ultima = $bandas[count($bandas) - 1];
        if ($hz >= $ultima) {
            return $porBanda[$ultima];
        }
        for ($i = 0; $i < count($bandas) - 1; $i++) {
            $a = $bandas[$i];
            $b = $bandas[$i + 1];
            if ($hz >= $a && $hz <= $b) {
                $t = (log($hz, 2) - log((float) $a, 2)) / (log((float) $b, 2) - log((float) $a, 2));
                return $porBanda[$a] + ($porBanda[$b] - $porBanda[$a]) * $t;
            }
        }
        return $porBanda[$ultima];
    }

    /**
     * Las cuatro pruebas de un oído, listas para dibujar.
     *
     * Cada una trae sus bandas, la respuesta esperada del caso, el piso de
     * ruido y el área normal. `pasa` dice si esa banda quedaría por encima
     * del criterio (señal sobre ruido), que es lo que el equipo marca como
     * PASS/REFER.
     *
     * @param array<string,mixed> $cfgOido
     * @return array<string,array<string,mixed>>
     */
    public static function pruebas(array $cfgOido): array
    {
        $aten = self::atenuacionPorBanda($cfgOido);
        $out = [];

        // TEOAE
        $pisoTe = self::pisoTeoae();
        $te = ['bandas' => [], 'piso' => $pisoTe, 'unidad' => 'dB SPL', 'area' => []];
        foreach (self::TEOAE['bandas'] as $hz) {
            $esperado = self::TEOAE['esperado'][$hz];
            $resp = $esperado - self::atenuacionEn($aten, (float) $hz);
            $te['bandas'][$hz] = [
                'respuesta' => $resp,
                'pasa' => ($resp - $pisoTe) >= self::TEOAE['min_snr_db'],
            ];
            $te['area'][$hz] = [$pisoTe + self::TEOAE['min_snr_db'], $esperado + 4];
        }
        $out['teoae'] = $te;

        // DP-grama
        $dp = ['bandas' => [], 'piso' => null, 'unidad' => 'dB SPL', 'area' => []];
        foreach (self::DPOAE['bandas'] as $hz) {
            $piso = self::pisoDpoae((float) $hz);
            $resp = self::dpEsperado((float) $hz) - self::atenuacionEn($aten, (float) $hz);
            $dp['bandas'][$hz] = [
                'respuesta' => $resp,
                'piso' => $piso,
                'pasa' => ($resp - $piso) >= self::DPOAE['min_sobre_ruido_db'],
            ];
            $dp['area'][$hz] = self::DPOAE['normal'][$hz];
        }
        $out['dpoae'] = $dp;

        // SFOAE
        $sf = ['bandas' => [], 'piso' => self::SFOAE['piso_db'], 'unidad' => 'dB', 'area' => []];
        foreach (self::SFOAE['bandas'] as $hz) {
            $esperado = self::SFOAE['esperado'][$hz];
            $resp = $esperado - self::atenuacionEn($aten, (float) $hz);
            $sf['bandas'][$hz] = [
                'respuesta' => $resp,
                'pasa' => ($resp - self::SFOAE['piso_db']) >= self::SFOAE['min_snr_db'],
            ];
            $sf['area'][$hz] = [self::SFOAE['piso_db'] + self::SFOAE['min_snr_db'], $esperado + 4];
        }
        $out['sfoae'] = $sf;

        return $out;
    }

    /**
     * Picos espontáneos que el caso declara, o la decisión de que los
     * decide el cliente por prevalencia.
     *
     * @param array<string,mixed> $cfgOido
     * @return array{modo:string,picos:array<int,array{hz:float,db:float}>}
     */
    public static function soae(array $cfgOido): array
    {
        $modo = (string) ($cfgOido['soae_mode'] ?? 'auto');
        $picos = [];
        foreach ((array) ($cfgOido['soae_peaks'] ?? []) as $pico) {
            if (!is_array($pico) || ($pico['hz'] ?? '') === '' || ($pico['hz'] ?? null) === null) {
                continue;
            }
            $picos[] = ['hz' => (float) $pico['hz'], 'db' => (float) ($pico['db'] ?? 0)];
        }
        return ['modo' => $modo, 'picos' => $picos];
    }
}
