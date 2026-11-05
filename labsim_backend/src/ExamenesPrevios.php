<?php

declare(strict_types=1);

/**
 * Exámenes que el paciente trae impresos a la cita, marcados por el docente
 * en el caso (cases.data['examenes_previos']). Valen para toda cita, del
 * curso o de práctica: el paciente solo entrega lo que está acá (más, en la
 * práctica libre, las hojas del libro que manda la app). Lo que la historia
 * cuenta y no está marcado, el paciente sabe que se lo hicieron pero no lo
 * trajo: no se deriva nada de la historia, porque un lactante terminaría
 * "entregando" la audiometría que viene a hacerse.
 *
 * Cada examen: ['dias' => -N (días antes de la cita, como {{-N}} en la
 * historia), 'prueba' => nombre con que lo dice la hoja, 'OD' => resultado,
 * 'OI' => resultado]. La app dibuja la hoja (core/ficha.py) con eso y nada
 * más: el resultado de cada oído.
 */
final class ExamenesPrevios
{
    public const MAX = 8;
    /** Sugerencias del formulario: el resultado es texto libre. */
    public const RESULTADOS = ['Pasa', 'Refiere', 'No evaluable', 'Normal', 'Alterado'];

    /**
     * Del POST (arrays paralelos prev_dias[], prev_prueba[], prev_od[],
     * prev_oi[]) a la lista que se guarda. Una fila sin nombre de prueba no
     * cuenta; dos con el mismo nombre se distinguen con un número, porque el
     * nombre es con lo que el paciente la entrega en el chat.
     *
     * @return list<array{dias:int, prueba:string, OD:string, OI:string}>
     */
    public static function fromForm(array $v): array
    {
        $lista = [];
        $vistos = [];
        foreach (array_keys((array) ($v['prev_prueba'] ?? [])) as $i) {
            $campo = static function (string $k) use ($v, $i): string {
                return trim(mb_substr((string) (((array) ($v[$k] ?? []))[$i] ?? ''), 0, 80));
            };
            // Coma y corchetes no: el nombre viaja en la marca [ENTREGA: a, b].
            $prueba = trim((string) preg_replace('/\s+/', ' ', strtr($campo('prev_prueba'), ',[]', '   ')));
            if ($prueba === '') {
                continue;
            }
            $base = $prueba;
            $n = 2;
            while (isset($vistos[mb_strtolower($prueba)])) {
                $prueba = $base . ' (' . $n++ . ')';
            }
            $vistos[mb_strtolower($prueba)] = true;
            $dias = abs((int) $campo('prev_dias'));
            $lista[] = [
                'dias' => -max(1, min(36500, $dias)),
                'prueba' => $prueba,
                'OD' => $campo('prev_od'),
                'OI' => $campo('prev_oi'),
            ];
            // Lo que concluyó quien lo hizo; vacío, la app lo arma con el resultado.
            $conclusion = trim(mb_substr((string) (((array) ($v['prev_conclusion'] ?? []))[$i] ?? ''), 0, 300));
            if ($conclusion !== '') {
                $lista[count($lista) - 1]['conclusion'] = $conclusion;
            }
            if (count($lista) >= self::MAX) {
                break;
            }
        }
        usort($lista, static function (array $a, array $b): int {
            return $a['dias'] <=> $b['dias'];
        });
        return $lista;
    }

    /**
     * Los del caso, validados (un caso viejo no los tiene).
     *
     * @return list<array{dias:int, prueba:string, OD:string, OI:string}>
     */
    public static function delCaso(array $caseData): array
    {
        $lista = [];
        foreach ((array) ($caseData['examenes_previos'] ?? []) as $e) {
            if (!is_array($e) || trim((string) ($e['prueba'] ?? '')) === '') {
                continue;
            }
            $lista[] = [
                'dias' => (int) ($e['dias'] ?? -1),
                'prueba' => trim((string) $e['prueba']),
                'OD' => trim((string) ($e['OD'] ?? '')),
                'OI' => trim((string) ($e['OI'] ?? '')),
            ] + (trim((string) ($e['conclusion'] ?? '')) !== '' ? ['conclusion' => trim((string) $e['conclusion'])] : []);
        }
        return $lista;
    }

    /** @return list<string> */
    public static function nombres(array $caseData): array
    {
        return array_map(static function (array $e): string {
            return $e['prueba'];
        }, self::delCaso($caseData));
    }
}
