<?php

declare(strict_types=1);

require_once __DIR__ . '/Osce.php';
require_once __DIR__ . '/LlmChat.php';
require_once __DIR__ . '/AnamnesisDraft.php';

/**
 * Estación de preguntas del OSCE (paso 3 de docs/osce_plan.md).
 *
 * El alumno responde en una tablet de la estación (student/osce_estacion.php,
 * sin login: la tablet se abre con el token de la estación y el alumno
 * escribe su código). La corrección es automática:
 *
 * - alternativa: por clave. Con una correcta, todo o nada; con varias
 *   ("marca todas las correctas"), (aciertos − marcas incorrectas) / correctas,
 *   nunca bajo 0.
 * - desarrollo: la IA lo corrige contra la pauta que escribió el docente
 *   (puntaje en pasos de 0,5 y una justificación para el alumno).
 *
 * Después, a mano: el docente revisa, ajusta el puntaje, escribe el
 * feedback y, ya publicados los resultados, resuelve las réplicas que el
 * alumno manda desde la página de su QR.
 */
final class OscePreguntas
{
    public const TIPOS = ['alternativa' => 'Alternativas', 'desarrollo' => 'Desarrollo (corrige la IA)'];

    public const PROMPT_IA = <<<'TXT'
Eres el corrector de una evaluación práctica tipo OSCE de Tecnología Médica,
mención Otorrinolaringología (electrofisiología auditiva y vestibular). Corriges
UNA respuesta de desarrollo de un estudiante contra la pauta que escribió el
docente.

Reglas:
- Evalúa solo con lo que pide la pauta. No agregues criterios propios ni
  exijas lo que la pauta no pide.
- Si la pauta reparte puntaje entre elementos, respétalo. Si no, asigna el
  puntaje en proporción a lo que la respuesta cubre de la pauta.
- Acepta sinónimos, abreviaturas clínicas y redacción informal si el concepto
  es correcto. La ortografía no descuenta salvo que cambie el sentido.
- Un error conceptual grave (por ejemplo, invertir una relación o un valor
  normal) descuenta aunque el resto esté bien.
- Respuesta vacía o sin relación con la pregunta: puntaje 0.
- El puntaje va de 0 al máximo indicado, en pasos de 0,5.

La justificación va dirigida al estudiante, en español de Chile, de 2 a 4
frases, en tono respetuoso y concreto: qué estuvo bien y qué faltó según la
pauta. No menciones que eres una IA ni hables de "la pauta del docente": habla
del contenido.

Responde SOLO con este JSON, sin texto alrededor ni bloques de código:
{"puntaje": <número>, "justificacion": "<texto>"}
TXT;

    // -- Preguntas (editor) -----------------------------------------------

    public static function preguntas(int $estacionId): array
    {
        Osce::migrar();
        $stmt = Db::get()->prepare('SELECT * FROM osce_pregunta WHERE estacion_id = ? ORDER BY orden, id');
        $stmt->execute([$estacionId]);
        return array_map([self::class, 'decodificar'], $stmt->fetchAll());
    }

    private static function decodificar(array $q): array
    {
        $q['opciones'] = json_decode((string) $q['alternativas'], true) ?: [];
        $q['correctas'] = array_map('intval', json_decode((string) $q['clave'], true) ?: []);
        return $q;
    }

    /**
     * Valida una pregunta del editor. Alternativas: una por línea; las
     * correctas empiezan con "*".
     */
    public static function limpiar(array $in): array
    {
        $tipo = (string) ($in['tipo'] ?? 'alternativa');
        if (!isset(self::TIPOS[$tipo])) {
            throw new InvalidArgumentException('Tipo de pregunta no válido.');
        }
        $enunciado = trim((string) ($in['enunciado'] ?? ''));
        if ($enunciado === '') {
            throw new InvalidArgumentException('Falta el enunciado.');
        }
        $puntaje = (float) str_replace(',', '.', (string) ($in['puntaje'] ?? '1'));
        if ($puntaje <= 0 || $puntaje > 100) {
            throw new InvalidArgumentException('Puntaje: mayor que 0 y hasta 100.');
        }
        $opciones = [];
        $correctas = [];
        $pauta = trim((string) ($in['pauta'] ?? ''));
        if ($tipo === 'alternativa') {
            foreach (preg_split('/\r?\n/', (string) ($in['opciones'] ?? '')) ?: [] as $linea) {
                $linea = trim($linea);
                if ($linea === '') {
                    continue;
                }
                if ($linea[0] === '*') {
                    $correctas[] = count($opciones);
                    $linea = trim(substr($linea, 1));
                }
                $opciones[] = mb_substr($linea, 0, 500);
            }
            if (count($opciones) < 2) {
                throw new InvalidArgumentException('Una pregunta de alternativas necesita al menos dos opciones.');
            }
            if (!$correctas) {
                throw new InvalidArgumentException('Marca la(s) correcta(s) con "*" al inicio de la línea.');
            }
        } elseif ($pauta === '') {
            throw new InvalidArgumentException('Una pregunta de desarrollo necesita pauta: es con lo que corrige la IA.');
        }
        return [
            'tipo' => $tipo,
            'enunciado' => mb_substr($enunciado, 0, 3000),
            'alternativas' => json_encode($opciones, JSON_UNESCAPED_UNICODE),
            'clave' => json_encode($correctas),
            'pauta' => mb_substr($pauta, 0, 4000),
            'puntaje' => $puntaje,
        ];
    }

    /** Texto del editor para las opciones: una por línea, "*" en las correctas. */
    public static function opcionesTexto(array $q): string
    {
        $lineas = [];
        foreach ($q['opciones'] as $i => $o) {
            $lineas[] = (in_array($i, $q['correctas'], true) ? '*' : '') . $o;
        }
        return implode("\n", $lineas);
    }

    public static function agregar(int $estacionId, array $q): void
    {
        Db::reintentar(static function () use ($estacionId, $q): void {
            $pdo = Db::get();
            $stmt = $pdo->prepare('SELECT COALESCE(MAX(orden), 0) + 1 FROM osce_pregunta WHERE estacion_id = ?');
            $stmt->execute([$estacionId]);
            $orden = (int) $stmt->fetchColumn();
            $stmt->closeCursor();
            $pdo->prepare('INSERT INTO osce_pregunta (estacion_id, orden, tipo, enunciado, alternativas, clave, pauta, puntaje) VALUES (?, ?, ?, ?, ?, ?, ?, ?)')
                ->execute([$estacionId, $orden, $q['tipo'], $q['enunciado'], $q['alternativas'], $q['clave'], $q['pauta'], $q['puntaje']]);
        });
    }

    public static function editar(int $estacionId, int $id, array $q): void
    {
        Db::reintentar(static function () use ($estacionId, $id, $q): void {
            Db::get()->prepare('UPDATE osce_pregunta SET tipo = ?, enunciado = ?, alternativas = ?, clave = ?, pauta = ?, puntaje = ? WHERE id = ? AND estacion_id = ?')
                ->execute([$q['tipo'], $q['enunciado'], $q['alternativas'], $q['clave'], $q['pauta'], $q['puntaje'], $id, $estacionId]);
        });
    }

    public static function quitar(int $estacionId, int $id): void
    {
        Db::reintentar(static function () use ($estacionId, $id): void {
            Db::get()->prepare('DELETE FROM osce_pregunta WHERE id = ? AND estacion_id = ?')->execute([$id, $estacionId]);
        });
    }

    public static function mover(int $estacionId, int $id, int $dir): void
    {
        $ids = array_map('intval', array_column(self::preguntas($estacionId), 'id'));
        $i = array_search($id, $ids, true);
        $j = $i === false ? false : $i + ($dir < 0 ? -1 : 1);
        if ($i === false || $j < 0 || $j >= count($ids)) {
            return;
        }
        [$ids[$i], $ids[$j]] = [$ids[$j], $ids[$i]];
        Db::reintentar(static function () use ($estacionId, $ids): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $upd = $pdo->prepare('UPDATE osce_pregunta SET orden = ? WHERE id = ? AND estacion_id = ?');
            foreach ($ids as $k => $qid) {
                $upd->execute([$k + 1, $qid, $estacionId]);
            }
            $pdo->commit();
        });
    }

    // -- GIFT ---------------------------------------------------------------

    /**
     * Lee preguntas en formato GIFT (el de Moodle): opción múltiple con
     * = (correcta) y ~ (incorrecta, ~%50% cuenta como correcta), verdadero/falso
     * ({T}/{F}) y ensayo ({}). Los ensayos quedan sin pauta: hay que
     * escribirla antes de usarlos. Lo que no entiende lo devuelve en 'errores'.
     *
     * @return array{preguntas: array<int, array>, errores: string[]}
     */
    public static function leerGift(string $texto): array
    {
        $texto = str_replace(["\r\n", "\r"], "\n", $texto);
        // Comentarios de línea y marcas de categoría.
        $lineas = array_filter(explode("\n", $texto), static function (string $l): bool {
            $t = ltrim($l);
            return strpos($t, '//') !== 0 && strpos($t, '$CATEGORY') !== 0;
        });
        $bloques = preg_split('/\n\s*\n/', implode("\n", $lineas)) ?: [];
        $preguntas = [];
        $errores = [];
        $escape = static fn (string $s): string => str_replace(['\\=', '\\~', '\\#', '\\{', '\\}', '\\:'], ['=', '~', '#', '{', '}', ':'], $s);
        foreach ($bloques as $n => $b) {
            $b = trim($b);
            if ($b === '') {
                continue;
            }
            // Llave de respuestas sin escapar.
            if (!preg_match('/^(.*?)(?<!\\\\)\{(.*)(?<!\\\\)\}(.*)$/s', $b, $m)) {
                $errores[] = 'Bloque ' . ($n + 1) . ': sin {respuestas}.';
                continue;
            }
            $enunciado = trim($m[1] . ' ' . $m[3]);
            $enunciado = trim((string) preg_replace('/^::.*?::/s', '', $enunciado));
            $enunciado = (string) preg_replace('/^\[(html|markdown|plain|moodle)\]/', '', $enunciado);
            $enunciado = trim($escape(strip_tags($enunciado)));
            $cuerpo = trim($m[2]);
            if ($enunciado === '') {
                $errores[] = 'Bloque ' . ($n + 1) . ': sin enunciado.';
                continue;
            }
            if ($cuerpo === '') {
                $preguntas[] = ['tipo' => 'desarrollo', 'enunciado' => $enunciado, 'opciones' => [], 'correctas' => [], 'pauta' => '', 'puntaje' => 1.0];
                continue;
            }
            if (preg_match('/^(T|TRUE|F|FALSE)\b/i', $cuerpo, $vf)) {
                $verdadero = in_array(strtoupper($vf[1]), ['T', 'TRUE'], true);
                $preguntas[] = ['tipo' => 'alternativa', 'enunciado' => $enunciado, 'opciones' => ['Verdadero', 'Falso'],
                                'correctas' => [$verdadero ? 0 : 1], 'pauta' => '', 'puntaje' => 1.0];
                continue;
            }
            $partes = preg_split('/(?<!\\\\)(?=[=~])/', $cuerpo) ?: [];
            $opciones = [];
            $correctas = [];
            foreach ($partes as $parte) {
                $parte = trim($parte);
                if ($parte === '' || ($parte[0] !== '=' && $parte[0] !== '~')) {
                    continue;
                }
                $correcta = $parte[0] === '=';
                $parte = substr($parte, 1);
                if (preg_match('/^%(-?\d+(?:\.\d+)?)%/', $parte, $pct)) {
                    $correcta = (float) $pct[1] > 0;
                    $parte = substr($parte, strlen($pct[0]));
                }
                $parte = (string) preg_replace('/(?<!\\\\)#.*$/s', '', $parte);   // feedback
                $parte = trim($escape(strip_tags($parte)));
                if (strpos($parte, '->') !== false || $parte === '') {
                    $opciones = [];
                    break; // emparejamiento u otra cosa: no se importa
                }
                if ($correcta) {
                    $correctas[] = count($opciones);
                }
                $opciones[] = $parte;
            }
            if (count($opciones) < 2 || !$correctas) {
                $errores[] = 'Bloque ' . ($n + 1) . ' ("' . mb_substr($enunciado, 0, 40) . '…"): tipo no soportado (solo alternativas, V/F y ensayo).';
                continue;
            }
            $preguntas[] = ['tipo' => 'alternativa', 'enunciado' => $enunciado, 'opciones' => $opciones,
                            'correctas' => $correctas, 'pauta' => '', 'puntaje' => 1.0];
        }
        return ['preguntas' => $preguntas, 'errores' => $errores];
    }

    /** Importa lo leído del GIFT. Los ensayos entran con una pauta por llenar. */
    public static function importarGift(int $estacionId, string $texto): array
    {
        $r = self::leerGift($texto);
        foreach ($r['preguntas'] as $q) {
            self::agregar($estacionId, [
                'tipo' => $q['tipo'],
                'enunciado' => mb_substr($q['enunciado'], 0, 3000),
                'alternativas' => json_encode($q['opciones'], JSON_UNESCAPED_UNICODE),
                'clave' => json_encode($q['correctas']),
                'pauta' => $q['tipo'] === 'desarrollo' ? '(Falta la pauta: escríbela antes del OSCE)' : '',
                'puntaje' => $q['puntaje'],
            ]);
        }
        return ['importadas' => count($r['preguntas']), 'errores' => $r['errores']];
    }

    // -- Corrección ------------------------------------------------------

    /**
     * Puntaje de una pregunta de alternativas. $marcadas son índices
     * originales (antes de barajar).
     */
    public static function puntajeAlternativa(array $correctas, array $marcadas, float $puntaje): float
    {
        $marcadas = array_values(array_unique(array_map('intval', $marcadas)));
        if (!$correctas || !$marcadas) {
            return 0.0;
        }
        if (count($correctas) === 1) {
            return $marcadas === $correctas ? $puntaje : 0.0;
        }
        $aciertos = count(array_intersect($marcadas, $correctas));
        $errores = count($marcadas) - $aciertos;
        return round(max(0.0, ($aciertos - $errores) / count($correctas)) * $puntaje, 2);
    }

    /** Lee la respuesta JSON del corrector IA; null si no sirve. */
    public static function parsearIa(string $raw, float $max): ?array
    {
        $clean = trim($raw);
        if (substr($clean, 0, 3) === '```') {
            $clean = trim((string) preg_replace('/^```[a-zA-Z]*\n?|```$/', '', $clean));
        }
        if (!preg_match('/\{.*\}/s', $clean, $m)) {
            return null;
        }
        $d = json_decode($m[0], true);
        if (!is_array($d) || !isset($d['puntaje']) || !is_numeric($d['puntaje'])) {
            return null;
        }
        $p = round(((float) $d['puntaje']) * 2) / 2;
        return [
            'puntaje' => max(0.0, min($max, $p)),
            'justificacion' => trim((string) ($d['justificacion'] ?? '')),
        ];
    }

    /** Orden en que este alumno ve las opciones (barajado fijo por alumno y pregunta). */
    public static function ordenOpciones(int $participanteId, int $preguntaId, int $n): array
    {
        $orden = range(0, $n - 1);
        usort($orden, static fn ($a, $b) => crc32("osce:{$participanteId}:{$preguntaId}:{$a}") <=> crc32("osce:{$participanteId}:{$preguntaId}:{$b}"));
        return $orden;
    }

    // -- Tablet de la estación ------------------------------------------------

    /** Token de la tablet de la estación (se crea la primera vez). */
    public static function tokenTablet(int $estacionId): string
    {
        $e = Osce::estacion($estacionId);
        $cfg = json_decode((string) ($e['config'] ?? '{}'), true) ?: [];
        if (!empty($cfg['tablet_token'])) {
            return (string) $cfg['tablet_token'];
        }
        $cfg['tablet_token'] = bin2hex(random_bytes(12));
        Db::reintentar(static function () use ($estacionId, $cfg): void {
            Db::get()->prepare('UPDATE osce_estacion SET config = ? WHERE id = ?')
                ->execute([json_encode($cfg, JSON_UNESCAPED_UNICODE), $estacionId]);
        });
        return (string) $cfg['tablet_token'];
    }

    /** Estación por el token de su tablet. */
    public static function estacionPorToken(string $token): ?array
    {
        Osce::migrar();
        if (!preg_match('/^[0-9a-f]{24}$/', $token)) {
            return null;
        }
        $stmt = Db::get()->prepare("SELECT * FROM osce_estacion WHERE config LIKE ?");
        $stmt->execute(['%"tablet_token":"' . $token . '"%']);
        $row = $stmt->fetch();
        $stmt->closeCursor();
        return $row ?: null;
    }

    /**
     * ¿Puede este alumno responder ahora en esta estación? Devuelve el
     * motivo si no.
     */
    public static function motivoNoPuede(array $o, array $est, array $p): ?string
    {
        if ($o['estado'] === 'borrador') {
            return 'El OSCE aún no parte.';
        }
        if ($o['estado'] !== 'en_curso') {
            return 'El OSCE ya terminó.';
        }
        $estaciones = Osce::estaciones((int) $o['id']);
        $indice = (int) array_search((int) $est['id'], array_map('intval', array_column($estaciones, 'id')), true);
        $stmt = Db::get()->prepare('SELECT COUNT(*) FROM osce_participante WHERE osce_id = ?');
        $stmt->execute([(int) $o['id']]);
        $cfg = Osce::cfgReloj($o, count($estaciones), (int) $stmt->fetchColumn());
        $stmt->closeCursor();
        $t = Osce::transcurrido($o, time());
        if ($t === null || !Osce::enVentana($cfg, $p, $indice, $t)) {
            return 'Según el reloj, ahora no te toca esta estación. Revisa tu tarjeta.';
        }
        $stmt = Db::get()->prepare('SELECT estado FROM osce_entrega WHERE participante_id = ? AND estacion_id = ?');
        $stmt->execute([(int) $p['id'], (int) $est['id']]);
        $estado = $stmt->fetchColumn();
        $stmt->closeCursor();
        if ($estado === 'enviada') {
            return 'Ya entregaste esta estación.';
        }
        return null;
    }

    /** Lo que ve el alumno en la tablet: preguntas sin clave, opciones barajadas, y lo que ya respondió. */
    public static function paraAlumno(array $est, array $p): array
    {
        $guardadas = self::respuestas((int) $est['id'], (int) $p['id']);
        $out = [];
        foreach (self::preguntas((int) $est['id']) as $q) {
            $item = [
                'id' => (int) $q['id'],
                'tipo' => $q['tipo'],
                'enunciado' => $q['enunciado'],
                'puntaje' => (float) $q['puntaje'],
                'respuesta' => $guardadas[(int) $q['id']] ?? null,
            ];
            if ($q['tipo'] === 'alternativa') {
                $orden = self::ordenOpciones((int) $p['id'], (int) $q['id'], count($q['opciones']));
                $item['opciones'] = array_map(static fn ($i) => ['i' => $i, 'texto' => $q['opciones'][$i]], $orden);
                $item['varias'] = count($q['correctas']) > 1;
            }
            $out[] = $item;
        }
        return $out;
    }

    /** Respuestas guardadas de un alumno: pregunta_id => valor (lista de índices o texto). */
    public static function respuestas(int $estacionId, int $participanteId): array
    {
        $stmt = Db::get()->prepare(
            'SELECT r.pregunta_id, r.valor FROM osce_resultado r JOIN osce_entrega e ON e.id = r.entrega_id
              WHERE e.estacion_id = ? AND e.participante_id = ? AND r.pregunta_id IS NOT NULL'
        );
        $stmt->execute([$estacionId, $participanteId]);
        $out = [];
        foreach ($stmt->fetchAll() as $r) {
            $out[(int) $r['pregunta_id']] = json_decode((string) $r['valor'], true);
        }
        return $out;
    }

    /**
     * Guarda las respuestas del alumno. Al entregar, corrige las
     * alternativas; las de desarrollo quedan para la IA (corregirIa).
     * Lo ya corregido por el docente no se pisa.
     *
     * @param array<int|string, mixed> $respuestas pregunta_id => lista de índices o texto
     */
    public static function guardarRespuestas(int $estacionId, int $participanteId, array $respuestas, bool $entregar): array
    {
        $preguntas = self::preguntas($estacionId);
        Db::reintentar(static function () use ($estacionId, $participanteId, $respuestas, $entregar, $preguntas): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $pdo->prepare(
                "INSERT INTO osce_entrega (participante_id, estacion_id) VALUES (?, ?)
                 ON CONFLICT (participante_id, estacion_id) DO NOTHING"
            )->execute([$participanteId, $estacionId]);
            $stmt = $pdo->prepare('SELECT id, estado FROM osce_entrega WHERE participante_id = ? AND estacion_id = ?');
            $stmt->execute([$participanteId, $estacionId]);
            $en = $stmt->fetch();
            $stmt->closeCursor();
            if ($en['estado'] === 'enviada') {
                $pdo->rollBack();
                return;
            }
            $entregaId = (int) $en['id'];
            $stmt = $pdo->prepare('SELECT pregunta_id, id FROM osce_resultado WHERE entrega_id = ? AND pregunta_id IS NOT NULL');
            $stmt->execute([$entregaId]);
            $existentes = [];
            foreach ($stmt->fetchAll() as $r) {
                $existentes[(int) $r['pregunta_id']] = (int) $r['id'];
            }
            $ins = $pdo->prepare("INSERT INTO osce_resultado (entrega_id, pregunta_id, valor, puntaje, fuente) VALUES (?, ?, ?, ?, ?)");
            $upd = $pdo->prepare('UPDATE osce_resultado SET valor = ?, puntaje = ?, fuente = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?');
            foreach ($preguntas as $q) {
                $qid = (int) $q['id'];
                $raw = $respuestas[$qid] ?? $respuestas[(string) $qid] ?? null;
                if ($q['tipo'] === 'alternativa') {
                    $valor = array_values(array_filter(is_array($raw) ? array_map('intval', $raw) : [],
                        static fn ($i) => $i >= 0 && $i < count($q['opciones'])));
                    $pts = $entregar ? self::puntajeAlternativa($q['correctas'], $valor, (float) $q['puntaje']) : null;
                    $fuente = 'auto';
                } else {
                    $valor = mb_substr(is_string($raw) ? $raw : '', 0, 8000);
                    // Vacío no necesita IA: 0 al entregar.
                    $pts = $entregar && trim($valor) === '' ? 0.0 : null;
                    $fuente = 'ia';
                }
                $json = json_encode($valor, JSON_UNESCAPED_UNICODE);
                if (isset($existentes[$qid])) {
                    $upd->execute([$json, $pts, $fuente, $existentes[$qid]]);
                } else {
                    $ins->execute([$entregaId, $qid, $json, $pts, $fuente]);
                }
            }
            if ($entregar) {
                $pdo->prepare("UPDATE osce_entrega SET estado = 'enviada', enviada_at = CURRENT_TIMESTAMP WHERE id = ?")->execute([$entregaId]);
            }
            $pdo->commit();
        });
        self::recalcular($estacionId, $participanteId);
        return ['estado' => $entregar ? 'enviada' : 'en_curso'];
    }

    /** Suma la entrega: lo no corregido cuenta 0 y queda como pendiente. */
    public static function recalcular(int $estacionId, int $participanteId): void
    {
        $preguntas = self::preguntas($estacionId);
        $max = array_sum(array_map(static fn ($q) => (float) $q['puntaje'], $preguntas));
        Db::reintentar(static function () use ($estacionId, $participanteId, $max): void {
            $pdo = Db::get();
            $pdo->prepare(
                'UPDATE osce_entrega SET puntaje_max = ?,
                        puntaje = (SELECT COALESCE(SUM(puntaje), 0) FROM osce_resultado WHERE entrega_id = osce_entrega.id AND pregunta_id IS NOT NULL)
                  WHERE participante_id = ? AND estacion_id = ?'
            )->execute([$max, $participanteId, $estacionId]);
        });
    }

    /**
     * Entregas que quedaron abiertas después de su tiempo (la tablet no
     * alcanzó a entregar: se cortó la red o se cerró): se entregan con lo
     * guardado.
     */
    public static function cerrarVencidas(array $o, array $est): int
    {
        if ($o['inicio_epoch'] === null) {
            return 0;
        }
        $estaciones = Osce::estaciones((int) $o['id']);
        $indice = (int) array_search((int) $est['id'], array_map('intval', array_column($estaciones, 'id')), true);
        $parts = Osce::participantes((int) $o['id']);
        $cfg = Osce::cfgReloj($o, count($estaciones), count($parts));
        $t = Osce::transcurrido($o, time());
        $cerradas = 0;
        $stmt = Db::get()->prepare("SELECT participante_id FROM osce_entrega WHERE estacion_id = ? AND estado = 'en_curso'");
        $stmt->execute([(int) $est['id']]);
        $abiertas = array_map('intval', $stmt->fetchAll(PDO::FETCH_COLUMN));
        foreach ($parts as $p) {
            if (!in_array((int) $p['id'], $abiertas, true)) {
                continue;
            }
            $v = Osce::ventana($cfg, $p, $indice);
            if ($o['estado'] !== 'en_curso' || $t > $v['fin_s'] + max(30, $cfg['pausa_s'])) {
                self::guardarRespuestas((int) $est['id'], (int) $p['id'], self::respuestas((int) $est['id'], (int) $p['id']), true);
                $cerradas++;
            }
        }
        return $cerradas;
    }

    /** Resultados de desarrollo entregados que aún no tienen puntaje. */
    public static function pendientesIa(int $estacionId, ?int $participanteId = null): array
    {
        $sql = "SELECT r.id FROM osce_resultado r
                  JOIN osce_entrega e ON e.id = r.entrega_id
                  JOIN osce_pregunta q ON q.id = r.pregunta_id
                 WHERE e.estacion_id = ? AND e.estado = 'enviada' AND q.tipo = 'desarrollo' AND r.puntaje IS NULL";
        $args = [$estacionId];
        if ($participanteId !== null) {
            $sql .= ' AND e.participante_id = ?';
            $args[] = $participanteId;
        }
        $stmt = Db::get()->prepare($sql . ' ORDER BY r.id');
        $stmt->execute($args);
        return array_map('intval', $stmt->fetchAll(PDO::FETCH_COLUMN));
    }

    /**
     * Corrige con IA una respuesta de desarrollo. Lanza si la IA no está
     * configurada o no responde: quien llama decide (la tablet lo ignora,
     * la revisión del docente lo muestra).
     */
    public static function corregirIa(int $resultadoId): array
    {
        $stmt = Db::get()->prepare(
            "SELECT r.id, r.valor, r.puntaje, e.estacion_id, e.participante_id, q.enunciado, q.pauta, q.puntaje AS maximo,
                    p.user_id, o.course_id
               FROM osce_resultado r
               JOIN osce_entrega e ON e.id = r.entrega_id
               JOIN osce_pregunta q ON q.id = r.pregunta_id
               JOIN osce_participante p ON p.id = e.participante_id
               JOIN osce o ON o.id = p.osce_id
              WHERE r.id = ? AND q.tipo = 'desarrollo'"
        );
        $stmt->execute([$resultadoId]);
        $r = $stmt->fetch();
        $stmt->closeCursor();   // viene la llamada al LLM y después la escritura
        if (!$r) {
            throw new InvalidArgumentException('Respuesta no encontrada.');
        }
        if (!LlmConfig::get()['active']) {
            throw new RuntimeException('La IA está desactivada (Admin → IA Paciente).');
        }
        $respuesta = (string) json_decode((string) $r['valor'], true);
        $max = (float) $r['maximo'];
        $mensaje = "PREGUNTA:\n" . $r['enunciado']
            . "\n\nPAUTA (puntaje máximo " . rtrim(rtrim(number_format($max, 2, '.', ''), '0'), '.') . "):\n" . $r['pauta']
            . "\n\nRESPUESTA DEL ESTUDIANTE:\n" . ($respuesta === '' ? '(vacía)' : $respuesta);
        $presupuesto = AnamnesisDraft::maxTokens();
        $opciones = [
            'model' => AnamnesisDraft::model(),
            'max_tokens' => $presupuesto,
            'timeout' => AnamnesisDraft::TIMEOUT_S,
            'campo_tokens' => 'Máximo de tokens del borrador de anamnesis',
            'tarea' => 'osce',
            'course_id' => (int) $r['course_id'],
            'user_id' => (int) $r['user_id'],
        ];
        try {
            $raw = LlmChat::reply(self::PROMPT_IA, [], $mensaje, $opciones);
        } catch (LlmBudgetException $e) {
            $reintento = AnamnesisDraft::retryBudget($presupuesto);
            if ($reintento <= $presupuesto) {
                throw $e;
            }
            $opciones['max_tokens'] = $reintento;
            $raw = LlmChat::reply(self::PROMPT_IA, [], $mensaje, $opciones);
        }
        $v = self::parsearIa($raw, $max);
        if ($v === null) {
            throw new RuntimeException('La IA no devolvió un puntaje legible.');
        }
        Db::reintentar(static function () use ($resultadoId, $v): void {
            // Si el docente ya puso puntaje mientras tanto, se respeta el suyo.
            Db::get()->prepare(
                "UPDATE osce_resultado SET ia_puntaje = ?, ia_comentario = ?,
                        puntaje = CASE WHEN fuente = 'docente' THEN puntaje ELSE ? END,
                        updated_at = CURRENT_TIMESTAMP
                  WHERE id = ?"
            )->execute([$v['puntaje'], $v['justificacion'], $v['puntaje'], $resultadoId]);
        });
        self::recalcular((int) $r['estacion_id'], (int) $r['participante_id']);
        return $v;
    }

    // -- Revisión del docente -------------------------------------------------

    /** Entregas de la estación con cada respuesta, para la revisión. */
    public static function revision(int $estacionId): array
    {
        $pdo = Db::get();
        $stmt = $pdo->prepare(
            'SELECT e.*, p.codigo, u.display_name FROM osce_entrega e
               JOIN osce_participante p ON p.id = e.participante_id
               JOIN users u ON u.id = p.user_id
              WHERE e.estacion_id = ? ORDER BY p.vuelta, p.circuito, p.puesto'
        );
        $stmt->execute([$estacionId]);
        $entregas = $stmt->fetchAll();
        $stmt = $pdo->prepare(
            'SELECT r.*, rp.id AS replica_id, rp.texto AS replica_texto, rp.respuesta AS replica_respuesta,
                    rp.estado AS replica_estado
               FROM osce_resultado r
               JOIN osce_entrega e ON e.id = r.entrega_id
               LEFT JOIN osce_replica rp ON rp.resultado_id = r.id
              WHERE e.estacion_id = ? AND r.pregunta_id IS NOT NULL'
        );
        $stmt->execute([$estacionId]);
        $porEntrega = [];
        foreach ($stmt->fetchAll() as $r) {
            $r['valor'] = json_decode((string) $r['valor'], true);
            $porEntrega[(int) $r['entrega_id']][(int) $r['pregunta_id']] = $r;
        }
        foreach ($entregas as &$e) {
            $e['respuestas'] = $porEntrega[(int) $e['id']] ?? [];
        }
        return $entregas;
    }

    /**
     * Lo que el docente cambia en la revisión de un alumno: puntaje y
     * feedback por respuesta, feedback general, y la resolución de las
     * réplicas. Un puntaje distinto del que había pasa a ser del docente.
     *
     * @param array<int|string, array{puntaje?:string, comentario?:string}> $porResultado
     * @param array<int|string, array{respuesta?:string, estado?:string}> $replicas
     */
    public static function guardarRevision(int $estacionId, int $entregaId, array $porResultado, array $replicas,
                                           string $feedback, int $evaluadorId): void
    {
        $preguntas = [];
        foreach (self::preguntas($estacionId) as $q) {
            $preguntas[(int) $q['id']] = $q;
        }
        $pdo = Db::get();
        $stmt = $pdo->prepare('SELECT id, pregunta_id, puntaje FROM osce_resultado WHERE entrega_id = ? AND pregunta_id IS NOT NULL');
        $stmt->execute([$entregaId]);
        $actuales = [];
        foreach ($stmt->fetchAll() as $r) {
            $actuales[(int) $r['id']] = $r;
        }
        $stmt = $pdo->prepare('SELECT participante_id FROM osce_entrega WHERE id = ? AND estacion_id = ?');
        $stmt->execute([$entregaId, $estacionId]);
        $participanteId = (int) $stmt->fetchColumn();
        $stmt->closeCursor();
        if ($participanteId === 0) {
            throw new InvalidArgumentException('Entrega no encontrada.');
        }
        Db::reintentar(static function () use ($pdo, $porResultado, $replicas, $actuales, $preguntas, $feedback, $entregaId, $evaluadorId): void {
            $pdo->beginTransaction();
            $upd = $pdo->prepare("UPDATE osce_resultado SET puntaje = ?, comentario = ?, fuente = CASE WHEN ? THEN 'docente' ELSE fuente END,
                                         evaluador_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?");
            foreach ($porResultado as $rid => $d) {
                $rid = (int) $rid;
                if (!isset($actuales[$rid])) {
                    continue;
                }
                $max = (float) ($preguntas[(int) $actuales[$rid]['pregunta_id']]['puntaje'] ?? 0);
                $raw = trim(str_replace(',', '.', (string) ($d['puntaje'] ?? '')));
                $antes = $actuales[$rid]['puntaje'];
                $pts = $raw === '' || !is_numeric($raw) ? ($antes === null ? null : (float) $antes) : max(0.0, min($max, (float) $raw));
                $cambio = $pts !== null && ($antes === null || abs((float) $antes - $pts) > 0.001);
                $upd->execute([$pts, mb_substr(trim((string) ($d['comentario'] ?? '')), 0, 2000), $cambio ? 1 : 0, $evaluadorId, $rid]);
            }
            $updR = $pdo->prepare(
                "UPDATE osce_replica SET respuesta = ?, estado = ?,
                        resuelta_at = CASE WHEN ? = 'pendiente' THEN NULL ELSE COALESCE(resuelta_at, CURRENT_TIMESTAMP) END
                  WHERE id = ? AND resultado_id IN (SELECT id FROM osce_resultado WHERE entrega_id = ?)"
            );
            foreach ($replicas as $repId => $d) {
                $estado = (string) ($d['estado'] ?? 'pendiente');
                if (!in_array($estado, ['pendiente', 'aceptada', 'rechazada'], true)) {
                    $estado = 'pendiente';
                }
                $updR->execute([mb_substr(trim((string) ($d['respuesta'] ?? '')), 0, 2000), $estado, $estado, (int) $repId, $entregaId]);
            }
            $pdo->prepare('UPDATE osce_entrega SET feedback = ? WHERE id = ?')->execute([mb_substr($feedback, 0, 4000), $entregaId]);
            $pdo->commit();
        });
        self::recalcular($estacionId, $participanteId);
    }

    // -- Réplica del alumno ----------------------------------------------------

    /**
     * El alumno pide revisar una respuesta (con los resultados publicados).
     * Una réplica por respuesta.
     */
    public static function replicar(int $participanteId, int $resultadoId, string $texto): void
    {
        $texto = trim($texto);
        if ($texto === '') {
            throw new InvalidArgumentException('Escribe en qué no estás de acuerdo.');
        }
        $stmt = Db::get()->prepare(
            "SELECT r.id FROM osce_resultado r JOIN osce_entrega e ON e.id = r.entrega_id
               JOIN osce_estacion es ON es.id = e.estacion_id
               JOIN osce o ON o.id = es.osce_id
              WHERE r.id = ? AND e.participante_id = ? AND es.tipo = 'preguntas' AND o.estado = 'publicado'"
        );
        $stmt->execute([$resultadoId, $participanteId]);
        $ok = $stmt->fetchColumn();
        $stmt->closeCursor();
        if (!$ok) {
            throw new InvalidArgumentException('No se puede hacer réplica de esa respuesta.');
        }
        Db::reintentar(static function () use ($resultadoId, $texto): void {
            $pdo = Db::get();
            $stmt = $pdo->prepare('SELECT COUNT(*) FROM osce_replica WHERE resultado_id = ?');
            $stmt->execute([$resultadoId]);
            $ya = (int) $stmt->fetchColumn();
            $stmt->closeCursor();
            if ($ya > 0) {
                throw new InvalidArgumentException('Ya hiciste réplica de esta respuesta.');
            }
            $pdo->prepare('INSERT INTO osce_replica (resultado_id, texto) VALUES (?, ?)')->execute([$resultadoId, mb_substr($texto, 0, 2000)]);
        });
    }

    /** Detalle de la estación de preguntas para la página del alumno (con sus réplicas). */
    public static function detalleAlumno(int $estacionId, int $participanteId): array
    {
        $preguntas = self::preguntas($estacionId);
        $stmt = Db::get()->prepare(
            'SELECT r.*, rp.texto AS replica_texto, rp.respuesta AS replica_respuesta, rp.estado AS replica_estado
               FROM osce_resultado r JOIN osce_entrega e ON e.id = r.entrega_id
               LEFT JOIN osce_replica rp ON rp.resultado_id = r.id
              WHERE e.estacion_id = ? AND e.participante_id = ? AND r.pregunta_id IS NOT NULL'
        );
        $stmt->execute([$estacionId, $participanteId]);
        $res = [];
        foreach ($stmt->fetchAll() as $r) {
            $res[(int) $r['pregunta_id']] = $r;
        }
        $out = [];
        foreach ($preguntas as $q) {
            $r = $res[(int) $q['id']] ?? null;
            $out[] = ['pregunta' => $q, 'resultado' => $r, 'valor' => $r ? json_decode((string) $r['valor'], true) : null];
        }
        return $out;
    }
}
