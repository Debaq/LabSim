<?php

declare(strict_types=1);

/**
 * Bibliografía de la electrococleografía: de dónde sale cada límite que usa
 * el cliente (src/abr/ecochg.py) y qué publica cada serie.
 *
 * Mismo criterio que AbrReferences: vive en el BACKEND porque el docente no
 * ve el repo del cliente, y se muestra solo a él (admin/normativas.php),
 * nunca al alumno.
 *
 * Los límites de acá son ESPEJO de los del cliente, no una configuración:
 * cambiarlos acá no cambia lo que mide la app. Lo que ninguna serie
 * publica (el corrimiento por tasa, los rangos de los cuadros del
 * generador) va marcado 'calculado' con la explicación de dónde sale.
 */
final class EcochgReferences
{
    /** Ficha de cada fuente citada. */
    public const FUENTES = [
        'E01' => [
            'cita' => 'Margolis RH, Rieks D, Fournier EM, Levine SE. Tympanic electrocochleography for diagnosis of Menière\'s disease. Arch Otolaryngol Head Neck Surg. 1995;121(1):44-55. PMID 7803022.',
            'n' => '53 adultos normoyentes sin síntomas de Ménière',
            'protocolo' => 'Electrodo de mecha sobre el tímpano bajo microscopio; click en condensación, rarefacción y alternado, tone burst de 1 y 2 kHz. Criterios de anormalidad fijados para 95% de especificidad.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/7803022/',
        ],
        'E02' => [
            'cita' => 'Devaiah AK, Dawson KL, Ferraro JA, Ator GA. Utility of area curve ratio electrocochleography in early Meniere disease. Arch Otolaryngol Head Neck Surg. 2003;129(5):547-551. PMID 12759268.',
            'n' => '8 pacientes con Ménière posible y 13 controles',
            'protocolo' => 'Electrodo timpánico, click alternado a 90 dB; razón de amplitudes y razón de áreas PS/PA.',
            'enlace' => 'https://pubmed.ncbi.nlm.nih.gov/12759268/',
        ],
        'E03' => [
            'cita' => 'Satar B, Meteoğlu A, Yetişer S, Özkaptan Y. Endolenfatik hidropsta kulak zarından elektrokokleografi: klinik ve elektrofizyolojik ilişkinin araştırılması. Türkiye Klinikleri J ENT. 2003;3(1):30-39.',
            'n' => '36 pacientes con Ménière definido o probable (AAO-HNS 1995) y 12 controles',
            'protocolo' => 'Electrodo timpánico, click a 80-100 dB nHL; límites = media de los controles + 2 DE.',
            'enlace' => 'https://www.turkiyeklinikleri.com/article/en-endolenfatik-hidropsta-kulak-zarindanelektrokokleografi-klinik-veelektrofizyolojik-iliskinin-arastirilmasi-32278.html',
        ],
        'E04' => [
            'cita' => 'Roland PS, Rosenbloom J, Yellin W, Meyerhoff WL. Intrasubject test-retest variability in clinical electrocochleography. Laryngoscope. 1993;103(9):963-966.',
            'n' => '17 adultos normoyentes, 34 oídos, 4 a 7 registros por oído',
            'protocolo' => 'Electrodo de conducto (TIPtrode de lámina de oro), registros semanales.',
            'enlace' => 'https://experts.nau.edu/en/publications/intrasubject-test-retest-variability-in-clinical-electrocochleogr/',
        ],
        'E05' => [
            'cita' => 'Wuyts FL, Van de Heyning PH, Van Spaendonck MP, Molenberghs G. A review of electrocochleography: instrumentation settings and meta-analysis of criteria for diagnosis of endolymphatic hydrops. Acta Otolaryngol Suppl. 1997;526:14-20. doi:10.3109/00016489709124014.',
            'n' => 'Revisión y metaanálisis de la literatura publicada',
            'protocolo' => 'Compara transtimpánico (TT) contra extratimpánico (ET, todo lo que no atraviesa el tímpano); click y tone burst.',
            'enlace' => 'https://documentserver.uhasselt.be/handle/1942/331',
        ],
        'E06' => [
            'cita' => 'Baba A, Takasaki K, Tanaka F, Tsukasaki N, Kumagami H, Takahashi H. Amplitude and area ratios of summating potential/action potential (SP/AP) in Meniere\'s disease. Acta Otolaryngol. 2009;129(1):25-29.',
            'n' => '198 pacientes con Ménière (209 oídos), revisión retrospectiva',
            'protocolo' => 'Electrodo transtimpánico; razón de amplitudes y razón de áreas PS/PA.',
            'enlace' => 'https://nagasaki-u.repo.nii.ac.jp/records/16623',
        ],
        'E07' => [
            'cita' => 'Lamounier P, Gobbo DA, de Souza TSA, de Oliveira CACP, Bahmad F Jr. Electrocochleography for Ménière\'s disease: is it reliable? Braz J Otorhinolaryngol. 2014;80(6):527-532. doi:10.1016/j.bjorl.2014.08.010.',
            'n' => 'Revisión sistemática, 19 estudios observacionales desde el año 2000',
            'protocolo' => 'Sensibilidad y especificidad del ECochG en el hidrops.',
            'enlace' => 'https://doi.org/10.1016/j.bjorl.2014.08.010',
        ],
    ];

    /**
     * Cada número que usa el cliente y de dónde sale. 'fuentes' vacío =
     * calculado por el modelo; la nota dice cómo.
     */
    public const LIMITES = [
        'sp_ap_tympanic' => [
            'label' => 'Razón PS/PA, electrodo en el tímpano',
            'valor' => '0,40',
            'fuentes' => ['E01', 'E03'],
            'nota' => 'Margolis 1995 fija el criterio para 95% de especificidad; las revisiones que lo citan dan el percentil 95 entre 0,40 y 0,49 según el nivel (dato de fuente secundaria, a confirmar en el original). Satar 2003 llega a 0,32 (0,22 ± 0,05 + 2 DE) con solo 12 controles. Se toma el extremo bajo de Margolis por ser la serie más grande.',
        ],
        'sp_ap_extratympanic' => [
            'label' => 'Razón PS/PA, electrodo de conducto (TipTrode)',
            'valor' => '0,50',
            'fuentes' => ['E04', 'E05'],
            'nota' => 'Roland 1993 publica media 0,22 ± 0,06 con rango 0,04-0,50: el 0,50 es el techo observado, no un corte estadístico. Wuyts 1997 propone 0,42 para el extratimpánico, pero en ese trabajo "extratimpánico" junta tímpano y conducto.',
        ],
        'sp_ap_transtympanic' => [
            'label' => 'Razón PS/PA, aguja en el promontorio',
            'valor' => '0,35',
            'fuentes' => ['E05'],
            'nota' => 'Corte transtimpánico del metaanálisis de Wuyts 1997.',
        ],
        'area_ratio' => [
            'label' => 'Razón de áreas PS/PA (los tres electrodos)',
            'valor' => '1,94',
            'fuentes' => ['E02', 'E06'],
            'nota' => 'Devaiah 2003: controles 1,34 ± 0,30, límite = + 2 DE, electrodo timpánico. Con electrodo transtimpánico Baba 2009 no la encontró más sensible que la de amplitudes (43,9% contra 57,1% de anormales en el Ménière definido).',
        ],
        'rar_cond' => [
            'label' => 'Separación del PA entre condensación y rarefacción',
            'valor' => '0,38 ms',
            'fuentes' => ['E03', 'E01'],
            'nota' => 'Satar 2003: controles 0,24 ± 0,07 ms + 2 DE. Margolis 1995 la recomienda como indicador de hidrops, pero en Satar los Ménière definidos promediaron 0,19 ms y agregarla no mejoró el diagnóstico: por eso los cuadros del generador la dejan a ambos lados del límite.',
        ],
        'nivel' => [
            'label' => 'Nivel al que el PS se mide entero',
            'valor' => '50 dB sobre el umbral del click',
            'fuentes' => ['E01'],
            'nota' => 'Calculado. En oídos sanos Margolis 1995 encuentra la razón poco dependiente del nivel en el rango clínico (0,29 a 68 dB nHL y 0,22 a 78, según una revisión que lo cita). El modelo deja el PS entero desde 50 dB sobre el umbral y lo achica por debajo, para que medir a nivel bajo sea un error posible.',
        ],
        'tasa' => [
            'label' => 'Corrimiento del PA por tasa (11,1 a 91/s)',
            'valor' => '0,20 ms',
            'fuentes' => [],
            'nota' => 'Calculado: sale del modelo de tasa de la onda I del ABR. Un oído sano corre 0,12 ms y uno que se adapta 2,5 veces más, 0,29 ms; el límite va entre los dos.',
        ],
        'sensibilidad' => [
            'label' => 'Ménière con ECochG normal',
            'valor' => '25-54%',
            'fuentes' => ['E07', 'E06', 'E03'],
            'nota' => 'Lamounier 2014 reúne 25-54% de Ménière con ECochG normal. Baba 2009: razón de amplitudes anormal en 57,1% de los definidos; Satar 2003: 53%. Los cuadros del generador dan siempre el hidrops alterado (Ménière 0,46-0,70, retardado 0,48-0,72 con electrodo de tímpano); un Ménière con ECochG normal se arma a mano.',
        ],
    ];
}
