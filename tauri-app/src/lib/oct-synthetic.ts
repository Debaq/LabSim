// Synthetic OCT data generation

// Retinal layer names
export const LAYERS = ["ILM", "RNFL", "GCL", "IPL", "INL", "OPL", "ONL", "IS/OS", "RPE"] as const;
export type LayerName = (typeof LAYERS)[number];

// Normal RNFL thickness by sector (µm) — TSNIT order
export const RNFL_NORMAL: Record<string, { mean: number; p5: number; p95: number }> = {
  T: { mean: 70, p5: 50, p95: 90 },
  TS: { mean: 125, p5: 100, p95: 155 },
  TI: { mean: 140, p5: 110, p95: 170 },
  N: { mean: 75, p5: 55, p95: 95 },
  NS: { mean: 105, p5: 80, p95: 130 },
  NI: { mean: 110, p5: 85, p95: 135 },
  S: { mean: 120, p5: 95, p95: 150 },
  I: { mean: 130, p5: 105, p95: 160 },
};

// Normal macular thickness (µm)
export const MACULA_NORMAL = {
  fovea: { mean: 260, sd: 20 },
  parafovea: { mean: 320, sd: 15 },
  perifovea: { mean: 290, sd: 15 },
};

// Seeded random for reproducibility
function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 1664525 + 1013904223) & 0xFFFFFFFF;
    return (s >>> 0) / 0xFFFFFFFF;
  };
}

// Generate B-scan retinal layers (y positions for each layer at each x)
export function generateBScan(
  width: number,
  isMacular: boolean,
  seed: number = 42,
  pathology: "normal" | "glaucoma" | "edema" | "drusen" = "normal",
): { layers: Record<LayerName, number[]>; height: number } {
  const rng = seededRandom(seed);
  const height = 500;
  const layers: Record<string, number[]> = {};
  const baseY = height * 0.3; // Top of retina

  // Foveal depression
  const foveaCenter = width / 2;
  const foveaDip = (x: number) => {
    if (!isMacular) return 0;
    const d = Math.abs(x - foveaCenter) / (width * 0.08);
    return -30 * Math.exp(-d * d);
  };

  // Noise
  const noise = (x: number, amp: number) => {
    return amp * Math.sin(x * 0.05 + rng() * 6) * 0.5 + amp * (rng() - 0.5) * 0.3;
  };

  // Layer offsets (cumulative thickness from ILM)
  const thicknesses: Record<string, number> = {
    ILM: 0,
    RNFL: pathology === "glaucoma" ? 12 : 25,
    GCL: 20,
    IPL: 18,
    INL: 22,
    OPL: 18,
    ONL: pathology === "edema" ? 80 : 45,
    "IS/OS": 15,
    RPE: 12,
  };

  let cumY = 0;
  for (const layer of LAYERS) {
    const arr: number[] = [];
    cumY += thicknesses[layer] ?? 0;
    for (let x = 0; x < width; x++) {
      const fovea = foveaDip(x);
      const n = noise(x, 1.5);
      let y = baseY + cumY + fovea + n;

      // Drusen bumps on RPE
      if (pathology === "drusen" && layer === "RPE") {
        const drusenX = [width * 0.3, width * 0.45, width * 0.6, width * 0.75];
        for (const dx of drusenX) {
          const dist = Math.abs(x - dx);
          if (dist < 15) y += 12 * Math.exp(-(dist * dist) / 50);
        }
      }

      arr.push(y);
    }
    layers[layer] = arr;
  }

  return { layers: layers as Record<LayerName, number[]>, height };
}

// Generate RNFL thickness profile (360 degrees, TSNIT order)
export function generateRNFLProfile(
  seed: number = 42,
  pathology: "normal" | "glaucoma" = "normal",
): { angle: number; thickness: number }[] {
  const rng = seededRandom(seed);
  const result: { angle: number; thickness: number }[] = [];

  for (let deg = 0; deg < 360; deg += 1) {
    // TSNIT: T=0°, S=90°, N=180°, I=270°
    const rad = (deg * Math.PI) / 180;

    // Normal double-hump pattern (thick at S and I)
    let t = 70; // baseline temporal
    t += 55 * Math.exp(-Math.pow((deg - 90) / 30, 2)); // Superior peak
    t += 65 * Math.exp(-Math.pow((deg - 270) / 30, 2)); // Inferior peak
    t += 15 * Math.exp(-Math.pow((deg - 45) / 20, 2)); // TS
    t += 15 * Math.exp(-Math.pow((deg - 315) / 20, 2)); // TI

    // Variation
    t += (rng() - 0.5) * 8;

    // Pathology
    if (pathology === "glaucoma") {
      // Thin superior and inferior
      t -= 25 * Math.exp(-Math.pow((deg - 90) / 40, 2));
      t -= 35 * Math.exp(-Math.pow((deg - 270) / 40, 2));
      t -= 10;
    }

    result.push({ angle: deg, thickness: Math.max(20, Math.round(t)) });
  }

  return result;
}

// Generate macular thickness map (9x9 grid, ETDRS sectors)
export function generateMacularMap(
  seed: number = 42,
  pathology: "normal" | "edema" | "atrophy" = "normal",
): { x: number; y: number; thickness: number }[] {
  const rng = seededRandom(seed);
  const result: { x: number; y: number; thickness: number }[] = [];

  for (let row = -4; row <= 4; row++) {
    for (let col = -4; col <= 4; col++) {
      const r = Math.sqrt(row * row + col * col);
      let t: number;

      if (r < 0.8) {
        t = MACULA_NORMAL.fovea.mean + (rng() - 0.5) * MACULA_NORMAL.fovea.sd;
      } else if (r < 2.5) {
        t = MACULA_NORMAL.parafovea.mean + (rng() - 0.5) * MACULA_NORMAL.parafovea.sd;
      } else {
        t = MACULA_NORMAL.perifovea.mean + (rng() - 0.5) * MACULA_NORMAL.perifovea.sd;
      }

      if (pathology === "edema") {
        t += 80 * Math.exp(-r * r / 4);
      }
      if (pathology === "atrophy") {
        t -= 40 * Math.exp(-r * r / 3);
      }

      result.push({ x: col, y: row, thickness: Math.max(100, Math.round(t)) });
    }
  }

  return result;
}

// Normative color coding
export function normativeColor(value: number, normal: { mean: number; p5: number; p95: number }): string {
  if (value >= normal.p95) return "#4ade80"; // Green - supernormal
  if (value >= normal.mean) return "#4ade80"; // Green
  if (value >= normal.p5) return "#fbbf24"; // Yellow - borderline
  if (value >= normal.p5 * 0.85) return "#f97316"; // Orange
  return "#ef4444"; // Red - outside normal
}

export type Pathology = "normal" | "glaucoma" | "edema" | "drusen" | "atrophy";
