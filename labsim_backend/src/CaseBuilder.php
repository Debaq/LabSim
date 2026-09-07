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

    // Ficha Otoscopia: N tomas en el tiempo por oído (misma cantidad para
    // OD y OI). 1 sola fase = "única" (no hay selector de modo aparte: el
    // número de fases mismo lo dice). Cada fase lleva un texto libre que
    // describe qué pasó desde la fase anterior (vacío en la fase 1 --
    // todavía no hay "anterior"). Qué fase le corresponde ver a cada
    // alumno según su propio avance con ese paciente: TODO, ver TODO.md.
    public const OTOSCOPIA_MAX_FASES = 20;

    public const Z_OPTIONS = ['A', 'As', 'Ad', 'C', 'Cs', 'B'];
    public const ETF_OPTIONS = ['Normal', 'Disfunción tubaria', 'Permeable', 'No permeable'];

    // Patología ABR por oído -- ver AbrMainWindow.py::test_test() (llama a
    // ABR_Curve, que mapea 'transmission' -> 'conductive' internamente).
    public const ABR_TYPE_OPTIONS = ['normal', 'coclear', 'transmission', 'neural'];

    // Patología EOA (OEA) por oído -- mismas categorías que ABR pero la
    // OEA responde distinto: 'neural' (neuropatía/retrococlear) mantiene
    // la OEA normal porque la cóclea está intacta (a diferencia de ABR,
    // que ahí sí sale alterado). Ver oae_attenuation_db en
    // src/oae/generators/base.py.
    public const EOAS_TYPE_OPTIONS = ['normal', 'coclear', 'transmission', 'neural'];

    // Frecuencias del perfil OEA por oído. Es la unión de las bandas que
    // usa cada prueba en el cliente (TEOAE 1-4k, DP-grama 1-8k, SFOAE
    // 0.5-4k, SOAE 0.7-4.5k), así el docente configura UNA curva por oído
    // y las cuatro pruebas quedan coherentes entre sí (una muesca en 4k
    // aparece en todas, como en un paciente real). Ver
    // resources/oae/normative_data.json.
    public const EOAS_FREQS = [500, 1000, 1500, 2000, 3000, 4000, 6000, 8000];

    // Desviación por frecuencia (dB) preseteada por patología, para el
    // botón "Autocompletar" del formulario: la coclear típica cae en
    // agudos, la de transmisión atenúa parejo con algo más en graves
    // (el oído medio transmite peor los graves de vuelta), la neural
    // deja la OEA intacta. Son valores de partida editables, no fijos
    // (memoria no_fixed_teaching_defaults: el docente ajusta el caso).
    public const EOAS_AUTOFILL_DELTAS = [
        'normal'       => [500 => 0, 1000 => 0, 1500 => 0, 2000 => 0, 3000 => 0, 4000 => 0, 6000 => 0, 8000 => 0],
        'coclear'      => [500 => 0, 1000 => 1, 1500 => 2, 2000 => 3, 3000 => 5, 4000 => 8, 6000 => 10, 8000 => 12],
        'transmission' => [500 => 6, 1000 => 5, 1500 => 4, 2000 => 4, 3000 => 3, 4000 => 3, 6000 => 3, 8000 => 3],
        'neural'       => [500 => 0, 1000 => 0, 1500 => 0, 2000 => 0, 3000 => 0, 4000 => 0, 6000 => 0, 8000 => 0],
    ];

    // SOAE (emisiones espontáneas): solo ~40-50% de los oídos normales
    // las tienen, así que en 'auto' el cliente las sortea (determinístico
    // por caso: el mismo paciente da siempre lo mismo). 'presentes' y
    // 'ausentes' fijan el hallazgo para poder mostrarlo en clase o evaluar
    // sobre algo que no cambie de oído en oído. Ver true_peaks() en
    // src/oae/generators/soae.py.
    public const EOAS_SOAE_MODES = ['auto', 'presentes', 'ausentes'];
    public const EOAS_SOAE_MODE_LABELS = [
        'auto' => 'Auto (sorteo por prevalencia)',
        'presentes' => 'Presentes (forzar)',
        'ausentes' => 'Ausentes (forzar)',
    ];
    // Picos SOAE que el docente puede fijar a mano por oído. Tres alcanza:
    // un oído real rara vez muestra más de 2-3 picos claros.
    public const EOAS_SOAE_MAX_PEAKS = 3;
    public const EOAS_SOAE_FREQ_MIN = 500;
    public const EOAS_SOAE_FREQ_MAX = 7000;
    // Nivel por defecto de un pico fijado a mano: en 1-2 kHz deja ~10 dB
    // sobre el piso, o sea visible sin ser irreal (los SOAE reales rondan
    // los 0 dB SPL y rara vez pasan de 20).
    public const EOAS_SOAE_DEFAULT_PEAK_DB = 6.0;

    // Defaults del perfil OEA por oído (paciente "limpio": sin atenuación
    // extra, sin ruido agregado, sello de sonda bueno).
    public const EOAS_DEFAULTS = [
        'umbral' => 20,
        'atten_db' => 0.0,
        'ruido_db' => 0.0,
        'sello_pct' => 85,
        'variabilidad_db' => 2.5,
        'soae_mode' => 'auto',
    ];

    // Patología VEMP por oído -- categorías vestibulares. 'sacular' afecta
    // CVEMP (P13/N23 sobre SCM), 'utricular' afecta OVEMP (N10/P16 sobre
    // oblicuo inferior), 'neural' afecta ambos (neuropatía vestibular).
    // Ver VEMP_generator_v1.py::calculate_wave_parameters.
    public const VEMP_TYPE_OPTIONS = ['normal', 'sacular', 'utricular', 'neural'];
    public const VEMP_SUBTIPOS = ['CVEMP', 'OVEMP', 'MVEMP'];

    // Picos por subtipo (orden de aparición en curva/tabla/PDF).
    public const VEMP_PEAKS = [
        'CVEMP' => ['p13', 'n23'],
        'OVEMP' => ['n10', 'p16'],
        'MVEMP' => ['p13', 'n23'],
    ];

    // Acumetría (diapasones 500 y 1000 Hz) -- se guarda dentro de
    // audiometría, no es tab aparte. Rinne es por oído (CA vs CO en ese
    // oído); Weber es un único resultado por frecuencia (a qué lado
    // lateraliza, o ninguno). Auto-calculado desde los umbrales tonales ya
    // cargados (índices 2=500Hz, 3=1000Hz en FREQUENCIES/Aerea/Osea),
    // modificable a mano por checkbox "auto" (mismo patrón que sdt_auto/
    // srt_auto con Fletcher).
    public const ACUMETRIA_FREQS = ['500' => 2, '1000' => 3]; // Hz => índice en FREQUENCIES

    public const RINNE_OPTIONS = ['positivo', 'negativo', 'falso_negativo'];
    public const RINNE_LABELS = [
        'positivo' => 'Positivo (CA > CO)',
        'negativo' => 'Negativo (CO > CA)',
        'falso_negativo' => 'Falso negativo (hipoacusia sensorioneural profunda, cruce óseo contralateral)',
    ];
    // Gap aérea-ósea (dB) desde el cual el Rinne auto-calculado da negativo.
    public const RINNE_GAP_THRESHOLD = 15;

    public const WEBER_OPTIONS = ['centrado', 'od', 'oi'];
    public const WEBER_LABELS = [
        'centrado' => 'Sin lateralización (centrado)',
        'od' => 'Lateraliza a OD',
        'oi' => 'Lateraliza a OI',
    ];
    // Asimetría de vía ósea (dB) entre oídos desde la cual el Weber
    // auto-calculado lateraliza (al oído con mejor -- menor dB -- umbral óseo).
    public const WEBER_ASYMMETRY_THRESHOLD = 10;

    /** Rinne auto: negativo si el gap aérea-ósea de ese oído en esa frecuencia es >= RINNE_GAP_THRESHOLD. "falso_negativo" nunca se auto-calcula, es solo elegible a mano. */
    /**
     * Picos SOAE cargados en el formulario -> shape de cases.data.
     *
     * Una fila sin Hz se ignora (el docente carga 1 pico y no tres), y el
     * nivel en blanco toma EOAS_SOAE_DEFAULT_PEAK_DB.
     */
    public static function soaePeaksFromForm($rows): array
    {
        $picos = [];
        if (!is_array($rows)) {
            return $picos;
        }
        for ($i = 0; $i < self::EOAS_SOAE_MAX_PEAKS; $i++) {
            $row = is_array($rows[$i] ?? null) ? $rows[$i] : [];
            $hz = (float) ($row['hz'] ?? 0);
            if ($hz <= 0) {
                continue;
            }
            $db = $row['db'] ?? '';
            $picos[] = [
                'hz' => $hz,
                'db' => ($db === '' || $db === null) ? self::EOAS_SOAE_DEFAULT_PEAK_DB : (float) $db,
            ];
        }
        return $picos;
    }

    /**
     * Valida los picos SOAE de un oído. Devuelve el mensaje de error o null.
     *
     * La separación mínima no es capricho: dos SOAE muy juntos se suprimen
     * entre sí y no coexisten en un oído real (~0.4 bark, ~6%). Ver
     * min_peak_spacing_ratio en resources/oae/normative_data.json.
     */
    public static function soaePeaksError(array $eoasLado): ?string
    {
        $picos = $eoasLado['soae_peaks'] ?? [];
        if (($eoasLado['soae_mode'] ?? 'auto') === 'ausentes' && $picos !== []) {
            return 'SOAE en modo "ausentes" no puede tener picos cargados: borrá las frecuencias o cambiá el modo.';
        }
        // Ordenados por frecuencia: el docente puede cargarlos en cualquier
        // orden en el formulario.
        usort($picos, static fn($a, $b) => $a['hz'] <=> $b['hz']);
        $hzPrevio = null;
        foreach ($picos as $pico) {
            if ($pico['hz'] < self::EOAS_SOAE_FREQ_MIN || $pico['hz'] > self::EOAS_SOAE_FREQ_MAX) {
                return sprintf('Frecuencia SOAE fuera de rango (%d-%d Hz).',
                    self::EOAS_SOAE_FREQ_MIN, self::EOAS_SOAE_FREQ_MAX);
            }
            if ($pico['db'] < -15 || $pico['db'] > 30) {
                return 'Nivel SOAE fuera de rango (-15 a 30 dB SPL).';
            }
            if ($hzPrevio !== null && (max($pico['hz'], $hzPrevio) / min($pico['hz'], $hzPrevio)) < 1.06) {
                return 'Dos picos SOAE del mismo oído deben estar separados al menos 6% en frecuencia (se suprimen entre sí).';
            }
            $hzPrevio = $pico['hz'];
        }
        return null;
    }

    public static function rinneAuto(int $air, int $bone): string
    {
        return ($air - $bone) >= self::RINNE_GAP_THRESHOLD ? 'negativo' : 'positivo';
    }

    /** Weber auto: lateraliza al oído con mejor (menor) umbral óseo si la asimetría ósea entre oídos es >= WEBER_ASYMMETRY_THRESHOLD; si no, centrado. */
    public static function weberAuto(int $boneOd, int $boneOi): string
    {
        if (abs($boneOd - $boneOi) < self::WEBER_ASYMMETRY_THRESHOLD) {
            return 'centrado';
        }
        return $boneOd < $boneOi ? 'od' : 'oi';
    }

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
    // 'normal' ES el patrón "ON" (meseta sostenida); no existe un tipo "on"
    // aparte, quedaba duplicado con este.
    public const REFLEX_CURVE_TYPES = ['normal', 'invertido', 'off', 'on-off'];

    public const REFLEX_CURVE_LABELS = [
        'normal' => 'ON',
        'invertido' => 'Invertido',
        'off' => 'OFF',
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

    /**
     * Fallback server-side de la fecha de nacimiento a partir de la edad --
     * el cálculo real vive en JS (case_create.php, recalcula al tipear la
     * edad); esto solo cubre el caso de que el campo llegue vacío (JS
     * deshabilitado). Año = año actual - edad, día/mes al azar dentro de
     * ese año.
     */
    public static function randomFechaNacForAge(int $age): string
    {
        $birthYear = (int) date('Y') - $age;
        $randomDay = random_int(0, 364);
        return date('d-m-Y', mktime(0, 0, 0, 1, 1 + $randomDay, $birthYear));
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
            'Rinne' => $form['rinne'],
            'Weber' => $form['weber'],
            'sector' => 'Camara_sono',
            'edad' => $age,
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
            'Carhart' => $form['carhart'],
            'Stat' => $form['stat'],
            'Rosemberg' => $form['rosemberg'],
            'Reflex' => $form['reflex'],
            'ETF' => [$form['etf_od'], $form['etf_oi']],
            'Anamnesis' => $form['anamnesis'],
            'PatientBehavior' => $form['comportamiento'] ?? '',
            'PatientDisposition' => (int) ($form['disposicion'] ?? 0),
            'Tinnitus' => $form['tinnitus'],
            'Otoscopia' => $form['otoscopia'],
            'ABR' => $form['abr'],
            'EOAS' => $form['eoas'],
            'VEMP' => $form['vemp'],
            'tipo' => 'normal',
        ];
    }

    /**
     * Inverso de buildCaseData(): reconstruye el shape de $_POST que espera
     * case_create.php a partir de un `cases.data` ya guardado, para
     * precargar el formulario al editar un caso existente.
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
        $v['age'] = isset($data['edad']) ? (string) $data['edad'] : '';

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

        // Igual que sdt_auto/srt_auto: se muestra el valor guardado tal cual
        // (acumetria_auto queda sin marcar) -- si quedara tildado el checkbox
        // "auto" el JS lo pisaría con el recálculo apenas cargara la página.
        $v['acumetria_auto'] = '';
        foreach (self::ACUMETRIA_FREQS as $hz => $freqIdx) {
            $v['rinne'][$hz]['od'] = $data['Rinne'][$hz]['od'] ?? 'positivo';
            $v['rinne'][$hz]['oi'] = $data['Rinne'][$hz]['oi'] ?? 'positivo';
            $v['weber'][$hz] = $data['Weber'][$hz] ?? 'centrado';
        }

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

        // Conteo fijo (no derivado de count($data[...])): un caso viejo sin
        // esta clave debe igual rellenar las N frecuencias del protocolo con
        // 0 (sin deterioro), no quedar con un array vacío.
        foreach (['carhart' => ['Carhart', 4], 'stat' => ['Stat', 3], 'rosemberg' => ['Rosemberg', 4]] as $formKey => [$dataKey, $count]) {
            [$od, $oi] = $unzip($data[$dataKey] ?? [], $count);
            $v[$formKey] = ['od' => $od, 'oi' => $oi];
        }

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
        $v['disposicion'] = (string) ($data['PatientDisposition'] ?? 0);

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

        // 'modo' venía en versiones anteriores de esta ficha (antes de que
        // se sacara el selector) -- se ignora si aparece en un caso viejo,
        // el número de fases ya guardadas dice lo mismo sin necesitarlo.
        $otoscopia = $data['Otoscopia'] ?? [];
        $otoscopiaFases = $otoscopia['fases'] ?? [];
        if (!is_array($otoscopiaFases) || count($otoscopiaFases) === 0) {
            $otoscopiaFases = [['texto' => '']];
        }
        $v['otoscopia'] = [
            'fases' => array_map(
                static fn($f) => ['texto' => (string) (is_array($f) ? ($f['texto'] ?? '') : '')],
                array_values($otoscopiaFases)
            ),
        ];

        $abr = $data['ABR'] ?? [];
        foreach (['OD' => 'od', 'OI' => 'oi'] as $ladoData => $ladoForm) {
            $ladoAbr = is_array($abr[$ladoData] ?? null) ? $abr[$ladoData] : [];
            $desv = is_array($ladoAbr['desviaciones'] ?? null) ? $ladoAbr['desviaciones'] : [];
            $fsp = is_array($ladoAbr['fsp_puntos'] ?? null) ? $ladoAbr['fsp_puntos'] : [];
            $ondaVal = static function (array $desv, string $onda, string $campo, $default) {
                return (string) ($desv[$onda][$campo] ?? $default);
            };
            $ladoAbrType = $ladoAbr['type'] ?? 'normal';
            $v['abr'][$ladoForm] = [
                'type' => in_array($ladoAbrType, self::ABR_TYPE_OPTIONS, true) ? $ladoAbrType : 'normal',
                'umbral' => (string) ($ladoAbr['umbral'] ?? 20),
                'lat_I' => $ondaVal($desv, 'onda_I', 'lat', 0),
                'amp_I' => $ondaVal($desv, 'onda_I', 'amp', 0),
                'lat_III' => $ondaVal($desv, 'onda_III', 'lat', 0),
                'amp_III' => $ondaVal($desv, 'onda_III', 'amp', 0),
                'lat_V' => $ondaVal($desv, 'onda_V', 'lat', 0),
                'amp_V' => $ondaVal($desv, 'onda_V', 'amp', 0),
                'fsp_800' => (string) ($fsp['800'] ?? 2.3),
                'fsp_2000' => (string) ($fsp['2000'] ?? 2.8),
                'fsp_obj' => (string) ($fsp['objetivo'] ?? 3.0),
            ];
            if (!empty($ladoAbr['repro']) || !isset($ladoAbr['repro'])) {
                // Default repro=true (caso nuevo sin ABR configurado aún, o
                // caso viejo de antes de esta clave -- ver DEFAULT_ABR_CASE
                // en AbrMainWindow.py): solo queda sin marcar si el docente
                // lo desmarcó explícitamente (repro === false guardado).
                $v['abr'][$ladoForm]['repro'] = '1';
            }
        }

        $eoas = $data['EOAS'] ?? [];
        foreach (['OD' => 'od', 'OI' => 'oi'] as $ladoData => $ladoForm) {
            $ladoEoas = is_array($eoas[$ladoData] ?? null) ? $eoas[$ladoData] : [];
            $ladoEoasType = $ladoEoas['type'] ?? 'normal';
            $desvEoas = is_array($ladoEoas['desviaciones'] ?? null) ? $ladoEoas['desviaciones'] : [];
            $v['eoas'][$ladoForm] = [
                'type' => in_array($ladoEoasType, self::EOAS_TYPE_OPTIONS, true) ? $ladoEoasType : 'normal',
                'umbral' => (string) ($ladoEoas['umbral'] ?? self::EOAS_DEFAULTS['umbral']),
                'atten_db' => (string) ($ladoEoas['atten_db'] ?? self::EOAS_DEFAULTS['atten_db']),
                'ruido_db' => (string) ($ladoEoas['ruido_db'] ?? self::EOAS_DEFAULTS['ruido_db']),
                'sello_pct' => (string) ($ladoEoas['sello_pct'] ?? self::EOAS_DEFAULTS['sello_pct']),
                'variabilidad_db' => (string) ($ladoEoas['variabilidad_db'] ?? self::EOAS_DEFAULTS['variabilidad_db']),
                'soae_mode' => in_array($ladoEoas['soae_mode'] ?? '', self::EOAS_SOAE_MODES, true)
                    ? $ladoEoas['soae_mode']
                    : self::EOAS_DEFAULTS['soae_mode'],
            ];
            // Picos SOAE fijados a mano (caso viejo: ninguno -> filas
            // vacías y el cliente decide por prevalencia).
            $picosSoae = is_array($ladoEoas['soae_peaks'] ?? null) ? array_values($ladoEoas['soae_peaks']) : [];
            for ($iSoae = 0; $iSoae < self::EOAS_SOAE_MAX_PEAKS; $iSoae++) {
                $picoSoae = is_array($picosSoae[$iSoae] ?? null) ? $picosSoae[$iSoae] : [];
                $v['eoas'][$ladoForm]['soae_peaks'][$iSoae] = [
                    'hz' => isset($picoSoae['hz']) ? (string) $picoSoae['hz'] : '',
                    'db' => isset($picoSoae['db']) ? (string) $picoSoae['db'] : '',
                ];
            }
            // Caso viejo (guardado antes del perfil por frecuencia): las
            // desviaciones no existen y quedan en 0 -- el cliente sigue
            // atenuando solo por type/umbral, igual que antes.
            foreach (self::EOAS_FREQS as $hzEoas) {
                $v['eoas'][$ladoForm]['desv'][(string) $hzEoas] = (string) ($desvEoas[(string) $hzEoas] ?? 0);
            }
        }

        $vemp = $data['VEMP'] ?? [];
        foreach (['OD' => 'od', 'OI' => 'oi'] as $ladoData => $ladoForm) {
            $ladoVemp = is_array($vemp[$ladoData] ?? null) ? $vemp[$ladoData] : [];
            $desv = is_array($ladoVemp['desviaciones'] ?? null) ? $ladoVemp['desviaciones'] : [];
            $ladoVempType = $ladoVemp['type'] ?? 'normal';
            $subtipo = $ladoVemp['subtipo'] ?? 'CVEMP';
            if (!in_array($subtipo, self::VEMP_SUBTIPOS, true)) {
                $subtipo = 'CVEMP';
            }
            $peaks = self::VEMP_PEAKS[$subtipo];
            $ladoFormArr = [
                'subtipo' => $subtipo,
                'type' => in_array($ladoVempType, self::VEMP_TYPE_OPTIONS, true) ? $ladoVempType : 'normal',
                'umbral' => (string) ($ladoVemp['umbral'] ?? 60),
                'repro_var' => (string) ($ladoVemp['repro_var'] ?? 0.2),
                'average_objetivo' => (string) ($ladoVemp['average_objetivo'] ?? 200),
            ];
            foreach ($peaks as $pico) {
                $ladoFormArr["lat_{$pico}"] = (string) ($desv[$pico]['lat'] ?? 0);
                $ladoFormArr["amp_{$pico}"] = (string) ($desv[$pico]['amp'] ?? 0);
            }
            if (!empty($ladoVemp['repro']) || !isset($ladoVemp['repro'])) {
                // Default repro=true (caso nuevo sin VEMP configurado aún):
                // solo queda sin marcar si el docente lo desmarcó
                // explícitamente (repro === false guardado).
                $ladoFormArr['repro'] = '1';
            }
            $v['vemp'][$ladoForm] = $ladoFormArr;
        }

        return $v;
    }
}
