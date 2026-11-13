<?php

declare(strict_types=1);

require_once __DIR__ . '/OtoscopiaPhoto.php';

/**
 * Base de otoscopias: fotos que se cargan una vez y se usan en cualquier
 * caso, para OD o para OI.
 *
 * Cada foto guarda el ORIGINAL (con la orientación EXIF ya aplicada y
 * achicado a MAX_ORIGINAL) más cómo encuadrarla: giro libre en grados,
 * centro y lado del recuadro cuadrado en píxeles del original. De ahí sale
 * la imagen "base" de 640x640, que es la foto tal como debe verse, sin
 * espejar. Además se marca hacia qué lado de la base queda ANTERIOR.
 *
 * Por qué alcanza con saber dónde queda anterior: la membrana timpánica
 * derecha y la izquierda son imagen especular una de la otra. Mirando por
 * el otoscopio, en el OD lo anterior cae a la derecha de la imagen (el
 * triángulo luminoso, anteroinferior, queda hacia las 5) y en el OI a la
 * izquierda (hacia las 7). Una foto con anterior a la derecha sirve tal
 * cual para OD y espejada para OI, y al revés. Espejar no mueve nada de
 * lugar en términos anatómicos: una perforación posterosuperior sigue
 * siendo posterosuperior. 'nd' es para fotos donde no se distingue (tapón
 * que ocupa todo el conducto): esas nunca se espejan.
 *
 * Asignar una foto a un caso COPIA la base (espejada si hace falta) al
 * archivo de siempre del caso (OtoscopiaPhoto, data/otoscopia_photos/), así
 * la app, el PDF y el modo sin cuenta no se enteran de que existe la base.
 * El vínculo queda en otoscopia_biblioteca_uso: si después se corrige el
 * giro o el lado de una foto, se reescriben los casos que la usan. Subir
 * otra foto a mano, borrarla o espejarla en la ficha corta el vínculo (ver
 * OtoscopiaPhoto::delete/save/mirror).
 */
final class OtoscopiaBiblioteca
{
    /** Lado del original más largo, en px: alcanza para recortar con zoom y no revienta la memoria de GD al girar. */
    private const MAX_ORIGINAL = 1600;
    private const SALIDA = 640;

    /** Clave guardada => rótulo. Sin CHECK en la tabla: la lista puede crecer sin migrar. */
    public const TIPOS = [
        'normal' => 'Normal',
        'perforacion' => 'Perforación',
        'cerumen' => 'Tapón de cerumen',
        'oma' => 'Otitis media aguda',
        'ome' => 'Otitis media con efusión',
        'omc' => 'Otitis media crónica',
        'retraccion' => 'Retracción / atelectasia',
        'timpanoesclerosis' => 'Timpanoesclerosis',
        'colesteatoma' => 'Colesteatoma',
        'tubo' => 'Tubo de ventilación',
        'otitis_externa' => 'Otitis externa',
        'cuerpo_extrano' => 'Cuerpo extraño',
        'otra' => 'Otra',
    ];

    public const ANTERIOR = [
        'izq' => 'a la izquierda',
        'der' => 'a la derecha',
        'nd' => 'no se distingue',
    ];

    private static bool $tablaLista = false;

    /** Crea las tablas si faltan (mismo SQL que schema.sql, IF NOT EXISTS en ambos lados). */
    public static function asegurarTablas(): void
    {
        if (self::$tablaLista) {
            return;
        }
        $pdo = Db::get();
        $pdo->exec("CREATE TABLE IF NOT EXISTS otoscopia_biblioteca (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ancho INTEGER NOT NULL,
            alto INTEGER NOT NULL,
            rotacion REAL NOT NULL DEFAULT 0,
            centro_x REAL NOT NULL,
            centro_y REAL NOT NULL,
            lado REAL NOT NULL,
            anterior TEXT CHECK (anterior IS NULL OR anterior IN ('izq', 'der', 'nd')),
            tipo TEXT,
            notas TEXT NOT NULL DEFAULT '',
            nombre_archivo TEXT NOT NULL DEFAULT '',
            created_by INTEGER,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )");
        $pdo->exec("CREATE TABLE IF NOT EXISTS otoscopia_biblioteca_uso (
            case_id TEXT NOT NULL,
            side TEXT NOT NULL,
            fase INTEGER NOT NULL,
            biblioteca_id INTEGER NOT NULL,
            PRIMARY KEY (case_id, side, fase)
        )");
        $pdo->exec('CREATE INDEX IF NOT EXISTS idx_otoscopia_uso_biblioteca ON otoscopia_biblioteca_uso (biblioteca_id)');
        self::$tablaLista = true;
    }

    // ------------------------------------------------------------------
    // Cálculos puros (sin GD ni base: los cubre tests/test_otoscopia_biblioteca.php)
    // ------------------------------------------------------------------

    /** ¿Hay que espejar la base para mostrarla en este oído? OD quiere anterior a la derecha; OI, a la izquierda. */
    public static function debeEspejar(?string $anterior, string $side): bool
    {
        if ($anterior === 'der') {
            return $side === 'oi';
        }
        if ($anterior === 'izq') {
            return $side === 'od';
        }
        return false;
    }

    /**
     * Dónde cae, en la imagen ya girada, un punto (x, y) del original.
     *
     * $grados es el giro HORARIO que ve el usuario (positivo = sentido del
     * reloj, con el eje y hacia abajo como en pantalla). La imagen girada es
     * la caja que la contiene, de $anchoGirada x $altoGirada, con el
     * contenido centrado: así lo deja imagerotate() de GD, y así lo dibuja
     * el editor en el canvas.
     *
     * @return array{0: float, 1: float}
     */
    public static function puntoEnGirada(float $x, float $y, float $ancho, float $alto, float $grados, float $anchoGirada, float $altoGirada): array
    {
        $t = deg2rad($grados);
        $dx = $x - $ancho / 2;
        $dy = $y - $alto / 2;
        return [
            $anchoGirada / 2 + $dx * cos($t) - $dy * sin($t),
            $altoGirada / 2 + $dx * sin($t) + $dy * cos($t),
        ];
    }

    /**
     * Parámetros de encuadre sanos: giro en (-180, 180], lado entre 8 px y
     * el doble de la diagonal (más allá ya es todo negro), centro dentro del
     * original. Lo que venga del navegador pasa por acá antes de guardarse.
     *
     * @return array{rotacion: float, centro_x: float, centro_y: float, lado: float}
     */
    public static function encuadreSano(float $rotacion, float $cx, float $cy, float $lado, int $ancho, int $alto): array
    {
        if (!is_finite($rotacion)) {
            $rotacion = 0.0;
        }
        $rotacion = fmod($rotacion, 360.0);
        if ($rotacion > 180.0) {
            $rotacion -= 360.0;
        } elseif ($rotacion <= -180.0) {
            $rotacion += 360.0;
        }
        $diag = sqrt((float) ($ancho * $ancho + $alto * $alto));
        if (!is_finite($lado) || $lado <= 0) {
            $lado = (float) min($ancho, $alto);
        }
        $lado = max(8.0, min($lado, 2 * $diag));
        $cx = is_finite($cx) ? max(0.0, min($cx, (float) $ancho)) : $ancho / 2;
        $cy = is_finite($cy) ? max(0.0, min($cy, (float) $alto)) : $alto / 2;
        return ['rotacion' => round($rotacion, 2), 'centro_x' => $cx, 'centro_y' => $cy, 'lado' => $lado];
    }

    public static function clasificada(array $fila): bool
    {
        return ($fila['anterior'] ?? null) !== null && (string) ($fila['tipo'] ?? '') !== '';
    }

    // ------------------------------------------------------------------
    // Archivos
    // ------------------------------------------------------------------

    public static function dir(): string
    {
        $dir = __DIR__ . '/../data/otoscopia_biblioteca';
        if (!is_dir($dir) && !mkdir($dir, 0775, true) && !is_dir($dir)) {
            throw new RuntimeException("No se pudo crear {$dir} (revisa permisos).");
        }
        return $dir;
    }

    public static function rutaOriginal(int $id): string
    {
        return self::dir() . '/' . $id . '_original.jpg';
    }

    /** Ruta de la base (webp o jpg, la que exista). Si no hay ninguna, la jpg (is_file() da false). */
    public static function rutaBase(int $id): string
    {
        foreach (['webp', 'jpg'] as $ext) {
            $p = self::dir() . '/' . $id . '.' . $ext;
            if (is_file($p)) {
                return $p;
            }
        }
        return self::dir() . '/' . $id . '.jpg';
    }

    private static function requiereGd(): void
    {
        if (!extension_loaded('gd')) {
            throw new RuntimeException('El servidor no tiene la extensión GD -- no se pueden procesar imágenes.');
        }
    }

    // ------------------------------------------------------------------
    // Altas, cambios, bajas
    // ------------------------------------------------------------------

    /**
     * Agrega una foto sin clasificar: sin girar, recuadro centrado del lado
     * corto. Devuelve el id nuevo.
     */
    public static function agregar(string $tmpPath, string $nombreArchivo, ?int $userId): int
    {
        self::requiereGd();
        self::asegurarTablas();
        $img = OtoscopiaPhoto::abrirImagen($tmpPath);
        $w = imagesx($img);
        $h = imagesy($img);
        $escala = min(1.0, self::MAX_ORIGINAL / max($w, $h));
        if ($escala < 1.0) {
            $nw = max(1, (int) round($w * $escala));
            $nh = max(1, (int) round($h * $escala));
            $chica = imagecreatetruecolor($nw, $nh);
            imagecopyresampled($chica, $img, 0, 0, 0, 0, $nw, $nh, $w, $h);
            imagedestroy($img);
            $img = $chica;
            $w = $nw;
            $h = $nh;
        }

        $pdo = Db::get();
        $pdo->prepare(
            'INSERT INTO otoscopia_biblioteca (ancho, alto, rotacion, centro_x, centro_y, lado, nombre_archivo, created_by)
             VALUES (?, ?, 0, ?, ?, ?, ?, ?)'
        )->execute([$w, $h, $w / 2, $h / 2, (float) min($w, $h), mb_substr($nombreArchivo, 0, 200), $userId]);
        $id = (int) $pdo->lastInsertId();

        try {
            if (!imagejpeg($img, self::rutaOriginal($id), 92)) {
                throw new RuntimeException('No se pudo guardar la imagen.');
            }
            imagedestroy($img);
            self::renderizarBase(self::fila($id));
        } catch (Throwable $e) {
            $pdo->prepare('DELETE FROM otoscopia_biblioteca WHERE id = ?')->execute([$id]);
            @unlink(self::rutaOriginal($id));
            throw $e;
        }
        return $id;
    }

    /** Id de la foto subida con ese nombre de archivo, o null (para no subir dos veces la misma en lote). */
    public static function idPorNombre(string $nombre): ?int
    {
        self::asegurarTablas();
        $stmt = Db::get()->prepare('SELECT id FROM otoscopia_biblioteca WHERE nombre_archivo = ? ORDER BY id LIMIT 1');
        $stmt->execute([mb_substr($nombre, 0, 200)]);
        $id = $stmt->fetchColumn();
        $stmt->closeCursor();
        return $id === false ? null : (int) $id;
    }

    /**
     * Tipo y notas sin tocar el encuadre ni el lado: para la carga en lote
     * (consola), donde el tipo ya se sabe pero el giro y el lado anterior
     * los revisa una persona en otoscopias.php. Sin lado sigue "sin clasificar".
     */
    public static function catalogar(int $id, ?string $tipo, string $notas): void
    {
        if ($tipo !== null && !isset(self::TIPOS[$tipo])) {
            throw new InvalidArgumentException('Tipo inválido: ' . $tipo);
        }
        self::asegurarTablas();
        Db::get()->prepare('UPDATE otoscopia_biblioteca SET tipo = ?, notas = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?')
            ->execute([$tipo, mb_substr(trim($notas), 0, 500), $id]);
    }

    public static function fila(int $id): array
    {
        self::asegurarTablas();
        $stmt = Db::get()->prepare('SELECT * FROM otoscopia_biblioteca WHERE id = ?');
        $stmt->execute([$id]);
        $fila = $stmt->fetch(PDO::FETCH_ASSOC);
        $stmt->closeCursor();
        if (!$fila) {
            throw new RuntimeException('Esa foto no está en la base.');
        }
        return $fila;
    }

    /**
     * Guarda encuadre y clasificación, rehace la base y reescribe la foto
     * de cada caso que la usa. Devuelve cuántas fotos de casos reescribió.
     *
     * @param array{rotacion: float, centro_x: float, centro_y: float, lado: float, anterior: ?string, tipo: ?string, notas: string} $datos
     */
    public static function guardar(int $id, array $datos): int
    {
        self::requiereGd();
        $fila = self::fila($id);
        $enc = self::encuadreSano(
            (float) $datos['rotacion'],
            (float) $datos['centro_x'],
            (float) $datos['centro_y'],
            (float) $datos['lado'],
            (int) $fila['ancho'],
            (int) $fila['alto']
        );
        $anterior = $datos['anterior'] ?? null;
        if ($anterior !== null && !isset(self::ANTERIOR[$anterior])) {
            throw new InvalidArgumentException('Lado anterior inválido.');
        }
        $tipo = $datos['tipo'] ?? null;
        if ($tipo !== null && !isset(self::TIPOS[$tipo])) {
            throw new InvalidArgumentException('Tipo inválido.');
        }
        Db::get()->prepare(
            'UPDATE otoscopia_biblioteca
                SET rotacion = ?, centro_x = ?, centro_y = ?, lado = ?, anterior = ?, tipo = ?, notas = ?,
                    updated_at = CURRENT_TIMESTAMP
              WHERE id = ?'
        )->execute([
            $enc['rotacion'], $enc['centro_x'], $enc['centro_y'], $enc['lado'],
            $anterior, $tipo, mb_substr(trim((string) ($datos['notas'] ?? '')), 0, 500), $id,
        ]);
        $fila = self::fila($id);
        self::renderizarBase($fila);
        return self::reescribirUsos($fila);
    }

    /**
     * Saca la foto de la base. Los casos que la usaban conservan su copia
     * (es un archivo propio del caso); solo se pierde el vínculo.
     */
    public static function borrar(int $id): void
    {
        self::asegurarTablas();
        $pdo = Db::get();
        $pdo->prepare('DELETE FROM otoscopia_biblioteca_uso WHERE biblioteca_id = ?')->execute([$id]);
        $pdo->prepare('DELETE FROM otoscopia_biblioteca WHERE id = ?')->execute([$id]);
        foreach ([self::rutaOriginal($id), self::dir() . '/' . $id . '.webp', self::dir() . '/' . $id . '.jpg'] as $p) {
            if (is_file($p)) {
                unlink($p);
            }
        }
    }

    /**
     * @param string $filtro '' = todas, 'pendientes' = sin clasificar, o una clave de TIPOS
     * @return list<array> filas con 'usos' (cuántas fotos de casos la usan)
     */
    public static function lista(string $filtro = ''): array
    {
        self::asegurarTablas();
        $sql = 'SELECT b.*, (SELECT COUNT(*) FROM otoscopia_biblioteca_uso u WHERE u.biblioteca_id = b.id) AS usos
                  FROM otoscopia_biblioteca b';
        $params = [];
        if ($filtro === 'pendientes') {
            $sql .= " WHERE b.anterior IS NULL OR b.tipo IS NULL OR b.tipo = ''";
        } elseif ($filtro !== '') {
            $sql .= ' WHERE b.tipo = ?';
            $params[] = $filtro;
        }
        $sql .= ' ORDER BY b.id';
        $stmt = Db::get()->prepare($sql);
        $stmt->execute($params);
        return $stmt->fetchAll(PDO::FETCH_ASSOC);
    }

    /** @return array{total: int, pendientes: int, por_tipo: array<string, int>} */
    public static function conteos(): array
    {
        $total = 0;
        $pendientes = 0;
        $porTipo = [];
        foreach (self::lista() as $f) {
            $total++;
            if (!self::clasificada($f)) {
                $pendientes++;
            }
            $t = (string) ($f['tipo'] ?? '');
            if ($t !== '') {
                $porTipo[$t] = ($porTipo[$t] ?? 0) + 1;
            }
        }
        return ['total' => $total, 'pendientes' => $pendientes, 'por_tipo' => $porTipo];
    }

    /** Siguiente sin clasificar después de $id (o la primera), o null. */
    public static function siguientePendiente(int $despuesDe): ?int
    {
        $pend = array_map(static function (array $f): int { return (int) $f['id']; }, self::lista('pendientes'));
        foreach ($pend as $p) {
            if ($p > $despuesDe) {
                return $p;
            }
        }
        foreach ($pend as $p) {
            if ($p !== $despuesDe) {
                return $p;
            }
        }
        return null;
    }

    // ------------------------------------------------------------------
    // Uso en casos
    // ------------------------------------------------------------------

    /**
     * Pone la foto $id en el oído/fase del caso (espejada si el oído lo
     * pide) y deja anotado el vínculo. No deja usar la misma foto en los dos
     * oídos del mismo caso: el alumno vería la misma imagen dada vuelta.
     */
    public static function asignar(string $caseId, string $side, int $fase, int $id): void
    {
        self::requiereGd();
        $fila = self::fila($id);
        if (!self::clasificada($fila)) {
            throw new RuntimeException('Esa foto todavía no está clasificada en la base.');
        }
        $otro = $side === 'od' ? 'oi' : 'od';
        $stmt = Db::get()->prepare(
            'SELECT COUNT(*) FROM otoscopia_biblioteca_uso WHERE case_id = ? AND side = ? AND biblioteca_id = ?'
        );
        $stmt->execute([$caseId, $otro, $id]);
        $enElOtro = (int) $stmt->fetchColumn() > 0;
        $stmt->closeCursor();
        if ($enElOtro) {
            throw new RuntimeException('Esa foto ya está en el otro oído de este caso: el alumno vería la misma imagen dada vuelta. Elige otra.');
        }
        self::escribirEnCaso($fila, $caseId, $side, $fase);
        Db::get()->prepare(
            'INSERT OR REPLACE INTO otoscopia_biblioteca_uso (case_id, side, fase, biblioteca_id) VALUES (?, ?, ?, ?)'
        )->execute([$caseId, $side, $fase, $id]);
    }

    /** Fila de la base usada en ese oído/fase del caso, o null. Nunca lanza (la ficha se dibuja igual). */
    public static function usoDe(string $caseId, string $side, int $fase): ?array
    {
        try {
            self::asegurarTablas();
            $stmt = Db::get()->prepare(
                'SELECT b.* FROM otoscopia_biblioteca_uso u JOIN otoscopia_biblioteca b ON b.id = u.biblioteca_id
                  WHERE u.case_id = ? AND u.side = ? AND u.fase = ?'
            );
            $stmt->execute([$caseId, $side, $fase]);
            $fila = $stmt->fetch(PDO::FETCH_ASSOC);
            $stmt->closeCursor();
            return $fila ?: null;
        } catch (Throwable $e) {
            return null;
        }
    }

    /** Corta el vínculo de ese oído/fase (la foto del caso pasó a ser propia). Nunca lanza. */
    public static function desvincular(string $caseId, string $side, int $fase): void
    {
        try {
            self::asegurarTablas();
            Db::get()->prepare('DELETE FROM otoscopia_biblioteca_uso WHERE case_id = ? AND side = ? AND fase = ?')
                ->execute([$caseId, $side, $fase]);
        } catch (Throwable $e) {
            // Sin tabla o base ocupada: lo peor es que una corrección futura
            // de la foto en la base reescriba este oído.
        }
    }

    /** Pasa los vínculos de un id temporal al case_id real (ver OtoscopiaPhoto::claim). Nunca lanza. */
    public static function reclamar(string $tempId, string $realCaseId): void
    {
        try {
            self::asegurarTablas();
            Db::get()->prepare('UPDATE OR REPLACE otoscopia_biblioteca_uso SET case_id = ? WHERE case_id = ?')
                ->execute([$realCaseId, $tempId]);
        } catch (Throwable $e) {
        }
    }

    /** Reescribe la foto de cada caso que usa esta fila; limpia vínculos de casos que ya no existen. */
    private static function reescribirUsos(array $fila): int
    {
        $pdo = Db::get();
        $stmt = $pdo->prepare('SELECT case_id, side, fase FROM otoscopia_biblioteca_uso WHERE biblioteca_id = ?');
        $stmt->execute([(int) $fila['id']]);
        $usos = $stmt->fetchAll(PDO::FETCH_ASSOC);
        $existe = $pdo->prepare('SELECT COUNT(*) FROM cases WHERE id = ?');
        $n = 0;
        foreach ($usos as $u) {
            $caseId = (string) $u['case_id'];
            $existe->execute([$caseId]);
            $hay = (int) $existe->fetchColumn() > 0;
            $existe->closeCursor();
            if (!$hay && substr($caseId, 0, 3) !== 'tmp') {
                $pdo->prepare('DELETE FROM otoscopia_biblioteca_uso WHERE case_id = ? AND side = ? AND fase = ?')
                    ->execute([$caseId, $u['side'], (int) $u['fase']]);
                continue;
            }
            self::escribirEnCaso($fila, $caseId, (string) $u['side'], (int) $u['fase']);
            $n++;
        }
        return $n;
    }

    private static function escribirEnCaso(array $fila, string $caseId, string $side, int $fase): void
    {
        $ruta = self::rutaBase((int) $fila['id']);
        if (!is_file($ruta)) {
            self::renderizarBase($fila);
            $ruta = self::rutaBase((int) $fila['id']);
        }
        $img = OtoscopiaPhoto::abrirImagen($ruta);
        if (self::debeEspejar($fila['anterior'] ?? null, $side)) {
            imageflip($img, IMG_FLIP_HORIZONTAL);
        }
        OtoscopiaPhoto::escribirImagen($caseId, $side, $fase, $img);
        imagedestroy($img);
    }

    // ------------------------------------------------------------------
    // Render
    // ------------------------------------------------------------------

    /**
     * Base de 640x640: el original girado y recortado según la fila, sin
     * espejar. Lo que cae fuera de la foto queda negro, como el fondo de
     * una otoscopia. El mismo modelo dibuja el editor en el canvas
     * (public/js/otoscopias.js): punto del canvas = centro + (640/lado) ·
     * giro(punto del original - centro del recuadro).
     */
    public static function renderizarBase(array $fila): void
    {
        self::requiereGd();
        $id = (int) $fila['id'];
        $src = OtoscopiaPhoto::abrirImagen(self::rutaOriginal($id));
        $w = imagesx($src);
        $h = imagesy($src);
        $grados = (float) $fila['rotacion'];
        $negro = imagecolorallocate($src, 0, 0, 0);
        if (abs($grados) > 0.001) {
            imagesetinterpolation($src, IMG_BICUBIC);
            // imagerotate gira en sentido antihorario: el giro horario del editor va con signo menos.
            $girada = imagerotate($src, -$grados, $negro);
            imagedestroy($src);
            if ($girada === false) {
                throw new RuntimeException('No se pudo girar la imagen.');
            }
            $src = $girada;
        }
        $wr = imagesx($src);
        $hr = imagesy($src);
        [$px, $py] = self::puntoEnGirada((float) $fila['centro_x'], (float) $fila['centro_y'], $w, $h, $grados, $wr, $hr);
        $lado = (float) $fila['lado'];
        $x0 = $px - $lado / 2;
        $y0 = $py - $lado / 2;

        $sal = self::SALIDA;
        $dst = imagecreatetruecolor($sal, $sal);
        imagefill($dst, 0, 0, imagecolorallocate($dst, 0, 0, 0));
        // Parte del recuadro que cae dentro de la imagen girada.
        $ix0 = max(0.0, $x0);
        $iy0 = max(0.0, $y0);
        $ix1 = min((float) $wr, $x0 + $lado);
        $iy1 = min((float) $hr, $y0 + $lado);
        if ($ix1 > $ix0 && $iy1 > $iy0) {
            $k = $sal / $lado;
            imagecopyresampled(
                $dst,
                $src,
                (int) round(($ix0 - $x0) * $k),
                (int) round(($iy0 - $y0) * $k),
                (int) round($ix0),
                (int) round($iy0),
                max(1, (int) round(($ix1 - $ix0) * $k)),
                max(1, (int) round(($iy1 - $iy0) * $k)),
                max(1, (int) round($ix1 - $ix0)),
                max(1, (int) round($iy1 - $iy0))
            );
        }
        imagedestroy($src);

        foreach (['webp', 'jpg'] as $ext) {
            $p = self::dir() . '/' . $id . '.' . $ext;
            if (is_file($p)) {
                unlink($p);
            }
        }
        if (function_exists('imagewebp')) {
            $ok = imagewebp($dst, self::dir() . '/' . $id . '.webp', 85);
        } else {
            $ok = imagejpeg($dst, self::dir() . '/' . $id . '.jpg', 88);
        }
        imagedestroy($dst);
        if (!$ok) {
            throw new RuntimeException('No se pudo guardar la imagen encuadrada.');
        }
    }
}
