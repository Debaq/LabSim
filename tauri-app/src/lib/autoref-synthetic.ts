/**
 * Genera lecturas sintéticas de autorefractómetro.
 * Simula variabilidad entre mediciones como un equipo real.
 */

function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

export interface AutorefReading {
  sph: number;   // esfera en dioptrías
  cyl: number;   // cilindro (siempre negativo o 0)
  axis: number;  // eje 0-180°
}

export interface AutorefResult {
  readings: AutorefReading[];       // mediciones individuales (típicamente 3)
  average: AutorefReading;          // promedio
  pd: number;                       // distancia pupilar mm
  k1: number;                       // queratometría plano mm / D
  k1Axis: number;
  k2: number;                       // queratometría curvo mm / D
  k2Axis: number;
  confidence: number;               // confiabilidad 0-100
}

export interface AutorefEyeConfig {
  sphere?: number;
  cylinder?: number;
  axis?: number;
  k1?: number;
  k2?: number;
}

export function generateAutorefResult(
  config: AutorefEyeConfig,
  pd: number,
  seed: number,
  alignmentQuality: number,
  numReadings: number = 3,
): AutorefResult {
  const rng = seededRandom(seed);

  const baseSph = config.sphere ?? 0;
  const baseCyl = config.cylinder ?? 0;
  const baseAxis = config.axis ?? 0;
  const baseK1 = config.k1 ?? 43.5;
  const baseK2 = config.k2 ?? 44.2;

  // Variabilidad: peor alineación = más varianza
  const qualityFactor = Math.max(0.3, alignmentQuality / 100);
  const sphVar = 0.25 / qualityFactor;
  const cylVar = 0.15 / qualityFactor;
  const axisVar = 5 / qualityFactor;

  const readings: AutorefReading[] = [];
  for (let i = 0; i < numReadings; i++) {
    readings.push({
      sph: Math.round((baseSph + (rng() - 0.5) * sphVar * 2) * 4) / 4, // pasos de 0.25
      cyl: Math.round((baseCyl + (rng() - 0.5) * cylVar * 2) * 4) / 4,
      axis: Math.round(baseAxis + (rng() - 0.5) * axisVar * 2) % 180,
    });
  }

  // Promedio
  const avgSph = Math.round((readings.reduce((s, r) => s + r.sph, 0) / numReadings) * 4) / 4;
  const avgCyl = Math.round((readings.reduce((s, r) => s + r.cyl, 0) / numReadings) * 4) / 4;
  // Eje promedio circular
  const sinSum = readings.reduce((s, r) => s + Math.sin((r.axis * Math.PI) / 90), 0);
  const cosSum = readings.reduce((s, r) => s + Math.cos((r.axis * Math.PI) / 90), 0);
  const avgAxis = Math.round(((Math.atan2(sinSum, cosSum) * 90) / Math.PI + 180) % 180);

  const confidence = Math.round(qualityFactor * (85 + rng() * 15));

  return {
    readings,
    average: { sph: avgSph, cyl: avgCyl, axis: avgAxis },
    pd: Math.round((pd + (rng() - 0.5) * 1) * 10) / 10,
    k1: Math.round((baseK1 + (rng() - 0.5) * 0.3) * 100) / 100,
    k1Axis: Math.round(baseAxis + (rng() - 0.5) * 10) % 180,
    k2: Math.round((baseK2 + (rng() - 0.5) * 0.3) * 100) / 100,
    k2Axis: (Math.round(baseAxis + (rng() - 0.5) * 10) + 90) % 180,
    confidence,
  };
}

export function formatDiopter(d: number): string {
  const sign = d >= 0 ? "+" : "";
  return `${sign}${d.toFixed(2)}`;
}
