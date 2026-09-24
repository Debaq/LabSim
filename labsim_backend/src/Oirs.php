<?php

declare(strict_types=1);

/**
 * Cómo se nombran y se muestran los avisos de la OIRS simulada (ver
 * OirsEvaluator.php, que los genera al cerrar una atención).
 *
 * En la base el tipo sigue siendo 'reclamo' / 'merito' (no se migra nada):
 * lo que cambia es cómo se le NOMBRA a la gente. "Reclamo" con remitente
 * "Oficina de Informaciones, Reclamos y Sugerencias" se leía como una queja
 * real, y hubo una alumna que se puso a llorar: el docente tuvo que
 * explicarle que era parte del juego. Al alumno se le muestra como lo que
 * es -- una sugerencia del paciente simulado -- y con un aviso de que es
 * parte del ejercicio.
 */
final class Oirs
{
    /** Remitente de los avisos nuevos (inbox_messages.remitente). */
    public const REMITENTE = 'OIRS (simulada)';

    /** Nombre de cada tipo de mensaje, para cualquier vista. */
    public const LABELS = [
        'reclamo' => 'Sugerencia de mejora',
        'merito' => 'Felicitación',
        'mensaje' => 'Mensaje docente',
    ];

    /** Asunto que ve el alumno, según el tipo. */
    public const ASUNTOS = [
        'reclamo' => 'Sugerencia de mejora sobre tu atención',
        'merito' => 'Felicitación por tu atención',
    ];

    public const AVISO_ALUMNO = 'Mensaje simulado: lo escribe el paciente virtual del caso según cómo '
        . 'se sintió tratado. Es parte del ejercicio para practicar el trato, no es un reclamo real ni '
        . 'queda en ningún registro fuera de LabSim.';

    /**
     * Deja con remitente y asunto suaves los avisos ya guardados. Los de
     * antes de este cambio decían "OIRS: Aviso de reclamo por atención
     * recibida..." y así se veían en las vistas del docente y en cualquier
     * lugar que leyera la tabla directo. Idempotente y barato: solo toca
     * las filas que todavía no están normalizadas, así que se puede llamar
     * en cada vista que lista mensajes.
     */
    public static function normalizarGuardados(PDO $pdo): void
    {
        foreach (self::ASUNTOS as $tipo => $asunto) {
            $pdo->prepare(
                'UPDATE inbox_messages SET asunto = ?, remitente = ?
                 WHERE tipo = ? AND (asunto <> ? OR remitente <> ?)'
            )->execute([$asunto, self::REMITENTE, $tipo, $asunto, self::REMITENTE]);
        }
    }

    public static function label(string $tipo): string
    {
        return self::LABELS[$tipo] ?? $tipo;
    }

    public static function esDeLaOirs(string $tipo): bool
    {
        return isset(self::ASUNTOS[$tipo]);
    }

    /**
     * El mensaje tal como lo ve el alumno: remitente y asunto suaves y
     * parejos (también los viejos, que se guardaron con "reclamo" en el
     * asunto), el nombre del tipo y el aviso de que es simulado. El cuerpo
     * no se toca: es el motivo, y es lo que sirve para aprender.
     */
    public static function paraAlumno(array $m): array
    {
        $tipo = (string) ($m['tipo'] ?? '');
        $m['tipo_label'] = self::label($tipo);
        if (self::esDeLaOirs($tipo)) {
            $m['remitente'] = self::REMITENTE;
            $m['asunto'] = self::ASUNTOS[$tipo];
            $m['aviso'] = self::AVISO_ALUMNO;
        }
        return $m;
    }
}
