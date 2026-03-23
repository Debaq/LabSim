/**
 * Motor de respuesta del paciente para pruebas con diapasón.
 *
 * Simula el comportamiento del paciente al colocar un diapasón
 * vibrante en diferentes posiciones:
 *
 * - Rinne: mastoides (VO) vs conducto (VA) → cuánto tiempo escucha cada vía
 * - Weber: vértex → lateralización
 * - Schwabach: mastoides → duración comparada con normal
 *
 * El diapasón estándar es de 512 Hz (≈500 Hz en umbrales).
 * La vibración decae exponencialmente con el tiempo.
 */

import type { AudiometryData } from "@/modules/audiometry/schema";
import type { EarSide } from "@/lib/audiometry-patient";

// ─── Constantes ─────────────────────────────────────────

/** Frecuencia del diapasón estándar (Hz). Se mapea a 500 Hz en umbrales */
export const FORK_FREQUENCY = 512;
const THRESHOLD_FREQ = "500";

/** Duración total de vibración del diapasón en segundos (máx teórico) */
const MAX_VIBRATION_SECS = 60;

/** Nivel de salida inicial del diapasón golpeado (dB HL aprox) */
const FORK_INITIAL_DB = 55;

/**
 * Duración normal de percepción por VA y VO para un oído normal.
 * Referencia clínica a 512 Hz.
 */
const NORMAL_VO_SECS = 20;

// ─── Seeded RNG ─────────────────────────────────────────

function seededRng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

// ─── Helpers ────────────────────────────────────────────

function getThreshold(data: AudiometryData, ear: EarSide, via: "air" | "bone"): number | null {
  const oido = ear === "right" ? "oidoDerecho" : "oidoIzquierdo";
  const section = via === "air" ? data.umbralesAereos : data.umbralesOseos;
  const val = section?.[oido]?.[THRESHOLD_FREQ];
  return val != null ? Number(val) : null;
}

/**
 * Calcula el nivel del diapasón (dB) a un tiempo dado.
 * El decaimiento es exponencial: db(t) = initial * e^(-k*t)
 */
function forkLevelAtTime(t: number): number {
  const k = Math.log(FORK_INITIAL_DB / 1) / MAX_VIBRATION_SECS;
  return FORK_INITIAL_DB * Math.exp(-k * t);
}

/**
 * Calcula en qué segundo el nivel del diapasón cae por debajo del umbral.
 * Retorna el tiempo en segundos (0 si nunca escucha, MAX si umbral ≤ 0).
 */
function timeUntilInaudible(thresholdDb: number): number {
  if (thresholdDb <= 0) return MAX_VIBRATION_SECS;
  if (thresholdDb >= FORK_INITIAL_DB) return 0;

  const k = Math.log(FORK_INITIAL_DB / 1) / MAX_VIBRATION_SECS;
  return Math.log(FORK_INITIAL_DB / thresholdDb) / k;
}

// ─── Rinne ──────────────────────────────────────────────

export interface RinneResponse {
  /** Duración percibida por VA (segundos) */
  vaDuration: number;
  /** Duración percibida por VO (segundos) */
  voDuration: number;
  /** Resultado: positivo (VA>VO), negativo (VO>VA), indefinido */
  resultado: "positivo" | "negativo" | "indefinido";
  /** El paciente dice que escucha en este momento (para animación en tiempo real) */
  hearsAtTime: (elapsed: number, via: "air" | "bone") => boolean;
}

export function simulateRinne(ear: EarSide, data: AudiometryData, seed: number): RinneResponse {
  const rng = seededRng(seed + (ear === "right" ? 100 : 200));
  const noise = () => (rng() - 0.5) * 3;

  const airThreshold = getThreshold(data, ear, "air") ?? 0;
  const boneThreshold = getThreshold(data, ear, "bone") ?? 0;

  // Duración que el paciente escucha por cada vía
  const vaTime = Math.max(0, timeUntilInaudible(airThreshold) + noise());
  const voTime = Math.max(0, timeUntilInaudible(boneThreshold) + noise());

  // Resultado según comparación de duraciones
  let resultado: "positivo" | "negativo" | "indefinido";
  const diff = vaTime - voTime;
  if (diff > 2) resultado = "positivo";
  else if (diff < -2) resultado = "negativo";
  else resultado = "indefinido";

  return {
    vaDuration: Math.round(vaTime * 10) / 10,
    voDuration: Math.round(voTime * 10) / 10,
    resultado,
    hearsAtTime: (elapsed: number, via: "air" | "bone") => {
      const threshold = via === "air" ? airThreshold : boneThreshold;
      const level = forkLevelAtTime(elapsed);
      return level >= threshold;
    },
  };
}

// ─── Weber ──────────────────────────────────────────────

export interface WeberResponse {
  /** Lateralización percibida */
  lateralizacion: "derecha" | "izquierda" | "central" | "no-lateraliza";
  /** Texto que el paciente dice */
  patientSays: string;
}

export function simulateWeber(data: AudiometryData, seed: number): WeberResponse {
  const rng = seededRng(seed + 300);

  const rightBone = getThreshold(data, "right", "bone") ?? 0;
  const leftBone = getThreshold(data, "left", "bone") ?? 0;
  const rightAir = getThreshold(data, "right", "air") ?? 0;
  const leftAir = getThreshold(data, "left", "air") ?? 0;

  const rightType = data.tipoPerdida?.oidoDerecho ?? "normal";
  const leftType = data.tipoPerdida?.oidoIzquierdo ?? "normal";

  const rightGap = rightAir - rightBone;
  const leftGap = leftAir - leftBone;

  let lat: "derecha" | "izquierda" | "central" | "no-lateraliza";

  // Conductiva: lateraliza al oído con más GAP (el enfermo)
  const rightConductiva = rightType === "conductiva" || rightType === "mixta";
  const leftConductiva = leftType === "conductiva" || leftType === "mixta";
  const rightSN = rightType.startsWith("sensorioneural");
  const leftSN = leftType.startsWith("sensorioneural");

  if (rightConductiva && !leftConductiva && rightGap >= 15) {
    lat = "derecha";
  } else if (leftConductiva && !rightConductiva && leftGap >= 15) {
    lat = "izquierda";
  } else if (rightSN && !leftSN && rightBone > leftBone + 10) {
    lat = "izquierda"; // lateraliza al oído sano
  } else if (leftSN && !rightSN && leftBone > rightBone + 10) {
    lat = "derecha"; // lateraliza al oído sano
  } else if (rightConductiva && leftConductiva) {
    // Ambos conductivos: lateraliza al que tiene más GAP
    if (rightGap > leftGap + 5) lat = "derecha";
    else if (leftGap > rightGap + 5) lat = "izquierda";
    else lat = "central";
  } else if (rightSN && leftSN) {
    // Ambos sensorioneurales: lateraliza al de mejor VO
    if (rightBone < leftBone - 10) lat = "derecha";
    else if (leftBone < rightBone - 10) lat = "izquierda";
    else lat = "central";
  } else {
    // Simétricos o caso complejo → central con un poco de ruido
    const jitter = (rng() - 0.5) * 8;
    const boneDiff = rightBone - leftBone + jitter;
    if (Math.abs(boneDiff) < 5) lat = "central";
    else lat = boneDiff < 0 ? "derecha" : "izquierda";
  }

  const says: Record<string, string> = {
    derecha: "Lo escucho más por el lado derecho",
    izquierda: "Lo escucho más por el lado izquierdo",
    central: "Lo escucho igual por ambos lados",
    "no-lateraliza": "No sabría decir por dónde lo escucho más",
  };

  return { lateralizacion: lat, patientSays: says[lat] };
}

// ─── Schwabach ──────────────────────────────────────────

export interface SchwabachResponse {
  /** Duración percibida por VO en segundos */
  durationSecs: number;
  /** Duración normal de referencia */
  normalDurationSecs: number;
  /** Resultado comparativo */
  resultado: "normal" | "acortado" | "alargado";
  /** Diferencia en segundos respecto a normal */
  differencesSecs: number;
  /** Función para animación en tiempo real */
  hearsAtTime: (elapsed: number) => boolean;
}

export function simulateSchwabach(ear: EarSide, data: AudiometryData, seed: number): SchwabachResponse {
  const rng = seededRng(seed + (ear === "right" ? 400 : 500));
  const noise = () => (rng() - 0.5) * 2;

  const boneThreshold = getThreshold(data, ear, "bone") ?? 0;
  const type = ear === "right"
    ? (data.tipoPerdida?.oidoDerecho ?? "normal")
    : (data.tipoPerdida?.oidoIzquierdo ?? "normal");

  const patientDuration = Math.max(0, timeUntilInaudible(boneThreshold) + noise());

  // Duración normal de referencia (examinador con audición normal)
  const normalDuration = NORMAL_VO_SECS + noise();

  const diff = patientDuration - normalDuration;

  let resultado: "normal" | "acortado" | "alargado";
  if (type === "conductiva" || type === "mixta") {
    // Conductivo: puede escuchar VO más tiempo que lo normal (alargado)
    resultado = diff > 3 ? "alargado" : Math.abs(diff) <= 3 ? "normal" : "acortado";
  } else if (type === "sensorioneural-coclear" || type === "sensorioneural-retrococlear") {
    // Sensorioneural: escucha menos tiempo (acortado)
    resultado = diff < -3 ? "acortado" : Math.abs(diff) <= 3 ? "normal" : "alargado";
  } else {
    resultado = Math.abs(diff) <= 3 ? "normal" : diff > 0 ? "alargado" : "acortado";
  }

  return {
    durationSecs: Math.round(patientDuration * 10) / 10,
    normalDurationSecs: Math.round(normalDuration * 10) / 10,
    resultado,
    differencesSecs: Math.round(diff * 10) / 10,
    hearsAtTime: (elapsed: number) => {
      const level = forkLevelAtTime(elapsed);
      return level >= boneThreshold;
    },
  };
}
