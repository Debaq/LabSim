/**
 * Generador sintético compartido para VNG y vHIT.
 *
 * Ambos equipos registran movimiento ocular, pero con diferentes pruebas:
 * - VNG: nistagmo espontáneo, posicional, calórico, oculomotor (sacadas, seguimiento, optocinético)
 * - vHIT: respuesta vestíbulo-ocular a impulsos cefálicos rápidos (6 canales semicirculares)
 */

// ─── Seeded RNG ──────────────────────────────────────

function rng(seed: number) {
  let s = seed;
  return () => { s = (s * 1664525 + 1013904223) & 0xFFFFFFFF; return (s >>> 0) / 0xFFFFFFFF; };
}

type Severity = "leve" | "moderado" | "severo";
function sevFactor(sev: Severity): number {
  return sev === "leve" ? 0.35 : sev === "moderado" ? 0.65 : 1.0;
}

// ─── Tipos compartidos ───────────────────────────────

export interface EyeTracePoint {
  timeMs: number;
  positionDeg: number;  // posición horizontal del ojo (grados)
  velocityDegS: number; // velocidad (°/s)
}

export interface NystagmusParams {
  /** Dirección de la fase rápida: "derecha" | "izquierda" | "ninguno" */
  direction: "derecha" | "izquierda" | "ninguno";
  /** Frecuencia del nistagmo (batidos/s). Normal: 0. Patológico: 1-4 */
  frequency: number;
  /** Amplitud (grados). Normal: 0. Patológico: 2-15 */
  amplitude: number;
  /** Velocidad de fase lenta (°/s). >5 = patológico */
  slowPhaseVelocity: number;
}

// ═══════════════════════════════════════════════════════
// VNG: PRUEBAS VESTIBULARES
// ═══════════════════════════════════════════════════════

// ─── Nistagmo espontáneo ─────────────────────────────

export function generateSpontaneousNystagmus(
  params: NystagmusParams,
  durationMs: number,
  seed: number,
): EyeTracePoint[] {
  const r = rng(seed);
  const points: EyeTracePoint[] = [];
  const step = 5; // cada 5ms (200 Hz, típico de VNG)

  if (params.direction === "ninguno" || params.frequency === 0) {
    // Sin nistagmo: movimiento suave con drift mínimo
    for (let t = 0; t < durationMs; t += step) {
      const drift = (r() - 0.5) * 0.5;
      points.push({ timeMs: t, positionDeg: drift, velocityDegS: drift * 10 });
    }
    return points;
  }

  // Nistagmo: dientes de sierra
  let pos = 0;
  const dir = params.direction === "derecha" ? 1 : -1;
  const slowVel = params.slowPhaseVelocity * (-dir); // fase lenta opuesta a fase rápida
  const period = 1000 / params.frequency;

  for (let t = 0; t < durationMs; t += step) {
    const phase = (t % period) / period;

    if (phase < 0.85) {
      // Fase lenta
      pos += (slowVel * step) / 1000;
      pos += (r() - 0.5) * 0.1; // ruido
    } else {
      // Fase rápida (sacada correctiva)
      pos = (r() - 0.5) * params.amplitude * 0.2;
    }

    // Limitar
    pos = Math.max(-params.amplitude, Math.min(params.amplitude, pos));
    const vel = phase < 0.85 ? slowVel : dir * params.amplitude * 5;

    points.push({ timeMs: t, positionDeg: Math.round(pos * 100) / 100, velocityDegS: Math.round(vel * 10) / 10 });
  }

  return points;
}

// ─── Prueba calórica ─────────────────────────────────

export interface CaloricResult {
  /** Traza de nistagmo inducido por agua caliente/fría */
  trace: EyeTracePoint[];
  /** Velocidad máxima de fase lenta (°/s) */
  peakSPV: number;
  /** Tiempo al pico desde inicio de irrigación (s) */
  timeToPeak: number;
}

export function generateCaloricResponse(
  ear: "derecho" | "izquierdo",
  temperature: "caliente" | "fria",
  /** SPV pico real del paciente (°/s). Normal: 15-50. Arreflexia: <5 */
  peakSpv: number,
  severity: Severity,
  seed: number,
): CaloricResult {
  const r = rng(seed);
  const sf = sevFactor(severity);
  const durationMs = 180000; // 3 minutos
  const step = 10;
  const points: EyeTracePoint[] = [];

  // Dirección del nistagmo según regla COWS
  // Caliente → mismo lado, Fría → lado contrario
  const dir = (temperature === "caliente" && ear === "derecho") || (temperature === "fria" && ear === "izquierdo")
    ? 1 : -1;

  const timeToPeak = 60 + r() * 30; // 60-90 segundos al pico
  let pos = 0;

  for (let t = 0; t < durationMs; t += step) {
    const tSec = t / 1000;
    // Envolvente: sube hasta el pico, luego baja
    const envelope = peakSpv * Math.exp(-((tSec - timeToPeak) ** 2) / (2 * (timeToPeak * 0.6) ** 2));
    const currentSPV = envelope + (r() - 0.5) * 2;

    // Fase lenta
    pos += ((-dir * currentSPV) * step) / 1000;

    // Fase rápida (cada ~300-500ms si hay nistagmo significativo)
    if (currentSPV > 3 && r() < (currentSPV / 100)) {
      pos = (r() - 0.5) * 2;
    }

    pos = Math.max(-20, Math.min(20, pos));
    points.push({ timeMs: t, positionDeg: Math.round(pos * 100) / 100, velocityDegS: Math.round(currentSPV * dir * 10) / 10 });
  }

  return { trace: points, peakSPV: Math.round(peakSpv * 10) / 10, timeToPeak: Math.round(timeToPeak) };
}

// ─── Sacadas ─────────────────────────────────────────

export interface SaccadeResult {
  trace: EyeTracePoint[];
  /** Latencia promedio (ms). Normal: 200-250 */
  avgLatency: number;
  /** Precisión promedio (%). Normal: 90-100 */
  avgAccuracy: number;
  /** Velocidad pico promedio (°/s). Normal: 300-500 */
  avgPeakVelocity: number;
}

export function generateSaccades(
  /** Latencia real del paciente (ms) */
  latency: number,
  /** Precisión (0-1). 1=100% */
  accuracy: number,
  /** Velocidad pico (°/s) */
  peakVelocity: number,
  seed: number,
): SaccadeResult {
  const r = rng(seed);
  const points: EyeTracePoint[] = [];
  const targets = [10, -10, 15, -15, 20, -20, 10, -10]; // posiciones target en grados
  let pos = 0;
  let t = 0;
  const step = 2;

  for (const target of targets) {
    // Periodo de fijación (500-800ms)
    const fixDuration = 500 + r() * 300;
    for (let dt = 0; dt < fixDuration; dt += step) {
      points.push({ timeMs: t, positionDeg: pos + (r() - 0.5) * 0.3, velocityDegS: (r() - 0.5) * 5 });
      t += step;
    }

    // Latencia
    const thisLatency = latency + (r() - 0.5) * 40;
    for (let dt = 0; dt < thisLatency; dt += step) {
      points.push({ timeMs: t, positionDeg: pos + (r() - 0.5) * 0.3, velocityDegS: (r() - 0.5) * 3 });
      t += step;
    }

    // Sacada
    const distance = target - pos;
    const thisAccuracy = accuracy + (r() - 0.5) * 0.1;
    const landing = pos + distance * thisAccuracy;
    const saccadeDuration = Math.abs(distance) / (peakVelocity / 1000) * 2; // ms aprox

    for (let dt = 0; dt < saccadeDuration; dt += step) {
      const progress = dt / saccadeDuration;
      const sigmoidProgress = 1 / (1 + Math.exp(-10 * (progress - 0.5)));
      const currentPos = pos + (landing - pos) * sigmoidProgress;
      const vel = (landing - pos) / (saccadeDuration / 1000) * Math.exp(-((progress - 0.5) ** 2) / 0.08);
      points.push({ timeMs: t, positionDeg: Math.round(currentPos * 100) / 100, velocityDegS: Math.round(vel * 10) / 10 });
      t += step;
    }

    pos = landing;
  }

  return {
    trace: points,
    avgLatency: Math.round(latency),
    avgAccuracy: Math.round(accuracy * 100),
    avgPeakVelocity: Math.round(peakVelocity),
  };
}

// ═══════════════════════════════════════════════════════
// vHIT: IMPULSO CEFÁLICO
// ═══════════════════════════════════════════════════════

export type SemicircularCanal = "lateral-der" | "lateral-izq" | "anterior-der" | "anterior-izq" | "posterior-der" | "posterior-izq";

export interface VHITImpulse {
  headTrace: EyeTracePoint[];
  eyeTrace: EyeTracePoint[];
  gain: number;
  hasCorrectiveSaccade: boolean;
  saccadeType: "none" | "overt" | "covert";
  /** Si este impulso es un artefacto de gafas (no sacada real) */
  isGoggleArtifact: boolean;
}

export interface VHITResult {
  canal: SemicircularCanal;
  impulses: VHITImpulse[];
  avgGain: number;
}

export interface VHITCanalParams {
  gain?: number;
  hasOvertSaccades?: boolean;
  hasCovertSaccades?: boolean;
  overtRate?: number;
  covertRate?: number;
  goggleArtifactRate?: number;
}

/**
 * Genera impulsos vHIT para un canal usando parámetros configurados por el docente.
 * Sacadas overt/covert y artefactos de gafas son controlados explícitamente.
 */
export function generateVHITImpulses(
  canal: SemicircularCanal,
  params: VHITCanalParams = {},
  numImpulses: number = 15,
  seed: number = 42,
): VHITResult {
  const r = rng(seed);
  const impulses: VHITImpulse[] = [];
  const baseGain = params.gain ?? 1.0;
  const goggleArtifactRate = params.goggleArtifactRate ?? 0;

  for (let i = 0; i < numImpulses; i++) {
    const thisGain = baseGain + (r() - 0.5) * 0.12;
    const headPeak = 10 + r() * 10;
    const durationMs = 150 + r() * 50;
    const step = 2;

    // ¿Este impulso es un artefacto de gafas?
    const isArtifact = r() < goggleArtifactRate;

    const headTrace: EyeTracePoint[] = [];
    const eyeTrace: EyeTracePoint[] = [];

    // Pre-impulso
    for (let t = 0; t < 100; t += step) {
      headTrace.push({ timeMs: t, positionDeg: (r() - 0.5) * 0.2, velocityDegS: 0 });
      eyeTrace.push({ timeMs: t, positionDeg: (r() - 0.5) * 0.2, velocityDegS: 0 });
    }

    // Impulso cefálico
    for (let t = 100; t < 100 + durationMs; t += step) {
      const phase = (t - 100) / durationMs;
      const headPos = headPeak * Math.sin(Math.PI * phase);
      const headVel = headPeak * Math.PI / (durationMs / 1000) * Math.cos(Math.PI * phase);

      headTrace.push({ timeMs: t, positionDeg: Math.round(headPos * 100) / 100, velocityDegS: Math.round(headVel) });

      let eyePos = -headPos * thisGain + (r() - 0.5) * 0.3;

      // Artefacto de gafas: el ojo "salta" brevemente en la misma dirección que la cabeza
      if (isArtifact && phase > 0.3 && phase < 0.5) {
        eyePos += headPos * 0.3 * Math.exp(-((phase - 0.4) ** 2) / 0.005);
      }

      eyeTrace.push({ timeMs: t, positionDeg: Math.round(eyePos * 100) / 100, velocityDegS: Math.round(-headVel * thisGain) });
    }

    // Post-impulso: sacadas según configuración del docente
    let saccadeType: "none" | "overt" | "covert" = "none";
    let hasCorrective = false;

    // Decidir si hay sacada según tasas configuradas
    if (params.hasOvertSaccades && r() < (params.overtRate ?? 0.7)) {
      saccadeType = "overt";
      hasCorrective = true;
    } else if (params.hasCovertSaccades && r() < (params.covertRate ?? 0.5)) {
      saccadeType = "covert";
      hasCorrective = true;
    }

    const postDuration = 300;
    const lastEyePos = eyeTrace[eyeTrace.length - 1].positionDeg;
    const error = 0 - lastEyePos;

    for (let t = 100 + durationMs; t < 100 + durationMs + postDuration; t += step) {
      const dt = t - (100 + durationMs);
      let eyePos = lastEyePos;

      if (hasCorrective && Math.abs(error) > 0.5) {
        const saccadeOnset = saccadeType === "overt" ? 15 + r() * 20 : 70 + r() * 40;

        if (dt > saccadeOnset && dt < saccadeOnset + 50) {
          const sProgress = (dt - saccadeOnset) / 50;
          eyePos = lastEyePos + error * Math.min(1, sProgress * 2.5);
        } else if (dt >= saccadeOnset + 50) {
          eyePos = (r() - 0.5) * 0.3;
        }
      } else {
        eyePos = lastEyePos * Math.exp(-dt / 200) + (r() - 0.5) * 0.2;
      }

      headTrace.push({ timeMs: t, positionDeg: (r() - 0.5) * 0.3, velocityDegS: 0 });
      eyeTrace.push({ timeMs: t, positionDeg: Math.round(eyePos * 100) / 100, velocityDegS: 0 });
    }

    impulses.push({
      headTrace,
      eyeTrace,
      gain: Math.round(thisGain * 100) / 100,
      hasCorrectiveSaccade: hasCorrective,
      saccadeType,
      isGoggleArtifact: isArtifact,
    });
  }

  const avgGain = Math.round((impulses.reduce((s, imp) => s + imp.gain, 0) / impulses.length) * 100) / 100;
  return { canal, impulses, avgGain };
}
