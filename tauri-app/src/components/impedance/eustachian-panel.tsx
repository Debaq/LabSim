/**
 * Panel de función tubárica.
 * Tres timpanogramas superpuestos: basal, post-Toynbee, post-Valsalva.
 * Se observa si el pico se desplaza, indicando función tubárica.
 */

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Play } from "lucide-react";
import { generateEustachianTest, type EustachianResult, type TympanogramPoint } from "@/lib/impedance-synthetic";
import type { EarPhysiology } from "@/modules/impedance/schema";

interface Props {
  ear: EarPhysiology;
  seed: number;
  variance: number;
  pressureRange: [number, number];
}

const CHART_W = 380;
const CHART_H = 180;
const PAD = { top: 15, right: 15, bottom: 30, left: 45 };
const INNER_W = CHART_W - PAD.left - PAD.right;
const INNER_H = CHART_H - PAD.top - PAD.bottom;

const CURVE_COLORS = {
  basal: "#94a3b8",       // gris — basal
  postToynbee: "#22d3ee", // cyan — post Toynbee
  postValsalva: "#f472b6", // pink — post Valsalva
};

export function EustachianPanel({ ear, seed, variance, pressureRange }: Props) {
  const [result, setResult] = useState<EustachianResult | null>(null);
  const [step, setStep] = useState<"idle" | "basal" | "toynbee" | "valsalva" | "done">("idle");

  const handleStart = () => {
    const r = generateEustachianTest(ear, seed, variance);
    setResult(r);
    setStep("basal");
    // Simular secuencia de pasos
    setTimeout(() => setStep("toynbee"), 1500);
    setTimeout(() => setStep("valsalva"), 3000);
    setTimeout(() => setStep("done"), 4500);
  };

  const [pMin, pMax] = pressureRange;

  if (!result) {
    return (
      <div className="flex flex-col items-center gap-2 py-4">
        <span className="text-[10px] ls-text-muted">Función tubárica — 3 timpanogramas</span>
        <Button size="xs" variant="ghost" onClick={handleStart} className="gap-1 text-[10px]">
          <Play className="h-3 w-3" />
          Iniciar secuencia
        </Button>
      </div>
    );
  }

  const allPoints = [...result.basal, ...result.postToynbee, ...result.postValsalva];
  const maxCompliance = Math.max(2, ...allPoints.map((d) => d.compliance)) * 1.1;

  const xScale = (p: number) => PAD.left + ((p - pMin) / (pMax - pMin)) * INNER_W;
  const yScale = (c: number) => PAD.top + INNER_H - (c / maxCompliance) * INNER_H;

  const curvePath = (points: TympanogramPoint[]) =>
    points.map((p, i) => `${i === 0 ? "M" : "L"} ${xScale(p.pressure).toFixed(1)} ${yScale(p.compliance).toFixed(1)}`).join(" ");

  const showBasal = step !== "idle";
  const showToynbee = step === "toynbee" || step === "valsalva" || step === "done";
  const showValsalva = step === "valsalva" || step === "done";

  // Presiones pico de cada curva
  const basalPeak = result.basal.reduce((b, p) => p.compliance > b.compliance ? p : b, result.basal[0]);
  const toynbeePeak = result.postToynbee.reduce((b, p) => p.compliance > b.compliance ? p : b, result.postToynbee[0]);
  const valsalvaPeak = result.postValsalva.reduce((b, p) => p.compliance > b.compliance ? p : b, result.postValsalva[0]);

  return (
    <div className="flex flex-col">
      <svg width={CHART_W} height={CHART_H} className="ls-bg">
        {/* Grid */}
        {Array.from({ length: 7 }, (_, i) => pMin + i * 100).filter((p) => p <= pMax).map((p) => (
          <line key={p} x1={xScale(p)} y1={PAD.top} x2={xScale(p)} y2={PAD.top + INNER_H} stroke="var(--ls-border)" strokeWidth={0.5} />
        ))}
        <line x1={PAD.left} y1={PAD.top + INNER_H} x2={PAD.left + INNER_W} y2={PAD.top + INNER_H} stroke="var(--ls-text-muted)" strokeWidth={1} />
        <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={PAD.top + INNER_H} stroke="var(--ls-text-muted)" strokeWidth={1} />

        {/* Curves */}
        {showBasal && <path d={curvePath(result.basal)} fill="none" stroke={CURVE_COLORS.basal} strokeWidth={1.2} />}
        {showToynbee && <path d={curvePath(result.postToynbee)} fill="none" stroke={CURVE_COLORS.postToynbee} strokeWidth={1.2} />}
        {showValsalva && <path d={curvePath(result.postValsalva)} fill="none" stroke={CURVE_COLORS.postValsalva} strokeWidth={1.2} />}

        {/* Axis labels */}
        <text x={CHART_W / 2} y={CHART_H - 3} textAnchor="middle" className="text-[8px]" fill="var(--ls-text-muted)">daPa</text>
      </svg>

      {/* Leyenda + valores */}
      <div className="flex gap-3 px-2 py-1.5 text-[9px]">
        <div className="flex items-center gap-1">
          <div className="h-1.5 w-3 rounded" style={{ background: CURVE_COLORS.basal }} />
          <span className="ls-text-muted">Basal ({basalPeak.pressure} daPa)</span>
        </div>
        {showToynbee && (
          <div className="flex items-center gap-1">
            <div className="h-1.5 w-3 rounded" style={{ background: CURVE_COLORS.postToynbee }} />
            <span className="ls-text-muted">Toynbee ({toynbeePeak.pressure} daPa)</span>
          </div>
        )}
        {showValsalva && (
          <div className="flex items-center gap-1">
            <div className="h-1.5 w-3 rounded" style={{ background: CURVE_COLORS.postValsalva }} />
            <span className="ls-text-muted">Valsalva ({valsalvaPeak.pressure} daPa)</span>
          </div>
        )}
      </div>

      {step === "done" && (
        <div className="px-2 py-1">
          <Button size="xs" variant="ghost" onClick={handleStart} className="gap-1 text-[10px]">
            <Play className="h-3 w-3" />
            Repetir
          </Button>
        </div>
      )}
    </div>
  );
}
