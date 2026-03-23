/**
 * Modelo de respuesta del paciente para audiometría.
 *
 * El audiómetro presenta un estímulo (tono puro, ruido, etc.) a cierta
 * intensidad, frecuencia, transductor y oído. Este módulo decide si el
 * paciente "levanta la mano" o no, basándose en:
 *
 * - Umbrales reales del oído evaluado (VA/VO)
 * - Crossover: el sonido puede cruzar al oído contralateral
 * - Enmascaramiento: ruido en el oído contralateral eleva su umbral efectivo
 * - Cooperación del paciente (falsos positivos/negativos)
 * - Fatiga (empeora con el tiempo)
 *
 * Patrón: perimetry-patient.ts
 */

import type { AudiometryData, PatientAudioConfig } from "@/modules/audiometry/schema";

// ─── Seeded RNG (mismo patrón que perimetry-patient.ts) ──

function seededRng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

// ─── Tipos ───────────────────────────────────────────────

export type TransducerType = "air" | "bone" | "free";
export type EarSide = "right" | "left";

export interface AudiometryPatientResponse {
  /** El paciente percibió el estímulo */
  heard: boolean;
  /** Tiempo de reacción en ms (null si no escuchó) */
  reactionTimeMs: number | null;
  /** Por dónde escuchó: oído evaluado o crossover al contralateral */
  heardVia: "ipsilateral" | "crossover" | null;
  /** Respondió sin estímulo real (falso positivo) */
  isFalsePositive: boolean;
  /** No respondió aunque debería escuchar (falso negativo) */
  isFalseNegative: boolean;
}

export interface MaskingConfig {
  /** Tipo de ruido de enmascaramiento */
  type: "nbn" | "wn" | "sn" | "pn";
  /** Nivel del ruido en dB HL */
  level: number;
  /** Oído donde se presenta el ruido */
  ear: EarSide;
}

export interface MaskingNeed {
  needed: boolean;
  reason: string;
  /** Nivel mínimo efectivo de enmascaramiento (dB HL) */
  minLevel: number;
  /** Nivel máximo antes de sobre-enmascarar (dB HL) */
  maxLevel: number;
}

// ─── Atenuación interaural ──────────────────────────────

/**
 * Atenuación interaural por transductor.
 * Es la pérdida de energía cuando el sonido cruza de un oído al otro
 * a través del cráneo.
 *
 * Valores conservadores (peor caso clínico):
 * - Supraaural: ~40 dB (varía 40-65 según frecuencia)
 * - Inserto:    ~55 dB (mejor aislamiento)
 * - Óseo:       ~0 dB  (vibra todo el cráneo)
 * - Campo libre: ~0 dB (llega a ambos oídos)
 */
const IA_BY_TRANSDUCER: Record<TransducerType, number> = {
  air: 40,
  bone: 0,
  free: 0,
};

/**
 * Atenuación interaural más precisa por frecuencia (auriculares supraurales).
 * Fuente: valores clínicos convencionales.
 */
const IA_BY_FREQUENCY: Record<number, number> = {
  250: 40,
  500: 40,
  1000: 40,
  1500: 45,
  2000: 45,
  3000: 50,
  4000: 50,
  6000: 55,
  8000: 55,
};

export function getInterauralAttenuation(transducer: TransducerType, frequency?: number): number {
  if (transducer !== "air") return IA_BY_TRANSDUCER[transducer];
  if (frequency && IA_BY_FREQUENCY[frequency] != null) return IA_BY_FREQUENCY[frequency];
  return IA_BY_TRANSDUCER.air;
}

// ─── Helpers para obtener umbrales del paciente ─────────

function getThreshold(
  thresholds: Record<string, number | null | undefined>,
  frequency: number,
): number | null {
  const val = thresholds[String(frequency)];
  return val != null ? val : null;
}

function getEarAirThreshold(data: AudiometryData, ear: EarSide, freq: number): number | null {
  const oido = ear === "right" ? "oidoDerecho" : "oidoIzquierdo";
  return getThreshold((data.umbralesAereos?.[oido] ?? {}) as Record<string, number | null>, freq);
}

function getEarBoneThreshold(data: AudiometryData, ear: EarSide, freq: number): number | null {
  const oido = ear === "right" ? "oidoDerecho" : "oidoIzquierdo";
  return getThreshold((data.umbralesOseos?.[oido] ?? {}) as Record<string, number | null>, freq);
}

/**
 * Obtiene el umbral real del oído según el transductor.
 * - Aéreo/Campo libre: usa umbral de VA
 * - Óseo: usa umbral de VO
 */
function getRealThreshold(
  data: AudiometryData,
  ear: EarSide,
  freq: number,
  transducer: TransducerType,
): number | null {
  if (transducer === "bone") {
    return getEarBoneThreshold(data, ear, freq);
  }
  return getEarAirThreshold(data, ear, freq);
}

// ─── Lógica de crossover ────────────────────────────────

/**
 * Determina si el sonido cruza al oído contralateral.
 * El crossover ocurre cuando:
 *   intensidad_presentada - atenuación_interaural >= umbral_VO_contralateral
 *
 * IMPORTANTE: el crossover SIEMPRE va por vía ósea (el cráneo vibra),
 * por eso se compara contra el umbral VO del contralateral.
 */
function checkCrossover(
  stimulusDb: number,
  transducer: TransducerType,
  freq: number,
  data: AudiometryData,
  nonTestEar: EarSide,
): boolean {
  const ia = getInterauralAttenuation(transducer, freq);
  const crossoverLevel = stimulusDb - ia;

  // El sonido que cruza llega por VO al otro oído
  const nonTestBone = getEarBoneThreshold(data, nonTestEar, freq);
  if (nonTestBone == null) return false;

  return crossoverLevel >= nonTestBone;
}

/**
 * Calcula si el enmascaramiento es efectivo para bloquear el crossover.
 * El masking eleva el umbral efectivo del oído contralateral.
 *
 * Umbral efectivo = max(umbral_real, nivel_masking - corrección)
 * Corrección por tipo de ruido: NBN = 0 dB, WN = -5 dB (menos eficiente)
 */
function isMaskingEffective(
  masking: MaskingConfig,
  nonTestEar: EarSide,
  freq: number,
  data: AudiometryData,
): boolean {
  // El masking debe estar en el oído contralateral
  if (masking.ear !== nonTestEar) return false;

  const nonTestBone = getEarBoneThreshold(data, nonTestEar, freq);
  if (nonTestBone == null) return true; // sin datos, asumimos que funciona

  // El masking es efectivo si su nivel >= umbral VO del oído enmascarado
  const correction = masking.type === "wn" ? -5 : masking.type === "pn" ? -3 : 0;
  const effectiveLevel = masking.level + correction;

  return effectiveLevel >= nonTestBone;
}

// ─── Respuesta del paciente ─────────────────────────────

/**
 * Simula la respuesta del paciente a un estímulo audiométrico.
 *
 * @param freq - Frecuencia del estímulo (Hz)
 * @param stimulusDb - Intensidad presentada (dB HL)
 * @param transducer - Tipo de transductor usado
 * @param testEar - Oído donde se presenta el estímulo
 * @param data - Datos audiométricos del paciente (umbrales reales)
 * @param config - Configuración del comportamiento del paciente
 * @param masking - Configuración de enmascaramiento (null si no hay)
 * @param progress - Progreso del examen (0-1) para fatiga
 * @param seed - Semilla para reproducibilidad
 */
export function simulateAudiometryResponse(
  freq: number,
  stimulusDb: number,
  transducer: TransducerType,
  testEar: EarSide,
  data: AudiometryData,
  config: PatientAudioConfig,
  masking: MaskingConfig | null,
  progress: number,
  seed: number,
): AudiometryPatientResponse {
  const rng = seededRng(seed + freq * 7 + stimulusDb);
  const nonTestEar: EarSide = testEar === "right" ? "left" : "right";

  const fpRate = config.falsePositiveRate ?? 0.03;
  const fnRate = config.falseNegativeRate ?? 0.02;
  const baseReactionMs = config.reactionTimeMs ?? 350;
  const fatigue = config.fatigueFactor ?? 0.1;

  // Fatiga: empeora las tasas de error con el progreso
  const fatigueMultiplier = 1 + fatigue * progress * 2;

  // 1. ¿El oído evaluado escucha el estímulo?
  const testThreshold = getRealThreshold(data, testEar, freq, transducer);
  const testEarHears = testThreshold != null && stimulusDb >= testThreshold;

  // 2. ¿Hay crossover al oído contralateral?
  let crossoverHears = checkCrossover(stimulusDb, transducer, freq, data, nonTestEar);

  // 3. Si hay enmascaramiento, ¿bloquea el crossover?
  if (crossoverHears && masking) {
    if (isMaskingEffective(masking, nonTestEar, freq, data)) {
      crossoverHears = false;
    }
  }

  // 4. El paciente escucha si cualquiera de los dos oídos percibe
  const actuallyHears = testEarHears || crossoverHears;

  // 5. Aplicar factores humanos (falsos positivos/negativos)
  if (!actuallyHears) {
    // No debería escuchar — pero puede ser un falso positivo
    const isFP = rng() < fpRate * fatigueMultiplier * 0.5;
    return {
      heard: isFP,
      reactionTimeMs: isFP ? Math.round(baseReactionMs + rng() * 400) : null,
      heardVia: null,
      isFalsePositive: isFP,
      isFalseNegative: false,
    };
  }

  // Debería escuchar — pero puede fallar (falso negativo)
  const isFN = rng() < fnRate * fatigueMultiplier;
  if (isFN) {
    return {
      heard: false,
      reactionTimeMs: null,
      heardVia: null,
      isFalsePositive: false,
      isFalseNegative: true,
    };
  }

  // Responde correctamente
  const heardVia: "ipsilateral" | "crossover" = testEarHears ? "ipsilateral" : "crossover";

  // Tiempo de reacción: base + variación + fatiga + proximidad al umbral
  const threshold = testEarHears ? (testThreshold ?? 0) : 0;
  const proximityPenalty = testEarHears
    ? Math.max(0, 10 - (stimulusDb - threshold)) * 15
    : 0;

  const rt = Math.round(
    baseReactionMs +
    (rng() - 0.3) * 150 +
    progress * fatigue * 200 +
    proximityPenalty,
  );

  return {
    heard: true,
    reactionTimeMs: Math.max(100, rt),
    heardVia,
    isFalsePositive: false,
    isFalseNegative: false,
  };
}

// ─── Necesidad de enmascaramiento ───────────────────────

/**
 * Determina si se necesita enmascaramiento para una medición.
 *
 * Criterios:
 * - Vía aérea: cuando VA(test) - VO(contralateral) >= atenuación interaural
 * - Vía ósea: cuando existe GAP aéreo-óseo >= 10 dB en el oído evaluado
 *   (la VO puede venir del contralateral si no se enmascara)
 */
export function needsMasking(
  freq: number,
  stimulusDb: number,
  transducer: TransducerType,
  testEar: EarSide,
  data: AudiometryData,
): MaskingNeed {
  const nonTestEar: EarSide = testEar === "right" ? "left" : "right";
  const ia = getInterauralAttenuation(transducer, freq);

  if (transducer === "air" || transducer === "free") {
    // VA: se necesita si VA(test) - VO(contra) >= IA
    const nonTestBone = getEarBoneThreshold(data, nonTestEar, freq);
    if (nonTestBone == null) {
      return { needed: false, reason: "Sin datos de VO contralateral", minLevel: 0, maxLevel: 0 };
    }

    const difference = stimulusDb - nonTestBone;
    if (difference >= ia) {
      // Mínimo: umbral VO contralateral + 10 dB de seguridad
      const minLevel = nonTestBone + 10;
      // Máximo: umbral VO contralateral + IA (evitar sobre-enmascaramiento)
      const testBone = getEarBoneThreshold(data, testEar, freq);
      const maxLevel = (testBone ?? stimulusDb) + ia - 5;

      return {
        needed: true,
        reason: `Diferencia VA(${stimulusDb}) - VO contra(${nonTestBone}) = ${difference} dB ≥ IA(${ia} dB)`,
        minLevel: Math.round(minLevel),
        maxLevel: Math.round(Math.max(minLevel, maxLevel)),
      };
    }

    return { needed: false, reason: "Diferencia insuficiente para crossover", minLevel: 0, maxLevel: 0 };
  }

  // VO: se necesita si hay GAP aéreo-óseo >= 10 dB en el oído NO evaluado
  // (porque la VO llega a ambos oídos, y si el contralateral tiene mejor VO,
  // podríamos estar midiendo el contralateral)
  const nonTestBone = getEarBoneThreshold(data, nonTestEar, freq);
  const testBone = getEarBoneThreshold(data, testEar, freq);

  if (nonTestBone == null || testBone == null) {
    return { needed: false, reason: "Sin datos suficientes de VO", minLevel: 0, maxLevel: 0 };
  }

  // En VO, SIEMPRE puede haber crossover (IA = 0)
  // Se necesita enmascarar si hay GAP en el oído NO evaluado
  const nonTestAir = getEarAirThreshold(data, nonTestEar, freq);
  const nonTestGap = nonTestAir != null ? nonTestAir - nonTestBone : 0;

  if (nonTestGap >= 10) {
    const minLevel = nonTestBone + 10;
    const testAir = getEarAirThreshold(data, testEar, freq);
    const maxLevel = (testAir ?? testBone) + ia - 5;

    return {
      needed: true,
      reason: `GAP contralateral = ${nonTestGap} dB ≥ 10 dB. VO puede venir del otro oído.`,
      minLevel: Math.round(minLevel),
      maxLevel: Math.round(Math.max(minLevel, maxLevel)),
    };
  }

  return { needed: false, reason: "GAP contralateral insuficiente", minLevel: 0, maxLevel: 0 };
}

// ─── Plateau ────────────────────────────────────────────

/**
 * Calcula el rango de plateau para enmascaramiento.
 * El plateau es el rango de niveles de masking donde el umbral
 * del oído evaluado no cambia (= umbral real).
 */
export function calculatePlateau(
  testEar: EarSide,
  freq: number,
  transducer: TransducerType,
  data: AudiometryData,
): { minEffective: number; maxBeforeOver: number; plateauWidth: number } {
  const nonTestEar: EarSide = testEar === "right" ? "left" : "right";
  const ia = getInterauralAttenuation(transducer, freq);

  const nonTestBone = getEarBoneThreshold(data, nonTestEar, freq) ?? 0;
  const testThreshold = getRealThreshold(data, testEar, freq, transducer) ?? 0;

  // Mínimo efectivo: debe superar el umbral VO del contralateral
  const minEffective = nonTestBone + 10;

  // Máximo antes de sobre-enmascarar: el masking cruza al oído evaluado
  // sobre-enmascaramiento = masking_level - IA >= umbral_VO_test
  const testBone = getEarBoneThreshold(data, testEar, freq) ?? testThreshold;
  const maxBeforeOver = testBone + ia - 5;

  const plateauWidth = Math.max(0, maxBeforeOver - minEffective);

  return {
    minEffective: Math.round(minEffective),
    maxBeforeOver: Math.round(maxBeforeOver),
    plateauWidth: Math.round(plateauWidth),
  };
}

// ─── PTA (Pure Tone Average) ────────────────────────────

/**
 * Calcula el PTA (promedio de umbrales a 500, 1000, 2000 Hz por VA).
 */
export function calculatePTA(data: AudiometryData, ear: EarSide): number | null {
  const freqs = [500, 1000, 2000];
  const thresholds = freqs.map((f) => getEarAirThreshold(data, ear, f)).filter((t): t is number => t != null);
  if (thresholds.length === 0) return null;
  return Math.round(thresholds.reduce((a, b) => a + b, 0) / thresholds.length);
}

/**
 * Calcula el GAP aéreo-óseo para una frecuencia y oído.
 */
export function calculateGap(data: AudiometryData, ear: EarSide, freq: number): number | null {
  const air = getEarAirThreshold(data, ear, freq);
  const bone = getEarBoneThreshold(data, ear, freq);
  if (air == null || bone == null) return null;
  return air - bone;
}
