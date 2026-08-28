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
            'tipo' => 'normal',
        ];
    }
}
