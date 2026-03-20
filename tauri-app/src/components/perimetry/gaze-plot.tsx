import { useRef, useEffect } from "react";

interface GazePlotProps {
  gazeHistory: { x: number; y: number; fixating: boolean }[];
}

export function GazePlot({ gazeHistory }: GazePlotProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const w = canvas.width;
    const h = canvas.height;
    const cx = w / 2;
    const cy = h / 2;

    ctx.fillStyle = "#0a0a0a";
    ctx.fillRect(0, 0, w, h);

    // Grid
    ctx.strokeStyle = "rgba(255,255,255,0.05)";
    ctx.lineWidth = 0.5;
    for (let i = 0; i <= 4; i++) {
      const x = (i / 4) * w;
      const y = (i / 4) * h;
      ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke();
      ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke();
    }

    // Center target zone
    ctx.strokeStyle = "rgba(0,255,100,0.1)";
    ctx.lineWidth = 1;
    ctx.beginPath();
    ctx.arc(cx, cy, 8, 0, Math.PI * 2);
    ctx.stroke();

    // Crosshair
    ctx.strokeStyle = "rgba(255,255,255,0.06)";
    ctx.beginPath();
    ctx.moveTo(cx, 0); ctx.lineTo(cx, h);
    ctx.moveTo(0, cy); ctx.lineTo(w, cy);
    ctx.stroke();

    // Gaze points
    const scale = 3; // degrees to pixels
    const last50 = gazeHistory.slice(-80);
    last50.forEach((pt, i) => {
      const alpha = 0.2 + (i / last50.length) * 0.8;
      const px = cx + pt.x * scale;
      const py = cy + pt.y * scale;
      ctx.fillStyle = pt.fixating
        ? `rgba(0,200,100,${alpha * 0.6})`
        : `rgba(255,60,60,${alpha * 0.8})`;
      ctx.beginPath();
      ctx.arc(px, py, 1.5, 0, Math.PI * 2);
      ctx.fill();
    });

  }, [gazeHistory]);

  return (
    <div className="rounded border border-white/[0.06] bg-black overflow-hidden">
      <div className="px-1.5 py-0.5 text-[7px] font-bold uppercase tracking-wider text-white/20 bg-black/50">
        Gaze Tracking
      </div>
      <canvas ref={canvasRef} width={160} height={100} className="block w-full" />
    </div>
  );
}
