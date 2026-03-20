import { useRef, useEffect } from "react";
import { generateBScan, LAYERS, type Pathology } from "@/lib/oct-synthetic";

interface BScanViewProps {
  seed: number;
  isMacular: boolean;
  pathology: Pathology;
}

export function BScanView({ seed, isMacular, pathology }: BScanViewProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const w = container.clientWidth;
    const h = container.clientHeight;
    canvas.width = w;
    canvas.height = h;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Background
    ctx.fillStyle = "#000";
    ctx.fillRect(0, 0, w, h);

    const p = pathology === "edema" || pathology === "drusen" || pathology === "atrophy" ? pathology : pathology === "glaucoma" ? "glaucoma" : "normal";
    const { layers, height: dataH } = generateBScan(w, isMacular, seed, p as "normal" | "glaucoma" | "edema" | "drusen");
    const scaleY = h / dataH;

    // Draw speckle noise (OCT texture)
    const imgData = ctx.getImageData(0, 0, w, h);
    const data = imgData.data;

    // Fill with retinal tissue between ILM and RPE
    const ilm = layers.ILM;
    const rpe = layers.RPE;
    for (let x = 0; x < w; x++) {
      const top = ilm[x] * scaleY;
      const bot = (rpe[x] + 12) * scaleY;
      for (let y = Math.max(0, Math.floor(top)); y < Math.min(h, Math.ceil(bot)); y++) {
        const idx = (y * w + x) * 4;
        // Base brightness based on layer position
        const relPos = (y - top) / (bot - top);
        let brightness = 60;

        // Layer-specific brightness
        for (let li = 0; li < LAYERS.length - 1; li++) {
          const layerY = layers[LAYERS[li]][x] * scaleY;
          const nextY = layers[LAYERS[li + 1]][x] * scaleY;
          if (y >= layerY && y < nextY) {
            // Hyperreflective layers: RNFL, GCL+IPL, OPL, IS/OS, RPE
            if (["RNFL", "GCL", "OPL", "IS/OS", "RPE"].includes(LAYERS[li])) {
              brightness = 140 + Math.random() * 40;
            } else if (LAYERS[li] === "INL") {
              brightness = 80 + Math.random() * 20;
            } else {
              brightness = 50 + Math.random() * 20;
            }
            break;
          }
        }

        // Speckle noise
        brightness += (Math.random() - 0.5) * 30;
        brightness = Math.max(0, Math.min(255, brightness));

        data[idx] = brightness;
        data[idx + 1] = brightness;
        data[idx + 2] = brightness;
        data[idx + 3] = 255;
      }
    }

    ctx.putImageData(imgData, 0, 0);

    // Draw layer lines (subtle)
    for (const layer of LAYERS) {
      const pts = layers[layer];
      ctx.strokeStyle = layer === "ILM" || layer === "RPE" ? "rgba(0,200,255,0.3)" : "rgba(0,200,255,0.1)";
      ctx.lineWidth = layer === "ILM" || layer === "RPE" ? 1 : 0.5;
      ctx.beginPath();
      for (let x = 0; x < w; x++) {
        const y = pts[x] * scaleY;
        if (x === 0) ctx.moveTo(x, y);
        else ctx.lineTo(x, y);
      }
      ctx.stroke();
    }

    // Layer labels on right edge
    ctx.fillStyle = "rgba(0,200,255,0.4)";
    ctx.font = "8px monospace";
    ctx.textAlign = "right";
    for (const layer of LAYERS) {
      const y = layers[layer][w - 5] * scaleY;
      ctx.fillText(layer, w - 2, y + 3);
    }

  }, [seed, isMacular, pathology]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => {
      if (canvasRef.current) canvasRef.current.dispatchEvent(new Event("resize"));
    });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="h-full w-full rounded border border-white/[0.06] bg-black overflow-hidden">
      <canvas ref={canvasRef} className="block h-full w-full" />
    </div>
  );
}
