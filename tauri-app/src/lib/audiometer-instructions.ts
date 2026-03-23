/**
 * Sistema de instrucciones verbales del audiómetro.
 *
 * En un examen real, el audiólogo DEBE dar instrucciones claras al paciente
 * antes de cada prueba. Sin la instrucción correcta, el paciente no sabe
 * qué hacer y no responde adecuadamente.
 *
 * El estudiante selecciona una instrucción predefinida (como si hablara
 * por el talkback). El texto se muestra en pantalla y se puede reproducir
 * por TTS. La instrucción activa determina CÓMO responde el paciente.
 */

// ─── Definición de instrucciones ────────────────────────

export interface Instruction {
  /** ID único */
  id: string;
  /** Texto corto para el botón */
  label: string;
  /** Lo que el audiólogo "dice" al paciente */
  speech: string;
  /** Categoría para agrupar en la UI */
  category: InstructionCategory;
  /** Modo de respuesta que activa en el paciente */
  responseMode: ResponseMode;
  /** Si es una pregunta (espera respuesta verbal, no manual) */
  isQuestion: boolean;
}

export type InstructionCategory =
  | "preparacion"
  | "audiometria"
  | "supraliminal"
  | "logoaudiometria"
  | "preguntas";

export const CATEGORY_LABELS: Record<InstructionCategory, string> = {
  preparacion: "Preparación",
  audiometria: "Audiometría",
  supraliminal: "Supraliminal",
  logoaudiometria: "Logo",
  preguntas: "Preguntas",
};

/**
 * Modo de respuesta del paciente según la instrucción recibida.
 *
 * - none: Sin instrucción, paciente no sabe qué hacer
 * - threshold_air: Audiometría aérea sin enmascarar — levanta mano al escuchar pito
 * - threshold_bone: Audiometría ósea sin enmascarar
 * - threshold_air_masked: Aérea con masking — ignora el ruido
 * - threshold_bone_masked: Ósea con masking
 * - sustained: Mantener mano levantada mientras escuche (Tone Decay / Carhart)
 * - sustained_masked: Mantener mano con masking (SISI en ruido)
 * - loudness: Avisar solo si molesta (LDL)
 * - binaural: Dos pitos alternados, comparar volumen (Fowler/ABLB)
 * - volume_change: Avisar cambio de volumen (SISI / Luscher)
 * - speech_detect: Levantar mano al escuchar voz (SDT)
 * - speech_repeat: Repetir palabras (SRT / UMD)
 * - question: Espera respuesta verbal del paciente
 */
export type ResponseMode =
  | "none"
  | "threshold_air"
  | "threshold_bone"
  | "threshold_air_masked"
  | "threshold_bone_masked"
  | "sustained"
  | "sustained_masked"
  | "loudness"
  | "binaural"
  | "volume_change"
  | "speech_detect"
  | "speech_repeat"
  | "question";

// ─── Catálogo de instrucciones ──────────────────────────

export const INSTRUCTIONS: Instruction[] = [
  // ─── Preparación ──────────────────────────────
  {
    id: "colocar_fonos",
    label: "Colocar fonos",
    speech: "Le voy a colocar estos fonos. Por estos fonos va a escuchar unos pitos. Cada pito que escuche, necesito que levante la mano, por más despacio que lo escuche.",
    category: "preparacion",
    responseMode: "threshold_air",
    isQuestion: false,
  },
  {
    id: "colocar_vibrador",
    label: "Colocar vibrador",
    speech: "Le voy a colocar este aparato detrás de su oreja. Necesito que me avise los pitos que escuche, levantando la mano.",
    category: "preparacion",
    responseMode: "threshold_bone",
    isQuestion: false,
  },
  {
    id: "aerea_con_ruido",
    label: "Aérea + ruido",
    speech: "Ahora va a escuchar un ruido por la otra orejita. Necesito que no le haga caso a ese ruido y que solo me avise los pitos que escuche.",
    category: "preparacion",
    responseMode: "threshold_air_masked",
    isQuestion: false,
  },
  {
    id: "osea_con_ruido",
    label: "Ósea + ruido",
    speech: "Le voy a colocar este aparato detrás de su oreja. Por la otra oreja va a escuchar un ruido. No le haga caso al ruido, solo avíseme los pitos.",
    category: "preparacion",
    responseMode: "threshold_bone_masked",
    isQuestion: false,
  },

  // ─── Audiometría ──────────────────────────────
  {
    id: "escuche_mi_voz",
    label: "Escuche mi voz",
    speech: "Apenas escuche mi voz, levante la mano.",
    category: "audiometria",
    responseMode: "speech_detect",
    isQuestion: false,
  },
  {
    id: "mano_levantada",
    label: "Mano levantada",
    speech: "Va a escuchar un pito continuo. Necesito que mantenga la mano levantada todo el momento que escuche el pito. Cuando deje de escucharlo, baje la mano.",
    category: "audiometria",
    responseMode: "sustained",
    isQuestion: false,
  },
  {
    id: "mano_levantada_ruido",
    label: "Mano + ruido",
    speech: "Va a sentir un ruido fuerte por un oído y un pito por el mismo oído. Necesito que mantenga la mano levantada mientras escuche el pito. No le haga caso al ruido.",
    category: "audiometria",
    responseMode: "sustained_masked",
    isQuestion: false,
  },

  // ─── Supraliminal ────────────────────────────
  {
    id: "pitos_fuertes",
    label: "Pitos fuertes",
    speech: "Ahora le voy a colocar unos pitos fuertes. Van a ser todos fuertes e irán aumentando en volumen. Solo si le molesta, levante la mano.",
    category: "supraliminal",
    responseMode: "loudness",
    isQuestion: false,
  },
  {
    id: "solo_si_molesta",
    label: "Solo si molesta",
    speech: "Solo si molesta el pito fuerte, levante la mano.",
    category: "supraliminal",
    responseMode: "loudness",
    isQuestion: false,
  },
  {
    id: "dos_pitos",
    label: "Dos pitos",
    speech: "Va a escuchar dos pitos, de forma alternada, un oído primero y otro después. Necesito que me diga si los escucha igual en volumen o si uno suena más fuerte que el otro.",
    category: "supraliminal",
    responseMode: "binaural",
    isQuestion: false,
  },
  {
    id: "cambie_de_volumen",
    label: "Cambio de volumen",
    speech: "Va a escuchar un pito de forma continua. Necesito que me avise cuando ese pito cambie de volumen, levantando la mano.",
    category: "supraliminal",
    responseMode: "volume_change",
    isQuestion: false,
  },

  // ─── Logoaudiometría ─────────────────────────
  {
    id: "dictar_palabras",
    label: "Dictar palabras",
    speech: "Ahora le voy a dictar unas palabras. Necesito que las repita en voz alta. Repita solo lo que entienda, no importa si no entiende todo.",
    category: "logoaudiometria",
    responseMode: "speech_repeat",
    isQuestion: false,
  },

  // ─── Preguntas ────────────────────────────────
  {
    id: "escucha",
    label: "¿Me escucha?",
    speech: "¿Me escucha?",
    category: "preguntas",
    responseMode: "question",
    isQuestion: true,
  },
  {
    id: "muy_fuerte",
    label: "¿Muy fuerte?",
    speech: "¿Está muy fuerte mi voz?",
    category: "preguntas",
    responseMode: "question",
    isQuestion: true,
  },
  {
    id: "molesta",
    label: "¿Molesta?",
    speech: "¿Molesta cuando le hablo?",
    category: "preguntas",
    responseMode: "question",
    isQuestion: true,
  },
  {
    id: "dejo_de_escuchar",
    label: "¿Dejó de escuchar?",
    speech: "¿Lo dejó de escuchar?",
    category: "preguntas",
    responseMode: "question",
    isQuestion: true,
  },
  {
    id: "sonidos_iguales",
    label: "¿Iguales?",
    speech: "¿Los escuchó iguales?",
    category: "preguntas",
    responseMode: "question",
    isQuestion: true,
  },
  {
    id: "en_que_oido",
    label: "¿Qué oído?",
    speech: "¿Qué oído escuchó más fuerte?",
    category: "preguntas",
    responseMode: "question",
    isQuestion: true,
  },
  {
    id: "pa_pa_pa",
    label: "Pa pa pa",
    speech: "Pa, pa, pa...",
    category: "preguntas",
    responseMode: "question",
    isQuestion: false,
  },
];

/** Buscar instrucción por ID */
export function getInstruction(id: string): Instruction | undefined {
  return INSTRUCTIONS.find((i) => i.id === id);
}

/** Instrucciones agrupadas por categoría */
export function getInstructionsByCategory(): Record<InstructionCategory, Instruction[]> {
  const grouped: Record<InstructionCategory, Instruction[]> = {
    preparacion: [],
    audiometria: [],
    supraliminal: [],
    logoaudiometria: [],
    preguntas: [],
  };
  for (const inst of INSTRUCTIONS) {
    grouped[inst.category].push(inst);
  }
  return grouped;
}

/**
 * Verifica si la instrucción activa es compatible con la prueba que se está haciendo.
 *
 * Si el estudiante intenta hacer audiometría ósea pero dio la instrucción
 * de "colocar fonos" (aérea), el paciente está confundido.
 *
 * @returns true si la instrucción es compatible, false si el paciente no sabe qué hacer
 */
// ─── Palabras clave por instrucción para matching de voz ─

const VOICE_KEYWORDS: Record<string, string[]> = {
  colocar_fonos: ["fonos", "auriculares", "colocar fonos", "poner fonos", "ponerse los fonos", "coloque", "audífonos"],
  colocar_vibrador: ["vibrador", "colocar vibrador", "aparato", "detrás de la oreja", "mastoide", "hueso"],
  aerea_con_ruido: ["ruido", "aérea con ruido", "otra oreja ruido", "no le haga caso", "enmascarar"],
  osea_con_ruido: ["ósea con ruido", "vibrador con ruido", "hueso con ruido", "vibrador ruido"],
  escuche_mi_voz: ["escuche mi voz", "escucha mi voz", "me escucha", "puede escucharme"],
  mano_levantada: ["mano levantada", "mantenga la mano", "mientras escuche", "pito continuo", "tono continuo"],
  mano_levantada_ruido: ["mano levantada", "ruido fuerte", "pito por el mismo"],
  pitos_fuertes: ["pitos fuertes", "fuerte", "fuertes", "aumentando", "volumen alto"],
  solo_si_molesta: ["molesta", "solo si molesta", "si le molesta"],
  dos_pitos: ["dos pitos", "alternado", "dos tonos", "un oído primero", "igual en volumen", "dos sonidos"],
  cambie_de_volumen: ["cambie de volumen", "cambio de volumen", "cambio", "volumen", "avise cuando cambie"],
  dictar_palabras: ["palabras", "dictar", "repita", "repetir", "voy a dictar"],
  escucha: ["me escucha", "escucha", "puede oírme"],
  muy_fuerte: ["muy fuerte", "fuerte mi voz", "demasiado fuerte"],
  molesta: ["molesta", "le molesta", "incómodo", "incomoda"],
  dejo_de_escuchar: ["dejó de escuchar", "dejo de escuchar", "ya no escucha", "ya no lo escucha"],
  sonidos_iguales: ["iguales", "sonidos iguales", "escuchó iguales", "mismo volumen", "suenan igual"],
  en_que_oido: ["qué oído", "que oído", "cuál oído", "cual oído", "más fuerte", "por dónde"],
  pa_pa_pa: ["pa pa", "papa"],
};

/**
 * Intenta reconocer una instrucción a partir de texto transcrito (STT).
 *
 * Hace fuzzy matching contra palabras clave de cada instrucción.
 * Retorna la mejor coincidencia o null si no se reconoce nada.
 */
export function matchVoiceToInstruction(transcript: string): Instruction | null {
  if (!transcript || transcript.trim().length < 2) return null;

  const normalized = transcript.toLowerCase()
    .normalize("NFD").replace(/[\u0300-\u036f]/g, "") // quitar acentos
    .replace(/[¿?¡!.,]/g, "")
    .trim();

  let bestMatch: Instruction | null = null;
  let bestScore = 0;

  for (const inst of INSTRUCTIONS) {
    const keywords = VOICE_KEYWORDS[inst.id] ?? [];
    let score = 0;

    for (const kw of keywords) {
      const kwNorm = kw.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      if (normalized.includes(kwNorm)) {
        // Más largo el keyword que matchea, mejor el score
        score = Math.max(score, kwNorm.length);
      }
    }

    // También comparar contra el speech completo de la instrucción
    const speechNorm = inst.speech.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "").replace(/[¿?¡!.,]/g, "");
    // Contar palabras en común
    const transcriptWords = normalized.split(/\s+/);
    const speechWords = speechNorm.split(/\s+/).filter((w) => w.length > 3);
    let wordMatches = 0;
    for (const tw of transcriptWords) {
      if (speechWords.some((sw) => sw.includes(tw) || tw.includes(sw))) {
        wordMatches++;
      }
    }
    if (wordMatches >= 2) {
      score = Math.max(score, wordMatches * 3);
    }

    if (score > bestScore) {
      bestScore = score;
      bestMatch = inst;
    }
  }

  // Requiere un score mínimo para evitar falsos positivos
  return bestScore >= 3 ? bestMatch : null;
}

export function isInstructionCompatible(
  activeMode: ResponseMode,
  transducer: "air" | "bone" | "free",
  hasMasking: boolean,
): boolean {
  if (activeMode === "none") return false;

  switch (activeMode) {
    case "threshold_air":
      return transducer === "air" && !hasMasking;
    case "threshold_bone":
      return transducer === "bone" && !hasMasking;
    case "threshold_air_masked":
      return transducer === "air" && hasMasking;
    case "threshold_bone_masked":
      return transducer === "bone" && hasMasking;
    case "sustained":
    case "sustained_masked":
    case "loudness":
    case "volume_change":
      return true; // Estas son independientes del transductor
    case "binaural":
      return true;
    case "speech_detect":
    case "speech_repeat":
      return true;
    case "question":
      return true;
    default:
      return false;
  }
}
