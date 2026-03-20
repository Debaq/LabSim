// Test patterns: coordinates in degrees from fixation
// Each point: [x, y] where + is temporal/superior

// 24-2 pattern: 54 points (excluding blind spot)
export const PATTERN_24_2: [number, number][] = [];
for (let y = -21; y <= 21; y += 6) {
  for (let x = -27; x <= 27; x += 6) {
    // Skip points outside typical 24-2 boundary
    const r = Math.sqrt(x * x + y * y);
    if (r > 27) continue;
    // Skip blind spot region (right eye: ~15,−1.5; left: ~−15,−1.5)
    if (Math.abs(x - 15) < 3 && Math.abs(y + 1.5) < 3) continue;
    if (Math.abs(x + 15) < 3 && Math.abs(y + 1.5) < 3) continue;
    PATTERN_24_2.push([x, y]);
  }
}

// 30-2 pattern: 76 points
export const PATTERN_30_2: [number, number][] = [];
for (let y = -27; y <= 27; y += 6) {
  for (let x = -27; x <= 27; x += 6) {
    const r = Math.sqrt(x * x + y * y);
    if (r > 31) continue;
    if (Math.abs(x - 15) < 3 && Math.abs(y + 1.5) < 3) continue;
    if (Math.abs(x + 15) < 3 && Math.abs(y + 1.5) < 3) continue;
    PATTERN_30_2.push([x, y]);
  }
}

// 10-2 pattern: 68 points (central)
export const PATTERN_10_2: [number, number][] = [];
for (let y = -9; y <= 9; y += 2) {
  for (let x = -9; x <= 9; x += 2) {
    PATTERN_10_2.push([x, y]);
  }
}

export const PATTERNS: Record<string, [number, number][]> = {
  "24-2": PATTERN_24_2,
  "30-2": PATTERN_30_2,
  "10-2": PATTERN_10_2,
};

// Strategies
export type Strategy = "sita-standard" | "sita-fast" | "full-threshold";

// Stimulus sizes (Goldmann)
export const STIMULUS_SIZES = ["I", "II", "III", "IV", "V"] as const;
export type StimulusSize = (typeof STIMULUS_SIZES)[number];

// Normal sensitivity values by eccentricity (dB, age-corrected baseline ~30yo)
export function normalSensitivity(x: number, y: number): number {
  const ecc = Math.sqrt(x * x + y * y);
  // Approximate hill of vision: higher in center, drops with eccentricity
  if (ecc <= 3) return 34;
  if (ecc <= 9) return 32;
  if (ecc <= 15) return 30;
  if (ecc <= 21) return 27;
  return 24;
}

// Grayscale color for a sensitivity value
export function sensitivityToGray(db: number): string {
  // 0 dB = black (not seen), 40 dB = white (full sensitivity)
  const clamped = Math.max(0, Math.min(40, db));
  const val = Math.round((clamped / 40) * 255);
  return `rgb(${val},${val},${val})`;
}

// Point result
export interface PointResult {
  x: number;
  y: number;
  sensitivity: number | null; // dB, null = not yet tested
  seen: boolean;
  totalDeviation?: number;
  patternDeviation?: number;
}

// Reliability indices
export interface ReliabilityIndices {
  fixationLosses: number;
  fixationLossesTotal: number;
  falsePositives: number;
  falsePositivesTotal: number;
  falseNegatives: number;
  falseNegativesTotal: number;
}
