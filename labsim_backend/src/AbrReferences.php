<?php

declare(strict_types=1);

/**
 * Bibliografía normativa del ABR: de dónde sale cada número y qué sets de
 * autor trae la app de fábrica.
 *
 * Vive en el BACKEND y no en el repo del cliente porque el docente no ve el
 * proyecto base: ve esta administración. La planilla completa (483 filas,
 * 27 fuentes) está en resources/normativa/ y se descarga desde
 * admin/normativas.php.
 *
 * Los sets de acá son de solo lectura: son lo que publicó cada serie, no
 * una opinión editable. El docente que quiera otros valores crea su propio
 * set en normativas.php -- los dos conviven en el mismo selector del caso.
 *
 * Un set NO tiene que estar completo. El caso resuelve onda por onda: lo
 * que el autor no define cae en el default de la app (ver
 * public/js/case/abr.js, resolveBaseline). Por eso acá solo se carga lo que
 * la serie publica de verdad, y las celdas que no publicó quedan afuera en
 * vez de rellenarse con otra fuente.
 */
final class AbrReferences
{
    /** Planilla de referencia, relativa a la raíz del backend. */
    public const PLANILLA = 'resources/normativa/ABR_valores_referencia_latencias_interpico.xlsx';

    /** Ficha de cada fuente citada. */
    public const FUENTES = [
        'F01' => [
            'cita' => 'Sanfins MD, Santillo MEA, Martins MFP, Silva DLdS, Gos E, Skarzynski PH, Hall JW III. The Influence of Sex, Ear, and Age on Auditory Brainstem Response. Diagnostics. 2026;16(7):971.',
            'n' => '244 sujetos (134 H / 110 M), 3-79 anios',
            'protocolo' => 'Click 0.1 ms rarefaccion, 80 dB nHL, 19.3/s, ER-3A, Fz-mastoides ipsi, filtro 0.1-3 kHz, 2x2000 barridos',
            'enlace' => 'https://doi.org/10.3390/diagnostics16070971',
        ],
        'F04' => [
            'cita' => 'Chalak S, Kale A, Deshpande VK, Biswas DA. Establishment of Normative Data for Monaural Recordings of Auditory Brainstem Response. J Clin Diagn Res. 2013.',
            'n' => '40 ninios, edad media 7.62 +/- 2.39 anios',
            'protocolo' => 'Click monoaural con enmascaramiento contralateral, 70 dB nHL, 11.1/s, filtro 100/250-5000 Hz, 2000 barridos',
            'enlace' => 'https://doi.org/10.7860/JCDR/2013/6768.3730',
        ],
        'F07' => [
            'cita' => 'Auditory Brainstem Response: reference-values for age (neonatos por edad gestacional).',
            'n' => '40 neonatos por grupo de edad gestacional',
            'protocolo' => 'Click; grupos de 35-36 y 37-38 semanas',
            'enlace' => 'https://www.researchgate.net/publication/263015732',
        ],
        'F09' => [
            'cita' => 'Jerger J, Hall J. Effects of age and sex on auditory brainstem response. Arch Otolaryngol. 1980;106(7):387-391.',
            'n' => '319 sujetos (182 H / 137 M), 98 normoyentes',
            'protocolo' => 'Click; latencia y amplitud de onda V por edad y sexo',
            'enlace' => 'https://doi.org/10.1001/archotol.1980.00790310011003',
        ],
        'F10' => [
            'cita' => 'Stockard JE, Stockard JJ, Westmoreland BF, Corfits JL. Brainstem auditory-evoked responses: normal variation as a function of stimulus and subject characteristics. Arch Neurol. 1979.',
            'n' => '64 adultos + 77 neonatos de termino',
            'protocolo' => 'Click rarefaccion vs condensacion, 30-70 dB SL/HL, 10 y 80 clicks/s',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/508145/',
        ],
        'F13' => [
            'cita' => 'Jiang ZD et al. The effect of click rate on latency and interpeak interval of the brain-stem auditory evoked potentials in children from birth to 6 years. Electroencephalogr Clin Neurophysiol. 1991.',
            'n' => '80 ninios (0-6 anios) + 21 adultos',
            'protocolo' => 'Click a 10, 30, 50, 70 y 90/s; 70, 40 y 20 dB HL/SL',
            'enlace' => 'https://www.sciencedirect.com/science/article/abs/pii/016855979190044X',
        ],
        'F18' => [
            'cita' => 'Normalization of Bone Conduction Auditory Brainstem Evoked Responses in Normal Hearing Individuals. J Int Adv Otol.',
            'n' => '100 sujetos (50 H / 50 M), 10-60 anios, 200 oidos',
            'protocolo' => 'ABR por via osea a 50, 30 y 10 dB nHL (el vibrador no entrega mas), 5 grupos etarios',
            'enlace' => 'https://advancedotology.org//en/normalization-of-bone-conduction-auditory-brainstem-evoked-responses-in-normal-hearing-individuals-131309',
        ],
        'F21' => [
            'cita' => 'Aguilar-Madrid G et al. Latencias de los potenciales evocados auditivos de tronco cerebral en trabajadores. 2015. PMID 26960049.',
            'n' => '196 sujetos (107 H / 89 M), 16-65 anios',
            'protocolo' => 'Nicolet Viking Quest, 2000 clicks de rarefaccion, 33/s, ventana 10 ms, camara sonoamortiguada',
            'enlace' => 'https://www.redalyc.org/pdf/4577/457745149012.pdf',
        ],
        'F24' => [
            'cita' => 'Cargnelutti M, Coser PL, Biaggio EP. LS CE-Chirp vs. Click in the neuroaudiological diagnosis by ABR. Braz J Otorhinolaryngol. 2017;83(3):313-317.',
            'n' => '30 sujetos / 60 oidos normoyentes',
            'protocolo' => '85 dB nHL, polaridad alternante, 17.1/s, filtro 100-3000 Hz; click y chirp en los MISMOS sujetos',
            'enlace' => 'https://doi.org/10.1016/j.bjorl.2016.04.018',
        ],
        'F25' => [
            'cita' => 'Rosa LAC et al. Auditory Brainstem Response: reference-values for age. CoDAS. 2014.',
            'n' => '80 lactantes por edad posconcepcional',
            'protocolo' => 'Click; grupos de 35-36, 37-38, 39-40 semanas y 6 meses',
            'enlace' => 'https://doi.org/10.1590/2317-1782/2014469in',
        ],
        'F26' => [
            'cita' => 'Hood LJ. Clinical Applications of the Auditory Brainstem Response. Singular Publishing Group. Tabla 2-3.',
            'n' => 'Mujeres normoyentes 20-30 anios; n de 2 a 20 segun celda',
            'protocolo' => 'Click, serie completa de 90 a 20 dB nHL, ondas I a VI e interpicos',
            'enlace' => 'Transcripcion aportada por el usuario; verificar contra el libro impreso',
        ],
        'F27' => [
            'cita' => 'Da Silva Nunes C, Gentile Matas C. Audiometria de tronco encefalico utilizando diferentes polaridades de presentacion del estimulo acustico. Rev Chil Fonoaudiol. 2005;6(2).',
            'n' => '50 adultos (25 H / 25 M), 18-40 anios, 100 oidos',
            'protocolo' => 'Bio-Logic Traveler Express, click 0.1 ms, 11.1/s, 80 dB HL, 2000 estimulos con replica',
            'enlace' => 'Revista Chilena de Fonoaudiologia, vol. 6, num. 2, 2005',
        ],
    ];

    /**
     * Qué fuente ancla cada población en el set de fábrica ("LabSim").
     * Lo que no está acá --ondas II, IV, VI, VII, microfónica, amplitudes
     * pediátricas y toda la vía ósea-- no lo publica ninguna serie y lo
     * calcula el generador a partir de estas.
     */
    public const ANCLAJE = [
        'adult_male'   => ['lat' => 'F01', 'amp' => 'F27'],
        'adult_female' => ['lat' => 'F01', 'amp' => 'F27'],
        'child'        => ['lat' => 'F04', 'amp' => 'calculada'],
        'toddler'        => ['lat' => 'calculada', 'amp' => 'calculada'],
        'neonate'      => ['lat' => 'F25', 'amp' => 'calculada'],
        'elderly_male'   => ['lat' => 'F21', 'amp' => 'F09'],
        'elderly_female' => ['lat' => 'F21', 'amp' => 'F09'],
    ];

    /**
     * Sets de autor que trae la app. Solo latencias y amplitudes que la
     * serie publica: lo demás lo completa el default.
     */
    public const SETS = [
        'sanfins_2026' => [
            'label' => 'Sanfins et al. 2026 (n=244, ER-3A, 80 dB nHL)',
            'fuente' => 'F01',
            'nota' => 'La serie no separa amplitud por sexo: publica onda I 0.36 y onda V 0.50 µV para el conjunto. La onda III no trae amplitud.',
            'populations' => [
                'adult_male' => [
                    'I' => ['lat' => 1.47, 'amp' => 0.36],
                    'III' => ['lat' => 3.75],
                    'V' => ['lat' => 5.68, 'amp' => 0.50],
                ],
                'adult_female' => [
                    'I' => ['lat' => 1.46, 'amp' => 0.36],
                    'III' => ['lat' => 3.65],
                    'V' => ['lat' => 5.54, 'amp' => 0.50],
                ],
            ],
        ],
        'aguilar_2015' => [
            'label' => 'Aguilar-Madrid et al. 2015 (n=196, supraaural, 33/s)',
            'fuente' => 'F21',
            'nota' => 'Tasa de 33/s y auricular supraaural: las latencias salen más largas que con inserción a 19/s. No publica amplitudes. El adulto es el promedio de sus tres bandas bajo 45 años; el adulto mayor, la banda de 45 o más (su onda III de hombre-izquierdo, 3.07 ms, contradice su propio interpico I-III y se reemplaza por 4.06).',
            'populations' => [
                'adult_male'   => ['I' => ['lat' => 1.74], 'III' => ['lat' => 3.91], 'V' => ['lat' => 5.86]],
                'adult_female' => ['I' => ['lat' => 1.70], 'III' => ['lat' => 3.81], 'V' => ['lat' => 5.70]],
                'elderly_male'   => ['I' => ['lat' => 1.83], 'III' => ['lat' => 3.98], 'V' => ['lat' => 5.85]],
                'elderly_female' => ['I' => ['lat' => 1.84], 'III' => ['lat' => 3.84], 'V' => ['lat' => 5.84]],
            ],
        ],
        'hood' => [
            'label' => 'Hood — Clinical Applications of the ABR (mujeres 20-30)',
            'fuente' => 'F26',
            'nota' => 'Tabla de texto de referencia, con n de 2 a 20 según la celda. Solo mujeres adultas. Es la fuente de la que sale la forma de la función latencia-intensidad que usa el generador.',
            'populations' => [
                'adult_female' => ['I' => ['lat' => 1.58], 'III' => ['lat' => 3.68], 'V' => ['lat' => 5.47]],
            ],
        ],
        'pediatrico' => [
            'label' => 'Pediátrico: Chalak 2013 (niño) y Rosa 2014 (neonato)',
            'fuente' => 'F04',
            'nota' => 'Chalak mide a 70 dB nHL, así que sus latencias son ~0.12 ms más largas que a 80; acá van tal como las publica. Rosa da el neonato de 39-40 semanas y no publica su onda V.',
            'populations' => [
                'child'   => ['I' => ['lat' => 1.66], 'III' => ['lat' => 3.67], 'V' => ['lat' => 5.62]],
                'neonate' => ['I' => ['lat' => 1.79], 'III' => ['lat' => 4.56]],
            ],
        ],
    ];

    /**
     * El default de la app en forma onda => ['lat'=>, 'amp'=>].
     *
     * La tabla vive en CaseWaveforms::CLICK_BASE (copia del normativo del
     * cliente) y acá solo se le cambia la forma. Antes había tres copias
     * más --normativas.php, case_create y public/js/case/abr.js-- y la del
     * JS se quedó vieja al reanclar el normativo: los casos se armaban
     * contra una tabla que la app ya no usaba.
     */
    public static function defaults(): array
    {
        require_once __DIR__ . '/CaseWaveforms.php';
        $out = [];
        foreach (CaseWaveforms::CLICK_BASE as $pop => $ondas) {
            foreach ($ondas as $onda => $par) {
                $out[$pop][$onda] = ['lat' => (float) $par[0], 'amp' => (float) $par[1]];
            }
        }
        return $out;
    }

    /**
     * El baseline que realmente se usó: el del set, completado con el
     * default de la app donde esa serie no publica nada. Es la misma
     * resolución que hace public/js/case/abr.js al armar el caso, campo
     * por campo, y sirve para dejar registrado con qué se construyó.
     *
     * @return array<string,array<string,float>> onda => ['lat'=>, 'amp'=>]
     */
    public static function resolve(string $setId, string $pop): array
    {
        require_once __DIR__ . '/CaseWaveforms.php';
        $base = CaseWaveforms::CLICK_BASE[$pop] ?? CaseWaveforms::CLICK_BASE['adult_female'];
        $set = self::SETS[$setId]['populations'][$pop] ?? [];
        $out = [];
        foreach (['I', 'III', 'V'] as $onda) {
            $out[$onda] = [
                'lat' => isset($set[$onda]['lat']) ? (float) $set[$onda]['lat'] : (float) $base[$onda][0],
                'amp' => isset($set[$onda]['amp']) ? (float) $set[$onda]['amp'] : (float) $base[$onda][1],
            ];
        }
        return $out;
    }

    /** Etiqueta del set, o null si no está registrado. */
    public static function label(string $setId, array $propios = []): ?string
    {
        if (isset(self::SETS[$setId]['label'])) {
            return (string) self::SETS[$setId]['label'];
        }
        if (isset($propios[$setId]['label'])) {
            return (string) $propios[$setId]['label'];
        }
        return null;
    }

    /** Ruta absoluta de la planilla, o null si no está desplegada. */
    public static function planilla(): ?string
    {
        $ruta = dirname(__DIR__) . '/' . self::PLANILLA;
        return is_file($ruta) ? $ruta : null;
    }

    /**
     * Catálogo para el selector del caso: los sets bibliográficos primero y
     * después los del docente. Un set propio con el mismo id pisa al de
     * fábrica -- así se puede corregir uno sin tocar código.
     */
    public static function catalog(array $propios): array
    {
        $out = [];
        foreach (self::SETS as $id => $set) {
            $out[$id] = [
                'label' => $set['label'],
                'populations' => $set['populations'],
                'bibliografico' => true,
                'fuente' => $set['fuente'],
            ];
        }
        foreach ($propios as $id => $set) {
            $out[$id] = $set;
        }
        return $out;
    }
}
