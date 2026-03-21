// === Corneal Topography Synthetic Data Generator ===

// Seeded RNG
function rng(seed: number) {
  let s = seed;
  return () => { s = (s * 1664525 + 1013904223) & 0xFFFFFFFF; return (s >>> 0) / 0xFFFFFFFF; };
}

export type CornealPathology =
  | "normal"
  | "keratoconus"
  | "pellucid"
  | "wtr-astigmatism"    // with-the-rule
  | "atr-astigmatism"    // against-the-rule
  | "oblique-astigmatism"
  | "post-lasik";

export type MapType = "axial" | "tangential" | "elevation" | "pachymetry";

export interface KeratometricIndices {
  k1: number;        // Flat meridian (D)
  k1Axis: number;    // Axis of K1 (°)
  k2: number;        // Steep meridian (D)
  k2Axis: number;    // Axis of K2 (°)
  kAvg: number;      // Average K
  kMax: number;      // Maximum K
  cylD: number;      // Cylinder in diopters
  simKAst: number;   // SimK astigmatism
  isa: number;       // Index of surface asymmetry
  ihd: number;       // Index of height decentration
  cct: number;       // Central corneal thickness (µm)
  tct: number;       // Thinnest corneal thickness (µm)
  tctX: number;      // Thinnest point X (mm)
  tctY: number;      // Thinnest point Y (mm)
}

// Normal corneal curvature: ~42-45 D center, flattening toward periphery
const NORMAL_K_CENTER = 43.5;
const NORMAL_K_RANGE = 1.5; // ±1.5 D natural variation
const NORMAL_CCT = 545; // µm

// Color map for curvature: cool (flat) → warm (steep)
// Blue (38D) → Green (41D) → Yellow (43D) → Orange (45D) → Red (48D) → Purple (52D+)
export function curvatureColor(diopters: number): [number, number, number] {
  const minD = 36;
  const maxD = 56;
  const t = Math.max(0, Math.min(1, (diopters - minD) / (maxD - minD)));

  if (t < 0.15) return [60, 60, Math.round(150 + t / 0.15 * 105)];         // dark blue → blue
  if (t < 0.25) return [0, Math.round((t - 0.15) / 0.1 * 200), 255];       // blue → cyan
  if (t < 0.35) return [0, Math.round(200 + (t - 0.25) / 0.1 * 55), Math.round(255 - (t - 0.25) / 0.1 * 200)]; // cyan → green
  if (t < 0.45) return [Math.round((t - 0.35) / 0.1 * 255), 255, 0];       // green → yellow
  if (t < 0.55) return [255, Math.round(255 - (t - 0.45) / 0.1 * 80), 0];  // yellow → orange
  if (t < 0.7)  return [255, Math.round(175 - (t - 0.55) / 0.15 * 175), 0]; // orange → red
  if (t < 0.85) return [Math.round(255 - (t - 0.7) / 0.15 * 55), 0, Math.round((t - 0.7) / 0.15 * 180)]; // red → purple
  return [200, 0, Math.round(180 + (t - 0.85) / 0.15 * 75)];               // deep purple
}

// Color map for pachymetry: thin (red) → normal (green) → thick (blue)
export function pachymetryColor(thickness: number): [number, number, number] {
  const minT = 400;
  const maxT = 650;
  const t = Math.max(0, Math.min(1, (thickness - minT) / (maxT - minT)));

  if (t < 0.2)  return [220, Math.round(t / 0.2 * 60), 20];               // red
  if (t < 0.4)  return [255, Math.round(60 + (t - 0.2) / 0.2 * 195), 0];  // orange → yellow
  if (t < 0.6)  return [Math.round(255 - (t - 0.4) / 0.2 * 255), 255, 0]; // yellow → green
  if (t < 0.8)  return [0, Math.round(255 - (t - 0.6) / 0.2 * 55), Math.round((t - 0.6) / 0.2 * 255)]; // green → cyan
  return [0, Math.round(200 - (t - 0.8) / 0.2 * 100), 255];               // cyan → blue
}

// Elevation color: negative (blue) → zero (green) → positive (red)
export function elevationColor(microns: number): [number, number, number] {
  const range = 60; // ±60 µm
  const t = Math.max(0, Math.min(1, (microns + range) / (2 * range)));

  if (t < 0.3)  return [0, Math.round(t / 0.3 * 150), Math.round(200 + t / 0.3 * 55)];
  if (t < 0.5)  return [0, Math.round(150 + (t - 0.3) / 0.2 * 105), Math.round(255 - (t - 0.3) / 0.2 * 255)];
  if (t < 0.7)  return [Math.round((t - 0.5) / 0.2 * 255), Math.round(255 - (t - 0.5) / 0.2 * 55), 0];
  return [255, Math.round(200 - (t - 0.7) / 0.3 * 200), 0];
}

/**
 * Genera un mapa de curvatura corneal 2D (en dioptrías).
 * Retorna un array plano de size×size con valores en dioptrías.
 * Coordenadas: centro = (size/2, size/2), cada pixel ≈ 0.1mm
 */
export function generateCurvatureMap(
  size: number,
  seed: number,
  pathology: CornealPathology,
  mapType: MapType = "axial",
): Float32Array {
  const r = rng(seed);
  const map = new Float32Array(size * size);
  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2; // corneal radius in pixels (~4.5mm)

  // Base curvature with slight patient variation
  const kBase = NORMAL_K_CENTER + (r() - 0.5) * NORMAL_K_RANGE;

  // Natural astigmatism axis and magnitude
  let astAxis = 90 + (r() - 0.5) * 20; // mostly WTR in normals
  let astMag = 0.3 + r() * 0.5;         // 0.3-0.8 D normal astigmatism

  // Pathology modifiers
  let kcConeX = 0, kcConeY = 0, kcSteepening = 0;
  let pellucidBandY = 0;
  let lasikFlatZone = 0;

  switch (pathology) {
    case "keratoconus":
      kcConeX = (r() - 0.5) * radius * 0.25;     // slightly decentered
      kcConeY = radius * 0.15 + r() * radius * 0.1; // inferotemporal
      kcSteepening = 4 + r() * 6;                   // 4-10 D steeper
      astMag = 2 + r() * 3;                         // irregular astigmatism
      astAxis = 60 + r() * 60;                      // variable axis
      break;
    case "pellucid":
      pellucidBandY = radius * 0.55 + r() * radius * 0.1;
      astMag = 3 + r() * 4;
      astAxis = 170 + r() * 20; // ATR pattern
      break;
    case "wtr-astigmatism":
      astAxis = 85 + r() * 10;
      astMag = 2 + r() * 2;
      break;
    case "atr-astigmatism":
      astAxis = 175 + r() * 10;
      astMag = 2 + r() * 2;
      break;
    case "oblique-astigmatism":
      astAxis = 30 + r() * 30;
      astMag = 1.5 + r() * 2.5;
      break;
    case "post-lasik":
      lasikFlatZone = 3 + r() * 2; // 3-5 D flatter in center
      astMag = 0.5 + r() * 1;
      break;
  }

  const astRad = (astAxis * Math.PI) / 180;

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const dx = x - cx;
      const dy = y - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);

      // Outside corneal zone → NaN
      if (dist > radius * 0.95) {
        map[y * size + x] = NaN;
        continue;
      }

      const normDist = dist / radius;
      const angle = Math.atan2(dy, dx);

      // Base: flattening toward periphery (prolate shape)
      let k = kBase - normDist * normDist * 2.5;

      // Regular astigmatism: bow-tie pattern
      const astComponent = Math.cos(2 * (angle - astRad));
      k += (astMag / 2) * astComponent;

      // Tangential map amplifies local curvature changes
      if (mapType === "tangential") {
        const localVar = (r() - 0.5) * 0.3;
        k += astMag * 0.3 * astComponent * (1 + normDist) + localVar;
      }

      // Pathology-specific deformations
      if (pathology === "keratoconus") {
        const dxCone = dx - kcConeX;
        const dyCone = dy - kcConeY;
        const coneDist = Math.sqrt(dxCone * dxCone + dyCone * dyCone);
        const coneRadius = radius * (0.2 + r() * 0.05);
        if (coneDist < coneRadius) {
          const coneT = 1 - coneDist / coneRadius;
          k += kcSteepening * coneT * coneT;
        }
      }

      if (pathology === "pellucid") {
        const bandDist = Math.abs(dy - pellucidBandY);
        const bandWidth = radius * 0.15;
        if (bandDist < bandWidth && Math.abs(dx) < radius * 0.6) {
          const bandT = 1 - bandDist / bandWidth;
          k += 3 * bandT * bandT;
          // Flattening just above the band (butterfly)
          if (dy < pellucidBandY && dy > pellucidBandY - bandWidth * 2) {
            k -= 2 * (1 - Math.abs(dy - pellucidBandY + bandWidth) / bandWidth);
          }
        }
      }

      if (pathology === "post-lasik") {
        const ablZone = radius * 0.45;
        if (dist < ablZone) {
          const ablT = 1 - (dist / ablZone);
          k -= lasikFlatZone * ablT * ablT;
        }
        // Transition knee
        if (dist > ablZone * 0.8 && dist < ablZone * 1.3) {
          k += 1.5 * Math.exp(-((dist - ablZone) ** 2) / (ablZone * 0.15) ** 2);
        }
      }

      // Noise
      k += (r() - 0.5) * 0.15;

      map[y * size + x] = k;
    }
  }

  return map;
}

/**
 * Genera un mapa de elevación corneal (en µm respecto a esfera de referencia).
 */
export function generateElevationMap(
  size: number,
  seed: number,
  pathology: CornealPathology,
): Float32Array {
  const r = rng(seed + 500);
  const map = new Float32Array(size * size);
  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2;

  let coneX = 0, coneY = 0;
  if (pathology === "keratoconus") {
    coneX = (r() - 0.5) * radius * 0.25;
    coneY = radius * 0.15 + r() * radius * 0.1;
  }

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const dx = x - cx;
      const dy = y - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist > radius * 0.95) {
        map[y * size + x] = NaN;
        continue;
      }

      const normDist = dist / radius;

      // Elevation relative to best-fit sphere
      let elev = normDist * normDist * 8 + (r() - 0.5) * 0.5;

      if (pathology === "keratoconus") {
        const dxC = dx - coneX;
        const dyC = dy - coneY;
        const coneDist = Math.sqrt(dxC * dxC + dyC * dyC);
        const coneR = radius * 0.22;
        if (coneDist < coneR) {
          elev += (15 + r() * 20) * (1 - coneDist / coneR) ** 2;
        }
      }

      if (pathology === "pellucid") {
        const bandY = radius * 0.55;
        const bandDist = Math.abs(dy - bandY);
        if (bandDist < radius * 0.15 && Math.abs(dx) < radius * 0.6) {
          elev += 12 * (1 - bandDist / (radius * 0.15)) ** 2;
        }
      }

      if (pathology === "post-lasik") {
        const ablZone = radius * 0.45;
        if (dist < ablZone) {
          elev -= (8 + r() * 4) * (1 - dist / ablZone) ** 2;
        }
      }

      map[y * size + x] = elev;
    }
  }

  return map;
}

/**
 * Genera un mapa de paquimetría corneal (espesor en µm).
 */
export function generatePachymetryMap(
  size: number,
  seed: number,
  pathology: CornealPathology,
): Float32Array {
  const r = rng(seed + 1000);
  const map = new Float32Array(size * size);
  const cx = size / 2;
  const cy = size / 2;
  const radius = size / 2;

  const baseCCT = NORMAL_CCT + (r() - 0.5) * 30;

  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const dx = x - cx;
      const dy = y - cy;
      const dist = Math.sqrt(dx * dx + dy * dy);

      if (dist > radius * 0.95) {
        map[y * size + x] = NaN;
        continue;
      }

      const normDist = dist / radius;

      // Normal: thinnest near center, thickens toward periphery
      let thickness = baseCCT + normDist * normDist * 120;
      // Slight nasal thickening
      thickness += (dx > 0 ? 1 : -1) * normDist * 8;
      thickness += (r() - 0.5) * 3;

      if (pathology === "keratoconus") {
        // Thinning at cone apex
        const coneX = (r() - 0.3) * radius * 0.1;
        const coneY = radius * 0.15;
        const coneDist = Math.sqrt((dx - coneX) ** 2 + (dy - coneY) ** 2);
        const coneR = radius * 0.3;
        if (coneDist < coneR) {
          thickness -= (80 + r() * 60) * (1 - coneDist / coneR) ** 2;
        }
      }

      if (pathology === "pellucid") {
        const bandY = radius * 0.55;
        const bandDist = Math.abs(dy - bandY);
        if (bandDist < radius * 0.2 && Math.abs(dx) < radius * 0.7) {
          thickness -= (60 + r() * 40) * (1 - bandDist / (radius * 0.2)) ** 2;
        }
      }

      if (pathology === "post-lasik") {
        const ablZone = radius * 0.45;
        if (dist < ablZone) {
          thickness -= (40 + r() * 20) * (1 - dist / ablZone) ** 2;
        }
      }

      map[y * size + x] = Math.max(350, thickness);
    }
  }

  return map;
}

/**
 * Calcula índices queratométricos a partir del mapa de curvatura.
 */
export function computeKeratometricIndices(
  curvatureMap: Float32Array,
  pachymetryMap: Float32Array,
  size: number,
  seed: number,
): KeratometricIndices {
  const cx = size / 2;
  const cy = size / 2;
  const r3mm = size * 0.33; // 3mm zone

  // Sample central 3mm for SimK
  const meridianPower: { angle: number; power: number }[] = [];
  for (let deg = 0; deg < 180; deg += 1) {
    const rad = (deg * Math.PI) / 180;
    let sum = 0, count = 0;
    for (let d = r3mm * 0.3; d < r3mm; d += 2) {
      const sx = Math.round(cx + Math.cos(rad) * d);
      const sy = Math.round(cy + Math.sin(rad) * d);
      if (sx >= 0 && sx < size && sy >= 0 && sy < size) {
        const v = curvatureMap[sy * size + sx];
        if (!isNaN(v)) { sum += v; count++; }
      }
      // Also sample opposite side
      const sx2 = Math.round(cx - Math.cos(rad) * d);
      const sy2 = Math.round(cy - Math.sin(rad) * d);
      if (sx2 >= 0 && sx2 < size && sy2 >= 0 && sy2 < size) {
        const v2 = curvatureMap[sy2 * size + sx2];
        if (!isNaN(v2)) { sum += v2; count++; }
      }
    }
    if (count > 0) meridianPower.push({ angle: deg, power: sum / count });
  }

  // Find flat and steep meridians
  let minPower = Infinity, maxPower = -Infinity;
  let k1Axis = 0, k2Axis = 90;
  for (const mp of meridianPower) {
    if (mp.power < minPower) { minPower = mp.power; k1Axis = mp.angle; }
    if (mp.power > maxPower) { maxPower = mp.power; k2Axis = mp.angle; }
  }

  // Find Kmax
  let kMax = -Infinity;
  for (let i = 0; i < size * size; i++) {
    if (!isNaN(curvatureMap[i]) && curvatureMap[i] > kMax) kMax = curvatureMap[i];
  }

  // Central corneal thickness
  const centerIdx = Math.round(cy) * size + Math.round(cx);
  const cct = Math.round(pachymetryMap[centerIdx]);

  // Thinnest point
  let tct = Infinity, tctX = 0, tctY = 0;
  for (let y = 0; y < size; y++) {
    for (let x = 0; x < size; x++) {
      const v = pachymetryMap[y * size + x];
      if (!isNaN(v) && v < tct) {
        tct = v;
        tctX = (x - cx) / (size / 9); // convert to mm (approx)
        tctY = (y - cy) / (size / 9);
      }
    }
  }

  const k1 = round2(minPower);
  const k2 = round2(maxPower);
  const kAvg = round2((k1 + k2) / 2);
  const cylD = round2(k2 - k1);

  // ISA: index of surface asymmetry (higher = more irregular)
  // Compare superior vs inferior hemi-meridians
  let isaDiff = 0, isaCount = 0;
  for (let deg = 0; deg < 180; deg += 5) {
    const sup = meridianPower.find(m => m.angle === deg);
    const inf = meridianPower.find(m => m.angle === ((deg + 90) % 180));
    if (sup && inf) {
      isaDiff += Math.abs(sup.power - inf.power);
      isaCount++;
    }
  }

  return {
    k1, k1Axis: Math.round(k1Axis),
    k2, k2Axis: Math.round(k2Axis),
    kAvg,
    kMax: round2(kMax),
    cylD,
    simKAst: cylD,
    isa: round2(isaCount > 0 ? isaDiff / isaCount : 0),
    ihd: round2(Math.abs(k2 - kAvg) * 0.8),
    cct,
    tct: Math.round(tct),
    tctX: round2(tctX),
    tctY: round2(tctY),
  };
}

function round2(n: number) {
  return Math.round(n * 100) / 100;
}

/**
 * Renderiza un mapa de topografía como ImageData para canvas.
 */
export function renderMapToImage(
  map: Float32Array,
  size: number,
  mapType: MapType,
): ImageData {
  const img = new ImageData(size, size);
  const d = img.data;

  for (let i = 0; i < size * size; i++) {
    const idx = i * 4;
    const val = map[i];

    if (isNaN(val)) {
      d[idx] = 20; d[idx + 1] = 20; d[idx + 2] = 25; d[idx + 3] = 255;
      continue;
    }

    let rgb: [number, number, number];
    if (mapType === "pachymetry") {
      rgb = pachymetryColor(val);
    } else if (mapType === "elevation") {
      rgb = elevationColor(val);
    } else {
      rgb = curvatureColor(val);
    }

    d[idx] = rgb[0];
    d[idx + 1] = rgb[1];
    d[idx + 2] = rgb[2];
    d[idx + 3] = 255;
  }

  return img;
}
