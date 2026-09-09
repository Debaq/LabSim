<?php

require_once __DIR__ . '/CaseProfile.php';
require_once __DIR__ . '/CaseReview.php';
require_once __DIR__ . '/Sala.php';

/**
 * Qué le falta a un caso para poder atenderse.
 *
 * El perfil auditivo deriva casi todo (ver CaseProfile), pero hay cosas que
 * NO se pueden calcular: qué curva timpanométrica corresponde, si la trompa
 * está permeable, cómo se ven las ondas del ABR más allá del umbral, qué
 * pasa en el VEMP. Son decisiones clínicas, no cuentas.
 *
 * Antes eso quedaba en el default silencioso: un caso conductivo con
 * timpanograma A, o un ABR "coclear" con la morfología de onda de un oído
 * sano. El alumno se encontraba con un paciente que no cierra, y el docente
 * no tenía cómo enterarse.
 *
 * Esta clase es el criterio único de "caso listo", y lo usan los dos
 * lugares donde importa: el editor (no se sale de la edición con esto
 * pendiente) y la agenda (no se cita un paciente así).
 *
 * Un pendiente se apaga de dos maneras: arreglando el dato, o declarando
 * revisada la ficha en el Resumen del editor (ver CaseReview). Lo segundo
 * es una decisión del docente sobre su propio caso -- "el timpanograma en A
 * con ese gap es lo que quiero" es una respuesta válida, y el editor no
 * está para discutirla. La única que no se apaga tildando es la anamnesis
 * que escribió el modelo: ahí lo que falta no es una decisión clínica sino
 * que alguien haya leído un texto que se inventó una máquina.
 *
 * A propósito NO revisa lo que puede estar vacío con razón: la anamnesis
 * escrita a mano, el texto de otoscopia, el comportamiento del paciente. Un
 * caso puede no tener nada de eso y seguir siendo un caso. La excepción es
 * la anamnesis que escribió el LLM: eso no está vacío, está sin leer, y es
 * lo contrario de opcional (ver AnamnesisDraft).
 */
final class CaseCompleteness
{
    /**
     * Timpanogramas que implican disfunción tubaria: dejar la ETF en
     * "Normal" con una de estas es no haber decidido, no un hallazgo.
     * B = ocupación, C/Cs = presión negativa (retracción).
     */
    public const TYMP_DISFUNCION = ['B', 'C', 'Cs'];

    /**
     * Lo que le falta al caso, listo para mostrar.
     *
     * @param array<string,mixed> $data cases.data
     * @return list<array{tab:string, texto:string, aceptable?:bool}> `tab`
     *         es la pestaña de case_create.php donde se arregla;
     *         `aceptable` en false marca lo que NO alcanza con revisar.
     */
    public static function pending(array $data): array
    {
        $pendientes = [];
        $perfil = CaseProfile::normalize($data);
        $airPairs = is_array($data['Aerea'] ?? null) ? $data['Aerea'] : [];
        $bonePairs = is_array($data['Osea'] ?? null) ? $data['Osea'] : [];

        $tympPorLado = ['OD' => (string) ($data['Z_OD'] ?? 'A'), 'OI' => (string) ($data['Z_OI'] ?? 'A')];
        $etf = is_array($data['ETF'] ?? null) ? $data['ETF'] : ['Normal', 'Normal'];
        $etfPorLado = ['OD' => (string) ($etf[0] ?? 'Normal'), 'OI' => (string) ($etf[1] ?? 'Normal')];

        foreach (['OD' => 0, 'OI' => 1] as $lado => $sideIdx) {
            $decomp = CaseProfile::decompose(
                $airPairs, $bonePairs, $sideIdx, (float) ($perfil[$lado]['cce_pct'] ?? 100.0)
            );
            $gap = CaseProfile::coreMax($decomp['gap']);
            $tymp = $tympPorLado[$lado];

            // --- Oído medio: el timpanograma nunca se deriva, y es el
            // default más fácil de dejar sin tocar (todo caso nace en A).
            if ($tymp === 'A' && $gap >= CaseProfile::WARN_TYMP_GAP_DB) {
                $pendientes[] = [
                    'tab' => 'timpanometria',
                    'texto' => sprintf(
                        'Timpanometría %s: hay un gap aéreo-óseo de %d dB y la curva quedó en A. Elegí la que corresponde (B ocupación, As rígido, Ad hipercompliante, C retracción) -- eso no se puede calcular desde el audiograma.',
                        $lado, (int) round($gap)
                    ),
                ];
            } elseif (in_array($tymp, self::TYMP_DISFUNCION, true) && $etfPorLado[$lado] === 'Normal') {
                $pendientes[] = [
                    'tab' => 'timpanometria',
                    'texto' => sprintf(
                        'Función tubaria %s: el timpanograma %s dice que la trompa no está trabajando bien, pero la ETF quedó en "Normal". Decidí cuál corresponde.',
                        $lado, $tymp
                    ),
                ];
            }

            // --- ABR: el perfil da umbral y tipo, nunca la morfología de
            // las ondas. Sin eso, un oído "coclear" dibuja las latencias y
            // amplitudes de uno sano y el alumno no tiene qué leer.
            $abrLado = is_array(($data['ABR'] ?? [])[$lado] ?? null) ? $data['ABR'][$lado] : [];
            if (($abrLado['type'] ?? 'normal') !== 'normal'
                && self::allZero($abrLado['desviaciones'] ?? [])) {
                $pendientes[] = [
                    'tab' => 'abr',
                    'texto' => sprintf(
                        'ABR %s: la patología es "%s" pero las latencias y amplitudes de las ondas están todas en 0, o sea las de un oído sano. Usá "Autocompletar según patología" o cargalas a mano.',
                        $lado, (string) $abrLado['type']
                    ),
                ];
            }

            // --- VEMP: el perfil no tiene eje vestibular. Si el caso tiene
            // patrón retrococlear, alguien tiene que decir qué pasa acá.
            $vempLado = is_array(($data['VEMP'] ?? [])[$lado] ?? null) ? $data['VEMP'][$lado] : [];
            // Las desviaciones viven en cada subtipo (`subtipos`); en un caso
            // guardado antes de que fueran tres estaban en la raíz del oído,
            // y allZero() tiene que mirar los dos lugares para no reclamarle
            // un VEMP a un caso viejo que sí lo tenía cargado.
            $vempDesv = [$vempLado['desviaciones'] ?? []];
            foreach ((array) ($vempLado['subtipos'] ?? []) as $vempSub) {
                $vempDesv[] = is_array($vempSub) ? ($vempSub['desviaciones'] ?? []) : [];
            }
            // `decidido` (por oído, casilla de la ficha VEMP) es el
            // antecesor de la revisión por ficha y sigue valiendo para los
            // casos que se guardaron con él. Los nuevos lo apagan tildando
            // VEMP en el Resumen -- ver el filtro del final.
            //
            // La salida existe porque el normal a veces SÍ es el hallazgo:
            // en la neuropatía auditiva el VEMP conservado con el ABR
            // desarmado es lo que localiza la lesión, y reclamárselo obligaba
            // a inventarle una alteración vestibular para poder guardar.
            if (CaseProfile::retroActivo($perfil[$lado]['retro'] ?? [])
                && empty($vempLado['decidido'])
                && ($vempLado['type'] ?? 'normal') === 'normal'
                && self::allZero($vempDesv)) {
                $pendientes[] = [
                    'tab' => 'vemp',
                    'texto' => sprintf(
                        'VEMP %s: el caso tiene patrón retrococlear cargado y el VEMP quedó normal sin tocar. El perfil no cubre lo vestibular: decidí si la lesión lo compromete o no, y si la respuesta es que no, dalo por revisado en el Resumen -- un VEMP normal puede ser el hallazgo.',
                        $lado
                    ),
                ];
            }
        }

        // --- Anamnesis escrita por el LLM: no entra al caso sin que un
        // docente la haya leído. El modelo puede inventar una cirugía que
        // no existe o un fármaco que no es ototóxico, y eso le llega al
        // alumno como parte del caso, indistinguible de lo que escribió el
        // docente. Ver AnamnesisDraft.
        $ia = is_array(($data['Anamnesis'] ?? [])['ia'] ?? null) ? $data['Anamnesis']['ia'] : [];
        if (!empty($ia['generado']) && empty($ia['verificado'])) {
            $pendientes[] = [
                'tab' => 'anamnesis',
                'texto' => 'Anamnesis: el borrador lo escribió el modelo de lenguaje y todavía nadie lo verificó. Leelo y tildá la casilla de verificación -- lo que quede acá le llega al alumno como parte del caso.',
                // No se apaga desde el Resumen: la revisión por ficha dice
                // "miré esto y está bien", y acá lo que hace falta es
                // exactamente eso pero sobre el texto, en la ficha, con la
                // casilla que ya existe. Aceptarlo de lejos sería tildar
                // que se leyó algo que no se abrió.
                'aceptable' => false,
            ];
        }

        // --- Sala: quién viene con el paciente (ver Sala::problemas). No
        // se valida quién acompaña a quién -- eso son recomendaciones, no
        // requisitos. Lo único que se reclama es un paciente que por su
        // edad no habla y encima viene solo: ahí no hay con quién levantar
        // la historia.
        //
        // Solo se revisa si el caso YA tiene sala guardada. Un caso anterior
        // al chat grupal (o creado desde create_a.py) no la tiene, y
        // reclamarle un acompañante que nunca se le pudo cargar dejaría de
        // golpe sin agendar a todos los casos pediátricos que ya existen.
        // Guardar el caso una vez desde el editor le escribe la sala, y de
        // ahí en adelante sí se valida.
        if (!empty($data['Sala']['personas'])) {
            foreach (Sala::problemas(Sala::desde($data)) as $problema) {
                $pendientes[] = ['tab' => 'sala', 'texto' => 'Sala: ' . $problema];
            }
        }

        // Las fichas que el docente ya declaró revisadas en el Resumen no
        // se reclaman: miró el estado y lo aceptó como está.
        return array_values(array_filter(
            $pendientes,
            static fn(array $p) => ($p['aceptable'] ?? true) === false
                || !CaseReview::revisada($data, $p['tab'])
        ));
    }

    /** Solo los textos, para un mensaje de una línea por ítem. */
    public static function pendingTexts(array $data): array
    {
        return array_map(static fn(array $p) => $p['texto'], self::pending($data));
    }

    /**
     * ¿Están todas las desviaciones en 0? Acepta las dos formas que usan
     * los módulos: anidada por onda/pico y plana por frecuencia.
     *
     * @param mixed $desviaciones
     */
    private static function allZero($desviaciones): bool
    {
        if (!is_array($desviaciones)) {
            return true;
        }
        foreach ($desviaciones as $valor) {
            if (is_array($valor)) {
                if (!self::allZero($valor)) {
                    return false;
                }
                continue;
            }
            if (abs((float) $valor) > 1e-9) {
                return false;
            }
        }
        return true;
    }
}
