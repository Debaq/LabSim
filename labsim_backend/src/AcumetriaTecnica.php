<?php

declare(strict_types=1);

require_once __DIR__ . '/EquiposTecnica.php';

/**
 * Técnica de la acumetría con diapasones (libro, H2): otoscopía primero,
 * explicar, diapasón de 512 Hz, Weber primero y en la línea media, Rinne
 * oído por oído (aire frente al conducto y hueso en la mastoides con el
 * mismo golpe) partiendo por el oído al que fue el Weber, preguntar lo que
 * corresponde y anotar lo que contestó el paciente.
 *
 * Lee ac_golpe, ac_apoyo (zona, oído, Hz, si vibraba), ac_instruccion y
 * ac_pregunta (con la zona y el oído donde estaba el diapasón). La verdad
 * es la del caso: Rinne y Weber por diapasón ('500' = 512 Hz). Null si el
 * alumno no apoyó el diapasón en el paciente.
 */
final class AcumetriaTecnica
{
    private const OIDOS = ['OD', 'OI'];
    private const LINEA = ['linea_media', 'fuera_de_linea'];
    private const RINNE = ['pabellon', 'mastoides'];
    private const PREG_WEBER = ['donde_mas_fuerte', 'igual_ambos', 'diga_donde'];
    private const PREG_RINNE = ['donde_mas_fuerte', 'compare_sonidos'];

    public static function evaluar(array $logs, array $caso, ?array $informe = null): ?array
    {
        $apoyos = [];
        $golpe = 0;
        foreach ($logs as $l) {
            if ($l['action'] === 'ac_golpe') {
                $golpe++;
            } elseif ($l['action'] === 'ac_apoyo') {
                $apoyos[] = $l + ['golpe' => $golpe];
            }
        }
        if (!$apoyos) {
            return null;
        }
        $reglas = [];
        $obs = [];
        $t0 = EquiposTecnica::t($apoyos[0]);

        // Otoscopía primero: si no se hizo en la atención, solo se advierte
        // (puede venir hecha); si se hizo después, es un error de orden.
        $tOto = EquiposTecnica::primera($logs, static function ($l) { return $l['action'] === 'ot_otoscopio'; });
        if ($tOto === null) {
            $obs[] = 'Usó los diapasones sin otoscopía en esta atención: un tapón o una efusión cambian el resultado.';
        } else {
            $reglas[] = [
                'texto' => 'La otoscopía va antes de los diapasones.',
                'cumple' => $tOto <= $t0,
                'detalle' => $tOto <= $t0 ? 'Así fue.' : 'La otoscopía fue después.',
                'peso' => 1,
            ];
        }

        $tExplica = EquiposTecnica::primera($logs, static function ($l) {
            return $l['action'] === 'ac_instruccion' && ($l['payload']['clave'] ?? '') === 'explicar_diapasones';
        });
        $reglas[] = [
            'texto' => 'Se le explica al paciente antes de apoyar el diapasón.',
            'cumple' => $tExplica !== null && $tExplica <= $t0,
            'detalle' => $tExplica === null ? 'No se le explicó.' : ($tExplica <= $t0 ? 'Se le explicó antes.' : 'Se le explicó después de empezar.'),
            'peso' => 1,
        ];

        $weber = array_values(array_filter($apoyos, static function ($a) { return in_array($a['payload']['zona'] ?? '', self::LINEA, true); }));
        $rinne = array_values(array_filter($apoyos, static function ($a) { return in_array($a['payload']['zona'] ?? '', self::RINNE, true); }));
        $usados = array_values(array_unique(array_map(static function ($a) { return (string) ($a['payload']['hz'] ?? ''); }, array_merge($weber, $rinne))));
        $reglas[] = [
            'texto' => 'Rinne y Weber con el diapasón de 512 Hz.',
            'cumple' => ($weber || $rinne) ? in_array('500', $usados, true) : null,
            'detalle' => in_array('500', $usados, true) ? 'Usó el de 512 Hz.' : 'Usó solo el de 1024 Hz.',
            'peso' => 1,
        ];

        $reglas[] = [
            'texto' => 'Se hace el Weber.',
            'cumple' => $weber !== [],
            'detalle' => $weber ? 'Se hizo.' : 'No apoyó el diapasón en la línea media.',
            'peso' => 2,
        ];
        if ($weber) {
            $enLinea = array_filter($weber, static function ($a) { return $a['payload']['zona'] === 'linea_media'; });
            $reglas[] = [
                'texto' => 'El Weber va en la línea media (frente o vértex).',
                'cumple' => $enLinea !== [],
                'detalle' => $enLinea ? 'En la línea media.' : 'A un lado de la línea media.',
                'peso' => 1,
            ];
            if ($rinne) {
                $reglas[] = [
                    'texto' => 'El Weber va primero: su resultado dice por dónde empezar el Rinne.',
                    'cumple' => EquiposTecnica::t($weber[0]) <= EquiposTecnica::t($rinne[0]),
                    'detalle' => EquiposTecnica::t($weber[0]) <= EquiposTecnica::t($rinne[0]) ? 'Así fue.' : 'Partió por el Rinne.',
                    'peso' => 1,
                ];
            }
            $preguntoW = self::pregunto($logs, self::LINEA, null, self::PREG_WEBER);
            $reglas[] = [
                'texto' => 'Con el diapasón en la línea media se pregunta dónde lo escucha.',
                'cumple' => $preguntoW,
                'detalle' => $preguntoW ? 'Se preguntó.' : 'No se preguntó con el diapasón en la línea media.',
                'peso' => 1,
            ];
        }

        // Rinne por oído: aire y hueso con el mismo golpe.
        $completos = [];
        foreach ([0, 1] as $o) {
            $porGolpe = [];
            foreach ($rinne as $a) {
                if (EquiposTecnica::oido($a['payload']['oido'] ?? null) === $o) {
                    $porGolpe[$a['golpe']][$a['payload']['zona']] = true;
                }
            }
            foreach ($porGolpe as $zonas) {
                if (count($zonas) === 2) {
                    $completos[] = $o;
                    break;
                }
            }
        }
        $reglas[] = [
            'texto' => 'Rinne en los dos oídos: frente al conducto y en la mastoides, con el mismo golpe.',
            'cumple' => count($completos) === 2,
            'logro' => count($completos) / 2,
            'detalle' => count($completos) === 2 ? 'En los dos.'
                : ($completos ? 'Solo en ' . self::OIDOS[$completos[0]] . '.' : 'En ningún oído comparó aire y hueso con el mismo golpe.'),
            'peso' => 2,
        ];
        if ($completos) {
            $preguntoR = 0;
            foreach ($completos as $o) {
                $preguntoR += self::pregunto($logs, self::RINNE, $o, self::PREG_RINNE) ? 1 : 0;
            }
            $reglas[] = [
                'texto' => 'En el Rinne se pregunta dónde lo escucha más fuerte: adelante o atrás.',
                'cumple' => $preguntoR === count($completos),
                'logro' => $preguntoR / count($completos),
                'detalle' => "Preguntó en {$preguntoR} de " . count($completos) . ' oído(s).',
                'peso' => 1,
            ];
        }
        $lateral = $caso['Weber']['500'] ?? null;
        $oLat = EquiposTecnica::oido($lateral);
        if ($weber && $rinne && $oLat !== null) {
            $primero = EquiposTecnica::oido($rinne[0]['payload']['oido'] ?? null);
            $reglas[] = [
                'texto' => 'El Rinne parte por el oído al que fue el Weber.',
                'cumple' => $primero === $oLat,
                'detalle' => 'Partió por ' . ($primero === null ? '—' : self::OIDOS[$primero]) . '.',
                'detalle_docente' => 'El Weber lateraliza a ' . self::OIDOS[$oLat] . '.',
                'peso' => 1,
            ];
        }

        $sinVibrar = array_filter($apoyos, static function ($a) { return ($a['payload']['vibrando'] ?? true) === false; });
        if ($sinVibrar) {
            $obs[] = sprintf('Apoyó el diapasón %d vez(veces) sin haberlo golpeado o ya apagado.', count($sinVibrar));
        }

        // Lo que anotó en el informe contra lo que contestó el paciente (la
        // verdad del caso en 512 Hz).
        $anotado = is_array($informe['acumetria'] ?? null) ? $informe['acumetria'] : null;
        if ($anotado !== null) {
            $bien = $total = 0;
            $mal = $malDoc = [];
            foreach (['od', 'oi'] as $oo) {
                $a = $anotado['rinne']['500'][$oo] ?? null;
                $v = $caso['Rinne']['500'][$oo] ?? null;
                if ($a !== null && $a !== '' && $v !== null) {
                    $total++;
                    if ($a === $v) {
                        $bien++;
                    } else {
                        $mal[] = 'Rinne ' . strtoupper($oo);
                        $malDoc[] = "Rinne {$oo}: anotó {$a}, el paciente era {$v}";
                    }
                }
            }
            $a = $anotado['weber']['500'] ?? null;
            $v = $caso['Weber']['500'] ?? null;
            if ($a !== null && $a !== '' && $v !== null) {
                $total++;
                if ($a === $v) {
                    $bien++;
                } else {
                    $mal[] = 'Weber';
                    $malDoc[] = "Weber: anotó {$a}, el paciente era {$v}";
                }
            }
            if ($total > 0) {
                $reglas[] = [
                    'texto' => 'Lo anotado corresponde a lo que contestó el paciente.',
                    'cumple' => $bien === $total,
                    'logro' => $bien / $total,
                    'detalle' => $bien === $total ? 'Todo calza.' : 'No calza: ' . EquiposTecnica::lista($mal) . '.',
                    'detalle_docente' => implode('; ', $malDoc),
                    'peso' => 2,
                ];
            }
        }
        return ['hecha' => true, 'reglas' => $reglas, 'oidos' => [], 'observaciones' => $obs];
    }

    /** Si hubo una pregunta o instrucción de esas claves con el diapasón en esa zona (y oído). */
    private static function pregunto(array $logs, array $zonas, ?int $oido, array $claves): bool
    {
        foreach ($logs as $l) {
            if (($l['action'] === 'ac_pregunta' || $l['action'] === 'ac_instruccion')
                && in_array($l['payload']['clave'] ?? '', $claves, true)
                && in_array($l['payload']['zona'] ?? '', $zonas, true)
                && ($oido === null || EquiposTecnica::oido($l['payload']['oido'] ?? null) === $oido)
                && ($l['payload']['retirado'] ?? false) === false) {
                return true;
            }
        }
        return false;
    }
}
