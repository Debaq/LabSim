import { useRef, useEffect } from "react";
import { generateRNFLProfile, RNFL_CLOCK_HOURS, type Pathology } from "@/lib/oct-synthetic";

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
    if (w <= 0 || h <= 0) return;
    canvas.width = w;
    canvas.height = h;

    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    ctx.fillStyle = "#0a0c0f";
    ctx.fillRect(0, 0, w, h);

    const p = pathology === "glaucoma" ? "glaucoma" : "normal";
    const profile = generateRNFLProfile(seed, p);

    const m = { top: 22, right: 12, bottom: 28, left: 38 };
    const pw = w - m.left - m.right;
    const ph = h - m.top - m.bottom;

    const xS = (deg: number) => m.left + (deg / 360) * pw;
    const yS = (t: number) => m.top + ph - ((t - 10) / 190) * ph;

    // Normal band from clock hours (interpolated)
    const p95: number[] = [];
    const p5: number[] = [];
    const p1: number[] = [];
    for (let deg = 0; deg < 360; deg++) {
      const hour = Math.floor(deg / 30) + 1;
      const hourData = RNFL_CLOCK_HOURS[hour > 12 ? hour - 12 : hour] ?? RNFL_CLOCK_HOURS[1];
      p95.push(hourData.mean * 1.15);
      p5.push(hourData.p5);
      p1.push(hourData.p1);
    }

    // Green band (p5 to p95)
    ctx.fillStyle = "rgba(34,197,94,0.12)";
    ctx.beginPath();
    for (let deg = 0; deg < 360; deg++) { const x = xS(deg); if (deg === 0) ctx.moveTo(x, yS(p95[deg])); else ctx.lineTo(x, yS(p95[deg])); }
    for (let deg = 359; deg >= 0; deg--) ctx.lineTo(xS(deg), yS(p5[deg]));
    ctx.closePath();
    ctx.fill();

    // Yellow band (p1 to p5)
    ctx.fillStyle = "rgba(234,179,8,0.08)";
    ctx.beginPath();
    for (let deg = 0; deg < 360; deg++) { const x = xS(deg); if (deg === 0) ctx.moveTo(x, yS(p5[deg])); else ctx.lineTo(x, yS(p5[deg])); }
    for (let deg = 359; deg >= 0; deg--) ctx.lineTo(xS(deg), yS(p1[deg]));
    ctx.closePath();
    ctx.fill();

    // Red zone below p1
    ctx.fillStyle = "rgba(239,68,68,0.06)";
    ctx.beginPath();
    for (let deg = 0; deg < 360; deg++) { const x = xS(deg); if (deg === 0) ctx.moveTo(x, yS(p1[deg])); else ctx.lineTo(x, yS(p1[deg])); }
    ctx.lineTo(xS(359), yS(10));
    ctx.lineTo(xS(0), yS(10));
    ctx.closePath();
    ctx.fill();

    // Band boundary lines
    ctx.setLineDash([2, 3]);
    ctx.lineWidth = 0.5;
    ctx.strokeStyle = "rgba(34,197,94,0.25)";
    ctx.beginPath(); for (let d = 0; d < 360; d++) { if (d === 0) ctx.moveTo(xS(d), yS(p95[d])); else ctx.lineTo(xS(d), yS(p95[d])); } ctx.stroke();
    ctx.strokeStyle = "rgba(234,179,8,0.3)";
    ctx.beginPath(); for (let d = 0; d < 360; d++) { if (d === 0) ctx.moveTo(xS(d), yS(p5[d])); else ctx.lineTo(xS(d), yS(p5[d])); } ctx.stroke();
    ctx.strokeStyle = "rgba(239,68,68,0.25)";
    ctx.beginPath(); for (let d = 0; d < 360; d++) { if (d === 0) ctx.moveTo(xS(d), yS(p1[d])); else ctx.lineTo(xS(d), yS(p1[d])); } ctx.stroke();
    ctx.setLineDash([]);

    // Y grid
    ctx.strokeStyle = "rgba(255,255,255,0.04)";
    ctx.lineWidth = 0.5;
    for (const t of [50, 100, 150]) {
      ctx.beginPath(); ctx.moveTo(m.left, yS(t)); ctx.lineTo(w - m.right, yS(t)); ctx.stroke();
      ctx.fillStyle = "rgba(255,255,255,0.2)";
      ctx.font = "8px monospace";
      ctx.textAlign = "right";
      ctx.fillText(`${t}`, m.left - 3, yS(t) + 3);
    }

    // TSNIT sector separators
    ctx.strokeStyle = "rgba(255,255,255,0.06)";
    for (const deg of [90, 180, 270]) {
      ctx.beginPath(); ctx.moveTo(xS(deg), m.top); ctx.lineTo(xS(deg), h - m.bottom); ctx.stroke();
    }

    // TSNIT labels
    ctx.fillStyle = "rgba(255,255,255,0.35)";
    ctx.font = "bold 10px sans-serif";
    ctx.textAlign = "center";
    ["T", "S", "N", "I", "T"].forEach((lbl, i) => ctx.fillText(lbl, xS(i * 90), h - 8));

    // Profile line — thick, yellow/orange
    ctx.strokeStyle = "#f59e0b";
    ctx.lineWidth = 2;
    ctx.shadowColor = "rgba(245,158,11,0.3)";
    ctx.shadowBlur = 4;
    ctx.beginPath();
    profile.forEach((pt, i) => { const x = xS(pt.angle); const y = yS(pt.thickness); if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); });
    ctx.stroke();
    ctx.shadowBlur = 0;

    // µm axis label
    ctx.fillStyle = "rgba(255,255,255,0.15)";
    ctx.font = "7px sans-serif";
    ctx.save();
    ctx.translate(10, m.top + ph / 2);
    ctx.rotate(-Math.PI / 2);
    ctx.textAlign = "center";
    ctx.fillText("Espesor (µm)", 0, 0);
    ctx.restore();

    // Title
    ctx.fillStyle = "rgba(255,255,255,0.4)";
    ctx.font = "bold 9px sans-serif";
    ctx.textAlign = "left";
    ctx.fillText("RNFL TSNIT Profile", m.left, 14);

    // Legend
    const lx = w - 80;
    ctx.font = "7px sans-serif";
    ctx.fillStyle = "rgba(34,197,94,0.6)"; ctx.fillRect(lx, 5, 8, 6); ctx.fillStyle = "rgba(255,255,255,0.3)"; ctx.textAlign = "left"; ctx.fillText("Normal", lx + 11, 10);
    ctx.fillStyle = "rgba(234,179,8,0.6)"; ctx.fillRect(lx, 13, 8, 6); ctx.fillStyle = "rgba(255,255,255,0.3)"; ctx.fillText("Límite", lx + 11, 18);
    ctx.fillStyle = "rgba(239,68,68,0.6)"; ctx.fillRect(lx, 21, 8, 6); ctx.fillStyle = "rgba(255,255,255,0.3)"; ctx.fillText("Fuera", lx + 11, 26);

  }, [seed, pathology]);

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
