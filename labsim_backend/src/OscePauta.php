<?php

declare(strict_types=1);

require_once __DIR__ . '/Osce.php';

/**
 * Estación de pauta docente del OSCE (paso 2 de docs/osce_plan.md): el
 * docente evalúa en vivo, ítem por ítem, en una tablet. Hay dos tipos de
 * ítem:
 *
 * - tick: cumple (puntaje completo), parcial (la mitad) o no cumple (0).
 * - impedancias: el docente anota el valor de cada cable en kΩ y el sistema
 *   calcula el interelectrodo (mayor − menor, y la tabla par a par) contra
 *   los límites del examen. Puntaje completo si cumplen el límite por
 *   electrodo y el interelectrodo, la mitad si cumple uno, 0 si ninguno.
 *
 * Un ítem crítico en "no cumple" (o impedancias en 0) deja la estación
 * reprobada aunque sume puntos (osce_entrega.critico_fallado).
 *
 * Las pautas precargadas salen del Protocolo Técnico ORL 2019: PEATC
 * clínico, PEAAT (AABR), cVEMP, oVEMP y estado estable. ECochG y latencias
 * media y tardía no están en ese protocolo: su montaje es el del simulador
 * (src/abr/protocols.py, src/abr/ecochg.py) y la página lo avisa.
 */
final class OscePauta
{
    public const TICK = ['cumple' => 'Cumple', 'parcial' => 'Parcial', 'no_cumple' => 'No cumple'];

    /**
     * Montaje por examen: electrodos (nombre del cable y sitio), límites en
     * kΩ (inter = null: el protocolo solo pide "similares", se muestra la
     * diferencia sin puntuarla), zonas que se limpian, posición del paciente
     * y transductor.
     */
    public const MONTAJES = [
        'peatc' => [
            'fuente' => 'Protocolo Técnico ORL 2019 · PEATC clínico',
            'electrodos' => [['Blanco (activo)', 'Vértex'], ['Negro (tierra)', 'Sobre una ceja'],
                             ['Rojo (referencia)', 'Mastoide derecha'], ['Azul (referencia)', 'Mastoide izquierda']],
            'max_kohm' => 5.0, 'inter_kohm' => 2.0,
            'zonas' => 'zona central de la frente, sobre una ceja y detrás de ambos oídos',
            'posicion' => 'Paciente en decúbito dorsal sobre la camilla',
            'transductor' => 'Fonos de inserción según el tamaño del conducto: rojo en OD, azul en OI',
            'material_extra' => 'otoscopio, riñón metálico, fonos de inserción, manta',
        ],
        'aabr' => [
            'fuente' => 'Protocolo Técnico ORL 2019 · PEAAT (GSI AudioScreener+)',
            'electrodos' => [['Negro (activo)', 'Vértex'], ['Rojo (referencia)', 'Mastoide derecha'],
                             ['Azul (referencia)', 'Mastoide izquierda']],
            'max_kohm' => 12.0, 'inter_kohm' => null,
            'zonas' => 'zona central de la frente y detrás de ambos oídos',
            'posicion' => 'Paciente en camilla, incubadora, cuna o en brazos del cuidador, cómodo',
            'transductor' => 'Oliva de la sonda según el tamaño del conducto; un oído y luego el otro',
            'material_extra' => 'otoscopio, riñón metálico, olivas de sonda de distintos tamaños, formularios de PEAAT',
        ],
        'estado_estable' => [
            'fuente' => 'Protocolo Técnico ORL 2019 · Potenciales de estado estable',
            'electrodos' => [['Blanco (positivo)', 'Vértex o línea media del cabello'], ['Negro (tierra)', 'Sobre la ceja izquierda'],
                             ['Rojo', 'Mastoide derecha'], ['Azul', 'Mastoide izquierda']],
            'max_kohm' => 3.0, 'inter_kohm' => null,
            'zonas' => 'vértex o línea del cabello, ceja izquierda y ambas mastoides (norma 10/20)',
            'posicion' => 'Paciente sentado o en la camilla, tranquilo, para que entre en sueño fisiológico',
            'transductor' => 'Fonos colocados después de los electrodos',
            'material_extra' => 'pads adhesivos desechables, otoscopio, fonos',
        ],
        'cvemp' => [
            'fuente' => 'Protocolo Técnico ORL 2019 · cVEMP',
            'electrodos' => [['Tierra', 'Frente (Fpz)'], ['Activo', 'Unión esternoclavicular'],
                             ['Referencia izquierda', 'Tercio superior ECM izquierdo'], ['Referencia derecha', 'Tercio superior ECM derecho']],
            'max_kohm' => 5.0, 'inter_kohm' => 2.0,
            'zonas' => 'frente, unión esternoclavicular y tercio superior de ambos ECM',
            'posicion' => 'Paciente sentado, cómodo',
            'transductor' => 'Fonos para la estimulación aérea',
            'material_extra' => 'otoscopio, crema abrasiva',
        ],
        'ovemp' => [
            'fuente' => 'Protocolo Técnico ORL 2019 · oVEMP',
            'electrodos' => [['Tierra', 'Frente (Fpz)'], ['Activo', 'Mentón'],
                             ['Referencia izquierda', 'Bajo la pupila del ojo derecho'], ['Referencia derecha', 'Bajo la pupila del ojo izquierdo']],
            'max_kohm' => 3.0, 'inter_kohm' => 1.0,
            'zonas' => 'frente, mentón y bajo ambos ojos',
            'posicion' => 'Paciente sentado, cómodo',
            'transductor' => 'Fonos para la estimulación aérea',
            'material_extra' => 'otoscopio, crema abrasiva',
        ],
        'ecochg' => [
            'fuente' => 'No está en el Protocolo 2019: montaje del simulador (ECochG extratimpánica)',
            'electrodos' => [['Activo (+)', 'Vértex'], ['Referencia (−)', 'TipTrode en el conducto del oído evaluado'],
                             ['Tierra', 'Frente']],
            'max_kohm' => 5.0, 'inter_kohm' => 2.0,
            'zonas' => 'vértex, frente y entrada del conducto',
            'posicion' => 'Paciente en decúbito dorsal sobre la camilla',
            'transductor' => 'TipTrode de inserción en el oído evaluado',
            'material_extra' => 'otoscopio, TipTrodes',
        ],
        'latencia_media' => [
            'fuente' => 'No está en el Protocolo 2019: montaje del simulador (vértex–mastoides)',
            'electrodos' => [['Blanco (activo)', 'Vértex'], ['Negro (tierra)', 'Frente'],
                             ['Rojo (referencia)', 'Mastoide derecha'], ['Azul (referencia)', 'Mastoide izquierda']],
            'max_kohm' => 5.0, 'inter_kohm' => 2.0,
            'zonas' => 'vértex, frente y detrás de ambos oídos',
            'posicion' => 'Paciente en decúbito dorsal, relajado',
            'transductor' => 'Fonos de inserción: rojo en OD, azul en OI',
            'material_extra' => 'otoscopio, fonos de inserción',
        ],
        'latencia_tardia' => [
            'fuente' => 'No está en el Protocolo 2019: montaje del simulador (vértex–lóbulos)',
            'electrodos' => [['Blanco (activo)', 'Vértex'], ['Negro (tierra)', 'Frente'],
                             ['Rojo (referencia)', 'Lóbulo derecho'], ['Azul (referencia)', 'Lóbulo izquierdo']],
            'max_kohm' => 5.0, 'inter_kohm' => 2.0,
            'zonas' => 'vértex, frente y ambos lóbulos de las orejas',
            'posicion' => 'Paciente sentado o semisentado, despierto y atento',
            'transductor' => 'Fonos de inserción: rojo en OD, azul en OI',
            'material_extra' => 'otoscopio, fonos de inserción',
        ],
    ];

    public static function montaje(string $examen): array
    {
        return self::MONTAJES[$examen] ?? self::MONTAJES['peatc'];
    }

    /**
     * Pauta de limpieza y preparación de electrodos del examen, como la
     * escribe el protocolo. Cada ítem: texto, puntaje, crítico, tipo, config.
     */
    public static function pautaBase(string $examen): array
    {
        $m = self::montaje($examen);
        $sitios = implode('; ', array_map(static fn ($e) => $e[0] . ': ' . $e[1], $m['electrodos']));
        $tick = static fn (string $t, float $p = 1, bool $c = false): array =>
            ['texto' => $t, 'puntaje' => $p, 'critico' => $c, 'tipo' => 'tick', 'config' => []];
        return [
            $tick('Prepara el material: alcohol, algodón, gel abrasivo, gel conductor, cinta adhesiva, electrodos y cables; ' . $m['material_extra'] . '.'),
            $tick('Enciende y verifica el funcionamiento del equipo.'),
            $tick('Mantiene separadas las áreas limpias y sucias.'),
            $tick('Realiza lavado clínico de manos.', 1, true),
            $tick('Se presenta como estudiante bajo supervisión docente y explica en qué consiste el examen.'),
            $tick('Explica la limpieza (' . $m['zonas'] . ') y que la piel puede quedar enrojecida o hacer una costra que desaparece en pocos días.'),
            $tick('Limpia con alcohol las zonas de los electrodos.'),
            $tick('Aplica gel abrasivo en una sola dirección, sin dañar la piel.'),
            $tick($m['posicion'] . '.'),
            $tick('Montaje: ' . $sitios . '.', 2, true),
            $tick('Usa gel conductor en cada electrodo y los fija con cinta adhesiva.'),
            [
                'texto' => 'Impedancias obtenidas',
                'puntaje' => 2,
                'critico' => false,
                'tipo' => 'impedancias',
                'config' => [
                    'electrodos' => array_map(static fn ($e) => $e[0] . ' · ' . $e[1], $m['electrodos']),
                    'max_kohm' => $m['max_kohm'],
                    'inter_kohm' => $m['inter_kohm'],
                ],
            ],
            $tick('Si alguna impedancia no cumple, repite la limpieza o agrega gel conductor antes de seguir.'),
            $tick($m['transductor'] . '.'),
        ];
    }

    // -- Cálculos puros ---------------------------------------------------

    /** "4,5" o "4.5" a float; vacío o inválido = null. */
    public static function kohm($raw): ?float
    {
        if ($raw === null || is_bool($raw)) {
            return null;
        }
        $s = trim(str_replace(',', '.', (string) $raw));
        if ($s === '' || !is_numeric($s)) {
            return null;
        }
        $v = (float) $s;
        return $v >= 0 && $v < 1000 ? round($v, 2) : null;
    }

    /**
     * Impedancias de un montaje contra sus límites.
     *
     * @param array<int, mixed> $valores kΩ por electrodo, en el orden del montaje
     * @return array{valores: array<int, ?float>, completo: bool, max: ?float, min: ?float,
     *               inter: ?float, pares: array<int, array{0:int, 1:int, 2:float}>,
     *               fuera: int[], ok_abs: ?bool, ok_inter: ?bool}
     */
    public static function impedancias(array $valores, ?float $maxKohm, ?float $interKohm): array
    {
        $v = array_map([self::class, 'kohm'], array_values($valores));
        $medidos = array_filter($v, static fn ($x) => $x !== null);
        $completo = $v !== [] && count($medidos) === count($v);
        $pares = [];
        $n = count($v);
        for ($i = 0; $i < $n; $i++) {
            for ($j = $i + 1; $j < $n; $j++) {
                if ($v[$i] !== null && $v[$j] !== null) {
                    $pares[] = [$i, $j, round(abs($v[$i] - $v[$j]), 2)];
                }
            }
        }
        $fuera = [];
        if ($maxKohm !== null) {
            foreach ($v as $i => $x) {
                if ($x !== null && $x >= $maxKohm) {
                    $fuera[] = $i;
                }
            }
        }
        $max = $medidos ? max($medidos) : null;
        $min = $medidos ? min($medidos) : null;
        $inter = $medidos ? round($max - $min, 2) : null;
        return [
            'valores' => $v,
            'completo' => $completo,
            'max' => $max,
            'min' => $min,
            'inter' => $inter,
            'pares' => $pares,
            'fuera' => $fuera,
            'ok_abs' => $completo && $maxKohm !== null ? $fuera === [] : null,
            'ok_inter' => $completo && $interKohm !== null ? $inter < $interKohm : null,
        ];
    }

    /**
     * Puntaje de un ítem y si deja la estación reprobada.
     *
     * @param array $item fila de osce_item (config ya decodificada en 'cfg')
     * @param mixed $valor tick: 'cumple'|'parcial'|'no_cumple'|''; impedancias: lista de kΩ
     * @return array{puntaje: float, critico_fallado: bool, marcado: bool, calculo: ?array}
     */
    public static function evaluarItem(array $item, $valor): array
    {
        $p = (float) $item['puntaje'];
        $critico = (int) $item['critico'] === 1;
        if ($item['tipo'] === 'impedancias') {
            $cfg = $item['cfg'] ?? [];
            $valores = is_array($valor) ? $valor : [];
            $nElec = count($cfg['electrodos'] ?? []);
            $valores = array_slice(array_pad(array_values($valores), $nElec, null), 0, $nElec);
            $c = self::impedancias(
                $valores,
                isset($cfg['max_kohm']) ? (float) $cfg['max_kohm'] : null,
                isset($cfg['inter_kohm']) ? (float) $cfg['inter_kohm'] : null
            );
            if (!$c['completo']) {
                return ['puntaje' => 0.0, 'critico_fallado' => false, 'marcado' => false, 'calculo' => $c];
            }
            $checks = array_values(array_filter([$c['ok_abs'], $c['ok_inter']], static fn ($x) => $x !== null));
            $ok = count(array_filter($checks));
            $frac = $checks === [] ? 1.0 : $ok / count($checks);
            return ['puntaje' => round($p * $frac, 2), 'critico_fallado' => $critico && $ok === 0 && $checks !== [],
                    'marcado' => true, 'calculo' => $c];
        }
        $valor = is_string($valor) ? $valor : '';
        switch ($valor) {
            case 'cumple': $pts = $p; break;
            case 'parcial': $pts = $p / 2; break;
            default: $pts = 0.0;
        }
        return [
            'puntaje' => round($pts, 2),
            'critico_fallado' => $critico && $valor === 'no_cumple',
            'marcado' => isset(self::TICK[$valor]),
            'calculo' => null,
        ];
    }

    // -- Base: ítems de la pauta -------------------------------------------

    public static function items(int $estacionId): array
    {
        Osce::migrar();
        $stmt = Db::get()->prepare('SELECT * FROM osce_item WHERE estacion_id = ? ORDER BY orden, id');
        $stmt->execute([$estacionId]);
        return array_map(static function (array $it): array {
            $it['cfg'] = json_decode((string) $it['config'], true) ?: [];
            return $it;
        }, $stmt->fetchAll());
    }

    /** Reemplaza la pauta de la estación por la del protocolo para su examen. */
    public static function cargarBase(int $estacionId, string $examen): void
    {
        $items = self::pautaBase($examen);
        Db::reintentar(static function () use ($estacionId, $items): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $pdo->prepare('DELETE FROM osce_item WHERE estacion_id = ?')->execute([$estacionId]);
            $ins = $pdo->prepare('INSERT INTO osce_item (estacion_id, orden, texto, puntaje, critico, tipo, config) VALUES (?, ?, ?, ?, ?, ?, ?)');
            foreach ($items as $k => $it) {
                $ins->execute([$estacionId, $k + 1, $it['texto'], $it['puntaje'], $it['critico'] ? 1 : 0, $it['tipo'],
                               json_encode($it['config'], JSON_UNESCAPED_UNICODE)]);
            }
            $pdo->commit();
        });
    }

    /** Valida un ítem del editor. Impedancias: un electrodo por línea. */
    public static function limpiarItem(array $in): array
    {
        $texto = trim((string) ($in['texto'] ?? ''));
        if ($texto === '') {
            throw new InvalidArgumentException('El ítem necesita un texto.');
        }
        $tipo = (string) ($in['tipo'] ?? 'tick');
        if (!in_array($tipo, ['tick', 'impedancias'], true)) {
            throw new InvalidArgumentException('Tipo de ítem no válido.');
        }
        $puntaje = (float) str_replace(',', '.', (string) ($in['puntaje'] ?? '1'));
        if ($puntaje <= 0 || $puntaje > 100) {
            throw new InvalidArgumentException('Puntaje del ítem: mayor que 0 y hasta 100.');
        }
        $cfg = [];
        if ($tipo === 'impedancias') {
            $lineas = preg_split('/\r?\n/', (string) ($in['electrodos'] ?? '')) ?: [];
            $elec = array_values(array_filter(array_map('trim', $lineas), static fn ($l) => $l !== ''));
            if (count($elec) < 2) {
                throw new InvalidArgumentException('Impedancias: al menos dos electrodos, uno por línea.');
            }
            $max = self::kohm($in['max_kohm'] ?? null);
            $inter = self::kohm($in['inter_kohm'] ?? null);
            if ($max === null || $max <= 0) {
                throw new InvalidArgumentException('Impedancias: falta el límite por electrodo (kΩ).');
            }
            $cfg = ['electrodos' => array_map(static fn ($l) => mb_substr($l, 0, 80), array_slice($elec, 0, 8)),
                    'max_kohm' => $max, 'inter_kohm' => $inter !== null && $inter > 0 ? $inter : null];
        }
        return ['texto' => mb_substr($texto, 0, 600), 'tipo' => $tipo, 'puntaje' => $puntaje,
                'critico' => !empty($in['critico']) ? 1 : 0, 'config' => json_encode($cfg, JSON_UNESCAPED_UNICODE)];
    }

    public static function agregarItem(int $estacionId, array $in): void
    {
        $it = self::limpiarItem($in);
        Db::reintentar(static function () use ($estacionId, $it): void {
            $pdo = Db::get();
            $stmt = $pdo->prepare('SELECT COALESCE(MAX(orden), 0) + 1 FROM osce_item WHERE estacion_id = ?');
            $stmt->execute([$estacionId]);
            $orden = (int) $stmt->fetchColumn();
            $stmt->closeCursor();
            $pdo->prepare('INSERT INTO osce_item (estacion_id, orden, texto, puntaje, critico, tipo, config) VALUES (?, ?, ?, ?, ?, ?, ?)')
                ->execute([$estacionId, $orden, $it['texto'], $it['puntaje'], $it['critico'], $it['tipo'], $it['config']]);
        });
    }

    public static function editarItem(int $estacionId, int $itemId, array $in): void
    {
        $it = self::limpiarItem($in);
        Db::reintentar(static function () use ($estacionId, $itemId, $it): void {
            Db::get()->prepare('UPDATE osce_item SET texto = ?, tipo = ?, puntaje = ?, critico = ?, config = ? WHERE id = ? AND estacion_id = ?')
                ->execute([$it['texto'], $it['tipo'], $it['puntaje'], $it['critico'], $it['config'], $itemId, $estacionId]);
        });
    }

    public static function quitarItem(int $estacionId, int $itemId): void
    {
        Db::reintentar(static function () use ($estacionId, $itemId): void {
            Db::get()->prepare('DELETE FROM osce_item WHERE id = ? AND estacion_id = ?')->execute([$itemId, $estacionId]);
        });
    }

    public static function moverItem(int $estacionId, int $itemId, int $dir): void
    {
        $ids = array_map('intval', array_column(self::items($estacionId), 'id'));
        $i = array_search($itemId, $ids, true);
        $j = $i === false ? false : $i + ($dir < 0 ? -1 : 1);
        if ($i === false || $j < 0 || $j >= count($ids)) {
            return;
        }
        [$ids[$i], $ids[$j]] = [$ids[$j], $ids[$i]];
        Db::reintentar(static function () use ($estacionId, $ids): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $upd = $pdo->prepare('UPDATE osce_item SET orden = ? WHERE id = ? AND estacion_id = ?');
            foreach ($ids as $k => $id) {
                $upd->execute([$k + 1, $id, $estacionId]);
            }
            $pdo->commit();
        });
    }

    // -- Base: evaluación de un alumno -------------------------------------

    /** Lo guardado para un alumno en esta estación: entrega + valor/comentario por ítem. */
    public static function cargar(int $estacionId, int $participanteId): array
    {
        $pdo = Db::get();
        $stmt = $pdo->prepare('SELECT * FROM osce_entrega WHERE participante_id = ? AND estacion_id = ?');
        $stmt->execute([$participanteId, $estacionId]);
        $en = $stmt->fetch() ?: null;
        $stmt->closeCursor();
        $items = [];
        if ($en !== null) {
            $stmt = $pdo->prepare('SELECT item_id, valor, comentario FROM osce_resultado WHERE entrega_id = ? AND item_id IS NOT NULL');
            $stmt->execute([(int) $en['id']]);
            foreach ($stmt->fetchAll() as $r) {
                $items[(int) $r['item_id']] = ['valor' => json_decode((string) $r['valor'], true), 'comentario' => $r['comentario']];
            }
        }
        return ['entrega' => $en, 'items' => $items];
    }

    /**
     * Guarda la evaluación completa de un alumno (lo que la tablet tenga en
     * pantalla) y recalcula el puntaje en el servidor. $terminar marca la
     * entrega como enviada; se puede seguir corrigiendo hasta publicar.
     *
     * @param array<int|string, array{valor?:mixed, comentario?:string}> $porItem
     * @return array{puntaje: float, puntaje_max: float, critico_fallado: bool, sin_marcar: int, estado: string}
     */
    public static function guardar(int $estacionId, int $participanteId, array $porItem, string $feedback,
                                   bool $terminar, ?int $evaluadorId): array
    {
        $items = self::items($estacionId);
        $total = 0.0;
        $max = 0.0;
        $critico = false;
        $sinMarcar = 0;
        $filas = [];
        foreach ($items as $it) {
            $dato = $porItem[(int) $it['id']] ?? $porItem[(string) $it['id']] ?? [];
            $valor = $dato['valor'] ?? null;
            $r = self::evaluarItem($it, $valor);
            $total += $r['puntaje'];
            $max += (float) $it['puntaje'];
            $critico = $critico || $r['critico_fallado'];
            if (!$r['marcado']) {
                $sinMarcar++;
            }
            $guardar = $it['tipo'] === 'impedancias'
                ? ['kohm' => $r['calculo']['valores'] ?? [], 'calculo' => $r['calculo']]
                : (is_string($valor) && isset(self::TICK[$valor]) ? $valor : '');
            $filas[] = [(int) $it['id'], json_encode($guardar, JSON_UNESCAPED_UNICODE), $r['puntaje'],
                        mb_substr(trim((string) ($dato['comentario'] ?? '')), 0, 2000)];
        }
        $estado = $terminar ? 'enviada' : 'en_curso';
        Db::reintentar(static function () use ($estacionId, $participanteId, $filas, $total, $max, $critico, $feedback, $terminar, $evaluadorId): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $pdo->prepare(
                "INSERT INTO osce_entrega (participante_id, estacion_id, estado, puntaje, puntaje_max, critico_fallado, feedback)
                 VALUES (?, ?, 'en_curso', ?, ?, ?, ?)
                 ON CONFLICT (participante_id, estacion_id) DO UPDATE SET
                    puntaje = excluded.puntaje, puntaje_max = excluded.puntaje_max,
                    critico_fallado = excluded.critico_fallado, feedback = excluded.feedback"
            )->execute([$participanteId, $estacionId, $total, $max, $critico ? 1 : 0, mb_substr($feedback, 0, 4000)]);
            $stmt = $pdo->prepare('SELECT id FROM osce_entrega WHERE participante_id = ? AND estacion_id = ?');
            $stmt->execute([$participanteId, $estacionId]);
            $entregaId = (int) $stmt->fetchColumn();
            $stmt->closeCursor();
            if ($terminar) {
                $pdo->prepare("UPDATE osce_entrega SET estado = 'enviada', enviada_at = COALESCE(enviada_at, CURRENT_TIMESTAMP) WHERE id = ?")
                    ->execute([$entregaId]);
            }
            $pdo->prepare('DELETE FROM osce_resultado WHERE entrega_id = ? AND item_id IS NOT NULL')->execute([$entregaId]);
            $ins = $pdo->prepare(
                "INSERT INTO osce_resultado (entrega_id, item_id, valor, puntaje, comentario, fuente, evaluador_id)
                 VALUES (?, ?, ?, ?, ?, 'docente', ?)"
            );
            foreach ($filas as [$itemId, $valor, $pts, $coment]) {
                $ins->execute([$entregaId, $itemId, $valor, $pts, $coment, $evaluadorId]);
            }
            $pdo->commit();
        });
        $actual = self::cargar($estacionId, $participanteId)['entrega'];
        return [
            'puntaje' => round($total, 2),
            'puntaje_max' => round($max, 2),
            'critico_fallado' => $critico,
            'sin_marcar' => $sinMarcar,
            'estado' => (string) ($actual['estado'] ?? $estado),
        ];
    }

    /** Quiénes ya tienen entrega en la estación: participante_id => estado. */
    public static function estadosEstacion(int $estacionId): array
    {
        $stmt = Db::get()->prepare('SELECT participante_id, estado FROM osce_entrega WHERE estacion_id = ?');
        $stmt->execute([$estacionId]);
        $out = [];
        foreach ($stmt->fetchAll() as $r) {
            $out[(int) $r['participante_id']] = $r['estado'];
        }
        return $out;
    }
}
