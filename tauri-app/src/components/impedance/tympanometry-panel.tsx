/**
 * Panel de timpanometría.
 * Muestra la curva compliance vs presión con animación de sweep en tiempo real.
 * Como un equipo real: la curva se traza de derecha a izquierda mientras el
 * equipo varía la presión de +200 a -400 daPa.
 */

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Play, Square } from "lucide-react";
import type { TympanogramPoint } from "@/lib/impedance-synthetic";
import type { ImpedanceSettings } from "./impedance-controls";

interface Props {
  data: TympanogramPoint[];
  settings: ImpedanceSettings;
  onStart: () => void;
  isRunning: boolean;
}

const CHART_W = 400;
const CHART_H = 200;
const PAD = { top: 20, right: 20, bottom: 30, left: 50 };
const INNER_W = CHART_W - PAD.left - PAD.right;
const INNER_H = CHART_H - PAD.top - PAD.bottom;

export function TympanometryPanel({ data, settings, onStart, isRunning }: Props) {
  const [visibleCount, setVisibleCount] = useState(0);
  const animRef = useRef<number | null>(null);

  // Velocidad del sweep
  const speedMs = settings.sweepSpeed === "slow" ? 80 : settings.sweepSpeed === "fast" ? 15 : 35;

  // Animar la curva punto por punto
  useEffect(() => {
    if (!isRunning || data.length === 0) return;
    setVisibleCount(0);

    let count = 0;
    const tick = () => {
      count++;
      setVisibleCount(count);
      if (count < data.length) {
        animRef.current = window.setTimeout(tick, speedMs);
      }
    };
    animRef.current = window.setTimeout(tick, speedMs);

    return () => {
      if (animRef.current) clearTimeout(animRef.current);
    };
  }, [isRunning, data, speedMs]);

  // Escalas
  const pMin = settings.pressureMin;
  const pMax = settings.pressureMax;
  const maxCompliance = Math.max(2, ...data.map((d) => d.compliance)) * 1.1;

  const xScale = (pressure: number) => PAD.left + ((pressure - pMin) / (pMax - pMin)) * INNER_W;
  const yScale = (compliance: number) => PAD.top + INNER_H - (compliance / maxCompliance) * INNER_H;

  const visibleData = data.slice(0, visibleCount);

  // Path de la curva
  const pathD = visibleData
    .map((p, i) => `${i === 0 ? "M" : "L"} ${xScale(p.pressure).toFixed(1)} ${yScale(p.compliance).toFixed(1)}`)
    .join(" ");

  // Encontrar pico
  const peak = data.reduce((best, p) => (p.compliance > best.compliance ? p : best), data[0] ?? { pressure: 0, compliance: 0 });

  // Grid lines
  const pressureTicks = [];
  for (let p = pMin; p <= pMax; p += 100) pressureTicks.push(p);
  const complianceTicks = [];
  for (let c = 0; c <= maxCompliance; c += 0.5) complianceTicks.push(c);

  return (
    <div className="flex flex-col">
      {/* Chart */}
      <svg width={CHART_W} height={CHART_H} className="ls-bg">
        {/* Grid */}
        {pressureTicks.map((p) => (
          <line key={`gx${p}`} x1={xScale(p)} y1={PAD.top} x2={xScale(p)} y2={PAD.top + INNER_H} stroke="var(--ls-border)" strokeWidth={0.5} />
        ))}
        {complianceTicks.map((c) => (
          <line key={`gy${c}`} x1={PAD.left} y1={yScale(c)} x2={PAD.left + INNER_W} y2={yScale(c)} stroke="var(--ls-border)" strokeWidth={0.5} />
        ))}

        {/* Axes */}
        <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={PAD.top + INNER_H} stroke="var(--ls-text-muted)" strokeWidth={1} />
        <line x1={PAD.left} y1={PAD.top + INNER_H} x2={PAD.left + INNER_W} y2={PAD.top + INNER_H} stroke="var(--ls-text-muted)" strokeWidth={1} />

        {/* Axis labels */}
        {pressureTicks.map((p) => (
          <text key={`lx${p}`} x={xScale(p)} y={PAD.top + INNER_H + 14} textAnchor="middle" className="text-[8px]" fill="var(--ls-text-muted)">{p}</text>
        ))}
        {complianceTicks.filter((c) => c > 0).map((c) => (
          <text key={`ly${c}`} x={PAD.left - 6} y={yScale(c) + 3} textAnchor="end" className="text-[8px]" fill="var(--ls-text-muted)">{c.toFixed(1)}</text>
        ))}

        {/* Units */}
        <text x={CHART_W / 2} y={CHART_H - 2} textAnchor="middle" className="text-[8px]" fill="var(--ls-text-muted)">daPa</text>
        <text x={8} y={CHART_H / 2} textAnchor="middle" className="text-[8px]" fill="var(--ls-text-muted)" transform={`rotate(-90, 8, ${CHART_H / 2})`}>ml</text>

        {/* Curve */}
        {visibleData.length > 1 && (
          <path d={pathD} fill="none" stroke="#22d3ee" strokeWidth={1.5} />
        )}

        {/* Peak marker (solo cuando terminó) */}
        {!isRunning && visibleCount >= data.length && peak.compliance > 0.1 && (
          <>
            <circle cx={xScale(peak.pressure)} cy={yScale(peak.compliance)} r={3} fill="#22d3ee" />
            <line x1={xScale(peak.pressure)} y1={yScale(peak.compliance) + 5} x2={xScale(peak.pressure)} y2={PAD.top + INNER_H} stroke="#22d3ee" strokeWidth={0.5} strokeDasharray="3,3" />
          </>
        )}
      </svg>

      {/* Valores medidos */}
      {!isRunning && visibleCount >= data.length && (
        <div className="flex gap-4 px-2 py-1.5 text-[10px] font-mono">
          <span className="ls-text-muted">Ypeak: <span className="text-cyan-400">{peak.compliance.toFixed(2)} ml</span></span>
          <span className="ls-text-muted">Ppeak: <span className="text-cyan-400">{peak.pressure} daPa</span></span>
          <span className="ls-text-muted">Vea: <span className="text-cyan-400">{data[data.length - 1]?.compliance.toFixed(2) ?? "—"} ml</span></span>
        </div>
      )}

      {/* Botón */}
      <div className="flex gap-1 px-2 py-1">
        <Button
          size="xs"
          variant="ghost"
          onClick={onStart}
          disabled={isRunning}
          className="gap-1 text-[10px] ls-text-muted hover:ls-text"
        >
          {isRunning ? <Square className="h-3 w-3" /> : <Play className="h-3 w-3" />}
          {isRunning ? "Midiendo..." : "Iniciar"}
        </Button>
      </div>
    </div>
  );
}
