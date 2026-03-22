/**
 * Generador sintético para tomografía Scheimpflug.
 *
 * Genera:
 * 1. Corte Scheimpflug (imagen de cámara anterior en sección)
 * 2. Mapas de elevación anterior y posterior
 * 3. Mapa paquimétrico punto a punto
 * 4. Índices de cámara anterior
 */

import type { ScheimpflugEyeConfig } from "@/modules/scheimpflug/schema";

// ─── Seeded RNG ──────────────────────────────────────

function rng(seed: number) {
  let s = seed;
  return () => { s = (s * 1664525 + 1013904223) & 0xFFFFFFFF; return (s >>> 0) / 0xFFFFFFFF; };
}

type Severity = "leve" | "moderado" | "severo";

function sevFactor(sev: Severity): number {
  return sev === "leve" ? 0.35 : sev === "moderado" ? 0.65 : 1.0;
}

// ─── Corte Scheimpflug ───────────────────────────────

export interface ScheimpflugCrossSection {
  /** Perfil de la superficie anterior corneal: x (mm) → y (µm elevación) */
  anteriorSurface: { x: number; y: number }[];
  /** Perfil de la superficie posterior corneal */
  posteriorSurface: { x: number; y: number }[];
  /** Perfil anterior del cristalino */
  lensAnterior: { x: number; y: number }[];
  /** Perfil posterior del cristalino */
  lensPosterior: { x: number; y: number }[];
  /** Profundidad de cámara anterior (mm) */
  acd: number;
  /** Posición del iris (simplificado) */
  irisY: number;
}

/**
 * Genera los perfiles del corte Scheimpflug.
 * Cada superficie es una curva que representa la sección transversal.
 */
export function generateCrossSection(
  config: ScheimpflugEyeConfig,
  seed: number,
): ScheimpflugCrossSection {
  const r = rng(seed);
  const sf = sevFactor((config.severidad ?? "moderado") as Severity);
  const path = config.cornealPathology ?? "normal";

  // Parámetros corneales
  const cct = (config.cct ?? 545) / 1000; // mm
  const acd = config.acd ?? 3.2 + (r() - 0.5) * 0.6;
  const lensThickness = config.lensThickness ?? 4.0 + (r() - 0.5) * 0.5;

  // Radios de curvatura (derivados de K)
  const k1Ant = config.k1Anterior ?? 43.5 + (r() - 0.5) * 1.5;
  const rAnt = 337.5 / k1Ant; // radio anterior en mm
  const k1Post = config.k1Posterior ?? -6.4 + (r() - 0.5) * 0.3;
  const rPost = 337.5 / Math.abs(k1Post);

  // Generar superficies
  const anteriorSurface: { x: number; y: number }[] = [];
  const posteriorSurface: { x: number; y: number }[] = [];
  const lensAnterior: { x: number; y: number }[] = [];
  const lensPosterior: { x: number; y: number }[] = [];

  const halfWidth = 4.5; // mm, mitad del diámetro corneal visible
  const steps = 100;

  for (let i = 0; i <= steps; i++) {
    const x = -halfWidth + (i / steps) * halfWidth * 2;
    const xNorm = x / halfWidth; // -1 a 1

    // Superficie anterior: parábola basada en radio de curvatura
    let yAnt = (x * x) / (2 * rAnt);

    // Patología: keratoconus agrega protuberancias
    if (path === "keratoconus") {
      const coneOffset = 0.8 + r() * 0.4; // descentrado inferior
      yAnt -= sf * 0.08 * Math.exp(-((x - coneOffset) ** 2) / 0.8);
    }
    if (path === "corneal-edema") {
      yAnt += sf * 0.03 * (1 - xNorm * xNorm); // engrosamiento central
    }

    anteriorSurface.push({ x, y: yAnt });

    // Superficie posterior: similar pero con CCT de separación
    let thickness = cct;
    // Engrosamiento periférico natural
    thickness += 0.04 * (xNorm * xNorm);
    // Patología
    if (path === "keratoconus") {
      const coneOffset = 0.8 + r() * 0.3;
      thickness -= sf * 0.06 * Math.exp(-((x - coneOffset) ** 2) / 1.2);
    }
    if (path === "corneal-edema") thickness += sf * 0.15 * (1 - xNorm * xNorm);
    if (path === "fuchs-dystrophy") thickness += sf * 0.08 * (1 - xNorm * xNorm * 0.5);

    const yPost = yAnt + thickness;
    posteriorSurface.push({ x, y: yPost });

    // Cristalino (solo zona central, ±3mm)
    if (Math.abs(x) <= 3.5) {
      const xLens = x / 3.5;
      const lensRant = 10 + (r() - 0.5) * 1; // radio anterior cristalino ~10mm
      const lensRpost = -6 + (r() - 0.5) * 0.5; // radio posterior ~-6mm

      const yLensAnt = yPost + acd + (xLens * xLens) * 0.3;
      const yLensPost = yLensAnt + lensThickness - (xLens * xLens) * 0.5;

      lensAnterior.push({ x, y: yLensAnt });
      lensPosterior.push({ x, y: yLensPost });
    }
  }

  const irisY = posteriorSurface[Math.floor(steps / 2)].y + acd * 0.15;

  return { anteriorSurface, posteriorSurface, lensAnterior, lensPosterior, acd, irisY };
}

// ─── Mapas de elevación ──────────────────────────────

export interface ElevationMapData {
  anterior: Float32Array; // µm respecto a esfera de referencia
  posterior: Float32Array;
  size: number;
}

export function generateElevationMaps(
  config: ScheimpflugEyeConfig,
  size: number,
  seed: number,
): ElevationMapData {
  const r = rng(seed + 300);
  const sf = sevFactor((config.severidad ?? "moderado") as Severity);
  const path = config.cornealPathology ?? "normal";
  const anterior = new Float32Array(size * size);
  const posterior = new Float32Array(size * size);
  const cx = size / 2;
  const radius = size / 2;

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const dx = (x - cx) / radius;
      const dy = (y - cx) / radius;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist > 1) {
        anterior[y * size + x] = NaN;
        posterior[y * size + x] = NaN;
        continue;
      }

      // Elevación anterior: referencia esférica
      let eAnt = (r() - 0.5) * 2; // ruido base ±1µm
      let ePost = (r() - 0.5) * 3;

      // Astigmatismo base
      const angle = Math.atan2(dy, dx);
      const kAxis = ((config.kAxis ?? 90) * Math.PI) / 180;
      eAnt += 3 * dist * dist * Math.cos(2 * (angle - kAxis));
      ePost += 4 * dist * dist * Math.cos(2 * (angle - kAxis));

      // Patologías
      if (path === "keratoconus") {
        const coneX = 0.15 + r() * 0.1;
        const coneY = 0.2 + r() * 0.1;
        const dCone = Math.sqrt((dx - coneX) ** 2 + (dy - coneY) ** 2);
        eAnt += sf * 30 * Math.exp(-(dCone ** 2) / 0.08);
        ePost += sf * 45 * Math.exp(-(dCone ** 2) / 0.1);
      }
      if (path === "pellucid") {
        const band = Math.exp(-((dy - 0.5) ** 2) / 0.04);
        eAnt += sf * 15 * band * (1 - dx * dx);
        ePost += sf * 25 * band * (1 - dx * dx);
      }
      if (path === "post-lasik" || path === "post-prk") {
        const ablation = Math.exp(-(dist ** 2) / 0.15);
        eAnt -= sf * 20 * ablation;
      }

      anterior[y * size + x] = eAnt;
      posterior[y * size + x] = ePost;
    }
  }

  return { anterior, posterior, size };
}

// ─── Mapa paquimétrico ───────────────────────────────

export function generatePachymetryMap(
  config: ScheimpflugEyeConfig,
  size: number,
  seed: number,
): Float32Array {
  const r = rng(seed + 600);
  const sf = sevFactor((config.severidad ?? "moderado") as Severity);
  const path = config.cornealPathology ?? "normal";
  const map = new Float32Array(size * size);
  const cx = size / 2;
  const radius = size / 2;

  const baseCCT = config.cct ?? 545 + (r() - 0.5) * 30;

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const dx = (x - cx) / radius;
      const dy = (y - cx) / radius;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist > 1) { map[y * size + x] = NaN; continue; }

      // Engrosamiento periférico natural
      let thickness = baseCCT + dist * dist * 60 + (r() - 0.5) * 5;

      if (path === "keratoconus") {
        const coneX = 0.15, coneY = 0.2;
        const dCone = Math.sqrt((dx - coneX) ** 2 + (dy - coneY) ** 2);
        thickness -= sf * 120 * Math.exp(-(dCone ** 2) / 0.1);
      }
      if (path === "corneal-edema" || path === "fuchs-dystrophy") {
        thickness += sf * 100 * (1 - dist * 0.5);
      }
      if (path === "post-lasik" || path === "post-prk") {
        thickness -= sf * 60 * Math.exp(-(dist ** 2) / 0.2);
      }

      map[y * size + x] = Math.max(300, thickness);
    }
  }

  return map;
}

// ─── Índices de cámara anterior ──────────────────────

export interface AnteriorChamberIndices {
  k1Ant: number; k2Ant: number; kAvgAnt: number; kAxisAnt: number;
  k1Post: number; k2Post: number;
  cct: number; thinnest: number; thinnestX: number; thinnestY: number;
  acd: number;
  acVolume: number;
  iridocornealAngle: number;
  lensDensity: number;
}

export function computeIndices(
  config: ScheimpflugEyeConfig,
  pachMap: Float32Array,
  size: number,
  seed: number,
): AnteriorChamberIndices {
  const r = rng(seed + 900);

  const k1Ant = config.k1Anterior ?? 43.0 + r() * 1.5;
  const k2Ant = config.k2Anterior ?? k1Ant + 0.5 + r() * 1.5;
  const k1Post = config.k1Posterior ?? -(6.0 + r() * 0.8);
  const k2Post = config.k2Posterior ?? k1Post - (0.2 + r() * 0.4);
  const acd = config.acd ?? 3.0 + r() * 0.8;
  const acVolume = config.acVolume ?? 140 + r() * 50;
  const angle = config.iridocornealAngle ?? 30 + r() * 10;
  const density = config.lensDensity ?? (config.lensStatus === "clear" ? 10 + r() * 8 : 35 + r() * 30);

  // Buscar punto más delgado
  let thinnest = 999;
  let thinnestX = 0, thinnestY = 0;
  const cx = size / 2;
  const radius = size / 2;

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const v = pachMap[y * size + x];
      if (!isNaN(v) && v < thinnest) {
        thinnest = v;
        thinnestX = ((x - cx) / radius) * 4.5;
        thinnestY = ((y - cx) / radius) * 4.5;
      }
    }
  }

  return {
    k1Ant: Math.round(k1Ant * 100) / 100,
    k2Ant: Math.round(k2Ant * 100) / 100,
    kAvgAnt: Math.round(((k1Ant + k2Ant) / 2) * 100) / 100,
    kAxisAnt: config.kAxis ?? Math.round(85 + r() * 10),
    k1Post: Math.round(k1Post * 100) / 100,
    k2Post: Math.round(k2Post * 100) / 100,
    cct: Math.round(config.cct ?? thinnest + 10),
    thinnest: Math.round(thinnest),
    thinnestX: Math.round(thinnestX * 10) / 10,
    thinnestY: Math.round(thinnestY * 10) / 10,
    acd: Math.round(acd * 100) / 100,
    acVolume: Math.round(acVolume),
    iridocornealAngle: Math.round(angle),
    lensDensity: Math.round(density),
  };
}
