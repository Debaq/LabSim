/**
 * Gráfico de traza ocular — compartido entre VNG y vHIT.
 * Muestra posición del ojo (°) vs tiempo (ms).
 * Opcionalmente muestra traza de cabeza superpuesta (para vHIT).
 */

import type { EyeTracePoint } from "@/lib/vestibular-synthetic";

interface Props {
  eyeTrace: EyeTracePoint[];
  headTrace?: EyeTracePoint[];
  width?: number;
  height?: number;
  label?: string;
  yRange?: number; // grados máximos
}

const PAD = { top: 12, right: 10, bottom: 18, left: 35 };

export function EyeTraceChart({
  eyeTrace,
  headTrace,
  width = 350,
  height = 140,
  label,
  yRange = 20,
}: Props) {
  const innerW = width - PAD.left - PAD.right;
  const innerH = height - PAD.top - PAD.bottom;

  if (eyeTrace.length === 0) {
    return (
      <div style={{ width, height }} className="flex items-center justify-center ls-bg rounded text-[10px] ls-text-muted">
        Sin datos
      </div>
    );
  }

  const maxT = eyeTrace[eyeTrace.length - 1].timeMs;
  const sx = (t: number) => PAD.left + (t / maxT) * innerW;
  const sy = (deg: number) => PAD.top + innerH / 2 - (deg / yRange) * (innerH / 2);

  const toPath = (points: EyeTracePoint[], decimation = 1) => {
    let d = "";
    for (let i = 0; i < points.length; i += decimation) {
      const p = points[i];
      d += `${i === 0 ? "M" : "L"} ${sx(p.timeMs).toFixed(1)} ${sy(p.positionDeg).toFixed(1)} `;
    }
    return d;
  };

  // Decimation para rendimiento
  const dec = eyeTrace.length > 2000 ? 4 : eyeTrace.length > 500 ? 2 : 1;

  return (
    <svg width={width} height={height} className="ls-bg rounded">
      {/* Grid */}
      <line x1={PAD.left} y1={sy(0)} x2={PAD.left + innerW} y2={sy(0)} stroke="var(--ls-border)" strokeWidth={0.5} />
      {[-yRange, -yRange / 2, yRange / 2, yRange].map((v) => (
        <line key={v} x1={PAD.left} y1={sy(v)} x2={PAD.left + innerW} y2={sy(v)} stroke="var(--ls-border)" strokeWidth={0.3} />
      ))}

      {/* Axes */}
      <line x1={PAD.left} y1={PAD.top} x2={PAD.left} y2={PAD.top + innerH} stroke="var(--ls-text-muted)" strokeWidth={0.5} />

      {/* Y labels */}
      <text x={PAD.left - 4} y={sy(yRange) + 3} textAnchor="end" className="text-[7px]" fill="var(--ls-text-muted)">{yRange}°</text>
      <text x={PAD.left - 4} y={sy(0) + 3} textAnchor="end" className="text-[7px]" fill="var(--ls-text-muted)">0</text>
      <text x={PAD.left - 4} y={sy(-yRange) + 3} textAnchor="end" className="text-[7px]" fill="var(--ls-text-muted)">-{yRange}°</text>

      {/* Head trace (if vHIT) */}
      {headTrace && headTrace.length > 0 && (
        <path d={toPath(headTrace, dec)} fill="none" stroke="rgba(251,146,60,0.6)" strokeWidth={1} />
      )}

      {/* Eye trace */}
      <path d={toPath(eyeTrace, dec)} fill="none" stroke="#22d3ee" strokeWidth={1.2} />

      {/* Label */}
      {label && (
        <text x={PAD.left + 4} y={PAD.top + 10} className="text-[8px]" fill="var(--ls-text-muted)">{label}</text>
      )}

      {/* Legend */}
      {headTrace && (
        <>
          <line x1={width - 80} y1={8} x2={width - 68} y2={8} stroke="rgba(251,146,60,0.6)" strokeWidth={1} />
          <text x={width - 65} y={11} className="text-[7px]" fill="var(--ls-text-muted)">Cabeza</text>
          <line x1={width - 80} y1={18} x2={width - 68} y2={18} stroke="#22d3ee" strokeWidth={1} />
          <text x={width - 65} y={21} className="text-[7px]" fill="var(--ls-text-muted)">Ojo</text>
        </>
      )}
    </svg>
  );
}
