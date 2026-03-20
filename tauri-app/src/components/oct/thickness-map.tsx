import { useRef, useEffect } from "react";
import { generateETDRS, ETDRS_NORMAL, thicknessColor, normativeColor, type Pathology } from "@/lib/oct-synthetic";

interface ThicknessMapProps {
  seed: number;
  pathology: Pathology;
  showColors?: boolean;
}

const SECTOR_LAYOUT = [
  { key: "outerSup",  cx: 0, cy: -3, r1: 2.5, r2: 4, a1: -60, a2: 60 },
  { key: "outerNas",  cx: 3, cy: 0,  r1: 2.5, r2: 4, a1: 30, a2: 150 },
  { key: "outerInf",  cx: 0, cy: 3,  r1: 2.5, r2: 4, a1: 120, a2: 240 },
  { key: "outerTemp", cx: -3, cy: 0, r1: 2.5, r2: 4, a1: 210, a2: 330 },
  { key: "innerSup",  cx: 0, cy: -1.5, r1: 0.8, r2: 2.5, a1: -60, a2: 60 },
  { key: "innerNas",  cx: 1.5, cy: 0, r1: 0.8, r2: 2.5, a1: 30, a2: 150 },
  { key: "innerInf",  cx: 0, cy: 1.5, r1: 0.8, r2: 2.5, a1: 120, a2: 240 },
  { key: "innerTemp", cx: -1.5, cy: 0, r1: 0.8, r2: 2.5, a1: 210, a2: 330 },
  { key: "fovea",     cx: 0, cy: 0, r1: 0, r2: 0.8, a1: 0, a2: 360 },
];

export function ThicknessMap({ seed, pathology, showColors = true }: ThicknessMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const size = canvas.width;
    const cx = size / 2;
    const cy = size / 2;
    const scale = size / 10;

    ctx.fillStyle = "#0a0a0a";
    ctx.fillRect(0, 0, size, size);

    const data = generateETDRS(seed, pathology);

    // Draw color map using pixel-level interpolation
    const minV = 150;
    const maxV = 420;

    for (let py = 0; py < size; py++) {
      for (let px = 0; px < size; px++) {
        const dx = (px - cx) / scale;
        const dy = (py - cy) / scale;
        const r = Math.sqrt(dx * dx + dy * dy);
        if (r > 4.2) continue;

        // Find sector
        const angle = ((Math.atan2(dy, dx) * 180 / Math.PI) + 360) % 360;
        let value: number | null = null;

        if (r < 0.8) value = data.fovea;
        else if (r < 2.5) {
          if (angle >= 300 || angle < 60) value = data.innerSup;
          else if (angle >= 60 && angle < 150) value = data.innerNas;
          else if (angle >= 150 && angle < 240) value = data.innerInf;
          else value = data.innerTemp;
        } else {
          if (angle >= 300 || angle < 60) value = data.outerSup;
          else if (angle >= 60 && angle < 150) value = data.outerNas;
          else if (angle >= 150 && angle < 240) value = data.outerInf;
          else value = data.outerTemp;
        }

        if (value !== null) {
          const [cr, cg, cb] = thicknessColor(value, minV, maxV);
          ctx.fillStyle = `rgb(${cr},${cg},${cb})`;
          ctx.fillRect(px, py, 1, 1);
        }
      }
    }

    // ETDRS grid lines
    ctx.strokeStyle = "rgba(0,0,0,0.5)";
    ctx.lineWidth = 1.5;
    for (const r of [0.8, 2.5, 4.2]) {
      ctx.beginPath();
      ctx.arc(cx, cy, r * scale, 0, Math.PI * 2);
      ctx.stroke();
    }
    // Quadrant lines
    for (const angle of [60, 150, 240, 330]) {
      const rad = (angle * Math.PI) / 180;
      ctx.beginPath();
      ctx.moveTo(cx + Math.cos(rad) * 0.8 * scale, cy + Math.sin(rad) * 0.8 * scale);
      ctx.lineTo(cx + Math.cos(rad) * 4.2 * scale, cy + Math.sin(rad) * 4.2 * scale);
      ctx.stroke();
    }

    // Values with normative colors or white
    ctx.font = `bold ${Math.max(10, size * 0.055)}px monospace`;
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";

    const positions: Record<string, [number, number]> = {
      fovea: [0, 0], innerSup: [0, -1.6], innerNas: [1.6, 0],
      innerInf: [0, 1.6], innerTemp: [-1.6, 0],
      outerSup: [0, -3.3], outerNas: [3.3, 0],
      outerInf: [0, 3.3], outerTemp: [-3.3, 0],
    };

    for (const [sec, [px, py]] of Object.entries(positions)) {
      const val = data[sec];
      if (val === undefined) continue;
      const norm = ETDRS_NORMAL[sec];

      // Shadow for readability
      ctx.fillStyle = "rgba(0,0,0,0.7)";
      ctx.fillText(String(val), cx + px * scale + 1, cy + py * scale + 1);

      ctx.fillStyle = showColors && norm ? normativeColor(val, norm) : "#fff";
      ctx.fillText(String(val), cx + px * scale, cy + py * scale);
    }

    // Title
    ctx.fillStyle = "rgba(255,255,255,0.4)";
    ctx.font = "bold 9px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("Macular Thickness (µm)", 4, 12);

    // Color bar
    const barX = size - 18;
    const barH = size * 0.6;
    const barY = (size - barH) / 2;
    for (let i = 0; i < barH; i++) {
      const t = 1 - i / barH;
      const val = minV + t * (maxV - minV);
      const [cr, cg, cb] = thicknessColor(val, minV, maxV);
      ctx.fillStyle = `rgb(${cr},${cg},${cb})`;
      ctx.fillRect(barX, barY + i, 10, 1);
    }
    ctx.fillStyle = "rgba(255,255,255,0.3)";
    ctx.font = "7px monospace";
    ctx.textAlign = "left";
    ctx.fillText(`${maxV}`, barX - 2, barY - 3);
    ctx.fillText(`${minV}`, barX - 2, barY + barH + 8);

  }, [seed, pathology, showColors]);

  return (
    <div className="rounded border ls-border bg-black overflow-hidden">
      <canvas ref={canvasRef} width={220} height={220} className="block w-full aspect-square" />
    </div>
  );
}
