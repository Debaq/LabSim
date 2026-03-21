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
    if (w <= 0 || h <= 0) return;
    canvas.width = w;
    canvas.height = h;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const imgData = generateBScan(w, h, isMacular, seed, pathology);
    ctx.putImageData(imgData, 0, 0);

    // Layer labels
    const colors = ["#00d4ff", "#00ccff", "#7799ff", "#99bbff", "#7799ff", "#ffcc55", "#5577aa", "#ffdd77", "#ff5533", "#ffaa33"];
    const labelY = [0.18, 0.22, 0.27, 0.32, 0.37, 0.43, 0.55, 0.62, 0.645, 0.67];
    ctx.font = "bold 9px monospace";
    ctx.textAlign = "right";
    LAYERS.forEach((layer, i) => {
      ctx.fillStyle = colors[i];
      ctx.globalAlpha = 0.7;
      ctx.fillText(layer, w - 4, h * labelY[i]);
    });
    ctx.globalAlpha = 1;

    // Scale bar
    ctx.fillStyle = "rgba(255,255,255,0.6)";
    ctx.fillRect(w - 55, h - 18, 35, 1.5);
    ctx.font = "7px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText("200 µm", w - 37, h - 7);

  }, [seed, isMacular, pathology]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => { canvasRef.current?.dispatchEvent(new Event("resize")); });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="h-full w-full rounded border ls-border bg-black overflow-hidden">
      <canvas ref={canvasRef} className="block h-full w-full" />
    </div>
  );
}
