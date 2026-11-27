<?php

declare(strict_types=1);

require_once __DIR__ . '/EquiposTecnica.php';
require_once __DIR__ . '/CaseBuilder.php';

/**
 * Técnica de la otoscopía (libro, H1): explicar, traccionar el pabellón
 * según la edad, el espéculo que corresponde, los dos oídos, empezar por el
 * que menos probablemente esté alterado y, cuando se sabe qué muestra la
 * foto, que el informe lo diga.
 *
 * Lee ot_instruccion, ot_traccion, ot_otoscopio (cada vez que el otoscopio
 * entra al conducto, con la tracción vigente y la edad) y
 * ot_especulo_grande (el espéculo de adulto en un niño: no entra).
 * Null si el alumno no usó el otoscopio con el paciente.
 */
final class OtoscopiaTecnica
{
    /** Edad desde la que entra el espéculo de adulto (Otoscopia.EDAD_ESPECULO_ADULTO). */
    public const EDAD_ESPECULO_ADULTO = 6;
    private const OIDOS = ['OD', 'OI'];

    /**
     * Qué tiene que aparecer en el informe para cada tipo de la biblioteca
     * de otoscopías: alguno de estos hallazgos (de membrana o de CAE). Vacío
     * = sin hallazgos patológicos.
     */
    public const HALLAZGOS_TIPO = [
        'normal' => [],
        'perforacion' => ['perforation'],
        'omc' => ['perforation', 'cae_otorrhea'],
        'timpanoesclerosis' => ['tympanosclerosis'],
        'otitis_externa' => ['cae_edema', 'cae_otorrhea'],
        'ome' => ['effusion'],
        'oma' => ['inflammation', 'myringitis', 'effusion'],
        'colesteatoma' => ['cholesteatoma'],
        'cerumen' => ['cae_cerumen'],
        'tubo' => ['tube'],
        'retraccion' => ['retraction'],
    ];
    /**
     * Lo típico de cada tipo de la base, para sugerirlo en la ficha cuando
     * la foto se elige de la base (el docente lo corrige): misma forma que
     * CaseBuilder::otoscopiaHallazgos.
     */
    public const TIPICO_TIPO = [
        'normal' => ['normal' => true],
        'perforacion' => ['cuadrantes' => ['toda' => ['perforation']]],
        'omc' => ['cuadrantes' => ['toda' => ['perforation']], 'cae' => ['cae_otorrhea']],
        'timpanoesclerosis' => ['cuadrantes' => ['toda' => ['tympanosclerosis']]],
        'otitis_externa' => ['cae' => ['cae_edema']],
        'ome' => ['cuadrantes' => ['toda' => ['effusion']]],
        'oma' => ['cuadrantes' => ['toda' => ['inflammation']]],
        'colesteatoma' => ['cuadrantes' => ['toda' => ['cholesteatoma']]],
        'cerumen' => ['cae' => ['cae_cerumen']],
        'tubo' => ['cuadrantes' => ['toda' => ['tube']]],
        'retraccion' => ['cuadrantes' => ['toda' => ['retraction']]],
    ];
    /** Lo que en el informe cuenta como "sin hallazgos". */
    private const SIN_HALLAZGO = ['cae_normal'];

    public static function evaluar(array $logs, array $caso, ?array $informe = null, array $tipos = []): ?array
    {
        $vistas = EquiposTecnica::filas($logs, ['ot_otoscopio', 'ot_especulo_grande']);
        if (!$vistas) {
            return null;
        }
        $edad = (float) ($vistas[0]['payload']['edad'] ?? ($caso['edad'] ?? 30));
        $reglas = [];
        $oidos = [];
        $obs = [];

        $t0 = EquiposTecnica::t($vistas[0]);
        $tExplica = EquiposTecnica::primera($logs, static function ($l) {
            return $l['action'] === 'ot_instruccion' && ($l['payload']['clave'] ?? '') === 'explicar_otoscopia';
        });
        $reglas[] = [
            'texto' => 'Se le explica al paciente antes de examinar.',
            'cumple' => $tExplica !== null && $tExplica <= $t0,
            'detalle' => $tExplica === null ? 'No se le explicó.' : ($tExplica <= $t0 ? 'Se le explicó antes.' : 'Se le explicó después de empezar.'),
            'peso' => 1,
        ];

        $examinados = [];
        foreach ($vistas as $v) {
            $o = EquiposTecnica::oido($v['payload']['oido'] ?? null);
            if ($o !== null && !in_array($o, $examinados, true)) {
                $examinados[] = $o;
            }
        }
        $reglas[] = [
            'texto' => 'Se examinan los dos oídos.',
            'cumple' => count($examinados) === 2,
            'logro' => count($examinados) / 2,
            'detalle' => count($examinados) === 2 ? 'Los dos.' : 'Solo ' . (self::OIDOS[$examinados[0] ?? 0]) . '.',
            'peso' => 2,
        ];

        // Por dónde empezar: el oído que menos probablemente esté alterado,
        // cuando la ficha deja saber cuál es (foto de la biblioteca o
        // impedanciometría no realizable en uno solo).
        $alterado = self::oidoAlterado($caso, $tipos);
        if ($alterado !== null && $examinados) {
            $reglas[] = [
                'texto' => 'Se empieza por el oído que menos probablemente esté alterado.',
                'cumple' => $examinados[0] !== $alterado,
                'detalle' => 'Empezó por ' . self::OIDOS[$examinados[0]] . '.',
                'detalle_docente' => 'El alterado es ' . self::OIDOS[$alterado] . '.',
                'peso' => 1,
            ];
        }

        $especuloEsperado = $edad >= self::EDAD_ESPECULO_ADULTO ? 'adulto' : 'pediatrico';
        foreach ($examinados as $o) {
            $propias = array_values(array_filter($vistas, static function ($v) use ($o) {
                return EquiposTecnica::oido($v['payload']['oido'] ?? null) === $o;
            }));
            $mejor = 0.0;
            $calidad = 'sin';
            foreach ($propias as $v) {
                if ($v['action'] !== 'ot_otoscopio') {
                    continue;
                }
                $q = ($v['payload']['traccion_correcta'] ?? false) ? ($v['payload']['traccion_calidad'] === 'buena' ? 1.0 : 0.5)
                    : (($v['payload']['traccion_calidad'] ?? 'sin') === 'regular' ? 0.5 : 0.0);
                if ($q >= $mejor) {
                    $mejor = $q;
                    $calidad = (string) ($v['payload']['traccion_calidad'] ?? 'sin');
                }
            }
            $r = [];
            $r[] = [
                'texto' => $edad < 3
                    ? 'Se tracciona el pabellón hacia abajo y atrás (menor de 3 años) para mirar.'
                    : 'Se tracciona el pabellón hacia arriba y atrás para mirar.',
                'cumple' => $mejor >= 1.0,
                'logro' => $mejor,
                'detalle' => $calidad === 'sin' ? 'Miró sin traccionar.' : 'Tracción ' . $calidad . '.',
                'peso' => 2,
            ];
            $grande = false;
            $ultimo = null;
            foreach ($propias as $v) {
                if ($v['action'] === 'ot_especulo_grande') {
                    $grande = true;
                } else {
                    $ultimo = (string) ($v['payload']['especulo'] ?? '');
                }
            }
            $bienEsp = !$grande && $ultimo === $especuloEsperado;
            $r[] = [
                'texto' => 'Se usa el espéculo más grande que entra cómodo (de adulto desde los ' . self::EDAD_ESPECULO_ADULTO . ' años).',
                'cumple' => $bienEsp,
                'detalle' => $grande ? 'Intentó con el de adulto en un conducto de niño.'
                    : ($ultimo === null ? 'No llegó a mirar.' : 'Miró con el ' . ($ultimo === 'adulto' ? 'de adulto' : 'pediátrico') . '.'),
                'peso' => 1,
            ];
            // Lo informado contra lo que muestra la foto: lo que cargó el
            // docente en la ficha; si no, el tipo de la foto de la base.
            $lado = strtolower(self::OIDOS[$o]);
            $verdad = CaseBuilder::otoscopiaHallazgos($caso['Otoscopia']['hallazgos'][$lado] ?? null);
            $tipo = $tipos[$lado] ?? null;
            if (is_array($informe) && $verdad['definida'] && ($verdad['normal'] || $verdad['cae'] || $verdad['cuadrantes'])) {
                $r[] = self::compararHallazgos($verdad, $informe, $lado);
            } elseif ($tipo !== null && isset(self::HALLAZGOS_TIPO[$tipo]) && is_array($informe)) {
                $marcados = self::marcados($informe, $lado);
                $esperados = self::HALLAZGOS_TIPO[$tipo];
                $ok = $esperados === []
                    ? array_diff($marcados, self::SIN_HALLAZGO) === []
                    : array_intersect($esperados, $marcados) !== [];
                $r[] = [
                    'texto' => 'El informe dice lo que se ve en la membrana y el conducto.',
                    'cumple' => $ok,
                    'detalle' => $ok ? 'Lo informado calza con la imagen.' : 'Lo informado no calza con la imagen.',
                    'detalle_docente' => 'Imagen: ' . str_replace('_', ' ', $tipo) . ' (de la base). Informó: '
                        . ($marcados ? implode(', ', array_map([self::class, 'etiqueta'], $marcados)) : 'nada marcado') . '.',
                    'peso' => 2,
                ];
            }
            $oidos[self::OIDOS[$o]] = $r;
        }

        if (!is_array($informe)) {
            $obs[] = 'No dejó informe de otoscopía: lo que vio no quedó registrado.';
        }
        return ['hecha' => true, 'reglas' => $reglas, 'oidos' => $oidos, 'observaciones' => $obs];
    }

    /**
     * El informe de un oído contra lo que el docente dijo que muestra la
     * foto. Se comparan los hallazgos (de membrana, en cualquier cuadrante, y
     * del conducto, sin contar "normal"): logro = coincidencias sobre la
     * unión, así descuenta tanto lo que no vio como lo que marcó de más. Si
     * la foto no tiene hallazgos, cumple el que no marcó ninguno. El
     * cuadrante y los textos van al detalle del docente.
     */
    public static function compararHallazgos(array $verdad, array $informe, string $lado): array
    {
        $esperados = self::conjunto($verdad);
        $marcados = array_values(array_diff(self::marcados($informe, $lado), self::SIN_HALLAZGO));
        $comunes = array_values(array_intersect($esperados, $marcados));
        $union = array_values(array_unique(array_merge($esperados, $marcados)));
        if ($esperados === []) {
            $logro = $marcados === [] ? 1.0 : 0.0;
            $detalle = $marcados === [] ? 'Sin hallazgos, como la imagen.' : 'Marcó hallazgos que la imagen no tiene.';
        } else {
            $logro = count($comunes) / count($union);
            $extra = count($marcados) - count($comunes);
            $detalle = sprintf('Encontró %d de %d hallazgo(s) de la imagen', count($comunes), count($esperados))
                . ($extra > 0 ? " y marcó {$extra} que no está(n)" : '') . '.';
        }
        $doc = 'Imagen: ' . self::describir($verdad['cuadrantes'], $verdad['cae'], $verdad['normal'])
            . '. Informó: ' . self::describir((array) ($informe[$lado]['cuadrantes'] ?? []), (array) ($informe[$lado]['cae'] ?? []), false) . '.';
        if ($verdad['texto'] !== '' || trim((string) ($informe[$lado]['observaciones'] ?? '')) !== '') {
            $doc .= ' Docente: "' . $verdad['texto'] . '". Alumno: "' . trim((string) ($informe[$lado]['observaciones'] ?? '')) . '".';
        }
        return [
            'texto' => 'El informe dice lo que se ve en la membrana y el conducto.',
            'cumple' => $logro >= 1.0,
            'logro' => $logro,
            'detalle' => $detalle,
            'detalle_docente' => $doc,
            'peso' => 2,
        ];
    }

    /** Hallazgos de una verdad cargada por el docente, como lista plana. */
    private static function conjunto(array $verdad): array
    {
        $out = [];
        foreach ($verdad['cuadrantes'] as $lista) {
            foreach ($lista as $h) {
                $out[] = $h;
            }
        }
        foreach ($verdad['cae'] as $c) {
            $out[] = $c;
        }
        return array_values(array_diff(array_unique($out), self::SIN_HALLAZGO));
    }

    private static function etiqueta(string $k): string
    {
        return CaseBuilder::OTOSCOPIA_HALLAZGOS[$k] ?? (CaseBuilder::OTOSCOPIA_CAE[$k] ?? $k);
    }

    private static function describir(array $cuadrantes, array $cae, bool $normal): string
    {
        if ($normal) {
            return 'normal';
        }
        $partes = [];
        foreach ($cuadrantes as $q => $lista) {
            foreach ((array) $lista as $h) {
                $partes[] = self::etiqueta((string) $h) . ' (' . (CaseBuilder::OTOSCOPIA_CUADRANTES[$q] ?? $q) . ')';
            }
        }
        foreach ($cae as $c) {
            $partes[] = 'CAE ' . mb_strtolower(self::etiqueta((string) $c));
        }
        return $partes ? implode(', ', $partes) : 'nada marcado';
    }

    /** Oído con la otoscopía alterada cuando el otro no lo está, o null. */
    public static function oidoAlterado(array $caso, array $tipos): ?int
    {
        $alt = [];
        foreach ([0, 1] as $o) {
            $lado = $o === 0 ? 'od' : 'oi';
            $tipo = $tipos[$lado] ?? null;
            $nr = ($caso[$o === 0 ? 'Z_OD' : 'Z_OI'] ?? null) === 'NR';
            // lo que cargó el docente manda sobre el tipo de la base
            $v = CaseBuilder::otoscopiaHallazgos($caso['Otoscopia']['hallazgos'][$lado] ?? null);
            if ($v['normal'] || $v['cae'] || $v['cuadrantes']) {
                $tipo = self::conjunto($v) === [] ? 'normal' : 'alterado';
            }
            $alt[$o] = $nr || ($tipo !== null && $tipo !== 'normal') ? true : ($tipo === 'normal' ? false : null);
        }
        if ($alt[0] === true && $alt[1] !== true) {
            return 0;
        }
        if ($alt[1] === true && $alt[0] !== true) {
            return 1;
        }
        return null;
    }

    /** Hallazgos marcados en el informe para un oído (membrana y CAE). */
    private static function marcados(array $informe, string $oido): array
    {
        $o = is_array($informe[$oido] ?? null) ? $informe[$oido] : [];
        $out = [];
        foreach ((array) ($o['cuadrantes'] ?? []) as $lista) {
            foreach ((array) $lista as $h) {
                $out[] = (string) $h;
            }
        }
        foreach ((array) ($o['cae'] ?? []) as $h) {
            $out[] = (string) $h;
        }
        return array_values(array_unique($out));
    }
}
