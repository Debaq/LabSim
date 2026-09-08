<?php

require_once __DIR__ . '/CaseProfile.php';

/**
 * Qué le falta a un caso para poder atenderse.
 *
 * El perfil auditivo deriva casi todo (ver CaseProfile), pero hay cosas que
 * NO se pueden calcular: qué curva timpanométrica corresponde, si la trompa
 * está permeable, cómo se ven las ondas del ABR más allá del umbral, qué
 * pasa en el VEMP. Son decisiones clínicas, no cuentas.
 *
 * Antes eso quedaba en el default silencioso: un caso conductivo con
 * timpanograma A, o un ABR "coclear" con la morfología de onda de un oído
 * sano. El alumno se encontraba con un paciente que no cierra, y el docente
 * no tenía cómo enterarse.
 *
 * Esta clase es el criterio único de "caso listo", y lo usan los dos
 * lugares donde importa: el editor (no se sale de la edición con esto
 * pendiente) y la agenda (no se cita un paciente así).
 *
 * A propósito NO revisa lo que puede estar vacío con razón: la anamnesis,
 * el texto de otoscopia, el comportamiento del paciente. Un caso puede no
 * tener nada de eso y seguir siendo un caso.
 */
final class CaseCompleteness
{
    /**
     * Timpanogramas que implican disfunción tubaria: dejar la ETF en
     * "Normal" con una de estas es no haber decidido, no un hallazgo.
     * B = ocupación, C/Cs = presión negativa (retracción).
     */
    public const TYMP_DISFUNCION = ['B', 'C', 'Cs'];

    /**
     * Lo que le falta al caso, listo para mostrar.
     *
     * @param array<string,mixed> $data cases.data
     * @return list<array{tab:string, texto:string}> `tab` es la pestaña de
     *         case_create.php donde se arregla.
     */
    public static function pending(array $data): array
    {
        $pendientes = [];
        $perfil = CaseProfile::normalize($data);
        $airPairs = is_array($data['Aerea'] ?? null) ? $data['Aerea'] : [];
        $bonePairs = is_array($data['Osea'] ?? null) ? $data['Osea'] : [];

        $tympPorLado = ['OD' => (string) ($data['Z_OD'] ?? 'A'), 'OI' => (string) ($data['Z_OI'] ?? 'A')];
        $etf = is_array($data['ETF'] ?? null) ? $data['ETF'] : ['Normal', 'Normal'];
        $etfPorLado = ['OD' => (string) ($etf[0] ?? 'Normal'), 'OI' => (string) ($etf[1] ?? 'Normal')];

        foreach (['OD' => 0, 'OI' => 1] as $lado => $sideIdx) {
            $decomp = CaseProfile::decompose(
                $airPairs, $bonePairs, $sideIdx, (float) ($perfil[$lado]['cce_pct'] ?? 100.0)
            );
            $gap = CaseProfile::coreMax($decomp['gap']);
            $tymp = $tympPorLado[$lado];

            // --- Oído medio: el timpanograma nunca se deriva, y es el
            // default más fácil de dejar sin tocar (todo caso nace en A).
            if ($tymp === 'A' && $gap >= CaseProfile::WARN_TYMP_GAP_DB) {
                $pendientes[] = [
                    'tab' => 'timpanometria',
                    'texto' => sprintf(
                        'Timpanometría %s: hay un gap aéreo-óseo de %d dB y la curva quedó en A. Elegí la que corresponde (B ocupación, As rígido, Ad hipercompliante, C retracción) -- eso no se puede calcular desde el audiograma.',
                        $lado, (int) round($gap)
                    ),
                ];
            } elseif (in_array($tymp, self::TYMP_DISFUNCION, true) && $etfPorLado[$lado] === 'Normal') {
                $pendientes[] = [
                    'tab' => 'timpanometria',
                    'texto' => sprintf(
                        'Función tubaria %s: el timpanograma %s dice que la trompa no está trabajando bien, pero la ETF quedó en "Normal". Decidí cuál corresponde.',
                        $lado, $tymp
                    ),
                ];
            }

            // --- ABR: el perfil da umbral y tipo, nunca la morfología de
            // las ondas. Sin eso, un oído "coclear" dibuja las latencias y
            // amplitudes de uno sano y el alumno no tiene qué leer.
            $abrLado = is_array(($data['ABR'] ?? [])[$lado] ?? null) ? $data['ABR'][$lado] : [];
            if (($abrLado['type'] ?? 'normal') !== 'normal'
                && self::allZero($abrLado['desviaciones'] ?? [])) {
                $pendientes[] = [
                    'tab' => 'abr',
                    'texto' => sprintf(
                        'ABR %s: la patología es "%s" pero las latencias y amplitudes de las ondas están todas en 0, o sea las de un oído sano. Usá "Autocompletar según patología" o cargalas a mano.',
                        $lado, (string) $abrLado['type']
                    ),
                ];
            }

            // --- VEMP: el perfil no tiene eje vestibular. Si el caso tiene
            // patrón retrococlear, alguien tiene que decir qué pasa acá.
            $vempLado = is_array(($data['VEMP'] ?? [])[$lado] ?? null) ? $data['VEMP'][$lado] : [];
            if (CaseProfile::retroActivo($perfil[$lado]['retro'] ?? [])
                && ($vempLado['type'] ?? 'normal') === 'normal'
                && self::allZero($vempLado['desviaciones'] ?? [])) {
                $pendientes[] = [
                    'tab' => 'vemp',
                    'texto' => sprintf(
                        'VEMP %s: el caso tiene patrón retrococlear cargado y el VEMP quedó normal sin tocar. El perfil no cubre lo vestibular: decidí si la lesión lo compromete o no.',
                        $lado
                    ),
                ];
            }
        }

        return $pendientes;
    }

    /** Solo los textos, para un mensaje de una línea por ítem. */
    public static function pendingTexts(array $data): array
    {
        return array_map(static fn(array $p) => $p['texto'], self::pending($data));
    }

    /**
     * ¿Están todas las desviaciones en 0? Acepta las dos formas que usan
     * los módulos: anidada por onda/pico y plana por frecuencia.
     *
     * @param mixed $desviaciones
     */
    private static function allZero($desviaciones): bool
    {
        if (!is_array($desviaciones)) {
            return true;
        }
        foreach ($desviaciones as $valor) {
            if (is_array($valor)) {
                if (!self::allZero($valor)) {
                    return false;
                }
                continue;
            }
            if (abs((float) $valor) > 1e-9) {
                return false;
            }
        }
        return true;
    }
}
