export interface KBArticle {
  id: string;
  title: string;
  content: string;
}

export interface KBCategory {
  id: string;
  label: string;
  icon: string;
  articles: KBArticle[];
}

export const HELP_KB: KBCategory[] = [
  // ═══════════════════════════════════════════════════
  // USAR LABSIM
  // ═══════════════════════════════════════════════════
  {
    id: "app",
    label: "Usar LabSim",
    icon: "monitor",
    articles: [
      {
        id: "app-inicio",
        title: "Primeros pasos",
        content:
          "LabSim simula un centro clínico completo. Desde el escritorio puedes abrir simuladores de equipos médicos, gestionar pacientes, agendar atenciones y comunicarte con la secretaria Karime.\n\nHaz doble click en los iconos del escritorio para abrir cada aplicación. También puedes usar el menú Inicio (botón LabSim en la barra de tareas).",
      },
      {
        id: "app-ventanas",
        title: "Ventanas y escritorio",
        content:
          "Las ventanas se pueden mover arrastrando la barra de título, redimensionar desde los bordes, minimizar y maximizar.\n\nLa barra de tareas inferior muestra las ventanas abiertas. Click para enfocar o minimizar.\n\nClick derecho en el escritorio abre un menú con opciones rápidas.",
      },
      {
        id: "app-ia",
        title: "Inteligencia Artificial",
        content:
          "LabSim incluye IA local (no requiere internet). Desde Configuración > Inteligencia Artificial puedes descargar un modelo LLM (Qwen) que permite que Karime y los pacientes respondan de forma inteligente.\n\nTambién puedes activar reconocimiento de voz (Whisper) y síntesis de voz (Piper) desde la misma sección.",
      },
      {
        id: "app-temas",
        title: "Personalización",
        content:
          "Click derecho > Personalizar escritorio, o Configuración > Apariencia.\n\nTres temas: Midnight (oscuro), Clínico (claro) y Nord. Puedes cambiar tamaño de fuente y color de fondo.",
      },
      {
        id: "app-mensajes",
        title: "Mensajes y Karime",
        content:
          "El sistema de mensajes permite comunicarte con Karime (secretaria del centro). Ella gestiona la agenda, avisa sobre pacientes y te notifica atrasos.\n\nSi la IA está activada, Karime responde de forma inteligente según su personalidad. Sin IA, usa respuestas predeterminadas.",
      },
      {
        id: "app-documentos",
        title: "Mis Documentos",
        content:
          "Mis Documentos organiza los archivos de tu práctica clínica en carpetas: Exámenes (por tipo), Informes, Evoluciones, Interconsultas y Notas.\n\nPuedes navegar con doble click en carpetas y usar los botones de atrás e inicio.",
      },
      {
        id: "app-conexion",
        title: "Conexión al servidor",
        content:
          "El indicador Wi-Fi en la barra de tareas muestra el estado de conexión:\n• Verde: conectado al servidor\n• Amarillo: verificando\n• Rojo: sin conexión\n\nClick en el icono para forzar una verificación. Puedes trabajar offline y sincronizar después.",
      },
    ],
  },
  // ═══════════════════════════════════════════════════
  // AUDIOMETRÍA
  // ═══════════════════════════════════════════════════
  {
    id: "audiometria",
    label: "Audiometría",
    icon: "headphones",
    articles: [
      {
        id: "audio-que-es",
        title: "¿Qué es una audiometría?",
        content:
          "La audiometría tonal liminar evalúa los umbrales auditivos por vía aérea (VA) y vía ósea (VO) en frecuencias de 250 Hz a 8000 Hz.\n\nPermite determinar el tipo de hipoacusia (conductiva, sensorioneural o mixta), el grado de pérdida y la configuración audiométrica.",
      },
      {
        id: "audio-procedimiento",
        title: "Procedimiento paso a paso",
        content:
          "1. Otoscopía previa para descartar obstrucciones\n2. Instrucciones al paciente: \"Presione el botón cada vez que escuche un tono, por más débil que sea\"\n3. Colocar auriculares (rojo = oído derecho, azul = izquierdo)\n4. Comenzar por el mejor oído a 1000 Hz\n5. Descender de 10 en 10 dB, ascender de 5 en 5 dB\n6. El umbral es el nivel más bajo donde responde 2 de 3 veces\n7. Evaluar: 1000, 2000, 4000, 8000, 500, 250 Hz\n8. Repetir vía ósea si hay pérdida por vía aérea",
      },
      {
        id: "audio-enmascaramiento",
        title: "Enmascaramiento",
        content:
          "Se requiere enmascaramiento cuando existe riesgo de audición cruzada.\n\nVía aérea: enmascarar cuando la diferencia entre VA del oído evaluado y VO del no evaluado es ≥ 40 dB (auriculares supraurales) o ≥ 55 dB (insertos).\n\nVía ósea: enmascarar cuando existe GAP aéreo-óseo ≥ 10 dB en el oído evaluado.\n\nMétodo de plateau: aumentar el ruido en pasos de 5 dB hasta que el umbral se mantenga estable en al menos 3 niveles consecutivos.",
      },
      {
        id: "audio-interpretacion",
        title: "Interpretación del audiograma",
        content:
          "Tipos de hipoacusia:\n• Conductiva: VA descendida, VO normal, GAP > 10 dB\n• Sensorioneural: VA y VO descendidas sin GAP significativo\n• Mixta: VO descendida + GAP > 10 dB\n\nGrados (PTA 500-4000 Hz):\n• Normal: ≤ 20 dB HL\n• Leve: 21-40 dB\n• Moderada: 41-55 dB\n• Moderada-severa: 56-70 dB\n• Severa: 71-90 dB\n• Profunda: > 90 dB HL",
      },
      {
        id: "audio-configuraciones",
        title: "Configuraciones audiométricas",
        content:
          "• Plana: umbrales similares en todas las frecuencias\n• Descendente: pérdida mayor en agudos (la más frecuente en presbiacusia y trauma acústico)\n• Ascendente: pérdida mayor en graves (rara, puede indicar Ménière o hidrops)\n• En U: pérdida en medias con conservación de graves y agudos\n• Escotoma: pérdida aislada en una frecuencia (típico: 4000 Hz en trauma acústico)\n• Esquina: solo restos auditivos en graves (hipoacusia profunda)",
      },
      {
        id: "audio-simbologia",
        title: "Simbología audiométrica",
        content:
          "Oído derecho (rojo):\n• VA sin enmascarar: O\n• VA enmascarada: △\n• VO sin enmascarar: <\n• VO enmascarada: [\n\nOído izquierdo (azul):\n• VA sin enmascarar: X\n• VA enmascarada: □\n• VO sin enmascarar: >\n• VO enmascarada: ]\n\nSin respuesta: flecha hacia abajo en el símbolo correspondiente.",
      },
      {
        id: "audio-logoaudiometria",
        title: "Logoaudiometría",
        content:
          "Evalúa la capacidad de discriminación del habla. Se presenta una lista de palabras a diferentes intensidades.\n\nMediciones principales:\n• SRT (Speech Reception Threshold): nivel donde el paciente repite correctamente el 50% de las palabras. Debe coincidir ±10 dB con el PTA.\n• SDS (Speech Discrimination Score): porcentaje de palabras correctas a 30-40 dB sobre SRT.\n\nUn SDS bajo con buena audiometría sugiere patología retrococlear.",
      },
      {
        id: "audio-neonatal",
        title: "Screening auditivo neonatal",
        content:
          "Todo recién nacido debe ser evaluado antes del mes de vida.\n\nMétodos:\n• OAE (Emisiones Otoacústicas): evalúan función de células ciliadas externas. Rápido y no invasivo.\n• BERA automático (aABR): evalúa la vía auditiva hasta tronco encefálico.\n\nProtocolo: si falla el primer screening, repetir al mes. Si persiste, derivar a evaluación audiológica completa antes de los 3 meses.",
      },
    ],
  },
  // ═══════════════════════════════════════════════════
  // IMPEDANCIOMETRÍA
  // ═══════════════════════════════════════════════════
  {
    id: "impedanciometria",
    label: "Impedanciometría",
    icon: "activity",
    articles: [
      {
        id: "imp-que-es",
        title: "¿Qué es la impedanciometría?",
        content:
          "Evalúa la función del oído medio mediante análisis de la impedancia acústica. Incluye timpanometría y reflejos acústicos estapediales.\n\nEs un examen objetivo (no requiere respuesta del paciente) y complementa la audiometría tonal.",
      },
      {
        id: "imp-timpanometria",
        title: "Timpanometría",
        content:
          "Mide la compliancia del sistema tímpano-osicular en función de la presión.\n\nCurvas de Jerger:\n• Tipo A: normal (pico entre -100 y +50 daPa)\n• Tipo As: pico reducido (fijación osicular, otosclerosis)\n• Tipo Ad: pico muy elevado (disyunción osicular, membrana flácida)\n• Tipo B: plana (líquido en oído medio, perforación, cerumen)\n• Tipo C: pico desplazado a negativos > -100 daPa (disfunción tubárica)",
      },
      {
        id: "imp-reflejos",
        title: "Reflejos acústicos",
        content:
          "El reflejo estapedial es la contracción bilateral del músculo del estribo ante un estímulo sonoro intenso (70-100 dB sobre umbral).\n\nSe evalúa ipsi y contralateral. Su presencia, ausencia y umbral orientan sobre:\n• Integridad de la vía auditiva del tronco\n• Lesiones retrococleares (decaimiento del reflejo: test de Anderson)\n• Patología de oído medio\n• Reclutamiento (reflejo presente a baja sensación en hipoacusias cocleares)",
      },
      {
        id: "imp-tuba",
        title: "Función tubárica",
        content:
          "La tuba auditiva (trompa de Eustaquio) ventila el oído medio. Su disfunción causa presión negativa y eventualmente otitis media con efusión.\n\nEvaluación:\n• Timpanometría: curva tipo C indica disfunción\n• Test de Williams: timpanograma con y sin maniobra de Valsalva/Toynbee\n• En perforación: la compliancia cambia al deglutir con la sonda puesta",
      },
      {
        id: "imp-pediatria",
        title: "Impedanciometría pediátrica",
        content:
          "En lactantes < 6 meses se usa tono sonda de 1000 Hz (no 226 Hz) porque el conducto auditivo del lactante es más compliantey el tono grave genera artefactos.\n\nEn niños mayores se usa el protocolo estándar. La timpanometría es especialmente útil para detectar otitis media con efusión, causa frecuente de hipoacusia conductiva en preescolares.",
      },
    ],
  },
  // ═══════════════════════════════════════════════════
  // OFTALMOLOGÍA
  // ═══════════════════════════════════════════════════
  {
    id: "oftalmologia",
    label: "Oftalmología",
    icon: "eye",
    articles: [
      {
        id: "oft-campo-visual",
        title: "Campimetría",
        content:
          "La perimetría computarizada evalúa el campo visual detectando estímulos luminosos en diferentes puntos.\n\nFundamental para glaucoma, lesiones neurológicas y patología retiniana.\n\nÍndices principales:\n• MD (Mean Deviation): defecto promedio global\n• PSD (Pattern Standard Deviation): irregularidad del defecto\n• VFI (Visual Field Index): porcentaje de campo visual funcional\n• GHT (Glaucoma Hemifield Test): compara hemicampos superior e inferior",
      },
      {
        id: "oft-campo-patrones",
        title: "Patrones de defecto campimétrico",
        content:
          "• Escotoma arciforme: sigue la distribución de fibras nerviosas. Típico de glaucoma.\n• Escalón nasal: diferencia entre hemicampos superior e inferior nasal. Glaucoma.\n• Hemianopsia homónima: defecto del mismo lado en ambos ojos. Lesión retroquiasmática.\n• Hemianopsia bitemporal: defecto temporal bilateral. Compresión quiasmática (adenoma hipofisiario).\n• Constricción concéntrica: reducción periférica global. Retinitis pigmentosa, glaucoma avanzado.\n• Escotoma central/cecocentral: afecta fijación. Neuritis óptica, maculopatía.",
      },
      {
        id: "oft-oct",
        title: "OCT",
        content:
          "Tomografía de Coherencia Óptica: imágenes de alta resolución de las capas retinianas usando interferometría.\n\nAplicaciones:\n• RNFL (capa de fibras nerviosas) para glaucoma\n• Espesor macular para edema, membranas, agujeros\n• Cabeza del nervio óptico: excavación, anillo neurorretiniano\n• OCT-Angiografía: vascularización sin contraste",
      },
      {
        id: "oft-oct-glaucoma",
        title: "OCT en glaucoma",
        content:
          "El OCT mide el grosor de la RNFL peripapilar y el complejo de células ganglionares maculares.\n\nSe compara con una base normativa por edad, sexo y etnia:\n• Verde: dentro de límites normales (p > 5%)\n• Amarillo: borderline (p 1-5%)\n• Rojo: fuera de límites normales (p < 1%)\n\nLa progresión se evalúa con análisis de tendencia (trend) y evento (event).",
      },
      {
        id: "oft-topografia",
        title: "Topografía corneal",
        content:
          "Mapea la curvatura de la superficie corneal.\n\nUsos:\n• Detección de queratocono y ectasias\n• Adaptación de lentes de contacto\n• Planificación de cirugía refractiva\n• Seguimiento post-quirúrgico\n\nMapas: axial (sagital), tangencial (instantáneo), elevación anterior/posterior, paquimetría.",
      },
      {
        id: "oft-queratocono",
        title: "Queratocono",
        content:
          "Ectasia corneal progresiva que produce adelgazamiento y protrusión cónica.\n\nSignos topográficos:\n• Asimetría inferior-superior > 1.4 D (índice I-S)\n• KISA% > 100%\n• Adelgazamiento corneal descentrado\n• Elevación posterior aumentada\n\nClasificación de Amsler-Krumeich: 4 estadios según K máximo, astigmatismo, paquimetría y cicatrices.",
      },
      {
        id: "oft-scheimpflug",
        title: "Scheimpflug (Pentacam)",
        content:
          "Cámara rotacional que fotografía una sección óptica de todo el segmento anterior.\n\nEvalúa:\n• Topografía anterior y posterior de la córnea\n• Paquimetría punto a punto (mapa)\n• Profundidad de cámara anterior\n• Densitometría del cristalino\n• Índices de ectasia (BAD-D, Belin-Ambrósio)\n\nÚtil para screening pre-refractivo y detección de ectasia subclínica.",
      },
      {
        id: "oft-autoref",
        title: "Autorefractometría",
        content:
          "El autorefractómetro mide objetivamente el error refractivo: miopía, hipermetropía y astigmatismo.\n\nProporciona esfera, cilindro y eje como punto de partida para la refracción subjetiva.\n\nLimitaciones: tiende a sobre-menos (más miopía) por acomodación. En niños se requiere cicloplejia para resultado confiable.",
      },
      {
        id: "oft-retinografia",
        title: "Retinografía",
        content:
          "Fotografía del fondo de ojo que documenta el estado de retina, nervio óptico y vasos.\n\nAplicaciones:\n• Documentación de retinopatía diabética (clasificación y seguimiento)\n• Evaluación de excavación papilar en glaucoma\n• Degeneración macular asociada a edad\n• Oclusiones vasculares\n• Desprendimiento de retina\n\nLa retinografía de campo amplio (ultra-widefield) captura hasta 200° del fondo.",
      },
    ],
  },
  // ═══════════════════════════════════════════════════
  // OTONEUROLOGÍA
  // ═══════════════════════════════════════════════════
  {
    id: "otoneurologia",
    label: "Otoneurología",
    icon: "brain",
    articles: [
      {
        id: "oto-vng",
        title: "VNG (Videonistagmografía)",
        content:
          "Registra movimientos oculares con cámaras infrarrojas para evaluar el sistema vestibular.\n\nIncluye:\n• Pruebas oculomotoras: sacadas, seguimiento suave, optocinético\n• Pruebas posicionales: Dix-Hallpike, roll test, posición estática\n• Prueba calórica bitérmica: agua o aire a 30°C y 44°C\n\nPermite diferenciar lesiones vestibulares periféricas de centrales.",
      },
      {
        id: "oto-vng-calorica",
        title: "Prueba calórica",
        content:
          "Estimula cada laberinto por separado con temperatura fría (30°C) y caliente (44°C).\n\nFórmula de Jongkees:\n• Paresia canalicular: asimetría > 20-25% entre oídos → lesión periférica del lado débil\n• Preponderancia direccional: asimetría > 30% en una dirección → puede ser central o compensación\n\nMnemotecnia COWS: Cold Opposite, Warm Same (dirección del nistagmo).",
      },
      {
        id: "oto-vhit",
        title: "vHIT",
        content:
          "Video Head Impulse Test: evalúa el VOR de alta frecuencia para cada canal semicircular.\n\nImpulsos cefálicos rápidos registrando respuesta ocular:\n• Ganancia normal: 0.8-1.2\n• Ganancia reducida: hipofunción del canal\n• Sacadas covert: durante el impulso (compensación temprana)\n• Sacadas overt: después del impulso (compensación tardía)\n\nVentaja sobre la calórica: evalúa los 6 canales y es más fisiológico.",
      },
      {
        id: "oto-vppb",
        title: "VPPB",
        content:
          "Vértigo Posicional Paroxístico Benigno: la causa más frecuente de vértigo.\n\nCausa: otolitos (cristales de CaCO₃) desplazados a los canales semicirculares.\n\nDiagnóstico:\n• Canal posterior (90%): maniobra de Dix-Hallpike → nistagmo torsional geotrópico\n• Canal horizontal: roll test → nistagmo horizontal\n\nTratamiento:\n• Canal posterior: maniobra de Epley o Semont\n• Canal horizontal: maniobra de Lempert (barbecue roll)",
      },
      {
        id: "oto-meniere",
        title: "Enfermedad de Ménière",
        content:
          "Tríada clásica: vértigo episódico + hipoacusia fluctuante + tinnitus + plenitud aural.\n\nCriterios diagnósticos (AAO-HNS 2015):\n• ≥ 2 episodios de vértigo de 20 min a 12 horas\n• Hipoacusia sensorioneural documentada\n• Síntomas aurales fluctuantes (tinnitus, plenitud)\n\nAudiometría: hipoacusia sensorioneural de predominio grave (ascendente) en etapas iniciales. ECoG: aumento relación SP/AP.",
      },
      {
        id: "oto-neurinoma",
        title: "Schwannoma vestibular",
        content:
          "Tumor benigno del VIII par (nervio vestibular), antes llamado neurinoma del acústico.\n\nSospecha clínica:\n• Hipoacusia sensorioneural unilateral progresiva\n• Tinnitus unilateral\n• Discriminación verbal desproporcionadamente mala\n• Reflejos acústicos ausentes o con decaimiento\n\nConfirmación: RMN con gadolinio. El ABR (BERA) muestra prolongación de onda V y latencia I-V.",
      },
    ],
  },
  // ═══════════════════════════════════════════════════
  // FLUJO CLÍNICO
  // ═══════════════════════════════════════════════════
  {
    id: "clinica",
    label: "Flujo clínico",
    icon: "clipboard",
    articles: [
      {
        id: "cli-agenda",
        title: "Agenda y atención de pacientes",
        content:
          "La agenda muestra los pacientes citados. Desde ella puedes:\n• Ver datos del paciente y motivo de consulta\n• Llamar al paciente cuando sea su turno\n• Registrar la atención y procedimientos\n\nKarime te avisará si hay atrasos o cambios.",
      },
      {
        id: "cli-larissa",
        title: "Ficha clínica (Larissa)",
        content:
          "Larissa es el sistema de ficha clínica del centro, formato MINSAL:\n• Datos de identificación\n• Anamnesis y antecedentes\n• Exámenes y resultados\n• Evoluciones clínicas\n• Interconsultas y derivaciones\n\nCada estudiante tiene su propia versión del paciente.",
      },
      {
        id: "cli-evolucion",
        title: "Evoluciones e interconsultas",
        content:
          "Después de cada atención registra una evolución con:\n• Motivo de consulta\n• Hallazgos de los exámenes\n• Hipótesis diagnóstica\n• Plan de manejo\n\nSi el caso lo requiere, genera una interconsulta a otra especialidad desde la ficha.",
      },
      {
        id: "cli-anamnesis",
        title: "Anamnesis audiológica",
        content:
          "Preguntas fundamentales:\n• Motivo de consulta y cronología\n• Hipoacusia: lateralidad, inicio, progresión, fluctuación\n• Tinnitus: unilateral/bilateral, tono, intensidad percibida\n• Vértigo: tipo, duración, desencadenantes, síntomas asociados\n• Otalgia, otorrea, plenitud aural\n• Exposición a ruido (laboral, recreativo)\n• Antecedentes: ototóxicos, cirugías, familia, comorbilidades\n• Desarrollo del lenguaje (en niños)",
      },
      {
        id: "cli-otoscopia",
        title: "Otoscopía",
        content:
          "Inspección del conducto auditivo externo y membrana timpánica.\n\nDescribir:\n• CAE: permeable, cerumen, exostosis, cuerpo extraño\n• Membrana timpánica: color, integridad, posición, movilidad\n• Triángulo luminoso: presente/ausente, posición\n• Mango del martillo: visible/no visible\n\nAlteraciones frecuentes: perforación, retracción, nivel hidroaéreo, miringitis, tubos de ventilación.",
      },
      {
        id: "cli-informe",
        title: "Redacción de informes",
        content:
          "Estructura del informe audiológico:\n1. Datos del paciente y fecha\n2. Motivo del examen\n3. Exámenes realizados (descripción técnica)\n4. Resultados (audiometría, impedanciometría, etc.)\n5. Correlación clínica\n6. Conclusión diagnóstica\n7. Recomendaciones\n\nLenguaje claro, objetivo y profesional. Evitar abreviaciones no estandarizadas.",
      },
    ],
  },
  // ═══════════════════════════════════════════════════
  // EQUIPAMIENTO
  // ═══════════════════════════════════════════════════
  {
    id: "equipos",
    label: "Equipamiento",
    icon: "settings",
    articles: [
      {
        id: "eq-audiometro",
        title: "Audiómetro clínico",
        content:
          "El audiómetro clínico de dos canales permite:\n• Tono puro por vía aérea y ósea\n• Ruido enmascarante (banda estrecha, blanco, speech noise)\n• Logoaudiometría (canal de voz + ruido)\n• Campo libre\n\nCalibración: según norma ISO 389. Verificar biológicamente cada día (el operador se autoevalúa).",
      },
      {
        id: "eq-impedanciometro",
        title: "Impedanciómetro",
        content:
          "Equipo para timpanometría y reflejos acústicos.\n\nComponentes:\n• Sonda: altavoz (tono sonda 226 Hz o 1000 Hz), micrófono, bomba de presión\n• Auricular contralateral para reflejos\n\nVerificar hermeticidad del sello antes de cada medición. En niños < 6 meses usar tono sonda de 1000 Hz.",
      },
      {
        id: "eq-calibracion",
        title: "Calibración y mantenimiento",
        content:
          "• Calibración electroacústica anual según norma ISO/IEC\n• Verificación biológica diaria: el operador evalúa sus propios umbrales\n• Limpieza de auriculares y olivas después de cada paciente\n• Almacenar en ambiente controlado (humedad, temperatura)\n• Registro de calibraciones en bitácora\n\nUn equipo descalibrado genera diagnósticos erróneos.",
      },
      {
        id: "eq-cabina",
        title: "Cabina audiométrica",
        content:
          "Requisitos según norma ANSI S3.1:\n• Nivel de ruido ambiental máximo por frecuencia\n• Paredes con aislamiento acústico y absorción interna\n• Puerta con sello hermético\n• Ventana de observación\n• Sistema de comunicación con el paciente\n• Iluminación adecuada\n\nVerificar periódicamente con sonómetro que el ruido ambiental no exceda los límites.",
      },
    ],
  },
  // ═══════════════════════════════════════════════════
  // AUDÍFONOS Y REHABILITACIÓN
  // ═══════════════════════════════════════════════════
  {
    id: "rehabilitacion",
    label: "Rehabilitación auditiva",
    icon: "ear",
    articles: [
      {
        id: "reh-audifonos",
        title: "Audífonos: tipos y selección",
        content:
          "Tipos principales:\n• BTE (retroauricular): versátil, para toda pérdida\n• RIC (receptor en canal): discreto, buena calidad sonora\n• ITE/ITC/CIC (intraauricular): estéticos, limitados en potencia\n\nSelección según:\n• Grado y configuración de la pérdida\n• Necesidades comunicativas del paciente\n• Destreza manual y capacidad cognitiva\n• Anatomía del conducto auditivo\n• Presupuesto",
      },
      {
        id: "reh-adaptacion",
        title: "Proceso de adaptación",
        content:
          "1. Evaluación audiológica completa\n2. Selección del audífono\n3. Toma de impresión (si es molde a medida)\n4. Programación inicial (prescripción NAL-NL2 o DSL)\n5. Verificación con medición en oído real (REM/RECD)\n6. Validación subjetiva (cuestionarios: APHAB, IOI-HA)\n7. Seguimiento y ajustes\n8. Consejería sobre uso, mantenimiento y expectativas",
      },
      {
        id: "reh-implante",
        title: "Implante coclear",
        content:
          "Dispositivo que estimula directamente el nervio auditivo, bypaseando el oído medio y las células ciliadas.\n\nCriterios generales:\n• Hipoacusia sensorioneural severa-profunda bilateral\n• Beneficio limitado con audífonos óptimamente adaptados\n• Evaluación multidisciplinaria (audiología, ORL, psicología, terapia)\n\nComponentes: procesador externo (micrófono, procesador, antena) + implante interno (receptor, electrodo intracoclear).",
      },
      {
        id: "reh-terapia",
        title: "Terapia auditiva",
        content:
          "Rehabilitación complementaria al dispositivo:\n• Entrenamiento auditivo: detección, discriminación, identificación, comprensión\n• Lectura labial como apoyo visual\n• Estrategias comunicativas para el paciente y la familia\n• Manejo del tinnitus (TRT, CBT)\n\nEn niños: terapia auditivo-verbal (TAV) o enfoque auditivo-oral para desarrollo del lenguaje.",
      },
    ],
  },
];
