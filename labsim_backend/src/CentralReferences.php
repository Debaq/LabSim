<?php

declare(strict_types=1);

/**
 * Bibliografía de los potenciales de latencia media y tardía (MLR, CAEP,
 * P300, MMN): de dónde sale cada número que usa el cliente
 * (src/abr/cortical.py y src/abr/Cortical_generator.py) y qué respalda cada
 * cuadro central del generador (CaseProfile::CENTRAL_SCENARIOS).
 *
 * Mismo criterio que EcochgReferences: vive en el BACKEND porque el docente
 * no ve el repo del cliente, se muestra solo a él (admin/bibliografia.php) y
 * los números son ESPEJO de los del cliente, no una configuración. Lo que
 * ninguna fuente accesible publica va marcado 'calculado' con su porqué.
 *
 * Verificado contra PubMed/Crossref el 2026-10-20 (Sharma 2002 y Duncan
 * 2009 con el texto completo; el resto por el resumen). De los libros (Hall,
 * Picton) solo se confirmó la edición, no el contenido: no respaldan
 * ningún número.
 */
final class CentralReferences
{
    /** Ficha de cada fuente citada. */
    public const FUENTES = [
        'C01' => [
            'cita' => 'Duncan CC, Barry RJ, Connolly JF, Fischer C, Michie PT, Näätänen R, Polich J, Reinvang I, Van Petten C. Event-related potentials in clinical research: guidelines for eliciting, recording, and quantifying mismatch negativity, P300, and N400. Clin Neurophysiol. 2009;120(11):1883-1908. PMID 19796989.',
            'n' => 'Guía de consenso, sin muestra propia',
            'protocolo' => 'Tablas de protocolo de MMN y P300: rechazo ±100 µV, ≥150 desviantes por tipo para la MMN, ≥36 ensayos por categoría para la P300, raros 10-20 %.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/19796989/',
        ],
        'C02' => [
            'cita' => 'Kraus N, McGee T. Clinical implications of primary and nonprimary pathway contributions to the middle latency response generating system. Ear Hear. 1993;14(1):36-48. PMID 8444337.',
            'n' => 'Revisión con datos animales y clínicos',
            'protocolo' => 'Generadores del MLR: vía primaria (lemniscal) y no primaria, sensible al sueño, la sedación y la maduración.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/8444337/',
        ],
        'C03' => [
            'cita' => 'Lightfoot G, Kennedy V. Cortical electric response audiometry hearing threshold estimation: accuracy, speed, and the effects of stimulus presentation features. Ear Hear. 2006;27(5):443-456. PMID 16957496.',
            'n' => '24 adultos voluntarios',
            'protocolo' => 'Tonos de 1, 3 y 8 kHz, N1-P2; umbral estimado con error medio de 6,5 dB.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/16957496/',
        ],
        'C04' => [
            'cita' => 'Martin BA, Tremblay KL, Korczak P. Speech evoked potentials: from the laboratory to the clinic. Ear Hear. 2008;29(3):285-313. PMID 18453883.',
            'n' => 'Revisión',
            'protocolo' => 'Potenciales corticales con habla: P1-N1-P2, ACC y MMN como medida de detección y discriminación.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/18453883/',
        ],
        'C05' => [
            'cita' => 'Musiek FE, Charette L, Kelly T, Lee WW, Musiek E. Hit and false-positive rates for the middle latency response in patients with central nervous system involvement. J Am Acad Audiol. 1999;10(3):124-132. doi:10.1055/s-0042-1748472.',
            'n' => '26 pacientes con lesión del SNC y 26 controles pareados por edad y audición',
            'protocolo' => 'Na y Pa en C3 y C4 estimulando cada oído; la diferencia porcentual de amplitud entre lados fue la medida más sensible y específica, mejor que la latencia.',
            'enlace' => 'https://doi.org/10.1055/s-0042-1748472',
        ],
        'C06' => [
            'cita' => 'Musiek FE, Nagle S. The middle latency response: a review of findings in various central nervous system lesions. J Am Acad Audiol. 2018;29(9):855-867. PMID 30278870.',
            'n' => 'Revisión de estudios y casos con lesión central documentada',
            'protocolo' => 'El MLR es razonablemente sensible y específico para el compromiso neurológico central.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/30278870/',
        ],
        'C07' => [
            'cita' => 'Polich J. Updating P300: an integrative theory of P3a and P3b. Clin Neurophysiol. 2007;118(10):2128-2148. PMID 17573239.',
            'n' => 'Revisión teórica',
            'protocolo' => 'P3a frontocentral ante lo novedoso; P3b parietal ante el blanco atendido; la amplitud depende de la probabilidad del blanco.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/17573239/',
        ],
        'C08' => [
            'cita' => 'Polich J, Howard L, Starr A. Effects of age on the P300 component of the event-related potential from auditory stimuli: peak definition, variation, and measurement. J Gerontol. 1985;40(6):721-726. PMID 4056328.',
            'n' => 'Jóvenes de 5 a 15 años y adultos de 20 a 86 años',
            'protocolo' => 'Oddball auditivo; la latencia de la P300 aumenta unos 65 ms entre los 20 y los 70 años.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/4056328/',
        ],
        'C09' => [
            'cita' => 'Sharma A, Dorman MF, Spahr AJ. A sensitive period for the development of the central auditory system in children with cochlear implants: implications for age of implantation. Ear Hear. 2002;23(6):532-539. PMID 12476090.',
            'n' => '136 normoyentes de 0,1 a 20 años y 104 niños con implante coclear',
            'protocolo' => '/ba/ de 90 ms, Cz contra mastoides, 0,1-100 Hz, rechazo ±100 µV. Latencia P1 = 155,6 - 32,746 ln(edad). Implante hasta los 3,5 años: P1 normal; de 3,6 a 6,5: variable; después de los 7: anormal.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/12476090/',
        ],
        'C10' => [
            'cita' => 'Weihing J, Schochat E, Musiek F. Ear and electrode effects reduce within-group variability in middle latency response amplitude measures. Int J Audiol. 2012;51(5):405-412. PMID 22404293.',
            'n' => '155 niños normoyentes',
            'protocolo' => 'Na-Pa en C3 y C4 con cada oído: las diferencias relativas (efecto electrodo, efecto oído) varían menos que las amplitudes absolutas.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/22404293/',
        ],
        'C11' => [
            'cita' => 'Galambos R, Makeig S, Talmachoff PJ. A 40-Hz auditory potential recorded from the human scalp. Proc Natl Acad Sci U S A. 1981;78(4):2643-2647. PMID 6941317.',
            'n' => 'Adultos normoyentes',
            'protocolo' => 'Respuesta de 40 Hz: los potenciales de latencia media se superponen al estimular cada 25 ms.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/6941317/',
        ],
        'C12' => [
            'cita' => 'Pialarissi PR, Almeida FS, Camanducaia LCBM, Jorge JJ Jr. Middle-latency auditory responses in neurological diseases. Braz J Otorhinolaryngol. 2007;73(4):540-548. PMID 17923926.',
            'n' => 'Grupo normal estandarizado previamente por los autores (n no informado en este trabajo)',
            'protocolo' => 'Click alternado a 7/s, 1000 barridos, 10-1200 Hz, activos sobre cada hemisferio contra mastoides. Normales: Na 17,9; Pa 29,4; Nb 41,4; Pb 51,4 ms.',
            'enlace' => 'https://pmc.ncbi.nlm.nih.gov/articles/PMC9443762/',
        ],
        'C13' => [
            'cita' => 'Eddins AC, Peterson JR. Time-intensity trading in the late auditory evoked potential. J Speech Lang Hear Res. 1999;42(3):516-525. PMID 10391619.',
            'n' => '5 adultos jóvenes normoyentes',
            'protocolo' => 'Tonos de 1 y 4 kHz de 8, 16, 32, 64 y 128 ms. Umbral del N1-P2: 24 dB menos a 1 kHz y 18 dB a 4 kHz de 8 a 128 ms (-4 a -6 dB por duplicación); a más duración, N1 y P2 más tempranos y más grandes.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/10391619/',
        ],
    ];

    /**
     * Cada número que usa el cliente y de dónde sale. 'fuentes' vacío =
     * calculado; la nota dice cómo.
     */
    public const LIMITES = [
        'mlr_latencias' => [
            'label' => 'Latencias del MLR en el adulto (Na, Pa, Nb, Pb)',
            'valor' => '18, 30, 41 y 52 ms',
            'fuentes' => ['C12'],
            'nota' => 'Medias de la serie normal de Pialarissi 2007 (17,9 / 29,4 / 41,4 / 51,4 ms). La serie no publica desvío: el ±2 DE de la tabla (2-4 ms) es calculado.',
        ],
        'efecto_electrodo' => [
            'label' => 'Efecto electrodo y efecto oído (diferencia de Na-Pa)',
            'valor' => '50 %',
            'fuentes' => [],
            'nota' => 'Calculado: es el criterio del docente. Musiek 1999 (C05) y Weihing 2012 (C10) leen la diferencia porcentual de amplitud entre lados porque varía menos que la amplitud absoluta, pero el corte publicado no se pudo verificar en el texto.',
        ],
        'p1_edad' => [
            'label' => 'Latencia de la P1 según la edad',
            'valor' => '155,6 - 32,746 ln(edad) ms',
            'fuentes' => ['C09'],
            'nota' => 'Regresión de Sharma 2002 sobre normoyentes de 0,1 a 20 años; fuera de ese tramo se usa el borde. El límite superior (media + 24 %) es calculado: el trabajo dibuja el intervalo de 95 % pero no lo publica como fórmula.',
        ],
        'p300_edad' => [
            'label' => 'Latencia de la P300 según la edad',
            'valor' => '300 ms + 1,3 ms por año desde los 20',
            'fuentes' => ['C08', 'C01'],
            'nota' => 'Polich 1985: unos 65 ms más entre los 20 y los 70 años; Duncan 2009: pico típico entre 300 y 400 ms. El desvío de 20 ms es calculado.',
        ],
        'mmn' => [
            'label' => 'MMN en la onda de diferencia',
            'valor' => '150-250 ms, 0,5-5 µV',
            'fuentes' => ['C01'],
            'nota' => 'Tabla de cuantificación de Duncan 2009; la latencia baja cuanto mayor es la diferencia entre estímulos, que es como la modela el cliente.',
        ],
        'mmn_desviantes' => [
            'label' => 'Desviantes para una MMN confiable',
            'valor' => '≥ 150',
            'fuentes' => ['C01'],
            'nota' => 'Duncan 2009, al menos 150 desviantes de cada tipo. Con el 20 % de raros son unos 750 barridos.',
        ],
        'rechazo' => [
            'label' => 'Rechazo de artefactos de los tardíos',
            'valor' => '±100 µV',
            'fuentes' => ['C01', 'C09'],
            'nota' => 'Duncan 2009 (MMN y P300) y el protocolo de Sharma 2002. El del MLR (±50 µV) es calculado: con 10-300 Hz el EEG de un barrido ya es de varios µV.',
        ],
        'umbral_cortical' => [
            'label' => 'Respuesta cortical cerca del umbral',
            'valor' => 'desde el umbral, entera a 40 dB SL',
            'fuentes' => ['C03'],
            'nota' => 'Lightfoot 2006: el N1-P2 estima el umbral conductual con un error medio de 6,5 dB. El cliente hace aparecer la respuesta en el umbral del oído y la deja entera a 40 dB por encima (calculado), atrasándose al bajar el nivel.',
        ],
        'duracion_estimulo' => [
            'label' => 'Duración del tono en los tardíos (CAEP, P300, MMN)',
            'valor' => '-6 dB (1 kHz) a -4,5 dB (4 kHz) por duplicación, entre 8 y 128 ms',
            'fuentes' => ['C13'],
            'nota' => 'El cliente lo aplica como nivel de sensación perdido contra el tono de rutina de 10-50-10 ms (60 ms efectivos: meseta más media rampa por lado): el 1-10-1 ms del ECochG pierde unos 15 dB y el 2-1-2 ciclos del ABR unos 17. El click cuenta como el tono de 8 ms. Las pendientes intermedias (2 kHz) y el recorte fuera de 8-128 ms son calculados.',
        ],
        'respuesta_40hz' => [
            'label' => 'Respuesta de 40 Hz',
            'valor' => 'superposición a 40/s',
            'fuentes' => ['C11'],
            'nota' => 'El cliente no la programa aparte: suma la respuesta de cada estímulo con las de los vecinos, y a 40/s sale sola.',
        ],
        'sueno' => [
            'label' => 'Pa del niño dormido',
            'valor' => 'según la etapa de sueño',
            'fuentes' => ['C02'],
            'nota' => 'La vía no primaria es sensible al sueño, la sedación y la maduración. Cuánto baja en cada captura es calculado (se sortea por captura).',
        ],
    ];

    /** Qué respalda cada cuadro central del generador. */
    public const CUADROS = [
        'central_normal' => [
            'fuentes' => ['C12', 'C09', 'C08'],
            'respalda' => 'Los valores normales por edad de los cuatro potenciales.',
        ],
        'nino_dormido' => [
            'fuentes' => ['C02'],
            'respalda' => 'Pa variable o ausente en el niño dormido o sedado sin que haya lesión.',
        ],
        'acv_temporal' => [
            'fuentes' => ['C05', 'C06', 'C10'],
            'respalda' => 'Na-Pa reducido sobre el hemisferio lesionado con cualquier oído (efecto electrodo); la amplitud es más sensible que la latencia.',
        ],
        'tpac' => [
            'fuentes' => ['C06', 'C04', 'C01'],
            'respalda' => 'MLR con asimetrías leves o normal, MMN reducida como medida de discriminación y P300 algo tardía.',
        ],
        'privacion_implante_tardio' => [
            'fuentes' => ['C09'],
            'respalda' => 'P1 tardía para la edad cuando el implante llega después del período sensible.',
        ],
        'deterioro_cognitivo' => [
            'fuentes' => ['C07', 'C01'],
            'respalda' => 'P300 prolongada y de menor amplitud con exógenos conservados; sensible pero inespecífica.',
        ],
    ];
}
