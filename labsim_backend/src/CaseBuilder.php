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

    public const Z_OPTIONS = ['A', 'As', 'Ad', 'C', 'Cs', 'B'];
    public const ETF_OPTIONS = ['Normal', 'Disfunción tubaria', 'Permeable', 'No permeable'];

    // Tipo de ruido percibido (acufenometría) -- "la forma" del acufeno,
    // junto a la frecuencia de matching (se reusa CaseBuilder::FREQUENCIES).
    public const TINNITUS_RUIDO_OPTIONS = ['Silbido', 'Zumbido', 'Siseo', 'Pitido', 'Campanilleo'];

    // Lateralidad del tinnitus -- independiente de permanente/ocasional (un
    // acufeno unilateral puede ser permanente igual que uno bilateral).
    // "unilateral" pide oído; "bilateral" admite predominio (asimetría).
    public const TINNITUS_LATERALIDAD_OPTIONS = ['craneal', 'unilateral', 'bilateral'];
    public const TINNITUS_PREDOMINIO_OPTIONS = ['igual', 'od', 'oi'];

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
        $v['fowler_freq'] = (string) ($fowler['freq'] ?? 0);
        $cuts = $fowler['cuts'] ?? [15, 30, 50];
        $v['fowler_cut1'] = (string) ($cuts[0] ?? 15);
        $v['fowler_cut2'] = (string) ($cuts[1] ?? 30);
        $v['fowler_cut3'] = (string) ($cuts[2] ?? 50);

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
