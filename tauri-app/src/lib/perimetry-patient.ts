/**
 * Modelo de respuesta del paciente para campimetría.
 *
 * El equipo presenta un estímulo a cierta intensidad en un punto del campo.
 * Este módulo decide si el paciente "presiona el botón" o no,
 * basándose en:
 * - Sensibilidad real del punto (del defecto configurado)
 * - Cooperación del paciente (falsos positivos/negativos)
 * - Fatiga (empeora con el tiempo)
 * - Fijación (se mueve del punto de fijación)
 * - Tiempo de reacción (variable)
 */

import { normalSensitivity } from "@/lib/perimetry-config";
import type { VFEyeConfig } from "@/modules/visual-field/schema";

// ─── Seeded RNG ──────────────────────────────────────

function seededRng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

// ─── Sensibilidad real por punto ─────────────────────

export type DefectType = NonNullable<VFEyeConfig["defecto"]>;
export type Severity = NonNullable<VFEyeConfig["severidad"]>;

/**
 * Calcula la sensibilidad real de un punto del campo visual (dB).
 * Esto es la "verdad" del ojo — lo que el paciente realmente puede ver.
 */
export function getTrueSensitivity(
  x: number,
  y: number,
  defect: DefectType,
  severity: Severity,
  mdTarget: number | null,
  seed: number,
): number {
  const rng = seededRng(seed + x * 100 + y);
  const norm = normalSensitivity(x, y);
  const sevFactor = severity === "leve" ? 0.4 : severity === "moderado" ? 0.7 : 1.0;
  const noise = (rng() - 0.5) * 3; // variación fisiológica natural

  let loss = 0;

  switch (defect) {
    case "normal":
      return Math.max(0, Math.min(40, Math.round(norm + noise)));
    case "escotoma-arcuato-sup":
      if (y < -3 && x > -3) loss = 18 * sevFactor * Math.exp(-((y + 12) ** 2) / 120);
      break;
    case "escotoma-arcuato-inf":
      if (y > 3 && x > -3) loss = 18 * sevFactor * Math.exp(-((y - 12) ** 2) / 120);
      break;
    case "escotoma-arcuato-doble":
      if (y < -3 && x > -3) loss = 16 * sevFactor * Math.exp(-((y + 12) ** 2) / 120);
      if (y > 3 && x > -3) loss += 16 * sevFactor * Math.exp(-((y - 12) ** 2) / 120);
      break;
    case "escalon-nasal":
      if (x > 6) loss = 12 * sevFactor * (y < 0 ? 1 : 0.2);
      break;
    case "hemianopsia-homonima-der":
      if (x > 0) loss = 28 * sevFactor;
      break;
    case "hemianopsia-homonima-izq":
      if (x < 0) loss = 28 * sevFactor;
      break;
    case "hemianopsia-bitemporal":
      if (x < 0) loss = 28 * sevFactor;
      break;
    case "cuadrantanopsia-sup":
      if (y > 0 && x > 0) loss = 26 * sevFactor;
      break;
    case "cuadrantanopsia-inf":
      if (y < 0 && x > 0) loss = 26 * sevFactor;
      break;
    case "depresion-general":
      loss = 10 * sevFactor;
      break;
    case "isla-central": {
      const ecc = Math.sqrt(x * x + y * y);
      if (ecc > 10) loss = 25 * sevFactor;
      break;
    }
    case "constriccion-periferica": {
      const ecc = Math.sqrt(x * x + y * y);
      if (ecc > 15) loss = 22 * sevFactor;
      else if (ecc > 10) loss = 12 * sevFactor;
      break;
    }
  }

  let sensitivity = norm - loss + noise;

  if (mdTarget !== null) {
    const currentDev = sensitivity - norm;
    const adjustment = (mdTarget - currentDev) * 0.3;
    sensitivity += adjustment;
  }

  return Math.max(0, Math.min(40, Math.round(sensitivity)));
}

// ─── Modelo de respuesta del paciente ────────────────

export interface PatientResponse {
  /** El paciente presionó el botón */
  responded: boolean;
  /** Tiempo de reacción en ms (null si no respondió) */
  reactionTimeMs: number | null;
  /** El paciente estaba fijando correctamente */
  wasFixating: boolean;
  /** Fue un falso positivo (respondió sin estímulo real) */
  isFalsePositive: boolean;
  /** Fue un falso negativo (no respondió aunque debería ver) */
  isFalseNegative: boolean;
}

/**
 * Simula la respuesta del paciente a un estímulo.
 *
 * @param trueSensitivity - Sensibilidad real del punto (dB)
 * @param stimulusDb - Intensidad del estímulo presentado (dB)
 * @param config - Configuración del comportamiento del paciente
 * @param progress - Progreso del test (0-1) para fatiga
 * @param isCatchTrial - Si es un catch trial (sin estímulo) para medir falsos positivos
 * @param seed - Semilla para reproducibilidad
 */
export function simulatePatientResponse(
  trueSensitivity: number,
  stimulusDb: number,
  config: VFEyeConfig,
  progress: number,
  isCatchTrial: boolean,
  seed: number,
): PatientResponse {
  const rng = seededRng(seed);

  const fpRate = config.falsePositiveRate ?? 0.03;
  const fnRate = config.falseNegativeRate ?? 0.02;
  const flRate = config.fixationLossRate ?? 0.05;
  const baseReactionMs = config.reactionTimeMs ?? 300;
  const fatigue = config.fatigueFactor ?? 0.1;

  // Fatiga: empeora las tasas de error con el progreso del test
  const fatigueMultiplier = 1 + fatigue * progress * 2;

  // Fijación
  const wasFixating = rng() > (flRate * fatigueMultiplier);

  if (isCatchTrial) {
    // Catch trial: no hay estímulo real
    const isFP = rng() < (fpRate * fatigueMultiplier);
    return {
      responded: isFP,
      reactionTimeMs: isFP ? Math.round(baseReactionMs + rng() * 200) : null,
      wasFixating,
      isFalsePositive: isFP,
      isFalseNegative: false,
    };
  }

  // ¿El paciente puede ver el estímulo?
  // Si el estímulo es más brillante que la sensibilidad del punto → sí lo ve
  // Más precisamente: el estímulo en dB atenuación. 0dB = máximo brillo.
  // Si trueSensitivity = 30dB, el paciente ve estímulos de 10dB (40-30) o más brillantes.
  // Estímulos se presentan como atenuación: 0dB = más brillante.
  // Simplificación: si stimulusDb <= trueSensitivity → lo ve

  const sees = stimulusDb <= trueSensitivity;

  if (sees) {
    // Debería responder, pero puede fallar (falso negativo por fatiga/distracción)
    const isFN = rng() < (fnRate * fatigueMultiplier);
    if (isFN) {
      return {
        responded: false,
        reactionTimeMs: null,
        wasFixating,
        isFalsePositive: false,
        isFalseNegative: true,
      };
    }

    // Responde correctamente
    // Tiempo de reacción: base + variación + fatiga
    const rt = Math.round(
      baseReactionMs +
      (rng() - 0.3) * 150 +
      progress * fatigue * 200 +
      // Peor tiempo de reacción si el estímulo está cerca del umbral
      Math.max(0, (trueSensitivity - stimulusDb - 5)) * 10
    );

    return {
      responded: true,
      reactionTimeMs: Math.max(100, rt),
      wasFixating,
      isFalsePositive: false,
      isFalseNegative: false,
    };
  } else {
    // No puede ver el estímulo — no debería responder
    // Pero puede ser un falso positivo
    const isFP = rng() < (fpRate * fatigueMultiplier * 0.5); // menos probable sin estímulo
    return {
      responded: isFP,
      reactionTimeMs: isFP ? Math.round(baseReactionMs + rng() * 400) : null,
      wasFixating,
      isFalsePositive: isFP,
      isFalseNegative: false,
    };
  }
}

// ─── Algoritmos de búsqueda de umbral por protocolo ──

export type Strategy = "sita-standard" | "sita-fast" | "full-threshold";

export interface ThresholdSearchState {
  pointIndex: number;
  x: number;
  y: number;
  presentations: { db: number; responded: boolean }[];
  estimatedThreshold: number | null;
  done: boolean;
}

/**
 * Configuración de staircase por protocolo.
 *
 * SITA Standard: 4dB grueso → 2dB fino, 2 reversiones en fino, máx 8 presentaciones
 * SITA Fast: 4dB grueso → 2dB fino, 1 reversión en fino, máx 4 presentaciones (extrapola)
 * Full Threshold: 4dB grueso → 2dB fino, 2 reversiones en fino, máx 10 presentaciones
 */
interface StaircaseConfig {
  coarseStep: number;
  fineStep: number;
  coarsePresentations: number; // cuántas presentaciones antes de pasar a fino
  requiredReversals: number;
  maxPresentations: number;
}

const STAIRCASE_CONFIGS: Record<Strategy, StaircaseConfig> = {
  "sita-standard": { coarseStep: 4, fineStep: 2, coarsePresentations: 2, requiredReversals: 2, maxPresentations: 8 },
  "sita-fast": { coarseStep: 4, fineStep: 2, coarsePresentations: 1, requiredReversals: 1, maxPresentations: 4 },
  "full-threshold": { coarseStep: 4, fineStep: 2, coarsePresentations: 3, requiredReversals: 2, maxPresentations: 10 },
};

/**
 * Decide la siguiente intensidad a presentar para un punto.
 * El algoritmo varía según el protocolo seleccionado.
 */
export function getNextStimulus(
  state: ThresholdSearchState,
  _trueSensitivity: number,
  strategy: Strategy = "sita-standard",
): number {
  const { presentations } = state;
  const cfg = STAIRCASE_CONFIGS[strategy];

  if (presentations.length === 0) {
    const norm = normalSensitivity(state.x, state.y);
    return Math.round(norm);
  }

  const last = presentations[presentations.length - 1];
  const step = presentations.length <= cfg.coarsePresentations ? cfg.coarseStep : cfg.fineStep;

  if (last.responded) {
    return Math.max(0, last.db - step);
  } else {
    return Math.min(40, last.db + step);
  }
}

/**
 * Determina si la búsqueda de umbral está completa según el protocolo.
 */
export function isThresholdDone(
  state: ThresholdSearchState,
  strategy: Strategy = "sita-standard",
): boolean {
  const { presentations } = state;
  const cfg = STAIRCASE_CONFIGS[strategy];

  if (presentations.length >= cfg.maxPresentations) return true;
  if (presentations.length < 2) return false;

  // Contar reversiones en fase fina
  let fineReversals = 0;
  for (let i = Math.max(1, cfg.coarsePresentations); i < presentations.length; i++) {
    if (presentations[i].responded !== presentations[i - 1].responded) {
      fineReversals++;
    }
  }

  return fineReversals >= cfg.requiredReversals;
}

/**
 * Estima el umbral desde las presentaciones.
 * SITA Fast usa la última reversión + extrapolación.
 * Full Threshold promedia las últimas 2 reversiones en fase fina.
 */
export function estimateThreshold(
  state: ThresholdSearchState,
  strategy: Strategy = "sita-standard",
): number {
  const { presentations } = state;
  if (presentations.length === 0) return 0;

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const _cfg = STAIRCASE_CONFIGS[strategy];
  const reversals: number[] = [];

  for (let i = 1; i < presentations.length; i++) {
    if (presentations[i].responded !== presentations[i - 1].responded) {
      reversals.push((presentations[i].db + presentations[i - 1].db) / 2);
    }
  }

  if (strategy === "sita-fast" && reversals.length > 0) {
    // SITA Fast: usa solo la última reversión
    return Math.round(reversals[reversals.length - 1]);
  }

  if (reversals.length >= 2) {
    // Standard y Full Threshold: promedio de últimas 2 reversiones
    const last2 = reversals.slice(-2);
    return Math.round(last2.reduce((a, b) => a + b, 0) / last2.length);
  }

  if (reversals.length === 1) {
    return Math.round(reversals[0]);
  }

  return presentations[presentations.length - 1].db;
}
