<?php

/**
 * Línea de tiempo del paciente: las atenciones previas del caso más las
 * atenciones del propio alumno, en un solo orden cronológico.
 *
 * Iban en dos listas separadas, y la del alumno se ordenaba por la fecha
 * COMO STRING ("dd-MM-yy"): "05-01-26" quedaba antes que "10-12-25" porque
 * alfabéticamente el 0 va antes que el 1. En un paciente atendido en dos
 * rondas a fin de año, el historial salía al revés.
 *
 * Las llaves {{N}} de la historia clínica se resuelven contra la fecha de
 * ESTA cita (N = días de diferencia, negativo hacia atrás), igual que en el
 * cliente de escritorio -- ver resolver_fechas_historia_clinica en
 * src/core/ficha.py. Es lo que permite que el mismo caso sirva en cualquier
 * fecha sin reescribir la ficha.
 */
final class HistoriaClinica
{
    /** Fecha de agenda ("dd-MM-yy") -> objeto, o null si no se puede leer. */
    public static function parseFechaAgenda(?string $fecha): ?DateTimeImmutable
    {
        if (!$fecha) {
            return null;
        }
        $dt = DateTimeImmutable::createFromFormat('d-m-y', $fecha);
        return $dt === false ? null : $dt->setTime(0, 0);
    }

    /** Reemplaza cada {{N}} por la fecha real, N días respecto de la cita. */
    public static function resolverFechas(string $texto, ?string $fechaCitaStr): string
    {
        $fechaCita = self::parseFechaAgenda($fechaCitaStr);
        if ($texto === '' || $fechaCita === null) {
            // Sin fecha de cita se deja la llave a la vista: mejor eso que
            // una fecha inventada (mismo criterio que el cliente).
            return $texto;
        }
        return (string) preg_replace_callback(
            '/\{\{([+-]?\d+)\}\}/',
            static function (array $m) use ($fechaCita): string {
                $dias = (int) $m[1];
                return $fechaCita->modify(($dias >= 0 ? '+' : '') . $dias . ' days')->format('d-m-Y');
            },
            $texto
        );
    }

    /**
     * Une las atenciones previas del caso con las del alumno y las ordena.
     *
     * @param string $historia    cases.data/patients.historia_clinica, sin resolver
     * @param string|null $fechaCita fecha de esta cita ("dd-MM-yy")
     * @param array<int,array{fecha:?string, hora_real:?string, nota:?string}> $atenciones
     *        Atenciones cerradas del alumno con este paciente, esta incluida.
     * @return list<array{fecha:string, hora:string, texto:string, propia:bool}>
     */
    public static function lineaTiempo(string $historia, ?string $fechaCita, array $atenciones): array
    {
        $entradas = [];

        foreach (explode("\n", self::resolverFechas($historia, $fechaCita)) as $linea) {
            $linea = trim($linea);
            if ($linea === '') {
                continue;
            }
            // La fecha ya resuelta encabeza la línea: se separa para poder
            // ordenarla y para mostrarla igual que las del alumno.
            $fecha = '';
            $texto = $linea;
            if (preg_match('/^(\d{2}-\d{2}-\d{4})\s*(.*)$/s', $linea, $m) === 1) {
                $fecha = $m[1];
                $texto = trim($m[2]);
            }
            $orden = DateTimeImmutable::createFromFormat('d-m-Y', $fecha ?: '');
            $entradas[] = [
                'fecha' => $fecha,
                'hora' => '',
                'texto' => $texto,
                'propia' => false,
                // Una línea sin fecha legible va al principio y conserva el
                // orden en que la escribió el docente.
                '_orden' => $orden === false ? PHP_INT_MIN : $orden->setTime(0, 0)->getTimestamp(),
            ];
        }

        foreach ($atenciones as $a) {
            $fechaTxt = (string) ($a['fecha'] ?? '');
            $dt = self::parseFechaAgenda($fechaTxt);
            $hora = (string) ($a['hora_real'] ?? '');
            $entradas[] = [
                // La agenda guarda "dd-MM-yy" y la historia clínica queda en
                // "dd-MM-yyyy": mezclados en una misma lista se leen como si
                // fueran formatos distintos de fechas distintas.
                'fecha' => $dt !== null ? $dt->format('d-m-Y') : $fechaTxt,
                'hora' => $hora,
                'texto' => trim((string) ($a['nota'] ?? '')),
                'propia' => true,
                // Una atención sin fecha legible es la de ahora: al final.
                '_orden' => $dt === null
                    ? PHP_INT_MAX
                    : $dt->getTimestamp() + self::segundosDelDia($hora),
            ];
        }

        // usort es estable desde PHP 8: las entradas con la misma clave
        // conservan el orden en que se cargaron (la historia primero).
        usort($entradas, static fn(array $a, array $b) => $a['_orden'] <=> $b['_orden']);

        return array_map(static function (array $e): array {
            unset($e['_orden']);
            return $e;
        }, $entradas);
    }

    /** Segundos desde medianoche de una hora "HH:MM:SS", 0 si no se entiende. */
    private static function segundosDelDia(string $hora): int
    {
        if (preg_match('/^(\d{1,2}):(\d{2})(?::(\d{2}))?$/', $hora, $m) !== 1) {
            return 0;
        }
        return ((int) $m[1]) * 3600 + ((int) $m[2]) * 60 + (int) ($m[3] ?? 0);
    }
}
