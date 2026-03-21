import { useRef, useEffect } from "react";
import { curvatureColor, pachymetryColor, elevationColor, type MapType } from "@/lib/corneal-topography-synthetic";

interface Props {
  mapType: MapType;
}

const SCALE_CONFIGS: Record<MapType, { min: number; max: number; step: number; unit: string; colorFn: (v: number) => [number, number, number] }> = {
  axial:      { min: 38, max: 52, step: 2, unit: "D", colorFn: curvatureColor },
  tangential: { min: 38, max: 52, step: 2, unit: "D", colorFn: curvatureColor },
  elevation:  { min: -40, max: 40, step: 10, unit: "µm", colorFn: elevationColor },
  pachymetry: { min: 400, max: 650, step: 50, unit: "µm", colorFn: pachymetryColor },
};

export function ColorScale({ mapType }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const config = SCALE_CONFIGS[mapType];

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const w = 16;
    const h = 160;
    canvas.width = w;
    canvas.height = h;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    for (let y = 0; y < h; y++) {
      const t = 1 - y / h;
      const val = config.min + t * (config.max - config.min);
      const [r, g, b] = config.colorFn(val);
      ctx.fillStyle = `rgb(${r},${g},${b})`;
      ctx.fillRect(0, y, w, 1);
    }
  }, [mapType, config]);

  const labels: number[] = [];
  for (let v = config.min; v <= config.max; v += config.step) {
    labels.push(v);
  }

  return (
    <div className="flex gap-1">
      <canvas
        ref={canvasRef}
        className="rounded-sm"
        style={{ width: 12, height: 140 }}
      />
      <div className="flex flex-col justify-between" style={{ height: 140 }}>
        {labels.reverse().map((v) => (
          <span key={v} className="text-[9px] font-mono ls-text-muted leading-none">
            {v}
          </span>
        ))}
        <span className="text-[8px] ls-text-muted mt-0.5">{config.unit}</span>
      </div>
    </div>
  );
}
