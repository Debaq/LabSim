<?php

final class CaseBuilder
{
    // Mismas 9 frecuencias que usa el audiómetro (Fowler en create_a.py
    // enumera esta misma lista) -- Aerea/Osea/LDL/Reflex se indexan por
    // posición en este array, no por el valor Hz.
    public const FREQUENCIES = [125, 250, 500, 1000, 2000, 3000, 4000, 6000, 8000];

    public const HIST_CHECKBOXES = [
        'hipoacusia_familiar', 'ototoxicos', 'trauma_acustico', 'otitis',
        'meningitis', 'tce', 'diabetes', 'hta',
    ];

    // Mismas etiquetas que case_create.php pinta junto a cada checkbox --
    // repetidas acá (en vez de que ese archivo las importe) porque acá las
    // usa LlmConfig::buildSystemPrompt() para armar el resumen en texto de
    // los antecedentes marcados, sin acoplarse al archivo del formulario.
    public const HIST_LABELS = [
        'hipoacusia_familiar' => 'Hipoacusia familiar', 'ototoxicos' => 'Ototóxicos',
        'trauma_acustico' => 'Trauma acústico', 'otitis' => 'Otitis', 'meningitis' => 'Meningitis',
        'tce' => 'TCE', 'diabetes' => 'Diabetes', 'hta' => 'HTA',
    ];

    public const Z_OPTIONS = ['A', 'As', 'Ad', 'C', 'Cs', 'B'];
    public const ETF_OPTIONS = ['Normal', 'Disfunción tubaria', 'Permeable', 'No permeable'];

    // Requisitos clínicos de aplicabilidad de Fowler/I.W.A. (ABLB): oído de
    // referencia dentro de rango normal, oído en estudio sensorioneural
    // (gap aéreo-óseo bajo) y fuera de rango normal, diferencia interaural
    // acotada, y frecuencia evaluada dentro del rango donde el criterio de
    // "al menos una frecuencia conservada" tiene sentido clínico.
    public const FOWLER_NORMAL_HL = 20;      // dB HL: umbral <= esto = "rango normal"
    public const FOWLER_SNHL_GAP_MAX = 10;   // dB: gap aéreo-óseo máximo para considerar sensorioneural puro
    public const FOWLER_DIFF_MIN = 20;       // dB: diferencia interaural mínima exigida
    public const FOWLER_DIFF_MAX = 40;       // dB: diferencia interaural máxima exigida
    public const FOWLER_FREQ_MIN_HZ = 250;
    public const FOWLER_FREQ_MAX_HZ = 4000;

    // Tipo de ruido percibido (acufenometría) -- "la forma" del acufeno,
    // junto a la frecuencia de matching (se reusa CaseBuilder::FREQUENCIES).
    public const TINNITUS_RUIDO_OPTIONS = ['Silbido', 'Zumbido', 'Siseo', 'Pitido', 'Campanilleo'];

    // Lateralidad del tinnitus -- independiente de permanente/ocasional (un
    // acufeno unilateral puede ser permanente igual que uno bilateral).
    // "unilateral" pide oído; "bilateral" admite predominio (asimetría).
    public const TINNITUS_LATERALIDAD_OPTIONS = ['craneal', 'unilateral', 'bilateral'];
    public const TINNITUS_PREDOMINIO_OPTIONS = ['igual', 'od', 'oi'];

    /** Índices de CaseBuilder::FREQUENCIES dentro del rango válido para Fowler/I.W.A. (250-4000 Hz). */
    public static function fowlerFreqOptions(): array
    {
        $out = [];
        foreach (self::FREQUENCIES as $i => $hz) {
            if ($hz >= self::FOWLER_FREQ_MIN_HZ && $hz <= self::FOWLER_FREQ_MAX_HZ) {
                $out[] = $i;
            }
        }
        return $out;
    }

    /**
     * Valida los requisitos clínicos de aplicabilidad del Fowler/I.W.A. (ABLB):
     *  1) hipoacusia sensorioneural en el oído en estudio (gap aéreo-óseo bajo),
     *     con el oído de referencia dentro de rango normal en esa frecuencia
     *     (cubre unilateral-normal-contralateral y bilateral-asimétrico, ya que
     *     la frecuencia evaluada queda automáticamente como "la conservada");
     *  2) diferencia interaural de 20 a 40 dB en la frecuencia evaluada;
     *  3) oído de referencia normal / oído en estudio fuera de rango normal.
     * $airPairs / $bonePairs: arrays [[od,oi], ...] indexados como FREQUENCIES
     * (mismo shape que Aerea/Osea en cases.data). Devuelve null si es válido,
     * o el mensaje de error si no.
     */
    public static function fowlerValidationError(int $freq, array $airPairs, array $bonePairs): ?string
    {
        $hz = self::FREQUENCIES[$freq] ?? null;
        if ($hz === null || $hz < self::FOWLER_FREQ_MIN_HZ || $hz > self::FOWLER_FREQ_MAX_HZ) {
            return 'La frecuencia de Fowler debe estar entre ' . self::FOWLER_FREQ_MIN_HZ . ' y ' . self::FOWLER_FREQ_MAX_HZ . ' Hz.';
        }

        $air = $airPairs[$freq] ?? [130, 130];
        $refSide = $air[0] <= $air[1] ? 0 : 1;
        $studySide = 1 - $refSide;
        $refTh = (int) $air[$refSide];
        $studyTh = (int) $air[$studySide];
        $diff = $studyTh - $refTh;

        if ($refTh > self::FOWLER_NORMAL_HL) {
            return "El oído de referencia (mejor umbral) debe estar dentro del rango normal (≤ " . self::FOWLER_NORMAL_HL . ' dB HL) en la frecuencia de Fowler.';
        }
        if ($studyTh <= self::FOWLER_NORMAL_HL) {
            return 'El oído en estudio debe tener un umbral fuera del rango normal (> ' . self::FOWLER_NORMAL_HL . ' dB HL) en la frecuencia de Fowler.';
        }
        if ($diff < self::FOWLER_DIFF_MIN || $diff > self::FOWLER_DIFF_MAX) {
            return 'La diferencia entre oídos en la frecuencia de Fowler debe estar entre ' . self::FOWLER_DIFF_MIN . ' y ' . self::FOWLER_DIFF_MAX . " dB (actual: {$diff} dB).";
        }

        $bone = $bonePairs[$freq] ?? [130, 130];
        $gap = $studyTh - (int) $bone[$studySide];
        if ($gap > self::FOWLER_SNHL_GAP_MAX) {
            return "El oído en estudio debe ser sensorioneural (gap aéreo-óseo ≤ " . self::FOWLER_SNHL_GAP_MAX . " dB); gap actual: {$gap} dB.";
        }

        return null;
    }

    /**
     * Todas las frecuencias (250-4000 Hz) donde los umbrales ya cargados
     * (Aerea/Osea) cumplen los requisitos de Fowler/I.W.A. (ver
     * fowlerValidationError) -- el caso puede calificar en más de una a la
     * vez, y el alumno debe poder encontrar cualquiera de ellas, así que el
     * form pide un patrón de reclutamiento por cada una, no solo una.
     */
    public static function fowlerQualifyingFreqs(array $airPairs, array $bonePairs): array
    {
        $out = [];
        foreach (self::fowlerFreqOptions() as $freq) {
            if (self::fowlerValidationError($freq, $airPairs, $bonePairs) === null) {
                $out[] = $freq;
            }
        }
        return $out;
    }

    // Patrón de reclutamiento -> cortes que le pasan al motor (Fowler.py):
    // ver docstring de Fowler.evaluate() para el porqué de estos valores --
    // en corto, "cuts" son quiebres en dB sobre el umbral del oído en
    // estudio que delimitan las zonas del algoritmo; un corte >= la salida
    // máxima práctica del audiómetro (200) equivale a "nunca se alcanza esa
    // zona". Debe coincidir exactamente con FOWLER_PATTERNS en Fowler.py.
    public const FOWLER_PATTERNS = [
        'none' => [200, 200, 200],       // sin reclutamiento: crecimiento paralelo, nunca iguala
        'partial' => [15, 200, 200],     // reclutamiento parcial: se acerca pero no cierra del todo
        'complete' => [15, 30, 200],     // reclutamiento completo: iguala sonoridad, no sobrepasa
        'over' => [15, 30, 50],          // sobre-reclutamiento: en niveles altos el oído afectado suena más fuerte
    ];

    public const FOWLER_PATTERN_LABELS = [
        'none' => 'Sin reclutamiento',
        'partial' => 'Reclutamiento parcial',
        'complete' => 'Reclutamiento completo',
        'over' => 'Sobre-reclutamiento',
    ];

    public static function fowlerCutsForPattern(string $pattern): array
    {
        return self::FOWLER_PATTERNS[$pattern] ?? self::FOWLER_PATTERNS['none'];
    }

    // Tipo de curva del reflejo acústico, por oído -- morfología del trazo
    // (no la intensidad umbral, que ya se captura en reflex_ipsi/contra).
    public const REFLEX_CURVE_TYPES = ['normal', 'invertido', 'on', 'on-off'];

    public const REFLEX_CURVE_LABELS = [
        'normal' => 'Normal',
        'invertido' => 'Invertido',
        'on' => 'ON',
        'on-off' => 'ON-OFF',
    ];

    /** Lista en texto de los antecedentes marcados (para el prompt del LLM) -- "ninguno relevante" si no hay ninguno. */
    public static function antecedentesSummary(array $antecedentes): string
    {
        $labels = [];
        foreach (self::HIST_CHECKBOXES as $key) {
            if (!empty($antecedentes[$key])) {
                $labels[] = self::HIST_LABELS[$key];
            }
        }
        return $labels ? implode(', ', $labels) : 'ninguno relevante';
    }

    /**
     * Describe en lenguaje natural (nada de Hz/dB) lo que el "paciente"
     * percibe según los datos de Tinnitus del caso -- para completar
     * {{tinnitus_desc}} en LlmConfig::DEFAULT_PROMPT. $t viene con el mismo
     * shape que cases.data.Tinnitus (o el array crudo del form de la ficha).
     */
    public static function describeTinnitus(array $t): string
    {
        $lateralidad = (string) ($t['lateralidad'] ?? 'craneal');
        $ruido = mb_strtolower((string) ($t['ruido'] ?? self::TINNITUS_RUIDO_OPTIONS[0]));
        $permanente = !empty($t['permanente']);
        $pulsatil = !empty($t['pulsatil']);

        $lugar = 'en la cabeza, sin poder decir bien de qué lado';
        if ($lateralidad === 'unilateral') {
            $lugar = 'solo en el oído ' . (($t['oido'] ?? 'od') === 'oi' ? 'izquierdo' : 'derecho');
        } elseif ($lateralidad === 'bilateral') {
            $predominio = (string) ($t['predominio'] ?? 'igual');
            $lugar = $predominio === 'igual'
                ? 'en ambos oídos por igual'
                : ('en ambos oídos, más fuerte del lado ' . ($predominio === 'od' ? 'derecho' : 'izquierdo'));
        }

        $tiempo = $permanente ? 'lo escuchas casi todo el tiempo' : 'te pasa solo de a ratos, no siempre';
        $pulso = $pulsatil ? ' y a veces sientes que va al compás de tu pulso' : '';

        return "Escuchas un {$ruido} {$lugar}; {$tiempo}{$pulso}.";
    }

    public static function nextCaseId(PDO $pdo): string
    {
        $max = (int) $pdo->query('SELECT MAX(CAST(id AS INTEGER)) FROM cases')->fetchColumn();
        return (string) ($max + 1);
    }

    /**
     * Volumen del canal auditivo (Vea) en cm3 -- mismo rango clínico
     * (Katz, Handbook of Clinical Audiology) que CreatePatient.ear_volume
     * en src/lib/helpers.py. gender: 0 = hombre, 1 = mujer.
     */
    public static function earVolume(int $age, int $gender): float
    {
        if ($age <= 5) {
            [$low, $high] = [0.30, 0.90];
        } elseif ($age <= 12) {
            [$low, $high] = [0.40, 1.00];
        } elseif ($age <= 17) {
            [$low, $high] = [0.60, 1.30];
        } else {
            [$low, $high] = $gender === 0 ? [0.9, 2.0] : [0.8, 1.8];
        }
        $value = $low + (mt_rand() / mt_getrandmax()) * ($high - $low);
        return round($value, 2);
    }

    /**
     * RUT falso a partir de la edad -- misma regresión lineal fija que
     * CreatePatient.rut_from_age en src/lib/helpers.py (no inventar otra:
     * tiene que dar edades consistentes con get_age_from_rut del lado
     * cliente). Se agrega un día aleatorio del año para no chocar RUTs
     * entre pacientes con la misma edad.
     */
    public static function rutFromAge(int $age): int
    {
        $slope = 3.3363697569700348e-06;
        $intercept = 1932.2573852507373;
        $birthYear = (int) date('Y') - $age;
        $randomDay = random_int(0, 364);
        $birthDateFloat = $birthYear + ($randomDay / 365);
        return (int) (($birthDateFloat - $intercept) / $slope);
    }

    /** Mejor 2 de [500,1000,2000 Hz] (índices 2,3,4), promedio, floor a múltiplo de 5. Igual que create_a.py::_fletcher_avg. */
    public static function fletcherAvg(array $airPairs): array
    {
        $sublist = array_slice($airPairs, 2, 3);
        $result = [];
        foreach ([0, 1] as $side) {
            $values = array_map(static fn(array $pair) => $pair[$side], $sublist);
            sort($values);
            $best2 = array_slice($values, 0, 2);
            $avg = array_sum($best2) / count($best2);
            $result[] = (int) (floor($avg / 5) * 5);
        }
        return $result;
    }

    /** Nombre + apellido al azar del banco compartido con la app de escritorio (resources/json/names.json). */
    public static function randomName(string $gender): array
    {
        $path = __DIR__ . '/../resources/names.json';
        $bank = json_decode((string) file_get_contents($path), true) ?? [];
        $nombres = $gender === 'men' ? ($bank['nombres_hombres'] ?? []) : ($bank['nombres_mujeres'] ?? []);
        $apellidos = $bank['apellidos'] ?? [];

        if (!$nombres || !$apellidos) {
            return ['Paciente', 'De Prueba', 'Apellido', 'Uno'];
        }

        $nombre1 = $nombres[array_rand($nombres)];
        $nombre2Pool = array_values(array_diff($nombres, [$nombre1]));
        $nombre2 = $nombre2Pool ? $nombre2Pool[array_rand($nombre2Pool)] : $nombre1;

        $apellido1 = $apellidos[array_rand($apellidos)];
        $apellido2Pool = array_values(array_diff($apellidos, [$apellido1]));
        $apellido2 = $apellido2Pool ? $apellido2Pool[array_rand($apellido2Pool)] : $apellido1;

        return [$nombre1, $nombre2, $apellido1, $apellido2];
    }

    /**
     * Arma el JSON de cases.data con el mismo shape que create_a.py::_save_case
     * -- el cliente (Audiometer.py/Z.py/ListWords.py) espera exactamente
     * estas claves. $form ya viene validado desde case_create.php.
     */
    public static function buildCaseData(array $form): array
    {
        $gender = (int) $form['gender'];
        $age = (int) $form['age'];

        return [
            'gender' => $gender,
            'id' => (int) $form['id'],
            'Aerea' => $form['aerea'],
            'Osea' => $form['osea'],
            'LDL' => $form['ldl'],
            'Aerea_mkg' => $form['aerea'],
            'Osea_mkg' => $form['osea'],
            'Z_OD' => $form['z_od'],
            'Z_OI' => $form['z_oi'],
            'sector' => 'Camara_sono',
            'volume' => [self::earVolume($age, $gender), self::earVolume($age, $gender), 'N/D'],
            'UMD' => $form['umd'],
            'SDT' => $form['sdt'],
            'SRT' => $form['srt'],
            'Fowler' => $form['fowler'],
            'Stenger' => $form['stenger'],
            'SISI' => $form['sisi'],
            'box' => 'Box_1',
            'result' => 1,
            'state_login' => 1,
            'recruit' => $form['recruit'],
            'decay' => $form['decay'],
            'Reflex' => $form['reflex'],
            'ETF' => [$form['etf_od'], $form['etf_oi']],
            'Anamnesis' => $form['anamnesis'],
            'PatientBehavior' => $form['comportamiento'] ?? '',
            'Tinnitus' => $form['tinnitus'],
            'tipo' => 'normal',
        ];
    }

    /**
     * Inverso de buildCaseData(): reconstruye el shape de $_POST que espera
     * case_create.php a partir de un `cases.data` ya guardado, para
     * precargar el formulario al editar un caso existente. `age` no se
     * reconstruye acá (no se guarda en cases.data) -- case_create.php la
     * resuelve aparte a partir de la cita asociada.
     */
    public static function caseDataToForm(array $data): array
    {
        $unzip = static function (array $pairs, int $count): array {
            $od = [];
            $oi = [];
            for ($n = 0; $n < $count; $n++) {
                $od[$n] = (string) ($pairs[$n][0] ?? 0);
                $oi[$n] = (string) ($pairs[$n][1] ?? 0);
            }
            return [$od, $oi];
        };

        $v = [];
        $v['gender'] = (string) ($data['gender'] ?? 0);

        $freqCount = count(self::FREQUENCIES);
        [$aereaOd, $aereaOi] = $unzip($data['Aerea'] ?? [], $freqCount);
        [$oseaOd, $oseaOi] = $unzip($data['Osea'] ?? [], $freqCount);
        [$ldlOd, $ldlOi] = $unzip($data['LDL'] ?? [], $freqCount);
        $v['aerea'] = ['od' => $aereaOd, 'oi' => $aereaOi];
        $v['osea'] = ['od' => $oseaOd, 'oi' => $oseaOi];
        $v['ldl'] = ['od' => $ldlOd, 'oi' => $ldlOi];

        // "LDL no medido" se guarda como 130 en las 9 frecuencias (ver
        // case_create.php) -- si alguna difiere, asumimos que sí se midió.
        $v['ldl_habilitado'] = [];
        foreach (['od' => $ldlOd, 'oi' => $ldlOi] as $side => $vals) {
            foreach ($vals as $val) {
                if ((int) $val !== 130) {
                    $v['ldl_habilitado'][$side] = '1';
                    break;
                }
            }
        }

        $v['z_od'] = $data['Z_OD'] ?? 'A';
        $v['z_oi'] = $data['Z_OI'] ?? 'A';

        $umd = $data['UMD'] ?? [];
        $v['umd_int'] = ['od' => (string) ($umd[0]['int'] ?? 35), 'oi' => (string) ($umd[1]['int'] ?? 35)];
        $v['umd_pct'] = ['od' => (string) ($umd[0]['percentage'] ?? 100), 'oi' => (string) ($umd[1]['percentage'] ?? 100)];

        $sdt = $data['SDT'] ?? [0, 0];
        $srt = $data['SRT'] ?? [0, 0];
        $v['sdt'] = ['od' => (string) ($sdt[0] ?? 0), 'oi' => (string) ($sdt[1] ?? 0)];
        $v['srt'] = ['od' => (string) ($srt[0] ?? 0), 'oi' => (string) ($srt[1] ?? 0)];
        // Se muestra el valor guardado tal cual -- si quedaran tildados los
        // checkboxes "auto" el JS los pisaría con el recálculo de Fletcher
        // apenas cargara la página.
        $v['sdt_auto'] = [];
        $v['srt_auto'] = [];

        $fowler = $data['Fowler'] ?? [];
        // freq/cuts/auto: shape viejo (una sola frecuencia elegida al crear
        // el caso), ya no se usa -- se ignora silenciosamente si aparece en
        // un caso guardado con la versión anterior; el patrón por frecuencia
        // (abajo) es la única fuente de verdad ahora.
        $v['fowler_pattern'] = [];
        foreach ((array) ($fowler['patterns'] ?? []) as $freq => $pattern) {
            $v['fowler_pattern'][(string) $freq] = (string) $pattern;
        }
        if (!empty($fowler['diplacusia'])) { $v['diplacusia'] = '1'; }

        $stenger = $data['Stenger'] ?? [false, false];
        $v['stenger'] = [];
        if (!empty($stenger[0])) { $v['stenger']['od'] = '1'; }
        if (!empty($stenger[1])) { $v['stenger']['oi'] = '1'; }

        $sisi = $data['SISI'] ?? [0, 0];
        $v['sisi'] = ['od' => (string) ($sisi[0] ?? 0), 'oi' => (string) ($sisi[1] ?? 0)];

        $recruit = $data['recruit'] ?? [false, false];
        $v['recruit'] = [];
        if (!empty($recruit[0])) { $v['recruit']['od'] = '1'; }
        if (!empty($recruit[1])) { $v['recruit']['oi'] = '1'; }

        $decay = $data['decay'] ?? [false, false];
        $v['decay'] = [];
        if (!empty($decay[0])) { $v['decay']['od'] = '1'; }
        if (!empty($decay[1])) { $v['decay']['oi'] = '1'; }

        $reflex = $data['Reflex'] ?? [];
        [$ipsiOd, $ipsiOi] = $unzip($reflex['ipsi'] ?? [], 4);
        [$contraOd, $contraOi] = $unzip($reflex['contra'] ?? [], 5);
        $v['reflex_ipsi'] = ['od' => $ipsiOd, 'oi' => $ipsiOi];
        $v['reflex_contra'] = ['od' => $contraOd, 'oi' => $contraOi];
        $reflexTipo = $reflex['tipo'] ?? [];
        $v['reflex_type'] = [
            'od' => (string) ($reflexTipo['od'] ?? 'normal'),
            'oi' => (string) ($reflexTipo['oi'] ?? 'normal'),
        ];

        $etf = $data['ETF'] ?? ['Normal', 'Normal'];
        $v['etf_od'] = $etf[0] ?? 'Normal';
        $v['etf_oi'] = $etf[1] ?? 'Normal';

        $anamnesis = $data['Anamnesis'] ?? [];
        $antecedentes = $anamnesis['antecedentes'] ?? [];
        $v['hist'] = [];
        foreach (self::HIST_CHECKBOXES as $h) {
            if (!empty($antecedentes[$h])) {
                $v['hist'][$h] = '1';
            }
        }
        $v['medicamentos'] = $anamnesis['medicamentos'] ?? '';
        $v['cirugias'] = $anamnesis['cirugias'] ?? '';
        $v['otros'] = $anamnesis['otros'] ?? '';
        $v['comportamiento'] = $data['PatientBehavior'] ?? '';

        $tinnitus = $data['Tinnitus'] ?? [];
        $v['tinnitus'] = [];
        foreach (['pulsatil', 'permanente'] as $flag) {
            if (!empty($tinnitus[$flag])) {
                $v['tinnitus'][$flag] = '1';
            }
        }
        $v['tinnitus']['lateralidad'] = $tinnitus['lateralidad'] ?? 'craneal';
        $v['tinnitus']['oido'] = $tinnitus['oido'] ?? 'od';
        $v['tinnitus']['predominio'] = $tinnitus['predominio'] ?? 'igual';
        $v['tinnitus']['ruido'] = $tinnitus['ruido'] ?? self::TINNITUS_RUIDO_OPTIONS[0];
        $v['tinnitus']['frecuencia'] = (string) ($tinnitus['frecuencia'] ?? self::FREQUENCIES[0]);

        return $v;
    }
}
