<?php

declare(strict_types=1);

require_once __DIR__ . '/Db.php';

/**
 * Faltas graves de una atención: lo que no se hace nunca, aunque el resto de
 * la técnica esté perfecto. No suman ni restan al porcentaje de la técnica
 * (AudiometriaTecnica): van aparte, en rojo, para el docente y el alumno.
 *
 * Hoy hay una: meter la sonda (o el auricular del contralateral) del
 * impedanciómetro en un oído NR (CaseBuilder::Z_NO_REALIZABLE) -- con
 * secreción ensucia la oliva y la sonda y contagia al próximo oído; con un
 * cuerpo extraño lo empuja; con atresia no hay conducto. La app la registra
 * como `z_no_realizable` y deja el equipo fuera de uso esa atención.
 */
final class FaltasGraves
{
    public const ACCIONES = [
        'z_no_realizable' => 'Usó el impedanciómetro en un oído donde la sonda no iba (no realizable)',
    ];

    /** Qué hizo, en las palabras del equipo, para el detalle. */
    private const PANTALLAS = [
        'tymp' => 'timpanograma',
        'reflex' => 'reflejos',
        'decay' => 'decay del reflejo',
        'etf' => 'función tubaria',
    ];

    /**
     * Faltas por atención.
     *
     * Lee solo las acciones de ACCIONES (pocas filas: no recorre el
     * action_logs del alumno entero) y mira el número de cita en el texto
     * antes de decodificar, igual que AudiometriaTecnica::deAtenciones.
     *
     * @param list<int> $appointmentIds
     * @return array<int,list<array{texto:string, detalle:string, hora:string}>>
     */
    public static function deAtenciones(int $studentId, array $appointmentIds): array
    {
        $quiero = array_flip(array_map('intval', $appointmentIds));
        if (!$quiero) {
            return [];
        }
        $acciones = array_keys(self::ACCIONES);
        $ph = implode(',', array_fill(0, count($acciones), '?'));
        $stmt = Db::get()->prepare(
            "SELECT client_ts, action, payload FROM action_logs WHERE user_id = ? AND action IN ({$ph}) ORDER BY id"
        );
        $stmt->execute(array_merge([$studentId], $acciones));
        $filas = $stmt->fetchAll();
        $stmt->closeCursor();

        $out = [];
        foreach ($filas as $l) {
            if (!preg_match('/"appointment_id":"?(\d+)/', (string) $l['payload'], $m) || !isset($quiero[(int) $m[1]])) {
                continue;
            }
            $out[(int) $m[1]][] = self::describir((string) $l['action'], (array) json_decode((string) $l['payload'], true), (string) $l['client_ts']);
        }
        return $out;
    }

    /**
     * @param array<string,mixed> $payload
     * @return array{texto:string, detalle:string, hora:string}
     */
    public static function describir(string $action, array $payload, string $hora): array
    {
        $detalle = '';
        if ($action === 'z_no_realizable') {
            $pantalla = self::PANTALLAS[(string) ($payload['screen'] ?? '')] ?? 'impedanciómetro';
            $detalle = sprintf('Sonda en %s, %s', (string) ($payload['side'] ?? '?'), $pantalla);
            if (($payload['screen'] ?? '') === 'reflex' || ($payload['screen'] ?? '') === 'decay') {
                $detalle .= ' ' . strtolower((string) ($payload['mode'] ?? ''));
            }
            if (!empty($payload['oido_nr']) && $payload['oido_nr'] !== ($payload['side'] ?? null)) {
                $detalle .= sprintf(' (el auricular iba en %s)', (string) $payload['oido_nr']);
            }
        }
        return [
            'texto' => self::ACCIONES[$action] ?? $action,
            'detalle' => trim($detalle),
            'hora' => substr($hora, 11, 5),
        ];
    }
}
