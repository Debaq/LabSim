import { useRef, useEffect, useMemo } from "react";
import {
  generateCurvatureMap,
  generateElevationMap,
  generatePachymetryMap,
  renderMapToImage,
  type CornealPathology,
  type MapType,
} from "@/lib/corneal-topography-synthetic";

interface Props {
  seed: number;
  pathology: CornealPathology;
  mapType: MapType;
  size?: number;
}

export function TopographyMap({ seed, pathology, mapType, size = 220 }: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null);

  const imageData = useMemo(() => {
    let map: Float32Array;
    if (mapType === "pachymetry") {
      map = generatePachymetryMap(size, seed, pathology);
    } else if (mapType === "elevation") {
      map = generateElevationMap(size, seed, pathology);
    } else {
      map = generateCurvatureMap(size, seed, pathology, mapType);
    }
    return renderMapToImage(map, size, mapType);
  }, [seed, pathology, mapType, size]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    ctx.putImageData(imageData, 0, 0);

    // Overlay: rings at 1mm, 3mm, 5mm, 7mm
    ctx.strokeStyle = "rgba(255,255,255,0.15)";
    ctx.lineWidth = 0.5;
    const cx = size / 2;
    const cy = size / 2;
    const pxPerMm = size / 9; // ~4.5mm radius = size/2

    for (const r of [1, 3, 5, 7]) {
      ctx.beginPath();
      ctx.arc(cx, cy, (r / 2) * pxPerMm, 0, Math.PI * 2);
      ctx.stroke();
    }

    // Cross-hair
    ctx.strokeStyle = "rgba(255,255,255,0.12)";
    ctx.beginPath();
    ctx.moveTo(cx, 0);
    ctx.lineTo(cx, size);
    ctx.moveTo(0, cy);
    ctx.lineTo(size, cy);
    ctx.stroke();

    // Ring labels
    ctx.fillStyle = "rgba(255,255,255,0.3)";
    ctx.font = "8px monospace";
    ctx.textAlign = "left";
    for (const r of [3, 5, 7]) {
      ctx.fillText(`${r}mm`, cx + (r / 2) * pxPerMm + 2, cy - 2);
    }
  }, [imageData, size]);

  return (
    <canvas
      ref={canvasRef}
      className="rounded-lg"
      style={{ width: size, height: size, imageRendering: "pixelated" }}
    />
  );
}
