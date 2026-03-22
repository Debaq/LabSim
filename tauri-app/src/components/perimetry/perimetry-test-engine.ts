/**
 * Motor del test de perimetría.
 *
 * Maneja la secuencia de presentaciones de estímulos,
 * la búsqueda de umbral por staircase, catch trials,
 * y la interacción con el modelo de respuesta del paciente.
 *
 * Separado de la UI para poder testearlo y mantenerlo independientemente.
 */

import { PATTERNS, normalSensitivity } from "@/lib/perimetry-config";
import type { Strategy } from "@/lib/perimetry-config";
import {
  getTrueSensitivity,
  simulatePatientResponse,
  getNextStimulus,
  isThresholdDone,
  estimateThreshold,
  type DefectType,
  type Severity,
  type ThresholdSearchState,
  type PatientResponse,
} from "@/lib/perimetry-patient";
import type { VFEyeConfig } from "@/modules/visual-field/schema";

// ─── Types ───────────────────────────────────────────

export interface TestPoint {
  index: number;
  x: number;
  y: number;
  trueSensitivity: number;    // La "verdad" del ojo en este punto
  estimatedThreshold: number | null;  // Lo que el test ha estimado
  presentations: { db: number; responded: boolean; rtMs: number | null }[];
  done: boolean;
}

export interface TestState {
  points: TestPoint[];
  currentPointIndex: number | null;
  currentStimulusDb: number | null;
  phase: "idle" | "presenting" | "waiting" | "done";
  presentationCount: number;
  catchTrialCount: number;
  catchTrialFP: number;      // falsos positivos en catch trials

  // Confiabilidad acumulada
  fixationLosses: number;
  fixationLossesTotal: number;
  falsePositives: number;
  falsePositivesTotal: number;
  falseNegatives: number;
  falseNegativesTotal: number;

  // Timing
  startedAt: number | null;
  elapsedMs: number;
}

export interface TestConfig {
  pattern: string;
  strategy: Strategy;
  eye: "OD" | "OI";
  eyeConfig: VFEyeConfig;
  seed: number;
}

// ─── Init ────────────────────────────────────────────

export function initTestState(config: TestConfig): TestState {
  const coords = PATTERNS[config.pattern] ?? PATTERNS["24-2"];
  const defect = (config.eyeConfig.defecto ?? "normal") as DefectType;
  const severity = (config.eyeConfig.severidad ?? "moderado") as Severity;
  const mdTarget = config.eyeConfig.mdObjetivo ?? null;

  const points: TestPoint[] = coords.map(([x, y], i) => {
    // Para hemianopsia bitemporal, invertir x para OI
    let px = x;
    if (defect === "hemianopsia-bitemporal" && config.eye === "OI") px = -px;

    const trueSens = getTrueSensitivity(px, y, defect, severity, mdTarget, config.seed + i);
    return {
      index: i,
      x, y,
      trueSensitivity: trueSens,
      estimatedThreshold: null,
      presentations: [],
      done: false,
    };
  });

  return {
    points,
    currentPointIndex: null,
    currentStimulusDb: null,
    phase: "idle",
    presentationCount: 0,
    catchTrialCount: 0,
    catchTrialFP: 0,
    fixationLosses: 0,
    fixationLossesTotal: 0,
    falsePositives: 0,
    falsePositivesTotal: 0,
    falseNegatives: 0,
    falseNegativesTotal: 0,
    startedAt: null,
    elapsedMs: 0,
  };
}

// ─── Seleccionar siguiente punto ─────────────────────

export function pickNextPoint(state: TestState): number | null {
  const untested = state.points.filter((p) => !p.done);
  if (untested.length === 0) return null;

  // Priorizar puntos con menos presentaciones (equidad)
  untested.sort((a, b) => a.presentations.length - b.presentations.length);

  // Algo de aleatoriedad para no ser predecible
  const pool = untested.slice(0, Math.max(3, Math.floor(untested.length * 0.3)));
  return pool[Math.floor(Math.random() * pool.length)].index;
}

// ─── Decidir si es catch trial ───────────────────────

export function shouldDoCatchTrial(state: TestState): boolean {
  // ~8% de las presentaciones son catch trials
  if (state.presentationCount < 5) return false;
  return Math.random() < 0.08;
}

// ─── Presentar estímulo ──────────────────────────────

export interface PresentationResult {
  pointIndex: number;
  stimulusDb: number;
  response: PatientResponse;
  isCatchTrial: boolean;
}

/**
 * Ejecuta una presentación: decide qué intensidad, presenta al paciente, obtiene respuesta.
 */
export function executePresentation(
  state: TestState,
  config: TestConfig,
): PresentationResult | null {
  const isCatch = shouldDoCatchTrial(state);

  if (isCatch) {
    // Catch trial: presentar en punto de mancha ciega o sin estímulo real
    const blindSpotIndex = state.points.findIndex((p) =>
      config.eye === "OD" ? (p.x === 15 && p.y === -3) : (p.x === -15 && p.y === -3)
    );
    const catchIndex = blindSpotIndex >= 0 ? blindSpotIndex : state.points[0].index;
    const progress = state.points.filter((p) => p.done).length / state.points.length;

    const response = simulatePatientResponse(
      0, // sensibilidad 0 en mancha ciega
      20, // intensidad arbitraria
      config.eyeConfig,
      progress,
      true, // isCatchTrial
      config.seed + state.presentationCount + 10000,
    );

    return { pointIndex: catchIndex, stimulusDb: 20, response, isCatchTrial: true };
  }

  // Seleccionar punto
  const pointIndex = pickNextPoint(state);
  if (pointIndex === null) return null;

  const point = state.points[pointIndex];

  // Determinar intensidad (staircase)
  const searchState: ThresholdSearchState = {
    pointIndex,
    x: point.x,
    y: point.y,
    presentations: point.presentations.map((p) => ({ db: p.db, responded: p.responded })),
    estimatedThreshold: point.estimatedThreshold,
    done: point.done,
  };

  const stimulusDb = getNextStimulus(searchState, point.trueSensitivity, config.strategy);
  const progress = state.points.filter((p) => p.done).length / state.points.length;

  const response = simulatePatientResponse(
    point.trueSensitivity,
    stimulusDb,
    config.eyeConfig,
    progress,
    false,
    config.seed + state.presentationCount + pointIndex * 100,
  );

  return { pointIndex, stimulusDb, response, isCatchTrial: false };
}

// ─── Aplicar resultado ───────────────────────────────

export function applyPresentation(state: TestState, result: PresentationResult, strategy: Strategy = "sita-standard"): TestState {
  const newState = { ...state };
  newState.presentationCount++;

  // Actualizar fijación
  newState.fixationLossesTotal++;
  if (!result.response.wasFixating) newState.fixationLosses++;

  if (result.isCatchTrial) {
    newState.catchTrialCount++;
    if (result.response.responded) {
      newState.catchTrialFP++;
      newState.falsePositives++;
    }
    newState.falsePositivesTotal++;
    return newState;
  }

  // Actualizar punto
  const points = [...state.points];
  const point = { ...points[result.pointIndex] };

  point.presentations = [
    ...point.presentations,
    { db: result.stimulusDb, responded: result.response.responded, rtMs: result.response.reactionTimeMs },
  ];

  // Actualizar confiabilidad
  if (result.response.isFalsePositive) {
    newState.falsePositives++;
    newState.falsePositivesTotal++;
  }
  if (result.response.isFalseNegative) {
    newState.falseNegatives++;
    newState.falseNegativesTotal++;
  }

  // Verificar si el umbral está determinado
  const searchState: ThresholdSearchState = {
    pointIndex: result.pointIndex,
    x: point.x,
    y: point.y,
    presentations: point.presentations.map((p) => ({ db: p.db, responded: p.responded })),
    estimatedThreshold: point.estimatedThreshold,
    done: point.done,
  };

  if (isThresholdDone(searchState, strategy)) {
    point.done = true;
    point.estimatedThreshold = estimateThreshold(searchState, strategy);
  }

  points[result.pointIndex] = point;
  newState.points = points;
  newState.currentPointIndex = result.pointIndex;
  newState.currentStimulusDb = result.stimulusDb;

  // ¿Terminó el test?
  if (points.every((p) => p.done)) {
    newState.phase = "done";
  }

  return newState;
}

// ─── Cálculo de índices ──────────────────────────────

export function calculateMD(points: TestPoint[]): number | null {
  const done = points.filter((p) => p.done && p.estimatedThreshold !== null);
  if (done.length === 0) return null;

  const totalDev = done.reduce((sum, p) => {
    const norm = normalSensitivity(p.x, p.y);
    return sum + ((p.estimatedThreshold ?? 0) - norm);
  }, 0);

  return Math.round((totalDev / done.length) * 10) / 10;
}

export function calculatePSD(points: TestPoint[]): number | null {
  const done = points.filter((p) => p.done && p.estimatedThreshold !== null);
  if (done.length < 5) return null;

  const md = calculateMD(points) ?? 0;
  const variance = done.reduce((sum, p) => {
    const norm = normalSensitivity(p.x, p.y);
    const dev = (p.estimatedThreshold ?? 0) - norm - md;
    return sum + dev * dev;
  }, 0) / done.length;

  return Math.round(Math.sqrt(variance) * 10) / 10;
}

export function getProgress(state: TestState): number {
  const done = state.points.filter((p) => p.done).length;
  return state.points.length > 0 ? done / state.points.length : 0;
}
