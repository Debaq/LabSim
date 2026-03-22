/**
 * Panel de reflejos acústicos.
 * Muestra la traza del reflejo (deflexión de compliance) cuando se presenta el estímulo.
 * El estudiante busca el umbral subiendo/bajando intensidad.
 */

import { useState, useEffect, useRef } from "react";
import { Button } from "@/components/ui/button";
import { Play } from "lucide-react";
import { generateReflexTrace, type ReflexTrace } from "@/lib/impedance-synthetic";
import type { EarPhysiology } from "@/modules/impedance/schema";
import type { ImpedanceSettings } from "./impedance-controls";

interface Props {
  ear: EarPhysiology;
  settings: ImpedanceSettings;
  seed: number;
  variance: number;
}

const CHART_W = 300;
const CHART_H = 120;
const PAD = { top: 10, right: 10, bottom: 20, left: 40 };
const INNER_W = CHART_W - PAD.left - PAD.right;
const INNER_H = CHART_H - PAD.top - PAD.bottom;

export function ReflexPanel({ ear, settings, seed, variance }: Props) {
  const [trace, setTrace] = useState<ReflexTrace | null>(null);
  const [visibleCount, setVisibleCount] = useState(0);
  const [measuring, setMeasuring] = useState(false);
  const animRef = useRef<number | null>(null);

  const threshold = settings.reflexMode === "ipsi"
    ? ear[`reflexIpsi${settings.reflexFrequency}` as keyof EarPhysiology] as number | null
    : ear[`reflexContra${settings.reflexFrequency}` as keyof EarPhysiology] as number | null;

  const handleMeasure = () => {
    const newTrace = generateReflexTrace(
      threshold,
      settings.reflexIntensity,
      seed + settings.reflexFrequency + (settings.reflexMode === "contra" ? 5000 : 0),
      variance,
    );
    setTrace(newTrace);
    setVisibleCount(0);
    setMeasuring(true);
  };

  // Animar la traza
  useEffect(() => {
    if (!measuring || !trace) return;
    let count = 0;
    const tick = () => {
      count += 3; // 3 puntos por frame
      setVisibleCount(Math.min(count, trace.timeMs.length));
      if (count < trace.timeMs.length) {
        animRef.current = window.setTimeout(tick, 20);
      } else {
        setMeasuring(false);
      }
    };
    animRef.current = window.setTimeout(tick, 20);
    return () => { if (animRef.current) clearTimeout(animRef.current); };
  }, [measuring, trace]);

  if (!trace) {
    return (
      <div className="flex flex-col items-center gap-2 py-4">
        <div className="text-[10px] ls-text-muted text-center">
          {settings.reflexMode === "ipsi" ? "Ipsilateral" : "Contralateral"} · {settings.reflexFrequency} Hz · {settings.reflexIntensity} dB
        </div>
        <Button size="xs" variant="ghost" onClick={handleMeasure} className="gap-1 text-[10px]">
          <Play className="h-3 w-3" />
          Presentar estímulo
        </Button>
      </div>
    );
  }

  const visible = trace.timeMs.slice(0, visibleCount);
  const visibleAmp = trace.amplitude.slice(0, visibleCount);

  const maxAmp = 0.15;
  const xScale = (t: number) => PAD.left + (t / 1500) * INNER_W;
  const yScale = (a: number) => PAD.top + INNER_H / 2 - (a / maxAmp) * (INNER_H / 2);

  const pathD = visible
    .map((t, i) => `${i === 0 ? "M" : "L"} ${xScale(t).toFixed(1)} ${yScale(visibleAmp[i]).toFixed(1)}`)
    .join(" ");

  // Detectar si hay reflejo visible
  const minAmp = Math.min(...trace.amplitude);
  const hasReflex = minAmp < -0.02;

  return (
    <div className="flex flex-col">
      <div className="flex items-center justify-between px-2 py-1">
        <span className="text-[10px] font-mono ls-text-muted">
          {settings.reflexMode === "ipsi" ? "IPSI" : "CONTRA"} · {settings.reflexFrequency} Hz · {settings.reflexIntensity} dB
        </span>
        {!measuring && (
          <span className={`text-[10px] font-mono ${hasReflex ? "text-emerald-400" : "text-zinc-500"}`}>
            {hasReflex ? "Deflexión detectada" : "Sin deflexión"}
          </span>
        )}
      </div>

      <svg width={CHART_W} height={CHART_H} className="ls-bg">
        {/* Baseline */}
        <line x1={PAD.left} y1={yScale(0)} x2={PAD.left + INNER_W} y2={yScale(0)} stroke="var(--ls-border)" strokeWidth={0.5} />

        {/* Stimulus indicator */}
        <rect x={xScale(200)} y={PAD.top} width={xScale(1200) - xScale(200)} height={INNER_H} fill="rgba(56,189,248,0.05)" />

        {/* Trace */}
        {visible.length > 1 && (
          <path d={pathD} fill="none" stroke="#f472b6" strokeWidth={1.5} />
        )}

        {/* Time axis */}
        <text x={PAD.left} y={CHART_H - 3} className="text-[7px]" fill="var(--ls-text-muted)">0ms</text>
        <text x={PAD.left + INNER_W} y={CHART_H - 3} textAnchor="end" className="text-[7px]" fill="var(--ls-text-muted)">1500ms</text>
        <text x={xScale(200)} y={CHART_H - 3} className="text-[7px]" fill="rgba(56,189,248,0.5)">↑stim</text>
      </svg>

      <div className="flex gap-1 px-2 py-1">
        <Button size="xs" variant="ghost" onClick={handleMeasure} disabled={measuring} className="gap-1 text-[10px]">
          <Play className="h-3 w-3" />
          {measuring ? "Midiendo..." : "Repetir"}
        </Button>
      </div>
    </div>
  );
}
