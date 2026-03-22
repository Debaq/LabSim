// === OCT Synthetic Data Generator — Clinical Accuracy ===

export type OctSeverity = "leve" | "moderado" | "severo";

/** Factor multiplicador de la patología según severidad */
function sevFactor(severity: OctSeverity): number {
  return severity === "leve" ? 0.35 : severity === "moderado" ? 0.65 : 1.0;
}

export const LAYERS = ["ILM", "RNFL", "GCL", "IPL", "INL", "OPL", "ONL", "ELM", "EZ", "RPE"] as const;
export type LayerName = (typeof LAYERS)[number];

export const LAYER_REFLECTIVITY: Record<LayerName, number> = {
  ILM: 0.9, RNFL: 0.85, GCL: 0.25, IPL: 0.7, INL: 0.3,
  OPL: 0.75, ONL: 0.2, ELM: 0.8, EZ: 0.95, RPE: 0.9,
};

export const LAYER_THICKNESS: Record<LayerName, { fovea: number; para: number; peri: number }> = {
  ILM:  { fovea: 2, para: 2, peri: 2 },
  RNFL: { fovea: 8, para: 25, peri: 35 },
  GCL:  { fovea: 12, para: 35, peri: 25 },
  IPL:  { fovea: 15, para: 30, peri: 22 },
  INL:  { fovea: 15, para: 35, peri: 28 },
  OPL:  { fovea: 25, para: 18, peri: 15 },
  ONL:  { fovea: 90, para: 55, peri: 45 },
  ELM:  { fovea: 2, para: 2, peri: 2 },
  EZ:   { fovea: 5, para: 5, peri: 5 },
  RPE:  { fovea: 12, para: 12, peri: 12 },
};

export const RNFL_CLOCK_HOURS: Record<number, { mean: number; p5: number; p1: number }> = {
  1: { mean: 115, p5: 85, p1: 70 }, 2: { mean: 100, p5: 70, p1: 55 },
  3: { mean: 72, p5: 50, p1: 40 },  4: { mean: 80, p5: 55, p1: 42 },
  5: { mean: 110, p5: 80, p1: 65 }, 6: { mean: 140, p5: 110, p1: 90 },
  7: { mean: 145, p5: 115, p1: 95 },8: { mean: 80, p5: 55, p1: 42 },
  9: { mean: 68, p5: 45, p1: 35 },  10: { mean: 75, p5: 52, p1: 40 },
  11: { mean: 120, p5: 90, p1: 72 },12: { mean: 130, p5: 100, p1: 80 },
};

export const RNFL_QUADRANTS: Record<string, { mean: number; p5: number; p1: number }> = {
  S: { mean: 122, p5: 95, p1: 78 }, N: { mean: 84, p5: 58, p1: 45 },
  I: { mean: 132, p5: 105, p1: 88 }, T: { mean: 74, p5: 50, p1: 38 },
};

export const ETDRS_NORMAL: Record<string, { mean: number; p5: number; p1: number }> = {
  fovea: { mean: 255, p5: 225, p1: 210 },
  innerSup: { mean: 325, p5: 300, p1: 285 }, innerNas: { mean: 330, p5: 305, p1: 290 },
  innerInf: { mean: 325, p5: 300, p1: 285 }, innerTemp: { mean: 315, p5: 290, p1: 275 },
  outerSup: { mean: 288, p5: 265, p1: 250 }, outerNas: { mean: 302, p5: 278, p1: 260 },
  outerInf: { mean: 278, p5: 255, p1: 240 }, outerTemp: { mean: 272, p5: 250, p1: 235 },
};

export const GCL_IPL_SECTORS: Record<string, { mean: number; p5: number; p1: number }> = {
  S: { mean: 84, p5: 72, p1: 63 }, SN: { mean: 86, p5: 73, p1: 64 },
  IN: { mean: 85, p5: 72, p1: 63 }, I: { mean: 82, p5: 70, p1: 61 },
  IT: { mean: 80, p5: 68, p1: 59 }, ST: { mean: 81, p5: 69, p1: 60 },
};

// === NORMATIVE COLORS ===
export function normativeColor(value: number, norm: { mean: number; p5: number; p1: number }): string {
  if (value > norm.mean * 1.12) return "#a3e635"; // Supernormal (lime green)
  if (value >= norm.p5) return "#22c55e";          // Green (normal ≥p5)
  if (value >= norm.p1) return "#eab308";          // Yellow (borderline p1-p5)
  return "#ef4444";                                 // Red (<p1)
}

// Warm OCT color map: deep blue → cyan → green → yellow → orange → red → magenta → white
export function thicknessColor(value: number, minV: number, maxV: number): [number, number, number] {
  const t = Math.max(0, Math.min(1, (value - minV) / (maxV - minV)));
  if (t < 0.1)  return [0, 0, Math.round(60 + t / 0.1 * 195)];
  if (t < 0.2)  return [0, Math.round((t - 0.1) / 0.1 * 200), 255];
  if (t < 0.35) return [0, Math.round(200 + (t - 0.2) / 0.15 * 55), Math.round(255 * (1 - (t - 0.2) / 0.15))];
  if (t < 0.5)  return [Math.round((t - 0.35) / 0.15 * 255), 255, 0];
  if (t < 0.65) return [255, Math.round(255 - (t - 0.5) / 0.15 * 100), 0];
  if (t < 0.8)  return [255, Math.round(155 - (t - 0.65) / 0.15 * 155), 0];
  if (t < 0.9)  return [255, 0, Math.round((t - 0.8) / 0.1 * 150)];
  return [255, Math.round((t - 0.9) / 0.1 * 120), Math.round(150 + (t - 0.9) / 0.1 * 105)];
}

// Seeded RNG
function rng(seed: number) {
  let s = seed;
  return () => { s = (s * 1664525 + 1013904223) & 0xFFFFFFFF; return (s >>> 0) / 0xFFFFFFFF; };
}

export type Pathology = "normal" | "glaucoma" | "edema" | "drusen" | "epiretinal" | "amd-dry" | "amd-wet";

// === B-SCAN ===
export function generateBScan(w: number, h: number, macular: boolean, seed: number, path: Pathology, _severity: OctSeverity = "moderado"): ImageData {
  const r = rng(seed);
  const img = new ImageData(w, h);
  const d = img.data;
  const retTop = h * 0.18;
  const fx = w / 2;

  // Layer boundaries
  const bounds: number[][] = [];
  for (let x = 0; x < w; x++) {
    const xn = (x - fx) / (w * 0.5);
    const ecc = Math.abs(xn);
    let y = retTop + 25 * Math.sin((x / w) * Math.PI); // curvature
    const col: number[] = [];

    for (const layer of LAYERS) {
      col.push(y);
      const th = LAYER_THICKNESS[layer];
      let t = ecc < 0.15 && macular ? th.fovea : ecc < 0.5 ? th.para : th.peri;

      if (macular && ecc < 0.2) {
        if (layer === "ONL") t *= 1.4;
        if (layer === "RNFL" || layer === "GCL") t *= 0.3;
      }
      if (path === "glaucoma" && (layer === "RNFL")) t *= 0.35 + r() * 0.15;
      if (path === "glaucoma" && layer === "GCL") t *= 0.55;
      if (path === "edema" && layer === "ONL") t *= 1.6 + r() * 0.4;
      if (path === "edema" && layer === "INL") t *= 1.4;
      if (path === "epiretinal" && layer === "ILM") t += 6 + Math.sin(x * 0.015) * 4;

      y += t * (h / 480);
    }
    col.push(y); // below RPE
    bounds.push(col);
  }

  // Render
  for (let y = 0; y < h; y++) {
    for (let x = 0; x < w; x++) {
      const idx = (y * w + x) * 4;
      let br = 2 + r() * 4;

      const col = bounds[x];
      for (let li = 0; li < LAYERS.length; li++) {
        if (y >= col[li] && y < col[li + 1]) {
          br = LAYER_REFLECTIVITY[LAYERS[li]] * 210 + r() * 40;
          if (r() < 0.3) br *= 0.55 + r() * 0.45; // speckle
          if (y - col[li] < 1.2 || col[li + 1] - y < 1.2) br *= 1.15;
          break;
        }
      }

      // Vitreous
      if (y < col[0]) br = 1 + r() * 3;

      // Choroid
      if (y > col[col.length - 1]) {
        const depth = y - col[col.length - 1];
        br = 55 + r() * 35 - depth * 0.3;
        if (Math.sin(x * 0.07 + seed) > 0.6) br *= 0.4;
      }

      // Edema: cystoid spaces
      if (path === "edema" && macular) {
        const inlY = col[4], elmY = col[7];
        if (y > inlY && y < elmY) {
          for (const cx of [w * 0.42, w * 0.47, w * 0.5, w * 0.53, w * 0.58]) {
            if (Math.sqrt((x - cx) ** 2 + (y - (inlY + elmY) / 2) ** 2) < 10 + r() * 6) br = 4 + r() * 6;
          }
        }
      }

      // Drusen: RPE bumps
      if (path === "drusen") {
        const rpeY = col[9];
        for (const dp of [0.25, 0.38, 0.55, 0.72]) {
          const dx = Math.abs(x / w - dp);
          if (dx < 0.025 && y > rpeY - 3 && y < rpeY + 18) br = 180 + r() * 50;
        }
      }

      // AMD wet: subretinal fluid
      if (path === "amd-wet" && Math.abs(x - fx) < w * 0.12) {
        const rpeY = col[9];
        if (y > rpeY - 3 && y < rpeY + 25) br = 5 + r() * 8;
      }

      br = Math.max(0, Math.min(255, br));
      d[idx] = br; d[idx + 1] = br; d[idx + 2] = br; d[idx + 3] = 255;
    }
  }
  return img;
}

// === Patient params interface ===
export interface OctPatientParams {
  rnflAvg?: number;                  // RNFL promedio global (µm)
  gclIplAvg?: number;               // GCL+IPL promedio (µm)
  centralMacularThickness?: number;  // Espesor macular central (µm)
  cooperationLevel?: number;         // 0-1
  tearFilmQuality?: number;          // 0-1
}

// === RNFL TSNIT ===
export function generateRNFLProfile(
  seed: number, path: Pathology, severity: OctSeverity = "moderado", params: OctPatientParams = {},
): { angle: number; thickness: number }[] {
  const r = rng(seed);
  const result: { angle: number; thickness: number }[] = [];

  // Generar perfil base
  const raw: number[] = [];
  for (let deg = 0; deg < 360; deg++) {
    let t = 68;
    t += 60 * Math.exp(-((deg - 90) ** 2) / 900);
    t += 70 * Math.exp(-((deg - 270) ** 2) / 900);
    t += 20 * Math.exp(-((deg - 50) ** 2) / 400);
    t += 20 * Math.exp(-((deg - 310) ** 2) / 400);
    t -= 15 * Math.exp(-((deg - 180) ** 2) / 600);
    t += (r() - 0.5) * 6;
    if (path === "glaucoma") {
      const sf = sevFactor(severity);
      t -= 30 * sf * Math.exp(-((deg - 270) ** 2) / 800);
      t -= 20 * sf * Math.exp(-((deg - 90) ** 2) / 800);
      t -= 8 * sf;
    }
    raw.push(Math.max(15, t));
  }

  // Si el docente definió RNFL promedio, escalar el perfil para que coincida
  if (params.rnflAvg !== undefined) {
    const currentAvg = raw.reduce((a, b) => a + b, 0) / raw.length;
    const scale = currentAvg > 0 ? params.rnflAvg / currentAvg : 1;
    for (let i = 0; i < raw.length; i++) raw[i] = Math.max(15, raw[i] * scale);
  }

  for (let deg = 0; deg < 360; deg++) {
    result.push({ angle: deg, thickness: Math.round(raw[deg]) });
  }
  return result;
}

// === ETDRS MAP ===
export function generateETDRS(
  seed: number, path: Pathology, severity: OctSeverity = "moderado", params: OctPatientParams = {},
): Record<string, number> {
  const r = rng(seed);
  const res: Record<string, number> = {};
  const sf = sevFactor(severity);

  for (const [sec, norm] of Object.entries(ETDRS_NORMAL)) {
    let t = norm.mean + (r() - 0.5) * 15;
    if (path === "edema") { t += sf * (sec === "fovea" ? 120 + r() * 60 : sec.startsWith("inner") ? 60 + r() * 30 : 20 + r() * 15); }
    if (path === "amd-dry" || path === "amd-wet") { t -= sf * (sec === "fovea" ? 30 + r() * 20 : sec.startsWith("inner") ? 15 + r() * 10 : 5); }
    if (path === "glaucoma" && sec.startsWith("inner")) t -= sf * (15 + r() * 8);
    res[sec] = Math.max(100, Math.round(t));
  }

  // Si el docente definió espesor macular central, ajustar fóvea y propagar
  if (params.centralMacularThickness !== undefined && res.fovea) {
    const diff = params.centralMacularThickness - res.fovea;
    res.fovea = params.centralMacularThickness;
    // Propagar parcialmente a inner sectors
    for (const sec of Object.keys(res)) {
      if (sec.startsWith("inner")) res[sec] = Math.max(100, Math.round(res[sec] + diff * 0.4));
      if (sec.startsWith("outer")) res[sec] = Math.max(100, Math.round(res[sec] + diff * 0.15));
    }
  }

  return res;
}

// === GCL+IPL ===
export function generateGCLIPL(
  seed: number, path: Pathology, severity: OctSeverity = "moderado", params: OctPatientParams = {},
): Record<string, number> {
  const r = rng(seed);
  const res: Record<string, number> = {};
  const sf = sevFactor(severity);

  for (const [sec, norm] of Object.entries(GCL_IPL_SECTORS)) {
    let t = norm.mean + (r() - 0.5) * 6;
    if (path === "glaucoma") t -= sf * (15 + r() * 10);
    res[sec] = Math.max(30, Math.round(t));
  }

  // Si el docente definió GCL+IPL promedio, escalar
  if (params.gclIplAvg !== undefined) {
    const vals = Object.values(res);
    const currentAvg = vals.reduce((a, b) => a + b, 0) / vals.length;
    const scale = currentAvg > 0 ? params.gclIplAvg / currentAvg : 1;
    for (const sec of Object.keys(res)) {
      res[sec] = Math.max(30, Math.round(res[sec] * scale));
    }
  }

  return res;
}
