// Rangos de intensidad por frecuencia, transductor y extensión
// Formato: [aéreo, óseo, campo_libre]
// Cada uno: [[min, max_normal], [max_extendido]]
export const INTENSITY_RANGES: Record<string, number[][][]> = {
  "125":   [[[-15, 100], [120]], [[0, 40], [50]],   [[0, 100], [120]]],
  "250":   [[[-15, 100], [120]], [[0, 45], [60]],   [[0, 100], [120]]],
  "500":   [[[-15, 100], [120]], [[0, 50], [60]],   [[0, 100], [120]]],
  "1000":  [[[-15, 100], [120]], [[0, 100], [100]],  [[0, 100], [120]]],
  "2000":  [[[-15, 100], [120]], [[0, 100], [100]],  [[0, 100], [120]]],
  "3000":  [[[-15, 100], [120]], [[0, 100], [100]],  [[0, 100], [120]]],
  "4000":  [[[-15, 100], [120]], [[0, 100], [100]],  [[0, 100], [120]]],
  "6000":  [[[-15, 100], [120]], [[0, 100], [100]],  [[0, 100], [120]]],
  "8000":  [[[-15, 100], [120]], [[0, 100], [100]],  [[0, 100], [120]]],
  "9000":  [[[-15, 65], [65]],   [[0, 65], [65]],    [[0, 65], [65]]],
  "10000": [[[-15, 75], [75]],   [[0, 75], [75]],    [[0, 75], [120]]],
  "11200": [[[-15, 100], [120]], [[0, 100], [100]],  [[0, 100], [75]]],
  "12500": [[[-15, 100], [100]], [[0, 100], [100]],  [[0, 100], [100]]],
  "14000": [[[-15, 60], [60]],   [[0, 60], [60]],    [[0, 60], [60]]],
  "16000": [[[-15, 40], [40]],   [[0, 40], [40]],    [[0, 40], [40]]],
};

// transductor index: 0=aéreo, 1=óseo, 2=campo libre
export function getIntensityRange(
  freq: number,
  transductor: number,
  ext: boolean,
): { min: number; max: number } {
  const key = String(freq);
  const ranges = INTENSITY_RANGES[key] ?? INTENSITY_RANGES["1000"];
  const tr = ranges[transductor] ?? ranges[0];
  const min = tr[0][0];
  const max = ext ? tr[1][0] : tr[0][1];
  return { min, max };
}

// Calibrar intensidad al step más cercano
export function calibrateToStep(val: number, step: number): number {
  return Math.round(val / step) * step;
}

// Frecuencias por modo de prueba y transductor
export function getFrequencyList(
  transductor: number,
  highFreq: boolean,
): number[] {
  // Base: 125-8000 por octavas
  const base = [125, 250, 500, 1000, 2000, 4000, 8000];
  const extras = [3000, 6000];
  const highExtras = [9000, 10000, 11200, 12500, 14000, 16000];

  // Óseo: máximo 4000
  if (transductor === 1) {
    const boneBase = [125, 250, 500, 1000, 2000, 4000];
    return [...boneBase, 3000, 6000].sort((a, b) => a - b);
  }

  // Campo libre: desde 250
  if (transductor === 2) {
    const clBase = [250, 500, 1000, 2000, 4000, 8000];
    return [...clBase, 3000, 6000].sort((a, b) => a - b);
  }

  // Aéreo
  const result = [...base, ...extras];
  if (highFreq) result.push(...highExtras);
  return result.sort((a, b) => a - b);
}

// Reglas de estímulos habilitados por canal
export type StimType = "tone" | "fm" | "speech" | "nbn" | "wn" | "sn" | "pn";

export function getEnabledStimuli(channel: 0 | 1): StimType[] {
  if (channel === 0) {
    // CH0: Tono, FM, Habla habilitados. NBN, WN, PN, SN deshabilitados
    // (solo se habilita SN cuando el otro canal tiene Habla)
    return ["tone", "fm", "speech"];
  }
  // CH1: Tono, NBN, SN habilitados. FM, Habla, WN, PN deshabilitados
  return ["tone", "nbn", "sn"];
}

// Pulsátil: tiempos en ms
export const PULSATILE_ON = 500;   // 50 ciclos * 10ms
export const PULSATILE_OFF = 500;  // 50 ciclos * 10ms

// Alternado: tiempos en ciclos de 100ms
export const ALTERNATE_IPSI = 7;   // 700ms ipsi
export const ALTERNATE_SILENCE = 3; // 300ms silencio
