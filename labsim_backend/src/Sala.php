<?php

declare(strict_types=1);

/**
 * La sala de atención: quiénes están frente al alumno, no solo el paciente.
 *
 * Hasta ahora un caso era exactamente una persona ("el paciente") y el chat
 * era 1 a 1. Eso deja fuera la mitad de la clínica real: el lactante no
 * habla y todo lo cuenta la madre; al menor de 14 la ley lo obliga a venir
 * acompañado; al adulto mayor que niega su hipoacusia lo desmiente la
 * esposa que sí la nota. Ese contraste entre lo que el paciente dice y lo
 * que el acompañante afirma ES el hallazgo clínico, y sin sala no existe.
 *
 * Un caso guardado antes de esto no tiene sala: desde($data) le arma una de
 * una sola persona a partir de los campos que ya existían
 * (PatientBehavior/PatientDisposition), así que nada se rompe y el chat
 * viejo sigue comportándose igual.
 *
 * Este archivo es solo modelo y reglas -- no toca BD ni LLM. El prompt de
 * cada persona lo arma LlmConfig; quién contesta cada turno se decide acá
 * (ver turno()) porque tiene que ser algo que el docente controle con los
 * rasgos del caso, no algo que el modelo improvise distinto cada vez.
 */
final class Sala
{
    public const VERSION = 1;

    /**
     * Edad bajo la cual el paciente NO puede ser atendido solo (Chile: el
     * menor de 14 requiere acompañante adulto). Es una regla del caso, no
     * una preferencia: CaseCompleteness la reclama como pendiente.
     */
    public const EDAD_ACOMPANANTE_OBLIGATORIO = 14;

    /**
     * Acompañantes que caben en el box por defecto. Existe para que el
     * alumno tenga que decidir a quién hace pasar cuando el caso trae más
     * gente que cupo -- decidirlo mal (dejar al lactante rodeado de cuatro
     * adultos, o peor, dejar al padre afuera) es evaluable.
     */
    public const AFORO_DEFAULT = 2;

    /**
     * Roles posibles. `paciente` es un rol más y no una entidad aparte: es
     * lo que permite que el motor de turnos trate a todos igual y que un
     * acompañante conteste una pregunta dirigida al paciente.
     */
    public const ROLES = [
        'paciente' => 'Paciente',
        'madre' => 'Madre',
        'padre' => 'Padre',
        'conyuge' => 'Cónyuge / pareja',
        'hijo' => 'Hijo/a',
        'abuelo' => 'Abuelo/a',
        'cuidador' => 'Cuidador/a',
        'hermano' => 'Hermano/a',
        'otro' => 'Otro acompañante',
    ];

    /**
     * Roles a los que el alumno NO puede pedirles que salgan del box. En
     * Chile no se le puede impedir a un padre acompañar a su hijo, así que
     * echar al padre es una falta, no una decisión de manejo de sala.
     */
    public const ROLES_NO_EXPULSABLES = ['madre', 'padre'];

    /**
     * Qué puede contar el propio paciente según su edad. No es un detalle
     * de ambientación: define de quién sale el dato clínico y, por lo
     * tanto, a quién tiene que preguntarle el alumno.
     */
    public const CAP_NULO = 'nulo';             // 0-2: no habla; solo conducta observable
    public const CAP_MINIMO = 'minimo';         // 3-5: nombre, "me duele acá", sí/no
    public const CAP_PARCIAL = 'parcial';       // 6-13: síntomas y colegio, no fechas ni fármacos
    public const CAP_CASI_TOTAL = 'casi_total'; // 14-17: casi todo, pero no lo perinatal
    public const CAP_TOTAL = 'total';           // adulto

    public const CAPACIDAD_DESC = [
        self::CAP_NULO => 'No hablas: eres una guagua. No produces frases. Solo hay conducta observable (llanto, sonrisa, girar la cabeza hacia un ruido, sacarte el fono, buscar a tu mamá).',
        self::CAP_MINIMO => 'Hablas poco y como niño pequeño: dices tu nombre, tu edad si la sabes, "me duele acá", "sí", "no". No manejas fechas, ni nombres de remedios, ni antecedentes.',
        self::CAP_PARCIAL => 'Hablas como niño de escuela: cuentas lo que sientes, lo que te pasa en el colegio, si escuchas mal la tele. No sabes desde cuándo con precisión, ni qué remedios tomas, ni nada de tu embarazo o tu parto.',
        self::CAP_CASI_TOTAL => 'Hablas como adolescente: cuentas casi todo lo tuyo con tus palabras. De tu embarazo, tu parto y tus primeros años solo sabes lo que te han contado, y no siempre bien.',
        self::CAP_TOTAL => 'Hablas como adulto: puedes contar tu historia completa, hasta donde la recuerdes y hasta donde tengas conciencia de tu problema.',
    ];

    /** Tipos de pregunta que el motor distingue para decidir quién contesta. */
    public const T_IDENTIDAD = 'identidad';
    public const T_SINTOMA = 'sintoma';
    public const T_TEMPORAL = 'temporal';
    public const T_FARMACO = 'farmaco';
    public const T_PERINATAL = 'perinatal';
    public const T_ANTECEDENTE = 'antecedente';
    public const T_GENERAL = 'general';

    /**
     * Qué tipo de pregunta puede contestar cada capacidad por sí misma.
     * Lo que cae fuera no es que se responda mal: lo contesta otro, y esa
     * es justamente la dinámica que el alumno tiene que aprender a leer.
     */
    public const MANEJA = [
        self::CAP_NULO => [],
        self::CAP_MINIMO => [self::T_IDENTIDAD, self::T_SINTOMA],
        self::CAP_PARCIAL => [self::T_IDENTIDAD, self::T_SINTOMA, self::T_GENERAL],
        self::CAP_CASI_TOTAL => [
            self::T_IDENTIDAD, self::T_SINTOMA, self::T_GENERAL,
            self::T_TEMPORAL, self::T_ANTECEDENTE,
        ],
        self::CAP_TOTAL => [
            self::T_IDENTIDAD, self::T_SINTOMA, self::T_GENERAL,
            self::T_TEMPORAL, self::T_ANTECEDENTE, self::T_FARMACO, self::T_PERINATAL,
        ],
    ];

    /**
     * Palabras que clasifican la pregunta del alumno. Sin tildes y en
     * minúsculas (ver normalizarTexto): el alumno escribe apurado y "desde
     * cuando" sin tilde tiene que clasificar igual que con ella.
     */
    private const PALABRAS_TIPO = [
        self::T_PERINATAL => [
            'embarazo', 'embarazada', 'parto', 'nacio', 'nacimiento', 'gesta',
            'prematuro', 'incubadora', 'neonatal', 'semanas de gestacion', 'cesarea',
            'lloro al nacer', 'apgar', 'ictericia', 'peso al nacer',
        ],
        self::T_FARMACO => [
            'medicamento', 'remedio', 'pastilla', 'farmaco', 'gotas', 'antibiotico',
            'tratamiento', 'toma algo', 'esta tomando', 'dosis', 'inyeccion',
        ],
        self::T_TEMPORAL => [
            'desde cuando', 'hace cuanto', 'cuando empezo', 'cuando comenzo',
            'hace cuantos', 'que edad tenia', 'primera vez', 'cuanto tiempo',
            'desde que', 'hace tiempo', 'que ano', 'cuando fue',
        ],
        self::T_ANTECEDENTE => [
            'operaron', 'operacion', 'cirugia', 'otitis', 'enfermedad', 'antecedente',
            'alergia', 'diabetes', 'presion', 'meningitis', 'convulsion',
            'lo vio otro', 'examen anterior', 'control anterior', 'audifono',
        ],
        self::T_SINTOMA => [
            'duele', 'dolor', 'escucha', 'escuchas', 'oye', 'oyes', 'molesta',
            'pito', 'pitido', 'zumbido', 'ruido', 'mareo', 'mareos', 'tapado',
            'supura', 'sale liquido', 'siente', 'sientes', 'te pasa', 'le pasa',
        ],
        self::T_IDENTIDAD => [
            'como te llamas', 'como se llama', 'cual es tu nombre', 'tu nombre',
            'cuantos anos', 'que edad', 'en que curso', 'donde vives', 'donde vive',
        ],
    ];

    /**
     * Frases con las que el alumno contiene al acompañante que contesta
     * por el paciente ("déjelo contestar a él"). Que esto funcione importa:
     * es la maniobra de entrevista que se quiere enseñar, y si el modelo
     * la ignorara el ejercicio no tendría salida.
     */
    private const PALABRAS_CONTENCION = [
        'dejelo', 'dejela', 'deje que', 'dejen que', 'permitame preguntarle',
        'quiero que me conteste', 'prefiero que responda', 'no la interrumpa',
        'no lo interrumpa', 'que conteste el', 'que conteste ella', 'que responda el',
        'que responda ella', 'le pregunto a', 'espere un momento',
    ];

    /** Turnos que dura la contención antes de que el acompañante vuelva a meterse. */
    public const SILENCIO_TURNOS = 3;

    /**
     * Máximo de personas que hablan en un turno además del destinatario.
     * Uno, y no "los que gatillen": dos interrupciones simultáneas suenan a
     * ruido, se leen mal en el chat y cuestan una llamada al LLM cada una.
     */
    public const MAX_INTERRUPCIONES = 1;

    /** Umbral de conciencia bajo el cual el paciente niega/minimiza lo suyo. */
    public const CONCIENCIA_BAJA = 40;

    public const RASGOS_DEFAULT = [
        'interrumpe' => 20,
        'conciencia' => 80,
        'confiabilidad' => 80,
    ];

    // -----------------------------------------------------------------
    // Modelo
    // -----------------------------------------------------------------

    /** Capacidad de relato que le corresponde a una edad en años. */
    public static function capacidad(int $edad): string
    {
        if ($edad <= 2) {
            return self::CAP_NULO;
        }
        if ($edad <= 5) {
            return self::CAP_MINIMO;
        }
        if ($edad <= 13) {
            return self::CAP_PARCIAL;
        }
        if ($edad <= 17) {
            return self::CAP_CASI_TOTAL;
        }
        return self::CAP_TOTAL;
    }

    /** ¿Esta persona puede contestar por sí misma una pregunta de este tipo? */
    public static function maneja(string $capacidad, string $tipo): bool
    {
        return in_array($tipo, self::MANEJA[$capacidad] ?? [], true);
    }

    /**
     * Normaliza una persona suelta contra los defaults. Las claves
     * desconocidas se descartan: esto viene de cases.data, que un docente
     * puede haber editado a mano desde una versión anterior del formulario.
     */
    public static function normalizePersona(array $p, int $indice = 0): array
    {
        $rol = (string) ($p['rol'] ?? 'otro');
        if (!isset(self::ROLES[$rol])) {
            $rol = 'otro';
        }
        $esPaciente = (bool) ($p['es_paciente'] ?? ($rol === 'paciente'));
        $edad = max(0, (int) ($p['edad'] ?? 0));

        return [
            'id' => self::safeId((string) ($p['id'] ?? ''), $indice),
            'rol' => $rol,
            'nombre' => trim((string) ($p['nombre'] ?? '')),
            'edad' => $edad,
            'genero' => (int) ($p['genero'] ?? 0) === 1 ? 1 : 0,
            'es_paciente' => $esPaciente,
            // El paciente nunca se va del box, y madre/padre no se pueden
            // echar. El resto sí, y decidirlo es parte del ejercicio.
            'obligatorio' => $esPaciente || in_array($rol, self::ROLES_NO_EXPULSABLES, true),
            'presente' => (bool) ($p['presente'] ?? true),
            'informante' => (bool) ($p['informante'] ?? false),
            'interrumpe' => self::pct($p['interrumpe'] ?? self::RASGOS_DEFAULT['interrumpe']),
            'conciencia' => self::pct($p['conciencia'] ?? self::RASGOS_DEFAULT['conciencia']),
            'confiabilidad' => self::pct($p['confiabilidad'] ?? self::RASGOS_DEFAULT['confiabilidad']),
            'version' => trim((string) ($p['version'] ?? '')),
            'comportamiento' => trim((string) ($p['comportamiento'] ?? '')),
            'disposicion' => max(-2, min(2, (int) ($p['disposicion'] ?? 0))),
        ];
    }

    /**
     * Normaliza la sala completa y deja invariantes que el resto del código
     * da por ciertas: hay exactamente un paciente, hay exactamente un
     * informante principal, y todos los ids son distintos.
     */
    public static function normalize(array $sala): array
    {
        $personas = [];
        $i = 0;
        foreach ((array) ($sala['personas'] ?? []) as $p) {
            if (!is_array($p)) {
                continue;
            }
            $personas[] = self::normalizePersona($p, $i);
            $i++;
        }
        $personas = self::dedupIds($personas);

        // Un solo paciente: si el formulario mandó dos marcados (o ninguno),
        // gana el primero, y si no hay ninguno se promueve el primero de la
        // lista -- una sala sin paciente no es representable río abajo.
        $vistoPaciente = false;
        foreach ($personas as $k => $p) {
            if ($p['es_paciente'] && !$vistoPaciente) {
                $vistoPaciente = true;
                continue;
            }
            if ($p['es_paciente']) {
                $personas[$k]['es_paciente'] = false;
                $personas[$k]['obligatorio'] = in_array($p['rol'], self::ROLES_NO_EXPULSABLES, true);
            }
        }
        if (!$vistoPaciente && $personas) {
            $personas[0]['es_paciente'] = true;
            $personas[0]['rol'] = 'paciente';
            $personas[0]['obligatorio'] = true;
        }

        $personas = self::asignarInformante($personas);

        return [
            'version' => self::VERSION,
            'aforo' => max(1, (int) ($sala['aforo'] ?? self::AFORO_DEFAULT)),
            'personas' => array_values($personas),
        ];
    }

    /**
     * Deja un único informante principal: quien aporta el relato clínico
     * cuando el alumno pregunta "a la sala" sin dirigirse a nadie.
     *
     * Si el docente no marcó a nadie, se elige solo: el paciente si su edad
     * le da para contar su historia, y si no el primer acompañante adulto
     * presente. Un lactante sin acompañante quedaría como informante de sí
     * mismo, que es absurdo pero irrepresentable de otra forma -- para eso
     * está la validación de CaseCompleteness.
     */
    private static function asignarInformante(array $personas): array
    {
        $idx = null;
        foreach ($personas as $k => $p) {
            if ($p['informante']) {
                $idx = $idx ?? $k;
            }
            $personas[$k]['informante'] = false;
        }
        if ($idx === null) {
            foreach ($personas as $k => $p) {
                if ($p['es_paciente'] && self::capacidad($p['edad']) !== self::CAP_NULO
                    && self::capacidad($p['edad']) !== self::CAP_MINIMO) {
                    $idx = $k;
                    break;
                }
            }
        }
        if ($idx === null) {
            foreach ($personas as $k => $p) {
                if (!$p['es_paciente'] && $p['edad'] >= 18) {
                    $idx = $k;
                    break;
                }
            }
        }
        if ($idx === null && $personas) {
            $idx = 0;
        }
        if ($idx !== null) {
            $personas[$idx]['informante'] = true;
        }
        return $personas;
    }

    private static function dedupIds(array $personas): array
    {
        $vistos = [];
        foreach ($personas as $k => $p) {
            $id = $p['id'];
            if (isset($vistos[$id])) {
                $id = 'p' . ($k + 1) . '_' . $k;
            }
            $vistos[$id] = true;
            $personas[$k]['id'] = $id;
        }
        return $personas;
    }

    /**
     * Id usable como nombre de archivo (la foto de cada persona se guarda
     * con el id pegado al case_id, ver PatientPhoto::key) y como valor de
     * un <select>. Vacío o con basura => pN por posición.
     */
    private static function safeId(string $id, int $indice): string
    {
        $safe = preg_replace('/[^A-Za-z0-9]/', '', $id) ?? '';
        return $safe !== '' ? substr($safe, 0, 16) : 'p' . ($indice + 1);
    }

    private static function pct($valor): int
    {
        return max(0, min(100, (int) $valor));
    }

    /**
     * Sala efectiva de un caso guardado. Si el caso no trae sala (creado
     * antes de esto, o desde create_a.py), se arma una de una sola persona
     * con los campos de paciente que ya existían: el chat se comporta
     * exactamente como antes, un paciente y nadie más.
     *
     * $nombre/$edad vienen de la cita (no viven en cases.data, ver
     * llm_chat.php) y solo se usan para ese caso de respaldo.
     */
    public static function desde(array $caseData, string $nombre = '', int $edad = 0): array
    {
        $sala = $caseData['Sala'] ?? null;
        if (is_array($sala) && !empty($sala['personas'])) {
            $normal = self::normalize($sala);
            // El nombre/edad reales del paciente son los de la cita: la
            // sala guardada puede haberse escrito con un nombre de ejemplo.
            foreach ($normal['personas'] as $k => $p) {
                if ($p['es_paciente']) {
                    if ($nombre !== '') {
                        $normal['personas'][$k]['nombre'] = $nombre;
                    }
                    if ($edad > 0) {
                        $normal['personas'][$k]['edad'] = $edad;
                    }
                    break;
                }
            }
            return $normal;
        }

        return self::normalize([
            'aforo' => self::AFORO_DEFAULT,
            'personas' => [[
                'id' => 'p1',
                'rol' => 'paciente',
                'nombre' => $nombre !== '' ? $nombre : 'el paciente',
                'edad' => $edad > 0 ? $edad : (int) ($caseData['edad'] ?? 0),
                'genero' => (int) ($caseData['gender'] ?? 0),
                'es_paciente' => true,
                'informante' => true,
                'comportamiento' => (string) ($caseData['PatientBehavior'] ?? ''),
                'disposicion' => (int) ($caseData['PatientDisposition'] ?? 0),
            ]],
        ]);
    }

    /** @return array<string,mixed>|null la persona con ese id, o null. */
    public static function persona(array $sala, string $id): ?array
    {
        foreach ($sala['personas'] as $p) {
            if ($p['id'] === $id) {
                return $p;
            }
        }
        return null;
    }

    public static function paciente(array $sala): ?array
    {
        foreach ($sala['personas'] as $p) {
            if ($p['es_paciente']) {
                return $p;
            }
        }
        return null;
    }

    public static function informante(array $sala): ?array
    {
        foreach ($sala['personas'] as $p) {
            if ($p['informante'] && $p['presente']) {
                return $p;
            }
        }
        // El informante marcado puede estar fuera del box (el alumno lo hizo
        // salir): contesta quien quedó adentro, no nadie.
        foreach ($sala['personas'] as $p) {
            if ($p['presente']) {
                return $p;
            }
        }
        return null;
    }

    /** @return array<int,array<string,mixed>> los que están dentro del box. */
    public static function presentes(array $sala): array
    {
        return array_values(array_filter($sala['personas'], static fn($p) => $p['presente']));
    }

    /**
     * La sala tal como la pinta el cliente: quién está, quién puede hablar,
     * a quién se le puede pedir que salga. Es lo único de la sala que sale
     * del servidor -- los rasgos (cuánto interrumpe, cuánta conciencia
     * tiene) se quedan acá: son la respuesta del ejercicio.
     */
    public static function paraCliente(array $sala): array
    {
        $out = [];
        foreach ($sala['personas'] as $p) {
            $out[] = [
                'id' => $p['id'],
                'nombre' => $p['nombre'],
                'rol' => $p['rol'],
                'etiqueta' => self::etiqueta($p),
                'es_paciente' => $p['es_paciente'],
                'obligatorio' => $p['obligatorio'],
                'presente' => $p['presente'],
                'informante' => $p['informante'],
                // Una guagua no cuenta nada, pero igual se le puede hablar:
                // lo que devuelve es conducta observable, no una frase.
                'habla' => self::capacidad((int) $p['edad']) !== self::CAP_NULO,
            ];
        }
        return $out;
    }

    /** Etiqueta corta para la UI: "Rosa (madre)" -- o solo el rol si no hay nombre. */
    public static function etiqueta(array $persona): string
    {
        $rol = self::ROLES[$persona['rol']] ?? 'Acompañante';
        $nombre = $persona['nombre'];
        if ($nombre === '') {
            return $rol;
        }
        return $persona['es_paciente'] ? $nombre : "{$nombre} ({$rol})";
    }

    // -----------------------------------------------------------------
    // Formulario del editor de casos (case_create.php)
    // -----------------------------------------------------------------

    /**
     * Arma la sala desde el $_POST del editor de casos. Los acompañantes
     * viajan como arrays paralelos (sala_rol[], sala_nombre[], ...), que es
     * lo que produce una tabla de filas que se agregan y se borran en el
     * navegador.
     *
     * El paciente NO viene en esas filas: sus datos ya están en el resto
     * del formulario (edad, género, comportamiento, sensibilidad) y
     * repetirlos acá sería tener dos verdades para lo mismo. Se inyecta
     * como primera persona con $paciente.
     *
     * @param array $paciente nombre, edad, genero, comportamiento, disposicion
     */
    public static function fromForm(array $v, array $paciente): array
    {
        $personas = [[
            'id' => 'p1',
            'rol' => 'paciente',
            'nombre' => trim((string) ($paciente['nombre'] ?? '')),
            'edad' => (int) ($paciente['edad'] ?? 0),
            'genero' => (int) ($paciente['genero'] ?? 0),
            'es_paciente' => true,
            'presente' => true,
            'informante' => ((string) ($v['sala_informante'] ?? 'p1')) === 'p1',
            'comportamiento' => (string) ($paciente['comportamiento'] ?? ''),
            'disposicion' => (int) ($paciente['disposicion'] ?? 0),
            'conciencia' => self::pct($v['paciente_conciencia'] ?? self::RASGOS_DEFAULT['conciencia']),
            'confiabilidad' => self::pct($v['paciente_confiabilidad'] ?? self::RASGOS_DEFAULT['confiabilidad']),
        ]];

        $roles = (array) ($v['sala_rol'] ?? []);
        foreach (array_keys($roles) as $i) {
            $campo = static fn(string $k, $default = '') => ((array) ($v[$k] ?? []))[$i] ?? $default;
            $nombre = trim((string) $campo('sala_nombre'));
            $rol = (string) $campo('sala_rol');
            // Fila en blanco: el editor deja una plantilla vacía al final y
            // guardarla crearía un acompañante fantasma sin nombre ni rol.
            if ($nombre === '' && ($rol === '' || $rol === 'otro')) {
                continue;
            }
            // El id viaja en el formulario (sala_id[]) y no se deriva de
            // la posición: la foto de cada acompañante se guarda con ese id
            // (ver PatientPhoto::key), así que borrar una fila de más
            // arriba no puede correrle la cara a los demás.
            $id = self::safeId((string) $campo('sala_id'), $i + 1);
            $personas[] = [
                'id' => $id,
                'rol' => $rol,
                'nombre' => $nombre,
                'edad' => (int) $campo('sala_edad', 0),
                'genero' => (int) $campo('sala_genero', 0),
                'es_paciente' => false,
                'presente' => true,
                'informante' => ((string) ($v['sala_informante'] ?? '')) === $id,
                'interrumpe' => $campo('sala_interrumpe', self::RASGOS_DEFAULT['interrumpe']),
                'confiabilidad' => $campo('sala_confiabilidad', self::RASGOS_DEFAULT['confiabilidad']),
                'version' => (string) $campo('sala_version'),
                'comportamiento' => (string) $campo('sala_comportamiento'),
                'disposicion' => (int) $campo('sala_disposicion', 0),
            ];
        }

        return self::normalize([
            'aforo' => (int) ($v['sala_aforo'] ?? self::AFORO_DEFAULT),
            'personas' => $personas,
        ]);
    }

    /**
     * Inverso de fromForm(): el shape que espera el editor para repintar
     * las filas de una sala ya guardada. El paciente queda fuera de
     * `acompanantes` por el mismo motivo que en fromForm.
     */
    public static function toForm(array $sala): array
    {
        $acompanantes = [];
        $informante = 'p1';
        $conciencia = self::RASGOS_DEFAULT['conciencia'];
        $confiabilidad = self::RASGOS_DEFAULT['confiabilidad'];

        foreach ($sala['personas'] as $p) {
            if ($p['informante']) {
                $informante = $p['id'];
            }
            if ($p['es_paciente']) {
                $conciencia = $p['conciencia'];
                $confiabilidad = $p['confiabilidad'];
                continue;
            }
            $acompanantes[] = $p;
        }

        return [
            'sala_aforo' => (string) $sala['aforo'],
            'sala_informante' => $informante,
            'paciente_conciencia' => (string) $conciencia,
            'paciente_confiabilidad' => (string) $confiabilidad,
            'acompanantes' => $acompanantes,
        ];
    }

    // -----------------------------------------------------------------
    // Validación (la consume CaseCompleteness)
    // -----------------------------------------------------------------

    /**
     * Problemas de la sala de un caso, en texto para el docente. Vacío =
     * la sala está bien armada.
     *
     * @return array<int,string>
     */
    public static function problemas(array $sala): array
    {
        $problemas = [];
        $paciente = self::paciente($sala);
        if ($paciente === null) {
            return ['La sala no tiene paciente.'];
        }

        $acompanantesAdultos = 0;
        foreach ($sala['personas'] as $p) {
            if (!$p['es_paciente'] && $p['edad'] >= 18) {
                $acompanantesAdultos++;
            }
            if ($p['nombre'] === '') {
                $problemas[] = 'Hay alguien en la sala sin nombre (' . (self::ROLES[$p['rol']] ?? 'acompañante') . ').';
            }
        }

        if ($paciente['edad'] < self::EDAD_ACOMPANANTE_OBLIGATORIO && $acompanantesAdultos === 0) {
            $problemas[] = sprintf(
                'El paciente tiene %d años: bajo los %d debe venir con un acompañante adulto.',
                $paciente['edad'],
                self::EDAD_ACOMPANANTE_OBLIGATORIO
            );
        }

        // Una guagua no puede ser su propio informante: el relato tiene que
        // salir de alguien que hable.
        if (self::capacidad($paciente['edad']) === self::CAP_NULO && $paciente['informante']) {
            $problemas[] = 'El paciente no habla por su edad: marca a un acompañante como informante principal.';
        }

        return $problemas;
    }

    // -----------------------------------------------------------------
    // Motor de turnos
    // -----------------------------------------------------------------

    /** Minúsculas sin tildes, para clasificar sin depender de cómo tipeó el alumno. */
    public static function normalizarTexto(string $texto): string
    {
        $texto = mb_strtolower($texto, 'UTF-8');
        return strtr($texto, [
            'á' => 'a', 'é' => 'e', 'í' => 'i', 'ó' => 'o', 'ú' => 'u',
            'ü' => 'u', 'ñ' => 'n',
        ]);
    }

    /**
     * De qué trata la pregunta del alumno. El orden importa: "¿desde cuándo
     * toma ese remedio?" es una pregunta de fármacos aunque tenga "desde
     * cuándo" -- lo que decide quién puede contestar es el dato pedido, y
     * el nombre del remedio lo sabe el que lo compra, no el niño.
     */
    public static function tipoPregunta(string $mensaje): string
    {
        $t = self::normalizarTexto($mensaje);
        foreach (self::PALABRAS_TIPO as $tipo => $palabras) {
            foreach ($palabras as $palabra) {
                if (strpos($t, $palabra) !== false) {
                    return $tipo;
                }
            }
        }
        return self::T_GENERAL;
    }

    /** ¿El alumno está pidiendo que dejen contestar al destinatario? */
    public static function esContencion(string $mensaje): bool
    {
        $t = self::normalizarTexto($mensaje);
        foreach (self::PALABRAS_CONTENCION as $palabra) {
            if (strpos($t, $palabra) !== false) {
                return true;
            }
        }
        return false;
    }

    /**
     * Quiénes hablan este turno.
     *
     * $dirigidoA: id de persona, o '' / 'sala' para preguntar al aire (lo
     * toma el informante principal, que es justamente lo que pasa en la
     * consulta real cuando uno no mira a nadie en particular).
     *
     * $silenciados: id => turnos que le quedan callado, producto de una
     * contención previa. El estado vive en el cliente y vuelve actualizado
     * en el resultado: el backend del chat es sin estado (cada turno manda
     * el historial completo) y meterle una tabla solo para esto sería
     * inventarle sesión a algo que no la tiene.
     *
     * $roll: inyectable para los tests -- por defecto random_int, porque en
     * una conversación real la abuela no interrumpe siempre en el mismo
     * turno.
     *
     * @return array{
     *   tipo: string,
     *   destinatario: ?array<string,mixed>,
     *   hablan: array<int,array{persona: array<string,mixed>, motivo: string}>,
     *   silenciados: array<string,int>
     * }
     */
    public static function turno(array $sala, string $dirigidoA, string $mensaje,
                                 array $silenciados = [], ?callable $roll = null): array
    {
        $roll = $roll ?? static fn(int $max) => random_int(1, $max);
        $tipo = self::tipoPregunta($mensaje);

        // Los silencios corren siempre, se haya contenido o no: un turno de
        // contención dura lo que dura y después el acompañante vuelve.
        $silenciados = self::descontarSilencios($silenciados);

        $destinatario = null;
        if ($dirigidoA !== '' && $dirigidoA !== 'sala') {
            $destinatario = self::persona($sala, $dirigidoA);
            if ($destinatario !== null && !$destinatario['presente']) {
                $destinatario = null;  // lo hicieron salir del box
            }
        }
        if ($destinatario === null) {
            $destinatario = self::informante($sala);
        }
        if ($destinatario === null) {
            return ['tipo' => $tipo, 'destinatario' => null, 'hablan' => [], 'silenciados' => $silenciados];
        }

        if (self::esContencion($mensaje)) {
            // "Señora, déjelo contestar a él": si el alumno no eligió
            // destinatario en la UI, el que estaba contestando era el
            // informante -- justamente a quien se está conteniendo. Contener
            // sin devolverle la palabra al paciente dejaría al alumno
            // hablando solo, así que el turno pasa al paciente.
            if (($dirigidoA === '' || $dirigidoA === 'sala') && !$destinatario['es_paciente']) {
                $paciente = self::paciente($sala);
                if ($paciente !== null && $paciente['presente']) {
                    $destinatario = $paciente;
                }
            }
            foreach (self::presentes($sala) as $p) {
                if ($p['id'] !== $destinatario['id']) {
                    $silenciados[$p['id']] = self::SILENCIO_TURNOS;
                }
            }
        }

        $capacidad = self::capacidad($destinatario['edad']);
        $manejaEl = self::maneja($capacidad, $tipo);

        $hablan = [[
            'persona' => $destinatario,
            'motivo' => $manejaEl ? 'responde' : ($capacidad === self::CAP_NULO ? 'no_verbal' : 'no_sabe'),
        ]];

        foreach (self::candidatosInterrupcion($sala, $destinatario, $tipo, $manejaEl, $silenciados, $roll) as $c) {
            $hablan[] = $c;
        }

        return [
            'tipo' => $tipo,
            'destinatario' => $destinatario,
            'hablan' => $hablan,
            'silenciados' => $silenciados,
        ];
    }

    /**
     * Quién se mete además del destinatario. El puntaje parte del rasgo
     * `interrumpe` que puso el docente y sube cuando la situación lo pide:
     * el destinatario no puede saber el dato, o lo está negando y el que
     * mira desde afuera sí lo ve.
     *
     * @return array<int,array{persona: array<string,mixed>, motivo: string}>
     */
    private static function candidatosInterrupcion(array $sala, array $destinatario, string $tipo,
                                                   bool $manejaEl, array $silenciados, callable $roll): array
    {
        $puntuados = [];
        foreach (self::presentes($sala) as $p) {
            if ($p['id'] === $destinatario['id'] || isset($silenciados[$p['id']])) {
                continue;
            }
            if (!self::maneja(self::capacidad($p['edad']), $tipo)) {
                continue;  // el que se mete tiene que poder aportar el dato
            }

            $puntaje = $p['interrumpe'];
            $motivo = 'interrumpe';

            // El dato no está al alcance del destinatario (la edad no le da,
            // o simplemente no le tocó vivirlo): quien lo tiene lo suelta.
            if (!$manejaEl) {
                $puntaje += 45;
                $motivo = 'aporta_dato';
            }

            // El clásico: el paciente niega su hipoacusia, el acompañante la
            // ve todos los días. Que aparezca solo si el destinatario tiene
            // baja conciencia lo hace un hallazgo del caso y no ruido.
            if ($destinatario['es_paciente'] && $destinatario['conciencia'] < self::CONCIENCIA_BAJA
                && in_array($tipo, [self::T_SINTOMA, self::T_TEMPORAL], true)) {
                $puntaje += 35;
                $motivo = 'corrige';
            }

            // Tiene su propia versión de los hechos: contradice al otro.
            if ($p['version'] !== '' && in_array($tipo, [self::T_SINTOMA, self::T_TEMPORAL, self::T_ANTECEDENTE], true)) {
                $puntaje += 20;
                if ($motivo === 'interrumpe') {
                    $motivo = 'contradice';
                }
            }

            $puntuados[] = ['persona' => $p, 'motivo' => $motivo, 'puntaje' => min(100, $puntaje)];
        }

        // Mayor puntaje primero: si dos podrían meterse, se mete el que la
        // situación empuja más, no el que quedó primero en la lista.
        usort($puntuados, static fn($a, $b) => $b['puntaje'] <=> $a['puntaje']);

        $elegidos = [];
        foreach ($puntuados as $c) {
            if (count($elegidos) >= self::MAX_INTERRUPCIONES) {
                break;
            }
            if ($roll(100) <= $c['puntaje']) {
                $elegidos[] = ['persona' => $c['persona'], 'motivo' => $c['motivo']];
            }
        }

        // Nadie puede contestar y el destinatario tampoco sabe: sin esto el
        // turno se iría en blanco (una guagua sola "respondiendo" una
        // pregunta sobre su parto). El de mayor puntaje entra igual.
        if (!$elegidos && !$manejaEl && $puntuados) {
            $elegidos[] = ['persona' => $puntuados[0]['persona'], 'motivo' => $puntuados[0]['motivo']];
        }

        return $elegidos;
    }

    /** @param array<string,int> $silenciados */
    private static function descontarSilencios(array $silenciados): array
    {
        $out = [];
        foreach ($silenciados as $id => $turnos) {
            $turnos = (int) $turnos - 1;
            if ($turnos > 0) {
                $out[(string) $id] = $turnos;
            }
        }
        return $out;
    }
}
