<?php

// Sin autoloader, igual que el resto de src/: la dependencia se declara
// donde se usa (ver la cabecera de LlmChat.php).
require_once __DIR__ . '/Db.php';
require_once __DIR__ . '/Clock.php';

/**
 * Registro de consumo de la API del LLM.
 *
 * Existe porque DeepSeek NO expone ningún endpoint de consumo: la API solo
 * devuelve el saldo que queda (ver saldo()), y el desglose por día o por
 * modelo vive únicamente en el panel web del proveedor. Si queremos saber
 * qué parte de la factura se va en el chat con el paciente y qué parte en
 * los borradores de anamnesis, hay que anotarlo nosotros, llamada por
 * llamada, con el bloque `usage` que viene en cada respuesta.
 *
 * Se guardan tokens, no plata. El precio cambia (y depende del horario, ver
 * ventana()), así que el costo se calcula al mostrar, con las tarifas que
 * el admin tenga cargadas en ese momento -- así corregir una tarifa mal
 * escrita arregla el histórico entero en vez de dejarlo mal para siempre.
 */
final class LlmUsage
{
    /**
     * Ventanas de precio pleno de DeepSeek, en HORA UTC y solo de lunes a
     * viernes: [desde, hasta). Fuera de esto el precio es la mitad.
     *
     * Traducido a Chile (UTC-4) cae 21:00-00:00 y 02:00-06:00, o sea que
     * todo el horario de clases chileno paga la tarifa rebajada sin que
     * nadie tenga que hacer nada. Se registra igual la ventana de cada
     * llamada porque el día que se agende algo de madrugada, o que el
     * proveedor mueva la franja, el histórico tiene que seguir cuadrando.
     */
    public const PEAK_WINDOWS_UTC = [[1, 4], [6, 10]];

    /** Lo que se paga fuera de la franja de precio pleno. */
    public const OFFPEAK_FACTOR = 0.5;

    /**
     * Los descuentos por horario son de DeepSeek. Un backend compatible con
     * OpenAI (LM Studio, un proxy propio) cobra plano o no cobra, así que
     * ahí toda llamada se anota como precio pleno y la tarifa que cargue el
     * admin se aplica tal cual.
     */
    public const PROVIDERS_CON_HORARIO = ['deepseek'];

    /**
     * Cuánto se guarda. Una fila por llamada: con 14 alumnos conversando no
     * es nada, pero tampoco tiene sentido arrastrar el detalle de hace tres
     * años cuando lo que se mira es el mes.
     */
    public const RETENCION_DIAS = 365;

    /**
     * Zona en la que se cortan los días del informe. Sin esto el corte
     * queda a las 21:00 hora de Chile (CURRENT_TIMESTAMP de SQLite es UTC)
     * y "hoy" arranca la noche anterior, que al mirar el panel no se
     * entiende. El desfase de una hora del horario de verano no se
     * persigue: mueve una llamada de borde entre dos días, no el total.
     *
     * Es la zona de la aplicación (ver Clock): se deja el alias para no
     * renombrar los usos, pero la declaración vive en un solo lugar.
     */
    public const ZONA_INFORME = Clock::ZONA;

    /** Tareas conocidas, en el orden en que se muestran. La clave es lo que se guarda. */
    public const TAREAS = [
        'chat_paciente' => 'Chat con el paciente',
        'sala' => 'Chat con acompañantes',
        'anamnesis' => 'Borrador de anamnesis',
        'oirs' => 'Evaluador OIRS',
        'prueba' => 'Pruebas del admin',
        '' => 'Sin clasificar',
    ];

    /**
     * ¿La llamada cae en precio pleno ("peak") o rebajado ("offpeak")?
     *
     * $ts en epoch (UTC); null = ahora.
     */
    public static function ventana(string $provider, ?int $ts = null): string
    {
        if (!in_array($provider, self::PROVIDERS_CON_HORARIO, true)) {
            return 'peak';
        }
        $ts = $ts ?? time();
        // gmdate y no date: el hosting puede tener cualquier zona por
        // defecto, y la franja del proveedor está definida en UTC.
        $diaSemana = (int) gmdate('N', $ts); // 1 = lunes .. 7 = domingo
        if ($diaSemana >= 6) {
            return 'offpeak';
        }
        $minutos = ((int) gmdate('G', $ts)) * 60 + (int) gmdate('i', $ts);
        foreach (self::PEAK_WINDOWS_UTC as $franja) {
            if ($minutos >= $franja[0] * 60 && $minutos < $franja[1] * 60) {
                return 'peak';
            }
        }
        return 'offpeak';
    }

    /**
     * Normaliza el bloque `usage` de la respuesta a lo que se guarda.
     *
     * El desglose de cache es lo que decide la factura y no lo que se
     * intuye mirando el total: un token que pegó en cache cuesta unas 50
     * veces menos que uno que no. Si el proveedor no lo reporta (cualquier
     * backend que no sea DeepSeek), se asume que no hubo cache y todo el
     * prompt entra como miss -- de más, nunca de menos.
     *
     * `completion_tokens` YA incluye los de razonamiento; `razonamiento` se
     * guarda aparte solo para poder mostrar cuánto del gasto se fue en
     * pensar, y no se suma al costo por separado.
     *
     * @param array<string,mixed> $usage Bloque `usage` crudo de la respuesta
     * @return array<string,int>
     */
    public static function normalizar(array $usage): array
    {
        $prompt = (int) ($usage['prompt_tokens'] ?? 0);
        $hit = (int) ($usage['prompt_cache_hit_tokens'] ?? 0);
        $miss = isset($usage['prompt_cache_miss_tokens'])
            ? (int) $usage['prompt_cache_miss_tokens']
            : max(0, $prompt - $hit);

        return [
            'prompt' => $prompt,
            'cache_hit' => $hit,
            'cache_miss' => $miss,
            'completion' => (int) ($usage['completion_tokens'] ?? 0),
            'razonamiento' => (int) ($usage['completion_tokens_details']['reasoning_tokens'] ?? 0),
            'total' => (int) ($usage['total_tokens'] ?? 0),
        ];
    }

    /**
     * Anota una llamada. NUNCA lanza: esto corre en el camino del chat del
     * alumno, y quedarse sin la estadística es molesto, pero cortarle la
     * conversación por no poder escribir una fila de contabilidad sería
     * bastante peor.
     *
     * $ctx: tarea, model, provider, course_id, user_id, ok.
     *
     * @param array<string,int> $tokens Salida de normalizar()
     * @param array<string,mixed> $ctx
     */
    public static function registrar(array $tokens, array $ctx): void
    {
        // Una llamada que no gastó nada no es una llamada: es un error de
        // red o un proveedor que no reporta `usage`. Anotarla ensucia el
        // promedio por llamada sin agregar información.
        if (($tokens['total'] ?? 0) <= 0 && ($tokens['prompt'] ?? 0) <= 0) {
            return;
        }
        try {
            self::asegurarTabla();
            $stmt = Db::get()->prepare(
                'INSERT INTO llm_usage (tarea, model, provider, course_id, user_id,
                        cache_hit, cache_miss, completion, razonamiento, total, ventana, ok)
                 VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'
            );
            $cursoId = (int) ($ctx['course_id'] ?? 0);
            $usuarioId = (int) ($ctx['user_id'] ?? 0);
            $stmt->execute([
                (string) ($ctx['tarea'] ?? ''),
                (string) ($ctx['model'] ?? ''),
                (string) ($ctx['provider'] ?? ''),
                $cursoId > 0 ? $cursoId : null,
                $usuarioId > 0 ? $usuarioId : null,
                (int) $tokens['cache_hit'],
                (int) $tokens['cache_miss'],
                (int) $tokens['completion'],
                (int) $tokens['razonamiento'],
                (int) $tokens['total'],
                self::ventana((string) ($ctx['provider'] ?? ''), null),
                !empty($ctx['ok']) ? 1 : 0,
            ]);
        } catch (Throwable $e) {
            error_log('[LlmUsage] no se pudo anotar el consumo: ' . $e->getMessage());
        }
    }

    /**
     * Tarifas efectivas en USD por millón de tokens, ya aplicado el
     * descuento de la ventana.
     *
     * @param array<string,mixed> $cfg Fila de LlmConfig::get()
     * @return array{cache_hit: float, cache_miss: float, output: float}
     */
    public static function tarifas(array $cfg, string $ventana): array
    {
        $factor = $ventana === 'peak' ? 1.0 : self::OFFPEAK_FACTOR;
        return [
            'cache_hit' => (float) ($cfg['price_cache_hit'] ?? 0) * $factor,
            'cache_miss' => (float) ($cfg['price_cache_miss'] ?? 0) * $factor,
            'output' => (float) ($cfg['price_output'] ?? 0) * $factor,
        ];
    }

    /**
     * Costo en USD de una fila (o de un grupo ya sumado, mismo shape).
     *
     * @param array<string,mixed> $fila cache_hit, cache_miss, completion, ventana
     * @param array<string,mixed> $cfg  Fila de LlmConfig::get()
     */
    public static function costo(array $fila, array $cfg): float
    {
        $t = self::tarifas($cfg, (string) ($fila['ventana'] ?? 'peak'));
        return ((int) ($fila['cache_hit'] ?? 0) * $t['cache_hit']
            + (int) ($fila['cache_miss'] ?? 0) * $t['cache_miss']
            + (int) ($fila['completion'] ?? 0) * $t['output']) / 1000000.0;
    }

    /**
     * Corte inferior de un período, como datetime UTC comparable con
     * created_at. $dias = 0 es "desde las 00:00 de hoy" en hora de Chile
     * (ver ZONA_INFORME); $dias = 7 es "desde las 00:00 de hace 6 días",
     * o sea hoy incluido y siete días en total.
     */
    public static function desde(int $dias): string
    {
        $tz = new DateTimeZone(self::ZONA_INFORME);
        $inicio = new DateTime('now', $tz);
        $inicio->setTime(0, 0, 0);
        if ($dias > 1) {
            $inicio->modify('-' . ($dias - 1) . ' days');
        }
        $inicio->setTimezone(new DateTimeZone('UTC'));
        return $inicio->format('Y-m-d H:i:s');
    }

    /**
     * Totales de un período, ya con el costo calculado. Agrupa por ventana
     * antes de sumar plata porque las dos mitades del día valen distinto:
     * sumar todos los tokens y multiplicar una sola vez daría un número que
     * no es el de la factura.
     *
     * $groupBy: expresión SQL de agrupación ('' = un solo total).
     *
     * @return array<string,array<string,mixed>> clave de grupo => totales
     */
    public static function resumen(string $desde, string $groupBy = '', array $cfg = []): array
    {
        if (!self::tablaExiste()) {
            return [];
        }
        $clave = $groupBy !== '' ? $groupBy : "''";
        $sql = "SELECT {$clave} AS grupo, ventana,
                       COUNT(*) AS llamadas,
                       SUM(ok = 0) AS fallidas,
                       SUM(cache_hit) AS cache_hit,
                       SUM(cache_miss) AS cache_miss,
                       SUM(completion) AS completion,
                       SUM(razonamiento) AS razonamiento,
                       SUM(total) AS total
                FROM llm_usage WHERE created_at >= ?
                GROUP BY grupo, ventana";
        $stmt = Db::get()->prepare($sql);
        $stmt->execute([$desde]);

        $out = [];
        foreach ($stmt->fetchAll() as $fila) {
            $g = (string) $fila['grupo'];
            if (!isset($out[$g])) {
                $out[$g] = [
                    'grupo' => $g, 'llamadas' => 0, 'fallidas' => 0, 'cache_hit' => 0,
                    'cache_miss' => 0, 'completion' => 0, 'razonamiento' => 0,
                    'total' => 0, 'costo' => 0.0,
                ];
            }
            foreach (['llamadas', 'fallidas', 'cache_hit', 'cache_miss', 'completion', 'razonamiento', 'total'] as $c) {
                $out[$g][$c] += (int) $fila[$c];
            }
            $out[$g]['costo'] += self::costo($fila, $cfg);
        }
        uasort($out, static function (array $a, array $b): int {
            return $b['costo'] <=> $a['costo'] ?: $b['total'] <=> $a['total'];
        });
        return $out;
    }

    /** Un único total del período (mismo shape que una fila de resumen()). */
    public static function total(string $desde, array $cfg = []): array
    {
        $r = self::resumen($desde, '', $cfg);
        return $r[''] ?? [
            'grupo' => '', 'llamadas' => 0, 'fallidas' => 0, 'cache_hit' => 0,
            'cache_miss' => 0, 'completion' => 0, 'razonamiento' => 0,
            'total' => 0, 'costo' => 0.0,
        ];
    }

    /**
     * Consumo día por día, para ver la curva del mes. El día se corta en
     * hora de Chile: el desfase se aplica en SQL con el offset vigente hoy
     * (ver ZONA_INFORME).
     *
     * @return array<int,array<string,mixed>>
     */
    public static function porDia(string $desde, array $cfg = []): array
    {
        if (!self::tablaExiste()) {
            return [];
        }
        $offset = (new DateTimeZone(self::ZONA_INFORME))->getOffset(new DateTime('now', new DateTimeZone('UTC')));
        $modificador = sprintf('%+d seconds', $offset);

        $stmt = Db::get()->prepare(
            "SELECT date(created_at, ?) AS dia, ventana,
                    COUNT(*) AS llamadas, SUM(cache_hit) AS cache_hit,
                    SUM(cache_miss) AS cache_miss, SUM(completion) AS completion,
                    SUM(total) AS total
             FROM llm_usage WHERE created_at >= ?
             GROUP BY dia, ventana ORDER BY dia DESC"
        );
        $stmt->execute([$modificador, $desde]);

        $out = [];
        foreach ($stmt->fetchAll() as $fila) {
            $dia = (string) $fila['dia'];
            if (!isset($out[$dia])) {
                $out[$dia] = ['dia' => $dia, 'llamadas' => 0, 'total' => 0, 'costo' => 0.0];
            }
            $out[$dia]['llamadas'] += (int) $fila['llamadas'];
            $out[$dia]['total'] += (int) $fila['total'];
            $out[$dia]['costo'] += self::costo($fila, $cfg);
        }
        return array_values($out);
    }

    /**
     * Borra lo que pasó RETENCION_DIAS. Lo llama admin/llm.php al mostrar
     * el panel y no cada INSERT: la limpieza no tiene ninguna urgencia, y
     * el camino del chat del alumno no debería cargar con un DELETE que no
     * le sirve a nadie en ese momento.
     */
    public static function purgar(): int
    {
        if (!self::tablaExiste()) {
            return 0;
        }
        $stmt = Db::get()->prepare("DELETE FROM llm_usage WHERE created_at < datetime('now', ?)");
        $stmt->execute(['-' . self::RETENCION_DIAS . ' days']);
        return $stmt->rowCount();
    }

    /** Fecha de la primera llamada anotada, o null si no hay ninguna. */
    public static function primerRegistro(): ?string
    {
        if (!self::tablaExiste()) {
            return null;
        }
        $fila = Db::get()->query('SELECT MIN(created_at) AS d FROM llm_usage')->fetch();
        $d = $fila ? (string) ($fila['d'] ?? '') : '';
        return $d !== '' ? $d : null;
    }

    /**
     * Saldo que queda en la cuenta del proveedor.
     *
     * Es lo ÚNICO que DeepSeek expone sobre plata: no hay endpoint de
     * consumo ni de histórico, así que esto sirve para saber cuánto queda,
     * no en qué se fue (para eso está el resto de esta clase).
     *
     * @return array{disponible: bool, saldos: array<int,array<string,string>>}
     */
    public static function saldo(array $cfg): array
    {
        if (trim((string) $cfg['api_key']) === '') {
            throw new RuntimeException('Falta configurar el api_key del LLM.');
        }
        $base = rtrim((string) $cfg['api_base_url'], '/');
        if ($base === '') {
            throw new RuntimeException('Falta la base URL de la API.');
        }

        $ch = curl_init($base . '/user/balance');
        curl_setopt_array($ch, [
            CURLOPT_RETURNTRANSFER => true,
            CURLOPT_HTTPHEADER => ['Authorization: Bearer ' . $cfg['api_key']],
            CURLOPT_TIMEOUT => 15,
        ]);
        $body = curl_exec($ch);
        $err = curl_error($ch);
        $status = (int) curl_getinfo($ch, CURLINFO_HTTP_CODE);
        curl_close($ch);

        if ($body === false) {
            throw new RuntimeException('No se pudo consultar el saldo: ' . $err);
        }
        $decoded = json_decode((string) $body, true);
        if ($status === 404) {
            // Un backend compatible con OpenAI no tiene por qué implementar
            // este endpoint: es propio de DeepSeek.
            throw new RuntimeException('Este proveedor no expone consulta de saldo (es un endpoint propio de DeepSeek).');
        }
        if ($status < 200 || $status >= 300) {
            $msg = is_array($decoded) ? ($decoded['error']['message'] ?? null) : null;
            throw new RuntimeException("El proveedor respondió HTTP {$status}: " . ($msg ?? (string) $body));
        }
        if (!is_array($decoded)) {
            throw new RuntimeException('Respuesta de saldo ilegible: ' . (string) $body);
        }

        $saldos = [];
        foreach ((array) ($decoded['balance_infos'] ?? []) as $b) {
            $saldos[] = [
                'moneda' => (string) ($b['currency'] ?? ''),
                'total' => (string) ($b['total_balance'] ?? ''),
                'regalado' => (string) ($b['granted_balance'] ?? ''),
                'recargado' => (string) ($b['topped_up_balance'] ?? ''),
            ];
        }
        return ['disponible' => !empty($decoded['is_available']), 'saldos' => $saldos];
    }

    /**
     * La tabla la crea schema.sql, pero el chat de un alumno puede correr
     * mucho antes de que alguien pase por "Aplicar schema" -- y durante
     * todo ese tiempo no se anotaría nada. Se crea al vuelo la primera vez
     * que hace falta, una sola vez por request: la migración son tres
     * consultas al catálogo, y en el camino del chat se llama por cada
     * mensaje que escribe el alumno.
     */
    private static bool $tablaLista = false;

    private static function asegurarTabla(): void
    {
        if (self::$tablaLista) {
            return;
        }
        Db::migrateLlmUsageIfNeeded();
        self::$tablaLista = true;
    }

    /**
     * La tabla es nueva: en una instalación que todavía no aplicó el schema
     * no existe, y una consulta de lectura no debe reventar el panel por
     * eso (el admin lo arregla con "Aplicar schema", ver admin/database.php).
     */
    private static function tablaExiste(): bool
    {
        $stmt = Db::get()->prepare("SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'llm_usage'");
        $stmt->execute();
        return (bool) $stmt->fetch();
    }
}
