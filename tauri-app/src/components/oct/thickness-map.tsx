import { useRef, useEffect } from "react";
import { generateMacularMap, type Pathology } from "@/lib/oct-synthetic";

interface ThicknessMapProps {
  seed: number;
  pathology: Pathology;
  type: "macular" | "rnfl";
}

export function ThicknessMap({ seed, pathology, type }: ThicknessMapProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const size = canvas.width;
    ctx.fillStyle = "#0a0a0a";
    ctx.fillRect(0, 0, size, size);

    const p = (pathology === "edema" || pathology === "atrophy") ? pathology : "normal";
    const data = generateMacularMap(seed, p as "normal" | "edema" | "atrophy");
    const cellSize = size / 9;

    // Draw cells with color interpolation
    data.forEach((pt) => {
      const px = (pt.x + 4) * cellSize;
      const py = (pt.y + 4) * cellSize;

      // Color: blue(thin) -> green(normal) -> yellow -> red(thick)
      const t = pt.thickness;
      let r: number, g: number, b: number;

      if (type === "macular") {
        // Macular: 200-400 range
        const norm = (t - 200) / 200;
        if (norm < 0.3) { r = 50; g = 100 + norm * 400; b = 200 - norm * 300; }
        else if (norm < 0.6) { r = 50 + (norm - 0.3) * 600; g = 220; b = 50; }
        else { r = 230; g = 220 - (norm - 0.6) * 500; b = 50; }
      } else {
        // RNFL: 40-180 range
        const norm = (t - 40) / 140;
        if (norm < 0.3) { r = 200; g = 50 + norm * 300; b = 50; }
        else if (norm < 0.7) { r = 50 + (0.7 - norm) * 200; g = 200; b = 50; }
        else { r = 50; g = 200; b = 50 + (norm - 0.7) * 300; }
      }

      // Circular mask (ETDRS grid is circular)
      const dist = Math.sqrt(pt.x * pt.x + pt.y * pt.y);
      if (dist > 4.5) return;

      ctx.fillStyle = `rgb(${Math.round(r)},${Math.round(g)},${Math.round(b)})`;
      ctx.fillRect(px, py, cellSize - 1, cellSize - 1);

      // Thickness number
      ctx.fillStyle = "rgba(255,255,255,0.7)";
      ctx.font = `bold ${Math.max(8, cellSize * 0.35)}px monospace`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      ctx.fillText(String(t), px + cellSize / 2, py + cellSize / 2);
    });

    // ETDRS rings
    ctx.strokeStyle = "rgba(255,255,255,0.15)";
    ctx.lineWidth = 1;
    const cx = size / 2;
    for (const r of [0.5, 1.5, 3]) {
      ctx.beginPath();
      ctx.arc(cx, cx, r * cellSize, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Cross
    ctx.strokeStyle = "rgba(255,255,255,0.08)";
    ctx.beginPath();
    ctx.moveTo(0, cx); ctx.lineTo(size, cx);
    ctx.moveTo(cx, 0); ctx.lineTo(cx, size);
    ctx.stroke();

    // Title
    ctx.fillStyle = "rgba(255,255,255,0.25)";
    ctx.font = "bold 8px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText(type === "macular" ? "Macular (µm)" : "RNFL (µm)", 4, 10);

  }, [seed, pathology, type]);

  return (
    <div className="rounded border border-white/[0.06] bg-black overflow-hidden">
      <canvas ref={canvasRef} width={180} height={180} className="block w-full aspect-square" />
    </div>
  );
}
