/**
 * Panel de deterioro del reflejo (Reflex Decay / Tone Decay Test).
 * Estimulación sostenida 10 segundos. Se mide si la amplitud cae >50%.
 * Frecuencias típicas: 500 y 1000 Hz.
 */

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Play } from "lucide-react";
import { generateReflexDecay, type ReflexDecayTrace } from "@/lib/impedance-synthetic";
import type { EarPhysiology } from "@/modules/impedance/schema";

interface Props {
  ear: EarPhysiology;
  frequency: 500 | 1000;
  seed: number;
}

const CHART_W = 350;
const CHART_H = 120;
const PAD = { top: 10, right: 10, bottom: 20, left: 40 };
const INNER_W = CHART_W - PAD.left - PAD.right;
const INNER_H = CHART_H - PAD.top - PAD.bottom;

export function ReflexDecayPanel({ ear, frequency, seed }: Props) {
  const [trace, setTrace] = useState<ReflexDecayTrace | null>(null);
  const [visibleCount, setVisibleCount] = useState(0);
  const [measuring, setMeasuring] = useState(false);
  const animRef = useRef<number | null>(null);

  const decayKey = frequency === 500 ? "reflexDecay500" : "reflexDecay1000";
  const decayPercent = (ear[decayKey] as number | undefined) ?? 0;

  const handleStart = () => {
    const newTrace = generateReflexDecay(decayPercent, seed + frequency);
    setTrace(newTrace);
    setVisibleCount(0);
    setMeasuring(true);
  };

  useEffect(() => {
    if (!measuring || !trace) return;
    let count = 0;
    const tick = () => {
      count += 2;
      setVisibleCount(Math.min(count, trace.timeMs.length));
      if (count < trace.timeMs.length) {
        animRef.current = window.setTimeout(tick, 25);
      } else {
        setMeasuring(false);
      }
    };
    animRef.current = window.setTimeout(tick, 25);
    return () => { if (animRef.current) clearTimeout(animRef.current); };
  }, [measuring, trace]);

  if (!trace) {
    return (
      <div className="flex flex-col items-center gap-2 py-3">
        <span className="text-[10px] ls-text-muted">{frequency} Hz — Deterioro del reflejo</span>
        <Button size="xs" variant="ghost" onClick={handleStart} className="gap-1 text-[10px]">
          <Play className="h-3 w-3" />
          Iniciar (10s)
        </Button>
      </div>
    );
  }

  const visible = trace.timeMs.slice(0, visibleCount);
  const visibleAmp = trace.amplitude.slice(0, visibleCount);
  const maxAmp = 0.12;
  const totalDuration = 12000;

  const xScale = (t: number) => PAD.left + (t / totalDuration) * INNER_W;
  const yScale = (a: number) => PAD.top + INNER_H / 2 - (a / maxAmp) * (INNER_H / 2);

  const pathD = visible
    .map((t, i) => `${i === 0 ? "M" : "L"} ${xScale(t).toFixed(1)} ${yScale(visibleAmp[i]).toFixed(1)}`)
    .join(" ");

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between px-2 py-1">
        <span className="text-[10px] font-mono ls-text-muted">{frequency} Hz — Decay test</span>
        {!measuring && visibleCount >= (trace?.timeMs.length ?? 0) && (
          <span className={`text-[10px] font-mono ${trace.decayPercent > 50 ? "text-red-400" : "text-emerald-400"}`}>
            Decay: {trace.decayPercent}%
          </span>
        )}
      </div>

      <svg width={CHART_W} height={CHART_H} className="ls-bg">
        <line x1={PAD.left} y1={yScale(0)} x2={PAD.left + INNER_W} y2={yScale(0)} stroke="var(--ls-border)" strokeWidth={0.5} />
        {/* Stimulus period */}
        <rect x={xScale(2000)} y={PAD.top} width={xScale(12000) - xScale(2000)} height={INNER_H} fill="rgba(251,146,60,0.05)" />

        {/* 50% reference line */}
        <line x1={xScale(2000)} y1={yScale(-0.04)} x2={xScale(12000)} y2={yScale(-0.04)} stroke="rgba(248,113,113,0.3)" strokeWidth={0.5} strokeDasharray="4,4" />
        <text x={xScale(12000) + 2} y={yScale(-0.04) + 3} className="text-[6px]" fill="rgba(248,113,113,0.5)">50%</text>

        {visible.length > 1 && (
          <path d={pathD} fill="none" stroke="#fb923c" strokeWidth={1.5} />
        )}

        <text x={PAD.left} y={CHART_H - 3} className="text-[7px]" fill="var(--ls-text-muted)">0s</text>
        <text x={xScale(2000)} y={CHART_H - 3} className="text-[7px]" fill="rgba(251,146,60,0.5)">↑stim</text>
        <text x={PAD.left + INNER_W} y={CHART_H - 3} textAnchor="end" className="text-[7px]" fill="var(--ls-text-muted)">12s</text>
      </svg>

      <div className="flex gap-1 px-2 py-1">
        <Button size="xs" variant="ghost" onClick={handleStart} disabled={measuring} className="gap-1 text-[10px]">
          <Play className="h-3 w-3" />
          {measuring ? "Midiendo..." : "Repetir"}
        </Button>
      </div>
    </div>
  );
}
