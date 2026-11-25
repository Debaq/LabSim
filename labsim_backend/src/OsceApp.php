<?php

declare(strict_types=1);

require_once __DIR__ . '/Osce.php';
require_once __DIR__ . '/OscePauta.php';

/**
 * Estaciones del OSCE que se rinden en la app LabSim (paso 4 de
 * docs/osce_plan.md): configuración del equipo y marcaje de curvas.
 *
 * El PC de la estación entra a LabSim como "Estación OSCE" con el código
 * corto de la estación (app_codigo en osce_estacion.config); cada alumno
 * escribe el suyo y la app abre el ABR con el caso de la estación. Al
 * entregar, la app manda la sesión del ABR tal cual (session_payload), el
 * panel de control y la verdad del generador de cada curva (latencias que
 * el equipo no muestra). Acá se corrige.
 *
 * Cada criterio es un osce_item de tipo 'auto' con su regla en config:
 *
 * - param:  {"fuente": "panel"|"equipo", "clave": "rate", "esperado": "21.1"}
 *           esperado: "a | b" (cualquiera), "10–12" (rango) o un valor.
 * - marca:  {"lado": "OD", "int": 80, "onda": "V", "tol_ms": 0.2}
 *           si en esa curva la onda existe, marcada a ±tol de la verdadera;
 *           si no existe (sin respuesta), no marcarla.
 *
 * La entrega completa queda en una fila de osce_resultado sin ítem
 * (registro): con ella se puede volver a corregir si el docente ajusta la
 * pauta, sin pisar los puntajes que él puso a mano.
 */
final class OsceApp
{
    public const TIPOS = ['config_equipo', 'marcaje'];

    /** Prueba del ABR que abre cada examen (combo "Tipo de prueba" de la app). */
    public const PRUEBA_DE_EXAMEN = [
        'peatc' => 'ABR', 'aabr' => 'ABR', 'general' => 'ABR', 'ecochg' => 'ECochG',
        'latencia_media' => 'MLR', 'latencia_tardia' => 'CAEP', 'estado_estable' => 'ASSR',
        'cvemp' => 'ABR', 'ovemp' => 'ABR',
    ];

    /**
     * Parámetros que se pueden evaluar: clave => [fuente, rótulo].
     * panel = lo que se ve en el panel de control; equipo = Parámetros
     * avanzados (technical).
     */
    public const PARAMETROS = [
        'test' => ['panel', 'Tipo de prueba'],
        'stim' => ['panel', 'Estímulo'],
        'pol' => ['panel', 'Polaridad'],
        'int' => ['panel', 'Intensidad (dB nHL)'],
        'rate' => ['panel', 'Tasa de estimulación (est/s)'],
        'filter_passhigh' => ['panel', 'Filtro pasa alto (Hz)'],
        'filter_down' => ['panel', 'Filtro pasa bajo (Hz)'],
        'average' => ['panel', 'Promediaciones'],
        'side' => ['panel', 'Oído'],
        'window_ms' => ['equipo', 'Ventana de análisis (ms)'],
        'gain' => ['equipo', 'Ganancia'],
        'transducer' => ['equipo', 'Transductor'],
        'artifact_reject_uv' => ['equipo', 'Rechazo de artefacto (µV)'],
    ];

    /**
     * Configuración esperada del PEATC clínico, como la escribe el
     * Protocolo Técnico ORL 2019 (tabla de "Parámetros"). La ventana dice
     * "10 s" en el protocolo: es 10 ms. "Delay 0" no existe en el equipo
     * simulado. La ganancia "10k" es ×10.000. El tipo de prueba no va: la
     * estación ya abre en la prueba de su examen.
     */
    public const ESPERADO_PEATC = [
        'stim' => 'Click | CE-Chirp | CE-Chirp LS | NB CE-Chirp LS 500 Hz | NB CE-Chirp LS 1 kHz | NB CE-Chirp LS 2 kHz | NB CE-Chirp LS 4 kHz | Burst 500 Hz | Burst 1 kHz | Burst 2 kHz | Burst 4 kHz',
        'pol' => 'Alternada',
        'int' => '80',
        'rate' => '21.1',
        'filter_passhigh' => '100',
        'filter_down' => '3000',
        'gain' => '10000',
        'window_ms' => '10',
        'transducer' => 'insert_earphone',
    ];

    /** Curvas que la app registra sola para la estación de marcaje. */
    public const CURVAS_BASE = "OD 80\nOD 60\nOD 40\nOD 20\nOI 80\nOI 60\nOI 40\nOI 20";

    public static function esApp(string $tipo): bool
    {
        return in_array($tipo, self::TIPOS, true);
    }

    public static function config(array $est): array
    {
        return json_decode((string) ($est['config'] ?? '{}'), true) ?: [];
    }

    private static function guardarConfig(int $estacionId, array $cfg): void
    {
        Db::reintentar(static function () use ($estacionId, $cfg): void {
            Db::get()->prepare('UPDATE osce_estacion SET config = ? WHERE id = ?')
                ->execute([json_encode($cfg, JSON_UNESCAPED_UNICODE), $estacionId]);
        });
    }

    // -- Código de la estación -----------------------------------------------

    /** Código corto que se escribe en el PC de la estación (se crea la primera vez). */
    public static function codigoEstacion(int $estacionId): string
    {
        $est = Osce::estacion($estacionId);
        $cfg = self::config($est ?? []);
        if (!empty($cfg['app_codigo'])) {
            return (string) $cfg['app_codigo'];
        }
        do {
            $codigo = Osce::nuevoCodigo();
        } while (self::estacionPorCodigo($codigo) !== null);
        $cfg['app_codigo'] = $codigo;
        self::guardarConfig($estacionId, $cfg);
        return $codigo;
    }

    public static function estacionPorCodigo(string $codigo): ?array
    {
        Osce::migrar();
        $codigo = Osce::normalizarCodigo($codigo);
        if (!preg_match('/^[2-9A-HJKMNP-Z]{3}-[2-9A-HJKMNP-Z]{3}$/', $codigo)) {
            return null;
        }
        $stmt = Db::get()->prepare('SELECT * FROM osce_estacion WHERE config LIKE ?');
        $stmt->execute(['%"app_codigo":"' . $codigo . '"%']);
        $row = $stmt->fetch();
        $stmt->closeCursor();
        return $row ?: null;
    }

    // -- Contenido de la estación (editor) -----------------------------------

    /** Casos con ABR configurado, para elegir el de la estación. */
    public static function casosConAbr(): array
    {
        $stmt = Db::get()->query(
            "SELECT c.id, c.data, p.nombre, p.apellido FROM cases c LEFT JOIN patients p ON p.id = c.patient_id
              WHERE c.archived_at IS NULL ORDER BY p.apellido, p.nombre, c.id"
        );
        $out = [];
        foreach ($stmt->fetchAll() as $c) {
            $data = json_decode((string) $c['data'], true) ?: [];
            if (empty($data['ABR']['OD']) && empty($data['ABR']['OI'])) {
                continue;
            }
            $tipoOd = (string) ($data['ABR']['OD']['type'] ?? '');
            $tipoOi = (string) ($data['ABR']['OI']['type'] ?? '');
            $nombre = trim(($c['nombre'] ?? '') . ' ' . ($c['apellido'] ?? ''));
            $out[] = ['id' => (string) $c['id'], 'rotulo' => ($nombre !== '' ? $nombre : 'Caso ' . $c['id'])
                . ' · OD ' . ($tipoOd ?: '—') . ' / OI ' . ($tipoOi ?: '—')];
        }
        return $out;
    }

    /**
     * Guarda el contenido de una estación de la app y rehace sus ítems.
     * config_equipo: un ítem por parámetro con esperado; marcaje: uno por
     * onda y curva (I, III y V en la intensidad máxima de cada oído, V en
     * las demás).
     */
    public static function guardarContenido(array $est, array $in): void
    {
        $cfg = self::config($est);
        $caseId = trim((string) ($in['case_id'] ?? ''));
        if ($caseId === '') {
            throw new InvalidArgumentException('Elige el caso del paciente de la estación.');
        }
        $cfg['case_id'] = $caseId;
        $cfg['prueba'] = self::PRUEBA_DE_EXAMEN[$est['examen']] ?? 'ABR';
        $items = [];
        if ($est['tipo'] === 'config_equipo') {
            $esperado = [];
            foreach (self::PARAMETROS as $clave => [$fuente, $rotulo]) {
                $valor = trim((string) ($in['esperado'][$clave] ?? ''));
                if ($valor === '') {
                    continue;
                }
                $esperado[$clave] = $valor;
                $items[] = ['texto' => $rotulo, 'puntaje' => (float) str_replace(',', '.', (string) ($in['puntos'][$clave] ?? '1')) ?: 1.0,
                            'critico' => !empty($in['critico'][$clave]),
                            'config' => ['regla' => 'param', 'fuente' => $fuente, 'clave' => $clave, 'esperado' => $valor]];
            }
            if (!$items) {
                throw new InvalidArgumentException('Indica al menos un parámetro esperado.');
            }
            $cfg['esperado'] = $esperado;
        } else {
            $curvas = self::leerCurvas((string) ($in['curvas'] ?? ''));
            if (!$curvas) {
                throw new InvalidArgumentException('Indica las curvas a registrar: una por línea, como "OD 80".');
            }
            $tol = (float) str_replace(',', '.', (string) ($in['tol_ms'] ?? '0.2'));
            if ($tol <= 0 || $tol > 2) {
                throw new InvalidArgumentException('Tolerancia: entre 0,05 y 2 ms.');
            }
            $cfg['curvas'] = $curvas;
            $cfg['tol_ms'] = $tol;
            $maxPorLado = [];
            foreach ($curvas as [$lado, $int]) {
                $maxPorLado[$lado] = max($maxPorLado[$lado] ?? -100, $int);
            }
            foreach ($curvas as [$lado, $int]) {
                $ondas = $int === $maxPorLado[$lado] ? ['I', 'III', 'V'] : ['V'];
                foreach ($ondas as $onda) {
                    $items[] = ['texto' => "{$lado} {$int} dB: onda {$onda}", 'puntaje' => 1.0, 'critico' => false,
                                'config' => ['regla' => 'marca', 'lado' => $lado, 'int' => $int, 'onda' => $onda, 'tol_ms' => $tol]];
                }
            }
        }
        $estId = (int) $est['id'];
        Db::reintentar(static function () use ($estId, $cfg, $items): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $pdo->prepare('UPDATE osce_estacion SET config = ? WHERE id = ?')
                ->execute([json_encode($cfg, JSON_UNESCAPED_UNICODE), $estId]);
            $pdo->prepare('DELETE FROM osce_item WHERE estacion_id = ?')->execute([$estId]);
            $ins = $pdo->prepare("INSERT INTO osce_item (estacion_id, orden, texto, puntaje, critico, tipo, config) VALUES (?, ?, ?, ?, ?, 'auto', ?)");
            foreach ($items as $k => $it) {
                $ins->execute([$estId, $k + 1, $it['texto'], $it['puntaje'], $it['critico'] ? 1 : 0,
                               json_encode($it['config'], JSON_UNESCAPED_UNICODE)]);
            }
            $pdo->commit();
        });
    }

    /** "OD 80" por línea → [["OD", 80], ...] (sin repetidas, en el orden dado). */
    public static function leerCurvas(string $texto): array
    {
        $out = [];
        foreach (preg_split('/[\r\n,;]+/', $texto) ?: [] as $linea) {
            if (!preg_match('/^\s*(OD|OI)\s*(-?\d{1,3})\s*$/i', $linea, $m)) {
                continue;
            }
            $par = [strtoupper($m[1]), (int) $m[2]];
            if ($par[1] < -10 || $par[1] > 110 || in_array($par, $out, true)) {
                continue;
            }
            $out[] = $par;
        }
        return array_slice($out, 0, 16);
    }

    public static function curvasTexto(array $curvas): string
    {
        return implode("\n", array_map(static fn ($c) => $c[0] . ' ' . $c[1], $curvas));
    }

    // -- Corrección (pura) -----------------------------------------------------

    /** ¿El valor cumple lo esperado? "a | b" = cualquiera, "x–y" o "x-y" = rango, si no igual. */
    public static function cumpleEsperado($valor, string $esperado): bool
    {
        if ($valor === null || $valor === '') {
            return false;
        }
        $v = trim((string) $valor);
        $num = static fn (string $s): ?float => is_numeric(str_replace(',', '.', trim($s))) ? (float) str_replace(',', '.', trim($s)) : null;
        if (strpos($esperado, '|') !== false) {
            foreach (explode('|', $esperado) as $opcion) {
                if (self::cumpleEsperado($v, trim($opcion))) {
                    return true;
                }
            }
            return false;
        }
        if (preg_match('/^\s*(-?[\d.,]+)\s*[–-]\s*(-?[\d.,]+)\s*$/u', $esperado, $m)) {
            $x = $num($v);
            $a = $num($m[1]);
            $b = $num($m[2]);
            return $x !== null && $a !== null && $b !== null && $x >= min($a, $b) - 1e-6 && $x <= max($a, $b) + 1e-6;
        }
        $x = $num($v);
        $e = $num($esperado);
        if ($x !== null && $e !== null) {
            return abs($x - $e) < 0.051;
        }
        return mb_strtolower($v) === mb_strtolower(trim($esperado));
    }

    /** Curva de la entrega con ese lado e intensidad (la primera registrada). */
    private static function curvaDe(array $payload, string $lado, int $int): ?array
    {
        foreach (($payload['abr']['curvas'] ?? []) as $nombre => $c) {
            if (($c['side'] ?? '') === $lado && (int) round((float) ($c['int'] ?? -999)) === $int) {
                return ['nombre' => (string) $nombre] + $c;
            }
        }
        return null;
    }

    /**
     * Evalúa un ítem automático contra la entrega.
     *
     * @return array{puntaje: float, ok: bool, alumno: string, esperado: string}
     */
    public static function evaluarItem(array $item, array $payload): array
    {
        $r = $item['cfg'] ?? (json_decode((string) ($item['config'] ?? '{}'), true) ?: []);
        $pts = (float) $item['puntaje'];
        if (($r['regla'] ?? '') === 'param') {
            $fuente = $r['fuente'] === 'equipo' ? ($payload['abr']['equipo'] ?? []) : ($payload['panel'] ?? []);
            $valor = $fuente[$r['clave']] ?? null;
            $ok = self::cumpleEsperado(is_bool($valor) ? ($valor ? 'sí' : 'no') : $valor, (string) $r['esperado']);
            return ['puntaje' => $ok ? $pts : 0.0, 'ok' => $ok,
                    'alumno' => $valor === null ? '—' : self::mostrar($r['clave'], $valor),
                    'esperado' => self::mostrarEsperado($r['clave'], (string) $r['esperado'])];
        }
        if (($r['regla'] ?? '') === 'marca') {
            $curva = self::curvaDe($payload, (string) $r['lado'], (int) $r['int']);
            if ($curva === null) {
                return ['puntaje' => 0.0, 'ok' => false, 'alumno' => 'sin curva', 'esperado' => '—'];
            }
            $verdad = $payload['verdad'][$curva['nombre']] ?? null;
            $onda = (string) $r['onda'];
            $lat = $verdad['waves'][$onda]['lat'] ?? null;
            $existe = $verdad !== null && !empty($verdad['visible']) && $lat !== null;
            $marca = $curva['LatAmp'][$onda][0] ?? null;
            $marca = is_numeric($marca) ? (float) $marca : null;
            $tol = (float) ($r['tol_ms'] ?? 0.2);
            $ok = $existe ? ($marca !== null && abs($marca - (float) $lat) <= $tol + 1e-9) : $marca === null;
            $fmt = static fn (?float $x): string => $x === null ? 'sin marca' : number_format($x, 2, ',', '') . ' ms';
            return ['puntaje' => $ok ? $pts : 0.0, 'ok' => $ok, 'alumno' => $fmt($marca),
                    'esperado' => $existe ? number_format((float) $lat, 2, ',', '') . ' ms ± ' . str_replace('.', ',', (string) $tol)
                                          : 'sin onda ' . $onda . ' (no marcar)'];
        }
        return ['puntaje' => 0.0, 'ok' => false, 'alumno' => '—', 'esperado' => '—'];
    }

    private const ROTULOS_VALOR = [
        'insert_earphone' => 'Fono de inserción', 'TDH39_headphone' => 'Fono de copa (TDH-39)', 'bone_vibrator' => 'Vibrador óseo',
    ];

    private static function mostrar(string $clave, $valor): string
    {
        if ($clave === 'gain' && is_numeric($valor)) {
            return '×' . number_format((float) $valor, 0, ',', '.');
        }
        if (is_numeric($valor)) {
            return rtrim(rtrim(number_format((float) $valor, 2, ',', ''), '0'), ',');
        }
        return self::ROTULOS_VALOR[(string) $valor] ?? (string) $valor;
    }

    private static function mostrarEsperado(string $clave, string $esperado): string
    {
        $partes = array_map('trim', explode('|', $esperado));
        if (count($partes) > 4) {
            return 'cualquiera de ' . count($partes) . ' opciones';
        }
        return implode(' o ', array_map(static fn ($p) => preg_match('/[–-]/u', $p) && !is_numeric($p) ? str_replace('-', '–', $p) : self::mostrar($clave, $p), $partes));
    }

    // -- Entrega ---------------------------------------------------------------

    /**
     * Guarda la entrega de la app (registro completo) y la corrige.
     * Al volver a corregir (docente), lo que el docente puso a mano se respeta.
     */
    public static function entregar(int $estacionId, int $participanteId, array $payload): array
    {
        $json = json_encode($payload, JSON_UNESCAPED_UNICODE);
        if ($json === false || strlen($json) > 6_000_000) {
            throw new InvalidArgumentException('Entrega demasiado grande o ilegible.');
        }
        Db::reintentar(static function () use ($estacionId, $participanteId, $json): void {
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
                throw new InvalidArgumentException('Ya entregaste esta estación.');
            }
            $pdo->prepare('DELETE FROM osce_resultado WHERE entrega_id = ? AND item_id IS NULL AND pregunta_id IS NULL')->execute([(int) $en['id']]);
            $pdo->prepare("INSERT INTO osce_resultado (entrega_id, valor, fuente) VALUES (?, ?, 'registro')")->execute([(int) $en['id'], $json]);
            $pdo->prepare("UPDATE osce_entrega SET estado = 'enviada', enviada_at = CURRENT_TIMESTAMP WHERE id = ?")->execute([(int) $en['id']]);
            $pdo->commit();
        });
        return self::corregir($estacionId, $participanteId);
    }

    /** La entrega guardada (registro) de un alumno, o null. */
    public static function registro(int $estacionId, int $participanteId): ?array
    {
        $stmt = Db::get()->prepare(
            "SELECT r.valor FROM osce_resultado r JOIN osce_entrega e ON e.id = r.entrega_id
              WHERE e.estacion_id = ? AND e.participante_id = ? AND r.fuente = 'registro'"
        );
        $stmt->execute([$estacionId, $participanteId]);
        $v = $stmt->fetchColumn();
        $stmt->closeCursor();
        return $v === false ? null : (json_decode((string) $v, true) ?: []);
    }

    /** Corrige (o vuelve a corregir) una entrega con los ítems actuales. */
    public static function corregir(int $estacionId, int $participanteId): array
    {
        $payload = self::registro($estacionId, $participanteId) ?? [];
        $items = OscePauta::items($estacionId);
        $pdo = Db::get();
        $stmt = $pdo->prepare('SELECT id FROM osce_entrega WHERE estacion_id = ? AND participante_id = ?');
        $stmt->execute([$estacionId, $participanteId]);
        $entregaId = (int) $stmt->fetchColumn();
        $stmt->closeCursor();
        $stmt = $pdo->prepare("SELECT item_id, puntaje, comentario, fuente FROM osce_resultado WHERE entrega_id = ? AND item_id IS NOT NULL");
        $stmt->execute([$entregaId]);
        $previos = [];
        foreach ($stmt->fetchAll() as $r) {
            $previos[(int) $r['item_id']] = $r;
        }
        $total = 0.0;
        $max = 0.0;
        $critico = false;
        $filas = [];
        foreach ($items as $it) {
            $e = self::evaluarItem($it, $payload);
            $prev = $previos[(int) $it['id']] ?? null;
            $manual = $prev !== null && $prev['fuente'] === 'docente';
            $pts = $manual ? (float) $prev['puntaje'] : $e['puntaje'];
            $total += $pts;
            $max += (float) $it['puntaje'];
            $critico = $critico || ((int) $it['critico'] === 1 && $pts <= 0.0);
            $filas[] = [(int) $it['id'], json_encode($e, JSON_UNESCAPED_UNICODE), $pts, $prev['comentario'] ?? '', $manual ? 'docente' : 'auto'];
        }
        Db::reintentar(static function () use ($pdo, $entregaId, $filas, $total, $max, $critico): void {
            $pdo->beginTransaction();
            $pdo->prepare('DELETE FROM osce_resultado WHERE entrega_id = ? AND item_id IS NOT NULL')->execute([$entregaId]);
            $ins = $pdo->prepare('INSERT INTO osce_resultado (entrega_id, item_id, valor, puntaje, comentario, fuente) VALUES (?, ?, ?, ?, ?, ?)');
            foreach ($filas as $f) {
                $ins->execute(array_merge([$entregaId], $f));
            }
            $pdo->prepare('UPDATE osce_entrega SET puntaje = ?, puntaje_max = ?, critico_fallado = ? WHERE id = ?')
                ->execute([$total, $max, $critico ? 1 : 0, $entregaId]);
            $pdo->commit();
        });
        return ['puntaje' => round($total, 2), 'puntaje_max' => round($max, 2), 'critico_fallado' => $critico];
    }

    /** Lo que ve el docente (y el alumno, publicado): ítem, valor del alumno, esperado, puntaje. */
    public static function detalle(int $estacionId, int $participanteId): array
    {
        $stmt = Db::get()->prepare(
            "SELECT r.* FROM osce_resultado r JOIN osce_entrega e ON e.id = r.entrega_id
              WHERE e.estacion_id = ? AND e.participante_id = ? AND r.item_id IS NOT NULL"
        );
        $stmt->execute([$estacionId, $participanteId]);
        $res = [];
        foreach ($stmt->fetchAll() as $r) {
            $res[(int) $r['item_id']] = $r;
        }
        $out = [];
        foreach (OscePauta::items($estacionId) as $it) {
            $r = $res[(int) $it['id']] ?? null;
            $out[] = ['item' => $it, 'resultado' => $r, 'eval' => $r ? (json_decode((string) $r['valor'], true) ?: []) : null];
        }
        return $out;
    }

    /**
     * Revisión del docente: puntaje y comentario por ítem y feedback
     * general. Un puntaje distinto del automático pasa a ser del docente.
     */
    public static function guardarRevision(int $estacionId, int $participanteId, array $porItem, string $feedback): void
    {
        $detalle = self::detalle($estacionId, $participanteId);
        $stmt = Db::get()->prepare('SELECT id FROM osce_entrega WHERE estacion_id = ? AND participante_id = ?');
        $stmt->execute([$estacionId, $participanteId]);
        $entregaId = (int) $stmt->fetchColumn();
        $stmt->closeCursor();
        if ($entregaId === 0) {
            throw new InvalidArgumentException('Entrega no encontrada.');
        }
        Db::reintentar(static function () use ($detalle, $porItem, $feedback, $entregaId): void {
            $pdo = Db::get();
            $pdo->beginTransaction();
            $upd = $pdo->prepare('UPDATE osce_resultado SET puntaje = ?, comentario = ?, fuente = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?');
            foreach ($detalle as $d) {
                $r = $d['resultado'];
                if ($r === null) {
                    continue;
                }
                $in = $porItem[(int) $d['item']['id']] ?? null;
                if ($in === null) {
                    continue;
                }
                $max = (float) $d['item']['puntaje'];
                $raw = trim(str_replace(',', '.', (string) ($in['puntaje'] ?? '')));
                $auto = (float) ($d['eval']['puntaje'] ?? 0);
                $pts = $raw === '' || !is_numeric($raw) ? (float) $r['puntaje'] : max(0.0, min($max, (float) $raw));
                $fuente = abs($pts - $auto) > 0.001 ? 'docente' : 'auto';
                $upd->execute([$pts, mb_substr(trim((string) ($in['comentario'] ?? '')), 0, 2000), $fuente, (int) $r['id']]);
            }
            $pdo->prepare('UPDATE osce_entrega SET feedback = ? WHERE id = ?')->execute([mb_substr($feedback, 0, 4000), $entregaId]);
            $pdo->commit();
        });
        // Totales con lo que quedó (mismo cálculo que corregir, sin reevaluar).
        $pdo = Db::get();
        $stmt = $pdo->prepare(
            "SELECT COALESCE(SUM(r.puntaje), 0), COALESCE(SUM(i.puntaje), 0),
                    COALESCE(MAX(CASE WHEN i.critico = 1 AND r.puntaje <= 0 THEN 1 ELSE 0 END), 0)
               FROM osce_resultado r JOIN osce_item i ON i.id = r.item_id WHERE r.entrega_id = ?"
        );
        $stmt->execute([$entregaId]);
        [$total, $max, $crit] = $stmt->fetch(PDO::FETCH_NUM);
        $stmt->closeCursor();
        Db::reintentar(static function () use ($pdo, $total, $max, $crit, $entregaId): void {
            $pdo->prepare('UPDATE osce_entrega SET puntaje = ?, puntaje_max = ?, critico_fallado = ? WHERE id = ?')
                ->execute([$total, $max, $crit, $entregaId]);
        });
    }

    // -- Lo que recibe la app al entrar ------------------------------------------

    /** Caso tal como lo usa la app (cases.data, con su id). */
    public static function caso(string $caseId): ?array
    {
        $stmt = Db::get()->prepare('SELECT id, data FROM cases WHERE id = ?');
        $stmt->execute([$caseId]);
        $row = $stmt->fetch();
        $stmt->closeCursor();
        if (!$row) {
            return null;
        }
        $data = json_decode((string) $row['data'], true) ?: [];
        $data['id'] = $data['id'] ?? $row['id'];
        return $data;
    }
}
