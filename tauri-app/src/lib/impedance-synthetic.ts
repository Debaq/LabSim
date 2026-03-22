import type { EarPhysiology } from "@/modules/impedance/schema";

/**
 * Generador sintético de datos de impedanciometría.
 *
 * A partir de los datos fisiológicos del oído (definidos por el docente),
 * genera las curvas y señales que el equipo mostraría.
 * El equipo NO interpreta — solo muestra datos crudos.
 */

// ─── Seeded RNG para reproducibilidad ────────────────

function seededRng(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) & 0xffffffff;
    return (s >>> 0) / 0xffffffff;
  };
}

// ─── Timpanometría ───────────────────────────────────

export interface TympanogramPoint {
  pressure: number; // daPa
  compliance: number; // ml o mmho
}

/**
 * Genera la curva de timpanometría completa.
 *
 * @param ear - Datos fisiológicos del oído
 * @param probeFreq - Frecuencia de la sonda (226, 678, 1000 Hz)
 * @param pressureRange - Rango de presión [min, max] en daPa
 * @param seed - Semilla para reproducibilidad
 * @param variance - Varianza natural (0-1)
 */
export function generateTympanogram(
  ear: EarPhysiology,
  probeFreq: number = 226,
  pressureRange: [number, number] = [-400, 200],
  seed: number = 42,
  variance: number = 0.05,
): TympanogramPoint[] {
  const rng = seededRng(seed);
  const [pMin, pMax] = pressureRange;
  const step = 5; // cada 5 daPa
  const points: TympanogramPoint[] = [];

  const peakCompliance = ear.compliancePeak ?? 0.8;
  const peakPressure = ear.middleEarPressure ?? 0;
  const volume = ear.earCanalVolume ?? 1.0;
  const width = ear.tympWidth ?? 100;
  const isPerforated = ear.perforated ?? false;

  // Ajustar según frecuencia de sonda (1000 Hz tiene curvas más anchas en neonatos)
  const freqFactor = probeFreq === 226 ? 1.0 : probeFreq === 678 ? 1.2 : 1.4;

  for (let p = pMax; p >= pMin; p -= step) {
    let compliance: number;

    if (isPerforated) {
      // Perforación: volumen alto, sin pico — curva plana alta
      compliance = volume + peakCompliance + (rng() - 0.5) * variance * 0.3;
    } else if (peakCompliance < 0.1) {
      // Tipo B (efusión): curva plana baja
      compliance = volume * 0.3 + (rng() - 0.5) * variance * 0.05;
    } else {
      // Curva gaussiana centrada en peakPressure
      const sigma = (width / 2.355) * freqFactor; // FWHM → sigma
      const exponent = -((p - peakPressure) ** 2) / (2 * sigma * sigma);
      compliance = volume + peakCompliance * Math.exp(exponent);

      // Agregar varianza natural
      compliance += (rng() - 0.5) * variance * peakCompliance * 0.15;
    }

    // Clamp a valores realistas
    compliance = Math.max(0, compliance);

    points.push({ pressure: p, compliance: Math.round(compliance * 100) / 100 });
  }

  return points;
}

// ─── Reflejos acústicos ──────────────────────────────

export interface ReflexTrace {
  timeMs: number[];
  amplitude: number[]; // deflexión de compliance en ml
}

/**
 * Genera la traza del reflejo acústico.
 * Si el reflejo está presente a esa intensidad, muestra deflexión.
 * Si no, muestra ruido de fondo.
 *
 * @param threshold - Umbral real del reflejo (null = ausente)
 * @param stimulusDb - Intensidad del estímulo presentado
 * @param seed - Semilla
 * @param variance - Varianza
 */
export function generateReflexTrace(
  threshold: number | null | undefined,
  stimulusDb: number,
  seed: number = 42,
  variance: number = 0.05,
): ReflexTrace {
  const rng = seededRng(seed + stimulusDb);
  const duration = 1500; // ms
  const step = 10; // cada 10ms
  const timeMs: number[] = [];
  const amplitude: number[] = [];

  const isPresent = threshold !== null && threshold !== undefined && stimulusDb >= threshold;
  const stimulusOnset = 200; // estímulo empieza a 200ms
  const stimulusDuration = 1000; // 1 segundo

  for (let t = 0; t < duration; t += step) {
    timeMs.push(t);

    let value = 0;
    const noise = (rng() - 0.5) * variance * 0.02;

    if (isPresent && t >= stimulusOnset && t <= stimulusOnset + stimulusDuration) {
      // Reflejo presente: deflexión proporcional a cuánto supera el umbral
      const overThreshold = stimulusDb - (threshold ?? 0);
      const maxDeflection = 0.05 + overThreshold * 0.005; // ml
      const onset = Math.min(1, (t - stimulusOnset) / 80); // rise time ~80ms
      const offset = t > stimulusOnset + stimulusDuration - 100
        ? Math.max(0, (stimulusOnset + stimulusDuration - t) / 100)
        : 1;
      value = -maxDeflection * onset * offset;
    }

    amplitude.push(value + noise);
  }

  return { timeMs, amplitude };
}

// ─── Deterioro del reflejo ───────────────────────────

export interface ReflexDecayTrace {
  timeMs: number[];
  amplitude: number[];
  decayPercent: number; // porcentaje de decaimiento medido
}

/**
 * Genera la traza de deterioro del reflejo (10 segundos de estimulación sostenida).
 *
 * @param decayPercent - Porcentaje de decaimiento real del oído (0-100)
 * @param seed - Semilla
 */
export function generateReflexDecay(
  decayPercent: number = 0,
  seed: number = 42,
): ReflexDecayTrace {
  const rng = seededRng(seed);
  const duration = 12000; // 12s total (2s baseline + 10s estímulo)
  const step = 20;
  const timeMs: number[] = [];
  const amplitude: number[] = [];
  const stimulusOnset = 2000;
  const stimulusDuration = 10000;
  const initialAmplitude = 0.08; // ml

  for (let t = 0; t < duration; t += step) {
    timeMs.push(t);

    let value = 0;
    const noise = (rng() - 0.5) * 0.003;

    if (t >= stimulusOnset && t <= stimulusOnset + stimulusDuration) {
      const elapsed = t - stimulusOnset;
      const progress = elapsed / stimulusDuration;
      // Decaimiento exponencial
      const decayFactor = 1 - (decayPercent / 100) * (1 - Math.exp(-progress * 3));
      value = -initialAmplitude * decayFactor;

      // Rise rápido al inicio
      const onset = Math.min(1, elapsed / 100);
      value *= onset;
    }

    amplitude.push(value + noise);
  }

  return { timeMs, amplitude, decayPercent };
}

// ─── Función tubárica ────────────────────────────────

export interface EustachianResult {
  /** Curvas de timpanometría: basal, post-Toynbee, post-Valsalva */
  basal: TympanogramPoint[];
  postToynbee: TympanogramPoint[];
  postValsalva: TympanogramPoint[];
}

/**
 * Genera las curvas de función tubárica.
 * Tres timpanogramas: basal, después de Toynbee, después de Valsalva.
 */
export function generateEustachianTest(
  ear: EarPhysiology,
  seed: number = 42,
  variance: number = 0.05,
): EustachianResult {
  const toynbeeShift = ear.toynbeeShift ?? -15;
  const valsalvaShift = ear.valsalvaShift ?? 15;

  const basal = generateTympanogram(ear, 226, [-400, 200], seed, variance);

  // Post-Toynbee: presión del oído medio cambia
  const postToynbeeEar: EarPhysiology = {
    ...ear,
    middleEarPressure: (ear.middleEarPressure ?? 0) + toynbeeShift,
  };
  const postToynbee = generateTympanogram(postToynbeeEar, 226, [-400, 200], seed + 100, variance);

  // Post-Valsalva: presión del oído medio cambia en dirección opuesta
  const postValsalvaEar: EarPhysiology = {
    ...ear,
    middleEarPressure: (ear.middleEarPressure ?? 0) + valsalvaShift,
  };
  const postValsalva = generateTympanogram(postValsalvaEar, 226, [-400, 200], seed + 200, variance);

  return { basal, postToynbee, postValsalva };
}

