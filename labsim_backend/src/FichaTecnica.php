<?php

declare(strict_types=1);

require_once __DIR__ . '/EquiposTecnica.php';

/**
 * Revisión de la ficha del paciente: si el alumno la miró antes de empezar
 * y si abrió los exámenes que trae el paciente. Lo registra la app desde la
 * versión que marca 'atencion_inicio' con registra ['ficha'] (ficha_ver,
 * ficha_visible, ficha_previo); en las atenciones de antes no hay nada que
 * leer y la sección no aparece.
 *
 * El análisis de lo leído (si lo usó en la entrevista y en la conclusión)
 * no se mide aquí: la entrevista cuenta lo que la ficha ya dice como
 * cubierto si la ficha se revisó (EntrevistaTecnica).
 */
final class FichaTecnica
{
    /** Margen después de empezar en que mirar la ficha todavía cuenta como "antes". */
    public const MARGEN_S = 120;

    /**
     * $logs: filas de UNA atención en orden (de esa cita o de la ficha de ese
     * caso). Null si la app de la atención no registraba la ficha.
     */
    public static function evaluar(array $logs, array $caso): ?array
    {
        $inicio = null;
        foreach ($logs as $l) {
            if ($l['action'] === 'atencion_inicio' && in_array('ficha', (array) ($l['payload']['registra'] ?? []), true)) {
                $inicio = $l;
                break;
            }
        }
        if ($inicio === null) {
            return null;
        }
        $t0 = EquiposTecnica::t($inicio);
        $vistas = array_values(array_filter($logs, static function ($l) { return $l['action'] === 'ficha_ver'; }));
        $antes = !empty($inicio['payload']['ficha_abierta']);
        foreach ($vistas as $v) {
            if (EquiposTecnica::t($v) <= $t0 + self::MARGEN_S) {
                $antes = true;
            }
        }
        $reglas = [[
            'texto' => 'Se revisa la ficha del paciente antes de empezar.',
            'cumple' => $antes,
            'detalle' => $antes ? 'La revisó.' : ($vistas ? 'La abrió recién después de empezar.' : 'No abrió la ficha.'),
            'detalle_docente' => 'Ficha a la vista: ' . self::tiempoVisible($logs, $t0) . '.',
            'peso' => 2,
        ]];
        $trae = array_values(array_filter(array_map('strval', (array) ($inicio['payload']['trae'] ?? []))));
        if ($trae) {
            $abiertos = [];
            foreach ($logs as $l) {
                if ($l['action'] === 'ficha_previo') {
                    $abiertos[(string) ($l['payload']['examen'] ?? '')] = true;
                }
            }
            $vio = array_values(array_filter($trae, static function ($e) use ($abiertos) { return isset($abiertos[$e]); }));
            $faltan = array_values(array_diff($trae, $vio));
            $reglas[] = [
                'texto' => 'Se abren los exámenes que trae el paciente.',
                'cumple' => $faltan === [],
                'logro' => count($vio) / count($trae),
                'detalle' => $faltan === [] ? 'Los abrió todos.' : 'No abrió: ' . EquiposTecnica::lista($faltan) . '.',
                'peso' => 2,
            ];
        }
        return ['hecha' => true, 'reglas' => $reglas, 'oidos' => [], 'observaciones' => [], 'revisada' => $antes || $vistas !== []];
    }

    /** Segundos con la ficha abierta (de ficha_visible), en palabras. */
    private static function tiempoVisible(array $logs, float $t0): string
    {
        $total = 0.0;
        $desde = null;
        foreach ($logs as $l) {
            if ($l['action'] !== 'ficha_visible') {
                continue;
            }
            $t = EquiposTecnica::t($l);
            if (!empty($l['payload']['visible'])) {
                $desde = $desde ?? $t;
            } elseif ($desde !== null) {
                $total += $t - $desde;
                $desde = null;
            }
        }
        if ($total <= 0) {
            return 'sin registro de cuánto rato';
        }
        return $total < 120 ? ((int) round($total)) . ' s' : ((int) round($total / 60)) . ' min';
    }
}
