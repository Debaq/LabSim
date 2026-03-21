/**
 * Generación sintética de imágenes de fondo de ojo para el retinógrafo.
 * Produce datos que el canvas renderiza como una retinografía realista.
 */

export type RetinopathyType =
  | "normal"
  | "npdr-leve"
  | "npdr-moderada"
  | "npdr-severa"
  | "pdr"
  | "glaucoma"
  | "dmae-seca"
  | "dmae-humeda"
  | "hta"
  | "oclusionVR"
  | "edema-macular";

export const RETINOPATHY_LABELS: Record<RetinopathyType, string> = {
  normal: "Normal",
  "npdr-leve": "RDNP Leve",
  "npdr-moderada": "RDNP Mod",
  "npdr-severa": "RDNP Sev",
  pdr: "RDP",
  glaucoma: "Glauc",
  "dmae-seca": "DMAE-s",
  "dmae-humeda": "DMAE-h",
  hta: "HTA",
  oclusionVR: "OVR",
  "edema-macular": "EM",
};

/** PRNG determinista basado en seed */
function seededRandom(seed: number) {
  let s = seed;
  return () => {
    s = (s * 16807 + 0) % 2147483647;
    return (s - 1) / 2147483646;
  };
}

export interface FundusParams {
  seed: number;
  pathology: RetinopathyType;
  eye: "OD" | "OI";
  signalQuality: number; // 1-10
}

interface Vessel {
  x: number;
  y: number;
  angle: number;
  width: number;
  isArtery: boolean;
  length: number;
  branches: Vessel[];
}

interface Lesion {
  x: number;
  y: number;
  radius: number;
  type: "microaneurysm" | "hemorrhage" | "exudate" | "drusen" | "cotton-wool" | "neovascularization" | "atrophy";
  color: string;
  opacity: number;
}

function generateVessels(rng: () => number, isOD: boolean): Vessel[] {
  const vessels: Vessel[] = [];
  // Disco óptico está nasal: OD a la izquierda, OI a la derecha
  const discX = isOD ? 0.35 : 0.65;
  const discY = 0.48;

  const numMain = 4 + Math.floor(rng() * 3);
  for (let i = 0; i < numMain; i++) {
    const baseAngle = (i / numMain) * Math.PI * 2 + (rng() - 0.5) * 0.4;
    const vessel: Vessel = {
      x: discX,
      y: discY,
      angle: baseAngle,
      width: 2 + rng() * 2,
      isArtery: i % 2 === 0,
      length: 0.25 + rng() * 0.2,
      branches: [],
    };

    // Sub-ramas
    const numBranches = 2 + Math.floor(rng() * 3);
    for (let b = 0; b < numBranches; b++) {
      vessel.branches.push({
        x: 0, y: 0, // se calcula al renderizar
        angle: baseAngle + (rng() - 0.5) * 1.2,
        width: vessel.width * (0.4 + rng() * 0.3),
        isArtery: vessel.isArtery,
        length: 0.08 + rng() * 0.12,
        branches: [],
      });
    }
    vessels.push(vessel);
  }
  return vessels;
}

function generateLesions(rng: () => number, pathology: RetinopathyType, isOD: boolean): Lesion[] {
  const lesions: Lesion[] = [];
  const maculaX = isOD ? 0.55 : 0.45;
  const maculaY = 0.50;

  switch (pathology) {
    case "npdr-leve": {
      // Pocos microaneurismas
      for (let i = 0; i < 5 + Math.floor(rng() * 5); i++) {
        lesions.push({
          x: maculaX + (rng() - 0.5) * 0.3,
          y: maculaY + (rng() - 0.5) * 0.3,
          radius: 0.003 + rng() * 0.004,
          type: "microaneurysm",
          color: "#8b0000",
          opacity: 0.6 + rng() * 0.3,
        });
      }
      break;
    }
    case "npdr-moderada": {
      // Microaneurismas + hemorragias puntiformes + exudados
      for (let i = 0; i < 15 + Math.floor(rng() * 10); i++) {
        lesions.push({
          x: maculaX + (rng() - 0.5) * 0.4,
          y: maculaY + (rng() - 0.5) * 0.4,
          radius: 0.003 + rng() * 0.005,
          type: rng() > 0.5 ? "microaneurysm" : "hemorrhage",
          color: rng() > 0.5 ? "#8b0000" : "#5c0000",
          opacity: 0.5 + rng() * 0.4,
        });
      }
      for (let i = 0; i < 4 + Math.floor(rng() * 4); i++) {
        lesions.push({
          x: maculaX + (rng() - 0.5) * 0.25,
          y: maculaY + (rng() - 0.5) * 0.25,
          radius: 0.005 + rng() * 0.008,
          type: "exudate",
          color: "#f5deb3",
          opacity: 0.6 + rng() * 0.3,
        });
      }
      break;
    }
    case "npdr-severa": {
      // Muchas hemorragias en los 4 cuadrantes + manchas algodonosas
      for (let i = 0; i < 30 + Math.floor(rng() * 15); i++) {
        const angle = rng() * Math.PI * 2;
        const dist = 0.1 + rng() * 0.3;
        lesions.push({
          x: 0.5 + Math.cos(angle) * dist,
          y: 0.5 + Math.sin(angle) * dist,
          radius: 0.004 + rng() * 0.01,
          type: rng() > 0.3 ? "hemorrhage" : "microaneurysm",
          color: "#6b0000",
          opacity: 0.5 + rng() * 0.4,
        });
      }
      for (let i = 0; i < 3 + Math.floor(rng() * 3); i++) {
        lesions.push({
          x: 0.5 + (rng() - 0.5) * 0.5,
          y: 0.5 + (rng() - 0.5) * 0.5,
          radius: 0.015 + rng() * 0.01,
          type: "cotton-wool",
          color: "#e8e8d0",
          opacity: 0.5 + rng() * 0.3,
        });
      }
      break;
    }
    case "pdr": {
      // Neovascularización + hemorragias
      for (let i = 0; i < 20 + Math.floor(rng() * 10); i++) {
        lesions.push({
          x: 0.5 + (rng() - 0.5) * 0.5,
          y: 0.5 + (rng() - 0.5) * 0.5,
          radius: 0.005 + rng() * 0.012,
          type: "hemorrhage",
          color: "#4a0000",
          opacity: 0.5 + rng() * 0.4,
        });
      }
      const discX = isOD ? 0.35 : 0.65;
      for (let i = 0; i < 3 + Math.floor(rng() * 3); i++) {
        lesions.push({
          x: discX + (rng() - 0.5) * 0.1,
          y: 0.48 + (rng() - 0.5) * 0.1,
          radius: 0.02 + rng() * 0.015,
          type: "neovascularization",
          color: "#cc3333",
          opacity: 0.4 + rng() * 0.3,
        });
      }
      break;
    }
    case "dmae-seca": {
      // Drusas en área macular
      for (let i = 0; i < 20 + Math.floor(rng() * 15); i++) {
        lesions.push({
          x: maculaX + (rng() - 0.5) * 0.2,
          y: maculaY + (rng() - 0.5) * 0.2,
          radius: 0.005 + rng() * 0.01,
          type: "drusen",
          color: "#e8d888",
          opacity: 0.4 + rng() * 0.4,
        });
      }
      // Atrofia geográfica
      if (rng() > 0.5) {
        lesions.push({
          x: maculaX,
          y: maculaY,
          radius: 0.04 + rng() * 0.03,
          type: "atrophy",
          color: "#d4b896",
          opacity: 0.3 + rng() * 0.2,
        });
      }
      break;
    }
    case "dmae-humeda": {
      // Hemorragia submacular + exudados + drusas
      lesions.push({
        x: maculaX,
        y: maculaY,
        radius: 0.05 + rng() * 0.03,
        type: "hemorrhage",
        color: "#550000",
        opacity: 0.5 + rng() * 0.3,
      });
      for (let i = 0; i < 8 + Math.floor(rng() * 6); i++) {
        lesions.push({
          x: maculaX + (rng() - 0.5) * 0.15,
          y: maculaY + (rng() - 0.5) * 0.15,
          radius: 0.006 + rng() * 0.008,
          type: "exudate",
          color: "#f0d890",
          opacity: 0.5 + rng() * 0.3,
        });
      }
      break;
    }
    case "glaucoma": {
      // No hay lesiones retinianas visibles en retinógrafo, pero el excavación se modifica
      // (se maneja en el renderizado del disco óptico)
      break;
    }
    case "hta": {
      // Hemorragias en llama + exudados + manchas algodonosas
      for (let i = 0; i < 10 + Math.floor(rng() * 8); i++) {
        const angle = rng() * Math.PI * 2;
        const dist = 0.1 + rng() * 0.25;
        lesions.push({
          x: 0.5 + Math.cos(angle) * dist,
          y: 0.5 + Math.sin(angle) * dist,
          radius: 0.008 + rng() * 0.01,
          type: "hemorrhage",
          color: "#7a0000",
          opacity: 0.4 + rng() * 0.3,
        });
      }
      // Exudados estrellados en mácula
      for (let i = 0; i < 8; i++) {
        const angle = (i / 8) * Math.PI * 2;
        lesions.push({
          x: maculaX + Math.cos(angle) * 0.04,
          y: maculaY + Math.sin(angle) * 0.04,
          radius: 0.004 + rng() * 0.003,
          type: "exudate",
          color: "#f5deb3",
          opacity: 0.6 + rng() * 0.2,
        });
      }
      break;
    }
    case "oclusionVR": {
      // Hemorragias masivas en un sector + venas dilatadas
      const sector = rng() > 0.5 ? 1 : -1;
      for (let i = 0; i < 25 + Math.floor(rng() * 15); i++) {
        lesions.push({
          x: 0.5 + (rng() * 0.3) * sector,
          y: 0.5 + (rng() - 0.5) * 0.4,
          radius: 0.006 + rng() * 0.015,
          type: "hemorrhage",
          color: "#5a0000",
          opacity: 0.5 + rng() * 0.4,
        });
      }
      for (let i = 0; i < 3; i++) {
        lesions.push({
          x: 0.5 + (rng() * 0.2) * sector,
          y: 0.5 + (rng() - 0.5) * 0.3,
          radius: 0.012 + rng() * 0.01,
          type: "cotton-wool",
          color: "#e0d8c0",
          opacity: 0.4 + rng() * 0.3,
        });
      }
      break;
    }
    case "edema-macular": {
      // Engrosamiento macular con exudados circinados
      for (let i = 0; i < 12 + Math.floor(rng() * 8); i++) {
        const angle = rng() * Math.PI * 2;
        const dist = 0.03 + rng() * 0.06;
        lesions.push({
          x: maculaX + Math.cos(angle) * dist,
          y: maculaY + Math.sin(angle) * dist,
          radius: 0.005 + rng() * 0.006,
          type: "exudate",
          color: "#f0d070",
          opacity: 0.5 + rng() * 0.3,
        });
      }
      for (let i = 0; i < 6 + Math.floor(rng() * 4); i++) {
        lesions.push({
          x: maculaX + (rng() - 0.5) * 0.12,
          y: maculaY + (rng() - 0.5) * 0.12,
          radius: 0.003 + rng() * 0.004,
          type: "microaneurysm",
          color: "#8b0000",
          opacity: 0.5 + rng() * 0.3,
        });
      }
      break;
    }
    default:
      break;
  }

  return lesions;
}

/** Renderiza una imagen de fondo de ojo sintética en un canvas */
export function renderFundus(
  ctx: CanvasRenderingContext2D,
  w: number,
  h: number,
  params: FundusParams,
) {
  const { seed, pathology, eye, signalQuality } = params;
  const rng = seededRandom(seed);
  const isOD = eye === "OD";
  const cx = w / 2;
  const cy = h / 2;
  const radius = Math.min(w, h) * 0.45;

  // Fondo negro
  ctx.fillStyle = "#000";
  ctx.fillRect(0, 0, w, h);

  // Círculo retiniano (fondo naranja-rojizo)
  const grad = ctx.createRadialGradient(cx, cy, 0, cx, cy, radius);
  grad.addColorStop(0, "#c85a20");
  grad.addColorStop(0.4, "#b84a18");
  grad.addColorStop(0.7, "#983812");
  grad.addColorStop(1, "#68280a");
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.fillStyle = grad;
  ctx.fill();

  // Clip al círculo
  ctx.save();
  ctx.beginPath();
  ctx.arc(cx, cy, radius, 0, Math.PI * 2);
  ctx.clip();

  // Textura sutil de la retina
  for (let i = 0; i < 200; i++) {
    const tx = cx + (rng() - 0.5) * radius * 2;
    const ty = cy + (rng() - 0.5) * radius * 2;
    ctx.fillStyle = `rgba(${140 + rng() * 40}, ${60 + rng() * 30}, ${15 + rng() * 15}, ${0.05 + rng() * 0.08})`;
    ctx.beginPath();
    ctx.arc(tx, ty, 2 + rng() * 8, 0, Math.PI * 2);
    ctx.fill();
  }

  // Disco óptico
  const discX = (isOD ? 0.35 : 0.65) * w;
  const discY = 0.48 * h;
  const discRadius = radius * 0.11;
  const cupRatio = pathology === "glaucoma" ? 0.7 + rng() * 0.15 : 0.3 + rng() * 0.15;

  // Anillo neurorretiniano
  const discGrad = ctx.createRadialGradient(discX, discY, 0, discX, discY, discRadius);
  discGrad.addColorStop(0, "#f5deb3");
  discGrad.addColorStop(0.6, "#e8c890");
  discGrad.addColorStop(1, "#d4a060");
  ctx.beginPath();
  ctx.arc(discX, discY, discRadius, 0, Math.PI * 2);
  ctx.fillStyle = discGrad;
  ctx.fill();

  // Excavación (cup)
  const cupRadius = discRadius * cupRatio;
  const cupGrad = ctx.createRadialGradient(discX, discY, 0, discX, discY, cupRadius);
  cupGrad.addColorStop(0, "#f0e0c0");
  cupGrad.addColorStop(0.5, "#e8d0a0");
  cupGrad.addColorStop(1, "#d8b880");
  ctx.beginPath();
  ctx.arc(discX, discY, cupRadius, 0, Math.PI * 2);
  ctx.fillStyle = cupGrad;
  ctx.fill();

  // Vasos sanguíneos
  const vessels = generateVessels(rng, isOD);
  for (const v of vessels) {
    drawVessel(ctx, v, w, h, rng, radius);
  }

  // Mácula y fóvea
  const maculaX = (isOD ? 0.55 : 0.45) * w;
  const maculaY = 0.50 * h;
  const maculaGrad = ctx.createRadialGradient(maculaX, maculaY, 0, maculaX, maculaY, radius * 0.08);
  maculaGrad.addColorStop(0, "rgba(40, 15, 5, 0.5)");
  maculaGrad.addColorStop(0.3, "rgba(60, 20, 8, 0.3)");
  maculaGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
  ctx.fillStyle = maculaGrad;
  ctx.beginPath();
  ctx.arc(maculaX, maculaY, radius * 0.08, 0, Math.PI * 2);
  ctx.fill();

  // Reflejo foveal
  const foveaGrad = ctx.createRadialGradient(maculaX, maculaY, 0, maculaX, maculaY, radius * 0.015);
  foveaGrad.addColorStop(0, "rgba(255, 255, 200, 0.15)");
  foveaGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
  ctx.fillStyle = foveaGrad;
  ctx.beginPath();
  ctx.arc(maculaX, maculaY, radius * 0.015, 0, Math.PI * 2);
  ctx.fill();

  // Lesiones patológicas
  const lesions = generateLesions(rng, pathology, isOD);
  for (const lesion of lesions) {
    drawLesion(ctx, lesion, w, h);
  }

  ctx.restore();

  // Degradado de borde (viñeta)
  const vignetteGrad = ctx.createRadialGradient(cx, cy, radius * 0.7, cx, cy, radius * 1.05);
  vignetteGrad.addColorStop(0, "rgba(0, 0, 0, 0)");
  vignetteGrad.addColorStop(1, "rgba(0, 0, 0, 1)");
  ctx.fillStyle = vignetteGrad;
  ctx.fillRect(0, 0, w, h);

  // Efecto de calidad de señal (ruido)
  if (signalQuality < 8) {
    const noiseLevel = (10 - signalQuality) * 0.025;
    for (let i = 0; i < 500; i++) {
      const nx = rng() * w;
      const ny = rng() * h;
      ctx.fillStyle = `rgba(${rng() > 0.5 ? 255 : 0}, ${rng() > 0.5 ? 200 : 0}, ${rng() > 0.5 ? 150 : 0}, ${noiseLevel * rng()})`;
      ctx.fillRect(nx, ny, 1 + rng() * 2, 1 + rng() * 2);
    }
  }

  // Flash / reflejo especular sutil
  const flashGrad = ctx.createRadialGradient(cx - radius * 0.2, cy - radius * 0.2, 0, cx, cy, radius);
  flashGrad.addColorStop(0, "rgba(255, 255, 220, 0.04)");
  flashGrad.addColorStop(1, "rgba(0, 0, 0, 0)");
  ctx.fillStyle = flashGrad;
  ctx.fillRect(0, 0, w, h);
}

function drawVessel(
  ctx: CanvasRenderingContext2D,
  vessel: Vessel,
  w: number,
  h: number,
  rng: () => number,
  retRadius: number,
) {
  const startX = vessel.x * w;
  const startY = vessel.y * h;
  const len = vessel.length * retRadius * 2;

  ctx.strokeStyle = vessel.isArtery ? "#cc2200" : "#880011";
  ctx.lineWidth = vessel.width;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";

  ctx.beginPath();
  ctx.moveTo(startX, startY);

  const steps = 8;
  let px = startX;
  let py = startY;
  for (let i = 1; i <= steps; i++) {
    const t = i / steps;
    const wobble = (rng() - 0.5) * 15;
    const nx = startX + Math.cos(vessel.angle) * len * t + Math.sin(vessel.angle) * wobble;
    const ny = startY + Math.sin(vessel.angle) * len * t - Math.cos(vessel.angle) * wobble;
    ctx.quadraticCurveTo(
      (px + nx) / 2 + (rng() - 0.5) * 8,
      (py + ny) / 2 + (rng() - 0.5) * 8,
      nx,
      ny,
    );
    px = nx;
    py = ny;
  }
  ctx.stroke();

  // Ramas
  for (const branch of vessel.branches) {
    const branchStart = 0.3 + rng() * 0.5;
    const bx = startX + Math.cos(vessel.angle) * len * branchStart;
    const by = startY + Math.sin(vessel.angle) * len * branchStart;
    const bLen = branch.length * retRadius * 2;

    ctx.lineWidth = branch.width;
    ctx.beginPath();
    ctx.moveTo(bx, by);

    let bpx = bx;
    let bpy = by;
    for (let i = 1; i <= 5; i++) {
      const t = i / 5;
      const wobble = (rng() - 0.5) * 8;
      const nx = bx + Math.cos(branch.angle) * bLen * t + Math.sin(branch.angle) * wobble;
      const ny = by + Math.sin(branch.angle) * bLen * t - Math.cos(branch.angle) * wobble;
      ctx.quadraticCurveTo(
        (bpx + nx) / 2 + (rng() - 0.5) * 5,
        (bpy + ny) / 2 + (rng() - 0.5) * 5,
        nx,
        ny,
      );
      bpx = nx;
      bpy = ny;
    }
    ctx.stroke();
  }
}

function drawLesion(ctx: CanvasRenderingContext2D, lesion: Lesion, w: number, h: number) {
  const x = lesion.x * w;
  const y = lesion.y * h;
  const r = lesion.radius * Math.min(w, h);

  ctx.globalAlpha = lesion.opacity;

  switch (lesion.type) {
    case "microaneurysm":
      ctx.fillStyle = lesion.color;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
      break;
    case "hemorrhage": {
      const hGrad = ctx.createRadialGradient(x, y, 0, x, y, r);
      hGrad.addColorStop(0, lesion.color);
      hGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = hGrad;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
      break;
    }
    case "exudate":
      ctx.fillStyle = lesion.color;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
      break;
    case "drusen": {
      const dGrad = ctx.createRadialGradient(x, y, 0, x, y, r);
      dGrad.addColorStop(0, lesion.color);
      dGrad.addColorStop(0.7, lesion.color + "88");
      dGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = dGrad;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
      break;
    }
    case "cotton-wool": {
      const cwGrad = ctx.createRadialGradient(x, y, 0, x, y, r);
      cwGrad.addColorStop(0, lesion.color);
      cwGrad.addColorStop(0.6, lesion.color + "66");
      cwGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = cwGrad;
      ctx.beginPath();
      ctx.ellipse(x, y, r * 1.3, r * 0.8, Math.random() * Math.PI, 0, Math.PI * 2);
      ctx.fill();
      break;
    }
    case "neovascularization":
      ctx.strokeStyle = lesion.color;
      ctx.lineWidth = 0.5;
      for (let i = 0; i < 12; i++) {
        const angle = (i / 12) * Math.PI * 2;
        const len = r * (0.5 + Math.random() * 0.5);
        ctx.beginPath();
        ctx.moveTo(x, y);
        ctx.lineTo(x + Math.cos(angle) * len, y + Math.sin(angle) * len);
        ctx.stroke();
      }
      break;
    case "atrophy": {
      const aGrad = ctx.createRadialGradient(x, y, 0, x, y, r);
      aGrad.addColorStop(0, lesion.color);
      aGrad.addColorStop(0.8, lesion.color + "44");
      aGrad.addColorStop(1, "rgba(0,0,0,0)");
      ctx.fillStyle = aGrad;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
      break;
    }
  }

  ctx.globalAlpha = 1;
}

/** Cup-to-disc ratio estimado según patología */
export function getCDRatio(pathology: RetinopathyType, seed: number): number {
  const rng = seededRandom(seed + 999);
  if (pathology === "glaucoma") return 0.7 + rng() * 0.15;
  return 0.3 + rng() * 0.15;
}
