import { useRef, useEffect } from "react";
import { generateRNFLProfile, RNFL_NORMAL, type Pathology } from "@/lib/oct-synthetic";

interface RNFLTSNITProps {
  seed: number;
  pathology: Pathology;
}

export function RNFLTSNIT({ seed, pathology }: RNFLTSNITProps) {
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

    ctx.fillStyle = "#0a0a0a";
    ctx.fillRect(0, 0, w, h);

    const p = pathology === "glaucoma" ? "glaucoma" : "normal";
    const profile = generateRNFLProfile(seed, p);

    const margin = { top: 20, right: 10, bottom: 25, left: 35 };
    const pw = w - margin.left - margin.right;
    const ph = h - margin.top - margin.bottom;

    const xScale = (deg: number) => margin.left + (deg / 360) * pw;
    const yScale = (t: number) => margin.top + ph - ((t - 20) / 180) * ph;

    // Normal band (p5-p95 across TSNIT)
    const bandPoints: { deg: number; p5: number; p95: number }[] = [];
    for (let deg = 0; deg < 360; deg++) {
      // Estimate p5/p95 based on position
      let sector: string;
      if (deg < 45) sector = "T";
      else if (deg < 90) sector = "TS";
      else if (deg < 135) sector = "S";
      else if (deg < 180) sector = "NS";
      else if (deg < 225) sector = "N";
      else if (deg < 270) sector = "NI";
      else if (deg < 315) sector = "I";
      else sector = "TI";
      const norm = RNFL_NORMAL[sector];
      bandPoints.push({ deg, p5: norm.p5, p95: norm.p95 });
    }

    // Draw normal band (green zone)
    ctx.fillStyle = "rgba(74,222,128,0.08)";
    ctx.beginPath();
    bandPoints.forEach((p, i) => {
      const x = xScale(p.deg);
      const y = yScale(p.p95);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    for (let i = bandPoints.length - 1; i >= 0; i--) {
      ctx.lineTo(xScale(bandPoints[i].deg), yScale(bandPoints[i].p5));
    }
    ctx.closePath();
    ctx.fill();

    // Draw p5 and p95 lines
    ctx.strokeStyle = "rgba(74,222,128,0.2)";
    ctx.lineWidth = 0.5;
    ctx.setLineDash([3, 3]);
    ctx.beginPath();
    bandPoints.forEach((p, i) => { const x = xScale(p.deg); if (i === 0) ctx.moveTo(x, yScale(p.p95)); else ctx.lineTo(x, yScale(p.p95)); });
    ctx.stroke();
    ctx.beginPath();
    bandPoints.forEach((p, i) => { const x = xScale(p.deg); if (i === 0) ctx.moveTo(x, yScale(p.p5)); else ctx.lineTo(x, yScale(p.p5)); });
    ctx.stroke();
    ctx.setLineDash([]);

    // Grid
    ctx.strokeStyle = "rgba(255,255,255,0.05)";
    ctx.lineWidth = 0.5;
    for (const t of [50, 100, 150]) {
      ctx.beginPath(); ctx.moveTo(margin.left, yScale(t)); ctx.lineTo(w - margin.right, yScale(t)); ctx.stroke();
      ctx.fillStyle = "rgba(255,255,255,0.2)";
      ctx.font = "8px monospace";
      ctx.textAlign = "right";
      ctx.fillText(`${t}`, margin.left - 3, yScale(t) + 3);
    }

    // TSNIT labels
    ctx.fillStyle = "rgba(255,255,255,0.25)";
    ctx.font = "bold 9px sans-serif";
    ctx.textAlign = "center";
    ["T", "S", "N", "I", "T"].forEach((lbl, i) => {
      ctx.fillText(lbl, xScale(i * 90), h - 5);
    });

    // Profile line
    ctx.strokeStyle = "rgba(255,200,50,0.9)";
    ctx.lineWidth = 1.5;
    ctx.beginPath();
    profile.forEach((p, i) => {
      const x = xScale(p.angle);
      const y = yScale(p.thickness);
      if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // µm label
    ctx.fillStyle = "rgba(255,255,255,0.15)";
    ctx.font = "7px sans-serif";
    ctx.save();
    ctx.translate(8, margin.top + ph / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.fillText("µm", 0, 0);
    ctx.restore();

    // Title
    ctx.fillStyle = "rgba(255,255,255,0.3)";
    ctx.font = "bold 8px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("RNFL TSNIT", margin.left, 12);

  }, [seed, pathology]);

  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const obs = new ResizeObserver(() => { canvasRef.current?.dispatchEvent(new Event("resize")); });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  return (
    <div ref={containerRef} className="h-full w-full rounded border border-white/[0.06] bg-black overflow-hidden">
      <canvas ref={canvasRef} className="block h-full w-full" />
    </div>
  );
}
