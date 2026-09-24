<?php

declare(strict_types=1);

/**
 * Revisión de un informe de ABR/electrococleo después de cerrar la atención.
 *
 * Al mismo paciente se le puede hacer más de un ABR, y el alumno tiene que
 * poder volver a una sesión anterior para verla o terminarla. Lo que NO
 * puede es registrar de nuevo: las curvas son lo que el equipo midió ese
 * día. Así que una vez 'atendido' el informe solo acepta lo que se hace
 * SOBRE las curvas --marcas, medidas que salen de las marcas, hallazgos y
 * conclusión--; el resto (trazos, setting, técnica, FSP) queda como estaba
 * aunque el cliente mande otra cosa. Las curvas que no existían se ignoran
 * y las que faltan en lo que llega se conservan.
 *
 * Sin base: recibe y devuelve arrays, así se prueba sin pdo_sqlite (ver
 * tests/test_report_revision.php).
 */
final class ReportRevision
{
    /** Tipos de informe que se pueden revisar tras el cierre. */
    const TIPOS = ['ABR', 'ELECTROCOCLEO'];

    /** Lo que se toca de cada curva al revisar: marcas y lo que sale de ellas. */
    const CAMPOS_CURVA = ['LatAmp', 'marcas', 'marcas_graf', 'ECochG'];

    /** Lo que se toca del informe completo. `tasa` sale de las medidas del ECochG. */
    const CAMPOS_INFORME = ['hallazgos', 'conclusion', 'tasa'];

    public static function admite(string $tipo): bool
    {
        return in_array($tipo, self::TIPOS, true);
    }

    /**
     * @param array  $guardado lo que ya estaba en reports.data
     * @param array  $entrante lo que manda el cliente
     * @param string $cuando   marca de tiempo de la revisión
     */
    public static function fusionar(array $guardado, array $entrante, string $cuando): array
    {
        $resultado = $guardado;
        foreach (self::CAMPOS_INFORME as $campo) {
            if (array_key_exists($campo, $entrante)) {
                $resultado[$campo] = $entrante[$campo];
            }
        }

        $curvas = is_array($guardado['curvas'] ?? null) ? $guardado['curvas'] : [];
        $nuevas = is_array($entrante['curvas'] ?? null) ? $entrante['curvas'] : [];
        foreach ($curvas as $nombre => $curva) {
            if (!is_array($curva) || !is_array($nuevas[$nombre] ?? null)) {
                continue;
            }
            foreach (self::CAMPOS_CURVA as $campo) {
                if (array_key_exists($campo, $nuevas[$nombre])) {
                    $curvas[$nombre][$campo] = $nuevas[$nombre][$campo];
                }
            }
        }
        if ($curvas) {
            $resultado['curvas'] = $curvas;
        }

        // El docente tiene que saber que el informe se tocó después de
        // cerrar la atención: no es lo mismo que haberlo entregado así.
        $revisiones = is_array($guardado['revisiones'] ?? null) ? $guardado['revisiones'] : [];
        $revisiones[] = $cuando;
        $resultado['revisiones'] = $revisiones;

        return $resultado;
    }
}
