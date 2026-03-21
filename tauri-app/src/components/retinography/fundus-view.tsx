import { useRef, useEffect } from "react";
import { renderFundus, type FundusParams } from "@/lib/retinography-synthetic";

interface Props {
  seed: number;
  pathology: FundusParams["pathology"];
  eye: "OD" | "OI";
  signalQuality: number;
}

export function FundusView({ seed, pathology, eye, signalQuality }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    // Tamaño del canvas según el contenedor
    const parent = canvas.parentElement;
    if (parent) {
      const size = Math.min(parent.clientWidth, parent.clientHeight);
      canvas.width = size;
      canvas.height = size;
    }

    renderFundus(ctx, canvas.width, canvas.height, {
      seed,
      pathology,
      eye,
      signalQuality,
    });
  }, [seed, pathology, eye, signalQuality]);

  // Re-render on resize
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const observer = new ResizeObserver(() => {
      const parent = canvas.parentElement;
      if (!parent) return;
      const size = Math.min(parent.clientWidth, parent.clientHeight);
      if (canvas.width !== size || canvas.height !== size) {
        canvas.width = size;
        canvas.height = size;
        const ctx = canvas.getContext("2d");
        if (ctx) {
          renderFundus(ctx, size, size, { seed, pathology, eye, signalQuality });
        }
      }
    });

    if (canvas.parentElement) observer.observe(canvas.parentElement);
    return () => observer.disconnect();
  }, [seed, pathology, eye, signalQuality]);

  return (
    <canvas
      ref={canvasRef}
      className="max-h-full max-w-full rounded"
      style={{ imageRendering: "auto" }}
    />
  );
}
