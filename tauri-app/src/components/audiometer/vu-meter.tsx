import { useEffect, useRef, useCallback } from "react";

interface VuMeterProps {
  level: number;
  active: boolean;
  height?: number;
}

export function VuMeter({ level, active, height = 14 }: VuMeterProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    const container = containerRef.current;
    if (!canvas || !container) return;

    const w = container.clientWidth;
    if (w <= 0) return;
    canvas.width = w;
    canvas.height = height;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.clearRect(0, 0, w, height);
    ctx.fillStyle = "rgba(0,0,0,0.7)";
    ctx.beginPath();
    ctx.roundRect(0, 0, w, height, 2);
    ctx.fill();

    const segs = Math.max(8, Math.floor(w / 7));
    const gap = 1;
    const segW = (w - 4) / segs - gap;
    const segH = height - 4;
    const dl = active ? level : 0;

    for (let i = 0; i < segs; i++) {
      const t = (i / segs) * 100;
      const lit = dl > t;
      if (lit) {
        ctx.fillStyle = i >= segs * 0.85 ? "rgba(239,68,68,0.9)" : i >= segs * 0.65 ? "rgba(251,191,36,0.85)" : "rgba(74,222,128,0.7)";
      } else {
        ctx.fillStyle = i >= segs * 0.85 ? "rgba(239,68,68,0.08)" : i >= segs * 0.65 ? "rgba(251,191,36,0.06)" : "rgba(74,222,128,0.05)";
      }
      ctx.fillRect(2 + i * (segW + gap), 2, segW, segH);
    }
  }, [level, active, height]);

  useEffect(() => { draw(); }, [draw]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => draw());
    obs.observe(el);
    return () => obs.disconnect();
  }, [draw]);

  return (
    <div ref={containerRef} className="w-full">
      <canvas ref={canvasRef} height={height} className="block w-full rounded-sm" style={{ height }} />
    </div>
  );
}
