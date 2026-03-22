import { useRef, useEffect } from "react";
import { renderFundus, type FundusParams, type FundusFilter } from "@/lib/retinography-synthetic";

interface Props {
  seed: number;
  pathology: FundusParams["pathology"];
  eye: "OD" | "OI";
  signalQuality: number;
  filter?: FundusFilter;
  diopterOffset?: number;
  flashIntensity?: number;
  captureAngle?: number;
}

export function FundusView({ seed, pathology, eye, signalQuality, filter, diopterOffset, flashIntensity, captureAngle }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const params: FundusParams = { seed, pathology, eye, signalQuality, filter, diopterOffset, flashIntensity, captureAngle };

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    const parent = canvas.parentElement;
    if (parent) {
      const size = Math.min(parent.clientWidth, parent.clientHeight);
      canvas.width = size;
      canvas.height = size;
    }

    renderFundus(ctx, canvas.width, canvas.height, params);
  }, [seed, pathology, eye, signalQuality, filter, diopterOffset, flashIntensity, captureAngle]);

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
          renderFundus(ctx, size, size, params);
        }
      }
    });

    if (canvas.parentElement) observer.observe(canvas.parentElement);
    return () => observer.disconnect();
  }, [seed, pathology, eye, signalQuality, filter, diopterOffset, flashIntensity, captureAngle]);

  return (
    <canvas
      ref={canvasRef}
      className="max-h-full max-w-full rounded"
      style={{ imageRendering: "auto" }}
    />
  );
}
