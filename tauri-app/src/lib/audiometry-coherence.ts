/**
 * Motor de derivación coherente para audiología.
 *
 * Dado un perfil audiológico (umbrales VA/VO + tipo de pérdida + indicadores),
 * genera resultados coherentes para TODAS las pruebas audiológicas.
 *
 * Principio: TODAS las pruebas SIEMPRE retornan datos completos.
 * La patología determina los VALORES, nunca la presencia/ausencia de resultados.
 * A todos los pacientes se les puede hacer todo — el estudiante deduce el diagnóstico.
 */

import type { AudiometryData, HearingLossType } from "@/modules/audiometry/schema";
import type { LogoaudiometryData } from "@/modules/logoaudiometry/schema";
import type { SupraliminalData } from "@/modules/supraliminal/schema";

// ─── Seeded RNG ──────────────────────────────────────────

function seededRng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

/** Variación gaussiana aproximada (Box-Muller simplificado) */
function gaussianNoise(rng: () => number, stdDev: number): number {
  const u1 = rng();
  const u2 = rng();
  const z = Math.sqrt(-2 * Math.log(Math.max(u1, 0.001))) * Math.cos(2 * Math.PI * u2);
  return z * stdDev;
}

// ─── Tipos del perfil por oído ──────────────────────────

export interface EarProfile {
  airThresholds: Record<string, number>;
  boneThresholds: Record<string, number>;
  ldlValues: Record<string, number>;
  hearingLossType: HearingLossType;
  hasRecruitment: boolean;
  hasToneDecay: boolean;
}

export interface FullAudiologicalProfile {
  right: EarProfile;
  left: EarProfile;
  seed: number;
}

// ─── Helpers ────────────────────────────────────────────

function buildEarProfile(data: AudiometryData, ear: "oidoDerecho" | "oidoIzquierdo"): EarProfile {
  const side = ear === "oidoDerecho" ? "oidoDerecho" : "oidoIzquierdo";
  const toRecord = (obj: Record<string, number | null | undefined>): Record<string, number> => {
    const r: Record<string, number> = {};
    for (const [k, v] of Object.entries(obj)) {
      if (v != null) r[k] = v;
    }
    return r;
  };

  return {
    airThresholds: toRecord(data.umbralesAereos?.[side] ?? {}),
    boneThresholds: toRecord(data.umbralesOseos?.[side] ?? {}),
    ldlValues: toRecord(data.ldl?.[side] ?? {}),
    hearingLossType: data.tipoPerdida?.[side] ?? "normal",
    hasRecruitment: data.reclutamiento?.[side] ?? false,
    hasToneDecay: data.deterioroTonal?.[side] ?? false,
  };
}

export function buildProfile(data: AudiometryData): FullAudiologicalProfile {
  return {
    right: buildEarProfile(data, "oidoDerecho"),
    left: buildEarProfile(data, "oidoIzquierdo"),
    seed: data.patientConfig?.seed ?? 42,
  };
}

/** PTA = promedio VA a 500, 1000, 2000 Hz */
function pta(ear: EarProfile): number {
  const freqs = [500, 1000, 2000];
  const vals = freqs.map((f) => ear.airThresholds[String(f)]).filter((v): v is number => v != null);
  if (vals.length === 0) return 0;
  return Math.round(vals.reduce((a, b) => a + b, 0) / vals.length);
}

/** Mejor umbral VA del oído */
function bestAirThreshold(ear: EarProfile): number {
  const vals = Object.values(ear.airThresholds);
  if (vals.length === 0) return 0;
  return Math.min(...vals);
}

/** GAP promedio a 500, 1000, 2000 Hz */
function averageGap(ear: EarProfile): number {
  const freqs = [500, 1000, 2000];
  const gaps: number[] = [];
  for (const f of freqs) {
    const a = ear.airThresholds[String(f)];
    const b = ear.boneThresholds[String(f)];
    if (a != null && b != null) gaps.push(a - b);
  }
  if (gaps.length === 0) return 0;
  return Math.round(gaps.reduce((a, b) => a + b, 0) / gaps.length);
}

/** Grado de pérdida según PTA */
function degree(ptaVal: number): "normal" | "leve" | "moderado" | "moderado-severo" | "severo" | "profundo" {
  if (ptaVal <= 20) return "normal";
  if (ptaVal <= 40) return "leve";
  if (ptaVal <= 55) return "moderado";
  if (ptaVal <= 70) return "moderado-severo";
  if (ptaVal <= 90) return "severo";
  return "profundo";
}

// ─── LOGOAUDIOMETRÍA ────────────────────────────────────

interface DerivedLogo {
  sdt: number | null;
  srt: number | null;
  umd1: { intensidad: number | null; porcentaje: number | null };
  umd2: { intensidad: number | null; porcentaje: number | null };
  umd3: { intensidad: number | null; porcentaje: number | null };
}

function deriveLogoForEar(ear: EarProfile, rng: () => number): DerivedLogo {
  const ptaVal = pta(ear);
  const type = ear.hearingLossType;
  const noise = () => Math.round(gaussianNoise(rng, 3));

  // SDT ≈ mejor umbral VA - 5 a 10 dB
  const sdt = Math.max(0, bestAirThreshold(ear) - 8 + noise());

  // SRT ≈ PTA ± 5 dB
  const srt = Math.max(0, ptaVal + noise());

  // Discriminación máxima según tipo de pérdida
  let maxDiscrim: number;
  let rollbackAmount: number;

  switch (type) {
    case "normal":
      maxDiscrim = 96 + Math.round(rng() * 4); // 96-100%
      rollbackAmount = 0;
      break;
    case "conductiva":
      maxDiscrim = 92 + Math.round(rng() * 8); // 92-100% (buena discriminación, solo desplazada)
      rollbackAmount = 0;
      break;
    case "sensorioneural-coclear": {
      // Discriminación reducida proporcionalmente al grado
      const d = degree(ptaVal);
      const base = d === "leve" ? 88 : d === "moderado" ? 76 : d === "moderado-severo" ? 64 : d === "severo" ? 48 : 28;
      maxDiscrim = base + Math.round(rng() * 12);
      // Rollback si hay reclutamiento
      rollbackAmount = ear.hasRecruitment ? 12 + Math.round(rng() * 16) : 0;
      break;
    }
    case "sensorioneural-retrococlear": {
      // Discriminación muy reducida
      const d = degree(ptaVal);
      const base = d === "leve" ? 68 : d === "moderado" ? 48 : d === "moderado-severo" ? 32 : 16;
      maxDiscrim = base + Math.round(rng() * 12);
      rollbackAmount = 20 + Math.round(rng() * 20); // rollback marcado
      break;
    }
    case "mixta": {
      const d = degree(ptaVal);
      const base = d === "leve" ? 80 : d === "moderado" ? 68 : d === "moderado-severo" ? 52 : 36;
      maxDiscrim = base + Math.round(rng() * 12);
      rollbackAmount = ear.hasRecruitment ? 8 + Math.round(rng() * 12) : 0;
      break;
    }
  }

  maxDiscrim = Math.min(100, Math.max(0, maxDiscrim));

  // UMD a 3 niveles de intensidad
  // UMD1: SRT + 20 dB → discriminación en ascenso
  // UMD2: SRT + 35 dB → cerca del máximo
  // UMD3: SRT + 50 dB → con posible rollback
  const umd1Int = srt + 20;
  const umd2Int = srt + 35;
  const umd3Int = srt + 50;

  const umd1Pct = Math.min(maxDiscrim, Math.round(maxDiscrim * 0.7 + rng() * 8));
  const umd2Pct = Math.min(100, maxDiscrim + Math.round(gaussianNoise(rng, 2)));
  const umd3Pct = Math.max(0, Math.min(100, maxDiscrim - rollbackAmount + Math.round(gaussianNoise(rng, 3))));

  return {
    sdt, srt,
    umd1: { intensidad: Math.min(100, umd1Int), porcentaje: Math.max(0, umd1Pct) },
    umd2: { intensidad: Math.min(100, umd2Int), porcentaje: Math.max(0, umd2Pct) },
    umd3: { intensidad: Math.min(100, umd3Int), porcentaje: Math.max(0, umd3Pct) },
  };
}

export function deriveLogoaudiometry(profile: FullAudiologicalProfile): LogoaudiometryData {
  const rngR = seededRng(profile.seed + 1000);
  const rngL = seededRng(profile.seed + 2000);

  const right = deriveLogoForEar(profile.right, rngR);
  const left = deriveLogoForEar(profile.left, rngL);

  return {
    sdt: { oidoDerecho: right.sdt, oidoIzquierdo: left.sdt },
    srt: { oidoDerecho: right.srt, oidoIzquierdo: left.srt },
    umd: {
      oidoDerecho: { umd1: right.umd1, umd2: right.umd2, umd3: right.umd3 },
      oidoIzquierdo: { umd1: left.umd1, umd2: left.umd2, umd3: left.umd3 },
    },
  };
}

// ─── SUPRALIMINARES ─────────────────────────────────────

const SUPRA_FREQS = ["500", "1000", "2000", "4000"];

interface DerivedSupra {
  sisi: Record<string, number>;
  carhart: Record<string, number>;
  maspetiol: string;
  luscher: Record<string, number>;
}

function deriveSupraForEar(ear: EarProfile, rng: () => number): DerivedSupra {
  const type = ear.hearingLossType;
  const sisi: Record<string, number> = {};
  const carhart: Record<string, number> = {};
  const luscher: Record<string, number> = {};

  for (const f of SUPRA_FREQS) {
    const airVal = ear.airThresholds[f];
    if (airVal == null) continue;

    const noise = () => Math.round(gaussianNoise(rng, 3));

    // SISI (%)
    switch (type) {
      case "normal":
        sisi[f] = Math.max(0, Math.min(100, 5 + Math.round(rng() * 15) + noise()));
        break;
      case "conductiva":
        sisi[f] = Math.max(0, Math.min(100, 5 + Math.round(rng() * 15) + noise()));
        break;
      case "sensorioneural-coclear":
        sisi[f] = Math.max(0, Math.min(100, 70 + Math.round(rng() * 30) + noise()));
        break;
      case "sensorioneural-retrococlear":
        sisi[f] = Math.max(0, Math.min(100, 0 + Math.round(rng() * 20) + noise()));
        break;
      case "mixta":
        sisi[f] = Math.max(0, Math.min(100, (ear.hasRecruitment ? 50 : 10) + Math.round(rng() * 20) + noise()));
        break;
    }

    // Carhart / Tone Decay (dB de deterioro)
    switch (type) {
      case "normal":
        carhart[f] = Math.max(0, Math.round(rng() * 5));
        break;
      case "conductiva":
        carhart[f] = Math.max(0, Math.round(rng() * 5));
        break;
      case "sensorioneural-coclear":
        carhart[f] = Math.max(0, Math.round(rng() * 10));
        break;
      case "sensorioneural-retrococlear":
        carhart[f] = Math.max(0, 15 + Math.round(rng() * 20));
        break;
      case "mixta":
        carhart[f] = Math.max(0, (ear.hasToneDecay ? 10 : 0) + Math.round(rng() * 10));
        break;
    }

    // Luscher / DLI (dB - umbral diferencial de intensidad)
    switch (type) {
      case "normal":
        luscher[f] = Math.max(0.5, +(2 + rng() * 1.5).toFixed(1));
        break;
      case "conductiva":
        luscher[f] = Math.max(0.5, +(2 + rng() * 1.5).toFixed(1));
        break;
      case "sensorioneural-coclear":
        luscher[f] = Math.max(0.2, +(0.3 + rng() * 0.7).toFixed(1));
        break;
      case "sensorioneural-retrococlear":
        luscher[f] = Math.max(0.5, +(2 + rng() * 2).toFixed(1));
        break;
      case "mixta":
        luscher[f] = Math.max(0.3, +(1 + rng() * 1.5).toFixed(1));
        break;
    }
  }

  // Maspetiol
  let maspetiol: string;
  switch (type) {
    case "sensorioneural-coclear":
      maspetiol = "Positivo";
      break;
    case "mixta":
      maspetiol = ear.hasRecruitment ? "Positivo" : "Dudoso";
      break;
    default:
      maspetiol = "Negativo";
  }

  return { sisi, carhart, maspetiol, luscher };
}

function deriveFowler(profile: FullAudiologicalProfile, rng: () => number): Record<string, { resultado: string | null; diferencia: number | null }> {
  // Fowler (ABLB): compara ecualización de sonoridad entre oídos
  // Solo tiene sentido clínico con asimetría, pero SIEMPRE se puede hacer
  const result: Record<string, { resultado: string | null; diferencia: number | null }> = {};

  for (const f of SUPRA_FREQS) {
    const rightAir = profile.right.airThresholds[f];
    const leftAir = profile.left.airThresholds[f];
    if (rightAir == null || leftAir == null) continue;

    const diff = Math.abs(rightAir - leftAir);
    const worseEar = rightAir > leftAir ? profile.right : profile.left;

    let resultado: string;
    let diferencia: number;

    if (diff < 10) {
      // Simétrico: sin reclutamiento significativo
      resultado = "Sin reclutamiento";
      diferencia = Math.round(rng() * 5);
    } else if (worseEar.hearingLossType === "sensorioneural-coclear" && worseEar.hasRecruitment) {
      // Coclear con reclutamiento: ecualización positiva
      resultado = "Reclutamiento positivo";
      diferencia = Math.max(0, Math.round(diff * (0.2 + rng() * 0.3))); // se reduce mucho
    } else if (worseEar.hearingLossType === "sensorioneural-retrococlear") {
      // Retrococlear: sin reclutamiento o reclutamiento negativo
      resultado = "Reclutamiento negativo";
      diferencia = Math.round(diff + rng() * 10); // se mantiene o aumenta
    } else {
      resultado = "Sin reclutamiento";
      diferencia = Math.round(diff * (0.8 + rng() * 0.2));
    }

    result[f] = { resultado, diferencia };
  }

  return result;
}

export function deriveSupraliminal(profile: FullAudiologicalProfile): SupraliminalData {
  const rngR = seededRng(profile.seed + 3000);
  const rngL = seededRng(profile.seed + 4000);
  const rngF = seededRng(profile.seed + 5000);

  const right = deriveSupraForEar(profile.right, rngR);
  const left = deriveSupraForEar(profile.left, rngL);
  const fowler = deriveFowler(profile, rngF);

  return {
    sisi: { od: right.sisi, oi: left.sisi },
    carhart: { od: right.carhart, oi: left.carhart },
    maspetiol: { od: right.maspetiol, oi: left.maspetiol },
    fowler,
    luscher: { od: right.luscher, oi: left.luscher },
  };
}

// ─── DIAPASONES ─────────────────────────────────────────

export interface DerivedTuningFork {
  rinne: {
    oidoDerecho: "positivo" | "negativo" | "indefinido" | null;
    oidoIzquierdo: "positivo" | "negativo" | "indefinido" | null;
  };
  weber: {
    lateralizacion: "derecha" | "izquierda" | "central" | "no-lateraliza" | null;
  };
  schwabach: {
    oidoDerecho: "normal" | "acortado" | "alargado" | null;
    oidoIzquierdo: "normal" | "acortado" | "alargado" | null;
  };
}

function deriveRinne(ear: EarProfile): "positivo" | "negativo" | "indefinido" {
  // Rinne: compara VA vs VO a 512 Hz (~500 Hz)
  const air = ear.airThresholds["500"];
  const bone = ear.boneThresholds["500"];
  if (air == null || bone == null) return "indefinido";

  const gap = air - bone;

  // Gap ≥ 15 dB → conductivo → Rinne negativo (VO > VA)
  if (gap >= 15) return "negativo";
  // Gap < 15 dB → normal o sensorioneural → Rinne positivo (VA > VO)
  return "positivo";
}

function deriveSchwabach(ear: EarProfile): "normal" | "acortado" | "alargado" {
  const type = ear.hearingLossType;
  switch (type) {
    case "normal":
      return "normal";
    case "conductiva":
      return "alargado";
    case "sensorioneural-coclear":
    case "sensorioneural-retrococlear":
      return "acortado";
    case "mixta": {
      // Depende del componente dominante
      const gap = averageGap(ear);
      const ptaVal = pta(ear);
      const boneAvg = ptaVal - gap;
      // Si la VO está elevada → hay componente sensorioneural → acortado
      if (boneAvg > 20) return "acortado";
      // Si la VO es normal pero hay GAP → predomina conductivo → alargado
      return "alargado";
    }
  }
}

function deriveWeber(profile: FullAudiologicalProfile): "derecha" | "izquierda" | "central" | "no-lateraliza" {
  const rightType = profile.right.hearingLossType;
  const leftType = profile.left.hearingLossType;
  const rightBone500 = profile.right.boneThresholds["500"] ?? 0;
  const leftBone500 = profile.left.boneThresholds["500"] ?? 0;
  const rightGap = averageGap(profile.right);
  const leftGap = averageGap(profile.left);

  // Ambos normales y simétricos → central
  if (rightType === "normal" && leftType === "normal") return "central";

  // Conductiva unilateral → lateraliza al oído ENFERMO
  if (rightType === "conductiva" && leftType === "normal") return "derecha";
  if (leftType === "conductiva" && rightType === "normal") return "izquierda";

  // Sensorioneural unilateral → lateraliza al oído SANO
  if ((rightType === "sensorioneural-coclear" || rightType === "sensorioneural-retrococlear") && leftType === "normal") return "izquierda";
  if ((leftType === "sensorioneural-coclear" || leftType === "sensorioneural-retrococlear") && rightType === "normal") return "derecha";

  // Bilateral asimétrico → según diferencia de VO y GAP
  // Conductiva bilateral: lateraliza al oído con más GAP (peor)
  if (rightType === "conductiva" && leftType === "conductiva") {
    if (rightGap > leftGap + 5) return "derecha";
    if (leftGap > rightGap + 5) return "izquierda";
    return "central";
  }

  // Sensorioneural bilateral: lateraliza al oído con mejor VO (más sano)
  if (
    (rightType === "sensorioneural-coclear" || rightType === "sensorioneural-retrococlear") &&
    (leftType === "sensorioneural-coclear" || leftType === "sensorioneural-retrococlear")
  ) {
    if (rightBone500 < leftBone500 - 10) return "derecha"; // mejor VO derecho
    if (leftBone500 < rightBone500 - 10) return "izquierda";
    return "central";
  }

  // Mixta o combinaciones complejas → comparar VO
  if (rightBone500 < leftBone500 - 10) return "derecha";
  if (leftBone500 < rightBone500 - 10) return "izquierda";

  // Si hay GAP unilateral significativo
  if (rightGap > leftGap + 10) return "derecha";
  if (leftGap > rightGap + 10) return "izquierda";

  return "central";
}

export function deriveTuningFork(profile: FullAudiologicalProfile): DerivedTuningFork {
  return {
    rinne: {
      oidoDerecho: deriveRinne(profile.right),
      oidoIzquierdo: deriveRinne(profile.left),
    },
    weber: {
      lateralizacion: deriveWeber(profile),
    },
    schwabach: {
      oidoDerecho: deriveSchwabach(profile.right),
      oidoIzquierdo: deriveSchwabach(profile.left),
    },
  };
}

// ─── IMPEDANCIOMETRÍA (reflejos esperados) ──────────────

export interface DerivedReflexes {
  reflexIpsi500: number | null;
  reflexIpsi1000: number | null;
  reflexIpsi2000: number | null;
  reflexIpsi4000: number | null;
  reflexContra500: number | null;
  reflexContra1000: number | null;
  reflexContra2000: number | null;
  reflexContra4000: number | null;
  reflexDecay500: number | null;
  reflexDecay1000: number | null;
}

function deriveReflexesForEar(ear: EarProfile, rng: () => number): DerivedReflexes {
  const type = ear.hearingLossType;
  const reflexFreqs = [500, 1000, 2000, 4000];
  const result: Record<string, number | null> = {};

  for (const f of reflexFreqs) {
    const airThreshold = ear.airThresholds[String(f)] ?? 0;
    const noise = Math.round(gaussianNoise(rng, 3));

    // Reflejos ipsilaterales
    let ipsi: number | null;
    switch (type) {
      case "normal":
        ipsi = 70 + Math.round(rng() * 25) + noise; // 70-95 dB sobre 0
        break;
      case "conductiva":
        ipsi = null; // ausentes (cadena osicular alterada)
        break;
      case "sensorioneural-coclear":
        if (airThreshold > 80) {
          ipsi = null; // ausentes en pérdidas severas
        } else {
          // Metz: reflejos presentes pero a menor diferencia (reclutamiento)
          ipsi = airThreshold + 25 + Math.round(rng() * 20) + noise;
          if (ear.hasRecruitment) ipsi = Math.min(ipsi, airThreshold + 40);
        }
        break;
      case "sensorioneural-retrococlear":
        ipsi = null; // ausentes o con decay
        if (rng() < 0.3 && airThreshold < 60) {
          ipsi = airThreshold + 60 + Math.round(rng() * 20); // presentes pero elevados
        }
        break;
      case "mixta":
        ipsi = rng() < 0.5 ? null : airThreshold + 40 + Math.round(rng() * 20) + noise;
        break;
    }
    result[`reflexIpsi${f}`] = ipsi != null ? Math.min(120, Math.max(50, ipsi)) : null;

    // Reflejos contralaterales (generalmente similares, ±5 dB)
    const contraOffset = Math.round(gaussianNoise(rng, 3));
    result[`reflexContra${f}`] = ipsi != null ? Math.min(120, Math.max(50, ipsi + contraOffset)) : null;
  }

  // Reflex decay
  let decay500: number | null = null;
  let decay1000: number | null = null;

  switch (type) {
    case "normal":
      decay500 = Math.max(0, Math.min(100, Math.round(10 + rng() * 20)));
      decay1000 = Math.max(0, Math.min(100, Math.round(10 + rng() * 25)));
      break;
    case "conductiva":
      decay500 = null; // no se puede medir si reflejo ausente
      decay1000 = null;
      break;
    case "sensorioneural-coclear":
      decay500 = Math.max(0, Math.min(100, Math.round(15 + rng() * 25)));
      decay1000 = Math.max(0, Math.min(100, Math.round(15 + rng() * 30)));
      break;
    case "sensorioneural-retrococlear":
      decay500 = Math.max(0, Math.min(100, Math.round(55 + rng() * 40))); // >50% patológico
      decay1000 = Math.max(0, Math.min(100, Math.round(60 + rng() * 40)));
      break;
    case "mixta":
      decay500 = ear.hasToneDecay ? Math.round(45 + rng() * 30) : Math.round(15 + rng() * 25);
      decay1000 = ear.hasToneDecay ? Math.round(50 + rng() * 30) : Math.round(20 + rng() * 25);
      break;
  }

  result.reflexDecay500 = decay500;
  result.reflexDecay1000 = decay1000;

  return result as unknown as DerivedReflexes;
}

export function deriveImpedanceReflexes(profile: FullAudiologicalProfile) {
  const rngR = seededRng(profile.seed + 6000);
  const rngL = seededRng(profile.seed + 7000);
  return {
    oidoDerecho: deriveReflexesForEar(profile.right, rngR),
    oidoIzquierdo: deriveReflexesForEar(profile.left, rngL),
  };
}

// ─── OAE ESPERADAS ──────────────────────────────────────

export interface DerivedOaeFreq {
  frequency: number;
  amplitude: number;
  noiseFloor: number;
  snr: number;
  pass: boolean;
}

function deriveOaeForEar(ear: EarProfile, rng: () => number): DerivedOaeFreq[] {
  const type = ear.hearingLossType;
  const oaeFreqs = [1000, 1500, 2000, 3000, 4000, 6000];
  const results: DerivedOaeFreq[] = [];

  for (const f of oaeFreqs) {
    const airThreshold = ear.airThresholds[String(f)] ?? ear.airThresholds[String(f === 1500 ? 1000 : f === 6000 ? 8000 : f)] ?? 0;
    const noiseFloor = -10 + Math.round(gaussianNoise(rng, 2));

    let amplitude: number;
    switch (type) {
      case "normal":
        amplitude = 8 + Math.round(rng() * 12 + gaussianNoise(rng, 2));
        break;
      case "conductiva":
        // Cóclea OK pero transmisión reducida → OAE pueden estar reducidas
        amplitude = 0 + Math.round(rng() * 6 + gaussianNoise(rng, 2));
        break;
      case "sensorioneural-coclear":
        // Ausentes si umbral > ~30 dB
        if (airThreshold > 30) {
          amplitude = -5 + Math.round(rng() * 5 + gaussianNoise(rng, 2));
        } else {
          amplitude = 3 + Math.round(rng() * 6);
        }
        break;
      case "sensorioneural-retrococlear":
        // Cóclea OK → OAE PRESENTES
        amplitude = 6 + Math.round(rng() * 10 + gaussianNoise(rng, 2));
        break;
      case "mixta":
        amplitude = airThreshold > 30 ? -3 + Math.round(rng() * 4) : 2 + Math.round(rng() * 5);
        break;
    }

    const snr = amplitude - noiseFloor;
    results.push({
      frequency: f,
      amplitude: Math.round(amplitude),
      noiseFloor: Math.round(noiseFloor),
      snr: Math.round(snr),
      pass: snr >= 6,
    });
  }

  return results;
}

export function deriveOae(profile: FullAudiologicalProfile) {
  const rngR = seededRng(profile.seed + 8000);
  const rngL = seededRng(profile.seed + 9000);
  return {
    oidoDerecho: deriveOaeForEar(profile.right, rngR),
    oidoIzquierdo: deriveOaeForEar(profile.left, rngL),
  };
}

// ─── ABR ESPERADO ───────────────────────────────────────

export interface DerivedAbrWave {
  presente: boolean;
  latencia: number | null; // ms
  amplitud: number | null; // µV
}

export interface DerivedAbrEar {
  ondaI: DerivedAbrWave;
  ondaIII: DerivedAbrWave;
  ondaV: DerivedAbrWave;
  intervaloIV: number | null; // ms (I-V)
  intervaloIIII: number | null; // ms (I-III)
  intervaloIIIV: number | null; // ms (III-V)
}

function deriveAbrForEar(ear: EarProfile, rng: () => number): DerivedAbrEar {
  const type = ear.hearingLossType;
  const ptaVal = pta(ear);
  const noise = () => gaussianNoise(rng, 0.1);

  // Latencias normales de referencia (ms) a 80 dB nHL
  const normalI = 1.6;
  const normalIII = 3.7;
  const normalV = 5.6;

  let ondaI: DerivedAbrWave;
  let ondaIII: DerivedAbrWave;
  let ondaV: DerivedAbrWave;

  switch (type) {
    case "normal":
      ondaI = { presente: true, latencia: +(normalI + noise()).toFixed(2), amplitud: +(0.3 + rng() * 0.2).toFixed(2) };
      ondaIII = { presente: true, latencia: +(normalIII + noise()).toFixed(2), amplitud: +(0.25 + rng() * 0.15).toFixed(2) };
      ondaV = { presente: true, latencia: +(normalV + noise()).toFixed(2), amplitud: +(0.4 + rng() * 0.2).toFixed(2) };
      break;

    case "conductiva":
      // Latencias aumentadas uniformemente (todo se retrasa igual)
      {
        const delay = 0.3 + rng() * 0.4; // 0.3-0.7 ms de retraso
        ondaI = { presente: true, latencia: +(normalI + delay + noise()).toFixed(2), amplitud: +(0.2 + rng() * 0.15).toFixed(2) };
        ondaIII = { presente: true, latencia: +(normalIII + delay + noise()).toFixed(2), amplitud: +(0.15 + rng() * 0.1).toFixed(2) };
        ondaV = { presente: true, latencia: +(normalV + delay + noise()).toFixed(2), amplitud: +(0.3 + rng() * 0.15).toFixed(2) };
      }
      break;

    case "sensorioneural-coclear":
      // Umbral elevado, latencias normales, amplitud reducida
      {
        const ampFactor = ptaVal > 60 ? 0.3 : ptaVal > 40 ? 0.5 : 0.7;
        ondaI = { presente: ptaVal < 80, latencia: ptaVal < 80 ? +(normalI + noise()).toFixed(2) : null, amplitud: ptaVal < 80 ? +(0.15 * ampFactor + rng() * 0.1).toFixed(2) : null };
        ondaIII = { presente: ptaVal < 70, latencia: ptaVal < 70 ? +(normalIII + noise()).toFixed(2) : null, amplitud: ptaVal < 70 ? +(0.1 * ampFactor + rng() * 0.08).toFixed(2) : null };
        ondaV = { presente: true, latencia: +(normalV + noise() + 0.1).toFixed(2), amplitud: +(0.2 * ampFactor + rng() * 0.1).toFixed(2) };
      }
      break;

    case "sensorioneural-retrococlear":
      // Onda I normal o casi normal, intervalo I-V PROLONGADO, onda V retrasada/ausente
      {
        ondaI = { presente: true, latencia: +(normalI + noise()).toFixed(2), amplitud: +(0.25 + rng() * 0.15).toFixed(2) };
        ondaIII = { presente: rng() > 0.3, latencia: rng() > 0.3 ? +(normalIII + 0.4 + rng() * 0.5 + noise()).toFixed(2) : null, amplitud: rng() > 0.3 ? +(0.08 + rng() * 0.08).toFixed(2) : null };
        const vPresent = rng() > 0.2;
        ondaV = { presente: vPresent, latencia: vPresent ? +(normalV + 0.8 + rng() * 1.0 + noise()).toFixed(2) : null, amplitud: vPresent ? +(0.1 + rng() * 0.1).toFixed(2) : null };
      }
      break;

    case "mixta":
      {
        const delay = 0.2 + rng() * 0.3;
        const ampFactor = ptaVal > 60 ? 0.4 : 0.6;
        ondaI = { presente: true, latencia: +(normalI + delay + noise()).toFixed(2), amplitud: +(0.15 * ampFactor + rng() * 0.1).toFixed(2) };
        ondaIII = { presente: ptaVal < 70, latencia: ptaVal < 70 ? +(normalIII + delay + noise()).toFixed(2) : null, amplitud: ptaVal < 70 ? +(0.1 * ampFactor + rng() * 0.08).toFixed(2) : null };
        ondaV = { presente: true, latencia: +(normalV + delay + noise() + 0.1).toFixed(2), amplitud: +(0.2 * ampFactor + rng() * 0.1).toFixed(2) };
      }
      break;
  }

  // Intervalos interpeak
  const intervaloIV = ondaI.latencia != null && ondaV.latencia != null ? +(ondaV.latencia - ondaI.latencia).toFixed(2) : null;
  const intervaloIIII = ondaI.latencia != null && ondaIII.latencia != null ? +(ondaIII.latencia - ondaI.latencia).toFixed(2) : null;
  const intervaloIIIV = ondaIII.latencia != null && ondaV.latencia != null ? +(ondaV.latencia - ondaIII.latencia).toFixed(2) : null;

  return { ondaI, ondaIII, ondaV, intervaloIV, intervaloIIII, intervaloIIIV };
}

export function deriveAbr(profile: FullAudiologicalProfile) {
  const rngR = seededRng(profile.seed + 10000);
  const rngL = seededRng(profile.seed + 11000);
  return {
    oidoDerecho: deriveAbrForEar(profile.right, rngR),
    oidoIzquierdo: deriveAbrForEar(profile.left, rngL),
  };
}

// ─── DERIVAR TODO ───────────────────────────────────────

export interface DerivedAll {
  logoaudiometry: LogoaudiometryData;
  supraliminal: SupraliminalData;
  tuningFork: DerivedTuningFork;
  impedanceReflexes: ReturnType<typeof deriveImpedanceReflexes>;
  oae: ReturnType<typeof deriveOae>;
  abr: ReturnType<typeof deriveAbr>;
}

/**
 * Genera datos coherentes para TODAS las pruebas a partir del perfil audiológico.
 * Todas las pruebas SIEMPRE retornan resultados completos.
 */
export function deriveAll(data: AudiometryData): DerivedAll {
  const profile = buildProfile(data);

  return {
    logoaudiometry: deriveLogoaudiometry(profile),
    supraliminal: deriveSupraliminal(profile),
    tuningFork: deriveTuningFork(profile),
    impedanceReflexes: deriveImpedanceReflexes(profile),
    oae: deriveOae(profile),
    abr: deriveAbr(profile),
  };
}
