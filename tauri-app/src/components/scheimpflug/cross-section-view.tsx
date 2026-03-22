/**
 * Vista del corte Scheimpflug — la imagen de sección transversal de la cámara anterior.
 * Muestra: córnea (anterior + posterior), cámara anterior, iris, cristalino.
 */

import type { ScheimpflugCrossSection } from "@/lib/scheimpflug-synthetic";

interface Props {
  data: ScheimpflugCrossSection;
  width?: number;
  height?: number;
}

const W = 380;
const H = 200;
const PAD = { top: 10, right: 10, bottom: 10, left: 10 };

export function CrossSectionView({ data, width = W, height = H }: Props) {
  const innerW = width - PAD.left - PAD.right;
  const innerH = height - PAD.top - PAD.bottom;

  // Escalar coordenadas reales (mm) a pixels
  const allY = [
    ...data.anteriorSurface.map((p) => p.y),
    ...data.posteriorSurface.map((p) => p.y),
    ...data.lensPosterior.map((p) => p.y),
  ];
  const minY = Math.min(...allY) - 0.2;
  const maxY = Math.max(...allY) + 0.2;
  const xRange = 9; // -4.5 a 4.5 mm

  const sx = (x: number) => PAD.left + ((x + xRange / 2) / xRange) * innerW;
  const sy = (y: number) => PAD.top + ((y - minY) / (maxY - minY)) * innerH;

  const toPath = (points: { x: number; y: number }[]) =>
    points.map((p, i) => `${i === 0 ? "M" : "L"} ${sx(p.x).toFixed(1)} ${sy(p.y).toFixed(1)}`).join(" ");

  // Fill entre anterior y posterior (córnea)
  const corneaFill = toPath(data.anteriorSurface) + " " +
    toPath([...data.posteriorSurface].reverse()).replace("M", "L") + " Z";

  // Fill del cristalino
  const lensFill = data.lensAnterior.length > 0
    ? toPath(data.lensAnterior) + " " +
      toPath([...data.lensPosterior].reverse()).replace("M", "L") + " Z"
    : "";

  return (
    <svg width={width} height={height} className="ls-bg rounded">
      {/* Background gradient — simula iluminación Scheimpflug */}
      <defs>
        <linearGradient id="scheimpflug-bg" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(0,0,0,0.9)" />
          <stop offset="100%" stopColor="rgba(10,15,30,0.95)" />
        </linearGradient>
        <linearGradient id="cornea-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(100,180,255,0.6)" />
          <stop offset="100%" stopColor="rgba(60,120,200,0.4)" />
        </linearGradient>
        <linearGradient id="lens-grad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="rgba(200,180,100,0.35)" />
          <stop offset="100%" stopColor="rgba(180,150,60,0.25)" />
        </linearGradient>
      </defs>

      <rect width={width} height={height} fill="url(#scheimpflug-bg)" rx={4} />

      {/* Córnea (fill translúcido azul) */}
      <path d={corneaFill} fill="url(#cornea-grad)" />

      {/* Superficie anterior (línea brillante) */}
      <path d={toPath(data.anteriorSurface)} fill="none" stroke="rgba(140,200,255,0.9)" strokeWidth={1.5} />

      {/* Superficie posterior */}
      <path d={toPath(data.posteriorSurface)} fill="none" stroke="rgba(100,160,220,0.6)" strokeWidth={1} />

      {/* Iris (líneas horizontales desde los bordes hasta la pupila) */}
      {data.irisY && (
        <>
          <line x1={sx(-4.5)} y1={sy(data.irisY)} x2={sx(-1.5)} y2={sy(data.irisY)}
            stroke="rgba(140,100,60,0.7)" strokeWidth={2} />
          <line x1={sx(1.5)} y1={sy(data.irisY)} x2={sx(4.5)} y2={sy(data.irisY)}
            stroke="rgba(140,100,60,0.7)" strokeWidth={2} />
          {/* Pupil gap */}
          <circle cx={sx(-1.5)} cy={sy(data.irisY)} r={2} fill="rgba(140,100,60,0.7)" />
          <circle cx={sx(1.5)} cy={sy(data.irisY)} r={2} fill="rgba(140,100,60,0.7)" />
        </>
      )}

      {/* Cristalino */}
      {lensFill && (
        <>
          <path d={lensFill} fill="url(#lens-grad)" />
          <path d={toPath(data.lensAnterior)} fill="none" stroke="rgba(220,200,120,0.5)" strokeWidth={1} />
          <path d={toPath(data.lensPosterior)} fill="none" stroke="rgba(200,180,100,0.4)" strokeWidth={0.8} />
        </>
      )}

      {/* ACD label */}
      <text x={sx(2.5)} y={sy(data.posteriorSurface[50]?.y ?? 0) + 15} className="text-[7px]" fill="rgba(100,180,255,0.5)">
        ACD: {data.acd.toFixed(2)} mm
      </text>

      {/* Scale marker */}
      <line x1={sx(-4)} y1={height - 15} x2={sx(-3)} y2={height - 15} stroke="rgba(255,255,255,0.3)" strokeWidth={1} />
      <text x={sx(-3.5)} y={height - 7} textAnchor="middle" className="text-[6px]" fill="rgba(255,255,255,0.3)">1mm</text>
    </svg>
  );
}
