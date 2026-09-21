<?php

declare(strict_types=1);

/**
 * Screening auditivo neonatal: qué tan probable es que ese bebé pase.
 *
 * Las primeras horas de vida son una pérdida de transmisión real y
 * transitoria --vérnix y líquido amniótico en el conducto, mesénquima en el
 * oído medio-- que se resuelve sola en dos o tres días. Lo que la
 * bibliografía publica NO son decibeles: son tasas de pase por franja
 * horaria. Así que la tabla manda y los dB salen de ella, no al revés.
 *
 * Fuentes de las tasas (aportadas por el docente):
 *   1. Seehiranwong W, Saengrat P. Timing of newborn hearing screening
 *      effects on passing rates. Am J Perinatol. 2025. PMID 40759178.
 *   2. Cheepcharoenrat C, Rerkasem A. Timing effect on TEOAE referral rates
 *      within and after 48 hours of birth. Int Arch Otorhinolaryngol. 2025.
 *      PMID 40735129.
 *   3. OAE in universal hearing screening: which day after birth should we
 *      examine the newborns? PMID 14564092.
 *   4. Akinpelu OV et al. OAE in newborn hearing screening: systematic
 *      review of protocols. Int J Pediatr Otorhinolaryngol. 2014. PMID
 *      24613088.
 *   5. Stewart DL et al. Universal newborn hearing screening with AABR:
 *      multisite investigation. J Perinatol. 2000. PMID 11190693.
 *   6. Doyle KJ et al. Newborn hearing screening by OAE and AABR. Int J
 *      Pediatr Otorhinolaryngol. 1997;41(2):111-9.
 *   7. Van Dyk M, Swanepoel DW, Hall JW 3rd. Outcomes with OAE and AABR in
 *      the first 48 h. Int J Pediatr Otorhinolaryngol. 2015. PMID 25921078.
 *   8. Newborn hearing screening: early ear examination improves the pass
 *      rate. PMCID PMC10645159.
 *   9. Lupoli et al. y Xiao et al., citados en (1).
 *  10. Nebraska DHHS, EHDI. Newborn Hearing Screening Protocol (JCIH 2019).
 *
 * El detalle importante de la tabla: a las pocas horas la TEOAE refiere en
 * más de la mitad de los recién nacidos SANOS, mientras el AABR pasa en el
 * 85%. Esa brecha es el contenido -- y es la razón de que el protocolo
 * recomiende screenear lo más tarde posible antes del alta, y de que un
 * "refiere" temprano sea motivo de rescreening y no un hallazgo.
 */
final class NewbornScreening
{
    /** [hora desde, hora hasta, P(pasa)] con audición normal. */
    public const PASS_TEOAE = [
        [0.0, 12.0, 0.40],
        [12.0, 24.0, 0.55],
        [24.0, 36.0, 0.75],
        [36.0, 48.0, 0.85],
        [48.0, 72.0, 0.93],
        [72.0, INF, 0.95],
    ];

    public const PASS_AABR = [
        [0.0, 12.0, 0.85],
        [12.0, 24.0, 0.92],
        [24.0, 36.0, 0.95],
        [36.0, 48.0, 0.96],
        [48.0, 72.0, 0.97],
        [72.0, INF, 0.97],
    ];

    /**
     * Modificadores que corren la EDAD EFECTIVA, en horas. Negativo = se
     * comporta como un bebé más joven (peor pase).
     *
     * La cesárea sin trabajo de parto no exprime el líquido del oído medio
     * como el canal vaginal; el prematuro tardío tiene el conducto más
     * estrecho y colapsable y más mesénquima sin reabsorber. El pequeño para
     * edad gestacional pasa MEJOR (conducto proporcionalmente más despejado
     * respecto de su madurez), así que suma horas.
     */
    public const MOD_HORAS = [
        'cesarea' => ['teoae' => -12.0, 'aabr' => -4.0],
        'pretermino_tardio' => ['teoae' => -13.0, 'aabr' => -6.0],
        'peg' => ['teoae' => 8.0, 'aabr' => 0.0],
    ];

    /**
     * Limpieza del vérnix del conducto antes de medir: no cambia la edad,
     * cambia directamente cuánto refiere (multiplica P(refiere)).
     */
    public const MOD_REFIERE = [
        'vernix_limpiado' => ['teoae' => 0.5, 'aabr' => 0.75],
    ];

    /** Líquido o vérnix que NO se resolvió: deja de ser cuestión de horas. */
    public const PERSISTENTE = ['teoae' => 0.20, 'aabr' => 0.80];

    /**
     * Pasado el primer mes esto deja de ser screening neonatal: el 5% que
     * sigue refiriendo a las 72 h es sonda, ruido y oído medio de verdad, no
     * el transitorio del parto. Sin este tope, un bebé de ocho meses --que
     * también tiene 'edad_horas' cargada-- heredaba la tasa del recién
     * nacido.
     */
    public const MAX_HORAS = 720.0;

    /**
     * Los dos umbrales que convierten la tabla en decibeles, medidos contra
     * los generadores de este mismo simulador y no inventados:
     *
     * - OAE_FAIL_DB: conductiva (dB HL) a la que la TEOAE cae bajo criterio.
     *   El generador aplica la regla de ida y vuelta (2 dB/dB, ver
     *   oae_attenuation_db) y pierde bandas pasando los ~7.5 dB de
     *   atenuación total.
     * - ABR_FAIL_DB: conductiva a la que el AABR de screening (35 dB nHL)
     *   deja de pasar. El umbral del recién nacido sano ronda 20 dB nHL y el
     *   transitorio le suma 0.6 dB por dB, así que hacen falta ~25 dB.
     *
     * Que la TEOAE caiga con tan poca conductiva no es un defecto del
     * modelo: es la razón clínica de que refiera tanto en las primeras
     * horas.
     */
    public const OAE_FAIL_DB = 3.75;
    public const ABR_FAIL_DB = 25.0;
    public const MAX_DB = 40.0;

    /** P(pasa) de esa prueba a esas horas, con los modificadores puestos. */
    public static function passProbability(string $prueba, ?float $horas, array $mods = []): float
    {
        if ($horas === null || $horas > self::MAX_HORAS) {
            return 1.0;
        }
        if (!empty($mods['liquido_persistente'])) {
            return self::PERSISTENTE[$prueba];
        }
        $horasEfectivas = $horas;
        foreach (self::MOD_HORAS as $mod => $delta) {
            if (!empty($mods[$mod])) {
                $horasEfectivas += $delta[$prueba];
            }
        }
        $horasEfectivas = max(0.0, $horasEfectivas);

        $tabla = $prueba === 'teoae' ? self::PASS_TEOAE : self::PASS_AABR;
        $p = $tabla[count($tabla) - 1][2];
        foreach ($tabla as [$desde, $hasta, $valor]) {
            if ($horasEfectivas >= $desde && $horasEfectivas < $hasta) {
                $p = $valor;
                break;
            }
        }
        foreach (self::MOD_REFIERE as $mod => $factor) {
            if (!empty($mods[$mod])) {
                $p = 1.0 - (1.0 - $p) * $factor[$prueba];
            }
        }
        return min(1.0, max(0.0, $p));
    }

    /**
     * Cuánta conductiva transitoria le tocó a ESTE bebé, en dB HL.
     *
     * `$u` es su percentil (0 a 1), sorteado una vez por oído y guardado en
     * el caso: dos recién nacidos de la misma edad no tienen la misma
     * cantidad de líquido, y esa variabilidad es justamente lo que la tabla
     * describe. La función es el inverso de la tabla: tramos lineales entre
     * los dos umbrales medidos, así que la proporción de bebés que pasa cada
     * prueba sale EXACTAMENTE la publicada.
     */
    public static function transientDb(?float $horas, array $mods = [], float $u = 0.5): float
    {
        if ($horas === null || $horas > self::MAX_HORAS) {
            return 0.0;
        }
        $u = min(1.0, max(0.0, $u));
        $pOae = self::passProbability('teoae', $horas, $mods);
        $pAbr = self::passProbability('aabr', $horas, $mods);
        // El que falla el AABR falla también la TEOAE: es la misma
        // conductiva, y el AABR aguanta mucho más.
        $pAbr = max($pAbr, $pOae);

        if ($pOae > 0.0 && $u <= $pOae) {
            return self::OAE_FAIL_DB * ($u / $pOae);
        }
        if ($u <= $pAbr) {
            $span = $pAbr - $pOae;
            $f = $span > 0.0 ? ($u - $pOae) / $span : 1.0;
            return self::OAE_FAIL_DB + (self::ABR_FAIL_DB - self::OAE_FAIL_DB) * $f;
        }
        $span = 1.0 - $pAbr;
        $f = $span > 0.0 ? ($u - $pAbr) / $span : 1.0;
        return self::ABR_FAIL_DB + (self::MAX_DB - self::ABR_FAIL_DB) * $f;
    }

    /** Qué va a informar el equipo con esa conductiva transitoria. */
    public static function resultado(float $transitorioDb): array
    {
        return [
            'teoae' => $transitorioDb <= self::OAE_FAIL_DB ? 'pasa' : 'refiere',
            'aabr' => $transitorioDb <= self::ABR_FAIL_DB ? 'pasa' : 'refiere',
        ];
    }
}
