<?php

declare(strict_types=1);

require_once __DIR__ . '/AbrReferences.php';
require_once __DIR__ . '/EcochgReferences.php';
require_once __DIR__ . '/CaseProfile.php';
require_once __DIR__ . '/BibliografiaPatologias.php';

/**
 * Toda la bibliografía de LabSim en un solo lugar, ordenada por examen, y
 * a qué número o comportamiento de la app corresponde cada cita.
 *
 * Se muestra en admin/bibliografia.php, solo al docente: el alumno lee un
 * examen, no una tabla normativa (ver AbrReferences).
 *
 * Las fichas del ABR y del ECochG NO se copian acá: siguen viviendo en
 * AbrReferences y EcochgReferences, que es donde las usa el resto del
 * backend. Acá se agrega lo que les faltaba --a qué corresponde cada una--
 * y las fuentes que estaban sueltas en comentarios del código (tamizaje
 * neonatal, normas, las del generador del ABR que no están en la planilla).
 *
 * Regla para agregar una cita: va con su ficha (cita, n, protocolo,
 * enlace) y con 'usa', la lista de lo que respalda en la app. Una cita que
 * no se pudo confirmar va con 'verificada' => false y la nota dice qué
 * falta; no se completa de memoria.
 */
final class Bibliografia
{
    /** Secciones en el orden en que se muestran. */
    public const SECCIONES = [
        'abr' => [
            'titulo' => 'ABR (potenciales de tronco)',
            'resumen' => 'Latencias y amplitudes normales por población, la función latencia-intensidad, el efecto de la tasa, la polaridad, el estímulo y la vía ósea. Las F son las 27 fuentes de la planilla de referencia; las A son las que usa el generador y no están en la planilla.',
        ],
        'ecochg' => [
            'titulo' => 'Electrococleografía',
            'resumen' => 'Límites de la razón PS/PA por electrodo, razón de áreas, separación entre polaridades y cuántos Ménière dan un ECochG normal.',
        ],
        'tamizaje' => [
            'titulo' => 'Tamizaje auditivo neonatal',
            'resumen' => 'Probabilidad de que un recién nacido pase TEOAE o AABR según las horas de vida, e indicadores de riesgo del paciente neonato.',
        ],
        'normas' => [
            'titulo' => 'Normas y clasificaciones',
            'resumen' => 'Normas y convenciones que usan el generador de casos, la ficha y el PDF: umbral esperable por edad, grado de hipoacusia, símbolos del audiograma.',
        ],
    ];

    /**
     * A qué corresponde cada fuente de la planilla ABR, más allá del set de
     * fábrica y de los sets publicados (eso se arma solo, ver usosAbr).
     * Sale de los comentarios del generador (src/abr/ABR_generator.py) y
     * de la ficha PDF.
     */
    public const USO_ABR = [
        'F01' => ['Polaridad de referencia: el normativo está medido en rarefacción, y las otras polaridades se expresan contra ella.'],
        'F09' => ['Ficha PDF del docente: caída del 10% de amplitud en el adulto mayor.'],
        'F10' => ['Polaridad: la rarefacción adelanta la onda I; en III y V no hay diferencia consistente.'],
        'F11' => ['Primera infancia (1-3 años): la onda V es la última en madurar; la población se interpola entre neonato y niño.'],
        'F13' => ['Tasa de estimulación: cuánto se alarga cada onda de 10 a 90/s (I 8%, III 11%, V 14%).'],
        'F18' => [
            'Vía ósea: el vibrador no entrega más de ~50 dB nHL (tope del equipo en la app).',
            'Vía ósea: los interpicos solo se publican cuando la onda I se ve, que es la excepción.',
        ],
        'F22' => ['Función latencia-intensidad: contraste de la serie de Hood (90 a 10 dB); cuánto se corre cada onda al bajar el nivel.'],
        'F23' => ['Tone burst: a 80 dB HL solo se identifica la onda V; la onda I del burst grave casi no existe.'],
        'F24' => ['Chirp contra click en los mismos sujetos. No publica anchos de onda: el afinamiento del chirp es derivado.'],
        'F26' => ['Función latencia-intensidad: forma de la curva (tramos sobre y bajo 50 dB) y desplazamiento de la onda I contra la V.'],
        'F27' => ['Polaridad: caída de amplitud de las ondas I y III al pasar a condensación.'],
    ];

    /** Fuentes del generador del ABR que no están en la planilla. */
    public const ABR_COMPLEMENTARIAS = [
        'A01' => [
            'cita' => 'Elberling C, Don M. Quality estimation of averaged auditory brainstem responses. Scand Audiol. 1984;13(3):187-197. doi:10.3109/01050398409043059.',
            'n' => 'Método',
            'protocolo' => 'Estimación de la relación señal/ruido del promedio (FSP) durante el registro.',
            'enlace' => 'https://doi.org/10.3109/01050398409043059',
            'usa' => [
                'FSP: cómo se calcula el valor esperado y con qué estadístico F se sortea el observado.',
                'Criterio de respuesta presente (FSP 3,1) y ruido del paciente que se despeja de los barridos del caso.',
            ],
        ],
        'A02' => [
            'cita' => 'Beattie RC. Normative wave V latency-intensity functions using the EARTONE 3A insert earphone and the Radioear B-71 bone vibrator. Scand Audiol. 1998;27(2):120-126.',
            'n' => 'Adultos normoyentes',
            'protocolo' => 'Vibrador óseo Radioear B-71.',
            'enlace' => 'Sin enlace',
            'verificada' => false,
            'nota' => 'En el código figura como "Beattie 1998 (Scand Audiol 27:120-6, B-71)". No se encontró el artículo en línea: el título está sin confirmar.',
            'usa' => ['Vía ósea: corrección de latencia por nivel (+0,3 ms a 40 dB, +0,4 a 30, +0,5 a 20, +0,8 a 10; nada desde 55).'],
        ],
        'A03' => [
            'cita' => 'Cobb KM, Stuart A. Neonate auditory brainstem responses to CE-Chirp and CE-Chirp octave band stimuli I y II. Ear Hear. 2016;37(6).',
            'n' => '168 neonatos sanos y 20 adultos jóvenes normoyentes',
            'protocolo' => 'CE-Chirp por vía aérea y ósea, y CE-Chirp por octavas; comparación con click y tone burst.',
            'enlace' => 'Sin enlace',
            'verificada' => false,
            'nota' => 'Autores, año y diseño confirmados; volumen y páginas a confirmar en el original.',
            'usa' => [
                'Umbral óseo contra aéreo según la edad: en el adulto la vía ósea lee ~15 dB más alto; en el lactante, casi igual (generador de perfil).',
                'Vía ósea del lactante: le sale más rápida que la aérea, al revés que en el adulto.',
            ],
        ],
        'A04' => [
            'cita' => 'Yang EY, Rupert AL, Moushegian G. A developmental study of bone conduction auditory brain stem response in infants. Ear Hear. 1987;8:244-251.',
            'n' => 'Lactantes',
            'protocolo' => 'ABR por vía ósea en distintas edades.',
            'enlace' => 'Sin enlace',
            'usa' => ['Vía ósea del lactante: más rápida que la aérea (cráneo sin suturar, oído medio con mesénquima).'],
        ],
        'A05' => [
            'cita' => 'Yang EY, Stuart A, Stenstrom R, Green WB. Test-retest variability of the auditory brainstem response to bone-conducted clicks in newborn infants. Audiology. 1993;32:89-94.',
            'n' => 'Recién nacidos',
            'protocolo' => 'Click por vía ósea, test-retest.',
            'enlace' => 'Sin enlace',
            'verificada' => false,
            'nota' => 'En el código figura como "Stuart et al. 1993". Esta es la serie de 1993 de ese grupo que más se parece; confirmar que sea la que se quiso citar.',
            'usa' => ['Vía ósea del lactante: más rápida que la aérea.'],
        ],
        'A06' => [
            'cita' => 'Seo YJ et al. Update on bone-conduction auditory brainstem responses: a review. J Audiol Otol. 2018;22(2):53-58. PMID 29471611.',
            'n' => 'Revisión',
            'protocolo' => 'ABR por vía ósea en lactantes, niños y adultos.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/29471611/',
            'usa' => ['Vía ósea: las ondas I y III rara vez se identifican; en la app salen más chicas y más anchas que por vía aérea.'],
        ],
    ];

    /** Tamizaje neonatal (NewbornScreening). Aportadas por el docente. */
    public const TAMIZAJE = [
        'N01' => [
            'cita' => 'Seehiranwong W, Saengrat P. Timing of newborn hearing screening effects on passing rates. Am J Perinatol. 2025. PMID 40759178.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/40759178/',
            'usa' => ['Tasas de pase de TEOAE y AABR por franja horaria.'],
        ],
        'N02' => [
            'cita' => 'Cheepcharoenrat C, Rerkasem A. Timing effect on TEOAE referral rates within and after 48 hours of birth. Int Arch Otorhinolaryngol. 2025. PMID 40735129.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/40735129/',
            'usa' => ['Tasas de "refiere" de TEOAE antes y después de las 48 horas.'],
        ],
        'N03' => [
            'cita' => 'OAE in universal hearing screening: which day after birth should we examine the newborns? PMID 14564092.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/14564092/',
            'usa' => ['Tasas de pase de TEOAE por día de vida.'],
        ],
        'N04' => [
            'cita' => 'Akinpelu OV et al. OAE in newborn hearing screening: systematic review of protocols. Int J Pediatr Otorhinolaryngol. 2014. PMID 24613088.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/24613088/',
            'usa' => ['Tasas de pase de TEOAE y momento del tamizaje.'],
        ],
        'N05' => [
            'cita' => 'Stewart DL et al. Universal newborn hearing screening with AABR: multisite investigation. J Perinatol. 2000. PMID 11190693.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/11190693/',
            'usa' => ['Tasas de pase del AABR.'],
        ],
        'N06' => [
            'cita' => 'Doyle KJ et al. Newborn hearing screening by OAE and AABR. Int J Pediatr Otorhinolaryngol. 1997;41(2):111-119.',
            'enlace' => 'Sin enlace',
            'usa' => ['Brecha entre TEOAE y AABR en las primeras horas.'],
        ],
        'N07' => [
            'cita' => 'Van Dyk M, Swanepoel DW, Hall JW 3rd. Outcomes with OAE and AABR in the first 48 h. Int J Pediatr Otorhinolaryngol. 2015. PMID 25921078.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/25921078/',
            'usa' => ['TEOAE refiere en más de la mitad de los sanos a pocas horas; el AABR pasa en ~85%.'],
        ],
        'N08' => [
            'cita' => 'Newborn hearing screening: early ear examination improves the pass rate. PMCID PMC10645159.',
            'enlace' => 'https://pmc.ncbi.nlm.nih.gov/articles/PMC10645159/',
            'usa' => ['Causa del "refiere" temprano: vérnix y líquido en el conducto, transitorio.'],
        ],
        'N09' => [
            'cita' => 'Lupoli et al. y Xiao et al., citados en Seehiranwong y Saengrat 2025 (N01).',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/40759178/',
            'usa' => ['Tasas de pase por franja horaria (series secundarias).'],
        ],
        'N10' => [
            'cita' => 'Nebraska DHHS, EHDI. Newborn Hearing Screening Protocol (basado en JCIH 2019).',
            'enlace' => 'Sin enlace',
            'usa' => ['Protocolo: tamizar lo más tarde posible antes del alta; "refiere" temprano = rescreening.'],
        ],
        'N11' => [
            'cita' => 'Joint Committee on Infant Hearing. Year 2019 Position Statement: Principles and Guidelines for Early Hearing Detection and Intervention Programs. J Early Hear Detect Interv. 2019;4(2):1-44.',
            'enlace' => 'https://doi.org/10.15142/fptk-b748',
            'usa' => [
                'Indicadores de riesgo del paciente neonato: peso < 1500 g, UCIN > 5 días, hiperbilirrubinemia con exanguinotransfusión, ototóxicos, infecciones congénitas.',
                'Peso y semanas mueven el tamizaje; las infecciones congénitas NO (son hipoacusia real, a veces tardía).',
                'Ficha PDF: línea "Indicadores de riesgo (JCIH 2019)".',
            ],
        ],
    ];

    /** Normas y clasificaciones. */
    public const NORMAS = [
        'S01' => [
            'cita' => 'ISO 7029:2017. Acoustics -- Statistical distribution of hearing thresholds related to age and gender.',
            'enlace' => 'https://www.iso.org/standard/42916.html',
            'usa' => [
                'Generador de casos: umbral mediano esperable por edad y sexo, que se suma al cuadro (pestaña Armado).',
                'Edad desde la que se aplica la desviación por edad (18 años).',
            ],
        ],
        'S02' => [
            'cita' => 'BIAP. Recomendación 02/1: Clasificación audiométrica de las deficiencias auditivas.',
            'enlace' => 'https://www.biap.org',
            'usa' => [
                'Grado de hipoacusia por promedio de 500, 1000, 2000 y 4000 Hz en vía aérea (normal hasta 20 dB HL).',
                'Generador: escala el cuadro para que el promedio caiga en el grado pedido.',
                'Ficha PDF: promedios BIAP aéreo y óseo.',
            ],
        ],
        'S03' => [
            'cita' => 'American Speech-Language-Hearing Association. Guidelines for audiometric symbols. ASHA. 1990;32(Suppl 2):25-30.',
            'enlace' => 'Sin enlace',
            'usa' => ['Símbolos del audiograma en el editor del caso y en el PDF.'],
        ],
    ];

    /**
     * Técnicas de examen tal como las enseña el docente, paso a paso. Son
     * la referencia contra la que se evalúa lo que hace el alumno (ver
     * 'usa'), así que se escriben como reglas que se puedan medir en el
     * registro de acciones.
     *
     * 'fuentes' queda vacío hasta contrastar la técnica con la literatura
     * científica y la normativa: con la misma regla que las citas, no se
     * completa de memoria.
     */
    public const TECNICAS = [
        'T01' => [
            'titulo' => 'Umbrales tonales por vía aérea',
            'resumen' => 'Técnica determinista y ordenada: siempre los mismos pasos, en el mismo orden.',
            'pasos' => [
                'Se parte por el oído mejor.',
                'Cada estímulo dura entre 1 y 2 segundos.',
                'Familiarización en 1 kHz: se parte en 40 dB HL. Si no responde, se sube de 10 en 10 dB hasta la primera respuesta.',
                'Desde la primera respuesta comienza la técnica: se dan dos estímulos en cada nivel y se baja de 10 en 10 dB mientras responda.',
                'Cuando en un nivel no responde, se sube de 5 en 5 dB para precisar el umbral: el umbral es el nivel que responde 2 de 3 o 3 de 5 veces.',
                'Orden de frecuencias: 1, 2, 3, 4, 6 y 8 kHz; luego 500, 250 y 125 Hz.',
                'Cada frecuencia nueva parte 10 dB sobre el umbral de la frecuencia anterior. Si no responde, se sube de 10 en 10 dB hasta la primera respuesta (familiarización) y luego sigue la técnica.',
                'Al terminar se repite 1 kHz para confirmar. Si da una diferencia mayor a 10 dB respecto de la primera vez, se repite todo el umbral.',
            ],
            'usa' => [
                'Indicador de efectividad de la toma de umbrales aéreos (pendiente): se evalúa con el registro de acciones del audiómetro.',
            ],
            'fuentes' => [],
            'nota' => 'Técnica tal como la enseña el docente. Falta contrastarla con la literatura científica y la normativa.',
        ],
    ];

    /**
     * Bibliografía de cada cuadro de CaseProfile::SCENARIOS, por clave.
     * Cada cita: eje, cita, enlace, respalda (qué valor), coincide
     * (si / parcial / no), nota y verificada. Un cuadro que no está acá es
     * una decisión de diseño sin bibliografía todavía. Las citas viven en
     * BibliografiaPatologias (son muchas para este archivo).
     */
    public const PATOLOGIAS = BibliografiaPatologias::CITAS;

    /** Nombre de cada eje de un cuadro, en el orden en que se muestran. */
    public const EJES = [
        'sn_shape' => 'Forma de la vía ósea (dB por frecuencia)',
        'sn_scale' => 'Escala de la forma ósea',
        'gap_shape' => 'Forma del gap aéreo-óseo (dB por frecuencia)',
        'gap_scale' => 'Escala del gap',
        'gap_max_db' => 'Techo del gap (dB)',
        'max_db' => 'Techo del promedio BIAP (dB HL)',
        'grados' => 'Grados posibles',
        'cce_pct' => 'Proporción coclear del daño (%)',
        'retro' => 'Patrón retrococlear del ABR',
        'z' => 'Timpanograma',
        'etf' => 'Función tubaria',
        'vemp' => 'VEMP',
        'ecochg' => 'Electrococleografía',
        'tinnitus' => 'Acúfeno',
        'conciencia' => 'Conciencia del problema (entrevista)',
        'lateralidad' => 'Sugerencia para el otro oído',
        'contralateral' => 'Oído contrario que exige el cuadro',
    ];

    /** Prefijo de la nota de una cita donde el generador difiere a propósito. */
    public const PREFIJO_DECISION = 'Decisión docente:';

    /**
     * Lo que el generador muestra SIEMPRE de una forma y en la realidad no
     * siempre es así: el Ménière con ECochG alterada, la EM con VEMP
     * alterado, el schwannoma con ABR alterado. El criterio es enseñar el
     * cuadro típico y patológico, y la fracción normal la da el docente en
     * la teoría. Para eso la tiene que tener a la vista, no enterrada en la
     * nota de una cita: la página la muestra arriba de cada cuadro y junta
     * en una sección.
     *
     * Sale de las citas cuya nota empieza con PREFIJO_DECISION, así que no
     * hay una segunda lista que mantener.
     *
     * @return array<string, array<int, array{eje:string, texto:string, cita:string}>>
     */
    public static function decisiones(): array
    {
        $out = [];
        foreach (self::PATOLOGIAS as $clave => $citas) {
            foreach ($citas as $c) {
                $nota = (string) ($c['nota'] ?? '');
                if (strpos($nota, self::PREFIJO_DECISION) !== 0) {
                    continue;
                }
                $out[$clave][] = [
                    'eje' => (string) $c['eje'],
                    'texto' => trim(substr($nota, strlen(self::PREFIJO_DECISION))),
                    'cita' => (string) $c['cita'],
                ];
            }
        }
        return $out;
    }

    /**
     * Los cuadros del generador (CaseProfile::SCENARIOS) con el porqué de
     * cada eje.
     *
     * El porqué NO se copia: se lee de los comentarios que tiene cada
     * cuadro en CaseProfile.php, que es donde se escribe al tomar la
     * decisión. Un comentario va con los ejes de la línea que lo sigue
     * ('grados', 'max_db' y 'gap_max_db' suelen ir juntos porque se
     * deciden juntos). Así lo que ve el docente es siempre lo que hace el
     * generador, sin una segunda copia que se quede vieja.
     *
     * Devuelve ['categorias' => [cat => intro], 'cuadros' => [clave => [
     *   'label', 'categoria', 'filas' => [['ejes' => [...], 'porque' => '']]]]].
     */
    public static function cuadros(): array
    {
        $lineas = file(__DIR__ . '/CaseProfile.php', FILE_IGNORE_NEW_LINES) ?: [];
        $categorias = [];
        $comentarios = [];
        $introGrupo = [];
        $actual = null;
        $pendiente = [];
        $dentro = false;
        foreach ($lineas as $l) {
            if (!$dentro) {
                $dentro = strpos($l, 'public const SCENARIOS = [') !== false;
                continue;
            }
            if (preg_match('/^    \];/', $l)) {
                break;
            }
            if (preg_match('/^ {8}\/\/ ?(.*)$/', $l, $m)) {
                if (strpos($m[1], '---') === 0) {
                    $introGrupo = [];
                } else {
                    $introGrupo[] = trim($m[1]);
                }
                continue;
            }
            if (preg_match("/^ {8}'([a-z0-9_]+)' => \\[$/", $l, $m)) {
                $actual = $m[1];
                $comentarios[$actual] = [];
                $pendiente = [];
                if ($introGrupo) {
                    $categoria = CaseProfile::SCENARIOS[$actual]['categoria'] ?? '';
                    $categorias[$categoria] = trim(($categorias[$categoria] ?? '') . ' ' . implode(' ', $introGrupo));
                    $introGrupo = [];
                }
                continue;
            }
            if ($actual === null) {
                continue;
            }
            if (preg_match('/^ {12}\/\/ ?(.*)$/', $l, $m)) {
                $pendiente[] = trim($m[1]);
                continue;
            }
            if (preg_match("/^ {12}'/", $l) && preg_match_all("/(?:^ {12}|, )'([a-z_]+)' =>/", $l, $mm)) {
                $comentarios[$actual][] = ['ejes' => $mm[1], 'porque' => implode(' ', $pendiente)];
                $pendiente = [];
            }
        }

        $cuadros = [];
        foreach (CaseProfile::SCENARIOS as $clave => $sc) {
            $filas = [];
            $vistos = [];
            foreach ($comentarios[$clave] ?? [] as $fila) {
                $ejes = array_values(array_filter($fila['ejes'], static function ($e) use ($sc) {
                    return isset(self::EJES[$e]) && array_key_exists($e, $sc);
                }));
                if ($ejes === [] && $fila['porque'] === '') {
                    continue;
                }
                if ($ejes === []) {
                    // Comentario sobre el label o la categoría: es el porqué
                    // del cuadro entero, va con el primer eje que siga.
                    $filas[] = ['ejes' => [], 'porque' => $fila['porque']];
                    continue;
                }
                $filas[] = ['ejes' => $ejes, 'porque' => $fila['porque']];
                $vistos = array_merge($vistos, $ejes);
            }
            // Los ejes sin comentario van juntos al final, en una sola fila:
            // son los valores que no necesitaron explicación.
            $sinPorque = [];
            foreach ($filas as $i => $fila) {
                if ($fila['porque'] === '') {
                    $sinPorque = array_merge($sinPorque, $fila['ejes']);
                    unset($filas[$i]);
                }
            }
            foreach (array_keys(self::EJES) as $eje) {
                if (array_key_exists($eje, $sc) && !in_array($eje, $vistos, true)) {
                    $sinPorque[] = $eje;
                }
            }
            $filas = array_values($filas);
            if ($sinPorque) {
                $orden = array_flip(array_keys(self::EJES));
                usort($sinPorque, static function ($a, $b) use ($orden) {
                    return $orden[$a] <=> $orden[$b];
                });
                $filas[] = ['ejes' => $sinPorque, 'porque' => ''];
            }
            $cuadros[$clave] = [
                'label' => $sc['label'],
                'categoria' => $sc['categoria'],
                'filas' => $filas,
            ];
        }
        return ['categorias' => $categorias, 'cuadros' => $cuadros];
    }

    /** Valor de un eje en texto corto: "125:5 250:5 ...", "0.5-1.2", etc. */
    public static function valorEje($v, bool $opciones = false): string
    {
        if ($v === null) {
            return '--';
        }
        if (is_bool($v)) {
            return $v ? 'sí' : 'no';
        }
        if (!is_array($v)) {
            return (string) $v;
        }
        if ($v === []) {
            return 'ninguno';
        }
        $esLista = array_keys($v) === range(0, count($v) - 1);
        if ($esLista) {
            // Dos números son un rango [mín, máx], salvo que el que llama
            // diga que es una lista de opciones (frecuencias del acúfeno).
            $num = !$opciones && count($v) === 2 && is_numeric($v[0]) && is_numeric($v[1]);
            if ($num) {
                return $v[0] == $v[1] ? (string) $v[0] : $v[0] . '-' . $v[1];
            }
            return implode(', ', array_map([self::class, 'valorEje'], $v));
        }
        $partes = [];
        foreach ($v as $k => $x) {
            if (is_int($k) && $k >= 125) {
                $partes[] = ($k >= 1000 ? ($k / 1000) . 'k' : $k) . ':' . self::valorEje($x);
            } else {
                $nombre = $k === 'lat_ms' ? 'latencia +ms' : $k;
                $partes[] = $nombre . ' ' . self::valorEje($x, in_array($k, ['frecuencia', 'ruido', 'type'], true));
            }
        }
        return implode(is_int(array_key_first($v)) ? ' ' : ' · ', $partes);
    }

    /**
     * Fuentes de una sección, cada una con su ficha y 'usa' (lista de a
     * qué corresponde). En el ABR, las de la planilla que no respaldan
     * ningún número quedan aparte (ver sinUsoAbr).
     */
    public static function fuentes(string $seccion): array
    {
        switch ($seccion) {
            case 'abr':
                $usos = self::usosAbr();
                $out = [];
                foreach (self::fichasAbr() as $fid => $f) {
                    if (!empty($usos[$fid])) {
                        $out[$fid] = $f + ['usa' => $usos[$fid]];
                    }
                }
                return $out + self::ABR_COMPLEMENTARIAS;
            case 'ecochg':
                $out = [];
                foreach (EcochgReferences::FUENTES as $fid => $f) {
                    $usa = [];
                    foreach (EcochgReferences::LIMITES as $lim) {
                        if (in_array($fid, $lim['fuentes'], true)) {
                            $usa[] = $lim['label'] . ' (' . $lim['valor'] . ').';
                        }
                    }
                    $out[$fid] = $f + ['usa' => $usa];
                }
                return $out;
            case 'tamizaje':
                return self::TAMIZAJE;
            case 'normas':
                return self::NORMAS;
        }
        return [];
    }

    /** Fuentes de la planilla ABR que no respaldan ningún número de la app. */
    public static function sinUsoAbr(): array
    {
        $usos = self::usosAbr();
        $out = [];
        foreach (self::fichasAbr() as $fid => $f) {
            if (empty($usos[$fid])) {
                $out[$fid] = $f;
            }
        }
        return $out;
    }

    private static function fichasAbr(): array
    {
        $fichas = AbrReferences::FUENTES;
        ksort($fichas);
        return $fichas;
    }

    /**
     * A qué corresponde cada fuente de la planilla: el anclaje del set de
     * fábrica y los sets publicados se leen de AbrReferences (así no se
     * desincronizan), y se les suma USO_ABR.
     */
    private static function usosAbr(): array
    {
        $poblacion = [
            'adult_male' => 'adulto hombre', 'adult_female' => 'adulto mujer',
            'child' => 'niño (3-17)', 'toddler' => 'primera infancia (1-3)',
            'neonate' => 'neonato', 'elderly_male' => 'adulto mayor hombre',
            'elderly_female' => 'adulto mayor mujer',
        ];
        $medida = ['lat' => 'Latencias', 'amp' => 'Amplitudes'];

        $anclas = [];
        foreach (AbrReferences::ANCLAJE as $pop => $porMedida) {
            foreach ($porMedida as $que => $fid) {
                $anclas[$fid][$que][] = $poblacion[$pop] ?? $pop;
            }
        }
        $usos = [];
        foreach ($anclas as $fid => $porMedida) {
            foreach ($porMedida as $que => $pops) {
                $usos[$fid][] = $medida[$que] . ' normales del set de fábrica: '
                    . implode(', ', array_unique($pops)) . '.';
            }
        }
        foreach (AbrReferences::SETS as $set) {
            $usos[$set['fuente']][] = 'Set publicado "' . $set['label'] . '" (selector de autor del caso).';
        }
        foreach (self::USO_ABR as $fid => $lista) {
            foreach ($lista as $uso) {
                $usos[$fid][] = $uso;
            }
        }
        unset($usos['calculada']);
        return $usos;
    }
}
